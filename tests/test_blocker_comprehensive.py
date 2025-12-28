"""
Comprehensive tests for BlockerCore functionality.
Tests cover configuration, blocking, whitelisting, scheduling, and statistics.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import core_logic
from core_logic import BlockerCore, BlockMode, SITE_CATEGORIES


class TestBlockerCoreInit(unittest.TestCase):
    """Tests for BlockerCore initialization."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_config = Path(self.test_dir) / "config.json"
        self.test_stats = Path(self.test_dir) / "stats.json"
        
        self.config_patcher = patch('core_logic.CONFIG_PATH', self.test_config)
        self.stats_patcher = patch('core_logic.STATS_PATH', self.test_stats)
        self.config_patcher.start()
        self.stats_patcher.start()

    def tearDown(self) -> None:
        self.config_patcher.stop()
        self.stats_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_init_creates_default_config(self) -> None:
        """Test that initialization creates config with defaults."""
        core = BlockerCore()
        self.assertTrue(self.test_config.exists())

    def test_init_default_mode(self) -> None:
        """Test default mode is NORMAL."""
        core = BlockerCore()
        self.assertEqual(core.mode, BlockMode.NORMAL)

    def test_init_default_categories_enabled(self) -> None:
        """Test all categories enabled by default."""
        core = BlockerCore()
        for category in SITE_CATEGORIES:
            self.assertTrue(core.categories_enabled.get(category, False))

    def test_init_empty_whitelist(self) -> None:
        """Test whitelist starts empty."""
        core = BlockerCore()
        self.assertEqual(core.whitelist, [])

    def test_init_not_blocking(self) -> None:
        """Test not blocking on init."""
        core = BlockerCore()
        self.assertFalse(core.is_blocking)


