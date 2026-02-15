#!/usr/bin/env python3
"""Generate a hero composition fit matrix for a theme.

This renders:
- per-slot overlays across all rarities
- optional "ALL gear equipped" row

Usage:
  python tools/preview_hero_theme_fit.py --theme space_pirate
  python tools/preview_hero_theme_fit.py --theme zoo_worker --output artifacts/hero_previews/zoo_fit.png
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from PySide6 import QtGui, QtWidgets

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hero_svg_system import render_hero_svg_character


RARITIES = ["common", "uncommon", "rare", "epic", "legendary", "celestial"]
RARITY_COLORS = {
    "common": "#9E9E9E",
    "uncommon": "#4CAF50",
    "rare": "#2196F3",
    "epic": "#9C27B0",
    "legendary": "#FF9800",
    "celestial": "#00E5FF",
}
SLOTS = ["Helmet", "Chestplate", "Gauntlets", "Boots", "Shield", "Weapon", "Cloak", "Amulet"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Preview hero SVG fit matrix for a theme.")
    p.add_argument("--theme", required=True, help="Theme/story id (e.g. space_pirate)")
    p.add_argument(
        "--output",
        default=None,
        help="Output PNG path (default: artifacts/hero_previews/<theme>_fit_matrix.png)",
    )
    p.add_argument(
        "--no-all-row",
        action="store_true",
        help="Skip the ALL-gear row.",
    )
    return p.parse_args()


def build_output_path(theme: str, output: str | None) -> Path:
    if output:
        return Path(output)
    return Path("artifacts") / "hero_previews" / f"{theme}_fit_matrix.png"


def draw_checker(p: QtGui.QPainter, x: int, y: int, w: int, h: int, step: int = 16) -> None:
    for yy in range(y, y + h, step):
        for xx in range(x, x + w, step):
            dark = ((xx // step) + (yy // step)) % 2 == 0
            p.fillRect(xx, yy, step, step, QtGui.QColor("#1a2234" if dark else "#101726"))


def main() -> int:
    args = parse_args()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    rows = list(SLOTS)
    if not args.no_all_row:
        rows.append("ALL")

    card_w, card_h = 200, 240
    img = QtGui.QImage(card_w * len(RARITIES), card_h * len(rows), QtGui.QImage.Format_ARGB32)
    img.fill(QtGui.QColor("#061225"))

    p = QtGui.QPainter(img)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

    for row_i, slot in enumerate(rows):
        for col_i, rarity in enumerate(RARITIES):
            x = col_i * card_w
            y = row_i * card_h

            p.setPen(QtGui.QPen(QtGui.QColor(RARITY_COLORS[rarity]), 2))
            p.setBrush(QtGui.QColor("#071a36"))
            p.drawRoundedRect(x + 6, y + 6, card_w - 12, card_h - 12, 10, 10)

            bx, by, bw, bh = x + 18, y + 34, card_w - 36, card_h - 52
            draw_checker(p, bx, by, bw, bh)

            equipped = {}
            if slot == "ALL":
                for s in SLOTS:
                    equipped[s] = {"rarity": rarity}
            else:
                equipped[slot] = {"rarity": rarity}

            tier = rarity if rarity in {"epic", "legendary", "celestial"} else None

            p.save()
            p.translate(bx + (bw - 180) // 2, by + 2)
            render_hero_svg_character(
                painter=p,
                story_theme=args.theme,
                equipped=equipped,
                power_tier=tier,
                canvas_width=180,
                canvas_height=220,
            )
            p.restore()

            p.setPen(QtGui.QColor("#e6f0ff"))
            p.drawText(x + 12, y + 22, f"{slot.lower()} {rarity}")

    p.end()

    out = build_output_path(args.theme, args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    ok = img.save(str(out))
    if not ok:
        print(f"Failed to save preview: {out}")
        return 1

    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
