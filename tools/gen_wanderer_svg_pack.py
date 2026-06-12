#!/usr/bin/env python3
"""Regenerate complete wanderer hero SVG pack with fit-aligned rarity progression.

Art direction: the Dreamweaver. Rarity arc rises from half-remembered,
fraying dreamwear through lucid silver, astral blue, nebula violet,
gold dawn-dream regalia, up to a living-constellation celestial set.
Slot semantics: Shield = dreamcatcher ward, Weapon = crescent dream staff,
Amulet = moon crystal, Helmet = dream circlet. Footprints match the
established hero body anchors.
"""

from __future__ import annotations

from pathlib import Path

try:
    from svg_pack_common import (
        RARITIES, RARITY_COLORS, RARITY_LIGHT,
        write, wrap, linear_gradient, radial_gradient,
        glow_pulse, shimmer_line, ember, orbit_glint,
        constellation, rivets, scratches, rune_strip,
    )
except ImportError:
    from tools.svg_pack_common import (
        RARITIES, RARITY_COLORS, RARITY_LIGHT,
        write, wrap, linear_gradient, radial_gradient,
        glow_pulse, shimmer_line, ember, orbit_glint,
        constellation, rivets, scratches, rune_strip,
    )

ROOT = Path("icons/heroes/wanderer")

# Weave face, weave shadow, outline, highlight, moon-metal trim.
PAL = {
    "common": {
        "weave": "#474e66", "shadow": "#333949", "edge": "#23283a",
        "hi": "#6f7791", "trim": "#8d96ad",
    },
    "uncommon": {
        "weave": "#46557a", "shadow": "#323d59", "edge": "#222b42",
        "hi": "#7b8cb2", "trim": "#9fb4d8",
    },
    "rare": {
        "weave": "#3c4f7d", "shadow": "#2a385c", "edge": "#1c2742",
        "hi": "#84a0d8", "trim": "#aac6f2",
    },
    "epic": {
        "weave": "#473a68", "shadow": "#33294c", "edge": "#221b36",
        "hi": "#9a86c6", "trim": "#c79be8",
    },
    "legendary": {
        "weave": "#5d5037", "shadow": "#423823", "edge": "#2e2716",
        "hi": "#cfa75f", "trim": "#ffd58a",
    },
    "celestial": {
        "weave": "#37596c", "shadow": "#264250", "edge": "#18303d",
        "hi": "#7fd2e4", "trim": "#9beefc",
    },
}


def tier_defs(rarity: str, prefix: str) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    parts = [
        linear_gradient(f"{prefix}Weave", [("0%", p["hi"]), ("45%", p["weave"]), ("100%", p["shadow"])]),
        linear_gradient(f"{prefix}Deep", [("0%", p["weave"]), ("100%", p["edge"])]),
    ]
    if rarity in ("epic", "legendary", "celestial"):
        parts.append(radial_gradient(f"{prefix}Aura", [("0%", c, 0.5), ("70%", c, 0.16), ("100%", c, 0.0)]))
    return "\n".join(parts)


def star4(cx, cy, r, color, opacity=0.9) -> str:
    """Four-point dream star."""
    return (
        f'<path d="M{cx} {cy - r} L{cx + r * 0.28} {cy - r * 0.28} L{cx + r} {cy} '
        f'L{cx + r * 0.28} {cy + r * 0.28} L{cx} {cy + r} L{cx - r * 0.28} {cy + r * 0.28} '
        f'L{cx - r} {cy} L{cx - r * 0.28} {cy - r * 0.28} Z" fill="{color}" opacity="{opacity}"/>'
    )


def crescent(cx, cy, r, color, opacity=0.95, tilt=0) -> str:
    """Crescent moon via two arcs."""
    transform = f' transform="rotate({tilt} {cx} {cy})"' if tilt else ""
    return (
        f'<path d="M{cx - r * 0.2} {cy - r} A{r} {r} 0 1 0 {cx - r * 0.2} {cy + r} '
        f'A{r * 0.78} {r * 0.78} 0 1 1 {cx - r * 0.2} {cy - r} Z" '
        f'fill="{color}" opacity="{opacity}"{transform}/>'
    )


# ---------------------------------------------------------------------------
# HELMET — dream circlet: band over the brow, crescent centerpiece,
# floating star points at higher tiers. Footprint: x66-114, y28-52.
# ---------------------------------------------------------------------------

