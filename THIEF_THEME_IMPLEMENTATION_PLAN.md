# Thief Theme Implementation Plan

Status: Implemented (pending commit/push)
Created: 2026-02-14
Last Updated: 2026-02-14
Owner: Codex + project maintainer

## Objective

Deliver a complete, production-ready thief theme package with:

- Story/theme already integrated in `gamification.py` (`story_id = "thief"`)
- Full Entitidex support (9 entities, perks, flavor routing, celebration, audio)
- UI/preview integrations
- Placeholder SVG assets for all required thief entities
- Visual bible and animation guidance for final art replacement

Narrative intent:

- A former street thief becomes a lawful protector and highly respected civic figure.
- Tone combines redemption, accountability, procedural discipline, and human warmth.

## Scope

In scope:

1. Story and theme integration verification.
2. Entitidex entity/perk/content implementation for thief.
3. Theme completion celebration and procedural celebration audio integration.
4. UI integration for Entitidex tabs and preview scripts.
5. Placeholder SVG generation and canonical art direction guide.

Out of scope:

1. Bespoke final illustration pass (placeholders are intentionally simple).
2. New gameplay systems unrelated to theme extension.

## Implementation Status

Implemented in working tree:

1. `entitidex/entity_pools.py`: added full `thief` entity pool (`thief_001..thief_009`).
2. `entitidex/entity_perks.py`: added perk coverage for all 9 thief entities.
3. `entitidex/encounter_system.py`: added thief dispatch + `_get_thief_flavor(...)`.
4. `entitidex/theme_completion.py`: added thief completion celebration metadata.
5. `entitidex/celebration_audio.py`: added `_compose_thief()` and composer mapping.
6. `entitidex_tab.py`: added thief exceptional color overrides and theme tab metadata.
7. `preview_entities.py`: added thief entity list and theme preview tab wiring.
8. `preview_character.py`: added thief hero power-tier preview row and updated subtitle.
9. `focus_blocker_qt.py`: added `_draw_thief_character()` dispatch (grounded hero silhouette path).
10. `icons/entities/` + `icons/entities/exceptional/` + `icons/celebrations/`: added thief placeholder SVG set.

## Theme Identity

- story_id: `thief`
- title: `The Badge and the Shadow`
- one-line pitch: A street thief trades shortcuts for accountability and earns lasting public trust.
- taxonomy: redemption, civic-duty, urban-procedural

## Entitidex Entity Design

Power curve: `10, 50, 150, 400, 700, 1100, 1500, 1800, 2000`

| Entity ID | Name | Role | Design intent |
|---|---|---|---|
| `thief_001` | Pocket Receipt Sparrow | evidence seed | Cute paper-bird that tracks truthful transactions |
| `thief_002` | Crime Sticker | interview support | Funny sticker that nudges admissions and shortens bluff cycles |
| `thief_003` | Lockpick Hairpin | precision access | Tiny tool for lawful openings and disciplined breach timing |
| `thief_004` | Stolen SIM | route intelligence | Cracked signal artifact that reveals hidden network paths |
| `thief_005` | Spray Can Silencer | stealth control | Mute canister that reduces panic/noise during extraction |
| `thief_006` | Hoodie Shadow | non-lethal infiltration | Empty fabric shell used for stealth-safe approach control |
| `thief_007` | Safe Cracker Stethoscope | evidence integrity | Stethoscope rig that reads lock truth without guesswork |
| `thief_008` | Crowbar Lever | breach endurance | Simple steel leverage tool with high-trust rescue utility |
| `thief_009` | Flashlight Beam | legendary reform unlock | Small tactical beam that exposes hidden/erased evidence |

## Visual Bible

Use this as the canonical art direction brief for thief entity art.

### Art Progression Rule

Visual progression must communicate:

1. survival skills from informal street systems,
2. growing procedural discipline,
3. transparent, accountable public leadership.

### Entity Art Direction Matrix

| Entity ID | Normal art direction | Exceptional uplift |
|---|---|---|
| `thief_001` | Folded receipt bird silhouette, scuffed paper textures, tiny ink marks | Clean silver paper edges, sharper audit glyph lines, brighter eye highlight |
| `thief_002` | Worn sticker badge, peeling corners, playful warning symbol | Foil sheen, cleaner geometry, holographic confession ring |
| `thief_003` | Rusty hairpin silhouette with lock-notch cues and pocket wear | Sonic tuning ribs, cleaner harmonic edge glow, master-key confidence |
| `thief_004` | Cracked SIM geometry, chipped corners, faint contact-strip noise | Matte black root-cell finish with trace-route pulse grid |
| `thief_005` | Rusted spray can body with worn cap and hush-foam motifs | Void canister shell, controlled mute haze, zero-flicker output cues |
| `thief_006` | Empty hoodie silhouette with subtle fabric fold motion | Near-black anomaly cloth with absorption edge shimmer |
| `thief_007` | Doctor stethoscope silhouette merged with safe dial accents | Resonator ring overlays and precise waveform glyphs |
| `thief_008` | Red steel crowbar form, chipped paint, honest tool readability | Plasma prybar edge glow with controlled thermal lane markings |
| `thief_009` | Dusty tactical beam module, narrow cone, minimal ornament | UV scanner uplift with admissible-evidence scan tracers |

### Global Style Guardrails

1. Favor silhouette readability over fine detail clutter.
2. Keep objects believable as urban tools first, fantasy symbols second.
3. Humor should come from concept contrast, not visual chaos.
4. Exceptional variants must feel like capability upgrades, not random recolors.
5. Legendary remains visually small by design; power is implied via context effects.

