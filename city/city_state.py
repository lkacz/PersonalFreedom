"""
City Building System - State Management
=======================================
Enums and type definitions for city state.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, TypedDict
from dataclasses import dataclass, field
from datetime import datetime


class CellStatus(str, Enum):
    """
    Explicit cell states - never infer from other fields.
    
    Using str, Enum for JSON serialization compatibility.
    
    Construction Flow:
    1. PLACED - Building selected, awaiting material payment to initiate
    2. BUILDING - Construction initiated (materials paid), receiving effort resources
    3. COMPLETE - Fully built, generating bonuses
    
    Only ONE building can be in BUILDING status at a time (active construction).
    """
    EMPTY = "empty"       # No building (cell is None in grid)
    PLACED = "placed"     # Building selected but construction not initiated (needs water+materials)
    BUILDING = "building" # Under active construction (receiving activity+focus)
    COMPLETE = "complete" # Fully built, generating bonuses


class ConstructionProgress(TypedDict):
    """Type definition for construction progress tracking."""
    water: int
    materials: int
    activity: int
    focus: int


class CellState(TypedDict, total=False):
    """
    Type definition for a grid cell with a building.
    
    Note: Empty cells are represented as None, not CellState with empty status.
    """
    building_id: str                    # Which building ("goldmine", "forge", etc.)
    status: str                         # CellStatus value
    level: int                          # Current level (1-max_level)
    construction_progress: ConstructionProgress
    placed_at: Optional[str]            # ISO timestamp when placed
    completed_at: Optional[str]         # ISO timestamp when level completed


class ResourceAmounts(TypedDict):
    """Type definition for resource amounts."""
    water: int
    materials: int
    activity: int
    focus: int


class CityData(TypedDict, total=False):
    """
    Type definition for the complete city state.
    
    Stored in adhd_buster["city"].
    """
    grid: List[List[Optional[CellState]]]  # 5×5 grid, None for empty cells
    resources: ResourceAmounts              # Current resource amounts (only water+materials accumulate)
    active_construction: Optional[tuple]    # (row, col) of building currently under construction, or None
    total_coins_generated: int              # Lifetime coins from city
    total_xp_generated: int                 # Lifetime XP from city
    last_collection_time: str               # ISO timestamp of last income collection


def create_empty_grid() -> List[List[None]]:
    """
    Create an empty 5×5 grid.
    
    IMPORTANT: Use list comprehension, NOT [[None]*5]*5
    The latter creates reference bugs where all rows point to same list.
    """
    from .city_constants import GRID_ROWS, GRID_COLS
    return [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]


def create_default_city_data() -> CityData:
    """Create default city data structure for new players."""
    return {
        "grid": create_empty_grid(),
        "resources": {
            "water": 0,
            "materials": 0,
            # Note: activity and focus are NOT stored here - they flow directly to active construction
            "activity": 0,  # Legacy field, kept at 0
            "focus": 0,     # Legacy field, kept at 0
        },
        "active_construction": None,  # (row, col) of building receiving effort resources
        "total_coins_generated": 0,
        "total_xp_generated": 0,
        "last_collection_time": datetime.now().isoformat(),
    }


def create_cell_state(building_id: str) -> CellState:
    """Create a new cell state for placing a building."""
    return {
        "building_id": building_id,
        "status": CellStatus.PLACED.value,
        "level": 1,
        "construction_progress": {
            "water": 0,
            "materials": 0,
            "activity": 0,
            "focus": 0,
        },
        "placed_at": datetime.now().isoformat(),
        "completed_at": None,
    }