def helmet_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"dCirc{idx}"

    details = []
    if idx == 0:
        details.append(f'<path d="M73 41.5 L78 43" stroke="{p["edge"]}" stroke-width="0.8" opacity="0.8"/>')  # bent band
        details.append(f'<path d="M101 40.2 Q104 41.6 106.5 41" stroke="{p["shadow"]}" stroke-width="0.7" fill="none" opacity="0.85"/>')
    if idx >= 1:
        details.append(crescent(90, 36.4, 4.4, p["trim"], opacity=0.95, tilt=18))
    if idx >= 2:
        details.append(star4(76.5, 36.2, 2.2, lc, 0.85))
        details.append(star4(103.5, 36.2, 2.2, lc, 0.85))
        details.append(shimmer_line(70, 43.8, 110, 43.8, lc, width=0.7, dur="3.5s", omin=0.25, omax=0.75))
    if idx >= 3:
        details.append(
            f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -2.6;0 0" dur="3.4s" repeatCount="indefinite"/>'
            + star4(70, 29.5, 1.9, c, 0.9)
            + star4(110, 29.5, 1.9, c, 0.9)
            + "</g>"
        )
    if idx >= 4:
        details.append(
            f'<path d="M84 30.5 Q90 25 96 30.5" stroke="{c}" stroke-width="1" fill="none" opacity="0.75">'
            f'<animate attributeName="opacity" values="0.75;1;0.5;0.75" dur="2.6s" repeatCount="indefinite"/></path>'
        )
        details.append(ember(85, 31, 0.65, lc, rise=6, dur="2.7s"))
        details.append(ember(95.5, 30.5, 0.6, c, rise=7, dur="3.2s", begin="1s"))
    if idx == 5:
        details.append(glow_pulse(90, 38, 29, 11, f"url(#{g}Aura)", dur="4.1s", omin=0.35, omax=0.75))
        details.append(constellation([(73, 32), (81.5, 28.6), (90, 27.4), (98.5, 28.6), (107, 32)], lc))
        details.append(orbit_glint(90, 38, 25, 1.0, lc, dur="9.5s"))

    body = f"""
  <g id="helmet_{rarity}">
    <path d="M68 42.5 Q90 34.5 112 42.5 L111.4 46.4 Q90 39.4 68.6 46.4 Z"
          fill="url(#{g}Weave)" stroke="{p["edge"]}" stroke-width="1"/>
    <path d="M70 43.6 Q90 36.8 110 43.6" stroke="{p["hi"]}" stroke-width="0.7" fill="none" opacity="0.7"/>
    <circle cx="78" cy="40.6" r="1" fill="{p["trim"]}" opacity="0.9"/>
    <circle cx="102" cy="40.6" r="1" fill="{p["trim"]}" opacity="0.9"/>
    <circle cx="90" cy="38.6" r="1.5" fill="{c}" opacity="0.95"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# CHESTPLATE — starweave vestments: wrap front, sash, moon-phase buttons.
# Footprint: x64-116, y76-146.
# ---------------------------------------------------------------------------

def chestplate_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"dVest{idx}"

    details = []
    # Moon-phase button column: new, half, full.
    details.append(
        f'<circle cx="90" cy="97" r="1.5" fill="{p["shadow"]}" stroke="{p["trim"]}" stroke-width="0.5"/>'
        f'<path d="M90 106.5 A1.5 1.5 0 0 1 90 109.5 Z" fill="{p["trim"]}"/><circle cx="90" cy="108" r="1.5" fill="none" stroke="{p["trim"]}" stroke-width="0.5"/>'
        f'<circle cx="90" cy="119" r="1.5" fill="{p["trim"]}"/>'
    )
    if idx == 0:
        details.append(f'<path d="M75 132 L79 136 M77.5 131.5 L74 135" stroke="{p["edge"]}" stroke-width="0.6" opacity="0.7"/>')  # frayed cross-stitch
        details.append(f'<path d="M101 88 Q104 90 106 88.5 L105 92 Q102 91 101 88 Z" fill="{p["shadow"]}" opacity="0.8"/>')
    if idx >= 1:
        # Night sash.
        details.append(
            f'<path d="M68 124 Q90 132 112 124 L112 130.5 Q90 138.5 68 130.5 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.8"/>'
            f'<path d="M70 126.5 Q90 134 110 126.5" stroke="{p["trim"]}" stroke-width="0.8" fill="none" opacity="0.85"/>'
        )
    if idx >= 2:
        details.append(star4(78, 92, 1.7, lc, 0.85))
        details.append(star4(102.5, 99, 1.5, lc, 0.75))
        details.append(star4(81, 113, 1.4, lc, 0.7))
        details.append(rune_strip(76, 137.2, 6, c, step=4.4, height=2.4, opacity=0.8))
    if idx >= 3:
        details.append(crescent(101, 88.5, 3.2, c, opacity=0.9, tilt=-15))
        details.append(
            f'<path d="M71 84 Q78 79.5 86 81.5 M109 84 Q102 79.5 94 81.5" stroke="{c}" stroke-width="0.9" fill="none" opacity="0.8"/>'
        )
    if idx >= 4:
        details.append(shimmer_line(69, 92, 69, 140, c, width=0.8, dur="3.3s", omin=0.25, omax=0.75))
        details.append(shimmer_line(111, 92, 111, 140, c, width=0.8, dur="3.3s", omin=0.75, omax=0.25))
        details.append(ember(80, 104, 0.7, lc, rise=9, dur="3s"))
        details.append(ember(100, 110, 0.65, c, rise=8, dur="3.5s", begin="1.2s"))
    if idx == 5:
        details.append(glow_pulse(90, 106, 25, 18, f"url(#{g}Aura)", dur="4.6s", omin=0.3, omax=0.65))
        details.append(constellation([(76, 96), (83, 90), (92, 89.5), (100, 94), (103, 103), (97, 110), (87, 111), (79, 105), (76, 96)], lc, dot_r=0.75))
        details.append(orbit_glint(90, 104, 20, 1.0, lc, dur="10s"))

    body = f"""
  <g id="chestplate_{rarity}">
    <path d="M70 79 L110 79 Q115 86 115 97 L112 145 L68 145 L65 97 Q65 86 70 79 Z"
          fill="url(#{g}Weave)" stroke="{p["edge"]}" stroke-width="1.05"/>
    <path d="M76 82 L90 90 L90 143 L74 143 Z" fill="url(#{g}Deep)" opacity="0.85"/>
    <path d="M104 82 L90 90 L90 143 L106 143 Z" fill="url(#{g}Deep)" opacity="0.7"/>
    <path d="M76 82 L90 90 M104 82 L90 90" stroke="{p["edge"]}" stroke-width="0.8" opacity="0.85"/>
    <path d="M73 86 Q70 110 71 142 M107 86 Q110 110 109 142" stroke="{p["shadow"]}" stroke-width="0.7" fill="none" opacity="0.6"/>
    <path d="M78 84 Q84 81 89 85" stroke="{p["hi"]}" stroke-width="0.7" fill="none" opacity="0.6"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# GAUNTLETS — dream wraps: wound ribbon cuffs with trailing ends and charms.
