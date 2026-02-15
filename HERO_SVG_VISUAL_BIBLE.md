# Hero SVG Visual Bible

Status: Production guidance for hero and gear SVG creation  
Scope: All current story themes  
Last updated: 2026-02-14

## 1. Art Production Standards

### 1.1 Canvas and Export

1. Use `viewBox="0 0 180 220"` for all hero layers.
2. Keep transparent background in every SVG.
3. Keep consistent hero grounding line around y=180..190.
4. Export one logical layer per file (base, gear, fx).

### 1.1a Slot-Fit Authoring Contract (Mandatory)

Gear files are not free-floating icons. They are composited onto a hero body through slot windows, so each item must be authored to fit a body region cleanly.

1. Draw each gear item as a slot-ready object that occupies most of the canvas (target occupancy: about 70%-92% of `180x220`).
2. Keep transparent margins tight and intentional (avoid tiny centered objects with large empty borders).
3. Keep item orientation body-compatible for its slot family:
   - Helmet: readable lower contact edge for head fit.
   - Chestplate: torso-centered mass and chest-facing symmetry.
   - Gauntlets: hand/forearm logic with clear left-right read.
   - Boots: sole/ground read near lower area.
   - Shield: inner grip/strap toward body-facing edge.
   - Weapon: held-orientation with a readable grip side.
   - Cloak: drape flow from shoulders downward, not icon-floating.
   - Amulet: compact chest ornament read, not oversized prop.
4. Do not draw full hero scenes inside gear files; author only the gear object layer.

### 1.2 Readability Rules

1. Silhouette must read at mini-size (70x90) and full-size (180x220).
2. Avoid thin strokes below 1.25px in source scale.
3. Keep face focal contrast high for identity recognition.
4. Use 3-value shading at minimum (light, mid, shadow).

### 1.2a Depth, Perspective, and Lighting (Mandatory)

1. Use gradient grading deliberately to communicate object depth (do not rely on flat fills).
2. Define a consistent key light direction per theme and keep it coherent across base + gear.
3. Include contact shadow cues where parts overlap to reinforce layer stacking and perspective.
4. Use subtle rim light/specular accents on high-value edges to improve readability and material feel.
5. Apply perspective-aware shape tapering/foreshortening where appropriate so forms feel dimensional.
6. Keep depth effects tasteful; avoid noisy over-rendering that hurts small-size readability.

### 1.3 Rarity Progression (Mandatory)

Items must change **form language**, not only color:

1. Common: practical, minimal detail, blunt silhouette.
2. Uncommon: one structural upgrade (trim, secondary plate, accessory).
3. Rare: distinct silhouette variation (wings, fins, segmented parts, asymmetry).
4. Epic: thematic signature motif + story-specific personality detail (avoid generic trope shapes).
5. Legendary: transformed geometry with memorable, non-cliche identity; must feel original to the theme.
6. Celestial: apex form that is surprising yet coherent with story logic; avoid abstract noise and overdesigned sci-fi spikes.

### 1.4 Animation Readiness

Even in static rendering mode, design files as animation-ready:

1. Separate movable subgroups in authoring source (cloak, antenna, tassel, sparks).
2. Keep pivots obvious (hinges, straps, joints).
3. Use layered glow/FX assets for high-tier motion.
4. Add minimal motion hooks where applicable (tiny idle sway, blink cue, glint pass), never busy loops.

### 1.5 Tone and Personality Guardrails

Keep visuals likable, relatable, and playful across all themes:

1. Favor tangible, everyday-inspired forms over abstract sci-fi geometry.
2. Use friendly silhouettes (clear head/torso/readable props, soft or rounded transitions where possible).
3. Include one witty or charming detail per hero/slot family (a clever badge, mascot-like motif, playful trim).
4. Keep designs emotionally warm: aspirational and fun, not cold or alien.
5. Avoid over-abstract symbols that read as generic shapes without story context.
6. Prefer original, story-grounded shapes over genre cliches, especially in Epic/Legendary/Celestial tiers.
7. Surprising design beats are encouraged when they remain readable and thematically coherent.

### 1.6 Eye Expression and Motion Readiness (Global)

All hero bases should be authored with eye motion in mind:

