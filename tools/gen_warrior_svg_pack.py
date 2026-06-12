#!/usr/bin/env python3
"""Regenerate complete warrior hero SVG pack with fit-aligned rarity progression.

Art direction: forged battle gear. Rarity arc runs from dented iron through
polished steel, rune-blued steel, dragon-forged violet, flame-gilded gold,
up to star-forged celestial glass. Gear keeps the established canvas
footprints so composition on the hero body is unchanged.
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
except ImportError:  # imported as tools.gen_warrior_svg_pack
    from tools.svg_pack_common import (
        RARITIES, RARITY_COLORS, RARITY_LIGHT,
        write, wrap, linear_gradient, radial_gradient,
        glow_pulse, shimmer_line, ember, orbit_glint,
        constellation, rivets, scratches, rune_strip,
    )

ROOT = Path("icons/heroes/warrior")

# Per-tier material palette: plate face, plate shadow, outline, highlight, trim metal.
PAL = {
    "common": {
        "plate": "#4d5563", "shadow": "#353c49", "edge": "#252c38",
        "hi": "#717e8f", "trim": "#6e7787", "strap": "#5d4434",
    },
    "uncommon": {
        "plate": "#56657a", "shadow": "#3a4658", "edge": "#26313f",
        "hi": "#8b99ac", "trim": "#79c47d", "strap": "#6a4d3a",
    },
    "rare": {
        "plate": "#4a5d78", "shadow": "#32425a", "edge": "#22304a",
        "hi": "#8fb2dc", "trim": "#64a8e8", "strap": "#5d4a6e",
    },
    "epic": {
        "plate": "#52476b", "shadow": "#392f4e", "edge": "#271f38",
        "hi": "#a08cc4", "trim": "#b167d6", "strap": "#4a3658",
    },
    "legendary": {
        "plate": "#6b5638", "shadow": "#4a3a24", "edge": "#332715",
        "hi": "#d9ab66", "trim": "#ffb74d", "strap": "#7a4a26",
    },
    "celestial": {
        "plate": "#3c5a6b", "shadow": "#27414f", "edge": "#19303c",
        "hi": "#8fd9e8", "trim": "#4dd9f0", "strap": "#2f6e80",
    },
}


def tier_defs(rarity: str, prefix: str) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    parts = [
        linear_gradient(f"{prefix}Plate", [("0%", p["hi"]), ("45%", p["plate"]), ("100%", p["shadow"])]),
        linear_gradient(f"{prefix}Deep", [("0%", p["plate"]), ("100%", p["edge"])]),
    ]
    if rarity in ("legendary", "celestial", "epic"):
        parts.append(radial_gradient(f"{prefix}Aura", [("0%", c, 0.5), ("70%", c, 0.16), ("100%", c, 0.0)]))
    return "\n".join(parts)


def idx_of(rarity: str) -> int:
    return RARITIES.index(rarity)


# ---------------------------------------------------------------------------
# HELMET — full war-helm over the crown, cheek guards, nasal bar, tier crest.
# Footprint: x64-116, y24-55.
# ---------------------------------------------------------------------------

def helmet_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"wHelm{idx}"

    details = []
    # Dome plate seams + rivet line on every tier.
    details.append(f'<path d="M78 33 Q90 27 102 33" stroke="{p["edge"]}" stroke-width="0.8" fill="none" opacity="0.8"/>')
    details.append(rivets([(72.5, 43.5), (90, 40.6), (107.5, 43.5)], r=1.0, fill=p["hi"], shadow=p["edge"]))

    if idx == 0:
        details.append(scratches([(76, 36, 82, 39), (98, 34.5, 104, 38), (84, 30.8, 88, 32.2)]))
        details.append(f'<path d="M99 44.5 L104 47.5" stroke="{p["edge"]}" stroke-width="1.1" opacity="0.75"/>')  # dent
    if idx >= 1:
        details.append(f'<path d="M66 45.5 Q90 38.5 114 45.5" stroke="{p["trim"]}" stroke-width="1.2" fill="none" opacity="0.9"/>')
    if idx >= 2:
        details.append(rune_strip(80.5, 41.6, 5, c, step=4.0, height=2.4, opacity=0.9))
        details.append(shimmer_line(70, 47.5, 110, 47.5, lc, width=0.7, dur="3.4s", omin=0.25, omax=0.8))
    if idx >= 3:
        # Dragon horns sweeping back from the temples.
        details.append(
            f'<path d="M68 38 Q60 30 62 20 Q67 27 72 32 Z" fill="url(#{g}Deep)" stroke="{c}" stroke-width="0.8"/>'
            f'<path d="M112 38 Q120 30 118 20 Q113 27 108 32 Z" fill="url(#{g}Deep)" stroke="{c}" stroke-width="0.8"/>'
        )
    if idx >= 4:
        # Winged crest and plume.
        details.append(
            f'<path d="M86 27 Q90 19 94 27 L92 31 L88 31 Z" fill="{c}" opacity="0.95"/>'
            f'<path d="M90 20.5 Q90.8 24 90 27.5 Q89.2 24 90 20.5 Z" fill="{lc}">'
            f'<animate attributeName="opacity" values="0.85;1;0.6;0.85" dur="1.9s" repeatCount="indefinite"/></path>'
        )
        details.append(ember(84.5, 25.5, 0.8, lc, rise=6, dur="2.3s"))
        details.append(ember(95.5, 26.5, 0.7, c, rise=7, dur="2.9s", begin="0.8s"))
    if idx == 5:
        details.append(glow_pulse(90, 38, 30, 12.5, f"url(#{g}Aura)", dur="4s", omin=0.4, omax=0.85))
        details.append(constellation([(74, 33.5), (82, 30), (90, 28.6), (98, 30), (106, 33.5)], lc))
        details.append(orbit_glint(90, 38, 26, 1.1, lc, dur="9s"))

    body = f"""
  <g id="helmet_{rarity}">
    <path d="M67 47 Q66 31 78 26.5 Q90 22.5 102 26.5 Q114 31 113 47 L106 47 Q104 34 90 32.6 Q76 34 74 47 Z"
          fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="1.1"/>
    <path d="M74 47 Q76 34 90 32.6 Q104 34 106 47 L103 49 Q90 44.5 77 49 Z" fill="url(#{g}Deep)" opacity="0.95"/>
    <path d="M67 46.5 L74 44.6 L74 56 Q69.5 54 67.5 50.5 Z" fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="0.9"/>
    <path d="M113 46.5 L106 44.6 L106 56 Q110.5 54 112.5 50.5 Z" fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="0.9"/>
    <path d="M88.5 33 L91.5 33 L91.2 42.5 L88.8 42.5 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.6"/>
    <path d="M70.5 30.5 Q78 25.5 86 24.6" stroke="{p["hi"]}" stroke-width="1.0" fill="none" opacity="0.7" stroke-linecap="round"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# CHESTPLATE — sculpted pectorals, abdominal lames, shoulder ties, tier core.
