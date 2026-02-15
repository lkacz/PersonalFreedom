#!/usr/bin/env python3
"""Regenerate complete scholar hero SVG pack with fit-aligned rarity progression."""

from __future__ import annotations

from pathlib import Path


ROOT = Path("icons/heroes/scholar")
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


def helmet_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    tassel = ""
    if idx >= 1:
        tassel = f'<path d="M101 39 L109 47 Q110 50 108 52" stroke="{c}" stroke-width="1.1" fill="none"/><circle cx="108" cy="52" r="1.6" fill="{c}"/>'
    lenses = ""
    if idx >= 2:
        lenses = (
            f'<circle cx="84" cy="48" r="2.5" fill="none" stroke="{c}" stroke-width="0.9"/>'
            f'<circle cx="96" cy="48" r="2.5" fill="none" stroke="{c}" stroke-width="0.9"/>'
        )
    glyph = ""
    if idx >= 3:
        glyph = f'<path d="M90 37.2 L92.2 40.8 L90 44.4 L87.8 40.8 Z" fill="{c}" opacity="0.95"/>'
    crown = ""
    if idx >= 4:
        crown = (
            f'<path d="M72 32 L79 28 L86 32 L93 28 L100 32 L107 28 L114 32 L114 36 L72 36 Z" fill="#273a59" stroke="{c}" stroke-width="0.9"/>'
            f'<path d="M74 33.4 L112 33.4" stroke="{c}" stroke-width="0.9" opacity="0.85"/>'
        )
    halo = ""
    if idx == 5:
        halo = (
            f'<ellipse cx="90" cy="44" rx="29" ry="9.4" fill="none" stroke="{c}" stroke-width="1.05" opacity="0.58"/>'
            '<ellipse cx="90" cy="44" rx="23" ry="7" fill="none" stroke="#b7f7ff" stroke-width="0.85" opacity="0.56"/>'
        )
    body = f"""
  <g id="helmet_{rarity}">
    <path d="M66 40 L114 40 L109 48 L71 48 Z" fill="#1f2f49" stroke="#132138" stroke-width="1.1"/>
    <rect x="75" y="48" width="30" height="3.8" rx="1.7" fill="#314565" stroke="#1a2b45" stroke-width="0.8"/>
    <path d="M79 41 L101 41 L101 47 L79 47 Z" fill="#3f577d" stroke="#1f304a" stroke-width="0.8"/>
    <path d="M79 42 L101 42" stroke="{c}" stroke-width="1" opacity="0.72"/>
    <circle cx="90" cy="45.1" r="1.5" fill="{c}" opacity="0.9"/>
    {tassel}
    {lenses}
    {glyph}
    {crown}
    {halo}
  </g>
"""
    return wrap(body)


def chestplate_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    layers = ""
    if idx >= 1:
        layers += '<path d="M73 88 L107 88 L104.5 135 L75.5 135 Z" fill="#556d95" opacity="0.7"/>'
    if idx >= 2:
        layers += (
            '<path d="M74 96 L106 96 M74 106 L106 106 M74 116 L106 116" stroke="#6e87b0" stroke-width="0.95" opacity="0.72"/>'
            f'<path d="M70 82 L79 76 L101 76 L110 82" stroke="{c}" stroke-width="1" fill="none" opacity="0.85"/>'
        )
    if idx >= 3:
        layers += f'<rect x="84.2" y="94.5" width="11.6" height="17.6" rx="2.4" fill="#1a2b44" stroke="{c}" stroke-width="1"/><path d="M87 103.2 L93 103.2" stroke="{c}" stroke-width="0.95"/>'
    if idx >= 4:
        layers += (
            f'<path d="M68 85 Q90 68 112 85" stroke="{c}" stroke-width="1.35" fill="none" opacity="0.86"/>'
            f'<path d="M69 131 Q90 141 111 131" stroke="{c}" stroke-width="1.18" fill="none" opacity="0.75"/>'
            f'<circle cx="90" cy="102.8" r="4.8" fill="none" stroke="{c}" stroke-width="1.15"/>'
        )
    if idx == 5:
        layers += (
            f'<ellipse cx="90" cy="104" rx="18.2" ry="7.5" fill="none" stroke="{c}" stroke-width="1" opacity="0.55"/>'
            '<ellipse cx="90" cy="104" rx="12.5" ry="5.4" fill="none" stroke="#bcf7ff" stroke-width="0.82" opacity="0.56"/>'
        )
    body = f"""
  <g id="chestplate_{rarity}">
    <path d="M70 79 L110 79 Q115 86 115 97 L112 145 L68 145 L65 97 Q65 86 70 79 Z" fill="#354d71" stroke="#182941" stroke-width="1.2"/>
    <path d="M76 84 L104 84 L105 143 L75 143 Z" fill="#4a638d" opacity="0.88"/>
    <path d="M76 84 L83 94 L80 143 L74 143 Z" fill="#2a3e5f" opacity="0.72"/>
    <path d="M104 84 L97 94 L100 143 L106 143 Z" fill="#2a3e5f" opacity="0.72"/>
    <path d="M90 84 L90 143" stroke="#223654" stroke-width="1.05" opacity="0.72"/>
    <path d="M75 136 Q90 141 105 136" stroke="{c}" stroke-width="1.2" opacity="0.82" fill="none"/>
    {layers}
  </g>
"""
    return wrap(body)