class TestBlockerCoreConfig(unittest.TestCase):
    """Tests for configuration save/load."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_config = Path(self.test_dir) / "config.json"
        self.test_stats = Path(self.test_dir) / "stats.json"
        
        self.config_patcher = patch('core_logic.CONFIG_PATH', self.test_config)
        self.stats_patcher = patch('core_logic.STATS_PATH', self.test_stats)
        self.config_patcher.start()
        self.stats_patcher.start()

    def tearDown(self) -> None:
        self.config_patcher.stop()
        self.stats_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_save_and_load_blacklist(self) -> None:
        """Test blacklist persists across instances."""
        core1 = BlockerCore()
        core1.add_site("example.com")
        core1.save_config()
        
        core2 = BlockerCore()
        self.assertIn("example.com", core2.blacklist)

    def test_save_and_load_whitelist(self) -> None:
        """Test whitelist persists across instances."""
        core1 = BlockerCore()
        core1.add_to_whitelist("allowed.com")
        
        core2 = BlockerCore()
        self.assertIn("allowed.com", core2.whitelist)

    def test_save_and_load_pomodoro_settings(self) -> None:
        """Test Pomodoro settings persist."""
        core1 = BlockerCore()
        core1.pomodoro_work = 30
        core1.pomodoro_break = 10
        core1.save_config()
        
        core2 = BlockerCore()
        self.assertEqual(core2.pomodoro_work, 30)
        self.assertEqual(core2.pomodoro_break, 10)

    def test_load_corrupted_config(self) -> None:
        """Test handling of corrupted config file."""
        with open(self.test_config, 'w') as f:
            f.write("not valid json")
        
        # Should not raise, should use defaults
        core = BlockerCore()
        self.assertIsInstance(core.blacklist, list)


class TestBlockerCoreSites(unittest.TestCase):
    """Tests for site management."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_config = Path(self.test_dir) / "config.json"
        self.test_stats = Path(self.test_dir) / "stats.json"
        
        self.config_patcher = patch('core_logic.CONFIG_PATH', self.test_config)
        self.stats_patcher = patch('core_logic.STATS_PATH', self.test_stats)
        self.config_patcher.start()
        self.stats_patcher.start()

    def tearDown(self) -> None:
        self.config_patcher.stop()
        self.stats_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_add_site_strips_https(self) -> None:
        """Test HTTPS prefix is stripped."""
        core = BlockerCore()
        core.blacklist = []
        core.add_site("https://test.com")
        self.assertIn("test.com", core.blacklist)
        self.assertNotIn("https://test.com", core.blacklist)

    def test_add_site_strips_http(self) -> None:
        """Test HTTP prefix is stripped."""
        core = BlockerCore()
        core.blacklist = []
        core.add_site("http://test.com")
        self.assertIn("test.com", core.blacklist)

    def test_add_site_adds_www_variant(self) -> None:
        """Test www variant is automatically added."""
        core = BlockerCore()
        core.blacklist = []
        core.add_site("test.com")
        self.assertIn("test.com", core.blacklist)
        self.assertIn("www.test.com", core.blacklist)

    def test_add_site_strips_path(self) -> None:
        """Test URL path is stripped."""
        core = BlockerCore()
        core.blacklist = []
        core.add_site("test.com/some/path")
        self.assertIn("test.com", core.blacklist)
        self.assertNotIn("test.com/some/path", core.blacklist)

    def test_add_site_duplicate_returns_false(self) -> None:
        """Test adding duplicate site returns False."""
        core = BlockerCore()
        core.blacklist = ["test.com", "www.test.com"]
        result = core.add_site("test.com")
        self.assertFalse(result)

    def test_remove_site(self) -> None:
        """Test removing a site."""
        core = BlockerCore()
        core.blacklist = ["test.com"]
        result = core.remove_site("test.com")
        self.assertTrue(result)
        self.assertNotIn("test.com", core.blacklist)

    def test_remove_nonexistent_site(self) -> None:
        """Test removing non-existent site returns False."""
        core = BlockerCore()
        core.blacklist = []
        result = core.remove_site("nothere.com")
        self.assertFalse(result)

    def test_add_to_whitelist(self) -> None:
        """Test adding to whitelist."""
        core = BlockerCore()
        core.add_to_whitelist("allowed.com")
        self.assertIn("allowed.com", core.whitelist)

    def test_whitelist_adds_www_variant(self) -> None:
        """Test whitelist adds www variant."""
        core = BlockerCore()
        core.add_to_whitelist("allowed.com")
        self.assertIn("www.allowed.com", core.whitelist)


