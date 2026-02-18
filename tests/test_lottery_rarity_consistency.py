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

    captured_animation_args = ()
    captured_animation_kwargs = {}
    captured_backend_kwargs = {}

    class DummyMergeLotteryDialog:
        def __init__(self, *args, **kwargs):
            nonlocal captured_animation_args
            captured_animation_args = args
            captured_animation_kwargs.update(kwargs)
            # Animation is now canonical for rolls.
            self.success_roll = 0.12
            self.tier_roll = 83.5
            self.celestial_roll = 0.91

        def exec_(self):
            return QtWidgets.QDialog.Accepted

        def get_results(self):
            return True, "Epic"

    def fake_perform_lucky_merge(items, **kwargs):
        captured_backend_kwargs.update(kwargs)
        return {
            "success": True,
            "items_lost": list(items),
            "roll": kwargs.get("success_roll", 0.12),
            "needed": 0.74,
            "tier_roll": kwargs.get("tier_roll", 83.5),
            "rolled_tier": "Epic",
            "tier_weights": [5, 10, 25, 45, 15],
            "base_rarity": "Rare",
            "tier_upgraded": True,
            "tier_jump": 2,
            "legendary_count": 11,
            "celestial_chance": 0.07,
            "celestial_roll": kwargs.get("celestial_roll"),
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
    assert captured_animation_args[0] == -1.0
    assert captured_animation_kwargs["tier_roll"] is None
    assert captured_animation_kwargs["celestial_chance"] == 0.0
    assert captured_animation_kwargs["legendary_count"] == 0
    assert captured_backend_kwargs["success_roll"] == pytest.approx(0.12)
    assert captured_backend_kwargs["tier_roll"] == pytest.approx(83.5)
    assert captured_backend_kwargs["celestial_roll"] == pytest.approx(0.91)


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


def test_merge_stage1_animation_uses_full_bar_with_celestial_lane(monkeypatch, qapp):
    from lottery_animation import MergeTwoStageLotteryDialog

    captured = {}

    def fake_animate_tier_stage(self, slider, result_label, target_roll, on_complete, max_position=100.0):
        captured["target_roll"] = target_roll
        captured["max_position"] = max_position

    monkeypatch.setattr(MergeTwoStageLotteryDialog, "_animate_tier_stage", fake_animate_tier_stage)

    dialog = MergeTwoStageLotteryDialog(
        success_roll=0.2,
        success_threshold=0.5,
        base_rarity="Legendary",
        tier_roll=80.0,
        rolled_tier="Legendary",
        celestial_chance=0.32,
        legendary_count=36,
    )

    dialog._start_stage_1()

    assert captured["target_roll"] < 100.0
    assert captured["max_position"] == pytest.approx(100.0, abs=0.001)
    dialog.close()


def test_merge_stage1_can_target_celestial_lane_when_triggered(monkeypatch, qapp):
    from lottery_animation import MergeTwoStageLotteryDialog

    captured = {}

    def fake_animate_tier_stage(self, slider, result_label, target_roll, on_complete, max_position=100.0):
        captured["target_roll"] = target_roll
        captured["max_position"] = max_position
        captured["tier_at_target"] = slider.get_tier_at_position(target_roll)
        captured["base_lane_end"] = slider.get_base_display_scale() * 100.0

    monkeypatch.setattr(MergeTwoStageLotteryDialog, "_animate_tier_stage", fake_animate_tier_stage)

    dialog = MergeTwoStageLotteryDialog(
        success_roll=0.2,
        success_threshold=0.5,
        base_rarity="Legendary",
        tier_roll=95.0,
        rolled_tier="Legendary",
        celestial_chance=0.32,
        legendary_count=36,
        celestial_triggered=True,
        celestial_roll=0.75,
        final_rarity="Celestial",
    )

    dialog._start_stage_1()

    assert captured["target_roll"] > captured["base_lane_end"]
    assert captured["target_roll"] <= 100.001
    assert captured["tier_at_target"] == "Celestial"
    assert captured["max_position"] == pytest.approx(100.0, abs=0.001)
    dialog.close()


def test_merge_stage1_omits_redundant_distribution_legend_row(qapp):
    from lottery_animation import MergeTwoStageLotteryDialog

    dialog = MergeTwoStageLotteryDialog(
        success_roll=0.2,
        success_threshold=0.5,
        base_rarity="Legendary",
        tier_roll=80.0,
        rolled_tier="Legendary",
        celestial_chance=0.32,
        legendary_count=36,
    )

    # Title, slider, result label (no redundant rarity text row).
    assert dialog.stage1_frame.layout().count() == 3
    dialog.close()


def test_merge_stage1_treats_near_full_ceiling_as_full_for_celestial_lane(monkeypatch, qapp):
    import lottery_animation
    from lottery_animation import MergeTwoStageLotteryDialog

    captured = {}

    monkeypatch.setattr(
        lottery_animation,
        "_extract_power_gate_ui_state",
        lambda _gating: (set(), 99.9995, ""),
    )

    def fake_animate_tier_stage(self, slider, result_label, target_roll, on_complete, max_position=100.0):
        captured["max_position"] = max_position

    monkeypatch.setattr(MergeTwoStageLotteryDialog, "_animate_tier_stage", fake_animate_tier_stage)

    dialog = MergeTwoStageLotteryDialog(
        success_roll=0.2,
        success_threshold=0.5,
        base_rarity="Legendary",
        tier_roll=80.0,
        rolled_tier="Legendary",
        celestial_chance=0.32,
        legendary_count=36,
    )

    dialog._start_stage_1()

    assert captured["max_position"] == pytest.approx(100.0, abs=0.001)
    dialog.close()


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


def test_activity_lottery_dialog_generates_canonical_rolls_for_backend(monkeypatch, qapp):
    import lottery_animation
    from lottery_animation import ActivityLotteryDialog

    observed = {}
    monkeypatch.setattr(lottery_animation.random, "random", lambda: 0.37)

    def fake_roll_activity_reward_outcome(effective_minutes, roll=None, adhd_buster=None):
        observed["effective_minutes"] = effective_minutes
        observed["roll"] = roll
        return {
            "rarity": "Epic",
            "roll": roll,
            "weights": [5, 15, 60, 15, 5],
            "power_gating": {},
        }

    monkeypatch.setattr("gamification.roll_activity_reward_outcome", fake_roll_activity_reward_outcome)
    monkeypatch.setattr(
        "gamification.generate_item",
        lambda rarity, story_id=None: {"name": "Activity Reward", "rarity": rarity, "slot": "weapon", "power": 44},
    )

    dialog = ActivityLotteryDialog(
        effective_minutes=45.0,
        pre_rolled_rarity="Rare",
        story_id="warrior",
        adhd_buster={},
    )

    assert observed["effective_minutes"] == pytest.approx(45.0, abs=1e-9)
    assert observed["roll"] == pytest.approx(37.0, abs=1e-9)
    assert dialog.tier_roll == pytest.approx(37.0, abs=1e-9)
    assert dialog.rolled_tier == "Epic"
    assert dialog.item.get("rarity") == "Epic"
    dialog.close()


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


def test_focus_lottery_dialog_generates_canonical_rolls_for_backend(monkeypatch, qapp):
    import lottery_animation
    from lottery_animation import FocusTimerLotteryDialog

    observed = {}
    monkeypatch.setattr(lottery_animation.random, "random", lambda: 0.42)

    def fake_roll_focus_reward_outcome(session_minutes=0, streak_days=0, adhd_buster=None, roll=None):
        observed["session_minutes"] = session_minutes
        observed["streak_days"] = streak_days
        observed["roll"] = roll
        return {
            "rarity": "Rare",
            "roll": roll,
            "weights": [30, 30, 25, 10, 5],
            "rarities": ["Common", "Uncommon", "Rare", "Epic", "Legendary"],
            "power_gating": {},
        }

    monkeypatch.setattr("gamification.roll_focus_reward_outcome", fake_roll_focus_reward_outcome)
    monkeypatch.setattr(
        "gamification.generate_item",
        lambda rarity, story_id=None, adhd_buster=None: {
            "name": "Focus Reward",
            "rarity": rarity,
            "slot": "weapon",
            "power": 77,
        },
    )

    dialog = FocusTimerLotteryDialog(
        session_minutes=50,
        streak_days=4,
        story_id="warrior",
        adhd_buster={},
    )

    assert observed["session_minutes"] == 50
    assert observed["streak_days"] == 4
    assert observed["roll"] == pytest.approx(42.0, abs=1e-9)
    assert dialog.tier_roll == pytest.approx(42.0, abs=1e-9)
    assert dialog.rolled_tier == "Rare"
    assert dialog.item.get("rarity") == "Rare"
    dialog.close()


def test_weight_lottery_dialog_generates_canonical_daily_rolls_for_backend(monkeypatch, qapp):
    import lottery_animation
    from lottery_animation import WeightLotteryDialog

    observed = {}
    monkeypatch.setattr(lottery_animation.random, "random", lambda: 0.58)

    def fake_roll_daily_weight_reward_outcome(weight_loss_grams, legendary_bonus=0, adhd_buster=None, roll=None):
        observed["weight_loss_grams"] = weight_loss_grams
        observed["legendary_bonus"] = legendary_bonus
        observed["roll"] = roll
        return {
            "rarity": "Epic",
            "roll": roll,
            "weights": [5, 15, 60, 15, 5],
            "power_gating": {},
        }

    monkeypatch.setattr("gamification.roll_daily_weight_reward_outcome", fake_roll_daily_weight_reward_outcome)
    monkeypatch.setattr(
        "gamification.generate_item",
        lambda rarity, story_id=None, adhd_buster=None: {
            "name": "Weight Reward",
            "rarity": rarity,
            "slot": "weapon",
            "power": 66,
        },
    )

    dialog = WeightLotteryDialog(
        item=None,
        reward_source="Daily Weigh-In",
        story_id="warrior",
        adhd_buster={},
        daily_progress_grams=230.0,
        daily_legendary_bonus=4,
    )

    assert observed["weight_loss_grams"] == pytest.approx(230.0, abs=1e-9)
    assert observed["legendary_bonus"] == 4
    assert observed["roll"] == pytest.approx(58.0, abs=1e-9)
    assert dialog.tier_roll == pytest.approx(58.0, abs=1e-9)
    assert dialog.rolled_tier == "Epic"
    assert dialog.item.get("rarity") == "Epic"
    dialog.close()


def test_water_lottery_dialog_generates_canonical_rolls_for_backend(monkeypatch, qapp):
    import lottery_animation
    from lottery_animation import WaterLotteryDialog

    observed = {}
    roll_stream = iter([0.25, 0.75])  # success_roll, tier_roll fraction
    monkeypatch.setattr(lottery_animation.random, "random", lambda: next(roll_stream))

    def fake_roll_water_reward_outcome(glass_number, success_roll=None, tier_roll=None, adhd_buster=None):
        observed["glass_number"] = glass_number
        observed["success_roll"] = success_roll
        observed["tier_roll"] = tier_roll
        return {
            "won": True,
            "success_roll": success_roll,
            "tier_roll": tier_roll,
            "rolled_tier": "Rare",
            "reward_tier": "Rare",
            "success_rate": 0.60,
            "power_gating": {},
        }

    monkeypatch.setattr("gamification.roll_water_reward_outcome", fake_roll_water_reward_outcome)
    monkeypatch.setattr(
        "gamification.generate_item",
        lambda rarity, story_id=None: {"name": "Generated", "rarity": rarity, "slot": "weapon", "power": 10},
    )

    dialog = WaterLotteryDialog(
        glass_number=3,
        lottery_attempts=0,
        story_id="warrior",
        adhd_buster={},
    )

    assert observed["glass_number"] == 3
    assert observed["success_roll"] == pytest.approx(0.25, abs=1e-9)
    assert observed["tier_roll"] == pytest.approx(75.0, abs=1e-9)
    assert dialog.win_roll == pytest.approx(0.25, abs=1e-9)
    assert dialog.tier_roll == pytest.approx(75.0, abs=1e-9)
    dialog.close()


def test_priority_lottery_dialog_generates_canonical_rolls_for_backend(monkeypatch, qapp):
    import lottery_animation
    from lottery_animation import PriorityLotteryDialog

    observed = {}
    roll_stream = iter([0.11, 0.66])  # win_roll, rarity_roll fraction
    monkeypatch.setattr(lottery_animation.random, "random", lambda: next(roll_stream))

    def fake_roll_priority_completion_reward(
        story_id=None,
        logged_hours=0,
        adhd_buster=None,
        win_roll_override=None,
        rarity_roll_override=None,
    ):
        observed["story_id"] = story_id
        observed["logged_hours"] = logged_hours
        observed["win_roll_override"] = win_roll_override
        observed["rarity_roll_override"] = rarity_roll_override
        return {
            "won": True,
            "chance": 57,
            "win_roll": win_roll_override,
            "rarity_roll": rarity_roll_override,
            "rarity": "Epic",
            "item": {"name": "Epic Reward", "rarity": "Epic", "slot": "weapon", "power": 120},
            "power_gating": {},
        }

    monkeypatch.setattr("gamification.roll_priority_completion_reward", fake_roll_priority_completion_reward)

    dialog = PriorityLotteryDialog(
        win_chance=0.57,
        priority_title="Test Priority",
        logged_hours=10.0,
        story_id="warrior",
        adhd_buster={},
    )

    assert observed["story_id"] == "warrior"
    assert observed["logged_hours"] == pytest.approx(10.0, abs=1e-9)
    assert observed["win_roll_override"] == pytest.approx(0.11, abs=1e-9)
    assert observed["rarity_roll_override"] == pytest.approx(66.0, abs=1e-9)
    assert dialog.win_roll == pytest.approx(0.11, abs=1e-9)
    assert dialog.rarity_roll == pytest.approx(66.0, abs=1e-9)
    assert dialog.won is True
    assert dialog.won_rarity == "Epic"
    dialog.close()
