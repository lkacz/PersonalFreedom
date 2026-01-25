"""Test item generation to verify special attributes are being rolled correctly."""

from gamification import generate_item, LUCKY_OPTION_CHANCES, LUCK_BOOST_CHANCES

print('=== Testing Item Generation with Special Attributes ===\n')

# Generate 10 items of each rarity and count special attributes
rarities = ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary']

for rarity in rarities:
    print(f'--- {rarity} Items (10 samples) ---')
    luck_boost_count = 0
    lucky_options_count = 0
    
    for i in range(10):
        item = generate_item(rarity=rarity, story_id='warrior')
        
        if item.get('luck_boost', 0) > 0:
            luck_boost_count += 1
        if item.get('lucky_options'):
            lucky_options_count += 1
    
    luck_chance = LUCK_BOOST_CHANCES.get(rarity, 0)
    lucky_chance = LUCKY_OPTION_CHANCES.get(rarity, {}).get("base_chance", 0)
    
    print(f'  Luck Boost: {luck_boost_count}/10 (expected ~{luck_chance}%)')
    print(f'  Lucky Options: {lucky_options_count}/10 (expected ~{lucky_chance}%)')
    print()

# Show a sample Legendary item with all attributes
print('=== Sample Legendary Item with All Attributes ===')
for i in range(50):
    item = generate_item(rarity='Legendary', story_id='warrior')
    if item.get('luck_boost') and item.get('lucky_options'):
        print(f'Name: {item["name"]}')
        print(f'Rarity: {item["rarity"]}')
        print(f'Slot: {item["slot"]}')
        print(f'Item Type: {item.get("item_type", "N/A")}')
        print(f'Power: {item["power"]}')
        print(f'Luck Boost: +{item["luck_boost"]}%')
        print(f'Lucky Options: {item["lucky_options"]}')
        break
else:
    print('(Could not find item with both attributes in 50 tries - checking last item)')
    
    # Show last generated item
    print(f'\nLast item generated:')
    print(f'  Name: {item["name"]}')
    print(f'  Luck Boost: {item.get("luck_boost", "None")}')
    print(f'  Lucky Options: {item.get("lucky_options", "None")}')
