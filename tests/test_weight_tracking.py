"""Tests for weight tracking gamification features."""

import pytest
from datetime import datetime, timedelta

# Import gamification weight functions
from gamification import (
    get_weight_from_date,
    get_closest_weight_before_date,
    get_previous_weight_entry,
    calculate_weight_loss,
    get_daily_weight_reward_rarity,
    check_weight_entry_rewards,
    get_weight_stats,
    format_weight_change,
    WEIGHT_DAILY_THRESHOLDS,
    WEIGHT_WEEKLY_LEGENDARY_THRESHOLD,
    WEIGHT_MONTHLY_LEGENDARY_THRESHOLD,
)


class TestWeightHelperFunctions:
    """Test weight tracking helper functions."""

    def test_get_weight_from_date_found(self):
        """Test finding weight for a specific date."""
        entries = [
            {"date": "2026-01-05", "weight": 80.0},
            {"date": "2026-01-06", "weight": 79.5},
            {"date": "2026-01-07", "weight": 79.2},
        ]
        assert get_weight_from_date(entries, "2026-01-06") == 79.5

    def test_get_weight_from_date_not_found(self):
        """Test weight lookup for missing date."""
        entries = [{"date": "2026-01-05", "weight": 80.0}]
        assert get_weight_from_date(entries, "2026-01-10") is None

    def test_get_closest_weight_before_date(self):
        """Test finding closest weight entry before a date."""
        entries = [
            {"date": "2026-01-01", "weight": 82.0},
            {"date": "2026-01-03", "weight": 81.0},
            {"date": "2026-01-05", "weight": 80.0},
        ]
        result = get_closest_weight_before_date(entries, "2026-01-04")
        assert result["date"] == "2026-01-03"
        assert result["weight"] == 81.0

    def test_get_closest_weight_before_date_exact_match(self):
        """Test closest weight when date matches exactly."""
        entries = [
            {"date": "2026-01-05", "weight": 80.0},
        ]
        result = get_closest_weight_before_date(entries, "2026-01-05")
        assert result["date"] == "2026-01-05"

    def test_get_closest_weight_before_date_empty(self):
        """Test closest weight with no entries."""
        assert get_closest_weight_before_date([], "2026-01-05") is None

    def test_get_previous_weight_entry(self):
        """Test getting previous weight entry."""
        entries = [
            {"date": "2026-01-05", "weight": 80.0},
            {"date": "2026-01-06", "weight": 79.5},
            {"date": "2026-01-07", "weight": 79.2},
        ]
        result = get_previous_weight_entry(entries, "2026-01-07")
        assert result["date"] == "2026-01-06"
        assert result["weight"] == 79.5

    def test_get_previous_weight_entry_first_entry(self):
        """Test previous entry for first weight entry."""
        entries = [{"date": "2026-01-05", "weight": 80.0}]
        assert get_previous_weight_entry(entries, "2026-01-05") is None

    def test_calculate_weight_loss_positive(self):
        """Test weight loss calculation (lost weight)."""
        loss = calculate_weight_loss(79.5, 80.0)
        assert loss == 500  # 500g lost

    def test_calculate_weight_loss_negative(self):
        """Test weight loss calculation (gained weight)."""
        loss = calculate_weight_loss(80.5, 80.0)
        assert loss == -500  # 500g gained

    def test_calculate_weight_loss_no_change(self):
        """Test weight loss calculation (no change)."""
        loss = calculate_weight_loss(80.0, 80.0)
        assert loss == 0


class TestDailyWeightRewards:
    """Test daily weight reward rarity calculation."""

    def test_same_weight_common(self):
        """Same weight should give Common item."""
        assert get_daily_weight_reward_rarity(0) == "Common"

    def test_100g_loss_uncommon(self):
        """100g loss should give Uncommon item."""
        assert get_daily_weight_reward_rarity(100) == "Uncommon"

    def test_200g_loss_rare(self):
        """200g loss should give Rare item."""
        assert get_daily_weight_reward_rarity(200) == "Rare"

    def test_300g_loss_epic(self):
        """300g loss should give Epic item."""
        assert get_daily_weight_reward_rarity(300) == "Epic"

    def test_500g_loss_legendary(self):
        """500g+ loss should give Legendary item."""
        assert get_daily_weight_reward_rarity(500) == "Legendary"
        assert get_daily_weight_reward_rarity(1000) == "Legendary"

    def test_weight_gain_no_reward(self):
        """Weight gain should give no reward."""
        assert get_daily_weight_reward_rarity(-100) is None


