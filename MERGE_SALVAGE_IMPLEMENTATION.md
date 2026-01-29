# Merge Materials System - Implementation Guide

## Overview

This document provides a comprehensive analysis and implementation recommendations for the **Merge Materials System** (also called "crafting leftovers" or "salvage materials"). This system rewards players with materials when using the Lucky Merge feature.

---

## 1. Current State Analysis

### 1.1 Two "Materials" Systems Exist

| System | Purpose | Storage Path | Source |
|--------|---------|--------------|--------|
| **Merge Materials** | Reward for merging items | `adhd_buster["materials"]` | Lucky Merge dialog |
| **City Materials** | Building construction resource | `adhd_buster["city"]["resources"]["materials"]` | Weight logging, exercise |

**Key Insight**: These are **completely separate systems** with different purposes, stored at different paths. There is **no data conflict**, but the shared "materials" terminology creates confusion.

### 1.2 Current Mechanics

```
MERGE MATERIALS FORMULA:
┌─────────────────────────────────────────────────────────────┐
│ Items < 10:   10% chance for +1 material                    │
│ Items = 10:   Guaranteed +1 material                        │
│ Items > 10:   Guaranteed +1 + 10% per extra item            │
│                                                             │
│ Example (15 items): 1 guaranteed + 5 × 10% = ~1.5 expected │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Current Implementation Files

| File | Component | Status |
|------|-----------|--------|
| [game_state.py](game_state.py#L95) | `materials_changed` signal | ✅ Defined |
| [game_state.py](game_state.py#L168) | `materials` property | ✅ Working |
| [game_state.py](game_state.py#L484) | `add_materials()` method | ✅ Working |
| [merge_dialog.py](merge_dialog.py#L59) | `calculate_merge_materials()` | ✅ Working |
| [merge_dialog.py](merge_dialog.py#L1664) | Display expected materials | ✅ Working |
| [merge_dialog.py](merge_dialog.py#L1756) | Roll for actual materials | ✅ Working |
| [merge_dialog.py](merge_dialog.py#L2575) | Show in success message | ✅ Working |
| [merge_dialog.py](merge_dialog.py#L2657) | Show in failure message | ✅ Working |
| [focus_blocker_qt.py](focus_blocker_qt.py#L19078) | Process earned materials | ✅ Working |

---

## 2. Problems Identified

### 2.1 ⚠️ CRITICAL: Naming Collision

**Problem**: Both systems use "materials" which will confuse developers and potentially users.

```python
# Merge Materials (new)
self.adhd_buster["materials"] = 42

# City Materials (existing)
self.adhd_buster["city"]["resources"]["materials"] = 75
```

**Risk**: Future code may accidentally access the wrong materials pool.

### 2.2 ⚠️ MEDIUM: No Total Display

**Problem**: Players earn materials but have no visibility into their accumulated total.

- The `materials_changed` signal is emitted but never connected
- No UI shows "Total Materials: X"
- Players cannot see their reward grow over time

### 2.3 ⚠️ MEDIUM: No Spending Mechanism

**Problem**: Materials accumulate indefinitely with no purpose.

- Cap at 999,999 (reasonable)
- But no way to spend them → eventually feels pointless

### 2.4 ⚠️ LOW: No Test Coverage

**Problem**: The calculation and state management logic has no unit tests.

---

## 3. Recommended Architecture

### 3.1 Rename to "Salvage" 

**Rationale**: Avoid confusion with City materials while maintaining thematic fit.

| Current Name | Proposed Name | Reason |
|--------------|---------------|--------|
| `materials` | `salvage` | Different from city "materials", fits "leftovers" theme |
| `materials_changed` | `salvage_changed` | Consistency |
| `add_materials()` | `add_salvage()` | Consistency |

**Alternative Names Considered**:
- `merge_scraps` - Descriptive but awkward
- `crafting_essence` - Too "magical" for underdog theme
- `scrap_metal` - Too literal, doesn't fit all themes
- **`salvage`** - ✅ Best fit: implies recovery from merging, distinct from city materials

### 3.2 Data Schema

```json
{
  "adhd_buster": {
    "salvage": 42,                    // Merge leftovers (renamed)
    "coins": 500,
    "level": 10,
    "city": {
      "resources": {
        "water": 100,
        "materials": 75               // City construction materials
      }
    }
  }
}
```

### 3.3 File Changes Required

#### game_state.py

```python
# Line 95: Rename signal
salvage_changed = QtCore.Signal(int)  # Salvage from merging

