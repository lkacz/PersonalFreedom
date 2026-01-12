# Architecture Analysis: Improving State Updates in Personal Liberty

## Current Issues Identified

### 1. **Imperative Refresh Pattern (Root Cause)**
The app uses ~25+ manual `refresh_all()` calls scattered throughout the codebase. Every time state changes, you must remember to call refresh. Missing even one leads to stale UI.

**Problem locations found:**
- [focus_blocker_qt.py#L1421](focus_blocker_qt.py#L1421) - After session
- [focus_blocker_qt.py#L3513](focus_blocker_qt.py#L3513) - After merge
- [focus_blocker_qt.py#L10944](focus_blocker_qt.py#L10944) - Timer-based
- ...and many more

### 2. **No Centralized State Management**
```
blocker.adhd_buster["inventory"]  → Inventory data
blocker.adhd_buster["equipped"]   → Equipment data  
blocker.adhd_buster["coins"]      → Currency
blocker.stats                     → Statistics
```
Changes to these dictionaries don't notify the UI automatically.

### 3. **Qt Signals Underutilized**
Only 3 timer-related signals exist. Game state changes (items, power, coins) have no signal infrastructure.

---

## Recommended Solutions

### Option A: Add Qt Signal Layer (Minimal Changes) ✅ RECOMMENDED

I've created `game_state.py` with a reactive state manager. Here's how to integrate:

**1. Initialize in main window:**
```python
from game_state import init_game_state

class FocusBlockerWindow(QtWidgets.QMainWindow):
    def __init__(self):
        ...
        self.game_state = init_game_state(self.blocker)
```

**2. Connect UI components:**
```python
class ADHDBusterTab(QtWidgets.QWidget):
    def __init__(self, blocker, parent=None):
        super().__init__(parent)
        ...
        # Get state manager and connect signals
        from game_state import get_game_state
        self.state = get_game_state()
        if self.state:
            self.state.power_changed.connect(self._update_power_display)
            self.state.inventory_changed.connect(self._refresh_inventory)
            self.state.equipment_changed.connect(self._refresh_slot)
            self.state.coins_changed.connect(self._update_coin_label)
```

**3. Use state manager for modifications:**
```python
# Instead of:
self.blocker.adhd_buster["inventory"].append(item)
self.blocker.save_config()
self.refresh_all()  # Easy to forget!

# Do this:
self.state.add_item(item)  # Auto-saves and emits signals
```

**Benefits:**
- Minimal code changes to existing structure
- Automatic UI updates via Qt's proven signal system
- Batch operations for multiple changes
- Easy debugging (can log all state changes)

---

### Option B: Consider Alternative Frameworks (Major Refactor)

If you're considering a larger rewrite, here are game-oriented alternatives:

| Framework | Best For | Pros | Cons |
|-----------|----------|------|------|
| **Pygame + PyQt overlay** | Real-time game elements | Smooth animations, game loop | Complex hybrid, two event loops |
| **Arcade (Python)** | 2D game with UI | Built for games, sprites | Would need full UI rewrite |
| **PyQt + QML** | Declarative UI | Data binding, reactive | Learning curve, QML syntax |
| **NiceGUI/Flet** | Web-based Python UI | Modern reactive, hot reload | Web overhead, different paradigm |
| **Ursina** | 3D/2D games | Game-focused, entity system | Overkill for this app |

**My Recommendation: Stick with PySide6 + Signal Pattern**

Qt/PySide6 is actually excellent for game-like apps when used properly. The issue isn't the framework—it's the current manual refresh pattern.

---

## Quick Fixes for Common Missing Updates

### Power Not Updating After Equip
```python
# In _on_slot_change method, ensure:
def _on_slot_change(self, slot: str, combo: QtWidgets.QComboBox):
    ...
    self.blocker.save_config()
    self._refresh_character()  # ← This updates power display
    # Better: self.state.equip_item(slot, item)
```

### Coins Not Updating After Session
```python
# In _on_session_complete, ensure:
def _on_session_complete(self, elapsed_seconds: int):
    ...
    self._update_coin_display()  # ← Ensure this is called
    if hasattr(self, 'adhd_tab'):
        self.adhd_tab.refresh_all()
```

### Inventory Not Showing New Items
```python
# After awarding items, force inventory refresh:
if hasattr(self, 'adhd_tab'):
    self.adhd_tab._refresh_inventory()
    self.adhd_tab._refresh_all_slot_combos()
```

---

## Migration Path

### Phase 1: Add State Manager (1 day)
1. Import `game_state.py` 
2. Initialize in main window
3. Connect signals in ADHDBusterTab

### Phase 2: Migrate Critical Paths (2-3 days)
1. Replace direct `adhd_buster` modifications with state manager calls
2. Remove redundant `refresh_all()` calls as signals take over
3. Test each game action (equip, merge, session complete)

### Phase 3: Full Integration (1 week)
1. All state modifications go through state manager
2. Add batch operations for complex multi-step actions
3. Add logging/debugging for state changes

---

## Example: Session Complete with Proper Updates

```python
def _on_session_complete(self, elapsed_seconds: int):
    """Handle session completion with proper state propagation."""
    from game_state import get_game_state
    state = get_game_state()
    
    if state:
        # Batch all changes together
        state.begin_batch()
        
        # Award item
        item = generate_random_item(elapsed_seconds)
        state.add_item(item)
        
        # Award coins
        coins = calculate_coin_reward(elapsed_seconds)
        state.add_coins(coins)
        
        # Award XP
        xp = calculate_xp_reward(elapsed_seconds)
        state.add_xp(xp)
        
        # Emit all signals at once
        state.end_batch()
        
        # Notify for reward popup
        state.notify_session_reward({
            "item": item,
            "coins": coins,
            "xp": xp
        })
    
    # Other non-gamification updates
    self.blocker.load_stats()
    if hasattr(self, 'stats_tab'):
        self.stats_tab.refresh()
```

---

## Conclusion

**The framework (PySide6/Qt) is fine for game-like apps.** The issue is the manual refresh pattern. 

Implementing the signal-based state manager will:
1. ✅ Eliminate forgotten refresh calls
2. ✅ Provide immediate UI feedback
3. ✅ Make debugging easier (log state changes)
4. ✅ Enable proper separation of concerns
5. ✅ Scale better as you add more features

The `game_state.py` file I created gives you a solid foundation. Start integrating it with the ADHD Buster tab first, then expand to other components.