class TestCheckWeightEntryRewards:
    """Test the complete reward checking function."""

    def test_first_entry_no_daily_reward(self):
        """First entry should not give daily reward (no previous)."""
        entries = []
        result = check_weight_entry_rewards(entries, 80.0, "2026-01-08")
        assert result["daily_reward"] is None

    def test_daily_loss_gives_reward(self):
        """Weight loss should give daily reward."""
        entries = [{"date": "2026-01-07", "weight": 80.0}]
        # Use 79.5 for exactly 500g loss to avoid floating point issues
        result = check_weight_entry_rewards(entries, 79.5, "2026-01-08")
        
        assert result["daily_reward"] is not None
        assert abs(result["daily_loss_grams"] - 500) < 1  # ~500g loss
        assert result["daily_reward"]["rarity"] == "Legendary"  # 500g = Legendary

    def test_weekly_legendary_threshold(self):
        """500g weekly loss should give legendary."""
        entries = [{"date": "2026-01-01", "weight": 80.5}]
        result = check_weight_entry_rewards(entries, 80.0, "2026-01-08")
        
        assert result["weekly_reward"] is not None
        assert result["weekly_reward"]["rarity"] == "Legendary"

    def test_monthly_legendary_threshold(self):
        """2kg monthly loss should give legendary."""
        entries = [{"date": "2025-12-09", "weight": 82.0}]
        result = check_weight_entry_rewards(entries, 80.0, "2026-01-08")
        
        assert result["monthly_reward"] is not None
        assert result["monthly_reward"]["rarity"] == "Legendary"

    def test_same_weight_gives_common(self):
        """Same weight should give Common item."""
        entries = [{"date": "2026-01-07", "weight": 80.0}]
        result = check_weight_entry_rewards(entries, 80.0, "2026-01-08")
        
        assert result["daily_reward"] is not None
        assert result["daily_reward"]["rarity"] == "Common"

    def test_weight_gain_no_daily_reward(self):
        """Weight gain should not give daily reward."""
        entries = [{"date": "2026-01-07", "weight": 80.0}]
        result = check_weight_entry_rewards(entries, 80.5, "2026-01-08")
        
        assert result["daily_reward"] is None
        assert result["daily_loss_grams"] == -500  # 500g gained


class TestWeightStats:
    """Test weight statistics calculation."""

    def test_empty_entries(self):
        """Empty entries should return None values."""
        stats = get_weight_stats([])
        assert stats["current"] is None
        assert stats["entries_count"] == 0

    def test_basic_stats(self):
        """Test basic statistics calculation."""
        entries = [
            {"date": "2026-01-01", "weight": 82.0},
            {"date": "2026-01-05", "weight": 81.0},
            {"date": "2026-01-08", "weight": 80.0},
        ]
        stats = get_weight_stats(entries)
        
        assert stats["current"] == 80.0
        assert stats["starting"] == 82.0
        assert stats["lowest"] == 80.0
        assert stats["highest"] == 82.0
        assert stats["total_change"] == 2.0  # Lost 2kg
        assert stats["entries_count"] == 3

    def test_stats_with_goal(self):
        """Test stats include proper calculations."""
        entries = [
            {"date": "2026-01-01", "weight": 85.0},
            {"date": "2026-01-08", "weight": 83.0},
        ]
        stats = get_weight_stats(entries, "kg")
        
        assert stats["total_change"] == 2.0
        assert stats["unit"] == "kg"


