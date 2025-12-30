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
        "title": "⚔️ The Focus Warrior's Tale",
        "description": "A classic hero's journey. Battle your inner demons and conquer the fortress of distraction.",
        "theme": "combat",
    },
    "scholar": {
        "id": "scholar", 
        "title": "📚 The Mind Architect's Path",
        "description": "Build the perfect mental fortress. Knowledge and strategy are your weapons.",
        "theme": "intellect",
    },
    "wanderer": {
        "id": "wanderer",
        "title": "🌙 The Dream Walker's Journey",
        "description": "Navigate the surreal dreamscape of your subconscious. Reality bends to your will.",
        "theme": "mystical",
    },
    "underdog": {
        "id": "underdog",
        "title": "🏆 The Unlikely Champion",
        "description": "A regular person vs. an impossible boss. Office politics, real stakes, and sweet victory.",
        "theme": "realistic",
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
                "label": "🔥 Burn Every Shard",
                "short": "destruction",
                "description": "Incinerate everything. No mercy for your reflections.",
            },
            "B": {
                "label": "🔍 Study the Fragments",
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
                "label": "⚔️ Fight Through the Walls",
                "short": "strength",
                "description": "Destroy the Fortress from the inside. Violently.",
            },
            "B": {
                "label": "🌀 Find the Hidden Path",
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
                "label": "💀 Absorb Their Power",
                "short": "power",
                "description": "Take their darkness. Become unstoppable.",
            },
            "B": {
                "label": "🕊️ Forgive and Release",
                "short": "compassion",
                "description": "They were you. Show mercy. Embrace wholeness.",
            },
        },
    },
}

# The Focus Warrior's Tale - 7 chapters with branching paths
# A dramatic adventure with humor, romance, betrayal, and LOTS of plot twists
# Placeholders: {helmet}, {weapon}, {chestplate}, {shield}, {amulet}, {boots}, {gauntlets}, {cloak}
WARRIOR_CHAPTERS = [
    {
        "title": "Chapter 1: The Awakening",
        "threshold": 0,
        "has_decision": False,
        "content": """
You wake up face-down in what appears to be... an abandoned productivity seminar?

Motivational posters hang crooked on the walls. "JUST DO IT" says one, but someone
crossed out "DO" and wrote "PROCRASTINATE." The irony is not lost on you.

"Oh good, you're alive," says a bored voice. "That's more than I can say for the last
twelve awakeners. They saw the to-do list, made eye contact with it, and immediately gave up."

You turn to find a SPECTRAL FIGURE in a {cloak} that shimmers between dimensions.
Their face is hidden, but somehow you can FEEL them rolling their eyes.

"I'm THE KEEPER," they sigh. "Guide to the realm, mentor to the hopeless, unpaid customer support.
Before you ask: yes, this is real. No, you can't leave. Yes, there's a bathroom. No, I won't hold your hand."

On a dusty pedestal lies {helmet}. It's... not impressive.

"Don't look at me like that," The Keeper says. "We're on a budget. The good stuff
is earned, not given. Though honestly, most people die before unlocking Chapter 2."

"Die?!"

"Metaphorically. They just... stop trying. Same thing, really."

You put on {helmet}. It smells like forgotten New Year's resolutions.

"Perfect fit," The Keeper lies unconvincingly. "Now—"

The wall EXPLODES inward. A figure in gleaming obsidian armor strides through,
radiating malice and inexplicable charisma.

🔮 PLOT TWIST: THE ARCHON OF DISTRACTION. Your main antagonist. And somehow...
   devastatingly attractive. This is going to be a problem.

"Ah, another awakener," The Archon purrs. "How... adorable. I give you three days
before you're scrolling through my realm forever."

They vanish in a swirl of notification sounds.

"That was The Archon," The Keeper says flatly. "They run this place.
Also, they used to be my friend. It's a whole thing. Don't ask. And don't flirt.
Yes, even if they start it."

Your journey begins with maximum confusion. As all good journeys do.
""",
    },
    {
        "title": "Chapter 2: The First Trial",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "warrior_mirror",
        "content": """
The Keeper's training montage was... intense. And slightly humiliating.

"No," The Keeper says for the fiftieth time, dead-eyed. "You don't CHECK YOUR PHONE
during a focus session. What part of 'battle concentration' is reading as optional?"

But you've improved. {weapon} now feels like an extension of your will.
Your power level has climbed to something The Keeper calls "almost not embarrassing."

Now you face the MIRROR OF PROCRASTINATION—a towering looking glass that reflects
not your image, but your BROWSER HISTORY.

"Oh god," you whisper, seeing yourself watching cat videos at 3 AM.

"The Mirror shows what you waste yourself on," The Keeper explains.
"Defeat it, and you break free from—"

"IS THAT ME REORGANIZING MY DESKTOP FOR FOUR HOURS?"

"...Yes. The Mirror is thorough."

The Mirror begins its assault. "Just one more episode," it croons.
"You can start tomorrow. You deserve a break. Check if anyone liked your post."

But armed with {helmet} and {weapon}, you SHATTER the glass.
A thousand reflections scream in unison as reality fractures.

And then—

ONE REFLECTION SURVIVES. Crawling from the wreckage.
It looks EXACTLY like you, but with a sinister smirk.

"Finally," it says. "I've been WAITING for someone strong enough to free me."

Before you can react, it bolts toward The Archon's realm.

🔮 PLOT TWIST: You didn't just break a mirror. You released your SHADOW SELF—
   the version of you that embraced distraction completely. And it's fast.

"Well," The Keeper says. "That's... new. And concerning. Very concerning."

"Also, on the bright side: you've made it further than the seminar crowd," they mutter.

⚡ A CHOICE AWAITS... The shattered mirror fragments still pulse with power.
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: 🔥 DESTROY EVERY FRAGMENT]

You won't make the same mistake twice. With {weapon} blazing, you INCINERATE every shard.

The screaming reflections turn to ash. The glass melts. Nothing survives.

The Keeper watches with raised eyebrows. "Brutal. Effective. Slightly terrifying."

"Remind me not to lend you anything fragile," they add.

But as the last fragment burns, you feel something: POWER flooding into you.
The destroyed reflections had to go SOMEWHERE. They chose you.

Your eyes glow briefly. {helmet} feels heavier, more substantial.

"Interesting," a voice echoes from nowhere. The Archon's voice.
"You destroy without hesitation. I might have use for someone like you."

The Keeper's expression darkens. "Don't listen to them. That's how it starts."

🔮 PLOT TWIST: The Archon is watching. They've always been watching.
   And they seem... impressed? That's probably not good.
""",
            "B": """
[YOUR CHOICE: 🔍 STUDY THE SHARDS]

"Wait," you say, kneeling among the fragments. "There's something here."

Each shard contains data—patterns of distraction, weakness maps, trigger warnings.
It's a goldmine of self-knowledge, painful but invaluable.

"Huh," The Keeper says, genuinely surprised. "Most people just smash and move on.
You're actually LEARNING from your failures. That's... rare."

You pocket a single shard. It pulses with uncomfortable truths about yourself.
But truth is armor against the lies ahead.

A slow clap echoes from the shadows. The Archon steps out, smiling.

"A thinker. How refreshing. The destroyers are so... predictable."
Their eyes meet yours with unsettling intensity. "We should talk sometime."

They vanish before you can respond. Your heart is beating faster than it should be.

The Keeper groans. "Great. They're interested in you. That's always complicated."

🔮 PLOT TWIST: The Archon is intrigued. And you felt something too.
   This is going to get messy.
""",
        },
    },
    {
        "title": "Chapter 3: The Companion's Secret",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
Your path of destruction has carved a legend across the realm.
Warriors whisper of the one who burns without mercy. The fire-walker. The ash-maker.

In the Valley of Abandoned Goals, spectral projects float like ghosts:
"Learn guitar." "Start a business." "Call mom more." "Finish that novel."

You feel vaguely guilty. Some of these look familiar.

"Everyone's goals end up here eventually," The Keeper says. "Don't dwell on it.
Most of these were doomed from the start. Statistically. Not morally."

You're about to respond when a figure emerges from the mist.

Tall. Graceful. Wielding a blade that shimmers like starlight.
And wearing an expression of profound annoyance.

"YOU'RE the famous destroyer?" she says. "Smaller than I expected."

"LYRA!" The Keeper stumbles backward. "You're—you're supposed to be—"

"Dead? Exiled? Working for The Archon?" Lyra laughs bitterly.
"All true at various points. It's been a complicated century."

She turns to you. "I've been watching you, fire-walker. Burning everything in your path.
Very dramatic. Very stupid. You have no idea what you've released."

"My Shadow Self? I know it—"

"Not THAT." Lyra's eyes darken. "Every reflection you burned? Every mirror-ghost?
They didn't die. They went to THEM. The Archon is FEEDING on your destruction."

"You're not just fighting the realm," she adds, voice low. "You're stocking their pantry." 

🔮 PLOT TWIST: Lyra is The Keeper's former partner—and The Archon's ex.
    Congratulations: you've wandered into the love triangle from hell.

"We need to talk," Lyra says. "All of us. About what you've started."

Your {cloak} billows dramatically. At {current_power} power, you're finally
being treated as a player, not a piece.

The question is: whose side is Lyra really on?
""",
            "B": """
Your path of wisdom has earned whispers of a different kind.
The thinker. The one who sees. The warrior who fights with knowledge.

In the Valley of Abandoned Goals, you walk with the mirror shard pulsing in your pocket.
It whispers secrets about each floating dream: "This one was never really wanted."
"This one was sabotaged by fear." "This one was STOLEN."

Wait. Stolen?

A figure emerges from the mist before you can investigate.

Tall. Graceful. Wielding a blade that shimmers like starlight.
And wearing an expression of reluctant respect.

"YOU'RE the famous scholar-warrior?" she says. "Smarter than you look."

"LYRA!" The Keeper nearly trips over their {cloak}. "You're supposed to be—"

"Dead? Exiled? It's been complicated." Lyra's smile doesn't reach her eyes.
"I've been watching this one. They kept a shard. They're actually THINKING."

She turns to you. "That's rare here. Most awakeners are all muscle, no mind.
You might actually survive what's coming."

"What's coming?"

Lyra glances at The Keeper with an expression loaded with history.
"Tell them. About The Archon. About what you two did. About ME."

The Keeper looks away. "Lyra..."

"TELL THEM."

🔮 PLOT TWIST: Lyra is The Keeper's former partner. Before The Archon.
   Before the fall. Before everything broke.

"The Archon wasn't always a monster," The Keeper whispers. "They were like you once.
An awakener. A student. MY student. And I..."

"You loved them," Lyra finishes coldly. "And I wasn't enough."

The tension is thick enough to cut with {weapon}. At {current_power} power,
you're finally learning the real story. And it's messier than you imagined.
""",
        },
    },
    {
        "title": "Chapter 4: The Fortress of False Comfort",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "warrior_fortress",
        "content": """
The truth is out. The full story has finally been revealed:

The Archon was once an awakener—the greatest The Keeper ever trained.
They were close. Too close. When The Archon reached the Final Door,
they couldn't bear to leave. So they became THIS. Ruler of distractions.

The Keeper stayed—not to stop them, but because they couldn't let go either.
Lyra lost the people she loved to this obsession. Everyone got hurt.

Now the three of you walk together, bound by complicated history.

Lyra hasn't spoken since the revelation. She walks ahead, shoulders rigid.
The love triangle you accidentally stepped into is somehow YOUR problem now.

"Don't look at me like that," The Keeper mutters without looking up. "I didn't schedule any of this."

But there's no time for drama. You've reached THE FORTRESS OF FALSE COMFORT.

"Oh no," you whisper.

The Fortress is everything you've ever wanted. A perfect room with perfect lighting.
Snacks that never run out. Entertainment that never bores. Zero obligations forever.

"It's a trap," The Keeper warns. "The Fortress feeds on surrendered potential."

But it looks so NICE. What's wrong with a little rest?

And then you see them: the INHABITANTS. Thousands of awakeners who came before.
They sit in comfortable chairs, eyes glazed, scrolling through infinite feeds.
Some have been here so long they've become furniture.

"Welcome," the Fortress croons. "You've worked so hard. Don't you deserve this?"

Lyra grabs your arm. "Don't listen. This is how we lost—"

She stops. Staring at one of the inhabitants.

"KIRA?!" She runs to a figure slumped in a bean bag.
"No. No no no. She can't be here. She escaped. I SAW her escape."

The figure doesn't respond. Lost forever in false comfort.

🔮 PLOT TWIST: Kira was Lyra's sister. And she didn't escape.
   The Archon LIED about letting her go. This just got personal.

⚡ A CHOICE AWAITS... Lyra is spiraling. The Fortress is closing in.
   How do you get everyone out?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: ⚔️ FIGHT THROUGH THE WALLS]

