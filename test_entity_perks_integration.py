
import unittest
from entitidex.entity_perks import calculate_active_perks, PerkType, ENTITY_PERKS
from gamification import (
    calculate_character_power, get_power_breakdown, get_entity_perk_bonuses,
    get_hydration_cooldown_minutes, get_hydration_daily_cap,
    HYDRATION_MIN_INTERVAL_HOURS, HYDRATION_MAX_DAILY_GLASSES
)

class MockProgress:
    def __init__(self, collected, exceptional):
        self.collected_entity_ids = collected
        self.exceptional_entities = exceptional

class TestEntityPerks(unittest.TestCase):
    def test_perk_calculation(self):
        # Setup: Warrior 001 (Power +1) and Warrior 002 (Power +5)
        # Warrior 001 is exceptional (Power +2)
        collected = {"warrior_001", "warrior_002"}
        exceptional = {"warrior_001"}
        
        progress = MockProgress(collected, exceptional)
        perks = calculate_active_perks(progress)
        
        # Expected: 2 (warrior_001 ex) + 5 (warrior_002 norm) = 7
        self.assertEqual(perks[PerkType.POWER_FLAT], 7)
        
    def test_gamification_integration(self):
        # Setup hero dict - note: data is stored under "entitidex" key
        adhd_buster = {
            "equipped": {},  # No gear
            "entitidex": {
                "collected_entity_ids": ["warrior_002"],  # +5 Power (list format)
                "exceptional_entities": {}
            }
        }
        
        # Test Power Calculation
        total_power = calculate_character_power(adhd_buster)
        self.assertEqual(total_power, 5)
        
        # Test Breakdown
        breakdown = get_power_breakdown(adhd_buster)
        self.assertEqual(breakdown["entity_bonus"], 5)
        self.assertEqual(breakdown["total_power"], 5)
        
    def test_entity_perk_bonuses_for_merge(self):
        """Test get_entity_perk_bonuses returns correct merge bonuses."""
        # underdog_003 = COIN_DISCOUNT 1 (normal), 2 (exceptional)
        # scholar_005 = MERGE_LUCK 1 (normal), 2 (exceptional)
        # underdog_007 = ALL_LUCK 3 (normal), 5 (exceptional)
        # scientist_002 = MERGE_SUCCESS 1 (normal), 2 (exceptional)
        adhd_buster = {
            "entitidex": {
                "collected_entity_ids": ["underdog_003", "scholar_005", "underdog_007", "scientist_002"],
                "exceptional_entities": {"underdog_003"}  # Exceptional gives +2 discount
            }
        }
        
        bonuses = get_entity_perk_bonuses(adhd_buster)
        
        # Check coin discount (underdog_003 exceptional = 2)
        self.assertEqual(bonuses["coin_discount"], 2)
        
        # Check merge luck (scholar_005 normal = 1)
        self.assertEqual(bonuses["merge_luck"], 1)
        
        # Check all_luck (underdog_007 normal = 3)
        self.assertEqual(bonuses["all_luck"], 3)
        
        # Check merge_success (scientist_002 normal = 1)
        self.assertEqual(bonuses["merge_success"], 1)
        
    def test_entity_perk_bonuses_empty_data(self):
        """Test get_entity_perk_bonuses handles empty data gracefully."""
        adhd_buster = {}
        bonuses = get_entity_perk_bonuses(adhd_buster)
        
        self.assertEqual(bonuses["coin_discount"], 0)
        self.assertEqual(bonuses["merge_luck"], 0)
        self.assertEqual(bonuses["all_luck"], 0)
        self.assertEqual(bonuses["merge_success"], 0)
        
    def test_hydration_cooldown_perk(self):
        """Test hydration cooldown reduction from entity perks."""
        # wanderer_004 = HYDRATION_COOLDOWN -5min (normal), -10min (exceptional)
        # underdog_005 = HYDRATION_COOLDOWN -5min (normal), -10min (exceptional)
        adhd_buster = {
            "entitidex": {
                "collected_entity_ids": ["wanderer_004", "underdog_005"],
                "exceptional_entities": {"wanderer_004"}  # -10min exceptional
            }
        }
        
        # Expected: -10 (wanderer_004 exceptional) + -5 (underdog_005 normal) = -15 min
        # Base is 120 min, so result should be 105 min
        cooldown = get_hydration_cooldown_minutes(adhd_buster)
        self.assertEqual(cooldown, 120 - 15)  # 105 minutes
        
    def test_hydration_cap_perk(self):
        """Test hydration cap increase from entity perks."""
        # wanderer_006 = HYDRATION_CAP +1 (normal/exceptional)
        # underdog_009 = HYDRATION_CAP +1 (normal/exceptional)
        adhd_buster = {
            "entitidex": {
                "collected_entity_ids": ["wanderer_006", "underdog_009"],
                "exceptional_entities": {}
            }
        }
        
        # Expected: +1 + +1 = +2 glasses
        # Base is 5, so result should be 7
        cap = get_hydration_daily_cap(adhd_buster)
        self.assertEqual(cap, HYDRATION_MAX_DAILY_GLASSES + 2)  # 7 glasses
        
    def test_hydration_defaults_no_perks(self):
        """Test hydration uses defaults when no perks collected."""
        adhd_buster = {"entitidex": {}}
        
        cooldown = get_hydration_cooldown_minutes(adhd_buster)
        cap = get_hydration_daily_cap(adhd_buster)
        
        self.assertEqual(cooldown, HYDRATION_MIN_INTERVAL_HOURS * 60)  # 120 min
        self.assertEqual(cap, HYDRATION_MAX_DAILY_GLASSES)  # 5 glasses

    def test_calculate_perks_handles_none_input(self):
        """Test calculate_active_perks handles None input gracefully."""
        perks = calculate_active_perks(None)
        self.assertEqual(perks, {})
        
    def test_calculate_perks_handles_none_collected_ids(self):
        """Test calculate_active_perks handles None collected_entity_ids."""
        perks = calculate_active_perks({"collected_entity_ids": None})
        self.assertEqual(perks, {})
        
    def test_calculate_perks_handles_none_exceptional(self):
        """Test calculate_active_perks handles None exceptional_entities."""
        perks = calculate_active_perks({
            "collected_entity_ids": ["warrior_001"],
            "exceptional_entities": None
        })
        # Should use normal value since exceptional is None
        self.assertEqual(perks[PerkType.POWER_FLAT], 1)


if __name__ == '__main__':
    unittest.main()
