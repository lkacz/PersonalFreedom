#!/usr/bin/env python3
"""Regenerate complete space pirate hero gear SVG pack with slot-fit rarity progression."""

from __future__ import annotations

from pathlib import Path


ROOT = Path("icons/heroes/space_pirate")
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
    trim = ""
    if idx >= 1:
        trim = (
            f'<path d="M58 45 Q90 38 122 45" stroke="{c}" stroke-width="1.2" fill="none" opacity="0.9"/>'
            f'<rect x="77" y="34" width="26" height="2.8" rx="1.3" fill="{c}" opacity="0.75"/>'
        )
    feather = ""
    if idx >= 2:
        feather = (
            f'<path d="M104 30 Q113 22 119 31 Q113 35 106 40 Z" fill="#3f2e44" stroke="{c}" stroke-width="0.8"/>'
            f'<path d="M108 33 Q112 30 115 34" stroke="{c}" stroke-width="0.8" fill="none" opacity="0.8"/>'
        )
    skull = ""
    if idx >= 3:
        skull = (
            f'<circle cx="90" cy="36.4" r="2.1" fill="#101521" stroke="{c}" stroke-width="0.8"/>'
            '<circle cx="89.2" cy="36.1" r="0.35" fill="#dbe7ff"/>'
            '<circle cx="90.8" cy="36.1" r="0.35" fill="#dbe7ff"/>'
            '<path d="M89.2 37.5 L90.8 37.5" stroke="#dbe7ff" stroke-width="0.45"/>'
        )
    command_crown = ""
    if idx >= 4:
        command_crown = (
            f'<path d="M72 28 L79 24 L86 28 L93 24 L100 28 L107 24 L114 28 L114 33 L72 33 Z" fill="#24364f" stroke="{c}" stroke-width="0.95"/>'
            f'<circle cx="93" cy="28.4" r="1.6" fill="{c}" opacity="0.95"/>'
        )
    celestial_ring = ""
    if idx == 5:
        celestial_ring = (
            f'<ellipse cx="90" cy="43" rx="31" ry="10.5" fill="none" stroke="{c}" stroke-width="1.1" opacity="0.58"/>'
            '<ellipse cx="90" cy="43" rx="25" ry="8" fill="none" stroke="#b7f7ff" stroke-width="0.9" opacity="0.55"/>'
        )
    body = f"""
  <g id="helmet_{rarity}">
    <path d="M58 44 Q90 34 122 44 L118 53 Q90 50 62 53 Z" fill="#17253a" stroke="#0e1624" stroke-width="1.2"/>
    <path d="M72 34 Q90 23 108 34 L108 45 L72 45 Z" fill="#2c3f5f" stroke="#152438" stroke-width="1"/>
    <rect x="75" y="44.4" width="30" height="7.4" rx="3.4" fill="#101826" stroke="#273854" stroke-width="0.9"/>
    <circle cx="84.5" cy="48" r="2" fill="#d7e3f5"/>
    <circle cx="95.5" cy="48" r="2" fill="#d7e3f5"/>
    <circle cx="84.5" cy="48" r="0.8" fill="#2a364a"/>
    <circle cx="95.5" cy="48" r="0.8" fill="#2a364a"/>
    <path d="M87.2 48 L92.8 48" stroke="#9cb6d9" stroke-width="0.8"/>
    {trim}
    {feather}
    {skull}
    {command_crown}
    {celestial_ring}
  </g>
"""
    return wrap(body)


