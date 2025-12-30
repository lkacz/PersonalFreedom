#!/usr/bin/env python3
"""Test script to verify story logic and structure."""

from gamification import (
    WARRIOR_CHAPTERS, WARRIOR_DECISIONS, get_chapter_content, 
    get_story_progress, ensure_hero_structure, make_story_decision,
    get_decision_path, has_made_decision, STORY_THRESHOLDS
)

def test_story_structure():
    """Verify basic story structure."""
    print("=== WARRIOR STORY STRUCTURE ===")
    print(f"Total chapters: {len(WARRIOR_CHAPTERS)}")
    print(f"Total decisions: {len(WARRIOR_DECISIONS)}")
    print(f"Thresholds: {STORY_THRESHOLDS}")
    print()
    
    for i, ch in enumerate(WARRIOR_CHAPTERS):
        num = i + 1
        title = ch.get("title", "Unknown")
        threshold = ch.get("threshold", 0)
        has_dec = ch.get("has_decision", False)
        has_var = "content_variations" in ch
        has_end = "endings" in ch
        
        print(f"Chapter {num}: {title}")
        print(f"  Threshold: {threshold} power")
        print(f"  Has decision: {has_dec}")
        
        if has_dec:
            dec_id = ch.get("decision_id")
            print(f"  Decision ID: {dec_id}")
            if num in WARRIOR_DECISIONS:
                dec = WARRIOR_DECISIONS[num]
                print(f"  Decision defined: YES")
                print(f"  Choices: A={dec['choices']['A']['label']}, B={dec['choices']['B']['label']}")
            else:
                print(f"  ERROR: Decision not found in WARRIOR_DECISIONS!")
            
            # Check content_after_decision exists
            if "content_after_decision" in ch:
                after = ch["content_after_decision"]
                print(f"  Content after A: {len(after.get('A', ''))} chars")
                print(f"  Content after B: {len(after.get('B', ''))} chars")
            else:
                print(f"  ERROR: No content_after_decision!")
        
        if has_var:
            variations = list(ch["content_variations"].keys())
            print(f"  Variations: {variations}")
        
        if has_end:
            endings = list(ch["endings"].keys())
            print(f"  Endings: {endings}")
        
        print()


def test_decision_paths():
    """Test all possible decision paths."""
    print("=== DECISION PATH TESTS ===")
    
    from gamification import calculate_character_power
    
    paths_to_test = [
        [],           # No decisions
        ["A"],        # First decision only
        ["B"],
        ["A", "A"],   # Two decisions
        ["A", "B"],
        ["B", "A"],
        ["B", "B"],
        ["A", "A", "A"],  # All three decisions
        ["A", "A", "B"],
        ["A", "B", "A"],
        ["A", "B", "B"],
        ["B", "A", "A"],
        ["B", "A", "B"],
        ["B", "B", "A"],
        ["B", "B", "B"],
    ]
    
    decision_chapters = [2, 4, 6]
    decision_ids = ["warrior_mirror", "warrior_fortress", "warrior_war"]
    
    for path in paths_to_test:
        adhd = {}
        ensure_hero_structure(adhd)
        
        test_equipped = {
            "Helmet": {"name": "Test Helmet", "rarity": "Legendary", "power": 250, "slot": "Helmet"},
            "Weapon": {"name": "Test Weapon", "rarity": "Legendary", "power": 250, "slot": "Weapon"},
            "Chestplate": {"name": "Test Chest", "rarity": "Legendary", "power": 250, "slot": "Chestplate"},
            "Boots": {"name": "Test Boots", "rarity": "Legendary", "power": 250, "slot": "Boots"},
            "Shield": {"name": "Test Shield", "rarity": "Legendary", "power": 250, "slot": "Shield"},
            "Gauntlets": {"name": "Test Gauntlets", "rarity": "Legendary", "power": 250, "slot": "Gauntlets"},
            "Cloak": {"name": "Test Cloak", "rarity": "Legendary", "power": 250, "slot": "Cloak"},
            "Amulet": {"name": "Test Amulet", "rarity": "Legendary", "power": 250, "slot": "Amulet"},
        }
        
        # Set equipped in both flat structure AND in hero structure
        adhd["equipped"] = test_equipped
        story_id = adhd.get("active_story", "warrior")
        if story_id in adhd.get("story_heroes", {}):
            adhd["story_heroes"][story_id]["equipped"] = test_equipped
        
        # Make decisions according to path
        for i, choice in enumerate(path):
            chapter_num = decision_chapters[i]
            make_story_decision(adhd, chapter_num, choice)
        
        path_str = "".join(path) if path else "(none)"
        decision_path = get_decision_path(adhd)
        
        print(f"Path {path_str}: decision_path='{decision_path}'")
        
        # Check Chapter 3 (variations based on first decision)
        if len(path) >= 1:
            ch3 = get_chapter_content(3, adhd)
            if ch3:
                content_preview = ch3["content"][:80].replace("\n", " ").strip()
                print(f"  Ch3 content starts: {content_preview}...")
        
        # Check Chapter 5 (variations based on first two decisions)
        if len(path) >= 2:
            # Debug: print what decisions are stored
            print(f"  Decisions stored: {adhd.get('story_decisions', {})}")
            ch5 = get_chapter_content(5, adhd)
            if ch5:
                content_preview = ch5["content"][:80].replace("\n", " ").strip()
                print(f"  Ch5 content starts: {content_preview}...")
        
        # Check Chapter 7 (endings based on all three decisions)
        if len(path) == 3:
            ch7 = get_chapter_content(7, adhd)
            if ch7:
                content_preview = ch7["content"][:80].replace("\n", " ").strip()
                print(f"  Ch7 ending: {content_preview}...")
    
    print()


