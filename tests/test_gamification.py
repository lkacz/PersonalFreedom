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
        from gamification import get_item_themes
        item = {"name": "Dragon-forged Helmet of Blazing Focus"}
        themes = get_item_themes(item)
        # In new system, first word is theme
        self.assertIn("Dragon-forged", themes)
    
    def test_get_item_themes_multiple(self) -> None:
        """Test item can have multiple themes."""
        from gamification import get_item_themes
        item = {"name": "Void-touched Crystal Amulet of Shadows"}
        themes = get_item_themes(item)
        self.assertIn("Void-touched", themes)
    
    def test_get_item_themes_none(self) -> None:
        """Test item with no matching themes."""
        from gamification import get_item_themes
        item = {"name": "Rusty Helmet of Mild Confusion"}
        themes = get_item_themes(item)
        # Even Rusty is a theme now
        self.assertIn("Rusty", themes)
    
    def test_calculate_set_bonuses_empty(self) -> None:
        """Test set bonus calculation with empty equipped."""
        from gamification import calculate_set_bonuses
        result = calculate_set_bonuses({})
        self.assertEqual(result["total_bonus"], 0)
        self.assertEqual(len(result["active_sets"]), 0)
    
    def test_calculate_set_bonuses_single_theme(self) -> None:
        """Test set bonus with items sharing one theme."""
        from gamification import calculate_set_bonuses
        equipped = {
            "Helmet": {"name": "Dragon Helmet of Power"},
            "Chestplate": {"name": "Dragon Chestplate of Might"}, # Changed to match first word
        }
        result = calculate_set_bonuses(equipped)
        # Dragon theme should activate (2 items)
        self.assertGreater(result["total_bonus"], 0)
        self.assertTrue(any(s["name"] == "Dragon" for s in result["active_sets"]))
    
    def test_calculate_set_bonuses_not_enough_matches(self) -> None:
        """Test no bonus when only 1 item has a theme."""
        from gamification import calculate_set_bonuses
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
        from gamification import calculate_merge_success_rate
        items = [{"rarity": "Common"}, {"rarity": "Common"}]
        rate = calculate_merge_success_rate(items, items_merge_luck=0)
        self.assertAlmostEqual(rate, 0.25, places=2)  # 25% base
    
    def test_merge_success_rate_with_extra_items(self) -> None:
        """Test merge success rate increases with more items."""
        from gamification import calculate_merge_success_rate
        items = [{"rarity": "Common"} for _ in range(5)]  # 5 items
        rate = calculate_merge_success_rate(items, items_merge_luck=0)
        # Base 25% + 3% per extra item (5-2=3 extras) = 34%
        self.assertAlmostEqual(rate, 0.34, places=2)
    
    def test_merge_success_rate_with_luck(self) -> None:
        """Test luck bonus affects merge rate."""
        from gamification import calculate_merge_success_rate
        items = [{"rarity": "Common"}, {"rarity": "Common"}]
        rate_no_luck = calculate_merge_success_rate(items, items_merge_luck=0)
        rate_with_luck = calculate_merge_success_rate(items, items_merge_luck=1)  # 1 luck = +1% (if treated as percentage points)
        # Luck should increase the rate
        self.assertGreater(rate_with_luck, rate_no_luck)
        # 1 luck should add 0.01 (1%)
        self.assertAlmostEqual(rate_with_luck - rate_no_luck, 0.01, places=3)
    
    def test_merge_success_rate_capped(self) -> None:
        """Test merge success rate is capped at 90%."""
        from gamification import calculate_merge_success_rate
        items = [{"rarity": "Common"} for _ in range(20)]  # Many items
        rate = calculate_merge_success_rate(items, items_merge_luck=1000)
        self.assertLessEqual(rate, 0.90)
    
    def test_get_merge_result_rarity(self) -> None:
        """Test merge result is one tier above HIGHEST non-Common.
        
        Common items are treated as 'fuel' and don't affect tier.
        Only non-Common items determine the base tier.
        Result = highest rarity + 1 tier (capped at Legendary).
        """
        from gamification import get_merge_result_rarity
        items = [
            {"rarity": "Common"},
            {"rarity": "Rare"},
            {"rarity": "Epic"}
        ]
        result = get_merge_result_rarity(items)
        # Common is ignored, highest non-Common is Epic -> Legendary
        self.assertEqual(result, "Legendary")
    
    def test_get_merge_result_same_rarity(self) -> None:
        """Test merge result with same rarity items."""
        from gamification import get_merge_result_rarity
        items = [
            {"rarity": "Rare"},
            {"rarity": "Rare"}
        ]
        result = get_merge_result_rarity(items)
        # Highest is Rare -> Epic
        self.assertEqual(result, "Epic")
    
    def test_perform_lucky_merge_returns_structure(self) -> None:
        """Test merge result has expected structure."""
        from gamification import perform_lucky_merge
        items = [
            {"rarity": "Common", "name": "Test 1"},
            {"rarity": "Common", "name": "Test 2"}
        ]
        result = perform_lucky_merge(items, items_merge_luck=0)
        self.assertIn("success", result)
        self.assertIn("items_lost", result)
        self.assertIn("roll", result)
        self.assertIn("needed", result)
        if result["success"]:
            self.assertIsNotNone(result["result_item"])
    
    def test_is_merge_worthwhile_all_legendary(self) -> None:
        """Legendary-only merges are allowed as rerolls."""
        from gamification import is_merge_worthwhile
        items = [
            {"rarity": "Legendary", "name": "Test 1"},
            {"rarity": "Legendary", "name": "Test 2"}
        ]
        worthwhile, reason = is_merge_worthwhile(items)
        self.assertTrue(worthwhile)
        self.assertEqual("", reason)
    
    def test_is_merge_worthwhile_mixed_rarity(self) -> None:
        """Test merge is worthwhile with mixed rarities."""
        from gamification import is_merge_worthwhile
        items = [
            {"rarity": "Common", "name": "Test 1"},
            {"rarity": "Legendary", "name": "Test 2"}
        ]
        worthwhile, reason = is_merge_worthwhile(items)
        self.assertTrue(worthwhile)
    
    def test_get_item_themes_word_boundary(self) -> None:
        """Test theme detection uses word boundaries (First word logic)."""
        from gamification import get_item_themes
        # Backfire -> theme is Backfire
        item = {"name": "Backfire Helmet of Confusion"}
        themes = get_item_themes(item)
        self.assertIn("Backfire", themes)
        self.assertNotIn("Fire", themes)
        
        # Fire -> theme is Fire
        item2 = {"name": "Fire Helmet of Burning"}
        themes2 = get_item_themes(item2)
        self.assertIn("Fire", themes2)
    
    def test_get_item_themes_star_word_boundary(self) -> None:
        """Test 'star' doesn't match 'upstart'."""
        from gamification import get_item_themes
        item = {"name": "Upstart Helmet of Beginners"}
        themes = get_item_themes(item)
        self.assertIn("Upstart", themes)
        self.assertNotIn("Star", themes)


