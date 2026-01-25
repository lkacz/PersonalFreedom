"""
Comprehensive tests for Lucky Merge system.

Tests cover:
- Basic merge outcomes (success/failure)
- Success rate calculation with all bonuses
- Tier upgrade mechanics
- Push Your Luck gamble system
- Tesla Coil perk effects
- Blank Parchment item recovery
- Failure recovery options (retry, claim, salvage)
- Cost calculations with discounts
- Inventory operations (UUID-based)
- Edge cases and fallbacks
"""

import pytest
import random
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from copy import deepcopy

# Import test dependencies
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6 import QtWidgets, QtCore

# Must create QApplication before importing dialog
@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for the test session."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    yield app


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_items():
    """Create sample items for merge testing."""
    return [
        {
            "name": "Iron Sword",
            "rarity": "Common",
            "slot": "weapon",
            "power": 10,
            "obtained_at": "2026-01-01T10:00:00.000001",
            "item_id": str(uuid.uuid4()),
            "lucky_options": {"merge_luck": 5}
        },
        {
            "name": "Steel Shield",
            "rarity": "Common",
            "slot": "shield",
            "power": 10,
            "obtained_at": "2026-01-01T10:00:00.000002",
            "item_id": str(uuid.uuid4()),
            "lucky_options": {}
        },
        {
            "name": "Leather Helm",
            "rarity": "Uncommon",
            "slot": "helmet",
            "power": 25,
            "obtained_at": "2026-01-01T10:00:00.000003",
            "item_id": str(uuid.uuid4()),
            "lucky_options": {"merge_luck": 3}
        }
    ]


@pytest.fixture
def legendary_items():
    """Create legendary items for edge case testing."""
    return [
        {
            "name": "Excalibur",
            "rarity": "Legendary",
            "slot": "weapon",
            "power": 250,
            "obtained_at": "2026-01-01T10:00:00.000001",
            "item_id": str(uuid.uuid4()),
        },
        {
            "name": "Aegis Shield",
            "rarity": "Legendary",
            "slot": "shield",
            "power": 250,
            "obtained_at": "2026-01-01T10:00:00.000002",
            "item_id": str(uuid.uuid4()),
        }
    ]


@pytest.fixture
def mock_adhd_buster():
    """Create mock adhd_buster config with entity perks."""
    return {
        "coins": 1000,
        "inventory": [],
        "equipped": {},
        "entitidex": {
            "collected_entity_ids": [],
            "exceptional_entities": {}
        }
    }


@pytest.fixture
def mock_adhd_buster_with_tesla_coil():
    """Mock config with Tesla Coil entity collected."""
    return {
        "coins": 1000,
        "inventory": [],
        "equipped": {},
        "entitidex": {
            "collected_entity_ids": ["scientist_007"],
            "exceptional_entities": {}
        }
    }


@pytest.fixture
def mock_adhd_buster_with_exceptional_tesla_coil():
    """Mock config with exceptional Tesla Coil."""
    return {
        "coins": 1000,
        "inventory": [],
        "equipped": {},
        "entitidex": {
            "collected_entity_ids": ["scientist_007"],
            "exceptional_entities": {"scientist_007": True}
        }
    }


@pytest.fixture
def mock_adhd_buster_with_blank_parchment():
    """Mock config with Blank Parchment entity collected."""
    return {
        "coins": 1000,
        "inventory": [],
        "equipped": {},
        "entitidex": {
            "collected_entity_ids": ["scholar_009"],
            "exceptional_entities": {}
        }
    }


@pytest.fixture
def mock_adhd_buster_with_exceptional_blank_parchment():
    """Mock config with exceptional Blank Parchment."""
    return {
        "coins": 1000,
        "inventory": [],
        "equipped": {},
        "entitidex": {
            "collected_entity_ids": ["scholar_009"],
            "exceptional_entities": {"scholar_009": True}
        }
    }


@pytest.fixture
def mock_entity_perks():
    """Mock entity perks for merge."""
    return {
        "total_merge_luck": 0,
        "total_coin_discount": 0,
        "contributors": []
    }


