"""
City Building System - Constants
================================
Centralized configuration values for the city system.
"""

from typing import List

# ============================================================================
# RESOURCE SYSTEM
# ============================================================================

# All resource types used in construction
RESOURCE_TYPES: List[str] = ["water", "materials", "activity", "focus"]

# STOCKPILE RESOURCES: Can be accumulated and spent later
# Water = hydration, Materials = weight management
STOCKPILE_RESOURCES: List[str] = ["water", "materials"]

# EFFORT RESOURCES: Cannot be accumulated - flow directly to active construction
# Activity = physical activity, Focus = focus sessions
# These represent REAL-TIME EFFORT the user puts into building
EFFORT_RESOURCES: List[str] = ["activity", "focus"]

RESOURCE_EMOJI = {
    "water": "💧",
    "materials": "🧱",
    "activity": "🏃",
    "focus": "🎯",
}

# ============================================================================
# OFFLINE INCOME
# ============================================================================

# Maximum hours of offline income that can accumulate
# Can be extended by future buildings (e.g., Warehouse)
MAX_OFFLINE_HOURS = 24

# ============================================================================
# BUILDING SLOTS (Level-Gated)
# ============================================================================

# Slot unlock progression: level threshold → max buildings allowed
# Players can build ANY building type, but limited by slot count
# User starts with 0 lots, first unlocks at level 2
BUILDING_SLOT_UNLOCKS = {
    1: 0,    # Level 1: No lots available (starter)
    2: 1,    # Level 2: 1st lot unlocked
    4: 2,    # Level 4: 2nd lot unlocked
    6: 3,    # Level 6: 3rd lot unlocked
    9: 4,    # Level 9: 4th lot unlocked
    13: 5,   # Level 13: 5th lot unlocked
    18: 6,   # Level 18: 6th lot unlocked
    24: 7,   # Level 24: 7th lot unlocked
    31: 8,   # Level 31: 8th lot unlocked
    39: 9,   # Level 39: 9th lot unlocked
    40: 10,  # Level 40: All 10 lots unlocked
}

# ============================================================================
# GRID CONFIGURATION
# ============================================================================

# Simple horizontal layout: 1 row x 10 columns = 10 building slots
GRID_ROWS = 1
GRID_COLS = 10
TOTAL_CELLS = GRID_ROWS * GRID_COLS  # 10 cells

# ============================================================================
# UPGRADE SCALING
# ============================================================================

# Each level costs 20% more resources than the previous
UPGRADE_COST_MULTIPLIER = 1.2

# ============================================================================
# DEMOLISH REFUND
# ============================================================================

# Percentage of invested resources returned on demolish
DEMOLISH_REFUND_PERCENT = 25

# ============================================================================
# UI CONSTANTS
# ============================================================================

# Cell size in pixels
CELL_SIZE = 96

# Animation frame budget (milliseconds)
ANIMATION_FRAME_BUDGET_MS = 16  # ~60 FPS

# SVG cache size
SVG_CACHE_MAX_SIZE = 50
