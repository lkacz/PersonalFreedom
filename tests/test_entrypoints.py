"""Tests for executable entrypoint wiring."""

from focus_blocker import main as legacy_main
from focus_blocker_qt import main as qt_main


def test_legacy_focus_blocker_shim_points_to_qt_main() -> None:
    """Legacy module entrypoint should resolve to the Qt app main function."""
    assert callable(legacy_main)
    assert legacy_main is qt_main

