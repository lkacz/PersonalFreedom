"""Test script to verify item award logic works correctly."""
import sys
import json
from datetime import datetime
from copy import deepcopy

# Import the necessary functions
from gamification import (
    generate_item, 
    sync_hero_data,
    ensure_hero_structure,
    STORY_MODE_ACTIVE
)

def run_item_award_flow() -> bool:
    """Simulate the Nighty-Night bonus award flow."""
    print("="*60)
    print("Testing Item Award Flow")
    print("="*60)
    
    # Create a mock adhd_buster structure
    adhd_buster = {
        "story_mode": STORY_MODE_ACTIVE,
        "active_story": "warrior",
        "story_heroes": {},
        "free_hero": {},
        "inventory": [],
        "equipped": {},
        "total_collected": 0,
        "luck_bonus": 0,
        "last_daily_reward_date": "",
        "max_power_reached": 0,
        "story_decisions": {},
        "diary": []
    }
    
    # Ensure hero structure
    ensure_hero_structure(adhd_buster)
    print(f"✓ Hero structure ensured")
    print(f"  Initial inventory size: {len(adhd_buster['inventory'])}")
    
    # Generate an item (simulate Nighty-Night bonus)
    rarity = "Legendary"  # Test with best rarity
    active_story = adhd_buster.get("active_story", "warrior")
    item = generate_item(rarity=rarity, story_id=active_story)
    
    # Validate item
    required_fields = ["name", "rarity", "slot", "item_type", "color", "power", "story_theme"]
    missing = [f for f in required_fields if f not in item]
    if missing:
        print(f"✗ Item missing required fields: {missing}")
        return False
    print(f"✓ Item generated successfully")
    print(f"  Name: {item['name']}")
    print(f"  Rarity: {item['rarity']}")
    print(f"  Slot: {item['slot']}")
    
    # Add source and timestamp
    item["source"] = "sleep_now_bonus"
    if "obtained_at" not in item:
        item["obtained_at"] = datetime.now().isoformat()
    
    # Add to inventory (using defensive copy)
    original_item = deepcopy(item)
    adhd_buster["inventory"].append(item.copy())
    adhd_buster["total_collected"] = adhd_buster.get("total_collected", 0) + 1
    
    print(f"✓ Item added to inventory")
    print(f"  Inventory size: {len(adhd_buster['inventory'])}")
    
    # Verify item is in inventory
    if len(adhd_buster["inventory"]) != 1:
        print(f"✗ Expected 1 item, found {len(adhd_buster['inventory'])}")
        return False
    
    # Verify item data is correct
    inv_item = adhd_buster["inventory"][0]
    if inv_item["name"] != original_item["name"]:
        print(f"✗ Item name mismatch: {inv_item['name']} != {original_item['name']}")
        return False
    if inv_item["rarity"] != original_item["rarity"]:
        print(f"✗ Item rarity mismatch: {inv_item['rarity']} != {original_item['rarity']}")
        return False
    
    print(f"✓ Item data verified in inventory")
    
    # Auto-equip if slot empty
    slot = item.get("slot")
    if slot and not adhd_buster["equipped"].get(slot):
        adhd_buster["equipped"][slot] = item.copy()
        print(f"✓ Item auto-equipped to {slot} slot")
    
    # Sync hero data
    pre_sync_inv_size = len(adhd_buster["inventory"])
    sync_hero_data(adhd_buster)
    post_sync_inv_size = len(adhd_buster["inventory"])
    
    if pre_sync_inv_size != post_sync_inv_size:
        print(f"✗ Inventory size changed during sync: {pre_sync_inv_size} -> {post_sync_inv_size}")
        return False
    
    print(f"✓ Hero data synced successfully")
    print(f"  Inventory size unchanged: {post_sync_inv_size}")
    
    # Verify item still in inventory after sync
    if len(adhd_buster["inventory"]) != 1:
        print(f"✗ Item lost after sync! Inventory size: {len(adhd_buster['inventory'])}")
        return False
    
    inv_item_after_sync = adhd_buster["inventory"][0]
    if inv_item_after_sync["name"] != original_item["name"]:
        print(f"✗ Item corrupted after sync!")
        return False
    
    print(f"✓ Item verified after sync")
    
    # Verify hero structure has the item
    active_story = adhd_buster.get("active_story")
    hero = adhd_buster["story_heroes"].get(active_story, {})
    hero_inventory = hero.get("inventory", [])
    
    if len(hero_inventory) != 1:
        print(f"✗ Hero inventory size mismatch: {len(hero_inventory)}")
        return False
    
    print(f"✓ Hero structure verified")
    print(f"  Hero inventory size: {len(hero_inventory)}")
    
    # Test JSON serialization (simulate save)
    try:
        json_str = json.dumps(adhd_buster)
        reloaded = json.loads(json_str)
        
        if len(reloaded["inventory"]) != 1:
            print(f"✗ Item lost during JSON serialization!")
            return False
        
        print(f"✓ JSON serialization successful")
        print(f"  Reloaded inventory size: {len(reloaded['inventory'])}")
        
    except Exception as e:
        print(f"✗ JSON serialization failed: {e}")
        return False
    
    print()
    print("="*60)
    print("✓ ALL TESTS PASSED - Item award flow is working correctly!")
    print("="*60)
    return True


def test_item_award_flow():
    """Pytest wrapper for the item award flow script."""
    assert run_item_award_flow() is True

if __name__ == "__main__":
    success = run_item_award_flow()
    sys.exit(0 if success else 1)
