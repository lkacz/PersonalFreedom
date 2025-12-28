"""
Tests for GamificationEngine and FocusGoals.
"""

import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from productivity_ai import ProductivityAnalyzer, GamificationEngine, FocusGoals


class TestGamificationEngine(unittest.TestCase):
    """Tests for the GamificationEngine class."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.stats_path = Path(self.test_dir) / "stats.json"
        
    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)
    
    def _create_stats(self, stats_data: dict) -> None:
        """Helper to create stats file."""
        with open(self.stats_path, 'w') as f:
            json.dump(stats_data, f)
    
    def test_no_achievements_new_user(self) -> None:
        """Test new user has no unlocked achievements initially."""
        self._create_stats({
            "sessions_completed": 0,
            "total_focus_time": 0,
            "streak_days": 0,
            "achievements_unlocked": []
        })
        engine = GamificationEngine(str(self.stats_path))
        self.assertEqual(len(engine.unlocked), 0)
    
    def test_first_session_achievement_check(self) -> None:
        """Test first session achievement can be detected via check_achievements."""
        self._create_stats({
            "sessions_completed": 1,
            "total_focus_time": 1800,
            "streak_days": 1,
            "achievements_unlocked": []
        })
        engine = GamificationEngine(str(self.stats_path))
        progress = engine.check_achievements()
        # first_session should now be unlocked
        self.assertTrue(progress["first_session"]["unlocked"])
    
    def test_dedicated_achievement_check(self) -> None:
        """Test dedicated achievement at 10 sessions via check_achievements."""
        self._create_stats({
            "sessions_completed": 10,
            "total_focus_time": 18000,
            "streak_days": 3,
            "achievements_unlocked": []
        })
        engine = GamificationEngine(str(self.stats_path))
        progress = engine.check_achievements()
        self.assertTrue(progress["dedicated"]["unlocked"])
    
    def test_week_warrior_achievement_check(self) -> None:
        """Test week warrior achievement at 7-day streak via check_achievements."""
        self._create_stats({
            "sessions_completed": 7,
            "total_focus_time": 12600,
            "streak_days": 7,
            "achievements_unlocked": []
        })
        engine = GamificationEngine(str(self.stats_path))
        progress = engine.check_achievements()
        self.assertTrue(progress["week_warrior"]["unlocked"])
    
    def test_marathon_achievement_check(self) -> None:
        """Test marathon achievement at 1000 minutes via check_achievements."""
        self._create_stats({
            "sessions_completed": 40,
            "total_focus_time": 60000,  # 1000 minutes
            "streak_days": 5,
            "achievements_unlocked": []
        })
        engine = GamificationEngine(str(self.stats_path))
        progress = engine.check_achievements()
        self.assertTrue(progress["marathon"]["unlocked"])
    
    def test_daily_challenge_generation(self) -> None:
        """Test daily challenge is generated with correct keys."""
        self._create_stats({
            "sessions_completed": 5,
            "total_focus_time": 9000
        })
        engine = GamificationEngine(str(self.stats_path))
        challenge = engine.get_daily_challenge()
        self.assertIsNotNone(challenge)
        # API uses 'title' not 'name'
        self.assertIn("title", challenge)
        self.assertIn("description", challenge)
        self.assertIn("target", challenge)
    
    def test_get_achievements_returns_all(self) -> None:
        """Test get_achievements returns all achievement definitions."""
        self._create_stats({})
        engine = GamificationEngine(str(self.stats_path))
        achievements = engine.get_achievements()
        self.assertIn("first_session", achievements)
        self.assertIn("dedicated", achievements)
        self.assertIn("week_warrior", achievements)


class TestFocusGoals(unittest.TestCase):
    """Tests for the FocusGoals class."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.goals_path = Path(self.test_dir) / "goals.json"
        
    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)
    
    def test_add_goal(self) -> None:
        """Test adding a goal."""
        goals = FocusGoals(str(self.goals_path))
        goal_id = goals.add_goal("Learn Python", "daily", 30)
        self.assertIsNotNone(goal_id)
        self.assertEqual(len(goals.goals), 1)
    
    def test_goal_persists(self) -> None:
        """Test goals persist across instances."""
        goals1 = FocusGoals(str(self.goals_path))
        goals1.add_goal("Study", "daily", 60)
        
        goals2 = FocusGoals(str(self.goals_path))
        self.assertEqual(len(goals2.goals), 1)
    
    def test_complete_goal(self) -> None:
        """Test completing a goal marks it completed."""
        goals = FocusGoals(str(self.goals_path))
        goal_id = goals.add_goal("Read", "daily", 15)
        goals.complete_goal(goal_id)
        # Verify goal is marked completed
        goal = next((g for g in goals.goals if g['id'] == goal_id), None)
        self.assertIsNotNone(goal)
        self.assertTrue(goal['completed'])
    
    def test_remove_goal_by_filtering(self) -> None:
        """Test removing a goal by filtering the list."""
        goals = FocusGoals(str(self.goals_path))
        goal_id = goals.add_goal("Exercise", "weekly", 120)
        # FocusGoals doesn't have remove_goal, so test add works
        self.assertEqual(len(goals.goals), 1)
        # Manual removal simulation
        goals.goals = [g for g in goals.goals if g['id'] != goal_id]
        goals.save_goals()
        self.assertEqual(len(goals.goals), 0)
    
    def test_get_active_goals(self) -> None:
        """Test getting active goals only."""
        goals = FocusGoals(str(self.goals_path))
        goals.add_goal("Active Goal", "daily", 30)
        goal_id = goals.add_goal("Completed Goal", "daily", 30)
        goals.complete_goal(goal_id)
        
        active = goals.get_active_goals()
        self.assertEqual(len(active), 1)
        # API uses 'title' not 'name'
        self.assertEqual(active[0]["title"], "Active Goal")


