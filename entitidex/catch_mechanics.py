"""
Catch Mechanics for the Entitidex System.

Handles probability calculations, pity system, and catch attempt logic
for bonding with entities.
"""

import random
from typing import Tuple, Optional
from .entity import Entity


# =============================================================================
# CONFIGURATION
# =============================================================================

CATCH_CONFIG = {
    # Base probability settings
    "probability_min": 0.01,           # 1% minimum (always a slim chance)
    "probability_max": 0.99,           # 99% maximum (never guaranteed)
    "probability_at_equal_power": 0.50,  # 50% when hero = entity power
    
    # Pity system settings
    "pity_enabled": True,
    "pity_threshold_1": 5,    # +10% after 5 failed attempts
    "pity_bonus_1": 0.10,
    "pity_threshold_2": 10,   # +25% after 10 failed attempts  
    "pity_bonus_2": 0.25,
    "pity_threshold_3": 15,   # +50% after 15 failed attempts
    "pity_bonus_3": 0.50,
    
    # Luck modifier settings
    "luck_modifiers_enabled": True,
    "max_luck_bonus": 0.15,   # Maximum +15% from luck items
}


# =============================================================================
# PROBABILITY CALCULATIONS
# =============================================================================

def calculate_join_probability(hero_power: int, entity_power: int) -> float:
    """
    Calculate the base probability of an entity joining (bonding with) the hero.
    
    This represents the entity testing the hero's worthiness. Higher hero power
    relative to entity power means higher chance of bonding.
    
    Formula:
    - At equal power: 50% chance (the entity is testing you)
    - Hero stronger: Scales from 50% to 99% as ratio increases
    - Hero weaker: Scales from 1% to 50% based on ratio
    
    Args:
        hero_power: The hero's current total power
        entity_power: The entity's power level
        
    Returns:
        Probability between 0.01 and 0.99
        
    Examples:
        >>> calculate_join_probability(10, 2000)   # ~0.5% (long way to go)
        >>> calculate_join_probability(1000, 2000)  # ~25% (getting close)
        >>> calculate_join_probability(2000, 2000)  # 50% (equals - prove yourself)
        >>> calculate_join_probability(4000, 2000)  # 99% (clearly worthy)
    """
    # Handle edge cases
    if hero_power <= 0 or entity_power <= 0:
        return CATCH_CONFIG["probability_min"]
    
    power_ratio = hero_power / entity_power
    
    if power_ratio >= 2.0:
        # Hero is much stronger: 99% (clearly worthy)
        probability = CATCH_CONFIG["probability_max"]
    elif power_ratio >= 1.0:
        # Hero is equal or stronger: 50% to 99%
        # Linear interpolation from 50% at ratio=1.0 to 99% at ratio=2.0
        probability = 0.5 + (power_ratio - 1.0) * 0.49
    else:
        # Hero is weaker: 1% to 50%
        # Linear interpolation from 1% at ratio=0 to 50% at ratio=1.0
        probability = CATCH_CONFIG["probability_min"] + (power_ratio * 0.49)
    
    # Clamp to valid range
    return max(
        CATCH_CONFIG["probability_min"],
        min(CATCH_CONFIG["probability_max"], probability)
    )


def apply_pity_bonus(base_probability: float, failed_attempts: int) -> float:
    """
    Apply pity system bonus based on number of failed attempts.
    
    The pity system prevents frustration by increasing catch probability
    after repeated failures on the same entity.
    
    Args:
        base_probability: The base join probability (0.0 to 1.0)
        failed_attempts: Number of previous failed catch attempts
        
    Returns:
        Modified probability with pity bonus applied (capped at 0.99)
    """
    if not CATCH_CONFIG["pity_enabled"]:
        return base_probability
    
    bonus = 0.0
    
    if failed_attempts >= CATCH_CONFIG["pity_threshold_3"]:
        bonus = CATCH_CONFIG["pity_bonus_3"]
    elif failed_attempts >= CATCH_CONFIG["pity_threshold_2"]:
        bonus = CATCH_CONFIG["pity_bonus_2"]
    elif failed_attempts >= CATCH_CONFIG["pity_threshold_1"]:
        bonus = CATCH_CONFIG["pity_bonus_1"]
    
    return min(CATCH_CONFIG["probability_max"], base_probability + bonus)


def apply_luck_modifier(probability: float, luck_bonus: float) -> float:
    """
    Apply luck modifier from equipped items or special events.
    
    Args:
        probability: Current catch probability
        luck_bonus: Additional luck bonus (0.0 to max_luck_bonus)
        
    Returns:
        Modified probability with luck applied (capped at 0.99)
    """
    if not CATCH_CONFIG["luck_modifiers_enabled"]:
        return probability
    
    # Clamp luck bonus to maximum allowed
    clamped_bonus = min(luck_bonus, CATCH_CONFIG["max_luck_bonus"])
    clamped_bonus = max(0.0, clamped_bonus)
    
    return min(CATCH_CONFIG["probability_max"], probability + clamped_bonus)


