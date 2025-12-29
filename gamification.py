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


# Tier jump probabilities for lucky merge (higher jumps are rarer for more thrill)
# +1 tier: 70%, +2 tiers: 22%, +3 tiers: 8%
MERGE_TIER_JUMP_WEIGHTS = [
    (1, 70),   # +1 tier: 70% chance
    (2, 22),   # +2 tiers: 22% chance  
    (3, 8),    # +3 tiers: 8% chance (jackpot!)
]


def get_random_tier_jump() -> int:
    """Roll for random tier upgrade on successful merge.
    
    Returns:
        Number of tiers to jump (1, 2, or 3)
    """
    roll = random.randint(1, 100)
    cumulative = 0
    for jump, weight in MERGE_TIER_JUMP_WEIGHTS:
        cumulative += weight
        if roll <= cumulative:
            return jump
    return 1  # Fallback


def perform_lucky_merge(items: list, luck_bonus: int = 0) -> dict:
    """Attempt a lucky merge of items.
    
    On success, the resulting item can be +1, +2, or +3 tiers higher than
    the base result (with decreasing probability for higher jumps).
    """
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
        "needed_pct": f"{success_rate*100:.1f}%",
        "tier_jump": 0
    }
    
    if result["success"]:
        # Get base rarity from lowest item
        lowest_idx = min(RARITY_ORDER.index(item.get("rarity", "Common")) for item in items)
        
        # Roll for tier jump
        tier_jump = get_random_tier_jump()
        result["tier_jump"] = tier_jump
        
        # Calculate final rarity with tier jump (capped at Legendary)
        final_idx = min(lowest_idx + tier_jump, len(RARITY_ORDER) - 1)
        final_rarity = RARITY_ORDER[final_idx]
        
        result["result_item"] = generate_item(rarity=final_rarity)
        result["base_rarity"] = RARITY_ORDER[lowest_idx]
        result["final_rarity"] = final_rarity
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


# Rarity order for tier calculations
RARITY_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]


def get_current_tier(adhd_buster: dict) -> str:
    """Get the highest rarity tier from equipped items."""
    equipped = adhd_buster.get("equipped", {})
    highest_tier = "Common"
    
    for item in equipped.values():
        if item:
            item_rarity = item.get("rarity", "Common")
            if RARITY_ORDER.index(item_rarity) > RARITY_ORDER.index(highest_tier):
                highest_tier = item_rarity
    
    return highest_tier


def get_boosted_rarity(current_tier: str) -> str:
    """Get a rarity one tier higher than current (capped at Legendary)."""
    current_idx = RARITY_ORDER.index(current_tier)
    boosted_idx = min(current_idx + 1, len(RARITY_ORDER) - 1)
    return RARITY_ORDER[boosted_idx]


def generate_daily_reward_item(adhd_buster: dict) -> dict:
    """Generate a daily reward item - one tier higher than current equipped tier."""
    current_tier = get_current_tier(adhd_buster)
    boosted_rarity = get_boosted_rarity(current_tier)
    return generate_item(rarity=boosted_rarity)


# Priority completion reward settings
PRIORITY_COMPLETION_CHANCE = 15  # 15% chance to win a reward
PRIORITY_REWARD_WEIGHTS = {
    # Low chance rewards are high tier - inverted from normal drops
    "Common": 5,       # 5% of rewards
    "Uncommon": 10,    # 10% of rewards  
    "Rare": 30,        # 30% of rewards
    "Epic": 35,        # 35% of rewards
    "Legendary": 20    # 20% of rewards!
}