def chestplate_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    lapels = (
        '<path d="M72 80 L86 88 L80 133 L72 131 Z" fill="#23334d" opacity="0.8"/>'
        '<path d="M108 80 L94 88 L100 133 L108 131 Z" fill="#23334d" opacity="0.8"/>'
    )
    seams = ""
    if idx >= 1:
        seams += (
            '<path d="M74 92 L106 92 M74 103 L106 103 M74 114 L106 114" stroke="#546e95" stroke-width="0.9" opacity="0.72"/>'
        )
    if idx >= 2:
        seams += (
            f'<path d="M70 81 L80 76 L100 76 L110 81" stroke="{c}" stroke-width="1" fill="none" opacity="0.8"/>'
            f'<rect x="86" y="95" width="8" height="20" rx="2" fill="#17263d" stroke="{c}" stroke-width="0.9"/>'
        )
    if idx >= 3:
        seams += (
            f'<circle cx="90" cy="105" r="5.2" fill="#1a2a42" stroke="{c}" stroke-width="1.1"/>'
            f'<path d="M90 100 L92.8 105 L90 110 L87.2 105 Z" fill="{c}" opacity="0.95"/>'
        )
    if idx >= 4:
        seams += (
            f'<path d="M67 83 Q90 66 113 83" stroke="{c}" stroke-width="1.35" fill="none" opacity="0.88"/>'
            f'<path d="M69 132 Q90 141 111 132" stroke="{c}" stroke-width="1.2" fill="none" opacity="0.78"/>'
        )
    if idx == 5:
        seams += (
            f'<ellipse cx="90" cy="104" rx="18" ry="8" fill="none" stroke="{c}" stroke-width="1" opacity="0.55"/>'
            '<ellipse cx="90" cy="104" rx="12.5" ry="5.6" fill="none" stroke="#b5f6ff" stroke-width="0.85" opacity="0.58"/>'
        )
    body = f"""
  <g id="chestplate_{rarity}">
    <path d="M70 79 L110 79 Q115 86 115 97 L112 145 L68 145 L65 97 Q65 86 70 79 Z" fill="#283d60" stroke="#15243a" stroke-width="1.25"/>
    <path d="M74 85 L106 85 L104 137 L76 137 Z" fill="#36507c" opacity="0.9"/>
    {lapels}
    <path d="M90 84 L90 139" stroke="#17263f" stroke-width="1" opacity="0.74"/>
    <path d="M76 136 Q90 141 104 136" stroke="{c}" stroke-width="1.25" opacity="0.78" fill="none"/>
    {seams}
  </g>
"""
    return wrap(body)


def gauntlets_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += (
            '<path d="M40 143 L60 143 M120 143 L140 143" stroke="#4e678f" stroke-width="1" opacity="0.8"/>'
        )
    if idx >= 2:
        details += (
            f'<circle cx="49.5" cy="147" r="1.5" fill="{c}"/><circle cx="130.5" cy="147" r="1.5" fill="{c}"/>'
            f'<path d="M44 151 L56 151 M124 151 L136 151" stroke="{c}" stroke-width="1.1" opacity="0.9"/>'
        )
    if idx >= 3:
        details += (
            f'<path d="M40 138 Q49 132 58 138" stroke="{c}" stroke-width="1.05" fill="none" opacity="0.8"/>'
            f'<path d="M122 138 Q131 132 140 138" stroke="{c}" stroke-width="1.05" fill="none" opacity="0.8"/>'
        )
    if idx >= 4:
        details += (
            f'<rect x="38" y="145.5" width="24" height="1.8" rx="0.9" fill="{c}" opacity="0.85"/>'
            f'<rect x="118" y="145.5" width="24" height="1.8" rx="0.9" fill="{c}" opacity="0.85"/>'
        )
    if idx == 5:
        details += (
            f'<ellipse cx="50" cy="146" rx="8.5" ry="3.1" fill="none" stroke="{c}" stroke-width="0.85" opacity="0.58"/>'
            f'<ellipse cx="130" cy="146" rx="8.5" ry="3.1" fill="none" stroke="{c}" stroke-width="0.85" opacity="0.58"/>'
        )
    body = f"""
  <g id="gauntlets_{rarity}">
    <path d="M38 133 L62 133 L61 156 L39 156 Z" fill="#324968" stroke="#1a2b45" stroke-width="1.15"/>
    <path d="M118 133 L142 133 L141 156 L119 156 Z" fill="#324968" stroke="#1a2b45" stroke-width="1.15"/>
    <path d="M44 134 L56 134 L56 128 Q50 126 44 128 Z" fill="#253957" stroke="#15243a" stroke-width="0.9"/>
    <path d="M124 134 L136 134 L136 128 Q130 126 124 128 Z" fill="#253957" stroke="#15243a" stroke-width="0.9"/>
    <rect x="42.5" y="150.4" width="15" height="2.8" rx="1.2" fill="#d0b388" opacity="0.92"/>
    <rect x="122.5" y="150.4" width="15" height="2.8" rx="1.2" fill="#d0b388" opacity="0.92"/>
    {details}
  </g>
"""
    return wrap(body)


