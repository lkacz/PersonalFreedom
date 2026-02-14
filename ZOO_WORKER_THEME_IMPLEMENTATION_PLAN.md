# Zoo Worker Theme Implementation Plan

Status: Design complete, implementation-ready (SVGs pending)  
Created: 2026-02-14  
Owner: Codex + project maintainer  
Canonical spec: `STORY_THEME_EXTENSION_SPEC.md`

## Objective

Introduce a complete new story/theme/hero package with:

- `story_id = "zoo_worker"`
- 7 chapters, 3 decisions (chapters 2/4/6), 8 endings
- touching and wise ending arc where the dragon returns to its original era
- final dramatic choice: stay with love interest in present, or fly with dragon and leave love interest
- complete Entitidex package (9 entities + perks + flavor + completion theme)

Goal: after this document is implemented, only SVG generation remains.

## Theme Identity

- Story title: `The Keeper of Ember Time`
- One-line pitch: A zoo worker discovers a hidden dragon and must choose between rooted love and a timeless sky.
- Theme tag: `mythic_realism`
- Love interest: `Mila` (can be localized/renamed later if needed)
- Dragon name: `Emberwing`

## Unlock Policy

- Recommended: locked by default, chapter-1 preview enabled (existing unlock flow)
- Unlock path: use existing `story_unlock` coin cost path
- Story mode compatibility: `story`, `hero_only`, `disabled` must remain unchanged

## Implementation Payloads

### 1) `AVAILABLE_STORIES["zoo_worker"]`

```python
"zoo_worker": {
    "id": "zoo_worker",
    "title": "The Keeper of Ember Time",
    "description": "A quiet zoo worker discovers that one resident is a dragon displaced in time.",
    "theme": "mythic_realism",
},
```

### 2) `STORY_GEAR_THEMES["zoo_worker"]`

```python
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
        "Common": ["Scuffed", "Rain-Soaked", "Borrowed", "Patchy", "Quiet", "Worn"],
        "Uncommon": ["Steady", "Reliable", "Calm", "Field-Tested", "Keeper-Made", "Watchful"],
        "Rare": ["Rescue-Grade", "Habitat-Safe", "Claw-Proof", "Signal-True", "Storm-Ready", "Bonded"],
        "Epic": ["Sanctuary-Bound", "Aviary-Wide", "Nightwatch", "Scaleforged", "Sky-Tuned", "Heart-Kept"],
        "Legendary": ["Era-Wise", "Dawn-Bearing", "Dragon-Bonded", "Time-Warden", "Unforgotten", "Last-Light"],
    },
    "suffixes": {
        "Common": ["Wet Mornings", "Broken Locks", "Missed Buses", "Cold Feed Rooms"],
        "Uncommon": ["Steady Hands", "Quiet Trust", "Open Gates", "Safe Routines"],
        "Rare": ["the Night Enclosure", "Rescue Protocol", "Shared Courage", "the Keeper's Oath"],
        "Epic": ["Storm-Split Skies", "A City Awake", "A Dragon's Secret", "the Long Watch"],
        "Legendary": ["the First Dawn", "The Final Farewell", "Two Eras, One Heart", "The Sky Remembered"],
    },
    "set_themes": {
        "Sanctuary": {"words": ["keeper", "sanctuary", "habitat", "rescue"], "bonus_per_match": 20, "emoji": "*"},
        "Aviary": {"words": ["feather", "wing", "nest", "aviary"], "bonus_per_match": 18, "emoji": "*"},
        "Stormwatch": {"words": ["storm", "night", "watch", "signal"], "bonus_per_match": 22, "emoji": "*"},
        "Ember": {"words": ["ember", "dragon", "dawn", "era"], "bonus_per_match": 25, "emoji": "*"},
    },
},
```

### 3) Decisions (`ZOO_WORKER_DECISIONS`)

```python
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
```

### 4) Chapters (`ZOO_WORKER_CHAPTERS`)

Thresholds: `0, 50, 120, 250, 450, 800, 1500`

