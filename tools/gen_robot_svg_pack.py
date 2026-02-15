#!/usr/bin/env python3
"""Regenerate complete robot hero gear SVG pack with fit-aligned rarity progression."""

from __future__ import annotations

from pathlib import Path


ROOT = Path("icons/heroes/robot")
RARITIES = ["common", "uncommon", "rare", "epic", "legendary", "celestial"]
RARITY_COLORS = {
    "common": "#9E9E9E",
    "uncommon": "#4CAF50",
    "rare": "#2196F3",
    "epic": "#9C27B0",
    "legendary": "#FF9800",
    "celestial": "#00E5FF",
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def wrap(body: str, defs: str = "") -> str:
    defs_block = f"<defs>\n{defs}\n</defs>\n" if defs else ""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 220" width="180" height="220">\n'
        f"{defs_block}{body}\n"
        "</svg>"
    )


def helmet_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    visor = ""
    if idx >= 1:
        visor = f'<rect x="74" y="44" width="32" height="8" rx="3" fill="{c}" opacity="0.22"/>'
    side = ""
    if idx >= 2:
        side = (
            f'<rect x="66.5" y="44" width="6" height="10" rx="2" fill="#2f415f" stroke="{c}" stroke-width="0.9"/>'
            f'<rect x="107.5" y="44" width="6" height="10" rx="2" fill="#2f415f" stroke="{c}" stroke-width="0.9"/>'
        )
    scan = ""
    if idx >= 3:
        scan = (
            f'<rect x="75" y="46.5" width="30" height="1.8" rx="0.9" fill="{c}" opacity="0.9">'
            '<animate attributeName="y" values="46.5;50;46.5" dur="1.8s" repeatCount="indefinite"/>'
            "</rect>"
        )
    crown = ""
    if idx >= 4:
        crown = (
            f'<path d="M72 35 L80 28 L88 35 L96 28 L104 35 L108 42 L72 42 Z" '
            f'fill="#283a57" stroke="{c}" stroke-width="1"/>'
            f'<circle cx="90" cy="34" r="2.5" fill="{c}" opacity="0.95"/>'
        )
    halo = ""
    if idx == 5:
        halo = (
            f'<ellipse cx="90" cy="43" rx="29" ry="11" fill="none" stroke="{c}" stroke-width="1.2" opacity="0.58"/>'
            '<ellipse cx="90" cy="43" rx="23" ry="8.5" fill="none" stroke="#b7f5ff" stroke-width="0.9" opacity="0.55"/>'
        )
    body = f"""
  <g id="helmet_{rarity}">
    <path d="M66 38 Q90 14 114 38 L114 52 L66 52 Z" fill="#30435f" stroke="#1a2740" stroke-width="1.5"/>
    <rect x="63" y="51" width="54" height="5" rx="2.5" fill="#3c5273" stroke="#1a2740" stroke-width="1"/>
    <rect x="86.5" y="23" width="7" height="21" rx="2" fill="#415a81" opacity="0.8"/>
    <rect x="74" y="46" width="32" height="6.4" rx="2.2" fill="#101927" stroke="#273851" stroke-width="0.8"/>
    <circle cx="90" cy="49.2" r="1.8" fill="{c}" opacity="0.95"/>
    {visor}
    {side}
    {scan}
    {crown}
    {halo}
  </g>
"""
    return wrap(body)


