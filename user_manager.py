import os
import shutil
import json
from pathlib import Path
from typing import List, Optional


class UserManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.users_dir = self.base_dir / "users"
        self.users_config_path = self.base_dir / "users.json"
        self.last_user_file = self.base_dir / ".last_user"
        
        # Files that should be moved to user directory during migration
        self.user_files = [
            "config.json",
            "stats.json",
            "goals.json",
            ".session_state.json"
        ]

    def ensure_directories(self):
        """Ensure users directory exists."""
        if self.users_dir.exists():
            if not self.users_dir.is_dir():
                raise NotADirectoryError(f"Users path is not a directory: {self.users_dir}")
            return

        self.users_dir.mkdir(parents=True)

    def get_users(self) -> List[str]:
        """Return a list of user names."""
        if not self.users_dir.exists() or not self.users_dir.is_dir():
            return []

        # List subdirectories in users folder
        try:
            users = [d.name for d in self.users_dir.iterdir() if d.is_dir()]
            # Sort case-insensitively for better UX
            return sorted(users, key=lambda s: s.lower())
        except (OSError, PermissionError):
            return []

    def user_exists(self, username: str) -> bool:
        """Check if user exists, using sanitized name."""
        clean_name = self._sanitize_username(username)
        if not clean_name:
            return False
        return (self.users_dir / clean_name).is_dir()

    def create_user(self, username: str) -> bool:
        """Create a new user directory."""
        try:
            self.ensure_directories()
        except OSError:
            return False

        clean_name = self._sanitize_username(username)
        if not clean_name:
            return False

        user_path = self.users_dir / clean_name
        if user_path.exists():
            return False

        try:
            user_path.mkdir(parents=True)
        except OSError:
            return False
        
        # Create default config if needed, or copy template
        # For now, just creating the directory is enough, app logic handles missing config
        return True

    def delete_user(self, username: str) -> bool:
        """Delete a user directory safely."""
        clean_name = self._sanitize_username(username)
        if not clean_name:
            return False
            
        if not self.user_exists(clean_name):
            return False

        user_path = self.users_dir / clean_name
        
        # Safety check: ensure path is inside users_dir (prevent path traversal)
        try:
            user_path.resolve().relative_to(self.users_dir.resolve())
        except ValueError:
            return False  # Path escapes users_dir
            
        try:
            shutil.rmtree(user_path)
            return True
        except (OSError, PermissionError):
            return False

    def migrate_if_needed(self):
        """Migrate root files to 'Default' user if users directory implies first run with new system."""
        self.ensure_directories()

        users = self.get_users()
        if users:
            # Users already exist, assume migration happened or new system is in use
            return

        # Check if we have root files to migrate
        files_found = any((self.base_dir / f).exists() for f in self.user_files)
        if files_found:
            # Migration needed
            print("Migrating single user data to 'Default' user profile...")
            default_user_path = self.users_dir / "Default"
            default_user_path.mkdir(parents=True, exist_ok=True)
            
            for filename in self.user_files:
                src = self.base_dir / filename
                dst = default_user_path / filename
                if src.exists():
                    try:
                        shutil.move(str(src), str(dst))
                    except Exception as e:
                        print(f"Error moving {filename}: {e}")
        else:
            # New install? Create Default user anyway so people can start
            # self.create_user("Default")
            pass

    def _sanitize_username(self, username: str) -> str:
        """Sanitize username to be safe for filesystem."""
        if not username:
            return ""
        # Simple cleanup, remove special chars
        keep = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ "
        cleaned = "".join(c for c in username if c in keep).strip()
        
        # Check for Windows reserved filenames
        reserved_names = {
            "CON", "PRN", "AUX", "NUL",
            "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
            "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        }
        if cleaned.upper() in reserved_names:
            return f"User_{cleaned}"  # Valid fallback for reserved names
            
        # Limit length to prevent filesystem issues
        return cleaned[:50] if cleaned else ""

    def sanitize_username(self, username: str) -> str:
        """Public wrapper for username sanitization."""
        return self._sanitize_username(username)

    def get_user_dir(self, username: str) -> Path:
        """Get user directory path, using sanitized name."""
        clean_name = self._sanitize_username(username)
        if not clean_name:
            raise ValueError("Invalid username")
        return self.users_dir / clean_name

    def save_last_user(self, username: str):
        """Save the last used username atomically."""
        try:
            clean_name = self._sanitize_username(username)
            if not clean_name:
                return
            
            # Atomic write pattern: write to temp file then rename
            temp_file = self.last_user_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(clean_name)
                f.flush()
                os.fsync(f.fileno())  # Ensure written to disk
            
            # Atomic replace
            os.replace(temp_file, self.last_user_file)
            
        except Exception as e:
            print(f"Failed to save last user: {e}")
            # Attempt cleanup
            try:
                if 'temp_file' in locals() and temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass

    def get_last_user(self) -> Optional[str]:
        """Get the last used username if it exists and is valid."""
        if not self.last_user_file.exists():
            return None

        try:
            with open(self.last_user_file, 'r', encoding='utf-8') as f:
                username = f.read().strip()
                # Validate user exists AND directory is accessible
                if username and self.user_exists(username):
                    user_dir = self.users_dir / self._sanitize_username(username)
                    if user_dir.exists() and user_dir.is_dir():
                        return username
        except Exception:
            pass
        return None

    def clear_last_user(self) -> bool:
        """Clear the last user setting.
        
        Returns:
            True if cleared successfully or file didn't exist, False on error.
        """
        if not self.last_user_file.exists():
            return True
        
        try:
            self.last_user_file.unlink()
            return True
        except PermissionError:
            # Try to clear file content instead of deleting
            try:
                with open(self.last_user_file, 'w', encoding='utf-8') as f:
                    f.write("")  # Empty the file
                return True
            except Exception:
                pass
        except Exception:
            pass
        
        return False
