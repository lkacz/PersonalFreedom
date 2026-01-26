"""
City Building System
====================
A passive income generator where users invest resources earned through
healthy activities to construct buildings that produce Coins and XP.

Usage:
    from city import get_city_bonuses, add_city_resource, collect_city_income
    
    # Get all city bonuses for gameplay modifiers
    bonuses = get_city_bonuses(adhd_buster)
    
    # Add resources from activities
    add_city_resource(adhd_buster, "water", 1)
    
    # Collect passive income
    income = collect_city_income(adhd_buster)
"""

# Module availability flag (matches existing pattern in gamification.py)
CITY_AVAILABLE = True

# Core state management
from .city_state import (
    CellStatus,
    CellState,
    CityData,
    ResourceAmounts,
    ConstructionProgress,
    create_empty_grid,
    create_default_city_data,
    create_cell_state,
)

# Constants
from .city_constants import (
    RESOURCE_TYPES,
    STOCKPILE_RESOURCES,
    EFFORT_RESOURCES,
    RESOURCE_EMOJI,
    MAX_OFFLINE_HOURS,
    BUILDING_SLOT_UNLOCKS,
    GRID_ROWS,
    GRID_COLS,
    UPGRADE_COST_MULTIPLIER,
    DEMOLISH_REFUND_PERCENT,
)

# Building definitions
from .city_buildings import CITY_BUILDINGS, get_building_by_id, get_all_building_ids

# Business logic
from .city_manager import (
    get_city_data,
    get_city_bonuses,
    add_city_resource,
    get_resources,
    consume_resources,
    can_place_building,
    place_building,
    remove_building,
    move_building,
    invest_resources,
    get_active_construction,
    get_active_construction_info,
    can_initiate_construction,
    initiate_construction,
    collect_city_income,
    get_pending_income,
    award_focus_session_income,
    award_exercise_income,
    get_max_building_slots,
    get_available_slots,
    get_next_slot_unlock,
    get_slot_unlock_at_level,
    get_placed_buildings,
    get_level_requirements,
    get_construction_progress,
    can_upgrade,
    can_initiate_upgrade,
    initiate_upgrade,
    start_upgrade,
)

# Synergy system
from .city_synergies import (
    BUILDING_SYNERGIES,
    SynergyMapping,
    calculate_building_synergy_bonus,
    get_all_synergy_bonuses,
    get_entity_synergy_tags,
    get_synergy_display_info,
)

__all__ = [
    # Module flag
    "CITY_AVAILABLE",
    
    # State types
    "CellStatus",
    "CellState",
    "CityData",
    "ResourceAmounts",
    "ConstructionProgress",
    
    # State helpers
    "create_empty_grid",
    "create_default_city_data",
    "create_cell_state",
    
    # Constants
    "RESOURCE_TYPES",
    "STOCKPILE_RESOURCES",
    "EFFORT_RESOURCES",
    "RESOURCE_EMOJI",
    "MAX_OFFLINE_HOURS",
    "BUILDING_SLOT_UNLOCKS",
    "GRID_ROWS",
    "GRID_COLS",
    "UPGRADE_COST_MULTIPLIER",
    "DEMOLISH_REFUND_PERCENT",
    
    # Buildings
    "CITY_BUILDINGS",
    "get_building_by_id",
    "get_all_building_ids",
    
    # Manager functions
    "get_city_data",
    "get_city_bonuses",
    "add_city_resource",
    "get_resources",
    "consume_resources",
    "can_place_building",
    "place_building",
    "remove_building",
    "move_building",
    "invest_resources",
    "get_active_construction",
    "get_active_construction_info",
    "can_initiate_construction",
    "initiate_construction",
    "collect_city_income",
    "get_pending_income",
    "award_focus_session_income",
    "award_exercise_income",
    "get_max_building_slots",
    "get_available_slots",
    "get_next_slot_unlock",
    "get_slot_unlock_at_level",
    "get_placed_buildings",
    "get_level_requirements",
    "get_construction_progress",
    "can_upgrade",
    "can_initiate_upgrade",
    "initiate_upgrade",
    "start_upgrade",
    
    # Synergy system
    "BUILDING_SYNERGIES",
    "SynergyMapping",
    "calculate_building_synergy_bonus",
    "get_all_synergy_bonuses",
    "get_entity_synergy_tags",
    "get_synergy_display_info",
]
