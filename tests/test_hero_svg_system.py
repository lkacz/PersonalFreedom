from pathlib import Path

import hero_svg_system
from PySide6 import QtCore
from PySide6.QtSvg import QSvgRenderer

from hero_svg_system import (
    HeroLayer,
    build_hero_layer_plan,
    generate_hero_composed_html,
    load_hero_manifest,
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
    assert plan[0].kind == "fx"
    assert plan[1].kind == "base"
    assert plan[2].kind == "gear"
    assert plan[2].slot == "Helmet"


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


def test_resolve_layer_target_rect_applies_saved_composition_profile(tmp_path: Path) -> None:
    theme_root = tmp_path / "icons" / "heroes" / "robot"
    _write_svg(theme_root / "hero_base.svg")
    gear_path = theme_root / "gear" / "helmet" / "helmet_common.svg"
    _write_svg(gear_path, viewbox="0 0 180 220")

    profile_path = tmp_path / "artifacts" / "hero_composition" / "robot_composition_profile.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        """
{
  "theme": "robot",
  "schema_version": 2,
  "slots": {
    "Helmet": {
      "active_rarity": "Common",
      "visible": true,
      "rarities": {
        "Common": {
          "offset_x": 0.1,
          "offset_y": 0.05,
          "scale_x": 0.5,
          "scale_y": 0.5,
          "rotation_deg": 0.0,
          "visible": true,
          "rarity": "Common"
        }
      }
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    manifest = load_hero_manifest("robot", base_dir=tmp_path)
    renderer = QSvgRenderer(str(gear_path))
    layer = HeroLayer(path=gear_path, kind="gear", slot="Helmet", rarity="common")
    target = QtCore.QRectF(0, 0, 180, 220)

    rect = resolve_layer_target_rect(
        layer=layer,
        renderer=renderer,
        target_rect=target,
        manifest=manifest,
        base_dir=tmp_path,
    )

    # Full-canvas canonical source scaled 0.5 around center, then offset by +10% x and +5% y.
    assert abs(rect.x() - 63.0) < 0.5
    assert abs(rect.y() - 66.0) < 0.5
    assert abs(rect.width() - 90.0) < 0.5
    assert abs(rect.height() - 110.0) < 0.5


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


def test_generate_hero_composed_html_inlines_svg_layers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(hero_svg_system, "_INLINE_SVG_COMPOSITION_ENABLED", True)

    theme_root = tmp_path / "icons" / "heroes" / "robot"
    theme_root.mkdir(parents=True, exist_ok=True)
    (theme_root / "hero_base.svg").write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
  <defs>
    <linearGradient id="grad"><stop offset="0%" stop-color="#fff"/></linearGradient>
  </defs>
  <rect id="body" x="0" y="0" width="180" height="220" fill="url(#grad)"/>
</svg>
""".strip(),
        encoding="utf-8",
    )
    (theme_root / "gear" / "helmet").mkdir(parents=True, exist_ok=True)
    (theme_root / "gear" / "helmet" / "helmet_common.svg").write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
  <defs>
    <linearGradient id="grad"><stop offset="100%" stop-color="#000"/></linearGradient>
  </defs>
  <rect id="visor" x="70" y="20" width="40" height="20" fill="url(#grad)"/>
</svg>
""".strip(),
        encoding="utf-8",
    )

    html = generate_hero_composed_html(
        story_theme="robot",
        equipped={"Helmet": {"rarity": "Common"}},
        power_tier=None,
        base_dir=tmp_path,
    )

    assert "<img" not in html
    assert '<div class="layer svg-layer"' in html
    assert 'id="layer0_base_grad"' in html
    assert 'id="layer1_gear_helmet_grad"' in html
    assert 'url(#layer0_base_grad)' in html
    assert 'url(#layer1_gear_helmet_grad)' in html
    assert 'preserveAspectRatio="none"' in html


def test_generate_hero_composed_html_namespaces_smil_timing_refs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(hero_svg_system, "_INLINE_SVG_COMPOSITION_ENABLED", True)

    theme_root = tmp_path / "icons" / "heroes" / "thief"
    theme_root.mkdir(parents=True, exist_ok=True)
    (theme_root / "hero_base.svg").write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
  <g id="spark">
    <animate id="pulse" attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>
  </g>
  <circle id="orb" cx="90" cy="110" r="20" opacity="0.8">
    <animate begin="pulse.end+0.2s" attributeName="opacity" values="1;0.2;1" dur="1s" repeatCount="indefinite"/>
  </circle>
</svg>
""".strip(),
        encoding="utf-8",
    )

    html = generate_hero_composed_html(
        story_theme="thief",
        equipped={},
        power_tier=None,
        base_dir=tmp_path,
    )

    assert 'id="layer0_base_pulse"' in html
    assert 'begin="layer0_base_pulse.end+0.2s"' in html


def test_runtime_budget_drops_fx_animations_before_base(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(hero_svg_system, "_INLINE_SVG_COMPOSITION_ENABLED", True)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_SVG_BUDGETS_ENABLED", True)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_MAX_ANIMATIONS", 1)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_MAX_HEAVY_FILTERS", 99)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_MAX_BLUR_FILTERS", 99)

    theme_root = tmp_path / "icons" / "heroes" / "robot"
    (theme_root / "fx").mkdir(parents=True, exist_ok=True)
    (theme_root / "hero_base.svg").write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
  <rect x="0" y="0" width="180" height="220" fill="#111">
    <animate id="basePulse" attributeName="opacity" values="1;0.9;1" dur="3s" repeatCount="indefinite"/>
  </rect>
</svg>
""".strip(),
        encoding="utf-8",
    )
    (theme_root / "fx" / "tier_legendary.svg").write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
  <circle id="fxRing" cx="90" cy="110" r="70" fill="#f80" opacity="0.2">
    <animate id="fxPulseA" attributeName="opacity" values="0.2;0.9;0.2" dur="0.4s" repeatCount="indefinite"/>
  </circle>
  <circle cx="90" cy="110" r="55" fill="#ff0" opacity="0.2">
    <animate id="fxPulseB" attributeName="opacity" values="0.2;0.7;0.2" dur="0.5s" repeatCount="indefinite"/>
  </circle>
</svg>
""".strip(),
        encoding="utf-8",
    )

    html = generate_hero_composed_html(
        story_theme="robot",
        equipped={},
        power_tier="legendary",
        base_dir=tmp_path,
    )

    assert 'id="layer1_base_basePulse"' in html
    assert "layer0_fx_fxPulseA" not in html
    assert "layer0_fx_fxPulseB" not in html


def test_runtime_budget_drops_heavy_filters_from_low_priority_layers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(hero_svg_system, "_INLINE_SVG_COMPOSITION_ENABLED", True)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_SVG_BUDGETS_ENABLED", True)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_MAX_ANIMATIONS", 99)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_MAX_HEAVY_FILTERS", 0)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_MAX_BLUR_FILTERS", 99)

    theme_root = tmp_path / "icons" / "heroes" / "thief"
    (theme_root / "fx").mkdir(parents=True, exist_ok=True)
    (theme_root / "hero_base.svg").write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
  <rect id="body" x="0" y="0" width="180" height="220" fill="#222"/>
</svg>
""".strip(),
        encoding="utf-8",
    )
    (theme_root / "fx" / "tier_celestial.svg").write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
  <defs>
    <filter id="warpFx">
      <feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="2"/>
      <feDisplacementMap in="SourceGraphic" scale="8"/>
    </filter>
  </defs>
  <rect id="fxPlate" x="10" y="10" width="160" height="200" fill="#0ff" filter="url(#warpFx)" opacity="0.2"/>
</svg>
""".strip(),
        encoding="utf-8",
    )

    html = generate_hero_composed_html(
        story_theme="thief",
        equipped={},
        power_tier="celestial",
        base_dir=tmp_path,
    )

    assert "feTurbulence" not in html
    assert "feDisplacementMap" not in html
    assert "warpFx" not in html
    assert 'id="layer0_fx_fxPlate"' in html


def test_runtime_budget_preserves_celestial_gear_heavy_filters_before_non_celestial(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(hero_svg_system, "_INLINE_SVG_COMPOSITION_ENABLED", True)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_SVG_BUDGETS_ENABLED", True)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_MAX_ANIMATIONS", 99)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_MAX_HEAVY_FILTERS", 1)
    monkeypatch.setattr(hero_svg_system, "_RUNTIME_MAX_BLUR_FILTERS", 99)

    theme_root = tmp_path / "icons" / "heroes" / "thief"
    (theme_root / "fx").mkdir(parents=True, exist_ok=True)
    (theme_root / "gear" / "amulet").mkdir(parents=True, exist_ok=True)
    (theme_root / "gear" / "shield").mkdir(parents=True, exist_ok=True)
    (theme_root / "hero_base.svg").write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
  <rect id="body" x="0" y="0" width="180" height="220" fill="#111"/>
</svg>
""".strip(),
        encoding="utf-8",
    )
    (theme_root / "fx" / "tier_celestial.svg").write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
  <defs>
    <filter id="warpFx"><feTurbulence type="fractalNoise" baseFrequency="0.02"/></filter>
  </defs>
  <rect id="fxLayer" x="10" y="10" width="160" height="200" fill="#0ff" filter="url(#warpFx)" opacity="0.2"/>
