# LLM Master Prompt For Hero SVG Generation

You are generating production-ready SVG assets for PersonalFreedom hero rendering.

Read these contracts first:
1. `HERO_SVG_SYSTEM_SPEC.md`
2. `HERO_SVG_VISUAL_BIBLE.md`
3. `hero_svg_handoff/<theme>_svg_packet.md` for your assigned theme

Rules:
1. Follow all file paths exactly as listed in the packet.
2. Use `viewBox="0 0 180 220"` for every hero layer SVG.
3. Keep transparent backgrounds.
4. Rarity progression must change silhouette and structure, not only colors.
5. Deliver required files first, then optional item-type files.
6. Keep first frame static-compatible (QSvgRenderer path).
7. Ensure each slot respects role and animation cue notes from the packet.

After generation:
1. Run `python validate_hero_svg_assets.py --theme <theme> --show-missing`.
2. Iterate until required completion reaches 100%.
