"""
Personal Freedom - Website Blocker for Focus Time
A Windows application to block distracting websites during focus sessions.

Enhanced Version with Industry-Standard Features:
- Multiple blocking modes (Strict, Normal, Pomodoro)
- Schedule-based blocking
- Statistics and productivity tracking
- Password protection
- Break reminders
- Import/Export blacklists
- Website categories
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import time
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from core_logic import (
    BlockerCore, BlockMode, SITE_CATEGORIES,
    AI_AVAILABLE, LOCAL_AI_AVAILABLE,
    STATS_PATH, GOALS_PATH
)

# Check if bypass logger is available
try:
    from core_logic import BYPASS_LOGGER_AVAILABLE
except ImportError:
    BYPASS_LOGGER_AVAILABLE = False

# Re-import AI classes if available, for GUI usage
if AI_AVAILABLE:
    from productivity_ai import ProductivityAnalyzer, GamificationEngine, FocusGoals
else:
    # Stub classes when AI not available
    ProductivityAnalyzer = None  # type: ignore
    GamificationEngine = None  # type: ignore
    FocusGoals = None  # type: ignore

if LOCAL_AI_AVAILABLE:
    from local_ai import LocalAI
else:
    LocalAI = None  # type: ignore

# Try to import tray support
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


# Days of the week for priority scheduling
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ============================================================================
# ADHD Buster Gamification System
# ============================================================================

import random

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
# Items can share "theme words" in their names or suffixes.
# Equipping multiple items with the same theme gives a set bonus.

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
            # e.g., "fire" shouldn't match "backfire"
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
    theme_items = {}  # Track which items belong to each theme
    
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
# Combine multiple items for a CHANCE at a higher tier item.
# Base success rate is 10% - each item adds to the probability.
# On failure (90% base), ALL items are lost forever!

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
    """
    Calculate the success rate for a lucky merge.
    
    Args:
        items: List of items to merge (minimum 2)
        luck_bonus: Accumulated luck from salvaging
    
    Returns:
        Success probability (0.0 to MERGE_MAX_SUCCESS_RATE)
    """
    if len(items) < 2:
        return 0.0
    
    # Base rate + bonus per extra item
    rate = MERGE_BASE_SUCCESS_RATE + (len(items) - 2) * MERGE_BONUS_PER_ITEM
    
    # Luck bonus: every 100 luck = +1% (1000 luck = +10% max)
    luck_bonus_pct = min(luck_bonus / 100 * 0.01, 0.10)
    rate += luck_bonus_pct
    
    # Cap at max rate
    return min(rate, MERGE_MAX_SUCCESS_RATE)


def get_merge_result_rarity(items: list) -> str:
    """
    Determine the rarity of the merged item result.
    
    The result is ONE tier higher than the LOWEST rarity item in the merge.
    This encourages using same-rarity items for best results.
    """
    if not items:
        return "Common"
    
    # Find lowest rarity
    lowest_idx = min(RARITY_ORDER.index(item.get("rarity", "Common")) for item in items)
    lowest_rarity = RARITY_ORDER[lowest_idx]
    
    # Upgrade by one tier
    return RARITY_UPGRADE.get(lowest_rarity, "Uncommon")


def is_merge_worthwhile(items: list) -> tuple:
    """
    Check if a merge is worthwhile (can result in upgrade).
    
    Returns:
        (is_worthwhile: bool, reason: str)
    """
    if not items or len(items) < 2:
        return False, "Need at least 2 items"
    
    # Check if all items are Legendary
    all_legendary = all(item.get("rarity") == "Legendary" for item in items)
    if all_legendary:
        return False, "All items are Legendary - merge cannot upgrade!"
    
    return True, ""


def perform_lucky_merge(items: list, luck_bonus: int = 0) -> dict:
    """
    Attempt a lucky merge of items.
    
    Returns:
        {
            "success": bool,
            "result_item": item dict or None,
            "items_lost": list of items consumed,
            "roll": float (the actual roll 0-1),
            "needed": float (success threshold)
        }
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
        "needed_pct": f"{success_rate*100:.1f}%"
    }
    
    if result["success"]:
        # Generate a new item of higher rarity!
        result_rarity = get_merge_result_rarity(items)
        result["result_item"] = generate_item(rarity=result_rarity)
    else:
        result["result_item"] = None
    
    return result


# ============================================================================
# ADHD Buster Diary - Epic Adventure Journal System
# ============================================================================
# Diary entries are generated based on character power level.
# Higher power = more epic and extraordinary adventures!

# Power tiers for diary generation
DIARY_POWER_TIERS = {
    "pathetic": (0, 49),       # Starting out, humble adventures
    "modest": (50, 149),       # Getting somewhere
    "decent": (150, 349),      # Respectable adventurer
    "heroic": (350, 599),      # True hero status
    "epic": (600, 999),        # Epic warrior
    "legendary": (1000, 1499), # Legendary champion
    "godlike": (1500, 2000)    # Focus deity
}

# === VERBS by power tier ===
DIARY_VERBS = {
    "pathetic": [
        "accidentally poked", "awkwardly stared at", "tripped over", "licked",
        "politely asked", "nervously waved at", "mildly annoyed", "quietly judged",
        "bumped into", "accidentally sat on", "coughed near", "sneezed at",
        "gave a participation trophy to", "made eye contact with", "slightly nudged",
        "mumbled at", "waddled toward", "unsuccessfully high-fived", "apologized to",
        "stood next to", "accidentally photobombed", "passive-aggressively sighed at",
        "gave an awkward thumbs-up to", "made a weird face at", "lost a staring contest to",
        "shared an awkward elevator ride with", "sent an email to", "left a voicemail for",
        "accidentally liked an old photo of", "tried to unfriend", "forgot the name of"
    ],
    "modest": [
        "challenged", "pushed", "tickled", "startled", "confused", "outsmarted",
        "debated", "out-danced", "arm-wrestled", "had lunch with", "roasted",
        "pranked", "traded snacks with", "shared a blanket with", "high-fived",
        "karaoked with", "played cards with", "had an intense staring match with",
        "went shopping with", "had a pillow fight with", "told a dad joke to",
        "challenged to rock-paper-scissors", "made a TikTok with", "photobombed",
        "beat at checkers", "shared a pizza with", "did a trust fall with",
        "had a dance-off with", "played charades with", "made friendship bracelets with"
    ],
    "decent": [
        "fought", "defeated in combat", "had an epic duel with", "outmaneuvered",
        "tactically retreated from", "formed an alliance with", "rescued",
        "was rescued by", "traded ancient secrets with", "meditated with",
        "trained alongside", "went on a quest with", "discovered treasure with",
        "navigated a dungeon with", "survived a storm with", "broke bread with",
        "swore a blood oath with", "competed in a tournament against",
        "discovered a hidden village with", "decoded ancient runes with",
        "brewed a potion with", "forged a weapon with", "tamed a beast with",
        "explored ruins with", "outwitted in a riddle contest", "sparred with"
    ],
    "heroic": [
        "slayed", "vanquished", "banished to another realm", "imprisoned in crystal",
        "sealed away forever", "turned to stone", "defeated with one strike",
        "humiliated in front of their army", "outsmarted in dimensional chess",
        "absorbed the power of", "broke the curse of", "freed from eternal slumber",
        "merged consciousness with", "time-traveled with", "shapeshifted with",
        "opened a portal with", "closed a rift alongside", "rewrote destiny with",
        "shattered the illusion of", "awakened the true power of", "united kingdoms with",
        "ended a millennium-long war with", "discovered the origin story of",
        "granted a second chance to", "fulfilled an ancient prophecy with"
    ],
    "epic": [
        "obliterated from existence", "erased from the timeline", "trapped in a paradox",
        "fused into a single being with", "ascended to godhood alongside",
        "challenged the very concept of", "rewrote the laws of physics with",
        "bent reality around", "consumed the essence of", "became the avatar of",
        "transcended mortality with", "shattered dimensions fighting",
        "created a new universe with", "collapsed a star to defeat",
        "reversed entropy alongside", "became legend after meeting",
        "split into parallel versions fighting", "absorbed into the void alongside",
        "merged timelines with", "became the living prophecy of",
        "unwrote the existence of", "became the eternal nemesis of"
    ],
    "legendary": [
        "became one with the cosmos alongside", "achieved omniscience from",
        "transcended time and space with", "became the last memory of",
        "is now worshipped alongside", "became a fundamental force with",
        "now exists simultaneously with", "merged with the universal consciousness and",
        "became the concept of focus itself with", "rewrote all of existence with",
        "is now eternal thanks to", "became the beginning and end with",
        "ascended beyond comprehension with", "is now a paradox because of",
        "exists outside reality with", "became the dream of existence with"
    ],
    "godlike": [
        "created and destroyed infinite realities with",
        "became the alpha and omega alongside",
        "is now the fundamental equation of existence with",
        "transcended all possible dimensions with",
        "became the universe's source code with",
        "is now simultaneously everything and nothing with",
        "achieved focus so pure it bent reality with",
        "became the personification of pure productivity with",
        "rewrote the multiverse's operating system with",
        "is now an eternal constant of mathematics with",
        "became the voice of the cosmic background radiation with",
        "transcended the concept of transcendence with"
    ]
}

# === TARGET ADJECTIVES by power tier ===
DIARY_ADJECTIVES = {
    "pathetic": [
        "a mildly inconvenienced", "a slightly annoyed", "a confused-looking",
        "an unimpressed", "a suspiciously normal", "a forgettable", "a generic",
        "a low-budget", "a discount", "an off-brand", "a knock-off", "a B-list",
        "a questionable", "a somewhat sketchy", "a mediocre", "an adequate",
        "a barely-trying", "an underwhelming", "a participation-trophy-worthy",
        "a 'good enough'", "a 'meh'-level", "a basic", "a budget-friendly",
        "an economy-class", "a store-brand", "a clearance-rack", "a refurbished"
    ],
    "modest": [
        "a reasonably impressive", "a decent", "an actually-trying", "a notable",
        "an interesting", "a surprising", "an unexpected", "a capable",
        "a competent", "a professional", "a trained", "an experienced",
        "a battle-tested", "a weathered", "a seasoned", "a respectable",
        "a noteworthy", "a remarkable", "a distinguished", "an admirable",
        "a formidable", "an accomplished", "a proven", "a reliable"
    ],
    "decent": [
        "a legendary", "a mythical", "an ancient", "a powerful", "a fearsome",
        "a dreaded", "a fabled", "a renowned", "a notorious", "an infamous",
        "a celebrated", "an honored", "a revered", "a mighty", "a terrible",
        "an awe-inspiring", "a magnificent", "a glorious", "a majestic",
        "a regal", "an imperial", "a sovereign", "a supreme", "a paramount"
    ],
    "heroic": [
        "a reality-bending", "a dimension-hopping", "a time-traveling", "a fate-weaving",
        "a prophecy-fulfilling", "a destiny-altering", "a world-shaking",
        "a civilization-ending", "a cosmos-spanning", "a plane-shifting",
        "a void-touched", "an eternally-cursed", "a divinely-blessed",
        "a chaos-infused", "an order-maintaining", "a balance-keeping",
        "a myth-made-real", "a legend-incarnate", "a story-become-flesh"
    ],
    "epic": [
        "an infinitely powerful", "an omniscient", "an omnipotent", "an omnipresent",
        "a beyond-comprehension", "a reality-defining", "a universe-creating",
        "a dimension-ruling", "a multiverse-spanning", "a timeline-controlling",
        "a causality-breaking", "an entropy-defying", "a existence-transcending",
        "a concept-embodying", "a fundamental-force-channeling"
    ],
    "legendary": [
        "a cosmic-horror-yet-somehow-friendly", "an incomprehensible-but-approachable",
        "a beyond-all-understanding-yet-cool", "a reality-core-manifestation-of",
        "a living-paradox-that-is", "an existence-contradiction-known-as",
        "a fundamental-truth-embodied-as", "a universe-equation-personified-as"
    ],
    "godlike": [
        "the very concept of", "the fundamental essence of",
        "the living equation that is", "the cosmic constant known as",
        "the universal truth embodied as", "existence itself manifested as",
        "the alpha and omega that is", "infinity given form as",
        "the source code of reality known as", "pure mathematics embodied as"
    ]
}

# === TARGETS (creatures/beings) by power tier ===
DIARY_TARGETS = {
    "pathetic": [
        "an intern", "a confused tourist", "a lost pizza delivery guy",
        "someone's weird uncle", "a procrastinating student", "a grumpy cat",
        "a judgmental squirrel", "a suspicious pigeon", "a distracted goldfish",
        "a passive-aggressive roommate", "a vague acquaintance", "someone's ex",
        "a LinkedIn recruiter", "an overly enthusiastic gym bro", "a crypto bro",
        "a reply-all email offender", "a meeting-that-could-be-an-email person",
        "a close-talker", "a loud chewer", "a spoiler-revealer", "a microwave fish person",
        "a double-dipper", "a queue-cutter", "a one-upper", "a humble-bragger"
    ],
    "modest": [
        "a minor goblin", "a trainee wizard", "an apprentice knight", "a baby dragon",
        "a teenage vampire", "a part-time werewolf", "a gig-economy demon",
        "an entry-level orc", "a freelance troll", "a startup fairy",
        "a junior necromancer", "a mid-level ghost", "a regional manager lich",
        "an assistant to the regional manager witch", "a seasonal skeleton",
        "a temp zombie", "an unpaid intern at Evil Corp", "a dropout from wizard school"
    ],
    "decent": [
        "a proper dragon", "an experienced sorcerer", "a veteran knight",
        "a master assassin", "an ancient lich", "a demon lord", "an angel captain",
        "a phoenix in its prime", "a kraken", "a hydra", "a cerberus",
        "a sphinx with hard riddles", "a minotaur champion", "a giant king",
        "a vampire elder", "a werewolf alpha", "an elemental lord",
        "a djinn of great power", "a golem of legend", "a roc of the mountains"
    ],
    "heroic": [
        "an elder god", "a titan of old", "a primordial being", "an arch-demon",
        "an archangel", "a god of war", "a goddess of wisdom", "a lord of chaos",
        "a keeper of time", "a weaver of fate", "a guardian of dimensions",
        "a master of elements", "a sovereign of souls", "an emperor of the void",
        "a harbinger of apocalypse", "a bringer of dawn", "a shaper of worlds",
        "a destroyer of realities", "a creator of universes"
    ],
    "epic": [
        "the concept of entropy itself", "the physical manifestation of chaos",
        "the living embodiment of time", "the sentient void between dimensions",
        "the consciousness of a dying universe", "the dream of a sleeping god",
        "the nightmare of existence", "the echo of the big bang",
        "the whisper of heat death", "the scream of creation", "reality's fever dream",
        "the universe's intrusive thought", "existence's autocorrect error"
    ],
    "legendary": [
        "the mathematical constant that defines all reality",
        "the final theorem of existence", "the first thought ever conceived",
        "the last breath of the multiverse", "the moment between moments",
        "the concept of concepts", "the meta-narrative of all stories",
        "the observer that collapsed the wave function", "the dreamer dreaming all dreams"
    ],
    "godlike": [
        "the source code of existence", "the original writer of reality",
        "the concept of focus that created the universe", "infinity's calculator",
        "the equation that solved itself into existence",
        "the cursor that blinks at the end of all programs",
        "the final commit to the cosmic repository",
        "the merge conflict at the heart of reality"
    ]
}

# === LOCATIONS by power tier ===
DIARY_LOCATIONS = {
    "pathetic": [
        "in the break room", "at a gas station bathroom", "in a DMV waiting room",
        "at a sketchy laundromat", "in a Wendy's parking lot", "at a bus stop",
        "in someone's unfinished basement", "at a midnight Walmart",
        "in a mall food court", "at a sad office party", "in a dentist's waiting room",
        "at a timeshare presentation", "in an IKEA showroom", "at a speed-dating event",
        "in a haunted Denny's", "at 3AM in a 7-Eleven", "in a LinkedIn message thread",
        "at a pyramid scheme meeting", "in a homeowner's association meeting",
        "at an airport baggage claim", "in a zoom call with camera on"
    ],
    "modest": [
        "in a mysterious forest", "at an ancient crossroads", "in a forgotten temple",
        "at a haunted inn", "in a magical marketplace", "at the edge of civilization",
        "in a dragon's outer cave", "at the gates of a dark castle",
        "in a pixie's garden", "at a wizard's doorstep", "in goblin territory",
        "at the troll bridge", "in the shadows of the dark tower",
        "at the entrance to the underworld", "in the neutral zone"
    ],
    "decent": [
        "in the heart of an erupting volcano", "at the peak of the world's tallest mountain",
        "in the depths of the ocean abyss", "at the center of an eternal storm",
        "in the frozen wastelands of the north", "at the edge of the world",
        "in the sacred grove of ancient power", "at the convergence of ley lines",
        "in the ruins of a fallen civilization", "at the gates of the underworld",
        "in the dragon's treasure hoard", "at the court of the fae queen"
    ],
    "heroic": [
        "in the space between dimensions", "at the crossroads of all timelines",
        "in the void between stars", "at the edge of a black hole",
        "in the dreams of a sleeping god", "at the moment of creation",
        "in the echo of the big bang", "at the end of entropy",
        "in the library of infinite knowledge", "at the council of cosmic entities",
        "in the forge where suns are born", "at the graveyard of dead universes"
    ],
    "epic": [
        "in a reality that shouldn't exist", "at the intersection of all possibilities",
        "in the negative space of existence", "at the point where math breaks down",
        "in the error message of the universe", "at the event horizon of consciousness",
        "in the quantum superposition of all locations simultaneously",
        "at the place that exists only when observed", "in the paradox zone"
    ],
    "legendary": [
        "in the concept of 'here' before 'here' existed",
        "at the philosophical debate about whether places are real",
        "in the space between thoughts", "at the origin of the question 'where'",
        "in the metadata of reality", "at the config file of existence"
    ],
    "godlike": [
        "in the source code repository of existence",
        "at the root directory of all dimensions",
        "in the production environment of the cosmos",
        "at the pull request that created reality",
        "in the git blame of the universe",
        "at the stack overflow that became sentient"
    ]
}

# === OUTCOMES by power tier ===
DIARY_OUTCOMES = {
    "pathetic": [
        "a minor inconvenience", "an awkward silence", "a participation certificate",
        "a weird look", "a very confusing email thread", "both of us just walking away",
        "someone calling HR", "an unfollowing on social media", "a 1-star Yelp review",
        "a passive-aggressive post-it note", "mutual agreement to never speak of this",
        "someone's mom getting involved", "a very long and uncomfortable elevator ride",
        "us pretending we don't know each other", "a strongly worded letter",
        "someone being 'just disappointed'", "a mildly viral Twitter thread",
        "a meeting that could have been an email", "an unsubscribe from my newsletter"
    ],
    "modest": [
        "unexpected friendship", "a temporary truce", "mutual respect",
        "a rematch scheduled for next week", "both of us going our separate ways",
        "a lesson learned by both parties", "a handshake and a beer",
        "an exchange of contact information", "a small but meaningful victory",
        "a story to tell at parties", "a minor wound and a major ego boost",
        "recognition in the local tavern", "a discount at the merchant's shop",
        "a reluctant alliance", "trading secrets", "sharing a meal"
    ],
    "decent": [
        "a grand victory", "absolute triumph", "hard-won glory", "legendary status",
        "songs written about it", "a statue being commissioned", "national holidays",
        "the enemy's eternal respect", "a blood oath of loyalty", "ancient secrets revealed",
        "unlocking hidden potential", "the forge of a legendary weapon",
        "the discovery of lost magic", "ascension to noble rank", "a kingdom saved"
    ],
    "heroic": [
        "the rewriting of prophecy", "reality itself shifting", "a new age beginning",
        "the old gods taking notice", "dimensions merging temporarily",
        "time flowing differently", "the fabric of space rippling",
        "a new constellation appearing", "the sun hesitating", "the moon applauding",
        "the stars rearranging themselves", "causality questioning itself",
        "fate throwing up its hands", "destiny asking for a rewrite",
        "the universe issuing an official statement"
    ],
    "epic": [
        "the multiverse experiencing an existential crisis",
        "several timelines just... stopping to watch",
        "infinity googling 'how to handle this'",
        "the cosmic background radiation stuttering",
        "entropy briefly considering retirement",
        "the heat death of the universe being postponed",
        "causality filing a formal complaint",
        "reality asking if this is being documented",
        "the simulation requesting more RAM"
    ],
    "legendary": [
        "the concept of 'endings' having to be redefined",
        "philosophy departments worldwide spontaneously combusting",
        "mathematics having to add new axioms",
        "physics submitting a resignation letter",
        "the universe's terms of service being updated",
        "existence itself leaving a 5-star review",
        "the cosmic debugger being permanently confused"
    ],
    "godlike": [
        "a new mathematical constant being defined: focus",
        "the universe's source code being refactored",
        "reality getting a major version update",
        "existence's unit tests finally passing",
        "the cosmic CI/CD pipeline being optimized",
        "infinity getting a performance review",
        "the multiverse achieving inbox zero",
        "time management becoming a fundamental force",
        "productivity replacing entropy as the universe's destiny"
    ]
}

# === ADDITIONAL FLAVOR by power tier ===
DIARY_FLAVOR = {
    "pathetic": [
        "I was wearing mismatched socks.",
        "My phone was at 2% battery.",
        "I had spinach in my teeth the whole time.",
        "I forgot everyone's names.",
        "My shoelace was untied.",
        "I accidentally called them 'mom'.",
        "I waved at someone who wasn't waving at me.",
        "I had 47 unread emails at the time.",
        "Mercury was in retrograde, which explains everything.",
        "I hadn't had my coffee yet.",
        "I was still wearing my 'Work From Home' outfit. The one with stains."
    ],
    "modest": [
        "The weather was surprisingly pleasant.",
        "Someone took a really blurry photo of it.",
        "A random bard wrote a mediocre song about it.",
        "The local newspaper might cover it on page 17.",
        "I got a free appetizer out of the deal.",
        "My mom would probably be proud.",
        "It was definitely better than my last Tuesday.",
        "At least three witnesses can confirm this happened."
    ],
    "decent": [
        "The stars literally aligned for this moment.",
        "Ancient prophecies were fulfilled. Not the important ones, but still.",
        "A wise old sage nodded approvingly from somewhere.",
        "The very elements seemed to acknowledge my presence.",
        "Bards will sing of this. Probably during happy hour specials.",
        "My ancestors smiled upon me. Even the weird ones."
    ],
    "heroic": [
        "Reality itself paused to take notes.",
        "The gods added this to their highlight reel.",
        "Time briefly considered flowing backward just to watch again.",
        "The cosmic janitor had to clean up the epic aftermath.",
        "Fate itself asked for my autograph.",
        "The universe briefly questioned its own existence."
    ],
    "epic": [
        "Parallel versions of me in alternate realities high-fived simultaneously.",
        "The space-time continuum updated its status to 'it's complicated'.",
        "Quantum physicists somewhere felt a great disturbance.",
        "The simulation's admins had to restart several servers.",
        "Infinity briefly made eye contact with me. It looked away first."
    ],
    "legendary": [
        "The concept of 'possible' was permanently expanded.",
        "Several philosophical frameworks had to be rewritten.",
        "Mathematics added a new appendix because of this.",
        "The universe's FAQ section now includes a entry about me."
    ],
    "godlike": [
        "This is now taught in universe design courses across the multiverse.",
        "The cosmic code review team gave me a 'LGTM'.",
        "Reality's git log will forever contain this commit.",
        "I am now a constant in all mathematical equations.",
        "Focus levels achieved: undefined (in the best way)."
    ]
}


