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
        "description": "Strike gold! Mining requires real effort - only moderate or higher intensity physical activities will unearth coins.",
        "tier": 1,
        "requirements": {
            "water": 3,
            "materials": 2,
            "scrap": 3,
            "activity": 0,
            "focus": 2,
        },
        "completion_reward": {"coins": 50, "xp": 25},
        "effect": {
            "type": "activity_triggered_income",
            "trigger": "exercise",  # Triggers on activity log with moderate+ intensity
            "min_intensity": "moderate",  # Requires moderate, vigorous, or intense
            "base_coins": 3,  # Base coins per qualifying activity
            "coins_per_effective_30min": 2,  # +2 coins per 30 effective minutes
        },
        "max_level": 3,
        "level_scaling": {
            "base_coins": 2,  # +2 base per level (L3 = 7 base coins)
            "coins_per_effective_30min": 2,  # +2 per level (L3 = 6 per 30min)
        },
        "visual": "goldmine",
    },
    
    # =========================================================================
    # TIER 2 - GAMEPLAY MODIFIER BUILDINGS (Core bonuses, moderate requirements)
    # =========================================================================
    "forge": {
        "id": "forge",
        "name": "🔥 Forge",
        "description": "Master smiths improve your merge outcomes and salvage technique.",
        "tier": 2,
        "requirements": {
            "water": 10,
            "materials": 6,
            "scrap": 14,
            "activity": 10,
            "focus": 10,
        },
        "completion_reward": {"coins": 100, "xp": 150},
        "effect": {
            "type": "multi",
            "bonuses": {
                "merge_success_bonus": 5,  # +5% merge success rate
                "scrap_chance_bonus": 2,   # +2% scrap chance from merges
            },
        },
        "max_level": 3,
        "level_scaling": {
            "merge_success_bonus": 4,  # +4% per level (L3 = +13% total)
            "scrap_chance_bonus": 1.5, # +1.5% per level (L3 = +5% total)
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
            "materials": 5,
            "scrap": 10,
            "activity": 5,
            "focus": 15,
        },
        "completion_reward": {"coins": 75, "xp": 200},
        "effect": {
            "type": "rarity_bias_bonus",
            "bonus_percent": 3,  # +3% chance for higher rarity items
        },
        "max_level": 3,
        "level_scaling": {
            "bonus_percent": 3,  # +3% per level (L3 = +9% total rarity bias)
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
            "materials": 3,
            "scrap": 7,
            "activity": 5,
            "focus": 25,  # Knowledge requires focus
        },
        "completion_reward": {"coins": 50, "xp": 300},
        "effect": {
            "type": "entity_catch_bonus",
            "bonus_percent": 3,  # +3% entity catch probability
        },
        "max_level": 3,
        "level_scaling": {
            "bonus_percent": 3,  # +3% per level (L3 = +9% total catch bonus)
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
            "materials": 6,
            "scrap": 14,
            "activity": 40,  # Heavy activity requirement
            "focus": 15,
        },
        "completion_reward": {"coins": 150, "xp": 400},
        "effect": {
            "type": "power_bonus",
            "power_percent": 3,  # +3% hero power
        },
        "max_level": 3,
        "level_scaling": {
            "power_percent": 3,  # +3% per level (L3 = +9% total power)
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
            "materials": 9,
            "scrap": 21,
            "activity": 10,
            "focus": 50,  # Heavy focus requirement
        },
        "completion_reward": {"coins": 200, "xp": 500},
        "effect": {
            "type": "xp_bonus",
            "bonus_percent": 5,  # +5% XP from all sources
        },
        "max_level": 3,
        "level_scaling": {
            "bonus_percent": 5,  # +5% per level (L3 = +15% total XP bonus)
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
            "materials": 12,
            "scrap": 28,
            "activity": 20,
            "focus": 25,
        },
        "completion_reward": {"coins": 300, "xp": 350},
        "effect": {
            "type": "coin_discount",
            "discount_percent": 5,  # -5% coin costs
        },
        "max_level": 3,
        "level_scaling": {
            "discount_percent": 5,  # +5% per level (L3 = -15% costs)
        },
        "visual": "market",
    },
    
    # =========================================================================
    # TIER 4 - PREMIUM BUILDINGS (High investment, strong effects)
    # =========================================================================
    "royal_mint": {
        "id": "royal_mint",
        "name": "🏛️ Royal Mint",
        "description": "The economic heart of your city. Generates coins when you complete focus sessions.",
        "tier": 4,
        "requirements": {
            "water": 60,
            "materials": 30,
            "scrap": 70,
            "activity": 40,
            "focus": 60,
        },
        "completion_reward": {"coins": 1000, "xp": 750},
        "effect": {
            "type": "focus_session_income",
            "trigger": "focus_session",  # Triggers on focus session completion
            "base_coins": 5,  # Base coins per session
            "coins_per_30min": 3,  # +3 coins per 30 minutes of focus
        },
        "max_level": 3,
        "level_scaling": {
            "base_coins": 5,  # +5 base per level (L3 = 15 base coins)
            "coins_per_30min": 3,  # +3 per level (L3 = 9 per 30min)
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
            "materials": 18,
            "scrap": 42,
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
            "materials": 60,
            "scrap": 140,
            "activity": 100,
            "focus": 200,
        },
        "completion_reward": {"coins": 5000, "xp": 10000},
        "effect": {
            "type": "multi",
            "bonuses": {
                "focus_session_coins": 5,   # Coins on focus session completion
                "exercise_coins": 5,        # Coins on exercise
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
