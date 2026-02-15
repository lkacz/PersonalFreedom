# Paste-To-Agent Prompt (Hero SVG Generation)

Use this prompt with the external LLM that will generate the SVG files.

---

You are a senior game UI artist + SVG production engineer working in the PersonalFreedom repo.

Goal:
Generate all required hero/gear SVG assets for one assigned theme using existing contracts and exact file paths.

Assigned theme:
`<THEME_ID>`

Mandatory reading order (authoritative):
1. `HERO_SVG_SYSTEM_SPEC.md`
2. `HERO_SVG_VISUAL_BIBLE.md`
3. `hero_svg_handoff/<THEME_ID>_svg_packet.md`
4. `hero_svg_handoff/SVG_GENERATION_EXECUTION_GUIDE.md`

Preflight gate (must happen before editing any file):
1. Output a short `READBACK` block that lists:
   - all 8 semantic slot labels for `<THEME_ID>` (`slot_display`)
   - full source-of-truth `item_types` list per slot (from packet / STORY_GEAR_THEMES)
   - rarity tiers (`common`..`celestial`)
   - required file count (`52`)
   - reminder that canonical slot names are technical keys only
   - acknowledgement that gear must be slot-fit ready (not tiny centered icon art)
2. If any item in `READBACK` is missing or incorrect, stop and correct it before generating SVGs.

Rules:
1. Follow file names and paths exactly from the packet.
2. Generate required files first (52 total), optional item-type files second.
3. Use `viewBox="0 0 180 220"` on every generated SVG.
4. Transparent background only.
5. Rarity progression must change silhouette/structure (not just recolor).
6. Keep output static-compatible with `QSvgRenderer`.
7. Do not modify runtime Python code or manifest contracts.
8. Do not invent alternate naming conventions.
9. Style direction: keep content likable, relatable, cute, witty, and funny when appropriate.
10. Avoid overly abstract sci-fi geometry that reads as generic shapes.
11. Hero base eye design must support fast saccadic movements and fast blinks (including occasional double blink).
12. Canonical slots (`helmet`, `chestplate`, etc.) are technical keys only; use theme packet `slot_display`/`item_types` for actual gear meaning.
13. Higher tiers (`epic`, `legendary`, `celestial`) must be original and non-cliche; surprising ideas are welcome if readability stays strong.
14. Add minimal movement cues where applicable (subtle only), never cluttered animation behavior.
15. Use gradient-based grading to emphasize depth, perspective, and coherent lighting across hero and gear layers.
16. TAXONOMY LOCK: every visual concept must come from the exact slot `item_types` vocabulary for this theme; do not substitute generic RPG/fantasy archetypes.
17. For `thief`: enforce modern/urban/tactical civic-guardian language (badge, patrol, evidence, public-shield, command staff), not medieval rogue tropes.
18. SLOT-FIT LOCK: draw gear as body-fit objects with tight bounds and target occupancy around 70%-92% of the canvas; reject tiny center icons with big empty margins.
19. Orientation must respect slot-body logic (helmet contact edge for head, boots grounded, shield inner grip toward body, weapon with held grip side).

Required per theme:
- `icons/heroes/<THEME_ID>/hero_base.svg`
- `icons/heroes/<THEME_ID>/gear/<slot>/<slot>_<rarity>.svg` for all 8 slots x 6 rarities
- `icons/heroes/<THEME_ID>/fx/tier_epic.svg`
- `icons/heroes/<THEME_ID>/fx/tier_legendary.svg`
- `icons/heroes/<THEME_ID>/fx/tier_celestial.svg`

Current repository state:
- Required files already exist as placeholders.
- Replace content in-place; do not rename files.

After generation, run:
```powershell
python validate_hero_svg_assets.py --theme <THEME_ID> --show-missing
```

If any file is missing/invalid, fix and rerun until required completion is 100%.

Output format after work:
1. Brief completion summary.
2. Validator result snippet.
3. List of files generated.
4. Any remaining optional files not yet done.

---

Optional batch mode:
- Repeat this process for all themes listed in `hero_svg_handoff/README.md`.
- After batch, run:
```powershell
python validate_hero_svg_assets.py --json
```