def gauntlets_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += '<path d="M40 143 L60 143 M120 143 L140 143" stroke="#6a84aa" stroke-width="0.9" opacity="0.8"/>'
    if idx >= 2:
        details += (
            f'<path d="M45 150 Q50 145 55 150" stroke="{c}" stroke-width="0.95" fill="none"/>'
            f'<path d="M125 150 Q130 145 135 150" stroke="{c}" stroke-width="0.95" fill="none"/>'
        )
    if idx >= 3:
        details += (
            f'<path d="M42 136 L58 136" stroke="{c}" stroke-width="1.05" opacity="0.85"/>'
            f'<path d="M122 136 L138 136" stroke="{c}" stroke-width="1.05" opacity="0.85"/>'
            f'<circle cx="49.5" cy="147.2" r="1.4" fill="{c}"/><circle cx="130.5" cy="147.2" r="1.4" fill="{c}"/>'
        )
    if idx >= 4:
        details += (
            f'<path d="M39 145.8 L61 145.8" stroke="{c}" stroke-width="1.35" opacity="0.82"/>'
            f'<path d="M119 145.8 L141 145.8" stroke="{c}" stroke-width="1.35" opacity="0.82"/>'
        )
    if idx == 5:
        details += (
            f'<ellipse cx="50" cy="146.5" rx="8.2" ry="3" fill="none" stroke="{c}" stroke-width="0.85" opacity="0.55"/>'
            f'<ellipse cx="130" cy="146.5" rx="8.2" ry="3" fill="none" stroke="{c}" stroke-width="0.85" opacity="0.55"/>'
        )
    body = f"""
  <g id="gauntlets_{rarity}">
    <path d="M38 134 L62 134 L61 156 L39 156 Z" fill="#3a5377" stroke="#1d304d" stroke-width="1.15"/>
    <path d="M118 134 L142 134 L141 156 L119 156 Z" fill="#3a5377" stroke="#1d304d" stroke-width="1.15"/>
    <rect x="42.8" y="150.2" width="14.3" height="2.8" rx="1.2" fill="#e0ccb2" opacity="0.92"/>
    <rect x="122.8" y="150.2" width="14.3" height="2.8" rx="1.2" fill="#e0ccb2" opacity="0.92"/>
    <path d="M44 138 L56 138 M124 138 L136 138" stroke="{c}" stroke-width="1" opacity="0.8"/>
    {details}
  </g>
"""
    return wrap(body)


