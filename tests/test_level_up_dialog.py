from __future__ import annotations

from level_up_dialog import EnhancedLevelUpDialog


def test_enhanced_level_up_dialog_constructs(qtbot):  # noqa: ANN001
    stats = {
        "total_power": 1234,
        "total_xp": 9876,
        "total_coins": 321,
        "productivity_score": 77,
        "total_focus_minutes": 120,
        "items_collected": 9,
        "unlocks": ["Test Unlock"],
        "rewards": None,
    }

    dialog = EnhancedLevelUpDialog(4, 5, stats, fullscreen=False, parent=None)
    qtbot.addWidget(dialog)

    assert dialog.old_level == 4
    assert dialog.new_level == 5
    dialog.close()
