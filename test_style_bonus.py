#!/usr/bin/env python3
"""Test the Legendary Minimalist Style Bonus system."""

import sys
sys.path.insert(0, ".")

from gamification import (
    calculate_legendary_minimalist_bonus,
    calculate_effective_power,
    get_power_breakdown,
    LEGENDARY_MINIMALIST_BONUS,
    LEGENDARY_MINIMALIST_STYLES,
)

# All 8 valid gear slots (must match gamification.py GEAR_SLOTS)
VALID_SLOTS = ["Helmet", "Chestplate", "Gauntlets", "Boots", "Shield", "Weapon", "Cloak", "Amulet"]


def make_legendary_item(name: str) -> dict:
    """Create a legendary item."""
    return {"name": name, "rarity": "Legendary", "power": 60}


def make_common_item(name: str) -> dict:
    """Create a common item."""
    return {"name": name, "rarity": "Common", "power": 10}


def test_all_legendary_no_bonus():
    """All 8 slots filled with Legendary = NO bonus (need 1 empty)."""
    equipped = {slot: make_legendary_item(f"Legendary {slot}") for slot in VALID_SLOTS}
    result = calculate_legendary_minimalist_bonus(equipped)
    assert not result["active"], "Should NOT be active when all 8 slots filled"
    assert result["bonus"] == 0
    print("✅ All 8 Legendary → NO bonus")


def test_7_legendary_1_empty():
    """7 Legendary + 1 empty = BONUS active."""
    for empty_slot in VALID_SLOTS:
        equipped = {slot: make_legendary_item(f"Legendary {slot}") for slot in VALID_SLOTS if slot != empty_slot}
        result = calculate_legendary_minimalist_bonus(equipped)
        assert result["active"], f"Should be active with {empty_slot} empty"
        assert result["empty_slot"] == empty_slot
        assert result["bonus"] == LEGENDARY_MINIMALIST_BONUS
        expected_style = LEGENDARY_MINIMALIST_STYLES[empty_slot]
        assert result["style"]["name"] == expected_style["name"]
    print("✅ 7 Legendary + 1 empty → BONUS (all 8 slots tested)")


def test_7_legendary_1_none():
    """7 Legendary + 1 None = BONUS active."""
    equipped = {slot: make_legendary_item(f"Legendary {slot}") for slot in VALID_SLOTS}
    equipped["Helmet"] = None  # Explicitly None
    result = calculate_legendary_minimalist_bonus(equipped)
    assert result["active"], "Should be active with Helmet=None"
    assert result["empty_slot"] == "Helmet"
    assert result["style"]["name"] == "Haircut Protector"
    print("✅ 7 Legendary + 1 None → BONUS")


def test_7_legendary_1_empty_dict():
    """7 Legendary + 1 empty dict {} = BONUS active (edge case)."""
    equipped = {slot: make_legendary_item(f"Legendary {slot}") for slot in VALID_SLOTS}
    equipped["Weapon"] = {}  # Empty dict, no name
    result = calculate_legendary_minimalist_bonus(equipped)
    assert result["active"], "Should be active with Weapon={}"
    assert result["empty_slot"] == "Weapon"
    assert result["style"]["name"] == "Body Linguist"
    print("✅ 7 Legendary + 1 empty dict → BONUS")


def test_7_legendary_1_nonlegendary():
    """7 Legendary + 1 non-Legendary = NO bonus."""
    equipped = {slot: make_legendary_item(f"Legendary {slot}") for slot in VALID_SLOTS}
    equipped["Shield"] = make_common_item("Common Shield")
    result = calculate_legendary_minimalist_bonus(equipped)
    assert not result["active"], "Should NOT be active with a non-Legendary item"
    assert result["bonus"] == 0
    print("✅ 7 Legendary + 1 Common → NO bonus")


def test_6_legendary_2_empty():
    """6 Legendary + 2 empty = NO bonus (need exactly 1 empty)."""
    equipped = {slot: make_legendary_item(f"Legendary {slot}") for slot in VALID_SLOTS}
    equipped["Helmet"] = None
    equipped["Boots"] = None
    result = calculate_legendary_minimalist_bonus(equipped)
    assert not result["active"], "Should NOT be active with 2 empty slots"
    assert result["bonus"] == 0
    print("✅ 6 Legendary + 2 empty → NO bonus")


def test_item_with_none_rarity():
    """Item with rarity=None counts as non-legendary."""
    equipped = {slot: make_legendary_item(f"Legendary {slot}") for slot in VALID_SLOTS}
    equipped["Gauntlets"] = {"name": "Weird Item", "rarity": None, "power": 30}
    result = calculate_legendary_minimalist_bonus(equipped)
    assert not result["active"], "Item with rarity=None should be non-legendary"
    print("✅ Item with rarity=None → NO bonus")


def test_effective_power_includes_style():
    """calculate_effective_power includes style bonus."""
    equipped = {slot: make_legendary_item(f"Legendary {slot}") for slot in VALID_SLOTS}
    equipped.pop("Cloak")  # Remove one slot
    result = calculate_effective_power(equipped)
    assert result["style_bonus"] == LEGENDARY_MINIMALIST_BONUS
    assert result["style_info"]["active"]
    assert result["style_info"]["style"]["name"] == "Rear View Legend"
    print("✅ calculate_effective_power includes style bonus")


def test_power_breakdown_includes_style():
    """get_power_breakdown includes style_bonus and style_info."""
    equipped = {slot: make_legendary_item(f"Legendary {slot}") for slot in VALID_SLOTS}
    equipped.pop("Amulet")  # Remove one slot
    adhd_buster = {"equipped": equipped}  # Wrap in adhd_buster dict
    breakdown = get_power_breakdown(adhd_buster)
    assert "style_bonus" in breakdown
    assert breakdown["style_bonus"] == LEGENDARY_MINIMALIST_BONUS
    assert breakdown["style_info"]["style"]["name"] == "Anti-Decorator"
    print("✅ get_power_breakdown includes style bonus")


def test_empty_equipped():
    """Empty equipped dict = NO bonus."""
    result = calculate_legendary_minimalist_bonus({})
    assert not result["active"]
    assert result["bonus"] == 0
    print("✅ Empty equipped → NO bonus")


def main():
    print("\n🧪 LEGENDARY MINIMALIST STYLE BONUS TESTS\n")
    print(f"Slots: {VALID_SLOTS}")
    print(f"Bonus: +{LEGENDARY_MINIMALIST_BONUS} power")
    print(f"Styles: {list(LEGENDARY_MINIMALIST_STYLES.keys())}")
    print()
    
    test_all_legendary_no_bonus()
    test_7_legendary_1_empty()
    test_7_legendary_1_none()
    test_7_legendary_1_empty_dict()
    test_7_legendary_1_nonlegendary()
    test_6_legendary_2_empty()
    test_item_with_none_rarity()
    test_effective_power_includes_style()
    test_power_breakdown_includes_style()
    test_empty_equipped()
    
    print("\n🎉 ALL TESTS PASSED!\n")


if __name__ == "__main__":
    main()
