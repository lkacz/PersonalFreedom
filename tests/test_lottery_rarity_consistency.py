import os

import pytest
from PySide6 import QtWidgets


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_merge_tier_upgrade_keeps_animation_and_award_in_sync(monkeypatch, qapp):
    import merge_dialog
    from merge_dialog import LuckyMergeDialog

    captured_animation_kwargs = {}

    class DummyMergeLotteryDialog:
        def __init__(self, *args, **kwargs):
            captured_animation_kwargs.update(kwargs)

        def exec_(self):
            return QtWidgets.QDialog.Accepted

        def get_results(self):
            return True, "Epic"

    def fake_perform_lucky_merge(items, **kwargs):
        return {
            "success": True,
            "items_lost": list(items),
            "roll": 0.12,
            "needed": 0.74,
            "tier_roll": 83.5,
            "rolled_tier": "Epic",
            "tier_weights": [5, 10, 25, 45, 15],
            "base_rarity": "Rare",
            "tier_upgraded": True,
            "tier_jump": 2,
            "legendary_count": 11,
            "celestial_chance": 0.07,
            "celestial_triggered": False,
            "final_rarity": "Epic",
            "result_item": {
                "name": "Epic Test Item",
                "rarity": "Epic",
                "slot": "weapon",
                "power": 100,
            },
        }

    items = [
        {"name": "Item A", "rarity": "Common", "slot": "weapon"},
        {"name": "Item B", "rarity": "Uncommon", "slot": "helmet"},
    ]
    adhd_buster = {
        "coins": 1000,
        "inventory": [],
        "equipped": {},
        "entitidex": {"collected_entity_ids": [], "exceptional_entities": {}},
    }

    dialog = LuckyMergeDialog(items, 0, {}, player_coins=1000, adhd_buster=adhd_buster)
    dialog.tier_upgrade_enabled = True
    dialog._show_result = lambda: None

    monkeypatch.setattr(merge_dialog, "MergeTwoStageLotteryDialog", DummyMergeLotteryDialog)
    monkeypatch.setattr(merge_dialog, "perform_lucky_merge", fake_perform_lucky_merge)

    dialog.execute_merge()

    assert dialog.merge_result["success"] is True
    assert dialog.merge_result["final_rarity"] == "Epic"
    assert dialog.merge_result["result_item"]["rarity"] == "Epic"
    assert dialog.merge_result["tier_upgraded"] is True
    assert captured_animation_kwargs["rolled_tier"] == "Epic"
    assert captured_animation_kwargs["tier_roll"] == 83.5
    assert captured_animation_kwargs["celestial_chance"] == 0.07
    assert captured_animation_kwargs["legendary_count"] == 11
    assert captured_animation_kwargs["final_rarity"] == "Epic"


def test_merge_tier_slider_displays_celestial_zone_when_unlocked(qapp):
    from lottery_animation import MergeTierSliderWidget

    slider = MergeTierSliderWidget(
        result_rarity="Legendary",
        upgraded=False,
        celestial_chance=0.07,
    )
    zones = slider.get_display_zone_weights()

    zone_map = {name: pct for name, pct in zones}
    assert "Celestial" in zone_map
    assert zone_map["Celestial"] == pytest.approx(7.0, abs=0.01)
    assert sum(zone_map.values()) == pytest.approx(100.0, abs=0.01)


def test_activity_lottery_can_reveal_pre_awarded_item_without_rarity_drift(qapp):
    from lottery_animation import ActivityLotteryDialog

    pre_awarded_item = {
        "name": "Legendary Fixed Reward",
        "rarity": "Legendary",
        "slot": "weapon",
        "power": 250,
    }

    dialog = ActivityLotteryDialog(
        effective_minutes=45,
        pre_rolled_rarity="Rare",
        story_id="warrior",
        item=pre_awarded_item,
    )

    dialog._finish_animation()
    rolled_tier, resolved_item = dialog.get_results()

    assert rolled_tier == "Legendary"
    assert resolved_item is pre_awarded_item


def test_activity_lottery_120_minute_display_is_guaranteed_top_tier(qapp):
    from lottery_animation import ActivityLotteryDialog

    dialog = ActivityLotteryDialog(
        effective_minutes=130,
        pre_rolled_rarity="Legendary",
        story_id="warrior",
        item={"name": "Guaranteed", "rarity": "Legendary", "slot": "weapon", "power": 1},
    )

    assert dialog.tier_weights == [0, 0, 0, 0, 100]


def test_focus_slider_can_use_backend_distribution_weights(qapp):
    from gamification import get_focus_rarity_distribution
    from lottery_animation import FocusTimerTierSliderWidget

    distribution = get_focus_rarity_distribution(session_minutes=60, streak_days=60, adhd_buster={})
    slider = FocusTimerTierSliderWidget(
        session_minutes=60,
        streak_days=60,
        tier_weights=distribution["weights"],
    )

    assert slider.zone_widths == distribution["weights"]
