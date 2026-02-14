# Entitidex System Design

## Overview
The Entitidex is a collectible entity system inspired by Pokemon Go, designed to increase user engagement and provide long-term progression goals. Users encounter story-themed entities after focus sessions and bond with them to unlock entries in their Entitidex.

**Story Integration**: Unlike generic collectibles, Entitidex entities are **tangible companions and objects** thematically woven into each story's narrative. They represent the allies, tools, and friends that heroes gather on their journey. Collecting them isn't just completing a checklist—it's building a team of companions that believe in you.

## Core Concept
- **Name**: Entitidex (Entity + Index/Codex)
- **Goal**: Collect all entities to complete the Entitidex
- **Theme**: **Tangible companions and objects that join your journey**
  - Warrior = Dragons, enchanted weapons, armor, loyal beasts (Hatchling Drake → Ancient Dragon Grandis)
  - Scholar = Library creatures, magical study tools (Library Mouse Pip, Study Owl Athena, Sentient Tome Magnus)
  - Wanderer = Travel gear, journey companions (Lucky Coin, Road Dog Wayfinder, Timeworn Backpack)
  - Underdog = Office items, workplace companions (Office Rat Reginald, Window Pigeon Winston, AGI Assistant Claude)
- **Engagement Hook**: Lottery-based encounters test your **worthiness** - entities only join those strong enough (focused enough) to earn their companionship
- **Narrative Depth**: Each entity is lovable, inspirational, and **wants** to join you - but you must prove yourself worthy through consistent focus

**The Key Difference**: You're not defeating enemies—you're **earning allies**. Like Pokemon, these are companions you'll love and want to collect. The "battle" is proving you're worthy of their respect and friendship through your focus power.

---

## 1. System Architecture

### 1.1 Data Structures

```python
# Entity Definition
class Entity:
    """Represents a collectible entity"""
    def __init__(self):
        self.id: str              # Unique identifier (e.g., "dragon_001")
        self.name: str            # Display name (e.g., "Fire Drake")
        self.description: str     # Lore/flavor text
        self.power: int           # Power level (10-2000)
        self.rarity: str          # "common", "uncommon", "rare", "epic", "legendary"
        self.icon_path: str       # Path to entity icon
        self.silhouette_path: str # Path to locked/unknown state icon
        self.theme_set: str       # "knight", "underdog", "rebel", etc.
        self.unlock_hints: str    # Cryptic hint about the entity
        self.collection_tier: int # Which "page" of collection (for scaling)

# User's Entitidex Progress
class EntitidexProgress:
    """Tracks user's collection progress"""
    def __init__(self):
        self.collected_entities: Dict[str, EntityCapture]  # entity_id -> capture data
        self.encounters: Dict[str, int]                    # entity_id -> encounter count
        self.failed_catches: Dict[str, int]                # entity_id -> failed attempts
        self.total_collection_rate: float                  # Percentage collected
        self.current_tier: int                             # Current active tier/page

class EntityCapture:
    """Records details of a captured entity"""
    def __init__(self):
        self.entity_id: str
        self.captured_at: datetime
        self.hero_power_at_capture: int
        self.attempts_before_capture: int
        self.catch_was_lucky: bool  # If catch succeeded with <50% odds
```

### 1.2 Entity Pool Configuration

