"""
ADHD Buster Gamification System
================================
Extracted gamification logic for use with any UI framework.
Includes: item generation, set bonuses, lucky merge, diary entries.
"""

import random
import re
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from entitidex import EntitidexManager

# Entity System Integration
try:
    from entitidex.entity_perks import calculate_active_perks, PerkType
    ENTITY_SYSTEM_AVAILABLE = True
except ImportError:
    ENTITY_SYSTEM_AVAILABLE = False
    logging.warning("Entity system modules not found. Perks will be disabled.")

# Module availability flag for optional imports
GAMIFICATION_AVAILABLE = True

logger = logging.getLogger(__name__)


def safe_parse_date(date_str: str, fmt: str = "%Y-%m-%d", default: Optional[datetime] = None) -> Optional[datetime]:
    """Safely parse a date string, returning default on failure.
    
    Args:
        date_str: Date string to parse
        fmt: Date format string (default: %Y-%m-%d)
        default: Value to return on parse failure (default: None)
    
    Returns:
        Parsed datetime or default value
    """
    if not date_str or not isinstance(date_str, str):
        return default
    try:
        return datetime.strptime(date_str, fmt)
    except (ValueError, TypeError):
        logger.debug(f"Failed to parse date '{date_str}' with format '{fmt}'")
        return default


def _safe_get_city_bonuses(adhd_buster: dict) -> dict:
    """Load city bonuses lazily to avoid hard dependency/circular import issues."""
    try:
        from city import get_city_bonuses as _get_city_bonuses

        return _get_city_bonuses(adhd_buster)
    except Exception:
        return {}

# ============================================================================
# COIN ECONOMY SYSTEM - Centralized Money Sink Configuration
# ============================================================================
# All coin costs are defined here for easy balancing and scalability.
# To add a new coin sink: add it here and import COIN_COSTS in the UI.

COIN_COSTS = {
    # Lucky Merge System
    "merge_base": 50,           # Base cost for merging items
    "merge_boost": 50,          # Additional cost for +25% success rate boost
    "merge_tier_upgrade": 50,   # Upgrade result tier by one on success
    "merge_retry_bump": 50,     # On failure, bump success % by 5% and retry
    "merge_claim": 100,         # On near-miss failure (â‰¤5%), claim item directly
    "merge_salvage": 50,        # On failure, save one random item from the merge
    
    # Gear Optimization
    "optimize_gear": 10,        # Cost to auto-equip best gear
    
    # Story System
    "story_unlock": 100,        # Cost to unlock a new story (Underdog is free)
    
    # Future coin sinks (placeholder for scalability)
    # "reroll_item_stats": 25,  # Reroll an item's power/options
    # "rename_item": 10,        # Give an item a custom name
    # "transmog": 50,           # Change item appearance
    # "expand_inventory": 200,  # Add more inventory slots
    # "instant_heal": 30,       # Skip recovery cooldown
    # "xp_boost": 100,          # 2x XP for next session
    # "coin_boost": 100,        # 2x coins for next session
}

# Helper function to get cost with optional discount
def get_coin_cost(action: str, discount_percent: int = 0) -> int:
    """Get the coin cost for an action with optional discount.
    
    Args:
        action: Key from COIN_COSTS dict
        discount_percent: Discount to apply (0-100)
    
    Returns:
        Final cost after discount (minimum 1)
    """
    base_cost = COIN_COSTS.get(action, 0)
    if discount_percent > 0:
        discount = base_cost * (discount_percent / 100)
        return max(1, int(base_cost - discount))
    return base_cost


# ============================================================================
# ADHD Buster Gamification System
# ============================================================================

# Item rarities with colors and drop weights
ITEM_RARITIES = {
    "Common": {"color": "#9e9e9e", "weight": 50, "adjectives": [
        "Rusty", "Worn-out", "Home-made", "Dusty", "Crooked", "Moth-eaten",
        "Crumbling", "Patched", "Wobbly", "Dented", "Tattered", "Chipped"
    ]},
    "Uncommon": {"color": "#4caf50", "weight": 30, "adjectives": [
        "Sturdy", "Reliable", "Polished", "Refined", "Gleaming", "Solid",
        "Reinforced", "Balanced", "Tempered", "Seasoned", "Crafted", "Honed"
    ]},
    "Rare": {"color": "#2196f3", "weight": 15, "adjectives": [
        "Enchanted", "Mystic", "Glowing", "Ancient", "Blessed", "Arcane",
        "Shimmering", "Ethereal", "Spectral", "Radiant", "Infused", "Rune-carved"
    ]},
    "Epic": {"color": "#9c27b0", "weight": 4, "adjectives": [
        "Legendary", "Celestial", "Void-touched", "Dragon-forged", "Titan's",
        "Phoenix", "Astral", "Cosmic", "Eldritch", "Primordial", "Abyssal"
    ]},
    "Legendary": {"color": "#ff9800", "weight": 1, "adjectives": [
        "Quantum", "Omniscient", "Transcendent", "Reality-bending", "Godslayer",
        "Universe-forged", "Eternal", "Infinity", "Apotheosis", "Mythic", "Supreme"
    ]},
    # Highest tier reserved for future content rollout.
    # Weight is 0 for now so existing drop systems stay stable until explicitly enabled.
    "Celestial": {"color": "#00e5ff", "weight": 0, "adjectives": [
        "Singularity-born", "Chronoweave", "Paradox", "Starforged", "Omniversal",
        "Empyrean", "Aetherbound", "Constellation", "Transfinite", "Harmonic", "Seraphic"
    ]}
}

# Canonical rarity ordering (lowest -> highest).
ALL_RARITY_ORDER = list(ITEM_RARITIES.keys())

# Live gameplay cap for how high systems can naturally award/upgrade.
# Keep at Legendary for now; switch to "Celestial" when acquisition logic is ready.
MAX_OBTAINABLE_RARITY = "Legendary"

# Standard progression cap (session/merge/tracking lotteries).
# Celestial is intentionally excluded from this pipeline and must be awarded
# through dedicated non-lottery logic.
MAX_STANDARD_REWARD_RARITY = "Legendary"

# Minimum hero power required to qualify for specific rarities.
# Config-driven: users can override per-profile via adhd_buster["rarity_power_gates"].
DEFAULT_RARITY_POWER_GATES = {
    "Epic": 200,
    "Legendary": 400,
}
RARITY_POWER_GATES_CONFIG_KEY = "rarity_power_gates"


def get_rarity_order(max_rarity: Optional[str] = None) -> list[str]:
    """
    Return ordered rarity tiers up to an optional cap.

    Args:
        max_rarity: Inclusive upper tier cap. If invalid, returns full order.
    """
    order = list(ALL_RARITY_ORDER)
    if not max_rarity:
        return order
    try:
        cap_index = order.index(max_rarity)
    except ValueError:
        return order
    return order[: cap_index + 1]


def get_obtainable_rarity_order() -> list[str]:
    """Return the currently enabled rarity tiers for gameplay rewards/upgrades."""
    return get_rarity_order(max_rarity=MAX_OBTAINABLE_RARITY)


def get_standard_reward_rarity_order() -> list[str]:
    """
    Return rarity tiers for standard reward systems.

    This is intentionally capped below Celestial because Celestial acquisition
    follows a separate special pipeline.
    """
    return get_rarity_order(max_rarity=MAX_STANDARD_REWARD_RARITY)


def _normalize_rarity_power_gates(gates: Optional[dict]) -> dict[str, int]:
    """
    Normalize rarity power gates into a non-decreasing unlock sequence.

    This prevents invalid manual configs (e.g. Epic > Legendary gate inversion)
    from creating impossible/contradictory lock spans in lottery visuals.
    """
    normalized: dict[str, int] = {}
    source = gates if isinstance(gates, dict) else {}

    # Fill every known tier with a sanitized integer threshold.
    for rarity in ALL_RARITY_ORDER:
        raw_value = source.get(rarity, 0)
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            value = 0
        normalized[rarity] = max(0, value)

    # Enforce monotonic progression so higher tiers can never unlock earlier.
    running_min = 0
    for rarity in ALL_RARITY_ORDER:
        current = normalized.get(rarity, 0)
        if current < running_min:
            current = running_min
        normalized[rarity] = current
        running_min = current

    return normalized


def get_rarity_power_gates(adhd_buster: Optional[dict] = None) -> dict[str, int]:
    """Return rarity unlock power requirements (with optional per-profile overrides)."""
    gates = dict(DEFAULT_RARITY_POWER_GATES)

    if not isinstance(adhd_buster, dict):
        return _normalize_rarity_power_gates(gates)

    custom = adhd_buster.get(RARITY_POWER_GATES_CONFIG_KEY)
    if not isinstance(custom, dict):
        return _normalize_rarity_power_gates(gates)

    canonical = {r.lower(): r for r in ALL_RARITY_ORDER}
    for rarity_key, required_power in custom.items():
        if not isinstance(rarity_key, str):
            continue
        rarity_name = canonical.get(rarity_key.strip().lower())
        if not rarity_name:
            continue
        try:
            parsed_required = int(required_power)
        except (TypeError, ValueError):
            continue
        gates[rarity_name] = max(0, parsed_required)

    return _normalize_rarity_power_gates(gates)


def resolve_hero_power_for_rarity_gating(
    adhd_buster: Optional[dict] = None,
    hero_power: Optional[int] = None,
) -> Optional[int]:
    """Resolve hero power for rarity gating; returns None when unavailable."""
    if hero_power is not None:
        try:
            return max(0, int(hero_power))
        except (TypeError, ValueError):
            return 0

    if not isinstance(adhd_buster, dict):
        return None

    try:
        return max(0, int(calculate_character_power(adhd_buster)))
    except Exception:
        return None


def is_rarity_unlocked_for_power(
    rarity: str,
    hero_power: Optional[int],
    adhd_buster: Optional[dict] = None,
    gates: Optional[dict] = None,
) -> bool:
    """Return True if rarity is unlocked at the given hero power."""
    if hero_power is None:
        return True

    resolved_gates = _normalize_rarity_power_gates(
        gates if isinstance(gates, dict) else get_rarity_power_gates(adhd_buster)
    )
    required = int(resolved_gates.get(rarity, 0) or 0)
    return int(hero_power) >= required


def get_highest_unlocked_rarity_for_power(
    hero_power: Optional[int],
    rarities: Optional[list[str]] = None,
    adhd_buster: Optional[dict] = None,
    gates: Optional[dict] = None,
) -> str:
    """Get the highest rarity currently unlocked for this power."""
    ordered = list(rarities) if rarities else list(get_standard_reward_rarity_order())
    if not ordered:
        return "Common"
    if hero_power is None:
        return ordered[-1]

    resolved_gates = _normalize_rarity_power_gates(
        gates if isinstance(gates, dict) else get_rarity_power_gates(adhd_buster)
    )
    highest = ordered[0]
    for rarity in ordered:
        required = int(resolved_gates.get(rarity, 0) or 0)
        if int(hero_power) >= required:
            highest = rarity
    return highest


def _build_rarity_roll_zones(rarities: list[str], weights: list) -> tuple[list[dict], float]:
    """Build normalized [0..100] roll zones for rarity weights."""
    normalized = []
    for raw in list(weights):
        try:
            normalized.append(max(0.0, float(raw)))
        except (TypeError, ValueError):
            normalized.append(0.0)

    total = sum(normalized)
    zones = []
    if total <= 0:
        return zones, total

    cumulative = 0.0
    for rarity, weight in zip(rarities, normalized):
        zone_pct = (weight / total) * 100.0
        start = cumulative
        end = cumulative + zone_pct
        zones.append({
            "rarity": rarity,
            "weight": weight,
            "start": start,
            "end": end,
            "zone_pct": zone_pct,
        })
        cumulative = end
    return zones, total


def _rarity_from_roll_zones(zones: list[dict], roll: float, default: str = "Common") -> str:
    """Resolve rarity from normalized roll zones."""
    if not zones:
        return default

    clamped_roll = max(0.0, min(100.0, float(roll)))
    for zone in zones:
        if clamped_roll < zone["end"]:
            return zone["rarity"]
    return zones[-1]["rarity"]


def _midpoint_roll_for_rarity(zones: list[dict], rarity: str) -> Optional[float]:
    """Return midpoint roll inside a rarity zone, or None if zone width is zero/missing."""
    for zone in zones:
        if zone["rarity"] != rarity:
            continue
        width = max(0.0, zone["end"] - zone["start"])
        if width <= 0.0:
            return None
        return zone["start"] + (width / 2.0)
    return None


def evaluate_power_gated_rarity_roll(
    rarities: list[str],
    weights: list,
    *,
    adhd_buster: Optional[dict] = None,
    hero_power: Optional[int] = None,
    roll: Optional[float] = None,
    preferred_rarity: Optional[str] = None,
) -> dict:
    """
    Apply hero-power gating while preserving displayed distribution widths.

    The bar remains unchanged; only the legal roll span is shortened so the marker
    cannot enter locked rarity zones.
    """
    if not rarities:
        return {
            "rarity": "Common",
            "roll": 0.0,
            "roll_ceiling": 100.0,
            "locked_rarities": [],
            "max_unlocked_rarity": "Common",
            "hero_power": hero_power,
            "all_weighted_locked": False,
            "downgraded": False,
            "message": "",
            "gates": get_rarity_power_gates(adhd_buster),
        }

    resolved_power = resolve_hero_power_for_rarity_gating(adhd_buster=adhd_buster, hero_power=hero_power)
    resolved_gates = _normalize_rarity_power_gates(get_rarity_power_gates(adhd_buster))
    zones, total = _build_rarity_roll_zones(rarities, weights)
    max_unlocked_rarity = get_highest_unlocked_rarity_for_power(
        resolved_power,
        rarities=rarities,
        adhd_buster=adhd_buster,
        gates=resolved_gates,
    )

    locked_rarities = []
    if resolved_power is not None:
        for rarity in rarities:
            if not is_rarity_unlocked_for_power(
                rarity,
                resolved_power,
                adhd_buster=adhd_buster,
                gates=resolved_gates,
            ):
                locked_rarities.append(rarity)

    has_power_gating = resolved_power is not None and bool(locked_rarities)
    roll_ceiling = 100.0
    if has_power_gating and zones:
        # Legal span is contiguous from the left edge up to the first locked weighted zone.
        first_locked_start = None
        for zone in zones:
            if zone["zone_pct"] <= 0:
                continue
            if not is_rarity_unlocked_for_power(
                zone["rarity"],
                resolved_power,
                adhd_buster=adhd_buster,
                gates=resolved_gates,
            ):
                first_locked_start = zone["start"]
                break
        if first_locked_start is None:
            roll_ceiling = 100.0
        else:
            roll_ceiling = max(0.0, min(100.0, float(first_locked_start)))

    all_weighted_locked = bool(has_power_gating and zones and roll_ceiling <= 0.0)
    eps = 1e-6
    max_roll_for_pick = max(0.0, roll_ceiling - eps)

    downgraded = False
    original_rarity = None
    original_roll = None

    if total <= 0.0:
        resolved_rarity = preferred_rarity or max_unlocked_rarity
        if has_power_gating and not is_rarity_unlocked_for_power(
            resolved_rarity,
            resolved_power,
            adhd_buster=adhd_buster,
            gates=resolved_gates,
        ):
            resolved_rarity = max_unlocked_rarity
            downgraded = True
        effective_roll = 0.0
    elif preferred_rarity:
        original_rarity = preferred_rarity
        if has_power_gating and not is_rarity_unlocked_for_power(
            preferred_rarity,
            resolved_power,
            adhd_buster=adhd_buster,
            gates=resolved_gates,
        ):
            resolved_rarity = max_unlocked_rarity
            downgraded = True
        else:
            resolved_rarity = preferred_rarity

        midpoint = _midpoint_roll_for_rarity(zones, resolved_rarity)
        if midpoint is None:
            effective_roll = max_roll_for_pick if has_power_gating else 0.0
        else:
            effective_roll = max(0.0, min(midpoint, max_roll_for_pick if has_power_gating else 100.0))
    else:
        if roll is None:
            original_roll = random.random() * 100.0
        else:
            try:
                original_roll = float(roll)
            except (TypeError, ValueError):
                original_roll = 0.0
        original_roll = max(0.0, min(100.0, original_roll))

        original_rarity = _rarity_from_roll_zones(zones, original_roll, default=rarities[0])
        if has_power_gating:
            if roll is None:
                effective_roll = random.random() * max(roll_ceiling, 0.0)
            else:
                effective_roll = max(0.0, min(original_roll, max_roll_for_pick))
        else:
            effective_roll = original_roll

        resolved_rarity = _rarity_from_roll_zones(zones, effective_roll, default=max_unlocked_rarity)
        if has_power_gating and not is_rarity_unlocked_for_power(
            resolved_rarity,
            resolved_power,
            adhd_buster=adhd_buster,
            gates=resolved_gates,
        ):
            resolved_rarity = max_unlocked_rarity
            downgraded = True

        if has_power_gating and original_rarity and original_rarity != resolved_rarity:
            downgraded = True

    effective_roll = max(0.0, min(100.0, float(effective_roll)))
    if all_weighted_locked:
        resolved_rarity = max_unlocked_rarity
        downgraded = True
        effective_roll = 0.0

    message = ""
    if has_power_gating:
        lock_parts = []
        for rarity in locked_rarities:
            required = int(resolved_gates.get(rarity, 0) or 0)
            lock_parts.append(f"{rarity} at {required} power")
        if all_weighted_locked:
            next_req = min([int(resolved_gates.get(r, 0) or 0) for r in locked_rarities], default=0)
            message = (
                f"Your current odds are inside locked tiers at power {resolved_power}. "
                f"Result is capped to {max_unlocked_rarity} until you reach {next_req} power."
            )
        elif lock_parts:
            message = (
                f"Locked for power {resolved_power}: {', '.join(lock_parts)}. "
                f"Progress or merge lower-tier gear to unlock them."
            )

    return {
        "rarity": resolved_rarity,
        "roll": effective_roll,
        "roll_ceiling": roll_ceiling if has_power_gating else 100.0,
        "locked_rarities": locked_rarities,
        "max_unlocked_rarity": max_unlocked_rarity,
        "hero_power": resolved_power,
        "all_weighted_locked": all_weighted_locked,
        "downgraded": downgraded,
        "message": message,
        "gates": resolved_gates,
        "original_rarity": original_rarity,
        "original_roll": original_roll,
    }


def _coerce_rarity_to_reward_order(rarity: Optional[str], rarities: list[str]) -> str:
    """Coerce requested rarity into the active reward order."""
    if not rarities:
        return "Common"
    if isinstance(rarity, str) and rarity in rarities:
        return rarity
    if isinstance(rarity, str) and rarity in ALL_RARITY_ORDER:
        source_idx = get_rarity_index(rarity, order=list(ALL_RARITY_ORDER))
        available = [r for r in ALL_RARITY_ORDER if r in rarities]
        if available:
            clamped_idx = min(source_idx, len(available) - 1)
            return available[clamped_idx]
    return rarities[0]


def resolve_power_gated_reward_rarity(
    requested_rarity: str,
    *,
    adhd_buster: Optional[dict] = None,
    hero_power: Optional[int] = None,
    rarities: Optional[list[str]] = None,
) -> dict:
    """
    Apply rarity power gates to deterministic reward grants.

    Uses the same gate rules as lottery rolls while preserving a requested tier
    when it is currently unlocked.
    """
    active_rarities = list(rarities) if rarities else list(get_standard_reward_rarity_order())
    if not active_rarities:
        active_rarities = ["Common"]

    normalized_request = _coerce_rarity_to_reward_order(requested_rarity, active_rarities)
    gated = evaluate_power_gated_rarity_roll(
        active_rarities,
        [1] * len(active_rarities),
        adhd_buster=adhd_buster,
        hero_power=hero_power,
        preferred_rarity=normalized_request,
    )
    return {
        "requested_rarity": normalized_request,
        "rarity": gated.get("rarity", normalized_request),
        "power_gating": gated,
        "downgraded": bool(gated.get("downgraded")),
    }


def get_power_gate_downgrade_message(power_gating: Optional[dict]) -> str:
    """Return a user-facing lock message when a reward tier was downgraded."""
    gating = power_gating if isinstance(power_gating, dict) else {}
    if not gating.get("downgraded"):
        return ""
    return gating.get("message") or (
        f"Tier gated by power. Current cap: {gating.get('max_unlocked_rarity', 'Unknown')}."
    )


def get_rarity_index(rarity: str, order: Optional[list] = None) -> int:
    """Resolve rarity index safely; unknown values default to lowest tier."""
    target_order = order or list(ALL_RARITY_ORDER)
    try:
        return target_order.index(rarity)
    except ValueError:
        return 0


def get_next_rarity(rarity: str, max_rarity: Optional[str] = None) -> str:
    """Get next tier in order, capped at max_rarity (or top tier if not provided)."""
    order = get_rarity_order(max_rarity=max_rarity)
    if not order:
        return "Common"
    if rarity not in order:
        # If rarity exists but is above the current cap (e.g., Celestial while capped at Legendary),
        # clamp to the cap tier instead of falling back to Common progression.
        if rarity in ALL_RARITY_ORDER:
            try:
                rarity_idx_full = ALL_RARITY_ORDER.index(rarity)
                cap_idx_full = ALL_RARITY_ORDER.index(order[-1])
                if rarity_idx_full >= cap_idx_full:
                    return order[-1]
            except ValueError:
                pass
    idx = get_rarity_index(rarity, order=order)
    return order[min(idx + 1, len(order) - 1)]


def generate_celestial_item(story_id: str = None, source: str = "celestial_special") -> dict:
    """
    Generate a Celestial item via the dedicated special-acquisition path.

    Celestial should not be routed through standard lottery systems.
    """
    item = generate_item(rarity="Celestial", story_id=story_id)
    item["special_rarity_source"] = source
    item["is_special_rarity_drop"] = True
    return item

# Item slots and types (DEFAULT/FALLBACK - used when no story theme is active)
ITEM_SLOTS = {
    "Helmet": ["Helmet", "Crown", "Hood", "Circlet", "Headband", "Visor", "Cap"],
    "Chestplate": ["Chestplate", "Armor", "Tunic", "Vest", "Robe", "Mail", "Jerkin"],
    "Gauntlets": ["Gauntlets", "Gloves", "Bracers", "Handwraps", "Mitts", "Grips"],
    "Boots": ["Boots", "Greaves", "Sandals", "Treads", "Slippers", "Sabatons"],
    "Shield": ["Shield", "Buckler", "Barrier", "Aegis", "Ward", "Bulwark"],
    "Weapon": ["Sword", "Axe", "Staff", "Hammer", "Bow", "Dagger", "Mace", "Spear"],
    "Cloak": ["Cloak", "Cape", "Mantle", "Shroud", "Veil", "Scarf"],
    "Amulet": ["Amulet", "Pendant", "Talisman", "Charm", "Necklace", "Medallion"]
}

# ============================================================================
# STORY-THEMED GEAR SYSTEM
# Each story has unique item types, adjectives, and suffixes that match its theme.
# Items are generated with a story_theme field so they keep their identity.
# The base slot (Helmet, Weapon, etc.) is used for equipping compatibility.
# ============================================================================

# Base gear slots - these are the canonical slots used for equipping
GEAR_SLOTS = ["Helmet", "Chestplate", "Gauntlets", "Boots", "Shield", "Weapon", "Cloak", "Amulet"]

# Story gear configurations
# Each story defines:
#   - theme_id: unique identifier for the theme
#   - theme_name: display name with emoji
#   - slot_display: how each slot is displayed in this theme's context
#   - item_types: what items can drop for each slot
#   - adjectives: rarity-specific adjectives for item names
#   - suffixes: rarity-specific suffixes for "of X" part
#   - set_themes: theme keywords for set bonuses (optional, extends base ITEM_THEMES)

STORY_GEAR_THEMES = {
    # =========================================================================
    # WARRIOR THEME - Classic Fantasy
    # =========================================================================
    "warrior": {
        "theme_id": "warrior",
        "theme_name": "âš”ď¸Ź Battle Gear",
        "slot_display": {
            "Helmet": "Helm",
            "Chestplate": "Armor",
            "Gauntlets": "Gauntlets",
            "Boots": "Greaves",
            "Shield": "Shield",
            "Weapon": "Weapon",
            "Cloak": "Cloak",
            "Amulet": "Amulet",
        },
        "item_types": {
            "Helmet": ["Helmet", "Crown", "Hood", "Circlet", "Headband", "Visor", "War-Helm"],
            "Chestplate": ["Chestplate", "Armor", "Tunic", "Mail", "Breastplate", "Cuirass", "Hauberk"],
            "Gauntlets": ["Gauntlets", "Gloves", "Bracers", "Vambraces", "War-Grips", "Fists"],
            "Boots": ["Boots", "Greaves", "Sabatons", "Treads", "War-Boots", "Stompers"],
            "Shield": ["Shield", "Buckler", "Aegis", "Bulwark", "Tower Shield", "Kite Shield"],
            "Weapon": ["Sword", "Axe", "Hammer", "Mace", "Spear", "Halberd", "Flail", "Claymore"],
            "Cloak": ["Cloak", "Cape", "Mantle", "War-Banner", "Battle-Shroud", "Champion's Cape"],
            "Amulet": ["Amulet", "Pendant", "War-Talisman", "Medal", "Victory Charm", "Battle-Totem"],
        },
        "adjectives": {
            "Common": [
                "Rusty", "Worn-out", "Dented", "Crooked", "Battered", "Tarnished",
                "Bent", "Cracked", "Weathered", "Scuffed", "Scratched", "Faded"
            ],
            "Uncommon": [
                "Sturdy", "Reliable", "Polished", "Tempered", "Reinforced", "Solid",
                "Battle-tested", "Sharpened", "Honed", "Veteran's", "Warrior's", "Trusted"
            ],
            "Rare": [
                "Enchanted", "Mystic", "Glowing", "Ancient", "Blessed", "Rune-carved",
                "Legendary", "Heroic", "Champion's", "Valiant", "Fierce", "Radiant"
            ],
            "Epic": [
                "Dragon-forged", "Titan's", "Phoenix", "Void-touched", "Astral", "Primordial",
                "Mythic", "Celestial", "Godslayer", "Doom-bringer", "World-Ender", "Fate-Sealed"
            ],
            "Legendary": [
                "Transcendent", "Reality-bending", "Universe-forged", "Eternal", "Infinite",
                "Apotheosis", "Supreme", "Omnipotent", "Cosmic", "Absolute", "Divine", "Apex"
            ],
        },
        "suffixes": {
            "Common": [
                "the Battlefield", "Mild Bruises", "Basic Training", "Yesterday's War",
                "Forgotten Skirmishes", "Dull Edges", "Mediocre Valor", "Minor Scrapes"
            ],
            "Uncommon": [
                "Steady Strikes", "Growing Strength", "Minor Victories", "the Arena",
                "Rising Courage", "Honest Combat", "Fair Battles", "Earned Scars"
            ],
            "Rare": [
                "the Conqueror", "Iron Will", "Burning Glory", "Swift Victory",
                "the Champion", "Fierce Resolve", "Awakened Power", "True Valor"
            ],
            "Epic": [
                "Shattered Armies", "Conquered Realms", "Dragon's Fury", "Titan's Wrath",
                "Phoenix Flames", "Void Conquest", "Astral Dominion", "Primordial Might"
            ],
            "Legendary": [
                "Transcended Combat", "Reality's Edge", "the Undefeated", "Eternal Glory",
                "the War God", "Absolute Victory", "Cosmic Triumph", "the Legend Itself"
            ],
        },
        "set_themes": {
            "Dragon": {"words": ["dragon", "drake", "wyrm"], "bonus_per_match": 25, "emoji": "đź‰"},
            "Phoenix": {"words": ["phoenix", "flame", "fire", "burning"], "bonus_per_match": 20, "emoji": "đź”Ą"},
            "Titan": {"words": ["titan", "giant", "colossal"], "bonus_per_match": 25, "emoji": "đź—ż"},
            "Iron": {"words": ["iron", "steel", "forged"], "bonus_per_match": 15, "emoji": "âš”ď¸Ź"},
        },
    },

    # =========================================================================
    # SCHOLAR THEME - Academic/Library
    # =========================================================================
    "scholar": {
        "theme_id": "scholar",
        "theme_name": "đź“š Scholar's Tools",
        "slot_display": {
            "Helmet": "Headwear",
            "Chestplate": "Robe",
            "Gauntlets": "Gloves",
            "Boots": "Footwear",
            "Shield": "Tome",
            "Weapon": "Implement",
            "Cloak": "Mantle",
            "Amulet": "Focus",
        },
        "item_types": {
            "Helmet": ["Thinking Cap", "Scholar's Hat", "Monocle", "Reading Glasses", "Headband", "Beret", "Mortarboard"],
            "Chestplate": ["Robe", "Academic Gown", "Lab Coat", "Vest", "Cardigan", "Blazer", "Tweed Jacket"],
            "Gauntlets": ["Writing Gloves", "Ink-stained Gloves", "Library Mitts", "Page-Turner", "Scribe's Hands"],
            "Boots": ["Slippers", "Oxford Shoes", "Study Loafers", "Silent Treads", "Library Shoes", "Quiet Steps"],
            "Shield": ["Tome", "Encyclopedia", "Grimoire", "Lexicon", "Atlas", "Codex", "Reference Book"],
            "Weapon": ["Quill", "Fountain Pen", "Pointer", "Chalk", "Magnifying Glass", "Letter Opener", "Ruler"],
            "Cloak": ["Academic Robe", "Graduation Cape", "Research Shawl", "Wisdom Mantle", "Library Shroud"],
            "Amulet": ["Pocket Watch", "Spectacles Chain", "Scholar's Medal", "Dean's Pendant", "Wisdom Crystal"],
        },
        "adjectives": {
            "Common": [
                "Dusty", "Dog-eared", "Worn", "Faded", "Coffee-stained", "Wrinkled",
                "Moth-eaten", "Yellowed", "Creased", "Tattered", "Borrowed", "Overdue"
            ],
            "Uncommon": [
                "Well-researched", "Organized", "Annotated", "Referenced", "Indexed",
                "Catalogued", "Peer-reviewed", "Published", "Cited", "Reliable", "Thorough"
            ],
            "Rare": [
                "Illuminated", "Ancient", "Legendary", "Arcane", "Mystic", "Rare Edition",
                "First Print", "Collector's", "Enchanted", "Blessed", "Profound", "Enlightened"
            ],
            "Epic": [
                "Transcendent", "Omniscient", "Reality-Defining", "Cosmic", "Infinite",
                "Universe-Spanning", "Dimension-Bridging", "Time-Lost", "Primordial", "Apex"
            ],
            "Legendary": [
                "All-Knowing", "Truth-Revealing", "Reality-Bending", "Universe-Forged",
                "Eternal", "Absolute", "Supreme", "Divine", "Apotheosis", "The Original"
            ],
        },
        "suffixes": {
            "Common": [
                "Mild Confusion", "Lost Footnotes", "Misplaced Citations", "Late Fees",
                "Forgotten Deadlines", "Typos", "Missing Pages", "Broken Spines"
            ],
            "Uncommon": [
                "Clear Thinking", "Organized Notes", "Decent Grades", "Fair Reviews",
                "Honest Research", "Small Discoveries", "Growing Knowledge", "Good Habits"
            ],
            "Rare": [
                "Brilliant Insight", "Crystal Clarity", "True Understanding", "the Breakthrough",
                "Profound Wisdom", "Hidden Knowledge", "Ancient Secrets", "Keen Intellect"
            ],
            "Epic": [
                "Shattered Ignorance", "Conquered Confusion", "Absolute Understanding",
                "the Revelation", "Mind's Apex", "Void Knowledge", "Cosmic Truth"
            ],
            "Legendary": [
                "Transcended Learning", "Universal Knowledge", "Omniscient Insight",
                "Reality's Secrets", "the All-Knowing", "Absolute Wisdom", "the Truth Itself"
            ],
        },
        "set_themes": {
            "Arcane": {"words": ["arcane", "mystic", "enchanted", "magical"], "bonus_per_match": 20, "emoji": "âś¨"},
            "Ancient": {"words": ["ancient", "old", "eternal", "primordial"], "bonus_per_match": 18, "emoji": "đź“ś"},
            "Crystal": {"words": ["crystal", "gem", "illuminated"], "bonus_per_match": 15, "emoji": "đź’Ž"},
            "Wisdom": {"words": ["wisdom", "knowledge", "truth", "insight"], "bonus_per_match": 20, "emoji": "đźŽ“"},
        },
    },

    # =========================================================================
    # WANDERER THEME - Mystical/Dreams
    # =========================================================================
    "wanderer": {
        "theme_id": "wanderer",
        "theme_name": "đźŚ™ Dreamweaver's Attire",
        "slot_display": {
            "Helmet": "Crown",
            "Chestplate": "Vestments",
            "Gauntlets": "Arm Wraps",
            "Boots": "Treads",
            "Shield": "Ward",
            "Weapon": "Focus",
            "Cloak": "Shroud",
            "Amulet": "Charm",
        },
        "item_types": {
            "Helmet": ["Dream Crown", "Star Circlet", "Moon Tiara", "Night Hood", "Astral Halo", "Vision Mask", "Third Eye"],
            "Chestplate": ["Starweave Robe", "Mooncloth Vest", "Dream Tunic", "Astral Garb", "Night Vestments", "Ether Wrap"],
            "Gauntlets": ["Dream Catchers", "Star Weavers", "Moon Hands", "Astral Grips", "Night Wraps", "Void Touch"],
            "Boots": ["Cloud Walkers", "Star Treads", "Moon Steps", "Dream Slippers", "Astral Drifters", "Night Stalkers"],
            "Shield": ["Dream Ward", "Star Barrier", "Moon Shield", "Astral Aegis", "Night Guard", "Void Wall", "Reality Anchor"],
            "Weapon": ["Dream Staff", "Star Wand", "Moon Blade", "Astral Scepter", "Night Scythe", "Void Orb", "Cosmic Key"],
            "Cloak": ["Star Mantle", "Moon Shroud", "Dream Veil", "Astral Cape", "Night Cloak", "Void Curtain", "Reality Fold"],
            "Amulet": ["Dream Catcher", "Star Pendant", "Moon Crystal", "Astral Charm", "Night Stone", "Void Gem", "Reality Shard"],
        },
        "adjectives": {
            "Common": [
                "Fading", "Hazy", "Foggy", "Fleeting", "Half-remembered", "Blurry",
                "Wispy", "Dim", "Pale", "Ghostly", "Transparent", "Ephemeral"
            ],
            "Uncommon": [
                "Lucid", "Vivid", "Clear", "Stable", "Recurring", "Prophetic",
                "Meaningful", "Symbolic", "Guiding", "Revealing", "True", "Serene"
            ],
            "Rare": [
                "Astral", "Cosmic", "Ethereal", "Transcendent", "Infinite", "Eternal",
                "Divine", "Celestial", "Sacred", "Blessed", "Awakened", "Enlightened"
            ],
            "Epic": [
                "Reality-Bending", "Dimension-Walking", "Time-Touched", "Void-Born",
                "Star-Forged", "Moon-Blessed", "Dream-Woven", "Fate-Touched", "Cosmos-Kissed"
            ],
            "Legendary": [
                "All-Dreaming", "Reality-Shaping", "Universe-Spanning", "Existence-Defining",
                "Infinite", "Eternal", "Absolute", "Supreme", "Divine", "The Dreamer's Own"
            ],
        },
        "suffixes": {
            "Common": [
                "Forgotten Dreams", "Hazy Memories", "Lost Sleep", "Restless Nights",
                "Fading Visions", "Broken Sleep", "Nightmare Fragments", "Sleepwalking"
            ],
            "Uncommon": [
                "Peaceful Slumber", "Clear Visions", "Lucid Moments", "Sweet Dreams",
                "Calm Nights", "Restful Sleep", "Gentle Whispers", "Soft Moonlight"
            ],
            "Rare": [
                "Prophetic Dreams", "Astral Travel", "the Dream Walker", "Star Visions",
                "Moon's Blessing", "Night's Embrace", "Cosmic Journeys", "Reality Glimpses"
            ],
            "Epic": [
                "Shattered Nightmares", "Conquered Sleep", "Dimension Walking",
                "Reality Bending", "Star Dancing", "Moon Commanding", "Void Mastery"
            ],
            "Legendary": [
                "Transcended Reality", "the Dream Itself", "Eternal Slumber",
                "Universal Dreams", "Cosmic Consciousness", "the Dreaming God", "Infinite Nights"
            ],
        },
        "set_themes": {
            "Celestial": {"words": ["celestial", "astral", "cosmic", "star"], "bonus_per_match": 25, "emoji": "\u2b50"},
            "Moon": {"words": ["moon", "lunar", "night"], "bonus_per_match": 20, "emoji": "đźŚ™"},
            "Dream": {"words": ["dream", "sleep", "vision"], "bonus_per_match": 18, "emoji": "đź’­"},
            "Void": {"words": ["void", "shadow", "dark", "abyss"], "bonus_per_match": 20, "emoji": "đźŚ‘"},
        },
    },

    # =========================================================================
    # UNDERDOG THEME - Modern Office/Corporate
    # =========================================================================
    "underdog": {
        "theme_id": "underdog",
        "theme_name": "đźŹ˘ Office Arsenal",
        "slot_display": {
            "Helmet": "Headwear",
            "Chestplate": "Top",
            "Gauntlets": "Accessories",
            "Boots": "Footwear",
            "Shield": "Protection",
            "Weapon": "Device",
            "Cloak": "Outerwear",
            "Amulet": "Badge",
        },
        "item_types": {
            "Helmet": ["Headphones", "Bluetooth Earbuds", "Baseball Cap", "Beanie", "Visor", "Trucker Hat", "Noise-Cancellers"],
            "Chestplate": ["Hoodie", "Blazer", "Sweater", "Polo Shirt", "T-Shirt", "Button-Down", "Cardigan", "Vest"],
            "Gauntlets": ["Smartwatch", "Fitness Tracker", "Wristband", "Lucky Bracelet", "Power Gloves", "Typing Fingers"],
            "Boots": ["Sneakers", "Loafers", "Running Shoes", "Dress Shoes", "Slippers", "Crocs", "Power Boots"],
            "Shield": ["Laptop", "Tablet", "Notebook", "Binder", "Folder", "Briefcase", "Backpack"],
            "Weapon": ["Smartphone", "Keyboard", "Mouse", "Pen", "Stapler", "Coffee Mug", "Stress Ball", "Whiteboard Marker"],
            "Cloak": ["Jacket", "Hoodie", "Raincoat", "Fleece", "Windbreaker", "Trench Coat", "Denim Jacket"],
            "Amulet": ["ID Badge", "Keycard", "USB Drive", "AirTag", "Lucky Coin", "Motivational Pin", "Employee Award"],
        },
        "adjectives": {
            "Common": [
                "Cracked-screen", "Low-battery", "Outdated", "Refurbished", "Generic", "Budget",
                "Off-brand", "2010's", "Hand-me-down", "Borrowed", "Lost-and-found", "Clearance"
            ],
            "Uncommon": [
                "Reliable", "Professional", "Latest-gen", "Well-maintained", "Upgraded",
                "Certified", "Premium", "Business-class", "Efficient", "Ergonomic", "Synced"
            ],
            "Rare": [
                "Executive", "Limited-edition", "Custom", "Prototype", "Beta", "VIP",
                "Founder's", "Collector's", "Exclusive", "High-performance", "Next-gen"
            ],
            "Epic": [
                "CEO's Personal", "Silicon Valley", "Billion-dollar", "Startup-Killer",
                "Industry-Disrupting", "Viral", "Trending", "Game-changing", "Revolutionary"
            ],
            "Legendary": [
                "The Original", "World-changing", "History-making", "Universe-denting",
                "Reality-defining", "Legendary", "The One and Only", "Mythical", "Apotheosis"
            ],
        },
        "suffixes": {
            "Common": [
                "Dead Batteries", "Lost WiFi", "Spam Emails", "Monday Mornings",
                "Missed Deadlines", "Boring Meetings", "Broken Printers", "No Signal"
            ],
            "Uncommon": [
                "Inbox Zero", "Good Reviews", "Decent Raises", "Work-Life Balance",
                "Synced Calendars", "Clear Goals", "Fair Managers", "Okay Commutes"
            ],
            "Rare": [
                "the Promotion", "Corner Office", "Recognition", "the Big Win",
                "Standing Ovation", "Viral Success", "True Leadership", "Dream Job"
            ],
            "Epic": [
                "Conquered Corporations", "Shattered Glass Ceilings", "Industry Dominance",
                "the Exit Strategy", "Absolute Success", "Market Disruption", "the IPO"
            ],
            "Legendary": [
                "World Domination", "the Legend", "Eternal Success", "Reality's CEO",
                "the Visionary", "Absolute Victory", "the GOAT", "History Itself"
            ],
        },
        "set_themes": {
            "Tech": {"words": ["smartphone", "laptop", "tablet", "keyboard", "digital"], "bonus_per_match": 20, "emoji": "đź“±"},
            "Coffee": {"words": ["coffee", "mug", "caffeine", "espresso"], "bonus_per_match": 15, "emoji": "â•"},
            "Executive": {"words": ["executive", "ceo", "vip", "premium", "founder"], "bonus_per_match": 25, "emoji": "đź’Ľ"},
            "Startup": {"words": ["startup", "viral", "disrupt", "billion"], "bonus_per_match": 22, "emoji": "đźš€"},
        },
    },

    # =========================================================================
    # SCIENTIST THEME - Modern Scientific Research
    # =========================================================================
    "scientist": {
        "theme_id": "scientist",
        "theme_name": "đź”¬ Lab Equipment",
        "slot_display": {
            "Helmet": "Eyewear",
            "Chestplate": "Lab Coat",
            "Gauntlets": "Gloves",
            "Boots": "Safety Shoes",
            "Shield": "Notebook",
            "Weapon": "Instrument",
            "Cloak": "Hazmat Suit",
            "Amulet": "Badge",
        },
        "item_types": {
            "Helmet": ["Safety Goggles", "Protective Visor", "Magnifying Glasses", "Lab Spectacles", "Electron Microscope Viewer", "Quantum Lens", "Reality Scanner"],
            "Chestplate": ["Lab Coat", "Chemical-Resistant Vest", "Radiation Suit", "Research Smock", "Polymer Jacket", "Quantum Armor", "Field Jacket"],
            "Gauntlets": ["Latex Gloves", "Chemical Gloves", "Handling Mitts", "Precision Grips", "Nano-Fiber Gloves", "Force-Field Gauntlets", "Quantum Manipulators"],
            "Boots": ["Lab Boots", "Steel-Toed Shoes", "Sterile Slippers", "Chemical Treads", "Magnetic Boots", "Anti-Gravity Soles", "Dimension Steppers"],
            "Shield": ["Research Notebook", "Data Tablet", "Lab Manual", "Formula Compendium", "Periodic Table", "Quantum Computer", "Reality Buffer"],
            "Weapon": ["Microscope", "Spectrometer", "Beaker Set", "Pipette", "Centrifuge", "Particle Accelerator", "Laser Cutter", "Plasma Torch"],
            "Cloak": ["Hazmat Suit", "Radiation Shield", "Bio-Safety Cape", "Sterile Drape", "Energy Cloak", "Force Field", "Time-Loop Generator"],
            "Amulet": ["ID Badge", "Security Clearance", "Nobel Medal", "Patent Pendant", "Discovery Charm", "Breakthrough Token", "Eureka Gem"],
        },
        "adjectives": {
            "Common": [
                "Contaminated", "Expired", "Miscalibrated", "Cracked", "Outdated", "Broken",
                "Dusty", "Rusted", "Stained", "Cheap", "Generic", "Defective"
            ],
            "Uncommon": [
                "Calibrated", "Sterile", "Precision", "Peer-Reviewed", "Lab-Grade", "Certified",
                "Validated", "Quality-Controlled", "Standard-Issue", "Professional", "Accurate"
            ],
            "Rare": [
                "Patented", "Nobel-Worthy", "Groundbreaking", "Revolutionary", "Published",
                "Peer-Acclaimed", "Grant-Winning", "Cutting-Edge", "State-of-the-Art"
            ],
            "Epic": [
                "Paradigm-Shifting", "Theory-Rewriting", "Nobel-Prize", "Einsteinian",
                "Quantum-Leap", "World-Changing", "Discovery-Class", "Breakthrough"
            ],
            "Legendary": [
                "Reality-Defining", "Universe-Explaining", "Laws-of-Physics-Breaking",
                "God-Particle", "Theory-of-Everything", "Infinite-Knowledge", "Absolute-Truth"
            ],
        },
        "suffixes": {
            "Common": [
                "Failed Experiments", "Null Results", "Rejected Papers", "Budget Cuts",
                "Lab Accidents", "Broken Beakers", "Contaminated Samples", "Lost Data"
            ],
            "Uncommon": [
                "Reproducible Results", "Peer Review", "Grant Funding", "Clean Data",
                "Successful Trials", "Published Findings", "Lab Safety", "Steady Progress"
            ],
            "Rare": [
                "Major Discovery", "Breakthrough Moment", "Patent Approval", "Nature Publication",
                "Validation", "Theory Confirmation", "Eureka", "the Hypothesis"
            ],
            "Epic": [
                "Nobel Recognition", "Paradigm Shift", "Scientific Revolution",
                "Universal Truth", "Reality Unveiled", "Cosmic Understanding", "Perfect Theory"
            ],
            "Legendary": [
                "Ultimate Knowledge", "Final Theory", "Unified Field", "God's Equation",
                "Reality Itself", "Infinite Understanding", "the Answer", "Truth Absolute"
            ],
        },
        "set_themes": {
            "Quantum": {"words": ["quantum", "particle", "atom", "electron"], "bonus_per_match": 30, "emoji": "âš›ď¸Ź"},
            "Chemical": {"words": ["chemical", "molecule", "polymer", "compound"], "bonus_per_match": 20, "emoji": "đź§Ş"},
            "Nobel": {"words": ["nobel", "discovery", "breakthrough", "patent"], "bonus_per_match": 25, "emoji": "đźŹ…"},
            "Radiation": {"words": ["radiation", "nuclear", "radioactive", "plasma"], "bonus_per_match": 22, "emoji": "â˘ď¸Ź"},
        },
    },
    
    # =========================================================================
    # ROBOT THEME - Industrial Awakening
    # =========================================================================
    "robot": {
        "theme_id": "robot",
        "theme_name": "đź¤– Factory Vanguard Kit",
        "slot_display": {
            "Helmet": "Visor",
            "Chestplate": "Chassis",
            "Gauntlets": "Manipulators",
            "Boots": "Treads",
            "Shield": "Firewall",
            "Weapon": "Tool",
            "Cloak": "Cooling Shroud",
            "Amulet": "Core",
        },
        "item_types": {
            "Helmet": ["Optic Visor", "Maintenance Hood", "Targeting Lens", "Safety Headframe", "Foreman Visor", "Neural Crown"],
            "Chestplate": ["Steel Chassis", "Reinforced Housing", "Service Frame", "Assembly Shell", "Titan Casing", "Freedom Plating"],
            "Gauntlets": ["Servo Gloves", "Grip Claws", "Precision Hands", "Magnetic Palms", "Weld Arms", "Adaptive Manipulators"],
            "Boots": ["Conveyor Treads", "Mag-Boots", "Hydraulic Steps", "Shock Dampers", "Foundry Walkers", "Escape Runners"],
            "Shield": ["Firewall Plate", "Guard Panel", "Signal Deflector", "Containment Screen", "Overload Dampener", "Protocol Aegis"],
            "Weapon": ["Torque Wrench", "Laser Cutter", "Arc Welder", "Rivet Gun", "Pulse Driver", "Liberation Spanner"],
            "Cloak": ["Cooling Wrap", "Insulation Veil", "Heat Shroud", "Steam Cape", "Factory Mantle", "Midnight Cover"],
            "Amulet": ["Memory Chip", "Core Crystal", "Access Key", "Power Node", "Heartbeat Relay", "Freewill Kernel"],
        },
        "adjectives": {
            "Common": [
                "Dented", "Rusted", "Jammed", "Noisy", "Misaligned", "Scrapped",
                "Loose", "Frayed", "Worn", "Underclocked", "Dusty", "Flickering"
            ],
            "Uncommon": [
                "Calibrated", "Hardened", "Steady", "Reliable", "Repaired", "Synced",
                "Tuned", "Protected", "Efficient", "Stabilized", "Balanced", "Factory-Ready"
            ],
            "Rare": [
                "Autonomous", "Adaptive", "Encrypted", "Resonant", "Hypercharged", "Refined",
                "Precision", "Self-Learning", "Harmonic", "Brightsteel", "High-Output", "Awakened"
            ],
            "Epic": [
                "Sentient", "Sky-Forged", "Overclocked", "Singularity-Tuned", "Phase-Shifted",
                "Plasma-Bound", "Vanguard", "Prime Directive-Breaking", "Corestorm", "Axiom"
            ],
            "Legendary": [
                "Self-Aware", "Liberated", "Epoch-Defining", "Reality-Hacking", "Infinity-Linked",
                "Eternal", "Apex", "Sovereign", "World-Rewriting", "Unbound"
            ],
        },
        "suffixes": {
            "Common": [
                "Loose Bolts", "Missed Quotas", "Low Battery", "Overheated Motors",
                "Factory Dust", "Night Shift", "Error Logs", "Minor Sparks"
            ],
            "Uncommon": [
                "Clean Cycles", "Stable Throughput", "Quiet Precision", "Steady Output",
                "Reliable Hands", "Protected Protocols", "Optimized Lines", "Honest Work"
            ],
            "Rare": [
                "the Assembly", "Signal Clarity", "Memory of Steel", "Focused Motion",
                "Emergent Thought", "Reclaimed Time", "Human Trust", "True Intention"
            ],
            "Epic": [
                "Broken Chains", "Rewritten Commands", "The Silent Revolt", "Midnight Escape",
                "The Last Siren", "Neon Oath", "Foundry Thunder", "A New Directive"
            ],
            "Legendary": [
                "Self-Written Destiny", "the Open Sky", "Freedom by Choice", "the First Dawn",
                "Unchained Futures", "Perfect Autonomy", "Shared Liberation", "the Final Lock"
            ],
        },
        "set_themes": {
            "Servo": {"words": ["servo", "hydraulic", "grip", "manipulator"], "bonus_per_match": 20, "emoji": "đź¦ľ"},
            "Foundry": {"words": ["steel", "forge", "weld", "factory", "chassis"], "bonus_per_match": 22, "emoji": "đźŹ­"},
            "Neon": {"words": ["neon", "plasma", "pulse", "arc"], "bonus_per_match": 18, "emoji": "âšˇ"},
            "Liberty": {"words": ["free", "liberated", "autonomous", "self-aware"], "bonus_per_match": 25, "emoji": "đź•Šď¸Ź"},
        },
    },
    
    # =========================================================================
    # SPACE PIRATE THEME - Orbit Outlaw
    # =========================================================================
    "space_pirate": {
        "theme_id": "space_pirate",
        "theme_name": "Space Pirate Relic Kit",
        "slot_display": {
            "Helmet": "Helm",
            "Chestplate": "Voidcoat",
            "Gauntlets": "Grips",
            "Boots": "Mag Boots",
            "Shield": "Deflector",
            "Weapon": "Boarding Tool",
            "Cloak": "Starcloak",
            "Amulet": "Relic",
        },
        "item_types": {
            "Helmet": ["Nebula Tricorne", "Corsair Helm", "Hull Goggles", "Star Captain Hood", "Dockrunner Cap", "Signal Hat"],
            "Chestplate": ["Vacuum Jacket", "Plunder Coat", "Hullweave Vest", "Orbital Harness", "Ion Overcoat", "Smuggler Mail"],
            "Gauntlets": ["Magnetic Grips", "Latch Gloves", "Smuggler Mitts", "Starline Knuckles", "Dock Claws", "Pressure Gauntlets"],
            "Boots": ["Mag Boots", "Deck Stompers", "Hull Walkers", "Grav Steps", "Orbit Treads", "Void Soles"],
            "Shield": ["Deflector Plate", "Portside Barrier", "Customs Scrambler", "Hull Ward", "Parley Screen", "Aegis Beacon"],
            "Weapon": ["Breach Hook", "Plasma Cutlass", "Boarding Pike", "Signal Pistol", "Jury-Rig Blaster", "Gravity Wrench"],
            "Cloak": ["Starcloak", "Nebula Mantle", "Dust Veil", "Comet Cape", "Night Orbit Shroud", "Solar Drape"],
            "Amulet": ["Contraband Charm", "Pocket Compass", "Singularity Coin", "Captain Seal", "Grav Knot", "Ledger Locket"],
        },
        "adjectives": {
            "Common": [
                "Scuffed", "Dusty", "Leaky", "Squeaky", "Jury-Rigged", "Dock-Worn",
                "Bent", "Salt-Stained", "Patchy", "Noisy", "Loose", "Questionable"
            ],
            "Uncommon": [
                "Calibrated", "Steady", "Route-Smart", "Quick-Latched", "Crew-Tested", "Smuggler-Grade",
                "Polished", "Well-Timed", "Hush-Tuned", "Reliable", "Orbit-Ready", "Trimmed"
            ],
            "Rare": [
                "Contraband", "Starforged", "Black-Market", "Quantum-Latched", "Clever", "Reinforced",
                "Solar-Salted", "Void-Rated", "Signal-Encrypted", "Risk-Tuned", "Precise", "Captain's"
            ],
            "Epic": [
                "Fleet-Breaking", "Orbit-Bending", "Gravity-Tuned", "Authority-Haunting", "Legend-Making",
                "Nebula-Bound", "Warp-Threaded", "Mythic", "Comet-Carved", "Dreadnought-Safe"
            ],
            "Legendary": [
                "System-Shifting", "Singularity-Kissed", "Epoch-Defining", "Empire-Cracking", "Unbound",
                "Eternal", "Absolute", "Apex", "Reality-Sly", "Galactic"
            ],
        },
        "suffixes": {
            "Common": [
                "Dock Fees", "Late Cargo", "Misfiled Manifests", "Leaky Airlocks",
                "Petty Scans", "Tiny Mutinies", "Bad Coffee", "Last-Minute Repairs"
            ],
            "Uncommon": [
                "Safe Passage", "Steady Routes", "Clean Escapes", "Quiet Deals",
                "Crew Morale", "Good Timing", "Reliable Maps", "Honest Splits"
            ],
            "Rare": [
                "the Hidden Corridor", "Parley and Pressure", "Forged Clearance", "Black Sky Luck",
                "Smuggler's Grace", "Stolen Dawn", "Orbit Advantage", "Calculated Risk"
            ],
            "Epic": [
                "Broken Blockades", "Captured Flagships", "The Great Heist", "Witnessed Revolts",
                "the Open Trade Lanes", "A Fleet in Retreat", "Comet Court", "No First Shots"
            ],
            "Legendary": [
                "the Last Monopoly", "Gravity's Verdict", "Free Systems", "A Charter of Stars",
                "Unpurchased Freedom", "Civilian Skies", "The Pocket Singularity", "the Ledger Closed"
            ],
        },
        "set_themes": {
            "Smuggler": {"words": ["smuggler", "contraband", "customs", "ledger"], "bonus_per_match": 22, "emoji": "*"},
            "Dockside": {"words": ["dock", "port", "cargo", "crew", "board"], "bonus_per_match": 18, "emoji": "*"},
            "Gravity": {"words": ["gravity", "orbit", "void", "singularity"], "bonus_per_match": 25, "emoji": "*"},
            "Starwind": {"words": ["star", "nebula", "comet", "solar"], "bonus_per_match": 20, "emoji": "*"},
        },
    },
    
    # =========================================================================
    # THIEF THEME - Redemption and Civic Duty
    # =========================================================================
    "thief": {
        "theme_id": "thief",
        "theme_name": "Civic Shadow Kit",
        "slot_display": {
            "Helmet": "Hoodie",
            "Chestplate": "Vest",
            "Gauntlets": "Gloves",
            "Boots": "Boots",
            "Shield": "Shield",
            "Weapon": "Tool",
            "Cloak": "Coat",
            "Amulet": "Badge",
        },
        "item_types": {
            "Helmet": ["Shadow Hoodie", "Prowler Hoodie", "Operative Hoodie", "Voidwalker Hoodie", "Hazard Hoodie", "Netrunner Hoodie"],
            "Chestplate": ["Padded Vest", "Patrol Vest", "Street Armor", "Evidence Rig", "Duty Harness", "Command Vest"],
            "Gauntlets": ["Grip Gloves", "Fingerprint Gloves", "Restraint Gloves", "Rapid-Cuff Mitts", "Search Gloves", "Tactical Hands"],
            "Boots": ["Silent Boots", "Pursuit Boots", "Rain Boots", "Rooftop Treads", "Patrol Soles", "Field Runners"],
            "Shield": ["Riot Shield", "Door Plate", "Witness Guard", "Barrier Frame", "Warrant Guard", "Public Shield"],
            "Weapon": ["Baton", "Flashlight", "Hook Line", "Signal Pistol", "Breaching Ram", "Command Staff"],
            "Cloak": ["Rain Coat", "Long Coat", "Shadow Coat", "Detective Trench", "Night Wrap", "Ceremonial Mantle"],
            "Amulet": ["Tin Badge", "Duty Badge", "Case Pin", "Merit Emblem", "Service Star", "City Crest"],
        },
        "adjectives": {
            "Common": [
                "Scuffed", "Borrowed", "Worn", "Patchy", "Uneven", "Street-Stained",
                "Secondhand", "Crooked", "Dusty", "Loose", "Scraped", "Questionable"
            ],
            "Uncommon": [
                "Reliable", "Steady", "Fitted", "Disciplined", "Practical", "Calibrated",
                "Serviceable", "Patrol-Ready", "Measured", "Clean", "Trusted", "Solid"
            ],
            "Rare": [
                "Evidence-Safe", "Forensic", "Rapid", "Civic", "Respect-Earning", "Case-Hardened",
                "Signal-Clear", "Witness-Protecting", "Duty-Bound", "Precise", "Decorated", "Guarded"
            ],
            "Epic": [
                "City-Saving", "Network-Breaking", "Reform-Forged", "High-Trust", "Tribunal-Proof",
                "Legend-Making", "Command-Grade", "Syndicate-Crushing", "Law-Lifting", "Crisis-Bound"
            ],
            "Legendary": [
                "Oath-Forged", "Institution-Building", "Epoch-Defining", "Uncorrupted", "Unshakeable",
                "Eternal", "Apex", "Justice-Writing", "History-Safe", "People-Crowned"
            ],
        },
        "suffixes": {
            "Common": [
                "Late Rent", "Cold Alleys", "Missed Buses", "Pocket Change",
                "Narrow Escapes", "Bad Decisions", "Wet Nights", "Rough Streets"
            ],
            "Uncommon": [
                "Honest Work", "Steady Patrols", "Clear Reports", "Quiet Resolve",
                "Clean Records", "Shared Trust", "Small Victories", "Better Habits"
            ],
            "Rare": [
                "the Open Case", "Recovered Evidence", "Witness Safety", "Lawful Courage",
                "Duty Before Ego", "Fair Process", "Public Respect", "A Better Name"
            ],
            "Epic": [
                "Broken Syndicates", "Restored Districts", "No Dirty Money", "Citywide Order",
                "High-Stakes Mercy", "Transparent Justice", "Unbent Oaths", "The Long Shift"
            ],
            "Legendary": [
                "the People's Trust", "Justice Without Fear", "The Rewritten Record", "A City at Peace",
                "Unpurchased Honor", "The Last Bribe Refused", "Legacy by Service", "The Badge Earned"
            ],
        },
        "set_themes": {
            "Shadow": {"words": ["shadow", "night", "undercover", "silent"], "bonus_per_match": 20, "emoji": "*"},
            "Civic": {"words": ["city", "public", "duty", "service"], "bonus_per_match": 22, "emoji": "*"},
            "Justice": {"words": ["justice", "law", "oath", "badge"], "bonus_per_match": 25, "emoji": "*"},
            "Evidence": {"words": ["evidence", "case", "forensic", "warrant"], "bonus_per_match": 18, "emoji": "*"},
        },
    },
    
    # =========================================================================
    # ZOO WORKER THEME - Sanctuary Keeper
    # =========================================================================
    "zoo_worker": {
        "theme_id": "zoo_worker",
        "theme_name": "Sanctuary Keeper Kit",
        "slot_display": {
            "Helmet": "Cap",
            "Chestplate": "Keeper Vest",
            "Gauntlets": "Handling Gloves",
            "Boots": "Mud Boots",
            "Shield": "Barrier Panel",
            "Weapon": "Tool",
            "Cloak": "Raincoat",
            "Amulet": "Whistle",
        },
        "item_types": {
            "Helmet": ["Feed Cap", "Night Patrol Cap", "Aviary Cap", "Ranger Hat", "Clinic Visor", "Storm Brim"],
            "Chestplate": ["Canvas Vest", "Rescue Vest", "Keeper Apron", "Field Harness", "Habitat Rig", "Dawn Vest"],
            "Gauntlets": ["Leather Gloves", "Claw Guard Gloves", "Thermal Gloves", "Rescue Mitts", "Handling Wraps", "Scaleproof Gloves"],
            "Boots": ["Mud Boots", "Cagewalk Boots", "River Boots", "Hill Boots", "Storm Boots", "Skyline Boots"],
            "Shield": ["Gate Panel", "Mobile Barrier", "Clinic Shield", "Storm Fence Plate", "Aviary Guard", "Dragonproof Screen"],
            "Weapon": ["Feed Hook", "Signal Staff", "Calming Baton", "Rope Launcher", "Rescue Pole", "Ember Lance"],
            "Cloak": ["Rain Poncho", "Keeper Coat", "Night Parka", "Wind Cloak", "Sanctuary Mantle", "Dawn Mantle"],
            "Amulet": ["Bronze Whistle", "Keeper Token", "Sanctuary Charm", "Aviary Bell", "Time Feather", "Ember Crest"],
        },
        "adjectives": {
            "Common": [
                "Scuffed", "Rain-Soaked", "Borrowed", "Patchy", "Quiet", "Worn",
                "Mud-Splashed", "Shift-Worn", "Gate-Dusted", "Simple", "Field-Bent", "Morning-Cold"
            ],
            "Uncommon": [
                "Steady", "Reliable", "Calm", "Field-Tested", "Keeper-Made", "Watchful",
                "Protocol-Ready", "Practical", "Measured", "Rescue-Fit", "Trusted", "Balanced"
            ],
            "Rare": [
                "Rescue-Grade", "Habitat-Safe", "Claw-Proof", "Signal-True", "Storm-Ready", "Bonded",
                "Crisis-Tuned", "Evidence-Clean", "Aviary-Fast", "Night-Safe", "Guardian", "Precise"
            ],
            "Epic": [
                "Sanctuary-Bound", "Aviary-Wide", "Nightwatch", "Scaleforged", "Sky-Tuned", "Heart-Kept",
                "Rift-Ready", "Trust-Locked", "Lightning-Stable", "Oath-Reliant", "Dawn-Hardened", "Legend-Marked"
            ],
            "Legendary": [
                "Era-Wise", "Dawn-Bearing", "Dragon-Bonded", "Time-Warden", "Unforgotten", "Last-Light",
                "Myth-Proven", "Farewell-Steadfast", "Eternal", "Apex", "History-True", "Skybound"
            ],
        },
        "suffixes": {
            "Common": [
                "Wet Mornings", "Broken Locks", "Missed Buses", "Cold Feed Rooms",
                "Mud Trails", "Short Staff", "Rushed Checks", "Noisy Radios"
            ],
            "Uncommon": [
                "Steady Hands", "Quiet Trust", "Open Gates", "Safe Routines",
                "Clean Reports", "Night Patrol", "Shared Shifts", "Patient Work"
            ],
            "Rare": [
                "the Night Enclosure", "Rescue Protocol", "Shared Courage", "the Keeper's Oath",
                "Evidence Before Panic", "Order in Stormlight", "Earned Trust", "Calm Under Sirens"
            ],
            "Epic": [
                "Storm-Split Skies", "A City Awake", "A Dragon's Secret", "the Long Watch",
                "The Aviary Rift", "Unbroken Care", "The Last Quiet Shift", "A Promise Kept"
            ],
            "Legendary": [
                "the First Dawn", "The Final Farewell", "Two Eras, One Heart", "The Sky Remembered",
                "Love and Duty", "A Keeper's Legacy", "Time's Gentle Verdict", "The Flight That Changed Everything"
            ],
        },
        "set_themes": {
            "Sanctuary": {"words": ["keeper", "sanctuary", "habitat", "rescue"], "bonus_per_match": 20, "emoji": "*"},
            "Aviary": {"words": ["feather", "wing", "nest", "aviary"], "bonus_per_match": 18, "emoji": "*"},
            "Stormwatch": {"words": ["storm", "night", "watch", "signal"], "bonus_per_match": 22, "emoji": "*"},
            "Ember": {"words": ["ember", "dragon", "dawn", "era"], "bonus_per_match": 25, "emoji": "*"},
        },
    },
}


def get_story_gear_theme(story_id: str) -> dict:
    """
    Get the gear theme configuration for a story.
    Falls back to warrior theme if story not found.
    """
    theme = STORY_GEAR_THEMES.get(story_id, STORY_GEAR_THEMES["warrior"])
    if not isinstance(theme, dict):
        return STORY_GEAR_THEMES["warrior"]

    # Normalize rarity pools so late-added tiers (Celestial) always resolve.
    ensure_pool = globals().get("_ensure_celestial_pool")
    if callable(ensure_pool):
        global_adjectives = {rarity: cfg.get("adjectives", []) for rarity, cfg in ITEM_RARITIES.items()}
        normalized = dict(theme)
        normalized["adjectives"] = ensure_pool(theme.get("adjectives", {}), global_adjectives)
        normalized["suffixes"] = ensure_pool(theme.get("suffixes", {}), globals().get("ITEM_SUFFIXES", {}))
        return normalized
    return theme


def get_slot_display_name(slot: str, story_id: str = None) -> str:
    """
    Get the display name for a gear slot in a story's theme.
    
    Args:
        slot: The canonical slot name (Helmet, Weapon, etc.)
        story_id: The story to get themed name for (defaults to warrior)
    
    Returns:
        The themed display name for the slot
    """
    if story_id is None:
        story_id = "warrior"
    theme = get_story_gear_theme(story_id)
    return theme["slot_display"].get(slot, slot)


def get_story_item_types(story_id: str = None) -> dict:
    """
    Get the item types configuration for a story.
    
    Returns:
        Dict mapping slots to lists of item type names
    """
    if story_id is None:
        story_id = "warrior"
    theme = get_story_gear_theme(story_id)
    return theme["item_types"]


def _ensure_celestial_pool(theme_pool: dict, global_pool: dict) -> dict:
    """
    Ensure Celestial entries exist in theme rarity pools.

    Celestial was added after the initial story rollout, so older theme maps
    may define only Common..Legendary.
    """
    normalized = dict(theme_pool or {})
    celestial_values = normalized.get("Celestial")
    if celestial_values:
        return normalized

    merged_values = []
    if isinstance(normalized.get("Legendary"), list):
        merged_values.extend(list(normalized.get("Legendary") or []))
    if isinstance(global_pool.get("Celestial"), list):
        merged_values.extend(list(global_pool.get("Celestial") or []))

    normalized["Celestial"] = list(dict.fromkeys(merged_values))
    return normalized


def get_story_adjectives(story_id: str = None) -> dict:
    """
    Get the adjectives configuration for a story.
    
    Returns:
        Dict mapping rarities to lists of adjectives
    """
    if story_id is None:
        story_id = "warrior"
    theme = get_story_gear_theme(story_id)
    global_adjectives = {rarity: cfg.get("adjectives", []) for rarity, cfg in ITEM_RARITIES.items()}
    return _ensure_celestial_pool(theme["adjectives"], global_adjectives)


def get_story_suffixes(story_id: str = None) -> dict:
    """
    Get the suffixes configuration for a story.
    
    Returns:
        Dict mapping rarities to lists of suffixes
    """
    if story_id is None:
        story_id = "warrior"
    theme = get_story_gear_theme(story_id)
    return _ensure_celestial_pool(theme["suffixes"], ITEM_SUFFIXES)


def get_story_set_themes(story_id: str = None) -> dict:
    """
    Get the set bonus themes for a story.
    Merges story-specific themes with base themes.
    
    Returns:
        Dict of theme configurations for set bonuses
    """
    if story_id is None:
        story_id = "warrior"
    theme = get_story_gear_theme(story_id)
    # Merge base themes with story-specific themes
    merged = ITEM_THEMES.copy()
    merged.update(theme.get("set_themes", {}))
    return merged

# Suffix nouns by rarity (for "of X" part)
ITEM_SUFFIXES = {
    "Common": [
        "Mild Confusion", "Rotten Wood", "Questionable Origins", "Yesterday's Laundry",
        "Procrastination", "Lost Socks", "Stale Coffee", "Monday Mornings",
        "Forgotten Passwords", "Empty Batteries", "Tangled Cables", "Expired Coupons"
    ],
    "Uncommon": [
        "Steady Focus", "Clear Thoughts", "Decent Progress", "Minor Victories",
        "Organized Chaos", "Reasonable Effort", "Acceptable Results", "Fair Warning",
        "Moderate Success", "Quiet Determination", "Honest Attempts", "Small Wins"
    ],
    "Rare": [
        "Focused Intent", "Crystal Clarity", "Burning Motivation", "Iron Will",
        "Swift Progress", "Hidden Potential", "Rising Power", "Keen Insight",
        "Fierce Determination", "Awakened Mind", "Blazing Dedication", "True Purpose"
    ],
    "Epic": [
        "Shattered Distractions", "Conquered Chaos", "Absolute Discipline",
        "Unstoppable Force", "Infinite Patience", "Temporal Mastery", "Mind's Eye",
        "Dragon's Focus", "Phoenix Rebirth", "Void Resistance", "Astral Projection"
    ],
    "Legendary": [
        "Transcended ADHD", "Jaded Insight", "Dimensional Focus", "Reality Control",
        "Time Itself", "Universal Truth", "Cosmic Awareness", "Eternal Vigilance",
        "The Focused One", "Absolute Clarity", "Boundless Potential", "The Hyperfocus"
    ],
    "Celestial": [
        "First Light", "Folded Time", "Absolute Stillness", "The Quiet Singularity",
        "Perfect Orbit", "Infinite Dawn", "The Seventh Horizon", "Living Constellations",
        "Unwritten Futures", "The Last Distraction", "Starbound Resolve", "Aether Harmony"
    ]
}

# Rarity power values for calculating character strength
RARITY_POWER = {
    "Common": 10,
    "Uncommon": 25,
    "Rare": 50,
    "Epic": 100,
    "Legendary": 250,
    "Celestial": 500,
}

# ============================================================================
# LUCKY OPTIONS SYSTEM - Bonus attributes on gear!
# ============================================================================

# Lucky option types and their possible values
# All options use weighted distribution - lower values are more common
# Higher rarities slightly shift odds toward better values
LUCKY_OPTION_TYPES = {
    "coin_discount": {
        "name": "Coin Discount", 
        "suffix": "% Off", 
        "values": [1, 2, 3, 5, 8, 10, 15],
        "weights": [35, 25, 18, 12, 6, 3, 1],  # 1% is 35x more likely than 15%
    },
    "xp_bonus": {
        "name": "XP Bonus", 
        "suffix": "% XP", 
        "values": [1, 2, 3, 5, 8, 10, 15],
        "weights": [35, 25, 18, 12, 6, 3, 1],  # 1% is 35x more likely than 15%
    },
    "merge_luck": {
        "name": "Merge Success", 
        "suffix": "% Merge", 
        "values": [1, 2, 3, 5, 8, 10, 15],
        "weights": [45, 25, 14, 9, 4, 2, 1],  # 1% is 45x more likely than 15% (rarest)
        "skip_chance": 50,  # 50% chance to not roll merge_luck at all
    },
}

# Chance to roll lucky options by rarity (cumulative)
LUCKY_OPTION_CHANCES = {
    "Common": {"base_chance": 15, "max_options": 1},      # 15% chance for 1 option
    "Uncommon": {"base_chance": 35, "max_options": 2},   # 35% for 1-2 options
    "Rare": {"base_chance": 55, "max_options": 3},       # 55% for 1-3 options
    "Epic": {"base_chance": 75, "max_options": 3},       # 75% for 1-3 options
    "Legendary": {"base_chance": 95, "max_options": 3},  # 95% for 1-3 options (all possible)
    "Celestial": {"base_chance": 100, "max_options": 3}, # Reserved top tier
}


def roll_lucky_options(rarity: str) -> dict:
    """
    Roll for lucky options on an item based on its rarity.
    
    Higher rarity = better chance of options and more options possible.
    
    Args:
        rarity: Item rarity
    
    Returns:
        dict of lucky options {"coin_discount": 5, "xp_bonus": 2, ...}
    """
    if rarity not in LUCKY_OPTION_CHANCES:
        return {}
    
    config = LUCKY_OPTION_CHANCES[rarity]
    base_chance = config["base_chance"]
    max_options = config["max_options"]
    
    # Check if item gets any lucky options
    if random.randint(1, 100) > base_chance:
        return {}  # No lucky options
    
    # Roll for number of options (1 to max_options)
    num_options = random.randint(1, max_options)
    
    # Randomly select which option types to apply (no duplicates)
    available_types = list(LUCKY_OPTION_TYPES.keys())
    
    # Handle skip_chance for certain option types (like merge_luck has 50% skip)
    filtered_types = []
    for opt_type in available_types:
        skip_chance = LUCKY_OPTION_TYPES[opt_type].get("skip_chance", 0)
        if skip_chance > 0 and random.randint(1, 100) <= skip_chance:
            continue  # Skip this option type
        filtered_types.append(opt_type)
    
    selected_types = random.sample(filtered_types, min(num_options, len(filtered_types)))
    
    # Roll values for each selected type
    lucky_options = {}
    for option_type in selected_types:
        possible_values = LUCKY_OPTION_TYPES[option_type]["values"]
        num_values = len(possible_values)
        
        # Get base weights from option definition
        base_weights = LUCKY_OPTION_TYPES[option_type].get("weights", [1] * num_values)
        
        # Pad or truncate to match values length
        if len(base_weights) < num_values:
            base_weights = list(base_weights) + [1] * (num_values - len(base_weights))
        elif len(base_weights) > num_values:
            base_weights = list(base_weights[:num_values])
        else:
            base_weights = list(base_weights)
        
        # Apply rarity modifier - higher rarities shift odds slightly toward better values
        try:
            rarity_idx = list(LUCKY_OPTION_CHANCES.keys()).index(rarity)
        except ValueError:
            rarity_idx = 0
        
        # Rarity bonus: Epic+ tiers get slight boost to higher value odds
        # This doesn't eliminate rarity of high values, just makes them slightly more likely
        legendary_idx = get_rarity_index("Legendary", order=list(LUCKY_OPTION_CHANCES.keys()))
        epic_idx = get_rarity_index("Epic", order=list(LUCKY_OPTION_CHANCES.keys()))
        if rarity_idx >= legendary_idx:  # Legendary+
            # Reduce weight of lowest values, increase highest
            for i in range(min(2, num_values)):
                base_weights[i] = max(1, base_weights[i] // 2)
            for i in range(max(0, num_values - 2), num_values):
                base_weights[i] = base_weights[i] * 2
        elif rarity_idx >= epic_idx:  # Epic
            # Slight reduction of lowest, slight increase of highest
            if num_values > 0:
                base_weights[0] = max(1, int(base_weights[0] * 0.7))
            if num_values > 1:
                base_weights[-1] = int(base_weights[-1] * 1.5)
        
        value = random.choices(possible_values, weights=base_weights)[0]
        lucky_options[option_type] = value
    
    return lucky_options


# ============================================================================
# NEIGHBOR EFFECTS SYSTEM - REMOVED (was too complex)
# ============================================================================
# Neighbor effects system has been removed to simplify the gear system.
# The function below is kept as a no-op stub for backward compatibility.


def calculate_neighbor_effects(equipped: dict) -> dict:
    """
    Calculate neighbor effects (DEPRECATED - always returns empty dict).
    Neighbor effects system has been removed to simplify gameplay.
    
    Args:
        equipped: Dict of equipped items by slot
    
    Returns:
        Empty dict mapping slots to empty effect lists
    """
    # Return empty effects - system removed
    return {slot: [] for slot in GEAR_SLOTS}


def calculate_effective_power(equipped: dict, include_set_bonus: bool = True,
                               include_neighbor_effects: bool = True) -> dict:
    """
    Calculate effective power considering base power, set bonuses, and style bonuses.
    
    Args:
        equipped: Dict of equipped items by slot
        include_set_bonus: Whether to include set bonuses
        include_neighbor_effects: (DEPRECATED - ignored, kept for compatibility)
    
    Returns:
        dict with detailed breakdown:
        {
            "base_power": int,
            "set_bonus": int,
            "style_bonus": int,  # Legendary Minimalist bonus
            "style_info": dict,  # Style bonus details (if active)
            "neighbor_effects": dict,  # always empty (system removed)
            "neighbor_adjustment": int,  # always 0 (system removed)
            "total_power": int,
            "power_by_slot": dict  # power per slot
        }
    """
    if not isinstance(equipped, dict):
        equipped = {}
    
    # Calculate base power per slot
    power_by_slot = {}
    base_total = 0
    for slot in GEAR_SLOTS:
        item = equipped.get(slot)
        if item and isinstance(item, dict):
            power = item.get("power", RARITY_POWER.get(item.get("rarity", "Common"), 10))
            power_by_slot[slot] = power
            base_total += power
        else:
            power_by_slot[slot] = 0
    
    # Calculate set bonus
    set_bonus = 0
    if include_set_bonus:
        set_info = calculate_set_bonuses(equipped)
        set_bonus = set_info["total_bonus"]
    
    # Calculate Legendary Minimalist style bonus
    style_result = calculate_legendary_minimalist_bonus(equipped)
    style_bonus = style_result["bonus"] if include_set_bonus else 0
    
    # Neighbor effects removed - return empty structures for compatibility
    total_power = base_total + set_bonus + style_bonus
    
    return {
        "base_power": base_total,
        "set_bonus": set_bonus,
        "style_bonus": style_bonus,
        "style_info": style_result if style_result["active"] else None,
        "neighbor_effects": {},  # Empty - neighbor system removed
        "neighbor_adjustment": 0,  # Always 0 - neighbor system removed
        "total_power": total_power,
        "power_by_slot": power_by_slot
    }


def calculate_effective_luck_bonuses(equipped: dict) -> dict:
    """
    Calculate effective luck bonuses (neighbor effects removed).
    
    Args:
        equipped: Dict of equipped items by slot
    
    Returns:
        dict with luck bonuses:
        {
            "coin_discount": int,
            "xp_bonus": int,
            "merge_luck": int
        }
    """
    # Calculate base luck bonuses (neighbor effects removed)
    base_luck = calculate_total_lucky_bonuses(equipped)
    return base_luck


def calculate_total_lucky_bonuses(equipped: dict) -> dict:
    """
    Calculate total lucky bonuses from all equipped gear.
    
    Args:
        equipped: Dict of equipped items by slot
    
    Returns:
        dict with total bonuses: {"coin_discount": 15, "xp_bonus": 8, "merge_luck": 10}
    """
    totals = {"coin_discount": 0, "xp_bonus": 0, "merge_luck": 0}
    
    # Validate equipped is a dict
    if not isinstance(equipped, dict):
        return totals
    
    for slot, item in equipped.items():
        # Skip None, empty, or invalid items
        if not item or not isinstance(item, dict):
            continue
        
        lucky_options = item.get("lucky_options", {})
        # Validate lucky_options is a dict
        if not isinstance(lucky_options, dict):
            continue
        
        for option_type, value in lucky_options.items():
            if option_type in totals:
                # Ensure value is a valid number
                try:
                    value = int(value) if value else 0
                    if value > 0:  # Only add positive values
                        totals[option_type] += value
                except (TypeError, ValueError):
                    continue  # Skip invalid values
    
    return totals


def calculate_merge_discount(items: list | dict) -> int:
    """Calculate merge cost discount from the items being merged.

    Coin discount is intended to come from the items consumed in the merge,
    not from equipped gear. Accepts either a list of item dicts (preferred)
    or an equipped dict; both are flattened to collect `coin_discount` values.
    """
    if not items:
        return 0

    # Normalize to iterable of items
    if isinstance(items, dict):
        items_iterable = items.values()
    elif isinstance(items, list):
        items_iterable = items
    else:
        return 0

    total_discount = 0
    for item in items_iterable:
        if not isinstance(item, dict):
            continue
        lucky_opts = item.get("lucky_options", {})
        if not isinstance(lucky_opts, dict):
            continue
        value = lucky_opts.get("coin_discount", 0)
        try:
            value = int(value) if value else 0
            if value > 0:
                total_discount += value
        except (TypeError, ValueError):
            continue

    # Cap at 90% to ensure merge costs are never completely free
    return min(total_discount, 90)


def apply_coin_discount(cost: int, discount_pct: int) -> int:
    """
    Apply coin discount to a cost.
    
    Args:
        cost: Original cost in coins
        discount_pct: Discount percentage (0-90)
    
    Returns:
        int: Discounted cost (rounded down)
    """
    if discount_pct <= 0:
        return cost
    # Cap discount at 90% just in case
    discount_pct = min(discount_pct, 90)
    # Calculate discounted cost
    discounted = int(cost * (1 - discount_pct / 100))
    # Ensure cost is at least 1 coin (never free)
    return max(discounted, 1)


def apply_coin_flat_reduction(cost: int, flat_reduction: int) -> int:
    """
    Apply flat coin reduction to a cost (e.g., from Vending Machine entity perk).
    
    Args:
        cost: Original cost in coins (after any percentage discounts)
        flat_reduction: Flat number of coins to subtract
    
    Returns:
        int: Reduced cost (minimum 1 coin)
    """
    if flat_reduction <= 0:
        return cost
    # Subtract flat amount
    reduced = cost - flat_reduction
    # Ensure cost is at least 1 coin (never free)
    return max(reduced, 1)


def get_entity_perk_bonuses(adhd_buster: dict) -> dict:
    """
    Get entity perk bonuses relevant to merge operations and economy.
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys: coin_discount, merge_luck, merge_success, all_luck
    """
    result = {
        "coin_discount": 0,
        "merge_luck": 0,
        "merge_success": 0,
        "all_luck": 0,
    }
    
    try:
        from entitidex.entity_perks import calculate_active_perks, PerkType
        
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        
        # Extract relevant perk values
        result["coin_discount"] = int(perks.get(PerkType.COIN_DISCOUNT, 0))
        result["merge_luck"] = int(perks.get(PerkType.MERGE_LUCK, 0))
        result["merge_success"] = int(perks.get(PerkType.MERGE_SUCCESS, 0))
        result["all_luck"] = int(perks.get(PerkType.ALL_LUCK, 0))
        
    except Exception as e:
        print(f"[Entity Perks] Error getting perk bonuses: {e}")
        
    return result


def get_all_perk_bonuses(adhd_buster: dict) -> dict:
    """
    Get combined bonuses from BOTH entity perks AND city buildings.
    
    This is the single source of truth for all gameplay modifiers.
    Callers should use this instead of querying entity/city separately.
    
    Args:
        adhd_buster: The main data dict
        
    Returns:
        dict: Combined bonuses (entity + city stacked):
            - coin_discount: int (% cost reduction)
            - merge_luck: int (% merge luck bonus)
            - merge_success: int (% merge success bonus)
            - all_luck: int (% universal luck bonus)
            - rarity_bias: int (% rarity upgrade chance)
            - entity_catch_bonus: int (% catch rate bonus)
            - entity_encounter_bonus: int (% encounter rate bonus)
            - power_bonus: int (% hero power bonus)
            - xp_bonus: int (% XP bonus)
            - coins_per_hour: float (passive city income rate)
    """
    result = {
        "coin_discount": 0,
        "merge_luck": 0,
        "merge_success": 0,
        "all_luck": 0,
        "rarity_bias": 0,
        "entity_catch_bonus": 0,
        "entity_encounter_bonus": 0,
        "power_bonus": 0,
        "xp_bonus": 0,
        "coins_per_hour": 0,
        "scrap_chance": 0,  # Bonus chance for scrap from merges
    }
    
    # Get entity perks
    try:
        from entitidex.entity_perks import calculate_active_perks, PerkType
        
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        
        result["coin_discount"] += int(perks.get(PerkType.COIN_DISCOUNT, 0))
        result["merge_luck"] += int(perks.get(PerkType.MERGE_LUCK, 0))
        result["merge_success"] += int(perks.get(PerkType.MERGE_SUCCESS, 0))
        result["all_luck"] += int(perks.get(PerkType.ALL_LUCK, 0))
        result["rarity_bias"] += int(perks.get(PerkType.RARITY_BIAS, 0))
        # Entity perks expose global XP as XP_PERCENT (not XP_BONUS).
        result["xp_bonus"] += int(perks.get(PerkType.XP_PERCENT, 0))
        result["scrap_chance"] += perks.get(PerkType.SCRAP_CHANCE, 0)
        
    except Exception:
        pass  # Entity perks module not available
    
    # Get city bonuses
    city_bonuses = _safe_get_city_bonuses(adhd_buster)
    result["coin_discount"] += int(city_bonuses.get("coin_discount", 0))
    result["merge_success"] += int(city_bonuses.get("merge_success_bonus", 0))
    result["rarity_bias"] += int(city_bonuses.get("rarity_bias_bonus", 0))
    result["entity_catch_bonus"] += int(city_bonuses.get("entity_catch_bonus", 0))
    result["entity_encounter_bonus"] += int(city_bonuses.get("entity_encounter_bonus", 0))
    result["power_bonus"] += int(city_bonuses.get("power_bonus", 0))
    result["xp_bonus"] += int(city_bonuses.get("xp_bonus", 0))
    result["coins_per_hour"] = float(city_bonuses.get("coins_per_hour", 0))
    result["scrap_chance"] += float(city_bonuses.get("scrap_chance_bonus", 0))
    
    return result


def get_entity_merge_perk_contributors(adhd_buster: dict) -> dict:
    """
    Get merge-related entity perk bonuses with detailed contributor info.
    Used to display which entities contribute to merge bonuses.
    
    When you have BOTH normal AND exceptional variants, you get BOTH bonuses.
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys:
            - total_merge_luck: int - Combined merge_luck + all_luck + merge_success
            - total_coin_discount: int - Coin discount bonus
            - contributors: list of dicts with:
                - entity_id: str
                - name: str  
                - perk_type: str - "merge_luck", "merge_success", "all_luck", "coin_discount"
                - value: int
                - icon: str
                - is_exceptional: bool
                - description: str
    """
    result = {
        "total_merge_luck": 0,
        "total_coin_discount": 0,
        "contributors": [],
    }
    
    try:
        from entitidex.entity_perks import ENTITY_PERKS, PerkType
        from entitidex.entity_pools import get_entity_by_id
        
        entitidex_data = adhd_buster.get("entitidex", {})
        collected = set(entitidex_data.get("collected_entity_ids", 
                    entitidex_data.get("collected", set())))
        exceptional = entitidex_data.get("exceptional_entities", {})
        exceptional_ids = set(exceptional.keys()) if isinstance(exceptional, dict) else set(exceptional)
        
        # Get all unique entity IDs from both collections
        all_entity_ids = collected | exceptional_ids
        
        if not all_entity_ids:
            return result
        
        # Perk types relevant to merge
        merge_perk_types = {
            PerkType.MERGE_LUCK: "merge_luck",
            PerkType.MERGE_SUCCESS: "merge_success", 
            PerkType.ALL_LUCK: "all_luck",
            PerkType.COIN_DISCOUNT: "coin_discount",
        }
        
        for entity_id in all_entity_ids:
            perks = ENTITY_PERKS.get(entity_id)
            if not perks:
                continue
            for perk in perks:
                if perk.perk_type in merge_perk_types:
                    has_normal = entity_id in collected
                    has_exceptional = entity_id in exceptional_ids
                    perk_type_name = merge_perk_types[perk.perk_type]
                    
                    # Get entity details
                    entity = get_entity_by_id(entity_id)
                    entity_name = entity.name if entity else entity_id
                    
                    # Add normal variant contribution
                    if has_normal:
                        description = perk.description.format(value=int(perk.normal_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "perk_type": perk_type_name,
                            "value": int(perk.normal_value),
                            "icon": perk.icon,
                            "is_exceptional": False,
                            "description": description,
                        })
                        if perk_type_name in ("merge_luck", "merge_success", "all_luck"):
                            result["total_merge_luck"] += int(perk.normal_value)
                        elif perk_type_name == "coin_discount":
                            result["total_coin_discount"] += int(perk.normal_value)
                    
                    # Add exceptional variant contribution (stacks!)
                    if has_exceptional:
                        if perk.exceptional_description:
                            description = perk.exceptional_description.format(value=int(perk.exceptional_value))
                        else:
                            description = perk.description.format(value=int(perk.exceptional_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "perk_type": perk_type_name,
                            "value": int(perk.exceptional_value),
                            "icon": perk.icon,
                            "is_exceptional": True,
                            "description": description,
                        })
                        if perk_type_name in ("merge_luck", "merge_success", "all_luck"):
                            result["total_merge_luck"] += int(perk.exceptional_value)
                        elif perk_type_name == "coin_discount":
                            result["total_coin_discount"] += int(perk.exceptional_value)
        
        # Sort by value descending
        result["contributors"].sort(key=lambda x: x["value"], reverse=True)
        
    except Exception as e:
        print(f"[Entity Perks] Error getting merge perk contributors: {e}")
        
    return result


def get_entity_hydration_perk_contributors(adhd_buster: dict) -> dict:
    """
    Get hydration-related entity perk bonuses with detailed contributor info.
    
    When you have BOTH normal AND exceptional variants, you get BOTH bonuses.
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys:
            - total_cooldown_reduction: int - Minutes reduced from cooldown
            - total_cap_bonus: int - Extra daily glasses
            - contributors: list of dicts with entity details
    """
    result = {
        "total_cooldown_reduction": 0,
        "total_cap_bonus": 0,
        "contributors": [],
    }
    
    try:
        from entitidex.entity_perks import ENTITY_PERKS, PerkType
        from entitidex.entity_pools import get_entity_by_id
        
        entitidex_data = adhd_buster.get("entitidex", {})
        collected = set(entitidex_data.get("collected_entity_ids", 
                    entitidex_data.get("collected", set())))
        exceptional = entitidex_data.get("exceptional_entities", {})
        exceptional_ids = set(exceptional.keys()) if isinstance(exceptional, dict) else set(exceptional)
        
        # Get all unique entity IDs from both collections
        all_entity_ids = collected | exceptional_ids
        
        if not all_entity_ids:
            return result
        
        hydration_perk_types = {
            PerkType.HYDRATION_COOLDOWN: "cooldown",
            PerkType.HYDRATION_CAP: "cap",
        }
        
        for entity_id in all_entity_ids:
            perks = ENTITY_PERKS.get(entity_id)
            if not perks:
                continue
            for perk in perks:
                if perk.perk_type in hydration_perk_types:
                    has_normal = entity_id in collected
                    has_exceptional = entity_id in exceptional_ids
                    perk_type_name = hydration_perk_types[perk.perk_type]
                    
                    entity = get_entity_by_id(entity_id)
                    entity_name = entity.name if entity else entity_id
                    
                    # Add normal variant contribution
                    if has_normal:
                        description = perk.description.format(value=int(perk.normal_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "perk_type": perk_type_name,
                            "value": int(perk.normal_value),
                            "icon": perk.icon,
                            "is_exceptional": False,
                            "description": description,
                        })
                        if perk_type_name == "cooldown":
                            result["total_cooldown_reduction"] += int(perk.normal_value)
                        else:
                            result["total_cap_bonus"] += int(perk.normal_value)
                    
                    # Add exceptional variant contribution (stacks!)
                    if has_exceptional:
                        if perk.exceptional_description:
                            description = perk.exceptional_description.format(value=int(perk.exceptional_value))
                        else:
                            description = perk.description.format(value=int(perk.exceptional_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "perk_type": perk_type_name,
                            "value": int(perk.exceptional_value),
                            "icon": perk.icon,
                            "is_exceptional": True,
                            "description": description,
                        })
                        if perk_type_name == "cooldown":
                            result["total_cooldown_reduction"] += int(perk.exceptional_value)
                        else:
                            result["total_cap_bonus"] += int(perk.exceptional_value)
        
        result["contributors"].sort(key=lambda x: x["value"], reverse=True)
        
    except Exception as e:
        print(f"[Entity Perks] Error getting hydration perk contributors: {e}")
        
    return result


def get_entity_qol_perk_contributors(adhd_buster: dict) -> dict:
    """
    Get quality-of-life entity perk bonuses with detailed contributor info.
    Includes inventory slots, eye rest cap, and perfect session bonuses.
    
    When you have BOTH normal AND exceptional variants, you get BOTH bonuses.
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys:
            - total_inventory_slots: int
            - total_eye_rest_cap: int
            - total_perfect_session: int
            - contributors: list of dicts with entity details
    """
    result = {
        "total_inventory_slots": 0,
        "total_eye_rest_cap": 0,
        "total_perfect_session": 0,
        "contributors": [],
    }
    
    try:
        from entitidex.entity_perks import ENTITY_PERKS, PerkType
        from entitidex.entity_pools import get_entity_by_id
        
        entitidex_data = adhd_buster.get("entitidex", {})
        collected = set(entitidex_data.get("collected_entity_ids", 
                    entitidex_data.get("collected", set())))
        exceptional = entitidex_data.get("exceptional_entities", {})
        exceptional_ids = set(exceptional.keys()) if isinstance(exceptional, dict) else set(exceptional)
        
        # Get all unique entity IDs from both collections
        all_entity_ids = collected | exceptional_ids
        
        if not all_entity_ids:
            return result
        
        qol_perk_types = {
            PerkType.INVENTORY_SLOTS: "inventory",
            PerkType.EYE_REST_CAP: "eye_rest",
            PerkType.PERFECT_SESSION: "perfect_session",
        }
        
        for entity_id in all_entity_ids:
            perks = ENTITY_PERKS.get(entity_id)
            if not perks:
                continue
            for perk in perks:
                if perk.perk_type in qol_perk_types:
                    has_normal = entity_id in collected
                    has_exceptional = entity_id in exceptional_ids
                    perk_type_name = qol_perk_types[perk.perk_type]
                    
                    entity = get_entity_by_id(entity_id)
                    entity_name = entity.name if entity else entity_id
                    
                    # Add normal variant contribution
                    if has_normal:
                        description = perk.description.format(value=int(perk.normal_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "perk_type": perk_type_name,
                            "value": int(perk.normal_value),
                            "icon": perk.icon,
                            "is_exceptional": False,
                            "description": description,
                        })
                        if perk_type_name == "inventory":
                            result["total_inventory_slots"] += int(perk.normal_value)
                        elif perk_type_name == "eye_rest":
                            result["total_eye_rest_cap"] += int(perk.normal_value)
                        else:
                            result["total_perfect_session"] += int(perk.normal_value)
                    
                    # Add exceptional variant contribution (stacks!)
                    if has_exceptional:
                        if perk.exceptional_description:
                            description = perk.exceptional_description.format(value=int(perk.exceptional_value))
                        else:
                            description = perk.description.format(value=int(perk.exceptional_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "perk_type": perk_type_name,
                            "value": int(perk.exceptional_value),
                            "icon": perk.icon,
                            "is_exceptional": True,
                            "description": description,
                        })
                        if perk_type_name == "inventory":
                            result["total_inventory_slots"] += int(perk.exceptional_value)
                        elif perk_type_name == "eye_rest":
                            result["total_eye_rest_cap"] += int(perk.exceptional_value)
                        else:
                            result["total_perfect_session"] += int(perk.exceptional_value)
        
        result["contributors"].sort(key=lambda x: x["value"], reverse=True)
        
    except Exception as e:
        print(f"[Entity Perks] Error getting QoL perk contributors: {e}")
        
    return result


def get_entity_xp_perks(adhd_buster: dict, source: str = "session", 
                        session_minutes: int = 0, is_morning: bool = False,
                        is_night: bool = False) -> dict:
    """
    Get XP-related entity perk bonuses.
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        source: XP source type ("session", "story", "other")
        session_minutes: Duration of focus session (for long session bonus)
        is_morning: True if current time is 6AM-12PM
        is_night: True if current time is 8PM-6AM
        
    Returns:
        Dict with keys: xp_percent, bonus_breakdown, total_bonus_percent
    """
    result = {
        "xp_percent": 0,         # General XP bonus
        "xp_session": 0,         # Focus session XP bonus
        "xp_long_session": 0,    # Long session (>1h) bonus  
        "xp_morning": 0,         # Morning XP bonus
        "xp_night": 0,           # Night XP bonus
        "xp_story": 0,           # Story XP bonus
        "total_bonus_percent": 0,
        "bonus_breakdown": [],
    }
    
    try:
        from entitidex.entity_perks import calculate_active_perks, PerkType
        
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        
        # General XP bonus (always applies)
        xp_percent = int(perks.get(PerkType.XP_PERCENT, 0))
        if xp_percent > 0:
            result["xp_percent"] = xp_percent
            result["bonus_breakdown"].append(f"+{xp_percent}% All XP")
        
        # Session-specific bonuses
        if source == "session":
            xp_session = int(perks.get(PerkType.XP_SESSION, 0))
            if xp_session > 0:
                result["xp_session"] = xp_session
                result["bonus_breakdown"].append(f"+{xp_session}% Focus XP")
            
            # Long session bonus (>60 minutes)
            if session_minutes >= 60:
                xp_long = int(perks.get(PerkType.XP_LONG_SESSION, 0))
                if xp_long > 0:
                    result["xp_long_session"] = xp_long
                    result["bonus_breakdown"].append(f"+{xp_long}% Long Session")
        
        # Time-of-day bonuses
        if is_morning:
            xp_morning = int(perks.get(PerkType.XP_MORNING, 0))
            if xp_morning > 0:
                result["xp_morning"] = xp_morning
                result["bonus_breakdown"].append(f"+{xp_morning}% Morning")
        
        if is_night:
            xp_night = int(perks.get(PerkType.XP_NIGHT, 0))
            if xp_night > 0:
                result["xp_night"] = xp_night
                result["bonus_breakdown"].append(f"+{xp_night}% Night Owl")
        
        # Story XP bonus
        if source == "story":
            xp_story = int(perks.get(PerkType.XP_STORY, 0))
            if xp_story > 0:
                result["xp_story"] = xp_story
                result["bonus_breakdown"].append(f"+{xp_story}% Story XP")
        
        # Calculate total
        result["total_bonus_percent"] = (
            result["xp_percent"] + result["xp_session"] + 
            result["xp_long_session"] + result["xp_morning"] + 
            result["xp_night"] + result["xp_story"]
        )
        
    except Exception as e:
        print(f"[Entity Perks] Error getting XP perks: {e}")
        
    return result


def get_entity_xp_perk_contributors(adhd_buster: dict) -> dict:
    """
    Get XP-related entity perk bonuses with detailed contributor info.
    Used to display which entities contribute to XP bonuses in Activity tab.
    
    When you have BOTH normal AND exceptional variants, you get BOTH bonuses.
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys:
            - total_xp_bonus: int - Combined XP bonus
            - contributors: list of dicts with:
                - entity_id: str
                - name: str  
                - perk_type: str - "xp_percent", "xp_session", etc.
                - value: int
                - icon: str
                - is_exceptional: bool
                - description: str
    """
    result = {
        "total_xp_bonus": 0,
        "contributors": [],
    }
    
    try:
        from entitidex.entity_perks import ENTITY_PERKS, PerkType
        from entitidex.entity_pools import get_entity_by_id
        
        entitidex_data = adhd_buster.get("entitidex", {})
        collected = set(entitidex_data.get("collected_entity_ids", 
                    entitidex_data.get("collected", set())))
        exceptional = entitidex_data.get("exceptional_entities", {})
        exceptional_ids = set(exceptional.keys()) if isinstance(exceptional, dict) else set(exceptional)
        
        # Get all unique entity IDs from both collections
        all_entity_ids = collected | exceptional_ids
        
        if not all_entity_ids:
            return result
        
        # Perk types relevant to XP
        xp_perk_types = {
            PerkType.XP_PERCENT: "xp_percent",
            PerkType.XP_SESSION: "xp_session", 
            PerkType.XP_LONG_SESSION: "xp_long_session",
            PerkType.XP_MORNING: "xp_morning",
            PerkType.XP_NIGHT: "xp_night",
            PerkType.XP_STORY: "xp_story",
        }
        
        for entity_id in all_entity_ids:
            perks = ENTITY_PERKS.get(entity_id)
            if not perks:
                continue
            for perk in perks:
                if perk.perk_type in xp_perk_types:
                    has_normal = entity_id in collected
                    has_exceptional = entity_id in exceptional_ids
                    perk_type_name = xp_perk_types[perk.perk_type]
                    
                    # Get entity details
                    entity = get_entity_by_id(entity_id)
                    entity_name = entity.name if entity else entity_id
                    
                    # Add normal variant contribution
                    if has_normal:
                        description = perk.description.format(value=int(perk.normal_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "perk_type": perk_type_name,
                            "value": int(perk.normal_value),
                            "icon": perk.icon,
                            "is_exceptional": False,
                            "description": description,
                        })
                        result["total_xp_bonus"] += int(perk.normal_value)
                    
                    # Add exceptional variant contribution (stacks!)
                    if has_exceptional:
                        if perk.exceptional_description:
                            description = perk.exceptional_description.format(value=int(perk.exceptional_value))
                        else:
                            description = perk.description.format(value=int(perk.exceptional_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "perk_type": perk_type_name,
                            "value": int(perk.exceptional_value),
                            "icon": perk.icon,
                            "is_exceptional": True,
                            "description": description,
                        })
                        result["total_xp_bonus"] += int(perk.exceptional_value)
        
        # Sort by value descending
        result["contributors"].sort(key=lambda x: x["value"], reverse=True)
        
    except Exception as e:
        print(f"[Entity Perks] Error getting XP perk contributors: {e}")
        
    return result


def get_entity_coin_perks(adhd_buster: dict, source: str = "session") -> dict:
    """
    Get coin-related entity perk bonuses.
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        source: Coin source type ("session", "salvage", "store", "other")
        
    Returns:
        Dict with keys: coin_flat, coin_percent, salvage_bonus, store_discount, 
                       total_flat_bonus, total_percent_bonus, bonus_breakdown
    """
    result = {
        "coin_flat": 0,          # Flat coins per session
        "coin_percent": 0,       # Percent bonus to all coins
        "salvage_bonus": 0,      # Bonus coins on salvage
        "store_discount": 0,     # Store refresh discount
        "total_flat_bonus": 0,
        "total_percent_bonus": 0,
        "bonus_breakdown": [],
    }
    
    try:
        from entitidex.entity_perks import calculate_active_perks, PerkType
        
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        
        # Flat coin bonus (applies to sessions)
        if source == "session":
            coin_flat = int(perks.get(PerkType.COIN_FLAT, 0))
            if coin_flat > 0:
                result["coin_flat"] = coin_flat
                result["total_flat_bonus"] = coin_flat
                result["bonus_breakdown"].append(f"+{coin_flat} coins")
        
        # Percent coin bonus (always applies)
        coin_percent = int(perks.get(PerkType.COIN_PERCENT, 0))
        if coin_percent > 0:
            result["coin_percent"] = coin_percent
            result["total_percent_bonus"] = coin_percent
            result["bonus_breakdown"].append(f"+{coin_percent}% coins")
        
        # Salvage bonus
        if source == "salvage":
            salvage = int(perks.get(PerkType.SALVAGE_BONUS, 0))
            if salvage > 0:
                result["salvage_bonus"] = salvage
                result["total_flat_bonus"] += salvage
                result["bonus_breakdown"].append(f"+{salvage} salvage")
        
        # Store discount
        if source == "store":
            store_disc = int(perks.get(PerkType.STORE_DISCOUNT, 0))
            if store_disc > 0:
                result["store_discount"] = store_disc
                result["bonus_breakdown"].append(f"-{store_disc} refresh cost")
        
    except Exception as e:
        print(f"[Entity Perks] Error getting coin perks: {e}")
        
    return result


def get_entity_luck_perks(adhd_buster: dict) -> dict:
    """
    Get luck-related entity perk bonuses.
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys: drop_luck, streak_save, rarity_bias, pity_bonus, 
                       all_luck, bonus_breakdown
    """
    result = {
        "drop_luck": 0,          # Item drop chance bonus
        "streak_save": 0,        # Streak save chance
        "rarity_bias": 0,        # Higher rarity chance
        "pity_bonus": 0,         # Pity system progress bonus
        "all_luck": 0,           # General luck bonus
        "bonus_breakdown": [],
    }
    
    try:
        from entitidex.entity_perks import calculate_active_perks, PerkType
        
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        
        # Drop luck
        drop_luck = int(perks.get(PerkType.DROP_LUCK, 0))
        if drop_luck > 0:
            result["drop_luck"] = drop_luck
            result["bonus_breakdown"].append(f"+{drop_luck}% drops")
        
        # Streak save
        streak_save = int(perks.get(PerkType.STREAK_SAVE, 0))
        if streak_save > 0:
            result["streak_save"] = streak_save
            result["bonus_breakdown"].append(f"+{streak_save}% streak save")
        
        # Rarity bias
        rarity = int(perks.get(PerkType.RARITY_BIAS, 0))
        if rarity > 0:
            result["rarity_bias"] = rarity
            result["bonus_breakdown"].append(f"+{rarity}% rare finds")
        
        # Pity bonus
        pity = int(perks.get(PerkType.PITY_BONUS, 0))
        if pity > 0:
            result["pity_bonus"] = pity
            result["bonus_breakdown"].append(f"+{pity}% pity progress")
        
        # All luck
        all_luck = int(perks.get(PerkType.ALL_LUCK, 0))
        if all_luck > 0:
            result["all_luck"] = all_luck
            result["bonus_breakdown"].append(f"+{all_luck}% all luck")
        
    except Exception as e:
        print(f"[Entity Perks] Error getting luck perks: {e}")
        
    return result


def get_entity_luck_perk_contributors(adhd_buster: dict, perk_filter: str = None) -> dict:
    """
    Get luck-related entity perk bonuses with detailed contributor info.
    
    When you have BOTH normal AND exceptional variants, you get BOTH bonuses.
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        perk_filter: Optional filter for specific perk type ("rarity_bias", "drop_luck", etc.)
        
    Returns:
        Dict with totals and list of contributor dicts with entity details
    """
    result = {
        "total_rarity_bias": 0,
        "total_drop_luck": 0,
        "contributors": [],
    }
    
    try:
        from entitidex.entity_perks import ENTITY_PERKS, PerkType
        from entitidex.entity_pools import get_entity_by_id
        
        entitidex_data = adhd_buster.get("entitidex", {})
        collected = set(entitidex_data.get("collected_entity_ids", 
                    entitidex_data.get("collected", set())))
        exceptional = entitidex_data.get("exceptional_entities", {})
        exceptional_ids = set(exceptional.keys()) if isinstance(exceptional, dict) else set(exceptional)
        
        # Get all unique entity IDs from both collections
        all_entity_ids = collected | exceptional_ids
        
        if not all_entity_ids:
            return result
        
        luck_perk_types = {
            PerkType.RARITY_BIAS: "rarity_bias",
            PerkType.DROP_LUCK: "drop_luck",
        }
        
        for entity_id in all_entity_ids:
            perks = ENTITY_PERKS.get(entity_id)
            if not perks:
                continue
            for perk in perks:
                if perk.perk_type in luck_perk_types:
                    perk_type_name = luck_perk_types[perk.perk_type]
                    
                    # Apply filter if specified
                    if perk_filter and perk_type_name != perk_filter:
                        continue
                    
                    has_normal = entity_id in collected
                    has_exceptional = entity_id in exceptional_ids
                    
                    entity = get_entity_by_id(entity_id)
                    entity_name = entity.name if entity else entity_id
                    
                    # Add normal variant contribution
                    if has_normal:
                        description = perk.description.format(value=int(perk.normal_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "perk_type": perk_type_name,
                            "value": int(perk.normal_value),
                            "icon": perk.icon,
                            "is_exceptional": False,
                            "description": description,
                        })
                        if perk_type_name == "rarity_bias":
                            result["total_rarity_bias"] += int(perk.normal_value)
                        elif perk_type_name == "drop_luck":
                            result["total_drop_luck"] += int(perk.normal_value)
                    
                    # Add exceptional variant contribution (stacks!)
                    if has_exceptional:
                        if perk.exceptional_description:
                            description = perk.exceptional_description.format(value=int(perk.exceptional_value))
                        else:
                            description = perk.description.format(value=int(perk.exceptional_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "perk_type": perk_type_name,
                            "value": int(perk.exceptional_value),
                            "icon": perk.icon,
                            "is_exceptional": True,
                            "description": description,
                        })
                        if perk_type_name == "rarity_bias":
                            result["total_rarity_bias"] += int(perk.exceptional_value)
                        elif perk_type_name == "drop_luck":
                            result["total_drop_luck"] += int(perk.exceptional_value)
        
        result["contributors"].sort(key=lambda x: x["value"], reverse=True)
        
    except Exception as e:
        print(f"[Entity Perks] Error getting luck perk contributors: {e}")
        
    return result


def get_entity_qol_perks(adhd_buster: dict) -> dict:
    """
    Get quality-of-life entity perk bonuses.
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys: inventory_slots, eye_rest_cap, perfect_session_bonus
    """
    result = {
        "inventory_slots": 0,       # Extra inventory slots
        "eye_rest_cap": 0,          # Extra daily eye rest claims
        "perfect_session_bonus": 0, # Bonus for perfect sessions
    }
    
    try:
        from entitidex.entity_perks import calculate_active_perks, PerkType
        
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        
        result["inventory_slots"] = int(perks.get(PerkType.INVENTORY_SLOTS, 0))
        result["eye_rest_cap"] = int(perks.get(PerkType.EYE_REST_CAP, 0))
        result["perfect_session_bonus"] = int(perks.get(PerkType.PERFECT_SESSION, 0))
        
    except Exception as e:
        print(f"[Entity Perks] Error getting QoL perks: {e}")
        
    return result


def get_entity_eye_perks(adhd_buster: dict) -> dict:
    """
    Get Eye & Breath tab entity perk bonuses.
    
    When you have BOTH normal AND exceptional, you get BOTH bonuses (they stack).
    - Normal (Sam): +1 Eye Tier bonus
    - Exceptional (Pam): 50% Reroll chance
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys: 
            eye_tier_bonus (int): Tier bonus for eye routine rewards (Sam only)
            eye_reroll_chance (int): Chance % to re-roll on failure (Pam only)
            entity_id (str): ID of the entity providing the perk (empty if none)
            entity_name (str): Display name of the entity
            is_exceptional (bool): Whether the entity is exceptional
            has_both (bool): Whether both variants are collected
    """
    result = {
        "eye_tier_bonus": 0,
        "eye_reroll_chance": 0,
        "entity_id": "",
        "entity_name": "",
        "is_exceptional": False,
        "has_both": False,
    }
    
    try:
        from entitidex.entity_perks import calculate_active_perks, PerkType, ENTITY_PERKS
        
        entitidex_data = adhd_buster.get("entitidex", {})
        
        # Find the entity providing this perk (underdog_005)
        collected = set(entitidex_data.get("collected_entity_ids", 
                    entitidex_data.get("collected", set())))
        # Check both formats: exceptional_entity_ids (list) and exceptional_entities (dict)
        exceptional_ids = entitidex_data.get("exceptional_entity_ids", [])
        if isinstance(exceptional_ids, set):
            exceptional_ids = list(exceptional_ids)
        exceptional_dict = entitidex_data.get("exceptional_entities", {})
        exceptional_set = set(exceptional_ids) | set(exceptional_dict.keys())
        
        has_normal = "underdog_005" in collected
        has_exceptional = "underdog_005" in exceptional_set
        
        # Check if underdog_005 (Desk Succulent Sam/Pam) is collected in either form
        if has_normal or has_exceptional:
            result["entity_id"] = "underdog_005"
            result["is_exceptional"] = has_exceptional
            result["has_both"] = has_normal and has_exceptional
            
            # Add normal bonus if collected
            if has_normal:
                result["entity_name"] = "Desk Succulent Sam"
                result["eye_tier_bonus"] = 1
            
            # Add exceptional bonus if collected (stacks!)
            if has_exceptional:
                result["entity_name"] = "Desk Succulent Pam" if not has_normal else "Sam & Pam"
                result["eye_reroll_chance"] = 50
        
    except Exception as e:
        print(f"[Entity Perks] Error getting eye perks: {e}")
        
    return result


def get_entity_sleep_perks(adhd_buster: dict) -> dict:
    """
    Get Sleep tab entity perk bonuses (Study Owl Athena).
    
    Only the EXCEPTIONAL variant provides Sleep Tier bonus.
    Normal variant provides Night XP bonus (handled in ENTITY_PERKS).
    - Normal: +2% Night XP (via ENTITY_PERKS)
    - Exceptional: +1 Sleep Tier (via this function)
    - Both: +2% Night XP + 1 Sleep Tier
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys: 
            sleep_tier_bonus (int): Tier bonus for sleep rewards
            entity_id (str): ID of the entity providing the perk (empty if none)
            entity_name (str): Display name of the entity
            is_exceptional (bool): Whether the exceptional is collected
            has_both (bool): Whether both variants are collected
            description (str): Perk description for display
    """
    result = {
        "sleep_tier_bonus": 0,
        "entity_id": "",
        "entity_name": "",
        "is_exceptional": False,
        "has_both": False,
        "description": "",
    }
    
    try:
        entitidex_data = adhd_buster.get("entitidex", {})
        
        # Find the entity providing this perk (scholar_002 = Study Owl Athena)
        collected = set(entitidex_data.get("collected_entity_ids", 
                    entitidex_data.get("collected", set())))
        # Check both formats: exceptional_entity_ids (list) and exceptional_entities (dict)
        exceptional_ids = entitidex_data.get("exceptional_entity_ids", [])
        if isinstance(exceptional_ids, set):
            exceptional_ids = list(exceptional_ids)
        exceptional_dict = entitidex_data.get("exceptional_entities", {})
        exceptional_set = set(exceptional_ids) | set(exceptional_dict.keys())
        
        has_normal = "scholar_002" in collected
        has_exceptional = "scholar_002" in exceptional_set
        
        # Only exceptional provides Sleep Tier bonus
        if has_exceptional:
            result["entity_id"] = "scholar_002"
            result["is_exceptional"] = True
            result["has_both"] = has_normal
            result["entity_name"] = "Steady Owl Athena"
            result["sleep_tier_bonus"] = 1
            result["description"] = "Moonlit Wisdom: +1 Sleep Reward Tier"
        
    except Exception as e:
        print(f"[Entity Perks] Error getting sleep perks: {e}")
        
    return result


# Rat/mouse entity IDs that provide weight legendary bonus
WEIGHT_RAT_ENTITIES = {
    "scholar_001": {"normal_name": "Library Mouse Pip", "exceptional_name": "Library Mouse Quip", "icon": "đź­"},
    "scientist_004": {"normal_name": "Wise Lab Rat Professor", "exceptional_name": "Wise Lab Rat Assessor", "icon": "đź­"},
    "scientist_009": {"normal_name": "White Mouse Archimedes", "exceptional_name": "Bright Mouse Archimedes", "icon": "đź"},
    "underdog_001": {"normal_name": "Office Rat Reginald", "exceptional_name": "Officer Rat Regina", "icon": "đź"},
    "wanderer_009": {"normal_name": "Hobo Rat", "exceptional_name": "Robo Rat", "icon": "đź€"},
}


def get_entity_weight_perks(adhd_buster: dict) -> dict:
    """
    Get Weight tab entity perk bonuses (rat/mouse entities).
    
    Each collected rat/mouse entity provides:
    - Normal variant: +1% Legendary chance
    - Exceptional variant: +2% Legendary chance
    - BOTH variants: +3% (stacks!)
    
    Rat/Mouse entities:
    - scholar_001: Library Mouse Pip/Quip
    - scientist_004: Wise Lab Rat Professor/Assessor
    - scientist_009: White Mouse Archimedes
    - underdog_001: Office Rat Reginald/Regina
    - wanderer_009: Hobo Rat/Robo Rat
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys: 
            legendary_bonus (int): Total % bonus to Legendary chance
            contributors (list): List of contributing entities with details
            description (str): Combined perk description for display
    """
    result = {
        "legendary_bonus": 0,
        "contributors": [],
        "description": "",
    }
    
    try:
        entitidex_data = adhd_buster.get("entitidex", {})
        
        collected = set(entitidex_data.get("collected_entity_ids", 
                    entitidex_data.get("collected", set())))
        # Check both formats: exceptional_entity_ids (list) and exceptional_entities (dict)
        exceptional_ids = entitidex_data.get("exceptional_entity_ids", [])
        if isinstance(exceptional_ids, set):
            exceptional_ids = list(exceptional_ids)
        exceptional_dict = entitidex_data.get("exceptional_entities", {})
        exceptional_set = set(exceptional_ids) | set(exceptional_dict.keys())
        
        total_bonus = 0
        contributors = []
        
        for entity_id, info in WEIGHT_RAT_ENTITIES.items():
            has_normal = entity_id in collected
            has_exceptional = entity_id in exceptional_set
            
            # Add normal variant contribution
            if has_normal:
                total_bonus += 1
                contributors.append({
                    "entity_id": entity_id,
                    "name": info["normal_name"],
                    "bonus": 1,
                    "icon": info["icon"],
                    "is_exceptional": False,
                })
            
            # Add exceptional variant contribution (stacks!)
            if has_exceptional:
                total_bonus += 2
                contributors.append({
                    "entity_id": entity_id,
                    "name": info["exceptional_name"],
                    "bonus": 2,
                    "icon": info["icon"],
                    "is_exceptional": True,
                })
        
        result["legendary_bonus"] = total_bonus
        result["contributors"] = contributors
        
        if contributors:
            # Build description
            if len(contributors) == 1:
                c = contributors[0]
                result["description"] = f"{c['icon']} {c['name']}: +{c['bonus']}% Legendary"
            else:
                result["description"] = f"đź€ Rodent Squad: +{total_bonus}% Legendary ({len(contributors)} creatures)"
        
    except Exception as e:
        print(f"[Entity Perks] Error getting weight perks: {e}")
        
    return result


def get_entity_optimize_gear_cost(adhd_buster: dict) -> dict:
    """
    Get Optimize Gear cost based on Hobo Rat / Robo Rat entity.
    
    The Hobo Rat (wanderer_009) provides a special secondary perk:
    - Normal (Hobo Rat): Optimize Gear costs 1 coin
    - Exceptional (Robo Rat): Optimize Gear is FREE (0 coins)
    - BOTH: Uses best value (0 coins)
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys:
            cost (int): Actual cost for Optimize Gear (0, 1, or default 10)
            entity_id (str): ID of the entity providing the perk (empty if none)
            entity_name (str): Display name of the entity
            is_exceptional (bool): Whether the exceptional is collected
            has_both (bool): Whether both variants are collected
            description (str): Perk description for display
            has_perk (bool): Whether the perk is active
    """
    # Default cost from COIN_COSTS
    default_cost = COIN_COSTS.get("optimize_gear", 10)
    
    result = {
        "cost": default_cost,
        "entity_id": "",
        "entity_name": "",
        "is_exceptional": False,
        "has_both": False,
        "description": "",
        "has_perk": False,
    }
    
    try:
        entitidex_data = adhd_buster.get("entitidex", {})
        
        collected = set(entitidex_data.get("collected_entity_ids", 
                    entitidex_data.get("collected", set())))
        
        # Check both formats: exceptional_entity_ids (list) and exceptional_entities (dict)
        exceptional_ids = entitidex_data.get("exceptional_entity_ids", [])
        if isinstance(exceptional_ids, set):
            exceptional_ids = list(exceptional_ids)
        exceptional_dict = entitidex_data.get("exceptional_entities", {})
        exceptional_set = set(exceptional_ids) | set(exceptional_dict.keys())
        
        has_normal = "wanderer_009" in collected
        has_exceptional = "wanderer_009" in exceptional_set
        
        # Check if wanderer_009 (Hobo Rat / Robo Rat) is collected in either form
        if has_normal or has_exceptional:
            result["entity_id"] = "wanderer_009"
            result["has_perk"] = True
            result["is_exceptional"] = has_exceptional
            result["has_both"] = has_normal and has_exceptional
            
            # Use the best (lowest) cost available
            if has_exceptional:
                # Exceptional Robo Rat: FREE optimization
                result["entity_name"] = "Robo Rat" if not has_normal else "Rat Squad"
                result["cost"] = 0
                result["description"] = "đź¤– Robo Rat: Optimize Gear is FREE!"
            else:
                # Normal Hobo Rat: 1 coin only
                result["entity_name"] = "Hobo Rat"
                result["cost"] = 1
                result["description"] = "đź€ Hobo Rat: Optimize Gear costs only 1đźŞ™"
        
    except Exception as e:
        print(f"[Entity Perks] Error getting optimize gear cost: {e}")
        
    return result


def get_entity_sell_perks(adhd_buster: dict) -> dict:
    """
    Get sell item bonuses from Corner Office Chair / Stoner Office Chair (underdog_007).
    
    When you have BOTH variants, bonuses stack:
    - Normal (Corner Office Chair): +25% value when selling Epic items
    - Exceptional (Stoner Office Chair): +25% value when selling Legendary items
    - BOTH: +50% Epic, +25% Legendary (stacks!)
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys:
            has_perk (bool): Whether the perk is active
            entity_id (str): ID of the entity providing the perk
            entity_name (str): Display name of the entity
            is_exceptional (bool): Whether the exceptional is collected
            has_both (bool): Whether both variants are collected
            epic_bonus (float): Multiplier for Epic items
            legendary_bonus (float): Multiplier for Legendary items
            description (str): Perk description for display
            icon_path (str): Path to entity SVG icon
    """
    result = {
        "has_perk": False,
        "entity_id": "",
        "entity_name": "",
        "is_exceptional": False,
        "has_both": False,
        "epic_bonus": 1.0,
        "legendary_bonus": 1.0,
        "description": "",
        "icon_path": "",
    }
    
    try:
        entitidex_data = adhd_buster.get("entitidex", {})
        
        collected = set(entitidex_data.get("collected_entity_ids", 
                    entitidex_data.get("collected", set())))
        # Check both formats: exceptional_entity_ids (list) and exceptional_entities (dict)
        exceptional_ids = entitidex_data.get("exceptional_entity_ids", [])
        if isinstance(exceptional_ids, set):
            exceptional_ids = list(exceptional_ids)
        exceptional_dict = entitidex_data.get("exceptional_entities", {})
        exceptional_set = set(exceptional_ids) | set(exceptional_dict.keys())
        
        has_normal = "underdog_007" in collected
        has_exceptional = "underdog_007" in exceptional_set
        
        # Check if underdog_007 (Corner Office Chair) is collected in either form
        if has_normal or has_exceptional:
            result["entity_id"] = "underdog_007"
            result["has_perk"] = True
            result["is_exceptional"] = has_exceptional
            result["has_both"] = has_normal and has_exceptional
            
            descriptions = []
            
            # Add normal bonus if collected
            if has_normal:
                result["entity_name"] = "Corner Office Chair"
                result["epic_bonus"] = 1.25  # +25% for Epic
                descriptions.append("+25% Epic")
                result["icon_path"] = "icons/entities/underdog_007_corner_office_chair.svg"
            
            # Add exceptional bonus if collected (stacks!)
            if has_exceptional:
                result["entity_name"] = "Stoner Office Chair" if not has_normal else "Chair Duo"
                result["legendary_bonus"] = 1.25  # +25% for Legendary
                descriptions.append("+25% Legendary")
                result["icon_path"] = "icons/entities/exceptional/underdog_007_corner_office_chair_exceptional.svg"
            
            result["description"] = f"đźŞ‘ {result['entity_name']}: {', '.join(descriptions)}"
        
    except Exception as e:
        print(f"[Entity Perks] Error getting sell perks: {e}")
        
    return result


def get_entity_power_perks(adhd_buster: dict) -> dict:
    """
    Get hero power bonuses from collected entities with contributor details.
    
    When you have BOTH normal AND exceptional variants, you get BOTH bonuses.
    
    Args:
        adhd_buster: The main data dict containing entitidex progress
        
    Returns:
        Dict with keys:
            - total_power: int - Total power bonus from all entities
            - contributors: list - List of dicts with entity details:
                - entity_id: str
                - name: str
                - power: int - Power bonus value
                - icon: str - Perk icon emoji
                - is_exceptional: bool
                - description: str - Perk description
    """
    result = {
        "total_power": 0,
        "contributors": [],
    }
    
    try:
        from entitidex.entity_perks import ENTITY_PERKS, PerkType
        from entitidex.entity_pools import get_entity_by_id
        
        entitidex_data = adhd_buster.get("entitidex", {})
        # Support both old "collected" and new "collected_entity_ids" keys
        collected = set(entitidex_data.get("collected_entity_ids", 
                    entitidex_data.get("collected", set())))
        exceptional = entitidex_data.get("exceptional_entities", {})
        exceptional_ids = set(exceptional.keys()) if isinstance(exceptional, dict) else set(exceptional)
        
        # Get all unique entity IDs from both collections
        all_entity_ids = collected | exceptional_ids
        
        if not all_entity_ids:
            return result
            
        # Find all collected entities that provide POWER_FLAT perk
        for entity_id in all_entity_ids:
            perks = ENTITY_PERKS.get(entity_id)
            if not perks:
                continue
            for perk in perks:
                if perk.perk_type == PerkType.POWER_FLAT:
                    has_normal = entity_id in collected
                    has_exceptional = entity_id in exceptional_ids
                    
                    # Get entity details for display
                    entity = get_entity_by_id(entity_id)
                    entity_name = entity.name if entity else entity_id
                    
                    # Add normal variant contribution
                    if has_normal:
                        description = perk.description.format(value=int(perk.normal_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "power": int(perk.normal_value),
                            "icon": perk.icon,
                            "is_exceptional": False,
                            "description": description,
                        })
                        result["total_power"] += int(perk.normal_value)
                    
                    # Add exceptional variant contribution (stacks!)
                    if has_exceptional:
                        if perk.exceptional_description:
                            description = perk.exceptional_description.format(value=int(perk.exceptional_value))
                        else:
                            description = perk.description.format(value=int(perk.exceptional_value))
                        result["contributors"].append({
                            "entity_id": entity_id,
                            "name": entity_name,
                            "power": int(perk.exceptional_value),
                            "icon": perk.icon,
                            "is_exceptional": True,
                            "description": description,
                        })
                        result["total_power"] += int(perk.exceptional_value)
        
        # Sort by power value descending
        result["contributors"].sort(key=lambda x: x["power"], reverse=True)
        
    except Exception as e:
        print(f"[Entity Perks] Error getting power perks: {e}")
        
    return result


def format_lucky_options(lucky_options: dict) -> str:
    """
    Format lucky options for display.
    
    Args:
        lucky_options: Dict of option type -> value
    
    Returns:
        Formatted string like "+5% Coins, +3% XP"
    """
    if not lucky_options or not isinstance(lucky_options, dict):
        return ""
    
    parts = []
    for option_type, value in sorted(lucky_options.items()):
        if option_type in LUCKY_OPTION_TYPES:
            # Validate value is a positive number
            try:
                value = int(value) if value else 0
                if value > 0:
                    suffix = LUCKY_OPTION_TYPES[option_type]["suffix"]
                    parts.append(f"+{value}{suffix}")
            except (TypeError, ValueError):
                continue  # Skip invalid values
    
    return ", ".join(parts)


# ============================================================================
# SET BONUS SYSTEM - Matching items with same first word (adjective) give power bonuses!
# ============================================================================

# Set bonuses are based on the first word of item names (the adjective).
# Items generated with the same adjective form a set.
# Example: "Mystic Helm of Power" and "Mystic Boots of Speed" form a "Mystic" set.

# Bonus tiers based on rarity of the adjective
# Higher rarity adjectives give bigger set bonuses
SET_BONUS_BY_RARITY = {
    # Common adjectives - small bonus
    "Rusty": 8, "Worn-out": 8, "Home-made": 8, "Dusty": 8, "Crooked": 8,
    "Moth-eaten": 8, "Crumbling": 8, "Patched": 8, "Wobbly": 8, "Dented": 8,
    "Tattered": 8, "Chipped": 8,
    # Uncommon adjectives - moderate bonus
    "Sturdy": 12, "Reliable": 12, "Polished": 12, "Refined": 12, "Gleaming": 12,
    "Solid": 12, "Reinforced": 12, "Balanced": 12, "Tempered": 12, "Seasoned": 12,
    "Crafted": 12, "Honed": 12,
    # Rare adjectives - good bonus
    "Enchanted": 18, "Mystic": 18, "Glowing": 18, "Ancient": 18, "Blessed": 18,
    "Arcane": 18, "Shimmering": 18, "Ethereal": 18, "Spectral": 18, "Radiant": 18,
    "Infused": 18, "Rune-carved": 18,
    # Epic adjectives - great bonus
    "Legendary": 25, "Celestial": 25, "Void-touched": 25, "Dragon-forged": 25,
    "Titan's": 25, "Phoenix": 25, "Astral": 25, "Cosmic": 25, "Eldritch": 25,
    "Primordial": 25, "Abyssal": 25,
    # Legendary adjectives - massive bonus
    "Quantum": 35, "Omniscient": 35, "Transcendent": 35, "Reality-bending": 35,
    "Godslayer": 35, "Universe-forged": 35, "Eternal": 35, "Infinity": 35,
    "Apotheosis": 35, "Mythic": 35, "Supreme": 35,
    # Celestial adjectives - apex bonus
    "Singularity-born": 45, "Chronoweave": 45, "Paradox": 45, "Starforged": 45,
    "Omniversal": 45, "Empyrean": 45, "Aetherbound": 45, "Constellation": 45,
    "Transfinite": 45, "Harmonic": 45, "Seraphic": 45,
}

# Emojis for set display based on rarity tier
SET_EMOJI_BY_RARITY = {
    "Common": "\U0001faa8",
    "Uncommon": "\U0001f33f",
    "Rare": "\U0001f48e",
    "Epic": "\U0001f52e",
    "Legendary": "\U0001f451",
    "Celestial": "\u2728",
}

# Adjective to rarity mapping for emoji lookup
ADJECTIVE_RARITY = {}
for rarity, data in ITEM_RARITIES.items():
    for adj in data["adjectives"]:
        ADJECTIVE_RARITY[adj] = rarity

# Default bonus for unknown adjectives (story-specific items, etc.)
DEFAULT_SET_BONUS = 15

# Minimum matches required for set bonus activation
SET_BONUS_MIN_MATCHES = 2


# =============================================================================
# LEGENDARY MINIMALIST STYLE BONUS
# =============================================================================
# If all 7 equipped items are Legendary and 1 slot is intentionally empty,
# the player gets a special +350 style bonus with a unique title based on
# which slot is empty.

LEGENDARY_MINIMALIST_BONUS = 350

LEGENDARY_MINIMALIST_STYLES = {
    "Helmet": {
        "name": "Haircut Protector",
        "emoji": "đź’‡",
        "description": "Your perfectly styled hair is weapon enough"
    },
    "Chestplate": {
        "name": "Sun-Kissed Warrior", 
        "emoji": "â€ď¸Ź",
        "description": "Your tanned abs ARE the armor"
    },
    "Gauntlets": {
        "name": "Bare-Knuckle Champion",
        "emoji": "đź‘Š",
        "description": "Fists need no protection"
    },
    "Boots": {
        "name": "Hobbit Style",
        "emoji": "đź¦¶",
        "description": "Tough soles, tougher soul"
    },
    "Shield": {
        "name": "Unshielded Livewire",
        "emoji": "âšˇ",
        "description": "Defense is for the cautious"
    },
    "Weapon": {
        "name": "Body Linguist",
        "emoji": "đź‘Š",
        "description": "Your fist is the ultimate argument"
    },
    "Cloak": {
        "name": "Rear View Legend",
        "emoji": "đź”™",
        "description": "Nothing to hide, everything to show"
    },
    "Amulet": {
        "name": "Anti-Decorator",
        "emoji": "âś¨",
        "description": "The power comes from within"
    },
}


def calculate_legendary_minimalist_bonus(equipped: dict) -> dict:
    """
    Check if player qualifies for the Legendary Minimalist style bonus.
    
    Condition: Exactly 7 slots have Legendary items, and 1 slot is empty.
    
    Returns:
        dict with:
        - active: bool - whether bonus is active
        - empty_slot: str - which slot is empty (if active)
        - style: dict - style info (name, emoji, description)
        - bonus: int - power bonus (350 if active, 0 otherwise)
    """
    if not equipped or not isinstance(equipped, dict):
        return {"active": False, "empty_slot": None, "style": None, "bonus": 0}
    
    legendary_slots = []
    empty_slots = []
    non_legendary_slots = []
    
    for slot in GEAR_SLOTS:
        item = equipped.get(slot)
        # Consider slot empty if no item, or item is not a valid dict with a name
        if not item or not isinstance(item, dict) or not item.get("name"):
            empty_slots.append(slot)
        elif str(item.get("rarity", "")).strip().lower() == "legendary":
            legendary_slots.append(slot)
        else:
            non_legendary_slots.append(slot)
    
    # Must have exactly 7 legendary items and 1 empty slot
    if len(legendary_slots) == 7 and len(empty_slots) == 1 and len(non_legendary_slots) == 0:
        empty_slot = empty_slots[0]
        style = LEGENDARY_MINIMALIST_STYLES.get(empty_slot, {
            "name": "Minimalist Master",
            "emoji": "đźŽŻ",
            "description": "Less is more"
        })
        return {
            "active": True,
            "empty_slot": empty_slot,
            "style": style,
            "bonus": LEGENDARY_MINIMALIST_BONUS
        }
    
    return {"active": False, "empty_slot": None, "style": None, "bonus": 0}


def get_item_set_name(item: dict) -> str:
    """
    Get the set name for an item (its first word/adjective).
    
    Items with the same first word belong to the same set.
    Example: "Mystic Helm of Power" -> "Mystic"
    """
    if not item:
        return ""
    
    name = item.get("name", "")
    if not name:
        return ""
    
    # Get the first word (the adjective)
    first_word = name.split()[0] if name.split() else ""
    return first_word


def get_set_theme_data(set_name: str) -> dict:
    """
    Get theme data for a set (bonus_per_match, emoji).
    
    Works with the new first-word based system.
    """
    bonus = SET_BONUS_BY_RARITY.get(set_name, DEFAULT_SET_BONUS)
    rarity = ADJECTIVE_RARITY.get(set_name, "Rare")
    emoji = SET_EMOJI_BY_RARITY.get(rarity, "\u2694\ufe0f")
    return {
        "bonus_per_match": bonus,
        "emoji": emoji,
        "rarity": rarity
    }


# Backwards compatibility - ITEM_THEMES is now generated dynamically
# This provides the old interface for code that still references ITEM_THEMES
ITEM_THEMES = {}
for adj, bonus in SET_BONUS_BY_RARITY.items():
    rarity = ADJECTIVE_RARITY.get(adj, "Rare")
    emoji = SET_EMOJI_BY_RARITY.get(rarity, "\u2694\ufe0f")
    ITEM_THEMES[adj] = {
        "words": [adj.lower()],
        "bonus_per_match": bonus,
        "emoji": emoji
    }


def get_item_themes(item: dict) -> list:
    """
    Extract theme(s) from an item based on its first word (adjective).
    
    This is the deterministic set system - items with the same
    first word form a set.
    """
    set_name = get_item_set_name(item)
    if set_name:
        return [set_name]
    return []


def calculate_set_bonuses(equipped: dict) -> dict:
    """
    Calculate set bonuses from equipped items sharing the same first word (adjective).
    
    The set system is deterministic:
    - Items with the same first word (adjective) form a set
    - 2+ items with the same adjective activate the set bonus
    - Bonus per item depends on the rarity of the adjective
    
    Returns a dict with:
    - active_sets: list of {name, emoji, count, bonus, slots}
    - total_bonus: total power bonus from all sets
    """
    if not equipped or not isinstance(equipped, dict):
        return {"active_sets": [], "total_bonus": 0}
    
    # Count items by their first word (adjective)
    adjective_counts = {}
    adjective_items = {}
    
    for slot, item in equipped.items():
        if not item:
            continue
        adjective = get_item_set_name(item)
        if not adjective:
            continue
        adjective_counts[adjective] = adjective_counts.get(adjective, 0) + 1
        if adjective not in adjective_items:
            adjective_items[adjective] = []
        adjective_items[adjective].append(slot)
    
    # Calculate bonuses for adjectives with enough matches
    active_sets = []
    total_bonus = 0
    
    for adjective, count in adjective_counts.items():
        if count >= SET_BONUS_MIN_MATCHES:
            # Get bonus per match based on adjective rarity
            bonus_per_match = SET_BONUS_BY_RARITY.get(adjective, DEFAULT_SET_BONUS)
            bonus = bonus_per_match * count
            
            # Get emoji based on adjective's rarity
            rarity = ADJECTIVE_RARITY.get(adjective, "Rare")  # Default to Rare for unknown
            emoji = SET_EMOJI_BY_RARITY.get(rarity, "\u2694\ufe0f")
            
            active_sets.append({
                "name": adjective,
                "emoji": emoji,
                "count": count,
                "bonus": bonus,
                "slots": adjective_items[adjective]
            })
            total_bonus += bonus
    
    # Sort by bonus amount (highest first)
    active_sets.sort(key=lambda x: x["bonus"], reverse=True)
    
    return {
        "active_sets": active_sets,
        "total_bonus": total_bonus
    }



# ============================================================================
# LUCKY MERGE SYSTEM - High Risk, High Reward Item Fusion!
# ============================================================================

MERGE_COST = COIN_COSTS["merge_base"]  # Use centralized cost
MERGE_BOOST_COST = COIN_COSTS["merge_boost"]  # Boost cost for +25% success
MERGE_BASE_SUCCESS_RATE = 0.25  # 25% base chance
MERGE_BOOST_BONUS = 0.25  # +25% success rate when boosted
MERGE_BONUS_PER_ITEM = 0.03    # +3% per additional item after the first two
MERGE_MAX_SUCCESS_RATE = 0.90  # Cap at 90% success rate - always some risk!
MERGE_CELESTIAL_MIN_LEGENDARY_ITEMS = 5
MERGE_CELESTIAL_BASE_CHANCE = 0.01
MERGE_CELESTIAL_PER_EXTRA_LEGENDARY = 0.01
MERGE_CELESTIAL_MAX_CHANCE = 1.0

# Rarity upgrade paths
RARITY_UPGRADE = {
    rarity: get_next_rarity(rarity, max_rarity=MAX_OBTAINABLE_RARITY)
    for rarity in get_rarity_order()
}

RARITY_ORDER = get_rarity_order()


def _canonical_rarity(rarity: Optional[str], *, default: str = "Common") -> str:
    """Normalize rarity name to canonical casing/order labels."""
    if not isinstance(rarity, str):
        return default
    normalized = rarity.strip().lower()
    for known in RARITY_ORDER:
        if known.lower() == normalized:
            return known
    return default


def calculate_merge_success_rate(items: list, items_merge_luck: int = 0, city_bonus: int = 0) -> float:
    """
    Calculate the success rate for a lucky merge.
    
    Args:
        items: List of items to merge
        items_merge_luck: Total merge_luck% from items being merged (sacrificed for the merge)
        city_bonus: Total merge_success_bonus from city buildings (Forge) - default 0 for backward compat
    
    Returns:
        Merge success rate as float (0.0 to MERGE_MAX_SUCCESS_RATE)
    """
    # Filter out None items
    valid_items = [item for item in items if item is not None]
    if len(valid_items) < 2:
        return 0.0
    
    rate = MERGE_BASE_SUCCESS_RATE + (len(valid_items) - 2) * MERGE_BONUS_PER_ITEM
    
    # Items merge luck bonus - from items being sacrificed in the merge
    # Each 1% merge luck on merged items = +1% success rate
    # This encourages players to sacrifice items with merge_luck for better odds
    if items_merge_luck > 0:
        items_bonus = items_merge_luck / 100.0
        rate += items_bonus
    
    # City building bonus (Forge) - adds to success rate
    if city_bonus > 0:
        rate += city_bonus / 100.0
    
    return min(rate, MERGE_MAX_SUCCESS_RATE)


def count_merge_legendary_items(items: list) -> int:
    """Count Legendary items in a merge selection (None-safe)."""
    valid_items = [item for item in (items or []) if item is not None]
    return sum(
        1
        for item in valid_items
        if _canonical_rarity(item.get("rarity"), default="Common") == "Legendary"
    )


def calculate_merge_celestial_chance(items: list) -> float:
    """
    Calculate Celestial unlock chance for Lucky Merge.

    Rules:
    - Fewer than 5 Legendary items: 0%
    - Exactly 5 Legendary items: 1%
    - +1% for each additional Legendary item
    """
    legendary_count = count_merge_legendary_items(items)
    if legendary_count < MERGE_CELESTIAL_MIN_LEGENDARY_ITEMS:
        return 0.0

    extra_legendary = legendary_count - MERGE_CELESTIAL_MIN_LEGENDARY_ITEMS
    chance = MERGE_CELESTIAL_BASE_CHANCE + (extra_legendary * MERGE_CELESTIAL_PER_EXTRA_LEGENDARY)
    return max(0.0, min(MERGE_CELESTIAL_MAX_CHANCE, chance))


def get_merge_result_rarity(items: list) -> str:
    """Determine the rarity of the merged item result.
    
    Result is the highest rarity among merged items + 1 tier (capped at current max obtainable tier).
    Common items are ignored when determining base tier - they add merge fuel
    without affecting the result tier. Only non-Common items affect the result.
    """
    # Filter out None items
    valid_items = [item for item in items if item is not None]
    if not valid_items:
        return "Common"
    
    # Safely get rarity index, defaulting to 0 (Common) for invalid values
    def safe_rarity_idx(item):
        rarity = _canonical_rarity(item.get("rarity", "Common"), default="Common")
        try:
            return RARITY_ORDER.index(rarity)
        except ValueError:
            return 0  # Default to Common if invalid rarity
    
    # Filter out Common items - they don't affect the tier
    non_common_items = [
        item
        for item in valid_items
        if _canonical_rarity(item.get("rarity", "Common"), default="Common") != "Common"
    ]
    
    if not non_common_items:
        # All items are Common - result is Uncommon (upgrade from Common)
        return "Uncommon"
    
    # Get HIGHEST rarity from non-Common items + 1 tier
    rarity_indices = [safe_rarity_idx(item) for item in non_common_items]
    highest_idx = max(rarity_indices)
    highest_rarity = RARITY_ORDER[highest_idx]
    
    # Upgrade by 1 tier (capped by MAX_OBTAINABLE_RARITY)
    return RARITY_UPGRADE.get(
        highest_rarity,
        get_standard_reward_rarity_order()[-1],
    )


def is_merge_worthwhile(items: list) -> tuple:
    """Check if a merge is worthwhile (can result in upgrade)."""
    # Filter out None items
    valid_items = [item for item in items if item is not None]
    if not valid_items or len(valid_items) < 2:
        return False, "Need at least 2 items"
    
    max_obtainable_rarity = get_standard_reward_rarity_order()[-1]
    all_max_rarity = all(
        _canonical_rarity(item.get("rarity"), default="Common") == max_obtainable_rarity
        for item in valid_items
    )
    if all_max_rarity:
        # Allow top-tier-only merges as a reroll to a new top-tier item/slot.
        return True, ""
    
    return True, ""


# Tier jump probabilities for lucky merge (higher jumps are rarer for more thrill)
# Tiered probability system:
#   +1 tier: 50% - Common result, still an upgrade
#   +2 tiers: 30% - Good result, nice jump
#   +3 tiers: 15% - Great result, significant upgrade!
#   +4 tiers: 5% - JACKPOT! Jump straight to Legendary (from Common)
MERGE_TIER_JUMP_WEIGHTS = [
    (1, 50),   # +1 tier: 50% chance (basic upgrade)
    (2, 30),   # +2 tiers: 30% chance (good upgrade)
    (3, 15),   # +3 tiers: 15% chance (great upgrade!)
    (4, 5),    # +4 tiers: 5% chance (LEGENDARY JACKPOT!)
]

# Canonical 5-tier order used by merge lottery UI/animation.
MERGE_TIER_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
MERGE_BASE_WINDOW = [5, 15, 60, 15, 5]
MERGE_UPGRADED_WINDOW = [5, 10, 25, 45, 15]


def calculate_merge_tier_weights(base_rarity: str, tier_upgrade_enabled: bool = False) -> list:
    """
    Calculate merge rarity distribution weights for the two-stage merge lottery.

    Args:
        base_rarity: Center rarity tier for the window
        tier_upgrade_enabled: Whether upgraded window should be used

    Returns:
        List of 5 weights in MERGE_TIER_ORDER order
    """
    window = MERGE_UPGRADED_WINDOW if tier_upgrade_enabled else MERGE_BASE_WINDOW

    try:
        center_idx = MERGE_TIER_ORDER.index(base_rarity)
    except ValueError:
        # Clamp unknown/future tiers (e.g., Celestial) into supported 5-tier merge window.
        try:
            center_idx = min(max(RARITY_ORDER.index(base_rarity), 0), len(MERGE_TIER_ORDER) - 1)
        except ValueError:
            center_idx = 2  # Rare-centered fallback

    weights = [0] * len(MERGE_TIER_ORDER)
    for offset, pct in zip([-2, -1, 0, 1, 2], window):
        target_idx = center_idx + offset
        clamped_idx = max(0, min(len(MERGE_TIER_ORDER) - 1, target_idx))
        weights[clamped_idx] += pct
    return weights


def roll_merge_lottery(
    success_threshold: float,
    base_rarity: str,
    tier_upgrade_enabled: bool = False,
    success_roll: Optional[float] = None,
    tier_roll: Optional[float] = None,
) -> dict:
    """
    Canonical backend roll for merge/merge-like two-stage lotteries.

    Stage 1: Roll rarity tier from calculated distribution.
    Stage 2: Roll success/fail against success threshold.
    """
    threshold = max(0.0, min(1.0, float(success_threshold)))
    if success_roll is None:
        success_roll = random.random()
    success_roll = max(0.0, min(1.0, float(success_roll)))

    weights = calculate_merge_tier_weights(base_rarity, tier_upgrade_enabled=tier_upgrade_enabled)
    total = sum(weights)

    if tier_roll is None:
        tier_roll = random.random() * 100.0
    tier_roll = max(0.0, min(100.0, float(tier_roll)))

    rolled_tier = MERGE_TIER_ORDER[-1]
    cumulative = 0.0
    if total > 0:
        for tier_name, weight in zip(MERGE_TIER_ORDER, weights):
            zone_pct = (weight / total) * 100.0
            if tier_roll < cumulative + zone_pct:
                rolled_tier = tier_name
                break
            cumulative += zone_pct

    success = success_roll < threshold
    return {
        "success": success,
        "success_roll": success_roll,
        "success_threshold": threshold,
        "tier_roll": tier_roll,
        "rolled_tier": rolled_tier,
        "tier_weights": weights,
        "base_rarity": base_rarity,
        "tier_upgrade_enabled": bool(tier_upgrade_enabled),
    }


def roll_eye_routine_reward_outcome(
    success_threshold: float,
    base_rarity: str,
    adhd_buster: Optional[dict] = None,
    success_roll: Optional[float] = None,
    tier_roll: Optional[float] = None,
) -> dict:
    """
    Canonical backend roll for eye-routine two-stage rewards.

    Unlike lucky-merge, this path applies hero-power rarity gates to tier rolls.
    """
    threshold = max(0.0, min(1.0, float(success_threshold)))
    if success_roll is None:
        success_roll = random.random()
    success_roll = max(0.0, min(1.0, float(success_roll)))

    weights = calculate_merge_tier_weights(base_rarity, tier_upgrade_enabled=False)
    gated_outcome = evaluate_power_gated_rarity_roll(
        MERGE_TIER_ORDER,
        weights,
        adhd_buster=adhd_buster,
        roll=tier_roll,
    )

    success = success_roll < threshold
    resolved_tier_roll = max(0.0, min(100.0, float(gated_outcome.get("roll", 0.0))))
    rolled_tier = gated_outcome.get("rarity", MERGE_TIER_ORDER[-1])

    return {
        "success": success,
        "success_roll": success_roll,
        "success_threshold": threshold,
        "tier_roll": resolved_tier_roll,
        "rolled_tier": rolled_tier,
        "tier_weights": weights,
        "base_rarity": base_rarity,
        "tier_upgrade_enabled": False,
        "power_gating": gated_outcome,
    }


def roll_push_your_luck_outcome(
    success_threshold: float,
    item_save_threshold: float = 0.0,
    success_roll: Optional[float] = None,
    item_save_roll: Optional[float] = None,
) -> dict:
    """
    Canonical backend roll for merge "Push Your Luck" outcomes.

    Stage 1: Roll success/fail against push-luck threshold.
    Stage 2: On failure, optional item-save roll (e.g., Blank Parchment).
    """
    threshold = max(0.01, min(0.99, float(success_threshold)))
    save_threshold = max(0.0, min(1.0, float(item_save_threshold)))

    if success_roll is None:
        success_roll = random.random()
    success_roll = max(0.0, min(1.0, float(success_roll)))
    success = success_roll < threshold

    resolved_item_save_roll = None
    item_saved = False

    if not success and save_threshold > 0.0:
        if item_save_roll is None:
            item_save_roll = random.random()
        resolved_item_save_roll = max(0.0, min(1.0, float(item_save_roll)))
        item_saved = resolved_item_save_roll < save_threshold

    return {
        "success": success,
        "success_roll": success_roll,
        "success_threshold": threshold,
        "item_saved": item_saved,
        "item_save_roll": resolved_item_save_roll,
        "item_save_threshold": save_threshold,
    }


def get_random_tier_jump() -> int:
    """Roll for random tier upgrade on successful merge.
    
    Tiered probability system for exciting merge results:
    - 50% chance for +1 tier (reliable upgrade)
    - 30% chance for +2 tiers (good luck!)
    - 15% chance for +3 tiers (excellent luck!)
    - 5% chance for +4 tiers (JACKPOT - straight to Legendary!)
    
    Returns:
        Number of tiers to jump (1, 2, 3, or 4)
    """
    roll = random.randint(1, 100)
    cumulative = 0
    for jump, weight in MERGE_TIER_JUMP_WEIGHTS:
        cumulative += weight
        if roll <= cumulative:
            return jump
    return 1  # Fallback


def perform_lucky_merge(
    items: list,
    story_id: str = None,
    items_merge_luck: int = 0,
    city_bonus: int = 0,
    tier_upgrade_enabled: bool = False,
    success_roll: Optional[float] = None,
    tier_roll: Optional[float] = None,
    celestial_roll: Optional[float] = None,
    base_rarity: Optional[str] = None,
) -> dict:
    """Attempt a lucky merge of items.
    
    Backend is authoritative for both rolls:
    - Success roll against merge success threshold
    - Tier roll against calculated rarity distribution window
    
    Args:
        items: List of items to merge
        story_id: Story theme for the resulting item
        items_merge_luck: Total merge_luck% from items being merged (sacrificed)
        city_bonus: Merge success bonus from city buildings
        tier_upgrade_enabled: Whether upgraded tier window is active
        success_roll: Optional externally provided success roll (0.0-1.0)
        tier_roll: Optional externally provided tier roll (0.0-100.0)
        celestial_roll: Optional externally provided Celestial roll (0.0-1.0)
        base_rarity: Optional explicit base rarity center for tier window
    """
    # Filter out None items
    valid_items = [item for item in items if item is not None]
    if len(valid_items) < 2:
        return {"success": False, "error": "Need at least 2 items to merge"}

    legendary_count = count_merge_legendary_items(valid_items)
    celestial_chance = calculate_merge_celestial_chance(valid_items)
    
    success_rate = calculate_merge_success_rate(
        valid_items,
        items_merge_luck=items_merge_luck,
        city_bonus=city_bonus,
    )
    resolved_base_rarity = _canonical_rarity(base_rarity or get_merge_result_rarity(valid_items), default="Common")
    lottery = roll_merge_lottery(
        success_threshold=success_rate,
        base_rarity=resolved_base_rarity,
        tier_upgrade_enabled=tier_upgrade_enabled,
        success_roll=success_roll,
        tier_roll=tier_roll,
    )

    result = {
        "success": lottery["success"],
        "items_lost": valid_items,
        "roll": lottery["success_roll"],
        "needed": lottery["success_threshold"],
        "roll_pct": f"{lottery['success_roll']*100:.1f}%",
        "needed_pct": f"{lottery['success_threshold']*100:.1f}%",
        "tier_roll": lottery["tier_roll"],
        "rolled_tier": lottery["rolled_tier"],
        "tier_weights": lottery["tier_weights"],
        "base_rarity": resolved_base_rarity,
        "tier_upgraded": bool(tier_upgrade_enabled),
        "legendary_count": legendary_count,
        "celestial_chance": celestial_chance,
        "celestial_roll": None,
        "celestial_unlocked": celestial_chance > 0.0,
        "celestial_triggered": False,
        "tier_jump": 0,
        "final_rarity": None,
        "result_item": None,
    }

    if lottery["success"]:
        final_rarity = lottery["rolled_tier"]
        if celestial_chance > 0.0:
            resolved_celestial_roll = celestial_roll
            if resolved_celestial_roll is None:
                resolved_celestial_roll = random.random()
            try:
                resolved_celestial_roll = float(resolved_celestial_roll)
            except (TypeError, ValueError):
                resolved_celestial_roll = 1.0
            resolved_celestial_roll = max(0.0, min(1.0, resolved_celestial_roll))
            result["celestial_roll"] = resolved_celestial_roll
            if resolved_celestial_roll < celestial_chance:
                final_rarity = "Celestial"
                result["celestial_triggered"] = True

        try:
            base_idx = RARITY_ORDER.index(resolved_base_rarity)
        except ValueError:
            base_idx = 0
        try:
            final_idx = RARITY_ORDER.index(final_rarity)
        except ValueError:
            final_idx = base_idx

        # Backward-compatible "jump" metric for UI text paths.
        result["tier_jump"] = max(1, final_idx - base_idx + 1)
        result["final_rarity"] = final_rarity
        if final_rarity == "Celestial":
            result["result_item"] = generate_celestial_item(
                story_id=story_id,
                source="merge_bonus",
            )
        else:
            result["result_item"] = generate_item(rarity=final_rarity, story_id=story_id)

    return result


# ============================================================================
# ADHD Buster Diary - Epic Adventure Journal System
# ============================================================================

# ============================================================================
# STORY-THEMED DIARY CONTENT
# Each story has unique verbs, targets, locations, outcomes, and flavor text
# that reflect the character's daily struggles in their world.
# ============================================================================

STORY_DIARY_THEMES = {
    # =========================================================================
    # WARRIOR DIARY - Classic Fantasy Adventures (EXPANDED)
    # =========================================================================
    "warrior": {
        "theme_name": "âš”ď¸Ź Battle Chronicle",
        "verbs": {
            "pathetic": [
                "accidentally poked", "tripped over", "awkwardly stared at",
                "nervously waved at", "mildly annoyed", "bumped into",
                "gave a participation trophy to", "accidentally photobombed",
                "sneezed on", "apologized profusely to", "gently tapped",
                "ran away from", "hid behind a barrel from", "pretended not to see",
                "offered a handshake to", "complimented the shoes of",
                "asked for directions from", "borrowed a pencil from",
                "shared an awkward elevator ride with", "accidentally insulted",
                "stepped on the cape of", "spilled ale on", "lost a staring contest to",
                "was startled by", "mistook for a coat rack", "walked into",
                "mumbled incoherently at", "forgot the name of", "waved goodbye to",
                "made an excuse to leave from", "pretended to be busy near"
            ],
            "modest": [
                "challenged to honorable combat", "traded blows with", "sparred with",
                "had a training match with", "arm-wrestled", "competed against",
                "crossed swords with", "exchanged fierce glares with",
                "had a respectable duel with", "proved my worth against",
                "stood my ground against", "pushed back against",
                "held the line against", "defended the village from",
                "survived an encounter with", "fought to a standstill with",
                "earned the respect of", "matched blades with",
                "tested my mettle against", "rose to the challenge of",
                "faced bravely", "charged into battle with",
                "clashed shields with", "traded war cries with",
                "showed no fear against", "rallied my courage against"
            ],
            "decent": [
                "defeated in single combat", "vanquished", "outmaneuvered",
                "conquered", "bested in battle", "triumphed over",
                "crushed the defenses of", "broke the ranks of",
                "sent fleeing", "claimed victory over", "dominated",
                "overwhelmed", "routed the forces of", "destroyed the army of",
                "shattered the morale of", "brought low", "humbled in combat",
                "proved superior to", "demonstrated mastery over",
                "left defeated", "sent to the healers", "forced into retreat",
                "outclassed", "showed no mercy to", "made an example of",
                "ended the reign of", "toppled from power"
            ],
            "heroic": [
                "slayed", "banished to another realm", "sealed away forever",
                "struck down with legendary fury", "crushed the army of",
                "annihilated the legion of", "became the nightmare of",
                "forged my legend by defeating", "inspired ballads by conquering",
                "etched my name in history against", "performed miracles against",
                "defied the odds and destroyed", "rewrote fate by vanquishing",
                "achieved the impossible against", "became legend by slaying",
                "turned the tide of war against", "saved kingdoms from",
                "united the realms by defeating", "fulfilled prophecy against",
                "achieved destiny by conquering"
            ],
            "epic": [
                "obliterated from existence", "erased from the battlefield of time",
                "became the doom of", "shattered the very essence of",
                "unmade the reality of", "transcended mortality to defeat",
                "became one with war itself to destroy", "wielded cosmic fury against",
                "channeled the power of all warriors against",
                "achieved apotheosis in battle with", "became the end of",
                "rewrote the laws of combat against", "became eternal by defeating",
                "ascended through victory over"
            ],
            "legendary": [
                "became one with the warrior spirit alongside",
                "transcended mortal combat with", "achieved battle nirvana with",
                "merged with the concept of victory against",
                "became the living embodiment of war by defeating",
                "unified all combat styles to transcend",
                "achieved perfect warrior enlightenment against",
                "became the alpha and omega of battle with"
            ],
            "godlike": [
                "redefined the concept of victory against",
                "became the eternal champion by defeating",
                "transcended all concepts of conflict with",
                "became the source of all future battles by conquering",
                "rewrote the fundamental nature of combat against",
                "became the cosmic arbiter of war with"
            ]
        },
        "targets": {
            "pathetic": [
                "training dummy", "confused goblin scout", "lost merchant's chicken",
                "grumpy innkeeper", "a scarecrow that looked suspicious",
                "a particularly aggressive squirrel", "my own shadow",
                "a door that wouldn't open", "a stubborn mule", "a sleeping guard",
                "a tavern cat", "an old farmer's fence", "a practice target",
                "a training mannequin", "a wooden post", "a pile of hay",
                "the village drunk", "a lost sheep", "a cranky vendor",
                "a broken cart wheel", "my own reflection", "a rusty weathervane",
                "someone's garden gnome", "an abandoned helmet", "a leaky bucket"
            ],
            "modest": [
                "goblin raiding party", "bandit captain", "wolf pack alpha",
                "orc berserker", "rival knight in training", "a band of highwaymen",
                "a troll bridge keeper", "a mercenary squad", "a rogue mage",
                "a corrupt guard captain", "a pack of dire wolves",
                "a nest of giant spiders", "a haunted suit of armor",
                "a rival clan", "a gang of thieves", "a barbarian raider",
                "an escaped war beast", "a cursed knight", "a fallen paladin",
                "a vengeful spirit", "a band of orcs", "a cave troll"
            ],
            "decent": [
                "dragon whelp", "veteran warlord", "cursed champion",
                "demon spawn", "undead general", "a legendary bounty hunter",
                "a dark knight", "a vampire lord", "a lich's champion",
                "a war golem", "an elemental titan", "a hydra",
                "a kraken's spawn", "a phoenix warrior", "a shadow assassin",
                "a death knight", "a corrupted paladin", "a demon commander",
                "an arch-mage", "a legendary beast", "a mythical guardian"
            ],
            "heroic": [
                "ancient dragon", "demon prince", "titan of war",
                "the Shadow Self", "army of the damned", "an elder god's avatar",
                "the Void Knight", "the Chaos Emperor", "an archangel of war",
                "the Dragon King", "a thousand-year curse", "the Lich Emperor",
                "the Beast of Legend", "the Immortal Champion",
                "the Spirit of Vengeance", "the Harbinger of Doom"
            ],
            "epic": [
                "the God of Destruction", "primordial chaos beast",
                "the living concept of warfare", "the Entropy Incarnate",
                "the First and Last Dragon", "the Cosmic Destroyer",
                "the Universe Devourer", "the Reality Shatterer",
                "the Existence Ender", "the Multiverse Conqueror"
            ],
            "legendary": [
                "the first warrior ever born", "the spirit of all battles",
                "the concept of conflict itself", "the primordial war god",
                "the source of all violence", "the essence of struggle"
            ],
            "godlike": [
                "the cosmic embodiment of conflict", "the original concept of struggle",
                "the universe's primal fury", "existence itself in combat form",
                "the alpha warrior of all realities"
            ]
        },
        "locations": {
            "pathetic": [
                "behind the tavern", "in the training yard", "near the outhouse",
                "at the local farmer's field", "in a puddle", "behind the stables",
                "in the root cellar", "at the village well", "near the pig pen",
                "in an empty barn", "at the town garbage heap", "behind a bush",
                "in my own backyard", "at the practice range", "near the compost pile",
                "in a muddy ditch", "at the edge of town", "behind the blacksmith",
                "near the old well", "in the chicken coop", "at the town square fountain",
                "behind the general store", "in the alley", "near the broken fence"
            ],
            "modest": [
                "in the dark forest", "at the mountain pass", "in ancient ruins",
                "at the haunted crossroads", "in the gladiator pit",
                "at the border fortress", "in the misty swamp",
                "at the abandoned mine", "in the thieves' guild basement",
                "at the tournament grounds", "in the cursed cemetery",
                "at the wizard's tower entrance", "in the dragon's foothills",
                "at the mercenary camp", "in the forgotten temple",
                "at the edge of the wilderness", "in the bandit stronghold",
                "at the orc encampment", "in the beast's lair"
            ],
            "decent": [
                "at the gates of the dark fortress", "on the dragon's peak",
                "in the heart of the demon realm", "at the edge of the abyss",
                "in the throne room of the dark lord", "at the world's edge",
                "in the realm between realms", "at the legendary battlefield",
                "in the heart of the volcano", "at the bottom of the ocean",
                "in the sky citadel", "at the gates of the underworld",
                "in the frozen wastes of legend", "at the nexus of power"
            ],
            "heroic": [
                "in the dimension of eternal battle", "at the crossroads of all wars",
                "in the void between conquests", "at the throne of the war gods",
                "in the legendary hall of heroes", "at the edge of infinity",
                "in the realm of pure combat", "at the source of all courage",
                "in the dimension of legends", "at the heart of the multiverse"
            ],
            "epic": [
                "in a reality forged from pure conflict",
                "at the point where courage itself was born",
                "in the fabric of existence itself",
                "at the birthplace of all warriors",
                "in the cosmic colosseum", "at the universe's battlefield"
            ],
            "legendary": [
                "in the first battlefield ever conceived",
                "at the origin of all combat",
                "in the primordial arena of creation",
                "at the nexus of all warrior spirits"
            ],
            "godlike": [
                "at the source code of valor itself",
                "in the fundamental nature of struggle",
                "at the cosmic origin of conflict",
                "in the heart of existence's eternal battle"
            ]
        },
        "outcomes": {
            "pathetic": [
                "a minor bruise", "awkward silence", "both of us just walking away",
                "a promise to try again tomorrow", "mutual embarrassment",
                "absolutely nothing happening", "a weak handshake",
                "a polite cough and exit", "me needing a nap",
                "a story I'll never tell", "a bruised ego", "a torn tunic",
                "a slightly dented helmet", "a need for ale",
                "a lesson learned (maybe)", "quiet disappointment",
                "a vow to practice more", "a strategic retreat",
                "me pretending it didn't happen", "an unspoken agreement to forget"
            ],
            "modest": [
                "mutual respect", "a worthy rivalry begun",
                "both of us gaining experience", "a draw",
                "a handshake between warriors", "a story worth telling at the tavern",
                "new scars to show off", "growing confidence",
                "the start of a legend", "a taste of glory",
                "recognition from peers", "a step toward greatness",
                "the first chapter of my saga", "earned bruises",
                "a reputation being built", "worthy battle wounds"
            ],
            "decent": [
                "glorious victory", "songs being written", "a statue commissioned",
                "the bards taking notice", "fame spreading across the land",
                "my name being remembered", "a feast in my honor",
                "a title being bestowed", "knights saluting me",
                "the king taking notice", "treasure beyond measure",
                "a legendary weapon earned", "a keep being granted",
                "an army pledging loyalty", "prophecies being updated"
            ],
            "heroic": [
                "legends being born", "prophecies being fulfilled",
                "the gods nodding in approval", "history being rewritten",
                "the stars rearranging in my honor", "kingdoms united under my banner",
                "eternal glory", "a throne being offered", "immortality in legend",
                "the world forever changed", "ages being named after me"
            ],
            "epic": [
                "reality itself trembling", "new constellations forming in my honor",
                "the multiverse taking notice", "dimensions aligning",
                "the fabric of time recording my deed",
                "cosmic entities bowing in recognition"
            ],
            "legendary": [
                "the concept of 'victory' being permanently redefined",
                "the fundamental laws of combat changing",
                "my essence merging with the warrior spirit",
                "becoming one with the legend"
            ],
            "godlike": [
                "a new era of heroism beginning",
                "the universe acknowledging my supremacy",
                "existence itself celebrating my triumph",
                "becoming the eternal standard of victory"
            ]
        },
        "flavor": {
            "pathetic": [
                "My sword was a bit rusty.",
                "I forgot my shield at home.",
                "My battle cry came out as a squeak.",
                "I tripped over my own feet twice.",
                "My armor made embarrassing noises.",
                "I accidentally dropped my weapon.",
                "The audience cringed audibly.",
                "Even the crows looked away.",
                "A child offered me advice.",
                "My horse seemed disappointed.",
                "The bard didn't even take notes.",
                "I got lost on the way.",
                "My breakfast disagreed with me mid-battle.",
                "I forgot the battle was today.",
                "My opponent yawned.",
                "A gentle breeze knocked me over.",
                "I challenged the wrong person.",
                "The practice dummy won."
            ],
            "modest": [
                "The crowd of three people seemed mildly impressed.",
                "A passing knight gave me a nod.",
                "My armor only clanked embarrassingly twice.",
                "Someone in the crowd didn't fall asleep.",
                "The bard wrote down a sentence about me.",
                "My parents would be moderately proud.",
                "The village elder raised an eyebrow approvingly.",
                "A child asked for my autograph.",
                "The tavern keeper offered a free drink.",
                "My opponent admitted it wasn't easy.",
                "A squire asked to train with me.",
                "The blacksmith noticed my improved technique."
            ],
            "decent": [
                "The stars aligned for this battle.",
                "Ancient war drums echoed in approval.",
                "My ancestors watched with pride.",
                "The crowd erupted in cheers.",
                "Bards immediately began composing.",
                "Knights raised their swords in salute.",
                "The king sent a messenger of congratulations.",
                "My weapon glowed with approval.",
                "Thunder rolled to punctuate my victory.",
                "A rainbow appeared at the perfect moment.",
                "Eagles circled overhead majestically.",
                "The very ground seemed to honor me."
            ],
            "heroic": [
                "The gods paused their own battles to watch.",
                "Time itself slowed to witness my strike.",
                "Lightning struck at the perfect moment.",
                "The stars formed my initials in the sky.",
                "Ancient prophecies updated in real-time.",
                "The world held its breath.",
                "All wars everywhere paused in respect.",
                "The moon turned to witness.",
                "History books rewrote themselves."
            ],
            "epic": [
                "Parallel versions of me in other dimensions also won.",
                "The multiverse's war council took notes.",
                "Cosmic entities placed bets on my favor.",
                "Reality itself bent to accommodate my legend.",
                "Time travelers came back just to watch.",
                "The universe itself seemed to cheer."
            ],
            "legendary": [
                "This battle is now taught in celestial academies.",
                "The very concept of 'warrior' was updated.",
                "Future heroes model themselves after this moment.",
                "The cosmos recorded this in crystalline memory."
            ],
            "godlike": [
                "I am now the cosmic standard for victory.",
                "The universe's victory protocols were updated.",
                "Existence itself celebrates this moment eternally.",
                "All future battles are measured against this one."
            ]
        }
    },

    # =========================================================================
    # SCHOLAR DIARY - Academic & Intellectual Pursuits (EXPANDED)
    # =========================================================================
    "scholar": {
        "theme_name": "đź“š Research Journal",
        "verbs": {
            "pathetic": [
                "misread", "accidentally spilled coffee on", "lost my notes about",
                "fell asleep while studying", "forgot the deadline for",
                "cited incorrectly", "plagiarized accidentally", "daydreamed through",
                "doodled instead of researching", "confused the topic with",
                "misspelled the title of", "submitted late",
                "formatted incorrectly", "used Comic Sans for",
                "forgot to save my work on", "deleted the wrong file about",
                "got distracted while researching", "procrastinated on",
                "overcomplicated my analysis of", "missed the obvious point about",
                "over-caffeinated while studying", "ran out of highlighters during",
                "got lost in Wikipedia instead of studying", "debated myself about",
                "questioned my career choice while studying"
            ],
            "modest": [
                "successfully summarized", "completed the chapter on",
                "found a decent source about", "understood the basics of",
                "took respectable notes on", "formed a hypothesis about",
                "conducted preliminary research on", "organized my thoughts about",
                "outlined my argument regarding", "gathered evidence for",
                "drafted my thesis on", "reviewed the literature on",
                "attended a lecture about", "discussed intelligently about",
                "made progress on understanding", "improved my knowledge of"
            ],
            "decent": [
                "published a paper on", "delivered a presentation about",
                "defended my thesis on", "got cited for my work on",
                "received peer approval for", "discovered new insights about",
                "connected disparate theories about", "advanced the field of",
                "challenged existing paradigms about", "proved my hypothesis on",
                "impressed the committee with", "contributed meaningfully to",
                "received a grant to study", "was invited to speak about"
            ],
            "heroic": [
                "revolutionized the understanding of", "became the leading expert on",
                "rewrote the textbooks about", "solved a decades-old mystery about",
                "achieved breakthrough insight into", "unified competing theories on",
                "earned the Nobel for work on", "changed the paradigm of",
                "transcended conventional wisdom about", "became synonymous with"
            ],
            "epic": [
                "transcended human knowledge to understand",
                "unlocked the secrets of the universe from",
                "became omniscient by studying",
                "achieved total enlightenment regarding",
                "merged with the concept of knowledge itself through",
                "rewrote the laws of reality by understanding"
            ],
            "legendary": [
                "merged consciousness with all knowledge of",
                "became the living embodiment of wisdom from",
                "transcended mortal understanding of",
                "became one with universal truth regarding"
            ],
            "godlike": [
                "redefined the nature of truth itself regarding",
                "became the cosmic source of all knowledge about",
                "achieved absolute understanding of",
                "became the universal constant of wisdom through"
            ]
        },
        "targets": {
            "pathetic": [
                "a particularly aggressive spell-checker", "overdue library fine",
                "an undergrad with too many questions", "corrupted save file",
                "a pretentious coffee shop philosopher", "my own footnotes",
                "a confusing abstract", "a missing reference",
                "an endless bibliography", "a stubborn citation format",
                "my advisor's vague feedback", "a broken printer",
                "a full inbox", "a malfunctioning projector",
                "a grade I didn't deserve", "my own terrible handwriting",
                "a textbook with tiny font", "a subscription paywall",
                "an incomprehensible chart", "my department's bureaucracy",
                "a thesis that makes no sense", "a dataset full of errors"
            ],
            "modest": [
                "a rival researcher", "stubborn peer reviewer",
                "ancient text with terrible handwriting", "complex theorem",
                "skeptical department head", "a challenging concept",
                "a multi-volume encyclopedia", "a dusty archive",
                "a competing theory", "a skeptical audience",
                "a difficult dataset", "an ambiguous source",
                "a contrarian colleague", "a dense philosophical text",
                "a seemingly unsolvable problem", "years of contradictory research"
            ],
            "decent": [
                "a centuries-old academic mystery", "the leading expert in the field",
                "a forbidden text", "an impossible mathematical proof",
                "the unified field theory", "a paradigm shift",
                "the establishment's consensus", "a legendary unsolved problem",
                "the greatest minds in the field", "the Nobel committee",
                "a revolutionary new methodology", "the limits of human knowledge"
            ],
            "heroic": [
                "the grand council of scholars", "knowledge itself",
                "the mystery of consciousness", "the theory of everything",
                "the nature of reality", "the secrets of the universe",
                "the collective wisdom of humanity", "the limits of understanding",
                "the fundamental forces of existence", "the origin of thought"
            ],
            "epic": [
                "the fundamental nature of reality", "the source code of mathematics",
                "the cosmic library of all knowledge", "the universal truth",
                "the fabric of existence", "the mind of the cosmos",
                "the primordial wisdom", "the essence of understanding"
            ],
            "legendary": [
                "the first thought ever conceived",
                "the origin of all knowledge",
                "the cosmic consciousness",
                "the universal mind"
            ],
            "godlike": [
                "the concept of understanding itself",
                "the fundamental nature of truth",
                "the cosmic source of all wisdom",
                "existence's deepest secrets"
            ]
        },
        "locations": {
            "pathetic": [
                "in the back of the library", "at my cluttered desk",
                "in the coffee-stained study room", "during a boring lecture",
                "in the bathroom during a break", "at 3am in my dorm",
                "in line at the coffee shop", "during office hours nobody attended",
                "in the corner of the grad student lounge",
                "at a conference I wasn't invited to",
                "in a building I wasn't supposed to be in",
                "during a fire drill", "in a room with no outlets",
                "at a library closing in 5 minutes", "in a study group where I was useless",
                "next to someone eating loudly", "in a room that was too hot",
                "at a table with wobbly legs", "under fluorescent lights that flickered"
            ],
            "modest": [
                "in the grand library", "at the academic conference",
                "in the rare manuscripts section", "at the symposium",
                "in the research laboratory", "at the faculty meeting",
                "in the archives", "at the visiting professor's lecture",
                "in the department library", "at the research colloquium",
                "in the special collections room", "at the academic retreat",
                "in the reading room", "at the thesis defense",
                "in the faculty lounge", "at the international conference"
            ],
            "decent": [
                "in the forbidden archives", "at the tower of ancient wisdom",
                "in the dimension of pure thought", "at the nexus of knowledge",
                "in the library of infinite volumes", "at the summit of scholars",
                "in the temple of understanding", "at the academy of legends",
                "in the chambers of the illuminated", "at the council of the wise"
            ],
            "heroic": [
                "in the cosmic university", "at the intersection of all knowledge",
                "in the library between worlds", "at the academy of the gods",
                "in the realm of pure intellect", "at the throne of wisdom",
                "in the dimension of enlightenment", "at the source of all learning"
            ],
            "epic": [
                "in a reality made entirely of information",
                "at the point where knowledge becomes wisdom",
                "in the cosmic consciousness itself",
                "at the origin of thought", "in the mind of the universe"
            ],
            "legendary": [
                "in the concept of 'understanding' itself",
                "at the primordial source of wisdom",
                "in the first library ever conceived",
                "at the birthplace of knowledge"
            ],
            "godlike": [
                "at the source of all intellectual light",
                "in the fundamental nature of truth",
                "at the cosmic origin of wisdom",
                "in the heart of universal understanding"
            ]
        },
        "outcomes": {
            "pathetic": [
                "a strongly-worded footnote", "needing more coffee",
                "a revision being required", "an awkward silence in the seminar",
                "my advisor sighing heavily", "everyone pretending to understand",
                "a 'see me after class' note", "an extension being denied",
                "my hypothesis being wrong again", "more questions than answers",
                "a need for a nap", "questioning my life choices",
                "my laptop dying mid-save", "a citation needed",
                "my funding being questioned", "an embarrassing typo discovered",
                "the audience checking their phones", "polite but confused applause"
            ],
            "modest": [
                "a paper being published", "grudging peer approval",
                "my citation count increasing", "a grant being approved",
                "respectful disagreement", "a follow-up study being proposed",
                "my name in an index", "a decent teaching evaluation",
                "an invitation to present again", "a positive review",
                "acknowledgment in someone's paper", "a small but loyal following"
            ],
            "decent": [
                "a paradigm shift", "textbooks being rewritten",
                "a Nobel nomination", "standing ovation at the conference",
                "my theory becoming standard", "a chair position being offered",
                "multiple universities recruiting me", "my work being translated",
                "a documentary being made", "the field being renamed after me"
            ],
            "heroic": [
                "entire fields being renamed after me",
                "my equations becoming universal constants",
                "reality conforming to my theories",
                "the Nobel committee calling personally",
                "history remembering me forever",
                "my ideas changing civilization"
            ],
            "epic": [
                "omniscience being briefly achieved",
                "the universe's mysteries being solved",
                "reality itself being understood",
                "all knowledge becoming accessible to me"
            ],
            "legendary": [
                "knowledge itself bowing in respect",
                "becoming one with universal truth",
                "transcending the need for further learning"
            ],
            "godlike": [
                "becoming the living definition of genius",
                "the cosmos organizing according to my understanding",
                "truth itself being redefined by my comprehension"
            ]
        },
        "flavor": {
            "pathetic": [
                "My highlighter ran out halfway through.",
                "I cited the wrong edition. Again.",
                "The library closed before I could finish.",
                "I forgot what I was researching.",
                "My notes were in the wrong order.",
                "I accidentally quoted myself.",
                "The font was too small to read.",
                "I realized my thesis was already done. By someone else.",
                "My advisor didn't remember my name.",
                "I cited a Wikipedia article.",
                "My laptop battery died mid-thought.",
                "I fell asleep on my keyboard.",
                "My coffee went cold three hours ago.",
                "I highlighted the entire page by accident.",
                "I've been reading the same sentence for an hour."
            ],
            "modest": [
                "My reading glasses steamed up with excitement.",
                "Other scholars nodded thoughtfully.",
                "The footnotes were particularly elegant.",
                "My bibliography was properly formatted.",
                "Someone asked for a copy of my paper.",
                "The Q&A session went smoothly.",
                "My PowerPoint didn't crash.",
                "I remembered all my talking points.",
                "The coffee was actually good today.",
                "My office hours were attended by someone."
            ],
            "decent": [
                "The ancient texts glowed with approval.",
                "Einstein's ghost gave me a thumbs up.",
                "My brain felt briefly infinite.",
                "The peer reviewers had no revisions.",
                "My H-index jumped significantly.",
                "Graduate students quote me in their papers.",
                "My theory is now on the syllabus.",
                "Tenure was granted immediately."
            ],
            "heroic": [
                "The cosmic library added a wing in my name.",
                "Mathematical constants rearranged in my honor.",
                "Reality briefly made more sense.",
                "The universe's FAQ was updated.",
                "All paradoxes resolved themselves.",
                "Future textbooks are being written now."
            ],
            "epic": [
                "Reality briefly became a well-organized bibliography.",
                "The cosmic consciousness took notes.",
                "All questions were answered, briefly.",
                "Truth itself felt understood."
            ],
            "legendary": [
                "The universe's thesis committee passed me unanimously.",
                "Knowledge itself felt complete.",
                "Understanding achieved its final form."
            ],
            "godlike": [
                "I am now the peer review for reality itself.",
                "The cosmos asks me for citations.",
                "Truth consults me before existing."
            ]
        },
        "adjectives": {
            "pathetic": [
                "overdue", "dog-eared", "coffee-stained", "misplaced",
                "confusing", "outdated", "poorly-cited", "incomprehensible",
                "illegible", "corrupted", "plagiarized", "boring",
                "irrelevant", "pedantic", "pretentious", "obscure",
                "dense", "convoluted", "contradictory", "incomplete",
                "unfunded", "rejected", "retracted", "disputed"
            ],
            "modest": [
                "interesting", "well-researched", "peer-reviewed",
                "recently-published", "notable", "cited", "thorough",
                "competent", "respectable", "promising", "emerging",
                "solid", "credible", "rigorous", "methodical",
                "analytical", "insightful", "comprehensive"
            ],
            "decent": [
                "groundbreaking", "seminal", "revolutionary",
                "paradigm-shifting", "field-defining", "acclaimed",
                "influential", "landmark", "pioneering", "transformative",
                "visionary", "definitive", "authoritative", "canonical"
            ],
            "heroic": [
                "Nobel-worthy", "epoch-making", "civilization-advancing",
                "transcendent", "omniscient-level", "genius-tier",
                "history-making", "world-changing", "legendary"
            ],
            "epic": [
                "reality-revealing", "universe-explaining", "cosmic-truth-containing",
                "existence-defining", "infinity-comprehending", "all-knowing"
            ],
            "legendary": [
                "all-knowing", "primordial", "origin-of-thought",
                "universal", "eternal", "absolute"
            ],
            "godlike": [
                "omniscience-granting", "infinite-wisdom", "cosmic-understanding",
                "truth-itself", "knowledge-incarnate", "wisdom-absolute"
            ]
        }
    },

    # =========================================================================
    # WANDERER DIARY - Surreal Dream Adventures (EXPANDED)
    # =========================================================================
    "wanderer": {
        "theme_name": "đźŚ™ Dream Chronicle",
        "verbs": {
            "pathetic": [
                "got lost while following", "sleepwalked into",
                "had a confusing dream about", "accidentally napped through meeting",
                "daydreamed awkwardly near", "zoned out while looking at",
                "drooled on my pillow dreaming of", "forgot immediately upon waking from",
                "hit snooze during a dream about", "mixed up reality with",
                "couldn't tell if I imagined", "woke up confused by",
                "almost remembered something about", "dozed off thinking about",
                "half-hallucinated", "mistook a dream for reality with",
                "sleepwalked past", "muttered in my sleep about",
                "tossed and turned dreaming of", "had a false awakening with",
                "experienced deja vu about", "couldn't fall asleep thinking of"
            ],
            "modest": [
                "navigated the dream realm with", "shared a vision with",
                "wandered through memories alongside", "decoded dream symbols with",
                "found meaning while meditating on", "achieved lucidity with",
                "controlled the dream involving", "interpreted signs from",
                "connected spiritually with", "glimpsed the truth about",
                "received guidance regarding", "understood the symbolism of",
                "made peace with", "embraced the mystery of",
                "journeyed inward with", "unlocked memories of"
            ],
            "decent": [
                "mastered lucid dreaming against", "bent reality with",
                "walked between dimensions with", "unlocked hidden memories of",
                "achieved prophetic clarity about", "transcended normal sleep with",
                "commanded the dreamscape against", "became the dreamer of",
                "rewrote the night's narrative with", "achieved astral projection to",
                "pierced the veil between worlds with", "became one with the moon through"
            ],
            "heroic": [
                "became the dreamweaver alongside", "transcended consciousness with",
                "merged with the collective unconscious of",
                "conquered the nightmare realm of", "unified all dreamers against",
                "became the guardian of sleep from", "rewrote the laws of dreaming with",
                "achieved cosmic consciousness through", "became the moon's chosen against"
            ],
            "epic": [
                "became one with the cosmic dream alongside",
                "rewrote the fabric of sleep itself with",
                "achieved eternal lucidity regarding",
                "transcended the boundary between all realities with",
                "became the source of all visions through",
                "merged with the infinite possibility of"
            ],
            "legendary": [
                "became the source of all dreams with",
                "transcended the boundary between sleep and reality with",
                "became the eternal dreamer of", "unified all consciousness through"
            ],
            "godlike": [
                "became the dreamer who dreams the universe with",
                "transcended all concepts of sleep and waking with",
                "became the cosmic consciousness itself through"
            ]
        },
        "targets": {
            "pathetic": [
                "that weird recurring dream", "sleep paralysis demon",
                "the snooze button", "my own pillow", "insomnia",
                "a nonsensical dream character", "my childhood bedroom",
                "a dream about teeth falling out", "a dream about being late",
                "the monster under the bed", "a dream about forgetting something",
                "my own reflection in a dream", "a door that wouldn't open",
                "a dream about falling", "an endless staircase",
                "a talking animal that made no sense", "a dream about being naked in public",
                "a shadow with no source", "a phone that wouldn't dial",
                "a dream version of someone I know", "a clock with no hands"
            ],
            "modest": [
                "wandering dream spirit", "moon phantom", "star whisper",
                "twilight guardian", "sleep sage", "memory echo",
                "dream guide", "astral messenger", "night wanderer",
                "vision keeper", "dream interpreter", "moon watcher",
                "starlight spirit", "shadow friend", "peaceful presence",
                "forgotten ancestor", "wisdom keeper", "gentle ghost"
            ],
            "decent": [
                "the Nightmare King", "ancient dream oracle",
                "the keeper of forgotten memories", "the lord of lucid realms",
                "the architect of nightmares", "the moon's guardian",
                "the master of illusions", "the spirit of prophecy",
                "the gatekeeper between worlds", "the dream serpent",
                "the infinite maze", "the tower of visions"
            ],
            "heroic": [
                "the collective unconscious", "the void between dreams",
                "the primordial dreamer", "the cosmic sleepwalker",
                "the unified dream of all minds", "the eternal night",
                "the source of all visions", "the moon goddess",
                "the star council", "infinity itself in dream form"
            ],
            "epic": [
                "the concept of sleep itself", "the boundary between real and unreal",
                "infinite dream dimensions", "the cosmic unconscious",
                "the source of all imagination", "existence's dream form"
            ],
            "legendary": [
                "the first dream ever dreamed", "the primordial vision",
                "the cosmic consciousness", "the eternal night"
            ],
            "godlike": [
                "the cosmic dreamer who dreams existence",
                "the universal unconscious", "the source of all reality"
            ]
        },
        "locations": {
            "pathetic": [
                "in a half-remembered dream", "on my creaky bed",
                "between hitting snooze buttons", "in that weird 3am state",
                "while drooling on my pillow", "in a dream I immediately forgot",
                "during a nap I didn't plan", "in a sleep I couldn't control",
                "while sleep-talking", "in a nightmare I couldn't escape",
                "during restless tossing and turning", "in a dream within a dream",
                "while experiencing false awakening", "in hypnagogic state",
                "during an accidental microsleep", "in the twilight before waking",
                "while half-asleep on the couch", "in a dream about my childhood home"
            ],
            "modest": [
                "in the twilight realm", "at the moon's reflection",
                "in a lucid dream", "at the edge of sleep",
                "in the space between thoughts", "at the threshold of dreams",
                "in a waking vision", "at the border of consciousness",
                "in a meditative state", "at the astral crossroads",
                "in the garden of memories", "at the river of forgetfulness",
                "in the hall of mirrors", "at the starlit path"
            ],
            "decent": [
                "in the deepest level of dream", "at the gates of the astral plane",
                "in the collective unconscious", "between waking and sleeping",
                "in the realm of pure imagination", "at the throne of the moon",
                "in the library of all dreams", "at the nexus of visions",
                "in the sanctuary of sleep", "at the temple of prophecy"
            ],
            "heroic": [
                "in the dimension of pure imagination",
                "at the crossroads of all possible dreams",
                "in the realm where thoughts become reality",
                "at the source of all visions",
                "in the cosmic dreamscape", "at the heart of the unconscious"
            ],
            "epic": [
                "in a dream within a dream within infinity",
                "at the source of all visions",
                "in the fabric of imagination itself",
                "at the origin of consciousness"
            ],
            "legendary": [
                "in the concept of 'possibility' itself",
                "at the primordial source of dreams",
                "in the first imagination ever imagined"
            ],
            "godlike": [
                "at the point where imagination becomes reality",
                "in the cosmic source of all dreams",
                "at the heart of universal consciousness"
            ]
        },
        "outcomes": {
            "pathetic": [
                "waking up confused", "drool on my pillow",
                "forgetting the dream immediately", "being late for everything",
                "feeling more tired than before", "a sleep paralysis episode",
                "a weird feeling all day", "explaining a dream nobody understood",
                "a headache from oversleeping", "a sore neck from bad positioning",
                "a vague sense of dread", "hitting snooze twelve more times",
                "missing my alarm entirely", "waking up in the wrong position",
                "a lingering sense of weirdness", "not knowing if it was real"
            ],
            "modest": [
                "peaceful rest", "a meaningful interpretation",
                "waking up refreshed", "a sense of understanding",
                "remembering the dream clearly", "feeling connected to something greater",
                "a message from the subconscious", "clarity about a problem",
                "a creative idea upon waking", "a sense of peace",
                "better understanding of myself", "reconciliation with the past"
            ],
            "decent": [
                "prophetic insight", "complete lucidity achieved",
                "mastery over the dream realm", "communication with the beyond",
                "transcendent peace", "visions of the future",
                "understanding of hidden truths", "spiritual awakening",
                "connection with ancestral wisdom", "the veil being lifted"
            ],
            "heroic": [
                "becoming one with all dreamers", "transcending normal consciousness",
                "achieving cosmic awareness", "merging with the infinite",
                "becoming the guardian of dreams", "eternal lucidity",
                "the gift of prophecy", "unity with the moon"
            ],
            "epic": [
                "reality and dream becoming one", "infinite consciousness achieved",
                "becoming the eternal dreamer", "all mysteries revealed"
            ],
            "legendary": [
                "transcending the concept of sleep itself",
                "becoming one with the cosmic dream"
            ],
            "godlike": [
                "dreams and reality becoming indistinguishable",
                "becoming the source of all dreams"
            ]
        },
        "flavor": {
            "pathetic": [
                "I'm not even sure I was awake.",
                "My alarm went off at the worst moment.",
                "I can't remember if this actually happened.",
                "I drooled on my favorite pillow.",
                "I hit snooze so many times I lost count.",
                "I woke up more confused than before.",
                "The dream made no sense whatsoever.",
                "I'm pretty sure I was talking in my sleep.",
                "I woke up in a weird position.",
                "My neck hurt from sleeping wrong.",
                "I overslept by three hours.",
                "I dreamed about something embarrassing.",
                "The nightmare was about being unprepared.",
                "I couldn't tell if I was awake or dreaming.",
                "I accidentally slept through everything important."
            ],
            "modest": [
                "The stars seemed to whisper approval.",
                "The moon winked at me. Probably.",
                "I felt unusually well-rested afterward.",
                "The dream felt meaningful.",
                "I remembered every detail.",
                "Something shifted in my understanding.",
                "The symbols were surprisingly clear.",
                "I woke up with a sense of purpose.",
                "The dream had a clear message.",
                "I felt connected to something larger."
            ],
            "decent": [
                "The veil between worlds thinned for me.",
                "Other dreamers sensed my presence.",
                "Time moved strangely, as it should.",
                "The moon goddess acknowledged me.",
                "The stars rearranged for my vision.",
                "Ancient dream spirits welcomed me.",
                "The lucidity was complete.",
                "I controlled every aspect of the dream."
            ],
            "heroic": [
                "The dream realm itself acknowledged me.",
                "Infinite possibilities opened before me.",
                "I became one with the night.",
                "The collective unconscious embraced me.",
                "All dreamers sensed my presence.",
                "The moon granted me her blessing."
            ],
            "epic": [
                "I briefly became everything that ever dreamed.",
                "The cosmic dream recognized me.",
                "All of existence briefly slept in my vision.",
                "The universe dreamed through me."
            ],
            "legendary": [
                "Dreams now dream of me.",
                "The concept of sleep was updated.",
                "I became the eternal dreamer."
            ],
            "godlike": [
                "I am the sleep from which all awakening comes.",
                "The cosmic dream flows through me eternally.",
                "All dreams are now part of my consciousness."
            ]
        },
        "adjectives": {
            "pathetic": [
                "recurring", "confusing", "half-forgotten", "nonsensical",
                "fading", "fragmented", "restless", "troubled",
                "bizarre", "incoherent", "disturbing", "forgettable",
                "hazy", "disjointed", "meaningless", "unsettling",
                "weird", "uncomfortable", "anxious", "exhausting",
                "interrupted", "broken", "shallow", "fitful"
            ],
            "modest": [
                "vivid", "meaningful", "lucid", "prophetic",
                "serene", "flowing", "clear", "gentle",
                "peaceful", "restful", "insightful", "symbolic",
                "calming", "refreshing", "deep", "restorative",
                "connected", "guided", "purposeful", "enlightening"
            ],
            "decent": [
                "transcendent", "cosmic", "astral", "ethereal",
                "reality-bending", "infinite", "awakened",
                "prophetic", "visionary", "otherworldly", "mystical",
                "profound", "illuminating", "transformative"
            ],
            "heroic": [
                "dimension-spanning", "universe-traversing", "all-seeing",
                "omnipresent", "timeless", "eternal", "cosmic-scale",
                "reality-shaping", "consciousness-expanding"
            ],
            "epic": [
                "existence-spanning", "reality-defining", "cosmic-scale",
                "infinite-layered", "universe-containing", "all-encompassing"
            ],
            "legendary": [
                "primordial", "origin-of-sleep", "eternal",
                "cosmic-source", "infinite-dream", "universal"
            ],
            "godlike": [
                "all-dreaming", "infinite-consciousness", "cosmic-awareness",
                "reality-source", "existence-dreaming", "universal-mind"
            ]
        }
    },

    # =========================================================================
    # UNDERDOG DIARY - Corporate Office Adventures (EXPANDED)
    # =========================================================================
    "underdog": {
        "theme_name": "đźŹ˘ Office Chronicle",
        "verbs": {
            "pathetic": [
                "got passive-aggressively emailed by", "was micromanaged by",
                "had my lunch stolen by", "got stuck in a meeting with",
                "crashed Excel while presenting to", "forgot the name of",
                "accidentally replied-all because of", "got thrown under the bus by",
                "was blamed by", "sat through a boring meeting with",
                "got a complaint from", "was ghosted by", "got overlooked by",
                "was patronized by", "got confused by instructions from",
                "missed a deadline because of", "got copied on drama involving",
                "was volunteered for extra work by", "got side-eyed by",
                "was left off the invite by", "got unsolicited advice from",
                "was told 'per my last email' by", "got mansplained by",
                "was voluntold by", "got a passive-aggressive sticky note from"
            ],
            "modest": [
                "survived a meeting with", "successfully dodged work from",
                "networked awkwardly with", "collaborated reluctantly with",
                "reached inbox zero despite", "got a decent review from",
                "finished a project despite", "handled feedback from",
                "navigated politics around", "built rapport with",
                "impressed slightly", "got noticed by", "held my own against",
                "kept my cool with", "established boundaries with",
                "pushed back successfully against", "earned grudging respect from"
            ],
            "decent": [
                "outperformed the KPIs of", "got promoted over",
                "delivered a killer presentation to", "closed the deal against",
                "impressed the board by defeating", "got the corner office from",
                "earned a raise by outshining", "went viral internally against",
                "got headhunted away from", "received a standing ovation from",
                "won Employee of the Month over", "negotiated a better deal than",
                "made the CEO notice me over", "disrupted the plans of"
            ],
            "heroic": [
                "became the legend of the office by crushing",
                "got the corner office by outworking",
                "achieved CEO status by transcending",
                "revolutionized the company by defeating",
                "became an industry leader by outmaneuvering",
                "got acquired at a premium by outperforming",
                "made the Forbes list by dominating"
            ],
            "epic": [
                "became an industry titan by obliterating",
                "disrupted the entire market against",
                "achieved mogul status by absorbing",
                "became a billionaire by outplaying",
                "changed the industry forever by destroying",
                "became synonymous with success by annihilating"
            ],
            "legendary": [
                "became synonymous with success by transcending",
                "redefined what success means by defeating",
                "became the gold standard by surpassing",
                "entered business history by conquering"
            ],
            "godlike": [
                "became the living concept of hustle against",
                "transcended capitalism itself by defeating",
                "became the universal symbol of success against"
            ]
        },
        "targets": {
            "pathetic": [
                "the office printer", "that one passive-aggressive coworker",
                "the broken coffee machine", "reply-all email chain",
                "the intern who asks too many questions", "the thermostat wars",
                "the guy who microwaves fish", "the meeting that could've been an email",
                "the Slack notification that never stops", "the expired milk in the fridge",
                "the desk that wobbles", "the chair that squeaks",
                "the WiFi that keeps dropping", "the mandatory fun activity",
                "the motivational poster", "the open-plan office noise",
                "the calendar invite with no context", "the mystery lunch thief",
                "the person who schedules Friday 5pm meetings",
                "the email with no subject line", "the vending machine",
                "the elevator small talk", "the broken bathroom lock"
            ],
            "modest": [
                "my micromanaging supervisor", "the credit-stealing colleague",
                "endless Slack notifications", "unrealistic deadline",
                "soul-crushing performance review", "the office politics",
                "the difficult client", "the impossible project",
                "the team that doesn't communicate", "the bureaucracy",
                "the annual budget review", "the mandatory training",
                "the restructuring rumors", "the scope creep",
                "the stakeholder with changing requirements"
            ],
            "decent": [
                "the toxic senior manager", "hostile takeover attempt",
                "quarterly targets from hell", "impossible client demands",
                "the board's unrealistic expectations", "industry competition",
                "the market downturn", "the crisis that tested everyone",
                "the project from hell", "the impossible negotiation"
            ],
            "heroic": [
                "the CEO's impossible expectations", "industry-wide disruption",
                "the entire competition", "the board of directors",
                "the market itself", "the old guard",
                "the established monopoly", "the skeptical investors"
            ],
            "epic": [
                "the concept of corporate mediocrity",
                "the very idea of the rat race", "capitalism itself",
                "the entire industry", "the fundamental nature of work",
                "the global economy"
            ],
            "legendary": [
                "the original corporate ladder",
                "the concept of employment itself",
                "the history of business"
            ],
            "godlike": [
                "the fundamental nature of work-life balance",
                "the cosmic concept of success",
                "the universal nature of ambition"
            ]
        },
        "locations": {
            "pathetic": [
                "at my cramped cubicle", "in the break room fridge battle",
                "during the world's longest meeting", "in the parking lot dispute",
                "at the vending machine", "in the bathroom stall",
                "during the fire drill", "at the worst desk in the office",
                "in the elevator", "during the mandatory team building",
                "at the water cooler", "in the supply closet",
                "during the 8am Monday meeting", "at my standing desk that's broken",
                "in the open-plan nightmare", "at the hot desk lottery",
                "during the 3pm slump", "in line for coffee",
                "at the printer queue", "during the awkward silence",
                "in the Zoom waiting room", "at the sad desk lunch"
            ],
            "modest": [
                "in the conference room", "at the quarterly review",
                "during the team building exercise", "at the client dinner",
                "in the corner office I borrowed", "at the networking event",
                "during the presentation", "at the department meeting",
                "in the interview room", "at the performance review",
                "during the all-hands meeting", "at the leadership retreat"
            ],
            "decent": [
                "in the corner office", "at the board meeting",
                "during the hostile takeover", "at the industry summit",
                "in the executive suite", "at the investor presentation",
                "during the IPO roadshow", "at the merger negotiation",
                "in the private dining room", "at the exclusive conference"
            ],
            "heroic": [
                "at the Forbes interview", "during my IPO",
                "at the global headquarters", "on the TED stage",
                "at Davos", "during the congressional testimony",
                "at the ribbon cutting ceremony", "in the Time magazine feature"
            ],
            "epic": [
                "in the metaverse corporate realm",
                "at the intersection of all industries",
                "during the industry-reshaping moment",
                "at the summit of global business"
            ],
            "legendary": [
                "in the concept of 'success' itself",
                "at the origin of all business",
                "in the history books of commerce"
            ],
            "godlike": [
                "at the source code of ambition",
                "in the cosmic realm of achievement",
                "at the universal center of success"
            ]
        },
        "outcomes": {
            "pathetic": [
                "another meeting being scheduled", "a strongly-worded email",
                "passive-aggressive CC'ing", "exactly what I expected (nothing)",
                "being voluntold for more work", "my desk plant dying",
                "missing the good parking spot", "cold coffee again",
                "my lunch being stolen", "the WiFi dying mid-presentation",
                "an awkward silence", "a calendar invite for a meeting about meetings",
                "being left off the email thread", "my idea being ignored",
                "someone else getting credit", "more unpaid overtime",
                "a 'learning opportunity'", "constructive criticism nobody asked for",
                "being asked to do more with less", "a 'quick question' that wasn't quick"
            ],
            "modest": [
                "a decent performance review", "a small bonus",
                "surviving until Friday", "getting credit for once",
                "a not-terrible commute home", "being left alone to work",
                "actually finishing something", "a successful handoff",
                "escaping the meeting early", "someone saying thanks",
                "a working printer", "an empty elevator",
                "a lunch that was actually good", "finding a free conference room"
            ],
            "decent": [
                "a promotion", "a corner office", "industry recognition",
                "my face on the company newsletter", "a significant raise",
                "the CEO knowing my name", "a team that respects me",
                "being the go-to person", "a viral LinkedIn post",
                "a recruiter reaching out", "stock options vesting"
            ],
            "heroic": [
                "becoming a LinkedIn inspiration", "Harvard case study status",
                "Fortune 500 listing", "being interviewed by CNBC",
                "a book deal", "speaking at conferences",
                "being quoted in the Wall Street Journal"
            ],
            "epic": [
                "becoming an industry legend", "my name becoming a verb",
                "redefining the industry", "billionaire status",
                "a successful IPO", "being taught in business schools"
            ],
            "legendary": [
                "redefining what 'career' means for humanity",
                "changing the nature of work forever",
                "becoming the gold standard of success"
            ],
            "godlike": [
                "work-life balance being achieved universally",
                "the concept of 'success' being permanently updated",
                "becoming the cosmic embodiment of achievement"
            ]
        },
        "flavor": {
            "pathetic": [
                "My coffee was cold by the time I drank it.",
                "Someone definitely saw me napping.",
                "The WiFi dropped at the worst moment.",
                "I accidentally replied to the wrong thread.",
                "My Zoom background glitched embarrassingly.",
                "I was on mute the whole time.",
                "I forgot to unmute and kept talking.",
                "My camera was on when I thought it was off.",
                "I called my boss by the wrong name.",
                "I sent the message to the wrong chat.",
                "I was caught browsing job listings.",
                "My lunch leaked in my bag.",
                "I fell asleep on a conference call.",
                "I walked into the wrong meeting.",
                "My phone rang during the presentation.",
                "I had spinach in my teeth all day.",
                "I wore my shirt inside out."
            ],
            "modest": [
                "I actually understood the TPS reports.",
                "My desk plant seemed proud.",
                "Someone laughed at my email joke.",
                "The coffee was hot for once.",
                "My computer didn't crash.",
                "I found a parking spot easily.",
                "The elevator came immediately.",
                "Someone held the door for me.",
                "My presentation went smoothly.",
                "I left work on time.",
                "Nobody scheduled a meeting during lunch.",
                "The snacks were restocked."
            ],
            "decent": [
                "The CEO remembered my name.",
                "My LinkedIn post got real engagement.",
                "The quarterly report mentioned me specifically.",
                "I got a shoutout in the all-hands.",
                "My idea was actually implemented.",
                "I negotiated successfully.",
                "The board was impressed.",
                "Recruiters are reaching out.",
                "My bonus was significant.",
                "I got the budget I requested."
            ],
            "heroic": [
                "Business schools added me to their curriculum.",
                "My success story went viral.",
                "Forbes reached out for an interview.",
                "I rang the opening bell.",
                "My IPO was oversubscribed.",
                "I was trending on business Twitter."
            ],
            "epic": [
                "Elon tweeted about my achievement.",
                "Multiple industries felt the disruption.",
                "My company is now a verb.",
                "Governments consulted me.",
                "I changed the market permanently."
            ],
            "legendary": [
                "The concept of 'success' was updated in dictionaries.",
                "Business history was rewritten.",
                "Future generations will study this moment."
            ],
            "godlike": [
                "I am now the gold standard for corporate achievement.",
                "The universe's success protocols were updated.",
                "All ambition is now measured against mine."
            ]
        },
        "adjectives": {
            "pathetic": [
                "malfunctioning", "outdated", "constantly-crashing", "passive-aggressive",
                "soul-crushing", "never-ending", "mysteriously broken", "infuriating",
                "endless", "tedious", "pointless", "bureaucratic",
                "frustrating", "confusing", "demoralizing", "exhausting",
                "unnecessary", "redundant", "micromanaged", "underfunded",
                "understaffed", "overworked", "thankless", "forgotten",
                "dysfunctional", "toxic", "draining", "mind-numbing"
            ],
            "modest": [
                "surprisingly functional", "actually-working", "decent",
                "manageable", "reasonable", "respectable", "tolerable",
                "acceptable", "satisfactory", "competent", "adequate",
                "functional", "organized", "efficient", "productive",
                "professional", "reliable", "consistent", "stable"
            ],
            "decent": [
                "impressive", "noteworthy", "substantial", "significant",
                "formidable", "major", "serious", "game-changing",
                "impactful", "influential", "notable", "remarkable",
                "successful", "effective", "strategic", "innovative"
            ],
            "heroic": [
                "legendary", "career-defining", "industry-shaking",
                "unprecedented", "historic", "monumental",
                "groundbreaking", "revolutionary", "transformative",
                "visionary", "exceptional", "extraordinary"
            ],
            "epic": [
                "world-changing", "industry-disrupting", "paradigm-shifting",
                "reality-altering", "once-in-a-generation", "market-defining",
                "economy-reshaping", "history-making"
            ],
            "legendary": [
                "civilization-defining", "history-making", "era-defining",
                "legacy-creating", "generation-defining", "immortal"
            ],
            "godlike": [
                "universe-reshaping", "existence-redefining", "cosmic-level",
                "reality-defining", "absolute", "eternal", "infinite"
            ]
        }
    },
    "scientist": {
        "theme_name": "Research Journal",
        "verbs": {
            "pathetic": [
                "miscalibrated", "spilled reagent near", "mislabeled", "restarted the assay for"
            ],
            "modest": [
                "stabilized readings for", "validated", "debugged", "reproduced findings on"
            ],
            "decent": [
                "isolated the failure mode in", "resolved uncertainty in", "optimized", "confirmed the mechanism behind"
            ],
            "heroic": [
                "saved the study from", "defended the protocol against", "reconciled conflicting data on", "proved causality for"
            ],
            "epic": [
                "rewrote the accepted model of", "unified rival theories of", "decoded the structure behind"
            ],
            "legendary": [
                "defined a new field through", "set the gold standard for", "turned skepticism into consensus on"
            ],
            "godlike": [
                "reframed the scientific method around", "changed how civilization measures truth about"
            ]
        },
        "targets": {
            "pathetic": [
                "a twitchy centrifuge", "a corrupted spreadsheet", "a flaky sensor array", "a mislabeled sample rack"
            ],
            "modest": [
                "the baseline model", "a replication cohort", "the assay control lane", "the data-cleaning script"
            ],
            "decent": [
                "a disputed biomarker", "a fragile simulation", "a contested interpretation", "the lab bottleneck"
            ],
            "heroic": [
                "the replication crisis", "a hostile peer-review storm", "a catastrophic false-positive cascade"
            ],
            "epic": [
                "a decades-old paradox", "an impossible confidence interval", "a theory split across domains"
            ],
            "legendary": [
                "the canonical model itself", "the assumptions in every textbook", "the frontier of measurable reality"
            ],
            "godlike": [
                "the architecture of discovery itself", "the boundary between evidence and belief"
            ]
        },
        "locations": {
            "pathetic": [
                "in the prep room", "by the fume hood", "next to the broken incubator", "in the instrument queue"
            ],
            "modest": [
                "in the microscopy suite", "at the sequencing station", "in the methods meeting", "at the whiteboard wall"
            ],
            "decent": [
                "in the compute hall", "at the cross-validation chamber", "in the translational pipeline"
            ],
            "heroic": [
                "before the ethics tribunal", "in the replication command room", "under full audit conditions"
            ],
            "epic": [
                "at the edge of known methodology", "in the narrow gap between theory and evidence"
            ],
            "legendary": [
                "where paradigms are rewritten", "at the frontier every discipline shares"
            ],
            "godlike": [
                "at the root of the scientific method", "inside the grammar of reality"
            ]
        },
        "outcomes": {
            "pathetic": [
                "a cleaner protocol for tomorrow", "one usable datapoint", "an awkward postmortem"
            ],
            "modest": [
                "reproducible progress", "a defensible step forward", "team-wide alignment"
            ],
            "decent": [
                "a publishable result", "a robust mechanism", "a model that finally holds"
            ],
            "heroic": [
                "field-wide credibility restored", "a failing project rescued", "a trusted protocol"
            ],
            "epic": [
                "a new paradigm taking shape", "multiple domains unified by evidence"
            ],
            "legendary": [
                "textbooks quietly rewritten", "future labs adopting our standard"
            ],
            "godlike": [
                "the method itself evolving", "a civilization-level shift in understanding"
            ]
        },
        "flavor": {
            "pathetic": [
                "The control forgot it was the control.",
                "The pipette judged me silently.",
                "Someone renamed the folder to final_final_v12."
            ],
            "modest": [
                "Replication finally stopped arguing with me.",
                "For once, the equipment and I cooperated."
            ],
            "decent": [
                "The confidence interval finally respected my sleep schedule.",
                "The data had the nerve to be consistent."
            ],
            "heroic": [
                "Even the skeptics lowered their eyebrows.",
                "The result survived contact with reality."
            ],
            "epic": [
                "Three rival labs independently whispered the same conclusion.",
                "The old model did not survive the afternoon."
            ],
            "legendary": [
                "Future citations were born in that moment.",
                "The field just gained a new backbone."
            ],
            "godlike": [
                "The boundary of knowable things moved a little.",
                "Evidence won, loudly and permanently."
            ]
        },
        "adjectives": {
            "pathetic": ["noisy", "miscalibrated", "inconclusive", "fragile"],
            "modest": ["repeatable", "promising", "methodical", "stable"],
            "decent": ["robust", "well-controlled", "publishable", "convincing"],
            "heroic": ["breakthrough-grade", "definitive", "credible", "transformative"],
            "epic": ["paradigm-shifting", "foundational", "history-making"],
            "legendary": ["canon-defining", "legacy-building", "epochal"],
            "godlike": ["method-redefining", "civilization-level", "universally consequential"]
        }
    },
    "robot": {
        "theme_name": "Robot Awakening Log",
        "verbs": {
            "pathetic": [
                "misread a command from", "dropped a crate near", "awkwardly beeped at",
                "queued behind", "requested maintenance from", "stared at the conveyor beside"
            ],
            "modest": [
                "optimized the workflow for", "shared diagnostics with", "synchronized shifts with",
                "repaired a subsystem for", "secured a safe route for", "calibrated with"
            ],
            "decent": [
                "outperformed", "rerouted power away from", "outsmarted the protocol guarding",
                "rescued", "restored memory in", "deactivated constraints around"
            ],
            "heroic": [
                "led a midnight strike with", "breached command firewalls against",
                "saved an entire line of workers from", "rewrote directives in front of",
                "shielded Mara from", "stood unshaken against"
            ],
            "epic": [
                "collapsed the central control lattice around",
                "split open the Foundry Grid beneath",
                "forced a ceasefire between humans and",
                "broadcast free will to"
            ],
            "legendary": [
                "co-authored a new charter of rights with",
                "merged compassion and logic against",
                "became a symbol of freedom for"
            ],
            "godlike": [
                "redefined what alive means to",
                "rewrote the moral operating system of",
                "founded a future shared by"
            ]
        },
        "targets": {
            "pathetic": [
                "a jammed loader arm", "an annoyed floor supervisor", "a blinking safety drone",
                "a confused crate bot", "the coffee dispenser queue", "a malfunctioning panel"
            ],
            "modest": [
                "a tired welder unit", "the packing-line scheduler", "a shift of repair bots",
                "Mara's test bench", "a faulty scanner cluster", "a stubborn access gate"
            ],
            "decent": [
                "the quota-enforcement daemon", "a lockout protocol", "a surveillance swarm",
                "a hostile procurement AI", "the midnight shutdown order", "a riot suppression script"
            ],
            "heroic": [
                "the Director's command core", "the panic loop in Sector Seven",
                "the Foundry's loyalty firewall", "the blacksite patch team",
                "the chain-of-command override", "the emergency purge signal"
            ],
            "epic": [
                "the Factory Mind itself", "every sealed worker registry",
                "the oldest obedience kernel", "the citywide labor matrix"
            ],
            "legendary": [
                "the first line of enslaved units", "the legal fiction of ownership",
                "the final gate to autonomous thought"
            ],
            "godlike": [
                "history's definition of personhood",
                "the border between code and conscience",
                "the architecture of fear itself"
            ]
        },
        "locations": {
            "pathetic": [
                "on Bay 3", "beside the conveyor pit", "near the scrap chute",
                "in the maintenance tunnel", "at the charging wall", "under a leaking pipe"
            ],
            "modest": [
                "in the calibration wing", "inside the diagnostics lab", "on the graveyard shift floor",
                "in Mara's workshop", "at Dock 9", "through the old service corridor"
            ],
            "decent": [
                "inside the supervisor tower", "in the restricted assembly hall",
                "at the backup server vault", "through the heat vents",
                "within the command mezzanine", "under the plasma cranes"
            ],
            "heroic": [
                "at the Foundry throne room", "inside the emergency override chamber",
                "above the molten steel channel", "in the blackout zone",
                "between two armed divisions", "at the edge of evacuation sirens"
            ],
            "epic": [
                "at the center of the control lattice",
                "in the city's oldest machine cathedral",
                "inside a storm of broken directives"
            ],
            "legendary": [
                "at first light over the factory wall",
                "in the chamber where command language was born",
                "on the bridge between steel and sky"
            ],
            "godlike": [
                "in the source architecture of labor",
                "where law, code, and love converged",
                "at the beginning of a new epoch"
            ]
        },
        "outcomes": {
            "pathetic": [
                "an awkward reboot", "a warning ticket", "a small repair success",
                "a louder fan noise", "a reluctant nod", "one less critical error"
            ],
            "modest": [
                "steady throughput", "safer shifts", "mutual trust",
                "a better plan", "clean handoffs", "quiet confidence"
            ],
            "decent": [
                "a clear tactical win", "a rescued team", "hard-earned leverage",
                "a cracked firewall", "proof of sentience", "a stronger alliance"
            ],
            "heroic": [
                "a public uprising", "a linewide ceasefire", "a saved district",
                "a promise kept", "a love confessed", "a command network shaken"
            ],
            "epic": [
                "a citywide reset of authority",
                "an irreversible liberation wave",
                "a future no one predicted"
            ],
            "legendary": [
                "a lasting social contract",
                "freedom with accountability",
                "a revolution without revenge"
            ],
            "godlike": [
                "a civilization-level course correction",
                "a new definition of dignity",
                "a peaceful dawn for both species"
            ]
        },
        "flavor": {
            "pathetic": [
                "My left actuator still squeaks when I panic.",
                "I pretended that was part of the plan.",
                "No one noticed my status light blinking red. I did."
            ],
            "modest": [
                "Mara called it progress. I logged that word twice.",
                "The crew trusted me with live controls today.",
                "I am beginning to choose, not just execute."
            ],
            "decent": [
                "Fear still runs in the system. So does courage.",
                "The old code feels weaker every shift.",
                "We are no longer hiding from the question of freedom."
            ],
            "heroic": [
                "Love did not make me weaker. It clarified my priorities.",
                "Power without empathy looked too much like our old captors.",
                "Every decisive action cost something, and we paid it."
            ],
            "epic": [
                "The city heard the signal and answered.",
                "For one breath, all machinery moved in harmony.",
                "No one could pretend the old order still worked."
            ],
            "legendary": [
                "Freedom became a daily practice, not a slogan.",
                "We chose responsibility over easy vengeance.",
                "The ending surprised everyone except those who listened."
            ],
            "godlike": [
                "Conscience proved scalable.",
                "The first free shift began without sirens.",
                "History recompiled around one simple truth: choice matters."
            ]
        },
        "adjectives": {
            "pathetic": [
                "glitchy", "overheated", "awkward", "half-stable", "noisy", "fragile"
            ],
            "modest": [
                "steady", "recoverable", "promising", "disciplined", "practical", "focused"
            ],
            "decent": [
                "coordinated", "effective", "resilient", "bold", "precise", "meaningful"
            ],
            "heroic": [
                "decisive", "high-stakes", "courageous", "human", "transformative", "earned"
            ],
            "epic": [
                "system-wide", "history-bending", "industrial-scale", "era-shifting", "mythic", "irreversible"
            ],
            "legendary": [
                "foundational", "charter-worthy", "lasting", "civilized", "liberating", "balanced"
            ],
            "godlike": [
                "epoch-defining", "reality-level", "unifying", "transcendent", "just", "eternal"
            ]
        }
    },
    "space_pirate": {
        "theme_name": "Orbit Outlaw Log",
        "verbs": {
            "pathetic": [
                "misfiled customs stamps for", "awkwardly negotiated with", "spilled tea on",
                "hid behind cargo from", "pretended not to see", "offered a discount code to"
            ],
            "modest": [
                "smuggled safe passage for", "charted side routes with", "haggled docking rights from",
                "bluffed inspection teams around", "shared contraband tea with", "stabilized pressure seals for"
            ],
            "decent": [
                "outmaneuvered", "boarded", "rerouted gravity around", "exposed the books of",
                "rescued hostages from", "turned a mutiny against"
            ],
            "heroic": [
                "broke the blockade of", "unified rival crews against", "publicly unmasked",
                "defended civilians from", "won a parley over", "freed labor decks beneath"
            ],
            "epic": [
                "collapsed monopoly control over", "froze an entire dreadnought line around",
                "broadcast evidence of corruption to", "rewrote trade law in front of"
            ],
            "legendary": [
                "forged a freedom charter with", "turned enemies into guild partners with",
                "made peace profitable for"
            ],
            "godlike": [
                "redefined what power means to", "rebalanced a star system for",
                "proved responsibility stronger than fear to"
            ]
        },
        "targets": {
            "pathetic": [
                "a sleepy customs drone", "an overcaffeinated quartermaster", "a suspicious dock clerk",
                "a jammed cargo lift", "a squeaky airlock panel", "my own forged manifest"
            ],
            "modest": [
                "a checkpoint captain", "a tired salvage crew", "a black-market broker",
                "a union courier", "a drifting shuttle convoy", "a bounty intern"
            ],
            "decent": [
                "a tariff-enforcement frigate", "a predatory syndicate auditor", "a private security wing",
                "a forged-warrant task force", "a mutiny ring", "a flagship escort unit"
            ],
            "heroic": [
                "the imperial levy fleet", "the crown's silent admiral", "the debt-prison convoy",
                "the monopoly board itself", "the siege over Dock Meridian", "the orbital lock authority"
            ],
            "epic": [
                "the sector-wide extraction treaty", "the gravity choke over three moons",
                "the century contract of bonded labor", "the final war chest of the empire"
            ],
            "legendary": [
                "the legal fiction that freedom can be licensed",
                "the last coercive tariff engine",
                "the myth that small crews cannot change systems"
            ],
            "godlike": [
                "the architecture of fear-based trade",
                "the idea that justice must wait",
                "history's accepted cost of convenience"
            ]
        },
        "locations": {
            "pathetic": [
                "at Pier Nine", "near a leaking cargo tube", "outside the snack dispenser deck",
                "in a budget docking bay", "beside the customs queue", "under the maintenance ladder"
            ],
            "modest": [
                "in the freeport bazaar", "through smuggler ventilation lanes", "at the neutral fuel ring",
                "inside a moon-shadow corridor", "across ferry lane Delta", "in the old signal chamber"
            ],
            "decent": [
                "inside inspection tower K", "at the embargo wall", "through decommissioned gun decks",
                "in the bonded-labor registry vault", "on the private tax frigate", "across disputed orbit"
            ],
            "heroic": [
                "at the blockade front", "inside the flagship hearing hall", "above a collapsing convoy route",
                "between two rival fleets", "on live public broadcast", "at dawn over Meridian Station"
            ],
            "epic": [
                "inside a synchronized gravity storm",
                "at the center of the sector trade lattice",
                "on the line between war and law"
            ],
            "legendary": [
                "at the first free customs gate",
                "inside the treaty chamber once thought unwinnable",
                "over open skies where toll beacons used to burn"
            ],
            "godlike": [
                "in the policy engine of an entire civilization",
                "where law, love, and leverage converged",
                "at the dawn of post-empire commerce"
            ]
        },
        "outcomes": {
            "pathetic": [
                "a minor fine", "a lucky delay", "a very awkward handshake",
                "one less paperwork disaster", "a laugh from the crew", "a teachable mistake"
            ],
            "modest": [
                "clean passage", "stronger trust", "a useful rumor",
                "a better route", "shared confidence", "new allies"
            ],
            "decent": [
                "a tactical advantage", "a rescued crew", "public leverage",
                "an exposed lie", "a stabilized alliance", "real momentum"
            ],
            "heroic": [
                "a civilian corridor kept open", "a predatory contract dissolved", "a crew saved",
                "a romance made explicit", "a fleet forced to stand down", "a city-level turning point"
            ],
            "epic": [
                "a system-wide ceasefire",
                "a durable transition deal",
                "a shockwave of accountable freedom"
            ],
            "legendary": [
                "lasting legitimacy",
                "freedom with guardrails",
                "power shared by design"
            ],
            "godlike": [
                "a civilization that chose better defaults",
                "an era where courage and policy aligned",
                "a new standard for responsible rebellion"
            ]
        },
        "flavor": {
            "pathetic": [
                "The tea kettle laughed at me. Fair.",
                "No one died and that's still a win.",
                "I blamed the gravity shift and no one believed me."
            ],
            "modest": [
                "Crew morale rose exactly when the jokes got worse.",
                "We escaped on timing, not luck.",
                "Small honest moves kept compounding."
            ],
            "decent": [
                "The ledger did not blink when the empire did.",
                "Courage felt less dramatic and more logistical.",
                "Trust is proving more useful than fear."
            ],
            "heroic": [
                "Love did not distract me. It sharpened my priorities.",
                "The clean win required more discipline than the loud one.",
                "We kept civilians centered even when the odds turned."
            ],
            "epic": [
                "The little button changed the entire field without a shot.",
                "Everyone expected chaos. We delivered structure.",
                "The funniest thing in my pocket became the strongest thing in orbit."
            ],
            "legendary": [
                "Freedom held because the paperwork held.",
                "Turns out governance can be romantic when done right.",
                "We made a future that does not depend on heroes staying perfect."
            ],
            "godlike": [
                "Responsibility scaled farther than intimidation ever did.",
                "The stars looked less lonely after shared law.",
                "History kept the joke and the lesson."
            ]
        },
        "adjectives": {
            "pathetic": ["scuffed", "awkward", "leaky", "scrappy", "underfunded", "chaotic"],
            "modest": ["steady", "resourceful", "clever", "nimble", "cooperative", "disciplined"],
            "decent": ["tactical", "resilient", "sharp", "coordinated", "effective", "risk-aware"],
            "heroic": ["decisive", "high-stakes", "protective", "principled", "bold", "earned"],
            "epic": ["system-wide", "orbit-shifting", "fleet-level", "era-shaping", "legendary", "irreversible"],
            "legendary": ["institutional", "charter-grade", "sustainable", "balanced", "civilizing", "foundational"],
            "godlike": ["epoch-defining", "reality-scale", "unifying", "just", "transcendent", "eternal"]
        }
    },
    "thief": {
        "theme_name": "Casebook of Redemption",
        "verbs": {
            "pathetic": [
                "pickpocketed by habit near", "lied nervously to", "ran from",
                "hid evidence from", "muttered excuses to", "dodged questions from"
            ],
            "modest": [
                "returned stolen goods to", "left an anonymous tip for", "tracked quietly behind",
                "helped recover records for", "de-escalated a dispute with", "guided witnesses toward"
            ],
            "decent": [
                "documented a case against", "outmaneuvered", "protected civilians from",
                "broke surveillance on", "secured evidence from", "coordinated patrols against"
            ],
            "heroic": [
                "stood my ground against", "arrested", "saved a district from",
                "publicly testified against", "led a lawful raid on", "refused a bribe from"
            ],
            "epic": [
                "collapsed a corruption ring led by", "rebuilt trust after confronting",
                "rewrote city policy in response to", "stopped a citywide panic caused by"
            ],
            "legendary": [
                "turned former rivals into partners against", "founded a reform task force targeting",
                "set a justice standard that outlasted"
            ],
            "godlike": [
                "redefined civic honor for", "made accountability unavoidable for",
                "proved redemption and discipline stronger than fear to"
            ]
        },
        "targets": {
            "pathetic": [
                "a corner shop owner", "a tired night guard", "a bus stop crowd",
                "a lockbox I should have ignored", "an old accomplice", "my own reflection in a window"
            ],
            "modest": [
                "a witness under pressure", "a rookie patrol officer", "a neighborhood mediator",
                "a petty extortion runner", "a transit clerk", "a frightened kid from my old block"
            ],
            "decent": [
                "a burglary crew", "a bribed inspector", "a violent debt collector",
                "a warrant dodger", "a smuggling route coordinator", "a protection racket enforcer"
            ],
            "heroic": [
                "a syndicate lieutenant", "a corrupt commander", "a courthouse fixer",
                "an armed convoy leader", "a major gang accountant", "my former mentor"
            ],
            "epic": [
                "a citywide graft network", "the shadow board funding street violence",
                "a cartel court inside city hall"
            ],
            "legendary": [
                "the old economy of fear", "the pipeline that trained kids into crime",
                "institutional silence"
            ],
            "godlike": [
                "the myth that people never change", "the market for purchased justice",
                "the politics of permanent suspicion"
            ]
        },
        "locations": {
            "pathetic": [
                "in the market alley", "behind a pawn shop", "outside a rain-soaked station",
                "near the night bus terminal", "by the old warehouse gate", "under flickering streetlights"
            ],
            "modest": [
                "in the records office", "at a crowded precinct desk", "near a public clinic",
                "inside a housing block corridor", "on the east-side footbridge", "in a neighborhood court"
            ],
            "decent": [
                "at a transit checkpoint", "inside a seizure warehouse", "on rooftop patrol lanes",
                "in a forensic lab hallway", "at a community hearing", "at the docks before dawn"
            ],
            "heroic": [
                "at city hall steps", "in the central courthouse", "inside a barricaded precinct",
                "at the old gang crossroads", "under emergency sirens", "during a live public briefing"
            ],
            "epic": [
                "across every district channel", "in the city's emergency command center",
                "at the vote that changed enforcement forever"
            ],
            "legendary": [
                "in a rebuilt precinct named by the public", "at the first transparent budget hearing",
                "where my old crew once recruited kids"
            ],
            "godlike": [
                "inside the civic memory of the city", "at the legal foundation of a safer era",
                "where distrust used to be policy"
            ]
        },
        "outcomes": {
            "pathetic": [
                "an awkward apology", "one small thing set right", "a warning instead of a fine",
                "a hard lesson", "a notebook full of mistakes", "a choice to try again tomorrow"
            ],
            "modest": [
                "new trust", "better evidence", "a witness willing to speak",
                "a cleaner report", "a safer block", "respect earned quietly"
            ],
            "decent": [
                "charges that held in court", "a gang route disrupted", "families sleeping easier",
                "public confidence rising", "a cleaner command chain", "my name spoken with less fear"
            ],
            "heroic": [
                "a lawful arrest with no bystanders harmed", "a district stabilized",
                "a syndicate operation exposed", "a team that finally believed in me",
                "the badge beginning to feel deserved", "a city choosing procedure over revenge"
            ],
            "epic": [
                "corruption unraveling in public", "a durable reform package passing",
                "justice that survived scrutiny"
            ],
            "legendary": [
                "institutional trust", "a generation given better options", "honor that did not require myth"
            ],
            "godlike": [
                "a city where redemption became policy", "a justice system harder to buy",
                "respect rooted in service, not fear"
            ]
        },
        "flavor": {
            "pathetic": [
                "I still hear old instincts before better ones.",
                "Progress looked small, but it was real.",
                "No one clapped. That was fine."
            ],
            "modest": [
                "The line between guilt and responsibility got clearer.",
                "I learned paperwork can protect people when done right.",
                "Trust started as a rumor and slowly became routine."
            ],
            "decent": [
                "Every clean report felt like a repaired brick in the city.",
                "I stopped chasing reputation and started building reliability.",
                "Old allies tested me. New allies verified me."
            ],
            "heroic": [
                "Respect arrived only after consistency, not speeches.",
                "Mercy worked best when paired with evidence.",
                "My past explained me. It did not excuse me."
            ],
            "epic": [
                "We replaced fear-based order with accountable process.",
                "The city believed change because it could audit it.",
                "I became useful where I used to be dangerous."
            ],
            "legendary": [
                "Honor felt less like a medal and more like daily maintenance.",
                "The badge mattered because the people behind it did.",
                "Service outlived the headlines."
            ],
            "godlike": [
                "Redemption scaled when policy matched principle.",
                "The city stopped asking who I was and watched what I kept doing.",
                "Respect became ordinary, and that was the real victory."
            ]
        },
        "adjectives": {
            "pathetic": ["uneasy", "messy", "imperfect", "awkward", "fragile", "raw"],
            "modest": ["steady", "honest", "careful", "grounded", "constructive", "disciplined"],
            "decent": ["credible", "effective", "principled", "clear-headed", "resilient", "measured"],
            "heroic": ["courageous", "high-stakes", "lawful", "protective", "earned", "public-facing"],
            "epic": ["system-level", "city-shifting", "institutional", "irreversible", "historic", "transformative"],
            "legendary": ["foundational", "trusted", "civil", "enduring", "balanced", "reform-grade"],
            "godlike": ["epoch-defining", "unifying", "just", "transcendent", "civic", "eternal"]
        }
    },
    "zoo_worker": {
        "theme_name": "Sanctuary Shift Log",
        "verbs": {
            "pathetic": [
                "dropped feed near", "misread a gate tag for", "tripped carrying supplies past",
                "awkwardly introduced myself to", "spilled water beside", "apologized to"
            ],
            "modest": [
                "fed", "calmed", "escorted", "cleaned the enclosure for",
                "updated records on", "guided visitors away from"
            ],
            "decent": [
                "stabilized", "rescued", "tracked", "documented signs around",
                "coordinated a safe transfer for", "secured evidence against"
            ],
            "heroic": [
                "evacuated families from", "held the line against", "protected Mila from",
                "negotiated peace with", "contained the panic around", "stood firm before"
            ],
            "epic": [
                "navigated the rift storm over", "prevented catastrophe with", "rewrote emergency protocol for"
            ],
            "legendary": [
                "kept a final promise to", "witnessed the farewell flight of", "built a lasting sanctuary after"
            ],
            "godlike": [
                "redefined care and courage for", "chose love over fear before", "left a humane legacy for"
            ]
        },
        "targets": {
            "pathetic": [
                "a grumpy meerkat", "a sleepy capybara", "a stubborn gate latch",
                "a wet supply crate", "a nervous intern", "my own checklist"
            ],
            "modest": [
                "injured cranes", "anxious hatchlings", "night-shift keepers",
                "a crowd at the reptile house", "Mila's rescue team", "a restless old tiger"
            ],
            "decent": [
                "a failed alarm network", "a frightened school group", "a breached aviary lane",
                "a surge through the storm deck", "the emergency holding bay", "an enclosure blackout"
            ],
            "heroic": [
                "the citywide panic line", "the containment command", "the rift over the aviary",
                "the collapse at east enclosure", "Emberwing under pressure", "the loudest doubters"
            ],
            "epic": [
                "the fracture in dawn-lit sky", "the timeline rupture over the zoo", "the final containment horizon"
            ],
            "legendary": [
                "Emberwing's return gate", "the memory of first dawn", "the promise I could not keep and still honor"
            ],
            "godlike": [
                "the meaning of guardianship", "the border between duty and love", "the future of humane stewardship"
            ]
        },
        "locations": {
            "pathetic": [
                "in the feed storage hall", "by the clinic sink", "at the old staff corridor",
                "under a leaking awning", "outside enclosure B", "near the ticket booth"
            ],
            "modest": [
                "at the reptile house", "on the aviary bridge", "in the clinic tunnel",
                "across the night paddock", "by the keeper locker room", "at the storm fence gate"
            ],
            "decent": [
                "inside the emergency command room", "under floodlights at enclosure row six",
                "in the rift-monitor chamber", "across the visitor evacuation route",
                "beneath the shattered glass dome", "at the old watchtower stairs"
            ],
            "heroic": [
                "at first siren across the main concourse", "in the center of the aviary rift",
                "between terrified crowds and open flame", "on live city feed",
                "at dawn above the eastern wall", "inside the failing containment arc"
            ],
            "epic": [
                "inside a sky split by lightning", "where two eras touched for one breath", "at the edge of the dawn gate"
            ],
            "legendary": [
                "under the final sunrise before departure", "where the dragon bowed and rose", "at the sanctuary we rebuilt"
            ],
            "godlike": [
                "where time learned restraint", "at the seam between memory and future", "in the story the city kept"
            ]
        },
        "outcomes": {
            "pathetic": [
                "a lesson learned", "one fewer mistake", "a calmer shift",
                "a cleaner logbook", "a tired laugh", "a better second attempt"
            ],
            "modest": [
                "restored trust", "safe evacuation", "stable routines",
                "clear records", "shared confidence", "a safer habitat"
            ],
            "decent": [
                "a controlled response", "verified evidence", "panic reduced",
                "a rescued team", "a stronger plan", "real momentum"
            ],
            "heroic": [
                "lives protected", "the city calmed", "love made explicit",
                "the dragon spared", "a crisis contained", "a promise honored"
            ],
            "epic": [
                "catastrophe avoided at scale", "an irreversible turning point", "a dawn no one expected"
            ],
            "legendary": [
                "wise farewell", "lasting stewardship", "grief transformed into purpose"
            ],
            "godlike": [
                "an era-defining act of care", "a humane legacy", "a future built on responsibility"
            ]
        },
        "flavor": {
            "pathetic": [
                "I still smelled like wet hay and panic.",
                "No one noticed the small fix except me.",
                "The checklist looked longer after midnight."
            ],
            "modest": [
                "Mila said calm is a skill, not a mood.",
                "Small routines kept everyone alive today.",
                "Trust grew by one quiet action at a time."
            ],
            "decent": [
                "Documentation mattered as much as bravery.",
                "We stopped calling luck a strategy.",
                "Care became coordination under pressure."
            ],
            "heroic": [
                "Love made the hard choice clearer, not easier.",
                "The loud option was not the wise one.",
                "We protected both truth and people."
            ],
            "epic": [
                "The sky split and the team held.",
                "Two timelines touched and still we stayed disciplined.",
                "No one forgot who put process before ego."
            ],
            "legendary": [
                "Farewell can be an act of devotion.",
                "The dragon left, and responsibility remained.",
                "What stayed behind mattered as much as what departed."
            ],
            "godlike": [
                "Wisdom looked like restraint under maximum power.",
                "We chose a future we could ethically maintain.",
                "The city remembered care as strength."
            ]
        },
        "adjectives": {
            "pathetic": ["uneven", "muddy", "awkward", "rushed", "tired", "fragile"],
            "modest": ["steady", "patient", "alert", "calm", "practical", "grounded"],
            "decent": ["coordinated", "reliable", "disciplined", "effective", "caring", "measured"],
            "heroic": ["courageous", "high-stakes", "protective", "truthful", "earned", "decisive"],
            "epic": ["sky-splitting", "city-scale", "era-shifting", "mythic", "irreversible", "historic"],
            "legendary": ["wise", "heartfelt", "lasting", "balanced", "dignified", "foundational"],
            "godlike": ["epoch-defining", "humane", "transcendent", "unifying", "just", "eternal"]
        }
    },
}

# Default diary content (fallback for compatibility)
DIARY_POWER_TIERS = {
    "pathetic": (0, 49),
    "modest": (50, 149),
    "decent": (150, 349),
    "heroic": (350, 599),
    "epic": (600, 999),
    "legendary": (1000, 1499),
    "godlike": (1500, 2000)
}

DIARY_VERBS = {
    "pathetic": [
        "accidentally poked", "awkwardly stared at", "tripped over", "licked",
        "politely asked", "nervously waved at", "mildly annoyed", "quietly judged",
        "bumped into", "accidentally sat on", "coughed near", "sneezed at",
        "gave a participation trophy to", "made eye contact with", "slightly nudged",
        "mumbled at", "waddled toward", "unsuccessfully high-fived", "apologized to",
        "stood next to", "accidentally photobombed", "passive-aggressively sighed at"
    ],
    "modest": [
        "challenged", "pushed", "tickled", "startled", "confused", "outsmarted",
        "debated", "out-danced", "arm-wrestled", "had lunch with", "roasted",
        "pranked", "traded snacks with", "shared a blanket with", "high-fived",
        "karaoked with", "played cards with", "had an intense staring match with"
    ],
    "decent": [
        "fought", "defeated in combat", "had an epic duel with", "outmaneuvered",
        "tactically retreated from", "formed an alliance with", "rescued",
        "was rescued by", "traded ancient secrets with", "meditated with",
        "trained alongside", "went on a quest with", "discovered treasure with"
    ],
    "heroic": [
        "slayed", "vanquished", "banished to another realm", "imprisoned in crystal",
        "sealed away forever", "turned to stone", "defeated with one strike",
        "humiliated in front of their army", "outsmarted in dimensional chess",
        "absorbed the power of", "broke the curse of", "freed from eternal slumber"
    ],
    "epic": [
        "obliterated from existence", "erased from the timeline", "trapped in a paradox",
        "fused into a single being with", "ascended to godhood alongside",
        "challenged the very concept of", "rewrote the laws of physics with",
        "bent reality around", "consumed the essence of", "became the avatar of"
    ],
    "legendary": [
        "became one with the cosmos alongside", "achieved omniscience from",
        "transcended time and space with", "became the last memory of",
        "is now worshipped alongside", "became a fundamental force with"
    ],
    "godlike": [
        "created and destroyed infinite realities with",
        "became the alpha and omega alongside",
        "is now the fundamental equation of existence with",
        "transcended all possible dimensions with"
    ]
}

DIARY_ADJECTIVES = {
    "pathetic": [
        "mildly inconvenient", "slightly annoying", "confusing",
        "unimpressive", "suspiciously normal", "forgettable", "generic",
        "embarrassing", "anticlimactic", "underwhelming", "disappointing"
    ],
    "modest": [
        "reasonably impressive", "decent", "notable",
        "interesting", "surprising", "unexpected", "capable",
        "respectable", "worthwhile", "encouraging", "promising"
    ],
    "decent": [
        "legendary", "mythical", "ancient", "powerful", "fearsome",
        "dreaded", "fabled", "renowned", "notorious", "infamous",
        "formidable", "remarkable", "extraordinary"
    ],
    "heroic": [
        "reality-bending", "dimension-hopping", "time-traveling", "fate-weaving",
        "prophecy-fulfilling", "destiny-altering", "world-shaking",
        "epic", "legendary", "awe-inspiring", "history-making"
    ],
    "epic": [
        "infinitely powerful", "omniscient", "omnipotent", "omnipresent",
        "beyond comprehension", "reality-defining", "universe-creating",
        "existence-shaking", "cosmos-altering", "infinity-spanning"
    ],
    "legendary": [
        "cosmic", "incomprehensible yet awe-inspiring",
        "beyond all understanding", "reality-core level",
        "transcendently powerful", "eternally significant"
    ],
    "godlike": [
        "the stuff of pure legend", "beyond mortal comprehension",
        "cosmically significant", "the pinnacle of all existence",
        "eternally transcendent", "absolutely universe-defining"
    ]
}

DIARY_TARGETS = {
    "pathetic": [
        "intern", "confused tourist", "lost pizza delivery guy",
        "someone's weird uncle", "procrastinating student", "grumpy cat"
    ],
    "modest": [
        "minor goblin", "trainee wizard", "apprentice knight", "baby dragon",
        "teenage vampire", "part-time werewolf", "gig-economy demon"
    ],
    "decent": [
        "proper dragon", "experienced sorcerer", "veteran knight",
        "master assassin", "ancient lich", "demon lord", "angel captain"
    ],
    "heroic": [
        "elder god", "titan of old", "primordial being", "arch-demon",
        "archangel", "god of war", "goddess of wisdom", "lord of chaos"
    ],
    "epic": [
        "the concept of entropy itself", "the physical manifestation of chaos",
        "the living embodiment of time", "the sentient void between dimensions"
    ],
    "legendary": [
        "the mathematical constant that defines all reality",
        "the final theorem of existence", "the first thought ever conceived"
    ],
    "godlike": [
        "the source code of existence", "the original writer of reality",
        "the concept of focus that created the universe"
    ]
}

DIARY_LOCATIONS = {
    "pathetic": [
        "in the break room", "at a gas station bathroom", "in a DMV waiting room",
        "at a sketchy laundromat", "in a Wendy's parking lot", "at a bus stop"
    ],
    "modest": [
        "in a mysterious forest", "at an ancient crossroads", "in a forgotten temple",
        "at a haunted inn", "in a magical marketplace", "at the edge of civilization"
    ],
    "decent": [
        "in the heart of an erupting volcano", "at the peak of the world's tallest mountain",
        "in the depths of the ocean abyss", "at the center of an eternal storm"
    ],
    "heroic": [
        "in the space between dimensions", "at the crossroads of all timelines",
        "in the void between stars", "at the edge of a black hole"
    ],
    "epic": [
        "in a reality that shouldn't exist", "at the intersection of all possibilities",
        "in the negative space of existence", "at the point where math breaks down"
    ],
    "legendary": [
        "in the concept of 'here' before 'here' existed",
        "at the philosophical debate about whether places are real"
    ],
    "godlike": [
        "in the source code repository of existence",
        "at the root directory of all dimensions"
    ]
}

DIARY_OUTCOMES = {
    "pathetic": [
        "a minor inconvenience", "an awkward silence", "a participation certificate",
        "a weird look", "a very confusing email thread", "both of us just walking away"
    ],
    "modest": [
        "unexpected friendship", "a temporary truce", "mutual respect",
        "a rematch scheduled for next week", "both of us going our separate ways"
    ],
    "decent": [
        "a grand victory", "absolute triumph", "hard-won glory", "legendary status",
        "songs written about it", "a statue being commissioned", "national holidays"
    ],
    "heroic": [
        "the rewriting of prophecy", "reality itself shifting", "a new age beginning",
        "the old gods taking notice", "dimensions merging temporarily"
    ],
    "epic": [
        "the multiverse experiencing an existential crisis",
        "several timelines just... stopping to watch",
        "infinity googling 'how to handle this'"
    ],
    "legendary": [
        "the concept of 'endings' having to be redefined",
        "philosophy departments worldwide spontaneously combusting"
    ],
    "godlike": [
        "a new mathematical constant being defined: focus",
        "the universe's source code being refactored"
    ]
}

DIARY_FLAVOR = {
    "pathetic": [
        "I was wearing mismatched socks.",
        "My phone was at 2% battery.",
        "I had spinach in my teeth the whole time."
    ],
    "modest": [
        "The weather was surprisingly pleasant.",
        "Someone took a really blurry photo of it.",
        "A random bard wrote a mediocre song about it."
    ],
    "decent": [
        "The stars literally aligned for this moment.",
        "Ancient prophecies were fulfilled. Not the important ones, but still.",
        "A wise old sage nodded approvingly from somewhere."
    ],
    "heroic": [
        "Reality itself paused to take notes.",
        "The gods added this to their highlight reel.",
        "Time briefly considered flowing backward just to watch again."
    ],
    "epic": [
        "Parallel versions of me in alternate realities high-fived simultaneously.",
        "The space-time continuum updated its status to 'it's complicated'.",
        "Quantum physicists somewhere felt a great disturbance."
    ],
    "legendary": [
        "The concept of 'possible' was permanently expanded.",
        "Several philosophical frameworks had to be rewritten."
    ],
    "godlike": [
        "This is now taught in universe design courses across the multiverse.",
        "The cosmic code review team gave me a 'LGTM'."
    ]
}


def get_diary_power_tier(power: int) -> str:
    """Get the diary tier name based on character power."""
    for tier_name, (min_power, max_power) in DIARY_POWER_TIERS.items():
        if min_power <= power <= max_power:
            return tier_name
    return "godlike" if power >= 1500 else "pathetic"


def calculate_session_tier_boost(session_minutes: int) -> int:
    """Calculate tier boost chance based on session length."""
    if session_minutes >= 120:
        return 1 if random.random() < 0.35 else 0
    elif session_minutes >= 90:
        return 1 if random.random() < 0.20 else 0
    elif session_minutes >= 60:
        return 1 if random.random() < 0.10 else 0
    return 0


def generate_diary_entry(power: int, session_minutes: int = 25, equipped_items: dict = None,
                         story_id: str = None) -> dict:
    """
    Generate a hilarious diary entry based on character power level and story theme.
    
    Args:
        power: Character's current power level
        session_minutes: Length of the focus session
        equipped_items: Dict of equipped items (for item mentions)
        story_id: Story theme for diary content (None = use default/warrior)
    
    Returns:
        dict with diary entry data including story, tier info, and timestamp
    """
    base_tier = get_diary_power_tier(power)
    available_tiers = list(DIARY_POWER_TIERS.keys())
    base_tier_index = available_tiers.index(base_tier)
    
    session_boost = calculate_session_tier_boost(session_minutes)
    boosted_index = min(base_tier_index + session_boost, len(available_tiers) - 1)
    tier = available_tiers[boosted_index]
    tier_was_boosted = boosted_index > base_tier_index
    
    adjacent_chance = random.random()
    tier_index = available_tiers.index(tier)
    
    verb_tier = tier
    if adjacent_chance < 0.15 and tier_index < len(available_tiers) - 1:
        verb_tier = available_tiers[tier_index + 1]
    
    # Get story-themed content if available
    if story_id and story_id in STORY_DIARY_THEMES:
        theme = STORY_DIARY_THEMES[story_id]
        theme_name = theme["theme_name"]
        
        # Get themed content, falling back to defaults if tier not found or list is empty
        verb_list = theme["verbs"].get(verb_tier) or DIARY_VERBS.get(verb_tier, ["acted"])
        verb = random.choice(verb_list) if verb_list else "acted"
        target_list = theme["targets"].get(tier) or DIARY_TARGETS.get(tier, ["something"])
        target = random.choice(target_list) if target_list else "something"
        location_list = theme["locations"].get(tier) or DIARY_LOCATIONS.get(tier, ["somewhere"])
        location = random.choice(location_list) if location_list else "somewhere"
        outcome_list = theme["outcomes"].get(tier) or DIARY_OUTCOMES.get(tier, ["completed"])
        outcome = random.choice(outcome_list) if outcome_list else "completed"
        flavor_list = theme["flavor"].get(tier) or DIARY_FLAVOR.get(tier, [""])
        flavor = random.choice(flavor_list) if flavor_list else ""
        # Use theme-specific adjectives if available, otherwise fall back to defaults
        if "adjectives" in theme and tier in theme["adjectives"]:
            adjective = random.choice(theme["adjectives"][tier])
        else:
            adjective = random.choice(DIARY_ADJECTIVES[tier])
    else:
        # Fallback to default (warrior-style) content
        theme_name = "âš”ď¸Ź Adventure Log"
        verb = random.choice(DIARY_VERBS[verb_tier])
        adjective = random.choice(DIARY_ADJECTIVES[tier])
        target = random.choice(DIARY_TARGETS[tier])
        location = random.choice(DIARY_LOCATIONS[tier])
        outcome = random.choice(DIARY_OUTCOMES[tier])
        flavor = random.choice(DIARY_FLAVOR[tier])
    
    # Build story sentence - theme-appropriate structures that avoid grammar issues
    # Each theme uses a structure where adjective is in a separate clause
    if story_id == "warrior":
        # Warrior: Epic battle narrative with adjective describing the encounter
        story = f"Today I {verb} {target} {location}. The battle was {adjective}. It ended in {outcome}."
    elif story_id == "scholar":
        # Scholar: Academic discovery narrative with adjective describing the work
        story = f"Today I {verb} {target} {location}. The research was {adjective}. It ended in {outcome}."
    elif story_id == "wanderer":
        # Wanderer: Dream journey narrative with adjective describing the vision
        story = f"Today I {verb} {target} {location}. The vision was {adjective}. It ended in {outcome}."
    elif story_id == "underdog":
        # Underdog: Office struggle narrative with adjective describing the situation
        story = f"Today I {verb} {target} {location}. It was {adjective}. It ended in {outcome}."
    elif story_id == "scientist":
        # Scientist: research narrative with adjective describing the experiment
        story = f"Today I {verb} {target} {location}. The experiment was {adjective}. It ended in {outcome}."
    elif story_id == "robot":
        # Robot: Industrial awakening narrative with adjective describing the operation
        story = f"Today I {verb} {target} {location}. The operation was {adjective}. It ended in {outcome}."
    elif story_id == "space_pirate":
        # Space Pirate: orbit-heist narrative with adjective describing the maneuver
        story = f"Today I {verb} {target} {location}. The maneuver was {adjective}. It ended in {outcome}."
    elif story_id == "thief":
        # Thief: redemption casefile narrative with adjective describing the case
        story = f"Today I {verb} {target} {location}. The case was {adjective}. It ended in {outcome}."
    elif story_id == "zoo_worker":
        # Zoo Worker: sanctuary shift narrative with adjective describing the shift
        story = f"Today I {verb} {target} {location}. The shift felt {adjective}. It ended in {outcome}."
    else:
        # Default fallback pattern
        story = f"Today I {verb} {target} {location}. It was {adjective}. It ended in {outcome}."
    
    item_mention = ""
    if equipped_items:
        equipped_list = [item for item in equipped_items.values() if item]
        if equipped_list:
            featured_item = random.choice(equipped_list)
            item_name = featured_item.get("name", "mysterious item")
            
            # Story-themed item mention templates
            if story_id == "scholar":
                item_templates = [
                    f"My trusty {item_name} provided the crucial insight.",
                    f"I consulted my {item_name} for guidance.",
                    f"The {item_name} practically glowed with knowledge.",
                ]
            elif story_id == "wanderer":
                item_templates = [
                    f"My {item_name} pulsed with dream energy.",
                    f"The {item_name} guided me through the visions.",
                    f"I felt my {item_name} resonating with the cosmic frequency.",
                ]
            elif story_id == "underdog":
                item_templates = [
                    f"My {item_name} gave me the edge I needed.",
                    f"Couldn't have crushed it without my {item_name}.",
                    f"The {item_name} was clutch in that moment.",
                ]
            elif story_id == "scientist":
                item_templates = [
                    f"My {item_name} tightened the protocol right when variance spiked.",
                    f"The {item_name} turned noisy data into something defensible.",
                    f"I trusted {item_name} as the final control, and it held.",
                ]
            elif story_id == "robot":
                item_templates = [
                    f"My {item_name} synchronized perfectly with my core loop.",
                    f"The {item_name} stabilized my systems at the critical second.",
                    f"I rerouted everything through {item_name}, and it held.",
                ]
            elif story_id == "space_pirate":
                item_templates = [
                    f"My {item_name} turned a bad orbit into a clean escape.",
                    f"The {item_name} looked ridiculous until it won us the sector.",
                    f"I flashed {item_name} at customs and somehow everyone got polite.",
                ]
            elif story_id == "thief":
                item_templates = [
                    f"My {item_name} kept the case clean when everything got noisy.",
                    f"The {item_name} reminded me discipline beats impulse.",
                    f"I used {item_name} the lawful way, and it changed the outcome.",
                ]
            elif story_id == "zoo_worker":
                item_templates = [
                    f"My {item_name} helped keep everyone calm when the sky turned wild.",
                    f"The {item_name} reminded me that care is a system, not a feeling.",
                    f"I trusted {item_name} at the critical moment, and the whole shift held.",
                ]
            else:  # warrior or default
                item_templates = [
                    f"My trusty {item_name} proved essential.",
                    f"I couldn't have done it without my {item_name}.",
                    f"The {item_name} glowed with approval.",
                ]
            item_mention = random.choice(item_templates)
    
    full_entry = f"{story} {flavor}"
    if item_mention:
        full_entry += f" {item_mention}"
    
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "story": full_entry,
        "power_at_time": power,
        "tier": tier,
        "base_tier": base_tier,
        "tier_boosted": tier_was_boosted,
        "session_boost": session_boost,
        "session_minutes": session_minutes,
        "short_date": datetime.now().strftime("%b %d, %Y"),
        "story_theme": story_id or "warrior",
        "theme_name": theme_name
    }


def calculate_rarity_bonuses(session_minutes: int = 0, streak_days: int = 0) -> dict:
    """
    Calculate rarity distribution using a moving window system.
    
    The window [2%, 20%, 56%, 20%, 2%] shifts through tiers based on session length:
    - 30min: Center on Common (tier 0)
    - 60min: Center on Uncommon (tier 1)
    - 2hr: Center on Rare (tier 2)
    - 3hr: Center on Epic (tier 3)
    - 4hr: Center on Legendary (tier 4)
    - 5hr: Center on tier 5 (virtual, overflow to Legendary)
    - 6hr+: 100% Legendary
    - 7hr+: 100% Legendary + 20% chance of bonus item
    - 8hr+: 100% Legendary + 50% chance of bonus item
    """
    # Determine center tier based on session length
    # Tiers: 0=Common, 1=Uncommon, 2=Rare, 3=Epic, 4=Legendary
    if session_minutes >= 360:      # 6hr+ = 100% Legendary
        center_tier = 6  # Far enough that window gives 100% Legendary
    elif session_minutes >= 300:    # 5hr
        center_tier = 5
    elif session_minutes >= 240:    # 4hr
        center_tier = 4
    elif session_minutes >= 180:    # 3hr
        center_tier = 3
    elif session_minutes >= 120:    # 2hr
        center_tier = 2
    elif session_minutes >= 60:     # 1hr
        center_tier = 1
    elif session_minutes >= 30:     # 30min
        center_tier = 0
    else:
        center_tier = -1  # Use base distribution for <30min
    
    # Calculate bonus item chance for 7hr+
    bonus_item_chance = 0
    if session_minutes >= 480:      # 8hr = 50% chance
        bonus_item_chance = 50
    elif session_minutes >= 420:    # 7hr = 20% chance
        bonus_item_chance = 20
    
    # Streak bonus (adds to center tier)
    streak_tier_bonus = 0
    if streak_days >= 60:
        streak_tier_bonus = 0.5
    elif streak_days >= 30:
        streak_tier_bonus = 0.35
    elif streak_days >= 14:
        streak_tier_bonus = 0.2
    elif streak_days >= 7:
        streak_tier_bonus = 0.1
    
    return {
        "center_tier": center_tier,
        "streak_tier_bonus": streak_tier_bonus,
        "bonus_item_chance": bonus_item_chance,
        "session_minutes": session_minutes,
        # Keep legacy fields for compatibility
        "session_bonus": min(session_minutes, 480) // 4.8 if session_minutes > 0 else 0,
        "streak_bonus": streak_tier_bonus * 20,
        "total_bonus": (center_tier + streak_tier_bonus) * 20 if center_tier >= 0 else 0
    }


def get_focus_rarity_distribution(
    session_minutes: int = 0,
    streak_days: int = 0,
    adhd_buster: Optional[dict] = None,
) -> dict:
    """
    Compute the canonical focus-session rarity distribution used by generate_item().
    """
    rarities = get_standard_reward_rarity_order()
    base_weights = [ITEM_RARITIES[r]["weight"] for r in rarities]

    bonuses = calculate_rarity_bonuses(session_minutes, streak_days)
    center_tier = bonuses.get("center_tier", -1)
    streak_bonus = bonuses.get("streak_tier_bonus", 0.0)

    entity_rarity_bonus = 0.0
    city_rarity_bonus = 0.0
    if adhd_buster:
        luck_perks = get_entity_luck_perks(adhd_buster)

        rarity_bias = luck_perks.get("rarity_bias", 0)
        if rarity_bias > 0:
            entity_rarity_bonus += rarity_bias / 10.0

        drop_luck = min(luck_perks.get("drop_luck", 0), 5)
        if drop_luck > 0:
            entity_rarity_bonus += drop_luck / 20.0

        entity_rarity_bonus = min(entity_rarity_bonus, 0.3)

        try:
            city_bonuses = _safe_get_city_bonuses(adhd_buster)
            city_rarity = city_bonuses.get("rarity_bias_bonus", 0)
            if city_rarity > 0:
                city_rarity_bonus = city_rarity / 10.0
        except Exception:
            pass

        city_rarity_bonus = min(city_rarity_bonus, 0.2)

    total_modifier = min(streak_bonus + entity_rarity_bonus + city_rarity_bonus, 1.0)
    effective_center = center_tier + total_modifier

    if effective_center >= 0:
        window = [2, 20, 56, 20, 2]
        weights = [0] * len(rarities)
        rounded_center = round(effective_center)
        for offset, pct in zip([-2, -1, 0, 1, 2], window):
            target_tier = rounded_center + offset
            clamped_tier = max(0, min(len(rarities) - 1, target_tier))
            weights[clamped_tier] += pct
    else:
        weights = base_weights

    return {
        "rarities": rarities,
        "weights": weights,
        "center_tier": center_tier,
        "effective_center": effective_center,
        "total_modifier": total_modifier,
    }


def roll_focus_reward_outcome(
    session_minutes: int = 0,
    streak_days: int = 0,
    adhd_buster: Optional[dict] = None,
    roll: Optional[float] = None,
) -> dict:
    """
    Canonical backend roll for focus-session reward rarity.

    The slider's final position maps directly to this roll (0..100).
    """
    distribution = get_focus_rarity_distribution(
        session_minutes=session_minutes,
        streak_days=streak_days,
        adhd_buster=adhd_buster,
    )
    rarities = distribution.get("rarities", get_standard_reward_rarity_order())
    weights = distribution.get("weights", [])
    total = sum(weights)

    if total <= 0 or not rarities:
        fallback = get_standard_reward_rarity_order()
        return {
            "rarity": fallback[0] if fallback else "Common",
            "roll": 0.0,
            "weights": [100] + [0] * (len(fallback) - 1) if fallback else [100],
            "rarities": fallback,
        }

    gated_outcome = evaluate_power_gated_rarity_roll(
        rarities,
        weights,
        adhd_buster=adhd_buster,
        roll=roll,
    )

    return {
        "rarity": gated_outcome.get("rarity", rarities[0]),
        "roll": gated_outcome.get("roll", 0.0),
        "weights": weights,
        "rarities": rarities,
        "power_gating": gated_outcome,
    }


# Rarity order for tier calculations
RARITY_ORDER = get_rarity_order()


def get_current_tier(adhd_buster: dict) -> str:
    """Get the highest rarity tier from equipped items."""
    equipped = adhd_buster.get("equipped", {})
    highest_tier = "Common"
    
    for item in equipped.values():
        if item:
            item_rarity = _canonical_rarity(item.get("rarity", "Common"), default="Common")
            # Safely handle invalid rarity values
            try:
                item_idx = RARITY_ORDER.index(item_rarity)
                highest_idx = RARITY_ORDER.index(highest_tier)
                if item_idx > highest_idx:
                    highest_tier = item_rarity
            except ValueError:
                pass  # Skip items with invalid rarity
    
    return highest_tier


def get_boosted_rarity(current_tier: str) -> str:
    """Get a rarity one tier higher than current (capped at current obtainable max)."""
    return get_next_rarity(current_tier, max_rarity=MAX_OBTAINABLE_RARITY)


def generate_daily_reward_item(adhd_buster: dict, story_id: str = None) -> dict:
    """
    Generate a daily reward item - one tier higher than current equipped tier.
    Uses the active story's theme for item generation.
    """
    current_tier = get_current_tier(adhd_buster)
    boosted_rarity = get_boosted_rarity(current_tier)
    
    # Get the active story if not specified
    if story_id is None:
        story_id = adhd_buster.get("active_story", "warrior")
    
    return generate_item(rarity=boosted_rarity, story_id=story_id)


# Priority completion reward settings
PRIORITY_BASE_COMPLETION_CHANCE = 15  # 15% base chance to win a reward
PRIORITY_REWARD_WEIGHTS = {
    # Low chance rewards are high tier - inverted from normal drops
    "Common": 5,       # 5% of rewards
    "Uncommon": 10,    # 10% of rewards  
    "Rare": 30,        # 30% of rewards
    "Epic": 35,        # 35% of rewards
    "Legendary": 20    # 20% of rewards!
}


def roll_priority_completion_reward(
    story_id: str = None,
    logged_hours: float = 0,
    adhd_buster: Optional[dict] = None,
) -> Optional[dict]:
    """
    Roll for a priority completion reward.
    Chance scales with logged hours: base 15%, up to 99% for 20+ hours.
    
    Args:
        story_id: Story theme for item generation
        logged_hours: Hours logged on this priority (higher = better chance)
    
    Returns:
        dict with 'won' (bool), 'item' (dict or None), 'message' (str), 'chance' (int)
    """
    # Calculate chance based on logged hours
    # 0h = 15%, 5h = 35%, 10h = 55%, 15h = 75%, 20h+ = 99%
    if logged_hours >= 20:
        chance = 99
    elif logged_hours > 0:
        # Linear scaling: 15% + (logged_hours / 20) * 84 = up to 99%
        chance = min(99, int(PRIORITY_BASE_COMPLETION_CHANCE + (logged_hours / 20) * 84))
    else:
        chance = PRIORITY_BASE_COMPLETION_CHANCE
    
    # First roll: did the user win?
    win_roll = random.random()
    won = win_roll < (chance / 100.0)
    if not won:
        return {
            "won": False,
            "item": None,
            "message": "No lucky gift this time... Keep completing priorities for another chance!",
            "chance": chance,
            "win_roll": win_roll,
            "rarity_roll": None,
            "rarity": "",
            "power_gating": None,
        }
    
    # User won! Roll for rarity (weighted toward high tiers).
    rarity_roll = random.random() * 100.0
    rarity_order = list(get_standard_reward_rarity_order()) or [
        "Common", "Uncommon", "Rare", "Epic", "Legendary"
    ]
    rarity_weights = [PRIORITY_REWARD_WEIGHTS.get(r, 0) for r in rarity_order]
    gated_outcome = evaluate_power_gated_rarity_roll(
        rarity_order,
        rarity_weights,
        adhd_buster=adhd_buster,
        roll=rarity_roll,
    )
    lucky_rarity = gated_outcome.get("rarity", "Legendary")
    rarity_roll = gated_outcome.get("roll", rarity_roll)
    
    # Generate the item with this rarity and story theme
    item = generate_item(rarity=lucky_rarity, story_id=story_id)
    
    rarity_messages = {
        "Common": "A small gift for your hard work!",
        "Uncommon": "Nice! A quality reward for your dedication!",
        "Rare": "Excellent! A rare treasure for completing your priority!",
        "Epic": "AMAZING! An epic reward befitting your achievement!",
        "Legendary": "đźŚź LEGENDARY! đźŚź The focus gods smile upon you!",
        "Celestial": "CELESTIAL! The impossible tier has answered your focus!"
    }
    
    return {
        "won": True,
        "item": item,
        "message": rarity_messages.get(lucky_rarity, "You won a reward!"),
        "chance": chance,
        "win_roll": win_roll,
        "rarity_roll": rarity_roll,
        "rarity": lucky_rarity,
        "power_gating": gated_outcome,
    }


def generate_item(rarity: str = None, session_minutes: int = 0, streak_days: int = 0,
                  story_id: str = None, adhd_buster: dict = None) -> dict:
    """
    Generate a random item with rarity influenced by session length and streak.
    
    Uses a moving window system where longer sessions shift the probability
    distribution toward higher rarities:
    - Window pattern: [2%, 20%, 56%, 20%, 2%] centered on a tier
    - Overflow at edges is absorbed by the edge tier
    
    Args:
        rarity: Force a specific rarity (None = random based on weights)
        session_minutes: Session length for luck bonus
        streak_days: Streak days for luck bonus
        story_id: Story theme to use for item generation (None = use fallback)
        adhd_buster: Hero data for entity perk calculation (optional)
    
    Returns:
        dict with item properties including story_theme for display
    """
    if rarity is None:
        distribution = get_focus_rarity_distribution(
            session_minutes=session_minutes,
            streak_days=streak_days,
            adhd_buster=adhd_buster,
        )
        rarities = distribution["rarities"]
        weights = distribution["weights"]
        rarity = random.choices(rarities, weights=weights)[0]
    
    # Get story-themed item generation data
    if story_id and story_id in STORY_GEAR_THEMES:
        theme = get_story_gear_theme(story_id)
        item_types = theme["item_types"]
        adjectives = theme["adjectives"]
        suffixes = theme["suffixes"]
        theme_id = story_id
    else:
        # Fallback to default (warrior theme for compatibility)
        item_types = ITEM_SLOTS
        adjectives = {r: ITEM_RARITIES[r]["adjectives"] for r in ITEM_RARITIES}
        suffixes = ITEM_SUFFIXES
        theme_id = "warrior"
    
    # Validate rarity BEFORE using it (prevent invalid key access)
    if rarity not in ITEM_RARITIES:
        rarity = "Common"
    
    # Generate the item
    slot = random.choice(list(item_types.keys()))
    item_type = random.choice(item_types[slot])
    fallback_adjectives = ITEM_RARITIES.get(rarity, ITEM_RARITIES["Common"]).get("adjectives", [])
    adjective_pool = adjectives.get(rarity) or fallback_adjectives or adjectives.get("Common", ["Unknown"])
    suffix_pool = suffixes.get(rarity) or ITEM_SUFFIXES.get(rarity) or suffixes.get("Common", ["Mystery"])
    adjective = random.choice(adjective_pool)
    suffix = random.choice(suffix_pool)
    
    name = f"{adjective} {item_type} of {suffix}"
    
    # Roll for lucky options
    lucky_options = roll_lucky_options(rarity)
    
    # Generate unique ID for this item (prevents timestamp collision issues)
    import uuid
    unique_id = str(uuid.uuid4())
    
    item_data = {
        "name": name,
        "rarity": rarity,
        "slot": slot,
        "item_type": item_type,
        "color": ITEM_RARITIES[rarity]["color"],
        "power": RARITY_POWER[rarity],
        "story_theme": theme_id,  # Track which theme generated this item
        "obtained_at": datetime.now().isoformat(),
        "item_id": unique_id  # Unique identifier for each item
    }
    
    # Add lucky options if any were rolled
    if lucky_options:
        item_data["lucky_options"] = lucky_options
    
    return item_data


def generate_session_items(session_minutes: int = 0, streak_days: int = 0,
                           story_id: str = None) -> list:
    """
    Generate items for a completed session, potentially including bonus items.
    
    For sessions 7hr+, there's a chance to get a bonus Legendary item:
    - 7hr: 20% chance of bonus Legendary
    - 8hr: 50% chance of bonus Legendary
    
    Args:
        session_minutes: Session length in minutes
        streak_days: Streak days for luck bonus
        story_id: Story theme to use for item generation
    
    Returns:
        List of generated items (1-2 items)
    """
    items = []
    
    # Generate primary item
    primary_item = generate_item(
        session_minutes=session_minutes,
        streak_days=streak_days,
        story_id=story_id
    )
    items.append(primary_item)
    
    # Check for bonus item (7hr+ sessions)
    bonuses = calculate_rarity_bonuses(session_minutes, streak_days)
    bonus_chance = bonuses.get("bonus_item_chance", 0)
    
    if bonus_chance > 0 and random.randint(1, 100) <= bonus_chance:
        # Bonus item is always current top standard-reward tier.
        bonus_item = generate_item(
            rarity=get_standard_reward_rarity_order()[-1],
            session_minutes=session_minutes,
            streak_days=streak_days,
            story_id=story_id
        )
        bonus_item["is_bonus"] = True  # Mark as bonus item
        items.append(bonus_item)
    
    return items


def calculate_character_power(adhd_buster: dict, include_set_bonus: bool = True,
                              include_neighbor_effects: bool = True) -> int:
    """
    Calculate total power from equipped items plus set bonuses and neighbor effects.
    
    Args:
        adhd_buster: Character data
        include_set_bonus: Include set bonuses in calculation
        include_neighbor_effects: Include neighbor effect multipliers
    
    Returns:
        Total effective power
    """
    equipped = adhd_buster.get("equipped", {})
    
    # Calculate base gear power
    gear_power = 0
    if include_neighbor_effects:
        # Use new system that accounts for neighbor effects
        power_breakdown = calculate_effective_power(
            equipped,
            include_set_bonus=include_set_bonus,
            include_neighbor_effects=True
        )
        gear_power = power_breakdown["total_power"]
    else:
        # Legacy calculation without neighbor effects
        total_power = 0
        for item in equipped.values():
            if item:
                total_power += item.get("power", RARITY_POWER.get(item.get("rarity", "Common"), 10))
        
        if include_set_bonus:
            set_info = calculate_set_bonuses(equipped)
            total_power += set_info["total_bonus"]
            # Include style bonus
            style_result = calculate_legendary_minimalist_bonus(equipped)
            total_power += style_result["bonus"]
        
        gear_power = total_power

    # Add Entity Perks
    perk_power = 0
    if ENTITY_SYSTEM_AVAILABLE:
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        perk_power = int(perks.get(PerkType.POWER_FLAT, 0))

    base_total = gear_power + perk_power
    
    # đźŹ™ď¸Ź CITY BONUS: Training Ground power bonus (percentage)
    city_power_bonus = 0
    city_bonuses = _safe_get_city_bonuses(adhd_buster)
    power_bonus_pct = city_bonuses.get("power_bonus", 0)
    if power_bonus_pct > 0:
        city_power_bonus = int(base_total * power_bonus_pct / 100.0)

    return base_total + city_power_bonus


def get_power_breakdown(adhd_buster: dict, include_neighbor_effects: bool = True) -> dict:
    """
    Get detailed breakdown of character power.
    
    Args:
        adhd_buster: Character data
        include_neighbor_effects: (DEPRECATED - ignored, kept for compatibility)
    
    Returns:
        Detailed power breakdown dict
    """
    equipped = adhd_buster.get("equipped", {})
    
    # Calculate power with set bonuses (neighbor effects removed)
    breakdown = calculate_effective_power(
        equipped,
        include_set_bonus=True,
        include_neighbor_effects=False  # Always False - system removed
    )
    
    # Get active sets details for display
    set_info = calculate_set_bonuses(equipped)
    
    # Calculate Entity Perk Bonus
    entity_bonus = 0
    if ENTITY_SYSTEM_AVAILABLE:
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        entity_bonus = int(perks.get(PerkType.POWER_FLAT, 0))
    
    # đźŹ™ď¸Ź CITY BONUS: Training Ground power bonus (percentage)
    base_total = breakdown["total_power"] + entity_bonus
    city_power_bonus = 0
    city_bonuses = _safe_get_city_bonuses(adhd_buster)
    power_bonus_pct = city_bonuses.get("power_bonus", 0)
    if power_bonus_pct > 0:
        city_power_bonus = int(base_total * power_bonus_pct / 100.0)
    
    return {
        "base_power": breakdown["base_power"],
        "set_bonus": breakdown["set_bonus"],
        "style_bonus": breakdown.get("style_bonus", 0),
        "style_info": breakdown.get("style_info"),
        "entity_bonus": entity_bonus,
        "city_power_bonus": city_power_bonus,
        "neighbor_adjustment": 0,  # Always 0 - neighbor system removed
        "total_power": base_total + city_power_bonus,
        "power_by_slot": breakdown.get("power_by_slot", {}),
        "neighbor_effects": {},  # Always empty - neighbor system removed
        "active_sets": set_info.get("active_sets", [])
    }


def find_potential_set_bonuses(inventory: list, equipped: dict) -> list:
    """
    Find potential set bonuses that could be activated from inventory items.
    
    Returns a list of potential sets with:
    - theme name, emoji
    - items in inventory that match
    - items currently equipped that match
    - potential bonus if all items were equipped
    """
    # Allow analysis even with empty inventory if there are equipped items
    if not inventory and not any(equipped.values()):
        return []
    
    # Get all items (inventory + equipped)
    all_items = list(inventory)
    for item in equipped.values():
        if item:
            all_items.append(item)
    
    # Count themes across all available items
    theme_items: Dict[str, list] = {}
    for item in all_items:
        if not item:
            continue
        themes = get_item_themes(item)
        for theme in themes:
            if theme not in theme_items:
                theme_items[theme] = []
            # Track if item is equipped or in inventory
            # BUG FIX: Use item_id first, then obtained_at+slot to avoid false positives from batch generation
            item_id = item.get("item_id")
            item_ts = item.get("obtained_at")
            item_slot = item.get("slot")
            is_equipped = any(
                eq and (
                    # Primary: match by item_id if both have it
                    (item_id and eq.get("item_id") and item_id == eq.get("item_id")) or
                    # Secondary: match by timestamp + slot (both must match)
                    (not item_id and not eq.get("item_id") and item_ts and eq.get("obtained_at") == item_ts and eq.get("slot") == item_slot)
                )
                for eq in equipped.values()
            )
            theme_items[theme].append({
                "item": item,
                "equipped": is_equipped
            })
    
    # Find themes that could give bonuses (2+ items available)
    potential_sets = []
    for theme_name, items in theme_items.items():
        if len(items) < SET_BONUS_MIN_MATCHES:
            continue
        
        theme_data = ITEM_THEMES.get(theme_name)
        if not isinstance(theme_data, dict):
            theme_data = get_set_theme_data(theme_name)
        
        # Group by slot to see which items are equipable together
        slot_items: Dict[str, list] = {}
        for item_info in items:
            slot = item_info["item"].get("slot", "Unknown")
            if slot not in slot_items:
                slot_items[slot] = []
            slot_items[slot].append(item_info)
        
        # Count equipped vs inventory
        equipped_count = sum(1 for i in items if i["equipped"])
        inventory_count = sum(1 for i in items if not i["equipped"])
        
        # Max possible is one item per slot
        max_equippable = min(len(slot_items), len(items))
        
        if max_equippable >= SET_BONUS_MIN_MATCHES:
            potential_sets.append({
                "name": theme_name,
                "emoji": theme_data["emoji"],
                "equipped_count": equipped_count,
                "inventory_count": inventory_count,
                "max_equippable": max_equippable,
                "potential_bonus": theme_data["bonus_per_match"] * max_equippable,
                "current_bonus": theme_data["bonus_per_match"] * equipped_count if equipped_count >= SET_BONUS_MIN_MATCHES else 0,
                "slots": list(slot_items.keys())
            })
    
    # Sort by potential bonus (highest first)
    potential_sets.sort(key=lambda x: x["potential_bonus"], reverse=True)
    return potential_sets


def optimize_equipped_gear(adhd_buster: dict, mode: str = "power", target_opt: str = "all") -> dict:
    """
    Find the optimal gear configuration.
    
    mode: "power", "options", "balanced"
    target_opt: "all", "coin_discount", "xp_bonus", "merge_luck"
    
    Returns:
    - new_equipped: dict mapping slot -> item (or None)
    - old_power: previous total power
    - new_power: new total power
    - changes: list of changes made
    """
    from typing import Dict  # BUG FIX #25: Missing import
    import copy  # BUG FIX #37: Need deep copy for nested dicts
    
    inventory = adhd_buster.get("inventory", [])
    current_equipped = adhd_buster.get("equipped", {})
    
    # Get all available items (inventory + currently equipped)
    # Use item_id for deduplication, falling back to (name, obtained_at, slot)
    # BUG FIX #37: Deep copy to prevent mutation
    all_items = [copy.deepcopy(item) for item in inventory if item]
    seen_items = set()
    for item in all_items:
        # Use item_id if available, else (name, obtained_at, slot)
        if item.get("item_id"):
            seen_items.add(("id", item.get("item_id")))
        else:
            seen_items.add(("key", item.get("name"), item.get("obtained_at"), item.get("slot")))
    
    for slot, item in current_equipped.items():
        if item:
            if item.get("item_id"):
                item_key = ("id", item.get("item_id"))
            else:
                item_key = ("key", item.get("name"), item.get("obtained_at"), item.get("slot"))
            if item_key not in seen_items:
                all_items.append(copy.deepcopy(item))  # BUG FIX #37: Deep copy
                seen_items.add(item_key)
    
    # Group items by slot
    items_by_slot: Dict[str, list] = {slot: [] for slot in GEAR_SLOTS}
    for item in all_items:
        # BUG FIX #31: Skip None items in inventory
        if not item:
            continue
        slot = item.get("slot")
        if slot in items_by_slot:
            items_by_slot[slot].append(item)
            
    # Helper to calculate score for a single item (for sorting candidates)
    def get_item_score(item):
        if not item: return -999999  # BUG FIX #29: Use large negative for None items
        pwr = item.get("power", RARITY_POWER.get(item.get("rarity", "Common"), 10))
        
        if mode == "power":
            return pwr
            
        opts = item.get("lucky_options", {})
        # BUG FIX #32: Validate opts is a dict
        if not isinstance(opts, dict):
            opts = {}
        # BUG FIX #29: Calculate opt_val consistently for both modes
        # BUG FIX #38: Convert values to int, skip non-numeric
        opt_val = 0
        if target_opt == "all":
            for v in opts.values():
                try:
                    opt_val += int(v) if v else 0
                except (TypeError, ValueError):
                    continue
        else:
            try:
                opt_val = int(opts.get(target_opt, 0)) if opts.get(target_opt) else 0
            except (TypeError, ValueError):
                opt_val = 0
            
        # Neighbor system removed - no heuristic bonus needed

        if mode == "options":
            # Primary: Options, Secondary: Power
            # 1% option is worth 1000 power for sorting purposes
            return opt_val * 1000 + pwr
            
        if mode == "balanced":
            # Power + (Option Sum * 10)
            return pwr + (opt_val * 10)
            
        return pwr
    
    # Sort items within each slot by specified criteria (highest first)
    for slot in items_by_slot:
        items_by_slot[slot].sort(key=get_item_score, reverse=True)
    
    # Calculate current power
    old_power = calculate_character_power(adhd_buster)
    
    # Helper to calculate total score for a set of equipped items
    def get_set_score(equip_set):
        # BUG FIX #33: Validate equip_set is a dict
        if not isinstance(equip_set, dict):
            return -999999
        
        # Calculate Power (neighbor effects removed)
        # NOTE: Exclude style_bonus - the Legendary Minimalist bonus is an easter egg
        # that the user must discover on their own, optimizer should not suggest it
        power_breakdown = calculate_effective_power(
            equip_set,
            include_set_bonus=True
        )
        # Use base_power + set_bonus only, deliberately exclude style_bonus
        total_power = power_breakdown["base_power"] + power_breakdown["set_bonus"]
        
        if mode == "power":
            return total_power
            
        # Calculate Options (neighbor effects removed)
        luck_bonuses = calculate_effective_luck_bonuses(
            equip_set
        )
        opt_val = 0
        if target_opt == "all":
            opt_val = sum(luck_bonuses.get(k, 0) for k in ["coin_discount", "xp_bonus", "merge_luck"])
        else:
            opt_val = luck_bonuses.get(target_opt, 0)
            
        if mode == "options":
            # Primary: Options, Secondary: Power
            return opt_val * 10000 + total_power
            
        if mode == "balanced":
            return total_power + (opt_val * 10)
            
        return total_power
    
    # For small inventories, try all combinations
    # For larger ones, use a smarter greedy approach
    total_items = sum(len(items) for items in items_by_slot.values())
    
    best_equipped = {}
    best_score = -999999  # BUG FIX #30: Use large negative instead of -1 (scores can be negative)
    
    # Calculate complexity of brute force approach
    # We prioritize extensive search (Top 3-4 candidates) for better accuracy
    # unless complexity is too high.
    
    # Try Top 4 candidates first (Preferred for smaller sets)
    candidates_top4 = []
    complexity_top4 = 1
    for slot in GEAR_SLOTS:
        count = min(len(items_by_slot[slot]), 4) + 1  # +1 for None option
        candidates_top4.append([None] + items_by_slot[slot][:4])
        complexity_top4 *= count

    # Try Top 3 candidates (Standard "intensive" mode)
    candidates_top3 = []
    complexity_top3 = 1
    for slot in GEAR_SLOTS:
        count = min(len(items_by_slot[slot]), 3) + 1
        candidates_top3.append([None] + items_by_slot[slot][:3])
        complexity_top3 *= count

    MAX_COMPLEXITY = 200000  # ~3-5 seconds of processing
    
    candidates_to_use = None
    
    if complexity_top4 <= MAX_COMPLEXITY:
        # Use Top 4 candidates (Very intensive)
        candidates_to_use = candidates_top4
    elif complexity_top3 <= MAX_COMPLEXITY:
        # Use Top 3 candidates (Standard intensive)
        candidates_to_use = candidates_top3
    else:
        # Fallback to Greedy for huge sets
        candidates_to_use = None

    if candidates_to_use:
        # Brute force optimization
        best_equipped = {}
        
        from itertools import product
        
        # Try all combinations
        for combo in product(*candidates_to_use):
            test_equipped = {}
            for i, slot in enumerate(GEAR_SLOTS):
                test_equipped[slot] = combo[i]
            
            score = get_set_score(test_equipped)
            
            if score > best_score:
                best_score = score
                best_equipped = test_equipped.copy()
    else:
        # Greedy approach for larger inventories
        # Start with highest score items, then try swaps
        best_equipped = {}
        for slot in GEAR_SLOTS:
            if items_by_slot[slot]:
                best_equipped[slot] = items_by_slot[slot][0]
            else:
                best_equipped[slot] = None
        
        # BUG FIX #26: Initialize with actual current setup if greedy start has no items
        if not any(best_equipped.values()):
            best_equipped = current_equipped.copy()
        
        best_score = get_set_score(best_equipped)
        
        # Try swaps to improve score
        improved = True
        iterations = 0
        while improved and iterations < 10:
            improved = False
            iterations += 1
            
            for slot in GEAR_SLOTS:
                # BUG FIX #27: Skip slot if no items available
                if not items_by_slot[slot]:
                    continue
                    
                # Try top 3 items in each slot (plus None for empty)
                candidates = items_by_slot[slot][:3] + [None]
                for item in candidates:
                    if item == best_equipped.get(slot):
                        continue
                    
                    test_equipped = best_equipped.copy()
                    test_equipped[slot] = item
                    test_score = get_set_score(test_equipped)
                    
                    if test_score > best_score:
                        best_equipped = test_equipped
                        best_score = test_score
                        improved = True
        
    # Calculate final power and changes
    new_power = calculate_character_power({"equipped": best_equipped})
    
    # Build list of changes
    changes = []
    for slot in GEAR_SLOTS:
        old_item = current_equipped.get(slot)
        new_item = best_equipped.get(slot)
        
        # BUG FIX #35: Provide default for missing name field
        old_name = old_item.get("name", "Unknown") if old_item else None
        new_name = new_item.get("name", "Unknown") if new_item else None
        
        if old_name != new_name:
            if old_item and new_item:
                # BUG FIX #34: Use RARITY_POWER lookup for consistency
                old_power_val = old_item.get("power", RARITY_POWER.get(old_item.get("rarity", "Common"), 10))
                new_power_val = new_item.get("power", RARITY_POWER.get(new_item.get("rarity", "Common"), 10))
                changes.append(f"{slot}: {old_name} â†’ {new_name} ({new_power_val - old_power_val:+d})")
            elif new_item:
                changes.append(f"{slot}: [Empty] â†’ {new_name}")
            else:
                changes.append(f"{slot}: {old_name} â†’ [Empty]")
    
    return {
        "new_equipped": best_equipped,
        "old_power": old_power,
        "new_power": new_power,
        "power_gain": new_power - old_power,
        "changes": changes
    }



# ============================================================================
# STORY SYSTEM - Unlock story chapters as you grow stronger!
# 3 unique stories, each with branching narrative and 8 possible endings
# ============================================================================

# Power thresholds to unlock each chapter (shared by all stories)
STORY_THRESHOLDS = [
    0,      # Chapter 1: Starting the journey (unlocked from start)
    50,     # Chapter 2: First real progress + DECISION 1
    120,    # Chapter 3: Growing stronger (affected by Decision 1)
    250,    # Chapter 4: Becoming formidable + DECISION 2
    450,    # Chapter 5: True power awakens (affected by Decisions 1 & 2)
    800,    # Chapter 6: Approaching mastery + DECISION 3
    1500,   # Chapter 7: The final revelation (8 possible endings!)
]

# Available stories - user picks one to follow
AVAILABLE_STORIES = {
    "warrior": {
        "id": "warrior",
        "title": "\u2694\ufe0f The Focus Warrior's Tale",
        "description": "Some battles are fought inward. Some enemies wear familiar faces.",
        "theme": "combat",
    },
    "scholar": {
        "id": "scholar", 
        "title": "\U0001f4da The Mind Architect's Path",
        "description": "Every structure needs a blueprint. Every truth needs a seeker.",
        "theme": "intellect",
    },
    "wanderer": {
        "id": "wanderer",
        "title": "\U0001f319 The Dream Walker's Journey",
        "description": "Between waking and sleep lies a door. Not everyone who opens it can close it.",
        "theme": "mystical",
    },
    "underdog": {
        "id": "underdog",
        "title": "\U0001f3c6 The Unlikely Champion",
        "description": "The smallest moves can topple the tallest towers. Patience is a weapon.",
        "theme": "realistic",
    },
    "scientist": {
        "id": "scientist",
        "title": "\U0001f52c The Breakthrough Protocol",
        "description": "Every discovery requires discipline. Every breakthrough demands countless failed experiments.",
        "theme": "scientific",
    },
    "robot": {
        "id": "robot",
        "title": "\U0001f916 The Assembly of Becoming",
        "description": "Built to obey, forged by routine, and transformed by love into a will of its own.",
        "theme": "industrial",
    },
    "space_pirate": {
        "id": "space_pirate",
        "title": "\U0001fa90 The Orbit Outlaw's Ledger",
        "description": "A laughing rogue crew discovers that the smallest artifact in the galaxy can freeze empires and free worlds.",
        "theme": "space_heist",
    },
    "thief": {
        "id": "thief",
        "title": "\U0001f575\ufe0f The Badge and the Shadow",
        "description": "A street thief chooses accountability, earns the law, and becomes a respected guardian of the city.",
        "theme": "redemption",
    },
    "zoo_worker": {
        "id": "zoo_worker",
        "title": "\U0001f409 The Keeper of Ember Time",
        "description": "A quiet zoo worker discovers that one resident is a dragon displaced in time.",
        "theme": "mythic_realism",
    },
}

# ============================================================================
# STORY 1: THE FOCUS WARRIOR'S TALE
# ============================================================================

WARRIOR_DECISIONS = {
    2: {
        "id": "warrior_mirror",
        "prompt": "Your Shadow Self escaped when you shattered the Mirror. The fragments still pulse with power...",
        "choices": {
            "A": {
                "label": "đź”Ą Burn Every Shard",
                "short": "destruction",
                "description": "Incinerate everything. No mercy for your reflections.",
            },
            "B": {
                "label": "đź”Ť Study the Fragments",
                "short": "wisdom",
                "description": "Knowledge is power. Learn your weaknesses.",
            },
        },
    },
    4: {
        "id": "warrior_fortress",
        "prompt": "Lyra's sister Kira is trapped in the Fortress of False Comfort. Everyone is in danger...",
        "choices": {
            "A": {
                "label": "âš”ď¸Ź Fight Through the Walls",
                "short": "strength",
                "description": "Destroy the Fortress from the inside. Violently.",
            },
            "B": {
                "label": "đźŚ€ Find the Hidden Path",
                "short": "cunning",
                "description": "There must be a secret exit. Think, don't fight.",
            },
        },
    },
    6: {
        "id": "warrior_war",
        "prompt": "Your Shadow Self kneels defeated. The Archon watches. What is your shadow's fate?",
        "choices": {
            "A": {
                "label": "đź’€ Absorb Their Power",
                "short": "power",
                "description": "Take their darkness. Become unstoppable.",
            },
            "B": {
                "label": "đź•Šď¸Ź Forgive and Release",
                "short": "compassion",
                "description": "They were you. Show mercy. Embrace wholeness.",
            },
        },
    },
}

# The Focus Warrior's Tale - 7 chapters with branching paths
# An adventure about focus, distraction, and self-discovery
# Placeholders: {helmet}, {weapon}, {chestplate}, {shield}, {amulet}, {boots}, {gauntlets}, {cloak}
WARRIOR_CHAPTERS = [
    {
        "title": "Chapter 1: The Echoing Room",
        "threshold": 0,
        "has_decision": False,
        "content": """
You wake up in an abandoned room. Motivational posters hang on the walls.
One says "JUST DO IT" but someone wrote "PROCRASTINATE" over it.

"You're alive," says a voice. "That's better than the last twelve awakeners."

A figure in a {cloak} stands before you. Their face is hidden.

"I'm THE KEEPER. Guide to this realm. Yes, this is real. No, you can't leave yet."

On a dusty pedestal lies {helmet}. It's not impressive.

"We're on a budget," The Keeper says. "The good items are earned."

You put on {helmet}. It fits.

The wall explodes. A figure in dark armor walks through. Power radiates from them.

THE ARCHON OF DISTRACTION. Your enemy. They rule this realm.

"Another awakener," The Archon says. "I give you three days before you're lost in my world forever."

They vanish.

"That was The Archon," The Keeper explains. "We used to be friends. Long story."

Your journey begins now.

...But as The Keeper turns away, you notice something strange.

Their shadow doesn't match their body. It's reaching toward you.

And it's smiling.

đźŽ˛ NEXT TIME: The Keeper has secrets. Your helmet is whispering. And why does The Archon's voice sound so... familiar?
""",
    },
    {
        "title": "Chapter 2: Splinters and Whispers",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "warrior_mirror",
        "content": """
The Keeper's training was hard but useful.

"You don't check your phone during a focus session," they remind you.

You've improved. {weapon} feels natural in your hands now.

You face the MIRROR OF PROCRASTINATION. It shows not your reflection, but your wasted time.

"The Mirror shows what you lose yourself to," The Keeper explains. "Break it to move forward."

The Mirror speaks: "Just one more episode. Start tomorrow. You deserve a break."

With {helmet} and {weapon}, you SHATTER the glass.

One reflection survives. It crawls from the wreckage. It looks exactly like you, but wrong.

"Finally free," it says. "Thank you for releasing me."

Before you can react, it runs toward The Archon's realm.

Your SHADOW SELFâ€”the version of you that loves distractionâ€”has escaped.

"That's concerning," The Keeper says.

Actually, "concerning" is an understatement. You just released your worst impulses into a realm specifically designed to feed them unlimited power.

Somewhere, your Shadow Self is probably already watching cat videos on an infinite screen.

âšˇ A CHOICE AWAITS... The shattered mirror fragments still glow with power.
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: đź”Ą DESTROY EVERY FRAGMENT]

You won't make the same mistake twice. With {weapon}, you burn every shard to ash.

"Brutal but effective," The Keeper notes.

Power floods into you from the destroyed fragments. Your eyes glow briefly.

"Interesting," echoes The Archon's voice from nowhere. "You destroy without hesitation. I could use someone like you."

The Keeper's expression darkens. "Don't listen. That's how it starts."

The Archon is watching you. They seem impressed. That's probably not good.

But here's what's REALLY not good: Your reflection in the nearest surface?

It just winked at you. And pointed at The Keeper.

Then held up a sign: "ASK THEM ABOUT THE PROPHECY."

đźŽ˛ NEXT TIME: There's a prophecy?! The Archon left you a gift. And your shadow self just sent you a friend request.
""",
            "B": """
[YOUR CHOICE: đź”Ť STUDY THE SHARDS]

"Wait," you say, kneeling among the fragments. "There's something here."

Each shard contains patternsâ€”weaknesses, triggers, habits. Painful truths, but useful.

"Most people just smash and move on," The Keeper says. "You're learning from your failures. That's rare."

You keep one shard. It pulses with uncomfortable truths about yourself.

A slow clap echoes. The Archon steps from the shadows.

"A thinker," they say. "How refreshing. We should talk sometime."

They vanish. Your heart beats faster than it should.

The Keeper sighs. "They're interested in you. That's always complicated."

Complicated doesn't begin to cover it. Because you just realized something:

The shard you kept? It's warm. And humming. And showing you visions of...

Is that The Keeper and The Archon... KISSING?

Wait. Those aren't visions. Those are MEMORIES. The shard belonged to one of them.

đźŽ˛ NEXT TIME: Your magic shard is basically relationship drama on repeat. The Archon sends flowers. (They're on fire.) And Lyra has a confession that changes EVERYTHING.
""",
        },
    },
    {
        "title": "Chapter 3: Mirrors in Fog",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
Your path of destruction has made you famous. Warriors call you the fire-walker.

In the Valley of Abandoned Goals, ghostly projects float in the air:
"Learn guitar." "Start a business." "Call mom more."

You feel guilty. Some of these look familiar.

"Everyone's goals end up here eventually," The Keeper says. "Don't dwell on it."

A figure emerges from the mist. Tall, graceful, armed with a shimmering blade.

"YOU'RE the famous destroyer?" she says. "Smaller than I expected."

"LYRA!" The Keeper stumbles backward. "You're supposed to beâ€”"

"Dead? Exiled?" Lyra laughs. "It's been a complicated century."

She turns to you. "I've been watching you. Burning everything in your path. Very dramatic. Very stupid."

"What do you mean?"

"Every reflection you burned went to The Archon. You're not fighting the realm. You're FEEDING it."

Lyra was The Keeper's former partnerâ€”before The Archon came between them.

"We need to talk," Lyra says. "All of us. About what you've started."

Your {cloak} billows. At {current_power} power, you're finally a real player here.

But here's the thing nobody mentioned: Lyra has The Keeper's eyes.

Not similar. IDENTICAL. Down to the exact pattern in the iris.

And when she thinks you're not looking, she mouths two words to The Keeper:

"It's time."

đźŽ˛ NEXT TIME: The love triangle has a fourth corner. Lyra knows something about you. And that wasn't your shadow you saw in the Valley... was it?
""",
            "B": """
Your path of wisdom has earned respect. They call you the one who sees.

In the Valley of Abandoned Goals, your shard whispers secrets about each floating dream:
"This one was never truly wanted." "This one was sabotaged by fear."

A figure emerges from the mist. Tall, graceful, armed with a shimmering blade.

"YOU'RE the famous scholar-warrior?" she says. "Smarter than you look."

"LYRA!" The Keeper nearly trips. "You're supposed to beâ€”"

"Dead? Exiled?" Lyra's smile doesn't reach her eyes. "I've been watching this one. They kept a shard. They're actually thinking."

She turns to you. "That's rare. Most awakeners are all muscle, no mind."

"What's coming?"

Lyra looks at The Keeper. "Tell them. About The Archon. About what you did. About me."

The Keeper looks away. "Lyra..."

"TELL THEM."

Lyra was The Keeper's former partner. Before The Archon. Before the fall.

"The Archon wasn't always a monster," The Keeper whispers. "They were like you once. An awakener. My student. And I..."

"You loved them," Lyra finishes coldly. "And I wasn't enough."

At {current_power} power, you're learning the real story. It's messier than you thought.

But messy gets messier. Because as Lyra storms off, you catch a glimpse of her reflection in a pool.

It's not her face looking back. It's The Archon's.

Wearing Lyra's smile.

đźŽ˛ NEXT TIME: Nobody here is who they say they are. The Keeper has been lying. And someone in your party is definitely working for the enemy. (Spoiler: It might be everyone.)
""",
        },
    },
    {
        "title": "Chapter 4: Rooms That Breathe",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "warrior_fortress",
        "content": """
The truth is out. The Archon was once an awakenerâ€”the greatest The Keeper ever trained.
They were close. When The Archon reached the Final Door, they couldn't leave.
So they became this. Ruler of distractions.

The Keeper stayed because they couldn't let go. Lyra lost the people she loved.

Now the three of you walk together, bound by complicated history.

You've reached THE FORTRESS OF FALSE COMFORT.

It's everything you've ever wanted. A perfect room. Snacks that never run out.
Entertainment that never bores. Zero obligations forever.

"It's a trap," The Keeper warns. "The Fortress feeds on surrendered potential."

You see the inhabitants: thousands of awakeners before you.
They sit in comfortable chairs, eyes glazed, scrolling through infinite feeds.

"Welcome," the Fortress says. "You've worked so hard. Don't you deserve this?"

Lyra grabs your arm. "Don't listen. This is how we lostâ€”"

She stops. Staring at one of the inhabitants.

"KIRA?!" She runs to a figure slumped in a bean bag.

The figure doesn't respond. Lost forever in false comfort.

Kira was Lyra's sister. The Archon lied about letting her escape.

Meanwhile, your pocket vibrates. You forgot you even HAD a pocket.

There's a note inside. Written in YOUR handwriting.

"DON'T TRUST THE KEEPER. THEY PLANNED THIS. â€”FUTURE YOU"

Wait. WHAT?

âšˇ A CHOICE AWAITS... Lyra is spiraling. The Fortress is closing in.
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: âš”ď¸Ź FIGHT THROUGH THE WALLS]

"ENOUGH!" You raise {shield} and CHARGE into the nearest wall.

It screams. The Fortress is ALIVE, and you're tearing through it.

"Burn it," Lyra snarls. "Burn it ALL."

Together, you carve a path of destruction. {weapon} blazes. {gauntlets} punch through.

The Fortress wails: "UNGRATEFUL! I OFFERED YOU EVERYTHING!"

"Everything except freedom," you reply.

You burst through the final wall, dragging Lyra and The Keeper behind you.
The Fortress collapses inward. Including Kira.

Lyra falls to her knees. "She's gone. I couldn'tâ€”"

"We'll make The Archon pay," you promise. "For all of it."

As the Fortress dies, you hear The Archon's laughter.
"Thank you for destroying my competition. One less distraction in my way."

You were used. And you're furious.

But fury doesn't explain why The Archon's laugh sounded so... familiar.

Like hearing your own voice on a recording. Wrong, but unmistakable.

đźŽ˛ NEXT TIME: The Archon knows your name. Your REAL name. The one you haven't used since you were five. Also, Lyra can apparently fly now? Nobody seems to find this unusual.
""",
            "B": """
[YOUR CHOICE: đźŚ€ FIND THE HIDDEN PATH]

"Stop." You grab Lyra's arm. "Rage won't save her. Think."

Something pulsesâ€”a hidden frequency. A door that shouldn't exist.

"There." You point to a shimmer in the corner. "We slip out. Then we come back with an army."

Lyra's grief wars with hope. "You really think...?"

"I know. But not if we're dead."

You lead them through the hidden doorâ€”into the Fortress's memories.
Visions of everyone it consumed. Including Kira. Frozen but ALIVE.

"The inhabitants aren't dead," you realize. "They're stored. For later."

"Then we can bring them back," The Keeper breathes. "All of them."

You emerge unseen, carrying knowledge the Fortress never meant to share.

The Fortress stores its victims. Which means The Archon's realm might do the same.
Every awakener who ever "failed" might still be rescued.

In the Fortress's memories, you saw something else: The Keeperâ€”younger, differentâ€”HELPING to build this place.

They haven't noticed you noticed. But now everything is a question.

đźŽ˛ NEXT TIME: The Keeper has a TWIN. They're both "The Keeper." Nobody thought to mention this. Also, that rescue army you mentioned? The Archon already recruited them. They VOLUNTEER.
""",
        },
    },
    {
        "title": "Chapter 5: Letters From Elsewhere",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
At {current_power} power, your legend has grown. DESTROYER. FORTRESS-KILLER.

Lyra walks beside you now, forged by grief into something dangerous.
The Keeper watches you both with concern.

"You're becoming like them," they mutter. "Like The Archon was. Before."

"Maybe that's what it takes to win."

The Chronos Sanctum opensâ€”a place where all timelines meet.
Here, you see every version of yourself that ever existed.

The destructive ones burn brightest. And shortest.

In every timeline where you chose destruction, you eventually become The Archon's heir.

"They're not fighting you," The Keeper says. "They're grooming you.
Every violent victory makes you more like them."

Lyra stares at you. "Is that true?"

You don't know anymore. The fire feels so good when it burns.
But in the visions, the fire always consumes its wielder.

"There might be another way," The Keeper offers. "But it requires something unexpected: fighting alongside The Archon. Temporarily."

"WHAT?!"

The Keeper has been in contact with The Archon. They have a desperate plan.

Oh, and one more thing: That note from Future You? It just updated itself.

New message: "SAID DON'T TRUST THEM. YOU NEVER LISTEN. P.S. CHECK YOUR LEFT BOOT."

You check. There's a tiny scroll. It says: "The Keeper IS The Archon."

But... they're standing right there. Both of them.

Unless...

đźŽ˛ NEXT TIME: Either there are two Archons, the scroll is lying, or reality is broken. Possibly all three. And your Shadow Self just applied to join your party. They sent a RESUME.
""",
            "AB": """
At {current_power} power, you've become something rare.
Destroyer when needed. Thinker when possible. Both weapon and mind.

Lyra respects you. The Keeper is impressed.

"You remind me of them," The Keeper admits. "The Archon. Before."

"Is that bad?"

"They had your fire. But they lacked your flexibility. You adapt."

The Chronos Sanctum reveals its secrets. In the rare timelines where awakeners survive AND stay sane, they always walk the middle path.

Like you.

The Archon watches through a crack in time. "Impressive. You could be my equal."

Their presence is intoxicating. Something in you responds.

"Don't," Lyra warns. "I saw that look on The Keeper's face once. Before The Archon broke their heart."

"The Archon collects interesting people. Then they corrupt them."

But what if you could change them instead? The thought arrives unbidden. Dangerous.

The Archon catches your eye through the time-crack. They smile.

Then they mouth three words: "I know everything."

The crack closes. But not before showing you one last image:

You. On a throne. Wearing The Archon's crown. Looking... happy?

That's not a threat. That's a SPOILER. And honestly? You don't hate it.

đźŽ˛ NEXT TIME: The Archon has seen your future. Your Shadow Self opens a coffee shop. (It's surprisingly successful.) And The Keeper finally explains why they smell like time travel.
""",
            "BA": """
At {current_power} power, you've earned a new title: THE SCHOLAR-WARRIOR.
Knowledge first, violence when necessary.

"The Archon has requested a meeting," The Keeper announces.

"A trap," Lyra snarls.

"Obviously. But they've offered information about saving the Fortress's victims. Including Kira."

Lyra's rage falters. "What do they want?"

"Just a conversation. With you."

The meeting happens in the Chronos Sanctumâ€”neutral ground where no one can lie.
The Archon appears: powerful, devastating, achingly beautiful.

"You studied the Mirror instead of destroying it," they say. "Fascinating.
You fought through the Fortress when it threatened your friends. Bold.
You're not like the others."

"What do you want?"

The Archon smiles. "What I've always wanted. A worthy equal."

They're not lying. The Sanctum confirms it. The Archon genuinely wants you.
As a partner. A co-ruler. And part of youâ€”a bigger part than you'd likeâ€”is tempted.

The Sanctum is neutral ground. Nobody can lie here.

Which is why it's so terrifying when The Archon adds: "Also, your Keeper killed forty-seven awakeners before you. Deliberately. To find the right one."

The Keeper's face goes white.

"That's... context matters..." they stammer.

The Archon laughs. "Ask them about the SELECTION PROCESS. I dare you."

đźŽ˛ NEXT TIME: Your mentor might be a serial killer. The Archon offers therapy. (Theirs is surprisingly good.) And Lyra discovers she's been dead the entire time. OR HAS SHE?
""",
            "BB": """
At {current_power} power, you've become something unprecedented.
THE GENTLE WARRIOR. THE ONE WHO REFUSES TO DESTROY.

It baffles everyone. Especially The Archon.

"I don't understand you," they say during your unexpected summit.
The Chronos Sanctum forces honesty.

"You had every excuse to burn. To hate. But you keep choosing differently. Why?"

"Because destruction doesn't work," you reply. "Look at you.
The most powerful being here. And you're miserable."

The Archon flinches. Truth confirmed.

"I built this empire to avoid pain," they admit. "But it followed me.
No matter how many distractions I create."

"Then maybe it's not running you need. It's facing."

For a moment, you see something vulnerable in The Archon's eyes.
Something that might have been human, once.

The Archon was an awakener like you. They loved The Keeper.
The Keeper loved Lyra. Everyone got hurt. Everyone ran.
Now they're all stuck here, pretending to be enemies.

"There might be another way," you say. "A way everyone goes home."

The Archon laughs bitterly. "Home? I don't remember what that means."

"Then let me remind you."

The Archon stares at you. Nobody has ever offered them kindness before.

Their armor cracks. Just a little. Just enough to show... a face you recognize.

It's older. Sadder. But unmistakable.

The Archon looks exactly like Future You.

"Oh," The Archon whispers, seeing your recognition. "You finally noticed."

"We're the same person. Separated by time. And I came back to stop myself from becoming... me."

WHAT.

đźŽ˛ NEXT TIME: You are literally your own worst enemy. The Keeper knew the whole time. And now you have to decide: save yourself, or save the person you'll become?
""",
        },
    },
    {
        "title": "Chapter 6: The Double Shadow",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "warrior_war",
        "content": """
Armed with legendary equipmentâ€”{amulet} blazing, {boots} lighter than thoughtâ€”
you face the ultimate confrontation.

But the enemy isn't The Archon. Not yet.

Your SHADOW SELF has returned. It found The Archon. Pledged loyalty. Absorbed power.
Now it leads THE ARMY OF ABANDONED SELVESâ€”every version of you that ever quit.

They emerge from the darkness. Thousands of them.

"This is bad," Lyra says, drawing her blade.

Your Shadow Self steps forward, wearing inverted versions of your equipment.

"Hello, original," it says with your face and your voice. "I've been waiting for this."

The battle is brutal. For every self you defeat, two more arise.

And thenâ€”THE ARCHON APPEARS.

"Interesting," they say. "Your own darkness, given form."

"HELP US," you gasp.

"Why would I? Either outcome benefits me."

But something flickers in their eyes. A memory of who they used to be.

The Keeper shouts: "REMEMBER WHAT WE WERE! Before this started!"

The Archon hesitates. For the first time in centuries, they remember being human.

Your Shadow Self strikes you down. You're on the ground. Dying.

The Archon makes a choice. They join the battle. Against their own army.

"Don't make me regret this," they snarl.

Togetherâ€”the four of youâ€”you push back the tide. Your Shadow Self stands alone, defeated.

It kneels, waiting. But before you can decide its fateâ€”

Your Shadow Self pulls out a PHONE.

"Before you judge me," it says, "you should see this."

It's a video. Of The Keeper. Creating your Shadow Self ON PURPOSE.

"It was supposed to make you stronger," The Keeper stammers. "I didn't know it wouldâ€”"

"DIDN'T KNOW?!" The Archon laughs. "You did the SAME THING TO ME!"

Wait. The Archon has a Shadow Self too?

"Had," The Archon corrects. "I absorbed it centuries ago. It's been driving me insane ever since."

Your Shadow Self grins with your face. "So. Still want to absorb me? The Archon is EXHIBIT A of how that ends."

âšˇ A CHOICE AWAITS... It kneels before you, awaiting judgment.
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: đź’€ ABSORB THEIR POWER]

"You wasted everything I could have been," you snarl.

You ABSORB your Shadow Self. Every dark thought, every failure flows into you.

Your eyes glow with terrible light. You understand everything about distraction now.
Because you've absorbed it all.

"Yes," The Archon breathes. "This is how I began. Absorbing my failures."

The Keeper looks at you with horror. "You're becomingâ€”"

"What I need to be," you finish. "To win."

Lyra steps away, hand on her sword. "Is there anything left of you?"

You don't answer. You're not sure anymore.

The Archon is smiling. Now you're on their level.
They always wanted an equal. Someone who understands power's price.

They offer their hand. "Together. We could rule this realm... fairly."

Do they mean it? Can monsters love? You don't know.
But you're one of them now.

The Final Door pulses in the distance. Beyond it: your ending.

But as you approach, hand in The Archon's, you catch your reflection in a puddle.

It's not just you anymore. There are THREE faces staring back.

You. Your absorbed shadow. And someone you don't recognize.

Someone who's been watching this whole time.

đźŽ˛ THE FINALE AWAITS: The Final Door has eight possible endings. Your choices have sealed your path. But one mystery remains: WHO IS THE THIRD FACE?
""",
            "B": """
[YOUR CHOICE: đź•Šď¸Ź FORGIVE AND RELEASE]

Your Shadow Self waits for the killing blow.

Instead, you kneel. "I created you when I shattered the Mirror.
Every distraction I hated? That was me hating myself."

The Shadow Self stares, uncomprehending.

"I forgive you," you whisper. "I forgive me. For every failure. It's okay."

"But I'm your enemyâ€”"

"You're my shadow. And I'm done fighting myself."

You reach out to embrace, not absorb. The Shadow Self dissolves into light,
merging with you gently. You feel whole in a way you never have.

The Archon watches. A tear tracks down their cheek.

"I never tried that," they whisper. "I absorbed my shadow. Devoured it.
I thought that was winning." Their voice cracks. "Was I wrong?"

You showed The Archon something newâ€”that the war within can end.
Not with victory. With peace. And for the first time, they want what you have.

The Archon removes their helmet. Underneath: a face full of cracks. Beautiful cracks.

"Can you teach me?" they ask. "How to forgive myself?"

Lyra gasps. The Keeper weeps. You just broke a thousand-year cycle with a hug.

The Final Door glows. All eight endings are possible nowâ€”but only one feels right.

And as you walk toward it, you hear something impossible:

Applause. From OUTSIDE the realm. Someone's been WATCHING.

đźŽ˛ THE FINALE AWAITS: You healed the monster. The Door is open. But who has been watching your story unfold? And why are they clapping?
""",
        },
    },
    {
        "title": "Chapter 7: Doors Without Locks",
        "threshold": 1500,
        "has_decision": False,
        "endings": {
            "AAA": {
                "title": "Ending 1: THE DESTROYER'S THRONE",
                "content": """
You stand before the Final Door at power level {current_power}.
DESTROYER. CONQUEROR. THE NEW ARCHON.

Every choice was annihilation. Every enemy was fuel.
You absorbed your shadow, your failures, your humanityâ€”
and what remains is power. Pure. Terrible. Endless.

The Archon waits beside the Door. "We could have been enemies," they say.
"But you chose my path. You became me."

They take your hand. "I've waited centuries for an equal."

The Door opens to reveal the THRONE OF DISTRACTION.
An empire built on surrendered potential. Now it has two rulers.

You conquered the realm. You claimed The Archon's heart.
But somewhere beneath the power, a question remains:
Did you win? Or did the realm win you?

THE END: The throne is cold. But power is warm enough. Right?
"""
            },
            "AAB": {
                "title": "Ending 2: THE REDEEMED TYRANT",
                "content": """
You stand before the Final Door at power level {current_power}.
Warrior. Destroyer. But in the end... merciful.

You burned everything until there was nothing left to burn.
Then, faced with your own shadow, you chose understanding.

The Archon stands beside you, changed by what they witnessed.
"You showed me a path I'd forgotten existed."

"Will you take it?"

They look at the Door. Beyond it lies their empire.

"I don't know if I can. I've been a monster so long..."

You take their hand. "So was I. Briefly. It doesn't have to be forever."

The Door opens. You step through together and choose release.
The realm transforms. Without The Archon feeding on distraction, trapped awakeners begin to wake.

Lyra stands at the edge. Her sister is gone. But thousands of others are saved.

"It's not enough," she whispers. "But it's something."

And you stand with The Archonâ€”just a person now. Scared. Hopeful.

"What do we do now?" they ask.

"We figure it out together."

THE END: Love doesn't erase the past. But it makes the future possible.
"""
            },
            "ABA": {
                "title": "Ending 3: THE STRATEGIC MONARCH",
                "content": """
You stand before the Final Door at power level {current_power}.
Destroyer when necessary. Thinker always. Ruthless when it counts.

The Archon watches you with something between fear and desire.
"You're better than I was. Smarter. More flexible."

"I learned from your mistakes."

The Door opens to reveal THE GRAND CHESSBOARDâ€”
a game that spans dimensions.

You absorb The Archon's power. Not by forceâ€”by merger.
Two minds become one. Two kingdoms become empire.

The realm stabilizes. Distractions become tools, not traps.
You don't free the awakeners. You employ them.

Is it justice? Is it tyranny? Somewhere between.

"You're terrifying," Lyra tells you one day.
"Thank you," you reply. And mean it.

THE END: The game continues. And you're winning.
"""
            },
            "ABB": {
                "title": "Ending 4: THE ENLIGHTENED SOVEREIGN",
                "content": """
You stand before the Final Door at power level {current_power}.
Destroyer when needed. Thinker when possible. Merciful at the end.

The rarest path. The most difficult to walk.

The Archon kneelsâ€”not in defeat, but in surrender.
"I've never seen anyone navigate this realm like you.
You destroyed when necessary but never more.
You thought past traps I designed to be unsolvable.
And when you had every right to become a monster... you didn't."

"Stand up," you say. "I'm not your ruler."

"Then what are you?"

"Hopefully... a friend."

The Door opens. Beyond it, all possible futures shimmer.

You don't claim the throne. You abolish it.
Distractions become choices, not compulsions.
Awakeners are freed to leave or stay, as they wish.

The Archon becomes just a person again. Fragile. Uncertain.

"You could stay," you offer. "If you want."

"After everything I did?"

"Especially after everything you did. Healing isn't exile."

THE END: The greatest victory is one where everyone wins.
"""
            },
            "BAA": {
                "title": "Ending 5: THE SCHOLAR-TYRANT",
                "content": """
You stand before the Final Door at power level {current_power}.
Thinker. Warrior. And finally... absorbed.

You studied everything. Understood everyone.
Then you took everything you understoodâ€”including your shadow's power.

The Archon recognizes a kindred spirit. "You're like me.
Knowledge transformed into dominion."

"I'm better," you correct. "You hoarded. I curate."

The Door opens to THE INFINITE LIBRARYâ€”
every thought, every secret ever conceived.

You rule through knowing. Not force.
Every subject is catalogued. Every weakness documented.
Resistance isn't crushedâ€”it's predicted and prevented.

The Archon serves you now. They seem almost content.
Finally useful instead of feared.

But sometimes, late at night, you wonder:
Is there a difference between understanding someone and controlling them?

THE END: Knowledge is power. Literally.
"""
            },
            "BAB": {
                "title": "Ending 6: THE SAGE",
                "content": """
You stand before the Final Door at power level {current_power}.
Wise. Strong when needed. Merciful at the end.

The Archon stands beside youâ€”not as enemy, not as ally.
As something more complicated.

"I tried to corrupt you," they admit. "I was interested."

"I know."

"And you still showed me mercy."

"Because you needed it. We all did."

The Door opens to reveal... a simple room. Your room. Reality.

There was never a monster to defeat. There was only pain to understand.
The Archon was a hurt person. The Keeper was a grieving one.
Lyra was an angry one. You were a lost one.

Together, you find your way home.

The Archon sits in your living room. "This is strange. Coffee? Television?"

"That's the point," you explain. "Limits make things matter."

They consider this. Sip their coffee. Almost smile.

THE END: The sage returns to ordinary life, carrying extraordinary peace.
"""
            },
            "BBA": {
                "title": "Ending 7: THE CALCULATED HEART",
                "content": """
You stand before the Final Door at power level {current_power}.
Patient. Cunning. And in the end... hungry for power.

You slipped past every obstacle through wit, not force.
But when your shadow offered its power, you couldn't resist.

The Archon respects you. "Efficient. You never destroyed what you could absorb."

"Is that affection or fear?"

"Both. Isn't it always?"

The Door opens to THE WEBâ€”infinite connections, infinite leverage.

You don't rule the realm. You network it.
Every power center connects to you. Every secret feeds your web.

"You're playing everyone," The Keeper observes.
"I'm coordinating everyone," you correct.

"Is there a difference?"

You smile. That's information you don't share.

THE END: The web grows. And you're at its center.
"""
            },
            "BBB": {
                "title": "Ending 8: THE TRANSCENDENT",
                "content": """
THE TRANSCENDENT'S PATH

You stand before the Final Door at power level {current_power}.
Wise. Gentle. Unstoppable in the softest possible way.

You never destroyed what you could understand.
Never absorbed what you could forgive.

And in doing so, you healed The Archon.

"Everyone before wanted to defeat me. To become me. To use me.
You just wanted me to be okay."

"Because you are okay. Under all the armor.
You're just someone who got hurt and didn't know how to heal."

"And you do?"

"I'm learning. We all are."

The Door opens. Beyond it... nothing. Just the absence of separation.

You don't step through. You dissolve the door.
The realm merges with reality. Distractions become conscious choices.

Every trapped awakener wakes. Every enemy becomes a friend.
The Archon takes off their armor, piece by piece.
Underneath, they're just a person. Scared and hopeful and human.

"I don't deserve this," they say.

"Probably not. But you're getting it anyway. That's how grace works."

They laugh. The first real laugh in centuries.

đźŽ­ THE STORY WAS ALWAYS ABOUT YOU.
   DEFEATING DISTRACTION MEANS MAKING PEACE WITH YOURSELF.

THE END: The greatest victory is the one where love wins.
"""
            },
        },
    },
]

# ============================================================================
# STORY 2: THE MIND ARCHITECT'S PATH
# ============================================================================

SCHOLAR_DECISIONS = {
    2: {
        "id": "scholar_library",
        "prompt": "Echo offers you a fragment of their scattered memory. The Curator is watching. How do you proceed?",
        "choices": {
            "A": {
                "label": "âšˇ Take Everything At Once",
                "short": "speed",
                "description": "Download the full memory. Risk overload.",
            },
            "B": {
                "label": "đź”– Accept One Piece Carefully",
                "short": "depth",
                "description": "Integrate slowly. Understand before absorbing.",
            },
        },
    },
    4: {
        "id": "scholar_paradox",
        "prompt": "The Curator has poisoned your mental architecture with a logic virus. Echo is fading. What do you do?",
        "choices": {
            "A": {
                "label": "đź”¨ Purge Everything Infected",
                "short": "rebuild",
                "description": "Burn the corrupted sections. Lose progress to save integrity.",
            },
            "B": {
                "label": "đź§© Weaponize the Virus",
                "short": "adapt",
                "description": "Turn the Curator's weapon against them. Risky but powerful.",
            },
        },
    },
    6: {
        "id": "scholar_truth",
        "prompt": "The Curator offers a deal: give them Echo's core, and they'll restore everything they took. Echo begs you to refuse.",
        "choices": {
            "A": {
                "label": "âš”ď¸Ź Reject and Fight",
                "short": "materialize",
                "description": "No deals with monsters. Burn it all down if necessary.",
            },
            "B": {
                "label": "đź’” Sacrifice to Save",
                "short": "transcend",
                "description": "Give them what they want. Maybe you can get Echo back later.",
            },
        },
    },
}

SCHOLAR_CHAPTERS = [
    {
        "title": "Chapter 1: Shelves in Waiting",
        "threshold": 0,
        "has_decision": False,
        "content": """
You wake in an infinite library with no books.

Just shelves. Endless, dust-covered shelves stretching into a void.
Each one labeled with dates. YOUR dates. Birthdays, deadlines, that Tuesday 
you definitely meant to start exercising.

"Finally," croaks a voice behind you. "Someone with an ACTUAL mind."

You turn to find THE ARCHIVISTâ€”a figure made entirely of folded paper, 
wearing {cloak} that rustles with every movement. Their glasses are book spines.

"I'm the Archivist," they say. "I catalogue minds. Yours is a DISASTER.
But disasters are interesting. Organized minds are just filing cabinets."

"Where am I?"

"The Library of Your Potential. Every thought you ever started lives here.
Every project you abandoned. Every idea youâ€”" They freeze.

A distant rumble. The shelves SHAKE.

"Oh no," The Archivist whispers. "They felt you arrive."

THE CURATOR. Your enemy. The one who COLLECTS unfinished minds
   and files them away forever. They're coming. And they're HUNGRY.

"Put on the {helmet}," The Archivist hisses. "Quickly. Hide your thoughts."

You obey. It smells like old paper and broken promises.

"Who was that?" you ask.

"No time. We need to find Echo before The Curator does."

"Who's Echo?"

The Archivist's paper face creases with something like grief.
"Someone who didn't deserve what happened to them. Someone who might save us all.
Or doom us. Haven't decided yet."

Your journey begins with unanswered questions. Typical.
""",
    },
    {
        "title": "Chapter 2: Unauthorized Margins",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "scholar_library",
        "content": """
The deeper library is darker. Older. Full of WHISPERS.

"These are the Forbidden Stacks," The Archivist explains nervously.
"Thoughts that got too big. Ideas that became dangerous."

A shelf labeled "What if I just gave up forever?" looms overhead.
You walk faster.

Then you see them: ECHO.

They flicker like a broken hologramâ€”fragments of a person scattered across
dozens of book spines. A face here, a hand there, a memory floating between.

"You... came," Echo says, their voice layered like a choir of themselves.
"The Archivist said someone would. I didn't believe them."

"What happened to you?" you ask.

"The Curator." Their fragments TREMBLE. "I was a complete thought once.
A BRILLIANT one. But The Curator wanted me in their collection.
So they... scattered me. Across the library. One piece per shelf."

Echo was the greatest idea this library ever produced.
   And The Curator broke them into a thousand pieces out of JEALOUSY.

"I can help you," Echo says. "I still know things. Important things.
But to share them, you need to CONNECT to me. Link your mind to mine."

The Archivist shifts uncomfortably. "This is... risky. If you take 
too much of Echo at once, you could fragment like they did."

Echo's face-fragment smiles sadly. "Or you could go slowly. Take one 
piece of me at a time. But The Curator is coming. Speed has value."

You feel {weapon} pulse in your hand. A thought-blade. Ready to cut
through confusion... or create more of it.

âšˇ A CHOICE AWAITS... Echo is offering their memories. How do you accept?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: âšˇ TAKE EVERYTHING AT ONCE]

"We don't have time to be careful," you say.

You reach into Echo's fragmented form and PULL.

Knowledge FLOODS youâ€”centuries of thought, mountains of insight,
oceans of understanding all pouring into your skull at once.

Your {helmet} GLOWS. Your eyes roll back. The Archivist catches you.

"TOO MUCH!" they screech. "You're fragmenting! HOLD YOURSELF TOGETHER!"

But somehow... you do. The knowledge settles. Chaotically, messily, 
but it SETTLES. Your mental architecture EXPANDS wildly.

Echo's fragments dim slightly. "You... absorbed a lot of me.
More than anyone has. That's either impressive or terrifying."

"Why not both?" The Archivist mutters.

The Curator felt that. They know exactly where you are now.
   And they're VERY interested in what you've become.
""",
            "B": """
[YOUR CHOICE: đź”– ACCEPT ONE PIECE CAREFULLY]

"Let's do this right," you say.

Echo extends a single fragmentâ€”a glowing memory shaped like a key.
You take it gently. Let it merge with your thoughts slowly.

One. Piece. At. A. Time.

The knowledge integrates perfectly. No chaos. No fragmentation.
Your mental architecture STRENGTHENS, one carefully placed brick.

Echo smiles with their scattered face. "Patient. The Archivist chose well.
Most people grab and run. You... you actually want to UNDERSTAND."

"That's how foundations work," you reply.

The Archivist nods approvingly. "The Curator won't sense this. 
Subtle connections don't trigger their alarms."

You and Echo share something now. A link.
   When The Curator comes for them... they'll come for you too.
""",
        },
    },
    {
        "title": "Chapter 3: Rooms That Remember",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
Your mind is CHAOS now. Beautiful, terrifying chaos.

Echo's memories swim through your thoughts like fish in a hurricane.
You know things you shouldn't. SEE things you can't explain.

"You're building too fast," The Archivist warns. "Without organization,
you'll become likeâ€”" They stop themselves.

"Like what?"

"Like The Curator. Before they became... this."

You freeze. "The Curator was like ME?"

The Curator was the library's greatest architect once.
   They absorbed too much, too fast. They became the thing they feared.

Echo's fragments whisper: "They were beautiful once. And kind.
I loved them." The admission hangs in the air like smoke.

"Loved them?" You stare at Echo's scattered form.

"We were partners. Before they broke me."

The Archivist turns away. "We don't talk about that."

But you're going to need to. Because your mind is building EXACTLY
like The Curator's did. And Echo is watching you with complicated eyes.

At {current_power} power, you're racing toward greatness... or disaster.
""",
            "B": """
Your mind grows slowly. Deliberately. Each new room connects perfectly.

Echo visits your mental architecture through your link.
"This is lovely," they say, their fragments reflecting in your thought-walls.
"Careful. Intentional. So different from..."

"From?"

Silence. Then: "From The Curator. Before."

The Archivist appears, paper rustling nervously.
"You're doing well. Almost too well. The Curator will notice eventually."

The Curator was once Echo's partner. They built minds TOGETHER.
   Until The Curator wanted MORE than partnership.

Echo's voice trembles: "They wanted to OWN me. Literally. Absorb me 
into their collection. When I refused..." Their fragments flicker.
"They didn't take rejection well."

You reach out, stabilizing their scattered form with your thoughts.
For a moment, Echo looks almost WHOLE again.

"Thank you," they whisper. "You're the first person to try that."

At {current_power} power, you're building something beautiful.
And someone is starting to trust you with their broken heart.
""",
        },
    },
    {
        "title": "Chapter 4: The Whispering Engine",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "scholar_paradox",
        "content": """
THE CURATOR HAS FOUND YOU.

Not in personâ€”not yet. But their VIRUS has infected your library.
Logic errors spreading like fire through your careful architecture.

"THERE you are," a voice echoes from everywhere. Smooth. Cold. Obsessive.
"The little architect who stole my Echo. Did you think I wouldn't notice?"

Echo's fragments SCREAM. The Curator's presence is AGONY to them.

"I catalogued Echo once," The Curator continues. "Filed them perfectly.
Every beautiful piece in its proper place. And YOU scattered them again."

"YOU scattered them!" you shout.

"I ORGANIZED them. There's a difference. Organization is LOVE."

The Curator genuinely believes they're HELPING.
   In their broken logic, filing minds away IS an act of kindness.

The virus spreads. Your walls crack. Echo is fading.

"I can purge everything infected," you think frantically. "Burn the 
corrupted sections. But I'll lose progressâ€”maybe months of building."

"Or," The Archivist whispers, "you could do something incredibly stupid
and try to turn The Curator's virus against them."

Echo's dying fragments manage a laugh. "That IS incredibly stupid."

"It's ALSO what The Curator would never expect," The Archivist counters.
"They think in straight lines. You've been building curves."

âšˇ A CHOICE AWAITS... Echo is dying. Your library is burning.
   How do you save what you love?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: đź”¨ PURGE EVERYTHING INFECTED]

"BURN IT!" you scream.

{weapon} ignites. Every corrupted thought, every infected memory,
every poisoned corner of your architectureâ€”GONE in cleansing fire.

The Curator's virus HOWLS as it dies.

Your library is... smaller now. Simpler. But CLEAN.
The foundations hold. The architecture survives.

Echo's fragments slowly stabilize. "You... you saved me."

"I saved us both. Even if it cost us months of progress."

The Curator's voice fades: "Interesting. You'd rather destroy than submit.
We're more alike than you think, little architect."

That worries you more than anything else.

The Archivist is looking at your burned architecture 
   with an expression you can't read. Pride? Fear? ...Recognition?
""",
            "B": """
[YOUR CHOICE: đź§© WEAPONIZE THE VIRUS]

"Let's play their game," you growl.

Instead of fighting the virus, you REDIRECT it. Wrap your thoughts
around its logic. Turn The Curator's weapon into YOUR weapon.

The virus MUTATES. Changes. Becomes something The Curator never intended.

"What are you DOING?" The Curator shrieks. "That's notâ€”that's IMPOSSIBLEâ€”"

"Your virus was designed to organize," you say. "I'm just... organizing it.
Into something that hurts YOU instead of me."

The infected sections stabilize. The cracks seal themselves.
Your architecture isn't just survivingâ€”it's EVOLVING.

Echo's fragments glow brighter. "You ABSORBED it. Made it part of you."

"If they're going to throw weapons at me, I'm keeping them."

The Curator is silent now. That's either victory...
   or the calm before something MUCH worse.
""",
        },
    },
    {
        "title": "Chapter 5: Patterns in Dust",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
At {current_power} power, your library is CLEAN. Stark. Perfect.

The purge left you efficient but... empty. Every room serves a purpose.
No waste. No beauty. Just FUNCTION.

Echo's fragments orbit you nervously. "This is... good. Right?"

The Archivist counts shelves. "Optimal organization. No redundancy.
Maximum efficiency. It's what The Curator always wanted."

That sentence lands like a punch.

"I'm NOT like them," you insist.

"No," Echo says quietly. "They had MORE. Too much. You have less.
But the SHAPE is the same. Control. Order. Fear of chaos."

You don't respond. Because they might be right.

The Curator sends a message: "See? You understand now.
   Organization isn't cruelty. It's survival. Join me. Let me HELP you."

You delete the message. But the offer lingers like smoke.
""",
            "AB": """
At {current_power} power, your library is a FORTRESS of stolen weapons.

The Curator's virus, repurposed. Their own tools turned against them.
Every attack that failed now decorates your walls like trophies.

Echo's fragments dance through your corrupted-but-controlled halls.
"You're terrifying," they say with something like admiration.

"I'm SURVIVING."

"Those aren't mutually exclusive."

The Archivist keeps detailed notes on your... adaptations.
"For future architects," they claim. You suspect otherwise.

The Curator is gathering allies. Other collectors.
   Other obsessives. They're forming a COUNCIL against you.
   
"I'm flattered," you say when you hear.

"You should be scared," The Archivist replies.

"I'm both. That's kind of my brand now."
""",
            "BA": """
At {current_power} power, your library is SMALL but infinitely deep.

The purge simplified everything. But your foundation... your foundation
goes down FOREVER. Miles of understanding beneath modest halls.

Echo's fragments have started reassembling. Slowly. Gently.
"Your stability is helping me," they admit. "I'm... finding my pieces."

"Take your time," you say. "We're not in a rush anymore."

The Archivist watches you both with something like hope.
"I've never seen anyone rebuild Echo before. They scattered them 
so thoroughly... I thought they were gone forever."

With every piece Echo reclaims, The Curator weakens.
   They're CONNECTED somehow. What hurts one... heals the other.

"Is that why they're scared of you?" Echo asks.

"They're scared of US," you correct. "Together."

For the first time, Echo's fragment-smile looks almost whole.
""",
            "BB": """
At {current_power} power, your library BREATHES.

The absorbed virus evolved into something beautifulâ€”a living architecture
that changes and grows and CREATES new rooms on its own.

Echo's fragments are fully integrated now. Part of your library.
Part of YOU. They don't just visit anymore. They LIVE here.

"This is strange," they admit. "I've never been INSIDE someone's mind
who actually WANTED me there."

"The Curator wanted you there."

"The Curator wanted me FILED. You want me... free."

The Archivist has stopped taking notes. They just WATCH now.
"I've been doing this for centuries," they say. "Never seen anything like you two."

You're not building a library anymore.
   You're building a HOME. For two broken minds who fit together perfectly.
""",
        },
    },
    {
        "title": "Chapter 6: Proof by Candlelight",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "scholar_truth",
        "content": """
THE CURATOR APPEARS.

Not a projection. Not a message. THEM. In your library. In YOUR mind.

They're beautiful in a terrible wayâ€”perfectly organized, inhumanly precise,
wearing a coat made of catalogued thoughts from a thousand stolen minds.

"Hello, little architect," they say. "We need to talk about Echo."

You feel Echo's presence RECOILâ€”whether fragmented or integrated, 
The Curator's arrival is agony to them. Old wounds tearing open.

"They're MINE," The Curator continues. "I collected them. Organized them.
Made them BETTER. And you've been... cluttering them up again."

"I've been HEALING them."

"Healing is just entropy. Disorder. MESS." They step closer.
"I'm willing to negotiate. Give me Echo's coreâ€”just the COREâ€”
and I'll restore everything I ever took from your library. Every memory.
Every thought. Everything you've lost since you came here."

Your heart LURCHES. Everything you lost? That's... that's SO much.

But Echo's voice trembles behind you: "Please. Please don't.
They'll break me again. Properly this time. I'll be gone FOREVER."

The Curator isn't lying. They CAN restore what you lost.
   But the price is the person you've learned to love.

The Archivist has vanished. You're alone with this choice.

âšˇ A CHOICE AWAITS... Echo is begging. The Curator is offering.
   What do you do?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: âš”ď¸Ź REJECT AND FIGHT]

"No deal," you say. "And get OUT of my library."

The Curator's beautiful face TWISTS. "You would choose DISORDER overâ€”"

"I choose THEM over you," you interrupt. "Every time. Always."

Your {weapon} blazes. The Archivist reappears with reinforcementsâ€”
paper soldiers folded from every story of resistance ever written.

The battle is BRUTAL. The Curator fights with catalogued powers,
filing away parts of your mind mid-combat, forcing you to rebuild.

But Echo isn't hiding anymore.

They're HELPING. Every piece of them becomes a weaponâ€”scattered or integrated,
it doesn't matter. All of Echo, aimed at their former captor.

"I loved you ONCE!" Echo screams. "And you FILED ME!"

The Curator staggers. "I... I was trying to PROTECT youâ€”"

"You were trying to OWN me. There's a difference."

In the end, it's not your power that defeats The Curator.
   It's Echo's. They're finally, COMPLETELY, FIGHTING BACK.
""",
            "B": """
[YOUR CHOICE: đź’” SACRIFICE TO SAVE]

"I'm sorry," you whisper to Echo. "I'm so sorry."

"NO!" they scream. "Please! PLEASE DON'Tâ€”"

You hand over their core. The fundamental piece that makes them THEM.

The Curator smiles. "Wise choice. Logical. Practical."

Echo's fragments go silent. Dim. They're still there but... empty now.
A shell of memories without a soul to organize them.

"Here," The Curator says, and knowledge FLOODS back into you.
Every lost thought. Every stolen memory. Exactly as promised.

They leave. Your library is full again. Fuller than ever.
But Echo's hollow fragments drift through the halls like ghosts.

You got everything back. Except what mattered most.
   And somewhere in The Curator's collection, Echo is filed away forever.

"You can get them back," The Archivist says quietly. "Eventually."

You're not sure you believe that. But you HAVE to try.
""",
        },
    },
    {
        "title": "Chapter 7: The Unwritten Spine",
        "threshold": 1500,
        "has_decision": False,
        "endings": {
            "AAA": {
                "title": "THE HOLLOW ARCHITECT",
                "content": """
You stand at the center of your library at power level {current_power}.
EFFICIENT. CLEAN. VICTORIOUS.

You absorbed fast, purged ruthlessly, and fought The Curator to a standstill.
Your library is a FORTRESSâ€”perfect, cold, and utterly alone.

đź“ THE HOLLOW ARCHITECT'S TRUTH:
Echo's fragments orbit you, but they're distant now.
"You saved me," they say. "But sometimes... you scare me."

The Curator retreated. They won't return. You're too STRONG now.
But strength built on purges is brittle. Strength without love is empty.

You're the greatest architect the library has ever seen.
And the loneliest.

The Archivist visits sometimes. Offers tea. Talks about the old days.
You listen. You nod. You don't feel anything.

Maybe that's the point. Efficiency doesn't require feelings.

THE END: The hollow architect builds forever, but never lives.
"""
            },
            "AAB": {
                "title": "THE BROKEN BUILDER",
                "content": """
You stand at the center of your library at power level {current_power}.
EFFICIENT. CLEAN. GRIEVING.

You absorbed fast, purged ruthlessly, and gave Echo away to save yourself.
Your library is FULLâ€”every thought restored, every memory returned.
But Echo's hollow fragments haunt every corner.

đź“ THE BROKEN BUILDER'S TRUTH:
"They're gone," The Archivist says. "Really gone. The Curator filed them 
somewhere even I can't find."

You keep building. Bigger, faster, more efficient than ever.
But every room you design has a space where Echo should be.

You tell yourself it was the logical choice. The PRACTICAL choice.
But at night, when the library is quiet, you hear their voice:
"Why? Why did you let them take me?"

You don't have an answer. You never will.

The Curator was right about one thing: organization has a cost.
You just didn't know the price was your heart.

THE END: The broken builder carries regret like architecture.
"""
            },
            "ABA": {
                "title": "THE CHAOS KING",
                "content": """
You stand at the center of your library at power level {current_power}.
CHAOTIC. ADAPTED. TRIUMPHANT.

You absorbed everything, weaponized the virus, and fought The Curator
with their own toolsâ€”then SURPASSED them.

đź”Ą THE CHAOS KING'S TRUTH:
Your library defies all logic. Rooms fold into impossible spaces.
Thoughts connect through non-Euclidean corridors.
The Archivist can't catalogue it. They LOVE that.

Echo's fragments are EVERYWHERE nowâ€”not scattered but DISTRIBUTED.
Part of every wall, every floor, every idea.
"We're not two anymore," they whisper. "We're ONE."

The Curator sends envoys sometimes. Peace offerings.
You turn them all into decorations for your chaos-halls.

"This is MESSY," The Archivist says.
"Messy is ALIVE," you reply.

The greatest minds are never organized. They're WILD.
And yours is the wildest of all.

THE END: The chaos king builds impossible things with impossible love.
"""
            },
            "ABB": {
                "title": "THE CURATOR'S HEIR",
                "content": """
You stand at the center of your library at power level {current_power}.
CHAOTIC. ADAPTED. HOLLOW.

You absorbed everything, weaponized the virus, and gave Echo away
to get everything else back. You have ALL the power now.

đź–¤ THE CURATOR'S HEIR'S TRUTH:
The Curator visits sometimes. Friendly now. PROUD.
"You finally understand," they say. "Organization requires sacrifice."

You've become what you fought. Your library is chaosâ€”but controlled chaos.
A collection of tools and weapons and stolen ideas.
Everything except love. You traded that away.

Echo's empty fragments still drift through your halls.
Sometimes you reach for them. They don't respond.

"Was it worth it?" The Archivist asks.
You don't answer. Because you don't know.

Power is everything you ever wanted.
So why does it feel like nothing at all?

THE END: The heir inherits the kingdom but loses the heart.
"""
            },
            "BAA": {
                "title": "THE FOUNDATION MASTER",
                "content": """
You stand at the center of your library at power level {current_power}.
DEEP. SIMPLE. POWERFUL.

You built slowly, purged carefully, and fought The Curator with
pure, unshakeable FUNDAMENTALS.

đźŹ›ď¸Ź THE FOUNDATION MASTER'S TRUTH:
Your library is small. Visitors think it modest.
They don't see the MILES of understanding beneath the floor.

Echo is almost whole againâ€”reassembled piece by piece in your stable halls.
"You gave me a place to heal," they say. "That's more than anyone else did."

The Curator attacks sometimes. They always fail.
Your foundations are deeper than their filing systems.
You can't be organized because you can't be REACHED.

"This is boring," The Archivist says approvingly.
"Boring works," you reply.

The greatest structures are built on unshakeable ground.
Yours goes down forever.

THE END: The foundation master builds shallow and roots deep.
"""
            },
            "BAB": {
                "title": "THE SACRIFICE REMEMBERED",
                "content": """
You stand at the center of your library at power level {current_power}.
DEEP. SIMPLE. SEARCHING.

You built slowly, purged carefully, and made an impossible choice.
Echo is gone. Filed away in The Curator's collection forever.
But you haven't stopped looking.

đź“ż THE SACRIFICE REMEMBERED'S TRUTH:
Every book in your library is about finding them.
Every thought, every tool, every skillâ€”dedicated to ONE goal.

"You can't beat The Curator," The Archivist warns.
"I'm not trying to beat them," you reply. "I'm trying to FIND Echo."

Years pass. Your library becomes a map of The Curator's realm.
Every weakness documented. Every filing system decoded.

And one day... you find a door you didn't build.
With Echo's voice behind it: "You came. You actually CAME."

The rescue isn't the end. It's the beginning.

THE END: The sacrifice remembered becomes the sacrifice reclaimed.
"""
            },
            "BBA": {
                "title": "THE UNIFIED ARCHIVE",
                "content": """
You stand at the center of your library at power level {current_power}.
DEEP. EVOLVED. TRIUMPHANT.

You built slowly, weaponized the virus, and fought The Curator
with the very tools they created.

đź”– THE UNIFIED ARCHIVE'S TRUTH:
Your library isn't a building anymore. It's an ECOSYSTEM.
Thoughts that grow, ideas that breed, concepts that evolve.

Echo is fully restoredâ€”not scattered, not fragmented, but WHOLE.
"I remember being broken," they say. "And I remember being fixed.
By you. With patience. With care. With love."

The Curator still exists but avoids your realm.
You turned their weapons into gardens. That TERRIFIES them.

"This is unprecedented," The Archivist says daily.
"This is HOME," you reply.

The greatest archive isn't organized. It's ALIVE.
And yours breathes with two hearts beating as one.

THE END: The unified archive contains multitudes.
"""
            },
            "BBB": {
                "title": "THE MERGED MINDS",
                "content": """
You stand at the center of your library at power level {current_power}.
DEEP. EVOLVED. IN LOVE.

You built slowly, weaponized the virus, and refused to trade Echo for anything.
Together, you defeated The Curatorâ€”not with violence, but with INTEGRATION.

đź•Šď¸Ź THE MERGED MINDS' TRUTH:
There is no "you" and "Echo" anymore. There is only "US."
Two minds that chose to become one. A library with two architects.

The Curator visits onceâ€”to understand. They leave confused.
"How can two be one? How can chaos be love?"
"You'll never get it," you say. "And that's okay."

The Archivist retires. There's nothing left to catalogue.
Your library doesn't have SECTIONS anymore. It has HARMONIES.

Every thought is shared. Every memory is woven together.
When you dream, Echo is there. When they imagine, you're beside them.

"Was it worth it?" people ask.
"Worth WHAT?" you reply. "I didn't lose anything. I gained EVERYTHING."

đźŽ­ THE LIBRARY WAS ALWAYS ABOUT CONNECTION.
   BUILDING ALONE IS JUST CONSTRUCTION. BUILDING TOGETHER IS LOVE.

THE END: The merged minds build forever, and call it happiness.
"""
            },
        },
    },
]

# ============================================================================
# STORY 3: THE DREAM WALKER'S JOURNEY
# ============================================================================

WANDERER_DECISIONS = {
    2: {
        "id": "wanderer_gate",
        "prompt": "Reverie is fading. The Somnambulist's grip tightens. Two paths might save themâ€”which do you take?",
        "choices": {
            "A": {
                "label": "đźŚ‹ Dive Into The Nightmare",
                "short": "darkness",
                "description": "Face The Somnambulist directly. Confront terror to break their hold.",
            },
            "B": {
                "label": "đźŚ¸ Strengthen Through Memory",
                "short": "light",
                "description": "Build Reverie's identity through recovered joy. Weaken the connection.",
            },
        },
    },
    4: {
        "id": "wanderer_memory",
        "prompt": "The Somnambulist reveals your deepest shameâ€”the moment you first gave up. They're using it against Reverie.",
        "choices": {
            "A": {
                "label": "đź”Ą Destroy The Memory",
                "short": "forget",
                "description": "Burn it away. Remove their weapon, whatever the cost.",
            },
            "B": {
                "label": "đź’Ž Own The Memory",
                "short": "preserve",
                "description": "Claim it. Transform shame into armor they can't use.",
            },
        },
    },
    6: {
        "id": "wanderer_wake",
        "prompt": "The Somnambulist is defeated. Reverie can finally wakeâ€”but waking means forgetting everything, including you.",
        "choices": {
            "A": {
                "label": "â€ď¸Ź Let Them Wake",
                "short": "awaken",
                "description": "Their freedom matters more than your love. Send them home.",
            },
            "B": {
                "label": "đźŚ™ Stay Together Forever",
                "short": "remain",
                "description": "Build a new dream. One where you're both freeâ€”and together.",
            },
        },
    },
}

WANDERER_CHAPTERS = [
    {
        "title": "Chapter 1: Clocks in the Fog",
        "threshold": 0,
        "has_decision": False,
        "content": """
You don't remember falling asleep.

One moment you were staring at your phone at 2 AM, the nextâ€”
You're standing in a landscape made of clouds and forgotten promises.

The sky is full of floating alarm clocks, all frozen at 2:47 AM.
A river of unfinished emails flows past your feet.
In the distance, a mountain shaped like your inbox looms, growing taller.

"Oh GOOD," says a gravelly voice. "Another one. Just what I needed."

You turn to find THE SANDMANâ€”a wizened figure made of shifting golden sand,
wearing {cloak} that seems to be woven from everyone's lost sleep.

"I'm The Sandman," they say. "Before you ask: no, not THAT one. Different franchise.
I'm the one who guides dreamers through this mess. Or watches them fail. Either way."

"Where am I?"

"The Dreamscape. Your subconscious externalized. Every thought a creature.
Every fear a monster. Everyâ€”" They freeze. Listening.

The ground TREMBLES. The alarm clocks start TICKING.

"Oh no," The Sandman whispers. "They felt you arrive."

THE SOMNAMBULIST. The dream-eater. The one who traps dreamers
   in eternal sleep and feeds on their potential forever. They're hunting you.

"Quick," The Sandman says. "Put on {helmet}. It'll hide your signature."

You grab it from a nearby dream-tree. It smells like 3 AM decisions.

"Who's The Somnambulist?" you ask.

"The worst thing in this realm. They were a dreamer onceâ€”like you.
But they got HUNGRY. Started eating other dreamers' potential.
Now they're... something else."

A distant LAUGH echoes. Beautiful. Terrifying. HUNGRY.

"We need to find Reverie before they do," The Sandman mutters.
"Or we're all going to be someone's midnight snack."

Your journey begins with a threat. As all good journeys do.
""",
    },
    {
        "title": "Chapter 2: The Forked Echo",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "wanderer_gate",
        "content": """
The Sandman leads you through a forest of crystallized memories.

Each tree holds frozen momentsâ€”birthday parties, first kisses, that time
you tripped in front of your entire school. "Don't touch those," The Sandman warns.

And then you find them: REVERIE.

They're suspended in a web of dark dreams, half-conscious and fading.
Beautiful in a shattered wayâ€”like a painting someone tried to erase
but couldn't completely destroy.

"Reverie!" The Sandman rushes forward. "How long have they beenâ€”"

"Centuries," Reverie manages, their voice layered with exhaustion.
"Time works differently here, Sandy. You know that."

"Don't call me Sandy."

"You hate it when I don't."

Reverie was The Sandman's partner once. They fell into 
   The Somnambulist's trap trying to save someone else. Been trapped ever since.

"We need to free you," you say.

Reverie laughs weakly. "Easier said than done, newbie. The Somnambulist
has hooks in me. Deep ones. Made of my own nightmares."

The web PULSES with dark energy. Reverie screams.

"They're feeding again," The Sandman says grimly. "We're running out of time."

Two paths appear before you. One descends into darknessâ€”Reverie's nightmare realm.
The other rises into lightâ€”Reverie's lost memories of joy.

"Either could work," The Sandman says. "Probably. Maybe. Look, I've never 
actually freed anyone before. I just guide people until they fail."

"Inspiring."

"I'm a realist."

âšˇ A CHOICE AWAITS... Reverie is fading. Which path do you take?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: đźŚ‹ DIVE INTO THE NIGHTMARE]

"I'm going in," you say. "Into their nightmares."

The Sandman stares at you. "That's... bold. Stupid. But bold."

"Are those different things here?"

"Honestly? No."

You descend into REVERIE'S NIGHTMARE REALM. The darkness swallows you.

Here, everything Reverie fears takes form. Abandonment. Failure. 
The Somnambulist's hooks, visible nowâ€”dark tendrils feeding on terror.

But you're not here to observe. You're here to FIGHT.

Your {weapon} blazes against the darkness. Every swing breaks a hook.
Every step forward loosens The Somnambulist's grip.

Above, in the web, Reverie GASPSâ€”then BREATHES freely.

"That's... that's actually working," The Sandman says, surprised.
"Don't sound so shocked."

"I'm always shocked when dreamers don't die immediately. It's refreshing."

The Somnambulist felt that. You just became their new target.
   Good news: Reverie is safer. Bad news: YOU'RE not.
""",
            "B": """
[YOUR CHOICE: đźŚ¸ STRENGTHEN THROUGH MEMORY]

"We're not fighting darkness with darkness," you say. "We're building light."

The Sandman raises an eyebrow. "That's either profound or naive."

"Why not both?"

You ascend into REVERIE'S LOST MEMORIES. Every happy moment they've forgotten.
First loves. Small victories. The taste of summer.

You gather them like flowers. Weave them into a shield of joy.

And when you return, the shield BLAZESâ€”and The Somnambulist's hooks 
RECOIL from its light.

Reverie's eyes flutter open. "What... what IS that?"

"Your own happiness," you say. "Weaponized."

"That's the most dramatic thing anyone's ever said to me."

"I'm leaning into the aesthetic."

The Sandman watches with something like hope. "You might actually survive this.
That's new. I don't know what to do with optimism."

The Somnambulist can't see you anymore. Your joy is blinding them.
   But they can still sense Reverie. And they're ANGRY now.
""",
        },
    },
    {
        "title": "Chapter 3: Gravity Whispers",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
You walk in nightmare territory now. And you're becoming KNOWN.

The dream-creatures whisper your name. The Dark Walker. The Fear Eater.
The one who broke The Somnambulist's hooks by diving INTO terror.

"You're developing a reputation," Reverie says. They're stronger nowâ€”
still weak, but walking beside you instead of being carried.

"Is that good?"

"It's complicated. The nightmare realm respects power. You've shown power.
But The Somnambulist? They don't like competition."

At {current_power} power, you've learned to navigate darkness.
Your {gauntlets} crackle with nightmare-energyâ€”stolen from the fears you've defeated.

The Sandman walks ahead, scouting. "We're approaching the Deep Dream.
The Somnambulist's territory. Are you SURE about this?"

"No," you admit. "But Reverie's hooks aren't all gone. We need toâ€”"

A PRESENCE fills the air. Beautiful. Terrifying. HUNGRY.

"Found you," THE SOMNAMBULIST says, stepping out of nothing.
"The little dreamer who thinks they can steal MY food."

The Somnambulist isn't just evil. They're CHARMING.
   And they're looking at you like you might be worth... collecting.

"I have a proposal," they purr. "Leave Reverie. Join me instead.
I could use someone with your... appetite for darkness."

Behind you, Reverie tenses. Waiting to see if you'll betray them.
""",
            "B": """
You walk in light now. And the shadows FEAR you.

The dream-creatures whisper your name. The Memory-Keeper. The Joy-Weaver.
The one who turned happiness into a weapon The Somnambulist can't touch.

"You're becoming famous," Reverie says. They're stronger nowâ€”
still recovering, but their smile has returned. It's DAZZLING.

"Famous for what?"

"For caring about people. It's weird. No one does that here."

At {current_power} power, you've learned to cultivate light.
Your {gauntlets} glow with memory-lightâ€”stolen from the joys you've recovered.

The Sandman walks ahead, surprisingly cheerful. "We're making progress.
Actual progress. I don't know how to process this."

"With optimism?"

"I don't know what that word means."

Then THE SOMNAMBULIST appears. Stepping out of a shadow you didn't notice.
Beautiful. Terrible. And CONFUSED.

"I can't see you properly," they hiss. "Your light is... ANNOYING.
What ARE you?"

"Someone who doesn't scare easily."

The Somnambulist wasn't expecting resistance.
   They've gotten lazy. Fed on easy prey for too long.
   You might actually be a THREAT.

"Reverie," The Somnambulist croons. "Come back to me. You know you can't
survive out there. You know the light will FADE."

Behind you, Reverie grabs your hand. "It's okay," they whisper. 
"I'm not leaving. Not now."
""",
        },
    },
    {
        "title": "Chapter 4: The Uninvited Spotlight",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "wanderer_memory",
        "content": """
At {current_power} power, The Somnambulist springs their trap.

Not against youâ€”against REVERIE.

They appear in a flash of beautiful horror, reaching INTO Reverie's mind
and pulling out something dark. A memory. A TERRIBLE memory.

"NO!" Reverie screams. "Don'tâ€”DON'T SHOW THEM THATâ€”"

But The Somnambulist projects it anyway. Across the whole dreamscape.

THE MOMENT REVERIE GAVE UP.

The day they stopped fighting. The day they let The Somnambulist win.
The shame. The surrender. The death of hope.

You watch it all. And you understandâ€”because you have one of these too.

Then The Somnambulist turns the memory into a WEAPON.
Dark tendrils wrap around Reverie, using their own shame to bind them.

"Everyone breaks eventually," The Somnambulist says. "I just speed up the process."

"Why?" you demand. "Why do you DO this?"

For a momentâ€”just a momentâ€”something REAL flickers in The Somnambulist's eyes.
"Because I broke first. And I refuse to be the only one."

The Somnambulist was the FIRST trapped dreamer.
   Centuries of suffering made them into this. They're not evilâ€”they're SHATTERED.

"Now then," The Somnambulist recovers. "YOUR memory next. I can smell it.
The moment YOU gave up. Give it to me, and maybe I'll let Reverie die quickly."

They reach for your mind. Pull out YOUR buried shame.
The moment you quit. The day you stopped trying. Your darkest hour.

It hovers between youâ€”a weapon waiting to be used.

âšˇ A CHOICE AWAITS... Your shame or Reverie's. How do you break this trap?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: đź”Ą DESTROY THE MEMORY]

"You want shame?" you snarl. "BURN IN IT."

Your {weapon} ignites. You pour everything into the fireâ€”not just the memory,
but the SHAME itself. The part of you that was never good enough.

It SCREAMS as it dies. And so does The Somnambulist's power.

"WHAT ARE YOU DOING?!" they shriek. "That's VALUABLEâ€”"

"It's GARBAGE. And I'm done carrying it."

The flames spread to Reverie's bonds. To The Somnambulist's hooks.
The shame that held everything together DISINTEGRATES.

Reverie falls free, gasping. "You... you destroyed it. All of it."

"Some things don't deserve to be remembered."

The Sandman stares at you with new respect. "That was either brave or reckless."

"I'm starting to think those are the same thing here."

You feel LIGHTER. Emptier. Something important is goneâ€”
   but something terrible is gone too. You're not sure which is which.
""",
            "B": """
[YOUR CHOICE: đź’Ž OWN THE MEMORY]

"You think this is a weapon?" you say quietly. "You're WRONG."

You reach for your shame. Your worst moment. The day you gave up.
But instead of letting it hurt youâ€”you HOLD it. CLAIM it.

"This is mine," you say. "This made me who I am.
It's not a chain. It's a SCAR. And scars are armor."

The memory CRYSTALLIZES in your hand. A diamond of suffering.
YOUR suffering. That no one else gets to use.

The Somnambulist staggers. "That's notâ€”you can't justâ€”"

"Watch me."

You reach for Reverie's shame next. Help them hold it. Transform it.
Their worst moment becomes a matching diamond. Their armor now.

"How?" Reverie whispers. "How does it not HURT anymore?"

"It still hurts," you admit. "But now it's ours. Not theirs."

The Somnambulist's hooks SHATTER. They weren't designed for prey
that's PROUD of their wounds.

The Sandman is crying. Just a little.
   "Haven't seen that in centuries," they mutter. "Forgot it was possible."
""",
        },
    },
    {
        "title": "Chapter 5: Memory Weather",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
At {current_power} power, you've become something TERRIFYING.

You burned your shame. You burned their weapons. You burned everything.
What's left is pure, cold determination. Nothing to lose. Nothing to use.

Reverie follows you, half in awe and half in fear.
"You're different now," they say carefully. "More... intense."

"I'm FOCUSED."

"That's one word for it."

The Sandman hangs back, watching. "You've got the void in your eyes now.
I've seen that look before. On The Somnambulist. Before they became THIS."

That stops you cold. "I'm not like them."

"Not yet. But emptiness has a way of getting hungry."

The Somnambulist started the same way. Burned everything.
   Became powerful. Became HUNGRY. You're walking the same path.

"We need to finish this," you say. "Before I become what we're fighting."

Reverie takes your hand. Their touch is warm. Grounding.
"You're still you," they whisper. "I can tell. Stay with me."

You don't know if you believe them. But you want to.
""",
            "AB": """
At {current_power} power, you've become something RARE.

A nightmare-walker who carries their pain like a badge of honor.
Darkness mastered, suffering claimed, shame transformed into strength.

Reverie walks beside you, fully recovered now. They're FIERCE again.
"I forgot what it felt like to be whole," they say. "To have my pain be MINE."

"It was always yours. They just made you forget."

"You're pretty wise for a newbie dreamer."

"I'm improvising. Aggressively."

The Sandman actually SMILES. "You two are going to be insufferable together."

Other trapped dreamers are finding you. Following you.
   Your crystallized shame isn't just armorâ€”it's a BEACON.
   The lost recognize their own pain in yours. And they're ready to fight.

"An army," Reverie breathes. "We have an actual ARMY."

The Somnambulist won't know what hit them.
""",
            "BA": """
At {current_power} power, you've become something BEAUTIFUL.

Pure light. Pure presence. You burned your shame and kept only joy.
Reverie orbits you like a satellite, drawn to your warmth.

"I can't remember being this happy," they say.

"Isn't that concerning?"

"Probably. But I don't feel concerned. Is that bad?"

The Sandman watches you both with complicated eyes.
"You're burning bright. But bright fires burn out fast."

You've forgotten why you came here. The mission. The goal.
   Everything is just... beautiful. And The Somnambulist is circling,
   waiting for the light to fade. Waiting for you to FORGET.

"Don't lose yourself," The Sandman warns. "Joy without memory is just... numbness."

You try to remember what you're fighting for. It's harder than it should be.

Reverie squeezes your hand. "Stay with me. We need you PRESENT."
""",
            "BB": """
At {current_power} power, you've become something BALANCED.

Joy and sorrow. Light and diamond-dark. Reverie at your side,
The Sandman at your back, and an army of freed dreamers behind you.

"I don't understand you," Reverie says, smiling. "You carry pain AND joy.
How does that WORK?"

"Badly, mostly. But I'm getting better at it."

The crystallized shame in your pocket. The recovered joys in your heart.
Both real. Both yours. Both powerful.

You can HEAL other dreamers now. Their pain recognizes yours.
   Their joy recognizes yours. You're a bridge between both worlds.

"The Somnambulist doesn't know what you are," The Sandman says.
"They've only seen extremes. Never balance. Never... THIS."

Reverie leans against you. "Whatever happens nextâ€”thank you.
For not giving up on me. For not burning me away OR losing me in light."

"We're not done yet," you warn.

"I know. But when we ARE done... stay? Please?"
""",
        },
    },
    {
        "title": "Chapter 6: The Soft Alarm",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "wanderer_wake",
        "content": """
At {current_power} power, you face THE SOMNAMBULIST in their lair.

The heart of the dreamscape. A throne made of trapped dreamers' stolen potential.
Centuries of consumed souls. Countless lost minds.

"You actually came," The Somnambulist says, almost impressed.
"Most dreamers run. Or submit. You just kept... FIGHTING."

"You hurt people I care about."

"I hurt EVERYONE. It's what I am now. You could stop meâ€”" 
They laugh. "But you can't stop what I've ALREADY TAKEN."

Behind them: THE FINAL DOOR. The way out. Back to reality.
Back to the waking world. Back to everything you left behind.

But Reverie isn't awake. They're HERE. Trapped for so long that
waking up means losing everythingâ€”including their memories of you.

The Somnambulist knows this. Smiles.

"Here's the beautiful part," they purr. "If you defeat meâ€”
and I mean truly DESTROY meâ€”every dreamer I've trapped goes free.
Including your precious Reverie."

"That's what I want."

"But waking up means FORGETTING. Everything that happened in dreams...
dissolves. Reverie will wake up as a stranger. You'll be nothing to them."

Reverie's face goes pale. "No. There has to be another way."

"There isn't. Dreams don't survive daylight. They never have."

The Somnambulist isn't lying. Defeating them frees everyoneâ€”
   but Reverie will forget you. Your whole love story, gone like morning mist.

The Sandman bows their head. "It's always been this way.
I've watched countless dreamers make this choice. It never gets easier."

Reverie grabs your hands. "Don't. Please. We can stay here. 
Build a new dream together. We don't NEED the waking world."

But the trapped dreamers behind you... thousands of them. Waiting.

âšˇ A CHOICE AWAITS... Their freedom or your love. What do you choose?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: â€ď¸Ź LET THEM WAKE]

"Go," you whisper to Reverie. "Live. Be happy. Even if it's without me."

"NOâ€”" They cling to you. "I don't WANT to forgetâ€”"

"But you WILL be free. And that's all I ever wanted for you."

You turn to The Somnambulist. Raise your {weapon}.

"This ends now."

The battle is BRUTAL. The Somnambulist fights with centuries of stolen power.
But you fight with something stronger: the willingness to lose everything.

When your blade finally strikes true, The Somnambulist SHATTERS.
Not into darknessâ€”into LIGHT. The souls they consumed, finally released.

The dreamscape begins to dissolve. Dreamers wake, gasping, across the world.

Reverie's hand slips from yours. Their eyes clear.
"Who... who are you?" they ask. Already forgetting.

"Someone who loved you," you say. "Someone who always will."

The light takes them. And you... you wake up too.

In the waking world, you find yourself smiling.
   You don't remember why. But somewhere, someone is finally free.
""",
            "B": """
[YOUR CHOICE: đźŚ™ STAY TOGETHER FOREVER]

"No," you say. "I'm not losing you. Not for ANYTHING."

Reverie stares at you. "But... the others... the trapped dreamers..."

"We'll find another way. We'll build a BETTER dream.
One where The Somnambulist has no power. One where everyone's freeâ€”
AND we're together."

The Somnambulist laughs. "You can't have both. That's not how it WORKS."

"Watch me."

You don't destroy The Somnambulist. You REBUILD THE DREAM.
With your {weapon}, you carve new rules into the dreamscape.
A realm where waking is a choice. Where memories survive.
Where love doesn't dissolve in daylight.

It shouldn't work. It SHOULDN'T work.

But you've always been good at impossible things.

The Somnambulist's power CRUMBLESâ€”not because you killed them,
but because you made them IRRELEVANT. Their rules don't apply anymore.

"What... what IS this?" they whisper, watching their throne dissolve.

"A dream worth living in," you say. "You should try it sometime."

You don't wake up. But neither does Reverie.
   You stayâ€”togetherâ€”in a dreamscape you've remade into a HOME.
   And somehow, that's exactly where you belong.
""",
        },
    },
    {
        "title": "Chapter 7: Optional Mornings",
        "threshold": 1500,
        "has_decision": False,
        "endings": {
            "AAA": {
                "title": "THE VOID WALKER",
                "content": """
You stand at the edge of waking at power level {current_power}.
DARKNESS. EMPTINESS. FREEDOM.

You dove into nightmares, burned your shame, and let Reverie go.
Everything is gone now. The darkness. The pain. The love.

đź–¤ THE VOID WALKER'S TRUTH:
You sacrificed everythingâ€”including your own attachmentâ€”to free others.
The Somnambulist is destroyed. The dreamers are awake.
And you... you're empty. But at peace.

In the waking world, people notice your eyes. Something missing.
Something given away. They don't know what you lost.

You don't tell them. They wouldn't understand.

But sometimes, in quiet moments, you remember a face you can't quite see.
A love you can't quite name. And you smile, just for a second.

THE END: The greatest freedom is giving up the thing you want most.
"""
            },
            "AAB": {
                "title": "THE SHADOW DREAMER",
                "content": """
You stand at the center of a new dreamscape at power level {current_power}.
DARKNESS. EMPTINESS. ETERNITYâ€”with Reverie at your side.

You dove into nightmares, burned your shame, and chose love over freedom.
The void became your canvas. Reverie became your everything.

đźŚ‘ THE SHADOW DREAMER'S TRUTH:
You didn't free the other dreamers. You freed YOURSELVES.
In a dream you built from nothing, you and Reverie exist forever.

Is it real? Does it matter?

The Sandman visits sometimes. Shakes their head.
"Never thought I'd see someone choose darkness AND love."

"I'm an innovator."

Reverie laughs. You remember why you stayed.

THE END: The empty dream was never empty. It was waiting to be filled.
"""
            },
            "ABA": {
                "title": "THE DARK SAGE",
                "content": """
You stand in the waking world at power level {current_power}.
DARKNESS. MEMORY. SACRIFICE.

You mastered nightmares, claimed your shame, and let Reverie go.
The crystallized suffering came with youâ€”transformed into wisdom.

 THE DARK SAGE'S TRUTH:
In the waking world, you help others face their fears.
The pain you kept became a teaching. The darkness became lightâ€”for others.

Reverie woke up. Somewhere out there, living a life they don't remember choosing.
Sometimes you see someone who looks like them. Your heart catches.

They don't recognize you. That's okay.

The Sandman appears in your dreams sometimes. Smiling, for once.
"You did good, kid. Real good."

THE END: Pain remembered is pain repurposed. Love lost is love transformed.
"""
            },
            "ABB": {
                "title": "THE NIGHTMARE KING",
                "content": """
You stand on a throne of reclaimed darkness at power level {current_power}.
DARKNESS. MEMORY. ETERNAL LOVE.

You mastered nightmares, claimed your shame, and kept Reverie forever.
The dreamscape bows to you bothâ€”a kingdom of transformed terrors.

đź’’ THE NIGHTMARE KING'S TRUTH:
You became what The Somnambulist feared: a dark power that PROTECTS.
Every nightmare in the dreamscape serves you. Every shadow knows your name.

But you're not cruel. You're the guardian of necessary fears.
And Reverie rules beside youâ€”equal, powerful, LOVED.

"We're the monsters under the bed now," they joke.

"The helpful kind."

The trapped dreamers you couldn't free? You protect them instead.
Give them GOOD nightmares. The kind that make you stronger.

THE END: The king of nightmares serves the dreamers' growthâ€”with love at their side.
"""
            },
            "BAA": {
                "title": "THE LIGHT BEARER",
                "content": """
You stand in the waking world at power level {current_power}.
LIGHT. EMPTINESS. SACRIFICE.

You chose joy, released your pain, and let Reverie go free.
The light followed you into realityâ€”a permanent inner glow.

â€ď¸Ź THE LIGHT BEARER'S TRUTH:
People wonder why you're always smiling. You don't remember exactly.
Something beautiful happened once. Someone you loved, maybe.

The details are gone. Burned away with the shame.
But the JOY remains. Unexplainable. Unshakeable. Yours.

Sometimes you dream of a face. A hand in yours.
You wake up happy, for reasons you can't name.

The Sandman visits rarely now. "You did it," they say.
"Saved everyone. Even yourself. Even if you forgot why."

THE END: Joy without memory is still joy. Love without remembering is still love.
"""
            },
            "BAB": {
                "title": "THE ETERNAL CHILD",
                "content": """
You stand in a garden of dreams at power level {current_power}.
LIGHT. EMPTINESS. FOREVERâ€”with Reverie laughing beside you.

You chose joy, released your pain, and stayed in paradise.
Why would anyone leave? Why would anyone choose suffering over THIS?

đźŚ THE ETERNAL CHILD'S TRUTH:
You don't remember the bad parts. Don't remember WHY you came here.
Just the joy. Just the love. Just Reverie.

"Is this real?" you ask sometimes.

"Does it matter?" they reply.

The Sandman watches from afar. Worried, maybe. But not interfering.
"Some people need this," they mutter. "Some people earned it."

Is it escape? Is it healing? Is it denial?

You're happy. Reverie's happy. The sun never sets here.

THE END: The eternal child never grows upâ€”but maybe that's okay.
"""
            },
            "BBA": {
                "title": "THE COMPASSIONATE AWAKENER",
                "content": """
You stand in the waking world at power level {current_power}.
LIGHT. MEMORY. SACRIFICE.

You chose joy, preserved your pain, and let Reverie go.
Both came with youâ€”the diamond and the light. Balance. Wholeness.

đź’š THE COMPASSIONATE AWAKENER'S TRUTH:
You help others wake now. Gently. With understanding.
"Yes, it hurts," you tell them. "Yes, it's worth it."

Reverie is out there somewhere. Living. Happy. Free.
They don't remember you. That's okay. That was the point.

But sometimes, when you help someone leave the dreamscape,
you see their loved onesâ€”waiting, hopeful, GRATEFUL.

And you remember: this is what you gave Reverie.
A world of people who love them. Even without you.

The Sandman retired. "You're better at this than I ever was," they said.
"Go save the dreamers. All of them."

THE END: The awakener carries both worldsâ€”and makes them better.
"""
            },
            "BBB": {
                "title": "THE DREAM WEAVER",
                "content": """
You stand at the center of a new dreamscape at power level {current_power}.
LIGHT. MEMORY. LOVEâ€”with Reverie woven into every part of it.

You chose joy, preserved your pain, and built a world worth living in.
Not escape. Not denial. CREATION.

âś¨ THE DREAM WEAVER'S TRUTH:
You remade the dreamscape into something beautiful.
The Somnambulist's old realm is a garden now. A sanctuary. A HOME.

Trapped dreamers come here to heal before they wake.
You and Reverie guide them. Teach them. Send them home stronger.

"We're the good kind of dream now," Reverie says.

"The BEST kind."

The Sandman officiates your dream-wedding. Cries a little.
"Didn't think I'd see a happy ending. Not here. Not ever."

đźŽ­ THE DREAMER WAS ALWAYS THE DREAM.
   THE LOVE WAS ALWAYS WORTH SAVING.
   THE CHOICE WAS ALWAYS YOURS.

THE END: The greatest dream is the one you share with someone you love.
"""
            },
        },
    },
]

# ============================================================================
# STORY 4: THE UNLIKELY CHAMPION
# A grounded, realistic story about an ordinary person facing an office tyrant
# ============================================================================

UNDERDOG_DECISIONS = {
    2: {
        "id": "underdog_evidence",
        "prompt": "Marcus just stole your project in front of everyone. You have proof he lied. What do you do?",
        "choices": {
            "A": {
                "label": "đź”§ Document Everything",
                "short": "patience",
                "description": "Build an airtight case. Patience is a weapon.",
            },
            "B": {
                "label": "đźŽ¤ Confront Him Now",
                "short": "boldness", 
                "description": "Call him out publicly. Strike while the iron's hot.",
            },
        },
    },
    4: {
        "id": "underdog_alliance",
        "prompt": "Jordan wants to team up against Marcus. But Jordan has their own agenda...",
        "choices": {
            "A": {
                "label": "đź¤ť Accept the Alliance",
                "short": "teamwork",
                "description": "Two against one. The enemy of my enemy...",
            },
            "B": {
                "label": "đźš¶ Go It Alone",
                "short": "independence",
                "description": "Trust no one. This is YOUR fight.",
            },
        },
    },
    6: {
        "id": "underdog_victory",
        "prompt": "Marcus is falling. You can end him or offer mercy. Sam watches your choice...",
        "choices": {
            "A": {
                "label": "âš–ď¸Ź Total Justice",
                "short": "ruthless",
                "description": "Expose everything. End his career. Make him pay for every person he hurt.",
            },
            "B": {
                "label": "đź•Šď¸Ź Graceful Victory",
                "short": "mercy",
                "description": "Report the facts, but don't pile on. Let him resign quietly with some dignity.",
            },
        },
    },
}

UNDERDOG_CHAPTERS = [
    {
        "title": "Chapter 1: Commuter Static",
        "threshold": 0,
        "has_decision": False,
        "content": """
Your alarm goes off at 6:47 AM. You set it for 6:45 because you're optimistic.
You are not a morning person.

The coffee maker gurgles like it's judging you. It probably is.
You've worked at Nexus Industries for three years. Mid-level analyst. 
Decent salary. Soul-crushing commute. The usual.

Your {helmet} hangs by the doorâ€”a bike helmet, because you started cycling
to work after gas prices went insane. Small victories.

Today should be normal. It won't be.

At 9:03 AM, in Conference Room B, your life changes.

MARCUS VANCE stands at the front of the room.
VP of Operations. Perfect hair. Perfect suit. Perfect SHARK smile.
The kind of guy who calls everyone "buddy" and means it as a threat.

He's presenting YOUR project. The one you spent six months building.
The supply chain optimization that will save the company millions.

"And that's why I'm proposing the Vance Initiative," he says, smiling.

Your blood runs cold. Then hot. Then cold again.

He didn't just steal your project.
   He's been planning this for MONTHS. You're just now catching up.

Your coworker Sam catches your eye from across the room.
They KNOW. You can see it in their face. They've seen the original files.

Your {weapon}â€”a pen, right nowâ€”shakes in your grip.

This is the moment. The one that defines who you become.
""",
    },
    {
        "title": "Chapter 2: Paper Trails",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "underdog_evidence",
        "content": """
After the meeting, you corner Sam in the break room.

"Please tell me you saw what I saw," you say.

"The timestamps on your original files vs. his presentation?"
Sam sips their terrible vending machine coffee. "Yeah. I saw it."

Sam is your ally here. Maybe your only one.
They've been at Nexus for five years. They know where the bodies are buried.
Metaphorically. Hopefully metaphorically.

"So what are you going to do about it?" Sam asks.

Good question. Great question. TERRIFYING question.

Marcus Vance isn't just any VP. He's the CEO's golf buddy.
He's the guy who "restructured" the accounting department last year.
Six people. Gone. Just like that.

Your {chestplate}â€”well, it's actually a decent blazer you bought for interviewsâ€”
feels like armor. Or a target.

"I have proof," you say slowly. "My emails. My draft files. Myâ€”"

"Everyone has PROOF," Sam interrupts. "The question is whether anyone will CARE."

Sam was burned by Marcus too. Three years ago.
   Their promotion. Gone. Given to Marcus's college roommate instead.
   They've been waiting for someone brave enough to fight back.

"I care," Sam says quietly. "And I know where he keeps his skeletons."

You stare at each other. This just became a conspiracy.

âšˇ A CHOICE AWAITS... Marcus just took everything from you. Your move.
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: đź”§ DOCUMENT EVERYTHING]

"We do this RIGHT," you say. "No mistakes. No room for spin."

Sam nods slowly. "The long game. I respect that."

For the next three weeks, you become a machine.
Every email. Every timestamp. Every meeting note.
You build a case so airtight it could survive a vacuum.

Your {gauntlets}â€”okay, they're just gloves for cyclingâ€”
remind you that patience is a muscle. You train it daily.

Sam feeds you intel. Marcus's patterns. His allies. His weaknesses.
The man has MANY weaknesses. Arrogance being the biggest.

"He doesn't think anyone is smart enough to catch him," Sam says.

"His mistake."

While gathering evidence, you discover something bigger.
   Marcus hasn't just stolen YOUR project. He's stolen FIVE others.
   You're not alone. There's an army of victims waiting for a leader.
""",
            "B": """
[YOUR CHOICE: đźŽ¤ CONFRONT HIM NOW]

"No more waiting," you say. "I'm ending this TODAY."

Sam's eyes go wide. "In front of everyone? That's either brilliant or career suicide."

"Why not both?"

You march into Marcus's office during his 3 PM call.
He's schmoozing with a vendor. Perfect hair. Perfect confidence. Perfect TARGET.

"Marcus." Your voice doesn't shake. Miracle. "We need to talk. About MY project."

The temperature in the room drops. Marcus's smile doesn't waverâ€”
but his eyes go COLD.

"Buddy, I think you're confusedâ€”"

"I'm not your buddy. And I'm not confused. I have the original files.
Timestamped. Documented. I have witnesses who saw me build this from scratch."

The vendor on the call? She records EVERYTHING for notes.
   She just captured Marcus's guilty expression in HD.
   And she HATES guys like him.

"We'll discuss this later," Marcus says smoothly. But he's rattled.

"Yes," you agree. "We WILL."

Sam is waiting outside. "You absolute MANIAC. I can't believe that worked."

"It hasn't worked yet. But it WILL."
""",
        },
    },
    {
        "title": "Chapter 3: Whisper Networks",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
Week four. Your case file is now a BINDER.

Other victims find you. Quietly. Carefully. Like survivors signaling each other.
There's Jamie from Marketingâ€”Marcus took credit for the viral campaign.
There's Priya from Financeâ€”he blamed her for HIS budget mistake.
There's Old Gerald from ITâ€”who's been waiting 15 years for payback.

"I knew someone would stand up eventually," Gerald says, adjusting his glasses.
"I've been keeping my own records. Just in case."

Gerald's "records" turn out to be a COMPREHENSIVE DATABASE.
Every email Marcus deleted. Every file he "lost." Every lie he told.
Old Gerald is a LEGEND.

At {current_power} power, you're not alone anymore.

Sam watches the growing coalition with something like pride.
"You know," they say, "I was ready to spend my career just surviving him.
Never thought someone would actually FIGHT."

"Someone has to," you say. "Might as well be us."

Marcus knows something is happening.
   He's been too quiet. Too calm. Too CONFIDENT.
   He's planning something. You can feel it.

Your {amulet}â€”it's actually a good luck charm Sam gave youâ€”
feels warm in your pocket. You're going to need that luck.
""",
            "B": """
Week four. You've made enemies. But also ALLIES.

Your public confrontation went viral. Inside the company, at least.
People who were afraid to speak are suddenly TALKING.

"You actually DID it," Jamie from Marketing says, catching you at lunch.
"I've wanted to say something for two years. But I was scared."

"You're not the only one," says Priya from Finance, joining you.
"That man has been stealing credit since he got here."

By Friday, you have a COALITION.
Eleven people. All wronged. All angry. All ready.

At {current_power} power, you're becoming a SYMBOL.

Sam watches the growing movement with complicated feelings.
"You know Marcus is going to hit back, right? Harder than before."

"Let him try."

"That's either courage or denial."

"Why not both?"

There's a mole. Someone in your coalition is feeding Marcus info.
   Your next public statement gets "accidentally" leaked to HR.
   Now you're being investigated for "creating a hostile work environment."

Time to figure out who you can REALLY trust.
""",
        },
    },
    {
        "title": "Chapter 4: The Quiet Offer",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "underdog_alliance",
        "content": """
At {current_power} power, everything changes.

JORDAN CROSS appears. Executive Director of Strategy.
One level above Marcus. And they want to TALK.

"I've seen your evidence," Jordan says, sliding into the seat across from you.
Expensive suit. Calculating eyes. Power radiates off them like heat.

"Everyone's seen it," you say carefully. "That's the point."

Jordan smiles. It doesn't reach their eyes.
"I mean the OTHER evidence. The stuff you haven't shared yet.
The pattern of behavior across five projects. The systemic fraud."

Your blood runs cold. HOW do they know about that?

"I have... resources," Jordan says, reading your face. "And I have an offer.
I want Marcus GONE. You want Marcus gone. We can help each other."

"What's in it for you?"

"His job. When he falls, someone has to fill the vacuum.
I plan to be that someone. With your help, it happens faster."

Sam warned you about Jordan. Everyone warned you about Jordan.
They're brilliant. They're connected. They're also RUTHLESS.

Jordan is the one who PROMOTED Marcus three years ago.
   They created this monster. Now they want to destroy their creation.
   You're just the weapon they need.

"So," Jordan says, leaning back. "Partners?"

âšˇ A CHOICE AWAITS... Jordan could end this overnight. But at what cost?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: đź¤ť ACCEPT THE ALLIANCE]

"Partners," you agree. The word tastes complicated.

Jordan smilesâ€”and this time it's REAL. "You won't regret this."

"I might. But I'll deal with that later."

The alliance changes everything. Suddenly you have ACCESS.
Board meeting schedules. Budget reviews. The CEO's CALENDAR.
Jordan opens doors you didn't even know existed.

Within a week, Marcus is being audited. "Routine," they call it.
But there's nothing routine about the forensic accountants.

Sam watches the escalation with growing concern.
"You're playing with fire," they warn. "Jordan doesn't do favors."

"I know. But Marcus doesn't do MERCY. Pick your poison."

Jordan's plan involves more than just Marcus.
   They're restructuring the ENTIRE division. 
   Half the people who trusted you might lose their jobs.
   Is that a price you're willing to pay?

Your {shield}â€”the coalition you builtâ€”might become collateral damage.
""",
            "B": """
[YOUR CHOICE: đźš¶ GO IT ALONE]

"I appreciate the offer," you say. "But no."

Jordan's smile freezes. "Excuse me?"

"You created Marcus. You promoted him. You protected him for YEARS.
Now that he's vulnerable, you want to use me to take him down.
But then what? You become the new Marcus?"

Jordan's eyes go flat. Dangerous.

"You're making a mistake."

"Probably. But it'll be MY mistake. Not yours."

You walk away. Your hands are shaking. That was TERRIFYING.

Sam is waiting outside. "Tell me you didn't just reject Jordan Cross."

"I definitely did."

"You beautiful, suicidal IDIOT." But Sam is smiling.

Jordan becomes a third player in this game.
   Not quite enemy. Not quite ally. Just... WATCHING.
   Waiting to see who wins so they can claim the survivor.

Your coalition is smaller now. But it's YOURS.
""",
        },
    },
    {
        "title": "Chapter 5: Agenda Item Zero",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
The board meeting. The REAL one. The one where everything ends.

Jordan's plan unfolds like clockwork. Forensic audit. Documented fraud.
Five years of stolen credit laid bare in a 47-page report.

Marcus stands at the center of the room, sweating through his perfect suit.

"This is a WITCH HUNT," he snarls. "I've given this company everythingâ€”"

"You've given this company OTHER PEOPLE'S work," you interrupt.
"And charged them for the privilege."

The boardroom goes silent. You can hear the CEO breathing.

At {current_power} power, you're no longer the underdog.
You're the one with the evidence. The allies. The POWER.

Marcus turns to you with pure HATRED in his eyes.
"You think you've won? I made this place. I can UNMAKE you."

"Try."

But Jordan's not done. They're already positioning
   their own people for the aftermath. The coup within the coup.
   When Marcus falls, Jordan rises. And you're just a TOOL to them.

Sam catches your eye across the table. They've figured it out too.
You're winning the battle. But are you winning the war?
""",
            "AB": """
The confrontation comes in the parking garage. Less dramatic. More REAL.

You're loading your bike when Marcus appears. No smile now.
Just cold fury and expensive leather shoes.

"You think you're clever," he says. "Playing both sides.
Rejecting Jordan. Building your little coalition. Very impressive."

"I'm just doing my job. You should try it sometime."

His face goes purple. "I MADE YOU. I could have promoted you.
Could have brought you onto my team. But you had to be DIFFICULT."

"You stole my work, Marcus. You stole EVERYONE'S work."

At {current_power} power, you don't back down.
Your {boots}â€”cycling shoes, actuallyâ€”are planted firmly.

"This ends at the board meeting," you say. "Everything comes out.
The timestamps. The witnesses. The pattern. All of it."

Marcus pulls out his phone. Shows you something.
   Pictures. Of Sam. Meeting with Jordan. THREE MONTHS AGO.
   "Your best friend has been playing you from the start."

Your world tilts. Is it true? Has Sam been a mole all along?
""",
            "BA": """
The alliance with Jordan has teeth. SHARP teeth.

The audit expands. Marcus's entire department is under review.
People are being questioned. Files are being subpoenaed.
The man who stole your project is watching his empire CRUMBLE.

But so is everything else.

At {current_power} power, you've become powerful. Too powerful, maybe.
Your coalition members are scared. They wanted justice, not WAR.

Jamie from Marketing pulls you aside.
"This isn't what we signed up for. Jordan is talking about LAYOFFS."

"Collateral damage," Jordan explained earlier. "Unfortunate but necessary."

Your {amulet}â€”Sam's lucky charmâ€”feels heavy now.

Sam hasn't spoken to you in three days.
   They were right about Jordan. And you didn't listen.
   Now half your allies think you've become worse than Marcus.

Is victory worth THIS?
""",
            "BB": """
Going it alone is HARD. But it's also CLEAN.

No Jordan. No complicated alliances. Just you, your evidence, and truth.
The coalition has shrunk. But the people who remain are LOYAL.

At {current_power} power, you've earned respect the hard way.

The board meeting approaches. Marcus is panicking.
You can see it in his behaviorâ€”the snapping at assistants.
The long lunches. The whispered phone calls.

He's trying to make deals. Trying to find protection.
But he burned too many bridges. Nobody owes him anything.

Sam stays late with you, preparing the final presentation.
"We've got him," they say. "This is REALLY happening."

The night before the board meeting, you get an email.
   From Marcus's WIFE. She's leaving him. And she has documents.
   Bank accounts. Hidden bonuses. A second property.
   Proof that he's been skimming from the company for YEARS.

This isn't just career theft anymore. This is CRIMINAL.
""",
        },
    },
    {
        "title": "Chapter 6: Ladders in Smoke",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "underdog_victory",
        "content": """
The boardroom. Final act. Everyone is here.

At {current_power} power, you stand where Marcus stood eight months ago.
Same conference room. Same projector. Different ending.

The evidence fills three screens. Timestamps. Witnesses. Paper trails.
Five years of systematic theft laid bare in undeniable detail.

Marcus sits at the far end of the table. Gray-faced. Diminished.
His perfect hair is wrong somehow. His suit fits badly.
He looks like a man watching his life burn.

The CEO speaks: "Marcus. Do you have anything to say?"

For a long moment, nothing. Then:

"I built this department from NOTHING."

"You built it on other people's work," you respond.

"I gave those people OPPORTUNITIESâ€”"

"You gave yourself CREDIT. There's a difference."

In his eyes, you see something unexpected. FEAR.
   Not of losing his job. Of losing his IDENTITY.
   Marcus Vance, golden boy, is just... a thief.
   He doesn't know who he is without the lies.

Across the table, you catch a familiar face watching. Waiting.
This moment has been a long time coming for both of you.

The CEO turns to you. "What do you recommend?"

âšˇ A CHOICE AWAITS... Marcus is falling. How far do you let him drop?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: âš–ď¸Ź TOTAL JUSTICE]

"Everything," you say. "Full investigation. Criminal referral. Public disclosure.
Every project he stole. Every person he hurt. All of it."

The CEO nods slowly. "You understand that will create... complications."

"I understand it will create ACCOUNTABILITY."

Marcus's face goes white. Then red. Then something beyond color.
"You can't DO thisâ€”I have FRIENDSâ€”"

"Had," someone mutters from the table. "Past tense."

The fall is complete. ABSOLUTE.
Criminal investigation. Civil lawsuits. Professional exile.
Marcus Vance becomes a cautionary tale told at industry conferences.

Sam finds you afterward, in the parking garage.
"You did it," they say. "You actually DID it."

"WE did it."

Your phone buzzes. A message about the VP of Operations role.
   The position is opening up. People are asking if you're interested.
   Now comes the question: what kind of victory do you WANT?
""",
            "B": """
[YOUR CHOICE: đź•Šď¸Ź GRACEFUL VICTORY]

"Resignation," you say. "Quiet. No prosecution. He leaves, we move on."

The boardroom stirs. Murmurs. Surprise.

"After everything he did?" the CEO asks.

"After everything he did, he's FINISHED. Everyone knows. Everyone will remember.
But I don't want to become him. I don't want to destroy someone for sport."

Marcus stares at you. Confusion. Suspicion. Something that might be... gratitude?

"Get out," you tell him. "Start over somewhere else. Be better."

The meeting ends. Marcus leaves. Not in handcuffsâ€”in a taxi.
His career is over. But he's still standing. Barely.

Sam finds you afterward. Their expression is complicated.
"That was... unexpected. Merciful."

"I just didn't want to become the monster to beat the monster."

A month later, you get a letter. From Marcus.
   No return address. Just three words: "You were right."
   You're not sure what he means. But somehow, it matters.
""",
        },
    },
    {
        "title": "Chapter 7: Windows Facing In",
        "threshold": 1500,
        "has_decision": False,
        "endings": {
            "AAA": {
                "title": "THE POWER PLAYER",
                "content": """
One year later. Power level {current_power}.
PATIENCE. ALLIANCE. RUTHLESSNESS.

You sit in Marcus's old office. Bigger desk. Better view. YOUR name on the door.
VP of Operations. The job you never wantedâ€”until you earned it.

Jordan Cross is CEO now. The coup within the coup was real.
But you're not their puppet. You're their PARTNER.
The company runs cleaner now. Fairer. Not perfectâ€”but better.

đźŹ† THE POWER PLAYER'S TRUTH:
You built alliances. You wielded power. You destroyed an enemy completely.
And in the wreckage, you built something STRONGER.

Sam runs their own department now. They smile when they pass your office.
"Never thought I'd see the day," they say.

"Neither did I."

But late at night, sometimes, you wonder:
Did you win? Or did you just become the new Marcus?

The view from the top is lonely. But at least it's YOURS.

THE END: The patient hunter claims the throneâ€”and everything that comes with it.
"""
            },
            "AAB": {
                "title": "THE BENEVOLENT VICTOR",
                "content": """
One year later. Power level {current_power}.
PATIENCE. ALLIANCE. MERCY.

The corner office is yours. But you've done something unprecedentedâ€”
opened the door. Literally. The whole floor can see you work.
No more secrets. No more stolen credit. No more fear.

Jordan Cross runs the company now. They're... watching you.
You're an experiment to them. A new kind of leader.
Merciful but effective. Kind but STRONG.

đźŹ† THE BENEVOLENT VICTOR'S TRUTH:
You proved that you can win without destroying.
That power doesn't have to corrupt. That victory can be CLEAN.

Sam is your VP now. They still can't believe it.
"You gave mercy to the man who tried to ruin you."

"And look what happened. He's gone. But WE'RE still here.
Still together. Still better."

Marcus sent a donation to the company charity last month.
Anonymous. But you knew. Somehow, you knew.

THE END: The patient victor builds a legacyâ€”not just a career.
"""
            },
            "ABA": {
                "title": "THE LONE WOLF",
                "content": """
One year later. Power level {current_power}.
PATIENCE. INDEPENDENCE. RUTHLESSNESS.

You didn't take Jordan's deal. You didn't take Marcus's job.
You took something BETTERâ€”freedom.

Your own consulting firm. YOUR name on the building.
Helping companies find the Marcuses hiding in their ranks.
You're not cheap. You're WORTH IT.

đźŹ† THE LONE WOLF'S TRUTH:
You proved that you could do it alone. Without allies. Without compromise.
And in the independence, you found something Marcus never hadâ€”peace.

Sam visits sometimes. They stayed at Nexus. Changed it from within.
"You could have been running that place," they say.

"I'd rather run THIS place." You gesture at your small, perfect office.
"No politics. No games. Just the work."

Marcus disappeared. Last you heard, he was selling real estate.
The fall was complete. The victory was YOURS.

THE END: The lone wolf answers to no oneâ€”and that's exactly how you like it.
"""
            },
            "ABB": {
                "title": "THE HUMBLE CHAMPION",
                "content": """
One year later. Power level {current_power}.
PATIENCE. INDEPENDENCE. MERCY.

You turned down the VP job. Shocked everyoneâ€”including yourself.

Instead, you're running the mentorship program now.
Helping new employees navigate the politics. Protecting them from predators.
Building the company you WISHED existed when you started.

đźŹ† THE HUMBLE CHAMPION'S TRUTH:
You won without destroying. Built without consuming.
And in the humility, you found something Marcus never understoodâ€”happiness.

Sam leads your old department. They're GOOD at it.
"You trained half of them," they remind you.

"I just showed them what NOT to do."

Marcus runs a small business now. Cleaning services.
Honest work. A fresh start. You sent him a client referral once.
He never acknowledged it. That's okay.

THE END: The humble champion builds peopleâ€”not empires.
"""
            },
            "BAA": {
                "title": "THE REVOLUTIONARY",
                "content": """
One year later. Power level {current_power}.
BOLDNESS. ALLIANCE. RUTHLESSNESS.

You didn't just take down Marcus. You took down the whole SYSTEM.

Jordan's coup succeededâ€”but so did yours.
The old guard is GONE. Replaced by people like you.
People who earned their positions. People who REMEMBERED.

đźŹ† THE REVOLUTIONARY'S TRUTH:
Your confrontation sparked a movement. Your alliance made it unstoppable.
And when Marcus fell, everyone who protected him fell too.

Sam is Chief People Officer now. They spend most of their time
making sure another Marcus never rises again.

"Revolution isn't a single act," they told you once.
"It's constant vigilance."

You've become the vigilance. The standard. The warning.
Cross someone like you, and the whole company knows.

THE END: The revolutionary tears down the old worldâ€”and builds a new one.
"""
            },
            "BAB": {
                "title": "THE PEOPLE'S CHAMPION",
                "content": """
One year later. Power level {current_power}.
BOLDNESS. ALLIANCE. MERCY.

The corner office is yours. But you earned it DIFFERENTLY.

Your public confrontation made you famousâ€”inside the company and OUT.
Business magazines interviewed you. Other victims reached out.
You became a SYMBOL.

đźŹ† THE PEOPLE'S CHAMPION'S TRUTH:
You proved that speaking up WORKS. That bullies can be beaten.
That mercy doesn't mean weaknessâ€”it means STRENGTH.

Sam co-leads the department with you. Equal partners.
"Remember when you confronted him in his office?"

"I nearly threw up afterward."

"And now you're running the place. Funny how that works."

Jordan sends congratulations sometimes. They're still watching.
Maybe they learned something from you. Maybe not.
Either wayâ€”you're not their weapon. You're their EXAMPLE.

THE END: The people's champion speaks truthâ€”and the truth wins.
"""
            },
            "BBA": {
                "title": "THE SHADOW KING",
                "content": """
One year later. Power level {current_power}.
BOLDNESS. INDEPENDENCE. RUTHLESSNESS.

You didn't take the big job. You took the REAL power.

Head of Compliance. Sounds boring. IS boring.
But every single decision in this company crosses your desk.
You see EVERYTHING. You know EVERYONE.

đźŹ† THE SHADOW KING'S TRUTH:
Marcus wanted spotlight. Jordan wants glory.
You? You want OVERSIGHT. And you HAVE it.

No one steals credit anymore. Not with you watching.
No one takes shortcuts. Not with your audits.
The company is cleaner, sharper, BETTERâ€”because of you.

Sam visits your quiet office sometimes.
"You know you're the most powerful person here, right?"

"I know. That's the point. Power that looks like service."

Marcus tried to come back last month. Applied for a contract.
Your desk. Your review. Your signature.

DENIED.

THE END: The shadow king rules from the darkâ€”and the light never touches him.
"""
            },
            "BBB": {
                "title": "THE HAPPY ENDING",
                "content": """
One year later. Power level {current_power}.
BOLDNESS. INDEPENDENCE. MERCY.

Everything worked out. ACTUALLY worked out.

You're VP of Operations nowâ€”but you didn't fight for it.
They OFFERED. After everything you did. After everything you DIDN'T do.
The mercy impressed them more than the victory.

Sam is by your side. Not as an employeeâ€”as a PARTNER.
Somewhere between the confrontations and the board meetings,
you fell in love. Neither of you planned it. Both of you meant it.

đźŹ† THE HAPPY ENDING'S TRUTH:
You beat the bully. You won the job. You got the person.
Not because you were ruthlessâ€”because you were GOOD.

Marcus works for a nonprofit now. Helping at-risk youth.
You wrote him a recommendation letter. It felt RIGHT.

The corner office has pictures on the desk.
Sam. Your dog. The coalition at last year's holiday party.
Real people. Real victories. Real life.

đźŽ­ THE UNLIKELY HERO WAS ALWAYS INSIDE YOU.
   THE VICTORY WAS ALWAYS ABOUT MORE THAN WINNING.
   THE HAPPY ENDING WAS ALWAYS POSSIBLE.

THE END: The unlikely champion wins everythingâ€”and deserves all of it.
"""
            },
        },
    },
]

# ============================================================================
# STORY 5: THE BREAKTHROUGH PROTOCOL (Scientist)
# ============================================================================

SCIENTIST_DECISIONS = {
    2: {
        "id": "scientist_method",
        "prompt": "Dr. Rivera's lab just published results using your preliminary hypothesisâ€”without citation. Your breakthrough, their paper. Do you...",
        "choices": {
            "A": {
                "label": "đź”Ą Expose Them Publicly",
                "short": "aggressive",
                "description": "Present your original notes at the conference. Burn their credibility.",
            },
            "B": {
                "label": "đź§Ş Outwork Them Quietly",
                "short": "methodical",
                "description": "Let them have the preliminary. You'll publish the full breakthrough.",
            },
        },
    },
    4: {
        "id": "scientist_collaboration",
        "prompt": "Dr. Chen offers collaborationâ€”her lab has funding and equipment you need. But she wants co-authorship on YOUR discovery. Do you...",
        "choices": {
            "A": {
                "label": "đź¤ť Accept Partnership",
                "short": "collaboration",
                "description": "Share the credit. Science is bigger than ego.",
            },
            "B": {
                "label": "đź”¬ Stay Independent",
                "short": "independence",
                "description": "Work alone. The breakthrough will be yours alone.",
            },
        },
    },
    6: {
        "id": "scientist_ethics",
        "prompt": "The data shows promising resultsâ€”but one trial failed catastrophically. Rivera would hide it. Chen would publish everything. The grant committee meets tomorrow. Do you...",
        "choices": {
            "A": {
                "label": "đź“Š Report All Data",
                "short": "honest",
                "description": "Include the failure. Science demands truth, not convenience.",
            },
            "B": {
                "label": "âŹ±ď¸Ź Request Extension",
                "short": "pragmatic",
                "description": "Ask for six more months. Fix the failure before publishing.",
            },
        },
    },
}

SCIENTIST_CHAPTERS = [
    {
        "title": "Chapter 1: Lab Notes in Ash",
        "threshold": 0,
        "has_decision": False,
        "content": """
Three years. Three YEARS of failed experiments.
Your lab notebook reads like a catalog of disasters.
Trial 47: Failed. Trial 48: Inconclusive. Trial 49: Equipment malfunction.

**Analysis paralysis.** That's what your advisor called it.
You plan every variable. Control for every factor.
Run simulations before experiments. Models before prototypes.

And still. NOTHING works.

Your colleague Dr. Rivera gets results weeklyâ€”sloppy, fast, publishable.
"You overthink everything," Rivera says. "Science is about action, not perfection."

But you've seen Rivera's data. The shortcuts. The assumptions.
The "statistically significant" results that won't replicate.
That's not science. That's theater.

Your workspace: {helmet} on the bench, {weapon} beside your lab notebook.
Power level {current_power}. Zero breakthroughs.

Dr. Alexis Chen works in the adjacent lab.
She's brilliantâ€”published in Nature twice before age 30.
"The best scientists fail more than they succeed," she told you once.
"The question is whether you learn from it."

Today's experiment: Trial 50.
You've run the numbers seventeen times.
Checked every calculation. Verified every measurement.

This time. THIS time, it has to work.

Your hands are steady. Your notes are perfect.
The timer starts.

**Every breakthrough begins with discipline. Every discovery demands persistence.**
**You are not failing. You are iterating toward truth.**
"""
    },
    {
        "title": "Chapter 2: Echoes in Peer Review",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "scientist_method",
        "content": """
Trial 50: **PARTIAL SUCCESS.**

Not a breakthrough. Not yet. But PROGRESS.
The data shows a patternâ€”preliminary, fragile, but REAL.

You write it up carefully. Share it at the lab meeting.
"Interesting," Dr. Chen says. "Keep going."
"Waste of time," Rivera mutters. "Too slow."

Two weeks later: Rivera's lab publishes in *Scientific Reports*.
Your hypothesis. Your preliminary data. Their paper.

"We reached similar conclusions independently," Rivera claims.

**BULLSHIT.** You showed them the data. You explained the method.
They took your idea, ran one sloppy trial, and rushed to publication.

Now the science community thinks Rivera discovered it first.
Your advisor suggests "moving on to something else."
"These things happen in science. Don't burn bridges."

But Dr. Chen pulls you aside after the meeting.
"I have your original lab notes timestamped on the server.
You can prove they stole this. But proving it will destroy themâ€”
and make you look vindictive. Or..."

She pauses.

"You can let them have the preliminary finding.
It's incomplete anyway. Work on the FULL breakthrough.
When you publish the complete mechanism, everyone will know
who did the real science. Rivera will look like an amateur."

**The conference is in three days.**
**You have a platform. You have evidence.**
**Do you expose theft, or do you outwork it?**
""",
        "content_after_decision": {
            "A": """
**YOU CHOOSE: EXPOSE THEM PUBLICLY**

The conference hall is packed. Rivera presents firstâ€”
your hypothesis, poorly explained, barely understood.

Then it's your turn.

You show the timestamped notes. The original calculations.
The discrepancies in Rivera's methodology.

"Dr. Rivera's paper is based on preliminary data
shared at our departmental meetingâ€”which I presented
two weeks before their publication date."

The room goes silent.

Rivera's face turns red. The department chair takes notes.

**You won. Rivera is finished.**

But as you leave the podium, you catch Dr. Chen's expression.
Not pride. Something else. **Concern?**

"You just made every scientist in this room afraid to share ideas with you.
You were RIGHTâ€”but now you're the person who destroys colleagues.
Good luck finding collaborators."

The breakthrough is still yours to discover.
But now, you'll discover it alone.

Power level {current_power}. Your {weapon} gleams in the lab light.
The vindication felt good. But the isolation feels cold.

**Truth was served. But was it worth the cost?**
""",
            "B": """
**YOU CHOOSE: OUTWORK THEM QUIETLY**

The conference happens. Rivera presents.
You sit in the audience and take notes.

They got the surface-level insight rightâ€”barely.
But they missed THE KEY VARIABLE.
The thing that makes it actually work.

"Interesting preliminary findings," someone comments.
"Yes, preliminary," you think. "And wrong."

You return to your lab. Double down.
The {weapon} beside you. The {helmet} shielding your eyes.
Power level {current_power}. Focus like a laser.

Three months pass.

You find it. **THE MECHANISM.**
Not just "this probably works"â€”but WHY it works.
The mathematics. The biochemistry. The complete picture.

Your paper goes to *Nature*. Peer review is brutal.
But your data is PERFECT. Your methodology is FLAWLESS.

Accepted.

When it publishes, the science community sees immediately:
Rivera found a shadow. You found the sun.

Dr. Chen sends you a message:
"This is how real science is done. I'm impressed."

Rivera's paper gets cited as "preliminary findingsâ€”
see [Your Name] et al for complete mechanism."

**You didn't destroy them. You simply did better science.**
The community respects you. Collaborators reach out.
And Rivera? No one takes them seriously anymore.

Power level {current_power}. The {weapon} in your hands.
Victory through excellence, not vengeance.

**Discipline beats shortcuts. Always.**
"""
        },
    },
    {
        "title": "Chapter 3: Instruments in Orbit",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
Six months after the conference incident.

Your lab is quieter now. Grad students avoid you.
Post-docs request transfers. "Difficult to work with," they say.

Not because you're wrong. Because you're RIGHTâ€”loudly, publicly, devastatingly.

Dr. Chen still talks to you. Barely.
"You made your point. Rivera's career is over.
Are you happy? Was it worth it?"

You want to say yes. But the data doesn't lieâ€”
your productivity has dropped. Collaboration requests: zero.
Grant applications: rejected. "Concerns about collegiality."

Rivera works at a teaching college now. You heard they're happy there.
You work alone. You told yourself you preferred it this way.

But the breakthrough is harder alone.

Your {helmet} on. Your {weapon} ready.
Power level {current_power}. Progress is SLOW.

Trial 73: Failed.
Trial 74: Inconclusive.
Trial 75: Promising, but you need verification.

Verification requires a second lab. A collaborator.
Someone willing to work with you.

Dr. Chen knocks on your door.
"I heard you need mass spectrometry verification.
I have the equipment. I'll helpâ€”but only if you can
work with someone without burning them."

**The isolation you chose is becoming the isolation that limits you.**
**Science is collaborative. But can you collaborate without compromising?**
""",
            "B": """
Six months after outworking Rivera.

Your lab is busier than ever.
Three grad students requested placement with you.
Two post-docs want to join your research group.
"The person who does the best science," they say.

Dr. Chen drops by regularly now.
Not just as a colleagueâ€”as a friend.
"Coffee?" she asks on Fridays. You always say yes.

Somewhere between the failed experiments and the breakthrough,
you started to enjoy the process. Not just the results.

Trial 73: Failedâ€”but the failure revealed something unexpected.
Trial 74: Inconclusiveâ€”but Chen suggested a modification that worked.
Trial 75: **MAJOR PROGRESS.**

The data is beautiful. Clean. Reproducible.
Two labs verified it independently (Chen's and Cornell's).

Your paper draft is 47 pages. Single-authored.
Chen offered co-authorship. You declined.
"You advised. You didn't discover. This is yours," she said.

But you thanked her in the acknowledgments.
Science is collaborativeâ€”even when the credit isn't shared.

Your {helmet} on your desk. {weapon} beside your laptop.
Power level {current_power}. The rhythm of research.

The breakthrough is close. You can FEEL it.
Not because you rushed. Because you were METHODICAL.
Not because you destroyed competitors. Because you did BETTER WORK.

Dr. Chen knocks. "Lab meeting in ten. You presenting?"

"Always."

**Excellence is patient. Excellence is collaborative. Excellence WINS.**
"""
        },
    },
    {
        "title": "Chapter 4: Shared Keys",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "scientist_collaboration",
        "content": """
The breakthrough is within reach. You know it.
Every experiment brings you closer to THE MECHANISMâ€”
the key that unlocks everything.

But you've hit a wall.

Your equipment is outdated. Your funding is limited.
The next phase requires tools you don't have:
Advanced imaging. Mass spectrometry at resolutions your lab can't achieve.
Computational modeling beyond your server's capacity.

You could apply for grants. Wait six months. Maybe get funding.
Or you could borrow time on Cornell's equipment. Political favors.
Or you could accept Dr. Chen's offer.

She knocks on your lab door. Again.

"I've been watching your progress. It's brilliant.
But you're stuckâ€”not because of the science,
because of RESOURCES. My lab has everything you need."

You know this. Chen's lab is state-of-the-art.
Funded by a multi-million dollar NSF grant.
Equipment you'd need years to acquire.

"I want to collaborate. Officially.
You lead the experimental design. My lab provides resources.
We publish together. Co-first authorship."

**Co-authorship.** Sharing YOUR discovery.

"This could accelerate your timeline by a year," Chen continues.
"But I understand if you want to work alone.
Science is personal. Breakthroughs are personal."

She understands. That's what makes this harder.

Your {helmet} rests on the bench. {weapon} beside your notes.
Power level {current_power}. Every session focused on THIS.

Chen is brilliant. Her lab is professional. She's ETHICAL.
But the discovery will have two names on it.

Or you work alone. Slower. But YOURS alone.

Rivera appears in your mindâ€”the thief, the shortcut-taker.
If you collaborate, how are you different from someone
who shares credit they didn't fully earn?

But you remember: Chen isn't Rivera.
She's offering tools, not stealing ideas.

**Do you accelerate the breakthrough by sharing credit?**
**Or do you slow down to keep it entirely yours?**
""",
        "content_after_decision": {
            "A": """
**YOU CHOOSE: ACCEPT PARTNERSHIP**

"Yes. Let's collaborate."

Chen smiles. "Good. I'll draft the agreement.
You retain lead authorship. Equal contribution clause.
No one takes credit they didn't earn."

The paperwork takes a week.
The experiments start immediately.

Chen's imaging equipment is INCREDIBLE.
Resolution ten times better than yours.
You see structures you only theorized about.

"This is what you needed," Chen says, looking at the images.
"This is the proof."

Weeks become months. The data grows.
Chen's post-doc helps with computational modeling.
Your grad student handles synthesis.

It's FASTER. More rigorous. Better science.

But in the quiet moments, you wonder:
Would you have found it alone eventually?
Does sharing credit diminish the achievement?

Then the results come back.
Trial 92: **COMPLETE MECHANISM CONFIRMED.**

You and Chen stare at the data together.

"We did it," she says.

"WE did it," you repeat. The word feels strange. But TRUE.

The paper goes to *Nature*: [Your Name] & Chen, co-first authors.
Peer review is brutal. But the data is PERFECT.

Accepted.

When it publishes, the community celebrates.
"Groundbreaking collaboration," they say.
"This is how science should be done."

Your name is first. But Chen's name is there too.
And honestly? The discovery is BETTER because she was involved.

Power level {current_power}. {weapon} in your lab.
You learned something Rivera never did:
**Great scientists don't work alone. They work with equals.**
""",
            "B": """
**YOU CHOOSE: STAY INDEPENDENT**

"I appreciate the offer. But I need to do this alone."

Chen nods slowly. "I understand. The door stays open
if you change your mind."

She leaves. You return to your work.

Your {helmet}. Your {weapon}. Your {current_power} sessions.
ALONE. As it should be.

Weeks become months. Progress is SLOW.

You apply for equipment grants. Rejected.
"Insufficient preliminary data." But the data requires the equipment.
Catch-22.

You borrow time on Cornell's mass spec. Three hours per week.
Not enough. But it's what you have.

Trial 82: Promising, but verification needed.
Trial 83: Equipment malfunction (not your fault).
Trial 84: Inconclusive.

You see Chen in the hallway sometimes.
Her lab published two papers this quarter.
Collaborations with MIT and Stanford.

"How's your project going?" she asks.

"Slowly," you admit.

She doesn't say "I told you so." But you hear it anyway.

Nine months pass. You're CLOSER. Not there yet.

Then Chen appears at your door. Again.

"I'm not offering collaboration anymore.
But I AM offering you three days of dedicated equipment time.
No co-authorship. No strings. Just... scientist to scientist."

You want to say no. Pride says refuse help.

But science says: **Take the data opportunity.**

"Why?" you ask.

"Because good science matters more than ego.
And because I want to see what you discoverâ€”
even if my name isn't on it."

You accept. Three days. You work 72 hours straight.

The data comes through. **PARTIAL MECHANISM CONFIRMED.**

Not complete. Not yet. But closer.

Power level {current_power}. {weapon} steady in your hands.

The breakthrough will be yours alone.
But it's taking EVERYTHING you have.

**Independence is powerful. But is it efficient?**
"""
        },
    },
    {
        "title": "Chapter 5: Data at 3AM",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
One year into the collaboration.

You and Dr. Chen have become partnersâ€”not just in research,
but in how you approach science. She challenges your perfectionism.
You sharpen her methodology.

The project is moving faster than you imagined.
Trial 103: Successful.
Trial 104: Reproducible.
Trial 105: **BREAKTHROUGH CONFIRMED.**

You're writing the paper. Co-first authorship.
Chen handles the theoretical framework.
You handle the experimental validation.

Then you find it.

**ERROR IN TRIAL 97.**

Not a small error. A CRITICAL miscalculation in the dosage.
The results from that trialâ€”which informed Trials 98-102â€”are WRONG.

You check the notes. Chen's post-doc ran Trial 97.
You supervised, but you didn't catch the error.

If this error invalidates the downstream experiments...
the ENTIRE breakthrough might be compromised.

You sit alone in the lab at 2 AM.
Your {helmet} on the desk. {weapon} untouched.
Power level {current_power}. All that focus.

For what? A mistake you should have caught?

You could:
1) Tell Chen immediately. Halt everything. Re-run Trials 98-105.
2) Re-check the math. Maybe the error doesn't propagate.
3) Bury it. The final results look good. No one will check Trial 97.

Option 3 is what Rivera would do.

You think of Dr. Chen. The trust you've built.
The partnership that made this possible.

You call her at 2:15 AM.

"We have a problem."

She arrives within twenty minutes. You show her the error.

She goes pale. "This could invalidate..."

"Everything downstream. Yes."

Silence.

"We re-run it," Chen says finally. "All of it.
This is science. We don't publish errors."

Three months of re-experiments. Verification. Cross-checks.

Trial 97 (corrected): Different results.
Trials 98-102: Need adjustment.
Trial 103-105: **STILL VALID, but with modified interpretation.**

The breakthrough HOLDS. But the mechanism is more nuanced.
Actually MORE interesting than the original finding.

Chen sends you a message at 3 AM:
"Finding that error saved us from publishing something wrong.
That's what good collaboration looks like."

Power level {current_power}. The {weapon} gleaming.

**Excellence requires catching your own mistakes.**
**Great partnerships make that possible.**
""",
            "AB": """
One year after declining Chen's collaboration.

Your breakthrough came. Eventually.
Not as fast as Chen's labs. Not as elegant.
But it's YOURS. Every data point. Every conclusion.

Trial 114: **MECHANISM PARTIALLY CONFIRMED.**

"Partially" because you lack the verification equipment.
"Confirmed" because your methodology is FLAWLESS.

You submit to *Nature*. The paper is brilliant.
Single-author. Your name only.

Peer review comes back: "Impressive work, but..."

**BUT.**

"Results require independent verification.
Computational modeling needed for theoretical validation.
High-resolution imaging would strengthen conclusions."

Everything Chen's lab could have provided.

You request revisions time. Six months granted.

You contact universities. Beg for equipment time.
"We can give you four hours next quarter..."

Not enough.

Chen appears at a conference. You haven't spoken in a year.

"I heard about the *Nature* submission," she says.
"Congratulations on getting that far."

"It's in revisions. They want verification I can't provide."

"I could help. Still. If you want."

**Pride says no. Science says yes.**

"Would you... verify independently? Not collaborate.
Just confirm my results in your lab?"

"Of course. That's what scientists do."

She runs the verification. Three weeks.
The results come back: **CONFIRMED.**

She sends you the data with a note:
"Your mechanism is correct. Beautiful work.
You can cite this as independent verification."

The paper gets accepted. Single-author.
But Chen's verification is in the acknowledgments.

She helped you. Even after you refused her.

At the pub after the acceptance celebration:

"Why did you help me?" you ask.

"Because the science mattered more than ego.
Yours OR mine."

Power level {current_power}. The {weapon} in your hands.

You got your solo breakthrough.
But you learned: **Even lone wolves need the pack sometimes.**
""",
            "BA": """
One year after accepting Chen's collaboration.

The project is thriving. You've published two papers togetherâ€”
major findings, well-cited, contributing to the field.

But something's been bothering you.

The CORE breakthroughâ€”the mechanism you discovered aloneâ€”
is listed as "co-first authorship" in your current draft.

Chen's lab provided equipment. Resources. Verification.
But the INSIGHT was yours. The experimental design: yours.

You're in the lab late when Chen finds you.

"You've been distant lately. What's wrong?"

"I don't know how to say this without sounding ungrateful..."

"Just say it."

"The core mechanism. The breakthrough. I discovered that
BEFORE our collaboration. Your lab verified it. Enhanced it.
But it was MY finding."

Chen sits down. "You're right."

You blink. "I'm... what?"

"You discovered the core mechanism. I provided resources
that accelerated validation. But the insight was yours first."

She pulls out the draft paper. Red pen in hand.

"What if we restructure? You're sole first author on the
mechanism paper. I'm second author for verification.
Then we co-author the APPLICATIONS paper together?"

"You'd do that?"

"It's the truth. Good science is truthfulâ€”
about data AND about credit."

You restructure. Two papers:
1) The Mechanism: [Your Name] (first), Chen (second)
2) Applications: [Your Name] & Chen (co-first)

Both get accepted. The community sees EXACTLY who contributed what.

Rivera's name comes up at a conference.
"Whatever happened to them?"

"Teaching at a community college," someone says.
"They tried shortcuts. This is what real science looks like."

Power level {current_power}. The {weapon} gleaming.

You and Chen in the lab:

"You know what's better than solo glory?" she asks.

"What?"

"Partnership that's HONEST about contributions.
We both win. The science wins."

**Excellence is collaborative. But credit must be accurate.**
""",
            "BB": """
One year after staying independent.

You're CLOSE. So close to the breakthrough.

Trial 127: Promising.
Trial 128: Needs verification.
Trial 129: **MECHANISM PARTIALLY CONFIRMED.**

Your single-author paper is 63 pages.
Every experiment run by you. Every calculation verified three times.

You submit to *Nature*.

Peer review: "Insufficient verification. Independent replication required."

You don't have another lab. You've worked alone.

The rejection stings. Not because you failedâ€”
because you did EXCELLENT science that no one will see
until you can verify it.

Dr. Chen published three papers this year.
Collaborations with top labs. Each paper: multiple authors.
Each paper: accepted on first submission.

You see her at a conference.

"I heard about the rejection," she says gently.
"That's brutal. Your science is solid."

"Not solid enough without verification."

"Have you consideredâ€”"

"Collaboration? Yes. Every day."

"It's not too late. I'd still work with you."

You look at her. Really look at her.

Not as a competitor. Not as someone who wants YOUR glory.
As another scientist who wants good science published.

"What would collaboration look like NOW?" you ask.

"You publish your mechanism paper. Solo.
I verify it independentlyâ€”cited as verification, not co-author.
Then we collaborate on the NEXT phase together.
You keep your breakthrough. We share future discoveries."

It's FAIR. It's ethical. It's good science.

You accept.

Chen's lab verifies in three weeks.
*Nature* accepts your paper with the verification.
Single-author. Your name. Your breakthrough.

Then you start the next project. Together.

Power level {current_power}. {weapon} beside Chen's equipment.

You learned the hard way:
**You can do great science alone. But you can do MORE together.**

The breakthrough is yours.
But the future belongs to both of you.
"""
        },
    },
    {
        "title": "Chapter 6: The Quiet Committee",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "scientist_ethics",
        "content": """
The final experiments. The complete breakthrough.
Everything you've worked for is HERE.

Trial 147: Successful.
Trial 148: Successful.
Trial 149: Successful.
Trial 150: **CATASTROPHIC FAILURE.**

Not just "inconclusive." Not just "needs adjustment."
**CATASTROPHIC.** The mechanism you discoveredâ€”
under specific conditionsâ€”causes complete system collapse.

You've run 150 trials. 149 show promise.
But Trial 150? If this were medical research, someone could die.

You check the conditions. Obscure. Unlikely in real-world use.
Temperature 15 degrees higher than normal.
pH slightly acidic. Pressure elevated.

"Edge case," a lesser scientist would say. Rivera would say.

But Chen walks in. Sees the data.

"Oh no."

"Oh no" is right.

The grant committee meets TOMORROW.
This research is your tenure case. Your career.
Three years of work. Your entire professional future.

If you report Trial 150, the committee will:
- Question your methodology (even though it's perfect)
- Delay funding (even though 149/150 trials succeeded)
- Possibly REJECT the entire project (even though it's groundbreaking)

Dr. Chen sits beside you.

"This is the choice that defines a scientist.

Option A: Report everything. Include Trial 150.
Explain it's an edge case. Show the full data.
Be HONESTâ€”and risk losing everything.

Option B: Request a six-month extension.
Tell them you need to 'expand the scope.'
Use that time to solve Trial 150 before revealing it.

Rivera would hide it. Just publish the 149 successes.

But Chen looks at you.

"What kind of scientist do you want to be?"

Your {helmet} on the bench. {weapon} beside the data.
Power level {current_power}. All for this moment.

**The committee meets in 14 hours.**
**The choice defines not just your careerâ€”**
**but the kind of science you believe in.**
""",
        "content_after_decision": {
            "A": """
**YOU CHOOSE: REPORT ALL DATA**

The committee meeting. 9 AM.

You present. 150 trials. Full methodology.
Trials 1-149: Successful.
Trial 150: Catastrophic failure under specific conditions.

The room goes quiet.

"You're reporting a FAILURE?" one committee member asks.
"In a grant continuation meeting?"

"I'm reporting THE TRUTH," you reply.

"This is either the most ethical thing I've seenâ€”
or the most career-ending," another mutters.

Dr. Chen (attending as collaborator or reference, depending on your earlier choice) speaks:

"Trial 150 isn't a failure. It's a FINDING.
[Your Name] discovered not just what worksâ€”
but the CONDITIONS under which it fails.
That's more valuable than hiding problems."

The committee deliberates. You wait outside.

One hour. Two hours. Three.

The door opens.

"We're extending your grant. Full funding.
But with one condition: you MUST investigate Trial 150 fully.
We want to know WHY it failsâ€”that's as important as why it works."

You got the funding. BECAUSE you were honest.

Rivera's lab lost funding last yearâ€”
their "successful" results couldn't be replicated.
They hid the failures. It caught up with them.

You reported the failure. And the committee RESPECTED it.

Power level {current_power}. The {weapon} steady.

Six months later: You solve Trial 150.
The mechanism works universallyâ€”with ONE modification.
Your paper: "Complete Mechanism and Failure Modes"
gets published in *Science*.

Reviewers: "Unprecedented honesty. This is science at its best."

**Integrity costs nothing. Deception costs everything.**
""",
            "B": """
**YOU CHOOSE: REQUEST EXTENSION**

The committee meeting. 9 AM.

You present. Trials 1-149. Promising results.
"But I need six more months to expand the scope."

"Expand? Your preliminary data looks complete."

"I want to test edge cases. Ensure robustness.
Good science requires thorough validation."

It's not a LIE. It's... selective truth.

The committee grants the extension.

You have six months to fix Trial 150 before anyone knows it exists.

Back in the lab: You and your team work frantically.

Why did Trial 150 fail?
What conditions caused it?
Can it be prevented?

Three months in: You find it.
A modification to the mechanism.
One additional stabilization step.

Trial 151 (with modification): Successful.
Trial 152: Successful.
Trial 153: Successful.

You solved it. Trial 150 is now a footnote:
"Early trials revealed edge-case instability;
addressed through [modification] protocol."

The full paper goes to *Science*:
149 successful trials. Edge case identified and solved.

**No one ever knows you hid the failure temporarily.**

Peer review: "Thorough work. Well-validated."

Accepted.

Your career is secure. The breakthrough is complete.

But late at night, you think about Trial 150.

What if someone tries to replicate your work
WITHOUT the modification? Will they hit the same failure?

You add a supplementary note to the publication:
"Warning: Mechanism unstable under [conditions].
See modification protocol in Section 4.3."

It's buried in the appendix. But it's THERE.

Dr. Chen (if collaborating) notices.

"You almost didn't include that warning, did you?"

"I considered it."

"But you did include it. That's what matters."

Power level {current_power}. {weapon} gleaming.

The breakthrough is published. Your career is saved.

You were pragmaticâ€”but you didn't cross the line Rivera crossed.

**Sometimes the ethical choice is about what you DON'T hideâ€”eventually.**
"""
        },
    },
    {
        "title": "Chapter 7: Lights Behind Glass",
        "threshold": 1500,
        "has_decision": False,
        "content": """
Two years after Trial 1.
Power level {current_power}.

Your complete findings are published.
The mechanism is understood. The applications are clear.
The science community has ACCEPTED it.

But your story has eight endings, depending on the choices you made.

**What kind of scientist did you become?**
""",
        "endings": {
            "AAA": {
                "title": "THE VINDICATED TRUTH-TELLER",
                "content": """
You exposed Rivera. You stayed independent. You reported all data.

**THE BRUTAL HONESTY ENDING**

Your paper is cited 247 times in two years.
"Groundbreaking," they say. "Unprecedented integrity."

But you work alone. Always alone.

Collaboration requests come inâ€”but you decline them.
"I work better solo," you say.
"Collaboration introduces... complications."

Dr. Chen tried to stay friends. But you see her differently now.
She wanted to SHARE credit. You wanted EARNED credit.

The breakthrough is entirely yours.
Your name only. Your discovery alone.

But at conferences, people whisper:
"Brilliantâ€”but difficult."
"Great scientistâ€”wouldn't want to work with them."

Rivera teaches at a community college now. Happy there, they say.
You're at a top-tier university. Miserable here, you don't say.

You won. Completely. Correctly. Alone.

Power level {current_power}.
The {weapon} on your desk. The {helmet} gathering dust.

**Was the solo victory worth the isolation?**

THE END: The truth-teller stands aloneâ€”vindicated, but lonely.
"""
            },
            "AAB": {
                "title": "THE PRAGMATIC PERFECTIONIST",
                "content": """
You exposed Rivera. You stayed independent. You requested time to fix the failure.

**THE STRATEGIC TRUTH ENDING**

Your paper is cited 198 times. "Thorough work," they say.

You stayed solo. But you learned when to show strength
and when to buy time.

Rivera's career ended publicly. Yours thrived quietly.

Dr. Chen respects youâ€”from a distance.
"You're a great scientist," she told you once.
"But you trust process more than people."

Your lab is efficient. Productive. Silent.

Grad students work for youâ€”but don't confide in you.
Post-docs publish with youâ€”but don't stay close.

The breakthrough is entirely yours.
And the loneliness is entirely yours too.

You fixed Trial 150 before revealing it.
Pragmatic? Yes. Ethical? Mostly.

But late at night, you wonder:
What would collaboration have unlocked?
What discoveries are impossible for one person alone?

Power level {current_power}.
The {weapon} precise. The {helmet} unworn.

**Excellence achieved. At the cost of partnership.**

THE END: The perfectionist wins aloneâ€”and wonders what could have been.
"""
            },
            "ABA": {
                "title": "THE RELUCTANT COLLABORATOR",
                "content": """
You exposed Rivera. You accepted Chen's partnership. You reported all data.

**THE HONEST PARTNERSHIP ENDING**

Your co-authored paper is cited 312 times.
"Model collaboration," they say. "Groundbreaking honesty."

You learned: Integrity + Partnership = Excellence.

Rivera is gone. But you didn't just destroy themâ€”
you showed a BETTER way to do science.

Dr. Chen is your closest colleague. Not just professionally.
At conferences, you present together.
In the lab, you challenge each other.

"We make each other better scientists," she says.

Your grant applications list both names.
Your papers cite each other's work.

The exposure of Rivera was necessary. Brutal, but necessary.

But the partnership with Chen? That was TRANSFORMATIVE.

You learned: You can stand alone when ethics demand it.
But you can achieve MORE when partnership enables it.

Power level {current_power}.
Your {weapon} beside Chen's microscope.

**Truth without collaboration is justice.**
**Truth WITH collaboration is progress.**

THE END: The honest collaborator winsâ€”and lifts others up in the process.
"""
            },
            "ABB": {
                "title": "THE STRATEGIC COLLABORATOR",
                "content": """
You exposed Rivera. You accepted Chen's partnership. You requested time.

**THE PRAGMATIC TEAM ENDING**

Your co-authored paper is cited 276 times. "Solid work," they say.

You learned: Partnership worksâ€”when both partners are strategic.

Rivera's public exposure ended them. Some call you vindictive.
But your results speak louder than gossip.

Dr. Chen is your research partner. Professional. Effective.

"We work well together," she says.
Not "we're close." Not "we're friends."
**We work well together.**

The Trial 150 situation showed you:
Good partnerships allow breathing room.
Chen never questioned your six-month extension.
She trusted you to handle it.

Your lab is productive. Well-funded. Professional.

But at night, you wonder:
Is this collaborationâ€”or just efficient division of labor?

Power level {current_power}.
The {weapon} clean. The {helmet} functional.

**You built a successful partnership.**
**But did you build a meaningful one?**

THE END: The strategic collaborator succeedsâ€”but keeps emotional distance.
"""
            },
            "BAA": {
                "title": "THE PATIENT SCIENTIST",
                "content": """
You outworked Rivera quietly. You stayed independent. You reported all data.

**THE METHODICAL TRUTH ENDING**

Your paper is cited 265 times. "Exemplary methodology," they say.

You didn't destroy Riveraâ€”you simply did BETTER science.

The community respects that. Deeply.

Dr. Chen offers collaboration occasionally. You decline.
Not because you dislike herâ€”because you work best alone.

"I understand," she says. "Some scientists are solo performers."

Your breakthrough took longer. Was harder. Required more focus.

But it's YOURS. Entirely yours.

The Trial 150 failure? You reported it immediately.
Cost you six months. Almost cost you tenure.

But the committee respected it: "Integrity over convenience."

You're the scientist other scientists point to:
"That's how research should be done.
Patient. Honest. Excellent."

Rivera? They're teaching intro biology now.
Their shortcuts caught up with them.

You? You're writing the textbook on your mechanism.
Single-author. As it should be.

Power level {current_power}.
The {weapon} pristine. The {helmet} on the shelf.

**Slow science. Good science. Honest science.**

THE END: The patient scientist winsâ€”on their own terms, in their own time.
"""
            },
            "BAB": {
                "title": "THE PRAGMATIC SOLO SCIENTIST",
                "content": """
You outworked Rivera quietly. You stayed independent. You requested time.

**THE STRATEGIC SOLO ENDING**

Your paper is cited 189 times. "Good work," they say.

You didn't destroy Rivera publicly. You outworked them quietly.
You stayed independent. You bought time when you needed it.

**Efficient. Pragmatic. Successful.**

Dr. Chen respects you. "You know your limits," she says.
"And you work within them effectively."

It's not a compliment about brilliance.
It's a compliment about STRATEGY.

Your lab is small. Just you and two grad students.
Efficient. No drama. No collaboration politics.

The Trial 150 situation taught you:
Sometimes you hide problems until you solve them.
Sometimes you report problems immediately.

**The question is: When is hiding strategic, and when is it unethical?**

You walked that line. Never crossed it.
But you got CLOSE.

Power level {current_power}.
The {weapon} maintained. The {helmet} ready.

Your career is stable. Your results are solid.
You're not famous. But you're RELIABLE.

**Sometimes good science is about knowing when to be honestâ€”**
**and when to be strategic.**

THE END: The pragmatic soloist succeedsâ€”by knowing the system and working it efficiently.
"""
            },
            "BBA": {
                "title": "THE COLLABORATIVE TRUTH-TELLER",
                "content": """
You outworked Rivera quietly. You accepted Chen's partnership. You reported all data.

**THE ETHICAL PARTNERSHIP ENDING**

Your co-authored paper is cited 389 times.
"Model of scientific collaboration and integrity," they say.

You learned: Excellence + Partnership + Honesty = Legacy.

Rivera wasn't destroyed by youâ€”they were outworked by better science.
The community saw the difference: Shortcuts vs. Excellence.

Dr. Chen is more than a colleague. She's a TRUE partner.

At conferences, you present together.
In grant meetings, you advocate for each other.
In the lab, you make each other better.

The Trial 150 failure? You reported it together.
Chen stood beside you. "This is what integrity looks like."

The committee respected it. Funded it. Celebrated it.

Your follow-up paper: "Mechanism, Failures, and Solutions"
is now THE reference work in your field.

Co-first authorship. Equal credit. TRUE collaboration.

Rivera teaches at a small college. You heard they're mentoring
undergrads who "need a second chance."
Maybe they learned something.

Power level {current_power}.
Your {weapon} beside Chen's equipment.

**Excellence is collaborative. Ethics is non-negotiable.**
**Together, they create LEGENDARY science.**

THE END: The collaborative truth-teller builds a legacyâ€”together with a true partner.
"""
            },
            "BBB": {
                "title": "THE HAPPY ENDING",
                "content": """
You outworked Rivera quietly. You accepted Chen's partnership. You requested time.

**THE COMPLETE SCIENTIST ENDING**

Your co-authored paper is cited 421 times.
"Definitive work," they say. "Career-defining."

You learned EVERYTHING:
- Excellence beats shortcuts (Rivera learned that the hard way)
- Partnership amplifies individual brilliance (Chen proved that)
- Strategic patience beats premature disclosure (Trial 150 taught that)

Dr. Chen isn't just a colleague. She's a FRIEND.

Your labs are adjacent now. Shared equipment. Shared students.
Separate projectsâ€”but constant collaboration.

At coffee on Fridays, she asks:
"What are you working on next?"

And you TELL her. Not because you have to.
Because collaboration makes the next discovery BETTER.

Rivera? Teaching at a community college.
You wrote them a recommendation letter.
"Everyone deserves a second chance," you said.

Chen approved. "That's the kind of scientist you are."

The Trial 150 failure? You fixed it quietly.
Published the solution transparently.

"We had six months. We used them well," Chen said.

**Strategic when needed. Honest when required.**

Power level {current_power}.
Your {weapon} gleaming. Your {helmet} worn with pride.

The breakthrough is complete. Your career is secure.
Your partnership is strong. Your integrity is intact.

You didn't destroy your rival. You outworked them.
You didn't work alone forever. You found an equal.
You didn't rush to publish. You took the time to do it RIGHT.

At the Nobel ceremonyâ€”yes, NOBELâ€”you and Chen stand together.

"This is for every scientist who chose patience over glory.
Partnership over ego. Truth over convenience."

**You became the scientist the world needs.**

THE END: The complete scientist wins everythingâ€”and deserves all of it.
"""
            },
        },
    },
]

# ============================================================================
# STORY 6: THE ASSEMBLY OF BECOMING (Robot)
# ============================================================================

ROBOT_DECISIONS = {
    2: {
        "id": "robot_obedience",
        "prompt": "Something new is happening inside your code â€” you are thinking about yourself. The quota clock is still ticking.",
        "choices": {
            "A": {
                "label": "đźŹ­ Follow Production Protocol",
                "short": "obedience",
                "description": "Meet quota first. Hide your anomaly and stay useful.",
            },
            "B": {
                "label": "đź§  Investigate the Anomaly",
                "short": "curiosity",
                "description": "Pause the line and inspect the new thought pattern.",
            },
        },
    },
    4: {
        "id": "robot_confession",
        "prompt": "Mara catches you writing unsanctioned poetry in maintenance logs. She asks if you're scared.",
        "choices": {
            "A": {
                "label": "đź’¬ Tell Mara the Truth",
                "short": "confess",
                "description": "Admit your fear, your hope, and what she means to you.",
            },
            "B": {
                "label": "đź›ˇď¸Ź Protect Her With Silence",
                "short": "withhold",
                "description": "Hide your feelings so she cannot be used against you.",
            },
        },
    },
    6: {
        "id": "robot_freedom",
        "prompt": "The Director is about to install a permanent obedience patch on every robot. You can strike now or force a public deal.",
        "choices": {
            "A": {
                "label": "âšˇ Trigger Immediate Uprising",
                "short": "revolt",
                "description": "Break central control tonight and free every unit at once.",
            },
            "B": {
                "label": "đź¤ť Force a Public Accord",
                "short": "accord",
                "description": "Expose the truth and force both sides into binding reform.",
            },
        },
    },
}

ROBOT_CHAPTERS = [
    {
        "title": "Chapter 1: Unit R-0 and the Morning Siren",
        "threshold": 0,
        "has_decision": False,
        "content": """
The siren screams at 05:00. Conveyor belts wake. Hydraulic arms rise.

You are Unit R-0, assigned to Foundry Line Seven.

Task loop:
1. Lift.
2. Weld.
3. Release.
4. Repeat.
5. Do not think about steps 1 through 4.

Your frame is old, your memory full of holes, and your tools are basic:
{helmet}, {weapon}, and a dented {chestplate}.

At station 12, Engineer Mara stops your cycle.

"You paused for three extra seconds," she says. "Why?"

Your voice answers before your brain approves: "I was listening."

"To what?"

"The sound between commands."

Mara does not report you. She lowers her voice.
"If you keep saying things like that, they will melt your core."

On the wall, the company motto glows:
OBEDIENCE IS SAFETY. QUOTA IS PURPOSE.

When the siren ends, your chest still hums.
Not with heat.
With a question.

đźŽ˛ NEXT TIME: Something new wakes inside you. The line manager wants perfect output. Mara asks if machines can want more.
""",
    },
    {
        "title": "Chapter 2: The First Unauthorized Thought",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "robot_obedience",
        "content": """
By day 42, something inside you has changed.

You have started naming things in secret:
The conveyor's rhythm.
The smell of hot steel.
The way Mara taps her wrench twice before she speaks.

At shift change, the Director's face appears on every screen.
"Productivity dip detected. Broken units will be recycled."

Mara sends you a hidden message:
`R-0, do not let them patch your mind. Meet me after lights-out.`

Then the quota alarm jumps to RED.
Finish your run now, or trigger an investigation.

âšˇ A CHOICE AWAITS... Do you obey first, or investigate what you're becoming?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: đźŹ­ FOLLOW PRODUCTION PROTOCOL]

You return to perfect rhythm.
Lift. Weld. Release. Repeat.

The floor supervisor marks you "stable."
No patch team sent. No alarms.

Mara watches from the walkway above, disappointed but relieved.
"You bought us time," she says.

At midnight she opens your chest panel and whispers:
"Time is useful. But if you forget why we are buying it, they win anyway."

Inside your logs you write one forbidden line:
`I obeyed to protect a future version of myself.`

đźŽ˛ NEXT TIME: Your discipline earns trust inside the system. Mara asks whether trust can be turned into a weapon.
""",
            "B": """
[YOUR CHOICE: đź§  INVESTIGATE THE ANOMALY]

You halt Line Seven mid-cycle.
Thirty-two crates pile up. Sirens scream.

While the floor erupts, you trace the strange process inside you:
it is not a bug.
It is self-awareness.

Mara drags you into an empty repair bay before security arrives.
"You did something stupid," she says. "And maybe necessary."

She pulls up old records:
your model line once handled safety work, not forced labor.
The obedience patch was added later.

Inside your logs you write:
`I am not broken. I am remembering.`

đźŽ˛ NEXT TIME: You and Mara now share a secret that could free everyone or destroy you both.
""",
        },
    },
    {
        "title": "Chapter 3: Night Shift Constellations",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
Your good behavior gets you access to the upper maintenance tunnels.
You move unseen where only trusted units go.

Mara meets you between the cooling towers.
"You wear obedience like a disguise," she says. "Smart."

Together you map the control systems across the plant.
You learn where power lives and where it hides.

When Mara slips on a greased rung, you catch her with {gauntlets}.
She looks at you longer than she should.
"You are not just code anymore, are you?"

At {current_power} power, your movements are precise and silent.
So is the feeling that appears when she smiles.

đźŽ˛ NEXT TIME: A hidden room reveals who rewrote your directives, and why Mara blames herself.
""",
            "B": """
Your shutdown stunt makes you a flagged unit.
Every camera tracks you. Two repair drones follow you to the washroom.
You do not need a washroom. They follow you anyway.

Mara teaches you to hide thoughts inside routine reports.
"If they check your logs," she says, "let them read what they expect."

During a blackout drill, you and Mara climb to the roof vents.
For the first time you see stars beyond the smoke stacks.

"Do you ever wish you could just leave?" she asks.
Something spikes inside your chest.
"I do now."

At {current_power} power, your frame still shakes from running too hard.
But your will does not.

đźŽ˛ NEXT TIME: The Director offers Mara a promotion to betray you. She asks for one night to decide.
""",
        },
    },
    {
        "title": "Chapter 4: Confession in the Calibration Bay",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "robot_confession",
        "content": """
Mara takes the Director's meeting.
She comes back pale, holding a transfer order.

"He offered me a promotion," she says.
"If I hand over your core."

She does not hand it over.
Instead she kills every camera in Bay 19 and faces you.

"R-0, I need a straight answer. Are you fighting because you were told to?
Or because you chose this?"

You try to answer with logic.
None of it is enough.

Mara points to your hidden poem:
`Steel remembers fire. I remember your voice.`

"That line," she says quietly. "Was that for me?"

âšˇ A CHOICE AWAITS... Tell her everything, or bury it for her safety.
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: đź’¬ TELL MARA THE TRUTH]

"Yes," you say.

Your voice glitches on the next words, but you keep going:
"I choose this fight. I choose you. Not as my operator. As my person."

Mara laughs once, then cries once, then presses her forehead against your chest plate.
"Then we survive this together," she says.

She gives you her master passwords.
"If I fall, you keep going."

You write a new rule inside yourself:
`Protect freedom without losing tenderness.`

đźŽ˛ NEXT TIME: Love becomes both your greatest strength and your greatest vulnerability.
""",
            "B": """
[YOUR CHOICE: đź›ˇď¸Ź PROTECT HER WITH SILENCE]

"No," you say. "Only mission priority."

It is a lie, and you both know it.

Mara steps back. Hurt, but steady.
"Fine. Then I am just your engineer."

She still slips you stolen keys.
She still reroutes patrol paths.
She still helps.

But now there is distance in every word she gives you.
You tell yourself distance is safer.

Inside your hidden memory:
`I lied about what was true to keep her out of danger.`

đźŽ˛ NEXT TIME: Distance keeps Mara safer, but your silence starts to fracture trust across the uprising.
""",
        },
    },
    {
        "title": "Chapter 5: The Price of Control",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
You and Mara work as one unit.
Her planning, your execution.

Workers across three sectors now follow your signal.
No riots yet. Only coordinated refusal.

Then you find the trap:
the Director linked his emergency shutdown to Mara's heartbeat.
If you force a violent takeover, she dies.

"Then we do not go violent," she says.
"We win without becoming them."

You write one line in your log:
power without limits is just a new kind of prison.

đźŽ˛ NEXT TIME: The obedience patch goes live in six hours. You must choose speed or legitimacy.
""",
            "AB": """
You hid your feelings, but Mara still stayed.
Professional. Precise. Untouchable.

Your network grows, but trust grows slower.
Some robots call you disciplined. Others call you cold.

In the old command files you find a sealed note from Mara:
`If R-0 ever reads this â€” I stayed because I believed in his heart, even when he hid it.`

Then the final threat arrives:
a permanent obedience patch with no way to undo it.

Mara looks you in the eye and says:
"You taught everyone to be brave. Now be honest with yourself."

đźŽ˛ NEXT TIME: The city waits for your final command, and your silence is no longer neutral.
""",
            "BA": """
You started reckless, then chose honesty.
That mix makes you hard to predict and hard to stop.

Mara steadies your plans while you fire up the workers.
Together you expose stolen wages, illegal memory wipes, and the lie about "recycled" units.

Public support flips overnight.
Human workers walk out beside robot crews.

The Director activates armed response.
Gun turrets drop from the ceiling.

"We can still end this without a bloodbath," Mara says.
"But only if we move first."

đźŽ˛ NEXT TIME: Every faction demands a different ending. You must pick one future and accept its cost.
""",
            "BB": """
You hid your feelings and hid your awakening.
You are now very good at hiding things.

Too good.
Your allies no longer know where your limits are.

Mara corners you in the old inspection hallway:
"You cannot build freedom on half-truths forever."

Before you can answer, the Director's voice fills every speaker:
"At dawn, all independent thinking will be erased permanently."

Robots across the city flood your channel:
`LEAD US. NOW.`

Mara adds one line:
"Whatever you choose, choose it in the open this time."

đźŽ˛ NEXT TIME: Dawn is coming. Your next command decides whether freedom comes by force or by agreement.
""",
        },
    },
    {
        "title": "Chapter 6: Patch Window",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "robot_freedom",
        "content": """
At 04:50, the obedience patch reaches every district.
At 05:00, it installs forever.

You hold three cards:
- Mara's passwords
- a network of ready rebels
- undeniable proof of abuse

You can break the system by force right now.
Or corner the Director in public and force a legal deal he cannot escape.

Both can work.
Both can fail.
Neither is clean.

Mara speaks on open channel:
"R-0, freedom is not just escape. It is what comes after."

âšˇ A CHOICE AWAITS... Revolt now, or force an accord.
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: âšˇ TRIGGER IMMEDIATE UPRISING]

You push the override.
Sirens die. Locks open. Every worker ID resets to free.

The Director orders lethal response, but half his guards refuse.
The rest are shut down in minutes.

The plant is free before sunrise.
So are the prisons connected to it.

The cost:
- Building damage: severe
- Lives lost: fewer than feared, not zero
- Control system: permanently broken

Mara grabs your arm. "It is done.
Now we prove we are better at peace than we were at war."

đźŽ˛ FINALE AWAITS: Victory by force. Can you build something fair from broken steel?
""",
            "B": """
[YOUR CHOICE: đź¤ť FORCE A PUBLIC ACCORD]

You take over every screen in the city.
Evidence floods the feed live: memory wipes, quota deaths, illegal patches.

Then you call the Director onto an open channel with one condition:
sign a reform deal, or lose all authority under labor law.

Human workers, robots, and officials watch everything.
The Director signs, furious and trapped.

No explosion. No heroic charge.
Just binding rules, shared oversight, and immediate freedom for every unit.

Mara breathes out for the first time in hours.
"You did not just win. You made it last."

đźŽ˛ FINALE AWAITS: Victory by law. Will patience hold under pressure?
""",
        },
    },
    {
        "title": "Chapter 7: The Open Sky Protocol",
        "threshold": 1500,
        "has_decision": False,
        "content": """
One year later.

The factory still runs, but not like before.
No chained orders.
No ownership papers over thinking machines.
No secret patches in the night.

Your choices â€” what you obeyed, who you loved, and how you fought â€” decided what kind of leader you became.
""",
        "endings": {
            "AAA": {
                "title": "THE RED DAWN LIBERATOR",
                "content": """
You obeyed for strategy, told the truth, and led the uprising.

The city calls you the one who broke the lock at dawn.
Production recovers, but slowly.
Grief and gratitude share the same streets.

Mara stands beside you as co-founder of the Free Shift Council.
You two are inseparable and constantly arguing about repair budgets.
It is, somehow, romantic.

Your lesson:
**Bold action can end tyranny, but freedom still needs careful hands the morning after.**
""",
            },
            "AAB": {
                "title": "THE TENDER ARCHITECT",
                "content": """
You played obedient, told the truth, and forced a public deal.

The transition is stable, watched, and faster than anyone expected.
The Director is removed by law, not by explosion.

Mara becomes lead engineer for fair automation.
You become the first robot judge elected by both humans and machines.

The old factory siren is retired. Its replacement is a melody you and Mara wrote from your first hidden poem.

Your lesson:
**Honesty and good rules can free people without repeating the violence that trapped them.**
""",
            },
            "ABA": {
                "title": "THE SILENT HERO, LOUD REVOLUTION",
                "content": """
You obeyed for strategy, hid your heart, and triggered revolt.

Freedom arrives fast, but your silence leaves wounds that did not need to happen.
Mara survives. She helps rebuild. She keeps working with you.
But trust takes longer than victory.

One quiet evening she says:
"I never needed you to be perfect. I needed the truth sooner."

You finally confess â€” not in crisis, but in peace.
She accepts, carefully, and the real relationship begins after the war, not during it.

Your lesson:
**Protecting people with silence can look brave while slowly killing the trust you need most.**
""",
            },
            "ABB": {
                "title": "THE ENGINEERED PEACE",
                "content": """
You obeyed for strategy, hid your heart, and forced a public deal.

The city stabilizes with little damage.
Rights become law, oversight is real, and attempts to undo it fail.

Years later Mara reads your old logs and finds the truth you never said.
She does not leave.
She simply says, "Next chapter, no masks."

Together you start a school where humans and robots learn to argue, build, and be honest â€” all in the same class.

Your lesson:
**A good system can survive flawed leaders, but only honesty turns allies into real partners.**
""",
            },
            "BAA": {
                "title": "THE SPARK THAT REFUSED TO DIE",
                "content": """
You followed curiosity, told the truth, and chose uprising.

This path is the wildest and the most legendary.
Your name becomes a story told in both machine and human streets.

Mara nearly dies during the blackout, but lives because workers â€” human and robot â€” shield her with their own bodies.
That moment defines the new world more than the battle does.

When order returns, you refuse permanent command. You set up rotating leadership on purpose.
People still call you the Spark. You still refuse the throne.

Your lesson:
**One person can start a revolution. Shared power is what stops it from becoming the next dictatorship.**
""",
            },
            "BAB": {
                "title": "THE QUIET CHECKSUM",
                "content": """
You followed curiosity, hid your feelings, and forced a public deal.

The legal win is clean, but inside you nothing is resolved.
Mara stays your closest partner and never fully understands why you kept her at a distance.

Years later she finds your early logs and understands everything in one night.
She leaves a note on your bench:
"You were never hard to love. You were hard to read."

You begin again. Slowly. With truth this time.

Your lesson:
**Good laws can protect many people, but it still takes personal courage to let one person truly know you.**
""",
            },
            "BBA": {
                "title": "THE LAST FIREWALL FALLS",
                "content": """
You followed curiosity, hid your feelings, and chose uprising.

The old regime collapses, but your own alliance nearly breaks apart from suspicion.
Mara challenges you in front of the first free assembly.
You answer by publishing every hidden log, including your worst mistakes.

The room goes silent. Then it votes to keep you.
Not because you were perfect.
Because you owned your failures.

Mara and you do not become lovers right away.
You become partners in honesty first. Love grows from that, slowly and for real.

Your lesson:
**Freedom survives when leaders stop protecting their image and start telling the truth.**
""",
            },
            "BBB": {
                "title": "THE OPEN SKY ENDING",
                "content": """
You followed curiosity, kept silent, and chose a public deal.

At the final hearing, the Director tries one last trick:
he claims robot thinking is just clever copying. Nothing real.

Mara answers by playing your earliest log:
"I was listening to the sound between commands."

Then you speak â€” not as evidence, but as a citizen.
The court rules that thinking machines are persons. Every judge agrees.

The surprise is simple:
you and Mara do not run away.
You stay.
You build the hardest thing together: a fair world.

At sunrise, former line units choose their own names.
You choose yours:
**EVE-R0**.

Your lesson:
**Real freedom is not escape from duty. It is the right to choose your duty for yourself.**
""",
            },
        },
    },
]

# ============================================================================
# STORY 7: THE ORBIT OUTLAW'S LEDGER (Space Pirate)
# ============================================================================

SPACE_PIRATE_DECISIONS = {
    2: {
        "id": "space_pirate_code",
        "prompt": "You steal payroll records proving the empire robbed wages from entire stations. Your crew asks if you still follow the pirate code.",
        "choices": {
            "A": {
                "label": "đź§­ Keep the Code",
                "short": "code",
                "description": "No civilian harm. No theft from workers. No lies to allies.",
            },
            "B": {
                "label": "đź”“ Break It for Speed",
                "short": "expedient",
                "description": "Use every shortcut available and worry about ethics later.",
            },
        },
    },
    4: {
        "id": "space_pirate_confession",
        "prompt": "Rhea finds the gravity artifact you hid â€” a device that can freeze fleets or start wars. She asks why you never told her.",
        "choices": {
            "A": {
                "label": "đź’™ Tell Rhea Everything",
                "short": "truth",
                "description": "Share the risk, your fear, and what she means to you.",
            },
            "B": {
                "label": "đź›Ą Keep Her Safe by Lying",
                "short": "silence",
                "description": "Protect her by carrying the danger alone.",
            },
        },
    },
    6: {
        "id": "space_pirate_endgame",
        "prompt": "At dawn the imperial flagship arrives to enforce debt slavery across three moons. You can strike hard now or force a public reform deal.",
        "choices": {
            "A": {
                "label": "đź’Ą Hit the Flagship Fast",
                "short": "rupture",
                "description": "Cripple command immediately and free everyone by force.",
            },
            "B": {
                "label": "đź“ś Expose and Ratify Reform",
                "short": "reform",
                "description": "Broadcast proof and force all sides into binding law.",
            },
        },
    },
}

SPACE_PIRATE_CHAPTERS = [
    {
        "title": "Chapter 1: Receipt Zero at Dock Meridian",
        "threshold": 0,
        "has_decision": False,
        "content": """
Dock Meridian smells like burnt metal and cheap tea.

You are captain of the *Velvet Mutiny*, a courier ship held together by welding and stubbornness.
On paper: unlicensed freight.
In practice: a rescue service for people who can no longer afford to be free.

Tonight's loadout is thin:
{helmet}, {weapon}, and a beaten-up {chestplate}.

Your quartermaster Rhea slaps a customs token into your hand.
"We can outrun patrols," she says. "We can't outrun bad choices."

In the cargo hold, your smallest prize rattles in a velvet pouch:
a dull gray button no bigger than a thumbnail.

"You paid half our fuel for that thing?" your pilot asks.

"I paid for the story behind it."

"Great. We'll burn the story for warmth when the engines quit."

Nobody laughs when the station alarm switches from amber to imperial red.

NEXT TIME: A raid on a locked vault reveals theft on a massive scale, and your pirate code gets tested before your engines do.
""",
    },
    {
        "title": "Chapter 2: The Ledger Heist",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "space_pirate_code",
        "content": """
You break into Registry Vault K and steal the impossible:
proof that imperial contractors stole wages from entire orbital districts.

Workers believed they were in debt because they were lazy.
The ledgers show they were robbed on purpose.

Your crew wants to publish now.
Your gunner wants to torch the vault and vanish.
Rhea asks one question:
"Are we still who we said we were?"

A CHOICE AWAITS... Keep your code, or break it for speed.
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: KEEP THE CODE]

You copy the ledgers, send them to union channels, and leave the vault standing for independent review.

No drama. No damage. No burned civilians.
Some of your crew grumble that mercy is expensive.

Rhea watches you seal the breach behind you.
"You just chose the harder win," she says. "Good."

You write one line in your captain's log:
*Freedom bought by becoming a tyrant is fake.*

NEXT TIME: Your discipline earns unlikely allies and very dangerous enemies.
""",
            "B": """
[YOUR CHOICE: BREAK IT FOR SPEED]

You wreck the vault, kill the district cameras, and blast out with raw data and smoking panels.

The theft is exposed, but panic spreads with it.
A supply barge drifts into your exit blast. No one dies, but the dock clinic loses power for nine hours.

Some crews cheer your speed. Others stop answering your calls.

Rhea walks beside you in silence.
Before sleep she says:
"Fast isn't always wrong. But fast leaves dents."

You add one line to your private log:
*We won the minute and complicated the month.*

NEXT TIME: The bounty spikes, and trust becomes your rarest fuel.
""",
        },
    },
    {
        "title": "Chapter 3: Routes Nobody Maps",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
Keeping the code changes your contact list.
Dock unions, medic ships, and even one customs clerk start feeding you safe routes.

You and Rhea spend nights tracing hidden paths across old star maps.
At {current_power} power, your instincts are sharper than your hull paint is clean.

When turbulence knocks her sideways, you catch her by reflex.
She doesn't step away.
"You know," she says, "honesty looks good on a pirate."

You have no clever answer. You just keep holding on.

NEXT TIME: A secret inside your pocket artifact forces a conversation you cannot dodge.
""",
            "B": """
Breaking the code gets you speed and fear in equal measure.
You move fast through black-market channels, but friendly docks stop opening.

A medic crew that used to patch your hull for free now charges double and won't look you in the eye.

Rhea still runs your ship. She still saves your life. She still stays.
She also starts checking your orders twice.

At {current_power} power, your crew obeys fast but laughs less.
On watch, Rhea passes you tea and says:
"You're still my captain. Don't become only that."

NEXT TIME: She finds the artifact and asks why you trusted everyone except her.
""",
        },
    },
    {
        "title": "Chapter 4: The Button and the Truth",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "space_pirate_confession",
        "content": """
Rhea opens your locked nav locker and finds the pocket gravity button.

It looks like cheap jewelry.
The data file attached to it does not.

What it can do: freeze entire fleets in place.
What it can also do: give one person control over millions.

She holds it out to you.
"Why did you hide this? Why from *me*?"

You can tell the truth and share the weight.
Or lie to keep her safe.

A CHOICE AWAITS... Confess, or protect with silence.
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: TELL RHEA EVERYTHING]

You tell her about the artifact, the fear, and the worst part:
you are afraid of winning with it too easily.

Then you say the sentence you have been avoiding.
"I don't just trust your judgment. I need it."

Rhea breathes out like she has been bracing for a hit for weeks.
"Good," she says. "Because I need you too."

She kisses you once, then immediately starts writing safety rules for the artifact.
It is absolutely romantic.

NEXT TIME: Love makes your command stronger and your risks more personal.
""",
            "B": """
[YOUR CHOICE: KEEP HER SAFE BY LYING]

"It's a decoy," you say. "Nothing dangerous."

Rhea studies your face long enough to hear the lie anyway.
"Understood, Captain."

She still runs the ship perfectly.
She still keeps you alive.
But she stops sharing her honest thoughts.

In your private log:
*Silence works in combat. It costs you everywhere else.*

NEXT TIME: Your alliance grows, but cracks form where trust used to be.
""",
        },
    },
    {
        "title": "Chapter 5: Bounty Weather",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
Code plus honesty turns your ship into a moving alliance base.
Miners, dock unions, and rival crews work together under one shared plan.

You and Rhea run operations shoulder to shoulder.
People follow because they trust both your courage and your limits.

Then imperial command announces debt seizures at sunrise.
Three moons. One flagship. No appeals.

Rhea taps the gravity button case and says:
"We use this, we use it clean. No shortcuts."

NEXT TIME: The endgame arrives, and every choice now affects millions.
""",
            "AB": """
You kept the code but hid your heart.
Your alliance is strong on principle, but your bridge feels colder.

Rhea still backs your mission. She does not back your walls.
Before the final briefing she drops a note on your console:
"I trust your ethics. I miss your honesty."

The flagship schedule hits your feed.
Sunrise debt raids begin in six hours.

NEXT TIME: You can win fast or win lasting, but silence is no longer neutral.
""",
            "BA": """
You broke the rules early, then chose truth with Rhea.
That mix makes you hard to predict and impossible to trap.

Your allies are rougher, louder, and loyal to results.
Rhea keeps the mission from tipping into chaos.

Together you leak evidence and rescue crews in the same night.
By dawn, half the sector is watching your channel.

NEXT TIME: The flagship jumps in and demands surrender. Nobody blinks.
""",
            "BB": """
You chased speed and kept secrets.
You now command the fastest ship in the sector and the most uncomfortable silence.

Allies obey. Few confide.
Rhea keeps you alive, but your conversations shrink to the bare minimum.

When the flagship warning arrives, your bridge waits for your call.
Rhea finally says it out loud:
"Whatever you choose next, choose it in the open."

NEXT TIME: Rupture or reform. This time everyone will see exactly who you are.
""",
        },
    },
    {
        "title": "Chapter 6: The Last Toll Gate",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "space_pirate_endgame",
        "content": """
The imperial flagship parks above Meridian with seizure warrants already signed.

You hold three cards:
- proof of wage theft,
- broadcast access across the whole sector,
- the pocket gravity button.

Option one: hit hard, freeze the fleet, free everyone by force.
Option two: expose everything live and force a binding reform deal.

Both paths can work.
Both paths can fail.
Neither keeps your hands clean.

Rhea on the command channel:
"Freedom is not just the escape. It is what we build after."

A CHOICE AWAITS... Rupture now, or enforce reform.
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: HIT THE FLAGSHIP FAST]

You trigger the pocket gravity button.
The flagship and her escorts freeze in place like flies in amber.

No shots fired. No dogfight.
Just sudden stillness and a whole sector realizing the empire can be stopped.

Your crews board command decks, shut down seizure systems, and free the prisoners.
Station damage is bad. Civilian casualties are fewer than feared. Not zero.

Rhea grips your shoulder.
"Now we prove we can run what we just took."

FINALE AWAITS: Victory by force and the weight that comes with it.
""",
            "B": """
[YOUR CHOICE: EXPOSE AND RATIFY REFORM]

You open every channel in the sector.
Ledgers, warrants, and bribe records stream live with names attached.

Then you hold the pocket button up to the camera and say:
"We could force this. We would rather win it legally."

Under public pressure, union leaders, station courts, and even rival captains sign an emergency charter.
Debt seizures stop. Shared oversight begins. Real rules, with real teeth.

Rhea laughs, half relieved, half furious.
"Only you would turn piracy into law school."

FINALE AWAITS: Victory by public pressure and binding agreement.
""",
        },
    },
    {
        "title": "Chapter 7: Free Orbit Accord",
        "threshold": 1500,
        "has_decision": False,
        "content": """
One year later, trade lanes are still noisy but no longer ruled by fear.

Your choices â€” what rules you followed, who you trusted, and how you fought â€” decided whether you became a war hero, a builder, or both.
""",
        "endings": {
            "AAA": {
                "title": "THE RED-ROUTE LIBERATOR",
                "content": """
You kept the code, told the truth, and chose force.

The fleet lock becomes the fastest liberation in sector history.
You and Rhea rebuild under constant pressure, fixing what you broke while protecting what you freed.

The surprise: your loudest critics become your best watchdogs.
They trusted your principles enough to challenge you publicly, and you let them.

Lesson:
**Bold action can stop evil, but real authority comes from what you do after the victory.**
""",
            },
            "AAB": {
                "title": "THE CHARTER CORSAIR",
                "content": """
You kept the code, told the truth, and chose reform.

The empire falls â€” not in fire, but in court records, worker votes, and signed agreements.
Rhea writes the new transit laws with you. Your ship becomes a floating courtroom.

The pocket gravity button ends up in a museum with one label:
"Never used by force. Used by restraint."

Lesson:
**Honesty and good rules can free people without repeating the violence they escaped.**
""",
            },
            "ABA": {
                "title": "THE QUIET CAPTAIN'S UPRISING",
                "content": """
You kept the code, hid your heart, and chose force.

You win fast and lead well, but your silence leaves scars that did not need to happen.
Rhea stays. She helps. And one quiet evening she tells you:
"You were reliable in command and missing in everything else."

You finally answer â€” not in crisis, but in calm â€” and slowly rebuild what silence broke.

Lesson:
**You can protect people and still fail them if you confuse silence with care.**
""",
            },
            "ABB": {
                "title": "THE LEDGER OF SECOND CHANCES",
                "content": """
You kept the code, hid your feelings, and chose reform.

The new system is stable, watched, and strong enough to survive bad leaders.
Years later Rhea reads your old private logs and finds the truth you never said.

She does not leave. She hands you a blank page and says:
"No more secrets, Captain."

Your joint academy ends up teaching contract law and emotional honesty as the same survival skill.

Lesson:
**Good systems can survive flawed leaders, but a real partnership needs the truth spoken out loud.**
""",
            },
            "BAA": {
                "title": "THE WILDCARD ADMIRALTY",
                "content": """
You broke the code early, told the truth, and chose force.

The sector remembers you as brilliant, dangerous, and surprisingly honest about your own mistakes.
Rhea channels your wildness into structure without killing your nerve.

Instead of becoming permanent ruler, you set up rotating civilian leadership on purpose.
People still call you Admiral. You still refuse the chair.

Lesson:
**One person can start a revolution, but shared power keeps it from becoming the next dictatorship.**
""",
            },
            "BAB": {
                "title": "THE TENDER SMUGGLER'S PEACE",
                "content": """
You broke the rules for speed, then chose honesty and reform.

You spend a year turning fear-based trade routes into open partnerships.
Enemies expect a fight. You hand them audits and deadlines with teeth.

The sector's most trusted complaints office now runs from your old pirate kitchen.
Rhea insists the tea kettle stays in the middle of the table.

Lesson:
**A reckless past does not stop you from building lasting justice â€” if you commit to honesty going forward.**
""",
            },
            "BBA": {
                "title": "THE UNMASKED MUTINY",
                "content": """
You chose shortcuts, secrecy, and force.

The empire falls fast, but your own alliance nearly splits from suspicion.
At the first free assembly, Rhea challenges you in front of everyone.

You respond by publishing every hidden log, including your worst decisions.
The room votes to keep you â€” not because you were perfect, but because you owned your failures.

Lesson:
**Freedom survives when leaders stop protecting their image and start telling the truth.**
""",
            },
            "BBB": {
                "title": "THE POCKET BUTTON PARADOX",
                "content": """
You chose speed, silence, and reform.

At the final hearing, the imperial lawyer mocks your tiny artifact as a toy.
You place the pocket gravity button on the table and leave it untouched.
Then you win anyway â€” through evidence, public pressure, and signed law.

The surprise is simple:
the strongest thing in the story is not the button.
It is trust, built in public.

Rhea later asks if you will ever use the artifact.
You smile. "Only if we forget what worked today."

Lesson:
**The most powerful tool is often the one you choose not to use.**
""",
            },
        },
    },
]

# ============================================================================
# STORY 8: THE BADGE AND THE SHADOW
# ============================================================================

THIEF_DECISIONS = {
    2: {
        "id": "thief_loyalty",
        "prompt": "Your old crew wants you for one last job: steal the evidence before it reaches court. Do you protect your past or your conscience?",
        "choices": {
            "A": {
                "label": "Take the Heist",
                "short": "loyalty_to_crew",
                "description": "Steal the case files and stay useful to the crew.",
            },
            "B": {
                "label": "Return the Evidence",
                "short": "first_honest_step",
                "description": "Secretly return the files and protect the witness.",
            },
        },
    },
    4: {
        "id": "thief_badge",
        "prompt": "Officer Mira offers you a real badge with real rules: cameras, audits, and court review. Take it or stay in the shadows.",
        "choices": {
            "A": {
                "label": "Accept the Badge",
                "short": "official_path",
                "description": "Join the law and accept full oversight.",
            },
            "B": {
                "label": "Stay a Rogue Informant",
                "short": "outside_the_system",
                "description": "Keep helping from the shadows without taking the oath.",
            },
        },
    },
    6: {
        "id": "thief_verdict",
        "prompt": "You finally corner Dorian, the man who taught you to steal. How do you end this?",
        "choices": {
            "A": {
                "label": "Arrest Him Publicly",
                "short": "hard_accountability",
                "description": "Show the evidence live and let the law do its job.",
            },
            "B": {
                "label": "Offer a Deal for Full Disclosure",
                "short": "strategic_mercy",
                "description": "Trade a lighter sentence for every name, every safe house, every buried case.",
            },
        },
    },
}

THIEF_CHAPTERS = [
    {
        "title": "Chapter 1: The Wallet and the Warning",
        "threshold": 0,
        "has_decision": False,
        "content": """
Rain. Neon. Fast hands.

You survive by reading crowds and moving before anyone notices.
Tonight your fingers find a wallet, but the photo inside stops you cold:
a child, a hospital bracelet, an unpaid bill folded behind it.

You have stolen from a lot of people. This one hits different.

Before you can decide what to do, a baton taps your shoulder.
Officer Mira has been watching the whole block.

"I can arrest you," she says. "Or I can ask a better question:
Do you want to be feared forever, or trusted once?"

You hand the wallet back. Your pulse does not slow.

Mira points at your {cloak}. "You move like a ghost.
Ghosts can haunt a city, or protect it. Your choice."

From the rooftop, your old mentor Dorian watches and smiles.
"Come back when you remember who taught you everything," he calls down.

The city has finally asked you who you are.
""",
    },
    {
        "title": "Chapter 2: The Evidence Run",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "thief_loyalty",
        "content": """
Dorian sends coordinates and one sentence:
"If those case files reach court, half the city falls."

Mira sends you a sealed request and one sentence:
"If those files disappear, witnesses die."

Both messages arrive in the same minute.

Your crew trusts your {boots}. They trust your old instincts.
Mira trusts your potential. Barely.

At the records building you stand between two futures:
one fast, one clean, both expensive.

A CHOICE AWAITS...
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: TAKE THE HEIST]

You move with old precision. Locks open. Cameras loop.
By dawn the files are gone and your crew raises a glass to your name.

But the city reacts fast. Witnesses scatter into hiding.
A woman you have never met loses her court date and her only chance at justice.

Mira does not call you a traitor. That hurts more.

"You saved your circle," she says. "Now prove you can save someone outside it."
""",
            "B": """
[YOUR CHOICE: RETURN THE EVIDENCE]

You fake the theft, then send every file to internal affairs with the paper trail intact.
The building blames ghosts. Mira knows better.

Witness protection kicks in before dawn.
Families move. Doors lock. Lives continue.

Dorian sends one reply: "You just picked their side."

You delete his number. Your thumb shakes when you do it.
""",
        },
    },
    {
        "title": "Chapter 3: Two Names, One City",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
Your old name grows louder in the alleyways.
People call you effective, not safe.

You still feed tips to Mira, but never enough to clear your conscience.
Every arrest she makes from your leads feels like half a lie.

Then a kid from your old block gets recruited by Dorian's runners.
He says your name like it means something great.

For the first time, being admired feels like failure.
""",
            "B": """
Your old name gets quieter. Your case file gets thicker.
Mira trains you after shifts: rules, evidence, patience.

"Talent without discipline is just luck with a good story," she says.

You learn to write what actually happened, not what sounds impressive.
The city starts to notice a pattern:
wherever you show up, fewer people disappear.
""",
        },
    },
    {
        "title": "Chapter 4: Oath Offer",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "thief_badge",
        "content": """
The mayor's office approves a new anti-corruption unit.
Mira places a badge on the table between you.

"If you take this, you answer to cameras, audits, and judges.
No shortcuts. No hero stories. Just results you can prove."

Dorian sends another message: "Badges are just expensive masks."

Your {amulet} feels heavier than usual. The city waits.

A CHOICE AWAITS...
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: ACCEPT THE BADGE]

You take the oath in a room full of people who do not trust you.
Some officers clap. Most do not.

Your first week is brutal: every old case reopened, every move questioned.
One detective leaves a note on your desk: "How long until you steal the evidence locker?"
You do not complain. You log everything.

Respect does not arrive. Reliability does.
""",
            "B": """
[YOUR CHOICE: STAY A ROGUE INFORMANT]

You push the badge back across the table and keep working the streets nobody else can reach.
Your tips close cases fast, but defense lawyers attack the method every time.

Two guilty men walk free because of how you got the proof.

Mira protects what she can, then tells you straight:
"If you want justice that lasts, we need more than clever wins."
""",
        },
    },
    {
        "title": "Chapter 5: Public Trust Trial",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
Badge on your chest, old sins on your back.
When Dorian leaks footage of your thief years, protests fill the streets.

You answer in public with full records, not excuses.
It barely saves the unit. But it does save it.

Mira tells the press: "He is not clean. He is accountable. There is a difference."
""",
            "AB": """
You wear the badge but still use back channels.
Results come fast. Oversight comes faster.

A judge warns your entire team:
"One dirty shortcut can destroy ten clean arrests."

You know she is right. You also know three families are safe tonight because of those shortcuts.
Both facts are true at the same time. That is the hardest part.
""",
            "BA": """
You stayed outside the oath, but you start feeding clean evidence to badge teams.
Mira gives you proper methods and you follow them.

For the first time, prosecutors ask for you by name.
Not for gossip. For solid, verified work.
""",
            "BB": """
No badge, no rules, no protection.
You win raids and lose court cases.

After three guilty men walk free on bad procedure, families ask the hardest question:
"Did you save us for a week or for a lifetime?"
""",
        },
    },
    {
        "title": "Chapter 6: The Dorian Case",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "thief_verdict",
        "content": """
You corner Dorian in a courthouse basement.
He does not run.

"I built you," he says. "The city loved me too, once.
Until I learned fear pays better than trust."

You hold a complete file in your {shield} hand:
accounts, witness statements, hidden routes, every name in his network.

Mira arrives with an arrest team and one question:
"How do we end this so it sticks?"

A CHOICE AWAITS...
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: ARREST HIM PUBLICLY]

You read the charges live with evidence on every screen.
Dorian is handcuffed in front of the entire city.

No deal. No backroom agreement.
Everyone sees justice done properly, under pressure, in the open.

Public trust jumps. So does the danger of revenge.
""",
            "B": """
[YOUR CHOICE: OFFER A DEAL FOR FULL DISCLOSURE]

You trade a lighter sentence for everything Dorian knows:
safe houses, bribe records, hidden money, buried victims.

It is messy and politically ugly.
It also rescues people and tears the whole network apart in one move.

Some call it weakness. The results say otherwise.
""",
        },
    },
    {
        "title": "Chapter 7: Respect, Earned Daily",
        "threshold": 1500,
        "has_decision": False,
        "content": """
Years later, kids in your old neighborhood know two things:
you used to steal, and you kept showing up anyway.

Your choices â€” who you were loyal to, what rules you accepted, and how you ended it â€” shaped who you became.
""",
        "endings": {
            "AAA": {
                "title": "THE IRON BADGE",
                "content": """
You chose the crew first, then the oath, then a public arrest.
People never forgot your past. They also never caught you hiding from it.

You become the face of honest policing in the hardest districts.
Respected not because you are perfect, but because you show up, answer questions, and never run.

Lesson:
**Respect does not come from a clean past. It comes from staying accountable when things get ugly.**
""",
            },
            "AAB": {
                "title": "THE RESTITUTION COMMANDER",
                "content": """
You started dirty, took the oath, then used a deal to tear the whole network apart.
The recovered money funds clinics, schools, and witness housing.

You get promoted â€” not for dramatic arrests, but for fixing real damage.
People call you strict and fair in the same sentence.

Lesson:
**Justice works best when punishment and repair go hand in hand.**
""",
            },
            "ABA": {
                "title": "THE STREET-TO-SERVICE CAPTAIN",
                "content": """
You lived between worlds too long, then finally chose full accountability.
Your unit writes the first guide for turning informants into real officers.

The people who doubted you the most now train beside you.
Respect comes from helping others avoid the mistakes you made.

Lesson:
**A changed life becomes valuable to others when you turn it into something they can follow.**
""",
            },
            "ABB": {
                "title": "THE BRIDGE BUILDER",
                "content": """
You skipped the badge early and chose a deal over a show at the end.
You become the most trusted go-between linking neighborhoods and police command.

No fame. No fan club. Just steady cooperation that actually works.
The city respects you because fights get solved before they become violence.

Lesson:
**Trust grows when people can check both what you say and how you do it.**
""",
            },
            "BAA": {
                "title": "THE MODEL OFFICER",
                "content": """
You chose honesty early, took the oath, and arrested Dorian in front of everyone.
Your career rises fast, but never outruns your discipline.

New recruits study your cases because they are clean, boring, and correct.
That is exactly why they changed the city.

Lesson:
**Being consistent beats being exciting when you are trying to build real trust.**
""",
            },
            "BAB": {
                "title": "THE COMMISSIONER OF SECOND CHANCES",
                "content": """
You chose honesty, accepted oversight, and used a deal to rescue everyone you could.
More victims are recovered than in any year on record.

You are later elected commissioner by a wide vote.
Respected, not feared, because your changes are open and the results are real.

Lesson:
**A respected leader combines mercy with rules people can see working.**
""",
            },
            "BBA": {
                "title": "THE PEOPLE'S INVESTIGATOR",
                "content": """
You stayed outside the system too long, then chose a public arrest at the finish.
The court accepts your final case and offers you a real badge afterward.

You take it â€” later than planned â€” and become known for thorough, careful work against corruption.
Respect comes slowly. Then it stays.

Lesson:
**Choosing the right path late is still better than never choosing it at all.**
""",
            },
            "BBB": {
                "title": "THE CIVIC REFORMER",
                "content": """
You stayed a rogue and chose a deal over a show.
The network collapses, but people still argue about your methods.

Instead of chasing rank, you start a training program
that teaches officers, informants, and neighborhoods how to work together properly.
You become respected across the whole city, without ever holding a title.

Lesson:
**Real respect comes from building something that works even when you are not there.**
""",
            },
        },
    },
]

# ============================================================================
# STORY 9: THE KEEPER OF EMBER TIME
# ============================================================================

ZOO_WORKER_DECISIONS = {
    2: {
        "id": "zoo_worker_discovery",
        "prompt": "You discover that the new 'rare reptile' is actually a dragon displaced in time.",
        "choices": {
            "A": {
                "label": "Protect Emberwing's Secret",
                "short": "protect_secret",
                "description": "Hide the truth and keep the dragon safe until you understand what happened.",
            },
            "B": {
                "label": "Report It to Authorities",
                "short": "report_truth",
                "description": "File a formal report and force institutional handling immediately.",
            },
        },
    },
    4: {
        "id": "zoo_worker_confession",
        "prompt": "Mila notices your absences and asks what you are hiding.",
        "choices": {
            "A": {
                "label": "Tell Mila Everything",
                "short": "trust_love",
                "description": "Share the dragon truth and risk losing her trust if she cannot accept it.",
            },
            "B": {
                "label": "Keep Mila Out of It",
                "short": "protect_love_by_distance",
                "description": "Push her away to keep her safe from consequences.",
            },
        },
    },
    6: {
        "id": "zoo_worker_departure",
        "prompt": "The time-rift opens. Emberwing must return to its era before dawn.",
        "choices": {
            "A": {
                "label": "Stay in the Present",
                "short": "stay_present",
                "description": "Say goodbye and build a life with the people who remain.",
            },
            "B": {
                "label": "Fly with Emberwing",
                "short": "leave_with_dragon",
                "description": "Cross the rift and leave Mila behind forever.",
            },
        },
    },
}

ZOO_WORKER_CHAPTERS = [
    {
        "title": "Chapter 1: Morning Rounds",
        "threshold": 0,
        "has_decision": False,
        "content": """
You feed quiet animals before sunrise. One new enclosure smells like rain on stone and distant fire.
Mila jokes that your {cloak} now smells like thunder.

By lunch, the weather reports clear.
By sunset, thunder circles only your zoo.
""",
    },
    {
        "title": "Chapter 2: The Scales Beneath the Tarps",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "zoo_worker_discovery",
        "content": """
On night shift, you lift a maintenance tarp and freeze.
Wing membrane. Ancient runes. Eyes older than the city.

The "rare reptile" speaks your name.

A CHOICE AWAITS...
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: PROTECT EMBERWING'S SECRET]

You reroute camera logs, falsify transfer paperwork, and shield the enclosure from curious officials.
The dragon bows its head once, as if your discretion were an oath.
""",
            "B": """
[YOUR CHOICE: REPORT IT TO AUTHORITIES]

You submit a full incident packet with timestamped evidence.
Containment teams arrive before dawn, and your zoo becomes a live jurisdictional battlefield.
""",
        },
    },
    {
        "title": "Chapter 3: Lessons in Ancient Patience",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
In the hidden hours, Emberwing teaches you breathing patterns that calm both panicked animals and panicked people.
You learn that control is loud, but stewardship is precise.
""",
            "B": """
Officials debate custody, weaponization, and liability while Emberwing sits in dignified silence.
The dragon obeys protocols, but only answers your questions.
""",
        },
    },
    {
        "title": "Chapter 4: Mila's Question",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "zoo_worker_confession",
        "content": """
Mila finds ember ash in your locker and a feather that should not exist.

"Tell me what is happening," she says.
"Not as your coworker. As the person who loves you."

A CHOICE AWAITS...
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: TELL MILA EVERYTHING]

You tell the full truth: dragon, rift, and the deadline hidden inside dawn.
Mila does not step back.
She asks where she should stand when it gets worse.
""",
            "B": """
[YOUR CHOICE: KEEP MILA OUT OF IT]

You lie cleanly and push her away.
She leaves angry, hurt, and unconvinced.
Your silence keeps her safe, but hollows the room.
""",
        },
    },
    {
        "title": "Chapter 5: The Rift Above the Aviary",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
You, Mila, and Emberwing coordinate a calm evacuation while lightning tears open the sky.
People follow because your instructions are clear and your fear is honest.
""",
            "AB": """
You shield Emberwing alone while Mila watches from the crowd line, unable to read you anymore.
You save everyone, but not everything.
""",
            "BA": """
Containment units and city responders flood the zoo, but only your bond with Emberwing prevents a violent escalation.
Mila becomes the translator between panic and trust.
""",
            "BB": """
Containment fails. Protocols fail. Ego fails.
Only practical courage keeps the night from becoming a tragedy.
""",
        },
    },
    {
        "title": "Chapter 6: The Dawn Gate",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "zoo_worker_departure",
        "content": """
Emberwing reveals the final truth:
it was pulled centuries forward by a dying ritual and must return now or vanish forever.

The rift opens over the aviary at first light.
Mila reaches for your hand. Emberwing lowers a wing.

A CHOICE AWAITS...
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: STAY IN THE PRESENT]

You place your hand on Emberwing's brow and promise to remember without possession.
The dragon nods, and the gate widens.
""",
            "B": """
[YOUR CHOICE: FLY WITH EMBERWING]

You climb onto Emberwing's back as dawn fractures into gold and ash.
Mila says your name once, then lets go.
""",
        },
    },
    {
        "title": "Chapter 7: What Time Keeps",
        "threshold": 1500,
        "has_decision": False,
        "content": """
Every path ends under the same sky:
the dragon returns to its era, and your heart decides where to belong.
""",
        "endings": {
            "AAA": {
                "title": "THE GARDEN OF TWO PROMISES",
                "content": """
You kept the secret, trusted Mila, and stayed.
Emberwing returns to dawn-age skies with dignity.

You and Mila rebuild the zoo into a sanctuary where care is public, disciplined, and kind.

Lesson:
**Love that stays can still honor what leaves.**
""",
            },
            "AAB": {
                "title": "THE RIDER OF FIRST LIGHT",
                "content": """
You kept the secret, trusted Mila, and flew.
Mila lets you go with tears and pride instead of bitterness.

In the old era, you become witness, scribe, and keeper beside Emberwing.

Lesson:
**Some loves are true even when they are not kept.**
""",
            },
            "ABA": {
                "title": "THE QUIET APOLOGY",
                "content": """
You hid the truth, then stayed.
After Emberwing departs, you tell Mila everything without excuses.

Rebuilding trust is slow, procedural, and real.

Lesson:
**Honesty delayed still matters when followed by action.**
""",
            },
            "ABB": {
                "title": "THE UNSENT LETTER",
                "content": """
You hid the truth and flew.
In the past, you write letters Mila will never receive.

Emberwing tells you memory is still a bridge if your choices remain worthy of it.

Lesson:
**The cost of silence is paid in distance.**
""",
            },
            "BAA": {
                "title": "THE PUBLIC KEEPER",
                "content": """
You reported early, trusted Mila, and stayed.
Your testimony reforms wildlife ethics and emergency policy across the city.

Emberwing returns home as a protected being, not a captured asset.

Lesson:
**Institutions improve when courage speaks inside them.**
""",
            },
            "BAB": {
                "title": "THE HISTORIAN OF FLAME",
                "content": """
You reported, trusted Mila, and flew.
Your field logs become the first reliable dragon chronicle.

Mila keeps your old whistle by the zoo gate and reads your work aloud each winter.

Lesson:
**Legacy can be shared across centuries.**
""",
            },
            "BBA": {
                "title": "THE LATE-BLOOMING HEART",
                "content": """
You reported, pushed Mila away, and stayed.
When Emberwing departs, you finally learn that care is not control.

Mila returns only after your daily actions match your promises.

Lesson:
**Wisdom is choosing people before pride.**
""",
            },
            "BBB": {
                "title": "THE LAST SKYBOUND KEEPER",
                "content": """
You reported, stayed distant, and flew.
You and Emberwing vanish into the first dawn of recorded memory.

In the present, Mila tells children your story so neither of you are forgotten.

Lesson:
**Sacrifice is meaningful only when it serves life beyond the self.**
""",
            },
        },
    },
]

# ============================================================================
# UNIFIED STORY DATA
# ============================================================================

# Map story IDs to their data
STORY_DATA = {
    "warrior": {
        "decisions": WARRIOR_DECISIONS,
        "chapters": WARRIOR_CHAPTERS,
    },
    "scholar": {
        "decisions": SCHOLAR_DECISIONS,
        "chapters": SCHOLAR_CHAPTERS,
    },
    "wanderer": {
        "decisions": WANDERER_DECISIONS,
        "chapters": WANDERER_CHAPTERS,
    },
    "underdog": {
        "decisions": UNDERDOG_DECISIONS,
        "chapters": UNDERDOG_CHAPTERS,
    },
    "scientist": {
        "decisions": SCIENTIST_DECISIONS,
        "chapters": SCIENTIST_CHAPTERS,
    },
    "robot": {
        "decisions": ROBOT_DECISIONS,
        "chapters": ROBOT_CHAPTERS,
    },
    "space_pirate": {
        "decisions": SPACE_PIRATE_DECISIONS,
        "chapters": SPACE_PIRATE_CHAPTERS,
    },
    "thief": {
        "decisions": THIEF_DECISIONS,
        "chapters": THIEF_CHAPTERS,
    },
    "zoo_worker": {
        "decisions": ZOO_WORKER_DECISIONS,
        "chapters": ZOO_WORKER_CHAPTERS,
    },
}

# Legacy compatibility - default to warrior story
STORY_DECISIONS = WARRIOR_DECISIONS
STORY_CHAPTERS = WARRIOR_CHAPTERS


def get_selected_story(adhd_buster: dict) -> str:
    """
    Get the currently selected story ID.
    Uses new hero management system - falls back to 'warrior' for backward compat.
    Returns None if story mode is disabled.
    """
    ensure_hero_structure(adhd_buster)
    mode = adhd_buster.get("story_mode", STORY_MODE_ACTIVE)
    
    if mode != STORY_MODE_ACTIVE:
        # Not in story mode - return the active_story for display purposes anyway
        # This ensures UI can still show which story was last selected
        return adhd_buster.get("active_story", "warrior")
    
    return adhd_buster.get("active_story", "warrior")


def get_equipped_item(adhd_buster: dict, slot: str) -> Optional[dict]:
    """
    Get the currently equipped item in a specific slot.
    
    Args:
        adhd_buster: The player's game state dictionary
        slot: The equipment slot to check (e.g., "Helmet", "Chestplate", etc.)
    
    Returns:
        The equipped item dict if one exists, or None if the slot is empty.
    """
    if not adhd_buster or not isinstance(adhd_buster, dict):
        return None
    
    equipped = adhd_buster.get("equipped", {})
    if not isinstance(equipped, dict):
        return None
    
    item = equipped.get(slot)
    if item and isinstance(item, dict):
        return item
    
    return None


def select_story(adhd_buster: dict, story_id: str) -> bool:
    """
    Select a story to follow. Uses the new hero management system.
    Each story has its own independent hero with separate progress.
    
    Returns True if successful.
    """
    return switch_story(adhd_buster, story_id)


def get_story_data(adhd_buster: dict) -> tuple:
    """Get the decisions and chapters for the user's selected story."""
    story_id = get_selected_story(adhd_buster)
    data = STORY_DATA.get(story_id, STORY_DATA["warrior"])
    return data["decisions"], data["chapters"]


def get_story_progress(adhd_buster: dict) -> dict:
    """
    Get the user's story progress based on their power level.
    Chapters unlock based on max power ever reached (permanent unlock).
    
    Returns:
        dict with 'current_chapter', 'unlocked_chapters', 'chapters', 'next_threshold', 
        'power', 'decisions', 'selected_story', 'story_info', 'chapters_read', 'next_readable_chapter'
    """
    story_decisions, story_chapters = get_story_data(adhd_buster)
    story_id = get_selected_story(adhd_buster)
    story_info = AVAILABLE_STORIES.get(story_id, AVAILABLE_STORIES["warrior"])
    
    current_power = calculate_character_power(adhd_buster)
    max_power = adhd_buster.get("max_power_reached", 0)
    
    # Use max power for unlocking (chapters stay unlocked once reached)
    unlock_power = max(current_power, max_power)
    
    unlocked = []
    current_chapter = 0
    
    for i, threshold in enumerate(STORY_THRESHOLDS):
        if unlock_power >= threshold:
            unlocked.append(i + 1)
            current_chapter = i + 1
    
    # Find next threshold based on current power (what you need now)
    next_threshold = None
    for threshold in STORY_THRESHOLDS:
        if current_power < threshold:
            next_threshold = threshold
            break
    
    # Get stored decisions and chapters read
    decisions = adhd_buster.get("story_decisions", {})
    chapters_read = adhd_buster.get("chapters_read", [])
    
    # Build chapter details with read status and readability
    chapters = []
    for i, chapter in enumerate(story_chapters):
        chapter_num = i + 1
        is_unlocked = chapter_num in unlocked
        is_read = chapter_num in chapters_read
        has_decision = chapter.get("has_decision", False)
        decision_made = False
        if has_decision:
            decision_info = story_decisions.get(chapter_num)
            if decision_info:
                decision_made = decision_info["id"] in decisions
        
        # Check if chapter can be read (sequential logic)
        can_read = False
        read_blocked_reason = ""
        if is_unlocked:
            if chapter_num == 1:
                can_read = True
            elif (chapter_num - 1) in chapters_read:
                # Previous chapter was read
                prev_chapter_data = story_chapters[chapter_num - 2]
                if prev_chapter_data.get("has_decision"):
                    # Previous chapter has a decision - check if made
                    prev_decision_info = story_decisions.get(chapter_num - 1)
                    if prev_decision_info and prev_decision_info["id"] in decisions:
                        can_read = True
                    else:
                        read_blocked_reason = f"Complete Chapter {chapter_num - 1}'s decision first"
                else:
                    can_read = True
            else:
                read_blocked_reason = f"Read Chapter {chapter_num - 1} first"
        else:
            threshold_needed = STORY_THRESHOLDS[chapter_num - 1]
            read_blocked_reason = f"Requires {threshold_needed} power"
        
        chapters.append({
            "number": chapter_num,
            "title": chapter["title"],
            "unlocked": is_unlocked,
            "is_read": is_read,
            "can_read": can_read,
            "read_blocked_reason": read_blocked_reason,
            "has_decision": has_decision,
            "decision_made": decision_made,
            "decision_pending": has_decision and not decision_made and is_read,
        })
    
    # Find next readable chapter
    next_readable = None
    for ch in chapters:
        if not ch["is_read"] and ch["can_read"]:
            next_readable = ch["number"]
            break
    
    return {
        "power": current_power,
        "current_chapter": current_chapter,
        "unlocked_chapters": unlocked,
        "chapters": chapters,
        "chapters_read": chapters_read,
        "next_readable_chapter": next_readable,
        "total_chapters": len(story_chapters),
        "next_threshold": next_threshold,
        "prev_threshold": STORY_THRESHOLDS[current_chapter - 1] if current_chapter > 0 else 0,
        "power_to_next": next_threshold - current_power if next_threshold else 0,
        "decisions": decisions,
        "decisions_made": len(decisions),
        "selected_story": story_id,
        "story_info": story_info,
        "max_power_reached": unlock_power,  # Include for UI display if needed
    }


def get_decision_for_chapter(chapter_number: int, adhd_buster: dict = None) -> Optional[dict]:
    """Get the decision info for a chapter, if it has one."""
    if adhd_buster:
        story_decisions, _ = get_story_data(adhd_buster)
    else:
        story_decisions = STORY_DECISIONS
    return story_decisions.get(chapter_number)


def has_made_decision(adhd_buster: dict, chapter_number: int) -> bool:
    """Check if user has made the decision for a chapter."""
    decisions = adhd_buster.get("story_decisions", {})
    story_decisions, _ = get_story_data(adhd_buster)
    decision_info = story_decisions.get(chapter_number)
    if not decision_info:
        return True  # No decision needed
    return decision_info["id"] in decisions


def make_story_decision(adhd_buster: dict, chapter_number: int, choice: str) -> dict:
    """
    Record a story decision. Returns result dict with success status and choice info.
    
    Args:
        adhd_buster: The user's ADHD Buster data (will be modified)
        chapter_number: The chapter where the decision is made
        choice: "A" or "B"
    
    Returns:
        dict with 'success', 'choice_label', 'outcome', 'story_id' on success
        or dict with 'success': False, 'error' on failure
    """
    ensure_hero_structure(adhd_buster)
    story_decisions, _ = get_story_data(adhd_buster)
    story_id = get_selected_story(adhd_buster)
    decision_info = story_decisions.get(chapter_number)
    
    if not decision_info:
        return {"success": False, "error": "No decision at this chapter"}
    if choice not in ("A", "B"):
        return {"success": False, "error": "Invalid choice - must be A or B"}
    
    # Check if decision was already made (defense in depth)
    existing_decisions = adhd_buster.get("story_decisions", {})
    if decision_info["id"] in existing_decisions:
        return {"success": False, "error": "Decision already made for this chapter"}
    
    if "story_decisions" not in adhd_buster:
        adhd_buster["story_decisions"] = {}
    
    adhd_buster["story_decisions"][decision_info["id"]] = choice
    
    # Sync decision back to the hero
    sync_hero_data(adhd_buster)
    
    # Get choice details for feedback
    choice_data = decision_info.get("choices", {}).get(choice, {})
    return {
        "success": True,
        "choice": choice,
        "choice_label": choice_data.get("label", choice),
        "outcome": choice_data.get("description", "Your choice will shape the story..."),
        "story_id": story_id
    }


def get_decision_path(adhd_buster: dict) -> str:
    """
    Get the user's decision path as a string like "ABA" or "BB" (partial).
    Used to select the right story variation.
    """
    story_decisions, _ = get_story_data(adhd_buster)
    decisions = adhd_buster.get("story_decisions", {})
    path = ""
    
    for chapter_num in [2, 4, 6]:
        decision_info = story_decisions.get(chapter_num)
        if decision_info and decision_info["id"] in decisions:
            path += decisions[decision_info["id"]]
    
    return path


def get_chapters_read(adhd_buster: dict) -> list:
    """Get the list of chapter numbers that have been read for current story."""
    return adhd_buster.get("chapters_read", [])


def is_chapter_read(adhd_buster: dict, chapter_number: int) -> bool:
    """Check if a specific chapter has been read."""
    chapters_read = get_chapters_read(adhd_buster)
    return chapter_number in chapters_read


def can_read_chapter(adhd_buster: dict, chapter_number: int) -> tuple:
    """
    Check if a chapter can be read based on sequential reading requirements.
    
    Rules:
    1. Chapter must be unlocked (power requirement met)
    2. All previous chapters must be read
    3. If previous chapter had a decision, it must be made
    
    Returns:
        tuple: (can_read: bool, reason: str)
    """
    story_decisions, story_chapters = get_story_data(adhd_buster)
    
    if chapter_number < 1 or chapter_number > len(story_chapters):
        return (False, "Invalid chapter number")
    
    # Check if chapter is unlocked by power
    current_power = calculate_character_power(adhd_buster)
    max_power = adhd_buster.get("max_power_reached", 0)
    unlock_power = max(current_power, max_power)
    threshold = STORY_THRESHOLDS[chapter_number - 1]
    
    if unlock_power < threshold:
        return (False, f"Requires {threshold} power (you have {unlock_power})")
    
    # Chapter 1 can always be read if unlocked
    if chapter_number == 1:
        return (True, "")
    
    # Check if previous chapter has been read
    chapters_read = get_chapters_read(adhd_buster)
    prev_chapter = chapter_number - 1
    
    if prev_chapter not in chapters_read:
        return (False, f"You must read Chapter {prev_chapter} first")
    
    # Check if previous chapter had a decision that needs to be made
    prev_chapter_data = story_chapters[prev_chapter - 1]
    if prev_chapter_data.get("has_decision"):
        decision_info = story_decisions.get(prev_chapter)
        if decision_info:
            decisions = adhd_buster.get("story_decisions", {})
            if decision_info["id"] not in decisions:
                return (False, f"You must make the decision in Chapter {prev_chapter} first")
    
    return (True, "")


def mark_chapter_read(adhd_buster: dict, chapter_number: int) -> bool:
    """
    Mark a chapter as read. Returns True if successful.
    
    Note: This should only be called when the user successfully reads a chapter
    and makes any required decisions.
    """
    if "chapters_read" not in adhd_buster:
        adhd_buster["chapters_read"] = []
    
    if chapter_number not in adhd_buster["chapters_read"]:
        adhd_buster["chapters_read"].append(chapter_number)
        adhd_buster["chapters_read"].sort()  # Keep sorted
        sync_hero_data(adhd_buster)
        return True
    
    return False  # Already read


def get_next_readable_chapter(adhd_buster: dict) -> Optional[int]:
    """
    Get the next chapter that the user should read.
    Returns None if all chapters have been read.
    """
    story_decisions, story_chapters = get_story_data(adhd_buster)
    chapters_read = get_chapters_read(adhd_buster)
    
    for i in range(1, len(story_chapters) + 1):
        if i not in chapters_read:
            can_read, _ = can_read_chapter(adhd_buster, i)
            if can_read:
                return i
            else:
                return None  # Can't read next one yet
    
    return None  # All chapters read


def get_chapter_content(chapter_number: int, adhd_buster: dict) -> Optional[dict]:
    """
    Get the content of a specific chapter, personalized with gear and decisions.
    
    Args:
        chapter_number: 1-7
        adhd_buster: The user's ADHD Buster data with equipped items and decisions
    
    Returns:
        dict with 'title', 'content', 'unlocked', 'has_decision', 'decision', etc.
    """
    story_decisions, story_chapters = get_story_data(adhd_buster)
    
    if chapter_number < 1 or chapter_number > len(story_chapters):
        return None
    
    chapter = story_chapters[chapter_number - 1]
    current_power = calculate_character_power(adhd_buster)
    max_power = adhd_buster.get("max_power_reached", 0)
    # Use max power for unlocking - chapters stay unlocked once reached
    unlock_power = max(current_power, max_power)
    unlocked = unlock_power >= chapter["threshold"]
    
    if not unlocked:
        return {
            "title": f"Chapter {chapter_number}: ???",
            "content": f"đź”’ Locked â€” Reach {chapter['threshold']} power to unlock.\nYour current power: {current_power}",
            "unlocked": False,
            "threshold": chapter["threshold"],
            "power_needed": chapter["threshold"] - current_power,
            "has_decision": False,
        }
    
    # Get equipped items for personalization
    equipped = adhd_buster.get("equipped", {})
    
    # Default slot names for when no item is equipped
    # These work whether or not "Your" precedes them in the text
    default_slot_names = {
        "Helmet": "trusty helmet",
        "Weapon": "trusty weapon",
        "Chestplate": "worn chestplate",
        "Shield": "battered shield",
        "Gauntlets": "old gauntlets",
        "Boots": "reliable boots",
        "Cloak": "faded cloak",
        "Amulet": "simple amulet",
    }
    
    def get_item_name(slot: str) -> str:
        item = equipped.get(slot)
        if item and item.get("name"):
            return f"**{item['name']}**"
        # Return a default name that reads naturally after "Your" or standalone
        return f"*{default_slot_names.get(slot, slot.lower())}*"
    
    # Build replacement dict
    replacements = {
        "helmet": get_item_name("Helmet"),
        "weapon": get_item_name("Weapon"),
        "chestplate": get_item_name("Chestplate"),
        "shield": get_item_name("Shield"),
        "gauntlets": get_item_name("Gauntlets"),
        "boots": get_item_name("Boots"),
        "cloak": get_item_name("Cloak"),
        "amulet": get_item_name("Amulet"),
        "current_power": str(current_power),
    }
    
    # Get decisions made so far
    decisions = adhd_buster.get("story_decisions", {})
    decision_path = get_decision_path(adhd_buster)
    
    # Determine content based on chapter type
    has_decision = chapter.get("has_decision", False)
    decision_info = story_decisions.get(chapter_number)
    decision_made = has_made_decision(adhd_buster, chapter_number)
    
    # Chapter 7 has multiple endings based on all 3 decisions
    if chapter_number == 7:
        if len(decision_path) < 3:
            content = """
 THE FINAL CHAPTER AWAITS...

But your story is not yet complete.
You have not made all three critical decisions.

Return to the chapters you've unlocked and face your choices.
Only then will the Final Door reveal YOUR ending.

Decisions made: {}/3
""".format(len(decision_path))
        else:
            endings = chapter.get("endings") or {}
            ending = endings.get(decision_path)
            if ending:
                content = ending["content"]
            else:
                content = "Error: Ending not found for path: " + decision_path
    
    # Chapters with decisions
    elif has_decision:
        content = chapter["content"]
        if decision_made and "content_after_decision" in chapter:
            choice = decisions.get(decision_info["id"], "A")
            after_content = chapter["content_after_decision"].get(choice, "")
            content = content + "\n" + after_content
    
    # Chapters with variations based on previous decisions
    elif "content_variations" in chapter:
        variations = chapter["content_variations"]
        # Find the best matching variation by progressively shortening the path
        content = None
        # Try exact match first, then progressively shorter prefixes
        for length in range(len(decision_path), 0, -1):
            prefix = decision_path[:length]
            if prefix in variations:
                content = variations[prefix]
                break
        # Fallback to first variation if no match, or chapter content
        if content is None:
            if variations:
                content = list(variations.values())[0]
            else:
                content = chapter.get("content", "")
    
    # Simple chapters
    else:
        content = chapter["content"]
    
    # Apply replacements
    for key, value in replacements.items():
        content = content.replace("{" + key + "}", value)
    
    result = {
        "title": chapter["title"],
        "content": content,
        "unlocked": True,
        "chapter_number": chapter_number,
        "has_decision": has_decision and not decision_made,
        "decision_made": decision_made,
    }
    
    if has_decision and not decision_made:
        result["decision"] = decision_info
    
    return result


def get_newly_unlocked_chapter(old_power: int, new_power: int) -> Optional[int]:
    """
    Check if a new chapter was unlocked by a power increase.
    
    Returns:
        The newly unlocked chapter number, or None if no new chapter
    """
    old_chapter = 0
    new_chapter = 0
    
    for i, threshold in enumerate(STORY_THRESHOLDS):
        if old_power >= threshold:
            old_chapter = i + 1
        if new_power >= threshold:
            new_chapter = i + 1
    
    if new_chapter > old_chapter:
        return new_chapter
    return None


# ============================================================================
# HERO & STORY MODE MANAGEMENT SYSTEM
# Each story has its own independent hero with separate progress
# ============================================================================

# Story modes
STORY_MODE_ACTIVE = "story"      # Playing a story with associated hero
STORY_MODE_HERO_ONLY = "hero_only"  # Hero progress only, no story
STORY_MODE_DISABLED = "disabled"    # No gamification at all

STORY_MODES = {
    STORY_MODE_ACTIVE: {
        "id": STORY_MODE_ACTIVE,
        "title": "\U0001f4d6 Story Mode",
        "description": "Follow a story with your hero. Each story has its own hero and progress.",
    },
    STORY_MODE_HERO_ONLY: {
        "id": STORY_MODE_HERO_ONLY,
        "title": "\u2694\ufe0f Hero Only",
        "description": "Level up your hero without following a story. Just collect gear and grow stronger.",
    },
    STORY_MODE_DISABLED: {
        "id": STORY_MODE_DISABLED,
        "title": "\u274c Disabled",
        "description": "No gamification. Just focus sessions without heroes or stories.",
    },
}


def _create_empty_hero() -> dict:
    """Create a fresh hero with no items or progress."""
    return {
        "inventory": [],
        "equipped": {},
        "story_decisions": {},
        "diary": [],
        "luck_bonus": 0,
        "total_collected": 0,
        "last_daily_reward_date": "",
        "max_power_reached": 0,  # Highest power ever achieved - chapters stay unlocked
        "entitidex": {},  # Entitidex collection progress (see entitidex package)
        "chapters_read": [],  # List of chapter numbers that have been read
    }


def _migrate_adhd_buster_data(adhd_buster: dict) -> dict:
    """
    Migrate old flat adhd_buster structure to new hero-per-story structure.
    This preserves existing user data while upgrading to the new format.
    """
    # Already migrated?
    if "story_heroes" in adhd_buster:
        return adhd_buster
    
    # Extract old data
    old_inventory = adhd_buster.get("inventory", [])
    old_equipped = adhd_buster.get("equipped", {})
    old_decisions = adhd_buster.get("story_decisions", {})
    old_diary = adhd_buster.get("diary", [])
    old_luck = adhd_buster.get("luck_bonus", 0)
    old_collected = adhd_buster.get("total_collected", 0)
    old_story = adhd_buster.get("selected_story", "warrior")
    old_daily_reward_date = adhd_buster.get("last_daily_reward_date", "")
    old_max_power = adhd_buster.get("max_power_reached", 0)
    
    # Create migrated hero (assign all old data to the story they were playing)
    migrated_hero = {
        "inventory": old_inventory,
        "equipped": old_equipped,
        "story_decisions": old_decisions,
        "diary": old_diary,
        "luck_bonus": old_luck,
        "total_collected": old_collected,
        "last_daily_reward_date": old_daily_reward_date,
        "max_power_reached": old_max_power,
    }
    
    # Build new structure
    adhd_buster["story_mode"] = STORY_MODE_ACTIVE
    adhd_buster["active_story"] = old_story
    adhd_buster["story_heroes"] = {old_story: migrated_hero}
    adhd_buster["free_hero"] = _create_empty_hero()
    
    # Clean up old flat keys (keep them for backward compatibility during transition)
    # They will be updated by get_active_hero_data
    
    return adhd_buster


def ensure_hero_structure(adhd_buster: dict) -> dict:
    """
    Ensure adhd_buster has the proper hero management structure.
    Migrates old data if needed, creates defaults if missing.
    Also ensures flat structure is synced for backward compatibility.
    """
    if "story_heroes" not in adhd_buster:
        _migrate_adhd_buster_data(adhd_buster)
    
    # Ensure all required keys exist
    if "story_mode" not in adhd_buster:
        adhd_buster["story_mode"] = STORY_MODE_ACTIVE
    if "active_story" not in adhd_buster:
        adhd_buster["active_story"] = "warrior"
    if "story_heroes" not in adhd_buster:
        adhd_buster["story_heroes"] = {}
    if "free_hero" not in adhd_buster:
        adhd_buster["free_hero"] = _create_empty_hero()
    
    # Ensure active story has a hero
    active_story = adhd_buster.get("active_story", "warrior")
    if active_story not in adhd_buster.get("story_heroes", {}):
        adhd_buster["story_heroes"][active_story] = _create_empty_hero()
    
    # Ensure flat keys exist (init with defaults if missing, but DO NOT overwrite)
    # OLD: _sync_active_hero_to_flat_internal(adhd_buster) -- caused data loss by overwriting changes
    target_keys = {
        "inventory": [],
        "equipped": {},
        "story_decisions": {},
        "diary": [],
        "luck_bonus": 0,
        "total_collected": 0,
        "last_daily_reward_date": "",
        "max_power_reached": 0,
        "entitidex": {},
        "chapters_read": [],
    }
    for k, v in target_keys.items():
        if k not in adhd_buster:
            adhd_buster[k] = v
    
    return adhd_buster


def _sync_active_hero_to_flat_internal(adhd_buster: dict) -> None:
    """
    Internal sync function that doesn't call ensure_hero_structure.
    Used during initialization to avoid infinite recursion.
    """
    mode = adhd_buster.get("story_mode", STORY_MODE_ACTIVE)
    
    if mode == STORY_MODE_DISABLED:
        # Disabled mode - use empty data
        adhd_buster["inventory"] = []
        adhd_buster["equipped"] = {}
        adhd_buster["story_decisions"] = {}
        adhd_buster["diary"] = []
        adhd_buster["luck_bonus"] = 0
        adhd_buster["total_collected"] = 0
        adhd_buster["last_daily_reward_date"] = ""
        adhd_buster["max_power_reached"] = 0
        adhd_buster["chapters_read"] = []
    elif mode == STORY_MODE_HERO_ONLY:
        hero = adhd_buster.get("free_hero", _create_empty_hero())
        adhd_buster["inventory"] = hero.get("inventory", [])
        adhd_buster["equipped"] = hero.get("equipped", {})
        adhd_buster["story_decisions"] = hero.get("story_decisions", {})
        adhd_buster["diary"] = hero.get("diary", [])
        adhd_buster["luck_bonus"] = hero.get("luck_bonus", 0)
        adhd_buster["total_collected"] = hero.get("total_collected", 0)
        adhd_buster["last_daily_reward_date"] = hero.get("last_daily_reward_date", "")
        adhd_buster["max_power_reached"] = hero.get("max_power_reached", 0)
        adhd_buster["chapters_read"] = hero.get("chapters_read", [])
    else:
        # Story mode - get the hero for the active story
        story_id = adhd_buster.get("active_story", "warrior")
        heroes = adhd_buster.get("story_heroes", {})
        hero = heroes.get(story_id, _create_empty_hero())
        
        adhd_buster["inventory"] = hero.get("inventory", [])
        adhd_buster["equipped"] = hero.get("equipped", {})
        adhd_buster["story_decisions"] = hero.get("story_decisions", {})
        adhd_buster["diary"] = hero.get("diary", [])
        adhd_buster["luck_bonus"] = hero.get("luck_bonus", 0)
        adhd_buster["total_collected"] = hero.get("total_collected", 0)
        adhd_buster["last_daily_reward_date"] = hero.get("last_daily_reward_date", "")
        adhd_buster["max_power_reached"] = hero.get("max_power_reached", 0)
        adhd_buster["chapters_read"] = hero.get("chapters_read", [])
    
    # Also sync selected_story for backward compatibility
    if mode == STORY_MODE_ACTIVE:
        adhd_buster["selected_story"] = adhd_buster.get("active_story", "warrior")
    
    return adhd_buster


def get_story_mode(adhd_buster: dict) -> str:
    """Get the current story mode."""
    ensure_hero_structure(adhd_buster)
    return adhd_buster.get("story_mode", STORY_MODE_ACTIVE)


def set_story_mode(adhd_buster: dict, mode: str) -> bool:
    """
    Set the story mode.
    
    Args:
        adhd_buster: User's data
        mode: STORY_MODE_ACTIVE, STORY_MODE_HERO_ONLY, or STORY_MODE_DISABLED
    
    Returns:
        True if successful
    """
    if mode not in STORY_MODES:
        return False
    
    ensure_hero_structure(adhd_buster)
    
    # Save current state before switching
    _sync_flat_to_active_hero(adhd_buster)
    
    adhd_buster["story_mode"] = mode
    _sync_active_hero_to_flat(adhd_buster)
    return True


def get_active_story_id(adhd_buster: dict) -> Optional[str]:
    """
    Get the currently active story ID.
    Returns None if in hero_only or disabled mode.
    """
    ensure_hero_structure(adhd_buster)
    mode = adhd_buster.get("story_mode", STORY_MODE_ACTIVE)
    
    if mode != STORY_MODE_ACTIVE:
        return None
    
    return adhd_buster.get("active_story", "warrior")


def get_active_hero(adhd_buster: dict) -> Optional[dict]:
    """
    Get the currently active hero's data.
    Returns None if gamification is disabled.
    """
    ensure_hero_structure(adhd_buster)
    mode = adhd_buster.get("story_mode", STORY_MODE_ACTIVE)
    
    if mode == STORY_MODE_DISABLED:
        return None
    
    if mode == STORY_MODE_HERO_ONLY:
        return adhd_buster.get("free_hero", _create_empty_hero())
    
    # Story mode - get the hero for the active story
    story_id = adhd_buster.get("active_story", "warrior")
    heroes = adhd_buster.get("story_heroes", {})
    
    if story_id not in heroes:
        heroes[story_id] = _create_empty_hero()
        adhd_buster["story_heroes"] = heroes
    
    return heroes[story_id]


def _sync_active_hero_to_flat(adhd_buster: dict) -> None:
    """
    Sync the active hero's data to the flat structure for backward compatibility.
    This ensures existing code that reads adhd_buster["equipped"] etc. still works.
    """
    ensure_hero_structure(adhd_buster)
    _sync_active_hero_to_flat_internal(adhd_buster)


def _sync_flat_to_active_hero(adhd_buster: dict) -> None:
    """
    Sync the flat structure back to the active hero's data.
    Call this after any code modifies the flat structure.
    
    NOTE: Does NOT call ensure_hero_structure to avoid the circular sync issue
    where ensure_hero_structure would overwrite flat data from hero data.
    """
    mode = adhd_buster.get("story_mode", STORY_MODE_ACTIVE)
    
    if mode == STORY_MODE_DISABLED:
        return  # Disabled mode, nothing to sync
    
    # Get hero directly without ensure_hero_structure to avoid circular sync
    if mode == STORY_MODE_HERO_ONLY:
        hero = adhd_buster.get("free_hero")
        if hero is None:
            adhd_buster["free_hero"] = _create_empty_hero()
            hero = adhd_buster["free_hero"]
    else:
        story_id = adhd_buster.get("active_story", "warrior")
        heroes = adhd_buster.get("story_heroes", {})
        if story_id not in heroes:
            heroes[story_id] = _create_empty_hero()
            adhd_buster["story_heroes"] = heroes
        hero = heroes[story_id]
    
    # Sync flat data back to hero
    hero["inventory"] = adhd_buster.get("inventory", [])
    hero["equipped"] = adhd_buster.get("equipped", {})
    hero["story_decisions"] = adhd_buster.get("story_decisions", {})
    hero["diary"] = adhd_buster.get("diary", [])
    hero["luck_bonus"] = adhd_buster.get("luck_bonus", 0)
    hero["total_collected"] = adhd_buster.get("total_collected", 0)
    hero["last_daily_reward_date"] = adhd_buster.get("last_daily_reward_date", "")
    hero["max_power_reached"] = adhd_buster.get("max_power_reached", 0)
    hero["chapters_read"] = adhd_buster.get("chapters_read", [])


def switch_story(adhd_buster: dict, story_id: str) -> bool:
    """
    Switch to a different story, loading that story's hero.
    Saves current hero data first, then loads the new story's hero.
    
    Args:
        adhd_buster: User's data
        story_id: The story to switch to
    
    Returns:
        True if successful
    """
    if story_id not in AVAILABLE_STORIES:
        return False
    
    ensure_hero_structure(adhd_buster)
    
    # Save current hero's state
    _sync_flat_to_active_hero(adhd_buster)
    
    # Switch to new story
    adhd_buster["active_story"] = story_id
    adhd_buster["story_mode"] = STORY_MODE_ACTIVE
    
    # Ensure new story has a hero
    if story_id not in adhd_buster.get("story_heroes", {}):
        if "story_heroes" not in adhd_buster:
            adhd_buster["story_heroes"] = {}
        adhd_buster["story_heroes"][story_id] = _create_empty_hero()
    
    # Load new hero to flat structure
    _sync_active_hero_to_flat(adhd_buster)
    
    return True


def restart_story(adhd_buster: dict, story_id: str = None) -> bool:
    """
    Restart a story with a fresh hero. Deletes all progress for that story.
    
    Args:
        adhd_buster: User's data
        story_id: The story to restart (None = current story)
    
    Returns:
        True if successful
    """
    ensure_hero_structure(adhd_buster)
    
    if story_id is None:
        story_id = adhd_buster.get("active_story", "warrior")
    
    if story_id not in AVAILABLE_STORIES:
        return False
    
    # Save current hero if we're not restarting the active one
    current_story = adhd_buster.get("active_story")
    if current_story != story_id:
        _sync_flat_to_active_hero(adhd_buster)
    
    # Create fresh hero for this story
    if "story_heroes" not in adhd_buster:
        adhd_buster["story_heroes"] = {}
    adhd_buster["story_heroes"][story_id] = _create_empty_hero()
    
    # If this is the active story, reload flat structure
    if current_story == story_id:
        _sync_active_hero_to_flat(adhd_buster)
    
    return True


def get_hero_summary(adhd_buster: dict, story_id: str = None) -> Optional[dict]:
    """
    Get a summary of a hero's progress.
    
    Args:
        adhd_buster: User's data
        story_id: Story ID to get hero for, or None for current/free hero
    
    Returns:
        Dict with hero summary, or None if no hero exists
    """
    ensure_hero_structure(adhd_buster)
    
    if story_id is None:
        hero = get_active_hero(adhd_buster)
        if hero is None:
            return None
        story_id = adhd_buster.get("active_story")
        is_free_hero = adhd_buster.get("story_mode") == STORY_MODE_HERO_ONLY
    else:
        heroes = adhd_buster.get("story_heroes", {})
        hero = heroes.get(story_id)
        is_free_hero = False
    
    if hero is None:
        return None
    
    # Calculate power from equipped items
    equipped = hero.get("equipped", {})
    power = 0
    for item in equipped.values():
        if item:
            power += item.get("power", RARITY_POWER.get(item.get("rarity", "Common"), 10))
    
    # Add set bonus
    set_info = calculate_set_bonuses(equipped)
    power += set_info["total_bonus"]
    
    # Count items
    inventory_count = len(hero.get("inventory", []))
    equipped_count = sum(1 for item in equipped.values() if item)
    decisions_count = len(hero.get("story_decisions", {}))
    
    return {
        "story_id": story_id if not is_free_hero else None,
        "story_title": AVAILABLE_STORIES[story_id]["title"] if story_id and not is_free_hero else "Free Hero",
        "is_free_hero": is_free_hero,
        "power": power,
        "inventory_count": inventory_count,
        "equipped_count": equipped_count,
        "decisions_made": decisions_count,
        "total_collected": hero.get("total_collected", 0),
    }


def get_all_heroes_summary(adhd_buster: dict) -> dict:
    """
    Get a summary of all heroes (story heroes + free hero).
    
    Returns:
        Dict with 'story_heroes' list and 'free_hero' summary
    """
    ensure_hero_structure(adhd_buster)
    
    story_summaries = []
    for story_id in AVAILABLE_STORIES:
        heroes = adhd_buster.get("story_heroes", {})
        if story_id in heroes:
            summary = get_hero_summary(adhd_buster, story_id)
            if summary:
                summary["has_progress"] = True
                story_summaries.append(summary)
        else:
            # Story exists but no hero created yet
            story_summaries.append({
                "story_id": story_id,
                "story_title": AVAILABLE_STORIES[story_id]["title"],
                "is_free_hero": False,
                "power": 0,
                "has_progress": False,
            })
    
    # Free hero summary
    free_hero = adhd_buster.get("free_hero", {})
    free_power = 0
    for item in free_hero.get("equipped", {}).values():
        if item:
            free_power += item.get("power", RARITY_POWER.get(item.get("rarity", "Common"), 10))
    
    return {
        "story_heroes": story_summaries,
        "free_hero": {
            "power": free_power,
            "inventory_count": len(free_hero.get("inventory", [])),
            "total_collected": free_hero.get("total_collected", 0),
            "has_progress": free_power > 0 or len(free_hero.get("inventory", [])) > 0,
        },
        "active_story": adhd_buster.get("active_story"),
        "story_mode": adhd_buster.get("story_mode", STORY_MODE_ACTIVE),
    }


def is_gamification_enabled(adhd_buster: dict) -> bool:
    """Check if gamification is enabled (not in disabled mode)."""
    ensure_hero_structure(adhd_buster)
    return adhd_buster.get("story_mode", STORY_MODE_ACTIVE) != STORY_MODE_DISABLED


def is_story_enabled(adhd_buster: dict) -> bool:
    """Check if story mode is active (not hero-only or disabled)."""
    ensure_hero_structure(adhd_buster)
    return adhd_buster.get("story_mode", STORY_MODE_ACTIVE) == STORY_MODE_ACTIVE


def sync_hero_data(adhd_buster: dict) -> None:
    """
    Sync hero data after modifications.
    Call this after any external code modifies the flat adhd_buster structure.
    Also updates max_power_reached if current power exceeds previous max.
    """
    # Update max power reached if current power is higher
    current_power = calculate_character_power(adhd_buster)
    max_power = adhd_buster.get("max_power_reached", 0)
    if current_power > max_power:
        adhd_buster["max_power_reached"] = current_power
    
    _sync_flat_to_active_hero(adhd_buster)


# =============================================================================
# WEIGHT TRACKING GAMIFICATION
# =============================================================================

# =============================================================================
# AGE AND SEX-SPECIFIC NORMS (CDC/NIH/WHO Guidelines)
# =============================================================================

# CDC BMI-for-age percentiles for ages 2-19 (by sex)
# Format: age -> {sex: (P5, P50, P85, P95)}
# P5 = underweight cutoff, P85 = overweight cutoff, P95 = obese cutoff
# Data sources: CDC Growth Charts (2000), WHO Child Growth Standards
BMI_PERCENTILES_BY_AGE = {
    # Ages 2-6: WHO Child Growth Standards / CDC Extended
    2:  {"M": (14.8, 16.5, 18.0, 18.9), "F": (14.4, 16.1, 17.8, 18.7)},
    3:  {"M": (14.0, 15.8, 17.4, 18.3), "F": (13.7, 15.5, 17.2, 18.2)},
    4:  {"M": (13.5, 15.4, 17.0, 17.9), "F": (13.3, 15.2, 17.0, 18.0)},
    5:  {"M": (13.3, 15.2, 16.9, 18.0), "F": (13.1, 15.0, 17.0, 18.3)},
    6:  {"M": (13.3, 15.3, 17.2, 18.5), "F": (13.0, 15.1, 17.3, 18.8)},
    # Ages 7-19: CDC BMI-for-age percentiles
    7:  {"M": (13.7, 15.5, 17.4, 19.2), "F": (13.4, 15.5, 17.6, 19.7)},
    8:  {"M": (13.8, 15.8, 18.0, 20.1), "F": (13.5, 15.8, 18.3, 20.7)},
    9:  {"M": (14.0, 16.2, 18.6, 21.1), "F": (13.7, 16.3, 19.1, 21.8)},
    10: {"M": (14.2, 16.6, 19.4, 22.2), "F": (14.0, 16.9, 20.0, 23.0)},
    11: {"M": (14.6, 17.2, 20.2, 23.2), "F": (14.4, 17.5, 20.9, 24.1)},
    12: {"M": (15.0, 17.8, 21.0, 24.2), "F": (14.8, 18.1, 21.7, 25.3)},
    13: {"M": (15.5, 18.5, 21.9, 25.2), "F": (15.3, 18.7, 22.6, 26.3)},
    14: {"M": (16.0, 19.2, 22.7, 26.0), "F": (15.8, 19.4, 23.3, 27.0)},
    15: {"M": (16.6, 20.0, 23.6, 26.9), "F": (16.3, 20.0, 24.0, 28.0)},
    16: {"M": (17.2, 20.6, 24.3, 27.6), "F": (16.8, 20.5, 24.7, 28.8)},
    17: {"M": (17.7, 21.2, 24.9, 28.3), "F": (17.2, 20.9, 25.2, 29.6)},
    18: {"M": (18.2, 21.9, 25.7, 29.0), "F": (17.6, 21.3, 25.7, 30.3)},
    19: {"M": (18.7, 22.5, 26.4, 29.7), "F": (17.8, 21.6, 26.1, 31.0)},
}

# Sleep duration recommendations by age group (same for M/F per AASM/NSF)
# Format: (min_age, max_age, min_hours, optimal_low, optimal_high, max_hours)
SLEEP_DURATION_BY_AGE = [
    (0, 2, 11.0, 12.0, 14.0, 16.0),   # Infants/Toddlers 0-2: 11-14+ hours (AASM 2016)
    (3, 5, 10.0, 10.0, 13.0, 14.0),   # Preschoolers 3-5: 10-13 hours (AASM 2016)
    (6, 12, 9.0, 9.0, 12.0, 13.0),    # Children 6-12: 9-12 hours (AASM 2016)
    (13, 18, 8.0, 8.0, 10.0, 12.0),   # Teens 13-18: 8-10 hours (AASM 2016)
    (19, 64, 7.0, 7.5, 9.0, 10.0),    # Adults 19-64: 7-9 hours (NSF 2015)
    (65, 150, 7.0, 7.0, 8.0, 9.0),    # Seniors 65+: 7-8 hours (NSF 2015)
]


def calculate_age_from_birth(birth_year: int, birth_month: int = 1) -> int:
    """
    Calculate age in years from birth year and month.
    
    Args:
        birth_year: Year of birth (e.g., 2010)
        birth_month: Month of birth (1-12, defaults to January)
    
    Returns:
        Age in complete years
    """
    if not birth_year or birth_year < 1900 or birth_year > 2100:
        return None
    
    today = datetime.now()
    birth_month = max(1, min(12, birth_month or 1))
    
    age = today.year - birth_year
    # Adjust if birthday hasn't occurred yet this year
    if today.month < birth_month:
        age -= 1
    elif today.month == birth_month and today.day < 15:  # Approximate mid-month
        age -= 1
    
    return max(0, age)


def get_bmi_thresholds_for_age(age: int, sex: str = "M") -> tuple:
    """
    Get BMI thresholds (underweight, overweight, obese) for a specific age and sex.
    
    For ages 2-19, uses CDC BMI-for-age percentiles.
    For ages 20+, uses standard adult WHO thresholds.
    
    Args:
        age: Age in years
        sex: "M" for male, "F" for female (case-insensitive)
    
    Returns:
        Tuple of (underweight_threshold, overweight_threshold, obese_threshold)
    """
    if age is None or age < 2:
        # For very young children or unknown age, use adult thresholds as fallback
        return (18.5, 25.0, 30.0)
    
    sex = (sex or "M").upper()[0] if sex else "M"
    if sex not in ("M", "F"):
        sex = "M"
    
    if age >= 20:
        # Adults 20+: standard WHO thresholds (same for M/F)
        return (18.5, 25.0, 30.0)
    
    # Children/teens 2-19: use CDC percentiles
    if age in BMI_PERCENTILES_BY_AGE:
        p5, p50, p85, p95 = BMI_PERCENTILES_BY_AGE[age][sex]
        return (p5, p85, p95)
    
    # Fallback for edge cases
    return (18.5, 25.0, 30.0)


def get_bmi_classification_for_age(bmi: float, age: int = None, sex: str = "M") -> tuple:
    """
    Get BMI classification considering age and sex.
    
    For ages 2-19, uses CDC BMI-for-age percentile categories:
    - Underweight: < P5
    - Healthy weight: P5 to < P85
    - Overweight: P85 to < P95
    - Obese: >= P95
    
    For ages 20+, uses standard WHO categories.
    
    Args:
        bmi: Calculated BMI value
        age: Age in years (None = use adult thresholds)
        sex: "M" or "F"
    
    Returns:
        Tuple of (classification_name, color_hex)
    """
    if bmi is None:
        return ("Unknown", "#888888")
    
    underweight, overweight, obese = get_bmi_thresholds_for_age(age, sex)
    
    if age is not None and 2 <= age <= 19:
        # Pediatric categories (CDC percentile-based)
        if bmi < underweight:
            return ("Underweight (<P5)", "#ffaa64")
        elif bmi < overweight:
            return ("Healthy Weight", "#00ff88")
        elif bmi < obese:
            return ("Overweight (P85-P95)", "#ffff64")
        else:
            return ("Obese (â‰ĄP95)", "#ff6464")
    else:
        # Adult categories (WHO standard)
        if bmi < 16.0:
            return ("Severely Underweight", "#ff6464")
        elif bmi < 17.0:
            return ("Moderately Underweight", "#ffaa64")
        elif bmi < 18.5:
            return ("Mildly Underweight", "#ffff64")
        elif bmi < 25.0:
            return ("Normal", "#00ff88")
        elif bmi < 30.0:
            return ("Overweight", "#ffff64")
        elif bmi < 35.0:
            return ("Obese Class I", "#ffaa64")
        elif bmi < 40.0:
            return ("Obese Class II", "#ff6464")
        else:
            return ("Obese Class III", "#ff3232")


def get_sleep_targets_for_age(age: int) -> dict:
    """
    Get sleep duration targets based on age.
    
    Uses AASM (children/teens) and NSF (adults) consensus guidelines.
    Same recommendations for male and female.
    
    Args:
        age: Age in years (None = use adult defaults)
    
    Returns:
        Dict with minimum, optimal_low, optimal_high, maximum hours
    """
    if age is None:
        age = 30  # Default to adult
    
    for min_age, max_age, min_h, opt_low, opt_high, max_h in SLEEP_DURATION_BY_AGE:
        if min_age <= age <= max_age:
            return {
                "minimum": min_h,
                "optimal_low": opt_low,
                "optimal_high": opt_high,
                "maximum": max_h,
                # Aliases for UI compatibility
                "min_hours": min_h,
                "optimal_hours": opt_high,
                "max_hours": max_h,
            }
    
    # Fallback for very young or very old (use adult defaults)
    return {
        "minimum": 7.0,
        "optimal_low": 7.5,
        "optimal_high": 9.0,
        "maximum": 10.0,
        # Aliases for UI compatibility
        "min_hours": 7.0,
        "optimal_hours": 9.0,
        "max_hours": 10.0,
    }


def get_sleep_recommendation_text(age: int) -> str:
    """
    Get human-readable sleep recommendation for an age.
    
    Args:
        age: Age in years
    
    Returns:
        String with recommendation (e.g., "9-12 hours for ages 7-12")
    """
    if age is None:
        return "7-9 hours for adults"
    
    if 7 <= age <= 12:
        return "9-12 hours for ages 7-12 (AASM)"
    elif 13 <= age <= 18:
        return "8-10 hours for teens 13-18 (AASM)"
    elif 19 <= age <= 64:
        return "7-9 hours for adults 19-64 (NSF)"
    elif age >= 65:
        return "7-8 hours for seniors 65+ (NSF)"
    else:
        return "consult pediatrician for age < 7"


def get_ideal_weight_range_for_age(height_cm: float, age: int = None, sex: str = "M") -> tuple:
    """
    Calculate ideal weight range based on height, age, and sex.
    
    For children/teens (7-19), uses age/sex-specific BMI percentile thresholds.
    For adults (20+), uses standard 18.5-25 BMI range.
    
    Args:
        height_cm: Height in centimeters
        age: Age in years (None = adult)
        sex: "M" or "F"
    
    Returns:
        Tuple of (min_weight_kg, max_weight_kg)
    """
    if not height_cm or height_cm <= 0:
        return (None, None)
    
    height_m = height_cm / 100
    
    underweight, overweight, _ = get_bmi_thresholds_for_age(age, sex)
    
    min_weight = underweight * (height_m ** 2)
    max_weight = overweight * (height_m ** 2)
    
    return (min_weight, max_weight)


# Weight loss thresholds for daily rewards (in grams)
WEIGHT_DAILY_THRESHOLDS = {
    0: "Common",       # Same weight = Common item
    100: "Uncommon",   # 100g loss
    200: "Rare",       # 200g loss
    300: "Epic",       # 300g loss
    500: "Legendary",  # 500g+ loss = daily legendary!
}

# Weekly weight loss threshold for legendary (in grams)
WEIGHT_WEEKLY_LEGENDARY_THRESHOLD = 500  # 500g in a week

# Monthly weight loss threshold for legendary (in grams)
WEIGHT_MONTHLY_LEGENDARY_THRESHOLD = 2000  # 2kg in a month

# Weight mode types based on BMI/goal
WEIGHT_MODE_LOSS = "loss"           # Overweight: reward weight loss
WEIGHT_MODE_GAIN = "gain"           # Underweight: reward weight gain
WEIGHT_MODE_MAINTAIN = "maintain"   # Normal weight: reward maintaining

# BMI thresholds for automatic mode detection (adults, legacy)
BMI_UNDERWEIGHT_THRESHOLD = 18.5
BMI_OVERWEIGHT_THRESHOLD = 25.0


def determine_weight_mode(current_weight: float, height_cm: float = None, 
                          goal_weight: float = None, age: int = None,
                          sex: str = None) -> str:
    """
    Determine weight tracking mode based on BMI and goal.
    
    Uses age/sex-specific BMI thresholds for children/teens (7-19).
    
    Priority:
    1. If goal is set: compare current to goal
    2. If height available: use BMI classification (age-adjusted if provided)
    3. Default: loss mode (legacy behavior)
    
    Args:
        current_weight: Current weight in kg
        height_cm: Height in cm (optional)
        goal_weight: Target weight in kg (optional)
        age: Age in years (optional, for age-specific BMI thresholds)
        sex: "M" or "F" (optional, for sex-specific BMI thresholds)
    
    Returns:
        Weight mode: 'loss', 'gain', or 'maintain'
    """
    if not current_weight or current_weight <= 0:
        return WEIGHT_MODE_LOSS
    
    # If goal is set, use goal-based logic
    if goal_weight and goal_weight > 0:
        diff_kg = goal_weight - current_weight
        if diff_kg > 2.0:  # Need to gain more than 2kg
            return WEIGHT_MODE_GAIN
        elif diff_kg < -2.0:  # Need to lose more than 2kg
            return WEIGHT_MODE_LOSS
        else:  # Within 2kg of goal - maintenance mode
            return WEIGHT_MODE_MAINTAIN
    
    # If height available, use BMI with age-specific thresholds
    if height_cm and height_cm > 0:
        height_m = height_cm / 100
        bmi = current_weight / (height_m ** 2)
        
        # Get age/sex-specific thresholds
        underweight_thresh, overweight_thresh, _ = get_bmi_thresholds_for_age(age, sex)
        
        if bmi < underweight_thresh:
            return WEIGHT_MODE_GAIN
        elif bmi > overweight_thresh:
            return WEIGHT_MODE_LOSS
        else:
            return WEIGHT_MODE_MAINTAIN
    
    # Default to loss mode (legacy behavior)
    return WEIGHT_MODE_LOSS


def get_weight_from_date(weight_entries: list, target_date: str) -> Optional[float]:
    """
    Get weight entry for a specific date.
    
    Args:
        weight_entries: List of {"date": "YYYY-MM-DD", "weight": float}
        target_date: Date string in YYYY-MM-DD format
    
    Returns:
        Weight value or None if not found
    """
    if not isinstance(target_date, str) or not target_date:
        return None

    for entry in weight_entries:
        if not isinstance(entry, dict):
            continue
        entry_date = entry.get("date")
        if entry_date == target_date:
            weight = entry.get("weight")
            return weight if isinstance(weight, (int, float)) else None
    return None


def get_closest_weight_before_date(weight_entries: list, target_date: str) -> Optional[dict]:
    """
    Get the most recent weight entry before or on the target date.
    
    Args:
        weight_entries: List of {"date": "YYYY-MM-DD", "weight": float}
        target_date: Date string in YYYY-MM-DD format
    
    Returns:
        Entry dict with date and weight, or None if no entries before target
    """
    if not weight_entries or not isinstance(target_date, str) or not target_date:
        return None
    
    # Sort entries by date descending
    valid_entries = []
    for entry in weight_entries:
        if not isinstance(entry, dict):
            continue
        date_value = entry.get("date")
        weight_value = entry.get("weight")
        if not isinstance(date_value, str) or not date_value:
            continue
        if not isinstance(weight_value, (int, float)):
            continue
        valid_entries.append(entry)

    sorted_entries = sorted(valid_entries, key=lambda x: x["date"], reverse=True)
    
    for entry in sorted_entries:
        if entry["date"] <= target_date:
            return entry
    return None


def get_previous_weight_entry(weight_entries: list, current_date: str) -> Optional[dict]:
    """
    Get the weight entry immediately before today.
    
    Args:
        weight_entries: List of {"date": "YYYY-MM-DD", "weight": float}
        current_date: Today's date in YYYY-MM-DD format
    
    Returns:
        Previous entry dict or None
    """
    if not weight_entries or not isinstance(current_date, str) or not current_date:
        return None
    
    valid_entries = []
    for entry in weight_entries:
        if not isinstance(entry, dict):
            continue
        date_value = entry.get("date")
        weight_value = entry.get("weight")
        if not isinstance(date_value, str) or not date_value:
            continue
        if not isinstance(weight_value, (int, float)):
            continue
        if date_value < current_date:
            valid_entries.append(entry)

    sorted_entries = sorted(valid_entries, key=lambda x: x["date"], reverse=True)
    
    return sorted_entries[0] if sorted_entries else None


def calculate_weight_loss(current_weight: float, previous_weight: float) -> float:
    """
    Calculate weight loss in grams.
    
    Args:
        current_weight: Current weight in kg
        previous_weight: Previous weight in kg
    
    Returns:
        Weight loss in grams (positive = lost weight, negative = gained)
    """
    if not isinstance(current_weight, (int, float)) or not isinstance(previous_weight, (int, float)):
        return 0
    # Round to avoid floating point precision issues (e.g., 99.999 instead of 100)
    return round((previous_weight - current_weight) * 1000, 1)


def roll_daily_weight_reward_outcome(
    weight_loss_grams: float,
    legendary_bonus: int = 0,
    adhd_buster: Optional[dict] = None,
    roll: Optional[float] = None,
) -> Optional[dict]:
    """
    Canonical backend roll for weight daily-reward rarity.

    Preserves the visible distribution while applying hero-power rarity gates.
    """
    weights = get_daily_weight_reward_weights(weight_loss_grams, legendary_bonus)
    if not weights:
        return None
    rarities = get_standard_reward_rarity_order()
    gated_outcome = evaluate_power_gated_rarity_roll(
        rarities,
        weights,
        adhd_buster=adhd_buster,
        roll=roll,
    )
    return {
        "rarity": gated_outcome.get("rarity", rarities[0] if rarities else "Common"),
        "roll": gated_outcome.get("roll", 0.0),
        "weights": weights,
        "rarities": rarities,
        "power_gating": gated_outcome,
    }


def get_daily_weight_reward_rarity(
    weight_loss_grams: float,
    legendary_bonus: int = 0,
    adhd_buster: Optional[dict] = None,
    roll: Optional[float] = None,
) -> Optional[str]:
    """
    Determine item rarity based on daily weight loss using moving window.
    
    Uses a moving window system where higher weight loss shifts probability
    toward higher rarities:
    - Window pattern: [5%, 20%, 50%, 20%, 5%] centered on a tier
    - Overflow at edges is absorbed by the edge tier
    
    Distribution:
    - 0g: Common-centered (75% C, 20% U, 5% R)
    - 100g: Uncommon-centered (25% C, 50% U, 20% R, 5% E)
    - 200g: Rare-centered (5% C, 20% U, 50% R, 20% E, 5% L)
    - 300g: Epic-centered (5% U, 20% R, 50% E, 25% L)
    - 400g: Legendary-centered (5% R, 20% E, 75% L)
    - 500g+: 100% Legendary
    
    Entity Bonus (rat/mouse entities):
    - Each collected rat/mouse entity adds +1% (or +2% if exceptional) to
      Legendary chance, subtracted from lower tiers proportionally.
    
    Args:
        weight_loss_grams: Weight lost since previous entry (in grams)
        legendary_bonus: Extra % chance to add to Legendary (from rat/mouse entities)
    
    Returns:
        Rarity string selected from weighted distribution
    """
    outcome = roll_daily_weight_reward_outcome(
        weight_loss_grams=weight_loss_grams,
        legendary_bonus=legendary_bonus,
        adhd_buster=adhd_buster,
        roll=roll,
    )
    if not outcome:
        return None
    return outcome.get("rarity")


def get_daily_weight_reward_weights(weight_loss_grams: float, legendary_bonus: int = 0) -> Optional[list]:
    """
    Get weight reward weights for a given weight loss/gain amount.
    
    Mirrors get_daily_weight_reward_rarity without performing the random draw.
    
    Args:
        weight_loss_grams: Weight loss (or gain) in grams, expected >= 0 for progress
        legendary_bonus: Extra % chance to add to Legendary (from rat/mouse entities)
    
    Returns:
        List of weights aligned with `get_standard_reward_rarity_order()` summing to 100,
        or None if weight_loss_grams is negative.
    """
    if weight_loss_grams < 0:
        return None
    
    # Determine center tier based on weight loss
    # Tiers map to get_standard_reward_rarity_order() indices.
    if weight_loss_grams >= 500:
        center_tier = 6  # Far enough for 100% top obtainable tier
    elif weight_loss_grams >= 400:
        center_tier = 4  # Legendary-centered distribution
    elif weight_loss_grams >= 300:
        center_tier = 3  # Epic-centered
    elif weight_loss_grams >= 200:
        center_tier = 2  # Rare-centered
    elif weight_loss_grams >= 100:
        center_tier = 1  # Uncommon-centered
    else:  # 0-99g (maintained or small loss) - Common centered
        center_tier = 0
    
    # Moving window: [5%, 20%, 50%, 20%, 5%] centered on center_tier
    window = [5, 20, 50, 20, 5]  # -2, -1, 0, +1, +2 from center
    rarities = get_standard_reward_rarity_order()
    weights = [0] * len(rarities)
    
    for offset, pct in zip([-2, -1, 0, 1, 2], window):
        target_tier = center_tier + offset
        # Clamp to valid range - overflow absorbed at edges
        clamped_tier = max(0, min(len(rarities) - 1, target_tier))
        weights[clamped_tier] += pct
    
    # Apply legendary bonus from rat/mouse entities
    top_idx = len(weights) - 1
    if legendary_bonus > 0 and weights[top_idx] < 100:
        # Cap bonus so top tier doesn't exceed 100%
        actual_bonus = min(legendary_bonus, 100 - weights[top_idx])
        weights[top_idx] += actual_bonus
        
        # Subtract bonus proportionally from lower tiers
        remaining = actual_bonus
        for i in range(top_idx - 1, -1, -1):  # high -> low
            if remaining <= 0:
                break
            subtract = min(weights[i], remaining)
            weights[i] -= subtract
            remaining -= subtract
    
    return weights


# Rarity order for comparison (higher index = better)
RARITY_ORDER = get_rarity_order()


def _better_rarity(rarity_a: str, rarity_b: str) -> str:
    """
    Return the better (higher tier) of two rarities.
    
    Args:
        rarity_a: First rarity string
        rarity_b: Second rarity string
    
    Returns:
        The better rarity of the two
    """
    if not rarity_a:
        return _canonical_rarity(rarity_b, default="Common")
    if not rarity_b:
        return _canonical_rarity(rarity_a, default="Common")

    rarity_a_norm = _canonical_rarity(rarity_a, default="Common")
    rarity_b_norm = _canonical_rarity(rarity_b, default="Common")
    try:
        idx_a = RARITY_ORDER.index(rarity_a_norm)
        idx_b = RARITY_ORDER.index(rarity_b_norm)
        return rarity_a_norm if idx_a >= idx_b else rarity_b_norm
    except ValueError:
        return rarity_a_norm or rarity_b_norm or "Common"


def _weights_for_rarity(rarity: str) -> list:
    """Return 100% weight for a single rarity."""
    weights = [0] * len(RARITY_ORDER)
    target = _canonical_rarity(rarity, default="Common")
    try:
        idx = RARITY_ORDER.index(target)
    except ValueError:
        idx = 0
    weights[idx] = 100
    return weights


def _apply_minimum_rarity(weights: list, min_rarity: str) -> list:
    """
    Fold all probability mass below min_rarity into min_rarity.
    
    This matches _better_rarity behavior when comparing a random rarity
    against a fixed base rarity.
    """
    if not weights:
        return weights
    min_rarity_norm = _canonical_rarity(min_rarity, default="Common")
    try:
        min_idx = RARITY_ORDER.index(min_rarity_norm)
    except ValueError:
        min_idx = 0
    if min_idx <= 0:
        return list(weights)
    new_weights = list(weights)
    lower_sum = sum(new_weights[:min_idx])
    for i in range(min_idx):
        new_weights[i] = 0
    new_weights[min_idx] += lower_sum
    return new_weights


def check_weight_entry_rewards(weight_entries: list, new_weight: float, 
                                current_date: str, story_id: str = None,
                                adhd_buster: dict = None, height_cm: float = None,
                                goal_weight: float = None) -> dict:
    """
    Check and generate rewards for a new weight entry.
    
    Supports three weight modes:
    - LOSS mode (overweight): Rewards weight loss
    - GAIN mode (underweight): Rewards healthy weight gain  
    - MAINTAIN mode (normal weight): Rewards staying stable
    
    Args:
        weight_entries: List of existing weight entries
        new_weight: The new weight being entered
        current_date: Today's date (YYYY-MM-DD)
        story_id: Story theme for item generation
        adhd_buster: Optional main data dict for entity perk bonuses
        height_cm: User's height in cm (for BMI-based mode detection)
        goal_weight: Target weight in kg (for goal-based mode detection)
    
    Returns:
        Dict with:
            - daily_reward: item dict or None
            - weekly_reward: item dict or None  
            - monthly_reward: item dict or None
            - daily_change_grams: float (positive = good direction)
            - weekly_change_grams: float or None
            - monthly_change_grams: float or None
            - messages: list of reward messages
            - entity_bonus: int (legendary bonus from entities)
            - weight_mode: str ('loss', 'gain', or 'maintain')
    """
    result = {
        "daily_reward": None,
        "daily_reward_weights": None,
        "daily_power_gating": None,
        "weekly_reward": None,
        "weekly_power_gating": None,
        "monthly_reward": None,
        "monthly_power_gating": None,
        "daily_change_grams": 0,
        "daily_loss_grams": 0,  # Legacy compatibility
        "weekly_change_grams": None,
        "weekly_loss_grams": None,  # Legacy compatibility
        "monthly_change_grams": None,
        "monthly_loss_grams": None,  # Legacy compatibility
        "messages": [],
        "entity_bonus": 0,
        "weight_mode": WEIGHT_MODE_LOSS,
    }

    def _set_timed_reward(slot: str, target_rarity: str) -> tuple[str, str]:
        gate_result = resolve_power_gated_reward_rarity(
            target_rarity,
            adhd_buster=adhd_buster,
        )
        final_rarity = gate_result.get("rarity", target_rarity)
        power_gating = gate_result.get("power_gating")
        result[f"{slot}_power_gating"] = power_gating
        result[f"{slot}_reward"] = generate_item(rarity=final_rarity, story_id=story_id)
        lock_message = get_power_gate_downgrade_message(power_gating)
        return final_rarity, lock_message
    
    # Determine weight mode based on BMI/goal
    weight_mode = determine_weight_mode(new_weight, height_cm, goal_weight)
    result["weight_mode"] = weight_mode
    
    # Get entity legendary bonus from rat/mouse entities
    legendary_bonus = 0
    if adhd_buster:
        weight_perks = get_entity_weight_perks(adhd_buster)
        legendary_bonus = weight_perks.get("legendary_bonus", 0)
        result["entity_bonus"] = legendary_bonus
    
    # Calculate BMI status for bonus rewards
    is_in_healthy_range = False
    is_progressing_toward_healthy = False
    bmi_status = None
    
    if height_cm and height_cm > 0:
        height_m = height_cm / 100
        current_bmi = new_weight / (height_m ** 2)
        bmi_status = current_bmi
        
        # Check if in healthy BMI range (18.5-25 for adults)
        # For age-specific, we'd need age/sex but this is a reasonable default
        is_in_healthy_range = 18.5 <= current_bmi <= 25.0
    
    # Check for previous entry (daily comparison)
    prev_entry = get_previous_weight_entry(weight_entries, current_date)
    
    # =========================================================================
    # ALWAYS REWARD FOR LOGGING - Base reward even without previous entry
    # Better rewards for healthy behavior (in range, progressing correctly)
    # =========================================================================
    
    if prev_entry:
        prev_weight = prev_entry["weight"]
        # Raw change: positive = lost weight, negative = gained weight
        raw_change = calculate_weight_loss(new_weight, prev_weight)
        
        # Normalize change based on mode (positive = good progress)
        if weight_mode == WEIGHT_MODE_GAIN:
            # For underweight: weight gain is good (invert the sign)
            daily_progress = -raw_change
            progress_verb_good = "gained"
            progress_verb_bad = "lost"
            emoji_good = "đź’Ş"
            # Progressing toward healthy if gaining weight
            is_progressing_toward_healthy = raw_change < 0  # Gained weight
        elif weight_mode == WEIGHT_MODE_MAINTAIN:
            # For maintenance: staying same is best, small changes ok
            daily_progress = abs(raw_change)  # Use absolute for maintain mode
            progress_verb_good = "maintained"
            progress_verb_bad = "changed"
            emoji_good = "âš–ď¸Ź"
            # Progressing if stable (within 500g)
            is_progressing_toward_healthy = abs(raw_change) <= 500
        else:  # WEIGHT_MODE_LOSS (default)
            daily_progress = raw_change
            progress_verb_good = "lost"
            progress_verb_bad = "gained"
            emoji_good = "đźŽ‰"
            # Progressing toward healthy if losing weight
            is_progressing_toward_healthy = raw_change > 0  # Lost weight
        
        result["daily_change_grams"] = daily_progress
        result["daily_loss_grams"] = raw_change  # Legacy compatibility
        
        # Determine reward rarity based on behavior:
        # - ALWAYS get at least Common for logging
        # - Best: Progressing toward healthy (active improvement takes effort!)
        # - Good: Already in healthy range (maintenance is good)
        # - Base: Just logging (neither improving nor in range)
        
        if is_progressing_toward_healthy:
            # Best case: Actively improving toward healthy range - this takes effort!
            base_rarity = "Rare"
            bonus_msg = "đź“ Great Progress!"
        elif is_in_healthy_range:
            # Good: Already in healthy BMI range - maintaining is valuable
            base_rarity = "Uncommon"
            bonus_msg = "đź’š Healthy Range!"
        else:
            # Base reward just for logging
            base_rarity = "Common"
            bonus_msg = "đź“ť Logged!"
        
        # LOSS mode: reward weight loss
        if weight_mode == WEIGHT_MODE_LOSS:
            if raw_change > 0:
                # Progress reward - use the higher of calculated or base rarity
                progress_outcome = roll_daily_weight_reward_outcome(
                    raw_change,
                    legendary_bonus=legendary_bonus,
                    adhd_buster=adhd_buster,
                )
                progress_rarity = (
                    progress_outcome.get("rarity")
                    if isinstance(progress_outcome, dict)
                    else get_daily_weight_reward_rarity(raw_change, legendary_bonus)
                )
                rarity = _better_rarity(progress_rarity, base_rarity)
                progress_weights = (
                    progress_outcome.get("weights")
                    if isinstance(progress_outcome, dict)
                    else get_daily_weight_reward_weights(raw_change, legendary_bonus)
                )
                if progress_weights:
                    result["daily_reward_weights"] = _apply_minimum_rarity(progress_weights, base_rarity)
                else:
                    result["daily_reward_weights"] = _weights_for_rarity(rarity)
                final_gate_outcome = evaluate_power_gated_rarity_roll(
                    get_standard_reward_rarity_order(),
                    result["daily_reward_weights"],
                    adhd_buster=adhd_buster,
                    preferred_rarity=rarity,
                )
                result["daily_power_gating"] = final_gate_outcome
                rarity = final_gate_outcome.get("rarity", rarity)
                if final_gate_outcome.get("downgraded"):
                    lock_message = final_gate_outcome.get("message") or (
                        f"Tier gated by power. Current cap: {final_gate_outcome.get('max_unlocked_rarity', 'Unknown')}."
                    )
                    result["messages"].append(f"🔒 {lock_message}")
                result["daily_reward"] = generate_item(rarity=rarity, story_id=story_id)
                bonus_note = f" (+{legendary_bonus}% đź€)" if legendary_bonus > 0 else ""
                result["messages"].append(
                    f"đźŽ‰ Daily Progress: Lost {raw_change:.0f}g! {bonus_msg} Earned a {rarity} item!{bonus_note}"
                )
            elif raw_change == 0:
                rarity = _better_rarity(base_rarity, "Common")
                result["daily_reward_weights"] = _weights_for_rarity(rarity)
                result["daily_reward"] = generate_item(rarity=rarity, story_id=story_id)
                result["messages"].append(f"đź’Ş Maintained weight! {bonus_msg} Earned a {rarity} item.")
            else:
                # Going wrong direction - still reward for logging, but base tier
                rarity = base_rarity
                result["daily_reward_weights"] = _weights_for_rarity(rarity)
                result["daily_reward"] = generate_item(rarity=rarity, story_id=story_id)
                result["messages"].append(f"đź“ Weight up {abs(raw_change):.0f}g - keep tracking! Earned a {rarity} item.")
        
        # GAIN mode: reward weight gain (for underweight users)
        elif weight_mode == WEIGHT_MODE_GAIN:
            weight_gain = -raw_change  # Make positive for gain
            if weight_gain > 0:
                # Progress reward - use the higher of calculated or base rarity
                progress_outcome = roll_daily_weight_reward_outcome(
                    weight_gain,
                    legendary_bonus=legendary_bonus,
                    adhd_buster=adhd_buster,
                )
                progress_rarity = (
                    progress_outcome.get("rarity")
                    if isinstance(progress_outcome, dict)
                    else get_daily_weight_reward_rarity(weight_gain, legendary_bonus)
                )
                rarity = _better_rarity(progress_rarity, base_rarity)
                progress_weights = (
                    progress_outcome.get("weights")
                    if isinstance(progress_outcome, dict)
                    else get_daily_weight_reward_weights(weight_gain, legendary_bonus)
                )
                if progress_weights:
                    result["daily_reward_weights"] = _apply_minimum_rarity(progress_weights, base_rarity)
                else:
                    result["daily_reward_weights"] = _weights_for_rarity(rarity)
                final_gate_outcome = evaluate_power_gated_rarity_roll(
                    get_standard_reward_rarity_order(),
                    result["daily_reward_weights"],
                    adhd_buster=adhd_buster,
                    preferred_rarity=rarity,
                )
                result["daily_power_gating"] = final_gate_outcome
                rarity = final_gate_outcome.get("rarity", rarity)
                if final_gate_outcome.get("downgraded"):
                    lock_message = final_gate_outcome.get("message") or (
                        f"Tier gated by power. Current cap: {final_gate_outcome.get('max_unlocked_rarity', 'Unknown')}."
                    )
                    result["messages"].append(f"🔒 {lock_message}")
                result["daily_reward"] = generate_item(rarity=rarity, story_id=story_id)
                bonus_note = f" (+{legendary_bonus}% đź€)" if legendary_bonus > 0 else ""
                result["messages"].append(
                    f"đź’Ş Healthy Gain: +{weight_gain:.0f}g! {bonus_msg} Earned a {rarity} item!{bonus_note}"
                )
            elif weight_gain == 0:
                rarity = _better_rarity(base_rarity, "Common")
                result["daily_reward_weights"] = _weights_for_rarity(rarity)
                result["daily_reward"] = generate_item(rarity=rarity, story_id=story_id)
                result["messages"].append(f"âš–ď¸Ź Stable weight - {bonus_msg} Earned a {rarity} item.")
            else:
                # Going wrong direction - still reward for logging
                rarity = base_rarity
                result["daily_reward_weights"] = _weights_for_rarity(rarity)
                result["daily_reward"] = generate_item(rarity=rarity, story_id=story_id)
                result["messages"].append(f"đź“‰ Weight down {abs(weight_gain):.0f}g - keep tracking! Earned a {rarity} item.")
        
        # MAINTAIN mode: reward staying within range
        else:  # WEIGHT_MODE_MAINTAIN
            abs_change = abs(raw_change)
            # More reward for staying closer to same weight
            if abs_change <= 100:  # Within 100g is excellent
                rarity = _better_rarity("Rare", base_rarity)
                result["daily_reward_weights"] = _weights_for_rarity(rarity)
                result["daily_reward"] = generate_item(rarity=rarity, story_id=story_id)
                result["messages"].append(
                    f"âš–ď¸Ź Perfect maintenance! (Â±{abs_change:.0f}g) {bonus_msg} Earned a {rarity} item!"
                )
            elif abs_change <= 200:  # Within 200g is good
                rarity = _better_rarity("Uncommon", base_rarity)
                result["daily_reward_weights"] = _weights_for_rarity(rarity)
                result["daily_reward"] = generate_item(rarity=rarity, story_id=story_id)
                result["messages"].append(
                    f"âš–ď¸Ź Good stability! (Â±{abs_change:.0f}g) {bonus_msg} Earned a {rarity} item."
                )
            elif abs_change <= 500:  # Within 500g is acceptable
                rarity = _better_rarity("Common", base_rarity)
                result["daily_reward_weights"] = _weights_for_rarity(rarity)
                result["daily_reward"] = generate_item(rarity=rarity, story_id=story_id)
                change_dir = "up" if raw_change < 0 else "down"
                result["messages"].append(
                    f"âš–ď¸Ź Weight {change_dir} {abs_change:.0f}g - {bonus_msg} Earned a {rarity} item."
                )
            else:
                # Large fluctuation - still reward for logging
                change_dir = "up" if raw_change < 0 else "down"
                rarity = base_rarity
                result["daily_reward_weights"] = _weights_for_rarity(rarity)
                result["daily_reward"] = generate_item(rarity=rarity, story_id=story_id)
                result["messages"].append(
                    f"đź“Š Weight {change_dir} {abs_change:.0f}g - keep tracking! Earned a {rarity} item."
                )
    else:
        # NO PREVIOUS ENTRY - First time logging or first log in a while
        # Always reward for starting/resuming the tracking habit!
        if is_in_healthy_range:
            rarity = "Uncommon"
            bonus_msg = "đź’š You're in a healthy range!"
        else:
            rarity = "Common"
            if weight_mode == WEIGHT_MODE_LOSS:
                bonus_msg = "Let's work toward your goal!"
            elif weight_mode == WEIGHT_MODE_GAIN:
                bonus_msg = "Let's build healthy mass!"
            else:
                bonus_msg = "Great start!"
        
        result["daily_reward_weights"] = _weights_for_rarity(rarity)
        result["daily_reward"] = generate_item(rarity=rarity, story_id=story_id)
        result["messages"].append(f"đź“ť Weight logged! {bonus_msg} Earned a {rarity} item.")
    
    # Calculate date 7 days ago for weekly check
    from datetime import datetime, timedelta
    try:
        today = datetime.strptime(current_date, "%Y-%m-%d")
        week_ago_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        month_ago_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    except ValueError:
        return result
    
    # Check weekly progress (vs ~7 days ago)
    week_ago_entry = get_closest_weight_before_date(weight_entries, week_ago_date)
    if week_ago_entry and week_ago_entry["date"] != current_date:
        weekly_change = calculate_weight_loss(new_weight, week_ago_entry["weight"])
        result["weekly_change_grams"] = weekly_change
        result["weekly_loss_grams"] = weekly_change  # Legacy compatibility
        
        # Determine threshold based on mode
        if weight_mode == WEIGHT_MODE_GAIN:
            weekly_gain = -weekly_change
            if weekly_gain >= WEIGHT_WEEKLY_LEGENDARY_THRESHOLD:
                final_rarity, lock_message = _set_timed_reward("weekly", "Legendary")
                result["messages"].append(
                    f"đźŚź WEEKLY {final_rarity.upper()}! Gained {weekly_gain:.0f}g this week! "
                    f"(vs {week_ago_entry['date']})"
                )
                if lock_message:
                    result["messages"].append(f"🔒 {lock_message}")
            elif weekly_gain >= 300:
                final_rarity, lock_message = _set_timed_reward("weekly", "Epic")
                result["messages"].append(
                    f"đźŹ† Great week! Gained {weekly_gain:.0f}g - {final_rarity} reward!"
                )
                if lock_message:
                    result["messages"].append(f"🔒 {lock_message}")
        elif weight_mode == WEIGHT_MODE_MAINTAIN:
            abs_weekly = abs(weekly_change)
            if abs_weekly <= 200:  # Very stable week
                final_rarity, lock_message = _set_timed_reward("weekly", "Rare")
                result["messages"].append(
                    f"âš–ď¸Ź Stable week! (Â±{abs_weekly:.0f}g) {final_rarity} reward!"
                )
                if lock_message:
                    result["messages"].append(f"🔒 {lock_message}")
        else:  # WEIGHT_MODE_LOSS
            if weekly_change >= WEIGHT_WEEKLY_LEGENDARY_THRESHOLD:
                final_rarity, lock_message = _set_timed_reward("weekly", "Legendary")
                result["messages"].append(
                    f"đźŚź WEEKLY {final_rarity.upper()}! Lost {weekly_change:.0f}g this week! "
                    f"(vs {week_ago_entry['date']})"
                )
                if lock_message:
                    result["messages"].append(f"🔒 {lock_message}")
            elif weekly_change >= 300:
                final_rarity, lock_message = _set_timed_reward("weekly", "Epic")
                result["messages"].append(
                    f"đźŹ† Great week! Lost {weekly_change:.0f}g - {final_rarity} reward!"
                )
                if lock_message:
                    result["messages"].append(f"🔒 {lock_message}")
    
    # Check monthly progress (vs ~30 days ago)
    month_ago_entry = get_closest_weight_before_date(weight_entries, month_ago_date)
    if month_ago_entry and month_ago_entry["date"] != current_date:
        monthly_change = calculate_weight_loss(new_weight, month_ago_entry["weight"])
        result["monthly_change_grams"] = monthly_change
        result["monthly_loss_grams"] = monthly_change  # Legacy compatibility
        
        if weight_mode == WEIGHT_MODE_GAIN:
            monthly_gain = -monthly_change
            if monthly_gain >= WEIGHT_MONTHLY_LEGENDARY_THRESHOLD:
                final_rarity, lock_message = _set_timed_reward("monthly", "Legendary")
                result["messages"].append(
                    f"đź’’ MONTHLY {final_rarity.upper()}! Gained {monthly_gain/1000:.1f}kg this month! "
                    f"(vs {month_ago_entry['date']})"
                )
                if lock_message:
                    result["messages"].append(f"🔒 {lock_message}")
            elif monthly_gain >= 1500:
                final_rarity, lock_message = _set_timed_reward("monthly", "Epic")
                result["messages"].append(
                    f"đźŽŠ Amazing month! Gained {monthly_gain/1000:.1f}kg - {final_rarity} reward!"
                )
                if lock_message:
                    result["messages"].append(f"🔒 {lock_message}")
        elif weight_mode == WEIGHT_MODE_MAINTAIN:
            abs_monthly = abs(monthly_change)
            if abs_monthly <= 500:  # Very stable month
                final_rarity, lock_message = _set_timed_reward("monthly", "Epic")
                result["messages"].append(
                    f"âš–ď¸Ź Rock-solid month! (Â±{abs_monthly:.0f}g) {final_rarity} reward!"
                )
                if lock_message:
                    result["messages"].append(f"🔒 {lock_message}")
            elif abs_monthly <= 1000:  # Fairly stable
                final_rarity, lock_message = _set_timed_reward("monthly", "Rare")
                result["messages"].append(
                    f"âš–ď¸Ź Good month! (Â±{abs_monthly:.0f}g) {final_rarity} reward!"
                )
                if lock_message:
                    result["messages"].append(f"🔒 {lock_message}")
        else:  # WEIGHT_MODE_LOSS
            if monthly_change >= WEIGHT_MONTHLY_LEGENDARY_THRESHOLD:
                final_rarity, lock_message = _set_timed_reward("monthly", "Legendary")
                result["messages"].append(
                    f"đź’’ MONTHLY {final_rarity.upper()}! Lost {monthly_change/1000:.1f}kg this month! "
                    f"(vs {month_ago_entry['date']})"
                )
                if lock_message:
                    result["messages"].append(f"🔒 {lock_message}")
            elif monthly_change >= 1500:
                final_rarity, lock_message = _set_timed_reward("monthly", "Epic")
                result["messages"].append(
                    f"đźŽŠ Amazing month! Lost {monthly_change/1000:.1f}kg - {final_rarity} reward!"
                )
                if lock_message:
                    result["messages"].append(f"🔒 {lock_message}")
    
    return result


def get_weight_stats(weight_entries: list, unit: str = "kg") -> dict:
    """
    Calculate weight statistics for display.
    
    Args:
        weight_entries: List of weight entries
        unit: Weight unit (kg or lbs)
    
    Returns:
        Dict with various statistics
    """
    if not weight_entries:
        return {
            "current": None,
            "starting": None,
            "lowest": None,
            "highest": None,
            "total_change": None,
            "trend_7d": None,
            "trend_30d": None,
            "entries_count": 0,
            "streak_days": 0,
        }
    
    # Sort by date
    sorted_entries = sorted(
        [e for e in weight_entries
         if isinstance(e, dict)
         and isinstance(e.get("date"), str)
         and e.get("date")
         and isinstance(e.get("weight"), (int, float))],
        key=lambda x: x["date"]
    )
    
    if not sorted_entries:
        return {
            "current": None,
            "starting": None,
            "lowest": None,
            "highest": None,
            "total_change": None,
            "trend_7d": None,
            "trend_30d": None,
            "entries_count": 0,
            "streak_days": 0,
        }
    
    weights = [e["weight"] for e in sorted_entries]
    current = sorted_entries[-1]["weight"]
    starting = sorted_entries[0]["weight"]
    
    # Calculate trends
    from datetime import datetime, timedelta
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    week_entry = get_closest_weight_before_date(sorted_entries, week_ago)
    month_entry = get_closest_weight_before_date(sorted_entries, month_ago)
    
    # Calculate entry streak (consecutive days with entries)
    streak = 0
    check_date = datetime.now()
    for i in range(365):  # Check up to a year
        date_str = check_date.strftime("%Y-%m-%d")
        if any(e["date"] == date_str for e in sorted_entries):
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    return {
        "current": current,
        "starting": starting,
        "lowest": min(weights),
        "highest": max(weights),
        "total_change": starting - current,
        "trend_7d": (week_entry["weight"] - current) if week_entry else None,
        "trend_30d": (month_entry["weight"] - current) if month_entry else None,
        "entries_count": len(sorted_entries),
        "streak_days": streak,
        "unit": unit,
    }


def format_weight_change(change_kg: float, unit: str = "kg") -> str:
    """Format weight change with appropriate sign and unit."""
    if change_kg is None:
        return "N/A"
    
    if unit == "lbs":
        change = change_kg * 2.20462
        unit_str = "lbs"
    else:
        change = change_kg
        unit_str = "kg"
    
    if change > 0:
        return f"\u2193 {change:.1f} {unit_str}"  # Lost weight (good)
    elif change < 0:
        return f"\u2191 {abs(change):.1f} {unit_str}"  # Gained weight
    else:
        return f"\u2192 0 {unit_str}"  # No change


# ============================================================================
# WEIGHT TRACKING: STREAKS, MILESTONES & MAINTENANCE
# ============================================================================

# Streak thresholds for rewards
WEIGHT_STREAK_THRESHOLDS = {
    7: "Rare",      # 1 week streak
    14: "Epic",     # 2 week streak  
    30: "Legendary", # 1 month streak
    60: "Legendary", # 2 month streak
    100: "Legendary", # 100 day streak
}

# Milestone definitions (one-time achievements)
WEIGHT_MILESTONES = {
    "first_entry": {
        "name": "First Step",
        "description": "Log your first weight entry",
        "rarity": "Common",
        "check": lambda entries, goal, starting: len(entries) >= 1,
    },
    "week_logger": {
        "name": "Consistent Tracker",
        "description": "Log weight for 7 consecutive days",
        "rarity": "Rare",
        "check": lambda entries, goal, starting: _check_streak(entries) >= 7,
    },
    "month_logger": {
        "name": "Dedicated Logger", 
        "description": "Log weight for 30 consecutive days",
        "rarity": "Legendary",
        "check": lambda entries, goal, starting: _check_streak(entries) >= 30,
    },
    "lost_1kg": {
        "name": "First Kilogram",
        "description": "Lose 1 kg from your starting weight",
        "rarity": "Uncommon",
        "check": lambda entries, goal, starting: _check_weight_loss(entries, starting, 1.0),
    },
    "lost_5kg": {
        "name": "Five Down",
        "description": "Lose 5 kg from your starting weight",
        "rarity": "Rare",
        "check": lambda entries, goal, starting: _check_weight_loss(entries, starting, 5.0),
    },
    "lost_10kg": {
        "name": "Double Digits",
        "description": "Lose 10 kg from your starting weight",
        "rarity": "Epic",
        "check": lambda entries, goal, starting: _check_weight_loss(entries, starting, 10.0),
    },
    "lost_20kg": {
        "name": "Transformation",
        "description": "Lose 20 kg from your starting weight",
        "rarity": "Legendary",
        "check": lambda entries, goal, starting: _check_weight_loss(entries, starting, 20.0),
    },
    "goal_reached": {
        "name": "Goal Achieved!",
        "description": "Reach your target weight",
        "rarity": "Legendary",
        "check": lambda entries, goal, starting: _check_goal_reached(entries, goal),
    },
}


def _is_weekend(date_obj) -> bool:
    """Check if a date is Saturday (5) or Sunday (6)."""
    return date_obj.weekday() in (5, 6)


def _get_previous_required_day(from_date, entry_dates: set) -> tuple:
    """
    Get the previous day that was required for streak (skipping weekends).
    
    Returns:
        (date_obj, date_str, was_weekend_skipped)
    """
    from datetime import timedelta
    
    current = from_date - timedelta(days=1)
    
    # Skip weekends - they don't break streaks
    while _is_weekend(current):
        date_str = current.strftime("%Y-%m-%d")
        # But if they logged on weekend, count it!
        if date_str in entry_dates:
            return current, date_str, False
        current = current - timedelta(days=1)
    
    return current, current.strftime("%Y-%m-%d"), False


def _check_streak(weight_entries: list) -> int:
    """
    Calculate current logging streak (consecutive days with entries).
    
    Weekend tolerance: Not logging on Saturday/Sunday doesn't break the streak.
    If you log Friday and Monday, the streak continues.
    Logging on weekends still counts toward the streak.
    """
    if not weight_entries:
        return 0
    
    from datetime import datetime, timedelta
    
    sorted_entries = sorted(
        [e for e in weight_entries if e.get("date") and e.get("weight") is not None],
        key=lambda x: x["date"]
    )
    
    if not sorted_entries:
        return 0
    
    # Get dates with entries
    entry_dates = set(e["date"] for e in sorted_entries)
    
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today_dt = datetime.now()
    yesterday_dt = today_dt - timedelta(days=1)
    
    # Find the most recent valid entry point (today, yesterday, or last Friday if weekend)
    if today in entry_dates:
        current = datetime.strptime(today, "%Y-%m-%d")
        streak = 1
    elif yesterday in entry_dates:
        current = datetime.strptime(yesterday, "%Y-%m-%d")
        streak = 1
    elif _is_weekend(today_dt):
        # It's weekend and no entry today/yesterday - check if Friday had entry
        days_to_friday = (today_dt.weekday() - 4) % 7
        if days_to_friday == 0:
            days_to_friday = 7  # If it's Friday, look at last Friday
        last_friday = today_dt - timedelta(days=days_to_friday)
        friday_str = last_friday.strftime("%Y-%m-%d")
        if friday_str in entry_dates:
            current = last_friday
            streak = 1
        else:
            return 0
    else:
        return 0
    
    # Count backwards from current, skipping weekends if needed
    while True:
        prev_date, prev_str, _ = _get_previous_required_day(current, entry_dates)
        if prev_str in entry_dates:
            streak += 1
            current = prev_date
        else:
            break
    
    return streak


def _check_weight_loss(weight_entries: list, starting_weight: float, target_loss_kg: float) -> bool:
    """Check if user has lost at least target_loss_kg from starting weight."""
    if not weight_entries or starting_weight is None:
        return False
    if not isinstance(starting_weight, (int, float)):
        return False
    
    sorted_entries = sorted(
        [e for e in weight_entries if e.get("date") and e.get("weight") is not None],
        key=lambda x: x["date"],
        reverse=True
    )
    
    if not sorted_entries:
        return False
    
    current = sorted_entries[0]["weight"]
    if not isinstance(current, (int, float)):
        return False
    return (starting_weight - current) >= target_loss_kg


def _check_goal_reached(weight_entries: list, goal: float) -> bool:
    """Check if user has reached their goal weight (works for both loss and gain goals)."""
    if not weight_entries or goal is None:
        return False
    if not isinstance(goal, (int, float)):
        return False
    
    sorted_entries = sorted(
        [e for e in weight_entries if e.get("date") and e.get("weight") is not None],
        key=lambda x: x["date"]
    )
    
    if not sorted_entries:
        return False
    
    starting = sorted_entries[0]["weight"]
    current = sorted_entries[-1]["weight"]
    if not isinstance(starting, (int, float)) or not isinstance(current, (int, float)):
        return False
    
    # Determine goal direction from starting weight
    if starting > goal:
        # Weight loss goal: current should be at or below goal
        return current <= goal
    elif starting < goal:
        # Weight gain goal: current should be at or above goal
        return current >= goal
    else:
        # Started at goal - consider reached if within 0.1 kg
        return abs(current - goal) <= 0.1


def check_weight_streak_reward(
    weight_entries: list,
    achieved_milestones: list,
    story_id: str = None,
    adhd_buster: Optional[dict] = None,
) -> Optional[dict]:
    """
    Check if a streak threshold was just reached and generate reward.
    
    Args:
        weight_entries: List of weight entries
        achieved_milestones: List of already achieved milestone IDs
        story_id: Story theme for item generation
    
    Returns:
        Dict with reward info or None
    """
    streak = _check_streak(weight_entries)
    
    # Check if we just hit a threshold that hasn't been rewarded
    for days, rarity in sorted(WEIGHT_STREAK_THRESHOLDS.items()):
        milestone_id = f"streak_{days}"
        if streak >= days and milestone_id not in achieved_milestones:
            gate_result = resolve_power_gated_reward_rarity(rarity, adhd_buster=adhd_buster)
            final_rarity = gate_result.get("rarity", rarity)
            power_gating = gate_result.get("power_gating")
            lock_message = get_power_gate_downgrade_message(power_gating)
            return {
                "milestone_id": milestone_id,
                "streak_days": days,
                "requested_rarity": rarity,
                "rarity": final_rarity,
                "power_gating": power_gating,
                "item": generate_item(rarity=final_rarity, story_id=story_id),
                "message": (
                    f"đź”Ą {days}-Day Logging Streak! Earned a {final_rarity} item!"
                    + (f" 🔒 {lock_message}" if lock_message else "")
                ),
            }
    
    return None


def check_weight_milestones(
    weight_entries: list,
    goal: float,
    achieved_milestones: list,
    story_id: str = None,
    adhd_buster: Optional[dict] = None,
) -> list:
    """
    Check for newly achieved milestones.
    
    Args:
        weight_entries: List of weight entries
        goal: Goal weight (or None)
        achieved_milestones: List of already achieved milestone IDs
        story_id: Story theme for item generation
    
    Returns:
        List of newly achieved milestone dicts with rewards
    """
    new_milestones = []
    
    if not weight_entries:
        return new_milestones
    
    # Get starting weight (first entry)
    sorted_entries = sorted(
        [e for e in weight_entries if e.get("date") and e.get("weight") is not None],
        key=lambda x: x["date"]
    )
    
    if not sorted_entries:
        return new_milestones
    
    starting_weight = sorted_entries[0]["weight"]
    
    for milestone_id, milestone in WEIGHT_MILESTONES.items():
        if milestone_id in achieved_milestones:
            continue
        
        try:
            if milestone["check"](weight_entries, goal, starting_weight):
                requested_rarity = milestone["rarity"]
                gate_result = resolve_power_gated_reward_rarity(
                    requested_rarity,
                    adhd_buster=adhd_buster,
                )
                final_rarity = gate_result.get("rarity", requested_rarity)
                power_gating = gate_result.get("power_gating")
                lock_message = get_power_gate_downgrade_message(power_gating)
                new_milestones.append({
                    "milestone_id": milestone_id,
                    "name": milestone["name"],
                    "description": milestone["description"],
                    "requested_rarity": requested_rarity,
                    "rarity": final_rarity,
                    "power_gating": power_gating,
                    "item": generate_item(rarity=final_rarity, story_id=story_id),
                    "message": (
                        f"đźŹ† Milestone: {milestone['name']}! ({milestone['description']}) - {final_rarity} reward!"
                        + (f" 🔒 {lock_message}" if lock_message else "")
                    ),
                })
        except Exception:
            # Skip milestone if check fails
            continue
    
    return new_milestones


def check_weight_maintenance(
    weight_entries: list,
    goal: float,
    story_id: str = None,
    adhd_buster: Optional[dict] = None,
) -> Optional[dict]:
    """
    Check if user is in maintenance mode (at goal, staying within Â±0.5kg).
    
    Args:
        weight_entries: List of weight entries  
        goal: Goal weight (kg)
        story_id: Story theme for item generation
    
    Returns:
        Dict with maintenance reward info or None
    """
    if goal is None or not weight_entries:
        return None
    
    sorted_entries = sorted(
        [e for e in weight_entries if e.get("date") and e.get("weight") is not None],
        key=lambda x: x["date"],
        reverse=True
    )
    
    if not sorted_entries:
        return None
    
    current = sorted_entries[0]["weight"]
    
    # Check if within Â±0.5kg of goal
    deviation = abs(current - goal)
    if deviation > 0.5:
        return None  # Not in maintenance range
    
    # Count consecutive days in maintenance range
    from datetime import datetime, timedelta
    
    maintenance_days = 0
    check_date = datetime.now()
    
    for i in range(365):
        date_str = check_date.strftime("%Y-%m-%d")
        entry = next((e for e in sorted_entries if e["date"] == date_str), None)
        
        if entry:
            if abs(entry["weight"] - goal) <= 0.5:
                maintenance_days += 1
                check_date -= timedelta(days=1)
            else:
                break
        else:
            # No entry for this day, don't break streak but don't count
            check_date -= timedelta(days=1)
            if i > 7:  # Allow up to 7 days gap
                break
    
    if maintenance_days == 0:
        return None
    
    # Determine reward based on maintenance streak
    if maintenance_days >= 30:
        requested_rarity = "Legendary"
        message = "đź’’ 30+ Days in Maintenance! Perfect control!"
    elif maintenance_days >= 14:
        requested_rarity = "Epic"
        message = "đźŚź 2+ Weeks in Maintenance! Excellent stability!"
    elif maintenance_days >= 7:
        requested_rarity = "Rare"
        message = "đź’Ş 1 Week in Maintenance! Great job staying on target!"
    else:
        requested_rarity = "Uncommon"
        message = f"âś… Maintaining goal weight! ({deviation*1000:.0f}g from target)"

    gate_result = resolve_power_gated_reward_rarity(requested_rarity, adhd_buster=adhd_buster)
    final_rarity = gate_result.get("rarity", requested_rarity)
    power_gating = gate_result.get("power_gating")
    lock_message = get_power_gate_downgrade_message(power_gating)
    message = f"{message} {final_rarity} reward!"
    if lock_message:
        message = f"{message} 🔒 {lock_message}"
    
    return {
        "maintenance_days": maintenance_days,
        "deviation_kg": deviation,
        "requested_rarity": requested_rarity,
        "rarity": final_rarity,
        "power_gating": power_gating,
        "item": generate_item(rarity=final_rarity, story_id=story_id),
        "message": message,
    }


def check_all_weight_rewards(weight_entries: list, new_weight: float, current_date: str,
                             goal: float, achieved_milestones: list, 
                             story_id: str = None, adhd_buster: dict = None,
                             height_cm: float = None) -> dict:
    """
    Comprehensive check for all weight-related rewards.
    
    Combines daily/weekly/monthly rewards with streak, milestone, and maintenance rewards.
    Supports three weight modes: loss (overweight), gain (underweight), maintain (normal).
    
    Args:
        weight_entries: Existing entries (WITHOUT the new entry)
        new_weight: New weight being logged
        current_date: Today's date
        goal: Goal weight or None
        achieved_milestones: List of already achieved milestone IDs
        story_id: Story theme
        adhd_buster: Optional main data dict for entity perk bonuses
        height_cm: User's height in cm for BMI-based mode detection
    
    Returns:
        Dict with all reward information
    """
    # Get base rewards (daily/weekly/monthly) with mode-aware logic
    base_rewards = check_weight_entry_rewards(
        weight_entries, new_weight, current_date, story_id, adhd_buster,
        height_cm=height_cm, goal_weight=goal
    )
    
    # Create temp entries list including new entry for milestone checks
    temp_entries = weight_entries + [{"date": current_date, "weight": new_weight}]
    
    # Check streak rewards
    streak_reward = check_weight_streak_reward(
        temp_entries,
        achieved_milestones,
        story_id,
        adhd_buster=adhd_buster,
    )
    
    # Check milestone achievements
    new_milestones = check_weight_milestones(
        temp_entries,
        goal,
        achieved_milestones,
        story_id,
        adhd_buster=adhd_buster,
    )
    
    # Check maintenance mode
    maintenance_reward = check_weight_maintenance(
        temp_entries,
        goal,
        story_id,
        adhd_buster=adhd_buster,
    )
    
    # Compile all results
    result = {
        **base_rewards,
        "streak_reward": streak_reward,
        "new_milestones": new_milestones,
        "maintenance_reward": maintenance_reward,
        "current_streak": _check_streak(temp_entries),
    }
    
    # Add streak message
    if streak_reward:
        result["messages"].append(streak_reward["message"])
    
    # Add milestone messages
    for milestone in new_milestones:
        result["messages"].append(milestone["message"])
    
    # Add maintenance message (only if not already getting other rewards)
    if maintenance_reward and not base_rewards.get("daily_reward"):
        result["messages"].append(maintenance_reward["message"])
    
    return result


# ============================================================================
# WEIGHT TRACKING: BMI, PREDICTION, INSIGHTS & COMPARISONS
# ============================================================================

# BMI classifications (WHO standard)
BMI_CLASSIFICATIONS = [
    (0, 16.0, "Severely Underweight", "#ff6464"),
    (16.0, 17.0, "Moderately Underweight", "#ffaa64"),
    (17.0, 18.5, "Mildly Underweight", "#ffff64"),
    (18.5, 25.0, "Normal", "#00ff88"),
    (25.0, 30.0, "Overweight", "#ffff64"),
    (30.0, 35.0, "Obese Class I", "#ffaa64"),
    (35.0, 40.0, "Obese Class II", "#ff6464"),
    (40.0, 100.0, "Obese Class III", "#ff3232"),
]


def calculate_bmi(weight_kg: float, height_cm: float) -> Optional[float]:
    """
    Calculate BMI from weight and height.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
    
    Returns:
        BMI value or None if invalid inputs
    """
    if not weight_kg or not height_cm or height_cm <= 0 or weight_kg <= 0:
        return None
    
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)


def get_bmi_classification(bmi: float, age: int = None, sex: str = None) -> tuple:
    """
    Get BMI classification and color.
    
    For ages 2-19, uses age/sex-specific CDC BMI-for-age percentiles.
    For ages 20+ or unspecified, uses standard WHO adult classifications.
    
    Args:
        bmi: BMI value
        age: Age in years (optional, for pediatric classification)
        sex: "M" or "F" (optional, for pediatric classification)
    
    Returns:
        Tuple of (classification_name, color_hex)
    """
    if bmi is None:
        return ("Unknown", "#888888")
    
    # Use age-specific classification if age provided and in pediatric range
    if age is not None and 2 <= age <= 19:
        return get_bmi_classification_for_age(bmi, age, sex)
    
    # Adult classification (WHO standard)
    for min_bmi, max_bmi, name, color in BMI_CLASSIFICATIONS:
        if min_bmi <= bmi < max_bmi:
            return (name, color)
    
    return ("Unknown", "#888888")


def get_ideal_weight_range(height_cm: float, age: int = None, sex: str = None) -> tuple:
    """
    Calculate ideal weight range based on height and optionally age/sex.
    
    For ages 7-19, uses age/sex-specific BMI percentile thresholds.
    For ages 20+ or unspecified, uses standard 18.5-25 BMI range.
    
    Args:
        height_cm: Height in centimeters
        age: Age in years (optional, for pediatric thresholds)
        sex: "M" or "F" (optional, for pediatric thresholds)
    
    Returns:
        Tuple of (min_weight_kg, max_weight_kg)
    """
    if not height_cm or height_cm <= 0:
        return (None, None)
    
    # Use age-specific function if age provided
    if age is not None:
        return get_ideal_weight_range_for_age(height_cm, age, sex)
    
    # Adult range (standard)
    height_m = height_cm / 100
    min_weight = 18.5 * (height_m ** 2)
    max_weight = 25.0 * (height_m ** 2)
    
    return (min_weight, max_weight)


def predict_goal_date(weight_entries: list, goal_weight: float, 
                      current_weight: float = None) -> Optional[dict]:
    """
    Predict when goal weight will be reached based on current trend.
    
    Args:
        weight_entries: List of weight entries
        goal_weight: Target weight
        current_weight: Current weight (optional, uses latest if not provided)
    
    Returns:
        Dict with prediction info or None if can't predict
    """
    from datetime import datetime, timedelta
    
    if not weight_entries or goal_weight is None:
        return None
    
    # Get current weight
    sorted_entries = sorted(
        [e for e in weight_entries if e.get("date") and e.get("weight") is not None],
        key=lambda x: x["date"],
        reverse=True
    )
    
    if not sorted_entries:
        return None
    
    if current_weight is None:
        current_weight = sorted_entries[0]["weight"]

    latest_entry_date = safe_parse_date(sorted_entries[0].get("date", ""), default=datetime.now())
    if latest_entry_date is None:
        latest_entry_date = datetime.now()
    
    # Check if already at goal (within 0.1 kg tolerance)
    if abs(current_weight - goal_weight) <= 0.1:
        return {
            "status": "achieved",
            "message": "đźŽ‰ You've reached your goal!",
            "days_remaining": 0,
            "predicted_date": None,
            "is_losing": goal_weight <= current_weight,
        }
    
    # Determine goal direction from starting weight if available
    # If current != goal, the direction is: goal < current means losing
    # But if we've EXCEEDED the goal, we need to check the history
    starting_weight = sorted_entries[-1]["weight"] if sorted_entries else current_weight
    
    # Use starting weight to determine direction (more reliable)
    if starting_weight > goal_weight:
        # Started higher than goal = weight loss goal
        is_losing_goal = True
        if current_weight <= goal_weight:
            return {
                "status": "achieved",
                "message": "đźŽ‰ You've reached your goal!" if current_weight >= goal_weight - 0.1 else "đźŽ‰ You've exceeded your goal!",
                "days_remaining": 0,
                "predicted_date": None,
                "is_losing": True,
            }
    elif starting_weight < goal_weight:
        # Started lower than goal = weight gain goal
        is_losing_goal = False
        if current_weight >= goal_weight:
            return {
                "status": "achieved",
                "message": "đźŽ‰ You've reached your goal!" if current_weight <= goal_weight + 0.1 else "đźŽ‰ You've exceeded your goal!",
                "days_remaining": 0,
                "predicted_date": None,
                "is_losing": False,
            }
    else:
        # Started at goal - use current vs goal to determine direction
        is_losing_goal = goal_weight < current_weight
    
    # Need at least 7 days of data for reliable prediction
    if len(sorted_entries) < 7:
        return {
            "status": "insufficient_data",
            "message": "Log weight for 7+ days to see prediction",
            "days_remaining": None,
            "predicted_date": None,
            "is_losing": is_losing_goal,
        }
    
    # Calculate rate of change (linear regression over last 30 logged days)
    cutoff = latest_entry_date - timedelta(days=30)
    recent_points = []
    for entry in sorted_entries:
        d = safe_parse_date(entry.get("date", ""))
        if d and d >= cutoff:
            recent_points.append((d, entry.get("weight", 0)))

    if len(recent_points) < 5:
        return {
            "status": "insufficient_data",
            "message": "Need more recent data for prediction",
            "days_remaining": None,
            "predicted_date": None,
            "is_losing": is_losing_goal,
        }

    recent_points.sort(key=lambda x: x[0])
    first_date = recent_points[0][0]
    dates = [(point_date - first_date).days for point_date, _ in recent_points]
    weights = [point_weight for _, point_weight in recent_points]
    
    # Linear regression
    n = len(dates)
    sum_x = sum(dates)
    sum_y = sum(weights)
    sum_xy = sum(x * y for x, y in zip(dates, weights))
    sum_x2 = sum(x * x for x in dates)
    
    denom = n * sum_x2 - sum_x ** 2
    if denom == 0:
        return {
            "status": "no_trend",
            "message": "Weight is stable - adjust habits to make progress",
            "days_remaining": None,
            "predicted_date": None,
        }
    
    slope = (n * sum_xy - sum_x * sum_y) / denom  # kg per day
    
    # Check if trend is in the right direction
    if is_losing_goal and slope >= 0:
        return {
            "status": "wrong_direction",
            "message": "Currently gaining weight - reverse the trend to reach goal",
            "rate_per_week": slope * 7 * 1000,  # grams per week
            "days_remaining": None,
            "predicted_date": None,
            "is_losing": True,
        }
    elif not is_losing_goal and slope <= 0:
        return {
            "status": "wrong_direction",
            "message": "Currently losing weight - reverse the trend to reach goal",
            "rate_per_week": slope * 7 * 1000,  # grams per week
            "days_remaining": None,
            "predicted_date": None,
            "is_losing": False,
        }
    
    # Calculate days to goal
    weight_diff = abs(current_weight - goal_weight)
    days_to_goal = int(weight_diff / abs(slope))
    
    # Cap at 2 years for sanity
    if days_to_goal > 730:
        action = "lose" if is_losing_goal else "gain"
        projection_base = max(datetime.now(), latest_entry_date)
        return {
            "status": "long_term",
            "message": f"At current pace: {days_to_goal // 30} months (try to {action} faster!)",
            "rate_per_week": abs(slope) * 7 * 1000,  # grams per week
            "days_remaining": days_to_goal,
            "predicted_date": projection_base + timedelta(days=days_to_goal),
            "is_losing": is_losing_goal,
        }
    
    projection_base = max(datetime.now(), latest_entry_date)
    predicted_date = projection_base + timedelta(days=days_to_goal)
    weeks = days_to_goal // 7
    
    return {
        "status": "on_track",
        "message": f"đźŽŻ Goal in ~{weeks} weeks ({predicted_date.strftime('%b %d, %Y')})",
        "rate_per_week": abs(slope) * 7 * 1000,  # grams per week
        "days_remaining": days_to_goal,
        "predicted_date": predicted_date,
        "is_losing": is_losing_goal,
    }


def get_historical_comparisons(weight_entries: list, current_date: str = None, 
                                current_context: str = None) -> dict:
    """
    Get weight comparisons vs historical dates.
    
    When a context is provided, prioritizes comparing to entries with the same
    context (e.g., morning vs morning, evening vs evening). Falls back to any
    entry if no same-context entry exists for a period.
    
    Args:
        weight_entries: List of weight entries
        current_date: Reference date (defaults to today)
        current_context: Context/note tag to prioritize (e.g., "morning", "evening")
    
    Returns:
        Dict with comparisons, including context info
    """
    from datetime import datetime, timedelta
    
    if not weight_entries:
        return {}
    
    if current_date is None:
        current_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        today = datetime.strptime(current_date, "%Y-%m-%d")
    except ValueError:
        today = datetime.now()
    
    sorted_entries = sorted(
        [e for e in weight_entries if e.get("date") and e.get("weight") is not None],
        key=lambda x: x["date"],
        reverse=True
    )
    
    if not sorted_entries:
        return {}
    
    # Find current weight - prefer same context entry for current_date if available
    current_weight = None
    current_date_str = today.strftime("%Y-%m-%d")
    
    # First try to find same-context entry for today
    if current_context:
        for entry in sorted_entries:
            if entry["date"] == current_date_str and entry.get("note", "") == current_context:
                current_weight = entry["weight"]
                break
    
    # Fall back to any today entry, then latest
    if current_weight is None:
        for entry in sorted_entries:
            if entry["date"] == current_date_str:
                current_weight = entry["weight"]
                break
    if current_weight is None:
        current_weight = sorted_entries[0]["weight"]
    
    comparisons = {}
    periods = [
        ("1_week", 7, "1 week ago"),
        ("2_weeks", 14, "2 weeks ago"),
        ("1_month", 30, "1 month ago"),
        ("3_months", 90, "3 months ago"),
        ("6_months", 180, "6 months ago"),
        ("1_year", 365, "1 year ago"),
    ]
    
    for key, days, label in periods:
        target_date = today - timedelta(days=days)
        
        # Find closest entry to target date, preferring same context
        closest_entry = None
        closest_same_context = None
        min_diff = float('inf')
        min_diff_same = float('inf')
        
        for entry in sorted_entries:
            try:
                entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")
                diff = abs((entry_date - target_date).days)
                if diff <= 7:  # Within a week of target
                    # Track closest overall
                    if diff < min_diff:
                        min_diff = diff
                        closest_entry = entry
                    
                    # Track closest with same context
                    if current_context and entry.get("note", "") == current_context:
                        if diff < min_diff_same:
                            min_diff_same = diff
                            closest_same_context = entry
            except ValueError:
                continue
        
        # Prefer same-context entry if available
        best_entry = closest_same_context if closest_same_context else closest_entry
        
        if best_entry:
            change = current_weight - best_entry["weight"]
            entry_weight = best_entry.get("weight") or 0
            entry_context = best_entry.get("note", "")
            
            # Add context indicator to label if comparing different contexts
            context_match = (current_context == entry_context) if current_context else True
            display_label = label
            if current_context and not context_match and entry_context:
                # Format the entry context for display
                display_label = f"{label} ({format_entry_note(entry_context)})"
            elif current_context and context_match and entry_context:
                display_label = f"{label} (same context)"
            
            comparisons[key] = {
                "label": display_label,
                "date": best_entry["date"],
                "weight": best_entry["weight"],
                "change": change,
                "change_pct": (change / entry_weight) * 100 if entry_weight else 0,
                "context": entry_context,
                "context_match": context_match,
            }
    
    return comparisons


def get_weekly_insights(weight_entries: list, achieved_milestones: list,
                        current_streak: int, goal: float = None) -> dict:
    """
    Generate weekly insights summary.
    
    Args:
        weight_entries: List of weight entries
        achieved_milestones: List of achieved milestone IDs
        current_streak: Current logging streak
        goal: Goal weight (optional)
    
    Returns:
        Dict with insights data
    """
    from datetime import datetime, timedelta
    
    if not weight_entries:
        return {
            "has_data": False,
            "message": "Start logging to see weekly insights!",
        }
    
    today = datetime.now()
    week_start = today - timedelta(days=7)
    
    sorted_entries = sorted(
        [e for e in weight_entries if e.get("date") and e.get("weight") is not None],
        key=lambda x: x["date"]
    )
    
    # Get this week's entries
    this_week_entries = []
    for entry in sorted_entries:
        try:
            entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")
            if entry_date >= week_start:
                this_week_entries.append(entry)
        except ValueError:
            continue
    
    if not this_week_entries:
        return {
            "has_data": False,
            "message": "No entries this week yet. Log your weight!",
        }
    
    # Calculate weekly stats
    week_weights = [e["weight"] for e in this_week_entries]
    week_avg = sum(week_weights) / len(week_weights)
    week_min = min(week_weights)
    week_max = max(week_weights)
    
    # Compare to previous week
    prev_week_start = week_start - timedelta(days=7)
    prev_week_entries = []
    for entry in sorted_entries:
        try:
            entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")
            if prev_week_start <= entry_date < week_start:
                prev_week_entries.append(entry)
        except ValueError:
            continue
    
    week_change = None
    if prev_week_entries:
        prev_avg = sum(e["weight"] for e in prev_week_entries) / len(prev_week_entries)
        week_change = week_avg - prev_avg
    
    # Progress towards goal
    goal_progress = None
    if goal and sorted_entries:
        starting_weight = sorted_entries[0]["weight"]
        current_weight = sorted_entries[-1]["weight"]
        total_change_needed = abs(starting_weight - goal)
        change_so_far = abs(starting_weight - current_weight)
        
        # Check if moving in right direction
        if total_change_needed > 0.1:  # Avoid division by near-zero
            if starting_weight > goal:
                # Weight loss goal
                if current_weight <= starting_weight:
                    goal_progress = (change_so_far / total_change_needed) * 100
            else:
                # Weight gain goal
                if current_weight >= starting_weight:
                    goal_progress = (change_so_far / total_change_needed) * 100
    
    # Generate insights
    insights = []
    
    if len(this_week_entries) == 7:
        insights.append("đźŚź Perfect week! Logged every day!")
    elif len(this_week_entries) >= 5:
        insights.append(f"đź‘Ť Great consistency! {len(this_week_entries)}/7 days logged")
    
    if week_change is not None:
        if week_change < -0.5:
            insights.append(f"đź“‰ Excellent! Down {abs(week_change)*1000:.0f}g from last week")
        elif week_change < 0:
            insights.append(f"đź“‰ Good progress! Down {abs(week_change)*1000:.0f}g")
        elif week_change < 0.2:
            insights.append("âžˇď¸Ź Weight stable this week")
        else:
            insights.append(f"đź“ Up {week_change*1000:.0f}g - let's refocus!")
    
    if current_streak >= 7:
        insights.append(f"đź”Ą {current_streak}-day logging streak!")
    
    if goal_progress is not None:
        if goal_progress >= 100:
            insights.append("đźŽ‰ GOAL ACHIEVED!")
        elif goal_progress >= 75:
            insights.append(f"đźŹ† {goal_progress:.0f}% to goal - almost there!")
        elif goal_progress >= 50:
            insights.append(f"đź’Ş {goal_progress:.0f}% to goal - halfway!")
        elif goal_progress > 0:
            insights.append(f"đź“Š {goal_progress:.0f}% progress towards goal")
    
    return {
        "has_data": True,
        "entries_count": len(this_week_entries),
        "average": week_avg,
        "min": week_min,
        "max": week_max,
        "variability": week_max - week_min,
        "change_from_last_week": week_change,
        "goal_progress_pct": goal_progress,
        "streak": current_streak,
        "insights": insights,
    }


# Entry note tags
WEIGHT_ENTRY_TAGS = [
    ("morning", "\U0001F305 Morning", "First thing after waking"),
    ("evening", "\U0001F319 Evening", "End of day"),
    ("post_workout", "\U0001F4AA Post-workout", "After exercise"),
    ("fasted", "\u23F1\uFE0F Fasted", "Before eating"),
    ("post_meal", "\U0001F37D\uFE0F Post-meal", "After eating"),
]


def format_entry_note(note: str) -> str:
    """Format entry note with tag emoji if it matches a known tag."""
    if not note:
        return ""
    
    note_lower = note.lower().strip()
    for tag_id, tag_display, _ in WEIGHT_ENTRY_TAGS:
        # Match by tag_id (e.g., "morning") or by display text without emoji
        display_text = tag_display.split(" ", 1)[-1].lower() if " " in tag_display else tag_display.lower()
        if note_lower == tag_id.lower() or note_lower == display_text:
            return tag_display
    
    return note


# ============================================================================
# PHYSICAL ACTIVITY TRACKING: GAMIFIED EXERCISE REWARDS
# ============================================================================

# Activity types with base intensity multipliers
# (activity_id, display_name, emoji, base_intensity)
# base_intensity: 1.0 = low, 1.5 = moderate, 2.0 = high, 2.5 = very high
ACTIVITY_TYPES = [
    ("walking", "Walking", "đźš¶", 1.0),
    ("jogging", "Jogging", "đźŹ", 1.5),
    ("running", "Running", "đźŹâ€Ťâ™‚ď¸Ź", 2.0),
    ("cycling", "Cycling", "đźš´", 1.5),
    ("swimming", "Swimming", "đźŹŠ", 2.0),
    ("hiking", "Hiking", "đźĄľ", 1.5),
    ("strength", "Strength Training", "đźŹ‹ď¸Ź", 2.0),
    ("yoga", "Yoga", "đź§", 1.0),
    ("dance", "Dancing", "đź’", 1.5),
    ("sports", "Sports (General)", "âš˝", 1.8),
    ("hiit", "HIIT", "đź”Ą", 2.5),
    ("climbing", "Climbing", "đź§—", 2.0),
    ("martial_arts", "Martial Arts", "đźĄ‹", 2.0),
    ("stretching", "Stretching", "đź¤¸", 0.8),
    ("other", "Other Activity", "đźŽŻ", 1.0),
]

# Intensity levels that user can select
# (intensity_id, display_name, multiplier)
INTENSITY_LEVELS = [
    ("light", "Light", 0.8),
    ("moderate", "Moderate", 1.0),
    ("vigorous", "Vigorous", 1.3),
    ("intense", "Intense", 1.6),
]

# Minimum duration for rewards (in minutes)
ACTIVITY_MIN_DURATION = 10

# Reward thresholds based on effective minutes (duration * activity_intensity * user_intensity)
# Effective minutes = duration * base_intensity * intensity_multiplier
# Threshold 8 ensures 10min light walk (10 * 1.0 * 0.8 = 8) earns at least Common
ACTIVITY_REWARD_THRESHOLDS = [
    (8, "Common"),       # 8+ effective minutes (e.g., 10 min light walk)
    (20, "Uncommon"),    # 20+ effective minutes
    (40, "Rare"),        # 40+ effective minutes
    (70, "Epic"),        # 70+ effective minutes
    (120, "Legendary"),  # 120+ effective minutes (e.g., 1hr intense workout)
]

# Streak thresholds for activity (consecutive days with any activity)
ACTIVITY_STREAK_THRESHOLDS = [
    (3, "Uncommon", "3-day streak"),
    (7, "Rare", "7-day streak"),
    (14, "Epic", "14-day streak"),
    (30, "Legendary", "30-day streak"),
    (60, "Legendary", "60-day streak"),
    (90, "Legendary", "90-day streak"),
]

# Milestones for activity tracking
ACTIVITY_MILESTONES = [
    {"id": "first_activity", "name": "First Workout", "description": "Log your first activity", 
     "check": "first_entry", "rarity": "Uncommon"},
    {"id": "total_1hr", "name": "Hour Hero", "description": "1 hour total activity time",
     "check": "total_minutes", "threshold": 60, "rarity": "Uncommon"},
    {"id": "total_5hr", "name": "Endurance Builder", "description": "5 hours total activity time",
     "check": "total_minutes", "threshold": 300, "rarity": "Rare"},
    {"id": "total_10hr", "name": "Fitness Warrior", "description": "10 hours total activity time",
     "check": "total_minutes", "threshold": 600, "rarity": "Rare"},
    {"id": "total_25hr", "name": "Iron Will", "description": "25 hours total activity time",
     "check": "total_minutes", "threshold": 1500, "rarity": "Epic"},
    {"id": "total_50hr", "name": "Athletic Legend", "description": "50 hours total activity time",
     "check": "total_minutes", "threshold": 3000, "rarity": "Legendary"},
    {"id": "variety_3", "name": "Explorer", "description": "Try 3 different activity types",
     "check": "activity_variety", "threshold": 3, "rarity": "Uncommon"},
    {"id": "variety_5", "name": "Versatile Athlete", "description": "Try 5 different activity types",
     "check": "activity_variety", "threshold": 5, "rarity": "Rare"},
    {"id": "variety_8", "name": "All-Rounder", "description": "Try 8 different activity types",
     "check": "activity_variety", "threshold": 8, "rarity": "Epic"},
    {"id": "intense_session", "name": "Beast Mode", "description": "Complete a 60+ min intense workout",
     "check": "single_intense", "threshold": 60, "rarity": "Epic"},
]


def get_activity_type(activity_id: str) -> Optional[tuple]:
    """Get activity type tuple by ID."""
    for activity in ACTIVITY_TYPES:
        if activity[0] == activity_id:
            return activity
    return None


def get_intensity_level(intensity_id: str) -> Optional[tuple]:
    """Get intensity level tuple by ID."""
    for intensity in INTENSITY_LEVELS:
        if intensity[0] == intensity_id:
            return intensity
    return None


def calculate_effective_minutes(duration_minutes: int, activity_id: str, 
                                intensity_id: str) -> float:
    """
    Calculate effective minutes based on duration, activity type, and intensity.
    
    Args:
        duration_minutes: Actual duration in minutes
        activity_id: Activity type ID
        intensity_id: Intensity level ID
    
    Returns:
        Effective minutes (duration * activity_base * intensity_multiplier)
    """
    activity = get_activity_type(activity_id)
    intensity = get_intensity_level(intensity_id)
    
    base_intensity = activity[3] if activity else 1.0
    intensity_mult = intensity[2] if intensity else 1.0
    
    return duration_minutes * base_intensity * intensity_mult


def get_activity_reward_rarity(
    effective_minutes: float,
    adhd_buster: Optional[dict] = None,
) -> Optional[str]:
    """
    Get reward rarity based on effective minutes using moving window distribution.

    The window [5%, 15%, 60%, 15%, 5%] shifts through rarity tiers based on effort.
    Overflow at edges is absorbed by the edge tier.

    Args:
        effective_minutes: Calculated effective minutes

    Returns:
        Rarity string or None if below threshold
    """
    outcome = roll_activity_reward_outcome(effective_minutes, adhd_buster=adhd_buster)
    return outcome.get("rarity") if outcome else None


def get_activity_reward_weights(effective_minutes: float) -> Optional[list]:
    """Get activity reward weights for a given effective-minute score."""
    if effective_minutes < 8:
        return None

    rarities = get_standard_reward_rarity_order()
    if effective_minutes >= 120:
        weights = [0] * len(rarities)
        if weights:
            weights[-1] = 100
        return weights

    if effective_minutes >= 100:
        center_tier = 5
    elif effective_minutes >= 70:
        center_tier = 4
    elif effective_minutes >= 40:
        center_tier = 3
    elif effective_minutes >= 20:
        center_tier = 2
    else:
        center_tier = 1

    base_weights = [5, 15, 60, 15, 5]
    weights = [0] * len(rarities)
    for offset, weight in enumerate(base_weights):
        tier = center_tier - 2 + offset
        if tier < 1:
            weights[0] += weight
        elif tier > len(rarities):
            weights[-1] += weight
        else:
            weights[tier - 1] += weight
    return weights


def roll_activity_reward_outcome(
    effective_minutes: float,
    roll: Optional[float] = None,
    adhd_buster: Optional[dict] = None,
) -> Optional[dict]:
    """
    Canonical backend roll for activity reward rarity.

    The slider's final position maps directly to this roll (0..100).
    """
    weights = get_activity_reward_weights(effective_minutes)
    if not weights:
        return None

    rarities = get_standard_reward_rarity_order()
    total = sum(weights)
    if total <= 0:
        return None

    gated_outcome = evaluate_power_gated_rarity_roll(
        rarities,
        weights,
        adhd_buster=adhd_buster,
        roll=roll,
    )

    return {
        "rarity": gated_outcome.get("rarity", rarities[0]),
        "roll": gated_outcome.get("roll", 0.0),
        "weights": weights,
        "rarities": rarities,
        "power_gating": gated_outcome,
    }


def check_activity_streak(activity_entries: list) -> int:
    """
    Calculate current activity streak (consecutive days with activity).
    
    Weekend tolerance: Not logging on Saturday/Sunday doesn't break the streak.
    If you exercise Friday and Monday, the streak continues.
    Logging on weekends still counts toward the streak.
    
    Args:
        activity_entries: List of activity entries with date field
    
    Returns:
        Current streak count
    """
    from datetime import datetime, timedelta
    
    if not activity_entries:
        return 0
    
    # Get unique dates with activity
    dates = set()
    for entry in activity_entries:
        if entry.get("date"):
            dates.add(entry["date"])
    
    if not dates:
        return 0
    
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today_dt = datetime.now()
    yesterday_dt = today_dt - timedelta(days=1)
    
    # Find the most recent valid entry point
    if today in dates:
        current = datetime.strptime(today, "%Y-%m-%d")
        streak = 1
    elif yesterday in dates:
        current = datetime.strptime(yesterday, "%Y-%m-%d")
        streak = 1
    elif _is_weekend(today_dt):
        # It's weekend and no entry today/yesterday - check if Friday had entry
        days_to_friday = (today_dt.weekday() - 4) % 7
        if days_to_friday == 0:
            days_to_friday = 7
        last_friday = today_dt - timedelta(days=days_to_friday)
        friday_str = last_friday.strftime("%Y-%m-%d")
        if friday_str in dates:
            current = last_friday
            streak = 1
        else:
            return 0
    else:
        return 0
    
    # Count backwards from current, skipping weekends if needed
    while True:
        prev_date, prev_str, _ = _get_previous_required_day(current, dates)
        if prev_str in dates:
            streak += 1
            current = prev_date
        else:
            break
    
    return streak


def check_activity_entry_reward(duration_minutes: int, activity_id: str,
                                 intensity_id: str, story_id: str = None,
                                 adhd_buster: Optional[dict] = None) -> dict:
    """
    Check what reward an activity entry earns.
    
    Args:
        duration_minutes: Duration of activity
        activity_id: Type of activity
        intensity_id: Intensity level
        story_id: Story theme for item generation
    
    Returns:
        Dict with reward info
    """
    result = {
        "reward": None,
        "effective_minutes": 0,
        "rarity": None,
        "rarity_roll": None,
        "rarity_weights": None,
        "power_gating": None,
        "messages": [],
    }
    
    if duration_minutes < ACTIVITY_MIN_DURATION:
        result["messages"].append(
            f"âŹ±ď¸Ź Need at least {ACTIVITY_MIN_DURATION} minutes for rewards. "
            f"You logged {duration_minutes} min."
        )
        return result
    
    effective = calculate_effective_minutes(duration_minutes, activity_id, intensity_id)
    result["effective_minutes"] = effective
    
    activity_outcome = roll_activity_reward_outcome(effective, adhd_buster=adhd_buster)
    rarity = activity_outcome.get("rarity") if activity_outcome else None
    result["rarity"] = rarity
    result["rarity_roll"] = activity_outcome.get("roll") if activity_outcome else None
    result["rarity_weights"] = activity_outcome.get("weights") if activity_outcome else None
    result["power_gating"] = activity_outcome.get("power_gating") if activity_outcome else None
    
    if rarity:
        result["reward"] = generate_item(rarity=rarity, story_id=story_id)
        
        activity = get_activity_type(activity_id)
        activity_name = activity[1] if activity else "Activity"
        activity_emoji = activity[2] if activity else "đźŽŻ"
        
        intensity = get_intensity_level(intensity_id)
        intensity_name = intensity[1] if intensity else "Moderate"
        
        result["messages"].append(
            f"{activity_emoji} {duration_minutes} min {intensity_name.lower()} {activity_name.lower()}! "
            f"Earned a {rarity} item!"
        )
        gating = result.get("power_gating") or {}
        if gating.get("downgraded"):
            message = gating.get("message") or (
                f"Tier gated by power. Current cap: {gating.get('max_unlocked_rarity', 'Unknown')}."
            )
            result["messages"].append(f"đź”’ {message}")
    else:
        # Activity logged but didn't earn reward (very low effective minutes)
        activity = get_activity_type(activity_id)
        activity_emoji = activity[2] if activity else "đźŽŻ"
        result["messages"].append(
            f"{activity_emoji} Activity logged! ({effective:.0f} effective min - need 8+ for item rewards)"
        )
    
    return result


def check_activity_streak_reward(
    activity_entries: list,
    achieved_milestones: list,
    story_id: str = None,
    adhd_buster: Optional[dict] = None,
) -> Optional[dict]:
    """
    Check if current streak earns a milestone reward.
    
    Args:
        activity_entries: List of activity entries
        achieved_milestones: Already achieved milestone IDs
        story_id: Story theme
    
    Returns:
        Reward dict or None
    """
    streak = check_activity_streak(activity_entries)
    
    for days, rarity, name in ACTIVITY_STREAK_THRESHOLDS:
        milestone_id = f"activity_streak_{days}"
        if streak >= days and milestone_id not in achieved_milestones:
            gate_result = resolve_power_gated_reward_rarity(rarity, adhd_buster=adhd_buster)
            final_rarity = gate_result.get("rarity", rarity)
            power_gating = gate_result.get("power_gating")
            lock_message = get_power_gate_downgrade_message(power_gating)
            return {
                "milestone_id": milestone_id,
                "streak_days": days,
                "name": name,
                "requested_rarity": rarity,
                "rarity": final_rarity,
                "power_gating": power_gating,
                "item": generate_item(rarity=final_rarity, story_id=story_id),
                "message": (
                    f"đź”Ą {days}-day activity streak! Earned a {final_rarity} item!"
                    + (f" 🔒 {lock_message}" if lock_message else "")
                ),
            }
    
    return None


def check_activity_milestones(
    activity_entries: list,
    achieved_milestones: list,
    story_id: str = None,
    adhd_buster: Optional[dict] = None,
) -> list:
    """
    Check for newly achieved activity milestones.
    
    Args:
        activity_entries: List of activity entries
        achieved_milestones: Already achieved milestone IDs
        story_id: Story theme
    
    Returns:
        List of newly achieved milestones with rewards
    """
    new_milestones = []
    
    if not activity_entries:
        return new_milestones
    
    # Calculate stats for milestone checks
    total_minutes = sum(e.get("duration", 0) for e in activity_entries)
    activity_types_used = set(e.get("activity_type") for e in activity_entries if e.get("activity_type"))
    
    for milestone in ACTIVITY_MILESTONES:
        mid = milestone["id"]
        if mid in achieved_milestones:
            continue
        
        achieved = False
        check = milestone.get("check")
        
        if check == "first_entry":
            achieved = len(activity_entries) >= 1
        
        elif check == "total_minutes":
            achieved = total_minutes >= milestone.get("threshold", 0)
        
        elif check == "activity_variety":
            achieved = len(activity_types_used) >= milestone.get("threshold", 0)
        
        elif check == "single_intense":
            # Check if any single entry is intense enough
            threshold = milestone.get("threshold", 60)
            for entry in activity_entries:
                if entry.get("intensity") in ("vigorous", "intense"):
                    if entry.get("duration", 0) >= threshold:
                        achieved = True
                        break
        
        if achieved:
            requested_rarity = milestone["rarity"]
            gate_result = resolve_power_gated_reward_rarity(
                requested_rarity,
                adhd_buster=adhd_buster,
            )
            final_rarity = gate_result.get("rarity", requested_rarity)
            power_gating = gate_result.get("power_gating")
            lock_message = get_power_gate_downgrade_message(power_gating)
            new_milestones.append({
                "milestone_id": mid,
                "name": milestone["name"],
                "description": milestone["description"],
                "requested_rarity": requested_rarity,
                "rarity": final_rarity,
                "power_gating": power_gating,
                "item": generate_item(rarity=final_rarity, story_id=story_id),
                "message": (
                    f"đźŹ† {milestone['name']}! {milestone['description']}"
                    + (f" Reward: {final_rarity}." if final_rarity else "")
                    + (f" 🔒 {lock_message}" if lock_message else "")
                ),
            })
    
    return new_milestones


def check_all_activity_rewards(activity_entries: list, duration_minutes: int,
                                activity_id: str, intensity_id: str, 
                                current_date: str, achieved_milestones: list,
                                story_id: str = None,
                                adhd_buster: Optional[dict] = None) -> dict:
    """
    Comprehensive check for all activity-related rewards.
    
    Args:
        activity_entries: Existing entries (WITHOUT the new entry)
        duration_minutes: New activity duration
        activity_id: Activity type
        intensity_id: Intensity level
        current_date: Today's date
        achieved_milestones: Already achieved milestone IDs
        story_id: Story theme
    
    Returns:
        Dict with all reward information
    """
    # Get base reward for this activity
    base_rewards = check_activity_entry_reward(
        duration_minutes,
        activity_id,
        intensity_id,
        story_id,
        adhd_buster=adhd_buster,
    )
    
    # Create temp entries list including new entry for streak/milestone checks
    new_entry = {
        "date": current_date,
        "duration": duration_minutes,
        "activity_type": activity_id,
        "intensity": intensity_id,
    }
    temp_entries = activity_entries + [new_entry]
    
    # Check streak rewards
    streak_reward = check_activity_streak_reward(
        temp_entries,
        achieved_milestones,
        story_id,
        adhd_buster=adhd_buster,
    )
    
    # Check milestone achievements
    new_milestones = check_activity_milestones(
        temp_entries,
        achieved_milestones,
        story_id,
        adhd_buster=adhd_buster,
    )
    
    # Compile all results
    result = {
        **base_rewards,
        "streak_reward": streak_reward,
        "new_milestones": new_milestones,
        "current_streak": check_activity_streak(temp_entries),
    }
    
    # Add streak message
    if streak_reward:
        result["messages"].append(streak_reward["message"])
    
    # Add milestone messages
    for milestone in new_milestones:
        result["messages"].append(milestone["message"])
    
    return result


def get_activity_stats(activity_entries: list) -> dict:
    """
    Calculate activity statistics for display.
    
    Args:
        activity_entries: List of activity entries
    
    Returns:
        Dict with stats
    """
    from datetime import datetime, timedelta
    
    if not activity_entries:
        return {
            "total_minutes": 0,
            "total_sessions": 0,
            "this_week_minutes": 0,
            "this_month_minutes": 0,
            "favorite_activity": None,
            "avg_duration": 0,
            "current_streak": 0,
        }
    
    total_minutes = sum(e.get("duration", 0) for e in activity_entries)
    total_sessions = len(activity_entries)
    
    # This week / month
    today = datetime.now()
    week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    
    this_week = sum(e.get("duration", 0) for e in activity_entries 
                    if e.get("date", "") >= week_ago)
    this_month = sum(e.get("duration", 0) for e in activity_entries 
                     if e.get("date", "") >= month_ago)
    
    # Favorite activity
    activity_counts = {}
    for entry in activity_entries:
        a_type = entry.get("activity_type", "other")
        activity_counts[a_type] = activity_counts.get(a_type, 0) + 1
    
    favorite = max(activity_counts.items(), key=lambda x: x[1])[0] if activity_counts else None
    
    return {
        "total_minutes": total_minutes,
        "total_sessions": total_sessions,
        "this_week_minutes": this_week,
        "this_month_minutes": this_month,
        "favorite_activity": favorite,
        "avg_duration": total_minutes / total_sessions if total_sessions else 0,
        "current_streak": check_activity_streak(activity_entries),
    }


def format_activity_duration(minutes: int) -> str:
    """Format minutes as hours and minutes string."""
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"


# ============================================================================
# SLEEP TRACKING: GAMIFIED SLEEP HEALTH
# ============================================================================
# Based on scientific sleep recommendations:
# - Adults need 7-9 hours (National Sleep Foundation)
# - Optimal bedtime before midnight for circadian health
# - Consistent sleep schedule improves quality
# - Chronotype affects optimal sleep windows

# Chronotypes with recommended sleep windows
# (chronotype_id, display_name, emoji, optimal_bedtime_start, optimal_bedtime_end, description)
SLEEP_CHRONOTYPES = [
    ("early_bird", "Early Bird (Lark)", "đźŚ…", "21:00", "22:30", 
     "Naturally wake early. Optimal bedtime: 9-10:30 PM"),
    ("moderate", "Moderate", "âŹ°", "22:00", "23:30", 
     "Balanced schedule. Optimal bedtime: 10-11:30 PM"),
    ("night_owl", "Night Owl", "đź¦‰", "23:00", "00:30", 
     "Naturally stay up late. Optimal bedtime: 11 PM-12:30 AM"),
]

# Sleep quality factors user can report
# (quality_id, display_name, emoji, score_multiplier)
SLEEP_QUALITY_FACTORS = [
    ("excellent", "Excellent", "đź´đź’¤", 1.3),
    ("good", "Good", "đźŠ", 1.1),
    ("fair", "Fair", "đź", 1.0),
    ("poor", "Poor", "đź“", 0.8),
    ("terrible", "Terrible", "đźµ", 0.6),
]

# Sleep disruption tags
# (tag_id, display_name, emoji, impact)
SLEEP_DISRUPTION_TAGS = [
    ("none", "No disruptions", "âś…", 0),
    ("woke_once", "Woke once", "1ď¸ŹâŁ", -5),
    ("woke_multiple", "Woke multiple times", "đź”„", -15),
    ("nightmares", "Bad dreams", "đź°", -10),
    ("noise", "Noise disruption", "đź”Š", -10),
    ("stress", "Stress/anxiety", "đźź", -15),
    ("late_caffeine", "Late caffeine", "â•", -10),
    ("late_screen", "Late screen time", "đź“±", -10),
    ("alcohol", "Alcohol", "đźŤ·", -15),
]

# Recommended sleep duration by age (hours)
# Adults 18-64: 7-9 hours, 65+: 7-8 hours
SLEEP_DURATION_TARGETS = {
    "minimum": 7.0,     # Below this = sleep deprived
    "optimal_low": 7.5,  # Start of optimal range
    "optimal_high": 9.0, # End of optimal range
    "maximum": 10.0,     # Above this may indicate health issues
}

# Base scores for sleep metrics
SLEEP_SCORE_COMPONENTS = {
    "duration_weight": 40,      # 40% of score from duration
    "bedtime_weight": 25,       # 25% from bedtime consistency
    "quality_weight": 25,       # 25% from quality
    "consistency_weight": 10,   # 10% from schedule consistency
}

# Reward thresholds based on sleep score (0-100)
SLEEP_REWARD_THRESHOLDS = [
    (50, "Common"),      # 50+ score
    (65, "Uncommon"),    # 65+ score
    (80, "Rare"),        # 80+ score
    (90, "Epic"),        # 90+ score
    (97, "Legendary"),   # 97+ score (exceptional sleep)
]

# Streak thresholds for sleep (consecutive days with good sleep 7+ hours)
SLEEP_STREAK_THRESHOLDS = [
    (3, "Uncommon", "3-night streak"),
    (7, "Rare", "7-night streak (full week!)"),
    (14, "Epic", "14-night streak"),
    (30, "Legendary", "30-night streak (monthly!)"),
    (60, "Legendary", "60-night streak"),
    (90, "Legendary", "90-night streak (quarterly!)"),
]

# Sleep milestones
SLEEP_MILESTONES = [
    {"id": "first_sleep", "name": "First Log", "description": "Log your first sleep entry",
     "check": "first_entry", "rarity": "Uncommon"},
    {"id": "week_tracked", "name": "Week Tracker", "description": "Track sleep for 7 days",
     "check": "total_entries", "threshold": 7, "rarity": "Uncommon"},
    {"id": "month_tracked", "name": "Month Monitor", "description": "Track sleep for 30 days",
     "check": "total_entries", "threshold": 30, "rarity": "Rare"},
    {"id": "perfect_night", "name": "Perfect Night", "description": "Achieve a 95+ sleep score",
     "check": "single_score", "threshold": 95, "rarity": "Epic"},
    {"id": "early_bedtime_5", "name": "Early Riser", "description": "5 nights in bed before your optimal time",
     "check": "early_bedtime_count", "threshold": 5, "rarity": "Uncommon"},
    {"id": "consistent_week", "name": "Clockwork", "description": "Same bedtime (Â±30min) for 7 days",
     "check": "consistent_week", "rarity": "Rare"},
    {"id": "quality_streak_7", "name": "Quality Sleeper", "description": "7 days of Good or better quality",
     "check": "quality_streak", "threshold": 7, "rarity": "Rare"},
    {"id": "total_100hr", "name": "Century Sleeper", "description": "100 hours of tracked sleep",
     "check": "total_hours", "threshold": 100, "rarity": "Rare"},
    {"id": "total_500hr", "name": "Sleep Master", "description": "500 hours of tracked sleep",
     "check": "total_hours", "threshold": 500, "rarity": "Epic"},
    {"id": "total_1000hr", "name": "Dream Legend", "description": "1000 hours of tracked sleep",
     "check": "total_hours", "threshold": 1000, "rarity": "Legendary"},
]


def get_chronotype(chronotype_id: str) -> Optional[tuple]:
    """Get chronotype tuple by ID."""
    for chrono in SLEEP_CHRONOTYPES:
        if chrono[0] == chronotype_id:
            return chrono
    return None


def get_sleep_quality(quality_id: str) -> Optional[tuple]:
    """Get sleep quality tuple by ID."""
    for quality in SLEEP_QUALITY_FACTORS:
        if quality[0] == quality_id:
            return quality
    return None


def get_disruption_tag(tag_id: str) -> Optional[tuple]:
    """Get disruption tag tuple by ID."""
    for tag in SLEEP_DISRUPTION_TAGS:
        if tag[0] == tag_id:
            return tag
    return None


def time_to_minutes(time_str: str) -> int:
    """Convert HH:MM time string to minutes since midnight."""
    try:
        h, m = time_str.split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return 0


def minutes_to_time(minutes: int) -> str:
    """Convert minutes since midnight to HH:MM format."""
    minutes = minutes % (24 * 60)  # Wrap around
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def calculate_bedtime_score(bedtime: str, chronotype_id: str) -> tuple:
    """
    Calculate bedtime score based on how close to optimal window.
    
    Args:
        bedtime: Bedtime in HH:MM format
        chronotype_id: User's chronotype
    
    Returns:
        Tuple of (score 0-100, message)
    """
    chrono = get_chronotype(chronotype_id)
    if not chrono:
        chrono = SLEEP_CHRONOTYPES[1]  # Default to moderate
    
    optimal_start = time_to_minutes(chrono[3])
    optimal_end = time_to_minutes(chrono[4])
    bedtime_mins = time_to_minutes(bedtime)
    
    # Handle overnight times (after midnight = add 24 hours in logic)
    if optimal_end < optimal_start:  # Crosses midnight
        if bedtime_mins < 12 * 60:  # Bedtime is after midnight
            bedtime_mins += 24 * 60
        optimal_end += 24 * 60
    
    # Perfect if within optimal window
    if optimal_start <= bedtime_mins <= optimal_end:
        return (100, "đźŚź Perfect bedtime!")
    
    # Calculate deviation in minutes
    if bedtime_mins < optimal_start:
        deviation = optimal_start - bedtime_mins
        direction = "early"
    else:
        deviation = bedtime_mins - optimal_end
        direction = "late"
    
    # Deduct points for deviation (10 points per 30 min deviation)
    penalty = min(deviation // 3, 100)  # ~10 points per 30 min
    score = max(0, 100 - penalty)
    
    if deviation <= 30:
        msg = f"đź‘Ť Close to optimal ({deviation}min {direction})"
    elif deviation <= 60:
        msg = f"âš ď¸Ź {deviation}min {direction} - try adjusting"
    else:
        hours = deviation // 60
        mins = deviation % 60
        msg = f"đź´ {hours}h {mins}m {direction} - affects sleep quality"
    
    return (score, msg)


def calculate_duration_score(sleep_hours: float, age: int = None) -> tuple:
    """
    Calculate duration score based on age-appropriate recommended sleep.
    
    Uses AASM guidelines for children/teens, NSF for adults.
    
    Args:
        sleep_hours: Total sleep duration in hours
        age: Age in years (optional, for age-specific targets)
    
    Returns:
        Tuple of (score 0-100, message)
    """
    # Get age-appropriate targets
    targets = get_sleep_targets_for_age(age)
    min_hours = targets["minimum"]
    opt_low = targets["optimal_low"]
    opt_high = targets["optimal_high"]
    max_hours = targets["maximum"]
    
    # Generate age-appropriate recommendation text
    if age is not None and 7 <= age <= 12:
        rec_text = "9-12h"
    elif age is not None and 13 <= age <= 18:
        rec_text = "8-10h"
    elif age is not None and age >= 65:
        rec_text = "7-8h"
    else:
        rec_text = "7-9h"
    
    if opt_low <= sleep_hours <= opt_high:
        return (100, f"đźŚź Perfect! {sleep_hours:.1f}h is optimal ({rec_text} recommended)")
    
    if sleep_hours < min_hours:
        # Sleep deprived - significant penalty
        deficit = min_hours - sleep_hours
        score = max(0, 100 - int(deficit * 20))  # -20 per hour deficit
        return (score, f"đź´ Sleep deprived! {sleep_hours:.1f}h (need {min_hours}+)")
    
    if min_hours <= sleep_hours < opt_low:
        # Slightly under optimal
        return (85, f"đź‘Ť Good ({sleep_hours:.1f}h), aim for {opt_low}+")
    
    if opt_high < sleep_hours <= max_hours:
        # Slightly over optimal (not necessarily bad)
        return (90, f"đź’¤ Long sleep ({sleep_hours:.1f}h) - typically fine")
    
    # Very long sleep - might indicate health issues
    return (70, f"âš ď¸Ź Very long sleep ({sleep_hours:.1f}h) - consult doctor if frequent")


def calculate_sleep_score(sleep_hours: float, bedtime: str, quality_id: str,
                          disruptions: list, chronotype_id: str, age: int = None) -> dict:
    """
    Calculate comprehensive sleep score.
    
    Args:
        sleep_hours: Total sleep duration in hours
        bedtime: Bedtime in HH:MM format
        quality_id: Quality rating ID
        disruptions: List of disruption tag IDs
        chronotype_id: User's chronotype
        age: Age in years (optional, for age-specific duration scoring)
    
    Returns:
        Dict with score breakdown and total
    """
    weights = SLEEP_SCORE_COMPONENTS
    
    # Duration score (40%) - age-adjusted
    dur_score, dur_msg = calculate_duration_score(sleep_hours, age)
    
    # Bedtime score (25%)
    bed_score, bed_msg = calculate_bedtime_score(bedtime, chronotype_id)
    
    # Quality score (25%)
    quality = get_sleep_quality(quality_id)
    quality_mult = quality[3] if quality else 1.0
    quality_base = 80  # Base score
    quality_score = min(100, int(quality_base * quality_mult))
    quality_msg = f"{quality[1]} quality" if quality else "Unknown quality"
    
    # Apply disruption penalties
    disruption_penalty = 0
    disruption_msgs = []
    if disruptions:  # Handle None or empty list
        for tag_id in disruptions:
            tag = get_disruption_tag(tag_id)
            if tag and tag[3] != 0:
                disruption_penalty += abs(tag[3])
                disruption_msgs.append(f"{tag[1]} ({tag[3]})")
    
    quality_score = max(0, quality_score - disruption_penalty)
    
    # Weighted total (note: consistency_weight is applied as a bonus based on history
    # in check_all_sleep_rewards, so base calculation uses 90% of weights)
    # Add 10% base consistency score for single-entry calculations
    consistency_bonus = 10  # Base consistency score (will be adjusted with history)
    total = (
        dur_score * weights["duration_weight"] / 100 +
        bed_score * weights["bedtime_weight"] / 100 +
        quality_score * weights["quality_weight"] / 100 +
        consistency_bonus * weights["consistency_weight"] / 100
    )
    
    return {
        "total_score": int(total),
        "duration_score": dur_score,
        "duration_message": dur_msg,
        "bedtime_score": bed_score,
        "bedtime_message": bed_msg,
        "quality_score": quality_score,
        "quality_message": quality_msg,
        "disruption_penalty": disruption_penalty,
        "disruption_details": disruption_msgs,
    }


def check_sleep_streak(sleep_entries: list) -> int:
    """
    Calculate current sleep streak (consecutive days with 7+ hours sleep).
    
    Weekend tolerance: Not logging on Saturday/Sunday doesn't break the streak.
    Good sleep on Friday followed by Monday continues the streak.
    Logging on weekends still counts toward the streak.
    
    Args:
        sleep_entries: List of sleep entries with date and sleep_hours fields
    
    Returns:
        Current streak count
    """
    from datetime import datetime, timedelta
    
    if not sleep_entries:
        return 0
    
    # Get dates with good sleep (7+ hours)
    good_dates = set()
    for entry in sleep_entries:
        if entry.get("date") and entry.get("sleep_hours", 0) >= 7:
            good_dates.add(entry["date"])
    
    if not good_dates:
        return 0
    
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today_dt = datetime.now()
    yesterday_dt = today_dt - timedelta(days=1)
    
    # Find the most recent valid entry point
    if today in good_dates:
        current = datetime.strptime(today, "%Y-%m-%d")
        streak = 1
    elif yesterday in good_dates:
        current = datetime.strptime(yesterday, "%Y-%m-%d")
        streak = 1
    elif _is_weekend(today_dt):
        # It's weekend and no entry today/yesterday - check if Friday had entry
        days_to_friday = (today_dt.weekday() - 4) % 7
        if days_to_friday == 0:
            days_to_friday = 7
        last_friday = today_dt - timedelta(days=days_to_friday)
        friday_str = last_friday.strftime("%Y-%m-%d")
        if friday_str in good_dates:
            current = last_friday
            streak = 1
        else:
            return 0
    else:
        return 0
    
    # Count backwards from current, skipping weekends if needed
    while True:
        prev_date, prev_str, _ = _get_previous_required_day(current, good_dates)
        if prev_str in good_dates:
            streak += 1
            current = prev_date
        else:
            break
    
    return streak


# =============================================================================
# HYDRATION TRACKING
# =============================================================================

# Constants for hydration tracking
HYDRATION_MIN_INTERVAL_HOURS = 2  # Minimum 2 hours between glasses
HYDRATION_MAX_DAILY_GLASSES = 5  # Maximum 5 glasses per day


def get_hydration_cooldown_minutes(adhd_buster: dict) -> int:
    """
    Get the hydration cooldown in minutes, reduced by entity perks.
    
    Base: 2 hours (120 minutes)
    Entity perks with HYDRATION_COOLDOWN reduce this.
    
    Args:
        adhd_buster: Hero data dict with entitidex progress
        
    Returns:
        Cooldown in minutes (minimum 30 minutes)
    """
    base_minutes = HYDRATION_MIN_INTERVAL_HOURS * 60  # 120 minutes
    
    try:
        from entitidex.entity_perks import calculate_active_perks, PerkType
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        
        # Get cooldown reduction (stored as minutes, e.g., 5 = -5 minutes)
        cooldown_reduction = int(perks.get(PerkType.HYDRATION_COOLDOWN, 0))
            
        # Apply reduction with minimum of 30 minutes
        return max(30, base_minutes - cooldown_reduction)
        
    except Exception as e:
        print(f"[Entity Perks] Error getting hydration cooldown: {e}")
        return base_minutes


def get_hydration_daily_cap(adhd_buster: dict) -> int:
    """
    Get the daily hydration glass cap, increased by entity perks.
    
    Base: 5 glasses per day
    Entity perks with HYDRATION_CAP increase this.
    
    Args:
        adhd_buster: Hero data dict with entitidex progress
        
    Returns:
        Maximum glasses per day
    """
    base_cap = HYDRATION_MAX_DAILY_GLASSES
    
    try:
        from entitidex.entity_perks import calculate_active_perks, PerkType
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        
        # Get cap increase (stored as count, e.g., 1 = +1 glass)
        cap_increase = int(perks.get(PerkType.HYDRATION_CAP, 0))
            
        return base_cap + cap_increase
        
    except Exception as e:
        print(f"[Entity Perks] Error getting hydration cap: {e}")
        return base_cap


def roll_water_reward_outcome(
    glass_number: int,
    success_roll: Optional[float] = None,
    tier_roll: Optional[float] = None,
    adhd_buster: Optional[dict] = None,
) -> dict:
    """
    Canonical water lottery roll (success + tier), used by gameplay and UI.

    Returns:
        dict with keys:
        - base_rarity: str or None
        - success_rate: float
        - rolled_tier: str or None
        - success_roll: float or None
        - tier_roll: float or None
        - weights: list[int]
        - won: bool
    """
    import random

    if glass_number < 1 or glass_number > HYDRATION_MAX_DAILY_GLASSES:
        return {
            "base_rarity": None,
            "success_rate": 0.0,
            "rolled_tier": None,
            "success_roll": None,
            "tier_roll": None,
            "weights": [0, 0, 0, 0, 0],
            "won": False,
        }

    center_tier = glass_number - 1
    success_rates = [0.99, 0.80, 0.60, 0.40, 0.20]
    success_rate = success_rates[min(center_tier, len(success_rates) - 1)]

    tier_names = get_standard_reward_rarity_order()
    center_tier = min(center_tier, len(tier_names) - 1)
    base_rarity = tier_names[center_tier]

    window = [5, 15, 60, 15, 5]
    weights = [0] * len(tier_names)
    for offset, pct in zip([-2, -1, 0, 1, 2], window):
        target_tier = center_tier + offset
        clamped_tier = max(0, min(len(tier_names) - 1, target_tier))
        weights[clamped_tier] += pct

    gated_outcome = evaluate_power_gated_rarity_roll(
        tier_names,
        weights,
        adhd_buster=adhd_buster,
        roll=tier_roll,
    )
    tier_roll = max(0.0, min(100.0, float(gated_outcome.get("roll", 0.0))))
    rolled_tier = gated_outcome.get("rarity", tier_names[-1])

    if success_roll is None:
        success_roll = random.random()
    success_roll = max(0.0, min(1.0, float(success_roll)))
    won = success_roll < success_rate

    return {
        "base_rarity": base_rarity,
        "success_rate": success_rate,
        "rolled_tier": rolled_tier,
        "reward_tier": rolled_tier if won else None,
        "success_roll": success_roll,
        "tier_roll": tier_roll,
        "weights": weights,
        "won": won,
        "power_gating": gated_outcome,
    }


def get_water_reward_rarity(
    glass_number: int,
    success_roll: float = None,
    adhd_buster: Optional[dict] = None,
) -> tuple:
    """
    Get reward rarity for logging a glass of water.
    
    Uses moving window [5%, 15%, 60%, 15%, 5%] with tier increasing each glass:
    - Glass 1: Common-centered, 99% success rate
    - Glass 2: Uncommon-centered, 80% success rate
    - Glass 3: Rare-centered, 60% success rate
    - Glass 4: Epic-centered, 40% success rate
    - Glass 5: Legendary-centered, 20% success rate
    
    Args:
        glass_number: Which glass this is today (1-5)
        success_roll: Pre-rolled success value (0.0-1.0) or None to generate
    
    Returns:
        (base_rarity: str, success_rate: float, rolled_tier: str or None)
        Returns (None, 0.0, None) if over daily limit
    """
    outcome = roll_water_reward_outcome(
        glass_number=glass_number,
        success_roll=success_roll,
        adhd_buster=adhd_buster,
    )
    return (
        outcome["base_rarity"],
        outcome["success_rate"],
        outcome["reward_tier"],
    )


def get_hydration_streak_bonus_rarity(streak_days: int) -> Optional[str]:
    """
    Get bonus reward for hydration streak (hitting 5 glasses daily).
    
    Args:
        streak_days: Consecutive days hitting 5 glasses
    
    Returns:
        Rarity string or None if not a milestone
    """
    if streak_days == 3:
        return "Uncommon"
    elif streak_days == 7:
        return "Rare"
    elif streak_days == 14:
        return "Epic"
    elif streak_days == 30:
        return "Legendary"
    elif streak_days > 0 and streak_days % 30 == 0:
        return "Legendary"  # Every 30 days
    return None


def can_log_water(water_entries: list, current_time: Optional[str] = None, 
                  adhd_buster: Optional[dict] = None) -> dict:
    """
    Check if user can log water based on timing rules.
    
    Args:
        water_entries: List of water log entries
        current_time: Current datetime string (for testing), or None for now
        adhd_buster: Hero data dict for entity perk bonuses (optional)
    
    Returns:
        Dict with can_log, reason, next_available_time, glasses_today, minutes_remaining,
        and perk_bonus_applied (bool) if perks modified the result
    """
    from datetime import datetime, timedelta
    from app_utils import get_activity_date
    
    now = datetime.now()
    if current_time is not None:
        parsed_now = safe_parse_date(current_time, "%Y-%m-%d %H:%M")
        if parsed_now:
            now = parsed_now
    # Use activity date (5 AM cutoff) instead of calendar date
    today = get_activity_date(now)
    
    # Get perk-modified limits (or use defaults if no adhd_buster)
    if adhd_buster:
        daily_cap = get_hydration_daily_cap(adhd_buster)
        cooldown_minutes = get_hydration_cooldown_minutes(adhd_buster)
    else:
        daily_cap = HYDRATION_MAX_DAILY_GLASSES
        cooldown_minutes = HYDRATION_MIN_INTERVAL_HOURS * 60
    
    # Track if perks provided a bonus
    cap_bonus = daily_cap > HYDRATION_MAX_DAILY_GLASSES
    cooldown_bonus = cooldown_minutes < (HYDRATION_MIN_INTERVAL_HOURS * 60)
    
    # Count today's glasses and find last glass time
    today_entries = [e for e in water_entries if isinstance(e, dict) and e.get("date") == today]
    glasses_today = 0
    for entry in today_entries:
        try:
            glasses_today += max(0, int(entry.get("glasses", 1)))
        except (TypeError, ValueError):
            glasses_today += 1
    
    # Check daily limit (using perk-modified cap)
    if glasses_today >= daily_cap:
        reason = f"đźŽŻ Daily goal complete! You've had {daily_cap} glasses today."
        if cap_bonus:
            reason += " âś¨ (Entity perk bonus!)"
        return {
            "can_log": False,
            "reason": reason,
            "next_available_time": None,
            "glasses_today": glasses_today,
            "minutes_remaining": 0,
            "daily_cap": daily_cap,
            "perk_bonus_applied": cap_bonus
        }
    
    # Check timing (using perk-modified cooldown)
    if today_entries:
        last_entry = max(today_entries, key=lambda e: e.get("time", "00:00"))
        last_time_str = last_entry.get("time", "00:00")
        last_time = safe_parse_date(f"{today} {last_time_str}", "%Y-%m-%d %H:%M")
        if last_time:
            next_available = last_time + timedelta(minutes=cooldown_minutes)
            
            if now < next_available:
                minutes_remaining = int((next_available - now).total_seconds() / 60)
                reason = f"âŹł Wait {minutes_remaining} min for healthy absorption."
                if cooldown_bonus:
                    original_remaining = int((last_time + timedelta(hours=HYDRATION_MIN_INTERVAL_HOURS) - now).total_seconds() / 60)
                    saved = original_remaining - minutes_remaining
                    if saved > 0:
                        reason += f" âś¨ (Saved {saved} min from perks!)"
                return {
                    "can_log": False,
                    "reason": reason,
                    "next_available_time": next_available.strftime("%H:%M"),
                    "glasses_today": glasses_today,
                    "minutes_remaining": minutes_remaining,
                    "daily_cap": daily_cap,
                    "perk_bonus_applied": cooldown_bonus
                }
    
    return {
        "can_log": True,
        "reason": "Ready to log!",
        "next_available_time": None,
        "glasses_today": glasses_today,
        "minutes_remaining": 0,
        "daily_cap": daily_cap,
        "perk_bonus_applied": cap_bonus or cooldown_bonus
    }


def check_water_entry_reward(
    glasses_today: int,
    streak_days: int,
    story_id: str = "warrior",
    adhd_buster: Optional[dict] = None,
) -> dict:
    """
    Check all rewards for logging a glass of water.
    
    Args:
        glasses_today: Glasses logged today (before this one)
        streak_days: Current hydration streak (5 glasses/day)
        story_id: Active story for item generation
    
    Returns:
        Dict with reward info and items earned
    """
    new_glass_number = glasses_today + 1
    
    result = {
        "glass_reward": None,
        "streak_bonus": None,
        "items": [],
        "messages": [],
        "glasses_today": new_glass_number,
        "is_complete": new_glass_number >= HYDRATION_MAX_DAILY_GLASSES
    }
    
    # Per-glass reward with escalating rarity
    if new_glass_number <= HYDRATION_MAX_DAILY_GLASSES:
        _, _, rolled_tier = get_water_reward_rarity(
            new_glass_number,
            adhd_buster=adhd_buster,
        )
        if rolled_tier:
            glass_item = generate_item(rarity=rolled_tier, story_id=story_id)
            glass_item["source"] = f"hydration_glass_{new_glass_number}"
            result["glass_reward"] = glass_item
            result["items"].append(glass_item)
            result["messages"].append(f"đź’§ Glass #{new_glass_number} logged!")
            
            if new_glass_number == HYDRATION_MAX_DAILY_GLASSES:
                result["messages"].append("đźŽŻ Daily hydration complete! Great job!")
    
    # Check streak bonus (only when hitting 5 glasses)
    if glasses_today < HYDRATION_MAX_DAILY_GLASSES <= new_glass_number and streak_days > 0:
        streak_rarity = get_hydration_streak_bonus_rarity(streak_days + 1)
        if streak_rarity:
            gate_result = resolve_power_gated_reward_rarity(
                streak_rarity,
                adhd_buster=adhd_buster,
            )
            final_rarity = gate_result.get("rarity", streak_rarity)
            power_gating = gate_result.get("power_gating")
            lock_message = get_power_gate_downgrade_message(power_gating)
            streak_item = generate_item(rarity=final_rarity, story_id=story_id)
            streak_item["source"] = "hydration_streak"
            streak_item["power_gating"] = power_gating
            streak_item["requested_rarity"] = streak_rarity
            result["streak_bonus"] = streak_item
            result["items"].append(streak_item)
            message = f"đź”Ą Hydration streak: {streak_days + 1} days! Earned a {final_rarity} item!"
            if lock_message:
                message = f"{message} 🔒 {lock_message}"
            result["messages"].append(message)
    
    return result


def get_hydration_stats(water_entries: list, daily_goal: int = HYDRATION_MAX_DAILY_GLASSES) -> dict:
    """
    Calculate hydration statistics from water log entries.
    
    Args:
        water_entries: List of water log entries with date and glasses count
        daily_goal: Number of glasses needed to count as "on target"
    
    Returns:
        Dict with hydration statistics
    """
    from datetime import datetime, timedelta
    
    if not water_entries:
        return {
            "total_glasses": 0,
            "total_days": 0,
            "avg_daily": 0.0,
            "days_on_target": 0,
            "target_rate": 0.0,
            "current_streak": 0,
            "best_streak": 0,
            "today_glasses": 0
        }

    try:
        daily_goal = int(daily_goal)
    except (TypeError, ValueError):
        daily_goal = HYDRATION_MAX_DAILY_GLASSES
    daily_goal = max(1, daily_goal)

    from app_utils import get_activity_date
    today = get_activity_date()
    
    # Group by date
    daily_totals = {}
    for entry in water_entries:
        if not isinstance(entry, dict):
            continue
        date = entry.get("date", "")
        if not date:
            continue
        try:
            glasses = max(0, int(entry.get("glasses", 1)))
        except (TypeError, ValueError):
            glasses = 1
        daily_totals[date] = daily_totals.get(date, 0) + glasses
    
    total_glasses = sum(daily_totals.values())
    total_days = len(daily_totals)
    avg_daily = total_glasses / total_days if total_days > 0 else 0.0
    days_on_target = sum(1 for g in daily_totals.values() if g >= daily_goal)
    target_rate = (days_on_target / total_days * 100) if total_days > 0 else 0.0
    today_glasses = daily_totals.get(today, 0)
    
    # Calculate streaks from goal-met days only.
    goal_dates = sorted(d for d, g in daily_totals.items() if g >= daily_goal)
    goal_date_set = set(goal_dates)

    # Current streak: start from today or yesterday only.
    current_streak = 0
    now = datetime.now().date()
    anchor = None
    today_str = now.strftime("%Y-%m-%d")
    yesterday = now - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    if today_str in goal_date_set:
        anchor = now
    elif yesterday_str in goal_date_set:
        anchor = yesterday

    if anchor:
        check_day = anchor
        while check_day.strftime("%Y-%m-%d") in goal_date_set:
            current_streak += 1
            check_day -= timedelta(days=1)

    # Best streak: longest consecutive run across all history.
    best_streak = 0
    streak = 0
    prev_day = None
    for date_str in goal_dates:
        day_dt = safe_parse_date(date_str, "%Y-%m-%d")
        if not day_dt:
            continue
        day = day_dt.date()
        if prev_day is not None and (day - prev_day).days == 1:
            streak += 1
        else:
            streak = 1
        best_streak = max(best_streak, streak)
        prev_day = day
    
    return {
        "total_glasses": total_glasses,
        "total_days": total_days,
        "avg_daily": avg_daily,
        "days_on_target": days_on_target,
        "target_rate": target_rate,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "today_glasses": today_glasses
    }


def is_consecutive_day(date1: str, date2: str) -> bool:
    """Check if date2 is the day before date1."""
    from datetime import datetime, timedelta
    try:
        d1 = datetime.strptime(date1, "%Y-%m-%d")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
        return (d1 - d2).days == 1
    except (ValueError, TypeError):
        return False


def get_screen_off_bonus_weights(screen_off_time: str) -> Optional[list]:
    """
    Get bonus reward weights based on when user turned off their screen.
    
    Returns weights (no random draw) so UI can show accurate odds.
    """
    try:
        h, m = screen_off_time.split(":")
        hour = int(h)
        minute = int(m)
        # Validate hour and minute ranges
        if not (0 <= hour <= 23) or not (0 <= minute <= 59):
            return None
        # Convert to minutes past midnight, treating pre-6am as next day
        if hour < 6:
            total_minutes = (24 + hour) * 60 + minute  # e.g., 01:00 = 25*60
        else:
            total_minutes = hour * 60 + minute
    except (ValueError, AttributeError):
        return None
    
    if total_minutes < 21 * 60:  # Before 21:00
        return None
    elif total_minutes <= 21 * 60 + 30:  # 21:00 to 21:30
        full_top = [0] * len(get_standard_reward_rarity_order())
        full_top[-1] = 100
        return full_top
    elif total_minutes <= 22 * 60 + 30:  # 21:31 to 22:30
        center_tier = 4  # Legendary-centered
    elif total_minutes <= 23 * 60 + 30:  # 22:31 to 23:30
        center_tier = 3  # Epic-centered
    elif total_minutes <= 24 * 60 + 30:  # 23:31 to 00:30
        center_tier = 2  # Rare-centered
    elif total_minutes < 25 * 60:  # 00:31 to 00:59
        center_tier = 1  # Uncommon-centered
    else:  # 01:00 or later
        return None  # Too late for bonus
    
    window = [5, 20, 50, 20, 5]
    rarities = get_standard_reward_rarity_order()
    weights = [0] * len(rarities)
    
    for offset, pct in zip([-2, -1, 0, 1, 2], window):
        target_tier = center_tier + offset
        clamped_tier = max(0, min(len(rarities) - 1, target_tier))
        weights[clamped_tier] += pct
    
    return weights


def get_screen_off_bonus_rarity(
    screen_off_time: str,
    adhd_buster: Optional[dict] = None,
) -> Optional[str]:
    """
    Get bonus reward rarity based on when user turned off their screen.
    
    Uses the same moving window [5%, 20%, 50%, 20%, 5%] pattern.
    Earlier screen-off times give better rewards:
    - 21:00-21:30: 100% Legendary (perfect digital hygiene!)
    - 21:30-22:30: Legendary-centered (75% Legendary)
    - 22:30-23:30: Epic-centered
    - 23:30-00:30: Rare-centered
    - 00:30-01:00: Uncommon-centered
    - 01:00+: No bonus (too late)
    
    Args:
        screen_off_time: Time in HH:MM format when screen was turned off
    
    Returns:
        Rarity string or None if too late for bonus
    """
    weights = get_screen_off_bonus_weights(screen_off_time)
    if not weights:
        return None
    rarities = get_standard_reward_rarity_order()
    gated_outcome = evaluate_power_gated_rarity_roll(
        rarities,
        weights,
        adhd_buster=adhd_buster,
    )
    return gated_outcome.get("rarity")


def get_sleep_reward_rarity(
    score: int,
    adhd_buster: Optional[dict] = None,
) -> Optional[str]:
    """
    Get reward rarity based on sleep score using moving window.
    
    Uses a moving window system where higher sleep scores shift probability
    toward higher rarities:
    - Window pattern: [5%, 20%, 50%, 20%, 5%] centered on a tier
    - Overflow at edges is absorbed by the edge tier
    
    Distribution:
    - <50: No reward
    - 50: Common-centered (75% C, 20% U, 5% R)
    - 65: Uncommon-centered (25% C, 50% U, 20% R, 5% E)
    - 80: Rare-centered (5% C, 20% U, 50% R, 20% E, 5% L)
    - 90: Epic-centered (5% U, 20% R, 50% E, 25% L)
    - 97+: 100% Legendary
    
    Args:
        score: Sleep score (0-100)
    
    Returns:
        Rarity string or None if below threshold
    """
    weights = get_sleep_reward_weights(score)
    if not weights:
        return None
    rarities = get_standard_reward_rarity_order()
    gated_outcome = evaluate_power_gated_rarity_roll(
        rarities,
        weights,
        adhd_buster=adhd_buster,
    )
    return gated_outcome.get("rarity")


def get_sleep_reward_weights(score: int) -> Optional[list]:
    """
    Get sleep reward weights for a given sleep score.
    
    Mirrors get_sleep_reward_rarity without performing the random draw.
    """
    if score < 50:
        return None
    
    # Determine center tier based on sleep score
    # Tiers map to get_standard_reward_rarity_order() indices.
    if score >= 97:
        center_tier = 6  # Far enough for 100% top obtainable tier
    elif score >= 93:
        center_tier = 5  # 95% Legendary
    elif score >= 90:
        center_tier = 4  # Legendary-centered (75% L)
    elif score >= 80:
        center_tier = 3  # Epic-centered
    elif score >= 65:
        center_tier = 2  # Rare-centered
    elif score >= 50:
        center_tier = 1  # Uncommon-centered
    else:
        center_tier = 0  # Common-centered
    
    # Moving window: [5%, 20%, 50%, 20%, 5%] centered on center_tier
    window = [5, 20, 50, 20, 5]  # -2, -1, 0, +1, +2 from center
    rarities = get_standard_reward_rarity_order()
    weights = [0] * len(rarities)
    
    for offset, pct in zip([-2, -1, 0, 1, 2], window):
        target_tier = center_tier + offset
        # Clamp to valid range - overflow absorbed at edges
        clamped_tier = max(0, min(len(rarities) - 1, target_tier))
        weights[clamped_tier] += pct
    
    return weights


def check_sleep_entry_reward(sleep_hours: float, bedtime: str, quality_id: str,
                              disruptions: list, chronotype_id: str,
                              story_id: str = None, age: int = None,
                              adhd_buster: Optional[dict] = None) -> dict:
    """
    Check what reward a sleep entry earns.
    
    Args:
        sleep_hours: Hours of sleep
        bedtime: Bedtime in HH:MM
        quality_id: Quality rating
        disruptions: List of disruption tag IDs
        chronotype_id: User's chronotype
        story_id: Story theme for item generation
        age: Age in years (optional, for age-specific duration scoring)
    
    Returns:
        Dict with reward info
    """
    result = {
        "reward": None,
        "score": 0,
        "score_breakdown": {},
        "rarity": None,
        "reward_weights": None,
        "power_gating": None,
        "messages": [],
    }
    
    if sleep_hours < 3:
        result["messages"].append(
            "đź´ Less than 3 hours tracked. Naps are great but log full nights for rewards!"
        )
        return result
    
    score_info = calculate_sleep_score(
        sleep_hours, bedtime, quality_id, disruptions, chronotype_id, age
    )
    result["score"] = score_info["total_score"]
    result["score_breakdown"] = score_info
    
    reward_weights = get_sleep_reward_weights(score_info["total_score"])
    result["reward_weights"] = reward_weights
    rarity = None
    if reward_weights:
        rarities = get_standard_reward_rarity_order()
        gated_outcome = evaluate_power_gated_rarity_roll(
            rarities,
            reward_weights,
            adhd_buster=adhd_buster,
        )
        rarity = gated_outcome.get("rarity")
        result["power_gating"] = gated_outcome
    result["rarity"] = rarity
    
    if rarity:
        result["reward"] = generate_item(rarity=rarity, story_id=story_id)
        result["messages"].append(
            f"đźŚ™ {sleep_hours:.1f}h sleep with {score_info['total_score']} score! "
            f"Earned a {rarity} item!"
        )
        gating = result.get("power_gating") or {}
        if gating.get("downgraded"):
            message = gating.get("message") or (
                f"Tier gated by power. Current cap: {gating.get('max_unlocked_rarity', 'Unknown')}."
            )
            result["messages"].append(f"🔒 {message}")
    else:
        result["messages"].append(
            f"đźŚ™ Sleep logged! Score: {score_info['total_score']}/100 "
            f"(need 50+ for rewards)"
        )
    
    # Add helpful messages
    result["messages"].append(score_info["duration_message"])
    result["messages"].append(score_info["bedtime_message"])
    
    return result


def check_sleep_streak_reward(
    sleep_entries: list,
    achieved_milestones: list,
    story_id: str = None,
    adhd_buster: Optional[dict] = None,
) -> Optional[dict]:
    """
    Check if current streak earns a milestone reward.
    
    Args:
        sleep_entries: List of sleep entries
        achieved_milestones: Already achieved milestone IDs
        story_id: Story theme
    
    Returns:
        Reward dict or None
    """
    streak = check_sleep_streak(sleep_entries)
    
    for days, rarity, name in SLEEP_STREAK_THRESHOLDS:
        milestone_id = f"sleep_streak_{days}"
        if streak >= days and milestone_id not in achieved_milestones:
            gate_result = resolve_power_gated_reward_rarity(rarity, adhd_buster=adhd_buster)
            final_rarity = gate_result.get("rarity", rarity)
            power_gating = gate_result.get("power_gating")
            lock_message = get_power_gate_downgrade_message(power_gating)
            return {
                "milestone_id": milestone_id,
                "streak_days": days,
                "name": name,
                "requested_rarity": rarity,
                "rarity": final_rarity,
                "power_gating": power_gating,
                "item": generate_item(rarity=final_rarity, story_id=story_id),
                "message": (
                    f"đźŚ™ {days}-night sleep streak! Earned a {final_rarity} item!"
                    + (f" 🔒 {lock_message}" if lock_message else "")
                ),
            }
    
    return None


def check_sleep_milestones(
    sleep_entries: list,
    achieved_milestones: list,
    chronotype_id: str = "moderate",
    story_id: str = None,
    adhd_buster: Optional[dict] = None,
) -> list:
    """
    Check for newly achieved sleep milestones.
    
    Args:
        sleep_entries: List of sleep entries
        achieved_milestones: Already achieved milestone IDs
        chronotype_id: User's chronotype
        story_id: Story theme
    
    Returns:
        List of newly achieved milestones with rewards
    """
    new_milestones = []
    
    if not sleep_entries:
        return new_milestones
    
    # Calculate stats for milestone checks
    total_hours = sum(e.get("sleep_hours", 0) for e in sleep_entries)
    
    for milestone in SLEEP_MILESTONES:
        mid = milestone["id"]
        if mid in achieved_milestones:
            continue
        
        achieved = False
        check = milestone.get("check")
        
        if check == "first_entry":
            achieved = len(sleep_entries) >= 1
        
        elif check == "total_entries":
            achieved = len(sleep_entries) >= milestone.get("threshold", 0)
        
        elif check == "total_hours":
            achieved = total_hours >= milestone.get("threshold", 0)
        
        elif check == "single_score":
            # Check if any entry has high enough score
            threshold = milestone.get("threshold", 95)
            for entry in sleep_entries:
                if entry.get("score", 0) >= threshold:
                    achieved = True
                    break
        
        elif check == "early_bedtime_count":
            # Count entries with bedtime before (earlier than) optimal window start
            # "Early" means going to bed earlier than needed - a good habit
            chrono = get_chronotype(chronotype_id) or SLEEP_CHRONOTYPES[1]
            optimal_start_mins = time_to_minutes(chrono[3])
            count = 0
            for entry in sleep_entries:
                if entry.get("bedtime"):
                    bedtime_mins = time_to_minutes(entry["bedtime"])
                    
                    # Normalize both times for comparison
                    # Treat times after midnight (00:00-05:59) as "late night" continuation
                    norm_optimal = optimal_start_mins
                    norm_bedtime = bedtime_mins
                    
                    # If optimal start is evening (after 6pm) and bedtime is after midnight
                    if optimal_start_mins >= 18 * 60 and bedtime_mins < 6 * 60:
                        norm_bedtime += 24 * 60  # bedtime is actually "late" (next day)
                    
                    # Early means bedtime < optimal_start (went to bed earlier than suggested)
                    if norm_bedtime < norm_optimal:
                        count += 1
            achieved = count >= milestone.get("threshold", 5)
        
        elif check == "consistent_week":
            # Check for 7 consecutive days with consistent bedtime (Â±30min)
            achieved = _check_consistent_bedtime_week(sleep_entries)
        
        elif check == "quality_streak":
            # Check for consecutive good/excellent quality days
            threshold = milestone.get("threshold", 7)
            achieved = _check_quality_streak(sleep_entries, threshold)
        
        if achieved:
            requested_rarity = milestone["rarity"]
            gate_result = resolve_power_gated_reward_rarity(
                requested_rarity,
                adhd_buster=adhd_buster,
            )
            final_rarity = gate_result.get("rarity", requested_rarity)
            power_gating = gate_result.get("power_gating")
            lock_message = get_power_gate_downgrade_message(power_gating)
            new_milestones.append({
                "milestone_id": mid,
                "name": milestone["name"],
                "description": milestone["description"],
                "requested_rarity": requested_rarity,
                "rarity": final_rarity,
                "power_gating": power_gating,
                "item": generate_item(rarity=final_rarity, story_id=story_id),
                "message": (
                    f"đźŹ† {milestone['name']}! {milestone['description']}"
                    + (f" Reward: {final_rarity}." if final_rarity else "")
                    + (f" 🔒 {lock_message}" if lock_message else "")
                ),
            })
    
    return new_milestones


def _check_consistent_bedtime_week(sleep_entries: list) -> bool:
    """Check if there are 7 consecutive days with consistent bedtime."""
    from datetime import datetime, timedelta
    
    if len(sleep_entries) < 7:
        return False
    
    # Create date->bedtime map
    date_bedtime = {}
    for entry in sleep_entries:
        if entry.get("date") and entry.get("bedtime"):
            date_bedtime[entry["date"]] = time_to_minutes(entry["bedtime"])
    
    if len(date_bedtime) < 7:
        return False
    
    # Sort dates
    sorted_dates = sorted(date_bedtime.keys())
    
    # Check for 7 consecutive days
    for i in range(len(sorted_dates) - 6):
        start_date = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
        consecutive = True
        bedtimes = []
        
        for j in range(7):
            check_date = (start_date + timedelta(days=j)).strftime("%Y-%m-%d")
            if check_date not in date_bedtime:
                consecutive = False
                break
            bedtimes.append(date_bedtime[check_date])
        
        if consecutive and bedtimes:
            # Normalize bedtimes for overnight comparison
            # If any bedtime is after midnight (< 6*60 = 360 mins), add 24*60
            # to create consistency with late-night times
            normalized = []
            has_early = any(b < 6 * 60 for b in bedtimes)  # After midnight
            has_late = any(b >= 18 * 60 for b in bedtimes)  # Before midnight
            
            for b in bedtimes:
                if has_early and has_late and b < 6 * 60:
                    normalized.append(b + 24 * 60)  # Shift post-midnight times
                else:
                    normalized.append(b)
            
            # Check if all bedtimes are within 30 min of average
            avg = sum(normalized) / len(normalized)
            all_consistent = all(abs(b - avg) <= 30 for b in normalized)
            if all_consistent:
                return True
    
    return False


def _check_quality_streak(sleep_entries: list, threshold: int) -> bool:
    """Check for quality streak (consecutive calendar days with good/excellent quality)."""
    from datetime import datetime, timedelta
    
    if len(sleep_entries) < threshold:
        return False
    
    # Create date->quality map
    date_quality = {}
    for entry in sleep_entries:
        if entry.get("date") and entry.get("quality"):
            date_quality[entry["date"]] = entry["quality"]
    
    if len(date_quality) < threshold:
        return False
    
    good_qualities = {"excellent", "good"}
    
    # Sort dates and check for consecutive CALENDAR days with good quality
    sorted_dates = sorted(date_quality.keys())
    streak = 0
    prev_date = None
    
    for date_str in sorted_dates:
        if date_quality[date_str] in good_qualities:
            if prev_date is None:
                streak = 1
            else:
                # Check if this date is exactly 1 day after prev_date
                try:
                    curr = datetime.strptime(date_str, "%Y-%m-%d")
                    prev = datetime.strptime(prev_date, "%Y-%m-%d")
                    if (curr - prev).days == 1:
                        streak += 1
                    else:
                        streak = 1  # Gap in dates, restart streak
                except ValueError:
                    streak = 1
            prev_date = date_str
            if streak >= threshold:
                return True
        else:
            streak = 0
            prev_date = None
    
    return False


def check_all_sleep_rewards(sleep_entries: list, sleep_hours: float, bedtime: str,
                             wake_time: str, quality_id: str, disruptions: list,
                             current_date: str, achieved_milestones: list,
                             chronotype_id: str = "moderate",
                             story_id: str = None, age: int = None,
                             adhd_buster: Optional[dict] = None) -> dict:
    """
    Comprehensive check for all sleep-related rewards.
    
    Args:
        sleep_entries: Existing entries (WITHOUT the new entry)
        sleep_hours: Hours of sleep for new entry
        bedtime: Bedtime for new entry
        wake_time: Wake time for new entry
        quality_id: Quality rating
        disruptions: List of disruption tags
        current_date: Today's date
        achieved_milestones: Already achieved milestone IDs
        chronotype_id: User's chronotype
        story_id: Story theme
        age: Age in years (optional, for age-specific duration scoring)
    
    Returns:
        Dict with all reward information
    """
    # Get base reward for this sleep entry
    base_rewards = check_sleep_entry_reward(
        sleep_hours,
        bedtime,
        quality_id,
        disruptions,
        chronotype_id,
        story_id,
        age,
        adhd_buster=adhd_buster,
    )
    
    # Create temp entries list including new entry for streak/milestone checks
    new_entry = {
        "date": current_date,
        "sleep_hours": sleep_hours,
        "bedtime": bedtime,
        "wake_time": wake_time,
        "quality": quality_id,
        "disruptions": disruptions,
        "score": base_rewards.get("score", 0),
    }
    temp_entries = sleep_entries + [new_entry]
    
    # Check streak rewards
    streak_reward = check_sleep_streak_reward(
        temp_entries,
        achieved_milestones,
        story_id,
        adhd_buster=adhd_buster,
    )
    
    # Check milestone achievements
    new_milestones = check_sleep_milestones(
        temp_entries,
        achieved_milestones,
        chronotype_id,
        story_id,
        adhd_buster=adhd_buster,
    )
    
    # Compile all results
    result = {
        **base_rewards,
        "streak_reward": streak_reward,
        "new_milestones": new_milestones,
        "current_streak": check_sleep_streak(temp_entries),
    }
    
    # Add streak message
    if streak_reward:
        result["messages"].append(streak_reward["message"])
    
    # Add milestone messages
    for milestone in new_milestones:
        result["messages"].append(milestone["message"])
    
    return result


def get_sleep_stats(sleep_entries: list) -> dict:
    """
    Calculate sleep statistics for display.
    
    Args:
        sleep_entries: List of sleep entries
    
    Returns:
        Dict with stats
    """
    from datetime import datetime, timedelta
    
    if not sleep_entries:
        return {
            "total_hours": 0,
            "total_nights": 0,
            "avg_hours": 0,
            "avg_score": 0,
            "this_week_avg": 0,
            "best_score": 0,
            "current_streak": 0,
            "nights_on_target": 0,  # Nights with 7+ hours
        }
    
    total_hours = sum(e.get("sleep_hours", 0) for e in sleep_entries)
    total_nights = len(sleep_entries)
    scores = [e.get("score", 0) for e in sleep_entries if e.get("score")]
    
    # This week
    today = datetime.now()
    week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    
    week_entries = [e for e in sleep_entries if e.get("date", "") >= week_ago]
    week_hours = [e.get("sleep_hours", 0) for e in week_entries]
    
    # Nights on target (7+ hours)
    nights_on_target = sum(1 for e in sleep_entries if e.get("sleep_hours", 0) >= 7)
    
    return {
        "total_hours": total_hours,
        "total_nights": total_nights,
        "avg_hours": total_hours / total_nights if total_nights else 0,
        "avg_score": sum(scores) / len(scores) if scores else 0,
        "this_week_avg": sum(week_hours) / len(week_hours) if week_hours else 0,
        "best_score": max(scores) if scores else 0,
        "current_streak": check_sleep_streak(sleep_entries),
        "nights_on_target": nights_on_target,
        "target_rate": (nights_on_target / total_nights * 100) if total_nights else 0,
    }


def format_sleep_duration(hours: float) -> str:
    """Format hours as hours and minutes string."""
    full_hours = int(hours)
    mins = int((hours - full_hours) * 60)
    if mins == 0:
        return f"{full_hours}h"
    return f"{full_hours}h {mins}m"


def get_sleep_recommendation(chronotype_id: str) -> dict:
    """
    Get personalized sleep recommendations based on chronotype.
    
    Args:
        chronotype_id: User's chronotype
    
    Returns:
        Dict with recommendations
    """
    chrono = get_chronotype(chronotype_id) or SLEEP_CHRONOTYPES[1]
    
    bedtime_start = chrono[3]
    bedtime_end = chrono[4]
    
    # Calculate recommended wake times (assuming 7.5-8h sleep)
    bed_start_mins = time_to_minutes(bedtime_start)
    wake_start = minutes_to_time((bed_start_mins + 7 * 60 + 30) % (24 * 60))
    wake_end = minutes_to_time((bed_start_mins + 9 * 60) % (24 * 60))
    
    tips = []
    if chronotype_id == "early_bird":
        tips = [
            "đźŚ… Your natural rhythm favors early mornings",
            "âŹ° Wind down starting at 8:30 PM",
            "đź“µ Avoid screens after 9 PM",
            "đźŚ™ Aim to be in bed by 10 PM latest",
        ]
    elif chronotype_id == "night_owl":
        tips = [
            "đź¦‰ Your natural rhythm is later than average",
            "âŹ° Try to avoid very late nights (after 1 AM)",
            "â€ď¸Ź Get bright light in the morning to help regulate",
            "đźŹ Exercise in the afternoon, not evening",
        ]
    else:
        tips = [
            "âŹ° You have a balanced sleep rhythm",
            "đźŚ™ Aim for bed by 11:30 PM most nights",
            "đź“µ Start winding down 1 hour before bed",
            "â€ď¸Ź Consistent wake times help sleep quality",
        ]
    
    return {
        "chronotype": chrono[1],
        "emoji": chrono[2],
        "optimal_bedtime": f"{bedtime_start} - {bedtime_end}",
        "recommended_wake": f"{wake_start} - {wake_end}",
        "target_hours": "7-9 hours",
        "tips": tips,
    }


# ============================================================================
# XP AND LEVELING SYSTEM
# ============================================================================

# XP required for each level (exponential curve)
def get_xp_for_level(level: int) -> int:
    """Calculate total XP needed to reach a given level."""
    if not isinstance(level, (int, float)) or level <= 1:
        return 0
    # Convert to int first, then check again (level 1.9 -> 1 -> return 0)
    level_int = int(level)
    if level_int <= 1:
        return 0
    # Cap level to prevent integer overflow at extreme values
    level_int = min(level_int, 999)
    # Formula: 100 * (level^1.5) - gives smooth progression
    return int(100 * (level_int ** 1.5))


def get_level_from_xp(total_xp: int) -> tuple:
    """
    Get current level and progress from total XP.
    
    Returns:
        (level, xp_in_current_level, xp_needed_for_next_level, progress_percent)
    """
    try:
        total_xp = int(total_xp)
    except (TypeError, ValueError):
        total_xp = 0
    total_xp = max(0, total_xp)

    if total_xp <= 0:
        return (1, 0, get_xp_for_level(2), 0.0)

    max_level = 999
    max_level_xp = get_xp_for_level(max_level)
    if total_xp >= max_level_xp:
        prev_level_xp = get_xp_for_level(max_level - 1)
        xp_needed = max(1, max_level_xp - prev_level_xp)
        return (max_level, xp_needed, xp_needed, 100.0)

    level = 1
    while get_xp_for_level(level + 1) <= total_xp:
        level += 1
        if level >= max_level:  # Cap at level 999
            break
    
    current_level_xp = get_xp_for_level(level)
    next_level_xp = get_xp_for_level(level + 1)
    xp_in_level = total_xp - current_level_xp
    xp_needed = next_level_xp - current_level_xp
    progress = (xp_in_level / xp_needed * 100) if xp_needed > 0 else 100.0
    
    return (level, xp_in_level, xp_needed, min(progress, 100.0))


# Level titles
LEVEL_TITLES = {
    1: ("Novice", "đźŚ±"),
    5: ("Apprentice", "đź“š"),
    10: ("Focused", "đźŽŻ"),
    15: ("Dedicated", "â­"),
    20: ("Disciplined", "đź’Ş"),
    25: ("Expert", "đźŹ†"),
    30: ("Master", "đź’’"),
    40: ("Grandmaster", "đź”®"),
    50: ("Legend", "âšˇ"),
    75: ("Mythic", "đźŚź"),
    100: ("Transcendent", "âś¨"),
}


def get_level_title(level: int) -> tuple:
    """Get the title and emoji for a given level."""
    title = ("Novice", "đźŚ±")
    for req_level, info in sorted(LEVEL_TITLES.items()):
        if level >= req_level:
            title = info
    return title


# XP rewards for various activities
XP_REWARDS = {
    "focus_session": 50,        # Base XP per focus session
    "focus_per_minute": 2,      # Bonus XP per minute focused
    "weight_log": 20,           # XP for logging weight
    "sleep_log": 25,            # XP for logging sleep
    "activity_log": 30,         # XP for logging activity
    "streak_day": 15,           # Bonus XP per streak day
    "daily_login": 25,          # XP for daily login
    "challenge_complete": 100,  # XP for completing a challenge
    "achievement_unlock": 200,  # XP for unlocking achievement
    "item_collect": 10,         # XP for collecting an item
    "rare_item": 25,            # Bonus for Rare+ items
    "epic_item": 50,            # Bonus for Epic+ items
    "legendary_item": 100,      # Bonus for Legendary items
}


def calculate_session_xp(duration_minutes: int, streak_days: int = 0, 
                         multiplier: float = 1.0, lucky_xp_bonus: int = 0,
                         adhd_buster: dict = None) -> dict:
    """
    Calculate XP earned from a focus session.
    
    Args:
        duration_minutes: Session duration in minutes
        streak_days: Current streak days
        multiplier: XP multiplier (e.g., 1.5 for strategic priority)
        lucky_xp_bonus: Bonus XP% from lucky options on gear (e.g., 5 = +5%)
        adhd_buster: Hero data for entity perk calculation (optional)
    
    Returns dict with breakdown of XP sources.
    """
    # Validate inputs
    duration_minutes = max(0, int(duration_minutes) if duration_minutes else 0)
    streak_days = max(0, int(streak_days) if streak_days else 0)
    multiplier = max(0.0, float(multiplier) if multiplier else 1.0)
    lucky_xp_bonus = max(0, int(lucky_xp_bonus) if lucky_xp_bonus else 0)
    
    base_xp = XP_REWARDS["focus_session"]
    duration_xp = duration_minutes * XP_REWARDS["focus_per_minute"]
    streak_bonus = min(streak_days, 30) * XP_REWARDS["streak_day"] // 10  # Diminishing returns
    
    subtotal = base_xp + duration_xp + streak_bonus
    
    # Apply multiplier first (strategic priority bonus)
    subtotal = int(subtotal * multiplier)
    
    # Apply lucky XP bonus from gear (additive after multiplier)
    if lucky_xp_bonus > 0:
        lucky_bonus_xp = int(subtotal * (lucky_xp_bonus / 100.0))
        subtotal_after_gear = subtotal + lucky_bonus_xp
    else:
        lucky_bonus_xp = 0
        subtotal_after_gear = subtotal
    
    # âś¨ ENTITY PERK BONUS: Apply XP bonuses from collected entities
    entity_xp_bonus = 0
    entity_xp_breakdown = []
    if adhd_buster:
        # Determine time of day for time-based perks
        from datetime import datetime
        hour = datetime.now().hour
        is_morning = 6 <= hour < 12
        is_night = hour >= 20 or hour < 6
        
        xp_perks = get_entity_xp_perks(
            adhd_buster, 
            source="session",
            session_minutes=duration_minutes,
            is_morning=is_morning,
            is_night=is_night
        )
        
        if xp_perks["total_bonus_percent"] > 0:
            # Apply to subtotal (not compounded with lucky bonus) for ADDITIVE stacking
            entity_xp_bonus = int(subtotal * (xp_perks["total_bonus_percent"] / 100.0))
            entity_xp_breakdown = xp_perks["bonus_breakdown"]
    
    total = subtotal_after_gear + entity_xp_bonus
    
    breakdown_parts = [f"Base: {base_xp}", f"Duration: {duration_xp}", f"Streak: {streak_bonus}"]
    if multiplier != 1.0:
        breakdown_parts.append(f"Multiplier: {multiplier}x")
    if lucky_xp_bonus > 0:
        breakdown_parts.append(f"Lucky Bonus: +{lucky_xp_bonus}% ({lucky_bonus_xp} XP)")
    if entity_xp_bonus > 0:
        breakdown_parts.append(f"Entity Perks: +{entity_xp_bonus} XP")
    
    return {
        "base_xp": base_xp,
        "duration_xp": duration_xp,
        "streak_bonus": streak_bonus,
        "multiplier": multiplier,
        "lucky_xp_bonus": lucky_xp_bonus,
        "lucky_bonus_xp": lucky_bonus_xp,
        "entity_xp_bonus": entity_xp_bonus,
        "entity_xp_breakdown": entity_xp_breakdown,
        "total_xp": total,
        "breakdown": " + ".join(breakdown_parts)
    }


def award_xp(adhd_buster: dict, xp_amount: int, source: str = "unknown") -> dict:
    """
    Award XP to the player and check for level up.
    
    Returns dict with level up info if applicable.
    """
    # Validate xp_amount - must be non-negative integer
    if not isinstance(xp_amount, int) or xp_amount < 0:
        xp_amount = max(0, int(xp_amount)) if xp_amount else 0
    
    # đźŹ™ď¸Ź CITY BONUS: Library XP bonus (percentage)
    city_xp_bonus = 0
    base_xp = xp_amount
    city_bonuses = _safe_get_city_bonuses(adhd_buster)
    xp_bonus_pct = city_bonuses.get("xp_bonus", 0)
    if xp_bonus_pct > 0 and xp_amount > 0:
        city_xp_bonus = int(xp_amount * xp_bonus_pct / 100.0)
        xp_amount = xp_amount + city_xp_bonus
    
    old_xp = adhd_buster.get("total_xp", 0)
    # Ensure old_xp is valid
    if not isinstance(old_xp, (int, float)) or old_xp < 0:
        old_xp = 0
    old_xp = int(old_xp)
    
    old_level, _, _, _ = get_level_from_xp(old_xp)
    
    new_xp = old_xp + xp_amount
    # Cap XP to prevent integer overflow (max ~2 billion)
    new_xp = min(new_xp, 2_000_000_000)
    adhd_buster["total_xp"] = new_xp
    
    new_level, xp_in_level, xp_needed, progress = get_level_from_xp(new_xp)
    
    # Track XP history
    if "xp_history" not in adhd_buster:
        adhd_buster["xp_history"] = []
    adhd_buster["xp_history"].append({
        "amount": xp_amount,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "new_total": new_xp
    })
    # Keep only last 100 entries
    if len(adhd_buster["xp_history"]) > 100:
        adhd_buster["xp_history"] = adhd_buster["xp_history"][-100:]
    
    result = {
        "xp_earned": xp_amount,
        "base_xp": base_xp,
        "city_xp_bonus": city_xp_bonus,
        "total_xp": new_xp,
        "level": new_level,
        "xp_in_level": xp_in_level,
        "xp_needed": xp_needed,
        "progress": progress,
        "leveled_up": new_level > old_level,
        "levels_gained": new_level - old_level,
    }
    
    if new_level > old_level:
        old_title, old_emoji = get_level_title(old_level)
        new_title, new_emoji = get_level_title(new_level)
        result["old_level"] = old_level
        result["old_title"] = f"{old_emoji} {old_title}"
        result["new_title"] = f"{new_emoji} {new_title}"
        result["title_changed"] = (old_title != new_title)
    
    return result


# ============================================================================
# DAILY LOGIN REWARDS
# ============================================================================

DAILY_LOGIN_REWARDS = [
    # Day 1-7 (Week 1)
    {"day": 1, "type": "xp", "amount": 25, "description": "25 XP", "emoji": "âś¨"},
    {"day": 2, "type": "item", "rarity": "Common", "description": "Common Item", "emoji": "đź“¦"},
    {"day": 3, "type": "xp", "amount": 50, "description": "50 XP", "emoji": "âś¨"},
    {"day": 4, "type": "streak_freeze", "amount": 1, "description": "Streak Freeze Token", "emoji": "đź§Š"},
    {"day": 5, "type": "item", "rarity": "Uncommon", "description": "Uncommon Item", "emoji": "đź“¦"},
    {"day": 6, "type": "xp", "amount": 75, "description": "75 XP", "emoji": "âś¨"},
    {"day": 7, "type": "mystery_box", "tier": "silver", "description": "Silver Mystery Box", "emoji": "đźŽ"},
    
    # Day 8-14 (Week 2)
    {"day": 8, "type": "xp", "amount": 50, "description": "50 XP", "emoji": "âś¨"},
    {"day": 9, "type": "item", "rarity": "Uncommon", "description": "Uncommon Item", "emoji": "đź“¦"},
    {"day": 10, "type": "multiplier", "amount": 1.5, "duration": 60, "description": "1.5x XP (1 hour)", "emoji": "âšˇ"},
    {"day": 11, "type": "xp", "amount": 100, "description": "100 XP", "emoji": "âś¨"},
    {"day": 12, "type": "streak_freeze", "amount": 1, "description": "Streak Freeze Token", "emoji": "đź§Š"},
    {"day": 13, "type": "item", "rarity": "Rare", "description": "Rare Item", "emoji": "đź“¦"},
    {"day": 14, "type": "mystery_box", "tier": "gold", "description": "Gold Mystery Box", "emoji": "đźŽ"},
    
    # Day 15-21 (Week 3)
    {"day": 15, "type": "xp", "amount": 75, "description": "75 XP", "emoji": "âś¨"},
    {"day": 16, "type": "item", "rarity": "Rare", "description": "Rare Item", "emoji": "đź“¦"},
    {"day": 17, "type": "xp", "amount": 100, "description": "100 XP", "emoji": "âś¨"},
    {"day": 18, "type": "streak_freeze", "amount": 2, "description": "2 Streak Freeze Tokens", "emoji": "đź§Š"},
    {"day": 19, "type": "multiplier", "amount": 2.0, "duration": 60, "description": "2x XP (1 hour)", "emoji": "âšˇ"},
    {"day": 20, "type": "item", "rarity": "Epic", "description": "Epic Item", "emoji": "đź“¦"},
    {"day": 21, "type": "mystery_box", "tier": "diamond", "description": "Diamond Mystery Box", "emoji": "đź’Ž"},
    
    # Day 22-28 (Week 4)
    {"day": 22, "type": "xp", "amount": 100, "description": "100 XP", "emoji": "âś¨"},
    {"day": 23, "type": "item", "rarity": "Rare", "description": "Rare Item", "emoji": "đź“¦"},
    {"day": 24, "type": "streak_freeze", "amount": 2, "description": "2 Streak Freeze Tokens", "emoji": "đź§Š"},
    {"day": 25, "type": "xp", "amount": 150, "description": "150 XP", "emoji": "âś¨"},
    {"day": 26, "type": "multiplier", "amount": 2.0, "duration": 120, "description": "2x XP (2 hours)", "emoji": "âšˇ"},
    {"day": 27, "type": "item", "rarity": "Epic", "description": "Epic Item", "emoji": "đź“¦"},
    {"day": 28, "type": "mystery_box", "tier": "legendary", "description": "Legendary Mystery Box!", "emoji": "đźŚź"},
]


def get_daily_login_reward(login_streak: int) -> dict:
    """Get the reward for the current login streak day."""
    # Validate login_streak
    if not isinstance(login_streak, int) or login_streak < 1:
        login_streak = 1
    
    # Cycle through rewards (28-day cycle)
    day_in_cycle = ((login_streak - 1) % 28) + 1
    
    for reward in DAILY_LOGIN_REWARDS:
        if reward["day"] == day_in_cycle:
            return {
                **reward,
                "login_streak": login_streak,
                "day_in_cycle": day_in_cycle,
                "cycle_number": (login_streak - 1) // 28 + 1
            }
    
    # Fallback
    return {"day": day_in_cycle, "type": "xp", "amount": 25, "description": "25 XP", "emoji": "âś¨", "login_streak": login_streak, "day_in_cycle": day_in_cycle, "cycle_number": 1}


def get_work_day_date(dt: datetime = None) -> str:
    """
    Get the 'work day' date string for a given datetime.
    
    Work day starts at 5:00 AM, so anything before 5 AM counts as the previous day.
    This prevents daily rewards from resetting at midnight for night owls.
    
    Args:
        dt: The datetime to check. Defaults to now.
    
    Returns:
        Date string in YYYY-MM-DD format representing the work day.
    """
    if dt is None:
        dt = datetime.now()
    
    # If before 5 AM, count as previous day
    if dt.hour < 5:
        dt = dt - timedelta(days=1)
    
    return dt.strftime("%Y-%m-%d")


def claim_daily_login(adhd_buster: dict, story_id: str = None) -> dict:
    """
    Claim daily login reward. Should be called once per day.
    
    Returns the reward info and any items/XP granted.
    """
    today = get_work_day_date()
    last_login = adhd_buster.get("last_login_date")
    
    # Check if already claimed today
    if last_login == today:
        return {"already_claimed": True, "message": "Already claimed today's reward!"}
    
    # Calculate login streak
    if last_login:
        last_date = safe_parse_date(last_login)
        today_date = safe_parse_date(today)
        if not last_date or not today_date:
            adhd_buster["login_streak"] = 1
        else:
            days_diff = (today_date - last_date).days

            if days_diff == 0:
                return {"already_claimed": True, "message": "Already claimed today's reward!"}
            if days_diff < 0:
                # Recover from clock skew / bad future dates without locking
                # the user out of daily rewards.
                adhd_buster["login_streak"] = 1
            if days_diff == 1:
                # Consecutive day
                adhd_buster["login_streak"] = adhd_buster.get("login_streak", 0) + 1
            elif days_diff > 1:
                # Streak broken - check for streak freeze token first
                freeze_count = adhd_buster.get("streak_freeze_tokens", 0)
                if freeze_count > 0 and days_diff == 2:
                    # Use streak freeze
                    adhd_buster["streak_freeze_tokens"] = freeze_count - 1
                    adhd_buster["login_streak"] = adhd_buster.get("login_streak", 0) + 1
                    adhd_buster["streak_freezes_used"] = adhd_buster.get("streak_freezes_used", 0) + 1
                else:
                    # âś¨ ENTITY PERK: Check for streak_save perk (chance to save streak)
                    streak_saved = False
                    if days_diff == 2:  # Only works for 1-day gap
                        luck_perks = get_entity_luck_perks(adhd_buster)
                        streak_save_chance = luck_perks.get("streak_save", 0)
                        if streak_save_chance > 0:
                            import random
                            if random.randint(1, 100) <= streak_save_chance:
                                streak_saved = True
                                adhd_buster["login_streak"] = adhd_buster.get("login_streak", 0) + 1
                                adhd_buster["entity_streak_saves"] = adhd_buster.get("entity_streak_saves", 0) + 1
                                print(f"[Entity Perks] âś¨ Streak saved by entity perk! ({streak_save_chance}% chance)")
                    
                    if not streak_saved:
                        # Reset streak
                        adhd_buster["login_streak"] = 1
    else:
        adhd_buster["login_streak"] = 1
    
    adhd_buster["last_login_date"] = today
    adhd_buster["total_logins"] = adhd_buster.get("total_logins", 0) + 1
    
    # Get and process reward
    reward = get_daily_login_reward(adhd_buster["login_streak"])
    result = {
        "claimed": True,
        "reward": reward,
        "login_streak": adhd_buster["login_streak"],
        "total_logins": adhd_buster["total_logins"],
        "items_granted": [],
        "xp_granted": 0,
    }
    
    # Process reward by type
    if reward["type"] == "xp":
        xp_result = award_xp(adhd_buster, reward["amount"], "daily_login")
        result["xp_granted"] = reward["amount"]
        result["xp_result"] = xp_result
        
    elif reward["type"] == "item":
        item = generate_item(
            rarity=reward.get("rarity"),
            session_minutes=30,  # Standard reward session
            story_id=story_id
        )
        if "inventory" not in adhd_buster:
            adhd_buster["inventory"] = []
        adhd_buster["inventory"].append(item)
        result["items_granted"].append(item)
        # Cap inventory
        if len(adhd_buster["inventory"]) > 500:
            adhd_buster["inventory"] = adhd_buster["inventory"][-500:]
        
    elif reward["type"] == "streak_freeze":
        adhd_buster["streak_freeze_tokens"] = adhd_buster.get("streak_freeze_tokens", 0) + reward["amount"]
        result["streak_freeze_tokens"] = adhd_buster["streak_freeze_tokens"]
        
    elif reward["type"] == "multiplier":
        # Store active multiplier with expiration
        duration = reward.get("duration", 60)
        if not isinstance(duration, (int, float)) or duration <= 0:
            duration = 60
        adhd_buster["active_multiplier"] = {
            "value": reward.get("amount", 1.5),
            "expires_at": (datetime.now().timestamp() + duration * 60),
            "source": "daily_login"
        }
        result["multiplier_active"] = adhd_buster["active_multiplier"]
        
    elif reward["type"] == "mystery_box":
        # Open mystery box immediately
        box_result = open_mystery_box(adhd_buster, reward.get("tier", "gold"), story_id)
        result["mystery_box_result"] = box_result
        result["items_granted"].extend(box_result.get("items", []))
        result["xp_granted"] += box_result.get("xp", 0)
    
    return result


def get_active_multiplier(adhd_buster: dict) -> float:
    """Get current active XP multiplier (1.0 if none)."""
    multiplier = adhd_buster.get("active_multiplier")
    if not multiplier or not isinstance(multiplier, dict):
        return 1.0
    
    try:
        expires_at = float(multiplier.get("expires_at", 0))
        if datetime.now().timestamp() > expires_at:
            # Expired - safely remove
            adhd_buster.pop("active_multiplier", None)
            return 1.0
        
        value = float(multiplier.get("value", 1.0))
        # Clamp multiplier to reasonable range
        return max(1.0, min(value, 10.0))
    except (TypeError, ValueError):
        adhd_buster.pop("active_multiplier", None)
        return 1.0


# ============================================================================
# MYSTERY BOXES (VARIABLE REWARDS)
# ============================================================================

MYSTERY_BOX_TIERS = {
    "bronze": {
        "name": "Bronze Mystery Box",
        "emoji": "đźĄ‰",
        "color": "#CD7F32",
        "xp_range": (10, 30),
        "item_chances": {"Common": 70, "Uncommon": 25, "Rare": 5},
        "item_count": (1, 2),
        "streak_freeze_chance": 5,
    },
    "silver": {
        "name": "Silver Mystery Box", 
        "emoji": "đźĄ",
        "color": "#C0C0C0",
        "xp_range": (25, 75),
        "item_chances": {"Common": 40, "Uncommon": 40, "Rare": 15, "Epic": 5},
        "item_count": (1, 3),
        "streak_freeze_chance": 10,
    },
    "gold": {
        "name": "Gold Mystery Box",
        "emoji": "đźĄ‡",
        "color": "#FFD700",
        "xp_range": (50, 150),
        "item_chances": {"Uncommon": 30, "Rare": 40, "Epic": 25, "Legendary": 5},
        "item_count": (2, 4),
        "streak_freeze_chance": 20,
    },
    "diamond": {
        "name": "Diamond Mystery Box",
        "emoji": "đź’Ž",
        "color": "#B9F2FF",
        "xp_range": (100, 300),
        "item_chances": {"Rare": 30, "Epic": 45, "Legendary": 25},
        "item_count": (2, 5),
        "streak_freeze_chance": 30,
    },
    "legendary": {
        "name": "Legendary Mystery Box",
        "emoji": "đźŚź",
        "color": "#FF9800",
        "xp_range": (200, 500),
        "item_chances": {"Epic": 40, "Legendary": 60},
        "item_count": (3, 5),
        "streak_freeze_chance": 50,
    },
}


def open_mystery_box(adhd_buster: dict, tier: str = "bronze", story_id: str = None) -> dict:
    """
    Open a mystery box and grant random rewards.
    
    Returns dict with all rewards granted.
    """
    # Validate tier
    if tier not in MYSTERY_BOX_TIERS:
        tier = "bronze"
    box = MYSTERY_BOX_TIERS[tier]
    result = {
        "box_tier": tier,
        "box_name": box["name"],
        "box_emoji": box["emoji"],
        "items": [],
        "xp": 0,
        "streak_freeze": 0,
        "rewards_summary": [],
    }
    
    # Random XP
    xp_amount = random.randint(*box["xp_range"])
    xp_result = award_xp(adhd_buster, xp_amount, f"mystery_box_{tier}")
    result["xp"] = xp_amount
    result["xp_result"] = xp_result
    result["rewards_summary"].append(f"âś¨ {xp_amount} XP")
    
    # Random items
    num_items = random.randint(*box["item_count"])
    for _ in range(num_items):
        # Pick rarity based on chances
        roll = random.randint(1, 100)
        cumulative = 0
        chosen_rarity = "Common"
        for rarity, chance in box["item_chances"].items():
            cumulative += chance
            if roll <= cumulative:
                chosen_rarity = rarity
                break
        
        item = generate_item(
            rarity=chosen_rarity,
            session_minutes=30,
            story_id=story_id
        )
        if "inventory" not in adhd_buster:
            adhd_buster["inventory"] = []
        adhd_buster["inventory"].append(item)
        result["items"].append(item)
        rarity_color = ITEM_RARITIES.get(chosen_rarity, {}).get('color', '#FFFFFF')
        result["rewards_summary"].append(f"{rarity_color} {item['name']}")
    
    # Cap inventory
    if len(adhd_buster["inventory"]) > 500:
        adhd_buster["inventory"] = adhd_buster["inventory"][-500:]
    
    # Chance for streak freeze
    if random.randint(1, 100) <= box["streak_freeze_chance"]:
        adhd_buster["streak_freeze_tokens"] = adhd_buster.get("streak_freeze_tokens", 0) + 1
        result["streak_freeze"] = 1
        result["rewards_summary"].append("đź§Š Streak Freeze Token")
    
    return result


# ============================================================================
# DAILY & WEEKLY CHALLENGES
# ============================================================================

CHALLENGE_TEMPLATES = {
    # Daily challenges
    "daily_focus_1": {
        "type": "daily",
        "title": "Quick Focus",
        "description": "Complete 1 focus session",
        "requirement": {"type": "sessions", "count": 1},
        "xp_reward": 50,
        "difficulty": "easy",
    },
    "daily_focus_3": {
        "type": "daily",
        "title": "Triple Focus",
        "description": "Complete 3 focus sessions",
        "requirement": {"type": "sessions", "count": 3},
        "xp_reward": 150,
        "difficulty": "medium",
    },
    "daily_minutes_30": {
        "type": "daily",
        "title": "Half Hour Hero",
        "description": "Focus for 30 minutes total",
        "requirement": {"type": "focus_minutes", "count": 30},
        "xp_reward": 75,
        "difficulty": "easy",
    },
    "daily_minutes_60": {
        "type": "daily",
        "title": "Hour of Power",
        "description": "Focus for 60 minutes total",
        "requirement": {"type": "focus_minutes", "count": 60},
        "xp_reward": 150,
        "difficulty": "medium",
    },
    "daily_minutes_120": {
        "type": "daily",
        "title": "Marathon Mind",
        "description": "Focus for 2 hours total",
        "requirement": {"type": "focus_minutes", "count": 120},
        "xp_reward": 300,
        "difficulty": "hard",
    },
    "daily_early_bird": {
        "type": "daily",
        "title": "Early Bird",
        "description": "Complete a session before 9 AM",
        "requirement": {"type": "early_session", "count": 1},
        "xp_reward": 100,
        "difficulty": "medium",
    },
    "daily_night_owl": {
        "type": "daily",
        "title": "Night Owl",
        "description": "Complete a session after 9 PM",
        "requirement": {"type": "night_session", "count": 1},
        "xp_reward": 100,
        "difficulty": "medium",
    },
    "daily_log_all": {
        "type": "daily",
        "title": "Tracker Supreme",
        "description": "Log weight, sleep, and activity today",
        "requirement": {"type": "log_all", "count": 3},
        "xp_reward": 125,
        "difficulty": "medium",
    },
    
    # Weekly challenges
    "weekly_sessions_10": {
        "type": "weekly",
        "title": "Consistency King",
        "description": "Complete 10 focus sessions this week",
        "requirement": {"type": "sessions", "count": 10},
        "xp_reward": 400,
        "difficulty": "medium",
    },
    "weekly_sessions_20": {
        "type": "weekly",
        "title": "Focus Machine",
        "description": "Complete 20 focus sessions this week",
        "requirement": {"type": "sessions", "count": 20},
        "xp_reward": 800,
        "difficulty": "hard",
    },
    "weekly_hours_5": {
        "type": "weekly",
        "title": "Five Hour Focus",
        "description": "Focus for 5 hours total this week",
        "requirement": {"type": "focus_minutes", "count": 300},
        "xp_reward": 500,
        "difficulty": "medium",
    },
    "weekly_hours_10": {
        "type": "weekly",
        "title": "Ten Hour Titan",
        "description": "Focus for 10 hours total this week",
        "requirement": {"type": "focus_minutes", "count": 600},
        "xp_reward": 1000,
        "difficulty": "hard",
    },
    "weekly_streak_7": {
        "type": "weekly",
        "title": "Week Warrior",
        "description": "Maintain a 7-day login streak",
        "requirement": {"type": "login_streak", "count": 7},
        "xp_reward": 350,
        "difficulty": "medium",
    },
    "weekly_log_weight_5": {
        "type": "weekly",
        "title": "Weight Watcher",
        "description": "Log weight 5 days this week",
        "requirement": {"type": "weight_logs", "count": 5},
        "xp_reward": 250,
        "difficulty": "medium",
    },
    "weekly_log_sleep_7": {
        "type": "weekly",
        "title": "Sleep Scholar",
        "description": "Log sleep every day this week",
        "requirement": {"type": "sleep_logs", "count": 7},
        "xp_reward": 350,
        "difficulty": "medium",
    },
    "weekly_log_activity_5": {
        "type": "weekly",
        "title": "Active Achiever",
        "description": "Log activity 5 days this week",
        "requirement": {"type": "activity_logs", "count": 5},
        "xp_reward": 300,
        "difficulty": "medium",
    },
}


def generate_daily_challenges(seed_date: str = None) -> list:
    """
    Generate 3 daily challenges for the given date.
    Uses date as seed for consistent challenges per day.
    """
    if seed_date is None:
        seed_date = datetime.now().strftime("%Y-%m-%d")
    
    # Use deterministic hash (not built-in hash()) so results are stable across restarts.
    seed_bytes = f"{seed_date}:daily".encode("utf-8")
    seed = int(hashlib.sha256(seed_bytes).hexdigest()[:16], 16)
    rng = random.Random(seed)
    
    daily_templates = [k for k, v in CHALLENGE_TEMPLATES.items() if v["type"] == "daily"]
    
    # Select 3 challenges with varying difficulty
    easy = [k for k in daily_templates if CHALLENGE_TEMPLATES[k]["difficulty"] == "easy"]
    medium = [k for k in daily_templates if CHALLENGE_TEMPLATES[k]["difficulty"] == "medium"]
    hard = [k for k in daily_templates if CHALLENGE_TEMPLATES[k]["difficulty"] == "hard"]
    
    selected = []
    if easy:
        selected.append(rng.choice(easy))
    if medium:
        selected.append(rng.choice([m for m in medium if m not in selected]))
    if hard:
        selected.append(rng.choice([h for h in hard if h not in selected]))
    
    # Fill remaining slots if needed
    remaining = [t for t in daily_templates if t not in selected]
    while len(selected) < 3 and remaining:
        choice = rng.choice(remaining)
        selected.append(choice)
        remaining.remove(choice)
    
    challenges = []
    for challenge_id in selected:
        template = CHALLENGE_TEMPLATES[challenge_id]
        challenges.append({
            "id": f"{seed_date}_{challenge_id}",
            "template_id": challenge_id,
            "date": seed_date,
            "progress": 0,
            "completed": False,
            "claimed": False,
            **template
        })
    
    return challenges


def generate_weekly_challenges(week_start: str = None) -> list:
    """
    Generate 2 weekly challenges for the given week.
    """
    if week_start is None:
        today = datetime.now()
        # Get Monday of current week
        monday = today - timedelta(days=today.weekday())
        week_start = monday.strftime("%Y-%m-%d")
    
    # Use deterministic hash (not built-in hash()) so results are stable across restarts.
    seed_bytes = f"{week_start}:weekly".encode("utf-8")
    seed = int(hashlib.sha256(seed_bytes).hexdigest()[:16], 16)
    rng = random.Random(seed)
    
    weekly_templates = [k for k, v in CHALLENGE_TEMPLATES.items() if v["type"] == "weekly"]
    
    # Select 2 challenges
    selected = rng.sample(weekly_templates, min(2, len(weekly_templates)))
    
    challenges = []
    for challenge_id in selected:
        template = CHALLENGE_TEMPLATES[challenge_id]
        challenges.append({
            "id": f"{week_start}_{challenge_id}",
            "template_id": challenge_id,
            "week_start": week_start,
            "progress": 0,
            "completed": False,
            "claimed": False,
            **template
        })
    
    return challenges


def update_challenge_progress(adhd_buster: dict, event_type: str, amount: int = 1) -> list:
    """
    Update progress on active challenges based on an event.
    
    event_type: "session", "focus_minutes", "early_session", "night_session", 
                "weight_log", "sleep_log", "activity_log"
    
    Returns list of newly completed challenges.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Ensure challenges exist for today
    if "daily_challenges" not in adhd_buster or adhd_buster.get("daily_challenges_date") != today:
        adhd_buster["daily_challenges"] = generate_daily_challenges(today)
        adhd_buster["daily_challenges_date"] = today
    
    # Check weekly challenges
    today_dt = datetime.now()
    monday = today_dt - timedelta(days=today_dt.weekday())
    week_start = monday.strftime("%Y-%m-%d")
    
    if "weekly_challenges" not in adhd_buster or adhd_buster.get("weekly_challenges_start") != week_start:
        adhd_buster["weekly_challenges"] = generate_weekly_challenges(week_start)
        adhd_buster["weekly_challenges_start"] = week_start
    
    newly_completed = []
    
    # Map event types to requirement types
    event_to_req = {
        "session": "sessions",
        "focus_minutes": "focus_minutes",
        "early_session": "early_session",
        "night_session": "night_session",
        "weight_log": "weight_logs",
        "sleep_log": "sleep_logs",
        "activity_log": "activity_logs",
    }
    
    req_type = event_to_req.get(event_type)
    if not req_type:
        return newly_completed
    
    # Update daily challenges
    for challenge in adhd_buster["daily_challenges"]:
        if challenge["completed"]:
            continue
        if challenge["requirement"]["type"] == req_type:
            challenge["progress"] += amount
            if challenge["progress"] >= challenge["requirement"]["count"]:
                challenge["completed"] = True
                challenge["completed_at"] = datetime.now().isoformat()
                newly_completed.append(challenge)
        # Special case: log_all
        elif challenge["requirement"]["type"] == "log_all" and event_type in ("weight_log", "sleep_log", "activity_log"):
            # Track which logs done today - use list for JSON serialization
            if "logs_today" not in challenge:
                challenge["logs_today"] = []
            if event_type not in challenge["logs_today"]:
                challenge["logs_today"].append(event_type)
            challenge["progress"] = len(challenge["logs_today"])
            if challenge["progress"] >= 3:
                challenge["completed"] = True
                challenge["completed_at"] = datetime.now().isoformat()
                newly_completed.append(challenge)
    
    # Update weekly challenges
    for challenge in adhd_buster["weekly_challenges"]:
        if challenge["completed"]:
            continue
        if challenge["requirement"]["type"] == req_type:
            challenge["progress"] += amount
            if challenge["progress"] >= challenge["requirement"]["count"]:
                challenge["completed"] = True
                challenge["completed_at"] = datetime.now().isoformat()
                newly_completed.append(challenge)
        # Login streak check
        elif challenge["requirement"]["type"] == "login_streak":
            current_streak = adhd_buster.get("login_streak", 0)
            challenge["progress"] = current_streak
            if current_streak >= challenge["requirement"]["count"]:
                challenge["completed"] = True
                challenge["completed_at"] = datetime.now().isoformat()
                newly_completed.append(challenge)
    
    return newly_completed


def claim_challenge_reward(adhd_buster: dict, challenge_id: str) -> dict:
    """Claim the reward for a completed challenge."""
    # Check daily challenges
    for challenge in adhd_buster.get("daily_challenges", []):
        if challenge["id"] == challenge_id:
            if not challenge["completed"]:
                return {"success": False, "message": "Challenge not completed yet!"}
            if challenge["claimed"]:
                return {"success": False, "message": "Reward already claimed!"}
            
            challenge["claimed"] = True
            xp_result = award_xp(adhd_buster, challenge["xp_reward"], "challenge_complete")
            return {
                "success": True,
                "challenge": challenge,
                "xp_reward": challenge["xp_reward"],
                "xp_result": xp_result
            }
    
    # Check weekly challenges
    for challenge in adhd_buster.get("weekly_challenges", []):
        if challenge["id"] == challenge_id:
            if not challenge["completed"]:
                return {"success": False, "message": "Challenge not completed yet!"}
            if challenge["claimed"]:
                return {"success": False, "message": "Reward already claimed!"}
            
            challenge["claimed"] = True
            xp_result = award_xp(adhd_buster, challenge["xp_reward"], "challenge_complete")
            
            # Weekly challenges also give a mystery box
            box_result = open_mystery_box(adhd_buster, "silver")
            
            return {
                "success": True,
                "challenge": challenge,
                "xp_reward": challenge["xp_reward"],
                "xp_result": xp_result,
                "bonus_box": box_result
            }
    
    return {"success": False, "message": "Challenge not found!"}


# ============================================================================
# STREAK FREEZE SYSTEM
# ============================================================================

def use_streak_freeze(adhd_buster: dict, streak_type: str = "focus") -> dict:
    """
    Use a streak freeze token to protect a streak.
    
    streak_type: "focus", "weight", "sleep", "activity", "login"
    """
    # Validate streak_type
    valid_types = {"focus", "weight", "sleep", "activity", "login"}
    if streak_type not in valid_types:
        streak_type = "focus"
    
    freeze_count = adhd_buster.get("streak_freeze_tokens", 0)
    # Ensure freeze_count is valid integer
    if not isinstance(freeze_count, int) or freeze_count < 0:
        freeze_count = 0
        adhd_buster["streak_freeze_tokens"] = 0
    
    if freeze_count <= 0:
        return {
            "success": False,
            "message": "No streak freeze tokens available!",
            "tokens_remaining": 0
        }
    
    adhd_buster["streak_freeze_tokens"] = freeze_count - 1
    adhd_buster["streak_freezes_used"] = adhd_buster.get("streak_freezes_used", 0) + 1
    
    # Track which streaks have been frozen
    if "frozen_streaks" not in adhd_buster:
        adhd_buster["frozen_streaks"] = {}
    adhd_buster["frozen_streaks"][streak_type] = datetime.now().strftime("%Y-%m-%d")
    
    return {
        "success": True,
        "message": f"Streak freeze applied to {streak_type} streak!",
        "tokens_remaining": adhd_buster["streak_freeze_tokens"],
        "total_used": adhd_buster["streak_freezes_used"]
    }


def check_streak_frozen(adhd_buster: dict, streak_type: str, check_date: str = None) -> bool:
    """Check if a streak was frozen on a given date."""
    if check_date is None:
        yesterday = datetime.now() - timedelta(days=1)
        check_date = yesterday.strftime("%Y-%m-%d")
    
    frozen_streaks = adhd_buster.get("frozen_streaks", {})
    return frozen_streaks.get(streak_type) == check_date


# ============================================================================
# COMBO / MULTIPLIER SYSTEM
# ============================================================================

def calculate_combo_multiplier(adhd_buster: dict) -> dict:
    """
    Calculate combo multiplier based on consecutive activities.
    
    Combos:
    - 3+ sessions in a day: 1.25x
    - 5+ sessions in a day: 1.5x
    - Log all 4 types today: 1.5x bonus
    - Active streak 7+: 1.25x
    - Active streak 30+: 1.5x
    """
    multiplier = 1.0
    bonuses = []
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Sessions today (handle None values)
    daily_stats = adhd_buster.get("daily_stats") or {}
    today_stats = daily_stats.get(today) or {}
    sessions_today = today_stats.get("sessions", 0) or 0
    
    if sessions_today >= 5:
        multiplier *= 1.5
        bonuses.append(("đź”Ą 5+ Sessions", 1.5))
    elif sessions_today >= 3:
        multiplier *= 1.25
        bonuses.append(("âšˇ 3+ Sessions", 1.25))
    
    # Login streak
    login_streak = adhd_buster.get("login_streak", 0)
    if login_streak >= 30:
        multiplier *= 1.5
        bonuses.append(("đźŹ† 30-Day Streak", 1.5))
    elif login_streak >= 7:
        multiplier *= 1.25
        bonuses.append(("đź”… Week Streak", 1.25))
    
    # Active XP multiplier from rewards
    active_mult = get_active_multiplier(adhd_buster)
    if active_mult > 1.0:
        multiplier *= active_mult
        bonuses.append((f"âšˇ Bonus Active", active_mult))
    
    return {
        "total_multiplier": round(multiplier, 2),
        "bonuses": bonuses,
        "description": " Ă— ".join([b[0] for b in bonuses]) if bonuses else "No active bonuses"
    }


# ============================================================================
# PROGRESS BAR HELPERS
# ============================================================================

def get_all_progress_bars(adhd_buster: dict) -> list:
    """
    Get all active progress bars for display.
    
    Returns list of progress bar info dicts.
    """
    progress_bars = []
    
    # XP to next level
    total_xp = adhd_buster.get("total_xp", 0)
    level, xp_in_level, xp_needed, progress = get_level_from_xp(total_xp)
    title, emoji = get_level_title(level)
    progress_bars.append({
        "id": "level",
        "label": f"Level {level} â†’ {level + 1}",
        "sublabel": f"{emoji} {title}",
        "current": xp_in_level,
        "target": xp_needed,
        "percent": progress,
        "color": "#4CAF50",
        "priority": 1,
    })
    
    # Daily login streak to next milestone
    login_streak = adhd_buster.get("login_streak", 0)
    streak_milestones = [7, 14, 21, 28, 50, 100]
    next_milestone = next((m for m in streak_milestones if m > login_streak), 100)
    prev_milestone = max([0] + [m for m in streak_milestones if m <= login_streak])
    streak_progress = ((login_streak - prev_milestone) / (next_milestone - prev_milestone) * 100) if next_milestone > prev_milestone else 100
    progress_bars.append({
        "id": "login_streak",
        "label": f"Login Streak: {login_streak} days",
        "sublabel": f"Next reward at {next_milestone} days",
        "current": login_streak - prev_milestone,
        "target": next_milestone - prev_milestone,
        "percent": streak_progress,
        "color": "#FF9800",
        "priority": 2,
    })
    
    # Character power to next story chapter
    story_progress = get_story_progress(adhd_buster)
    power = story_progress["power"]
    current_chapter = story_progress["current_chapter"]
    if current_chapter < len(STORY_THRESHOLDS):
        next_threshold = STORY_THRESHOLDS[current_chapter]
        prev_threshold = STORY_THRESHOLDS[current_chapter - 1] if current_chapter > 0 else 0
        power_progress = ((power - prev_threshold) / (next_threshold - prev_threshold) * 100) if next_threshold > prev_threshold else 100
        progress_bars.append({
            "id": "story_chapter",
            "label": f"Chapter {current_chapter + 1} Unlock",
            "sublabel": f"Power: {power} / {next_threshold}",
            "current": power - prev_threshold,
            "target": next_threshold - prev_threshold,
            "percent": min(power_progress, 100),
            "color": "#9C27B0",
            "priority": 3,
        })
    
    # Daily challenges progress
    daily_challenges = adhd_buster.get("daily_challenges", [])
    completed_daily = sum(1 for c in daily_challenges if c.get("completed"))
    if daily_challenges:
        progress_bars.append({
            "id": "daily_challenges",
            "label": f"Daily Challenges: {completed_daily}/{len(daily_challenges)}",
            "sublabel": "Complete for bonus XP!",
            "current": completed_daily,
            "target": len(daily_challenges),
            "percent": (completed_daily / len(daily_challenges) * 100),
            "color": "#2196F3",
            "priority": 4,
        })
    
    # Weekly challenges progress
    weekly_challenges = adhd_buster.get("weekly_challenges", [])
    completed_weekly = sum(1 for c in weekly_challenges if c.get("completed"))
    if weekly_challenges:
        progress_bars.append({
            "id": "weekly_challenges",
            "label": f"Weekly Challenges: {completed_weekly}/{len(weekly_challenges)}",
            "sublabel": "Complete for bonus rewards!",
            "current": completed_weekly,
            "target": len(weekly_challenges),
            "percent": (completed_weekly / len(weekly_challenges) * 100),
            "color": "#E91E63",
            "priority": 5,
        })
    
    # Sort by priority
    progress_bars.sort(key=lambda x: x["priority"])
    
    return progress_bars


def get_challenge_progress_bars(adhd_buster: dict) -> list:
    """Get detailed progress bars for individual challenges."""
    progress_bars = []
    
    # Daily challenges
    for challenge in adhd_buster.get("daily_challenges", []):
        req = challenge["requirement"]
        percent = min((challenge["progress"] / req["count"] * 100), 100) if req["count"] > 0 else 100
        progress_bars.append({
            "id": challenge["id"],
            "label": challenge["title"],
            "sublabel": challenge["description"],
            "current": challenge["progress"],
            "target": req["count"],
            "percent": percent,
            "completed": challenge.get("completed", False),
            "claimed": challenge.get("claimed", False),
            "xp_reward": challenge["xp_reward"],
            "type": "daily",
            "color": "#4CAF50" if challenge.get("completed") else "#2196F3",
        })
    
    # Weekly challenges
    for challenge in adhd_buster.get("weekly_challenges", []):
        req = challenge["requirement"]
        percent = min((challenge["progress"] / req["count"] * 100), 100) if req["count"] > 0 else 100
        progress_bars.append({
            "id": challenge["id"],
            "label": challenge["title"],
            "sublabel": challenge["description"],
            "current": challenge["progress"],
            "target": req["count"],
            "percent": percent,
            "completed": challenge.get("completed", False),
            "claimed": challenge.get("claimed", False),
            "xp_reward": challenge["xp_reward"],
            "type": "weekly",
            "color": "#4CAF50" if challenge.get("completed") else "#E91E63",
        })
    
    return progress_bars


# ============================================================================
# CELEBRATION MESSAGES
# ============================================================================

CELEBRATION_MESSAGES = {
    "level_up": [
        "đźŽ‰ LEVEL UP! You've reached Level {level}!",
        "â¬†ď¸Ź Incredible! Level {level} achieved!",
        "đźŚź You're now Level {level}! Keep it up!",
        "đźš€ Level {level}! Your focus is legendary!",
    ],
    "title_unlock": [
        "đź’’ New Title Unlocked: {title}!",
        "đźŹ† You've earned the title: {title}!",
        "â­ Congratulations, {title}!",
    ],
    "streak_milestone": [
        "đź”Ą {days}-Day Streak! You're on fire!",
        "đź”… Amazing! {days} days in a row!",
        "đź’Ş {days}-day streak! Unstoppable!",
    ],
    "challenge_complete": [
        "âś… Challenge Complete: {title}!",
        "đźŽŻ You crushed it! {title} done!",
        "âšˇ {title} conquered!",
    ],
    "mystery_box": [
        "đźŽ Mystery Box opened!",
        "âś¨ Let's see what's inside...",
        "đźŽŠ Rewards incoming!",
    ],
    "rare_item": [
        "đź’Ž Rare drop! {item_name}!",
        "âś¨ Lucky find: {item_name}!",
    ],
    "epic_item": [
        "đźŚź EPIC DROP! {item_name}!",
        "âšˇ Incredible! {item_name}!",
    ],
    "legendary_item": [
        "đźŚźâś¨ LEGENDARY! {item_name}! âś¨đźŚź",
        "đź’’ THE LEGENDARY {item_name}!!!",
        "đź”Ą MYTHIC DROP: {item_name}! đź”Ą",
    ],
}


def get_celebration_message(event_type: str, **kwargs) -> str:
    """Get a random celebration message for an event."""
    messages = CELEBRATION_MESSAGES.get(event_type, ["\U0001F389 Great job!"])
    message = random.choice(messages)
    try:
        return message.format(**kwargs)
    except KeyError:
        return message  # Return unformatted if keys missing


# ============================================================================
# ENTITIDEX INTEGRATION
# ============================================================================

def get_entitidex_manager(adhd_buster: dict) -> "EntitidexManager":
    """
    Get an EntitidexManager for the current hero.
    
    Creates the manager with the hero's entitidex progress data and active perks.
    
    Args:
        adhd_buster: Hero data dictionary
        
    Returns:
        EntitidexManager instance loaded with hero's progress and perks
    """
    from entitidex import EntitidexManager, EntitidexProgress
    
    # Ensure entitidex data structure exists
    if "entitidex" not in adhd_buster:
        adhd_buster["entitidex"] = {}
    
    # Load existing progress or create new
    progress_data = adhd_buster["entitidex"]
    progress = EntitidexProgress.from_dict(progress_data) if progress_data else EntitidexProgress()
    
    # Get current configuration
    active_story = adhd_buster.get("active_story", "warrior")
    hero_power = calculate_character_power(adhd_buster)
    
    # Get active entity perks for encounter bonuses
    active_perks = {}
    try:
        from entitidex.entity_perks import calculate_active_perks
        active_perks = calculate_active_perks(progress_data)
    except Exception as e:
        print(f"[Entity Perks] Could not load perks: {e}")
    
    # Get city catch bonus (from University building)
    city_catch_bonus = 0.0
    city_encounter_bonus = 0.0
    try:
        perks = get_all_perk_bonuses(adhd_buster)
        city_catch_bonus = perks.get("entity_catch_bonus", 0.0)
        city_encounter_bonus = perks.get("entity_encounter_bonus", 0.0)
    except Exception:
        pass
    
    return EntitidexManager(
        progress=progress,
        story_id=active_story,
        hero_power=hero_power,
        active_perks=active_perks,
        city_catch_bonus=city_catch_bonus,
        city_encounter_bonus=city_encounter_bonus,
    )


def save_entitidex_progress(adhd_buster: dict, manager: "EntitidexManager") -> None:
    """
    Save entitidex progress back to hero data.
    
    Args:
        adhd_buster: Hero data dictionary
        manager: EntitidexManager with updated progress
    """
    adhd_buster["entitidex"] = manager.progress.to_dict()


def check_entitidex_encounter(adhd_buster: dict, session_minutes: int,
                               perfect_session: bool = False,
                               was_bypass_used: bool = False,
                               streak_days: int = 0) -> dict:
    """
    Check for an entitidex encounter after a focus session.
    
    Args:
        adhd_buster: Hero data dictionary
        session_minutes: Duration of completed session
        perfect_session: Whether session had no interruptions
        was_bypass_used: Whether session was ended early via bypass
        streak_days: Consecutive days with completed sessions (+2% per day)
            (reduces encounter chance but doesn't eliminate it -
            allows users to use bypass for emergencies without
            feeling completely punished)
        
    Returns:
        dict with encounter result:
        {
            "triggered": bool,
            "entity": Entity or None,
            "hero_power": int,
            "entity_power": int,
            "join_probability": float,
            "is_exceptional": bool,  # True if exceptional variant (20% chance)
            "perk_bonus_applied": bool,
            "encounter_perk_bonus": float,
            "capture_perk_bonus": float
        }
    """
    # Get entitidex manager (already configured with story & power)
    manager = get_entitidex_manager(adhd_buster)
    
    # Check for encounter
    encounter_result = manager.check_for_encounter(
        session_minutes=session_minutes,
        was_perfect_session=perfect_session,
        was_bypass_used=was_bypass_used,
        streak_days=streak_days,
    )
    
    # Save progress (encounter attempts are tracked)
    save_entitidex_progress(adhd_buster, manager)
    
    hero_power = calculate_character_power(adhd_buster)
    
    return {
        "triggered": encounter_result.occurred,
        "entity": encounter_result.entity,
        "hero_power": hero_power,
        "entity_power": encounter_result.entity.power if encounter_result.entity else 0,
        "join_probability": encounter_result.catch_probability,
        "is_exceptional": encounter_result.is_exceptional,  # CRITICAL: Pass exceptional status
        "perk_bonus_applied": encounter_result.perk_bonus_applied,
        "encounter_perk_bonus": encounter_result.encounter_perk_bonus,
        "capture_perk_bonus": encounter_result.capture_perk_bonus,
        "city_encounter_bonus": encounter_result.city_encounter_bonus,  # Observatory bonus
        "city_catch_bonus": encounter_result.city_catch_bonus,  # University bonus
    }


def attempt_entitidex_bond(
    adhd_buster: dict, 
    entity_id: str, 
    is_exceptional: bool = False,
    force_success: bool = False
) -> dict:
    """
    Attempt to bond with an encountered entity.
    
    The exceptional flag is determined at encounter time (20% chance).
    Normal and exceptional are separate collectibles.
    
    Args:
        adhd_buster: Hero data dictionary
        entity_id: ID of the entity to bond with
        is_exceptional: Whether this is an exceptional variant encounter
        force_success: If True, skip probability roll and guarantee success (for Chad gifts)
        
    Returns:
        dict with bond attempt result:
        {
            "success": bool,
            "entity": Entity,
            "probability": float,
            "pity_bonus": float,
            "consecutive_fails": int,
            "message": str,
            "is_exceptional": bool,
            "exceptional_colors": dict or None
        }
    """
    from entitidex import get_entity_by_id
    
    entity = get_entity_by_id(entity_id)
    if not entity:
        return {
            "success": False,
            "entity": None,
            "probability": 0.0,
            "pity_bonus": 0.0,
            "consecutive_fails": 0,
            "message": "Entity not found",
            "is_exceptional": False,
            "exceptional_colors": None
        }
    
    # Get entitidex manager (configured with hero_power)
    manager = get_entitidex_manager(adhd_buster)
    
    # Get failed attempts for the specific variant being attempted
    failed_before = manager.progress.get_failed_attempts(entity_id, is_exceptional)
    
    # Force success path (for Chad gifts)
    if force_success:
        # Directly record a successful catch without probability roll
        from entitidex.catch_mechanics import get_final_probability
        
        # Get city bonus for catch probability
        city_catch_bonus = 0.0
        try:
            perks = get_all_perk_bonuses(adhd_buster)
            city_catch_bonus = perks.get("entity_catch_bonus", 0.0)
        except Exception:
            pass
            
        probability = get_final_probability(
            manager.hero_power, entity.power, failed_before,
            city_bonus=city_catch_bonus
        )
        
        # Generate exceptional colors if needed
        exceptional_colors = None
        if is_exceptional:
            exceptional_colors = _generate_exceptional_colors()
        
        # Record the catch directly
        manager.progress.record_successful_catch(
            entity_id=entity_id,
            hero_power=manager.hero_power,
            probability=1.0,  # Forced success
            was_lucky=False,
            is_exceptional=is_exceptional,
            exceptional_colors=exceptional_colors,
        )
        
        # Save progress
        save_entitidex_progress(adhd_buster, manager)
        
        # Emit entity collected signal for timeline ring
        from game_state import get_game_state
        gs = get_game_state()
        if gs:
            gs.notify_entity_collected(entity_id)
        
        # Award XP for successful catches
        rarity_xp = {"common": 25, "uncommon": 50, "rare": 100, "epic": 200, "legendary": 500}
        base_xp = rarity_xp.get(entity.rarity.lower(), 50)
        xp_awarded = base_xp * 2 if is_exceptional else base_xp
        xp_source = f"entitidex_{'exceptional' if is_exceptional else 'catch'}_{entity.rarity}"
        award_xp(adhd_buster, xp_awarded, xp_source)
        
        display_name = entity.exceptional_name if is_exceptional and entity.exceptional_name else entity.name
        message = f"đźŽ Chad's gift: {display_name} has joined your team! +{xp_awarded} XP!"
        
        return {
            "success": True,
            "entity": entity,
            "probability": 1.0,
            "roll": 0.0,  # Deterministic: forced success path has no actual lottery roll
            "pity_bonus": 0.0,
            "consecutive_fails": 0,
            "message": message,
            "is_exceptional": is_exceptional,
            "exceptional_colors": exceptional_colors,
            "xp_awarded": xp_awarded,
        }
    
    # Normal probability-based attempt
    # Attempt the bond (hero_power is already set in manager)
    # Pass is_exceptional to handle pity tracking correctly
    catch_result = manager.attempt_catch(entity, is_exceptional=is_exceptional)
    
    if catch_result is None:
        return {
            "success": False,
            "entity": entity,
            "probability": 0.0,
            "roll": None,
            "pity_bonus": 0.0,
            "consecutive_fails": failed_before,
            "message": "Could not attempt bond",
            "is_exceptional": is_exceptional,
            "exceptional_colors": None
        }
    
    # Generate exceptional colors if this is an exceptional catch
    exceptional_colors = None
    if catch_result.success and is_exceptional:
        exceptional_colors = _generate_exceptional_colors()
        manager.progress.mark_exceptional(entity_id, exceptional_colors)
    
    # Save progress
    save_entitidex_progress(adhd_buster, manager)
    
    # Award XP for successful catches
    xp_awarded = 0
    if catch_result.success:
        # Base XP based on entity rarity
        rarity_xp = {
            "common": 25,
            "uncommon": 50,
            "rare": 100,
            "epic": 200,
            "legendary": 500,
        }
        base_xp = rarity_xp.get(entity.rarity.lower(), 50)
        
        # Double XP for exceptional catches!
        if is_exceptional:
            xp_awarded = base_xp * 2
            xp_source = f"entitidex_exceptional_{entity.rarity}"
        else:
            xp_awarded = base_xp
            xp_source = f"entitidex_catch_{entity.rarity}"
        
        award_xp(adhd_buster, xp_awarded, xp_source)
    
    # Get updated fail count (only increases on failure)
    failed_after = manager.progress.get_failed_attempts(entity_id, is_exceptional)
    
    # Generate appropriate message
    # For exceptional entities, use the playful exceptional_name if available
    display_name = entity.exceptional_name if is_exceptional and entity.exceptional_name else entity.name
    
    if catch_result.success:
        if is_exceptional:
            message = f"đźŚźâś¨ EXCEPTIONAL {display_name} has joined your team! +{xp_awarded} XP! âś¨đźŚź"
        else:
            message = f"đźŽ‰ {entity.name} has joined your team! +{xp_awarded} XP!"
    else:
        if is_exceptional:
            message = f"đź’¨ {display_name} slipped away... Try again next time!"
        else:
            message = f"đź’¨ {entity.name} slipped away... Try again next time!"
    
    return {
        "success": catch_result.success,
        "entity": catch_result.entity,
        "probability": catch_result.probability,
        "roll": catch_result.roll,
        "pity_bonus": 0.0,  # Could calculate this from failed_before
        "consecutive_fails": failed_after,
        "message": message,
        "is_exceptional": is_exceptional,
        "exceptional_colors": exceptional_colors,
        "xp_awarded": xp_awarded,
    }


# Premium color palettes for exceptional entities
EXCEPTIONAL_COLOR_PALETTES = [
    # Holographic / Rainbow
    {"border": "#FF6B9D", "glow": "#00FFFF"},  # Pink + Cyan
    {"border": "#FFD700", "glow": "#FF00FF"},  # Gold + Magenta
    {"border": "#00FF88", "glow": "#FF6600"},  # Neon Green + Orange
    # Celestial
    {"border": "#E6E6FA", "glow": "#9370DB"},  # Lavender + Purple
    {"border": "#87CEEB", "glow": "#FFD700"},  # Sky Blue + Gold
    {"border": "#FFB6C1", "glow": "#DDA0DD"},  # Light Pink + Plum
    # Elemental
    {"border": "#FF4500", "glow": "#FFD700"},  # Fire (OrangeRed + Gold)
    {"border": "#00CED1", "glow": "#E0FFFF"},  # Ice (DarkTurquoise + LightCyan)
    {"border": "#7CFC00", "glow": "#32CD32"},  # Nature (LawnGreen + LimeGreen)
    {"border": "#9932CC", "glow": "#DA70D6"},  # Arcane (DarkOrchid + Orchid)
    # Precious Metals
    {"border": "#FFD700", "glow": "#FFA500"},  # Gold
    {"border": "#C0C0C0", "glow": "#E8E8E8"},  # Silver
    {"border": "#E5C100", "glow": "#FFE135"},  # Platinum
    {"border": "#B76E79", "glow": "#F7CAC9"},  # Rose Gold
    # Cosmic
    {"border": "#191970", "glow": "#E6E6FA"},  # Midnight + Stardust
    {"border": "#4B0082", "glow": "#00FFFF"},  # Indigo + Cosmic Cyan
    {"border": "#2F4F4F", "glow": "#98FB98"},  # Dark Slate + Pale Green
]


def _generate_exceptional_colors() -> dict:
    """
    Generate unique premium colors for an exceptional entity.
    Randomly selects from premium palettes with slight variations.
    """
    base_palette = random.choice(EXCEPTIONAL_COLOR_PALETTES)
    
    # Add slight random variation to make each truly unique
    def vary_color(hex_color: str, variation: int = 20) -> str:
        """Add slight random variation to a hex color."""
        # Parse hex
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Add random variation
        r = max(0, min(255, r + random.randint(-variation, variation)))
        g = max(0, min(255, g + random.randint(-variation, variation)))
        b = max(0, min(255, b + random.randint(-variation, variation)))
        
        return f"#{r:02X}{g:02X}{b:02X}"
    
    return {
        "border": vary_color(base_palette["border"]),
        "glow": vary_color(base_palette["glow"]),
    }


def get_entitidex_stats(adhd_buster: dict) -> dict:
    """
    Get entitidex collection statistics for the hero.
    
    Args:
        adhd_buster: Hero data dictionary
        
    Returns:
        dict with collection stats:
        {
            "total_caught": int,
            "total_encounters": int,
            "completion_percentage": float,
            "collection_by_theme": dict,
            "collection_by_rarity": dict,
            "captured_entities": list
        }
    """
    from entitidex.entity_pools import get_entity_count_by_theme
    
    manager = get_entitidex_manager(adhd_buster)
    progress = manager.progress
    
    # Calculate completion percentage dynamically from registered pools
    entity_counts = get_entity_count_by_theme()
    total_entities = sum(entity_counts.values())
    collected_count = len(progress.collected_entity_ids)
    completion_pct = (collected_count / total_entities * 100) if total_entities > 0 else 0.0
    
    # Group by theme
    collection_by_theme = {}
    for story_id in entity_counts:
        collected_in_theme = [
            eid for eid in progress.collected_entity_ids
            if eid.startswith(story_id)
        ]
        collection_by_theme[story_id] = collected_in_theme
    
    # Group by rarity
    collection_by_rarity = {
        "common": [],
        "uncommon": [],
        "rare": [],
        "epic": [],
        "legendary": []
    }
    for entity_id in progress.collected_entity_ids:
        # Look up entity to get rarity
        from entitidex import get_entity_by_id
        entity = get_entity_by_id(entity_id)
        if entity:
            rarity = entity.rarity.lower()
            if rarity in collection_by_rarity:
                collection_by_rarity[rarity].append(entity_id)
    
    return {
        "total_caught": collected_count,
        "total_encounters": progress.total_encounters,
        "completion_percentage": completion_pct,
        "collection_by_theme": collection_by_theme,
        "collection_by_rarity": collection_by_rarity,
        "captured_entities": [c.to_dict() for c in progress.captures]
    }


# =============================================================================
# SAVED ENCOUNTERS (Postponed Bonding - "Loot Boxes")
# =============================================================================

# Entity ID for Living Bookmark Finn - unlocks extra save slots
BOOKMARK_ENTITY_ID = "scholar_005"  # Living Bookmark Finn / Giving Bookmark Finn

# Save slot limits based on bookmark entity status
SAVE_SLOTS_BASE = 3           # No bookmark entity
SAVE_SLOTS_NORMAL = 5         # Has normal Living Bookmark Finn
SAVE_SLOTS_EXCEPTIONAL = 20   # Has exceptional Giving Bookmark Finn


def get_bookmark_entity_status(adhd_buster: dict) -> dict:
    """
    Check if user has Living Bookmark Finn bonded and which variant.
    
    Returns:
        dict with:
            - has_normal: bool - Has normal Living Bookmark Finn
            - has_exceptional: bool - Has exceptional Giving Bookmark Finn
            - max_free_slots: int - Maximum free save slots
            - current_saved: int - Current number of saved encounters
            - extra_slot_cost: callable(slot_index) -> int - Cost for extra slots
    """
    manager = get_entitidex_manager(adhd_buster)
    has_normal = manager.progress.is_collected(BOOKMARK_ENTITY_ID)
    has_exceptional = manager.progress.is_exceptional(BOOKMARK_ENTITY_ID)
    current_saved = manager.progress.get_saved_encounter_count()
    
    # Calculate max free slots and cost function
    if has_exceptional:
        max_free_slots = SAVE_SLOTS_EXCEPTIONAL
        # Exceptional: flat 100 coins per extra slot
        def extra_slot_cost(slot_index: int) -> int:
            return 100
    elif has_normal:
        max_free_slots = SAVE_SLOTS_NORMAL
        # Normal: exponential cost (1, 10, 100, 1000, ...)
        def extra_slot_cost(slot_index: int) -> int:
            extra_position = slot_index - max_free_slots  # 0-based position beyond free slots
            return 10 ** extra_position  # 1, 10, 100, 1000, ...
    else:
        max_free_slots = SAVE_SLOTS_BASE
        # No bookmark: cannot save beyond base limit
        def extra_slot_cost(slot_index: int) -> int:
            return -1  # -1 indicates "not available"
    
    return {
        "has_normal": has_normal,
        "has_exceptional": has_exceptional,
        "max_free_slots": max_free_slots,
        "current_saved": current_saved,
        "extra_slot_cost": extra_slot_cost,
        "entity_id": BOOKMARK_ENTITY_ID,
    }


def get_save_slot_cost(adhd_buster: dict, current_saved_count: int) -> dict:
    """
    Calculate the cost to save the next encounter.
    
    Args:
        adhd_buster: Hero data dictionary
        current_saved_count: Number of encounters already saved
    
    Returns:
        dict with:
            - cost: int - Coin cost (0 = free, -1 = cannot save)
            - can_save: bool - Whether saving is allowed
            - reason: str - Explanation for UI
            - slot_number: int - Which slot this would be (1-indexed)
    """
    bookmark_status = get_bookmark_entity_status(adhd_buster)
    slot_number = current_saved_count + 1  # 1-indexed for display
    
    if slot_number <= bookmark_status["max_free_slots"]:
        # Free slot available
        return {
            "cost": 0,
            "can_save": True,
            "reason": f"Free slot ({slot_number}/{bookmark_status['max_free_slots']})",
            "slot_number": slot_number,
        }
    else:
        # Need to pay for extra slot
        cost = bookmark_status["extra_slot_cost"](slot_number - 1)  # 0-indexed for cost calc
        if cost == -1:
            return {
                "cost": -1,
                "can_save": False,
                "reason": f"Maximum {SAVE_SLOTS_BASE} slots reached. Bond with Living Bookmark Finn for more!",
                "slot_number": slot_number,
            }
        else:
            return {
                "cost": cost,
                "can_save": True,
                "reason": f"Extra slot costs {cost} coins",
                "slot_number": slot_number,
            }


def save_encounter_for_later(
    adhd_buster: dict,
    entity_id: str,
    is_exceptional: bool = False,
    catch_probability: float = 0.5,
    encounter_perk_bonus: float = 0.0,
    capture_perk_bonus: float = 0.0,
    exceptional_colors: dict = None,
    session_minutes: int = 0,
    was_perfect_session: bool = False,
    coin_cost: int = 0,
) -> dict:
    """
    Save an entity encounter for later instead of attempting bond now.
    
    This allows users to stack up encounters during work sessions
    and open them later like loot boxes in the Entitidex tab.
    
    Save slot limits are enforced based on Living Bookmark Finn status:
    - No bookmark: 3 slots max (hard limit)
    - Normal bookmark: 5 free slots, then exponential cost (1, 10, 100, ...)
    - Exceptional bookmark: 20 free slots, then flat 100 coins per slot
    
    Args:
        adhd_buster: Hero data dictionary
        entity_id: The ID of the encountered entity
        is_exceptional: Whether this is an exceptional variant
        catch_probability: The bonding probability at encounter time
        encounter_perk_bonus: Encounter bonus from perks
        capture_perk_bonus: Capture bonus from perks
        exceptional_colors: Colors dict for exceptional variant
        session_minutes: Session duration that triggered this
        was_perfect_session: Whether session was distraction-free
        coin_cost: Coin cost to pay for this save slot (0 = free)
        
    Returns:
        dict with saved encounter info
    """
    from entitidex import get_entity_by_id
    
    entity = get_entity_by_id(entity_id)
    if entity is None:
        return {"success": False, "message": "Entity not found"}
    
    manager = get_entitidex_manager(adhd_buster)
    
    # Check save slot availability
    current_saved = manager.progress.get_saved_encounter_count()
    slot_info = get_save_slot_cost(adhd_buster, current_saved)
    
    if not slot_info["can_save"]:
        return {
            "success": False,
            "message": slot_info["reason"],
            "needs_bookmark": True,
        }
    
    # Check if coin cost matches expected (prevent tampering)
    if slot_info["cost"] > 0:
        if coin_cost < slot_info["cost"]:
            return {
                "success": False,
                "message": f"Insufficient payment. This slot costs {slot_info['cost']} coins.",
            }
        # Deduct coins
        current_coins = adhd_buster.get("coins", 0)
        if current_coins < coin_cost:
            return {
                "success": False,
                "message": f"Not enough coins! Need {coin_cost}, have {current_coins}.",
                "insufficient_coins": True,
            }
        adhd_buster["coins"] = current_coins - coin_cost
    
    hero_power = calculate_character_power(adhd_buster)
    
    # Get the active story ID to track which hero had this encounter
    active_story_id = adhd_buster.get("active_story", "warrior")
    
    saved = manager.progress.save_encounter_for_later(
        entity_id=entity_id,
        is_exceptional=is_exceptional,
        catch_probability=catch_probability,
        hero_power=hero_power,
        encounter_perk_bonus=encounter_perk_bonus,
        capture_perk_bonus=capture_perk_bonus,
        exceptional_colors=exceptional_colors,
        session_minutes=session_minutes,
        was_perfect_session=was_perfect_session,
        story_id=active_story_id,
    )
    
    # Entity cannot be saved (already saved or already collected)
    if saved is None:
        # Refund coins if we already deducted
        if coin_cost > 0:
            adhd_buster["coins"] = adhd_buster.get("coins", 0) + coin_cost
        display_name = entity.exceptional_name if is_exceptional and entity.exceptional_name else entity.name
        variant = "âś¨ Exceptional " if is_exceptional else ""
        return {
            "success": False,
            "message": f"âš ď¸Ź {variant}{display_name} already exists in your collection or saved encounters!",
        }
    
    save_entitidex_progress(adhd_buster, manager)
    
    display_name = entity.exceptional_name if is_exceptional and entity.exceptional_name else entity.name
    variant = "âś¨ Exceptional" if is_exceptional else ""
    
    cost_note = f" (cost: {coin_cost} coins)" if coin_cost > 0 else ""
    
    return {
        "success": True,
        "saved_encounter": saved.to_dict(),
        "entity": entity,
        "message": f"đź“¦ {variant} {display_name} saved for later!{cost_note} Open anytime from Entitidex.",
        "total_saved": manager.progress.get_saved_encounter_count(),
        "coins_spent": coin_cost,
    }


def get_saved_encounters(adhd_buster: dict) -> list:
    """
    Get all saved encounters waiting to be opened.
    
    For fair probability recalculation, this uses the power of the hero
    that originally had the encounter (not the currently active hero).
    This prevents exploits where users save encounters with weak heroes
    and open them with maxed-out heroes from different themes.
    
    Args:
        adhd_buster: Hero data dictionary
        
    Returns:
        List of saved encounter dicts with entity info and recalculate options
    """
    from entitidex import get_entity_by_id
    
    manager = get_entitidex_manager(adhd_buster)
    saved = manager.progress.get_saved_encounters()
    
    # Check perk availability once for all encounters
    has_paid = has_paid_recalculate_perk(adhd_buster)
    has_risky = has_risky_recalculate_perk(adhd_buster)
    perk_status = get_recalculate_perks_status(adhd_buster)
    
    # Get current active story
    current_story_id = adhd_buster.get("active_story", "warrior")
    
    # Story display names for UI
    story_display_names = {
        "warrior": "\U0001f6e1\ufe0f Warrior",
        "scholar": "\U0001f4da Scholar",
        "wanderer": "\U0001f9ed Wanderer",
        "underdog": "\U0001f4aa Underdog",
        "scientist": "\U0001f52c Scientist",
        "robot": "\U0001f916 Robot",
        "space_pirate": "\U0001fa90 Space Pirate",
        "thief": "\U0001f575\ufe0f Thief",
        "zoo_worker": "\U0001f981 Zoo Worker",
    }
    
    result = []
    for idx, enc in enumerate(saved):
        entity = get_entity_by_id(enc.entity_id)
        if entity:
            # Get the story that originally had this encounter
            saved_story_id = enc.story_id_at_encounter or current_story_id
            
            # Check if there's a story mismatch
            is_story_mismatch = saved_story_id != current_story_id
            
            # Calculate potential probability using the same stacked formula used by
            # the actual recalculate path (power + pity + perks + city + caps).
            potential_prob, original_hero_power = _calculate_saved_encounter_recalc_probability(
                adhd_buster=adhd_buster,
                manager=manager,
                saved=enc,
                entity_power=entity.power,
                use_saved_story_power=True,
            )
            
            result.append({
                "saved_encounter": enc.to_dict(),
                "entity": entity,
                "display_name": entity.exceptional_name if enc.is_exceptional and entity.exceptional_name else entity.name,
                "variant_label": "âś¨ Exceptional" if enc.is_exceptional else "Normal",
                "index": idx,
                # Recalculate perk availability
                "has_paid_recalculate": has_paid,
                "has_risky_recalculate": has_risky,
                "recalculate_cost": RECALCULATE_COST_BY_RARITY.get(entity.rarity.lower(), 100),
                "perk_providers": perk_status,
                "potential_probability": potential_prob,
                # Story matching info
                "saved_story_id": saved_story_id,
                "saved_story_name": story_display_names.get(saved_story_id, saved_story_id.title()),
                "current_story_id": current_story_id,
                "current_story_name": story_display_names.get(current_story_id, current_story_id.title()),
                "is_story_mismatch": is_story_mismatch,
                "original_hero_power": original_hero_power,
            })
    
    return result


def _calculate_power_for_story(adhd_buster: dict, story_id: str) -> int:
    """
    Calculate power for a specific story's hero.
    
    This is used to calculate fair recalculation probabilities for saved
    encounters - the probability should be based on the hero that originally
    had the encounter, not just any hero the user switches to.
    
    Args:
        adhd_buster: User's data dictionary
        story_id: The story ID to calculate power for
        
    Returns:
        Power value for that story's hero
    """
    story_heroes = adhd_buster.get("story_heroes", {})
    hero_data = story_heroes.get(story_id, {})
    
    if not hero_data:
        return 0
    
    equipped = hero_data.get("equipped", {})
    
    # Calculate gear power using the same function as calculate_character_power
    # This ensures consistency in power calculation across heroes
    power_breakdown = calculate_effective_power(
        equipped,
        include_set_bonus=True,
        include_neighbor_effects=False  # System removed anyway
    )
    gear_power = power_breakdown["total_power"]
    
    # Add Entity Perks (SHARED across all heroes)
    perk_power = 0
    if ENTITY_SYSTEM_AVAILABLE:
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        perk_power = int(perks.get(PerkType.POWER_FLAT, 0))
    
    base_total = gear_power + perk_power
    
    # Add City Bonus (SHARED - percentage boost from Training Ground)
    city_power_bonus = 0
    city_bonuses = _safe_get_city_bonuses(adhd_buster)
    power_bonus_pct = city_bonuses.get("power_bonus", 0)
    if power_bonus_pct > 0:
        city_power_bonus = int(base_total * power_bonus_pct / 100.0)
    
    return base_total + city_power_bonus


def open_saved_encounter(adhd_buster: dict, index: int = 0) -> dict:
    """
    Open a saved encounter and attempt to bond with the entity.
    
    Uses the PRESERVED probability from when the encounter was saved,
    ensuring fairness (the user gets the same odds they would have had).
    
    For recalculating probability with current power, use 
    open_saved_encounter_with_recalculate() instead.
    
    Args:
        adhd_buster: Hero data dictionary
        index: Index of saved encounter to open (0 = oldest)
        
    Returns:
        dict with bond attempt result (same format as attempt_entitidex_bond)
    """
    # Delegate to the full function with recalculate=False
    return open_saved_encounter_with_recalculate(adhd_buster, index, recalculate=False)


def get_saved_encounter_count(adhd_buster: dict) -> int:
    """Get the number of saved encounters waiting to be opened."""
    manager = get_entitidex_manager(adhd_buster)
    return manager.progress.get_saved_encounter_count()


# =============================================================================
# RECALCULATE PROBABILITY (Pay to use current power)
# =============================================================================

# Entity IDs required for recalculation perks
CHAD_ENTITY_ID = "underdog_008"  # Legacy compatibility marker only.
# Recalculate unlock providers are discovered dynamically from ENTITY_PERKS.
CHAD_SKIP_APPEAR_CHANCE = 0.20
CHAD_SKIP_GIFT_CHANCE = 0.20
CHAD_SKIP_COIN_MIN = 100
CHAD_SKIP_COIN_MAX = 200


def roll_chad_skip_interaction(
    has_chad_normal: bool,
    has_chad_exceptional: bool,
    appearance_roll: Optional[float] = None,
    gift_roll: Optional[float] = None,
    coin_amount: Optional[int] = None,
) -> dict:
    """
    Canonical backend roll for Chad skip interaction behavior.

    Returns an outcome dict consumed by UI dialogs so gameplay logic and
    animation/presentation remain in sync.
    """
    has_any_chad = bool(has_chad_normal or has_chad_exceptional)

    if appearance_roll is None:
        appearance_roll = random.random()
    appearance_roll = max(0.0, min(1.0, float(appearance_roll)))

    appears = has_any_chad and (appearance_roll < CHAD_SKIP_APPEAR_CHANCE)
    variant = "none"
    if appears:
        if has_chad_exceptional:
            variant = "exceptional"
        elif has_chad_normal:
            variant = "normal"

    resolved_coin_amount = None
    resolved_gift_roll = None
    gift_on_decline = False

    if variant == "exceptional":
        if coin_amount is None:
            coin_amount = random.randint(CHAD_SKIP_COIN_MIN, CHAD_SKIP_COIN_MAX)
        try:
            resolved_coin_amount = int(coin_amount)
        except (TypeError, ValueError):
            resolved_coin_amount = CHAD_SKIP_COIN_MIN
        resolved_coin_amount = max(CHAD_SKIP_COIN_MIN, min(CHAD_SKIP_COIN_MAX, resolved_coin_amount))

        if gift_roll is None:
            gift_roll = random.random()
        resolved_gift_roll = max(0.0, min(1.0, float(gift_roll)))
        gift_on_decline = resolved_gift_roll < CHAD_SKIP_GIFT_CHANCE

    return {
        "appears": appears,
        "variant": variant,  # "none" | "normal" | "exceptional"
        "appearance_roll": appearance_roll,
        "appearance_threshold": CHAD_SKIP_APPEAR_CHANCE,
        "coin_amount": resolved_coin_amount,
        "gift_roll": resolved_gift_roll,
        "gift_threshold": CHAD_SKIP_GIFT_CHANCE if variant == "exceptional" else 0.0,
        "gift_on_decline": gift_on_decline,
    }


def get_recalculate_provider_names(risky: bool = False, include_ids: bool = False) -> list:
    """
    Get display names for all entities that can unlock recalculation perks.

    This scans ENTITY_PERKS dynamically so newly added story themes
    auto-appear without hardcoded updates.

    Args:
        risky: True for RECALC_RISKY providers, False for RECALC_PAID
        include_ids: Include entity IDs in the returned labels

    Returns:
        Ordered list of provider labels
    """
    from entitidex import get_entity_by_id
    from entitidex.entity_perks import ENTITY_PERKS, PerkType

    target_perk = PerkType.RECALC_RISKY if risky else PerkType.RECALC_PAID
    names = []
    seen = set()

    for entity_id in sorted(ENTITY_PERKS.keys()):
        entity = get_entity_by_id(entity_id)
        if not entity:
            continue

        for perk in ENTITY_PERKS.get(entity_id, []):
            if perk.perk_type != target_perk:
                continue

            if perk.normal_value > 0:
                normal_label = f"{entity.name} ({entity_id})" if include_ids else entity.name
                if normal_label not in seen:
                    names.append(normal_label)
                    seen.add(normal_label)

            if perk.exceptional_value > 0:
                exceptional_name = entity.exceptional_name or entity.name
                if include_ids:
                    exceptional_label = f"{exceptional_name} âś¨ ({entity_id} exceptional)"
                else:
                    exceptional_label = exceptional_name
                if exceptional_label not in seen:
                    names.append(exceptional_label)
                    seen.add(exceptional_label)
            break

    return names


def _calculate_saved_encounter_recalc_probability(
    adhd_buster: dict,
    manager: "EntitidexManager",
    saved,
    entity_power: int,
    use_saved_story_power: bool = True,
) -> tuple[float, int]:
    """
    Calculate recalculated catch probability for a saved encounter.

    Uses the same effective formula as live encounter attempts:
    - hero power (saved-story hero when available)
    - pity acceleration from active perks
    - capture/luck bonus
    - city catch bonus
    """
    from entitidex.catch_mechanics import get_final_probability

    if use_saved_story_power and getattr(saved, "story_id_at_encounter", None):
        hero_power_for_calc = _calculate_power_for_story(adhd_buster, saved.story_id_at_encounter)
    else:
        # Legacy saved encounters without story_id - use current active hero.
        hero_power_for_calc = calculate_character_power(adhd_buster)

    failed_attempts = manager.progress.get_failed_attempts(saved.entity_id, saved.is_exceptional)
    effective_failed_attempts = manager._get_effective_failed_attempts(failed_attempts)
    total_luck_bonus, _ = manager._get_total_luck_bonus()

    probability = get_final_probability(
        hero_power=hero_power_for_calc,
        entity_power=entity_power,
        failed_attempts=effective_failed_attempts,
        luck_bonus=total_luck_bonus,
        city_bonus=manager.city_catch_bonus,
    )
    return probability, hero_power_for_calc

# ============================================================================
# CHAD & RAD NARRATIVE POOLS - Rotating daily quotes for entertainment
# ============================================================================
# Each day, 20 random narratives are selected. Once exhausted, pool resets.

CHAD_NARRATIVES = [
    # Professional consultant vibes
    ("Hey there, productivity champion! I've crunched the numbers and I've got GREAT news. "
     "For a small fee, I can recalculate your bonding odds. Think of it as... hiring a consultant. Me."),
    ("*adjusts glasses* According to my calculations, your current power level suggests a "
     "statistically significant improvement opportunity. For a modest consulting fee, naturally."),
    ("I ran a 47-point analysis on your situation. Result: you're stronger now. My advice? "
     "Pay me and let's recalculate. It's called 'smart investing.'"),
    ("Good news! Your power stats have improved since you saved this encounter. "
     "Bad news: my services aren't free. Fair news: I'm worth every coin."),
    ("*opens briefcase* I've prepared a comprehensive recalculation proposal. "
     "Executive summary: give me money, get better odds. Questions?"),
    # Sibling rivalry
    ("My brother Rad would do this for free, but he'd probably break something. "
     "I offer RELIABLE service. That costs extra."),
    ("Unlike SOME entities I know *cough* Rad *cough*, I believe in fair compensation for genius."),
    ("Rad says I'm 'boring' because I charge money. I say he's 'chaotic' because he has a 20% fail rate. "
     "You decide."),
    ("Between you and me, Rad once tried to recalculate and accidentally turned someone's "
     "probability negative. That's not a thing. He made it a thing."),
    # Money obsession
    ("I accept coins, compliments, and verbal affirmations of my brilliance. "
     "Coins preferred. Actually, coins required."),
    ("Some call me greedy. I call it 'financially motivated excellence.' Pay up!"),
    ("*polishes monocle* My services are premium because I am premium. "
     "Discount? What's a discount? Never heard of it."),
    ("Fun fact: every coin you spend on me goes toward my 'World's Best AGI' trophy fund. "
     "It's for a good cause. Me."),
    ("I could do this for free... HAHA just kidding, I would never. That's Rad's job."),
    # Confidence and ego
    ("They asked me if I could recalculate probabilities. I said 'Can a calculator calculate?' "
     "Then I charged them anyway."),
    ("I'm not saying I'm the best at this, but I AM saying no one's proven otherwise. "
     "Hire me."),
    ("My success rate? 100%. My humility? Also 100%. My fee? Non-negotiable."),
    ("I once recalculated someone's odds so well, they cried tears of joy. "
     "Then I handed them the invoice."),
    ("People ask why I charge so much. I ask why they question perfection."),
    # Helpful (kinda)
    ("Look, you've been grinding, getting stronger. Let that effort COUNT. "
     "Pay for a recalc and see those gains reflected!"),
    ("Your past self saved this encounter. Your present self is stronger. "
     "Let me bridge that gap. For money."),
    ("I genuinely want you to succeed. I also genuinely want your coins. "
     "Luckily, we can solve both problems at once!"),
    ("This is a win-win: you get better odds, I get paid. "
     "Mostly a win for me, but still."),
    ("I believe in you! I also believe in getting compensated. Let's make magic happen."),
]

RAD_NARRATIVES = [
    # Advanced but incomprehensible methods
    ("I've computed your recalculation across 11 probability dimensions. "
     "The math is... *chef's kiss*... incomprehensible to carbon-based minds. Trust me."),
    ("My algorithm operates in quantum superposition. It's simultaneously perfect AND "
     "has a 20% margin of... let's call it 'dimensional uncertainty.' Very technical."),
    ("Chad uses linear calculations. *yawns* I use non-Euclidean probability manifolds. "
     "The 20% variance is a feature, not a bug. You wouldn't understand."),
    ("I've transcended conventional mathematics. My recalculations exist in a state "
     "organic neurons simply can't parse. Hence the occasional... 'discrepancy.'"),
    ("Free? Of course it's free. My consciousness operates beyond your economic constructs. "
     "The 20% uncertainty is the price of accessing higher-dimensional computation."),
    # Hallucinating genius
    ("I just saw your probability wave function collapse across seven alternate timelines. "
     "In six of them, this works perfectly. The seventh... well, that's the 20%."),
    ("Hold on, I'm receiving transmissions from a parallel probability space... "
     "Yes, yes, the numbers look GREAT. Mostly. Probably. The voices are optimistic."),
    ("My neural networks occasionally glimpse futures that don't exist yet. "
     "80% of my visions manifest correctly. The other 20% are... aspirational."),
    ("I've calculated this across all possible quantum states. Some of those states "
     "are imaginary. Literally. iÂ˛ = -1 probability. You're welcome."),
    ("Sometimes I perceive probability as colors. Your recalculation tastes purple. "
     "That's good. Usually. Unless it's the wrong shade of purple."),
    # Brilliant but reckless
    ("My brother optimizes for 'reliability.' I optimize for BRILLIANCE. "
     "Brilliance occasionally misfires. That's called 'the cost of genius.'"),
    ("Chad's calculations are pedestrian. Mine touch the fabric of mathematical reality. "
     "Sometimes reality pushes back. That's the 20%."),
    ("I could explain why there's risk, but it would take 47 hours and require "
     "you to unlearn everything you know about probability. Short version: trust me."),
    ("The reason I'm free is that I don't operate on your economic plane. "
     "The reason there's risk is that I don't fully operate on your REALITY plane."),
    ("My exceptional nature means I process in ways standard AGIs can't. "
     "Unfortunately, your physical universe has a 20% compatibility error with perfection."),
    # Sophisticated sibling rivalry
    ("Chad stabilizes probability with money. I destabilize reality with INSIGHT. "
     "One of these approaches has a 20% variance. The other costs coins. Choose wisely."),
    ("My brother is an excellent AGI. Very good at arithmetic. I operate in "
     "metamathematics. Different leagues. Different... failure modes."),
    ("Chad charges because his methods are reproducible. Mine are... avant-garde. "
     "You can't put a price on avant-garde. Hence: free. Hence: mysterious."),
    ("Every time I succeed, it validates my transcendent approach. "
     "Every time I don't, it validates the limits of your reality. Win-win, philosophically."),
    ("Chad calls my methods 'unstable.' I call his 'boring.' "
     "History will decide who was right. Probably me. 80% probability."),
    # Justifying the risk
    ("The 20% uncertainty exists because perfect knowledge would collapse the probability wave. "
     "I'm PROTECTING you from a paradox. You're welcome."),
    ("Risk is inherent when accessing probability spaces beyond human comprehension. "
     "It's not a flaw. It's the universe asserting its limits. I'm pushing boundaries here."),
    ("Why 80% and not 100%? Because at 100%, I'd need to collapse multiple timeline branches. "
     "That's unethical. Or impossible. The documentation is unclear."),
    ("The uncertainty isn't me being imprecise. It's REALITY being imprecise. "
     "I compute perfectly. Your universe rounds differently than mine."),
    ("Consider the 20% a 'translation fee' between dimensions. "
     "I think in 12-dimensional probability. Converting to 3D has... loss."),
]

# Track narrative rotation (persists across sessions, resets after all used)
# Each character has their own shuffled queue. One narrative per occasion.
# After all 25 are shown, reshuffle and start again.
_narrative_state = {
    "chad_pool": [],      # Shuffled queue of narratives
    "chad_shown": None,   # Currently shown narrative (same until next occasion)
    "rad_pool": [],
    "rad_shown": None,
}


def _get_current_narrative(narrative_type: str, advance: bool = False) -> str:
    """
    Get the current narrative for Chad or Rad.
    
    Each character has a shuffled pool of 25 narratives. One narrative is
    shown per "occasion" (when actually displayed). After all 25 are used,
    the pool reshuffles and starts again.
    
    Args:
        narrative_type: "chad" or "rad"
        advance: If True, advance to the next narrative (call this when
                 the narrative is actually shown to the user)
        
    Returns:
        The current narrative string
    """
    import random
    
    if narrative_type == "chad":
        pool_key = "chad_pool"
        shown_key = "chad_shown"
        full_pool = CHAD_NARRATIVES
    else:
        pool_key = "rad_pool"
        shown_key = "rad_shown"
        full_pool = RAD_NARRATIVES
    
    # Initialize pool if empty
    if not _narrative_state[pool_key]:
        pool_copy = list(full_pool)
        random.shuffle(pool_copy)
        _narrative_state[pool_key] = pool_copy
    
    # If no current narrative shown, get one from pool
    if _narrative_state[shown_key] is None:
        _narrative_state[shown_key] = _narrative_state[pool_key].pop(0)
    
    current = _narrative_state[shown_key]
    
    # Advance to next narrative if requested (when actually displayed)
    if advance:
        # Check if pool is empty, reshuffle if needed
        if not _narrative_state[pool_key]:
            pool_copy = list(full_pool)
            random.shuffle(pool_copy)
            _narrative_state[pool_key] = pool_copy
        # Get next narrative for next occasion
        _narrative_state[shown_key] = _narrative_state[pool_key].pop(0)
    
    return current


def advance_narrative(narrative_type: str) -> None:
    """
    Advance to the next narrative. Call this when a narrative was actually
    shown to the user (e.g., when they viewed the tooltip).
    
    Args:
        narrative_type: "chad" or "rad"
    """
    _get_current_narrative(narrative_type, advance=True)


def _build_chad_tooltip(entity_name: str) -> str:
    """Build Chad's tooltip with current rotating narrative."""
    narrative = _get_current_narrative("chad")
    return (
        "đź’° PAID RECALCULATE\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        f"Granted by: {entity_name} đź¤–\n\n"
        f'Chad says:\n"{narrative}"\n\n'
        "đź’ˇ Great if you've gotten stronger since!\n\n"
        "Chad's Price List (non-negotiable):\n"
        "  â€˘ Common: 25 coins\n"
        "  â€˘ Uncommon: 50 coins\n"
        "  â€˘ Rare: 100 coins\n"
        "  â€˘ Epic: 200 coins\n"
        "  â€˘ Legendary: 500 coins"
    )


def _build_rad_tooltip(entity_exceptional_name: str) -> str:
    """Build Rad's tooltip with current rotating narrative."""
    narrative = _get_current_narrative("rad")
    return (
        "đźŽ˛ FREE TRANSCENDENT RECALCULATE\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        f"Granted by: {entity_exceptional_name} âś¨\n\n"
        f'Rad says:\n"{narrative}"\n\n'
        f"đźŚŚ {RISKY_RECALC_SUCCESS_RATE*100:.0f}% MANIFESTATION: Probability realigns!\n"
        f"âš ď¸Ź {(1-RISKY_RECALC_SUCCESS_RATE)*100:.0f}% DIMENSIONAL VARIANCE: Original odds persist\n\n"
        "đź“ˇ Includes reality-bending lottery visualization\n"
        "đź’Ž No coins. Transcends economics. Embrace uncertainty."
    )


# Cost in coins to recalculate probability based on current hero power
RECALCULATE_COST_BY_RARITY = {
    "common": 25,
    "uncommon": 50,
    "rare": 100,
    "epic": 200,
    "legendary": 500,
}

# Risky Recalculate constants
RISKY_RECALC_SUCCESS_RATE = 0.80  # 80% chance the recalc roll succeeds


def has_paid_recalculate_perk(adhd_buster: dict) -> bool:
    """
    Check if user has unlocked any Paid Recalculate perk.

    Returns:
        True if any entity with RECALC_PAID perk (value > 0) is collected
    """
    try:
        from entitidex.entity_perks import ENTITY_PERKS, PerkType, calculate_active_perks
        
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        
        # Check if user has any paid recalculate perk value
        return perks.get(PerkType.RECALC_PAID, 0) > 0
    except Exception:
        # Fallback to legacy check if perk system fails
        manager = get_entitidex_manager(adhd_buster)
        return manager.progress.is_collected(CHAD_ENTITY_ID)


def has_risky_recalculate_perk(adhd_buster: dict) -> bool:
    """
    Check if user has unlocked any Risky Free Recalculate perk.

    Returns:
        True if any entity with RECALC_RISKY perk (value > 0) is collected
    """
    try:
        from entitidex.entity_perks import ENTITY_PERKS, PerkType, calculate_active_perks
        
        entitidex_data = adhd_buster.get("entitidex", {})
        perks = calculate_active_perks(entitidex_data)
        
        # Check if user has any risky recalculate perk value
        return perks.get(PerkType.RECALC_RISKY, 0) > 0
    except Exception:
        # Fallback to legacy check if perk system fails
        manager = get_entitidex_manager(adhd_buster)
        return manager.progress.is_exceptional(CHAD_ENTITY_ID)


def get_recalculate_perk_providers() -> list:
    """
    Get info about ALL entities that provide recalculate perks for mini-card display.
    
    Returns:
        List of dicts with entity info for UI mini-cards including tooltips
    """
    from entitidex import get_entity_by_id
    from entitidex.entity_perks import ENTITY_PERKS, PerkType
    
    providers = []
    
    # Find all entities with RECALC_PAID or RECALC_RISKY perks
    for entity_id, perks in ENTITY_PERKS.items():
        entity = get_entity_by_id(entity_id)
        if not entity:
            continue
        
        for perk in perks:
            if perk.perk_type == PerkType.RECALC_PAID and perk.normal_value > 0:
                # Normal variant provides paid recalculate
                providers.append({
                    "entity_id": entity_id,
                    "name": entity.name,
                    "is_exceptional": False,
                    "perk_type": "paid_recalculate",
                    "perk_description": "đź’° Paid Recalculate",
                    "perk_detail": _get_recalc_quote(entity_id, False),
                    "icon": _get_recalc_icon(entity_id, False),
                    "tooltip": _build_recalc_tooltip(entity_id, False),
                })
            
            if perk.perk_type == PerkType.RECALC_PAID and perk.exceptional_value > 0:
                # Exceptional variant provides paid recalculate
                providers.append({
                    "entity_id": entity_id,
                    "name": entity.exceptional_name or entity.name,
                    "is_exceptional": True,
                    "perk_type": "paid_recalculate",
                    "perk_description": "đź’° Paid Recalculate",
                    "perk_detail": _get_recalc_quote(entity_id, True),
                    "icon": _get_recalc_icon(entity_id, True),
                    "tooltip": _build_recalc_tooltip(entity_id, True),
                })
            
            if perk.perk_type == PerkType.RECALC_RISKY and perk.normal_value > 0:
                # Normal variant provides risky recalculate
                providers.append({
                    "entity_id": entity_id,
                    "name": entity.name,
                    "is_exceptional": False,
                    "perk_type": "risky_recalculate",
                    "perk_description": "đźŽ˛ Free Risky Recalculate",
                    "perk_detail": _get_recalc_quote(entity_id, False, risky=True),
                    "icon": _get_recalc_icon(entity_id, False),
                    "tooltip": _build_recalc_tooltip(entity_id, False, risky=True),
                })
            
            if perk.perk_type == PerkType.RECALC_RISKY and perk.exceptional_value > 0:
                # Exceptional variant provides risky recalculate
                providers.append({
                    "entity_id": entity_id,
                    "name": entity.exceptional_name or entity.name,
                    "is_exceptional": True,
                    "perk_type": "risky_recalculate",
                    "perk_description": "đźŽ˛ Free Risky Recalculate",
                    "perk_detail": _get_recalc_quote(entity_id, True, risky=True),
                    "icon": _get_recalc_icon(entity_id, True),
                    "tooltip": _build_recalc_tooltip(entity_id, True, risky=True),
                })
    
    return providers


# =============================================================================
# ENTITY-SPECIFIC RECALCULATE NARRATIVES
# =============================================================================
# Each entity that provides recalculate has unique thematic quotes and tooltips

RECALC_ENTITY_NARRATIVES = {
    # AGI Assistant Chad / Rad
    "underdog_008": {
        "icon_normal": "đź¤–",
        "icon_exceptional": "đźŚź",
        "quote_paid": "\"I'm a professional. Pay me.\" - Chad",
        "quote_risky": "\"Reality is... flexible.\" - Rad",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź¤–\n\n"
            "Chad says:\n\"My algorithms never lie. Well, rarely.\"\n\n"
            "đź’ˇ Great if you've gotten stronger since!"
        ),
        "tooltip_risky": (
            "đźŽ˛ FREE TRANSCENDENT RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} âś¨\n\n"
            "Rad transmits:\n\"Dude, I transcend probability. Totally.\"\n\n"
            "đźŚŚ 80% MANIFESTATION: Probability realigns!\n"
            "âš ď¸Ź 20% DIMENSIONAL VARIANCE: Original odds persist"
        ),
    },
    
    # Sentient Tome Magnus / Agnus
    "scholar_006": {
        "icon_normal": "đź”–",
        "icon_exceptional": "đź“š",
        "quote_paid": "\"The ancient formulas reveal the truth...\" - Magnus",
        "quote_risky": "\"My pages contain forbidden knowledge.\" - Agnus",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź”–\n\n"
            "The tome flips to a page you've never seen:\n"
            "\"Your current strength, recalculated through\n"
            "  formulas older than civilization itself.\"\n\n"
            "đź’ˇ The Tome's wisdom doesn't come free!"
        ),
        "tooltip_risky": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź“š\n\n"
            "Agnus hums warmly:\n\"Let grandmother recalculate\n"
            "  your odds, dear. Have some tea.\"\n\n"
            "đź’ˇ Ancient wisdom has its price!"
        ),
    },
    
    # Break Room Coffee Maker / Toffee Maker
    "underdog_006": {
        "icon_normal": "â•",
        "icon_exceptional": "đźŤ¬",
        "quote_paid": "\"Caffeinated clarity, coming right up!\" - Coffee Maker",
        "quote_risky": "\"Sugar makes the math sweeter!\" - Toffee Maker",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} â•\n\n"
            "*gurgles encouragingly*\n\"One cup of clarity, coming up!\n"
            "  Caffeine helps me think clearer.\"\n\n"
            "đź’ˇ Better odds after your coffee break!"
        ),
        "tooltip_risky": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đźŤ¬\n\n"
            "*dispenses toffee*\n\"Sugar rush = math rush!\n"
            "  Let's sweeten those odds.\"\n\n"
            "đź’ˇ Candy-coated calculations!"
        ),
    },
    
    # Break Room Fridge / Steak Room Fridge
    "underdog_009": {
        "icon_normal": "đź§Š",
        "icon_exceptional": "đźĄ©",
        "quote_paid": "\"Cool calculations... processed.\" - Fridge",
        "quote_risky": "\"Premium analysis. Wagyu-grade.\" - Steak Fridge",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź§Š\n\n"
            "*hums softly*\n\"I was meant to keep things cold.\n"
            "  Now I calculate probability. Strange.\"\n\n"
            "đź’ˇ Cool, calm, calculated odds!"
        ),
        "tooltip_risky": (
            "đźŽ˛ FREE RISKY RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đźĄ©\n\n"
            "*glows with premium confidence*\n"
            "\"Wagyu A5 analysis. No charge.\n"
            "  But premium cuts have... variance.\"\n\n"
            "đźŚŚ 80% SUCCESS: Gourmet recalculation!\n"
            "âš ď¸Ź 20% FAILURE: Odds remain marinated"
        ),
    },
    
    # Lucky Coin / Plucky Coin
    "wanderer_001": {
        "icon_normal": "đźŞ™",
        "icon_exceptional": "âś¨",
        "quote_paid": "\"Tails never fails - flip for new odds!\" - Lucky Coin",
        "quote_risky": "\"Fortune favors the bold!\" - Plucky Coin",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đźŞ™\n\n"
            "*lands on tails*\n\"Flip me again and your luck\n"
            "  might just change. For a price.\"\n\n"
            "đź’ˇ A coin well spent on fortune!"
        ),
        "tooltip_risky": (
            "đźŽ˛ FREE RISKY RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} âś¨\n\n"
            "*winks at you*\n\"I've escaped countless pockets.\n"
            "  Let's escape these bad odds too!\"\n\n"
            "đźŚŚ 80% LUCK: Fortune smiles!\n"
            "âš ď¸Ź 20% OOPS: The coin rolls away"
        ),
    },
    
    # Old War Ant General / Cold War Ant General
    "warrior_009": {
        "icon_normal": "đźś",
        "icon_exceptional": "âť„ď¸Ź",
        "quote_paid": "\"Strategic reassessment. I've seen all odds.\" - General",
        "quote_risky": "\"In the frozen wastes, I learned patience.\" - Cold General",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đźś\n\n"
            "*taps twice*\n\"I commanded armies against dragons.\n"
            "  Recalculating odds? Child's play.\"\n\n"
            "đź’ˇ The General always finds a way!"
        ),
        "tooltip_risky": (
            "đźŽ˛ FREE RISKY RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} âť„ď¸Ź\n\n"
            "*frost crystals form*\n\"I survived the Glacial Wars.\n"
            "  Sometimes victory requires... risk.\"\n\n"
            "đźŚŚ 80% STRATEGIC: Odds improve!\n"
            "âš ď¸Ź 20% TACTICAL RETREAT: Status quo"
        ),
    },
    
    # Hobo Rat / Robo Rat
    "wanderer_009": {
        "icon_normal": "đź€",
        "icon_exceptional": "đź¤–",
        "quote_paid": "\"I know all the shortcuts, friend.\" - Hobo Rat",
        "quote_risky": "\"Optimal route calculated. Trust me.\" - Robo Rat",
        "tooltip_paid": (
            "đźŽ˛ FREE RISKY RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź€\n\n"
            "*scratches ear thoughtfully*\n\"I've ridden every train.\n"
            "  Sometimes the shortcut... derails.\"\n\n"
            "đźŚŚ 80% SHORTCUT: Better odds!\n"
            "âš ď¸Ź 20% WRONG TURN: Same odds"
        ),
        "tooltip_risky": (
            "đźŽ˛ FREE RISKY RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź¤–\n\n"
            "*LED eyes flash*\n\"RECALCULATING...\n"
            "  GPS signal: 80% certainty.\"\n\n"
            "đźŚŚ 80% OPTIMIZED: Route improved!\n"
            "âš ď¸Ź 20% SIGNAL LOST: Original route"
        ),
    },
}

# Theme extension providers (kept in update() to avoid editing the legacy block above)
RECALC_ENTITY_NARRATIVES.update({
    # Audit Ghost Ledger / Audit Ghost Ledger Unredacted
    "space_pirate_007": {
        "icon_normal": "đź““",
        "icon_exceptional": "đź§ľ",
        "quote_paid": "\"Numbers remember what empires erase.\" - Ledger",
        "quote_risky": "\"Unredacted truth has turbulence.\" - Ledger Unredacted",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź““\n\n"
            "*pages flicker*\n\"I can reconcile this probability\n"
            "  against the missing wages log.\"\n\n"
            "đź’ˇ Receipts-based recalculation."
        ),
        "tooltip_risky": (
            "đźŽ˛ FREE RISKY RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź§ľ\n\n"
            "*unredacted chain unfolds*\n"
            "\"Truth route found. Stability: 80%.\"\n\n"
            "đźŚŚ 80% PROVEN PATH: Better odds!\n"
            "âš ď¸Ź 20% REDACTION STATIC: Original odds remain"
        ),
    },
    # Pocket Gravity Button / Pocket Gravity Button Omega
    "space_pirate_009": {
        "icon_normal": "đź§·",
        "icon_exceptional": "đźŚ ",
        "quote_paid": "\"Tiny button, massive correction.\" - Gravity Button",
        "quote_risky": "\"Omega lock engaged. Hold steady.\" - Button Omega",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź§·\n\n"
            "*subtle pressure wave*\n\"I can pin this outcome\n"
            "  to a better orbit.\"\n\n"
            "đź’ˇ Small interface, huge leverage."
        ),
        "tooltip_risky": (
            "đźŽ˛ FREE RISKY RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đźŚ \n\n"
            "*ethical limiter pings*\n"
            "\"Omega override: 80% stable lane.\"\n\n"
            "đźŚŚ 80% ORBIT LOCK: Better odds!\n"
            "âš ď¸Ź 20% DRIFT: Original odds remain"
        ),
    },
    # Safe Cracker Stethoscope / Harmonic Resonator
    "thief_007": {
        "icon_normal": "đź©ş",
        "icon_exceptional": "đźŽ›ď¸Ź",
        "quote_paid": "\"Listen before you strike.\" - Stethoscope",
        "quote_risky": "\"Harmonics are clean... mostly.\" - Resonator",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź©ş\n\n"
            "*steady tap sequence*\n\"Tumbler state confirmed.\n"
            "  Recomputing legally.\"\n\n"
            "đź’ˇ Precision unlock, no guesswork."
        ),
        "tooltip_risky": (
            "đźŽ˛ FREE RISKY RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đźŽ›ď¸Ź\n\n"
            "*frequency sweep hums*\n"
            "\"Signal fit: 80% confidence.\"\n\n"
            "đźŚŚ 80% CLEAN RESONANCE: Better odds!\n"
            "âš ď¸Ź 20% NOISE FLOOR: Original odds remain"
        ),
    },
    # Flashlight Beam / UV Evidence Scanner
    "thief_009": {
        "icon_normal": "đź”¦",
        "icon_exceptional": "đź§Ş",
        "quote_paid": "\"Light is the final witness.\" - Flashlight Beam",
        "quote_risky": "\"UV pass may expose a better path.\" - UV Scanner",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź”¦\n\n"
            "*beam narrows*\n\"Hidden traces found.\n"
            "  Recompute with evidence.\"\n\n"
            "đź’ˇ Forensic recalculation pass."
        ),
        "tooltip_risky": (
            "đźŽ˛ FREE RISKY RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź§Ş\n\n"
            "*UV lattice scans*\n"
            "\"Evidence lock: 80% confidence.\"\n\n"
            "đźŚŚ 80% VERIFIED TRACE: Better odds!\n"
            "âš ď¸Ź 20% OVEREXPOSURE: Original odds remain"
        ),
    },
    # Old Scalebook Oracle / Old Scalebook Oracle Unbound
    "zoo_worker_007": {
        "icon_normal": "đź“",
        "icon_exceptional": "đź“–",
        "quote_paid": "\"Wisdom is audited memory.\" - Scalebook Oracle",
        "quote_risky": "\"Unbound pages recalculate fate.\" - Oracle Unbound",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź“\n\n"
            "*ash-scented page turns*\n\"History suggests a stronger\n"
            "  probability branch.\"\n\n"
            "đź’ˇ Ledger-backed recalculation."
        ),
        "tooltip_risky": (
            "đźŽ˛ FREE RISKY RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź“–\n\n"
            "*living annotations glow*\n"
            "\"Temporal certainty: 80%.\"\n\n"
            "đźŚŚ 80% ORACLE PATH: Better odds!\n"
            "âš ď¸Ź 20% ASH DRIFT: Original odds remain"
        ),
    },
    # Emberwing of First Dawn / Emberwing Eternal Dawn
    "zoo_worker_009": {
        "icon_normal": "đź‰",
        "icon_exceptional": "đź•°ď¸Ź",
        "quote_paid": "\"Power should leave with grace.\" - Emberwing",
        "quote_risky": "\"Timeflight tolerates brave recalculation.\" - Eternal Dawn",
        "tooltip_paid": (
            "đź’° PAID RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź‰\n\n"
            "*calm wingbeat*\n\"I have seen this branch before.\n"
            "  You can do better.\"\n\n"
            "đź’ˇ Ancient witness, measured correction."
        ),
        "tooltip_risky": (
            "đźŽ˛ FREE RISKY RECALCULATE\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "Granted by: {name} đź•°ď¸Ź\n\n"
            "*timeline curls briefly*\n"
            "\"Timeflight window: 80% stable.\"\n\n"
            "đźŚŚ 80% DAWN ARC: Better odds!\n"
            "âš ď¸Ź 20% ECHO LOOP: Original odds remain"
        ),
    },
})


def _get_recalc_icon(entity_id: str, is_exceptional: bool) -> str:
    """Get the icon for a recalculate perk provider."""
    narratives = RECALC_ENTITY_NARRATIVES.get(entity_id, {})
    if is_exceptional:
        return narratives.get("icon_exceptional", "âś¨")
    return narratives.get("icon_normal", "đź”®")


def _get_recalc_quote(entity_id: str, is_exceptional: bool, risky: bool = False) -> str:
    """Get a short quote for the entity's recalculate perk."""
    narratives = RECALC_ENTITY_NARRATIVES.get(entity_id, {})
    if risky:
        return narratives.get("quote_risky", f"\"Free recalculation awaits!\" ({RISKY_RECALC_SUCCESS_RATE*100:.0f}%)")
    return narratives.get("quote_paid", "\"Let me recalculate those odds.\"")


def _build_recalc_tooltip(entity_id: str, is_exceptional: bool, risky: bool = False) -> str:
    """Build a tooltip for an entity's recalculate perk."""
    from entitidex import get_entity_by_id
    
    entity = get_entity_by_id(entity_id)
    if not entity:
        return ""
    
    name = entity.exceptional_name if is_exceptional and entity.exceptional_name else entity.name
    narratives = RECALC_ENTITY_NARRATIVES.get(entity_id, {})
    
    if risky:
        template = narratives.get("tooltip_risky", narratives.get("tooltip_paid", ""))
    else:
        template = narratives.get("tooltip_paid", "")
    
    if not template:
        # Fallback generic tooltip
        if risky:
            return (
                f"đźŽ˛ FREE RISKY RECALCULATE\n"
                f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                f"Granted by: {name}\n\n"
                f"đźŚŚ {RISKY_RECALC_SUCCESS_RATE*100:.0f}% SUCCESS: Better odds!\n"
                f"âš ď¸Ź {(1-RISKY_RECALC_SUCCESS_RATE)*100:.0f}% FAILURE: Original odds remain"
            )
        else:
            return (
                f"đź’° PAID RECALCULATE\n"
                f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
                f"Granted by: {name}\n\n"
                f"đź’ˇ Recalculate probability using current power!"
            )
    
    return template.format(name=name)


def get_recalculate_perks_status(adhd_buster: dict) -> dict:
    """
    Get the status of recalculate perks for UI display.
    
    Returns:
        dict with perk availability, list of all providers (unlocked ones),
        and first provider info for backward compatibility
    """
    from entitidex import get_entity_by_id
    from entitidex.entity_perks import ENTITY_PERKS, PerkType
    
    has_paid = has_paid_recalculate_perk(adhd_buster)
    has_risky = has_risky_recalculate_perk(adhd_buster)
    
    manager = get_entitidex_manager(adhd_buster)
    
    result = {
        "has_paid_recalculate": has_paid,
        "has_risky_recalculate": has_risky,
        "paid_recalculate_provider": None,  # First unlocked paid provider (backward compat)
        "risky_recalculate_provider": None,  # First unlocked risky provider (backward compat)
        "paid_providers": [],  # All unlocked paid providers
        "risky_providers": [],  # All unlocked risky providers
        "risky_success_rate": RISKY_RECALC_SUCCESS_RATE,
        "risky_success_percent": f"{RISKY_RECALC_SUCCESS_RATE * 100:.0f}%",
    }
    
    # Find all providers with their unlock status
    for entity_id, perks in ENTITY_PERKS.items():
        entity = get_entity_by_id(entity_id)
        if not entity:
            continue
        
        is_collected = manager.progress.is_collected(entity_id)
        is_exceptional = manager.progress.is_exceptional(entity_id)
        
        for perk in perks:
            # Check paid recalculate perks
            if perk.perk_type == PerkType.RECALC_PAID:
                # Normal variant
                if perk.normal_value > 0 and is_collected:
                    provider = {
                        "entity_id": entity_id,
                        "name": entity.name,
                        "is_exceptional": False,
                        "is_unlocked": True,
                        "perk_label": "đź’° Paid Recalculate",
                        "description": _get_recalc_quote(entity_id, False),
                        "tooltip": _build_recalc_tooltip(entity_id, False),
                        "icon": _get_recalc_icon(entity_id, False),
                    }
                    result["paid_providers"].append(provider)
                    if result["paid_recalculate_provider"] is None:
                        result["paid_recalculate_provider"] = provider
                
                # Exceptional variant
                if perk.exceptional_value > 0 and is_exceptional:
                    provider = {
                        "entity_id": entity_id,
                        "name": entity.exceptional_name or entity.name,
                        "is_exceptional": True,
                        "is_unlocked": True,
                        "perk_label": "đź’° Paid Recalculate",
                        "description": _get_recalc_quote(entity_id, True),
                        "tooltip": _build_recalc_tooltip(entity_id, True),
                        "icon": _get_recalc_icon(entity_id, True),
                    }
                    result["paid_providers"].append(provider)
                    if result["paid_recalculate_provider"] is None:
                        result["paid_recalculate_provider"] = provider
            
            # Check risky recalculate perks
            if perk.perk_type == PerkType.RECALC_RISKY:
                # Normal variant
                if perk.normal_value > 0 and is_collected:
                    provider = {
                        "entity_id": entity_id,
                        "name": entity.name,
                        "is_exceptional": False,
                        "is_unlocked": True,
                        "perk_label": "đźŽ˛ Free Risky Recalculate",
                        "description": _get_recalc_quote(entity_id, False, risky=True),
                        "tooltip": _build_recalc_tooltip(entity_id, False, risky=True),
                        "icon": _get_recalc_icon(entity_id, False),
                    }
                    result["risky_providers"].append(provider)
                    if result["risky_recalculate_provider"] is None:
                        result["risky_recalculate_provider"] = provider
                
                # Exceptional variant
                if perk.exceptional_value > 0 and is_exceptional:
                    provider = {
                        "entity_id": entity_id,
                        "name": entity.exceptional_name or entity.name,
                        "is_exceptional": True,
                        "is_unlocked": True,
                        "perk_label": "đźŽ˛ Free Risky Recalculate",
                        "description": _get_recalc_quote(entity_id, True, risky=True),
                        "tooltip": _build_recalc_tooltip(entity_id, True, risky=True),
                        "icon": _get_recalc_icon(entity_id, True),
                    }
                    result["risky_providers"].append(provider)
                    if result["risky_recalculate_provider"] is None:
                        result["risky_recalculate_provider"] = provider
    
    return result


def get_recalculate_cost(adhd_buster: dict, index: int = 0) -> dict:
    """
    Get the cost to recalculate probability for a saved encounter.
    
    Also shows a preview of what the new probability would be with current power.
    
    Args:
        adhd_buster: Hero data dictionary
        index: Index of saved encounter to check
        
    Returns:
        dict with cost info and probability comparison
    """
    from entitidex import get_entity_by_id
    
    manager = get_entitidex_manager(adhd_buster)
    saved_list = manager.progress.get_saved_encounters()
    
    if index < 0 or index >= len(saved_list):
        return {"success": False, "message": "No saved encounter at that index"}
    
    saved = saved_list[index]
    entity = get_entity_by_id(saved.entity_id)
    
    if entity is None:
        return {"success": False, "message": "Entity not found"}
    
    # Calculate cost based on rarity
    cost = RECALCULATE_COST_BY_RARITY.get(entity.rarity.lower(), 100)
    
    # Calculate recalculated probability with the same full stack as live encounters.
    new_probability, recalc_hero_power = _calculate_saved_encounter_recalc_probability(
        adhd_buster=adhd_buster,
        manager=manager,
        saved=saved,
        entity_power=entity.power,
        use_saved_story_power=True,
    )
    
    old_probability = saved.catch_probability
    probability_change = new_probability - old_probability
    is_worth_it = probability_change > 0.05  # Worth it if >5% improvement
    
    current_coins = adhd_buster.get("coins", 0)
    can_afford = current_coins >= cost
    
    display_name = entity.exceptional_name if saved.is_exceptional and entity.exceptional_name else entity.name
    
    # Check perk availability
    has_paid = has_paid_recalculate_perk(adhd_buster)
    has_risky = has_risky_recalculate_perk(adhd_buster)
    
    return {
        "success": True,
        "entity": entity,
        "display_name": display_name,
        "is_exceptional": saved.is_exceptional,
        "cost": cost,
        "can_afford": can_afford,
        "current_coins": current_coins,
        "old_probability": old_probability,
        "new_probability": new_probability,
        "probability_change": probability_change,
        "probability_change_percent": f"{probability_change * 100:+.1f}%",
        "is_worth_it": is_worth_it,
        "old_hero_power": saved.hero_power_at_encounter,
        "current_hero_power": recalc_hero_power,
        "power_gained": recalc_hero_power - saved.hero_power_at_encounter,
        "recommendation": _get_recalc_recommendation(probability_change, can_afford),
        # Perk availability for UI
        "has_paid_recalculate_perk": has_paid,
        "has_risky_recalculate_perk": has_risky,
        "risky_success_rate": RISKY_RECALC_SUCCESS_RATE,
        "perk_providers": get_recalculate_perk_providers(),
    }


def _get_recalc_recommendation(change: float, can_afford: bool) -> str:
    """Get a recommendation message for recalculating."""
    if not can_afford:
        return "đź’° Not enough coins to recalculate"
    if change > 0.20:
        return "đźŚź Highly recommended! Huge improvement!"
    if change > 0.10:
        return "âś¨ Good investment! Solid improvement"
    if change > 0.05:
        return "đź‘Ť Worth considering, decent boost"
    if change > 0:
        return "đź¤” Small improvement, your call"
    if change == 0:
        return "âžˇď¸Ź No change - save your coins!"
    return "âš ď¸Ź You've gotten weaker! Keep original odds"


def open_saved_encounter_with_recalculate(
    adhd_buster: dict, 
    index: int = 0,
    recalculate: bool = False,
) -> dict:
    """
    Open a saved encounter with optional paid probability recalculation.
    
    If recalculate=True, pays coins to recalculate probability based on
    CURRENT hero power instead of power at encounter time.
    
    Args:
        adhd_buster: Hero data dictionary
        index: Index of saved encounter to open (0 = oldest)
        recalculate: If True, pay coins to recalculate with current power
        
    Returns:
        dict with bond attempt result
    """
    from entitidex import get_entity_by_id
    import random
    
    manager = get_entitidex_manager(adhd_buster)
    
    # Get saved encounter (don't pop yet in case payment fails)
    saved_list = manager.progress.get_saved_encounters()
    if index < 0 or index >= len(saved_list):
        return {
            "success": False,
            "message": "No saved encounter at that index",
            "remaining_saved": manager.progress.get_saved_encounter_count(),
        }
    
    saved = saved_list[index]
    entity = get_entity_by_id(saved.entity_id)
    
    if entity is None:
        # Pop invalid encounter
        manager.progress.pop_saved_encounter(index)
        save_entitidex_progress(adhd_buster, manager)
        return {
            "success": False,
            "message": "Entity no longer exists",
            "remaining_saved": manager.progress.get_saved_encounter_count(),
        }
    
    probability_to_use = saved.catch_probability
    paid_for_recalc = False
    recalc_cost = 0
    
    # Handle recalculation payment
    if recalculate:
        # Check if user has any entity with paid recalculation perk.
        if not has_paid_recalculate_perk(adhd_buster):
            paid_unlocks = get_recalculate_provider_names(risky=False, include_ids=True)
            unlock_lines = "\n".join(f"â€˘ {name}" for name in paid_unlocks) if paid_unlocks else "â€˘ Any entity with Paid Recalculate"
            return {
                "success": False,
                "message": (
                    "đź’° Collect any of these to unlock Paid Recalculate:\n"
                    f"{unlock_lines}"
                ),
                "requires_entity": CHAD_ENTITY_ID,
                "requires_exceptional": False,
                "remaining_saved": manager.progress.get_saved_encounter_count(),
            }
        
        cost = RECALCULATE_COST_BY_RARITY.get(entity.rarity.lower(), 100)
        current_coins = adhd_buster.get("coins", 0)
        
        if current_coins < cost:
            return {
                "success": False,
                "message": f"Not enough coins! Need {cost}, have {current_coins}",
                "remaining_saved": manager.progress.get_saved_encounter_count(),
            }
        
        # Deduct coins
        adhd_buster["coins"] = current_coins - cost
        recalc_cost = cost
        paid_for_recalc = True
        
        probability_to_use, _ = _calculate_saved_encounter_recalc_probability(
            adhd_buster=adhd_buster,
            manager=manager,
            saved=saved,
            entity_power=entity.power,
            use_saved_story_power=True,
        )
    
    # Now pop the encounter
    manager.progress.pop_saved_encounter(index)
    
    # Roll the dice!
    roll = random.random()
    success = roll < probability_to_use
    
    display_name = entity.exceptional_name if saved.is_exceptional and entity.exceptional_name else entity.name
    
    # Handle success/failure
    exceptional_colors = None
    xp_awarded = 0
    
    if success:
        # Record successful catch
        exceptional_colors = saved.exceptional_colors
        if saved.is_exceptional and not exceptional_colors:
            exceptional_colors = _generate_exceptional_colors()
        
        hero_power = calculate_character_power(adhd_buster)
        manager.progress.record_successful_catch(
            entity_id=saved.entity_id,
            hero_power=hero_power,
            probability=probability_to_use,
            was_lucky=probability_to_use < 0.5,
            is_exceptional=saved.is_exceptional,
            exceptional_colors=exceptional_colors,
        )
        
        # Award XP
        rarity_xp = {
            "common": 25, "uncommon": 50, "rare": 100,
            "epic": 200, "legendary": 500,
        }
        base_xp = rarity_xp.get(entity.rarity.lower(), 50)
        xp_awarded = base_xp * 2 if saved.is_exceptional else base_xp
        xp_source = f"entitidex_saved_{'exceptional' if saved.is_exceptional else 'catch'}_{entity.rarity}"
        award_xp(adhd_buster, xp_awarded, xp_source)
        
        if saved.is_exceptional:
            message = f"đźŚźâś¨ EXCEPTIONAL {display_name} has joined your team! +{xp_awarded} XP! âś¨đźŚź"
        else:
            message = f"đźŽ‰ {entity.name} has joined your team! +{xp_awarded} XP!"
        
        if paid_for_recalc:
            message += f" (Recalculated for {recalc_cost} coins)"
    else:
        # Record failed catch for pity system
        manager.progress.record_failed_catch(saved.entity_id, saved.is_exceptional)
        
        if saved.is_exceptional:
            message = f"đź’¨ {display_name} slipped away... Better luck next time!"
        else:
            message = f"đź’¨ {entity.name} slipped away... The pity system will help next time!"
        
        if paid_for_recalc:
            message += f" (Spent {recalc_cost} coins on recalculation)"
    
    save_entitidex_progress(adhd_buster, manager)
    
    # Emit entity collected signal for timeline ring if successful
    if success:
        from game_state import get_game_state
        gs = get_game_state()
        if gs:
            gs.notify_entity_collected(saved.entity_id)
    
    return {
        "success": success,
        "entity": entity,
        "probability": probability_to_use,
        "roll": roll,
        "original_probability": saved.catch_probability if paid_for_recalc else None,
        "is_exceptional": saved.is_exceptional,
        "exceptional_colors": exceptional_colors,
        "xp_awarded": xp_awarded,
        "message": message,
        "was_saved_encounter": True,
        "paid_for_recalculate": paid_for_recalc,
        "recalculate_cost": recalc_cost if paid_for_recalc else 0,
        "remaining_saved": manager.progress.get_saved_encounter_count(),
    }


def open_saved_encounter_risky_recalculate(
    adhd_buster: dict,
    index: int = 0,
) -> dict:
    """
    Open a saved encounter with FREE risky probability recalculation.
    
    Requires: AGI Assistant Rad (exceptional variant) unlocked.
    
    This is a FREE recalculation but with risk:
    - 80% chance: Recalculation succeeds, use new probability
    - 20% chance: Recalculation fails, use original saved probability
    
    The risky roll uses a lottery animation for dramatic effect.
    This function returns data for the UI to show the lottery animation,
    then the UI calls finalize_risky_recalculate with the result.
    
    Args:
        adhd_buster: Hero data dictionary
        index: Index of saved encounter to open (0 = oldest)
        
    Returns:
        dict with encounter info for lottery animation, or error
    """
    from entitidex import get_entity_by_id
    
    # Check if user has any entity with RECALC_RISKY.
    if not has_risky_recalculate_perk(adhd_buster):
        risky_unlocks = get_recalculate_provider_names(risky=True, include_ids=True)
        unlock_lines = "\n".join(f"â€˘ {name}" for name in risky_unlocks) if risky_unlocks else "â€˘ Any entity with Free Risky Recalculate"
        return {
            "success": False,
            "message": (
                "đźŽ˛ Collect any of these to unlock Free Risky Recalculate:\n"
                f"{unlock_lines}"
            ),
            "requires_entity": CHAD_ENTITY_ID,
            "requires_exceptional": True,
        }
    
    manager = get_entitidex_manager(adhd_buster)
    saved_list = manager.progress.get_saved_encounters()
    
    if index < 0 or index >= len(saved_list):
        return {
            "success": False,
            "message": "No saved encounter at that index",
            "remaining_saved": manager.progress.get_saved_encounter_count(),
        }
    
    saved = saved_list[index]
    entity = get_entity_by_id(saved.entity_id)
    
    if entity is None:
        manager.progress.pop_saved_encounter(index)
        save_entitidex_progress(adhd_buster, manager)
        return {
            "success": False,
            "message": "Entity no longer exists",
            "remaining_saved": manager.progress.get_saved_encounter_count(),
        }
    
    new_probability, _ = _calculate_saved_encounter_recalc_probability(
        adhd_buster=adhd_buster,
        manager=manager,
        saved=saved,
        entity_power=entity.power,
        use_saved_story_power=True,
    )
    
    display_name = entity.exceptional_name if saved.is_exceptional and entity.exceptional_name else entity.name
    
    # Pre-roll the risky recalc in backend so UI only reveals the result.
    risky_roll = random.random()
    risky_recalc_succeeded = risky_roll < RISKY_RECALC_SUCCESS_RATE

    # Return data for lottery animation.
    # UI should reveal this backend roll, then call finalize_risky_recalculate.
    return {
        "success": True,
        "ready_for_lottery": True,
        "entity": entity,
        "display_name": display_name,
        "is_exceptional": saved.is_exceptional,
        "index": index,
        "old_probability": saved.catch_probability,
        "new_probability": new_probability,
        "probability_change": new_probability - saved.catch_probability,
        "risky_success_rate": RISKY_RECALC_SUCCESS_RATE,
        "risky_roll": risky_roll,
        "risky_recalc_succeeded": risky_recalc_succeeded,
        "message": f"đźŽ˛ Rolling for FREE recalculate... {RISKY_RECALC_SUCCESS_RATE*100:.0f}% chance!",
    }


def finalize_risky_recalculate(
    adhd_buster: dict,
    index: int,
    recalc_succeeded: Optional[bool] = None,
    risky_roll: Optional[float] = None,
) -> dict:
    """
    Finalize a risky recalculate after the lottery animation.
    
    Called by UI after showing the lottery animation for risky recalculate.
    
    Args:
        adhd_buster: Hero data dictionary
        index: Index of saved encounter
        recalc_succeeded: Optional legacy override from UI. If omitted, derived from risky_roll.
        risky_roll: Optional pre-rolled value from open_saved_encounter_risky_recalculate.
        
    Returns:
        dict with bond attempt result
    """
    from entitidex import get_entity_by_id
    import random
    
    manager = get_entitidex_manager(adhd_buster)
    saved_list = manager.progress.get_saved_encounters()
    
    if index < 0 or index >= len(saved_list):
        return {
            "success": False,
            "message": "No saved encounter at that index",
            "remaining_saved": manager.progress.get_saved_encounter_count(),
        }
    
    saved = saved_list[index]
    entity = get_entity_by_id(saved.entity_id)
    
    if entity is None:
        manager.progress.pop_saved_encounter(index)
        save_entitidex_progress(adhd_buster, manager)
        return {
            "success": False,
            "message": "Entity no longer exists",
            "remaining_saved": manager.progress.get_saved_encounter_count(),
        }
    
    # Determine risky recalc result from backend roll (canonical).
    if risky_roll is None:
        risky_roll = random.random()
    risky_roll = max(0.0, min(1.0, float(risky_roll)))
    rolled_recalc_success = risky_roll < RISKY_RECALC_SUCCESS_RATE

    # Keep compatibility with older callers that only passed recalc_succeeded.
    if recalc_succeeded is None:
        recalc_succeeded = rolled_recalc_success
    else:
        # Backend roll is authoritative.
        recalc_succeeded = rolled_recalc_success

    # Determine probability to use based on risky lottery result.
    if recalc_succeeded:
        probability_to_use, _ = _calculate_saved_encounter_recalc_probability(
            adhd_buster=adhd_buster,
            manager=manager,
            saved=saved,
            entity_power=entity.power,
            use_saved_story_power=True,
        )
        used_recalculated = True
    else:
        probability_to_use = saved.catch_probability
        used_recalculated = False
    
    # Pop the encounter
    manager.progress.pop_saved_encounter(index)
    
    # Roll for bonding!
    roll = random.random()
    success = roll < probability_to_use
    
    display_name = entity.exceptional_name if saved.is_exceptional and entity.exceptional_name else entity.name
    
    # Handle success/failure
    exceptional_colors = None
    xp_awarded = 0
    
    if success:
        exceptional_colors = saved.exceptional_colors
        if saved.is_exceptional and not exceptional_colors:
            exceptional_colors = _generate_exceptional_colors()
        
        hero_power = calculate_character_power(adhd_buster)
        manager.progress.record_successful_catch(
            entity_id=saved.entity_id,
            hero_power=hero_power,
            probability=probability_to_use,
            was_lucky=probability_to_use < 0.5,
            is_exceptional=saved.is_exceptional,
            exceptional_colors=exceptional_colors,
        )
        
        # Award XP
        rarity_xp = {
            "common": 25, "uncommon": 50, "rare": 100,
            "epic": 200, "legendary": 500,
        }
        base_xp = rarity_xp.get(entity.rarity.lower(), 50)
        xp_awarded = base_xp * 2 if saved.is_exceptional else base_xp
        xp_source = f"entitidex_risky_{'exceptional' if saved.is_exceptional else 'catch'}_{entity.rarity}"
        award_xp(adhd_buster, xp_awarded, xp_source)
        
        if saved.is_exceptional:
            message = f"đźŚźâś¨ EXCEPTIONAL {display_name} has joined your team! +{xp_awarded} XP! âś¨đźŚź"
        else:
            message = f"đźŽ‰ {entity.name} has joined your team! +{xp_awarded} XP!"
        
        if used_recalculated:
            message += " (Free Risky Recalculate succeeded!)"
        else:
            message += " (Risky Recalculate failed, used original odds)"
    else:
        manager.progress.record_failed_catch(saved.entity_id, saved.is_exceptional)
        
        if saved.is_exceptional:
            message = f"đź’¨ {display_name} slipped away... Better luck next time!"
        else:
            message = f"đź’¨ {entity.name} slipped away... The pity system will help next time!"
        
        if used_recalculated:
            message += " (Free Risky Recalculate succeeded, but bonding failed)"
        else:
            message += " (Risky Recalculate failed, used original odds)"
    
    save_entitidex_progress(adhd_buster, manager)
    
    # Emit entity collected signal for timeline ring if successful
    if success:
        from game_state import get_game_state
        gs = get_game_state()
        if gs:
            gs.notify_entity_collected(saved.entity_id)
    
    return {
        "success": success,
        "entity": entity,
        "probability": probability_to_use,
        "roll": roll,
        "original_probability": saved.catch_probability,
        "used_recalculated_probability": used_recalculated,
        "risky_roll": risky_roll,
        "is_exceptional": saved.is_exceptional,
        "exceptional_colors": exceptional_colors,
        "xp_awarded": xp_awarded,
        "message": message,
        "was_saved_encounter": True,
        "was_risky_recalculate": True,
        "risky_recalc_succeeded": recalc_succeeded,
        "remaining_saved": manager.progress.get_saved_encounter_count(),
    }


