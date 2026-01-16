"""
Centralized Game State Manager with Qt Signals for reactive UI updates.

This module provides a reactive state management pattern for the gamification system.
All state changes emit signals that UI components can subscribe to, ensuring
consistent and automatic UI updates without manual refresh calls.

Industry Standard Pattern: Observer/Pub-Sub with Qt Signals
- All state modifications go through this manager
- Changes automatically emit signals to subscribed UI components
- Batch operations group multiple changes into single UI update
- Thread-safe signal emission via Qt's event loop

Race Condition Prevention:
- All operations run on the main Qt thread (no explicit threading)
- Batch mode defers saves until end_batch() for atomic multi-step operations
- Exception-safe batch operations using try/finally patterns
- Re-entrancy guard on singleton initialization
"""

from PySide6 import QtCore
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager
import copy
import logging
import uuid

logger = logging.getLogger(__name__)


def deep_copy_item(item: dict) -> dict:
    """Create a deep copy of an item dict, handling nested structures.
    
    This ensures lucky_options, neighbor_effect, and other nested dicts
    are properly copied to prevent mutations leaking between copies.
    """
    if not item:
        return {}
    # Use copy.deepcopy for full isolation
    return copy.deepcopy(item)


class _BatchContext:
    """Context manager for batch operations."""
    
    def __init__(self, state_manager: 'GameStateManager'):
        self._state = state_manager
    
    def __enter__(self):
        self._state.begin_batch()
        return self._state
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._state.end_batch()
        return False  # Don't suppress exceptions


