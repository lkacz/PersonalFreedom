
import sys
import os

# Add local directory to path
sys.path.append(os.getcwd())

try:
    from gamification import generate_item, get_neighbor_effect_emoji
    
    print("Testing Item Generation & Neighbor Effects...")
    
    # Generate 10 Legendary items (80% chance for effect)
    count_effects = 0
    for i in range(10):
        item = generate_item(rarity="Legendary")
        emoji = get_neighbor_effect_emoji(item)
        has_effect = "neighbor_effect" in item
        print(f"Item {i+1}: {item['name']} | Effect: {has_effect} | Emoji: '{emoji}'")
        if has_effect:
            count_effects += 1
            
    print(f"\nTotal items with effects: {count_effects}/10")
    
except Exception as e:
    print(f"Error: {e}")
