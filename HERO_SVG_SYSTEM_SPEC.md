# Hero SVG System Specification (Authoritative)

Status: Canonical contract for SVG hero + gear rendering  
Last updated: 2026-02-14

## 1. Purpose

This document defines the runtime and asset contract for rendering heroes and equipped gear from SVG assets.

It is designed for safe migration:

1. SVG rendering is **opt-in by asset presence**.
2. Procedural painter rendering remains the fallback path.
3. Missing/invalid assets must never break hero rendering.

If this file conflicts with older hero art notes, this file wins.

## 2. Design Principles

1. Theme isolation: each `story_id` owns its own hero SVG pack.
2. Layered composition: hero is rendered from base + gear slot layers (+ optional FX).
3. Deterministic lookup: file resolution follows strict pattern order.
4. Backward compatibility: no asset -> no crash -> procedural fallback.
5. Performance-safe: `QSvgRenderer` is cached by file path + mtime.

## 3. Runtime Integration Points

Primary runtime file:

- `hero_svg_system.py`

Primary render caller:

- `focus_blocker_qt.py` (`CharacterCanvas.render_content`)

Behavior:

1. Try `render_hero_svg_character(...)`.
2. If it returns `True`, SVG output is used.
3. If it returns `False` or raises, existing theme-specific painter code renders as before.

## 4. Directory and File Contract

Root:

- `icons/heroes/<story_id>/`

Required:

- `hero_base.svg` (preferred)  
Fallback base names supported:
- `hero.svg`
- `base.svg`

Gear layers:

- `icons/heroes/<story_id>/gear/<slot_slug>/...`

Optional tier FX layer:

- `icons/heroes/<story_id>/fx/tier_<power_tier_slug>.svg`

Optional manifest:

- `icons/heroes/<story_id>/hero_manifest.json`

## 5. Slot and Rarity Normalization

Canonical slot keys:

- `Helmet`
- `Chestplate`
- `Gauntlets`
- `Boots`
- `Shield`
- `Weapon`
- `Cloak`
- `Amulet`

Slot slugs:

- `helmet`, `chestplate`, `gauntlets`, `boots`, `shield`, `weapon`, `cloak`, `amulet`

Rarity slugs:

- `common`, `uncommon`, `rare`, `epic`, `legendary`, `celestial`

## 6. Layer Resolution Rules

### 6.1 Base Layer

Resolution order:

1. `base.file` from manifest (default: `hero_base.svg`)
2. `base.fallback_files` from manifest (default: `hero_base.svg`, `hero.svg`, `base.svg`)

If no base layer exists, SVG path is treated as unavailable and procedural fallback is used.

### 6.2 Gear Layer

For each equipped slot, these patterns are attempted in order:

1. `gear/{slot}/{item_type}_{rarity}.svg`
2. `gear/{slot}/{item_name}_{rarity}.svg`
3. `gear/{slot}/{item_type}.svg`
4. `gear/{slot}/{slot}_{rarity}.svg`
5. `gear/{slot}/{rarity}.svg`
6. `gear/{slot}/{slot}.svg`

Token sources:

- `slot`: normalized slot slug
- `item_type`: slug from item `item_type`
- `item_name`: slug from item `name`
- `rarity`: normalized rarity slug

Missing slot layers are allowed; base still renders.

### 6.3 FX Layer

Optional tier FX layer is resolved from:

- `fx.tier_pattern` (default: `fx/tier_{power_tier}.svg`)

FX alias fallback (implemented):

1. `godlike` -> `celestial` -> `legendary` -> `epic`
2. `celestial` -> `legendary` -> `epic`
3. `legendary` -> `epic`

This keeps FX resilient when gameplay tier labels differ from asset tier labels.

### 6.4 Smart Layer Fit/Anchor (Implemented)

Rendering supports per-layer fit/anchor correction:

1. Canonical source layers (`viewBox ~= 180x220`) render full-canvas (legacy behavior).
2. Non-canonical gear source layers auto-fit into slot anchor boxes using contain-fit.
3. Manifest `layout` overrides can explicitly control fit/anchor/offset/scale/box.

Supported fit modes:

- `stretch` (fill target rect)
- `contain` (preserve aspect ratio inside target rect)
- `auto` (gear: smart slot fit for non-canonical source; otherwise stretch)

Supported anchors:

- `center`, `top`, `bottom`, `left`, `right`
- `top_left`, `top_center`, `top_right`
- `center_left`, `center_right`
- `bottom_left`, `bottom_center`, `bottom_right`