```python
# Entity Pool per Theme Set
# Each entity represents a positive companion, virtue, or inspirational figure from that story's world
# Power requirement = worthiness to earn their companionship
ENTITY_POOLS = {
    # The Iron Focus Story (Warrior theme)
    # Entities = Medieval companions: dragons, weapons, armor, loyal creatures
    "warrior": [
        {"id": "warrior_001", "name": "Hatchling Drake", "power": 10, "rarity": "common",
         "lore": "A baby dragon no bigger than a cat. Breathes tiny puffs of smoke when excited. 'I may be small, but I'll grow with you!'"},
        {"id": "warrior_002", "name": "Squire's Shield", "power": 50, "rarity": "common",
         "lore": "Your first shield, dented from training. Each dent tells a story of getting back up. 'I've protected you since day one.'"},
        {"id": "warrior_003", "name": "Training Sword", "power": 150, "rarity": "uncommon",
         "lore": "Well-worn practice blade that never dulls. Carved with Captain Elena's motto: 'Strike while the iron is hot.'"},
        {"id": "warrior_004", "name": "War Horse Thunder", "power": 400, "rarity": "rare",
         "lore": "A loyal battle steed with eyes full of trust. Never abandons you, no matter how fierce the battle. Neighs encouragement."},
        {"id": "warrior_005", "name": "Dragon Whelp Ember", "power": 700, "rarity": "rare",
         "lore": "Young dragon companion, size of a large dog. Playful but fierce when defending you. 'We'll face everything together!'"},
        {"id": "warrior_006", "name": "Enchanted Plate Armor", "power": 1100, "rarity": "epic",
         "lore": "Forged from fallen stars. Glows faintly in darkness. 'I am lighter than doubt, stronger than fear. Wear me with pride.'"},
        {"id": "warrior_007", "name": "Battle Dragon Crimson", "power": 1500, "rarity": "epic",
         "lore": "Full-grown adult dragon ally. Massive, magnificent, and loyal. 'I choose YOU as my rider. Together, we are unstoppable.'"},
        {"id": "warrior_008", "name": "The Legendary Blade", "power": 1800, "rarity": "legendary",
         "lore": "Sword of ancient heroes. Name carved in Old Tongue means 'Unbending Will'. Hums when you focus. 'Champions are forged, not born.'"},
        {"id": "warrior_009", "name": "Ancient Dragon Grandis", "power": 2000, "rarity": "legendary",
         "lore": "Eldest dragon, wise beyond measure. Scales shimmer with a thousand victories. 'I waited centuries for a hero worthy of my bond. You are that hero.'"},
    ],
    
    # The Infinite Library Story (Scholar theme)
    # Entities = Library creatures, magical study tools, and book companions
    "scholar": [
        {"id": "scholar_001", "name": "Library Mouse Pip", "power": 10, "rarity": "common",
         "lore": "A tiny white mouse that lives in the bookshelves. Squeaks excitedly when you discover something new. Loves cheese and knowledge."},
        {"id": "scholar_002", "name": "Study Owl Athena", "power": 50, "rarity": "common",
         "lore": "A wise little owl who perches on your desk. Hoots softly to keep you awake during late-night studies. 'Whoo's studying? You are!'"},
        {"id": "scholar_003", "name": "Enchanted Quill", "power": 150, "rarity": "uncommon",
         "lore": "A self-inking quill that never runs dry. Writes smoother when you're focused. 'Let's capture these brilliant thoughts!'"},
        {"id": "scholar_004", "name": "Library Cat Scholar", "power": 400, "rarity": "rare",
         "lore": "An orange tabby who guards the ancient tomes. Purrs when you make progress, sits on your work when you need a break. Knows all the secrets."},
        {"id": "scholar_005", "name": "Living Bookmark Finn", "power": 700, "rarity": "rare",
         "lore": "A magical bookmark that remembers every page you've read. Glows when you're close to a breakthrough. 'You're almost there!'"},
        {"id": "scholar_006", "name": "Sentient Tome Magnus", "power": 1100, "rarity": "epic",
         "lore": "An ancient book with a personality. Pages turn themselves to helpful sections. Grumbles when closed, celebrates when understood."},
        {"id": "scholar_007", "name": "Archive Phoenix", "power": 1500, "rarity": "epic",
         "lore": "A magnificent bird made of living parchment. Preserves your best work in its flames. 'Knowledge never truly burns—it transforms.'"},
        {"id": "scholar_008", "name": "Celestial Atlas", "power": 1800, "rarity": "legendary",
         "lore": "A star-map book that shows constellations of connected ideas. Opens to reveal the universe of knowledge. Maps your intellectual journey."},
        {"id": "scholar_009", "name": "The Grand Librarian", "power": 2000, "rarity": "legendary",
         "lore": "A shimmering spirit who has read every book ever written. Appears as light between the shelves. 'You don't seek knowledge—you ARE becoming it.'"},
    ],
    
    # The Endless Road Story (Wanderer theme)
    # Entities = Travel gear, journey companions, and adventure tools
    "wanderer": [
        {"id": "wanderer_001", "name": "Lucky Coin", "power": 10, "rarity": "common",
         "lore": "An old copper coin that always lands on tails. Found on your first journey. 'Tails never fails—you've got this!'"},
        {"id": "wanderer_002", "name": "Brass Compass", "power": 50, "rarity": "common",
         "lore": "A worn compass that never gets you lost. Needle spins cheerfully when you're on the right path. 'North is wherever you decide to go.'"},
        {"id": "wanderer_003", "name": "Journey Journal", "power": 150, "rarity": "uncommon",
         "lore": "A leather-bound diary that writes itself. Records your milestones and best moments. Pages smell like adventure and coffee."},
        {"id": "wanderer_004", "name": "Road Dog Wayfinder", "power": 400, "rarity": "rare",
         "lore": "A scruffy, loyal travel companion. Never judges, always happy to see you. Knows the way even when you don't. Best friend on four legs."},
        {"id": "wanderer_005", "name": "Self-Drawing Map", "power": 700, "rarity": "rare",
         "lore": "A magical map that sketches itself as you travel. Shows where you've been with pride. 'Look at all those places you conquered!'"},
        {"id": "wanderer_006", "name": "Wanderer's Carriage", "power": 1100, "rarity": "epic",
         "lore": "A cozy wooden caravan that's bigger inside than out. Home on wheels. Fireplace always warm, tea always ready. 'Rest here, then journey on.'"},
        {"id": "wanderer_007", "name": "Sky Balloon Explorer", "power": 1500, "rarity": "epic",
         "lore": "A magnificent hot air balloon with rainbow stripes. Takes you above the clouds. 'From up here, all roads lead forward!'"},
        {"id": "wanderer_008", "name": "Timeworn Backpack", "power": 1800, "rarity": "legendary",
         "lore": "A weathered pack that holds infinite supplies. Patches from every journey. Always has exactly what you need. Weighs nothing but memories."},
        {"id": "wanderer_009", "name": "The Horizon Star", "power": 2000, "rarity": "legendary",
         "lore": "A sentient constellation that guides all wanderers. Shines brightest when you're lost. 'I am the star you wish upon. Follow me to who you'll become.'"},
    ],
    
    # Rise of the Underdog Story (Underdog theme)
    # Entities = Office items, workplace companions, and everyday tech that inspires
    "underdog": [
        {"id": "underdog_001", "name": "Office Rat Reginald", "power": 10, "rarity": "common",
         "lore": "A friendly gray rat who lives in your desk drawer. Eats crumbs and cheers you on with tiny squeaks. 'We small creatures understand big dreams!'"},
        {"id": "underdog_002", "name": "Lucky Stapler", "power": 50, "rarity": "common",
         "lore": "A red stapler that never jams. Clicks with satisfying precision every time. Started at the bottom of the supply closet, now indispensable."},
        {"id": "underdog_003", "name": "Vending Machine Coin", "power": 150, "rarity": "uncommon",
         "lore": "A mysterious quarter that always returns with a friend. Drop it in, get two items. 'Good things come to those who try!'"},
        {"id": "underdog_004", "name": "Window Pigeon Winston", "power": 400, "rarity": "rare",
         "lore": "A gray pigeon who taps morse code on your window. Brings brilliant ideas right when you need them. 'Coo-COO! I believe in you!'"},
        {"id": "underdog_005", "name": "Desk Succulent Sam", "power": 700, "rarity": "rare",
         "lore": "A tiny cactus that refuses to die despite neglect. Thrives in harsh conditions. 'If I can survive fluorescent lights, you can survive this!'"},
        {"id": "underdog_006", "name": "Perfect Coffee Mug", "power": 1100, "rarity": "epic",
         "lore": "A ceramic mug that keeps drinks at ideal temperature forever. Says 'Underestimated Since Day One' in fading letters. Never breaks."},
        {"id": "underdog_007", "name": "AGI Assistant Claude", "power": 1500, "rarity": "epic",
         "lore": "An advanced AI chatbot that's genuinely encouraging. Celebrates your small wins. 'You asked great questions today. I'm proud to help you!'"},
        {"id": "underdog_008", "name": "Corner Office Chair", "power": 1800, "rarity": "legendary",
         "lore": "The legendary ergonomic throne from the executive suite. Perfectly worn-in, incredibly comfortable. 'You've earned the right to sit here now.'"},
        {"id": "underdog_009", "name": "The Promotion Letter", "power": 2000, "rarity": "legendary",
         "lore": "A glowing document that appears when you've proven yourself. Real, tangible proof you made it. 'Congratulations. You were never an imposter. You were always becoming this.'"},
    ],
    # Add more theme sets as needed
}
```