def roll_priority_completion_reward() -> dict | None:
    """
    Roll for a priority completion reward.
    Low chance (15%) to win, but if you win, high chance of Epic/Legendary!
    
    Returns:
        dict with 'won' (bool), 'item' (dict or None), 'message' (str)
    """
    # First roll: did the user win?
    if random.randint(1, 100) > PRIORITY_COMPLETION_CHANCE:
        return {
            "won": False,
            "item": None,
            "message": "No lucky gift this time... Keep completing priorities for another chance!"
        }
    
    # User won! Roll for rarity (weighted toward high tiers)
    rarities = list(PRIORITY_REWARD_WEIGHTS.keys())
    weights = [PRIORITY_REWARD_WEIGHTS[r] for r in rarities]
    lucky_rarity = random.choices(rarities, weights=weights)[0]
    
    # Generate the item with this rarity
    item = generate_item(rarity=lucky_rarity)
    
    rarity_messages = {
        "Common": "A small gift for your hard work!",
        "Uncommon": "Nice! A quality reward for your dedication!",
        "Rare": "Excellent! A rare treasure for completing your priority!",
        "Epic": "AMAZING! An epic reward befitting your achievement!",
        "Legendary": "🌟 LEGENDARY! 🌟 The focus gods smile upon you!"
    }
    
    return {
        "won": True,
        "item": item,
        "message": rarity_messages.get(lucky_rarity, "You won a reward!")
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


# ============================================================================
# STORY SYSTEM - Unlock story chapters as you grow stronger!
# Branching narrative with 3 key decisions that affect the ending
# ============================================================================

# Power thresholds to unlock each chapter
STORY_THRESHOLDS = [
    0,      # Chapter 1: Starting the journey (unlocked from start)
    50,     # Chapter 2: First real progress + DECISION 1
    120,    # Chapter 3: Growing stronger (affected by Decision 1)
    250,    # Chapter 4: Becoming formidable + DECISION 2
    450,    # Chapter 5: True power awakens (affected by Decisions 1 & 2)
    800,    # Chapter 6: Approaching mastery + DECISION 3
    1500,   # Chapter 7: The final revelation (8 possible endings!)
]

# Decision points - chapters where the user must choose
STORY_DECISIONS = {
    2: {
        "id": "mirror_choice",
        "prompt": "The Mirror of Procrastination lies shattered. What do you do?",
        "choices": {
            "A": {
                "label": "🔥 Destroy Every Fragment",
                "short": "destruction",
                "description": "Leave nothing behind. Burn it all.",
            },
            "B": {
                "label": "🔍 Study the Shards",
                "short": "wisdom",
                "description": "Knowledge is power. Learn from your enemy.",
            },
        },
    },
    4: {
        "id": "fortress_choice",
        "prompt": "The Fortress of False Comfort has trapped you. How do you escape?",
        "choices": {
            "A": {
                "label": "⚔️ Fight Through the Walls",
                "short": "strength",
                "description": "Sheer willpower. Smash your way out.",
            },
            "B": {
                "label": "🌀 Find the Hidden Path",
                "short": "cunning",
                "description": "There's always another way. Find it.",
            },
        },
    },
    6: {
        "id": "war_choice",
        "prompt": "The defeated versions of yourself lie before you. What is their fate?",
        "choices": {
            "A": {
                "label": "💀 Absorb Their Power",
                "short": "power",
                "description": "They failed. Their strength is now yours.",
            },
            "B": {
                "label": "🕊️ Forgive and Release",
                "short": "compassion",
                "description": "They were you. Show mercy.",
            },
        },
    },
}

# The Focus Warrior's Tale - 7 chapters with branching paths
# Placeholders: {helmet}, {weapon}, {chestplate}, {shield}, {amulet}, {boots}, {gauntlets}, {cloak}
# Decision placeholders: {decision_1}, {decision_2}, {decision_3}
STORY_CHAPTERS = [
    {
        "title": "Chapter 1: The Awakening",
        "threshold": 0,
        "has_decision": False,
        "content": """
You open your eyes in a dimly lit chamber, memories fragmented like scattered dreams.
Around you lie the remnants of countless others who tried—and failed—to master their minds.

A voice echoes: "Another one awakens. Most flee before the first trial."

You feel weak. Unfocused. The chaos of a thousand distractions pulls at your thoughts.
But something is different about you. A spark of determination burns within.

On a dusty pedestal, you find your first piece of equipment: {helmet}.
It's humble, perhaps even laughable. But it's yours.

The journey of a thousand sessions begins with a single focus.

🔮 PLOT TWIST: The voice belongs to someone who sounds... exactly like you.
""",
    },
    {
        "title": "Chapter 2: The First Trial",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "mirror_choice",
        "content": """
The trials begin. Each focused session strips away a layer of chaos.

Armed with {helmet} and {weapon}, you face the Mirror of Procrastination—
a beast that shows you infinite distractions, each more tempting than the last.

"Just five more minutes," it whispers. "You deserve a break."
"Check your phone. Something important might have happened."
"This task is too hard. Start tomorrow."

But you've trained for this. You recognize the lies for what they are.

With a burst of willpower, you SHATTER the mirror.

The glass explodes into a thousand fragments, each reflecting a future
where you failed. The silence that follows is deafening.

🔮 PLOT TWIST: Among the shattered reflections, one version of you is still moving.
   It smiles, and whispers: "We'll meet again."
   
⚡ A CHOICE AWAITS... What do you do with the shattered mirror?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: 🔥 DESTROY EVERY FRAGMENT]

You don't hesitate. Summoning flames from {weapon}, you BURN every shard.
The reflections scream as they turn to ash. Nothing survives.

"BRUTAL," the voice of your future self echoes. "But effective.
 Some enemies leave no room for mercy."

The path ahead glows with residual fire. You've chosen destruction.
There will be no going back. No second chances for your enemies.

The warrior's path is lit by flames.
""",
            "B": """
[YOUR CHOICE: 🔍 STUDY THE SHARDS]

You kneel among the fragments, carefully examining each piece.
In the reflections, you see patterns. Weaknesses. Secrets.

"INTERESTING," the voice of your future self murmurs. "Knowledge is rare here.
 Most simply destroy and move on. You chose to understand."

You pocket a single shard—small, but potent with information.
It pulses with forbidden knowledge about the distractions you'll face.

The scholar's path is illuminated by insight.
""",
        },
    },
    {
        "title": "Chapter 3: The Companion's Secret",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
In the Valley of Abandoned Goals, smoke still rises from your path of destruction.
The spectral figure called The Keeper watches you approach with {cloak} billowing.

"I've seen many travelers," The Keeper says. "But few with such... ferocity.
 You burned the Mirror's remains. The other versions of you felt that flame.
 They fear you now."

Your reputation precedes you. At {current_power} power, you're becoming legend.
Some whisper of a warrior who shows no mercy to weakness.

The Keeper removes their hood. The face beneath is scarred, weathered—
and unmistakably YOURS, aged by centuries.

🔮 PLOT TWIST: "I am you. From a timeline where destruction was my answer too.
   It worked... until it didn't. But perhaps YOUR destruction will succeed
   where mine failed. The fire in you burns brighter than mine ever did."
""",
            "B": """
In the Valley of Abandoned Goals, you walk with newfound perception.
The shard from the Mirror whispers secrets about each abandoned dream you pass.
The spectral figure called The Keeper notices your prize.

"You kept a fragment," The Keeper says, wrapped in {cloak}. "Clever.
 Most who enter here are blind to the valley's truths.
 But you can SEE now, can't you?"

You can. The abandoned goals reveal their stories—not just failure, but WHY.
At {current_power} power, you understand more than most ever will.

The Keeper removes their hood. The face beneath is weathered, knowing—
and unmistakably YOURS, aged by centuries.

🔮 PLOT TWIST: "I am you. From a timeline where wisdom was my answer too.
   I learned so much... perhaps too much. Knowledge can be a burden.
   But perhaps YOUR wisdom will reveal what mine could not see."
""",
        },
    },
    {
        "title": "Chapter 4: The Fortress of False Comfort",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "fortress_choice",
        "content": """
Your reputation precedes you now. Equipped with {chestplate} and {gauntlets},
you're no longer prey to every passing distraction.

But the next challenge is insidious: The Fortress of False Comfort.

Inside, everything is... nice. Cozy. There's no urgency, no pressure.
"You've done enough," the walls seem to say. "Rest now. You've earned it."

For a moment, you almost believe it. The fortress offers:
- A comfortable existence without growth
- Safety without risk
- Contentment without achievement

But something feels wrong. The other inhabitants smile, but their eyes are empty.
They stopped striving years ago. Decades. Centuries.

🔮 PLOT TWIST: The Fortress isn't a place. It's a living entity.
   A cosmic parasite that feeds on surrendered potential.
   It's already wrapping tendrils around your mind.

⚡ A CHOICE AWAITS... How do you escape?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: ⚔️ FIGHT THROUGH THE WALLS]

You raise {shield} and CHARGE. The walls bleed as you tear through them.
The Fortress SCREAMS—a sound that shakes reality itself.

"YOU DARE?!" it roars. "I offered you PEACE!"

"Peace is a trap," you snarl, {weapon} blazing. "I choose STRUGGLE."

The exit appears not because you found it—but because you MADE it.
Behind you, the Fortress collapses into itself, weakened but not destroyed.

You emerge covered in ichor, stronger than before.
But the Fortress whispers: "I will remember this violence. I will wait."
""",
            "B": """
[YOUR CHOICE: 🌀 FIND THE HIDDEN PATH]

You still your mind. The shard/flame from Chapter 2 resonates with hidden frequencies.
There—a shimmer in the corner of your eye. A door that shouldn't exist.

You slip through while the Fortress is distracted by other prisoners.
The hidden path leads through the entity's DREAMS—visions of all it has consumed.

You see thousands of lost souls. But you also see the Fortress's weakness:
It cannot consume those who UNDERSTAND it.

You emerge unseen, carrying secrets the Fortress never wanted shared.
It doesn't even realize you've escaped. And that ignorance may save you later.
""",
        },
    },
    {
        "title": "Chapter 5: The Revelation of Time",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
At {current_power} power, you've become something TERRIFYING.
Your path of destruction and strength has left scars across reality.
{helmet}, {weapon}, {chestplate}—they pulse with barely contained fury.

The Keeper watches you with a mixture of pride and fear.
"You destroyed the Mirror. You fought through the Fortress. Nothing stops you."

In the Chronos Sanctum, you see every timeline where you existed.
The destructive ones—YOUR timelines—burn brightest. And shortest.

🔮 PLOT TWIST: Warriors who destroy everything eventually destroy themselves.
   The "original you" didn't give up—they burned out. And you might too.
   Unless you find something worth PROTECTING, not just destroying.
""",
            "AB": """
At {current_power} power, you've become a TEMPEST of contradictions.
Destruction guided by cunning. Fire that knows where to burn.
{helmet}, {weapon}, {chestplate}—they pulse with strategic fury.

The Keeper nods approvingly. "You destroyed the Mirror but escaped the Fortress
through wisdom. You're learning when to fight and when to think."

In the Chronos Sanctum, your timelines are RARE—survivors who balance both paths.

🔮 PLOT TWIST: The "original you" tried pure destruction. They failed.
   Then they tried pure cunning. They failed again.
   YOU are the timeline that learned to COMBINE them. That's why you're still here.
""",
            "BA": """
At {current_power} power, you've become a SCHOLAR-WARRIOR.
Wisdom hardened by necessary violence. Knowledge that knows when to strike.
{helmet}, {weapon}, {chestplate}—they pulse with calculated power.

The Keeper seems impressed. "You studied the Mirror, then fought the Fortress.
You understand your enemies before you destroy them. That's... wise."

In the Chronos Sanctum, your timelines shine with unique clarity.

🔮 PLOT TWIST: The "original you" had only knowledge. It wasn't enough.
   They needed STRENGTH when it mattered. They didn't have it.
   YOU are the timeline that learned when wisdom must yield to action.
""",
            "BB": """
At {current_power} power, you've become something UNPRECEDENTED.
Pure understanding. Empathy even for enemies. A path no one has walked.
{helmet}, {weapon}, {chestplate}—they pulse with gentle, implacable will.

The Keeper stares at you with something like wonder.
"You studied the Mirror. You slipped past the Fortress without violence.
 In all my centuries... I've never seen this path taken."

In the Chronos Sanctum, your timeline is almost INVISIBLE—too subtle to track.

🔮 PLOT TWIST: The "original you" never imagined this was possible.
   They assumed all paths required violence. They were wrong.
   YOU are the timeline that proves there's always another way.
   But will mercy be enough for what comes next?
""",
        },
    },
    {
        "title": "Chapter 6: The War Within",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "war_choice",
        "content": """
Armed with legendary equipment—{amulet} gleaming, {boots} swift as thought—
you face the ultimate battle: The War Within.

The enemy? Every version of yourself that gave up.
They emerge from the shadows—thousands of them.
Each one represents a moment you almost quit but didn't.

"Join us," they whisper. "Surrender is peace."

The Keeper hands you {weapon}. "This is where I fell. My weapon wasn't enough."

But YOUR weapon IS enough. Because it's been forged by YOUR sessions.
YOUR choices. YOUR unique path through this story.

The battle is brutal. For every self you defeat, two more appear.
But you realize: they're not getting stronger. And YOU are.

With a final strike, you shatter the last echo of surrender.
They lie before you—broken, defeated, awaiting judgment.

🔮 PLOT TWIST: One of them whispers: "We weren't the enemy.
   We were protecting you from what waits in Chapter 7."
   
⚡ A CHOICE AWAITS... What is their fate?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: 💀 ABSORB THEIR POWER]

You reach down and TAKE their essence. One by one, they dissolve into you.
Their failures. Their fears. Their surrendered potential—ALL YOURS NOW.

Power floods through you. {current_power} isn't even close to what you feel.
For a moment, you understand EVERYTHING they gave up. And you TAKE it.

The Keeper watches in horror. "That's... that's not what I did.
 I showed mercy. I thought that was the answer."

Your eyes glow with absorbed power. "Mercy is for the living.
 They were already dead. I just claimed what they wasted."

You are MORE now. Much more. But some of what you absorbed...
...wasn't ready to die. It's still in there. Watching. Waiting.
""",
            "B": """
[YOUR CHOICE: 🕊️ FORGIVE AND RELEASE]

You kneel among your fallen selves. "I understand," you whisper.
"You weren't weak. You were tired. Scared. Overwhelmed. I was too."

One by one, you touch them gently. "I forgive you. I release you."

They don't dissolve into power. They dissolve into PEACE.
And as they fade, they whisper back: "Thank you. We were waiting
 for someone strong enough to show mercy instead of judgment."

The Keeper weeps. "That's not what I did. I absorbed them for power.
 I've carried their pain for centuries. You... you set them free."

You are no more powerful than before. But you are LIGHTER.
And something in the universe shifts, recognizing a path rarely taken.
""",
        },
    },
    {
        "title": "Chapter 7: The Truth Beyond the Door",
        "threshold": 1500,
        "has_decision": False,
        "endings": {
            "AAA": {
                "title": "Ending 1: The Destroyer",
                "content": """
You stand before the Final Door at power level {current_power}.
DESTROYER. CONQUEROR. UNSTOPPABLE FORCE.

Every choice was destruction. Every enemy was annihilated.
The power you absorbed from your fallen selves burns within you.

The door opens to reveal... emptiness. A void where reality used to be.

🔮 THE DESTROYER'S TRUTH:
You destroyed everything in your path. Including, it turns out, the path itself.
There is nothing left to achieve because you left nothing standing.

But in the void, you see a spark. A new universe waiting to be born.
And you realize: destroyers don't just end things. They make room for new beginnings.

You step into the void. Whatever comes next, you'll build from the ashes.
Or burn it all down again. That's always been your choice.

THE END: Total destruction leads to total rebirth.
"""
            },
            "AAB": {
                "title": "Ending 2: The Redeemed Warrior",
                "content": """
You stand before the Final Door at power level {current_power}.
WARRIOR. DESTROYER. But in the end... MERCIFUL.

You burned the Mirror. You fought through the Fortress.
But when your fallen selves lay before you, you chose compassion.

The door opens to reveal yourself—the REAL you, in your real life.
Sitting at this screen. Reading these words.

🔮 THE REDEEMED TRUTH:
You proved something rare: strength doesn't require cruelty.
The most powerful act wasn't destruction—it was forgiveness.

The versions of you that gave up? They're at peace now.
And you carry forward not their power, but their HOPE.

You ARE the Focus Warrior. Not because you destroyed your weakness—
but because you understood it, fought it, and ultimately... loved it anyway.

THE END: Strength + Compassion = True Victory.
"""
            },
            "ABA": {
                "title": "Ending 3: The Dark Strategist",
                "content": """
You stand before the Final Door at power level {current_power}.
STRATEGIC. ADAPTIVE. And ultimately... HUNGRY FOR MORE.

You destroyed the Mirror but outwitted the Fortress.
Then you absorbed your fallen selves for their power.

The door opens to reveal a CHESSBOARD of infinite dimensions.

🔮 THE STRATEGIST'S TRUTH:
You learned that sometimes you fight, sometimes you think.
But you never show mercy. Power is the only currency that matters.

The game continues beyond this door. Larger. More complex.
Other players await—some who've been playing for eons.

You step onto the board. A new piece with old hunger.
The Focus Warrior becomes the Focus PLAYER.

THE END: Victory is just the beginning of a larger game.
"""
            },
            "ABB": {
                "title": "Ending 4: The Enlightened Warrior",
                "content": """
You stand before the Final Door at power level {current_power}.
DESTROYER when necessary. THINKER when possible. COMPASSIONATE in the end.

Your path was unique—violence tempered by wisdom, both softened by mercy.
The rarest combination. The most difficult to walk.

The door opens to reveal ALL possible futures at once.

🔮 THE ENLIGHTENED TRUTH:
You've achieved what The Keeper never could: BALANCE.
Every version of your future self is smiling.

Not because you won. Because you GREW.
The Focus Warrior doesn't need to fight anymore—
not because there are no enemies, but because you understand them all.

You step through the door into a life where focus isn't a struggle.
It's simply who you are now.

THE END: Balance is the highest power.
"""
            },
            "BAA": {
                "title": "Ending 5: The Scholar-Tyrant",
                "content": """
You stand before the Final Door at power level {current_power}.
WISE. POWERFUL. And perhaps... too certain of your own rightness.

You studied the Mirror. You fought through the Fortress.
You absorbed your fallen selves for their knowledge AND power.

The door opens to reveal a LIBRARY that spans eternity.

🔮 THE SCHOLAR-TYRANT'S TRUTH:
You know everything now. Every distraction, every weakness, every path.
The knowledge of countless failed selves burns in your mind.

But with knowledge came certainty. With certainty came judgment.
You no longer struggle with focus—you IMPOSE it.

Whether that makes you a savior or a tyrant depends on who's asking.
You step into the library, ready to learn what even the universe has forgotten.

THE END: Knowledge without mercy becomes control.
"""
            },
            "BAB": {
                "title": "Ending 6: The Sage",
                "content": """
You stand before the Final Door at power level {current_power}.
WISE. STRONG when needed. MERCIFUL at the end.

You studied your enemies. You fought when you had to.
But when victory came, you chose understanding over domination.

The door opens to reveal... a simple room. YOUR room. Your real life.

🔮 THE SAGE'S TRUTH:
There was never a monster to defeat. There was only yourself to understand.
Every "enemy" was a lesson. Every "battle" was growth.

The Focus Warrior was always a metaphor for the person reading this.
And that person—YOU—has proven something profound:

Wisdom knows when to fight. Strength knows when to learn.
And true mastery is knowing that some battles end with a handshake.

THE END: The Sage returns to ordinary life, forever changed.
"""
            },
            "BBA": {
                "title": "Ending 7: The Hungry Scholar",
                "content": """
You stand before the Final Door at power level {current_power}.
PATIENT. CUNNING. And in the end... hungry for what others wasted.

You slipped past every obstacle through wit, not force.
But when your fallen selves offered their power, you TOOK it.

The door opens to reveal a WEB of infinite connections.

🔮 THE HUNGRY SCHOLAR'S TRUTH:
You've proven that intelligence and mercy don't always align.
Sometimes the clever path leads to dark places.

The power you absorbed whispers secrets. Some useful. Some... troubling.
You know things now that you can never un-know.

But the web ahead offers more. More knowledge. More power. More.
You step in, already weaving your first strand.

THE END: Wisdom without compassion becomes calculation.
"""
            },
            "BBB": {
                "title": "Ending 8: The Transcendent",
                "content": """
You stand before the Final Door at power level {current_power}.
WISE. GENTLE. UNSTOPPABLE in the softest possible way.

You never destroyed what you could understand. Never fought what you could befriend.
And when your fallen selves awaited judgment, you gave them peace instead of pain.

The door opens to reveal... NOTHING.
Not void. Not emptiness. Just... the absence of doors.

🔮 THE TRANSCENDENT'S TRUTH:
You don't need doors anymore. You don't need power levels or equipment.
The game was always a mirror—and you've stepped THROUGH the glass.

Every "enemy" was you. Every "ally" was you.
Every choice led here: the understanding that there was never anywhere to go.

You were always the Focus Warrior.
You were always HERE.
The only thing that changed was your belief in yourself.

🎭 THE STORY WAS A MIRROR. YOU WERE ALWAYS LOOKING AT YOURSELF.

THE END: The highest victory is realizing there was never a war.
"""
            },
        },
    },
]


