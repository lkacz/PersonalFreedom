"""
Tests for Hero Management and Core Gamification edge cases.

Tests cover:
- Hero data migration with max_power_reached preservation
- get_current_tier with invalid rarity handling
- get_boosted_rarity with invalid tier handling
- Hero sync operations
- Story switching edge cases
"""

import unittest
from gamification import (
    _create_empty_hero,
    _migrate_adhd_buster_data,
    ensure_hero_structure,
    get_current_tier,
    get_boosted_rarity,
    generate_daily_reward_item,
    calculate_character_power,
    get_active_hero,
    sync_hero_data,
    switch_story,
    restart_story,
    get_hero_summary,
    get_all_heroes_summary,
    is_gamification_enabled,
    _sync_flat_to_active_hero,
    _sync_active_hero_to_flat,
    STORY_MODE_ACTIVE,
    STORY_MODE_HERO_ONLY,
    STORY_MODE_DISABLED,
    RARITY_ORDER,
    RARITY_POWER,
)


class TestMigration(unittest.TestCase):
    """Tests for data migration."""
    
    def test_migration_preserves_max_power_reached(self) -> None:
        """Test migration preserves max_power_reached when upgrading from old format."""
        old_data = {
            "inventory": [{"name": "Test Item", "rarity": "Epic", "slot": "weapon"}],
            "equipped": {"weapon": {"name": "Test Sword", "rarity": "Rare", "power": 50}},
            "story_decisions": {"1": "choice_a"},
            "luck_bonus": 15,
            "total_collected": 42,
            "selected_story": "warrior",
            "max_power_reached": 350,  # Key data to preserve!
        }
        
        result = _migrate_adhd_buster_data(old_data)
        
        # Verify migration created proper structure
        self.assertIn("story_heroes", result)
        self.assertIn("warrior", result["story_heroes"])
        
        # Key assertion: max_power_reached should be preserved
        hero = result["story_heroes"]["warrior"]
        self.assertEqual(hero.get("max_power_reached"), 350)
    
    def test_migration_handles_missing_max_power(self) -> None:
        """Test migration handles old data with no max_power_reached field."""
        old_data = {
            "inventory": [],
            "equipped": {},
            "selected_story": "warrior",
        }
        
        result = _migrate_adhd_buster_data(old_data)
        
        # Should default to 0
        hero = result["story_heroes"]["warrior"]
        self.assertEqual(hero.get("max_power_reached"), 0)
    
    def test_migration_skips_already_migrated(self) -> None:
        """Test migration doesn't re-migrate already migrated data."""
        already_migrated = {
            "story_heroes": {"warrior": {"max_power_reached": 100}},
            "story_mode": STORY_MODE_ACTIVE,
            "max_power_reached": 200,  # Flat structure has different value
        }
        
        result = _migrate_adhd_buster_data(already_migrated)
        
        # Should not have changed
        self.assertEqual(result["story_heroes"]["warrior"]["max_power_reached"], 100)


