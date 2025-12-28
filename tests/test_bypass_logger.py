"""Tests for the bypass_logger module."""
import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestBypassLogger:
    """Tests for the BypassLogger class."""

    @pytest.fixture
    def temp_log_path(self, tmp_path):
        """Create a temporary log path."""
        return tmp_path / "bypass_attempts.json"

    @pytest.fixture
    def logger(self, temp_log_path, monkeypatch):
        """Create a BypassLogger with temporary path."""
        import bypass_logger
        monkeypatch.setattr(bypass_logger, 'BYPASS_LOG_PATH', temp_log_path)
        # Reset singleton
        bypass_logger._bypass_logger_instance = None
        return bypass_logger.BypassLogger()

    def test_init_creates_default_structure(self, logger):
        """Test that initialization creates default attempts structure."""
        assert logger.attempts["total_attempts"] == 0
        assert logger.attempts["attempts_by_site"] == {}
        assert len(logger.attempts["attempts_by_hour"]) == 24
        assert logger.attempts["daily_attempts"] == {}
        assert logger.attempts["session_history"] == []

    def test_init_loads_existing_data(self, temp_log_path, monkeypatch):
        """Test that initialization loads existing data from file."""
        import bypass_logger
        monkeypatch.setattr(bypass_logger, 'BYPASS_LOG_PATH', temp_log_path)
        
        # Create existing data
        existing_data = {
            "total_attempts": 5,
            "attempts_by_site": {"example.com": 3},
            "attempts_by_hour": {str(i): 0 for i in range(24)},
            "daily_attempts": {"2024-01-01": 5},
            "session_history": []
        }
        temp_log_path.write_text(json.dumps(existing_data))
        
        logger = bypass_logger.BypassLogger()
        assert logger.attempts["total_attempts"] == 5
        assert logger.attempts["attempts_by_site"]["example.com"] == 3

    def test_init_handles_corrupted_file(self, temp_log_path, monkeypatch):
        """Test that initialization handles corrupted JSON file."""
        import bypass_logger
        monkeypatch.setattr(bypass_logger, 'BYPASS_LOG_PATH', temp_log_path)
        
        temp_log_path.write_text("not valid json {{{")
        
        logger = bypass_logger.BypassLogger()
        # Should fall back to default structure
        assert logger.attempts["total_attempts"] == 0

    def test_log_attempt_increments_total(self, logger):
        """Test that logging an attempt increments total count."""
        logger.log_attempt("facebook.com", "/")
        assert logger.attempts["total_attempts"] == 1
        
        logger.log_attempt("twitter.com", "/home")
        assert logger.attempts["total_attempts"] == 2

    def test_log_attempt_tracks_by_site(self, logger):
        """Test that attempts are tracked per site."""
        logger.log_attempt("facebook.com")
        logger.log_attempt("facebook.com")
        logger.log_attempt("twitter.com")
        
        assert logger.attempts["attempts_by_site"]["facebook.com"] == 2
        assert logger.attempts["attempts_by_site"]["twitter.com"] == 1

    def test_log_attempt_strips_port(self, logger):
        """Test that port is stripped from site name."""
        logger.log_attempt("facebook.com:443")
        assert "facebook.com" in logger.attempts["attempts_by_site"]
        assert "facebook.com:443" not in logger.attempts["attempts_by_site"]

    def test_log_attempt_tracks_by_hour(self, logger):
        """Test that attempts are tracked by hour."""
        current_hour = str(datetime.now().hour)
        logger.log_attempt("example.com")
        
        assert logger.attempts["attempts_by_hour"][current_hour] >= 1

    def test_log_attempt_tracks_by_day(self, logger):
        """Test that attempts are tracked by day."""
        today = datetime.now().strftime("%Y-%m-%d")
        logger.log_attempt("example.com")
        
        assert logger.attempts["daily_attempts"][today] == 1

    def test_log_attempt_adds_to_current_session(self, logger):
        """Test that attempts are added to current session list."""
        assert len(logger.current_session_attempts) == 0
        
        logger.log_attempt("example.com", "/path")
        
        assert len(logger.current_session_attempts) == 1
        assert logger.current_session_attempts[0]["site"] == "example.com"
        assert logger.current_session_attempts[0]["path"] == "/path"

    def test_log_attempt_saves_periodically(self, logger, temp_log_path, monkeypatch):
        """Test that attempts are saved every 5 attempts."""
        import bypass_logger
        monkeypatch.setattr(bypass_logger, 'BYPASS_LOG_PATH', temp_log_path)
        
        # Log 4 attempts - should not save yet
        for i in range(4):
            logger.log_attempt(f"site{i}.com")
        
        # Log 5th attempt - should save
        logger.log_attempt("site5.com")
        
        # Verify file was created
        assert temp_log_path.exists()

    def test_get_statistics_empty(self, logger):
        """Test statistics with no attempts."""
        stats = logger.get_statistics()
        
        assert stats["total_attempts"] == 0
        assert stats["top_sites"] == []
        assert stats["current_session"] == 0

    def test_get_statistics_with_data(self, logger):
        """Test statistics with recorded attempts."""
        logger.log_attempt("facebook.com")
        logger.log_attempt("facebook.com")
        logger.log_attempt("twitter.com")
        
        stats = logger.get_statistics()
        
        assert stats["total_attempts"] == 3
        assert stats["top_sites"][0] == ("facebook.com", 2)
        assert stats["current_session"] == 3
        assert "facebook.com" in stats["session_sites"]

    def test_get_statistics_recent_trend(self, logger):
        """Test that recent trend includes last 7 days."""
        stats = logger.get_statistics()
        
        assert len(stats["recent_trend"]) == 7

    def test_get_insights_no_attempts(self, logger):
        """Test insights with no attempts."""
        insights = logger.get_insights()
        
        assert len(insights) == 1
        assert "Great focus" in insights[0]

    def test_get_insights_with_attempts(self, logger):
        """Test insights with recorded attempts."""
        for _ in range(5):
            logger.log_attempt("facebook.com")
        
        insights = logger.get_insights()
        
        assert any("facebook.com" in i for i in insights)

    def test_stop_server_saves_session_summary(self, logger):
        """Test that stopping server saves session summary."""
        # Simulate having a server to stop with a mock
        mock_server = MagicMock()
        logger.server = mock_server
        logger.log_attempt("facebook.com")
        logger.log_attempt("twitter.com")
        
        logger.stop_server()
        
        assert len(logger.attempts["session_history"]) == 1
        assert logger.attempts["session_history"][0]["attempt_count"] == 2

    def test_stop_server_clears_current_session(self, logger):
        """Test that stopping server clears current session."""
        # Simulate having a server to stop with a mock
        mock_server = MagicMock()
        logger.server = mock_server
        logger.log_attempt("example.com")
        assert len(logger.current_session_attempts) == 1
        
        logger.stop_server()
        
        assert len(logger.current_session_attempts) == 0

    def test_stop_server_limits_session_history(self, logger):
        """Test that session history is limited to 100 entries."""
        # Pre-fill with 100 sessions
        logger.attempts["session_history"] = [{"date": "2024-01-01", "attempt_count": 1, "sites": []}] * 100
        
        logger.log_attempt("example.com")
        logger.stop_server()
        
        assert len(logger.attempts["session_history"]) == 100