# Footprint: x64-116, y76-146.
# ---------------------------------------------------------------------------

def chestplate_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"wChest{idx}"

    details = []
    # Abdominal lames on all tiers.
    details.append(
        f'<path d="M73 118 L107 118 M74 126 L106 126 M75 134 L105 134" stroke="{p["edge"]}" stroke-width="0.9" opacity="0.85"/>'
        f'<path d="M73 119.2 L107 119.2 M74 127.2 L106 127.2" stroke="{p["hi"]}" stroke-width="0.5" opacity="0.5"/>'
    )
    details.append(rivets([(70.5, 84), (109.5, 84), (69.5, 112), (110.5, 112)], r=1.0, fill=p["hi"], shadow=p["edge"]))

    if idx == 0:
        details.append(scratches([(78, 96, 86, 102), (97, 88, 103, 92), (80, 124, 85, 127.5)]))
        details.append(f'<path d="M95 128 Q99 131 103 129" stroke="{p["edge"]}" stroke-width="1.2" fill="none" opacity="0.7"/>')
    if idx >= 1:
        details.append(f'<path d="M70 81 L80 76.5 L100 76.5 L110 81" stroke="{p["trim"]}" stroke-width="1.15" fill="none" opacity="0.9"/>')
        details.append(f'<rect x="86.4" y="138" width="7.2" height="5.4" rx="1.2" fill="url(#{g}Deep)" stroke="{p["trim"]}" stroke-width="0.8"/>')
    if idx >= 2:
        details.append(rune_strip(76.5, 112.3, 7, c, step=4.0, height=2.4, opacity=0.85))
        details.append(shimmer_line(72, 86.5, 90, 81.5, lc, width=0.8, dur="3.1s", omin=0.2, omax=0.7))
    if idx >= 3:
        # Dragon-scale shoulder rows.
        scale_row = []
        for rdx, (sy, n, x0) in enumerate([(88, 4, 71), (93.5, 3, 73)]):
            for i in range(n):
                sx = x0 + i * 5.4
                scale_row.append(f'<path d="M{sx} {sy} q2.7 -3.4 5.4 0 q-2.7 3.0 -5.4 0 Z" fill="url(#{g}Deep)" stroke="{c}" stroke-width="0.55" opacity="0.9"/>')
                mx = 180 - sx - 5.4
                scale_row.append(f'<path d="M{mx} {sy} q2.7 -3.4 5.4 0 q-2.7 3.0 -5.4 0 Z" fill="url(#{g}Deep)" stroke="{c}" stroke-width="0.55" opacity="0.9"/>')
        details.append("".join(scale_row))
    if idx >= 4:
        details.append(
            f'<path d="M82 96 Q90 88 98 96 Q94 93 90 99 Q86 93 82 96 Z" fill="{c}" opacity="0.95">'
            f'<animate attributeName="opacity" values="0.95;0.65;0.95" dur="2.6s" repeatCount="indefinite"/></path>'
        )
        details.append(ember(84, 104, 0.8, lc, rise=8, dur="2.7s"))
        details.append(ember(96, 106, 0.7, c, rise=9, dur="3.3s", begin="1.1s"))
    if idx == 5:
        details.append(glow_pulse(90, 103, 26, 17, f"url(#{g}Aura)", dur="4.4s", omin=0.35, omax=0.8))
        details.append(constellation([(78, 95), (84, 90.5), (90, 89), (96, 90.5), (102, 95), (96, 100), (90, 102), (84, 100), (78, 95)], lc, dot_r=0.8))
        details.append(orbit_glint(90, 100, 21, 1.0, lc, dur="10s"))

    body = f"""
  <g id="chestplate_{rarity}">
    <path d="M70 79 L110 79 Q115 86 115 97 L112 145 L68 145 L65 97 Q65 86 70 79 Z"
          fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="1.1"/>
    <path d="M73 84 Q81 81 89 84.5 L89 104 Q82 108.5 74.5 105.5 Z" fill="url(#{g}Deep)" opacity="0.95"/>
    <path d="M107 84 Q99 81 91 84.5 L91 104 Q98 108.5 105.5 105.5 Z" fill="url(#{g}Deep)" opacity="0.95"/>
    <path d="M90 80 L90 144" stroke="{p["edge"]}" stroke-width="1.0" opacity="0.9"/>
    <path d="M68 110 L73 108 L107 108 L112 110 L111.5 116 L68.5 116 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.8"/>
    <path d="M74 84.5 Q80 82.4 87 84.6" stroke="{p["hi"]}" stroke-width="0.8" fill="none" opacity="0.65"/>
    <path d="M67.5 96 L66.5 140 M112.5 96 L113.5 140" stroke="{p["edge"]}" stroke-width="0.7" opacity="0.6"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# GAUNTLETS — layered vambrace plates with flared cuffs and knuckle studs.
# Footprints: left x37-63 / right x117-143, y132-158.
# ---------------------------------------------------------------------------

def gauntlets_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"wGaunt{idx}"

    def one(x0: float, mirror: bool) -> str:
        # x0 is the left edge of a 26-wide cuff. Plates stack toward the wrist.
        xm = x0 + 13
        parts = [
            f'<path d="M{x0+1} 134 L{x0+25} 134 L{x0+23.5} 144 L{x0+2.5} 144 Z" fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="1"/>',
            f'<path d="M{x0+2.5} 144 L{x0+23.5} 144 L{x0+22.5} 151 L{x0+3.5} 151 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.9"/>',
            f'<path d="M{x0+3.5} 151 L{x0+22.5} 151 L{x0+21} 157 L{x0+5} 157 Z" fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="0.9"/>',
            f'<path d="M{x0+3} 138.6 L{x0+23} 138.6" stroke="{p["hi"]}" stroke-width="0.6" opacity="0.6"/>',
            f'<rect x="{x0+6}" y="152.6" width="14" height="2.6" rx="1.2" fill="{p["strap"]}" stroke="{p["edge"]}" stroke-width="0.5"/>',
        ]
        if idx == 0:
            parts.append(scratches([(x0 + 5, 136.5, x0 + 10, 139.5), (x0 + 16, 146, x0 + 20, 148.5)]))
        if idx >= 1:
            parts.append(f'<path d="M{x0+2} 144 L{x0+24} 144" stroke="{p["trim"]}" stroke-width="1.0" opacity="0.9"/>')
        if idx >= 2:
            parts.append(rune_strip(x0 + 6.5, 146.3, 3, c, step=4.4, height=2.2, opacity=0.9))
        if idx >= 3:
            parts.append(
                f'<path d="M{xm} 132.5 L{xm+3} 128 L{xm+1} 134 Z" fill="url(#{g}Deep)" stroke="{c}" stroke-width="0.6"/>'
                f'<circle cx="{xm}" cy="141.2" r="2.1" fill="url(#{g}Deep)" stroke="{c}" stroke-width="0.8"/>'
                f'<circle cx="{xm}" cy="141.2" r="0.8" fill="{c}"/>'
            )
        if idx >= 4:
            parts.append(
                f'<circle cx="{xm}" cy="141.2" r="3.4" fill="none" stroke="{c}" stroke-width="0.6" opacity="0.55">'
                f'<animate attributeName="opacity" values="0.55;0.95;0.55" dur="2.4s" repeatCount="indefinite"/></circle>'
            )
            parts.append(ember(xm - 4.5, 136, 0.65, lc, rise=6, dur="2.8s", begin="0.4s" if mirror else "0s"))
        if idx == 5:
            parts.append(glow_pulse(xm, 145, 13, 10, f"url(#{g}Aura)", dur="4.2s", omin=0.35, omax=0.75))
            parts.append(constellation([(x0 + 5, 137), (xm, 134.6), (x0 + 21, 137)], lc, dot_r=0.7))
        return "".join(parts)

    body = f"""
  <g id="gauntlets_{rarity}">
    {one(37, False)}
    {one(117, True)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# BOOTS — armored sabatons: shin plate, ankle strap, ridged toe cap.
# Footprints: left x41-79 / right x101-139, y184-210.
# ---------------------------------------------------------------------------

def boots_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"wBoot{idx}"

    def one(x0: float, flip: bool) -> str:
        # x0 = left edge of a 38-wide boot block.
        xm = x0 + 19
        parts = [
            f'<path d="M{x0+3} 186 L{x0+33} 186 L{x0+34.5} 199 L{x0+1.5} 199 Z" fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="1"/>',
            f'<path d="M{x0+1} 198 L{x0+36} 198 L{x0+38} 207 L{x0-1} 207 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="1"/>',
            f'<path d="M{x0-1} 206.2 L{x0+38} 206.2 L{x0+38} 209 L{x0-1} 209 Z" fill="{p["edge"]}"/>',
            f'<path d="M{x0+5} 190 L{x0+31} 190" stroke="{p["hi"]}" stroke-width="0.6" opacity="0.6"/>',
            f'<rect x="{x0+8}" y="192.6" width="20" height="3" rx="1.4" fill="{p["strap"]}" stroke="{p["edge"]}" stroke-width="0.55"/>',
            f'<path d="M{x0+30} 199 Q{x0+35} 202.5 {x0+33.5} 206" stroke="{p["hi"]}" stroke-width="0.7" fill="none" opacity="0.55"/>',
        ]
        if idx == 0:
            parts.append(scratches([(x0 + 7, 200.5, x0 + 13, 204), (x0 + 24, 188, x0 + 29, 190.5)]))
        if idx >= 1:
            parts.append(f'<path d="M{x0+2} 197.2 L{x0+34} 197.2" stroke="{p["trim"]}" stroke-width="1.05" opacity="0.9"/>')
            parts.append(rivets([(x0 + 11.5, 194.1), (x0 + 24.5, 194.1)], r=0.85, fill=p["hi"], shadow=p["edge"]))
        if idx >= 2:
            parts.append(rune_strip(x0 + 9, 201.6, 4, c, step=4.6, height=2.2, opacity=0.85))
        if idx >= 3:
            parts.append(
                f'<path d="M{xm-5} 186 L{xm} 181.5 L{xm+5} 186 Z" fill="url(#{g}Deep)" stroke="{c}" stroke-width="0.7"/>'
                f'<circle cx="{xm}" cy="188.6" r="1.1" fill="{c}"/>'
            )
        if idx >= 4:
            parts.append(shimmer_line(x0 + 2, 207.8, x0 + 36, 207.8, c, width=1.0, dur="2.5s", omin=0.3, omax=0.95))
            parts.append(ember(xm + (3 if flip else -3), 196, 0.6, lc, rise=7, dur="3.1s", begin="0.9s" if flip else "0s"))
        if idx == 5:
            parts.append(glow_pulse(xm, 198, 18.5, 8.5, f"url(#{g}Aura)", dur="4.6s", omin=0.3, omax=0.7))
            parts.append(constellation([(x0 + 7, 189), (xm, 187), (x0 + 31, 189)], lc, dot_r=0.7))
        return "".join(parts)

    body = f"""
  <g id="boots_{rarity}">
    {one(41, False)}
    {one(101, True)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# SHIELD — heater shield with central boss, cross ribs and tier emblem.
# Footprint: x28-66, y98-152.
# ---------------------------------------------------------------------------

def shield_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"wShield{idx}"

    details = []
    details.append(rivets([(35, 105.5), (59, 105.5), (33.5, 128), (60.5, 128)], r=0.95, fill=p["hi"], shadow=p["edge"]))
    if idx == 0:
        details.append(scratches([(38, 112, 45, 118), (52, 134, 57, 138), (40, 140, 44, 143)]))
        details.append(f'<path d="M54 110 L58 116 L55 117 Z" fill="{p["edge"]}" opacity="0.8"/>')  # notch
    if idx >= 1:
        details.append(f'<path d="M33 104 L61 104 L63.5 109 L63.5 138 L57.5 146.5 L36.5 146.5 L30.5 138 L30.5 109 Z" fill="none" stroke="{p["trim"]}" stroke-width="1.1" opacity="0.9"/>')
    if idx >= 2:
        details.append(rune_strip(38.5, 107.2, 5, c, step=3.9, height=2.3, opacity=0.9))
        details.append(shimmer_line(33, 136, 47, 145.5, lc, width=0.7, dur="3.6s", omin=0.2, omax=0.7))
    if idx >= 3:
        # Rampant dragon emblem (stylized) under the boss.
        details.append(
            f'<path d="M42 130 Q45 124 50 126 Q48 128 49 130 Q53 129 54 133 Q50 132 48 134 Q46 137 43 136 Q45 133 42 130 Z" '
            f'fill="{c}" opacity="0.92"/>'
            f'<circle cx="50.5" cy="127" r="0.6" fill="{lc}"/>'
        )
    if idx >= 4:
        details.append(
            f'<circle cx="47" cy="117.5" r="6.4" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.6">'
            f'<animate attributeName="opacity" values="0.6;1;0.6" dur="2.2s" repeatCount="indefinite"/></circle>'
        )
        details.append(ember(40, 122, 0.7, lc, rise=8, dur="2.9s"))
        details.append(ember(55, 124, 0.6, c, rise=7, dur="2.4s", begin="0.7s"))
    if idx == 5:
        details.append(glow_pulse(47, 124, 21, 26, f"url(#{g}Aura)", dur="4.8s", omin=0.3, omax=0.7))
        details.append(constellation([(37, 110), (47, 106), (57, 110), (60, 122), (47, 132), (34, 122), (37, 110)], lc, dot_r=0.75))
        details.append(orbit_glint(47, 122, 17, 1.0, lc, dur="9.5s"))

    body = f"""
  <g id="shield_{rarity}">
    <path d="M31 101 L63 101 L66 107 L66 137 L59 148.5 L47 152 L35 148.5 L28 137 L28 107 Z"
          fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="1.15"/>
    <path d="M33.5 104.5 L60.5 104.5 L63 109.5 L63 136 L57 146 L47 149 L37 146 L31 136 L31 109.5 Z"
          fill="url(#{g}Deep)" opacity="0.95"/>
    <path d="M47 104 L47 149" stroke="{p["edge"]}" stroke-width="1.0" opacity="0.85"/>
    <path d="M31.5 117.5 L62.5 117.5" stroke="{p["edge"]}" stroke-width="0.9" opacity="0.8"/>
    <circle cx="47" cy="117.5" r="4.6" fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="1"/>
    <circle cx="47" cy="117.5" r="1.7" fill="{c}" opacity="0.95"/>
    <path d="M33 106.5 Q40 103.5 46 103.8" stroke="{p["hi"]}" stroke-width="0.75" fill="none" opacity="0.6"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# WEAPON — war axe held in the right hand; blade grows more storied per tier.
# Group keeps the established transform rotate(-24 121 131).
# ---------------------------------------------------------------------------

def weapon_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"wWeap{idx}"

    details = []
    if idx == 0:
        # Chipped edge.
        details.append(f'<path d="M146 100.5 L148.5 103 L146 104.5 Z" fill="#10141c" opacity="0.85"/>')
        details.append(scratches([(130, 106, 136, 109), (128, 114, 133, 117)], color="#3c4f68", width=0.6, opacity=0.8))
    if idx >= 1:
        details.append(f'<path d="M126 103.5 Q139 95.5 148 105" stroke="{p["trim"]}" stroke-width="0.95" fill="none" opacity="0.85"/>')
    if idx >= 2:
        details.append(rune_strip(117.3, 137.5, 1, c, step=4, height=2.6, opacity=0.95))
        details.append(rune_strip(117.3, 143.5, 1, c, step=4, height=2.6, opacity=0.8))
        details.append(shimmer_line(127.5, 121, 149, 103, lc, width=0.85, dur="2.7s", omin=0.35, omax=1.0))
    if idx >= 3:
        # Rear counter-blade making it a double axe.
        details.append(
            f'<path d="M116 104 Q103 96 95 107 Q107 110 114.5 122 Z" fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="1"/>'
            f'<path d="M113.5 106.5 L110.5 110.8 L113.5 115 L116.3 110.8 Z" fill="{lc}" opacity="0.85"/>'
        )
    if idx >= 4:
        # Flame lick along the leading edge.
        details.append(
            f'<path d="M128 119 Q137 110 147.5 104.5 Q144 110.5 138 116 Q133.5 119.5 128 119 Z" fill="{c}" opacity="0.55">'
            f'<animate attributeName="opacity" values="0.55;0.85;0.35;0.55" dur="1.7s" repeatCount="indefinite"/></path>'
        )
        details.append(ember(141, 104, 0.8, lc, rise=8, dur="2.2s"))
        details.append(ember(133, 112, 0.65, c, rise=7, dur="2.8s", begin="0.6s"))
    if idx == 5:
        details.append(glow_pulse(137, 109, 16, 11, f"url(#{g}Aura)", dur="3.8s", omin=0.35, omax=0.8))
        details.append(constellation([(128, 117), (134, 111), (141, 106), (148, 103.5)], lc, dot_r=0.7))
        details.append(orbit_glint(120.3, 144, 7.5, 0.85, lc, dur="7s"))

    body = f"""
  <g id="weapon_{rarity}" transform="rotate(-24 121 131)">
    <rect x="115.2" y="126" width="10.2" height="38" rx="3.2" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="1"/>
    <path d="M116 130 L124.6 130 M116 152 L124.6 152" stroke="{p["strap"]}" stroke-width="2.2" opacity="0.95"/>
    <rect x="118.6" y="160.5" width="3.4" height="5" rx="1.5" fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="0.7"/>
    <path d="M114.4 126 L126.2 126 L127.8 121.4 L112.8 121.4 Z" fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="1"/>
    <path d="M124 102 Q141 91 152.5 105.5 Q138.5 111 126.5 124 Z" fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="1.1"/>
    <path d="M126.5 105 Q138 97.5 147.5 105.5 Q137 110 128.5 119 Z" fill="url(#{g}Deep)" opacity="0.92"/>
    <path d="M126.3 103.5 L129.6 108.8 L126.3 114.2 L123 108.8 Z" fill="{lc}" opacity="0.9"/>
    <circle cx="120.3" cy="123.7" r="1.1" fill="{c}" opacity="0.95"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# CLOAK — war banner draped from the shoulders; reads behind the torso
# with side panels and a collar clasp. Footprint: x54-126, y72-192.
# ---------------------------------------------------------------------------

def cloak_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"wCloak{idx}"

    details = []
    if idx == 0:
        # Torn hem.
        details.append(f'<path d="M60 186 L64 191 L67 185.5 L71 190.5 L74 185 L70 182 Z" fill="url(#{g}Deep)" opacity="0.8"/>')
        details.append(f'<path d="M112 184 L116 189.5 L120 183.5 L116 181 Z" fill="url(#{g}Deep)" opacity="0.8"/>')
    if idx >= 1:
        details.append(f'<path d="M58 96 Q57 140 60.5 184 M122 96 Q123 140 119.5 184" stroke="{p["trim"]}" stroke-width="0.9" fill="none" opacity="0.7"/>')
    if idx >= 2:
        details.append(rune_strip(60.5, 178.5, 4, c, step=4.0, height=2.4, opacity=0.7))
        details.append(rune_strip(104.5, 178.5, 4, c, step=4.0, height=2.4, opacity=0.7))
    if idx >= 3:
        # Embroidered dragon sigil on the left panel.
        details.append(
            f'<path d="M62 128 Q66 121 71.5 124 Q69 126.5 70 129.5 Q74.5 128.5 75.5 133 Q71 132 69 134.5 Q66.5 138 63 136.5 Q65.5 132.5 62 128 Z" '
            f'fill="none" stroke="{c}" stroke-width="0.85" opacity="0.85"/>'
        )
    if idx >= 4:
        details.append(shimmer_line(59, 100, 59, 178, c, width=0.8, dur="3.4s", omin=0.25, omax=0.8))
        details.append(shimmer_line(121, 100, 121, 178, c, width=0.8, dur="3.4s", omin=0.8, omax=0.25))
        details.append(ember(64, 160, 0.7, lc, rise=10, dur="3.2s"))
        details.append(ember(117, 154, 0.6, c, rise=9, dur="2.7s", begin="1.2s"))
    if idx == 5:
        details.append(glow_pulse(90, 135, 37, 42, f"url(#{g}Aura)", dur="5.2s", omin=0.22, omax=0.5))
        details.append(constellation([(63, 110), (68, 124), (65, 142), (70, 158), (66, 172)], lc, dot_r=0.7))
        details.append(constellation([(117, 110), (112, 124), (115, 142), (110, 158), (114, 172)], lc, dot_r=0.7))

    body = f"""
  <g id="cloak_{rarity}" opacity="0.96">
    <path d="M64 75 Q90 70 116 75 L124 92 L120 188 Q105 183 90 183 Q75 183 60 188 L56 92 Z"
          fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="1" opacity="0.62"/>
    <path d="M64 78 L77 74.5 L78 86 L66 90 Z" fill="url(#{g}Deep)" opacity="0.9"/>
    <path d="M116 78 L103 74.5 L102 86 L114 90 Z" fill="url(#{g}Deep)" opacity="0.9"/>
    <path d="M66 92 Q63 138 62.5 182 M114 92 Q117 138 117.5 182" stroke="{p["edge"]}" stroke-width="0.8" fill="none" opacity="0.55"/>
    <path d="M70 150 L61 189 L74 189 Z" fill="url(#{g}Deep)" opacity="0.6"/>
    <path d="M110 150 L119 188 L106 189 Z" fill="url(#{g}Deep)" opacity="0.6"/>
    <path d="M78 76.5 Q90 73.5 102 76.5 L101 81 Q90 78.6 79 81 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.7"/>
    <circle cx="90" cy="78.6" r="1.6" fill="{c}" opacity="0.95"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# AMULET — chained war talisman at the sternum with a cut gem core.
# Footprint: x80-100, y88-112.
# ---------------------------------------------------------------------------

def amulet_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"wAmu{idx}"

    details = []
    if idx >= 1:
        details.append(f'<path d="M90 94.2 L94.6 97 L94.6 103 L90 105.8 L85.4 103 L85.4 97 Z" fill="none" stroke="{p["trim"]}" stroke-width="0.9" opacity="0.9"/>')
    if idx >= 2:
        details.append(
            f'<circle cx="90" cy="100" r="9.6" fill="none" stroke="{c}" stroke-width="0.7" opacity="0.5">'
            f'<animateTransform attributeName="transform" type="rotate" values="0 90 100;360 90 100" dur="9s" repeatCount="indefinite"/>'
            "</circle>"
        )
        details.append(f'<path d="M90 90.4 L91 92.4 L90 94 L89 92.4 Z" fill="{lc}" opacity="0.9"/>')
    if idx >= 3:
        details.append(
            f'<path d="M83 100 L78.6 97.6 L80 102.6 Z" fill="{c}" opacity="0.9"/>'
            f'<path d="M97 100 L101.4 97.6 L100 102.6 Z" fill="{c}" opacity="0.9"/>'
        )
    if idx >= 4:
        details.append(
            f'<circle cx="90" cy="100" r="3.2" fill="{c}" opacity="0.3">'
            f'<animate attributeName="r" values="2.6;5;2.6" dur="2.3s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.3;0.12;0.3" dur="2.3s" repeatCount="indefinite"/>'
            "</circle>"
        )
        details.append(ember(86.5, 95, 0.55, lc, rise=6, dur="2.6s"))
    if idx == 5:
        details.append(glow_pulse(90, 100, 13, 11, f"url(#{g}Aura)", dur="3.6s", omin=0.4, omax=0.85))
        details.append(orbit_glint(90, 100, 12.4, 0.9, lc, dur="6.5s"))
        details.append(constellation([(83.5, 93.5), (90, 91), (96.5, 93.5)], lc, dot_r=0.6))

    body = f"""
  <g id="amulet_{rarity}">
    <path d="M83 88.5 Q90 84.5 97 88.5" stroke="{p["hi"]}" stroke-width="1.1" fill="none" opacity="0.95"/>
    <path d="M85.5 89.7 Q90 87 94.5 89.7" stroke="{p["edge"]}" stroke-width="0.6" fill="none" opacity="0.7"/>
    <path d="M90 92.8 L95.8 96.4 L95.8 103.6 L90 107.2 L84.2 103.6 L84.2 96.4 Z"
          fill="url(#{g}Plate)" stroke="{p["edge"]}" stroke-width="1"/>
    <path d="M90 95.6 L93.4 97.8 L93.4 102.2 L90 104.4 L86.6 102.2 L86.6 97.8 Z" fill="url(#{g}Deep)"/>
    <path d="M90 97.2 L92 100 L90 102.8 L88 100 Z" fill="{c}" opacity="0.98"/>
    <path d="M89.2 97.9 L90 99 L89 99.8 Z" fill="{lc}" opacity="0.9"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# FX tiers — battle aura backdrops behind the hero.
# ---------------------------------------------------------------------------

def fx_epic() -> str:
    c = RARITY_COLORS["epic"]
    lc = RARITY_LIGHT["epic"]
    defs = radial_gradient("wFxEpic", [("0%", c, 0.4), ("65%", c, 0.12), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_epic">
    <ellipse cx="90" cy="120" rx="52" ry="78" fill="url(#wFxEpic)"/>
    <ellipse cx="90" cy="201" rx="40" ry="8.5" fill="{c}" opacity="0.3">
      <animate attributeName="opacity" values="0.3;0.5;0.3" dur="3.1s" repeatCount="indefinite"/>
    </ellipse>
    <path d="M52 168 Q49 140 56 116" stroke="{c}" stroke-width="1.1" fill="none" opacity="0.55"/>
    <path d="M128 168 Q131 140 124 116" stroke="{c}" stroke-width="1.1" fill="none" opacity="0.55"/>
    {ember(58, 150, 1.0, lc, rise=16, dur="3.4s")}
    {ember(122, 156, 0.9, c, rise=18, dur="4.1s", begin="1.3s")}
    {ember(70, 178, 0.8, lc, rise=14, dur="2.9s", begin="0.6s")}
  </g>
"""
    return wrap(body, defs)


def fx_legendary() -> str:
    c = RARITY_COLORS["legendary"]
    lc = RARITY_LIGHT["legendary"]
    defs = radial_gradient("wFxLeg", [("0%", c, 0.45), ("60%", c, 0.16), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_legendary">
    <ellipse cx="90" cy="118" rx="58" ry="86" fill="url(#wFxLeg)"/>
    <ellipse cx="90" cy="202" rx="46" ry="9" fill="{c}" opacity="0.35">
      <animate attributeName="opacity" values="0.35;0.6;0.35" dur="2.7s" repeatCount="indefinite"/>
    </ellipse>
    <path d="M47 178 Q40 130 58 96 M133 178 Q140 130 122 96" stroke="{c}" stroke-width="1.3" fill="none" opacity="0.6"/>
    <path d="M55 188 Q58 181 55.5 174 Q60 178 60.5 185 Q57 191 55 188 Z" fill="{c}" opacity="0.7">
      <animate attributeName="opacity" values="0.7;0.95;0.5;0.7" dur="1.9s" repeatCount="indefinite"/>
    </path>
    <path d="M124 186 Q127 179 124.5 172 Q129 176 129.5 183 Q126 189 124 186 Z" fill="{lc}" opacity="0.65">
      <animate attributeName="opacity" values="0.65;0.9;0.45;0.65" dur="2.3s" repeatCount="indefinite"/>
    </path>
    {ember(60, 160, 1.1, lc, rise=22, dur="3.2s")}
    {ember(120, 166, 1.0, c, rise=24, dur="3.8s", begin="1.1s")}
    {ember(88, 186, 0.9, lc, rise=18, dur="2.8s", begin="0.5s")}
  </g>
"""
    return wrap(body, defs)


def fx_celestial() -> str:
    c = RARITY_COLORS["celestial"]
    lc = RARITY_LIGHT["celestial"]
    defs = radial_gradient("wFxCel", [("0%", c, 0.4), ("55%", c, 0.14), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_celestial">
    <rect x="56" y="0" width="68" height="220" fill="{c}" opacity="0.05"/>
    <ellipse cx="90" cy="116" rx="60" ry="92" fill="url(#wFxCel)"/>
    <ellipse cx="90" cy="203" rx="48" ry="9" fill="{c}" opacity="0.3">
      <animate attributeName="opacity" values="0.3;0.55;0.3" dur="3.6s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="90" cy="120" rx="50" ry="76" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.4">
      <animate attributeName="opacity" values="0.4;0.7;0.4" dur="4.4s" repeatCount="indefinite"/>
    </ellipse>
    {constellation([(50, 60), (62, 42), (80, 33), (100, 33), (118, 42), (130, 60)], lc)}
    {constellation([(48, 150), (58, 170), (74, 184)], lc, dot_r=0.7)}
    {constellation([(132, 150), (122, 170), (106, 184)], lc, dot_r=0.7)}
    {orbit_glint(90, 118, 54, 1.3, lc, dur="12s")}
    {ember(66, 150, 0.8, lc, rise=26, dur="4.6s")}
    {ember(114, 158, 0.8, lc, rise=24, dur="5.2s", begin="2s")}
  </g>
"""
    return wrap(body, defs)


# ---------------------------------------------------------------------------
# HERO BASE — unchanged silhouette (kept stable so the character look and
# all gear anchors stay consistent).
# ---------------------------------------------------------------------------

def hero_base_svg() -> str:
    return wrap(
        """
  <defs>
    <linearGradient id="armorGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#5a6373"/>
      <stop offset="100%" stop-color="#303744"/>
    </linearGradient>
    <linearGradient id="innerGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#364354"/>
      <stop offset="100%" stop-color="#1f2937"/>
    </linearGradient>
    <linearGradient id="pantsGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2e3a4a"/>
      <stop offset="100%" stop-color="#1a2230"/>
    </linearGradient>
    <linearGradient id="skinGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f3d5bf"/>
      <stop offset="100%" stop-color="#d8ab8f"/>
    </linearGradient>
    <linearGradient id="hairGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#5b4635"/>
      <stop offset="100%" stop-color="#322519"/>
    </linearGradient>
    <radialGradient id="shadowGrad" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0%" stop-color="#000" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <ellipse cx="90" cy="206" rx="42" ry="7" fill="url(#shadowGrad)"/>

  <g id="hero_body">
    <animateTransform attributeName="transform" type="translate" values="0 0;0 -0.6;0 0" dur="4.2s" repeatCount="indefinite"/>

    <path d="M72 166 Q70 185 73 201 L86 201 Q87 178 84 166 Z" fill="url(#pantsGrad)"/>
    <path d="M97 166 Q95 178 96 201 L109 201 Q112 184 108.5 166 Z" fill="url(#pantsGrad)"/>
    <path d="M71 193 L86.5 193 L88 201 L69.8 201 Z" fill="#454d5a"/>
    <path d="M95.5 193 L111 193 L112.5 201 L94.3 201 Z" fill="#454d5a"/>

    <circle cx="68.5" cy="87.8" r="8.2" fill="#3d4653"/>
    <circle cx="111.5" cy="87.8" r="8.2" fill="#3d4653"/>
    <path d="M70 72 Q60 86 62 103 L67 166 L113 166 L118 103 Q120 86 110 72 Z" fill="url(#armorGrad)"/>
    <path d="M78 78 L103 78 L105 152 L76 152 Z" fill="url(#innerGrad)"/>
    <path d="M79 79 L85 92 M101 79 L95 92" stroke="#8f9caf" stroke-width="1"/>
    <path d="M90 79 L90 153" stroke="#242f3f" stroke-width="1.1"/>
    <path d="M76 160 L105 160 Q103 166 101 170 L80 170 Q77 166 76 160 Z" fill="#6b4a39"/>
    <rect x="88.4" y="160.4" width="3.2" height="7.1" rx="0.8" fill="#b98b5e"/>

    <path d="M62 92 Q56 102 57 116 L58 145 Q58 151 62 151 Q66 151 67 145 L68 116 Q68 103 71 93 Z" fill="url(#armorGrad)"/>
    <path d="M118 92 Q124 102 123 116 L122 145 Q122 151 118 151 Q114 151 113 145 L112 116 Q112 103 109 93 Z" fill="url(#armorGrad)"/>
    <ellipse cx="59.5" cy="149" rx="3.6" ry="3.9" fill="url(#skinGrad)"/>
    <ellipse cx="120.5" cy="149" rx="3.6" ry="3.9" fill="url(#skinGrad)"/>

    <rect x="85.2" y="63.5" width="9.6" height="10" rx="3.8" fill="url(#skinGrad)"/>
    <ellipse cx="90" cy="49" rx="13.2" ry="15.2" fill="url(#skinGrad)"/>
    <path d="M77.2 45 Q82 34 90 33 Q99 34 102.8 45 L101.5 47.8 Q90 44 78.5 47.8 Z" fill="url(#hairGrad)"/>

    <g id="eyes">
      <animateTransform attributeName="transform" type="translate"
        values="0 0; -0.4 0.1; 0.7 -0.2; 0 0; 0.25 0.1; 0 0"
        keyTimes="0;0.13;0.24;0.57;0.75;1" dur="4.2s" repeatCount="indefinite"/>
      <ellipse cx="85.1" cy="49.2" rx="1.9" ry="1.5" fill="#f4fbff">
        <animate attributeName="ry" values="1.5;1.5;0.2;1.5;1.5;0.2;1.5" keyTimes="0;0.2;0.22;0.24;0.68;0.70;1" dur="5s" repeatCount="indefinite"/>
      </ellipse>
      <ellipse cx="94.9" cy="49.2" rx="1.9" ry="1.5" fill="#f4fbff">
        <animate attributeName="ry" values="1.5;1.5;0.2;1.5;1.5;0.2;1.5" keyTimes="0;0.2;0.22;0.24;0.68;0.70;1" dur="5s" repeatCount="indefinite"/>
      </ellipse>
      <circle cx="85.1" cy="49.2" r="0.65" fill="#25313f"/>
      <circle cx="94.9" cy="49.2" r="0.65" fill="#25313f"/>
    </g>

    <path d="M88.7 52.8 L89.4 56.8 L90.6 56.8 L91.3 52.8" fill="#b68770"/>
    <path d="M85.8 59.1 Q90 60.3 94.2 59.1" stroke="#744f3f" stroke-width="0.92" fill="none" stroke-linecap="round"/>
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
    print("warrior pack regenerated")


if __name__ == "__main__":
    main()
