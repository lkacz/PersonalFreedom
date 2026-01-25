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
    max_slots = 2  # Default for level 1
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


# ============================================================================
# RESOURCE MANAGEMENT
# ============================================================================

def add_city_resource(
    adhd_buster: dict,
    resource_type: str,
    amount: int,
    game_state=None
) -> int:
    """
    Add resources to city inventory.
    
    Called by activity hooks (water, weight, activity, focus tabs).
    
    Args:
        adhd_buster: Player data dict
        resource_type: One of RESOURCE_TYPES
        amount: Amount to add
        game_state: Optional GameStateManager for signal emission
    
    Returns:
        New total for that resource
    """
    if resource_type not in RESOURCE_TYPES:
        _logger.warning(f"Invalid resource type: {resource_type}")
        return 0
    
    city = get_city_data(adhd_buster)
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
    Invest resources into a building's construction.
    
    Automatically transitions PLACED → BUILDING on first investment.
    
    Args:
        adhd_buster: Player data
        row, col: Grid coordinates
        resources_to_invest: {resource_type: amount} to invest
        game_state: Optional for batch mode and signals
    
    Returns:
        {
            "success": bool,
            "invested": {resource: amount_actually_invested},
            "remaining_needs": {resource: still_needed},
            "completed": bool,
            "error": str (if failed),
        }
    """
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
        return {"success": False, "error": "Invalid coordinates"}
    
    # Safe grid access - handle malformed data
    if not _is_valid_grid_cell(grid, row, col):
        return {"success": False, "error": "Grid data corrupted"}
    
    cell = grid[row][col]
    if cell is None:
        return {"success": False, "error": "No building at this location"}
    
    if cell.get("status") == CellStatus.COMPLETE.value:
        return {"success": False, "error": "Already complete"}
    
    # Use batch mode if game_state provided (single save at end)
    if game_state and hasattr(game_state, 'begin_batch'):
        game_state.begin_batch()
    
    try:
        # Auto-transition PLACED → BUILDING on first investment
        if cell.get("status") == CellStatus.PLACED.value:
            cell["status"] = CellStatus.BUILDING.value
        
        building_id = cell.get("building_id")
        if not building_id:
            return {"success": False, "error": "Cell has no building"}
        
        building_def = CITY_BUILDINGS.get(building_id, {})
        level = cell.get("level", 1)
        requirements = get_level_requirements(building_def, level)
        progress = cell.get("construction_progress", {})
        available = city.get("resources", {})
        
        invested = {}
        
        for resource, amount in resources_to_invest.items():
            if resource not in RESOURCE_TYPES:
                continue
            
            needed = requirements.get(resource, 0) - progress.get(resource, 0)
            have = available.get(resource, 0)
            to_invest = min(amount, needed, have)
            
            if to_invest > 0:
                available[resource] = have - to_invest
                progress[resource] = progress.get(resource, 0) + to_invest
                invested[resource] = to_invest
        
        cell["construction_progress"] = progress
        
        # Check if level is now complete
        completed = all(
            progress.get(r, 0) >= requirements.get(r, 0)
            for r in RESOURCE_TYPES
        )
        
        if completed:
            cell["status"] = CellStatus.COMPLETE.value
            cell["completed_at"] = datetime.now().isoformat()
            
            # Award completion reward
            reward = building_def.get("completion_reward", {})
            if reward:
                _award_completion_reward(adhd_buster, reward, game_state)
            
            # Emit building completed signal
            if game_state and hasattr(game_state, 'city_building_completed'):
                try:
                    game_state._emit(
                        game_state.city_building_completed,
                        building_id
                    )
                except Exception:
                    pass
        else:
            # Emit progress signal
            if game_state and hasattr(game_state, 'city_building_progress'):
                try:
                    game_state._emit(
                        game_state.city_building_progress,
                        building_id
                    )
                except Exception:
                    pass
        
        remaining = {
            r: max(0, requirements.get(r, 0) - progress.get(r, 0))
            for r in RESOURCE_TYPES
        }
        
        return {
            "success": True,
            "invested": invested,
            "remaining_needs": remaining,
            "completed": completed,
        }
    
    finally:
        if game_state and hasattr(game_state, 'end_batch'):
            game_state.end_batch()


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
    
    return True, f"Can upgrade to L{current_level + 1}"


def start_upgrade(adhd_buster: dict, row: int, col: int) -> bool:
    """Start upgrading a completed building to the next level."""
    can, _ = can_upgrade(adhd_buster, row, col)
    if not can:
        return False
    
    city = get_city_data(adhd_buster)
    grid = city.get("grid", [])
    
    # Safe grid access - handle malformed data
    if not _is_valid_grid_cell(grid, row, col):
        return False
    
    cell = grid[row][col]
    if cell is None:
        return False
    
    # Increment target level, reset progress, change status
    cell["level"] = cell.get("level", 1) + 1
    cell["status"] = CellStatus.BUILDING.value
    cell["construction_progress"] = {r: 0 for r in RESOURCE_TYPES}
    cell["completed_at"] = None
    
    return True


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
            "coins_per_hour": int,
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
        "merge_success_bonus": 0,
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
                # Wonder - adds multiple bonuses
                for bonus_key, value in effect.get("bonuses", {}).items():
                    if bonus_key in bonuses:
                        bonuses[bonus_key] += value
    
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
