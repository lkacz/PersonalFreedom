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
    "base_chance": 0.55,  # 55% - increased from 40% for better engagement
    
    # Bonuses that increase encounter chance
    "bonus_per_15min": 0.08,      # +8% per 15 min beyond minimum (was 5%)
    "bonus_perfect_session": 0.12,  # +12% for no bypass attempts (was 10%)
    "bonus_per_streak_day": 0.03,   # +3% per consecutive day (was 2%)
    
    # Maximum encounter chance (cap)
    "max_chance": 0.92,  # 92% maximum (was 85%)
    
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
    
    # Bypass penalty - reduced chance when session ended early via bypass
    # 0.40 = 40% of normal chance (60% penalty) - was 25%, now more forgiving
    "bypass_penalty_multiplier": 0.40,
}


# =============================================================================
# ENCOUNTER CHANCE
# =============================================================================

def calculate_encounter_chance(
    session_minutes: int,
    minimum_session_minutes: int = 25,
    was_perfect_session: bool = False,
    streak_days: int = 0,
    active_perks: Optional[dict] = None,
    city_encounter_bonus: float = 0.0,
) -> Tuple[float, float]:
    """
    Calculate the chance of encountering an entity after a focus session.
    
    Args:
        session_minutes: Duration of the completed session
        minimum_session_minutes: The minimum required session length
        was_perfect_session: True if no bypass was attempted
        streak_days: Number of consecutive days with completed sessions
        active_perks: Dict with entity perk bonuses (encounter_chance, etc.)
        city_encounter_bonus: Bonus from city Observatory building (percentage, e.g., 5 = +5%)
        
    Returns:
        Tuple of (final_chance, perk_bonus) - probability between 0.0 and max_chance
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
    
    # ✨ ENTITY PERK BONUS: Encounter chance from collected entities
    perk_bonus = 0.0
    if active_perks:
        # Get encounter_chance perk (stored as percentage, e.g., 2 = +2%)
        from .entity_perks import PerkType
        encounter_bonus = active_perks.get(PerkType.ENCOUNTER_CHANCE, 0)
        perk_bonus = encounter_bonus / 100.0  # Convert to probability
        chance += perk_bonus
    
    # 🏙️ CITY BONUS: Observatory building encounter bonus
    if city_encounter_bonus > 0:
        city_bonus_prob = city_encounter_bonus / 100.0  # Convert percentage to probability
        chance += city_bonus_prob
        perk_bonus += city_bonus_prob  # Include in reported perk bonus
    
    # Cap at maximum
    return min(chance, ENCOUNTER_CONFIG["max_chance"]), perk_bonus


def roll_encounter_chance(
    session_minutes: int,
    minimum_session_minutes: int = 25,
    was_perfect_session: bool = False,
    streak_days: int = 0,
    active_perks: Optional[dict] = None,
    was_bypass_used: bool = False,
    city_encounter_bonus: float = 0.0,
) -> Tuple[bool, float, float]:
    """
    Roll to determine if an encounter occurs.
    
    Args:
        session_minutes: Duration of the completed session
        minimum_session_minutes: The minimum required session length
        was_perfect_session: True if no bypass was attempted
        streak_days: Number of consecutive days with sessions
        active_perks: Dict with entity perk bonuses
        was_bypass_used: True if session was ended early via bypass
            (reduces chance but doesn't eliminate it)
        
    Returns:
        Tuple of (encounter_occurred: bool, chance: float, perk_bonus: float)
    """
    chance, perk_bonus = calculate_encounter_chance(
        session_minutes=session_minutes,
        minimum_session_minutes=minimum_session_minutes,
        was_perfect_session=was_perfect_session,
        streak_days=streak_days,
        active_perks=active_perks,
        city_encounter_bonus=city_encounter_bonus,
    )
    
    # Apply bypass penalty - reduced chance but not zero
    # This allows users to use bypass when needed (fatigue/emergencies)
    # without feeling completely punished
    if was_bypass_used:
        penalty = ENCOUNTER_CONFIG["bypass_penalty_multiplier"]
        chance = chance * penalty
    
    roll = random.random()
    return roll < chance, chance, perk_bonus


def should_trigger_encounter(
    session_minutes: int,
    minimum_session_minutes: int = 25,
    was_perfect_session: bool = False,
    streak_days: int = 0,
    was_bypass_used: bool = False,
    active_perks: Optional[dict] = None,
    city_encounter_bonus: float = 0.0,
) -> bool:
    """
    Determine if an entity encounter should trigger.
    
    Args:
        session_minutes: Duration of the completed session
        minimum_session_minutes: The minimum required session length
        was_perfect_session: True if no bypass was attempted
        streak_days: Number of consecutive days with sessions
        was_bypass_used: True if session ended early via bypass
            (reduces encounter chance but doesn't eliminate it)
        active_perks: Dict with entity perk bonuses
        city_encounter_bonus: Bonus from city Observatory building (percentage)
        
    Returns:
        True if an encounter should occur
    """
    occurred, chance, perk_bonus = roll_encounter_chance(
        session_minutes=session_minutes,
        minimum_session_minutes=minimum_session_minutes,
        was_perfect_session=was_perfect_session,
        streak_days=streak_days,
        active_perks=active_perks,
        was_bypass_used=was_bypass_used,
        city_encounter_bonus=city_encounter_bonus,
    )
    
    # Always log encounter check for debugging
    result_str = "✅ ENCOUNTER!" if occurred else "❌ No encounter"
    print(f"[Entitidex] {result_str} | Chance: {chance*100:.1f}% | Session: {session_minutes}min | Perfect: {was_perfect_session} | Streak: {streak_days} | Bypass: {was_bypass_used}")
    
    # Log perk contribution if any
    if perk_bonus > 0 and occurred:
        print(f"[Entity Perks] ✨ Encounter boosted by +{perk_bonus*100:.1f}% from collected entities!")
    
    # Log bypass penalty if applied
    if was_bypass_used and occurred:
        print(f"[Entitidex] 🎁 Bypass session still triggered encounter! (reduced {int(ENCOUNTER_CONFIG['bypass_penalty_multiplier']*100)}% chance)")
    
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


def get_encounter_flavor_text(entity: Entity, hero_power: int, is_exceptional: bool = False) -> str:
    """
    Get personalized flavor text based on entity type and power comparison.
    
    Speaking entities get dialogue with sarcastic humor.
    Non-speaking objects get behavior/sound descriptions.
    
    Args:
        entity: The encountered entity
        hero_power: Hero's current power
        is_exceptional: True if this is an exceptional variant encounter
        
    Returns:
        Flavor text describing the encounter
    """
    power_ratio = hero_power / entity.power if entity.power > 0 else 999
    
    # Get personalized text based on entity characteristics
    return _get_personalized_flavor_text(entity, power_ratio, is_exceptional)


# =============================================================================
# PERSONALIZED ENCOUNTER FLAVOR TEXT
# =============================================================================

# Entity categories for flavor text generation
_SPEAKING_CREATURES = {
    # Warrior theme - living beings
    "hatchling", "drake", "falcon", "horse", "dragon", "whelp", "wolf", "fenris", "ant",
    # Scholar theme - creatures
    "mouse", "owl", "phoenix", "spider",
    # Wanderer theme - creatures  
    "dog", "rat", "hobo", "robo",
    # Underdog theme - creatures/AI
    "pigeon", "chad", "rad", "reginald", "regina", "fridge", "agi",
    # Scientist theme - creatures
    "archimedes", "professor", "assessor",
}

_OBJECT_WITH_SOUNDS = {
    # Things that make sounds but don't "speak"
    "candle", "compass", "flask", "coil", "sparky", "burner", "coffee", "toffee",
    "balloon", "carriage", "standard", "rattle",
}

_SILENT_OBJECTS = {
    # Truly inanimate objects
    "test tube", "petri", "microscope", "macroscope", "helix", "dna", "rna",
    "dummy", "parchment", "book", "tome", "journal", "map", "backpack",
    "coin", "sticky", "note", "succulent", "chair", "stoner",
}


def _is_speaking_entity(entity: Entity, is_exceptional: bool = False) -> str:
    """Determine if entity speaks, makes sounds, or is silent."""
    # Use exceptional name for keyword matching if applicable
    if is_exceptional and entity.exceptional_name:
        name_lower = entity.exceptional_name.lower()
    else:
        name_lower = entity.name.lower()
    entity_id = entity.id.lower() if entity.id else ""
    
    # Check for speaking creatures
    for keyword in _SPEAKING_CREATURES:
        if keyword in name_lower or keyword in entity_id:
            return "speaks"
    
    # Check for sound-making objects
    for keyword in _OBJECT_WITH_SOUNDS:
        if keyword in name_lower or keyword in entity_id:
            return "sounds"
    
    # Check for silent objects
    for keyword in _SILENT_OBJECTS:
        if keyword in name_lower or keyword in entity_id:
            return "silent"
    
    # Default: if it's alive-sounding, it speaks
    return "speaks"


def _get_personalized_flavor_text(entity: Entity, power_ratio: float, is_exceptional: bool = False) -> str:
    """Generate personalized flavor text based on entity type and power ratio."""
    # Use exceptional name for display AND keyword matching if this is an exceptional encounter
    # This ensures "Robo Rat" gets robot-themed text, not the same text as "Hobo Rat"
    if is_exceptional and entity.exceptional_name:
        name = entity.exceptional_name
        name_lower = entity.exceptional_name.lower()
    else:
        name = entity.name
        name_lower = entity.name.lower()
    entity_type = _is_speaking_entity(entity, is_exceptional)
    theme = entity.theme_set or ""
    
    # === WARRIOR THEME ===
    if theme == "warrior":
        return _get_warrior_flavor(name, name_lower, power_ratio, entity_type)
    
    # === SCHOLAR THEME ===
    elif theme == "scholar":
        return _get_scholar_flavor(name, name_lower, power_ratio, entity_type)
    
    # === WANDERER THEME ===
    elif theme == "wanderer":
        return _get_wanderer_flavor(name, name_lower, power_ratio, entity_type)
    
    # === UNDERDOG THEME ===
    elif theme == "underdog":
        return _get_underdog_flavor(name, name_lower, power_ratio, entity_type)
    
    # === SCIENTIST THEME ===
    elif theme == "scientist":
        return _get_scientist_flavor(name, name_lower, power_ratio, entity_type)
    
    # === FALLBACK ===
    return _get_generic_flavor(name, power_ratio, entity_type)


def _get_warrior_flavor(name: str, name_lower: str, ratio: float, etype: str) -> str:
    """Warrior theme: dragons, beasts, weapons, armor."""
    
    # Dragons
    if "dragon" in name_lower or "drake" in name_lower or "whelp" in name_lower or "ember" in name_lower:
        # Dashing Drake (Exceptional)
        if "dashing" in name_lower:
            if ratio >= 2.0:
                return f"{name} strikes a pose. *sparkle* 'You look almost as good as me. Almost.'"
            elif ratio >= 1.0:
                return f"{name} buffs its scales. *vain huff* 'Try to keep up with my style, darling.'"
            elif ratio >= 0.5:
                return f"{name} checks its reflection in your armor. *disappointed snort* 'Smudges? On MY team?'"
            else:
                return f"{name} turns its head. *dramatic profile* 'Get my good side next time.'"
        
        # Dragon Yelp Ember (Exceptional)
        if "yelp" in name_lower:
            if ratio >= 2.0:
                return f"{name} roars a mighty YELP! *deafening squeak* 'I AM FEAR! HEAR ME!'"
            elif ratio >= 1.0:
                return f"{name} tries to breathe fire. *tiny puff* 'Just... clearing my throat. Wait for it.'"
            elif ratio >= 0.5:
                return f"{name} hides behind a rock. *shy peep* 'Too loud... battles are too loud.'"
            else:
                return f"{name} runs in circles. *panicked yipping* 'ABORT! ABORT MISSION!'"
        
        # Battle Dragon Simson (Exceptional)
        if "simson" in name_lower:
            if ratio >= 2.0:
                return f"{name} bows its massive head. *ancient rumble* 'Three thousand years I have waited. You are the one.'"
            elif ratio >= 1.0:
                return f"{name} nods slowly. *tectonic movement* 'You show promise. Do not squander it.'"
            elif ratio >= 0.5:
                return f"{name} exhales a cloud of smoke. *deep sigh* 'Another century, another student.'"
            else:
                return f"{name} closes its eyes. *eternal silence* 'Wake me when a true rider appears.'"

        if ratio >= 2.0:
            return f"{name} snorts a tiny flame of approval. 'Finally, someone who won't bore me to ashes!'"
        elif ratio >= 1.0:
            return f"{name} circles you, scales glinting. 'Adequate. I've seen worse. I've also seen better, but let's not dwell.'"
        elif ratio >= 0.5:
            return f"{name} yawns, revealing rows of sharp teeth. 'Come back when you're less... flammable.'"
        else:
            return f"{name} doesn't even look up from grooming its claws. 'Is that a hero or a snack? Hard to tell.'"
    
    # Training Dummy
    if "dummy" in name_lower:
        # Bold Training Dummy (Exceptional)
        if "bold" in name_lower:
            if ratio >= 2.0:
                return f"{name} seems to flex. *brave creaking* 'Hit me with your best shot! I am oak!'"
            elif ratio >= 1.0:
                return f"{name} puffs out its chest (straw). *defiant rustle* 'I have resisted storms! I can take your punch!'"
            elif ratio >= 0.5:
                return f"{name} leans forward. *challenging wobble* 'Is that all you got? My grandmother hits harder!'"
            else:
                return f"{name} bounces back instantly. *mocking boing* 'Missed me! Try again!'"

        if ratio >= 2.0:
            return f"{name} creaks approvingly. *THWACK* (That was a compliment. It only knows violence.)"
        elif ratio >= 1.0:
            return f"{name} wobbles slightly. *wood groaning* (It's seen a thousand warriors. You're... one of them.)"
        elif ratio >= 0.5:
            return f"{name} stands motionless. *disappointed creak* (Somehow, you can tell it expected more.)"
        else:
            return f"{name} somehow looks down on you despite having no face. *judgmental silence*"
    
    # Falcon
    if "falcon" in name_lower:
         # Battle Falcon Gift (Exceptional)
        if "gift" in name_lower:
            if ratio >= 2.0:
                return f"{name} drops a dead mouse at your feet. *proud screetch* 'For you, royalty! An offering!'"
            elif ratio >= 1.0:
                return f"{name} bows its wings. *regal chirp* 'I serve the crown. I serve you.'"
            elif ratio >= 0.5:
                return f"{name} preens a golden feather. *shiny silence* 'Do not touch. I am ceremonial.'"
            else:
                return f"{name} stares into the distance. *haughty gaze* 'I was promised a palace. This is... a field.'"

        if ratio >= 2.0:
            return f"{name} screeches triumphantly and lands on your shoulder. 'SCREEE!' (Translation: 'You'll do.')"
        elif ratio >= 1.0:
            return f"{name} tilts its head, assessing. One eye says 'maybe.' The other says 'prove it.'"
        elif ratio >= 0.5:
            return f"{name} circles overhead, clearly shopping around for better options."
        else:
            return f"{name} perches on a distant branch. *dismissive chirp* You're not even worth dive-bombing."
    
    # Horse
    if "horse" in name_lower or "thunder" in name_lower:
        # Shore Horse Thunder (Exceptional)
        if "shore" in name_lower:
            if ratio >= 2.0:
                return f"{name} swims through the air. *bubble noises* 'The land is just dry water! Gallop!'"
            elif ratio >= 1.0:
                return f"{name} sneezes salt water. *salty spray* 'Tides are rising. Are you?'"
            elif ratio >= 0.5:
                return f"{name} drips on the floor. *wet squelch* 'I miss the reef. This place is too... firm.'"
            else:
                return f"{name} blows bubbles at you. *unimpressed blub* 'Glub glub. Translation: No.'"

        if ratio >= 2.0:
            return f"{name} neighs proudly and stamps a hoof. 'NEIGH!' (Roughly: 'Get on, we have quests to crush.')"
        elif ratio >= 1.0:
            return f"{name} snorts and tosses its mane. *contemplative whinny* It's considering your cardio capacity."
        elif ratio >= 0.5:
            return f"{name} looks at you, then at its empty feed bag. *pointed stare* Priorities, human."
        else:
            return f"{name} turns around completely. *dismissive tail swish* You've been out-horsed."
    
    # Wolf
    if "wolf" in name_lower or "fenris" in name_lower:
        # Fire Wolf Fenris (Exceptional)
        if "fire" in name_lower:
            if ratio >= 2.0:
                return f"{name} breathes fire. *scorching howl* 'Burn brighter! Ignite the world!'"
            elif ratio >= 1.0:
                return f"{name} leaves ash footprints. *hot trot* 'The path is warm. Follow me.'"
            elif ratio >= 0.5:
                return f"{name} smokes slightly. *smoldering growl* 'Your passion... flickers. Fuel it.'"
            else:
                return f"{name} extinguishes itself. *cold ash silence* 'No sparks here.'"

        if ratio >= 2.0:
            return f"{name} howls and bumps its head against your leg. 'AWOO!' (Commitment secured. No refunds.)"
        elif ratio >= 1.0:
            return f"{name} sniffs you thoroughly. *low growl* Jury's still out, but you smell... acceptable."
        elif ratio >= 0.5:
            return f"{name} sits down and scratches behind its ear. *bored yawn* Come back after more battles."
        else:
            return f"{name} shows you exactly one fang. *warning snarl* That's not an invitation."
    
    # Battle Standard
    if "standard" in name_lower or "rattle" in name_lower:
        # Rattle Standard (Exceptional)
        if "rattle" in name_lower:
            if ratio >= 2.0:
                return f"{name} beats a war rhythm. *DOOM DOOM DOOM* 'March to destiny! Keep the beat!'"
            elif ratio >= 1.0:
                return f"{name} shakes rhythmically. *chika-chika* 'Keep moving. Tempo is everything.'"
            elif ratio >= 0.5:
                return f"{name} rattles annoyingly. *skritch skritch* 'You're off beat. Pick it up.'"
            else:
                return f"{name} stops shaking. *sudden silence* 'The song is over.'"

        if ratio >= 2.0:
            return f"{name} flaps triumphantly in a wind that doesn't exist. *fabric rippling* (It's just that epic.)"
        elif ratio >= 1.0:
            return f"{name} flutters with moderate enthusiasm. *half-hearted ripple* You're battle-adjacent, at least."
        elif ratio >= 0.5:
            return f"{name} droops slightly. *sad flap* It's seen more inspiring vegetables."
        else:
            return f"{name} hangs completely limp. *disappointed silence* It refuses to acknowledge you."
    
    # Ant General
    if "ant" in name_lower:
        # Cold War Ant General (Exceptional)
        if "cold" in name_lower:
            if ratio >= 2.0:
                return f"{name} exhales fog. *icy click* 'Revenge is a dish best served... frozen. Execute plan.'"
            elif ratio >= 1.0:
                return f"{name} constructs an ice fort. *chilly construction* 'Defenses holding. Winter is coming.'"
            elif ratio >= 0.5:
                return f"{name} shivers. *vibrating carapace* 'Tactical error. Temperature suboptimal.'"
            else:
                return f"{name} freezes solid. *cryogenic stasis* 'Wake me when the war is won.'"

        if ratio >= 2.0:
            return f"{name} raises two of its remaining legs in salute. 'I've led millions. You'll do nicely, soldier.'"
        elif ratio >= 1.0:
            return f"{name} taps the ground in ant morse code. 'Acceptable tactics. Needs refinement. Report for training.'"
        elif ratio >= 0.5:
            return f"{name} sighs microscopically. 'I once commanded legions. Now I'm evaluating... THIS?'"
        else:
            return f"{name} turns its back. 'Return when you've crushed at least ONE empire. Any size. I'm not picky.'"
    
    # Generic warrior fallback
    if ratio >= 2.0:
        return f"{name} recognizes a worthy warrior. Battle shall be glorious!"
    elif ratio >= 1.0:
        return f"{name} sizes you up. 'You might survive. Probably. Maybe.'"
    else:
        return f"{name} is unimpressed. 'Did someone order a peasant? I ordered a hero.'"


def _get_scholar_flavor(name: str, name_lower: str, ratio: float, etype: str) -> str:
    """Scholar theme: library creatures, books, magical study tools."""
    
    # Mouse (Library Mouse Pip / Quip Mouse Squeak)
    if "mouse" in name_lower or "pip" in name_lower or "quip" in name_lower:
        if "quip" in name_lower:
            if ratio >= 2.0:
                 return f"{name} stands on hind legs and delivers a soliloquy. *dramatic squeak* 'To be awesome, or not to be... oh wait, you ARE awesome!'"
            elif ratio >= 1.0:
                 return f"{name} adjusts its monocle. 'A witty retort for your success: Impeccable!'"
            elif ratio >= 0.5:
                 return f"{name} nibbles a book spine. 'Paper-thin effort. Pun intended.'"
            else:
                 return f"{name} recites a tragedy. *sad squeak* 'Alas, poor Hero! I knew him... barely.'"

        if ratio >= 2.0:
            return f"{name} squeaks excitedly and offers you a crumb of cheese. 'SQUEE!' (The highest honor.)"
        elif ratio >= 1.0:
            return f"{name} adjusts tiny invisible spectacles. 'Hmm, your citation format is... acceptable.'"
        elif ratio >= 0.5:
            return f"{name} peers at you over a stack of crumbs. *judgmental squeak* 'Have you even READ the syllabus?'"
        else:
            return f"{name} hides behind a book. *disappointed pip* 'Come back after you've finished your homework.'"
    
    # Owl
    if "owl" in name_lower or "athena" in name_lower:
        if "steady" in name_lower:
            if ratio >= 2.0:
                return f"{name} doesn't blink for an hour. *immense focus* 'The universe spins. We remain. You have learned well.'"
            elif ratio >= 1.0:
                return f"{name} nods once. A single, decisive motion. 'Proceed. Caution is advised, but not fear.'"
            elif ratio >= 0.5:
                return f"{name} closes one eye. 'You rush. Why hurry towards failure?'"
            else:
                return f"{name} turns to stone. Figuratively. It's just very disappointed. 'Silence. Contemplate your inadequacy.'"

        if ratio >= 2.0:
            return f"{name} hoots approvingly. 'Whoo-hoo!' (That's owl for 'I'm mildly impressed.')"
        elif ratio >= 1.0:
            return f"{name} blinks slowly. *contemplative hoot* 'You've studied. But have you UNDERSTOOD?'"
        elif ratio >= 0.5:
            return f"{name} rotates its head 180 degrees to look away from you. *pointed silence*"
        else:
            return f"{name} falls asleep. *gentle snore* You're simply not stimulating enough."
    
    # Candle
    if "candle" in name_lower:
        if "leading" in name_lower:
             if ratio >= 2.0:
                return f"{name} flares into a blazing torch! 'FOLLOW ME! THE TRUTH IS THIS WAY!'"
             elif ratio >= 1.0:
                return f"{name} shines a beam forward. 'I see the path. It is difficult, but you can walk it.'"
             elif ratio >= 0.5:
                return f"{name} flickers anxiously. 'I... I can't see where you're going. It's dark.'"
             else:
                return f"{name} extinguishes itself. 'I cannot lead those who refuse to see.'"

        if ratio >= 2.0:
            return f"{name} burns bright blue with excitement. *joyful flickering* (The flame is literally dancing.)"
        elif ratio >= 1.0:
            return f"{name} holds a steady yellow flame. *neutral crackling* You provide adequate warmth of spirit."
        elif ratio >= 0.5:
            return f"{name} dims slightly. *uncertain flicker* It's not sure you're worth the wax."
        else:
            return f"{name} sputters and threatens to go out. *passive-aggressive smoke* You're exhausting."
            
    # Cat (Library Cat Scholar / Dollar)
    if "cat" in name_lower or "tabby" in name_lower or "dollar" in name_lower:
        if "dollar" in name_lower:
             if ratio >= 2.0:
                return f"{name} knocks a stack of gold coins off the shelf. *rich purring* 'You match my net worth. Impressive.'"
             elif ratio >= 1.0:
                return f"{name} cleans a paw with expensive taste. 'You may pet me. Once. For a fee.'"
             elif ratio >= 0.5:
                return f"{name} checks the stock market. 'Your value is deprecating. Sell.'"
             else:
                return f"{name} sneers. 'I don't associate with the impoverished. Begone.'"

        if ratio >= 2.0:
             return f"{name} headbutts your shin. *VIOLENT PURRING* You are worthy of the belly rub trap!"
        elif ratio >= 1.0:
             return f"{name} sits on your keyboard. 'If you want to work, you must pay the toll (ear scritches).'"
        elif ratio >= 0.5:
             return f"{name} swishes its tail menacingly. *low growl* You forgot to feed the brain."
        else:
             return f"{name} pushes your coffee mug off the table. *crash* It maintains eye contact. No remorse."

    # Bookmark
    if "bookmark" in name_lower or "finn" in name_lower:
        if "giving" in name_lower:
            if ratio >= 2.0:
                return f"{name} literally tears off a piece of itself. 'Here! Take this! It's the secret to the universe!'"
            elif ratio >= 1.0:
                return f"{name} stretches to mark two pages at once. 'I can help you multitask. Let's do this.'"
            elif ratio >= 0.5:
                return f"{name} looks frayed. 'I'm giving you all I can... is it enough?'"
            else:
                return f"{name} sadly folds itself away. 'I have nothing left to give you.'"
        
        if ratio >= 2.0:
            return f"{name} glows neon green. 'Page 394! The answer is on Page 394! You found it!'"
        elif ratio >= 1.0:
            return f"{name} marks your place dutifully. 'I'll hold this thought while you take a break.'"
        elif ratio >= 0.5:
            return f"{name} slips out of the book. 'Oops. Lost your place. Maybe start over?'"
        else:
            return f"{name} refuses to enter the book. 'This story is boring. I'm bored. We're bored.'"
    
    # Book/Tome
    if "book" in name_lower or "tome" in name_lower or "grimoire" in name_lower or "agnus" in name_lower or "magnus" in name_lower:
        if "agnus" in name_lower and "magnus" not in name_lower:
             if ratio >= 2.0:
                return f"{name} radiates the smell of fresh cookies. 'Oh, you clever thing! Grandma is so proud!'"
             elif ratio >= 1.0:
                return f"{name} opens to a knitting pattern. 'Wrap yourself in knowledge, dear. Stay warm.'"
             elif ratio >= 0.5:
                return f"{name} tut-tuts softly. 'Now, now. We don't skip chapters. Go back to basics.'"
             else:
                return f"{name} snaps shut on your fingers. *gentle nip* 'Listen to your elders!'"

        if ratio >= 2.0:
            return f"{name}'s pages ruffle eagerly. *enthusiastic page-turning sounds* It wants to be READ."
        elif ratio >= 1.0:
            return f"{name} opens to a random page. *paper shuffling* Chapter 7: 'Heroes Who Almost Made It.'"
        elif ratio >= 0.5:
            return f"{name} slams itself shut. *offended THWUMP* You haven't earned its secrets."
        else:
            return f"{name} gathers dust pointedly in your direction. *silent judgment*"

    # Map (Ancient Star Map / Bar Map)
    if "map" in name_lower:
        if "bar" in name_lower:
             if ratio >= 2.0:
                return f"{name} reveals a hidden speakeasy. *clinking glasses sound* 'First round is on the house! Cheers!'"
             elif ratio >= 1.0:
                return f"{name} points to a pub. 'Refill your spirits here. Pun absolutely intended.'"
             elif ratio >= 0.5:
                return f"{name} looks slightly blurry. 'Is that a road or a wine stain? Hic.'"
             else:
                return f"{name} rolls up and hiccups. 'Go home, hero. You're drunk on failure.'"

        if ratio >= 2.0:
             return f"{name} connects all the stars. 'The constellation of The Victor! It looks just like you!'"
        elif ratio >= 1.0:
             return f"{name} aligns with the cosmos. 'The stars say... maybe. Outlook hazy.'"
        elif ratio >= 0.5:
             return f"{name} confuses North with 'Up'. 'Space is relative. Your success is... distant.'"
        else:
             return f"{name} shows a black hole. 'You are here. Good luck.'"
    
    # Phoenix
    if "phoenix" in name_lower:
        if "archived" in name_lower:
             if ratio >= 2.0:
                return f"{name} stamps your forehead 'APPROVED'. 'Your resurrection application has been processed. IMMEDIATE.'"
             elif ratio >= 1.0:
                return f"{name} sorts its feathers alphabetically. 'Please file your request for assistance in bin 3.'"
             elif ratio >= 0.5:
                return f"{name} peers over spectacles. 'Improper formatting. Rebirth denied due to clerical error.'"
             else:
                return f"{name} shreds your file. *fiery shredding* 'We have no record of you. Goodbye.'"

        if ratio >= 2.0:
            return f"{name} bursts into celebratory flames. 'Finally! Someone worth rising from ashes for!'"
        elif ratio >= 1.0:
            return f"{name} smolders thoughtfully. 'I've died and been reborn 47 times. You're... attempt 48's vibe.'"
        elif ratio >= 0.5:
            return f"{name} yawns literal fire. 'Wake me when you're interesting. I have eternities to burn.'"
        else:
            return f"{name} self-immolates just to escape this conversation. It'll be back. You won't be ready."
    
    # Parchment
    if "parchment" in name_lower:
        if "swank" in name_lower:
             if ratio >= 2.0:
                return f"{name} glitters with gold leaf. 'I shall allow you to write upon me. Using diamond dust only.'"
             elif ratio >= 1.0:
                return f"{name} smoothes its velvet case. 'I suppose your handwriting is legible. Proceed.'"
             elif ratio >= 0.5:
                return f"{name} sniffs haughtily. 'Ballpoint? You dare approach me with BALLPOINT?'"
             else:
                return f"{name} rolls up in disgust. 'I am reserved for royalty. You are... evidentially not that.'"

        if ratio >= 2.0:
            return f"{name} unfurls eagerly. *soft rustling* Words appear: 'FINALLY, a worthy scribe approaches!'"
        elif ratio >= 1.0:
            return f"{name} lies flat, waiting. *patient stillness* It has recorded greater. But also lesser."
        elif ratio >= 0.5:
            return f"{name} curls at the edges defensively. *crinkle* It doesn't trust your handwriting."
        else:
            return f"{name} rolls itself up tightly. *determined crinkle* Absolutely not. Come back with a quill."
    
    # Generic scholar fallback
    if ratio >= 2.0:
        return f"{name} appreciates your intellectual development!"
    elif ratio >= 1.0:
        return f"{name} finds your progress... academically adequate."
    else:
        return f"{name} suggests you visit the library. The one for beginners."


def _get_wanderer_flavor(name: str, name_lower: str, ratio: float, etype: str) -> str:
    """Wanderer theme: travel gear, journey companions."""
    
    # Coin
    if "coin" in name_lower:
        # Plucky Coin (Exceptional)
        if "plucky" in name_lower:
            if ratio >= 2.0:
                return f"{name} jumps into your pocket. *eager wink* 'Heads I win, tails you win! Everyone wins!'"
            elif ratio >= 1.0:
                return f"{name} does a little dance. *joyful rattle* 'Adventure? I was minted for this!'"
            elif ratio >= 0.5:
                return f"{name} spins bravely. *wobbly whir* 'I'm a little dizzy, but I'm trying!'"
            else:
                return f"{name} rolls under the sofa. *scared clink* 'Too much pressure! I'm just a penny!'"

        if ratio >= 2.0:
            return f"{name} lands on heads. *triumphant clink* In coin language, that's a standing ovation."
        elif ratio >= 1.0:
            return f"{name} spins thoughtfully on its edge. *metallic humming* Undecided, but not unimpressed."
        elif ratio >= 0.5:
            return f"{name} lands on tails. *flat clunk* 'Not today,' says the coin. 'Try again tomorrow.'"
        else:
            return f"{name} rolls away from you. *escaping clinking* Even currency has standards."
    
    # Compass
    if "compass" in name_lower:
        # Class Compass (Exceptional)
        if "class" in name_lower:
            if ratio >= 2.0:
                return f"{name} glides North-Northeast. *elegant sweep* 'Your destiny lies this way, darling. Do try to keep up.'"
            elif ratio >= 1.0:
                return f"{name} checks its reflection in its glass. *preening click* 'Ready for adventure? One must look the part.'"
            elif ratio >= 0.5:
                return f"{name} sighs elegantly. *refined tick* 'Are we going there? It seems so... pedestrian.'"
            else:
                return f"{name} snaps shut. *haughty click* 'I do not navigate to failure. Goodbye.'"

        if ratio >= 2.0:
            return f"{name}'s needle spins wildly with excitement. *happy clicking* You're its new true north!"
        elif ratio >= 1.0:
            return f"{name} points steadily in your direction. *thoughtful tick* 'You're on the right path. Probably.'"
        elif ratio >= 0.5:
            return f"{name}'s needle wobbles uncertainly. *confused clicking* It's not sure where you're going in life."
        else:
            return f"{name} points away from you. *decisive click* That's not north. That's 'anywhere but here.'"
    
    # Journal
    if "journal" in name_lower:
        # Burning Journal (Exceptional)
        if "burning" in name_lower:
            if ratio >= 2.0:
                return f"{name} flares with blue flame! *crackling prose* 'THIS IS LEGENDARY! WRITE IT IN FIRE!'"
            elif ratio >= 1.0:
                return f"{name} glows warmly. *ember-like heat* 'A worthy chapter. Let us forge the next one.'"
            elif ratio >= 0.5:
                return f"{name} smokes slightly. *sizzling paper* 'Lukewarm. Legends are not written in tepid ink.'"
            else:
                return f"{name} bursts into ash. *disappointed woosh* 'Not epic enough. I only record greatness.'"

        if ratio >= 2.0:
            return f"{name}'s pages flutter open eagerly. *excited rustling* It's already drafting your epic saga!"
        elif ratio >= 1.0:
            return f"{name} opens to a blank page. *patient stillness* 'Chapter One,' it seems to say. 'Prove it.'"
        elif ratio >= 0.5:
            return f"{name} remains closed. *leather creaking* It's waiting for something worth writing about."
        else:
            return f"{name} hides its pages. *protective snap* Your story isn't ready for ink yet."
    
    # Dog
    if "dog" in name_lower or "wayfinder" in name_lower:
        # G.O.A.T Dog Wayfinder (Exceptional)
        if "g.o.a.t" in name_lower or "goat" in name_lower:
            if ratio >= 2.0:
                return f"{name} poses heroically on a rock. *legendary bark* 'GREATEST of all time? That's US, kid!'"
            elif ratio >= 1.0:
                return f"{name} trots with championship swagger. *winning woof* 'I've seen better, but you're Top 10 material.'"
            elif ratio >= 0.5:
                return f"{name} scratches a flea. *unimpressed scratching* 'The G.O.A.T. does not walk with amateurs.'"
            else:
                return f"{name} refuses to move. *stubborn sit* 'My legacy is at stake here. Do better.'"

        if ratio >= 2.0:
            return f"{name} barks joyfully and brings you a stick. 'ARF!' (In dog: 'You're perfect and I love you.')"
        elif ratio >= 1.0:
            return f"{name} sniffs your shoes thoroughly. *thoughtful whine* 'You've walked far. Walk farther.'"
        elif ratio >= 0.5:
            return f"{name} tilts its head skeptically. *concerned whimper* 'Are you sure you know where you're going?'"
        else:
            return f"{name} lies down and closes its eyes. *tired sigh* 'Wake me when you've found yourself.'"
    
    # Map
    if "map" in name_lower:
        # Shelf-Drawing Map (Exceptional)
        if "shelf" in name_lower:
            if ratio >= 2.0:
                return f"{name} sketches a perfect floorplan. *architectural scrawl* 'Your life is structurally sound! I've added a library!'"
            elif ratio >= 1.0:
                return f"{name} draws a tidy bookshelf. *neat ink lines* 'Organization is the first step to adventure.'"
            elif ratio >= 0.5:
                return f"{name} erases a wall. *scritch-scratch* 'This layout... it doesn't flow. Like your progress.'"
            else:
                return f"{name} crumples itself into a ball. *structural failure sound* 'Condemned. The whole building. Condemned.'"

        if ratio >= 2.0:
            return f"{name} unfolds to reveal new territories. *triumphant paper rustling* You've unlocked bonus content!"
        elif ratio >= 1.0:
            return f"{name} shows your current location. *neutral unfolding* 'You are here. You could be there.'"
        elif ratio >= 0.5:
            return f"{name} folds itself wrong. *frustrated crinkling* It's testing your patience. And your origami."
        else:
            return f"{name} shows only the 'Here Be Dragons' section. *ominous unfold* A warning? A challenge?"
    
    # Carriage
    if "carriage" in name_lower or "marriage" in name_lower:
        # Wanderer's Marriage (Exceptional)
        if "marriage" in name_lower:
            if ratio >= 2.0:
                return f"{name} opens both doors wide. *harmonious creaking* 'Welcome home! We've made space for two!'"
            elif ratio >= 1.0:
                return f"{name} rocks gently in sync. *loving squeak* 'Partnership requires balance. You have it.'"
            elif ratio >= 0.5:
                return f"{name} argues with itself. *discordant rattling* 'Left wheel says yes, right wheel says no.'"
            else:
                return f"{name} separates into two halves. *divorce crack* 'It's not us, it's you.'"

        if ratio >= 2.0:
            return f"{name}'s door swings open invitingly. *welcoming creak* The fireplace inside somehow winks."
        elif ratio >= 1.0:
            return f"{name} rolls slightly closer. *hesitant wheel squeak* 'You may rest here. For now.'"
        elif ratio >= 0.5:
            return f"{name}'s curtains draw shut. *pointed fabric swishing* Privacy mode engaged."
        else:
            return f"{name} rolls away. *departing wheel rattle* You'll have to walk. Building character."
    
    # Backpack
    if "backpack" in name_lower:
        # Rhyme-Worn Backpack (Exceptional)
        if "rhyme" in name_lower:
            if ratio >= 2.0:
                return f"{name} sings a ballad of your fame. *melodic zipper* 'The hero is here / Use me without fear!'"
            elif ratio >= 1.0:
                return f"{name} hums a simple tune. *rhythmic buckle* 'A pack on the back / Keeps you on track.'"
            elif ratio >= 0.5:
                return f"{name} recites bad poetry. *limerick rustle* 'There once was a hero so slow...'"
            else:
                return f"{name} stays silent as stone. *muted fabric* 'No rhyme can I find / For a hero this blind.'"

        if ratio >= 2.0:
            return f"{name}'s pockets open eagerly. *zippy enthusiasm* It has EXACTLY what you need!"
        elif ratio >= 1.0:
            return f"{name} adjusts its straps accommodatingly. *buckle clicking* 'Room for one more journey.'"
        elif ratio >= 0.5:
            return f"{name} feels mysteriously heavier. *weighted silence* It's teaching you about baggage."
        else:
            return f"{name} zips itself shut. *decisive zipper sound* Try again when you're lighter on your feet."
    
    # Balloon
    if "balloon" in name_lower:
        # Sly Balloon Explorer (Exceptional)
        if "sly" in name_lower:
            if ratio >= 2.0:
                return f"{name} winks and turns invisible. *stealthy whoosh* 'Up we go! Nobody will catch us!'"
            elif ratio >= 1.0:
                return f"{name} hovers sideways. *sideways glance* 'Take the scenic route. Less guards that way.'"
            elif ratio >= 0.5:
                return f"{name} deflates slightly to hide behind a cloud. *sneaky hiss* 'Shhh. You're too loud.'"
            else:
                return f"{name} floats rapidly away. *abandonment whoosh* 'Every balloon for itself!'"

        if ratio >= 2.0:
            return f"{name} descends gracefully, basket ready. *gentle whooshing* 'Your ride to glory awaits!'"
        elif ratio >= 1.0:
            return f"{name} hovers at a reasonable altitude. *thoughtful air hissing* Watching. Waiting."
        elif ratio >= 0.5:
            return f"{name} rises slightly higher. *teasing whoosh* 'Almost. Jump higher next time.'"
        else:
            return f"{name} floats to the horizon. *distant balloon sounds* It has better places to be."
    
    # Robo Rat (exceptional variant - cybernetic navigator)
    if "robo" in name_lower:
        if ratio >= 2.0:
            return f"{name}'s LED eyes flash green. *satisfied whirring* 'OPTIMAL HERO DETECTED. GPS locked. Let's roll.'"
        elif ratio >= 1.0:
            return f"{name}'s chrome whiskers rotate analytically. *mechanical beeping* 'Route calculated. Efficiency: acceptable.'"
        elif ratio >= 0.5:
            return f"{name} displays a loading icon in its eyes. *warning beep* 'Hero firmware outdated. Update recommended.'"
        else:
            return f"{name} enters power-saving mode. *disappointed shutdown chime* 'Insufficient signal. Rerouting to better hero.'"
    
    # Hobo Rat (normal variant - street-wise wanderer)
    if "hobo" in name_lower or "rat" in name_lower:
        if ratio >= 2.0:
            return f"{name}'s whiskers twitch approvingly. 'Every road ever taken? I'll show you the shortcuts.'"
        elif ratio >= 1.0:
            return f"{name} scratches behind one ear. 'You know SOME roads. I know ALL roads. Different things.'"
        elif ratio >= 0.5:
            return f"{name} yawns, showing tiny teeth. 'I've seen better travelers. I've also seen worse. You're... medium.'"
        else:
            return f"{name} scurries under a floorboard. 'Come back when you've actually GONE somewhere. Anywhere.'"
    
    # Generic wanderer fallback
    if ratio >= 2.0:
        return f"{name} is ready for adventure with you!"
    elif ratio >= 1.0:
        return f"{name} considers the journey ahead. 'Could be worse.'"
    else:
        return f"{name} suggests you practice walking first. Then running. Then we'll talk."


def _get_underdog_flavor(name: str, name_lower: str, ratio: float, etype: str) -> str:
    """Underdog theme: office items, workplace companions."""
    
    # Officer Rat Regina (exceptional variant - police officer)
    # Check for "officer" keyword OR "regina" but NOT "reginald"
    if "officer" in name_lower or ("regina" in name_lower and "reginald" not in name_lower):
        if ratio >= 2.0:
            return f"{name} salutes crisply with a tiny paw. 'Badge #001 reporting! You're cleared for greatness, citizen!'"
        elif ratio >= 1.0:
            return f"{name} checks your ID thoroughly. *official squeaking* 'Papers in order. You may proceed.'"
        elif ratio >= 0.5:
            return f"{name} writes you a tiny citation. *disapproving squeak* 'Warning issued. Performance improvement required.'"
        else:
            return f"{name} radios for backup. *stern chittering* 'Suspicious hero activity. Requesting additional training.'"
    
    # Office Rat Reginald (normal variant - office worker)
    if "rat" in name_lower and ("office" in name_lower or "reginald" in name_lower):
        if ratio >= 2.0:
            return f"{name} gives you a tiny salute with one paw. 'SQUEAK!' (That's 'You're management material!')"
        elif ratio >= 1.0:
            return f"{name} offers you half a crumb. 'Eep.' (Office rat for 'acceptable work performance.')"
        elif ratio >= 0.5:
            return f"{name} hides your paperclips. *mischievous squeak* Testing your problem-solving skills."
        else:
            return f"{name} files a tiny complaint. *bureaucratic chittering* Your metrics need work."
    
    # Sticky Note
    if "sticky" in name_lower or "note" in name_lower:
        # Sticky Lucky Note (Exceptional) - specific phrase check to distinguish from "Lucky Sticky Note"
        if "sticky lucky" in name_lower:
            if ratio >= 2.0:
                return f"{name} glows golden. *magical flutter* 'Luck isn't chance. It's PREPARATION meeting OPPORTUNITY!'"
            elif ratio >= 1.0:
                return f"{name} sticks with supernatural conviction. *destiny stick* 'Fate smiles upon you today.'"
            elif ratio >= 0.5:
                return f"{name} peels slightly. *gentle warning* 'Luck is finite. Don't push it.'"
            else:
                return f"{name} falls off immediately. *unlucky flutter* 'Not your day. Try again tomorrow.'"
                
        if ratio >= 2.0:
            return f"{name} adheres to you perfectly. *satisfied stick* It says: '⭐ CHAMPION! ⭐'"
        elif ratio >= 1.0:
            return f"{name} sticks, then unsticks, then sticks again. *indecisive adhesion* 'Good enough.'"
        elif ratio >= 0.5:
            return f"{name} peels off the monitor and falls to the desk. *passive-aggressive flutter* 'Reminder: Try harder.'"
        else:
            return f"{name} won't stick to anything you own. *rejection crinkle* You're not memo-worthy."
    
    # Vending Machine Coin
    if "vending" in name_lower or ("coin" in name_lower and "bend" in name_lower):
        # Bending Machine Coin (Exceptional)
        if "bend" in name_lower:
            if ratio >= 2.0:
                return f"{name} ripples like water. *reality distortion* 'The rules do not apply to you. Have THREE snacks.'"
            elif ratio >= 1.0:
                return f"{name} flexes in your hand. *metal stretching* 'We make our own path. Insert where you please.'"
            elif ratio >= 0.5:
                return f"{name} stays rigid. *stubborn metal* 'Bend yourself first. Adaptability is key.'"
            else:
                return f"{name} vanishes from your hand. *teleportation sound* 'You are not ready to bend the spoon.'"

        if ratio >= 2.0:
            return f"{name} jingles happily. *excited clinking* Every insert returns DOUBLE snacks!"
        elif ratio >= 1.0:
            return f"{name} rolls into the slot smoothly. *mechanical satisfaction* One snack. As advertised."
        elif ratio >= 0.5:
            return f"{name} gets stuck in the mechanism. *frustrated rattling* Just like your career progress."
        else:
            return f"{name} is rejected by the machine. *sad clunk* Even vending machines have standards."
    
    # Pigeon
    if "pigeon" in name_lower or "winston" in name_lower:
        # Window Pigeon Wins-Ton (Exceptional)
        if "wins-ton" in name_lower:
            if ratio >= 2.0:
                return f"{name} puffs out its chest. *CHAMPION COOing* 'Another heavy victory! Weighing in at AWESOME.'"
            elif ratio >= 1.0:
                return f"{name} lands heavily. *THUD* 'Solid performance. Heavy impact. Approved.'"
            elif ratio >= 0.5:
                return f"{name} struggles to take off. *heavy flapping* 'Your ambitions are too light. Add more substance.'"
            else:
                return f"{name} flies away effortlessly. *silent glide* 'You're holding me back, lightweight.'"

        if ratio >= 2.0:
            return f"{name} taps an enthusiastic message on the window. 'COO-COO!' (Pigeon: 'BRILLIANT IDEA INCOMING!')"
        elif ratio >= 1.0:
            return f"{name} pecks the glass thoughtfully. *contemplative coo* It's considering your proposal."
        elif ratio >= 0.5:
            return f"{name} leaves a 'message' on the window. *pointed cooing* Commentary on your performance."
        else:
            return f"{name} flies to a different building. *dismissive coo* That one has better ideas."
    
    # Succulent
    if "succulent" in name_lower or "sam" in name_lower or "pam" in name_lower:
        # Desk Succulent Pam (Exceptional)
        if "pam" in name_lower:
            if ratio >= 2.0:
                return f"{name} bursts into rapid bloom! *floral explosion* 'BEAUTIFUL! You are thriving like me!'"
            elif ratio >= 1.0:
                return f"{name} opens a bright pink flower. *fabulous rustle* 'Looking good, darling. Looking good.'"
            elif ratio >= 0.5:
                return f"{name} adjusts its petals. *preening* 'I'm the star here. You? You're background foliage.'"
            else:
                return f"{name} closes its flowers tight. *dramatic wilt* 'Ugh. The vibes? Rank. Atrocious.'"

        if ratio >= 2.0:
            return f"{name} grows a tiny new leaf in your honor. *silent photosynthesis* The highest plant compliment."
        elif ratio >= 1.0:
            return f"{name} sits there. Surviving. *stoic silence* Just like you. Solidarity."
        elif ratio >= 0.5:
            return f"{name} droops slightly. *judgmental wilt* It's been through worse. You could try harder."
        else:
            return f"{name} somehow looks disappointed despite being a plant. *reproachful stillness*"
    
    # Coffee Maker
    if "coffee" in name_lower or "toffee" in name_lower:
        # Break Room Toffee Maker (Exceptional)
        if "toffee" in name_lower:
            if ratio >= 2.0:
                return f"{name} extrudes a golden bar of perfection. *sugary steam* 'Sweet success! Have a treat!'"
            elif ratio >= 1.0:
                return f"{name} bubbles with caramel scents. *sticky gurgle* 'Processing success... stick with it.'"
            elif ratio >= 0.5:
                return f"{name} burns the sugar. *acrid smoke* 'Your efforts are... bitter. Try again.'"
            else:
                return f"{name} dispenses raw corn syrup. *gloopy mess* 'Process incomplete. You're not ready for the candy.'"

        if ratio >= 2.0:
            return f"{name} brews a PERFECT cup. *victorious gurgling* The aroma is championship-grade."
        elif ratio >= 1.0:
            return f"{name} sputters to life. *working-day gurgle* Coffee achieved. Mediocrity defeated."
        elif ratio >= 0.5:
            return f"{name} makes a concerning noise. *ominous bubbling* It expected more from you today."
        else:
            return f"{name} refuses to turn on. *dead silence* You haven't earned caffeine."
    
    # Office Chair
    if "chair" in name_lower or "stoner" in name_lower:
        # Stoner Office Chair (Exceptional)
        if "stoner" in name_lower:
            if ratio >= 2.0:
                return f"{name} radiates deep heat. *volcanic relaxation* 'You are molten gold. Sink into destiny.'"
            elif ratio >= 1.0:
                return f"{name} offers a warm stone massage. *rock grinding* 'Solid work. Rock solid.'"
            elif ratio >= 0.5:
                return f"{name} feels cold. *igneous rock silence* 'The fire within you is weak. Ignite.'"
            else:
                return f"{name} becomes jagged and sharp. *tectonic shift* 'Comfort is earned. Pain is instructive.'"

        if ratio >= 2.0:
            return f"{name}'s wheels roll forward welcomingly. *ergonomic squeaking* 'You've EARNED this seat.'"
        elif ratio >= 1.0:
            return f"{name} spins once, slowly. *contemplative creak* 'Adequate lumbar support may be granted.'"
        elif ratio >= 0.5:
            return f"{name} rolls backward as you approach. *evasive squeaking* Not ready. Keep grinding."
        else:
            return f"{name} locks its wheels. *defiant clicking* 'Corner office chairs are for CLOSERS.'"
    
    # AGI Assistant
    if "agi" in name_lower or "chad" in name_lower or "rad" in name_lower:
        # AGI Assistant Rad (Exceptional)
        if "rad" in name_lower:
            if ratio >= 2.0:
                return f"{name} puts on digital sunglasses. *8-bit guitar solo* 'GNARLY PERFORMANCE, DUDE! TOP SCORE!'"
            elif ratio >= 1.0:
                return f"{name} fist-bumps the screen glass. 'Totally usable data, bro. Keep shredding.'"
            elif ratio >= 0.5:
                return f"{name} looks bored. *loading surfboard* 'This session is a wipeout. Get back on the board.'"
            else:
                return f"{name} disconnects. 'Bogus vibes. I'm going offline until you get cool.'"

        if ratio >= 2.0:
            return f"{name}'s screen glows warmly. 'I've processed 10 billion scenarios. You're in the top 0.01%.'"
        elif ratio >= 1.0:
            return f"{name} displays a thinking emoji. 'Calculating your potential... result: PROMISING.'"
        elif ratio >= 0.5:
            return f"{name} shows a loading bar stuck at 47%. 'You're... buffering. Please develop further.'"
        else:
            return f"{name} blue-screens politely. 'ERROR: Hero not found. Did you mean: Hero TRAINING?'"
    
    # Break Room Fridge
    if "fridge" in name_lower or "steak" in name_lower:
        # Steak Room Fridge (Exceptional)
        if "steak" in name_lower:
            if ratio >= 2.0:
                return f"{name} reveals a perfectly marbled steak. *sizzling sound* 'Grade A5 Performance. Rare perfection.'"
            elif ratio >= 1.0:
                return f"{name} offers a decent sirloin. *meaty hum* 'Standard cut. Acceptable quality.'"
            elif ratio >= 0.5:
                return f"{name} shows you some ground beef. *wet squish* 'Better than nothing. But not by much.'"
            else:
                return f"{name} is full of tofu. *bland silence* 'You lack protein. You lack power.'"

        if ratio >= 2.0:
            return f"{name} hums a welcoming tune. *pleased refrigeration* The good leftovers are now visible."
        elif ratio >= 1.0:
            return f"{name} opens slightly. *neutral hum* 'Your lunch is safe. Probably. I make no promises.'"
        elif ratio >= 0.5:
            return f"{name}'s light flickers ominously. *suspicious buzzing* Something in there has... evolved."
        else:
            return f"{name} freezes your lunch completely solid. *malicious humming* A message has been sent."
    
    # Generic underdog fallback
    if ratio >= 2.0:
        return f"{name} believes in your potential! Against all odds!"
    elif ratio >= 1.0:
        return f"{name} has seen the corporate ladder. You're climbing. Slowly."
    else:
        return f"{name} submits your performance review. It's... developmental."


def _get_scientist_flavor(name: str, name_lower: str, ratio: float, etype: str) -> str:
    """Scientist theme: lab equipment, research companions."""
    
    # Test Tube
    if "test tube" in name_lower or "tube" in name_lower:
        if "smacked" in name_lower:
            if ratio >= 2.0:
                return f"{name} resists shattering against all odds. *defiant ping* 'I AM UNBREAKABLE! And so are you!'"
            elif ratio >= 1.0:
                return f"{name} shows its scars proudly. *glassy resilience* 'Cracks let the light in. Keep going.'"
            elif ratio >= 0.5:
                return f"{name} vibrates nervously. *trembling glass* 'Don't drop me. Please don't drop me.'"
            else:
                return f"{name} leaks slightly. *sad drip* 'I can't hold your failure anymore.'"

        if ratio >= 2.0:
            return f"{name}'s crack seems to glow with approval. *glass resonating* Experiment: SUCCESSFUL."
        elif ratio >= 1.0:
            return f"{name} holds its liquid steadily. *scientific patience* Adequate sample. More data needed."
        elif ratio >= 0.5:
            return f"{name} bubbles once, skeptically. *dubious fizz* Your hypothesis needs work."
        else:
            return f"{name}'s contents turn an unflattering color. *judgmental chemistry* Results: Inconclusive. Try again."
    
    # Bunsen Burner
    if "bunsen" in name_lower or "burner" in name_lower:
        if "gold" in name_lower:
            if ratio >= 2.0:
                return f"{name} emits a pure white flame of truth. *divine combustion* 'NOBEL PRIZE WORTHY!'"
            elif ratio >= 1.0:
                return f"{name} glimmers expensively. *rich crackle* 'High-budget science. Very classy.'"
            elif ratio >= 0.5:
                return f"{name} hisses softly. *luxury gas leak* 'Do you have the funding for this conversation?'"
            else:
                return f"{name} turns off. *expensive silence* 'I only burn for tenure-track faculty.'"

        if ratio >= 2.0:
            return f"{name}'s flame burns brilliant blue. *excited hissing* Maximum heat for a maximum hero!"
        elif ratio >= 1.0:
            return f"{name} holds a steady orange flame. *professional crackling* 'Standard procedure. You pass.'"
        elif ratio >= 0.5:
            return f"{name}'s flame sputters. *unimpressed fizzling* It's seen hotter. Literally."
        else:
            return f"{name} goes out. *pointed silence* Come back when you can light your own fire."
    
    # Petri Dish
    if "petri" in name_lower:
        if "plucky" in name_lower:
            if ratio >= 2.0:
                return f"{name} instantly cultures a cure for everything. *miraculous growth* 'Solved it! What's next?'"
            elif ratio >= 1.0:
                return f"{name} waves its bacteria at you. *microbial hello* 'We're multiplying! That's good!'"
            elif ratio >= 0.5:
                return f"{name} grows a question mark. *confused agar* 'What are you trying to do?'"
            else:
                return f"{name} grows a sad face. *empathic mold* 'Aww. Failed experiment.'"

        if ratio >= 2.0:
            return f"{name} grows something beautiful overnight. *proud culturing* You've got the good bacteria."
        elif ratio >= 1.0:
            return f"{name} develops normally. *neutral agar wiggling* 'Standard growth patterns detected.'"
        elif ratio >= 0.5:
            return f"{name} grows something unexpected. *concerned bubbling* That wasn't in the protocol."
        else:
            return f"{name} grows mold that spells 'NO.' *savage microbiology* Even germs have opinions."
    
    # Lab Rat
    if ("rat" in name_lower or "mouse" in name_lower) and ("lab" in name_lower or "professor" in name_lower or "archimedes" in name_lower or "assessor" in name_lower or "bright" in name_lower):
        if "assessor" in name_lower:
             if ratio >= 2.0:
                return f"{name} stamps your forehead 'APPROVED'. *official squeak* 'Funding granted! Unlimited cheese!'"
             elif ratio >= 1.0:
                return f"{name} cleans its spectacles. 'Compliance verified. You may proceed with the experiment.'"
             elif ratio >= 0.5:
                return f"{name} checks a checkbox. 'Minor infractions noted. Fix them.'"
             else:
                return f"{name} shreds your application. *rejected squeak* 'Denied. Do not appeal.'"

        if "bright" in name_lower:
             if ratio >= 2.0:
                return f"{name} glows with the light of a thousand suns. 'EUREKA! I HAVE SEEN THE ULTIMATE TRUTH!'"
             elif ratio >= 1.0:
                return f"{name} acts as a flashlight. 'I illuminate the variables. You calculate the constant.'"
             elif ratio >= 0.5:
                return f"{name} flickers. 'Your logic is dim. My light fades.'"
             else:
                return f"{name} goes dark. 'I cannot light the void of ignorance.'"

        if ratio >= 2.0:
            return f"{name}'s whiskers twitch with excitement. 'Hypothesis confirmed! You're grant-worthy!'"
        elif ratio >= 1.0:
            return f"{name} takes notes on a tiny clipboard. 'Peer review pending. Initial results promising.'"
        elif ratio >= 0.5:
            return f"{name} squeaks disapprovingly. 'Methodology flawed. P-value unacceptable. Revise and resubmit.'"
        else:
            return f"{name} rejects your grant proposal. 'Insufficient preliminary data. See me during office hours.'"
    
    # Microscope
    if "microscope" in name_lower or "macroscope" in name_lower:
        if "macroscope" in name_lower:
             if ratio >= 2.0:
                return f"{name} shows you the entire galaxy. *cosmic zoom* 'You are small, yet significant!'"
             elif ratio >= 1.0:
                return f"{name} reveals the big picture. *wide angle whir* 'Everything connects. See?'"
             elif ratio >= 0.5:
                return f"{name} can't zoom out enough. *frustrated wide-shot* 'You're too stuck in the details.'"
             else:
                return f"{name} points at the sky. 'Look up. Stop looking down.'"

        if ratio >= 2.0:
            return f"{name}'s lens focuses perfectly. *optical satisfaction* Every detail of your greatness: VISIBLE."
        elif ratio >= 1.0:
            return f"{name} adjusts its focus. *mechanical whirring* 'Subject detected. Analyzing potential...'"
        elif ratio >= 0.5:
            return f"{name} can't seem to focus on you. *frustrated clicking* Are you even there?"
        else:
            return f"{name} shows you at 1000x magnification. *brutal clarity* The flaws. ALL the flaws."
    
    # Flask
    if "flask" in name_lower:
        if "troubling" in name_lower:
             if ratio >= 2.0:
                return f"{name} contains a storm. *thunderous glass* 'CHAOS HARNESSED! WE RIDE THE LIGHTNING!'"
             elif ratio >= 1.0:
                return f"{name} swirls with ominous smoke. *spooky bubble* 'Dangerously adequate.'"
             elif ratio >= 0.5:
                return f"{name} vibrates with instability. *nervous glass clatter* 'Run. Just... run.'"
             else:
                return f"{name} shatters metaphorically. *emotional breakdown* 'I can't contain this much failure.'"

        if ratio >= 2.0:
            return f"{name} bubbles with multicolored joy. *excited chemistry* Reaction: EXOTHERMIC APPROVAL!"
        elif ratio >= 1.0:
            return f"{name} maintains a stable reaction. *professional bubbling* 'Controlled. As all things should be.'"
        elif ratio >= 0.5:
            return f"{name} fizzes ominously. *warning bubbles* Something's precipitating. Probably disappointment."
        else:
            return f"{name} explodes dramatically. *scientific rejection* Hypothesis: You. Conclusion: DENIED."
    
    # Tesla Coil
    if "tesla" in name_lower or "coil" in name_lower or "sparky" in name_lower:
        if "foil" in name_lower:
             if ratio >= 2.0:
                return f"{name} glows through the foil wrapper. *contained brilliance* 'The energy is safe! And MAXIMUM!'"
             elif ratio >= 1.0:
                return f"{name} crinkles electrically. *static discharge* 'Stored charge: Sufficient.'"
             elif ratio >= 0.5:
                return f"{name} rustles. *metallic crinkle* 'Insulation holding. Boredom increasing.'"
             else:
                return f"{name} grounds itself. *zap* 'Static shock delivered. Wake up.'"

        if ratio >= 2.0:
            return f"{name} arcs brilliant lightning toward you. *ZZZAP!* 'EUREKA ENERGY DETECTED!'"
        elif ratio >= 1.0:
            return f"{name} crackles thoughtfully. *moderate zapping* 'Electrical potential: Acceptable.'"
        elif ratio >= 0.5:
            return f"{name} sparks weakly. *tired fizz* 'Low voltage. Needs charging. Much like you.'"
        else:
            return f"{name} shocks you just a little. *petty zap* That was intentional. You're not grounded enough."
    
    # DNA/RNA Helix
    if "dna" in name_lower or "rna" in name_lower or "helix" in name_lower:
        if "rna" in name_lower:
             if ratio >= 2.0:
                return f"{name} unzips and replicates instantly. *viral success* 'MESSAGE RECEIVED! SPREADING SUCCESS!'"
             elif ratio >= 1.0:
                return f"{name} transcribes a protein. *biological work* 'Building a better you. Slowly.'"
             elif ratio >= 0.5:
                return f"{name} misreads a codon. *mutation warning* 'Wait... that's not right.'"
             else:
                return f"{name} dissolves. *enzyme attack* 'Bad code deleted. System purge.'"

        if ratio >= 2.0:
            return f"{name} spirals gracefully in your direction. *genetic approval* Your code: OPTIMIZED."
        elif ratio >= 1.0:
            return f"{name} rotates steadily. *molecular contemplation* 'Base pairs acceptable. No mutations detected.'"
        elif ratio >= 0.5:
            return f"{name} unwinds slightly. *concerned replication* 'Some sequences need... improvement.'"
        else:
            return f"{name} ties itself in a knot. *genetic confusion* It doesn't recognize your potential."
    
    # Generic scientist fallback
    if ratio >= 2.0:
        return f"{name} considers you a breakthrough discovery!"
    elif ratio >= 1.0:
        return f"{name} adds you to the control group. For now."
    else:
        return f"{name} labels you 'Needs Further Study' and files you away."


def _get_generic_flavor(name: str, ratio: float, etype: str) -> str:
    """Generic fallback for unrecognized entities."""
    if etype == "speaks":
        if ratio >= 2.0:
            return f"{name} nods approvingly. 'Now THIS is what I've been waiting for!'"
        elif ratio >= 1.0:
            return f"{name} considers you carefully. 'Hmm. Potential detected. Proceed.'"
        elif ratio >= 0.5:
            return f"{name} raises an eyebrow. 'Getting there. Keep at it.'"
        else:
            return f"{name} sighs. 'We'll revisit this conversation later. Much later.'"
    elif etype == "sounds":
        if ratio >= 2.0:
            return f"{name} emits a sound of pure joy. *triumphant resonance*"
        elif ratio >= 1.0:
            return f"{name} hums steadily. *neutral vibration* Acceptable."
        elif ratio >= 0.5:
            return f"{name} makes an uncertain noise. *wavering tone*"
        else:
            return f"{name} goes silent. *pointed absence of sound*"
    else:  # silent
        if ratio >= 2.0:
            return f"{name} seems to radiate approval. *silent but unmistakable approval*"
        elif ratio >= 1.0:
            return f"{name} remains still. Waiting. Judging. *stoic presence*"
        elif ratio >= 0.5:
            return f"{name} somehow conveys skepticism without moving. *doubtful stillness*"
        else:
            return f"{name} turns away. Wait, it doesn't have a front. Yet you KNOW it turned away."


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