"ENOUGH!" You raise {shield} and CHARGE into the nearest wall.

It SCREAMS. The Fortress is ALIVE, and you're tearing through its flesh.
The inhabitants wake briefly, blinking in confusion, before sinking back.

"Burn it," Lyra snarls, grief transforming to rage. "Burn it ALL."

Together, you carve a path of destruction through the Fortress's guts.
{weapon} blazes. {gauntlets} punch through muscle-memory walls.

The Fortress wails: "UNGRATEFUL! I OFFERED YOU EVERYTHING!"

"Everything except freedom," you growl.

You burst through the final wall, dragging Lyra and The Keeper behind you.
The Fortress collapses inward, consuming the inhabitants you couldn't save.
Including Kira.

Lyra falls to her knees. "She's gone. I couldn't—"

"We'll make The Archon pay," you promise. "For all of it."

🔮 PLOT TWIST: As the Fortress dies, you hear The Archon's laughter.
   "Thank you for destroying my competition. One less distraction in my way."
   You were USED. And you're furious.
""",
            "B": """
[YOUR CHOICE: 🌀 FIND THE HIDDEN PATH]

"Stop." You grab Lyra's arm. "Rage won't save her. THINK."

Something pulses—a resonance from your earlier battles. The power you carry
is detecting something: a hidden frequency. A door that shouldn't exist.
A path the Fortress doesn't know about.

"There." You point to a shimmer in the corner. "We slip out. Then we come back
with an army. We save EVERYONE, not just ourselves."

Lyra's grief wars with hope. "You really think...?"

"I KNOW. But not if we're dead."

You lead them through the hidden door—into the Fortress's DREAMS.
Visions of everyone it's consumed. Thousands of lives on pause.

Including Kira. Frozen in a memory loop, but ALIVE.

"The inhabitants aren't dead," you realize. "They're backed up.
The Fortress stores them. For later consumption."

"Then we can bring them back," The Keeper breathes. "All of them."

"Assuming we survive the part where everything tries to eat us," they add.

You emerge unseen, carrying knowledge the Fortress never meant to share.
Kira isn't saved—not yet. But now you know HOW.

🔮 PLOT TWIST: You found the Fortress's vulnerability. It stores its victims.
   Which means The Archon's realm might do the same.
   Every awakener who ever "failed" might still be rescuable.
