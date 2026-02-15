"""
Hero SVG rendering subsystem.

This module provides a safe SVG-first rendering path for hero + equipped gear.
It also supports optional runtime composition overrides loaded from:
`artifacts/hero_composition/<theme>_composition_profile.json`.
If required assets are missing or invalid, callers can fall back to procedural
rendering without breaking gameplay.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

from PySide6 import QtCore, QtGui
from PySide6.QtSvg import QSvgRenderer

from app_utils import get_app_dir

logger = logging.getLogger(__name__)


HERO_CANVAS_WIDTH = 180
HERO_CANVAS_HEIGHT = 220

GEAR_SLOT_ORDER = (
    "Cloak",
    "Chestplate",
    "Boots",
    "Gauntlets",
    "Amulet",
    "Helmet",
    "Shield",
    "Weapon",
)

_SLOT_SLUGS: Dict[str, str] = {
    "Helmet": "helmet",
    "Chestplate": "chestplate",
    "Gauntlets": "gauntlets",
    "Boots": "boots",
    "Shield": "shield",
    "Weapon": "weapon",
    "Cloak": "cloak",
    "Amulet": "amulet",
}

_RARITY_SLUGS: Dict[str, str] = {
    "common": "common",
    "uncommon": "uncommon",
    "rare": "rare",
    "epic": "epic",
    "legendary": "legendary",
    "celestial": "celestial",
}

_DEFAULT_GEAR_PATTERNS = (
    "gear/{slot}/{item_type}_{rarity}.svg",
    "gear/{slot}/{item_name}_{rarity}.svg",
    "gear/{slot}/{item_type}.svg",
    "gear/{slot}/{slot}_{rarity}.svg",
    "gear/{slot}/{rarity}.svg",
    "gear/{slot}/{slot}.svg",
)

_DEFAULT_BASE_FILES = ("hero_base.svg", "hero.svg", "base.svg")
_DEFAULT_FX_PATTERN = "fx/tier_{power_tier}.svg"

# FX tier aliases bridge gameplay tier naming (e.g., "godlike") to
# asset tier naming (e.g., "celestial"), while preserving strict file lookup.
_FX_TIER_ALIASES: Dict[str, tuple[str, ...]] = {
    "godlike": ("celestial", "legendary", "epic"),
    "celestial": ("legendary", "epic"),
    "legendary": ("epic",),
}

# Default normalized slot boxes used by smart auto-fit when a gear SVG uses
# a non-canonical viewBox (i.e., not the full 180x220 canvas).
_DEFAULT_GEAR_SLOT_BOXES: Dict[str, tuple[float, float, float, float]] = {
    "helmet": (0.28, 0.06, 0.44, 0.28),
    "chestplate": (0.24, 0.22, 0.52, 0.34),
    "gauntlets": (0.18, 0.30, 0.64, 0.34),
    "boots": (0.28, 0.64, 0.44, 0.30),
    "shield": (0.08, 0.28, 0.34, 0.44),
    "weapon": (0.58, 0.24, 0.34, 0.52),
    "cloak": (0.16, 0.20, 0.68, 0.64),
    "amulet": (0.40, 0.30, 0.20, 0.20),
}

_ANCHOR_FACTORS: Dict[str, tuple[float, float]] = {
    "top_left": (0.0, 0.0),
    "top_center": (0.5, 0.0),
    "top_right": (1.0, 0.0),
    "center_left": (0.0, 0.5),
    "center": (0.5, 0.5),
    "center_right": (1.0, 0.5),
    "bottom_left": (0.0, 1.0),
    "bottom_center": (0.5, 1.0),
    "bottom_right": (1.0, 1.0),
    "left": (0.0, 0.5),
    "right": (1.0, 0.5),
    "top": (0.5, 0.0),
    "bottom": (0.5, 1.0),
}

_renderer_cache: Dict[str, tuple[float, QSvgRenderer]] = {}
_composition_profile_cache: Dict[str, tuple[float, dict]] = {}
_renderer_active_ref_counts: Dict[str, int] = {}


@dataclass(frozen=True)
class HeroLayer:
    """Resolved hero layer asset."""

    path: Path
    kind: str  # base | gear | fx
    slot: Optional[str] = None
    rarity: Optional[str] = None
    item_type: Optional[str] = None


def _slugify(value: str) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "unknown"


def _normalize_slot(slot: str) -> str:
    return _SLOT_SLUGS.get(slot, _slugify(slot))


def _normalize_rarity(rarity: str) -> str:
    return _RARITY_SLUGS.get((rarity or "common").strip().lower(), "common")


def _fx_tier_candidates(power_tier: str) -> list[str]:
    """Return prioritized FX tier slugs to try for a given gameplay tier."""
    slug = _slugify(power_tier)
    aliases = _FX_TIER_ALIASES.get(slug, ())
    return [slug, *aliases]


def _normalize_anchor(anchor: str) -> tuple[float, float]:
    key = _slugify(anchor).replace("middle", "center")
    return _ANCHOR_FACTORS.get(key, _ANCHOR_FACTORS["center"])


def _float_pair(value, default: tuple[float, float]) -> tuple[float, float]:
    if isinstance(value, (int, float)):
        val = float(value)
        return (val, val)
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return (float(value[0]), float(value[1]))
        except (TypeError, ValueError):
            return default
    return default


def _normalized_box(value) -> Optional[tuple[float, float, float, float]]:
    if not isinstance(value, (list, tuple)) or len(value) < 4:
        return None
    try:
        x, y, w, h = float(value[0]), float(value[1]), float(value[2]), float(value[3])
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    return (x, y, w, h)


def _box_to_rect(target_rect: QtCore.QRectF, box: tuple[float, float, float, float]) -> QtCore.QRectF:
    x, y, w, h = box
    return QtCore.QRectF(
        target_rect.x() + x * target_rect.width(),
        target_rect.y() + y * target_rect.height(),
        w * target_rect.width(),
        h * target_rect.height(),
    )


def _renderer_source_size(renderer: QSvgRenderer) -> tuple[float, float]:
    view_box = renderer.viewBoxF()
    if view_box.isValid() and view_box.width() > 0 and view_box.height() > 0:
        return (float(view_box.width()), float(view_box.height()))
    default_size = renderer.defaultSize()
    if default_size.width() > 0 and default_size.height() > 0:
        return (float(default_size.width()), float(default_size.height()))
    return (float(HERO_CANVAS_WIDTH), float(HERO_CANVAS_HEIGHT))


def _approx_equal(lhs: float, rhs: float, tolerance_ratio: float = 0.08) -> bool:
    return abs(lhs - rhs) <= max(abs(rhs), 1.0) * tolerance_ratio


def _is_canonical_canvas_source(source_w: float, source_h: float) -> bool:
    return _approx_equal(source_w, float(HERO_CANVAS_WIDTH)) and _approx_equal(source_h, float(HERO_CANVAS_HEIGHT))


def _fit_contain_rect(
    source_w: float,
    source_h: float,
    box_rect: QtCore.QRectF,
    anchor: str = "center",
) -> QtCore.QRectF:
    if source_w <= 0 or source_h <= 0 or box_rect.width() <= 0 or box_rect.height() <= 0:
        return QtCore.QRectF(box_rect)
    scale = min(box_rect.width() / source_w, box_rect.height() / source_h)
    draw_w = source_w * scale
    draw_h = source_h * scale
    ax, ay = _normalize_anchor(anchor)
    draw_x = box_rect.x() + (box_rect.width() - draw_w) * ax
    draw_y = box_rect.y() + (box_rect.height() - draw_h) * ay
    return QtCore.QRectF(draw_x, draw_y, draw_w, draw_h)


def _composition_profile_path(story_theme: str, base_dir: Optional[Path] = None) -> Path:
    root = Path(base_dir) if base_dir else get_app_dir()
    return root / "artifacts" / "hero_composition" / f"{story_theme}_composition_profile.json"


def _load_theme_composition_profile(story_theme: str, base_dir: Optional[Path] = None) -> Optional[dict]:
    theme_slug = _slugify(story_theme)
    if not theme_slug:
        return None

    profile_path = _composition_profile_path(theme_slug, base_dir=base_dir)
    cache_key = str(profile_path.resolve())

    if not profile_path.exists():
        _composition_profile_cache.pop(cache_key, None)
        return None

    try:
        mtime = profile_path.stat().st_mtime
    except OSError:
        return None

    cached = _composition_profile_cache.get(cache_key)
    if cached and cached[0] == mtime:
        return cached[1]

    try:
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Invalid composition profile for theme '%s': %s", story_theme, exc)
        return None

    if not isinstance(data, dict):
        logger.warning("Composition profile for theme '%s' is not a JSON object", story_theme)
        return None

    _composition_profile_cache[cache_key] = (mtime, data)
    return data


def _coerce_profile_layout_override(raw_cfg: dict) -> dict:
    cfg: dict = {}
    if not isinstance(raw_cfg, dict):
        return cfg

    try:
        ox = float(raw_cfg.get("offset_x", 0.0))
        oy = float(raw_cfg.get("offset_y", 0.0))
        cfg["offset"] = [ox, oy]
    except (TypeError, ValueError):
        pass

    try:
        sx = float(raw_cfg.get("scale_x", 1.0))
        sy = float(raw_cfg.get("scale_y", 1.0))
        cfg["scale"] = [sx, sy]
    except (TypeError, ValueError):
        pass

    try:
        cfg["rotation_deg"] = float(raw_cfg.get("rotation_deg", raw_cfg.get("rotation", 0.0)) or 0.0)
    except (TypeError, ValueError):
        pass

    if "visible" in raw_cfg:
        cfg["visible"] = bool(raw_cfg.get("visible"))

    return cfg


def _resolve_profile_slot_payload(slots: dict, slot: str) -> Optional[dict]:
    if not isinstance(slots, dict):
        return None
    slot_slug = _normalize_slot(slot)
    for key in (slot, slot_slug):
        payload = slots.get(key)
        if isinstance(payload, dict):
            return payload
    for key, payload in slots.items():
        if not isinstance(payload, dict):
            continue
        if _normalize_slot(str(key)) == slot_slug:
            return payload
    return None


def _profile_override_for_layer(profile: Optional[dict], layer: HeroLayer) -> dict:
    if layer.kind != "gear" or not layer.slot or not isinstance(profile, dict):
        return {}
    slots = profile.get("slots", {})
    slot_payload = _resolve_profile_slot_payload(slots, layer.slot)
    if not isinstance(slot_payload, dict):
        return {}

    # v2 schema: slot -> {visible, active_rarity, rarities: {Common: {...}}}
    raw_rarities = slot_payload.get("rarities", {})
    if isinstance(raw_rarities, dict):
        rarity_slug = _normalize_rarity(layer.rarity or "common")
        candidates = []
        if layer.rarity:
            candidates.extend([str(layer.rarity), str(layer.rarity).title(), str(layer.rarity).lower()])
        candidates.extend([rarity_slug, rarity_slug.title(), rarity_slug.capitalize()])
        raw_cfg = None
        for key in candidates:
            val = raw_rarities.get(key)
            if isinstance(val, dict):
                raw_cfg = val
                break
        if raw_cfg is None:
            for key, value in raw_rarities.items():
                if isinstance(value, dict) and _normalize_rarity(str(key)) == rarity_slug:
                    raw_cfg = value
                    break
        override = _coerce_profile_layout_override(raw_cfg or {})
        if "visible" not in override and "visible" in slot_payload:
            override["visible"] = bool(slot_payload.get("visible"))
        return override

    # v1 schema fallback: slot -> {offset_x, offset_y, ...}
    return _coerce_profile_layout_override(slot_payload)


def _layer_layout_config(manifest: Optional[dict], layer: HeroLayer, base_dir: Optional[Path] = None) -> dict:
    layout_root = manifest.get("layout", {}) if isinstance(manifest, dict) else {}
    if not isinstance(layout_root, dict):
        layout_root = {}

    if layer.kind == "base":
        config = {"fit": "stretch", "anchor": "center", "offset": [0.0, 0.0], "scale": [1.0, 1.0]}
        base_cfg = layout_root.get("base", {})
        if isinstance(base_cfg, dict):
            config.update(base_cfg)
        return config

    if layer.kind == "fx":
        config = {"fit": "stretch", "anchor": "center", "offset": [0.0, 0.0], "scale": [1.0, 1.0]}
        fx_cfg = layout_root.get("fx", {})
        if isinstance(fx_cfg, dict):
            config.update(fx_cfg)
        return config

    # gear defaults + optional per-slot override
    config = {"fit": "auto", "anchor": "center", "offset": [0.0, 0.0], "scale": [1.0, 1.0]}
    gear_cfg = layout_root.get("gear", {})
    if not isinstance(gear_cfg, dict):
        return config

    default_cfg = gear_cfg.get("default", {})
    if isinstance(default_cfg, dict):
        config.update(default_cfg)

    slot_slug = _normalize_slot(layer.slot or "")
    slots_cfg = gear_cfg.get("slots", {})
    slot_cfg = slots_cfg.get(slot_slug) if isinstance(slots_cfg, dict) else None
    if slot_cfg is None:
        slot_cfg = gear_cfg.get(slot_slug)
    if isinstance(slot_cfg, dict):
        config.update(slot_cfg)

    story_theme = ""
    if isinstance(manifest, dict):
        story_theme = str(manifest.get("theme_id", "")).strip()
    profile = _load_theme_composition_profile(story_theme, base_dir=base_dir) if story_theme else None
    profile_override = _profile_override_for_layer(profile, layer)
    if profile_override:
        config.update(profile_override)

    return config


def resolve_layer_target_rect(
    layer: HeroLayer,
    renderer: QSvgRenderer,
    target_rect: QtCore.QRectF,
    manifest: Optional[dict] = None,
    base_dir: Optional[Path] = None,
) -> QtCore.QRectF:
    """
    Resolve per-layer draw rect with smart fit/anchor correction.

    Smart mode behavior:
    - Canonical 180x220 layers: stretch full canvas.
    - Non-canonical gear layers: auto-fit into slot box (contain + anchor).
    - Manifest `layout` block can override fit/anchor/offset/scale/box.
    """
    if target_rect.width() <= 0 or target_rect.height() <= 0:
        target_rect = QtCore.QRectF(0, 0, HERO_CANVAS_WIDTH, HERO_CANVAS_HEIGHT)

    source_w, source_h = _renderer_source_size(renderer)
    canonical_source = _is_canonical_canvas_source(source_w, source_h)
    cfg = _layer_layout_config(manifest, layer, base_dir=base_dir)

    fit = _slugify(str(cfg.get("fit", "auto")))
    if fit == "keep_aspect_ratio":
        fit = "contain"
    if fit not in {"auto", "stretch", "contain"}:
        fit = "auto"
    anchor = str(cfg.get("anchor", "center"))
    offset_x, offset_y = _float_pair(cfg.get("offset", [0.0, 0.0]), (0.0, 0.0))
    scale_x, scale_y = _float_pair(cfg.get("scale", [1.0, 1.0]), (1.0, 1.0))
    if scale_x <= 0:
        scale_x = 1.0
    if scale_y <= 0:
        scale_y = 1.0

    manual_box = _normalized_box(cfg.get("box"))
    if manual_box:
        base_rect = _box_to_rect(target_rect, manual_box)
    elif layer.kind == "gear" and fit in {"auto", "contain"} and not canonical_source:
        slot_box = _DEFAULT_GEAR_SLOT_BOXES.get(_normalize_slot(layer.slot or ""))
        base_rect = _box_to_rect(target_rect, slot_box) if slot_box else QtCore.QRectF(target_rect)
    else:
        base_rect = QtCore.QRectF(target_rect)

    if fit == "auto":
        fit = "contain" if (layer.kind == "gear" and not canonical_source) else "stretch"

    if fit == "contain":
        draw_rect = _fit_contain_rect(source_w, source_h, base_rect, anchor=anchor)
    else:
        draw_rect = QtCore.QRectF(base_rect)

    # Uniformly scale around rect center (fine-tuning hook from manifest).
    if abs(scale_x - 1.0) > 1e-6 or abs(scale_y - 1.0) > 1e-6:
        center = draw_rect.center()
        new_w = draw_rect.width() * scale_x
        new_h = draw_rect.height() * scale_y
        draw_rect = QtCore.QRectF(center.x() - new_w / 2, center.y() - new_h / 2, new_w, new_h)

    # Offset is normalized to full hero canvas target dimensions.
    if abs(offset_x) > 1e-6 or abs(offset_y) > 1e-6:
        draw_rect.translate(offset_x * target_rect.width(), offset_y * target_rect.height())

    return draw_rect


def _theme_root(story_theme: str, base_dir: Optional[Path] = None) -> Path:
    root = Path(base_dir) if base_dir else get_app_dir()
    return root / "icons" / "heroes" / (story_theme or "warrior")


def _manifest_path(story_theme: str, base_dir: Optional[Path] = None) -> Path:
    return _theme_root(story_theme, base_dir=base_dir) / "hero_manifest.json"


def _default_manifest(story_theme: str) -> dict:
    return {
        "version": 1,
        "theme_id": story_theme,
        "canvas": {"width": HERO_CANVAS_WIDTH, "height": HERO_CANVAS_HEIGHT},
        "base": {"file": "hero_base.svg", "fallback_files": list(_DEFAULT_BASE_FILES)},
        "gear": {"slot_order": list(GEAR_SLOT_ORDER), "patterns": list(_DEFAULT_GEAR_PATTERNS)},
        "fx": {"tier_pattern": _DEFAULT_FX_PATTERN},
        "layout": {
            "base": {"fit": "stretch", "anchor": "center", "offset": [0.0, 0.0], "scale": [1.0, 1.0]},
            "gear": {"default": {"fit": "auto", "anchor": "center", "offset": [0.0, 0.0], "scale": [1.0, 1.0]}},
            "fx": {"fit": "stretch", "anchor": "center", "offset": [0.0, 0.0], "scale": [1.0, 1.0]},
        },
        "animation": {},
    }


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_hero_manifest(story_theme: str, base_dir: Optional[Path] = None) -> dict:
    """
    Load optional per-theme hero manifest.

    Missing or invalid manifest files are tolerated; defaults are returned.
    """
    manifest = _default_manifest(story_theme)
    path = _manifest_path(story_theme, base_dir=base_dir)
    if not path.exists():
        return manifest

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Invalid hero manifest for theme '%s': %s", story_theme, exc)
        return manifest

    if not isinstance(data, dict):
        logger.warning("Hero manifest for theme '%s' is not a JSON object", story_theme)
        return manifest
    return _deep_merge(manifest, data)


def _resolve_existing(theme_dir: Path, rel_candidates: Iterable[str]) -> Optional[Path]:
    for rel in rel_candidates:
        candidate = theme_dir / rel
        if candidate.exists():
            return candidate
    return None


def resolve_hero_base_layer(
    story_theme: str,
    manifest: Optional[dict] = None,
    base_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Resolve a theme base hero SVG path."""
    manifest = manifest or load_hero_manifest(story_theme, base_dir=base_dir)
    theme_dir = _theme_root(story_theme, base_dir=base_dir)
    base_block = manifest.get("base", {})
    preferred = str(base_block.get("file", "hero_base.svg"))
    fallback_files = [str(x) for x in base_block.get("fallback_files", _DEFAULT_BASE_FILES)]
    rel_candidates = [preferred] + [x for x in fallback_files if x != preferred]
    return _resolve_existing(theme_dir, rel_candidates)


