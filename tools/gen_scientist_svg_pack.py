#!/usr/bin/env python3
"""Regenerate complete scientist hero SVG pack with fit-aligned rarity progression.

Art direction: working lab equipment that escalates from chipped, taped-up
gear through certified instruments, blue-glass precision optics, violet
plasma prototypes, amber reactor-grade apparatus, up to quantum celestial
instruments. Slot semantics: Helmet = goggles, Shield = data tablet,
Weapon = analyzer with reagent bulb, Amulet = ID badge, Cloak = hazmat
drape / energy field. Footprints match the established hero body anchors.
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

ROOT = Path("icons/heroes/scientist")

# Casing face, casing shadow, outline, highlight, status accent, glass tint.
PAL = {
    "common": {
        "case": "#5a626e", "shadow": "#3f4651", "edge": "#2b323c",
        "hi": "#8a93a0", "trim": "#9aa3b0", "glass": "#aebdc9",
    },
    "uncommon": {
        "case": "#5d6a78", "shadow": "#414c59", "edge": "#2b3540",
        "hi": "#93a2b2", "trim": "#7ec983", "glass": "#bcd6c4",
    },
    "rare": {
        "case": "#4c5f76", "shadow": "#354459", "edge": "#232f40",
        "hi": "#8fb0d4", "trim": "#64a8e8", "glass": "#aed4f5",
    },
    "epic": {
        "case": "#544a6e", "shadow": "#3b3450", "edge": "#282239",
        "hi": "#a18fc7", "trim": "#b167d6", "glass": "#d3aef0",
    },
    "legendary": {
        "case": "#6a5839", "shadow": "#4a3d26", "edge": "#332a17",
        "hi": "#d3a967", "trim": "#ffb74d", "glass": "#ffd9a1",
    },
    "celestial": {
        "case": "#3d5a6a", "shadow": "#29424e", "edge": "#1a313c",
        "hi": "#8cd7e6", "trim": "#4dd9f0", "glass": "#b8f3ff",
    },
}


def tier_defs(rarity: str, prefix: str) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    parts = [
        linear_gradient(f"{prefix}Case", [("0%", p["hi"]), ("45%", p["case"]), ("100%", p["shadow"])]),
        linear_gradient(f"{prefix}Deep", [("0%", p["case"]), ("100%", p["edge"])]),
        linear_gradient(f"{prefix}Glass", [("0%", p["glass"]), ("100%", p["shadow"])]),
    ]
    if rarity in ("epic", "legendary", "celestial"):
        parts.append(radial_gradient(f"{prefix}Aura", [("0%", c, 0.5), ("70%", c, 0.16), ("100%", c, 0.0)]))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# HELMET — lab goggles strapped over the brow; HUD optics grow per tier.
# Footprint: x66-114, y38-55.
# ---------------------------------------------------------------------------

def helmet_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"cGogg{idx}"

    details = []
    if idx == 0:
        details.append(f'<path d="M84 41.5 L88 44.5" stroke="{p["edge"]}" stroke-width="0.7" opacity="0.85"/>')  # cracked lens
        details.append(f'<rect x="97.5" y="40" width="4.5" height="2.2" rx="0.5" fill="#c8c2ae" opacity="0.85"/>')  # tape patch
    if idx >= 1:
        details.append(
            f'<rect x="70.5" y="44.2" width="4.6" height="5" rx="1" fill="url(#{g}Deep)" stroke="{p["trim"]}" stroke-width="0.8"/>'
            f'<circle cx="72.8" cy="46.7" r="0.9" fill="{p["trim"]}"/>'
            f'<rect x="104.9" y="44.2" width="4.6" height="5" rx="1" fill="url(#{g}Deep)" stroke="{p["trim"]}" stroke-width="0.8"/>'
            f'<circle cx="107.2" cy="46.7" r="0.9" fill="{p["trim"]}"/>'
        )
    if idx >= 2:
        # Scanning HUD line sweeping across the right lens.
        details.append(
            f'<path d="M91.8 42.6 L98.6 42.6" stroke="{lc}" stroke-width="0.6" opacity="0.7">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 6;0 0" dur="2.8s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.7;0.25;0.7" dur="2.8s" repeatCount="indefinite"/></path>'
        )
        details.append(rune_strip(78.5, 38.2, 5, c, step=4.6, height=2.0, opacity=0.8))
    if idx >= 3:
        # Side analyzer arm folding over the left lens.
        details.append(
            f'<path d="M70 42 L66.5 38.5 L70.5 36.8" stroke="{c}" stroke-width="1" fill="none"/>'
            f'<circle cx="70.8" cy="36.6" r="1.7" fill="url(#{g}Deep)" stroke="{c}" stroke-width="0.8"/>'
            f'<circle cx="70.8" cy="36.6" r="0.6" fill="{lc}">'
            f'<animate attributeName="opacity" values="1;0.3;1" dur="1.6s" repeatCount="indefinite"/></circle>'
        )
    if idx >= 4:
        details.append(shimmer_line(73, 53.2, 107, 53.2, c, width=0.8, dur="2.6s", omin=0.3, omax=0.9))
        details.append(ember(76, 38, 0.6, lc, rise=5, dur="2.5s"))
        details.append(ember(103, 37, 0.55, c, rise=6, dur="3.1s", begin="0.9s"))
    if idx == 5:
        details.append(glow_pulse(90, 45, 27, 9.5, f"url(#{g}Aura)", dur="4s", omin=0.35, omax=0.75))
        details.append(constellation([(72, 37.5), (81, 35), (90, 34.2), (99, 35), (108, 37.5)], lc))
        details.append(orbit_glint(90, 45, 24, 0.95, lc, dur="9s"))

    body = f"""
  <g id="helmet_{rarity}">
    <path d="M67 44 Q90 39.5 113 44 L113 47 Q90 42.8 67 47 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.9"/>
    <rect x="78.6" y="40.6" width="10.4" height="8.2" rx="2.6" fill="url(#{g}Glass)" stroke="{p["edge"]}" stroke-width="1" opacity="0.92"/>
    <rect x="91" y="40.6" width="10.4" height="8.2" rx="2.6" fill="url(#{g}Glass)" stroke="{p["edge"]}" stroke-width="1" opacity="0.92"/>
    <path d="M89 44.4 L91 44.4" stroke="{p["edge"]}" stroke-width="1.1"/>
    <path d="M80.2 42.2 Q83 41 86 42" stroke="#ffffff" stroke-width="0.7" fill="none" opacity="0.65"/>
    <path d="M92.6 42.2 Q95.4 41 98.4 42" stroke="#ffffff" stroke-width="0.7" fill="none" opacity="0.65"/>
    <rect x="75.4" y="42.8" width="3.2" height="3.6" rx="0.8" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="0.7"/>
    <rect x="101.4" y="42.8" width="3.2" height="3.6" rx="0.8" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="0.7"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# CHESTPLATE — lab coat front: pocket protector, vial rack, hazard tags.
