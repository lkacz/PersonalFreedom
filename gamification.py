"""
ADHD Buster Gamification System
================================
Extracted gamification logic for use with any UI framework.
Includes: item generation, set bonuses, lucky merge, diary entries.
"""

import random
import re
from datetime import datetime

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
    ]}
}

# Item slots and types
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
    ]
}

# Rarity power values for calculating character strength
RARITY_POWER = {
    "Common": 10,
    "Uncommon": 25,
    "Rare": 50,
    "Epic": 100,
    "Legendary": 250
}

# ============================================================================
# SET BONUS SYSTEM - Matching themed items give power bonuses!
# ============================================================================

# Theme categories that items can belong to (extracted from item names)
ITEM_THEMES = {
    # Creature themes
    "Goblin": {"words": ["goblin", "gremlin", "imp"], "bonus_per_match": 15, "emoji": "👺"},
    "Dragon": {"words": ["dragon", "drake", "wyrm", "draconic"], "bonus_per_match": 25, "emoji": "🐉"},
    "Phoenix": {"words": ["phoenix", "flame", "fire", "burning", "blazing"], "bonus_per_match": 20, "emoji": "🔥"},
    "Void": {"words": ["void", "shadow", "dark", "abyss", "abyssal"], "bonus_per_match": 20, "emoji": "🌑"},
    "Celestial": {"words": ["celestial", "astral", "cosmic", "star", "divine"], "bonus_per_match": 25, "emoji": "⭐"},
    "Titan": {"words": ["titan", "giant", "colossal", "primordial"], "bonus_per_match": 25, "emoji": "🗿"},
    "Arcane": {"words": ["arcane", "mystic", "enchanted", "magical", "rune"], "bonus_per_match": 18, "emoji": "✨"},
    "Ancient": {"words": ["ancient", "old", "eternal", "timeless"], "bonus_per_match": 18, "emoji": "📜"},
    "Crystal": {"words": ["crystal", "gem", "jewel", "diamond"], "bonus_per_match": 15, "emoji": "💎"},
    "Iron": {"words": ["iron", "steel", "metal", "forge", "forged"], "bonus_per_match": 12, "emoji": "⚔️"},
    # Silly themes  
    "Procrastination": {"words": ["procrastination", "lazy", "distract", "coffee"], "bonus_per_match": 10, "emoji": "☕"},
    "Focus": {"words": ["focus", "clarity", "discipline", "determination"], "bonus_per_match": 20, "emoji": "🎯"},
    "Chaos": {"words": ["chaos", "random", "wild", "unpredictable"], "bonus_per_match": 15, "emoji": "🌀"},
    "Quantum": {"words": ["quantum", "reality", "dimension", "paradox"], "bonus_per_match": 30, "emoji": "🔮"},
}

# Minimum matches required for set bonus activation
SET_BONUS_MIN_MATCHES = 2


def get_item_themes(item: dict) -> list:
    """Extract theme(s) from an item based on its name."""
    if not item:
        return []
    
    name_lower = item.get("name", "").lower()
    themes = []
    
    for theme_name, theme_data in ITEM_THEMES.items():
        for word in theme_data["words"]:
            # Use word boundary matching to avoid partial matches
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, name_lower):
                themes.append(theme_name)
                break  # Only count each theme once per item
    
    return themes