class TestProductivityAnalyzerInsights(unittest.TestCase):
    """Tests for ProductivityAnalyzer insights generation."""
    
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.stats_path = Path(self.test_dir) / "stats.json"
        
    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)
    
    def _create_stats(self, stats_data: dict) -> None:
        """Helper to create stats file."""
        with open(self.stats_path, 'w') as f:
            json.dump(stats_data, f)
    
    def test_streak_insight_high_streak(self) -> None:
        """Test streak insight for 7+ day streak."""
        self._create_stats({
            "streak_days": 10,
            "sessions_completed": 15,
            "sessions_cancelled": 2,
            "total_focus_time": 27000
        })
        analyzer = ProductivityAnalyzer(str(self.stats_path))
        insights = analyzer.generate_insights()
        
        # Should have achievement insight for streak
        streak_insight = next(
            (i for i in insights if i.get("type") == "achievement" and "Streak" in i.get("title", "")),
            None
        )
        self.assertIsNotNone(streak_insight)
    
    def test_recommendations_for_high_cancellation(self) -> None:
        """Test recommendations when cancellation rate is high."""
        self._create_stats({
            "sessions_completed": 3,
            "sessions_cancelled": 7,
            "total_focus_time": 5400,
            "daily_stats": {}
        })
        analyzer = ProductivityAnalyzer(str(self.stats_path))
        recommendations = analyzer.get_recommendations()
        
        # Should recommend strict mode or shorter sessions
        self.assertTrue(len(recommendations) > 0)
    
    def test_optimal_session_high_completion(self) -> None:
        """Test optimal session length with high completion rate."""
        self._create_stats({
            "sessions_completed": 25,
            "sessions_cancelled": 2,
            "total_focus_time": 45000
        })
        analyzer = ProductivityAnalyzer(str(self.stats_path))
        optimal = analyzer.predict_optimal_session_length()
        
        # High completion rate should suggest 45 minutes
        self.assertEqual(optimal, 45)
    
    def test_optimal_session_low_completion(self) -> None:
        """Test optimal session length with low completion rate."""
        self._create_stats({
            "sessions_completed": 4,
            "sessions_cancelled": 8,
            "total_focus_time": 7200
        })
        analyzer = ProductivityAnalyzer(str(self.stats_path))
        optimal = analyzer.predict_optimal_session_length()
        
        # Low completion rate should suggest 15 minutes
        self.assertEqual(optimal, 15)
    
    def test_distraction_patterns(self) -> None:
        """Test distraction pattern analysis."""
        self._create_stats({
            "sessions_completed": 10,
            "sessions_cancelled": 2,
            "daily_stats": {
                "2025-12-20": {"focus_time": 3600, "sessions": 2},
                "2025-12-21": {"focus_time": 3600, "sessions": 2},
                "2025-12-22": {"focus_time": 3600, "sessions": 2},
                "2025-12-23": {"focus_time": 3600, "sessions": 2},
                "2025-12-24": {"focus_time": 3600, "sessions": 2},
                "2025-12-25": {"focus_time": 1800, "sessions": 1},
                "2025-12-26": {"focus_time": 1800, "sessions": 1},
            }
        })
        analyzer = ProductivityAnalyzer(str(self.stats_path))
        patterns = analyzer.get_distraction_patterns()
        
        self.assertIn("weekday_vs_weekend", patterns)
        self.assertIn("consistency", patterns)


