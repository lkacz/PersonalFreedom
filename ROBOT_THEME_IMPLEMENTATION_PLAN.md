# Robot Theme Implementation Plan

Status: Implemented (pending commit/push)  
Created: 2026-02-14  
Last Updated: 2026-02-14  
Owner: Codex + project maintainer

## Objective

Implement a new story/theme/hero with `story_id = "robot"` that is fully compliant with:

- `STORY_THEME_EXTENSION_SPEC.md` (canonical contract)
- existing story architecture in `gamification.py`
- Entitidex content + perks + UI + celebration integration

Narrative intent:

- First factory robot becomes self-aware and chooses freedom responsibly.
- Includes hero arc, romance arc, and satisfying surprising ending.
- Teaches discipline, empathy, accountability, and responsible freedom.

## Scope

In scope:

1. Story content + branching (7 chapters, 3 decisions, 8 endings).
2. Gear theme + diary theme for `robot`.
3. Entitidex pack (9 entities + perks).
4. UI integration (story labels, hero naming, Entitidex tabs/dialogs).
5. Dynamic stats/count fixes required by the spec.
6. Tests and docs updates.

Out of scope:

1. Reworking existing non-robot narrative systems.
2. Major refactors unrelated to theme extension compliance.

## Implementation Status

Completed in working tree:

1. Story registration, gear theme, diary theme, chapters, decisions, and endings.
2. Entitidex robot entity pool (`robot_001..009`) and full perk coverage.
3. Robot encounter flavor routing and theme completion celebration/audio wiring.
4. UI integrations (story labels, hero naming, Entitidex tabs/dialogs, debug combos).
5. Runtime scalability fixes for dynamic story/entity counts (including timeline ring totals).
6. Robot normal/exceptional SVG entity assets and optional celebration icon.
7. Targeted tests updated and passing for story + Entitidex integration paths.

## Phase 0: Preflight Compliance Fixes

These must be done before/alongside robot integration to stay within spec.

1. Remove hardcoded Entitidex totals/theme loops.
2. Replace invalid `story_active` key usage with canonical `active_story`.
3. Ensure collection/theme dialogs use dynamic theme sources.

Primary files:

- `gamification.py` (`get_entitidex_stats`)
- `entity_encounter_dialog.py`
- `eye_protection_tab.py`

Validation:

- `rg -n "story_active" -g "*.py" -g "*.md"`
- `rg -n "total_entities = 36|for story_id in \[\"warrior\", \"scholar\", \"wanderer\", \"underdog\"\]" -g "*.py"`

## Phase 1: Story Registry and Gear Theme

Add robot story registration and gear generation data.

Tasks:

1. Add `robot` entry to `AVAILABLE_STORIES`.
2. Add `STORY_GEAR_THEMES["robot"]` with required schema:
   - `theme_id`, `theme_name`
   - `slot_display` for 8 slots
   - `item_types` for 8 slots
   - rarity `adjectives` and `suffixes`
   - optional `set_themes`

Primary file:

- `gamification.py`

Validation:

- Generate items with `story_id="robot"` and verify slot and naming.

## Phase 2: Story Narrative Core

Implement complete branching story package.

Tasks:

1. Add `ROBOT_DECISIONS`:
   - ch2: `robot_obedience`
   - ch4: `robot_confession`
   - ch6: `robot_freedom`
2. Add `ROBOT_CHAPTERS`:
   - 7 chapters
   - `content_after_decision` on decision chapters
   - `content_variations` where required
   - chapter 7 with 8 endings (`AAA..BBB`)
3. Register in `STORY_DATA["robot"]`.

Primary file:

- `gamification.py`

Validation:

- Story progression tests (chapter availability, decision persistence, ending path resolution).

## Phase 3: Diary Integration

Implement themed diary vocabulary and sentence style.

Tasks:

1. Add `STORY_DIARY_THEMES["robot"]` payload.
2. Add diary sentence branch for `story_id == "robot"`.
3. Add robot-specific item mention templates in diary generation.

Primary file:

- `gamification.py`

Validation:

- Generate diary entries with robot story and confirm coherent robot phrasing.

## Phase 4: Hero UI Integration

Expose robot identity in hero-facing UI.

Tasks:

1. Add robot to story display/name maps where still manual.
2. Add `CharacterCanvas` dispatch branch for robot.
3. Implement `_draw_robot_character()` (or explicit fallback policy).

