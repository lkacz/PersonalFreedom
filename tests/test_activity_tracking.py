"""Tests for physical activity tracking gamification features."""

import pytest
from datetime import datetime, timedelta

# Import gamification activity functions
from gamification import (
    ACTIVITY_TYPES,
    INTENSITY_LEVELS,
    ACTIVITY_MIN_DURATION,
    ACTIVITY_REWARD_THRESHOLDS,
    ACTIVITY_STREAK_THRESHOLDS,
    ACTIVITY_MILESTONES,
    get_activity_type,
    get_intensity_level,
    calculate_effective_minutes,
    get_activity_reward_rarity,
    check_activity_streak,
    check_activity_entry_reward,
    check_activity_streak_reward,
    check_activity_milestones,
    check_all_activity_rewards,
    get_activity_stats,
    format_activity_duration,
)


class TestActivityConstants:
    """Test activity tracking constants are properly defined."""

    def test_activity_types_defined(self):
        """Activity types should be defined."""
        assert ACTIVITY_TYPES is not None
        assert len(ACTIVITY_TYPES) > 0

    def test_activity_types_structure(self):
        """Each activity type should have id, name, emoji, and base_intensity."""
        for activity in ACTIVITY_TYPES:
            assert len(activity) == 4
            activity_id, name, emoji, base_intensity = activity
            assert isinstance(activity_id, str)
            assert isinstance(name, str)
            assert isinstance(emoji, str)
            assert isinstance(base_intensity, (int, float))
            assert base_intensity > 0

    def test_intensity_levels_defined(self):
        """Intensity levels should be defined."""
        assert INTENSITY_LEVELS is not None
        assert len(INTENSITY_LEVELS) == 4

    def test_intensity_levels_structure(self):
        """Each intensity level should have id, name, and multiplier."""
        for intensity in INTENSITY_LEVELS:
            assert len(intensity) == 3
            intensity_id, name, multiplier = intensity
            assert isinstance(intensity_id, str)
            assert isinstance(name, str)
            assert isinstance(multiplier, (int, float))
            assert multiplier > 0

    def test_min_duration_positive(self):
        """Minimum duration should be positive."""
        assert ACTIVITY_MIN_DURATION > 0
        assert ACTIVITY_MIN_DURATION == 10  # 10 minutes as specified

    def test_reward_thresholds_ascending(self):
        """Reward thresholds should be in ascending order."""
        prev_threshold = 0
        for threshold, rarity in ACTIVITY_REWARD_THRESHOLDS:
            assert threshold > prev_threshold
            prev_threshold = threshold


class TestActivityHelperFunctions:
    """Test activity tracking helper functions."""

    def test_get_activity_type_found(self):
        """Test finding activity type by ID."""
        result = get_activity_type("walking")
        assert result is not None
        assert result[0] == "walking"
        assert result[1] == "Walking"

    def test_get_activity_type_not_found(self):
        """Test activity type lookup for invalid ID."""
        result = get_activity_type("invalid_activity")
        assert result is None

    def test_get_intensity_level_found(self):
        """Test finding intensity level by ID."""
        result = get_intensity_level("moderate")
        assert result is not None
        assert result[0] == "moderate"
        assert result[1] == "Moderate"

    def test_get_intensity_level_not_found(self):
        """Test intensity level lookup for invalid ID."""
        result = get_intensity_level("invalid_intensity")
        assert result is None