def chestplate_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    ribs = ""
    if idx >= 1:
        ribs = (
            '<path d="M72 86 L72 126 M108 86 L108 126" stroke="#4f668a" stroke-width="1" opacity="0.7"/>'
        )
    segments = ""
    if idx >= 2:
        segments = (
            f'<path d="M74 93 L106 93 M74 104 L106 104 M74 115 L106 115" stroke="{c}" stroke-width="0.95" opacity="0.6"/>'
        )
    core = ""
    if idx >= 3:
        core = (
            f'<circle cx="90" cy="103" r="8" fill="#1b2b45" stroke="{c}" stroke-width="1.3"/>'
            f'<circle cx="90" cy="103" r="2.4" fill="{c}">'
            '<animate attributeName="r" values="2;3.4;2" dur="2.1s" repeatCount="indefinite"/>'
            "</circle>"
        )
    frame = ""
    if idx >= 4:
        frame = (
            f'<path d="M67 82 L76 76 L104 76 L113 82 L109 136 L71 136 Z" fill="none" stroke="{c}" stroke-width="1.1" opacity="0.9"/>'
            f'<rect x="83.8" y="95" width="12.4" height="16" rx="2.5" fill="#16263d" stroke="{c}" stroke-width="1"/>'
        )
    halo = ""
    if idx == 5:
        halo = (
            f'<ellipse cx="90" cy="104" rx="22" ry="10" fill="none" stroke="{c}" stroke-width="1.1" opacity="0.56"/>'
            '<ellipse cx="90" cy="104" rx="16" ry="7" fill="none" stroke="#b5f4ff" stroke-width="0.85" opacity="0.55"/>'
        )
    body = f"""
  <g id="chestplate_{rarity}">
    <path d="M66 80 L114 80 L111 136 L69 136 Z" fill="#334966" stroke="#1d2d48" stroke-width="1.25"/>
    <path d="M72 86 L108 86 L105.5 129 L74.5 129 Z" fill="#445d81" opacity="0.92"/>
    <path d="M71 89 Q90 100 109 89" stroke="#617ba4" stroke-width="0.95" opacity="0.75" fill="none"/>
    <path d="M90 86 L90 131" stroke="#243754" stroke-width="1.05" opacity="0.74"/>
    <path d="M75 128 Q90 133 105 128" stroke="{c}" stroke-width="1.25" opacity="0.78" fill="none"/>
    {ribs}
    {segments}
    {core}
    {frame}
    {halo}
  </g>
"""
    return wrap(body)


def gauntlets_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    extra = ""
    if idx >= 1:
        extra += (
            '<rect x="39.5" y="140.5" width="21" height="3.2" rx="1.6" fill="#4d6588" opacity="0.8"/>'
            '<rect x="119.5" y="140.5" width="21" height="3.2" rx="1.6" fill="#4d6588" opacity="0.8"/>'
        )
    if idx >= 2:
        extra += (
            f'<circle cx="50" cy="146" r="1.5" fill="{c}"/>'
            f'<circle cx="130" cy="146" r="1.5" fill="{c}"/>'
        )
    if idx >= 3:
        extra += (
            f'<circle cx="50" cy="146" r="5.4" fill="{c}" opacity="0.2">'
            '<animate attributeName="opacity" values="0.08;0.25;0.08" dur="2s" repeatCount="indefinite"/>'
            "</circle>"
            f'<circle cx="130" cy="146" r="5.4" fill="{c}" opacity="0.2">'
            '<animate attributeName="opacity" values="0.08;0.25;0.08" dur="2s" begin="0.35s" repeatCount="indefinite"/>'
            "</circle>"
        )
    if idx >= 4:
        extra += (
            f'<path d="M38 142 L35 137 L40 137 Z" fill="{c}"/>'
            f'<path d="M142 142 L145 137 L140 137 Z" fill="{c}"/>'
        )
    if idx == 5:
        extra += (
            f'<ellipse cx="50" cy="146" rx="8.5" ry="3.2" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.6"/>'
            f'<ellipse cx="130" cy="146" rx="8.5" ry="3.2" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.6"/>'
        )
    body = f"""
  <g id="gauntlets_{rarity}">
    <path d="M37 134 L63 134 L62 156 L38 156 Z" fill="#344a67" stroke="#1c2d49" stroke-width="1.2"/>
    <path d="M117 134 L143 134 L142 156 L118 156 Z" fill="#344a67" stroke="#1c2d49" stroke-width="1.2"/>
    <path d="M40 145 L60 145" stroke="{c}" stroke-width="1.5" opacity="0.95"/>
    <path d="M120 145 L140 145" stroke="{c}" stroke-width="1.5" opacity="0.95"/>
    <rect x="43" y="151" width="14" height="2.8" rx="1.2" fill="#d0b388" opacity="0.92"/>
    <rect x="123" y="151" width="14" height="2.8" rx="1.2" fill="#d0b388" opacity="0.92"/>
    {extra}
  </g>
"""
    return wrap(body)