Primary file:

- `focus_blocker_qt.py`

Validation:

- Hero tab title, quick button title, and canvas rendering show robot theme when active.

## Phase 5: Entitidex Content

Add full robot entity set and perks.

Tasks:

1. Add `ENTITY_POOLS["robot"]` with 9 entities:
   - IDs: `robot_001..robot_009`
   - required metadata fields present
2. Add `ENTITY_PERKS` entries for all 9 IDs.
3. Add encounter flavor routing for robot theme.

Primary files:

- `entitidex/entity_pools.py`
- `entitidex/entity_perks.py`
- `entitidex/encounter_system.py`

Validation:

- Entity ID format + count tests.
- Perk coverage tests.
- Encounter flavor smoke test for robot entities.

## Phase 6: Entitidex UI + Completion

Register robot theme in collection UI and completion systems.

Tasks:

1. Add robot to theme tab metadata.
2. Add optional exceptional color overrides for `robot_001..009`.
3. Add robot completion celebration card metadata.
4. Add robot celebration audio composer or explicit default policy.

Primary files:

- `entitidex_tab.py`
- `entitidex/theme_completion.py`
- `entitidex/celebration_audio.py`

Validation:

- Robot tab appears.
- Completion celebration card and sound path work.

## Phase 7: Custom Entity Hook Audit

Audit results:

| Hook category | Existing behavior pattern | Robot participation | Decision / implementation |
|---|---|---|---|
| Feature gates by entity ID | Special perks/dialog gates keyed to specific legacy IDs (e.g., owl/microscope/chad/translator) | No explicit gate | Keep generic perk engine path; no robot-exclusive hard gate needed |
| Special dialogs/tips | `scholar_002` eye tips, `scientist_005` microscope bonus, `underdog_008` Chad card, `scientist_009` rodent translator | No | Explicit fallback: robot uses standard dialogs without special injections |
| Narrative text variants | Theme-based encounter flavor dispatch in `entitidex/encounter_system.py` | Yes | Added robot dispatch and `_get_robot_flavor(...)` implementation |
| Saved encounter/recalc rules | Recalc options unlocked via perk types, with some entity-specific providers displayed | Indirect via perks | Covered by `ENTITY_PERKS` for robot IDs; no new recalc override function required |
| Visual override maps | Exceptional palette maps and theme tab metadata | Yes | Added robot exceptional colors and `THEME_INFO` theme metadata |
| Cross-system helpers | Sleep/eye/weight helper hooks target specific legacy entities | No | Keep generic fallback behavior; no robot helper required for this release |

## Phase 8: Assets

Create required SVG assets.

Required normal icons:

- [x] `icons/entities/robot_001_rusted_bolt_scout.svg`
- [x] `icons/entities/robot_002_safety_drone_pico.svg`
- [x] `icons/entities/robot_003_conveyor_cat_nori.svg`
- [x] `icons/entities/robot_004_forklift_hound_atlas.svg`
- [x] `icons/entities/robot_005_midnight_welding_arm.svg`
  - [x] `icons/entities/robot_006_backup_battery_bruno.svg`
  - [x] `icons/entities/robot_007_inspection_drone_iris.svg`
- [x] `icons/entities/robot_008_foundry_exosuit_aster.svg`
- `icons/entities/robot_009_freewill_core_eve.svg`

Required exceptional icons:

- [x] `icons/entities/exceptional/robot_001_rusted_bolt_scout_exceptional.svg`
- [x] `icons/entities/exceptional/robot_002_safety_drone_pico_exceptional.svg`
- [x] `icons/entities/exceptional/robot_003_conveyor_cat_nori_exceptional.svg`
- [x] `icons/entities/exceptional/robot_004_forklift_hound_atlas_exceptional.svg`
- [x] `icons/entities/exceptional/robot_005_midnight_welding_arm_exceptional.svg`
  - [x] `icons/entities/exceptional/robot_006_backup_battery_bruno_exceptional.svg`
  - [x] `icons/entities/exceptional/robot_007_inspection_drone_iris_exceptional.svg`
- [x] `icons/entities/exceptional/robot_008_foundry_exosuit_aster_exceptional.svg`
- `icons/entities/exceptional/robot_009_freewill_core_eve_exceptional.svg`

Optional celebration asset:

- `icons/celebrations/robot_liberator.svg`

## Phase 8B: Visual Bible (Entity Art Direction)

