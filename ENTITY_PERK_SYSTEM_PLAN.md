# Entity Perk System Implementation Plan

## Overview

Each collected entity in the Entitidex provides a **persistent passive perk** that enhances the user's experience. Perks activate automatically when the entity is unlocked (normal variant) or enhanced when the exceptional variant is collected.

**Core Design Principles:**
1. **Small but Noticeable** - Each perk provides a minor advantage, not game-breaking
2. **Thematic Alignment** - Perks match the entity's lore and personality
3. **Visual Feedback** - Users see when perks activate with tooltips/notifications
4. **Stacking** - Multiple collected entities stack their bonuses
5. **Discovery Joy** - Learning what a new entity does rewards exploration

---

## Complete Entity Perk Assignments

### 🗡️ WARRIOR (The Iron Focus) - Power & Combat Theme

| Entity | Normal Perk | Exceptional Perk |
|--------|-------------|------------------|
| **warrior_001** Hatchling Drake | +1 Hero Base Power | +2 Hero Base Power |
| **warrior_002** Old Training Dummy | +5 Hero Base Power | +10 Hero Base Power |
| **warrior_003** Battle Falcon Swift | +1% Entity Encounter Chance | +2% Entity Encounter Chance |
| **warrior_004** War Horse Thunder | -5min Session Cooldown (rest between sessions) | -10min Session Cooldown |
| **warrior_005** Dragon Whelp Ember | +3 Hero Base Power | +6 Hero Base Power |
| **warrior_006** Battle Standard | +2% XP from Focus Sessions | +4% XP from Focus Sessions |
| **warrior_007** Battle Dragon Crimson | +5 Hero Base Power | +10 Hero Base Power |
| **warrior_008** Dire Wolf Fenris | +5% Entity Capture Probability | +8% Entity Capture Probability |
| **warrior_009** Old War Ant General | +10 Hero Base Power (Legendary) | +15 Hero Base Power |

**Warrior Theme Total (all normal):** +24 Hero Power, +1% Encounter, +2% XP, -5min Cooldown, +5% Capture

---

### 📚 SCHOLAR (The Infinite Library) - Knowledge & XP Theme

| Entity | Normal Perk | Exceptional Perk |
|--------|-------------|------------------|
| **scholar_001** Library Mouse Pip | +1% XP from Focus Sessions | +2% XP from Focus Sessions |
| **scholar_002** Study Owl Athena | +2% XP during Night Hours (8PM-6AM) | +4% XP Night Bonus |
| **scholar_003** Reading Candle | +5min Focus Session Extension Allowed | +10min Extension Allowed |
| **scholar_004** Library Cat Scholar | +1% Item Drop Luck | +2% Item Drop Luck |
| **scholar_005** Living Bookmark Finn | +1% Merge Luck | +2% Merge Luck |
| **scholar_006** Sentient Tome Magnus | +2% XP from Focus Sessions | +4% XP from Focus Sessions |
| **scholar_007** Ancient Star Map | +1% Rare Entity Encounter Bias | +2% Rare Entity Bias |
| **scholar_008** Archive Phoenix | +5% XP from Completed Story Chapters | +8% Story XP |
| **scholar_009** Blank Parchment | +5% XP from All Sources (Legendary) | +8% All XP |

**Scholar Theme Total (all normal):** +11% XP (various sources), +1% Drop Luck, +1% Merge Luck, +5min Extension

---

### 🏕️ WANDERER (The Endless Road) - Travel & Coins Theme

| Entity | Normal Perk | Exceptional Perk |
|--------|-------------|------------------|
| **wanderer_001** Lucky Coin | +1 Coin from Focus Sessions | +2 Coins per Session |
| **wanderer_002** Brass Compass | +1% Daily Streak Preservation Chance | +2% Streak Save |
| **wanderer_003** Journey Journal | +2 Coins on Session Streak (3+ days) | +4 Streak Coins |
| **wanderer_004** Road Dog Wayfinder | -5min Hydration Cooldown | -10min Hydration Cooldown |
| **wanderer_005** Self-Drawing Map | +5% Coin Bonus on Perfect Sessions | +10% Perfect Coin Bonus |
| **wanderer_006** Wanderer's Carriage | +1 Daily Hydration Cap (6 instead of 5) | +1 More (7 total) |
| **wanderer_007** Timeworn Backpack | +1 Inventory Slot | +2 Inventory Slots |
| **wanderer_008** Sky Balloon Explorer | +2 Coins from Focus Sessions | +4 Coins per Session |
| **wanderer_009** Hobo Rat | +5% All Coin Gains (Legendary) | +8% All Coin Gains |

