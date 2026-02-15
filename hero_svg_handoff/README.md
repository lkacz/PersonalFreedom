# Hero SVG Handoff Pack

This folder contains detailed packets for another LLM to generate hero and gear SVG assets.
Primary contracts:
- `HERO_SVG_SYSTEM_SPEC.md`
- `HERO_SVG_VISUAL_BIBLE.md`

## Packets
- `warrior_svg_packet.md`
- `scholar_svg_packet.md`
- `wanderer_svg_packet.md`
- `underdog_svg_packet.md`
- `scientist_svg_packet.md`
- `robot_svg_packet.md`
- `space_pirate_svg_packet.md`
- `thief_svg_packet.md`
- `zoo_worker_svg_packet.md`

## How To Use
1. Open the packet for the target theme.
2. Feed the packet to the SVG-generation LLM.
3. Generate required files first, then optional item-type files.
4. Run `python validate_hero_svg_assets.py` to track completion.