## Animation Direction Guide

Use this section as canonical motion guidance for thief visuals.

### Motion Narrative

1. Early tier: awkward but earnest motion loops.
2. Mid tier: cleaner timing and procedural confidence.
3. Late tier: calm, controlled, high-trust command cues.
4. Legendary tier: tiny source object, broad but restrained systemic response.

### Technical Standards

1. Preferred format: animated SVG with static fallback.
2. Loop durations:
   - common/uncommon: `3.0s` to `4.4s`
   - rare/epic: `2.6s` to `3.8s`
   - legendary: `3.8s` to `5.4s`
3. Max concurrently animated parts per icon: `<= 3`.
4. Avoid strobing or flashes above `3 Hz`.
5. Preserve readability at 64-96 px.
6. Exceptional motion should add control/clarity layers, not replace identity motion.
7. Support reduced-motion fallback frame.

### Entity Animation Matrix

| Entity ID | Normal animation | Exceptional uplift |
|---|---|---|
| `thief_001` | wing flutter + receipt stamp bounce | cleaner cadence + audit spark trace |
| `thief_002` | peel-curl + badge pulse | foil shimmer + ring sweep |
| `thief_003` | micro lock-click + pin vibration loop | harmonic sweep + clean unlock pulse |
| `thief_004` | SIM contact blink + packet ripple | rooted trace-lattice sweep + confidence lock |
| `thief_005` | canister hiss puff + nozzle twitch | controlled mute-fog wave + stable pressure pulse |
| `thief_006` | cloth drift + edge fade | vantablack absorption shimmer + silhouette snapback |
| `thief_007` | stethoscope diaphragm pulse + dial tick | resonator waveform ring + precision settle |
| `thief_008` | pry angle shift + impact settle | plasma edge charge + controlled vent trail |
| `thief_009` | flashlight cone sweep + dust reveal | UV scan pass + forensic marker bloom |

### Hero Animation Direction (CharacterCanvas)

1. Idle stance drift: 1-2 px over `3.8s`.
2. Coat edge movement: low-amplitude sway over `4.4s`.
3. Badge/relic pulse: subtle cycle every `2.6s`.
4. High-tier aura scales by coherence, not speed.
5. Motion should read deliberate and trained, never frantic.

## Asset Manifest

### Required normal entity placeholders

- `icons/entities/thief_001_pocket_receipt_sparrow.svg`
- `icons/entities/thief_002_crime_sticker.svg`
- `icons/entities/thief_003_lockpick_hairpin.svg`
- `icons/entities/thief_004_stolen_sim.svg`
- `icons/entities/thief_005_spray_can_silencer.svg`
- `icons/entities/thief_006_hoodie_shadow.svg`
- `icons/entities/thief_007_safe_cracker_stethoscope.svg`
- `icons/entities/thief_008_crowbar_lever.svg`
- `icons/entities/thief_009_flashlight_beam.svg`

### Required exceptional entity placeholders

- `icons/entities/exceptional/thief_001_pocket_receipt_sparrow_exceptional.svg`
- `icons/entities/exceptional/thief_002_crime_sticker_exceptional.svg`
- `icons/entities/exceptional/thief_003_lockpick_hairpin_exceptional.svg`
- `icons/entities/exceptional/thief_004_stolen_sim_exceptional.svg`
- `icons/entities/exceptional/thief_005_spray_can_silencer_exceptional.svg`
- `icons/entities/exceptional/thief_006_hoodie_shadow_exceptional.svg`
- `icons/entities/exceptional/thief_007_safe_cracker_stethoscope_exceptional.svg`
- `icons/entities/exceptional/thief_008_crowbar_lever_exceptional.svg`
- `icons/entities/exceptional/thief_009_flashlight_beam_exceptional.svg`

### Optional celebration placeholder

- `icons/celebrations/thief_celebration.svg`

## Custom Hook Audit

| Hook category | Pattern | Thief participation | Decision |
|---|---|---|---|
| Feature gates by entity ID | Legacy special-case IDs in some subsystems | partial | thief uses generic perk gates; no new hardcoded ID gate added |
| Encounter flavor variants | Theme dispatch in `encounter_system.py` | yes | added `thief` branch + dedicated flavor function |
| Saved encounter/recalc rules | Perk types drive availability | yes | thief perks include `RECALC_PAID` and `RECALC_RISKY` providers |
| Theme completion visuals/audio | theme metadata + composer map | yes | added thief celebration entry and thief composer |
| Visual override maps | exceptional color map + tab info | yes | added thief color entries and tab metadata |
| Hero render dispatch | story-theme branch in `CharacterCanvas` | yes | added dedicated thief dispatch method (grounded renderer path) |

## Validation Checklist

1. Verify `ENTITY_POOLS["thief"]` has 9 entities and proper ID order.
2. Verify `ENTITY_PERKS` has all `thief_001..thief_009` entries.
3. Verify thief encounters produce thief flavor text.
4. Verify Entitidex tab shows thief as a selectable theme.
5. Verify preview scripts show thief entity and character sections.
6. Verify thief celebration metadata resolves and audio composer is available.
7. Verify all thief placeholder SVG files resolve via filename conventions.

## Definition of Done

Thief package is complete when:

1. Story, gear, diary, and hero theme are selectable and stable.
2. Entitidex thief collection is fully implemented (entities + perks + flavor + celebration).
3. Placeholder assets exist for all required thief SVG paths.
4. Visual bible and animation guidance are documented for future final-art pass.