class TestDailyRewardSystem(unittest.TestCase):
    """Tests for the daily gear reward system functions."""
    
    def test_get_current_tier_empty(self) -> None:
        """Test current tier is Common when nothing equipped."""
        from gamification import get_current_tier
        adhd_buster = {"equipped": {}}
        self.assertEqual(get_current_tier(adhd_buster), "Common")
    
    def test_get_current_tier_with_items(self) -> None:
        """Test current tier returns highest equipped rarity."""
        from gamification import get_current_tier
        adhd_buster = {
            "equipped": {
                "Helmet": {"name": "Test Helmet", "rarity": "Common"},
                "Weapon": {"name": "Test Sword", "rarity": "Rare"},
                "Boots": {"name": "Test Boots", "rarity": "Uncommon"}
            }
        }
        self.assertEqual(get_current_tier(adhd_buster), "Rare")
    
    def test_get_boosted_rarity(self) -> None:
        """Test boosted rarity is one tier higher."""
        from gamification import get_boosted_rarity
        self.assertEqual(get_boosted_rarity("Common"), "Uncommon")
        self.assertEqual(get_boosted_rarity("Uncommon"), "Rare")
        self.assertEqual(get_boosted_rarity("Rare"), "Epic")
        self.assertEqual(get_boosted_rarity("Epic"), "Legendary")
        self.assertEqual(get_boosted_rarity("Legendary"), "Legendary")  # Capped
    
    def test_generate_daily_reward_item(self) -> None:
        """Test daily reward generates correct rarity tier."""
        from gamification import generate_daily_reward_item
        adhd_buster = {
            "equipped": {
                "Helmet": {"name": "Test Helmet", "rarity": "Uncommon"}
            }
        }
        item = generate_daily_reward_item(adhd_buster)
        # Current tier is Uncommon, so reward should be Rare
        self.assertEqual(item["rarity"], "Rare")
        self.assertIn("name", item)
        self.assertIn("power", item)
        self.assertIn("slot", item)