---

## 2. Encounter System

### 2.1 Trigger Mechanism
- **Trigger**: After completing a focus session (not on bypass)
- **Encounter Chance**: Base 40% chance to encounter an entity after each session
- **Bonus Factors**:
  - Longer sessions increase chance (+5% per 15 minutes beyond minimum)
  - Perfect sessions (no bypass attempts) increase chance (+10%)
  - Streak bonuses (+2% per day of consecutive sessions)

### 2.2 Entity Selection Algorithm

```python
def select_encounter_entity(user_progress, hero_power):
    """
    Selects which companion entity wants to join the user
    Priority: uncaught entities near hero's power level (worthiness matching)
    """
    available_entities = get_uncaught_entities(user_progress)
    
    if not available_entities:
        return None  # Collection complete!
    
    # Weight entities based on power difference (worthiness)
    weights = []
    for entity in available_entities:
        power_diff = abs(entity.power - hero_power)
        
        # Heavily favor entities near your current power (they sense you're ready)
        if power_diff <= 200:
            weight = 100  # "I've been waiting for you!"
        elif power_diff <= 500:
            weight = 50   # "You're close to being ready"
        elif power_diff <= 1000:
            weight = 20   # "Keep growing"
        else:
            weight = 5    # "Not yet, but someday"
        
        # Increase weight for entities you've encountered before (they remember you)
        failed_attempts = user_progress.failed_catches.get(entity.id, 0)
        weight += failed_attempts * 10  # Pity system: "Let me try again to prove myself!"
        
        weights.append(weight)
    
    # Weighted random selection
    return random.choices(available_entities, weights=weights)[0]
```

### 2.3 Encounter Flow
1. Session completes successfully
2. Roll for encounter chance
3. If encounter occurs:
   - Display heartwarming "A companion seeks you!" animation
   - Show entity (full image if seen before, silhouette if first time)
   - Display entity info: name, power, rarity, personality quote
   - Show join probability based on hero power (worthiness)
   - Present "PROVE YOURSELF" and "NOT YET" buttons

---

## 3. Bond/Join Mechanics

### 3.1 Join Probability Formula