## 7. Manifest Schema

Path:

- `icons/heroes/<story_id>/hero_manifest.json`

Minimal example:

```json
{
  "version": 1,
  "theme_id": "robot",
  "canvas": { "width": 180, "height": 220 },
  "base": {
    "file": "hero_base.svg",
    "fallback_files": ["hero_base.svg", "hero.svg", "base.svg"]
  },
  "gear": {
    "slot_order": ["Cloak", "Chestplate", "Boots", "Gauntlets", "Amulet", "Helmet", "Shield", "Weapon"],
    "patterns": [
      "gear/{slot}/{item_type}_{rarity}.svg",
      "gear/{slot}/{item_name}_{rarity}.svg",
      "gear/{slot}/{item_type}.svg",
      "gear/{slot}/{slot}_{rarity}.svg",
      "gear/{slot}/{rarity}.svg",
      "gear/{slot}/{slot}.svg"
    ]
  },
  "fx": {
    "tier_pattern": "fx/tier_{power_tier}.svg"
  },
  "layout": {
    "base": { "fit": "stretch", "anchor": "center", "offset": [0.0, 0.0], "scale": [1.0, 1.0] },
    "gear": {
      "default": { "fit": "auto", "anchor": "center", "offset": [0.0, 0.0], "scale": [1.0, 1.0] },
      "slots": {
        "helmet": { "fit": "contain", "anchor": "top_center", "box": [0.28, 0.06, 0.44, 0.28] }
      }
    },
    "fx": { "fit": "stretch", "anchor": "center", "offset": [0.0, 0.0], "scale": [1.0, 1.0] }
  },
  "animation": {}
}
```

Notes:

1. Unknown keys are allowed for forward compatibility.
2. `animation` is metadata-only for now (see Section 10).
3. `offset` values are normalized to full hero canvas size (x,y).
4. `scale` may be single value or `[x, y]`.
5. `box` is normalized `[x, y, width, height]` in hero canvas space.
6. Omit manifest entirely to use defaults.

## 8. Rendering and Performance

Renderer:

- `QSvgRenderer` per layer.

Cache policy:

- Keyed by absolute file path.
- Auto-refresh when source `mtime` changes.

Failure policy:

1. Invalid base SVG -> fail SVG path -> procedural fallback.
2. Invalid gear SVG -> skip that layer only.
3. Exceptions must never crash hero UI.

## 9. Validation Tooling

Validation script:

- `validate_hero_svg_assets.py`

Examples:

```powershell
python validate_hero_svg_assets.py
python validate_hero_svg_assets.py --theme robot
python validate_hero_svg_assets.py --json
```

Expected use:

1. CI preflight for asset completeness.
2. Artist handoff verification before release.

## 10. Animation Contract

The runtime currently supports static layer composition and optional FX layers.

Animation guidance for asset generation:

1. Prefer subtle looped motion in SVG itself for future web-rendered contexts.
2. Keep static-compatible first frame for `QSvgRenderer` usage.
3. Author separate FX overlays for high tiers (`tier_epic`, `tier_legendary`, `tier_celestial`, `tier_godlike` if used).

Recommended future runtime extension (not required now):

1. Manifest-driven per-layer motion profile (`idle_bob`, `cloak_sway`, `weapon_glint`).
2. Optional `QWebEngineView` pipeline for full SVG animation.
3. Runtime toggle between static and animated render modes.

## 11. Migration Safety Plan

Phase 1 (implemented):

1. Add SVG subsystem with strict fallback.
2. Integrate `CharacterCanvas` with SVG-first attempt.
3. Keep all existing procedural theme painters untouched.

Phase 2 (asset rollout):

1. Create base hero SVG for each theme.
2. Create at least slot-level fallback gear SVGs (`{slot}_{rarity}`) for all 8 slots.
3. Add item-type-specific variants for visual richness.

Phase 3 (quality + polish):

1. Add tier FX overlays.
2. Add full item-type coverage across rarities.
3. Add optional animation metadata per theme.

## 12. Definition of Done (SVG Hero Pack)

A theme pack is considered production-ready when:

1. Base hero SVG exists and renders.
2. Each gear slot has rarity-aware SVG designs (not color-only swaps).
3. Epic and Legendary tiers include silhouette/detail upgrades.
4. Visual style matches theme bible requirements.
5. Validation script reports base present and expected slot files available.
6. Manual checks confirm Hero tab and mini-hero are stable.
