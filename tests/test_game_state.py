"""
Tests for the GameStateManager reactive state system.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestGameStateManager:
    """Test the GameStateManager class."""
    
    @pytest.fixture
    def mock_blocker(self):
        """Create a mock blocker with adhd_buster data."""
        blocker = Mock()
        blocker.adhd_buster = {
            "inventory": [],
            "equipped": {},
            "coins": 100,
            "hero": {"xp": 0, "level": 1}
        }
        blocker.save_config = Mock()
        return blocker
    
    @pytest.fixture
    def game_state(self, mock_blocker):
        """Create a GameStateManager instance."""
        from game_state import GameStateManager, reset_game_state
        reset_game_state()  # Clear singleton
        return GameStateManager(mock_blocker)
    
    def test_init(self, game_state, mock_blocker):
        """Test GameStateManager initialization."""
        assert game_state._blocker == mock_blocker
        assert game_state._batch_mode is False
    
    def test_add_item(self, game_state, mock_blocker):
        """Test adding an item to inventory."""
        item = {"id": "test1", "name": "Test Item", "slot": "Helmet", "rarity": "Common"}
        game_state.add_item(item)
        
        assert len(mock_blocker.adhd_buster["inventory"]) == 1
        assert mock_blocker.adhd_buster["inventory"][0]["id"] == "test1"
        mock_blocker.save_config.assert_called()
    
    def test_remove_item(self, game_state, mock_blocker):
        """Test removing an item from inventory."""
        item = {"id": "test1", "name": "Test Item", "slot": "Helmet", "rarity": "Common"}
        mock_blocker.adhd_buster["inventory"].append(item)
        
        result = game_state.remove_item("test1")
        
        assert result is True
        assert len(mock_blocker.adhd_buster["inventory"]) == 0
    
    def test_remove_item_not_found(self, game_state, mock_blocker):
        """Test removing non-existent item returns False."""
        result = game_state.remove_item("nonexistent")
        assert result is False
    
    def test_add_coins(self, game_state, mock_blocker):
        """Test adding coins."""
        initial_coins = mock_blocker.adhd_buster["coins"]
        new_total = game_state.add_coins(50)
        
        assert new_total == initial_coins + 50
        assert mock_blocker.adhd_buster["coins"] == new_total
    
    def test_spend_coins_sufficient(self, game_state, mock_blocker):
        """Test spending coins when sufficient."""
        mock_blocker.adhd_buster["coins"] = 100
        result = game_state.spend_coins(50)
        
        assert result is True
        assert mock_blocker.adhd_buster["coins"] == 50
    
    def test_spend_coins_insufficient(self, game_state, mock_blocker):
        """Test spending coins when insufficient."""
        mock_blocker.adhd_buster["coins"] = 30
        result = game_state.spend_coins(50)
        
        assert result is False
        assert mock_blocker.adhd_buster["coins"] == 30  # Unchanged
    
    def test_equip_item(self, game_state, mock_blocker):
        """Test equipping an item."""
        item = {"id": "helm1", "name": "Test Helmet", "slot": "Helmet", "rarity": "Rare"}
        game_state.equip_item("Helmet", item)
        
        equipped = mock_blocker.adhd_buster["equipped"]["Helmet"]
        # Check the original fields are preserved
        assert equipped["id"] == item["id"]
        assert equipped["name"] == item["name"]
        assert equipped["slot"] == item["slot"]
        assert equipped["rarity"] == item["rarity"]
        # equip_item now adds an item_id for unique identification
        assert "item_id" in equipped
        mock_blocker.save_config.assert_called()
    
    def test_batch_operations(self, game_state, mock_blocker):
        """Test batch mode groups operations."""
        signals_emitted = []
        game_state.coins_changed.connect(lambda x: signals_emitted.append(("coins", x)))
        game_state.inventory_changed.connect(lambda: signals_emitted.append(("inventory",)))
        
        game_state.begin_batch()
        game_state.add_coins(10)
        game_state.add_coins(20)
        game_state.add_item({"id": "test", "name": "Test"})
        
        # No signals yet during batch
        # Note: signals are queued, not emitted
        
        game_state.end_batch()
        
        # After end_batch, signals should be emitted (deduplicated)
        assert len(signals_emitted) >= 1  # At least coins_changed and inventory_changed
    
    def test_swap_equipped_item(self, game_state, mock_blocker):
        """Test swapping equipped item.
        
        Design: Items are ALWAYS in inventory, equipped dict holds references.
        When swapping, both old and new items remain in inventory.
        """
        old_item = {"id": "old", "name": "Old Helmet", "slot": "Helmet"}
        new_item = {"id": "new", "name": "New Helmet", "slot": "Helmet"}
        
        # Both items are in inventory, old item is equipped
        mock_blocker.adhd_buster["equipped"]["Helmet"] = old_item
        mock_blocker.adhd_buster["inventory"] = [old_item, new_item]
        
        returned = game_state.swap_equipped_item("Helmet", new_item)
        
        # Old item is returned
        assert returned["id"] == "old"
        # New item is now equipped (as a deep copy)
        assert mock_blocker.adhd_buster["equipped"]["Helmet"]["id"] == "new"
        # Both items still in inventory
        assert len(mock_blocker.adhd_buster["inventory"]) == 2
        assert any(i["id"] == "old" for i in mock_blocker.adhd_buster["inventory"])
        assert any(i["id"] == "new" for i in mock_blocker.adhd_buster["inventory"])
    
    def test_sell_item(self, game_state, mock_blocker):
        """Test selling an item."""
        item = {"id": "sell1", "name": "Sellable Item"}
        mock_blocker.adhd_buster["inventory"] = [item]
        initial_coins = mock_blocker.adhd_buster["coins"]
        
        result = game_state.sell_item("sell1", 25)
        
        assert result is True
        assert mock_blocker.adhd_buster["coins"] == initial_coins + 25
        assert len(mock_blocker.adhd_buster["inventory"]) == 0
    
    def test_get_current_power(self, game_state, mock_blocker):
        """Test getting current power."""
        # With no equipped items, power should be 0 or calculated value
        power = game_state.get_current_power()
        assert isinstance(power, int)
    
    def test_get_current_coins(self, game_state, mock_blocker):
        """Test getting current coins."""
        mock_blocker.adhd_buster["coins"] = 500
        assert game_state.get_current_coins() == 500


class TestGameStateSingleton:
    """Test the singleton pattern for game state."""
    
    def test_get_game_state_returns_none_without_blocker(self):
        """Test get_game_state returns None if no blocker provided."""
        from game_state import get_game_state, reset_game_state
        reset_game_state()
        result = get_game_state()
        assert result is None
    
    def test_init_game_state_creates_instance(self):
        """Test init_game_state creates a new instance."""
        from game_state import init_game_state, get_game_state, reset_game_state
        reset_game_state()
        
        mock_blocker = Mock()
        mock_blocker.adhd_buster = {"inventory": [], "equipped": {}, "coins": 0}
        
        state = init_game_state(mock_blocker)
        assert state is not None
        
        # Should return same instance
        state2 = get_game_state()
        assert state2 is state
    
    def test_reset_clears_singleton(self):
        """Test reset_game_state clears the singleton."""
        from game_state import init_game_state, get_game_state, reset_game_state
        
        mock_blocker = Mock()
        mock_blocker.adhd_buster = {"inventory": [], "equipped": {}, "coins": 0}
        
        init_game_state(mock_blocker)
        reset_game_state()
        
        result = get_game_state()
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