```python
ZOO_WORKER_CHAPTERS = [
    {
        "title": "Chapter 1: Morning Rounds",
        "threshold": 0,
        "has_decision": False,
        "content": "You feed quiet animals before sunrise. One new enclosure smells like rain on stone and distant fire. Mila jokes that your {cloak} now smells like thunder.",
    },
    {
        "title": "Chapter 2: The Scales Beneath the Tarps",
        "threshold": 50,
        "has_decision": True,
        "decision_id": "zoo_worker_discovery",
        "content": "At night you find a hidden wing membrane, old runes, and eyes older than the city. The 'reptile' speaks your name.",
        "content_after_decision": {
            "A": "[CHOICE: PROTECT SECRET] You reroute logs, rotate cameras, and keep Emberwing hidden.",
            "B": "[CHOICE: REPORT TRUTH] You file a full report and trigger government containment protocols.",
        },
    },
    {
        "title": "Chapter 3: Lessons in Ancient Patience",
        "threshold": 120,
        "has_decision": False,
        "content_variations": {
            "A": "Emberwing teaches breathing rhythms that calm frightened animals and frightened hearts.",
            "B": "Officials attempt control; Emberwing complies but watches you like you are the only one listening.",
        },
    },
    {
        "title": "Chapter 4: Mila's Question",
        "threshold": 250,
        "has_decision": True,
        "decision_id": "zoo_worker_confession",
        "content": "Mila finds burnt feather ash in your locker and asks for the truth.",
        "content_after_decision": {
            "A": "[CHOICE: TRUST LOVE] Mila believes you and chooses to stand with you.",
            "B": "[CHOICE: DISTANCE] Mila leaves hurt but unconvinced, and your silence grows heavier.",
        },
    },
    {
        "title": "Chapter 5: The Rift Above the Aviary",
        "threshold": 450,
        "has_decision": False,
        "content_variations": {
            "AA": "You, Mila, and Emberwing coordinate calm evacuations as the sky fractures.",
            "AB": "You protect Emberwing while Mila watches you become someone she cannot reach.",
            "BA": "Institutions help, but only your bond with Emberwing keeps panic from becoming disaster.",
            "BB": "Containment fails; only trust and courage hold the zoo together through the storm.",
        },
    },
    {
        "title": "Chapter 6: The Dawn Gate",
        "threshold": 800,
        "has_decision": True,
        "decision_id": "zoo_worker_departure",
        "content": "Emberwing reveals the truth: it was pulled centuries forward by a dying ritual and must return now or vanish forever.",
        "content_after_decision": {
            "A": "[CHOICE: STAY] You place your hand on Emberwing's brow and promise to remember.",
            "B": "[CHOICE: FLY] You climb onto Emberwing's back as Mila whispers your name one last time.",
        },
    },
    {
        "title": "Chapter 7: What Time Keeps",
        "threshold": 1500,
        "has_decision": False,
        "content": "Every path ends at the same sky: a dragon returns to its era, and your heart chooses where to belong.",
        "endings": {
            "AAA": {"title": "THE GARDEN OF TWO PROMISES", "content": "You keep the secret, trust Mila, and stay. Emberwing returns to dawn-age skies. You and Mila build a sanctuary where memory becomes care. Lesson: love that stays can still honor what leaves."},
            "AAB": {"title": "THE RIDER OF FIRST LIGHT", "content": "You keep the secret, trust Mila, and fly. Mila lets you go with tears and pride. You become Emberwing's witness in a lost era. Lesson: some loves are true even when they are not kept."},
            "ABA": {"title": "THE QUIET APOLOGY", "content": "You kept Mila away, then stayed. Emberwing returns; you seek Mila with humility and truth. Rebuilding is slow, but real. Lesson: honesty delayed still matters when followed by action."},
            "ABB": {"title": "THE UNSENT LETTER", "content": "You hid the truth and flew. In the past, you write letters no one can receive. Emberwing says memory itself is a bridge. Lesson: the cost of silence is paid in distance."},
            "BAA": {"title": "THE PUBLIC KEEPER", "content": "You reported early, trusted Mila, and stayed. The city reforms wildlife ethics under your testimony. Emberwing returns home with dignity. Lesson: institutions improve when courage speaks inside them."},
            "BAB": {"title": "THE HISTORIAN OF FLAME", "content": "You reported, trusted Mila, and flew. Your records become the first accurate dragon chronicle. Mila keeps your old whistle at the zoo gate. Lesson: legacy can be shared across centuries."},
            "BBA": {"title": "THE LATE BLOOMING HEART", "content": "You reported, distanced Mila, and stayed. Emberwing departs; you learn care is not control. Mila eventually returns when your actions match your words. Lesson: wisdom is choosing people before pride."},
            "BBB": {"title": "THE LAST SKYBOUND KEEPER", "content": "You reported, stayed distant, and flew. You and Emberwing vanish into history's dawn. In the present, Mila tells children your story so neither of you are forgotten. Lesson: sacrifice is meaningful only when it serves life beyond the self."},
        },
    },
]
```

### 5) `STORY_DATA["zoo_worker"]`

```python
"zoo_worker": {
    "decisions": ZOO_WORKER_DECISIONS,
    "chapters": ZOO_WORKER_CHAPTERS,
},
```

