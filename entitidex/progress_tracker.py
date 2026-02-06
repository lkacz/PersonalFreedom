"""
Progress Tracker for the Entitidex System.

Tracks user's collection progress, encounters, failed catches,
and capture history.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from .entity import Entity, EntityCapture, SavedEncounter
from .entity_pools import get_entities_for_story, get_entity_by_id, get_total_entity_count


@dataclass
class EntitidexProgress:
    """
    Tracks a user's Entitidex collection progress.
    
    This class manages:
    - Which entities have been collected (normal variants)
    - Which exceptional entity variants have been collected (separate from normal)
    - Encounter history (entities seen but not caught)
    - Failed catch attempts (for pity system)
    - Detailed capture records
    """
    
    # Core tracking data - normal variants
    collected_entity_ids: Set[str] = field(default_factory=set)
    encounters: Dict[str, int] = field(default_factory=dict)  # entity_id -> count
    failed_catches: Dict[str, int] = field(default_factory=dict)  # entity_id -> count
    
    # Exceptional entity variants - SEPARATE collectibles (20% encounter chance)
    # Format: {entity_id: {"border": "#HEX", "glow": "#HEX"}}
    exceptional_entities: Dict[str, dict] = field(default_factory=dict)
    # Failed catches for exceptional variants specifically
    exceptional_failed_catches: Dict[str, int] = field(default_factory=dict)
    
    # Detailed capture records
    captures: List[EntityCapture] = field(default_factory=list)
    
    # Saved encounters (postponed bonding attempts - "loot boxes")
    saved_encounters: List[SavedEncounter] = field(default_factory=list)
    
    # Progress metadata
    current_tier: int = 1
    total_catch_attempts: int = 0
    total_encounters: int = 0
    lucky_catches: int = 0
    
    # Theme completion tracking
    # Format: {theme_id: ISO timestamp string of completion}
    theme_completions: Dict[str, str] = field(default_factory=dict)
    # Track if the first-time celebration popup was shown
    celebration_seen: Dict[str, bool] = field(default_factory=dict)
    # Track celebration card click counts per theme for milestone rewards
    celebration_clicks: Dict[str, int] = field(default_factory=dict)
    # Track which quote to show next (separate from click count so milestones don't skip quotes)
    celebration_quote_index: Dict[str, int] = field(default_factory=dict)
    # User preference: enable/disable TTS voice for celebration quotes
    celebration_voice_enabled: bool = True
    
    # ==========================================================================
    # COLLECTION STATE
    # ==========================================================================
    
    def is_collected(self, entity_id: str) -> bool:
        """Check if an entity has been collected."""
        return entity_id in self.collected_entity_ids
    
    def is_encountered(self, entity_id: str) -> bool:
        """Check if an entity has been encountered (seen) before."""
        return entity_id in self.encounters
    
    def get_encounter_count(self, entity_id: str) -> int:
        """Get the number of times an entity has been encountered."""
        return self.encounters.get(entity_id, 0)
    
    def get_failed_attempts(self, entity_id: str, is_exceptional: bool = False) -> int:
        """Get the number of failed catch attempts for an entity variant."""
        if is_exceptional:
            return self.exceptional_failed_catches.get(entity_id, 0)
        return self.failed_catches.get(entity_id, 0)
    
    def is_exceptional(self, entity_id: str) -> bool:
        """Check if an exceptional variant of this entity has been collected."""
        return entity_id in self.exceptional_entities
    
    def get_exceptional_colors(self, entity_id: str) -> Optional[dict]:
        """Get the exceptional color palette for an entity."""
        return self.exceptional_entities.get(entity_id)
    
    def is_variant_available(self, entity_id: str, is_exceptional: bool) -> bool:
        """
        Check if a specific variant (normal or exceptional) can still be encountered.
        
        Args:
            entity_id: The entity ID
            is_exceptional: True for exceptional variant, False for normal
            
        Returns:
            True if this variant hasn't been collected yet
        """
        if is_exceptional:
            return entity_id not in self.exceptional_entities
        else:
            return entity_id not in self.collected_entity_ids
    
    # ==========================================================================
    # RECORDING EVENTS
    # ==========================================================================
    
    def record_encounter(self, entity_id: str) -> None:
        """
        Record that an entity was encountered.
        
        Args:
            entity_id: The ID of the encountered entity
        """
        self.encounters[entity_id] = self.encounters.get(entity_id, 0) + 1
        self.total_encounters += 1
    
    def record_failed_catch(self, entity_id: str, is_exceptional: bool = False) -> None:
        """
        Record a failed catch attempt for a specific variant.
        
        Args:
            entity_id: The ID of the entity that escaped
            is_exceptional: True if this was an exceptional variant encounter
        """
        if is_exceptional:
            self.exceptional_failed_catches[entity_id] = self.exceptional_failed_catches.get(entity_id, 0) + 1
        else:
            self.failed_catches[entity_id] = self.failed_catches.get(entity_id, 0) + 1
        self.total_catch_attempts += 1
    
    def mark_exceptional(self, entity_id: str, colors: dict) -> None:
        """
        Mark an entity as exceptional with unique colors.
        
        Args:
            entity_id: The ID of the exceptional entity
            colors: Dict with "border" and "glow" hex colors
        """
        self.exceptional_entities[entity_id] = colors
    
    def record_successful_catch(
        self,
        entity_id: str,
        hero_power: int,
        probability: float,
        was_lucky: bool = False,
        is_exceptional: bool = False,
        exceptional_colors: Optional[dict] = None,
    ) -> EntityCapture:
        """
        Record a successful entity catch.
        
        Args:
            entity_id: The ID of the caught entity
            hero_power: Hero's power at time of catch
            probability: The catch probability that was rolled against
            was_lucky: Whether this was a lucky catch (<50% odds)
            is_exceptional: True if this was an exceptional variant
            exceptional_colors: Colors dict for exceptional variant
            
        Returns:
            The EntityCapture record that was created
        """
        # Calculate attempts (failed + this success) based on variant
        if is_exceptional:
            attempts = self.exceptional_failed_catches.get(entity_id, 0) + 1
        else:
            attempts = self.failed_catches.get(entity_id, 0) + 1
        
        # Create capture record
        capture = EntityCapture(
            entity_id=entity_id,
            captured_at=datetime.now(),
            hero_power_at_capture=hero_power,
            attempts_before_capture=attempts,
            catch_probability=probability,
            was_lucky_catch=was_lucky,
        )
        
        # Update tracking based on variant
        if is_exceptional:
            # Mark as exceptional with colors
            if exceptional_colors:
                self.exceptional_entities[entity_id] = exceptional_colors
            else:
                # Default colors if none provided
                self.exceptional_entities[entity_id] = {
                    "border": "#FFD700",
                    "glow": "#FFA500"
                }
            # Reset exceptional failed attempts
            if entity_id in self.exceptional_failed_catches:
                del self.exceptional_failed_catches[entity_id]
        else:
            # Normal variant collected
            self.collected_entity_ids.add(entity_id)
            # Reset failed attempts for this entity
            if entity_id in self.failed_catches:
                del self.failed_catches[entity_id]
        
        self.captures.append(capture)
        self.total_catch_attempts += 1
        
        if was_lucky:
            self.lucky_catches += 1
        
        return capture
    
    # ==========================================================================
    # SAVED ENCOUNTERS (Postponed Bonding - "Loot Boxes")
    # ==========================================================================
    
    def save_encounter_for_later(
        self,
        entity_id: str,
        is_exceptional: bool = False,
        catch_probability: float = 0.5,
        hero_power: int = 0,
        encounter_perk_bonus: float = 0.0,
        capture_perk_bonus: float = 0.0,
        exceptional_colors: Optional[dict] = None,
        session_minutes: int = 0,
        was_perfect_session: bool = False,
        story_id: Optional[str] = None,
    ) -> Optional[SavedEncounter]:
        """
        Save an encounter for later instead of attempting bond now.
        
        This allows users to stack up encounters and open them later
        like loot boxes in the Entitidex tab.
        
        Only one instance of each entity variant exists in the universe,
        so the same entity cannot be saved twice or saved if already collected.
        
        Args:
            entity_id: The ID of the encountered entity
            is_exceptional: Whether this is an exceptional variant
            catch_probability: The bonding probability at encounter time
            hero_power: User's power when encountered
            encounter_perk_bonus: Encounter bonus from perks
            capture_perk_bonus: Capture bonus from perks
            exceptional_colors: Colors dict for exceptional variant
            session_minutes: Session duration that triggered this
            was_perfect_session: Whether session was distraction-free
            story_id: The story/hero theme that had the encounter (for fair recalculation)
            
        Returns:
            The SavedEncounter that was created, or None if entity already saved/collected
        """
        # Check if entity is already saved (same variant type)
        saved_ids = self.get_saved_entity_ids(is_exceptional=is_exceptional)
        if entity_id in saved_ids:
            return None  # Entity already saved for later
        
        # Check if entity is already collected
        if is_exceptional:
            if entity_id in self.exceptional_entities:
                return None  # Exceptional variant already collected
        else:
            if entity_id in self.collected_entity_ids:
                return None  # Normal variant already collected
        
        # Get current failed attempts for this variant (preserved for pity)
        if is_exceptional:
            failed_attempts = self.exceptional_failed_catches.get(entity_id, 0)
        else:
            failed_attempts = self.failed_catches.get(entity_id, 0)
        
        saved = SavedEncounter(
            entity_id=entity_id,
            is_exceptional=is_exceptional,
            catch_probability=catch_probability,
            hero_power_at_encounter=hero_power,
            failed_attempts=failed_attempts,
            encounter_perk_bonus=encounter_perk_bonus,
            capture_perk_bonus=capture_perk_bonus,
            exceptional_colors=exceptional_colors,
            session_minutes=session_minutes,
            was_perfect_session=was_perfect_session,
            story_id_at_encounter=story_id,
        )
        
        self.saved_encounters.append(saved)
        return saved
    
    def get_saved_encounter_count(self) -> int:
        """Get the number of saved encounters waiting to be opened."""
        return len(self.saved_encounters)
    
    def get_saved_encounters(self) -> List[SavedEncounter]:
        """Get all saved encounters, sorted by save date (oldest first)."""
        return sorted(self.saved_encounters, key=lambda e: e.saved_at)
    
    def pop_saved_encounter(self, index: int = 0) -> Optional[SavedEncounter]:
        """
        Remove and return a saved encounter by index.
        
        Args:
            index: Index of the encounter to pop (default: oldest first)
            
        Returns:
            The SavedEncounter or None if index invalid
        """
        sorted_encounters = self.get_saved_encounters()
        if 0 <= index < len(sorted_encounters):
            encounter = sorted_encounters[index]
            self.saved_encounters.remove(encounter)
            return encounter
        return None
    
    def pop_saved_encounter_by_entity(
        self, 
        entity_id: str, 
        is_exceptional: Optional[bool] = None
    ) -> Optional[SavedEncounter]:
        """
        Remove and return a saved encounter for a specific entity.
        
        Args:
            entity_id: The entity ID to find
            is_exceptional: If specified, match only this variant type
            
        Returns:
            The SavedEncounter or None if not found
        """
        for encounter in self.saved_encounters:
            if encounter.entity_id == entity_id:
                if is_exceptional is None or encounter.is_exceptional == is_exceptional:
                    self.saved_encounters.remove(encounter)
                    return encounter
        return None
    
    def clear_saved_encounters(self) -> int:
        """
        Clear all saved encounters.
        
        Returns:
            Number of encounters that were cleared
        """
        count = len(self.saved_encounters)
        self.saved_encounters.clear()
        return count
    
    def get_saved_entity_ids(self, is_exceptional: Optional[bool] = None) -> Set[str]:
        """
        Get set of entity IDs currently in saved encounters.
        
        Saved entities are "reserved" and shouldn't appear in wild encounters.
        
        Args:
            is_exceptional: If None, return all saved IDs. 
                           If True, only exceptional saved IDs.
                           If False, only normal saved IDs.
        
        Returns:
            Set of entity IDs that are saved for later
        """
        if is_exceptional is None:
            return {e.entity_id for e in self.saved_encounters}
        return {e.entity_id for e in self.saved_encounters if e.is_exceptional == is_exceptional}
    
    # ==========================================================================
    # PROGRESS CALCULATIONS
    # ==========================================================================
    
    def get_collection_count(self, story_id: Optional[str] = None) -> int:
        """
        Get count of collected entities.
        
        Args:
            story_id: If provided, count only for this story theme
            
        Returns:
            Number of collected entities
        """
        if story_id is None:
            return len(self.collected_entity_ids)
        
        # Count for specific story
        count = 0
        for entity_id in self.collected_entity_ids:
            if entity_id.startswith(story_id):
                count += 1
        return count
    
    def get_collection_rate(self, story_id: Optional[str] = None) -> float:
        """
        Get collection completion rate as a percentage.
        
        Args:
            story_id: If provided, calculate only for this story theme
            
        Returns:
            Percentage between 0.0 and 1.0
        """
        if story_id is None:
            total = get_total_entity_count()
            collected = len(self.collected_entity_ids)
        else:
            entities = get_entities_for_story(story_id)
            total = len(entities)
            collected = self.get_collection_count(story_id)
        
        if total == 0:
            return 0.0
        
        return collected / total
    
    def get_uncollected_entity_ids(self, story_id: str) -> List[str]:
        """
        Get list of entity IDs not yet collected for a story.
        
        Args:
            story_id: The story theme to check
            
        Returns:
            List of uncollected entity IDs
        """
        entities = get_entities_for_story(story_id)
        uncollected = []
        
        for entity in entities:
            if entity.id not in self.collected_entity_ids:
                uncollected.append(entity.id)
        
        return uncollected
    
    def get_uncollected_entities(self, story_id: str) -> List[Entity]:
        """
        Get list of Entity objects not yet collected for a story.
        
        Note: This returns entities where the NORMAL variant isn't collected.
        Use get_available_entity_variants for the new dual-track system.
        
        Args:
            story_id: The story theme to check
            
        Returns:
            List of uncollected Entity objects
        """
        entities = get_entities_for_story(story_id)
        return [e for e in entities if e.id not in self.collected_entity_ids]
    
    def get_available_entity_variants(
        self, story_id: str, is_exceptional: bool
    ) -> List[Entity]:
        """
        Get entities that have the specified variant still available.
        
        Excludes entities that are:
        - Already collected (for that variant)
        - Currently saved for later (reserved)
        
        Args:
            story_id: The story theme to check
            is_exceptional: True to get entities missing exceptional variant,
                          False to get entities missing normal variant
                          
        Returns:
            List of Entity objects with the specified variant available
        """
        entities = get_entities_for_story(story_id)
        # Get IDs of saved entities (reserved, can't appear in wild)
        saved_ids = self.get_saved_entity_ids(is_exceptional)
        
        if is_exceptional:
            # Return entities where we DON'T have the exceptional variant
            # AND it's not saved for later
            return [e for e in entities 
                    if e.id not in self.exceptional_entities 
                    and e.id not in saved_ids]
        else:
            # Return entities where we DON'T have the normal variant
            # AND it's not saved for later
            return [e for e in entities 
                    if e.id not in self.collected_entity_ids 
                    and e.id not in saved_ids]
    
    def has_any_available_variants(self, story_id: str) -> Tuple[bool, bool]:
        """
        Check if there are any normal or exceptional variants available.
        
        Excludes entities that are saved for later (reserved).
        
        Args:
            story_id: The story theme to check
            
        Returns:
            Tuple of (has_normal_available, has_exceptional_available)
        """
        entities = get_entities_for_story(story_id)
        saved_normal = self.get_saved_entity_ids(is_exceptional=False)
        saved_exceptional = self.get_saved_entity_ids(is_exceptional=True)
        
        has_normal = any(
            e.id not in self.collected_entity_ids and e.id not in saved_normal 
            for e in entities
        )
        has_exceptional = any(
            e.id not in self.exceptional_entities and e.id not in saved_exceptional 
            for e in entities
        )
        return has_normal, has_exceptional
    
    def get_catch_success_rate(self) -> float:
        """
        Calculate overall catch success rate.
        
        Returns:
            Success rate between 0.0 and 1.0
        """
        if self.total_catch_attempts == 0:
            return 0.0
        
        successful = len(self.captures)
        return successful / self.total_catch_attempts
    
    # ==========================================================================
    # CAPTURE HISTORY
    # ==========================================================================
    
    def get_capture_for_entity(self, entity_id: str) -> Optional[EntityCapture]:
        """
        Get the capture record for a specific entity.
        
        Args:
            entity_id: The entity to look up
            
        Returns:
            EntityCapture if found, None otherwise
        """
        for capture in self.captures:
            if capture.entity_id == entity_id:
                return capture
        return None
    
    def get_recent_captures(self, limit: int = 5) -> List[EntityCapture]:
        """
        Get most recent captures.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of most recent EntityCapture records
        """
        sorted_captures = sorted(
            self.captures,
            key=lambda c: c.captured_at,
            reverse=True
        )
        return sorted_captures[:limit]
    
    def get_lucky_capture_ids(self) -> List[str]:
        """Get IDs of all entities caught with lucky catches."""
        return [c.entity_id for c in self.captures if c.was_lucky_catch]
    
    # ==========================================================================
    # STATISTICS
    # ==========================================================================
    
    def get_statistics(self, story_id: Optional[str] = None) -> dict:
        """
        Get comprehensive statistics about collection progress.
        
        Args:
            story_id: If provided, stats are scoped to this story
            
        Returns:
            Dictionary of statistics
        """
        if story_id:
            collected = self.get_collection_count(story_id)
            total = len(get_entities_for_story(story_id))
        else:
            collected = len(self.collected_entity_ids)
            total = get_total_entity_count()
        
        return {
            "collected": collected,
            "total": total,
            "completion_rate": self.get_collection_rate(story_id),
            "total_encounters": self.total_encounters,
            "total_catch_attempts": self.total_catch_attempts,
            "catch_success_rate": self.get_catch_success_rate(),
            "lucky_catches": self.lucky_catches,
            "current_tier": self.current_tier,
            "entities_with_pity": len(self.failed_catches) + len(self.exceptional_failed_catches),
        }
    
    # ==========================================================================
    # SERIALIZATION
    # ==========================================================================
    
    def to_dict(self) -> dict:
        """Convert progress to dictionary for saving."""
        return {
            "collected_entity_ids": list(self.collected_entity_ids),
            "encounters": self.encounters.copy(),
            "failed_catches": self.failed_catches.copy(),
            "exceptional_failed_catches": self.exceptional_failed_catches.copy(),
            "exceptional_entities": self.exceptional_entities.copy(),
            "captures": [c.to_dict() for c in self.captures],
            "current_tier": self.current_tier,
            "total_catch_attempts": self.total_catch_attempts,
            "total_encounters": self.total_encounters,
            "lucky_catches": self.lucky_catches,
            "saved_encounters": [e.to_dict() for e in self.saved_encounters],
            "theme_completions": self.theme_completions.copy(),
            "celebration_seen": self.celebration_seen.copy(),
            "celebration_clicks": self.celebration_clicks.copy(),
            "celebration_quote_index": self.celebration_quote_index.copy(),
            "celebration_voice_enabled": self.celebration_voice_enabled,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EntitidexProgress":
        """Create progress from dictionary."""
        progress = cls()

        if not isinstance(data, dict):
            return progress

        def _as_non_negative_int(value, default=0) -> int:
            try:
                parsed = int(value)
            except (TypeError, ValueError):
                return default
            return max(0, parsed)

        def _sanitize_counter(raw) -> Dict[str, int]:
            if not isinstance(raw, dict):
                return {}
            cleaned = {}
            for key, value in raw.items():
                try:
                    count = int(value)
                except (TypeError, ValueError):
                    continue
                if count < 0:
                    continue
                cleaned[str(key)] = count
            return cleaned

        def _sanitize_int_map(raw) -> Dict[str, int]:
            return _sanitize_counter(raw)

        def _sanitize_bool_map(raw) -> Dict[str, bool]:
            if not isinstance(raw, dict):
                return {}
            return {str(k): bool(v) for k, v in raw.items()}

        def _sanitize_str_map(raw) -> Dict[str, str]:
            if not isinstance(raw, dict):
                return {}
            return {str(k): str(v) for k, v in raw.items()}

        def _sanitize_exceptional_entities(raw) -> Dict[str, dict]:
            if not isinstance(raw, dict):
                return {}
            cleaned = {}
            for entity_id, colors in raw.items():
                if not isinstance(colors, dict):
                    continue
                border = colors.get("border", "#FFD700")
                glow = colors.get("glow", "#FFA500")
                if not isinstance(border, str):
                    border = "#FFD700"
                if not isinstance(glow, str):
                    glow = "#FFA500"
                cleaned[str(entity_id)] = {"border": border, "glow": glow}
            return cleaned

        def _parse_capture_records(raw) -> List[EntityCapture]:
            if not isinstance(raw, list):
                return []
            parsed = []
            for item in raw:
                if not isinstance(item, dict):
                    continue
                try:
                    parsed.append(EntityCapture.from_dict(item))
                except Exception:
                    continue
            return parsed

        def _parse_saved_encounters(raw) -> List[SavedEncounter]:
            if not isinstance(raw, list):
                return []
            parsed = []
            for item in raw:
                if not isinstance(item, dict):
                    continue
                try:
                    parsed.append(SavedEncounter.from_dict(item))
                except Exception:
                    continue
            return parsed

        # Support both old "collected" and new "collected_entity_ids" keys.
        collected_data = data.get("collected_entity_ids", data.get("collected", []))
        if isinstance(collected_data, dict):
            collected_ids = [k for k, is_present in collected_data.items() if bool(is_present)]
        elif isinstance(collected_data, (list, set, tuple)):
            collected_ids = [entity_id for entity_id in collected_data if isinstance(entity_id, str)]
        else:
            collected_ids = []

        progress.collected_entity_ids = set(collected_ids)
        progress.encounters = _sanitize_counter(data.get("encounters"))
        progress.failed_catches = _sanitize_counter(data.get("failed_catches"))
        progress.exceptional_failed_catches = _sanitize_counter(data.get("exceptional_failed_catches"))
        progress.exceptional_entities = _sanitize_exceptional_entities(data.get("exceptional_entities"))
        progress.captures = _parse_capture_records(data.get("captures"))
        progress.current_tier = max(1, _as_non_negative_int(data.get("current_tier", 1), default=1))
        progress.total_catch_attempts = _as_non_negative_int(data.get("total_catch_attempts", 0), default=0)
        progress.total_encounters = _as_non_negative_int(data.get("total_encounters", 0), default=0)
        progress.lucky_catches = _as_non_negative_int(data.get("lucky_catches", 0), default=0)
        progress.saved_encounters = _parse_saved_encounters(data.get("saved_encounters"))
        progress.theme_completions = _sanitize_str_map(data.get("theme_completions"))
        progress.celebration_seen = _sanitize_bool_map(data.get("celebration_seen"))
        progress.celebration_clicks = _sanitize_int_map(data.get("celebration_clicks"))
        progress.celebration_quote_index = _sanitize_int_map(data.get("celebration_quote_index"))

        voice_enabled = data.get("celebration_voice_enabled", True)
        progress.celebration_voice_enabled = voice_enabled if isinstance(voice_enabled, bool) else True
        
        return progress
    
    # ==========================================================================
    # DISPLAY HELPERS
    # ==========================================================================
    
    def get_progress_display(self, story_id: str) -> str:
        """
        Get a display string for story progress.
        
        Args:
            story_id: The story to show progress for
            
        Returns:
            String like "6/9 (66.7%)"
        """
        collected = self.get_collection_count(story_id)
        total = len(get_entities_for_story(story_id))
        rate = self.get_collection_rate(story_id) * 100
        
        return f"{collected}/{total} ({rate:.1f}%)"
    
    def is_collection_complete(self, story_id: Optional[str] = None) -> bool:
        """
        Check if collection is complete.
        
        Args:
            story_id: If provided, check only this story
            
        Returns:
            True if all entities are collected
        """
        return self.get_collection_rate(story_id) >= 1.0
    
    # ==========================================================================
    # THEME COMPLETION TRACKING
    # ==========================================================================
    
    def is_theme_fully_complete(self, theme_id: str) -> bool:
        """
        Check if ALL variants (normal + exceptional) are collected for a theme.
        
        This is the requirement for unlocking the celebration card.
        
        Args:
            theme_id: The theme identifier (e.g., "warrior", "scholar")
            
        Returns:
            True if every entity in the theme has BOTH normal and exceptional collected
        """
        entities = get_entities_for_story(theme_id)
        
        for entity in entities:
            # Must have normal variant
            if entity.id not in self.collected_entity_ids:
                return False
            # Must have exceptional variant
            if entity.id not in self.exceptional_entities:
                return False
        
        return len(entities) > 0  # Must have at least 1 entity
    
    def get_theme_completion_stats(self, theme_id: str) -> dict:
        """
        Get detailed completion statistics for a theme.
        
        Args:
            theme_id: The theme identifier
            
        Returns:
            Dict with normal_collected, exceptional_collected, total, percent, etc.
        """
        entities = get_entities_for_story(theme_id)
        total = len(entities)
        
        normal_collected = sum(
            1 for e in entities if e.id in self.collected_entity_ids
        )
        exceptional_collected = sum(
            1 for e in entities if e.id in self.exceptional_entities
        )
        
        # Total slots = normal + exceptional for each entity
        total_slots = total * 2
        total_collected = normal_collected + exceptional_collected
        percent = (total_collected / total_slots * 100) if total_slots > 0 else 0
        
        return {
            "theme_id": theme_id,
            "total_entities": total,
            "normal_collected": normal_collected,
            "exceptional_collected": exceptional_collected,
            "total_slots": total_slots,
            "total_collected": total_collected,
            "percent": percent,
            "is_complete": self.is_theme_fully_complete(theme_id),
            "completion_date": self.theme_completions.get(theme_id),
            "celebration_seen": self.celebration_seen.get(theme_id, False),
        }
    
    def record_theme_completion(self, theme_id: str) -> bool:
        """
        Record that a theme was just completed (if not already recorded).
        
        Call this after a successful catch to check if completion was achieved.
        
        Args:
            theme_id: The theme that may have been completed
            
        Returns:
            True if this is a NEW completion (first time)
        """
        if theme_id in self.theme_completions:
            return False  # Already recorded
        
        if self.is_theme_fully_complete(theme_id):
            self.theme_completions[theme_id] = datetime.now().isoformat()
            return True
        
        return False
    
    def mark_celebration_seen(self, theme_id: str) -> None:
        """Mark that the celebration popup was shown for a theme."""
        self.celebration_seen[theme_id] = True
    
    def has_seen_celebration(self, theme_id: str) -> bool:
        """Check if the celebration popup was already shown."""
        return self.celebration_seen.get(theme_id, False)
    
    def get_completed_themes(self) -> list:
        """Get list of theme IDs that have been fully completed."""
        return list(self.theme_completions.keys())