def test_chapter_content_generation():
    """Test that all chapters generate content correctly."""
    print("=== CHAPTER CONTENT GENERATION ===")
    
    from gamification import calculate_character_power, sync_hero_data
    
    adhd = {}
    ensure_hero_structure(adhd)
    
    # Give enough power to unlock all chapters (need 1500+ for chapter 7)
    # 8 slots x 250 power = 2000 power
    test_equipped = {
        "Helmet": {"name": "Test Helmet", "rarity": "Legendary", "power": 250, "slot": "Helmet"},
        "Weapon": {"name": "Test Weapon", "rarity": "Legendary", "power": 250, "slot": "Weapon"},
        "Chestplate": {"name": "Test Chest", "rarity": "Legendary", "power": 250, "slot": "Chestplate"},
        "Boots": {"name": "Test Boots", "rarity": "Legendary", "power": 250, "slot": "Boots"},
        "Shield": {"name": "Test Shield", "rarity": "Legendary", "power": 250, "slot": "Shield"},
        "Gauntlets": {"name": "Test Gauntlets", "rarity": "Legendary", "power": 250, "slot": "Gauntlets"},
        "Cloak": {"name": "Test Cloak", "rarity": "Legendary", "power": 250, "slot": "Cloak"},
        "Amulet": {"name": "Test Amulet", "rarity": "Legendary", "power": 250, "slot": "Amulet"},
    }
    
    # Set equipped in both flat structure AND in hero structure
    adhd["equipped"] = test_equipped
    story_id = adhd.get("active_story", "warrior")
    if story_id in adhd.get("story_heroes", {}):
        adhd["story_heroes"][story_id]["equipped"] = test_equipped
    
    power = calculate_character_power(adhd)
    print(f"Total power: {power}")
    
    # Make all decisions (path BBB for variety)
    make_story_decision(adhd, 2, "B")
    make_story_decision(adhd, 4, "B")
    make_story_decision(adhd, 6, "B")
    
    for chapter_num in range(1, 8):
        ch = get_chapter_content(chapter_num, adhd)
        if ch:
            print(f"Chapter {chapter_num}: {ch['title']}")
            print(f"  Unlocked: {ch['unlocked']}")
            print(f"  Has decision (pending): {ch.get('has_decision', False)}")
            print(f"  Decision made: {ch.get('decision_made', False)}")
            print(f"  Content length: {len(ch['content'])} chars")
            
            # Check for placeholder issues
            if "{" in ch["content"] and "}" in ch["content"]:
                import re
                placeholders = re.findall(r'\{[a-z_]+\}', ch["content"])
                if placeholders:
                    print(f"  WARNING: Unresolved placeholders: {placeholders}")
        else:
            print(f"Chapter {chapter_num}: ERROR - No content returned!")
        print()


def test_cliffhangers():
    """Check that cliffhangers are present in chapters."""
    print("=== CLIFFHANGER CHECK ===")
    
    for i, ch in enumerate(WARRIOR_CHAPTERS):
        num = i + 1
        content = ch.get("content", "")
        
        # Check for cliffhanger markers
        has_next_time = "NEXT TIME:" in content
        has_finale = "FINALE AWAITS" in content
        has_dice = "🎲" in content
        
        if num < 7:  # Not the final chapter
            if has_next_time or has_dice:
                print(f"Chapter {num}: ✓ Has cliffhanger")
            else:
                print(f"Chapter {num}: ✗ Missing cliffhanger in main content")
        
        # Check content_after_decision
        if "content_after_decision" in ch:
            for choice, after_content in ch["content_after_decision"].items():
                has_hook = "NEXT TIME:" in after_content or "FINALE AWAITS" in after_content or "🎲" in after_content
                if has_hook:
                    print(f"Chapter {num} (after {choice}): ✓ Has cliffhanger")
                else:
                    print(f"Chapter {num} (after {choice}): ✗ Missing cliffhanger")
        
        # Check content_variations
        if "content_variations" in ch:
            for var_key, var_content in ch["content_variations"].items():
                has_hook = "NEXT TIME:" in var_content or "🎲" in var_content
                if has_hook:
                    print(f"Chapter {num} ({var_key}): ✓ Has cliffhanger")
                else:
                    print(f"Chapter {num} ({var_key}): ✗ Missing cliffhanger")
    
    print()


if __name__ == "__main__":
    test_story_structure()
    test_cliffhangers()
    test_chapter_content_generation()
    test_decision_paths()
