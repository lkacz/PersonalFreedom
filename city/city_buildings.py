"""
City Building System - Building Definitions
============================================
All 10 building configurations with requirements, effects, and scaling.
"""

from typing import Dict, Any

# ============================================================================
# BUILDING DEFINITIONS
# ============================================================================

CITY_BUILDINGS: Dict[str, Dict[str, Any]] = {
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
        "completion_reward": {"coins": 150, "xp": 400},
        "effect": {
            "type": "power_bonus",
            "power_percent": 3,  # +3% hero power
        },
        "max_level": 5,
        "level_scaling": {
            "power_percent": 2,  # +2% per level (L5 = +11% total power)
        },
        "visual": "training_ground",
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
        "completion_reward": {"coins": 200, "xp": 500},
        "effect": {
            "type": "xp_bonus",
            "bonus_percent": 5,  # +5% XP from all sources
        },
        "max_level": 5,
        "level_scaling": {
            "bonus_percent": 3,  # +3% per level (L5 = +17% total XP bonus)
        },
        "visual": "library",
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
        "completion_reward": {"coins": 300, "xp": 350},
        "effect": {
            "type": "coin_discount",
            "discount_percent": 5,  # -5% coin costs
        },
        "max_level": 5,
        "level_scaling": {
            "discount_percent": 3,  # +3% per level (L5 = -17% costs)
        },
        "visual": "market",
    },
    
    # =========================================================================
    # TIER 4 - PREMIUM BUILDINGS (High investment, strong effects)
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
            "focus": 100,  # Heavy focus requirement
        },
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
        "level_scaling": {},  # No scaling for Wonder
        "visual": "wonder",
    },
}


def get_building_by_id(building_id: str) -> Dict[str, Any]:
    """Get building definition by ID."""
    return CITY_BUILDINGS.get(building_id, {})


def get_all_building_ids() -> list:
    """Get list of all building IDs."""
    return list(CITY_BUILDINGS.keys())


def get_buildings_by_tier(tier: int) -> list:
    """Get all buildings of a specific tier."""
    return [
        b for b in CITY_BUILDINGS.values()
        if b.get("tier") == tier
    ]
