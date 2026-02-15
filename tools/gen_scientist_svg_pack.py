#!/usr/bin/env python3
"""Regenerate complete scientist hero SVG pack with fit-aligned rarity progression."""

from __future__ import annotations

from pathlib import Path


ROOT = Path("icons/heroes/scientist")
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


def helmet_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    side = ""
    if idx >= 1:
        side = f'<rect x="72" y="46.2" width="4.8" height="4.6" rx="1" fill="{c}" opacity="0.75"/><rect x="103.2" y="46.2" width="4.8" height="4.6" rx="1" fill="{c}" opacity="0.75"/>'
    strap = ""
    if idx >= 2:
        strap = f'<path d="M76 48.5 L104 48.5" stroke="{c}" stroke-width="1.05" opacity="0.85"/>'
    crown = ""
    if idx >= 3:
        crown = f'<path d="M84 36 L96 36 L99 43 L81 43 Z" fill="#2e4364" stroke="{c}" stroke-width="0.95"/><circle cx="90" cy="39.5" r="1.8" fill="{c}" opacity="0.95"/>'
    aura = ""
    if idx >= 4:
        aura = f'<ellipse cx="90" cy="48.5" rx="19" ry="7.4" fill="none" stroke="{c}" stroke-width="1.1" opacity="0.62"/>'
    halo = ""
    if idx == 5:
        halo = f'<ellipse cx="90" cy="48.5" rx="25.5" ry="9.8" fill="none" stroke="{c}" stroke-width="1.1" opacity="0.56"/><ellipse cx="90" cy="48.5" rx="21" ry="8.1" fill="none" stroke="#baf8ff" stroke-width="0.85" opacity="0.58"/>'
    body = f"""
  <g id="helmet_{rarity}">
    <rect x="76.2" y="44.6" width="27.6" height="8" rx="3.2" fill="#153047" stroke="#0e1b2b" stroke-width="0.9"/>
    <circle cx="85.5" cy="48.5" r="2.6" fill="none" stroke="#cceeff" stroke-width="1"/>
    <circle cx="94.5" cy="48.5" r="2.6" fill="none" stroke="#cceeff" stroke-width="1"/>
    <path d="M88.1 48.5 L91.9 48.5" stroke="#cceeff" stroke-width="0.85"/>
    <path d="M79.3 48.5 L83 48.5 M97 48.5 L100.7 48.5" stroke="{c}" stroke-width="0.9" opacity="0.8"/>
    {side}
    {strap}
    {crown}
    {aura}
    {halo}
  </g>
"""
    return wrap(body)


def chestplate_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += '<path d="M74 90 L106 90 M74 100 L106 100 M74 110 L106 110 M74 120 L106 120" stroke="#7c8da7" stroke-width="0.85" opacity="0.72"/>'
    if idx >= 2:
        details += f'<path d="M72 82 L80 76 L100 76 L108 82" stroke="{c}" stroke-width="1" fill="none" opacity="0.82"/><path d="M76 134 Q90 139 104 134" stroke="{c}" stroke-width="1.05" fill="none" opacity="0.75"/>'
    if idx >= 3:
        details += f'<rect x="84.5" y="94.5" width="11" height="16.5" rx="2.3" fill="#183048" stroke="{c}" stroke-width="1"/><path d="M87 103 L93 103" stroke="{c}" stroke-width="0.92"/>'
    if idx >= 4:
        details += f'<path d="M68 86 Q90 70 112 86" stroke="{c}" stroke-width="1.28" fill="none" opacity="0.85"/><path d="M74 114 L106 114" stroke="{c}" stroke-width="1.1" opacity="0.8"/>'
    if idx == 5:
        details += f'<ellipse cx="90" cy="103" rx="18" ry="7.2" fill="none" stroke="{c}" stroke-width="0.95" opacity="0.54"/><ellipse cx="90" cy="103" rx="12.5" ry="5.2" fill="none" stroke="#baf8ff" stroke-width="0.8" opacity="0.58"/>'
    body = f"""
  <g id="chestplate_{rarity}">
    <path d="M70 79 L110 79 Q115 86 115 97 L112 145 L68 145 L65 97 Q65 86 70 79 Z" fill="#dae0ea" stroke="#97a3b4" stroke-width="1.1"/>
    <path d="M76 84 L104 84 L105 143 L75 143 Z" fill="#4b5c79" opacity="0.92"/>
    <path d="M76 84 L83 94 L80 143 L74 143 Z" fill="#303f5b" opacity="0.75"/>
    <path d="M104 84 L97 94 L100 143 L106 143 Z" fill="#303f5b" opacity="0.75"/>
    <path d="M90 84 L90 143" stroke="#24324a" stroke-width="1.02"/>
    <path d="M79 86 L86 92 M101 86 L94 92" stroke="#dce4f0" stroke-width="1.05" opacity="0.7"/>
    {details}
  </g>
"""
    return wrap(body)


