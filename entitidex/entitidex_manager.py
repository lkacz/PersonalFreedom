"""
Entitidex Manager - Core orchestration for the Entitidex system.

Provides a high-level API for managing entity encounters, catches,
and collection progress. This is the main interface for integrating
the Entitidex system with the rest of the application.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List

from .entity import Entity, EntityCapture
from .entity_pools import get_entities_for_story, get_entity_by_id
from .progress_tracker import EntitidexProgress
from .catch_mechanics import (
    get_final_probability,
    attempt_catch,
    is_lucky_catch,
    get_probability_description,
    format_probability_display,
)
from .encounter_system import (
    should_trigger_encounter,
    select_encounter_entity,
    roll_encounter_chance,
    get_encounter_announcement,
    get_encounter_flavor_text,
    get_next_recommended_entity,
)


@dataclass
class EncounterResult:
    """Result of an encounter trigger check."""
    
    occurred: bool
    entity: Optional[Entity] = None
    is_first_encounter: bool = False
    is_exceptional: bool = False  # True if this is an exceptional variant (20% chance)
    announcement: str = ""
    flavor_text: str = ""
    catch_probability: float = 0.0
    probability_display: str = ""
    probability_description: str = ""
    perk_bonus_applied: bool = False  # True if entity perks contributed to encounter/capture
    encounter_perk_bonus: float = 0.0  # Encounter chance bonus from perks (percentage)
    capture_perk_bonus: float = 0.0  # Capture probability bonus from perks (percentage)
    city_encounter_bonus: float = 0.0  # Encounter chance bonus from Observatory (percentage)
    city_catch_bonus: float = 0.0  # Capture bonus from University (percentage)


@dataclass
class CatchResult:
    """Result of a catch attempt."""
    
    success: bool
    entity: Entity
    probability: float
    message: str
    was_lucky: bool = False
    capture_record: Optional[EntityCapture] = None


class EntitidexManager:
    """
    Main manager for the Entitidex system.
    
    Coordinates encounters, catches, and progress tracking.
    Provides a clean API for the UI layer.
    
    Usage:
        manager = EntitidexManager(progress, story_id="warrior", hero_power=500)
        
        # After session completion
        encounter = manager.check_for_encounter(
            session_minutes=30,
            was_perfect_session=True
        )
        
        if encounter.occurred:
            # Show encounter dialog with encounter.entity
            result = manager.attempt_catch()
            if result.success:
                # Celebration!
    """
    
    def __init__(
        self,
        progress: Optional[EntitidexProgress] = None,
        story_id: str = "warrior",
        hero_power: int = 0,
        luck_bonus: float = 0.0,
        active_perks: Optional[Dict] = None,
        city_catch_bonus: float = 0.0,
        city_encounter_bonus: float = 0.0,
        adhd_buster: dict = None,
    ):
        """
        Initialize the Entitidex manager.
        
        Args:
            progress: User's progress (created fresh if None)
            story_id: Current active story theme
            hero_power: Hero's current total power
            luck_bonus: Any luck bonus from equipped items
            active_perks: Dictionary of active entity perks (from entity_perks.py)
            city_catch_bonus: Bonus from city buildings (University) - percentage
            city_encounter_bonus: Bonus from city buildings (Observatory) - percentage
            adhd_buster: Hero data dict for daily encounter tracking (diminishing returns)
        """
        self.progress = progress or EntitidexProgress()
        self.story_id = story_id
        self.hero_power = hero_power
        self.luck_bonus = luck_bonus
        self.active_perks = active_perks or {}
        self.city_catch_bonus = city_catch_bonus
        self.city_encounter_bonus = city_encounter_bonus
        self.adhd_buster = adhd_buster  # For daily encounter tracking
        
        # Current encounter state
        self._current_encounter: Optional[Entity] = None
        self._current_encounter_is_exceptional: bool = False
    
    # =========================================================================
    # CONFIGURATION
    # =========================================================================
    
    def set_story(self, story_id: str) -> None:
        """Change the active story theme."""
        self.story_id = story_id
    
    def set_hero_power(self, power: int) -> None:
        """Update the hero's power level."""
        self.hero_power = power
    
    def set_luck_bonus(self, bonus: float) -> None:
        """Update luck bonus from equipped items."""
        self.luck_bonus = bonus
    
    def set_active_perks(self, perks: Dict) -> None:
        """Update active entity perks."""
        self.active_perks = perks or {}
    
    # =========================================================================
    # ENCOUNTER HANDLING
    # =========================================================================
    
    def check_for_encounter(
        self,
        session_minutes: int,
        minimum_session_minutes: int = 25,
        was_perfect_session: bool = False,
        streak_days: int = 0,
        was_bypass_used: bool = False,
    ) -> EncounterResult:
        """
        Check if an entity encounter occurs after a focus session.
        
        This is the main entry point after a session completes.
        
        Args:
            session_minutes: Duration of the completed session
            minimum_session_minutes: Minimum required session length
            was_perfect_session: True if no bypass was attempted
            streak_days: Consecutive days with sessions
            was_bypass_used: True if bypass was used (no encounter)
            
        Returns:
            EncounterResult with encounter details if one occurred
        """
        # Check if encounter triggers (now with perk support)
        should_trigger = should_trigger_encounter(
            session_minutes=session_minutes,
            minimum_session_minutes=minimum_session_minutes,
            was_perfect_session=was_perfect_session,
            streak_days=streak_days,
            was_bypass_used=was_bypass_used,
            active_perks=self.active_perks,
            city_encounter_bonus=self.city_encounter_bonus,
            adhd_buster=self.adhd_buster,
        )
        
        if not should_trigger:
            return EncounterResult(occurred=False)
        
        # Select which entity appears (now returns tuple with is_exceptional)
        entity, is_exceptional = select_encounter_entity(
            progress=self.progress,
            hero_power=self.hero_power,
            story_id=self.story_id,
        )
        
        if entity is None:
            # Collection complete!
            return EncounterResult(occurred=False)
        
        # Record the encounter
        is_first = not self.progress.is_encountered(entity.id)
        self.progress.record_encounter(entity.id)
        
        # Store current encounter for catch attempt (including exceptional status)
        self._current_encounter = entity
        self._current_encounter_is_exceptional = is_exceptional
        
        # Calculate catch probability (use variant-specific failed attempts)
        failed_attempts = self.progress.get_failed_attempts(entity.id, is_exceptional)
        
        # Combine luck_bonus with entity perk capture bonus
        total_luck_bonus = self.luck_bonus
        capture_perk = 0.0
        encounter_perk = 0.0
        if self.active_perks:
            from .entity_perks import PerkType
            capture_bonus = self.active_perks.get(PerkType.CAPTURE_BONUS, 0)
            encounter_bonus = self.active_perks.get(PerkType.ENCOUNTER_CHANCE, 0)
            if capture_bonus > 0:
                total_luck_bonus += capture_bonus / 100.0  # Convert to probability bonus
                capture_perk = capture_bonus
                print(f"[Entity Perks] ✨ Capture boosted by +{capture_bonus}% from collected entities!")
            if encounter_bonus > 0:
                encounter_perk = encounter_bonus
        
        probability = get_final_probability(
            hero_power=self.hero_power,
            entity_power=entity.power,
            failed_attempts=failed_attempts,
            luck_bonus=total_luck_bonus,
            city_bonus=self.city_catch_bonus,
        )
        
        perk_bonus = capture_perk > 0 or encounter_perk > 0
        city_bonus_applied = self.city_encounter_bonus > 0 or self.city_catch_bonus > 0
        
        return EncounterResult(
            occurred=True,
            entity=entity,
            is_first_encounter=is_first,
            is_exceptional=is_exceptional,
            announcement=get_encounter_announcement(entity, is_first, is_exceptional),
            flavor_text=get_encounter_flavor_text(entity, self.hero_power, is_exceptional),
            catch_probability=probability,
            probability_display=format_probability_display(probability),
            probability_description=get_probability_description(probability),
            perk_bonus_applied=perk_bonus or city_bonus_applied,
            encounter_perk_bonus=encounter_perk,
            capture_perk_bonus=capture_perk,
            city_encounter_bonus=self.city_encounter_bonus,
            city_catch_bonus=self.city_catch_bonus,
        )
    
    def force_encounter(self, entity_id: str) -> Optional[EncounterResult]:
        """
        Force a specific entity encounter (for testing/debugging).
        
        Args:
            entity_id: ID of the entity to encounter
            
        Returns:
            EncounterResult or None if entity not found
        """
        entity = get_entity_by_id(entity_id)
        
        if entity is None:
            return None
        
        is_first = not self.progress.is_encountered(entity.id)
        self.progress.record_encounter(entity.id)
        self._current_encounter = entity
        self._current_encounter_is_exceptional = False  # Debug encounters default to normal
        
        failed_attempts = self.progress.get_failed_attempts(entity.id)
        
        # Apply entity perk capture bonus
        total_luck_bonus = self.luck_bonus
        capture_perk = 0.0
        if self.active_perks:
            from .entity_perks import PerkType
            capture_bonus = self.active_perks.get(PerkType.CAPTURE_BONUS, 0)
            if capture_bonus > 0:
                total_luck_bonus += capture_bonus / 100.0
                capture_perk = capture_bonus
        
        probability = get_final_probability(
            hero_power=self.hero_power,
            entity_power=entity.power,
            failed_attempts=failed_attempts,
            luck_bonus=total_luck_bonus,
            city_bonus=self.city_catch_bonus,
        )
        
        return EncounterResult(
            occurred=True,
            entity=entity,
            is_first_encounter=is_first,
            announcement=get_encounter_announcement(entity, is_first),
            flavor_text=get_encounter_flavor_text(entity, self.hero_power),
            catch_probability=probability,
            probability_display=format_probability_display(probability),
            probability_description=get_probability_description(probability),
            perk_bonus_applied=capture_perk > 0,
            encounter_perk_bonus=0.0,  # Force encounter bypasses encounter chance
            capture_perk_bonus=capture_perk,
        )
    
    @property
    def has_active_encounter(self) -> bool:
        """Check if there's an active encounter waiting for catch attempt."""
        return self._current_encounter is not None
    
    @property
    def current_encounter(self) -> Optional[Entity]:
        """Get the current encountered entity."""
        return self._current_encounter
    
    def dismiss_encounter(self) -> None:
        """Dismiss the current encounter without attempting to catch."""
        self._current_encounter = None
        self._current_encounter_is_exceptional = False
    
    # =========================================================================
    # CATCH HANDLING
    # =========================================================================
    
    def attempt_catch(
        self, 
        entity: Optional[Entity] = None,
        is_exceptional: Optional[bool] = None,
        exceptional_colors: Optional[dict] = None,
    ) -> Optional[CatchResult]:
        """
        Attempt to catch the current or specified entity.
        
        Args:
            entity: Entity to catch (uses current encounter if None)
            is_exceptional: True if this is an exceptional variant attempt
                           (uses stored value if None)
            exceptional_colors: Colors to use for exceptional variant
            
        Returns:
            CatchResult with outcome, or None if no encounter active
        """
        target = entity or self._current_encounter
        
        if target is None:
            return None
        
        # Use provided is_exceptional or fall back to stored state
        exceptional = is_exceptional if is_exceptional is not None else self._current_encounter_is_exceptional
        
        # Get failed attempts for pity calculation (specific to the variant)
        failed_attempts = self.progress.get_failed_attempts(target.id, exceptional)
        
        # Apply pity bonus from entity perks (accelerates pity progression)
        effective_failed_attempts = failed_attempts
        if self.active_perks:
            from .entity_perks import PerkType
            pity_bonus_pct = self.active_perks.get(PerkType.PITY_BONUS, 0)
            if pity_bonus_pct > 0:
                # Boost effective failed attempts by the perk percentage
                # e.g. 20% bonus with 5 fails = 6 effective fails
                effective_failed_attempts = int(failed_attempts * (1 + pity_bonus_pct / 100.0))
        
        # Combine luck_bonus with entity perk capture bonus
        total_luck_bonus = self.luck_bonus
        if self.active_perks:
            from .entity_perks import PerkType
            capture_bonus = self.active_perks.get(PerkType.CAPTURE_BONUS, 0)
            if capture_bonus > 0:
                total_luck_bonus += capture_bonus / 100.0  # Convert to probability bonus
        
        # Attempt the catch
        success, probability, message = attempt_catch(
            hero_power=self.hero_power,
            entity=target,
            failed_attempts=effective_failed_attempts,
            luck_bonus=total_luck_bonus,
        )
        
        was_lucky = is_lucky_catch(probability) if success else False
        capture_record = None
        
        if success:
            # Record successful catch with variant tracking
            capture_record = self.progress.record_successful_catch(
                entity_id=target.id,
                hero_power=self.hero_power,
                probability=probability,
                was_lucky=was_lucky,
                is_exceptional=exceptional,
                exceptional_colors=exceptional_colors,
            )
        else:
            # Record failed attempt for the specific variant
            self.progress.record_failed_catch(target.id, exceptional)
        
        # Clear current encounter state
        self._current_encounter = None
        self._current_encounter_is_exceptional = False
        
        return CatchResult(
            success=success,
            entity=target,
            probability=probability,
            message=message,
            was_lucky=was_lucky,
            capture_record=capture_record,
        )
    
    # =========================================================================
    # COLLECTION INFO
    # =========================================================================
    
    def get_collection_entities(self) -> List[Tuple[Entity, bool]]:
        """
        Get all entities for current story with collection status.
        
        Returns:
            List of (Entity, is_collected) tuples
        """
        entities = get_entities_for_story(self.story_id)
        result = []
        
        for entity in entities:
            is_collected = self.progress.is_collected(entity.id)
            result.append((entity, is_collected))
        
        return result
    
    def get_entity_details(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an entity.
        
        Args:
            entity_id: The entity to look up
            
        Returns:
            Dictionary with entity details and capture info, or None
        """
        entity = get_entity_by_id(entity_id)
        
        if entity is None:
            return None
        
        is_collected = self.progress.is_collected(entity_id)
        capture = self.progress.get_capture_for_entity(entity_id)
        failed_attempts = self.progress.get_failed_attempts(entity_id)
        
        # Calculate current catch probability
        current_prob = get_final_probability(
            hero_power=self.hero_power,
            entity_power=entity.power,
            failed_attempts=failed_attempts,
            luck_bonus=self.luck_bonus,
            city_bonus=self.city_catch_bonus,
        )
        
        return {
            "entity": entity,
            "is_collected": is_collected,
            "is_encountered": self.progress.is_encountered(entity_id),
            "encounter_count": self.progress.get_encounter_count(entity_id),
            "failed_attempts": failed_attempts,
            "capture": capture,
            "current_catch_probability": current_prob,
            "probability_display": format_probability_display(current_prob),
            "probability_description": get_probability_description(current_prob),
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collection statistics for the current story."""
        stats = self.progress.get_statistics(self.story_id)
        
        # Add recommended next entity
        recommended = get_next_recommended_entity(
            progress=self.progress,
            hero_power=self.hero_power,
            story_id=self.story_id,
        )
        stats["recommended_entity"] = recommended
        
        return stats
    
    def get_progress_display(self) -> str:
        """Get progress display string like '6/9 (66.7%)'."""
        return self.progress.get_progress_display(self.story_id)
    
    def is_collection_complete(self) -> bool:
        """Check if current story's collection is complete."""
        return self.progress.is_collection_complete(self.story_id)
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def save_progress(self) -> Dict[str, Any]:
        """
        Get progress data for saving.
        
        Returns:
            Dictionary that can be stored in config
        """
        return self.progress.to_dict()
    
    def load_progress(self, data: Dict[str, Any]) -> None:
        """
        Load progress from saved data.
        
        Args:
            data: Dictionary from save file
        """
        self.progress = EntitidexProgress.from_dict(data)
    
    @classmethod
    def from_config(
        cls,
        config_data: Dict[str, Any],
        story_id: str,
        hero_power: int,
        luck_bonus: float = 0.0,
    ) -> "EntitidexManager":
        """
        Create manager from config data.
        
        Args:
            config_data: The entitidex section from config
            story_id: Current story theme
            hero_power: Hero's current power
            luck_bonus: Luck bonus from items
            
        Returns:
            Configured EntitidexManager instance
        """
        progress = EntitidexProgress.from_dict(config_data) if config_data else None
        
        return cls(
            progress=progress,
            story_id=story_id,
            hero_power=hero_power,
            luck_bonus=luck_bonus,
        )
