# Hero SVG Generation Execution Guide

Status: actionable handoff for external SVG-generation agents  
Last updated: 2026-02-14

## 1. Current System Status

Hero/themed/rarity gear SVG runtime is implemented and integrated.  
Procedural hero rendering remains fallback when SVG files are missing.

Validation status (current workspace):
- All 9 themes have manifest + directory scaffolding.
- Required SVG coverage is currently `52 / 52` per theme as placeholder content.
- Primary task is replacing placeholder art with production SVG content in-place.

Use:
```powershell
python validate_hero_svg_assets.py --json
```

## 2. Canonical Contracts

Read in this order:
1. `HERO_SVG_SYSTEM_SPEC.md`
2. `HERO_SVG_VISUAL_BIBLE.md`
3. `hero_svg_handoff/<theme>_svg_packet.md`

If documents conflict, priority is exactly the order above.

## 3. Required Output Per Theme

Minimum production pack per theme:
- `hero_base.svg` (1)
- Slot fallback gear: 8 slots x 6 rarities = 48 files
- Tier FX overlays: `tier_epic.svg`, `tier_legendary.svg`, `tier_celestial.svg` (3)

Total required files per theme: `52`.

Semantic rule:
- Canonical slot names are technical compatibility keys.
- Story-facing gear meaning must follow each theme's `slot_display` and `item_types`.
- Do not treat non-warrior themes as literal helmet/chestplate armor sets.
- Do not substitute cross-genre defaults (for example generic fantasy rogue gear for `thief`).

Rarities (must exist in naming and design progression):
- `common`
- `uncommon`
- `rare`
- `epic`
- `legendary`
- `celestial`

## 4. Non-Negotiable Technical Rules

1. Keep file paths and names exactly as listed in each theme packet.
2. Use `viewBox="0 0 180 220"` for all hero/gear/fx SVGs.
3. Transparent background only.
4. Rarity progression must change silhouette/form, not only color.
5. Keep assets static-compatible (first-frame readable for `QSvgRenderer`).
6. Do not change manifest schema or runtime lookup rules.
7. Keep designs likable/relatable/cute/witty; avoid over-abstract sci-fi noise.
8. Epic/Legendary/Celestial should be original and non-cliche, with surprising but coherent tier upgrades.
9. Hero eyes should support saccadic motion + fast blink behavior.
10. Add minimal movement cues where applicable; keep motion subtle and readable.
11. Use gradient grading with consistent light direction to reinforce depth, overlap hierarchy, and perspective.
12. TAXONOMY LOCK: slot concepts must match the exact `item_types` vocabulary in the theme packet.
13. SLOT-FIT LOCK: gear assets must be authored as body-fit objects with tight bounds and approximately 70%-92% occupancy of canvas.
14. Reject tiny-center-icon composition and oversized transparent margins; slot orientation must match body-contact intent.

## 5. Recommended Delivery Flow (Per Theme)

1. Complete a preflight readback:
   - list 8 semantic slot labels (`slot_display`) for theme
   - list full `item_types` entries per slot for theme
   - confirm canonical slots are technical keys
   - confirm required file count is 52
   - confirm slot-fit authoring intent (body-fit composition, no tiny centered icon assets)
2. Generate/replace all 52 required files first.
3. Run validator:
```powershell
python validate_hero_svg_assets.py --theme <theme_id> --show-missing
```
4. Fix all missing/invalid files until required completion reaches 100%.
5. Only then generate optional item-type variants listed in packet.

## 6. QA Gate

A theme is handoff-complete when all are true:
1. Validator shows no missing required files for that theme.
2. `hero_base.svg` renders cleanly and has consistent silhouette.
3. All 8 slots have 6 rarity variants with visible structural progression.
4. `tier_epic.svg`, `tier_legendary.svg`, `tier_celestial.svg` exist.
5. No path/name deviations from packet.

## 7. Batch Completion Commands

Check all themes:
```powershell
python validate_hero_svg_assets.py --show-missing
```

Machine-readable report:
```powershell
python validate_hero_svg_assets.py --json
```
