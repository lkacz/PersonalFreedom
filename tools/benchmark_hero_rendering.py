"""
Benchmark hero rendering paths and emit a markdown baseline report.

Usage:
  python tools/benchmark_hero_rendering.py --iterations 120 --output-md artifacts/hero_perf_baseline.md
"""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Optional

from PySide6 import QtGui, QtWidgets

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from hero_svg_system import (
    HERO_CANVAS_HEIGHT,
    HERO_CANVAS_WIDTH,
    generate_hero_composed_html,
    render_hero_svg_character,
)


_SLOT_ORDER = (
    ("Helmet", "helmet"),
    ("Chestplate", "chestplate"),
    ("Gauntlets", "gauntlets"),
    ("Boots", "boots"),
    ("Shield", "shield"),
    ("Weapon", "weapon"),
    ("Cloak", "cloak"),
    ("Amulet", "amulet"),
)


def _ensure_qt_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    q = max(0.0, min(100.0, float(q)))
    rank = (len(sorted_values) - 1) * (q / 100.0)
    lower = int(rank)
    upper = min(len(sorted_values) - 1, lower + 1)
    weight = rank - float(lower)
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def _summarize_ms(samples: list[float]) -> dict:
    if not samples:
        return {"count": 0, "avg_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0}
    return {
        "count": len(samples),
        "avg_ms": statistics.fmean(samples),
        "p95_ms": _percentile(samples, 95.0),
        "max_ms": max(samples),
    }


def _discover_item(theme_dir: Path, slot_slug: str, rarity_slug: str) -> Optional[dict]:
    slot_dir = theme_dir / "gear" / slot_slug
    if not slot_dir.exists():
        return None

    preferred = sorted(slot_dir.glob(f"*_{rarity_slug}.svg"))
    candidates = preferred or sorted(slot_dir.glob("*.svg"))
    if not candidates:
        return None

    selected = candidates[0]
    stem = selected.stem
    suffix = f"_{rarity_slug}"
    if stem.endswith(suffix):
        item_type_slug = stem[: -len(suffix)]
    else:
        item_type_slug = stem
    item_name = item_type_slug.replace("_", " ").title()
    return {
        "item_type": item_type_slug,
        "name": item_name,
        "rarity": rarity_slug.title(),
    }


def _build_equipped(theme_dir: Path, rarity_slug: str) -> dict:
    equipped = {}
    for slot_name, slot_slug in _SLOT_ORDER:
        item = _discover_item(theme_dir, slot_slug, rarity_slug)
        if item:
            equipped[slot_name] = item
    return equipped


def _benchmark_html(theme: str, equipped: dict, tier: str, iterations: int) -> tuple[dict, int]:
    samples: list[float] = []
    html_size = 0
    _ = generate_hero_composed_html(theme, equipped, power_tier=tier)
    for _i in range(iterations):
        start = time.perf_counter()
        html = generate_hero_composed_html(theme, equipped, power_tier=tier)
        samples.append((time.perf_counter() - start) * 1000.0)
        html_size = len(html)
    return _summarize_ms(samples), html_size


def _benchmark_fallback_paint(theme: str, equipped: dict, tier: str, iterations: int) -> dict:
    samples: list[float] = []
    image = QtGui.QImage(
        HERO_CANVAS_WIDTH,
        HERO_CANVAS_HEIGHT,
        QtGui.QImage.Format_ARGB32_Premultiplied,
    )
    for _i in range(iterations):
        image.fill(0)
        painter = QtGui.QPainter(image)
        try:
            start = time.perf_counter()
            render_hero_svg_character(
                painter,
                story_theme=theme,
                equipped=equipped,
                power_tier=tier,
                canvas_width=HERO_CANVAS_WIDTH,
                canvas_height=HERO_CANVAS_HEIGHT,
            )
            samples.append((time.perf_counter() - start) * 1000.0)
        finally:
            painter.end()
    return _summarize_ms(samples)


def _collect_rows(
    themes: list[str],
    tiers: list[str],
    iterations: int,
    include_fallback: bool,
) -> list[dict]:
    rows: list[dict] = []
    heroes_root = ROOT_DIR / "icons" / "heroes"

    for theme in themes:
        theme_dir = heroes_root / theme
        if not theme_dir.exists():
            continue
        for tier in tiers:
            rarity = "celestial" if tier in {"godlike", "celestial"} else "legendary"
            equipped = _build_equipped(theme_dir, rarity)
            html_stats, html_size = _benchmark_html(theme, equipped, tier, iterations)
            row = {
                "theme": theme,
                "tier": tier,
                "equipped_slots": len(equipped),
                "html_size": html_size,
                "html_avg_ms": html_stats["avg_ms"],
                "html_p95_ms": html_stats["p95_ms"],
                "html_max_ms": html_stats["max_ms"],
            }
            if include_fallback:
                fallback_stats = _benchmark_fallback_paint(theme, equipped, tier, max(20, iterations // 2))
                row.update(
                    {
                        "fallback_avg_ms": fallback_stats["avg_ms"],
                        "fallback_p95_ms": fallback_stats["p95_ms"],
                        "fallback_max_ms": fallback_stats["max_ms"],
                    }
                )
            rows.append(row)
    return rows


def _render_markdown(rows: list[dict], iterations: int, include_fallback: bool) -> str:
    lines = [
        "# Hero Rendering Baseline",
        "",
        f"- Iterations per scenario: `{iterations}`",
        f"- Inline SVG composition: `{os.environ.get('PF_HERO_INLINE_SVG_COMPOSITION', '1')}`",
        f"- Runtime budgets: `{os.environ.get('PF_HERO_RUNTIME_BUDGETS', '1')}`",
        "",
    ]
    if include_fallback:
        lines.append(
            "| Theme | Tier | Slots | HTML Size | HTML Avg ms | HTML p95 ms | HTML Max ms | Fallback Avg ms | Fallback p95 ms | Fallback Max ms |"
        )
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for row in rows:
            lines.append(
                f"| {row['theme']} | {row['tier']} | {row['equipped_slots']} | {row['html_size']} | "
                f"{row['html_avg_ms']:.2f} | {row['html_p95_ms']:.2f} | {row['html_max_ms']:.2f} | "
                f"{row.get('fallback_avg_ms', 0.0):.2f} | {row.get('fallback_p95_ms', 0.0):.2f} | {row.get('fallback_max_ms', 0.0):.2f} |"
            )
    else:
        lines.append("| Theme | Tier | Slots | HTML Size | HTML Avg ms | HTML p95 ms | HTML Max ms |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for row in rows:
            lines.append(
                f"| {row['theme']} | {row['tier']} | {row['equipped_slots']} | {row['html_size']} | "
                f"{row['html_avg_ms']:.2f} | {row['html_p95_ms']:.2f} | {row['html_max_ms']:.2f} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark hero rendering paths.")
    parser.add_argument("--iterations", type=int, default=100, help="Iterations per scenario.")
    parser.add_argument(
        "--themes",
        nargs="*",
        default=["thief", "space_pirate", "robot", "zoo_worker"],
        help="Hero themes to benchmark.",
    )
    parser.add_argument(
        "--tiers",
        nargs="*",
        default=["legendary", "godlike"],
        help="Power tiers to benchmark.",
    )
    parser.add_argument(
        "--include-fallback-render",
        action="store_true",
        help="Also benchmark fallback QPainter/QSvgRenderer rendering path.",
    )
    parser.add_argument("--output-md", type=str, default="", help="Optional markdown output path.")
    args = parser.parse_args()

    _ensure_qt_app()
    rows = _collect_rows(
        themes=[str(t) for t in args.themes],
        tiers=[str(t) for t in args.tiers],
        iterations=max(1, int(args.iterations)),
        include_fallback=bool(args.include_fallback_render),
    )
    md = _render_markdown(
        rows=rows,
        iterations=max(1, int(args.iterations)),
        include_fallback=bool(args.include_fallback_render),
    )
    print(md)
    if args.output_md:
        out_path = Path(args.output_md)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        print(f"[saved] {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
