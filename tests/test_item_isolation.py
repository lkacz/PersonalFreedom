"""
Comprehensive tests for item isolation and deep copy behavior.
Tests ensure external code cannot mutate internal game state through references.
"""
import pytest
from datetime import datetime


class MockBlocker:
    """Mock blocker for testing GameStateManager."""
    def __init__(self):
        self.adhd_buster = {
            "inventory": [],
            "equipped": {},
            "coins": 100,
            "total_collected": 0
        }
    
    def save_config(self):
        """Mock save - does nothing."""
        pass


@pytest.fixture
def game_state():
    """Create a fresh GameStateManager instance for each test."""
    from game_state import GameStateManager, reset_game_state
    reset_game_state()
    blocker = MockBlocker()
    gs = GameStateManager(blocker)
    return gs


def test_add_item_deep_copy_isolation(game_state):
    """Test that add_item deep copies items to prevent external mutation."""
    # Create an item with nested structure
    original_item = {
        "name": "Test Sword",
        "slot": "Weapon",
        "rarity": "Rare",
        "power": 50,
        "lucky_options": {
            "coin_bonus": 10,
            "xp_bonus": 5
        },
        "obtained_at": datetime.now().isoformat()
    }
    
    # Add item to inventory
    game_state.add_item(original_item)
    
    # Mutate the original item (both shallow and deep properties)
    original_item["power"] = 999
    original_item["lucky_options"]["coin_bonus"] = 9999
    original_item["lucky_options"]["new_bonus"] = 42
    
    # Verify inventory item was NOT affected
    inventory = game_state.adhd_buster["inventory"]
    assert len(inventory) == 1
    stored_item = inventory[0]
    
    assert stored_item["power"] == 50, "Shallow property was mutated!"
    assert stored_item["lucky_options"]["coin_bonus"] == 10, "Nested property was mutated!"
    assert "new_bonus" not in stored_item["lucky_options"], "New key leaked into stored item!"


def test_equip_item_deep_copy_isolation(game_state):
    """Test that equip_item deep copies items to prevent external mutation."""
    # Create an item with nested structure
    original_item = {
        "name": "Test Helmet",
        "slot": "Helmet",
        "rarity": "Epic",
        "power": 75,
        "neighbor_effect": {
            "type": "friendly",
            "target": "power",
            "multiplier": 1.15
        },
        "obtained_at": datetime.now().isoformat()
    }
    
    # Equip the item
    game_state.equip_item("Helmet", original_item)
    
    # Mutate the original item
    original_item["power"] = 999
    original_item["neighbor_effect"]["multiplier"] = 9.99
    original_item["neighbor_effect"]["new_field"] = "exploit"
    
    # Verify equipped item was NOT affected
    equipped = game_state.adhd_buster["equipped"]
    assert "Helmet" in equipped
    stored_item = equipped["Helmet"]
    
    assert stored_item["power"] == 75, "Shallow property was mutated!"
    assert stored_item["neighbor_effect"]["multiplier"] == 1.15, "Nested property was mutated!"
    assert "new_field" not in stored_item["neighbor_effect"], "New key leaked into stored item!"


def test_award_items_batch_no_duplication(game_state):
    """Test that award_items_batch properly adds all items to inventory and auto-equips to empty slots.
    
    Design: All awarded items go to inventory. Auto-equip sets the equipped slot
    to reference the item in inventory. Items are always in inventory.
    """
    # Create items for all equipment slots
    items_to_award = [
        {"name": "Auto Helmet", "slot": "Helmet", "rarity": "Common", "power": 10},
        {"name": "Auto Sword", "slot": "Weapon", "rarity": "Common", "power": 15},
        {"name": "Spare Helmet", "slot": "Helmet", "rarity": "Uncommon", "power": 20},
    ]
    
    # Award items with auto_equip=True
    result = game_state.award_items_batch(items_to_award, auto_equip=True)
    
    # Verify results
    inventory = game_state.adhd_buster["inventory"]
    equipped = game_state.adhd_buster["equipped"]
    
    # First helmet and sword should be equipped (empty slots)
    assert "Helmet" in equipped
    assert equipped["Helmet"]["name"] == "Auto Helmet"
    assert "Weapon" in equipped
    assert equipped["Weapon"]["name"] == "Auto Sword"
    
    # ALL items should be in inventory (equipped items stay in inventory)
    assert len(inventory) == 3
    inventory_names = {item["name"] for item in inventory}
    assert inventory_names == {"Auto Helmet", "Auto Sword", "Spare Helmet"}
    
    # Verify return values are correct
    assert len(result["equipped"]) == 2, "Should report 2 equipped items"
    assert len(result["items"]) == 3, "Should report 3 items added to inventory"