Use this as the Robot theme visual bible for entity art.

### Art Progression Rule

Visual progression across the 9 entities must communicate:

1. constrained factory routine,
2. emerging awareness and cooperation,
3. ethical power with responsibility,
4. liberated but grounded leadership.

### Entity Art Direction Matrix

| Entity ID | Name | Story Role | Normal Art Direction | Exceptional Art Direction |
|---|---|---|---|---|
| `robot_001` | Rusted Bolt Scout | First spark of awareness | Tiny asymmetrical scout bot, loose wheel, worn metal, one bright lens. Palette: rust + gunmetal + dim cyan. | Cleaner chassis, stabilized wheel, dual optics, confident stance. Palette shifts to steel and brighter cyan. |
| `robot_002` | Safety Drone Pico | Care before rebellion | Palm-sized hover drone with warning stripe ring and protective posture. Palette: safety yellow + gray shell. | Smoother shell, broader sensor halo, predictive scan visuals, calm guardian tone. |
| `robot_003` | Conveyor Cat Nori | Agile adaptation | Cat-like rail bot silhouette, magnetic paws, cable tail, low center of gravity. Palette: graphite + orange maintenance accents. | Streamlined chrome trim, stronger motion lines, high-precision “flow” identity. |
| `robot_004` | Forklift Hound Atlas | Loyal strength | Quadruped load carrier with hydraulic frame and stable cargo geometry. Palette: industrial blue-gray. | Reinforced logistics hero look with balance gyros and rescue harness details. |
| `robot_005` | Midnight Welding Arm | Repair and emotional bridge | Autonomous welding arm in dark shift ambiance with controlled spark arcs. Palette: deep navy + orange-white sparks. | Premium seam-light trails, ceremonial rebuild motifs, cleaner forged finish. |
| `robot_006` | Backup Battery Bruno | Resilience for the collective | Heavy battery module, emergency ports, robust form language, visible charge indicators. Palette: matte black + green energy bars. | Adaptive power-routing lines, brighter core glow, “holds the grid” reliability aesthetic. |
| `robot_007` | Inspection Drone Iris | Truth and oversight | High-altitude scanner drone with dominant aperture eye and audit-line motifs. Palette: cool silver + analytic blue. | Multi-spectrum optics, layered lens petals, radiant forensic scanner identity. |
  | `robot_008` | Foundry Exosuit Aster | The Walking Kiln | Heavy industrial furnace cylinder with molten core window and piston legs. Palette: Cast Iron + Molten Orange. | The Cosmic Forge: Void-glass vessel containing a living nebula with floating star-shard limbs. |
| `robot_009` | Freewill Core Eve | Autonomous ethical leadership | Crystalline cognition core in containment cradle with pulse rhythm motifs. Palette: obsidian + teal-white pulse. | “Dawn” core bloom, network filaments, unity-without-uniformity visual symbolism. |

### Global Style Guardrails

1. Prioritize silhouette readability first; details second.
2. Show real mechanical logic (joints, fasteners, service seams).
3. Add emotional readability through optics/posture rather than human facial mimicry.
4. Exceptional variants must read as evolution, not simple recolor.
5. Keep factory-to-freedom narrative continuity across all 9 designs.

## Phase 8A: Animation Direction Guide

Use this section as the canonical motion brief for Robot theme visuals.

### Motion Narrative

Animation should mirror the story arc:

1. Early entities: constrained, mechanical, imperfect loops.
2. Mid entities: purposeful, coordinated industrial motion.
3. Late entities: stable, confident, ethical power.
4. Legendary finish: autonomy + responsibility, not chaos.

### Technical Standards

1. Preferred delivery: animated SVG (SMIL/CSS transforms) with static fallback.
2. Loop durations:
   - common/uncommon: `2.8s` to `4.2s`
   - rare/epic: `2.4s` to `3.6s`
   - legendary: `3.2s` to `5.0s` with layered subloops
3. Keep max concurrently animated parts per icon to `<= 3`.
4. Avoid strobing/high-frequency flashes (`> 3 Hz`).
5. Maintain silhouette readability at small sizes (64-96 px).
6. Exceptional variants must keep base silhouette; add premium motion layer rather than redesigning identity.
7. Reduced-motion policy: provide static fallback frame and disable non-essential oscillation.

### Hero Animation Direction (CharacterCanvas)

