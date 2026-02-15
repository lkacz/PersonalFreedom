"""Regression tests for hydration-related calculation paths."""

from datetime import datetime, timedelta
from unittest.mock import patch

from app_utils import get_activity_date
from gamification import (
    can_log_water,
    check_water_entry_reward,
    get_hydration_stats,
    get_water_reward_rarity,
    roll_water_reward_outcome,
)


def test_get_hydration_stats_respects_daily_goal() -> None:
    """Daily goal should drive target and streak math."""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    entries = [
        {"date": today, "glasses": 6},
        {"date": yesterday, "glasses": 6},
    ]

    stats_goal_6 = get_hydration_stats(entries, daily_goal=6)
    assert stats_goal_6["days_on_target"] == 2
    assert stats_goal_6["current_streak"] >= 2
    assert stats_goal_6["best_streak"] >= 2

    stats_goal_7 = get_hydration_stats(entries, daily_goal=7)
    assert stats_goal_7["days_on_target"] == 0
    assert stats_goal_7["current_streak"] == 0
    assert stats_goal_7["best_streak"] == 0


def test_get_hydration_stats_invalid_goal_falls_back() -> None:
    """Invalid daily goals should fall back to safe defaults."""
    today = datetime.now().strftime("%Y-%m-%d")
    entries = [{"date": today, "glasses": 5}]
    stats = get_hydration_stats(entries, daily_goal="invalid")
    assert stats["days_on_target"] == 1


def test_get_hydration_stats_does_not_bridge_gap_for_current_streak() -> None:
    """Current streak should break on missing day, even if older days are consecutive."""
    today = datetime.now().strftime("%Y-%m-%d")
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    entries = [
        {"date": today, "glasses": 5},
        {"date": two_days_ago, "glasses": 5},
        {"date": three_days_ago, "glasses": 5},
    ]

    stats = get_hydration_stats(entries, daily_goal=5)
    assert stats["current_streak"] == 1
    assert stats["best_streak"] == 2


def test_can_log_water_counts_glasses_field_for_cap() -> None:
    """Daily cap checks should use actual glasses totals, not entry count."""
    today = get_activity_date()
    entries = [
        {"date": today, "time": "08:00", "glasses": 4},
        {"date": today, "time": "10:30", "glasses": 1},
    ]

    result = can_log_water(entries, adhd_buster={})
    assert result["can_log"] is False
    assert result["glasses_today"] == 5


def test_get_hydration_stats_uses_activity_date_for_today_glasses() -> None:
    """today_glasses should respect activity-day cutoff, not calendar date."""
    entries = [
        {"date": "2026-02-01", "glasses": 3},
        {"date": "2026-01-31", "glasses": 5},
    ]
    with patch("app_utils.get_activity_date", return_value="2026-01-31"):
        stats = get_hydration_stats(entries, daily_goal=5)
    assert stats["today_glasses"] == 5


def test_check_water_entry_reward_uses_rolled_tier() -> None:
    """Water entry reward should use rolled_tier, not tuple payload."""
    with patch("gamification.get_water_reward_rarity", return_value=("Common", 0.99, "Epic")):
        result = check_water_entry_reward(glasses_today=0, streak_days=0, story_id="warrior")

    assert result["glass_reward"] is not None
    assert result["glass_reward"]["rarity"] == "Epic"


def test_check_water_entry_reward_handles_failed_roll() -> None:
    """Failed rarity roll should not create a glass reward item."""
    with patch("gamification.get_water_reward_rarity", return_value=("Rare", 0.2, None)):
        result = check_water_entry_reward(glasses_today=0, streak_days=0, story_id="warrior")

    assert result["glass_reward"] is None


def test_roll_water_reward_outcome_keeps_tier_roll_even_when_fail() -> None:
    """UI can still reveal the rolled tier even if the claim roll fails."""
    outcome = roll_water_reward_outcome(glass_number=5, success_roll=1.0, tier_roll=0.0)
    assert outcome["won"] is False
    assert outcome["rolled_tier"] is not None
    assert get_water_reward_rarity(glass_number=5, success_roll=1.0)[2] is None