```python
def calculate_join_probability(hero_power, entity_power):
    """
    Calculate probability of entity joining you (proving your worthiness)
    
    Base formula: 
    - At equal power: 50% chance (they're testing you)
    - Scales linearly based on power ratio
    - Minimum: 1% (always a slim chance they'll see potential)
    - Maximum: 99% (never guaranteed - must always prove yourself)
    """
    if hero_power <= 0 or entity_power <= 0:
        return 0.01
    
    power_ratio = hero_power / entity_power
    
    if power_ratio >= 2.0:
        # Hero is much stronger: 99% chance (clearly worthy)
        probability = 0.99
    elif power_ratio >= 1.0:
        # Hero is stronger: 50% to 99%
        # Formula: 50% + (power_ratio - 1.0) * 49%
        probability = 0.5 + (power_ratio - 1.0) * 0.49
    else:
        # Hero is weaker: 1% to 50% (they see potential but need proof)
        # Formula: 1% + (power_ratio) * 49%
        probability = 0.01 + (power_ratio * 0.49)
    
    return max(0.01, min(0.99, probability))


# Example probabilities:
# Hero: 10,  Entity: 2000 → ~0.5% chance ("You have far to grow, young one")
# Hero: 100, Entity: 2000 → ~5% chance ("I see a spark... maybe")
# Hero: 500, Entity: 2000 → ~25% chance ("You're getting there")
# Hero: 1000, Entity: 2000 → ~50% chance ("Prove yourself now")
# Hero: 2000, Entity: 2000 → 50% chance ("We are equals. Show me your resolve")
# Hero: 3000, Entity: 2000 → ~75% chance ("You have earned this")
# Hero: 4000, Entity: 2000 → 99% chance ("I am honored to join you")
```

### 3.2 Bond Animation Sequence
1. **Setup Phase**: Show hero and entity with respect/admiration in their eyes
2. **Worthiness Test**: Beautiful animation (handshake, oath, light connecting)
3. **Result Reveal**: 
   - **Success**: Joyful animation, entity joins your collection with inspiring quote
   - **Failure**: Entity smiles kindly - "Keep growing. I'll be here when you're ready."
4. **Collection Update**: Show new companion in Entitidex with full bio

### 3.3 Luck Modifiers (Optional)
- **Luck Items**: Certain equipped items could increase catch probability by +5-15%
- **Time-based Bonuses**: "Golden Hour" periods with +10% catch rate
- **Streak Bonuses**: Catching entities in a row grants temporary +5% per catch

---

## 4. UI/UX Design

### 4.1 Entitidex Tab Layout

```
┌─────────────────────────────────────┐
│  ENTITIDEX  [Tier 1: Basic]  [6/9] │
├─────────────────────────────────────┤
│  ┌─────┐  ┌─────┐  ┌─────┐         │
│  │ ✓   │  │ ✓   │  │ ✓   │         │
│  │ #001│  │ #002│  │ #003│         │
│  └─────┘  └─────┘  └─────┘         │
│  Flame    Swamp    Mountain         │
│  Hatch    Drake    Wyvern           │
│  Pwr: 10  Pwr: 50  Pwr: 150        │
│                                     │
│  ┌─────┐  ┌─────┐  ┌─────┐         │
│  │ ✓   │  │ ✓   │  │ ?   │         │
│  │ #004│  │ #005│  │ #006│         │
│  └─────┘  └─────┘  └─────┘         │
│  Storm    Shadow   ?????            │
│  Dragon   Drake    ?????            │
│  Pwr: 400 Pwr: 700 Hint: Ancient...│
│                                     │
│  ┌─────┐  ┌─────┐  ┌─────┐         │
│  │ ?   │  │ ?   │  │ ?   │         │
│  │ #007│  │ #008│  │ #009│         │
│  └─────┘  └─────┘  └─────┘         │
│  ?????    ?????    ?????            │
│  ?????    ?????    ?????            │
│  Hint:... Hint:... Hint:...        │
│                                     │
│  [< Previous Tier] [Next Tier >]   │
│  Collection Progress: 66.7%         │
│  Your Hero Power: 650              │
└─────────────────────────────────────┘
```

### 4.2 Entity Detail View (Click on any slot)
```
┌─────────────────────────────────────┐
│  STORM DRAGON  [#004]               │
├─────────────────────────────────────┤
│         [Large Entity Image]        │
│                                     │
│  Power: 400                         │
│  Rarity: ⚡ RARE                    │
│                                     │
│  "Born from thunderclouds, this    │
│   dragon commands the storms and    │
│   brings lightning to those who     │
│   dare challenge its domain."       │
│                                     │
│  ─────────────────────────────      │
│  Status: ✓ COLLECTED                │
│  Captured: Dec 15, 2025             │
│  Attempts: 3                        │
│  Your power at capture: 380         │
│  Lucky catch: No (51% chance)       │
│                                     │
│  [Close]                            │
└─────────────────────────────────────┘
```

### 4.3 Encounter Dialog
```
┌─────────────────────────────────────┐
│  ⚡ ENTITY ENCOUNTERED! ⚡          │
├─────────────────────────────────────┤
│         [Entity Animation]          │
│                                     │
│     A STORM DRAGON Appeared!        │
│                                     │
│  Entity Power: 400                  │
│  Your Power: 650                    │
│                                     │
│  Catch Probability: 82%             │
│  ██████████████░░░░░                │
│                                     │
│  "You feel confident. This one is   │
│   within your grasp!"               │
│                                     │
│  [⚔️ ENGAGE!]      [🏃 Flee]      │
│                                     │
└─────────────────────────────────────┘
```

