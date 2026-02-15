#!/usr/bin/env python3
"""Validate hero SVG packs for one or all themes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gamification import AVAILABLE_STORIES
from hero_svg_system import validate_hero_svg_theme_pack


RARITIES = ["common", "uncommon", "rare", "epic", "legendary", "celestial"]
SLOT_SLUGS = {
    "Cloak": "cloak",
    "Chestplate": "chestplate",
    "Boots": "boots",
    "Gauntlets": "gauntlets",
    "Amulet": "amulet",
    "Helmet": "helmet",
    "Shield": "shield",
    "Weapon": "weapon",
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate hero SVG asset packs.")
    parser.add_argument(
        "--theme",
        dest="theme",
        default=None,
        help="Validate only one theme id (example: robot).",
    )
    parser.add_argument(
        "--base-dir",
        dest="base_dir",
        default=None,
        help="Override app base directory (for CI/temp packs).",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Emit JSON output only.",
    )
    parser.add_argument(
        "--show-missing",
        dest="show_missing",
        action="store_true",
        help="Print all missing required files.",
    )
    return parser


def _required_files_for_theme(theme_id: str) -> list[str]:
    files = [f"icons/heroes/{theme_id}/hero_base.svg"]
    for slot_slug in SLOT_SLUGS.values():
        for rarity in RARITIES:
            files.append(f"icons/heroes/{theme_id}/gear/{slot_slug}/{slot_slug}_{rarity}.svg")
    files.append(f"icons/heroes/{theme_id}/fx/tier_epic.svg")
    files.append(f"icons/heroes/{theme_id}/fx/tier_legendary.svg")
    files.append(f"icons/heroes/{theme_id}/fx/tier_celestial.svg")
    return files


def _apply_completion_stats(report: dict) -> dict:
    theme_id = report["theme_id"]
    required_files = _required_files_for_theme(theme_id)
    required_existing = []
    required_missing = []
    for rel in required_files:
        if Path(rel).exists():
            required_existing.append(rel)
        else:
            required_missing.append(rel)

    total = len(required_files)
    present = len(required_existing)
    report["required_count"] = total
    report["required_present"] = present
    report["required_missing_count"] = len(required_missing)
    report["completion_pct"] = round((present / total) * 100.0, 2) if total else 0.0
    report["required_missing"] = required_missing
    report["required_existing"] = required_existing
    return report


def _apply_semantic_slot_stats(report: dict) -> dict:
    required_slots = list(SLOT_SLUGS.keys())
    manifest_path = Path(report.get("manifest_path", ""))
    slot_display = {}
    semantic_contract = None

    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            gear_payload = payload.get("gear", {}) if isinstance(payload, dict) else {}
            if isinstance(gear_payload, dict):
                slot_display = gear_payload.get("slot_display", {}) or {}
                semantic_contract = gear_payload.get("semantic_contract")
        except Exception:
            slot_display = {}
            semantic_contract = None

    present_slots = []
    missing_slots = []
    resolved_labels = {}
    for slot in required_slots:
        label = slot_display.get(slot) if isinstance(slot_display, dict) else None
        if isinstance(label, str) and label.strip():
            present_slots.append(slot)
            resolved_labels[slot] = label.strip()
        else:
            missing_slots.append(slot)

    report["slot_display_labels"] = resolved_labels
    report["slot_display_present_count"] = len(present_slots)
    report["slot_display_missing"] = missing_slots
    report["slot_display_complete"] = not missing_slots
    report["semantic_contract_present"] = isinstance(semantic_contract, str) and bool(semantic_contract.strip())
    return report


def _collect_reports(theme: str | None, base_dir: Path | None) -> list[dict]:
    themes = [theme] if theme else list(AVAILABLE_STORIES.keys())
    reports = [validate_hero_svg_theme_pack(story_theme=t, base_dir=base_dir) for t in themes]
    normalized = [_apply_completion_stats(report) for report in reports]
    return [_apply_semantic_slot_stats(report) for report in normalized]


def main() -> int:
    args = _build_parser().parse_args()
    base_dir = Path(args.base_dir) if args.base_dir else None
    reports = _collect_reports(args.theme, base_dir)

    if args.as_json:
        print(json.dumps(reports, indent=2))
        return 0

    for report in reports:
        ready = "READY" if report["is_ready"] else "MISSING_BASE"
        print(f"[{ready}] {report['theme_id']} :: {report['theme_dir']}")
        if not report["base_exists"]:
            print("  - missing base hero SVG")
        populated_slots = {
            slot: files for slot, files in report["slot_candidates"].items() if files
        }
        if populated_slots:
            for slot, files in populated_slots.items():
                print(f"  - {slot}: {len(files)} files")
        else:
            print("  - no gear SVG files found")
        print(
            f"  - required completion: {report['required_present']}/{report['required_count']} "
            f"({report['completion_pct']}%)"
        )
        print(
            f"  - semantic slot labels: {report['slot_display_present_count']}/{len(SLOT_SLUGS)} "
            f"(complete={report['slot_display_complete']})"
        )
        if args.show_missing and report["required_missing"]:
            for rel in report["required_missing"]:
                print(f"    * missing: {rel}")
        if args.show_missing and report["slot_display_missing"]:
            for slot in report["slot_display_missing"]:
                print(f"    * missing slot_display label: {slot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