class TestPriorityCompletionReward(unittest.TestCase):
    """Tests for priority completion reward system."""
    
    def test_roll_priority_completion_reward_returns_dict(self) -> None:
        """Test roll returns proper structure."""
        from gamification import roll_priority_completion_reward
        result = roll_priority_completion_reward()
        self.assertIn("won", result)
        self.assertIn("item", result)
        self.assertIn("message", result)
        self.assertIn("chance", result)
        self.assertIsInstance(result["won"], bool)
        self.assertIsInstance(result["message"], str)
        self.assertIsInstance(result["chance"], int)
    
    def test_roll_priority_completion_reward_item_when_won(self) -> None:
        """Test that winning produces a valid item."""
        from gamification import roll_priority_completion_reward
        # Use high hours to ensure high chance of winning
        won_result = None
        for _ in range(50):
            result = roll_priority_completion_reward(logged_hours=20)  # 99% chance
            if result["won"]:
                won_result = result
                break
        
        # Should have won at least once with 99% chance
        self.assertIsNotNone(won_result, "Should have won at least once with 99% chance")
        item = won_result["item"]
        self.assertIsNotNone(item)
        self.assertIn("name", item)
        self.assertIn("rarity", item)
        self.assertIn("slot", item)
        self.assertIn("power", item)
    
    def test_roll_priority_reward_high_tier_weighted(self) -> None:
        """Test that rewards are weighted toward high tiers."""
        from gamification import roll_priority_completion_reward
        rarities = {"Common": 0, "Uncommon": 0, "Rare": 0, "Epic": 0, "Legendary": 0}
        
        # Use high hours to ensure wins for testing distribution
        wins = 0
        for _ in range(200):
            result = roll_priority_completion_reward(logged_hours=20)  # 99% chance
            if result["won"]:
                wins += 1
                rarities[result["item"]["rarity"]] += 1
        
        # With enough wins, high tiers should dominate
        if wins > 50:
            high_tier_count = rarities["Rare"] + rarities["Epic"] + rarities["Legendary"]
            low_tier_count = rarities["Common"] + rarities["Uncommon"]
            # High tiers should be more common than low tiers (85% vs 15%)
            self.assertGreater(high_tier_count, low_tier_count, 
                "High tier rewards should be more common than low tier")
    
    def test_roll_priority_completion_chance_scales_with_hours(self) -> None:
        """Test that win chance scales with logged hours."""
        from gamification import roll_priority_completion_reward
        
        # 0 hours = 15% base chance
        result = roll_priority_completion_reward(logged_hours=0)
        self.assertEqual(result["chance"], 15)
        
        # 10 hours = 15% + (10/20)*84 = 15% + 42% = 57%
        result = roll_priority_completion_reward(logged_hours=10)
        self.assertEqual(result["chance"], 57)
        
        # 20+ hours = 99% max
        result = roll_priority_completion_reward(logged_hours=20)
        self.assertEqual(result["chance"], 99)
        
        # Even more hours still caps at 99%
        result = roll_priority_completion_reward(logged_hours=50)
        self.assertEqual(result["chance"], 99)


class TestStorySystem(unittest.TestCase):
    """Tests for the Story System."""
    
    def test_story_thresholds_defined(self) -> None:
        """Test that story thresholds are defined."""
        from gamification import STORY_THRESHOLDS, STORY_CHAPTERS
        self.assertEqual(len(STORY_THRESHOLDS), 7)
        self.assertEqual(len(STORY_CHAPTERS), 7)
        # Thresholds should be ascending
        for i in range(1, len(STORY_THRESHOLDS)):
            self.assertGreater(STORY_THRESHOLDS[i], STORY_THRESHOLDS[i-1])
    
    def test_get_story_progress_new_user(self) -> None:
        """Test story progress for new user."""
        from gamification import get_story_progress
        adhd_buster = {"equipped": {}, "inventory": []}
        progress = get_story_progress(adhd_buster)
        
        self.assertEqual(progress["power"], 0)
        self.assertEqual(progress["current_chapter"], 1)  # Chapter 1 unlocked at 0
        self.assertIn(1, progress["unlocked_chapters"])
        self.assertEqual(progress["total_chapters"], 7)
    
    def test_get_story_progress_with_power(self) -> None:
        """Test story progress with equipped items."""
        from gamification import get_story_progress
        adhd_buster = {
            "equipped": {
                "Helmet": {"name": "Epic Helmet", "rarity": "Epic", "power": 100},
                "Weapon": {"name": "Rare Sword", "rarity": "Rare", "power": 50}
            },
            "inventory": []
        }
        progress = get_story_progress(adhd_buster)
        
        self.assertEqual(progress["power"], 150)  # 100 + 50
        self.assertGreater(progress["current_chapter"], 1)
        self.assertIn(1, progress["unlocked_chapters"])
        self.assertIn(2, progress["unlocked_chapters"])  # 50 threshold
        self.assertIn(3, progress["unlocked_chapters"])  # 120 threshold
    
    def test_get_chapter_content_unlocked(self) -> None:
        """Test getting content for an unlocked chapter."""
        from gamification import get_chapter_content
        adhd_buster = {"equipped": {}, "inventory": []}
        
        chapter = get_chapter_content(1, adhd_buster)
        
        self.assertIsNotNone(chapter)
        self.assertTrue(chapter["unlocked"])
        self.assertIn("title", chapter)
        self.assertIn("content", chapter)
        self.assertIn("The Echoing Room", chapter["title"])
    
    def test_get_chapter_content_locked(self) -> None:
        """Test getting content for a locked chapter."""
        from gamification import get_chapter_content
        adhd_buster = {"equipped": {}, "inventory": []}
        
        chapter = get_chapter_content(7, adhd_buster)  # Needs 1500 power
        
        self.assertIsNotNone(chapter)
        self.assertFalse(chapter["unlocked"])
        self.assertIn("threshold", chapter)
        self.assertIn("power_needed", chapter)
    
    def test_get_chapter_content_personalized(self) -> None:
        """Test that chapter content is personalized with gear names."""
        from gamification import get_chapter_content
        adhd_buster = {
            "equipped": {
                "Helmet": {"name": "Dragon Crown of Focus", "rarity": "Epic", "power": 100}
            },
            "inventory": []
        }
        
        chapter = get_chapter_content(1, adhd_buster)
        
        self.assertIsNotNone(chapter)
        # The helmet name should appear in the content
        self.assertIn("Dragon Crown of Focus", chapter["content"])
    
    def test_get_newly_unlocked_chapter(self) -> None:
        """Test detecting newly unlocked chapters."""
        from gamification import get_newly_unlocked_chapter
        
        # No new chapter
        result = get_newly_unlocked_chapter(40, 45)
        self.assertIsNone(result)
        
        # New chapter unlocked (threshold at 50)
        result = get_newly_unlocked_chapter(40, 60)
        self.assertEqual(result, 2)
        
        # Multiple chapters unlocked, returns the new one
        result = get_newly_unlocked_chapter(0, 130)
        self.assertEqual(result, 3)  # Crossed 50 and 120, returns 3


