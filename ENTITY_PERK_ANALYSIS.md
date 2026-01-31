# Entity Perk System - Comprehensive Analysis

## Overview

This document analyzes all entity perks in the system, identifying which follow the standard stacking model and which have **special/exclusive behaviors**.

---

## Perk Stacking Rules

### Standard Behavior (Most Entities)
When you collect **BOTH normal AND exceptional** variants of an entity:
- Normal perk value is added
- Exceptional perk value is added
- **Total = Normal + Exceptional** (they stack!)

### Special Cases
Some entities provide **different abilities** for normal vs exceptional variants, or have special handling outside the standard perk system.

---

## Entity Perks by Category

### 🗡️ WARRIOR (Power & Combat)

| Entity ID | Normal Name | Normal Perk | Exceptional Name | Exceptional Perk | Stacking |
|-----------|------------|-------------|------------------|------------------|----------|
| warrior_001 | Dragon Hatchling | +1 Power | Dragon Inferno | +2 Power | ✅ Standard |
| warrior_002 | Training Dummy | +5 Power | Bold Training Dummy | +10 Power | ✅ Standard |
| warrior_003 | Battle Falcon | +1% Encounter | War Eagle | +2% Encounter | ✅ Standard |
| warrior_004 | War Horse | +5% XP (>1h) | Nightmare Steed | +8% XP (>1h) | ✅ Standard |
| warrior_005 | Dragon Whelp Ember | +3 Power | Inferno Drake | +6 Power | ✅ Standard |
| warrior_006 | Battle Standard | +2% Focus XP | War Banner | +4% Focus XP | ✅ Standard |
| warrior_007 | Crimson Dragon | +5 Power | Blood Dragon | +10 Power | ✅ Standard |
| warrior_008 | Wolf Pack | +5% Capture | Alpha Pack | +8% Capture | ✅ Standard |
| warrior_009 | Ant General | +10 Power, Paid Recalc | Ice Swarm Emperor | +15 Power, Risky Recalc | ⚠️ Special* |

*warrior_009 has mutually exclusive recalculation abilities:
- Normal: `RECALC_PAID=1` (pay coins to recalculate)
- Exceptional: `RECALC_RISKY=1` (free 80% success recalc)
- Both perks have 0 value for the other variant, so collecting both gives you BOTH abilities!

---

### 📚 SCHOLAR (Knowledge & XP)

| Entity ID | Normal Name | Normal Perk | Exceptional Name | Exceptional Perk | Stacking |
|-----------|------------|-------------|------------------|------------------|----------|
| scholar_001 | Library Mouse Pip | +1% Focus XP | Library Mouse Quip | +2% Focus XP | ✅ Standard |
| scholar_002 | Study Owl Athena | +2% Night XP | Steady Owl Athena | +1 Sleep Tier | ⚠️ **SPECIAL** |
| scholar_003 | Candle Moth | +2% Morning XP | Dawn Moth | +4% Morning XP | ✅ Standard |
| scholar_004 | Sphinx Cat | +1% Item Drops | Eternal Sphinx | +2% Item Drops | ✅ Standard |
| scholar_005 | Bookmark Serpent | +1% Merge Luck | Arcane Serpent | +2% Merge Luck | ✅ Standard |
| scholar_006 | Ancient Tome | +2% Focus XP, Paid Recalc | Forbidden Grimoire | +4% Focus XP, Paid Recalc | ✅ Standard |
| scholar_007 | Star Map | +1% Rare Finds | Celestial Atlas | +2% Rare Finds | ✅ Standard |
| scholar_008 | Phoenix Quill | +5% Story XP, +1% Scrap | Eternal Flame | +8% Story XP, +2% Scrap | ✅ Standard |
| scholar_009 | Blank Scroll | 10% Item Recovery | Omniscient Scroll | 20% Item Recovery | ✅ Standard |

---

### 🧭 WANDERER (Travel & Coins)

