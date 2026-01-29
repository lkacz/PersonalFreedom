# Materials System Scrutiny Report

## Executive Summary

The **Merge Materials System** was successfully implemented as a reward mechanism for the Lucky Merge feature. This scrutiny confirms the system is correctly implemented with proper user isolation and persistence. However, there is a **naming overlap** with the existing City Materials system that could cause confusion - though the data is stored separately and there is **no actual conflict**.

---

## 1. System Overview

### 1.1 Merge Materials (NEW)
- **Purpose**: Reward players with "leftover materials" when merging items
- **Storage Location**: `adhd_buster["materials"]`
- **Signal**: `GameStateManager.materials_changed`
- **Method**: `GameStateManager.add_materials(amount)`

### 1.2 City Materials (EXISTING)
- **Purpose**: Resource for constructing/upgrading buildings in the City system
- **Storage Location**: `adhd_buster["city"]["resources"]["materials"]`
- **Method**: `add_city_resource(adhd_buster, "materials", amount)`

### 1.3 Key Distinction
| Aspect | Merge Materials | City Materials |
|--------|-----------------|----------------|
| Storage | `adhd_buster["materials"]` | `adhd_buster["city"]["resources"]["materials"]` |
| Source | Lucky Merge (crafting leftovers) | Weight logging, exercise, activities |
| Use | TBD (future crafting?) | Building construction/upgrades |
| Signal | `materials_changed` | `city_resources_changed` |
| Max Cap | 999,999 | No cap (stockpile) |

---

## 2. Implementation Analysis

### 2.1 Core Logic: `calculate_merge_materials()` [merge_dialog.py](merge_dialog.py#L59-L120)

```python
def calculate_merge_materials(item_count: int, do_roll: bool = False) -> tuple:
    """
    Rules:
    - < 10 items: 10% chance of +1 material
    - >= 10 items: guaranteed +1 material  
    - Each item above 10: 10% chance of +1 additional material
    """
```

**Assessment**: ✅ Correctly implements the specified rules.

### 2.2 State Management: `add_materials()` [game_state.py](game_state.py#L484-L506)

```python
def add_materials(self, amount: int) -> int:
    if amount <= 0:
        return self.adhd_buster.get("materials", 0)
    
    current = self.adhd_buster.get("materials", 0)
    new_total = min(current + amount, 999_999)  # Cap at 999,999
    self.adhd_buster["materials"] = new_total
    self._save_config()  # Persist immediately
    
    self._emit(self.materials_changed, new_total)
    return new_total
```

**Assessment**: ✅ Robust implementation with:
- Guard against negative/zero amounts
- Cap at reasonable maximum
- Immediate persistence via `_save_config()`
- Signal emission for reactive UI

### 2.3 Signal Definition [game_state.py](game_state.py#L95)

```python
materials_changed = QtCore.Signal(int)  # New materials total
```

**Assessment**: ✅ Signal defined correctly.

### 2.4 Property Accessor [game_state.py](game_state.py#L168-L170)

```python
@property
def materials(self) -> int:
    return self.adhd_buster.get("materials", 0)
```

**Assessment**: ✅ Provides clean access to current materials count.

---

## 3. UI Integration

### 3.1 Merge Dialog Display

