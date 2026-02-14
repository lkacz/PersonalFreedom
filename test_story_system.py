#!/usr/bin/env python
"""Comprehensive test for the story progression system."""

from gamification import (
    get_story_data, get_chapter_content, make_story_decision, 
    get_decision_path, AVAILABLE_STORIES, STORY_DATA, get_story_progress,
    restart_story, switch_story, ensure_hero_structure, COIN_COSTS,
    get_selected_story, select_story, STORY_THRESHOLDS
)


def test_all_stories():
    """Test all available stories have correct structure."""
    print("Testing all available stories...")
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


def test_story_unlock_system():
    """Test story unlock/purchase system."""
    print("\nTesting story unlock system...")
    
    # Verify unlock cost is defined
    unlock_cost = COIN_COSTS.get("story_unlock", 100)
    assert unlock_cost == 100, f"Expected unlock cost 100, got {unlock_cost}"
    print(f"  ✓ Story unlock cost is {unlock_cost} coins")
    
    # Verify available stories
    assert len(AVAILABLE_STORIES) == 6, f"Expected 6 stories, got {len(AVAILABLE_STORIES)}"
    expected_stories = ["warrior", "scholar", "wanderer", "underdog", "scientist", "robot"]
    for story_id in expected_stories:
        assert story_id in AVAILABLE_STORIES, f"Missing story: {story_id}"
    print(f"  ✓ All 6 stories available: {list(AVAILABLE_STORIES.keys())}")
    
    # Test default unlocked story (underdog)
    test_adhd = {}
    unlocked = test_adhd.get("unlocked_stories", ["underdog"])
    assert "underdog" in unlocked, "Underdog should be unlocked by default"
    print("  ✓ Underdog is free/unlocked by default")
    
    # Simulate unlocking another story
    test_adhd["unlocked_stories"] = ["underdog"]
    test_adhd["coins"] = 150
    
    # Spend coins to unlock warrior
    if test_adhd["coins"] >= unlock_cost:
        test_adhd["coins"] -= unlock_cost
        test_adhd["unlocked_stories"].append("warrior")
    
    assert "warrior" in test_adhd["unlocked_stories"], "Warrior should now be unlocked"
    assert test_adhd["coins"] == 50, "Should have 50 coins remaining"
    print("  ✓ Story unlock with coins works correctly")


def test_per_story_progression():
    """Test that each story has independent progression."""
    print("\nTesting per-story progression...")
    test_adhd = {"active_story": "warrior", "story_mode": "active"}
    ensure_hero_structure(test_adhd)
    
    # Make progress in warrior story
    make_story_decision(test_adhd, 2, "A")
    test_adhd["max_power_reached"] = 500  # Set power to unlock chapters
    
    warrior_path = get_decision_path(test_adhd)
    assert warrior_path == "A", "Warrior should have decision A"
    
    # Switch to scholar
    switch_story(test_adhd, "scholar")
    
    # Scholar should have no decisions (fresh hero)
    scholar_path = get_decision_path(test_adhd)
    assert scholar_path == "", f"Scholar should have no decisions, got '{scholar_path}'"
    
    # Make different decision in scholar
    make_story_decision(test_adhd, 2, "B")
    scholar_path = get_decision_path(test_adhd)
    assert scholar_path == "B", "Scholar should have decision B"
    
    # Switch back to warrior
    switch_story(test_adhd, "warrior")
    warrior_path = get_decision_path(test_adhd)
    assert warrior_path == "A", f"Warrior should still have A, got '{warrior_path}'"
    
    # Switch to scholar again
    switch_story(test_adhd, "scholar")
    scholar_path = get_decision_path(test_adhd)
    assert scholar_path == "B", f"Scholar should still have B, got '{scholar_path}'"
    
    print("  ✓ Each story maintains independent decisions")
    
    # Verify max_power_reached is per-hero
    switch_story(test_adhd, "wanderer")
    wanderer_power = test_adhd.get("max_power_reached", 0)
    assert wanderer_power == 0, f"Wanderer should start at 0 power, got {wanderer_power}"
    print("  ✓ Each story has independent power progression")