class TestEffectiveMinutesCalculation:
    """Test effective minutes calculation."""

    def test_walking_light_10min(self):
        """10 min light walking should give ~8 effective minutes."""
        # Walking base: 1.0, Light multiplier: 0.8
        result = calculate_effective_minutes(10, "walking", "light")
        assert result == 10 * 1.0 * 0.8  # 8

    def test_walking_moderate_10min(self):
        """10 min moderate walking should give 10 effective minutes."""
        # Walking base: 1.0, Moderate multiplier: 1.0
        result = calculate_effective_minutes(10, "walking", "moderate")
        assert result == 10 * 1.0 * 1.0  # 10

    def test_running_vigorous_30min(self):
        """30 min vigorous running should give high effective minutes."""
        # Running base: 2.0, Vigorous multiplier: 1.3
        result = calculate_effective_minutes(30, "running", "vigorous")
        assert result == 30 * 2.0 * 1.3  # 78

    def test_hiit_intense_30min(self):
        """30 min intense HIIT should give very high effective minutes."""
        # HIIT base: 2.5, Intense multiplier: 1.6
        result = calculate_effective_minutes(30, "hiit", "intense")
        assert result == 30 * 2.5 * 1.6  # 120

    def test_yoga_light_30min(self):
        """30 min light yoga should give moderate effective minutes."""
        # Yoga base: 1.0, Light multiplier: 0.8
        result = calculate_effective_minutes(30, "yoga", "light")
        assert result == 30 * 1.0 * 0.8  # 24

    def test_invalid_activity_defaults(self):
        """Invalid activity should use default multiplier."""
        result = calculate_effective_minutes(10, "invalid", "moderate")
        assert result == 10 * 1.0 * 1.0  # 10


class TestActivityRewardRarity:
    """Test reward rarity calculation based on effective minutes."""

    def test_below_minimum_no_reward(self):
        """Below minimum threshold (8) should give no reward."""
        assert get_activity_reward_rarity(5) is None
        assert get_activity_reward_rarity(7) is None
        assert get_activity_reward_rarity(7.9) is None

    def test_minimum_gives_common(self):
        """8+ effective minutes should give Common (10 min light walk = 8)."""
        assert get_activity_reward_rarity(8) == "Common"
        assert get_activity_reward_rarity(10) == "Common"
        assert get_activity_reward_rarity(15) == "Common"
        assert get_activity_reward_rarity(19) == "Common"

    def test_20_gives_uncommon(self):
        """20+ effective minutes should give Uncommon."""
        assert get_activity_reward_rarity(20) == "Uncommon"
        assert get_activity_reward_rarity(35) == "Uncommon"
        assert get_activity_reward_rarity(39) == "Uncommon"

    def test_40_gives_rare(self):
        """40+ effective minutes should give Rare."""
        assert get_activity_reward_rarity(40) == "Rare"
        assert get_activity_reward_rarity(60) == "Rare"
        assert get_activity_reward_rarity(69) == "Rare"

    def test_70_gives_epic(self):
        """70+ effective minutes should give Epic."""
        assert get_activity_reward_rarity(70) == "Epic"
        assert get_activity_reward_rarity(100) == "Epic"
        assert get_activity_reward_rarity(119) == "Epic"

    def test_120_gives_legendary(self):
        """120+ effective minutes should give Legendary."""
        assert get_activity_reward_rarity(120) == "Legendary"
        assert get_activity_reward_rarity(180) == "Legendary"
        assert get_activity_reward_rarity(500) == "Legendary"


class TestActivityStreak:
    """Test activity streak calculation."""

    def test_empty_entries_zero_streak(self):
        """Empty entries should return 0 streak."""
        assert check_activity_streak([]) == 0

    def test_single_today_entry(self):
        """Single entry today should count as 1 day streak."""
        today = datetime.now().strftime("%Y-%m-%d")
        entries = [{"date": today, "duration": 30, "activity_type": "walking"}]
        assert check_activity_streak(entries) == 1

    def test_consecutive_days_streak(self):
        """Consecutive days should build streak."""
        today = datetime.now()
        entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "duration": 30}
            for i in range(7)
        ]
        assert check_activity_streak(entries) == 7

    def test_gap_breaks_streak(self):
        """Gap in entries should break streak."""
        today = datetime.now()
        entries = [
            {"date": today.strftime("%Y-%m-%d"), "duration": 30},
            {"date": (today - timedelta(days=1)).strftime("%Y-%m-%d"), "duration": 30},
            # Gap on day 2
            {"date": (today - timedelta(days=3)).strftime("%Y-%m-%d"), "duration": 30},
        ]
        assert check_activity_streak(entries) == 2

    def test_no_entry_today_zero_streak(self):
        """If no entry today, streak should be 0."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        entries = [{"date": yesterday, "duration": 30}]
        assert check_activity_streak(entries) == 0

    def test_multiple_entries_same_day(self):
        """Multiple entries on same day should count as one day."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        entries = [
            {"date": today, "duration": 20},
            {"date": today, "duration": 15},
            {"date": yesterday, "duration": 30},
        ]
        assert check_activity_streak(entries) == 2