def boots_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += '<path d="M44 194 L73 194 M106 194 L135 194" stroke="#6b83a8" stroke-width="0.95" opacity="0.8"/>'
    if idx >= 2:
        details += f'<rect x="53" y="189.8" width="6" height="2.4" rx="1" fill="{c}" opacity="0.85"/><rect x="120" y="189.8" width="6" height="2.4" rx="1" fill="{c}" opacity="0.85"/>'
    if idx >= 3:
        details += (
            f'<path d="M45 202.6 L74 202.6" stroke="{c}" stroke-width="1.15" opacity="0.85"/>'
            f'<path d="M106 202.6 L135 202.6" stroke="{c}" stroke-width="1.15" opacity="0.85"/>'
        )
    if idx >= 4:
        details += (
            f'<path d="M48 188 Q60 181 72 188" stroke="{c}" stroke-width="1" fill="none" opacity="0.85"/>'
            f'<path d="M108 188 Q120 181 132 188" stroke="{c}" stroke-width="1" fill="none" opacity="0.85"/>'
        )
    if idx == 5:
        details += (
            f'<ellipse cx="60" cy="207" rx="12" ry="3.2" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.55"/>'
            f'<ellipse cx="120" cy="207" rx="12" ry="3.2" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.55"/>'
        )
    body = f"""
  <g id="boots_{rarity}">
    <path d="M43 188 L74 188 L76 202 L41 202 Z" fill="#3c5276" stroke="#1d2f4a" stroke-width="1.15"/>
    <path d="M104 188 L135 188 L137 202 L102 202 Z" fill="#3c5276" stroke="#1d2f4a" stroke-width="1.15"/>
    <path d="M41 201 L77 201 L79 209 L39 209 Z" fill="#242c3a" stroke="#0f1622" stroke-width="1"/>
    <path d="M102 201 L138 201 L140 209 L100 209 Z" fill="#242c3a" stroke="#0f1622" stroke-width="1"/>
    <path d="M45 192 L74 192" stroke="{c}" stroke-width="1.2" opacity="0.9"/>
    <path d="M106 192 L135 192" stroke="{c}" stroke-width="1.2" opacity="0.9"/>
    {details}
  </g>
"""
    return wrap(body)


def shield_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += '<path d="M38 108 L58 108 M38 116 L58 116 M38 124 L58 124 M38 132 L58 132" stroke="#657fa9" stroke-width="0.82" opacity="0.75"/>'
    if idx >= 2:
        details += f'<path d="M40 102 L58 102 L62 108 L62 140 L58 146 L40 146 L36 140 L36 108 Z" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.82"/>'
    if idx >= 3:
        details += (
            f'<rect x="43" y="115.5" width="12" height="2" rx="1" fill="{c}" opacity="0.86">'
            '<animate attributeName="y" values="115.5;137;115.5" dur="2.1s" repeatCount="indefinite"/>'
            "</rect>"
        )
    if idx >= 4:
        details += f'<path d="M44 126 L49 131 L55 121" stroke="{c}" stroke-width="1.1" fill="none"/><circle cx="49.5" cy="110.4" r="2.1" fill="#1f2f49" stroke="{c}" stroke-width="0.92"/>'
    if idx == 5:
        details += f'<ellipse cx="49" cy="125" rx="17.2" ry="8.2" fill="none" stroke="{c}" stroke-width="1" opacity="0.56"/><ellipse cx="49" cy="125" rx="11.6" ry="5.5" fill="none" stroke="#b6f7ff" stroke-width="0.8" opacity="0.56"/>'
    body = f"""
  <g id="shield_{rarity}">
    <path d="M34 100 L60 100 L64 106 L64 142 L60 149 L34 149 L30 142 L30 106 Z" fill="#324a70" stroke="#162740" stroke-width="1.2"/>
    <rect x="36.5" y="103.4" width="21" height="42" rx="2" fill="#4a628c" opacity="0.85"/>
    <path d="M41 100 L53 100 L57 94 L45 94 Z" fill="#293d5e" stroke="#17263d" stroke-width="0.8"/>
    <path d="M30 106 L64 106" stroke="{c}" stroke-width="1" opacity="0.82"/>
    {details}
  </g>
"""
    return wrap(body)