def test_award_items_batch_deep_copy_isolation(game_state):
    """Test that award_items_batch deep copies all items."""
    # Create items with nested structures
    original_items = [
        {
            "name": "Batch Armor",
            "slot": "Chestplate",
            "rarity": "Rare",
            "power": 60,
            "lucky_options": {"coin_bonus": 15},
            "obtained_at": datetime.now().isoformat()
        },
        {
            "name": "Batch Boots",
            "slot": "Boots",
            "rarity": "Common",
            "power": 20,
            "obtained_at": datetime.now().isoformat()
        }
    ]
    
    # Award items
    game_state.award_items_batch(original_items, auto_equip=True)
    
    # Mutate original items
    original_items[0]["power"] = 999
    original_items[0]["lucky_options"]["coin_bonus"] = 9999
    original_items[1]["power"] = 888
    
    # Verify equipped items were NOT affected
    equipped = game_state.adhd_buster["equipped"]
    assert equipped["Chestplate"]["power"] == 60, "Equipped item was mutated!"
    assert equipped["Chestplate"]["lucky_options"]["coin_bonus"] == 15, "Nested property was mutated!"
    assert equipped["Boots"]["power"] == 20, "Equipped item was mutated!"


def test_swap_equipped_item_isolation(game_state):
    """Test that swap_equipped_item maintains isolation between inventory and equipped.
    
    Design: Items stay in inventory when equipped. Equipped dict holds a deep copy
    to prevent mutation of inventory items via equipped references.
    """
    # Add item to inventory
    inventory_item = {
        "name": "Swap Test Item",
        "slot": "Weapon",
        "rarity": "Epic",
        "power": 100,
        "lucky_options": {"xp_bonus": 20},
        "obtained_at": datetime.now().isoformat()
    }
    game_state.add_item(inventory_item)
    
    # Get the item from inventory (this is a reference to the stored copy)
    inventory = game_state.adhd_buster["inventory"]
    stored_ref = inventory[0]
    
    # Equip it via swap (item stays in inventory, equipped gets a deep copy)
    result = game_state.swap_equipped_item("Weapon", stored_ref)
    
    # Item should STILL be in inventory (equipped items stay in inventory)
    assert len(game_state.adhd_buster["inventory"]) == 1, f"Item should stay in inventory after equipping. Inventory: {game_state.adhd_buster['inventory']}"
    
    # Verify item is in equipped
    equipped = game_state.adhd_buster["equipped"]
    assert "Weapon" in equipped
    assert equipped["Weapon"]["name"] == "Swap Test Item"
    
    # Mutate the original reference we passed to swap
    stored_ref["power"] = 999
    stored_ref["lucky_options"]["xp_bonus"] = 9999
    
    # Verify equipped item was NOT affected (deep copy protection)
    assert equipped["Weapon"]["power"] == 100, "Equipped item was mutated via old reference!"
    assert equipped["Weapon"]["lucky_options"]["xp_bonus"] == 20, "Nested property was mutated!"


def test_no_duplication_exploit_via_unequip_reequip(game_state):
    """Test that unequip->equip cycle maintains a single item in inventory.
    
    Design: All items are in inventory. Equip/unequip just updates the equipped dict.
    """
    # Award an item with auto-equip
    item = {"name": "Test Item", "slot": "Helmet", "rarity": "Rare", "power": 50}
    game_state.award_items_batch([item], auto_equip=True)
    
    # Verify initial state: 1 in equipped, 1 in inventory (item is in both)
    assert "Helmet" in game_state.adhd_buster["equipped"]
    assert len(game_state.adhd_buster["inventory"]) == 1
    
    # Unequip the item (item stays in inventory, just removed from equipped)
    unequipped = game_state.unequip_item("Helmet")
    assert unequipped is not None
    assert len(game_state.adhd_buster["inventory"]) == 1  # Still 1 in inventory
    assert "Helmet" not in game_state.adhd_buster["equipped"]
    
    # Re-equip via swap (item stays in inventory, equipped is updated)
    inv_item = game_state.adhd_buster["inventory"][0]
    game_state.swap_equipped_item("Helmet", inv_item)
    
    # Verify final state: 1 in equipped, 1 in inventory (same item, no duplication)
    assert "Helmet" in game_state.adhd_buster["equipped"]
    assert len(game_state.adhd_buster["inventory"]) == 1
    
    # CRITICAL: Only 1 unique item in system (in inventory, referenced by equipped)
    assert game_state.adhd_buster["inventory"][0]["name"] == "Test Item"
    assert game_state.adhd_buster["equipped"]["Helmet"]["name"] == "Test Item"


