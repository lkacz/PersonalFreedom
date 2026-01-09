"""Tests for sleep tracking gamification features."""

import unittest
from datetime import datetime, timedelta

from gamification import (
    SLEEP_CHRONOTYPES,
    SLEEP_QUALITY_FACTORS,
    SLEEP_DISRUPTION_TAGS,
    SLEEP_DURATION_TARGETS,
    SLEEP_REWARD_THRESHOLDS,
    SLEEP_STREAK_THRESHOLDS,
    SLEEP_MILESTONES,
    get_chronotype,
    get_sleep_quality,
    get_disruption_tag,
    time_to_minutes,
    minutes_to_time,
    calculate_bedtime_score,
    calculate_duration_score,
    calculate_sleep_score,
    check_sleep_streak,
    get_sleep_reward_rarity,
    check_sleep_entry_reward,
    check_sleep_streak_reward,
    check_sleep_milestones,
    check_all_sleep_rewards,
    get_sleep_stats,
    format_sleep_duration,
    get_sleep_recommendation,
)


class TestSleepConstants(unittest.TestCase):
    """Tests for sleep tracking constants."""
    
    def test_chronotypes_defined(self) -> None:
        """Test that chronotypes are properly defined."""
        self.assertEqual(len(SLEEP_CHRONOTYPES), 3)
        for chrono in SLEEP_CHRONOTYPES:
            self.assertEqual(len(chrono), 6)
            # (id, name, emoji, optimal_start, optimal_end, description)
            self.assertIsInstance(chrono[0], str)  # id
            self.assertIsInstance(chrono[1], str)  # name
            self.assertIsInstance(chrono[2], str)  # emoji
            self.assertIn(":", chrono[3])  # time format
            self.assertIn(":", chrono[4])  # time format
    
    def test_quality_factors_defined(self) -> None:
        """Test that quality factors are properly defined."""
        self.assertGreaterEqual(len(SLEEP_QUALITY_FACTORS), 4)
        for quality in SLEEP_QUALITY_FACTORS:
            self.assertEqual(len(quality), 4)
            # (id, name, emoji, multiplier)
            self.assertIsInstance(quality[3], (int, float))
            self.assertGreater(quality[3], 0)
    
    def test_disruption_tags_defined(self) -> None:
        """Test that disruption tags are properly defined."""
        self.assertGreaterEqual(len(SLEEP_DISRUPTION_TAGS), 5)
        for tag in SLEEP_DISRUPTION_TAGS:
            self.assertEqual(len(tag), 4)
            # (id, name, emoji, impact)
            self.assertIsInstance(tag[3], int)
    
    def test_duration_targets_defined(self) -> None:
        """Test that duration targets are scientifically reasonable."""
        self.assertEqual(SLEEP_DURATION_TARGETS["minimum"], 7.0)
        self.assertGreaterEqual(SLEEP_DURATION_TARGETS["optimal_high"], 8.0)
        self.assertLessEqual(SLEEP_DURATION_TARGETS["optimal_high"], 10.0)
    
    def test_reward_thresholds_ordered(self) -> None:
        """Test that reward thresholds are in ascending order."""
        prev_threshold = 0
        for threshold, rarity in SLEEP_REWARD_THRESHOLDS:
            self.assertGreater(threshold, prev_threshold)
            prev_threshold = threshold
    
    def test_streak_thresholds_ordered(self) -> None:
        """Test that streak thresholds are in ascending order."""
        prev_days = 0
        for days, rarity, name in SLEEP_STREAK_THRESHOLDS:
            self.assertGreater(days, prev_days)
            prev_days = days
    
    def test_milestones_have_required_fields(self) -> None:
        """Test that all milestones have required fields."""
        required = {"id", "name", "description", "check", "rarity"}
        for milestone in SLEEP_MILESTONES:
            self.assertTrue(required.issubset(milestone.keys()), 
                           f"Milestone {milestone.get('id')} missing fields")