**Wanderer Theme Total (all normal):** +3 Coins/Session, -5min Hydration CD, +1 Hydration Cap, +1 Inventory Slot, +5% Coin Gains

---

### 🏢 UNDERDOG (Rise of the Underdog) - Workplace & Luck Theme

| Entity | Normal Perk | Exceptional Perk |
|--------|-------------|------------------|
| **underdog_001** Office Rat Reginald | +1% Item Drop Chance | +2% Item Drop Chance |
| **underdog_002** Lucky Sticky Note | +1% Merge Luck | +2% Merge Luck |
| **underdog_003** Vending Machine Coin | -1 Coin Cost on All Operations | -2 Coin Discount |
| **underdog_004** Window Pigeon Winston | +1 Coin on Item Salvage | +2 Coins per Salvage |
| **underdog_005** Desk Succulent Sam | -5min Hydration Cooldown | -10min Hydration Cooldown |
| **underdog_006** Break Room Coffee Maker | +1 Eye Rest Claim per Day | +2 Eye Rest Claims |
| **underdog_007** Corner Office Chair | +3% All Luck Stats | +5% All Luck Stats |
| **underdog_008** AGI Assistant Chad | +2% Entity Capture Probability | +4% Capture Probability |
| **underdog_009** Break Room Fridge | +1 Daily Hydration Cap (Legendary) | +1 More Hydration Cap |

**Underdog Theme Total (all normal):** +1% Drop, +1% Merge Luck, -1 Coin Cost, -5min Hydration CD, +1 Eye Rest, +3% All Luck, +2% Capture

---

### 🔬 SCIENTIST (The Breakthrough Protocol) - Research & Discovery Theme

| Entity | Normal Perk | Exceptional Perk |
|--------|-------------|------------------|
| **scientist_001** Cracked Test Tube | +1% Uncommon Item Chance | +2% Uncommon Item Chance |
| **scientist_002** Old Bunsen Burner | +1% Merge Success Rate | +2% Merge Success |
| **scientist_003** Lucky Petri Dish | +1% Rare Item Chance | +2% Rare Item Chance |
| **scientist_004** Wise Lab Rat Professor | +5% Pity System Bonus | +8% Pity Bonus |
| **scientist_005** Vintage Microscope | Reveal Next Entity Hint in Entitidex | Reveal 2 Hints |
| **scientist_006** Bubbling Flask | +2% Epic Item Chance | +4% Epic Item Chance |
| **scientist_007** Tesla Coil Sparky | +3% Perfect Session Bonus (coins/items) | +5% Perfect Bonus |
| **scientist_008** Golden DNA Helix | +1% Legendary Item Chance | +2% Legendary Item Chance |
| **scientist_009** White Mouse Archimedes | +3% All Discovery Bonuses (Legendary) | +5% All Discovery |

**Scientist Theme Total (all normal):** +1% Uncommon, +1% Rare, +2% Epic, +1% Legendary, +5% Pity, +3% Perfect Bonus

---

## Perk Categories Summary

### 1. **Power Bonuses** (Hero Stats)
- Flat power boosts: +1, +3, +5, +10
- Applied in `calculate_character_power()` function

### 2. **Coin Modifiers**
- Flat coin bonuses: +1, +2 per session
- Percentage bonuses: +5% all coins
- Discounts: -1 coin cost on operations

### 3. **Luck Modifiers**
- Merge luck: +1%, +2%
- Item drop luck: +1%, +2%
- All luck: +3%

### 4. **Hydration System**
- Cooldown reduction: -5min, -10min
- Daily cap increase: +1 glass

### 5. **Entity Encounters**
- Encounter chance: +1%, +2%
- Capture probability: +2%, +5%, +8%
- Pity bonus: +5%

### 6. **XP Modifiers**
- Session XP: +1%, +2%
- All XP: +5%
- Story XP: +5%

### 7. **Item Rarity Modifiers**
- Uncommon chance: +1%
- Rare chance: +1%
- Epic chance: +2%
- Legendary chance: +1%

### 8. **Quality of Life**
- Inventory slots: +1
- Eye rest claims: +1
- Session extension: +5min
- Streak preservation: +1%

---

## Implementation Architecture

### New Module: `entity_perks.py`

