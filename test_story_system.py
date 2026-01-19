#!/usr/bin/env python
"""Comprehensive test for the story progression system."""

from gamification import (
    get_story_data, get_chapter_content, make_story_decision, 
    get_decision_path, AVAILABLE_STORIES, STORY_DATA, get_story_progress,
    restart_story, switch_story, ensure_hero_structure
)


def test_all_stories():
    """Test all 5 stories have correct structure."""
    print("Testing all 5 stories...")
    for story_id in AVAILABLE_STORIES:
        data = STORY_DATA.get(story_id)
        decisions = data["decisions"]
        chapters = data["chapters"]
        
        # Verify 7 chapters
        assert len(chapters) == 7, f"{story_id}: Expected 7 chapters, got {len(chapters)}"
        
        # Verify decisions at chapters 2, 4, 6
        for ch in [2, 4, 6]:
            assert ch in decisions, f"{story_id}: Missing decision for chapter {ch}"
            d = decisions[ch]
            assert "id" in d, f"{story_id} ch{ch}: Missing decision id"
            assert "prompt" in d, f"{story_id} ch{ch}: Missing prompt"
            assert "choices" in d, f"{story_id} ch{ch}: Missing choices"
            assert "A" in d["choices"] and "B" in d["choices"], f"{story_id} ch{ch}: Missing A or B choice"
        
        # Verify chapters 2, 4, 6 have has_decision: True
        for ch_num in [2, 4, 6]:
            assert chapters[ch_num - 1].get("has_decision") == True, f"{story_id} ch{ch_num}: has_decision should be True"
        
        # Verify chapters 3, 5 have content_variations
        for ch_num in [3, 5]:
            assert "content_variations" in chapters[ch_num - 1], f"{story_id} ch{ch_num}: Missing content_variations"
        
        # Verify chapter 7 has endings
        assert "endings" in chapters[6], f"{story_id} ch7: Missing endings"
        endings = chapters[6]["endings"]
        expected_endings = ["AAA", "AAB", "ABA", "ABB", "BAA", "BAB", "BBA", "BBB"]
        for ending in expected_endings:
            assert ending in endings, f"{story_id} ch7: Missing ending {ending}"
        
        print(f"  ✓ {story_id}: All checks passed")


def test_make_story_decision():
    """Test make_story_decision returns correct dict structure."""
    print("\nTesting make_story_decision...")
    test_adhd = {"active_story": "warrior", "story_mode": "active"}
    ensure_hero_structure(test_adhd)
    
    result = make_story_decision(test_adhd, 2, "A")
    assert isinstance(result, dict), "make_story_decision should return dict"
    assert result.get("success") == True, "Decision should succeed"
    assert "choice_label" in result, "Result should have choice_label"
    assert "outcome" in result, "Result should have outcome"
    assert "story_id" in result, "Result should have story_id"
    print("  ✓ make_story_decision returns correct dict structure")
    
    # Test invalid choice
    result2 = make_story_decision(test_adhd, 2, "C")
    assert result2.get("success") == False, "Invalid choice should fail"
    assert "error" in result2, "Should have error message"
    print("  ✓ Invalid choice correctly rejected")
    
    # Test decision at non-decision chapter
    result3 = make_story_decision(test_adhd, 1, "A")
    assert result3.get("success") == False, "Non-decision chapter should fail"
    print("  ✓ Non-decision chapter correctly rejected")


def test_decision_path():
    """Test decision path tracking."""
    print("\nTesting decision path...")
    test_adhd = {"active_story": "warrior", "story_mode": "active"}
    ensure_hero_structure(test_adhd)
    
    # Initially empty
    path = get_decision_path(test_adhd)
    assert path == "", f'Expected empty path, got "{path}"'
    
    # Make decisions
    make_story_decision(test_adhd, 2, "A")
    path = get_decision_path(test_adhd)
    assert path == "A", f'Expected path "A", got "{path}"'
    
    make_story_decision(test_adhd, 4, "B")
    path = get_decision_path(test_adhd)
    assert path == "AB", f'Expected path "AB", got "{path}"'
    
    make_story_decision(test_adhd, 6, "A")
    path = get_decision_path(test_adhd)
    assert path == "ABA", f'Expected path "ABA", got "{path}"'
    
    print("  ✓ Decision path correctly tracked")