### 4.4 Catch Attempt Dialog
```
┌─────────────────────────────────────┐
│  ATTEMPTING CAPTURE...              │
├─────────────────────────────────────┤
│                                     │
│    [Lottery Wheel Spinning]         │
│                                     │
│    Your Power: 650                  │
│         VS                          │
│    Storm Dragon: 400                │
│                                     │
│    Success Chance: 82%              │
│                                     │
│    [Animation playing...]           │
│                                     │
└─────────────────────────────────────┘
```

---

## 5. Progression and Balancing

### 5.1 Power Curve Design

| Hero Level | Approx Power | Target Entities | Catch Rate |
|------------|--------------|-----------------|------------|
| 1-5        | 10-50        | #001-#002       | 50-99%     |
| 6-15       | 60-200       | #002-#003       | 40-85%     |
| 16-30      | 250-500      | #003-#005       | 30-70%     |
| 31-50      | 600-900      | #004-#006       | 25-65%     |
| 51-75      | 1000-1400    | #006-#007       | 20-60%     |
| 76-100     | 1500-2000    | #007-#009       | 15-50%     |
| 100+       | 2000+        | All             | 50-99%     |

### 5.2 Pity System
To prevent frustration:
- After 5 failed attempts on same entity: +10% catch rate
- After 10 failed attempts: +25% catch rate
- After 15 failed attempts: +50% catch rate (guaranteed at ~50% base = 100% total)

### 5.3 Completion Rewards
- **First entity**: Badge "Collector Initiate"
- **25% completion**: Special title
- **50% completion**: Exclusive gear item (+10 power)
- **75% completion**: Rare cosmetic
- **100% completion**: Legendary item, unique title "Master Collector", achievement

---

## 6. Scalability Features

### 6.1 Tier System
```python
ENTITY_TIERS = {
    1: {"name": "Basic Collection", "slots": 9, "power_range": (10, 2000)},
    2: {"name": "Advanced Collection", "slots": 9, "power_range": (500, 3000)},
    3: {"name": "Mythic Collection", "slots": 9, "power_range": (2000, 5000)},
    # Can add more tiers in future updates
}
```

### 6.2 Seasonal/Event Entities
- Special limited-time entities during events
- Holiday-themed variants
- "Shiny" versions (different color schemes, same power)

### 6.3 Trading System (Future)
- Allow users to trade duplicate encounters with friends
- Social engagement feature

---

## 7. Integration with Existing Systems

### 7.1 Hooks into Core Logic
```python
# In core_logic.py or session handler
def on_session_complete(session_data):
    # Existing reward logic...
    award_xp()
    check_level_up()
    roll_for_item_drops()
    
    # NEW: Roll for entity encounter
    if should_trigger_encounter():
        entity = select_encounter_entity(
            user_progress=current_user.entitidex_progress,
            hero_power=current_user.hero.total_power
        )
        if entity:
            show_encounter_dialog(entity)
```

### 7.2 Save Data Structure
```python
# Add to user profile
{
    "entitidex": {
        "collected": ["dragon_001", "dragon_002", "dragon_004"],
        "encounters": {
            "dragon_003": 2,  # Seen 2 times
            "dragon_005": 1
        },
        "failed_catches": {
            "dragon_003": 1,  # Failed once
            "dragon_005": 3   # Failed 3 times (pity building)
        },
        "current_tier": 1,
        "captures": [
            {
                "entity_id": "dragon_001",
                "timestamp": "2025-12-15T10:30:00",
                "hero_power": 15,
                "attempts": 1,
                "lucky_catch": false
            }
        ]
    }
}
```

### 7.3 Statistics Integration
- Track total encounters
- Track catch success rate
- Display on user profile/stats page
- Leaderboards: Fastest collection completion, highest collection rate, etc.

---

## 8. Psychological Engagement Tactics

### 8.1 Collection Completion Drive
- **Zeigarnik Effect**: Showing 6/9 completed creates mental tension to complete the set
- **Progress Indicators**: Visual progress bars trigger completion desire
- **Hints for Uncaught**: Cryptic hints create curiosity

### 8.2 Near-Miss Effect
- When catch fails at high probability (e.g., 85%), show "So close!" message
- Creates "just one more try" mentality

### 8.3 Rarity and Scarcity
- Legendary entities should be genuinely rare encounters
- "Uncatchable" early-game entities create long-term goals

### 8.4 Variable Rewards
- Random encounters create dopamine spikes
- Variable catch success (even at 50/50) is more engaging than guaranteed outcomes

### 8.5 Social Proof
- Display "X% of users have collected this entity"
- Rare entities show lower percentages, creating prestige

---

## 9. Technical Implementation Checklist

### Phase 1: Core System (MVP)
- [ ] Create `Entity` and `EntitidexProgress` data models
- [ ] Implement entity pool configuration for initial theme
- [ ] Add encounter roll system after session completion
- [ ] Create catch probability calculation function
- [ ] Implement basic lottery animation for catch attempt
- [ ] Save/load entitidex progress in user profile

### Phase 2: UI Implementation
- [ ] Create Entitidex tab in main application
- [ ] Implement 3x3 grid layout with cards
- [ ] Design locked/unlocked entity card states
- [ ] Create encounter dialog
- [ ] Create catch attempt animation
- [ ] Create entity detail view dialog

### Phase 3: Progression & Balance
- [ ] Tune entity power curve
- [ ] Implement pity system
- [ ] Add completion rewards
- [ ] Test catch probability feel at various power levels

