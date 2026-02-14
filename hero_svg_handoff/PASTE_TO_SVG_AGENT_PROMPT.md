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

Rules:
1. Follow file names and paths exactly from the packet.
2. Generate required files first (52 total), optional item-type files second.
3. Use `viewBox="0 0 180 220"` on every generated SVG.
4. Transparent background only.
5. Rarity progression must change silhouette/structure (not just recolor).
6. Keep output static-compatible with `QSvgRenderer`.
7. Do not modify runtime Python code or manifest contracts.
8. Do not invent alternate naming conventions.

Required per theme:
- `icons/heroes/<THEME_ID>/hero_base.svg`
- `icons/heroes/<THEME_ID>/gear/<slot>/<slot>_<rarity>.svg` for all 8 slots x 6 rarities
- `icons/heroes/<THEME_ID>/fx/tier_epic.svg`
- `icons/heroes/<THEME_ID>/fx/tier_legendary.svg`
- `icons/heroes/<THEME_ID>/fx/tier_celestial.svg`

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