def boots_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    extras = ""
    if idx >= 1:
        extras += (
            '<rect x="50" y="195" width="20" height="2" rx="1" fill="#4f6688" opacity="0.85"/>'
            '<rect x="110" y="195" width="20" height="2" rx="1" fill="#4f6688" opacity="0.85"/>'
        )
    if idx >= 2:
        extras += f'<path d="M48 190 L44 192 L48 196 Z" fill="{c}" opacity="0.85"/><path d="M132 190 L136 192 L132 196 Z" fill="{c}" opacity="0.85"/>'
    if idx >= 3:
        extras += (
            f'<rect x="46" y="203" width="28" height="2.4" rx="1.2" fill="{c}" opacity="0.95">'
            '<animate attributeName="opacity" values="0.45;1;0.45" dur="1.9s" repeatCount="indefinite"/>'
            "</rect>"
            f'<rect x="106" y="203" width="28" height="2.4" rx="1.2" fill="{c}" opacity="0.95">'
            '<animate attributeName="opacity" values="0.45;1;0.45" dur="1.9s" begin="0.3s" repeatCount="indefinite"/>'
            "</rect>"
        )
    if idx >= 4:
        extras += f'<rect x="54" y="191" width="7" height="3" rx="1" fill="{c}"/><rect x="119" y="191" width="7" height="3" rx="1" fill="{c}"/>'
    if idx == 5:
        extras += f'<ellipse cx="60" cy="207" rx="12" ry="3.4" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.58"/><ellipse cx="120" cy="207" rx="12" ry="3.4" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.58"/>'
    body = f"""
  <g id="boots_{rarity}">
    <path d="M44 188 L74 188 L76 203 L42 203 Z" fill="#364d6a" stroke="#1a2b45" stroke-width="1.2"/>
    <path d="M104 188 L134 188 L136 203 L102 203 Z" fill="#364d6a" stroke="#1a2b45" stroke-width="1.2"/>
    <path d="M42 202 L77 202 L79 210 L40 210 Z" fill="#212c3c" stroke="#101722" stroke-width="1"/>
    <path d="M102 202 L137 202 L139 210 L100 210 Z" fill="#212c3c" stroke="#101722" stroke-width="1"/>
    <path d="M45 193 L74 193" stroke="{c}" stroke-width="1.4" opacity="0.95"/>
    <path d="M105 193 L134 193" stroke="{c}" stroke-width="1.4" opacity="0.95"/>
    {extras}
  </g>
"""
    return wrap(body)