def weapon_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += f'<path d="M126 104 Q138 96 146 108" stroke="{c}" stroke-width="0.95" fill="none" opacity="0.85"/>'
    if idx >= 2:
        details += f'<path d="M127 112 Q139 106 147 99" stroke="{c}" stroke-width="0.9" fill="none" opacity="0.75"/>'
    if idx >= 3:
        details += (
            f'<circle cx="142" cy="102.5" r="1.6" fill="{c}" opacity="0.95"/>'
            f'<path d="M124 124 L128 120 L131 126 L127 130 Z" fill="#294260" stroke="{c}" stroke-width="0.9"/>'
        )
    if idx >= 4:
        details += (
            f'<path d="M124 106 Q140 94 151 106" stroke="{c}" stroke-width="1.35" fill="none" opacity="0.92"/>'
            f'<path d="M126 118 Q140 112 149 105" stroke="{c}" stroke-width="0.95" fill="none" opacity="0.8">'
            '<animate attributeName="opacity" values="0.45;1;0.45" dur="1.5s" repeatCount="indefinite"/>'
            "</path>"
        )
    if idx == 5:
        details += f'<ellipse cx="142" cy="103" rx="10.8" ry="4.3" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.56"/>'
    body = f"""
  <g id="weapon_{rarity}" transform="rotate(-24 121 131)">
    <rect x="115.2" y="126" width="10.2" height="36" rx="3" fill="#1b2b43" stroke="#0e1725" stroke-width="1"/>
    <rect x="116.8" y="134" width="7" height="2.4" rx="1" fill="{c}" opacity="0.92"/>
    <rect x="116.8" y="145" width="7" height="2.4" rx="1" fill="{c}" opacity="0.75"/>
    <rect x="118.8" y="160" width="3.2" height="4.8" rx="1.4" fill="#28405d"/>
    <path d="M114.8 126 L125.6 126 L127 122 L113.6 122 Z" fill="#38537a" stroke="#1a2b45" stroke-width="1"/>
    <path d="M124 102 Q141 92 152 106 Q138 111 126 124 Z" fill="#cadcf2" stroke="#314b6a" stroke-width="1.05"/>
    <path d="M126.3 103.5 L129.6 108.8 L126.3 114.2 L123 108.8 Z" fill="#f2f7ff" opacity="0.9"/>
    {details}
  </g>
"""
    return wrap(body)


def cloak_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += '<path d="M72 94 L68 182 M108 94 L112 182" stroke="#9cb7dd" stroke-width="0.8" opacity="0.45"/>'
    if idx >= 2:
        details += f'<path d="M68 83 Q90 96 112 83" stroke="{c}" stroke-width="1" fill="none" opacity="0.82"/>'
    if idx >= 3:
        details += (
            f'<rect x="74" y="106" width="32" height="1.6" rx="0.8" fill="{c}" opacity="0.74"/>'
            f'<rect x="74" y="124" width="32" height="1.6" rx="0.8" fill="{c}" opacity="0.74"/>'
            f'<rect x="74" y="142" width="32" height="1.6" rx="0.8" fill="{c}" opacity="0.74"/>'
        )
    if idx >= 4:
        details += (
            f'<path d="M66 112 Q90 96 114 112" stroke="{c}" stroke-width="1.35" fill="none" opacity="0.85"/>'
            f'<path d="M66 150 Q90 136 114 150" stroke="{c}" stroke-width="1.1" fill="none" opacity="0.68"/>'
        )
    if idx == 5:
        details += f'<ellipse cx="90" cy="136" rx="33" ry="18" fill="none" stroke="{c}" stroke-width="1" opacity="0.5"/>'
    body = f"""
  <g id="cloak_{rarity}" opacity="0.9">
    <path d="M63 74 L117 74 L124 92 L117 191 L63 191 L56 92 Z" fill="#1f2f49" opacity="0.5"/>
    <path d="M68 82 L112 82 L116 97 L112 186 L68 186 L64 97 Z" fill="#344d75" opacity="0.46"/>
    <path d="M70 150 L62 191 L74 191 Z" fill="#1b2c45" opacity="0.7"/>
    <path d="M108 150 L120 189 L106 190 Z" fill="#1b2c45" opacity="0.7"/>
    {details}
  </g>
"""
    return wrap(body)