1. Provide separate eye/eyelid groups in source authoring (left eye, right eye, upper/lower lids where applicable).
2. Design for quick saccadic gaze shifts: short, fast jumps with tiny settle motion.
3. Design for fast blinks: brief close-open cycles, with occasional double blink behavior.
4. Keep a clean neutral frame (forward gaze, eyes open) for static render fallback.
5. Prioritize cute/expressive readability over hyper-realistic eye detail.

## 2. Layer Contract

For each `story_id`:

1. `hero_base.svg`
2. `gear/<slot>/<slot>_<rarity>.svg` minimum set (8 slots x 6 rarities)
3. `gear/<slot>/<item_type>_<rarity>.svg` preferred set for item-type uniqueness
4. Optional `fx/tier_<tier>.svg`

Slots:

1. `helmet`
2. `chestplate`
3. `gauntlets`
4. `boots`
5. `shield`
6. `weapon`
7. `cloak`
8. `amulet`

### 2.1 Canonical Slots vs Story Meaning

1. Slot names above are technical keys for runtime compatibility and file lookup.
2. Story-facing meaning is theme-specific and must come from `STORY_GEAR_THEMES[story_id]` (`slot_display` + `item_types`).
3. Only warrior should default to literal armor readings like "helmet/chestplate".
4. Non-warrior themes must reinterpret slot art to match their world (for example, Helmet key may represent cap, visor, crown, hat, goggles, etc.).

### 2.2 Story Vocabulary Lock (Non-Negotiable)

1. Treat each theme packet `item_types` list as source-of-truth vocabulary for visual concepts.
2. Do not introduce cross-genre substitutions that are not represented in that vocabulary.
3. If a concept is not in the slot `item_types` list, do not use it as a primary item identity.
4. For thief specifically: keep modern urban civic/tactical semantics; avoid medieval rogue defaults.

### 2.3 Runtime Slot Box Reference (Normalized)

Use this placement map when judging body-fit and composition intent. Values are normalized `[x, y, width, height]` in the `180x220` canvas.

| Slot key | Slot box |
| --- | --- |
| `helmet` | `[0.28, 0.06, 0.44, 0.28]` |
| `chestplate` | `[0.24, 0.22, 0.52, 0.34]` |
| `gauntlets` | `[0.18, 0.30, 0.64, 0.34]` |
| `boots` | `[0.28, 0.64, 0.44, 0.30]` |
| `shield` | `[0.08, 0.28, 0.34, 0.44]` |
| `weapon` | `[0.58, 0.24, 0.34, 0.52]` |
| `cloak` | `[0.16, 0.20, 0.68, 0.64]` |
| `amulet` | `[0.40, 0.30, 0.20, 0.20]` |

Interpretation:

1. Runtime fit places gear into these slot windows; your SVG must still read correctly after that transform.
2. If an item looks good only when centered as a tiny icon, the asset is invalid for this pipeline.
3. Validate against real hero composition, not isolated file view.

## 3. Theme Direction

## 3.1 Warrior

Hero base: disciplined frontline fighter, broad stance, battle-ready posture.  
Palette: steel, leather, bronze, ember accents.

Slot directives:

1. Helmet: from basic helm to dragon-crowned war helm.
2. Chestplate: tunic to articulated war cuirass with layered pauldrons.
3. Gauntlets: wraps to plated claw gauntlets.
4. Boots: field boots to heavy sabatons with engraved greaves.
5. Shield: buckler to rune-carved fortress shield.
6. Weapon: short blade to legendary polearm/dragon-forged great weapon.
7. Cloak: plain cape to battle-banner cloak with torn heroic edge.
8. Amulet: simple talisman to command sigil medallion.

Animation cues:

1. Idle: subtle chest rise and cape settle.
2. Weapon: periodic metal glint sweep.
3. Cloak: low-frequency lateral sway.
4. Legendary: ember motes orbit chest and blade.

## 3.2 Scholar

Hero base: composed academic archetype, upright and precise silhouette.  
Palette: navy, parchment, mahogany, ink, gold filigree.

Slot directives:

1. Helmet: scholar cap -> crowned mortarboard/lens halo.
2. Chestplate: layered robe/vest -> ceremonial knowledge mantle.
3. Gauntlets: writing gloves -> illuminated script bracers.
4. Boots: quiet shoes -> formal arcane-soled footwear.
5. Shield: notebook -> codex bulwark with page-metal fusion.
6. Weapon: quill/pointer -> gravity pen staff.
7. Cloak: research shawl -> archive veil with glyph border.
8. Amulet: pocket watch -> chronicle core pendant.

Animation cues:

