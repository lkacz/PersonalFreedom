#!/usr/bin/env python3
"""
Script to add unique SMIL animations to SVG entity files based on their content.
Each entity gets an animation that matches its character/nature.
"""
import os
import re

ICONS_PATH = r"F:\_DEV\PersonalFreedom\icons\entities"

# Animation templates for different entity types
ANIMATIONS = {
    # SCHOLAR entities
    "scholar_001_library_mouse_pip.svg": {
        # Mouse whiskers twitch, tail swishes
        "search": r'(<line x1="48" y1="24" x2="56" y2="22"[^>]*/>)',
        "replace": r'''<line x1="48" y1="24" x2="56" y2="22" stroke="#9E9E9E" stroke-width="0.5">
    <animate attributeName="y2" values="22;20;22;24;22" dur="0.8s" repeatCount="indefinite"/>
  </line>''',
        "additional": [
            (r'(<path d="M20 32 Q12 28, 8 32 Q4 36, 8 40"[^>]*/>)',
             r'''<path d="M20 32 Q12 28, 8 32 Q4 36, 8 40" stroke="#E0E0E0" stroke-width="2.5" fill="none" stroke-linecap="round">
    <animate attributeName="d" values="M20 32 Q12 28, 8 32 Q4 36, 8 40;M20 32 Q10 30, 6 34 Q2 38, 6 42;M20 32 Q12 28, 8 32 Q4 36, 8 40" dur="1.2s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "scholar_002_study_owl_athena.svg": {
        # Owl blinks slowly, head slight tilt
        "search": r'(<!-- Cute big eyes -->)',
        "replace": r'''<!-- Cute big eyes - blinking -->''',
        "additional": [
            (r'(<circle cx="28" cy="24" r="5" fill="white"/>)',
             r'''<circle cx="28" cy="24" r="5" fill="white">
    <animate attributeName="ry" values="5;0.5;5" dur="4s" repeatCount="indefinite"/>
  </circle>'''),
            (r'(<circle cx="40" cy="24" r="5" fill="white"/>)',
             r'''<circle cx="40" cy="24" r="5" fill="white">
    <animate attributeName="ry" values="5;0.5;5" dur="4s" repeatCount="indefinite"/>
  </circle>''')
        ]
    },
    
    "scholar_003_reading_candle.svg": {
        # Flame flickers
        "search": r'(<path d="M32 4 Q28 10, 30 14 Q32 18, 32 16 Q32 18, 34 14 Q36 10, 32 4" fill="url\(#flameCore\)"/>)',
        "replace": r'''<path d="M32 4 Q28 10, 30 14 Q32 18, 32 16 Q32 18, 34 14 Q36 10, 32 4" fill="url(#flameCore)">
    <animate attributeName="d" values="M32 4 Q28 10, 30 14 Q32 18, 32 16 Q32 18, 34 14 Q36 10, 32 4;M32 3 Q27 9, 29 13 Q31 17, 32 15 Q33 17, 35 13 Q37 9, 32 3;M32 5 Q29 11, 31 15 Q32 19, 32 17 Q32 19, 33 15 Q35 11, 32 5;M32 4 Q28 10, 30 14 Q32 18, 32 16 Q32 18, 34 14 Q36 10, 32 4" dur="0.5s" repeatCount="indefinite"/>
  </path>''',
        "additional": [
            (r'(<circle cx="26" cy="8" r="0.8" fill="#FFEB3B" opacity="0.7"/>)',
             r'''<circle cx="26" cy="8" r="0.8" fill="#FFEB3B" opacity="0.7">
    <animate attributeName="opacity" values="0.7;0.3;0.7;1;0.7" dur="0.8s" repeatCount="indefinite"/>
    <animate attributeName="cy" values="8;6;8" dur="1.5s" repeatCount="indefinite"/>
  </circle>''')
        ]
    },
    
    "scholar_004_library_cat_scholar.svg": {
        # Cat tail swishes, ears twitch
        "search": r'(<!-- Long elegant tail -->)',
        "replace": r'''<!-- Long elegant tail - animated -->''',
        "additional": [
            (r'(<path d="M46 44 Q54 40, 58 46 Q60 52, 56 56"[^>]*/>)',
             r'''<path d="M46 44 Q54 40, 58 46 Q60 52, 56 56" stroke="#424242" stroke-width="3" fill="none" stroke-linecap="round">
    <animate attributeName="d" values="M46 44 Q54 40, 58 46 Q60 52, 56 56;M46 44 Q52 42, 56 48 Q58 54, 52 58;M46 44 Q54 40, 58 46 Q60 52, 56 56" dur="2s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "scholar_005_living_bookmark_finn.svg": {
        # Bookmark ribbon waves
        "search": r'(<!-- Ribbon tails -->)',
        "replace": r'''<!-- Ribbon tails - waving -->''',
        "additional": [
            (r'(<path d="M24 46[^"]*"[^>]*fill="#7E57C2"[^>]*/>)',
             r'''<path d="M24 46 Q22 52, 26 58 Q24 62, 22 64" fill="#7E57C2">
    <animate attributeName="d" values="M24 46 Q22 52, 26 58 Q24 62, 22 64;M24 46 Q20 52, 24 58 Q22 62, 20 64;M24 46 Q22 52, 26 58 Q24 62, 22 64" dur="1.5s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "scholar_006_sentient_tome_magnus.svg": {
        # Pages flutter slightly, eye blinks
        "search": r'(<!-- Fluttering page corners -->)',
        "replace": r'''<!-- Fluttering page corners - animated -->''',
        "additional": [
            (r'(<path d="M52 24 Q56 22, 54 18"[^>]*/>)',
             r'''<path d="M52 24 Q56 22, 54 18" fill="#FFFDE7">
    <animate attributeName="d" values="M52 24 Q56 22, 54 18;M52 24 Q58 20, 56 16;M52 24 Q56 22, 54 18" dur="0.8s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "scholar_007_ancient_star_map.svg": {
        # Stars twinkle
        "search": r'(<!-- Constellation stars -->)',
        "replace": r'''<!-- Constellation stars - twinkling -->''',
        "additional": [
            (r'(<circle cx="20" cy="20" r="1.5" fill="#FFD54F"/>)',
             r'''<circle cx="20" cy="20" r="1.5" fill="#FFD54F">
    <animate attributeName="opacity" values="1;0.4;1" dur="1.5s" repeatCount="indefinite"/>
  </circle>'''),
            (r'(<circle cx="44" cy="18" r="2" fill="#FFD54F"/>)',
             r'''<circle cx="44" cy="18" r="2" fill="#FFD54F">
    <animate attributeName="opacity" values="0.6;1;0.6" dur="1.2s" repeatCount="indefinite"/>
  </circle>''')
        ]
    },
    
    "scholar_008_archive_phoenix.svg": {
        # Flame feathers flicker
        "search": r'(<!-- Flame-like feather tips -->)',
        "replace": r'''<!-- Flame-like feather tips - flickering -->''',
        "additional": [
            (r'(<path d="M16 28 Q12 24, 14 20 Q10 22, 8 18"[^>]*/>)',
             r'''<path d="M16 28 Q12 24, 14 20 Q10 22, 8 18" fill="#FF5722">
    <animate attributeName="d" values="M16 28 Q12 24, 14 20 Q10 22, 8 18;M16 28 Q11 23, 13 19 Q9 21, 7 17;M16 28 Q12 24, 14 20 Q10 22, 8 18" dur="0.4s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "scholar_009_blank_parchment.svg": {
        # Slight paper curl/wave
        "search": r'(<!-- Paper curl hint -->)',
        "replace": r'''<!-- Paper curl hint - breathing -->''',
        "additional": [
            (r'(<path d="M48 54 Q52 52, 50 48"[^>]*/>)',
             r'''<path d="M48 54 Q52 52, 50 48" fill="#FFFDE7">
    <animate attributeName="d" values="M48 54 Q52 52, 50 48;M48 54 Q54 50, 52 46;M48 54 Q52 52, 50 48" dur="2s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    # SCIENTIST entities
    "scientist_001_cracked_test_tube.svg": {
        # Liquid bubbles rise
        "search": r'(<!-- Small bubbles in liquid -->)',
        "replace": r'''<!-- Small bubbles in liquid - rising -->''',
        "additional": [
            (r'(<circle cx="30" cy="42" r="1" fill="white" opacity="0.6"/>)',
             r'''<circle cx="30" cy="42" r="1" fill="white" opacity="0.6">
    <animate attributeName="cy" values="42;36;30;42" dur="2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.6;0.8;0.2;0.6" dur="2s" repeatCount="indefinite"/>
  </circle>'''),
            (r'(<circle cx="34" cy="46" r="1.5" fill="white" opacity="0.5"/>)',
             r'''<circle cx="34" cy="46" r="1.5" fill="white" opacity="0.5">
    <animate attributeName="cy" values="46;38;32;46" dur="2.5s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.5;0.7;0.1;0.5" dur="2.5s" repeatCount="indefinite"/>
  </circle>''')
        ]
    },
    
    "scientist_004_wise_lab_rat_professor.svg": {
        # Whiskers twitch, nose wiggles
        "search": r'(<!-- Whiskers -->)',
        "replace": r'''<!-- Whiskers - twitching -->''',
        "additional": [
            (r'(<line x1="46" y1="30" x2="56" y2="28"[^>]*/>)',
             r'''<line x1="46" y1="30" x2="56" y2="28" stroke="#9E9E9E" stroke-width="0.5">
    <animate attributeName="y2" values="28;26;28;30;28" dur="0.6s" repeatCount="indefinite"/>
  </line>'''),
            (r'(<ellipse cx="44" cy="32" rx="2" ry="1.5" fill="#F48FB1"/>)',
             r'''<ellipse cx="44" cy="32" rx="2" ry="1.5" fill="#F48FB1">
    <animate attributeName="rx" values="2;2.2;2;1.8;2" dur="0.4s" repeatCount="indefinite"/>
  </ellipse>''')
        ]
    },
    
    # UNDERDOG entities
    "underdog_001_office_rat_reginald.svg": {
        # Tail twitches, coffee cup steams
        "search": r'(<!-- Long elegant tail -->)',
        "replace": r'''<!-- Long elegant tail - twitching -->''',
        "additional": [
            (r'(<path d="M16 42 Q8 38, 6 44 Q4 50, 10 52"[^>]*/>)',
             r'''<path d="M16 42 Q8 38, 6 44 Q4 50, 10 52" stroke="#BDBDBD" stroke-width="2" fill="none" stroke-linecap="round">
    <animate attributeName="d" values="M16 42 Q8 38, 6 44 Q4 50, 10 52;M16 42 Q6 40, 4 46 Q2 52, 8 54;M16 42 Q8 38, 6 44 Q4 50, 10 52" dur="1.5s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "underdog_002_lucky_sticky_note.svg": {
        # Corner flaps slightly
        "search": r'(<!-- Curled corner -->)',
        "replace": r'''<!-- Curled corner - flapping -->''',
        "additional": [
            (r'(<path d="M42 8 L54 8 L54 20 Q50 18, 42 20 Q44 14, 42 8"[^>]*/>)',
             r'''<path d="M42 8 L54 8 L54 20 Q50 18, 42 20 Q44 14, 42 8" fill="#FFE082">
    <animate attributeName="d" values="M42 8 L54 8 L54 20 Q50 18, 42 20 Q44 14, 42 8;M40 8 L54 8 L54 22 Q48 20, 40 22 Q42 15, 40 8;M42 8 L54 8 L54 20 Q50 18, 42 20 Q44 14, 42 8" dur="2s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "underdog_003_vending_machine_coin.svg": {
        # Coin glints
        "search": r'(<!-- Lucky glint -->)',
        "replace": r'''<!-- Lucky glint - shining -->''',
        "additional": [
            (r'(<circle cx="40" cy="24" r="2" fill="white" opacity="0.8"/>)',
             r'''<circle cx="40" cy="24" r="2" fill="white" opacity="0.8">
    <animate attributeName="opacity" values="0.8;0.2;0.8;1;0.8" dur="2s" repeatCount="indefinite"/>
  </circle>''')
        ]
    },
    
    "underdog_004_window_pigeon_winston.svg": {
        # Head bobs, foot taps morse
        "search": r'(<!-- Tapping foot -->)',
        "replace": r'''<!-- Tapping foot - morse code -->''',
        "additional": [
            (r'(<circle cx="37" cy="50" r="2"/>)',
             r'''<circle cx="37" cy="50" r="2">
    <animate attributeName="cy" values="50;48;50;48;48;50" dur="1s" repeatCount="indefinite"/>
  </circle>''')
        ]
    },
    
    "underdog_005_desk_succulent_sam.svg": {
        # Gentle sway
        "search": r'(<!-- Main rosette center -->)',
        "replace": r'''<!-- Main rosette center - gently swaying -->''',
        "additional": [
            (r'(<ellipse cx="32" cy="32" rx="8" ry="6" fill="url\(#succulentGreen\)"[^>]*/>)',
             r'''<g transform-origin="32 50">
    <animate attributeName="transform" attributeType="XML" type="rotate" values="-2;2;-2" dur="3s" repeatCount="indefinite"/>
  </g>''')
        ]
    },
    
    # WANDERER entities  
    "wanderer_001_lucky_coin.svg": {
        # Coin spins/glints
        "search": r'(<!-- Lucky sparkle -->)',
        "replace": r'''<!-- Lucky sparkle - animated -->''',
        "additional": [
            (r'(<circle cx="44" cy="18" r="1.5"/>)',
             r'''<circle cx="44" cy="18" r="1.5">
    <animate attributeName="opacity" values="0.5;1;0.5;0.2;0.5" dur="1.5s" repeatCount="indefinite"/>
  </circle>'''),
            (r'(<circle cx="48" cy="24" r="1"/>)',
             r'''<circle cx="48" cy="24" r="1">
    <animate attributeName="opacity" values="0.2;0.8;0.2" dur="1.2s" repeatCount="indefinite"/>
  </circle>''')
        ]
    },
    
    "wanderer_002_brass_compass.svg": {
        # Needle wobbles slightly
        "search": r'(<!-- Compass needle -->)',
        "replace": r'''<!-- Compass needle - wobbling -->''',
        "additional": [
            (r'(<path d="M32 18 L28 32 L32 28 L36 32 Z" fill="#C62828"/>)',
             r'''<path d="M32 18 L28 32 L32 28 L36 32 Z" fill="#C62828">
    <animateTransform attributeName="transform" type="rotate" values="-5,32,32;5,32,32;-5,32,32" dur="2s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    # WARRIOR entities
    "warrior_001_hatchling_drake.svg": {
        # Smoke puffs float up
        "search": r'(<!-- Tiny smoke puffs -->)',
        "replace": r'''<!-- Tiny smoke puffs - floating -->''',
        "additional": [
            (r'(<circle cx="48" cy="22" r="3" fill="#B0BEC5" opacity="0.5"/>)',
             r'''<circle cx="48" cy="22" r="3" fill="#B0BEC5" opacity="0.5">
    <animate attributeName="cy" values="22;18;14;22" dur="2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.5;0.3;0.1;0.5" dur="2s" repeatCount="indefinite"/>
  </circle>'''),
            (r'(<circle cx="52" cy="18" r="2" fill="#CFD8DC" opacity="0.4"/>)',
             r'''<circle cx="52" cy="18" r="2" fill="#CFD8DC" opacity="0.4">
    <animate attributeName="cy" values="18;14;10;18" dur="2.2s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.4;0.2;0;0.4" dur="2.2s" repeatCount="indefinite"/>
  </circle>''')
        ]
    },
    
    "warrior_002_old_training_dummy.svg": {
        # Slight wobble like just been hit
        "search": r'(<!-- Body -->)',
        "replace": r'''<!-- Body - wobbling -->''',
        "additional": [
            (r'(<rect x="24" y="24" width="16" height="24" rx="2" fill="url\(#dummyBody\)"/>)',
             r'''<rect x="24" y="24" width="16" height="24" rx="2" fill="url(#dummyBody)">
    <animateTransform attributeName="transform" type="rotate" values="-2,32,48;2,32,48;-2,32,48" dur="1.5s" repeatCount="indefinite"/>
  </rect>''')
        ]
    },
    
    "warrior_003_battle_falcon_swift.svg": {
        # Wings flutter, head moves alertly
        "search": r'(<!-- Left wing \(spread for attack\) -->)',
        "replace": r'''<!-- Left wing (spread for attack) - fluttering -->''',
        "additional": [
            (r'(<path d="M16 36 Q8 30, 6 38 Q4 46, 12 48 Q18 44, 20 40 Z" fill="url\(#falconWing\)"[^>]*/>)',
             r'''<path d="M16 36 Q8 30, 6 38 Q4 46, 12 48 Q18 44, 20 40 Z" fill="url(#falconWing)" stroke="#3E2723" stroke-width="0.5">
    <animate attributeName="d" values="M16 36 Q8 30, 6 38 Q4 46, 12 48 Q18 44, 20 40 Z;M16 36 Q6 28, 4 36 Q2 44, 10 46 Q16 42, 18 38 Z;M16 36 Q8 30, 6 38 Q4 46, 12 48 Q18 44, 20 40 Z" dur="0.8s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "warrior_004_war_horse_thunder.svg": {
        # Mane flows, nostrils flare
        "search": r'(<!-- Flowing mane -->)',
        "replace": r'''<!-- Flowing mane - animated -->''',
        "additional": [
            (r'(<path d="M18 14 Q14 18, 16 24 Q12 28, 14 34"[^>]*/>)',
             r'''<path d="M18 14 Q14 18, 16 24 Q12 28, 14 34" fill="#212121">
    <animate attributeName="d" values="M18 14 Q14 18, 16 24 Q12 28, 14 34;M18 14 Q12 20, 14 26 Q10 30, 12 36;M18 14 Q14 18, 16 24 Q12 28, 14 34" dur="1.5s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "warrior_005_dragon_whelp_ember.svg": {
        # Fire breath flickers
        "search": r'(<!-- Tiny fire breath -->)',
        "replace": r'''<!-- Tiny fire breath - flickering -->''',
        "additional": [
            (r'(<path d="M50 30 Q54 28, 56 32 Q58 28, 56 26"[^>]*/>)',
             r'''<path d="M50 30 Q54 28, 56 32 Q58 28, 56 26" fill="#FF5722">
    <animate attributeName="d" values="M50 30 Q54 28, 56 32 Q58 28, 56 26;M50 30 Q56 26, 58 30 Q60 26, 58 24;M50 30 Q54 28, 56 32 Q58 28, 56 26" dur="0.3s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "warrior_006_battle_standard.svg": {
        # Flag waves in wind
        "search": r'(<!-- Flag fabric -->)',
        "replace": r'''<!-- Flag fabric - waving -->''',
        "additional": [
            (r'(<path d="M16 8 Q32 12, 48 8 Q48 20, 32 24 Q16 20, 16 8"[^>]*/>)',
             r'''<path d="M16 8 Q32 12, 48 8 Q48 20, 32 24 Q16 20, 16 8" fill="url(#flagRed)">
    <animate attributeName="d" values="M16 8 Q32 12, 48 8 Q48 20, 32 24 Q16 20, 16 8;M16 8 Q28 14, 48 6 Q50 18, 34 22 Q18 18, 16 8;M16 8 Q32 12, 48 8 Q48 20, 32 24 Q16 20, 16 8" dur="1.5s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "warrior_007_battle_dragon_crimson.svg": {
        # Fire breath roars, wings move
        "search": r'(<!-- Fire breath -->)',
        "replace": r'''<!-- Fire breath - roaring -->''',
        "additional": [
            (r'(<path d="M50 26 Q56 22, 58 28 Q62 24, 60 20"[^>]*/>)',
             r'''<path d="M50 26 Q56 22, 58 28 Q62 24, 60 20" fill="#FF5722">
    <animate attributeName="d" values="M50 26 Q56 22, 58 28 Q62 24, 60 20;M50 26 Q58 20, 60 26 Q64 22, 62 18;M50 26 Q56 22, 58 28 Q62 24, 60 20" dur="0.25s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "warrior_008_dire_wolf_fenris.svg": {
        # Tail swishes, eyes glow
        "search": r'(<!-- Bushy tail -->)',
        "replace": r'''<!-- Bushy tail - swishing -->''',
        "additional": [
            (r'(<path d="M8 36 Q4 32, 6 26 Q2 22, 8 20"[^>]*/>)',
             r'''<path d="M8 36 Q4 32, 6 26 Q2 22, 8 20" fill="#424242">
    <animate attributeName="d" values="M8 36 Q4 32, 6 26 Q2 22, 8 20;M8 36 Q2 34, 4 28 Q0 24, 6 22;M8 36 Q4 32, 6 26 Q2 22, 8 20" dur="1.8s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
    
    "warrior_009_old_war_ant_general.svg": {
        # Antennae twitch
        "search": r'(<!-- Antennae -->)',
        "replace": r'''<!-- Antennae - twitching -->''',
        "additional": [
            (r'(<path d="M28 14 Q24 8, 20 6"[^>]*/>)',
             r'''<path d="M28 14 Q24 8, 20 6" stroke="#212121" stroke-width="1.5" fill="none">
    <animate attributeName="d" values="M28 14 Q24 8, 20 6;M28 14 Q22 10, 18 8;M28 14 Q24 8, 20 6" dur="0.8s" repeatCount="indefinite"/>
  </path>''')
        ]
    },
}


def add_animation_to_svg(filepath, animation_config):
    """Add animation to a single SVG file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already has animation
    if '<animate' in content:
        print(f"  Skipping {os.path.basename(filepath)} - already has animation")
        return False
    
    modified = False
    
    # Apply main replacement if exists
    if 'search' in animation_config and 'replace' in animation_config:
        new_content = re.sub(animation_config['search'], animation_config['replace'], content, count=1)
        if new_content != content:
            content = new_content
            modified = True
    
    # Apply additional replacements
    if 'additional' in animation_config:
        for search, replace in animation_config['additional']:
            new_content = re.sub(search, replace, content, count=1)
            if new_content != content:
                content = new_content
                modified = True
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Added animation to {os.path.basename(filepath)}")
        return True
    else:
        print(f"  ⚠ No changes made to {os.path.basename(filepath)} - patterns not found")
        return False


def main():
    """Process all SVG files that need animations."""
    print("Adding SMIL animations to entity SVGs...\n")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for filename, config in ANIMATIONS.items():
        filepath = os.path.join(ICONS_PATH, filename)
        if os.path.exists(filepath):
            result = add_animation_to_svg(filepath, config)
            if result:
                success_count += 1
            elif '<animate' in open(filepath, 'r', encoding='utf-8').read():
                skip_count += 1
            else:
                fail_count += 1
        else:
            print(f"  ✗ File not found: {filename}")
            fail_count += 1
    
    print(f"\n{'='*50}")
    print(f"Animation update complete!")
    print(f"  Animated: {success_count}")
    print(f"  Skipped (already animated): {skip_count}")
    print(f"  Failed: {fail_count}")


if __name__ == "__main__":
    main()
