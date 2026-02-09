"""Regression tests for persistence and save-ordering fixes."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from focus_blocker_qt import FocusBlockerWindow
from game_state import GameStateManager
from gamification import get_bookmark_entity_status


class _FakeProgress:
    def __init__(self, *, has_normal: bool, has_exceptional: bool, saved_count: int):
        self._has_normal = has_normal
        self._has_exceptional = has_exceptional
        self._saved_count = saved_count

    def is_collected(self, _entity_id: str) -> bool:
        return self._has_normal

    def is_exceptional(self, _entity_id: str) -> bool:
        return self._has_exceptional

    def get_saved_encounter_count(self) -> int:
        return self._saved_count


class _FakeManager:
    def __init__(self, progress: _FakeProgress):
        self.progress = progress


def test_bookmark_status_includes_current_saved_count():
    """Bookmark status should expose current saved encounter count for UI/cost logic."""
    fake_manager = _FakeManager(
        _FakeProgress(has_normal=True, has_exceptional=False, saved_count=7)
    )

    with patch("gamification.get_entitidex_manager", return_value=fake_manager):
        status = get_bookmark_entity_status({})

    assert status["current_saved"] == 7
    assert status["has_normal"] is True
    assert status["has_exceptional"] is False


def test_force_save_syncs_hero_data_before_saving():
    """force_save should run hero sync then persist config."""
    blocker = Mock()
    blocker.adhd_buster = {"coins": 10, "inventory": [], "equipped": {}}
    blocker.save_config = Mock()

    state = GameStateManager(blocker)

    with patch("gamification.sync_hero_data") as sync_hero_data:
        state.force_save()

    sync_hero_data.assert_called_once_with(blocker.adhd_buster)
    blocker.save_config.assert_called_once()


def test_force_save_still_saves_if_sync_raises():
    """force_save should not skip persistence if hero sync fails."""
    blocker = Mock()
    blocker.adhd_buster = {"coins": 10, "inventory": [], "equipped": {}}
    blocker.save_config = Mock()

    state = GameStateManager(blocker)

    with patch("gamification.sync_hero_data", side_effect=RuntimeError("boom")):
        state.force_save()

    blocker.save_config.assert_called_once()


def test_flush_persistent_state_prefers_game_state_force_save():
    """Window flush should use GameState force_save when available and not batched."""
    blocker = Mock()
    game_state = Mock()
    game_state._batch_depth = 0
    target = SimpleNamespace(blocker=blocker, game_state=game_state)

    FocusBlockerWindow._flush_persistent_state(target)

    game_state.force_save.assert_called_once()
    blocker.save_config.assert_not_called()
    blocker.save_stats.assert_called_once()


def test_flush_persistent_state_falls_back_to_config_during_batch():
    """Window flush should avoid force_save mid-batch and fallback to save_config."""
    blocker = Mock()
    game_state = Mock()
    game_state._batch_depth = 1
    target = SimpleNamespace(blocker=blocker, game_state=game_state)

    FocusBlockerWindow._flush_persistent_state(target)

    game_state.force_save.assert_not_called()
    blocker.save_config.assert_called_once()
    blocker.save_stats.assert_called_once()


def test_flush_persistent_state_without_game_state_uses_config_fallback():
    """Window flush should persist config/stats even when GameState is missing."""
    blocker = Mock()
    target = SimpleNamespace(blocker=blocker, game_state=None)

    FocusBlockerWindow._flush_persistent_state(target)

    blocker.save_config.assert_called_once()
    blocker.save_stats.assert_called_once()


def test_flush_persistent_state_fallbacks_when_force_save_fails():
    """Window flush should still save config/stats if GameState force_save fails."""
    blocker = Mock()
    game_state = Mock()
    game_state._batch_depth = 0
    game_state.force_save.side_effect = RuntimeError("boom")
    target = SimpleNamespace(blocker=blocker, game_state=game_state)

    FocusBlockerWindow._flush_persistent_state(target)

    game_state.force_save.assert_called_once()
    blocker.save_config.assert_called_once()
    blocker.save_stats.assert_called_once()