class TestHelperFunctions(unittest.TestCase):
    """Tests for helper functions."""
    
    def test_get_chronotype_valid(self) -> None:
        """Test getting valid chronotype."""
        chrono = get_chronotype("early_bird")
        self.assertIsNotNone(chrono)
        self.assertEqual(chrono[0], "early_bird")
    
    def test_get_chronotype_invalid(self) -> None:
        """Test getting invalid chronotype returns None."""
        self.assertIsNone(get_chronotype("invalid"))
    
    def test_get_sleep_quality_valid(self) -> None:
        """Test getting valid sleep quality."""
        quality = get_sleep_quality("good")
        self.assertIsNotNone(quality)
        self.assertEqual(quality[0], "good")
    
    def test_get_sleep_quality_invalid(self) -> None:
        """Test getting invalid quality returns None."""
        self.assertIsNone(get_sleep_quality("invalid"))
    
    def test_get_disruption_tag_valid(self) -> None:
        """Test getting valid disruption tag."""
        tag = get_disruption_tag("nightmares")
        self.assertIsNotNone(tag)
        self.assertEqual(tag[0], "nightmares")
    
    def test_time_to_minutes_valid(self) -> None:
        """Test time conversion to minutes."""
        self.assertEqual(time_to_minutes("00:00"), 0)
        self.assertEqual(time_to_minutes("12:00"), 720)
        self.assertEqual(time_to_minutes("23:59"), 1439)
        self.assertEqual(time_to_minutes("08:30"), 510)
    
    def test_time_to_minutes_invalid(self) -> None:
        """Test invalid time returns 0."""
        self.assertEqual(time_to_minutes("invalid"), 0)
        self.assertEqual(time_to_minutes(None), 0)
    
    def test_minutes_to_time(self) -> None:
        """Test minutes to time conversion."""
        self.assertEqual(minutes_to_time(0), "00:00")
        self.assertEqual(minutes_to_time(720), "12:00")
        self.assertEqual(minutes_to_time(1439), "23:59")
        # Test wrap around
        self.assertEqual(minutes_to_time(24 * 60), "00:00")


class TestBedtimeScore(unittest.TestCase):
    """Tests for bedtime score calculation."""
    
    def test_perfect_bedtime_moderate(self) -> None:
        """Test perfect bedtime for moderate chronotype."""
        score, msg = calculate_bedtime_score("22:30", "moderate")
        self.assertEqual(score, 100)
        self.assertIn("Perfect", msg)
    
    def test_perfect_bedtime_early_bird(self) -> None:
        """Test perfect bedtime for early bird."""
        score, msg = calculate_bedtime_score("21:30", "early_bird")
        self.assertEqual(score, 100)
    
    def test_perfect_bedtime_night_owl(self) -> None:
        """Test perfect bedtime for night owl."""
        score, msg = calculate_bedtime_score("23:30", "night_owl")
        self.assertEqual(score, 100)
    
    def test_late_bedtime_penalty(self) -> None:
        """Test late bedtime gets penalized."""
        score, _ = calculate_bedtime_score("02:00", "moderate")
        self.assertLess(score, 100)
    
    def test_early_bedtime_penalty(self) -> None:
        """Test very early bedtime gets small penalty."""
        score, _ = calculate_bedtime_score("19:00", "moderate")
        self.assertLess(score, 100)
    
    def test_invalid_chronotype_uses_moderate(self) -> None:
        """Test invalid chronotype defaults to moderate."""
        score, _ = calculate_bedtime_score("22:30", "invalid")
        self.assertGreaterEqual(score, 0)


class TestDurationScore(unittest.TestCase):
    """Tests for sleep duration score calculation."""
    
    def test_optimal_duration(self) -> None:
        """Test optimal sleep duration gets full score."""
        score, msg = calculate_duration_score(8.0)
        self.assertEqual(score, 100)
        self.assertIn("Perfect", msg)
    
    def test_minimum_duration(self) -> None:
        """Test minimum acceptable duration."""
        score, _ = calculate_duration_score(7.0)
        self.assertGreaterEqual(score, 80)
    
    def test_short_sleep_penalty(self) -> None:
        """Test short sleep gets penalized heavily."""
        score, msg = calculate_duration_score(5.0)
        self.assertLess(score, 70)
        self.assertIn("deprived", msg.lower())
    
    def test_very_short_sleep(self) -> None:
        """Test very short sleep gets severe penalty."""
        score, _ = calculate_duration_score(3.0)
        self.assertLess(score, 30)
    
    def test_long_sleep_acceptable(self) -> None:
        """Test slightly long sleep is acceptable."""
        score, _ = calculate_duration_score(9.5)
        self.assertGreaterEqual(score, 80)
    
    def test_very_long_sleep_warning(self) -> None:
        """Test very long sleep shows warning."""
        score, msg = calculate_duration_score(11.0)
        self.assertLess(score, 80)
        self.assertIn("Very long", msg)


