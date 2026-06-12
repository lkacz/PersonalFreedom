#!/usr/bin/env python3
"""Regenerate complete scholar hero SVG pack with fit-aligned rarity progression.

Art direction: academia made arcane. Rarity arc runs from coffee-stained
study wear through brass-fitted lecture dress, scrying silver, glyph-inked
violet, gold-illuminated manuscript regalia, up to a star-chart celestial
edition. Slot semantics: Shield = grand tome, Weapon = quill, Amulet =
pocket watch. Footprints match the established hero body anchors.
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

ROOT = Path("icons/heroes/scholar")

# Fabric face, fabric shadow, outline, highlight, metal trim, leather.
PAL = {
    "common": {
        "cloth": "#42526b", "shadow": "#2e3a4f", "edge": "#202b3c",
        "hi": "#6b7c95", "trim": "#8b96a8", "leather": "#5d4a39",
    },
    "uncommon": {
        "cloth": "#475d80", "shadow": "#32445f", "edge": "#22304a",
        "hi": "#7e94b8", "trim": "#c9a063", "leather": "#6b5341",
    },
    "rare": {
        "cloth": "#3f5a85", "shadow": "#2c4063", "edge": "#1e2f4c",
        "hi": "#88abd8", "trim": "#9fc3ef", "leather": "#4f5570",
    },
    "epic": {
        "cloth": "#4b4674", "shadow": "#353055", "edge": "#25213d",
        "hi": "#9b8fc9", "trim": "#b167d6", "leather": "#473a5e",
    },
    "legendary": {
        "cloth": "#5f4f35", "shadow": "#443821", "edge": "#2f2715",
        "hi": "#cfa75f", "trim": "#ffc066", "leather": "#74552f",
    },
    "celestial": {
        "cloth": "#37596c", "shadow": "#264250", "edge": "#18303d",
        "hi": "#7fd2e4", "trim": "#4dd9f0", "leather": "#2f6e80",
    },
}


def tier_defs(rarity: str, prefix: str) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    parts = [
        linear_gradient(f"{prefix}Cloth", [("0%", p["hi"]), ("45%", p["cloth"]), ("100%", p["shadow"])]),
        linear_gradient(f"{prefix}Deep", [("0%", p["cloth"]), ("100%", p["edge"])]),
    ]
    if rarity in ("epic", "legendary", "celestial"):
        parts.append(radial_gradient(f"{prefix}Aura", [("0%", c, 0.5), ("70%", c, 0.16), ("100%", c, 0.0)]))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# HELMET — mortarboard with swinging tassel over a fitted cap band.
# Footprint: x64-116, y26-55.
# ---------------------------------------------------------------------------

def helmet_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"sHelm{idx}"

    details = []
    if idx == 0:
        details.append(scratches([(78, 36.5, 84, 38.5), (97, 34, 102, 36)], color=p["edge"], width=0.6, opacity=0.7))
        details.append(f'<path d="M105 32.8 L109 35.2 L105.5 36.4 Z" fill="{p["shadow"]}" opacity="0.9"/>')  # bent corner
    if idx >= 1:
        # Tassel swinging from the board button.
        details.append(
            f'<g><animateTransform attributeName="transform" type="rotate" '
            f'values="-4 90 31;5 90 31;-4 90 31" dur="3.6s" repeatCount="indefinite"/>'
            f'<path d="M90 31 Q101 32.5 106.5 41 Q108 45 107 49" stroke="{p["trim"]}" stroke-width="1.1" fill="none"/>'
            f'<path d="M105.6 48.6 L108.4 48.6 L108.7 54 L105.3 54 Z" fill="{p["trim"]}"/>'
            f'<circle cx="107" cy="48.4" r="1.3" fill="{lc}"/>'
            "</g>"
        )
    if idx >= 2:
        details.append(rune_strip(78, 44.4, 6, c, step=4.1, height=2.2, opacity=0.85))
        details.append(shimmer_line(64, 31.5, 116, 31.5, lc, width=0.6, dur="3.8s", omin=0.2, omax=0.65))
    if idx >= 3:
        # Floating glyph diamonds above the board.
        details.append(
            f'<path d="M76 24.5 L78 27.5 L76 30.5 L74 27.5 Z" fill="{c}" opacity="0.85">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -2.4;0 0" dur="3.1s" repeatCount="indefinite"/></path>'
            f'<path d="M103 23.5 L105 26.5 L103 29.5 L101 26.5 Z" fill="{c}" opacity="0.75">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -3;0 0" dur="3.9s" repeatCount="indefinite"/></path>'
        )
    if idx >= 4:
        # Gilded laurel curling along the board's front edge.
        details.append(
            f'<path d="M68 36.5 Q76 33.5 84 35.5 M112 36.5 Q104 33.5 96 35.5" stroke="{p["trim"]}" stroke-width="1.1" fill="none" opacity="0.95"/>'
            f'<circle cx="73" cy="35.2" r="1.0" fill="{p["trim"]}"/><circle cx="80" cy="34.4" r="0.85" fill="{p["trim"]}"/>'
            f'<circle cx="107" cy="35.2" r="1.0" fill="{p["trim"]}"/><circle cx="100" cy="34.4" r="0.85" fill="{p["trim"]}"/>'
        )
        details.append(ember(86, 28, 0.7, lc, rise=6, dur="2.8s"))
    if idx == 5:
        details.append(glow_pulse(90, 34, 30, 11, f"url(#{g}Aura)", dur="4.2s", omin=0.35, omax=0.8))
        details.append(constellation([(72, 28.5), (81, 25.5), (90, 24.4), (99, 25.5), (108, 28.5)], lc))
        details.append(orbit_glint(90, 33, 27, 1.0, lc, dur="10s"))

    body = f"""
  <g id="helmet_{rarity}">
    <path d="M66 40 L114 40 L109 48 L71 48 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="1.05"/>
    <rect x="75" y="48" width="30" height="3.8" rx="1.7" fill="url(#{g}Cloth)" stroke="{p["edge"]}" stroke-width="0.8"/>
    <path d="M62 33 L90 26.5 L118 33 L90 39.5 Z" fill="url(#{g}Cloth)" stroke="{p["edge"]}" stroke-width="1.1"/>
    <path d="M66 33.6 L90 28.4 L114 33.6 L90 38.6 Z" fill="url(#{g}Deep)" opacity="0.65"/>
    <path d="M62 33 L90 39.5 L90 42.2 L62 35.4 Z" fill="{p["shadow"]}" stroke="{p["edge"]}" stroke-width="0.7"/>
    <path d="M118 33 L90 39.5 L90 42.2 L118 35.4 Z" fill="{p["edge"]}" stroke="{p["edge"]}" stroke-width="0.7"/>
    <circle cx="90" cy="31" r="1.5" fill="{p["trim"]}"/>
    <path d="M68 33.4 Q79 30.6 88 30" stroke="{p["hi"]}" stroke-width="0.7" fill="none" opacity="0.6"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# CHESTPLATE — lecture vest and gown front: lapels, buttons, satchel strap.