class TestStoryDecisions(unittest.TestCase):
    """Tests for the branching story decision system."""
    
    def test_story_decisions_defined(self) -> None:
        """Test that story decisions are defined for specific chapters."""
        from gamification import STORY_DECISIONS
        # Decisions at chapters 2, 4, and 6
        self.assertIn(2, STORY_DECISIONS)
        self.assertIn(4, STORY_DECISIONS)
        self.assertIn(6, STORY_DECISIONS)
        self.assertEqual(len(STORY_DECISIONS), 3)
    
    def test_decision_structure(self) -> None:
        """Test that each decision has required fields."""
        from gamification import STORY_DECISIONS
        for chapter_num, decision in STORY_DECISIONS.items():
            self.assertIn("id", decision)
            self.assertIn("prompt", decision)
            self.assertIn("choices", decision)
            self.assertIn("A", decision["choices"])
            self.assertIn("B", decision["choices"])
            # Each choice should have label and description
            for choice in ["A", "B"]:
                self.assertIn("label", decision["choices"][choice])
                self.assertIn("description", decision["choices"][choice])
    
    def test_get_decision_for_chapter(self) -> None:
        """Test getting decision info for a chapter."""
        from gamification import get_decision_for_chapter
        
        # Chapter with decision (default warrior story)
        adhd_buster = {}  # Uses default warrior story
        decision = get_decision_for_chapter(2, adhd_buster)
        self.assertIsNotNone(decision)
        self.assertEqual(decision["id"], "warrior_mirror")
        
        # Chapter without decision
        decision = get_decision_for_chapter(1, adhd_buster)
        self.assertIsNone(decision)
    
    def test_has_made_decision(self) -> None:
        """Test checking if a decision has been made."""
        from gamification import has_made_decision
        
        # No decisions made
        adhd_buster = {"story_decisions": {}}
        self.assertFalse(has_made_decision(adhd_buster, 2))
        
        # Decision made (warrior story IDs)
        adhd_buster = {"story_decisions": {"warrior_mirror": "A"}}
        self.assertTrue(has_made_decision(adhd_buster, 2))
        
        # Chapter without decision returns True (no decision needed)
        self.assertTrue(has_made_decision(adhd_buster, 1))
    
    def test_make_story_decision(self) -> None:
        """Test making a story decision."""
        from gamification import make_story_decision
        
        adhd_buster = {}
        
        # Make decision for chapter 2
        result = make_story_decision(adhd_buster, 2, "A")
        self.assertTrue(result)
        self.assertEqual(adhd_buster["story_decisions"]["warrior_mirror"], "A")
        
        # Invalid choice - returns dict with success=False
        result = make_story_decision(adhd_buster, 2, "C")
        self.assertFalse(result.get("success", True))
        
        # Chapter without decision - returns dict with success=False
        result = make_story_decision(adhd_buster, 1, "A")
        self.assertFalse(result.get("success", True))
    
    def test_get_decision_path(self) -> None:
        """Test getting the decision path string."""
        from gamification import get_decision_path
        
        # No decisions
        adhd_buster = {"story_decisions": {}}
        self.assertEqual(get_decision_path(adhd_buster), "")
        
        # One decision (warrior story IDs)
        adhd_buster = {"story_decisions": {"warrior_mirror": "A"}}
        self.assertEqual(get_decision_path(adhd_buster), "A")
        
        # Two decisions
        adhd_buster = {"story_decisions": {"warrior_mirror": "B", "warrior_fortress": "A"}}
        self.assertEqual(get_decision_path(adhd_buster), "BA")
        
        # All three decisions
        adhd_buster = {"story_decisions": {
            "warrior_mirror": "A",
            "warrior_fortress": "B",
            "warrior_war": "A"
        }}
        self.assertEqual(get_decision_path(adhd_buster), "ABA")
    
    def test_chapter_7_requires_all_decisions(self) -> None:
        """Test that chapter 7 content requires all decisions."""
        from gamification import get_chapter_content
        
        # Power high enough for chapter 7 (1500+)
        adhd_buster = {
            "equipped": {
                "Helmet": {"power": 300},
                "Weapon": {"power": 300},
                "Chestplate": {"power": 300},
                "Shield": {"power": 300},
                "Gauntlets": {"power": 200},
                "Boots": {"power": 200},
            },
            "inventory": [],
            "story_decisions": {"warrior_mirror": "A"}  # Only 1 decision
        }
        
        chapter = get_chapter_content(7, adhd_buster)
        
        self.assertIsNotNone(chapter)
        self.assertTrue(chapter["unlocked"])
        self.assertIn("not yet complete", chapter["content"])
        self.assertIn("1/3", chapter["content"])
    
    def test_chapter_7_endings_by_path(self) -> None:
        """Test that chapter 7 has different endings based on decisions."""
        from gamification import get_chapter_content
        
        # Power high enough for chapter 7
        base_equipped = {
            "Helmet": {"power": 300},
            "Weapon": {"power": 300},
            "Chestplate": {"power": 300},
            "Shield": {"power": 300},
            "Gauntlets": {"power": 200},
            "Boots": {"power": 200},
        }
        
        # Path AAA - "The Destroyer" (warrior story)
        adhd_buster_aaa = {
            "equipped": base_equipped,
            "inventory": [],
            "story_decisions": {
                "warrior_mirror": "A",
                "warrior_fortress": "A",
                "warrior_war": "A"
            }
        }
        chapter_aaa = get_chapter_content(7, adhd_buster_aaa)
        self.assertIn("DESTROYER", chapter_aaa["content"])
        
        # Path BBB - "The Transcendent"
        adhd_buster_bbb = {
            "equipped": base_equipped,
            "inventory": [],
            "story_decisions": {
                "warrior_mirror": "B",
                "warrior_fortress": "B",
                "warrior_war": "B"
            }
        }
        chapter_bbb = get_chapter_content(7, adhd_buster_bbb)
        self.assertIn("TRANSCENDENT", chapter_bbb["content"].upper())
        
        # Different paths should have different content
        self.assertNotEqual(chapter_aaa["content"], chapter_bbb["content"])
    
    def test_story_progress_includes_chapters_with_decisions(self) -> None:
        """Test that story progress includes chapter decision info."""
        from gamification import get_story_progress
        
        adhd_buster = {
            "equipped": {"Weapon": {"power": 100}},
            "inventory": [],
            "story_decisions": {"warrior_mirror": "A"}
        }
        
        progress = get_story_progress(adhd_buster)
        
        self.assertIn("chapters", progress)
        self.assertIsInstance(progress["chapters"], list)
        
        # Find chapter 2 (has decision)
        ch2 = next(ch for ch in progress["chapters"] if ch["number"] == 2)
        self.assertTrue(ch2["has_decision"])
        self.assertTrue(ch2["decision_made"])
        
        # Find chapter 4 (has decision, not made)
        ch4 = next(ch for ch in progress["chapters"] if ch["number"] == 4)
        self.assertTrue(ch4["has_decision"])
        self.assertFalse(ch4["decision_made"])