class TestSleepScore(unittest.TestCase):
    """Tests for comprehensive sleep score calculation."""
    
    def test_perfect_sleep(self) -> None:
        """Test perfect sleep conditions."""
        result = calculate_sleep_score(
            sleep_hours=8.0,
            bedtime="22:30",
            quality_id="excellent",
            disruptions=[],
            chronotype_id="moderate"
        )
        self.assertGreater(result["total_score"], 80)
        self.assertEqual(result["duration_score"], 100)
    
    def test_poor_sleep(self) -> None:
        """Test poor sleep conditions."""
        result = calculate_sleep_score(
            sleep_hours=5.0,
            bedtime="02:00",
            quality_id="poor",
            disruptions=["woke_multiple", "stress"],
            chronotype_id="moderate"
        )
        self.assertLess(result["total_score"], 50)
    
    def test_disruptions_reduce_score(self) -> None:
        """Test that disruptions reduce quality score."""
        result_no_disruption = calculate_sleep_score(
            sleep_hours=8.0, bedtime="22:30", quality_id="good",
            disruptions=[], chronotype_id="moderate"
        )
        result_with_disruption = calculate_sleep_score(
            sleep_hours=8.0, bedtime="22:30", quality_id="good",
            disruptions=["woke_multiple", "nightmares"], chronotype_id="moderate"
        )
        self.assertGreater(
            result_no_disruption["quality_score"],
            result_with_disruption["quality_score"]
        )
    
    def test_score_breakdown_present(self) -> None:
        """Test that score breakdown is returned."""
        result = calculate_sleep_score(
            sleep_hours=7.5, bedtime="23:00", quality_id="good",
            disruptions=[], chronotype_id="moderate"
        )
        self.assertIn("duration_score", result)
        self.assertIn("bedtime_score", result)
        self.assertIn("quality_score", result)
        self.assertIn("disruption_penalty", result)


class TestSleepStreak(unittest.TestCase):
    """Tests for sleep streak calculation."""
    
    def test_empty_entries_zero_streak(self) -> None:
        """Test empty entries gives zero streak."""
        self.assertEqual(check_sleep_streak([]), 0)
    
    def test_no_good_sleep_zero_streak(self) -> None:
        """Test no good sleep (7+ hours) gives zero streak."""
        entries = [
            {"date": datetime.now().strftime("%Y-%m-%d"), "sleep_hours": 5.0}
        ]
        self.assertEqual(check_sleep_streak(entries), 0)
    
    def test_single_good_night(self) -> None:
        """Test single good night today."""
        entries = [
            {"date": datetime.now().strftime("%Y-%m-%d"), "sleep_hours": 8.0}
        ]
        self.assertEqual(check_sleep_streak(entries), 1)
    
    def test_consecutive_streak(self) -> None:
        """Test consecutive nights streak."""
        today = datetime.now()
        entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "sleep_hours": 7.5}
            for i in range(5)
        ]
        streak = check_sleep_streak(entries)
        self.assertGreaterEqual(streak, 4)
    
    def test_streak_breaks_on_gap(self) -> None:
        """Test streak breaks when there's a gap."""
        today = datetime.now()
        entries = [
            {"date": today.strftime("%Y-%m-%d"), "sleep_hours": 8.0},
            {"date": (today - timedelta(days=3)).strftime("%Y-%m-%d"), "sleep_hours": 8.0},
        ]
        streak = check_sleep_streak(entries)
        self.assertEqual(streak, 1)