# Line 168: Rename property
@property
def salvage(self) -> int:
    """Get current salvage count (merge leftovers)."""
    return self.adhd_buster.get("salvage", 0)

# Line 484: Rename method
def add_salvage(self, amount: int) -> int:
    """Add salvage (merge leftovers) and emit signal."""
    if amount <= 0:
        return self.adhd_buster.get("salvage", 0)
    
    current = self.adhd_buster.get("salvage", 0)
    new_total = min(current + amount, 999_999)
    self.adhd_buster["salvage"] = new_total
    self._save_config()
    
    self._emit(self.salvage_changed, new_total)
    return new_total
```

#### merge_dialog.py

```python
# Line 59: Rename function
def calculate_merge_salvage(item_count: int, do_roll: bool = False) -> tuple:
    """Calculate salvage (leftovers) from a merge based on item count."""
    # ... (same logic)

# UI text changes:
# "🧱 +1 material" → "🔩 +1 salvage"
# "🧱 10% chance" → "🔩 10% chance"
```

#### focus_blocker_qt.py

```python
# Line 19078: Update processing
salvage_earned = result.get("salvage_earned", 0)
if salvage_earned > 0:
    self._game_state.add_salvage(salvage_earned)
```

---

## 4. Spending Mechanisms

### 4.1 Immediate Implementation (Phase 1)

**Guaranteed Merge Success** - Spend salvage to guarantee a merge succeeds.

```python
SALVAGE_GUARANTEE_COST = 50  # Spend 50 salvage to guarantee success

# In merge_dialog.py execute_merge():
if self.guarantee_enabled:
    is_success = True  # Bypass roll
    # Deduct salvage via game_state.deduct_salvage()
```

**UI**: Add checkbox "🔩 Guarantee Success (50 salvage)" next to boost options.

### 4.2 Future Spending Options (Phase 2+)

| Feature | Cost | Description |
|---------|------|-------------|
| **Reroll Item Slot** | 25 salvage | Change which slot a merged item goes to |
| **Reroll Item Name** | 10 salvage | Get a new random name for item |
| **Add Lucky Attribute** | 30 salvage | Force +1 lucky attribute on result |
| **Enhance Tier** | 100 salvage | +1 tier to ANY item (not just merged) |
| **Convert to Coins** | 10 salvage | Exchange 10 salvage → 15 coins |

### 4.3 Integration with City System

**Option A: Keep Separate** (Recommended)
- Salvage = Merge system currency
- City Materials = Construction currency
- Clear separation of concerns

**Option B: Allow Conversion**
- Add "Recycling Center" city building
- Converts salvage to city materials (e.g., 5 salvage → 1 material)
- Creates connection between systems

---

## 5. UI Display Recommendations

### 5.1 Merge Dialog Header

Add total salvage display at the top of the merge dialog:

```
┌─────────────────────────────────────────────────────────┐
│ ⚡ Lucky Merge                    🔩 Your Salvage: 142 │
├─────────────────────────────────────────────────────────┤
│ [Items being merged...]                                 │
```

### 5.2 ADHD Buster Tab Status

Add salvage to the character status display:

```
┌─────────────────────────────────────────────────────────┐
│ 🦸 HERO  ⚔ 1,250 Power  🪙 500 Coins  🔩 142 Salvage   │
└─────────────────────────────────────────────────────────┘
```

### 5.3 Toast Notifications

When earning salvage, show a brief toast:

```
🔩 +3 Salvage (leftovers from merge)
```

---

## 6. Implementation Order

### Phase 1: Rename & Display (Essential)

1. **Rename all references** from `materials` to `salvage`
   - game_state.py: signal, property, method
   - merge_dialog.py: function, UI text, result keys
   - focus_blocker_qt.py: processing code
   
2. **Add total display** in merge dialog header
   - Show "🔩 Your Salvage: X" next to dialog title
   
3. **Add unit tests** for calculation and state management

### Phase 2: Basic Spending (Value Addition)

4. **Add "Guarantee Success"** option
   - Checkbox in merge dialog
   - Costs 50 salvage
   - Bypasses success roll

5. **Add salvage toast notifications**
   - Show when salvage is earned
   - Connect to `salvage_changed` signal

### Phase 3: Advanced Features (Future)

6. **Add more spending options** (reroll, enhance, convert)
7. **Consider city integration** (Recycling Center building)
8. **Add salvage-specific achievements**

---

## 7. Migration Strategy

### 7.1 Data Migration

For existing users with `materials` data:

```python
def migrate_materials_to_salvage(adhd_buster: dict) -> None:
    """One-time migration from materials to salvage."""
    if "materials" in adhd_buster and "salvage" not in adhd_buster:
        adhd_buster["salvage"] = adhd_buster.pop("materials")
        logger.info(f"Migrated materials → salvage: {adhd_buster['salvage']}")
