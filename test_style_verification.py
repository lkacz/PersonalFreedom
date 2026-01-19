#!/usr/bin/env python3
"""Comprehensive verification of style bonus implementation."""

from gamification import (
    calculate_effective_power, 
    get_power_breakdown, 
    calculate_character_power,
    optimize_equipped_gear,
    GEAR_SLOTS,
    LEGENDARY_MINIMALIST_BONUS
)

print('=' * 60)
print('STYLE BONUS VERIFICATION')
print('=' * 60)

# Test 1: calculate_effective_power includes style bonus
print('\n[1] calculate_effective_power with 7 Legendary + 1 empty:')
equipped = {s: {'name': f'Legendary {s}', 'rarity': 'Legendary', 'power': 250} for s in GEAR_SLOTS if s != 'Weapon'}
result = calculate_effective_power(equipped)
print(f'    Base: {result["base_power"]}')
print(f'    Set: {result["set_bonus"]}')
print(f'    Style: {result["style_bonus"]}')
print(f'    Total: {result["total_power"]}')
expected = result['base_power'] + result['set_bonus'] + result['style_bonus']
print(f'    Expected: {expected}, Match: {result["total_power"] == expected}')

# Test 2: calculate_effective_power with 8 Legendary (no style bonus)
print('\n[2] calculate_effective_power with 8 Legendary (full set):')
equipped_full = {s: {'name': f'Legendary {s}', 'rarity': 'Legendary', 'power': 250} for s in GEAR_SLOTS}
result2 = calculate_effective_power(equipped_full)
print(f'    Base: {result2["base_power"]}')
print(f'    Set: {result2["set_bonus"]}')
print(f'    Style: {result2["style_bonus"]} (should be 0)')
print(f'    Total: {result2["total_power"]}')

# Test 3: get_power_breakdown includes entity_bonus
print('\n[3] get_power_breakdown with real entity patrons:')
adhd_buster = {
    'equipped': equipped,  # 7 legendary, weapon empty
    'entitidex': {
        'discovered': {
            # Use real entity IDs that have POWER_FLAT perks
            'warrior_001': {'name': 'Hatchling Drake', 'rarity': 'common', 'count': 5},
            'warrior_002': {'name': 'Old Training Dummy', 'rarity': 'common', 'count': 10},
        }
    }
}
breakdown = get_power_breakdown(adhd_buster)
print(f'    Base: {breakdown["base_power"]}')
print(f'    Set: {breakdown["set_bonus"]}')
print(f'    Style: {breakdown["style_bonus"]}')
print(f'    Entity: {breakdown["entity_bonus"]}')
print(f'    Total: {breakdown["total_power"]}')
expected_total = breakdown['base_power'] + breakdown['set_bonus'] + breakdown['style_bonus'] + breakdown['entity_bonus']
print(f'    Expected: {expected_total}, Match: {breakdown["total_power"] == expected_total}')

# Test 4: calculate_character_power
print('\n[4] calculate_character_power:')
char_power = calculate_character_power(adhd_buster)
print(f'    Result: {char_power}')
print(f'    Matches breakdown total: {char_power == breakdown["total_power"]}')

print()
print('=' * 60)
print('OPTIMIZER NAIVE TO STYLE BONUS')
print('=' * 60)

# Test 5: Optimizer should prefer full 8 legendary over 7+empty
print('\n[5] Optimizer should prefer 8 Legendary over 7+empty:')
# Create inventory with 8 legendary items
test_adhd = {
    'inventory': [{'name': f'Legendary {s}', 'slot': s, 'rarity': 'Legendary', 'power': 250, 'obtained_at': f't{i}'} for i, s in enumerate(GEAR_SLOTS)],
    'equipped': {}
}
result = optimize_equipped_gear(test_adhd, mode='power')
equipped_count = sum(1 for s in GEAR_SLOTS if result['new_equipped'].get(s))
print(f'    Items equipped: {equipped_count} (should be 8)')
print(f'    New power: {result["new_power"]}')

# Calculate what power would be with style bonus (7 items)
style_power = 7 * 250 + LEGENDARY_MINIMALIST_BONUS  # No set bonus for simplicity
full_power = 8 * 250
print(f'    Full 8 items power (no set): {full_power}')
print(f'    7 items + style bonus: {style_power}')
print(f'    Optimizer chose: {"8 items (CORRECT)" if equipped_count == 8 else "7 items (WRONG - style bonus leaked!)"}')

print()
print('=' * 60)
print('SUMMARY')
print('=' * 60)

all_pass = True

# Check 1: Optimizer chose 8 items (ignores style bonus)
if equipped_count == 8:
    print('[PASS] Optimizer ignores style bonus - chose 8 items')
else:
    print('[FAIL] Optimizer may be considering style bonus')
    all_pass = False

# Check 2: Total power formula
if breakdown["total_power"] == expected_total:
    print('[PASS] Total power = base + set + style + entity')
else:
    print('[FAIL] Total power formula incorrect')
    all_pass = False

# Check 3: Character power matches breakdown
if char_power == breakdown["total_power"]:
    print('[PASS] calculate_character_power matches breakdown')
else:
    print('[FAIL] calculate_character_power mismatch')
    all_pass = False

print()
if all_pass:
    print('✅ ALL CHECKS PASSED!')
else:
    print('❌ SOME CHECKS FAILED!')