def boots_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += (
            '<path d="M45 194 L73 194 M106 194 L134 194" stroke="#5f789e" stroke-width="1" opacity="0.85"/>'
        )
    if idx >= 2:
        details += (
            f'<path d="M48 190 L44 192 L48 196 Z" fill="{c}" opacity="0.85"/>'
            f'<path d="M132 190 L136 192 L132 196 Z" fill="{c}" opacity="0.85"/>'
        )
    if idx >= 3:
        details += (
            f'<rect x="46.5" y="203.2" width="27" height="2.1" rx="1" fill="{c}" opacity="0.88"/>'
            f'<rect x="106.5" y="203.2" width="27" height="2.1" rx="1" fill="{c}" opacity="0.88"/>'
        )
    if idx >= 4:
        details += (
            f'<circle cx="60" cy="191.6" r="1.3" fill="{c}"/><circle cx="120" cy="191.6" r="1.3" fill="{c}"/>'
            f'<path d="M52 188 Q60 182 68 188" stroke="{c}" stroke-width="0.95" fill="none" opacity="0.9"/>'
            f'<path d="M112 188 Q120 182 128 188" stroke="{c}" stroke-width="0.95" fill="none" opacity="0.9"/>'
        )
    if idx == 5:
        details += (
            f'<ellipse cx="60" cy="207" rx="12" ry="3.4" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.55"/>'
            f'<ellipse cx="120" cy="207" rx="12" ry="3.4" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.55"/>'
        )
    body = f"""
  <g id="boots_{rarity}">
    <path d="M44 188 L74 188 L76 202 L42 202 Z" fill="#324b6f" stroke="#1b2d48" stroke-width="1.2"/>
    <path d="M104 188 L134 188 L136 202 L102 202 Z" fill="#324b6f" stroke="#1b2d48" stroke-width="1.2"/>
    <path d="M42 201 L77 201 L79 209 L40 209 Z" fill="#1f2a3a" stroke="#101722" stroke-width="1"/>
    <path d="M102 201 L137 201 L139 209 L100 209 Z" fill="#1f2a3a" stroke="#101722" stroke-width="1"/>
    <path d="M46 192 L74 192" stroke="{c}" stroke-width="1.3" opacity="0.92"/>
    <path d="M106 192 L134 192" stroke="{c}" stroke-width="1.3" opacity="0.92"/>
    {details}
  </g>
"""
    return wrap(body)


def shield_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    panel = "M33 103 L61 98 L65 122 L59 149 L36 147 L33 129 Z"
    details = ""
    if idx >= 1:
        details += (
            '<path d="M38 111 L59 111 M38 120 L59 120 M38 129 L59 129" stroke="#58739b" stroke-width="0.92" opacity="0.72"/>'
        )
    if idx >= 2:
        details += (
            f'<path d="M40 105 L58 102 L61 118 L57 143 L40 141 L38 125 Z" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.8"/>'
        )
    if idx >= 3:
        details += (
            f'<rect x="42" y="115" width="14" height="2.1" rx="1" fill="{c}" opacity="0.85">'
            '<animate attributeName="y" values="115;138;115" dur="2.1s" repeatCount="indefinite"/>'
            "</rect>"
        )
    if idx >= 4:
        details += (
            f'<path d="M47 126 L51 131 L56 122" stroke="{c}" stroke-width="1.1" fill="none"/>'
            f'<circle cx="49.5" cy="111.5" r="2.3" fill="#17243a" stroke="{c}" stroke-width="0.95"/>'
        )
    if idx == 5:
        details += (
            f'<ellipse cx="49" cy="126" rx="17" ry="8.2" fill="none" stroke="{c}" stroke-width="1" opacity="0.56"/>'
            '<ellipse cx="49" cy="126" rx="11.5" ry="5.6" fill="none" stroke="#bcf7ff" stroke-width="0.85" opacity="0.58"/>'
        )
    body = f"""
  <g id="shield_{rarity}">
    <path d="{panel}" fill="#2e476f" stroke="#13233a" stroke-width="1.2"/>
    <path d="{panel}" fill="none" stroke="{c}" stroke-width="1" opacity="0.95"/>
    <path d="M37 106 L60 105" stroke="#a6c0e4" stroke-width="0.85" opacity="0.62"/>
    {details}
  </g>
"""
    return wrap(body)