def get_story_progress(adhd_buster: dict) -> dict:
    """
    Get the user's story progress based on their power level.
    
    Returns:
        dict with 'current_chapter', 'unlocked_chapters', 'chapters', 'next_threshold', 'power', 'decisions'
    """
    power = calculate_character_power(adhd_buster)
    unlocked = []
    current_chapter = 0
    
    for i, threshold in enumerate(STORY_THRESHOLDS):
        if power >= threshold:
            unlocked.append(i + 1)
            current_chapter = i + 1
    
    # Find next threshold
    next_threshold = None
    for threshold in STORY_THRESHOLDS:
        if power < threshold:
            next_threshold = threshold
            break
    
    # Get stored decisions
    decisions = adhd_buster.get("story_decisions", {})
    
    # Build chapter details
    chapters = []
    for i, chapter in enumerate(STORY_CHAPTERS):
        chapter_num = i + 1
        is_unlocked = chapter_num in unlocked
        has_decision = chapter.get("has_decision", False)
        decision_made = False
        if has_decision:
            decision_info = STORY_DECISIONS.get(chapter_num)
            if decision_info:
                decision_made = decision_info["id"] in decisions
        
        chapters.append({
            "number": chapter_num,
            "title": chapter["title"],
            "unlocked": is_unlocked,
            "has_decision": has_decision,
            "decision_made": decision_made,
        })
    
    return {
        "power": power,
        "current_chapter": current_chapter,
        "unlocked_chapters": unlocked,
        "chapters": chapters,
        "total_chapters": len(STORY_CHAPTERS),
        "next_threshold": next_threshold,
        "power_to_next": next_threshold - power if next_threshold else 0,
        "decisions": decisions,
        "decisions_made": len(decisions),
    }