class TestFormatWeightChange:
    """Test weight change formatting."""

    def test_format_loss_kg(self):
        """Format weight loss in kg."""
        result = format_weight_change(1.5, "kg")
        assert "↓" in result
        assert "1.5" in result
        assert "kg" in result

    def test_format_gain_kg(self):
        """Format weight gain in kg."""
        result = format_weight_change(-0.5, "kg")
        assert "↑" in result
        assert "0.5" in result

    def test_format_no_change(self):
        """Format no weight change."""
        result = format_weight_change(0, "kg")
        assert "→" in result
        assert "0" in result

    def test_format_none(self):
        """Format None value."""
        result = format_weight_change(None, "kg")
        assert result == "N/A"

    def test_format_lbs(self):
        """Format in pounds."""
        result = format_weight_change(1.0, "lbs")
        assert "lbs" in result


class TestWeightThresholds:
    """Test threshold constants are properly defined."""

    def test_daily_thresholds_exist(self):
        """Daily thresholds should be defined."""
        assert 0 in WEIGHT_DAILY_THRESHOLDS
        assert 100 in WEIGHT_DAILY_THRESHOLDS
        assert 200 in WEIGHT_DAILY_THRESHOLDS
        assert 300 in WEIGHT_DAILY_THRESHOLDS
        assert 500 in WEIGHT_DAILY_THRESHOLDS

    def test_weekly_threshold(self):
        """Weekly threshold should be 500g."""
        assert WEIGHT_WEEKLY_LEGENDARY_THRESHOLD == 500

    def test_monthly_threshold(self):
        """Monthly threshold should be 2000g (2kg)."""
        assert WEIGHT_MONTHLY_LEGENDARY_THRESHOLD == 2000


# ============================================================================
# NEW TESTS: Streaks, Milestones, and Maintenance Mode
# ============================================================================

from gamification import (
    _check_streak,
    _check_weight_loss,
    _check_goal_reached,
    check_weight_streak_reward,
    check_weight_milestones,
    check_weight_maintenance,
    check_all_weight_rewards,
    WEIGHT_STREAK_THRESHOLDS,
    WEIGHT_MILESTONES,
)