class TestMultiStorySystem(unittest.TestCase):
    """Tests for the multi-story selection system."""
    
    def test_available_stories_defined(self) -> None:
        """Test that multiple stories are available."""
        from gamification import AVAILABLE_STORIES
        self.assertEqual(len(AVAILABLE_STORIES), 5)
        self.assertIn("warrior", AVAILABLE_STORIES)
        self.assertIn("scholar", AVAILABLE_STORIES)
        self.assertIn("wanderer", AVAILABLE_STORIES)
        self.assertIn("underdog", AVAILABLE_STORIES)
        self.assertIn("scientist", AVAILABLE_STORIES)
    
    def test_story_has_required_fields(self) -> None:
        """Test that each story has required fields."""
        from gamification import AVAILABLE_STORIES
        for story_id, story in AVAILABLE_STORIES.items():
            self.assertIn("id", story)
            self.assertIn("title", story)
            self.assertIn("description", story)
            self.assertIn("theme", story)
    
    def test_get_selected_story_default(self) -> None:
        """Test that default story is warrior."""
        from gamification import get_selected_story
        adhd_buster = {}
        self.assertEqual(get_selected_story(adhd_buster), "warrior")
    
    def test_select_story(self) -> None:
        """Test selecting a different story."""
        from gamification import select_story, get_selected_story
        adhd_buster = {}
        
        # Select scholar story
        result = select_story(adhd_buster, "scholar")
        self.assertTrue(result)
        self.assertEqual(get_selected_story(adhd_buster), "scholar")
        
        # Invalid story returns False
        result = select_story(adhd_buster, "invalid_story")
        self.assertFalse(result)
    
    def test_select_story_clears_decisions(self) -> None:
        """Test that switching stories clears previous decisions."""
        from gamification import select_story
        adhd_buster = {
            "selected_story": "warrior",
            "story_decisions": {"warrior_mirror": "A", "warrior_fortress": "B"}
        }
        
        # Switch to scholar
        select_story(adhd_buster, "scholar")
        self.assertEqual(adhd_buster["story_decisions"], {})
    
    def test_story_data_exists_for_all_stories(self) -> None:
        """Test that each story has decisions and chapters."""
        from gamification import STORY_DATA
        for story_id in ["warrior", "scholar", "wanderer", "underdog"]:
            self.assertIn(story_id, STORY_DATA)
            self.assertIn("decisions", STORY_DATA[story_id])
            self.assertIn("chapters", STORY_DATA[story_id])
            # Each story should have 7 chapters
            self.assertEqual(len(STORY_DATA[story_id]["chapters"]), 7)
            # Each story should have 3 decisions
            self.assertEqual(len(STORY_DATA[story_id]["decisions"]), 3)
    
    def test_scholar_story_content(self) -> None:
        """Test that scholar story has unique content."""
        from gamification import get_chapter_content, select_story
        adhd_buster = {"equipped": {}, "inventory": []}
        select_story(adhd_buster, "scholar")
        
        chapter = get_chapter_content(1, adhd_buster)
        self.assertIsNotNone(chapter)
        self.assertIn("Shelves in Waiting", chapter["title"])
    
    def test_wanderer_story_content(self) -> None:
        """Test that wanderer story has unique content."""
        from gamification import get_chapter_content, select_story
        adhd_buster = {"equipped": {}, "inventory": []}
        select_story(adhd_buster, "wanderer")
        
        chapter = get_chapter_content(1, adhd_buster)
        self.assertIsNotNone(chapter)
        self.assertIn("Clocks in the Fog", chapter["title"])
    
    def test_underdog_story_content(self) -> None:
        """Test that underdog story has unique content."""
        from gamification import get_chapter_content, select_story
        adhd_buster = {"equipped": {}, "inventory": []}
        select_story(adhd_buster, "underdog")
        
        chapter = get_chapter_content(1, adhd_buster)
        self.assertIsNotNone(chapter)
        self.assertIn("Commuter Static", chapter["title"])
    
    def test_story_progress_includes_story_info(self) -> None:
        """Test that story progress includes selected story info."""
        from gamification import get_story_progress
        adhd_buster = {"equipped": {}, "inventory": []}
        
        progress = get_story_progress(adhd_buster)
        
        self.assertIn("selected_story", progress)
        self.assertIn("story_info", progress)
        self.assertEqual(progress["selected_story"], "warrior")