def test_content_variations():
    """Test content variations based on decisions."""
    print("\nTesting content variations...")
    test_adhd = {"active_story": "warrior", "story_mode": "active", "max_power_reached": 500}
    ensure_hero_structure(test_adhd)
    
    # Make decision at chapter 2
    make_story_decision(test_adhd, 2, "A")
    
    # Chapter 3 should use "A" variation
    ch3 = get_chapter_content(3, test_adhd)
    assert ch3 is not None, "Chapter 3 should exist"
    assert ch3.get("unlocked") == True, "Chapter 3 should be unlocked"
    assert "content" in ch3, "Chapter 3 should have content"
    print("  ✓ Content variations work for chapter 3")
    
    # Make decision at chapter 4
    make_story_decision(test_adhd, 4, "B")
    
    # Chapter 5 should use "AB" variation
    ch5 = get_chapter_content(5, test_adhd)
    assert ch5 is not None, "Chapter 5 should exist"
    assert "content" in ch5, "Chapter 5 should have content"
    print("  ✓ Content variations work for chapter 5")


def test_chapter_7_endings():
    """Test chapter 7 has correct ending based on all 3 decisions."""
    print("\nTesting chapter 7 endings...")
    test_adhd = {"active_story": "warrior", "story_mode": "active", "max_power_reached": 2000}
    ensure_hero_structure(test_adhd)
    
    # Before 3 decisions, chapter 7 should say "not complete"
    ch7 = get_chapter_content(7, test_adhd)
    assert "not yet complete" in ch7.get("content", "").lower() or "not made all" in ch7.get("content", "").lower(), \
        "Chapter 7 should show incomplete message before 3 decisions"
    print("  ✓ Chapter 7 shows incomplete message without 3 decisions")
    
    # Make all 3 decisions
    make_story_decision(test_adhd, 2, "B")
    make_story_decision(test_adhd, 4, "B")
    make_story_decision(test_adhd, 6, "B")
    
    path = get_decision_path(test_adhd)
    assert path == "BBB", f'Expected path "BBB", got "{path}"'
    
    ch7 = get_chapter_content(7, test_adhd)
    assert "not yet complete" not in ch7.get("content", "").lower(), \
        "Chapter 7 should show ending after 3 decisions"
    print("  ✓ Chapter 7 shows correct ending after 3 decisions")


def test_story_restart():
    """Test story restart clears decisions."""
    print("\nTesting story restart...")
    test_adhd = {"active_story": "warrior", "story_mode": "active"}
    ensure_hero_structure(test_adhd)
    
    # Make a decision
    make_story_decision(test_adhd, 2, "A")
    path = get_decision_path(test_adhd)
    assert path == "A", "Decision should be recorded"
    
    # Restart story
    result = restart_story(test_adhd, "warrior")
    assert result == True, "Restart should succeed"
    
    # Decision should be cleared
    path = get_decision_path(test_adhd)
    assert path == "", f'Expected empty path after restart, got "{path}"'
    print("  ✓ Story restart clears decisions")


def test_story_switch():
    """Test switching stories preserves each story's decisions."""
    print("\nTesting story switching...")
    test_adhd = {"active_story": "warrior", "story_mode": "active"}
    ensure_hero_structure(test_adhd)
    
    # Make decision in warrior story
    make_story_decision(test_adhd, 2, "A")
    warrior_path = get_decision_path(test_adhd)
    assert warrior_path == "A", "Warrior decision should be recorded"
    
    # Switch to scholar story
    switch_story(test_adhd, "scholar")
    
    # Scholar should have no decisions
    scholar_path = get_decision_path(test_adhd)
    assert scholar_path == "", f'Scholar should have empty path, got "{scholar_path}"'
    
    # Make decision in scholar story
    make_story_decision(test_adhd, 2, "B")
    scholar_path = get_decision_path(test_adhd)
    assert scholar_path == "B", "Scholar decision should be recorded"
    
    # Switch back to warrior
    switch_story(test_adhd, "warrior")
    
    # Warrior should still have its decision
    warrior_path = get_decision_path(test_adhd)
    assert warrior_path == "A", f'Warrior should still have path "A", got "{warrior_path}"'
    
    print("  ✓ Story switching preserves each story's decisions")


def test_get_chapter_content_locked():
    """Test get_chapter_content returns locked info for locked chapters."""
    print("\nTesting locked chapter handling...")
    test_adhd = {"active_story": "warrior", "story_mode": "active", "max_power_reached": 0}
    ensure_hero_structure(test_adhd)
    
    # Chapter 2 requires 50 power
    ch2 = get_chapter_content(2, test_adhd)
    assert ch2.get("unlocked") == False, "Chapter 2 should be locked"
    assert "power_needed" in ch2, "Should show power needed"
    assert ch2.get("power_needed") == 50, "Should need 50 power"
    print("  ✓ Locked chapters show correct info")


if __name__ == "__main__":
    test_all_stories()
    test_make_story_decision()
    test_decision_path()
    test_content_variations()
    test_chapter_7_endings()
    test_story_restart()
    test_story_switch()
    test_get_chapter_content_locked()
    
    print("\n" + "="*50)
    print("✅ ALL STORY SYSTEM TESTS PASSED!")
    print("="*50)