| Location | Display |
|----------|---------|
| [merge_dialog.py#L1670-L1676](merge_dialog.py#L1670) | Expected materials next to button: "🧱 +1 guaranteed" or "🧱 10% chance" |
| [merge_dialog.py#L2573-L2575](merge_dialog.py#L2575) | Success message: "🧱 +X material(s) (leftovers)" |
| [merge_dialog.py#L2657-L2662](merge_dialog.py#L2662) | Failure message: "🧱 +X material(s) (salvaged leftovers)" |

**Assessment**: ✅ Materials are displayed at all relevant points in the merge flow.

### 3.2 Processing in Main Window [focus_blocker_qt.py](focus_blocker_qt.py#L19078-L19081)

```python
materials_earned = result.get("materials_earned", 0)
if materials_earned > 0:
    self._game_state.add_materials(materials_earned)
```

**Assessment**: ✅ Materials are correctly processed after merge completion.

### 3.3 Missing UI: Total Materials Display

⚠️ **ISSUE FOUND**: There is currently **no UI displaying the player's total merge materials**.

The `materials_changed` signal is emitted but never connected to any UI handler. Players can see materials earned per merge, but have no way to see their accumulated total.

**Recommendation**: Add a materials display to one of:
1. ADHD Buster tab header (next to power/coins/level)
2. A new "Crafting" or "Workshop" section
3. The merge dialog itself as a header "Your Materials: X 🧱"

---

## 4. User Switching & Data Isolation

### 4.1 Storage Path
Materials are stored at `adhd_buster["materials"]` where `adhd_buster` is the user-specific dictionary loaded from `config.json` under the user's profile.

### 4.2 User Switch Handling [focus_blocker_qt.py](focus_blocker_qt.py#L25801-L26000)

The `_reload_user()` method:
1. Creates new `BlockerCore(username=new_username)` - loads new user's `adhd_buster`
2. Calls `reset_game_state()` - clears singleton
3. Creates new `GameStateManager` with new `blocker.adhd_buster`

**Assessment**: ✅ Materials are correctly isolated per user. When switching users:
- Old user's materials remain in their saved config
- New user's materials are loaded fresh from their config
- The `GameStateManager.materials` property returns the new user's value

### 4.3 Persistence
Materials are saved immediately via `_save_config()` in `add_materials()`.

**Assessment**: ✅ No risk of data loss on app close.

---

## 5. Integration Across Tabs

| Tab | Materials Integration | Status |
|-----|----------------------|--------|
| ADHD Buster | Merge dialog shows earned materials | ✅ |
| City | Uses separate city materials (no conflict) | ✅ |
| Entitidex | No integration | N/A |
| Story | No integration | N/A |
| Timer | No integration | N/A |
| Other Tabs | No integration | N/A |

**Note**: Merge materials are currently a standalone resource with no spending mechanism.

---

## 6. Potential Issues & Recommendations

### 6.1 ⚠️ Naming Confusion (Medium Priority)

**Problem**: Two different "materials" systems could confuse developers and users:
- Merge Materials: `adhd_buster["materials"]`
- City Materials: `adhd_buster["city"]["resources"]["materials"]`

**Recommendation**: Consider renaming merge materials to a distinct name:
- `merge_scraps`
- `salvage`
- `crafting_leftovers`
- `essence`

**Impact**: Would require updating:
- `game_state.py`: Property, signal, method names
- `merge_dialog.py`: Display text and result keys
- `focus_blocker_qt.py`: Processing code

### 6.2 ⚠️ Missing Total Display (Medium Priority)

**Problem**: Players earn materials but cannot see their total.

**Recommendation**: Add a materials display. Options:
1. **Quick**: Add "🧱 Materials: X" to the merge dialog header
2. **Better**: Add to ADHD Buster tab status section
3. **Best**: Create a "Workshop" section where materials can be spent

### 6.3 ℹ️ No Spending Mechanism (Low Priority - Future Feature)

**Current State**: Materials accumulate but cannot be spent.

**Future Recommendations**:
1. Use materials to guarantee merge success
2. Use materials to enhance items
3. Convert materials to coins or other resources
4. Use materials for special crafting recipes

### 6.4 ✅ Signal Not Connected (Informational)

The `materials_changed` signal is emitted but not connected to any handler. This is fine if no UI needs to react to material changes. Once a total display is added, it should connect to this signal.

---

## 7. Test Coverage

### 7.1 Current Tests
No dedicated tests found for the merge materials system.

### 7.2 Recommended Tests

```python
# tests/test_merge_materials.py

def test_calculate_merge_materials_under_10():
    """10% chance for items < 10"""
    # Mock random to return 0.05 (< 0.10 = success)
    materials, desc = calculate_merge_materials(5, do_roll=True)
    assert materials == 1
    
def test_calculate_merge_materials_exactly_10():
    """Guaranteed +1 for 10 items"""
    materials, desc = calculate_merge_materials(10, do_roll=True)
    assert materials >= 1
    
def test_calculate_merge_materials_over_10():
    """Guaranteed +1 plus 10% per extra item"""
    # With 15 items: guaranteed 1 + 5 chances at 10% each
    pass

def test_add_materials_saves():
    """Verify materials persist"""
    pass
    
def test_materials_capped_at_max():
    """Verify 999,999 cap"""
    pass
    
def test_user_switch_isolates_materials():
    """Verify materials are user-specific"""
    pass
```

---

## 8. Data Schema

### 8.1 Config.json Structure

```json
{
  "users": {
    "PlayerOne": {
      "adhd_buster": {
        "materials": 42,  // Merge materials (NEW)
        "coins": 500,
        "level": 10,
        "city": {
          "resources": {
            "water": 100,
            "materials": 75  // City materials (EXISTING)
          }
        }
      }
    }
  }
}
```

### 8.2 Key Paths
| Resource | JSON Path |
|----------|-----------|
| Merge Materials | `users.{username}.adhd_buster.materials` |
| City Materials | `users.{username}.adhd_buster.city.resources.materials` |

---

## 9. Conclusion

### Summary
| Aspect | Status |
|--------|--------|
| Core Implementation | ✅ Correct |
| Merge Dialog Integration | ✅ Complete |
| Persistence | ✅ Working |
| User Isolation | ✅ Working |
| Signal System | ✅ Defined, not connected (OK) |
| Naming Clarity | ⚠️ Confusing (two "materials" types) |
| Total Display | ⚠️ Missing |
| Spending Mechanism | ℹ️ Future feature |
| Test Coverage | ⚠️ Missing |

### Overall Assessment: **FUNCTIONAL** ✅

The Materials System for Merging is correctly implemented and functional. The main recommendations are:

1. **Add a total materials display** so players can see accumulated materials
2. **Consider renaming** to avoid confusion with City materials
3. **Add unit tests** for the calculation and state management logic
4. **Design a spending mechanism** to give materials purpose

---

*Report generated: Materials System Scrutiny*
*Files analyzed: game_state.py, merge_dialog.py, focus_blocker_qt.py, city_manager.py*