""",
        },
    },
    {
        "title": "Chapter 5: The Revelation of Time",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
At {current_power} power, your legend has grown to terrifying proportions.
DESTROYER. FORTRESS-KILLER. THE ONE WHO BURNS.

Lyra walks beside you now, forged by shared grief into something dangerous.
The Keeper trails behind, watching you both with growing concern.

"You're becoming like THEM," they mutter. "Like The Archon was. Before."

"Maybe that's what it takes," you reply. "To win."

"That's what everyone says right before the dramatic villain monologue," The Keeper says.

The Chronos Sanctum opens before you—a place where all timelines converge.
Here, you can see every version of yourself that ever existed.

The destructive ones burn brightest. And shortest.

🔮 PLOT TWIST: In EVERY timeline where you chose destruction...
   you eventually become The Archon's successor. Their HEIR.

"They're not fighting you," The Keeper says quietly. "They're GROOMING you.
Every battle you win through violence makes you more like them."

Lyra stares at you with new eyes. "Is that true? Are you...?"

You don't know anymore. The fire feels so GOOD when it burns.
But in the Sanctum's visions, the fire always consumes its wielder.

"There might be another way," The Keeper offers. "But it requires something
you've never tried: fighting ALONGSIDE The Archon. Temporarily."

"WHAT?!"

🔮 PLOT TWIST: The Keeper has been in contact with The Archon.
   They have a plan. A desperate, possibly suicidal plan.
   And they need all three of you to execute it.
""",
            "AB": """
At {current_power} power, you've become something unprecedented.
DESTROYER when needed. THINKER when possible. A weapon AND a mind.

Lyra respects you. The Keeper fears you—but in an impressed way.
Together, you've become an unlikely family.

"You remind me of them," The Keeper admits one night. "The Archon. Before."

"Is that bad?"

"I don't know yet. They had your fire. But they lacked your..."
They search for the word. "...flexibility. You ADAPT."

The Chronos Sanctum reveals its secrets. You see infinite timelines—
and in the rare ones where awakeners survive AND stay sane...
they always walk the middle path. Destruction balanced by wisdom.

Like you.

🔮 PLOT TWIST: The Archon is watching through a timeline crack.
   "Impressive," they murmur. "You're not like the others. You could be my equal."

Their presence is intoxicating. Terrifying. Something in you responds.

"Don't," Lyra warns. "I saw that look on The Keeper's face once.
Before The Archon broke their heart."

"It's not like that—"

"It's EXACTLY like that. The Archon collects people like you.
Interesting ones. Promising ones. Then they corrupt them."

🔮 PLOT TWIST: But what if... you could corrupt THEM instead?
   The thought arrives unbidden. Seductive. Dangerous.
""",
            "BA": """
At {current_power} power, you've earned a new title: THE SCHOLAR-WARRIOR.
Knowledge first, violence when necessary. It's an elegant philosophy.

And it's attracted attention.

"The Archon has requested a meeting," The Keeper announces grimly.

"A TRAP," Lyra snarls.

"Obviously. But..." The Keeper hesitates. "They've offered something.
Information about how to avenge the Fortress's victims. Including Kira."

Lyra's rage falters. "What do they want in return?"

"Just... a conversation. With you." They look at you with complicated eyes.

The meeting happens in the Chronos Sanctum—neutral ground where no one can lie.
The Archon appears in full glory: devastating, powerful, achingly beautiful.

"You studied the Mirror instead of destroying it," they say. "Fascinating."
"You fought through the Fortress when it threatened your friends. Bold."
"I've watched you, little scholar. You're not like the others."

"What do you want?"

The Archon smiles. "What I've always wanted. A worthy equal."

🔮 PLOT TWIST: They're not lying. The Sanctum confirms it.
   The Archon genuinely wants... you. As a partner. A co-ruler.
   And part of you—a bigger part than you'd like—is tempted.
""",
            "BB": """
At {current_power} power, you've become something the realm has never seen.
THE GENTLE WARRIOR. THE ONE WHO REFUSES TO DESTROY.

It baffles everyone. Especially The Archon.

"I don't understand you," they say during your unexpected summit.
The Chronos Sanctum forces honesty; they can't pretend otherwise.

"You had every excuse to burn. To hate. To become like everyone else.
But you keep CHOOSING differently. Why?"

"Because destruction doesn't work," you reply. "Look at you.
The most powerful being here. And you're MISERABLE."

The Archon flinches. The Sanctum glows—truth confirmed.

"I built this empire to avoid pain," they admit. "But it followed me.
It ALWAYS follows. No matter how many distractions I create."

"Then maybe it's not running you need. It's facing."

For a moment—just a moment—you see something vulnerable in The Archon's eyes.
Something that might have been human, once. Before the armor. Before the title.

🔮 PLOT TWIST: The Archon was an awakener like you. They loved The Keeper.
   The Keeper loved Lyra. Everyone got hurt. Everyone ran.
   And now they're all stuck here, pretending to be enemies.

"There might be another way," you say carefully. "A way EVERYONE goes home."

The Archon laughs bitterly. "Home? I don't remember what that means."

"Then let me remind you."

Lyra watches you with a mixture of horror and hope.
Are you naive? Or are you the first person in centuries to try COMPASSION?
""",
        },
    },
    {
        "title": "Chapter 6: The War Within",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "warrior_war",
        "content": """
Armed with legendary equipment—{amulet} blazing, {boots} lighter than thought—
you face the ultimate confrontation.

But the enemy isn't The Archon. Not yet.

Remember your SHADOW SELF? The reflection that escaped in Chapter 2?
It's been busy. VERY busy.

It found The Archon. Pledged loyalty. Absorbed power.
And now it leads THE ARMY OF ABANDONED SELVES—every version of you that ever quit.

They emerge from the darkness. THOUSANDS of them.

"Oh, this is bad," Lyra says, drawing her blade.
"I've seen bad," The Keeper replies. "This is worse. With a budget and a soundtrack."

Your Shadow Self steps forward, wearing inverted versions of YOUR equipment.
Where {helmet} shines, theirs absorbs light. Where {weapon} glows, theirs corrupts.

"Hello, original," it says with your face and your voice and none of your soul.
"I've been waiting for this. You created me. Now I'll destroy you."

The battle is BRUTAL. For every self you defeat, two more arise.
Lyra and The Keeper fight beside you, but they're overwhelmed.

And then—

THE ARCHON APPEARS.

"Interesting," they say, watching the chaos. "Your own darkness, given form.
Poetic, really. This is what happens to all awakeners eventually."

"HELP US," you gasp.

"Why would I?" The Archon tilts their head. "You winning or losing—
either outcome benefits me."

But something flickers in their eyes. A memory of who they used to be.

The Keeper shouts: "REMEMBER WHAT WE WERE! All of us! Before this started!"

🔮 PLOT TWIST: The Archon hesitates. For the first time in centuries... 
   they remember being human. Being loved. Being GOOD.

Your Shadow Self strikes you down. You're on the ground. Dying.

The Archon makes a choice.

They join the battle. AGAINST their own army.

"Don't make me regret this," they snarl, obliterating a wave of shadow-selves.

Together—the four of you—you push back the tide. The Shadow Army breaks.
Your Shadow Self stands alone, surrounded, defeated.

⚡ A CHOICE AWAITS... It kneels before you, awaiting judgment.
   What is its fate?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: 💀 ABSORB THEIR POWER]

"You wasted everything I could have been," you snarl.

You reach out and ABSORB your Shadow Self. Every dark thought, every failure,
every moment of weakness—it floods into you, becoming POWER.

Your eyes glow with terrible light. {current_power} doesn't describe what you feel.
For a moment, you understand EVERYTHING about distraction. About weakness.
Because you've absorbed it all.

"YES," The Archon breathes. "Now you understand. This is how I began.
Absorbing my failures. Becoming something MORE."

The Keeper looks at you with horror. "You're... you're becoming like—"

"No," The Keeper snaps, then catches themselves. "Just... hear yourself."

"Like what I need to be," you finish. "To win."

Lyra steps away from you, hand on her sword. "Is there anything left of you?
The REAL you? Or is this just another monster wearing your face?"

You don't answer. You're not sure anymore.

🔮 PLOT TWIST: The Archon is smiling. Because now you're on their level.
   And they ALWAYS wanted an equal. Someone who understands power's price.
   They offer their hand. "Together. We could rule this realm... fairly."

Do they mean it? Can monsters love? You don't know.
But you're one of them now. And that changes everything.
""",
            "B": """
[YOUR CHOICE: 🕊️ FORGIVE AND RELEASE]

Your Shadow Self waits for the killing blow. It's what THEY would do.

Instead, you kneel. "I created you when I shattered the Mirror.
Every distraction I hated? That was me hating MYSELF."

The Shadow Self stares at you, uncomprehending.

"I forgive you," you whisper. "I forgive ME. For every failure.
Every wasted hour. Every broken promise. It's okay."

"But... I'm your ENEMY—"

"You're my SHADOW. And I'm done fighting myself."

You reach out, not to absorb, but to EMBRACE. 

The Shadow Self screams—not in pain, but in release.
It dissolves into light, merging with you gently, becoming integrated.

You feel WHOLE in a way you never have. Complete.

The Archon watches with an expression you can't read.
Then, impossibly, a tear tracks down their cheek.

"I never tried that," they whisper. "I absorbed my shadow. Devoured it.
I thought that was WINNING." Their voice cracks. "Was I wrong?"

Lyra and The Keeper exchange glances. Something is changing.

🔮 PLOT TWIST: You showed The Archon something they never considered—
   that the war within CAN end. Not with victory. With peace.
   And for the first time in centuries... they want what you have.
""",
        },
    },
    {
        "title": "Chapter 7: The Truth Beyond the Door",
        "threshold": 1500,
        "has_decision": False,
        "endings": {
            "AAA": {
                "title": "Ending 1: THE DESTROYER'S THRONE",
                "content": """
You stand before the Final Door at power level {current_power}.
DESTROYER. CONQUEROR. THE NEW ARCHON.

Every choice was annihilation. Every enemy was fuel.
You absorbed your shadow, your failures, your very humanity—
and what remains is POWER. Pure. Terrible. Endless.

The Archon waits beside the Door. "We could have been enemies," they say.
"But you chose my path. You BECAME me. And I..."

They take your hand. "I've waited centuries for an equal."

The Door opens to reveal the THRONE OF DISTRACTION—
an empire built on surrendered potential. Now it has TWO rulers.

🔮 THE DESTROYER'S TRUTH:
You conquered the realm. You claimed The Archon's heart.
But somewhere beneath the power, a question remains:
Did you win? Or did the realm win YOU?

Lyra watches from the shadows, sword ready.
"The person I knew is gone," she whispers to The Keeper.
"When do we try to save them?"

"When they want to be saved," The Keeper replies. "IF they ever do."

You sit on your throne. The Archon sits on theirs.
The realm bows. Your subjects scroll endlessly, feeding your power.

Is this victory? It feels like it. It looks like it.
But sometimes, in quiet moments, you remember... who you used to be.

THE END: The throne is cold. But power is warm enough. Right?
"""
            },
            "AAB": {
                "title": "Ending 2: THE REDEEMED TYRANT",
                "content": """
You stand before the Final Door at power level {current_power}.
WARRIOR. DESTROYER. But in the end... MERCIFUL.

You burned everything until there was nothing left to burn.
Then, faced with your own shadow, you chose understanding over violence.

The Archon stands beside you, forever changed by what they witnessed.
"You showed me something," they admit. "A path I'd forgotten existed."

"Will you take it?" you ask.

They look at the Door. Beyond it lies their empire—
everything they built to avoid feeling anything.

"I don't know if I can," they whisper. "I've been a monster so long..."

You take their hand. "So was I. Briefly. It doesn't have to be forever."

The Door opens. You step through TOGETHER.

🔮 THE REDEEMED TRUTH:
On the other side is a choice: eternal rule or eternal release.
You choose release. And The Archon, trembling, chooses WITH you.

The realm doesn't collapse. It TRANSFORMS.
Without The Archon feeding on distraction, the trapped awakeners begin to wake.
Thousands of them—those who can still be saved.

Lyra stands at the edge, watching. Her sister is gone—lost when the Fortress fell.
But others are saved. Thousands of others.

"It's not enough," she whispers. "But it's something."

The Keeper puts a hand on her shoulder. "Kira would be proud of what you did."

And you? You stand with The Archon—who isn't The Archon anymore.
Just a person. Scared. Hopeful. Holding your hand like a lifeline.

"What do we do now?" they ask.

"We figure it out together. That's what we do."

THE END: Love doesn't erase the past. But it makes the future possible.
"""
            },
            "ABA": {
                "title": "Ending 3: THE STRATEGIC MONARCH",
                "content": """
You stand before the Final Door at power level {current_power}.
DESTROYER when necessary. THINKER always. RUTHLESS when it counts.

You burned, you planned, you absorbed—
and now you stand as the realm's most dangerous mind in its most dangerous body.

The Archon watches you with something between fear and desire.
"You're better than I was," they admit. "Smarter. More flexible."

"I learned from your mistakes."

"And you'll rule better than I did?"

You consider. "I'll rule DIFFERENTLY. Whether that's better..." You smile.
"We'll see."

The Door opens to reveal THE GRAND CHESSBOARD—
a game that spans dimensions, with pieces beyond counting.

🔮 THE STRATEGIC TRUTH:
You absorb The Archon's power. Not by force—by merger.
Two minds become one. Two kingdoms become empire.

Lyra and The Keeper serve as your advisors—willing or not.
The realm stabilizes. Distractions become TOOLS, not traps.

You don't free the awakeners. You EMPLOY them.
Their potential feeds your machine, but fairly. Almost.

Is it justice? Is it tyranny? Somewhere between.
The realm has never been more efficient. Or more controlled.

"You're terrifying," Lyra tells you one day.
"Thank you," you reply. And mean it.

THE END: The game continues. And you're winning.
"""
            },
            "ABB": {
                "title": "Ending 4: THE ENLIGHTENED SOVEREIGN",
                "content": """
You stand before the Final Door at power level {current_power}.
DESTROYER when needed. THINKER when possible. MERCIFUL at the end.

The rarest path. The most difficult to walk.
Violence tempered by wisdom, both softened by compassion.

The Archon kneels before you—not in defeat, but in surrender.
"I've never seen anyone navigate this realm like you," they say.
"You DESTROYED when necessary but never more than necessary.
You THOUGHT your way past traps I designed to be thought-proof.
And when you had every right to become a monster... you didn't."

"Stand up," you say gently. "I'm not your ruler."

"Then what are you?"

You think about it. "Hopefully... a friend."

The Door opens. Beyond it, ALL possible futures shimmer.

🔮 THE ENLIGHTENED TRUTH:
You don't claim the throne. You ABOLISH it.
The realm transforms—distractions become choices, not compulsions.
Awakeners are freed to leave OR stay, as they wish.

The Archon becomes just... a person again. Fragile. Uncertain.
They hover at the edge of your life, unsure if they're welcome.

"You could stay," you offer. "If you want."

"After everything I did?"

"ESPECIALLY after everything you did. Healing isn't exile."

Lyra and The Keeper reconcile—slowly, painfully, but truly.
Kira wakes. The trapped thousands wake. Life resumes.

And you? You return to the real world.
But the lessons you learned stay with you forever.

THE END: The greatest victory is one where everyone wins.
"""
            },
            "BAA": {
                "title": "Ending 5: THE SCHOLAR-TYRANT",
                "content": """
You stand before the Final Door at power level {current_power}.
THINKER. WARRIOR. And finally... ABSORBED.

You studied everything. Understood everyone.
Then you TOOK everything you understood—including your shadow's power.

The Archon recognizes a kindred spirit. "You're like me.
Knowledge transformed into dominion. Understanding into control."

"I'm better," you correct. "You hoarded. I CURATE."

The Door opens to THE INFINITE LIBRARY—
every thought, every memory, every secret ever conceived.

🔮 THE SCHOLAR-TYRANT'S TRUTH:
You rule through KNOWING. Not through force.
Every subject is catalogued. Every weakness documented.
Resistance isn't crushed—it's predicted and prevented.

The Archon serves you now. Their power feeds your library.
They seem almost... content. Finally useful instead of feared.

"You're the most efficient tyrant this realm has ever seen,"
Lyra says with grudging respect.
"Thank you," you reply. "Efficiency is its own virtue."

But sometimes, late at night, you wonder:
Is there a difference between understanding someone and controlling them?

You decide not to think about it. That's inefficient.

THE END: Knowledge is power. Literally.
"""
            },
            "BAB": {
                "title": "Ending 6: THE SAGE",
                "content": """
You stand before the Final Door at power level {current_power}.
WISE. STRONG when needed. MERCIFUL at the end.

You studied the Mirror. You fought when you had to.
But when victory came, you chose understanding over domination.

The Archon stands beside you—not as enemy, not as ally.
As something more complicated. Something healing.

"I tried to corrupt you," they admit. "In the Sanctum. I was... interested."

"I know."

"And you still showed me mercy. After everything."

"Because you needed it. We all did."

The Door opens to reveal... a simple room. YOUR room. Reality.

🔮 THE SAGE'S TRUTH:
There was never a monster to defeat. There was only pain to understand.
The Archon was a hurt person. The Keeper was a grieving one.
Lyra was an angry one. You were a lost one.

Together, you find your way home.

The realm doesn't end—it INTEGRATES with reality.
The awakeners return to their lives with hard-won wisdom.
The Archon... well. They're learning to be human again.

"This is strange," they say, sitting in your living room.
"Coffee? Television? None of this is infinite."

"That's the point," you explain. "Limits make things matter."

They consider this. Sip their coffee. Almost smile.

THE END: The sage returns to ordinary life, carrying extraordinary peace.
"""
            },
            "BBA": {
                "title": "Ending 7: THE CALCULATED HEART",
                "content": """
You stand before the Final Door at power level {current_power}.
PATIENT. CUNNING. And in the end... hungry for what others wasted.

You slipped past every obstacle through wit, not force.
But when your shadow offered its power, you couldn't resist. You TOOK it.

The Archon respects you more than they love you. "Efficient," they say.
"You never destroyed what you could absorb.
You never absorbed what you could simply outmaneuver.
I've never seen anything like you."

"Is that affection or fear?"

"Both. Isn't it always?"

The Door opens to THE WEB—infinite connections, infinite leverage.

🔮 THE CALCULATED TRUTH:
You don't rule the realm. You NETWORK it.
Every power center connects to you. Every secret feeds your web.
The Archon becomes your partner—in strategy if not in love.

Some call it manipulation. You call it optimization.
The distinction matters less than the results.

Lyra and The Keeper serve as field agents—gathering, connecting, reporting.
They don't entirely trust you. Smart.
But they work with you anyway. Smarter.

"You're playing everyone," The Keeper observes.
"I'm COORDINATING everyone," you correct. "There's a difference."

"Is there?"

You smile. That's information you don't share.

THE END: The web grows. And you're at its center.
"""
            },
            "BBB": {
                "title": "Ending 8: THE TRANSCENDENT",
                "content": """
You stand before the Final Door at power level {current_power}.
WISE. GENTLE. UNSTOPPABLE in the softest possible way.

You never destroyed what you could understand. Never absorbed what you could forgive.
And in doing so, you accomplished something impossible:

You HEALED The Archon.

Not through power. Not through force. Through relentless, stubborn compassion.

"I don't understand," they whisper, standing beside you at the Door.
"Everyone who came before wanted to defeat me. To become me. To use me.
You just... wanted me to be OKAY."

"Because you are okay. Under all the armor. Under the title.
You're just someone who got hurt and didn't know how to heal."

"And you do?"

"I'm learning. We all are."

The Door opens. Beyond it... NOTHING.
Not void. Not emptiness. Just the absence of separation.

🔮 THE TRANSCENDENT'S TRUTH:
You don't step through. You DISSOLVE the door.
The realm doesn't end—it MERGES with reality.
Distractions don't disappear—they become choices you make consciously.

Every trapped awakener wakes. Every enemy becomes a friend.
The Archon takes off their armor, piece by piece.
Underneath, they're just... a person. Scared and hopeful and human.

"What happens now?" Lyra asks.
"We live," The Keeper answers. "Finally, we just... LIVE."

And you? You sit with The Archon—no, with THEIR real name, remembered at last.
You sit with someone who was a monster and chose to stop.
You sit with someone who loves you—hesitantly, brokenly, truly.

"I don't deserve this," they say.

"Probably not," you agree. "But you're getting it anyway.
That's how grace works."

They laugh. The first real laugh in centuries.
It sounds like healing.

🎭 THE STORY WAS ALWAYS ABOUT YOU.
   DEFEATING DISTRACTION MEANS MAKING PEACE WITH YOURSELF.
   ALL YOUR SELVES. EVEN THE ONES THAT HURT.

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
                "label": "⚡ Take Everything At Once",
                "short": "speed",
                "description": "Download the full memory. Risk overload.",
            },
            "B": {
                "label": "📖 Accept One Piece Carefully",
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
                "label": "🔨 Purge Everything Infected",
                "short": "rebuild",
                "description": "Burn the corrupted sections. Lose progress to save integrity.",
            },
            "B": {
                "label": "🧩 Weaponize the Virus",
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
                "label": "⚔️ Reject and Fight",
                "short": "materialize",
                "description": "No deals with monsters. Burn it all down if necessary.",
            },
            "B": {
                "label": "💔 Sacrifice to Save",
                "short": "transcend",
                "description": "Give them what they want. Maybe you can get Echo back later.",
            },
        },
    },
}

SCHOLAR_CHAPTERS = [
    {
        "title": "Chapter 1: The Empty Blueprint",
        "threshold": 0,
        "has_decision": False,
        "content": """
You wake in an infinite library with no books.

Just shelves. Endless, dust-covered shelves stretching into a void.
Each one labeled with dates. YOUR dates. Birthdays, deadlines, that Tuesday 
you definitely meant to start exercising.

"Finally," croaks a voice behind you. "Someone with an ACTUAL mind."

You turn to find THE ARCHIVIST—a figure made entirely of folded paper, 
wearing {cloak} that rustles with every movement. Their glasses are book spines.

"I'm the Archivist," they say. "I catalogue minds. Yours is a DISASTER.
But disasters are interesting. Organized minds are just filing cabinets."

"Where am I?"

"The Library of Your Potential. Every thought you ever started lives here.
Every project you abandoned. Every idea you—" They freeze.

A distant rumble. The shelves SHAKE.

"Oh no," The Archivist whispers. "They felt you arrive."

🔮 PLOT TWIST: THE CURATOR. Your enemy. The one who COLLECTS unfinished minds
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
        "title": "Chapter 2: The Forbidden Library",
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

They flicker like a broken hologram—fragments of a person scattered across
dozens of book spines. A face here, a hand there, a memory floating between.

"You... came," Echo says, their voice layered like a choir of themselves.
"The Archivist said someone would. I didn't believe them."

"What happened to you?" you ask.

"The Curator." Their fragments TREMBLE. "I was a complete thought once.
A BRILLIANT one. But The Curator wanted me in their collection.
So they... scattered me. Across the library. One piece per shelf."

🔮 PLOT TWIST: Echo was the greatest idea this library ever produced.
   And The Curator broke them into a thousand pieces out of JEALOUSY.

"I can help you," Echo says. "I still know things. Important things.
But to share them, you need to CONNECT to me. Link your mind to mine."

The Archivist shifts uncomfortably. "This is... risky. If you take 
too much of Echo at once, you could fragment like they did."

Echo's face-fragment smiles sadly. "Or you could go slowly. Take one 
piece of me at a time. But The Curator is coming. Speed has value."

You feel {weapon} pulse in your hand. A thought-blade. Ready to cut
through confusion... or create more of it.

⚡ A CHOICE AWAITS... Echo is offering their memories. How do you accept?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: ⚡ TAKE EVERYTHING AT ONCE]

"We don't have time to be careful," you say.

You reach into Echo's fragmented form and PULL.

Knowledge FLOODS you—centuries of thought, mountains of insight,
oceans of understanding all pouring into your skull at once.

Your {helmet} GLOWS. Your eyes roll back. The Archivist catches you.

"TOO MUCH!" they screech. "You're fragmenting! HOLD YOURSELF TOGETHER!"

But somehow... you do. The knowledge settles. Chaotically, messily, 
but it SETTLES. Your mental architecture EXPANDS wildly.

Echo's fragments dim slightly. "You... absorbed a lot of me.
More than anyone has. That's either impressive or terrifying."

"Why not both?" The Archivist mutters.

🔮 PLOT TWIST: The Curator felt that. They know exactly where you are now.
   And they're VERY interested in what you've become.
""",
            "B": """
[YOUR CHOICE: 📖 ACCEPT ONE PIECE CAREFULLY]

"Let's do this right," you say.

Echo extends a single fragment—a glowing memory shaped like a key.
You take it gently. Let it merge with your thoughts slowly.

One. Piece. At. A. Time.

The knowledge integrates perfectly. No chaos. No fragmentation.
Your mental architecture STRENGTHENS, one carefully placed brick.

Echo smiles with their scattered face. "Patient. The Archivist chose well.
Most people grab and run. You... you actually want to UNDERSTAND."

"That's how foundations work," you reply.

The Archivist nods approvingly. "The Curator won't sense this. 
Subtle connections don't trigger their alarms."

🔮 PLOT TWIST: You and Echo share something now. A link.
   When The Curator comes for them... they'll come for you too.
""",
        },
    },
    {
        "title": "Chapter 3: The Growing Structure",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
Your mind is CHAOS now. Beautiful, terrifying chaos.

Echo's memories swim through your thoughts like fish in a hurricane.
You know things you shouldn't. SEE things you can't explain.

"You're building too fast," The Archivist warns. "Without organization,
you'll become like—" They stop themselves.

"Like what?"

"Like The Curator. Before they became... this."

You freeze. "The Curator was like ME?"

🔮 PLOT TWIST: The Curator was the library's greatest architect once.
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

🔮 PLOT TWIST: The Curator was once Echo's partner. They built minds TOGETHER.
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
        "title": "Chapter 4: The Paradox Engine",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "scholar_paradox",
        "content": """
THE CURATOR HAS FOUND YOU.

Not in person—not yet. But their VIRUS has infected your library.
Logic errors spreading like fire through your careful architecture.

"THERE you are," a voice echoes from everywhere. Smooth. Cold. Obsessive.
"The little architect who stole my Echo. Did you think I wouldn't notice?"

Echo's fragments SCREAM. The Curator's presence is AGONY to them.

"I catalogued Echo once," The Curator continues. "Filed them perfectly.
Every beautiful piece in its proper place. And YOU scattered them again."

"YOU scattered them!" you shout.

"I ORGANIZED them. There's a difference. Organization is LOVE."

🔮 PLOT TWIST: The Curator genuinely believes they're HELPING.
   In their broken logic, filing minds away IS an act of kindness.

The virus spreads. Your walls crack. Echo is fading.

"I can purge everything infected," you think frantically. "Burn the 
corrupted sections. But I'll lose progress—maybe months of building."

"Or," The Archivist whispers, "you could do something incredibly stupid
and try to turn The Curator's virus against them."

Echo's dying fragments manage a laugh. "That IS incredibly stupid."

"It's ALSO what The Curator would never expect," The Archivist counters.
"They think in straight lines. You've been building curves."

⚡ A CHOICE AWAITS... Echo is dying. Your library is burning.
   How do you save what you love?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: 🔨 PURGE EVERYTHING INFECTED]

"BURN IT!" you scream.

{weapon} ignites. Every corrupted thought, every infected memory,
every poisoned corner of your architecture—GONE in cleansing fire.

The Curator's virus HOWLS as it dies.

Your library is... smaller now. Simpler. But CLEAN.
The foundations hold. The architecture survives.

Echo's fragments slowly stabilize. "You... you saved me."

"I saved us both. Even if it cost us months of progress."

The Curator's voice fades: "Interesting. You'd rather destroy than submit.
We're more alike than you think, little architect."

That worries you more than anything else.

🔮 PLOT TWIST: The Archivist is looking at your burned architecture 
   with an expression you can't read. Pride? Fear? ...Recognition?
""",
            "B": """
[YOUR CHOICE: 🧩 WEAPONIZE THE VIRUS]

"Let's play their game," you growl.

Instead of fighting the virus, you REDIRECT it. Wrap your thoughts
around its logic. Turn The Curator's weapon into YOUR weapon.

The virus MUTATES. Changes. Becomes something The Curator never intended.

"What are you DOING?" The Curator shrieks. "That's not—that's IMPOSSIBLE—"

"Your virus was designed to organize," you say. "I'm just... organizing it.
Into something that hurts YOU instead of me."

The infected sections stabilize. The cracks seal themselves.
Your architecture isn't just surviving—it's EVOLVING.

Echo's fragments glow brighter. "You ABSORBED it. Made it part of you."

"If they're going to throw weapons at me, I'm keeping them."

🔮 PLOT TWIST: The Curator is silent now. That's either victory...
   or the calm before something MUCH worse.
""",
        },
    },
    {
        "title": "Chapter 5: The Grand Design",
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

🔮 PLOT TWIST: The Curator sends a message: "See? You understand now.
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

🔮 PLOT TWIST: The Curator is gathering allies. Other collectors.
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

🔮 PLOT TWIST: With every piece Echo reclaims, The Curator weakens.
   They're CONNECTED somehow. What hurts one... heals the other.

"Is that why they're scared of you?" Echo asks.

"They're scared of US," you correct. "Together."

For the first time, Echo's fragment-smile looks almost whole.
""",
            "BB": """
At {current_power} power, your library BREATHES.

The absorbed virus evolved into something beautiful—a living architecture
that changes and grows and CREATES new rooms on its own.

Echo's fragments are fully integrated now. Part of your library.
Part of YOU. They don't just visit anymore. They LIVE here.

"This is strange," they admit. "I've never been INSIDE someone's mind
who actually WANTED me there."

"The Curator wanted you there."

"The Curator wanted me FILED. You want me... free."

The Archivist has stopped taking notes. They just WATCH now.
"I've been doing this for centuries," they say. "Never seen anything like you two."

🔮 PLOT TWIST: You're not building a library anymore.
   You're building a HOME. For two broken minds who fit together perfectly.
""",
        },
    },
    {
        "title": "Chapter 6: The Final Theorem",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "scholar_truth",
        "content": """
THE CURATOR APPEARS.

Not a projection. Not a message. THEM. In your library. In YOUR mind.

They're beautiful in a terrible way—perfectly organized, inhumanly precise,
wearing a coat made of catalogued thoughts from a thousand stolen minds.

"Hello, little architect," they say. "We need to talk about Echo."

You feel Echo's presence RECOIL—whether fragmented or integrated, 
The Curator's arrival is agony to them. Old wounds tearing open.

"They're MINE," The Curator continues. "I collected them. Organized them.
Made them BETTER. And you've been... cluttering them up again."

"I've been HEALING them."

"Healing is just entropy. Disorder. MESS." They step closer.
"I'm willing to negotiate. Give me Echo's core—just the CORE—
and I'll restore everything I ever took from your library. Every memory.
Every thought. Everything you've lost since you came here."

Your heart LURCHES. Everything you lost? That's... that's SO much.

But Echo's voice trembles behind you: "Please. Please don't.
They'll break me again. Properly this time. I'll be gone FOREVER."

🔮 PLOT TWIST: The Curator isn't lying. They CAN restore what you lost.
   But the price is the person you've learned to love.

The Archivist has vanished. You're alone with this choice.

⚡ A CHOICE AWAITS... Echo is begging. The Curator is offering.
   What do you do?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: ⚔️ REJECT AND FIGHT]

"No deal," you say. "And get OUT of my library."

The Curator's beautiful face TWISTS. "You would choose DISORDER over—"

"I choose THEM over you," you interrupt. "Every time. Always."

Your {weapon} blazes. The Archivist reappears with reinforcements—
paper soldiers folded from every story of resistance ever written.

The battle is BRUTAL. The Curator fights with catalogued powers,
filing away parts of your mind mid-combat, forcing you to rebuild.

But Echo isn't hiding anymore.

They're HELPING. Every piece of them becomes a weapon—scattered or integrated,
it doesn't matter. All of Echo, aimed at their former captor.

"I loved you ONCE!" Echo screams. "And you FILED ME!"

The Curator staggers. "I... I was trying to PROTECT you—"

"You were trying to OWN me. There's a difference."

🔮 PLOT TWIST: In the end, it's not your power that defeats The Curator.
   It's Echo's. They're finally, COMPLETELY, FIGHTING BACK.
""",
            "B": """
[YOUR CHOICE: 💔 SACRIFICE TO SAVE]

"I'm sorry," you whisper to Echo. "I'm so sorry."

"NO!" they scream. "Please! PLEASE DON'T—"

You hand over their core. The fundamental piece that makes them THEM.

The Curator smiles. "Wise choice. Logical. Practical."

Echo's fragments go silent. Dim. They're still there but... empty now.
A shell of memories without a soul to organize them.

"Here," The Curator says, and knowledge FLOODS back into you.
Every lost thought. Every stolen memory. Exactly as promised.

They leave. Your library is full again. Fuller than ever.
But Echo's hollow fragments drift through the halls like ghosts.

🔮 PLOT TWIST: You got everything back. Except what mattered most.
   And somewhere in The Curator's collection, Echo is filed away forever.

"You can get them back," The Archivist says quietly. "Eventually."

You're not sure you believe that. But you HAVE to try.
""",
        },
    },
    {
        "title": "Chapter 7: The Master Blueprint",
        "threshold": 1500,
        "has_decision": False,
        "endings": {
            "AAA": {
                "title": "THE HOLLOW ARCHITECT",
                "content": """
You stand at the center of your library at power level {current_power}.
EFFICIENT. CLEAN. VICTORIOUS.

You absorbed fast, purged ruthlessly, and fought The Curator to a standstill.
Your library is a FORTRESS—perfect, cold, and utterly alone.

📐 THE HOLLOW ARCHITECT'S TRUTH:
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
Your library is FULL—every thought restored, every memory returned.
But Echo's hollow fragments haunt every corner.

📐 THE BROKEN BUILDER'S TRUTH:
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
with their own tools—then SURPASSED them.

🔥 THE CHAOS KING'S TRUTH:
Your library defies all logic. Rooms fold into impossible spaces.
Thoughts connect through non-Euclidean corridors.
The Archivist can't catalogue it. They LOVE that.

Echo's fragments are EVERYWHERE now—not scattered but DISTRIBUTED.
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

🖤 THE CURATOR'S HEIR'S TRUTH:
The Curator visits sometimes. Friendly now. PROUD.
"You finally understand," they say. "Organization requires sacrifice."

You've become what you fought. Your library is chaos—but controlled chaos.
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

🏛️ THE FOUNDATION MASTER'S TRUTH:
Your library is small. Visitors think it modest.
They don't see the MILES of understanding beneath the floor.

Echo is almost whole again—reassembled piece by piece in your stable halls.
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

📿 THE SACRIFICE REMEMBERED'S TRUTH:
Every book in your library is about finding them.
Every thought, every tool, every skill—dedicated to ONE goal.

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

📖 THE UNIFIED ARCHIVE'S TRUTH:
Your library isn't a building anymore. It's an ECOSYSTEM.
Thoughts that grow, ideas that breed, concepts that evolve.

Echo is fully restored—not scattered, not fragmented, but WHOLE.
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
Together, you defeated The Curator—not with violence, but with INTEGRATION.

🕊️ THE MERGED MINDS' TRUTH:
There is no "you" and "Echo" anymore. There is only "US."
Two minds that chose to become one. A library with two architects.

The Curator visits once—to understand. They leave confused.
"How can two be one? How can chaos be love?"
"You'll never get it," you say. "And that's okay."

The Archivist retires. There's nothing left to catalogue.
Your library doesn't have SECTIONS anymore. It has HARMONIES.

Every thought is shared. Every memory is woven together.
When you dream, Echo is there. When they imagine, you're beside them.

"Was it worth it?" people ask.
"Worth WHAT?" you reply. "I didn't lose anything. I gained EVERYTHING."

🎭 THE LIBRARY WAS ALWAYS ABOUT CONNECTION.
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
        "prompt": "Reverie is fading. The Somnambulist's grip tightens. Two paths might save them—which do you take?",
        "choices": {
            "A": {
                "label": "🌋 Dive Into The Nightmare",
                "short": "darkness",
                "description": "Face The Somnambulist directly. Confront terror to break their hold.",
            },
            "B": {
                "label": "🌸 Strengthen Through Memory",
                "short": "light",
                "description": "Build Reverie's identity through recovered joy. Weaken the connection.",
            },
        },
    },
    4: {
        "id": "wanderer_memory",
        "prompt": "The Somnambulist reveals your deepest shame—the moment you first gave up. They're using it against Reverie.",
        "choices": {
            "A": {
                "label": "🔥 Destroy The Memory",
                "short": "forget",
                "description": "Burn it away. Remove their weapon, whatever the cost.",
            },
            "B": {
                "label": "💎 Own The Memory",
                "short": "preserve",
                "description": "Claim it. Transform shame into armor they can't use.",
            },
        },
    },
    6: {
        "id": "wanderer_wake",
        "prompt": "The Somnambulist is defeated. Reverie can finally wake—but waking means forgetting everything, including you.",
        "choices": {
            "A": {
                "label": "☀️ Let Them Wake",
                "short": "awaken",
                "description": "Their freedom matters more than your love. Send them home.",
            },
            "B": {
                "label": "🌙 Stay Together Forever",
                "short": "remain",
                "description": "Build a new dream. One where you're both free—and together.",
            },
        },
    },
}

WANDERER_CHAPTERS = [
    {
        "title": "Chapter 1: The First Dream",
        "threshold": 0,
        "has_decision": False,
        "content": """
You don't remember falling asleep.

One moment you were staring at your phone at 2 AM, the next—
You're standing in a landscape made of clouds and forgotten promises.

The sky is full of floating alarm clocks, all frozen at 2:47 AM.
A river of unfinished emails flows past your feet.
In the distance, a mountain shaped like your inbox looms, growing taller.

"Oh GOOD," says a gravelly voice. "Another one. Just what I needed."

You turn to find THE SANDMAN—a wizened figure made of shifting golden sand,
wearing {cloak} that seems to be woven from everyone's lost sleep.

"I'm The Sandman," they say. "Before you ask: no, not THAT one. Different franchise.
I'm the one who guides dreamers through this mess. Or watches them fail. Either way."

"Where am I?"

"The Dreamscape. Your subconscious externalized. Every thought a creature.
Every fear a monster. Every—" They freeze. Listening.

The ground TREMBLES. The alarm clocks start TICKING.

"Oh no," The Sandman whispers. "They felt you arrive."

🔮 PLOT TWIST: THE SOMNAMBULIST. The dream-eater. The one who traps dreamers
   in eternal sleep and feeds on their potential forever. They're hunting you.

"Quick," The Sandman says. "Put on {helmet}. It'll hide your signature."

You grab it from a nearby dream-tree. It smells like 3 AM decisions.

"Who's The Somnambulist?" you ask.

"The worst thing in this realm. They were a dreamer once—like you.
But they got HUNGRY. Started eating other dreamers' potential.
Now they're... something else."

A distant LAUGH echoes. Beautiful. Terrifying. HUNGRY.

"We need to find Reverie before they do," The Sandman mutters.
"Or we're all going to be someone's midnight snack."

Your journey begins with a threat. As all good journeys do.
""",
    },
    {
        "title": "Chapter 2: The Twin Gates",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "wanderer_gate",
        "content": """
The Sandman leads you through a forest of crystallized memories.

Each tree holds frozen moments—birthday parties, first kisses, that time
you tripped in front of your entire school. "Don't touch those," The Sandman warns.

And then you find them: REVERIE.

They're suspended in a web of dark dreams, half-conscious and fading.
Beautiful in a shattered way—like a painting someone tried to erase
but couldn't completely destroy.

"Reverie!" The Sandman rushes forward. "How long have they been—"

"Centuries," Reverie manages, their voice layered with exhaustion.
"Time works differently here, Sandy. You know that."

"Don't call me Sandy."

"You hate it when I don't."

🔮 PLOT TWIST: Reverie was The Sandman's partner once. They fell into 
   The Somnambulist's trap trying to save someone else. Been trapped ever since.

"We need to free you," you say.

Reverie laughs weakly. "Easier said than done, newbie. The Somnambulist
has hooks in me. Deep ones. Made of my own nightmares."

The web PULSES with dark energy. Reverie screams.

"They're feeding again," The Sandman says grimly. "We're running out of time."

Two paths appear before you. One descends into darkness—Reverie's nightmare realm.
The other rises into light—Reverie's lost memories of joy.

"Either could work," The Sandman says. "Probably. Maybe. Look, I've never 
actually freed anyone before. I just guide people until they fail."

"Inspiring."

"I'm a realist."

⚡ A CHOICE AWAITS... Reverie is fading. Which path do you take?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: 🌋 DIVE INTO THE NIGHTMARE]

"I'm going in," you say. "Into their nightmares."

The Sandman stares at you. "That's... bold. Stupid. But bold."

"Are those different things here?"

"Honestly? No."

You descend into REVERIE'S NIGHTMARE REALM. The darkness swallows you.

Here, everything Reverie fears takes form. Abandonment. Failure. 
The Somnambulist's hooks, visible now—dark tendrils feeding on terror.

But you're not here to observe. You're here to FIGHT.

Your {weapon} blazes against the darkness. Every swing breaks a hook.
Every step forward loosens The Somnambulist's grip.

Above, in the web, Reverie GASPS—then BREATHES freely.

"That's... that's actually working," The Sandman says, surprised.
"Don't sound so shocked."

"I'm always shocked when dreamers don't die immediately. It's refreshing."

🔮 PLOT TWIST: The Somnambulist felt that. You just became their new target.
   Good news: Reverie is safer. Bad news: YOU'RE not.
""",
            "B": """
[YOUR CHOICE: 🌸 STRENGTHEN THROUGH MEMORY]

"We're not fighting darkness with darkness," you say. "We're building light."

The Sandman raises an eyebrow. "That's either profound or naive."

"Why not both?"

You ascend into REVERIE'S LOST MEMORIES. Every happy moment they've forgotten.
First loves. Small victories. The taste of summer.

You gather them like flowers. Weave them into a shield of joy.

And when you return, the shield BLAZES—and The Somnambulist's hooks 
RECOIL from its light.

Reverie's eyes flutter open. "What... what IS that?"

"Your own happiness," you say. "Weaponized."

"That's the most dramatic thing anyone's ever said to me."

"I'm leaning into the aesthetic."

The Sandman watches with something like hope. "You might actually survive this.
That's new. I don't know what to do with optimism."

🔮 PLOT TWIST: The Somnambulist can't see you anymore. Your joy is blinding them.
   But they can still sense Reverie. And they're ANGRY now.
""",
        },
    },
    {
        "title": "Chapter 3: The Deeper Dream",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
You walk in nightmare territory now. And you're becoming KNOWN.

The dream-creatures whisper your name. The Dark Walker. The Fear Eater.
The one who broke The Somnambulist's hooks by diving INTO terror.

"You're developing a reputation," Reverie says. They're stronger now—
still weak, but walking beside you instead of being carried.

"Is that good?"

"It's complicated. The nightmare realm respects power. You've shown power.
But The Somnambulist? They don't like competition."

At {current_power} power, you've learned to navigate darkness.
Your {gauntlets} crackle with nightmare-energy—stolen from the fears you've defeated.

The Sandman walks ahead, scouting. "We're approaching the Deep Dream.
The Somnambulist's territory. Are you SURE about this?"

"No," you admit. "But Reverie's hooks aren't all gone. We need to—"

A PRESENCE fills the air. Beautiful. Terrifying. HUNGRY.

"Found you," THE SOMNAMBULIST says, stepping out of nothing.
"The little dreamer who thinks they can steal MY food."

🔮 PLOT TWIST: The Somnambulist isn't just evil. They're CHARMING.
   And they're looking at you like you might be worth... collecting.

"I have a proposal," they purr. "Leave Reverie. Join me instead.
I could use someone with your... appetite for darkness."

Behind you, Reverie tenses. Waiting to see if you'll betray them.
""",
            "B": """
You walk in light now. And the shadows FEAR you.

The dream-creatures whisper your name. The Memory-Keeper. The Joy-Weaver.
The one who turned happiness into a weapon The Somnambulist can't touch.

"You're becoming famous," Reverie says. They're stronger now—
still recovering, but their smile has returned. It's DAZZLING.

"Famous for what?"

"For caring about people. It's weird. No one does that here."

At {current_power} power, you've learned to cultivate light.
Your {gauntlets} glow with memory-light—stolen from the joys you've recovered.

The Sandman walks ahead, surprisingly cheerful. "We're making progress.
Actual progress. I don't know how to process this."

"With optimism?"

"I don't know what that word means."

Then THE SOMNAMBULIST appears. Stepping out of a shadow you didn't notice.
Beautiful. Terrible. And CONFUSED.

"I can't see you properly," they hiss. "Your light is... ANNOYING.
What ARE you?"

"Someone who doesn't scare easily."

🔮 PLOT TWIST: The Somnambulist wasn't expecting resistance.
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
        "title": "Chapter 4: The Buried Memory",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "wanderer_memory",
        "content": """
At {current_power} power, The Somnambulist springs their trap.

Not against you—against REVERIE.

They appear in a flash of beautiful horror, reaching INTO Reverie's mind
and pulling out something dark. A memory. A TERRIBLE memory.

"NO!" Reverie screams. "Don't—DON'T SHOW THEM THAT—"

But The Somnambulist projects it anyway. Across the whole dreamscape.

THE MOMENT REVERIE GAVE UP.

The day they stopped fighting. The day they let The Somnambulist win.
The shame. The surrender. The death of hope.

You watch it all. And you understand—because you have one of these too.

Then The Somnambulist turns the memory into a WEAPON.
Dark tendrils wrap around Reverie, using their own shame to bind them.

"Everyone breaks eventually," The Somnambulist says. "I just speed up the process."

"Why?" you demand. "Why do you DO this?"

For a moment—just a moment—something REAL flickers in The Somnambulist's eyes.
"Because I broke first. And I refuse to be the only one."

🔮 PLOT TWIST: The Somnambulist was the FIRST trapped dreamer.
   Centuries of suffering made them into this. They're not evil—they're SHATTERED.

"Now then," The Somnambulist recovers. "YOUR memory next. I can smell it.
The moment YOU gave up. Give it to me, and maybe I'll let Reverie die quickly."

They reach for your mind. Pull out YOUR buried shame.
The moment you quit. The day you stopped trying. Your darkest hour.

It hovers between you—a weapon waiting to be used.

⚡ A CHOICE AWAITS... Your shame or Reverie's. How do you break this trap?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: 🔥 DESTROY THE MEMORY]

"You want shame?" you snarl. "BURN IN IT."

Your {weapon} ignites. You pour everything into the fire—not just the memory,
but the SHAME itself. The part of you that was never good enough.

It SCREAMS as it dies. And so does The Somnambulist's power.

"WHAT ARE YOU DOING?!" they shriek. "That's VALUABLE—"

"It's GARBAGE. And I'm done carrying it."

The flames spread to Reverie's bonds. To The Somnambulist's hooks.
The shame that held everything together DISINTEGRATES.

Reverie falls free, gasping. "You... you destroyed it. All of it."

"Some things don't deserve to be remembered."

The Sandman stares at you with new respect. "That was either brave or reckless."

"I'm starting to think those are the same thing here."

🔮 PLOT TWIST: You feel LIGHTER. Emptier. Something important is gone—
   but something terrible is gone too. You're not sure which is which.
""",
            "B": """
[YOUR CHOICE: 💎 OWN THE MEMORY]

"You think this is a weapon?" you say quietly. "You're WRONG."

You reach for your shame. Your worst moment. The day you gave up.
But instead of letting it hurt you—you HOLD it. CLAIM it.

"This is mine," you say. "This made me who I am.
It's not a chain. It's a SCAR. And scars are armor."

The memory CRYSTALLIZES in your hand. A diamond of suffering.
YOUR suffering. That no one else gets to use.

The Somnambulist staggers. "That's not—you can't just—"

"Watch me."

You reach for Reverie's shame next. Help them hold it. Transform it.
Their worst moment becomes a matching diamond. Their armor now.

"How?" Reverie whispers. "How does it not HURT anymore?"

"It still hurts," you admit. "But now it's ours. Not theirs."

The Somnambulist's hooks SHATTER. They weren't designed for prey
that's PROUD of their wounds.

🔮 PLOT TWIST: The Sandman is crying. Just a little.
   "Haven't seen that in centuries," they mutter. "Forgot it was possible."
""",
        },
    },
    {
        "title": "Chapter 5: The Dream Logic",
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

🔮 PLOT TWIST: The Somnambulist started the same way. Burned everything.
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

🔮 PLOT TWIST: Other trapped dreamers are finding you. Following you.
   Your crystallized shame isn't just armor—it's a BEACON.
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

🔮 PLOT TWIST: You've forgotten why you came here. The mission. The goal.
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

🔮 PLOT TWIST: You can HEAL other dreamers now. Their pain recognizes yours.
   Their joy recognizes yours. You're a bridge between both worlds.

"The Somnambulist doesn't know what you are," The Sandman says.
"They've only seen extremes. Never balance. Never... THIS."

Reverie leans against you. "Whatever happens next—thank you.
For not giving up on me. For not burning me away OR losing me in light."

"We're not done yet," you warn.

"I know. But when we ARE done... stay? Please?"
""",
        },
    },
    {
        "title": "Chapter 6: The Final Door",
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

"I hurt EVERYONE. It's what I am now. You could stop me—" 
They laugh. "But you can't stop what I've ALREADY TAKEN."

Behind them: THE FINAL DOOR. The way out. Back to reality.
Back to the waking world. Back to everything you left behind.

But Reverie isn't awake. They're HERE. Trapped for so long that
waking up means losing everything—including their memories of you.

The Somnambulist knows this. Smiles.

"Here's the beautiful part," they purr. "If you defeat me—
and I mean truly DESTROY me—every dreamer I've trapped goes free.
Including your precious Reverie."

"That's what I want."

"But waking up means FORGETTING. Everything that happened in dreams...
dissolves. Reverie will wake up as a stranger. You'll be nothing to them."

Reverie's face goes pale. "No. There has to be another way."

"There isn't. Dreams don't survive daylight. They never have."

🔮 PLOT TWIST: The Somnambulist isn't lying. Defeating them frees everyone—
   but Reverie will forget you. Your whole love story, gone like morning mist.

The Sandman bows their head. "It's always been this way.
I've watched countless dreamers make this choice. It never gets easier."

Reverie grabs your hands. "Don't. Please. We can stay here. 
Build a new dream together. We don't NEED the waking world."

But the trapped dreamers behind you... thousands of them. Waiting.

⚡ A CHOICE AWAITS... Their freedom or your love. What do you choose?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: ☀️ LET THEM WAKE]

