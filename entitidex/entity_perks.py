"""
Entity Perk System

Manages persistent bonuses from collected Entitidex entities.
Provides the specific perk definitions and calculation logic.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class PerkType(Enum):
    # Hero Stats
    POWER_FLAT = "power_flat"              # +X hero power
    
    # Economics
    COIN_FLAT = "coin_flat"                # +X coins per action/session
    COIN_PERCENT = "coin_percent"          # +X% coin gains
    COIN_DISCOUNT = "coin_discount"        # -X coin costs (general)
    STORE_DISCOUNT = "store_discount"      # -X coin cost on store refreshes
    SALVAGE_BONUS = "salvage_bonus"        # +X coins on salvage
    
    # Progression
    XP_PERCENT = "xp_percent"              # +X% XP gains (general)
    XP_SESSION = "xp_session"              # +X% XP from focus sessions
    XP_LONG_SESSION = "xp_long_session"    # +X% XP from sessions > 1 hour
    XP_NIGHT = "xp_night"                  # +X% XP during night (8PM-6AM)
    XP_MORNING = "xp_morning"              # +X% XP during morning (6AM-12PM)
    XP_STORY = "xp_story"                  # +X% XP from story chapters
    
    # Luck & RNG
    MERGE_LUCK = "merge_luck"              # +X% merge success chance
    MERGE_SUCCESS = "merge_success"        # +X% merge success rate (same as luck?)
    DROP_LUCK = "drop_luck"                # +X% item drop chance
    ALL_LUCK = "all_luck"                  # +X% to all luck stats
    STREAK_SAVE = "streak_save"            # +X% chance to save streak
    
    # Encounters
    ENCOUNTER_CHANCE = "encounter_chance"  # +X% entity encounter chance
    CAPTURE_BONUS = "capture_bonus"        # +X% capture probability
    RARITY_BIAS = "rarity_bias"            # +X% chance for higher rarity
    PITY_BONUS = "pity_bonus"              # +X% to pity system progress
    
    # Quality of Life
    HYDRATION_COOLDOWN = "hydration_cd"    # -X minutes hydration cooldown
    HYDRATION_CAP = "hydration_cap"        # +X daily hydration cap
    INVENTORY_SLOTS = "inventory_slots"    # +X inventory slots
    EYE_REST_CAP = "eye_rest_cap"          # +X daily eye rest claims
    PERFECT_SESSION = "perfect_session"    # +X% bonus for perfect sessions (no distractions)
    
    # Eye & Breath Tab
    EYE_TIER_BONUS = "eye_tier_bonus"      # +X tier to Eye routine rewards
    EYE_REROLL_CHANCE = "eye_reroll"       # X% chance to re-roll on Eye routine failure
    
    # Sleep Tab
    SLEEP_TIER_BONUS = "sleep_tier_bonus"  # +X tier to Go to Sleep Now rewards
    
    # Weight Tab
    WEIGHT_LEGENDARY = "weight_legendary"  # +X% Legendary chance when logging weight
    
    # Gear Optimization (Hobo Rat / Robo Rat)
    OPTIMIZE_GEAR_DISCOUNT = "optimize_gear_discount"  # Reduce Optimize Gear cost
    
    # Sell Items (Corner Office Chair / Stoner Office Chair)
    SELL_RARITY_BONUS = "sell_rarity_bonus"  # +X% sell value for Epic/Legendary items
    
    # Gamble / Push Your Luck
    GAMBLE_LUCK = "gamble_luck"              # +X% gamble success chance (Push Your Luck)
    GAMBLE_SAFETY = "gamble_safety"          # X% chance to keep item on gamble failure
    
    # City Resources (Scrap from merging)
    SCRAP_CHANCE = "scrap_chance"            # +X% scrap chance per merge roll
    
    # Saved Encounter Recalculation
    RECALC_PAID = "recalc_paid"              # Enables paid probability recalculation
    RECALC_RISKY = "recalc_risky"            # Enables free but risky recalculation (80% success)


@dataclass
class EntityPerk:
    """Defines a perk granted by an entity."""
    entity_id: str
    perk_type: PerkType
    normal_value: float
    exceptional_value: float
    description: str  # Format string expecting {value} placeholder (for normal)
    icon: str = "✨"
    exceptional_description: str = ""  # Optional override for exceptional variant


# =============================================================================
# PERK DEFINITIONS
# =============================================================================
# Each entity can have multiple perks - stored as List[EntityPerk]
# For backward compatibility, single perks are wrapped in lists automatically

ENTITY_PERKS: Dict[str, List[EntityPerk]] = {
    # -------------------------------------------------------------------------
    # WARRIOR (Power & Combat)
    # -------------------------------------------------------------------------
    "warrior_001": [EntityPerk("warrior_001", PerkType.POWER_FLAT, 1, 2, "Hatchling's Warmth: +{value} Hero Power", "🐉", "Dragon's Blaze: +{value} Hero Power")],
    "warrior_002": [EntityPerk("warrior_002", PerkType.POWER_FLAT, 5, 10, "Training Resilience: +{value} Hero Power", "🎯", "Master's Precision: +{value} Hero Power")],
    "warrior_003": [EntityPerk("warrior_003", PerkType.ENCOUNTER_CHANCE, 1, 2, "Falcon Eyes: +{value}% Encounter Chance", "🦅", "Eagle's Vision: +{value}% Encounter Chance")],
    "warrior_004": [EntityPerk("warrior_004", PerkType.XP_LONG_SESSION, 5, 8, "War Horse Endurance: +{value}% XP for sessions > 1h", "🐎", "Nightmare Stamina: +{value}% XP for sessions > 1h")],
    "warrior_005": [EntityPerk("warrior_005", PerkType.POWER_FLAT, 3, 6, "Dragon Strength: +{value} Hero Power", "🔥", "Inferno Might: +{value} Hero Power")],
    "warrior_006": [EntityPerk("warrior_006", PerkType.XP_SESSION, 2, 4, "Battle Standard: +{value}% Focus XP", "🚩", "War Banner: +{value}% Focus XP")],
    "warrior_007": [EntityPerk("warrior_007", PerkType.POWER_FLAT, 5, 10, "Crimson Power: +{value} Hero Power", "🐲", "Blood Dragon Fury: +{value} Hero Power")],
    "warrior_008": [EntityPerk("warrior_008", PerkType.CAPTURE_BONUS, 5, 8, "Pack Hunter: +{value}% Capture Chance", "🐺", "Alpha Predator: +{value}% Capture Chance")],
    "warrior_009": [
        EntityPerk("warrior_009", PerkType.POWER_FLAT, 10, 15, "General's Command: +{value} Hero Power", "🐜", "Swarm Emperor: +{value} Hero Power"),
        EntityPerk("warrior_009", PerkType.RECALC_PAID, 1, 0, "Strategic Assessment: Recalculate probability", "🎯", ""),
        EntityPerk("warrior_009", PerkType.RECALC_RISKY, 0, 1, "", "❄️", "Glacial Intuition: Free risky recalculate"),
    ],

    # -------------------------------------------------------------------------
    # SCHOLAR (Knowledge & XP)
    # -------------------------------------------------------------------------
    "scholar_001": [EntityPerk("scholar_001", PerkType.XP_SESSION, 1, 2, "Mouse Curiosity: +{value}% Focus XP", "🐭", "Genius Whiskers: +{value}% Focus XP")],
    "scholar_002": [EntityPerk("scholar_002", PerkType.XP_NIGHT, 2, 0, "Night Owl: +{value}% XP (8PM-6AM)", "🦉", "Moonlit Wisdom: +1 Sleep Tier")],
    "scholar_003": [EntityPerk("scholar_003", PerkType.XP_MORNING, 2, 4, "Early Bird: +{value}% XP (6AM-12PM)", "🕯️", "Dawn's First Light: +{value}% XP (6AM-12PM)")],
    "scholar_004": [EntityPerk("scholar_004", PerkType.DROP_LUCK, 1, 2, "Library Luck: +{value}% Item Drops", "🐱", "Sphinx's Fortune: +{value}% Item Drops")],
    "scholar_005": [EntityPerk("scholar_005", PerkType.MERGE_LUCK, 1, 2, "Smart Merger: +{value}% Merge Luck", "🔖", "Arcane Fusion: +{value}% Merge Luck")],
    "scholar_006": [
        EntityPerk("scholar_006", PerkType.XP_SESSION, 2, 4, "Ancient Wisdom: +{value}% Focus XP", "📖", "Forbidden Knowledge: +{value}% Focus XP"),
        EntityPerk("scholar_006", PerkType.RECALC_PAID, 1, 1, "Page Turner: Recalculate probability", "📚", "Forbidden Formula: Recalculate probability"),
    ],
    "scholar_007": [EntityPerk("scholar_007", PerkType.RARITY_BIAS, 1, 2, "Star Chart: +{value}% Rare Finds", "🗺️", "Celestial Atlas: +{value}% Rare Finds")],
    "scholar_008": [
        EntityPerk("scholar_008", PerkType.XP_STORY, 5, 8, "Phoenix Rebirth: +{value}% Story XP", "🐦", "Eternal Flame: +{value}% Story XP"),
        EntityPerk("scholar_008", PerkType.SCRAP_CHANCE, 1, 2, "Ash Recovery: +{value}% Scrap Chance", "♻️", "Phoenix Salvage: +{value}% Scrap Chance"),
    ],
    "scholar_009": [EntityPerk("scholar_009", PerkType.GAMBLE_SAFETY, 10, 20, "Tabula Rasa: {value}% Item Recovery", "📜", "Omniscient Scroll: {value}% Item Recovery")],

    # -------------------------------------------------------------------------
    # WANDERER (Travel & Coins)
    # -------------------------------------------------------------------------
    "wanderer_001": [
        EntityPerk("wanderer_001", PerkType.COIN_FLAT, 1, 2, "Lucky Copper: +{value} Coin per session", "🪙", "Golden Fortune: +{value} Coins per session"),
        EntityPerk("wanderer_001", PerkType.RECALC_PAID, 1, 0, "Fortune's Flip: Recalculate probability", "🍀", ""),
        EntityPerk("wanderer_001", PerkType.RECALC_RISKY, 0, 1, "", "✨", "Lucky Break: Free risky recalculate"),
    ],
    "wanderer_002": [EntityPerk("wanderer_002", PerkType.STREAK_SAVE, 1, 2, "True North: +{value}% Streak Save Chance", "🧭", "Fate's Compass: +{value}% Streak Save Chance")],
    "wanderer_003": [EntityPerk("wanderer_003", PerkType.COIN_FLAT, 2, 4, "Travel Log: +{value} Coins on Streak", "📓", "Treasure Chronicle: +{value} Coins on Streak")],
    "wanderer_004": [EntityPerk("wanderer_004", PerkType.HYDRATION_COOLDOWN, 5, 10, "Thirsty Dog: -{value}min Water Cooldown", "🐕", "Oasis Hound: -{value}min Water Cooldown")],
    "wanderer_005": [EntityPerk("wanderer_005", PerkType.PERFECT_SESSION, 5, 10, "Mapped Out: +{value}% Perfect Session Bonus", "🗺️", "Master Navigator: +{value}% Perfect Session Bonus")],
    "wanderer_006": [EntityPerk("wanderer_006", PerkType.HYDRATION_CAP, 1, 1, "Carriage Water: +{value} Daily Glass Cap", "⛺", "Oasis Camp: +{value} Daily Glass Cap")],
    "wanderer_007": [EntityPerk("wanderer_007", PerkType.INVENTORY_SLOTS, 1, 2, "Pack Mule: +{value} Inventory Slots", "🎒", "Dimensional Satchel: +{value} Inventory Slots")],
    "wanderer_008": [EntityPerk("wanderer_008", PerkType.COIN_FLAT, 2, 4, "High Flyer: +{value} Coins per session", "🎈", "Sky Voyager: +{value} Coins per session")],
    "wanderer_009": [
        EntityPerk("wanderer_009", PerkType.COIN_PERCENT, 5, 8, "Hobo Wisdom: +{value}% All Coin Gains", "🐀", "Rat King's Treasure: +{value}% All Coin Gains"),
        EntityPerk("wanderer_009", PerkType.SCRAP_CHANCE, 1, 2, "Scavenger's Eye: +{value}% Scrap Chance", "♻️", "Master Salvager: +{value}% Scrap Chance"),
        EntityPerk("wanderer_009", PerkType.RECALC_RISKY, 1, 1, "Route Optimization: Free risky recalculate", "🗺️", "GPS Override: Free risky recalculate"),
    ],

    # -------------------------------------------------------------------------
    # UNDERDOG (Workplace & Luck)
    # -------------------------------------------------------------------------
    "underdog_001": [
        EntityPerk("underdog_001", PerkType.DROP_LUCK, 1, 2, "Scavenger: +{value}% Item Drops", "🐁", "Master Forager: +{value}% Item Drops"),
        EntityPerk("underdog_001", PerkType.SCRAP_CHANCE, 1, 2, "Office Scrounger: +{value}% Scrap Chance", "♻️", "Dumpster Diver: +{value}% Scrap Chance"),
    ],
    "underdog_002": [EntityPerk("underdog_002", PerkType.MERGE_LUCK, 1, 2, "Sticky Luck: +{value}% Merge Luck", "📝", "Blessed Adhesion: +{value}% Merge Luck")],
    "underdog_003": [EntityPerk("underdog_003", PerkType.COIN_DISCOUNT, 1, 2, "Vending Value: -{value} Coin Cost", "🎰", "Jackpot Machine: -{value} Coin Cost")],
    "underdog_004": [EntityPerk("underdog_004", PerkType.SALVAGE_BONUS, 1, 2, "Winston's Find: +{value} Coins on Salvage", "🐦", "Golden Beak: +{value} Coins on Salvage")],
    "underdog_005": [EntityPerk("underdog_005", PerkType.EYE_TIER_BONUS, 1, 0, "Dry Eye: +{value} Eye Tier", "🌵", "Desert Eye: 50% Reroll")],
    "underdog_006": [
        EntityPerk("underdog_006", PerkType.STORE_DISCOUNT, 1, 2, "Free Refill: -{value} Store Refresh Cost", "☕", "Endless Brew: -{value} Store Refresh Cost"),
        EntityPerk("underdog_006", PerkType.RECALC_PAID, 1, 1, "Caffeinated Clarity: Recalculate probability", "☕", "Sugar Rush Math: Recalculate probability"),
    ],
    "underdog_007": [EntityPerk("underdog_007", PerkType.ALL_LUCK, 3, 5, "Executive Luck: +{value}% All Luck", "🪑", "CEO's Fortune: +{value}% All Luck")],
    "underdog_008": [
        EntityPerk("underdog_008", PerkType.CAPTURE_BONUS, 2, 4, "Chad's Algorithm: +{value}% Capture Probability", "🤖", "Sigma Protocol: +{value}% Capture Probability"),
        EntityPerk("underdog_008", PerkType.RECALC_PAID, 1, 0, "AI Consultation: Recalculate probability", "💰", ""),
        EntityPerk("underdog_008", PerkType.RECALC_RISKY, 0, 1, "", "🌟", "Transcendent Analysis: Free risky recalculate"),
    ],
    "underdog_009": [
        EntityPerk("underdog_009", PerkType.HYDRATION_CAP, 1, 1, "Cool Storage: +{value} Daily Glass Cap", "🧊", "Frost Vault: +{value} Daily Glass Cap"),
        EntityPerk("underdog_009", PerkType.RECALC_PAID, 1, 0, "Cool Calculations: Recalculate probability", "🧊", ""),
        EntityPerk("underdog_009", PerkType.RECALC_RISKY, 0, 1, "", "🥩", "Wagyu Wisdom: Free risky recalculate"),
    ],

    # -------------------------------------------------------------------------
    # SCIENTIST (Research & Discovery)
    # -------------------------------------------------------------------------
    "scientist_001": [EntityPerk("scientist_001", PerkType.RARITY_BIAS, 1, 2, "Experiment: +{value}% Uncommon Chance", "🧪", "Breakthrough Formula: +{value}% Uncommon Chance")],
    "scientist_002": [EntityPerk("scientist_002", PerkType.MERGE_SUCCESS, 1, 2, "Lab Safety: +{value}% Merge Success", "🔥", "Controlled Combustion: +{value}% Merge Success")],
    "scientist_003": [
        EntityPerk("scientist_003", PerkType.RARITY_BIAS, 1, 2, "Culture Growth: +{value}% Rare Chance", "🧫", "Perfect Specimen: +{value}% Rare Chance"),
        EntityPerk("scientist_003", PerkType.SCRAP_CHANCE, 1, 2, "Petri Salvage: +{value}% Scrap Chance", "♻️", "Bio-Recovery: +{value}% Scrap Chance"),
    ],
    "scientist_004": [EntityPerk("scientist_004", PerkType.PITY_BONUS, 5, 8, "Peer Review: +{value}% Pity Progress", "🐭", "Nobel Recognition: +{value}% Pity Progress")],
    "scientist_005": [
        EntityPerk("scientist_005", PerkType.XP_SESSION, 2, 4, "Micro-Focus: +{value}% Focus XP", "🔬", "Quantum Focus: +{value}% Focus XP"),
        EntityPerk("scientist_005", PerkType.SCRAP_CHANCE, 1, 2, "Micro-Salvage: +{value}% Scrap Chance", "♻️", "Quantum Extraction: +{value}% Scrap Chance"),
    ],
    "scientist_006": [EntityPerk("scientist_006", PerkType.RARITY_BIAS, 2, 4, "Reaction Base: +{value}% Epic Chance", "⚗️", "Philosopher's Stone: +{value}% Epic Chance")],
    "scientist_007": [EntityPerk("scientist_007", PerkType.GAMBLE_LUCK, 5, 20, "Risk Assessment: +{value}% Gamble Chance", "⚡", "Lightning Luck: +{value}% Gamble Chance")],
    "scientist_008": [EntityPerk("scientist_008", PerkType.RARITY_BIAS, 1, 2, "Golden Standard: +{value}% Legendary Chance", "🧬", "Divine Helix: +{value}% Legendary Chance")],
    "scientist_009": [EntityPerk("scientist_009", PerkType.XP_PERCENT, 3, 5, "Eureka Moment: +{value}% Discovery XP", "🐁", "Genius Awakening: +{value}% Discovery XP")],
}


def calculate_active_perks(progress_data: Optional[dict]) -> Dict[PerkType, float]:
    """
    Calculate total bonuses from all collected entities.
    
    When you collect BOTH normal AND exceptional variants of an entity,
    you get BOTH bonuses (they stack).
    
    Args:
        progress_data: Dict or Object containing 'collected_entity_ids' (set/list) 
                       and 'exceptional_entities' (dict/set).
                       Can be raw dict or EntitidexProgress object.
                       Can be None or empty (returns empty dict).
    
    Returns:
        Dict mapping PerkType to total value (float).
    """
    totals: Dict[PerkType, float] = {}
    
    # Handle None input
    if progress_data is None:
        return totals
    
    # Handle different input types (dict vs object)
    if hasattr(progress_data, 'collected_entity_ids'):
        collected = progress_data.collected_entity_ids
        exceptional = progress_data.exceptional_entities
    else:
        # Support both old "collected" and new "collected_entity_ids" keys
        collected = progress_data.get('collected_entity_ids', 
                    progress_data.get('collected', set()))
        exceptional = progress_data.get('exceptional_entities', {})
    
    # Handle None values within dict
    if collected is None:
        collected = set()
    if exceptional is None:
        exceptional = {}
    
    # Build set of exceptional entity IDs for quick lookup
    exceptional_ids = set()
    if isinstance(exceptional, set):
        exceptional_ids = exceptional
    elif isinstance(exceptional, dict):
        exceptional_ids = set(exceptional.keys())
    
    # Collect all unique entity IDs from both normal and exceptional collections
    all_entity_ids = set(collected) | exceptional_ids
    
    for entity_id in all_entity_ids:
        perks = ENTITY_PERKS.get(entity_id)
        if perks:
            has_normal = entity_id in collected
            has_exceptional = entity_id in exceptional_ids
            
            # Process all perks for this entity
            for perk in perks:
                # Add normal value if collected normally
                if has_normal:
                    current = totals.get(perk.perk_type, 0.0)
                    totals[perk.perk_type] = current + perk.normal_value
                
                # Add exceptional value if collected as exceptional (stacks!)
                if has_exceptional:
                    current = totals.get(perk.perk_type, 0.0)
                    totals[perk.perk_type] = current + perk.exceptional_value
            
    return totals

def get_perk_description(entity_id: str, is_exceptional: bool = False) -> str:
    """Get human-readable perk description for an entity.
    
    Exceptional entities use their unique exceptional_description if available,
    providing more epic/powerful-sounding perk names.
    
    Returns all perks for the entity, joined by newlines.
    """
    perks = ENTITY_PERKS.get(entity_id)
    if not perks:
        return ""
    
    descriptions = []
    for perk in perks:
        value = perk.exceptional_value if is_exceptional else perk.normal_value
        
        # Skip perks with zero value (entity doesn't have this perk for this variant)
        if value == 0:
            continue
        
        # Use exceptional description if available and this is an exceptional entity
        if is_exceptional and perk.exceptional_description:
            description = perk.exceptional_description.format(value=value)
        else:
            description = perk.description.format(value=value)
        
        descriptions.append(f"{perk.icon} {description}")
    
    return "\n".join(descriptions)


# =============================================================================
# PERK EXPLANATIONS - Detailed descriptions of how each perk works
# =============================================================================

PERK_EXPLANATIONS: Dict[PerkType, str] = {
    # Hero Stats
    PerkType.POWER_FLAT: "Permanently adds to your Hero Power, increasing your overall strength in all game mechanics.",
    
    # Economics
    PerkType.COIN_FLAT: "Grants bonus coins each time you complete a focus session or qualifying action.",
    PerkType.COIN_PERCENT: "Increases all coin earnings by a percentage - applies to session rewards, salvage, and bonuses.",
    PerkType.COIN_DISCOUNT: "Reduces coin costs on various actions like store purchases and refreshes.",
    PerkType.STORE_DISCOUNT: "Specifically reduces the cost of refreshing the store to get new items.",
    PerkType.SALVAGE_BONUS: "Grants extra coins when salvaging unwanted items from your inventory.",
    
    # Progression
    PerkType.XP_PERCENT: "Increases all XP gains by a percentage - applies to focus sessions, story, and other activities.",
    PerkType.XP_SESSION: "Specifically boosts XP earned from completing focus sessions.",
    PerkType.XP_LONG_SESSION: "Bonus XP kicks in only for focus sessions longer than 1 hour - rewards deep work!",
    PerkType.XP_NIGHT: "Extra XP during night hours (8PM-6AM) - perfect for night owls.",
    PerkType.XP_MORNING: "Extra XP during morning hours (6AM-12PM) - rewards early risers.",
    PerkType.XP_STORY: "Increases XP earned from completing story chapters.",
    
    # Luck & RNG
    PerkType.MERGE_LUCK: "Improves your success chance when merging items - less failures!",
    PerkType.MERGE_SUCCESS: "Increases the base merge success rate calculation.",
    PerkType.DROP_LUCK: "Increases the chance of receiving item drops from various activities.",
    PerkType.ALL_LUCK: "Universal luck bonus that applies to ALL luck-based mechanics.",
    PerkType.STREAK_SAVE: "When you would lose your streak, this gives a chance to save it instead.",
    
    # Encounters
    PerkType.ENCOUNTER_CHANCE: "Increases how often you encounter new entities during focus sessions.",
    PerkType.CAPTURE_BONUS: "When you encounter an entity, this improves your chance to successfully capture it.",
    PerkType.RARITY_BIAS: "Shifts the rarity distribution - higher rarities become more likely.",
    PerkType.PITY_BONUS: "Accelerates pity system progress - guarantees come sooner.",
    
    # Quality of Life
    PerkType.HYDRATION_COOLDOWN: "Reduces the cooldown between water reminders - get hydrated faster!",
    PerkType.HYDRATION_CAP: "Increases maximum daily water glasses you can log for rewards.",
    PerkType.INVENTORY_SLOTS: "Permanently adds inventory slots - carry more gear!",
    PerkType.EYE_REST_CAP: "Increases how many eye rest sessions you can claim per day.",
    PerkType.PERFECT_SESSION: "Bonus rewards for completing sessions without distractions (no bypasses).",
    
    # Eye & Breath Tab
    PerkType.EYE_TIER_BONUS: "Upgrades the tier of rewards from Eye routine - better loot!",
    PerkType.EYE_REROLL_CHANCE: "Chance to automatically re-roll if an Eye routine fails.",
    
    # Sleep Tab
    PerkType.SLEEP_TIER_BONUS: "Upgrades the tier of rewards from Go to Sleep Now - better items!",
    
    # Weight Tab
    PerkType.WEIGHT_LEGENDARY: "Increases chance of Legendary items when logging weight.",
    
    # Gear Optimization
    PerkType.OPTIMIZE_GEAR_DISCOUNT: "Reduces the coin cost of the Optimize Gear feature.",
    
    # Sell Items
    PerkType.SELL_RARITY_BONUS: "Increases sell value for Epic and Legendary items.",
    
    # Gamble / Push Your Luck
    PerkType.GAMBLE_LUCK: "Improves success chance when using 'Push Your Luck' in item merging.",
    PerkType.GAMBLE_SAFETY: "When Push Your Luck FAILS, this gives a chance to keep your item instead of losing it!",
    
    # Scrap / Salvage
    PerkType.SCRAP_CHANCE: "Increases the chance of receiving bonus scrap when merging items - useful for city construction!",
    
    # Saved Encounter Recalculation
    PerkType.RECALC_PAID: "Allows paying coins to recalculate the catch probability of saved encounters using your current hero power. Great if you've gotten stronger since saving!",
    PerkType.RECALC_RISKY: "Free probability recalculation with 80% success rate. If successful, uses your current power. If it fails, the original odds remain unchanged.",
}


def get_perk_explanation(entity_id: str) -> str:
    """Get detailed explanation of how a perk works.
    
    Returns human-readable explanations of all perk mechanics for this entity,
    helping users understand when and how the perks are applied.
    """
    perks = ENTITY_PERKS.get(entity_id)
    if not perks:
        return ""
    
    explanations = []
    for perk in perks:
        explanation = PERK_EXPLANATIONS.get(perk.perk_type, "This perk provides passive bonuses.")
        explanations.append(explanation)
    
    return "\n\n".join(explanations)