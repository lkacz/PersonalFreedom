# Story Development Guide

**Personal Liberty - ADHD Buster Gamification System**

*Guide for creating new story content and scaling the narrative system*

> Canonical reference: `STORY_THEME_EXTENSION_SPEC.md`
>  
> If this guide conflicts with `STORY_THEME_EXTENSION_SPEC.md`, follow the spec file.

---

## Table of Contents

1. [Story System Overview](#story-system-overview)
2. [Story Architecture](#story-architecture)
3. [Adding a New Story - Complete Walkthrough](#adding-a-new-story---complete-walkthrough)
4. [Story Components Breakdown](#story-components-breakdown)
5. [Gear Theme Design Guidelines](#gear-theme-design-guidelines)
6. [Character Design Specifications](#character-design-specifications)
7. [Narrative Content Guidelines](#narrative-content-guidelines)
8. [Testing Checklist](#testing-checklist)
9. [Best Practices & Considerations](#best-practices--considerations)
10. [Future Expansion Ideas](#future-expansion-ideas)

---

## Story System Overview

The ADHD Buster gamification system uses **story themes** to contextualize the player's productivity journey. Each story provides:

- **Unique narrative context** - Why are you focusing? What's the motivation?
- **Themed equipment** - Gear items styled to match the story's world
- **Character identity** - Visual representation with story-specific design
- **Progressive narrative** - Chapters that unlock as you advance
- **Separate progression** - Each story has its own hero, inventory, and equipped gear

### Current Stories (v3.1.4)

| Story ID | Title | Theme | Target Audience |
|----------|-------|-------|-----------------|
| `warrior` | The Iron Focus | Medieval warrior battling distractions | Traditional gamers, achievement-oriented |
| `scholar` | The Infinite Library | Scholar seeking ancient knowledge | Book lovers, researchers, students |
| `wanderer` | The Endless Road | Traveler exploring focus landscapes | Explorers, creative types |
| `underdog` | Rise of the Underdog | Underdog proving themselves | Late bloomers, comeback seekers |

**New Feature**: Each story now includes an **Entitidex** - a collectible entity system where users encounter and capture story-themed entities after focus sessions (see `ENTITIDEX_DESIGN.md` for details).

---

## Story Architecture

### File Structure

```
PersonalFreedom/
├── gamification.py          # Core story + gear + rewards
│   ├── STORY_GEAR_THEMES    # Gear theme definitions (story-themed drops)
│   ├── AVAILABLE_STORIES    # Story registry (title/description/theme)
│   ├── <STORY>_DECISIONS    # Per-story decisions (Ch 2/4/6)
│   ├── <STORY>_CHAPTERS     # Per-story chapter list (currently 7 chapters)
│   ├── STORY_DATA           # Maps story_id -> {decisions, chapters}
│   ├── get_chapter_content()# Renders chapters w/ branching + placeholders
│   └── generate_item()      # Item generation (stores story_theme)
├── focus_blocker_qt.py      # UI implementation
│   └── CharacterCanvas      # Visual character rendering (line 7234)
└── config.json              # User's story data
    ├── active_story         # Currently selected story
    ├── story_mode           # Mode: "story", "hero_only", "disabled"
    ├── story_heroes         # Hero data per story (created lazily per story)
    │   └── [story_id]
    │       ├── inventory            # Story-specific items
    │       ├── equipped             # Story-specific gear
    │       ├── story_decisions      # Decision choices by decision_id
    │       ├── diary                # Story-specific diary entries
    │       └── max_power_reached    # For chapter unlock progress display
    └── free_hero            # Hero-only mode data
```

### Data Flow

```
User Action (Focus Session)
    ↓
Generate Reward (with story_id)
    ↓
Create Item (themed to story)
    ↓
Add to Inventory (defensive copy)
    ↓
Save Config → Sync Hero Data → Save Again
    ↓
Display in Hero Tab (story-specific view)
```

---

## Adding a New Story - Complete Walkthrough

### Step 1: Define Story Metadata

**File:** `gamification.py`  
**Location:** `AVAILABLE_STORIES` dict (search for `AVAILABLE_STORIES = {`)

```python
AVAILABLE_STORIES = {
    "warrior": {...},
    "scholar": {...},
    "wanderer": {...},
    "underdog": {...},
    
    # ADD NEW STORY HERE
    "explorer": {
        "id": "explorer",
        "title": "🗺️ The Lost Expedition",
        "description": "Lead an expedition to uncover forgotten ruins and the discipline to survive them.",
        "theme": "adventure",
    },
}
```

**Required Fields:**
- `id` - Must match the dict key (e.g., key `"explorer"` => `"id": "explorer"`)
- `title` - Display name (emoji is typically embedded directly here)
- `description` - One-sentence pitch
- `theme` - Free-form tag (flavor/organization)

### Step 2: Create Gear Theme

**File:** `gamification.py`  
**Location:** `STORY_GEAR_THEMES` dict (near the top; search for `STORY_GEAR_THEMES = {`)

**Important**: Also create matching entities for the **Entitidex** system. See `ENTITIDEX_DESIGN.md` for entity creation guidelines. Your entities should thematically match your story's narrative and provide tangible companions.

```python
STORY_GEAR_THEMES = {
    "warrior": {...},
    "scholar": {...},
    "wanderer": {...},
    "underdog": {...},
    
    # ADD GEAR THEME HERE
    "explorer": {
        "theme_id": "explorer",
        "theme_name": "🗺️ Expedition Gear",
        "slot_display": {
            "Helmet": "Hat",
            "Chestplate": "Vest",
            "Gauntlets": "Gloves",
            "Boots": "Boots",
            "Shield": "Map",
            "Weapon": "Tool",
            "Cloak": "Coat",
            "Amulet": "Charm",
        },
        "item_types": {
            "Helmet": ["Pith Helmet", "Safari Hat", "Expedition Cap", "Trail Hood"],
            "Chestplate": ["Explorer Vest", "Field Jacket", "Rope Harness", "Canvas Rig"],
            "Gauntlets": ["Mapping Gloves", "Climbing Gloves", "Artifact Mitts", "Grip Wraps"],
            "Boots": ["Trekking Boots", "Jungle Boots", "Ruin Walkers", "Trail Treads"],
            "Shield": ["Field Map", "Compass Case", "Survey Board", "Travel Ledger"],
            "Weapon": ["Machete", "Expedition Pick", "Ruin Prybar", "Survey Hammer"],
            "Cloak": ["Rain Cloak", "Dust Coat", "Expedition Cape", "Weathered Wrap"],
            "Amulet": ["Compass Pendant", "Stone Medallion", "Relic Charm", "Marker Token"],
        },
        "adjectives": {
            "Common": ["Weathered", "Dusty", "Dented", "Scuffed"],
            "Uncommon": ["Reliable", "Reinforced", "Trail-tested", "Surveyor's"],
            "Rare": ["Ancient", "Inscribed", "Well-kept", "Artifact-bound"],
            "Epic": ["Mythic", "Ruin-born", "Storm-hardened", "Lost-era"],
            "Legendary": ["World-mapped", "History-forged", "Unbreakable", "Everfound"],
        },
        "suffixes": {
            "Common": ["the Trail", "Dust and Mosquitos", "Bad Weather", "Loose Screws"],
            "Uncommon": ["Discovery", "the Expedition", "Safe Passage", "Steady Hands"],
            "Rare": ["the Ruins", "Old Warnings", "Hidden Doors", "Lost Pages"],
            "Epic": ["Sunken Vaults", "Forbidden Chambers", "Storm Seasons", "Mapless Lands"],
            "Legendary": ["the First Compass", "Uncharted Truth", "the Last Landmark", "Eternal Return"],
        },
    },
}
```

**Design Guidelines:**
- **8 gear slots** are required (Helmet, Chestplate, Gauntlets, Boots, Shield, Weapon, Cloak, Amulet)
- **`item_types` should include multiple base names per slot** (4+ is a good minimum)
- **`adjectives` + `suffixes` must define all rarities** (Common → Legendary)
- **Thematic consistency** - items should feel cohesive

### Step 3: Write Narrative Chapters

**File:** `gamification.py`  
**Location:** Per-story chapter lists (e.g., `WARRIOR_CHAPTERS`) + `STORY_DATA`

```python
# 1) Define decisions (currently 3 decisions total, at chapters 2/4/6).
EXPLORER_DECISIONS = {
    2: {
        "id": "explorer_map",
        "prompt": "The jungle splits into three routes, but you can only commit to one approach.",
        "choices": {
            "A": {"label": "🧭 Take the Safe Route", "short": "steady", "description": "Slower progress, fewer risks."},
            "B": {"label": "⛏️ Cut Through the Unknown", "short": "bold", "description": "Faster progress, higher stakes."},
        },
    },
    4: {"id": "explorer_relic", "prompt": "...", "choices": {"A": {"label": "...", "short": "...", "description": "..."}, "B": {"label": "...", "short": "...", "description": "..."}}},
    6: {"id": "explorer_return", "prompt": "...", "choices": {"A": {"label": "...", "short": "...", "description": "..."}, "B": {"label": "...", "short": "...", "description": "..."}}},
}

# 2) Define chapters as a 7-entry list (unlock by POWER thresholds, not XP level).
EXPLORER_CHAPTERS = [
    {"title": "Chapter 1: The Edge of the Map", "threshold": 0, "has_decision": False, "content": "..."},
    {"title": "Chapter 2: First Markings", "threshold": 50, "has_decision": True, "decision_id": "explorer_map", "content": "...", "content_after_decision": {"A": "...", "B": "..."}},
    # Chapters 3-6...
    {"title": "Chapter 7: What the Ruins Reveal", "threshold": 1500, "has_decision": False, "content": "...", "endings": {"AAA": {"content": "..."}, "AAB": {"content": "..."}, "ABA": {"content": "..."}, "ABB": {"content": "..."}, "BAA": {"content": "..."}, "BAB": {"content": "..."}, "BBA": {"content": "..."}, "BBB": {"content": "..."}}},
]

# 3) Register the story so the engine can find its chapters/decisions.
STORY_DATA["explorer"] = {"decisions": EXPLORER_DECISIONS, "chapters": EXPLORER_CHAPTERS}
```

**Chapter Writing Guidelines:**
- **Current engine structure:** 7 chapters (1–7)
- **Unlocking is based on power thresholds** (from equipped gear), not XP level
- **Connect to gameplay** - Reference focus sessions, persistence, concentration
- **Escalating stakes** - Each chapter should feel more significant
- **Narrative payoff** - Build towards a satisfying conclusion
- **Markdown formatting** - Use **bold** and *italics* for emphasis
- **Paragraph breaks** - Keep it readable (2-3 paragraphs per chapter)

**Personalization placeholders (as implemented in `get_chapter_content()`):**
- `{helmet}`, `{weapon}`, `{chestplate}`, `{shield}`, `{gauntlets}`, `{boots}`, `{cloak}`, `{amulet}`, `{current_power}`

**Branching (as implemented):**
- **Decisions:** Chapters 2, 4, and 6 present a decision with two choices: `A` or `B`.
- **After-decision text:** Use `content_after_decision["A"|"B"]` to append consequences when re-reading.
- **Variations:** Non-decision chapters may include `content_variations` keyed by decision-path prefixes (e.g., `"A"`, `"AB"`).
- **Endings:** Chapter 7 may define `endings` for each full 3-choice path (`AAA`…`BBB`) = 8 endings.

### Step 4: Implement Character Rendering

**File:** `focus_blocker_qt.py`  
**Location:** `CharacterCanvas` class (around line 7234)

Add a new rendering method for your story's character:

```python
def paintEvent(self, event) -> None:
    """Main paint event - delegates to story-specific renderer."""
    story_theme = self.story_theme
    
    if story_theme == "warrior":
        self._draw_warrior_character(event)
    elif story_theme == "scholar":
        self._draw_scholar_character(event)
    elif story_theme == "wanderer":
        self._draw_wanderer_character(event)
    elif story_theme == "underdog":
        self._draw_underdog_character(event)
    # ADD NEW CHARACTER RENDERER HERE
    elif story_theme == "explorer":
        self._draw_explorer_character(event)
    else:
        self._draw_warrior_character(event)  # Fallback

def _draw_explorer_character(self, event) -> None:
    """Draw explorer character with expedition gear."""
    painter = QtGui.QPainter(self)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    
    # Draw tier-specific glow/particles
    self._draw_tier_effects(painter)
    
    # Character base (explorer silhouette)
    painter.setPen(QtGui.QPen(QtGui.QColor("#8B4513"), 3))  # Brown outline
    painter.setBrush(QtGui.QColor("#D2691E"))  # Tan/khaki color
    
    # Head (circle)
    painter.drawEllipse(65, 20, 50, 50)
    
    # Body (rectangle with rounded corners)
    painter.drawRoundedRect(60, 70, 60, 70, 5, 5)
    
    # Arms (vest with utility pockets)
    painter.drawLine(60, 80, 40, 120)  # Left arm
    painter.drawLine(120, 80, 140, 120)  # Right arm
    
    # Legs (sturdy expedition pants)
    painter.drawLine(75, 140, 70, 180)  # Left leg
    painter.drawLine(105, 140, 110, 180)  # Right leg
    
    # Equipment visualization (based on slots)
    self._draw_equipped_indicators(painter, "explorer")
    
    # Power number display
    painter.setPen(QtGui.QColor("#FFD700"))  # Gold
    painter.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
    painter.drawText(QtCore.QRect(0, 190, 180, 30), 
                     QtCore.Qt.AlignCenter, 
                     f"⚡ {self.power}")
    
    painter.end()
```

**Rendering Guidelines:**
- **Consistent dimensions** - Keep within 180x220 canvas
- **Story-appropriate colors** - Match the theme aesthetics
- **Simple shapes** - Use basic Qt drawing primitives (circles, rectangles, lines)
- **Visual feedback** - Show equipped items somehow (icons, colors, effects)
- **Tier effects** - Use `_draw_tier_effects()` for power-based visuals

### Step 5: Initialize Default Hero Data

**File:** `gamification.py`  
**Location:** `ensure_hero_structure()` function (around line 7083)

The current implementation uses a **hero-per-story** model stored in `adhd_buster["story_heroes"]`.
Heroes are created **lazily** when a story is first selected (or when `active_story` points at it).

```python
def ensure_hero_structure(adhd_buster: dict) -> dict:
    """Ensure hero management keys exist and the active story has a hero."""
    # Creates/ensures:
    #   adhd_buster["story_heroes"], adhd_buster["free_hero"], adhd_buster["active_story"], ...
    # Ensures there is a hero dict for the active story in story_heroes.
    return adhd_buster
```

✅ **No code changes needed** - New story heroes are auto-created when selected.

### Step 6: Test Integration

**File:** `test_item_award.py` (create or modify)

```python
def test_new_story():
    """Test item generation for new story."""
    from gamification import generate_item, ensure_hero_structure
    
    # Mock adhd_buster
    adhd_buster = {
        "active_story": "explorer",
        "story_mode": "story",
    }
    
    # Initialize structure
    ensure_hero_structure(adhd_buster)
    assert "story_heroes" in adhd_buster
    assert "explorer" in adhd_buster["story_heroes"]
    
    # Generate item
    item = generate_item(rarity="Rare", story_id="explorer")
    
    # Validate
    assert item is not None
    assert item["story_theme"] == "explorer"
    assert item["rarity"] == "Rare"
    assert "slot" in item
    assert "name" in item
    
    print(f"✓ Generated: {item['name']} ({item['rarity']} {item['slot']})")

if __name__ == "__main__":
    test_new_story()
```

---

## Story Components Breakdown

### Entity Design for Entitidex (New Requirement)

When creating a new story, you must also design **9 collectible entities** for the Entitidex system. These entities should be thematically integrated with your story's narrative.

#### Entity Design Principles

**1. Entities as Tangible Companions**
Your entities should be **real, tangible objects and creatures** that users could imagine meeting in real life:
- **Warrior**: Dragons, weapons, armor, loyal beasts (dragons, enchanted swords, war horses)
- **Scholar**: Library creatures, magical study tools (mice, owls, sentient books, enchanted quills)
- **Wanderer**: Travel gear, journey companions (compasses, maps, loyal dogs, magical backpacks)
- **Underdog**: Office items, workplace companions (desk pets, lucky staplers, AI assistants, pigeons)

**2. Power Progression** (10 → 2000)
Distribute power levels across 9 entities:
```python
[10, 50, 150, 400, 700, 1100, 1500, 1800, 2000]
```

Map to rarities:
- #001-#002: Common (10-50)
- #003: Uncommon (150)
- #004-#005: Rare (400-700)
- #006-#007: Epic (1100-1500)
- #008-#009: Legendary (1800-2000)

**3. Story Integration**
Connect entities to your narrative:
- Reference story characters (e.g., "Captain Elena warns about this one")
- Link to chapter themes (e.g., Chapter 4's choice relates to entity #005)
- Use story-specific terminology
- Create narrative payoff (final entity represents story's ultimate challenge)

#### Entity Creation Template

```python
{
    "id": "<story>_00X",
    "name": "Tangible Companion Name",
    "power": XXX,
    "rarity": "common|uncommon|rare|epic|legendary",
    "lore": "2-3 sentences. Make it real and touchable. Give it personality. Users should want to collect it!"
}
```

#### Example: Explorer Story Entities

If you were creating "The Lost Expedition" explorer story:

```python
"explorer": [
    {"id": "explorer_001", "name": "Expedition Mouse Mapley", "power": 10, "rarity": "common",
     "lore": "A tiny mouse who rides in your pack. Squeaks when danger approaches. 'I'll be your lookout!'"},
    {"id": "explorer_002", "name": "Trusty Canteen", "power": 50, "rarity": "common",
     "lore": "An old canteen that never runs empty. 'Stay hydrated, explorer. The ruins await.'"},
    {"id": "explorer_003", "name": "Trail Machete", "power": 150, "rarity": "uncommon",
     "lore": "A well-worn blade that cuts through any obstacle. Inscribed: 'The path reveals itself to those who clear it.'"},
    {"id": "explorer_004", "name": "Expedition Parrot Polly", "power": 400, "rarity": "rare",
     "lore": "A colorful parrot who scouts ahead and mimics ancient languages. 'Squawk! Treasure ahead!'"},
    {"id": "explorer_005", "name": "Self-Healing Rope", "power": 700, "rarity": "rare",
     "lore": "An enchanted rope that mends itself. Never frays. 'I'll always hold you up when you're climbing.'"},
    {"id": "explorer_006", "name": "Ancient Translation Stone", "power": 1100, "rarity": "epic",
     "lore": "A glowing crystal that translates any ancient language. Hums with millennia of wisdom. 'The secrets are yours now.'"},
    {"id": "explorer_007", "name": "Expedition Jaguar Shadow", "power": 1500, "rarity": "epic",
     "lore": "A sleek jungle cat who adopted you. Silent, powerful, protective. Leads you through the darkest paths."},
    {"id": "explorer_008", "name": "The Map That Remembers", "power": 1800, "rarity": "legendary",
     "lore": "A living map created by a thousand explorers. Shows every discovered ruin. 'Your discoveries add to my legend.'"},
    {"id": "explorer_009", "name": "Spirit of Discovery", "power": 2000, "rarity": "legendary",
     "lore": "A golden compass that points to your heart's true destination. 'I am every explorer's final companion. Welcome to the found.'"},
]
```

#### Entity Naming Conventions

**Good Entity Names:**
- Descriptive of the challenge: "Blank Page Demon", "Analysis Paralysis Sphinx"
- Story-appropriate tone: Medieval for warrior, academic for scholar
- Memorable and unique: "The Success Paradox", "Rock Bottom's Reflection"
- Escalating threat: Early entities sound minor, late ones sound epic

**Avoid:**
- Generic names: "Entity 1", "Companion 3"
- Inconsistent tone: Mixing modern slang with medieval fantasy (unless it's the Underdog story)
- Overly long names: "The Really Really Special Ultimate Amazing Super Dragon"
- Abstract concepts: Make them tangible things you could see, touch, or pet

#### Lore Writing Guidelines

Each entity needs **2-3 sentence lore** that:

1. **Describes the challenge**: What does this entity represent?
2. **Connects to story**: Reference characters, plot points, or themes
3. **Personal impact**: How does it affect the hero's journey?

**Example Analysis:**

```
"A gray pigeon who taps morse code on your window. Brings brilliant ideas right when you need them. 'Coo-COO! I believe in you!'"
                ↓                                    ↓                                    ↓
         What it IS                        What it DOES                          Personality/Quote
    (tangible creature)               (helpful ability)                       (makes you love it)
```

#### Testing Your Entities

**Thematic Consistency Check:**
- [ ] Do all 9 entities feel like they belong in the same world?
- [ ] Do they reference your story's narrative?
- [ ] Do early entities feel "humble beginnings" and late ones feel "ultimate companion"?
- [ ] Would a player WANT to collect all of them? Are they likable?

**Power Balance Check:**
- [ ] Powers match the standard distribution (10, 50, 150, 400, 700, 1100, 1500, 1800, 2000)
- [ ] Rarities assigned correctly (common for <100, legendary for 1800+)
- [ ] Each entity has clear progression (not random jumps)

**Naming Quality Check:**
- [ ] Names are unique within your entity pool
- [ ] Tone matches your story (serious vs. humorous vs. dramatic)
- [ ] No duplicates with other stories' entities
- [ ] Memorable enough that players will discuss them

#### Integration with Story Chapters

Align entity power with chapter unlock thresholds:

```python
# Your story chapters
EXPLORER_CHAPTERS = [
    {"title": "Chapter 1: The Edge of the Map", "threshold": 0, ...},      # Players can catch: #001-#002
    {"title": "Chapter 2: First Markings", "threshold": 50, ...},          # Players can catch: #002-#003
    {"title": "Chapter 3: Into the Unknown", "threshold": 150, ...},       # Players can catch: #003-#004
    {"title": "Chapter 4: The Depths", "threshold": 400, ...},             # Players can catch: #004-#005
    {"title": "Chapter 5: The Discovery", "threshold": 700, ...},          # Players can catch: #005-#006
    {"title": "Chapter 6: The Truth", "threshold": 1100, ...},             # Players can catch: #006-#007
    {"title": "Chapter 7: The Return", "threshold": 1500, ...},            # Players can catch: #007-#009
]

# Reference entities in chapter text:
"Chapter 4 content": "A colorful parrot joins your expedition. It scouts ahead, calling out warnings in ancient tongues..."
# This connects to entity #004: "Expedition Parrot Polly" (400 power)
```

#### Entity Unlock Hints

For uncaught entities, display hints that build anticipation:

```python
# Instead of showing the entity name, show:
"Hint: A tiny companion that loves cheese and discoveries..." # (Expedition Mouse Mapley)
"Hint: A feathered friend who speaks ancient languages..." # (Expedition Parrot Polly)
"Hint: The ultimate guide to everywhere you've been searching..." # (Spirit of Discovery)
```

---

## Story Components Breakdown

### Item Generation Flow

```python
# User completes focus session
session_minutes = 60

# Determine rarity based on session length
rarity = "Rare"  # 1hr session

# Get active story
active_story = adhd_buster.get("active_story", "warrior")

# Generate themed item
item = generate_item(rarity=rarity, story_id=active_story)
# Returns: {
#   "name": "Ancient Expedition Pick of Discovery",
#   "rarity": "Rare",
#   "slot": "Weapon",
#   "power": 50,
#   "color": "#4169E1",
#   "story_theme": "explorer",
#   "obtained_at": "2026-01-11T15:30:00"
# }

# Add to inventory (DEFENSIVE COPY!)
adhd_buster["inventory"].append(item.copy())

# Save → Sync → Save pattern
blocker.save_config()
sync_hero_data(adhd_buster)
blocker.save_config()
```

### Rarity Distribution System

**Session Length → Rarity Probabilities:**

| Duration | Common | Uncommon | Rare | Epic | Legendary |
|----------|--------|----------|------|------|-----------|
| <30min   | 50%    | 30%      | 15%  | 4%   | 1%        |
| 30min    | 75%    | 20%      | 5%   | 0%   | 0%        |
| 1hr      | 25%    | 50%      | 20%  | 5%   | 0%        |
| 2hr      | 5%     | 20%      | 50%  | 20%  | 5%        |
| 3hr      | 0%     | 5%       | 20%  | 50%  | 25%       |
| 4hr      | 0%     | 0%       | 5%   | 20%  | 75%       |
| 6hr+     | 0%     | 0%       | 0%   | 0%   | 100%      |

**Bonus Items:**
- 7hr+ sessions: +20% chance for 2nd Legendary
- 8hr+ sessions: +50% chance for 2nd Legendary

### Power Calculation

```python
RARITY_POWER = {
    "Common": 10,
    "Uncommon": 25,
    "Rare": 50,
    "Epic": 100,
    "Legendary": 250,
}

# Total power = sum of equipped items
total_power = sum(item["power"] for item in equipped.values())

# Power tier determines visual effects
# pathetic (0-99), modest (100-249), decent (250-499), 
# heroic (500-999), epic (1000-1999), legendary (2000-2999), 
# godlike (3000+)
```

---

## Gear Theme Design Guidelines

### Naming Formula

```
[Prefix] [Base Name] [Suffix]
└─────┘  └────────┘  └──────┘
Weathered Explorer's Pick of Discovery
  10+      5+ per     10+
options    slot     options
```

**Example Generation:**
- Common: "Explorer's Pick"
- Uncommon: "Weathered Explorer's Pick"
- Rare: "Ancient Explorer's Pick of Discovery"
- Epic: "Legendary Expedition Pick of the Ancients"
- Legendary: "Mythical Sacred Expedition Pick of Discovery"

### Thematic Consistency Checklist

- [ ] **Visual cohesion** - All items feel like they belong in the same world
- [ ] **Narrative fit** - Names match the story's tone and setting
- [ ] **Cultural accuracy** - Research real-world inspirations (if applicable)
- [ ] **Fantasy balance** - Legendary items should feel *powerful* but not ridiculous
- [ ] **Slot diversity** - Each slot should have distinct item types
- [ ] **Rarity progression** - Common → Legendary should feel meaningful

### Theme Examples by Genre

**Medieval Fantasy (Warrior):**
- Focus: Combat, honor, medieval warfare
- Materials: Iron, steel, enchanted metals
- Adjectives: Battle-worn, forged, blessed, cursed

**Academic/Library (Scholar):**
- Focus: Knowledge, research, ancient texts
- Materials: Parchment, ink, crystal, scrolls
- Adjectives: Ancient, forbidden, illuminated, arcane

**Nature/Travel (Wanderer):**
- Focus: Exploration, weather, terrain
- Materials: Leather, wood, stone, wind
- Adjectives: Weathered, wind-swept, nomadic, eternal

**Sport/Competition (Underdog):**
- Focus: Training, competition, proving yourself
- Materials: Sweatbands, jerseys, equipment
- Adjectives: Rookie, veteran, championship, legendary

---

## Character Design Specifications

### Visual Design Requirements

**Canvas Dimensions:**
- Width: 180px
- Height: 220px
- Bottom 30px reserved for power display

**Color Palette:**
- **Primary color** - Main character body/clothing (matches story theme)
- **Secondary color** - Accent/details (contrasts with primary)
- **Outline color** - Character border (usually darker shade of primary)
- **Power tier effects** - Dynamic based on total power (auto-handled)

### Tier Visual Effects (Auto-Applied)

| Tier | Power Range | Glow Color | Particle Count | Outline |
|------|-------------|------------|----------------|---------|
| Pathetic | 0-99 | None | 0 | Gray |
| Modest | 100-249 | None | 0 | Green tint |
| Decent | 250-499 | Light green | 0 | Green |
| Heroic | 500-999 | Blue | 4 particles | Blue |
| Epic | 1000-1999 | Purple | 6 particles | Purple |
| Legendary | 2000-2999 | Orange | 8 particles | Orange |
| Godlike | 3000+ | Gold | 12 particles | Gold |

### Drawing Tips (Qt/PySide6)

```python
# Basic shapes
painter.drawEllipse(x, y, width, height)  # Circles/ovals
painter.drawRect(x, y, width, height)     # Rectangles
painter.drawRoundedRect(x, y, w, h, rx, ry)  # Rounded rectangles
painter.drawLine(x1, y1, x2, y2)          # Lines
painter.drawPolygon([QPoint(x1,y1), QPoint(x2,y2), ...])  # Custom shapes

# Colors
painter.setPen(QtGui.QColor("#RRGGBB"))   # Outline color
painter.setBrush(QtGui.QColor("#RRGGBB")) # Fill color

# Transparency (for glows/effects)
painter.setOpacity(0.5)  # 0.0 = invisible, 1.0 = solid
```

### Story-Specific Visual Adaptation Guide

**Key Principle:** Each story should have a **distinct visual identity** that players immediately recognize.

#### Visual Style Categories

These categories are **art-direction buckets**. For grounded stories, treat glow/particles as **stylized UI emphasis** (tier feedback), not supernatural powers. For explicitly magical/fantasy stories, you may depict supernatural effects, but keep rules consistent.

**1. Historical/Medieval (Warrior, Knight)**

Palette example:
```python
PRIMARY = "#4A4A4A"      # Steel gray
SECONDARY = "#8B4513"    # Leather brown
ACCENT = "#FFD700"       # Gold trim
OUTLINE = "#2F2F2F"      # Dark iron
```

Character elements:
- Armor plates (rectangles with metallic sheen)
- Sharp, angular shapes (swords, shields)
- Heavy boots, thick gauntlets
- Cape/cloak flowing from shoulders

Equipment indicators:
- Weapon: small blade icon near right hand
- Shield: strapped to left arm
- Armor: plate lines on torso

**2. Academic/Scholarly (Scholar, Scientist)**

Palette example:
```python
PRIMARY = "#4B0082"      # Deep indigo
SECONDARY = "#DAA520"    # Golden accents
ACCENT = "#87CEEB"       # Light blue (clarity/knowledge)
OUTLINE = "#2E0854"      # Dark purple
```

Character elements:
- Robes/jacket lines (rounded shapes)
- Academic cap or neat hair silhouette
- Book, notebook, or clipboard in hand
- Spectacles (small circles on face)

Equipment indicators:
- Weapon-slot indicator: pen/quill/ruler icon (theme choice)
- Book icons as background motifs
- Stylized particles as dust/motes (visual emphasis only)

**3. Modern/Urban (Underdog, Athlete, Hacker)**

Palette example:
```python
PRIMARY = "#FF6B6B"      # Athletic red
SECONDARY = "#4ECDC4"    # Cyan accent
ACCENT = "#FFE66D"       # Bright yellow
OUTLINE = "#1A1A2E"      # Dark modern
```

Character elements:
- Casual clothing (hoodie, jersey)
- Sneakers (slightly detailed shoes)
- Cap or headband
- Simplified, clean lines
- Athletic/active pose

Equipment indicators:
- Weapon-slot indicator: sports gear icon (bat/ball/gloves)
- Accessories: headphones, wristbands
- Motion lines for energy

**4. Nature/Exploration (Wanderer, Explorer, Ranger)**

Palette example:
```python
PRIMARY = "#8B7355"      # Khaki/tan
SECONDARY = "#228B22"    # Forest green
ACCENT = "#D2691E"       # Terracotta
OUTLINE = "#654321"      # Dark brown
```

Character elements:
- Practical clothing (vest, pants)
- Visible gear (backpack outline)
- Weathered, lived-in appearance
- Rope coiled at side
- Wide-brimmed hat or bandana

Equipment indicators:
- Weapon-slot indicator: machete/pick silhouette
- Map/compass details
- Dirt/weathering marks (subtle)

**5. Sci-Fi/Futuristic (Cyborg, Astronaut, Android)**

Palette example:
```python
PRIMARY = "#0A0E27"      # Dark space blue
SECONDARY = "#00FFF0"    # Cyan tech
ACCENT = "#FF00FF"       # Neon magenta
OUTLINE = "#000000"      # Pure black
```

Character elements:
- Angular, geometric shapes
- Highlight lines (circuit patterns)
- Helmet/visor (horizontal line across face)
- Tech panels on armor
- Smooth, streamlined silhouette

Equipment indicators:
- Weapon-slot indicator: tech tool / blaster silhouette
- HUD-style overlays (lines/boxes), sparingly
- Pulsing highlight lights (UI emphasis)

**6. Fantasy/Magical (Sorcerer, Witch, Paladin)**

Use this category only when the story is clearly supernatural.

Palette example:
```python
PRIMARY = "#1B1B3A"      # Midnight blue
SECONDARY = "#4B0082"    # Deep violet
ACCENT = "#FFD700"       # Gold
OUTLINE = "#0B0B1A"      # Near-black
```

Character elements:
- Cloaks/robes (soft curves)
- Iconic silhouette (staff, talisman, cape collar)
- Runic patterns (simple lines, not busy)

Equipment indicators:
- Weapon-slot indicator: staff/blade with a faint glow
- Amulet-slot indicator: small gem/crest
- Particles/glow acceptable here (but keep intensity tied to tier/power)

#### Equipment Visualization Techniques

**Method 1: Icon Overlay**
```python
def _draw_equipped_indicators(self, painter, story_theme):
    """Draw small icons showing equipped gear."""
    equipped = self.equipped
    
    # Helmet - top of head
    if equipped.get("Helmet"):
        self._draw_gear_icon(painter, 80, 15, "helmet", story_theme)
    
    # Weapon - right hand area
    if equipped.get("Weapon"):
        self._draw_gear_icon(painter, 135, 100, "weapon", story_theme)
    
    # Shield - left hand area
    if equipped.get("Shield"):
        self._draw_gear_icon(painter, 35, 100, "shield", story_theme)

def _draw_gear_icon(self, painter, x, y, slot, theme):
    """Draw theme-appropriate gear icon."""
    if theme == "warrior":
        if slot == "weapon":
            # Draw sword
            painter.drawLine(x, y, x+5, y+15)
    elif theme == "scholar":
        if slot == "weapon":
            # Draw pen/quill
            painter.drawLine(x, y, x, y+18)
            painter.drawLine(x, y+18, x+4, y+14)
    # ... more themes
```

**Method 2: Color Variation**
```python
def _get_character_colors_by_power(self, base_colors, equipped):
    """Adjust character colors based on equipped gear quality."""
    avg_rarity = self._calculate_avg_rarity(equipped)
    
    if avg_rarity >= 4:  # Mostly Legendary
        # Add golden shimmer to colors
        return self._add_shimmer(base_colors, "#FFD700")
    elif avg_rarity >= 3:  # Mostly Epic
        # Add purple shimmer
        return self._add_shimmer(base_colors, "#9370DB")
    
    return base_colors
```

**Method 3: Emphasis/Glow Effects**
```python
def _draw_tier_effects(self, painter):
    """Draw glow/particle effects based on total power."""
    tier = self._get_power_tier()
    
    if tier in self.TIER_GLOW:
        glow_color = QtGui.QColor(self.TIER_GLOW[tier])
        glow_color.setAlpha(50)  # Semi-transparent
        
        # Draw glow ring around character
        painter.setPen(QtGui.QPen(glow_color, 8))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawEllipse(40, 40, 100, 140)
    
    # Draw particles for high tiers
    if tier in self.TIER_PARTICLES:
        color, count = self.TIER_PARTICLES[tier]
        self._draw_particles(painter, color, count)
```

#### Character Pose & Personality

**Matching Pose to Story Archetype:**

```python
# Warrior - Strong, grounded stance
body_x = 90
body_y_top = 70
body_y_bottom = 140
painter.drawLine(body_x, body_y_top, body_x, body_y_bottom)  # Straight vertical

# Scholar - Slightly hunched, reading pose
body_x = 90
body_y_top = 70
body_y_bottom = 145
painter.drawLine(body_x, body_y_top, body_x+5, body_y_bottom)  # Slight lean forward

# Wanderer - Dynamic, moving stance
body_x = 85
body_y_top = 70
body_y_bottom = 140
painter.drawLine(body_x, body_y_top, body_x+10, body_y_bottom)  # Leaning into motion

# Athlete - Active, energetic pose
# Draw with bent knees, arms in motion
left_arm_angle = 30  # Degrees
right_arm_angle = -30  # Opposite direction
```

#### Animation Considerations (Future Enhancement)

While the current system uses static images, consider these for future updates:

```python
# Breathing animation (subtle scale pulse)
# Idle particles floating around character
# Subtle highlight pulsing
# Cape/cloak subtle movement
# Power number flash on level up
```

#### Color Psychology by Story Type

| Story Type | Primary Emotion | Color Strategy | Example Palette |
|------------|-----------------|----------------|-----------------|
| Heroic Quest | Courage, nobility | Bold primaries, metallic accents | Red, Gold, Steel |
| Mystery/Investigation | Curiosity, intellect | Cool tones, muted accents | Navy, Silver, Teal |
| Survival/Adventure | Determination, grit | Earthy, natural tones | Brown, Green, Orange |
| Sci-Fi/Tech | Innovation, future | Neon accents, dark base | Black, Cyan, Magenta |
| Horror/Dark | Tension, fear | Desaturated, high contrast | Crimson, Shadow, Pale |
| Comedy/Light | Joy, energy | Bright, saturated | Yellow, Pink, Lime |

#### Practical Example: Complete Character Renderer

```python
def _draw_explorer_character(self, event) -> None:
    """Explorer character with expedition theme."""
    # Requires: import random
    painter = QtGui.QPainter(self)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    
    # Step 1: Draw tier effects (auto-handled glow/particles)
    self._draw_tier_effects(painter)
    
    # Step 2: Define theme colors
    khaki = QtGui.QColor("#8B7355")
    brown = QtGui.QColor("#654321")
    tan = QtGui.QColor("#D2B48C")
    
    # Step 3: Draw character body
    painter.setPen(QtGui.QPen(brown, 3))
    painter.setBrush(khaki)
    
    # Head (sun-tanned)
    painter.drawEllipse(65, 20, 50, 50)
    
    # Hat (wide-brimmed explorer hat)
    painter.setBrush(tan)
    painter.drawEllipse(55, 15, 70, 20)  # Brim
    painter.setBrush(brown)
    painter.drawEllipse(70, 10, 40, 25)  # Crown
    
    # Body (expedition vest)
    painter.setBrush(khaki)
    painter.drawRoundedRect(60, 70, 60, 70, 5, 5)
    
    # Vest pockets (detail)
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.drawRect(65, 80, 15, 10)  # Left pocket
    painter.drawRect(100, 80, 15, 10)  # Right pocket
    
    # Arms
    painter.setBrush(khaki)
    painter.drawLine(60, 80, 40, 120)  # Left arm
    painter.drawLine(120, 80, 140, 120)  # Right arm
    
    # Hands (holding equipment)
    painter.setBrush(tan)
    painter.drawEllipse(35, 115, 10, 10)  # Left hand
    painter.drawEllipse(135, 115, 10, 10)  # Right hand
    
    # Legs (sturdy pants)
    painter.setPen(QtGui.QPen(brown, 4))
    painter.drawLine(75, 140, 70, 180)  # Left leg
    painter.drawLine(105, 140, 110, 180)  # Right leg
    
    # Boots (heavy duty)
    painter.setBrush(brown)
    painter.drawEllipse(65, 175, 15, 12)  # Left boot
    painter.drawEllipse(105, 175, 15, 12)  # Right boot
    
    # Step 4: Draw equipped gear indicators
    if self.equipped.get("Weapon"):
        # Machete at side
        painter.setPen(QtGui.QPen(QtGui.QColor("#C0C0C0"), 2))  # Silver blade
        painter.drawLine(50, 100, 45, 130)
    
    if self.equipped.get("Shield"):  # Map as "shield"
        # Rolled map in hand
        painter.setPen(QtGui.QPen(QtGui.QColor("#F5DEB3"), 3))
        painter.drawLine(135, 120, 135, 135)
    
    if self.equipped.get("Amulet"):
        # Compass pendant
        painter.setBrush(QtGui.QColor("#FFD700"))
        painter.drawEllipse(87, 70, 6, 6)
    
    # Step 5: Add weathering/wear details
    painter.setOpacity(0.3)
    painter.setPen(QtGui.QPen(brown, 1))
    # Dirt marks on vest
    for _ in range(5):
        x = random.randint(65, 110)
        y = random.randint(75, 130)
        painter.drawLine(x, y, x+3, y)
    
    painter.setOpacity(1.0)
    
    # Step 6: Power display
    painter.setPen(QtGui.QColor("#D2691E"))  # Terracotta
    painter.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
    painter.drawText(QtCore.QRect(0, 190, 180, 30),
                     QtCore.Qt.AlignCenter,
                     f"Power: {self.power}")
    
    painter.end()
```

---

## Narrative Content Guidelines

### Dramatic Structure Framework (Screenwriting Best Practices)

Modern story development should follow proven dramatic structures from professional screenwriting. This creates emotionally engaging narratives that keep players invested across multiple focus sessions.

#### The Three-Act Structure (Applied to Progressive Chapters)

The current engine ships with **7 chapters per story** and **3 binary decisions**.
Use this structure so your story fits the implemented unlock + branching model.

**ACT I: Setup (Chapters 1–2)**
- **Chapter 1** - Ordinary World: establish the hero, weakness, and tone
- **Chapter 2** - Call + Decision 1: introduce the central conflict and make the first A/B choice

**ACT II: Confrontation (Chapters 3–6)**
- **Chapter 3** - Crossing the Threshold: commitment + first consequences
- **Chapter 4** - Rising Action + Decision 2: pressure increases; second A/B choice
- **Chapter 5** - Midpoint Twist: major reveal that reframes the journey (can branch via `content_variations`)
- **Chapter 6** - Dark Night + Decision 3: the hardest tradeoff; third A/B choice

**ACT III: Resolution (Chapter 7)**
- **Chapter 7** - Endings: 8 possible endings keyed by decision path (`AAA`…`BBB`)

### Essential Story Elements

#### 1. The Protagonist (Player Character)

**Core Attributes:**
- **Fatal Flaw** - A weakness that holds the hero back (procrastination, self-doubt, impulsivity, fear of failure)
- **External Goal** - What the hero is trying to achieve (defeat enemy, complete mission, prove themselves)
- **Internal Arc** - Overcoming the hero's weakness to become who the hero needs to be
- **Relatable Struggles** - Real challenges that mirror productivity battles

**Example: The Reluctant Warrior**
```markdown
Marcus was once a decorated soldier, but **self-doubt** paralyzed him after a failed mission. 
Now he must lead a desperate defense, but first he must learn to trust his instincts again.

Fatal Flaw: Second-guesses every decision
External Goal: Protect the kingdom from invasion
Internal Arc: Learning that perfection isn't required, decisive action is
```

#### 2. The Love Interest (Emotional Stakes)

**Purpose:** Provides emotional depth, raises stakes, offers support and conflict

**Character Types:**
- **The Confidant** - Believes in hero when he/she doesn't believe in himself/herself
- **The Challenger** - Pushes hero to be better, doesn't accept excuses
- **The Mirror** - Shares similar struggles, grows alongside hero
- **The Prize** - Someone worth becoming better for (romantic or platonic)

**Integration Guidelines:**
- Introduce in Chapter 2-3 (after hero is established)
- Give the love interest a goal and agency beyond supporting the hero
- Create tension: love interest may doubt hero's ability
- Use clear gender pronouns: "She reached out her hand" / "He turned away"
- Make relationship conditional on growth (if hero doesn't change, relationship fails)

**Example Introduction:**
```markdown
In the training yard, you meet Captain Elena Voss. She's earned every rank through 
relentless discipline—something you've never mastered. 

"Another recruit who thinks talent is enough?" she asks, her sharp eyes measuring you. 
"Talent fails when it matters. Discipline endures."

She doesn't believe you have what it takes. **You'll have to prove her wrong.**
```

#### 3. The Antagonist (The Opposition)

**Requirements:**
- **Strong and Competent** - A genuine threat, not easily defeated
- **Opposite of Hero** - Represents what the hero could become if the hero gives in to weakness
- **Clear Motivation** - Believable goals, even if methods are wrong
- **Personal Connection** - Some link to hero makes conflict meaningful
- **Genre-Appropriate Power** - In grounded stories, rely on real-world advantages (resources, influence, experience). In magical stories, supernatural power is allowed but must have rules, costs, and limits.

**Antagonist Archetypes:**

**Type A: The Dark Mirror**
```markdown
General Kade was once like you—talented but undisciplined. He chose the easy path, 
using his gifts for personal gain. Now he commands the enemy forces, and he sees your 
potential as a threat. "Join me," he offers. "Stop fighting yourself. Stop trying to be 
perfect. Take what you want." He represents the temptation to give up on growth.
```

**Type B: The System**
```markdown
The Scholar's Guild doesn't want you to succeed. You're an outsider, self-taught, and 
your unorthodox methods threaten the guild's established order. Dean Hargrove has spent 30 
years building his reputation—he won't let some upstart with "raw talent" undermine 
everything he's built. He'll use every bureaucratic tool to stop your research.
```

**Type C: The Rival**
```markdown
Sarah Chen has everything you don't: focus, discipline, a spotless record. She's been 
training for this championship since childhood while you're the late bloomer, the 
comeback kid trying to make up for lost time. She doesn't hate you—she just knows 
she's better, and she'll prove it when it counts. The worst part? She's probably right.
```

#### 4. Plot Twists (Every Chapter)

**Guidelines:**
- **Foreshadow subtly** - Hint at twist 1-2 chapters earlier
- **Earn the surprise** - Twist must make sense in retrospect
- **Raise stakes** - Each twist makes situation more complex
- **Challenge assumptions** - Force the hero to reconsider core beliefs

**Twist Categories:**

**Identity Twist:**
```markdown
Chapter 5: The ally who's been helping you is actually working for the antagonist. 
The "traitor" everyone warned you about? Innocent. You've been helping the wrong side.
```

**Stakes Twist:**
```markdown
Chapter 6: Saving the artifact won't stop the invasion—it'll trigger it. The antagonist 
has been counting on you "doing the right thing" to spring his trap.
```

**Personal Twist:**
```markdown
Chapter 7: Your mentor's final lesson wasn't wisdom—it was his confession. The mission 
that haunts you? He gave the order. The failure that defined you? It was his test, and 
you passed. Your weakness was manufactured.
```

**Love Interest Twist:**
```markdown
Chapter 4: Elena isn't your critic—she's your advocate. Every harsh word was designed 
to make you stronger because she knows what's coming. She's been protecting you by 
pushing you away.
```

### Branching Narrative & Multiple Endings

#### Decision Framework

**Key Decision Points (Chapters 2, 4, 6):**

Each decision should be:
- **Morally ambiguous** - No obvious "right" answer
- **Sacrifice required** - Both options have costs
- **Reflects character growth** - Choice reveals who hero has become
- **Affects relationships** - Impacts love interest, allies, antagonist

**Example Difficult Choice (Chapter 6):**

```markdown
The enemy has captured Elena. General Kade offers a trade: the battle plans for her life.

OPTION A: Surrender the Plans
- Save Elena (she lives)
- Lose strategic advantage (kingdom vulnerable)
- Elena's reaction: Angry that you traded thousands of lives for hers
- Antagonist's move: Uses plans to crush resistance
- **Consequence:** Relationship damaged, harder ending required

OPTION B: Refuse the Trade
- Keep the plans (kingdom safer)
- Elena faces torture/possible death
- Ally's reaction: Respect your sacrifice, or condemnation for coldness?
- Antagonist's move: Executes Elena publicly to break morale
- **Consequence:** Possible guilt, but strategic advantage maintained

None of these feel "good." Both require sacrifice. The choice is agonizing.
```

#### Ending Variations (Chapter 7)

In the current implementation, endings are selected by the full 3-decision path (`AAA`…`BBB`).
Write your endings as separate `endings["AAA"|...|"BBB"]["content"]` entries.

**POSITIVE ENDING** - "Victory & Growth"
Requirements: Overcame weakness, maintained relationships, made selfless choices
```markdown
You stand victorious, but changed. The weakness that defined you is gone—not erased, 
but mastered. Elena stands beside you, not as your critic but as your equal. 

"You did it," she says. "Not because you were perfect, but because you kept showing up."

General Kade is defeated, but his final words haunt you: "I was you, once. Remember 
that." The victory is real, but so is the cost. Still, you've proven something to 
yourself—**discipline beats talent when talent doesn't work hard enough.**

[Hero achieves goal, maintains relationship, defeats antagonist, overcomes weakness]
```

**NEUTRAL ENDING** - "Pyrrhic Victory"
Requirements: Mixed choices, partial growth, sacrificed relationships for mission
```markdown
The kingdom is saved, but at what cost? General Kade lies defeated, his ambitions crushed. 
But Elena is gone—not dead, but departed. "You chose the mission over everything else," 
she said before leaving. "Maybe that's what heroes do. But I needed someone, not a hero."

You won the war but lost the person who made you want to win. Your weakness? You never 
fully conquered it. You just learned to power through, consequences be damned.

The medal feels hollow. The accolades ring false. You saved everyone except yourself.

[Hero achieves external goal, loses relationships, weakness remains]
```

**NEGATIVE ENDING** - "Tragic Failure"
Requirements: Failed to overcome weakness, made selfish choices, lost allies
```markdown
You failed. Not because you weren't talented—you were always talented. You failed because 
when it mattered most, **you hesitated.** The weakness you brought to this journey? It's 
still there, stronger than ever.

General Kade wins, not through superior strength, but through your inaction. "I told you," 
he says as the kingdom falls. "Discipline beats talent. I disciplined myself to be ruthless. 
You just... hoped it would work out."

Elena tried to help you. She pushed, she challenged, she believed. And you let her down.

The ending isn't dramatic. It's pathetic. And it's exactly what you deserved.

[Hero fails external goal, loses relationships, remains trapped by weakness]
```

**BITTERSWEET ENDING** - "Growth Through Loss"
Requirements: Overcame weakness, but paid ultimate price
```markdown
You defeated General Kade, but the victory cost everything. The battle plans you refused 
to surrender? They worked. The kingdom stands. But Elena didn't survive her captivity.

At her memorial, you hold the medal she once mocked you for chasing. "She made me better," 
you tell her captain. "Every harsh word, every challenge. She saw who I could be."

"She loved you," the captain says. "Not who you could be. Who you were becoming."

Your weakness is gone. But so is the person who helped you defeat it. The hero's journey 
is complete. The cost was everything.

[Hero overcomes weakness, achieves mission, but loses what mattered most]
```

### Chapter Structure Template (Revised)

```markdown
**Chapter [N]: [Dramatic Title with Promise/Threat]**
*Power Threshold: [X] | Arc: [Setup/Confrontation/Resolution]*

**THE SITUATION**
[1-2 sentences: Where are we now? What's changed since last chapter?]

**THE CHALLENGE**
[2-3 paragraphs: Present the obstacle, introduce/develop characters]
- Reference hero's fatal flaw naturally
- Show antagonist's influence (direct or indirect)
- Develop relationship with love interest/allies
- Build tension through realistic conflict

**THE TWIST**
[Major revelation that changes player's understanding]
- Subvert expectations established earlier
- Raise stakes or complicate situation
- Create new questions while answering old ones

**THE CHOICE** (for decision chapters)
[Present difficult decision with no clear right answer]
Option A: [Consequence of safety/caution]
Option B: [Consequence of risk/action]

**THE CONSEQUENCE** (next chapter callback)
[Show impact of previous decisions]

**CLOSING**
[1-2 sentences: Forward momentum, emotional note, dramatic question]
```

### Writing Best Practices (Expanded)

**DO:**
- ✅ Use consistent pronouns for male/female characters: "Marcus gripped his sword" / "Elena raised her shield"
- ✅ Create realistic conflict (resources, time, trust, skill gaps)
- ✅ Show character growth through actions, not declarations
- ✅ Make every choice painful (lose something valuable either way)
- ✅ Connect narrative to focus sessions: "Each day of training (focus session) brings you closer"
- ✅ Build romantic/platonic tension through competence and respect
- ✅ Give antagonist legitimate grievances or understandable motivations
- ✅ End chapters on dramatic questions or cliffhangers
- ✅ Foreshadow twists through subtle details
- ✅ Show consequences of player choices in subsequent chapters
- ✅ Use second-person consistently: "You see..." "You decide..."

**DON'T:**
- ❌ Use singular "they" for individual male/female characters (use he/she for clarity)
- ❌ In grounded stories, introduce supernatural solutions or unexplained powers
- ❌ In magical stories, use magic as a free pass (it must have rules, tradeoffs, and consequences)
- ❌ Make "right" choice obvious (moral simplicity)
- ❌ Introduce a love interest just for romance (give the love interest agency and a goal)
- ❌ Create cartoonish villains (no monologuing, no stupidity)
- ❌ Resolve internal conflicts too easily
- ❌ Break your story's established rules
- ❌ Inject contemporary political messaging; keep the story character-driven
- ❌ Preach or moralize (show consequences, don't lecture)
- ❌ Give players easy outs (both choices must cost something)
- ❌ Write more than 5 paragraphs per chapter

### Narrative Themes to Consider

**Classic Story Arcs (Enhanced):**
- **Hero's Journey** - Ordinary person becomes extraordinary through overcoming fatal flaw
- **Redemption Arc** - Fallen hero proves the hero can rise again despite past failures
- **Quest for Truth** - Uncovering secrets while confronting personal demons
- **Rise to Power** - Building influence while maintaining integrity
- **Love & Loss** - Achieving goals at the cost of what matters most
- **The Rival's Path** - Two people pushing each other to greatness, with only one crown

**Emotional Hooks (Expanded):**
- **Belonging** - Finding your place while staying true to yourself
- **Achievement** - Proving doubters wrong, especially yourself
- **Love** - Becoming worthy of someone who sees your potential
- **Justice** - Righting wrongs without becoming the villain
- **Legacy** - Building something that outlasts your weaknesses
- **Redemption** - Proving past failures don't define future success

### Example: Complete Story Arc Outline

**Title:** "The Iron Focus" (Warrior Story)

**PROTAGONIST:**
- Name: Marcus Thorne (he/him)
- Fatal Flaw: Crippling self-doubt from past failure
- External Goal: Stop General Kade's invasion
- Internal Arc: Learning to trust his instincts

**LOVE INTEREST:**
- Name: Captain Elena Voss (she/her)
- Role: Mentor who becomes equal partner
- Arc: Starts critical, ends supportive (if Marcus grows)

**ANTAGONIST:**
- Name: General Kade (he/him)
- Motivation: Believes discipline requires ruthlessness
- Connection: Was Marcus's commanding officer during "the failure"
- Strength: Superior resources, tactical genius, no hesitation

**CHAPTER BREAKDOWN:**

**Chapter 1:** "The Haunted Soldier"
- Setup: Marcus can’t lead because he second-guesses every move
- Introduction: Elena challenges him in training
- Twist: The “easy” mission is secretly a test

**Chapter 2 (Decision 1):** "Call to Arms"
- Challenge: The kingdom needs a leader; Marcus is recommended despite failures
- Relationship: Elena opposes the choice publicly
- A/B Decision: take the command immediately / refuse and investigate the truth

**Chapter 3:** "First Blood"
- Consequences: content can vary based on Decision 1 (`content_variations`)
- Twist: Enemy commander is revealed—General Kade, former mentor

**Chapter 4 (Decision 2):** "The Offer"
- Kade offers Marcus a position
- A/B Decision: accept the ruthless path / reject it and protect civilians

**Chapter 5:** "Betrayal"
- Midpoint twist: victory was a setup; the “win” costs something real
- Show visible consequences of Decisions 1–2

**Chapter 6 (Decision 3):** "The Trade"
- Crisis: Kade forces an impossible trade
- A/B Decision: sacrifice strategy to save someone / sacrifice someone to save the mission

**Chapter 7 (Endings):** "The Iron Focus"
- Provide 8 endings keyed by decision path (`AAA`…`BBB`)
- Each ending resolves: (1) Marcus’s internal arc, (2) Elena relationship outcome, (3) Kade outcome

---

---

## Testing Checklist

### Pre-Release Testing

- [ ] **Item Generation Test**
  - [ ] Generate 100+ items - check for naming issues
  - [ ] Test all rarity levels (Common → Legendary)
  - [ ] Verify all 8 slots generate items
  - [ ] Check for typos in prefixes/suffixes

- [ ] **Character Rendering Test**
  - [ ] Character displays correctly at all power tiers
  - [ ] Glow effects work (heroic → godlike)
  - [ ] No visual glitches or overlaps
  - [ ] Power number displays correctly

- [ ] **Story Progression Test**
    - [ ] All chapters unlock at correct power thresholds
  - [ ] Chapter text displays without formatting issues
  - [ ] Story list shows new story correctly
  - [ ] Story switching works (inventory separate)

- [ ] **Integration Test**
  - [ ] Complete focus session → receive themed item
  - [ ] Item appears in inventory (correct story)
  - [ ] Item persists after app restart
  - [ ] Can equip/unequip items
  - [ ] Power calculation includes new items

- [ ] **Edge Cases**
  - [ ] New user starts with new story selected
  - [ ] Existing user sees new story as option
  - [ ] Story mode = "hero_only" (no story) still works
  - [ ] Story mode = "disabled" doesn't break

### User Acceptance Testing

- [ ] **Thematic Consistency** - Does the story *feel* cohesive?
- [ ] **Narrative Quality** - Is the writing engaging?
- [ ] **Item Names** - Do items sound cool/appropriate?
- [ ] **Visual Appeal** - Does the character look good?
- [ ] **Motivation** - Does the story motivate focus sessions?

---

## Best Practices & Considerations

### Code Quality

**Defensive Copying Pattern (CRITICAL):**
```python
# ✅ CORRECT - Use defensive copy
item = generate_item(rarity="Rare", story_id=active_story)
adhd_buster["inventory"].append(item.copy())

# ❌ WRONG - Reference issues
item = generate_item(rarity="Rare", story_id=active_story)
adhd_buster["inventory"].append(item)  # BAD! Same object reference
```

**Save Order Pattern (CRITICAL):**
```python
# ✅ CORRECT
blocker.save_config()           # Save flat data first
sync_hero_data(adhd_buster)     # Sync to hero structure
blocker.save_config()           # Save again after sync

# ❌ WRONG
sync_hero_data(adhd_buster)     # Sync first
blocker.save_config()           # Data loss if sync fails!
```

### Performance Considerations

- **Inventory Size Cap**: 500 items max (line 1259 in focus_blocker_qt.py)
  - Oldest items auto-removed when limit reached
  - Prevents unbounded memory growth
  
- **Item Generation Speed**: Fast (< 1ms per item)
  - No external API calls
  - Simple random selection from predefined pools

- **Character Rendering**: Efficient (< 10ms per frame)
  - Simple Qt drawing primitives
  - Minimal redraws (only on data changes)

### Localization Planning

If planning to support multiple languages:

```python
# Future-proof structure
STORY_GEAR_THEMES = {
    "explorer": {
        "theme_id": "explorer",
        "theme_name": "🗺️ Expedition Gear",  # Translate this (or keep emoji consistent)
        "slot_display": {
            "Helmet": "Hat",  # Translate this
            # ...
        },
        "item_types": {
            "Helmet": [
                "Pith Helmet",  # Could be translated or culturally adapted
                # ...
            ],
        },
    },
}
```

Consider:
- Story titles/descriptions → Translatable strings
- Gear names → May need cultural adaptations
- Narrative chapters → Major translation effort

### Accessibility

- **Colorblind-Friendly**: Use rarity icons + colors
- **Screen Readers**: Ensure text descriptions exist
- **Cognitive Load**: Keep UI simple, one story at a time

---

## Future Expansion Ideas

### Story Categories

**Personal Growth Stories:**
- "The Phoenix Rising" - Recovering from burnout
- "The Mindful Monk" - Meditation and inner peace
- "The Time Architect" - Mastering productivity systems

**Fantasy/Adventure Stories:**
- "The Void Walker" - Exploring dimensions of focus
- "The Dragon Tamer" - Taming the chaos dragon
- "The Star Navigator" - Space exploration through focus

**Professional/Career Stories:**
- "The CEO Chronicles" - Building an empire
- "The Artist's Journey" - Creating masterpieces
- "The Coder's Saga" - Building legendary software

**Historical/Cultural Stories:**
- "The Samurai Path" - Bushido and discipline
- "The Viking Voyage" - Conquest through persistence
- "The Renaissance Master" - Art, science, invention

### Advanced Features (Future)

**Story Crossovers:**
- Unlock special items by completing multiple stories
- "Multiverse Hero" achievement
- Shared legendary items across stories

**Entitidex System** (See `ENTITIDEX_DESIGN.md`)
- Collectible entities themed to each story
- Catch entities after focus sessions (Pokemon Go-style)
- 9 entities per story, scaling from 10 to 2000 power
- Lottery-based catch mechanics
- Story-integrated lore (e.g., Warrior entities are loyal allies and legendary gear)

**Dynamic Narratives:**
- Branching storylines based on player choices
- Multiple endings depending on focus patterns
- Procedurally generated side quests

**Community Content:**
- User-submitted story themes
- Steam Workshop integration
- Story rating/review system

**Seasonal Events:**
- Limited-time story variants
- Holiday-themed gear
- Special challenge stories

---

## Quick Reference: Files to Modify

Adding a new story requires changes to:

| File | Section | Purpose |
|------|---------|---------|
| `gamification.py` | `AVAILABLE_STORIES` | Story metadata |
| `gamification.py` | `STORY_GEAR_THEMES` | Gear theme data |
| `gamification.py` | `<STORY>_DECISIONS`, `<STORY>_CHAPTERS`, `STORY_DATA` | Narrative + branching registration |
| `focus_blocker_qt.py` | `CharacterCanvas.paintEvent()` + `_draw_<story>_character()` | Character rendering (optional but recommended) |
| `test_item_award.py` | Add test function | Integration testing |

**No changes needed in:**
- `core_logic.py` - Story-agnostic
- `config.json` - Auto-initializes new stories
- UI tabs - Use story_id dynamically

---

## Example: Minimal Viable Story

The absolute minimum to add a functional story:

```python
# 1. Story metadata (AVAILABLE_STORIES entry)
"mystory": {
    "id": "mystory",
    "title": "🎯 My Story Title",
    "description": "Brief description of the journey.",
    "theme": "custom",
}

# 2. Gear theme (15 lines minimum - 8 slots × 1 base name each + 2 affixes)
"mystory": {
    "theme_id": "mystory",
    "theme_name": "🎭 My Story Gear",
    "slot_display": {
        "Helmet": "Helmet",
        "Chestplate": "Chest",
        "Gauntlets": "Hands",
        "Boots": "Boots",
        "Shield": "Shield",
        "Weapon": "Weapon",
        "Cloak": "Cloak",
        "Amulet": "Amulet",
    },
    "item_types": {
        "Helmet": ["Basic Helm"],
        "Chestplate": ["Basic Armor"],
        "Gauntlets": ["Basic Gloves"],
        "Boots": ["Basic Boots"],
        "Shield": ["Basic Shield"],
        "Weapon": ["Basic Weapon"],
        "Cloak": ["Basic Cloak"],
        "Amulet": ["Basic Amulet"],
    },
    "adjectives": {
        "Common": ["Old"],
        "Uncommon": ["Sturdy"],
        "Rare": ["Special"],
        "Epic": ["Epic"],
        "Legendary": ["Legendary"],
    },
    "suffixes": {
        "Common": ["Power"],
        "Uncommon": ["Practice"],
        "Rare": ["Focus"],
        "Epic": ["Resolve"],
        "Legendary": ["Destiny"],
    },
}

# 3. Narrative chapters (currently 7 total) + decisions (Ch 2/4/6), registered via STORY_DATA
MYSTORY_DECISIONS = {
    2: {"id": "mystory_d1", "prompt": "...", "choices": {"A": {"label": "...", "short": "...", "description": "..."}, "B": {"label": "...", "short": "...", "description": "..."}}},
    4: {"id": "mystory_d2", "prompt": "...", "choices": {"A": {"label": "...", "short": "...", "description": "..."}, "B": {"label": "...", "short": "...", "description": "..."}}},
    6: {"id": "mystory_d3", "prompt": "...", "choices": {"A": {"label": "...", "short": "...", "description": "..."}, "B": {"label": "...", "short": "...", "description": "..."}}},
}

MYSTORY_CHAPTERS = [
    {"title": "Chapter 1: The Beginning", "threshold": 0, "has_decision": False, "content": "Your journey starts here. Stay focused."},
    # ... chapters 2-6 ...
    {"title": "Chapter 7: The End", "threshold": 1500, "has_decision": False, "content": "...", "endings": {"AAA": {"content": "..."}, "AAB": {"content": "..."}, "ABA": {"content": "..."}, "ABB": {"content": "..."}, "BAA": {"content": "..."}, "BAB": {"content": "..."}, "BBA": {"content": "..."}, "BBB": {"content": "..."}}},
]

STORY_DATA["mystory"] = {"decisions": MYSTORY_DECISIONS, "chapters": MYSTORY_CHAPTERS}

# 4. Character rendering (~20 lines)
elif story_theme == "mystory":
    self._draw_mystory_character(event)

def _draw_mystory_character(self, event):
    painter = QtGui.QPainter(self)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    self._draw_tier_effects(painter)
    # Draw simple stick figure
    painter.setPen(QtGui.QPen(QtGui.QColor("#000000"), 3))
    painter.drawEllipse(65, 20, 50, 50)  # Head
    painter.drawLine(90, 70, 90, 140)    # Body
    painter.drawLine(90, 90, 60, 120)    # Left arm
    painter.drawLine(90, 90, 120, 120)   # Right arm
    painter.drawLine(90, 140, 70, 180)   # Left leg
    painter.drawLine(90, 140, 110, 180)  # Right leg
    painter.end()
```

**Total:** ~50 lines of code for a basic playable story!

---

## Contact & Contributions

**Project Repository:** [PersonalFreedom GitHub](https://github.com/lkacz/PersonalFreedom)

**Contribution Guidelines:**
1. Fork the repository
2. Create a feature branch (`feature/new-story-name`)
3. Implement story following this guide
4. Test thoroughly (checklist above)
5. Submit pull request with:
   - Story description
   - Screenshots of character rendering
   - Sample generated item names
   - Testing results

**Questions or Ideas?**
- Open a GitHub issue with the tag `story-development`
- Include mockups, narrative drafts, or inspiration sources

---

## Appendix: Story ID Naming Conventions

**Best Practices:**
- Lowercase only
- No spaces (use underscores if needed)
- Short and memorable (max 15 chars)
- Avoid special characters
- No numbers (unless thematic, like "blade_runner_2049")

**Good Examples:**
- `warrior`, `scholar`, `wanderer`, `underdog`
- `explorer`, `detective`, `astronaut`, `samurai`
- `phoenix`, `dragon`, `ninja`, `hacker`

**Bad Examples:**
- `MyAwesomeStory` (mixed case)
- `story 1` (spaces, generic)
- `super-cool-story-2024` (too long, special chars)
- `test`, `temp`, `new` (non-descriptive)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2026 | Initial guide created |

---

**Happy Story Development! 🎮📖**

*Remember: Every great story starts with a single focus session.*