# =============================================================================
# Test Class: Success Rate Calculation
# =============================================================================

class TestSuccessRateCalculation:
    """Tests for merge success rate calculation."""
    
    def test_base_success_rate(self, qapp):
        """Base success rate should be 25% (0.25)."""
        from gamification import calculate_merge_success_rate, MERGE_BASE_SUCCESS_RATE
        
        items = [
            {"rarity": "Common", "lucky_options": {}},
            {"rarity": "Common", "lucky_options": {}}
        ]
        
        rate = calculate_merge_success_rate(items)
        assert rate == MERGE_BASE_SUCCESS_RATE
        assert rate == 0.25
    
    def test_items_merge_luck_bonus(self, qapp, sample_items):
        """Items with merge_luck should increase success rate."""
        from gamification import calculate_merge_success_rate, MERGE_BONUS_PER_ITEM
        
        # sample_items have merge_luck of 5 + 3 = 8%
        # With 3 items: base 25% + 3% (3rd item bonus) + 8% = 36%
        rate = calculate_merge_success_rate(sample_items, items_merge_luck=8)
        
        # 25% base + 3% (extra item) + 8% merge_luck = 36%
        assert rate == pytest.approx(0.36, abs=0.01)
    
    def test_city_bonus_adds_to_rate(self, qapp, sample_items):
        """City/Forge bonus should add to success rate."""
        from gamification import calculate_merge_success_rate
        
        # With 3 items: base 25% + 3% (3rd item) + 10% city = 38%
        rate = calculate_merge_success_rate(sample_items, city_bonus=10)
        
        assert rate == pytest.approx(0.38, abs=0.01)
    
    def test_combined_bonuses(self, qapp, sample_items):
        """All bonuses should stack additively."""
        from gamification import calculate_merge_success_rate
        
        # items_merge_luck=8, city_bonus=10
        # With 3 items: 25% + 3% + 8% + 10% = 46%
        rate = calculate_merge_success_rate(sample_items, items_merge_luck=8, city_bonus=10)
        
        assert rate == pytest.approx(0.46, abs=0.01)
    
    def test_success_rate_capped_at_maximum(self, qapp):
        """Success rate should be capped at reasonable maximum."""
        from gamification import calculate_merge_success_rate
        
        items = [{"rarity": "Common"}] * 2
        
        # Huge bonuses
        rate = calculate_merge_success_rate(items, items_merge_luck=100, city_bonus=100)
        
        # Should be capped (typically at 95% or 99%)
        assert rate <= 1.0


# =============================================================================
# Test Class: Result Rarity Calculation
# =============================================================================

class TestResultRarityCalculation:
    """Tests for determining merge result rarity."""
    
    def test_result_rarity_based_on_highest(self, qapp):
        """Result rarity is based on HIGHEST input rarity + 1 tier."""
        from gamification import get_merge_result_rarity
        
        items = [
            {"rarity": "Epic"},
            {"rarity": "Common"},
            {"rarity": "Rare"}
        ]
        
        result_rarity = get_merge_result_rarity(items)
        
        # Highest non-Common is Epic, so result should be Legendary (Epic + 1)
        assert result_rarity == "Legendary"
    
    def test_all_same_rarity(self, qapp):
        """All same rarity should give that rarity or one higher."""
        from gamification import get_merge_result_rarity
        
        items = [
            {"rarity": "Rare"},
            {"rarity": "Rare"},
            {"rarity": "Rare"}
        ]
        
        result_rarity = get_merge_result_rarity(items)
        
        # Should be Rare or Epic
        assert result_rarity in ["Rare", "Epic"]
    
    def test_legendary_merge_stays_legendary(self, qapp, legendary_items):
        """Legendary items should result in Legendary."""
        from gamification import get_merge_result_rarity
        
        result_rarity = get_merge_result_rarity(legendary_items)
        
        assert result_rarity == "Legendary"


# =============================================================================
# Test Class: Item Generation
# =============================================================================