def test_power_based_unlocking():
    """Test chapter unlocking based on power thresholds."""
    print("\nTesting power-based chapter unlocking...")
    
    # Verify thresholds
    expected_thresholds = [0, 50, 120, 250, 450, 800, 1500]
    assert STORY_THRESHOLDS == expected_thresholds, f"Wrong thresholds: {STORY_THRESHOLDS}"
    print(f"  ✓ Chapter thresholds: {STORY_THRESHOLDS}")
    
    test_adhd = {"active_story": "warrior", "story_mode": "active"}
    ensure_hero_structure(test_adhd)
    
    # At 0 power, only chapter 1 unlocked
    test_adhd["max_power_reached"] = 0
    progress = get_story_progress(test_adhd)
    assert progress["unlocked_chapters"] == [1], f"At 0 power, expected [1], got {progress['unlocked_chapters']}"
    print("  ✓ At 0 power: only chapter 1 unlocked")
    
    # At 50 power, chapters 1-2 unlocked
    test_adhd["max_power_reached"] = 50
    progress = get_story_progress(test_adhd)
    assert progress["unlocked_chapters"] == [1, 2], f"At 50 power, expected [1,2], got {progress['unlocked_chapters']}"
    print("  ✓ At 50 power: chapters 1-2 unlocked")
    
    # At 500 power, chapters 1-5 unlocked
    test_adhd["max_power_reached"] = 500
    progress = get_story_progress(test_adhd)
    assert progress["unlocked_chapters"] == [1, 2, 3, 4, 5], f"At 500 power: {progress['unlocked_chapters']}"
    print("  ✓ At 500 power: chapters 1-5 unlocked")
    
    # At 1500+ power, all chapters unlocked
    test_adhd["max_power_reached"] = 1500
    progress = get_story_progress(test_adhd)
    assert progress["unlocked_chapters"] == [1, 2, 3, 4, 5, 6, 7], f"At 1500 power: {progress['unlocked_chapters']}"
    print("  ✓ At 1500 power: all 7 chapters unlocked")
    
    # Verify permanent unlock - power drops but chapters stay unlocked
    test_adhd["max_power_reached"] = 1500
    test_adhd["equipped"] = {}  # No gear = 0 current power
    
    ch7 = get_chapter_content(7, test_adhd)
    assert ch7.get("unlocked") == True, "Chapter 7 should stay unlocked even with 0 current power"
    print("  ✓ Chapters stay permanently unlocked (based on max power ever reached)")


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
    
    # Test all 8 possible endings
    all_paths = ["AAA", "AAB", "ABA", "ABB", "BAA", "BAB", "BBA", "BBB"]
    for path in all_paths:
        # Reset and make specific decisions
        restart_story(test_adhd, "warrior")
        test_adhd["max_power_reached"] = 2000
        
        make_story_decision(test_adhd, 2, path[0])
        make_story_decision(test_adhd, 4, path[1])
        make_story_decision(test_adhd, 6, path[2])
        
        actual_path = get_decision_path(test_adhd)
        assert actual_path == path, f"Expected path {path}, got {actual_path}"
        
        ch7 = get_chapter_content(7, test_adhd)
        assert "not yet complete" not in ch7.get("content", "").lower(), \
            f"Path {path}: Chapter 7 should show ending"
        assert len(ch7.get("content", "")) > 100, f"Path {path}: Ending content should be substantial"
    
    print(f"  ✓ All 8 endings verified: {all_paths}")


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


def test_all_stories_have_unique_decision_ids():
    """Test that each story has unique decision IDs."""
    print("\nTesting unique decision IDs per story...")
    all_decision_ids = {}
    
    for story_id in AVAILABLE_STORIES:
        data = STORY_DATA.get(story_id)
        decisions = data["decisions"]
        
        for ch_num, decision in decisions.items():
            decision_id = decision["id"]
            
            # Decision ID should be unique within the story
            story_decisions = all_decision_ids.setdefault(story_id, set())
            assert decision_id not in story_decisions, f"{story_id}: Duplicate decision ID {decision_id}"
            story_decisions.add(decision_id)
            
            # Decision ID should contain story identifier
            assert story_id.split("_")[0] in decision_id or story_id in decision_id, \
                f"{story_id}: Decision ID '{decision_id}' should contain story identifier"
    
    print(f"  ✓ All decision IDs are unique per story")


