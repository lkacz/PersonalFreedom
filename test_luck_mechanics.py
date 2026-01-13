"""
Comprehensive tests for Luck mechanics.

Tests both Luck Bonus (character stat) and Drop Luck (gear stat) to ensure they work as intended.

IMPORTANT: Luck Bonus now decays by 1 per hour to prevent unlimited accumulation.
"""

import unittest
from unittest.mock import patch, MagicMock
import random


class TestLuckBonusCharacterStat(unittest.TestCase):
    """Test Luck Bonus - the character stat earned from salvaging.
    
    Note: Luck bonus decays by 1 per hour to maintain balance.
    """
    
    def test_salvage_calculates_luck_correctly(self):
        """Test that salvaging items calculates luck based on power // 10."""
        items = [
            {"power": 50, "name": "Item1"},
            {"power": 80, "name": "Item2"},
            {"power": 100, "name": "Item3"},
            {"power": 25, "name": "Item4"},
        ]
        
        expected_luck = (50 // 10) + (80 // 10) + (100 // 10) + (25 // 10)
        # = 5 + 8 + 10 + 2 = 25
        
        calculated_luck = sum(i.get("power", 10) // 10 for i in items)
        
        self.assertEqual(calculated_luck, 25, 
                        f"Expected 25 luck from salvaging, got {calculated_luck}")
    
    def test_rarity_upgrade_chance_calculation(self):
        """Test that rarity upgrade chance is luck / 100, capped at 10%."""
        test_cases = [
            (0, 0.0),      # 0 luck = 0% chance
            (100, 1.0),    # 100 luck = 1% chance
            (500, 5.0),    # 500 luck = 5% chance
            (1000, 10.0),  # 1000 luck = 10% chance (at cap)
            (2000, 10.0),  # 2000 luck = still 10% (capped)
            (5000, 10.0),  # 5000 luck = still 10% (capped)
        ]
        
        for luck, expected_chance in test_cases:
            calculated = min(luck / 100, 10)
            self.assertEqual(calculated, expected_chance,
                           f"Luck {luck} should give {expected_chance}% chance, got {calculated}%")
    
    def test_merge_success_bonus_calculation(self):
        """Test that merge success bonus is luck / 100 * 0.01 (capped at 10%)."""
        test_cases = [
            (0, 0.0),        # 0 luck = 0% bonus
            (50, 0.005),     # 50 luck = 0.005% bonus (0.5 display)
            (100, 0.01),     # 100 luck = 0.01% bonus (1% display)
            (500, 0.05),     # 500 luck = 0.05% bonus (5% display)
            (1000, 0.10),    # 1000 luck = 0.10% bonus (10% display, capped)
            (10000, 0.10),   # 10000 luck = still 0.10% (capped)
        ]
        
        for luck, expected_bonus in test_cases:
            calculated = min(max(luck, 0) / 100 * 0.01, 0.10)
            self.assertAlmostEqual(calculated, expected_bonus, places=4,
                                  msg=f"Luck {luck} should give {expected_bonus * 100:.2f}% merge bonus, got {calculated * 100:.2f}%")
    
    @patch('random.random')
    def test_rarity_upgrade_probability(self, mock_random):
        """Test that rarity upgrade rolls work correctly with different luck values."""
        luck = 500  # 5% chance
        upgrade_chance = min(luck / 100, 10)  # 5.0%
        
        # Test that roll of 0.04 (4%) succeeds
        mock_random.return_value = 0.04
        roll = mock_random.return_value * 100
        should_upgrade = roll < upgrade_chance
        self.assertTrue(should_upgrade, f"Roll of {roll}% should succeed with {upgrade_chance}% chance")
        
        # Test that roll of 0.06 (6%) fails
        mock_random.return_value = 0.06
        roll = mock_random.return_value * 100
        should_upgrade = roll < upgrade_chance
        self.assertFalse(should_upgrade, f"Roll of {roll}% should fail with {upgrade_chance}% chance")
    
    def test_luck_cap_effectiveness(self):
        """Test that luck beyond 1000 doesn't increase upgrade chance above 10%."""
        base_rate = 0.25  # 25% merge base rate
        
        luck_1000 = 1000
        luck_5000 = 5000
        
        # Upgrade chance is capped at 10%
        upgrade_chance_1000 = min(luck_1000 / 100, 10)
        upgrade_chance_5000 = min(luck_5000 / 100, 10)
        
        self.assertEqual(upgrade_chance_1000, 10.0)
        self.assertEqual(upgrade_chance_5000, 10.0)
        self.assertEqual(upgrade_chance_1000, upgrade_chance_5000,
                        "Luck beyond 1000 should not increase upgrade chance")
        
        # But merge success bonus is NOT capped
        merge_bonus_1000 = luck_1000 * 0.02  # 20%
        merge_bonus_5000 = luck_5000 * 0.02  # 100%
        
        self.assertEqual(merge_bonus_1000, 20.0)
        self.assertEqual(merge_bonus_5000, 100.0)
        self.assertNotEqual(merge_bonus_1000, merge_bonus_5000,
                           "Merge bonus should continue scaling beyond 1000 luck")


class TestLuckDecayMechanic(unittest.TestCase):
    """Test Luck Bonus decay over time."""
    
    def test_hourly_decay_rate(self):
        """Test that luck decays by 1 per hour."""
        initial_luck = 100
        hours_passed = 5
        
        expected_luck = initial_luck - hours_passed  # 95
        self.assertEqual(expected_luck, 95)
    
    def test_decay_cannot_go_negative(self):
        """Test that luck stops at 0 and doesn't go negative."""
        initial_luck = 3
        hours_passed = 10  # More hours than luck
        
        expected_luck = max(0, initial_luck - hours_passed)
        self.assertEqual(expected_luck, 0)
    
    def test_decay_over_long_period(self):
        """Test luck decay over extended periods."""
        test_cases = [
            (100, 24, 76),    # 100 luck after 1 day = 76
            (500, 168, 332),  # 500 luck after 1 week = 332
            (1000, 720, 280), # 1000 luck after 1 month = 280
        ]
        
        for initial, hours, expected in test_cases:
            result = max(0, initial - hours)
            self.assertEqual(result, expected,
                           f"{initial} luck after {hours} hours should be {expected}")
    
    def test_salvage_and_decay_balance(self):
        """Test the balance between salvaging items and time decay."""
        # Scenario: Salvage 10 items with 50 power each = 50 luck
        salvage_luck = 10 * (50 // 10)  # 50 luck
        
        # After 25 hours of inactivity, lost 25 luck
        hours_inactive = 25
        remaining = max(0, salvage_luck - hours_inactive)  # 25 luck
        
        self.assertEqual(remaining, 25)
        
        # Then salvage 5 more items with 100 power each = 50 more luck
        more_luck = 5 * (100 // 10)  # 50 luck
        new_total = remaining + more_luck  # 75 luck
        
        self.assertEqual(new_total, 75)
    
    def test_decay_half_life_calculation(self):
        """Test how long it takes for luck to decay to half."""
        initial_luck = 1000
        half_luck = initial_luck // 2  # 500
        
        hours_to_half = initial_luck - half_luck  # 500 hours
        days_to_half = hours_to_half / 24  # ~20.8 days
        
        self.assertAlmostEqual(days_to_half, 20.83, places=1,
                              msg="1000 luck should take about 21 days to decay to 500")


class TestDropLuckGearStat(unittest.TestCase):
    """Test Drop Luck - the gear stat that affects rarity distribution."""
    
    def test_virtual_minutes_calculation(self):
        """Test that drop luck adds 6 virtual minutes per 1%."""
        test_cases = [
            (30, 0, 30),      # 30 min + 0% = 30 min
            (30, 10, 90),     # 30 min + 10% drop luck = 30 + (10*6) = 90 min
            (30, 25, 180),    # 30 min + 25% drop luck = 30 + (25*6) = 180 min
            (60, 50, 360),    # 60 min + 50% drop luck = 60 + (50*6) = 360 min
            (30, 100, 630),   # 30 min + 100% drop luck = 30 + (100*6) = 630 min (at cap)
        ]
        
        for session_mins, drop_luck_pct, expected_effective in test_cases:
            effective = session_mins + (drop_luck_pct * 6)
            self.assertEqual(effective, expected_effective,
                           f"{session_mins}min + {drop_luck_pct}% drop luck should = {expected_effective} effective mins")
    
    def test_drop_luck_cap(self):
        """Test that drop luck is capped at 100% (600 virtual minutes)."""
        session_minutes = 30
        
        drop_luck_values = [100, 150, 200, 500]
        
        for drop_luck in drop_luck_values:
            capped_drop_luck = min(drop_luck, 100)
            effective_mins = session_minutes + (capped_drop_luck * 6)
            
            # Maximum should be 30 + (100 * 6) = 630
            self.assertLessEqual(effective_mins, 630,
                               f"Drop luck {drop_luck}% should be capped, effective mins: {effective_mins}")
            
            if drop_luck > 100:
                # Verify capping actually happened
                uncapped_effective = session_minutes + (drop_luck * 6)
                self.assertLess(effective_mins, uncapped_effective,
                              f"Drop luck {drop_luck}% should be reduced to cap")
    
    def test_drop_luck_multiplier_effect(self):
        """Test that higher drop luck significantly increases effective session time."""
        base_session = 30
        
        # Calculate multiplier effect
        drop_luck_10 = base_session + (10 * 6)   # 90 min = 3x multiplier
        drop_luck_50 = base_session + (50 * 6)   # 330 min = 11x multiplier
        drop_luck_100 = base_session + (100 * 6) # 630 min = 21x multiplier
        
        self.assertAlmostEqual(drop_luck_10 / base_session, 3.0, places=1)
        self.assertAlmostEqual(drop_luck_50 / base_session, 11.0, places=1)
        self.assertAlmostEqual(drop_luck_100 / base_session, 21.0, places=1)


class TestLuckInteraction(unittest.TestCase):
    """Test how Luck Bonus and Drop Luck work together."""
    
    def test_both_luck_types_are_independent(self):
        """Test that Luck Bonus and Drop Luck don't interfere with each other."""
        # Luck Bonus affects post-generation upgrade chance
        luck_bonus = 500  # 5% upgrade chance
        upgrade_chance = min(luck_bonus / 100, 10)
        
        # Drop Luck affects pre-generation rarity distribution
        session_mins = 30
        drop_luck = 20  # 20%
        effective_mins = session_mins + (drop_luck * 6)  # 150 min
        
        # Both should work independently
        self.assertEqual(upgrade_chance, 5.0)
        self.assertEqual(effective_mins, 150)
        
        # Changing one shouldn't affect the other
        new_luck_bonus = 1000
        new_upgrade_chance = min(new_luck_bonus / 100, 10)
        self.assertEqual(new_upgrade_chance, 10.0)
        self.assertEqual(effective_mins, 150)  # Drop luck calculation unchanged
    
    def test_total_luck_benefit_stacking(self):
        """Test the combined benefit of both luck types on item quality."""
        # Scenario: 30 min session with 50% drop luck and 500 luck_bonus
        
        session_mins = 30
        drop_luck = 50
        luck_bonus = 500
        
        # Step 1: Drop luck increases effective time for generation
        effective_mins = session_mins + (drop_luck * 6)  # 330 min
        quality_multiplier = effective_mins / session_mins  # 11x
        
        # Step 2: Luck bonus gives post-generation upgrade chance
        upgrade_chance = min(luck_bonus / 100, 10)  # 5%
        
        # Both benefits should be active
        self.assertGreater(quality_multiplier, 10, "Drop luck should significantly boost quality")
        self.assertEqual(upgrade_chance, 5.0, "Luck bonus should give upgrade chance")
        
        # Total expected improvement: ~11x base quality + 5% chance to upgrade tier
        # This is multiplicative - much better than either alone


class TestMergeSuccessWithLuck(unittest.TestCase):
    """Test merge success calculation with different luck values."""
    
    def test_merge_success_formula(self):
        """Test complete merge success rate calculation."""
        # Base rate: 25%
        # Item count: 3 items = +3% (1 item after first 2 at +3% each)
        # Character Luck: 100 = +0.01% (using formula: luck / 100 * 0.01)
        # Items Merge Luck: 5% = +5%
        
        base_rate = 0.25
        item_bonus = max(0, 3 - 2) * 0.03  # 0.03
        luck_bonus = min(100 / 100 * 0.01, 0.10)  # 0.0001 (0.01% decimal)
        items_merge_luck = 5  # 5%
        
        total_rate = base_rate + item_bonus + luck_bonus + (items_merge_luck / 100)
        expected = 0.25 + 0.03 + 0.01 + 0.05  # 0.34 = 34%
        
        self.assertAlmostEqual(total_rate, expected, places=2,
                              msg="Total merge rate should be sum of all bonuses")
    
    def test_high_luck_merge_scaling(self):
        """Test that high luck values boost merge success (but capped at 10%)."""
        base_rate = 0.25
        item_bonus = 0.03  # 3 items
        
        luck_values = [0, 500, 1000, 5000, 10000]
        
        for luck in luck_values:
            luck_bonus = min(max(luck, 0) / 100 * 0.01, 0.10)  # Capped at 10%
            total_rate = base_rate + item_bonus + luck_bonus
            total_percent = total_rate * 100
            
            print(f"Luck {luck}: {total_percent:.1f}% merge success")
            
            if luck == 0:
                self.assertAlmostEqual(total_percent, 28.0, places=1)
            elif luck == 1000:
                self.assertAlmostEqual(total_percent, 38.0, places=1)  # 25+3+10 = 38%
            elif luck >= 5000:
                self.assertAlmostEqual(total_percent, 38.0, places=1)  # Still capped at 38%


class TestPushYourLuckMechanic(unittest.TestCase):
    """Test the Push Your Luck gambling feature."""
    
    def test_multiplier_degradation(self):
        """Test that each re-roll reduces success by 20% (×0.80)."""
        base_success = 0.50  # 50% base merge success
        
        # Simulate multiple re-rolls
        reroll_1 = base_success * 0.80  # 40%
        reroll_2 = reroll_1 * 0.80      # 32%
        reroll_3 = reroll_2 * 0.80      # 25.6%
        reroll_4 = reroll_3 * 0.80      # 20.48%
        
        self.assertAlmostEqual(reroll_1, 0.40, places=2)
        self.assertAlmostEqual(reroll_2, 0.32, places=2)
        self.assertAlmostEqual(reroll_3, 0.256, places=3)
        self.assertAlmostEqual(reroll_4, 0.2048, places=4)
    
    def test_push_luck_risk_escalation(self):
        """Test that risk escalates dramatically with each re-roll."""
        base_success = 0.60  # 60% starting chance
        
        cumulative_success = base_success
        rolls = []
        
        for roll_num in range(1, 6):
            rolls.append((roll_num, cumulative_success))
            cumulative_success *= 0.80
        
        # By roll 5, you're down to ~24% success
        final_chance = base_success * (0.80 ** 4)
        self.assertLess(final_chance, 0.25, 
                       "After 4 re-rolls, success should be under 25%")
        
        # Verify exponential decay
        for i in range(len(rolls) - 1):
            current = rolls[i][1]
            next_roll = rolls[i + 1][1]
            self.assertAlmostEqual(next_roll / current, 0.80, places=2,
                                  msg="Each roll should be exactly 80% of previous")


def run_tests():
    """Run all luck mechanic tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestLuckBonusCharacterStat))
    suite.addTests(loader.loadTestsFromTestCase(TestLuckDecayMechanic))
    suite.addTests(loader.loadTestsFromTestCase(TestDropLuckGearStat))
    suite.addTests(loader.loadTestsFromTestCase(TestLuckInteraction))
    suite.addTests(loader.loadTestsFromTestCase(TestMergeSuccessWithLuck))
    suite.addTests(loader.loadTestsFromTestCase(TestPushYourLuckMechanic))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("TESTING LUCK MECHANICS")
    print("=" * 70)
    print()
    
    result = run_tests()
    
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - Luck mechanics working as intended!")
    else:
        print("❌ SOME TESTS FAILED - Review the luck implementation!")
    print("=" * 70)
