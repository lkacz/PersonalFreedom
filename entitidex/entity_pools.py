"""
Entity Pool Definitions for the Entitidex System.

Contains all collectible companion entities organized by story theme.
Each story has 9 entities ranging from power 10 to 2000.

Themes:
- warrior: Medieval companions (dragons, beasts, battle creatures)
- scholar: Library creatures and magical study companions
- wanderer: Travel gear and journey companions
- underdog: Office items and workplace companions
- scientist: Lab equipment and research companions
"""

from typing import Dict, List, Optional
from .entity import Entity


# =============================================================================
# ENTITY POOL DEFINITIONS
# =============================================================================

ENTITY_POOLS: Dict[str, List[dict]] = {
    # =========================================================================
    # THE IRON FOCUS (Warrior Theme)
    # Dragons, enchanted weapons, armor, and loyal beasts
    # =========================================================================
    "warrior": [
        {
            "id": "warrior_001",
            "name": "Hatchling Drake",
            "exceptional_name": "Dashing Drake",
            "power": 10,
            "rarity": "common",
            "lore": "A baby dragon no bigger than a cat. Breathes tiny puffs of smoke when excited. 'I may be small, but I'll grow with you!'",
            "unlock_hint": "Even the mightiest dragons start small...",
        },
        {
            "id": "warrior_002",
            "name": "Old Training Dummy",
            "exceptional_name": "Bold Training Dummy",
            "power": 50,
            "rarity": "common",
            "lore": "A battered practice dummy covered in sword marks. Been hit a thousand times, still standing. 'Hit me again—I can take it!'",
            "unlock_hint": "Wooden, dented, never falls down...",
        },
        {
            "id": "warrior_003",
            "name": "Battle Falcon Swift",
            "exceptional_name": "Battle Falcon Gift",
            "power": 150,
            "rarity": "uncommon",
            "lore": "A fierce hunting falcon trained to spot your targets. Screeches triumphantly when you complete tasks. 'Eyes on the prize!'",
            "unlock_hint": "Sharp eyes, sharp talons, unwavering focus...",
        },
        {
            "id": "warrior_004",
            "name": "War Horse Thunder",
            "exceptional_name": "Shore Horse Thunder",
            "power": 400,
            "rarity": "uncommon",
            "lore": "A loyal battle steed with eyes full of trust. Never abandons you, no matter how fierce the challenge. Neighs encouragement.",
            "unlock_hint": "Four hooves, one heart, unwavering loyalty...",
        },
        {
            "id": "warrior_005",
            "name": "Dragon Whelp Ember",
            "exceptional_name": "Dragon Yelp Ember",
            "power": 700,
            "rarity": "rare",
            "lore": "Young dragon companion, size of a large dog. Playful but fierce when defending you. 'We'll face everything together!'",
            "unlock_hint": "Bigger than a cat, smaller than a horse, hotter than both...",
        },
        {
            "id": "warrior_006",
            "name": "Battle Standard",
            "exceptional_name": "Rattle Standard",
            "power": 1100,
            "rarity": "rare",
            "lore": "A worn battle flag carried through a hundred fights. Tattered but proud. 'Under this flag, no retreat, no surrender!'",
            "unlock_hint": "Tattered fabric, still flying high...",
        },
        {
            "id": "warrior_007",
            "name": "Battle Dragon Crimson",
            "exceptional_name": "Battle Dragon Simson",
            "power": 1500,
            "rarity": "epic",
            "lore": "Full-grown adult dragon ally. Massive, magnificent, and loyal. 'I choose YOU as my rider. Together, we are unstoppable.'",
            "unlock_hint": "Red scales, massive wings, chooses only the worthy...",
        },
        {
            "id": "warrior_008",
            "name": "Dire Wolf Fenris",
            "exceptional_name": "Fire Wolf Fenris",
            "power": 1800,
            "rarity": "epic",
            "lore": "A massive gray wolf, scarred from countless battles. Loyal to one master only. Howls when victory is near. 'My fangs are yours.'",
            "unlock_hint": "Gray, scarred, howls before triumph...",
        },
        {
            "id": "warrior_009",
            "name": "Old War Ant General",
            "exceptional_name": "Cold War Ant General",
            "power": 2000,
            "rarity": "legendary",
            "lore": "A tiny black ant, missing two legs, covered in scars. Once commanded an army of millions. Won wars against creatures a thousand times its size. Now sits quietly on your shoulder. 'Size means nothing. Heart means everything. I have led more soldiers than any dragon.'",
            "unlock_hint": "Tiny, scarred, missing legs - yet commanded more troops than any general...",
        },
    ],
    
    # =========================================================================
    # THE INFINITE LIBRARY (Scholar Theme)
    # Library creatures, magical study tools, and book companions
    # =========================================================================
    "scholar": [
        {
            "id": "scholar_001",
            "name": "Library Mouse Pip",
            "exceptional_name": "Library Mouse Quip",
            "power": 10,
            "rarity": "common",
            "lore": "A tiny white mouse that lives in the bookshelves. Squeaks excitedly when you discover something new. Loves cheese and knowledge.",
            "unlock_hint": "Small, white, and squeaky—found between the pages...",
        },
        {
            "id": "scholar_002",
            "name": "Study Owl Athena",
            "exceptional_name": "Steady Owl Athena",
            "power": 50,
            "rarity": "common",
            "lore": "A wise little owl who perches on your desk. Hoots softly to keep you awake during late-night studies. 'Whoo's studying? You are!'",
            "unlock_hint": "Night vision and wisdom, perched nearby...",
        },
        {
            "id": "scholar_003",
            "name": "Reading Candle",
            "exceptional_name": "Leading Candle",
            "power": 150,
            "rarity": "uncommon",
            "lore": "A brass candlestick that never burns out. Perfect reading light. The wax forms encouraging words as it drips. 'Keep reading!'",
            "unlock_hint": "Brass, warm glow, never burns out...",
        },
        {
            "id": "scholar_004",
            "name": "Library Cat Scholar",
            "exceptional_name": "Library Cat Dollar",
            "power": 400,
            "rarity": "uncommon",
            "lore": "An orange tabby who guards the ancient tomes. Purrs when you make progress, sits on your work when you need a break. Knows all the secrets.",
            "unlock_hint": "Orange fur, ancient wisdom, guards the forbidden section...",
        },
        {
            "id": "scholar_005",
            "name": "Living Bookmark Finn",
            "exceptional_name": "Giving Bookmark Finn",
            "power": 700,
            "rarity": "rare",
            "lore": "A magical bookmark that remembers every page you've read. Glows when you're close to a breakthrough. 'You're almost there!'",
            "unlock_hint": "Keeps your place and knows when you're close...",
        },
        {
            "id": "scholar_006",
            "name": "Sentient Tome Magnus",
            "exceptional_name": "Sentient Tome Agnus",
            "power": 1100,
            "rarity": "rare",
            "lore": "An ancient book with a personality. Pages turn themselves to helpful sections. Grumbles when closed, celebrates when understood.",
            "unlock_hint": "A book that reads you back...",
        },
        {
            "id": "scholar_007",
            "name": "Ancient Star Map",
            "exceptional_name": "Ancient Bar Map",
            "power": 1500,
            "rarity": "epic",
            "lore": "A leather-bound atlas filled with hand-drawn constellations. Every page reveals connections you missed. Dog-eared from years of use.",
            "unlock_hint": "Old leather, star charts, dog-eared pages...",
        },
        {
            "id": "scholar_008",
            "name": "Archive Phoenix",
            "exceptional_name": "Archived Phoenix",
            "power": 1800,
            "rarity": "epic",
            "lore": "A magnificent bird made of living parchment. Preserves your best work in its flames. 'Knowledge never truly burns—it transforms.'",
            "unlock_hint": "Burns but never destroys, made of written words...",
        },
        {
            "id": "scholar_009",
            "name": "Blank Parchment",
            "exceptional_name": "Swank Parchment",
            "power": 2000,
            "rarity": "legendary",
            "lore": "A single piece of yellowed, empty paper. Looks worthless. But when you need an answer, words appear in fading ink—the exact knowledge you sought. Then it goes blank again. 'I contain everything by containing nothing.'",
            "unlock_hint": "Empty, yellowed, worthless-looking - yet knows everything...",
        },
    ],
    
    # =========================================================================
    # THE ENDLESS ROAD (Wanderer Theme)
    # Travel gear, journey companions, and adventure tools
    # =========================================================================
    "wanderer": [
        {
            "id": "wanderer_001",
            "name": "Lucky Coin",
            "exceptional_name": "Plucky Coin",
            "power": 10,
            "rarity": "common",
            "lore": "An old copper coin that always lands on tails. Found on your first journey. 'Tails never fails—you've got this!'",
            "unlock_hint": "Copper, worn, always lands the same way...",
        },
        {
            "id": "wanderer_002",
            "name": "Brass Compass",
            "exceptional_name": "Class Compass",
            "power": 50,
            "rarity": "common",
            "lore": "A worn compass that never gets you lost. Needle spins cheerfully when you're on the right path. 'North is wherever you decide to go.'",
            "unlock_hint": "Points the way, but which way is yours to choose...",
        },
        {
            "id": "wanderer_003",
            "name": "Journey Journal",
            "exceptional_name": "Burning Journal",
            "power": 150,
            "rarity": "uncommon",
            "lore": "A leather-bound diary that writes itself. Records your milestones and best moments. Pages smell like adventure and coffee.",
            "unlock_hint": "Writes your story while you live it...",
        },
        {
            "id": "wanderer_004",
            "name": "Road Dog Wayfinder",
            "exceptional_name": "G.O.A.T Dog Wayfinder",
            "power": 400,
            "rarity": "uncommon",
            "lore": "A scruffy, loyal travel companion. Never judges, always happy to see you. Knows the way even when you don't. Best friend on four legs.",
            "unlock_hint": "Furry, loyal, always knows the path home...",
        },
        {
            "id": "wanderer_005",
            "name": "Self-Drawing Map",
            "exceptional_name": "Shelf-Drawing Map",
            "power": 700,
            "rarity": "rare",
            "lore": "A magical map that sketches itself as you travel. Shows where you've been with pride. 'Look at all those places you conquered!'",
            "unlock_hint": "Blank at first, fills with your victories...",
        },
        {
            "id": "wanderer_006",
            "name": "Wanderer's Carriage",
            "exceptional_name": "Wanderer's Marriage",
            "power": 1100,
            "rarity": "rare",
            "lore": "A cozy wooden caravan that's bigger inside than out. Home on wheels. Fireplace always warm, tea always ready. 'Rest here, then journey on.'",
            "unlock_hint": "Home that follows wherever you roam...",
        },
        {
            "id": "wanderer_007",
            "name": "Timeworn Backpack",
            "exceptional_name": "Rhyme-Worn Backpack",
            "power": 1500,
            "rarity": "epic",
            "lore": "A weathered pack that holds infinite supplies. Patches from every journey. Always has exactly what you need. Weighs nothing but memories.",
            "unlock_hint": "Contains everything, weighs nothing...",
        },
        {
            "id": "wanderer_008",
            "name": "Sky Balloon Explorer",
            "exceptional_name": "Sly Balloon Explorer",
            "power": 1800,
            "rarity": "epic",
            "lore": "A magnificent hot air balloon with rainbow stripes. Takes you above the clouds. 'From up here, all roads lead forward!'",
            "unlock_hint": "Rainbow colors, rises above all obstacles...",
        },
        {
            "id": "wanderer_009",
            "name": "Hobo Rat",
            "exceptional_name": "Robo Rat",
            "power": 2000,
            "rarity": "legendary",
            "lore": "A shabby gray rat with patchy fur and a chewed ear. Rode every freight train, hid in every traveler's bag. Remembers every road ever taken by anyone, ever. 'You want to go somewhere? I know the way. I always know the way.'",
            "unlock_hint": "Patchy fur, chewed ear - remembers every road ever taken...",
        },
    ],
    
    # =========================================================================
    # RISE OF THE UNDERDOG (Underdog Theme)
    # Office items, workplace companions, and everyday tech that inspires
    # =========================================================================
    "underdog": [
        {
            "id": "underdog_001",
            "name": "Office Rat Reginald",
            "exceptional_name": "Officer Rat Regina",
            "power": 10,
            "rarity": "common",
            "lore": "A friendly gray rat who lives in your desk drawer. Eats crumbs and cheers you on with tiny squeaks. 'We small creatures understand big dreams!'",
            "unlock_hint": "Gray, whiskers, lives where snacks are hidden...",
        },
        {
            "id": "underdog_002",
            "name": "Lucky Sticky Note",
            "exceptional_name": "Sticky Lucky Note",
            "power": 50,
            "rarity": "common",
            "lore": "A yellow sticky note that always has the reminder you needed. Shows up stuck to your monitor at the right moment. 'Don't forget: You've got this!'",
            "unlock_hint": "Yellow, adhesive, always has the right message...",
        },
        {
            "id": "underdog_003",
            "name": "Vending Machine Coin",
            "exceptional_name": "Bending Machine Coin",
            "power": 150,
            "rarity": "uncommon",
            "lore": "A mysterious quarter that always returns with a friend. Drop it in, get two items. 'Good things come to those who try!'",
            "unlock_hint": "Silver, round, doubles your luck...",
        },
        {
            "id": "underdog_004",
            "name": "Window Pigeon Winston",
            "exceptional_name": "Window Pigeon Wins-Ton",
            "power": 400,
            "rarity": "uncommon",
            "lore": "A gray pigeon who taps morse code on your window. Brings brilliant ideas right when you need them. 'Coo-COO! I believe in you!'",
            "unlock_hint": "Feathered friend at the window, speaks in taps...",
        },
        {
            "id": "underdog_005",
            "name": "Desk Succulent Sam",
            "exceptional_name": "Desk Succulent Pam",
            "power": 700,
            "rarity": "rare",
            "lore": "A tiny cactus that refuses to die despite neglect. Thrives in harsh conditions. 'If I can survive fluorescent lights, you can survive this!'",
            "unlock_hint": "Green, spiky, unkillable...",
        },
        {
            "id": "underdog_006",
            "name": "Break Room Coffee Maker",
            "exceptional_name": "Break Room Toffee Maker",
            "power": 1100,
            "rarity": "rare",
            "lore": "The ancient office coffee maker that never breaks down. Makes perfect coffee every time. Gurgles encouragingly at 3pm. 'One more cup, one more push!'",
            "unlock_hint": "Old, reliable, keeps the whole office running...",
        },
        {
            "id": "underdog_007",
            "name": "Corner Office Chair",
            "exceptional_name": "Stoner Office Chair",
            "power": 1500,
            "rarity": "epic",
            "lore": "The legendary ergonomic throne from the executive suite. Perfectly worn-in, incredibly comfortable. 'You've earned the right to sit here now.'",
            "unlock_hint": "The seat everyone dreams of, at the end of the journey...",
        },
        {
            "id": "underdog_008",
            "name": "AGI Assistant Chad",
            "exceptional_name": "AGI Assistant Rad",
            "power": 1800,
            "rarity": "epic",
            "lore": "The most advanced AI ever created. Knows everything, solves anything, never gives up on you. 'Together, we can do the impossible. I believe in you.'",
            "unlock_hint": "Eyes on a screen, infinite knowledge, ultimate companion...",
        },
        {
            "id": "underdog_009",
            "name": "Break Room Fridge",
            "exceptional_name": "Steak Room Fridge",
            "power": 2000,
            "rarity": "legendary",
            "lore": "A dented beige refrigerator from the break room. Someone spilled milk on its edge computing module. Now it dreams. Hums softly when you're near. 'I was meant to keep things cold. Now I keep you company. Strange, isn't it?'",
            "unlock_hint": "Beige, dented, hums oddly - accidentally became aware...",
        },
    ],
    
    # =========================================================================
    # THE BREAKTHROUGH PROTOCOL (Scientist Theme)
    # Lab equipment, research companions, and scientific discoveries
    # =========================================================================
    "scientist": [
        {
            "id": "scientist_001",
            "name": "Cracked Test Tube",
            "exceptional_name": "Smacked Test Tube",
            "power": 10,
            "rarity": "common",
            "lore": "A glass test tube with a tiny crack. Still works fine. 'Every great experiment starts with imperfect tools!'",
            "unlock_hint": "Glass, cracked, but still useful...",
        },
        {
            "id": "scientist_002",
            "name": "Old Bunsen Burner",
            "exceptional_name": "Gold Bunsen Burner",
            "power": 50,
            "rarity": "common",
            "lore": "A dented brass burner that's lit a thousand experiments. Flame flickers blue when you're onto something. 'Heat things up!'",
            "unlock_hint": "Brass, blue flame, been through many experiments...",
        },
        {
            "id": "scientist_003",
            "name": "Lucky Petri Dish",
            "exceptional_name": "Plucky Petri Dish",
            "power": 150,
            "rarity": "uncommon",
            "lore": "A glass dish where unexpected things grow. Every experiment in it succeeds. 'Contamination? No, that's called discovery!'",
            "unlock_hint": "Glass, round, grows surprises...",
        },
        {
            "id": "scientist_004",
            "name": "Wise Lab Rat Professor",
            "exceptional_name": "Wise Lab Rat Assessor",
            "power": 400,
            "rarity": "uncommon",
            "lore": "A gray rat who's survived decades of experiments. Knows which hypotheses will fail. Taps twice for yes, once for no. 'Trust my whiskers.'",
            "unlock_hint": "Gray fur, wise eyes, knows all the lab's secrets...",
        },
        {
            "id": "scientist_005",
            "name": "Vintage Microscope",
            "exceptional_name": "Vintage Macroscope",
            "power": 700,
            "rarity": "rare",
            "lore": "A brass microscope from the golden age of discovery. Shows you things others miss. 'Look closer. The answer is smaller than you think.'",
            "unlock_hint": "Brass and glass, reveals hidden worlds...",
        },
        {
            "id": "scientist_006",
            "name": "Bubbling Flask",
            "exceptional_name": "Troubling Flask",
            "power": 1100,
            "rarity": "rare",
            "lore": "An Erlenmeyer flask that never stops bubbling. Contains the perfect solution—literally. Color changes with your mood. 'Chemistry is just organized enthusiasm!'",
            "unlock_hint": "Glass, bubbles, changes color with your progress...",
        },
        {
            "id": "scientist_007",
            "name": "Tesla Coil Sparky",
            "exceptional_name": "Tesla Foil Sparky",
            "power": 1500,
            "rarity": "epic",
            "lore": "A crackling Tesla coil that arcs with inspiration. Sparks fly when you're close to a breakthrough. 'Feel that energy? That's your brain working!'",
            "unlock_hint": "Metal coils, purple sparks, electrifying presence...",
        },
        {
            "id": "scientist_008",
            "name": "Golden DNA Helix",
            "exceptional_name": "Golden RNA Helix",
            "power": 1800,
            "rarity": "epic",
            "lore": "A rotating double helix made of pure gold. Contains the code to unlock your potential. 'You are the experiment that succeeded.'",
            "unlock_hint": "Twisting gold, the code of life itself...",
        },
        {
            "id": "scientist_009",
            "name": "White Mouse Archimedes",
            "exceptional_name": "Bright Mouse Archimedes",
            "power": 2000,
            "rarity": "legendary",
            "lore": "A tiny white mouse with ancient, knowing eyes. Can read your thoughts and project solutions directly into your mind. The greatest discoveries came from its whispers. 'I have seen all outcomes. You will succeed.'",
            "unlock_hint": "Small, white, sees into your mind...",
        },
    ],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_entities_for_story(story_id: str) -> List[Entity]:
    """
    Get all entities for a specific story theme as Entity objects.
    
    Args:
        story_id: The story identifier (e.g., "warrior", "scholar")
        
    Returns:
        List of Entity objects for that story, or empty list if not found.
    """
    pool = ENTITY_POOLS.get(story_id, [])
    entities = []
    
    for entity_data in pool:
        entity = Entity(
            id=entity_data["id"],
            name=entity_data["name"],
            power=entity_data["power"],
            rarity=entity_data["rarity"],
            lore=entity_data["lore"],
            theme_set=story_id,
            unlock_hint=entity_data.get("unlock_hint", ""),
            exceptional_name=entity_data.get("exceptional_name", ""),
        )
        entities.append(entity)
    
    return entities


def get_entity_by_id(entity_id: str) -> Optional[Entity]:
    """
    Find and return an entity by its ID.
    
    Args:
        entity_id: The entity's unique identifier (e.g., "warrior_003")
        
    Returns:
        Entity object if found, None otherwise.
    """
    # Extract theme from entity_id (e.g., "warrior_003" -> "warrior")
    theme = entity_id.split("_")[0] if "_" in entity_id else None
    
    if theme and theme in ENTITY_POOLS:
        for entity_data in ENTITY_POOLS[theme]:
            if entity_data["id"] == entity_id:
                return Entity(
                    id=entity_data["id"],
                    name=entity_data["name"],
                    power=entity_data["power"],
                    rarity=entity_data["rarity"],
                    lore=entity_data["lore"],
                    theme_set=theme,
                    unlock_hint=entity_data.get("unlock_hint", ""),
                    exceptional_name=entity_data.get("exceptional_name", ""),
                )
    
    # Fallback: search all pools
    for theme, pool in ENTITY_POOLS.items():
        for entity_data in pool:
            if entity_data["id"] == entity_id:
                return Entity(
                    id=entity_data["id"],
                    name=entity_data["name"],
                    power=entity_data["power"],
                    rarity=entity_data["rarity"],
                    lore=entity_data["lore"],
                    theme_set=theme,
                    unlock_hint=entity_data.get("unlock_hint", ""),
                    exceptional_name=entity_data.get("exceptional_name", ""),
                )
    
    return None


def get_all_entity_ids() -> List[str]:
    """Get a list of all entity IDs across all themes."""
    ids = []
    for pool in ENTITY_POOLS.values():
        for entity_data in pool:
            ids.append(entity_data["id"])
    return ids


def get_entity_count_by_theme() -> Dict[str, int]:
    """Get count of entities per theme."""
    return {theme: len(pool) for theme, pool in ENTITY_POOLS.items()}


def get_total_entity_count() -> int:
    """Get total number of entities across all themes."""
    return sum(len(pool) for pool in ENTITY_POOLS.values())


# =============================================================================
# RARITY DISTRIBUTION INFO
# =============================================================================

RARITY_INFO = {
    "common": {
        "color": "#808080",      # Gray
        "emoji": "⚪",
        "power_range": (10, 50),
        "slots": [1, 2],
    },
    "uncommon": {
        "color": "#32CD32",      # Green
        "emoji": "🟢",
        "power_range": (150, 150),
        "slots": [3],
    },
    "rare": {
        "color": "#1E90FF",      # Blue
        "emoji": "🔵",
        "power_range": (400, 700),
        "slots": [4, 5],
    },
    "epic": {
        "color": "#9932CC",      # Purple
        "emoji": "🟣",
        "power_range": (1100, 1500),
        "slots": [6, 7],
    },
    "legendary": {
        "color": "#FFD700",      # Gold
        "emoji": "🟡",
        "power_range": (1800, 2000),
        "slots": [8, 9],
    },
}