1. Idle: page flutter and tiny dust motes.
2. Weapon: ink-line trace pulse.
3. Shield: page-corner flick and glyph blink.
4. Legendary: rotating annotation ring around amulet.

## 3.3 Wanderer

Hero base: dream traveler, soft asymmetry, floating textile behavior.  
Palette: moonlight blue, indigo, lavender, starlight cyan.

Slot directives:

1. Helmet: circlet/hood -> astral crown with crescent frame.
2. Chestplate: woven dream vest -> constellation breast lattice.
3. Gauntlets: wraps -> star-threaded handframes.
4. Boots: cloud steps -> moon-phase drifters.
5. Shield: dream ward -> aurora mirror aegis.
6. Weapon: wand/staff -> cosmic key-scepter.
7. Cloak: veil -> night-sky mantle with internal star map.
8. Amulet: moon crystal -> singularity prism.

Animation cues:

1. Idle: slow bob (floating feel).
2. Cloak: wave-like drift.
3. Amulet: heartbeat glow.
4. Legendary: faint parallax starfield FX layer.

## 3.4 Underdog

Hero base: everyday worker transformed into resilient street champion.  
Palette: charcoal, denim blue, office neutrals, tactical neon accents.

Slot directives:

1. Helmet: cap/headset -> urban command headset-crown hybrid.
2. Chestplate: hoodie/blazer -> reinforced civic vest.
3. Gauntlets: wrist tech -> utility control gauntlets.
4. Boots: sneakers -> impact-resistant urban stompers.
5. Shield: laptop/folder -> portable barrier slate.
6. Weapon: phone/stapler motif -> improvised tactical baton.
7. Cloak: jacket/windbreaker -> iconic comeback coat.
8. Amulet: badge/keycard -> crest of earned legitimacy.

Animation cues:

1. Idle: slight shoulder shift, practical stance.
2. Weapon: status LED pulse.
3. Shield: scan-line sweep.
4. Legendary: city-light reflections moving across armor planes.

## 3.5 Scientist

Hero base: modern researcher with precision instrument profile.  
Palette: white lab neutrals, cyan optics, hazard yellow, graphite.

Slot directives:

1. Helmet: goggles -> quantum lens crown.
2. Chestplate: lab coat -> layered research exoshell.
3. Gauntlets: latex -> nano-manipulator hands.
4. Boots: sterile shoes -> magnetic precision boots.
5. Shield: tablet/notebook -> adaptive data slab.
6. Weapon: pipette/tool -> modular field instrument.
7. Cloak: biosafety drape -> containment field cape.
8. Amulet: ID badge -> breakthrough reactor token.

Animation cues:

1. Idle: instrument indicator blinks.
2. Weapon: measurement line sweep.
3. Shield: UI pulse.
4. Legendary: controlled particle helix around amulet.

## 3.6 Robot

Hero base: factory-origin machine evolving toward self-directed identity.  
Palette: steel blue, gunmetal, warning amber, electric cyan.

Slot directives:

1. Helmet: visor frame -> autonomous cognition crown.
2. Chestplate: service shell -> liberated core housing.
3. Gauntlets: servo hands -> adaptive heavy manipulators.
4. Boots: conveyor treads -> precision mobility struts.
5. Shield: guard panel -> protocol-breaking harmonic barrier.
6. Weapon: wrench/cutter -> high-output forge arm.
7. Cloak: thermal wrap -> plume-like heat mantle.
8. Amulet: memory chip -> freewill kernel with reactor ring.

Animation cues:

1. Idle: micro servo settle and eye scan.
2. Weapon: weld-spark flicker.
3. Chest core: pulse loop tied to rarity.
4. Legendary: rotating ring + aurora exhaust FX layer.

## 3.7 Space Pirate

Hero base: opportunistic but charismatic orbital outlaw.  
Palette: void navy, brass, hazard orange, ion teal.

Slot directives:

1. Helmet: tricorne/goggles -> star captain battle helm.
2. Chestplate: plunder coat -> vacuum-sealed corsair cuirass.
3. Gauntlets: magnetic grips -> boarding command gauntlets.
4. Boots: deck boots -> grav-stabilized hull walkers.
5. Shield: deflector plate -> treaty-breaker bastion.
6. Weapon: hook/cutlass -> gravity-bent duel weapon.
7. Cloak: dust veil -> comet-tail command cape.
8. Amulet: contraband charm -> singularity ledger lock.

