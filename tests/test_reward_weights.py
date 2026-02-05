"""Tests for reward weight helpers (sleep and weight)."""

from gamification import (
    get_sleep_reward_weights,
    get_screen_off_bonus_weights,
    check_weight_entry_rewards,
)


def test_sleep_reward_weights_legendary() -> None:
    # 97+ score should be 100% Legendary
    weights = get_sleep_reward_weights(97)
    assert weights == [0, 0, 0, 0, 100]


def test_screen_off_bonus_weights_legendary() -> None:
    # 21:00-21:30 should be 100% Legendary
    weights = get_screen_off_bonus_weights("21:10")
    assert weights == [0, 0, 0, 0, 100]


def test_daily_weight_reward_weights_with_floor() -> None:
    # Weight loss progress with base rarity Rare should fold lower tiers into Rare.
    weight_entries = [{"date": "2025-01-01", "weight": 100.0}]
    result = check_weight_entry_rewards(
        weight_entries=weight_entries,
        new_weight=99.8,  # 200g loss
        current_date="2025-01-02",
        story_id="warrior",
        adhd_buster=None,
        height_cm=None,
        goal_weight=None,
    )
    assert result["daily_reward_weights"] == [0, 0, 75, 20, 5]