def shield_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    x = 26
    y = 90
    w = 36 + idx
    h = 56 + idx * 2
    panel = f"M{x+2} {y+4} L{x+w-3} {y} L{x+w} {y+h*0.44:.1f} L{x+w-5} {y+h} L{x+4} {y+h-2} L{x} {y+h*0.6:.1f} Z"
    details = ""
    if idx >= 1:
        details += f'<path d="M{x+7} {y+16} L{x+w-9} {y+16} M{x+7} {y+26} L{x+w-9} {y+26}" stroke="#5e769d" stroke-width="1.05" opacity="0.8"/>'
    if idx >= 2:
        details += f'<path d="M{x+8} {y+9} L{x+w-8} {y+9} L{x+w-8} {y+h-10} L{x+8} {y+h-10} Z" fill="none" stroke="{c}" stroke-width="0.85" opacity="0.7"/>'
    if idx >= 3:
        details += (
            f'<rect x="{x+8}" y="{y+14}" width="{w-16}" height="2" fill="{c}" opacity="0.95">'
            f'<animate attributeName="y" values="{y+14};{y+h-15};{y+14}" dur="2.3s" repeatCount="indefinite"/>'
            "</rect>"
        )
    if idx >= 4:
        cx = x + w / 2
        cy = y + h * 0.56
        details += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.4" fill="#192d47" stroke="{c}" stroke-width="1.2"/><path d="M{cx-3:.1f} {cy:.1f} L{cx+3:.1f} {cy:.1f} M{cx:.1f} {cy-3:.1f} L{cx:.1f} {cy+3:.1f}" stroke="{c}" stroke-width="1.1"/>'
    if idx == 5:
        cx = x + w / 2
        cy = y + h * 0.53
        details += f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{w/2+9:.1f}" ry="{h/2+5:.1f}" fill="none" stroke="{c}" stroke-width="1.1" opacity="0.52"/>'
    body = f"""
  <g id="shield_{rarity}">
    <path d="{panel}" fill="#365071" stroke="#16253c" stroke-width="1.3"/>
    <path d="{panel}" fill="none" stroke="{c}" stroke-width="1" opacity="0.95"/>
    <path d="M{x+5} {y+13} L{x+w-6} {y+12}" stroke="#a3bbdf" stroke-width="0.9" opacity="0.6"/>
    {details}
  </g>
"""
    return wrap(body)


def weapon_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    head = '<path d="M124 102 Q141 92 152 106 Q138 111 126 124 Z" fill="#c5d8ec" stroke="#304968" stroke-width="1.1"/>'
    if idx == 0:
        head = '<path d="M124 104 Q136 98 144 110 Q136 113 126 122 Z" fill="#4a6688" stroke="#213550" stroke-width="1"/>'
    energy = ""
    if idx >= 2:
        energy += f'<path d="M125 106 Q140 96 151 106" stroke="{c}" stroke-width="1.5" fill="none" opacity="0.95"/>'
    if idx >= 3:
        energy += f'<path d="M126 118 Q140 112 149 105" stroke="{c}" stroke-width="0.95" fill="none" opacity="0.85"><animate attributeName="opacity" values="0.55;1;0.55" dur="1.5s" repeatCount="indefinite"/></path>'
    guard = ""
    if idx >= 4:
        guard += f'<path d="M114 126 L122 121 L127 129 L119 134 Z" fill="#27405e" stroke="{c}" stroke-width="1"/><circle cx="119" cy="127.5" r="1.5" fill="{c}"/>'
    halo = ""
    if idx == 5:
        halo += f'<ellipse cx="142" cy="103" rx="11" ry="4.5" fill="none" stroke="{c}" stroke-width="1" opacity="0.62"/>'
    body = f"""
  <g id="weapon_{rarity}" transform="rotate(-24 121 131)">
    <rect x="115" y="126" width="10.5" height="36" rx="3" fill="#18253a" stroke="#0d1522" stroke-width="1"/>
    <rect x="116.8" y="134" width="7" height="2.5" rx="1" fill="{c}" opacity="0.96"/>
    <rect x="116.8" y="145" width="7" height="2.4" rx="1" fill="{c}" opacity="0.78"/>
    <rect x="118.8" y="160" width="3.2" height="5" rx="1.4" fill="#233a59"/>
    <path d="M114.8 126 L125.8 126 L127.2 122 L113.6 122 Z" fill="#314b6d" stroke="#1b2d47" stroke-width="1"/>
    {head}
    {energy}
    {guard}
    {halo}
  </g>
"""
    return wrap(body)