| Entity ID | Normal Name | Normal Perk | Exceptional Name | Exceptional Perk | Stacking |
|-----------|------------|-------------|------------------|------------------|----------|
| wanderer_001 | Lucky Coin | +1 Coin, Paid Recalc | Golden Coin | +2 Coins, Risky Recalc | ⚠️ Special* |
| wanderer_002 | Brass Compass | +1% Streak Save | Class Compass | +2% Streak Save | ✅ Standard |
| wanderer_003 | Travel Journal | +2 Coins | Treasure Chronicle | +4 Coins | ✅ Standard |
| wanderer_004 | Thirsty Dog | -5min Water CD | Oasis Hound | -10min Water CD | ✅ Standard |
| wanderer_005 | Treasure Map | +5% Perfect Session | Master Navigator | +10% Perfect Session | ✅ Standard |
| wanderer_006 | Camp Wagon | +1 Water Cap | Oasis Camp | +1 Water Cap | ✅ Standard |
| wanderer_007 | Pack Mule | +1 Inventory Slot | Dimensional Satchel | +2 Inventory Slots | ✅ Standard |
| wanderer_008 | Hot Air Balloon | +2 Coins | Sky Voyager | +4 Coins | ✅ Standard |
| wanderer_009 | Hobo Rat | +5% Coins, +1% Scrap, Risky Recalc | Robo Rat | +8% Coins, +2% Scrap, Risky Recalc | ✅ Standard |

*wanderer_001: Similar to warrior_009 - normal gets Paid Recalc (1,0), exceptional gets Risky Recalc (0,1).

---

### 💼 UNDERDOG (Workplace & Luck)

| Entity ID | Normal Name | Normal Perk | Exceptional Name | Exceptional Perk | Stacking |
|-----------|------------|-------------|------------------|------------------|----------|
| underdog_001 | Office Rat Reginald | +1% Drops, +1% Scrap | Officer Rat Regina | +2% Drops, +2% Scrap | ✅ Standard |
| underdog_002 | Sticky Note | +1% Merge Luck | Blessed Post-It | +2% Merge Luck | ✅ Standard |
| underdog_003 | Vending Machine | -1 Coin Cost | Jackpot Machine | -2 Coin Cost | ✅ Standard |
| underdog_004 | Office Bird Winston | +1 Salvage Coins | Golden Beak | +2 Salvage Coins | ✅ Standard |
| underdog_005 | Desk Succulent Sam | +1 Eye Tier | Desk Succulent Pam | 50% Eye Reroll | ⚠️ **SPECIAL** |
| underdog_006 | Coffee Mug | -1 Store Refresh, Paid Recalc | Endless Brew | -2 Store Refresh, Paid Recalc | ✅ Standard |
| underdog_007 | Corner Office Chair | +3% All Luck | Stoner Office Chair | +5% All Luck | ✅ Standard |
| underdog_008 | Chad GPT | +2% Capture, Paid Recalc | Sigma GPT | +4% Capture, Risky Recalc | ⚠️ Special* |
| underdog_009 | Office Fridge | +1 Water Cap, Paid Recalc | Wagyu Fridge | +1 Water Cap, Risky Recalc | ⚠️ Special* |

### ⚠️ CRITICAL: underdog_005 (Desk Succulent Sam/Pam)

This entity has **completely different perks** for normal vs exceptional:

**In ENTITY_PERKS (entity_perks.py):**
```python
"underdog_005": [EntityPerk("underdog_005", PerkType.EYE_TIER_BONUS, 1, 0, "Dry Eye: +{value} Eye Tier", "🌵", "Desert Eye: 50% Reroll")]
```
- Normal: EYE_TIER_BONUS = 1
- Exceptional: EYE_TIER_BONUS = **0** (not 50!)

**In get_entity_eye_perks() (gamification.py) - HARDCODED SPECIAL LOGIC:**
```python
if has_normal:
    result["eye_tier_bonus"] = 1   # +1 tier from normal
if has_exceptional:
    result["eye_reroll_chance"] = 50  # 50% reroll from exceptional
```

