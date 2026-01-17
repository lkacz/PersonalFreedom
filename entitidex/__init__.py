"""
Entitidex - Collectible Companion System

A Pokemon Go-style collection feature where users encounter and bond with
story-themed entities after completing focus sessions.
"""

from .entity import Entity, EntityCapture, SavedEncounter
from .entity_pools import ENTITY_POOLS, get_entities_for_story, get_entity_by_id
from .catch_mechanics import (
    calculate_join_probability,
    apply_pity_bonus,
    attempt_catch,
    CATCH_CONFIG,
)
from .progress_tracker import EntitidexProgress
from .encounter_system import (
    should_trigger_encounter,
    select_encounter_entity,
    roll_encounter_chance,
    ENCOUNTER_CONFIG,
)
from .entitidex_manager import EntitidexManager
from .theme_completion import (
    ThemeCelebration,
    THEME_CELEBRATIONS,
    get_theme_celebration,
    get_all_theme_ids,
)
from .celebration_audio import (
    CelebrationAudioManager,
    play_celebration_sound,
    preload_celebration_sounds,
)

__all__ = [
    # Data models
    "Entity",
    "EntityCapture",
    "SavedEncounter",
    "EntitidexProgress",
    # Entity data
    "ENTITY_POOLS",
    "get_entities_for_story",
    "get_entity_by_id",
    # Catch mechanics
    "calculate_join_probability",
    "apply_pity_bonus",
    "attempt_catch",
    "CATCH_CONFIG",
    # Encounter system
    "should_trigger_encounter",
    "select_encounter_entity",
    "roll_encounter_chance",
    "ENCOUNTER_CONFIG",
    # Manager
    "EntitidexManager",
    # Theme completion
    "ThemeCelebration",
    "THEME_CELEBRATIONS",
    "get_theme_celebration",
    "get_all_theme_ids",
    # Celebration audio
    "CelebrationAudioManager",
    "play_celebration_sound",
    "preload_celebration_sounds",
]

__version__ = "1.0.0"
