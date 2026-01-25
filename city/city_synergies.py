"""
City Building System - Entity Synergies
========================================
Entity-building bonus calculations.

Philosophy: Collected entities with thematic connections boost specific buildings.
This creates a satisfying loop: collect entities → boost buildings → get better rewards.
"""

import logging
from typing import Dict, Set, List, Optional
from dataclasses import dataclass

from .city_state import CellStatus

_logger = logging.getLogger(__name__)


@dataclass
class SynergyMapping:
    """Maps entity tags to building bonuses."""
    building_id: str
    entity_tags: Set[str]     # Tags that trigger synergy
    bonus_type: str           # Which building effect to boost
    normal_bonus: float       # % bonus per normal entity (0.05 = 5%)
    exceptional_bonus: float  # % bonus per exceptional entity
    max_bonus: float          # Cap on total synergy bonus (0.50 = 50%)


# ============================================================================
# SYNERGY DEFINITIONS
# ============================================================================

BUILDING_SYNERGIES: Dict[str, SynergyMapping] = {
    "goldmine": SynergyMapping(
        building_id="goldmine",
        entity_tags={"mining", "earth", "treasure", "dwarf", "dragon", "underground", "gold"},
        bonus_type="coins_per_hour",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "forge": SynergyMapping(
        building_id="forge",
        entity_tags={"fire", "crafting", "smithing", "phoenix", "salamander", "heat", "metal"},
        bonus_type="merge_success_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "artisan_guild": SynergyMapping(
        building_id="artisan_guild",
        entity_tags={"art", "beauty", "creativity", "muse", "fairy", "inspiration", "craft"},
        bonus_type="rarity_bias_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "university": SynergyMapping(
        building_id="university",
        entity_tags={"knowledge", "books", "wisdom", "owl", "scholar", "learning", "academic", "study"},
        bonus_type="entity_catch_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "training_ground": SynergyMapping(
        building_id="training_ground",
        entity_tags={"strength", "combat", "athletics", "warrior", "physical", "muscle", "training"},
        bonus_type="power_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "library": SynergyMapping(
        building_id="library",
        entity_tags={"reading", "lore", "history", "scribe", "tome", "ancient", "books", "knowledge"},
        bonus_type="xp_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "market": SynergyMapping(
        building_id="market",
        entity_tags={"trade", "commerce", "luck", "merchant", "fortune", "bargain", "gold"},
        bonus_type="coin_discount",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "royal_mint": SynergyMapping(
        building_id="royal_mint",
        entity_tags={"wealth", "gold", "prosperity", "treasure", "coins", "rich", "dragon"},
        bonus_type="coins_per_hour",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "observatory": SynergyMapping(
        building_id="observatory",
        entity_tags={"stars", "night", "vision", "owl", "moon", "astronomy", "sky", "eyes", "celestial"},
        bonus_type="entity_encounter_bonus",
        normal_bonus=0.05,
        exceptional_bonus=0.10,
        max_bonus=0.50,
    ),
    "wonder": SynergyMapping(
        building_id="wonder",
        entity_tags={"legendary"},  # Only legendary entities boost Wonder
        bonus_type="all",           # Boosts ALL effects
        normal_bonus=0.03,
        exceptional_bonus=0.05,
        max_bonus=0.30,
    ),
}


# ============================================================================
# SYNERGY CALCULATION
# ============================================================================

def get_entity_synergy_tags(entity_id: str) -> Set[str]:
    """
    Get synergy tags for an entity.
    
    Attempts to get tags from entity metadata.
    Falls back to deriving from entity name/description.
    
    Future: Add 'synergy_tags' field to entity definitions.
    """
    try:
        from entitidex.entity_pools import get_entity_by_id
        entity = get_entity_by_id(entity_id)
        if entity:
            # Check for explicit synergy_tags
            if hasattr(entity, 'synergy_tags') and entity.synergy_tags:
                return set(entity.synergy_tags)
            
            # Derive from entity properties
            tags = set()
            
            # Check rarity for legendary
            rarity = getattr(entity, 'rarity', '').lower()
            if rarity in ('legendary', 'mythic'):
                tags.add('legendary')
            
            # Derive from entity name (simple keyword matching)
            name = getattr(entity, 'name', '').lower()
            description = getattr(entity, 'description', '').lower()
            full_text = f"{name} {description}"
            
            # Keyword matching for common themes
            keyword_to_tags = {
                'owl': {'owl', 'wisdom', 'night', 'vision'},
                'phoenix': {'phoenix', 'fire', 'legendary'},
                'dragon': {'dragon', 'treasure', 'fire', 'legendary'},
                'scholar': {'scholar', 'knowledge', 'academic'},
                'book': {'books', 'knowledge', 'reading'},
                'star': {'stars', 'celestial', 'astronomy'},
                'moon': {'moon', 'night', 'celestial'},
                'gold': {'gold', 'treasure', 'wealth'},
                'warrior': {'warrior', 'combat', 'strength'},
                'smith': {'smithing', 'crafting', 'fire'},
                'merchant': {'merchant', 'trade', 'commerce'},
                'muse': {'muse', 'art', 'inspiration'},
                'fairy': {'fairy', 'magic', 'beauty'},
                'dwarf': {'dwarf', 'mining', 'underground'},
                'mole': {'underground', 'earth', 'mining'},
                'eye': {'eyes', 'vision'},
                'fire': {'fire', 'heat'},
                'earth': {'earth', 'underground'},
                'water': {'water'},
                'ancient': {'ancient', 'lore', 'history'},
                'wise': {'wisdom', 'knowledge'},
            }
            
            for keyword, keyword_tags in keyword_to_tags.items():
                if keyword in full_text:
                    tags.update(keyword_tags)
            
            return tags
            
    except ImportError:
        _logger.debug("Entity pools module not available")
    except Exception as e:
        _logger.debug(f"Error getting entity tags: {e}")
    
    return set()


def calculate_building_synergy_bonus(
    building_id: str,
    adhd_buster: dict
) -> Dict:
    """
    Calculate synergy bonus for a building from collected entities.
    
    Returns:
        {
            "bonus_type": str or None,
            "bonus_percent": float (0.0 to max_bonus),
            "contributors": [{entity_id, is_exceptional, bonus}],
            "capped": bool (True if at max),
        }
    """
    synergy = BUILDING_SYNERGIES.get(building_id)
    if not synergy:
        return {
            "bonus_type": None,
            "bonus_percent": 0.0,
            "contributors": [],
            "capped": False,
        }
    
    entitidex_data = adhd_buster.get("entitidex", {})
    
    # Get collected entities - handle both old and new data formats
    collected = entitidex_data.get("collected_entity_ids", 
                entitidex_data.get("collected", set()))
    
    # Convert to set if it's a list
    if isinstance(collected, list):
        collected = set(collected)
    
    # Get exceptional entities
    exceptional = entitidex_data.get("exceptional_entities", {})
    if isinstance(exceptional, list):
        exceptional = set(exceptional)
    elif isinstance(exceptional, dict):
        exceptional = set(exceptional.keys())
    
    total_bonus = 0.0
    contributors = []
    
    for entity_id in collected:
        entity_tags = get_entity_synergy_tags(entity_id)
        
        # Check for tag overlap
        if entity_tags & synergy.entity_tags:
            is_exceptional = entity_id in exceptional
            bonus = synergy.exceptional_bonus if is_exceptional else synergy.normal_bonus
            total_bonus += bonus
            
            contributors.append({
                "entity_id": entity_id,
                "is_exceptional": is_exceptional,
                "bonus": bonus,
            })
    
    # Apply cap
    capped = total_bonus > synergy.max_bonus
    capped_bonus = min(total_bonus, synergy.max_bonus)
    
    return {
        "bonus_type": synergy.bonus_type,
        "bonus_percent": capped_bonus,
        "contributors": contributors,
        "capped": capped,
    }


def get_all_synergy_bonuses(adhd_buster: dict) -> Dict[str, float]:
    """
    Get all synergy bonuses from entities for all completed buildings.
    
    Only completed buildings receive synergy bonuses.
    
    Returns dict matching get_city_bonuses() structure, to be multiplied on top.
    """
    synergy_bonuses = {
        "coins_per_hour": 0.0,
        "merge_success_bonus": 0.0,
        "rarity_bias_bonus": 0.0,
        "entity_catch_bonus": 0.0,
        "entity_encounter_bonus": 0.0,
        "power_bonus": 0.0,
        "xp_bonus": 0.0,
        "coin_discount": 0.0,
    }
    
    city_data = adhd_buster.get("city", {})
    grid = city_data.get("grid", [])
    
    if not grid:
        return synergy_bonuses
    
    # Only completed buildings get synergy bonuses
    for row in grid:
        for cell in row:
            if cell is None:
                continue
            if cell.get("status") != CellStatus.COMPLETE.value:
                continue
            
            building_id = cell.get("building_id")
            synergy = calculate_building_synergy_bonus(building_id, adhd_buster)
            
            if synergy["bonus_percent"] <= 0:
                continue
            
            if synergy["bonus_type"] == "all":
                # Wonder: boost all bonuses
                for key in synergy_bonuses:
                    synergy_bonuses[key] += synergy["bonus_percent"]
            elif synergy["bonus_type"] in synergy_bonuses:
                synergy_bonuses[synergy["bonus_type"]] += synergy["bonus_percent"]
    
    return synergy_bonuses


def get_synergy_display_info(building_id: str, adhd_buster: dict) -> dict:
    """
    Get formatted synergy info for UI display.
    
    Returns:
        {
            "total_bonus_percent": int (e.g., 15 for 15%),
            "contributors": [{"name": str, "bonus": str, "is_exceptional": bool}],
            "is_capped": bool,
            "cap_value": int,
        }
    """
    synergy_result = calculate_building_synergy_bonus(building_id, adhd_buster)
    
    # Get entity names for display
    contributors_display = []
    for contrib in synergy_result["contributors"]:
        entity_name = contrib["entity_id"]  # Default to ID
        
        try:
            from entitidex.entity_pools import get_entity_by_id
            entity = get_entity_by_id(contrib["entity_id"])
            if entity and hasattr(entity, 'name'):
                entity_name = entity.name
        except Exception:
            pass
        
        bonus_str = f"+{int(contrib['bonus'] * 100)}%"
        if contrib["is_exceptional"]:
            bonus_str += " (Exceptional)"
        
        contributors_display.append({
            "name": entity_name,
            "bonus": bonus_str,
            "is_exceptional": contrib["is_exceptional"],
        })
    
    synergy_def = BUILDING_SYNERGIES.get(building_id)
    cap_value = int(synergy_def.max_bonus * 100) if synergy_def else 50
    
    return {
        "total_bonus_percent": int(synergy_result["bonus_percent"] * 100),
        "contributors": contributors_display,
        "is_capped": synergy_result["capped"],
        "cap_value": cap_value,
    }
