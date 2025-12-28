"""Additional tests to increase coverage for core_logic.py"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import core_logic
from core_logic import BlockerCore, BlockMode, SITE_CATEGORIES


class TestBlockerCoreSessionState(unittest.TestCase):
    """Tests for session state management."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_config = Path(self.test_dir) / "config.json"
        self.test_stats = Path(self.test_dir) / "stats.json"
        self.test_session = Path(self.test_dir) / "session_state.json"
        
        self.config_patcher = patch('core_logic.CONFIG_PATH', self.test_config)
        self.stats_patcher = patch('core_logic.STATS_PATH', self.test_stats)
        self.session_patcher = patch('core_logic.SESSION_STATE_PATH', self.test_session)
        self.config_patcher.start()
        self.stats_patcher.start()
        self.session_patcher.start()

    def tearDown(self) -> None:
        self.config_patcher.stop()
        self.stats_patcher.stop()
        self.session_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_save_session_state_creates_file(self) -> None:
        """Test that save_session_state creates the session file."""
        core = BlockerCore()
        core.session_id = "test-session-123"
        core.mode = BlockMode.NORMAL
        core.save_session_state(3600)
        
        self.assertTrue(self.test_session.exists())

    def test_save_session_state_content(self) -> None:
        """Test that saved session state has correct content."""
        core = BlockerCore()
        core.session_id = "test-session-456"
        core.mode = BlockMode.STRICT
        core.save_session_state(1800)
        
        with open(self.test_session, 'r') as f:
            state = json.load(f)
        
        self.assertEqual(state["session_id"], "test-session-456")
        self.assertEqual(state["mode"], BlockMode.STRICT)
        self.assertEqual(state["planned_duration"], 1800)

    def test_clear_session_state_removes_file(self) -> None:
        """Test that clear_session_state removes the file."""
        core = BlockerCore()
        core.session_id = "test-session"
        core.save_session_state(3600)
        self.assertTrue(self.test_session.exists())
        
        core.clear_session_state()
        self.assertFalse(self.test_session.exists())

    def test_clear_session_state_no_file(self) -> None:
        """Test clear_session_state works when no file exists."""
        core = BlockerCore()
        # Should not raise
        core.clear_session_state()

    def test_check_orphaned_session_no_file(self) -> None:
        """Test check_orphaned_session returns None when no file."""
        core = BlockerCore()
        result = core.check_orphaned_session()
        self.assertIsNone(result)


class TestBlockerCoreBypassLogger(unittest.TestCase):
    """Tests for bypass logger integration."""
    
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

    def test_get_bypass_statistics_no_logger(self) -> None:
        """Test get_bypass_statistics when no logger."""
        core = BlockerCore()
        core.bypass_logger = None
        result = core.get_bypass_statistics()
        self.assertIsNone(result)

    def test_get_bypass_insights_no_logger(self) -> None:
        """Test get_bypass_insights when no logger."""
        core = BlockerCore()
        core.bypass_logger = None
        result = core.get_bypass_insights()
        self.assertEqual(result, [])

    def test_get_bypass_statistics_with_logger(self) -> None:
        """Test get_bypass_statistics delegates to logger."""
        core = BlockerCore()
        mock_logger = MagicMock()
        mock_logger.get_statistics.return_value = {"total_attempts": 5}
        core.bypass_logger = mock_logger
        
        result = core.get_bypass_statistics()
        
        mock_logger.get_statistics.assert_called_once()
        self.assertEqual(result["total_attempts"], 5)

    def test_get_bypass_insights_with_logger(self) -> None:
        """Test get_bypass_insights delegates to logger."""
        core = BlockerCore()
        mock_logger = MagicMock()
        mock_logger.get_insights.return_value = ["Insight 1", "Insight 2"]
        core.bypass_logger = mock_logger
        
        result = core.get_bypass_insights()
        
        mock_logger.get_insights.assert_called_once()
        self.assertEqual(len(result), 2)


class TestBlockerCoreCategories(unittest.TestCase):
    """Tests for category management."""
    
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

    def test_toggle_category_disables(self) -> None:
        """Test disabling a category removes its sites from effective blacklist."""
        core = BlockerCore()
        # Ensure facebook is not in custom blacklist
        if "facebook.com" in core.blacklist:
            core.blacklist.remove("facebook.com")
        if "www.facebook.com" in core.blacklist:
            core.blacklist.remove("www.facebook.com")
        # Disable Social Media
        core.categories_enabled["Social Media"] = False
        core.save_config()
        
        effective = core.get_effective_blacklist()
        # Facebook should not be in effective list when Social Media disabled
        # and not in custom blacklist
        self.assertNotIn("facebook.com", effective)

    def test_toggle_category_enables(self) -> None:
        """Test enabling a category adds its sites to effective blacklist."""
        core = BlockerCore()
        # Enable Social Media (should be enabled by default)
        core.categories_enabled["Social Media"] = True
        
        effective = core.get_effective_blacklist()
        self.assertIn("facebook.com", effective)

    def test_custom_site_included(self) -> None:
        """Test custom sites are included in effective blacklist."""
        core = BlockerCore()
        core.add_site("mydistractingsite.com")
        
        effective = core.get_effective_blacklist()
        self.assertIn("mydistractingsite.com", effective)


