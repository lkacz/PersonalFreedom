#!/usr/bin/env python3
"""Interactive hero composition manager for SVG slot alignment.

This development tool lets you:
- choose a theme
- load base hero + one gear layer per slot
- drag slot layers to align against the base
- scale (Ctrl + wheel) and rotate (Shift + wheel) selected slot layers
- save/load per-slot, per-rarity transform profiles to JSON

The saved profile is intended as an empirical alignment reference that can be
used later to patch SVG source transforms or manifest layout overrides.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtSvgWidgets import QGraphicsSvgItem

ROOT = Path(__file__).resolve().parent.parent

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hero_svg_system import (  # noqa: E402
    HERO_CANVAS_HEIGHT,
    HERO_CANVAS_WIDTH,
    GEAR_SLOT_ORDER,
    load_hero_manifest,
    resolve_hero_base_layer,
    resolve_hero_gear_layer,
)


RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Celestial"]
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


@dataclass
class SlotTransform:
    offset_x: float = 0.0
    offset_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation_deg: float = 0.0
    visible: bool = True
    rarity: str = "Common"

    def clone(self, **overrides) -> "SlotTransform":
        data = asdict(self)
        data.update(overrides)
        return SlotTransform(**data)


class LayerItem(QGraphicsSvgItem):
    """Movable/selectable SVG layer bound to a slot."""

    def __init__(self, slot: str, svg_path: Path, owner: "CompositionManagerWindow") -> None:
        super().__init__(str(svg_path))
        self.slot = slot
        self._owner = owner
        self.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable
            | QtWidgets.QGraphicsItem.ItemIsSelectable
            | QtWidgets.QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            self._owner.on_slot_item_moved(self.slot)
        elif change == QtWidgets.QGraphicsItem.ItemSelectedHasChanged and bool(value):
            self._owner.on_scene_slot_selected(self.slot)
        return super().itemChange(change, value)


class CompositionView(QtWidgets.QGraphicsView):
    """Canvas view with interaction helpers."""

    def __init__(self, owner: "CompositionManagerWindow") -> None:
        super().__init__()
        self._owner = owner
        self._zoom = 1.0
        self.setRenderHints(
            QtGui.QPainter.Antialiasing
            | QtGui.QPainter.SmoothPixmapTransform
            | QtGui.QPainter.TextAntialiasing
        )
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setBackgroundBrush(QtGui.QColor("#0c1222"))

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        slot = self._owner.current_slot
        if slot:
            delta = event.angleDelta().y()
            mods = event.modifiers()
            if mods & QtCore.Qt.ControlModifier:
                factor = 1.03 if delta > 0 else 0.97
                self._owner.adjust_selected_scale(factor)
                event.accept()
                return
            if mods & QtCore.Qt.ShiftModifier:
                step = 2.0 if delta > 0 else -2.0
                self._owner.adjust_selected_rotation(step)
                event.accept()
                return

        # Default: zoom viewport
        factor = 1.08 if event.angleDelta().y() > 0 else 0.92
        self._zoom = max(0.35, min(7.0, self._zoom * factor))
        self.resetTransform()
        self.scale(self._zoom, self._zoom)
        event.accept()


class CompositionManagerWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Hero SVG Composition Manager")
        self.resize(1320, 860)

        self._syncing = False
        self.current_theme: Optional[str] = None
        self.current_slot: Optional[str] = None
        self.base_item: Optional[QGraphicsSvgItem] = None
        self.slot_items: Dict[str, Optional[LayerItem]] = {slot: None for slot in GEAR_SLOT_ORDER}
        self.slot_transforms: Dict[str, Dict[str, SlotTransform]] = self._new_slot_transform_map()
        self.slot_rarity_combos: Dict[str, QtWidgets.QComboBox] = {}
        self.slot_visibility_checks: Dict[str, QtWidgets.QCheckBox] = {}
        self.slot_select_buttons: Dict[str, QtWidgets.QPushButton] = {}

        self._build_ui()
        self._populate_themes()
        if self.theme_combo.count() > 0:
            self.theme_combo.setCurrentIndex(0)
            self.load_theme(self.theme_combo.currentText())

    def _new_slot_transform_map(self) -> Dict[str, Dict[str, SlotTransform]]:
        return {
            slot: {rarity: SlotTransform(rarity=rarity) for rarity in RARITIES}
            for slot in GEAR_SLOT_ORDER
        }

    def _active_rarity_for_slot(self, slot: str) -> str:
        combo = self.slot_rarity_combos.get(slot)
        rarity = combo.currentText() if combo else "Common"
        return rarity if rarity in RARITIES else "Common"

    def _active_cfg_for_slot(self, slot: str) -> SlotTransform:
        rarity = self._active_rarity_for_slot(slot)
        return self.slot_transforms[slot][rarity]

    def _build_ui(self) -> None:
        root = QtWidgets.QWidget()
        self.setCentralWidget(root)
        layout = QtWidgets.QHBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left = QtWidgets.QWidget()
        left.setMinimumWidth(430)
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setSpacing(10)

        header = QtWidgets.QLabel("Hero Composition Manager")
        header.setStyleSheet("font-size: 18px; font-weight: 700; color: #e3ecff;")
        left_layout.addWidget(header)

        hint = QtWidgets.QLabel(
            "Drag selected layer on canvas.\n"
            "Ctrl + wheel: scale | Shift + wheel: rotate | wheel: zoom canvas."
        )
        hint.setStyleSheet("color: #b8c4de;")
        left_layout.addWidget(hint)

        theme_row = QtWidgets.QHBoxLayout()
        theme_row.addWidget(QtWidgets.QLabel("Theme:"))
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.theme_combo, 1)
        reload_btn = QtWidgets.QPushButton("Reload")
        reload_btn.clicked.connect(lambda: self.load_theme(self.theme_combo.currentText()))
        theme_row.addWidget(reload_btn)
        left_layout.addLayout(theme_row)

        slots_group = QtWidgets.QGroupBox("Slots")
        slots_layout = QtWidgets.QGridLayout(slots_group)
        slots_layout.setHorizontalSpacing(8)
        slots_layout.setVerticalSpacing(5)
        slots_layout.addWidget(QtWidgets.QLabel("Slot"), 0, 0)
        slots_layout.addWidget(QtWidgets.QLabel("Show"), 0, 1)
        slots_layout.addWidget(QtWidgets.QLabel("Rarity"), 0, 2)
        slots_layout.addWidget(QtWidgets.QLabel("Select"), 0, 3)

        for row, slot in enumerate(GEAR_SLOT_ORDER, start=1):
            slot_lbl = QtWidgets.QLabel(slot)
            slot_lbl.setStyleSheet("color: #d7e2ff;")
            slots_layout.addWidget(slot_lbl, row, 0)

            vis = QtWidgets.QCheckBox()
            vis.setChecked(True)
            vis.stateChanged.connect(lambda _v, s=slot: self._on_slot_visible_changed(s))
            slots_layout.addWidget(vis, row, 1)
            self.slot_visibility_checks[slot] = vis

            rarity = QtWidgets.QComboBox()
            rarity.addItems(RARITIES)
            rarity.setCurrentText("Common")
            rarity.currentTextChanged.connect(lambda _t, s=slot: self._on_slot_rarity_changed(s))
            slots_layout.addWidget(rarity, row, 2)
            self.slot_rarity_combos[slot] = rarity

            sel = QtWidgets.QPushButton("Pick")
            sel.clicked.connect(lambda _c=False, s=slot: self.select_slot(s))
            slots_layout.addWidget(sel, row, 3)
            self.slot_select_buttons[slot] = sel

        left_layout.addWidget(slots_group)

        controls_group = QtWidgets.QGroupBox("Selected Slot Transform")
        form = QtWidgets.QFormLayout(controls_group)

        self.selected_slot_label = QtWidgets.QLabel("None")
        self.selected_slot_label.setStyleSheet("font-weight: 700; color: #e3ecff;")
        form.addRow("Slot:", self.selected_slot_label)

        self.offset_x_spin = QtWidgets.QDoubleSpinBox()
        self.offset_x_spin.setRange(-1.0, 1.0)
        self.offset_x_spin.setSingleStep(0.005)
        self.offset_x_spin.setDecimals(4)
        self.offset_x_spin.valueChanged.connect(self._on_transform_spin_changed)
        form.addRow("Offset X:", self.offset_x_spin)

        self.offset_y_spin = QtWidgets.QDoubleSpinBox()
        self.offset_y_spin.setRange(-1.0, 1.0)
        self.offset_y_spin.setSingleStep(0.005)
        self.offset_y_spin.setDecimals(4)
        self.offset_y_spin.valueChanged.connect(self._on_transform_spin_changed)
        form.addRow("Offset Y:", self.offset_y_spin)

        self.scale_x_spin = QtWidgets.QDoubleSpinBox()
        self.scale_x_spin.setRange(0.10, 5.0)
        self.scale_x_spin.setSingleStep(0.01)
        self.scale_x_spin.setDecimals(4)
        self.scale_x_spin.valueChanged.connect(self._on_transform_spin_changed)
        form.addRow("Scale X:", self.scale_x_spin)

        self.scale_y_spin = QtWidgets.QDoubleSpinBox()
        self.scale_y_spin.setRange(0.10, 5.0)
        self.scale_y_spin.setSingleStep(0.01)
        self.scale_y_spin.setDecimals(4)
        self.scale_y_spin.valueChanged.connect(self._on_transform_spin_changed)
        form.addRow("Scale Y:", self.scale_y_spin)

        self.rotation_spin = QtWidgets.QDoubleSpinBox()
        self.rotation_spin.setRange(-360.0, 360.0)
        self.rotation_spin.setSingleStep(1.0)
        self.rotation_spin.setDecimals(2)
        self.rotation_spin.valueChanged.connect(self._on_transform_spin_changed)
        form.addRow("Rotation (deg):", self.rotation_spin)

        btn_row = QtWidgets.QHBoxLayout()
        reset_slot_btn = QtWidgets.QPushButton("Reset Slot")
        reset_slot_btn.clicked.connect(self.reset_selected_slot)
        btn_row.addWidget(reset_slot_btn)
        reset_all_btn = QtWidgets.QPushButton("Reset All")
        reset_all_btn.clicked.connect(self.reset_all_slots)
        btn_row.addWidget(reset_all_btn)
        form.addRow(btn_row)

        left_layout.addWidget(controls_group)

        io_group = QtWidgets.QGroupBox("Profiles")
        io_layout = QtWidgets.QVBoxLayout(io_group)
        save_btn = QtWidgets.QPushButton("Save + Apply To App")
        save_btn.clicked.connect(self.save_profile)
        io_layout.addWidget(save_btn)
        load_btn = QtWidgets.QPushButton("Load Profile JSON")
        load_btn.clicked.connect(self.load_profile_dialog)
        io_layout.addWidget(load_btn)
        self.profile_path_label = QtWidgets.QLabel("")
        self.profile_path_label.setStyleSheet("color: #9fb0d6; font-size: 11px;")
        self.profile_path_label.setWordWrap(True)
        io_layout.addWidget(self.profile_path_label)
        left_layout.addWidget(io_group)

        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet("color: #b7f7c4; padding: 6px 0;")
        left_layout.addWidget(self.status)
        left_layout.addStretch()

        layout.addWidget(left, 0)

        self.scene = QtWidgets.QGraphicsScene(0, 0, HERO_CANVAS_WIDTH, HERO_CANVAS_HEIGHT, self)
        self._init_scene_background()

        self.view = CompositionView(self)
        self.view.setScene(self.scene)
        self.view.setSceneRect(-6, -6, HERO_CANVAS_WIDTH + 12, HERO_CANVAS_HEIGHT + 12)
        self.view.scale(2.75, 2.75)
        self.view._zoom = 2.75
        layout.addWidget(self.view, 1)

    def _init_scene_background(self) -> None:
        tile = QtGui.QPixmap(16, 16)
        p = QtGui.QPainter(tile)
        p.fillRect(0, 0, 16, 16, QtGui.QColor("#1c2434"))
        p.fillRect(0, 0, 8, 8, QtGui.QColor("#101726"))
        p.fillRect(8, 8, 8, 8, QtGui.QColor("#101726"))
        p.end()
        self.scene.setBackgroundBrush(QtGui.QBrush(tile))

        frame = self.scene.addRect(
            0,
            0,
            HERO_CANVAS_WIDTH,
            HERO_CANVAS_HEIGHT,
            QtGui.QPen(QtGui.QColor("#4d6aa8"), 1.0),
        )
        frame.setZValue(-50)

    def _populate_themes(self) -> None:
        heroes_root = ROOT / "icons" / "heroes"
        themes = []
        if heroes_root.exists():
            for p in sorted(heroes_root.iterdir()):
                if not p.is_dir():
                    continue
                if (p / "hero_manifest.json").exists() or (p / "hero_base.svg").exists():
                    themes.append(p.name)
        self.theme_combo.clear()
        self.theme_combo.addItems(themes)

    def _theme_profile_path(self, theme: str) -> Path:
        return ROOT / "artifacts" / "hero_composition" / f"{theme}_composition_profile.json"

    def _on_theme_changed(self, theme: str) -> None:
        if theme:
            self.load_theme(theme)

    def _slot_defaults_from_manifest(self, theme: str) -> Dict[str, SlotTransform]:
        manifest = load_hero_manifest(theme, base_dir=ROOT)
        layout = manifest.get("layout", {})
        gear_cfg = layout.get("gear", {}) if isinstance(layout, dict) else {}
        default_cfg = gear_cfg.get("default", {}) if isinstance(gear_cfg, dict) else {}
        slots_cfg = gear_cfg.get("slots", {}) if isinstance(gear_cfg, dict) else {}

        def read_cfg(slot: str) -> dict:
            slug = SLOT_SLUGS.get(slot, slot.lower())
            slot_cfg = {}
            if isinstance(default_cfg, dict):
                slot_cfg.update(default_cfg)
            if isinstance(slots_cfg, dict) and isinstance(slots_cfg.get(slug), dict):
                slot_cfg.update(slots_cfg[slug])
            elif isinstance(gear_cfg, dict) and isinstance(gear_cfg.get(slug), dict):
                slot_cfg.update(gear_cfg[slug])
            return slot_cfg

        result: Dict[str, SlotTransform] = {}
        for slot in GEAR_SLOT_ORDER:
            cfg = read_cfg(slot)
            off = cfg.get("offset", [0.0, 0.0])
            sc = cfg.get("scale", [1.0, 1.0])
            try:
                ox = float(off[0]) if isinstance(off, (list, tuple)) and len(off) > 0 else float(off)
            except Exception:
                ox = 0.0
            try:
                oy = float(off[1]) if isinstance(off, (list, tuple)) and len(off) > 1 else float(off)
            except Exception:
                oy = 0.0
            try:
                sx = float(sc[0]) if isinstance(sc, (list, tuple)) and len(sc) > 0 else float(sc)
            except Exception:
                sx = 1.0
            try:
                sy = float(sc[1]) if isinstance(sc, (list, tuple)) and len(sc) > 1 else float(sc)
            except Exception:
                sy = sx
            rot = float(cfg.get("rotation_deg", cfg.get("rotation", 0.0)) or 0.0)
            result[slot] = SlotTransform(offset_x=ox, offset_y=oy, scale_x=sx, scale_y=sy, rotation_deg=rot)
        return result

    def _resolve_slot_layer_path(self, theme: str, slot: str, rarity: str) -> Optional[Path]:
        # Try resolver first.
        item_stub = {"rarity": rarity, "item_type": slot, "name": f"{slot} {rarity}"}
        path = resolve_hero_gear_layer(theme, slot, item_stub, base_dir=ROOT)
        if path and path.exists():
            return path
        # Fallback to canonical slot_{rarity}.svg.
        slot_slug = SLOT_SLUGS[slot]
        p = ROOT / "icons" / "heroes" / theme / "gear" / slot_slug / f"{slot_slug}_{rarity.lower()}.svg"
        return p if p.exists() else None

    def _clear_scene_items(self) -> None:
        for slot, item in self.slot_items.items():
            if item is not None:
                self.scene.removeItem(item)
                self.slot_items[slot] = None
        if self.base_item is not None:
            self.scene.removeItem(self.base_item)
            self.base_item = None

    def load_theme(self, theme: str) -> None:
        theme = (theme or "").strip()
        if not theme:
            return
        self.current_theme = theme
        self._clear_scene_items()
        defaults = self._slot_defaults_from_manifest(theme)
        self.slot_transforms = self._new_slot_transform_map()
        for slot in GEAR_SLOT_ORDER:
            visible = self.slot_visibility_checks[slot].isChecked()
            for rarity in RARITIES:
                self.slot_transforms[slot][rarity] = defaults[slot].clone(rarity=rarity, visible=visible)

        base_path = resolve_hero_base_layer(theme, base_dir=ROOT)
        if not base_path or not base_path.exists():
            self.status.setText(f"Missing base hero SVG for theme: {theme}")
            return

        self.base_item = QGraphicsSvgItem(str(base_path))
        self.base_item.setFlags(QtWidgets.QGraphicsItem.GraphicsItemFlag(0))
        self.base_item.setZValue(0)
        self.scene.addItem(self.base_item)

        for idx, slot in enumerate(GEAR_SLOT_ORDER, start=1):
            self._rebuild_slot_item(slot, z=10 + idx)

        self.select_slot(GEAR_SLOT_ORDER[0])
        profile_path = self._theme_profile_path(theme)
        self.profile_path_label.setText(f"Default profile path:\n{profile_path}")
        self.status.setText(f"Loaded theme: {theme}")

    def _rebuild_slot_item(self, slot: str, z: float) -> None:
        old = self.slot_items.get(slot)
        was_selected = bool(old and old.isSelected())
        if old is not None:
            self.scene.removeItem(old)
            self.slot_items[slot] = None

        if not self.current_theme:
            return
        rarity = self.slot_rarity_combos[slot].currentText()
        path = self._resolve_slot_layer_path(self.current_theme, slot, rarity)
        if not path:
            return

        item = LayerItem(slot=slot, svg_path=path, owner=self)
        item.setZValue(z)
        self.scene.addItem(item)
        self.slot_items[slot] = item
        self._apply_slot_transform(slot)
        if was_selected:
            item.setSelected(True)

    def _apply_slot_transform(self, slot: str) -> None:
        item = self.slot_items.get(slot)
        if item is None:
            return
        cfg = self._active_cfg_for_slot(slot)

        self._syncing = True
        try:
            br = item.boundingRect()
            center = br.center()

            tr = QtGui.QTransform()
            tr.translate(center.x(), center.y())
            tr.rotate(cfg.rotation_deg)
            tr.scale(cfg.scale_x, cfg.scale_y)
            tr.translate(-center.x(), -center.y())
            item.setTransform(tr, False)
            item.setPos(cfg.offset_x * HERO_CANVAS_WIDTH, cfg.offset_y * HERO_CANVAS_HEIGHT)
            item.setVisible(cfg.visible)
        finally:
            self._syncing = False

    def on_slot_item_moved(self, slot: str) -> None:
        if self._syncing:
            return
        item = self.slot_items.get(slot)
        if item is None:
            return
        cfg = self._active_cfg_for_slot(slot)
        p = item.pos()
        cfg.offset_x = p.x() / HERO_CANVAS_WIDTH
        cfg.offset_y = p.y() / HERO_CANVAS_HEIGHT
        if slot == self.current_slot:
            self._sync_controls_from_slot(slot)

    def on_scene_slot_selected(self, slot: str) -> None:
        self.select_slot(slot)

    def select_slot(self, slot: str) -> None:
        self.current_slot = slot
        self.selected_slot_label.setText(slot)

        for s, btn in self.slot_select_buttons.items():
            btn.setStyleSheet("font-weight: 700; color: #111;" if s == slot else "")

        item = self.slot_items.get(slot)
        self._syncing = True
        try:
            for other_slot, other_item in self.slot_items.items():
                if other_item is not None:
                    other_item.setSelected(other_slot == slot and item is not None)
        finally:
            self._syncing = False

        self._sync_controls_from_slot(slot)

    def _sync_controls_from_slot(self, slot: str) -> None:
        cfg = self._active_cfg_for_slot(slot)
        self._syncing = True
        try:
            self.offset_x_spin.setValue(cfg.offset_x)
            self.offset_y_spin.setValue(cfg.offset_y)
            self.scale_x_spin.setValue(cfg.scale_x)
            self.scale_y_spin.setValue(cfg.scale_y)
            self.rotation_spin.setValue(cfg.rotation_deg)
        finally:
            self._syncing = False

    def _on_transform_spin_changed(self) -> None:
        if self._syncing or not self.current_slot:
            return
        cfg = self._active_cfg_for_slot(self.current_slot)
        cfg.offset_x = self.offset_x_spin.value()
        cfg.offset_y = self.offset_y_spin.value()
        cfg.scale_x = self.scale_x_spin.value()
        cfg.scale_y = self.scale_y_spin.value()
        cfg.rotation_deg = self.rotation_spin.value()
        self._apply_slot_transform(self.current_slot)

    def _on_slot_rarity_changed(self, slot: str) -> None:
        idx = GEAR_SLOT_ORDER.index(slot)
        self._rebuild_slot_item(slot, z=10 + idx + 1)
        cfg = self._active_cfg_for_slot(slot)
        self._syncing = True
        try:
            self.slot_visibility_checks[slot].setChecked(cfg.visible)
        finally:
            self._syncing = False
        if slot == self.current_slot:
            self.select_slot(slot)

    def _on_slot_visible_changed(self, slot: str) -> None:
        if self._syncing:
            return
        visible = self.slot_visibility_checks[slot].isChecked()
        for rarity in RARITIES:
            self.slot_transforms[slot][rarity].visible = visible
        self._apply_slot_transform(slot)

    def adjust_selected_scale(self, factor: float) -> None:
        if not self.current_slot:
            return
        cfg = self._active_cfg_for_slot(self.current_slot)
        cfg.scale_x = max(0.10, min(5.0, cfg.scale_x * factor))
        cfg.scale_y = max(0.10, min(5.0, cfg.scale_y * factor))
        self._apply_slot_transform(self.current_slot)
        self._sync_controls_from_slot(self.current_slot)

    def adjust_selected_rotation(self, step: float) -> None:
        if not self.current_slot:
            return
        cfg = self._active_cfg_for_slot(self.current_slot)
        cfg.rotation_deg = max(-360.0, min(360.0, cfg.rotation_deg + step))
        self._apply_slot_transform(self.current_slot)
        self._sync_controls_from_slot(self.current_slot)

    def reset_selected_slot(self) -> None:
        if not self.current_slot or not self.current_theme:
            return
        rarity = self._active_rarity_for_slot(self.current_slot)
        visible = self.slot_visibility_checks[self.current_slot].isChecked()
        defaults = self._slot_defaults_from_manifest(self.current_theme)
        self.slot_transforms[self.current_slot][rarity] = defaults[self.current_slot].clone(
            rarity=rarity,
            visible=visible,
        )
        self._apply_slot_transform(self.current_slot)
        self._sync_controls_from_slot(self.current_slot)

    def reset_all_slots(self) -> None:
        if not self.current_theme:
            return
        defaults = self._slot_defaults_from_manifest(self.current_theme)
        for slot in GEAR_SLOT_ORDER:
            visible = self.slot_visibility_checks[slot].isChecked()
            for rarity in RARITIES:
                self.slot_transforms[slot][rarity] = defaults[slot].clone(rarity=rarity, visible=visible)
            self._apply_slot_transform(slot)
        if self.current_slot:
            self._sync_controls_from_slot(self.current_slot)

    def save_profile(self) -> None:
        if not self.current_theme:
            return
        out_path = self._theme_profile_path(self.current_theme)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "theme": self.current_theme,
            "canvas": {"width": HERO_CANVAS_WIDTH, "height": HERO_CANVAS_HEIGHT},
            "schema_version": 2,
            "slots": {
                slot: {
                    "active_rarity": self.slot_rarity_combos[slot].currentText(),
                    "visible": self.slot_visibility_checks[slot].isChecked(),
                    "rarities": {
                        rarity: asdict(cfg)
                        for rarity, cfg in self.slot_transforms[slot].items()
                    },
                }
                for slot in GEAR_SLOT_ORDER
            },
        }
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.status.setText(f"Saved + applied profile: {out_path}")

    def load_profile_dialog(self) -> None:
        start = str(self._theme_profile_path(self.current_theme or ""))
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load Composition Profile",
            start,
            "JSON files (*.json)",
        )
        if not file_path:
            return
        self.load_profile(Path(file_path))

    def load_profile(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.status.setText(f"Failed to load profile: {exc}")
            return

        theme = str(data.get("theme") or "").strip()
        if theme and theme != self.current_theme:
            idx = self.theme_combo.findText(theme)
            if idx >= 0:
                self.theme_combo.setCurrentIndex(idx)
            else:
                self.status.setText(f"Profile theme '{theme}' not found.")
                return

        slots = data.get("slots", {})
        if not isinstance(slots, dict):
            self.status.setText("Invalid profile: missing slots object")
            return

        for slot in GEAR_SLOT_ORDER:
            raw = slots.get(slot, {})
            if not isinstance(raw, dict):
                continue

            # Backward compatibility: slot payload was a single transform in v1.
            if "rarities" not in raw:
                template = self._active_cfg_for_slot(slot).clone()
                template.offset_x = float(raw.get("offset_x", template.offset_x))
                template.offset_y = float(raw.get("offset_y", template.offset_y))
                template.scale_x = max(0.10, float(raw.get("scale_x", template.scale_x)))
                template.scale_y = max(0.10, float(raw.get("scale_y", template.scale_y)))
                template.rotation_deg = float(raw.get("rotation_deg", template.rotation_deg))
                template.visible = bool(raw.get("visible", template.visible))
                for rarity_name in RARITIES:
                    self.slot_transforms[slot][rarity_name] = template.clone(rarity=rarity_name)
                rarity = str(raw.get("rarity", template.rarity))
                if rarity in RARITIES:
                    self.slot_rarity_combos[slot].setCurrentText(rarity)
                self.slot_visibility_checks[slot].setChecked(template.visible)
                self._apply_slot_transform(slot)
                continue

            raw_rarities = raw.get("rarities", {})
            if not isinstance(raw_rarities, dict):
                continue
            for rarity in RARITIES:
                rarity_raw = raw_rarities.get(rarity, {})
                if not isinstance(rarity_raw, dict):
                    continue
                cfg = self.slot_transforms[slot][rarity]
                cfg.offset_x = float(rarity_raw.get("offset_x", cfg.offset_x))
                cfg.offset_y = float(rarity_raw.get("offset_y", cfg.offset_y))
                cfg.scale_x = max(0.10, float(rarity_raw.get("scale_x", cfg.scale_x)))
                cfg.scale_y = max(0.10, float(rarity_raw.get("scale_y", cfg.scale_y)))
                cfg.rotation_deg = float(rarity_raw.get("rotation_deg", cfg.rotation_deg))
                cfg.visible = bool(rarity_raw.get("visible", cfg.visible))
                cfg.rarity = rarity

            active_rarity = str(raw.get("active_rarity", self.slot_rarity_combos[slot].currentText()))
            if active_rarity in RARITIES:
                self.slot_rarity_combos[slot].setCurrentText(active_rarity)

            vis = bool(raw.get("visible", self.slot_visibility_checks[slot].isChecked()))
            self.slot_visibility_checks[slot].setChecked(vis)
            self._apply_slot_transform(slot)

        if self.current_slot:
            self._sync_controls_from_slot(self.current_slot)
        self.status.setText(f"Loaded profile: {path}")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interactive hero SVG composition manager")
    parser.add_argument(
        "--theme",
        default="",
        help="Theme to preselect on startup (e.g. underdog, robot, zoo_worker).",
    )
    parser.add_argument(
        "--profile",
        default="",
        help="Optional path to a composition profile JSON to load after startup.",
    )
    return parser


def main() -> int:
    args = _build_arg_parser().parse_args()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    win = CompositionManagerWindow()
    if args.theme:
        idx = win.theme_combo.findText(args.theme.strip())
        if idx >= 0:
            win.theme_combo.setCurrentIndex(idx)
    if args.profile:
        profile_path = Path(args.profile).expanduser()
        if profile_path.exists():
            win.load_profile(profile_path)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