def calculate_set_bonuses(equipped: dict) -> dict:
    """
    Calculate set bonuses from equipped items sharing themes.
    
    Returns a dict with:
    - active_sets: list of {name, emoji, count, bonus}
    - total_bonus: total power bonus from all sets
    """
    if not equipped:
        return {"active_sets": [], "total_bonus": 0}
    
    # Count themes across all equipped items
    theme_counts = {}
    theme_items = {}
    
    for slot, item in equipped.items():
        if not item:
            continue
        themes = get_item_themes(item)
        for theme in themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
            if theme not in theme_items:
                theme_items[theme] = []
            theme_items[theme].append(slot)
    
    # Calculate bonuses for themes with enough matches
    active_sets = []
    total_bonus = 0
    
    for theme_name, count in theme_counts.items():
        if count >= SET_BONUS_MIN_MATCHES:
            theme_data = ITEM_THEMES[theme_name]
            bonus = theme_data["bonus_per_match"] * count
            active_sets.append({
                "name": theme_name,
                "emoji": theme_data["emoji"],
                "count": count,
                "bonus": bonus,
                "slots": theme_items[theme_name]
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

MERGE_BASE_SUCCESS_RATE = 0.10  # 10% base chance
MERGE_BONUS_PER_ITEM = 0.03    # +3% per additional item after the first two
MERGE_MAX_SUCCESS_RATE = 0.35  # Cap at 35% success rate

# Rarity upgrade paths
RARITY_UPGRADE = {
    "Common": "Uncommon",
    "Uncommon": "Rare",
    "Rare": "Epic",
    "Epic": "Legendary",
    "Legendary": "Legendary"  # Can't go higher
}

RARITY_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]


def calculate_merge_success_rate(items: list, luck_bonus: int = 0) -> float:
    """Calculate the success rate for a lucky merge."""
    if len(items) < 2:
        return 0.0
    
    rate = MERGE_BASE_SUCCESS_RATE + (len(items) - 2) * MERGE_BONUS_PER_ITEM
    luck_bonus_pct = min(luck_bonus / 100 * 0.01, 0.10)
    rate += luck_bonus_pct
    
    return min(rate, MERGE_MAX_SUCCESS_RATE)


def get_merge_result_rarity(items: list) -> str:
    """Determine the rarity of the merged item result."""
    if not items:
        return "Common"
    
    lowest_idx = min(RARITY_ORDER.index(item.get("rarity", "Common")) for item in items)
    lowest_rarity = RARITY_ORDER[lowest_idx]
    
    return RARITY_UPGRADE.get(lowest_rarity, "Uncommon")


def is_merge_worthwhile(items: list) -> tuple:
    """Check if a merge is worthwhile (can result in upgrade)."""
    if not items or len(items) < 2:
        return False, "Need at least 2 items"
    
    all_legendary = all(item.get("rarity") == "Legendary" for item in items)
    if all_legendary:
        return False, "All items are Legendary - merge cannot upgrade!"
    
    return True, ""


def perform_lucky_merge(items: list, luck_bonus: int = 0) -> dict:
    """Attempt a lucky merge of items."""
    if len(items) < 2:
        return {"success": False, "error": "Need at least 2 items to merge"}
    
    success_rate = calculate_merge_success_rate(items, luck_bonus)
    roll = random.random()
    
    result = {
        "success": roll < success_rate,
        "items_lost": items,
        "roll": roll,
        "needed": success_rate,
        "roll_pct": f"{roll*100:.1f}%",
        "needed_pct": f"{success_rate*100:.1f}%"
    }
    
    if result["success"]:
        result_rarity = get_merge_result_rarity(items)
        result["result_item"] = generate_item(rarity=result_rarity)
    else:
        result["result_item"] = None
    
    return result


# ============================================================================
# ADHD Buster Diary - Epic Adventure Journal System
# ============================================================================

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
        "a mildly inconvenienced", "a slightly annoyed", "a confused-looking",
        "an unimpressed", "a suspiciously normal", "a forgettable", "a generic"
    ],
    "modest": [
        "a reasonably impressive", "a decent", "an actually-trying", "a notable",
        "an interesting", "a surprising", "an unexpected", "a capable"
    ],
    "decent": [
        "a legendary", "a mythical", "an ancient", "a powerful", "a fearsome",
        "a dreaded", "a fabled", "a renowned", "a notorious", "an infamous"
    ],
    "heroic": [
        "a reality-bending", "a dimension-hopping", "a time-traveling", "a fate-weaving",
        "a prophecy-fulfilling", "a destiny-altering", "a world-shaking"
    ],
    "epic": [
        "an infinitely powerful", "an omniscient", "an omnipotent", "an omnipresent",
        "a beyond-comprehension", "a reality-defining", "a universe-creating"
    ],
    "legendary": [
        "a cosmic-horror-yet-somehow-friendly", "an incomprehensible-but-approachable",
        "a beyond-all-understanding-yet-cool", "a reality-core-manifestation-of"
    ],
    "godlike": [
        "the very concept of", "the fundamental essence of",
        "the living equation that is", "the cosmic constant known as"
    ]
}