class GameStateManager(QtCore.QObject):
    """
    Centralized state manager that emits Qt signals on state changes.
    
    This enables reactive UI updates - components subscribe to changes
    they care about and automatically update when state changes.
    
    Usage:
        state = GameStateManager(blocker)
        state.power_changed.connect(self._update_power_display)
        state.inventory_changed.connect(self._refresh_inventory)
        
        # When modifying state:
        state.add_item(item)  # Automatically emits inventory_changed, power_changed
    """
    
    # === State Change Signals ===
    
    # Inventory signals
    inventory_changed = QtCore.Signal()  # Any inventory change
    item_added = QtCore.Signal(dict)  # New item added (item data)
    item_removed = QtCore.Signal(str)  # Item removed (item id)
    items_merged = QtCore.Signal(dict)  # Items merged (new item data)
    
    # Equipment signals
    equipment_changed = QtCore.Signal(str)  # Slot that changed
    item_equipped = QtCore.Signal(str, dict)  # (slot, item)
    item_unequipped = QtCore.Signal(str)  # slot
    
    # Power/Stats signals
    power_changed = QtCore.Signal(int)  # New total power
    set_bonus_changed = QtCore.Signal(dict)  # Set bonus info
    luck_bonus_changed = QtCore.Signal(int)  # New luck_bonus total
    
    # Currency signals
    coins_changed = QtCore.Signal(int)  # New coin total
    xp_changed = QtCore.Signal(int, int)  # (new_xp, new_level)
    
    # Hero signals
    hero_changed = QtCore.Signal()  # Hero selection changed
    story_changed = QtCore.Signal(str)  # Story theme changed
    
    # Session signals
    session_reward_earned = QtCore.Signal(dict)  # Reward data (item, xp, coins)
    
    # General refresh (fallback for complex multi-changes)
    full_refresh_required = QtCore.Signal()
    
    # Config/data reload signals
    config_saved = QtCore.Signal()
    config_loaded = QtCore.Signal()
    
    def __init__(self, blocker, parent: Optional[QtCore.QObject] = None):
        super().__init__(parent)
        self._blocker = blocker
        self._batch_depth = 0  # Support nested batch operations
        self._pending_signals: List[tuple] = []
        self._subscribers: Dict[str, List[Callable]] = {}
        self._save_pending = False  # Track if save is needed at end of batch
        self._debug_mode = False
        logger.info("GameStateManager initialized")
        
    def enable_debug(self, enabled: bool = True):
        """Enable debug logging for all state changes."""
        self._debug_mode = enabled
        
    def _log_change(self, action: str, details: str = ""):
        """Log a state change if debug mode is enabled."""
        if self._debug_mode:
            logger.debug(f"[GameState] {action}: {details}")
        
    @property
    def adhd_buster(self) -> dict:
        """Access to the underlying adhd_buster data."""
        return self._blocker.adhd_buster
    
    @property
    def inventory(self) -> list:
        """Access to inventory list."""
        return self.adhd_buster.get("inventory", [])
    
    @property
    def equipped(self) -> dict:
        """Access to equipped items dict."""
        return self.adhd_buster.get("equipped", {})
    
    @property
    def coins(self) -> int:
        """Get current coin count."""
        return self.adhd_buster.get("coins", 0)
    
    # === Batch Operations ===
    
    @property
    def _batch_mode(self) -> bool:
        """Check if currently in batch mode (supports nested batches)."""
        return self._batch_depth > 0
    
    def begin_batch(self):
        """Start batching signals - emit all at once when end_batch is called.
        
        Also defers save_config calls until end_batch for efficiency.
        Supports nested batch operations - only outermost end_batch emits signals.
        """
        if self._batch_depth == 0:
            # First batch - clear pending signals
            self._pending_signals = []
            self._save_pending = False
        self._batch_depth += 1
    
    def end_batch(self):
        """End batch mode, save if needed, and emit all pending signals.
        
        Uses try/finally to ensure batch mode is always properly exited,
        even if signal emission raises an exception.
        
        Supports nested batches - only outermost end_batch saves and emits.
        """
        if self._batch_depth <= 0:
            logger.warning("end_batch called without matching begin_batch")
            return
        
        self._batch_depth -= 1
        
        # Only process signals/save on outermost batch end
        if self._batch_depth > 0:
            return
        
        try:
            # Save once at end if any operation requested it
            if self._save_pending:
                self._sync_and_save()
                self._save_pending = False
            
            # Deduplicate signals (keep last occurrence for each signal type)
            seen = {}
            for sig, args in self._pending_signals:
                seen[sig] = args
            
            for sig, args in seen.items():
                try:
                    if args is None:
                        sig.emit()
                    elif isinstance(args, tuple):
                        sig.emit(*args)
                    else:
                        sig.emit(args)
                except Exception as e:
                    logger.error(f"Error emitting signal {sig}: {e}")
        finally:
            # Clear pending signals
            self._pending_signals = []
    
    def batch(self):
        """Context manager for batch operations.
        
        Usage:
            with game_state.batch():
                game_state.add_item(item1)
                game_state.add_item(item2)
                game_state.add_coins(100)
            # All signals emitted here, single save
        """
        return _BatchContext(self)
    
    def _sync_and_save(self):
        """Sync gamification data and save to disk."""
        try:
            from gamification import sync_hero_data
            sync_hero_data(self.adhd_buster)
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Error syncing hero data: {e}")
        
        try:
            self._blocker.save_config()
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            # Don't re-raise - log and continue to prevent cascading failures

    def _save_config(self):
        """Save config, or defer if in batch mode."""
        if self._batch_mode:
            self._save_pending = True
        else:
            self._sync_and_save()
    
    def _emit(self, signal, *args):
        """Emit a signal, or queue it if in batch mode."""
        if self._batch_mode:
            self._pending_signals.append((signal, args if args else None))
        else:
            try:
                if args:
                    signal.emit(*args)
                else:
                    signal.emit()
            except Exception:
                pass  # Silently handle signal emission errors
    
    # === State Modification Methods ===
    
    # Base maximum inventory size to prevent unbounded growth
    MAX_INVENTORY_SIZE = 500
    
    # Valid equipment slots (must match GEAR_SLOTS in gamification.py)
    VALID_SLOTS = {"Helmet", "Chestplate", "Gauntlets", "Boots", "Shield", "Weapon", "Cloak", "Amulet"}
    
    def get_max_inventory_size(self) -> int:
        """Get maximum inventory size including entity perk bonuses."""
        try:
            from gamification import get_entity_qol_perks
            qol_perks = get_entity_qol_perks(self.adhd_buster)
            bonus_slots = qol_perks.get("inventory_slots", 0)
            return self.MAX_INVENTORY_SIZE + bonus_slots
        except Exception:
            return self.MAX_INVENTORY_SIZE
    
    def _match_item(self, item: dict, item_id: str) -> bool:
        """Match an item by ID or fallback identifiers.
        
        Handles items that may not have an 'id' field by falling back to
        matching by 'obtained_at' timestamp or name+slot+rarity combination.
        """
        # Guard: require valid item_id
        if not item_id:
            return False
        
        # Primary: match by id (ensure non-empty)
        item_actual_id = item.get("id")
        if item_actual_id and item_actual_id == item_id:
            return True
        
        # Fallback: id might be the obtained_at timestamp
        obtained_at = item.get("obtained_at")
        if obtained_at and obtained_at == item_id:
            return True
        
        # Fallback: id might be a composite key "name:slot:rarity"
        if ":" in item_id:
            parts = item_id.split(":", 2)
            if len(parts) == 3:
                name, slot, rarity = parts
                if (item.get("name") == name and 
                    item.get("slot") == slot and 
                    item.get("rarity") == rarity):
                    return True
        
        return False
    
    def add_item(self, item: dict, track_collected: bool = True) -> None:
        """Add an item to inventory and emit appropriate signals.
        
        Args:
            item: The item to add (will be deep copied to prevent external mutation)
            track_collected: Whether to increment total_collected counter (default True)
        """
        if not item:
            logger.warning("add_item called with empty item")
            return
        
        inventory = self.adhd_buster.setdefault("inventory", [])
        # Deep copy to prevent external code from retaining references that could mutate inventory
        item_copy = deep_copy_item(item)
        inventory.append(item_copy)
        
        # Track total collected
        if track_collected:
            self.adhd_buster["total_collected"] = self.adhd_buster.get("total_collected", 0) + 1
        
        # Cap inventory size (with entity perk bonus) to prevent unbounded growth
        max_size = self.get_max_inventory_size()
        if len(inventory) > max_size:
            self.adhd_buster["inventory"] = inventory[-max_size:]
        
        self._save_config()
        
        self._emit(self.item_added, item_copy)
        self._emit(self.inventory_changed)
    
    def remove_item(self, item_id: str) -> bool:
        """Remove an item from inventory by ID.
        
        Uses flexible matching that handles items without 'id' fields.
        """
        if not item_id:
            logger.warning("remove_item called with empty item_id")
            return False
        
        inventory = self.adhd_buster.get("inventory", [])
        for i, item in enumerate(inventory):
            if self._match_item(item, item_id):
                inventory.pop(i)
                self._save_config()
                self._emit(self.item_removed, item_id)
                self._emit(self.inventory_changed)
                return True
        return False
    
    def equip_item(self, slot: str, item: dict) -> bool:
        """Equip an item to a slot.
        
        Args:
            slot: Equipment slot (must be a valid slot name)
            item: Item to equip (will be deep copied to prevent external mutation)
        
        Returns:
            True if equipped successfully, False on validation failure
        """
        if not slot:
            logger.warning("equip_item called with empty slot")
            return False
        if not item or not isinstance(item, dict):
            logger.warning(f"equip_item called with invalid item: {item}")
            return False
        if slot not in self.VALID_SLOTS:
            logger.warning(f"equip_item called with unknown slot: {slot}")
            # Allow it anyway for forward compatibility with new slots
        
        equipped = self.adhd_buster.setdefault("equipped", {})
        old_item = equipped.get(slot)
        
        # Deep copy to prevent external code from retaining references that could mutate equipped gear
        item_copy = deep_copy_item(item)
        equipped[slot] = item_copy
        self._save_config()
        
        self._emit(self.item_equipped, slot, item_copy)
        self._emit(self.equipment_changed, slot)
        self._emit_power_update()
        return True
    
    def unequip_item(self, slot: str) -> Optional[dict]:
        """Unequip an item from a slot.
        
        Note: Items are always in inventory even when equipped.
        This just removes the equipped reference - no need to add to inventory.
        
        Handles edge cases:
        - Slot not in equipped dict
        - Slot exists but value is None or empty
        """
        equipped = self.adhd_buster.get("equipped", {})
        if slot not in equipped:
            return None
        
        item = equipped.get(slot)
        if not item:  # None or empty dict
            # Just clean up the slot entry
            equipped.pop(slot, None)
            self._save_config()
            self._emit(self.equipment_changed, slot)
            return None
        
        # Remove from equipped (item remains in inventory)
        del equipped[slot]
        self._save_config()
        
        self._emit(self.item_unequipped, slot)
        self._emit(self.equipment_changed, slot)
        self._emit(self.inventory_changed)
        self._emit_power_update()
        
        # Return a copy for the caller (defensive programming)
        return deep_copy_item(item)
    
    def add_coins(self, amount: int) -> int:
        """Add coins and emit signal. Returns new total.
        
        Args:
            amount: Coins to add (must be non-negative, use spend_coins for deductions)
        """
        if amount < 0:
            logger.warning(f"add_coins called with negative amount {amount}, use spend_coins instead")
            return self.adhd_buster.get("coins", 0)
        
        current = self.adhd_buster.get("coins", 0)
        # Cap coins to prevent integer overflow (2 billion max)
        new_total = min(current + amount, 2_000_000_000)
        self.adhd_buster["coins"] = new_total
        self._save_config()
        
        self._emit(self.coins_changed, new_total)
        return new_total
    
    def add_luck_bonus(self, amount: int) -> int:
        """Add luck bonus and return new total.
        
        Args:
            amount: Luck bonus to add (must be non-negative)
        """
        if amount < 0:
            logger.warning(f"add_luck_bonus called with negative amount {amount}")
            return self.adhd_buster.get("luck_bonus", 0)
        
        current = self.adhd_buster.get("luck_bonus", 0)
        # Cap luck bonus to reasonable maximum (10000)
        new_total = min(current + amount, 10_000)
        self.adhd_buster["luck_bonus"] = new_total
        self._save_config()
        self.luck_bonus_changed.emit(new_total)
        return new_total
    
    def decay_luck_bonus(self, amount: int = 1) -> int:
        """Decay luck bonus by specified amount (minimum 0). Returns new total.
        
        This is called hourly to gradually reduce accumulated luck.
        
        Args:
            amount: Amount to decay (default 1 per hour)
        """
        import time
        
        current = self.adhd_buster.get("luck_bonus", 0)
        if current <= 0:
            return 0
        
        new_total = max(0, current - amount)
        self.adhd_buster["luck_bonus"] = new_total
        
        # Track last decay time
        self.adhd_buster["luck_last_decay"] = int(time.time())
        
        self._save_config()
        self.luck_bonus_changed.emit(new_total)
        logger.info(f"Luck bonus decayed: {current} -> {new_total} (-{amount})")
        return new_total
    
    def bulk_remove_items(self, items: List[dict]) -> int:
        """Remove multiple items from inventory. Returns number removed.
        
        Matches items by obtained_at or name+slot+rarity.
        """
        if not items:
            return 0
        
        self.begin_batch()
        try:
            inventory = self.adhd_buster.get("inventory", [])
            
            # Build removal set using multiple identifiers
            items_to_remove = set()
            for i in items:
                if i.get("obtained_at"):
                    items_to_remove.add(("ts", i.get("obtained_at")))
                items_to_remove.add(("key", (i.get("name"), i.get("slot"), i.get("rarity"))))
            
            removed_keys = set()
            new_inventory = []
            removed_count = 0
            
            for item in inventory:
                item_ts = item.get("obtained_at")
                item_key = (item.get("name"), item.get("slot"), item.get("rarity"))
                
                should_remove = False
                if item_ts and ("ts", item_ts) in items_to_remove and ("ts", item_ts) not in removed_keys:
                    should_remove = True
                    removed_keys.add(("ts", item_ts))
                elif not item_ts and ("key", item_key) in items_to_remove:
                    remove_identifier = ("key_instance", item_key)
                    if remove_identifier not in removed_keys:
                        should_remove = True
                        removed_keys.add(remove_identifier)
                
                if should_remove:
                    removed_count += 1
                    self._emit(self.item_removed, item.get("id") or item.get("obtained_at") or "")
                else:
                    new_inventory.append(item)
            
            self.adhd_buster["inventory"] = new_inventory
            self._save_config()
            self._emit(self.inventory_changed)
            
            return removed_count
        finally:
            self.end_batch()
    
    def spend_coins(self, amount: int) -> bool:
        """Spend coins if sufficient. Returns True if successful.
        
        Args:
            amount: Coins to spend (must be non-negative)
        """
        if amount < 0:
            logger.warning(f"spend_coins called with negative amount {amount}")
            return False
        if amount == 0:
            return True  # Spending 0 is always successful
        
        current = self.adhd_buster.get("coins", 0)
        if current >= amount:
            new_total = current - amount
            self.adhd_buster["coins"] = new_total
            self._save_config()
            self._emit(self.coins_changed, new_total)
            return True
        return False
    
    def add_xp(self, amount: int) -> tuple:
        """Add XP and emit signal. Returns (new_xp, new_level, leveled_up).
        
        Args:
            amount: XP to add (must be non-negative)
        """
        if amount < 0:
            logger.warning(f"add_xp called with negative amount {amount}")
            hero = self.adhd_buster.get("hero", {})
            return (hero.get("xp", 0), hero.get("level", 1), False)
        if amount == 0:
            hero = self.adhd_buster.get("hero", {})
            return (hero.get("xp", 0), hero.get("level", 1), False)
        
        hero = self.adhd_buster.get("hero", {})

        # --- Update Total XP (Source of Truth for XP Ring) ---
        current_total = self.adhd_buster.get("total_xp", 0)
        new_total_xp = current_total + amount
        # Cap at 2B to prevent overflow
        new_total_xp = min(new_total_xp, 2_000_000_000)
        self.adhd_buster["total_xp"] = new_total_xp

        # --- Calculate Level ---
        try:
            from gamification import get_level_from_xp
            new_level, xp_in_level, xp_needed, progress = get_level_from_xp(new_total_xp)
            # Use calculated values
            new_xp = xp_in_level
            old_level = hero.get("level", 1)
            leveled_up = new_level > old_level
        except ImportError:
            # Fallback (Legacy Logic)
            current_xp = hero.get("xp", 0)
            current_level = hero.get("level", 1)
            
            new_xp = current_xp + amount
            new_level = current_level
            leveled_up = False
            
            xp_for_next = current_level * 100
            while new_xp >= xp_for_next:
                new_xp -= xp_for_next
                new_level += 1
                leveled_up = True
                xp_for_next = new_level * 100
        
        hero["xp"] = new_xp
        hero["level"] = new_level
        self.adhd_buster["hero"] = hero
        self._save_config()
        
        self._emit(self.xp_changed, new_xp, new_level)
        if leveled_up:
            self._emit(self.hero_changed)
        
        return (new_xp, new_level, leveled_up)
    
    def merge_items(self, item_ids: List[str], result_item: dict) -> bool:
        """Merge items into a new item.
        
        Uses flexible item matching that handles items without 'id' fields.
        Deep copies the result_item to ensure isolation.
        """
        if not item_ids:
            logger.warning("merge_items called with empty item_ids list")
            return False
        if not result_item:
            logger.warning("merge_items called with empty result_item")
            return False
        
        inventory = self.adhd_buster.get("inventory", [])
        
        # Find and remove source items using flexible matching
        items_to_remove = set()
        for item_id in item_ids:
            for idx, item in enumerate(inventory):
                if idx not in items_to_remove and self._match_item(item, item_id):
                    items_to_remove.add(idx)
                    break
        
        if len(items_to_remove) != len(item_ids):
            logger.warning(f"merge_items: only found {len(items_to_remove)}/{len(item_ids)} items")
            return False  # Not all items found
        
        # Remove items in reverse order to maintain indices
        new_inventory = [item for idx, item in enumerate(inventory) if idx not in items_to_remove]
        
        # Deep copy result item to ensure isolation
        result_copy = deep_copy_item(result_item)
        new_inventory.append(result_copy)
        self.adhd_buster["inventory"] = new_inventory
        self._save_config()
        
        self._emit(self.items_merged, result_copy)
        self._emit(self.inventory_changed)
        self._emit_power_update()  # In case merged item is equipped
        return True
    
    def perform_merge(self, items: List[dict], result_item: Optional[dict], 
                      success: bool) -> bool:
        """
        Perform a merge operation - remove source items, add result if successful.
        
        This is the preferred method for UI code to perform merges. It handles:
        - Removing source items by matching obtained_at or name+slot+rarity
        - Adding the result item (deep copied) on success
        - Proper signal emission
        
        Args:
            items: List of source items to remove
            result_item: The result item to add (None if merge failed)
            success: Whether the merge succeeded
        
        Returns:
            True if operation completed successfully
        """
        if not items:
            logger.warning("perform_merge called with empty items list")
            return False
        
        self.begin_batch()
        try:
            inventory = self.adhd_buster.get("inventory", [])
            
            # Build removal set using multiple identifiers
            items_to_remove = set()
            for i in items:
                # Use timestamp if available
                if i.get("obtained_at"):
                    items_to_remove.add(("ts", i.get("obtained_at")))
                # Also add name+slot+rarity as fallback identifier
                items_to_remove.add(("key", (i.get("name"), i.get("slot"), i.get("rarity"))))
            
            # Track which items have been removed (to handle duplicates correctly)
            removed_keys = set()
            new_inventory = []
            for item in inventory:
                item_ts = item.get("obtained_at")
                item_key = (item.get("name"), item.get("slot"), item.get("rarity"))
                
                # Check if this item should be removed
                should_remove = False
                if item_ts and ("ts", item_ts) in items_to_remove and ("ts", item_ts) not in removed_keys:
                    should_remove = True
                    removed_keys.add(("ts", item_ts))
                elif not item_ts and ("key", item_key) in items_to_remove:
                    # For items without timestamp, remove only one instance
                    remove_identifier = ("key_instance", item_key)
                    if remove_identifier not in removed_keys:
                        should_remove = True
                        removed_keys.add(remove_identifier)
                
                if not should_remove:
                    new_inventory.append(item)
            
            # Add result item if merge succeeded
            if success and result_item:
                result_copy = deep_copy_item(result_item)
                new_inventory.append(result_copy)
                self._emit(self.items_merged, result_copy)
            
            self.adhd_buster["inventory"] = new_inventory
            self._save_config()
            self._emit(self.inventory_changed)
            self._emit_power_update()
            
            return True
        finally:
            self.end_batch()
    
    def set_all_equipped(self, new_equipped: Dict[str, dict]) -> None:
        """
        Replace all equipped items with a new configuration.
        
        This is used by gear optimization to apply a new loadout.
        Deep copies all items to ensure isolation.
        
        Args:
            new_equipped: Dict mapping slot names to item dicts
        """
        self.begin_batch()
        try:
            # Deep copy each equipped item
            copied_equipped = {}
            for slot, item in new_equipped.items():
                if item and isinstance(item, dict):
                    copied_equipped[slot] = deep_copy_item(item)
                else:
                    copied_equipped[slot] = None
            
            # Remove None values
            copied_equipped = {k: v for k, v in copied_equipped.items() if v}
            
            self.adhd_buster["equipped"] = copied_equipped
            self._save_config()
            
            # Emit signal for each slot that changed
            for slot in copied_equipped:
                self._emit(self.equipment_changed, slot)
            self._emit_power_update()
        finally:
            self.end_batch()
    
    def set_story(self, story_id: str) -> None:
        """Change the active story theme."""
        self.adhd_buster["selected_story"] = story_id
        self._save_config()
        self._emit(self.story_changed, story_id)
        self._emit(self.full_refresh_required)
    
    def _emit_power_update(self):
        """Calculate and emit current power."""
        try:
            from gamification import calculate_character_power, get_power_breakdown
            power = calculate_character_power(self.adhd_buster)
            self._log_change("power_update", f"power={power}")
            self._emit(self.power_changed, power)
            
            # Also emit set bonus changes
            breakdown = get_power_breakdown(self.adhd_buster)
            self._emit(self.set_bonus_changed, breakdown)
        except ImportError:
            pass
    
    def notify_session_reward(self, reward_data: dict) -> None:
        """Notify that a session reward was earned."""
        self._log_change("session_reward", str(reward_data))
        self._emit(self.session_reward_earned, reward_data)
        self._emit(self.inventory_changed)
        self._emit_power_update()
    
    def request_full_refresh(self):
        """Request all connected components to do a full refresh."""
        self._log_change("full_refresh_requested", "")
        self._emit(self.full_refresh_required)
    
    # === Convenience Methods for Complex Operations ===
    
    def award_session_rewards(self, item: dict, coins: int, xp: int, 
                               streak_bonus: int = 0, strategic_bonus: bool = False) -> dict:
        """
        Award all session completion rewards atomically.
        
        This batches all reward operations together for a single UI update.
        Returns a summary of what was awarded.
        """
        self.begin_batch()
        try:
            # Add item to inventory
            if item:
                self.add_item(item)
            
            # Add coins
            total_coins = coins
            if streak_bonus:
                total_coins += streak_bonus
            new_coin_total = self.add_coins(total_coins)
            
            # Add XP
            xp_result = self.add_xp(xp)
            
            result = {
                "item": item,
                "coins_earned": total_coins,
                "coin_total": new_coin_total,
                "xp_earned": xp,
                "new_xp": xp_result[0],
                "new_level": xp_result[1],
                "leveled_up": xp_result[2],
                "streak_bonus": streak_bonus,
                "strategic_bonus": strategic_bonus,
            }
            
            self._log_change("session_rewards", str(result))
            return result
            
        finally:
            self.end_batch()
    
    def swap_equipped_item(self, slot: str, new_item: Optional[dict]) -> Optional[dict]:
        """
        Swap equipped item in a slot. Returns the previously equipped item.
        
        If new_item is None, just unequips the current item.
        Items stay in inventory when equipped (visible with Eq checkmark).
        
        Edge cases handled:
        - Empty slot value
        - new_item not in inventory (still equips, as item may come from other sources)
        """
        if not slot:
            logger.warning("swap_equipped_item called with empty slot")
            return None
        
        self.begin_batch()
        try:
            equipped = self.adhd_buster.setdefault("equipped", {})
            self.adhd_buster.setdefault("inventory", [])
            
            old_item = equipped.get(slot)
            
            # Emit unequip signal for old item (item stays in inventory)
            if old_item and isinstance(old_item, dict):
                self._emit(self.item_unequipped, slot)
            
            # Equip new item (item stays in inventory, just reference in equipped dict)
            if new_item and isinstance(new_item, dict):
                # Deep copy the new item to ensure equipped version is isolated
                equipped[slot] = deep_copy_item(new_item)
                self._emit(self.item_equipped, slot, equipped[slot])
            else:
                # Just unequip
                if slot in equipped:
                    del equipped[slot]
            
            self._save_config()
            self._emit(self.equipment_changed, slot)
            self._emit(self.inventory_changed)
            self._emit_power_update()
            
            self._log_change("swap_equipped", f"slot={slot}, old={old_item}, new={new_item}")
            return old_item if old_item and isinstance(old_item, dict) else None
            
        finally:
            self.end_batch()
    
    def sell_item(self, item_id: str, sell_value: int) -> bool:
        """Sell an item for coins.
        
        Args:
            item_id: ID of item to sell
            sell_value: Coins to receive (must be non-negative)
        """
        if not item_id:
            logger.warning("sell_item called with empty item_id")
            return False
        if sell_value < 0:
            logger.warning(f"sell_item called with negative sell_value: {sell_value}")
            sell_value = 0  # Still remove item, just don't give negative coins
        
        self.begin_batch()
        try:
            if self.remove_item(item_id):
                if sell_value > 0:
                    self.add_coins(sell_value)
                self._log_change("sell_item", f"id={item_id}, value={sell_value}")
                return True
            return False
        finally:
            self.end_batch()
    
    def bulk_sell_items(self, item_ids: List[str], total_value: int) -> int:
        """Sell multiple items. Returns number of items successfully sold."""
        self.begin_batch()
        try:
            sold_count = 0
            for item_id in item_ids:
                if self.remove_item(item_id):
                    sold_count += 1
            
            if sold_count > 0:
                self.add_coins(total_value)
            
            self._log_change("bulk_sell", f"sold={sold_count}/{len(item_ids)}, value={total_value}")
            return sold_count
        finally:
            self.end_batch()
    
    def get_current_power(self) -> int:
        """Get current character power (convenience method)."""
        try:
            from gamification import calculate_character_power
            return calculate_character_power(self.adhd_buster)
        except ImportError:
            return 0
    
    def get_current_coins(self) -> int:
        """Get current coin count (convenience method)."""
        return self.adhd_buster.get("coins", 0)
    
    def force_save(self) -> None:
        """Force save config and emit saved signal."""
        self._blocker.save_config()
        self._emit(self.config_saved)
        self._log_change("force_save", "config saved")

    def award_items_batch(self, items: List[dict], coins: int = 0, 
                           auto_equip: bool = True, source: str = "") -> dict:
        """
        Award multiple items in a batch with optional auto-equip to empty slots.
        
        This is the preferred method for tracker rewards (sleep, activity, weight, etc.)
        that may award multiple items at once.
        
        Args:
            items: List of items to add to inventory
            coins: Optional coins to award
            auto_equip: Whether to auto-equip items to empty slots
            source: Optional source label for logging
        
        Returns:
            dict with awarded items and coins info
        """
        if not items and coins == 0:
            return {"items": [], "coins": 0, "equipped": []}
        
        self.begin_batch()
        try:
            equipped_items = []
            added_items = []  # Track what was actually added
            inventory = self.adhd_buster.setdefault("inventory", [])
            equipped = self.adhd_buster.setdefault("equipped", {})
            
            for item in items:
                if not item:
                    continue
                
                # Deep copy to prevent mutation leaking
                item_copy = deep_copy_item(item)
                
                # Always add to inventory first
                inventory.append(item_copy)
                added_items.append(item_copy)
                self._emit(self.item_added, item_copy)
                
                # Auto-equip to empty slot if enabled
                if auto_equip:
                    slot = item_copy.get("slot")
                    if slot and not equipped.get(slot):
                        # Equip a deep copy (inventory and equipped should be isolated)
                        equipped_copy = deep_copy_item(item_copy)
                        equipped[slot] = equipped_copy
                        equipped_items.append(equipped_copy)
                        self._emit(self.item_equipped, slot, equipped_copy)
            
            # Update total collected
            if items:
                self.adhd_buster["total_collected"] = self.adhd_buster.get("total_collected", 0) + len(items)
            
            # Cap inventory size to prevent unbounded growth
            if len(inventory) > self.MAX_INVENTORY_SIZE:
                self.adhd_buster["inventory"] = inventory[-self.MAX_INVENTORY_SIZE:]
            
            # Add coins
            new_coin_total = None
            if coins > 0:
                new_coin_total = self.add_coins(coins)
            
            # Save and emit (deferred if in batch, otherwise save now)
            self._save_config()
            self._emit(self.inventory_changed)
            self._emit_power_update()
            
            self._log_change("award_items_batch", f"source={source}, items={len(items)}, coins={coins}")
            
            return {
                "items": added_items,  # Return the copies that were actually added
                "coins": coins,
                "coin_total": new_coin_total,
                "equipped": equipped_items
            }
        finally:
            self.end_batch()


# Singleton instance (created when needed)
# Note: This is accessed from the main Qt thread only. If background threads
# need state access, use Qt signals/slots for thread-safe communication.
_game_state: Optional[GameStateManager] = None
_init_lock = False  # Simple guard to detect re-entrancy issues


def get_game_state(blocker=None) -> Optional[GameStateManager]:
    """Get the global game state manager instance.
    
    Thread Safety: Must be called from the main Qt thread only.
    """
    global _game_state, _init_lock
    if _game_state is None and blocker is not None:
        if _init_lock:
            logger.warning("Recursive game state initialization detected!")
            return None
        _init_lock = True
        try:
            _game_state = GameStateManager(blocker)
        finally:
            _init_lock = False
    return _game_state


def init_game_state(blocker) -> GameStateManager:
    """Initialize the global game state manager.
    
    Thread Safety: Must be called from the main Qt thread only.
    """
    global _game_state
    _game_state = GameStateManager(blocker)
    return _game_state


def reset_game_state() -> None:
    """Reset the global game state (for testing)."""
    global _game_state
    _game_state = None