def amulet_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += f'<circle cx="90" cy="100" r="6.6" fill="none" stroke="{c}" stroke-width="1.1" opacity="0.85"/>'
    if idx >= 2:
        details += (
            f'<path d="M90 95.3 L92.3 99.6 L90 103.9 L87.7 99.6 Z" fill="{c}" opacity="0.9"/>'
            f'<path d="M84.5 100 L95.5 100" stroke="{c}" stroke-width="0.92" opacity="0.8"/>'
        )
    if idx >= 3:
        details += (
            f'<circle cx="90" cy="100" r="10.2" fill="none" stroke="{c}" stroke-width="0.88" opacity="0.45">'
            '<animateTransform attributeName="transform" type="rotate" values="0 90 100;360 90 100" dur="8s" repeatCount="indefinite"/>'
            "</circle>"
        )
    if idx >= 4:
        details += f'<path d="M82 100 L76 97 L78 104 Z" fill="{c}" opacity="0.9"/><path d="M98 100 L104 97 L102 104 Z" fill="{c}" opacity="0.9"/>'
    if idx == 5:
        details += f'<ellipse cx="90" cy="100" rx="14.2" ry="5.2" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.58"/><ellipse cx="90" cy="100" rx="10.7" ry="3.9" fill="none" stroke="#b9f8ff" stroke-width="0.8" opacity="0.58"/>'
    pulse = ""
    if idx >= 3:
        pulse = (
            f'<circle cx="90" cy="100" r="2.7" fill="{c}" opacity="0.24">'
            '<animate attributeName="r" values="2.1;4.4;2.1" dur="2s" repeatCount="indefinite"/>'
            "</circle>"
        )
    body = f"""
  <g id="amulet_{rarity}">
    <path d="M86 90 Q90 86 94 90" stroke="#8a9cb5" stroke-width="1.05" fill="none"/>
    <circle cx="90" cy="100" r="5.1" fill="#263c5c" stroke="#122033" stroke-width="1"/>
    <circle cx="90" cy="100" r="2" fill="{c}" opacity="0.95"/>
    {details}
    {pulse}
  </g>
"""
    return wrap(body)


def fx_epic() -> str:
    return wrap(
        """
  <g id="fx_epic">
    <ellipse cx="90" cy="101" rx="25" ry="12" fill="#9C27B0" opacity="0.1"/>
    <circle cx="90" cy="100" r="19" fill="none" stroke="#9C27B0" stroke-width="1.7" opacity="0.67"/>
    <path d="M69 100 L111 100" stroke="#cf83ef" stroke-width="1.05" opacity="0.74"/>
    <circle cx="66" cy="93" r="1.2" fill="#cf83ef"/>
    <circle cx="114" cy="109" r="1.2" fill="#cf83ef"/>
  </g>
"""
    )


def fx_legendary() -> str:
    return wrap(
        """
  <g id="fx_legendary">
    <ellipse cx="90" cy="100" rx="29" ry="14" fill="#FF9800" opacity="0.11"/>
    <ellipse cx="90" cy="100" rx="35" ry="17" fill="none" stroke="#FF9800" stroke-width="1.5" opacity="0.75"/>
    <ellipse cx="90" cy="100" rx="22.5" ry="10.8" fill="none" stroke="#ffd59f" stroke-width="1.05" opacity="0.67"/>
    <path d="M57 102 Q90 75 123 102" stroke="#FF9800" stroke-width="1.4" fill="none" opacity="0.74"/>
    <circle cx="90" cy="82" r="2" fill="#FF9800"/>
  </g>
"""
    )


def fx_celestial() -> str:
    return wrap(
        """
  <g id="fx_celestial">
    <rect x="60" y="0" width="60" height="220" fill="#00E5FF" opacity="0.045"/>
    <ellipse cx="90" cy="100" rx="31" ry="14.3" fill="#00E5FF" opacity="0.1"/>
    <ellipse cx="90" cy="100" rx="39" ry="18.3" fill="none" stroke="#00E5FF" stroke-width="1.15" opacity="0.7"/>
    <ellipse cx="90" cy="100" rx="33" ry="15.1" fill="none" stroke="#a9f8ff" stroke-width="0.9" opacity="0.58"/>
    <path d="M90 67 L90 133" stroke="#bdf9ff" stroke-width="1" opacity="0.55"/>
    <path d="M57 100 L123 100" stroke="#bdf9ff" stroke-width="1" opacity="0.55"/>
    <circle cx="60" cy="88" r="1.25" fill="#9bf6ff"/>
    <circle cx="120" cy="92" r="1.2" fill="#9bf6ff"/>
    <circle cx="104" cy="116" r="1.1" fill="#9bf6ff"/>
    <circle cx="76" cy="116" r="1.1" fill="#9bf6ff"/>
  </g>
"""
    )


def main() -> None:
    write(ROOT / "hero_base.svg", hero_base_svg())
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
    print("scholar pack regenerated")


if __name__ == "__main__":
    main()

