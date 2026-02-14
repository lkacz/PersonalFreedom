# Space Pirate Theme Implementation Plan

Status: Planned  
Created: 2026-02-14  
Owner: Codex + project maintainer

## Objective

Design and implement a new story/theme/hero with `story_id = "space_pirate"` that fully complies with:

- `STORY_THEME_EXTENSION_SPEC.md` (canonical contract)
- current multi-story architecture in `gamification.py`
- Entitidex integration requirements (entities/perks/ui/celebration)

Creative mandate:

1. Space pirate fantasy with characterful humor and emotional stakes.
2. Entitidex entities must be surprising/non-obvious (not generic pirate cliches).
3. Legendary entity must appear small/disappointing at first glance, then reveal overwhelming narrative power.

## Scope

In scope:

1. Full story package (7 chapters, 3 decisions, 8 endings).
2. Theme-specific gear naming and diary voice.
3. Entitidex package with 9 entities (`space_pirate_001..009`) and full perk coverage.
4. UI and system integration across runtime touchpoints.
5. Hook audit and regression-safe rollout.

Out of scope:

1. Rework of existing legacy themes.
2. Asset polish beyond required integration baseline (if another agent owns art execution, this plan remains canonical for direction/integration).

## Theme Identity Draft

- `story_id`: `space_pirate`
- Working title: `The Orbit Outlaw's Ledger`
- Tone: irreverent, clever, humane
- Core conflict: steal autonomy from exploitative star empires without becoming what you hate
- Hero fantasy: under-resourced rogue captain who wins by wit, coalition-building, and disciplined risk

## Narrative Blueprint (Implementation-Level)

### Decision Spine

1. Chapter 2 decision (`space_pirate_code`):
   - A: Keep pirate code (principled constraints)
   - B: Break code for tactical advantage
2. Chapter 4 decision (`space_pirate_confession`):
   - A: Trust your quartermaster/love interest with the full truth
   - B: Keep secrets to protect them
3. Chapter 6 decision (`space_pirate_endgame`):
   - A: Hit the flagship hard and fast
   - B: Expose corruption and force systemic transition

### Chapter Arc

1. Salvage raid gone wrong reveals empire-scale coercion.
2. First major moral choice defines leadership style.
3. Crew cohesion rises/falls based on trust trajectory.
4. Romance/trust pivot with operational consequences.
5. Midgame reversal: bounty, betrayal risk, coalition politics.
6. Endgame choice between rupture and durable reform.
7. Eight-path finale (`AAA..BBB`) with satisfying consequences and practical life lesson.

### Learning Outcomes

1. Freedom without accountability degrades into predation.
2. Short-term wins can destroy long-term legitimacy.
3. Trust is a strategic asset, not just an emotional luxury.

## Entitidex Design Mandate

### Surprising/Funny Entity Principle

Entity roster must avoid obvious space-pirate mascots (parrots, swords, standard skull drones).  
Prefer absurd, overlooked, or mundane-looking objects/creatures with high narrative utility.

### Planned Entity Concepts (Draft)

Power curve target remains: `10, 50, 150, 400, 700, 1100, 1500, 1800, 2000`.

1. `space_pirate_001` - **Scuffed Customs Stamp**
   - Looks like office junk; actually forges access to half the quadrant.
2. `space_pirate_002` - **Laughing Airlock Seal**
   - A rubber gasket that squeaks at danger and saves hull integrity.
3. `space_pirate_003` - **Contraband Tea Kettle**
   - Comic morale item that doubles as pressure-decoy signal jammer.
4. `space_pirate_004` - **Dock Rat Cartographer**
   - Tiny station vermin with impossible memory for hidden routes.
5. `space_pirate_005` - **Mutiny Complaint Box**
   - Bureaucratic relic that predicts interpersonal failure before betrayal.
6. `space_pirate_006` - **Polite Boarding Cone**
   - Traffic cone-looking beacon that nulls hostile targeting if planted first.
7. `space_pirate_007` - **Audit Ghost Ledger**
   - Sentient accounting tablet that exposes siphoned war funds in real time.