class TestBypassAttemptHandler:
    """Tests for the BypassAttemptHandler class."""

    def test_generate_reminder_page_contains_site(self):
        """Test that reminder page contains the blocked site."""
        from bypass_logger import BypassAttemptHandler
        
        handler = MagicMock(spec=BypassAttemptHandler)
        html = BypassAttemptHandler._generate_reminder_page(handler, "facebook.com")
        
        assert "facebook.com" in html
        assert "Stay Focused" in html

    def test_log_message_suppressed(self):
        """Test that default logging is suppressed."""
        from bypass_logger import BypassAttemptHandler
        
        handler = MagicMock(spec=BypassAttemptHandler)
        # Should not raise any exceptions
        BypassAttemptHandler.log_message(handler, "%s", "test")


class TestGetBypassLogger:
    """Tests for the get_bypass_logger function."""

    def test_returns_singleton(self, tmp_path, monkeypatch):
        """Test that get_bypass_logger returns a singleton."""
        import bypass_logger
        monkeypatch.setattr(bypass_logger, 'BYPASS_LOG_PATH', tmp_path / "log.json")
        bypass_logger._bypass_logger_instance = None
        
        logger1 = bypass_logger.get_bypass_logger()
        logger2 = bypass_logger.get_bypass_logger()
        
        assert logger1 is logger2