def gauntlets_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += '<path d="M40 143 L60 143 M120 143 L140 143" stroke="#7f90ab" stroke-width="0.85" opacity="0.75"/>'
    if idx >= 2:
        details += f'<path d="M44 136 L56 136 M124 136 L136 136" stroke="{c}" stroke-width="0.95" opacity="0.82"/>'
    if idx >= 3:
        details += f'<circle cx="49.5" cy="147.2" r="1.4" fill="{c}"/><circle cx="130.5" cy="147.2" r="1.4" fill="{c}"/>'
    if idx >= 4:
        details += f'<path d="M39 145.8 L61 145.8" stroke="{c}" stroke-width="1.22" opacity="0.82"/><path d="M119 145.8 L141 145.8" stroke="{c}" stroke-width="1.22" opacity="0.82"/>'
    if idx == 5:
        details += f'<ellipse cx="50" cy="146.4" rx="8.2" ry="3" fill="none" stroke="{c}" stroke-width="0.82" opacity="0.54"/><ellipse cx="130" cy="146.4" rx="8.2" ry="3" fill="none" stroke="{c}" stroke-width="0.82" opacity="0.54"/>'
    body = f"""
  <g id="gauntlets_{rarity}">
    <path d="M38 134 L62 134 L61 156 L39 156 Z" fill="#dbe2ec" stroke="#97a3b4" stroke-width="1"/>
    <path d="M118 134 L142 134 L141 156 L119 156 Z" fill="#dbe2ec" stroke="#97a3b4" stroke-width="1"/>
    <rect x="42.8" y="150.2" width="14.3" height="2.8" rx="1.2" fill="#f6fbff" opacity="0.92"/>
    <rect x="122.8" y="150.2" width="14.3" height="2.8" rx="1.2" fill="#f6fbff" opacity="0.92"/>
    <path d="M44.5 138 L55.5 138 M124.5 138 L135.5 138" stroke="#415370" stroke-width="0.9"/>
    {details}
  </g>
"""
    return wrap(body)