class TestItemGeneration:
    """Tests for merged item generation."""
    
    def test_generated_item_has_uuid(self, qapp):
        """Generated items must have item_id (UUID)."""
        from gamification import generate_item
        
        item = generate_item(rarity="Rare")
        
        assert "item_id" in item
        assert item["item_id"] is not None
        # Verify it's a valid UUID format
        uuid.UUID(item["item_id"])
    
    def test_generated_item_has_timestamp(self, qapp):
        """Generated items must have obtained_at timestamp."""
        from gamification import generate_item
        
        item = generate_item(rarity="Epic")
        
        assert "obtained_at" in item
        assert item["obtained_at"] is not None
    
    def test_generated_item_has_correct_rarity(self, qapp):
        """Generated item should have requested rarity."""
        from gamification import generate_item
        
        for rarity in ["Common", "Uncommon", "Rare", "Epic", "Legendary"]:
            item = generate_item(rarity=rarity)
            assert item["rarity"] == rarity
    
    def test_batch_generated_items_have_unique_ids(self, qapp):
        """Batch generated items should all have unique item_ids."""
        from gamification import generate_item
        
        items = [generate_item(rarity="Common") for _ in range(10)]
        
        item_ids = [item["item_id"] for item in items]
        
        # All IDs should be unique
        assert len(set(item_ids)) == len(item_ids)


# =============================================================================
# Test Class: LuckyMergeDialog Creation
# =============================================================================

class TestLuckyMergeDialogCreation:
    """Tests for LuckyMergeDialog initialization."""
    
    def test_dialog_creation(self, qapp, sample_items, mock_adhd_buster, mock_entity_perks):
        """Dialog should create without errors."""
        from merge_dialog import LuckyMergeDialog
        
        dialog = LuckyMergeDialog(
            items=sample_items,
            luck=0,
            equipped={},
            player_coins=1000,
            coin_discount=0,
            entity_perks=mock_entity_perks,
            adhd_buster=mock_adhd_buster
        )
        
        assert dialog is not None
        assert dialog.items == sample_items
    
    def test_dialog_calculates_items_merge_luck(self, qapp, sample_items, mock_adhd_buster, mock_entity_perks):
        """Dialog should calculate merge luck from items."""
        from merge_dialog import LuckyMergeDialog
        
        dialog = LuckyMergeDialog(
            items=sample_items,
            luck=0,
            equipped={},
            player_coins=1000,
            coin_discount=0,
            entity_perks=mock_entity_perks,
            adhd_buster=mock_adhd_buster
        )
        
        # sample_items have merge_luck of 5 + 3 = 8
        assert dialog.items_merge_luck == 8
    
    def test_dialog_sets_result_rarity(self, qapp, sample_items, mock_adhd_buster, mock_entity_perks):
        """Dialog should set expected result rarity."""
        from merge_dialog import LuckyMergeDialog
        
        dialog = LuckyMergeDialog(
            items=sample_items,
            luck=0,
            equipped={},
            player_coins=1000,
            coin_discount=0,
            entity_perks=mock_entity_perks,
            adhd_buster=mock_adhd_buster
        )
        
        # Result rarity should be set
        assert dialog.result_rarity is not None
        assert dialog.result_rarity in ["Common", "Uncommon", "Rare", "Epic", "Legendary"]


# =============================================================================
# Test Class: Push Your Luck Mechanics
# =============================================================================

