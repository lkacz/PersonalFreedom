"""
Entity data model for the Entitidex system.

Defines the Entity class representing collectible companions, and EntityCapture
for recording successful captures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Set, FrozenSet


@dataclass
class Entity:
    """Represents a collectible companion entity."""
    
    id: str                     # Unique identifier (e.g., "warrior_001")
    name: str                   # Display name (e.g., "Hatchling Drake")
    power: int                  # Power level (10-2000)
    rarity: str                 # "common", "uncommon", "rare", "epic", "legendary", "celestial"
    lore: str                   # Flavor text / personality description
    theme_set: str              # "warrior", "scholar", "wanderer", "underdog", "scientist", "robot", "space_pirate", "thief", "zoo_worker"
    
    # Optional fields with defaults
    icon_path: str = ""         # Path to entity icon
    silhouette_path: str = ""   # Path to locked/unknown state icon
    unlock_hint: str = ""       # Cryptic hint about the entity
    collection_tier: int = 1    # Which "page" of collection (for scaling)
    exceptional_name: str = ""  # Playful name variant for exceptional cards
    exceptional_lore: str = ""  # Unique lore for exceptional variant
    
    # City building synergy tags (e.g., {"fire", "crafting"} boosts Forge)
    synergy_tags: FrozenSet[str] = field(default_factory=frozenset)
    
    @property
    def rarity_emoji(self) -> str:
        """Get emoji representation of rarity."""
        return {
            "common": "⚪",
            "uncommon": "🟢",
            "rare": "🔵",
            "epic": "🟣",
            "legendary": "🟡",
            "celestial": "✨",
        }.get(self.rarity, "⚪")
    
    @property
    def rarity_display(self) -> str:
        """Get display text for rarity."""
        return f"{self.rarity_emoji} {self.rarity.upper()}"
    
    @property
    def slot_number(self) -> int:
        """Extract slot number from entity ID (e.g., 'warrior_003' -> 3)."""
        try:
            return int(self.id.split("_")[-1])
        except (ValueError, IndexError):
            return 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "power": self.power,
            "rarity": self.rarity,
            "lore": self.lore,
            "theme_set": self.theme_set,
            "icon_path": self.icon_path,
            "silhouette_path": self.silhouette_path,
            "unlock_hint": self.unlock_hint,
            "collection_tier": self.collection_tier,
            "exceptional_name": self.exceptional_name,
            "exceptional_lore": self.exceptional_lore,
            "synergy_tags": list(self.synergy_tags),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Entity":
        """Create Entity from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            power=data["power"],
            rarity=data["rarity"],
            lore=data.get("lore", ""),
            theme_set=data.get("theme_set", ""),
            icon_path=data.get("icon_path", ""),
            silhouette_path=data.get("silhouette_path", ""),
            unlock_hint=data.get("unlock_hint", ""),
            collection_tier=data.get("collection_tier", 1),
            exceptional_name=data.get("exceptional_name", ""),
            exceptional_lore=data.get("exceptional_lore", ""),
            synergy_tags=frozenset(data.get("synergy_tags", [])),
        )


@dataclass
class EntityCapture:
    """Records details of a captured entity."""
    
    entity_id: str                              # ID of captured entity
    captured_at: datetime = field(default_factory=datetime.now)
    hero_power_at_capture: int = 0              # User's power when caught
    attempts_before_capture: int = 1            # Total attempts including success
    catch_probability: float = 0.5              # What the probability was
    was_lucky_catch: bool = False               # If catch succeeded with <50% odds
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "entity_id": self.entity_id,
            "captured_at": self.captured_at.isoformat(),
            "hero_power_at_capture": self.hero_power_at_capture,
            "attempts_before_capture": self.attempts_before_capture,
            "catch_probability": self.catch_probability,
            "was_lucky_catch": self.was_lucky_catch,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EntityCapture":
        """Create EntityCapture from dictionary."""
        captured_at = data.get("captured_at")
        if isinstance(captured_at, str):
            captured_at = datetime.fromisoformat(captured_at)
        elif captured_at is None:
            captured_at = datetime.now()
            
        return cls(
            entity_id=data["entity_id"],
            captured_at=captured_at,
            hero_power_at_capture=data.get("hero_power_at_capture", 0),
            attempts_before_capture=data.get("attempts_before_capture", 1),
            catch_probability=data.get("catch_probability", 0.5),
            was_lucky_catch=data.get("was_lucky_catch", False),
        )

@dataclass
class SavedEncounter:
    """
    Represents a postponed entity encounter saved for later.
    
    When a user clicks "Save for Later" instead of attempting to bond,
    the encounter is stored with all its parameters preserved. This allows
    users to stack up encounters during work sessions and "open" them later
    like loot boxes in the Entitidex tab.
    
    The story_id_at_encounter field tracks which hero originally had the
    encounter, ensuring probability recalculation is based on that hero's
    power growth (not a different, potentially stronger hero).
    """
    
    entity_id: str                              # ID of the encountered entity
    is_exceptional: bool = False                # Whether this is an exceptional variant
    catch_probability: float = 0.5              # The bonding probability at time of encounter
    hero_power_at_encounter: int = 0            # User's power when encountered
    failed_attempts: int = 0                    # Failed attempts at time of save (for pity)
    saved_at: datetime = field(default_factory=datetime.now)
    encounter_perk_bonus: float = 0.0           # Encounter bonus from perks (preserved)
    capture_perk_bonus: float = 0.0             # Capture bonus from perks (preserved)
    exceptional_colors: Optional[dict] = None   # Colors for exceptional variant
    session_minutes: int = 0                    # Session duration that triggered this
    was_perfect_session: bool = False           # Whether session was distraction-free
    story_id_at_encounter: Optional[str] = None # Story/hero theme when encounter was saved
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "entity_id": self.entity_id,
            "is_exceptional": self.is_exceptional,
            "catch_probability": self.catch_probability,
            "hero_power_at_encounter": self.hero_power_at_encounter,
            "failed_attempts": self.failed_attempts,
            "saved_at": self.saved_at.isoformat(),
            "encounter_perk_bonus": self.encounter_perk_bonus,
            "capture_perk_bonus": self.capture_perk_bonus,
            "exceptional_colors": self.exceptional_colors,
            "session_minutes": self.session_minutes,
            "was_perfect_session": self.was_perfect_session,
            "story_id_at_encounter": self.story_id_at_encounter,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SavedEncounter":
        """Create SavedEncounter from dictionary."""
        saved_at = data.get("saved_at")
        if isinstance(saved_at, str):
            saved_at = datetime.fromisoformat(saved_at)
        elif saved_at is None:
            saved_at = datetime.now()
        
        return cls(
            entity_id=data["entity_id"],
            is_exceptional=data.get("is_exceptional", False),
            catch_probability=data.get("catch_probability", 0.5),
            hero_power_at_encounter=data.get("hero_power_at_encounter", 0),
            failed_attempts=data.get("failed_attempts", 0),
            saved_at=saved_at,
            encounter_perk_bonus=data.get("encounter_perk_bonus", 0.0),
            capture_perk_bonus=data.get("capture_perk_bonus", 0.0),
            exceptional_colors=data.get("exceptional_colors"),
            session_minutes=data.get("session_minutes", 0),
            was_perfect_session=data.get("was_perfect_session", False),
            story_id_at_encounter=data.get("story_id_at_encounter"),
        )