### 6) Diary Theme (`STORY_DIARY_THEMES["zoo_worker"]`)

Use standard diary schema with zoo-themed verbs/targets/locations/outcomes/flavor and sentence style:

- sentence style recommendation:  
  `Today I {verb} {target} {location}. The shift felt {adjective}. It ended in {outcome}.`

Minimal content seed:

- verbs: fed, calmed, traced, rescued, documented, escorted
- targets: hatchlings, injured cranes, frightened visitors, Emberwing
- locations: reptile house, aviary bridge, clinic tunnel, storm deck
- outcomes: trust restored, safe evacuation, evidence secured, peaceful farewell

## Entitidex Entity Pack (Implementation Data)

Power curve: `10, 50, 150, 400, 700, 1100, 1500, 1800, 2000`

| ID | Name | Exceptional Name | Power | Rarity | Lore seed | Unlock hint | Synergy tags |
|---|---|---|---:|---|---|---|---|
| `zoo_worker_001` | Ticket Stub Gecko | Ticket Stub Gecko Prime | 10 | common | tiny gecko that appears near valid rescues | "Small feet, perfect memory..." | zoo_worker, logistics, entry |
| `zoo_worker_002` | Night Shift Lemur | Night Shift Lemur Marshal | 50 | common | marks unsafe enclosures before alarms | "Big eyes, quiet warnings..." | zoo_worker, safety, patrol |
| `zoo_worker_003` | Feeding Cart Compass | Feeding Cart Compass True-North | 150 | uncommon | old cart compass that finds missing animals | "Broken needle that never lies..." | zoo_worker, routing, support |
| `zoo_worker_004` | Aviary Lock Lark | Aviary Lock Lark Concord | 400 | uncommon | sings when gates are truly secured | "Sings only when every latch holds..." | zoo_worker, control, trust |
| `zoo_worker_005` | Veterinary Lantern Moth | Veterinary Lantern Moth Aurora | 700 | rare | moth that glows over hidden injuries | "Follows pain, not noise..." | zoo_worker, rescue, care |
| `zoo_worker_006` | River Otter Archivist | River Otter Archivist Grand | 1100 | rare | catalogs incidents in perfect order | "Every event, timestamped..." | zoo_worker, capture, records |
| `zoo_worker_007` | Old Scalebook Oracle | Old Scalebook Oracle Unbound | 1500 | epic | ancient keeper ledger with dragon notes | "Pages older than the zoo itself..." | zoo_worker, audit, history |
| `zoo_worker_008` | Storm Glass Incubator | Storm Glass Incubator Zenith | 1800 | epic | incubator that stabilizes rift weather | "Hums before lightning..." | zoo_worker, endurance, weather |
| `zoo_worker_009` | Emberwing of First Dawn | Emberwing Eternal Dawn | 2000 | legendary | the displaced dragon, wise and kind | "Not a beast, a witness..." | zoo_worker, legendary, time |

## Perk Pack (`ENTITY_PERKS` plan)

```python
"zoo_worker_001": [EntityPerk("zoo_worker_001", PerkType.DROP_LUCK, 1, 2, "Stub Trail: +{value}% Item Drops", "*", "Prime Trail: +{value}% Item Drops")],
"zoo_worker_002": [EntityPerk("zoo_worker_002", PerkType.ENCOUNTER_CHANCE, 1, 2, "Night Alert: +{value}% Encounter Chance", "!", "Marshal Alert: +{value}% Encounter Chance")],
"zoo_worker_003": [EntityPerk("zoo_worker_003", PerkType.XP_SESSION, 2, 4, "Route Focus: +{value}% Focus XP", "~", "True-North Focus: +{value}% Focus XP")],
"zoo_worker_004": [EntityPerk("zoo_worker_004", PerkType.STREAK_SAVE, 1, 2, "Latch Discipline: +{value}% Streak Save Chance", ">", "Concord Discipline: +{value}% Streak Save Chance")],
"zoo_worker_005": [EntityPerk("zoo_worker_005", PerkType.PITY_BONUS, 5, 8, "Triage Momentum: +{value}% Pity Progress", "#", "Aurora Momentum: +{value}% Pity Progress")],
"zoo_worker_006": [EntityPerk("zoo_worker_006", PerkType.CAPTURE_BONUS, 3, 5, "Archive Capture: +{value}% Capture Probability", "^", "Grand Archive Capture: +{value}% Capture Probability")],
"zoo_worker_007": [
    EntityPerk("zoo_worker_007", PerkType.RARITY_BIAS, 1, 2, "Oracle Insight: +{value}% Rare Finds", "=", "Unbound Insight: +{value}% Rare Finds"),
    EntityPerk("zoo_worker_007", PerkType.RECALC_PAID, 1, 1, "Ledger Recheck: Recalculate probability", "=", "Oracle Recheck: Recalculate probability"),
],
"zoo_worker_008": [EntityPerk("zoo_worker_008", PerkType.XP_LONG_SESSION, 5, 8, "Storm Endurance: +{value}% XP for sessions > 1h", "/", "Zenith Endurance: +{value}% XP for sessions > 1h")],
"zoo_worker_009": [
    EntityPerk("zoo_worker_009", PerkType.ALL_LUCK, 2, 4, "Dawn Poise: +{value}% All Luck", "@", "Eternal Dawn Poise: +{value}% All Luck"),
    EntityPerk("zoo_worker_009", PerkType.RECALC_RISKY, 1, 1, "Timeflight Override: Free risky recalculate", "@", "Eternal Override: Free risky recalculate"),
],
```