def weapon_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    blade = '<path d="M125 102 Q139 98 145 112 Q136 116 126 123 Z" fill="#5d7397" stroke="#263a56" stroke-width="1"/>'
    if idx >= 2:
        blade = '<path d="M124 100 Q142 92 152 106 Q138 111 126 124 Z" fill="#cddcf0" stroke="#304968" stroke-width="1.05"/>'
    glow = ""
    if idx >= 3:
        glow += f'<path d="M125 106 Q140 96 151 106" stroke="{c}" stroke-width="1.4" fill="none" opacity="0.92"/>'
    if idx >= 4:
        glow += (
            f'<path d="M126 118 Q140 112 149 105" stroke="{c}" stroke-width="0.95" fill="none" opacity="0.82">'
            '<animate attributeName="opacity" values="0.45;1;0.45" dur="1.4s" repeatCount="indefinite"/>'
            "</path>"
        )
    hook = ""
    if idx >= 1:
        hook += f'<path d="M145 111 Q152 114 151 122 Q148 129 140 127" stroke="{c}" stroke-width="1" fill="none" opacity="0.8"/>'
    if idx == 5:
        hook += f'<ellipse cx="142" cy="103" rx="10.8" ry="4.5" fill="none" stroke="{c}" stroke-width="0.95" opacity="0.58"/>'
    body = f"""
  <g id="weapon_{rarity}" transform="rotate(-26 122 130)">
    <rect x="115.5" y="126" width="10" height="35" rx="3" fill="#172337" stroke="#0d1522" stroke-width="1"/>
    <rect x="117.1" y="133" width="6.8" height="2.4" rx="1" fill="{c}" opacity="0.96"/>
    <rect x="117.1" y="143" width="6.8" height="2.4" rx="1" fill="{c}" opacity="0.78"/>
    <rect x="118.8" y="158" width="3.4" height="5.2" rx="1.5" fill="#233a59"/>
    <path d="M115.4 126 L125.6 126 L127 122 L114 122 Z" fill="#2e4667" stroke="#1b2c45" stroke-width="1"/>
    {blade}
    {hook}
    {glow}
  </g>
"""
    return wrap(body)


def cloak_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    tails = (
        '<path d="M68 150 L60 192 L73 191 Z" fill="#1b2b44" opacity="0.72"/>'
        '<path d="M109 150 L121 189 L106 190 Z" fill="#1b2b44" opacity="0.72"/>'
    )
    details = ""
    if idx >= 1:
        details += '<path d="M72 95 L66 183 M108 95 L114 183" stroke="#9bb6dd" stroke-width="0.82" opacity="0.45"/>'
    if idx >= 2:
        details += f'<path d="M68 84 Q90 96 112 84" stroke="{c}" stroke-width="1.05" fill="none" opacity="0.82"/>'
    if idx >= 3:
        details += (
            f'<circle cx="76" cy="118" r="1.1" fill="{c}" opacity="0.72"/><circle cx="104" cy="125" r="1" fill="{c}" opacity="0.72"/>'
            f'<circle cx="95" cy="145" r="1.1" fill="{c}" opacity="0.68"/><circle cx="84" cy="138" r="0.9" fill="{c}" opacity="0.68"/>'
        )
    if idx >= 4:
        details += (
            f'<path d="M67 110 Q90 95 113 110" stroke="{c}" stroke-width="1.4" fill="none" opacity="0.8"/>'
            f'<path d="M66 152 Q90 136 114 152" stroke="{c}" stroke-width="1.15" fill="none" opacity="0.62"/>'
        )
    if idx == 5:
        details += f'<ellipse cx="90" cy="135" rx="33" ry="18" fill="none" stroke="{c}" stroke-width="1.05" opacity="0.5"/>'
    body = f"""
  <g id="cloak_{rarity}" opacity="0.9">
    <path d="M63 74 L117 74 L124 92 L117 191 L63 191 L56 92 Z" fill="#1a2941" opacity="0.52"/>
    <path d="M68 82 L112 82 L116 97 L112 186 L68 186 L64 97 Z" fill="#2d4267" opacity="0.45"/>
    {tails}
    {details}
  </g>
"""
    return wrap(body)