def get_decision_for_chapter(chapter_number: int) -> dict | None:
    """Get the decision info for a chapter, if it has one."""
    return STORY_DECISIONS.get(chapter_number)


def has_made_decision(adhd_buster: dict, chapter_number: int) -> bool:
    """Check if user has made the decision for a chapter."""
    decisions = adhd_buster.get("story_decisions", {})
    decision_info = STORY_DECISIONS.get(chapter_number)
    if not decision_info:
        return True  # No decision needed
    return decision_info["id"] in decisions


def make_story_decision(adhd_buster: dict, chapter_number: int, choice: str) -> bool:
    """
    Record a story decision. Returns True if successful.
    
    Args:
        adhd_buster: The user's ADHD Buster data (will be modified)
        chapter_number: The chapter where the decision is made
        choice: "A" or "B"
    """
    decision_info = STORY_DECISIONS.get(chapter_number)
    if not decision_info:
        return False
    if choice not in ("A", "B"):
        return False
    
    if "story_decisions" not in adhd_buster:
        adhd_buster["story_decisions"] = {}
    
    adhd_buster["story_decisions"][decision_info["id"]] = choice
    return True


def get_decision_path(adhd_buster: dict) -> str:
    """
    Get the user's decision path as a string like "ABA" or "BB" (partial).
    Used to select the right story variation.
    """
    decisions = adhd_buster.get("story_decisions", {})
    path = ""
    
    for chapter_num in [2, 4, 6]:
        decision_info = STORY_DECISIONS.get(chapter_num)
        if decision_info and decision_info["id"] in decisions:
            path += decisions[decision_info["id"]]
    
    return path