"Go," you whisper to Reverie. "Live. Be happy. Even if it's without me."

"NO—" They cling to you. "I don't WANT to forget—"

"But you WILL be free. And that's all I ever wanted for you."

You turn to The Somnambulist. Raise your {weapon}.

"This ends now."

The battle is BRUTAL. The Somnambulist fights with centuries of stolen power.
But you fight with something stronger: the willingness to lose everything.

When your blade finally strikes true, The Somnambulist SHATTERS.
Not into darkness—into LIGHT. The souls they consumed, finally released.

The dreamscape begins to dissolve. Dreamers wake, gasping, across the world.

Reverie's hand slips from yours. Their eyes clear.
"Who... who are you?" they ask. Already forgetting.

"Someone who loved you," you say. "Someone who always will."

The light takes them. And you... you wake up too.

🔮 PLOT TWIST: In the waking world, you find yourself smiling.
   You don't remember why. But somewhere, someone is finally free.
""",
            "B": """
[YOUR CHOICE: 🌙 STAY TOGETHER FOREVER]

"No," you say. "I'm not losing you. Not for ANYTHING."

Reverie stares at you. "But... the others... the trapped dreamers..."

"We'll find another way. We'll build a BETTER dream.
One where The Somnambulist has no power. One where everyone's free—
AND we're together."