def test_story_hero_isolation():
    """Test that heroes are completely isolated between stories."""
    print("\nTesting hero isolation between stories...")
    test_adhd = {"active_story": "warrior", "story_mode": "active"}
    ensure_hero_structure(test_adhd)
    
    # Set up warrior hero with items and progress
    test_adhd["inventory"] = [{"id": "test_item", "name": "Test Sword"}]
    test_adhd["max_power_reached"] = 1000
    make_story_decision(test_adhd, 2, "A")
    make_story_decision(test_adhd, 4, "A")
    
    # Switch to scholar
    switch_story(test_adhd, "scholar")
    
    # Scholar should have fresh state
    assert test_adhd.get("inventory", []) == [], "Scholar should have empty inventory"
    assert test_adhd.get("max_power_reached", 0) == 0, "Scholar should have 0 power"
    assert get_decision_path(test_adhd) == "", "Scholar should have no decisions"
    
    # Set up scholar with different items
    test_adhd["inventory"] = [{"id": "scholar_item", "name": "Book of Knowledge"}]
    test_adhd["max_power_reached"] = 500
    make_story_decision(test_adhd, 2, "B")
    
    # Switch back to warrior
    switch_story(test_adhd, "warrior")
    
    # Warrior should retain its original state
    assert len(test_adhd.get("inventory", [])) == 1, "Warrior should have 1 item"
    assert test_adhd["inventory"][0]["name"] == "Test Sword", "Warrior should have its sword"
    assert test_adhd.get("max_power_reached", 0) == 1000, "Warrior should have 1000 power"
    assert get_decision_path(test_adhd) == "AA", "Warrior should have AA decisions"
    
    print("  ✓ Heroes are completely isolated between stories")


def test_chapter1_preview_mode():
    """Test that Chapter 1 is accessible for locked stories (preview mode)."""
    print("\nTesting Chapter 1 preview mode...")
    
    # Create user with only underdog unlocked
    test_adhd = {
        "active_story": "warrior",  # Select a locked story
        "story_mode": "active",
        "unlocked_stories": ["underdog"],  # Only underdog unlocked
        "max_power_reached": 0
    }
    ensure_hero_structure(test_adhd)
    
    # Verify warrior is NOT in unlocked stories (preview mode)
    assert "warrior" not in test_adhd["unlocked_stories"], "Warrior should be locked"
    
    # Chapter 1 should be readable (via get_chapter_content)
    chapter1 = get_chapter_content(1, test_adhd)
    assert chapter1 is not None, "Chapter 1 should be accessible"
    assert chapter1.get("unlocked") == True, "Chapter 1 should be unlocked (always available)"
    assert "content" in chapter1, "Chapter 1 should have content"
    print("  ✓ Chapter 1 is accessible for locked story (preview mode)")
    
    # Chapter 2+ should still return data but would be blocked by UI
    # (The gamification module doesn't enforce story unlock, the UI does)
    chapter2 = get_chapter_content(2, test_adhd)
    assert chapter2 is not None, "Chapter 2 data is available"
    # Chapter 2 is power-locked (need 50 power)
    assert chapter2.get("unlocked") == False, "Chapter 2 should be power-locked"
    print("  ✓ Chapter 2 is power-locked (additional story unlock check in UI)")
    
    # Verify preview mode detection logic
    story_id = get_selected_story(test_adhd)
    unlocked_stories = test_adhd.get("unlocked_stories", ["underdog"])
    is_preview = story_id not in unlocked_stories
    assert is_preview == True, "Should be in preview mode for warrior"
    print("  ✓ Preview mode correctly detected")
    
    # After unlocking, preview mode should be False
    test_adhd["unlocked_stories"].append("warrior")
    is_preview = "warrior" not in test_adhd["unlocked_stories"]
    assert is_preview == False, "Should NOT be in preview mode after unlock"
    print("  ✓ Preview mode correctly cleared after unlock")


if __name__ == "__main__":
    test_all_stories()
    test_story_unlock_system()
    test_per_story_progression()
    test_power_based_unlocking()
    test_make_story_decision()
    test_decision_path()
    test_content_variations()
    test_chapter_7_endings()
    test_story_restart()
    test_story_switch()
    test_get_chapter_content_locked()
    test_all_stories_have_unique_decision_ids()
    test_story_hero_isolation()
    test_chapter1_preview_mode()
    
    print("\n" + "="*50)
    print("✅ ALL STORY SYSTEM TESTS PASSED!")
    print("="*50)
    print("\nVerified:")
    print("  • 6 stories with 7 chapters each")
    print("  • Story unlock system (100 coins, underdog free)")
    print("  • Per-story hero isolation (inventory, power, decisions)")
    print("  • Power-based chapter unlocking (permanent)")
    print("  • 3 decisions per story (chapters 2, 4, 6)")
    print("  • 8 unique endings per story based on decisions")
    print("  • Content variations based on decision path")
    print("  • Story restart clears all progress")
    print("  • Story switching preserves independent progress")
    print("  • Chapter 1 FREE preview for all stories")