class TestSleepRewards(unittest.TestCase):
    """Tests for sleep reward functions."""
    
    def test_reward_rarity_below_threshold(self) -> None:
        """Test no reward for low score."""
        self.assertIsNone(get_sleep_reward_rarity(30))
    
    def test_reward_rarity_common(self) -> None:
        """Test common reward for decent score."""
        rarity = get_sleep_reward_rarity(55)
        self.assertEqual(rarity, "Common")
    
    def test_reward_rarity_legendary(self) -> None:
        """Test legendary reward for exceptional score."""
        rarity = get_sleep_reward_rarity(98)
        self.assertEqual(rarity, "Legendary")
    
    def test_entry_reward_short_sleep(self) -> None:
        """Test entry reward for very short sleep."""
        result = check_sleep_entry_reward(
            sleep_hours=2.0, bedtime="01:00", quality_id="poor",
            disruptions=[], chronotype_id="moderate"
        )
        self.assertIsNone(result["reward"])
        self.assertIn("less than 3", result["messages"][0].lower())
    
    def test_entry_reward_good_sleep(self) -> None:
        """Test entry reward for good sleep."""
        result = check_sleep_entry_reward(
            sleep_hours=8.0, bedtime="22:30", quality_id="good",
            disruptions=[], chronotype_id="moderate"
        )
        self.assertIsNotNone(result["score"])
        self.assertGreater(result["score"], 50)
    
    def test_streak_reward_check(self) -> None:
        """Test streak reward checking."""
        today = datetime.now()
        entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "sleep_hours": 8.0}
            for i in range(4)
        ]
        result = check_sleep_streak_reward(entries, [])
        self.assertIsNotNone(result)
        self.assertEqual(result["streak_days"], 3)
    
    def test_streak_reward_already_achieved(self) -> None:
        """Test streak reward not given if already achieved."""
        today = datetime.now()
        entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "sleep_hours": 8.0}
            for i in range(4)
        ]
        result = check_sleep_streak_reward(entries, ["sleep_streak_3"])
        # Should not return 3-day streak again, might return higher tier or None
        if result:
            self.assertNotEqual(result["streak_days"], 3)


class TestSleepMilestones(unittest.TestCase):
    """Tests for sleep milestone checking."""
    
    def test_first_entry_milestone(self) -> None:
        """Test first entry milestone."""
        entries = [{"date": "2024-01-01", "sleep_hours": 7.0}]
        milestones = check_sleep_milestones(entries, [])
        milestone_ids = [m["milestone_id"] for m in milestones]
        self.assertIn("first_sleep", milestone_ids)
    
    def test_milestone_not_repeated(self) -> None:
        """Test milestone not awarded twice."""
        entries = [{"date": "2024-01-01", "sleep_hours": 7.0}]
        milestones = check_sleep_milestones(entries, ["first_sleep"])
        milestone_ids = [m["milestone_id"] for m in milestones]
        self.assertNotIn("first_sleep", milestone_ids)
    
    def test_total_hours_milestone(self) -> None:
        """Test total hours milestone."""
        entries = [
            {"date": f"2024-01-{i:02d}", "sleep_hours": 8.0}
            for i in range(1, 15)  # 14 nights * 8h = 112 hours
        ]
        milestones = check_sleep_milestones(entries, [])
        milestone_ids = [m["milestone_id"] for m in milestones]
        self.assertIn("total_100hr", milestone_ids)
    
    def test_perfect_night_milestone(self) -> None:
        """Test perfect night milestone."""
        entries = [{"date": "2024-01-01", "sleep_hours": 8.0, "score": 96}]
        milestones = check_sleep_milestones(entries, [])
        milestone_ids = [m["milestone_id"] for m in milestones]
        self.assertIn("perfect_night", milestone_ids)


class TestSleepStats(unittest.TestCase):
    """Tests for sleep statistics calculation."""
    
    def test_empty_stats(self) -> None:
        """Test stats for empty entries."""
        stats = get_sleep_stats([])
        self.assertEqual(stats["total_nights"], 0)
        self.assertEqual(stats["avg_hours"], 0)
        self.assertEqual(stats["current_streak"], 0)
    
    def test_basic_stats(self) -> None:
        """Test basic stats calculation."""
        entries = [
            {"date": "2024-01-01", "sleep_hours": 7.0, "score": 70},
            {"date": "2024-01-02", "sleep_hours": 8.0, "score": 85},
            {"date": "2024-01-03", "sleep_hours": 6.0, "score": 55},
        ]
        stats = get_sleep_stats(entries)
        self.assertEqual(stats["total_nights"], 3)
        self.assertAlmostEqual(stats["avg_hours"], 7.0, places=1)
        self.assertEqual(stats["best_score"], 85)
        self.assertEqual(stats["nights_on_target"], 2)  # 7h and 8h nights
    
    def test_target_rate_calculation(self) -> None:
        """Test target rate percentage."""
        entries = [
            {"date": "2024-01-01", "sleep_hours": 8.0},
            {"date": "2024-01-02", "sleep_hours": 8.0},
            {"date": "2024-01-03", "sleep_hours": 5.0},
            {"date": "2024-01-04", "sleep_hours": 7.0},
        ]
        stats = get_sleep_stats(entries)
        self.assertEqual(stats["nights_on_target"], 3)
        self.assertEqual(stats["target_rate"], 75.0)