def get_final_probability(
    hero_power: int,
    entity_power: int,
    failed_attempts: int = 0,
    luck_bonus: float = 0.0
) -> float:
    """
    Calculate the final catch probability with all modifiers applied.
    
    Args:
        hero_power: Hero's current power
        entity_power: Entity's power level
        failed_attempts: Previous failed attempts on this entity
        luck_bonus: Bonus from luck items/effects
        
    Returns:
        Final probability between 0.01 and 0.99
    """
    # Step 1: Calculate base probability
    base_prob = calculate_join_probability(hero_power, entity_power)
    
    # Step 2: Apply pity bonus
    with_pity = apply_pity_bonus(base_prob, failed_attempts)
    
    # Step 3: Apply luck modifier
    final = apply_luck_modifier(with_pity, luck_bonus)
    
    return final


# =============================================================================
# CATCH ATTEMPT
# =============================================================================

def attempt_catch(
    hero_power: int,
    entity: Entity,
    failed_attempts: int = 0,
    luck_bonus: float = 0.0
) -> Tuple[bool, float, str]:
    """
    Attempt to catch (bond with) an entity.
    
    Args:
        hero_power: Hero's current total power
        entity: The Entity object to attempt catching
        failed_attempts: Number of previous failed attempts on this entity
        luck_bonus: Bonus from equipped luck items
        
    Returns:
        Tuple of (success: bool, probability: float, message: str)
    """
    # Calculate final probability
    probability = get_final_probability(
        hero_power=hero_power,
        entity_power=entity.power,
        failed_attempts=failed_attempts,
        luck_bonus=luck_bonus,
    )
    
    # Roll the dice
    roll = random.random()
    success = roll < probability
    
    # Generate appropriate message
    if success:
        if probability < 0.25:
            message = f"Against all odds, {entity.name} senses your potential and joins you!"
        elif probability < 0.50:
            message = f"{entity.name} is impressed by your determination and decides to join!"
        elif probability < 0.75:
            message = f"{entity.name} nods approvingly and pledges their companionship!"
        else:
            message = f"{entity.name} eagerly joins your collection!"
    else:
        if probability > 0.75:
            message = f"So close! {entity.name} says 'Almost... try again!'"
        elif probability > 0.50:
            message = f"{entity.name} smiles kindly. 'You're getting there. Keep growing!'"
        elif probability > 0.25:
            message = f"{entity.name} watches you with interest. 'Keep proving yourself.'"
        else:
            message = f"{entity.name} sees potential in you. 'Return when you're stronger.'"
    
    return success, probability, message


def is_lucky_catch(probability: float) -> bool:
    """
    Determine if a catch was "lucky" (succeeded with <50% odds).
    
    Args:
        probability: The probability that was used for the catch
        
    Returns:
        True if probability was under 50%
    """
    return probability < 0.50


# =============================================================================
# DISPLAY HELPERS
# =============================================================================

def get_probability_description(probability: float) -> str:
    """
    Get a human-readable description of catch probability.
    
    Args:
        probability: Catch probability (0.0 to 1.0)
        
    Returns:
        Descriptive string about the odds
    """
    pct = probability * 100
    
    if pct >= 90:
        return "Almost certain! They're eager to join."
    elif pct >= 75:
        return "Very good odds. Show them your worth!"
    elif pct >= 50:
        return "Fair chance. You're being tested."
    elif pct >= 25:
        return "Challenging. They need more convincing."
    elif pct >= 10:
        return "Difficult. Keep growing stronger."
    else:
        return "Near impossible... but miracles happen."


def get_probability_color(probability: float) -> str:
    """
    Get a color code for probability display.
    
    Args:
        probability: Catch probability (0.0 to 1.0)
        
    Returns:
        Hex color code string
    """
    if probability >= 0.75:
        return "#32CD32"  # Green - very good
    elif probability >= 0.50:
        return "#FFD700"  # Gold - fair
    elif probability >= 0.25:
        return "#FFA500"  # Orange - challenging
    else:
        return "#FF4500"  # Red-orange - difficult


def format_probability_display(probability: float) -> str:
    """
    Format probability for UI display.
    
    Args:
        probability: Catch probability (0.0 to 1.0)
        
    Returns:
        Formatted string like "75.5%"
    """
    return f"{probability * 100:.1f}%"