def cloak_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    tail = ""
    if idx >= 2:
        tail = '<path d="M70 160 L62 190 L74 190 Z" fill="#1f314d" opacity="0.65"/><path d="M110 160 L118 190 L106 190 Z" fill="#1f314d" opacity="0.65"/>'
    vent = ""
    if idx >= 1:
        vent = '<path d="M74 96 L69 181 M106 96 L111 181" stroke="#94aed6" stroke-width="0.82" opacity="0.42"/>'
    sparks = ""
    if idx >= 3:
        sparks = f'<circle cx="76" cy="118" r="1.2" fill="{c}" opacity="0.75"/><circle cx="104" cy="125" r="1" fill="{c}" opacity="0.75"/><circle cx="96" cy="146" r="1.2" fill="{c}" opacity="0.7"/><circle cx="83" cy="139" r="0.9" fill="{c}" opacity="0.7"/>'
    bands = ""
    if idx >= 4:
        bands = f'<path d="M69 112 Q90 96 111 112" stroke="{c}" stroke-width="1.45" fill="none" opacity="0.8"/><path d="M68 151 Q90 137 112 151" stroke="{c}" stroke-width="1.15" fill="none" opacity="0.62"/>'
    aura = ""
    if idx == 5:
        aura = f'<ellipse cx="90" cy="136" rx="34" ry="19" fill="none" stroke="{c}" stroke-width="1.1" opacity="0.5"/>'
    body = f"""
  <g id="cloak_{rarity}" opacity="0.9">
    <path d="M63 74 L117 74 L124 91 L118 191 L62 191 L56 91 Z" fill="#1b2b44" opacity="0.52"/>
    <path d="M68 82 L112 82 L116 97 L112 186 L68 186 L64 97 Z" fill="#2f466d" opacity="0.45"/>
    <path d="M68 82 Q90 90 112 82" stroke="{c}" stroke-width="1.05" opacity="0.82" fill="none"/>
    {vent}
    {tail}
    {sparks}
    {bands}
    {aura}
  </g>
"""
    return wrap(body)


def amulet_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    ring = ""
    if idx >= 1:
        ring += f'<circle cx="90" cy="100" r="7" fill="none" stroke="{c}" stroke-width="1.2" opacity="0.86"/>'
    chip = ""
    if idx >= 2:
        chip += f'<path d="M90 93 L94 100 L90 107 L86 100 Z" fill="{c}" opacity="0.9"/>'
    orbit = ""
    if idx >= 3:
        orbit += f'<circle cx="90" cy="100" r="10.6" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.45"><animateTransform attributeName="transform" type="rotate" values="0 90 100;360 90 100" dur="8s" repeatCount="indefinite"/></circle>'
    core = ""
    if idx >= 4:
        core += f'<path d="M82 100 L76 97 L78 104 Z" fill="{c}" opacity="0.9"/><path d="M98 100 L104 97 L102 104 Z" fill="{c}" opacity="0.9"/>'
    halo = ""
    if idx == 5:
        halo += f'<ellipse cx="90" cy="100" rx="14.5" ry="5.4" fill="none" stroke="#b6f8ff" stroke-width="0.9" opacity="0.6"/>'
    pulse = ""
    if idx >= 3:
        pulse += f'<circle cx="90" cy="100" r="3.2" fill="{c}" opacity="0.24"><animate attributeName="r" values="2.2;4.8;2.2" dur="2s" repeatCount="indefinite"/></circle>'
    body = f"""
  <g id="amulet_{rarity}">
    <path d="M86 90 Q90 86 94 90" stroke="#8394ac" stroke-width="1.1" fill="none"/>
    <rect x="85" y="94" width="10" height="12" rx="2" fill="#223550" stroke="#101b2b" stroke-width="1"/>
    <circle cx="90" cy="100" r="2.1" fill="{c}" opacity="0.96"/>
    {ring}
    {chip}
    {orbit}
    {core}
    {halo}
    {pulse}
  </g>
"""
    return wrap(body)


def fx_epic() -> str:
    return wrap(
        """
  <g id="fx_epic">
    <ellipse cx="90" cy="102" rx="24" ry="12" fill="#9C27B0" opacity="0.12"/>
    <circle cx="90" cy="100" r="19" fill="none" stroke="#9C27B0" stroke-width="1.8" opacity="0.68"/>
    <path d="M67 100 L113 100" stroke="#9C27B0" stroke-width="1.2" opacity="0.7"/>
    <path d="M90 81 L90 119" stroke="#cf83ef" stroke-width="1" opacity="0.75"/>
    <circle cx="63" cy="92" r="1.4" fill="#cf83ef"/>
    <circle cx="117" cy="109" r="1.2" fill="#cf83ef"/>
  </g>
"""
    )