class TestFormatFunctions(unittest.TestCase):
    """Tests for formatting functions."""
    
    def test_format_sleep_duration(self) -> None:
        """Test sleep duration formatting."""
        self.assertEqual(format_sleep_duration(8.0), "8h")
        self.assertEqual(format_sleep_duration(7.5), "7h 30m")
        self.assertEqual(format_sleep_duration(6.25), "6h 15m")
    
    def test_format_sleep_duration_edge_cases(self) -> None:
        """Test duration formatting edge cases."""
        self.assertEqual(format_sleep_duration(0), "0h")
        self.assertEqual(format_sleep_duration(12.0), "12h")


class TestSleepRecommendations(unittest.TestCase):
    """Tests for sleep recommendations."""
    
    def test_moderate_recommendations(self) -> None:
        """Test recommendations for moderate chronotype."""
        rec = get_sleep_recommendation("moderate")
        self.assertIn("Moderate", rec["chronotype"])
        self.assertIsNotNone(rec["optimal_bedtime"])
        self.assertIsNotNone(rec["recommended_wake"])
        self.assertGreater(len(rec["tips"]), 0)
    
    def test_early_bird_recommendations(self) -> None:
        """Test recommendations for early bird."""
        rec = get_sleep_recommendation("early_bird")
        self.assertIn("Early", rec["chronotype"])
        # Early birds should have earlier optimal bedtime
        self.assertIn("21", rec["optimal_bedtime"])
    
    def test_night_owl_recommendations(self) -> None:
        """Test recommendations for night owl."""
        rec = get_sleep_recommendation("night_owl")
        self.assertIn("Owl", rec["chronotype"])
        # Night owls have later optimal bedtime
        self.assertIn("23", rec["optimal_bedtime"])
    
    def test_invalid_chronotype_fallback(self) -> None:
        """Test invalid chronotype falls back to moderate."""
        rec = get_sleep_recommendation("invalid")
        self.assertIsNotNone(rec["optimal_bedtime"])


class TestComprehensiveRewards(unittest.TestCase):
    """Tests for comprehensive reward checking."""
    
    def test_check_all_sleep_rewards(self) -> None:
        """Test comprehensive reward check."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        existing_entries = [
            {"date": yesterday, "sleep_hours": 8.0, "score": 80}
        ]
        
        result = check_all_sleep_rewards(
            sleep_entries=existing_entries,
            sleep_hours=8.0,
            bedtime="22:30",
            wake_time="06:30",
            quality_id="good",
            disruptions=[],
            current_date=today,
            achieved_milestones=[],
            chronotype_id="moderate",
            story_id="warrior"
        )
        
        self.assertIn("score", result)
        self.assertIn("messages", result)
        self.assertIn("current_streak", result)
        self.assertIn("new_milestones", result)
    
    def test_streak_tracked_correctly(self) -> None:
        """Test streak is tracked in comprehensive check."""
        today = datetime.now()
        existing_entries = [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "sleep_hours": 8.0}
            for i in range(1, 3)  # Yesterday and day before
        ]
        
        result = check_all_sleep_rewards(
            sleep_entries=existing_entries,
            sleep_hours=8.0,
            bedtime="22:30",
            wake_time="06:30",
            quality_id="good",
            disruptions=[],
            current_date=today.strftime("%Y-%m-%d"),
            achieved_milestones=[],
            chronotype_id="moderate",
        )
        
        self.assertGreaterEqual(result["current_streak"], 3)


if __name__ == "__main__":
    unittest.main()