```python
"""
Entity Perk System

Manages persistent bonuses from collected Entitidex entities.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

class PerkType(Enum):
    POWER_FLAT = "power_flat"              # +X hero power
    COIN_FLAT = "coin_flat"                # +X coins per action
    COIN_PERCENT = "coin_percent"          # +X% coin gains
    COIN_DISCOUNT = "coin_discount"        # -X coin costs
    XP_PERCENT = "xp_percent"              # +X% XP gains
    MERGE_LUCK = "merge_luck"              # +X% merge success
    DROP_LUCK = "drop_luck"                # +X% item drop chance
    ENCOUNTER_CHANCE = "encounter_chance"  # +X% entity encounter
    CAPTURE_BONUS = "capture_bonus"        # +X% capture probability
    HYDRATION_COOLDOWN = "hydration_cd"    # -X minutes cooldown
    HYDRATION_CAP = "hydration_cap"        # +X daily glasses
    INVENTORY_SLOTS = "inventory_slots"    # +X slots
    EYE_REST_CAP = "eye_rest_cap"          # +X daily claims
    PITY_BONUS = "pity_bonus"              # +X% pity system
    RARITY_BIAS = "rarity_bias"            # +X% for specific rarity


@dataclass
class EntityPerk:
    """Defines a perk granted by an entity."""
    entity_id: str
    perk_type: PerkType
    normal_value: float
    exceptional_value: float
    description: str
    icon: str = "✨"


# Complete perk definitions
ENTITY_PERKS: Dict[str, EntityPerk] = {
    # WARRIOR
    "warrior_001": EntityPerk("warrior_001", PerkType.POWER_FLAT, 1, 2, 
                               "Hatchling's Warmth: +{value} Hero Power", "🐉"),
    "warrior_002": EntityPerk("warrior_002", PerkType.POWER_FLAT, 5, 10,
                               "Training Resilience: +{value} Hero Power", "🎯"),
    # ... (all 45 entities defined)
}


def calculate_active_perks(progress: 'EntitidexProgress') -> Dict[PerkType, float]:
    """
    Calculate total bonuses from all collected entities.
    
    Returns dict of PerkType -> total_value
    """
    totals: Dict[PerkType, float] = {}
    
    for entity_id in progress.collected_entity_ids:
        perk = ENTITY_PERKS.get(entity_id)
        if perk:
            value = perk.exceptional_value if progress.is_exceptional(entity_id) else perk.normal_value
            totals[perk.perk_type] = totals.get(perk.perk_type, 0) + value
    
    return totals


def get_perk_description(entity_id: str, is_exceptional: bool = False) -> str:
    """Get human-readable perk description for an entity."""
    perk = ENTITY_PERKS.get(entity_id)
    if not perk:
        return "No perk"
    
    value = perk.exceptional_value if is_exceptional else perk.normal_value
    return f"{perk.icon} {perk.description.format(value=value)}"
```

---

## Integration Points

### 1. Power Calculation (`gamification.py`)

```python
def calculate_character_power(adhd_buster: dict, ...) -> int:
    """Enhanced with entity perks."""
    base_power = ... # existing calculation
    
    # NEW: Add entity perk bonuses
    progress = get_entitidex_progress(adhd_buster)
    perks = calculate_active_perks(progress)
    perk_power = perks.get(PerkType.POWER_FLAT, 0)
    
    return base_power + perk_power
```

### 2. Coin Operations (`game_state.py`, `merge_dialog.py`)

```python
def apply_coin_perk(base_coins: int, perks: Dict) -> int:
    """Apply coin bonuses from entity perks."""
    flat_bonus = perks.get(PerkType.COIN_FLAT, 0)
    percent_bonus = perks.get(PerkType.COIN_PERCENT, 0) / 100
    
    return int(base_coins * (1 + percent_bonus) + flat_bonus)


def apply_coin_discount_perk(cost: int, perks: Dict) -> int:
    """Apply coin discount from entity perks."""
    discount = perks.get(PerkType.COIN_DISCOUNT, 0)
    return max(1, cost - int(discount))  # Minimum 1 coin
```

### 3. Merge Dialog (`merge_dialog.py`)

```python
def get_total_merge_luck(self) -> float:
    """Include entity perk merge luck."""
    base_luck = self.gear_merge_luck
    perk_luck = self.active_perks.get(PerkType.MERGE_LUCK, 0)
    return base_luck + perk_luck
```

### 4. Hydration System (`gamification.py`)

```python
HYDRATION_MIN_INTERVAL_HOURS = 2  # Base value

def get_hydration_cooldown_minutes(perks: Dict) -> int:
    """Get cooldown with perk reductions."""
    base_minutes = HYDRATION_MIN_INTERVAL_HOURS * 60
    reduction = perks.get(PerkType.HYDRATION_COOLDOWN, 0)
    return max(30, base_minutes - reduction)  # Minimum 30 min


def get_max_daily_glasses(perks: Dict) -> int:
    """Get daily cap with perk increases."""
    base_cap = HYDRATION_MAX_DAILY_GLASSES  # 5
    bonus = perks.get(PerkType.HYDRATION_CAP, 0)
    return base_cap + int(bonus)
```