```

Call this in `GameStateManager.__init__()` before first access.

### 7.2 Backward Compatibility

The property can provide fallback:

```python
@property
def salvage(self) -> int:
    # Check new key first, fall back to old key for migration
    if "salvage" in self.adhd_buster:
        return self.adhd_buster["salvage"]
    return self.adhd_buster.get("materials", 0)
```

---

## 8. Test Plan

### 8.1 Unit Tests

```python
# tests/test_merge_salvage.py

class TestCalculateMergeSalvage:
    def test_under_10_items_no_roll(self):
        """Expected value is 0.10 for < 10 items."""
        expected, desc = calculate_merge_salvage(5, do_roll=False)
        assert expected == 0.10
        assert "10% chance" in desc

    def test_exactly_10_items_no_roll(self):
        """Expected value is 1.0 for exactly 10 items."""
        expected, desc = calculate_merge_salvage(10, do_roll=False)
        assert expected == 1.0
        assert "Guaranteed +1" in desc

    def test_over_10_items_no_roll(self):
        """Expected value includes bonus for extra items."""
        expected, desc = calculate_merge_salvage(15, do_roll=False)
        assert expected == 1.5  # 1 + (5 * 0.10)

    @patch('random.random', return_value=0.05)
    def test_under_10_items_roll_success(self, mock_random):
        """10% roll succeeds when random < 0.10."""
        actual, desc = calculate_merge_salvage(5, do_roll=True)
        assert actual == 1
        assert "+1" in desc

    @patch('random.random', return_value=0.15)
    def test_under_10_items_roll_failure(self, mock_random):
        """10% roll fails when random >= 0.10."""
        actual, desc = calculate_merge_salvage(5, do_roll=True)
        assert actual == 0


class TestAddSalvage:
    def test_adds_to_existing(self, game_state):
        game_state.adhd_buster["salvage"] = 10
        result = game_state.add_salvage(5)
        assert result == 15
        assert game_state.salvage == 15

    def test_caps_at_max(self, game_state):
        game_state.adhd_buster["salvage"] = 999_990
        result = game_state.add_salvage(100)
        assert result == 999_999

    def test_ignores_negative(self, game_state):
        game_state.adhd_buster["salvage"] = 10
        result = game_state.add_salvage(-5)
        assert result == 10

    def test_emits_signal(self, game_state, qtbot):
        with qtbot.waitSignal(game_state.salvage_changed):
            game_state.add_salvage(10)
```

### 8.2 Integration Tests

```python
class TestMergeDialogSalvageIntegration:
    def test_salvage_displayed_before_merge(self, merge_dialog):
        """Merge dialog shows expected salvage."""
        assert "🔩" in merge_dialog.materials_info.text()

    def test_salvage_earned_on_success(self, merge_dialog, mock_random):
        """Successful merge awards salvage."""
        mock_random.return_value = 0.0  # Guarantee success
        merge_dialog.execute_merge()
        assert merge_dialog.merge_result["salvage_earned"] >= 0

    def test_salvage_earned_on_failure(self, merge_dialog, mock_random):
        """Failed merge still awards salvage."""
        mock_random.return_value = 0.99  # Guarantee failure
        merge_dialog.execute_merge()
        assert merge_dialog.merge_result["salvage_earned"] >= 0
```

---

## 9. Conclusion

### Summary of Recommendations

| Priority | Action | Effort |
|----------|--------|--------|
| **HIGH** | Rename `materials` → `salvage` | Medium |
| **HIGH** | Add total salvage display | Low |
| **MEDIUM** | Add "Guarantee Success" spending | Medium |
| **MEDIUM** | Add unit tests | Medium |
| **LOW** | Add more spending options | High |
| **LOW** | City integration | High |

### Key Decisions

1. **Rename to "salvage"** - Avoids confusion with city materials
2. **Keep systems separate** - Clear separation of concerns
3. **Add display first** - Players should see their rewards
4. **Add spending later** - Gives purpose to accumulation

### Implementation Complexity

- **Phase 1 (Rename + Display)**: ~2-3 hours
- **Phase 2 (Basic Spending)**: ~3-4 hours  
- **Phase 3 (Advanced Features)**: ~8-10 hours

---

*Document: Merge Materials System Implementation Guide*
*Status: Ready for implementation*
*Files to modify: game_state.py, merge_dialog.py, focus_blocker_qt.py*