def amulet_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += f'<circle cx="90" cy="100" r="6.8" fill="none" stroke="{c}" stroke-width="1.15" opacity="0.85"/>'
    if idx >= 2:
        details += (
            f'<path d="M90 95.2 L92.4 99.4 L90 103.5 L87.6 99.4 Z" fill="{c}" opacity="0.92"/>'
            f'<path d="M84.5 100 L95.5 100" stroke="{c}" stroke-width="0.95" opacity="0.82"/>'
        )
    if idx >= 3:
        details += (
            f'<circle cx="90" cy="100" r="10.4" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.45">'
            '<animateTransform attributeName="transform" type="rotate" values="0 90 100;360 90 100" dur="8s" repeatCount="indefinite"/>'
            "</circle>"
        )
    if idx >= 4:
        details += (
            f'<path d="M82 100 L76 97 L78 104 Z" fill="{c}" opacity="0.9"/>'
            f'<path d="M98 100 L104 97 L102 104 Z" fill="{c}" opacity="0.9"/>'
        )
    if idx == 5:
        details += (
            f'<ellipse cx="90" cy="100" rx="14.2" ry="5.2" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.58"/>'
            '<ellipse cx="90" cy="100" rx="10.6" ry="3.8" fill="none" stroke="#bcf8ff" stroke-width="0.8" opacity="0.58"/>'
        )
    pulse = ""
    if idx >= 3:
        pulse = (
            f'<circle cx="90" cy="100" r="2.8" fill="{c}" opacity="0.24">'
            '<animate attributeName="r" values="2.2;4.6;2.2" dur="2s" repeatCount="indefinite"/>'
            "</circle>"
        )
    body = f"""
  <g id="amulet_{rarity}">
    <path d="M86 90 Q90 86 94 90" stroke="#8394ac" stroke-width="1.1" fill="none"/>
    <rect x="85" y="94" width="10" height="12" rx="2" fill="#223550" stroke="#101b2b" stroke-width="1"/>
    <circle cx="90" cy="100" r="2.1" fill="{c}" opacity="0.96"/>
    {details}
    {pulse}
  </g>
"""
    return wrap(body)


def fx_epic() -> str:
    return wrap(
        """
  <g id="fx_epic">
    <ellipse cx="90" cy="102" rx="26" ry="12" fill="#9C27B0" opacity="0.1"/>
    <circle cx="90" cy="101" r="20" fill="none" stroke="#9C27B0" stroke-width="1.7" opacity="0.66"/>
    <path d="M68 100 Q90 89 112 100" stroke="#d48af0" stroke-width="1.1" fill="none" opacity="0.76"/>
    <circle cx="66" cy="95" r="1.2" fill="#ca7ae9"/>
    <circle cx="115" cy="107" r="1.2" fill="#ca7ae9"/>
  </g>
"""
    )


def fx_legendary() -> str:
    return wrap(
        """
  <g id="fx_legendary">
    <ellipse cx="90" cy="100" rx="29" ry="14" fill="#FF9800" opacity="0.11"/>
    <ellipse cx="90" cy="100" rx="35" ry="17.5" fill="none" stroke="#FF9800" stroke-width="1.5" opacity="0.74"/>
    <ellipse cx="90" cy="100" rx="23" ry="11.2" fill="none" stroke="#ffd69f" stroke-width="1.05" opacity="0.66"/>
    <path d="M57 102 Q90 73 123 102" stroke="#FF9800" stroke-width="1.4" fill="none" opacity="0.74"/>
    <path d="M62 113 Q90 90 118 113" stroke="#ffc36f" stroke-width="1" fill="none" opacity="0.62"/>
    <circle cx="90" cy="82" r="2" fill="#FF9800"/>
  </g>
"""
    )


def fx_celestial() -> str:
    return wrap(
        """
  <g id="fx_celestial">
    <rect x="60" y="0" width="60" height="220" fill="#00E5FF" opacity="0.045"/>
    <ellipse cx="90" cy="100" rx="31" ry="14.5" fill="#00E5FF" opacity="0.1"/>
    <ellipse cx="90" cy="100" rx="39" ry="18.5" fill="none" stroke="#00E5FF" stroke-width="1.15" opacity="0.7"/>
    <ellipse cx="90" cy="100" rx="33" ry="15.2" fill="none" stroke="#a6f8ff" stroke-width="0.9" opacity="0.58"/>
    <path d="M90 67 L90 133" stroke="#bdf9ff" stroke-width="1" opacity="0.54"/>
    <path d="M57 100 L123 100" stroke="#bdf9ff" stroke-width="1" opacity="0.54"/>
    <circle cx="60" cy="88" r="1.3" fill="#9bf6ff"/>
    <circle cx="120" cy="92" r="1.2" fill="#9bf6ff"/>
    <circle cx="104" cy="116" r="1.1" fill="#9bf6ff"/>
    <circle cx="76" cy="116" r="1.1" fill="#9bf6ff"/>
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
    print("space_pirate pack regenerated")


if __name__ == "__main__":
    main()

