#!/usr/bin/env python
"""Comprehensive edge case testing for Power Analysis Dialog."""
import sys
sys.path.insert(0, '.')

from gamification import (
    get_power_breakdown,
    generate_item,
    GEAR_SLOTS
)


def run_scenario(name: str, equipped: dict):
    """Test a specific scenario."""
    print(f"\n{'='*60}")
    print(f"Scenario: {name}")
    print('='*60)
    
    adhd_buster = {"equipped": equipped}
    try:
        breakdown = get_power_breakdown(adhd_buster, include_neighbor_effects=True)
        
        print(f"✓ Breakdown generated successfully")
        print(f"  Total Power: {breakdown['total_power']}")
        print(f"  Base: {breakdown['base_power']}, Set: {breakdown['set_bonus']}, Neighbor: {breakdown['neighbor_adjustment']:+d}")
        
        # Check required keys
        required = ['base_power', 'set_bonus', 'neighbor_adjustment', 'total_power', 
                   'power_by_slot', 'neighbor_effects', 'active_sets']
        missing = [k for k in required if k not in breakdown]
        if missing:
            print(f"  ✗ Missing keys: {missing}")
        else:
            print(f"  ✓ All required keys present")
        
        # Check neighbor effects structure
        neighbor_effects = breakdown.get('neighbor_effects', {})
        if neighbor_effects:
            print(f"  ✓ Neighbor effects: {len(neighbor_effects)} slots affected")
            for slot, data in neighbor_effects.items():
                if 'effects' not in data or 'multiplier' not in data:
                    print(f"    ✗ {slot} missing required fields")
        
        # Check power_by_slot has all slots
        power_by_slot = breakdown.get('power_by_slot', {})
        missing_slots = [s for s in GEAR_SLOTS if s not in power_by_slot]
        if missing_slots:
            print(f"  ✗ Missing slots in power_by_slot: {missing_slots}")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main() -> None:
    # Test 1: Empty equipment
    print("\nTest 1: Empty Equipment")
    run_scenario("No items equipped", {})

    # Test 2: Single item, no effects
    print("\nTest 2: Single Item")
    helmet = generate_item(rarity="Common", story_id="warrior")
    helmet["slot"] = "Helmet"
    run_scenario("Only helmet equipped", {"Helmet": helmet})

    # Test 3: Full equipment with neighbor effects
    print("\nTest 3: Full Set with Neighbor Effects")
    equipped = {}
    for i, slot in enumerate(GEAR_SLOTS):
        item = generate_item(rarity="Rare" if i % 2 == 0 else "Epic", story_id="warrior")
        item["slot"] = slot
        # Add neighbor effect to every other item
        if i % 2 == 0:
            item["neighbor_effect"] = {
                "type": "boost",
                "target": "power",
                "multiplier": 1.10
            }
        equipped[slot] = item

    run_scenario("Full equipment with alternating neighbor effects", equipped)

    # Test 4: Multiple neighbor effects on same slot
    print("\nTest 4: Multiple Neighbor Effects (Chain)")
    helmet = generate_item(rarity="Legendary", story_id="warrior")
    helmet["slot"] = "Helmet"
    helmet["neighbor_effect"] = {"type": "boost", "target": "power", "multiplier": 1.20}

    chestplate = generate_item(rarity="Legendary", story_id="warrior")
    chestplate["slot"] = "Chestplate"
    # Chestplate is neighbor to Helmet, so it will be affected

    gauntlets = generate_item(rarity="Legendary", story_id="warrior")
    gauntlets["slot"] = "Gauntlets"
    gauntlets["neighbor_effect"] = {"type": "boost", "target": "power", "multiplier": 1.15}
    # Gauntlets affect Chestplate too (if Chestplate is neighbor to Gauntlets)

    run_scenario("Chain neighbor effects", {
        "Helmet": helmet,
        "Chestplate": chestplate,
        "Gauntlets": gauntlets
    })

    # Test 5: Unfriendly effects (penalty)
    print("\nTest 5: Unfriendly Effects (Penalty)")
    weapon = generate_item(rarity="Epic", story_id="warrior")
    weapon["slot"] = "Weapon"
    weapon["neighbor_effect"] = {"type": "drain", "target": "power", "multiplier": 0.85}

    shield = generate_item(rarity="Epic", story_id="warrior")
    shield["slot"] = "Shield"

    run_scenario("Weapon with drain effect affecting Shield", {
        "Weapon": weapon,
        "Shield": shield
    })

    # Test 6: Null items in slots (defensive check)
    print("\nTest 6: Null Items in Equipment Dict")
    run_scenario("Equipment dict with None values", {
        "Helmet": None,
        "Chestplate": generate_item(rarity="Common", story_id="warrior"),
        "Weapon": None
    })

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