def resolve_hero_gear_layer(
    story_theme: str,
    slot: str,
    item: dict,
    manifest: Optional[dict] = None,
    base_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Resolve the best-matching gear layer for an equipped item."""
    if not item:
        return None

    manifest = manifest or load_hero_manifest(story_theme, base_dir=base_dir)
    theme_dir = _theme_root(story_theme, base_dir=base_dir)

    slot_slug = _normalize_slot(slot)
    item_type_slug = _slugify(item.get("item_type", slot))
    item_name_slug = _slugify(item.get("name", item_type_slug))
    rarity_slug = _normalize_rarity(item.get("rarity", "common"))

    tokens = {
        "slot": slot_slug,
        "item_type": item_type_slug,
        "item_name": item_name_slug,
        "rarity": rarity_slug,
    }

    patterns = manifest.get("gear", {}).get("patterns", list(_DEFAULT_GEAR_PATTERNS))
    rel_candidates = []
    for raw_pattern in patterns:
        try:
            rel_candidates.append(str(raw_pattern).format(**tokens))
        except Exception:
            continue
    return _resolve_existing(theme_dir, rel_candidates)


def resolve_hero_tier_fx_layer(
    story_theme: str,
    power_tier: Optional[str],
    manifest: Optional[dict] = None,
    base_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Resolve optional tier FX overlay layer."""
    if not power_tier:
        return None
    manifest = manifest or load_hero_manifest(story_theme, base_dir=base_dir)
    pattern = manifest.get("fx", {}).get("tier_pattern", _DEFAULT_FX_PATTERN)
    theme_dir = _theme_root(story_theme, base_dir=base_dir)
    for tier_slug in _fx_tier_candidates(power_tier):
        rel = str(pattern).format(power_tier=tier_slug)
        candidate = theme_dir / rel
        if candidate.exists():
            return candidate
    return None


def build_hero_layer_plan(
    story_theme: str,
    equipped: Optional[dict],
    power_tier: Optional[str] = None,
    base_dir: Optional[Path] = None,
    manifest: Optional[dict] = None,
) -> list[HeroLayer]:
    """
    Build ordered layer plan for hero rendering.

    Returns empty list if base layer is missing (caller should fallback).
    """
    manifest = manifest or load_hero_manifest(story_theme, base_dir=base_dir)
    base_layer = resolve_hero_base_layer(story_theme, manifest=manifest, base_dir=base_dir)
    if not base_layer:
        return []

    fx_layer = resolve_hero_tier_fx_layer(
        story_theme=story_theme,
        power_tier=power_tier,
        manifest=manifest,
        base_dir=base_dir,
    )

    # Draw order: FX background -> base hero -> gear overlays.
    # This guarantees tier FX stays behind the character across all themes.
    layers: list[HeroLayer] = []
    if fx_layer:
        layers.append(HeroLayer(path=fx_layer, kind="fx"))
    layers.append(HeroLayer(path=base_layer, kind="base"))

    equipped = equipped or {}
    slot_order = manifest.get("gear", {}).get("slot_order", list(GEAR_SLOT_ORDER))

    for slot in slot_order:
        item = equipped.get(slot)
        if not item:
            continue
        layer_path = resolve_hero_gear_layer(
            story_theme=story_theme,
            slot=slot,
            item=item,
            manifest=manifest,
            base_dir=base_dir,
        )
        if not layer_path:
            continue
        layers.append(
            HeroLayer(
                path=layer_path,
                kind="gear",
                slot=slot,
                rarity=_normalize_rarity(item.get("rarity", "common")),
                item_type=_slugify(item.get("item_type", slot)),
            )
        )

    return layers


def validate_hero_svg_theme_pack(
    story_theme: str,
    base_dir: Optional[Path] = None,
) -> dict:
    """Return a validation summary for a theme hero SVG pack."""
    manifest = load_hero_manifest(story_theme, base_dir=base_dir)
    theme_dir = _theme_root(story_theme, base_dir=base_dir)
    base_layer = resolve_hero_base_layer(story_theme, manifest=manifest, base_dir=base_dir)

    slot_candidates: Dict[str, list[str]] = {}
    for slot in manifest.get("gear", {}).get("slot_order", list(GEAR_SLOT_ORDER)):
        slot_slug = _normalize_slot(slot)
        slot_dir = theme_dir / "gear" / slot_slug
        candidates = []
        if slot_dir.exists():
            for svg_file in slot_dir.glob("*.svg"):
                candidates.append(svg_file.name)
        slot_candidates[slot] = sorted(candidates)

    return {
        "theme_id": story_theme,
        "theme_dir": str(theme_dir),
        "manifest_path": str(_manifest_path(story_theme, base_dir=base_dir)),
        "manifest_exists": _manifest_path(story_theme, base_dir=base_dir).exists(),
        "base_layer": str(base_layer) if base_layer else None,
        "base_exists": bool(base_layer),
        "slot_candidates": slot_candidates,
        "is_ready": bool(base_layer),
    }


def clear_hero_svg_cache() -> None:
    """Clear renderer cache (useful for tooling/hot-reload workflows)."""
    _renderer_cache.clear()
    _composition_profile_cache.clear()
    _renderer_active_ref_counts.clear()


def _set_renderer_animation_enabled(renderer: QSvgRenderer, enabled: bool) -> None:
    """Best-effort animation toggle for a renderer."""
    try:
        renderer.setAnimationEnabled(bool(enabled))
    except Exception:
        # Non-animated documents or older bindings may reject this call.
        pass


def get_hero_svg_layer_renderers(
    story_theme: str,
    equipped: Optional[dict],
    power_tier: Optional[str] = None,
    base_dir: Optional[Path] = None,
) -> list[tuple[str, QSvgRenderer]]:
    """
    Resolve and return unique renderer objects for the hero's active layer plan.

    Returns:
        List of `(absolute_path, renderer)` tuples.
    """
    manifest = load_hero_manifest(story_theme, base_dir=base_dir)
    layers = build_hero_layer_plan(
        story_theme=story_theme,
        equipped=equipped,
        power_tier=power_tier,
        base_dir=base_dir,
        manifest=manifest,
    )
    if not layers:
        return []

    refs: list[tuple[str, QSvgRenderer]] = []
    seen: set[str] = set()
    for layer in layers:
        abs_path = str(layer.path.resolve())
        if abs_path in seen:
            continue
        renderer = _get_cached_renderer(layer.path)
        if not renderer:
            continue
        seen.add(abs_path)
        refs.append((abs_path, renderer))
    return refs


def retain_hero_svg_renderer_paths(paths: Iterable[str]) -> None:
    """
    Mark renderer paths as actively used by visible hero canvases.

    Animated renderers are enabled while at least one active consumer exists.
    """
    for abs_path in {str(p) for p in paths if p}:
        count = _renderer_active_ref_counts.get(abs_path, 0) + 1
        _renderer_active_ref_counts[abs_path] = count
        cached = _renderer_cache.get(abs_path)
        if cached:
            _set_renderer_animation_enabled(cached[1], True)


def release_hero_svg_renderer_paths(paths: Iterable[str]) -> None:
    """
    Release active usage refs for renderer paths.

    When ref-count reaches zero, renderer animation is paused.
    """
    for abs_path in {str(p) for p in paths if p}:
        current = _renderer_active_ref_counts.get(abs_path, 0)
        if current <= 1:
            _renderer_active_ref_counts.pop(abs_path, None)
            cached = _renderer_cache.get(abs_path)
            if cached:
                _set_renderer_animation_enabled(cached[1], False)
        else:
            _renderer_active_ref_counts[abs_path] = current - 1


def evict_inactive_hero_svg_renderers() -> int:
    """
    Remove cached renderers that are no longer retained by active canvases.

    Returns:
        Number of renderer instances evicted from cache.
    """
    removed = 0
    for abs_path in list(_renderer_cache.keys()):
        if _renderer_active_ref_counts.get(abs_path, 0) > 0:
            continue
        _renderer_cache.pop(abs_path, None)
        removed += 1
    return removed


def _get_cached_renderer(path: Path) -> Optional[QSvgRenderer]:
    abs_path = str(path.resolve())
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None

    cached = _renderer_cache.get(abs_path)
    if cached and cached[0] == mtime:
        renderer = cached[1]
        _set_renderer_animation_enabled(
            renderer,
            _renderer_active_ref_counts.get(abs_path, 0) > 0,
        )
        return renderer

    renderer = QSvgRenderer(abs_path)
    if not renderer.isValid():
        logger.warning("Invalid hero SVG asset: %s", abs_path)
        return None

    _set_renderer_animation_enabled(renderer, _renderer_active_ref_counts.get(abs_path, 0) > 0)
    _renderer_cache[abs_path] = (mtime, renderer)
    return renderer


def render_hero_svg_character(
    painter: QtGui.QPainter,
    story_theme: str,
    equipped: Optional[dict],
    power_tier: Optional[str] = None,
    canvas_width: int = HERO_CANVAS_WIDTH,
    canvas_height: int = HERO_CANVAS_HEIGHT,
    base_dir: Optional[Path] = None,
) -> bool:
    """
    Render hero and gear from SVG layer plan.

    Returns:
        True if SVG rendering succeeded (base layer rendered), else False.
    """
    manifest = load_hero_manifest(story_theme, base_dir=base_dir)
    layers = build_hero_layer_plan(
        story_theme=story_theme,
        equipped=equipped,
        power_tier=power_tier,
        base_dir=base_dir,
        manifest=manifest,
    )
    if not layers:
        return False

    target = QtCore.QRectF(0, 0, canvas_width, canvas_height)
    base_rendered = False

    for layer in layers:
        renderer = _get_cached_renderer(layer.path)
        if not renderer:
            if layer.kind == "base":
                return False
            continue
        renderer.setAspectRatioMode(QtCore.Qt.IgnoreAspectRatio)
        layer_cfg = _layer_layout_config(manifest, layer, base_dir=base_dir)
        if layer.kind == "gear" and not bool(layer_cfg.get("visible", True)):
            continue
        layer_target = resolve_layer_target_rect(
            layer=layer,
            renderer=renderer,
            target_rect=target,
            manifest=manifest,
            base_dir=base_dir,
        )

        try:
            rotation_deg = float(layer_cfg.get("rotation_deg", layer_cfg.get("rotation", 0.0)) or 0.0)
        except (TypeError, ValueError):
            rotation_deg = 0.0

        if abs(rotation_deg) > 1e-6:
            center = layer_target.center()
            painter.save()
            painter.translate(center)
            painter.rotate(rotation_deg)
            painter.translate(-center)
            renderer.render(painter, layer_target)
            painter.restore()
        else:
            renderer.render(painter, layer_target)

        if layer.kind == "base":
            base_rendered = True

    return base_rendered