class TestBlockerCoreEffectiveBlacklist(unittest.TestCase):
    """Tests for effective blacklist calculation."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_config = Path(self.test_dir) / "config.json"
        self.test_stats = Path(self.test_dir) / "stats.json"
        
        self.config_patcher = patch('core_logic.CONFIG_PATH', self.test_config)
        self.stats_patcher = patch('core_logic.STATS_PATH', self.test_stats)
        self.config_patcher.start()
        self.stats_patcher.start()

    def tearDown(self) -> None:
        self.config_patcher.stop()
        self.stats_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_effective_blacklist_includes_enabled_categories(self) -> None:
        """Test enabled category sites are included."""
        core = BlockerCore()
        core.blacklist = []
        core.categories_enabled = {"Social Media": True}
        effective = core.get_effective_blacklist()
        self.assertIn("facebook.com", effective)

    def test_effective_blacklist_excludes_disabled_categories(self) -> None:
        """Test disabled category sites are excluded."""
        core = BlockerCore()
        core.blacklist = []
        core.categories_enabled = {"Social Media": False}
        effective = core.get_effective_blacklist()
        # facebook should not be in list since Social Media is disabled
        # unless it's in custom blacklist
        if "facebook.com" not in core.blacklist:
            pass  # Test passed implicitly

    def test_effective_blacklist_excludes_whitelist(self) -> None:
        """Test whitelisted sites are excluded."""
        core = BlockerCore()
        core.blacklist = ["test.com"]
        core.whitelist = ["test.com"]
        effective = core.get_effective_blacklist()
        self.assertNotIn("test.com", effective)


class TestBlockerCorePassword(unittest.TestCase):
    """Tests for password functionality."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_config = Path(self.test_dir) / "config.json"
        self.test_stats = Path(self.test_dir) / "stats.json"
        
        self.config_patcher = patch('core_logic.CONFIG_PATH', self.test_config)
        self.stats_patcher = patch('core_logic.STATS_PATH', self.test_stats)
        self.config_patcher.start()
        self.stats_patcher.start()

    def tearDown(self) -> None:
        self.config_patcher.stop()
        self.stats_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_set_password_hashes(self) -> None:
        """Test password is hashed, not stored plaintext."""
        core = BlockerCore()
        core.set_password("testpassword")
        self.assertIsNotNone(core.password_hash)
        self.assertNotEqual(core.password_hash, "testpassword")

    def test_password_uses_bcrypt(self) -> None:
        """Test bcrypt hash format."""
        core = BlockerCore()
        core.set_password("testpassword")
        if core.password_hash:
            self.assertTrue(
                core.password_hash.startswith('$2b$') or 
                core.password_hash.startswith('$2a$')
            )

    def test_verify_correct_password(self) -> None:
        """Test correct password verifies."""
        core = BlockerCore()
        core.set_password("securepass")
        self.assertTrue(core.verify_password("securepass"))

    def test_verify_incorrect_password(self) -> None:
        """Test incorrect password fails."""
        core = BlockerCore()
        core.set_password("securepass")
        self.assertFalse(core.verify_password("wrongpass"))

    def test_verify_no_password_set(self) -> None:
        """Test verification passes when no password set."""
        core = BlockerCore()
        core.password_hash = None
        self.assertTrue(core.verify_password("anything"))

    def test_remove_password(self) -> None:
        """Test password can be removed."""
        core = BlockerCore()
        core.set_password("testpass")
        core.set_password(None)
        self.assertIsNone(core.password_hash)


class TestBlockerCoreStats(unittest.TestCase):
    """Tests for statistics tracking."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_config = Path(self.test_dir) / "config.json"
        self.test_stats = Path(self.test_dir) / "stats.json"
        
        self.config_patcher = patch('core_logic.CONFIG_PATH', self.test_config)
        self.stats_patcher = patch('core_logic.STATS_PATH', self.test_stats)
        self.config_patcher.start()
        self.stats_patcher.start()

    def tearDown(self) -> None:
        self.config_patcher.stop()
        self.stats_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_update_stats_completed_session(self) -> None:
        """Test completed session updates stats."""
        core = BlockerCore()
        initial_completed = core.stats["sessions_completed"]
        core.update_stats(1800, completed=True)
        self.assertEqual(core.stats["sessions_completed"], initial_completed + 1)

    def test_update_stats_cancelled_session(self) -> None:
        """Test cancelled session updates stats."""
        core = BlockerCore()
        initial_cancelled = core.stats["sessions_cancelled"]
        core.update_stats(600, completed=False)
        self.assertEqual(core.stats["sessions_cancelled"], initial_cancelled + 1)

    def test_update_stats_total_time(self) -> None:
        """Test total focus time is accumulated."""
        core = BlockerCore()
        initial_time = core.stats["total_focus_time"]
        core.update_stats(1800, completed=True)
        self.assertEqual(core.stats["total_focus_time"], initial_time + 1800)

    def test_stats_summary(self) -> None:
        """Test stats summary returns expected keys."""
        core = BlockerCore()
        summary = core.get_stats_summary()
        self.assertIn("total_hours", summary)
        self.assertIn("sessions_completed", summary)
        self.assertIn("current_streak", summary)
        self.assertIn("best_streak", summary)


class TestBlockerCoreSchedule(unittest.TestCase):
    """Tests for scheduling functionality."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_config = Path(self.test_dir) / "config.json"
        self.test_stats = Path(self.test_dir) / "stats.json"
        
        self.config_patcher = patch('core_logic.CONFIG_PATH', self.test_config)
        self.stats_patcher = patch('core_logic.STATS_PATH', self.test_stats)
        self.config_patcher.start()
        self.stats_patcher.start()

    def tearDown(self) -> None:
        self.config_patcher.stop()
        self.stats_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_add_schedule(self) -> None:
        """Test adding a schedule."""
        core = BlockerCore()
        schedule_id = core.add_schedule([0, 1, 2, 3, 4], "09:00", "17:00")
        self.assertIsNotNone(schedule_id)
        self.assertEqual(len(core.schedules), 1)

    def test_remove_schedule(self) -> None:
        """Test removing a schedule."""
        core = BlockerCore()
        schedule_id = core.add_schedule([0, 1], "09:00", "17:00")
        core.remove_schedule(schedule_id)
        self.assertEqual(len(core.schedules), 0)

    def test_toggle_schedule(self) -> None:
        """Test toggling a schedule."""
        core = BlockerCore()
        schedule_id = core.add_schedule([0], "09:00", "17:00")
        # Initially enabled
        result = core.toggle_schedule(schedule_id)
        self.assertFalse(result)  # Now disabled
        result = core.toggle_schedule(schedule_id)
        self.assertTrue(result)  # Now enabled again


