from pathlib import Path

from PySide6 import QtCore
from PySide6.QtSvg import QSvgRenderer

from hero_svg_system import (
    HeroLayer,
    build_hero_layer_plan,
    resolve_layer_target_rect,
    resolve_hero_base_layer,
    resolve_hero_gear_layer,
    resolve_hero_tier_fx_layer,
    validate_hero_svg_theme_pack,
)


def _write_svg(path: Path, viewbox: str = "0 0 180 220") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}"></svg>',
        encoding="utf-8",
    )


def test_build_plan_empty_when_base_missing(tmp_path: Path) -> None:
    plan = build_hero_layer_plan(
        story_theme="robot",
        equipped={"Helmet": {"item_type": "Safety Drone", "rarity": "Rare"}},
        power_tier="epic",
        base_dir=tmp_path,
    )
    assert plan == []


def test_resolve_gear_prefers_item_type_and_rarity(tmp_path: Path) -> None:
    base = tmp_path / "icons" / "heroes" / "robot"
    _write_svg(base / "hero_base.svg")
    _write_svg(base / "gear" / "helmet" / "safety_drone_rare.svg")
    _write_svg(base / "gear" / "helmet" / "helmet_rare.svg")

    layer = resolve_hero_gear_layer(
        story_theme="robot",
        slot="Helmet",
        item={"item_type": "Safety Drone", "rarity": "Rare", "name": "Any"},
        base_dir=tmp_path,
    )
    assert layer is not None
    assert layer.name == "safety_drone_rare.svg"


def test_resolve_gear_falls_back_to_slot_rarity(tmp_path: Path) -> None:
    base = tmp_path / "icons" / "heroes" / "robot"
    _write_svg(base / "hero_base.svg")
    _write_svg(base / "gear" / "helmet" / "helmet_epic.svg")

    layer = resolve_hero_gear_layer(
        story_theme="robot",
        slot="Helmet",
        item={"rarity": "Epic", "name": "No Type"},
        base_dir=tmp_path,
    )
    assert layer is not None
    assert layer.name == "helmet_epic.svg"


def test_resolve_gear_supports_celestial_rarity(tmp_path: Path) -> None:
    base = tmp_path / "icons" / "heroes" / "robot"
    _write_svg(base / "hero_base.svg")
    _write_svg(base / "gear" / "helmet" / "helmet_celestial.svg")

    layer = resolve_hero_gear_layer(
        story_theme="robot",
        slot="Helmet",
        item={"rarity": "Celestial", "name": "No Type"},
        base_dir=tmp_path,
    )
    assert layer is not None
    assert layer.name == "helmet_celestial.svg"


def test_build_plan_includes_base_gear_and_fx(tmp_path: Path) -> None:
    theme_root = tmp_path / "icons" / "heroes" / "zoo_worker"
    _write_svg(theme_root / "hero_base.svg")
    _write_svg(theme_root / "gear" / "helmet" / "helmet_common.svg")
    _write_svg(theme_root / "fx" / "tier_legendary.svg")

    plan = build_hero_layer_plan(
        story_theme="zoo_worker",
        equipped={"Helmet": {"rarity": "Common"}},
        power_tier="legendary",
        base_dir=tmp_path,
    )

    assert len(plan) == 3
    assert plan[0].kind == "base"
    assert plan[1].kind == "gear"
    assert plan[1].slot == "Helmet"
    assert plan[2].kind == "fx"


def test_resolve_tier_fx_aliases_godlike_to_celestial(tmp_path: Path) -> None:
    theme_root = tmp_path / "icons" / "heroes" / "robot"
    _write_svg(theme_root / "hero_base.svg")
    _write_svg(theme_root / "fx" / "tier_celestial.svg")

    fx = resolve_hero_tier_fx_layer(
        story_theme="robot",
        power_tier="godlike",
        base_dir=tmp_path,
    )
    assert fx is not None
    assert fx.name == "tier_celestial.svg"


def test_resolve_layer_target_rect_keeps_full_canvas_for_canonical_svg(tmp_path: Path) -> None:
    svg = tmp_path / "full.svg"
    _write_svg(svg, viewbox="0 0 180 220")
    renderer = QSvgRenderer(str(svg))
    layer = HeroLayer(path=svg, kind="gear", slot="Helmet")
    target = QtCore.QRectF(0, 0, 180, 220)

    rect = resolve_layer_target_rect(layer=layer, renderer=renderer, target_rect=target, manifest={})

    assert abs(rect.x() - 0.0) < 0.01
    assert abs(rect.y() - 0.0) < 0.01
    assert abs(rect.width() - 180.0) < 0.01
    assert abs(rect.height() - 220.0) < 0.01


def test_resolve_layer_target_rect_auto_fits_noncanonical_gear(tmp_path: Path) -> None:
    svg = tmp_path / "helmet_partial.svg"
    _write_svg(svg, viewbox="0 0 60 30")
    renderer = QSvgRenderer(str(svg))
    layer = HeroLayer(path=svg, kind="gear", slot="Helmet")
    target = QtCore.QRectF(0, 0, 180, 220)

    rect = resolve_layer_target_rect(layer=layer, renderer=renderer, target_rect=target, manifest={})

    assert rect.width() < target.width()
    assert rect.height() < target.height()
    # Helmet region should stay near top section of canvas.
    assert rect.y() < (target.height() * 0.45)


def test_resolve_layer_target_rect_honors_manifest_override_box_anchor_offset(tmp_path: Path) -> None:
    svg = tmp_path / "helmet_partial.svg"
    _write_svg(svg, viewbox="0 0 60 30")
    renderer = QSvgRenderer(str(svg))
    layer = HeroLayer(path=svg, kind="gear", slot="Helmet")
    target = QtCore.QRectF(0, 0, 180, 220)
    manifest = {
        "layout": {
            "gear": {
                "helmet": {
                    "fit": "contain",
                    "anchor": "top_left",
                    "box": [0.10, 0.10, 0.20, 0.20],
                    "offset": [0.10, 0.00],
                }
            }
        }
    }

    rect = resolve_layer_target_rect(layer=layer, renderer=renderer, target_rect=target, manifest=manifest)

    # box x starts at 18; offset adds 18 => expected x ~= 36
    assert abs(rect.x() - 36.0) < 0.5
    # top-left anchored should keep y at box top (~22)
    assert abs(rect.y() - 22.0) < 0.5


def test_validate_theme_pack_reports_base_and_slot_candidates(tmp_path: Path) -> None:
    theme_root = tmp_path / "icons" / "heroes" / "thief"
    _write_svg(theme_root / "hero_base.svg")
    _write_svg(theme_root / "gear" / "weapon" / "weapon_common.svg")

    report = validate_hero_svg_theme_pack("thief", base_dir=tmp_path)
    assert report["base_exists"] is True
    assert report["is_ready"] is True
    assert "weapon_common.svg" in report["slot_candidates"]["Weapon"]


def test_resolve_base_layer_with_default_names(tmp_path: Path) -> None:
    theme_root = tmp_path / "icons" / "heroes" / "space_pirate"
    _write_svg(theme_root / "hero.svg")
    base_layer = resolve_hero_base_layer("space_pirate", base_dir=tmp_path)
    assert base_layer is not None
    assert base_layer.name == "hero.svg"