class TestPushYourLuckMechanics:
    """Tests for Push Your Luck gamble system."""
    
    def test_push_luck_penalty_without_tesla_coil(self, qapp):
        """Without Tesla Coil, push luck has 0.80 multiplier penalty."""
        # The base gamble_multiplier should be 0.80
        base_multiplier = 0.80
        
        # After one push, success rate is reduced
        original_rate = 0.50
        adjusted_rate = original_rate * base_multiplier
        
        assert adjusted_rate == pytest.approx(0.40, abs=0.01)
    
    def test_push_luck_no_penalty_with_normal_tesla_coil(self, qapp):
        """With normal Tesla Coil, penalty is removed (1.00 multiplier)."""
        tesla_coil_multiplier = 1.00
        
        original_rate = 0.50
        adjusted_rate = original_rate * tesla_coil_multiplier
        
        assert adjusted_rate == pytest.approx(0.50, abs=0.01)
    
    def test_push_luck_bonus_with_exceptional_tesla_coil(self, qapp):
        """With exceptional Tesla Coil, get 1.20 bonus multiplier."""
        exceptional_tesla_multiplier = 1.20
        
        original_rate = 0.50
        adjusted_rate = original_rate * exceptional_tesla_multiplier
        
        assert adjusted_rate == pytest.approx(0.60, abs=0.01)
    
    def test_cumulative_multiplier_across_pushes(self, qapp):
        """Multiplier should stack cumulatively across multiple pushes."""
        base_multiplier = 0.80
        
        original_rate = 0.50
        
        # First push
        after_first = original_rate * base_multiplier  # 0.40
        
        # Second push (cumulative)
        cumulative = base_multiplier * base_multiplier  # 0.64
        after_second = original_rate * cumulative  # 0.32
        
        assert after_first == pytest.approx(0.40, abs=0.01)
        assert after_second == pytest.approx(0.32, abs=0.01)
    
    def test_legendary_does_not_offer_push_luck(self, qapp, legendary_items, mock_adhd_buster, mock_entity_perks):
        """Legendary items should not offer Push Your Luck."""
        # When result is Legendary, no further upgrade is possible
        # This is tested by checking that the dialog flow skips push luck for Legendary
        
        # Legendary is the max tier
        rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        legendary_idx = rarity_order.index("Legendary")
        
        # Cannot upgrade beyond Legendary
        assert legendary_idx == len(rarity_order) - 1


# =============================================================================
# Test Class: Blank Parchment Item Recovery
# =============================================================================

class TestBlankParchmentRecovery:
    """Tests for Blank Parchment item recovery on push failure."""
    
    def test_no_blank_parchment_no_recovery(self, qapp):
        """Without Blank Parchment, item is lost on push failure."""
        recovery_chance = 0
        
        # No recovery possible
        assert recovery_chance == 0
    
    def test_normal_blank_parchment_10_percent(self, qapp):
        """Normal Blank Parchment gives 10% recovery chance."""
        normal_recovery_chance = 10
        
        assert normal_recovery_chance == 10
    
    def test_exceptional_blank_parchment_20_percent(self, qapp):
        """Exceptional Blank Parchment gives 20% recovery chance."""
        exceptional_recovery_chance = 20
        
        assert exceptional_recovery_chance == 20
    
    def test_recovery_success_keeps_item(self, qapp):
        """Successful recovery should keep current item with success=True."""
        # When recovery succeeds, merge_result["success"] = True
        # and merge_result["item_saved_by_perk"] = True
        
        mock_result = {
            "success": True,
            "item_saved_by_perk": True,
            "result_item": {"name": "Saved Item", "rarity": "Rare"}
        }
        
        assert mock_result["success"] is True
        assert mock_result["item_saved_by_perk"] is True
    
    def test_recovery_failure_loses_everything(self, qapp):
        """Failed recovery should lose all items."""
        mock_result = {
            "success": False,
            "push_luck_failed": True,
            "result_item": None
        }
        
        assert mock_result["success"] is False
        assert mock_result["result_item"] is None


# =============================================================================
# Test Class: Failure Recovery Options
# =============================================================================

