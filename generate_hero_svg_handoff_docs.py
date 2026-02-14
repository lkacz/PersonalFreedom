#!/usr/bin/env python3
"""
Generate hero SVG handoff artifacts:
1) Theme scaffold manifests under icons/heroes/<theme>/
2) Machine-readable asset plan JSON
3) Detailed per-theme LLM packets for SVG production

Run:
    python generate_hero_svg_handoff_docs.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

from gamification import AVAILABLE_STORIES, STORY_GEAR_THEMES


ROOT = Path(__file__).resolve().parent
HANDOFF_DIR = ROOT / "hero_svg_handoff"
HERO_ROOT = ROOT / "icons" / "heroes"

RARITIES = ["common", "uncommon", "rare", "epic", "legendary", "celestial"]
SLOT_SLUGS = {
    "Helmet": "helmet",
    "Chestplate": "chestplate",
    "Gauntlets": "gauntlets",
    "Boots": "boots",
    "Shield": "shield",
    "Weapon": "weapon",
    "Cloak": "cloak",
    "Amulet": "amulet",
}

SLOT_ORDER = ["Cloak", "Chestplate", "Boots", "Gauntlets", "Amulet", "Helmet", "Shield", "Weapon"]


def slugify(value: str) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def clean_display_title(value: str | None, fallback: str) -> str:
    text = (value or "").strip()
    if not text:
        return fallback
    # Drop leading emoji/mojibake/punctuation markers from display titles.
    text = re.sub(r"^[^A-Za-z0-9]+", "", text)
    ascii_text = text.encode("ascii", errors="ignore").decode("ascii").strip()
    ascii_text = re.sub(r"\s+", " ", ascii_text)
    return ascii_text or fallback


THEME_BRIEFS = {
    "warrior": {
        "style": "Disciplined frontline fighter. Heavy silhouettes, engraved metal, leather utility.",
        "palette": ["#6f7f8f", "#3a434d", "#8d6e63", "#c98a3a", "#ffb74d"],
        "hero_base": "Broad-shoulder combat stance, grounded feet, readable helmet/head profile.",
        "motifs": ["dragon sigils", "battle scars", "banner trims", "forged rivets"],
    },
    "scholar": {
        "style": "Academic tactician. Tailored layers, codex-inspired geometry, careful symmetry.",
        "palette": ["#1f2d4a", "#4f5d7a", "#8d6e63", "#c7b299", "#d9c27a"],
        "hero_base": "Upright posture, robe/coat silhouette, visual focus on head and chest insignia.",
        "motifs": ["glyph lines", "book clasps", "ink channels", "seal medallions"],
    },
    "wanderer": {
        "style": "Mystic traveler. Flowing cloth, celestial cuts, curved asymmetric accents.",
        "palette": ["#25305a", "#443a7a", "#6f67a8", "#87d1e6", "#c3b2e6"],
        "hero_base": "Floating or soft-bent stance, long cloth read, moon-star focal ornament.",
        "motifs": ["constellations", "crescent forms", "veil layers", "astral rings"],
    },
    "underdog": {
        "style": "Urban comeback hero. Practical streetwear into tactical civic gear.",
        "palette": ["#2f3b4a", "#4f6a8a", "#708ca6", "#d97706", "#cbd5e1"],
        "hero_base": "Compact ready stance, relatable silhouette, clear jacket/hood shape.",
        "motifs": ["utility straps", "city marks", "badge clips", "rugged seams"],
    },
    "scientist": {
        "style": "Modern research defender. Clean lab forms merged with precision tech.",
        "palette": ["#dbe5ef", "#9fb8cf", "#5a7289", "#f59e0b", "#36c2d9"],
        "hero_base": "Lab-coat identity, precision visor profile, instrument-ready hands.",
        "motifs": ["measurement ticks", "containment panels", "reactor cores", "helix hints"],
    },
    "robot": {
        "style": "Factory-origin machine becoming autonomous. Industrial planes with luminous core.",
        "palette": ["#263238", "#4a6375", "#7ea3bd", "#ff8a3d", "#36d6e7"],
        "hero_base": "Readable mech torso, expressive optic zone, sturdy lower chassis.",
        "motifs": ["servo joints", "weld seams", "vent lines", "core rings"],
    },
    "space_pirate": {
        "style": "Orbital rogue captain. Nautical-pirate cues fused with vacuum-era hardware.",
        "palette": ["#1f2a44", "#3e4f74", "#6c7aa1", "#ff9f43", "#79d3f2"],
        "hero_base": "Captain-forward silhouette, coat-tail or mantle shape, swagger posture.",
        "motifs": ["star charts", "hull bolts", "ion trims", "contraband seals"],
    },
    "thief": {
        "style": "Redeemed infiltrator to civic guardian. Covert lines with lawful insignia.",
        "palette": ["#223046", "#3d5572", "#6b7f95", "#f87171", "#d4dce6"],
        "hero_base": "Lean pursuit silhouette, coat profile, disciplined tactical stance.",
        "motifs": ["badge geometry", "evidence lines", "signal lights", "restraint hardware"],
    },
    "zoo_worker": {
        "style": "Grounded caretaker with mythic destiny. Field utility plus ancient dragon echoes.",
        "palette": ["#314534", "#5f7e5d", "#8da18b", "#d6a55a", "#f0d7a6"],
        "hero_base": "Keeper-ready posture, hat/visor readability, warm practical silhouette.",
        "motifs": ["feather sigils", "sanctuary emblems", "storm straps", "ember accents"],
    },
}


SLOT_GUIDANCE = {
    "Helmet": "Head identity piece. Prioritize profile readability and theme signature crest.",
    "Chestplate": "Main mass-defining body layer. Largest storytelling surface after base hero.",
    "Gauntlets": "Functional hand/tool interface. Show dexterity and role-specific mechanics.",
    "Boots": "Movement identity. Encode terrain, mobility mode, and weight class.",
    "Shield": "Defensive philosophy. Make silhouette distinct from chestplate/weapon.",
    "Weapon": "Primary action silhouette. Highest visual contrast and directional energy.",
    "Cloak": "Motion layer. Build depth and emotional tone through shape and edge cuts.",
    "Amulet": "Narrative core token. Small but high-contrast and symbolically loaded.",
}


RARITY_GUIDANCE = {
    "common": "Simple practical geometry, minimal ornament, stable materials.",
    "uncommon": "Add one structural upgrade (trim, plate, attachment, or secondary contour).",
    "rare": "Introduce silhouette mutation (fins, flare, asymmetry, segmented layer).",
    "epic": "Add signature motif + emissive channels; complexity should be clearly higher.",
    "legendary": "Transform form language into ceremonial/mythic version with unique outline.",
    "celestial": "Break silhouette boundaries with transcendent motifs, layered aura geometry, and unmistakable apex identity.",
}


ANIMATION_BY_SLOT = {
    "Helmet": "Visor sweep or indicator blink every 2-4s.",
    "Chestplate": "Core pulse or panel breathing loop (slow, 3-5s).",
    "Gauntlets": "Knuckle light wave or servo twitch loop (subtle).",
    "Boots": "Sole glow ripple or dust/spark kick pulse.",
    "Shield": "Border scan sweep or shield-ripple pulse.",
    "Weapon": "Edge glint sweep or energy charge loop.",
    "Cloak": "Low-frequency sway with occasional gust accent.",
    "Amulet": "Heartbeat glow pulse with small orbiting mote.",
}


def ensure_theme_scaffold(story_id: str) -> dict:
    theme_dir = HERO_ROOT / story_id
    theme_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = theme_dir / "hero_manifest.json"
    manifest = {
        "version": 1,
        "theme_id": story_id,
        "canvas": {"width": 180, "height": 220},
        "base": {
            "file": "hero_base.svg",
            "fallback_files": ["hero_base.svg", "hero.svg", "base.svg"],
        },
        "gear": {
            "slot_order": SLOT_ORDER,
            "patterns": [
                "gear/{slot}/{item_type}_{rarity}.svg",
                "gear/{slot}/{item_name}_{rarity}.svg",
                "gear/{slot}/{item_type}.svg",
                "gear/{slot}/{slot}_{rarity}.svg",
                "gear/{slot}/{rarity}.svg",
                "gear/{slot}/{slot}.svg",
            ],
        },
        "fx": {"tier_pattern": "fx/tier_{power_tier}.svg"},
        "animation": {
            "notes": "Static-compatible first frame required. Motion-ready group structure encouraged."
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Track folder intent in git before actual SVG production.
    for slot_slug in SLOT_SLUGS.values():
        slot_dir = theme_dir / "gear" / slot_slug
        slot_dir.mkdir(parents=True, exist_ok=True)
        gitkeep = slot_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")

    fx_dir = theme_dir / "fx"
    fx_dir.mkdir(parents=True, exist_ok=True)
    fx_gitkeep = fx_dir / ".gitkeep"
    if not fx_gitkeep.exists():
        fx_gitkeep.write_text("", encoding="utf-8")

    return manifest


def build_required_files(story_id: str) -> List[str]:
    files = [f"icons/heroes/{story_id}/hero_base.svg"]
    for slot in SLOT_ORDER:
        slot_slug = SLOT_SLUGS[slot]
        for rarity in RARITIES:
            files.append(f"icons/heroes/{story_id}/gear/{slot_slug}/{slot_slug}_{rarity}.svg")
    files.extend(
        [
            f"icons/heroes/{story_id}/fx/tier_epic.svg",
            f"icons/heroes/{story_id}/fx/tier_legendary.svg",
            f"icons/heroes/{story_id}/fx/tier_celestial.svg",
        ]
    )
    return files


def build_optional_item_files(story_id: str) -> List[str]:
    theme = STORY_GEAR_THEMES[story_id]
    files: List[str] = []
    for slot, item_types in theme.get("item_types", {}).items():
        slot_slug = SLOT_SLUGS.get(slot)
        if not slot_slug:
            continue
        for item_type in item_types:
            item_slug = slugify(item_type)
            for rarity in RARITIES:
                files.append(
                    f"icons/heroes/{story_id}/gear/{slot_slug}/{item_slug}_{rarity}.svg"
                )
    return files


def build_theme_packet(story_id: str) -> str:
    story = AVAILABLE_STORIES[story_id]
    brief = THEME_BRIEFS[story_id]
    theme = STORY_GEAR_THEMES[story_id]
    display_title = clean_display_title(
        story.get("title"),
        story_id.replace("_", " ").title(),
    )

    required_files = build_required_files(story_id)
    optional_files = build_optional_item_files(story_id)

    lines: List[str] = []
    lines.append(f"# {story_id} Hero SVG Packet")
    lines.append("")
    lines.append("## Theme Snapshot")
    lines.append(f"- story_id: `{story_id}`")
    lines.append(f"- title: {display_title}")
    lines.append(f"- style intent: {brief['style']}")
    lines.append(f"- hero base direction: {brief['hero_base']}")
    lines.append(
        f"- motif keywords: {', '.join(brief['motifs'])}"
    )
    lines.append(
        f"- palette anchors: {', '.join(brief['palette'])}"
    )
    lines.append("")
    lines.append("## Mandatory Output Files")
    lines.append("Generate all files below.")
    for file_path in required_files:
        lines.append(f"- `{file_path}`")
    lines.append("")
    lines.append("## Preferred Item-Type Output Files")
    lines.append("Generate these for full visual variety. If constrained, prioritize Helmet, Chestplate, Weapon, Shield.")
    for file_path in optional_files:
        lines.append(f"- `{file_path}`")
    lines.append("")
    lines.append("## Slot-by-Slot Direction")
    for slot in SLOT_ORDER:
        lines.append(f"### {slot}")
        lines.append(f"- role: {SLOT_GUIDANCE[slot]}")
        lines.append(f"- animation cue: {ANIMATION_BY_SLOT[slot]}")
        item_types = theme.get("item_types", {}).get(slot, [])
        lines.append(f"- item types to represent: {', '.join(item_types)}")
        lines.append("- rarity progression:")
        for rarity in RARITIES:
            lines.append(f"  - {rarity}: {RARITY_GUIDANCE[rarity]}")
    lines.append("")
    lines.append("## Global Quality Gates")
    lines.append("- Do not use only color swaps across rarities; geometry and silhouette must evolve.")
    lines.append("- Keep readability at 70x90 and 180x220.")
    lines.append("- Keep transparent backgrounds.")
    lines.append("- Ensure first frame is static-compatible (for QSvgRenderer path).")
    lines.append("- Keep layering aligned with hero base center and foot line.")
    lines.append("")
    lines.append("## LLM Generation Prompt")
    lines.append("Use this with your SVG-generation model:")
    lines.append("")
    lines.append("```text")
    lines.append("You are generating production SVG assets for PersonalFreedom hero rendering.")
    lines.append(f"Theme: {story_id}")
    lines.append("Follow file names exactly as listed in this packet.")
    lines.append("Canvas/viewBox: 0 0 180 220. Transparent background.")
    lines.append("For each rarity tier, change silhouette/design complexity, not only colors.")
    lines.append("Respect slot role and animation cues in this packet.")
    lines.append("Output valid standalone SVG files only.")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def generate_handoff_docs() -> None:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    HERO_ROOT.mkdir(parents=True, exist_ok=True)

    summary_lines = [
        "# Hero SVG Handoff Pack",
        "",
        "This folder contains detailed packets for another LLM to generate hero and gear SVG assets.",
        "Primary contracts:",
        "- `HERO_SVG_SYSTEM_SPEC.md`",
        "- `HERO_SVG_VISUAL_BIBLE.md`",
        "",
        "## Packets",
    ]

    plan = {"themes": {}}

    for story_id in AVAILABLE_STORIES.keys():
        ensure_theme_scaffold(story_id)
        packet_text = build_theme_packet(story_id)
        packet_path = HANDOFF_DIR / f"{story_id}_svg_packet.md"
        packet_path.write_text(packet_text, encoding="utf-8")

        required_files = build_required_files(story_id)
        optional_files = build_optional_item_files(story_id)
        plan["themes"][story_id] = {
            "required_files": required_files,
            "optional_item_files": optional_files,
            "required_count": len(required_files),
            "optional_count": len(optional_files),
        }
        summary_lines.append(f"- `{packet_path.name}`")

    summary_lines.extend(
        [
            "",
            "## How To Use",
            "1. Open the packet for the target theme.",
            "2. Feed the packet to the SVG-generation LLM.",
            "3. Generate required files first, then optional item-type files.",
            "4. Run `python validate_hero_svg_assets.py` to track completion.",
        ]
    )

    (HANDOFF_DIR / "README.md").write_text("\n".join(summary_lines), encoding="utf-8")
    (HANDOFF_DIR / "hero_svg_asset_plan.json").write_text(
        json.dumps(plan, indent=2), encoding="utf-8"
    )

    count_lines = [
        "# Hero SVG Asset Counts",
        "",
        "| Theme | Required Files | Optional Item-Type Files |",
        "|---|---:|---:|",
    ]
    for story_id in AVAILABLE_STORIES.keys():
        entry = plan["themes"][story_id]
        count_lines.append(
            f"| `{story_id}` | {entry['required_count']} | {entry['optional_count']} |"
        )
    (HANDOFF_DIR / "ASSET_COUNTS.md").write_text("\n".join(count_lines), encoding="utf-8")

    master_prompt = """# LLM Master Prompt For Hero SVG Generation

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
"""
    (HANDOFF_DIR / "LLM_MASTER_PROMPT.md").write_text(master_prompt, encoding="utf-8")


if __name__ == "__main__":
    generate_handoff_docs()
    print("Generated hero SVG handoff docs and scaffolds.")