# Footprint: x64-116, y76-146.
# ---------------------------------------------------------------------------

def chestplate_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"cCoat{idx}"

    details = []
    # Pocket protector with pens on all tiers.
    details.append(
        f'<rect x="95" y="88" width="10" height="8.4" rx="1" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.7"/>'
        f'<path d="M97 88 L97 84.6 M99.6 88 L99.2 83.4 M102.2 88 L102.2 84.8" stroke="{p["trim"]}" stroke-width="1"/>'
    )
    if idx == 0:
        details.append(f'<ellipse cx="80" cy="92" rx="3.4" ry="2.4" fill="#7a6a3f" opacity="0.5"/>')  # chemical stain
        details.append(f'<ellipse cx="98" cy="124" rx="2.6" ry="1.9" fill="#3f5a46" opacity="0.45"/>')
        details.append(scratches([(76, 110, 81, 114), (100, 104, 104, 107)], color=p["edge"], width=0.6, opacity=0.6))
    if idx >= 1:
        # Buttoned placket + collar tabs.
        details.append(
            f'<circle cx="90" cy="98" r="1" fill="{p["trim"]}"/><circle cx="90" cy="110" r="1" fill="{p["trim"]}"/>'
            f'<circle cx="90" cy="122" r="1" fill="{p["trim"]}"/><circle cx="90" cy="134" r="1" fill="{p["trim"]}"/>'
            f'<path d="M84 80 L90 88 L96 80" stroke="{p["hi"]}" stroke-width="1" fill="none" opacity="0.85"/>'
        )
    if idx >= 2:
        # Vial rack strip with three reagent tubes.
        vials = []
        for i, (vx, fill_h) in enumerate([(75.5, 4.6), (80.3, 3.4), (85.1, 5.2)]):
            vials.append(
                f'<rect x="{vx}" y="100" width="3.2" height="7.6" rx="1.4" fill="url(#{g}Glass)" stroke="{p["edge"]}" stroke-width="0.6" opacity="0.95"/>'
                f'<rect x="{vx + 0.55}" y="{107 - fill_h}" width="2.1" height="{fill_h}" rx="0.9" fill="{c}" opacity="0.85">'
                f'<animate attributeName="opacity" values="0.85;0.55;0.85" dur="{2.3 + 0.5 * i}s" repeatCount="indefinite"/></rect>'
            )
        details.append(f'<rect x="74" y="99" width="15.6" height="9.8" rx="1.4" fill="none" stroke="{p["trim"]}" stroke-width="0.8"/>' + "".join(vials))
    if idx >= 3:
        # Radiation-grade seal patch.
        details.append(
            f'<circle cx="99" cy="112" r="4.2" fill="url(#{g}Deep)" stroke="{c}" stroke-width="0.9"/>'
            f'<path d="M99 112 L99 108.4 A3.6 3.6 0 0 1 102.1 110.2 Z M99 112 L95.9 110.2 A3.6 3.6 0 0 1 99 108.4 Z" fill="{c}" opacity="0.9"/>'
            f'<circle cx="99" cy="112" r="1" fill="{lc}"/>'
        )
    if idx >= 4:
        details.append(
            f'<path d="M68 84 Q90 70 112 84" stroke="{c}" stroke-width="1.2" fill="none" opacity="0.8"/>'
        )
        details.append(shimmer_line(90, 84, 90, 142, lc, width=0.7, dur="3.2s", omin=0.2, omax=0.65))
        details.append(ember(82, 118, 0.7, lc, rise=9, dur="2.9s"))
        details.append(ember(101, 100, 0.6, c, rise=8, dur="3.4s", begin="1.2s"))
    if idx == 5:
        details.append(glow_pulse(90, 106, 25, 18, f"url(#{g}Aura)", dur="4.5s", omin=0.3, omax=0.7))
        details.append(constellation([(77, 95), (84, 90), (93, 90), (101, 95), (102, 104), (95, 110), (85, 109), (78, 103), (77, 95)], lc, dot_r=0.75))
        details.append(orbit_glint(90, 104, 20, 1.0, lc, dur="10.5s"))

    body = f"""
  <g id="chestplate_{rarity}">
    <path d="M70 79 L110 79 Q115 86 115 97 L112 145 L68 145 L65 97 Q65 86 70 79 Z"
          fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="1.05"/>
    <path d="M76 83 L89 83 L89 143 L75.5 143 Z" fill="url(#{g}Deep)" opacity="0.55"/>
    <path d="M104 83 L91 83 L91 143 L104.5 143 Z" fill="url(#{g}Deep)" opacity="0.55"/>
    <path d="M76 83 L83.5 83 L78.5 94 L74.5 90 Z" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="0.7"/>
    <path d="M104 83 L96.5 83 L101.5 94 L105.5 90 Z" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="0.7"/>
    <path d="M90 83 L90 143" stroke="{p["edge"]}" stroke-width="0.9" opacity="0.8"/>
    <rect x="72.5" y="128" width="9.6" height="10" rx="1.2" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.7" opacity="0.9"/>
    <rect x="97.9" y="128" width="9.6" height="10" rx="1.2" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.7" opacity="0.9"/>
    <path d="M73 85 Q80 82.6 87 84.4" stroke="{p["hi"]}" stroke-width="0.7" fill="none" opacity="0.55"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# GAUNTLETS — sealed lab gloves: cuff rings, grip pads, status LEDs.
# Footprints: left x37-63 / right x117-143, y132-158.
# ---------------------------------------------------------------------------

def gauntlets_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"cGlove{idx}"

    def one(x0: float, mirror: bool) -> str:
        xm = x0 + 13
        parts = [
            f'<path d="M{x0+1.5} 134 L{x0+24.5} 134 L{x0+23.5} 145 L{x0+2.5} 145 Z" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="1"/>',
            f'<path d="M{x0+2.5} 145 L{x0+23.5} 145 L{x0+22} 157 L{x0+4} 157 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.9"/>',
            f'<path d="M{x0+2} 141 L{x0+24} 141" stroke="{p["hi"]}" stroke-width="0.6" opacity="0.55"/>',
            # Sealed cuff ring.
            f'<rect x="{x0+2}" y="143.6" width="22" height="2.8" rx="1.3" fill="url(#{g}Deep)" stroke="{p["trim"]}" stroke-width="0.7"/>',
        ]
        if idx == 0:
            parts.append(f'<rect x="{xm-3}" y="136.4" width="6" height="2.4" rx="0.5" fill="#c8c2ae" opacity="0.8"/>')  # tape
            parts.append(scratches([(x0 + 5, 149, x0 + 9, 152)], color=p["edge"], width=0.55, opacity=0.7))
        if idx >= 1:
            parts.append(
                f'<circle cx="{x0+5.5}" cy="145" r="0.8" fill="{p["trim"]}">'
                f'<animate attributeName="opacity" values="1;0.35;1" dur="2.2s" repeatCount="indefinite"/></circle>'
            )
        if idx >= 2:
            # Grip pads.
            parts.append(
                f'<rect x="{x0+6}" y="150" width="3.4" height="4.6" rx="1" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="0.5"/>'
                f'<rect x="{x0+11}" y="151" width="3.4" height="4.6" rx="1" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="0.5"/>'
                f'<rect x="{x0+16}" y="150" width="3.4" height="4.6" rx="1" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="0.5"/>'
            )
            parts.append(rune_strip(x0 + 6, 136.6, 3, c, step=5.0, height=2.0, opacity=0.85))
        if idx >= 3:
            parts.append(
                f'<circle cx="{xm}" cy="140.4" r="2" fill="url(#{g}Deep)" stroke="{c}" stroke-width="0.8"/>'
                f'<circle cx="{xm}" cy="140.4" r="0.7" fill="{lc}">'
                f'<animate attributeName="opacity" values="1;0.4;1" dur="1.8s" repeatCount="indefinite"/></circle>'
            )
        if idx >= 4:
            parts.append(
                f'<path d="M{x0+3} 156 L{x0+23} 156" stroke="{c}" stroke-width="0.9" opacity="0.5">'
                f'<animate attributeName="opacity" values="0.5;1;0.5" dur="2.5s" repeatCount="indefinite"/></path>'
            )
            parts.append(ember(xm + (4 if mirror else -4), 136.5, 0.6, lc, rise=6, dur="2.9s", begin="0.8s" if mirror else "0s"))
        if idx == 5:
            parts.append(glow_pulse(xm, 145, 13, 10, f"url(#{g}Aura)", dur="4.3s", omin=0.3, omax=0.7))
            parts.append(constellation([(x0 + 5, 137.6), (xm, 135.6), (x0 + 21, 137.6)], lc, dot_r=0.7))
        return "".join(parts)

    body = f"""
  <g id="gauntlets_{rarity}">
    {one(37, False)}
    {one(117, True)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# BOOTS — safety shoes: composite toe caps, hazard stripe, tread sole.
# Footprints: left x41-79 / right x101-139, y184-210.
# ---------------------------------------------------------------------------

def boots_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"cBoot{idx}"

    def one(x0: float, flip: bool) -> str:
        xm = x0 + 19
        parts = [
            f'<path d="M{x0+4} 186 L{x0+32} 186 L{x0+34} 198 L{x0+2} 198 Z" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="1"/>',
            f'<path d="M{x0+1} 197.5 L{x0+35} 197.5 L{x0+37.5} 206.5 L{x0-0.5} 206.5 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="1"/>',
            # Tread sole.
            f'<path d="M{x0-0.5} 205.6 L{x0+37.5} 205.6 L{x0+37.5} 209 L{x0-0.5} 209 Z" fill="{p["edge"]}"/>',
            f'<path d="M{x0+4} 206.4 L{x0+5.6} 208.4 M{x0+10} 206.4 L{x0+11.6} 208.4 M{x0+16} 206.4 L{x0+17.6} 208.4 M{x0+22} 206.4 L{x0+23.6} 208.4 M{x0+28} 206.4 L{x0+29.6} 208.4" stroke="{p["shadow"]}" stroke-width="1.1"/>',
            # Composite toe cap.
            f'<path d="M{x0+25} 198 L{x0+32.5} 186.6 L{x0+34} 198 Z" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="0.7" opacity="0.9"/>',
        ]
        if idx == 0:
            parts.append(scratches([(x0 + 7, 200.5, x0 + 12, 203.5), (x0 + 25, 188.5, x0 + 29, 191)], color=p["edge"], width=0.6, opacity=0.7))
        if idx >= 1:
            # Hazard stripe band.
            stripe = "".join(
                f'<path d="M{x0 + 5 + i * 6} 192 L{x0 + 8 + i * 6} 189" stroke="{p["trim"]}" stroke-width="1.6"/>'
                for i in range(4)
            )
            parts.append(f'<rect x="{x0+4}" y="188.6" width="26" height="3.8" rx="0.8" fill="{p["shadow"]}" opacity="0.8"/>{stripe}')
        if idx >= 2:
            parts.append(rune_strip(x0 + 9, 200.8, 4, c, step=4.5, height=2.2, opacity=0.8))
        if idx >= 3:
            parts.append(
                f'<circle cx="{x0+7}" cy="195.4" r="1.4" fill="url(#{g}Deep)" stroke="{c}" stroke-width="0.7"/>'
                f'<circle cx="{x0+7}" cy="195.4" r="0.5" fill="{lc}">'
                f'<animate attributeName="opacity" values="1;0.35;1" dur="2s" repeatCount="indefinite"/></circle>'
            )
        if idx >= 4:
            parts.append(shimmer_line(x0 + 1, 207.4, x0 + 36, 207.4, c, width=1.0, dur="2.7s", omin=0.3, omax=0.9))
            parts.append(ember(xm + (3 if flip else -3), 195, 0.55, lc, rise=6, dur="3.2s", begin="1.1s" if flip else "0s"))
        if idx == 5:
            parts.append(glow_pulse(xm, 198, 18, 8, f"url(#{g}Aura)", dur="4.8s", omin=0.25, omax=0.6))
            parts.append(constellation([(x0 + 8, 189.5), (xm, 187.4), (x0 + 30, 189.5)], lc, dot_r=0.65))
        return "".join(parts)

    body = f"""
  <g id="boots_{rarity}">
    {one(41, False)}
    {one(101, True)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# SHIELD — research tablet: screen bezel, live data trace, port row.
# Footprint: x28-66, y98-152.
# ---------------------------------------------------------------------------

def shield_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"cTab{idx}"

    details = []
    if idx == 0:
        # Cracked screen corner + sticky note.
        details.append(f'<path d="M56 107 L59.5 111 L57 112.5 M58 108.5 L60 113" stroke="{p["edge"]}" stroke-width="0.6" fill="none" opacity="0.85"/>')
        details.append(f'<rect x="36" y="134" width="7.5" height="7" fill="#d8cf9a" opacity="0.9" transform="rotate(-6 39.7 137.5)"/>')
    if idx >= 1:
        # Status LED row.
        details.append(
            f'<circle cx="38" cy="146.4" r="0.9" fill="{p["trim"]}">'
            f'<animate attributeName="opacity" values="1;0.3;1" dur="2.1s" repeatCount="indefinite"/></circle>'
            f'<circle cx="41.6" cy="146.4" r="0.9" fill="{p["trim"]}" opacity="0.75"/>'
            f'<circle cx="45.2" cy="146.4" r="0.9" fill="{p["shadow"]}"/>'
        )
    if idx >= 2:
        # Live data trace drifting across the screen.
        details.append(
            f'<path d="M36 124 L40 124 L42.5 118.5 L45.5 129 L48.5 121 L51 124 L58 124" '
            f'stroke="{lc}" stroke-width="0.9" fill="none" opacity="0.9">'
            f'<animate attributeName="opacity" values="0.9;0.45;0.9" dur="2.4s" repeatCount="indefinite"/></path>'
        )
        details.append(rune_strip(37, 111.2, 5, c, step=4.2, height=2.2, opacity=0.8))
    if idx >= 3:
        # Molecule diagram in screen corner.
        details.append(
            f'<circle cx="40" cy="133.5" r="1.3" fill="none" stroke="{c}" stroke-width="0.6"/>'
            f'<circle cx="45.5" cy="131" r="1.3" fill="none" stroke="{c}" stroke-width="0.6"/>'
            f'<circle cx="44" cy="136.5" r="1.3" fill="none" stroke="{c}" stroke-width="0.6"/>'
            f'<path d="M41.2 132.9 L44.3 131.6 M44.6 132.2 L44.2 135.2 M41.1 134.3 L42.8 135.9" stroke="{c}" stroke-width="0.55"/>'
        )
    if idx >= 4:
        details.append(
            f'<rect x="33.5" y="105.5" width="27" height="39" rx="2" fill="none" stroke="{c}" stroke-width="0.8" opacity="0.6">'
            f'<animate attributeName="opacity" values="0.6;1;0.6" dur="2.6s" repeatCount="indefinite"/></rect>'
        )
        details.append(ember(39, 119, 0.65, lc, rise=8, dur="2.8s"))
        details.append(ember(53, 127, 0.6, c, rise=7, dur="3.3s", begin="1s"))
    if idx == 5:
        details.append(glow_pulse(47, 125, 20, 26, f"url(#{g}Aura)", dur="4.3s", omin=0.3, omax=0.7))
        details.append(constellation([(38, 112), (47, 108.6), (56, 112), (58, 124), (51, 134), (40, 132), (38, 112)], lc, dot_r=0.75))
        details.append(orbit_glint(47, 124, 16.5, 0.95, lc, dur="9.5s"))

    body = f"""
  <g id="shield_{rarity}">
    <rect x="30" y="100.5" width="34" height="49" rx="3.4" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="1.15"/>
    <rect x="33" y="104" width="28" height="42" rx="2" fill="url(#{g}Deep)"/>
    <rect x="34.5" y="106.5" width="25" height="37" rx="1.6" fill="{p["shadow"]}" opacity="0.9"/>
    <path d="M36 109 L58 109" stroke="{p["hi"]}" stroke-width="0.6" opacity="0.5"/>
    <path d="M48 101.8 L52 101.8" stroke="{p["edge"]}" stroke-width="0.8"/>
    <path d="M52 148.6 L56 148.6 M46 148.6 L50 148.6" stroke="{p["edge"]}" stroke-width="1" opacity="0.85"/>
    <path d="M31.5 104 Q33 101.6 36 101.2" stroke="{p["hi"]}" stroke-width="0.7" fill="none" opacity="0.6"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# WEAPON — handheld analyzer on the -24° axis: grip, stem and reagent bulb
# with live contents; escalates to plasma instrument.
# ---------------------------------------------------------------------------

def weapon_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"cInst{idx}"

    details = []
    if idx == 0:
        details.append(f'<path d="M133 109 L137 113" stroke="{p["edge"]}" stroke-width="0.6" opacity="0.9"/>')  # crack
        details.append(f'<rect x="118" y="132" width="5" height="2.2" rx="0.5" fill="#c8c2ae" opacity="0.85" transform="rotate(8 120.5 133)"/>')
    if idx >= 1:
        details.append(
            f'<circle cx="120.3" cy="156" r="1" fill="{p["trim"]}">'
            f'<animate attributeName="opacity" values="1;0.35;1" dur="2s" repeatCount="indefinite"/></circle>'
        )
    if idx >= 2:
        # Bubbles rising in the reagent bulb.
        details.append(
            f'<circle cx="135" cy="112" r="0.9" fill="{lc}" opacity="0.85">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -7" dur="2.2s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.85;0.85;0" dur="2.2s" repeatCount="indefinite"/></circle>'
            f'<circle cx="139" cy="114" r="0.7" fill="{lc}" opacity="0.75">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -8" dur="2.9s" begin="0.7s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.75;0.75;0" dur="2.9s" begin="0.7s" repeatCount="indefinite"/></circle>'
        )
        details.append(rune_strip(117.2, 140.5, 1, c, step=4, height=2.4, opacity=0.9))
    if idx >= 3:
        # Coil winding around the stem.
        details.append(
            f'<path d="M126.5 126 Q130 124.5 128.5 122 Q126 120.5 129.5 118.5 Q133 117 131 114.5" '
            f'stroke="{c}" stroke-width="0.9" fill="none" opacity="0.9"/>'
        )
    if idx >= 4:
        details.append(
            f'<circle cx="137" cy="108.5" r="8.6" fill="none" stroke="{c}" stroke-width="0.8" opacity="0.55">'
            f'<animate attributeName="opacity" values="0.55;0.95;0.55" dur="2.1s" repeatCount="indefinite"/></circle>'
        )
        details.append(ember(133, 102, 0.7, lc, rise=8, dur="2.4s"))
        details.append(ember(141, 104, 0.6, c, rise=7, dur="2.9s", begin="0.9s"))
    if idx == 5:
        details.append(glow_pulse(137, 108, 14, 11, f"url(#{g}Aura)", dur="3.7s", omin=0.35, omax=0.8))
        details.append(constellation([(129, 115), (134, 109.5), (140, 105), (146, 102)], lc, dot_r=0.7))
        details.append(orbit_glint(137, 108.5, 11, 0.85, lc, dur="6.5s"))

    body = f"""
  <g id="weapon_{rarity}" transform="rotate(-24 121 131)">
    <rect x="116.6" y="128" width="7.4" height="34" rx="2.9" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.95"/>
    <path d="M116.8 134 L123.8 134 M116.8 150 L123.8 150" stroke="{p["trim"]}" stroke-width="1.5" opacity="0.95"/>
    <rect x="118.5" y="158" width="3.6" height="6" rx="1.5" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="0.7"/>
    <path d="M121.5 128 L127 121 L131 116" stroke="url(#{g}Case)" stroke-width="4.6" stroke-linecap="round"/>
    <path d="M121.5 128 L127 121 L131 116" stroke="{p["edge"]}" stroke-width="0.7" opacity="0.5"/>
    <circle cx="137" cy="108.5" r="7.8" fill="url(#{g}Glass)" stroke="{p["edge"]}" stroke-width="1" opacity="0.95"/>
    <path d="M131.5 104.5 Q134 101.5 138 101.2" stroke="#ffffff" stroke-width="0.8" fill="none" opacity="0.7"/>
    <path d="M130.4 110.5 A6.8 6.8 0 0 0 143.2 110.5 Q137 114.5 130.4 110.5 Z" fill="{c}" opacity="0.8"/>
    <circle cx="137" cy="99.6" r="1.6" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="0.7"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# CLOAK — hazmat drape evolving into a containment energy field.
# Footprint: x54-126, y72-192.
# ---------------------------------------------------------------------------

def cloak_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"cHaz{idx}"

    details = []
    if idx == 0:
        details.append(f'<rect x="63" y="150" width="8" height="3" rx="0.6" fill="#c8c2ae" opacity="0.8" transform="rotate(-7 67 151.5)"/>')
        details.append(f'<path d="M112 178 L116 184 L119 177.5 L115 175 Z" fill="url(#{g}Deep)" opacity="0.75"/>')
    if idx >= 1:
        # Sealed zipper seam.
        details.append(
            f'<path d="M90 78 L90 182" stroke="{p["trim"]}" stroke-width="1" opacity="0.6"/>'
            f'<rect x="88.8" y="84" width="2.4" height="3.4" rx="0.7" fill="{p["trim"]}" opacity="0.9"/>'
        )
    if idx >= 2:
        details.append(rune_strip(61.5, 172.5, 3, c, step=4.4, height=2.4, opacity=0.65))
        details.append(rune_strip(105.5, 172.5, 3, c, step=4.4, height=2.4, opacity=0.65))
        details.append(
            f'<path d="M62 110 Q60 140 61.5 172 M118 110 Q120 140 118.5 172" stroke="{p["trim"]}" stroke-width="0.9" fill="none" opacity="0.6"/>'
        )
    if idx >= 3:
        # Biohazard-style trefoil on the left panel.
        details.append(
            f'<circle cx="68" cy="128" r="1.3" fill="none" stroke="{c}" stroke-width="0.7"/>'
            f'<path d="M68 124.4 A3.6 3.6 0 0 1 71.2 130 M68 124.4 A3.6 3.6 0 0 0 64.8 130 M64.9 130.1 Q68 132.4 71.1 130.1" '
            f'stroke="{c}" stroke-width="0.85" fill="none" opacity="0.9"/>'
        )
    if idx >= 4:
        # Hex containment cells fading in and out.
        hexes = []
        for hx, hy, d in [(64, 104, "3.4s"), (115, 120, "4.1s"), (66, 148, "3.8s")]:
            hexes.append(
                f'<path d="M{hx} {hy-3.4} L{hx+3} {hy-1.7} L{hx+3} {hy+1.7} L{hx} {hy+3.4} L{hx-3} {hy+1.7} L{hx-3} {hy-1.7} Z" '
                f'fill="none" stroke="{c}" stroke-width="0.65" opacity="0.55">'
                f'<animate attributeName="opacity" values="0.55;0.15;0.55" dur="{d}" repeatCount="indefinite"/></path>'
            )
        details.append("".join(hexes))
        details.append(ember(67, 160, 0.65, lc, rise=11, dur="3.6s"))
        details.append(ember(114, 152, 0.6, c, rise=10, dur="3.1s", begin="1.3s"))
    if idx == 5:
        details.append(glow_pulse(90, 134, 36, 42, f"url(#{g}Aura)", dur="5.5s", omin=0.2, omax=0.45))
        details.append(constellation([(64, 108), (69, 124), (66, 142), (71, 158), (67, 174)], lc, dot_r=0.7))
        details.append(constellation([(116, 108), (111, 124), (114, 142), (109, 158), (113, 174)], lc, dot_r=0.7))

    body = f"""
  <g id="cloak_{rarity}" opacity="0.95">
    <path d="M64 75 Q90 70 116 75 L124 92 L120 188 Q105 183 90 183 Q75 183 60 188 L56 92 Z"
          fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="1" opacity="0.55"/>
    <path d="M66 92 Q64 138 63 182 M114 92 Q116 138 117 182" stroke="{p["edge"]}" stroke-width="0.75" fill="none" opacity="0.5"/>
    <path d="M72 76 L78 74.8 L80 88 L73 90 Z M108 76 L102 74.8 L100 88 L107 90 Z" fill="url(#{g}Deep)" opacity="0.8"/>
    <path d="M70 150 L61 189 L74 189 Z" fill="url(#{g}Deep)" opacity="0.5"/>
    <path d="M110 150 L119 188 L106 189 Z" fill="url(#{g}Deep)" opacity="0.5"/>
    <path d="M79 76 Q90 73.4 101 76 L100 80.6 Q90 78.4 80 80.6 Z" fill="url(#{g}Deep)" stroke="{p["edge"]}" stroke-width="0.7"/>
    <circle cx="90" cy="78.5" r="1.4" fill="{c}" opacity="0.9"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# AMULET — clip-on ID badge maturing into an atom-orbit eureka emblem.
# Footprint: x80-102, y88-114.
# ---------------------------------------------------------------------------

def amulet_svg(rarity: str, idx: int) -> str:
    p = PAL[rarity]
    c = RARITY_COLORS[rarity]
    lc = RARITY_LIGHT[rarity]
    g = f"cBadge{idx}"

    details = []
    if idx >= 1:
        details.append(f'<rect x="84.6" y="95.4" width="10.8" height="13.2" rx="1.4" fill="none" stroke="{p["trim"]}" stroke-width="0.9" opacity="0.95"/>')
    if idx >= 2:
        # Electron orbit rings.
        details.append(
            f'<ellipse cx="90" cy="102" rx="9.4" ry="3.6" fill="none" stroke="{c}" stroke-width="0.6" opacity="0.6">'
            f'<animateTransform attributeName="transform" type="rotate" values="0 90 102;360 90 102" dur="7s" repeatCount="indefinite"/></ellipse>'
            f'<ellipse cx="90" cy="102" rx="9.4" ry="3.6" fill="none" stroke="{c}" stroke-width="0.6" opacity="0.6" transform="rotate(60 90 102)"/>'
        )
    if idx >= 3:
        details.append(
            f'<circle cx="98.6" cy="99" r="1" fill="{lc}">'
            f'<animateTransform attributeName="transform" type="rotate" values="0 90 102;360 90 102" dur="4.5s" repeatCount="indefinite"/></circle>'
        )
    if idx >= 4:
        details.append(
            f'<circle cx="90" cy="102" r="3.4" fill="{c}" opacity="0.3">'
            f'<animate attributeName="r" values="2.8;5;2.8" dur="2.4s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.3;0.12;0.3" dur="2.4s" repeatCount="indefinite"/></circle>'
        )
        details.append(ember(86, 95, 0.5, lc, rise=5, dur="2.6s"))
    if idx == 5:
        details.append(glow_pulse(90, 102, 12.5, 11, f"url(#{g}Aura)", dur="3.7s", omin=0.35, omax=0.8))
        details.append(orbit_glint(90, 102, 11.4, 0.85, lc, dur="6s"))
        details.append(constellation([(84.5, 94), (90, 92), (95.5, 94)], lc, dot_r=0.6))

    body = f"""
  <g id="amulet_{rarity}">
    <path d="M83 88 Q90 92.4 97 88" stroke="{p["trim"]}" stroke-width="1.1" fill="none" opacity="0.95"/>
    <rect x="88.6" y="91.4" width="2.8" height="2.6" rx="0.6" fill="{p["trim"]}"/>
    <rect x="83.6" y="94.4" width="12.8" height="15.2" rx="1.8" fill="url(#{g}Case)" stroke="{p["edge"]}" stroke-width="1"/>
    <rect x="85.6" y="96.6" width="8.8" height="4" rx="0.8" fill="url(#{g}Glass)" opacity="0.95"/>
    <path d="M86.2 103.4 L93.8 103.4 M86.2 105.4 L92 105.4 M86.2 107.4 L93 107.4" stroke="{p["shadow"]}" stroke-width="0.7" opacity="0.9"/>
    <circle cx="90" cy="102" r="1.1" fill="{c}" opacity="0.95"/>
    {''.join(details)}
  </g>
"""
    return wrap(body, tier_defs(rarity, g))


# ---------------------------------------------------------------------------
# FX tiers — reaction glow and rising charged motes.
# ---------------------------------------------------------------------------

def fx_epic() -> str:
    c = RARITY_COLORS["epic"]
    lc = RARITY_LIGHT["epic"]
    defs = radial_gradient("cFxEpic", [("0%", c, 0.38), ("65%", c, 0.12), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_epic">
    <ellipse cx="90" cy="120" rx="52" ry="78" fill="url(#cFxEpic)"/>
    <ellipse cx="90" cy="201" rx="40" ry="8.5" fill="{c}" opacity="0.28">
      <animate attributeName="opacity" values="0.28;0.48;0.28" dur="3.2s" repeatCount="indefinite"/>
    </ellipse>
    <path d="M52 164 Q48 134 58 110 M128 164 Q132 134 122 110" stroke="{c}" stroke-width="1.05" fill="none" opacity="0.5"/>
    <path d="M54 124 L57 124 M55.5 122.5 L55.5 125.5" stroke="{lc}" stroke-width="0.7" opacity="0.8">
      <animateTransform attributeName="transform" type="translate" values="0 0;2 -8;0 0" dur="3.9s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.8;0.25;0.8" dur="3.9s" repeatCount="indefinite"/>
    </path>
    {ember(60, 150, 0.95, lc, rise=16, dur="3.5s")}
    {ember(121, 154, 0.85, c, rise=18, dur="4.2s", begin="1.4s")}
    {ember(75, 178, 0.75, lc, rise=13, dur="3s", begin="0.7s")}
  </g>
"""
    return wrap(body, defs)


def fx_legendary() -> str:
    c = RARITY_COLORS["legendary"]
    lc = RARITY_LIGHT["legendary"]
    defs = radial_gradient("cFxLeg", [("0%", c, 0.42), ("60%", c, 0.15), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_legendary">
    <ellipse cx="90" cy="118" rx="58" ry="86" fill="url(#cFxLeg)"/>
    <ellipse cx="90" cy="202" rx="46" ry="9" fill="{c}" opacity="0.32">
      <animate attributeName="opacity" values="0.32;0.55;0.32" dur="2.8s" repeatCount="indefinite"/>
    </ellipse>
    <path d="M48 176 Q42 128 60 96 M132 176 Q138 128 120 96" stroke="{c}" stroke-width="1.25" fill="none" opacity="0.55"/>
    <ellipse cx="58" cy="140" rx="6.5" ry="2.6" fill="none" stroke="{lc}" stroke-width="0.7" opacity="0.6">
      <animateTransform attributeName="transform" type="rotate" values="0 58 140;360 58 140" dur="6s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="123" cy="128" rx="6.5" ry="2.6" fill="none" stroke="{lc}" stroke-width="0.7" opacity="0.55" transform="rotate(45 123 128)">
      <animate attributeName="opacity" values="0.55;0.2;0.55" dur="3.4s" repeatCount="indefinite"/>
    </ellipse>
    {ember(62, 160, 1.05, lc, rise=22, dur="3.3s")}
    {ember(118, 164, 0.95, c, rise=24, dur="3.9s", begin="1.2s")}
    {ember(90, 186, 0.85, lc, rise=18, dur="2.9s", begin="0.5s")}
  </g>
"""
    return wrap(body, defs)


def fx_celestial() -> str:
    c = RARITY_COLORS["celestial"]
    lc = RARITY_LIGHT["celestial"]
    defs = radial_gradient("cFxCel", [("0%", c, 0.38), ("55%", c, 0.13), ("100%", c, 0.0)])
    body = f"""
  <g id="fx_celestial">
    <rect x="56" y="0" width="68" height="220" fill="{c}" opacity="0.05"/>
    <ellipse cx="90" cy="116" rx="60" ry="92" fill="url(#cFxCel)"/>
    <ellipse cx="90" cy="203" rx="48" ry="9" fill="{c}" opacity="0.28">
      <animate attributeName="opacity" values="0.28;0.5;0.28" dur="3.7s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="90" cy="120" rx="50" ry="76" fill="none" stroke="{c}" stroke-width="0.85" opacity="0.38">
      <animate attributeName="opacity" values="0.38;0.65;0.38" dur="4.5s" repeatCount="indefinite"/>
    </ellipse>
    {constellation([(50, 58), (64, 40), (82, 32), (102, 33), (119, 43), (130, 60)], lc)}
    {constellation([(48, 148), (58, 168), (74, 182)], lc, dot_r=0.7)}
    {constellation([(132, 148), (122, 168), (106, 182)], lc, dot_r=0.7)}
    {orbit_glint(90, 118, 54, 1.25, lc, dur="12.5s")}
    {ember(66, 152, 0.75, lc, rise=26, dur="4.7s")}
    {ember(114, 158, 0.75, lc, rise=24, dur="5.3s", begin="2s")}
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
      <stop offset="0%" stop-color="#f0f3f8"/>
      <stop offset="100%" stop-color="#d8dde6"/>
    </linearGradient>
    <linearGradient id="innerGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#4a5872"/>
      <stop offset="100%" stop-color="#2a364b"/>
    </linearGradient>
    <linearGradient id="pantsGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2a3951"/>
      <stop offset="100%" stop-color="#172334"/>
    </linearGradient>
    <linearGradient id="skinGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#f4d7c0"/>
      <stop offset="100%" stop-color="#ddb193"/>
    </linearGradient>
    <linearGradient id="hairGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#5c544f"/>
      <stop offset="100%" stop-color="#35302d"/>
    </linearGradient>
    <radialGradient id="shadowGrad" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0%" stop-color="#000" stop-opacity="0.32"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <ellipse cx="90" cy="206" rx="40" ry="7" fill="url(#shadowGrad)"/>

  <g id="hero_body">
    <animateTransform attributeName="transform" type="translate" values="0 0;0 -0.8;0 0" dur="4.5s" repeatCount="indefinite"/>

    <path d="M73 166 Q71 186 74 201 L84.5 201 Q85.5 179 82.5 166 Z" fill="url(#pantsGrad)"/>
    <path d="M98 166 Q96 179 97 201 L107.5 201 Q110.5 184 107.2 166 Z" fill="url(#pantsGrad)"/>
    <path d="M73 193 L85.5 193 L87 201 L71.5 201 Z" fill="#404b5c"/>
    <path d="M96 193 L108.5 193 L110 201 L94.5 201 Z" fill="#404b5c"/>

    <circle cx="69.5" cy="88" r="7" fill="#d8dee8"/>
    <circle cx="110.5" cy="88" r="7" fill="#d8dee8"/>
    <path d="M71 72 Q61 86 63 103 L68 166 L112 166 L117 103 Q119 86 109 72 Z" fill="url(#coatGrad)" stroke="#b6bdc9" stroke-width="0.9"/>
    <path d="M79 78 L102 78 L104 152 L77 152 Z" fill="url(#innerGrad)"/>
    <path d="M80 79 L85.8 92 M100 79 L94.2 92" stroke="#d7deea" stroke-width="1.1"/>
    <path d="M90 79 L90 153" stroke="#1e2e45" stroke-width="1"/>
    <path d="M76 160 L105 160 Q103 166 101 170 L80 170 Q77 166 76 160 Z" fill="#586070"/>
    <rect x="88.5" y="160.4" width="3" height="7" rx="0.8" fill="#95a8bf"/>

    <path d="M63 92 Q57 102 58 116 L59 145 Q59 151 63 151 Q67 151 68 145 L69 116 Q69 103 72 93 Z" fill="url(#coatGrad)" stroke="#b6bdc9" stroke-width="0.8"/>
    <path d="M117 92 Q123 102 122 116 L121 145 Q121 151 117 151 Q113 151 112 145 L111 116 Q111 103 108 93 Z" fill="url(#coatGrad)" stroke="#b6bdc9" stroke-width="0.8"/>
    <ellipse cx="60.5" cy="149" rx="3.5" ry="3.9" fill="url(#skinGrad)"/>
    <ellipse cx="119.5" cy="149" rx="3.5" ry="3.9" fill="url(#skinGrad)"/>

    <rect x="85.2" y="63.5" width="9.6" height="10" rx="3.8" fill="url(#skinGrad)"/>
    <ellipse cx="90" cy="49" rx="13.2" ry="15.2" fill="url(#skinGrad)"/>
    <path d="M77.2 45 Q82 34 90 33 Q99 34 102.8 45 L101.5 47.8 Q90 44 78.5 47.8 Z" fill="url(#hairGrad)"/>

    <rect x="80.8" y="45.8" width="8" height="5.8" rx="1.4" fill="none" stroke="#cfeeff" stroke-width="0.9"/>
    <rect x="91.2" y="45.8" width="8" height="5.8" rx="1.4" fill="none" stroke="#cfeeff" stroke-width="0.9"/>
    <path d="M88.8 48.7 L91.2 48.7" stroke="#cfeeff" stroke-width="0.85"/>
    <path d="M80.8 48.7 L79.3 48.1 M99.2 48.7 L100.7 48.1" stroke="#cfeeff" stroke-width="0.7" opacity="0.75"/>

    <g id="eyes">
      <animateTransform attributeName="transform" type="translate"
        values="0 0; -0.5 0.1; 0.8 -0.2; 0 0; 0.3 0.1; 0 0"
        keyTimes="0;0.13;0.24;0.57;0.75;1" dur="4.1s" repeatCount="indefinite"/>
      <ellipse cx="85.1" cy="49.1" rx="1.8" ry="1.5" fill="#f4fbff">
        <animate attributeName="ry" values="1.5;1.5;0.2;1.5;1.5;0.2;1.5" keyTimes="0;0.2;0.22;0.24;0.68;0.70;1" dur="5.1s" repeatCount="indefinite"/>
      </ellipse>
      <ellipse cx="94.9" cy="49.1" rx="1.8" ry="1.5" fill="#f4fbff">
        <animate attributeName="ry" values="1.5;1.5;0.2;1.5;1.5;0.2;1.5" keyTimes="0;0.2;0.22;0.24;0.68;0.70;1" dur="5.1s" repeatCount="indefinite"/>
      </ellipse>
      <circle cx="85.1" cy="49.1" r="0.65" fill="#25313f"/>
      <circle cx="94.9" cy="49.1" r="0.65" fill="#25313f"/>
    </g>

    <path d="M88.7 52.8 L89.4 56.8 L90.6 56.8 L91.3 52.8" fill="#b68770"/>
    <path d="M86.1 59.2 Q90 60.6 93.9 59.2" stroke="#745345" stroke-width="0.9" fill="none" stroke-linecap="round"/>
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
    print("scientist pack regenerated")


if __name__ == "__main__":
    main()