def boots_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += '<path d="M44 194 L73 194 M106 194 L135 194" stroke="#8a9cb7" stroke-width="0.88" opacity="0.75"/>'
    if idx >= 2:
        details += f'<rect x="53" y="189.7" width="6" height="2.3" rx="1" fill="{c}" opacity="0.85"/><rect x="120" y="189.7" width="6" height="2.3" rx="1" fill="{c}" opacity="0.85"/>'
    if idx >= 3:
        details += f'<path d="M45 202.5 L74 202.5" stroke="{c}" stroke-width="1.08" opacity="0.84"/><path d="M106 202.5 L135 202.5" stroke="{c}" stroke-width="1.08" opacity="0.84"/>'
    if idx >= 4:
        details += f'<path d="M48 188 Q60 181 72 188" stroke="{c}" stroke-width="0.95" fill="none" opacity="0.84"/><path d="M108 188 Q120 181 132 188" stroke="{c}" stroke-width="0.95" fill="none" opacity="0.84"/>'
    if idx == 5:
        details += f'<ellipse cx="60" cy="207" rx="12" ry="3.2" fill="none" stroke="{c}" stroke-width="0.86" opacity="0.54"/><ellipse cx="120" cy="207" rx="12" ry="3.2" fill="none" stroke="{c}" stroke-width="0.86" opacity="0.54"/>'
    body = f"""
  <g id="boots_{rarity}">
    <path d="M43 188 L74 188 L76 202 L41 202 Z" fill="#dce3ed" stroke="#98a4b5" stroke-width="1"/>
    <path d="M104 188 L135 188 L137 202 L102 202 Z" fill="#dce3ed" stroke="#98a4b5" stroke-width="1"/>
    <path d="M41 201 L77 201 L79 209 L39 209 Z" fill="#5a6270" stroke="#2c323b" stroke-width="1"/>
    <path d="M102 201 L138 201 L140 209 L100 209 Z" fill="#5a6270" stroke="#2c323b" stroke-width="1"/>
    <path d="M45 192 L74 192" stroke="{c}" stroke-width="1.12" opacity="0.88"/>
    <path d="M106 192 L135 192" stroke="{c}" stroke-width="1.12" opacity="0.88"/>
    {details}
  </g>
"""
    return wrap(body)


def shield_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += '<path d="M38 109 L58 109 M38 117 L58 117 M38 125 L58 125 M38 133 L58 133" stroke="#8fa3bf" stroke-width="0.82" opacity="0.75"/>'
    if idx >= 2:
        details += f'<path d="M40 103 L58 103 L62 109 L62 140 L58 146 L40 146 L36 140 L36 109 Z" fill="none" stroke="{c}" stroke-width="0.9" opacity="0.82"/>'
    if idx >= 3:
        details += f'<rect x="43" y="115.5" width="12" height="2" rx="1" fill="{c}" opacity="0.86"><animate attributeName="y" values="115.5;137;115.5" dur="2.1s" repeatCount="indefinite"/></rect>'
    if idx >= 4:
        details += f'<path d="M44 126 L49 131 L55 121" stroke="{c}" stroke-width="1.08" fill="none"/><circle cx="49.5" cy="110.4" r="2.05" fill="#22334d" stroke="{c}" stroke-width="0.9"/>'
    if idx == 5:
        details += f'<ellipse cx="49" cy="125" rx="17.2" ry="8.2" fill="none" stroke="{c}" stroke-width="0.95" opacity="0.55"/><ellipse cx="49" cy="125" rx="11.7" ry="5.5" fill="none" stroke="#baf8ff" stroke-width="0.8" opacity="0.58"/>'
    body = f"""
  <g id="shield_{rarity}">
    <path d="M34 100 L60 100 L64 106 L64 142 L60 149 L34 149 L30 142 L30 106 Z" fill="#dce3ed" stroke="#97a4b5" stroke-width="1"/>
    <rect x="36.5" y="103.4" width="21" height="42" rx="2" fill="#4b5d7a" opacity="0.9"/>
    <path d="M41 100 L53 100 L57 94 L45 94 Z" fill="#dce3ed" stroke="#97a4b5" stroke-width="0.8"/>
    <path d="M30 106 L64 106" stroke="{c}" stroke-width="0.98" opacity="0.82"/>
    {details}
  </g>
"""
    return wrap(body)