class TestGetCurrentTier(unittest.TestCase):
    """Tests for get_current_tier with edge cases."""
    
    def test_get_current_tier_empty_equipped(self) -> None:
        """Test get_current_tier with no equipped items."""
        adhd = {"equipped": {}}
        self.assertEqual(get_current_tier(adhd), "Common")
    
    def test_get_current_tier_none_values(self) -> None:
        """Test get_current_tier handles None values in equipped."""
        adhd = {"equipped": {"weapon": None, "armor": None}}
        self.assertEqual(get_current_tier(adhd), "Common")
    
    def test_get_current_tier_valid_rarities(self) -> None:
        """Test get_current_tier returns highest rarity."""
        adhd = {
            "equipped": {
                "weapon": {"rarity": "Common"},
                "armor": {"rarity": "Rare"},
                "helmet": {"rarity": "Uncommon"},
            }
        }
        self.assertEqual(get_current_tier(adhd), "Rare")
    
    def test_get_current_tier_invalid_rarity_skipped(self) -> None:
        """Test get_current_tier skips items with invalid rarity."""
        adhd = {
            "equipped": {
                "weapon": {"rarity": "InvalidRarity"},  # Invalid!
                "armor": {"rarity": "Uncommon"},
            }
        }
        # Should skip invalid and return Uncommon
        self.assertEqual(get_current_tier(adhd), "Uncommon")
    
    def test_get_current_tier_all_invalid_rarities(self) -> None:
        """Test get_current_tier returns Common when all rarities are invalid."""
        adhd = {
            "equipped": {
                "weapon": {"rarity": "SuperDuper"},
                "armor": {"rarity": "UltraRare"},
            }
        }
        # Should return Common as default
        self.assertEqual(get_current_tier(adhd), "Common")
    
    def test_get_current_tier_missing_rarity_key(self) -> None:
        """Test get_current_tier handles items without rarity key."""
        adhd = {
            "equipped": {
                "weapon": {"name": "Sword"},  # No rarity key!
                "armor": {"rarity": "Epic"},
            }
        }
        # Item without rarity defaults to Common, Epic is higher
        self.assertEqual(get_current_tier(adhd), "Epic")
    
    def test_get_current_tier_legendary(self) -> None:
        """Test get_current_tier correctly identifies Legendary as highest."""
        adhd = {
            "equipped": {
                "weapon": {"rarity": "Legendary"},
                "armor": {"rarity": "Common"},
            }
        }
        self.assertEqual(get_current_tier(adhd), "Legendary")


class TestGetBoostedRarity(unittest.TestCase):
    """Tests for get_boosted_rarity with edge cases."""
    
    def test_get_boosted_rarity_all_valid_tiers(self) -> None:
        """Test get_boosted_rarity for all valid tiers."""
        self.assertEqual(get_boosted_rarity("Common"), "Uncommon")
        self.assertEqual(get_boosted_rarity("Uncommon"), "Rare")
        self.assertEqual(get_boosted_rarity("Rare"), "Epic")
        self.assertEqual(get_boosted_rarity("Epic"), "Legendary")
        self.assertEqual(get_boosted_rarity("Legendary"), "Legendary")  # Capped
    
    def test_get_boosted_rarity_invalid_tier(self) -> None:
        """Test get_boosted_rarity handles invalid tier gracefully."""
        # Should default to Common (index 0) and boost to Uncommon
        self.assertEqual(get_boosted_rarity("InvalidTier"), "Uncommon")
    
    def test_get_boosted_rarity_empty_string(self) -> None:
        """Test get_boosted_rarity handles empty string."""
        self.assertEqual(get_boosted_rarity(""), "Uncommon")
    
    def test_get_boosted_rarity_case_sensitive(self) -> None:
        """Test get_boosted_rarity is case-sensitive (matches RARITY_ORDER)."""
        # "common" lowercase should not match "Common"
        result = get_boosted_rarity("common")
        self.assertEqual(result, "Uncommon")  # Falls back to Common + 1


class TestGenerateDailyRewardItem(unittest.TestCase):
    """Tests for daily reward generation."""
    
    def test_generate_daily_reward_empty_equipped(self) -> None:
        """Test daily reward with empty equipped gives Uncommon (Common + 1)."""
        adhd = {"equipped": {}}
        item = generate_daily_reward_item(adhd)
        self.assertEqual(item["rarity"], "Uncommon")
    
    def test_generate_daily_reward_with_legendary(self) -> None:
        """Test daily reward with Legendary equipped stays Legendary."""
        adhd = {"equipped": {"weapon": {"rarity": "Legendary"}}}
        item = generate_daily_reward_item(adhd)
        # Can't go higher than Legendary
        self.assertEqual(item["rarity"], "Legendary")
    
    def test_generate_daily_reward_uses_story_id(self) -> None:
        """Test daily reward uses specified story_id."""
        adhd = {"equipped": {}, "active_story": "scholar"}
        item = generate_daily_reward_item(adhd, story_id="warrior")
        # Should use specified story_id, not active_story
        self.assertEqual(item.get("story_theme"), "warrior")