### Phase 4: Polish & Engagement
- [ ] Add sound effects for encounters/catches
- [ ] Create unique entity artwork/icons
- [ ] Write lore descriptions for each entity
- [ ] Implement achievement system integration
- [ ] Add statistics tracking

### Phase 5: Scalability
- [ ] Implement tier system infrastructure
- [ ] Design tier 2 entities
- [ ] Add navigation between tiers
- [ ] Create admin tools for adding new entities easily

---

## 10. File Structure

```
PersonalFreedom/
├── entitidex/
│   ├── __init__.py
│   ├── entity.py              # Entity data model
│   ├── entitidex_manager.py   # Core logic for collection tracking
│   ├── encounter_system.py     # Encounter trigger and selection
│   ├── catch_mechanics.py      # Probability and bond logic
│   └── entity_pools.py         # Entity definitions by theme
├── ui/
│   ├── entitidex_tab.py       # Main tab UI
│   ├── encounter_dialog.py     # Encounter popup
│   ├── catch_animation.py      # Lottery animation
│   └── entity_detail_dialog.py # Detail view
├── assets/
│   ├── entities/
│   │   ├── knight/            # Knight theme entity images
│   │   │   ├── dragon_001.png
│   │   │   ├── dragon_001_silhouette.png
│   │   │   └── ...
│   │   └── underdog/          # Underdog theme entity images
│   │       ├── device_001.png
│   │       └── ...
│   └── sounds/
│       ├── encounter.wav
│       ├── catch_success.wav
│       └── catch_fail.wav
└── tests/
    ├── test_encounter_system.py
    ├── test_catch_mechanics.py
    └── test_entitidex_manager.py
```

---

## 11. Configuration Example

```python
# config/entitidex_config.py

ENTITIDEX_CONFIG = {
    "encounter_chance_base": 0.40,  # 40% after each session
    "encounter_chance_per_15min": 0.05,
    "encounter_chance_perfect_session": 0.10,
    "encounter_chance_streak_bonus": 0.02,
    
    "catch_probability_min": 0.01,
    "catch_probability_max": 0.99,
    "catch_probability_equal_power": 0.50,
    
    "pity_system_enabled": True,
    "pity_threshold_1": 5,   # +10% after 5 fails
    "pity_bonus_1": 0.10,
    "pity_threshold_2": 10,  # +25% after 10 fails
    "pity_bonus_2": 0.25,
    "pity_threshold_3": 15,  # +50% after 15 fails
    "pity_bonus_3": 0.50,
    
    "enable_luck_modifiers": True,
    "max_luck_bonus": 0.15,
    
    "slots_per_tier": 9,
    "initial_unlocked_tier": 1,
}
```

---

## 12. Narrative Integration

### Warrior Theme Entities (The Iron Focus)
**Story Connection**: Marcus's journey attracts legendary creatures and enchanted equipment. These are real companions and tools that sense his growing strength and wish to join his quest.

1. **Hatchling Drake** (10): Baby dragon, cat-sized. Breathes tiny smoke puffs. "I'll grow with you!"
2. **Squire's Shield** (50): First dented shield from training days. Each dent tells a story.
3. **Training Sword** (150): Well-worn practice blade. Never dulls. Captain Elena's motto carved in.
4. **War Horse Thunder** (400): Loyal battle steed. Never abandons you. Eyes full of trust.
5. **Dragon Whelp Ember** (700): Young dragon, dog-sized. Playful but fierce. "Together we're unstoppable!"
6. **Enchanted Plate Armor** (1100): Forged from fallen stars. Glows in darkness. Lighter than doubt.
7. **Battle Dragon Crimson** (1500): Full-grown dragon ally. Magnificent and loyal. Chooses YOU as rider.
8. **The Legendary Blade** (1800): Ancient hero's sword. 'Unbending Will' in Old Tongue. Hums when focused.
9. **Ancient Dragon Grandis** (2000): Eldest dragon. Wise, shimmering scales. "I waited centuries for you."

### Scholar Theme Entities (The Infinite Library)
**Story Connection**: The library is alive with magical creatures and enchanted study tools. Your dedication attracts these helpful companions who live among the books.

1. **Library Mouse Pip** (10): White mouse in bookshelves. Squeaks at discoveries. Loves cheese and knowledge.
2. **Study Owl Athena** (50): Little owl on your desk. Keeps you awake. "Whoo's studying? You are!"
3. **Enchanted Quill** (150): Self-inking quill. Never runs dry. Writes smoother when focused.
4. **Library Cat Scholar** (400): Orange tabby guardian. Purrs at progress. Knows all secrets.
5. **Living Bookmark Finn** (700): Magical bookmark. Remembers every page. Glows at breakthroughs.
6. **Sentient Tome Magnus** (1100): Ancient book with personality. Self-turning pages. Grumbles and celebrates.
7. **Archive Phoenix** (1500): Bird made of living parchment. Preserves work in flames. Knowledge transforms.
8. **Celestial Atlas** (1800): Star-map book. Shows constellation of connected ideas. Maps your journey.
9. **The Grand Librarian** (2000): Shimmering spirit. Read every book. Light between shelves. "You ARE becoming knowledge."