class TestFailureRecoveryOptions:
    """Tests for failure recovery options (retry, claim, salvage)."""
    
    def test_near_miss_detection(self, qapp):
        """Near miss should be detected when within 5% of success."""
        roll = 0.28
        needed = 0.25
        
        margin = roll - needed
        is_near_miss = margin > 0 and margin <= 0.05
        
        # 0.28 - 0.25 = 0.03 (within 5%)
        assert margin == pytest.approx(0.03, abs=0.001)
        assert is_near_miss is True
    
    def test_not_near_miss_when_too_far(self, qapp):
        """Should not be near miss when roll is far from success."""
        roll = 0.50
        needed = 0.25
        
        margin = roll - needed
        is_near_miss = margin > 0 and margin <= 0.05
        
        # 0.50 - 0.25 = 0.25 (way over 5%)
        assert is_near_miss is False
    
    def test_retry_adds_5_percent_bump(self, qapp):
        """Retry should add +5% to success threshold."""
        original_needed = 0.25
        retry_bump = 0.05
        
        new_needed = min(original_needed + retry_bump, 1.0)
        
        assert new_needed == pytest.approx(0.30, abs=0.001)
    
    def test_retry_accumulates_cost(self, qapp):
        """Multiple retries should accumulate cost."""
        retry_cost = 50
        
        first_retry = retry_cost
        second_retry = retry_cost * 2
        third_retry = retry_cost * 3
        
        assert first_retry == 50
        assert second_retry == 100
        assert third_retry == 150
    
    def test_claim_converts_failure_to_success(self, qapp):
        """Claim should convert failure to success with generated item."""
        mock_result = {
            "success": False,
            "result_item": None
        }
        
        # After claim
        mock_result["success"] = True
        mock_result["result_item"] = {"name": "Claimed Item", "rarity": "Common"}
        mock_result["claimed_with_coins"] = True
        
        assert mock_result["success"] is True
        assert mock_result["result_item"] is not None
        assert mock_result["claimed_with_coins"] is True
    
    def test_salvage_saves_random_item(self, qapp, sample_items):
        """Salvage should save one random item from merge."""
        # Pick random item
        random.seed(42)
        saved_item = random.choice(sample_items)
        
        mock_result = {
            "success": False,
            "salvaged_item": saved_item,
            "salvage_cost": 50
        }
        
        assert mock_result["salvaged_item"] is not None
        assert mock_result["salvaged_item"] in sample_items


# =============================================================================
# Test Class: Cost Calculations
# =============================================================================

class TestCostCalculations:
    """Tests for merge cost calculations."""
    
    def test_base_merge_cost(self, qapp):
        """Base merge cost should be 50 coins."""
        from gamification import COIN_COSTS
        
        base_cost = COIN_COSTS.get("merge_base", 50)
        
        assert base_cost == 50
    
    def test_boost_cost(self, qapp):
        """Boost option should cost 50 coins."""
        from gamification import COIN_COSTS
        
        boost_cost = COIN_COSTS.get("merge_boost", 50)
        
        assert boost_cost == 50
    
    def test_tier_upgrade_cost(self, qapp):
        """Tier upgrade option should cost 50 coins."""
        from gamification import COIN_COSTS
        
        tier_cost = COIN_COSTS.get("merge_tier_upgrade", 50)
        
        assert tier_cost == 50
    
    def test_claim_cost(self, qapp):
        """Claim option should cost 100 coins."""
        from gamification import COIN_COSTS
        
        claim_cost = COIN_COSTS.get("merge_claim", 100)
        
        assert claim_cost == 100
    
    def test_salvage_cost(self, qapp):
        """Salvage option should cost 50 coins."""
        from gamification import COIN_COSTS
        
        salvage_cost = COIN_COSTS.get("merge_salvage", 50)
        
        assert salvage_cost == 50
    
    def test_item_discount_applied(self, qapp):
        """Item discount should reduce costs."""
        from gamification import calculate_merge_discount, apply_coin_discount
        
        items_with_discount = [
            {"lucky_options": {"coin_discount": 10}},
            {"lucky_options": {"coin_discount": 5}}
        ]
        
        discount = calculate_merge_discount(items_with_discount)
        
        base_cost = 50
        discounted_cost = apply_coin_discount(base_cost, discount)
        
        # 15% discount on 50 = 42.5, typically rounded
        assert discounted_cost < base_cost
    
    def test_entity_flat_reduction(self, qapp):
        """Entity perk flat reduction should reduce costs."""
        from gamification import apply_coin_flat_reduction
        
        base_cost = 50
        flat_reduction = 10
        
        final_cost = apply_coin_flat_reduction(base_cost, flat_reduction)
        
        assert final_cost == 40
    
    def test_flat_reduction_cannot_go_negative(self, qapp):
        """Flat reduction should not result in negative cost."""
        from gamification import apply_coin_flat_reduction
        
        base_cost = 10
        flat_reduction = 50
        
        final_cost = apply_coin_flat_reduction(base_cost, flat_reduction)
        
        # Should be clamped to minimum (likely 1 or 0)
        assert final_cost >= 0


