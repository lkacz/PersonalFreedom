#!/usr/bin/env python3
"""Render hero base + selected gear overlays at 3x for visual inspection."""
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

theme = sys.argv[1] if len(sys.argv) > 1 else "warrior"
rarity = sys.argv[2] if len(sys.argv) > 2 else "common"
out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(f"artifacts/hero_previews/{theme}_{rarity}_compose.png")

app = QApplication([])
root = Path("icons/heroes") / theme
W, H, S = 180, 220, 3

img = QtGui.QImage(W * S, H * S, QtGui.QImage.Format_ARGB32)
img.fill(QtGui.QColor("#10141c"))
painter = QtGui.QPainter(img)
painter.setRenderHint(QtGui.QPainter.Antialiasing)
rect = QtCore.QRectF(0, 0, W * S, H * S)

layers = [root / "hero_base.svg"]
for slot in ["cloak", "chestplate", "boots", "gauntlets", "amulet", "helmet", "shield", "weapon"]:
    layers.insert(1 if slot == "cloak" else len(layers), root / "gear" / slot / f"{slot}_{rarity}.svg")

for layer in layers:
    if layer.exists():
        r = QSvgRenderer(str(layer))
        r.render(painter, rect)
    else:
        print(f"missing: {layer}")

painter.end()
out.parent.mkdir(parents=True, exist_ok=True)
img.save(str(out))
print(out)
