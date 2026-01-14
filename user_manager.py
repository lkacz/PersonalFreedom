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
        if not self.users_dir.exists():
            self.users_dir.mkdir(parents=True)

    def get_users(self) -> List[str]:
        """Return a list of user names."""
        if not self.users_dir.exists():
            return []
        
        # List subdirectories in users folder
        users = [d.name for d in self.users_dir.iterdir() if d.is_dir()]
        return sorted(users)

    def user_exists(self, username: str) -> bool:
        return (self.users_dir / username).exists()

    def create_user(self, username: str) -> bool:
        """Create a new user directory."""
        self.ensure_directories()
        
        clean_name = self._sanitize_username(username)
        if not clean_name:
            return False
            
        user_path = self.users_dir / clean_name
        if user_path.exists():
            return False
            
        user_path.mkdir(parents=True)
        
        # Create default config if needed, or copy template
        # For now, just creating the directory is enough, app logic handles missing config
        
        return True

    def delete_user(self, username: str) -> bool:
        """Delete a user directory."""
        if not self.user_exists(username):
            return False
            
        shutil.rmtree(self.users_dir / username)
        return True

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
        # Simple cleanup, remove special chars
        keep = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ "
        cleaned = "".join(c for c in username if c in keep).strip()
        return cleaned

    def get_user_dir(self, username: str) -> Path:
        return self.users_dir / username

    def save_last_user(self, username: str):
        """Save the last used username."""
        try:
            with open(self.last_user_file, 'w', encoding='utf-8') as f:
                f.write(username)
        except Exception as e:
            print(f"Failed to save last user: {e}")

    def get_last_user(self) -> Optional[str]:
        """Get the last used username if it exists and is valid."""
        if not self.last_user_file.exists():
            return None
            
        try:
            with open(self.last_user_file, 'r', encoding='utf-8') as f:
                username = f.read().strip()
                if self.user_exists(username):
                    return username
        except Exception:
            return None
        return None

    def clear_last_user(self):
        """Clear the last user setting."""
        if self.last_user_file.exists():
            try:
                self.last_user_file.unlink()
            except Exception:
                pass