**Current behavior after my fix:**
- Normal only: +1 Eye Tier
- Exceptional only: 50% Reroll
- **BOTH: +1 Eye Tier AND 50% Reroll** ✅ (they stack because they're different abilities!)

---

### 🔬 SCIENTIST (Research & Discovery)

| Entity ID | Normal Name | Normal Perk | Exceptional Name | Exceptional Perk | Stacking |
|-----------|------------|-------------|------------------|------------------|----------|
| scientist_001 | Lab Flask | +1% Uncommon | Breakthrough Flask | +2% Uncommon | ✅ Standard |
| scientist_002 | Bunsen Burner | +1% Merge Success | Controlled Flame | +2% Merge Success | ✅ Standard |
| scientist_003 | Petri Dish | +1% Rare, +1% Scrap | Perfect Specimen | +2% Rare, +2% Scrap | ✅ Standard |
| scientist_004 | Wise Lab Rat Professor | +5% Pity Progress | Wise Lab Rat Assessor | +8% Pity Progress | ✅ Standard |
| scientist_005 | Microscope | +2% Focus XP, +1% Scrap | Quantum Scope | +4% Focus XP, +2% Scrap | ✅ Standard |
| scientist_006 | Alembic | +2% Epic Chance | Philosopher's Stone | +4% Epic Chance | ✅ Standard |
| scientist_007 | Tesla Coil | +5% Gamble Luck | Lightning Rod | +20% Gamble Luck | ✅ Standard |
| scientist_008 | DNA Helix | +1% Legendary | Divine Helix | +2% Legendary | ✅ Standard |
| scientist_009 | White Mouse Archimedes | +3% All XP | Bright Mouse Archimedes | +5% All XP | ✅ Standard |

---

## Special Secondary Perks (Hardcoded in gamification.py)

These entities have **additional special abilities** beyond their ENTITY_PERKS definitions, handled by dedicated functions:

### 1. Sleep Tier Bonus (scholar_002 - Study Owl Athena)
**Function:** `get_entity_sleep_perks()`
- Normal: +0 (no sleep bonus from normal)
- Exceptional: +1 Sleep Tier
- **Both: +1 Sleep Tier** (exceptional only provides this)

Note: Normal provides +2% Night XP (via ENTITY_PERKS). Exceptional provides +1 Sleep Tier (via hardcoded function). Having BOTH gives +2% Night XP AND +1 Sleep Tier - they are complementary abilities.

### 2. Weight Legendary Bonus (Rodent Entities)
**Function:** `get_entity_weight_perks()`
**Entities:** scholar_001, scientist_004, scientist_009, underdog_001, wanderer_009

Each rodent provides:
- Normal: +1% Legendary chance
- Exceptional: +2% Legendary chance
- **Both: +3%** (stacked)

### 3. Optimize Gear Cost (wanderer_009 - Hobo/Robo Rat)
**Function:** `get_entity_optimize_gear_cost()`
- Normal: 1 coin cost (instead of 10)
- Exceptional: **FREE** (0 coins)
- Both: Uses best value (0 coins) - not stacked, uses minimum

### 4. Sell Bonus (underdog_007 - Corner/Stoner Office Chair)
**Function:** `get_entity_sell_perks()`
- Normal: +25% Epic sell value
- Exceptional: +25% Legendary sell value
- **Both: +25% Epic, +25% Legendary** (different bonuses, both apply)

Note: This is SEPARATE from the ALL_LUCK perk which also stacks.

---

## Entities with RECALC Abilities (Mutually Exclusive)

These entities provide probability recalculation for saved encounters. Normal and exceptional variants provide DIFFERENT types:

| Entity | Normal | Exceptional |
|--------|--------|-------------|
| warrior_009 (Ant General) | RECALC_PAID (costs coins) | RECALC_RISKY (free, 80% success) |
| wanderer_001 (Lucky Coin) | RECALC_PAID | RECALC_RISKY |
| underdog_008 (Chad GPT) | RECALC_PAID | RECALC_RISKY |
| underdog_009 (Office Fridge) | RECALC_PAID | RECALC_RISKY |
| scholar_006 (Ancient Tome) | RECALC_PAID | RECALC_PAID (same) |
| underdog_006 (Coffee Mug) | RECALC_PAID | RECALC_PAID (same) |
| wanderer_009 (Hobo Rat) | RECALC_RISKY | RECALC_RISKY (same) |

**Collecting BOTH variants gives you BOTH abilities** when they differ!

---

## Summary: Fixes Applied

All my fixes ensure that:

1. **Standard perks STACK** when you have both variants
2. **Special abilities** from different functions also stack appropriately  
3. **Exceptional-only entities** (not in `collected_entity_ids` but in `exceptional_entities`) are now properly recognized
4. **Different abilities** (like Eye Tier vs Eye Reroll) correctly provide BOTH benefits when you have both variants

### Files Fixed:
- `entitidex/entity_perks.py` - `calculate_active_perks()`
- `entitidex_tab.py` - Progress bar, perks summary dialog
- `focus_blocker_qt.py` - Timeline ring
- `gamification.py` - All `get_entity_*_perks()` and `get_entity_*_perk_contributors()` functions
- `city/city_synergies.py` - Building synergy bonuses

---

## Validation

After fixes, the test case:
- Training Dummy (normal): +5 Power
- Bold Training Dummy (exceptional): +10 Power  
- Dragon Whelp Ember (normal): +3 Power

**Expected: 5 + 10 + 3 = 18 Power** ✅
