"""
Entity Perk System for Entitidex
================================
Manages persistent passive bonuses from collected entities.

Each collected entity provides a "Small but Noticeable" perk.
Exceptional variants provide an enhanced version of the same perk.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum, auto

# Avoid circular imports - we only need the interface of EntitidexProgress
# passed at runtime, so we don't import it here directly if not needed for type hinting.
# For type hinting, we can use string forward reference or TYPE_CHECKING block.


class PerkType(Enum):
    """Types of bonuses granted by entities."""
    # HERO POWER
    POWER_FLAT = "power_flat"              # +X hero power
    
    # COIN ECONOMY
    COIN_FLAT = "coin_flat"                # +X coins per session
    COIN_PERCENT = "coin_percent"          # +X% coin gains from all sources
    COIN_DISCOUNT = "coin_discount"        # -X flat coin cost reduction on operations
    
    # XP & PROGRESSION
    XP_PERCENT = "xp_percent"              # +X% XP gains
    SESSION_XP = "session_xp"              # +X% XP specifically from focus sessions
    STORY_XP = "story_xp"                  # +X% XP from story rewards
    
    # LUCK & RNG
    MERGE_LUCK = "merge_luck"              # +X% success rate in gear merging
    DROP_LUCK = "drop_luck"                # +X% chance for item drops
    ITEM_RARITY = "item_rarity"            # +X% chance upgrade (needs specific rarity context)
    UNCOMMON_CHANCE = "uncommon_chance"    # +X% specifically for uncommon
    RARE_CHANCE = "rare_chance"            # +X% specifically for rare
    EPIC_CHANCE = "epic_chance"            # +X% specifically for epic
    LEGENDARY_CHANCE = "legendary_chance"  # +X% specifically for legendary
    
    # ENTITY ENCOUNTERS
    ENCOUNTER_CHANCE = "encounter_chance"  # +X% chance to find entity after session
    CAPTURE_BONUS = "capture_bonus"        # +X% probability to catch entity
    PITY_BONUS = "pity_bonus"              # +X% multiplier to pity system
    
    # QUALITY OF LIFE
    HYDRATION_COOLDOWN = "hydration_cd"    # -X minutes to hydration reminder cooldown
    HYDRATION_CAP = "hydration_cap"        # +X to daily water glass cap
    INVENTORY_SLOTS = "inventory_slots"    # +X inventory slots (not yet fully implemented)
    EYE_REST_CAP = "eye_rest_cap"          # +X to daily eye rest claim limit
    SESSION_EXT = "session_ext"            # +X minutes allowable extension
    STREAK_SAVE = "streak_save"            # +X% chance to save streak on miss


@dataclass
class EntityPerk:
    """Defines a perk granted by a specific entity."""
    entity_id: str
    perk_type: PerkType
    normal_value: float       # Value granted by normal variant
    exceptional_value: float  # Value granted by exceptional variant (replaces normal)
    description: str          # Description template, e.g., "+{value} Hero Power"
    icon: str = "✨"          # Emoji icon for the perk


# =============================================================================
# PERK DEFINITIONS - THE SOURCE OF TRUTH
# =============================================================================

ENTITY_PERKS: Dict[str, EntityPerk] = {
    # -------------------------------------------------------------------------
    # WARRIOR POOL (Power & Combat)
    # -------------------------------------------------------------------------
    "warrior_001": EntityPerk("warrior_001", PerkType.POWER_FLAT, 1, 2, "+{value} Hero Power", "💥"),
    "warrior_002": EntityPerk("warrior_002", PerkType.POWER_FLAT, 5, 10, "+{value} Hero Power", "🪵"),
    "warrior_003": EntityPerk("warrior_003", PerkType.ENCOUNTER_CHANCE, 1, 2, "+{value}% Encounter Chance", "🦅"),
    "warrior_004": EntityPerk("warrior_004", PerkType.HYDRATION_COOLDOWN, 5, 10, "-{value}m Hydration Cooldown", "🐴"),
    "warrior_005": EntityPerk("warrior_005", PerkType.POWER_FLAT, 3, 6, "+{value} Hero Power", "🔥"),
    "warrior_006": EntityPerk("warrior_006", PerkType.SESSION_XP, 2, 4, "+{value}% Session XP", "🚩"),
    "warrior_007": EntityPerk("warrior_007", PerkType.POWER_FLAT, 5, 10, "+{value} Hero Power", "🐲"),
    "warrior_008": EntityPerk("warrior_008", PerkType.CAPTURE_BONUS, 5, 8, "+{value}% Capture Probability", "🐺"),
    "warrior_009": EntityPerk("warrior_009", PerkType.POWER_FLAT, 10, 15, "+{value} Hero Power", "👑"),

    # -------------------------------------------------------------------------
    # SCHOLAR POOL (Knowledge & XP)
    # -------------------------------------------------------------------------
    "scholar_001": EntityPerk("scholar_001", PerkType.SESSION_XP, 1, 2, "+{value}% Session XP", "🐭"),
    "scholar_002": EntityPerk("scholar_002", PerkType.XP_PERCENT, 2, 4, "+{value}% XP (Night Bonus)", "🦉"), # Simplified to general XP for now
    "scholar_003": EntityPerk("scholar_003", PerkType.SESSION_EXT, 5, 10, "+{value}m Session Extension", "🕯️"),
    "scholar_004": EntityPerk("scholar_004", PerkType.DROP_LUCK, 1, 2, "+{value}% Item Drop Luck", "🐈"),
    "scholar_005": EntityPerk("scholar_005", PerkType.MERGE_LUCK, 1, 2, "+{value}% Merge Luck", "🔖"),
    "scholar_006": EntityPerk("scholar_006", PerkType.SESSION_XP, 2, 4, "+{value}% Session XP", "📖"),
    "scholar_007": EntityPerk("scholar_007", PerkType.RARE_CHANCE, 1, 2, "+{value}% Rare Encounter Bias", "🗺️"), # Approximated
    "scholar_008": EntityPerk("scholar_008", PerkType.STORY_XP, 5, 8, "+{value}% Story XP", "🦅"),
    "scholar_009": EntityPerk("scholar_009", PerkType.XP_PERCENT, 5, 8, "+{value}% All XP Gains", "📜"),

    # -------------------------------------------------------------------------
    # WANDERER POOL (Travel & Coins)
    # -------------------------------------------------------------------------
    "wanderer_001": EntityPerk("wanderer_001", PerkType.COIN_FLAT, 1, 2, "+{value} Coin per Session", "🪙"),
    "wanderer_002": EntityPerk("wanderer_002", PerkType.STREAK_SAVE, 1, 2, "+{value}% Streak Save Chance", "🧭"),
    "wanderer_003": EntityPerk("wanderer_003", PerkType.COIN_FLAT, 2, 4, "+{value} Coins (Streak Bonus)", "📓"), # Simplified
    "wanderer_004": EntityPerk("wanderer_004", PerkType.HYDRATION_COOLDOWN, 5, 10, "-{value}m Hydration Cooldown", "🐕"),
    "wanderer_005": EntityPerk("wanderer_005", PerkType.COIN_PERCENT, 5, 10, "+{value}% Perfect Session Coins", "🗺️"), # Simplified
    "wanderer_006": EntityPerk("wanderer_006", PerkType.HYDRATION_CAP, 1, 1, "+{value} Daily Water Cap", "🐎"),
    "wanderer_007": EntityPerk("wanderer_007", PerkType.INVENTORY_SLOTS, 1, 2, "+{value} Inventory Slot", "🎒"),
    "wanderer_008": EntityPerk("wanderer_008", PerkType.COIN_FLAT, 2, 4, "+{value} Coins per Session", "🎈"),
    "wanderer_009": EntityPerk("wanderer_009", PerkType.COIN_PERCENT, 5, 8, "+{value}% All Coin Gains", "🐀"),

    # -------------------------------------------------------------------------
    # UNDERDOG POOL (Workplace & Luck)
    # -------------------------------------------------------------------------
    "underdog_001": EntityPerk("underdog_001", PerkType.DROP_LUCK, 1, 2, "+{value}% Item Drop Chance", "👔"),
    "underdog_002": EntityPerk("underdog_002", PerkType.MERGE_LUCK, 1, 2, "+{value}% Merge Luck", "📝"),
    "underdog_003": EntityPerk("underdog_003", PerkType.COIN_DISCOUNT, 1, 2, "-{value} Coin Cost (All Actions)", "🎰"),
    "underdog_004": EntityPerk("underdog_004", PerkType.COIN_FLAT, 1, 2, "+{value} Coin on Salvage", "🐦"), # Specific hook needed
    "underdog_005": EntityPerk("underdog_005", PerkType.HYDRATION_COOLDOWN, 5, 10, "-{value}m Hydration Cooldown", "🌵"),
    "underdog_006": EntityPerk("underdog_006", PerkType.EYE_REST_CAP, 1, 2, "+{value} Eye Rest Claims/Day", "☕"),
    "underdog_007": EntityPerk("underdog_007", PerkType.MERGE_LUCK, 3, 5, "+{value}% Merge Luck", "🪑"), # Generalized luck to merge luck
    "underdog_008": EntityPerk("underdog_008", PerkType.CAPTURE_BONUS, 2, 4, "+{value}% Capture Probability", "🤖"),
    "underdog_009": EntityPerk("underdog_009", PerkType.HYDRATION_CAP, 1, 2, "+{value} Daily Water Cap", "🧊"),

    # -------------------------------------------------------------------------
    # SCIENTIST POOL (Research & Discovery)
    # -------------------------------------------------------------------------
    "scientist_001": EntityPerk("scientist_001", PerkType.UNCOMMON_CHANCE, 1, 2, "+{value}% Uncommon Item Chance", "🧪"),
    "scientist_002": EntityPerk("scientist_002", PerkType.MERGE_LUCK, 1, 2, "+{value}% Merge Success", "🔥"),
    "scientist_003": EntityPerk("scientist_003", PerkType.RARE_CHANCE, 1, 2, "+{value}% Rare Item Chance", "🧫"),
    "scientist_004": EntityPerk("scientist_004", PerkType.PITY_BONUS, 5, 8, "+{value}% Pity System Bonus", "🐁"),
    "scientist_005": EntityPerk("scientist_005", PerkType.ENCOUNTER_CHANCE, 2, 4, "+{value}% Hint Reveal/Encounter", "🔬"), # Bonus mechanics may vary
    "scientist_006": EntityPerk("scientist_006", PerkType.EPIC_CHANCE, 2, 4, "+{value}% Epic Item Chance", "⚗️"),
    "scientist_007": EntityPerk("scientist_007", PerkType.COIN_PERCENT, 3, 5, "+{value}% Perfect Session Bonus", "⚡"),
    "scientist_008": EntityPerk("scientist_008", PerkType.LEGENDARY_CHANCE, 1, 2, "+{value}% Legendary Item Chance", "🧬"),
    "scientist_009": EntityPerk("scientist_009", PerkType.DROP_LUCK, 3, 5, "+{value}% Discovery/Drop Luck", "🐁"),
}


# =============================================================================
# PERK CALCULATION
# =============================================================================

def calculate_active_perks(progress_tracker: object) -> Dict[PerkType, float]:
    """
    Calculate the total aggregated value for each active perk type.
    
    Args:
        progress_tracker: An instance of EntitidexProgress that has:
                          - collected_entity_ids (set)
                          - is_exceptional(entity_id) (method)
    
    Returns:
        Dict mapping PerkType to total value (float/int)
    """
    totals: Dict[PerkType, float] = {}
    
    # Iterate through all collected entities
    # We use list(progress_tracker.collected_entity_ids) if it's a set
    if not hasattr(progress_tracker, 'collected_entity_ids'):
        return totals
        
    for entity_id in progress_tracker.collected_entity_ids:
        perk = ENTITY_PERKS.get(entity_id)
        if perk:
            # Determine which value to use (normal vs exceptional)
            is_exc = False
            if hasattr(progress_tracker, 'is_exceptional'):
                is_exc = progress_tracker.is_exceptional(entity_id)
            
            value = perk.exceptional_value if is_exc else perk.normal_value
            
            # Aggregate
            current = totals.get(perk.perk_type, 0.0)
            totals[perk.perk_type] = current + value
            
    return totals


def get_perk_for_entity(entity_id: str, is_exceptional: bool = False) -> Optional[str]:
    """
    Get a human-readable description string for a specific entity's perk.
    
    Args:
        entity_id: The ID of the entity
        is_exceptional: Whether to show the exceptional variant value
        
    Returns:
        String like "✨ +1 Hero Power" or None if no perk exists
    """
    perk = ENTITY_PERKS.get(entity_id)
    if not perk:
        return None
        
    value = perk.exceptional_value if is_exceptional else perk.normal_value
    
    # Format value (if int, show as int, else float)
    val_str = str(int(value)) if value.is_integer() else str(value)
    
    return f"{perk.icon} {perk.description.format(value=val_str)}"


def get_perk_breakdown(progress_tracker: object) -> Dict[str, float]:
    """
    Get a flattened summary of all active perks for UI display.
    
    Returns:
        Dict like {"Hero Power": 24, "Coin Discount": 2, ...}
    """
    active = calculate_active_perks(progress_tracker)
    breakdown = {}
    
    # Map internal types to user-friendly labels
    TYPE_LABELS = {
        PerkType.POWER_FLAT: "Hero Power",
        PerkType.COIN_FLAT: "Coin Income (Flat)",
        PerkType.COIN_PERCENT: "Coin Income (%)",
        PerkType.COIN_DISCOUNT: "Coin Cost Reduction",
        PerkType.MERGE_LUCK: "Merge Luck",
        PerkType.DROP_LUCK: "Item Drop Chance",
        PerkType.HYDRATION_COOLDOWN: "Hydration Cooldown Reduction (min)",
        PerkType.HYDRATION_CAP: "Daily Hydration Cap",
        PerkType.ENCOUNTER_CHANCE: "Entity Encounter Chance",
    }
    
    for p_type, val in active.items():
        if val > 0:
            label = TYPE_LABELS.get(p_type, p_type.value.replace("_", " ").title())
            breakdown[label] = val
            
    return breakdown


def calculate_active_perks_from_dict(progress_data: dict) -> Dict[PerkType, float]:
    """
    Calculate active perks from a raw progress dictionary (e.g. from JSON state).
    
    Args:
        progress_data: Dictionary containing 'collected_entity_ids' (list)
                       and 'exceptional_entities' (dict)
                       
    Returns:
        Dict mapping PerkType to total value
    """
    totals: Dict[PerkType, float] = {}
    
    collected = progress_data.get("collected_entity_ids", [])
    exceptional = progress_data.get("exceptional_entities", {})
    
    for entity_id in collected:
        perk = ENTITY_PERKS.get(entity_id)
        if perk:
            is_exc = entity_id in exceptional
            value = perk.exceptional_value if is_exc else perk.normal_value
            
            totals[perk.perk_type] = totals.get(perk.perk_type, 0.0) + value
            
    return totals
