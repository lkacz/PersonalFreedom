"""
Encounter System for the Entitidex.

Handles triggering encounters after focus sessions and selecting
which entity appears based on user progress and hero power.
"""

import random
from typing import Optional, List, Tuple
from .entity import Entity
from .entity_pools import get_entities_for_story
from .progress_tracker import EntitidexProgress


# =============================================================================
# CONFIGURATION
# =============================================================================

ENCOUNTER_CONFIG = {
    # Base encounter chance after completing a focus session
    "base_chance": 0.40,  # 40%
    
    # Bonuses that increase encounter chance
    "bonus_per_15min": 0.05,      # +5% per 15 min beyond minimum
    "bonus_perfect_session": 0.10,  # +10% for no bypass attempts
    "bonus_per_streak_day": 0.02,   # +2% per consecutive day
    
    # Maximum encounter chance (cap)
    "max_chance": 0.85,  # 85% maximum
    
    # Entity selection weights
    "weight_power_near": 100,      # Entity within 200 power of hero
    "weight_power_close": 50,      # Entity within 500 power
    "weight_power_medium": 20,     # Entity within 1000 power
    "weight_power_far": 5,         # Entity more than 1000 away
    "weight_per_failed_attempt": 10,  # Pity bonus per failed catch
    
    # Power thresholds for weighting
    "power_near_threshold": 200,
    "power_close_threshold": 500,
    "power_medium_threshold": 1000,
    
    # Exceptional encounter chance (20%)
    "exceptional_chance": 0.20,
}


# =============================================================================
# ENCOUNTER CHANCE
# =============================================================================

def calculate_encounter_chance(
    session_minutes: int,
    minimum_session_minutes: int = 25,
    was_perfect_session: bool = False,
    streak_days: int = 0,
    active_perks: dict = None,
) -> float:
    """
    Calculate the chance of encountering an entity after a focus session.
    
    Args:
        session_minutes: Duration of the completed session
        minimum_session_minutes: The minimum required session length
        was_perfect_session: True if no bypass was attempted
        streak_days: Number of consecutive days with completed sessions
        active_perks: Dictionary of active entity perks
        
    Returns:
        Probability between 0.0 and max_chance
    """
    chance = ENCOUNTER_CONFIG["base_chance"]
    
    # Bonus for longer sessions
    extra_minutes = max(0, session_minutes - minimum_session_minutes)
    extra_15min_blocks = extra_minutes // 15
    chance += extra_15min_blocks * ENCOUNTER_CONFIG["bonus_per_15min"]
    
    # Bonus for perfect session
    if was_perfect_session:
        chance += ENCOUNTER_CONFIG["bonus_perfect_session"]
    
    # Bonus for streak
    chance += streak_days * ENCOUNTER_CONFIG["bonus_per_streak_day"]
    
    # Bonus from Entity Perks
    if active_perks:
        from .entity_perks import PerkType
        perk_bonus = active_perks.get(PerkType.ENCOUNTER_CHANCE, 0)
        chance += (perk_bonus / 100.0)
    
    # Cap at maximum
    return min(chance, ENCOUNTER_CONFIG["max_chance"])


def roll_encounter_chance(
    session_minutes: int,
    minimum_session_minutes: int = 25,
    was_perfect_session: bool = False,
    streak_days: int = 0,
    active_perks: dict = None,
) -> Tuple[bool, float]:
    """
    Roll to determine if an encounter occurs.
    
    Args:
        session_minutes: Duration of the completed session
        minimum_session_minutes: The minimum required session length
        was_perfect_session: True if no bypass was attempted
        streak_days: Number of consecutive days with sessions
        active_perks: Dictionary of active entity perks
        
    Returns:
        Tuple of (encounter_occurred: bool, chance: float)
    """
    chance = calculate_encounter_chance(
        session_minutes=session_minutes,
        minimum_session_minutes=minimum_session_minutes,
        was_perfect_session=was_perfect_session,
        streak_days=streak_days,
        active_perks=active_perks,
    )
    
    roll = random.random()
    return roll < chance, chance