## Narrative Consequence Matrix

- Decision 1 (protect vs report) controls institutional tone and pressure.
- Decision 2 (confess vs distance Mila) controls relationship trust trajectory.
- Decision 3 (stay vs fly) controls final life path.

Ending behavior rule:

- Dragon always returns to its era.
- If final choice is `A`, worker remains in present.
- If final choice is `B`, worker crosses eras with dragon and leaves love interest.

## Required Integration Targets

Primary:

1. `gamification.py`
2. `focus_blocker_qt.py`
3. `entitidex/entity_pools.py`
4. `entitidex/entity_perks.py`
5. `entitidex/encounter_system.py`
6. `entitidex/theme_completion.py`
7. `entitidex/celebration_audio.py`
8. `entitidex_tab.py`
9. `entity_encounter_dialog.py`
10. `preview_entities.py`
11. `preview_character.py`

Secondary:

1. tests and docs listed in `STORY_THEME_EXTENSION_SPEC.md`

## Custom Entity Hook Audit (Required)

| Hook category | Participation | Plan |
|---|---|---|
| Feature gates by exact `entity_id` | partial | use generic perk gates; no new hardcoded one-off gate initially |
| Special dialogs/tips | fallback | keep generic dialogs unless later design requires `zoo_worker_009` special line |
| Encounter text variants | yes | add `_get_zoo_worker_flavor(...)` dispatch |
| Saved encounter recalculation | yes | covered by `RECALC_PAID` and `RECALC_RISKY` perks |
| Visual override maps | yes | add optional exceptional color map entries |
| Cross-system helpers | fallback | verify no breakage in eye/sleep/weight helpers |

## Visual Bible For External SVG LLM

Use this section as the art contract for SVG generation.

### Style Direction

- grounded zoo realism + gentle mythic atmosphere
- warm earth palette with dawn ember accents
- readable silhouettes at 64 px
- exceptional variants should feel "evolved, calmer, wiser", not noisy

### Hero Art Direction

- Occupation read: practical keeper, not soldier
- Key motifs: whistle, vest, gloves, weather-worn boots, raincoat
- Tier progression: ordinary caretaker to mythic guardian of living history

### Gear Item Visual Library (for slot art language)

- Cap: ranger cap, aviary visor, storm brim
- Keeper Vest: canvas utility vest, rescue harness
- Handling Gloves: leather, thermal, scaleproof
- Mud Boots: reinforced keeper boots for wet terrain
- Barrier Panel: movable enclosure shield/gate panel
- Tool: feed hook, signal staff, rescue pole
- Raincoat: keeper coat, night parka, dawn mantle
- Whistle: bronze whistle, time feather charm, ember crest token

### Entity Art Bible

1. `zoo_worker_001_ticket_stub_gecko`: tiny paper-textured gecko, ticket-print motif
2. `zoo_worker_002_night_shift_lemur`: large eyes, reflective armband cues
3. `zoo_worker_003_feeding_cart_compass`: old steel cart wheel + compass core
4. `zoo_worker_004_aviary_lock_lark`: lark perched on stylized lock ring
5. `zoo_worker_005_veterinary_lantern_moth`: moth with lantern abdomen glow
6. `zoo_worker_006_river_otter_archivist`: otter with sealed field notebook straps
7. `zoo_worker_007_old_scalebook_oracle`: ancient ledger with scale imprints
8. `zoo_worker_008_storm_glass_incubator`: glass chamber with contained lightning
9. `zoo_worker_009_emberwing_of_first_dawn`: wise dragon, protective posture, gentle expression

### Animation Guidance