def test_award_items_batch_auto_equip_false(game_state):
    """Test that award_items_batch with auto_equip=False adds all items to inventory."""
    items = [
        {"name": "Item 1", "slot": "Helmet", "rarity": "Common", "power": 10},
        {"name": "Item 2", "slot": "Weapon", "rarity": "Rare", "power": 30},
    ]
    
    # Award with auto_equip=False
    result = game_state.award_items_batch(items, auto_equip=False)
    
    # All items should be in inventory
    inventory = game_state.adhd_buster["inventory"]
    assert len(inventory) == 2
    
    # No items should be equipped
    equipped = game_state.adhd_buster["equipped"]
    assert len(equipped) == 0
    
    # Result should reflect this
    assert len(result["items"]) == 2
    assert len(result["equipped"]) == 0


def test_multiple_items_same_slot_with_auto_equip(game_state):
    """Test handling of multiple items for the same slot with auto-equip.
    
    Design: All items go to inventory. Only first item for empty slot is auto-equipped.
    """
    items = [
        {"name": "Helmet 1", "slot": "Helmet", "rarity": "Common", "power": 10},
        {"name": "Helmet 2", "slot": "Helmet", "rarity": "Rare", "power": 30},
        {"name": "Helmet 3", "slot": "Helmet", "rarity": "Epic", "power": 50},
    ]
    
    # Award with auto_equip=True
    result = game_state.award_items_batch(items, auto_equip=True)
    
    # First helmet should be equipped
    equipped = game_state.adhd_buster["equipped"]
    assert "Helmet" in equipped
    assert equipped["Helmet"]["name"] == "Helmet 1"
    
    # ALL helmets should be in inventory (equipped items stay in inventory)
    inventory = game_state.adhd_buster["inventory"]
    assert len(inventory) == 3
    helmet_names = {item["name"] for item in inventory}
    assert helmet_names == {"Helmet 1", "Helmet 2", "Helmet 3"}
    
    # Verify counts
    assert len(result["equipped"]) == 1
    assert len(result["items"]) == 3


def test_unequip_item_deep_copy_isolation(game_state):
    """Test that unequip_item uses deep copy to prevent reference leaks.
    
    Design: Items are always in inventory. Unequip just removes from equipped dict.
    The returned item is a deep copy for safety.
    """
    # Award and auto-equip an item with nested properties
    item = {
        "name": "Test Helmet",
        "slot": "Helmet",
        "rarity": "Epic",
        "power": 150,
        "lucky_options": {"coin_bonus": 10, "xp_bonus": 5}
    }
    game_state.award_items_batch([item], auto_equip=True)
    
    # Verify it's equipped AND in inventory
    assert "Helmet" in game_state.adhd_buster["equipped"]
    assert len(game_state.adhd_buster["inventory"]) == 1
    equipped_item = game_state.adhd_buster["equipped"]["Helmet"]
    
    # Unequip and get the returned value
    returned_item = game_state.unequip_item("Helmet")
    
    # Verify it's no longer equipped but still in inventory
    assert "Helmet" not in game_state.adhd_buster["equipped"]
    assert len(game_state.adhd_buster["inventory"]) == 1  # Still 1 item
    inventory_item = game_state.adhd_buster["inventory"][0]
    
    # Test 1: Mutating the returned item should NOT affect inventory
    if returned_item:
        returned_item["power"] = 9999
        returned_item["lucky_options"]["coin_bonus"] = 9999
        
        assert inventory_item["power"] == 150, "Inventory item was mutated via returned reference!"
        assert inventory_item["lucky_options"]["coin_bonus"] == 10, "Nested property was mutated!"
    
    # Test 2: Mutating the original equipped reference should NOT affect inventory
    equipped_item["power"] = 8888
    equipped_item["lucky_options"]["xp_bonus"] = 8888
    
    assert inventory_item["power"] == 150, "Inventory item was mutated via old equipped reference!"
    assert inventory_item["lucky_options"]["xp_bonus"] == 5, "Nested property was mutated via old equipped reference!"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