8. `space_pirate_008` - **Retired Parade Thruster**
   - Ridiculous ceremonial engine that becomes a precision escape miracle.
9. `space_pirate_009` - **Pocket Gravity Button** (legendary non-obvious apex)
   - Appears as a cheap coat button; actually a dormant singularity governor.
   - Story reveal: it can pin dreadnought fleets in place without firing a shot.

Legendary intent:

1. First impression: tiny, unserious, almost disappointing.
2. Reveal: strategic, civilization-scale power with heavy ethical consequences.

## Phase Plan

## Phase 0: Preflight Safety and Registry Audit

Tasks:

1. Confirm no invalid key usage (`story_active`).
2. Confirm no hardcoded story/entity totals in runtime paths.
3. Confirm target branch can accept new story without migration breakage.

## Phase 1: Story and Theme Registry

Primary file: `gamification.py`

Tasks:

1. Add `AVAILABLE_STORIES["space_pirate"]`.
2. Add `STORY_GEAR_THEMES["space_pirate"]` with full required schema.
3. Add diary theme payload (`STORY_DIARY_THEMES["space_pirate"]`) and sentence routing.

## Phase 2: Narrative Data Implementation

Primary file: `gamification.py`

Tasks:

1. Add `SPACE_PIRATE_DECISIONS` (3 decision points).
2. Add `SPACE_PIRATE_CHAPTERS` (7 chapters + branch-aware content + 8 endings).
3. Register in `STORY_DATA["space_pirate"]`.

## Phase 3: Hero UI and Story Labels

Primary file: `focus_blocker_qt.py`

Tasks:

1. Add hero display name map entry.
2. Add CharacterCanvas dispatch for `space_pirate` (dedicated renderer or intentional fallback).
3. Update debug/admin story selectors.

Secondary label maps:

1. Saved encounter story display naming in `gamification.py`.
2. Any dialog-level theme display maps in `entity_encounter_dialog.py`.

## Phase 4: Entitidex Content and Perks

Primary files:

- `entitidex/entity_pools.py`
- `entitidex/entity_perks.py`
- `entitidex/encounter_system.py`

Tasks:

1. Add 9 entity definitions with complete metadata.
2. Add perk coverage for all 9 IDs.
3. Implement theme-specific encounter flavor routing.

## Phase 5: Entitidex UI, Completion, Audio

Primary files:

- `entitidex_tab.py`
- `entitidex/theme_completion.py`
- `entitidex/celebration_audio.py`

Tasks:

1. Add theme tab metadata.
2. Add optional exceptional color overrides.
3. Add theme completion celebration card.
4. Add theme audio composer mapping or explicit default strategy.

## Phase 6: Custom Entity Hook Audit

Audit categories:

1. Feature gates by `entity_id`.
2. Special dialogs/tips by `entity_id`.
3. Narrative text variants and encounter route special cases.
4. Saved encounter recalculation providers.
5. Visual overrides and cross-system helper hooks.

Output requirement:

1. For each category, mark `participates` vs `fallback`.
2. Document explicit reasoning for non-participation.

## Phase 7: Asset Manifest and Art Direction

Required outputs:

1. 9 normal SVGs in `icons/entities/`.
2. 9 exceptional SVGs in `icons/entities/exceptional/`.
3. Optional celebration asset in `icons/celebrations/`.

Naming contract:

- `icons/entities/space_pirate_00X_<entity_slug>.svg`
- `icons/entities/exceptional/space_pirate_00X_<entity_slug>_exceptional.svg`

Art direction constraints:

1. Silhouette-first readability.
2. Humor through concept and pose, not visual noise.
3. Legendary item must visibly read "small/trivial" while lore/perk text conveys real scale.

## Phase 7A: Visual Bible (Entity Art Direction)

Use this as the Space Pirate theme visual bible for entity art and animation.

### Art Progression Rule

Visual progression across the 9 entities must communicate:

1. scrappy improvisation and playful misdirection,
2. rising crew coordination and political leverage,
3. disciplined systemic power over brute force.

### Entity Art Direction Matrix

