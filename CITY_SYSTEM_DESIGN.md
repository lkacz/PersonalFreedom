# City Building System - Design & Integration Outline

## Executive Summary

The City system is a **passive income generator** where users invest resources earned through healthy activities (hydration, weight management, physical activity, focus sessions) to construct buildings that produce Coins and XP over time. Like the Entitidex, the City persists across all story themes.

**Key Features:**
- **Level-Gated Building Slots**: Player XP level determines how many buildings can be placed (not which types)
- **Entity-Building Synergy**: Collected entities with thematic connections boost specific buildings
- **Starter Buildings**: Goldmine and Forge available immediately at Level 1

---

## 1. Core Concepts

### 1.1 Resource System

**Resource Categories:**

There are now TWO distinct types of resources in the city system:

| Category | Resources | Behavior |
|----------|-----------|----------|
| **STOCKPILE** | Water 💧, Materials 🧱 | Accumulate in city reserves. Spent upfront to START construction. |
| **EFFORT** | Activity 🏃, Focus 🎯 | Do NOT accumulate. Flow directly to the active construction. |

**Resource Details:**

| Resource | Emoji | Earned By | Generation Rate |
|----------|-------|-----------|-----------------|
| **WATER** | 💧 | Drinking water (hydration log) | +1 per glass logged |
| **MATERIALS** | 🧱 | Weight management | See below |
| **ACTIVITY** | 🏃 | Physical activity log | +1 per activity logged, duration bonus |
| **FOCUS** | 🎯 | Focus sessions | +1 per 30 min focused |

**Materials Generation (Weight Logging):**

All weight goals reward the same amount when achieved - this ensures fairness regardless of your health journey:

| Your Goal | Achievement Criteria | Reward |
|-----------|---------------------|--------|
| 📉 **Lose weight** (overweight) | Log weight lower than previous | +2 MATERIALS |
| 📈 **Gain weight** (underweight) | Log weight higher than previous | +2 MATERIALS |
| ⚖️ **Maintain weight** (healthy BMI) | Stay within BMI 18.5-25.0 | +2 MATERIALS |
| ❌ Off-target | Weight logged but not meeting goal | +0 MATERIALS |

**Key Points:**
- You must **log your weight daily** in the Body tab to earn materials
- The system automatically detects your goal based on your BMI and settings
- All three positive outcomes reward equally (+2 materials each)
- **Maintain goal only works if you're in the healthy BMI range (18.5-25)**
- Consistency is key: daily logging = daily materials!

### 1.1.1 Construction Flow (Two-Phase Model)

**Phase 1: Initiate Construction (Upfront Payment)**
- User selects a PLACED building
- User pays STOCKPILE resources (Water + Materials) upfront
- If sufficient resources: Building enters BUILDING status
- Building becomes the "active construction"
- **Only ONE building can be under active construction at a time**

**Phase 2: Complete Construction (Effort Over Time)**
- User earns Activity and Focus through daily habits
- EFFORT resources automatically flow to the active construction
- No manual investment needed - just keep up healthy habits!
- When effort requirements are met: Building auto-completes
- Building enters COMPLETE status, clears active construction slot

**Why This Design:**
- **Stockpile (Water/Materials)**: Represents planning and preparation
- **Effort (Activity/Focus)**: Represents ongoing commitment and work
- **Single Active Build**: Focuses player attention, prevents spreading thin
- **Auto-Flow**: Rewards consistent healthy behavior, reduces micro-management

```
┌─────────────────────────────────────────────────────────────┐
│                    CONSTRUCTION FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. PLACED (Blueprint selected)                             │
│     ↓                                                       │
│     └─ User clicks "Start Construction"                     │
│        └─ Pays Water + Materials (stockpile)                │
│                                                             │
│  2. BUILDING (Active construction - only 1 at a time)       │
│     ↓                                                       │
│     └─ User earns Activity + Focus (effort)                 │
│        └─ Automatically contributes to building             │
│                                                             │
│  3. COMPLETE (Generating bonuses)                           │
│     ↓                                                       │
│     └─ Coins + effects active                               │
│        └─ Can now start another construction                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Building System

Buildings have:
- **Grid Placement**: Each building occupies one cell in a 1×10 horizontal grid (10 slots)
- **Independence**: All buildings are independently constructable (no prerequisites)
- **Construction Requirements**: Resources needed to complete
- **Construction Progress**: Tracked per-resource, visually shown as building emerges
- **Completion Reward**: One-time bonus on finishing
- **Gameplay Effect**: Ongoing bonuses (coins, stats, luck)

### 1.3 Grid Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                          YOUR CITY (1×10 Horizontal Grid)                                       │
├───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬─────┤
│   Slot 1  │   Slot 2  │   Slot 3  │   Slot 4  │   Slot 5  │   Slot 6  │   Slot 7  │   Slot 8  │   Slot 9  │ 10  │
│  ⛏️ Mine  │  🔥 Forge │  🎨 Guild │  [Empty]  │  [Locked] │  [Locked] │  [Locked] │  [Locked] │  [Locked] │ 🔒  │
│  L3 ✓     │  L1 75%   │  [Placed] │           │   Lv 9    │   Lv 13   │   Lv 18   │   Lv 24   │   Lv 31   │ 39  │
└───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴─────┘

Cell States:
  [Empty]   = Unlocked slot, no building (can place any building type)
  [Locked]  = Slot not yet unlocked (shows required level)
  [Placed]  = Building placed, awaiting upfront payment (Water + Materials)
  L1 75%    = Under active construction, level 1 target, 75% effort complete
  L3 ✓      = Completed at level 3, generating bonuses

Construction Notes:
- PLACED → BUILDING: User pays Water + Materials upfront
- BUILDING → COMPLETE: Activity + Focus auto-flow until requirements met
- Only ONE building can be in BUILDING status at a time (active construction)
- Player XP level determines available slots, not building types
- Locked slots are HIDDEN in the UI until unlocked by leveling up
```

**Key Grid Concepts:**
- **10 unique buildings** can be placed in **10 building slots** (1:1 ratio when fully unlocked)
- **Building slots unlock progressively with XP level** (see Section 1.4)
- **Locked slots are hidden** until the player reaches the required level
- **Each building can only be built once** (no duplicates)
- **Player chooses WHERE to place** - purely cosmetic, no adjacency bonuses
- **Any building type** can be built in any unlocked slot
- **Entity synergies** boost building effectiveness (see Section 1.5)

### 1.4 Level-Gated Building Slots

**Philosophy:** XP level determines HOW MANY buildings you can have, not WHICH types.
This gives players a clear reason to level up - each milestone unlocks a new building slot.

| Player Level | Building Slots | Unlocked At | Notes |
|--------------|----------------|-------------|-------|
| 1 | 0 | - | City unlocked but no slots yet (motivation to level up!) |
| 2 | 1 | Level 2 | First slot - player chooses their first building |
| 4 | 2 | Level 4 | Second slot unlocked |
| 6 | 3 | Level 6 | Third slot unlocked |
| 9 | 4 | Level 9 | Fourth slot unlocked |
| 13 | 5 | Level 13 | Fifth slot (halfway to max!) |
| 18 | 6 | Level 18 | Sixth slot unlocked |
| 24 | 7 | Level 24 | Seventh slot unlocked |
| 31 | 8 | Level 31 | Eighth slot unlocked |
| 39 | 9 | Level 39 | Ninth slot unlocked |
| 40 | 10 | Level 40 | ALL 10 SLOTS UNLOCKED! Full city available |

**Design Rationale:**
- **Level 1 = 0 slots**: City tab is visible but locked slots create anticipation
- **Level 2 = First slot**: Quick early reward for engagement
- **Accelerating gaps**: Early unlocks are fast (2→4→6), later ones are spaced (31→39→40)
- **No type restrictions**: Players choose WHICH buildings based on strategy
- **Level 40 milestone**: All 10 buildings at max level = fully built city

```python
# In city/city_constants.py

# Slot unlock progression (level → max_buildings)
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

def get_max_building_slots(player_level: int) -> int:
    """
    Get maximum building slots available at given player level.
    
    Returns number of buildings the player can have placed.
    """
    max_slots = 0  # Default for level 1
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
    player_level = get_level_from_xp(total_xp)[0]  # Returns (level, xp_in_level, xp_needed, progress)
    
    max_slots = get_max_building_slots(player_level)
    current_buildings = len(get_placed_buildings(adhd_buster))
    
    return max(0, max_slots - current_buildings)


def get_next_slot_unlock(adhd_buster: dict) -> dict:
    """
    Get info about next slot unlock for UI display.
    
    Returns: {"current_slots": int, "next_unlock_level": int, "slots_after": int}
    """
    from gamification import get_level_from_xp
    
    total_xp = adhd_buster.get("total_xp", 0)
    player_level = get_level_from_xp(total_xp)[0]  # Returns (level, xp_in_level, xp_needed, progress)
    
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
```

**UI Display:**
```
┌─────────────────────────────────────────────────────────────┐
│  🏙️ Your City                        🏠 3/4 Buildings      │
│                                       Next slot at Level 9  │
│                                                             │
│  ℹ️ Only unlocked slots are shown in the grid.              │
│     Locked slots appear as you level up!                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.5 Entity-Building Synergy System

**Philosophy:** Collected entities with thematic connections boost specific buildings.
This creates a satisfying loop: collect entities → boost buildings → get better rewards.

**Synergy Categories:**

| Building | Synergy Theme | Example Entities | Bonus Type |
|----------|---------------|------------------|------------|
| **Goldmine** | Mining, Earth, Treasure | Dwarf, Dragon (hoard), Mole | +% coins/hour |
| **Forge** | Fire, Crafting, Smithing | Phoenix, Salamander, Blacksmith Spirit | +% merge success |
| **Artisan Guild** | Art, Beauty, Creativity | Muse, Fairy, Unicorn | +% rarity bias |
| **University** | Knowledge, Books, Wisdom | Owl, Sphinx, Scholar Ghost, Bookworm | +% entity catch |
| **Training Ground** | Strength, Combat, Athletics | Warrior Spirit, Minotaur, Centaur | +% power bonus |
| **Library** | Reading, Lore, History | Scribe Spirit, Tome Elemental, Wise Owl | +% XP bonus |
| **Market** | Trade, Commerce, Luck | Leprechaun, Fortune Cat, Merchant Spirit | +% coin discount |
| **Royal Mint** | Wealth, Gold, Prosperity | Golden Goose, Dragon, Treasure Sprite | +% coins/hour |
| **Observatory** | Stars, Night, Vision | Owl, Star Sprite, Moon Spirit, Astronomer | +% encounter rate |
| **Wonder** | All/Legendary | Any Legendary entity | +% ALL bonuses |

**Synergy Bonus Calculation:**
- **Normal entity**: +5% bonus to matched building
- **Exceptional entity**: +10% bonus to matched building
- **Multiple matches**: Stack additively (cap at +50%)

```python
# In city/city_synergies.py

from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class SynergyMapping:
    """Maps entity tags to building bonuses."""
    building_id: str
    entity_tags: Set[str]  # Tags that trigger synergy
    bonus_type: str        # Which building effect to boost
    normal_bonus: float    # % bonus per normal entity (0.05 = 5%)
    exceptional_bonus: float  # % bonus per exceptional entity
    max_bonus: float       # Cap on total synergy bonus (0.50 = 50%)