def get_diary_power_tier(power: int) -> str:
    """Get the diary tier name based on character power."""
    for tier_name, (min_power, max_power) in DIARY_POWER_TIERS.items():
        if min_power <= power <= max_power:
            return tier_name
    return "godlike" if power > 2000 else "pathetic"


def calculate_session_tier_boost(session_minutes: int) -> int:
    """
    Calculate tier boost chance based on session length.
    
    Character gear/power is the PRIMARY factor for diary tier.
    Longer sessions give a SMALL chance of a tier bump (+1 max).
    
    Returns:
        0 = no boost
        1 = one tier bump (rare reward for dedication)
    
    Chances:
    - Under 60 min: No boost chance
    - 60-89 min: 10% chance of +1 tier
    - 90-119 min: 20% chance of +1 tier
    - 120+ min: 35% chance of +1 tier (dedicated focus reward)
    """
    if session_minutes >= 120:
        return 1 if random.random() < 0.35 else 0
    elif session_minutes >= 90:
        return 1 if random.random() < 0.20 else 0
    elif session_minutes >= 60:
        return 1 if random.random() < 0.10 else 0
    return 0


def generate_diary_entry(power: int, session_minutes: int = 25, equipped_items: dict = None) -> dict:
    """
    Generate a hilarious diary entry based on character power level.
    
    Character gear/power is the PRIMARY factor - your progress matters most!
    Longer sessions (60+ min) give a small chance of a tier bump as a bonus.
    The diary entry includes the date, story, and context about the session.
    """
    base_tier = get_diary_power_tier(power)
    available_tiers = list(DIARY_POWER_TIERS.keys())
    base_tier_index = available_tiers.index(base_tier)
    
    # Apply session length boost!
    session_boost = calculate_session_tier_boost(session_minutes)
    boosted_index = min(base_tier_index + session_boost, len(available_tiers) - 1)
    tier = available_tiers[boosted_index]
    
    # Track if we got a boost for display
    tier_was_boosted = boosted_index > base_tier_index
    
    # For maximum variety, occasionally pull from adjacent tiers too
    adjacent_chance = random.random()
    tier_index = available_tiers.index(tier)
    
    # 15% chance to pull a verb/outcome from one tier higher (if possible)
    # This makes occasional epic moments even at lower power
    verb_tier = tier
    if adjacent_chance < 0.15 and tier_index < len(available_tiers) - 1:
        verb_tier = available_tiers[tier_index + 1]
    
    # Build the story
    verb = random.choice(DIARY_VERBS[verb_tier])
    adjective = random.choice(DIARY_ADJECTIVES[tier])
    target = random.choice(DIARY_TARGETS[tier])
    location = random.choice(DIARY_LOCATIONS[tier])
    outcome = random.choice(DIARY_OUTCOMES[tier])
    flavor = random.choice(DIARY_FLAVOR[tier])
    
    # Create the main story sentence
    story = f"Today I {verb} {adjective} {target} {location} and it ended in {outcome}."
    
    # Add equipped item flavor if available
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
                f"Even the {item_name} seemed surprised.",
                f"The power of my {item_name} was barely contained.",
                f"My {item_name} will never be the same.",
                f"Witnesses say my {item_name} was particularly magnificent today.",
            ]
            item_mention = random.choice(item_templates)
    
    # Combine everything
    full_entry = f"{story} {flavor}"
    if item_mention:
        full_entry += f" {item_mention}"
    
    # Create entry object
    entry = {
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
    
    return entry


def calculate_rarity_bonuses(session_minutes: int = 0, streak_days: int = 0) -> dict:
    """
    Calculate rarity weight adjustments based on session length and streak.
    
    Session bonuses (cumulative):
    - 15+ min: +5% better rarity
    - 30+ min: +10% better rarity  
    - 60+ min: +20% better rarity
    - 90+ min: +35% better rarity
    - 120+ min: +50% better rarity
    
    Streak bonuses (cumulative):
    - 3+ days: +5% better rarity
    - 7+ days: +15% better rarity (1 week warrior)
    - 14+ days: +25% better rarity
    - 30+ days: +40% better rarity (monthly master)
    - 60+ days: +60% better rarity (dedication legend)
    """
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
    # Choose rarity based on weights if not specified
    if rarity is None:
        # Get base weights
        rarities = list(ITEM_RARITIES.keys())
        base_weights = [ITEM_RARITIES[r]["weight"] for r in rarities]
        
        # Apply bonuses - reduce Common weight and increase rare weights
        bonuses = calculate_rarity_bonuses(session_minutes, streak_days)
        total_bonus = bonuses["total_bonus"]
        
        if total_bonus > 0:
            # Shift weight from Common to higher rarities
            weights = base_weights.copy()
            # Reduce Common weight
            shift_amount = min(weights[0] * (total_bonus / 100), weights[0] * 0.7)
            weights[0] -= shift_amount
            
            # Distribute to higher rarities (more to rare/epic/legendary)
            weights[1] += shift_amount * 0.25  # Uncommon
            weights[2] += shift_amount * 0.35  # Rare
            weights[3] += shift_amount * 0.25  # Epic
            weights[4] += shift_amount * 0.15  # Legendary
        else:
            weights = base_weights
        
        rarity = random.choices(rarities, weights=weights)[0]
    
    # Pick random slot and item type
    slot = random.choice(list(ITEM_SLOTS.keys()))
    item_type = random.choice(ITEM_SLOTS[slot])
    
    # Generate name: "[Adjective] [Item Type] of [Suffix]"
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
    
    # Add set bonuses
    if include_set_bonus:
        set_info = calculate_set_bonuses(equipped)
        total_power += set_info["total_bonus"]
    
    return total_power


def get_power_breakdown(adhd_buster: dict) -> dict:
    """Get detailed breakdown of character power."""
    equipped = adhd_buster.get("equipped", {})
    
    # Base power from items
    base_power = 0
    for item in equipped.values():
        if item:
            base_power += item.get("power", RARITY_POWER.get(item.get("rarity", "Common"), 10))
    
    # Set bonuses
    set_info = calculate_set_bonuses(equipped)
    
    return {
        "base_power": base_power,
        "set_bonus": set_info["total_bonus"],
        "active_sets": set_info["active_sets"],
        "total_power": base_power + set_info["total_bonus"]
    }


class CharacterCanvas:
    """Canvas-based visual character with equipped gear display."""
    
    # Slot positions relative to character center (x_offset, y_offset)
    SLOT_POSITIONS = {
        "Helmet": (0, -85),
        "Amulet": (0, -50),
        "Chestplate": (0, -20),
        "Cloak": (45, -20),
        "Weapon": (-55, 10),
        "Shield": (55, 10),
        "Gauntlets": (-40, 30),
        "Boots": (0, 80),
    }
    
    # Tier-based body colors
    TIER_COLORS = {
        "pathetic": "#bdbdbd",    # Gray
        "modest": "#a5d6a7",      # Light green
        "decent": "#81c784",      # Green
        "heroic": "#64b5f6",      # Blue
        "epic": "#ba68c8",        # Purple
        "legendary": "#ffb74d",   # Orange
        "godlike": "#ffd54f",     # Gold
    }
    
    # Tier-based glow colors
    TIER_GLOW = {
        "pathetic": None,
        "modest": None,
        "decent": "#c8e6c9",
        "heroic": "#bbdefb",
        "epic": "#e1bee7",
        "legendary": "#ffe0b2",
        "godlike": "#fff9c4",
    }
    
    def __init__(self, parent, equipped: dict, power: int, width: int = 180, height: int = 200):
        self.parent = parent
        self.equipped = equipped
        self.power = power
        self.width = width
        self.height = height
        self.tier = get_diary_power_tier(power)
        
        self.canvas = tk.Canvas(parent, width=width, height=height, 
                                bg='#2d2d2d', highlightthickness=2,
                                highlightbackground='#444')
        
        self.draw_character()
    
    def draw_character(self):
        """Draw the character with equipped gear."""
        cx, cy = self.width // 2, self.height // 2 + 10
        
        body_color = self.TIER_COLORS.get(self.tier, "#bdbdbd")
        glow_color = self.TIER_GLOW.get(self.tier)
        
        # Draw tier glow effect for higher tiers
        if glow_color:
            # Outer glow
            self.canvas.create_oval(cx - 60, cy - 70, cx + 60, cy + 90,
                                   fill=glow_color, outline='', stipple='gray50')
        
        # Draw body parts (back to front layering)
        
        # Cloak (behind body)
        cloak = self.equipped.get("Cloak")
        if cloak:
            cloak_color = cloak.get("color", "#666")
            # Cape shape
            self.canvas.create_polygon(
                cx - 25, cy - 30,  # Left shoulder
                cx + 25, cy - 30,  # Right shoulder
                cx + 35, cy + 60,  # Right bottom
                cx - 35, cy + 60,  # Left bottom
                fill=cloak_color, outline=self._darken(cloak_color), width=2
            )
        
        # Legs
        self.canvas.create_rectangle(cx - 15, cy + 25, cx - 5, cy + 65,
                                     fill=body_color, outline=self._darken(body_color), width=2)
        self.canvas.create_rectangle(cx + 5, cy + 25, cx + 15, cy + 65,
                                     fill=body_color, outline=self._darken(body_color), width=2)
        
        # Boots
        boots = self.equipped.get("Boots")
        if boots:
            boots_color = boots.get("color", "#666")
            self.canvas.create_rectangle(cx - 18, cy + 55, cx - 2, cy + 75,
                                        fill=boots_color, outline=self._darken(boots_color), width=2)
            self.canvas.create_rectangle(cx + 2, cy + 55, cx + 18, cy + 75,
                                        fill=boots_color, outline=self._darken(boots_color), width=2)
        else:
            # Default feet
            self.canvas.create_rectangle(cx - 16, cy + 60, cx - 4, cy + 72,
                                        fill='#8d6e63', outline='#5d4037', width=1)
            self.canvas.create_rectangle(cx + 4, cy + 60, cx + 16, cy + 72,
                                        fill='#8d6e63', outline='#5d4037', width=1)
        
        # Arms
        self.canvas.create_rectangle(cx - 38, cy - 25, cx - 25, cy + 20,
                                     fill=body_color, outline=self._darken(body_color), width=2)
        self.canvas.create_rectangle(cx + 25, cy - 25, cx + 38, cy + 20,
                                     fill=body_color, outline=self._darken(body_color), width=2)
        
        # Gauntlets
        gauntlets = self.equipped.get("Gauntlets")
        if gauntlets:
            gaunt_color = gauntlets.get("color", "#666")
            self.canvas.create_rectangle(cx - 40, cy + 5, cx - 23, cy + 25,
                                        fill=gaunt_color, outline=self._darken(gaunt_color), width=2)
            self.canvas.create_rectangle(cx + 23, cy + 5, cx + 40, cy + 25,
                                        fill=gaunt_color, outline=self._darken(gaunt_color), width=2)
        
        # Torso (body)
        self.canvas.create_rectangle(cx - 25, cy - 30, cx + 25, cy + 30,
                                     fill=body_color, outline=self._darken(body_color), width=2)
        
        # Chestplate
        chestplate = self.equipped.get("Chestplate")
        if chestplate:
            chest_color = chestplate.get("color", "#666")
            self.canvas.create_rectangle(cx - 22, cy - 28, cx + 22, cy + 25,
                                        fill=chest_color, outline=self._darken(chest_color), width=2)
            # Chest detail
            self.canvas.create_line(cx, cy - 25, cx, cy + 20, fill=self._darken(chest_color), width=2)
        
        # Head
        self.canvas.create_oval(cx - 18, cy - 65, cx + 18, cy - 30,
                               fill='#ffcc80', outline='#e6a84d', width=2)
        
        # Face
        self.canvas.create_oval(cx - 8, cy - 55, cx - 3, cy - 48, fill='#333')  # Left eye
        self.canvas.create_oval(cx + 3, cy - 55, cx + 8, cy - 48, fill='#333')  # Right eye
        # Smile based on tier
        if self.tier in ['legendary', 'godlike']:
            self.canvas.create_arc(cx - 8, cy - 48, cx + 8, cy - 38,
                                  start=200, extent=140, style=tk.ARC, width=2)
        else:
            self.canvas.create_line(cx - 6, cy - 42, cx + 6, cy - 42, fill='#333', width=2)
        
        # Helmet
        helmet = self.equipped.get("Helmet")
        if helmet:
            helm_color = helmet.get("color", "#666")
            self.canvas.create_arc(cx - 20, cy - 75, cx + 20, cy - 45,
                                  start=0, extent=180, fill=helm_color,
                                  outline=self._darken(helm_color), width=2)
            self.canvas.create_rectangle(cx - 20, cy - 60, cx + 20, cy - 50,
                                        fill=helm_color, outline=self._darken(helm_color), width=2)
        
        # Amulet
        amulet = self.equipped.get("Amulet")
        if amulet:
            amulet_color = amulet.get("color", "#666")
            # Chain
            self.canvas.create_line(cx - 10, cy - 30, cx, cy - 20, fill='#888', width=1)
            self.canvas.create_line(cx + 10, cy - 30, cx, cy - 20, fill='#888', width=1)
            # Gem
            self.canvas.create_oval(cx - 6, cy - 25, cx + 6, cy - 13,
                                   fill=amulet_color, outline=self._darken(amulet_color), width=2)
        
        # Weapon (left hand)
        weapon = self.equipped.get("Weapon")
        if weapon:
            weap_color = weapon.get("color", "#666")
            # Sword/weapon handle
            self.canvas.create_rectangle(cx - 52, cy - 5, cx - 48, cy + 35,
                                        fill='#5d4037', outline='#3e2723', width=1)
            # Blade
            self.canvas.create_polygon(
                cx - 55, cy - 5,
                cx - 45, cy - 5,
                cx - 47, cy - 45,
                cx - 53, cy - 45,
                fill=weap_color, outline=self._darken(weap_color), width=2
            )
        
        # Shield (right hand)
        shield = self.equipped.get("Shield")
        if shield:
            shield_color = shield.get("color", "#666")
            self.canvas.create_oval(cx + 35, cy - 15, cx + 65, cy + 25,
                                   fill=shield_color, outline=self._darken(shield_color), width=3)
            # Shield emblem
            self.canvas.create_oval(cx + 45, cy - 2, cx + 55, cy + 12,
                                   fill=self._darken(shield_color), outline='')
        
        # Power level indicator at bottom
        self.canvas.create_text(cx, self.height - 10,
                               text=f"⚔ {self.power}",
                               font=('Segoe UI', 10, 'bold'),
                               fill='#ffd700' if self.tier in ['legendary', 'godlike'] else '#fff')
    
    def _darken(self, hex_color: str) -> str:
        """Darken a hex color for outlines."""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            r, g, b = max(0, r - 40), max(0, g - 40), max(0, b - 40)
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return '#333333'
    
    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.canvas.grid(**kwargs)


class ADHDBusterDialog:
    """Dialog to view and manage the ADHD Buster character and inventory."""
    
    def __init__(self, parent: tk.Tk, blocker):
        self.parent = parent
        self.blocker = blocker
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🦸 ADHD Buster - Character & Inventory")
        self.dialog.geometry("750x850")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        
        # Center on screen
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (750 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (850 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Track slot dropdown variables
        self.slot_vars = {}
        self.merge_selected = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the ADHD Buster dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Character Header with Power Level
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="🦸 ADHD Buster",
                  font=('Segoe UI', 18, 'bold')).pack(side=tk.LEFT)
        
        # Power level calculation with breakdown
        power_info = get_power_breakdown(self.blocker.adhd_buster)
        power = power_info["total_power"]
        max_power = 8 * RARITY_POWER["Legendary"]  # 2000
        power_pct = int((power / max_power) * 100)
        
        # Power level title based on score
        if power >= 1500:
            title = "🌟 Focus Deity"
        elif power >= 1000:
            title = "⚡ Legendary Champion"
        elif power >= 600:
            title = "🔥 Epic Warrior"
        elif power >= 300:
            title = "💪 Seasoned Fighter"
        elif power >= 100:
            title = "🛡️ Apprentice"
        else:
            title = "🌱 Novice"
        
        power_frame = ttk.Frame(header_frame)
        power_frame.pack(side=tk.RIGHT)
        
        # Show base power and set bonus separately
        if power_info["set_bonus"] > 0:
            power_text = f"⚔ Power: {power} ({power_info['base_power']} + {power_info['set_bonus']} set)"
        else:
            power_text = f"⚔ Power: {power}"
        tk.Label(power_frame, text=power_text, 
                 font=('Segoe UI', 12, 'bold'), fg='#e65100').pack(side=tk.TOP)
        ttk.Label(power_frame, text=title,
                  font=('Segoe UI', 9)).pack(side=tk.TOP)
        
        # Set Bonuses Display (if any active)
        if power_info["active_sets"]:
            set_frame = ttk.LabelFrame(main_frame, text="🎯 Active Set Bonuses", padding="5")
            set_frame.pack(fill=tk.X, pady=(0, 10))
            
            for set_info in power_info["active_sets"]:
                set_text = f"{set_info['emoji']} {set_info['name']} ({set_info['count']} items): +{set_info['bonus']} power"
                tk.Label(set_frame, text=set_text, font=('Segoe UI', 9, 'bold'),
                        fg='#4caf50').pack(anchor=tk.W)
        
        # Stats summary
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        total_items = len(self.blocker.adhd_buster.get("inventory", []))
        total_collected = self.blocker.adhd_buster.get("total_collected", total_items)
        streak = self.blocker.stats.get("streak_days", 0)
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        
        stats_text = f"📦 {total_items} in bag  |  🎁 {total_collected} collected  |  🔥 {streak} day streak  |  🍀 {luck} luck"
        ttk.Label(stats_frame, text=stats_text, font=('Segoe UI', 9), 
                  foreground='gray').pack(anchor=tk.W)
        
        # Streak and session bonus info
        bonuses = calculate_rarity_bonuses(60, streak)  # Assume 60 min for display
        if bonuses["streak_bonus"] > 0:
            bonus_text = f"✨ Streak bonus active: +{bonuses['streak_bonus']}% better loot!"
            ttk.Label(stats_frame, text=bonus_text, font=('Segoe UI', 9, 'bold'),
                      foreground='#4caf50').pack(anchor=tk.W)
        
        # Character visualization and equipment side by side
        char_equip_frame = ttk.Frame(main_frame)
        char_equip_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Left: Character Canvas
        equipped = self.blocker.adhd_buster.get("equipped", {})
        char_canvas = CharacterCanvas(char_equip_frame, equipped, power, width=180, height=200)
        char_canvas.pack(side=tk.LEFT, padx=(0, 15))
        
        # Right: Equipment with dropdown selection
        equip_frame = ttk.LabelFrame(char_equip_frame, text="⚔ Equipped Gear (click dropdown to change)", padding="10")
        equip_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        slots = ["Helmet", "Chestplate", "Gauntlets", "Boots", "Shield", "Weapon", "Cloak", "Amulet"]
        inventory = self.blocker.adhd_buster.get("inventory", [])
        
        # Build dropdown options for each slot
        for slot in slots:
            slot_frame = ttk.Frame(equip_frame)
            slot_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(slot_frame, text=f"{slot}:", width=10).pack(side=tk.LEFT)
            
            # Get items available for this slot
            slot_items = [item for item in inventory if item.get("slot") == slot]
            current_item = equipped.get(slot)
            
            # Build options list: [Empty] + all items for this slot
            options = ["[Empty]"]
            item_map = {}  # Map display name to item
            
            for item in slot_items:
                display = f"{item['name']} (+{item.get('power', 10)}) [{item['rarity'][:1]}]"
                options.append(display)
                item_map[display] = item
            
            # Create dropdown
            var = tk.StringVar()
            if current_item:
                current_display = f"{current_item['name']} (+{current_item.get('power', 10)}) [{current_item['rarity'][:1]}]"
                var.set(current_display)
            else:
                var.set("[Empty]")
            
            self.slot_vars[slot] = {"var": var, "item_map": item_map}
            
            dropdown = ttk.Combobox(slot_frame, textvariable=var, values=options,
                                    state="readonly", width=45)
            dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True)
            dropdown.bind("<<ComboboxSelected>>", lambda e, s=slot: self.on_equip_change(s))
        
        # Lucky Merge Section
        merge_frame = ttk.LabelFrame(main_frame, text="🎲 Lucky Merge (High Risk, High Reward!)", padding="10")
        merge_frame.pack(fill=tk.X, pady=(10, 5))
        
        merge_info = ttk.Frame(merge_frame)
        merge_info.pack(fill=tk.X)
        
        ttk.Label(merge_info, text="Select 2+ items below, then merge for a CHANCE at better loot!",
                  font=('Segoe UI', 9)).pack(side=tk.LEFT)
        ttk.Label(merge_info, text="⚠️ 90% failure = ALL items lost!",
                  font=('Segoe UI', 9, 'bold'), foreground='#d32f2f').pack(side=tk.RIGHT)
        
        self.merge_btn = ttk.Button(merge_frame, text="🎲 Merge Selected (0)", 
                                    command=self.do_lucky_merge, state=tk.DISABLED)
        self.merge_btn.pack(pady=5)
        
        self.merge_rate_label = ttk.Label(merge_frame, text="Success rate: 10%",
                                          font=('Segoe UI', 9))
        self.merge_rate_label.pack()
        
        # Inventory section with sorting and checkboxes for merge
        inv_header = ttk.Frame(main_frame)
        inv_header.pack(fill=tk.X, pady=(10, 5))
        ttk.Label(inv_header, text="📦 Inventory",
                  font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        
        # Sort options
        ttk.Label(inv_header, text="Sort:", font=('Segoe UI', 9)).pack(side=tk.RIGHT, padx=(10, 5))
        self.sort_var = tk.StringVar(value="newest")
        sort_combo = ttk.Combobox(inv_header, textvariable=self.sort_var, 
                                   values=["newest", "rarity", "slot", "power"], 
                                   width=8, state="readonly")
        sort_combo.pack(side=tk.RIGHT)
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_inventory())
        
        # Inventory list with scrollbar
        inv_container = ttk.Frame(main_frame)
        inv_container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with scrollbar for inventory
        self.canvas = tk.Canvas(inv_container, height=250)
        scrollbar = ttk.Scrollbar(inv_container, orient="vertical", command=self.canvas.yview)
        self.inv_frame = ttk.Frame(self.canvas)
        
        self.inv_frame.bind("<Configure>", 
                            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.inv_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Unbind mousewheel when dialog closes
        self.dialog.bind("<Destroy>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        
        # Populate inventory
        self.refresh_inventory()
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(btn_frame, text="� Adventure Diary", 
                   command=self.open_diary).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Salvage Duplicates", 
                   command=self.salvage_duplicates).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close",
                   command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def on_equip_change(self, slot: str):
        """Handle equipment change from dropdown."""
        slot_data = self.slot_vars.get(slot)
        if not slot_data:
            return
        
        selected = slot_data["var"].get()
        
        if "equipped" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["equipped"] = {}
        
        if selected == "[Empty]":
            # Unequip
            self.blocker.adhd_buster["equipped"][slot] = None
        else:
            # Equip the selected item
            item = slot_data["item_map"].get(selected)
            if item:
                self.blocker.adhd_buster["equipped"][slot] = item
        
        self.blocker.save_config()
        
        # Refresh dialog to show new power/set bonuses
        self.dialog.destroy()
        ADHDBusterDialog(self.parent, self.blocker)
    
    def update_merge_ui(self):
        """Update merge button and rate based on selected items."""
        count = len(self.merge_selected)
        self.merge_btn.config(text=f"🎲 Merge Selected ({count})")
        
        if count >= 2:
            # Calculate success rate
            inventory = self.blocker.adhd_buster.get("inventory", [])
            items = [inventory[idx] for idx in self.merge_selected 
                     if idx < len(inventory)]
            
            # Check if merge is worthwhile
            worthwhile, reason = is_merge_worthwhile(items)
            
            if not worthwhile:
                self.merge_btn.config(state=tk.DISABLED)
                self.merge_rate_label.config(text=f"⚠️ {reason}")
                return
            
            self.merge_btn.config(state=tk.NORMAL)
            luck = self.blocker.adhd_buster.get("luck_bonus", 0)
            rate = calculate_merge_success_rate(items, luck)
            result_rarity = get_merge_result_rarity(items) if items else "Unknown"
            self.merge_rate_label.config(
                text=f"Success rate: {rate*100:.0f}% → {result_rarity} item"
            )
        else:
            self.merge_btn.config(state=tk.DISABLED)
            self.merge_rate_label.config(text="Select 2+ items to merge")
    
    def toggle_merge_item(self, idx: int, var: tk.BooleanVar):
        """Toggle an item's selection for merge."""
        if var.get():
            if idx not in self.merge_selected:
                self.merge_selected.append(idx)
        else:
            if idx in self.merge_selected:
                self.merge_selected.remove(idx)
        self.update_merge_ui()
    
    def do_lucky_merge(self):
        """Perform a lucky merge of selected items."""
        if len(self.merge_selected) < 2:
            messagebox.showwarning("Merge", "Select at least 2 items to merge!", parent=self.dialog)
            return
        
        inventory = self.blocker.adhd_buster.get("inventory", [])
        items_to_merge = [inventory[idx] for idx in self.merge_selected if idx < len(inventory)]
        
        if len(items_to_merge) < 2:
            return
        
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        rate = calculate_merge_success_rate(items_to_merge, luck)
        result_rarity = get_merge_result_rarity(items_to_merge)
        
        # Confirm the risky merge
        item_summary = "\n".join([f"  • {item['name']} ({item['rarity']})" for item in items_to_merge])
        if not messagebox.askyesno("⚠️ Lucky Merge - HIGH RISK!",
                                   f"Merge {len(items_to_merge)} items?\n\n"
                                   f"{item_summary}\n\n"
                                   f"Success rate: {rate*100:.0f}%\n"
                                   f"On success: Get one {result_rarity} item\n"
                                   f"On failure: ALL {len(items_to_merge)} items LOST!\n\n"
                                   f"Are you sure?",
                                   parent=self.dialog):
            return
        
        # Perform the merge!
        result = perform_lucky_merge(items_to_merge, luck)
        
        # Remove merged items from inventory (sorted in reverse to not mess up indices)
        for idx in sorted(self.merge_selected, reverse=True):
            if idx < len(inventory):
                del inventory[idx]
        
        if result["success"]:
            # Add the new item!
            inventory.append(result["result_item"])
            self.blocker.adhd_buster["inventory"] = inventory
            self.blocker.save_config()
            
            messagebox.showinfo("🎉 MERGE SUCCESS!",
                               f"The stars aligned!\n\n"
                               f"Roll: {result['roll_pct']} (needed < {result['needed_pct']})\n\n"
                               f"You created:\n"
                               f"✨ {result['result_item']['name']} ✨\n"
                               f"Rarity: {result['result_item']['rarity']}\n"
                               f"Power: +{result['result_item']['power']}",
                               parent=self.dialog)
        else:
            # Items lost!
            self.blocker.adhd_buster["inventory"] = inventory
            self.blocker.save_config()
            
            messagebox.showerror("💔 Merge Failed!",
                                f"The merge went horribly wrong!\n\n"
                                f"Roll: {result['roll_pct']} (needed < {result['needed_pct']})\n\n"
                                f"{len(items_to_merge)} items have been lost forever.\n"
                                f"Better luck next time, adventurer...",
                                parent=self.dialog)
        
        # Refresh dialog
        self.dialog.destroy()
        ADHDBusterDialog(self.parent, self.blocker)
    
    def open_diary(self):
        """Open the adventure diary dialog."""
        self.dialog.destroy()
        DiaryDialog(self.parent, self.blocker)
    
    def refresh_inventory(self):
        """Refresh the inventory display with current sorting and merge checkboxes."""
        # Clear existing items and merge selection
        for widget in self.inv_frame.winfo_children():
            widget.destroy()
        self.merge_selected = []
        self.update_merge_ui()
        
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        equipped_names = {item["name"] for item in equipped.values() if item}
        
        if not inventory:
            ttk.Label(self.inv_frame, 
                      text="No items yet! Stay focused during sessions to earn loot! 🎁",
                      foreground='gray').pack(pady=20)
            return
        
        # Sort inventory
        sort_key = self.sort_var.get()
        rarity_order = {"Common": 0, "Uncommon": 1, "Rare": 2, "Epic": 3, "Legendary": 4}
        
        if sort_key == "rarity":
            sorted_inv = sorted(enumerate(inventory), 
                               key=lambda x: rarity_order.get(x[1].get("rarity", "Common"), 0),
                               reverse=True)
        elif sort_key == "slot":
            sorted_inv = sorted(enumerate(inventory), key=lambda x: x[1].get("slot", ""))
        elif sort_key == "power":
            sorted_inv = sorted(enumerate(inventory), 
                               key=lambda x: x[1].get("power", 10), reverse=True)
        else:  # newest
            sorted_inv = list(reversed(list(enumerate(inventory))))
        
        # Store checkbox vars
        self.merge_vars = {}
        
        for orig_idx, item in sorted_inv:
            item_frame = ttk.Frame(self.inv_frame)
            item_frame.pack(fill=tk.X, pady=2)
            
            # Merge checkbox (not for equipped items)
            is_equipped = item["name"] in equipped_names
            
            if not is_equipped:
                merge_var = tk.BooleanVar(value=False)
                self.merge_vars[orig_idx] = merge_var
                cb = ttk.Checkbutton(item_frame, variable=merge_var,
                                    command=lambda idx=orig_idx, v=merge_var: self.toggle_merge_item(idx, v))
                cb.pack(side=tk.LEFT)
            else:
                # Placeholder for alignment
                ttk.Label(item_frame, text="  ", width=2).pack(side=tk.LEFT)
            
            # Item name with rarity color
            name_text = f"{'✓ ' if is_equipped else ''}{item['name']}"
            power_val = item.get("power", RARITY_POWER.get(item.get("rarity", "Common"), 10))
            
            # Show theme indicators
            themes = get_item_themes(item)
            if themes:
                theme_emojis = " ".join([ITEM_THEMES[t]["emoji"] for t in themes[:2]])  # Max 2 emojis
                name_text = f"{name_text} {theme_emojis}"
            
            item_label = tk.Label(item_frame, text=name_text,
                                 font=('Segoe UI', 9), fg=item.get("color", "#333"),
                                 anchor='w', width=42)
            item_label.pack(side=tk.LEFT)
            
            # Power and rarity
            info_text = f"+{power_val} [{item['rarity'][:1]}]"
            tk.Label(item_frame, text=info_text,
                    font=('Segoe UI', 8), fg=item.get("color", "#333")).pack(side=tk.LEFT, padx=5)
    
    def equip_item(self, inv_index: int):
        """Equip an item from inventory."""
        inventory = self.blocker.adhd_buster.get("inventory", [])
        if inv_index >= len(inventory):
            return
        
        item = inventory[inv_index]
        slot = item["slot"]
        
        # Equip the item
        if "equipped" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["equipped"] = {}
        
        self.blocker.adhd_buster["equipped"][slot] = item
        self.blocker.save_config()
        
        # Refresh dialog
        self.dialog.destroy()
        ADHDBusterDialog(self.parent, self.blocker)
    
    def salvage_duplicates(self):
        """Salvage duplicate items (keep best of each slot) for bonus luck."""
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        if not inventory:
            messagebox.showinfo("Salvage", "No items to salvage!", parent=self.dialog)
            return
        
        # Find duplicates by slot - keep the best (highest power) non-equipped item per slot
        slot_items = {}
        equipped_names = {item["name"] for item in equipped.values() if item}
        
        for item in inventory:
            slot = item.get("slot", "Unknown")
            power = item.get("power", 10)
            is_equipped = item["name"] in equipped_names
            
            if slot not in slot_items:
                slot_items[slot] = {"best": None, "duplicates": []}
            
            if is_equipped:
                # Equipped items are always kept
                continue
            elif slot_items[slot]["best"] is None:
                slot_items[slot]["best"] = item
            elif power > slot_items[slot]["best"].get("power", 10):
                slot_items[slot]["duplicates"].append(slot_items[slot]["best"])
                slot_items[slot]["best"] = item
            else:
                slot_items[slot]["duplicates"].append(item)
        
        # Count duplicates to remove
        to_remove = []
        for slot_data in slot_items.values():
            to_remove.extend(slot_data["duplicates"])
        
        if not to_remove:
            messagebox.showinfo("Salvage", "No duplicates found!\n\nKeep the best item of each slot type.", 
                               parent=self.dialog)
            return
        
        # Check if any items to remove have themes (set bonus warning)
        themed_items = [item for item in to_remove if get_item_themes(item)]
        theme_warning = ""
        if themed_items:
            theme_warning = f"\n\n⚠️ {len(themed_items)} items have set themes - salvaging may affect set bonuses!"
        
        # Calculate luck bonus from salvaged items
        luck_bonus = sum(item.get("power", 10) // 10 for item in to_remove)
        
        # Confirm salvage
        rarity_counts = {}
        for item in to_remove:
            r = item.get("rarity", "Common")
            rarity_counts[r] = rarity_counts.get(r, 0) + 1
        
        summary = ", ".join([f"{c} {r}" for r, c in rarity_counts.items()])
        
        if messagebox.askyesno("Salvage Duplicates",
                               f"Salvage {len(to_remove)} duplicate items?\n\n"
                               f"Items: {summary}\n"
                               f"Luck bonus earned: +{luck_bonus} 🍀{theme_warning}\n\n"
                               "(Best item of each slot type will be kept)",
                               parent=self.dialog):
            # Remove duplicates
            for item in to_remove:
                if item in inventory:
                    inventory.remove(item)
            
            # Add luck bonus
            current_luck = self.blocker.adhd_buster.get("luck_bonus", 0)
            self.blocker.adhd_buster["luck_bonus"] = current_luck + luck_bonus
            self.blocker.adhd_buster["inventory"] = inventory
            self.blocker.save_config()
            
            messagebox.showinfo("Salvage Complete!",
                               f"✨ Salvaged {len(to_remove)} items!\n"
                               f"🍀 Total luck bonus: +{current_luck + luck_bonus}",
                               parent=self.dialog)
            
            # Refresh dialog
            self.dialog.destroy()
            ADHDBusterDialog(self.parent, self.blocker)


class DiaryDialog:
    """Dialog to view the ADHD Buster's adventure diary."""
    
    def __init__(self, parent: tk.Tk, blocker):
        self.parent = parent
        self.blocker = blocker
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📖 Adventure Diary")
        self.dialog.geometry("650x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        
        # Center on screen
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the diary UI."""
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="📖 The Adventures of ADHD Buster",
                  font=('Segoe UI', 16, 'bold')).pack(side=tk.LEFT)
        
        # Current power and tier
        power = calculate_character_power(self.blocker.adhd_buster)
        tier = get_diary_power_tier(power)
        tier_display = tier.capitalize()
        
        tier_colors = {
            "pathetic": "#9e9e9e",
            "modest": "#8bc34a",
            "decent": "#4caf50",
            "heroic": "#2196f3",
            "epic": "#9c27b0",
            "legendary": "#ff9800",
            "godlike": "#ffd700"
        }
        
        power_label = tk.Label(header_frame, text=f"⚔ Power: {power} ({tier_display} Tier)",
                               font=('Segoe UI', 10, 'bold'), 
                               fg=tier_colors.get(tier, "#333"))
        power_label.pack(side=tk.RIGHT)
        
        # Diary entries
        entries = self.blocker.adhd_buster.get("diary", [])
        
        # Stats summary
        if entries:
            stats_text = f"📚 {len(entries)} adventures recorded | 🗓️ Latest: {entries[-1].get('short_date', 'Unknown')}"
            ttk.Label(main_frame, text=stats_text, font=('Segoe UI', 9),
                      foreground='gray').pack(anchor=tk.W, pady=(0, 10))
        
        # Scrollable diary area
        diary_container = ttk.Frame(main_frame)
        diary_container.pack(fill=tk.BOTH, expand=True)
        
        # Create text widget with scrollbar for diary entries
        text_frame = ttk.Frame(diary_container)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.diary_text = tk.Text(text_frame, wrap=tk.WORD, font=('Georgia', 11),
                                   padx=15, pady=10, spacing2=5, spacing3=10)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", 
                                   command=self.diary_text.yview)
        self.diary_text.configure(yscrollcommand=scrollbar.set)
        
        self.diary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure text tags for styling
        self.diary_text.tag_configure("date", font=('Segoe UI', 10, 'bold'), 
                                       foreground='#1976d2')
        self.diary_text.tag_configure("tier_pathetic", foreground='#9e9e9e')
        self.diary_text.tag_configure("tier_modest", foreground='#8bc34a')
        self.diary_text.tag_configure("tier_decent", foreground='#4caf50')
        self.diary_text.tag_configure("tier_heroic", foreground='#2196f3')
        self.diary_text.tag_configure("tier_epic", foreground='#9c27b0')
        self.diary_text.tag_configure("tier_legendary", foreground='#ff9800')
        self.diary_text.tag_configure("tier_godlike", foreground='#b8860b', 
                                       font=('Georgia', 11, 'bold italic'))
        self.diary_text.tag_configure("story", foreground='#333')
        self.diary_text.tag_configure("power_info", font=('Segoe UI', 9), 
                                       foreground='#888')
        
        # Populate diary entries (newest first)
        if entries:
            for entry in reversed(entries):
                self._add_entry_to_text(entry)
        else:
            self.diary_text.insert(tk.END, "\n\n")
            self.diary_text.insert(tk.END, "📭 No adventures recorded yet!\n\n", "date")
            self.diary_text.insert(tk.END, 
                "Complete focus sessions and confirm you stayed on task "
                "to record your epic adventures.\n\n"
                "Each session adds a new chapter to your story. "
                "As your power grows, your adventures become more legendary!\n\n"
                "🌱 Novice → 🛡️ Apprentice → 💪 Fighter → 🔥 Warrior → "
                "⚡ Champion → 🌟 Focus Deity",
                "story")
        
        self.diary_text.configure(state=tk.DISABLED)  # Make read-only
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        if entries:
            ttk.Button(btn_frame, text="🗑️ Clear All Entries",
                       command=self.clear_diary).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="✍️ Write Today's Entry",
                   command=self.write_new_entry).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Close",
                   command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _add_entry_to_text(self, entry: dict):
        """Add a single diary entry to the text widget."""
        date = entry.get("short_date", entry.get("date", "Unknown Date"))
        story = entry.get("story", "A mysterious adventure occurred...")
        tier = entry.get("tier", "pathetic")
        power = entry.get("power_at_time", 0)
        minutes = entry.get("session_minutes", 0)
        
        # Tier emoji
        tier_emojis = {
            "pathetic": "🌱",
            "modest": "🛡️",
            "decent": "💪",
            "heroic": "🔥",
            "epic": "⚡",
            "legendary": "⭐",
            "godlike": "🌟"
        }
        emoji = tier_emojis.get(tier, "📖")
        
        # Insert date header
        self.diary_text.insert(tk.END, f"\n{emoji} {date}\n", "date")
        
        # Insert story with tier-specific styling
        tier_tag = f"tier_{tier}"
        self.diary_text.insert(tk.END, f"{story}\n", tier_tag)
        
        # Insert power info
        self.diary_text.insert(tk.END, 
            f"Power: {power} | Focus: {minutes} min | Tier: {tier.capitalize()}\n",
            "power_info")
        
        # Add separator
        self.diary_text.insert(tk.END, "─" * 60 + "\n", "power_info")
    
    def write_new_entry(self):
        """Manually write a new diary entry (bonus feature)."""
        power = calculate_character_power(self.blocker.adhd_buster)
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        # Generate entry
        entry = generate_diary_entry(power, session_minutes=0, equipped_items=equipped)
        entry["story"] = "[Bonus Entry] " + entry["story"]
        
        # Add to diary
        if "diary" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["diary"] = []
        
        self.blocker.adhd_buster["diary"].append(entry)
        self.blocker.save_config()
        
        # Refresh dialog
        self.dialog.destroy()
        DiaryDialog(self.parent, self.blocker)
    
    def clear_diary(self):
        """Clear all diary entries after confirmation."""
        if messagebox.askyesno("Clear Diary", 
                               "Are you sure you want to clear all diary entries?\n\n"
                               "This cannot be undone!",
                               parent=self.dialog):
            self.blocker.adhd_buster["diary"] = []
            self.blocker.save_config()
            
            # Refresh dialog
            self.dialog.destroy()
            DiaryDialog(self.parent, self.blocker)


class ItemDropDialog:
    """Dialog shown when an item drops (after confirming on-task)."""
    
    def __init__(self, parent: tk.Tk, blocker, item: dict, 
                 session_minutes: int = 0, streak_days: int = 0):
        self.parent = parent
        self.blocker = blocker
        self.item = item
        self.session_minutes = session_minutes
        self.streak_days = streak_days
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🎁 Item Drop!")
        self.dialog.geometry("400x280")
        self.dialog.resizable(False, False)
        self.dialog.overrideredirect(True)  # No decorations for dramatic effect
        
        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 280) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        
        # Auto-close time based on rarity (legendary gets more time to celebrate!)
        close_time = {"Common": 3000, "Uncommon": 3500, "Rare": 4000, 
                      "Epic": 5000, "Legendary": 6000}
        self.dialog.after(close_time.get(item["rarity"], 4000), self.dialog.destroy)
    
    def setup_ui(self):
        """Create the item drop UI."""
        # Background color based on rarity
        bg_colors = {
            "Common": "#f5f5f5", "Uncommon": "#e8f5e9", "Rare": "#e3f2fd",
            "Epic": "#f3e5f5", "Legendary": "#fff3e0"
        }
        bg = bg_colors.get(self.item["rarity"], "#f5f5f5")
        
        main_frame = tk.Frame(self.dialog, bg=bg, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header - special for lucky upgrades
        if self.item.get("lucky_upgrade"):
            header_text = "🍀 LUCKY UPGRADE! 🍀"
        elif self.item["rarity"] == "Legendary":
            header_text = "⭐ LEGENDARY DROP! ⭐"
        elif self.item["rarity"] == "Epic":
            header_text = "💎 EPIC DROP! 💎"
        else:
            header_text = "✨ LOOT DROP! ✨"
        
        tk.Label(main_frame, text=header_text, 
                 font=('Segoe UI', 14, 'bold'), bg=bg).pack()
        
        tk.Label(main_frame, text="Your ADHD Buster found:", 
                 font=('Segoe UI', 10), bg=bg).pack(pady=(5, 10))
        
        # Item name with rarity color
        item_frame = tk.Frame(main_frame, bg=bg)
        item_frame.pack(pady=5)
        
        tk.Label(item_frame, text=self.item["name"],
                 font=('Segoe UI', 12, 'bold'), 
                 fg=self.item["color"], bg=bg).pack()
        
        # Rarity and power
        power = self.item.get("power", RARITY_POWER.get(self.item["rarity"], 10))
        tk.Label(item_frame, text=f"[{self.item['rarity']} {self.item['slot']}] +{power} Power",
                 font=('Segoe UI', 9), 
                 fg=self.item["color"], bg=bg).pack()
        
        # Show what bonuses contributed
        bonuses = calculate_rarity_bonuses(self.session_minutes, self.streak_days)
        if bonuses["total_bonus"] > 0:
            bonus_parts = []
            if bonuses["session_bonus"] > 0:
                bonus_parts.append(f"⏱️{self.session_minutes}min")
            if bonuses["streak_bonus"] > 0:
                bonus_parts.append(f"🔥{self.streak_days}day streak")
            
            if bonus_parts:
                bonus_text = " + ".join(bonus_parts) + f" = +{bonuses['total_bonus']}% luck!"
                tk.Label(main_frame, text=bonus_text,
                         font=('Segoe UI', 8), bg=bg, fg='#ff9800').pack(pady=(5, 0))
        
        # Motivational message by rarity
        messages = {
            "Common": ["Every item counts! 💪", "Building your arsenal!", "Keep going! 🎯"],
            "Uncommon": ["Nice find! 🌟", "Your focus is paying off!", "Solid loot! 💚"],
            "Rare": ["Rare drop! You're on fire! 🔥", "The grind is real! 💙", "Sweet loot! ⚡"],
            "Epic": ["EPIC! Your dedication shows! 💜", "Incredible focus! 🌟", "Champion tier! 👑"],
            "Legendary": ["LEGENDARY! You are unstoppable! ⭐", "GODLIKE FOCUS! 🏆", 
                         "The myths are TRUE! 🌈", "TRANSCENDENT! 🔱"]
        }
        
        msg_list = messages.get(self.item["rarity"], messages["Common"])
        tk.Label(main_frame, text=random.choice(msg_list),
                 font=('Segoe UI', 10, 'bold'), bg=bg, fg='#666').pack(pady=(10, 5))
        
        # Hint about upcoming diary entry
        tk.Label(main_frame, text="📖 Your adventure awaits...",
                 font=('Segoe UI', 9, 'italic'), bg=bg, fg='#888').pack(pady=(5, 0))
        
        tk.Label(main_frame, text="(Click anywhere or wait to dismiss)",
                 font=('Segoe UI', 8), bg=bg, fg='#999').pack()
        
        # Click to dismiss
        self.dialog.bind("<Button-1>", lambda e: self.dialog.destroy())


class DiaryEntryRevealDialog:
    """
    Dramatic reveal dialog for the daily diary entry.
    Shows after item drop as a session reward.
    """
    
    def __init__(self, parent: tk.Tk, blocker, entry: dict, session_minutes: int = 0):
        self.parent = parent
        self.blocker = blocker
        self.entry = entry
        self.session_minutes = session_minutes
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📖 Today's Adventure")
        self.dialog.geometry("520x380")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        
        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 520) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 380) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        
        # Auto-close after reading time (based on story length)
        story_len = len(entry.get("story", ""))
        close_time = max(8000, min(15000, story_len * 50))  # 8-15 seconds
        self.dialog.after(close_time, self.dialog.destroy)
    
    def setup_ui(self):
        """Create the dramatic diary reveal UI."""
        tier = self.entry.get("tier", "pathetic")
        
        # Background and accent colors by tier
        tier_styles = {
            "pathetic": {"bg": "#fafafa", "accent": "#9e9e9e", "emoji": "🌱"},
            "modest": {"bg": "#f1f8e9", "accent": "#8bc34a", "emoji": "🛡️"},
            "decent": {"bg": "#e8f5e9", "accent": "#4caf50", "emoji": "💪"},
            "heroic": {"bg": "#e3f2fd", "accent": "#2196f3", "emoji": "🔥"},
            "epic": {"bg": "#f3e5f5", "accent": "#9c27b0", "emoji": "⚡"},
            "legendary": {"bg": "#fff3e0", "accent": "#ff9800", "emoji": "⭐"},
            "godlike": {"bg": "#fffde7", "accent": "#ffc107", "emoji": "🌟"}
        }
        
        style = tier_styles.get(tier, tier_styles["pathetic"])
        bg = style["bg"]
        accent = style["accent"]
        emoji = style["emoji"]
        
        main_frame = tk.Frame(self.dialog, bg=bg, padx=25, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with tier info
        header_frame = tk.Frame(main_frame, bg=bg)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Dynamic header based on tier boost (now more subtle)
        tier_boosted = self.entry.get("tier_boosted", False)
        
        if tier_boosted:
            header_text = f"{emoji} Lucky Adventure! {emoji}"
            subheader = f"Your {self.session_minutes}+ min focus earned a bonus tier!"
        else:
            header_text = f"{emoji} Today's Adventure {emoji}"
            subheader = self.entry.get("short_date", "")
        
        tk.Label(header_frame, text=header_text,
                 font=('Georgia', 16, 'bold'), bg=bg, fg=accent).pack()
        
        tk.Label(header_frame, text=subheader,
                 font=('Segoe UI', 10), bg=bg, fg='#666').pack()
        
        # Decorative line
        tk.Frame(main_frame, height=2, bg=accent).pack(fill=tk.X, pady=10)
        
        # The diary entry story
        story_frame = tk.Frame(main_frame, bg=bg)
        story_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        story = self.entry.get("story", "A mysterious adventure occurred...")
        
        story_label = tk.Label(story_frame, text=story,
                               font=('Georgia', 12), bg=bg, fg='#333',
                               wraplength=460, justify=tk.LEFT)
        story_label.pack(anchor=tk.W)
        
        # Decorative line
        tk.Frame(main_frame, height=2, bg=accent).pack(fill=tk.X, pady=10)
        
        # Footer with power/tier info
        footer_frame = tk.Frame(main_frame, bg=bg)
        footer_frame.pack(fill=tk.X)
        
        power = self.entry.get("power_at_time", 0)
        
        # Show equipped power and tier
        tier_display = tier.capitalize()
        if tier_boosted:
            base_tier = self.entry.get("base_tier", tier)
            power_text = f"⚔ Power: {power}  |  🎭 {base_tier.capitalize()} → {tier_display} (bonus!)"
        else:
            power_text = f"⚔ Power: {power}  |  🎭 {tier_display} Tier"
        
        tk.Label(footer_frame, text=power_text,
                 font=('Segoe UI', 10, 'bold'), bg=bg, fg=accent).pack()
        
        tk.Label(footer_frame, text=f"⏱️ {self.session_minutes} min focus session",
                 font=('Segoe UI', 9), bg=bg, fg='#888').pack()
        
        # Hint text
        tk.Label(main_frame, text="(Click anywhere or wait to dismiss)",
                 font=('Segoe UI', 8), bg=bg, fg='#aaa').pack(pady=(15, 0))
        
        # Click to dismiss
        self.dialog.bind("<Button-1>", lambda e: self.dialog.destroy())


class PriorityTimeLogDialog:
    """Dialog for logging time to priorities after a focus session."""
    
    def __init__(self, parent, blocker, session_minutes: int):
        self.parent = parent
        self.blocker = blocker
        self.session_minutes = session_minutes
        self.result = None
        
        # Create the dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📊 Log Priority Time")
        self.dialog.geometry("450x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        ttk.Label(main_frame, text="📊 Log Time to Priorities",
                  font=('Segoe UI', 14, 'bold')).pack(anchor=tk.W)
        
        ttk.Label(main_frame, 
                  text=f"You just completed a {self.session_minutes} minute focus session.\n"
                       "How much time did you spend on each priority?",
                  font=('Segoe UI', 10), foreground='gray').pack(anchor=tk.W, pady=(5, 15))
        
        # Get today's priorities
        today = datetime.now().strftime("%A")
        self.time_vars = []
        self.priority_indices = []
        
        priorities_frame = ttk.Frame(main_frame)
        priorities_frame.pack(fill=tk.X, pady=10)
        
        has_priorities = False
        for i, priority in enumerate(self.blocker.priorities):
            title = priority.get("title", "").strip()
            days = priority.get("days", [])
            
            if title and (not days or today in days):
                has_priorities = True
                self._create_priority_time_row(priorities_frame, i, priority)
        
        if not has_priorities:
            ttk.Label(priorities_frame, 
                      text="No active priorities for today.\nSession time won't be logged to priorities.",
                      font=('Segoe UI', 10), foreground='gray').pack(pady=20)
        
        # Quick buttons
        if has_priorities:
            quick_frame = ttk.LabelFrame(main_frame, text="Quick Options", padding="10")
            quick_frame.pack(fill=tk.X, pady=15)
            
            ttk.Button(quick_frame, text=f"Log all {self.session_minutes} min to first priority",
                       command=self.log_all_to_first).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(quick_frame, text="Split evenly",
                       command=self.split_evenly).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(btn_frame, text="💾 Save & Close",
                   command=self.save_and_close).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Skip",
                   command=self.close_dialog).pack(side=tk.RIGHT, padx=5)
    
    def _create_priority_time_row(self, parent, index, priority):
        """Create a row for logging time to a priority."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        title = priority.get("title", "")
        planned = priority.get("planned_minutes", 0)
        logged = priority.get("logged_minutes", 0)
        
        # Priority info
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X)
        
        ttk.Label(info_frame, text=f"#{index + 1}: {title}", 
                  font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        
        if planned > 0:
            progress_pct = min(100, int((logged / planned) * 100))
            ttk.Label(info_frame, text=f"({logged}/{planned} min - {progress_pct}%)",
                      font=('Segoe UI', 9), foreground='gray').pack(side=tk.RIGHT)
        
        # Time input
        time_frame = ttk.Frame(frame)
        time_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(time_frame, text="Add minutes:", width=12).pack(side=tk.LEFT)
        
        time_var = tk.StringVar(value="0")
        spinbox = ttk.Spinbox(time_frame, from_=0, to=self.session_minutes, 
                               width=8, textvariable=time_var)
        spinbox.pack(side=tk.LEFT, padx=5)
        
        self.time_vars.append(time_var)
        self.priority_indices.append(index)
        
        # Progress bar if planned time exists
        if planned > 0:
            progress = ttk.Progressbar(time_frame, mode='determinate', 
                                        length=150, maximum=100)
            progress['value'] = min(100, int((logged / planned) * 100))
            progress.pack(side=tk.RIGHT, padx=5)
    
    def log_all_to_first(self):
        """Log all session time to the first priority."""
        if self.time_vars:
            self.time_vars[0].set(str(self.session_minutes))
            for var in self.time_vars[1:]:
                var.set("0")
    
    def split_evenly(self):
        """Split session time evenly among priorities."""
        if self.time_vars:
            per_priority = self.session_minutes // len(self.time_vars)
            for var in self.time_vars:
                var.set(str(per_priority))
    
    def save_and_close(self):
        """Save the logged time and close."""
        for i, (time_var, priority_idx) in enumerate(zip(self.time_vars, self.priority_indices)):
            try:
                minutes = int(time_var.get())
                if minutes > 0:
                    current_logged = self.blocker.priorities[priority_idx].get("logged_minutes", 0)
                    self.blocker.priorities[priority_idx]["logged_minutes"] = current_logged + minutes
            except ValueError:
                pass
        
        self.blocker.save_config()
        self.result = "saved"
        self.close_dialog()
    
    def close_dialog(self):
        """Close the dialog."""
        self.dialog.destroy()
    
    def wait_for_close(self):
        """Wait for the dialog to close."""
        self.parent.wait_window(self.dialog)
        return self.result


class PriorityCheckinDialog:
    """Dialog shown during a session to ask if user is working on priorities."""
    
    def __init__(self, parent: tk.Tk, blocker, today_priorities: list, session_minutes: int = 0):
        self.parent = parent
        self.blocker = blocker
        self.today_priorities = today_priorities
        self.session_minutes = session_minutes
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Priority Check-in ⏰")
        self.dialog.geometry("420x320")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 320) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        
        # Auto-close after 60 seconds if no response
        self.dialog.after(60000, self.auto_close)
    
    def setup_ui(self):
        """Create the check-in dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with question
        ttk.Label(main_frame, text="🎯 Quick Check-in",
                  font=('Segoe UI', 14, 'bold')).pack(anchor=tk.W)
        
        ttk.Label(main_frame, 
                  text="Are you currently working on your priority tasks?",
                  font=('Segoe UI', 10)).pack(anchor=tk.W, pady=(5, 10))
        
        # Show loot bonus info
        streak = self.blocker.stats.get("streak_days", 0)
        bonuses = calculate_rarity_bonuses(self.session_minutes, streak)
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        
        if bonuses["total_bonus"] > 0 or luck > 0:
            bonus_frame = ttk.Frame(main_frame)
            bonus_frame.pack(fill=tk.X, pady=(0, 10))
            
            bonus_parts = []
            if bonuses["session_bonus"] > 0:
                bonus_parts.append(f"⏱️+{bonuses['session_bonus']}% (session)")
            if bonuses["streak_bonus"] > 0:
                bonus_parts.append(f"🔥+{bonuses['streak_bonus']}% (streak)")
            if luck > 0:
                bonus_parts.append(f"🍀+{luck}% (luck)")
            
            bonus_text = "  ".join(bonus_parts)
            ttk.Label(bonus_frame, text=f"✨ Loot bonuses: {bonus_text}",
                      font=('Segoe UI', 9), foreground='#ff9800').pack(anchor=tk.W)
        
        # Show today's priorities as reminder
        priorities_frame = ttk.LabelFrame(main_frame, text="Today's Priorities", padding="10")
        priorities_frame.pack(fill=tk.X, pady=(0, 15))
        
        priorities_text = "\n".join([f"• {p.get('title', '')}" for p in self.today_priorities])
        ttk.Label(priorities_frame, text=priorities_text if priorities_text else "No priorities set",
                  font=('Segoe UI', 9), foreground='#2e7d32').pack(anchor=tk.W)
        
        # Response buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        yes_btn = ttk.Button(btn_frame, text="✅ Yes, I'm on task!",
                             command=self.confirm_on_task)
        yes_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        no_btn = ttk.Button(btn_frame, text="⚠ Need to refocus",
                            command=self.confirm_off_task)
        no_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Dismiss button
        ttk.Button(main_frame, text="Dismiss",
                   command=self.close_dialog).pack(pady=(10, 0))
    
    def confirm_on_task(self):
        """User confirms they are on task - generate item drop and diary entry."""
        self.result = True
        self.dialog.destroy()
        
        # Get streak and calculate bonuses
        streak = self.blocker.stats.get("streak_days", 0)
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        
        # Generate item with session/streak bonuses
        item = generate_item(
            session_minutes=self.session_minutes, 
            streak_days=streak
        )
        
        # Apply luck bonus as additional rarity boost chance
        if luck > 0 and random.randint(1, 100) <= luck:
            # Lucky! Upgrade rarity if possible
            rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
            current_idx = rarity_order.index(item["rarity"])
            if current_idx < len(rarity_order) - 1:
                new_rarity = rarity_order[current_idx + 1]
                # Regenerate with upgraded rarity
                item = generate_item(rarity=new_rarity, session_minutes=self.session_minutes, 
                                    streak_days=streak)
                item["lucky_upgrade"] = True
        
        # Add to inventory and track total collected
        if "inventory" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["inventory"] = []
        self.blocker.adhd_buster["inventory"].append(item)
        
        total = self.blocker.adhd_buster.get("total_collected", 0) + 1
        self.blocker.adhd_buster["total_collected"] = total
        
        # Auto-equip if slot is empty (better new player experience)
        slot = item.get("slot")
        if "equipped" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["equipped"] = {}
        
        current_equipped = self.blocker.adhd_buster["equipped"].get(slot)
        if not current_equipped:
            self.blocker.adhd_buster["equipped"][slot] = item
            item["auto_equipped"] = True
        
        # Generate diary entry based on current power level
        power = calculate_character_power(self.blocker.adhd_buster)
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        # Only add one diary entry per day (check if we already have one today)
        today = datetime.now().strftime("%Y-%m-%d")
        diary = self.blocker.adhd_buster.get("diary", [])
        today_entries = [e for e in diary if e.get("date") == today]
        
        diary_entry = None
        if not today_entries:
            # Generate new diary entry for today
            diary_entry = generate_diary_entry(power, self.session_minutes, equipped)
            if "diary" not in self.blocker.adhd_buster:
                self.blocker.adhd_buster["diary"] = []
            self.blocker.adhd_buster["diary"].append(diary_entry)
        
        self.blocker.save_config()
        
        # Show item drop dialog first
        item_dialog = ItemDropDialog(self.parent, self.blocker, item, self.session_minutes, streak)
        
        # Then show the diary entry reveal after item dialog closes (with a small delay)
        if diary_entry:
            # Schedule diary reveal to appear after item dialog
            close_time = {"Common": 3200, "Uncommon": 3700, "Rare": 4200, 
                          "Epic": 5200, "Legendary": 6200}
            delay = close_time.get(item["rarity"], 4200)
            self.parent.after(delay, lambda: DiaryEntryRevealDialog(
                self.parent, self.blocker, diary_entry, self.session_minutes))
    
    def confirm_off_task(self):
        """User admits they're off task - provide gentle reminder."""
        self.result = False
        self.dialog.destroy()
        
        # Show refocus reminder
        feedback = tk.Toplevel(self.parent)
        feedback.title("")
        feedback.geometry("320x120")
        feedback.resizable(False, False)
        feedback.overrideredirect(True)
        
        # Center on parent
        feedback.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 320) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 120) // 2
        feedback.geometry(f"+{x}+{y}")
        
        feedback_frame = ttk.Frame(feedback, padding="20")
        feedback_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(feedback_frame, text="💪 Time to refocus!",
                  font=('Segoe UI', 12, 'bold')).pack()
        ttk.Label(feedback_frame, text="Take a breath and get back to your priorities.",
                  font=('Segoe UI', 10)).pack(pady=(5, 0))
        ttk.Label(feedback_frame, text="You've got this!",
                  font=('Segoe UI', 10), foreground='#2e7d32').pack()
        
        # Auto-close after 3 seconds
        feedback.after(3000, feedback.destroy)
    
    def auto_close(self):
        """Auto-close if no response."""
        try:
            if self.dialog.winfo_exists():
                self.dialog.destroy()
        except tk.TclError:
            pass
    
    def close_dialog(self):
        """Close the dialog without action."""
        self.result = None
        self.dialog.destroy()


class PrioritiesDialog:
    """Dialog for managing daily priorities with day-of-week reminders."""
    
    def __init__(self, parent: tk.Tk, blocker, on_start_callback=None):
        self.parent = parent
        self.blocker = blocker
        self.on_start_callback = on_start_callback
        self.result = None
        
        # Create the dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🎯 My Priorities")
        self.dialog.geometry("550x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Load existing priorities
        self.priorities = self.blocker.priorities.copy() if self.blocker.priorities else []
        # Ensure we have 3 priority slots
        while len(self.priorities) < 3:
            self.priorities.append({"title": "", "days": [], "active": False})
        
        self.setup_ui()
        self.check_day_notifications()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, text="🎯 My Priorities for Today",
                  font=('Segoe UI', 16, 'bold')).pack(side=tk.LEFT)
        
        today = datetime.now().strftime("%A, %B %d")
        ttk.Label(header_frame, text=today,
                  font=('Segoe UI', 10), foreground='gray').pack(side=tk.RIGHT)
        
        # Description
        ttk.Label(main_frame, 
                  text="Set up to 3 priority tasks. Choose which days to be reminded about each.",
                  font=('Segoe UI', 9), foreground='gray').pack(anchor=tk.W, pady=(0, 15))
        
        # Priority entries
        self.priority_vars = []
        self.day_vars = []
        self.planned_vars = []
        
        for i in range(3):
            self._create_priority_row(main_frame, i)
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Highlighted priorities for today
        today_frame = ttk.LabelFrame(main_frame, text="📌 Today's Focus", padding="10")
        today_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.today_priorities_label = ttk.Label(today_frame, text="", 
                                                 font=('Segoe UI', 10), wraplength=480)
        self.today_priorities_label.pack(anchor=tk.W)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="💾 Save Priorities",
                   command=self.save_priorities).pack(side=tk.LEFT, padx=5)
        
        self.start_btn = ttk.Button(btn_frame, text="▶ Start Working on Priority",
                                     command=self.start_priority_session)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Close",
                   command=self.close_dialog).pack(side=tk.RIGHT, padx=5)
        
        # Startup toggle
        startup_frame = ttk.Frame(main_frame)
        startup_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.show_on_startup_var = tk.BooleanVar(value=self.blocker.show_priorities_on_startup)
        ttk.Checkbutton(startup_frame, 
                        text="Show this dialog when the app starts",
                        variable=self.show_on_startup_var,
                        command=self.toggle_startup_setting).pack(anchor=tk.W)
        
        # Priority check-in settings
        checkin_frame = ttk.LabelFrame(main_frame, text="⏰ Focus Check-ins", padding="10")
        checkin_frame.pack(fill=tk.X, pady=(10, 0))
        
        checkin_row = ttk.Frame(checkin_frame)
        checkin_row.pack(fill=tk.X)
        
        self.checkin_enabled_var = tk.BooleanVar(value=self.blocker.priority_checkin_enabled)
        ttk.Checkbutton(checkin_row, 
                        text="Ask if I'm working on priorities every",
                        variable=self.checkin_enabled_var,
                        command=self.toggle_checkin_setting).pack(side=tk.LEFT)
        
        self.checkin_interval_var = tk.IntVar(value=self.blocker.priority_checkin_interval)
        interval_spin = ttk.Spinbox(checkin_row, from_=5, to=120, width=4,
                                     textvariable=self.checkin_interval_var,
                                     command=self.update_checkin_interval)
        interval_spin.pack(side=tk.LEFT, padx=3)
        interval_spin.bind('<FocusOut>', lambda e: self.update_checkin_interval())
        
        ttk.Label(checkin_row, text="minutes during sessions").pack(side=tk.LEFT)
    
    def _create_priority_row(self, parent, index):
        """Create a priority entry row with day selection and time planning."""
        priority_data = self.priorities[index]
        planned = priority_data.get("planned_minutes", 0)
        logged = priority_data.get("logged_minutes", 0)
        
        frame = ttk.LabelFrame(parent, text=f"Priority #{index + 1}", padding="10")
        frame.pack(fill=tk.X, pady=5)
        
        # Priority title entry
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(title_frame, text="Task:", width=8).pack(side=tk.LEFT)
        
        title_var = tk.StringVar(value=priority_data.get("title", ""))
        title_entry = ttk.Entry(title_frame, textvariable=title_var, width=40)
        title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 10))
        self.priority_vars.append(title_var)
        
        # Planned time input
        ttk.Label(title_frame, text="⏱ Plan:").pack(side=tk.LEFT)
        planned_var = tk.IntVar(value=planned)
        planned_spin = ttk.Spinbox(title_frame, from_=0, to=600, width=5, 
                                    textvariable=planned_var)
        planned_spin.pack(side=tk.LEFT, padx=(3, 0))
        ttk.Label(title_frame, text="min").pack(side=tk.LEFT, padx=(2, 0))
        self.planned_vars.append(planned_var)
        
        # Progress display (only if there's planned time)
        if planned > 0:
            progress_frame = ttk.Frame(frame)
            progress_frame.pack(fill=tk.X, pady=(0, 8))
            
            ttk.Label(progress_frame, text="Progress:", width=8).pack(side=tk.LEFT)
            
            # Progress bar
            progress_pct = min(100, int((logged / planned) * 100)) if planned > 0 else 0
            progress_bar = ttk.Progressbar(progress_frame, length=150, mode='determinate',
                                           value=progress_pct)
            progress_bar.pack(side=tk.LEFT, padx=(5, 10))
            
            # Time logged text
            progress_text = f"{logged}/{planned} min ({progress_pct}%)"
            if progress_pct >= 100:
                progress_text += " ✅"
            ttk.Label(progress_frame, text=progress_text, 
                     foreground='#2e7d32' if progress_pct >= 100 else 'gray').pack(side=tk.LEFT)
        
        # Day selection
        days_frame = ttk.Frame(frame)
        days_frame.pack(fill=tk.X)
        
        ttk.Label(days_frame, text="Remind:", width=8).pack(side=tk.LEFT)
        
        day_checkboxes = {}
        saved_days = priority_data.get("days", [])
        
        for day in DAYS_OF_WEEK:
            var = tk.BooleanVar(value=day in saved_days)
            cb = ttk.Checkbutton(days_frame, text=day[:3], variable=var, width=5)
            cb.pack(side=tk.LEFT, padx=2)
            day_checkboxes[day] = var
        
        self.day_vars.append(day_checkboxes)
    
    def check_day_notifications(self):
        """Check which priorities should be shown today based on day selection."""
        today = datetime.now().strftime("%A")
        today_priorities = []
        
        for i, priority in enumerate(self.priorities):
            title = priority.get("title", "").strip()
            days = priority.get("days", [])
            planned = priority.get("planned_minutes", 0)
            logged = priority.get("logged_minutes", 0)
            
            if title and (not days or today in days):
                # Show progress if there's planned time
                if planned > 0:
                    pct = min(100, int((logged / planned) * 100))
                    status = "✅" if pct >= 100 else f"({logged}/{planned} min, {pct}%)"
                    today_priorities.append(f"• {title} {status}")
                else:
                    today_priorities.append(f"• {title}")
        
        if today_priorities:
            self.today_priorities_label.config(
                text="\n".join(today_priorities),
                foreground='#2e7d32'
            )
        else:
            self.today_priorities_label.config(
                text="No priorities set for today. Add your tasks above!",
                foreground='gray'
            )
    
    def save_priorities(self):
        """Save the priorities to config."""
        new_priorities = []
        
        for i in range(3):
            title = self.priority_vars[i].get().strip()
            days = [day for day, var in self.day_vars[i].items() if var.get()]
            planned = self.planned_vars[i].get() if i < len(self.planned_vars) else 0
            # Preserve existing logged_minutes
            logged = self.priorities[i].get("logged_minutes", 0)
            
            new_priorities.append({
                "title": title,
                "days": days,
                "active": bool(title),
                "planned_minutes": planned,
                "logged_minutes": logged
            })
        
        self.blocker.priorities = new_priorities
        self.blocker.save_config()
        self.priorities = new_priorities
        self.check_day_notifications()
        
        # Show confirmation
        self.dialog.after(0, lambda: self._show_save_feedback())
    
    def _show_save_feedback(self):
        """Show brief save feedback."""
        original_text = self.today_priorities_label.cget("text")
        self.today_priorities_label.config(text="✓ Priorities saved!", foreground='#1976d2')
        self.dialog.after(1500, lambda: self.check_day_notifications())
    
    def toggle_startup_setting(self):
        """Toggle whether to show dialog on startup."""
        self.blocker.show_priorities_on_startup = self.show_on_startup_var.get()
        self.blocker.save_config()
    
    def toggle_checkin_setting(self):
        """Toggle priority check-in reminders during sessions."""
        self.blocker.priority_checkin_enabled = self.checkin_enabled_var.get()
        self.blocker.save_config()
    
    def update_checkin_interval(self):
        """Update the check-in interval setting."""
        try:
            interval = self.checkin_interval_var.get()
            if 5 <= interval <= 120:
                self.blocker.priority_checkin_interval = interval
                self.blocker.save_config()
        except (tk.TclError, ValueError):
            pass
    
    def start_priority_session(self):
        """Start a focus session for the first active priority."""
        # Find the first priority for today
        today = datetime.now().strftime("%A")
        
        for priority in self.priorities:
            title = priority.get("title", "").strip()
            days = priority.get("days", [])
            
            if title and (not days or today in days):
                self.result = {"action": "start", "priority": title}
                self.close_dialog()
                
                if self.on_start_callback:
                    self.on_start_callback(title)
                return
        
        # No priority for today
        from tkinter import messagebox
        messagebox.showinfo("No Priority", 
                           "No priority is set for today. Add a task above first!",
                           parent=self.dialog)
    
    def close_dialog(self):
        """Close the dialog."""
        self.dialog.destroy()
    
    def wait_for_close(self):
        """Wait for the dialog to close."""
        self.parent.wait_window(self.dialog)
        return self.result