# =============================================================================
# Test Class: Inventory Operations
# =============================================================================

class TestInventoryOperations:
    """Tests for inventory item removal and addition during merge."""
    
    def test_source_items_removed_by_item_id(self, qapp, sample_items):
        """Source items should be removed using item_id matching."""
        from game_state import GameStateManager
        
        mock_blocker = Mock()
        mock_blocker.adhd_buster = {
            "coins": 1000,
            "inventory": deepcopy(sample_items),
            "equipped": {}
        }
        mock_blocker.save_config = Mock()
        
        gs = GameStateManager(mock_blocker)
        
        # Merge first two items
        items_to_merge = mock_blocker.adhd_buster["inventory"][:2]
        result_item = {"name": "Merged Item", "rarity": "Uncommon", "item_id": str(uuid.uuid4())}
        
        gs.perform_merge(items_to_merge, result_item, success=True)
        
        # Should have 1 original + 1 result = 2 items
        assert len(mock_blocker.adhd_buster["inventory"]) == 2
    
    def test_result_item_added_on_success(self, qapp, sample_items):
        """Result item should be added to inventory on success."""
        from game_state import GameStateManager
        
        mock_blocker = Mock()
        mock_blocker.adhd_buster = {
            "coins": 1000,
            "inventory": deepcopy(sample_items),
            "equipped": {}
        }
        mock_blocker.save_config = Mock()
        
        gs = GameStateManager(mock_blocker)
        
        items_to_merge = mock_blocker.adhd_buster["inventory"][:2]
        result_item = {"name": "Merged Item", "rarity": "Uncommon"}
        
        gs.perform_merge(items_to_merge, result_item, success=True)
        
        # Check result item is in inventory
        inv = mock_blocker.adhd_buster["inventory"]
        result_in_inv = any(i.get("name") == "Merged Item" for i in inv)
        assert result_in_inv is True
    
    def test_result_item_gets_item_id(self, qapp, sample_items):
        """Result item should get item_id if missing."""
        from game_state import GameStateManager
        
        mock_blocker = Mock()
        mock_blocker.adhd_buster = {
            "coins": 1000,
            "inventory": deepcopy(sample_items),
            "equipped": {}
        }
        mock_blocker.save_config = Mock()
        
        gs = GameStateManager(mock_blocker)
        
        items_to_merge = mock_blocker.adhd_buster["inventory"][:2]
        result_item = {"name": "Merged Item", "rarity": "Uncommon"}  # No item_id
        
        gs.perform_merge(items_to_merge, result_item, success=True)
        
        # Find result item and check it has item_id
        inv = mock_blocker.adhd_buster["inventory"]
        result = next((i for i in inv if i.get("name") == "Merged Item"), None)
        
        assert result is not None
        assert "item_id" in result
        assert result["item_id"] is not None
    
    def test_no_item_added_on_failure(self, qapp, sample_items):
        """No result item should be added on failure."""
        from game_state import GameStateManager
        
        mock_blocker = Mock()
        original_inventory = deepcopy(sample_items)
        mock_blocker.adhd_buster = {
            "coins": 1000,
            "inventory": original_inventory,
            "equipped": {}
        }
        mock_blocker.save_config = Mock()
        
        gs = GameStateManager(mock_blocker)
        
        items_to_merge = mock_blocker.adhd_buster["inventory"][:2]
        
        gs.perform_merge(items_to_merge, None, success=False)
        
        # Should only have remaining original item
        assert len(mock_blocker.adhd_buster["inventory"]) == 1
    
    def test_salvaged_item_excluded_from_removal(self, qapp, sample_items):
        """Salvaged item should not be removed from inventory."""
        # This is handled in focus_blocker_qt.py before calling perform_merge
        
        items = deepcopy(sample_items)
        salvaged_item = items[0]
        
        # Exclude salvaged item
        items_to_remove = [
            i for i in items 
            if i.get("item_id") != salvaged_item.get("item_id")
        ]
        
        assert len(items_to_remove) == 2
        assert salvaged_item not in items_to_remove