class TestStreakCalculation:
    """Test streak calculation functions."""

    def test_empty_entries_zero_streak(self):
        """Empty entries should return 0 streak."""
        assert _check_streak([]) == 0

    def test_single_today_entry(self):
        """Single entry today should count as 1 day streak."""
        today = datetime.now().strftime("%Y-%m-%d")
        entries = [{"date": today, "weight": 80.0}]
        assert _check_streak(entries) == 1

    def test_consecutive_days_streak(self):
        """Consecutive days should build streak."""
        today = datetime.now()
        entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "weight": 80.0}
            for i in range(7)  # 7 consecutive days
        ]
        assert _check_streak(entries) == 7

    def test_gap_breaks_streak(self):
        """Gap in entries should break streak."""
        today = datetime.now()
        entries = [
            {"date": today.strftime("%Y-%m-%d"), "weight": 80.0},
            {"date": (today - timedelta(days=1)).strftime("%Y-%m-%d"), "weight": 80.0},
            # Gap on day 2
            {"date": (today - timedelta(days=3)).strftime("%Y-%m-%d"), "weight": 80.0},
        ]
        assert _check_streak(entries) == 2  # Only today and yesterday count

    def test_no_entry_today_zero_streak(self):
        """If no entry today, streak should be 0."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        entries = [{"date": yesterday, "weight": 80.0}]
        assert _check_streak(entries) == 0


class TestWeightLossCheck:
    """Test weight loss milestone detection."""

    def test_no_entries_false(self):
        """No entries should return False."""
        assert _check_weight_loss([], 80.0, 1.0) is False

    def test_no_starting_weight_false(self):
        """No starting weight should return False."""
        entries = [{"date": "2026-01-01", "weight": 80.0}]
        assert _check_weight_loss(entries, None, 1.0) is False

    def test_lost_enough_weight(self):
        """Should detect when target loss achieved."""
        entries = [
            {"date": "2026-01-01", "weight": 85.0},  # starting
            {"date": "2026-01-10", "weight": 83.5},  # lost 1.5kg
        ]
        assert _check_weight_loss(entries, 85.0, 1.0) is True
        assert _check_weight_loss(entries, 85.0, 1.5) is True
        assert _check_weight_loss(entries, 85.0, 2.0) is False

    def test_no_loss(self):
        """No loss should return False."""
        entries = [
            {"date": "2026-01-01", "weight": 80.0},
            {"date": "2026-01-10", "weight": 80.5},  # gained
        ]
        assert _check_weight_loss(entries, 80.0, 1.0) is False


class TestGoalReached:
    """Test goal reached detection."""

    def test_no_goal_false(self):
        """No goal should return False."""
        entries = [{"date": "2026-01-01", "weight": 70.0}]
        assert _check_goal_reached(entries, None) is False

    def test_goal_reached(self):
        """Should detect when goal weight reached."""
        entries = [
            {"date": "2026-01-01", "weight": 80.0},
            {"date": "2026-01-10", "weight": 75.0},  # At goal
        ]
        assert _check_goal_reached(entries, 75.0) is True
        assert _check_goal_reached(entries, 76.0) is True  # Below goal also counts

    def test_goal_not_reached(self):
        """Should return False when above goal."""
        entries = [{"date": "2026-01-01", "weight": 80.0}]
        assert _check_goal_reached(entries, 75.0) is False


class TestStreakRewards:
    """Test streak reward generation."""

    def test_no_streak_no_reward(self):
        """No streak should give no reward."""
        result = check_weight_streak_reward([], [], "warrior")
        assert result is None

    def test_7_day_streak_reward(self):
        """7 day streak should give Rare reward."""
        today = datetime.now()
        entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "weight": 80.0}
            for i in range(7)
        ]
        result = check_weight_streak_reward(entries, [], "warrior")
        assert result is not None
        assert result["streak_days"] == 7
        assert result["rarity"] == "Rare"
        assert result["item"] is not None

    def test_already_achieved_no_duplicate(self):
        """Already achieved streaks should not give duplicate rewards."""
        today = datetime.now()
        entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "weight": 80.0}
            for i in range(7)
        ]
        result = check_weight_streak_reward(entries, ["streak_7"], "warrior")
        assert result is None  # Already achieved


class TestMilestoneRewards:
    """Test milestone achievement detection."""

    def test_first_entry_milestone(self):
        """First entry should trigger first_entry milestone."""
        entries = [{"date": "2026-01-01", "weight": 80.0}]
        milestones = check_weight_milestones(entries, None, [], "warrior")
        
        milestone_ids = [m["milestone_id"] for m in milestones]
        assert "first_entry" in milestone_ids

    def test_lost_1kg_milestone(self):
        """Losing 1kg should trigger lost_1kg milestone."""
        entries = [
            {"date": "2026-01-01", "weight": 80.0},
            {"date": "2026-01-10", "weight": 78.5},  # Lost 1.5kg
        ]
        milestones = check_weight_milestones(entries, None, [], "warrior")
        
        milestone_ids = [m["milestone_id"] for m in milestones]
        assert "lost_1kg" in milestone_ids

    def test_goal_reached_milestone(self):
        """Reaching goal should trigger goal_reached milestone."""
        entries = [
            {"date": "2026-01-01", "weight": 80.0},
            {"date": "2026-01-30", "weight": 75.0},
        ]
        milestones = check_weight_milestones(entries, 75.0, [], "warrior")
        
        milestone_ids = [m["milestone_id"] for m in milestones]
        assert "goal_reached" in milestone_ids

    def test_no_duplicate_milestones(self):
        """Already achieved milestones should not be given again."""
        entries = [{"date": "2026-01-01", "weight": 80.0}]
        milestones = check_weight_milestones(entries, None, ["first_entry"], "warrior")
        
        milestone_ids = [m["milestone_id"] for m in milestones]
        assert "first_entry" not in milestone_ids


class TestMaintenanceMode:
    """Test maintenance mode detection and rewards."""

    def test_no_goal_no_maintenance(self):
        """No goal means no maintenance reward."""
        entries = [{"date": datetime.now().strftime("%Y-%m-%d"), "weight": 75.0}]
        result = check_weight_maintenance(entries, None, "warrior")
        assert result is None

    def test_not_at_goal_no_maintenance(self):
        """If not within ±0.5kg of goal, no maintenance."""
        entries = [{"date": datetime.now().strftime("%Y-%m-%d"), "weight": 76.0}]
        result = check_weight_maintenance(entries, 75.0, "warrior")
        assert result is None  # 1kg away, too far

    def test_at_goal_maintenance_reward(self):
        """Within ±0.5kg of goal should trigger maintenance."""
        entries = [{"date": datetime.now().strftime("%Y-%m-%d"), "weight": 75.3}]
        result = check_weight_maintenance(entries, 75.0, "warrior")
        
        assert result is not None
        assert result["deviation_kg"] <= 0.5
        assert result["item"] is not None

    def test_maintenance_streak_escalates_rarity(self):
        """Longer maintenance streaks should give better rewards."""
        today = datetime.now()
        # 7+ days at goal
        entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "weight": 75.0 + (i * 0.05)}
            for i in range(8)  # 8 days all within range
        ]
        result = check_weight_maintenance(entries, 75.0, "warrior")
        
        assert result is not None
        assert result["rarity"] == "Rare"  # 7+ days


class TestComprehensiveRewards:
    """Test the check_all_weight_rewards function."""

    def test_combines_all_reward_types(self):
        """Should return combined results from all reward checks."""
        today = datetime.now()
        entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "weight": 80.0 - (i * 0.1)}
            for i in range(1, 8)  # 7 previous days with weight loss
        ]
        
        result = check_all_weight_rewards(
            entries, 
            79.0,  # New weight (0.1kg loss from yesterday) 
            today.strftime("%Y-%m-%d"),
            None,  # No goal
            [],    # No milestones achieved
            "warrior"
        )
        
        # Should have daily reward
        assert result.get("daily_reward") is not None or result.get("daily_loss_grams") is not None
        # Should have streak info
        assert "current_streak" in result
        # Should have milestone list
        assert "new_milestones" in result
        # Messages should exist
        assert "messages" in result

    def test_includes_new_entry_for_milestone_check(self):
        """New entry should be included when checking milestones."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Empty entries list, adding first entry
        result = check_all_weight_rewards(
            [],     # No previous entries
            80.0,   # First entry
            today,
            None,
            [],
            "warrior"
        )
        
        # Should detect first_entry milestone
        milestone_ids = [m["milestone_id"] for m in result.get("new_milestones", [])]
        assert "first_entry" in milestone_ids