def should_trigger_encounter(
    session_minutes: int,
    minimum_session_minutes: int = 25,
    was_perfect_session: bool = False,
    streak_days: int = 0,
    was_bypass_used: bool = False,
    active_perks: dict = None,
) -> bool:
    """
    Determine if an entity encounter should trigger.
    
    Args:
        session_minutes: Duration of the completed session
        minimum_session_minutes: The minimum required session length
        was_perfect_session: True if no bypass was attempted
        streak_days: Number of consecutive days with sessions
        was_bypass_used: True if bypass was used (no encounter possible)
        active_perks: Dictionary of active entity perks
        
    Returns:
        True if an encounter should occur
    """
    # No encounters on bypassed sessions
    if was_bypass_used:
        return False
    
    occurred, _ = roll_encounter_chance(
        session_minutes=session_minutes,
        minimum_session_minutes=minimum_session_minutes,
        was_perfect_session=was_perfect_session,
        streak_days=streak_days,
        active_perks=active_perks,
    )
    
    return occurred


# =============================================================================
# ENTITY SELECTION
# =============================================================================

def _calculate_entity_weight(
    entity: Entity,
    hero_power: int,
    failed_attempts: int = 0,
) -> int:
    """
    Calculate selection weight for an entity based on power proximity.
    
    Entities near the hero's power level are more likely to appear,
    as they "sense" the hero is ready for them.
    
    Args:
        entity: The entity to weight
        hero_power: Hero's current power level
        failed_attempts: Previous failed catches (pity bonus)
        
    Returns:
        Weight value (higher = more likely to be selected)
    """
    power_diff = abs(entity.power - hero_power)
    
    # Base weight based on power proximity
    if power_diff <= ENCOUNTER_CONFIG["power_near_threshold"]:
        weight = ENCOUNTER_CONFIG["weight_power_near"]  # "I've been waiting for you!"
    elif power_diff <= ENCOUNTER_CONFIG["power_close_threshold"]:
        weight = ENCOUNTER_CONFIG["weight_power_close"]  # "You're close to ready"
    elif power_diff <= ENCOUNTER_CONFIG["power_medium_threshold"]:
        weight = ENCOUNTER_CONFIG["weight_power_medium"]  # "Keep growing"
    else:
        weight = ENCOUNTER_CONFIG["weight_power_far"]  # "Not yet, but someday"
    
    # Pity bonus: entities you've failed to catch before are more likely to appear
    weight += failed_attempts * ENCOUNTER_CONFIG["weight_per_failed_attempt"]
    
    return weight


def select_encounter_entity(
    progress: EntitidexProgress,
    hero_power: int,
    story_id: str,
) -> Tuple[Optional[Entity], bool]:
    """
    Select which entity appears during an encounter.
    
    First rolls whether this is an exceptional encounter (20% chance).
    Then prioritizes uncaught entities (of that variant) near the hero's power level.
    Entities that have been failed before get a pity bonus.
    
    Args:
        progress: User's Entitidex progress
        hero_power: Hero's current total power
        story_id: Current story theme
        
    Returns:
        Tuple of (Entity to encounter or None, is_exceptional flag)
    """
    # First, roll whether this is an exceptional encounter (20% chance)
    is_exceptional = random.random() < ENCOUNTER_CONFIG["exceptional_chance"]
    
    # Check what variants are available
    has_normal, has_exceptional = progress.has_any_available_variants(story_id)
    
    # If we rolled exceptional but there are no exceptional variants left,
    # fall back to normal. If we rolled normal but there are no normal left,
    # try exceptional.
    if is_exceptional and not has_exceptional:
        if has_normal:
            is_exceptional = False
        else:
            return None, False  # Collection complete!
    elif not is_exceptional and not has_normal:
        if has_exceptional:
            is_exceptional = True
        else:
            return None, False  # Collection complete!
    
    # Get entities with the chosen variant still available
    available = progress.get_available_entity_variants(story_id, is_exceptional)
    
    if not available:
        return None, False  # This shouldn't happen given checks above
    
    # Calculate weights for each entity
    weights = []
    for entity in available:
        failed_attempts = progress.get_failed_attempts(entity.id, is_exceptional)
        weight = _calculate_entity_weight(entity, hero_power, failed_attempts)
        weights.append(weight)
    
    # Weighted random selection
    selected = random.choices(available, weights=weights, k=1)[0]
    
    return selected, is_exceptional


