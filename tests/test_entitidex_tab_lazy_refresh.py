"""Regression tests for EntitidexTab lazy-init refresh safety."""

from entitidex_tab import EntitidexTab


class _DummyBlocker:
    def __init__(self):
        self.adhd_buster = {}

    def save_config(self):
        pass


def test_refresh_before_ui_build_does_not_crash(qtbot):
    """refresh() must be safe before Entitidex UI widgets are created."""
    blocker = _DummyBlocker()
    tab = EntitidexTab(blocker)
    qtbot.addWidget(tab)

    # No full UI yet (lazy-init path): this used to crash with missing label attrs.
    assert not hasattr(tab, "total_progress_label")

    tab.refresh()
    tab.reload_data()
    tab._on_story_changed("scholar")

    # Progress mutations should still work even when UI is not built yet.
    tab.add_encountered_entity("warrior_001")
    assert tab.progress.get_encounter_count("warrior_001") == 1
