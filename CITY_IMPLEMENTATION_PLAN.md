# City System Implementation Plan

**Based on:** CITY_SYSTEM_DESIGN.md v1.9  
**Created:** 2026-01-25  
**Status:** ✅ COMPLETE

---

## Implementation Summary

All 9 phases have been successfully completed:

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Core Package Structure | ✅ Complete |
| 2 | Data Structures & Enums | ✅ Complete |
| 3 | Building Definitions | ✅ Complete |
| 4 | City Manager Logic | ✅ Complete |
| 5 | Synergy System | ✅ Complete |
| 6 | UI Components | ✅ Complete |
| 7 | Integration Hooks | ✅ Complete |
| 8 | SVG Assets | ✅ Complete |
| 9 | Unit Tests | ✅ 53 passing |

### Files Created
- `city/__init__.py` - Package exports
- `city/city_constants.py` - Configuration constants
- `city/city_state.py` - Enums and state helpers  
- `city/city_buildings.py` - 10 building definitions
- `city/city_manager.py` - Core business logic (~600 lines)
- `city/city_synergies.py` - Entity-building synergies
- `city_tab.py` - Main UI tab with dialogs
- `tests/test_city_system.py` - Unit tests
- `icons/city/*.svg` - 10 building icons

### Integration Points
- City tab added to main window
- Resource generation: focus sessions, water, activity
- Synergy bonuses from collected entities

---

## Original Implementation Phases

### Phase 1: Core Package Structure ⏳
Create the `city/` package with proper `__init__.py` exports.

**Files to create:**
```
city/
├── __init__.py           # Package exports
├── city_constants.py     # RESOURCE_TYPES, MAX_OFFLINE_HOURS, etc.
├── city_state.py         # CellStatus enum, data schema
├── city_buildings.py     # CITY_BUILDINGS definitions
├── city_manager.py       # Business logic
├── city_synergies.py     # Entity-building synergy system
└── city_utils.py         # Helper functions
```

**Dependencies:** None (standalone module)

---

### Phase 2: Data Structures & Enums ⏳
Define core types that other modules depend on.

**Deliverables:**
- `CellStatus` enum (EMPTY, PLACED, BUILDING, COMPLETE)
- `RESOURCE_TYPES` list
- `BUILDING_SLOT_UNLOCKS` dict
- Type hints for cell state schema

**Dependencies:** Phase 1

---

### Phase 3: Building Definitions ⏳
Create all 10 building configurations.

**Deliverables:**
- `CITY_BUILDINGS` dict with all 10 buildings
- Each building has: requirements, effects, scaling, visual refs

**Dependencies:** Phase 2

---

### Phase 4: City Manager Logic ⏳
Core business functions for city operations.

**Deliverables:**
- `get_city_data()` - Initialize/retrieve city state
- `get_max_building_slots()` - Level-based slot calculation
- `get_available_slots()` - Remaining slots
- `can_place_building()` - Validation
- `place_building()` - Place a building in grid
- `invest_resources()` - Construction progress
- `collect_city_income()` - Passive income collection
- `get_city_bonuses()` - Calculate all bonuses
- Resource management functions

**Dependencies:** Phases 2, 3

---

### Phase 5: Synergy System ⏳
Entity-building bonus calculations.

**Deliverables:**
- `SynergyMapping` dataclass
- `BUILDING_SYNERGIES` dict
- `get_entity_synergy_tags()` - Get tags for entity
- `calculate_building_synergy_bonus()` - Per-building bonus
- `get_all_synergy_bonuses()` - Combined synergies

**Dependencies:** Phase 4

---

### Phase 6: UI Components ⏳
PySide6 widgets for the City tab.

**Deliverables:**
- `CityCell` - Single grid cell widget
- `CityGrid` - 5×5 container
- `CityTab` - Main tab widget
- `BuildingPickerDialog` - Select building to place
- `BuildingDetailsPanel` - Show building info
- Animation lifecycle management

**Dependencies:** Phases 4, 5

---

### Phase 7: Integration Hooks ⏳
Connect city system to existing app.

**Deliverables:**
- Add `CITY_AVAILABLE` flag to focus_blocker_qt.py
- Add resource generation hooks (water, materials, activity, focus)
- Add city signals to game_state.py
- Register CityTab in main window
- Add `get_all_perk_bonuses()` combined helper

**Dependencies:** Phases 4, 6

---

### Phase 8: SVG Assets ⏳
Create building icons.

**Deliverables:**
- 10 static building SVGs (64×64)
- 10 animated building SVGs (SMIL/CSS)
- Construction overlay SVG
- Placeholder/silhouette SVG

**Dependencies:** None (can be parallel)

---

### Phase 9: Tests ⏳
Unit tests for city system.

**Deliverables:**
- `test_city_manager.py` - Business logic tests
- `test_city_synergies.py` - Synergy calculation tests
- `test_city_integration.py` - Integration tests

**Dependencies:** Phases 4, 5

---

## Execution Order

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
                                        │
                                        ▼
Phase 8 ─────────────────────────► Phase 6 ──► Phase 7 ──► Phase 9
(parallel)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing code | All hooks wrapped in try/except with CITY_AVAILABLE flag |
| Performance issues | LRU caching, single WebEngine, opacity-only animations |
| Memory leaks | Proper cleanup in hideEvent, deleteLater on widgets |
| State corruption | Grid is single source of truth, batch mode for updates |

---

## Current Progress

| Phase | Status | Files Created |
|-------|--------|---------------|
| 1 | ⏳ Not Started | - |
| 2 | ⏳ Not Started | - |
| 3 | ⏳ Not Started | - |
| 4 | ⏳ Not Started | - |
| 5 | ⏳ Not Started | - |
| 6 | ⏳ Not Started | - |
| 7 | ⏳ Not Started | - |
| 8 | ⏳ Not Started | - |
| 9 | ⏳ Not Started | - |

---

*Last Updated: 2026-01-25*