def get_encounter_preview(
    progress: EntitidexProgress,
    hero_power: int,
    story_id: str,
    is_exceptional: bool = False,
) -> List[Tuple[Entity, float]]:
    """
    Preview which entities are most likely to appear and their relative chances.
    
    Useful for debugging or showing hints to users.
    
    Args:
        progress: User's Entitidex progress
        hero_power: Hero's current power
        story_id: Story theme
        is_exceptional: If True, preview exceptional variants; False for normal
        
    Returns:
        List of (Entity, probability) sorted by probability descending
    """
    available = progress.get_available_entity_variants(story_id, is_exceptional)
    
    if not available:
        return []
    
    # Calculate weights
    weights = []
    for entity in available:
        failed_attempts = progress.get_failed_attempts(entity.id, is_exceptional)
        weight = _calculate_entity_weight(entity, hero_power, failed_attempts)
        weights.append(weight)
    
    total_weight = sum(weights)
    
    # Convert to probabilities
    preview = []
    for entity, weight in zip(available, weights):
        probability = weight / total_weight if total_weight > 0 else 0
        preview.append((entity, probability))
    
    # Sort by probability descending
    preview.sort(key=lambda x: x[1], reverse=True)
    
    return preview


# =============================================================================
# ENCOUNTER MESSAGES
# =============================================================================

def get_encounter_announcement(entity: Entity, is_first_time: bool, is_exceptional: bool = False) -> str:
    """
    Get the announcement message for an entity encounter.
    
    Args:
        entity: The encountered entity
        is_first_time: True if this is the first time encountering this entity
        is_exceptional: True if this is an exceptional variant
        
    Returns:
        Announcement message string
    """
    if is_exceptional:
        # Use exceptional name if available
        display_name = entity.exceptional_name or entity.name
        if is_first_time:
            return f"🌟 EXCEPTIONAL! 🌟\n\n{display_name} has appeared!"
        else:
            return f"🌟 Another chance at an EXCEPTIONAL! 🌟\n\n{display_name} returns!"
    else:
        if is_first_time:
            return f"✨ A new companion seeks you! ✨\n\n{entity.name} has appeared!"
        else:
            return f"🔄 A familiar friend returns!\n\n{entity.name} wants another chance to join you!"


def get_encounter_flavor_text(entity: Entity, hero_power: int) -> str:
    """
    Get flavor text based on power comparison.
    
    Args:
        entity: The encountered entity
        hero_power: Hero's current power
        
    Returns:
        Flavor text describing the encounter
    """
    power_ratio = hero_power / entity.power if entity.power > 0 else 999
    
    if power_ratio >= 2.0:
        return f"{entity.name} looks at you with admiration. 'I would be honored to join such a worthy hero!'"
    elif power_ratio >= 1.0:
        return f"{entity.name} studies you carefully. 'You seem ready. Prove yourself!'"
    elif power_ratio >= 0.5:
        return f"{entity.name} tilts their head curiously. 'You have potential... but are you ready?'"
    elif power_ratio >= 0.25:
        return f"{entity.name} watches from a distance. 'Keep growing, young one. I'll be here.'"
    else:
        return f"{entity.name} emanates incredible power. 'Return when you are stronger, brave soul.'"


# =============================================================================
# COMPLETION CHECKING
# =============================================================================

def is_story_collection_complete(progress: EntitidexProgress, story_id: str) -> bool:
    """
    Check if all entities for a story have been collected.
    
    Args:
        progress: User's progress
        story_id: Story to check
        
    Returns:
        True if all entities are collected
    """
    return progress.is_collection_complete(story_id)


def get_next_recommended_entity(
    progress: EntitidexProgress,
    hero_power: int,
    story_id: str,
) -> Optional[Entity]:
    """
    Get the recommended next entity to focus on (best catch odds).
    
    Args:
        progress: User's progress
        hero_power: Hero's current power
        story_id: Story theme
        
    Returns:
        Entity with best current catch odds, or None if complete
    """
    from .catch_mechanics import get_final_probability
    
    uncollected = progress.get_uncollected_entities(story_id)
    
    if not uncollected:
        return None
    
    best_entity = None
    best_probability = -1.0
    
    for entity in uncollected:
        failed = progress.get_failed_attempts(entity.id)
        prob = get_final_probability(hero_power, entity.power, failed)
        
        if prob > best_probability:
            best_probability = prob
            best_entity = entity
    
    return best_entity