### 5. Entity Encounters (`entitidex/encounter_system.py`)

```python
def calculate_encounter_chance(..., perks: Dict = None) -> float:
    """Include perk bonuses in encounter chance."""
    base_chance = ... # existing calculation
    perk_bonus = (perks or {}).get(PerkType.ENCOUNTER_CHANCE, 0) / 100
    return min(0.90, base_chance + perk_bonus)
```

---

## User Feedback System

### 1. Perk Activation Tooltips

When a perk affects something, show a brief notification:

```python
class PerkNotification:
    """Shows when entity perks activate."""
    
    @staticmethod
    def show_perk_activation(perk: EntityPerk, context: str):
        """
        Show brief tooltip when perk activates.
        
        Example: "🐉 Hatchling Drake: +1 Power active!"
        """
        msg = f"{perk.icon} {get_entity_name(perk.entity_id)}: {context}"
        # Show as toast notification
```

### 2. Perk Summary in Entitidex Tab

Add a "Active Perks" panel showing:
- Total power bonus: +24
- Total coin bonus: +5%
- Merge luck: +2%
- etc.

### 3. Entity Card Perk Display

When hovering over a collected entity, show its perk:
```
🐉 Hatchling Drake
⚪ COMMON | Power: 10
━━━━━━━━━━━━━━━━━━━━
✨ PERK: +1 Hero Power
(+2 if Exceptional)
```

### 4. Session Complete Summary

At session end, show which perks contributed:
```
Session Complete!
🪙 Coins earned: 15 (+2 from Lucky Coin 🪙)
⚡ XP earned: 100 (+5% from Study Owl 🦉)
💪 Hero Power: 150 (+10 from Training Dummy 🎯)
```

---

## Implementation Phases

### Phase 1: Core System (Day 1)
- [ ] Create `entitidex/entity_perks.py` with perk definitions
- [ ] Implement `calculate_active_perks()` function
- [ ] Add perk type enum and data structures

### Phase 2: Power Integration (Day 1)
- [ ] Modify `calculate_character_power()` to include perks
- [ ] Add perk display to Hero stats panel
- [ ] Show power breakdown with perk contributions

### Phase 3: Coin Integration (Day 2)
- [ ] Add perk modifiers to coin rewards
- [ ] Add perk discounts to coin costs
- [ ] Update merge dialog with perk costs

### Phase 4: Luck Integration (Day 2)
- [ ] Integrate merge luck perks
- [ ] Integrate drop luck perks
- [ ] Add luck display in relevant UIs

### Phase 5: Hydration & Eye Rest (Day 3)
- [ ] Modify hydration cooldown calculation
- [ ] Modify daily hydration cap
- [ ] Modify eye rest claim limits

### Phase 6: Entity System Integration (Day 3)
- [ ] Add encounter chance perks
- [ ] Add capture probability perks
- [ ] Enhance pity system with perks

### Phase 7: UI Feedback (Day 4)
- [ ] Add perk tooltips to entity cards
- [ ] Create "Active Perks" summary panel
- [ ] Add perk activation notifications
- [ ] Update session complete dialog

### Phase 8: Testing & Polish (Day 4)
- [ ] Write unit tests for perk calculations
- [ ] Test perk stacking behavior
- [ ] Verify exceptional bonuses work
- [ ] Balance pass on values

---

## Testing Checklist

- [ ] Perks activate only for collected entities
- [ ] Exceptional variants give enhanced perks
- [ ] Perks stack correctly from multiple entities
- [ ] UI shows accurate perk totals
- [ ] Notifications appear when perks activate
- [ ] Perks persist across app restarts
- [ ] Perks update immediately when entities collected

---

## Balance Notes

- **Power perks**: Total potential +60+ from all entities (significant but not game-breaking)
- **Coin perks**: ~15% increase in coin income (noticeable but fair)
- **Luck perks**: ~5-10% improvement (helps but doesn't guarantee)
- **Hydration**: Up to 30min cooldown reduction (quality of life)
- **Legendary entities**: Have strongest perks (reward for completing collection)

---

## Example: Perk in Action

**User collects "Vending Machine Coin" (underdog_003)**

Before:
- Merge cost: 50 coins

After:
- Merge cost: 49 coins (shows strikethrough: ~~50~~ 49 🪙)
- Toast notification: "🪙 Vending Machine Coin: -1 coin on all operations!"
- Entity card shows: "✨ PERK: -1 Coin Cost"

---

*This system transforms the Entitidex from a pure collection feature into a meaningful progression system where every entity matters.*