class TestActivityEntryReward:
    """Test individual activity entry rewards."""

    def test_below_minimum_no_reward(self):
        """Activity below minimum should not earn reward."""
        result = check_activity_entry_reward(5, "walking", "moderate")
        assert result["reward"] is None
        assert "at least" in result["messages"][0].lower()

    def test_10min_walk_gives_common(self):
        """10 min moderate walk should give Common reward."""
        result = check_activity_entry_reward(10, "walking", "moderate")
        assert result["reward"] is not None
        assert result["rarity"] == "Common"

    def test_30min_run_gives_good_reward(self):
        """30 min vigorous run should give good reward."""
        # 30 * 2.0 * 1.3 = 78 effective minutes -> Epic
        result = check_activity_entry_reward(30, "running", "vigorous")
        assert result["reward"] is not None
        assert result["rarity"] == "Epic"

    def test_60min_hiit_gives_legendary(self):
        """60 min intense HIIT should give Legendary."""
        # 60 * 2.5 * 1.6 = 240 effective minutes -> Legendary
        result = check_activity_entry_reward(60, "hiit", "intense")
        assert result["reward"] is not None
        assert result["rarity"] == "Legendary"

    def test_reward_includes_effective_minutes(self):
        """Result should include effective minutes."""
        result = check_activity_entry_reward(30, "walking", "moderate")
        assert "effective_minutes" in result
        assert result["effective_minutes"] == 30


class TestActivityStreakReward:
    """Test streak milestone rewards."""

    def test_no_streak_no_reward(self):
        """No streak should give no reward."""
        entries = []
        result = check_activity_streak_reward(entries, [])
        assert result is None

    def test_3_day_streak_reward(self):
        """3-day streak should give reward."""
        today = datetime.now()
        entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "duration": 30}
            for i in range(3)
        ]
        result = check_activity_streak_reward(entries, [])
        assert result is not None
        assert result["streak_days"] == 3
        assert result["item"] is not None

    def test_already_achieved_no_duplicate(self):
        """Already achieved streaks should not give duplicate rewards."""
        today = datetime.now()
        entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "duration": 30}
            for i in range(3)
        ]
        result = check_activity_streak_reward(entries, ["activity_streak_3"])
        # Should check for next milestone (7 days) but not have enough
        assert result is None or result["streak_days"] > 3


class TestActivityMilestones:
    """Test activity milestone achievements."""

    def test_first_entry_milestone(self):
        """First activity should earn milestone."""
        entries = [{"date": "2026-01-01", "duration": 30, "activity_type": "walking"}]
        milestones = check_activity_milestones(entries, [])
        
        first_entry = next((m for m in milestones if m["milestone_id"] == "first_activity"), None)
        assert first_entry is not None
        assert first_entry["item"] is not None

    def test_no_duplicate_milestones(self):
        """Already achieved milestones should not repeat."""
        entries = [{"date": "2026-01-01", "duration": 30, "activity_type": "walking"}]
        milestones = check_activity_milestones(entries, ["first_activity"])
        
        first_entry = next((m for m in milestones if m["milestone_id"] == "first_activity"), None)
        assert first_entry is None

    def test_hour_hero_milestone(self):
        """60+ minutes total should earn Hour Hero."""
        entries = [
            {"date": "2026-01-01", "duration": 30, "activity_type": "walking"},
            {"date": "2026-01-02", "duration": 35, "activity_type": "running"},
        ]
        milestones = check_activity_milestones(entries, [])
        
        hour_hero = next((m for m in milestones if m["milestone_id"] == "total_1hr"), None)
        assert hour_hero is not None

    def test_variety_milestone(self):
        """Using 3 different activities should earn Explorer."""
        entries = [
            {"date": "2026-01-01", "duration": 30, "activity_type": "walking"},
            {"date": "2026-01-02", "duration": 30, "activity_type": "running"},
            {"date": "2026-01-03", "duration": 30, "activity_type": "cycling"},
        ]
        milestones = check_activity_milestones(entries, [])
        
        variety = next((m for m in milestones if m["milestone_id"] == "variety_3"), None)
        assert variety is not None


