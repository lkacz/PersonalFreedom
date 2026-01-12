"""Test deep copy isolation in GameStateManager."""
from game_state import GameStateManager, deep_copy_item


class MockBlocker:
    def __init__(self):
        self.adhd_buster = {'inventory': [], 'equipped': {}, 'coins': 0}
    def save_config(self):
        pass


def test_swap_equipped_item_isolation():
    """Test that swap_equipped_item creates isolated copies."""
    blocker = MockBlocker()
    gs = GameStateManager(blocker)

    # Create item with nested dict
    item = {
        'name': 'Test', 
        'slot': 'Weapon', 
        'obtained_at': '2024-01-01', 
        'lucky_options': {'power': 10}
    }
    blocker.adhd_buster['inventory'].append(item)

    # Swap to equipped
    gs.swap_equipped_item('Weapon', item)

    # Mutate original
    item['lucky_options']['power'] = 999

    # Check equipped copy is isolated
    equipped = blocker.adhd_buster['equipped']['Weapon']
    print(f"Original lucky_options.power: {item['lucky_options']['power']}")
    print(f"Equipped lucky_options.power: {equipped['lucky_options']['power']}")
    assert equipped['lucky_options']['power'] == 10, "Equipped item should be isolated!"
    print("✅ swap_equipped_item isolation test PASSED")


def test_award_items_batch_isolation():
    """Test that award_items_batch creates isolated copies."""
    blocker = MockBlocker()
    gs = GameStateManager(blocker)

    # Create item with nested dict
    item = {
        'name': 'Test', 
        'slot': 'Helmet', 
        'obtained_at': '2024-01-02', 
        'lucky_options': {'drop_luck': 5}
    }

    # Award the item
    result = gs.award_items_batch([item], coins=0, auto_equip=True)

    # Mutate original
    item['lucky_options']['drop_luck'] = 999

    # Check inventory and equipped are isolated
    inv_item = blocker.adhd_buster['inventory'][0]
    eq_item = blocker.adhd_buster['equipped']['Helmet']
    
    print(f"Original drop_luck: {item['lucky_options']['drop_luck']}")
    print(f"Inventory drop_luck: {inv_item['lucky_options']['drop_luck']}")
    print(f"Equipped drop_luck: {eq_item['lucky_options']['drop_luck']}")
    
    assert inv_item['lucky_options']['drop_luck'] == 5, "Inventory item should be isolated!"
    assert eq_item['lucky_options']['drop_luck'] == 5, "Equipped item should be isolated!"
    print("✅ award_items_batch isolation test PASSED")


if __name__ == '__main__':
    test_swap_equipped_item_isolation()
    test_award_items_batch_isolation()
    print("\n✅ All isolation tests PASSED!")