class TestHeroManagement(unittest.TestCase):
    """Tests for the new hero management system."""
    
    def test_ensure_hero_structure_creates_new(self) -> None:
        """Test that ensure_hero_structure creates proper structure for new users."""
        from gamification import ensure_hero_structure, STORY_MODE_ACTIVE
        adhd_buster = {}
        
        ensure_hero_structure(adhd_buster)
        
        self.assertIn("story_mode", adhd_buster)
        self.assertIn("active_story", adhd_buster)
        self.assertIn("story_heroes", adhd_buster)
        self.assertIn("free_hero", adhd_buster)
        self.assertEqual(adhd_buster["story_mode"], STORY_MODE_ACTIVE)
    
    def test_migration_preserves_existing_data(self) -> None:
        """Test that migration preserves existing user data."""
        from gamification import ensure_hero_structure
        
        # Simulate old data format
        adhd_buster = {
            "inventory": [{"name": "Test Sword", "power": 10}],
            "equipped": {"weapon": {"name": "Old Sword", "power": 5}},
            "story_decisions": {"decision_1": "A"},
            "selected_story": "scholar",
            "luck_bonus": 5,
            "total_collected": 10,
        }
        
        ensure_hero_structure(adhd_buster)
        
        # Check data was preserved in the story hero
        self.assertIn("scholar", adhd_buster["story_heroes"])
        hero = adhd_buster["story_heroes"]["scholar"]
        self.assertEqual(len(hero["inventory"]), 1)
        self.assertEqual(hero["equipped"]["weapon"]["name"], "Old Sword")
        self.assertEqual(hero["story_decisions"]["decision_1"], "A")
        self.assertEqual(hero["luck_bonus"], 5)
    
    def test_switch_story_saves_and_loads_hero(self) -> None:
        """Test that switching stories saves current hero and loads new one."""
        from gamification import ensure_hero_structure, switch_story
        
        # Start with warrior
        adhd_buster = {"inventory": [], "equipped": {}}
        ensure_hero_structure(adhd_buster)
        
        # Add items to warrior hero
        adhd_buster["equipped"]["weapon"] = {"name": "Warrior Sword", "power": 20}
        adhd_buster["inventory"].append({"name": "Warrior Item", "power": 10})
        
        # Switch to scholar
        switch_story(adhd_buster, "scholar")
        
        # Scholar should have empty gear
        self.assertEqual(len(adhd_buster["inventory"]), 0)
        self.assertEqual(len(adhd_buster["equipped"]), 0)
        
        # Add scholar items
        adhd_buster["equipped"]["head"] = {"name": "Scholar Hat", "power": 15}
        
        # Switch back to warrior
        switch_story(adhd_buster, "warrior")
        
        # Warrior items should be back
        self.assertEqual(adhd_buster["equipped"]["weapon"]["name"], "Warrior Sword")
        self.assertEqual(len(adhd_buster["inventory"]), 1)
        
        # Switch back to scholar
        switch_story(adhd_buster, "scholar")
        
        # Scholar hat should still be there
        self.assertEqual(adhd_buster["equipped"]["head"]["name"], "Scholar Hat")
    
    def test_restart_story_clears_hero(self) -> None:
        """Test that restarting a story clears that hero's progress."""
        from gamification import ensure_hero_structure, restart_story
        
        adhd_buster = {
            "inventory": [{"name": "Item"}],
            "equipped": {"weapon": {"name": "Sword"}},
            "story_decisions": {"d1": "A"},
        }
        ensure_hero_structure(adhd_buster)
        
        restart_story(adhd_buster, "warrior")
        
        # Hero should be empty now
        self.assertEqual(len(adhd_buster["inventory"]), 0)
        self.assertEqual(len(adhd_buster["equipped"]), 0)
        self.assertEqual(len(adhd_buster["story_decisions"]), 0)
    
    def test_story_modes(self) -> None:
        """Test story mode switching."""
        from gamification import (
            ensure_hero_structure, set_story_mode, get_story_mode,
            is_gamification_enabled, is_story_enabled,
            STORY_MODE_ACTIVE, STORY_MODE_HERO_ONLY, STORY_MODE_DISABLED
        )
        
        adhd_buster = {}
        ensure_hero_structure(adhd_buster)
        
        # Default is story mode
        self.assertEqual(get_story_mode(adhd_buster), STORY_MODE_ACTIVE)
        self.assertTrue(is_gamification_enabled(adhd_buster))
        self.assertTrue(is_story_enabled(adhd_buster))
        
        # Switch to hero only
        set_story_mode(adhd_buster, STORY_MODE_HERO_ONLY)
        self.assertEqual(get_story_mode(adhd_buster), STORY_MODE_HERO_ONLY)
        self.assertTrue(is_gamification_enabled(adhd_buster))
        self.assertFalse(is_story_enabled(adhd_buster))
        
        # Switch to disabled
        set_story_mode(adhd_buster, STORY_MODE_DISABLED)
        self.assertEqual(get_story_mode(adhd_buster), STORY_MODE_DISABLED)
        self.assertFalse(is_gamification_enabled(adhd_buster))
        self.assertFalse(is_story_enabled(adhd_buster))
    
    def test_get_active_hero_returns_correct_hero(self) -> None:
        """Test that get_active_hero returns the right hero based on mode."""
        from gamification import (
            ensure_hero_structure, get_active_hero, set_story_mode, switch_story,
            STORY_MODE_ACTIVE, STORY_MODE_HERO_ONLY, STORY_MODE_DISABLED
        )
        
        adhd_buster = {}
        ensure_hero_structure(adhd_buster)
        
        # In story mode, get story hero
        adhd_buster["story_heroes"]["warrior"]["inventory"].append({"name": "Story Item"})
        hero = get_active_hero(adhd_buster)
        self.assertEqual(len(hero["inventory"]), 1)
        
        # In hero only mode, get free hero
        set_story_mode(adhd_buster, STORY_MODE_HERO_ONLY)
        adhd_buster["free_hero"]["inventory"].append({"name": "Free Item"})
        hero = get_active_hero(adhd_buster)
        self.assertEqual(len(hero["inventory"]), 1)
        self.assertEqual(hero["inventory"][0]["name"], "Free Item")
        
        # In disabled mode, get None
        set_story_mode(adhd_buster, STORY_MODE_DISABLED)
        hero = get_active_hero(adhd_buster)
        self.assertIsNone(hero)
    
    def test_get_hero_summary(self) -> None:
        """Test hero summary generation."""
        from gamification import ensure_hero_structure, get_hero_summary
        
        adhd_buster = {
            "equipped": {"weapon": {"name": "Sword", "power": 25, "rarity": "Rare"}},
            "inventory": [{"name": "Item1"}, {"name": "Item2"}],
            "total_collected": 15,
        }
        ensure_hero_structure(adhd_buster)
        
        summary = get_hero_summary(adhd_buster)
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary["story_id"], "warrior")
        self.assertEqual(summary["inventory_count"], 2)
        self.assertEqual(summary["equipped_count"], 1)
        self.assertGreater(summary["power"], 0)
    
    def test_get_all_heroes_summary(self) -> None:
        """Test all heroes summary."""
        from gamification import ensure_hero_structure, get_all_heroes_summary, switch_story
        
        adhd_buster = {}
        ensure_hero_structure(adhd_buster)
        
        # Add some progress to warrior
        adhd_buster["story_heroes"]["warrior"]["total_collected"] = 10
        
        # Create scholar hero with progress
        switch_story(adhd_buster, "scholar")
        adhd_buster["story_heroes"]["scholar"]["total_collected"] = 5
        
        summary = get_all_heroes_summary(adhd_buster)
        
        self.assertIn("story_heroes", summary)
        self.assertIn("free_hero", summary)
        self.assertEqual(summary["story_mode"], "story")
        
        # Should have all stories
        self.assertEqual(len(summary["story_heroes"]), 5)
        
        # Warrior and scholar should have progress
        warrior = next(h for h in summary["story_heroes"] if h["story_id"] == "warrior")
        scholar = next(h for h in summary["story_heroes"] if h["story_id"] == "scholar")
        self.assertTrue(warrior["has_progress"])
        self.assertTrue(scholar["has_progress"])
    
    def test_sync_hero_data_after_modifications(self) -> None:
        """Test that sync_hero_data updates hero after flat modifications."""
        from gamification import ensure_hero_structure, sync_hero_data, switch_story
        
        adhd_buster = {}
        ensure_hero_structure(adhd_buster)
        
        # Modify flat structure (simulating old code)
        adhd_buster["inventory"].append({"name": "New Item"})
        adhd_buster["equipped"]["weapon"] = {"name": "New Sword"}
        
        # Sync back to hero
        sync_hero_data(adhd_buster)
        
        # Switch to another story and back
        switch_story(adhd_buster, "scholar")
        switch_story(adhd_buster, "warrior")
        
        # Data should be preserved
        self.assertEqual(len(adhd_buster["inventory"]), 1)
        self.assertEqual(adhd_buster["equipped"]["weapon"]["name"], "New Sword")
    
    def test_backward_compatibility_with_select_story(self) -> None:
        """Test that select_story still works with new system."""
        from gamification import select_story, get_selected_story, ensure_hero_structure
        
        adhd_buster = {}
        
        # Old code would just set selected_story
        success = select_story(adhd_buster, "scholar")
        
        self.assertTrue(success)
        self.assertEqual(get_selected_story(adhd_buster), "scholar")
        
        # Should have created structure
        self.assertIn("story_heroes", adhd_buster)
    
    def test_invalid_story_rejected(self) -> None:
        """Test that invalid story IDs are rejected."""
        from gamification import switch_story, restart_story
        
        adhd_buster = {}
        
        self.assertFalse(switch_story(adhd_buster, "nonexistent"))
        self.assertFalse(restart_story(adhd_buster, "invalid_story"))
    
    def test_decisions_are_per_story(self) -> None:
        """Test that story decisions are stored per-story."""
        from gamification import ensure_hero_structure, switch_story, make_story_decision
        
        adhd_buster = {}
        ensure_hero_structure(adhd_buster)
        
        # Make decision in warrior story (chapter 2 has ID "warrior_mirror")
        make_story_decision(adhd_buster, 2, "A")
        self.assertEqual(adhd_buster["story_decisions"]["warrior_mirror"], "A")
        
        # Switch to scholar
        switch_story(adhd_buster, "scholar")
        
        # Scholar should have no decisions
        self.assertEqual(len(adhd_buster["story_decisions"]), 0)
        
        # Make decision in scholar (chapter 4 has ID "scholar_echo")
        make_story_decision(adhd_buster, 4, "B")
        
        # Switch back to warrior
        switch_story(adhd_buster, "warrior")
        
        # Warrior's decision should still be there
        self.assertEqual(adhd_buster["story_decisions"]["warrior_mirror"], "A")
        self.assertNotIn("scholar_echo", adhd_buster["story_decisions"])


if __name__ == '__main__':
    unittest.main()