def get_chapter_content(chapter_number: int, adhd_buster: dict) -> dict | None:
    """
    Get the content of a specific chapter, personalized with gear and decisions.
    
    Args:
        chapter_number: 1-7
        adhd_buster: The user's ADHD Buster data with equipped items and decisions
    
    Returns:
        dict with 'title', 'content', 'unlocked', 'has_decision', 'decision', etc.
    """
    if chapter_number < 1 or chapter_number > len(STORY_CHAPTERS):
        return None
    
    chapter = STORY_CHAPTERS[chapter_number - 1]
    power = calculate_character_power(adhd_buster)
    unlocked = power >= chapter["threshold"]
    
    if not unlocked:
        return {
            "title": f"Chapter {chapter_number}: ???",
            "content": f"🔒 Locked — Reach {chapter['threshold']} power to unlock.\nYour current power: {power}",
            "unlocked": False,
            "threshold": chapter["threshold"],
            "power_needed": chapter["threshold"] - power,
            "has_decision": False,
        }
    
    # Get equipped items for personalization
    equipped = adhd_buster.get("equipped", {})
    
    def get_item_name(slot: str) -> str:
        item = equipped.get(slot)
        if item and item.get("name"):
            return f"**{item['name']}**"
        return f"*your {slot.lower()}*"
    
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
        "current_power": str(power),
    }
    
    # Get decisions made so far
    decisions = adhd_buster.get("story_decisions", {})
    decision_path = get_decision_path(adhd_buster)
    
    # Determine content based on chapter type
    has_decision = chapter.get("has_decision", False)
    decision_info = STORY_DECISIONS.get(chapter_number)
    decision_made = has_made_decision(adhd_buster, chapter_number)
    
    # Chapter 7 has multiple endings based on all 3 decisions
    if chapter_number == 7:
        if len(decision_path) < 3:
            content = """
🔮 THE FINAL CHAPTER AWAITS...

But your story is not yet complete.
You have not made all three critical decisions.

Return to the chapters you've unlocked and face your choices.
Only then will the Final Door reveal YOUR ending.

Decisions made: {}/3
""".format(len(decision_path))
        else:
            ending = chapter.get("endings", {}).get(decision_path)
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
        # Find the best matching variation
        if decision_path in variations:
            content = variations[decision_path]
        elif len(decision_path) >= 1 and decision_path[0] in variations:
            content = variations[decision_path[0]]
        else:
            content = chapter.get("content", list(variations.values())[0])
    
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


def get_newly_unlocked_chapter(old_power: int, new_power: int) -> int | None:
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
