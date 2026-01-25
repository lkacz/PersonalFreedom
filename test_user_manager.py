"""
Tests for UserManager and user switching logic.

Run with: python -m pytest test_user_manager.py -v
"""
import os
import sys
import shutil
import tempfile
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from user_manager import UserManager


class TestUserManager:
    """Tests for the UserManager class."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.user_manager = UserManager(self.temp_dir)
        yield
        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ensure_directories_creates_users_folder(self):
        """Test that ensure_directories creates the users folder."""
        assert not self.user_manager.users_dir.exists()
        self.user_manager.ensure_directories()
        assert self.user_manager.users_dir.exists()
        assert self.user_manager.users_dir.is_dir()

    def test_get_users_empty(self):
        """Test get_users returns empty list when no users exist."""
        self.user_manager.ensure_directories()
        users = self.user_manager.get_users()
        assert users == []

    def test_create_user_basic(self):
        """Test creating a basic user."""
        result = self.user_manager.create_user("TestUser")
        assert result is True
        assert self.user_manager.user_exists("TestUser")
        users = self.user_manager.get_users()
        assert "TestUser" in users

    def test_create_user_duplicate(self):
        """Test that creating a duplicate user fails."""
        self.user_manager.create_user("TestUser")
        result = self.user_manager.create_user("TestUser")
        assert result is False

    def test_create_user_empty_name(self):
        """Test that creating user with empty name fails."""
        result = self.user_manager.create_user("")
        assert result is False

    def test_create_user_special_characters(self):
        """Test that special characters are sanitized."""
        result = self.user_manager.create_user("Test<>User:*?")
        assert result is True
        # Should be sanitized to "TestUser"
        assert self.user_manager.user_exists("TestUser")

    def test_delete_user(self):
        """Test deleting a user."""
        self.user_manager.create_user("ToDelete")
        assert self.user_manager.user_exists("ToDelete")
        result = self.user_manager.delete_user("ToDelete")
        assert result is True
        assert not self.user_manager.user_exists("ToDelete")

    def test_delete_nonexistent_user(self):
        """Test that deleting a non-existent user fails gracefully."""
        result = self.user_manager.delete_user("NonExistent")
        assert result is False

    def test_get_user_dir(self):
        """Test get_user_dir returns correct path."""
        self.user_manager.create_user("DirTest")
        user_dir = self.user_manager.get_user_dir("DirTest")
        expected = self.user_manager.users_dir / "DirTest"
        assert user_dir == expected

    def test_get_user_dir_invalid_name(self):
        """Test get_user_dir raises error for invalid name."""
        with pytest.raises(ValueError):
            self.user_manager.get_user_dir("")

    def test_sanitize_username(self):
        """Test username sanitization."""
        # Valid characters
        assert self.user_manager.sanitize_username("TestUser123") == "TestUser123"
        # Spaces allowed
        assert self.user_manager.sanitize_username("Test User") == "Test User"
        # Special characters removed
        assert self.user_manager.sanitize_username("Test<>User") == "TestUser"
        # Length limit
        long_name = "A" * 100
        assert len(self.user_manager.sanitize_username(long_name)) == 50

    def test_save_and_get_last_user(self):
        """Test saving and retrieving last user."""
        self.user_manager.create_user("LastUserTest")
        self.user_manager.save_last_user("LastUserTest")
        
        last = self.user_manager.get_last_user()
        assert last == "LastUserTest"

    def test_get_last_user_nonexistent(self):
        """Test get_last_user returns None if user doesn't exist."""
        # Save a user that doesn't exist
        self.user_manager.ensure_directories()
        with open(self.user_manager.last_user_file, 'w') as f:
            f.write("NonExistentUser")
        
        last = self.user_manager.get_last_user()
        assert last is None

    def test_clear_last_user(self):
        """Test clearing last user."""
        self.user_manager.create_user("ToClear")
        self.user_manager.save_last_user("ToClear")
        assert self.user_manager.last_user_file.exists()
        
        result = self.user_manager.clear_last_user()
        assert result is True
        assert not self.user_manager.last_user_file.exists()

    def test_clear_last_user_no_file(self):
        """Test clearing last user when no file exists returns True."""
        # Should not raise, should return True
        result = self.user_manager.clear_last_user()
        assert result is True

    def test_multiple_users_sorted(self):
        """Test that get_users returns users sorted case-insensitively."""
        self.user_manager.create_user("Zoe")
        self.user_manager.create_user("alice")
        self.user_manager.create_user("Bob")
        
        users = self.user_manager.get_users()
        assert users == ["alice", "Bob", "Zoe"]

    def test_migrate_if_needed_no_files(self):
        """Test migration with no existing files does nothing."""
        self.user_manager.migrate_if_needed()
        # Should just ensure users dir exists
        assert self.user_manager.users_dir.exists()

    def test_migrate_if_needed_with_files(self):
        """Test migration moves files to Default user."""
        # Create some root files
        (self.temp_dir / "config.json").write_text('{"test": true}')
        (self.temp_dir / "stats.json").write_text('{"xp": 100}')
        
        self.user_manager.migrate_if_needed()
        
        # Check files were moved
        default_dir = self.user_manager.users_dir / "Default"
        assert default_dir.exists()
        assert (default_dir / "config.json").exists()
        assert (default_dir / "stats.json").exists()
        # Original files should be gone
        assert not (self.temp_dir / "config.json").exists()
        assert not (self.temp_dir / "stats.json").exists()

    def test_migrate_if_needed_skips_if_users_exist(self):
        """Test migration is skipped if users already exist."""
        # Create a user first
        self.user_manager.create_user("ExistingUser")
        # Create some root files
        (self.temp_dir / "config.json").write_text('{"test": true}')
        
        self.user_manager.migrate_if_needed()
        
        # Root file should still be there (migration skipped)
        assert (self.temp_dir / "config.json").exists()