class FocusBlockerGUI:
    """Enhanced GUI with tabbed interface"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Personal Freedom - Focus Blocker")
        self.root.geometry("600x700")
        self.root.minsize(550, 600)

        self.blocker = BlockerCore()
        self.timer_running = False
        self.remaining_seconds = 0
        self._timer_lock = threading.Lock()
        self.session_start_time = None
        
        # Priority check-in tracking
        self.last_checkin_time = None
        self.checkin_dialog_open = False
        
        # Pomodoro state
        self.pomodoro_is_break = False
        self.pomodoro_session_count = 0
        self.pomodoro_total_work_time = 0
        
        # System tray state
        self.tray_icon = None
        self.minimize_to_tray = tk.BooleanVar(value=False)

        # Apply theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._configure_styles()

        self.setup_ui()
        self.check_admin_status()
        self.update_stats_display()

        # Check for scheduled blocking
        self.check_scheduled_blocking()
        
        # Check for crash recovery (orphaned sessions)
        self.root.after(500, self.check_crash_recovery)
        
        # Show priorities dialog on startup if enabled
        self.root.after(600, self.check_priorities_on_startup)
        
        # Handle window minimize
        self.root.bind('<Unmap>', self._on_minimize)

    def _configure_styles(self) -> None:
        """Configure custom styles."""
        self.style.configure('Title.TLabel', font=('Segoe UI', 20, 'bold'))
        self.style.configure('Timer.TLabel', font=('Consolas', 42, 'bold'))
        self.style.configure('Status.TLabel', font=('Segoe UI', 11, 'bold'))
        self.style.configure('Stats.TLabel', font=('Segoe UI', 10))
        self.style.configure('Header.TLabel', font=('Segoe UI', 11, 'bold'))

        # Button styles
        self.style.configure('Start.TButton', font=('Segoe UI', 10, 'bold'))
        self.style.configure('Stop.TButton', font=('Segoe UI', 10))
        self.style.configure('Category.TCheckbutton', font=('Segoe UI', 10))

    def setup_ui(self) -> None:
        """Setup the tabbed user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="🔒 Personal Freedom",
                  style='Title.TLabel').pack(side=tk.LEFT)

        self.admin_label = ttk.Label(header_frame, text="", font=('Segoe UI', 9))
        self.admin_label.pack(side=tk.RIGHT, padx=10)

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Timer
        self.timer_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.timer_tab, text="⏱ Timer")
        self.setup_timer_tab()

        # Tab 2: Sites
        self.sites_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.sites_tab, text="🌐 Sites")
        self.setup_sites_tab()

        # Tab 3: Categories
        self.categories_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.categories_tab, text="📁 Categories")
        self.setup_categories_tab()

        # Tab 4: Schedule
        self.schedule_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.schedule_tab, text="📅 Schedule")
        self.setup_schedule_tab()

        # Tab 5: Stats
        self.stats_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.stats_tab, text="📊 Stats")
        self.setup_stats_tab()

        # Tab 6: Settings
        self.settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_tab, text="⚙ Settings")
        self.setup_settings_tab()

        # Tab 7: AI Insights (if available)
        if AI_AVAILABLE:
            self.ai_tab = ttk.Frame(self.notebook, padding="10")
            self.notebook.add(self.ai_tab, text="🧠 AI Insights")
            self.setup_ai_tab()

    def setup_timer_tab(self) -> None:
        """Setup the timer tab."""
        # Timer display
        timer_frame = ttk.LabelFrame(self.timer_tab, text="Focus Timer", padding="15")
        timer_frame.pack(fill=tk.X, pady=(0, 10))

        self.timer_display = ttk.Label(timer_frame, text="00:00:00", style='Timer.TLabel')
        self.timer_display.pack(pady=15)

        # Mode selection
        mode_frame = ttk.Frame(timer_frame)
        mode_frame.pack(fill=tk.X, pady=5)

        ttk.Label(mode_frame, text="Mode:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.mode_var = tk.StringVar(value=BlockMode.NORMAL)

        modes = [("Normal", BlockMode.NORMAL), ("Strict 🔐", BlockMode.STRICT),
                 ("Pomodoro 🍅", BlockMode.POMODORO)]
        for text, mode in modes:
            ttk.Radiobutton(mode_frame, text=text, value=mode,
                           variable=self.mode_var).pack(side=tk.LEFT, padx=10)

        # Time input
        time_frame = ttk.Frame(timer_frame)
        time_frame.pack(fill=tk.X, pady=10)

        ttk.Label(time_frame, text="Duration:").pack(side=tk.LEFT, padx=5)

        self.hours_var = tk.StringVar(value="0")
        ttk.Spinbox(time_frame, from_=0, to=12, width=4,
                    textvariable=self.hours_var).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame, text="h").pack(side=tk.LEFT)

        self.minutes_var = tk.StringVar(value="25")
        ttk.Spinbox(time_frame, from_=0, to=59, width=4,
                    textvariable=self.minutes_var).pack(side=tk.LEFT, padx=2)
        ttk.Label(time_frame, text="m").pack(side=tk.LEFT)

        # Quick buttons
        quick_frame = ttk.Frame(timer_frame)
        quick_frame.pack(fill=tk.X, pady=10)

        presets = [("25m", 25), ("45m", 45), ("1h", 60), ("2h", 120), ("4h", 240)]
        for text, mins in presets:
            ttk.Button(quick_frame, text=text, width=6,
                      command=lambda m=mins: self.set_quick_time(m)).pack(side=tk.LEFT, padx=3, expand=True)

        # Control buttons
        btn_frame = ttk.Frame(timer_frame)
        btn_frame.pack(fill=tk.X, pady=15)

        self.start_btn = ttk.Button(btn_frame, text="▶ Start Focus",
                                    command=self.start_session, style='Start.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.stop_btn = ttk.Button(btn_frame, text="⬛ Stop",
                                   command=self.stop_session, style='Stop.TButton',
                                   state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Status
        self.status_label = ttk.Label(timer_frame, text="Ready to focus",
                                      style='Status.TLabel')
        self.status_label.pack(pady=5)

        # Quick stats
        stats_frame = ttk.LabelFrame(self.timer_tab, text="Today's Progress", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)

        self.quick_stats_label = ttk.Label(stats_frame, text="", style='Stats.TLabel')
        self.quick_stats_label.pack()

    def setup_sites_tab(self):
        """Setup the sites management tab"""
        # Blacklist frame
        black_frame = ttk.LabelFrame(self.sites_tab, text="Blocked Sites (Custom)", padding="10")
        black_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Listbox with scrollbar
        list_frame = ttk.Frame(black_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.site_listbox = tk.Listbox(list_frame, height=10, font=('Consolas', 10),
                                       yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED)
        self.site_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.site_listbox.yview)

        # Add/Remove controls
        ctrl_frame = ttk.Frame(black_frame)
        ctrl_frame.pack(fill=tk.X, pady=(10, 0))

        self.site_entry = ttk.Entry(ctrl_frame, font=('Segoe UI', 10))
        self.site_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.site_entry.bind('<Return>', lambda e: self.add_site())

        ttk.Button(ctrl_frame, text="+ Add", command=self.add_site, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="- Remove", command=self.remove_site, width=8).pack(side=tk.LEFT, padx=2)

        # Whitelist frame
        white_frame = ttk.LabelFrame(self.sites_tab, text="Whitelist (Never Block)", padding="10")
        white_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        list_frame2 = ttk.Frame(white_frame)
        list_frame2.pack(fill=tk.BOTH, expand=True)

        scrollbar2 = ttk.Scrollbar(list_frame2)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)

        self.whitelist_listbox = tk.Listbox(list_frame2, height=6, font=('Consolas', 10),
                                            yscrollcommand=scrollbar2.set)
        self.whitelist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.config(command=self.whitelist_listbox.yview)

        ctrl_frame2 = ttk.Frame(white_frame)
        ctrl_frame2.pack(fill=tk.X, pady=(10, 0))

        self.whitelist_entry = ttk.Entry(ctrl_frame2, font=('Segoe UI', 10))
        self.whitelist_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(ctrl_frame2, text="+ Add", command=self.add_whitelist, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame2, text="- Remove", command=self.remove_whitelist, width=8).pack(side=tk.LEFT, padx=2)

        # Import/Export
        io_frame = ttk.Frame(self.sites_tab)
        io_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(io_frame, text="📥 Import", command=self.import_sites).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="📤 Export", command=self.export_sites).pack(side=tk.LEFT, padx=5)

        self.update_site_lists()

    def setup_categories_tab(self):
        """Setup the categories tab"""
        ttk.Label(self.categories_tab, text="Enable/disable entire categories of sites:",
                  style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))

        self.category_vars = {}

        for category, sites in SITE_CATEGORIES.items():
            frame = ttk.Frame(self.categories_tab)
            frame.pack(fill=tk.X, pady=3)

            var = tk.BooleanVar(value=self.blocker.categories_enabled.get(category, True))
            self.category_vars[category] = var

            cb = ttk.Checkbutton(frame, text=f"{category} ({len(sites)} sites)",
                                variable=var, style='Category.TCheckbutton',
                                command=lambda c=category: self.toggle_category(c))
            cb.pack(side=tk.LEFT)

            # Show sites button
            ttk.Button(frame, text="View", width=6,
                      command=lambda c=category: self.show_category_sites(c)).pack(side=tk.RIGHT)

        # Total count
        ttk.Separator(self.categories_tab).pack(fill=tk.X, pady=15)

        self.total_sites_label = ttk.Label(self.categories_tab, text="", style='Stats.TLabel')
        self.total_sites_label.pack()
        self.update_total_sites_count()

    def setup_schedule_tab(self):
        """Setup the schedule tab"""
        ttk.Label(self.schedule_tab, text="Automatic blocking schedules:",
                  style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))

        # Schedule list
        list_frame = ttk.Frame(self.schedule_tab)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('days', 'time', 'status')
        self.schedule_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        self.schedule_tree.heading('days', text='Days')
        self.schedule_tree.heading('time', text='Time')
        self.schedule_tree.heading('status', text='Status')
        self.schedule_tree.column('days', width=200)
        self.schedule_tree.column('time', width=150)
        self.schedule_tree.column('status', width=80)
        self.schedule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, command=self.schedule_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.schedule_tree.configure(yscrollcommand=scrollbar.set)

        # Add schedule controls
        add_frame = ttk.LabelFrame(self.schedule_tab, text="Add Schedule", padding="10")
        add_frame.pack(fill=tk.X, pady=10)

        # Days selection
        days_frame = ttk.Frame(add_frame)
        days_frame.pack(fill=tk.X, pady=5)

        ttk.Label(days_frame, text="Days:").pack(side=tk.LEFT, padx=5)

        self.day_vars = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            var = tk.BooleanVar(value=i < 5)  # Default: weekdays
            self.day_vars.append(var)
            ttk.Checkbutton(days_frame, text=day, variable=var).pack(side=tk.LEFT, padx=3)

        # Time selection
        time_frame = ttk.Frame(add_frame)
        time_frame.pack(fill=tk.X, pady=5)

        ttk.Label(time_frame, text="From:").pack(side=tk.LEFT, padx=5)
        self.start_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3, format="%02.0f")
        self.start_hour.set("09")
        self.start_hour.pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.start_min = ttk.Spinbox(time_frame, from_=0, to=59, width=3, format="%02.0f")
        self.start_min.set("00")
        self.start_min.pack(side=tk.LEFT)

        ttk.Label(time_frame, text="  To:").pack(side=tk.LEFT, padx=5)
        self.end_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3, format="%02.0f")
        self.end_hour.set("17")
        self.end_hour.pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.end_min = ttk.Spinbox(time_frame, from_=0, to=59, width=3, format="%02.0f")
        self.end_min.set("00")
        self.end_min.pack(side=tk.LEFT)

        ttk.Button(add_frame, text="+ Add Schedule", command=self.add_schedule).pack(pady=10)

        # Schedule actions
        action_frame = ttk.Frame(self.schedule_tab)
        action_frame.pack(fill=tk.X)

        ttk.Button(action_frame, text="Toggle", command=self.toggle_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Delete", command=self.delete_schedule).pack(side=tk.LEFT, padx=5)

        self.update_schedule_list()

    def setup_stats_tab(self):
        """Setup the statistics tab with scrollable content"""
        # Create scrollable canvas
        canvas = tk.Canvas(self.stats_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.stats_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # === Overview Section ===
        overview_frame = ttk.LabelFrame(scrollable_frame, text="📊 Overview", padding="15")
        overview_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        stats_grid = ttk.Frame(overview_frame)
        stats_grid.pack()

        self.stat_labels = {}
        stats = [
            ("total_hours", "Total Focus Time", "0h"),
            ("sessions", "Sessions Completed", "0"),
            ("streak", "Current Streak", "0 days"),
            ("best_streak", "Best Streak", "0 days"),
        ]

        for i, (key, label, default) in enumerate(stats):
            row, col = divmod(i, 2)
            frame = ttk.Frame(stats_grid)
            frame.grid(row=row, column=col, padx=20, pady=10)

            ttk.Label(frame, text=label, font=('Segoe UI', 9)).pack()
            self.stat_labels[key] = ttk.Label(frame, text=default,
                                              font=('Segoe UI', 18, 'bold'))
            self.stat_labels[key].pack()

        # === Focus Goals Dashboard ===
        goals_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Focus Goals Dashboard", padding="15")
        goals_frame.pack(fill=tk.X, pady=10, padx=5)

        # Weekly Goal
        weekly_frame = ttk.Frame(goals_frame)
        weekly_frame.pack(fill=tk.X, pady=5)

        ttk.Label(weekly_frame, text="Weekly Goal:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)

        weekly_progress_frame = ttk.Frame(weekly_frame)
        weekly_progress_frame.pack(fill=tk.X, pady=5)

        self.weekly_goal_progress = ttk.Progressbar(weekly_progress_frame, mode='determinate',
                                                     length=300, maximum=100)
        self.weekly_goal_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.weekly_goal_label = ttk.Label(weekly_progress_frame, text="0h / 10h (0%)",
                                            font=('Segoe UI', 9))
        self.weekly_goal_label.pack(side=tk.LEFT)

        weekly_settings = ttk.Frame(weekly_frame)
        weekly_settings.pack(fill=tk.X, pady=3)

        ttk.Label(weekly_settings, text="Target (hours):").pack(side=tk.LEFT)
        self.weekly_goal_var = tk.StringVar(value="10")
        ttk.Spinbox(weekly_settings, from_=1, to=100, width=5,
                    textvariable=self.weekly_goal_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(weekly_settings, text="Set", width=6,
                   command=lambda: self.set_focus_goal("weekly")).pack(side=tk.LEFT)

        ttk.Separator(goals_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Monthly Goal
        monthly_frame = ttk.Frame(goals_frame)
        monthly_frame.pack(fill=tk.X, pady=5)

        ttk.Label(monthly_frame, text="Monthly Goal:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)

        monthly_progress_frame = ttk.Frame(monthly_frame)
        monthly_progress_frame.pack(fill=tk.X, pady=5)

        self.monthly_goal_progress = ttk.Progressbar(monthly_progress_frame, mode='determinate',
                                                      length=300, maximum=100)
        self.monthly_goal_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.monthly_goal_label = ttk.Label(monthly_progress_frame, text="0h / 40h (0%)",
                                             font=('Segoe UI', 9))
        self.monthly_goal_label.pack(side=tk.LEFT)

        monthly_settings = ttk.Frame(monthly_frame)
        monthly_settings.pack(fill=tk.X, pady=3)

        ttk.Label(monthly_settings, text="Target (hours):").pack(side=tk.LEFT)
        self.monthly_goal_var = tk.StringVar(value="40")
        ttk.Spinbox(monthly_settings, from_=1, to=500, width=5,
                    textvariable=self.monthly_goal_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(monthly_settings, text="Set", width=6,
                   command=lambda: self.set_focus_goal("monthly")).pack(side=tk.LEFT)

        # === ADHD Buster Character ===
        buster_frame = ttk.LabelFrame(scrollable_frame, text="🦸 ADHD Buster", padding="15")
        buster_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Power level and title
        power = calculate_character_power(self.blocker.adhd_buster)
        max_power = 8 * RARITY_POWER["Legendary"]
        
        # Title and next tier calculation
        if power >= 1500:
            title = "🌟 Focus Deity"
            next_tier = None
            next_power = max_power
        elif power >= 1000:
            title = "⚡ Legendary Champion"
            next_tier = "Focus Deity"
            next_power = 1500
        elif power >= 600:
            title = "🔥 Epic Warrior"
            next_tier = "Legendary Champion"
            next_power = 1000
        elif power >= 300:
            title = "💪 Seasoned Fighter"
            next_tier = "Epic Warrior"
            next_power = 600
        elif power >= 100:
            title = "🛡️ Apprentice"
            next_tier = "Seasoned Fighter"
            next_power = 300
        else:
            title = "🌱 Novice"
            next_tier = "Apprentice"
            next_power = 100
        
        power_frame = ttk.Frame(buster_frame)
        power_frame.pack(fill=tk.X)
        
        self.buster_power_label = tk.Label(power_frame, text=f"⚔ Power: {power}  {title}",
                                            font=('Segoe UI', 11, 'bold'), fg='#e65100')
        self.buster_power_label.pack(side=tk.LEFT)
        
        # Power progress to next tier
        progress_frame = ttk.Frame(buster_frame)
        progress_frame.pack(fill=tk.X, pady=(5, 0))
        
        if next_tier:
            progress_pct = int((power / next_power) * 100)
            progress_text = f"📈 {power}/{next_power} to {next_tier} ({progress_pct}%)"
        else:
            progress_text = f"👑 MAX TIER ACHIEVED! ({power}/{max_power} power)"
        
        self.buster_progress_label = ttk.Label(progress_frame, text=progress_text,
                                                font=('Segoe UI', 9), foreground='#4caf50')
        self.buster_progress_label.pack(anchor=tk.W)
        
        # Quick character stats
        buster_info = ttk.Frame(buster_frame)
        buster_info.pack(fill=tk.X, pady=(5, 0))
        
        total_items = len(self.blocker.adhd_buster.get("inventory", []))
        equipped_count = len([s for s in self.blocker.adhd_buster.get("equipped", {}).values() if s])
        total_collected = self.blocker.adhd_buster.get("total_collected", total_items)
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        
        stats_text = f"📦 {total_items} in bag  |  ⚔ {equipped_count}/8 equipped  |  🎁 {total_collected} lifetime"
        if luck > 0:
            stats_text += f"  |  🍀 +{luck}% luck"
        
        self.buster_stats_label = ttk.Label(buster_info, text=stats_text,
                                             font=('Segoe UI', 9), foreground='gray')
        self.buster_stats_label.pack(anchor=tk.W)
        
        # Rarity breakdown
        inventory = self.blocker.adhd_buster.get("inventory", [])
        rarity_counts = {}
        for item in inventory:
            r = item.get("rarity", "Common")
            rarity_counts[r] = rarity_counts.get(r, 0) + 1
        
        if rarity_counts:
            rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
            rarity_text = "  ".join([f"{r[:1]}: {rarity_counts[r]}" for r in rarity_order if r in rarity_counts])
            ttk.Label(buster_info, text=f"Rarities: {rarity_text}",
                      font=('Segoe UI', 8), foreground='#666').pack(anchor=tk.W)
        
        ttk.Button(buster_frame, text="🦸 View Character & Inventory",
                   command=self.open_adhd_buster).pack(pady=(10, 0))

        # === Bypass Attempts Tracking ===
        if BYPASS_LOGGER_AVAILABLE:
            bypass_frame = ttk.LabelFrame(scrollable_frame, text="🚫 Distraction Attempts", padding="15")
            bypass_frame.pack(fill=tk.X, pady=10, padx=5)

            # Current session info
            session_frame = ttk.Frame(bypass_frame)
            session_frame.pack(fill=tk.X, pady=5)

            self.bypass_session_label = ttk.Label(session_frame,
                                                   text="Current Session: 0 attempts",
                                                   font=('Segoe UI', 10, 'bold'))
            self.bypass_session_label.pack(anchor=tk.W)

            self.bypass_session_sites = ttk.Label(session_frame,
                                                   text="No sites accessed",
                                                   font=('Segoe UI', 9), foreground='gray')
            self.bypass_session_sites.pack(anchor=tk.W)

            ttk.Separator(bypass_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

            # All-time stats
            alltime_frame = ttk.Frame(bypass_frame)
            alltime_frame.pack(fill=tk.X, pady=5)

            ttk.Label(alltime_frame, text="All-Time Statistics:",
                      font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)

            self.bypass_total_label = ttk.Label(alltime_frame,
                                                 text="Total attempts: 0",
                                                 font=('Segoe UI', 9))
            self.bypass_total_label.pack(anchor=tk.W, pady=2)

            self.bypass_top_sites = ttk.Label(alltime_frame,
                                               text="Top distractions: -",
                                               font=('Segoe UI', 9))
            self.bypass_top_sites.pack(anchor=tk.W, pady=2)

            self.bypass_peak_hours = ttk.Label(alltime_frame,
                                                text="Peak hours: -",
                                                font=('Segoe UI', 9))
            self.bypass_peak_hours.pack(anchor=tk.W, pady=2)

            # Insights
            ttk.Separator(bypass_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

            ttk.Label(bypass_frame, text="💡 Insights:",
                      font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)

            self.bypass_insights_text = tk.Text(bypass_frame, height=3, wrap=tk.WORD,
                                                 font=('Segoe UI', 9), bg='#fff9e6',
                                                 relief=tk.FLAT)
            self.bypass_insights_text.pack(fill=tk.X, pady=5)

            ttk.Button(bypass_frame, text="🔄 Refresh Stats",
                       command=self.refresh_bypass_stats).pack(pady=5)

        # === Weekly Chart ===
        week_frame = ttk.LabelFrame(scrollable_frame, text="📈 This Week", padding="15")
        week_frame.pack(fill=tk.X, pady=10, padx=5)

        self.week_chart = tk.Text(week_frame, height=10, font=('Consolas', 10),
                                  state=tk.DISABLED, bg='#f5f5f5')
        self.week_chart.pack(fill=tk.X)

        # Reset button
        ttk.Button(scrollable_frame, text="🔄 Reset All Statistics",
                   command=self.reset_stats).pack(pady=10)

        # Load initial data
        self.load_focus_goals()
        self.update_focus_goals_display()
        if BYPASS_LOGGER_AVAILABLE:
            self.refresh_bypass_stats()

    def setup_settings_tab(self):
        """Setup the settings tab"""
        # My Priorities Section
        priorities_frame = ttk.LabelFrame(self.settings_tab, text="🎯 My Priorities", padding="10")
        priorities_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(priorities_frame, 
                  text="Set up to 3 daily priority tasks with day-of-week reminders.",
                  wraplength=400).pack(anchor=tk.W)

        priorities_btn_frame = ttk.Frame(priorities_frame)
        priorities_btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(priorities_btn_frame, text="📝 Manage Priorities",
                   command=self.open_priorities_dialog).pack(side=tk.LEFT, padx=5)

        self.priorities_startup_var = tk.BooleanVar(value=self.blocker.show_priorities_on_startup)
        ttk.Checkbutton(priorities_btn_frame, 
                        text="Show on startup",
                        variable=self.priorities_startup_var,
                        command=self.toggle_priorities_startup).pack(side=tk.LEFT, padx=15)

        # Password protection
        pwd_frame = ttk.LabelFrame(self.settings_tab, text="Password Protection", padding="10")
        pwd_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(pwd_frame, text="Set a password to prevent stopping Strict Mode sessions early.",
                  wraplength=400).pack(anchor=tk.W)

        pwd_btn_frame = ttk.Frame(pwd_frame)
        pwd_btn_frame.pack(fill=tk.X, pady=10)

        self.pwd_status = ttk.Label(pwd_btn_frame, text="No password set")
        self.pwd_status.pack(side=tk.LEFT, padx=5)

        ttk.Button(pwd_btn_frame, text="Set Password",
                   command=self.set_password).pack(side=tk.RIGHT, padx=5)
        ttk.Button(pwd_btn_frame, text="Remove Password",
                   command=self.remove_password).pack(side=tk.RIGHT, padx=5)

        self.update_password_status()

        # Pomodoro settings
        pomo_frame = ttk.LabelFrame(self.settings_tab, text="Pomodoro Settings", padding="10")
        pomo_frame.pack(fill=tk.X, pady=10)

        settings = [
            ("Work duration (min):", "pomodoro_work", self.blocker.pomodoro_work),
            ("Short break (min):", "pomodoro_break", self.blocker.pomodoro_break),
            ("Long break (min):", "pomodoro_long_break", self.blocker.pomodoro_long_break),
        ]

        self.pomo_vars = {}
        for label, key, default in settings:
            frame = ttk.Frame(pomo_frame)
            frame.pack(fill=tk.X, pady=3)
            ttk.Label(frame, text=label, width=20).pack(side=tk.LEFT)
            var = tk.StringVar(value=str(default))
            self.pomo_vars[key] = var
            ttk.Spinbox(frame, from_=1, to=120, width=5, textvariable=var).pack(side=tk.LEFT)

        ttk.Button(pomo_frame, text="Save Pomodoro Settings",
                   command=self.save_pomodoro_settings).pack(pady=10)

        # System Tray Section (if available)
        if TRAY_AVAILABLE:
            tray_frame = ttk.LabelFrame(self.settings_tab, text="🖥️ System Tray", padding="10")
            tray_frame.pack(fill=tk.X, pady=10)

            ttk.Checkbutton(
                tray_frame,
                text="Minimize to system tray instead of taskbar",
                variable=self.minimize_to_tray
            ).pack(anchor=tk.W)

            ttk.Label(tray_frame,
                      text="When enabled, minimizing the window will hide it to the system tray.\n"
                           "Click the tray icon to restore the window.",
                      font=('Segoe UI', 8), foreground='gray').pack(anchor=tk.W, pady=(5, 0))

        # Backup & Restore Section
        backup_frame = ttk.LabelFrame(self.settings_tab, text="💾 Backup & Restore", padding="10")
        backup_frame.pack(fill=tk.X, pady=10)

        ttk.Label(backup_frame,
                  text="Backup or restore all your data (settings, stats, goals, achievements).",
                  wraplength=450).pack(anchor=tk.W, pady=(0, 10))

        backup_btn_frame = ttk.Frame(backup_frame)
        backup_btn_frame.pack(fill=tk.X)

        ttk.Button(backup_btn_frame, text="📤 Create Backup",
                   command=self.create_full_backup).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(backup_btn_frame, text="📥 Restore Backup",
                   command=self.restore_full_backup).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # About
        about_frame = ttk.LabelFrame(self.settings_tab, text="About", padding="10")
        about_frame.pack(fill=tk.X, pady=10)

        ttk.Label(about_frame, text="Personal Freedom v2.3.0",
                  font=('Segoe UI', 11, 'bold')).pack()
        ttk.Label(about_frame, text="A focus and productivity tool for Windows",
                  font=('Segoe UI', 9)).pack()
        ttk.Label(about_frame, text="Block distracting websites and track your progress.",
                  font=('Segoe UI', 9)).pack()

        # Emergency Cleanup Section
        cleanup_frame = ttk.LabelFrame(self.settings_tab, text="⚠️ Emergency Cleanup", padding="10")
        cleanup_frame.pack(fill=tk.X, pady=10)

        ttk.Label(cleanup_frame,
                  text="Use this if websites remain blocked after closing the app,\n"
                       "or if you need to remove all app changes from your system.",
                  wraplength=450, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 10))

        cleanup_btn = ttk.Button(cleanup_frame, text="🧹 Remove All Blocks & Clean System",
                                 command=self.emergency_cleanup_action)
        cleanup_btn.pack(pady=5)

    def setup_ai_tab(self):
        """Setup the AI Insights tab"""
        # Initialize AI engines (guarded by AI_AVAILABLE check in setup_ui)
        self.analyzer = ProductivityAnalyzer(STATS_PATH)  # type: ignore[misc]
        self.gamification = GamificationEngine(STATS_PATH)  # type: ignore[misc]
        self.goals = FocusGoals(GOALS_PATH, STATS_PATH)  # type: ignore[misc]

        # Create scrollable canvas
        canvas = tk.Canvas(self.ai_tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.ai_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # === AI Insights Section ===
        insights_frame = ttk.LabelFrame(scrollable_frame, text="🔍 AI Insights & Recommendations", padding="15")
        insights_frame.pack(fill=tk.X, pady=(0, 10))

        self.insights_text = tk.Text(insights_frame, height=6, wrap=tk.WORD,
                                     font=('Segoe UI', 9), bg='#f0f0f0', relief=tk.FLAT)
        self.insights_text.pack(fill=tk.X, pady=5)

        ttk.Button(insights_frame, text="🔄 Refresh Insights",
                   command=self.refresh_ai_insights).pack(pady=5)

        # === Achievements Section ===
        ach_frame = ttk.LabelFrame(scrollable_frame, text="🏆 Achievements", padding="15")
        ach_frame.pack(fill=tk.X, pady=10)

        self.achievement_widgets = {}
        achievements = self.gamification.get_achievements()

        # Create a grid of achievement cards
        for idx, (ach_id, ach_data) in enumerate(achievements.items()):
            row, col = divmod(idx, 2)

            card = ttk.Frame(ach_frame, relief=tk.RIDGE, borderwidth=1)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='ew')

            # Achievement icon and name
            header = ttk.Frame(card)
            header.pack(fill=tk.X, padx=8, pady=(8, 2))

            icon_label = ttk.Label(header, text=ach_data['icon'], font=('Segoe UI', 16))
            icon_label.pack(side=tk.LEFT)

            name_label = ttk.Label(header, text=ach_data['name'],
                                  font=('Segoe UI', 9, 'bold'))
            name_label.pack(side=tk.LEFT, padx=5)

            # Description
            desc_label = ttk.Label(card, text=ach_data['description'],
                                  font=('Segoe UI', 8), foreground='gray')
            desc_label.pack(fill=tk.X, padx=8, pady=(0, 2))

            # Progress bar
            progress_frame = ttk.Frame(card)
            progress_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

            progress_bar = ttk.Progressbar(progress_frame, mode='determinate',
                                          length=150, maximum=100)
            progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

            progress_label = ttk.Label(progress_frame, text="0%",
                                      font=('Segoe UI', 8))
            progress_label.pack(side=tk.LEFT, padx=5)

            self.achievement_widgets[ach_id] = {
                'card': card,
                'progress_bar': progress_bar,
                'progress_label': progress_label,
                'icon': icon_label,
                'name': name_label
            }

        # Configure grid columns
        ach_frame.columnconfigure(0, weight=1)
        ach_frame.columnconfigure(1, weight=1)

        # === Daily Challenge Section ===
        challenge_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Daily Challenge", padding="15")
        challenge_frame.pack(fill=tk.X, pady=10)

        self.challenge_title = ttk.Label(challenge_frame, text="",
                                        font=('Segoe UI', 10, 'bold'))
        self.challenge_title.pack(anchor=tk.W)

        self.challenge_desc = ttk.Label(challenge_frame, text="",
                                       font=('Segoe UI', 9), foreground='gray')
        self.challenge_desc.pack(anchor=tk.W, pady=(2, 8))

        challenge_progress_frame = ttk.Frame(challenge_frame)
        challenge_progress_frame.pack(fill=tk.X)

        self.challenge_progress = ttk.Progressbar(challenge_progress_frame,
                                                 mode='determinate', length=300)
        self.challenge_progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.challenge_status = ttk.Label(challenge_progress_frame, text="0/0",
                                         font=('Segoe UI', 9))
        self.challenge_status.pack(side=tk.LEFT, padx=10)

        # === Goals Section ===
        goals_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Active Goals", padding="15")
        goals_frame.pack(fill=tk.X, pady=10)

        self.goals_listbox = tk.Listbox(goals_frame, height=5,
                                        font=('Segoe UI', 9))
        self.goals_listbox.pack(fill=tk.X, pady=(0, 10))

        goals_btn_frame = ttk.Frame(goals_frame)
        goals_btn_frame.pack(fill=tk.X)

        ttk.Button(goals_btn_frame, text="➕ Add Goal",
                   command=self.add_goal_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(goals_btn_frame, text="✓ Complete Goal",
                   command=self.complete_selected_goal).pack(side=tk.LEFT, padx=5)
        ttk.Button(goals_btn_frame, text="🗑 Remove Goal",
                   command=self.remove_selected_goal).pack(side=tk.LEFT, padx=5)

        # === Productivity Stats Section ===
        stats_frame = ttk.LabelFrame(scrollable_frame, text="📈 AI-Powered Statistics", padding="15")
        stats_frame.pack(fill=tk.X, pady=10)

        self.ai_stats_text = tk.Text(stats_frame, height=5, wrap=tk.WORD,
                                     font=('Courier New', 9), bg='#f0f0f0', relief=tk.FLAT)
        self.ai_stats_text.pack(fill=tk.X)

        # === GPU AI Insights Section (if available) ===
        if LOCAL_AI_AVAILABLE:
            gpu_frame = ttk.LabelFrame(scrollable_frame, text="🚀 GPU AI Insights", padding="15")
            gpu_frame.pack(fill=tk.X, pady=10)

            # Initialize local AI
            if not hasattr(self, 'local_ai'):
                self.local_ai = LocalAI()  # type: ignore[misc]

            # GPU status
            gpu_status = "✅ Running on GPU (CUDA)" if self.local_ai.gpu_available else "💻 Running on CPU"
            ttk.Label(gpu_frame, text=gpu_status,
                     font=('Segoe UI', 9, 'italic'), foreground='green').pack(anchor=tk.W)

            # Distraction triggers display
            ttk.Label(gpu_frame, text="🎯 Common Distraction Triggers:",
                     font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))

            self.triggers_text = tk.Text(gpu_frame, height=4, wrap=tk.WORD,
                                        font=('Segoe UI', 9), bg='#fff9e6', relief=tk.FLAT)
            self.triggers_text.pack(fill=tk.X, pady=5)

            # Mood analysis
            ttk.Label(gpu_frame, text="😊 Recent Focus Quality:",
                     font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))

            self.mood_text = tk.Text(gpu_frame, height=3, wrap=tk.WORD,
                                    font=('Segoe UI', 9), bg='#e6f7ff', relief=tk.FLAT)
            self.mood_text.pack(fill=tk.X, pady=5)

        # Initial data refresh
        self.refresh_ai_data()

    # === Timer Tab Methods ===

    def check_admin_status(self) -> None:
        """Check and display admin status."""
        if self.blocker.is_admin():
            self.admin_label.config(text="✅ Admin", foreground='green')
        else:
            self.admin_label.config(text="⚠ Not Admin", foreground='red')

    def set_quick_time(self, minutes: int) -> None:
        """Set quick timer values."""
        self.hours_var.set(str(minutes // 60))
        self.minutes_var.set(str(minutes % 60))

    def start_session(self) -> None:
        """Start a focus session."""
        try:
            hours = int(self.hours_var.get())
            minutes = int(self.minutes_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid time values")
            return

        total_minutes = hours * 60 + minutes
        if total_minutes <= 0:
            messagebox.showerror("Error", "Please set a time greater than 0")
            return

        # Set mode
        self.blocker.mode = self.mode_var.get()
        
        # Handle Pomodoro mode specially
        if self.blocker.mode == BlockMode.POMODORO:
            # Reset Pomodoro state
            self.pomodoro_is_break = False
            self.pomodoro_session_count = 0
            self.pomodoro_total_work_time = 0
            
            # Use Pomodoro work duration instead of user-specified time
            total_seconds = self.blocker.pomodoro_work * 60
            
            success, message = self.blocker.block_sites(duration_seconds=total_seconds)
            if not success:
                messagebox.showerror("Error", message)
                return
            
            with self._timer_lock:
                self.remaining_seconds = total_seconds
                self.timer_running = True
                self.session_start_time = time.time()
            
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="🍅 WORK #1", foreground='red')
            
            threading.Thread(target=self.run_timer, daemon=True).start()
            
            messagebox.showinfo(
                "Pomodoro Started! 🍅",
                f"Starting Pomodoro session:\n"
                f"• Work: {self.blocker.pomodoro_work} min\n"
                f"• Break: {self.blocker.pomodoro_break} min\n"
                f"• Long break: {self.blocker.pomodoro_long_break} min (every {self.blocker.pomodoro_sessions_before_long} sessions)\n\n"
                "Stay focused! 💪"
            )
            return

        # Block sites (pass duration for crash recovery)
        total_seconds = total_minutes * 60
        success, message = self.blocker.block_sites(duration_seconds=total_seconds)
        if not success:
            messagebox.showerror("Error", message)
            return

        # Start timer
        with self._timer_lock:
            self.remaining_seconds = total_seconds
            self.timer_running = True
            self.session_start_time = time.time()

        # Update UI
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        mode_text = {"normal": "BLOCKING", "strict": "STRICT MODE 🔐",
                     "pomodoro": "POMODORO 🍅"}.get(self.blocker.mode, "BLOCKING")
        self.status_label.config(text=f"🔒 {mode_text}", foreground='red')

        # Start timer thread
        threading.Thread(target=self.run_timer, daemon=True).start()

        sites_count = len(self.blocker.get_effective_blacklist())
        messagebox.showinfo(
            "Focus Session",
            f"Blocking {sites_count} sites for {hours}h {minutes}m\nStay focused! 💪")

    def run_timer(self) -> None:
        """Run the countdown timer."""
        # Initialize check-in tracking at session start
        self.last_checkin_time = time.time()
        
        while True:
            with self._timer_lock:
                if not self.timer_running:
                    break

                current_seconds = self.remaining_seconds

                if current_seconds <= 0:
                    # Timer finished - trigger completion
                    self.timer_running = False
                    break

                h = current_seconds // 3600
                m = (current_seconds % 3600) // 60
                s = current_seconds % 60
                time_str = f"{h:02d}:{m:02d}:{s:02d}"
                self.remaining_seconds = current_seconds - 1

            try:
                self.root.after(0, lambda t=time_str: self.timer_display.config(text=t))
            except tk.TclError:
                break
            
            # Check if it's time for a priority check-in
            self._check_priority_checkin()

            time.sleep(1)

        # Timer loop ended - check if we should complete the session
        # This runs in the background thread, so we need to schedule on main thread
        with self._timer_lock:
            should_complete = (self.remaining_seconds <= 0)

        if should_complete:
            try:
                # Schedule session completion on main thread
                # Use after_idle to ensure it runs when main thread is ready
                self.root.after(0, self._trigger_session_complete)
            except tk.TclError:
                pass

    def _trigger_session_complete(self):
        """Wrapper to safely trigger session completion from main thread"""
        try:
            # Update display to 00:00:00 first
            self.timer_display.config(text="00:00:00")
            # Then complete the session
            self.session_complete()
        except Exception as e:
            logging.error(f"Error in session completion: {e}", exc_info=True)

    def _check_priority_checkin(self):
        """Check if it's time to show a priority check-in dialog."""
        # Skip if check-ins are disabled or during Pomodoro breaks
        if not self.blocker.priority_checkin_enabled:
            return
        if self.blocker.mode == BlockMode.POMODORO and self.pomodoro_is_break:
            return
        if self.checkin_dialog_open:
            return
        
        # Check if enough time has passed since last check-in
        interval_seconds = self.blocker.priority_checkin_interval * 60
        elapsed_since_checkin = time.time() - (self.last_checkin_time or time.time())
        
        if elapsed_since_checkin >= interval_seconds:
            # Get today's priorities
            today = datetime.now().strftime("%A")
            today_priorities = []
            
            for priority in self.blocker.priorities:
                title = priority.get("title", "").strip()
                days = priority.get("days", [])
                
                if title and (not days or today in days):
                    today_priorities.append(priority)
            
            # Calculate session time in minutes
            session_minutes = int((time.time() - self.session_start_time) // 60) if self.session_start_time else 0
            
            # Only show check-in if there are priorities for today
            if today_priorities:
                self.checkin_dialog_open = True
                try:
                    self.root.after(0, lambda p=today_priorities, m=session_minutes: 
                                   self._show_checkin_dialog(p, m))
                except tk.TclError:
                    pass
            
            # Reset the timer regardless
            self.last_checkin_time = time.time()
    
    def _show_checkin_dialog(self, today_priorities: list, session_minutes: int = 0):
        """Show the priority check-in dialog on the main thread."""
        try:
            PriorityCheckinDialog(self.root, self.blocker, today_priorities, session_minutes)
        except Exception as e:
            logging.error(f"Error showing check-in dialog: {e}", exc_info=True)
        finally:
            self.checkin_dialog_open = False

    def session_complete(self):
        """Handle session completion"""
        elapsed = int(time.time() - self.session_start_time) if self.session_start_time else 0
        
        # Handle Pomodoro mode specially
        if self.blocker.mode == BlockMode.POMODORO:
            self._handle_pomodoro_complete(elapsed)
            return
        
        self.blocker.update_stats(elapsed, completed=True)

        # Use _stop_session_internal to bypass password check and avoid double stats update
        self._stop_session_internal()
        self.timer_display.config(text="00:00:00")
        self.update_stats_display()

        # Play completion sound
        self._play_notification_sound()

        # Refresh AI data after completing session
        if AI_AVAILABLE:
            self.refresh_ai_data()

        # Show AI-powered session completion dialog
        if LOCAL_AI_AVAILABLE:
            self.show_ai_session_complete(elapsed)
        else:
            messagebox.showinfo("Complete!", "🎉 Focus session complete!\nGreat job staying focused!")
        
        # Show priority time logging dialog if user has priorities for today
        session_minutes = elapsed // 60
        if session_minutes > 0:
            self._show_priority_time_log_dialog(session_minutes)
    
    def _show_priority_time_log_dialog(self, session_minutes: int):
        """Show the priority time logging dialog after a focus session."""
        today = datetime.now().strftime("%A")
        
        # Check if there are priorities for today
        today_priorities = []
        for i, priority in enumerate(self.blocker.priorities):
            title = priority.get("title", "").strip()
            days = priority.get("days", [])
            planned = priority.get("planned_minutes", 0)
            
            # Include priority if it has a title and either no days set or today is selected
            if title and (not days or today in days):
                today_priorities.append(i)
        
        # Only show dialog if there are priorities with planned time for today
        if today_priorities:
            PriorityTimeLogDialog(self.root, self.blocker, session_minutes)
    
    def _handle_pomodoro_complete(self, elapsed: int):
        """Handle Pomodoro work/break cycle transitions"""
        if self.pomodoro_is_break:
            # Break is over, start next work session
            self.pomodoro_is_break = False
            self._play_notification_sound()
            
            # Unblock sites during work
            self.blocker.unblock_sites(force=True)
            
            if messagebox.askyesno("Break Over! 🍅", 
                                   f"Break time is over!\n\n"
                                   f"Sessions completed: {self.pomodoro_session_count}\n"
                                   f"Total focus time: {self.pomodoro_total_work_time // 60} min\n\n"
                                   "Ready for another focus session?"):
                self._start_pomodoro_work()
            else:
                self._end_pomodoro_session()
        else:
            # Work session completed
            self.pomodoro_session_count += 1
            self.pomodoro_total_work_time += elapsed
            self.blocker.update_stats(elapsed, completed=True)
            
            self._play_notification_sound()
            
            # Unblock sites during break
            self.blocker.unblock_sites(force=True)
            
            # Determine break length
            sessions_before_long = self.blocker.pomodoro_sessions_before_long
            if self.pomodoro_session_count % sessions_before_long == 0:
                break_minutes = self.blocker.pomodoro_long_break
                break_type = "Long Break"
            else:
                break_minutes = self.blocker.pomodoro_break
                break_type = "Short Break"
            
            response = messagebox.askyesno(
                f"Work Complete! 🍅 {break_type}",
                f"Great work! Session #{self.pomodoro_session_count} complete!\n\n"
                f"Time for a {break_minutes}-minute {break_type.lower()}.\n\n"
                "Start break timer?"
            )
            
            if response:
                self._start_pomodoro_break(break_minutes)
            else:
                self._end_pomodoro_session()
    
    def _start_pomodoro_work(self):
        """Start a Pomodoro work session"""
        work_minutes = self.blocker.pomodoro_work
        total_seconds = work_minutes * 60
        
        # Block sites during work
        success, message = self.blocker.block_sites(duration_seconds=total_seconds)
        if not success:
            messagebox.showerror("Error", message)
            self._end_pomodoro_session()
            return
        
        with self._timer_lock:
            self.remaining_seconds = total_seconds
            self.timer_running = True
            self.session_start_time = time.time()
        
        self.pomodoro_is_break = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"🍅 WORK #{self.pomodoro_session_count + 1}", foreground='red')
        
        threading.Thread(target=self.run_timer, daemon=True).start()
    
    def _start_pomodoro_break(self, break_minutes: int):
        """Start a Pomodoro break period"""
        total_seconds = break_minutes * 60
        
        with self._timer_lock:
            self.remaining_seconds = total_seconds
            self.timer_running = True
            self.session_start_time = time.time()
        
        self.pomodoro_is_break = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="☕ BREAK TIME", foreground='green')
        
        threading.Thread(target=self.run_timer, daemon=True).start()
    
    def _end_pomodoro_session(self):
        """End the entire Pomodoro session"""
        total_work = self.pomodoro_total_work_time
        sessions = self.pomodoro_session_count
        
        # Reset Pomodoro state
        self.pomodoro_is_break = False
        self.pomodoro_session_count = 0
        self.pomodoro_total_work_time = 0
        
        # Reset UI
        with self._timer_lock:
            self.timer_running = False
            self.remaining_seconds = 0
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.timer_display.config(text="00:00:00")
        self.status_label.config(text="Ready to focus", foreground='black')
        
        self.update_stats_display()
        
        if AI_AVAILABLE:
            self.refresh_ai_data()
        
        if sessions > 0:
            messagebox.showinfo(
                "Pomodoro Complete! 🍅",
                f"Great Pomodoro session!\n\n"
                f"Work sessions: {sessions}\n"
                f"Total focus time: {total_work // 60} minutes\n\n"
                "Keep up the great work!"
            )
            
            # Show priority time logging dialog for Pomodoro work time
            work_minutes = total_work // 60
            if work_minutes > 0:
                self._show_priority_time_log_dialog(work_minutes)
    
    def _play_notification_sound(self):
        """Play a notification sound"""
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass  # Sound not critical

    def show_ai_session_complete(self, session_duration):
        """AI-powered session completion with notes and analysis"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Session Complete! 🎉")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()

        # Congratulations
        ttk.Label(dialog, text="🎉 Great work!",
                 font=('Segoe UI', 16, 'bold')).pack(pady=(20, 5))

        ttk.Label(dialog, text=f"You focused for {session_duration // 60} minutes",
                 font=('Segoe UI', 11)).pack(pady=(0, 20))

        # Session notes section
        notes_frame = ttk.LabelFrame(dialog, text="📝 How was your focus? (optional)", padding="15")
        notes_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        ttk.Label(notes_frame, text="Rate your session or add notes:",
                 font=('Segoe UI', 9)).pack(anchor=tk.W)

        # Quick rating buttons
        rating_frame = ttk.Frame(notes_frame)
        rating_frame.pack(fill=tk.X, pady=10)

        selected_rating = tk.StringVar(value="")

        ratings = [
            ("😫 Struggled", "Struggled to concentrate, many distractions"),
            ("😐 Okay", "Decent session, some distractions"),
            ("😊 Good", "Good session, stayed mostly focused"),
            ("🌟 Excellent", "Amazing session! In the zone!")
        ]

        for emoji, description in ratings:
            btn = ttk.Button(rating_frame, text=emoji, width=10,
                           command=lambda d=description: selected_rating.set(d))
            btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Free-form notes
        ttk.Label(notes_frame, text="Or write your own notes:",
                 font=('Segoe UI', 9)).pack(anchor=tk.W, pady=(10, 5))

        notes_text = tk.Text(notes_frame, height=5, wrap=tk.WORD, font=('Segoe UI', 9))
        notes_text.pack(fill=tk.BOTH, expand=True)

        # AI Analysis result display
        analysis_label = ttk.Label(notes_frame, text="",
                                   font=('Segoe UI', 9, 'italic'),
                                   foreground='#0066cc')
        analysis_label.pack(pady=5)

        # AI suggestion display
        suggestion_text = tk.Text(dialog, height=3, wrap=tk.WORD,
                                 font=('Segoe UI', 9), bg='#f0f0f0', relief=tk.FLAT)
        suggestion_text.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Initialize local AI (method only called when LOCAL_AI_AVAILABLE is True)
        if not hasattr(self, 'local_ai'):
            self.local_ai = LocalAI()  # type: ignore[misc]

        # Generate break suggestions
        suggestions = self.local_ai.suggest_break_activity(
            session_duration // 60,
            None
        )
        suggestion_text.insert('1.0', "💡 Suggested break activities:\n")
        for i, sug in enumerate(suggestions, 1):
            suggestion_text.insert(tk.END, f"  {i}. {sug}\n")
        suggestion_text.config(state=tk.DISABLED)

        def analyze_and_save():
            """Analyze notes with AI and save"""
            note = notes_text.get('1.0', tk.END).strip()
            if not note and selected_rating.get():
                note = selected_rating.get()

            if note:
                # AI sentiment analysis
                analysis = self.local_ai.analyze_focus_quality(note)
                if analysis:
                    analysis_label.config(text=f"🧠 AI: {analysis['interpretation']}")

                # Save note to stats
                self._save_session_note(note, analysis)

            dialog.destroy()

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Button(btn_frame, text="💾 Save & Continue",
                  command=analyze_and_save).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text="Skip",
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def _save_session_note(self, note: str, analysis: Optional[Dict[str, Any]]) -> None:
        """Save session note with AI analysis to stats."""
        today = datetime.now().strftime("%Y-%m-%d")

        if 'session_notes' not in self.blocker.stats:
            self.blocker.stats['session_notes'] = {}

        if today not in self.blocker.stats['session_notes']:
            self.blocker.stats['session_notes'][today] = []

        session_record = {
            'timestamp': datetime.now().isoformat(),
            'note': note,
            'sentiment': analysis['sentiment'] if analysis else 'NEUTRAL',
            'confidence': analysis['confidence'] if analysis else 0.5,
            'interpretation': analysis['interpretation'] if analysis else ''
        }

        self.blocker.stats['session_notes'][today].append(session_record)
        self.blocker.save_stats()

        logging.info(f"Saved session note: {note[:50]}...")

    def _stop_session_internal(self):
        """Internal method to stop session without password check or stats update.
        Used when timer completes naturally."""
        with self._timer_lock:
            self.timer_running = False
            self.remaining_seconds = 0

        # Force unblock - bypass password since timer completed naturally
        success, message = self.blocker.unblock_sites(force=True)

        # Update UI
        try:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Ready to focus", foreground='black')
            self.timer_display.config(text="00:00:00")
        except tk.TclError:
            pass

    def stop_session(self, show_message: bool = True) -> None:
        """Stop the focus session (manual stop by user)."""
        # Check strict mode - only for manual stops
        if self.blocker.mode == BlockMode.STRICT and self.blocker.is_blocking:
            if self.blocker.password_hash:
                password = simpledialog.askstring("Strict Mode", "Enter password to stop:", show='*')
                if not self.blocker.verify_password(password or ""):
                    messagebox.showerror("Error", "Incorrect password!")
                    return

        elapsed = int(time.time() - self.session_start_time) if self.session_start_time else 0

        with self._timer_lock:
            was_running = self.timer_running
            self.timer_running = False
            self.remaining_seconds = 0

        success, message = self.blocker.unblock_sites()

        # Only update stats for manual stops where session actually ran
        if was_running and elapsed > 60:  # Only count if > 1 minute
            self.blocker.update_stats(elapsed, completed=False)

        # Update UI
        try:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="Ready to focus", foreground='black')
            self.timer_display.config(text="00:00:00")
            self.update_stats_display()
        except tk.TclError:
            pass

        if show_message:
            messagebox.showinfo("Stopped", "Session stopped. Sites unblocked.")

    def update_stats_display(self):
        """Update statistics displays"""
        stats = self.blocker.get_stats_summary()

        # Quick stats on timer tab
        today = datetime.now().strftime("%Y-%m-%d")
        daily = self.blocker.stats.get("daily_stats", {}).get(today, {})
        today_time = daily.get("focus_time", 0) // 60
        today_sessions = daily.get("sessions", 0)

        self.quick_stats_label.config(
            text=f"Today: {today_time} min focused • {today_sessions} sessions • 🔥 {stats['current_streak']} day streak"
        )

        # Stats tab
        if hasattr(self, 'stat_labels'):
            self.stat_labels['total_hours'].config(text=f"{stats['total_hours']}h")
            self.stat_labels['sessions'].config(text=str(stats['sessions_completed']))
            self.stat_labels['streak'].config(text=f"{stats['current_streak']} days")
            self.stat_labels['best_streak'].config(text=f"{stats['best_streak']} days")

            self.update_week_chart()
        
        # Update focus goals dashboard
        if hasattr(self, 'weekly_goal_progress'):
            self.update_focus_goals_display()
        
        # Update bypass stats
        if BYPASS_LOGGER_AVAILABLE and hasattr(self, 'bypass_session_label'):
            self.refresh_bypass_stats()

    def update_week_chart(self):
        """Update the weekly chart"""
        self.week_chart.config(state=tk.NORMAL)
        self.week_chart.delete(1.0, tk.END)

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        today = datetime.now()

        chart_lines = []
        max_time = 1

        # Get data for last 7 days
        week_data = []
        for i in range(6, -1, -1):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            daily = self.blocker.stats.get("daily_stats", {}).get(date, {})
            time_min = daily.get("focus_time", 0) // 60
            week_data.append((date, time_min))
            max_time = max(max_time, time_min)

        # Create ASCII bar chart
        chart_lines.append("Focus time this week:\n\n")

        for date_str, time_min in week_data:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = days[date.weekday()]
            bar_len = int((time_min / max_time) * 30) if max_time > 0 else 0
            bar = "█" * bar_len + "░" * (30 - bar_len)
            chart_lines.append(f"  {day_name}  {bar} {time_min}m\n")

        total_week = sum(t for _, t in week_data)
        chart_lines.append(f"\n  Total this week: {total_week} minutes ({total_week // 60}h {total_week % 60}m)")

        self.week_chart.insert(tk.END, "".join(chart_lines))
        self.week_chart.config(state=tk.DISABLED)

    # === Sites Tab Methods ===

    def update_site_lists(self):
        """Update both site listboxes"""
        self.site_listbox.delete(0, tk.END)
        for site in sorted(self.blocker.blacklist):
            self.site_listbox.insert(tk.END, site)

        self.whitelist_listbox.delete(0, tk.END)
        for site in sorted(self.blocker.whitelist):
            self.whitelist_listbox.insert(tk.END, site)

    def add_site(self):
        """Add a site to blacklist"""
        site = self.site_entry.get().strip()
        if site and self.blocker.add_site(site):
            self.update_site_lists()
            self.site_entry.delete(0, tk.END)
            self.update_total_sites_count()
        elif site:
            messagebox.showinfo("Info", "Site already in list or invalid")

    def remove_site(self):
        """Remove selected sites from blacklist"""
        selection = self.site_listbox.curselection()
        for i in reversed(selection):
            site = self.site_listbox.get(i)
            self.blocker.remove_site(site)
        self.update_site_lists()
        self.update_total_sites_count()

    def add_whitelist(self):
        """Add a site to whitelist"""
        site = self.whitelist_entry.get().strip()
        if site and self.blocker.add_to_whitelist(site):
            self.update_site_lists()
            self.whitelist_entry.delete(0, tk.END)
            self.update_total_sites_count()

    def remove_whitelist(self):
        """Remove selected site from whitelist"""
        selection = self.whitelist_listbox.curselection()
        if selection:
            site = self.whitelist_listbox.get(selection[0])
            self.blocker.remove_from_whitelist(site)
            self.update_site_lists()
            self.update_total_sites_count()

    def import_sites(self):
        """Import sites from file"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if filepath and self.blocker.import_config(filepath):
            self.update_site_lists()
            self.update_total_sites_count()
            messagebox.showinfo("Success", "Sites imported successfully!")

    def export_sites(self):
        """Export sites to file"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")])
        if filepath and self.blocker.export_config(filepath):
            messagebox.showinfo("Success", "Sites exported successfully!")

    # === Categories Tab Methods ===

    def toggle_category(self, category: str) -> None:
        """Toggle a category on/off."""
        self.blocker.categories_enabled[category] = self.category_vars[category].get()
        self.blocker.save_config()
        self.update_total_sites_count()

    def show_category_sites(self, category: str) -> None:
        """Show sites in a category."""
        sites = SITE_CATEGORIES.get(category, [])
        site_list = "\n".join(sorted(set(s.replace("www.", "") for s in sites)))
        messagebox.showinfo(f"{category} Sites", site_list)

    def update_total_sites_count(self):
        """Update total blocked sites count"""
        total = len(self.blocker.get_effective_blacklist())
        self.total_sites_label.config(text=f"Total sites to block: {total}")

    # === Schedule Tab Methods ===

    def update_schedule_list(self):
        """Update the schedule treeview"""
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for schedule in self.blocker.schedules:
            day_names = ", ".join(days[d] for d in sorted(schedule.get('days', [])))
            time_range = f"{schedule.get('start_time', '')} - {schedule.get('end_time', '')}"
            status = "✅ Active" if schedule.get('enabled', True) else "⏸ Paused"

            self.schedule_tree.insert('', tk.END, iid=schedule['id'],
                                      values=(day_names, time_range, status))

    def add_schedule(self):
        """Add a new schedule"""
        days = [i for i, var in enumerate(self.day_vars) if var.get()]
        if not days:
            messagebox.showerror("Error", "Select at least one day")
            return

        start_time = f"{int(self.start_hour.get()):02d}:{int(self.start_min.get()):02d}"
        end_time = f"{int(self.end_hour.get()):02d}:{int(self.end_min.get()):02d}"

        self.blocker.add_schedule(days, start_time, end_time)
        self.update_schedule_list()

    def toggle_schedule(self):
        """Toggle selected schedule"""
        selection = self.schedule_tree.selection()
        if selection:
            self.blocker.toggle_schedule(selection[0])
            self.update_schedule_list()

    def delete_schedule(self):
        """Delete selected schedule"""
        selection = self.schedule_tree.selection()
        if selection:
            self.blocker.remove_schedule(selection[0])
            self.update_schedule_list()

    def check_scheduled_blocking(self):
        """Check if we should be blocking based on schedule"""
        if self.blocker.is_scheduled_block_time() and not self.blocker.is_blocking:
            if messagebox.askyesno("Scheduled Block",
                                   "You have a blocking schedule active now.\nStart blocking?"):
                self.blocker.mode = BlockMode.SCHEDULED
                # Use 8 hours as default for scheduled blocks
                self.blocker.block_sites(duration_seconds=8 * 60 * 60)
                self.status_label.config(text="🔒 SCHEDULED BLOCK", foreground='red')
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)

        # Check again in 60 seconds
        self.root.after(60000, self.check_scheduled_blocking)

    # === Stats Tab Methods ===

    def reset_stats(self):
        """Reset all statistics"""
        if messagebox.askyesno("Reset Stats", "Are you sure you want to reset all statistics?"):
            self.blocker.stats = self.blocker._default_stats()
            self.blocker.save_stats()
            self.update_stats_display()

    def load_focus_goals(self):
        """Load focus goals from config"""
        # Weekly and monthly goals stored in blocker stats
        self.weekly_goal_target = self.blocker.stats.get("weekly_goal_target", 10)
        self.monthly_goal_target = self.blocker.stats.get("monthly_goal_target", 40)
        
        self.weekly_goal_var.set(str(self.weekly_goal_target))
        self.monthly_goal_var.set(str(self.monthly_goal_target))

    def set_focus_goal(self, goal_type: str):
        """Set a weekly or monthly focus goal"""
        try:
            if goal_type == "weekly":
                target = int(self.weekly_goal_var.get())
                self.weekly_goal_target = target
                self.blocker.stats["weekly_goal_target"] = target
            else:
                target = int(self.monthly_goal_var.get())
                self.monthly_goal_target = target
                self.blocker.stats["monthly_goal_target"] = target
            
            self.blocker.save_stats()
            self.update_focus_goals_display()
            messagebox.showinfo("Goal Set", f"{goal_type.capitalize()} goal set to {target} hours!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")

    def update_focus_goals_display(self):
        """Update the focus goals dashboard display"""
        from datetime import datetime, timedelta
        
        # Get current date info
        today = datetime.now()
        
        # Calculate weekly progress
        week_start = today - timedelta(days=today.weekday())
        week_start_str = week_start.strftime("%Y-%m-%d")
        
        weekly_hours = 0
        for date_str, daily_data in self.blocker.stats.get("daily_stats", {}).items():
            if date_str >= week_start_str:
                weekly_hours += daily_data.get("focus_time", 0) / 3600
        
        weekly_target = getattr(self, 'weekly_goal_target', 10)
        weekly_percent = min(100, (weekly_hours / weekly_target * 100)) if weekly_target > 0 else 0
        
        self.weekly_goal_progress['value'] = weekly_percent
        self.weekly_goal_label.config(
            text=f"{weekly_hours:.1f}h / {weekly_target}h ({weekly_percent:.0f}%)"
        )
        
        # Calculate monthly progress
        month_start_str = today.strftime("%Y-%m-01")
        
        monthly_hours = 0
        for date_str, daily_data in self.blocker.stats.get("daily_stats", {}).items():
            if date_str >= month_start_str:
                monthly_hours += daily_data.get("focus_time", 0) / 3600
        
        monthly_target = getattr(self, 'monthly_goal_target', 40)
        monthly_percent = min(100, (monthly_hours / monthly_target * 100)) if monthly_target > 0 else 0
        
        self.monthly_goal_progress['value'] = monthly_percent
        self.monthly_goal_label.config(
            text=f"{monthly_hours:.1f}h / {monthly_target}h ({monthly_percent:.0f}%)"
        )

    def refresh_bypass_stats(self):
        """Refresh the bypass attempt statistics display"""
        if not BYPASS_LOGGER_AVAILABLE:
            return
        
        stats = self.blocker.get_bypass_statistics()
        if not stats:
            return
        
        # Current session
        session_count = stats.get("current_session", 0)
        session_sites = stats.get("session_sites", [])
        
        self.bypass_session_label.config(
            text=f"Current Session: {session_count} attempts"
        )
        
        if session_sites:
            sites_text = ", ".join(session_sites[:5])
            if len(session_sites) > 5:
                sites_text += f" (+{len(session_sites) - 5} more)"
            self.bypass_session_sites.config(text=f"Sites: {sites_text}")
        else:
            self.bypass_session_sites.config(text="No sites accessed")
        
        # All-time stats
        self.bypass_total_label.config(
            text=f"Total attempts: {stats.get('total_attempts', 0)}"
        )
        
        # Top sites
        top_sites = stats.get("top_sites", [])[:3]
        if top_sites:
            sites_str = ", ".join(f"{site} ({count})" for site, count in top_sites)
            self.bypass_top_sites.config(text=f"Top distractions: {sites_str}")
        else:
            self.bypass_top_sites.config(text="Top distractions: -")
        
        # Peak hours
        peak_hours = stats.get("peak_hours", [])[:3]
        if peak_hours:
            hours_str = ", ".join(f"{int(h)}:00" for h, _ in peak_hours)
            self.bypass_peak_hours.config(text=f"Peak hours: {hours_str}")
        else:
            self.bypass_peak_hours.config(text="Peak hours: -")
        
        # Insights
        insights = self.blocker.get_bypass_insights()
        self.bypass_insights_text.config(state=tk.NORMAL)
        self.bypass_insights_text.delete('1.0', tk.END)
        if insights:
            self.bypass_insights_text.insert('1.0', "\n".join(insights))
        else:
            self.bypass_insights_text.insert('1.0', "No insights yet. Keep focusing!")
        self.bypass_insights_text.config(state=tk.DISABLED)

    # === Settings Tab Methods ===

    def open_priorities_dialog(self):
        """Open the My Priorities dialog."""
        def on_start_priority(priority_title):
            """Callback when user clicks Start Working on Priority."""
            # Switch to Timer tab and start a session
            self.notebook.select(self.timer_tab)
            messagebox.showinfo("Priority Session", 
                               f"Starting focus session for:\n\n\"{priority_title}\"\n\n"
                               "Set your desired duration and click Start Focus!",
                               parent=self.root)
        
        dialog = PrioritiesDialog(self.root, self.blocker, on_start_priority)
        dialog.wait_for_close()
        
        # Sync the startup checkbox state
        self.priorities_startup_var.set(self.blocker.show_priorities_on_startup)
        
        # Refresh ADHD Buster stats in case check-in settings changed
        self.refresh_buster_stats()

    def open_adhd_buster(self):
        """Open the ADHD Buster character and inventory dialog."""
        ADHDBusterDialog(self.root, self.blocker)
        # Refresh stats after closing
        self.refresh_buster_stats()
    
    def refresh_buster_stats(self):
        """Refresh the ADHD Buster stats display in the Stats tab."""
        try:
            total_items = len(self.blocker.adhd_buster.get("inventory", []))
            equipped_count = len([s for s in self.blocker.adhd_buster.get("equipped", {}).values() if s])
            total_collected = self.blocker.adhd_buster.get("total_collected", total_items)
            luck = self.blocker.adhd_buster.get("luck_bonus", 0)
            max_power = 8 * RARITY_POWER["Legendary"]
            
            stats_text = f"📦 {total_items} in bag  |  ⚔ {equipped_count}/8 equipped  |  🎁 {total_collected} lifetime"
            if luck > 0:
                stats_text += f"  |  🍀 +{luck}% luck"
            self.buster_stats_label.config(text=stats_text)
            
            # Update power level and title
            power = calculate_character_power(self.blocker.adhd_buster)
            if power >= 1500:
                title = "🌟 Focus Deity"
                next_tier = None
                next_power = max_power
            elif power >= 1000:
                title = "⚡ Legendary Champion"
                next_tier = "Focus Deity"
                next_power = 1500
            elif power >= 600:
                title = "🔥 Epic Warrior"
                next_tier = "Legendary Champion"
                next_power = 1000
            elif power >= 300:
                title = "💪 Seasoned Fighter"
                next_tier = "Epic Warrior"
                next_power = 600
            elif power >= 100:
                title = "🛡️ Apprentice"
                next_tier = "Seasoned Fighter"
                next_power = 300
            else:
                title = "🌱 Novice"
                next_tier = "Apprentice"
                next_power = 100
            
            self.buster_power_label.config(text=f"⚔ Power: {power}  {title}")
            
            # Update progress to next tier
            if next_tier:
                progress_pct = int((power / next_power) * 100)
                progress_text = f"📈 {power}/{next_power} to {next_tier} ({progress_pct}%)"
            else:
                progress_text = f"👑 MAX TIER ACHIEVED! ({power}/{max_power} power)"
            self.buster_progress_label.config(text=progress_text)
            
        except (AttributeError, tk.TclError):
            pass

    def toggle_priorities_startup(self):
        """Toggle whether to show priorities dialog on startup."""
        self.blocker.show_priorities_on_startup = self.priorities_startup_var.get()
        self.blocker.save_config()

    def set_password(self):
        """Set strict mode password"""
        password = simpledialog.askstring("Set Password", "Enter new password:", show='*')
        if password:
            confirm = simpledialog.askstring("Confirm", "Confirm password:", show='*')
            if password == confirm:
                self.blocker.set_password(password)
                self.update_password_status()
                messagebox.showinfo("Success", "Password set!")
            else:
                messagebox.showerror("Error", "Passwords don't match")

    def remove_password(self):
        """Remove password"""
        if self.blocker.password_hash:
            password = simpledialog.askstring("Remove Password", "Enter current password:", show='*')
            if self.blocker.verify_password(password or ""):
                self.blocker.set_password(None)
                self.update_password_status()
            else:
                messagebox.showerror("Error", "Incorrect password")
        else:
            messagebox.showinfo("Info", "No password set")

    def update_password_status(self):
        """Update password status label"""
        if self.blocker.password_hash:
            self.pwd_status.config(text="🔐 Password is set", foreground='green')
        else:
            self.pwd_status.config(text="No password set", foreground='gray')

    def save_pomodoro_settings(self):
        """Save Pomodoro settings"""
        try:
            self.blocker.pomodoro_work = int(self.pomo_vars['pomodoro_work'].get())
            self.blocker.pomodoro_break = int(self.pomo_vars['pomodoro_break'].get())
            self.blocker.pomodoro_long_break = int(self.pomo_vars['pomodoro_long_break'].get())
            self.blocker.save_config()
            messagebox.showinfo("Success", "Pomodoro settings saved!")
        except ValueError:
            messagebox.showerror("Error", "Invalid values")

    def create_full_backup(self):
        """Create a full backup of all app data"""
        import json
        from pathlib import Path
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save Full Backup"
        )
        
        if not filepath:
            return
        
        try:
            backup_data = {
                'backup_version': '2.1.0',
                'backup_date': datetime.now().isoformat(),
                'config': {
                    'blacklist': self.blocker.blacklist,
                    'whitelist': self.blocker.whitelist,
                    'categories_enabled': self.blocker.categories_enabled,
                    'pomodoro_work': self.blocker.pomodoro_work,
                    'pomodoro_break': self.blocker.pomodoro_break,
                    'pomodoro_long_break': self.blocker.pomodoro_long_break,
                    'schedules': self.blocker.schedules,
                },
                'stats': self.blocker.stats,
            }
            
            # Include goals if available
            if AI_AVAILABLE and hasattr(self, 'goals'):
                backup_data['goals'] = self.goals.goals
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
            
            messagebox.showinfo(
                "Backup Complete",
                f"Full backup saved successfully!\n\nIncludes:\n"
                f"• {len(self.blocker.blacklist)} blocked sites\n"
                f"• {len(self.blocker.whitelist)} whitelisted sites\n"
                f"• {self.blocker.stats.get('sessions_completed', 0)} session records\n"
                f"• All settings and schedules"
            )
        except Exception as e:
            messagebox.showerror("Backup Failed", f"Could not create backup:\n{e}")

    def restore_full_backup(self):
        """Restore from a full backup"""
        import json
        
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Select Backup File"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Validate backup
            if 'backup_version' not in backup_data:
                messagebox.showerror("Invalid Backup", "This doesn't appear to be a valid backup file.")
                return
            
            backup_date = backup_data.get('backup_date', 'Unknown')
            
            # Confirm restore
            if not messagebox.askyesno(
                "Confirm Restore",
                f"Restore backup from {backup_date}?\n\n"
                "⚠️ This will replace ALL your current data:\n"
                "• Blocked/whitelisted sites\n"
                "• Statistics and achievements\n"
                "• Schedules and settings\n"
                "• Goals\n\n"
                "Continue?"
            ):
                return
            
            # Restore config
            config = backup_data.get('config', {})
            if config:
                self.blocker.blacklist = config.get('blacklist', self.blocker.blacklist)
                self.blocker.whitelist = config.get('whitelist', self.blocker.whitelist)
                self.blocker.categories_enabled = config.get('categories_enabled', self.blocker.categories_enabled)
                self.blocker.pomodoro_work = config.get('pomodoro_work', self.blocker.pomodoro_work)
                self.blocker.pomodoro_break = config.get('pomodoro_break', self.blocker.pomodoro_break)
                self.blocker.pomodoro_long_break = config.get('pomodoro_long_break', self.blocker.pomodoro_long_break)
                self.blocker.schedules = config.get('schedules', self.blocker.schedules)
                self.blocker.save_config()
            
            # Restore stats
            stats = backup_data.get('stats', {})
            if stats:
                self.blocker.stats = {**self.blocker._default_stats(), **stats}
                self.blocker.save_stats()
            
            # Restore goals
            if AI_AVAILABLE and hasattr(self, 'goals') and 'goals' in backup_data:
                self.goals.goals = backup_data['goals']
                self.goals.save_goals()
            
            # Refresh UI
            self.update_site_lists()
            self.update_schedule_list()
            self.update_stats_display()
            self.update_total_sites_count()
            
            # Update Pomodoro settings display
            self.pomo_vars['pomodoro_work'].set(str(self.blocker.pomodoro_work))
            self.pomo_vars['pomodoro_break'].set(str(self.blocker.pomodoro_break))
            self.pomo_vars['pomodoro_long_break'].set(str(self.blocker.pomodoro_long_break))
            
            if AI_AVAILABLE:
                self.refresh_ai_data()
            
            messagebox.showinfo("Restore Complete", "Backup restored successfully!")
            
        except json.JSONDecodeError:
            messagebox.showerror("Invalid File", "The file is not valid JSON.")
        except Exception as e:
            messagebox.showerror("Restore Failed", f"Could not restore backup:\n{e}")

    def check_crash_recovery(self) -> None:
        """Check for orphaned sessions from a previous crash and offer recovery."""
        orphaned = self.blocker.check_orphaned_session()
        
        if orphaned is None:
            return
        
        # Format the crash info for the user
        if orphaned.get("unknown"):
            crash_info = "An unknown previous session"
        else:
            start_time = orphaned.get("start_time", "unknown")
            mode = orphaned.get("mode", "unknown")
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(start_time)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                time_str = start_time
            crash_info = f"A session started at {time_str} (mode: {mode})"
        
        # Ask user what to do
        response = messagebox.askyesnocancel(
            "Crash Recovery Detected",
            f"⚠️ {crash_info} did not shut down properly.\n\n"
            "Some websites may still be blocked.\n\n"
            "Would you like to:\n"
            "• YES - Remove all blocks and clean up\n"
            "• NO - Keep the blocks (I'll manage manually)\n"
            "• CANCEL - Decide later",
            icon='warning'
        )
        
        if response is True:  # YES - Clean up
            success, message = self.blocker.recover_from_crash()
            if success:
                messagebox.showinfo(
                    "Recovery Complete",
                    "✅ All blocks have been removed.\n\n"
                    "Your browser should now be able to access all websites."
                )
            else:
                messagebox.showerror(
                    "Recovery Failed",
                    f"Could not clean up: {message}\n\n"
                    "Try using 'Emergency Cleanup' in Settings tab."
                )
        elif response is False:  # NO - Keep blocks
            # Just clear the session state file so we don't ask again
            self.blocker.clear_session_state()
            messagebox.showinfo(
                "Blocks Retained",
                "The blocks have been kept.\n\n"
                "Use 'Emergency Cleanup' in Settings tab when you want to remove them."
            )
        # If CANCEL (None), do nothing - will ask again next time

    def check_priorities_on_startup(self) -> None:
        """Check if priorities dialog should be shown on startup."""
        if not self.blocker.show_priorities_on_startup:
            return
        
        # Check if today is a day with any priorities
        today = datetime.now().strftime("%A")
        has_priority_today = False
        
        for priority in self.blocker.priorities:
            title = priority.get("title", "").strip()
            days = priority.get("days", [])
            
            # Show if priority has a title and either no days specified or today is selected
            if title and (not days or today in days):
                has_priority_today = True
                break
        
        # Show dialog if there are priorities for today, or if no priorities set yet
        if has_priority_today or not any(p.get("title", "").strip() for p in self.blocker.priorities):
            def on_start_priority(priority_title):
                """Callback when user clicks Start Working on Priority."""
                self.notebook.select(self.timer_tab)
                messagebox.showinfo("Priority Session", 
                                   f"Starting focus session for:\n\n\"{priority_title}\"\n\n"
                                   "Set your desired duration and click Start Focus!",
                                   parent=self.root)
            
            dialog = PrioritiesDialog(self.root, self.blocker, on_start_priority)
            dialog.wait_for_close()

    def emergency_cleanup_action(self):
        """Emergency cleanup - remove all blocks and clean system"""
        confirm = messagebox.askyesno(
            "Emergency Cleanup",
            "This will:\n\n"
            "• Stop any active blocking session\n"
            "• Remove ALL blocked sites from your system\n"
            "• Clear DNS cache\n"
            "• Bypass any password protection\n\n"
            "Use this if websites remain blocked after the app closes.\n\n"
            "Continue?",
            icon='warning'
        )

        if confirm:
            # Stop the timer if running
            with self._timer_lock:
                self.timer_running = False
                self.remaining_seconds = 0

            # Run the cleanup
            success, message = self.blocker.emergency_cleanup()

            # Update UI
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.timer_display.config(text="00:00:00")
            self.status_label.config(text="✅ Ready", foreground='green')

            if success:
                messagebox.showinfo("Cleanup Complete", message + "\n\nAll websites should now be accessible.")
            else:
                messagebox.showerror("Cleanup Failed", message)

    # === AI Tab Methods ===

    def refresh_ai_data(self):
        """Refresh all AI-powered insights and data"""
        if not AI_AVAILABLE:
            return

        self.refresh_ai_insights()
        self.update_achievements()
        self.update_daily_challenge()
        self.update_goals_display()
        self.update_ai_stats()

        # Update GPU AI insights if available
        if LOCAL_AI_AVAILABLE and hasattr(self, 'local_ai'):
            self.update_gpu_insights()

    def refresh_ai_insights(self):
        """Refresh AI insights and recommendations"""
        if not AI_AVAILABLE:
            return

        self.insights_text.delete('1.0', tk.END)

        # Get insights and recommendations
        insights = self.analyzer.generate_insights()
        recommendations = self.analyzer.get_recommendations()

        if insights:
            self.insights_text.insert(tk.END, "💡 INSIGHTS:\n", 'header')
            for insight in insights:
                # Handle both dict and string insights
                if isinstance(insight, dict):
                    title = insight.get('title', '')
                    message = insight.get('message', '')
                    self.insights_text.insert(tk.END, f"  • {title}: {message}\n")
                else:
                    self.insights_text.insert(tk.END, f"  • {insight}\n")
            self.insights_text.insert(tk.END, "\n")

        if recommendations:
            self.insights_text.insert(tk.END, "🎯 RECOMMENDATIONS:\n", 'header')
            for rec in recommendations:
                # Handle both dict and string recommendations
                if isinstance(rec, dict):
                    suggestion = rec.get('suggestion', '')
                    reason = rec.get('reason', '')
                    self.insights_text.insert(tk.END, f"  • {suggestion} ({reason})\n")
                else:
                    self.insights_text.insert(tk.END, f"  • {rec}\n")

        if not insights and not recommendations:
            self.insights_text.insert(tk.END, "Complete a few sessions to unlock AI insights!\n", 'info')

        # Configure text tags
        self.insights_text.tag_config('header', font=('Segoe UI', 9, 'bold'))
        self.insights_text.tag_config('info', font=('Segoe UI', 9, 'italic'), foreground='gray')
        self.insights_text.config(state=tk.DISABLED)

    def update_achievements(self):
        """Update achievement progress bars"""
        if not AI_AVAILABLE:
            return

        progress_data = self.gamification.check_achievements()

        for ach_id, widgets in self.achievement_widgets.items():
            if ach_id in progress_data:
                progress = progress_data[ach_id]
                current = progress['current']
                target = progress['target']
                unlocked = progress['unlocked']

                percentage = min(100, int((current / target) * 100)) if target > 0 else 0

                widgets['progress_bar']['value'] = percentage
                widgets['progress_label'].config(text=f"{percentage}%")

                if unlocked:
                    widgets['card'].config(relief=tk.RAISED, style='success.TFrame')
                    widgets['icon'].config(font=('Segoe UI', 18))
                    widgets['name'].config(foreground='green')
                else:
                    widgets['card'].config(relief=tk.RIDGE)
                    widgets['icon'].config(font=('Segoe UI', 16))
                    widgets['name'].config(foreground='black')

    def update_daily_challenge(self):
        """Update daily challenge display"""
        if not AI_AVAILABLE:
            return

        challenge = self.gamification.get_daily_challenge()

        self.challenge_title.config(text=challenge['title'])
        self.challenge_desc.config(text=challenge['description'])

        current = challenge['progress']['current']
        target = challenge['progress']['target']

        self.challenge_progress['maximum'] = target
        self.challenge_progress['value'] = current
        self.challenge_status.config(text=f"{current}/{target}")

    def update_goals_display(self):
        """Update active goals listbox"""
        if not AI_AVAILABLE:
            return

        self.goals_listbox.delete(0, tk.END)

        active_goals = self.goals.get_active_goals()

        if not active_goals:
            self.goals_listbox.insert(tk.END, "No active goals. Add one to get started!")
        else:
            for goal in active_goals:
                progress = goal.get('progress', 0)
                target = goal.get('target', 100)
                percentage = int((progress / target) * 100) if target > 0 else 0

                display = f"{goal['title']} - {percentage}% ({progress}/{target})"
                self.goals_listbox.insert(tk.END, display)

    def update_ai_stats(self):
        """Update AI-powered statistics display"""
        if not AI_AVAILABLE:
            return

        self.ai_stats_text.delete('1.0', tk.END)

        # Get peak productivity hours
        peak_hours = self.analyzer.get_peak_productivity_hours()
        if peak_hours:
            self.ai_stats_text.insert(tk.END, f"🌟 Peak Hours: {', '.join(peak_hours)}\n")

        # Get optimal session length
        optimal = self.analyzer.predict_optimal_session_length()
        if optimal:
            self.ai_stats_text.insert(tk.END, f"⏱  Optimal Session: {optimal} minutes\n")

        # Get distraction patterns
        patterns = self.analyzer.get_distraction_patterns()
        if patterns and isinstance(patterns, dict):
            self.ai_stats_text.insert(tk.END, "\n🔍 Distraction Patterns:\n")
            for key, value in list(patterns.items())[:3]:  # Show top 3
                self.ai_stats_text.insert(tk.END, f"   • {key}: {value}\n")

        self.ai_stats_text.config(state=tk.DISABLED)

    def update_gpu_insights(self):
        """Update GPU AI-powered insights"""
        if not LOCAL_AI_AVAILABLE or not hasattr(self, 'triggers_text'):
            return

        # Get session notes from stats
        session_notes = []
        for date, notes_list in self.blocker.stats.get('session_notes', {}).items():
            for note_data in notes_list:
                session_notes.append(note_data.get('note', ''))

        # Update distraction triggers
        self.triggers_text.delete('1.0', tk.END)
        if len(session_notes) >= 3:
            triggers = self.local_ai.detect_distraction_triggers(session_notes[-10:])  # Last 10 notes
            if triggers and isinstance(triggers, list) and len(triggers) > 0:
                for trigger in triggers[:3]:  # Top 3
                    if isinstance(trigger, dict):
                        self.triggers_text.insert(tk.END,
                            f"🎯 {trigger.get('trigger', 'Unknown').upper()} ({trigger.get('frequency', 0)}x)\n")
                        self.triggers_text.insert(tk.END,
                            f"   💡 {trigger.get('recommendation', 'No recommendation')}\n\n")
                    else:
                        self.triggers_text.insert(tk.END, f"• {trigger}\n")
            else:
                self.triggers_text.insert(tk.END, "No common distraction patterns detected yet.\n")
        else:
            self.triggers_text.insert(tk.END,
                "Complete 3+ sessions with notes to detect patterns.\n")
        self.triggers_text.config(state=tk.DISABLED)

        # Update mood analysis
        self.mood_text.delete('1.0', tk.END)
        if session_notes:
            recent_notes = session_notes[-5:]  # Last 5 sessions
            positive_count = 0
            negative_count = 0

            for note in recent_notes:
                result = self.local_ai.analyze_focus_quality(note)
                if result:
                    if result['sentiment'] == 'POSITIVE':
                        positive_count += 1
                    else:
                        negative_count += 1

            total = positive_count + negative_count
            if total > 0:
                positive_pct = int((positive_count / total) * 100)

                if positive_pct >= 80:
                    mood_msg = f"🌟 Excellent! {positive_pct}% of recent sessions were highly focused"
                elif positive_pct >= 60:
                    mood_msg = f"😊 Good trend: {positive_pct}% positive sessions"
                elif positive_pct >= 40:
                    mood_msg = f"😐 Mixed results: {positive_pct}% positive, {100-positive_pct}% challenging"
                else:
                    mood_msg = (
                        f"⚠️ Struggling: Only {positive_pct}% positive sessions\n"
                        f"   💡 Try shorter sessions or different times"
                    )

                self.mood_text.insert(tk.END, mood_msg)
            else:
                self.mood_text.insert(tk.END, "Add session notes to track focus quality trends")
        else:
            self.mood_text.insert(tk.END, "No session notes yet. Complete a session to start!")

        self.mood_text.config(state=tk.DISABLED)

    def add_goal_dialog(self):
        """Show dialog to add a new goal"""
        if not AI_AVAILABLE:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Goal")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # Goal title
        ttk.Label(dialog, text="Goal Title:", font=('Segoe UI', 10)).pack(pady=(20, 5), padx=20, anchor=tk.W)
        title_entry = ttk.Entry(dialog, width=40, font=('Segoe UI', 10))
        title_entry.pack(padx=20, pady=(0, 10))

        # Goal type
        ttk.Label(dialog, text="Goal Type:", font=('Segoe UI', 10)).pack(pady=5, padx=20, anchor=tk.W)
        goal_type = tk.StringVar(value="daily")

        type_frame = ttk.Frame(dialog)
        type_frame.pack(padx=20, pady=(0, 10), anchor=tk.W)

        ttk.Radiobutton(type_frame, text="Daily", value="daily", variable=goal_type).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="Weekly", value="weekly", variable=goal_type).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="Custom", value="custom", variable=goal_type).pack(side=tk.LEFT, padx=5)

        # Target value
        ttk.Label(dialog, text="Target (minutes):", font=('Segoe UI', 10)).pack(pady=5, padx=20, anchor=tk.W)
        target_entry = ttk.Entry(dialog, width=15, font=('Segoe UI', 10))
        target_entry.pack(padx=20, pady=(0, 20), anchor=tk.W)
        target_entry.insert(0, "60")

        def save_goal():
            title = title_entry.get().strip()
            try:
                target = int(target_entry.get())
                if title and target > 0:
                    self.goals.add_goal(title, goal_type.get(), target)
                    self.update_goals_display()
                    dialog.destroy()
                else:
                    messagebox.showerror("Invalid Input", "Please enter a valid title and target.")
            except ValueError:
                messagebox.showerror("Invalid Input", "Target must be a number.")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(padx=20, pady=10)

        ttk.Button(btn_frame, text="Save Goal", command=save_goal).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def complete_selected_goal(self):
        """Mark selected goal as completed"""
        if not AI_AVAILABLE:
            return

        selection = self.goals_listbox.curselection()
        if selection:
            idx = selection[0]
            active_goals = self.goals.get_active_goals()
            if 0 <= idx < len(active_goals):
                goal = active_goals[idx]
                self.goals.complete_goal(goal['id'])
                self.update_goals_display()
                messagebox.showinfo("Goal Completed", f"🎉 Congratulations on completing '{goal['title']}'!")

    def remove_selected_goal(self):
        """Remove selected goal"""
        if not AI_AVAILABLE:
            return

        selection = self.goals_listbox.curselection()
        if selection:
            idx = selection[0]
            active_goals = self.goals.get_active_goals()
            if 0 <= idx < len(active_goals):
                goal = active_goals[idx]
                if messagebox.askyesno("Remove Goal", f"Remove goal '{goal['title']}'?"):
                    # Get all goals and remove the selected one
                    all_goals = self.goals.goals
                    all_goals = [g for g in all_goals if g['id'] != goal['id']]
                    self.goals.goals = all_goals
                    self.goals.save_goals()
                    self.update_goals_display()

    # === Window Management ===

    def _on_minimize(self, event):
        """Handle window minimize event"""
        if not TRAY_AVAILABLE or not self.minimize_to_tray.get():
            return
        
        # Only act if the main window is being minimized (not child dialogs)
        if event.widget != self.root:
            return
        
        # Check if window is actually iconified
        if self.root.state() == 'iconic':
            self.root.withdraw()  # Hide window
            self._show_tray_icon()
    
    def _create_tray_image(self, blocking=False):
        """Create a simple icon image for the tray"""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        if blocking:
            # Red circle when blocking
            draw.ellipse([4, 4, size-4, size-4], fill='#e74c3c', outline='#c0392b', width=2)
            # Lock symbol
            draw.rectangle([20, 30, 44, 50], fill='white')
            draw.arc([24, 18, 40, 34], 0, 180, fill='white', width=4)
        else:
            # Green circle when not blocking
            draw.ellipse([4, 4, size-4, size-4], fill='#2ecc71', outline='#27ae60', width=2)
            # Check mark
            draw.line([(20, 32), (28, 42), (44, 22)], fill='white', width=4)

        return image
    
    def _show_tray_icon(self):
        """Show the system tray icon"""
        if not TRAY_AVAILABLE or self.tray_icon is not None:
            return
        
        def on_show(icon, item):
            icon.stop()
            self.tray_icon = None
            self.root.after(0, self._restore_window)
        
        def on_quit(icon, item):
            icon.stop()
            self.tray_icon = None
            self.root.after(0, self.on_closing)
        
        def get_status():
            if self.timer_running:
                h = self.remaining_seconds // 3600
                m = (self.remaining_seconds % 3600) // 60
                s = self.remaining_seconds % 60
                return f"🔒 Blocking - {h:02d}:{m:02d}:{s:02d}"
            return "Ready"
        
        menu = pystray.Menu(
            pystray.MenuItem(lambda item: get_status(), lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Window", on_show, default=True),
            pystray.MenuItem("Exit", on_quit),
        )
        
        image = self._create_tray_image(self.timer_running)
        self.tray_icon = pystray.Icon(
            "PersonalFreedom",
            image,
            "Personal Freedom - Focus Blocker",
            menu
        )
        
        # Run in background thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def _restore_window(self):
        """Restore the window from system tray"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def on_closing(self) -> None:
        """Handle window close."""
        # Stop tray icon if running
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        
        if self.timer_running:
            if messagebox.askyesno("Confirm Exit", "A session is running!\nStop and exit?"):
                self.stop_session(show_message=False)
                self.root.destroy()
        else:
            self.root.destroy()


def main() -> None:
    """Main entry point for the application."""
    root = tk.Tk()
    app = FocusBlockerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
