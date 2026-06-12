#!/usr/bin/env python3
"""Shared helpers for hero SVG pack generators.

All gear renders 1:1 on the canonical 180x220 hero canvas, so builders here
take absolute canvas coordinates. Animations must satisfy
tools/lint_hero_svg_animations.py: animateTransform for transforms,
matched values/keyTimes cardinality, dur >= 0.2s, and a presentable
static first frame.
"""

from __future__ import annotations

from pathlib import Path

RARITIES = ["common", "uncommon", "rare", "epic", "legendary", "celestial"]

RARITY_COLORS = {
    "common": "#9E9E9E",
    "uncommon": "#4CAF50",
    "rare": "#2196F3",
    "epic": "#9C27B0",
    "legendary": "#FF9800",
    "celestial": "#00E5FF",
}

# Lighter companions for highlights / inner glows per rarity.
RARITY_LIGHT = {
    "common": "#cfcfcf",
    "uncommon": "#a5d6a7",
    "rare": "#90caf9",
    "epic": "#ce93d8",
    "legendary": "#ffcc80",
    "celestial": "#b2f4ff",
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def wrap(body: str, defs: str = "") -> str:
    defs_block = f"  <defs>\n{defs}\n  </defs>\n" if defs.strip() else ""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220" width="180" height="220">\n'
        f"{defs_block}{body}\n"
        "</svg>"
    )


def linear_gradient(gid: str, stops: list[tuple[str, str]], x1=0, y1=0, x2=0, y2=1) -> str:
    rows = "\n".join(
        f'      <stop offset="{off}" stop-color="{color}"/>' for off, color in stops
    )
    return (
        f'    <linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">\n'
        f"{rows}\n    </linearGradient>"
    )


def radial_gradient(gid: str, stops: list[tuple[str, str, float]]) -> str:
    rows = "\n".join(
        f'      <stop offset="{off}" stop-color="{color}" stop-opacity="{op}"/>'
        for off, color, op in stops
    )
    return (
        f'    <radialGradient id="{gid}" cx="0.5" cy="0.5" r="0.5">\n'
        f"{rows}\n    </radialGradient>"
    )


def glow_pulse(cx, cy, rx, ry, color, dur="3.2s", omin=0.18, omax=0.42) -> str:
    """Soft breathing halo ellipse (static first frame at mid opacity)."""
    mid = round((omin + omax) / 2, 3)
    return (
        f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{color}" opacity="{mid}">'
        f'<animate attributeName="opacity" values="{mid};{omax};{omin};{mid}" dur="{dur}" repeatCount="indefinite"/>'
        "</ellipse>"
    )


def shimmer_line(x1, y1, x2, y2, color, width=1.0, dur="2.8s", omin=0.3, omax=0.95) -> str:
    """Edge line whose brightness slowly travels between two opacities."""
    mid = round((omin + omax) / 2, 3)
    return (
        f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{color}" stroke-width="{width}" '
        f'stroke-linecap="round" opacity="{mid}">'
        f'<animate attributeName="opacity" values="{mid};{omax};{omin};{mid}" dur="{dur}" repeatCount="indefinite"/>'
        "</path>"
    )


def ember(cx, cy, r, color, rise=9.0, dur="2.6s", begin="0s") -> str:
    """Small particle drifting upward and fading, looping."""
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="0.75">'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0 0;0 {-rise}" dur="{dur}" begin="{begin}" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0.75;0.9;0" dur="{dur}" begin="{begin}" repeatCount="indefinite"/>'
        "</circle>"
    )


def orbit_glint(cx, cy, orbit_r, dot_r, color, dur="8s") -> str:
    """A glint dot circling a center point (rotate transform keeps lint happy)."""
    return (
        f'<g><animateTransform attributeName="transform" type="rotate" '
        f'values="0 {cx} {cy};360 {cx} {cy}" dur="{dur}" repeatCount="indefinite"/>'
        f'<circle cx="{cx + orbit_r}" cy="{cy}" r="{dot_r}" fill="{color}" opacity="0.9"/>'
        f'<circle cx="{cx + orbit_r}" cy="{cy}" r="{dot_r * 2.1}" fill="{color}" opacity="0.25"/>'
        "</g>"
    )


def constellation(points: list[tuple[float, float]], color, line_color=None, dot_r=0.85) -> str:
    """Star dots joined by hairlines, with a slow twinkle on alternating dots."""
    line_color = line_color or color
    parts = []
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        parts.append(
            f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{line_color}" '
            'stroke-width="0.45" opacity="0.5"/>'
        )
    for i, (x, y) in enumerate(points):
        if i % 2 == 0:
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="{dot_r}" fill="{color}" opacity="0.85">'
                f'<animate attributeName="opacity" values="0.85;0.3;0.85" dur="{2.2 + 0.4 * i}s" '
                'repeatCount="indefinite"/></circle>'
            )
        else:
            parts.append(f'<circle cx="{x}" cy="{y}" r="{dot_r}" fill="{color}" opacity="0.7"/>')
    return "".join(parts)


def rivets(coords: list[tuple[float, float]], r=0.9, fill="#aab4c4", shadow="#2c3848") -> str:
    parts = []
    for x, y in coords:
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>')
        parts.append(f'<circle cx="{x + 0.25}" cy="{y + 0.3}" r="{r * 0.45}" fill="{shadow}" opacity="0.55"/>')
    return "".join(parts)


def scratches(segs: list[tuple[float, float, float, float]], color="#1d2735", width=0.55, opacity=0.6) -> str:
    return "".join(
        f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{color}" stroke-width="{width}" '
        f'opacity="{opacity}" stroke-linecap="round"/>'
        for x1, y1, x2, y2 in segs
    )


def rune_strip(x, y, count, color, step=4.2, height=2.6, opacity=0.85) -> str:
    """A row of tiny angular rune marks."""
    glyphs = []
    shapes = [
        "M{0} {1} L{0} {2} M{0} {3} L{4} {1}",
        "M{0} {1} L{4} {2} M{4} {1} L{0} {2}",
        "M{0} {2} L{0} {1} L{4} {1}",
        "M{0} {1} L{4} {1} L{0} {2} L{4} {2}",
    ]
    for i in range(count):
        gx = x + i * step
        top = y
        bot = y + height
        midy = y + height / 2
        tpl = shapes[i % len(shapes)]
        glyphs.append(tpl.format(round(gx, 2), top, bot, midy, round(gx + 1.8, 2)))
    d = " ".join(glyphs)
    return (
        f'<path d="{d}" stroke="{color}" stroke-width="0.55" fill="none" '
        f'opacity="{opacity}" stroke-linecap="round"/>'
    )