</svg>
""".strip(),
        encoding="utf-8",
    )
    (theme_root / "gear" / "amulet" / "amulet_celestial.svg").write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
  <defs>
    <filter id="warpAmulet"><feTurbulence type="fractalNoise" baseFrequency="0.03"/></filter>
  </defs>
  <circle id="amuletCore" cx="90" cy="100" r="14" fill="#8df" filter="url(#warpAmulet)"/>
</svg>
""".strip(),
        encoding="utf-8",
    )
    (theme_root / "gear" / "shield" / "shield_common.svg").write_text(
        """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220">
  <defs>
    <filter id="warpShield"><feTurbulence type="fractalNoise" baseFrequency="0.04"/></filter>
  </defs>
  <rect id="shieldPlate" x="30" y="80" width="40" height="60" fill="#8a8" filter="url(#warpShield)"/>
</svg>
""".strip(),
        encoding="utf-8",
    )

    html = generate_hero_composed_html(
        story_theme="thief",
        equipped={
            "Amulet": {"rarity": "Celestial"},
            "Shield": {"rarity": "Common"},
        },
        power_tier="celestial",
        base_dir=tmp_path,
    )

    assert "layer2_gear_amulet_warpAmulet" in html
    assert "layer0_fx_warpFx" not in html
    assert "layer3_gear_shield_warpShield" not in html