def fx_legendary() -> str:
    return wrap(
        """
  <g id="fx_legendary">
    <ellipse cx="90" cy="100" rx="28" ry="14" fill="#FF9800" opacity="0.12"/>
    <ellipse cx="90" cy="100" rx="34" ry="17" fill="none" stroke="#FF9800" stroke-width="1.6" opacity="0.76"/>
    <ellipse cx="90" cy="100" rx="22" ry="11" fill="none" stroke="#ffd59f" stroke-width="1.1" opacity="0.66"/>
    <path d="M58 101 Q90 76 122 101" stroke="#FF9800" stroke-width="1.5" fill="none" opacity="0.76"/>
    <circle cx="90" cy="83" r="2.1" fill="#FF9800" opacity="0.9"/>
    <circle cx="71" cy="90" r="1.3" fill="#ffc36f"/>
    <circle cx="109" cy="89" r="1.3" fill="#ffc36f"/>
  </g>
"""
    )


def fx_celestial() -> str:
    return wrap(
        """
  <g id="fx_celestial">
    <rect x="60" y="0" width="60" height="220" fill="#00E5FF" opacity="0.05"/>
    <ellipse cx="90" cy="100" rx="30" ry="14" fill="#00E5FF" opacity="0.11"/>
    <ellipse cx="90" cy="100" rx="38" ry="18" fill="none" stroke="#00E5FF" stroke-width="1.2" opacity="0.72"/>
    <ellipse cx="90" cy="100" rx="32" ry="15" fill="none" stroke="#9ff7ff" stroke-width="0.9" opacity="0.58"/>
    <path d="M90 68 L90 132" stroke="#bdf9ff" stroke-width="1.1" opacity="0.55"/>
    <path d="M58 100 L122 100" stroke="#bdf9ff" stroke-width="1.1" opacity="0.55"/>
    <circle cx="60" cy="88" r="1.4" fill="#9bf6ff"/>
    <circle cx="120" cy="92" r="1.3" fill="#9bf6ff"/>
    <circle cx="104" cy="116" r="1.2" fill="#9bf6ff"/>
    <circle cx="76" cy="116" r="1.2" fill="#9bf6ff"/>
  </g>
"""
    )


def main() -> None:
    for idx, rarity in enumerate(RARITIES):
        write(ROOT / "gear" / "helmet" / f"helmet_{rarity}.svg", helmet_svg(rarity, idx))
        write(ROOT / "gear" / "chestplate" / f"chestplate_{rarity}.svg", chestplate_svg(rarity, idx))
        write(ROOT / "gear" / "gauntlets" / f"gauntlets_{rarity}.svg", gauntlets_svg(rarity, idx))
        write(ROOT / "gear" / "boots" / f"boots_{rarity}.svg", boots_svg(rarity, idx))
        write(ROOT / "gear" / "shield" / f"shield_{rarity}.svg", shield_svg(rarity, idx))
        write(ROOT / "gear" / "weapon" / f"weapon_{rarity}.svg", weapon_svg(rarity, idx))
        write(ROOT / "gear" / "cloak" / f"cloak_{rarity}.svg", cloak_svg(rarity, idx))
        write(ROOT / "gear" / "amulet" / f"amulet_{rarity}.svg", amulet_svg(rarity, idx))

    write(ROOT / "fx" / "tier_epic.svg", fx_epic())
    write(ROOT / "fx" / "tier_legendary.svg", fx_legendary())
    write(ROOT / "fx" / "tier_celestial.svg", fx_celestial())
    print("robot pack regenerated")


if __name__ == "__main__":
    main()