def weapon_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += f'<path d="M126 103.5 Q139 96 146 108" stroke="{c}" stroke-width="0.9" fill="none" opacity="0.82"/>'
    if idx >= 2:
        details += f'<path d="M127 111.5 Q139 106 147 99" stroke="{c}" stroke-width="0.85" fill="none" opacity="0.75"/>'
    if idx >= 3:
        details += f'<circle cx="142" cy="102.5" r="1.5" fill="{c}" opacity="0.95"/><path d="M124 124 L128 120 L131 126 L127 130 Z" fill="#28415f" stroke="{c}" stroke-width="0.88"/>'
    if idx >= 4:
        details += f'<path d="M124 106 Q140 94 151 106" stroke="{c}" stroke-width="1.28" fill="none" opacity="0.9"/><path d="M126 118 Q140 112 149 105" stroke="{c}" stroke-width="0.9" fill="none" opacity="0.8"><animate attributeName="opacity" values="0.45;1;0.45" dur="1.5s" repeatCount="indefinite"/></path>'
    if idx == 5:
        details += f'<ellipse cx="142" cy="103" rx="10.8" ry="4.3" fill="none" stroke="{c}" stroke-width="0.88" opacity="0.55"/>'
    body = f"""
  <g id="weapon_{rarity}" transform="rotate(-24 121 131)">
    <rect x="115.2" y="126" width="10.2" height="36" rx="3" fill="#1b2b43" stroke="#0e1725" stroke-width="1"/>
    <rect x="116.8" y="134" width="7" height="2.4" rx="1" fill="{c}" opacity="0.92"/>
    <rect x="116.8" y="145" width="7" height="2.4" rx="1" fill="{c}" opacity="0.75"/>
    <rect x="118.8" y="160" width="3.2" height="4.8" rx="1.4" fill="#28405d"/>
    <path d="M114.8 126 L125.6 126 L127 122 L113.6 122 Z" fill="#38537a" stroke="#1a2b45" stroke-width="1"/>
    <path d="M124 102 Q141 92 152 106 Q138 111 126 124 Z" fill="#d7e6f8" stroke="#385372" stroke-width="1.02"/>
    <path d="M126.3 103.5 L129.6 108.8 L126.3 114.2 L123 108.8 Z" fill="#ffffff" opacity="0.92"/>
    {details}
  </g>
"""
    return wrap(body)


def cloak_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += '<path d="M72 94 L68 182 M108 94 L112 182" stroke="#9fb3d1" stroke-width="0.8" opacity="0.45"/>'
    if idx >= 2:
        details += f'<path d="M68 83 Q90 96 112 83" stroke="{c}" stroke-width="0.95" fill="none" opacity="0.82"/>'
    if idx >= 3:
        details += f'<rect x="74" y="106" width="32" height="1.6" rx="0.8" fill="{c}" opacity="0.73"/><rect x="74" y="124" width="32" height="1.6" rx="0.8" fill="{c}" opacity="0.73"/><rect x="74" y="142" width="32" height="1.6" rx="0.8" fill="{c}" opacity="0.73"/>'
    if idx >= 4:
        details += f'<path d="M66 112 Q90 96 114 112" stroke="{c}" stroke-width="1.25" fill="none" opacity="0.85"/><path d="M66 150 Q90 136 114 150" stroke="{c}" stroke-width="1.05" fill="none" opacity="0.67"/>'
    if idx == 5:
        details += f'<ellipse cx="90" cy="136" rx="33" ry="18" fill="none" stroke="{c}" stroke-width="0.95" opacity="0.5"/>'
    body = f"""
  <g id="cloak_{rarity}" opacity="0.86">
    <path d="M63 74 L117 74 L124 92 L117 191 L63 191 L56 92 Z" fill="#dce3ed" opacity="0.36"/>
    <path d="M68 82 L112 82 L116 97 L112 186 L68 186 L64 97 Z" fill="#5a6f92" opacity="0.34"/>
    <path d="M70 150 L62 191 L74 191 Z" fill="#415a80" opacity="0.5"/>
    <path d="M108 150 L120 189 L106 190 Z" fill="#415a80" opacity="0.5"/>
    {details}
  </g>
"""
    return wrap(body)


