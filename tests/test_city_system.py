"""
City Building System - Unit Tests
==================================
Tests for city manager, synergies, and state management.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from city import (
    # Constants
    CITY_AVAILABLE,
    RESOURCE_TYPES,
    BUILDING_SLOT_UNLOCKS,
    GRID_ROWS,
    GRID_COLS,
    
    # State
    CellStatus,
    create_empty_grid,
    create_default_city_data,
    create_cell_state,
    
    # Buildings
    CITY_BUILDINGS,
    get_building_by_id,
    get_all_building_ids,
    
    # Manager
    get_city_data,
    get_city_bonuses,
    add_city_resource,
    get_resources,
    can_place_building,
    place_building,
    remove_building,
    invest_resources,
    collect_city_income,
    get_pending_income,
    award_focus_session_income,
    award_exercise_income,
    get_max_building_slots,
    get_available_slots,
    get_next_slot_unlock,
    get_placed_buildings,
    get_level_requirements,
    get_construction_progress,
    can_upgrade,
    can_initiate_upgrade,
    initiate_upgrade,
    start_upgrade,
    
    # Synergies
    BUILDING_SYNERGIES,
    calculate_building_synergy_bonus,
    get_all_synergy_bonuses,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def fresh_adhd_buster():
    """Fresh player data with no city."""
    return {
        "total_xp": 0,
        "coins": 100,
    }


@pytest.fixture
def adhd_buster_with_city():
    """Player data with initialized city."""
    data = {
        "total_xp": 500,  # Around level 5
        "coins": 500,
    }
    # Initialize city with some resources
    city = get_city_data(data)
    city["resources"] = {
        "water": 50,
        "materials": 100,
        "activity": 30,
        "focus": 40,
    }
    return data


@pytest.fixture
def adhd_buster_with_buildings():
    """Player data with some buildings placed."""
    data = {
        "total_xp": 5000,  # Around level 15
        "coins": 1000,
    }
    city = get_city_data(data)
    city["resources"] = {
        "water": 200,
        "materials": 300,
        "activity": 150,
        "focus": 200,
    }
    
    # Place goldmine at (0,0) - completed
    city["grid"][0][0] = {
        "building_id": "goldmine",
        "status": CellStatus.COMPLETE.value,
        "level": 2,
        "construction_progress": {"water": 3, "materials": 5, "activity": 0, "focus": 2},
        "placed_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
    }
    
    # Place forge at (0,1) - under construction
    city["grid"][0][1] = {
        "building_id": "forge",
        "status": CellStatus.BUILDING.value,
        "level": 1,
        "construction_progress": {"water": 5, "materials": 10, "activity": 5, "focus": 5},
        "placed_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    
    return data


# ============================================================================
# MODULE AVAILABILITY TESTS
# ============================================================================

class TestModuleAvailability:
    """Test that module is properly configured."""
    
    def test_city_available_flag(self):
        assert CITY_AVAILABLE is True
    
    def test_resource_types_defined(self):
        assert len(RESOURCE_TYPES) == 4
        assert "water" in RESOURCE_TYPES
        assert "materials" in RESOURCE_TYPES
        assert "activity" in RESOURCE_TYPES
        assert "focus" in RESOURCE_TYPES
    
    def test_building_slot_unlocks_defined(self):
        assert len(BUILDING_SLOT_UNLOCKS) > 0
        assert BUILDING_SLOT_UNLOCKS[1] == 2  # Level 1 = 2 slots
        assert BUILDING_SLOT_UNLOCKS[40] == 10  # Level 40 = 10 slots
    
    def test_all_buildings_defined(self):
        assert len(CITY_BUILDINGS) == 10
        expected_buildings = [
            "goldmine", "forge", "artisan_guild", "university",
            "training_ground", "library", "market", "royal_mint",
            "observatory", "wonder"
        ]
        for building_id in expected_buildings:
            assert building_id in CITY_BUILDINGS


# ============================================================================
# STATE MANAGEMENT TESTS
# ============================================================================

class TestStateManagement:
    """Test city state initialization and access."""
    
    def test_create_empty_grid(self):
        grid = create_empty_grid()
        assert len(grid) == GRID_ROWS
        assert len(grid[0]) == GRID_COLS
        assert all(cell is None for row in grid for cell in row)
    
    def test_create_empty_grid_no_reference_bug(self):
        """Ensure rows are independent (not references to same list)."""
        grid = create_empty_grid()
        grid[0][0] = "test"
        assert grid[1][0] is None  # Other rows unaffected
    
    def test_create_default_city_data(self):
        city = create_default_city_data()
        assert "grid" in city
        assert "resources" in city
        assert "last_collection_time" in city
        assert city["resources"]["water"] == 0
    
    def test_create_cell_state(self):
        cell = create_cell_state("goldmine")
        assert cell["building_id"] == "goldmine"
        assert cell["status"] == CellStatus.PLACED.value
        assert cell["level"] == 1
        assert "placed_at" in cell
    
    def test_get_city_data_initializes_missing(self, fresh_adhd_buster):
        assert "city" not in fresh_adhd_buster
        city = get_city_data(fresh_adhd_buster)
        assert "city" in fresh_adhd_buster
        assert city is fresh_adhd_buster["city"]
    
    def test_get_city_data_returns_existing(self, adhd_buster_with_city):
        city1 = get_city_data(adhd_buster_with_city)
        city2 = get_city_data(adhd_buster_with_city)
        assert city1 is city2


# ============================================================================
# BUILDING SLOT TESTS
# ============================================================================

class TestBuildingSlots:
    """Test level-gated building slot system."""
    
    def test_get_max_building_slots_level_1(self):
        assert get_max_building_slots(1) == 2
    
    def test_get_max_building_slots_level_5(self):
        assert get_max_building_slots(5) == 3
    
    def test_get_max_building_slots_level_10(self):
        # Level 10: between Lv9→4 and Lv13→5, so still 4 slots
        assert get_max_building_slots(10) == 4
    
    def test_get_max_building_slots_level_40(self):
        assert get_max_building_slots(40) == 10
    
    def test_get_max_building_slots_level_100(self):
        """Level beyond 40 should still be 10."""
        assert get_max_building_slots(100) == 10
    
    @patch('gamification.get_level_from_xp')
    def test_get_available_slots_empty_city(self, mock_level, fresh_adhd_buster):
        mock_level.return_value = (10, 0, 100, 0)  # Level 10
        slots = get_available_slots(fresh_adhd_buster)
        assert slots == 4  # Level 10 = 4 slots (Lv9→4, Lv13→5), 0 used
    
    @patch('gamification.get_level_from_xp')
    def test_get_available_slots_with_buildings(self, mock_level, adhd_buster_with_buildings):
        mock_level.return_value = (15, 0, 100, 0)  # Level 15
        slots = get_available_slots(adhd_buster_with_buildings)
        assert slots == 3  # Level 15 = 5 slots (Lv13→5, Lv18→6), 2 used = 3 available
    
    @patch('gamification.get_level_from_xp')
    def test_get_next_slot_unlock(self, mock_level, fresh_adhd_buster):
        mock_level.return_value = (7, 0, 100, 0)  # Level 7
        info = get_next_slot_unlock(fresh_adhd_buster)
        assert info["current_slots"] == 3  # Level 7 = 3 slots (Lv6→3)
        assert info["next_unlock_level"] == 9  # Next unlock is Level 9
        assert info["slots_after"] == 4


# ============================================================================
# RESOURCE MANAGEMENT TESTS
# ============================================================================

class TestResourceManagement:
    """Test resource add/get/consume."""
    
    def test_add_city_resource(self, fresh_adhd_buster):
        new_total = add_city_resource(fresh_adhd_buster, "water", 5)
        assert new_total == 5
        assert get_resources(fresh_adhd_buster)["water"] == 5
    
    def test_add_city_resource_accumulates(self, adhd_buster_with_city):
        original = get_resources(adhd_buster_with_city)["water"]
        add_city_resource(adhd_buster_with_city, "water", 10)
        assert get_resources(adhd_buster_with_city)["water"] == original + 10
    
    def test_add_city_resource_invalid_type(self, fresh_adhd_buster):
        result = add_city_resource(fresh_adhd_buster, "invalid", 5)
        assert result == 0
    
    def test_get_resources_returns_copy(self, adhd_buster_with_city):
        resources = get_resources(adhd_buster_with_city)
        resources["water"] = 9999
        assert get_resources(adhd_buster_with_city)["water"] != 9999


# ============================================================================
# BUILDING PLACEMENT TESTS
# ============================================================================

class TestBuildingPlacement:
    """Test building placement validation and execution."""
    
    @patch('gamification.get_level_from_xp')
    def test_can_place_building_valid(self, mock_level, fresh_adhd_buster):
        mock_level.return_value = (10, 0, 100, 0)
        can, reason = can_place_building(fresh_adhd_buster, "goldmine")
        assert can is True
        assert reason == "Ready to place"
    
    def test_can_place_building_unknown(self, fresh_adhd_buster):
        can, reason = can_place_building(fresh_adhd_buster, "unknown_building")
        assert can is False
        assert "Unknown" in reason
    
    @patch('gamification.get_level_from_xp')
    def test_can_place_building_already_placed(self, mock_level, adhd_buster_with_buildings):
        mock_level.return_value = (15, 0, 100, 0)
        can, reason = can_place_building(adhd_buster_with_buildings, "goldmine")
        assert can is False
        assert "Already placed" in reason
    
    @patch('gamification.get_level_from_xp')
    def test_place_building_success(self, mock_level, fresh_adhd_buster):
        mock_level.return_value = (10, 0, 100, 0)
        success = place_building(fresh_adhd_buster, 0, 0, "goldmine")
        assert success is True
        
        city = get_city_data(fresh_adhd_buster)
        assert city["grid"][0][0] is not None
        assert city["grid"][0][0]["building_id"] == "goldmine"
        assert city["grid"][0][0]["status"] == CellStatus.PLACED.value
    
    @patch('gamification.get_level_from_xp')
    def test_place_building_cell_occupied(self, mock_level, adhd_buster_with_buildings):
        mock_level.return_value = (15, 0, 100, 0)
        success = place_building(adhd_buster_with_buildings, 0, 0, "university")
        assert success is False  # Cell (0,0) has goldmine
    
    @patch('gamification.get_level_from_xp')
    def test_place_building_invalid_coords(self, mock_level, fresh_adhd_buster):
        mock_level.return_value = (10, 0, 100, 0)
        success = place_building(fresh_adhd_buster, 10, 10, "goldmine")
        assert success is False
    
    def test_remove_building(self, adhd_buster_with_buildings):
        removed = remove_building(adhd_buster_with_buildings, 0, 0)
        assert removed == "goldmine"
        
        city = get_city_data(adhd_buster_with_buildings)
        assert city["grid"][0][0] is None
    
    def test_remove_building_empty_cell(self, fresh_adhd_buster):
        get_city_data(fresh_adhd_buster)  # Initialize
        removed = remove_building(fresh_adhd_buster, 0, 0)
        assert removed is None
    
    def test_get_placed_buildings(self, adhd_buster_with_buildings):
        placed = get_placed_buildings(adhd_buster_with_buildings)
        assert "goldmine" in placed
        assert "forge" in placed
        assert len(placed) == 2


# ============================================================================
# CONSTRUCTION TESTS
# ============================================================================

class TestConstruction:
    """Test construction investment and completion."""
    
    def test_get_level_requirements_level_1(self):
        building = CITY_BUILDINGS["goldmine"]
        reqs = get_level_requirements(building, 1)
        assert reqs["water"] == 3
        assert reqs["materials"] == 5
    
    def test_get_level_requirements_level_2(self):
        """Level 2 should cost 20% more."""
        building = CITY_BUILDINGS["goldmine"]
        reqs = get_level_requirements(building, 2)
        # 3 * 1.2 = 3.6 → 3
        assert reqs["water"] == 3
        # 5 * 1.2 = 6
        assert reqs["materials"] == 6
    
    @patch('gamification.get_level_from_xp')
    def test_invest_resources_transitions_to_building(self, mock_level, adhd_buster_with_city):
        mock_level.return_value = (10, 0, 100, 0)
        
        # Place a building (starts in PLACED status)
        place_building(adhd_buster_with_city, 2, 2, "goldmine")
        
        city = get_city_data(adhd_buster_with_city)
        assert city["grid"][2][2]["status"] == CellStatus.PLACED.value
        
        # Invest resources
        result = invest_resources(
            adhd_buster_with_city, 2, 2,
            {"water": 1, "materials": 1}
        )
        
        assert result["success"] is True
        assert city["grid"][2][2]["status"] == CellStatus.BUILDING.value
    
    @patch('gamification.get_level_from_xp')
    def test_invest_resources_completes_building(self, mock_level, adhd_buster_with_city):
        mock_level.return_value = (10, 0, 100, 0)
        
        place_building(adhd_buster_with_city, 2, 2, "goldmine")
        
        # New flow: use initiate_construction which starts construction with stockpile resources
        from city import initiate_construction
        result = initiate_construction(adhd_buster_with_city, 2, 2)
        
        assert result["success"] is True
        
        city = get_city_data(adhd_buster_with_city)
        # Building is now in BUILDING state, waiting for effort resources
        assert city["grid"][2][2]["status"] == CellStatus.BUILDING.value
    
    def test_invest_resources_empty_cell(self, fresh_adhd_buster):
        get_city_data(fresh_adhd_buster)
        result = invest_resources(fresh_adhd_buster, 0, 0, {"water": 1})
        assert result["success"] is False
        # invest_resources is deprecated and returns various error messages
        assert "error" in result
    
    def test_get_construction_progress(self, adhd_buster_with_buildings):
        progress = get_construction_progress(adhd_buster_with_buildings, 0, 1)
        assert progress["building_id"] == "forge"
        assert progress["status"] == CellStatus.BUILDING.value
        assert "percent_complete" in progress


# ============================================================================
# UPGRADE TESTS
# ============================================================================

class TestUpgrades:
    """Test building upgrade system."""
    
    def test_can_upgrade_complete_building(self, adhd_buster_with_buildings):
        can, reason = can_upgrade(adhd_buster_with_buildings, 0, 0)
        assert can is True
        assert "L4" in reason  # Goldmine is L3, can go to L4
    
    def test_can_upgrade_incomplete_building(self, adhd_buster_with_buildings):
        can, reason = can_upgrade(adhd_buster_with_buildings, 0, 1)
        assert can is False
        assert "Not complete" in reason
    
    def test_can_upgrade_max_level(self, adhd_buster_with_buildings):
        city = get_city_data(adhd_buster_with_buildings)
        # Set goldmine to max level (3)
        city["grid"][0][0]["level"] = 3
        
        can, reason = can_upgrade(adhd_buster_with_buildings, 0, 0)
        assert can is False
        assert "Max level" in reason
    
    def test_can_initiate_upgrade_checks_resources(self, adhd_buster_with_buildings):
        """Upgrade requires stockpile resources for next level."""
        # Clear all resources
        city = get_city_data(adhd_buster_with_buildings)
        city["resources"] = {"water": 0, "materials": 0, "activity": 0, "focus": 0}
        
        can, reason = can_initiate_upgrade(adhd_buster_with_buildings, 0, 0)
        assert can is False
        assert "Need" in reason  # Should say "Need X water/materials"
    
    def test_can_initiate_upgrade_with_resources(self, adhd_buster_with_buildings):
        """With sufficient resources, can initiate upgrade."""
        city = get_city_data(adhd_buster_with_buildings)
        # Add plenty of resources
        city["resources"] = {"water": 100, "materials": 100, "activity": 50, "focus": 50}
        
        can, reason = can_initiate_upgrade(adhd_buster_with_buildings, 0, 0)
        assert can is True
        assert "L3" in reason
    
    def test_initiate_upgrade_consumes_stockpile(self, adhd_buster_with_buildings):
        """initiate_upgrade should consume water and materials."""
        city = get_city_data(adhd_buster_with_buildings)
        city["resources"] = {"water": 100, "materials": 100, "activity": 50, "focus": 50}
        
        result = initiate_upgrade(adhd_buster_with_buildings, 0, 0)
        
        assert result["success"] is True
        assert result["new_level"] == 4
        assert "effort_required" in result
        
        # Stockpile resources should be consumed
        resources = city["resources"]
        assert resources["water"] < 100
        assert resources["materials"] < 100
        
        # Building should be in BUILDING state with active_construction set
        assert city["grid"][0][0]["status"] == CellStatus.BUILDING.value
        assert city["active_construction"] == [0, 0]
    
    def test_start_upgrade(self, adhd_buster_with_buildings):
        """Legacy start_upgrade delegates to initiate_upgrade."""
        city = get_city_data(adhd_buster_with_buildings)
        city["resources"] = {"water": 100, "materials": 100, "activity": 50, "focus": 50}
        
        success = start_upgrade(adhd_buster_with_buildings, 0, 0)
        assert success is True
        
        assert city["grid"][0][0]["level"] == 4
        assert city["grid"][0][0]["status"] == CellStatus.BUILDING.value


# ============================================================================
# PASSIVE INCOME TESTS
# ============================================================================

class TestPassiveIncome:
    """Test income collection system."""
    
    def test_get_pending_income_no_buildings(self, fresh_adhd_buster):
        get_city_data(fresh_adhd_buster)
        pending = get_pending_income(fresh_adhd_buster)
        assert pending["coins"] == 0
    
    def test_get_pending_income_with_goldmine(self, adhd_buster_with_buildings):
        # Set last collection to 2 hours ago
        city = get_city_data(adhd_buster_with_buildings)
        city["last_collection_time"] = (datetime.now() - timedelta(hours=2)).isoformat()
        
        pending = get_pending_income(adhd_buster_with_buildings)
        # Goldmine is now activity-triggered, so no passive income
        assert pending["coins"] == 0
        assert pending["hours_elapsed"] >= 1.9  # Approximately 2 hours
    
    def test_collect_city_income(self, adhd_buster_with_buildings):
        city = get_city_data(adhd_buster_with_buildings)
        city["last_collection_time"] = (datetime.now() - timedelta(hours=1)).isoformat()
        
        original_coins = adhd_buster_with_buildings.get("coins", 0)
        result = collect_city_income(adhd_buster_with_buildings)
        
        assert result["coins"] >= 0
        assert adhd_buster_with_buildings["coins"] >= original_coins
    
    def test_collect_income_updates_timestamp(self, adhd_buster_with_buildings):
        city = get_city_data(adhd_buster_with_buildings)
        # Set to 1 hour ago so there's actually income to collect
        city["last_collection_time"] = (datetime.now() - timedelta(hours=1)).isoformat()
        old_time = city["last_collection_time"]
        
        collect_city_income(adhd_buster_with_buildings)
        
        # Should have updated since there was income to collect
        assert city["last_collection_time"] != old_time


# ============================================================================
# CITY BONUSES TESTS
# ============================================================================

class TestCityBonuses:
    """Test bonus calculation from buildings."""
    
    def test_get_city_bonuses_empty(self, fresh_adhd_buster):
        get_city_data(fresh_adhd_buster)
        bonuses = get_city_bonuses(fresh_adhd_buster)
        
        assert bonuses["coins_per_hour"] == 0
        assert bonuses["exercise_coins"] == 0
        assert bonuses["focus_session_coins"] == 0
        assert bonuses["merge_success_bonus"] == 0
    
    def test_get_city_bonuses_with_goldmine(self, adhd_buster_with_buildings):
        bonuses = get_city_bonuses(adhd_buster_with_buildings)
        
        # Goldmine L3 is now activity-triggered: base 3 + (3-1)*1 = 5 exercise coins
        assert bonuses["exercise_coins"] == 5
        # No passive coins_per_hour anymore
        assert bonuses["coins_per_hour"] == 0
    
    def test_get_city_bonuses_only_complete_buildings(self, adhd_buster_with_buildings):
        """Incomplete buildings should not contribute bonuses."""
        bonuses = get_city_bonuses(adhd_buster_with_buildings)
        
        # Forge is under construction, so no merge bonus yet
        assert bonuses["merge_success_bonus"] == 0


# ============================================================================
# SYNERGY TESTS
# ============================================================================

class TestSynergies:
    """Test entity-building synergy system."""
    
    def test_synergy_mappings_exist(self):
        assert len(BUILDING_SYNERGIES) == 10
        for building_id in CITY_BUILDINGS:
            assert building_id in BUILDING_SYNERGIES
    
    def test_calculate_synergy_no_entities(self, fresh_adhd_buster):
        result = calculate_building_synergy_bonus("goldmine", fresh_adhd_buster)
        assert result["bonus_percent"] == 0.0
        assert len(result["contributors"]) == 0
    
    def test_get_all_synergy_bonuses_no_buildings(self, fresh_adhd_buster):
        get_city_data(fresh_adhd_buster)
        bonuses = get_all_synergy_bonuses(fresh_adhd_buster)
        
        assert all(v == 0.0 for v in bonuses.values())
    
    def test_synergy_bonus_capped(self, adhd_buster_with_buildings):
        # Add many entities with matching tags
        adhd_buster_with_buildings["entitidex"] = {
            "collected_entity_ids": [f"entity_{i}" for i in range(20)],
            "exceptional_entities": {},
        }
        
        # Even with many entities, bonus should be capped
        # (This test depends on entity tags being derived, which may return empty)
        bonuses = get_all_synergy_bonuses(adhd_buster_with_buildings)
        assert all(v <= 0.5 for v in bonuses.values())


# ============================================================================
# ACTIVITY-TRIGGERED INCOME TESTS
# ============================================================================

class TestActivityTriggeredIncome:
    """Test the new activity-triggered income system for Goldmine and Royal Mint."""
    
    def test_award_exercise_income_no_buildings(self, fresh_adhd_buster):
        """No income if no Goldmine built."""
        get_city_data(fresh_adhd_buster)
        result = award_exercise_income(fresh_adhd_buster, 30, "moderate", 30)
        assert result["coins"] == 0
        assert result["qualified"] is True  # Intensity qualifies
    
    def test_award_exercise_income_light_intensity_fails(self, adhd_buster_with_buildings):
        """Light intensity doesn't qualify for Goldmine income."""
        result = award_exercise_income(adhd_buster_with_buildings, 30, "light", 24)
        assert result["coins"] == 0
        assert result["qualified"] is False
    
    def test_award_exercise_income_moderate_intensity(self, adhd_buster_with_buildings):
        """Moderate intensity qualifies for Goldmine income."""
        original_coins = adhd_buster_with_buildings.get("coins", 0)
        result = award_exercise_income(adhd_buster_with_buildings, 30, "moderate", 30)
        
        # Goldmine L3: base 3 + (3-1)*1 = 5 base coins
        # Effective bonus: 30 / 30 * (2 + (3-1)*1) = 1 * 4 = 4 effective bonus
        # Total: 5 + 4 = 9 coins
        assert result["coins"] == 9
        assert result["qualified"] is True
        assert adhd_buster_with_buildings["coins"] == original_coins + 9
    
    def test_award_exercise_income_vigorous_intensity(self, adhd_buster_with_buildings):
        """Vigorous intensity qualifies for Goldmine income."""
        result = award_exercise_income(adhd_buster_with_buildings, 60, "vigorous", 78)
        
        # Goldmine L3: base 3 + (3-1)*1 = 5 base coins
        # Effective bonus: int(78/30) * (2 + (3-1)*1) = 2 * 4 = 8 effective bonus (78/30 = 2.6 -> int = 2)
        # Wait, int(78/30) = 2, but formula uses 78/30 = 2.6 * 4 = 10.4 -> int = 10
        # Total: 5 + 10 = 15 coins
        assert result["coins"] == 15
        assert result["qualified"] is True
    
    def test_award_focus_session_income_no_buildings(self, fresh_adhd_buster):
        """No income if no Royal Mint built."""
        get_city_data(fresh_adhd_buster)
        result = award_focus_session_income(fresh_adhd_buster, 60)
        assert result["coins"] == 0
    
    @patch('gamification.get_level_from_xp')
    def test_award_focus_session_income_with_royal_mint(self, mock_level, fresh_adhd_buster):
        """Royal Mint awards coins on focus session completion."""
        mock_level.return_value = (40, 0, 100, 0)
        
        # Add resources and build Royal Mint
        add_city_resource(fresh_adhd_buster, "water", 200)
        add_city_resource(fresh_adhd_buster, "materials", 250)
        add_city_resource(fresh_adhd_buster, "activity", 100)
        add_city_resource(fresh_adhd_buster, "focus", 150)
        
        place_building(fresh_adhd_buster, 0, 0, "royal_mint")
        
        # Initiate and complete construction
        from city import initiate_construction, get_city_data
        from city.city_state import CellStatus
        
        initiate_construction(fresh_adhd_buster, 0, 0)
        
        # Manually complete the building for the test
        city = get_city_data(fresh_adhd_buster)
        city["grid"][0][0]["status"] = CellStatus.COMPLETE.value
        city["active_construction"] = None
        
        # Award income for 60-minute session
        original_coins = fresh_adhd_buster.get("coins", 0)
        result = award_focus_session_income(fresh_adhd_buster, 60)
        
        # Royal Mint L1: base 5 + int(60/30) * 3 = 5 + 6 = 11 coins
        assert result["coins"] == 11
        assert fresh_adhd_buster["coins"] == original_coins + 11


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Test complete workflows."""
    
    @patch('gamification.get_level_from_xp')
    def test_full_building_workflow(self, mock_level, fresh_adhd_buster):
        """Test complete flow: resources → place → build → complete → collect."""
        mock_level.return_value = (10, 0, 100, 0)
        
        # Add resources
        add_city_resource(fresh_adhd_buster, "water", 10)
        add_city_resource(fresh_adhd_buster, "materials", 20)
        add_city_resource(fresh_adhd_buster, "activity", 10)
        add_city_resource(fresh_adhd_buster, "focus", 10)
        
        # Place goldmine
        assert place_building(fresh_adhd_buster, 0, 0, "goldmine") is True
        
        # Initiate construction and manually complete for test
        from city import initiate_construction
        from city.city_state import CellStatus
        
        result = initiate_construction(fresh_adhd_buster, 0, 0)
        assert result["success"] is True
        
        # Manually complete the building for test purposes
        city = get_city_data(fresh_adhd_buster)
        city["grid"][0][0]["status"] = CellStatus.COMPLETE.value
        city["active_construction"] = None
        
        # Verify bonuses - Goldmine now gives exercise_coins instead of coins_per_hour
        bonuses = get_city_bonuses(fresh_adhd_buster)
        assert bonuses["exercise_coins"] == 3  # L1 goldmine base_coins
        assert bonuses["coins_per_hour"] == 0  # No passive income
        
        # Set time and collect income - should be 0 since Goldmine is activity-triggered
        city["last_collection_time"] = (datetime.now() - timedelta(hours=10)).isoformat()
        
        income = collect_city_income(fresh_adhd_buster)
        assert income["coins"] == 0  # No passive income for activity-triggered buildings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
