#!/usr/bin/env python
"""Quick test of lucky options generation."""
import sys
sys.path.insert(0, '.')

from gamification import generate_item, LUCKY_OPTION_CHANCES

print('Testing 30 Legendary items for lucky_options:')
items_with_lucky = 0
items_with_neighbor = 0
items_with_luck_boost = 0

for i in range(30):
    item = generate_item(rarity='Legendary', story_id='warrior')
    if item.get('lucky_options'):
        items_with_lucky += 1
        print(f'  Item {i+1}: Lucky: {item["lucky_options"]}')
    if item.get('neighbor_effect'):
        items_with_neighbor += 1
    if item.get('luck_boost'):
        items_with_luck_boost += 1

print(f'\nSummary:')
print(f'  Items with lucky_options: {items_with_lucky}/30 (expected ~95%)')
print(f'  Items with neighbor_effect: {items_with_neighbor}/30 (expected ~80%)')
print(f'  Items with luck_boost: {items_with_luck_boost}/30 (expected ~80%)')
print(f'\nLUCKY_OPTION_CHANCES: {LUCKY_OPTION_CHANCES}')