def amulet_svg(rarity: str, idx: int) -> str:
    c = RARITY_COLORS[rarity]
    details = ""
    if idx >= 1:
        details += f'<circle cx="90" cy="100" r="6.6" fill="none" stroke="{c}" stroke-width="1.05" opacity="0.85"/>'
    if idx >= 2:
        details += f'<path d="M90 95.3 L92.3 99.6 L90 103.9 L87.7 99.6 Z" fill="{c}" opacity="0.9"/><path d="M84.5 100 L95.5 100" stroke="{c}" stroke-width="0.9" opacity="0.8"/>'
    if idx >= 3:
        details += f'<circle cx="90" cy="100" r="10.2" fill="none" stroke="{c}" stroke-width="0.86" opacity="0.45"><animateTransform attributeName="transform" type="rotate" values="0 90 100;360 90 100" dur="8s" repeatCount="indefinite"/></circle>'
    if idx >= 4:
        details += f'<path d="M82 100 L76 97 L78 104 Z" fill="{c}" opacity="0.9"/><path d="M98 100 L104 97 L102 104 Z" fill="{c}" opacity="0.9"/>'
    if idx == 5:
        details += f'<ellipse cx="90" cy="100" rx="14.2" ry="5.2" fill="none" stroke="{c}" stroke-width="0.88" opacity="0.58"/><ellipse cx="90" cy="100" rx="10.7" ry="3.9" fill="none" stroke="#bcf8ff" stroke-width="0.78" opacity="0.58"/>'
    pulse = ""
    if idx >= 3:
        pulse = f'<circle cx="90" cy="100" r="2.7" fill="{c}" opacity="0.24"><animate attributeName="r" values="2.1;4.4;2.1" dur="2s" repeatCount="indefinite"/></circle>'
    body = f"""
  <g id="amulet_{rarity}">
    <path d="M86 90 Q90 86 94 90" stroke="#8fa2bc" stroke-width="1.02" fill="none"/>
    <circle cx="90" cy="100" r="5.1" fill="#304868" stroke="#15263c" stroke-width="1"/>
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
    <circle cx="90" cy="100" r="19" fill="none" stroke="#9C27B0" stroke-width="1.65" opacity="0.66"/>
    <path d="M69 100 L111 100" stroke="#cf83ef" stroke-width="1" opacity="0.74"/>
    <circle cx="66" cy="93" r="1.15" fill="#cf83ef"/>
    <circle cx="114" cy="109" r="1.15" fill="#cf83ef"/>
  </g>
"""
    )


def fx_legendary() -> str:
    return wrap(
        """
  <g id="fx_legendary">
    <ellipse cx="90" cy="100" rx="29" ry="14" fill="#FF9800" opacity="0.11"/>
    <ellipse cx="90" cy="100" rx="35" ry="17" fill="none" stroke="#FF9800" stroke-width="1.45" opacity="0.74"/>
    <ellipse cx="90" cy="100" rx="22.5" ry="10.8" fill="none" stroke="#ffd59f" stroke-width="1" opacity="0.67"/>
    <path d="M57 102 Q90 75 123 102" stroke="#FF9800" stroke-width="1.35" fill="none" opacity="0.74"/>
    <circle cx="90" cy="82" r="1.95" fill="#FF9800"/>
  </g>
"""
    )


def fx_celestial() -> str:
    return wrap(
        """
  <g id="fx_celestial">
    <rect x="60" y="0" width="60" height="220" fill="#00E5FF" opacity="0.045"/>
    <ellipse cx="90" cy="100" rx="31" ry="14.3" fill="#00E5FF" opacity="0.1"/>
    <ellipse cx="90" cy="100" rx="39" ry="18.3" fill="none" stroke="#00E5FF" stroke-width="1.12" opacity="0.7"/>
    <ellipse cx="90" cy="100" rx="33" ry="15.1" fill="none" stroke="#b1f9ff" stroke-width="0.88" opacity="0.58"/>
    <path d="M90 67 L90 133" stroke="#bdf9ff" stroke-width="1" opacity="0.55"/>
    <path d="M57 100 L123 100" stroke="#bdf9ff" stroke-width="1" opacity="0.55"/>
    <circle cx="60" cy="88" r="1.2" fill="#9bf6ff"/>
    <circle cx="120" cy="92" r="1.15" fill="#9bf6ff"/>
    <circle cx="104" cy="116" r="1.08" fill="#9bf6ff"/>
    <circle cx="76" cy="116" r="1.08" fill="#9bf6ff"/>
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
    print("scientist pack regenerated")


if __name__ == "__main__":
    main()