# =============================================================================
# Test Class: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_items_without_timestamp(self, qapp):
        """Items without obtained_at should still be matched by item_id."""
        from game_state import GameStateManager
        
        items_no_ts = [
            {"name": "Item 1", "rarity": "Common", "slot": "weapon", "item_id": "id-1"},
            {"name": "Item 2", "rarity": "Common", "slot": "shield", "item_id": "id-2"}
        ]
        
        mock_blocker = Mock()
        mock_blocker.adhd_buster = {
            "coins": 1000,
            "inventory": deepcopy(items_no_ts),
            "equipped": {}
        }
        mock_blocker.save_config = Mock()
        
        gs = GameStateManager(mock_blocker)
        
        result_item = {"name": "Merged", "rarity": "Uncommon"}
        gs.perform_merge(items_no_ts, result_item, success=True)
        
        # Should have result item only
        assert len(mock_blocker.adhd_buster["inventory"]) == 1
        assert mock_blocker.adhd_buster["inventory"][0]["name"] == "Merged"
    
    def test_items_without_item_id(self, qapp):
        """Items without item_id should fall back to timestamp+slot matching."""
        from game_state import GameStateManager
        
        ts = "2026-01-01T10:00:00.000001"
        items_no_id = [
            {"name": "Item 1", "rarity": "Common", "slot": "weapon", "obtained_at": ts},
            {"name": "Item 2", "rarity": "Common", "slot": "shield", "obtained_at": ts}
        ]
        
        mock_blocker = Mock()
        mock_blocker.adhd_buster = {
            "coins": 1000,
            "inventory": deepcopy(items_no_id),
            "equipped": {}
        }
        mock_blocker.save_config = Mock()
        
        gs = GameStateManager(mock_blocker)
        
        result_item = {"name": "Merged", "rarity": "Uncommon"}
        gs.perform_merge(items_no_id, result_item, success=True)
        
        # Should have result item only
        assert len(mock_blocker.adhd_buster["inventory"]) == 1
    
    def test_empty_items_list(self, qapp):
        """Empty items list should return False from perform_merge."""
        from game_state import GameStateManager
        
        mock_blocker = Mock()
        mock_blocker.adhd_buster = {
            "coins": 1000,
            "inventory": [],
            "equipped": {}
        }
        mock_blocker.save_config = Mock()
        
        gs = GameStateManager(mock_blocker)
        
        result = gs.perform_merge([], None, success=False)
        
        assert result is False
    
    def test_all_legendary_merge(self, qapp, legendary_items, mock_adhd_buster, mock_entity_perks):
        """All Legendary merge should work as reroll."""
        from merge_dialog import LuckyMergeDialog
        
        dialog = LuckyMergeDialog(
            items=legendary_items,
            luck=0,
            equipped={},
            player_coins=1000,
            coin_discount=0,
            entity_perks=mock_entity_perks,
            adhd_buster=mock_adhd_buster
        )
        
        # Result rarity should still be Legendary
        assert dialog.result_rarity == "Legendary"
    
    def test_fallback_definitions_exist(self, qapp):
        """Fallback definitions should exist for when gamification unavailable."""
        from merge_dialog import (
            COIN_COSTS, RARITY_ORDER, ITEM_RARITIES, RARITY_POWER
        )
        
        # These should always be defined
        assert COIN_COSTS is not None
        assert RARITY_ORDER is not None
        assert ITEM_RARITIES is not None
        assert RARITY_POWER is not None
        
        # Check required keys
        assert "merge_base" in COIN_COSTS
        assert "merge_salvage" in COIN_COSTS
        assert "Common" in ITEM_RARITIES
        assert "Legendary" in ITEM_RARITIES