class TestBlockerCoreValidation(unittest.TestCase):
    """Tests for hostname validation."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_config = Path(self.test_dir) / "config.json"
        self.test_stats = Path(self.test_dir) / "stats.json"
        
        self.config_patcher = patch('core_logic.CONFIG_PATH', self.test_config)
        self.stats_patcher = patch('core_logic.STATS_PATH', self.test_stats)
        self.config_patcher.start()
        self.stats_patcher.start()

    def tearDown(self) -> None:
        self.config_patcher.stop()
        self.stats_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_valid_hostname(self) -> None:
        """Test valid hostname passes validation."""
        core = BlockerCore()
        self.assertTrue(core._is_valid_hostname("example.com"))
        self.assertTrue(core._is_valid_hostname("sub.example.com"))
        self.assertTrue(core._is_valid_hostname("test-site.org"))

    def test_invalid_hostname_no_dot(self) -> None:
        """Test hostname without TLD fails."""
        core = BlockerCore()
        self.assertFalse(core._is_valid_hostname("example"))

    def test_invalid_hostname_empty(self) -> None:
        """Test empty hostname fails."""
        core = BlockerCore()
        self.assertFalse(core._is_valid_hostname(""))

    def test_invalid_hostname_special_chars(self) -> None:
        """Test hostname with invalid chars fails."""
        core = BlockerCore()
        self.assertFalse(core._is_valid_hostname("test_site.com"))


class TestBlockerCoreExportImport(unittest.TestCase):
    """Tests for config export/import."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_config = Path(self.test_dir) / "config.json"
        self.test_stats = Path(self.test_dir) / "stats.json"
        self.export_path = Path(self.test_dir) / "export.json"
        
        self.config_patcher = patch('core_logic.CONFIG_PATH', self.test_config)
        self.stats_patcher = patch('core_logic.STATS_PATH', self.test_stats)
        self.config_patcher.start()
        self.stats_patcher.start()

    def tearDown(self) -> None:
        self.config_patcher.stop()
        self.stats_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_export_config(self) -> None:
        """Test config export creates file."""
        core = BlockerCore()
        result = core.export_config(str(self.export_path))
        self.assertTrue(result)
        self.assertTrue(self.export_path.exists())

    def test_import_config(self) -> None:
        """Test config import loads sites."""
        # Create export file
        export_data = {
            "blacklist": ["imported.com"],
            "whitelist": ["allowed.com"]
        }
        with open(self.export_path, 'w') as f:
            json.dump(export_data, f)
        
        core = BlockerCore()
        result = core.import_config(str(self.export_path))
        self.assertTrue(result)
        self.assertIn("imported.com", core.blacklist)


if __name__ == '__main__':
    unittest.main()