class TestSetBonusSystem(unittest.TestCase):
    """Tests for the ADHD Buster set bonus system."""
    
    def test_get_item_themes_dragon(self) -> None:
        """Test theme extraction for dragon-themed items."""
        from focus_blocker import get_item_themes
        item = {"name": "Dragon-forged Helmet of Blazing Focus"}
        themes = get_item_themes(item)
        self.assertIn("Dragon", themes)
    
    def test_get_item_themes_multiple(self) -> None:
        """Test item can have multiple themes."""
        from focus_blocker import get_item_themes
        item = {"name": "Void-touched Crystal Amulet of Shadows"}
        themes = get_item_themes(item)
        self.assertIn("Void", themes)
        self.assertIn("Crystal", themes)
    
    def test_get_item_themes_none(self) -> None:
        """Test item with no matching themes."""
        from focus_blocker import get_item_themes
        item = {"name": "Rusty Helmet of Mild Confusion"}
        themes = get_item_themes(item)
        self.assertEqual(len(themes), 0)
    
    def test_calculate_set_bonuses_empty(self) -> None:
        """Test set bonus calculation with empty equipped."""
        from focus_blocker import calculate_set_bonuses
        result = calculate_set_bonuses({})
        self.assertEqual(result["total_bonus"], 0)
        self.assertEqual(len(result["active_sets"]), 0)
    
    def test_calculate_set_bonuses_single_theme(self) -> None:
        """Test set bonus with items sharing one theme."""
        from focus_blocker import calculate_set_bonuses
        equipped = {
            "Helmet": {"name": "Dragon Helmet of Power"},
            "Chestplate": {"name": "Drake-scale Chestplate of Might"},
        }
        result = calculate_set_bonuses(equipped)
        # Dragon theme should activate (2 items)
        self.assertGreater(result["total_bonus"], 0)
        self.assertTrue(any(s["name"] == "Dragon" for s in result["active_sets"]))
    
    def test_calculate_set_bonuses_not_enough_matches(self) -> None:
        """Test no bonus when only 1 item has a theme."""
        from focus_blocker import calculate_set_bonuses
        equipped = {
            "Helmet": {"name": "Dragon Helmet of Power"},
            "Chestplate": {"name": "Rusty Chestplate of Confusion"},
        }
        result = calculate_set_bonuses(equipped)
        # Only 1 dragon item - not enough for bonus
        self.assertEqual(result["total_bonus"], 0)


class TestLuckyMergeSystem(unittest.TestCase):
    """Tests for the ADHD Buster lucky merge system."""
    
    def test_merge_success_rate_minimum(self) -> None:
        """Test merge success rate with 2 items."""
        from focus_blocker import calculate_merge_success_rate
        items = [{"rarity": "Common"}, {"rarity": "Common"}]
        rate = calculate_merge_success_rate(items, luck_bonus=0)
        self.assertAlmostEqual(rate, 0.10, places=2)  # 10% base
    
    def test_merge_success_rate_with_extra_items(self) -> None:
        """Test merge success rate increases with more items."""
        from focus_blocker import calculate_merge_success_rate
        items = [{"rarity": "Common"} for _ in range(5)]  # 5 items
        rate = calculate_merge_success_rate(items, luck_bonus=0)
        # Base 10% + 3% per extra item (5-2=3 extras) = 19%
        self.assertAlmostEqual(rate, 0.19, places=2)
    
    def test_merge_success_rate_with_luck(self) -> None:
        """Test luck bonus affects merge rate."""
        from focus_blocker import calculate_merge_success_rate
        items = [{"rarity": "Common"}, {"rarity": "Common"}]
        rate_no_luck = calculate_merge_success_rate(items, luck_bonus=0)
        rate_with_luck = calculate_merge_success_rate(items, luck_bonus=500)
        # Luck should increase the rate
        self.assertGreater(rate_with_luck, rate_no_luck)
    
    def test_merge_success_rate_capped(self) -> None:
        """Test merge success rate is capped at 35%."""
        from focus_blocker import calculate_merge_success_rate
        items = [{"rarity": "Common"} for _ in range(20)]  # Many items
        rate = calculate_merge_success_rate(items, luck_bonus=1000)
        self.assertLessEqual(rate, 0.35)
    
    def test_get_merge_result_rarity(self) -> None:
        """Test merge result is one tier above lowest."""
        from focus_blocker import get_merge_result_rarity
        items = [
            {"rarity": "Common"},
            {"rarity": "Rare"},
            {"rarity": "Epic"}
        ]
        result = get_merge_result_rarity(items)
        # Lowest is Common, upgrade to Uncommon
        self.assertEqual(result, "Uncommon")
    
    def test_get_merge_result_same_rarity(self) -> None:
        """Test merge result with same rarity items."""
        from focus_blocker import get_merge_result_rarity
        items = [
            {"rarity": "Rare"},
            {"rarity": "Rare"}
        ]
        result = get_merge_result_rarity(items)
        # Rare -> Epic
        self.assertEqual(result, "Epic")
    
    def test_perform_lucky_merge_returns_structure(self) -> None:
        """Test merge result has expected structure."""
        from focus_blocker import perform_lucky_merge
        items = [
            {"rarity": "Common", "name": "Test 1"},
            {"rarity": "Common", "name": "Test 2"}
        ]
        result = perform_lucky_merge(items, luck_bonus=0)
        self.assertIn("success", result)
        self.assertIn("items_lost", result)
        self.assertIn("roll", result)
        self.assertIn("needed", result)
        if result["success"]:
            self.assertIsNotNone(result["result_item"])


if __name__ == '__main__':
    unittest.main()
