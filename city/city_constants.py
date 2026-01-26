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
BUILDING_SLOT_UNLOCKS = {
    1: 2,    # Levels 1-4: 2 slots (starter)
    5: 3,    # Levels 5-9: 3 slots
    10: 4,   # Levels 10-14: 4 slots
    15: 5,   # Levels 15-19: 5 slots
    20: 6,   # Levels 20-24: 6 slots
    25: 7,   # Levels 25-29: 7 slots
    30: 8,   # Levels 30-34: 8 slots
    35: 9,   # Levels 35-39: 9 slots
    40: 10,  # Level 40+: All 10 buildings
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
