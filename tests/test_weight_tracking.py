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
