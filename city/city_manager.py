"""
City Building System - Manager
==============================
Core business logic for city operations.

This module is the single source of truth for all city state mutations.
All UI code should call these functions rather than directly modifying state.
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

from .city_constants import (
    RESOURCE_TYPES,
    STOCKPILE_RESOURCES,
    EFFORT_RESOURCES,
    MAX_OFFLINE_HOURS,
    BUILDING_SLOT_UNLOCKS,
    GRID_ROWS,
    GRID_COLS,
    UPGRADE_COST_MULTIPLIER,
    DEMOLISH_REFUND_PERCENT,
)
from .city_state import (
    CellStatus,
    CellState,
    CityData,
    create_default_city_data,
    create_cell_state,
)
from .city_buildings import CITY_BUILDINGS

_logger = logging.getLogger(__name__)


def _is_valid_grid_cell(grid: list, row: int, col: int) -> bool:
    """
    Check if grid[row][col] is safely accessible.
    
    Returns True if the cell exists, False if grid is malformed or coords are out of bounds.
    """
    if row < 0 or row >= len(grid):
        return False
    if col < 0 or col >= len(grid[row]):
        return False
    return True


# ============================================================================
# STATE ACCESS
# ============================================================================

def get_city_data(adhd_buster: dict) -> CityData:
    """
    Get or initialize city data from adhd_buster.
    
    Creates default structure if missing.
    This is the entry point for all city state access.
    """
    if "city" not in adhd_buster:
        adhd_buster["city"] = create_default_city_data()
    return adhd_buster["city"]


def get_placed_buildings(adhd_buster: dict) -> List[str]:
    """
    Get list of building IDs currently placed in the grid.
    
    Scans grid (source of truth) rather than maintaining separate list.
    """
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    placed = []
    for row in grid:
        for cell in row:
            if cell is not None:
                placed.append(cell.get("building_id"))
    
    return placed


# ============================================================================
# LEVEL-GATED BUILDING SLOTS
# ============================================================================

def get_max_building_slots(player_level: int) -> int:
    """
    Get maximum building slots available at given player level.
    
    Returns number of buildings the player can have placed.
    Building TYPES are never restricted - only slot COUNT.
    """
    max_slots = 0  # Default for level 1 (no lots until level 2)
    for level_threshold, slots in sorted(BUILDING_SLOT_UNLOCKS.items()):
        if player_level >= level_threshold:
            max_slots = slots
    return max_slots


def get_available_slots(adhd_buster: dict) -> int:
    """
    Get remaining slots player can use for new buildings.
    
    Returns: max_slots - current_buildings_placed
    """
    from gamification import get_level_from_xp
    
    # Get player level from XP
    total_xp = adhd_buster.get("total_xp", 0)
    player_level = get_level_from_xp(total_xp)[0]
    
    max_slots = get_max_building_slots(player_level)
    current_buildings = len(get_placed_buildings(adhd_buster))
    
    return max(0, max_slots - current_buildings)


def get_next_slot_unlock(adhd_buster: dict) -> dict:
    """
    Get info about next slot unlock for UI display.
    
    Returns: {
        "current_slots": int,
        "current_level": int,
        "next_unlock_level": int or None,
        "slots_after": int or None,
    }
    """
    from gamification import get_level_from_xp
    
    total_xp = adhd_buster.get("total_xp", 0)
    player_level = get_level_from_xp(total_xp)[0]
    
    current_max = get_max_building_slots(player_level)
    
    # Find next unlock threshold
    next_level = None
    next_slots = None
    for level_threshold, slots in sorted(BUILDING_SLOT_UNLOCKS.items()):
        if level_threshold > player_level:
            next_level = level_threshold
            next_slots = slots
            break
    
    return {
        "current_slots": current_max,
        "current_level": player_level,
        "next_unlock_level": next_level,  # None if maxed
        "slots_after": next_slots,
    }


def get_slot_unlock_at_level(new_level: int, old_level: int = None) -> dict:
    """
    Check if a level unlocks a new building slot.
    
    Args:
        new_level: The level just reached
        old_level: The previous level (optional, if None checks if new_level is an unlock level)
    
    Returns: {
        "unlocked": bool,  # True if this level unlocks a new slot
        "slot_number": int or None,  # Which slot number (1-10) was unlocked
        "total_slots": int,  # Total slots available at new_level
        "is_first_slot": bool,  # True if this is the first building slot
        "all_slots_unlocked": bool,  # True if all 10 slots are now unlocked
    }
    """
    new_slots = get_max_building_slots(new_level)
    old_slots = get_max_building_slots(old_level) if old_level else 0
    
    # Check if we unlocked at least one new slot
    unlocked = new_slots > old_slots
    
    # If multiple levels were skipped, report the slots unlocked
    slots_unlocked = new_slots - old_slots if unlocked else 0
    
    return {
        "unlocked": unlocked,
        "slot_number": new_slots if unlocked else None,
        "slots_unlocked_count": slots_unlocked,
        "total_slots": new_slots,
        "is_first_slot": new_slots == 1 and old_slots == 0,
        "all_slots_unlocked": new_slots >= 10,
    }


# ============================================================================
# RESOURCE MANAGEMENT
# ============================================================================

def get_active_construction(adhd_buster: dict) -> Optional[Tuple[int, int]]:
    """
    Get the coordinates of the currently active construction.
    
    Only ONE building can be under active construction at a time.
    Activity and Focus resources flow directly to this building.
    
    Returns:
        (row, col) tuple if there's active construction, None otherwise
    """
    city = get_city_data(adhd_buster)
    active = city.get("active_construction")
    
    if active is None:
        return None
    
    # Handle both tuple and list formats (JSON serialization converts tuples to lists)
    if isinstance(active, (list, tuple)) and len(active) == 2:
        row, col = active
        # Verify the building is still in BUILDING status
        grid = city.get("grid", [])
        if _is_valid_grid_cell(grid, row, col):
            cell = grid[row][col]
            if cell and cell.get("status") == CellStatus.BUILDING.value:
                return (row, col)
    
    # Active construction is invalid or completed - clear it
    city["active_construction"] = None
    return None


def get_active_construction_info(adhd_buster: dict) -> Optional[dict]:
    """
    Get detailed info about the active construction for UI display.
    
    Returns:
        {
            "row": int,
            "col": int,
            "building_id": str,
            "building_name": str,
            "level": int,
            "progress": {resource: invested},
            "requirements": {resource: needed},
            "effort_progress_percent": float,  # Activity+Focus progress only
        }
        or None if no active construction
    """
    coords = get_active_construction(adhd_buster)
    if coords is None:
        return None
    
    row, col = coords
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    cell = grid[row][col]
    
    building_id = cell.get("building_id")
    building_def = CITY_BUILDINGS.get(building_id, {})
    level = cell.get("level", 1)
    requirements = get_level_requirements(building_def, level)
    progress = cell.get("construction_progress", {})
    
    # Calculate effort progress (activity + focus only)
    effort_required = sum(requirements.get(r, 0) for r in EFFORT_RESOURCES)
    effort_invested = sum(progress.get(r, 0) for r in EFFORT_RESOURCES)
    effort_percent = (effort_invested / effort_required * 100) if effort_required > 0 else 100
    
    return {
        "row": row,
        "col": col,
        "building_id": building_id,
        "building_name": building_def.get("name", building_id),
        "level": level,
        "progress": progress.copy(),
        "requirements": requirements,
        "effort_progress_percent": min(100.0, effort_percent),
    }


def add_city_resource(
    adhd_buster: dict,
    resource_type: str,
    amount: int,
    game_state=None
) -> int:
    """
    Add resources to city inventory OR directly to active construction.
    
    STOCKPILE RESOURCES (water, materials):
        - Accumulate in city inventory
        - User spends them manually to initiate construction
    
    EFFORT RESOURCES (activity, focus):
        - Flow DIRECTLY to active construction (if any)
        - Do NOT accumulate - represent real-time effort
        - If no active construction, the effort is lost (with warning)
    
    Args:
        adhd_buster: Player data dict
        resource_type: One of RESOURCE_TYPES
        amount: Amount to add
        game_state: Optional GameStateManager for signal emission
    
    Returns:
        New total for that resource (or amount invested if effort resource)
    """
    if resource_type not in RESOURCE_TYPES:
        _logger.warning(f"Invalid resource type: {resource_type}")
        return 0
    
    city = get_city_data(adhd_buster)
    
    # EFFORT RESOURCES: Route directly to active construction
    if resource_type in EFFORT_RESOURCES:
        return _add_effort_to_construction(adhd_buster, resource_type, amount, game_state)
    
    # STOCKPILE RESOURCES: Accumulate in inventory
    resources = city.get("resources", {})
    old_value = resources.get(resource_type, 0)
    new_value = old_value + amount
    resources[resource_type] = new_value
    city["resources"] = resources
    
    # Emit signal for UI toast notification
    if game_state is not None:
        try:
            if hasattr(game_state, 'city_resource_earned'):
                game_state._emit(
                    game_state.city_resource_earned,
                    resource_type, amount, new_value
                )
        except Exception as e:
            _logger.debug(f"Failed to emit city_resource_earned: {e}")
    
    return new_value


def _add_effort_to_construction(
    adhd_buster: dict,
    resource_type: str,
    amount: int,
    game_state=None
) -> int:
    """
    Add effort resource (activity/focus) directly to active construction.
    
    Returns amount actually invested (0 if no active construction or not needed).
    """
    coords = get_active_construction(adhd_buster)
    
    if coords is None:
        # No active construction - effort is "wasted" but that's by design
        # The user should initiate a building first
        _logger.debug(f"No active construction to receive {resource_type} - effort not applied")
        return 0
    
    row, col = coords
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    cell = grid[row][col]
    
    building_id = cell.get("building_id")
    building_def = CITY_BUILDINGS.get(building_id, {})
    level = cell.get("level", 1)
    requirements = get_level_requirements(building_def, level)
    progress = cell.get("construction_progress", {})
    
    # Calculate how much we need and can invest
    needed = requirements.get(resource_type, 0)
    invested = progress.get(resource_type, 0)
    remaining = max(0, needed - invested)
    to_invest = min(amount, remaining)
    
    if to_invest <= 0:
        return 0
    
    # Apply the effort
    progress[resource_type] = invested + to_invest
    cell["construction_progress"] = progress
    
    # Emit progress signal
    if game_state and hasattr(game_state, 'city_building_progress'):
        try:
            game_state._emit(game_state.city_building_progress, building_id)
        except Exception:
            pass
    
    # Check if construction is now complete (all resources met)
    completed = all(
        progress.get(r, 0) >= requirements.get(r, 0)
        for r in RESOURCE_TYPES
    )
    
    if completed:
        _complete_construction(adhd_buster, row, col, game_state)
    
    return to_invest


def _complete_construction(
    adhd_buster: dict,
    row: int,
    col: int,
    game_state=None
) -> None:
    """Mark a building as complete and award rewards."""
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    cell = grid[row][col]
    
    cell["status"] = CellStatus.COMPLETE.value
    cell["completed_at"] = datetime.now().isoformat()
    
    # Clear active construction
    city["active_construction"] = None
    
    building_id = cell.get("building_id")
    building_def = CITY_BUILDINGS.get(building_id, {})
    
    # Award completion reward
    reward = building_def.get("completion_reward", {})
    if reward:
        _award_completion_reward(adhd_buster, reward, game_state)
    
    # Emit building completed signal
    if game_state and hasattr(game_state, 'city_building_completed'):
        try:
            game_state._emit(game_state.city_building_completed, building_id)
        except Exception:
            pass
    
    _logger.info(f"Building {building_id} at ({row}, {col}) completed!")


def get_resources(adhd_buster: dict) -> Dict[str, int]:
    """Get current resource amounts."""
    city = get_city_data(adhd_buster)
    return city.get("resources", {}).copy()


def consume_resources(adhd_buster: dict, amounts: Dict[str, int]) -> bool:
    """
    Consume resources from city inventory.
    
    Returns True if successful, False if insufficient resources.
    """
    city = get_city_data(adhd_buster)
    resources = city.get("resources", {})
    
    # Check if we have enough
    for resource, needed in amounts.items():
        if resources.get(resource, 0) < needed:
            return False
    
    # Consume
    for resource, needed in amounts.items():
        resources[resource] = resources.get(resource, 0) - needed
    
    return True


# ============================================================================
# BUILDING PLACEMENT
# ============================================================================

def can_place_building(adhd_buster: dict, building_id: str) -> Tuple[bool, str]:
    """
    Check if a building can be placed.
    
    Checks:
    1. Building type is valid
    2. Building not already placed (uniqueness)
    3. Player has available building slots (level-gated)
    
    Returns (can_place, reason).
    """
    if building_id not in CITY_BUILDINGS:
        return False, "Unknown building"
    
    placed = get_placed_buildings(adhd_buster)
    if building_id in placed:
        return False, "Already placed in city"
    
    # Check slot availability based on player level
    available_slots = get_available_slots(adhd_buster)
    if available_slots <= 0:
        next_info = get_next_slot_unlock(adhd_buster)
        if next_info["next_unlock_level"]:
            return False, f"No slots available. Next slot at Level {next_info['next_unlock_level']}"
        else:
            return False, "Maximum buildings reached"
    
    return True, "Ready to place"


def place_building(
    adhd_buster: dict,
    row: int,
    col: int,
    building_id: str
) -> bool:
    """
    Place a building in an empty cell.
    
    Returns True on success, False on failure.
    """
    can_place, reason = can_place_building(adhd_buster, building_id)
    if not can_place:
        _logger.warning(f"Cannot place {building_id}: {reason}")
        return False
    
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    # Validate coordinates
    if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
        _logger.warning(f"Invalid cell coordinates: ({row}, {col})")
        return False
    
    # Safe grid access - handle malformed data
    if not _is_valid_grid_cell(grid, row, col):
        _logger.warning(f"Grid data corrupted at ({row}, {col})")
        return False
    
    # Check cell is empty
    if grid[row][col] is not None:
        _logger.warning(f"Cell ({row}, {col}) is not empty")
        return False
    
    # Place the building
    grid[row][col] = create_cell_state(building_id)
    
    _logger.info(f"Placed {building_id} at ({row}, {col})")
    return True


def place_and_start_building(
    adhd_buster: dict,
    row: int,
    col: int,
    building_id: str,
    game_state=None
) -> dict:
    """
    Place a building AND immediately start construction in one step.
    
    This combines place_building() + initiate_construction() for a streamlined flow:
    1. Validates building can be placed
    2. Checks no other building is under construction
    3. Checks player has sufficient stockpile resources (water + materials)
    4. Places building AND starts construction
    5. Sets this as active_construction
    
    Args:
        adhd_buster: Player data
        row, col: Grid coordinates
        building_id: ID of building to construct
        game_state: Optional for signals
    
    Returns:
        {
            "success": bool,
            "error": str (if failed),
            "building_id": str,
            "building_name": str,
            "effort_required": {"activity": int, "focus": int},
            "missing_resources": {"water": int, "materials": int} (if resources insufficient),
        }
    """
    # Check if building can be placed (type valid, not already built, slots available)
    can_place, place_reason = can_place_building(adhd_buster, building_id)
    if not can_place:
        return {"success": False, "error": place_reason}
    
    # Check if another building is already under construction
    active = get_active_construction(adhd_buster)
    if active is not None:
        city = get_city_data(adhd_buster)
        grid = city.get("grid", [])
        active_row, active_col = active
        if _is_valid_grid_cell(grid, active_row, active_col):
            active_cell = grid[active_row][active_col]
            if active_cell:
                active_name = CITY_BUILDINGS.get(active_cell.get("building_id"), {}).get("name", "Unknown")
                return {"success": False, "error": f"Already building: {active_name}. Complete it first!"}
        return {"success": False, "error": "Another building is under construction"}
    
    # Get building definition and requirements
    building_def = CITY_BUILDINGS.get(building_id)
    if not building_def:
        return {"success": False, "error": "Unknown building type"}
    
    requirements = get_level_requirements(building_def, 1)  # Level 1 for new building
    
    # Check if player has sufficient stockpile resources
    city = get_city_data(adhd_buster)
    resources = city.get("resources", {})
    missing = {}
    for res_type in STOCKPILE_RESOURCES:
        needed = requirements.get(res_type, 0)
        have = resources.get(res_type, 0)
        if have < needed:
            missing[res_type] = needed - have
    
    if missing:
        return {
            "success": False, 
            "error": "Insufficient resources",
            "missing_resources": missing,
        }
    
    grid = city.get("grid", [])
    
    # Validate coordinates
    if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
        return {"success": False, "error": "Invalid grid coordinates"}
    
    if not _is_valid_grid_cell(grid, row, col):
        return {"success": False, "error": "Grid data corrupted"}
    
    # Check cell is empty
    if grid[row][col] is not None:
        return {"success": False, "error": "Plot is not empty"}
    
    # Create new cell state directly in BUILDING status (skip PLACED)
    from datetime import datetime
    cell = {
        "building_id": building_id,
        "status": CellStatus.BUILDING.value,  # Start as BUILDING, not PLACED
        "level": 1,
        "construction_progress": {},
        "placed_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    
    # Consume and record stockpile resources
    progress = cell["construction_progress"]
    for res_type in STOCKPILE_RESOURCES:
        needed = requirements.get(res_type, 0)
        resources[res_type] = resources.get(res_type, 0) - needed
        progress[res_type] = needed  # Mark as fully invested
    
    # Place the building
    grid[row][col] = cell
    
    # Set as active construction
    city["active_construction"] = [row, col]
    
    _logger.info(f"Placed and started construction of {building_id} at ({row}, {col})")
    
    # Emit construction started signal
    if game_state and hasattr(game_state, 'city_building_progress'):
        try:
            game_state._emit(game_state.city_building_progress, building_id)
        except Exception:
            pass
    
    # Calculate remaining effort needed
    effort_required = {
        res_type: requirements.get(res_type, 0)
        for res_type in EFFORT_RESOURCES
    }
    
    return {
        "success": True,
        "building_id": building_id,
        "building_name": building_def.get("name", building_id),
        "effort_required": effort_required,
    }


def remove_building(
    adhd_buster: dict,
    row: int,
    col: int,
    refund: bool = True
) -> Optional[str]:
    """
    Remove a building from the grid.
    
    Args:
        adhd_buster: Player data
        row, col: Grid coordinates
        refund: Whether to refund invested resources
    
    Returns:
        Building ID that was removed, or None if cell was empty
    """
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
        return None
    
    # Safe grid access - handle malformed data
    if not _is_valid_grid_cell(grid, row, col):
        return None
    
    cell = grid[row][col]
    if cell is None:
        return None
    
    building_id = cell.get("building_id")
    
    # Calculate refund
    if refund:
        progress = cell.get("construction_progress", {})
        refund_amounts = {
            r: int(progress.get(r, 0) * DEMOLISH_REFUND_PERCENT / 100)
            for r in RESOURCE_TYPES
        }
        
        # Add refund to resources
        resources = city.get("resources", {})
        for r, amount in refund_amounts.items():
            if amount > 0:
                resources[r] = resources.get(r, 0) + amount
    
    # Remove building
    grid[row][col] = None
    
    _logger.info(f"Removed {building_id} from ({row}, {col})")
    return building_id


def move_building(
    adhd_buster: dict,
    from_row: int,
    from_col: int,
    to_row: int,
    to_col: int
) -> bool:
    """
    Swap two cells (move/rearrange buildings).
    
    Both cells can be buildings or empty - just swaps contents.
    No refunds, no bonus changes - purely cosmetic.
    """
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    # Validate coordinates
    for r, c in [(from_row, from_col), (to_row, to_col)]:
        if r < 0 or r >= GRID_ROWS or c < 0 or c >= GRID_COLS:
            return False
    
    # Simple swap
    grid[from_row][from_col], grid[to_row][to_col] = \
        grid[to_row][to_col], grid[from_row][from_col]
    
    return True


# ============================================================================
# CONSTRUCTION SYSTEM
# ============================================================================

def get_level_requirements(building_def: dict, level: int) -> Dict[str, int]:
    """
    Calculate requirements for a specific level.
    
    Level 1 = base requirements
    Level N = base * (1.2 ^ (N-1)) - each level costs 20% more
    """
    base = building_def.get("requirements", {})
    if level <= 1:
        return base.copy()
    
    multiplier = UPGRADE_COST_MULTIPLIER ** (level - 1)
    return {r: int(v * multiplier) for r, v in base.items()}


def get_construction_progress(adhd_buster: dict, row: int, col: int) -> dict:
    """
    Get detailed construction progress for a cell.
    
    Returns:
        {
            "building_id": str,
            "level": int,
            "status": str,
            "progress": {resource: invested},
            "requirements": {resource: needed},
            "percent_complete": float,
        }
    """
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
        return {}
    
    # Safe grid access - handle malformed data
    if not _is_valid_grid_cell(grid, row, col):
        return {}
    
    cell = grid[row][col]
    if cell is None:
        return {}
    
    building_id = cell.get("building_id")
    building_def = CITY_BUILDINGS.get(building_id, {})
    level = cell.get("level", 1)
    requirements = get_level_requirements(building_def, level)
    progress = cell.get("construction_progress", {})
    
    total_required = sum(requirements.values())
    total_invested = sum(progress.get(r, 0) for r in requirements)
    percent = (total_invested / total_required * 100) if total_required > 0 else 100
    
    return {
        "building_id": building_id,
        "level": level,
        "status": cell.get("status"),
        "progress": progress.copy(),
        "requirements": requirements,
        "percent_complete": min(100.0, percent),
    }


def invest_resources(
    adhd_buster: dict,
    row: int,
    col: int,
    resources_to_invest: Dict[str, int],
    game_state=None
) -> dict:
    """
    DEPRECATED: Use initiate_construction() for new construction flow.
    
    This function is kept for backward compatibility but now only handles
    STOCKPILE resources (water, materials) for initiating construction.
    EFFORT resources (activity, focus) flow automatically via add_city_resource().
    
    For the new flow:
    1. User calls initiate_construction() with water+materials payment
    2. Activity+focus flow automatically to active_construction
    """
    # Filter to only stockpile resources
    stockpile_only = {
        r: v for r, v in resources_to_invest.items()
        if r in STOCKPILE_RESOURCES
    }
    
    if not stockpile_only:
        return {"success": False, "error": "Use initiate_construction() for new flow"}
    
    # Delegate to initiate_construction if this is a PLACED building
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    if not _is_valid_grid_cell(grid, row, col):
        return {"success": False, "error": "Invalid cell"}
    
    cell = grid[row][col]
    if cell and cell.get("status") == CellStatus.PLACED.value:
        return initiate_construction(adhd_buster, row, col, game_state)
    
    return {"success": False, "error": "Building already initiated or complete"}


def can_initiate_construction(adhd_buster: dict, row: int, col: int) -> Tuple[bool, str]:
    """
    Check if a PLACED building can be initiated (construction started).
    
    Requirements:
    1. Building must be in PLACED status
    2. No other building is currently under active construction
    3. Player has sufficient water + materials
    
    Returns (can_initiate, reason).
    """
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
        return False, "Invalid coordinates"
    
    if not _is_valid_grid_cell(grid, row, col):
        return False, "Grid data corrupted"
    
    cell = grid[row][col]
    if cell is None:
        return False, "No building at this location"
    
    if cell.get("status") != CellStatus.PLACED.value:
        if cell.get("status") == CellStatus.BUILDING.value:
            return False, "Already under construction"
        elif cell.get("status") == CellStatus.COMPLETE.value:
            return False, "Already complete"
        return False, f"Invalid status: {cell.get('status')}"
    
    # Check if another building is already under construction
    active = get_active_construction(adhd_buster)
    if active is not None:
        active_row, active_col = active
        active_cell = grid[active_row][active_col]
        active_name = CITY_BUILDINGS.get(active_cell.get("building_id"), {}).get("name", "Unknown")
        return False, f"Already building: {active_name}"
    
    # Check if player has sufficient stockpile resources
    building_id = cell.get("building_id")
    building_def = CITY_BUILDINGS.get(building_id, {})
    level = cell.get("level", 1)
    requirements = get_level_requirements(building_def, level)
    resources = city.get("resources", {})
    
    for res_type in STOCKPILE_RESOURCES:
        needed = requirements.get(res_type, 0)
        have = resources.get(res_type, 0)
        if have < needed:
            return False, f"Need {needed} {res_type}, have {have}"
    
    return True, "Ready to initiate"


def initiate_construction(
    adhd_buster: dict,
    row: int,
    col: int,
    game_state=None
) -> dict:
    """
    Initiate construction on a PLACED building.
    
    This is the NEW construction flow:
    1. Consumes water + materials from inventory (upfront payment)
    2. Transitions building from PLACED → BUILDING
    3. Sets this building as active_construction
    4. From now on, all activity + focus earned flows to this building
    
    Args:
        adhd_buster: Player data
        row, col: Grid coordinates of PLACED building
        game_state: Optional for signals
    
    Returns:
        {
            "success": bool,
            "error": str (if failed),
            "building_id": str,
            "building_name": str,
            "effort_required": {"activity": int, "focus": int},
        }
    """
    can, reason = can_initiate_construction(adhd_buster, row, col)
    if not can:
        return {"success": False, "error": reason}
    
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    cell = grid[row][col]
    
    building_id = cell.get("building_id")
    building_def = CITY_BUILDINGS.get(building_id, {})
    level = cell.get("level", 1)
    requirements = get_level_requirements(building_def, level)
    resources = city.get("resources", {})
    progress = cell.get("construction_progress", {})
    
    # Consume stockpile resources (water + materials)
    for res_type in STOCKPILE_RESOURCES:
        needed = requirements.get(res_type, 0)
        resources[res_type] = resources.get(res_type, 0) - needed
        progress[res_type] = needed  # Mark as fully invested
    
    cell["construction_progress"] = progress
    
    # Transition to BUILDING status
    cell["status"] = CellStatus.BUILDING.value
    
    # Set as active construction
    city["active_construction"] = [row, col]  # List for JSON serialization
    
    _logger.info(f"Initiated construction of {building_id} at ({row}, {col})")
    
    # Emit construction started signal
    if game_state and hasattr(game_state, 'city_building_progress'):
        try:
            game_state._emit(game_state.city_building_progress, building_id)
        except Exception:
            pass
    
    # Calculate remaining effort needed
    effort_required = {
        res_type: requirements.get(res_type, 0)
        for res_type in EFFORT_RESOURCES
    }
    
    return {
        "success": True,
        "building_id": building_id,
        "building_name": building_def.get("name", building_id),
        "effort_required": effort_required,
    }


def _award_completion_reward(
    adhd_buster: dict,
    reward: dict,
    game_state=None
) -> None:
    """Award coins/XP for completing a building."""
    coins = reward.get("coins", 0)
    xp = reward.get("xp", 0)
    
    if coins > 0:
        adhd_buster["coins"] = adhd_buster.get("coins", 0) + coins
    
    if xp > 0:
        if game_state and hasattr(game_state, 'add_xp'):
            game_state.add_xp(xp)
        else:
            adhd_buster["total_xp"] = adhd_buster.get("total_xp", 0) + xp


# ============================================================================
# UPGRADE SYSTEM
# ============================================================================

def can_upgrade(adhd_buster: dict, row: int, col: int) -> Tuple[bool, str]:
    """Check if a completed building can be upgraded."""
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
        return False, "Invalid coordinates"
    
    # Safe grid access - handle malformed data
    if not _is_valid_grid_cell(grid, row, col):
        return False, "Grid data corrupted"
    
    cell = grid[row][col]
    if cell is None:
        return False, "No building"
    
    if cell.get("status") != CellStatus.COMPLETE.value:
        return False, "Not complete"
    
    building_id = cell.get("building_id")
    if not building_id:
        return False, "Cell has no building"
    
    building_def = CITY_BUILDINGS.get(building_id, {})
    max_level = building_def.get("max_level", 1)
    current_level = cell.get("level", 1)
    
    if current_level >= max_level:
        return False, f"Max level ({max_level}) reached"
    
    # Check if another building is already under construction
    active = get_active_construction(adhd_buster)
    if active is not None:
        active_row, active_col = active
        active_cell = grid[active_row][active_col]
        active_name = CITY_BUILDINGS.get(active_cell.get("building_id"), {}).get("name", "Unknown")
        return False, f"Already building: {active_name}"
    
    return True, f"Can upgrade to L{current_level + 1}"


def can_initiate_upgrade(adhd_buster: dict, row: int, col: int) -> Tuple[bool, str]:
    """
    Check if a completed building can be upgraded with current resources.
    
    Requirements:
    1. Building must be COMPLETE
    2. Not at max level
    3. No other building under construction
    4. Sufficient stockpile resources (water + materials) for next level
    
    Returns (can_initiate, reason).
    """
    can, reason = can_upgrade(adhd_buster, row, col)
    if not can:
        return can, reason
    
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    cell = grid[row][col]
    
    building_id = cell.get("building_id")
    building_def = CITY_BUILDINGS.get(building_id, {})
    current_level = cell.get("level", 1)
    next_level = current_level + 1
    
    # Calculate requirements for NEXT level
    requirements = get_level_requirements(building_def, next_level)
    resources = city.get("resources", {})
    
    # Check stockpile resources (water + materials)
    for res_type in STOCKPILE_RESOURCES:
        needed = requirements.get(res_type, 0)
        have = resources.get(res_type, 0)
        if have < needed:
            return False, f"Need {needed} {res_type}, have {have}"
    
    return True, f"Ready to upgrade to L{next_level}"


def initiate_upgrade(
    adhd_buster: dict,
    row: int,
    col: int,
    game_state=None
) -> dict:
    """
    Initiate upgrade on a COMPLETE building.
    
    Two-phase upgrade flow (same as construction):
    1. Consumes water + materials from inventory (upfront payment)
    2. Increments target level, transitions building COMPLETE → BUILDING
    3. Sets this building as active_construction
    4. From now on, all activity + focus earned flows to this building
    
    Args:
        adhd_buster: Player data
        row, col: Grid coordinates of COMPLETE building
        game_state: Optional for signals
    
    Returns:
        {
            "success": bool,
            "error": str (if failed),
            "building_id": str,
            "building_name": str,
            "new_level": int,
            "effort_required": {"activity": int, "focus": int},
        }
    """
    can, reason = can_initiate_upgrade(adhd_buster, row, col)
    if not can:
        return {"success": False, "error": reason}
    
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    cell = grid[row][col]
    
    building_id = cell.get("building_id")
    building_def = CITY_BUILDINGS.get(building_id, {})
    current_level = cell.get("level", 1)
    next_level = current_level + 1
    
    # Calculate requirements for next level
    requirements = get_level_requirements(building_def, next_level)
    resources = city.get("resources", {})
    
    # Initialize construction progress
    progress = {}
    
    # Consume stockpile resources (water + materials)
    for res_type in STOCKPILE_RESOURCES:
        needed = requirements.get(res_type, 0)
        resources[res_type] = resources.get(res_type, 0) - needed
        progress[res_type] = needed  # Mark as fully invested
    
    # Initialize effort resource progress to 0
    for res_type in EFFORT_RESOURCES:
        progress[res_type] = 0
    
    # Increment level and transition to BUILDING status
    cell["level"] = next_level
    cell["status"] = CellStatus.BUILDING.value
    cell["construction_progress"] = progress
    cell["completed_at"] = None
    
    # Set as active construction
    city["active_construction"] = [row, col]
    
    _logger.info(f"Initiated upgrade of {building_id} to L{next_level} at ({row}, {col})")
    
    # Emit construction started signal
    if game_state and hasattr(game_state, 'city_building_progress'):
        try:
            game_state._emit(game_state.city_building_progress, building_id)
        except Exception:
            pass
    
    # Calculate remaining effort needed
    effort_required = {
        res_type: requirements.get(res_type, 0)
        for res_type in EFFORT_RESOURCES
    }
    
    return {
        "success": True,
        "building_id": building_id,
        "building_name": building_def.get("name", building_id),
        "new_level": next_level,
        "effort_required": effort_required,
    }


def start_upgrade(adhd_buster: dict, row: int, col: int) -> bool:
    """
    DEPRECATED: Use initiate_upgrade() for the proper two-phase flow.
    
    This function is kept for backward compatibility but now delegates
    to initiate_upgrade().
    """
    result = initiate_upgrade(adhd_buster, row, col)
    return result.get("success", False)


# ============================================================================
# PASSIVE INCOME
# ============================================================================

def collect_city_income(adhd_buster: dict, game_state=None) -> dict:
    """
    Collect passive income from all completed buildings.
    
    Uses UNIFIED income model: effect.coins_per_hour * hours_elapsed
    
    Returns:
        {
            "coins": int,
            "breakdown": [{building, rate, coins}],
            "hours_elapsed": float,
        }
    """
    city = get_city_data(adhd_buster)
    
    last_collection_str = city.get(
        "last_collection_time",
        datetime.now().isoformat()
    )
    
    try:
        last_collection = datetime.fromisoformat(last_collection_str)
    except (ValueError, TypeError):
        last_collection = datetime.now()
    
    now = datetime.now()
    hours_elapsed = (now - last_collection).total_seconds() / 3600
    
    # Cap at configurable limit
    hours_elapsed = min(hours_elapsed, MAX_OFFLINE_HOURS)
    
    total_coins = 0
    breakdown = []
    
    # Scan grid for completed buildings with passive income
    grid = city.get("grid", [])
    for row in grid:
        for cell in row:
            if cell is None:
                continue
            if cell.get("status") != CellStatus.COMPLETE.value:
                continue
            
            building_def = CITY_BUILDINGS.get(cell.get("building_id"), {})
            effect = building_def.get("effect", {})
            
            # Calculate coins per hour for this building
            coins_rate = 0
            
            if effect.get("type") == "passive_income":
                level = cell.get("level", 1)
                base_rate = effect.get("coins_per_hour", 0)
                scaling = building_def.get("level_scaling", {}).get("coins_per_hour", 0)
                coins_rate = base_rate + (level - 1) * scaling
            
            elif effect.get("type") == "multi":
                # Wonder has coins_per_hour in bonuses
                coins_rate = effect.get("bonuses", {}).get("coins_per_hour", 0)
            
            if coins_rate > 0:
                amount = int(coins_rate * hours_elapsed)
                if amount > 0:
                    total_coins += amount
                    breakdown.append({
                        "building": building_def.get("name", "Unknown"),
                        "rate": coins_rate,
                        "coins": amount,
                    })
    
    # Update collection time
    city["last_collection_time"] = now.isoformat()
    city["total_coins_generated"] = city.get("total_coins_generated", 0) + total_coins
    
    # Award coins to player
    if total_coins > 0:
        adhd_buster["coins"] = adhd_buster.get("coins", 0) + total_coins
        
        if game_state and hasattr(game_state, 'city_income_collected'):
            try:
                game_state._emit(
                    game_state.city_income_collected,
                    {"coins": total_coins}
                )
            except Exception:
                pass
    
    return {
        "coins": total_coins,
        "breakdown": breakdown,
        "hours_elapsed": hours_elapsed,
    }


# Intensity levels that qualify for Goldmine income (moderate and above)
QUALIFYING_INTENSITIES = {"moderate", "vigorous", "intense"}


def award_focus_session_income(
    adhd_buster: dict,
    session_minutes: int,
    game_state=None
) -> dict:
    """
    Award income from Royal Mint and Wonder when a focus session is completed.
    
    Args:
        adhd_buster: Player data
        session_minutes: Duration of the completed focus session in minutes
        game_state: Optional game state for signal emission
    
    Returns:
        {
            "coins": int,
            "breakdown": [{building, base_coins, time_bonus, total_coins}],
        }
    """
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    total_coins = 0
    breakdown = []
    
    # Scan grid for completed buildings that trigger on focus sessions
    for row in grid:
        for cell in row:
            if cell is None:
                continue
            if cell.get("status") != CellStatus.COMPLETE.value:
                continue
            
            building_id = cell.get("building_id")
            building_def = CITY_BUILDINGS.get(building_id, {})
            effect = building_def.get("effect", {})
            level = cell.get("level", 1)
            scaling = building_def.get("level_scaling", {})
            
            coins_earned = 0
            base_coins = 0
            time_bonus = 0
            
            # Royal Mint: focus_session_income type
            if effect.get("type") == "focus_session_income":
                
                base_coins = effect.get("base_coins", 0)
                base_coins += (level - 1) * scaling.get("base_coins", 0)
                
                coins_per_30min = effect.get("coins_per_30min", 0)
                coins_per_30min += (level - 1) * scaling.get("coins_per_30min", 0)
                
                time_bonus = int((session_minutes / 30) * coins_per_30min)
                coins_earned = base_coins + time_bonus
                
            # Wonder: multi effect with focus_session_coins bonus
            elif effect.get("type") == "multi":
                bonus_coins = effect.get("bonuses", {}).get("focus_session_coins", 0)
                if bonus_coins > 0:
                    base_coins = bonus_coins
                    time_bonus = int((session_minutes / 30) * (bonus_coins // 2))
                    coins_earned = base_coins + time_bonus
            
            if coins_earned > 0:
                total_coins += coins_earned
                breakdown.append({
                    "building": building_def.get("name", "Unknown"),
                    "building_id": building_id,
                    "base_coins": base_coins,
                    "time_bonus": time_bonus,
                    "total_coins": coins_earned,
                })
    
    # Award coins to player
    if total_coins > 0:
        adhd_buster["coins"] = adhd_buster.get("coins", 0) + total_coins
        
        # Track in city stats
        city["total_coins_generated"] = city.get("total_coins_generated", 0) + total_coins
        city["focus_sessions_rewarded"] = city.get("focus_sessions_rewarded", 0) + 1
        
        if game_state and hasattr(game_state, 'city_income_collected'):
            try:
                game_state._emit(
                    game_state.city_income_collected,
                    {"coins": total_coins, "source": "focus_session"}
                )
            except Exception:
                pass
    
    return {
        "coins": total_coins,
        "breakdown": breakdown,
    }


def award_exercise_income(
    adhd_buster: dict,
    duration_minutes: int,
    intensity_id: str,
    effective_minutes: float = None,
    game_state=None
) -> dict:
    """
    Award income from Goldmine and Wonder when exercise is logged.
    
    Only awards coins if intensity is moderate or higher.
    
    Args:
        adhd_buster: Player data
        duration_minutes: Raw duration of the activity
        intensity_id: Intensity level (light, moderate, vigorous, intense)
        effective_minutes: Optional pre-calculated effective minutes
        game_state: Optional game state for signal emission
    
    Returns:
        {
            "coins": int,
            "breakdown": [{building, base_coins, effective_bonus, total_coins}],
            "qualified": bool,  # True if intensity was moderate+
        }
    """
    # Check if intensity qualifies
    if intensity_id not in QUALIFYING_INTENSITIES:
        return {
            "coins": 0,
            "breakdown": [],
            "qualified": False,
        }
    
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    # Use effective minutes if provided, otherwise use raw duration
    eff_mins = effective_minutes if effective_minutes is not None else duration_minutes
    
    total_coins = 0
    breakdown = []
    
    # Scan grid for completed buildings that trigger on exercise
    for row in grid:
        for cell in row:
            if cell is None:
                continue
            if cell.get("status") != CellStatus.COMPLETE.value:
                continue
            
            building_id = cell.get("building_id")
            building_def = CITY_BUILDINGS.get(building_id, {})
            effect = building_def.get("effect", {})
            level = cell.get("level", 1)
            scaling = building_def.get("level_scaling", {})
            
            coins_earned = 0
            base_coins = 0
            effective_bonus = 0
            
            # Goldmine: activity_triggered_income with trigger=exercise
            if (effect.get("type") == "activity_triggered_income" and 
                effect.get("trigger") == "exercise"):
                
                # Check minimum intensity requirement
                min_intensity = effect.get("min_intensity", "moderate")
                # All qualifying intensities meet moderate requirement
                
                base_coins = effect.get("base_coins", 0)
                base_coins += (level - 1) * scaling.get("base_coins", 0)
                
                coins_per_30min = effect.get("coins_per_effective_30min", 0)
                coins_per_30min += (level - 1) * scaling.get("coins_per_effective_30min", 0)
                
                effective_bonus = int((eff_mins / 30) * coins_per_30min)
                coins_earned = base_coins + effective_bonus
                
            # Wonder: multi effect with exercise_coins bonus
            elif effect.get("type") == "multi":
                bonus_coins = effect.get("bonuses", {}).get("exercise_coins", 0)
                if bonus_coins > 0:
                    base_coins = bonus_coins
                    effective_bonus = int((eff_mins / 30) * (bonus_coins // 2))
                    coins_earned = base_coins + effective_bonus
            
            if coins_earned > 0:
                total_coins += coins_earned
                breakdown.append({
                    "building": building_def.get("name", "Unknown"),
                    "building_id": building_id,
                    "base_coins": base_coins,
                    "effective_bonus": effective_bonus,
                    "total_coins": coins_earned,
                })
    
    # Award coins to player
    if total_coins > 0:
        adhd_buster["coins"] = adhd_buster.get("coins", 0) + total_coins
        
        # Track in city stats
        city["total_coins_generated"] = city.get("total_coins_generated", 0) + total_coins
        city["exercises_rewarded"] = city.get("exercises_rewarded", 0) + 1
        
        if game_state and hasattr(game_state, 'city_income_collected'):
            try:
                game_state._emit(
                    game_state.city_income_collected,
                    {"coins": total_coins, "source": "exercise"}
                )
            except Exception:
                pass
    
    return {
        "coins": total_coins,
        "breakdown": breakdown,
        "qualified": True,
    }


def get_pending_income(adhd_buster: dict) -> dict:
    """
    Preview pending income WITHOUT collecting (read-only).
    
    Use this for UI display: "Collect 45 Coins" button label.
    Does NOT mutate last_collection_time.
    """
    city = get_city_data(adhd_buster)
    
    last_collection_str = city.get(
        "last_collection_time",
        datetime.now().isoformat()
    )
    
    try:
        last_collection = datetime.fromisoformat(last_collection_str)
    except (ValueError, TypeError):
        last_collection = datetime.now()
    
    now = datetime.now()
    hours_elapsed = (now - last_collection).total_seconds() / 3600
    hours_elapsed = min(hours_elapsed, MAX_OFFLINE_HOURS)
    
    total_coins = 0
    
    grid = city.get("grid", [])
    for row in grid:
        for cell in row:
            if cell is None:
                continue
            if cell.get("status") != CellStatus.COMPLETE.value:
                continue
            
            building_def = CITY_BUILDINGS.get(cell.get("building_id"), {})
            effect = building_def.get("effect", {})
            
            coins_rate = 0
            if effect.get("type") == "passive_income":
                level = cell.get("level", 1)
                base_rate = effect.get("coins_per_hour", 0)
                scaling = building_def.get("level_scaling", {}).get("coins_per_hour", 0)
                coins_rate = base_rate + (level - 1) * scaling
            elif effect.get("type") == "multi":
                coins_rate = effect.get("bonuses", {}).get("coins_per_hour", 0)
            
            if coins_rate > 0:
                total_coins += int(coins_rate * hours_elapsed)
    
    return {
        "coins": total_coins,
        "hours_elapsed": hours_elapsed,
    }


# ============================================================================
# BONUS CALCULATION
# ============================================================================

def get_city_bonuses(adhd_buster: dict) -> dict:
    """
    Calculate total bonuses from all completed city buildings.
    
    CRITICAL: Scans GRID (source of truth), not a separate buildings dict.
    
    Returns:
        dict: {
            "coins_per_hour": int,  # Legacy, may be 0 if no passive_income buildings
            "focus_session_coins": int,  # Coins per focus session (Royal Mint)
            "exercise_coins": int,  # Coins per qualifying exercise (Goldmine)
            "merge_success_bonus": int,
            "rarity_bias_bonus": int,
            "entity_catch_bonus": int,
            "entity_encounter_bonus": int,
            "power_bonus": int,
            "xp_bonus": int,
            "coin_discount": int,
        }
    """
    bonuses = {
        "coins_per_hour": 0,
        "focus_session_coins": 0,
        "exercise_coins": 0,
        "merge_success_bonus": 0,
        "scrap_chance_bonus": 0,  # Bonus chance for scrap from merges (Forge)
        "rarity_bias_bonus": 0,
        "entity_catch_bonus": 0,
        "entity_encounter_bonus": 0,
        "power_bonus": 0,
        "xp_bonus": 0,
        "coin_discount": 0,
    }
    
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    # Scan grid for completed buildings
    for row in grid:
        for cell in row:
            if cell is None:
                continue
            if cell.get("status") != CellStatus.COMPLETE.value:
                continue
            
            building_id = cell.get("building_id")
            building_def = CITY_BUILDINGS.get(building_id)
            if not building_def:
                continue
            
            level = cell.get("level", 1)
            effect = building_def.get("effect", {})
            scaling = building_def.get("level_scaling", {})
            
            effect_type = effect.get("type")
            
            if effect_type == "passive_income":
                base = effect.get("coins_per_hour", 0)
                per_level = scaling.get("coins_per_hour", 0)
                bonuses["coins_per_hour"] += base + (level - 1) * per_level
            
            elif effect_type == "activity_triggered_income":
                # Calculate the base coins for display purposes
                trigger = effect.get("trigger")
                if trigger == "exercise":
                    base = effect.get("base_coins", 0)
                    per_level = scaling.get("base_coins", 0)
                    bonuses["exercise_coins"] += base + (level - 1) * per_level
                    
            elif effect_type == "focus_session_income":
                # Focus session triggered income (Royal Mint)
                base = effect.get("base_coins", 0)
                per_level = scaling.get("base_coins", 0)
                bonuses["focus_session_coins"] += base + (level - 1) * per_level
                
            elif effect_type == "merge_success_bonus":
                base = effect.get("bonus_percent", 0)
                per_level = scaling.get("bonus_percent", 0)
                bonuses["merge_success_bonus"] += base + (level - 1) * per_level
                
            elif effect_type == "rarity_bias_bonus":
                base = effect.get("bonus_percent", 0)
                per_level = scaling.get("bonus_percent", 0)
                bonuses["rarity_bias_bonus"] += base + (level - 1) * per_level
                
            elif effect_type == "entity_catch_bonus":
                base = effect.get("bonus_percent", 0)
                per_level = scaling.get("bonus_percent", 0)
                bonuses["entity_catch_bonus"] += base + (level - 1) * per_level
                
            elif effect_type == "entity_encounter_bonus":
                base = effect.get("bonus_percent", 0)
                per_level = scaling.get("bonus_percent", 0)
                bonuses["entity_encounter_bonus"] += base + (level - 1) * per_level
                
            elif effect_type == "power_bonus":
                base = effect.get("power_percent", 0)
                per_level = scaling.get("power_percent", 0)
                bonuses["power_bonus"] += base + (level - 1) * per_level
                
            elif effect_type == "xp_bonus":
                base = effect.get("bonus_percent", 0)
                per_level = scaling.get("bonus_percent", 0)
                bonuses["xp_bonus"] += base + (level - 1) * per_level
                
            elif effect_type == "coin_discount":
                base = effect.get("discount_percent", 0)
                per_level = scaling.get("discount_percent", 0)
                bonuses["coin_discount"] += base + (level - 1) * per_level
            
            elif effect_type == "multi":
                # Multi-effect buildings (Forge, Wonder) - adds multiple bonuses with level scaling
                for bonus_key, base_value in effect.get("bonuses", {}).items():
                    if bonus_key in bonuses:
                        per_level = scaling.get(bonus_key, 0)
                        bonuses[bonus_key] += base_value + (level - 1) * per_level
    
    # Apply entity synergy bonuses on top of building bonuses
    try:
        from .city_synergies import get_all_synergy_bonuses
        synergy_bonuses = get_all_synergy_bonuses(adhd_buster)
        
        # synergy_value is 0.0-0.5 (representing 0%-50% bonus multiplier)
        # bonuses[key] is the base percentage (e.g., 10 means 10%)
        # Result: 10 * (1 + 0.25) = 12 → 12% total bonus
        for key, synergy_value in synergy_bonuses.items():
            if key in bonuses and synergy_value > 0:
                bonuses[key] = int(bonuses[key] * (1 + synergy_value))
    except ImportError:
        # Synergy module not yet created
        pass
    except Exception as e:
        _logger.debug(f"Error applying synergy bonuses: {e}")
    
    return bonuses