Animation cues:

1. Idle: low hover sway as if on ship deck.
2. Cloak: vacuum flutter bursts.
3. Weapon: charged ion edge shimmer.
4. Legendary: star-speck drift and lens flare sweep.

## 3.8 Thief

Hero base: agile infiltrator turned disciplined public guardian.  
Palette: dusk blue, asphalt gray, badge silver, signal red.

Slot directives:

1. Helmet: cap/hood -> inspector cap with tactical optics.
2. Chestplate: vest -> civic protector armor.
3. Gauntlets: grip gloves -> restraint-enabled tactical gloves.
4. Boots: silent soles -> pursuit-grade city runners.
5. Shield: barrier frame -> public order bulwark.
6. Weapon: baton/light tool -> command enforcement staff.
7. Cloak: trench coat -> ceremonial reform mantle.
8. Amulet: badge token -> city crest of trust.

Animation cues:

1. Idle: subtle coat hem movement.
2. Weapon: baton light flick.
3. Shield: evidence grid flash.
4. Legendary: heartbeat beacon sweep (public guardian signal).

## 3.9 Zoo Worker

Hero base: grounded caretaker with mythic destiny undertone.  
Palette: earth greens, canvas tan, storm gray, ember gold.

Slot directives:

1. Helmet: keeper hat -> dragon-rider crest brim.
2. Chestplate: field vest -> sanctuary guardian harness.
3. Gauntlets: handling gloves -> scaleproof keeper gauntlets.
4. Boots: mud/rain boots -> stormflight expedition boots.
5. Shield: gate panel -> dragonproof sanctuary ward.
6. Weapon: feed hook/staff -> ember-guiding lance.
7. Cloak: rain poncho -> dawn mantle with wing contour.
8. Amulet: whistle/token -> time-feather heart crest.

Animation cues:

1. Idle: cloth flutter and lantern pulse.
2. Cloak: wing-like lift-drop rhythm.
3. Amulet: warm ember breathing glow.
4. Legendary: distant scale shimmer and horizon light sweep.

## 4. Rarity-Driven Gear Shape Rules (All Themes)

Apply to every slot, every theme:

1. Common: one dominant shape, no tertiary silhouette.
2. Uncommon: add one secondary silhouette element.
3. Rare: add one directional motion cue shape (fin, plume, blade curve, trailing edge).
4. Epic: add one identity-defining motif unique to theme (not a genre default trope).
5. Legendary: dual-motif composition plus ceremonial framing geometry with unique silhouette logic.
6. Celestial: introduce a surprising apex twist that still reads as the same item family and theme.

Do not satisfy rarity progression with hue shift alone.

## 5. Slot-Specific Animation Blueprint

Use these animation families consistently for canonical slot keys and their theme-specific semantic equivalents:

1. Helmet: indicator blink, visor sweep, minor tilt.
2. Chestplate: center glow pulse or panel breathing.
3. Gauntlets: knuckle light wave or finger servo twitch.
4. Boots: sole glow ripple or dust/spark kick.
5. Shield: border sweep, sigil scan, ripple shield pulse.
6. Weapon: edge glint, energy charge, looped hum wave.
7. Cloak: low-frequency sway, rare gust spikes.
8. Amulet: heartbeat pulse, orbiting mote loop.
9. Hero eyes (base layer): saccadic micro-jumps + fast blinks (with occasional double blink).
10. Global motion cap: keep motion minimal, readable, and tasteful.

## 6. Asset QA Checklist

For every exported SVG:

1. Correct naming convention and folder.
2. Scales correctly at 70x90 and 180x220.
3. No clipped geometry outside viewBox.
4. Layer order works over `hero_base.svg`.
5. Epic and Legendary are silhouette-distinct from lower tiers.
6. Visual style aligns with theme section in this bible.
7. Higher tiers (Epic/Legendary/Celestial) are original, non-cliche, and not reduced to abstract sci-fi noise.
8. Gear object occupancy is slot-fit ready (not a tiny center icon with oversized empty margins).
9. Contact edge/orientation reads correctly for the intended body slot.

For every theme:

1. Hero base communicates unique identity at first glance.
2. All 8 slots have rarity progression across 6 tiers.
3. Animation-ready grouping is present in source files.
4. Optional tier FX overlays exist for `epic`, `legendary`, and `celestial`.
5. Eye groups and eyelid logic are authored for saccades + fast blink behavior.