# Synergy definitions - extensible for future entities
BUILDING_SYNERGIES: Dict[str, SynergyMapping] = {
    "goldmine": SynergyMapping(
        building_id="goldmine",
        entity_tags={"mining", "earth", "treasure", "dwarf", "dragon", "underground"},
        bonus_type="coins_per_hour",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "forge": SynergyMapping(
        building_id="forge",
        entity_tags={"fire", "crafting", "smithing", "phoenix", "salamander", "heat"},
        bonus_type="merge_success_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "artisan_guild": SynergyMapping(
        building_id="artisan_guild",
        entity_tags={"art", "beauty", "creativity", "muse", "fairy", "inspiration"},
        bonus_type="rarity_bias_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "university": SynergyMapping(
        building_id="university",
        entity_tags={"knowledge", "books", "wisdom", "owl", "scholar", "learning", "academic"},
        bonus_type="entity_catch_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "training_ground": SynergyMapping(
        building_id="training_ground",
        entity_tags={"strength", "combat", "athletics", "warrior", "physical", "muscle"},
        bonus_type="power_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "library": SynergyMapping(
        building_id="library",
        entity_tags={"reading", "lore", "history", "scribe", "tome", "ancient", "books"},
        bonus_type="xp_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "market": SynergyMapping(
        building_id="market",
        entity_tags={"trade", "commerce", "luck", "merchant", "fortune", "bargain"},
        bonus_type="coin_discount",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "royal_mint": SynergyMapping(
        building_id="royal_mint",
        entity_tags={"wealth", "gold", "prosperity", "treasure", "coins", "rich"},
        bonus_type="coins_per_hour",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "observatory": SynergyMapping(
        building_id="observatory",
        entity_tags={"stars", "night", "vision", "owl", "moon", "astronomy", "sky", "eyes"},
        bonus_type="entity_encounter_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "wonder": SynergyMapping(
        building_id="wonder",
        entity_tags={"legendary"},  # Only legendary entities boost Wonder
        bonus_type="all",  # Boosts ALL effects
        normal_bonus=0.03,
        exceptional_bonus=0.05,
        max_bonus=0.30,
    ),
}


def get_entity_synergy_tags(entity_id: str) -> Set[str]:
    """
    Get synergy tags for an entity.
    
    Reads the synergy_tags field from the Entity object.
    Falls back to keyword matching from name/lore for backward compatibility.
    """
    try:
        from entitidex.entity_pools import get_entity_by_id
        entity = get_entity_by_id(entity_id)
        if entity:
            # Uses entity.synergy_tags (FrozenSet[str])
            return set(entity.synergy_tags)
    except Exception:
        pass
    return set()


def calculate_building_synergy_bonus(
    building_id: str,
    adhd_buster: dict
) -> Dict[str, float]:
    """
    Calculate synergy bonus for a building from collected entities.
    
    Returns:
        {"bonus_type": str, "bonus_percent": float, "contributors": list}
    """
    synergy = BUILDING_SYNERGIES.get(building_id)
    if not synergy:
        return {"bonus_type": None, "bonus_percent": 0.0, "contributors": []}
    
    entitidex_data = adhd_buster.get("entitidex", {})
    collected = entitidex_data.get("collected_entity_ids", 
                entitidex_data.get("collected", set()))
    exceptional = entitidex_data.get("exceptional_entities", {})
    
    total_bonus = 0.0
    contributors = []
    
    for entity_id in collected:
        entity_tags = get_entity_synergy_tags(entity_id)
        
        # Check for tag overlap
        if entity_tags & synergy.entity_tags:
            is_exceptional = entity_id in exceptional
            bonus = synergy.exceptional_bonus if is_exceptional else synergy.normal_bonus
            total_bonus += bonus
            
            contributors.append({
                "entity_id": entity_id,
                "is_exceptional": is_exceptional,
                "bonus": bonus,
            })
    
    # Apply cap
    capped_bonus = min(total_bonus, synergy.max_bonus)
    
    return {
        "bonus_type": synergy.bonus_type,
        "bonus_percent": capped_bonus,
        "contributors": contributors,
        "capped": total_bonus > synergy.max_bonus,
    }


def get_all_synergy_bonuses(adhd_buster: dict) -> Dict[str, float]:
    """
    Get all synergy bonuses from entities for all buildings.
    
    Returns dict matching get_city_bonuses() structure, to be added on top.
    """
    synergy_bonuses = {
        "coins_per_hour": 0.0,
        "merge_success_bonus": 0.0,
        "rarity_bias_bonus": 0.0,
        "entity_catch_bonus": 0.0,
        "entity_encounter_bonus": 0.0,
        "power_bonus": 0.0,
        "xp_bonus": 0.0,
        "coin_discount": 0.0,
    }
    
    city_data = adhd_buster.get("city", {})
    grid = city_data.get("grid", [])
    
    # Only completed buildings get synergy bonuses
    for row in grid:
        for cell in row:
            if cell is None:
                continue
            if cell.get("status") != "complete":
                continue
            
            building_id = cell.get("building_id")
            synergy = calculate_building_synergy_bonus(building_id, adhd_buster)
            
            if synergy["bonus_type"] == "all":
                # Wonder: boost all bonuses
                for key in synergy_bonuses:
                    synergy_bonuses[key] += synergy["bonus_percent"]
            elif synergy["bonus_type"] in synergy_bonuses:
                synergy_bonuses[synergy["bonus_type"]] += synergy["bonus_percent"]
    
    return synergy_bonuses
```

**Entity Tag Integration (IMPLEMENTED):**

The Entity class now has a `synergy_tags` field (FrozenSet[str]) that defines which buildings the entity boosts:

```python
# In entitidex/entity.py

@dataclass
class Entity:
    id: str
    name: str
    power: int
    rarity: str
    lore: str
    theme_set: str
    # ... other fields ...
    
    # City building synergy tags (e.g., {"fire", "crafting"} boosts Forge)
    synergy_tags: FrozenSet[str] = field(default_factory=frozenset)

# Example entity definitions with synergy tags (from entity_pools.py):
{
    "id": "warrior_001",
    "name": "Hatchling Drake",
    "power": 10,
    "rarity": "common",
    "lore": "A baby dragon...",
    "synergy_tags": ["dragon", "fire", "treasure"],  # Boosts Goldmine + Forge
},
{
    "id": "scholar_002", 
    "name": "Study Owl Athena",
    "power": 50,
    "rarity": "common",
    "lore": "A wise little owl...",
    "synergy_tags": ["owl", "wisdom", "night", "vision", "knowledge"],  # Boosts University + Library + Observatory
},
```

**UI Display for Synergies:**
```
┌─────────────────────────────────────────────────────────────┐
│  🎓 University (L3 ✓)                                       │
│  Effect: +10% Entity Catch                                  │
│                                                             │
│  🔗 Entity Synergies: +15%                                  │
│     🦉 Wise Owl (+10% - Exceptional)                        │
│     👻 Scholarly Ghost (+5%)                                │
│                                                             │
│  Total Catch Bonus: +25%                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Data Structures

### 2.1 Resource State

```python
# In adhd_buster dict (persisted in config.json)
"city": {
    "resources": {
        "water": 45,      # Accumulated WATER (stockpile)
        "materials": 23,  # Accumulated MATERIALS (stockpile)
        # NOTE: activity and focus are NOT accumulated - they flow directly to construction
    },
    
    # 1x10 Grid - THE SINGLE SOURCE OF TRUTH for all building state
    # Simple horizontal layout: 1 row x 10 columns = 10 building slots
    # Use list comprehension to avoid reference bugs: [[None for _ in range(10)] for _ in range(1)]
    "grid": [
        # Row 0 (the only row - horizontal layout)
        [
            {"building_id": "goldmine", "status": "complete", "level": 3, "construction_progress": {...}},
            {"building_id": "forge", "status": "building", "level": 1, "construction_progress": {"water": 8, "materials": 15, ...}},
            {"building_id": "artisan_guild", "status": "placed", "level": 1, "construction_progress": {}},
            None,  # Empty unlocked slot
            None,  # Slot 5-10: Locked until player reaches required level (hidden in UI)
            None,
            None,
            None,
            None,
            None,
        ],
    ],
    
    # Track which building is currently under construction (only 1 at a time)
    "active_construction": [0, 1],  # [row, col] or null if none
    
    # NOTE: placed_buildings is DERIVED from grid scan, not stored separately
    # Use get_placed_buildings(grid) helper to compute on demand
    
    # Stats
    "total_coins_generated": 1250,
    "total_xp_generated": 3400,
    "last_collection_time": "2026-01-25T08:00:00",
}
```

### 2.2 Cell State Schema

```python
from enum import Enum

class CellStatus(str, Enum):
    """Explicit cell states - never infer from other fields."""
    EMPTY = "empty"       # No building (cell is None)
    PLACED = "placed"     # Building selected but construction not started
    BUILDING = "building" # Under active construction (progress > 0)
    COMPLETE = "complete" # Fully built, generating bonuses

# Each cell in the grid can be:
CellState = None | {
    "building_id": str,           # Which building ("goldmine", "forge", etc.)
    "status": str,                # CellStatus value: "placed", "building", "complete"
    "level": int,                 # Current level (1-max_level)
    "construction_progress": {    # Per-resource progress (for current level)
        "water": int,             # Amount invested
        "materials": int,
        "activity": int,
        "focus": int,
    },
    "placed_at": str | None,      # ISO timestamp when placed
    "completed_at": str | None,   # ISO timestamp when level completed
}

# Helper to derive placed buildings from grid (replaces stored list)
def get_placed_buildings(grid: list) -> list[str]:
    """Scan grid to get list of placed building IDs."""
    return [
        cell["building_id"]
        for row in grid
        for cell in row
        if cell is not None
    ]
```

### 2.3 Building Definitions

```python
# city_buildings.py - Building Configuration

CITY_BUILDINGS = {
    # =========================================================================
    # TIER 1 - STARTER BUILDINGS (Immediately available, low requirements)
    # =========================================================================
    "goldmine": {
        "id": "goldmine",
        "name": "⛏️ Goldmine",
        "description": "Strike gold! Generates passive income over time.",
        "tier": 1,
        "requirements": {
            "water": 3,
            "materials": 5,
            "activity": 0,
            "focus": 2,
        },
        # No prerequisites - all buildings are independent
        "completion_reward": {"coins": 50, "xp": 25},
        "effect": {
            "type": "passive_income",
            "coins_per_hour": 1,  # +1 coin/hour = 24 coins/day
        },
        "max_level": 5,
        "level_scaling": {
            "coins_per_hour": 0.5,  # +0.5/hour per level (L5 = 3 coins/hour = 72/day)
        },
        "visual": "goldmine",
    },
    
    # =========================================================================
    # TIER 2 - GAMEPLAY MODIFIER BUILDINGS (Core bonuses, moderate requirements)
    # =========================================================================
    "forge": {
        "id": "forge",
        "name": "🔥 Forge",
        "description": "Master smiths improve your merge outcomes.",
        "tier": 2,
        "requirements": {
            "water": 10,
            "materials": 20,
            "activity": 10,
            "focus": 10,
        },
        # No prerequisites - build in any order
        "completion_reward": {"coins": 100, "xp": 150},
        "effect": {
            "type": "merge_success_bonus",
            "bonus_percent": 5,  # +5% merge success rate
        },
        "max_level": 3,
        "level_scaling": {
            "bonus_percent": 5,  # +5% per level (L3 = +15% total)
        },
        "visual": "forge",
        # Integration note: Hooks into calculate_merge_success_rate()
        # Current base is ~25%, so +15% is significant but not OP
    },
    
    "artisan_guild": {
        "id": "artisan_guild",
        "name": "🎨 Artisan Guild",
        "description": "Master craftsmen produce higher quality items.",
        "tier": 2,
        "requirements": {
            "water": 15,
            "materials": 15,
            "activity": 5,
            "focus": 15,
        },
        # No prerequisites - build in any order
        "completion_reward": {"coins": 75, "xp": 200},
        "effect": {
            "type": "rarity_bias_bonus",
            "bonus_percent": 3,  # +3% chance for higher rarity items
        },
        "max_level": 5,
        "level_scaling": {
            "bonus_percent": 2,  # +2% per level (L5 = +11% total rarity bias)
        },
        "visual": "artisan_guild",
        # Integration note: Adds to existing rarity_bias perk system
        # Affects all item drops (focus, hydration, weight, activity rewards)
    },
    
    "university": {
        "id": "university",
        "name": "🎓 University",
        "description": "Scholars study entity behavior, improving your catch rate.",
        "tier": 2,
        "requirements": {
            "water": 15,
            "materials": 10,
            "activity": 5,
            "focus": 25,  # Knowledge requires focus
        },
        # No prerequisites - build in any order
        "completion_reward": {"coins": 50, "xp": 300},
        "effect": {
            "type": "entity_catch_bonus",
            "bonus_percent": 2,  # +2% entity catch probability
        },
        "max_level": 5,
        "level_scaling": {
            "bonus_percent": 2,  # +2% per level (L5 = +10% total catch bonus)
        },
        "visual": "university",
        # Integration note: New city bonus path, separate from item luck
        # Current max_luck_bonus from items is +15%, this adds another vector
        # Hooks into get_final_probability() via new city_bonuses parameter
    },
    
    # =========================================================================
    # TIER 3 - ADVANCED BUILDINGS (Significant bonuses, higher requirements)
    # =========================================================================
    "training_ground": {
        "id": "training_ground",
        "name": "🏋️ Training Ground",
        "description": "Physical training grants hero power bonus.",
        "tier": 3,
        "requirements": {
            "water": 25,
            "materials": 20,
            "activity": 40,  # Heavy activity requirement
            "focus": 15,
        },
        # No prerequisites - build in any order
        "completion_reward": {"coins": 150, "xp": 400},
        "effect": {
            "type": "power_bonus",
            "power_percent": 3,  # +3% hero power
        },
        "max_level": 5,
        "level_scaling": {
            "power_percent": 2,  # +2% per level (L5 = +11% hero power)
        },
        "visual": "training_ground",
        # Integration note: Hooks into calculate_character_power()
        # Multiplicative bonus on final power calculation
    },
    
    "library": {
        "id": "library",
        "name": "📚 Library",
        "description": "Ancient tomes reveal knowledge. Bonus XP from all activities.",
        "tier": 3,
        "requirements": {
            "water": 20,
            "materials": 30,
            "activity": 10,
            "focus": 50,  # Heavy focus requirement
        },
        # No prerequisites - build in any order
        "completion_reward": {"coins": 200, "xp": 500},
        "effect": {
            "type": "xp_bonus",
            "bonus_percent": 5,  # +5% XP from all sources
        },
        "max_level": 5,
        "level_scaling": {
            "bonus_percent": 3,  # +3% per level (L5 = +17% XP bonus)
        },
        "visual": "library",
        # Integration note: Multiplicative bonus on XP rewards
        # Stacks with entity xp_bonus perks
    },
    
    "market": {
        "id": "market",
        "name": "🏪 Market",
        "description": "Bustling trade means better prices. Reduces coin costs.",
        "tier": 3,
        "requirements": {
            "water": 30,
            "materials": 40,
            "activity": 20,
            "focus": 25,
        },
        # No prerequisites - build in any order
        "completion_reward": {"coins": 300, "xp": 350},
        "effect": {
            "type": "coin_discount",
            "discount_percent": 5,  # -5% coin costs (shop, merge, etc.)
        },
        "max_level": 5,
        "level_scaling": {
            "discount_percent": 3,  # +3% per level (L5 = -17% costs)
        },
        "visual": "market",
        # Integration note: Hooks into calculate_rarity_bonuses()
        # Stacks with entity coin_discount perks
    },
    
    # =========================================================================
    # TIER 4 - ENDGAME BUILDINGS (Major bonuses, steep requirements)
    # =========================================================================
    "royal_mint": {
        "id": "royal_mint",
        "name": "🏛️ Royal Mint",
        "description": "The economic heart of your city. Massive passive income.",
        "tier": 4,
        "requirements": {
            "water": 60,
            "materials": 100,
            "activity": 40,
            "focus": 60,
        },
        # No prerequisites - build in any order
        "completion_reward": {"coins": 1000, "xp": 750},
        "effect": {
            "type": "passive_income",
            "coins_per_hour": 5,  # +5 coins/hour = 120/day
        },
        "max_level": 10,
        "level_scaling": {
            "coins_per_hour": 2,  # +2/hour per level (L10 = 23 coins/hour = 552/day)
        },
        "visual": "royal_mint",
    },
    
    "observatory": {
        "id": "observatory",
        "name": "🔭 Observatory",
        "description": "Stars reveal secrets. Increases entity encounter rate.",
        "tier": 4,
        "requirements": {
            "water": 40,
            "materials": 60,
            "activity": 20,
            "focus": 100,
        },
        # No prerequisites - build in any order
        "completion_reward": {"coins": 500, "xp": 1000},
        "effect": {
            "type": "entity_encounter_bonus",
            "bonus_percent": 10,  # +10% entity encounter rate
        },
        "max_level": 3,
        "level_scaling": {
            "bonus_percent": 5,  # +5% per level (L3 = +20% encounters)
        },
        "visual": "observatory",
        # Integration note: Hooks into entity encounter roll
        # More frequent encounters = more chances to catch
    },
    
    # =========================================================================
    # TIER 5 - WONDER (Ultimate achievement, massive investment)
    # =========================================================================
    "wonder": {
        "id": "wonder",
        "name": "🏰 Wonder of the World",
        "description": "A monument to human achievement. Grants ALL bonuses!",
        "tier": 5,
        "requirements": {
            "water": 150,
            "materials": 200,
            "activity": 100,
            "focus": 200,
        },
        # No prerequisites - but HUGE resource cost gates it naturally
        "completion_reward": {"coins": 5000, "xp": 10000},
        "effect": {
            "type": "multi",
            "bonuses": {
                "coins_per_hour": 10,       # Passive income
                "merge_success_bonus": 5,   # +5% merge
                "rarity_bias_bonus": 5,     # +5% rarity
                "entity_catch_bonus": 5,    # +5% catch
                "xp_bonus": 10,             # +10% XP
                "power_bonus": 5,           # +5% power
            },
        },
        "max_level": 1,  # Unique - cannot be upgraded
        "visual": "wonder",
    },
}
```

---

## 2A. Building Effect Types & Integration Points

### Effect Type Reference

| Effect Type | Parameter | Integration Point | Stacks With |
|-------------|-----------|-------------------|-------------|
| `passive_income` | `coins_per_hour` | City income collection timer | Multiple buildings |
| `merge_success_bonus` | `bonus_percent` | `calculate_merge_success_rate()` | Item merge_luck, consumables |
| `rarity_bias_bonus` | `bonus_percent` | Rarity roll in item drops | Entity `RARITY_BIAS` perk |
| `entity_catch_bonus` | `bonus_percent` | `get_final_probability()` | Item luck, pity system |
| `entity_encounter_bonus` | `bonus_percent` | Entity encounter roll | Story bonuses |
| `power_bonus` | `power_percent` | `calculate_character_power()` | Gear, entity power perks |
| `xp_bonus` | `bonus_percent` | XP award calculations | Entity XP perks |
| `coin_discount` | `discount_percent` | Cost calculations | Entity coin_discount perk |

### Integration Code Snippets

**⚠️ IMPORTANT: Backward Compatibility**

All function signature changes use **default parameters** to maintain backward compatibility.
Existing callers continue to work unchanged. New callers can pass city_bonus.

**Merge Success Bonus (Forge):**
```python
# In gamification.py - calculate_merge_success_rate()
# CHANGE: Add city_bonus parameter with default=0 (backward compatible)
def calculate_merge_success_rate(items: list, items_merge_luck: int = 0, 
                                  city_bonus: int = 0) -> float:
    """
    Args:
        items_merge_luck: From sacrificed items (existing)
        city_bonus: Total merge_success_bonus from city buildings (NEW, default 0)
    """
    valid_items = [item for item in items if item is not None]
    if len(valid_items) < 2:
        return 0.0
    
    rate = MERGE_BASE_SUCCESS_RATE + (len(valid_items) - 2) * MERGE_BONUS_PER_ITEM
    
    # Items merge luck bonus (existing)
    if items_merge_luck > 0:
        rate += items_merge_luck / 100.0
    
    # NEW: City building bonus (Forge) - only if provided
    if city_bonus > 0:
        rate += city_bonus / 100.0
    
    return min(rate, MERGE_MAX_SUCCESS_RATE)

# CALLER UPDATE (in merge dialog):
# Before: success_rate = calculate_merge_success_rate(items, items_merge_luck)
# After:  
from gamification import get_all_perk_bonuses
bonuses = get_all_perk_bonuses(adhd_buster)
success_rate = calculate_merge_success_rate(
    items, 
    items_merge_luck, 
    city_bonus=bonuses.get("merge_success", 0)
)
```

**Entity Catch Bonus (University):**
```python
# In entitidex/catch_mechanics.py - get_final_probability()
# CHANGE: Add city_bonus parameter with default=0.0 (backward compatible)
def get_final_probability(hero_power: int, entity_power: int, 
                          failed_attempts: int = 0,
                          luck_bonus: float = 0.0,
                          city_bonus: float = 0.0) -> float:  # NEW parameter
    """
    Args:
        luck_bonus: From equipped items (existing)
        city_bonus: Total entity_catch_bonus from city buildings (0.0 to 0.15)
    """
    base = calculate_join_probability(hero_power, entity_power)
    with_pity = apply_pity_bonus(base, failed_attempts)
    with_luck = with_pity + luck_bonus
    
    # NEW: Add city building bonus (University)
    with_city = with_luck + city_bonus
    
    return min(CATCH_CONFIG["probability_max"], with_city)
```

**Rarity Bias Bonus (Artisan Guild):**
```python
# In gamification.py - item rarity roll
def roll_item_rarity(base_weights: dict, entity_bonus: int = 0, 
                     city_bonus: int = 0) -> str:
    """
    Args:
        city_bonus: Total rarity_bias_bonus from city buildings (Artisan Guild)
    """
    total_bias = entity_bonus + city_bonus
    # Shift weights toward higher rarities based on total_bias
    # Each 1% bias = 1% reduction in Common weight, distributed up
    ...
```

### Combined Perk Helper (Entity + City)

```python
# In gamification.py - Unified bonus accessor matching get_entity_perk_bonuses pattern
def get_all_perk_bonuses(adhd_buster: dict) -> dict:
    """
    Get combined bonuses from BOTH entity perks AND city buildings.
    
    This is the single source of truth for all gameplay modifiers.
    Callers should use this instead of querying entity/city separately.
    
    Returns:
        dict: Combined bonuses (entity + city stacked)
    """
    # Get entity perks (existing)
    result = {
        "coin_discount": 0,
        "merge_luck": 0,
        "merge_success": 0,
        "all_luck": 0,
        "rarity_bias": 0,
        "entity_catch_bonus": 0,
        "entity_encounter_bonus": 0,
        "power_bonus": 0,
        "xp_bonus": 0,
        "coins_per_hour": 0,
    }
    
    # Entity perks
    try:
        from entitidex.entity_perks import calculate_active_perks, PerkType
        
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        
        result["coin_discount"] += int(perks.get(PerkType.COIN_DISCOUNT, 0))
        result["merge_luck"] += int(perks.get(PerkType.MERGE_LUCK, 0))
        result["merge_success"] += int(perks.get(PerkType.MERGE_SUCCESS, 0))
        result["all_luck"] += int(perks.get(PerkType.ALL_LUCK, 0))
        result["rarity_bias"] += int(perks.get(PerkType.RARITY_BIAS, 0))
        result["xp_bonus"] += int(perks.get(PerkType.XP_BONUS, 0))
    except Exception:
        pass
    
    # City bonuses (NEW)
    try:
        from city.city_manager import get_city_bonuses
        
        city = get_city_bonuses(adhd_buster)
        result["coin_discount"] += city.get("coin_discount", 0)
        result["merge_success"] += city.get("merge_success_bonus", 0)
        result["rarity_bias"] += city.get("rarity_bias_bonus", 0)
        result["entity_catch_bonus"] += city.get("entity_catch_bonus", 0)
        result["entity_encounter_bonus"] += city.get("entity_encounter_bonus", 0)
        result["power_bonus"] += city.get("power_bonus", 0)
        result["xp_bonus"] += city.get("xp_bonus", 0)
        result["coins_per_hour"] += city.get("coins_per_hour", 0)
    except Exception:
        pass
    
    return result
```

### City Bonuses Helper Function

```python
# In city/city_manager.py
def get_city_bonuses(adhd_buster: dict) -> dict:
    """
    Calculate total bonuses from all completed city buildings.
    
    CRITICAL: Scans GRID (source of truth), not a separate buildings dict.
    This matches the unified persistence model from v1.5.
    
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
    
    city_data = adhd_buster.get("city", {})
    grid = city_data.get("grid", [])
    
    # Scan grid for completed buildings (source of truth)
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
    
    # ADD: Entity synergy bonuses on top of building bonuses
    # Import from city_synergies module (same package)
    from city.city_synergies import get_all_synergy_bonuses
    synergy_bonuses = get_all_synergy_bonuses(adhd_buster)
    # synergy_value is 0.0-0.5 (representing 0%-50% bonus multiplier)
    # bonuses[key] is the base percentage (e.g., 10 means 10%)
    # Result: 10 * (1 + 0.25) = 12 → 12% total bonus
    for key, synergy_value in synergy_bonuses.items():
        if key in bonuses and key != "coins_per_hour":
            # Percentage bonuses: multiply base by (1 + synergy_percent)
            bonuses[key] = int(bonuses[key] * (1 + synergy_value))
        elif key == "coins_per_hour":
            # Coins/hour: multiply base rate by synergy multiplier
            bonuses[key] = int(bonuses[key] * (1 + synergy_value))
    
    return bonuses
```

---

## 3. File Structure

```
PersonalFreedom/
├── city/
│   ├── __init__.py              # Package exports
│   ├── city_buildings.py        # CITY_BUILDINGS definitions
│   ├── city_manager.py          # Business logic (resource mgmt, construction)
│   ├── city_state.py            # State management with signals
│   ├── city_bonuses.py          # get_city_bonuses() - calculates all modifiers
│   ├── city_svg_cache.py        # SVG LRU caching utilities
│   └── city_utils.py            # Helper functions
├── city_tab.py                  # UI Tab (similar to entitidex_tab.py)
│                                # Contains: BuildingCard, AnimatedBuildingWidget,
│                                # ConstructionProgressOverlay, CityTab
├── icons/
│   └── city/                    # Building SVG icons (10 buildings)
│       ├── goldmine.svg         # Static 64x64 viewBox
│       ├── goldmine_animated.svg # With SMIL/CSS animations
│       ├── forge.svg
│       ├── forge_animated.svg   # Flickering flames
│       ├── artisan_guild.svg
│       ├── artisan_guild_animated.svg
│       ├── university.svg
│       ├── university_animated.svg # Floating book pages
│       ├── training_ground.svg
│       ├── training_ground_animated.svg
│       ├── library.svg
│       ├── library_animated.svg # Page turning effect
│       ├── market.svg
│       ├── market_animated.svg  # Crowd bustle
│       ├── royal_mint.svg
│       ├── royal_mint_animated.svg # Coin shimmer
│       ├── observatory.svg
│       ├── observatory_animated.svg # Rotating dome, stars
│       ├── wonder.svg
│       ├── wonder_animated.svg  # Grand celebration effects
│       ├── _construction.svg    # Scaffolding overlay
│       ├── _locked.svg          # Lock icon overlay
│       └── _silhouette_mask.svg # Template for locked buildings
└── tests/
    └── test_city_system.py      # Unit tests
```

---

## 4. Integration Points

### 4.1 Resource Generation Hooks

**IMPORTANT:** These hooks follow the exact pattern from `_log_water()` in focus_blocker_qt.py:
- Access game_state via `getattr(main_window, 'game_state', None)`
- Use try/except for graceful degradation
- Emit signal for UI updates

**Hydration Tab** (💧 Water):
```python
# In focus_blocker_qt.py - _log_water() method, AFTER existing water logging
def _log_water(self):
    # ... existing water logging logic (entry creation, lottery, etc.) ...
    
    # NEW: Generate WATER resource for city (matches game_state access pattern)
    if CITY_AVAILABLE and add_city_resource:
        try:
            main_window = self.window()
            game_state = getattr(main_window, 'game_state', None)
            new_total = add_city_resource(
                self.blocker.adhd_buster, 
                "water", 
                amount=1,
                game_state=game_state  # For toast notification signal
            )
        except Exception as e:
            pass  # Graceful degradation - don't break water logging
```

**Weight Tab** (🧱 Materials):
```python
# In focus_blocker_qt.py - _log_weight() method, AFTER existing weight logic
def _log_weight(self):
    # ... existing weight logging logic ...
    
    # NEW: Generate MATERIALS based on goal progress
    if CITY_AVAILABLE and add_city_resource:
        try:
            main_window = self.window()
            game_state = getattr(main_window, 'game_state', None)
            
            if goal_met:  # Lost weight when goal=lose, etc.
                add_city_resource(self.blocker.adhd_buster, "materials", 2, game_state)
            elif within_tolerance:  # Close to goal
                add_city_resource(self.blocker.adhd_buster, "materials", 1, game_state)
            # else: 0 materials (off-target)
        except Exception:
            pass
```

**Activity Tab** (🏃 Activity):
```python
# In focus_blocker_qt.py - _log_activity() method, AFTER existing activity logic
def _log_activity(self):
    # ... existing activity logging logic ...
    
    # NEW: Generate ACTIVITY resource
    if CITY_AVAILABLE and add_city_resource:
        try:
            main_window = self.window()
            game_state = getattr(main_window, 'game_state', None)
            
            # Base: 1 per activity, bonus for duration
            base_amount = 1
            duration_bonus = duration_minutes // 30  # +1 per 30 min
            add_city_resource(
                self.blocker.adhd_buster, 
                "activity", 
                base_amount + duration_bonus,
                game_state
            )
        except Exception:
            pass
```

**Focus Session** (🎯 Focus):
```python
# In focus_blocker_qt.py - _on_session_complete or _give_session_rewards
def _give_session_rewards(self, session_minutes: int):
    # ... existing session reward logic (XP, coins, items) ...
    
    # NEW: Generate FOCUS resource
    if CITY_AVAILABLE and add_city_resource:
        try:
            main_window = self.window()
            game_state = getattr(main_window, 'game_state', None)
            
            focus_amount = session_minutes // 30  # 1 per 30 min
            if focus_amount > 0:
                add_city_resource(
                    self.blocker.adhd_buster, 
                    "focus", 
                    focus_amount,
                    game_state
                )
        except Exception:
            pass
```

### 4.2 Game State Integration

```python
# In game_state.py - Add new signals
class GameStateManager(QtCore.QObject):
    # ... existing signals ...
    
    # City signals
    city_resources_changed = QtCore.Signal()  # Resource amounts changed
    city_resource_earned = QtCore.Signal(str, int, int)  # (resource_type, amount, new_total) - for toast
    city_building_progress = QtCore.Signal(str)  # Building ID with progress
    city_building_completed = QtCore.Signal(str)  # Building ID completed
    city_income_collected = QtCore.Signal(dict)  # {"coins": X, "xp": Y}
```

### 4.3 Tab Registration

```python
# In focus_blocker_qt.py - Module-level deferred import pattern (like gamification)

# Module-level placeholders (matches existing pattern)
CITY_AVAILABLE = False
add_city_resource = None
get_city_bonuses = None

def load_heavy_modules():
    """Called at startup - load city module if available."""
    global CITY_AVAILABLE, add_city_resource, get_city_bonuses
    
    try:
        from city.city_manager import (
            add_city_resource as _add_city_resource,
            get_city_bonuses as _get_city_bonuses,
        )
        add_city_resource = _add_city_resource
        get_city_bonuses = _get_city_bonuses
        CITY_AVAILABLE = True
    except ImportError:
        CITY_AVAILABLE = False

# In _create_tabs() - matches EntitidexTab pattern exactly
if GAMIFICATION_AVAILABLE and CITY_AVAILABLE:
    from city_tab import CityTab
    self.city_tab = CityTab(self.blocker, self)  # (blocker, parent) - correct pattern
    self.tabs.addTab(self.city_tab, "🏙️ City")
else:
    self.city_tab = None
```

---

## 5. Core Logic Implementation

### 5.1 city_manager.py

```python
"""
City Manager - Core business logic for the City building system.

KEY DESIGN DECISIONS:
- Grid is THE SINGLE SOURCE OF TRUTH for all building state
- No prerequisites - all buildings independent
- Status is EXPLICIT (CellStatus enum), never inferred
- Income uses effect.coins_per_hour * hours_elapsed (unified model)
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from enum import Enum
from .city_buildings import CITY_BUILDINGS

# Resource types
RESOURCE_TYPES = ["water", "materials", "activity", "focus"]
GRID_SIZE = 5

# Configurable limits (future buildings like "Clock Tower" can extend these)
MAX_OFFLINE_HOURS = 24  # Cap on accumulated offline income
DEMOLISH_REFUND_PERCENT = 25  # % of invested resources returned on demolish

class CellStatus(str, Enum):
    PLACED = "placed"     # Building chosen, construction not started
    BUILDING = "building" # Under active construction
    COMPLETE = "complete" # Fully built


def get_city_data(adhd_buster: dict) -> dict:
    """Get or initialize city data structure with grid as source of truth."""
    if "city" not in adhd_buster:
        adhd_buster["city"] = {
            "resources": {r: 0 for r in RESOURCE_TYPES},
            # Grid is source of truth - use comprehension to avoid reference bugs
            "grid": [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)],
            "total_coins_generated": 0,
            "total_xp_generated": 0,
            "last_collection_time": datetime.now().isoformat(),
        }
    # Migration: ensure grid exists and is properly sized
    city = adhd_buster["city"]
    if "grid" not in city or len(city["grid"]) != GRID_SIZE:
        city["grid"] = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    return city


def get_placed_buildings(adhd_buster: dict) -> list[str]:
    """Derive placed building IDs from grid scan (not stored separately)."""
    city = get_city_data(adhd_buster)
    return [
        cell["building_id"]
        for row in city["grid"]
        for cell in row
        if cell is not None
    ]


def add_city_resource(adhd_buster: dict, resource_type: str, amount: int,
                      game_state=None) -> int:
    """
    Add resources to the city pool. Returns new total.
    
    If game_state is provided, emits city_resource_earned signal
    for toast notifications (reinforces habit→reward loop).
    """
    if resource_type not in RESOURCE_TYPES:
        return 0
    
    city = get_city_data(adhd_buster)
    current = city["resources"].get(resource_type, 0)
    new_total = current + amount
    city["resources"][resource_type] = new_total
    
    # Emit signal for toast notification (optional but recommended)
    if game_state is not None:
        game_state.city_resource_earned.emit(resource_type, amount, new_total)
    
    return new_total


def get_resources(adhd_buster: dict) -> dict:
    """Get current resource amounts."""
    city = get_city_data(adhd_buster)
    return city["resources"].copy()


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
    
    # NEW: Check slot availability based on player level
    available_slots = get_available_slots(adhd_buster)
    if available_slots <= 0:
        next_info = get_next_slot_unlock(adhd_buster)
        if next_info["next_unlock_level"]:
            return False, f"No slots available. Next slot at Level {next_info['next_unlock_level']}"
        else:
            return False, "Maximum buildings reached"
    
    return True, "Ready to place"


def place_building(adhd_buster: dict, row: int, col: int, building_id: str) -> bool:
    """Place a building in an empty cell. Returns success."""
    can_place, _ = can_place_building(adhd_buster, building_id)
    if not can_place:
        return False
    
    city = get_city_data(adhd_buster)
    if city["grid"][row][col] is not None:
        return False  # Cell not empty
    
    city["grid"][row][col] = {
        "building_id": building_id,
        "status": CellStatus.PLACED.value,
        "level": 1,
        "construction_progress": {r: 0 for r in RESOURCE_TYPES},
        "placed_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    return True


def start_construction(adhd_buster: dict, row: int, col: int) -> bool:
    """Transition a PLACED cell to BUILDING status."""
    city = get_city_data(adhd_buster)
    cell = city["grid"][row][col]
    
    if cell is None or cell.get("status") != CellStatus.PLACED.value:
        return False
    
    cell["status"] = CellStatus.BUILDING.value
    return True


def invest_resources(adhd_buster: dict, row: int, col: int,
                     resources_to_invest: dict,
                     game_state=None) -> dict:
    """
    Invest resources into a building's construction.
    
    Automatically transitions PLACED → BUILDING on first investment.
    
    Args:
        game_state: Optional GameStateManager for batch mode and signals
    
    Returns:
        {"success": bool, "invested": dict, "remaining_needs": dict, "completed": bool}
    """
    city = get_city_data(adhd_buster)
    cell = city["grid"][row][col]
    
    if cell is None:
        return {"success": False, "error": "Empty cell"}
    
    if cell.get("status") == CellStatus.COMPLETE.value:
        return {"success": False, "error": "Already complete"}
    
    # Use batch mode if game_state provided (single save at end)
    if game_state:
        game_state.begin_batch()
    
    try:
        # Auto-transition PLACED → BUILDING on first investment
        if cell.get("status") == CellStatus.PLACED.value:
            cell["status"] = CellStatus.BUILDING.value
        
        building_def = CITY_BUILDINGS[cell["building_id"]]
        level = cell.get("level", 1)
        requirements = get_level_requirements(building_def, level)
        progress = cell["construction_progress"]
        available = city["resources"]
        
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
        
        # Check if level is now complete
        completed = all(
            progress.get(r, 0) >= requirements.get(r, 0)
            for r in RESOURCE_TYPES
        )
        
        if completed:
            cell["status"] = CellStatus.COMPLETE.value
            cell["completed_at"] = datetime.now().isoformat()
            # Emit building completed signal
            if game_state:
                game_state._emit(game_state.city_building_completed, cell["building_id"])
        else:
            # Emit progress signal
            if game_state:
                game_state._emit(game_state.city_building_progress, cell["building_id"])
        
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
        if game_state:
            game_state.end_batch()  # Emits signals, saves config


def get_level_requirements(building_def: dict, level: int) -> dict:
    """
    Calculate requirements for a specific level.
    
    Level 1 = base requirements
    Level N = base * (1.2 ^ (N-1)) - each level costs 20% more
    """
    base = building_def["requirements"]
    if level <= 1:
        return base.copy()
    
    multiplier = 1.2 ** (level - 1)
    return {r: int(v * multiplier) for r, v in base.items()}


def can_upgrade(adhd_buster: dict, row: int, col: int) -> Tuple[bool, str]:
    """Check if a completed building can be upgraded."""
    city = get_city_data(adhd_buster)
    cell = city["grid"][row][col]
    
    if cell is None or cell.get("status") != CellStatus.COMPLETE.value:
        return False, "Not complete"
    
    building_def = CITY_BUILDINGS[cell["building_id"]]
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
    cell = city["grid"][row][col]
    
    # Increment target level, reset progress, change status
    cell["level"] = cell.get("level", 1) + 1
    cell["status"] = CellStatus.BUILDING.value
    cell["construction_progress"] = {r: 0 for r in RESOURCE_TYPES}
    cell["completed_at"] = None
    
    return True


def move_building(adhd_buster: dict, from_row: int, from_col: int,
                  to_row: int, to_col: int) -> bool:
    """
    Swap two cells (move/rearrange buildings).
    
    Both cells can be buildings or empty - just swaps contents.
    No refunds, no bonus changes - purely cosmetic.
    """
    city = get_city_data(adhd_buster)
    grid = city["grid"]
    
    # Simple swap
    grid[from_row][from_col], grid[to_row][to_col] = \
        grid[to_row][to_col], grid[from_row][from_col]
    
    return True


def collect_city_income(adhd_buster: dict) -> dict:
    """
    Collect passive income from all completed buildings.
    
    Uses UNIFIED income model: effect.coins_per_hour * hours_elapsed
    """
    city = get_city_data(adhd_buster)
    
    last_collection = datetime.fromisoformat(
        city.get("last_collection_time", datetime.now().isoformat())
    )
    now = datetime.now()
    hours_elapsed = (now - last_collection).total_seconds() / 3600
    
    # Cap at configurable limit (future buildings can extend MAX_OFFLINE_HOURS)
    hours_elapsed = min(hours_elapsed, MAX_OFFLINE_HOURS)
    
    total_coins = 0
    breakdown = []
    
    # Scan grid for completed buildings with passive income
    for row in city["grid"]:
        for cell in row:
            if cell is None or cell.get("status") != CellStatus.COMPLETE.value:
                continue
            
            building_def = CITY_BUILDINGS.get(cell["building_id"])
            if not building_def:
                continue
            
            effect = building_def.get("effect", {})
            if effect.get("type") != "passive_income":
                continue
            
            # Calculate income: base + (level-1) * scaling
            level = cell.get("level", 1)
            base_rate = effect.get("coins_per_hour", 0)
            scaling = building_def.get("level_scaling", {}).get("coins_per_hour", 0)
            rate = base_rate + (level - 1) * scaling
            
            amount = int(rate * hours_elapsed)
            if amount > 0:
                total_coins += amount
                breakdown.append({
                    "building": building_def["name"],
                    "rate": rate,
                    "coins": amount,
                })
    
    city["last_collection_time"] = now.isoformat()
    city["total_coins_generated"] = city.get("total_coins_generated", 0) + total_coins
    
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
    
    last_collection = datetime.fromisoformat(
        city.get("last_collection_time", datetime.now().isoformat())
    )
    now = datetime.now()
    hours_elapsed = (now - last_collection).total_seconds() / 3600
    hours_elapsed = min(hours_elapsed, MAX_OFFLINE_HOURS)
    
    total_coins = 0
    
    for row in city["grid"]:
        for cell in row:
            if cell is None or cell.get("status") != CellStatus.COMPLETE.value:
                continue
            
            building_def = CITY_BUILDINGS.get(cell["building_id"])
            if not building_def:
                continue
            
            effect = building_def.get("effect", {})
            if effect.get("type") != "passive_income":
                continue
            
            level = cell.get("level", 1)
            base_rate = effect.get("coins_per_hour", 0)
            scaling = building_def.get("level_scaling", {}).get("coins_per_hour", 0)
            rate = base_rate + (level - 1) * scaling
            total_coins += int(rate * hours_elapsed)
    
    return {
        "coins": total_coins,
        "hours_elapsed": hours_elapsed,
        "capped": hours_elapsed >= MAX_OFFLINE_HOURS,
    }


def demolish_building(adhd_buster: dict, row: int, col: int) -> dict:
    """
    Remove a building from the grid with partial resource refund.
    
    Returns refunded resources (DEMOLISH_REFUND_PERCENT of invested).
    Use sparingly - buildings are meant to be permanent investments.
    """
    city = get_city_data(adhd_buster)
    cell = city["grid"][row][col]
    
    if cell is None:
        return {"success": False, "error": "Empty cell"}
    
    building_id = cell["building_id"]
    building_def = CITY_BUILDINGS.get(building_id, {})
    progress = cell.get("construction_progress", {})
    
    # Calculate refund based on invested resources
    refund = {}
    for resource in RESOURCE_TYPES:
        invested = progress.get(resource, 0)
        refund_amount = int(invested * DEMOLISH_REFUND_PERCENT / 100)
        if refund_amount > 0:
            city["resources"][resource] = city["resources"].get(resource, 0) + refund_amount
            refund[resource] = refund_amount
    
    # Clear the cell
    city["grid"][row][col] = None
    
    return {
        "success": True,
        "demolished": building_def.get("name", building_id),
        "refund": refund,
    }
```

---

## 6. UI Design (city_tab.py)

### 6.1 Grid-Based Layout

The City tab displays a **5×5 interactive grid** where players can place and construct buildings.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  🏙️ Your City                                                [Collect 💰] │
├──────────────────────────────────────────────────────────────────────────┤
│  RESOURCES                                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │ 💧 Water │ │ 🧱 Mats  │ │ 🏃 Active│ │ 🎯 Focus │                     │
│  │    45    │ │    23    │ │    31    │ │    67    │                     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                     │
├──────────────────────────────────────────────────────────────────────────┤
│                             CITY GRID (5×5)                               │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐                │
│  │ ⛏️ Mine  │ 🔥 Forge │ 🎨 Guild │    ➕    │    ➕    │  Row 0         │
│  │ L5 ✓     │ L2 🔨75% │ L1 🔨20% │  [Add]   │  [Add]   │                │
│  │ [Anim]   │ [Build]  │ [Build]  │          │          │                │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┤                │
│  │ 🎓 Univ  │ 📚 Lib   │    ➕    │    ➕    │    ➕    │  Row 1         │
│  │ L3 🔨50% │  [New]   │  [Add]   │  [Add]   │  [Add]   │                │
│  │ [Build]  │          │          │          │          │                │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┤                │
│  │    ➕    │    ➕    │    ➕    │    ➕    │    ➕    │  Row 2         │
│  │  [Add]   │  [Add]   │  [Add]   │  [Add]   │  [Add]   │                │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┤                │
│  │    ➕    │    ➕    │    ➕    │    ➕    │    ➕    │  Row 3         │
│  │  [Add]   │  [Add]   │  [Add]   │  [Add]   │  [Add]   │                │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┤                │
│  │    ➕    │    ➕    │    ➕    │    ➕    │    ➕    │  Row 4         │
│  │  [Add]   │  [Add]   │  [Add]   │  [Add]   │  [Add]   │                │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘                │
│                                                                           │
│  Selected: 🔥 Forge (L2 - 75% complete)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ Progress: ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░ 75%                                 │ │
│  │ 💧 8/10   🧱 15/20   🏃 7/10   🎯 8/10                              │ │
│  │                                               [Invest Resources]    │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Cell Visual States

Each grid cell can be in one of four states:

| State | Visual | Interaction |
|-------|--------|-------------|
| **Empty** | ➕ with "Add" label | Click → Opens building picker dialog |
| **Placed (Not Started)** | Building icon, greyed out | Click → Shows "Start Construction" button |
| **Under Construction** | Building icon + progress ring | Click → Shows progress + "Invest" button |
| **Completed** | Animated SVG, glow effect | Click → Shows stats + upgrade option |

### 6.3 Building Picker Dialog

When clicking an empty cell, a dialog appears to choose which building to place:

```
┌─────────────────────────────────────────────────────────┐
│  Choose Building for Cell (2, 1)              [X Close] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Available Buildings:                                    │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ⛏️ Goldmine                           [✓ Placed]   │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 🏋️ Training Ground               [Select]         │ │
│  │ Cost: 💧25  🧱20  🏃40  🎯15                       │ │
│  │ Effect: +11% hero power (at L5)                    │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 🏛️ Royal Mint                     [Select]         │ │
│  │ Cost: 💧60  🧱100  🏃40  🎯60                      │ │
│  │ Effect: +552 coins/day (at L10)                    │ │
│  └────────────────────────────────────────────────────┘ │
│  ...                                                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 6.4 Construction Progress Visualization

Buildings under construction show progress as they're built:

```
Construction Stages (visual progression):
  0%  - Empty foundation, scaffolding
 25%  - Foundation laid, walls starting
 50%  - Walls up, roof frame visible
 75%  - Roof on, details being added
100%  - Complete! Scaffolding removed, animated

Progress Ring around cell:
  ┌─────────────────┐
  │    🔥 Forge     │
  │  ╭─────────╮    │  ← Progress ring fills clockwise
  │  │  [SVG]  │    │     as construction progresses
  │  ╰─────────╯    │
  │    L2 75%       │
  └─────────────────┘
```

### 6.5 UI Components

1. **Resource Bar**: Shows current resource amounts with icons
2. **Grid Container**: 5×5 QGridLayout of CityCell widgets
3. **CityCell Widget**: 96×96 clickable cell with visual states
4. **Selection Panel**: Details for currently selected cell
5. **Building Picker**: Dialog to choose building for empty cells
6. **Invest Button**: Invest available resources into construction
7. **Collect Button**: Collect accumulated passive income
8. **Progress Rings**: Circular progress around cells under construction

---

## 6A. SVG Graphics Architecture

The City tab uses an SVG graphics system mirroring the Entitidex implementation:
- **Animated SVGs** for completed buildings (smoke, movement, activity)
- **Static SVGs** for construction/locked states (silhouette overlays)
- **LRU caching** for optimal memory/performance
- **Animation freeze/resume** based on tab visibility

### 6A.1 SVG Asset Structure

```
icons/
└── city/
    ├── goldmine.svg              # Tier 1: Pickaxe, gold ore (64x64 viewBox)
    ├── goldmine_animated.svg     # Sparkle on gold nuggets
    ├── forge.svg                 # Tier 2: Anvil, hammer, flames
    ├── forge_animated.svg        # Flickering flames, hammer swing
    ├── artisan_guild.svg         # Tier 2: Paintbrush, chisel, masterpiece
    ├── artisan_guild_animated.svg # Sparkling finished items
    ├── university.svg            # Tier 2: Books, graduation cap, scroll
    ├── university_animated.svg   # Floating book pages, glowing knowledge
    ├── training_ground.svg       # Tier 3: Weights, training dummies
    ├── training_ground_animated.svg # Swinging equipment
    ├── library.svg               # Tier 3: Bookshelves, reading desk
    ├── library_animated.svg      # Page turning, floating letters
    ├── market.svg                # Tier 3: Stalls, goods, crowds
    ├── market_animated.svg       # Bustling crowd movement
    ├── royal_mint.svg            # Tier 4: Grand building, coins
    ├── royal_mint_animated.svg   # Coin shimmer, wealth sparkle
    ├── observatory.svg           # Tier 4: Telescope, stars, dome
    ├── observatory_animated.svg  # Rotating dome, twinkling stars
    ├── wonder.svg                # Tier 5: Grand monument
    ├── wonder_animated.svg       # Rainbow aura, particle celebration
    ├── _construction.svg         # Overlay: scaffolding, workers
    ├── _locked.svg               # Overlay: lock icon, chains
    └── _silhouette_mask.svg      # Template for locked buildings
```

### 6A.2 SVG Cache System

```python
# city_tab.py - Mirroring entitidex_tab.py patterns

from collections import OrderedDict
from typing import Optional
from PySide6.QtSvg import QSvgRenderer
from PySide6 import QtGui

# Industry standard: Module-level LRU caches for singleton-like behavior
_SVG_CACHE_MAX = 50  # Fewer buildings than entities → smaller cache

_building_renderer_cache: OrderedDict[str, QSvgRenderer] = OrderedDict()
_building_pixmap_cache: OrderedDict[str, QtGui.QPixmap] = OrderedDict()
_building_svg_content_cache: OrderedDict[str, str] = OrderedDict()


def _lru_cache_get(cache: OrderedDict, key: str):
    """Get from LRU cache, moving to end on access (most recent)."""
    if key in cache:
        cache.move_to_end(key)
        return cache[key]
    return None


def _lru_cache_set(cache: OrderedDict, key: str, value, max_size: int = _SVG_CACHE_MAX):
    """Set in LRU cache, evicting oldest if at capacity."""
    if key in cache:
        cache.move_to_end(key)
    else:
        if len(cache) >= max_size:
            cache.popitem(last=False)  # Remove oldest (first)
        cache[key] = value


def get_cached_building_renderer(svg_path: str) -> Optional[QSvgRenderer]:
    """Get or create QSvgRenderer for static building SVGs."""
    cached = _lru_cache_get(_building_renderer_cache, svg_path)
    if cached is not None:
        return cached
    
    try:
        renderer = QSvgRenderer(svg_path)
        if renderer.isValid():
            _lru_cache_set(_building_renderer_cache, svg_path, renderer)
            return renderer
    except Exception:
        pass
    return None


def clear_building_caches():
    """Clear all SVG caches (e.g., on theme change or memory pressure)."""
    global _building_renderer_cache, _building_pixmap_cache, _building_svg_content_cache
    _building_renderer_cache.clear()
    _building_pixmap_cache.clear()
    _building_svg_content_cache.clear()


def get_cache_stats() -> dict:
    """Return cache statistics for debugging/monitoring."""
    return {
        "renderers": len(_building_renderer_cache),
        "pixmaps": len(_building_pixmap_cache),
        "svg_content": len(_building_svg_content_cache),
        "max_size": _SVG_CACHE_MAX,
    }
```

### 6A.3 Animated Building Widget

```python
# city_tab.py - AnimatedBuildingWidget

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtSvgWidgets import QSvgWidget

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False


class AnimatedBuildingWidget(QtWidgets.QWidget):
    """
    Widget for displaying animated building SVGs using QWebEngineView.
    
    SMIL/CSS animations supported:
    - Windmill rotation (Farm)
    - Smoke rising (Workshop, Hospital)
    - Water ripples (Well)
    - Book pages turning (Library)
    - Coin shimmer (Mint)
    - Grand particle effects (Wonder)
    
    Falls back to QSvgWidget for systems without WebEngine.
    
    OPTIMIZATION: Uses cached SVG content to avoid redundant file I/O.
    """
    
    __slots__ = ('svg_path', 'web_view', 'svg_widget', '_animations_paused')
    
    def __init__(self, svg_path: str, size: int = 128, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.web_view = None
        self.svg_widget = None
        self._animations_paused = False
        self.setFixedSize(size, size)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        if HAS_WEBENGINE:
            self.web_view = QWebEngineView(self)
            self.web_view.setFixedSize(size, size)
            self.web_view.page().setBackgroundColor(QtCore.Qt.transparent)
            self.web_view.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            
            self._load_svg(size)
            layout.addWidget(self.web_view)
        else:
            self.svg_widget = QSvgWidget(svg_path, self)
            self.svg_widget.setFixedSize(size, size)
            self.svg_widget.setStyleSheet("background: transparent;")
            layout.addWidget(self.svg_widget)
    
    def _load_svg(self, size: int):
        """Load SVG into WebEngine with proper HTML wrapper."""
        if not self.web_view:
            return
        
        # Use cached SVG content
        svg_content = _lru_cache_get(_building_svg_content_cache, self.svg_path)
        if svg_content is None:
            try:
                with open(self.svg_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                _lru_cache_set(_building_svg_content_cache, self.svg_path, svg_content)
            except Exception:
                svg_content = '<svg></svg>'
        
        html = f'''<!DOCTYPE html>
<html>
<head>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ 
        width: {size}px; height: {size}px; 
        overflow: hidden; background: transparent;
        display: flex; align-items: center; justify-content: center;
    }}
    svg {{ width: {size}px; height: {size}px; display: block; }}
</style>
</head>
<body>{svg_content}</body>
</html>'''
        
        from pathlib import Path
        base_url = QtCore.QUrl.fromLocalFile(str(Path(self.svg_path).parent) + '/')
        self.web_view.setHtml(html, base_url)
    
    def stop_animations(self) -> None:
        """Pause all CSS/SMIL animations to save CPU when hidden."""
        if self._animations_paused:
            return
        self._animations_paused = True
        
        if self.web_view:
            self.web_view.page().runJavaScript(
                "document.querySelectorAll('*').forEach(el => el.style.animationPlayState = 'paused');"
                "document.querySelectorAll('animate, animateTransform, animateMotion').forEach(el => el.endElement ? el.endElement() : null);"
            )
    
    def restart_animations(self) -> None:
        """Resume animations when visible again."""
        if not self._animations_paused:
            return
        self._animations_paused = False
        
        if self.web_view:
            self.web_view.page().runJavaScript(
                "document.querySelectorAll('*').forEach(el => el.style.animationPlayState = '');"
                "document.querySelectorAll('animate, animateTransform, animateMotion').forEach(el => el.beginElement ? el.beginElement() : null);"
            )
```

### 6A.4 CityCell Widget (Grid Cell)

```python
class CityCell(QtWidgets.QFrame):
    """
    Single cell in the 5×5 city grid.
    
    States:
    - EMPTY: Shows ➕ icon, clickable to place a building
    - PLACED: Building icon (greyed), click to start construction
    - BUILDING: Building icon + progress ring, shows construction
    - COMPLETE: Animated building, pulsing glow
    """
    
    cell_clicked = QtCore.Signal(int, int)  # Emits (row, col)
    
    CELL_SIZE = 96  # Fixed cell size in pixels
    
    def __init__(self, row: int, col: int, cell_state: dict = None, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.cell_state = cell_state  # None = empty, dict = building data
        
        self.setFixedSize(self.CELL_SIZE, self.CELL_SIZE)
        self.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Raised)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        
        # Animation tracking
        self._progress_animation = None
        self._glow_animation = None
        self._building_widget = None
        self._animations_paused = False
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        
        if self.cell_state is None:
            # EMPTY CELL - show add button
            self._create_empty_cell(layout)
        elif not self.cell_state.get("completed", False):
            # UNDER CONSTRUCTION - show building with progress ring
            self._create_construction_cell(layout)
        else:
            # COMPLETED - show animated building
            self._create_completed_cell(layout)
    
    def _create_empty_cell(self, layout):
        """Empty cell with ➕ icon."""
        add_label = QtWidgets.QLabel("➕")
        add_label.setAlignment(QtCore.Qt.AlignCenter)
        add_label.setStyleSheet("font-size: 32px; color: #888;")
        layout.addWidget(add_label)
        
        hint_label = QtWidgets.QLabel("Add")
        hint_label.setAlignment(QtCore.Qt.AlignCenter)
        hint_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(hint_label)
        
        self.setStyleSheet("""
            CityCell {
                background: #f0f0f0;
                border: 2px dashed #ccc;
                border-radius: 8px;
            }
            CityCell:hover {
                background: #e0e8ff;
                border-color: #4a90d9;
            }
        """)
    
    def _create_construction_cell(self, layout):
        """
        Building under construction with progress ring.
        
        VISUAL CONTINUITY:
        - New Build (level 1): Show building SVG with construction overlay
        - Upgrade (level 2+): Show building SVG (recognizable) with scaffolding overlay
        This prevents jarring visual regression when upgrading advanced buildings.
        """
        building_id = self.cell_state.get("building_id")
        building_def = CITY_BUILDINGS.get(building_id, {})
        level = self.cell_state.get("level", 1)
        
        # Calculate progress percentage
        progress = self._calculate_progress()
        
        # Container for layered construction visuals
        container = QtWidgets.QWidget()
        container.setFixedSize(64, 64)
        container_layout = QtWidgets.QStackedLayout(container)
        container_layout.setStackingMode(QtWidgets.QStackedLayout.StackAll)
        
        # Layer 1: Building SVG (static) - always show the actual building
        svg_path = get_app_dir() / "icons" / "city" / f"{building_id}.svg"
        if svg_path.exists():
            building_svg = self._create_static_svg(str(svg_path), 64)
            # For upgrades (L2+), keep full opacity; for new builds, slight fade
            if level == 1:
                building_svg.setStyleSheet("opacity: 0.6;")
            container_layout.addWidget(building_svg)
        
        # Layer 2: Construction/scaffolding overlay
        construction_path = get_app_dir() / "icons" / "city" / "_construction.svg"
        if construction_path.exists():
            scaffold_svg = self._create_static_svg(str(construction_path), 64)
            container_layout.addWidget(scaffold_svg)
        
        self._building_widget = container
        layout.addWidget(container)
        
        # Progress ring is drawn in paintEvent() around the cell
        self._progress_percent = progress
        
        # Level and progress label
        level = self.cell_state.get("level", 1)
        label = QtWidgets.QLabel(f"L{level} {progress:.0f}%")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet("font-size: 9px; font-weight: bold;")
        layout.addWidget(label)
        
        self.setStyleSheet("""
            CityCell {
                background: #fff8e0;
                border: 2px solid #ffa500;
                border-radius: 8px;
            }
        """)
    
    def _create_completed_cell(self, layout):
        """
        Completed building - static SVG in grid, animated in selection panel.
        
        NOTE: Grid cells use STATIC QSvgWidget only (per WebEngine limit).
        The selection panel has a shared QWebEngineView for animations.
        """
        building_id = self.cell_state.get("building_id")
        building_def = CITY_BUILDINGS.get(building_id, {})
        level = self.cell_state.get("level", 1)
        
        # Grid cells use STATIC SVG only (shared WebEngine in selection panel)
        static_path = get_app_dir() / "icons" / "city" / f"{building_id}.svg"
        if static_path.exists():
            self._building_widget = self._create_static_svg(str(static_path), 64)
        
        if self._building_widget:
            layout.addWidget(self._building_widget)
        
        # Level indicator
        label = QtWidgets.QLabel(f"L{level} ✓")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet("font-size: 9px; font-weight: bold; color: #228b22;")
        layout.addWidget(label)
        
        # Pulsing glow for completed buildings
        self._start_glow_animation()
        
        self.setStyleSheet("""
            CityCell {
                background: #e8ffe8;
                border: 2px solid #228b22;
                border-radius: 8px;
            }
        """)
    
    def _calculate_progress(self) -> float:
        """Calculate construction progress as percentage."""
        if not self.cell_state:
            return 0.0
        
        building_id = self.cell_state.get("building_id")
        building_def = CITY_BUILDINGS.get(building_id, {})
        requirements = building_def.get("requirements", {})
        progress_data = self.cell_state.get("construction_progress", {})
        
        total_required = sum(requirements.values())
        if total_required == 0:
            return 100.0
        
        total_invested = sum(progress_data.get(res, 0) for res in requirements.keys())
        return (total_invested / total_required) * 100
    
    def paintEvent(self, event):
        """Custom paint for progress ring on construction cells."""
        super().paintEvent(event)
        
        if self.cell_state and not self.cell_state.get("completed", False):
            # Draw progress ring around the cell
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            
            pen = QtGui.QPen(QtGui.QColor("#ffa500"), 4)
            painter.setPen(pen)
            
            rect = self.rect().adjusted(4, 4, -4, -4)
            span_angle = int(self._calculate_progress() * 3.6 * 16)  # Qt uses 1/16 degree
            painter.drawArc(rect, 90 * 16, -span_angle)  # Start from top, clockwise
            
            painter.end()
    
    def mousePressEvent(self, event):
        """Emit click signal with coordinates."""
        if event.button() == QtCore.Qt.LeftButton:
            self.cell_clicked.emit(self.row, self.col)
        super().mousePressEvent(event)
    
    def pause_animations(self):
        if self._animations_paused:
            return
        self._animations_paused = True
        if self._glow_animation:
            self._glow_animation.pause()
        if isinstance(self._building_widget, AnimatedBuildingWidget):
            self._building_widget.stop_animations()
    
    def resume_animations(self):
        if not self._animations_paused:
            return
        self._animations_paused = False
        if self._glow_animation:
            self._glow_animation.resume()
        if isinstance(self._building_widget, AnimatedBuildingWidget):
            self._building_widget.restart_animations()
```

### 6A.5 CityGrid Widget (1×10 Container)

```python
class CityGrid(QtWidgets.QWidget):
    """
    1×10 horizontal grid container for city cells.
    
    Manages:
    - Grid layout of CityCell widgets (single row, 10 columns)
    - Cell click handling
    - Batch animation pause/resume
    - Hides locked slots (only shows unlocked slots based on player level)
    """
    
    cell_selected = QtCore.Signal(int, int, object)  # row, col, cell_state
    
    GRID_SIZE = 5
    
    def __init__(self, city_data: dict, parent=None):
        super().__init__(parent)
        self.city_data = city_data
        self._cells: list[list[CityCell]] = []
        
        self._build_grid()
    
    def _build_grid(self):
        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        grid_data = self.city_data.get("grid", [[None]*5 for _ in range(5)])
        
        for row in range(self.GRID_SIZE):
            row_cells = []
            for col in range(self.GRID_SIZE):
                cell_state = grid_data[row][col] if row < len(grid_data) else None
                cell = CityCell(row, col, cell_state)
                cell.cell_clicked.connect(self._on_cell_clicked)
                layout.addWidget(cell, row, col)
                row_cells.append(cell)
            self._cells.append(row_cells)
    
    def _on_cell_clicked(self, row: int, col: int):
        """Handle cell click - emit with state for parent to process."""
        cell_state = self.city_data.get("grid", [[None]*5]*5)[row][col]
        self.cell_selected.emit(row, col, cell_state)
    
    def update_cell(self, row: int, col: int, new_state: dict):
        """Update a single cell after building placed or progress made."""
        # Remove old cell
        old_cell = self._cells[row][col]
        old_cell.pause_animations()
        old_cell.deleteLater()
        
        # Create new cell with updated state
        new_cell = CityCell(row, col, new_state)
        new_cell.cell_clicked.connect(self._on_cell_clicked)
        
        # Replace in layout
        layout = self.layout()
        layout.addWidget(new_cell, row, col)
        self._cells[row][col] = new_cell
    
    def pause_all_animations(self):
        for row in self._cells:
            for cell in row:
                cell.pause_animations()
    
    def resume_all_animations(self):
        for row in self._cells:
            for cell in row:
                cell.resume_animations()
```

### 6A.6 Building Details Panel (Obsolete, replaced by grid cells)

The previous BuildingCard design is replaced by the CityCell + selection panel approach.
When a cell is clicked, the selection panel at the bottom shows detailed info:

### 6A.7 CityTab with Grid Layout

```python
class CityTab(QtWidgets.QWidget):
    """
    City building tab with 1×10 horizontal grid and animation lifecycle management.
    
    Features:
    - 1×10 horizontal grid of CityCell widgets (locked slots are hidden)
    - Selection panel for cell details
    - Building picker dialog for empty cells
    - Resource bar at top
    - Collect button for passive income
    
    Mirrors EntitidexTab patterns:
    - Lazy initialization on first show
    - Animation pause on hideEvent/minimize
    - Animation resume on showEvent/restore
    """
    
    def __init__(self, blocker, parent=None):
        super().__init__(parent)
        self.blocker = blocker
        self.adhd_buster = blocker.adhd_buster
        
        # Grid reference
        self._city_grid: CityGrid = None
        self._selected_cell: tuple = None  # (row, col)
        
        # Animation lifecycle tracking
        self._is_visible = False
        self._initialized = False
        
        # Placeholder for lazy loading
        self._setup_placeholder()
    
    def _build_ui(self):
        """Build the full city tab UI."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Resource bar
        self._resource_bar = self._create_resource_bar()
        layout.addWidget(self._resource_bar)
        
        # City grid (5×5)
        city_data = self.adhd_buster.get("city", {})
        self._city_grid = CityGrid(city_data)
        self._city_grid.cell_selected.connect(self._on_cell_selected)
        layout.addWidget(self._city_grid)
        
        # Selection panel (shows details of selected cell)
        self._selection_panel = self._create_selection_panel()
        layout.addWidget(self._selection_panel)
        
        # Collect button
        self._collect_btn = QtWidgets.QPushButton("💰 Collect Income")
        self._collect_btn.clicked.connect(self._collect_income)
        layout.addWidget(self._collect_btn)
    
    def _on_cell_selected(self, row: int, col: int, cell_state):
        """Handle cell selection - update selection panel."""
        self._selected_cell = (row, col)
        
        if cell_state is None:
            # Empty cell - show building picker
            self._show_building_picker(row, col)
        else:
            # Show building details in selection panel (with animated SVG)
            self._update_selection_panel(row, col, cell_state)
    
    def _show_building_picker(self, row: int, col: int):
        """Show dialog to choose a building for empty cell."""
        from city.city_manager import get_placed_buildings, place_building
        
        placed = get_placed_buildings(self.adhd_buster)
        available = [b for b in CITY_BUILDINGS.keys() if b not in placed]
        
        # Show picker dialog with available buildings
        dialog = BuildingPickerDialog(available, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            building_id = dialog.selected_building
            if place_building(self.adhd_buster, row, col, building_id):
                self._refresh_cell(row, col)
                self.blocker._save_config()
    
    def _refresh_cell(self, row: int, col: int):
        """Refresh a single cell from grid data."""
        city = self.adhd_buster.get("city", {})
        grid = city.get("grid", [])
        new_state = grid[row][col] if row < len(grid) else None
        self._city_grid.update_cell(row, col, new_state)
    
    def _update_selection_panel(self, row: int, col: int, cell_state: dict):
        """
        Update selection panel with building details.
        
        BUILDING STATE HANDLING:
        - COMPLETE: Show animated SVG in shared WebEngineView
        - BUILDING: Show static building SVG with grayscale filter + progress bars
        - PLACED: Show static building SVG with "Start Construction" button
        """
        building_id = cell_state.get("building_id")
        building_def = CITY_BUILDINGS.get(building_id, {})
        status = cell_state.get("status")
        
        if status == CellStatus.COMPLETE.value:
            # Full animated SVG in the shared WebEngineView
            animated_path = get_app_dir() / "icons" / "city" / f"{building_id}_animated.svg"
            if animated_path.exists() and self._selection_animation:
                self._selection_animation.load_svg(str(animated_path))
        
        elif status == CellStatus.BUILDING.value:
            # Static SVG with construction overlay + grayscale hint
            # Shows the building is "there" but not fully operational
            static_path = get_app_dir() / "icons" / "city" / f"{building_id}.svg"
            if static_path.exists() and self._selection_animation:
                self._selection_animation.load_svg_with_filter(
                    str(static_path), filter_type="grayscale"
                )
            # Also show progress bars and "Invest" button
            self._show_investment_controls(row, col, cell_state)
        
        elif status == CellStatus.PLACED.value:
            # Static SVG, "Start Construction" button
            static_path = get_app_dir() / "icons" / "city" / f"{building_id}.svg"
            if static_path.exists() and self._selection_animation:
                self._selection_animation.load_svg(str(static_path))
            self._show_start_construction_button(row, col)
    
    def _update_collect_button(self):
        """
        Update Collect button label with pending income preview.
        
        Shows "Collect 45 Coins" instead of generic "Collect Income".
        Provides immediate feedback on accumulated value.
        """
        from city.city_manager import get_pending_income
        
        pending = get_pending_income(self.adhd_buster)
        coins = pending.get("coins", 0)
        
        if coins > 0:
            label = f"💰 Collect {coins} Coins"
            if pending.get("capped"):
                label += " (MAX)"
            self._collect_btn.setText(label)
            self._collect_btn.setEnabled(True)
        else:
            self._collect_btn.setText("💰 No Income Yet")
            self._collect_btn.setEnabled(False)
    
    def _enter_move_mode(self):
        """Enable move mode - next two cell clicks will swap."""
        self._move_mode = True
        self._move_from = None
        # Show visual hint
    
    def _handle_move_click(self, row: int, col: int):
        """Handle cell click in move mode."""
        from city.city_manager import move_building
        
        if self._move_from is None:
            self._move_from = (row, col)
            # Highlight selected cell
        else:
            # Perform swap
            from_row, from_col = self._move_from
            move_building(self.adhd_buster, from_row, from_col, row, col)
            
            # Refresh both cells
            self._refresh_cell(from_row, from_col)
            self._refresh_cell(row, col)
            
            self._move_mode = False
            self._move_from = None
            self.blocker._save_config()
    
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Resume animations when tab becomes visible."""
        super().showEvent(event)
        self._is_visible = True
        
        if not self._initialized:
            self._initialized = True
            self._build_ui()
        
        # Resume selection panel animation only (grid cells are static)
        if self._selection_animation:
            self._selection_animation.restart_animations()
    
    def hideEvent(self, event: QtGui.QHideEvent) -> None:
        """Pause animations when tab is hidden."""
        super().hideEvent(event)
        self._is_visible = False
        
        # Pause selection panel animation
        if self._selection_animation:
            self._selection_animation.stop_animations()
    
    def on_window_minimized(self) -> None:
        """Called by parent when app is minimized to tray."""
        if not self._is_visible:
            return
        self._is_visible = False
        if self._selection_animation:
            self._selection_animation.stop_animations()
    
    def on_window_restored(self) -> None:
        """Called by parent when app is restored."""
        if self._is_visible:
            return
        self._is_visible = True
        if self._city_grid and self._initialized:
            self._city_grid.resume_all_animations()
```

### 6A.8 Construction Progress Visualization

```python
class ConstructionProgressOverlay(QtWidgets.QWidget):
    """
    Animated overlay showing construction progress.
    
    Features:
    - Per-resource progress bars (💧🧱🏃🎯)
    - Overall completion percentage
    - Animated scaffolding/workers (optional)
    - Particle effects when resources invested
    """
    
    def __init__(self, building_state: dict, requirements: dict, parent=None):
        super().__init__(parent)
        self.state = building_state
        self.requirements = requirements
        self._progress_bars = {}
        self._build_ui()
    
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Per-resource mini progress bars
        for resource, required in self.requirements.items():
            if required <= 0:
                continue
            
            current = self.state.get("construction_progress", {}).get(resource, 0)
            bar = self._create_resource_bar(resource, current, required)
            self._progress_bars[resource] = bar
            layout.addWidget(bar)
    
    def _create_resource_bar(self, resource: str, current: int, total: int):
        """Create color-coded progress bar for resource."""
        RESOURCE_COLORS = {
            "water": "#4fc3f7",     # Light blue
            "materials": "#8d6e63", # Brown
            "activity": "#81c784",  # Green
            "focus": "#ba68c8",     # Purple
        }
        # ... bar creation with fill percentage ...
        pass
    
    def update_progress(self, new_state: dict):
        """Animate progress bar updates when resources invested."""
        for resource, bar in self._progress_bars.items():
            new_value = new_state.get("construction_progress", {}).get(resource, 0)
            # Animate bar fill
            self._animate_bar(bar, new_value)
    
    def _animate_bar(self, bar, target_value: int):
        """Smooth animation for progress updates."""
        # QPropertyAnimation on bar width
        pass
```

### 6A.9 Performance Optimizations Summary

| Optimization | Implementation | Benefit |
|--------------|---------------|---------|
| **LRU Caching** | `OrderedDict` with 50-item limit | Reuse renderers, avoid redundant I/O |
| **Lazy Init** | Build UI on first `showEvent` | Faster app startup |
| **Animation Pause** | `pause_animations()` on hide | Near-zero CPU when hidden |
| **Visibility Check** | Only animate visible cards | No wasted animation frames |
| **WebEngine Limit** | Max 1 active view (see below) | Avoid memory explosion |
| **Batch Updates** | Update multiple cards in one pass | Reduce layout reflows |
| **__slots__** | Use on widget classes | Lower memory per card |

**⚠️ CRITICAL: WebEngine Instance Limit**

25 `QWebEngineView` instances is NOT viable - each consumes ~20-50MB and spawns Chromium processes.

**Recommended approach:**
1. Grid cells use **static QSvgWidget** or cached pixmaps for ALL states
2. ONE shared `QWebEngineView` in the **selection/details panel** for the selected building
3. When user selects a completed building → swap animated SVG to the shared view
4. When deselected → swap back to static display

This gives the "wow factor" of animations for the focused building without memory explosion.

---

## 6B. Advanced Performance & Visual Quality Architecture

This section details **industry-standard optimizations** that ensure the City graphics system is both **lightweight** and **visually impressive**.

### 6B.1 Performance Targets (Industry Benchmarks)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Frame Rate** | 60 FPS (16.67ms/frame) | No jank during animations |
| **Memory (Idle)** | < 50 MB for City tab | After caches populated |
| **Memory (Active)** | < 80 MB peak | During animations/transitions |
| **CPU (Hidden)** | ~0% (< 0.5%) | When tab not visible |
| **CPU (Visible)** | < 5% | During normal operation |
| **Startup Time** | < 100ms | From tab click to first render |
| **Animation Start** | < 16ms | From trigger to first frame |

### 6B.2 SVG Asset Optimization (Pre-Build)

Before runtime, SVGs should be optimized:

```bash
# Industry standard: SVGO for SVG optimization
# Reduces file size 40-80% without quality loss

# Install: npm install -g svgo
svgo --config svgo.config.js -f icons/city/ -o icons/city/

# svgo.config.js
module.exports = {
  plugins: [
    'removeDoctype',
    'removeXMLProcInst',
    'removeComments',
    'removeMetadata',
    'removeEditorsNSData',
    'cleanupAttrs',
    'mergeStyles',
    'inlineStyles',
    'minifyStyles',
    'cleanupIds',                    # Short IDs save bytes
    'removeUselessDefs',
    'cleanupNumericValues',          # Round to 2 decimals
    'convertColors',                 # Hex to short form
    'removeUnknownsAndDefaults',
    'removeNonInheritableGroupAttrs',
    'removeUselessStrokeAndFill',
    'cleanupEnableBackground',
    'removeHiddenElems',
    'removeEmptyText',
    'convertShapeToPath',            # Smaller path data
    'convertEllipseToCircle',
    'moveGroupAttrsToElems',
    'collapseGroups',
    'convertPathData',               # Optimize path commands
    'convertTransform',
    'removeEmptyAttrs',
    'removeEmptyContainers',
    { name: 'removeViewBox', active: false },  # Keep viewBox!
    { name: 'cleanupIds', params: { prefix: 'b' } },  # Short prefixes
  ]
};
```

**Target SVG sizes:**
- Static building SVG: < 2 KB each (after optimization)
- Animated building SVG: < 5 KB each (more complex paths)
- Total icons/city/: < 60 KB (all 22 files)

### 6B.3 GPU-Accelerated Rendering

```python
# city_tab.py - Enable hardware acceleration

class OptimizedCityCell(QtWidgets.QFrame):
    """
    City cell with GPU-accelerated rendering.
    
    Industry standard: Use composition layers for animated elements
    to offload work from CPU to GPU.
    """
    
    def __init__(self, row: int, col: int, parent=None):
        super().__init__(parent)
        
        # Enable GPU acceleration for this widget's subtree
        # Qt automatically uses OpenGL for compositing when available
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        # Industry standard: Request high-performance graphics
        # This hints to the compositor to use GPU layers
        self.setGraphicsEffect(None)  # No software effects
        
        # For progress ring animations, use QPropertyAnimation
        # which Qt optimizes via the scene graph
        self._setup_gpu_animations()
    
    def _setup_gpu_animations(self):
        """Configure animations for GPU-friendly rendering."""
        # Opacity animations are GPU-accelerated (no repaint)
        self._opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        
        # Glow pulse animation (opacity is GPU-composited)
        self._glow_anim = QtCore.QPropertyAnimation(
            self._opacity_effect, b"opacity"
        )
        self._glow_anim.setDuration(1500)
        self._glow_anim.setStartValue(0.85)
        self._glow_anim.setEndValue(1.0)
        self._glow_anim.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        self._glow_anim.setLoopCount(-1)  # Infinite
```

### 6B.4 Efficient Animation Techniques

**Rule: Animate opacity only - never geometry**

Qt widgets don't have CSS-like transform properties. Geometry animations trigger layout recalculation and are expensive. Use opacity effects only for runtime animations.

```python
# ✅ GOOD: GPU-friendly animations (opacity only)
class EfficientAnimations:
    """Industry standard: Opacity-only animations for Qt widgets."""
    
    @staticmethod
    def create_pulse_effect(widget: QtWidgets.QWidget) -> tuple:
        """
        Pulse effect using opacity - GPU composited.
        
        NOTE: Do NOT animate geometry/scale in Qt - it triggers layout.
        For 'scale' illusions, use pre-rendered pixmaps at different sizes.
        """
        effect = QtWidgets.QGraphicsOpacityEffect(widget)
        effect.setOpacity(1.0)
        
        anim = QtCore.QPropertyAnimation(effect, b"opacity")
        anim.setDuration(1500)
        anim.setKeyValueAt(0.0, 0.85)
        anim.setKeyValueAt(0.5, 1.0)
        anim.setKeyValueAt(1.0, 0.85)
        anim.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        anim.setLoopCount(-1)
        
        widget.setGraphicsEffect(effect)
        return effect, anim
    
    @staticmethod
    def create_shimmer_effect(widget: QtWidgets.QWidget) -> tuple:
        """Shimmer using opacity gradient - GPU composited."""
        effect = QtWidgets.QGraphicsOpacityEffect(widget)
        
        # Animate opacity between 0.9 and 1.0 (subtle shimmer)
        anim = QtCore.QPropertyAnimation(effect, b"opacity")
        anim.setDuration(2000)
        anim.setKeyValueAt(0.0, 0.9)
        anim.setKeyValueAt(0.5, 1.0)
        anim.setKeyValueAt(1.0, 0.9)
        anim.setLoopCount(-1)
        
        return effect, anim

# ❌ BAD: CPU-heavy (triggers layout/repaint every frame)
# - Animating geometry (width/height/pos) - EXPENSIVE in Qt
# - QPropertyAnimation on b"geometry" - triggers full layout
# - Changing stylesheets every frame
# - Calling update() in a timer without batching
```

### 6B.5 Smart Animation Frame Management

```python
# city_tab.py - Frame-rate aware animation manager

class AnimationFrameManager:
    """
    Centralized animation frame manager for all city cells.
    
    Industry standard: Single requestAnimationFrame equivalent
    instead of N independent timers (reduces overhead).
    """
    
    _instance = None
    _FRAME_BUDGET_MS = 16  # 60 FPS target
    
    @classmethod
    def instance(cls) -> 'AnimationFrameManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self._subscribers: list[Callable] = []
        self._timer = QtCore.QTimer()
        self._timer.setInterval(16)  # ~60 FPS
        self._timer.timeout.connect(self._on_frame)
        self._running = False
        self._last_frame_time = 0
    
    def subscribe(self, callback: Callable[[float], None]) -> None:
        """Subscribe to frame updates. Callback receives delta_time in seconds."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)
            if not self._running and self._subscribers:
                self._start()
    
    def unsubscribe(self, callback: Callable) -> None:
        """Unsubscribe from frame updates."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            if self._running and not self._subscribers:
                self._stop()
    
    def _start(self):
        self._running = True
        self._last_frame_time = time.perf_counter()
        self._timer.start()
    
    def _stop(self):
        self._running = False
        self._timer.stop()
    
    def _on_frame(self):
        """Single frame tick for all subscribers."""
        now = time.perf_counter()
        delta = now - self._last_frame_time
        self._last_frame_time = now
        
        # Frame budget tracking
        frame_start = time.perf_counter()
        
        for callback in self._subscribers:
            try:
                callback(delta)
            except Exception as e:
                _logger.warning("Animation callback error: %s", e)
        
        # Industry standard: Log frame budget overruns
        frame_time_ms = (time.perf_counter() - frame_start) * 1000
        if frame_time_ms > self._FRAME_BUDGET_MS:
            _logger.debug("Frame budget exceeded: %.1fms > %dms", 
                         frame_time_ms, self._FRAME_BUDGET_MS)
```

### 6B.6 Memory-Efficient Pixmap Pooling

```python
# city_tab.py - Pixmap pool for construction overlays

class PixmapPool:
    """
    Pool of pre-rendered pixmaps for common visual states.
    
    Industry standard: Object pooling prevents GC pressure
    from frequent allocations during animations.
    """
    
    def __init__(self):
        self._pool: dict[str, list[QtGui.QPixmap]] = {}
        self._stats = {"hits": 0, "misses": 0, "returns": 0}
    
    def acquire(self, key: str, size: tuple[int, int], 
                factory: Callable[[], QtGui.QPixmap]) -> QtGui.QPixmap:
        """
        Get a pixmap from pool or create new one.
        
        Args:
            key: Category key (e.g., "progress_ring_64")
            size: (width, height) for validation
            factory: Function to create new pixmap if pool empty
        """
        pool_key = f"{key}_{size[0]}x{size[1]}"
        
        if pool_key in self._pool and self._pool[pool_key]:
            self._stats["hits"] += 1
            return self._pool[pool_key].pop()
        
        self._stats["misses"] += 1
        return factory()
    
    def release(self, key: str, pixmap: QtGui.QPixmap) -> None:
        """Return pixmap to pool for reuse."""
        size = (pixmap.width(), pixmap.height())
        pool_key = f"{key}_{size[0]}x{size[1]}"
        
        if pool_key not in self._pool:
            self._pool[pool_key] = []
        
        # Industry standard: Limit pool size to prevent unbounded growth
        if len(self._pool[pool_key]) < 10:
            self._stats["returns"] += 1
            self._pool[pool_key].append(pixmap)
    
    def get_stats(self) -> dict:
        """Return pool statistics for monitoring."""
        return {
            **self._stats,
            "pool_sizes": {k: len(v) for k, v in self._pool.items()},
        }


# Module-level singleton
_pixmap_pool = PixmapPool()
```

### 6B.7 WebEngine Optimization

```python
# city_tab.py - Optimized WebEngine settings

class OptimizedAnimatedBuildingWidget(QtWidgets.QWidget):
    """
    WebEngine-based animated SVG with maximum performance.
    
    Industry optimizations:
    - Disable unnecessary features
    - Enable hardware acceleration
    - Minimal DOM (single SVG element)
    """
    
    __slots__ = ('svg_path', 'web_view', '_paused', '_size')
    
    def __init__(self, svg_path: str, size: int = 64, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self._size = size
        self._paused = False
        self.setFixedSize(size, size)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if HAS_WEBENGINE:
            self.web_view = QWebEngineView(self)
            self._configure_webengine()
            self._load_optimized_svg()
            layout.addWidget(self.web_view)
    
    def _configure_webengine(self):
        """Apply industry-standard WebEngine optimizations."""
        settings = self.web_view.settings()
        
        # Essential: Enable for animations
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        
        # Disable features we don't need (reduces memory/CPU)
        settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, False)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)  # Keep for SVG
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, False)
        settings.setAttribute(QWebEngineSettings.ScreenCaptureEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, False)  # Not needed for SVG
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)  # GPU for 2D
        settings.setAttribute(QWebEngineSettings.PdfViewerEnabled, False)
        
        # Transparent background
        self.web_view.page().setBackgroundColor(QtCore.Qt.transparent)
        self.web_view.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.web_view.setFixedSize(self._size, self._size)
    
    def _load_optimized_svg(self):
        """Load SVG with optimized HTML wrapper."""
        svg_content = _lru_cache_get(_building_svg_content_cache, self.svg_path)
        if svg_content is None:
            try:
                with open(self.svg_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                _lru_cache_set(_building_svg_content_cache, self.svg_path, svg_content)
            except Exception:
                svg_content = '<svg></svg>'
        
        # Optimized HTML: Minimal DOM, GPU-friendly CSS
        html = f'''<!DOCTYPE html>
<html>
<head>
<style>
    * {{ margin: 0; padding: 0; }}
    html, body {{ 
        width: {self._size}px; 
        height: {self._size}px; 
        overflow: hidden;
        background: transparent;
        /* GPU acceleration hint */
        transform: translateZ(0);
        will-change: transform;
    }}
    svg {{
        width: {self._size}px;
        height: {self._size}px;
        /* Hardware layer for animations */
        transform: translateZ(0);
        backface-visibility: hidden;
    }}
</style>
</head>
<body>{svg_content}</body>
</html>'''
        
        base_url = QtCore.QUrl.fromLocalFile(str(Path(self.svg_path).parent) + '/')
        self.web_view.setHtml(html, base_url)
    
    def pause_animations(self):
        """Pause all animations - near-zero CPU when paused."""
        if self._paused:
            return
        self._paused = True
        
        if self.web_view:
            # Industry standard: Pause both CSS and SMIL animations
            self.web_view.page().runJavaScript('''
                document.querySelectorAll('*').forEach(el => {
                    el.style.animationPlayState = 'paused';
                    el.style.webkitAnimationPlayState = 'paused';
                });
                document.querySelectorAll('animate, animateTransform, animateMotion, set').forEach(el => {
                    if (el.pauseAnimations) el.pauseAnimations();
                });
            ''')
    
    def resume_animations(self):
        """Resume animations."""
        if not self._paused:
            return
        self._paused = False
        
        if self.web_view:
            self.web_view.page().runJavaScript('''
                document.querySelectorAll('*').forEach(el => {
                    el.style.animationPlayState = '';
                    el.style.webkitAnimationPlayState = '';
                });
                document.querySelectorAll('animate, animateTransform, animateMotion, set').forEach(el => {
                    if (el.unpauseAnimations) el.unpauseAnimations();
                    else if (el.beginElement) el.beginElement();
                });
            ''')
```

### 6B.8 Visual Quality Enhancements (Low Cost, High Impact)

These effects create visual polish with minimal performance impact:

```python
# city_tab.py - Eye-catching effects

class VisualPolish:
    """
    Visual enhancements that maximize impressiveness while staying lightweight.
    
    Principle: Use CSS/compositor effects, not per-frame CPU work.
    """
    
    @staticmethod
    def apply_completion_glow(cell: QtWidgets.QFrame) -> QtWidgets.QGraphicsDropShadowEffect:
        """
        Subtle animated glow for completed buildings.
        
        GPU-composited drop shadow - very cheap on modern GPUs.
        Creates "magical" completed feel without heavy particles.
        """
        glow = QtWidgets.QGraphicsDropShadowEffect(cell)
        glow.setBlurRadius(15)
        glow.setColor(QtGui.QColor(100, 200, 100, 180))  # Soft green
        glow.setOffset(0, 0)  # Centered glow
        
        # Animate blur radius for pulsing effect
        anim = QtCore.QPropertyAnimation(glow, b"blurRadius")
        anim.setDuration(2000)
        anim.setStartValue(10)
        anim.setEndValue(20)
        anim.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        anim.setLoopCount(-1)
        
        cell.setGraphicsEffect(glow)
        return glow
    
    @staticmethod
    def apply_rarity_border(cell: QtWidgets.QFrame, tier: int) -> None:
        """
        Color-coded borders by building tier.
        
        CSS border - zero runtime cost after initial paint.
        """
        TIER_COLORS = {
            1: "#9e9e9e",  # Common: Gray
            2: "#4caf50",  # Uncommon: Green  
            3: "#2196f3",  # Rare: Blue
            4: "#9c27b0",  # Epic: Purple
            5: "#ff9800",  # Legendary: Gold
        }
        color = TIER_COLORS.get(tier, "#9e9e9e")
        cell.setStyleSheet(f"""
            CityCell {{
                border: 3px solid {color};
                border-radius: 8px;
            }}
        """)
    
    @staticmethod
    def apply_construction_pulse(cell: QtWidgets.QFrame) -> QtWidgets.QGraphicsDropShadowEffect:
        """
        Subtle orange pulse for buildings under construction.
        
        Indicates activity without distracting animation.
        """
        glow = QtWidgets.QGraphicsDropShadowEffect(cell)
        glow.setBlurRadius(8)
        glow.setColor(QtGui.QColor(255, 165, 0, 150))  # Orange
        glow.setOffset(0, 0)
        
        anim = QtCore.QPropertyAnimation(glow, b"blurRadius")
        anim.setDuration(1500)
        anim.setKeyValueAt(0.0, 5)
        anim.setKeyValueAt(0.5, 12)
        anim.setKeyValueAt(1.0, 5)
        anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
        anim.setLoopCount(-1)
        
        cell.setGraphicsEffect(glow)
        return glow


class ProgressRingPainter:
    """
    High-quality progress ring rendering with anti-aliasing.
    
    Industry standard: Pre-render ring segments as cached pixmaps
    for smooth animation without per-frame path computation.
    """
    
    # Pre-computed ring segments (0-100% in 5% increments)
    _ring_cache: dict[int, QtGui.QPixmap] = {}
    
    @classmethod
    def get_ring_pixmap(cls, progress: int, size: int = 72, 
                        color: QtGui.QColor = None) -> QtGui.QPixmap:
        """
        Get cached progress ring pixmap.
        
        Args:
            progress: 0-100 (rounded to nearest 5)
            size: Pixmap size in pixels
            color: Ring color (default orange for construction)
        """
        # Round to 5% for cache efficiency (20 cached variants)
        progress_key = (progress // 5) * 5
        cache_key = f"{progress_key}_{size}"
        
        if cache_key in cls._ring_cache:
            return cls._ring_cache[cache_key]
        
        # Render new ring
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        
        # Ring parameters
        ring_width = 4
        rect = QtCore.QRectF(
            ring_width / 2, ring_width / 2,
            size - ring_width, size - ring_width
        )
        
        # Background ring (gray)
        pen = QtGui.QPen(QtGui.QColor(200, 200, 200, 100), ring_width)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(rect)
        
        # Progress arc (colored)
        if progress_key > 0:
            color = color or QtGui.QColor(255, 165, 0)  # Orange
            pen = QtGui.QPen(color, ring_width)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            painter.setPen(pen)
            
            span_angle = int(progress_key * 3.6 * 16)  # Qt uses 1/16 degrees
            painter.drawArc(rect, 90 * 16, -span_angle)  # Start from top, clockwise
        
        painter.end()
        
        # Cache the result
        cls._ring_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def clear_cache(cls):
        """Clear ring cache (e.g., on color scheme change)."""
        cls._ring_cache.clear()
```

### 6B.9 Celebration Effects (One-Time, High Impact)

```python
# city_tab.py - Completion celebrations

class BuildingCompletionCelebration(QtWidgets.QWidget):
    """
    One-time celebration effect when a building completes.
    
    Industry standard: Particle systems are expensive; use sparingly.
    This implementation creates particles only once (on completion),
    then cleans up after animation finishes.
    """
    
    def __init__(self, parent: QtWidgets.QWidget, building_name: str):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        # Position over the parent cell
        self.setGeometry(parent.geometry())
        
        # Particle state
        self._particles: list[dict] = []
        self._animation_timer = QtCore.QTimer(self)
        self._animation_timer.timeout.connect(self._update_particles)
        self._start_time = 0
        self._duration = 1500  # 1.5 seconds
        
        self._create_particles()
        self.show()
        self._start_animation()
    
    def _create_particles(self):
        """Create confetti particles - limited count for performance."""
        import random
        
        PARTICLE_COUNT = 20  # Industry standard: Keep particle count low
        COLORS = [
            QtGui.QColor(255, 215, 0),   # Gold
            QtGui.QColor(100, 200, 100), # Green
            QtGui.QColor(100, 150, 255), # Blue
            QtGui.QColor(255, 100, 100), # Red
            QtGui.QColor(200, 100, 255), # Purple
        ]
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        for _ in range(PARTICLE_COUNT):
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(50, 150)
            self._particles.append({
                "x": center_x,
                "y": center_y,
                "vx": speed * math.cos(angle),
                "vy": speed * math.sin(angle) - 50,  # Upward bias
                "size": random.uniform(3, 8),
                "color": random.choice(COLORS),
                "rotation": random.uniform(0, 360),
                "rotation_speed": random.uniform(-180, 180),
                "opacity": 1.0,
            })
    
    def _start_animation(self):
        self._start_time = time.perf_counter()
        self._animation_timer.start(16)  # 60 FPS
    
    def _update_particles(self):
        """Update particle physics - runs for limited time only."""
        elapsed = (time.perf_counter() - self._start_time) * 1000
        
        if elapsed >= self._duration:
            self._animation_timer.stop()
            self.close()
            return
        
        progress = elapsed / self._duration
        dt = 0.016  # Assume 60 FPS
        
        for p in self._particles:
            # Physics
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 200 * dt  # Gravity
            p["rotation"] += p["rotation_speed"] * dt
            p["opacity"] = 1.0 - progress  # Fade out
        
        self.update()
    
    def paintEvent(self, event):
        """Draw particles with efficient batched rendering."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        for p in self._particles:
            if p["opacity"] <= 0:
                continue
            
            color = QtGui.QColor(p["color"])
            color.setAlphaF(p["opacity"])
            painter.setBrush(color)
            painter.setPen(QtCore.Qt.NoPen)
            
            painter.save()
            painter.translate(p["x"], p["y"])
            painter.rotate(p["rotation"])
            
            # Draw as small rectangle (faster than circles)
            size = p["size"]
            painter.drawRect(-size/2, -size/2, size, size)
            
            painter.restore()
```

### 6B.10 Performance Monitoring & Profiling

```python
# city_tab.py - Built-in performance monitoring

class PerformanceMonitor:
    """
    Lightweight performance monitoring for development/debugging.
    
    Industry standard: Always include perf monitoring in graphics-heavy systems.
    Can be enabled via config flag without code changes.
    """
    
    _enabled = False
    _frame_times: list[float] = []
    _max_samples = 100
    
    @classmethod
    def enable(cls, enabled: bool = True):
        cls._enabled = enabled
        cls._frame_times.clear()
    
    @classmethod
    def record_frame(cls, frame_time_ms: float):
        if not cls._enabled:
            return
        
        cls._frame_times.append(frame_time_ms)
        if len(cls._frame_times) > cls._max_samples:
            cls._frame_times.pop(0)
    
    @classmethod
    def get_stats(cls) -> dict:
        """Get performance statistics."""
        if not cls._frame_times:
            return {"enabled": cls._enabled, "samples": 0}
        
        times = cls._frame_times
        return {
            "enabled": cls._enabled,
            "samples": len(times),
            "avg_ms": sum(times) / len(times),
            "max_ms": max(times),
            "min_ms": min(times),
            "fps": 1000 / (sum(times) / len(times)) if times else 0,
            "dropped_frames": sum(1 for t in times if t > 16.67),
        }
    
    @classmethod
    def log_summary(cls):
        """Log performance summary to debug log."""
        stats = cls.get_stats()
        if stats.get("samples", 0) > 0:
            _logger.debug(
                "City Performance: FPS=%.1f, Avg=%.1fms, Max=%.1fms, Dropped=%d/%d",
                stats["fps"], stats["avg_ms"], stats["max_ms"],
                stats["dropped_frames"], stats["samples"]
            )


# Integration with AnimationFrameManager
def _performance_wrapper(original_callback: Callable) -> Callable:
    """Wrap animation callback with performance tracking."""
    def wrapped(delta_time: float):
        start = time.perf_counter()
        original_callback(delta_time)
        elapsed_ms = (time.perf_counter() - start) * 1000
        PerformanceMonitor.record_frame(elapsed_ms)
    return wrapped
```

### 6B.11 Memory Management Best Practices

```python
# Industry-standard memory management patterns

class CityTabMemoryOptimized:
    """Memory management patterns for City tab."""
    
    def __init__(self):
        # Weak references for observer patterns
        import weakref
        self._cell_refs: list[weakref.ref] = []
    
    def _cleanup_stale_refs(self):
        """Periodically clean up dead weak references."""
        self._cell_refs = [ref for ref in self._cell_refs if ref() is not None]
    
    def _on_low_memory(self):
        """
        Called when system signals low memory.
        
        Industry standard: Implement graceful degradation.
        """
        # Clear all caches
        clear_building_caches()
        ProgressRingPainter.clear_cache()
        _pixmap_pool._pool.clear()
        
        # Stop non-essential animations
        for ref in self._cell_refs:
            cell = ref()
            if cell and hasattr(cell, 'pause_animations'):
                cell.pause_animations()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        _logger.info("City tab: Low memory cleanup completed")


# Memory usage estimation
def estimate_city_memory_usage() -> dict:
    """Estimate current memory usage of City system."""
    import sys
    
    cache_stats = get_cache_stats()
    
    # Rough estimates
    renderer_size = cache_stats["renderers"] * 50_000  # ~50KB per renderer
    pixmap_size = cache_stats["pixmaps"] * 20_000      # ~20KB per pixmap
    svg_content_size = cache_stats["svg_content"] * 5_000  # ~5KB per SVG
    
    return {
        "renderer_cache_kb": renderer_size // 1024,
        "pixmap_cache_kb": pixmap_size // 1024,
        "svg_content_cache_kb": svg_content_size // 1024,
        "total_estimated_kb": (renderer_size + pixmap_size + svg_content_size) // 1024,
    }
```

### 6B.12 Quality vs Performance Configuration

```python
# Quality presets for different system capabilities

class QualityPreset:
    """
    Quality presets that balance visuals vs performance.
    
    Industry standard: Provide user-selectable quality levels.
    """
    
    LOW = {
        "animation_enabled": False,           # No animations
        "glow_effects_enabled": False,        # No GPU glow
        "particle_effects_enabled": False,    # No particles
        "progress_ring_segments": 4,          # Coarse rings
        "webengine_enabled": False,           # Static SVGs only
        "max_cache_size": 20,                 # Smaller cache
    }
    
    MEDIUM = {
        "animation_enabled": True,
        "glow_effects_enabled": True,
        "particle_effects_enabled": False,    # Skip particles
        "progress_ring_segments": 10,
        "webengine_enabled": True,
        "max_cache_size": 35,
    }
    
    HIGH = {
        "animation_enabled": True,
        "glow_effects_enabled": True,
        "particle_effects_enabled": True,
        "progress_ring_segments": 20,         # Smooth rings
        "webengine_enabled": True,
        "max_cache_size": 50,
    }
    
    @classmethod
    def detect_recommended(cls) -> dict:
        """
        Auto-detect recommended quality based on system.
        
        Industry standard: Adapt to hardware capabilities.
        """
        import platform
        
        # Check for known low-power scenarios
        if platform.system() == "Windows":
            try:
                import psutil
                memory_gb = psutil.virtual_memory().total / (1024 ** 3)
                cpu_count = psutil.cpu_count()
                
                if memory_gb < 4 or cpu_count < 4:
                    return cls.LOW
                elif memory_gb < 8:
                    return cls.MEDIUM
                else:
                    return cls.HIGH
            except ImportError:
                pass
        
        # Default to medium
        return cls.MEDIUM
```

---

## 7. Entity Perk Integration (Optional Future)

Potential entity perks for City system:

```python
# In entity_perks.py (future addition)
PerkType.CITY_RESOURCE_BONUS = "city_resource_bonus"    # +X% resources
PerkType.CITY_BUILD_SPEED = "city_build_speed"          # -X% requirements
PerkType.CITY_INCOME_BONUS = "city_income_bonus"        # +X% passive income
```

---

## 8. Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)
1. Create `city/` package with data structures
2. Implement `city_manager.py` core functions
3. Add city data to config persistence
4. Add resource generation hooks to existing tabs
5. Create `city_svg_cache.py` with LRU cache utilities

### Phase 2: SVG Assets (Days 3-4)
1. Design 11 building SVGs (static, 64x64 viewBox)
2. Create animated versions for completed buildings:
   - Farm: windmill rotation
   - Well: water ripple
   - Workshop: hammer swing, sparks
   - Library: page turning
   - Mint: coin shimmer
   - Wonder: particle celebration
3. Create overlay assets (_construction.svg, _locked.svg)
4. Test WebEngine rendering with SMIL/CSS animations

### Phase 3: Basic UI (Days 5-6)
1. Create `city_tab.py` with resource display
2. Implement `BuildingCard` with three visual states
3. Implement `AnimatedBuildingWidget` with QWebEngineView
4. Add construction progress visualization
5. Add "Invest" functionality with progress bar animations

### Phase 4: Animation Lifecycle (Day 7)
1. Implement `showEvent`/`hideEvent` handlers
2. Add `on_window_minimized`/`on_window_restored` hooks
3. Wire up to main window minimize/restore events
4. Test animation freeze/resume across tab switches
5. Verify CPU usage drops to ~0 when tab hidden

### Phase 5: Income System (Days 8-9)
1. Implement passive income collection
2. Add "Collect" button with animation
3. Integrate with existing coin/XP systems
4. Add to game_state.py signals

### Phase 6: Polish (Days 10-12)
1. Building unlock animations (confetti, sound)
2. Completion celebrations (similar to Entitidex)
3. Construction start/invest particle effects
4. Tutorial/help text with tooltips
5. Unit tests for cache, lifecycle, state
6. Performance profiling and optimization

---

## 9. Balance Considerations

### 9.1 Resource Generation Rate

Assuming average user behavior per day:
- 5 glasses of water → 5 WATER
- 1 weight log (on target) → 2 MATERIALS
- 1-2 activity logs → 2-4 ACTIVITY
- 60 min focus → 2 FOCUS

**Daily Total**: ~5 WATER, ~2 MATERIALS, ~3 ACTIVITY, ~2 FOCUS

### 9.2 Building Completion Time

| Building | Tier | Cost | Days to Complete | Effect at Max Level |
|----------|------|------|------------------|---------------------|
| **Goldmine** | 1 | 3W + 5M + 2F | ~2 days | +3 coins/hour (72/day) |
| **Forge** | 2 | 10W + 20M + 10A + 10F | ~8 days | +15% merge success |
| **Artisan Guild** | 2 | 15W + 15M + 5A + 15F | ~10 days | +11% rarity bias |
| **University** | 2 | 15W + 10M + 5A + 25F | ~12 days | +10% entity catch |
| **Training Ground** | 3 | 25W + 20M + 40A + 15F | ~20 days | +11% hero power |
| **Library** | 3 | 20W + 30M + 10A + 50F | ~25 days | +17% XP bonus |
| **Market** | 3 | 30W + 40M + 20A + 25F | ~25 days | -17% coin costs |
| **Royal Mint** | 4 | 60W + 100M + 40A + 60F | ~50 days | +23 coins/hour (552/day) |
| **Observatory** | 4 | 40W + 60M + 20A + 100F | ~55 days | +20% entity encounters |
| **Wonder** | 5 | 150W + 200M + 100A + 200F | ~120 days | ALL bonuses combined! |

### 9.3 Cumulative Bonuses (Fully Built City at Max Levels)

| Bonus Type | Total from Buildings | Stacks With |
|------------|---------------------|-------------|
| **Passive Income** | 36 coins/hour (864/day)* | N/A |
| **Merge Success** | +20% | Item merge_luck, consumables |
| **Rarity Bias** | +16% | Entity RARITY_BIAS perks |
| **Entity Catch** | +15% | Item luck, pity system |
| **Entity Encounters** | +20% | Story bonuses |
| **Hero Power** | +16% | Gear, entity power perks |
| **XP Bonus** | +27% | Entity XP perks |
| **Coin Discount** | -17% | Entity coin_discount perks |

*Breakdown: Goldmine L5 (3/hr) + Royal Mint L10 (23/hr) + Wonder (10/hr) = 36/hr

### 9.4 Balance Analysis

**Why gameplay modifiers > pure passive income:**
1. **Engagement**: Bonuses amplify active play, not replace it
2. **Synergy**: Stack with entities → encourages collecting
3. **Meaningful choice**: Build Forge OR Artisan Guild first?
4. **Long-term goals**: Max-level buildings take months of consistency

**Power Curve Check:**
- Early game (Day 10): Goldmine + Forge = +72 coins/day, +5% merge
- Mid game (Day 60): Most Tier 2-3 = +10% catch, +11% rarity, +17% XP
- End game (Day 150+): Full city = significant but not game-breaking bonuses

**Comparison to existing systems:**
- Entity perks: Max ~15% luck, ~15% rarity (rare entities)
- City bonuses: Comparable but requires investment
- Combined: ~30% for each stat = meaningful progression ceiling

---

## 10. Summary

The City system adds:

1. **1×10 Horizontal Grid Layout**: Visual city with 10 building slots (unlocked progressively by level)
2. **10 Independent Buildings**: No prerequisites, build any building if you have resources
3. **Gameplay Modifiers**: Buildings affect merge, catch, rarity, XP, power
4. **Passive Income**: Goldmine + Royal Mint for coin generation
5. **Visual Progression**: Watch buildings construct and animate when complete
6. **Theme-Neutral**: Works across all story modes
7. **Animated Graphics**: SMIL/CSS animated SVGs for completed buildings
8. **Performance Optimized**: GPU-accelerated, 60 FPS target, near-zero CPU when hidden

The system is designed to be:
- **Progressive** (1×10 grid with slots unlocking at specific levels: 2, 4, 6, 9, 13, 18, 24, 31, 39, 40)
- **Independent** (no building prerequisites - freedom of choice)
- **Balanced** (months to complete, amplifies but doesn't replace active play)
- **Engaging** (visual construction progress, upgrade paths)
- **Synergistic** (city bonuses + entity perks stack meaningfully)
- **Maintainable** (modular code structure, clean integration points)
- **Performant** (LRU caching, GPU compositing, animation lifecycle, quality presets)
- **Visually Impressive** (glow effects, progress rings, completion celebrations)

### Grid Design Philosophy

| Aspect | Decision |
|--------|----------|
| **Grid Size** | 1×10 = 10 cells (matches 10 unique buildings) |
| **Slot Unlocking** | Progressive: Lv2, Lv4, Lv6, Lv9, Lv13, Lv18, Lv24, Lv31, Lv39, Lv40 |
| **Independence** | No prerequisites - player chooses build order |
| **Placement** | Player picks cell location (cosmetic only) |
| **Uniqueness** | Each building can only be placed once |
| **Hidden Slots** | Locked slots are hidden in UI (appear as you level up) |

### Building Philosophy

| Building | Philosophy |
|----------|-----------|
| **Goldmine** | First building - teaches passive income concept |
| **Forge** | Core gameplay - merge is central to progression |
| **Artisan Guild** | Quality of life - better drops without more grinding |
| **University** | Entity collection - knowledge helps you bond |
| **Training Ground** | Power scaling - fitness makes you stronger |
| **Library** | XP acceleration - knowledge speeds leveling |
| **Market** | Economy - trade reduces costs |
| **Royal Mint** | Endgame income - rewards long-term consistency |
| **Observatory** | Entity encounters - see more, catch more |
| **Wonder** | Ultimate goal - proof of discipline mastery |

### Performance Targets & Optimizations

| Target | Goal | Implementation |
|--------|------|----------------|
| **Frame Rate** | 60 FPS (16.67ms) | GPU-accelerated animations, compositor layers |
| **Memory (Idle)** | < 50 MB | LRU caching, object pooling, weak refs |
| **Memory (Active)** | < 80 MB peak | Pixmap pooling, cache eviction |
| **CPU (Hidden)** | ~0% (< 0.5%) | Animation pause on tab hide/minimize |
| **CPU (Visible)** | < 5% | Single frame manager, batched updates |
| **Startup** | < 100ms | Lazy initialization, deferred loading |

### Visual Quality Features

| Feature | Implementation | Cost |
|---------|---------------|------|
| **Glow Effects** | QGraphicsDropShadowEffect | GPU-composited, low CPU |
| **Progress Rings** | Pre-cached pixmaps (5% intervals) | Zero runtime calculation |
| **Tier Borders** | CSS border colors | Zero runtime cost |
| **Completion Particles** | One-time, 1.5s, 20 particles | Self-cleanup after animation |
| **Shimmer/Pulse** | Opacity animations | GPU-composited |
| **SVG Animations** | SMIL/CSS in WebEngine | Browser-optimized |

### Technical Highlights

| Feature | Implementation |
|---------|---------------|
| **Grid Layout** | 5×5 QGridLayout of CityCell widgets |
| **Cell States** | Empty → Placed → Building → Complete |
| **Progress Ring** | Cached pixmaps, circular arc rendering |
| **SVG Graphics** | QWebEngineView with SMIL/CSS animations |
| **GPU Acceleration** | will-change, translateZ(0), compositor hints |
| **Fallback** | QSvgWidget when WebEngine unavailable |
| **Caching** | OrderedDict LRU cache (50 items) |
| **Animation Lifecycle** | pause/resume on visibility changes |
| **Quality Presets** | Low/Medium/High with auto-detect |
| **Performance Monitoring** | Built-in frame time tracking |
| **Memory Management** | Pixmap pooling, weak refs, GC triggers |

---

## 11. Integration Verification Checklist

**Pre-Implementation Verification:**

| Check | File | What to Verify |
|-------|------|----------------|
| ✅ Config persistence | `core_logic.py` | `adhd_buster` auto-saves new `city` key |
| ✅ Game state signals | `game_state.py` | Add 4 new signals (see Section 4.2) |
| ✅ Deferred imports | `focus_blocker_qt.py` | Add `CITY_AVAILABLE` flag pattern |
| ✅ Tab registration | `focus_blocker_qt.py` | Use `CityTab(self.blocker, self)` |
| ✅ Hydration hook | `focus_blocker_qt.py` | Add to `_log_water()` with try/except |
| ✅ Weight hook | `focus_blocker_qt.py` | Add to `_log_weight()` with try/except |
| ✅ Activity hook | `focus_blocker_qt.py` | Add to `_log_activity()` with try/except |
| ✅ Focus hook | `focus_blocker_qt.py` | Add to `_give_session_rewards()` |
| ✅ Merge bonus | `gamification.py` | Add `city_bonus` param to `calculate_merge_success_rate()` |
| ✅ Catch bonus | `catch_mechanics.py` | Add `city_bonus` param to `get_final_probability()` |
| ✅ Combined perks | `gamification.py` | Add `get_all_perk_bonuses()` helper |

**Post-Implementation Smoke Tests:**

| Test | Expected Result |
|------|-----------------|
| Start app without city/ folder | App starts normally, CITY_AVAILABLE=False |
| Log water | No crash, +1 Water resource (if city available) |
| Log weight on-target | No crash, +2 Materials resource |
| Complete 30min focus | No crash, +1 Focus resource |
| Open City tab | Lazy init, grid displays, no WebEngine per cell |
| Place building | Cell updates, config saves |
| Invest resources | Progress updates, batch save works |
| Complete building | Status=COMPLETE, bonuses apply |
| Merge items | City merge_success_bonus applied |
| Entity encounter | City entity_catch_bonus applied |
| Minimize app | Animations pause, CPU drops |
| Restore app | Animations resume |
| Switch away from City tab | Selection panel animation pauses |

**Backward Compatibility Guarantees:**

| Aspect | Guarantee |
|--------|-----------|
| **Old configs** | Missing `city` key → auto-initialized with defaults |
| **Function signatures** | All new params have defaults (city_bonus=0) |
| **Missing module** | CITY_AVAILABLE=False → all hooks skip gracefully |
| **Signal connections** | New signals only emitted if listeners exist |
| **Batch mode** | Works with or without game_state parameter |

---

*Design Document v1.9 - 2026-01-25*

**Changelog:**
- v1.9: Final Scrutiny & API Alignment
  - **Fixed Function Name**: `calculate_level_from_xp()` → `get_level_from_xp()[0]` (actual gamification.py API)
  - **Added Missing Import**: `from city.city_synergies import get_all_synergy_bonuses` in get_city_bonuses()
  - **Clarified Grid Diagram**: Changed `[Locked]` → `[Placed]` to avoid confusion with type restrictions
  - **Improved UI Display**: "Building Slots: 4/6" → "🏠 4/6 Buildings" for clarity
  - **Added Synergy Math Comment**: Clarified that synergy_value is 0.0-0.5 multiplier on base percentages
  - **Added Design Note**: "Building TYPES are never locked. Only building SLOTS are level-gated."
- v1.8: Entity Synergies & Level-Gated Slots
  - **Level-Gated Building Slots**: XP level determines max buildings (2 at L1, +1 every 5 levels, 10 at L40)
  - **Goldmine + Forge Starter**: Both available immediately at Level 1 to teach mechanics
  - **BUILDING_SLOT_UNLOCKS**: New constant mapping level thresholds → slot counts
  - **Slot Management Functions**: `get_max_building_slots()`, `get_available_slots()`, `get_next_slot_unlock()`
  - **Entity-Building Synergy System**: Thematic entities boost matching buildings (+5% normal, +10% exceptional)
  - **BUILDING_SYNERGIES**: New mapping with SynergyMapping dataclass per building
  - **Synergy Categories**: Goldmine←mining, University←knowledge/books/owl, Observatory←stars/vision/eyes, etc.
  - **Synergy Cap**: +50% max bonus per building (prevents overpowered stacking)
  - **Wonder Special**: Only legendary entities contribute, boosts ALL effects
  - **synergy_tags Field**: New entity dataclass field for future entity definitions
  - **get_all_synergy_bonuses()**: Returns synergy dict matching `get_city_bonuses()` structure
  - **UI Examples**: Building slot counter in header, synergy contributor list in building panel
- v1.7: Seamless Integration Audit (Breaking Change Prevention)
  - **get_city_bonuses() Fixed**: Now scans grid (source of truth), not separate buildings dict
  - **Deferred Import Pattern**: Added CITY_AVAILABLE flag + module-level placeholders
  - **Tab Registration Fixed**: Constructor now matches pattern `CityTab(blocker, self)`
  - **Resource Hook Pattern**: Matches exact `_log_water()` game_state access pattern
  - **Batch Mode Support**: `invest_resources()` uses `begin_batch/end_batch` for atomic updates
  - **Combined Perk Helper**: Added `get_all_perk_bonuses()` for unified entity+city bonuses
  - **Graceful Degradation**: All hooks wrapped in try/except to prevent breaking existing features
  - **Signal Emission Pattern**: Uses `game_state._emit()` matching existing signal pattern
- v1.6: Expert Review II (UX & Future-Proofing)
  - **Pending Income Preview**: Added `get_pending_income()` read-only helper; Collect button shows "Collect 45 Coins"
  - **Configurable Offline Cap**: Extracted `MAX_OFFLINE_HOURS = 24` constant for future building extensions
  - **Demolish Function**: Added `demolish_building()` with `DEMOLISH_REFUND_PERCENT = 25` resource return
  - **Resource Toast Notifications**: `add_city_resource()` emits `city_resource_earned` signal for habit→reward feedback
  - **Upgrade Visual Continuity**: Construction cells now overlay scaffolding on building SVG (not blank foundation)
  - **Selection Panel BUILDING State**: Explicit handling - grayscale filter on static SVG + progress bars
  - **_update_collect_button()**: Polls pending income to show exact coin amount on button label
- v1.5: Expert Review Implementation (Architecture Hardening)
  - **Unified Persistence Model**: Grid is now THE SINGLE SOURCE OF TRUTH; removed dual `placed_buildings` storage
  - **Explicit CellStatus Enum**: PLACED, BUILDING, COMPLETE states replace inferred `completed` boolean
  - **Removed Prerequisite Logic**: `can_place_building()` now checks uniqueness only (no prerequisites per design)
  - **Fixed Income Math**: Corrected 26→36 coins/hour (Goldmine 3 + Royal Mint 23 + Wonder 10)
  - **Fixed List Multiplication Bug**: Added warning about `[[None]*5]*5` pattern; use comprehensions
  - **WebEngine Limit**: Added critical guidance - max 1 shared view in selection panel only
  - **Animation Contradiction Fix**: Changed to "opacity only - never geometry" to match Qt reality
  - **Unified Income Model**: Removed `generation` block; use `effect.coins_per_hour * hours` everywhere
  - **Upgrade Requirements**: Added `get_level_requirements()` with 1.2^(level-1) scaling factor
  - **Move/Swap Mode**: Added `move_building()` function for cell rearrangement
  - **Grid-Based API**: Rewrote `city_manager.py` with `place_building()`, `invest_resources()`, `start_upgrade()` functions
  - **CityTab Cleanup**: Removed dead code, use manager functions for all state changes
  - **get_placed_buildings() Helper**: Derive placed building list from grid scan (no separate storage)
- v1.4: Advanced Performance & Visual Quality Architecture (Section 6B)
  - GPU acceleration patterns and compositor layer hints
  - Centralized AnimationFrameManager (single timer for all cells)
  - PixmapPool for memory-efficient progress rings
  - Optimized WebEngine settings (disable unused features)
  - VisualPolish effects (glow, shimmer, tier borders)
  - Pre-cached ProgressRingPainter (20 cached variants)
  - BuildingCompletionCelebration (limited particles, auto-cleanup)
  - PerformanceMonitor for frame time tracking
  - Memory management patterns (weak refs, low-memory handler)
  - QualityPreset system with auto-detection
  - SVG optimization guide (SVGO pre-build pipeline)
  - Industry-standard benchmarks and targets
- v1.3: Grid-based layout (5×5), independent buildings, CityCell/CityGrid widgets
- v1.2: Gameplay modifier buildings (Goldmine, Forge, Artisan Guild, University, Observatory)
- v1.1: Added SVG Graphics Architecture (Section 6A)
- v1.0: Initial design with resource system and building definitions