# Footprint: x64-116, y76-146.
# ---------------------------------------------------------------------------

def chestplate_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"sChest{idx}"

    details = []
    # Button column on all tiers.
    details.append(
        f'<circle cx="90" cy="96" r="1.1" fill="{p["trim"]}"/><circle cx="90" cy="106" r="1.1" fill="{p["trim"]}"/>'
        f'<circle cx="90" cy="116" r="1.1" fill="{p["trim"]}"/><circle cx="90" cy="126" r="1.1" fill="{p["trim"]}"/>'
    )
    if idx == 0:
        details.append(scratches([(79, 99, 84, 103), (98, 121, 102, 124)], color=p["edge"], width=0.6, opacity=0.65))
        details.append(f'<ellipse cx="99" cy="92" rx="3" ry="2.2" fill="#3b3328" opacity="0.5"/>')  # coffee stain
        details.append(f'<rect x="73.5" y="129" width="7" height="5" rx="0.8" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.6"/>')  # patch
    if idx >= 1:
        # Leather satchel strap with brass buckle.
        details.append(
            f'<path d="M71 81 L106 138 L101 141 L67 86 Z" fill="{p["leather"]}" stroke="{p["edge"]}" stroke-width="0.8" opacity="0.95"/>'
            f'<rect x="85.2" y="106.6" width="5.6" height="4.6" rx="0.9" fill="none" stroke="{p["trim"]}" stroke-width="1.0"/>'
        )
    if idx >= 2:
        details.append(f'<rect x="95.5" y="86.5" width="9" height="7" rx="1" fill="url(#{g}Deep)" stroke="{p["trim"]}" stroke-width="0.8"/>')
        details.append(f'<path d="M97.2 86.5 L97.2 84 M99.8 86.5 L99.4 83.2 M102.4 86.5 L102.4 84.4" stroke="{p["trim"]}" stroke-width="0.9"/>')  # pens
        details.append(rune_strip(74, 134.6, 5, c, step=4.2, height=2.4, opacity=0.8))
    if idx >= 3:
        # Wax seal sigil.
        details.append(
            f'<circle cx="78.5" cy="120" r="4.4" fill="{c}" opacity="0.9"/>'
            f'<circle cx="78.5" cy="120" r="2.9" fill="none" stroke="{lc}" stroke-width="0.6"/>'
            f'<path d="M77 120 L78.3 121.4 L80.3 118.6" stroke="{lc}" stroke-width="0.7" fill="none"/>'
        )
    if idx >= 4:
        # Illuminated-manuscript border filigree.
        details.append(
            f'<path d="M68 84 Q73 80 78 83 Q73 85 70 89 M112 84 Q107 80 102 83 Q107 85 110 89" stroke="{p["trim"]}" stroke-width="0.9" fill="none" opacity="0.9"/>'
            f'<path d="M67.5 138 Q74 142.5 81 140.5 M112.5 138 Q106 142.5 99 140.5" stroke="{p["trim"]}" stroke-width="0.9" fill="none" opacity="0.85"/>'
        )
        details.append(shimmer_line(90, 82, 90, 142, lc, width=0.7, dur="3.4s", omin=0.2, omax=0.6))
        details.append(ember(83, 100, 0.7, lc, rise=8, dur="3s"))
    if idx == 5:
        details.append(glow_pulse(90, 106, 25, 18, f"url(#{g}Aura)", dur="4.6s", omin=0.3, omax=0.7))
        details.append(constellation([(76, 92), (84, 88), (94, 89), (102, 94), (104, 103), (98, 110), (88, 111), (79, 106), (76, 92)], lc, dot_r=0.75))
        details.append(orbit_glint(90, 104, 20, 1.0, lc, dur="11s"))

    body = f"""
  <g id="chestplate_{rarity}">
    <path d="M70 79 L110 79 Q115 86 115 97 L112 145 L68 145 L65 97 Q65 86 70 79 Z"
          fill="url(#{g}Cloth)" stroke="{p["edge"]}" stroke-width="1.1"/>
    <path d="M76 83 L89 83 L89 143 L75.5 143 Z" fill="url(#{g}Deep)" opacity="0.92"/>
    <path d="M104 83 L91 83 L91 143 L104.5 143 Z" fill="url(#{g}Deep)" opacity="0.92"/>
    <path d="M76 83 L84 83 L78.5 96 L74.5 92 Z" fill="url(#{g}Cloth)" stroke="{p["edge"]}" stroke-width="0.7"/>
    <path d="M104 83 L96 83 L101.5 96 L105.5 92 Z" fill="url(#{g}Cloth)" stroke="{p["edge"]}" stroke-width="0.7"/>
    <path d="M90 83 L90 143" stroke="{p["edge"]}" stroke-width="0.9" opacity="0.85"/>
    <path d="M68 138 L112 138 L111.7 142.6 L68.3 142.6 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.7"/>
    <path d="M77 84.5 Q82 82.8 87 84.2" stroke="{p["hi"]}" stroke-width="0.7" fill="none" opacity="0.6"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# GAUNTLETS — scribe's cuffs: rolled sleeve plates, ink stains, pen loops.
# Footprints: left x37-63 / right x117-143, y132-158.
# ---------------------------------------------------------------------------

def gauntlets_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"sGaunt{idx}"

    def one(x0: float, mirror: bool) -> str:
        xm = x0 + 13
        parts = [
            f'<path d="M{x0+1} 134 L{x0+25} 134 L{x0+24} 146 L{x0+2} 146 Z" fill="url(#{g}Cloth)" stroke="{p["edge"]}" stroke-width="1"/>',
            f'<path d="M{x0+2} 146 L{x0+24} 146 L{x0+22.5} 157 L{x0+3.5} 157 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.9"/>',
            f'<path d="M{x0+1.5} 139.5 L{x0+24.5} 139.5" stroke="{p["hi"]}" stroke-width="0.7" opacity="0.6"/>',
            f'<path d="M{x0+3} 146 L{x0+23} 146" stroke="{p["trim"]}" stroke-width="1.1" opacity="0.9"/>',
        ]
        if idx == 0:
            parts.append(f'<ellipse cx="{xm + (4 if mirror else -4)}" cy="151" rx="2.6" ry="1.8" fill="#1c2331" opacity="0.75"/>')  # ink stain
            parts.append(scratches([(x0 + 5, 136, x0 + 9, 138.5)], color=p["edge"], width=0.55, opacity=0.7))
        if idx >= 1:
            parts.append(
                f'<path d="M{x0+4.5} 150.5 Q{xm} 147.5 {x0+21.5} 150.5" stroke="{p["trim"]}" stroke-width="0.9" fill="none" opacity="0.9"/>'
            )
        if idx >= 2:
            # Pen loop with a small quill stub.
            parts.append(
                f'<rect x="{xm-1.4}" y="148.4" width="2.8" height="5.4" rx="1.1" fill="none" stroke="{p["trim"]}" stroke-width="0.8"/>'
                f'<path d="M{xm} 147.8 L{xm} 144.6" stroke="{lc}" stroke-width="0.9"/>'
            )
            parts.append(rune_strip(x0 + 5.5, 141.4, 3, c, step=4.6, height=2.2, opacity=0.85))
        if idx >= 3:
            parts.append(
                f'<path d="M{xm} 133.6 L{xm+1.8} 136.4 L{xm} 139.2 L{xm-1.8} 136.4 Z" fill="{c}" opacity="0.9"/>'
            )
        if idx >= 4:
            parts.append(
                f'<path d="M{x0+3} 155.6 L{x0+23} 155.6" stroke="{c}" stroke-width="0.9" opacity="0.5">'
                f'<animate attributeName="opacity" values="0.5;0.95;0.5" dur="2.7s" repeatCount="indefinite"/></path>'
            )
            parts.append(ember(xm + (4 if mirror else -4), 137, 0.6, lc, rise=6, dur="3.1s", begin="0.7s" if mirror else "0s"))
        if idx == 5:
            parts.append(glow_pulse(xm, 145, 13, 10, f"url(#{g}Aura)", dur="4.4s", omin=0.3, omax=0.7))
            parts.append(constellation([(x0 + 5, 137.5), (xm, 135.4), (x0 + 21, 137.5)], lc, dot_r=0.7))
        return "".join(parts)

    body = f"""
  <g id="gauntlets_{rarity}">
    {one(37, False)}
    {one(117, True)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# BOOTS — polished oxfords: toe cap, laces, stacked heel on the boot blocks.
# Footprints: left x41-79 / right x101-139, y184-210.
# ---------------------------------------------------------------------------

def boots_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"sBoot{idx}"

    def one(x0: float, flip: bool) -> str:
        xm = x0 + 19
        parts = [
            f'<path d="M{x0+4} 186 L{x0+32} 186 L{x0+34} 198 L{x0+2} 198 Z" fill="url(#{g}Cloth)" stroke="{p["edge"]}" stroke-width="1"/>',
            f'<path d="M{x0+1} 197.5 L{x0+35} 197.5 L{x0+37.5} 206.5 L{x0-0.5} 206.5 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="1"/>',
            f'<path d="M{x0-0.5} 205.8 L{x0+37.5} 205.8 L{x0+37.5} 209 L{x0-0.5} 209 Z" fill="{p["edge"]}"/>',
            # Toe cap seam + lace panel.
            f'<path d="M{x0+24} 198 Q{x0+29} 201.5 {x0+27.5} 205.5" stroke="{p["hi"]}" stroke-width="0.75" fill="none" opacity="0.7"/>',
            f'<path d="M{x0+9} 188.5 L{x0+18} 188.5 M{x0+9.6} 191 L{x0+17.4} 191 M{x0+10.2} 193.5 L{x0+16.8} 193.5" stroke="{p["leather"]}" stroke-width="1" opacity="0.95"/>',
            f'<circle cx="{x0+9}" cy="188.5" r="0.7" fill="{p["trim"]}"/><circle cx="{x0+18}" cy="188.5" r="0.7" fill="{p["trim"]}"/>',
        ]
        if idx == 0:
            parts.append(scratches([(x0 + 6, 201, x0 + 11, 204), (x0 + 26, 188, x0 + 30, 190)], color=p["edge"], width=0.6, opacity=0.7))
        if idx >= 1:
            parts.append(f'<path d="M{x0+2} 196.6 L{x0+34} 196.6" stroke="{p["trim"]}" stroke-width="1.0" opacity="0.9"/>')
        if idx >= 2:
            parts.append(rune_strip(x0 + 9, 201.4, 4, c, step=4.5, height=2.2, opacity=0.8))
        if idx >= 3:
            parts.append(
                f'<path d="M{xm} 182.6 L{xm+2} 185.4 L{xm} 188.2 L{xm-2} 185.4 Z" fill="{c}" opacity="0.9"/>'
            )
        if idx >= 4:
            parts.append(shimmer_line(x0 + 1, 207.4, x0 + 36, 207.4, c, width=0.95, dur="2.9s", omin=0.25, omax=0.85))
            parts.append(ember(xm + (3 if flip else -3), 195, 0.55, lc, rise=6, dur="3.4s", begin="1s" if flip else "0s"))
        if idx == 5:
            parts.append(glow_pulse(xm, 198, 18, 8, f"url(#{g}Aura)", dur="5s", omin=0.25, omax=0.6))
            parts.append(constellation([(x0 + 7, 189.5), (xm, 187.5), (x0 + 31, 189.5)], lc, dot_r=0.65))
        return "".join(parts)

    body = f"""
  <g id="boots_{rarity}">
    {one(41, False)}
    {one(101, True)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# SHIELD — the grand tome: bound cover, spine ribs, corner caps, clasp.
# Footprint: x28-66, y98-152.
# ---------------------------------------------------------------------------

def shield_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"sTome{idx}"

    details = []
    # Corner caps on every tier.
    for cx_, cy_ in [(33.5, 104.5), (60.5, 104.5), (33.5, 145.5), (60.5, 145.5)]:
        details.append(
            f'<path d="M{cx_-3} {cy_} L{cx_} {cy_-3} L{cx_+3} {cy_} L{cx_} {cy_+3} Z" '
            f'fill="{p["trim"]}" opacity="0.95" stroke="{p["edge"]}" stroke-width="0.5"/>'
        )
    if idx == 0:
        details.append(scratches([(38, 112, 44, 117), (52, 132, 56, 136)], color=p["edge"], width=0.6, opacity=0.7))
        details.append(f'<path d="M58 99.5 L62 103 L57.5 103.5 Z" fill="{p["shadow"]}" opacity="0.9"/>')  # dog-ear
    if idx >= 1:
        details.append(
            f'<rect x="44" y="120.6" width="7" height="8.8" rx="1.2" fill="url(#{g}Deep)" stroke="{p["trim"]}" stroke-width="0.9"/>'
            f'<circle cx="47.5" cy="125" r="1.2" fill="{p["trim"]}"/>'
        )
    if idx >= 2:
        details.append(rune_strip(37.5, 109.4, 5, c, step=4.2, height=2.6, opacity=0.95))
        details.append(shimmer_line(34, 117, 60, 117, lc, width=0.6, dur="3.3s", omin=0.25, omax=0.7))
    if idx >= 3:
        # Floating letters drifting off the page edge.
        details.append(
            f'<path d="M56 124 L58.4 124 M57.2 122.8 L57.2 125.2" stroke="{c}" stroke-width="0.7" opacity="0.9">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;3 -5;0 0" dur="3.7s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.9;0.2;0.9" dur="3.7s" repeatCount="indefinite"/></path>'
            f'<circle cx="55" cy="132" r="0.8" fill="{c}" opacity="0.8">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;4 -7;0 0" dur="4.3s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.8;0.15;0.8" dur="4.3s" repeatCount="indefinite"/></circle>'
        )
    if idx >= 4:
        # Gold illumination border.
        details.append(
            f'<rect x="35.5" y="106.5" width="23" height="37" rx="1.5" fill="none" stroke="{p["trim"]}" stroke-width="0.8" opacity="0.9"/>'
            f'<path d="M36.5 113 Q40 110 43 112.5 M59.5 113 Q56 110 53 112.5" stroke="{p["trim"]}" stroke-width="0.7" fill="none" opacity="0.85"/>'
        )
        details.append(ember(40, 121, 0.65, lc, rise=8, dur="2.8s"))
    if idx == 5:
        details.append(glow_pulse(47, 125, 20, 26, f"url(#{g}Aura)", dur="4.4s", omin=0.3, omax=0.7))
        details.append(constellation([(38, 112), (47, 108.5), (56, 112), (58, 124), (51, 134), (40, 132), (38, 112)], lc, dot_r=0.75))
        details.append(orbit_glint(47, 124, 16.5, 0.95, lc, dur="9s"))

    body = f"""
  <g id="shield_{rarity}">
    <path d="M31 101 L60 99.5 L65 103.5 L65 147 L60 151 L31 149.5 L28.5 146 L28.5 104.5 Z"
          fill="url(#{g}Cloth)" stroke="{p["edge"]}" stroke-width="1.15"/>
    <path d="M31 101 L31 149.5 L28.5 146 L28.5 104.5 Z" fill="{p["edge"]}"/>
    <path d="M62.8 103 L62.8 147.6" stroke="{p["hi"]}" stroke-width="1.6" opacity="0.85"/>
    <path d="M62 106 L62 144" stroke="#e8dcc0" stroke-width="1.1" opacity="0.75"/>
    <path d="M33 108 L33 142 M35.8 105 L35.8 145" stroke="{p["edge"]}" stroke-width="0.8" opacity="0.6"/>
    <rect x="37" y="108" width="20" height="34" rx="1.8" fill="url(#{g}Deep)" opacity="0.9"/>
    <path d="M34 124.6 L29 124.6 M34 130.4 L29 130.4" stroke="{p["trim"]}" stroke-width="1.3" opacity="0.9"/>
    <path d="M39 110 Q46 107.5 53 110" stroke="{p["hi"]}" stroke-width="0.65" fill="none" opacity="0.55"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# WEAPON — the scribe's quill along the established -24° axis: feather,
# barrel and nib, with ink magic budding at higher tiers.
# ---------------------------------------------------------------------------

def weapon_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"sQuill{idx}"

    details = []
    if idx == 0:
        # Ragged feather notches.
        details.append(
            f'<path d="M138 102 L141 104.5 L137.5 105 Z M132 109 L135 111 L131.5 111.8 Z" fill="#10141c" opacity="0.55"/>'
        )
    if idx >= 1:
        details.append(f'<path d="M127 117 Q136 107 146 101" stroke="{p["trim"]}" stroke-width="0.8" fill="none" opacity="0.85"/>')
    if idx >= 2:
        details.append(rune_strip(117.4, 137.8, 1, c, step=4, height=2.6, opacity=0.95))
        details.append(
            f'<circle cx="120.3" cy="166.8" r="1.5" fill="{c}" opacity="0.9">'
            f'<animate attributeName="opacity" values="0.9;0.4;0.9" dur="2.6s" repeatCount="indefinite"/></circle>'
        )
    if idx >= 3:
        # Ink swirl rising off the plume.
        details.append(
            f'<path d="M134 104 Q139 99 137 94 Q142 97 141.5 103" stroke="{c}" stroke-width="0.8" fill="none" opacity="0.75">'
            f'<animate attributeName="opacity" values="0.75;0.25;0.75" dur="3.2s" repeatCount="indefinite"/></path>'
        )
        details.append(ember(143, 99, 0.7, lc, rise=7, dur="2.9s"))
    if idx >= 4:
        details.append(
            f'<path d="M125.5 121 Q135 111.5 147 104 Q141 112 133 118.5 Q129 121.5 125.5 121 Z" fill="{c}" opacity="0.4">'
            f'<animate attributeName="opacity" values="0.4;0.7;0.25;0.4" dur="2.1s" repeatCount="indefinite"/></path>'
        )
        details.append(ember(136, 108, 0.6, c, rise=8, dur="2.4s", begin="0.8s"))
    if idx == 5:
        details.append(glow_pulse(137, 107, 15, 11, f"url(#{g}Aura)", dur="3.9s", omin=0.3, omax=0.75))
        details.append(constellation([(128, 116), (135, 110), (142, 104.5), (148, 100.5)], lc, dot_r=0.7))
        details.append(orbit_glint(120.3, 145, 7, 0.8, lc, dur="7.5s"))

    body = f"""
  <g id="weapon_{rarity}" transform="rotate(-24 121 131)">
    <rect x="117" y="128" width="6.6" height="34" rx="2.8" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.95"/>
    <path d="M117.2 134 L123.4 134 M117.2 152 L123.4 152" stroke="{p["trim"]}" stroke-width="1.6" opacity="0.95"/>
    <path d="M118.6 162 L121.9 162 L120.3 168.5 Z" fill="{p["trim"]}" stroke="{p["edge"]}" stroke-width="0.6"/>
    <path d="M120.3 164.5 L120.3 167.6" stroke="{p["edge"]}" stroke-width="0.5"/>
    <path d="M121 128 Q126 116 134 107 Q142 99 151 95.5 Q146 104 139 111.5 Q131 119.5 124 124.5 Z"
          fill="url(#{g}Cloth)" stroke="{p["edge"]}" stroke-width="1"/>
    <path d="M122.5 125 Q132 114 149 97" stroke="{p["edge"]}" stroke-width="0.9" fill="none" opacity="0.9"/>
    <path d="M126 119 Q124 115 125.5 111 M131 113 Q129 109 130.5 105 M137 106.5 Q135 103 136.5 99.5"
          stroke="{p["shadow"]}" stroke-width="0.7" fill="none" opacity="0.8"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# CLOAK — academic gown: yoke pleats, facing bands, braid cords.
# Footprint: x54-126, y72-192.
# ---------------------------------------------------------------------------

def cloak_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"sCloak{idx}"

    details = []
    if idx == 0:
        details.append(f'<path d="M61 184 L65 190 L68.5 184.5 L72 189.5 L75 184 L70 181.5 Z" fill="url(#{g}Deep)" opacity="0.75"/>')
        details.append(f'<rect x="108" y="168" width="6.5" height="5" rx="0.8" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.5" opacity="0.85"/>')
    if idx >= 1:
        # Velvet facing bands down both fronts.
        details.append(f'<path d="M63 88 Q61 138 62.5 184 M117 88 Q119 138 117.5 184" stroke="{p["trim"]}" stroke-width="1.4" fill="none" opacity="0.8"/>')
    if idx >= 2:
        # Braided cord and button at the yoke.
        details.append(
            f'<path d="M74 84 Q90 92 106 84" stroke="{p["trim"]}" stroke-width="0.9" fill="none" opacity="0.9"/>'
            f'<circle cx="90" cy="88.6" r="1.4" fill="{p["trim"]}"/>'
        )
        details.append(rune_strip(62, 174.5, 3, c, step=4.4, height=2.4, opacity=0.7))
        details.append(rune_strip(105, 174.5, 3, c, step=4.4, height=2.4, opacity=0.7))
    if idx >= 3:
        # Open-book sigil on the left panel.
        details.append(
            f'<path d="M62.5 126 Q66.5 124 70.5 126 L70.5 133 Q66.5 131 62.5 133 Z M70.5 126 Q74.5 124 78.5 126 L78.5 133 Q74.5 131 70.5 133 Z" '
            f'fill="none" stroke="{c}" stroke-width="0.8" opacity="0.85"/>'
        )
    if idx >= 4:
        details.append(shimmer_line(60, 100, 60, 180, c, width=0.8, dur="3.6s", omin=0.2, omax=0.7))
        details.append(shimmer_line(120, 100, 120, 180, c, width=0.8, dur="3.6s", omin=0.7, omax=0.2))
        details.append(ember(66, 158, 0.65, lc, rise=10, dur="3.5s"))
        details.append(ember(115, 150, 0.6, c, rise=9, dur="3s", begin="1.4s"))
    if idx == 5:
        details.append(glow_pulse(90, 134, 36, 42, f"url(#{g}Aura)", dur="5.4s", omin=0.2, omax=0.45))
        details.append(constellation([(64, 108), (69, 124), (66, 142), (71, 158), (67, 174)], lc, dot_r=0.7))
        details.append(constellation([(116, 108), (111, 124), (114, 142), (109, 158), (113, 174)], lc, dot_r=0.7))

    body = f"""
  <g id="cloak_{rarity}" opacity="0.96">
    <path d="M64 75 Q90 70 116 75 L124 92 L120 188 Q105 183 90 183 Q75 183 60 188 L56 92 Z"
          fill="url(#{g}Cloth)" stroke="{p["edge"]}" stroke-width="1" opacity="0.6"/>
    <path d="M66 92 Q64 138 63 182 M114 92 Q116 138 117 182" stroke="{p["edge"]}" stroke-width="0.75" fill="none" opacity="0.55"/>
    <path d="M72 76 L78 74.8 L80 88 L73 90 Z M108 76 L102 74.8 L100 88 L107 90 Z" fill="url(#{g}Deep)" opacity="0.85"/>
    <path d="M70 92 Q70 130 69 178 M110 92 Q110 130 111 178" stroke="{p["shadow"]}" stroke-width="0.7" fill="none" opacity="0.5"/>
    <path d="M70 150 L61 189 L74 189 Z" fill="url(#{g}Deep)" opacity="0.55"/>
    <path d="M110 150 L119 188 L106 189 Z" fill="url(#{g}Deep)" opacity="0.55"/>
    <path d="M79 76 Q90 73.4 101 76 L100 80.6 Q90 78.4 80 80.6 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.7"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# AMULET — brass pocket watch: chain swag, case, ticking hands, crown.
# Footprint: x78-102, y86-114.
# ---------------------------------------------------------------------------

def amulet_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"sWatch{idx}"

    details = []
    if idx >= 1:
        details.append(f'<circle cx="90" cy="101" r="7.6" fill="none" stroke="{p["trim"]}" stroke-width="0.9" opacity="0.95"/>')
    if idx >= 2:
        # Ticking hands (slow rotate keeps a clean static frame).
        details.append(
            f'<path d="M90 101 L90 96.4" stroke="{lc}" stroke-width="0.9" stroke-linecap="round">'
            f'<animateTransform attributeName="transform" type="rotate" values="0 90 101;360 90 101" dur="12s" repeatCount="indefinite"/></path>'
            f'<path d="M90 101 L93.2 101" stroke="{lc}" stroke-width="0.7" stroke-linecap="round">'
            f'<animateTransform attributeName="transform" type="rotate" values="0 90 101;360 90 101" dur="60s" repeatCount="indefinite"/></path>'
        )
    if idx >= 3:
        details.append(
            f'<path d="M84.8 96 L83 94.2 M95.2 96 L97 94.2 M84.8 106 L83 107.8 M95.2 106 L97 107.8" '
            f'stroke="{c}" stroke-width="0.7" opacity="0.85"/>'
        )
    if idx >= 4:
        details.append(
            f'<circle cx="90" cy="101" r="3" fill="{c}" opacity="0.28">'
            f'<animate attributeName="r" values="2.4;4.8;2.4" dur="2.5s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.28;0.1;0.28" dur="2.5s" repeatCount="indefinite"/></circle>'
        )
        details.append(ember(86, 95.5, 0.5, lc, rise=5, dur="2.7s"))
    if idx == 5:
        details.append(glow_pulse(90, 101, 12.5, 11, f"url(#{g}Aura)", dur="3.8s", omin=0.35, omax=0.8))
        details.append(orbit_glint(90, 101, 11.6, 0.85, lc, dur="7s"))
        details.append(constellation([(84, 93.6), (90, 91.4), (96, 93.6)], lc, dot_r=0.6))

    body = f"""
  <g id="amulet_{rarity}">
    <path d="M82 88 Q86 92.5 90 92.8 Q94 92.5 98 88" stroke="{p["trim"]}" stroke-width="1.1" fill="none" opacity="0.95"/>
    <circle cx="82" cy="88" r="0.9" fill="{p["trim"]}"/>
    <circle cx="98" cy="88" r="0.9" fill="{p["trim"]}"/>
    <rect x="88.9" y="92.4" width="2.2" height="2.2" rx="0.6" fill="{p["trim"]}"/>
    <circle cx="90" cy="101" r="6.2" fill="url(#{g}Cloth)" stroke="{p["edge"]}" stroke-width="1"/>
    <circle cx="90" cy="101" r="4.6" fill="#e9e2ce" opacity="0.95"/>
    <path d="M90 97.4 L90 98.6 M93.6 101 L92.4 101 M90 104.6 L90 103.4 M86.4 101 L87.6 101"
          stroke="{p["edge"]}" stroke-width="0.6" opacity="0.9"/>
    <path d="M90 101 L90 98.2 M90 101 L92 101" stroke="{p["edge"]}" stroke-width="0.8" stroke-linecap="round"/>
    <circle cx="90" cy="101" r="0.7" fill="{p["edge"]}"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# FX tiers — study-lamp glow and drifting knowledge motes.
# ---------------------------------------------------------------------------

def fx_epic() -> str:
    c = RARITY_COLORS["epic"]
    lc = RARITY_LIGHT["epic"]
    defs = radial_gradient("sFxEpic", [("0%", c, 0.38), ("65%", c, 0.12), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_epic">
    <ellipse cx="90" cy="120" rx="52" ry="78" fill="url(#sFxEpic)"/>
    <ellipse cx="90" cy="201" rx="40" ry="8.5" fill="{c}" opacity="0.28">
      <animate attributeName="opacity" values="0.28;0.48;0.28" dur="3.3s" repeatCount="indefinite"/>
    </ellipse>
    <path d="M52 164 Q48 134 58 110 M128 164 Q132 134 122 110" stroke="{c}" stroke-width="1.05" fill="none" opacity="0.5"/>
    <path d="M55 122 L57.4 122 M56.2 120.8 L56.2 123.2" stroke="{lc}" stroke-width="0.7" opacity="0.85">
      <animateTransform attributeName="transform" type="translate" values="0 0;3 -9;0 0" dur="4.2s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.85;0.2;0.85" dur="4.2s" repeatCount="indefinite"/>
    </path>
    {ember(60, 150, 0.95, lc, rise=16, dur="3.6s")}
    {ember(121, 154, 0.85, c, rise=18, dur="4.3s", begin="1.4s")}
    {ember(74, 178, 0.75, lc, rise=13, dur="3s", begin="0.7s")}
  </g>
"""
    return wrap(body, defs)


def fx_legendary() -> str:
    c = RARITY_COLORS["legendary"]
    lc = RARITY_LIGHT["legendary"]
    defs = radial_gradient("sFxLeg", [("0%", c, 0.42), ("60%", c, 0.15), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_legendary">
    <ellipse cx="90" cy="118" rx="58" ry="86" fill="url(#sFxLeg)"/>
    <ellipse cx="90" cy="202" rx="46" ry="9" fill="{c}" opacity="0.32">
      <animate attributeName="opacity" values="0.32;0.55;0.32" dur="2.9s" repeatCount="indefinite"/>
    </ellipse>
    <path d="M48 176 Q42 128 60 96 M132 176 Q138 128 120 96" stroke="{c}" stroke-width="1.25" fill="none" opacity="0.55"/>
    <path d="M53 142 Q57 139 61 142 L61 149 Q57 146 53 149 Z M61 142 Q65 139 69 142 L69 149 Q65 146 61 149 Z"
          fill="none" stroke="{lc}" stroke-width="0.8" opacity="0.7">
      <animateTransform attributeName="transform" type="translate" values="0 0;0 -7;0 0" dur="4.6s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.7;0.25;0.7" dur="4.6s" repeatCount="indefinite"/>
    </path>
    {ember(62, 160, 1.05, lc, rise=22, dur="3.4s")}
    {ember(118, 164, 0.95, c, rise=24, dur="4s", begin="1.2s")}
    {ember(90, 186, 0.85, lc, rise=18, dur="3s", begin="0.5s")}
  </g>
"""
    return wrap(body, defs)


def fx_celestial() -> str:
    c = RARITY_COLORS["celestial"]
    lc = RARITY_LIGHT["celestial"]
    defs = radial_gradient("sFxCel", [("0%", c, 0.38), ("55%", c, 0.13), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_celestial">
    <rect x="56" y="0" width="68" height="220" fill="{c}" opacity="0.05"/>
    <ellipse cx="90" cy="116" rx="60" ry="92" fill="url(#sFxCel)"/>
    <ellipse cx="90" cy="203" rx="48" ry="9" fill="{c}" opacity="0.28">
      <animate attributeName="opacity" values="0.28;0.5;0.28" dur="3.8s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="90" cy="120" rx="50" ry="76" fill="none" stroke="{c}" stroke-width="0.85" opacity="0.38">
      <animate attributeName="opacity" values="0.38;0.65;0.38" dur="4.6s" repeatCount="indefinite"/>
    </ellipse>
    {constellation([(50, 58), (64, 40), (82, 32), (102, 33), (119, 43), (130, 60)], lc)}
    {constellation([(48, 148), (58, 168), (74, 182)], lc, dot_r=0.7)}
    {constellation([(132, 148), (122, 168), (106, 182)], lc, dot_r=0.7)}
    {orbit_glint(90, 118, 54, 1.25, lc, dur="13s")}
    {ember(66, 152, 0.75, lc, rise=26, dur="4.8s")}
    {ember(114, 158, 0.75, lc, rise=24, dur="5.4s", begin="2.1s")}
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
    <linearGradient id="coatGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#324564"/>
      <stop offset="100%" stop-color="#1d2d49"/>
    </linearGradient>
    <linearGradient id="vestGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#4b5f85"/>
      <stop offset="100%" stop-color="#2c3f60"/>
    </linearGradient>
    <linearGradient id="pantsGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#243751"/>
      <stop offset="100%" stop-color="#152236"/>
    </linearGradient>
    <linearGradient id="skinGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f1d7c1"/>
      <stop offset="100%" stop-color="#dcb191"/>
    </linearGradient>
    <linearGradient id="hairGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#5a4637"/>
      <stop offset="100%" stop-color="#31241c"/>
    </linearGradient>
    <radialGradient id="shadowGrad" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0%" stop-color="#000" stop-opacity="0.32"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <ellipse cx="90" cy="206" rx="40" ry="7" fill="url(#shadowGrad)"/>

  <g id="hero_body" transform="rotate(-2 90 128)">
    <animateTransform attributeName="transform" additive="sum" type="translate" values="0 0;0 -0.8;0 0" dur="4.8s" repeatCount="indefinite"/>

    <path d="M74 166 Q72 184 75 201 L85 201 Q86 180 83 166 Z" fill="url(#pantsGrad)"/>
    <path d="M97 166 Q95 178 96 201 L106 201 Q109 183 106 166 Z" fill="url(#pantsGrad)"/>
    <path d="M74 193 L86 193 L87.5 201 L73 201 Z" fill="#3f4552"/>
    <path d="M95.5 193 L107.5 193 L109 201 L94.5 201 Z" fill="#3f4552"/>

    <circle cx="71" cy="88" r="7.2" fill="#273a59"/>
    <circle cx="109" cy="88" r="7.2" fill="#273a59"/>
    <path d="M72 73 Q62 86 64 103 L68 166 L111 166 L116 103 Q117 86 108 73 Z" fill="url(#coatGrad)"/>
    <path d="M79 79 L102 79 L104 152 L77 152 Z" fill="url(#vestGrad)"/>
    <path d="M80 80 L86 92 M101 80 L95 92" stroke="#d8b97c" stroke-width="1.1" opacity="0.7"/>
    <path d="M90 79 L90 153" stroke="#223450" stroke-width="1.05" opacity="0.7"/>
    <path d="M76 160 L105 160 Q103 165 101 169 L80 169 Q77 165 76 160 Z" fill="#6a4738"/>
    <rect x="88.4" y="160.3" width="3.2" height="7.1" rx="0.8" fill="#d4b276"/>

    <path d="M64 92 Q58 101 59 116 L60 145 Q60 151 63.8 151 Q67.5 151 68.5 145 L70 116 Q70 103 73 93 Z" fill="url(#coatGrad)"/>
    <path d="M116 92 Q122 101 121 116 L120 145 Q120 151 116.2 151 Q112.5 151 111.5 145 L110 116 Q110 103 107 93 Z" fill="url(#coatGrad)"/>
    <ellipse cx="61.5" cy="149" rx="3.5" ry="3.9" fill="url(#skinGrad)"/>
    <ellipse cx="118.5" cy="149" rx="3.5" ry="3.9" fill="url(#skinGrad)"/>

    <rect x="85.4" y="63.5" width="9.2" height="10" rx="3.7" fill="url(#skinGrad)"/>
    <ellipse cx="90" cy="49" rx="13.2" ry="15.2" fill="url(#skinGrad)"/>
    <path d="M77 45 Q82 34 90 33 Q99 34 103 45 L101.8 47.8 Q90 44 78.2 47.8 Z" fill="url(#hairGrad)"/>
    <path d="M77.5 44 Q89 39 102.5 44 L102.5 46.5 Q89.5 44.5 77.5 46.5 Z" fill="#1f3049"/>

    <rect x="81.5" y="46.2" width="7.2" height="5.2" rx="1.3" fill="none" stroke="#d3dceb" stroke-width="0.9"/>
    <rect x="91.3" y="46.2" width="7.2" height="5.2" rx="1.3" fill="none" stroke="#d3dceb" stroke-width="0.9"/>
    <path d="M88.7 48.8 L91.3 48.8" stroke="#d3dceb" stroke-width="0.8"/>

    <g id="eyes" transform="translate(0 0)">
      <animateTransform attributeName="transform" type="translate"
        values="0 0; -0.6 0.1; 0.8 -0.2; 0 0; 0.3 0.1; 0 0"
        keyTimes="0;0.12;0.24;0.56;0.74;1" dur="4.2s" repeatCount="indefinite"/>
      <ellipse cx="85.2" cy="49.1" rx="1.9" ry="1.6" fill="#f4fbff">
        <animate attributeName="ry" values="1.6;1.6;0.2;1.6;1.6;0.2;1.6" keyTimes="0;0.19;0.21;0.23;0.68;0.70;1" dur="5s" repeatCount="indefinite"/>
      </ellipse>
      <ellipse cx="94.8" cy="49.1" rx="1.9" ry="1.6" fill="#f4fbff">
        <animate attributeName="ry" values="1.6;1.6;0.2;1.6;1.6;0.2;1.6" keyTimes="0;0.19;0.21;0.23;0.68;0.70;1" dur="5s" repeatCount="indefinite"/>
      </ellipse>
      <circle cx="85.2" cy="49.1" r="0.7" fill="#26303e"/>
      <circle cx="94.8" cy="49.1" r="0.7" fill="#26303e"/>
    </g>

    <path d="M88.7 52.6 L89.4 56.8 L90.6 56.8 L91.3 52.6" fill="#b58771"/>
    <path d="M85.6 59.2 Q90 61.2 94.4 59.2" stroke="#775043" stroke-width="0.9" fill="none" stroke-linecap="round"/>
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
    print("scholar pack regenerated")


if __name__ == "__main__":
    main()