| Entity ID | Name | Story Role | Normal Art Direction | Exceptional Art Direction |
|---|---|---|---|---|
| `space_pirate_001` | Scuffed Customs Stamp | Entry through ignored systems | Worn handheld stamp with chipped paint, greasy thumb marks, and dock paperwork texture cues. Palette: slate + brass + faded orange. | Cleaner forged stamp body with holographic seal aura and precision edge lighting. |
| `space_pirate_002` | Laughing Airlock Seal | Comic safety sentinel | Rubbery gasket silhouette with expressive pressure ripples and warning grin motif. Palette: teal + charcoal + mint highlights. | Multi-ring pressure harmonics, cleaner contouring, and protective resonance halo. |
| `space_pirate_003` | Contraband Tea Kettle | Morale and misdirection | Retro kettle canister with smug steam vent and patched wiring clip-ons. Palette: warm copper + navy + cream steam tones. | Refined polished shell, aurora-steam trails, and tactical decoy glyph accents. |
| `space_pirate_004` | Dock Rat Cartographer | Hidden-route intelligence | Tiny station rat with map-scrap harness and route-marker tail light. Palette: steel gray + ice blue. | Sharper navigator silhouette, starmap projection ribbons, and elite scout posture. |
| `space_pirate_005` | Mutiny Complaint Box | Governance and conflict prediction | Bureaucratic drop-box relic with bent slot flap, stamped warning tabs, and satirical office vibe. Palette: maroon + gunmetal + paper beige. | Tribunal-grade casing, predictive ticker glow, and order-with-humor authority read. |
| `space_pirate_006` | Polite Boarding Cone | Non-lethal tactical control | Traffic-cone beacon with absurdly formal insignia and clean targeting-null zone markings. Palette: hazard amber + deep blue-gray. | Sovereign boarding beacon look with refined anti-lock targeting rings and command trim. |
| `space_pirate_007` | Audit Ghost Ledger | Truth weaponized | Haunted ledger slab with spectral page edges, redaction scars, and floating account lines. Palette: cyan-white spectral glow + graphite. | Forensic-grade clarity, layered data phantoms, and high-authority disclosure framing. |
| `space_pirate_008` | Retired Parade Thruster | Last-resort escape mastery | Ceremonial engine can with dented parade chrome, tassel mounts, and patched vector nozzles. Palette: cobalt + silver + ember orange. | Recommissioned precision thruster with elegant vector fins and choreographed plume geometry. |
| `space_pirate_009` | Pocket Gravity Button | Small object, civilization-scale leverage | Tiny coat-button silhouette in protective mount; intentionally underwhelming first read. Palette: olive-gold + muted ivory + low cosmic glow. | Keep small scale; add controlled lensing distortions and orbiting micro-field tracers that imply immense restraint. |

### Global Style Guardrails

1. Preserve comedic readability at first glance and strategic credibility at second glance.
2. Prefer utilitarian wear details (labels, screws, patches, audit marks) over ornamental clutter.
3. Exceptional variants must look upgraded in control and precision, not just brighter.
4. Keep the legendary intentionally small in silhouette; power is conveyed through environmental reaction.

## Phase 7B: Animation Direction Guide

Use this section as the canonical motion brief for Space Pirate theme visuals.

### Motion Narrative

Animation should mirror the story arc:

1. Early entities: scrappy, slightly awkward utility loops.
2. Mid entities: coordinated crew-tool choreography.
3. Late entities: stable, high-confidence system control.
4. Legendary finish: tiny source object with large but disciplined field response.

### Technical Standards

1. Preferred delivery: animated SVG (SMIL/CSS transforms) with static fallback.
2. Loop durations:
   - common/uncommon: `3.0s` to `4.4s`
   - rare/epic: `2.6s` to `3.8s`
   - legendary: `3.6s` to `5.2s` with layered subloops
3. Keep max concurrently animated parts per icon to `<= 3`.
4. Avoid strobing/high-frequency flashes (`> 3 Hz`).
5. Maintain silhouette readability at small sizes (64-96 px).
6. Exceptional variants should add a control/precision layer, not replace identity motion.
7. Reduced-motion policy: provide static fallback frame and disable non-essential oscillation.