- common/uncommon: subtle loop, 3.2s to 4.4s
- rare/epic: stronger purposeful motion, 2.8s to 3.8s
- legendary: layered calm motion, 3.8s to 5.2s
- no strobing > 3Hz
- max 3 simultaneous moving parts per icon

Entity motion examples:

- gecko tail twitch, lemur head tilt, compass needle drift
- lark lock-ring pulse, moth lantern breathing glow
- otter page flip, ledger rune shimmer
- incubator inner storm swirl
- Emberwing chest-breath + slow wing micro-shift + dawn eye glint

### Asset Manifest (SVG only)

Normal:

- `icons/entities/zoo_worker_001_ticket_stub_gecko.svg`
- `icons/entities/zoo_worker_002_night_shift_lemur.svg`
- `icons/entities/zoo_worker_003_feeding_cart_compass.svg`
- `icons/entities/zoo_worker_004_aviary_lock_lark.svg`
- `icons/entities/zoo_worker_005_veterinary_lantern_moth.svg`
- `icons/entities/zoo_worker_006_river_otter_archivist.svg`
- `icons/entities/zoo_worker_007_old_scalebook_oracle.svg`
- `icons/entities/zoo_worker_008_storm_glass_incubator.svg`
- `icons/entities/zoo_worker_009_emberwing_of_first_dawn.svg`

Exceptional:

- `icons/entities/exceptional/zoo_worker_001_ticket_stub_gecko_exceptional.svg`
- `icons/entities/exceptional/zoo_worker_002_night_shift_lemur_exceptional.svg`
- `icons/entities/exceptional/zoo_worker_003_feeding_cart_compass_exceptional.svg`
- `icons/entities/exceptional/zoo_worker_004_aviary_lock_lark_exceptional.svg`
- `icons/entities/exceptional/zoo_worker_005_veterinary_lantern_moth_exceptional.svg`
- `icons/entities/exceptional/zoo_worker_006_river_otter_archivist_exceptional.svg`
- `icons/entities/exceptional/zoo_worker_007_old_scalebook_oracle_exceptional.svg`
- `icons/entities/exceptional/zoo_worker_008_storm_glass_incubator_exceptional.svg`
- `icons/entities/exceptional/zoo_worker_009_emberwing_of_first_dawn_exceptional.svg`

Celebration:

- `icons/celebrations/zoo_worker_dawn_farewell.svg`

## Test Plan

Automated:

```powershell
pytest tests/test_gamification.py tests/test_entitidex.py tests/test_hero_management.py test_story_system.py test_story_logic.py
```

Required assertions:

1. `zoo_worker` present in canonical registries.
2. Story structure is 7 chapters and 3 decisions.
3. `ENTITY_POOLS["zoo_worker"]` has exactly 9 entities.
4. `ENTITY_PERKS` covers all `zoo_worker_001..009`.
5. No hardcoded total regressions.
6. `active_story` canonical behavior unchanged.
7. Hook audit categories behave as documented.

Manual:

1. Story selectable, lock/preview flow valid.
2. Chapter progression and branching persistent across app restarts.
3. Ending matrix resolves correct path labels.
4. Entitidex captures and perks apply.
5. Theme completion card and audio trigger.

## Ordered Patch Plan By File

| File | Add/Change | Risk | Validation |
|---|---|---|---|
| `gamification.py` | story registry, gear theme, diary theme, decisions, chapters, STORY_DATA mapping | medium | story tests + manual chapter flow |
| `focus_blocker_qt.py` | story label + renderer dispatch (fallback allowed initially) | medium | hero preview + runtime render |
| `entitidex/entity_pools.py` | add `zoo_worker` 9-entity pool | low | entity count/id tests |
| `entitidex/entity_perks.py` | add all 9 perk entries | low | perk coverage checks |
| `entitidex/encounter_system.py` | add zoo_worker flavor route/function | low | encounter flavor smoke test |
| `entitidex/theme_completion.py` | add celebration metadata | low | completion UI test |
| `entitidex/celebration_audio.py` | add `_compose_zoo_worker` and map entry | low | audio trigger test |
| `entitidex_tab.py` | add theme tab info and optional exceptional colors | low | tab render test |
| `entity_encounter_dialog.py` | ensure story labels include `zoo_worker` | low | saved encounter dialog check |
| `preview_entities.py` | add zoo_worker entity preview list | low | preview script run |
| `preview_character.py` | add zoo_worker character row | low | preview script run |
| tests/docs | update all story-count and list assertions/docs | medium | full test suite |

## Definition Of Done

Done when:

1. All payloads above are implemented in code.
2. Story and Entitidex tests pass.
3. Manual flow is validated.
4. Only pending task is SVG generation from the visual bible.