class TestStreakThresholds:
    """Test streak threshold configuration."""

    def test_thresholds_defined(self):
        """All expected streak thresholds should be defined."""
        assert 7 in WEIGHT_STREAK_THRESHOLDS
        assert 14 in WEIGHT_STREAK_THRESHOLDS
        assert 30 in WEIGHT_STREAK_THRESHOLDS
        assert 100 in WEIGHT_STREAK_THRESHOLDS

    def test_rarity_escalation(self):
        """Higher streaks should give better rewards."""
        assert WEIGHT_STREAK_THRESHOLDS[7] == "Rare"
        assert WEIGHT_STREAK_THRESHOLDS[14] == "Epic"
        assert WEIGHT_STREAK_THRESHOLDS[30] == "Legendary"


class TestMilestoneDefinitions:
    """Test milestone definitions."""

    def test_all_milestones_have_required_fields(self):
        """All milestones should have name, description, rarity, check."""
        for milestone_id, milestone in WEIGHT_MILESTONES.items():
            assert "name" in milestone, f"{milestone_id} missing name"
            assert "description" in milestone, f"{milestone_id} missing description"
            assert "rarity" in milestone, f"{milestone_id} missing rarity"
            assert "check" in milestone, f"{milestone_id} missing check"
            assert callable(milestone["check"]), f"{milestone_id} check not callable"

    def test_expected_milestones_exist(self):
        """Expected milestones should be defined."""
        expected = ["first_entry", "lost_1kg", "lost_5kg", "lost_10kg", "goal_reached"]
        for m_id in expected:
            assert m_id in WEIGHT_MILESTONES, f"Missing milestone: {m_id}"