### Hero Animation Direction (CharacterCanvas)

1. Idle drift: subtle `1-2 px` vertical sway over `3.8s`.
2. Coat/cape or jacket edge: low-amplitude flutter over `4.5s`.
3. Visor/eye highlight: restrained glint pulse every `2.4s`.
4. Handheld relic glow: slow confidence pulse (normal `3.0s`, high tier `3.6s` dual pulse).
5. Tier aura should increase in structure and cohesion, not raw flicker speed.

### Entity Animation Matrix

| Entity ID | Name | Normal Animation | Exceptional Uplift |
|---|---|---|---|
| `space_pirate_001` | Scuffed Customs Stamp | Stamp compression + ink rebound (`3.6s`) | Holographic seal imprint sweep with cleaner cadence |
| `space_pirate_002` | Laughing Airlock Seal | Gentle squish pulse + pressure ripple (`3.4s`) | Harmonic safety ring expansion and stabilized hull-beat rhythm |
| `space_pirate_003` | Contraband Tea Kettle | Lid rattle + steam puff drift (`3.2s`) | Controlled aurora-steam ribbon + signal-decoy blink |
| `space_pirate_004` | Dock Rat Cartographer | Quick head tilt + route-tail tracer (`2.8s`) | Starmap arc projection with precise waypoint locking |
| `space_pirate_005` | Mutiny Complaint Box | Slot flap clack + paper rise/fall (`3.0s`) | Predictive ticker glow and tribunal pulse frame |
| `space_pirate_006` | Polite Boarding Cone | Beacon spin + polite warning blink (`3.1s`) | Target-null lattice sweep with command-grade timing |
| `space_pirate_007` | Audit Ghost Ledger | Page flutter + ghost numeral orbit (`3.3s`) | Multi-layer data apparition and forensic scan sweep |
| `space_pirate_008` | Retired Parade Thruster | Sputter burst + nozzle wobble correction (`3.5s`) | Clean vector-thrust plume choreography and inertial ring lock |
| `space_pirate_009` | Pocket Gravity Button | Tiny core blink + subtle local lens warp (`4.8s`) | Orbiting micro-field tracers + calm macro-distortion wave |

### Celebration Motion Notes

For `icons/celebrations/space_pirate_accord.svg`:

1. Layer 1: static accord emblem (crew + civic symbol).
2. Layer 2: slow orbital arc drift (`4.8s` loop).
3. Layer 3: sparse "paper-to-stars" particles (audit sheets becoming constellations).
4. Final read should feel earned and cooperative, not explosive conquest.

## Phase 8: Tests and Validation

Automated minimum:

```powershell
pytest tests/test_gamification.py tests/test_entitidex.py tests/test_hero_management.py test_story_system.py test_story_logic.py
```

Focused checks:

1. New story is present in canonical registries.
2. Story structure is 7 chapters / 3 decisions.
3. Exactly 9 entities in `ENTITY_POOLS["space_pirate"]`.
4. Perk coverage exists for all 9 IDs.
5. No hardcoded total assumptions regress.
6. Hook-audit behavior passes fallback/participation expectations.

Manual checks:

1. Story appears in UI selection.
2. Chapter 1 preview/lock behavior works.
3. Hero identity and labels resolve correctly.
4. Space Pirate entities encounter/capture correctly.
5. Theme completion celebration renders and plays audio.

## Deliverables (Plan Stage)

This planning stage must produce:

1. Finalized story/gear/diary/entity/perk payload drafts.
2. Hook audit table with explicit implementation decisions.
3. Asset filename manifest.
4. Ordered file-by-file patch list with risk notes.

## Definition of Done

Done when all are true:

1. `space_pirate` is integrated across all required touchpoints in `STORY_THEME_EXTENSION_SPEC.md`.
2. Story and entity systems are fully data-complete and internally consistent.
3. Legendary non-obvious entity payoff is reflected in lore, perks, and ending consequences.
4. Test suite passes with no regressions in existing themes.
5. Documentation and changelog reflect the new theme.