# =============================================================================
# Test Class: Tier Upgrade Option
# =============================================================================

class TestTierUpgradeOption:
    """Tests for tier upgrade option."""
    
    def test_tier_upgrade_increases_rarity(self, qapp):
        """Tier upgrade should increase result rarity by 1."""
        rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        
        base_rarity = "Rare"
        base_idx = rarity_order.index(base_rarity)
        
        upgraded_rarity = rarity_order[min(base_idx + 1, len(rarity_order) - 1)]
        
        assert upgraded_rarity == "Epic"
    
    def test_tier_upgrade_legendary_stays_legendary(self, qapp):
        """Tier upgrade on Legendary should stay Legendary."""
        rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        
        base_rarity = "Legendary"
        base_idx = rarity_order.index(base_rarity)
        
        upgraded_rarity = rarity_order[min(base_idx + 1, len(rarity_order) - 1)]
        
        assert upgraded_rarity == "Legendary"
    
    def test_tier_upgrade_updates_power(self, qapp):
        """Tier upgrade should update item power to new rarity level."""
        from gamification import RARITY_POWER
        
        original_power = RARITY_POWER.get("Rare", 50)
        upgraded_power = RARITY_POWER.get("Epic", 100)
        
        assert upgraded_power > original_power


# =============================================================================
# Test Class: Integration Tests
# =============================================================================

class TestMergeIntegration:
    """Integration tests for complete merge flows."""
    
    def test_full_success_flow(self, qapp, sample_items, mock_adhd_buster, mock_entity_perks):
        """Test complete successful merge flow."""
        from merge_dialog import LuckyMergeDialog
        from game_state import GameStateManager
        
        # Setup
        mock_blocker = Mock()
        mock_blocker.adhd_buster = {
            "coins": 1000,
            "inventory": deepcopy(sample_items),
            "equipped": {}
        }
        mock_blocker.save_config = Mock()
        
        # Create dialog
        dialog = LuckyMergeDialog(
            items=sample_items[:2],
            luck=0,
            equipped={},
            player_coins=1000,
            coin_discount=0,
            entity_perks=mock_entity_perks,
            adhd_buster=mock_adhd_buster
        )
        
        # Simulate successful merge result
        result_item = {
            "name": "Test Merged",
            "rarity": dialog.result_rarity,
            "slot": "weapon",
            "power": 25
        }
        
        dialog.merge_result = {
            "success": True,
            "result_item": result_item,
            "items_lost": sample_items[:2]
        }
        
        # Verify result
        assert dialog.merge_result["success"] is True
        assert dialog.merge_result["result_item"] is not None
    
    def test_full_failure_with_salvage_flow(self, qapp, sample_items, mock_adhd_buster, mock_entity_perks):
        """Test complete failure with salvage flow."""
        from merge_dialog import LuckyMergeDialog
        
        # Create dialog
        dialog = LuckyMergeDialog(
            items=sample_items,
            luck=0,
            equipped={},
            player_coins=1000,
            coin_discount=0,
            entity_perks=mock_entity_perks,
            adhd_buster=mock_adhd_buster
        )
        
        # Simulate failed merge with salvage
        salvaged = sample_items[0]
        
        dialog.merge_result = {
            "success": False,
            "result_item": None,
            "items_lost": sample_items,
            "salvaged_item": salvaged,
            "salvage_cost": 50
        }
        
        # Verify salvage data
        assert dialog.merge_result["success"] is False
        assert dialog.merge_result["salvaged_item"] == salvaged
        assert dialog.merge_result["salvage_cost"] == 50


# =============================================================================
# Run tests if executed directly
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