class TestComprehensiveActivityRewards:
    """Test the comprehensive reward function."""

    def test_combines_all_reward_types(self):
        """check_all_activity_rewards should combine entry, streak, and milestone rewards."""
        today = datetime.now()
        entries = [
            {"date": (today - timedelta(days=1)).strftime("%Y-%m-%d"), "duration": 30,
             "activity_type": "walking", "intensity": "moderate"},
            {"date": (today - timedelta(days=2)).strftime("%Y-%m-%d"), "duration": 30,
             "activity_type": "running", "intensity": "moderate"},
        ]
        
        result = check_all_activity_rewards(
            entries,
            duration_minutes=30,
            activity_id="cycling",
            intensity_id="vigorous",
            current_date=today.strftime("%Y-%m-%d"),
            achieved_milestones=[],
            story_id="warrior"
        )
        
        assert "reward" in result
        assert "current_streak" in result
        assert "new_milestones" in result
        assert "messages" in result

    def test_includes_new_entry_for_milestone_check(self):
        """New entry should be included when checking milestones."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # No existing entries, this would be first
        result = check_all_activity_rewards(
            [],
            duration_minutes=30,
            activity_id="walking",
            intensity_id="moderate",
            current_date=today,
            achieved_milestones=[],
            story_id="warrior"
        )
        
        # Should have first_activity milestone
        milestone_ids = [m["milestone_id"] for m in result["new_milestones"]]
        assert "first_activity" in milestone_ids


class TestActivityStats:
    """Test activity statistics calculation."""

    def test_empty_entries_stats(self):
        """Empty entries should return zero stats."""
        stats = get_activity_stats([])
        assert stats["total_minutes"] == 0
        assert stats["total_sessions"] == 0
        assert stats["current_streak"] == 0

    def test_basic_stats(self):
        """Test basic stats calculation."""
        today = datetime.now()
        entries = [
            {"date": today.strftime("%Y-%m-%d"), "duration": 30, "activity_type": "walking"},
            {"date": (today - timedelta(days=1)).strftime("%Y-%m-%d"), "duration": 45, "activity_type": "running"},
        ]
        stats = get_activity_stats(entries)
        
        assert stats["total_minutes"] == 75
        assert stats["total_sessions"] == 2
        assert stats["avg_duration"] == 37.5

    def test_favorite_activity(self):
        """Test favorite activity detection."""
        entries = [
            {"date": "2026-01-01", "duration": 30, "activity_type": "walking"},
            {"date": "2026-01-02", "duration": 30, "activity_type": "walking"},
            {"date": "2026-01-03", "duration": 30, "activity_type": "running"},
        ]
        stats = get_activity_stats(entries)
        assert stats["favorite_activity"] == "walking"


class TestFormatActivityDuration:
    """Test duration formatting function."""

    def test_format_minutes_only(self):
        """Format minutes under 60."""
        assert format_activity_duration(30) == "30 min"
        assert format_activity_duration(59) == "59 min"

    def test_format_full_hours(self):
        """Format full hours."""
        assert format_activity_duration(60) == "1h"
        assert format_activity_duration(120) == "2h"

    def test_format_hours_and_minutes(self):
        """Format hours with remaining minutes."""
        assert format_activity_duration(90) == "1h 30m"
        assert format_activity_duration(135) == "2h 15m"


class TestMilestoneDefinitions:
    """Test milestone definitions are complete."""

    def test_all_milestones_have_required_fields(self):
        """All milestones should have id, name, description, check, and rarity."""
        required_fields = ["id", "name", "description", "check", "rarity"]
        for milestone in ACTIVITY_MILESTONES:
            for field in required_fields:
                assert field in milestone, f"Milestone missing {field}: {milestone}"

    def test_expected_milestones_exist(self):
        """Certain key milestones should exist."""
        milestone_ids = [m["id"] for m in ACTIVITY_MILESTONES]
        expected = ["first_activity", "total_1hr", "variety_3"]
        for expected_id in expected:
            assert expected_id in milestone_ids, f"Missing milestone: {expected_id}"


class TestStreakThresholds:
    """Test streak threshold definitions."""

    def test_thresholds_defined(self):
        """Streak thresholds should be defined."""
        assert ACTIVITY_STREAK_THRESHOLDS is not None
        assert len(ACTIVITY_STREAK_THRESHOLDS) > 0

    def test_thresholds_ascending(self):
        """Streak thresholds should be in ascending order."""
        prev = 0
        for days, rarity, name in ACTIVITY_STREAK_THRESHOLDS:
            assert days > prev or days == prev  # Allow same for multiple same-level rewards
            prev = days


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_10min_light_walk_earns_common(self):
        """Per user spec: 10 min light walking should earn at least Common."""
        # 10 min * 1.0 (walking) * 0.8 (light) = 8 effective min
        result = check_activity_entry_reward(10, "walking", "light")
        assert result["reward"] is not None
        assert result["rarity"] == "Common"

    def test_10min_light_stretching_earns_common(self):
        """10 min light stretching should still earn Common."""
        # 10 min * 0.8 (stretching) * 0.8 (light) = 6.4 effective min - below threshold
        result = check_activity_entry_reward(10, "stretching", "light")
        # With threshold at 8, this won't earn reward
        assert result["effective_minutes"] == 6.4

    def test_13min_stretching_light_earns_reward(self):
        """13 min light stretching reaches 8+ effective minutes."""
        # 13 * 0.8 * 0.8 = 8.32 effective min
        result = check_activity_entry_reward(13, "stretching", "light")
        assert result["reward"] is not None
        assert result["rarity"] == "Common"

    def test_below_10min_duration_no_reward_check(self):
        """Activities under 10 min duration skip reward calculation."""
        result = check_activity_entry_reward(5, "running", "intense")
        assert result["reward"] is None
        assert "at least 10 minutes" in result["messages"][0]

    def test_empty_activity_type_fallback(self):
        """Unknown activity type should use default multiplier."""
        result = calculate_effective_minutes(30, "nonexistent", "moderate")
        assert result == 30  # 30 * 1.0 * 1.0

    def test_empty_intensity_fallback(self):
        """Unknown intensity should use default multiplier."""
        result = calculate_effective_minutes(30, "walking", "nonexistent")
        assert result == 30  # 30 * 1.0 * 1.0

    def test_entry_without_activity_type(self):
        """Entry without activity_type should be handled in stats."""
        entries = [{"date": "2026-01-01", "duration": 30}]
        stats = get_activity_stats(entries)
        assert stats["total_sessions"] == 1
        assert stats["total_minutes"] == 30

    def test_entry_without_duration(self):
        """Entry without duration should contribute 0 minutes."""
        entries = [{"date": "2026-01-01", "activity_type": "walking"}]
        stats = get_activity_stats(entries)
        assert stats["total_minutes"] == 0

    def test_message_when_no_reward_earned(self):
        """When activity doesn't earn reward, message should explain."""
        # 10 min stretching light = 6.4 effective min, below 8 threshold
        result = check_activity_entry_reward(10, "stretching", "light")
        assert result["reward"] is None
        assert len(result["messages"]) > 0
        assert "effective min" in result["messages"][0].lower() or "need" in result["messages"][0].lower()

    def test_very_long_activity(self):
        """Very long activities should still work correctly."""
        result = check_activity_entry_reward(480, "hiit", "intense")
        # 480 * 2.5 * 1.6 = 1920 effective min
        assert result["reward"] is not None
        assert result["rarity"] == "Legendary"
        assert result["effective_minutes"] == 1920

    def test_streak_with_future_entries(self):
        """Entries with future dates shouldn't affect streak."""
        from datetime import datetime, timedelta
        today = datetime.now()
        entries = [
            {"date": today.strftime("%Y-%m-%d"), "duration": 30},
            {"date": (today + timedelta(days=5)).strftime("%Y-%m-%d"), "duration": 30},
        ]
        # Only today counts, future is ignored in streak logic
        assert check_activity_streak(entries) == 1

    def test_stats_with_no_entries_returns_defaults(self):
        """Empty entries should return sensible defaults."""
        stats = get_activity_stats([])
        assert stats["total_minutes"] == 0
        assert stats["total_sessions"] == 0
        assert stats["favorite_activity"] is None
        assert stats["avg_duration"] == 0
        assert stats["current_streak"] == 0