class TestUserSwitchLogic:
    """Tests for user switch logic used in the GUI."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory for each test."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.user_manager = UserManager(self.temp_dir)
        yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_switch_clears_last_user(self):
        """Test that switching user clears the last user setting."""
        # Setup: create and set a user
        self.user_manager.create_user("User1")
        self.user_manager.save_last_user("User1")
        assert self.user_manager.get_last_user() == "User1"
        
        # Action: simulate switch by clearing last user
        self.user_manager.clear_last_user()
        
        # Verify: last user is cleared
        assert self.user_manager.get_last_user() is None

    def test_switch_to_new_user(self):
        """Test the full user switch workflow."""
        # Setup initial user
        self.user_manager.create_user("OriginalUser")
        self.user_manager.save_last_user("OriginalUser")
        
        # Create config for original user
        orig_dir = self.user_manager.get_user_dir("OriginalUser")
        (orig_dir / "config.json").write_text('{"theme": "dark"}')
        
        # Simulate switch: clear last user
        self.user_manager.clear_last_user()
        
        # Simulate new selection
        self.user_manager.create_user("NewUser")
        self.user_manager.save_last_user("NewUser")
        
        # Verify new user is now active
        assert self.user_manager.get_last_user() == "NewUser"

    def test_auto_login_validation(self):
        """Test that auto-login validates user directory exists."""
        # Create user and set as last
        self.user_manager.create_user("ValidUser")
        self.user_manager.save_last_user("ValidUser")
        
        # Verify auto-login works
        assert self.user_manager.get_last_user() == "ValidUser"
        
        # Delete the user directory (simulate corruption/deletion)
        user_dir = self.user_manager.get_user_dir("ValidUser")
        shutil.rmtree(user_dir)
        
        # Now auto-login should fail validation
        assert self.user_manager.get_last_user() is None

    def test_invalid_last_user_file_content(self):
        """Test handling of corrupted last user file."""
        self.user_manager.ensure_directories()
        # Write garbage to last user file
        with open(self.user_manager.last_user_file, 'w') as f:
            f.write("   \n\t  ")  # Whitespace only
        
        assert self.user_manager.get_last_user() is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