class TestEnsureHeroStructure(unittest.TestCase):
    """Tests for ensure_hero_structure."""
    
    def test_ensure_hero_structure_empty_dict(self) -> None:
        """Test ensure_hero_structure initializes empty dict properly."""
        adhd = {}
        ensure_hero_structure(adhd)
        
        self.assertIn("story_mode", adhd)
        self.assertIn("active_story", adhd)
        self.assertIn("story_heroes", adhd)
        self.assertIn("free_hero", adhd)
    
    def test_ensure_hero_structure_creates_default_story_hero(self) -> None:
        """Test ensure_hero_structure creates hero for default story (warrior)."""
        adhd = {}
        ensure_hero_structure(adhd)
        
        # Default active_story is "warrior"
        self.assertEqual(adhd["active_story"], "warrior")
        self.assertIn("warrior", adhd["story_heroes"])
    
    def test_ensure_hero_structure_preserves_existing_data(self) -> None:
        """Test ensure_hero_structure doesn't overwrite existing data."""
        adhd = {
            "story_mode": STORY_MODE_HERO_ONLY,
            "story_heroes": {"warrior": {"max_power_reached": 500}},
            "free_hero": {"luck_bonus": 25},
        }
        ensure_hero_structure(adhd)
        
        # Data should be preserved
        self.assertEqual(adhd["story_mode"], STORY_MODE_HERO_ONLY)
        self.assertEqual(adhd["story_heroes"]["warrior"]["max_power_reached"], 500)
        self.assertEqual(adhd["free_hero"]["luck_bonus"], 25)


class TestSyncHeroData(unittest.TestCase):
    """Tests for sync_hero_data."""
    
    def test_sync_hero_data_called(self) -> None:
        """Test sync_hero_data can be called without error."""
        adhd = {}
        ensure_hero_structure(adhd)
        
        # Should not raise
        sync_hero_data(adhd)
    
    def test_sync_hero_data_syncs_to_hero(self) -> None:
        """Test sync_hero_data syncs flat structure to hero."""
        adhd = {}
        ensure_hero_structure(adhd)
        
        # Modify flat structure
        adhd["inventory"].append({"name": "Test Item"})
        
        sync_hero_data(adhd)
        
        # Hero should have the item
        hero = get_active_hero(adhd)
        self.assertEqual(len(hero["inventory"]), 1)


class TestSwitchStory(unittest.TestCase):
    """Tests for switch_story."""
    
    def test_switch_story_invalid_story(self) -> None:
        """Test switch_story rejects invalid story ID."""
        adhd = {}
        ensure_hero_structure(adhd)
        
        result = switch_story(adhd, "nonexistent_story")
        
        self.assertFalse(result)
    
    def test_switch_story_valid_story(self) -> None:
        """Test switch_story works for valid story (warrior)."""
        adhd = {}
        ensure_hero_structure(adhd)
        
        # Switch from default warrior to warrior (same story should work)
        result = switch_story(adhd, "warrior")
        
        self.assertTrue(result)
        self.assertEqual(adhd["active_story"], "warrior")
    
    def test_switch_story_maintains_warrior_hero(self) -> None:
        """Test switch_story maintains warrior hero after switch."""
        adhd = {}
        ensure_hero_structure(adhd)
        
        switch_story(adhd, "warrior")
        
        self.assertIn("warrior", adhd["story_heroes"])


class TestRestartStory(unittest.TestCase):
    """Tests for restart_story."""
    
    def test_restart_story_clears_hero(self) -> None:
        """Test restart_story creates fresh hero with empty data."""
        adhd = {
            "active_story": "warrior",
            "inventory": [{"name": "Old Item"}],
            "equipped": {"weapon": {"name": "Old Weapon"}},
        }
        ensure_hero_structure(adhd)
        
        restart_story(adhd, "warrior")
        
        # Flat structure should be cleared
        self.assertEqual(adhd["inventory"], [])
        self.assertEqual(adhd["equipped"], {})
    
    def test_restart_story_invalid_story(self) -> None:
        """Test restart_story rejects invalid story."""
        adhd = {}
        ensure_hero_structure(adhd)
        
        result = restart_story(adhd, "invalid_story")
        
        self.assertFalse(result)