class TestBlockerCorePomodoro(unittest.TestCase):
    """Tests for Pomodoro functionality."""
    
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

    def test_default_pomodoro_settings(self) -> None:
        """Test default Pomodoro settings."""
        core = BlockerCore()
        self.assertEqual(core.pomodoro_work, 25)
        self.assertEqual(core.pomodoro_break, 5)
        self.assertEqual(core.pomodoro_long_break, 15)
        self.assertEqual(core.pomodoro_sessions_before_long, 4)

    def test_pomodoro_settings_persist(self) -> None:
        """Test Pomodoro settings persist across instances."""
        core1 = BlockerCore()
        core1.pomodoro_work = 30
        core1.pomodoro_break = 10
        core1.save_config()
        
        core2 = BlockerCore()
        self.assertEqual(core2.pomodoro_work, 30)
        self.assertEqual(core2.pomodoro_break, 10)

    def test_pomodoro_mode(self) -> None:
        """Test setting Pomodoro mode."""
        core = BlockerCore()
        core.mode = BlockMode.POMODORO
        self.assertEqual(core.mode, BlockMode.POMODORO)


class TestBlockerCoreDefaultStats(unittest.TestCase):
    """Tests for default stats structure."""
    
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

    def test_default_stats_structure(self) -> None:
        """Test default stats has correct structure."""
        core = BlockerCore()
        stats = core._default_stats()
        
        self.assertIn("total_focus_time", stats)
        self.assertIn("sessions_completed", stats)
        self.assertIn("sessions_cancelled", stats)
        self.assertIn("daily_stats", stats)
        self.assertIn("streak_days", stats)
        self.assertIn("last_session_date", stats)
        self.assertIn("best_streak", stats)

    def test_default_stats_values(self) -> None:
        """Test default stats values are zero."""
        core = BlockerCore()
        stats = core._default_stats()
        
        self.assertEqual(stats["total_focus_time"], 0)
        self.assertEqual(stats["sessions_completed"], 0)
        self.assertEqual(stats["sessions_cancelled"], 0)
        self.assertEqual(stats["streak_days"], 0)


class TestBlockerCoreURLCleaning(unittest.TestCase):
    """Tests for URL cleaning in add_site and add_to_whitelist."""
    
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

    def test_whitelist_strips_http(self) -> None:
        """Test whitelist strips http prefix."""
        core = BlockerCore()
        core.add_to_whitelist("http://allowed.com")
        self.assertIn("allowed.com", core.whitelist)

    def test_whitelist_strips_https(self) -> None:
        """Test whitelist strips https prefix."""
        core = BlockerCore()
        core.add_to_whitelist("https://allowed.com")
        self.assertIn("allowed.com", core.whitelist)

    def test_whitelist_strips_path(self) -> None:
        """Test whitelist strips URL path."""
        core = BlockerCore()
        core.add_to_whitelist("allowed.com/some/path")
        self.assertIn("allowed.com", core.whitelist)

    def test_remove_from_whitelist_success(self) -> None:
        """Test removing from whitelist."""
        core = BlockerCore()
        core.add_to_whitelist("allowed.com")
        result = core.remove_from_whitelist("allowed.com")
        self.assertTrue(result)
        self.assertNotIn("allowed.com", core.whitelist)

    def test_remove_from_whitelist_not_found(self) -> None:
        """Test removing non-existent site from whitelist."""
        core = BlockerCore()
        result = core.remove_from_whitelist("notinlist.com")
        self.assertFalse(result)


class TestBlockerCoreFlushDNS(unittest.TestCase):
    """Tests for DNS flushing."""
    
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

    @patch('subprocess.run')
    def test_flush_dns_calls_ipconfig(self, mock_run) -> None:
        """Test _flush_dns calls ipconfig."""
        core = BlockerCore()
        core._flush_dns()
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertIn('/flushdns', call_args[0][0])

    @patch('subprocess.run', side_effect=Exception("DNS error"))
    def test_flush_dns_handles_error(self, mock_run) -> None:
        """Test _flush_dns handles errors gracefully."""
        core = BlockerCore()
        # Should not raise
        core._flush_dns()


class TestBlockerCoreModes(unittest.TestCase):
    """Tests for different blocking modes."""
    
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

    def test_block_mode_constants(self) -> None:
        """Test BlockMode constants."""
        self.assertEqual(BlockMode.NORMAL, "normal")
        self.assertEqual(BlockMode.STRICT, "strict")
        self.assertEqual(BlockMode.POMODORO, "pomodoro")
        self.assertEqual(BlockMode.SCHEDULED, "scheduled")

    def test_set_strict_mode(self) -> None:
        """Test setting strict mode."""
        core = BlockerCore()
        core.mode = BlockMode.STRICT
        self.assertEqual(core.mode, BlockMode.STRICT)


class TestBlockerCoreStatsUpdate(unittest.TestCase):
    """Tests for stats update functionality."""
    
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

    def test_update_stats_daily_entry(self) -> None:
        """Test update_stats creates daily entry."""
        core = BlockerCore()
        core.update_stats(1500, completed=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertIn(today, core.stats["daily_stats"])

    def test_stats_summary_format(self) -> None:
        """Test get_stats_summary returns correct format."""
        core = BlockerCore()
        core.update_stats(3600, completed=True)
        
        summary = core.get_stats_summary()
        
        # Check for expected keys in summary
        self.assertIsInstance(summary, dict)
        self.assertTrue(len(summary) > 0)


if __name__ == '__main__':
    unittest.main()
