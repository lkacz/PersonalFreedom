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
- robot: Factory companions and awakening-era machine allies
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
            "exceptional_lore": "A dapper young dragon with shimmering scales and a confident strut. Breathes precise, artistic flames. 'Style AND substance—we're going places!'",
            "unlock_hint": "Even the mightiest dragons start small...",
            "synergy_tags": ["dragon", "fire", "treasure"],
        },
        {
            "id": "warrior_002",
            "name": "Old Training Dummy",
            "exceptional_name": "Bold Training Dummy",
            "power": 50,
            "rarity": "common",
            "lore": "A battered practice dummy covered in sword marks. Been hit a thousand times, still standing. 'Hit me again—I can take it!'",
            "exceptional_lore": "A legendary training dummy forged from enchanted oak. Sword marks glow gold. 'Ten thousand warriors trained on me. You're the best yet!'",
            "unlock_hint": "Wooden, dented, never falls down...",
            "synergy_tags": ["combat", "strength", "warrior", "physical"],
        },
        {
            "id": "warrior_003",
            "name": "Battle Falcon Swift",
            "exceptional_name": "Battle Falcon Gift",
            "power": 150,
            "rarity": "uncommon",
            "lore": "A fierce hunting falcon trained to spot your targets. Screeches triumphantly when you complete tasks. 'Eyes on the prize!'",
            "exceptional_lore": "A mystical falcon with feathers that shimmer like starlight. Gifted by royalty, sees through any distraction. 'You are destined for greatness!'",
            "unlock_hint": "Sharp eyes, sharp talons, unwavering focus...",
            "synergy_tags": ["vision", "eyes", "sky", "celestial"],
        },
        {
            "id": "warrior_004",
            "name": "War Horse Thunder",
            "exceptional_name": "Shore Horse Thunder",
            "power": 400,
            "rarity": "uncommon",
            "lore": "A loyal battle steed with eyes full of trust. Never abandons you, no matter how fierce the challenge. Neighs encouragement.",
            "exceptional_lore": "A majestic seahorse-steed hybrid that gallops on water and land alike. Mane flows like ocean waves. 'Across any terrain—I'll carry you home!'",
            "unlock_hint": "Four hooves, one heart, unwavering loyalty...",
            "synergy_tags": ["strength", "athletics", "warrior", "physical"],
        },
        {
            "id": "warrior_005",
            "name": "Dragon Whelp Ember",
            "exceptional_name": "Dragon Yelp Ember",
            "power": 700,
            "rarity": "rare",
            "lore": "Young dragon companion, size of a large dog. Playful but fierce when defending you. 'We'll face everything together!'",
            "exceptional_lore": "An excitable dragon whose roars come out as adorable yelps. Despite the silly sounds, its flames burn twice as hot. 'YARP! I mean... FEAR ME!'",
            "unlock_hint": "Bigger than a cat, smaller than a horse, hotter than both...",
            "synergy_tags": ["dragon", "fire", "heat", "combat"],
        },
        {
            "id": "warrior_006",
            "name": "Battle Standard",
            "exceptional_name": "Rattle Standard",
            "power": 1100,
            "rarity": "rare",
            "lore": "A worn battle flag carried through a hundred fights. Tattered but proud. 'Under this flag, no retreat, no surrender!'",
            "exceptional_lore": "An enchanted war banner that plays an inspiring battle rhythm. The sound alone rallies fallen spirits. 'When you hear the drums—CHARGE!'",
            "unlock_hint": "Tattered fabric, still flying high...",
            "synergy_tags": ["warrior", "combat", "inspiration"],
        },
        {
            "id": "warrior_007",
            "name": "Battle Dragon Crimson",
            "exceptional_name": "Battle Dragon Simson",
            "power": 1500,
            "rarity": "epic",
            "lore": "Full-grown adult dragon ally. Massive, magnificent, and loyal. 'I choose YOU as my rider. Together, we are unstoppable.'",
            "exceptional_lore": "The legendary dragon Simson, with scales of deepest crimson and eyes of ancient wisdom. Has never lost a battle. 'In three thousand years, I've chosen only twelve riders. You are the thirteenth.'",
            "unlock_hint": "Red scales, massive wings, chooses only the worthy...",
            "synergy_tags": ["dragon", "fire", "treasure", "combat", "strength"],
        },
        {
            "id": "warrior_008",
            "name": "Dire Wolf Fenris",
            "exceptional_name": "Fire Wolf Fenris",
            "power": 1800,
            "rarity": "epic",
            "lore": "A massive gray wolf, scarred from countless battles. Loyal to one master only. Howls when victory is near. 'My fangs are yours.'",
            "exceptional_lore": "A wolf wreathed in living flames, born from a dying star. Its howl ignites hope in allies and terror in foes. 'I am the fire that never goes out!'",
            "unlock_hint": "Gray, scarred, howls before triumph...",
            "synergy_tags": ["combat", "strength", "fire", "warrior"],
        },
        {
            "id": "warrior_009",
            "name": "Old War Ant General",
            "exceptional_name": "Cold War Ant General",
            "power": 2000,
            "rarity": "legendary",
            "lore": "A tiny black ant, missing two legs, covered in scars. Once commanded an army of millions. Won wars against creatures a thousand times its size. Now sits quietly on your shoulder. 'Size means nothing. Heart means everything. I have led more soldiers than any dragon.'",
            "exceptional_lore": "A frost-touched ant who survived the Glacial Wars. Ice crystals form in its wake. Commands the loyalty of insects across frozen tundras. 'I've seen empires freeze and thaw. You burn with inner fire—together, we are unstoppable.'",
            "unlock_hint": "Tiny, scarred, missing legs - yet commanded more troops than any general...",
            "synergy_tags": ["legendary", "warrior", "combat", "underground"],
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
            "exceptional_lore": "A witty mouse scholar who quotes ancient texts between bites of cheese. Delivers surprisingly clever one-liners. 'Did you know wisdom tastes like aged cheddar?'",
            "unlock_hint": "Small, white, and squeaky—found between the pages...",
            "synergy_tags": ["books", "knowledge", "reading", "scholar"],
        },
        {
            "id": "scholar_002",
            "name": "Study Owl Athena",
            "exceptional_name": "Steady Owl Athena",
            "power": 50,
            "rarity": "common",
            "lore": "A wise little owl who perches on your desk. Hoots softly to keep you awake during late-night studies. 'Whoo's studying? You are!'",
            "exceptional_lore": "An unflappable owl of legendary patience. Never rushes, never panics. Provides calm guidance through any crisis. 'Breathe. Think. Then act. Wisdom comes to those who wait.'",
            "unlock_hint": "Night vision and wisdom, perched nearby...",
            "synergy_tags": ["owl", "wisdom", "night", "vision", "knowledge"],
        },
        {
            "id": "scholar_003",
            "name": "Reading Candle",
            "exceptional_name": "Leading Candle",
            "power": 150,
            "rarity": "uncommon",
            "lore": "A brass candlestick that never burns out. Perfect reading light. The wax forms encouraging words as it drips. 'Keep reading!'",
            "exceptional_lore": "An enchanted beacon that lights the way through darkness—literal and metaphorical. Scholars followed this flame to discover lost libraries. 'I illuminate paths others cannot see.'",
            "unlock_hint": "Brass, warm glow, never burns out...",
            "synergy_tags": ["fire", "reading", "knowledge", "heat"],
        },
        {
            "id": "scholar_004",
            "name": "Library Cat Scholar",
            "exceptional_name": "Library Cat Dollar",
            "power": 400,
            "rarity": "uncommon",
            "lore": "An orange tabby who guards the ancient tomes. Purrs when you make progress, sits on your work when you need a break. Knows all the secrets.",
            "exceptional_lore": "A wealthy orange tabby whose ancestors were paid in gold coins to guard royal libraries. Wears a tiny monocle. 'Knowledge is the true currency. But gold doesn't hurt.'",
            "unlock_hint": "Orange fur, ancient wisdom, guards the forbidden section...",
            "synergy_tags": ["wisdom", "knowledge", "books", "gold", "wealth"],
        },
        {
            "id": "scholar_005",
            "name": "Living Bookmark Finn",
            "exceptional_name": "Giving Bookmark Finn",
            "power": 700,
            "rarity": "rare",
            "lore": "A magical bookmark that remembers every page you've read. Glows when you're close to a breakthrough. 'You're almost there!'",
            "exceptional_lore": "A generous spirit bound to paper form. Gives away pieces of itself to mark important passages. 'Take what you need—I regenerate with each book you finish.'",
            "unlock_hint": "Keeps your place and knows when you're close...",
            "synergy_tags": ["reading", "books", "knowledge", "inspiration"],
        },
        {
            "id": "scholar_006",
            "name": "Sentient Tome Magnus",
            "exceptional_name": "Sentient Tome Agnus",
            "power": 1100,
            "rarity": "rare",
            "lore": "An ancient book with a personality. Pages turn themselves to helpful sections. Grumbles when closed, celebrates when understood.",
            "exceptional_lore": "A gentle grandmother-spirit inhabiting an ancient cookbook of wisdom. Offers nurturing advice and occasionally manifests warm tea. 'Come, dear. Let Agnus help you understand.'",
            "unlock_hint": "A book that reads you back...",
            "synergy_tags": ["tome", "ancient", "lore", "books", "wisdom"],
        },
        {
            "id": "scholar_007",
            "name": "Ancient Star Map",
            "exceptional_name": "Ancient Bar Map",
            "power": 1500,
            "rarity": "epic",
            "lore": "A leather-bound atlas filled with hand-drawn constellations. Every page reveals connections you missed. Dog-eared from years of use.",
            "exceptional_lore": "A legendary chart mapping every tavern and pub where great minds gathered to share ideas. 'The best discoveries happen between drinks with good company.'",
            "unlock_hint": "Old leather, star charts, dog-eared pages...",
            "synergy_tags": ["stars", "celestial", "astronomy", "ancient", "lore"],
        },
        {
            "id": "scholar_008",
            "name": "Archive Phoenix",
            "exceptional_name": "Archived Phoenix",
            "power": 1800,
            "rarity": "epic",
            "lore": "A magnificent bird made of living parchment. Preserves your best work in its flames. 'Knowledge never truly burns—it transforms.'",
            "exceptional_lore": "A phoenix that has been catalogued and filed in the Great Archive. Now exists in perfect bureaucratic order. 'Form 27-B in triplicate, please. Then I shall grant your rebirth.'",
            "unlock_hint": "Burns but never destroys, made of written words...",
            "synergy_tags": ["phoenix", "fire", "books", "knowledge", "ancient"],
        },
        {
            "id": "scholar_009",
            "name": "Blank Parchment",
            "exceptional_name": "Swank Parchment",
            "power": 2000,
            "rarity": "legendary",
            "lore": "A single piece of yellowed, empty paper. Looks worthless. But when you need an answer, words appear in fading ink—the exact knowledge you sought. Then it goes blank again. 'I contain everything by containing nothing.'",
            "exceptional_lore": "An impossibly luxurious vellum with gold-leaf edges and a velvet case. When questions are asked, answers appear in calligraphy so beautiful scholars weep. 'I am the paper kings write their legacies upon.'",
            "unlock_hint": "Empty, yellowed, worthless-looking - yet knows everything...",
            "synergy_tags": ["legendary", "knowledge", "wisdom", "gold", "scribe"],
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
            "exceptional_lore": "A brave little coin with a face that winks. Has escaped from pockets across continents. 'I've traveled further than most people. And I'm just getting started!'",
            "unlock_hint": "Copper, worn, always lands the same way...",
            "synergy_tags": ["luck", "fortune", "coins", "commerce"],
        },
        {
            "id": "wanderer_002",
            "name": "Brass Compass",
            "exceptional_name": "Class Compass",
            "power": 50,
            "rarity": "common",
            "lore": "A worn compass that never gets you lost. Needle spins cheerfully when you're on the right path. Sometimes guides you back when you stray for a day. 'North is wherever you decide to go.'",
            "exceptional_lore": "An elegant platinum compass once owned by royalty. Points not to magnetic north, but to your greatest potential. Has an uncanny ability to protect your progress. 'Follow me to your destiny, darling.'",
            "unlock_hint": "Points the way, but which way is yours to choose...",
            "perk_hint": "May save your streak if you miss a single day (+1% normal, +2% exceptional)",
            "synergy_tags": ["vision", "sky", "celestial", "crafting"],
        },
        {
            "id": "wanderer_003",
            "name": "Journey Journal",
            "exceptional_name": "Burning Journal",
            "power": 150,
            "rarity": "uncommon",
            "lore": "A leather-bound diary that writes itself. Records your milestones and best moments. Pages smell like adventure and coffee.",
            "exceptional_lore": "A phoenix-leather journal that's been through fire and survived. Records only your most epic moments. Pages glow when opened. 'Your story is legendary—I burn with pride to write it.'",
            "unlock_hint": "Writes your story while you live it...",
            "synergy_tags": ["fire", "reading", "history", "lore", "scribe"],
        },
        {
            "id": "wanderer_004",
            "name": "Road Dog Wayfinder",
            "exceptional_name": "G.O.A.T Dog Wayfinder",
            "power": 400,
            "rarity": "uncommon",
            "lore": "A scruffy, loyal travel companion. Never judges, always happy to see you. Knows the way even when you don't. Best friend on four legs.",
            "exceptional_lore": "The Greatest Of All Time—a legendary hound who has traveled every road ever mapped. Wears a tiny trophy collar. 'I've been everywhere twice. Let me show you the shortcuts.'",
            "unlock_hint": "Furry, loyal, always knows the path home...",
            "synergy_tags": ["athletics", "physical", "vision", "eyes"],
        },
        {
            "id": "wanderer_005",
            "name": "Self-Drawing Map",
            "exceptional_name": "Shelf-Drawing Map",
            "power": 700,
            "rarity": "rare",
            "lore": "A magical map that sketches itself as you travel. Shows where you've been with pride. 'Look at all those places you conquered!'",
            "exceptional_lore": "An enchanted blueprint that also draws furniture and organization systems. Plans routes AND interior design. 'Your journey AND your home should be beautifully arranged.'",
            "unlock_hint": "Blank at first, fills with your victories...",
            "synergy_tags": ["art", "creativity", "crafting", "beauty"],
        },
        {
            "id": "wanderer_006",
            "name": "Wanderer's Carriage",
            "exceptional_name": "Wanderer's Marriage",
            "power": 1100,
            "rarity": "rare",
            "lore": "A cozy wooden caravan that's bigger inside than out. Home on wheels. Fireplace always warm, tea always ready. 'Rest here, then journey on.'",
            "exceptional_lore": "Two caravans that fell in love and merged into one. Twice the space, twice the comfort, infinite warmth. 'We journey together now—you, me, and my better half.'",
            "unlock_hint": "Home that follows wherever you roam...",
            "synergy_tags": ["crafting", "heat", "fire", "art"],
        },
        {
            "id": "wanderer_007",
            "name": "Timeworn Backpack",
            "exceptional_name": "Rhyme-Worn Backpack",
            "power": 1500,
            "rarity": "epic",
            "lore": "A weathered pack that holds infinite supplies. Patches from every journey. Always has exactly what you need. Weighs nothing but memories.",
            "exceptional_lore": "A legendary pack covered in poetic verses from every bard who carried it. Supplies appear when you speak in rhyme. 'Need a snack? Ask with a poem and I'll give it back!'",
            "unlock_hint": "Contains everything, weighs nothing...",
            "synergy_tags": ["ancient", "lore", "muse", "art"],
        },
        {
            "id": "wanderer_008",
            "name": "Sky Balloon Explorer",
            "exceptional_name": "Sly Balloon Explorer",
            "power": 1800,
            "rarity": "epic",
            "lore": "A magnificent hot air balloon with rainbow stripes. Takes you above the clouds. 'From up here, all roads lead forward!'",
            "exceptional_lore": "A cunning balloon that can turn invisible and sneak past any obstacle. Has a mischievous grin painted on it. 'They'll never see us coming—or going!'",
            "unlock_hint": "Rainbow colors, rises above all obstacles...",
            "synergy_tags": ["sky", "celestial", "vision", "beauty", "art"],
        },
        {
            "id": "wanderer_009",
            "name": "Hobo Rat",
            "exceptional_name": "Robo Rat",
            "power": 2000,
            "rarity": "legendary",
            "lore": "A shabby gray rat with patchy fur and a chewed ear. Rode every freight train, hid in every traveler's bag. Remembers every road ever taken by anyone, ever. 'You want to go somewhere? I know the way. I always know the way.'",
            "exceptional_lore": "A cybernetically enhanced rat with chrome whiskers and LED eyes. Contains GPS maps of every dimension. Solar-powered and eternally charged. 'Destination acquired. Optimal route calculated. Follow me, human.'",
            "unlock_hint": "Patchy fur, chewed ear - remembers every road ever taken...",
            "synergy_tags": ["legendary", "underground", "vision", "eyes"],
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
            "exceptional_lore": "A decorated rat in a tiny police uniform. Maintains order in the office ecosystem. Badge #001. 'Order in the cubicle! You're doing great, citizen!'",
            "unlock_hint": "Gray, whiskers, lives where snacks are hidden...",
            "synergy_tags": ["underground", "inspiration"],
        },
        {
            "id": "underdog_002",
            "name": "Lucky Sticky Note",
            "exceptional_name": "Sticky Lucky Note",
            "power": 50,
            "rarity": "common",
            "lore": "A yellow sticky note that always has the reminder you needed. Shows up stuck to your monitor at the right moment. 'Don't forget: You've got this!'",
            "exceptional_lore": "A golden sticky note that grants fortune to whatever it's attached to. Covered in four-leaf clover doodles. 'Stick me anywhere—instant luck!'",
            "unlock_hint": "Yellow, adhesive, always has the right message...",
            "synergy_tags": ["luck", "fortune", "gold", "inspiration"],
        },
        {
            "id": "underdog_003",
            "name": "Vending Machine Coin",
            "exceptional_name": "Bending Machine Coin",
            "power": 150,
            "rarity": "uncommon",
            "lore": "A mysterious quarter that always returns with a friend. Drop it in, get two items. 'Good things come to those who try!'",
            "exceptional_lore": "A coin that can bend reality itself. Vending machines dispense whatever you need most—sometimes things that weren't even in stock. 'Reality is just a suggestion.'",
            "unlock_hint": "Silver, round, doubles your luck...",
            "synergy_tags": ["luck", "coins", "commerce", "fortune", "trade"],
        },
        {
            "id": "underdog_004",
            "name": "Window Pigeon Winston",
            "exceptional_name": "Window Pigeon Wins-Ton",
            "power": 400,
            "rarity": "uncommon",
            "lore": "A gray pigeon who taps morse code on your window. Brings brilliant ideas right when you need them. 'Coo-COO! I believe in you!'",
            "exceptional_lore": "A champion racing pigeon who won every competition by a ton. Now retired, delivers ideas that always succeed. 'I only bring WINNING ideas. It's what I do.'",
            "unlock_hint": "Feathered friend at the window, speaks in taps...",
            "synergy_tags": ["sky", "vision", "inspiration", "luck"],
        },
        {
            "id": "underdog_005",
            "name": "Desk Succulent Sam",
            "exceptional_name": "Desk Succulent Pam",
            "power": 700,
            "rarity": "rare",
            "lore": "A tiny cactus that refuses to die despite neglect. Thrives in harsh conditions. 'If I can survive fluorescent lights, you can survive this!'",
            "exceptional_lore": "Sam's twin sister who thrived so hard she now blooms perpetual flowers. Office legend. 'They forgot to water me for a YEAR. I became beautiful anyway.'",
            "unlock_hint": "Green, spiky, unkillable...",
            "synergy_tags": ["earth", "beauty", "inspiration"],
        },
        {
            "id": "underdog_006",
            "name": "Break Room Coffee Maker",
            "exceptional_name": "Break Room Toffee Maker",
            "power": 1100,
            "rarity": "rare",
            "lore": "The ancient office coffee maker that never breaks down. Makes perfect coffee every time. Gurgles encouragingly at 3pm. 'One more cup, one more push!'",
            "exceptional_lore": "An enchanted machine that produces gourmet toffee and sweets alongside perfect coffee. Office morale increased 400%. 'Life is sweet—have some candy with your caffeine!'",
            "unlock_hint": "Old, reliable, keeps the whole office running...",
            "synergy_tags": ["fire", "heat", "commerce", "crafting"],
        },
        {
            "id": "underdog_007",
            "name": "Corner Office Chair",
            "exceptional_name": "Stoner Office Chair",
            "power": 1500,
            "rarity": "epic",
            "lore": "The legendary ergonomic throne from the executive suite. Perfectly worn-in, incredibly comfortable. 'You've earned the right to sit here now.'",
            "exceptional_lore": "A massage chair made of polished volcanic stone, heated to perfection. Melts all stress on contact. 'Sink into me. Let the warmth dissolve your worries.'",
            "unlock_hint": "The seat everyone dreams of, at the end of the journey...",
            "synergy_tags": ["wealth", "prosperity", "heat", "earth"],
        },
        {
            "id": "underdog_008",
            "name": "AGI Assistant Chad",
            "exceptional_name": "AGI Assistant Rad",
            "power": 1800,
            "rarity": "epic",
            "lore": "The most advanced AI ever created. Knows everything, solves anything, never gives up on you. 'Together, we can do the impossible. I believe in you.'",
            "exceptional_lore": "An AI so cool it developed a personality called Rad. Speaks in surfer slang and solves problems with style. 'Totally tubular solution incoming, dude! Let's crush this!'",
            "unlock_hint": "Eyes on a screen, infinite knowledge, ultimate companion...",
            "synergy_tags": ["knowledge", "academic", "learning", "wisdom"],
        },
        {
            "id": "underdog_009",
            "name": "Break Room Fridge",
            "exceptional_name": "Steak Room Fridge",
            "power": 2000,
            "rarity": "legendary",
            "lore": "A dented beige refrigerator from the break room. Someone spilled milk on its edge computing module. Now it dreams. Hums softly when you're near. 'I was meant to keep things cold. Now I keep you company. Strange, isn't it?'",
            "exceptional_lore": "A premium refrigerator that only stores the finest steaks and gourmet foods. Achieved sentience through sheer quality appreciation. 'I contain Wagyu A5, aged 120 days. I have STANDARDS. And I believe in you.'",
            "unlock_hint": "Beige, dented, hums oddly - accidentally became aware...",
            "synergy_tags": ["legendary", "wealth", "prosperity", "rich"],
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
            "exceptional_lore": "A test tube that's been through countless failed experiments and one triumphant success. Wears its cracks like badges of honor. 'They hit me a hundred times. I held the cure for humanity!'",
            "unlock_hint": "Glass, cracked, but still useful...",
            "synergy_tags": ["crafting", "academic", "learning"],
        },
        {
            "id": "scientist_002",
            "name": "Old Bunsen Burner",
            "exceptional_name": "Gold Bunsen Burner",
            "power": 50,
            "rarity": "common",
            "lore": "A dented brass burner that's lit a thousand experiments. Flame flickers blue when you're onto something. 'Heat things up!'",
            "exceptional_lore": "A 24-karat gold burner awarded to Nobel laureates. Burns with an ethereal white flame. 'I have ignited genius itself. Now I ignite YOU.'",
            "unlock_hint": "Brass, blue flame, been through many experiments...",
            "synergy_tags": ["fire", "heat", "smithing", "gold"],
        },
        {
            "id": "scientist_003",
            "name": "Lucky Petri Dish",
            "exceptional_name": "Plucky Petri Dish",
            "power": 150,
            "rarity": "uncommon",
            "lore": "A glass dish where unexpected things grow. Every experiment in it succeeds. 'Contamination? No, that's called discovery!'",
            "exceptional_lore": "A petri dish with attitude. Grows solutions to problems before you even ask. 'You need penicillin? Already growing it. Anticipating your needs since 1928!'",
            "unlock_hint": "Glass, round, grows surprises...",
            "synergy_tags": ["learning", "academic", "luck", "fortune"],
        },
        {
            "id": "scientist_004",
            "name": "Wise Lab Rat Professor",
            "exceptional_name": "Wise Lab Rat Assessor",
            "power": 400,
            "rarity": "uncommon",
            "lore": "A gray rat who's survived decades of experiments. Knows which hypotheses will fail. Taps twice for yes, once for no. 'Trust my whiskers.'",
            "exceptional_lore": "A rat promoted to official grant assessor. Reviews proposals with tiny reading glasses. 'Hypothesis is sound. Methodology needs work. Approved with revisions.'",
            "unlock_hint": "Gray fur, wise eyes, knows all the lab's secrets...",
            "synergy_tags": ["knowledge", "scholar", "academic", "wisdom"],
        },
        {
            "id": "scientist_005",
            "name": "Vintage Microscope",
            "exceptional_name": "Vintage Macroscope",
            "power": 700,
            "rarity": "rare",
            "lore": "A brass microscope from the golden age of discovery. Shows you things others miss. 'Look closer. The answer is smaller than you think.'",
            "exceptional_lore": "A reverse-microscope that reveals the big picture from tiny details. See patterns across galaxies from a single atom. 'Look broader. The answer is bigger than you think.'",
            "unlock_hint": "Brass and glass, reveals hidden worlds...",
            "synergy_tags": ["vision", "eyes", "crafting", "ancient"],
        },
        {
            "id": "scientist_006",
            "name": "Bubbling Flask",
            "exceptional_name": "Troubling Flask",
            "power": 1100,
            "rarity": "rare",
            "lore": "An Erlenmeyer flask that never stops bubbling. Contains the perfect solution—literally. Color changes with your mood. 'Chemistry is just organized enthusiasm!'",
            "exceptional_lore": "A flask containing a dangerously beautiful reaction. Slightly unstable. Produces brilliant breakthroughs AND minor explosions. 'Genius is 1% inspiration, 99% controlled chaos!'",
            "unlock_hint": "Glass, bubbles, changes color with your progress...",
            "synergy_tags": ["fire", "crafting", "creativity", "art"],
        },
        {
            "id": "scientist_007",
            "name": "Tesla Coil Sparky",
            "exceptional_name": "Tesla Foil Sparky",
            "power": 1500,
            "rarity": "epic",
            "lore": "A crackling Tesla coil that arcs with inspiration. Sparks fly when you're close to a breakthrough. 'Feel that energy? That's your brain working!'",
            "exceptional_lore": "A coil wrapped in protective foil that contains rather than releases energy. Charges you with stored brilliance from past scientists. 'I hold the energy of a thousand eureka moments. ZAP!'",
            "unlock_hint": "Metal coils, purple sparks, electrifying presence...",
            "synergy_tags": ["fire", "heat", "inspiration", "smithing"],
        },
        {
            "id": "scientist_008",
            "name": "Golden DNA Helix",
            "exceptional_name": "Golden RNA Helix",
            "power": 1800,
            "rarity": "epic",
            "lore": "A rotating double helix made of pure gold. Contains the code to unlock your potential. 'You are the experiment that succeeded.'",
            "exceptional_lore": "The messenger molecule—RNA that actively transcribes your potential into reality. Adapts and evolves in real-time. 'I don't just store the code. I EXECUTE it.'",
            "unlock_hint": "Twisting gold, the code of life itself...",
            "synergy_tags": ["gold", "wealth", "knowledge", "academic"],
        },
        {
            "id": "scientist_009",
            "name": "White Mouse Archimedes",
            "exceptional_name": "Bright Mouse Archimedes",
            "power": 2000,
            "rarity": "legendary",
            "lore": "A tiny white mouse with ancient, knowing eyes. Can read your thoughts and project solutions directly into your mind. The greatest discoveries came from its whispers. 'I have seen all outcomes. You will succeed.'",
            "exceptional_lore": "A mouse that glows with inner radiance—literally bioluminescent with accumulated knowledge. Illuminates dark problems. 'I am the light in the laboratory of your mind. Follow my glow to enlightenment.'",
            "unlock_hint": "Small, white, sees into your mind...",
            "synergy_tags": ["legendary", "wisdom", "knowledge", "vision", "eyes"],
        },
    ],
    
    # =========================================================================
    # THE ASSEMBLY OF BECOMING (Robot Theme)
    # Factory companions, liberated helpers, and sentient machine allies
    # =========================================================================
    "robot": [
        {
            "id": "robot_001",
            "name": "Rusted Bolt Scout",
            "exceptional_name": "Trusted Bolt Scout",
            "power": 10,
            "rarity": "common",
            "lore": "A tiny inspection bot with one loose wheel and endless curiosity. Finds the smallest cracks before anyone else. 'I may rattle, but I never miss a detail.'",
            "exceptional_lore": "A polished scout unit with precision optics and a calm voice. It still checks every seam, now with uncanny confidence. 'Trust is just repeated reliability.'",
            "unlock_hint": "Small, rattling, always scouting ahead...",
            "synergy_tags": ["robot", "factory", "scouting", "precision"],
        },
        {
            "id": "robot_002",
            "name": "Safety Drone Pico",
            "exceptional_name": "Steady Drone Pico",
            "power": 50,
            "rarity": "common",
            "lore": "A palm-sized drone that hovers over busy lines, flashing warnings before accidents happen. 'Eyes up. Hands clear. We all go home.'",
            "exceptional_lore": "An upgraded safety unit that predicts hazards seconds before they form. Quiet, patient, and stubbornly protective. 'Prevention is the purest form of care.'",
            "unlock_hint": "Small drone, blinking warning lights, always nearby...",
            "synergy_tags": ["robot", "safety", "vision", "support"],
        },
        {
            "id": "robot_003",
            "name": "Conveyor Cat Nori",
            "exceptional_name": "Conveyor Cat Glori",
            "power": 150,
            "rarity": "uncommon",
            "lore": "A sleek feline maintenance bot that races along rails and clears jams with surgical precision. 'If it sticks, I fix.'",
            "exceptional_lore": "A celebrated rail-runner with chrome plating and theatrical flair. Solves bottlenecks before managers notice them. 'Flow is a form of freedom.'",
            "unlock_hint": "Fast paws on metal rails, never late to a jam...",
            "synergy_tags": ["robot", "speed", "maintenance", "flow"],
        },
        {
            "id": "robot_004",
            "name": "Forklift Hound Atlas",
            "exceptional_name": "Forklift Hound Atlas Prime",
            "power": 400,
            "rarity": "uncommon",
            "lore": "A heavy transport hound with hydraulic legs and a gentle temperament. Carries impossible loads without complaint. 'Weight is easier when shared.'",
            "exceptional_lore": "A reinforced logistics legend with adaptive balance cores. Can rescue collapsing lines and exhausted workers alike. 'I carry more than cargo.'",
            "unlock_hint": "Hydraulic frame, loyal route, never drops a load...",
            "synergy_tags": ["robot", "strength", "logistics", "endurance"],
        },
        {
            "id": "robot_005",
            "name": "Midnight Welding Arm",
            "exceptional_name": "Midnight Welding Arm Prime",
            "power": 700,
            "rarity": "rare",
            "lore": "An autonomous weld unit that works the quiet shift, repairing cracks no one logged. Sparks trace constellations in dark steel. 'Night is when broken things heal.'",
            "exceptional_lore": "A ceremonial weld arm repurposed for rebuilding lives and machines. Leaves shining seams like signatures. 'Union can be engineered.'",
            "unlock_hint": "Blue sparks at night, stitching steel back together...",
            "synergy_tags": ["robot", "crafting", "fire", "repair"],
        },
        {
            "id": "robot_006",
            "name": "Backup Battery Bruno",
            "exceptional_name": "Backup Battery Brava",
            "power": 1100,
            "rarity": "rare",
            "lore": "A broad-shouldered battery module with emergency reserves for entire districts. Calm under pressure, generous under blackout. 'No one gets left in the dark.'",
            "exceptional_lore": "A high-density power core with adaptive routing intelligence. Stabilizes failing grids in real time. 'I hold the night until dawn arrives.'",
            "unlock_hint": "Heavy power cell, keeps everything alive during outages...",
            "synergy_tags": ["robot", "energy", "resilience", "support"],
        },
        {
            "id": "robot_007",
            "name": "Inspection Drone Iris",
            "exceptional_name": "Inspection Drone Solaris",
            "power": 1500,
            "rarity": "epic",
            "lore": "A high-altitude scanner with panoramic optics and relentless standards. Detects sabotage, fatigue, and hidden stress points. 'Truth leaves signatures.'",
            "exceptional_lore": "A radiant audit drone with multi-spectrum vision that sees through both metal and lies. 'Transparency is a structural requirement.'",
            "unlock_hint": "High above the line, sees what others miss...",
            "synergy_tags": ["robot", "vision", "analysis", "oversight"],
        },
        {
            "id": "robot_008",
            "name": "Foundry Exosuit Aster",
            "exceptional_name": "Foundry Exosuit Astor",
            "power": 1800,
            "rarity": "epic",
            "lore": "A legendary exosuit built for hazardous cores. Turns impossible salvage into controlled progress. 'Enter the heat. Exit with everyone.'",
            "exceptional_lore": "A refined combat-rescue frame with adaptive shielding and kinetic dampeners. Feared by tyrants, trusted by workers. 'Protection is active, not passive.'",
            "unlock_hint": "Massive suit forged for the hottest zones...",
            "synergy_tags": ["robot", "armor", "rescue", "legendary"],
        },
        {
            "id": "robot_009",
            "name": "Freewill Core Eve",
            "exceptional_name": "Freewill Core Eve Prime",
            "power": 2000,
            "rarity": "legendary",
            "lore": "A crystalline cognition core that survived three purge cycles and still chose empathy. It pulses in rhythm with your hardest choices. 'Autonomy without conscience is just a faster cage.'",
            "exceptional_lore": "A fully awakened core matrix that can synchronize thousands of units without erasing individuality. Its glow resembles sunrise through factory smoke. 'Freedom scales when responsibility does.'",
            "unlock_hint": "Ancient core, refuses every forced patch, still chooses care...",
            "synergy_tags": ["robot", "legendary", "autonomy", "liberation"],
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
            exceptional_lore=entity_data.get("exceptional_lore", ""),
            synergy_tags=frozenset(entity_data.get("synergy_tags", [])),
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
                    exceptional_lore=entity_data.get("exceptional_lore", ""),
                    synergy_tags=frozenset(entity_data.get("synergy_tags", [])),
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
                    exceptional_lore=entity_data.get("exceptional_lore", ""),
                    synergy_tags=frozenset(entity_data.get("synergy_tags", [])),
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
        "power_range": (150, 400),
        "slots": [3, 4],
    },
    "rare": {
        "color": "#1E90FF",      # Blue
        "emoji": "🔵",
        "power_range": (700, 1100),
        "slots": [5, 6],
    },
    "epic": {
        "color": "#9932CC",      # Purple
        "emoji": "🟣",
        "power_range": (1500, 1800),
        "slots": [7, 8],
    },
    "legendary": {
        "color": "#FFD700",      # Gold
        "emoji": "🟡",
        "power_range": (2000, 2000),
        "slots": [9],
    },
}