class TestGetHeroSummary(unittest.TestCase):
    """Tests for get_hero_summary."""
    
    def test_get_hero_summary_basic(self) -> None:
        """Test get_hero_summary returns summary dict."""
        adhd = {}
        ensure_hero_structure(adhd)
        
        result = get_hero_summary(adhd)
        
        self.assertIsNotNone(result)
        self.assertIn("power", result)
        self.assertIn("inventory_count", result)
    
    def test_get_hero_summary_counts_items(self) -> None:
        """Test get_hero_summary counts items correctly."""
        adhd = {}
        ensure_hero_structure(adhd)
        
        # Add items to flat structure
        adhd["inventory"].append({"name": "Item1"})
        adhd["inventory"].append({"name": "Item2"})
        adhd["equipped"]["weapon"] = {"name": "Sword", "rarity": "Rare", "power": 50}
        
        # Sync to hero
        sync_hero_data(adhd)
        
        result = get_hero_summary(adhd)
        
        self.assertEqual(result["inventory_count"], 2)
        self.assertEqual(result["equipped_count"], 1)
        self.assertGreater(result["power"], 0)


class TestIsGamificationEnabled(unittest.TestCase):
    """Tests for is_gamification_enabled."""
    
    def test_enabled_in_active_mode(self) -> None:
        """Test gamification is enabled in active story mode."""
        adhd = {"story_mode": STORY_MODE_ACTIVE, "story_heroes": {}}
        ensure_hero_structure(adhd)
        adhd["story_mode"] = STORY_MODE_ACTIVE  # Ensure mode is set after ensure
        
        self.assertTrue(is_gamification_enabled(adhd))
    
    def test_enabled_in_hero_only_mode(self) -> None:
        """Test gamification is enabled in hero-only mode."""
        adhd = {"story_mode": STORY_MODE_HERO_ONLY, "story_heroes": {}}
        ensure_hero_structure(adhd)
        adhd["story_mode"] = STORY_MODE_HERO_ONLY
        
        self.assertTrue(is_gamification_enabled(adhd))
    
    def test_disabled_in_disabled_mode(self) -> None:
        """Test gamification is disabled in disabled mode."""
        adhd = {"story_mode": STORY_MODE_DISABLED, "story_heroes": {}}
        ensure_hero_structure(adhd)
        adhd["story_mode"] = STORY_MODE_DISABLED
        
        self.assertFalse(is_gamification_enabled(adhd))


class TestCalculateCharacterPower(unittest.TestCase):
    """Tests for calculate_character_power."""
    
    def test_power_with_empty_equipped(self) -> None:
        """Test power is 0 with no equipped items."""
        adhd = {"equipped": {}}
        self.assertEqual(calculate_character_power(adhd), 0)
    
    def test_power_with_items(self) -> None:
        """Test power sums from equipped items."""
        adhd = {
            "equipped": {
                "weapon": {"rarity": "Common", "power": 10},
                "armor": {"rarity": "Rare", "power": 50},
            }
        }
        # 10 + 50 = 60, plus any set bonuses
        power = calculate_character_power(adhd, include_set_bonus=False)
        self.assertEqual(power, 60)
    
    def test_power_uses_rarity_default_if_missing(self) -> None:
        """Test power calculation uses rarity default if power key missing."""
        adhd = {
            "equipped": {
                "weapon": {"rarity": "Epic"},  # No power key
            }
        }
        power = calculate_character_power(adhd, include_set_bonus=False)
        self.assertEqual(power, RARITY_POWER["Epic"])


class TestCreateEmptyHero(unittest.TestCase):
    """Tests for _create_empty_hero."""
    
    def test_empty_hero_has_all_keys(self) -> None:
        """Test empty hero has all required keys."""
        hero = _create_empty_hero()
        
        self.assertIn("inventory", hero)
        self.assertIn("equipped", hero)
        self.assertIn("story_decisions", hero)
        self.assertIn("diary", hero)
        self.assertIn("luck_bonus", hero)
        self.assertIn("total_collected", hero)
        self.assertIn("last_daily_reward_date", hero)
        self.assertIn("max_power_reached", hero)
    
    def test_empty_hero_has_correct_defaults(self) -> None:
        """Test empty hero has correct default values."""
        hero = _create_empty_hero()
        
        self.assertEqual(hero["inventory"], [])
        self.assertEqual(hero["equipped"], {})
        self.assertEqual(hero["luck_bonus"], 0)
        self.assertEqual(hero["max_power_reached"], 0)


if __name__ == "__main__":
    unittest.main()