The Somnambulist laughs. "You can't have both. That's not how it WORKS."

"Watch me."

You don't destroy The Somnambulist. You REBUILD THE DREAM.
With your {weapon}, you carve new rules into the dreamscape.
A realm where waking is a choice. Where memories survive.
Where love doesn't dissolve in daylight.

It shouldn't work. It SHOULDN'T work.

But you've always been good at impossible things.

The Somnambulist's power CRUMBLES—not because you killed them,
but because you made them IRRELEVANT. Their rules don't apply anymore.

"What... what IS this?" they whisper, watching their throne dissolve.

"A dream worth living in," you say. "You should try it sometime."

🔮 PLOT TWIST: You don't wake up. But neither does Reverie.
   You stay—together—in a dreamscape you've remade into a HOME.
   And somehow, that's exactly where you belong.
""",
        },
    },
    {
        "title": "Chapter 7: The Dreamer's Truth",
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

🖤 THE VOID WALKER'S TRUTH:
You sacrificed everything—including your own attachment—to free others.
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
DARKNESS. EMPTINESS. ETERNITY—with Reverie at your side.

You dove into nightmares, burned your shame, and chose love over freedom.
The void became your canvas. Reverie became your everything.

🌑 THE SHADOW DREAMER'S TRUTH:
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
The crystallized suffering came with you—transformed into wisdom.

🔮 THE DARK SAGE'S TRUTH:
In the waking world, you help others face their fears.
The pain you kept became a teaching. The darkness became light—for others.

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
The dreamscape bows to you both—a kingdom of transformed terrors.

👑 THE NIGHTMARE KING'S TRUTH:
You became what The Somnambulist feared: a dark power that PROTECTS.
Every nightmare in the dreamscape serves you. Every shadow knows your name.

But you're not cruel. You're the guardian of necessary fears.
And Reverie rules beside you—equal, powerful, LOVED.

"We're the monsters under the bed now," they joke.

"The helpful kind."

The trapped dreamers you couldn't free? You protect them instead.
Give them GOOD nightmares. The kind that make you stronger.

THE END: The king of nightmares serves the dreamers' growth—with love at their side.
"""
            },
            "BAA": {
                "title": "THE LIGHT BEARER",
                "content": """
You stand in the waking world at power level {current_power}.
LIGHT. EMPTINESS. SACRIFICE.

You chose joy, released your pain, and let Reverie go free.
The light followed you into reality—a permanent inner glow.

☀️ THE LIGHT BEARER'S TRUTH:
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
LIGHT. EMPTINESS. FOREVER—with Reverie laughing beside you.

You chose joy, released your pain, and stayed in paradise.
Why would anyone leave? Why would anyone choose suffering over THIS?

🌈 THE ETERNAL CHILD'S TRUTH:
You don't remember the bad parts. Don't remember WHY you came here.
Just the joy. Just the love. Just Reverie.

"Is this real?" you ask sometimes.

"Does it matter?" they reply.

The Sandman watches from afar. Worried, maybe. But not interfering.
"Some people need this," they mutter. "Some people earned it."

Is it escape? Is it healing? Is it denial?

You're happy. Reverie's happy. The sun never sets here.

THE END: The eternal child never grows up—but maybe that's okay.
"""
            },
            "BBA": {
                "title": "THE COMPASSIONATE AWAKENER",
                "content": """
You stand in the waking world at power level {current_power}.
LIGHT. MEMORY. SACRIFICE.

You chose joy, preserved your pain, and let Reverie go.
Both came with you—the diamond and the light. Balance. Wholeness.

💚 THE COMPASSIONATE AWAKENER'S TRUTH:
You help others wake now. Gently. With understanding.
"Yes, it hurts," you tell them. "Yes, it's worth it."

Reverie is out there somewhere. Living. Happy. Free.
They don't remember you. That's okay. That was the point.

But sometimes, when you help someone leave the dreamscape,
you see their loved ones—waiting, hopeful, GRATEFUL.

And you remember: this is what you gave Reverie.
A world of people who love them. Even without you.

The Sandman retired. "You're better at this than I ever was," they said.
"Go save the dreamers. All of them."

THE END: The awakener carries both worlds—and makes them better.
"""
            },
            "BBB": {
                "title": "THE DREAM WEAVER",
                "content": """
You stand at the center of a new dreamscape at power level {current_power}.
LIGHT. MEMORY. LOVE—with Reverie woven into every part of it.

You chose joy, preserved your pain, and built a world worth living in.
Not escape. Not denial. CREATION.

✨ THE DREAM WEAVER'S TRUTH:
You remade the dreamscape into something beautiful.
The Somnambulist's old realm is a garden now. A sanctuary. A HOME.

Trapped dreamers come here to heal before they wake.
You and Reverie guide them. Teach them. Send them home stronger.

"We're the good kind of dream now," Reverie says.

"The BEST kind."

The Sandman officiates your dream-wedding. Cries a little.
"Didn't think I'd see a happy ending. Not here. Not ever."

🎭 THE DREAMER WAS ALWAYS THE DREAM.
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
                "label": "📧 Document Everything",
                "short": "patience",
                "description": "Build an airtight case. Patience is a weapon.",
            },
            "B": {
                "label": "🎤 Confront Him Now",
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
                "label": "🤝 Accept the Alliance",
                "short": "teamwork",
                "description": "Two against one. The enemy of my enemy...",
            },
            "B": {
                "label": "🚶 Go It Alone",
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
                "label": "⚖️ Total Justice",
                "short": "ruthless",
                "description": "Destroy his career completely. He earned it.",
            },
            "B": {
                "label": "🕊️ Graceful Victory",
                "short": "mercy",
                "description": "Win, but leave him standing. Be better.",
            },
        },
    },
}

UNDERDOG_CHAPTERS = [
    {
        "title": "Chapter 1: Monday Morning",
        "threshold": 0,
        "has_decision": False,
        "content": """
Your alarm goes off at 6:47 AM. You set it for 6:45 because you're optimistic.
You are not a morning person.

The coffee maker gurgles like it's judging you. It probably is.
You've worked at Nexus Industries for three years. Mid-level analyst. 
Decent salary. Soul-crushing commute. The usual.

Your {helmet} hangs by the door—a bike helmet, because you started cycling
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

🔮 PLOT TWIST: He didn't just steal your project.
   He's been planning this for MONTHS. You're just now catching up.

Your coworker Sam catches your eye from across the room.
They KNOW. You can see it in their face. They've seen the original files.

Your {weapon}—a pen, right now—shakes in your grip.

This is the moment. The one that defines who you become.
""",
    },
    {
        "title": "Chapter 2: The Evidence",
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

Your {chestplate}—well, it's actually a decent blazer you bought for interviews—
feels like armor. Or a target.

"I have proof," you say slowly. "My emails. My draft files. My—"

"Everyone has PROOF," Sam interrupts. "The question is whether anyone will CARE."

🔮 PLOT TWIST: Sam was burned by Marcus too. Three years ago.
   Their promotion. Gone. Given to Marcus's college roommate instead.
   They've been waiting for someone brave enough to fight back.

"I care," Sam says quietly. "And I know where he keeps his skeletons."

You stare at each other. This just became a conspiracy.

⚡ A CHOICE AWAITS... Marcus just took everything from you. Your move.
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: 📧 DOCUMENT EVERYTHING]

"We do this RIGHT," you say. "No mistakes. No room for spin."

Sam nods slowly. "The long game. I respect that."

For the next three weeks, you become a machine.
Every email. Every timestamp. Every meeting note.
You build a case so airtight it could survive a vacuum.

Your {gauntlets}—okay, they're just gloves for cycling—
remind you that patience is a muscle. You train it daily.

Sam feeds you intel. Marcus's patterns. His allies. His weaknesses.
The man has MANY weaknesses. Arrogance being the biggest.

"He doesn't think anyone is smart enough to catch him," Sam says.

"His mistake."

🔮 PLOT TWIST: While gathering evidence, you discover something bigger.
   Marcus hasn't just stolen YOUR project. He's stolen FIVE others.
   You're not alone. There's an army of victims waiting for a leader.
""",
            "B": """
[YOUR CHOICE: 🎤 CONFRONT HIM NOW]

"No more waiting," you say. "I'm ending this TODAY."

Sam's eyes go wide. "In front of everyone? That's either brilliant or career suicide."

"Why not both?"

You march into Marcus's office during his 3 PM call.
He's schmoozing with a vendor. Perfect hair. Perfect confidence. Perfect TARGET.

"Marcus." Your voice doesn't shake. Miracle. "We need to talk. About MY project."

The temperature in the room drops. Marcus's smile doesn't waver—
but his eyes go COLD.

"Buddy, I think you're confused—"

"I'm not your buddy. And I'm not confused. I have the original files.
Timestamped. Documented. I have witnesses who saw me build this from scratch."

🔮 PLOT TWIST: The vendor on the call? She records EVERYTHING for notes.
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
        "title": "Chapter 3: The Allies",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": """
Week four. Your case file is now a BINDER.

Other victims find you. Quietly. Carefully. Like survivors signaling each other.
There's Jamie from Marketing—Marcus took credit for the viral campaign.
There's Priya from Finance—he blamed her for HIS budget mistake.
There's Old Gerald from IT—who's been waiting 15 years for payback.

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

🔮 PLOT TWIST: Marcus knows something is happening.
   He's been too quiet. Too calm. Too CONFIDENT.
   He's planning something. You can feel it.

Your {amulet}—it's actually a good luck charm Sam gave you—
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

🔮 PLOT TWIST: There's a mole. Someone in your coalition is feeding Marcus info.
   Your next public statement gets "accidentally" leaked to HR.
   Now you're being investigated for "creating a hostile work environment."

Time to figure out who you can REALLY trust.
""",
        },
    },
    {
        "title": "Chapter 4: The Betrayal",
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

🔮 PLOT TWIST: Jordan is the one who PROMOTED Marcus three years ago.
   They created this monster. Now they want to destroy their creation.
   You're just the weapon they need.

"So," Jordan says, leaning back. "Partners?"

⚡ A CHOICE AWAITS... Jordan could end this overnight. But at what cost?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: 🤝 ACCEPT THE ALLIANCE]

"Partners," you agree. The word tastes complicated.

Jordan smiles—and this time it's REAL. "You won't regret this."

"I might. But I'll deal with that later."

The alliance changes everything. Suddenly you have ACCESS.
Board meeting schedules. Budget reviews. The CEO's CALENDAR.
Jordan opens doors you didn't even know existed.

Within a week, Marcus is being audited. "Routine," they call it.
But there's nothing routine about the forensic accountants.

Sam watches the escalation with growing concern.
"You're playing with fire," they warn. "Jordan doesn't do favors."

"I know. But Marcus doesn't do MERCY. Pick your poison."

🔮 PLOT TWIST: Jordan's plan involves more than just Marcus.
   They're restructuring the ENTIRE division. 
   Half the people who trusted you might lose their jobs.
   Is that a price you're willing to pay?

Your {shield}—the coalition you built—might become collateral damage.
""",
            "B": """
[YOUR CHOICE: 🚶 GO IT ALONE]

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

🔮 PLOT TWIST: Jordan becomes a third player in this game.
   Not quite enemy. Not quite ally. Just... WATCHING.
   Waiting to see who wins so they can claim the survivor.

Your coalition is smaller now. But it's YOURS.
""",
        },
    },
    {
        "title": "Chapter 5: The Showdown",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": """
The board meeting. The REAL one. The one where everything ends.

Jordan's plan unfolds like clockwork. Forensic audit. Documented fraud.
Five years of stolen credit laid bare in a 47-page report.

Marcus stands at the center of the room, sweating through his perfect suit.

"This is a WITCH HUNT," he snarls. "I've given this company everything—"

"You've given this company OTHER PEOPLE'S work," you interrupt.
"And charged them for the privilege."

The boardroom goes silent. You can hear the CEO breathing.

At {current_power} power, you're no longer the underdog.
You're the one with the evidence. The allies. The POWER.

Marcus turns to you with pure HATRED in his eyes.
"You think you've won? I made this place. I can UNMAKE you."

"Try."

🔮 PLOT TWIST: But Jordan's not done. They're already positioning
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
Your {boots}—cycling shoes, actually—are planted firmly.

"This ends at the board meeting," you say. "Everything comes out.
The timestamps. The witnesses. The pattern. All of it."

🔮 PLOT TWIST: Marcus pulls out his phone. Shows you something.
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

Your {amulet}—Sam's lucky charm—feels heavy now.

🔮 PLOT TWIST: Sam hasn't spoken to you in three days.
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
You can see it in his behavior—the snapping at assistants.
The long lunches. The whispered phone calls.

He's trying to make deals. Trying to find protection.
But he burned too many bridges. Nobody owes him anything.

Sam stays late with you, preparing the final presentation.
"We've got him," they say. "This is REALLY happening."

🔮 PLOT TWIST: The night before the board meeting, you get an email.
   From Marcus's WIFE. She's leaving him. And she has documents.
   Bank accounts. Hidden bonuses. A second property.
   Proof that he's been skimming from the company for YEARS.

This isn't just career theft anymore. This is CRIMINAL.
""",
        },
    },
    {
        "title": "Chapter 6: The Fall",
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

"I gave those people OPPORTUNITIES—"

"You gave yourself CREDIT. There's a difference."

🔮 PLOT TWIST: In his eyes, you see something unexpected. FEAR.
   Not of losing his job. Of losing his IDENTITY.
   Marcus Vance, golden boy, is just... a thief.
   He doesn't know who he is without the lies.

Across the table, you catch a familiar face watching. Waiting.
This moment has been a long time coming for both of you.

The CEO turns to you. "What do you recommend?"

⚡ A CHOICE AWAITS... Marcus is falling. How far do you let him drop?
""",
        "content_after_decision": {
            "A": """
[YOUR CHOICE: ⚖️ TOTAL JUSTICE]

"Everything," you say. "Full investigation. Criminal referral. Public disclosure.
Every project he stole. Every person he hurt. All of it."

The CEO nods slowly. "You understand that will create... complications."

"I understand it will create ACCOUNTABILITY."

Marcus's face goes white. Then red. Then something beyond color.
"You can't DO this—I have FRIENDS—"

"Had," someone mutters from the table. "Past tense."

The fall is complete. ABSOLUTE.
Criminal investigation. Civil lawsuits. Professional exile.
Marcus Vance becomes a cautionary tale told at industry conferences.

Sam finds you afterward, in the parking garage.
"You did it," they say. "You actually DID it."

"WE did it."

🔮 PLOT TWIST: Your phone buzzes. A message about the VP of Operations role.
   The position is opening up. People are asking if you're interested.
   Now comes the question: what kind of victory do you WANT?
""",
            "B": """
[YOUR CHOICE: 🕊️ GRACEFUL VICTORY]

"Resignation," you say. "Quiet. No prosecution. He leaves, we move on."

The boardroom stirs. Murmurs. Surprise.

"After everything he did?" the CEO asks.

"After everything he did, he's FINISHED. Everyone knows. Everyone will remember.
But I don't want to become him. I don't want to destroy someone for sport."

Marcus stares at you. Confusion. Suspicion. Something that might be... gratitude?

"Get out," you tell him. "Start over somewhere else. Be better."

The meeting ends. Marcus leaves. Not in handcuffs—in a taxi.
His career is over. But he's still standing. Barely.

Sam finds you afterward. Their expression is complicated.
"That was... unexpected. Merciful."

"I just didn't want to become the monster to beat the monster."

🔮 PLOT TWIST: A month later, you get a letter. From Marcus.
   No return address. Just three words: "You were right."
   You're not sure what he means. But somehow, it matters.
""",
        },
    },
    {
        "title": "Chapter 7: The Victory",
        "threshold": 1500,
        "has_decision": False,
        "endings": {
            "AAA": {
                "title": "THE POWER PLAYER",
                "content": """
One year later. Power level {current_power}.
PATIENCE. ALLIANCE. RUTHLESSNESS.

You sit in Marcus's old office. Bigger desk. Better view. YOUR name on the door.
VP of Operations. The job you never wanted—until you earned it.

Jordan Cross is CEO now. The coup within the coup was real.
But you're not their puppet. You're their PARTNER.
The company runs cleaner now. Fairer. Not perfect—but better.

🏆 THE POWER PLAYER'S TRUTH:
You built alliances. You wielded power. You destroyed an enemy completely.
And in the wreckage, you built something STRONGER.

Sam runs their own department now. They smile when they pass your office.
"Never thought I'd see the day," they say.

"Neither did I."

But late at night, sometimes, you wonder:
Did you win? Or did you just become the new Marcus?

The view from the top is lonely. But at least it's YOURS.

THE END: The patient hunter claims the throne—and everything that comes with it.
"""
            },
            "AAB": {
                "title": "THE BENEVOLENT VICTOR",
                "content": """
One year later. Power level {current_power}.
PATIENCE. ALLIANCE. MERCY.

The corner office is yours. But you've done something unprecedented—
opened the door. Literally. The whole floor can see you work.
No more secrets. No more stolen credit. No more fear.

Jordan Cross runs the company now. They're... watching you.
You're an experiment to them. A new kind of leader.
Merciful but effective. Kind but STRONG.

🏆 THE BENEVOLENT VICTOR'S TRUTH:
You proved that you can win without destroying.
That power doesn't have to corrupt. That victory can be CLEAN.

Sam is your VP now. They still can't believe it.
"You gave mercy to the man who tried to ruin you."

"And look what happened. He's gone. But WE'RE still here.
Still together. Still better."

Marcus sent a donation to the company charity last month.
Anonymous. But you knew. Somehow, you knew.

THE END: The patient victor builds a legacy—not just a career.
"""
            },
            "ABA": {
                "title": "THE LONE WOLF",
                "content": """
One year later. Power level {current_power}.
PATIENCE. INDEPENDENCE. RUTHLESSNESS.

You didn't take Jordan's deal. You didn't take Marcus's job.
You took something BETTER—freedom.

Your own consulting firm. YOUR name on the building.
Helping companies find the Marcuses hiding in their ranks.
You're not cheap. You're WORTH IT.

🏆 THE LONE WOLF'S TRUTH:
You proved that you could do it alone. Without allies. Without compromise.
And in the independence, you found something Marcus never had—peace.

Sam visits sometimes. They stayed at Nexus. Changed it from within.
"You could have been running that place," they say.

"I'd rather run THIS place." You gesture at your small, perfect office.
"No politics. No games. Just the work."

Marcus disappeared. Last you heard, he was selling real estate.
The fall was complete. The victory was YOURS.

THE END: The lone wolf answers to no one—and that's exactly how you like it.
"""
            },
            "ABB": {
                "title": "THE HUMBLE CHAMPION",
                "content": """
One year later. Power level {current_power}.
PATIENCE. INDEPENDENCE. MERCY.

You turned down the VP job. Shocked everyone—including yourself.

Instead, you're running the mentorship program now.
Helping new employees navigate the politics. Protecting them from predators.
Building the company you WISHED existed when you started.

🏆 THE HUMBLE CHAMPION'S TRUTH:
You won without destroying. Built without consuming.
And in the humility, you found something Marcus never understood—happiness.

Sam leads your old department. They're GOOD at it.
"You trained half of them," they remind you.

"I just showed them what NOT to do."

Marcus runs a small business now. Cleaning services.
Honest work. A fresh start. You sent him a client referral once.
He never acknowledged it. That's okay.

THE END: The humble champion builds people—not empires.
"""
            },
            "BAA": {
                "title": "THE REVOLUTIONARY",
                "content": """
One year later. Power level {current_power}.
BOLDNESS. ALLIANCE. RUTHLESSNESS.

You didn't just take down Marcus. You took down the whole SYSTEM.

Jordan's coup succeeded—but so did yours.
The old guard is GONE. Replaced by people like you.
People who earned their positions. People who REMEMBERED.

🏆 THE REVOLUTIONARY'S TRUTH:
Your confrontation sparked a movement. Your alliance made it unstoppable.
And when Marcus fell, everyone who protected him fell too.

Sam is Chief People Officer now. They spend most of their time
making sure another Marcus never rises again.

"Revolution isn't a single act," they told you once.
"It's constant vigilance."

You've become the vigilance. The standard. The warning.
Cross someone like you, and the whole company knows.

THE END: The revolutionary tears down the old world—and builds a new one.
"""
            },
            "BAB": {
                "title": "THE PEOPLE'S CHAMPION",
                "content": """
One year later. Power level {current_power}.
BOLDNESS. ALLIANCE. MERCY.

The corner office is yours. But you earned it DIFFERENTLY.

Your public confrontation made you famous—inside the company and OUT.
Business magazines interviewed you. Other victims reached out.
You became a SYMBOL.

🏆 THE PEOPLE'S CHAMPION'S TRUTH:
You proved that speaking up WORKS. That bullies can be beaten.
That mercy doesn't mean weakness—it means STRENGTH.

Sam co-leads the department with you. Equal partners.
"Remember when you confronted him in his office?"

"I nearly threw up afterward."

"And now you're running the place. Funny how that works."

Jordan sends congratulations sometimes. They're still watching.
Maybe they learned something from you. Maybe not.
Either way—you're not their weapon. You're their EXAMPLE.

THE END: The people's champion speaks truth—and the truth wins.
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

🏆 THE SHADOW KING'S TRUTH:
Marcus wanted spotlight. Jordan wants glory.
You? You want OVERSIGHT. And you HAVE it.

No one steals credit anymore. Not with you watching.
No one takes shortcuts. Not with your audits.
The company is cleaner, sharper, BETTER—because of you.

Sam visits your quiet office sometimes.
"You know you're the most powerful person here, right?"

"I know. That's the point. Power that looks like service."

Marcus tried to come back last month. Applied for a contract.
Your desk. Your review. Your signature.

DENIED.

THE END: The shadow king rules from the dark—and the light never touches him.
"""
            },
            "BBB": {
                "title": "THE HAPPY ENDING",
                "content": """
One year later. Power level {current_power}.
BOLDNESS. INDEPENDENCE. MERCY.

Everything worked out. ACTUALLY worked out.

You're VP of Operations now—but you didn't fight for it.
They OFFERED. After everything you did. After everything you DIDN'T do.
The mercy impressed them more than the victory.

Sam is by your side. Not as an employee—as a PARTNER.
Somewhere between the confrontations and the board meetings,
you fell in love. Neither of you planned it. Both of you meant it.

🏆 THE HAPPY ENDING'S TRUTH:
You beat the bully. You won the job. You got the person.
Not because you were ruthless—because you were GOOD.

Marcus works for a nonprofit now. Helping at-risk youth.
You wrote him a recommendation letter. It felt RIGHT.

The corner office has pictures on the desk.
Sam. Your dog. The coalition at last year's holiday party.
Real people. Real victories. Real life.

🎭 THE UNLIKELY HERO WAS ALWAYS INSIDE YOU.
   THE VICTORY WAS ALWAYS ABOUT MORE THAN WINNING.
   THE HAPPY ENDING WAS ALWAYS POSSIBLE.

THE END: The unlikely champion wins everything—and deserves all of it.
"""
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
    
    Returns:
        dict with 'current_chapter', 'unlocked_chapters', 'chapters', 'next_threshold', 
        'power', 'decisions', 'selected_story', 'story_info'
    """
    story_decisions, story_chapters = get_story_data(adhd_buster)
    story_id = get_selected_story(adhd_buster)
    story_info = AVAILABLE_STORIES.get(story_id, AVAILABLE_STORIES["warrior"])
    
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
    for i, chapter in enumerate(story_chapters):
        chapter_num = i + 1
        is_unlocked = chapter_num in unlocked
        has_decision = chapter.get("has_decision", False)
        decision_made = False
        if has_decision:
            decision_info = story_decisions.get(chapter_num)
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
        "total_chapters": len(story_chapters),
        "next_threshold": next_threshold,
        "power_to_next": next_threshold - power if next_threshold else 0,
        "decisions": decisions,
        "decisions_made": len(decisions),
        "selected_story": story_id,
        "story_info": story_info,
    }


def get_decision_for_chapter(chapter_number: int, adhd_buster: dict = None) -> dict | None:
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


def make_story_decision(adhd_buster: dict, chapter_number: int, choice: str) -> bool:
    """
    Record a story decision. Returns True if successful.
    
    Args:
        adhd_buster: The user's ADHD Buster data (will be modified)
        chapter_number: The chapter where the decision is made
        choice: "A" or "B"
    """
    ensure_hero_structure(adhd_buster)
    story_decisions, _ = get_story_data(adhd_buster)
    decision_info = story_decisions.get(chapter_number)
    if not decision_info:
        return False
    if choice not in ("A", "B"):
        return False
    
    if "story_decisions" not in adhd_buster:
        adhd_buster["story_decisions"] = {}
    
    adhd_buster["story_decisions"][decision_info["id"]] = choice
    
    # Sync decision back to the hero
    sync_hero_data(adhd_buster)
    return True


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


def get_chapter_content(chapter_number: int, adhd_buster: dict) -> dict | None:
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
    decision_info = story_decisions.get(chapter_number)
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
        "title": "📖 Story Mode",
        "description": "Follow a story with your hero. Each story has its own hero and progress.",
    },
    STORY_MODE_HERO_ONLY: {
        "id": STORY_MODE_HERO_ONLY,
        "title": "⚔️ Hero Only",
        "description": "Level up your hero without following a story. Just collect gear and grow stronger.",
    },
    STORY_MODE_DISABLED: {
        "id": STORY_MODE_DISABLED,
        "title": "🚫 Disabled",
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
    
    # Create migrated hero (assign all old data to the story they were playing)
    migrated_hero = {
        "inventory": old_inventory,
        "equipped": old_equipped,
        "story_decisions": old_decisions,
        "diary": old_diary,
        "luck_bonus": old_luck,
        "total_collected": old_collected,
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
    
    # Sync flat structure for backward compatibility
    _sync_active_hero_to_flat_internal(adhd_buster)
    
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
    elif mode == STORY_MODE_HERO_ONLY:
        hero = adhd_buster.get("free_hero", _create_empty_hero())
        adhd_buster["inventory"] = hero.get("inventory", [])
        adhd_buster["equipped"] = hero.get("equipped", {})
        adhd_buster["story_decisions"] = hero.get("story_decisions", {})
        adhd_buster["diary"] = hero.get("diary", [])
        adhd_buster["luck_bonus"] = hero.get("luck_bonus", 0)
        adhd_buster["total_collected"] = hero.get("total_collected", 0)
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
    adhd_buster["story_mode"] = mode
    _sync_active_hero_to_flat(adhd_buster)
    return True


def get_active_story_id(adhd_buster: dict) -> str | None:
    """
    Get the currently active story ID.
    Returns None if in hero_only or disabled mode.
    """
    ensure_hero_structure(adhd_buster)
    mode = adhd_buster.get("story_mode", STORY_MODE_ACTIVE)
    
    if mode != STORY_MODE_ACTIVE:
        return None
    
    return adhd_buster.get("active_story", "warrior")


def get_active_hero(adhd_buster: dict) -> dict | None:
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
    """
    ensure_hero_structure(adhd_buster)
    hero = get_active_hero(adhd_buster)
    
    if hero is None:
        return  # Disabled mode, nothing to sync
    
    # Sync flat data back to hero
    hero["inventory"] = adhd_buster.get("inventory", [])
    hero["equipped"] = adhd_buster.get("equipped", {})
    hero["story_decisions"] = adhd_buster.get("story_decisions", {})
    hero["diary"] = adhd_buster.get("diary", [])
    hero["luck_bonus"] = adhd_buster.get("luck_bonus", 0)
    hero["total_collected"] = adhd_buster.get("total_collected", 0)


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


def get_hero_summary(adhd_buster: dict, story_id: str = None) -> dict | None:
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
    """
    _sync_flat_to_active_hero(adhd_buster)
