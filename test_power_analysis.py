#!/usr/bin/env python
"""Quick test of Power Analysis Dialog logic."""
import sys
sys.path.insert(0, '.')

from gamification import (
    get_power_breakdown,
    generate_item,
    GEAR_SLOTS
)

# Create test equipped items
print("=" * 60)
print("Testing Power Analysis Data Structure")
print("=" * 60)

equipped = {}
for slot in ["Helmet", "Chestplate", "Weapon"]:
    item = generate_item(rarity="Epic", story_id="warrior")
    item["slot"] = slot
    # Add a neighbor effect to Helmet
    if slot == "Helmet":
        item["neighbor_effect"] = {
            "type": "synergy",
            "target": "power",
            "multiplier": 1.15
        }
    equipped[slot] = item

adhd_buster = {"equipped": equipped}

# Get breakdown
breakdown = get_power_breakdown(adhd_buster, include_neighbor_effects=True)

print("\nBreakdown keys:", list(breakdown.keys()))
print("\nBreakdown structure:")
for key, value in breakdown.items():
    if isinstance(value, dict):
        print(f"  {key}: {type(value).__name__} with {len(value)} entries")
        if key == "neighbor_effects":
            for slot, effect_data in value.items():
                print(f"    {slot}: {effect_data}")
    else:
        print(f"  {key}: {value}")

# Check if active_sets is present
if "active_sets" in breakdown:
    print("\n✓ active_sets is present")
else:
    print("\n✗ active_sets is MISSING (needed for dialog bottom section)")
    print("   Dialog will fail when trying to display set bonus details")

# Verify power_by_slot matches expected
print("\nPower by slot:")
for slot in GEAR_SLOTS:
    power = breakdown.get("power_by_slot", {}).get(slot, 0)
    print(f"  {slot}: {power}")
