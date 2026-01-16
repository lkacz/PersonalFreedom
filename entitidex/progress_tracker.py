"""
Progress Tracker for the Entitidex System.

Tracks user's collection progress, encounters, failed catches,
and capture history.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from .entity import Entity, EntityCapture
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
    
    # Progress metadata
    current_tier: int = 1
    total_catch_attempts: int = 0
    total_encounters: int = 0
    lucky_catches: int = 0
    
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
        
        Args:
            story_id: The story theme to check
            is_exceptional: True to get entities missing exceptional variant,
                          False to get entities missing normal variant
                          
        Returns:
            List of Entity objects with the specified variant available
        """
        entities = get_entities_for_story(story_id)
        if is_exceptional:
            # Return entities where we DON'T have the exceptional variant
            return [e for e in entities if e.id not in self.exceptional_entities]
        else:
            # Return entities where we DON'T have the normal variant
            return [e for e in entities if e.id not in self.collected_entity_ids]
    
    def has_any_available_variants(self, story_id: str) -> Tuple[bool, bool]:
        """
        Check if there are any normal or exceptional variants available.
        
        Args:
            story_id: The story theme to check
            
        Returns:
            Tuple of (has_normal_available, has_exceptional_available)
        """
        entities = get_entities_for_story(story_id)
        has_normal = any(e.id not in self.collected_entity_ids for e in entities)
        has_exceptional = any(e.id not in self.exceptional_entities for e in entities)
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
            "entities_with_pity": len(self.failed_catches),
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
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EntitidexProgress":
        """Create progress from dictionary."""
        progress = cls()
        
        # Support both old "collected" and new "collected_entity_ids" keys for backwards compatibility
        collected_data = data.get("collected_entity_ids", data.get("collected", []))
        progress.collected_entity_ids = set(collected_data)
        progress.encounters = data.get("encounters", {}).copy()
        progress.failed_catches = data.get("failed_catches", {}).copy()
        progress.exceptional_failed_catches = data.get("exceptional_failed_catches", {}).copy()
        progress.exceptional_entities = data.get("exceptional_entities", {}).copy()
        progress.captures = [
            EntityCapture.from_dict(c) for c in data.get("captures", [])
        ]
        progress.current_tier = data.get("current_tier", 1)
        progress.total_catch_attempts = data.get("total_catch_attempts", 0)
        progress.total_encounters = data.get("total_encounters", 0)
        progress.lucky_catches = data.get("lucky_catches", 0)
        
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
