# Hero SVG Generation Execution Guide

Status: actionable handoff for external SVG-generation agents  
Last updated: 2026-02-14

## 1. Current System Status

Hero/themed/rarity gear SVG runtime is implemented and integrated.  
Procedural hero rendering remains fallback when SVG files are missing.

Validation status (current workspace):
- All 9 themes have manifest + directory scaffolding.
- Required SVG coverage is currently `0 / 52` per theme.
- This means code path is ready; asset production is the remaining blocking work.

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

## 5. Recommended Delivery Flow (Per Theme)

1. Generate all 52 required files first.
2. Run validator:
```powershell
python validate_hero_svg_assets.py --theme <theme_id> --show-missing
```
3. Fix all missing/invalid files until required completion reaches 100%.
4. Only then generate optional item-type variants listed in packet.

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