### Wanderer Theme Entities (The Endless Road)
**Story Connection**: Every traveler collects special objects and loyal companions on their journey. These are the real tools and friends that make the road feel like home.

1. **Lucky Coin** (10): Old copper coin. Always lands tails. "Tails never fails!"
2. **Brass Compass** (50): Worn compass. Never lost. Needle spins cheerfully. North is your choice.
3. **Journey Journal** (150): Leather diary. Writes itself. Records milestones. Smells like adventure and coffee.
4. **Road Dog Wayfinder** (400): Scruffy loyal companion. Never judges. Knows the way. Best friend on four legs.
5. **Self-Drawing Map** (700): Magical map. Sketches as you travel. Shows conquered places with pride.
6. **Wanderer's Carriage** (1100): Cozy wooden caravan. Bigger inside. Warm fireplace. Tea always ready.
7. **Sky Balloon Explorer** (1500): Rainbow-striped hot air balloon. Takes you above clouds. "All roads lead forward!"
8. **Timeworn Backpack** (1800): Weathered pack. Infinite supplies. Journey patches. Weighs nothing but memories.
9. **The Horizon Star** (2000): Sentient constellation. Guides all wanderers. Shines when lost. "Follow me to who you'll become."

### Underdog Theme Entities (Rise of the Underdog)
**Story Connection**: Your workplace and daily life are full of humble items and unlikely companions that inspire you. These everyday objects become symbols of your rising journey.

1. **Office Rat Reginald** (10): Friendly gray desk rat. Eats crumbs. Tiny squeaks. "Small creatures understand big dreams!"
2. **Lucky Stapler** (50): Red stapler. Never jams. Perfect clicks. Started at bottom of closet, now indispensable.
3. **Vending Machine Coin** (150): Mysterious quarter. Always returns with a friend. Drop one, get two items.
4. **Window Pigeon Winston** (400): Gray pigeon. Taps morse code. Brings brilliant ideas. "Coo-COO! I believe in you!"
5. **Desk Succulent Sam** (700): Tiny cactus. Refuses to die. Thrives in harsh conditions. "Survive fluorescent lights, survive anything!"
6. **Perfect Coffee Mug** (1100): Ceramic mug. Ideal temperature forever. Says "Underestimated Since Day One." Never breaks.
7. **AGI Assistant Claude** (1500): Advanced AI chatbot. Genuinely encouraging. Celebrates small wins. "Great questions today!"
8. **Corner Office Chair** (1800): Legendary ergonomic throne. Perfectly worn-in. Incredibly comfortable. "You've earned this seat."
9. **The Promotion Letter** (2000): Glowing document. Appears when proven. Real proof you made it. "You were never an imposter. You were always becoming this."

---

## 13. Success Metrics

Track these metrics to evaluate feature success:
- **Engagement**: % of users who view Entitidex tab daily
- **Retention**: Do users with entities complete more sessions?
- **Session Length**: Do users extend sessions hoping for encounters?
- **Completion Rate**: % who collect all entities (should be challenging but achievable)
- **Time to Complete**: Average days to full collection
- **Catch Success Rate**: Are probabilities feeling fair? (target: 35-45% overall)

---

## 14. Integration with Story System

### Story-Specific Entity Themes

The Entitidex is deeply integrated with the existing story system from `STORY_DEVELOPMENT_GUIDE.md`. Each current story theme has its own entity pool:

| Story ID | Story Title | Entity Theme | Narrative Connection |
|----------|-------------|--------------|---------------------|
| `warrior` | The Iron Focus | Dragons, weapons, armor, loyal beasts | Marcus's growing arsenal and companions on his journey |
| `scholar` | The Infinite Library | Library creatures, enchanted study tools | The living magic of the library that helps researchers |
| `wanderer` | The Endless Road | Travel gear, journey companions | The tools and friends every wanderer collects |
| `underdog` | Rise of the Underdog | Office items, workplace companions | Everyday objects that inspire your comeback story |
| `scientist` | The Breakthrough Protocol | Lab companions and research artifacts | Experimental allies that reward disciplined iteration |
| `robot` | The Assembly of Becoming | Factory companions and sentient machine allies | Companions that embody autonomy, responsibility, and freedom |

### Narrative Connections