DIARY_TARGETS = {
    "pathetic": [
        "an intern", "a confused tourist", "a lost pizza delivery guy",
        "someone's weird uncle", "a procrastinating student", "a grumpy cat"
    ],
    "modest": [
        "a minor goblin", "a trainee wizard", "an apprentice knight", "a baby dragon",
        "a teenage vampire", "a part-time werewolf", "a gig-economy demon"
    ],
    "decent": [
        "a proper dragon", "an experienced sorcerer", "a veteran knight",
        "a master assassin", "an ancient lich", "a demon lord", "an angel captain"
    ],
    "heroic": [
        "an elder god", "a titan of old", "a primordial being", "an arch-demon",
        "an archangel", "a god of war", "a goddess of wisdom", "a lord of chaos"
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


def generate_diary_entry(power: int, session_minutes: int = 25, equipped_items: dict = None) -> dict:
    """Generate a hilarious diary entry based on character power level."""
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
    
    verb = random.choice(DIARY_VERBS[verb_tier])
    adjective = random.choice(DIARY_ADJECTIVES[tier])
    target = random.choice(DIARY_TARGETS[tier])
    location = random.choice(DIARY_LOCATIONS[tier])
    outcome = random.choice(DIARY_OUTCOMES[tier])
    flavor = random.choice(DIARY_FLAVOR[tier])
    
    story = f"Today I {verb} {adjective} {target} {location} and it ended in {outcome}."
    
    item_mention = ""
    if equipped_items:
        equipped_list = [item for item in equipped_items.values() if item]
        if equipped_list:
            featured_item = random.choice(equipped_list)
            item_name = featured_item.get("name", "mysterious item")
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
        "short_date": datetime.now().strftime("%b %d, %Y")
    }


def calculate_rarity_bonuses(session_minutes: int = 0, streak_days: int = 0) -> dict:
    """Calculate rarity weight adjustments based on session length and streak."""
    session_bonus = 0
    if session_minutes >= 120:
        session_bonus = 50
    elif session_minutes >= 90:
        session_bonus = 35
    elif session_minutes >= 60:
        session_bonus = 20
    elif session_minutes >= 30:
        session_bonus = 10
    elif session_minutes >= 15:
        session_bonus = 5
    
    streak_bonus = 0
    if streak_days >= 60:
        streak_bonus = 60
    elif streak_days >= 30:
        streak_bonus = 40
    elif streak_days >= 14:
        streak_bonus = 25
    elif streak_days >= 7:
        streak_bonus = 15
    elif streak_days >= 3:
        streak_bonus = 5
    
    return {
        "session_bonus": session_bonus,
        "streak_bonus": streak_bonus,
        "total_bonus": session_bonus + streak_bonus
    }


def generate_item(rarity: str = None, session_minutes: int = 0, streak_days: int = 0) -> dict:
    """Generate a random item with rarity influenced by session length and streak."""
    if rarity is None:
        rarities = list(ITEM_RARITIES.keys())
        base_weights = [ITEM_RARITIES[r]["weight"] for r in rarities]
        
        bonuses = calculate_rarity_bonuses(session_minutes, streak_days)
        total_bonus = bonuses["total_bonus"]
        
        if total_bonus > 0:
            weights = base_weights.copy()
            shift_amount = min(weights[0] * (total_bonus / 100), weights[0] * 0.7)
            weights[0] -= shift_amount
            weights[1] += shift_amount * 0.25
            weights[2] += shift_amount * 0.35
            weights[3] += shift_amount * 0.25
            weights[4] += shift_amount * 0.15
        else:
            weights = base_weights
        
        rarity = random.choices(rarities, weights=weights)[0]
    
    slot = random.choice(list(ITEM_SLOTS.keys()))
    item_type = random.choice(ITEM_SLOTS[slot])
    adjective = random.choice(ITEM_RARITIES[rarity]["adjectives"])
    suffix = random.choice(ITEM_SUFFIXES[rarity])
    
    name = f"{adjective} {item_type} of {suffix}"
    
    return {
        "name": name,
        "rarity": rarity,
        "slot": slot,
        "item_type": item_type,
        "color": ITEM_RARITIES[rarity]["color"],
        "power": RARITY_POWER[rarity],
        "obtained_at": datetime.now().isoformat()
    }


def calculate_character_power(adhd_buster: dict, include_set_bonus: bool = True) -> int:
    """Calculate total power from equipped items plus set bonuses."""
    equipped = adhd_buster.get("equipped", {})
    total_power = 0
    for item in equipped.values():
        if item:
            total_power += item.get("power", RARITY_POWER.get(item.get("rarity", "Common"), 10))
    
    if include_set_bonus:
        set_info = calculate_set_bonuses(equipped)
        total_power += set_info["total_bonus"]
    
    return total_power


def get_power_breakdown(adhd_buster: dict) -> dict:
    """Get detailed breakdown of character power."""
    equipped = adhd_buster.get("equipped", {})
    
    base_power = 0
    for item in equipped.values():
        if item:
            base_power += item.get("power", RARITY_POWER.get(item.get("rarity", "Common"), 10))
    
    set_info = calculate_set_bonuses(equipped)
    
    return {
        "base_power": base_power,
        "set_bonus": set_info["total_bonus"],
        "active_sets": set_info["active_sets"],
        "total_power": base_power + set_info["total_bonus"]
    }