# Footprints: left x37-63 / right x117-143, y132-158.
# ---------------------------------------------------------------------------

def gauntlets_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"dWrap{idx}"

    def one(x0: float, mirror: bool) -> str:
        xm = x0 + 13
        sgn = -1 if mirror else 1
        parts = [
            f'<path d="M{x0+2} 134 L{x0+24} 134 L{x0+23} 157 L{x0+3} 157 Z" fill="url(#{g}Weave)" stroke="{p["edge"]}" stroke-width="1"/>',
            # Diagonal ribbon winding.
            f'<path d="M{x0+2.5} 138 L{x0+23.5} 142 M{x0+2.5} 145 L{x0+23.5} 149 M{x0+2.5} 152 L{x0+23.5} 156" stroke="url(#{g}Deep)" stroke-width="3.2" opacity="0.9"/>',
            f'<path d="M{x0+2.5} 138 L{x0+23.5} 142 M{x0+2.5} 145 L{x0+23.5} 149" stroke="{p["hi"]}" stroke-width="0.5" opacity="0.5"/>',
        ]
        if idx == 0:
            # Loose trailing end.
            parts.append(
                f'<path d="M{xm + sgn * 9} 156 Q{xm + sgn * 12} 161 {xm + sgn * 10} 165" stroke="url(#{g}Deep)" stroke-width="2.4" fill="none" opacity="0.85"/>'
            )
        if idx >= 1:
            parts.append(f'<path d="M{x0+2} 141.5 L{x0+24} 145.5" stroke="{p["trim"]}" stroke-width="1" opacity="0.9"/>')
        if idx >= 2:
            parts.append(star4(xm, 137.4, 1.7, lc, 0.85))
            parts.append(rune_strip(x0 + 6, 152.6, 3, c, step=4.8, height=2.0, opacity=0.85))
        if idx >= 3:
            parts.append(crescent(xm + sgn * 6, 147, 2.2, c, opacity=0.9, tilt=sgn * 20))
        if idx >= 4:
            parts.append(
                f'<path d="M{x0+3} 156 L{x0+23} 156" stroke="{c}" stroke-width="0.9" opacity="0.5">'
                f'<animate attributeName="opacity" values="0.5;0.95;0.5" dur="2.6s" repeatCount="indefinite"/></path>'
            )
            parts.append(ember(xm + sgn * 4, 136.5, 0.6, lc, rise=6, dur="3s", begin="0.8s" if mirror else "0s"))
        if idx == 5:
            parts.append(glow_pulse(xm, 145, 13, 10, f"url(#{g}Aura)", dur="4.4s", omin=0.3, omax=0.65))
            parts.append(constellation([(x0 + 5, 137.5), (xm, 135.2), (x0 + 21, 137.5)], lc, dot_r=0.7))
        return "".join(parts)

    body = f"""
  <g id="gauntlets_{rarity}">
    {one(37, False)}
    {one(117, True)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# BOOTS — cloud walkers: soft curved boots resting on drifting cloud puffs.
# Footprints: left x41-79 / right x101-139, y184-210.
# ---------------------------------------------------------------------------

def boots_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"dCloud{idx}"

    def one(x0: float, flip: bool) -> str:
        xm = x0 + 19
        parts = [
            f'<path d="M{x0+5} 186 Q{xm} 182.5 {x0+31} 186 L{x0+33.5} 198.5 Q{xm} 194.5 {x0+2.5} 198.5 Z" fill="url(#{g}Weave)" stroke="{p["edge"]}" stroke-width="1"/>',
            f'<path d="M{x0+3} 197.6 Q{xm} 193.8 {x0+33} 197.6 L{x0+35.5} 205 Q{xm} 201.5 {x0+0.5} 205 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.9"/>',
            # Cloud puffs at the sole.
            f'<ellipse cx="{x0+8}" cy="206.4" rx="6.4" ry="2.7" fill="{p["hi"]}" opacity="0.5">'
            f'<animate attributeName="opacity" values="0.5;0.7;0.5" dur="3.2s" repeatCount="indefinite"/></ellipse>',
            f'<ellipse cx="{xm}" cy="207.6" rx="8" ry="3" fill="{p["hi"]}" opacity="0.42">'
            f'<animate attributeName="opacity" values="0.42;0.62;0.42" dur="3.8s" repeatCount="indefinite"/></ellipse>',
            f'<ellipse cx="{x0+29}" cy="206.4" rx="6" ry="2.6" fill="{p["hi"]}" opacity="0.5">'
            f'<animate attributeName="opacity" values="0.5;0.68;0.5" dur="2.9s" repeatCount="indefinite"/></ellipse>',
            f'<path d="M{x0+7} 190.5 Q{xm} 187.5 {x0+29} 190.5" stroke="{p["hi"]}" stroke-width="0.65" fill="none" opacity="0.6"/>',
        ]
        if idx == 0:
            parts.append(scratches([(x0 + 8, 199.5, x0 + 13, 202.5)], color=p["edge"], width=0.6, opacity=0.65))
        if idx >= 1:
            parts.append(f'<path d="M{x0+4} 196.8 Q{xm} 193 {x0+32} 196.8" stroke="{p["trim"]}" stroke-width="1" fill="none" opacity="0.9"/>')
        if idx >= 2:
            parts.append(star4(x0 + 29, 191.4, 1.6, lc, 0.85))
            parts.append(rune_strip(x0 + 9, 200.4, 4, c, step=4.6, height=2.0, opacity=0.75))
        if idx >= 3:
            parts.append(crescent(x0 + 8, 191.4, 2.0, c, opacity=0.9, tilt=-12))
        if idx >= 4:
            parts.append(shimmer_line(x0 + 2, 204.2, x0 + 34, 204.2, c, width=0.95, dur="2.8s", omin=0.3, omax=0.85))
            parts.append(ember(xm + (3 if flip else -3), 194, 0.55, lc, rise=7, dur="3.3s", begin="1.1s" if flip else "0s"))
        if idx == 5:
            parts.append(glow_pulse(xm, 197, 18, 8.5, f"url(#{g}Aura)", dur="4.7s", omin=0.25, omax=0.6))
            parts.append(constellation([(x0 + 8, 189), (xm, 186.6), (x0 + 30, 189)], lc, dot_r=0.65))
        return "".join(parts)

    body = f"""
  <g id="boots_{rarity}">
    {one(41, False)}
    {one(101, True)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# SHIELD — dreamcatcher ward: woven hoop, web, hanging feathers.
# Footprint: x28-66, y98-152.
# ---------------------------------------------------------------------------

def shield_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"dWard{idx}"

    cx, cy, R = 47, 119, 16.5

    # Web: spokes + two inner polygon rings.
    import math
    spokes = []
    ring1 = []
    ring2 = []
    for k in range(8):
        a = math.pi / 4 * k
        x_, y_ = cx + R * math.cos(a), cy + R * math.sin(a)
        spokes.append(f"M{cx} {cy} L{round(x_, 1)} {round(y_, 1)}")
        r1x, r1y = cx + R * 0.62 * math.cos(a + 0.39), cy + R * 0.62 * math.sin(a + 0.39)
        ring1.append((round(r1x, 1), round(r1y, 1)))
        r2x, r2y = cx + R * 0.3 * math.cos(a), cy + R * 0.3 * math.sin(a)
        ring2.append((round(r2x, 1), round(r2y, 1)))
    ring1_d = "M" + " L".join(f"{x_} {y_}" for x_, y_ in ring1) + " Z"
    ring2_d = "M" + " L".join(f"{x_} {y_}" for x_, y_ in ring2) + " Z"

    def feather(fx, fy, length, color, dur) -> str:
        return (
            f'<g><animateTransform attributeName="transform" type="rotate" '
            f'values="-3 {fx} {fy};3 {fx} {fy};-3 {fx} {fy}" dur="{dur}" repeatCount="indefinite"/>'
            f'<path d="M{fx} {fy} L{fx} {fy + length}" stroke="{p["trim"]}" stroke-width="0.7"/>'
            f'<path d="M{fx} {fy + length} Q{fx - 2.4} {fy + length + 3.5} {fx} {fy + length + 8} '
            f'Q{fx + 2.4} {fy + length + 3.5} {fx} {fy + length} Z" fill="{color}" opacity="0.9"/>'
            f'<path d="M{fx} {fy + length + 1.5} L{fx} {fy + length + 6.5}" stroke="{p["edge"]}" stroke-width="0.4" opacity="0.8"/>'
            "</g>"
        )

    details = []
    if idx == 0:
        # Torn web strand.
        details.append(f'<path d="M{cx - 4} {cy + 3} Q{cx - 7} {cy + 8} {cx - 10} {cy + 9}" stroke="{p["trim"]}" stroke-width="0.5" fill="none" opacity="0.75"/>')
    if idx >= 1:
        details.append(f'<circle cx="{cx}" cy="{cy}" r="{R - 2.4}" fill="none" stroke="{p["trim"]}" stroke-width="0.6" opacity="0.75"/>')
    if idx >= 2:
        details.append(star4(cx + 7.5, cy - 8, 1.7, lc, 0.9))
        details.append(rune_strip(cx - 9.5, cy + R + 1.8, 5, c, step=4.0, height=2.2, opacity=0.8))
    if idx >= 3:
        details.append(crescent(cx, cy, 4.2, c, opacity=0.95, tilt=20))
    if idx >= 4:
        details.append(
            f'<circle cx="{cx}" cy="{cy}" r="{R + 3.2}" fill="none" stroke="{c}" stroke-width="0.8" opacity="0.5">'
            f'<animate attributeName="opacity" values="0.5;0.95;0.5" dur="2.4s" repeatCount="indefinite"/></circle>'
        )
        details.append(ember(cx - 9, cy + 4, 0.65, lc, rise=8, dur="2.9s"))
        details.append(ember(cx + 9, cy + 7, 0.6, c, rise=7, dur="2.5s", begin="0.8s"))
    if idx == 5:
        details.append(glow_pulse(cx, cy + 6, 21, 26, f"url(#{g}Aura)", dur="4.6s", omin=0.3, omax=0.65))
        details.append(constellation([(cx - 11, cy - 10), (cx, cy - 14.5), (cx + 11, cy - 10), (cx + 13, cy + 6), (cx, cy + 14.5), (cx - 13, cy + 6), (cx - 11, cy - 10)], lc, dot_r=0.7))
        details.append(orbit_glint(cx, cy, R + 5.5, 1.0, lc, dur="9s"))

    body = f"""
  <g id="shield_{rarity}">
    <circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#{g}Deep)" fill-opacity="0.35" stroke="url(#{g}Weave)" stroke-width="3.4"/>
    <circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{p["edge"]}" stroke-width="0.8"/>
    <path d="{' '.join(spokes)}" stroke="{p["trim"]}" stroke-width="0.5" opacity="0.85"/>
    <path d="{ring1_d}" fill="none" stroke="{p["trim"]}" stroke-width="0.5" opacity="0.8"/>
    <path d="{ring2_d}" fill="none" stroke="{p["trim"]}" stroke-width="0.5" opacity="0.75"/>
    <circle cx="{cx}" cy="{cy}" r="1.6" fill="{c}" opacity="0.95"/>
    <path d="M{cx - 7} {cy - R - 1.5} Q{cx} {cy - R - 5} {cx + 7} {cy - R - 1.5}" stroke="{p["trim"]}" stroke-width="1" fill="none"/>
    {feather(cx - 9, cy + R - 3.5, 6, c, "4.2s")}
    {feather(cx, cy + R - 1, 8, lc, "5s")}
    {feather(cx + 9, cy + R - 3.5, 6, c, "4.6s")}
    <circle cx="{cx - 9}" cy="{cy + R - 2.5}" r="0.8" fill="{p["trim"]}"/>
    <circle cx="{cx}" cy="{cy + R}" r="0.8" fill="{p["trim"]}"/>
    <circle cx="{cx + 9}" cy="{cy + R - 2.5}" r="0.8" fill="{p["trim"]}"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# WEAPON — crescent dream staff on the -24° axis: shaft, crescent finial
# cradling a drifting star orb, stardust trail at higher tiers.
# ---------------------------------------------------------------------------

def weapon_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"dStaff{idx}"

    details = []
    if idx == 0:
        details.append(f'<path d="M119.5 140 Q121.5 141.5 120 144" stroke="{p["edge"]}" stroke-width="0.7" fill="none" opacity="0.85"/>')  # crack
    if idx >= 1:
        details.append(f'<path d="M118 132 L122.6 132 M118 156 L122.6 156" stroke="{p["trim"]}" stroke-width="1.4" opacity="0.95"/>')
    if idx >= 2:
        details.append(star4(137.5, 107.5, 2.6, lc, 0.95))
        details.append(
            f'<circle cx="137.5" cy="107.5" r="4.6" fill="none" stroke="{lc}" stroke-width="0.55" opacity="0.6">'
            f'<animate attributeName="opacity" values="0.6;0.2;0.6" dur="2.6s" repeatCount="indefinite"/></circle>'
        )
    if idx >= 3:
        # Stardust trail drifting off the crescent.
        details.append(
            f'<circle cx="146" cy="103" r="0.8" fill="{lc}" opacity="0.85">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;5 -6" dur="2.8s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.85;0" dur="2.8s" repeatCount="indefinite"/></circle>'
            f'<circle cx="143" cy="112" r="0.65" fill="{c}" opacity="0.75">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;6 -4" dur="3.4s" begin="1s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.75;0" dur="3.4s" begin="1s" repeatCount="indefinite"/></circle>'
        )
    if idx >= 4:
        details.append(
            f'<path d="M129 116 Q133 120 138 119" stroke="{c}" stroke-width="0.9" fill="none" opacity="0.7">'
            f'<animate attributeName="opacity" values="0.7;0.3;0.7" dur="2.2s" repeatCount="indefinite"/></path>'
        )
        details.append(ember(133, 103, 0.7, lc, rise=8, dur="2.5s"))
        details.append(ember(141, 100, 0.6, c, rise=7, dur="3s", begin="0.9s"))
    if idx == 5:
        details.append(glow_pulse(137, 107, 15, 12, f"url(#{g}Aura)", dur="3.8s", omin=0.35, omax=0.75))
        details.append(constellation([(128, 116), (133, 110), (139, 104.5), (145, 100)], lc, dot_r=0.7))
        details.append(orbit_glint(137.5, 107.5, 9.5, 0.85, lc, dur="7s"))

    body = f"""
  <g id="weapon_{rarity}" transform="rotate(-24 121 131)">
    <rect x="118.4" y="120" width="3.9" height="44" rx="1.9" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.9"/>
    <path d="M118.6 126 Q116 124 116.4 121 M122.1 126 Q124.6 124 124.2 121" stroke="{p["trim"]}" stroke-width="0.8" fill="none" opacity="0.85"/>
    <path d="M129.5 118 A11.5 11.5 0 1 1 146.5 99.5 A9 9 0 1 0 129.5 118 Z"
          fill="url(#{g}Weave)" stroke="{p["edge"]}" stroke-width="1"/>
    <circle cx="137.5" cy="107.5" r="2.4" fill="{c}" opacity="0.95"/>
    <circle cx="136.7" cy="106.6" r="0.8" fill="#ffffff" opacity="0.85"/>
    <rect x="118.9" y="161" width="2.9" height="3.8" rx="1.2" fill="url(#{g}Weave)" stroke="{p["edge"]}" stroke-width="0.6"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# CLOAK — night shroud: gradient drape with a living star field.
# Footprint: x54-126, y72-192.
# ---------------------------------------------------------------------------

def cloak_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"dShroud{idx}"

    details = []
    # Faint star field on every tier (denser per tier).
    base_stars = [(66, 104), (72, 130), (64, 158), (112, 112), (116, 144), (110, 170)]
    for i, (sx, sy) in enumerate(base_stars):
        details.append(
            f'<circle cx="{sx}" cy="{sy}" r="0.7" fill="{p["trim"]}" opacity="0.6">'
            f'<animate attributeName="opacity" values="0.6;0.2;0.6" dur="{3 + 0.45 * i}s" repeatCount="indefinite"/></circle>'
        )
    if idx == 0:
        details.append(f'<path d="M61 184 L65 190 L68.5 184 L72 189 L75 183.5 L70 181 Z" fill="url(#{g}Deep)" opacity="0.7"/>')  # frayed hem
    if idx >= 1:
        details.append(crescent(90, 79.4, 2.6, p["trim"], opacity=0.95, tilt=12))
    if idx >= 2:
        details.append(star4(70, 116, 1.6, lc, 0.8))
        details.append(star4(113, 128, 1.5, lc, 0.75))
        details.append(star4(68, 146, 1.4, lc, 0.7))
    if idx >= 3:
        # Connected constellation lines on the right panel.
        details.append(
            f'<path d="M108 104 L114 112 L112 124 L116 136" stroke="{c}" stroke-width="0.5" opacity="0.6" fill="none"/>'
        )
        details.append(star4(108, 104, 1.5, c, 0.85))
        details.append(star4(116, 136, 1.5, c, 0.85))
    if idx >= 4:
        details.append(shimmer_line(59, 100, 59, 180, c, width=0.8, dur="3.7s", omin=0.2, omax=0.7))
        details.append(shimmer_line(121, 100, 121, 180, c, width=0.8, dur="3.7s", omin=0.7, omax=0.2))
        details.append(ember(66, 162, 0.65, lc, rise=11, dur="3.6s"))
        details.append(ember(114, 154, 0.6, c, rise=10, dur="3.1s", begin="1.4s"))
    if idx == 5:
        details.append(glow_pulse(90, 134, 36, 42, f"url(#{g}Aura)", dur="5.6s", omin=0.2, omax=0.42))
        details.append(constellation([(64, 108), (69, 124), (66, 142), (71, 158), (67, 174)], lc, dot_r=0.7))
        details.append(constellation([(116, 108), (111, 124), (114, 142), (109, 158), (113, 174)], lc, dot_r=0.7))

    body = f"""
  <g id="cloak_{rarity}" opacity="0.96">
    <path d="M64 75 Q90 70 116 75 L124 92 L120 188 Q105 183 90 183 Q75 183 60 188 L56 92 Z"
          fill="url(#{g}Weave)" stroke="{p["edge"]}" stroke-width="1" opacity="0.6"/>
    <path d="M66 92 Q64 138 63 182 M114 92 Q116 138 117 182" stroke="{p["edge"]}" stroke-width="0.75" fill="none" opacity="0.5"/>
    <path d="M72 76 L78 74.8 L80 88 L73 90 Z M108 76 L102 74.8 L100 88 L107 90 Z" fill="url(#{g}Deep)" opacity="0.8"/>
    <path d="M70 150 L61 189 L74 189 Z" fill="url(#{g}Deep)" opacity="0.5"/>
    <path d="M110 150 L119 188 L106 189 Z" fill="url(#{g}Deep)" opacity="0.5"/>
    <path d="M79 76 Q90 73.4 101 76 L100 80.6 Q90 78.4 80 80.6 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.7"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# AMULET — moon crystal pendant in a woven cradle.
# Footprint: x80-102, y88-114.
# ---------------------------------------------------------------------------

def amulet_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"dMoon{idx}"

    details = []
    if idx >= 1:
        details.append(f'<path d="M85.2 95.4 L90 92.6 L94.8 95.4" stroke="{p["trim"]}" stroke-width="0.8" fill="none" opacity="0.9"/>')
    if idx >= 2:
        details.append(
            f'<circle cx="90" cy="101.5" r="8.8" fill="none" stroke="{c}" stroke-width="0.6" opacity="0.5">'
            f'<animateTransform attributeName="transform" type="rotate" values="0 90 101.5;360 90 101.5" dur="10s" repeatCount="indefinite"/></circle>'
        )
        details.append(star4(96.2, 95.2, 1.4, lc, 0.85))
    if idx >= 3:
        details.append(crescent(85.2, 97.4, 1.8, c, opacity=0.95, tilt=-18))
    if idx >= 4:
        details.append(
            f'<circle cx="90" cy="101.5" r="3.4" fill="{c}" opacity="0.3">'
            f'<animate attributeName="r" values="2.8;5.2;2.8" dur="2.4s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.3;0.12;0.3" dur="2.4s" repeatCount="indefinite"/></circle>'
        )
        details.append(ember(86, 95.5, 0.5, lc, rise=5, dur="2.7s"))
    if idx == 5:
        details.append(glow_pulse(90, 101.5, 12.5, 11, f"url(#{g}Aura)", dur="3.7s", omin=0.35, omax=0.75))
        details.append(orbit_glint(90, 101.5, 11.2, 0.85, lc, dur="6.5s"))
        details.append(constellation([(84.4, 93.8), (90, 91.6), (95.6, 93.8)], lc, dot_r=0.6))

    body = f"""
  <g id="amulet_{rarity}">
    <path d="M83 88.5 Q90 85 97 88.5" stroke="{p["trim"]}" stroke-width="1" fill="none" opacity="0.95"/>
    <path d="M86.8 96.8 L90 94.2 L93.2 96.8 L93.2 105 L90 108.4 L86.8 105 Z"
          fill="url(#{g}Weave)" stroke="{p["edge"]}" stroke-width="0.95"/>
    <path d="M88 98 L90 96.4 L92 98 L92 104.4 L90 106.5 L88 104.4 Z" fill="{c}" opacity="0.9"/>
    <path d="M88.8 98.6 L90 97.6 L90 100 Z" fill="#ffffff" opacity="0.7"/>
    <path d="M90 92.8 L90 90.4" stroke="{p["trim"]}" stroke-width="0.8"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# FX tiers — drifting dream haze and constellation glints.
# ---------------------------------------------------------------------------

def fx_epic() -> str:
    c = RARITY_COLORS["epic"]
    lc = RARITY_LIGHT["epic"]
    defs = radial_gradient("dFxEpic", [("0%", c, 0.38), ("65%", c, 0.12), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_epic">
    <ellipse cx="90" cy="120" rx="52" ry="78" fill="url(#dFxEpic)"/>
    <ellipse cx="90" cy="201" rx="40" ry="8.5" fill="{c}" opacity="0.26">
      <animate attributeName="opacity" values="0.26;0.46;0.26" dur="3.4s" repeatCount="indefinite"/>
    </ellipse>
    <path d="M52 164 Q48 134 58 110 M128 164 Q132 134 122 110" stroke="{c}" stroke-width="1.05" fill="none" opacity="0.48"/>
    {star4(58, 122, 2.0, lc, 0.8)}
    {star4(124, 134, 1.8, lc, 0.7)}
    {ember(60, 150, 0.95, lc, rise=17, dur="3.7s")}
    {ember(121, 154, 0.85, c, rise=19, dur="4.4s", begin="1.5s")}
    {ember(74, 178, 0.75, lc, rise=14, dur="3.1s", begin="0.7s")}
  </g>
"""
    return wrap(body, defs)


def fx_legendary() -> str:
    c = RARITY_COLORS["legendary"]
    lc = RARITY_LIGHT["legendary"]
    defs = radial_gradient("dFxLeg", [("0%", c, 0.42), ("60%", c, 0.15), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_legendary">
    <ellipse cx="90" cy="118" rx="58" ry="86" fill="url(#dFxLeg)"/>
    <ellipse cx="90" cy="202" rx="46" ry="9" fill="{c}" opacity="0.3">
      <animate attributeName="opacity" values="0.3;0.52;0.3" dur="3s" repeatCount="indefinite"/>
    </ellipse>
    <path d="M48 176 Q42 128 60 96 M132 176 Q138 128 120 96" stroke="{c}" stroke-width="1.2" fill="none" opacity="0.52"/>
    <path d="M52 132 A6 6 0 1 1 61 124 A4.6 4.6 0 1 0 52 132 Z" fill="{lc}" opacity="0.7">
      <animate attributeName="opacity" values="0.7;0.4;0.7" dur="3.6s" repeatCount="indefinite"/>
    </path>
    {star4(125, 120, 2.4, lc, 0.85)}
    {star4(60, 156, 1.9, c, 0.7)}
    {ember(62, 160, 1.05, lc, rise=23, dur="3.5s")}
    {ember(118, 164, 0.95, c, rise=25, dur="4.1s", begin="1.3s")}
    {ember(90, 186, 0.85, lc, rise=19, dur="3s", begin="0.5s")}
  </g>
"""
    return wrap(body, defs)


def fx_celestial() -> str:
    c = RARITY_COLORS["celestial"]
    lc = RARITY_LIGHT["celestial"]
    defs = radial_gradient("dFxCel", [("0%", c, 0.38), ("55%", c, 0.13), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_celestial">
    <rect x="56" y="0" width="68" height="220" fill="{c}" opacity="0.05"/>
    <ellipse cx="90" cy="116" rx="60" ry="92" fill="url(#dFxCel)"/>
    <ellipse cx="90" cy="203" rx="48" ry="9" fill="{c}" opacity="0.26">
      <animate attributeName="opacity" values="0.26;0.48;0.26" dur="3.9s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="90" cy="120" rx="50" ry="76" fill="none" stroke="{c}" stroke-width="0.85" opacity="0.36">
      <animate attributeName="opacity" values="0.36;0.62;0.36" dur="4.7s" repeatCount="indefinite"/>
    </ellipse>
    {constellation([(50, 58), (64, 40), (82, 32), (102, 33), (119, 43), (130, 60)], lc)}
    {constellation([(48, 148), (58, 168), (74, 182)], lc, dot_r=0.7)}
    {constellation([(132, 148), (122, 168), (106, 182)], lc, dot_r=0.7)}
    {star4(56, 100, 2.2, lc, 0.85)}
    {star4(126, 92, 2.0, lc, 0.8)}
    {orbit_glint(90, 118, 54, 1.25, lc, dur="13.5s")}
    {ember(66, 152, 0.75, lc, rise=27, dur="4.9s")}
    {ember(114, 158, 0.75, lc, rise=25, dur="5.5s", begin="2.2s")}
  </g>
"""
    return wrap(body, defs)


# ---------------------------------------------------------------------------
# HERO BASE — unchanged silhouette.
# ---------------------------------------------------------------------------

def hero_base_svg() -> str:
    return wrap(
        """
  <defs>
    <linearGradient id="robeGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3a4d78"/>
      <stop offset="100%" stop-color="#202f4e"/>
    </linearGradient>
    <linearGradient id="innerGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#6074a3"/>
      <stop offset="100%" stop-color="#3e527d"/>
    </linearGradient>
    <linearGradient id="pantsGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2a395c"/>
      <stop offset="100%" stop-color="#16233c"/>
    </linearGradient>
    <linearGradient id="skinGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f2d6bf"/>
      <stop offset="100%" stop-color="#d9ac90"/>
    </linearGradient>
    <linearGradient id="hairGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#5a4a4b"/>
      <stop offset="100%" stop-color="#30272b"/>
    </linearGradient>
    <radialGradient id="shadowGrad" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0%" stop-color="#000" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <ellipse cx="90" cy="206" rx="42" ry="7" fill="url(#shadowGrad)"/>

  <g id="hero_body">
    <animateTransform attributeName="transform" type="translate" values="0 0;0 -1.2;0 0" dur="5.2s" repeatCount="indefinite"/>

    <path d="M73 166 Q71 186 74 201 L85.5 201 Q86.5 179 83.5 166 Z" fill="url(#pantsGrad)"/>
    <path d="M97 166 Q95 179 96 201 L107.5 201 Q110.5 184 107.2 166 Z" fill="url(#pantsGrad)"/>
    <path d="M73 193 L85.5 193 L87 201 L71.5 201 Z" fill="#3f4b5f"/>
    <path d="M96 193 L108.5 193 L110 201 L94.5 201 Z" fill="#3f4b5f"/>

    <circle cx="69.5" cy="88" r="7.2" fill="#2b3f66"/>
    <circle cx="110.5" cy="88" r="7.2" fill="#2b3f66"/>
    <path d="M71 72 Q61 86 63 103 L68 166 L112 166 L117 103 Q119 86 109 72 Z" fill="url(#robeGrad)"/>
    <path d="M79 78 L102 78 L104 152 L77 152 Z" fill="url(#innerGrad)"/>
    <path d="M80 79 L86 92 M100 79 L94 92" stroke="#b9c9f0" stroke-width="1" opacity="0.7"/>
    <path d="M90 79 L90 153" stroke="#233552" stroke-width="1"/>
    <path d="M76 160 L105 160 Q103 166 101 170 L80 170 Q77 166 76 160 Z" fill="#56607a"/>
    <rect x="88.5" y="160.4" width="3" height="7" rx="0.8" fill="#cfd8e8"/>

    <path d="M63 92 Q57 102 58 116 L59 145 Q59 151 63 151 Q67 151 68 145 L69 116 Q69 103 72 93 Z" fill="url(#robeGrad)"/>
    <path d="M117 92 Q123 102 122 116 L121 145 Q121 151 117 151 Q113 151 112 145 L111 116 Q111 103 108 93 Z" fill="url(#robeGrad)"/>
    <ellipse cx="60.5" cy="149" rx="3.5" ry="3.9" fill="url(#skinGrad)"/>
    <ellipse cx="119.5" cy="149" rx="3.5" ry="3.9" fill="url(#skinGrad)"/>

    <rect x="85.2" y="63.5" width="9.6" height="10" rx="3.8" fill="url(#skinGrad)"/>
    <ellipse cx="90" cy="49" rx="13.2" ry="15.2" fill="url(#skinGrad)"/>
    <path d="M77.2 45 Q82 34 90 33 Q99 34 102.8 45 L101.5 47.8 Q90 44 78.5 47.8 Z" fill="url(#hairGrad)"/>
    <path d="M78 44 Q88 38 102 44 L102 46.3 Q89 44 78 46.3 Z" fill="#25375b"/>

    <g id="eyes">
      <animateTransform attributeName="transform" type="translate"
        values="0 0; -0.5 0.1; 0.8 -0.2; 0 0; 0.3 0.1; 0 0"
        keyTimes="0;0.12;0.23;0.56;0.74;1" dur="4.3s" repeatCount="indefinite"/>
      <ellipse cx="85.1" cy="49.1" rx="1.8" ry="1.5" fill="#f4fbff">
        <animate attributeName="ry" values="1.5;1.5;0.2;1.5;1.5;0.2;1.5" keyTimes="0;0.2;0.22;0.24;0.68;0.70;1" dur="5.2s" repeatCount="indefinite"/>
      </ellipse>
      <ellipse cx="94.9" cy="49.1" rx="1.8" ry="1.5" fill="#f4fbff">
        <animate attributeName="ry" values="1.5;1.5;0.2;1.5;1.5;0.2;1.5" keyTimes="0;0.2;0.22;0.24;0.68;0.70;1" dur="5.2s" repeatCount="indefinite"/>
      </ellipse>
      <circle cx="85.1" cy="49.1" r="0.65" fill="#25313f"/>
      <circle cx="94.9" cy="49.1" r="0.65" fill="#25313f"/>
    </g>

    <path d="M88.7 52.8 L89.4 56.8 L90.6 56.8 L91.3 52.8" fill="#b68770"/>
    <path d="M86.1 59.2 Q90 60.8 93.9 59.2" stroke="#745345" stroke-width="0.9" fill="none" stroke-linecap="round"/>

    <circle cx="74" cy="84" r="1" fill="#9cd8ff" opacity="0.45"/>
    <circle cx="105" cy="90" r="1" fill="#9cd8ff" opacity="0.45"/>
  </g>
"""
    )


def main() -> None:
    write(ROOT / "hero_base.svg", hero_base_svg())
    slot_fns = {
        "helmet": helmet_svg,
        "chestplate": chestplate_svg,
        "gauntlets": gauntlets_svg,
        "boots": boots_svg,
        "shield": shield_svg,
        "weapon": weapon_svg,
        "cloak": cloak_svg,
        "amulet": amulet_svg,
    }
    for idx, rarity in enumerate(RARITIES):
        for slot, fn in slot_fns.items():
            write(ROOT / "gear" / slot / f"{slot}_{rarity}.svg", fn(rarity, idx))

    write(ROOT / "fx" / "tier_epic.svg", fx_epic())
    write(ROOT / "fx" / "tier_legendary.svg", fx_legendary())
    write(ROOT / "fx" / "tier_celestial.svg", fx_celestial())
    print("wanderer pack regenerated")


if __name__ == "__main__":
    main()