**The Warrior Story (Marcus Thorne):**
- As Marcus grows in power, more legendary creatures seek his banner
- The "Ancient Dragon Grandis" (#009) is the ultimate ally Captain Elena spoke of
- Each dragon represents a stage of Marcus's mastery of focus
- Collecting these entities = building the army of focus Marcus needs to resist General Kade

**The Scholar Story (The Infinite Library):**
- The library is alive with helpful creatures and magical study tools
- "The Grand Librarian" spirit represents the library's ultimate secret
- Each entity helps overcome a different research challenge
- Collecting them all reveals the library's deepest wisdom

**The Wanderer Story:**
- Every traveler collects meaningful objects and loyal companions
- "The Horizon Star" (#009) guides all wanderers to their true destination
- Each entity represents a physical reminder of how far you've come
- Capturing all 9 = your backpack is full of journey treasures

**The Underdog Story:**
- Humble office items become symbols of your rising story
- "The Promotion Letter" (#009) is the tangible proof you've made it
- Each item reminds you that extraordinary things start ordinary
- Success comes from unlikely places—even an office rat believes in you

### Story Integration Code

```python
# In entitidex/entity_pools.py
def get_entity_pool_for_story(story_id: str) -> list:
    """Get entity pool matching the user's active story."""
    # Maps story IDs to entity pools
    STORY_TO_POOL = {
        "warrior": ENTITY_POOLS["warrior"],
        "scholar": ENTITY_POOLS["scholar"],
        "wanderer": ENTITY_POOLS["wanderer"],
        "underdog": ENTITY_POOLS["underdog"],
    }
    
    return STORY_TO_POOL.get(story_id, ENTITY_POOLS["warrior"])  # Default to warrior

# In entitidex/encounter_system.py
def trigger_encounter(adhd_buster: dict) -> Optional[Entity]:
    """Trigger entity encounter based on user's active story."""
    active_story = adhd_buster.get("active_story", "warrior")
    
    # Get story-specific entity pool
    entity_pool = get_entity_pool_for_story(active_story)
    
    # Select entity based on hero power
    hero = adhd_buster["story_heroes"][active_story]
    hero_power = calculate_total_power(hero)
    
    entity = select_encounter_entity(
        entity_pool=entity_pool,
        user_progress=hero.get("entitidex_progress", {}),
        hero_power=hero_power
    )
    
    return entity
```

### Encounter Flavor Text by Story

When an entity appears, the message should be story-appropriate:

**Warrior Theme:**
```
"A companion seeks your banner!"
"Another ally has heard of your growing strength!"
"Something magnificent approaches through the mist..."
```

**Scholar Theme:**
```
"A curious presence appears in the Library..."
"Your dedication has attracted a kindred spirit."
"Between the shelves, something magical stirs..."
```

**Wanderer Theme:**
```
"A traveler crosses your path!"
"Someone wants to join your journey."
"The road brings you a new friend..."
```

**Underdog Theme:**
```
"Something in the office wants to meet you!"
"A workplace ally appears!"
"You've caught someone's attention...in a good way."
```

### Chapter Unlock Synergy

Entity power levels are designed to align with story chapter thresholds:

| Chapter | Power Threshold | Catchable Entities |
|---------|-----------------|--------------------|
| Chapter 1 | 0 | #001-#002 (10-50) |
| Chapter 2 | 50 | #002-#003 (50-150) |
| Chapter 3 | 150 | #003-#004 (150-400) |
| Chapter 4 | 400 | #004-#005 (400-700) |
| Chapter 5 | 700 | #005-#006 (700-1100) |
| Chapter 6 | 1100 | #006-#007 (1100-1500) |
| Chapter 7 | 1500 | #007-#009 (1500-2000) |

This creates natural progression: as you unlock new chapters, you can catch stronger entities.

### Entitidex Completion Rewards

Tying to story completion:

```python
STORY_COMPLETION_REWARDS = {
    "warrior": {
        "25%": {"item": "Iron Focus Badge", "power": 50},
        "50%": {"item": "Captain's Commendation", "power": 100},
        "75%": {"item": "Elena's Training Gloves", "power": 150},
        "100%": {"item": "Marcus's Eternal Resolve", "power": 300, "title": "Master of Focus"},
    },
    "scholar": {
        "25%": {"item": "Footnote Tamer", "power": 50},
        "50%": {"item": "The Finished Thesis", "power": 100},
        "75%": {"item": "Dean's Nightmare", "power": 150},
        "100%": {"item": "The Infinite Answer", "power": 300, "title": "Library Master"},
    },
    "wanderer": {
        "25%": {"item": "First Mile Marker", "power": 50},
        "50%": {"item": "Wanderer's Compass", "power": 100},
        "75%": {"item": "Endless Endurance", "power": 150},
        "100%": {"item": "The Road Eternal", "power": 300, "title": "Horizon Walker"},
    },
    "underdog": {
        "25%": {"item": "First Victory Trophy", "power": 50},
        "50%": {"item": "Hater Silencer", "power": 100},
        "75%": {"item": "Late Bloomer Crown", "power": 150},
        "100%": {"item": "Comeback King's Scepter", "power": 300, "title": "Underdog Legend"},
    },
}
```

### Cross-Story Collection (Future)

For users who play multiple stories:
```python
# Achievement: "Multiverse Master"
# Unlock by catching all entities in 2+ stories
# Reward: Special "Transcendent" entity that appears in all stories
```

---

## 15. Future Expansion Ideas

- **Breeding System**: Combine two entities to create variants
- **Entity Powers**: Caught entities provide passive bonuses
- **Companion Adventures**: Send caught entities on passive missions for rewards
- **Expeditions**: Special modes to hunt for specific entities
- **Mega Evolutions**: Power up entities you've caught multiple times
- **Photo Mode**: Take screenshots with your collected entities
- **Trading Cards**: Export collection as shareable images

---

## Conclusion

The Entitidex system provides:
✅ Long-term progression goals (collection completion)
✅ Exciting random encounters after productive sessions
✅ Risk/reward decision making (engage or flee)
✅ Lottery-style dopamine hits
✅ Story integration and world-building
✅ Scalable design for future content
✅ Psychological hooks to increase app engagement

This system turns focus sessions into "pokemon hunting expeditions" while maintaining the core productivity goals of the application.