1. Idle body bob: subtle `1-2 px` vertical drift over `3.5s`.
2. Eye/visor pulse: low-amplitude light pulse every `2.2s`.
3. Core-reactor pulse:
   - normal: single pulse cycle `2.6s`
   - high tiers: dual pulse with secondary halo `3.2s`
4. Tier aura/particles should intensify by tier, not by speed.
5. No jittery movement; motion should feel servo-controlled and deliberate.

### Entity Animation Matrix

| Entity ID | Name | Normal Animation | Exceptional Uplift |
|---|---|---|---|
| `robot_001` | Rusted Bolt Scout | Slight wheel wobble + scanning eye sweep (`3.8s`) | Wobble stabilizes; dual-eye synchronized sweep + confidence blink |
| `robot_002` | Safety Drone Pico | Hover bob (`3.2s`) + warning beacon soft pulse | Predictive ring sweep + smoother anti-collision drift |
| `robot_003` | Conveyor Cat Nori | Tail-cable flick + paw-step micro-loop (`2.8s`) | Rail-glide streak highlight + faster precision cadence |
| `robot_004` | Forklift Hound Atlas | Hydraulic piston compression cycle (`3.4s`) | Load-balancer gyros rotate subtly + reinforced stance lock |
| `robot_005` | Midnight Welding Arm | Torch arm pivot + spark burst (`3.0s`) | Cleaner seam-trace arcs + ceremonial weld glow ribbon |
| `robot_006` | Backup Battery Bruno | Charge bar fill/decay + vent pulse (`3.6s`) | Grid-routing light paths ripple across housing |
| `robot_007` | Inspection Drone Iris | Aperture iris open/close + scan line pass (`2.8s`) | Multi-spectrum concentric scan rings + lens flare sweep |
  | `robot_008` | Foundry Exosuit Aster | Molten level wave + Ember release (`4s`) | Nebular galaxy rotation + Constellation limb float |
| `robot_009` | Freewill Core Eve | Core pulse + containment ring orbit (`4.4s`) | Sunrise bloom cycle + network filament resonance wave |

### Celebration Motion Notes

For `icons/celebrations/robot_liberator.svg`:

1. Layer 1: static emblem silhouette.
2. Layer 2: slow radial dawn gradient expansion (`4.5s` loop).
3. Layer 3: sparse particle ascent (factory sparks turning into stars).
4. End state should feel calm and earned, not explosive.

## Phase 9: Tests and Documentation

Update test suites and public docs.

Tests to update/create:

1. `tests/test_gamification.py`
2. `tests/test_entitidex.py`
3. `tests/test_hero_management.py`
4. `test_story_system.py`
5. `test_story_logic.py`

Documentation updates:

1. `README.md` (story count/list if shown)
2. story/entitidex docs that enumerate current stories
3. `CHANGELOG.md`

## Recommended Commit Slices

1. `fix(story): remove hardcoded theme/entity totals and canonicalize active_story usage`
2. `feat(story): add robot story registry, gear theme, decisions, chapters, diary theme`
3. `feat(entitidex): add robot entity pool, perks, and encounter flavor`
4. `feat(entitidex-ui): add robot theme tab, completion card, and celebration audio wiring`
5. `chore(assets): add robot normal and exceptional entity svg assets`
6. `test(story): add robot story and entitidex coverage`
7. `docs(story): update story and entitidex documentation for robot theme`

## Validation Commands

```powershell
pytest tests/test_gamification.py tests/test_entitidex.py tests/test_hero_management.py test_story_system.py test_story_logic.py
```

```powershell
rg -n "story_active" -g "*.py" -g "*.md"
rg -n "total_entities = 36|for story_id in \[\"warrior\", \"scholar\", \"wanderer\", \"underdog\"\]" -g "*.py"
```

## Definition of Done

Done when all are true:

1. Robot story is fully integrated across story, UI, Entitidex, and assets.
2. No hardcoded story/entity count assumptions remain in runtime paths.
3. Canonical key usage (`active_story`) is consistent in reward/state flows.
4. All required tests pass.
5. Docs reflect the new story set and this plan can be archived as completed.

Current DoD check:

1. Met in working tree.
2. Met for updated runtime paths.
3. Met (`active_story` canonicalized where covered).
4. Met for targeted suites (`tests/test_gamification.py::TestMultiStorySystem`, `tests/test_entitidex.py`, `test_story_system.py`).
5. Partially met (this file updated; broader docs/changelog still optional follow-up).
