# Gear System Logic - Complete Technical Documentation

## System Overview

The gear system has three interconnected layers:
1. **Base Item Properties** (power, rarity, slot)
2. **Lucky Options** (bonus % stats like +5% coins)
3. **Neighbor Effects** (positional bonuses/penalties between adjacent slots)

---

## Part 1: Item Generation

### When Items Are Generated

```python
generate_item(rarity=None, session_minutes=0, streak_days=0, story_id=None)
```

**Called from:**
- End of focus session (lines 1256-1360 in focus_blocker_qt.py)
- Sleep tracking rewards
- Weight tracking rewards
- Activity tracking rewards
- Merge system results

### Generation Flow

#### Step 1: Determine Rarity
If rarity not forced, calculate based on session/streak:

```python
# Example: 90 minute session
session_minutes = 90

# Calculate bonuses
bonuses = calculate_rarity_bonuses(90, streak_days=5)
# Returns: {"center_tier": 2, "streak_tier_bonus": 0}
# center_tier 2 = "Rare"

# Apply moving window [5%, 20%, 50%, 20%, 5%]
# Centered on tier 2 (Rare):
weights = [
    5,   # Common (tier 0, offset -2)
    20,  # Uncommon (tier 1, offset -1)
    50,  # Rare (tier 2, offset 0) <- CENTER
    20,  # Epic (tier 3, offset +1)
    5    # Legendary (tier 4, offset +2)
]

# So 90min session: 50% Rare, 20% Epic, 20% Uncommon, 5% Legendary, 5% Common
```

**Tier System:**
- Tier 0 = Common
- Tier 1 = Uncommon  
- Tier 2 = Rare
- Tier 3 = Epic
- Tier 4 = Legendary

**Session Minutes to Tier:**
- <30 min: No bonus (base weights)
- 30-59 min: Tier 1 (Uncommon center)
- 60-119 min: Tier 2 (Rare center)
- 120-179 min: Tier 3 (Epic center)
- 180+ min: Tier 4 (Legendary center)

#### Step 2: Roll Lucky Options

```python
lucky_options = roll_lucky_options(rarity)
```

**Probability by Rarity:**
- Common: 5% chance → 1 option max
- Uncommon: 15% chance → 1-2 options
- Rare: 35% chance → 1-3 options
- Epic: 60% chance → 1-4 options (all types possible)
- Legendary: 90% chance → 1-4 options

**Example Legendary Item Roll:**
```python
# 90% chance passes
# Roll 1-4 options: let's say 3
# Select 3 random types from: [coin_bonus, xp_bonus, drop_luck, merge_luck]
# Selected: coin_bonus, xp_bonus, drop_luck

# For each type, roll value from weighted distribution:
# coin_bonus values: [1, 2, 3, 5, 8, 10, 15]
# Legendary uses weights: [1, 1, 2, 3, 4, 5, 6]
# Higher values more likely for Legendary

# Result: {"coin_bonus": 10, "xp_bonus": 8, "drop_luck": 5}
```

**Value Weights by Rarity:**
```python
# Epic+ (rarity_idx >= 3):
weights = [1, 1, 2, 3, 4, 5, 6]  # Heavily favor high values

# Rare (rarity_idx == 2):
weights = [1, 2, 3, 3, 2, 1, 1]  # Bell curve, middle values

# Common/Uncommon:
weights = [5, 4, 3, 2, 1, 1, 1]  # Heavily favor low values
```

#### Step 3: Roll Neighbor Effect

```python
neighbor_effect = roll_neighbor_effect(rarity)
```

**Probability by Rarity:**
- Common: 5% chance
- Uncommon: 10% chance
- Rare: 20% chance
- Epic: 35% chance
- Legendary: 50% chance

**If successful:**
1. Random effect type: "friendly" or "unfriendly" (50/50)
2. Random target: one of 6 types (power, luck_all, luck_coin, luck_xp, luck_drop, luck_merge)
3. Calculate multiplier based on type and rarity

**Multiplier Calculation:**
```python
# Example: Legendary (rarity_idx = 4) friendly power effect

effect_type = "friendly"
target = "power"

# Get ranges
friendly_range = (1.05, 1.25)  # Power friendly range

# Scale based on rarity (0.0 for Common, 1.0 for Legendary)
t = 4 / (5-1) = 4/4 = 1.0

# Interpolate
multiplier = 1.05 + (1.25 - 1.05) * 1.0 = 1.25

# Add randomness
multiplier += random.uniform(-0.02, 0.02)  # e.g., 1.23 to 1.27

# Clamp to 0.5-2.0 range (safety)
multiplier = max(0.5, min(2.0, multiplier))

# Result: ~1.25x (25% boost)
```

**Result Example:**
```python
{
    "type": "friendly",
    "target": "power", 
    "multiplier": 1.25
}
```

#### Step 4: Create Final Item

```python
item = {
    "name": "Legendary Quantum Sword of Infinity",
    "rarity": "Legendary",
    "slot": "Weapon",
    "power": 250,  # Base power for Legendary
    "color": "#ff9800",
    "story_theme": "warrior",
    "obtained_at": "2026-01-11T10:30:00",
    
    # Optional (if rolled):
    "lucky_options": {
        "coin_bonus": 10,
        "xp_bonus": 8,
        "drop_luck": 5
    },
    
    # Optional (if rolled):
    "neighbor_effect": {
        "type": "friendly",
        "target": "power",
        "multiplier": 1.25
    }
}
```

---

## Part 2: Power Calculation

### Base Power Calculation (Simple)

```python
equipped = {
    "Helmet": {"power": 100, "rarity": "Epic"},
    "Weapon": {"power": 250, "rarity": "Legendary"}
}

base_power = 100 + 250 = 350
```

### With Neighbor Effects

#### Step 1: Map Neighbor Relationships

```python
SLOT_NEIGHBORS = {
    "Helmet": ["Chestplate"],
    "Chestplate": ["Helmet", "Gauntlets"],
    "Gauntlets": ["Chestplate", "Boots"],
    "Boots": ["Gauntlets", "Shield"],
    "Shield": ["Boots", "Weapon"],
    "Weapon": ["Shield", "Cloak"],
    "Cloak": ["Weapon", "Amulet"],
    "Amulet": ["Cloak"]
}
```

**Visual Layout (Vertical in UI):**
```
Helmet        ← Top
   ↕
Chestplate
   ↕
Gauntlets
   ↕
Boots
   ↕
Shield
   ↕
Weapon
   ↕
Cloak
   ↕
Amulet        ← Bottom
```

#### Step 2: Calculate Neighbor Effects

```python
def calculate_neighbor_effects(equipped):
    # For each equipped item
    # If it has neighbor_effect
    # Apply to its neighbors (if equipped)
```

**Example Setup:**
```python
equipped = {
    "Helmet": {
        "power": 100,
        "neighbor_effect": {
            "type": "friendly",
            "target": "power",
            "multiplier": 1.20  # +20% boost
        }
    },
    "Chestplate": {
        "power": 100
        # No neighbor effect
    },
    "Gauntlets": {
        "power": 100,
        "neighbor_effect": {
            "type": "unfriendly",
            "target": "power",
            "multiplier": 0.80  # -20% penalty
        }
    }
}
```

**Effect Propagation:**
```python
effects = {
    "Helmet": [],  # Nothing affects Helmet
    "Chestplate": [
        {
            "source": "Helmet",
            "type": "friendly",
            "target": "power",
            "multiplier": 1.20
        },
        {
            "source": "Gauntlets",
            "type": "unfriendly",
            "target": "power",
            "multiplier": 0.80
        }
    ],
    "Gauntlets": [
        {
            "source": "Chestplate",
            # No effect because Chestplate has no neighbor_effect
        }
    ]
}
```

**Wait, correction - Chestplate has no neighbor_effect, so Gauntlets receives nothing from it!**

```python
effects = {
    "Helmet": [],
    "Chestplate": [
        # Receives from Helmet (friendly 1.20x)
        # Receives from Gauntlets (unfriendly 0.80x)
    ],
    "Gauntlets": []  # Receives nothing (Chestplate has no effect)
}
```

#### Step 3: Apply Multipliers

```python
# Chestplate receives both effects
base_power = 100

# Multiply all effects together
total_multiplier = 1.20 * 0.80 = 0.96

# Calculate adjusted power
adjusted_power = int(100 * 0.96) = 96

# Clamp to minimum 1 (safety)
adjusted_power = max(1, 96) = 96

# Adjustment
adjustment = 96 - 100 = -4
```

**Final Power:**
```python
power_by_slot = {
    "Helmet": 100,       # Unaffected
    "Chestplate": 96,    # Reduced by net effect
    "Gauntlets": 100     # Unaffected
}

total_power = 100 + 96 + 100 = 296
neighbor_adjustment = -4
```

### Complex Example: Full Chain

```python
equipped = {
    "Helmet": {
        "power": 100,
        "neighbor_effect": {"type": "friendly", "target": "power", "multiplier": 1.10}
    },
    "Chestplate": {
        "power": 100,
        "neighbor_effect": {"type": "friendly", "target": "power", "multiplier": 1.15}
    },
    "Gauntlets": {
        "power": 100,
        "neighbor_effect": {"type": "friendly", "target": "power", "multiplier": 1.10}
    }
}
```

**Effects:**
- Helmet: No incoming effects → Power = 100
- Chestplate: Receives from Helmet (1.10x) AND Gauntlets (1.10x)
  - 100 * 1.10 * 1.10 = 121 → Power = 121
- Gauntlets: Receives from Chestplate (1.15x)
  - 100 * 1.15 = 115 → Power = 115

**Total: 100 + 121 + 115 = 336** (vs 300 base = +36 from neighbor effects)

---

## Part 3: Lucky Options System

### Bonus Calculation

```python
def calculate_total_lucky_bonuses(equipped):
    totals = {"coin_bonus": 0, "xp_bonus": 0, "drop_luck": 0, "merge_luck": 0}
    
    for item in equipped.values():
        lucky_options = item.get("lucky_options", {})
        for option_type, value in lucky_options.items():
            totals[option_type] += value
    
    return totals
```

**Example:**
```python
equipped = {
    "Helmet": {
        "lucky_options": {"coin_bonus": 5, "xp_bonus": 3}
    },
    "Weapon": {
        "lucky_options": {"coin_bonus": 10, "drop_luck": 5}
    },
    "Boots": {
        # No lucky options
    }
}

totals = {
    "coin_bonus": 15,   # 5 + 10
    "xp_bonus": 3,      # 3 + 0
    "drop_luck": 5,     # 0 + 5
    "merge_luck": 0     # 0 + 0
}
```

### Application Points

#### 1. Coin Rewards (Session End)
```python
base_coins = 100
coin_bonus_pct = 15  # From lucky options

# Cap at 200%
coin_bonus_pct = min(coin_bonus_pct, 200)

bonus_coins = int(100 * (15 / 100)) = 15
total_coins = 100 + 15 = 115
```

#### 2. XP Rewards
```python
base_xp = 50
xp_bonus_pct = 3

# Applied AFTER strategic priority multiplier
# If strategic: base * 1.5 = 75
# Then lucky: 75 * (3/100) = 2.25 → 2
total_xp = 75 + 2 = 77
```

#### 3. Drop Luck (Item Rarity)
```python
session_minutes = 60
drop_luck_bonus = 5  # 5%

# Each 1% = +6 virtual minutes
# Cap at 100%
drop_luck_bonus = min(drop_luck_bonus, 100)

virtual_minutes = 5 * 6 = 30
effective_minutes = 60 + 30 = 90

# Use 90 minutes for rarity calculation instead of 60
# Shifts from Rare-center to ~Epic-center
```

#### 4. Merge Luck
```python
base_rate = 0.15  # 15%
merge_luck_bonus = 10  # 10%

# Direct percentage addition
merge_luck_bonus_decimal = 10 / 100 = 0.10
total_rate = 0.15 + 0.10 = 0.25  # 25%

# Capped by MERGE_MAX_SUCCESS_RATE (35%)
total_rate = min(0.25, 0.35) = 0.25
```

---

## Part 4: Neighbor Effects on Lucky Options

### The Complex Part: Luck Multiplication

**Setup:**
```python
equipped = {
    "Helmet": {
        "lucky_options": {"coin_bonus": 10, "xp_bonus": 5},
        "neighbor_effect": {
            "type": "friendly",
            "target": "luck_coin",  # Target specific luck type
            "multiplier": 1.20
        }
    },
    "Chestplate": {
        "lucky_options": {"coin_bonus": 5}
        # No neighbor effect
    }
}
```

**Question: Does Helmet's neighbor effect affect Chestplate's coin_bonus?**

**Answer: YES!**

**How it works:**
```python
# Step 1: Calculate which slots receive effects
effects = calculate_neighbor_effects(equipped)
# Chestplate receives from Helmet: luck_coin 1.20x

# Step 2: Apply to Chestplate's lucky_options
chestplate_lucky = {"coin_bonus": 5}

# Helmet targets "luck_coin" which maps to "coin_bonus"
base_value = 5
adjusted_value = int(5 * 1.20) = 6
adjustment = 6 - 5 = 1

# Step 3: Sum all bonuses
total_coin_bonus = 10 (Helmet) + 5 (Chestplate base) + 1 (neighbor adjustment)
                 = 16
```

### luck_all Target (Special Case)

```python
equipped = {
    "Helmet": {
        "lucky_options": {
            "coin_bonus": 10,
            "xp_bonus": 5,
            "drop_luck": 3
        },
        "neighbor_effect": {
            "type": "friendly",
            "target": "luck_all",  # Affects ALL luck types
            "multiplier": 1.10
        }
    },
    "Chestplate": {
        "lucky_options": {
            "coin_bonus": 5,
            "xp_bonus": 3
        }
    }
}
```

**Calculation:**
```python
# Chestplate receives luck_all effect
# Applies to EACH luck type it has

# coin_bonus: 5 * 1.10 = 5.5 → 5 (int) → adjustment = 0
# xp_bonus: 3 * 1.10 = 3.3 → 3 (int) → adjustment = 0

# Total bonuses:
coin_bonus = 10 + 5 + 0 = 15
xp_bonus = 5 + 3 + 0 = 8
drop_luck = 3 + 0 = 3
```

**Note:** Int conversion means small bonuses may show no effect!

---

## Part 5: Gear Optimization

### Three Modes

```python
optimize_equipped_gear(adhd_buster, mode="power", target_opt="all")
```

**Modes:**
1. **"power"** - Maximize total power
2. **"options"** - Maximize lucky options
3. **"balanced"** - Balance power and options

### Scoring System

```python
def get_item_score(item):
    power = item.get("power", 10)
    lucky_options = item.get("lucky_options", {})
    
    # Calculate option value
    if target_opt == "all":
        opt_val = sum(lucky_options.values())
    else:
        opt_val = lucky_options.get(target_opt, 0)
    
    if mode == "power":
        return power
    
    elif mode == "options":
        # 1% option = 1000 power for sorting
        return opt_val * 1000 + power
    
    elif mode == "balanced":
        # Power + (options * 10)
        return power + (opt_val * 10)
```

**Example Comparison:**
```python
item_a = {"power": 250, "lucky_options": {}}
item_b = {"power": 100, "lucky_options": {"coin_bonus": 15, "xp_bonus": 10}}

# Power mode:
score_a = 250
score_b = 100
# Winner: item_a

# Options mode:
score_a = 0 * 1000 + 250 = 250
score_b = 25 * 1000 + 100 = 25100
# Winner: item_b

# Balanced mode:
score_a = 250 + (0 * 10) = 250
score_b = 100 + (25 * 10) = 350
# Winner: item_b
```

### Set Score Calculation

**For entire equipment set:**
```python
def get_set_score(equipped):
    # Calculate power with neighbor effects
    power_breakdown = calculate_effective_power(equipped)
    total_power = power_breakdown["total_power"]
    
    if mode == "power":
        return total_power
    
    # Calculate options with neighbor effects
    luck = calculate_effective_luck_bonuses(equipped)
    opt_val = sum(luck.get(k, 0) for k in ["coin_bonus", "xp_bonus", "drop_luck", "merge_luck"])
    
    if mode == "options":
        return opt_val * 10000 + total_power
    
    elif mode == "balanced":
        return total_power + (opt_val * 10)
```

**Why neighbor effects matter:**
- Two items individually may score lower
- But together with synergistic neighbor effects, they score higher
- Optimizer finds these combos

### Algorithm

**Small Inventories (<50 items total):**
- Try all combinations of top 3 items per slot
- Brute force best configuration

**Large Inventories:**
- Start with greedy selection (best item per slot)
- Iteratively try swaps
- Keep improvements, repeat until no improvement (max 10 iterations)

### Optimization Heuristic

To ensure high-synergy items (like "Friendly Power" supporters) aren't filtered out during the greedy selection phase, `get_item_score` uses a heuristic:
- **Power Mode/Balanced:** Adds `(NeighborMultiplier - 1.0) * 100 * ImpactedNeighbors` to score.
- **Luck Mode:** Adds equivalent luck value based on neighbor effects.
- **Result:** A low-power but high-synergy item (e.g., +25% Power to 2 neighbors) gets a score boost (~50 points), ensuring it's tested as a candidate.

---

## Part 6: Edge Cases & Safety

### Validation at Every Level

1. **Item Generation:**
   - Clamp multipliers 0.5x - 2.0x
   - Validate rarity before use
   - Default to Common if invalid

2. **Neighbor Effect Calculation:**
   - Skip malformed neighbor_effect dicts
   - Validate all required keys exist
   - Type-check each field
   - Only apply to equipped neighbors

3. **Power Calculation:**
   - Clamp adjusted power to minimum 1
   - Skip slots with 0 base power
   - Int conversion for all values

4. **Lucky Options:**
   - Validate dict types
   - Try-except around int conversions
   - Only add positive values
   - Cap bonuses (200% coins/xp, 100% drop luck)

### Zero/None Handling

```python
# Empty equipped
equipped = {}
# Returns: all zeros, no crash

# None in slots
equipped = {"Helmet": None, "Weapon": {"power": 100}}
# Skips None, processes Weapon

# Zero power items
equipped = {"Helmet": {"power": 0}}
# Skips in neighbor calculations (avoids division/multiplication on 0)
```

### Negative Power Prevention

```python
# Extreme unfriendly effect
multiplier = 0.01  # -99% penalty
base_power = 100

adjusted = int(100 * 0.01) = 1
adjusted = max(1, adjusted) = 1  # Clamped!

# Negative multiplier (data corruption)
multiplier = -0.50
adjusted = int(100 * -0.50) = -50
adjusted = max(1, -50) = 1  # Clamped!
```

---

## Part 7: Display Logic

### Neighbor Effect Formatting

```python
neighbor_effect = {
    "type": "friendly",
    "target": "power",
    "multiplier": 1.15
}

# Calculate percentage
pct = abs(int((1.15 - 1.0) * 100)) = 15

# Get emoji
emoji = "⬆️" if type == "friendly" else "⬇️"

# Format
display = "⬆️ 15% Power to neighbors"
```

**Examples:**
- Friendly 1.20x → "⬆️ 20% Power to neighbors"
- Unfriendly 0.80x → "⬇️ 20% Power to neighbors"
- Friendly 1.05x → "⬆️ 5% Coin Luck to neighbors"

### Lucky Options Formatting

```python
lucky_options = {"coin_bonus": 10, "xp_bonus": 5, "drop_luck": 3}

parts = []
for type, value in lucky_options.items():
    suffix = LUCKY_OPTION_TYPES[type]["suffix"]
    parts.append(f"+{value}{suffix}")

display = ", ".join(parts)
# Result: "+10% Coins, +5% XP, +3% Better Drops"
```

---

## Summary: The Complete Flow

1. **Generate Item**
   - Roll rarity (session/streak based)
   - Roll lucky options (5-90% chance, rarity based)
   - Roll neighbor effect (5-50% chance, rarity based)

2. **Equip Items**
   - Store in equipped dict by slot
   - Deep copy to preserve nested dicts

3. **Calculate Power**
   - Sum base power from all slots
   - Add set bonuses (matching themes)
   - Calculate neighbor effects (multiply affected slots)
   - Sum total

4. **Calculate Luck Bonuses**
   - Sum lucky_options from all slots
   - Apply neighbor effects to luck types
   - Use in coin/xp/drop/merge calculations

5. **Optimize**
   - Score items individually (mode-dependent)
   - Score complete sets (includes neighbor synergies)
   - Find configuration with highest score

6. **Display**
   - Show base power + set bonus + neighbor adjustment
   - Show lucky bonuses with neighbor effects
   - Show indicators (⬆️/⬇️) for neighbor effects

---

## Part 8: Advanced Scenarios & Real-World Examples

### Scenario 1: The Perfect Chain (Maximum Power Build)

**Objective:** Maximize total power using neighbor effect stacking

**Equipment Setup:**
```python
equipped = {
    "Helmet": {
        "name": "Legendary Dragon Crown",
        "power": 250,
        "rarity": "Legendary",
        "neighbor_effect": {
            "type": "friendly",
            "target": "power",
            "multiplier": 1.25  # +25% to Chestplate
        }
    },
    "Chestplate": {
        "name": "Epic Titanium Armor",
        "power": 200,
        "rarity": "Epic",
        "neighbor_effect": {
            "type": "friendly",
            "target": "power",
            "multiplier": 1.20  # +20% to Gauntlets
        }
    },
    "Gauntlets": {
        "name": "Legendary Force Gauntlets",
        "power": 250,
        "rarity": "Legendary",
        "neighbor_effect": {
            "type": "friendly",
            "target": "power",
            "multiplier": 1.25  # +25% to Boots
        }
    },
    "Boots": {
        "name": "Epic Speed Boots",
        "power": 200,
        "rarity": "Epic",
        "neighbor_effect": {
            "type": "friendly",
            "target": "power",
            "multiplier": 1.15  # +15% to Shield
        }
    },
    "Shield": {
        "name": "Legendary Aegis",
        "power": 250,
        "rarity": "Legendary",
        # No neighbor effect (end of chain)
    }
}
```

**Power Calculation:**

| Slot | Base Power | Receives From | Multipliers | Final Power | Gain |
|------|-----------|---------------|-------------|-------------|------|
| Helmet | 250 | None | 1.0 | 250 | 0 |
| Chestplate | 200 | Helmet (1.25×) + Gauntlets (1.20×) | 1.25 × 1.20 = 1.50× | 200 × 1.50 = **300** | +100 |
| Gauntlets | 250 | Chestplate (1.20×) + Boots (1.15×) | 1.20 × 1.15 = 1.38× | 250 × 1.38 = **345** | +95 |
| Boots | 200 | Gauntlets (1.25×) + Shield (none) | 1.25× | 200 × 1.25 = **250** | +50 |
| Shield | 250 | Boots (1.15×) | 1.15× | 250 × 1.15 = **287** | +37 |

**Result:**
- Base Total: 250 + 200 + 250 + 200 + 250 = **1,150**
- Final Total: 250 + 300 + 345 + 250 + 287 = **1,432**
- **Net Gain: +282 power (+24.5% increase)**

**Key Insight:** Central slots (Chestplate, Gauntlets) benefit most from multiple neighbors!

---

### Scenario 2: The Luck Amplifier (Coin Farming Build)

**Objective:** Maximize coin_bonus for currency farming

**Equipment Setup:**
```python
equipped = {
    "Helmet": {
        "power": 100,
        "lucky_options": {"coin_bonus": 15, "xp_bonus": 10},
        "neighbor_effect": {
            "type": "friendly",
            "target": "luck_coin",
            "multiplier": 1.20  # +20% to Chestplate's coins
        }
    },
    "Chestplate": {
        "power": 100,
        "lucky_options": {"coin_bonus": 10, "drop_luck": 5},
        "neighbor_effect": {
            "type": "friendly",
            "target": "luck_all",
            "multiplier": 1.15  # +15% to Gauntlets' ALL luck
        }
    },
    "Gauntlets": {
        "power": 100,
        "lucky_options": {"coin_bonus": 15},
        "neighbor_effect": {
            "type": "friendly",
            "target": "luck_coin",
            "multiplier": 1.25  # +25% to Boots' coins
        }
    },
    "Boots": {
        "power": 100,
        "lucky_options": {"coin_bonus": 10},
        # No neighbor effect
    }
}
```

**Luck Calculation:**

**Base Lucky Options (before neighbor effects):**
- Helmet: coin_bonus = 15
- Chestplate: coin_bonus = 10
- Gauntlets: coin_bonus = 15
- Boots: coin_bonus = 10
- **Base Total: 50%**

**Apply Neighbor Effects:**

1. **Helmet** receives nothing → coin_bonus = 15

2. **Chestplate** receives from Helmet:
   - Target: luck_coin → affects coin_bonus
   - Base: 10
   - Adjusted: 10 × 1.20 = 12
   - Gain: +2
   - **Final: 12**

3. **Gauntlets** receives from Chestplate:
   - Target: luck_all → affects ALL luck types
   - Base: 15
   - Adjusted: 15 × 1.15 = 17.25 → 17
   - Gain: +2
   - **Final: 17**

4. **Boots** receives from Gauntlets:
   - Target: luck_coin → affects coin_bonus
   - Base: 10
   - Adjusted: 10 × 1.25 = 12.5 → 12
   - Gain: +2
   - **Final: 12**

**Result:**
- Base Total: 50%
- With Neighbor Effects: 15 + 12 + 17 + 12 = **56%**
- **Net Gain: +6% coin bonus (+12% increase)**

**Practical Impact (100 coin session):**
- Without gear: 100 coins
- With base lucky options: 100 × 1.50 = 150 coins
- With neighbor effects: 100 × 1.56 = 156 coins
- **Extra 6 coins per session!**

---

### Scenario 3: The Mixed Blessing (Unfriendly Effect Management)

**Objective:** Understand how unfriendly effects impact builds

**Equipment Setup:**
```python
equipped = {
    "Helmet": {
        "power": 250,
        "neighbor_effect": {
            "type": "friendly",
            "target": "power",
            "multiplier": 1.25  # +25%
        }
    },
    "Chestplate": {
        "power": 200,
        "neighbor_effect": {
            "type": "unfriendly",
            "target": "power",
            "multiplier": 0.80  # -20% (cursed item!)
        }
    },
    "Gauntlets": {
        "power": 250,
        "neighbor_effect": {
            "type": "friendly",
            "target": "power",
            "multiplier": 1.20  # +20%
        }
    }
}
```

**Power Calculation:**

| Slot | Base | Receives | Multipliers | Final | Note |
|------|------|----------|-------------|-------|------|
| Helmet | 250 | None | 1.0 | 250 | Safe |
| Chestplate | 200 | Helmet (1.25×) + Gauntlets (1.20×) | 1.25 × 1.20 = 1.50× | 200 × 1.50 = **300** | Boosted despite its own curse! |
| Gauntlets | 250 | Chestplate (0.80×) | 0.80× | 250 × 0.80 = **200** | Weakened by curse |

**Result:**
- Base Total: 700
- Final Total: 250 + 300 + 200 = **750**
- Net: +50 power

**Key Insight:** The cursed item (Chestplate) doesn't hurt itself—it only hurts its neighbors! But incoming friendly effects can more than compensate.

**When to Keep Cursed Items:**
- ✅ If it has high base stats or valuable lucky options
- ✅ If positioned at top/bottom (fewer neighbors to hurt)
- ✅ If surrounded by friendly items that boost it
- ❌ If in center slots (hurts multiple neighbors)
- ❌ If neighbors are your best items

---

### Scenario 4: luck_all vs Specific Targets

**Equipment Setup A: Specific Targets**
```python
equipped_a = {
    "Helmet": {
        "lucky_options": {"coin_bonus": 10, "xp_bonus": 10, "drop_luck": 10},
        "neighbor_effect": {"type": "friendly", "target": "luck_coin", "multiplier": 1.20}
    },
    "Chestplate": {
        "lucky_options": {"coin_bonus": 10, "xp_bonus": 10, "drop_luck": 10}
    }
}
```

**Result A:**
- Chestplate coin_bonus: 10 × 1.20 = 12 (+2)
- Chestplate xp_bonus: 10 (unchanged)
- Chestplate drop_luck: 10 (unchanged)
- **Total gain: +2 across one stat**

**Equipment Setup B: luck_all**
```python
equipped_b = {
    "Helmet": {
        "lucky_options": {"coin_bonus": 10, "xp_bonus": 10, "drop_luck": 10},
        "neighbor_effect": {"type": "friendly", "target": "luck_all", "multiplier": 1.10}
    },
    "Chestplate": {
        "lucky_options": {"coin_bonus": 10, "xp_bonus": 10, "drop_luck": 10}
    }
}
```

**Result B:**
- Chestplate coin_bonus: 10 × 1.10 = 11 (+1)
- Chestplate xp_bonus: 10 × 1.10 = 11 (+1)
- Chestplate drop_luck: 10 × 1.10 = 11 (+1)
- **Total gain: +3 distributed across all stats**

**Trade-off:**
- Specific targets: **Higher multiplier** (1.15-1.25×), focused boost
- luck_all: **Lower multiplier** (1.05-1.15×), broader boost
- Choose based on specialization vs versatility

---

## Part 9: Mathematical Analysis

### Expected Value Calculations

#### Lucky Options Expected Value by Rarity

**Common:**
- Roll chance: 5%
- Max options: 1
- Value weights: [5,4,3,2,1,1,1]
- Average value: (1×5 + 2×4 + 3×3 + 5×2 + 8×1 + 10×1 + 15×1) / 17 ≈ 4.24
- **Expected value: 0.05 × 1 × 4.24 ≈ 0.21% per type**

**Epic:**
- Roll chance: 60%
- Max options: 4
- Average options: 2.5
- Value weights: [1,1,2,3,4,5,6]
- Average value: (1×1 + 2×1 + 3×2 + 5×3 + 8×4 + 10×5 + 15×6) / 22 ≈ 8.95
- **Expected value: 0.60 × 2.5 × 8.95 ≈ 13.4% per type**

**Legendary:**
- Roll chance: 90%
- Max options: 4
- Average options: 3
- Average value: 8.95
- **Expected value: 0.90 × 3 × 8.95 ≈ 24.2% per type**

**Insight:** Legendary items give ~100× more luck value than Common items!

#### Neighbor Effect Expected Power Gain

**Assumptions:**
- 5 items equipped (average setup)
- 2 center slots (receive from 2 neighbors each)
- 2 edge slots (receive from 1 neighbor each)
- 1 corner slot (receives nothing or from 1)

**Conservative Estimate (All Rare):**
- Neighbor effect chance: 20%
- Expected friendly multiplier: 1.10× average
- Expected slots affected: 5 × 0.20 × (2 neighbors each) = 2 slots receive boost
- Average boost per slot: 10%
- **Expected power gain: ~5-8%**

**Aggressive Estimate (All Legendary):**
- Neighbor effect chance: 50%
- Expected friendly multiplier: 1.15× average
- Expected slots affected: 5 × 0.50 × 2 = 5 slots (multiple effects)
- Some slots receive 2× multipliers: 1.15 × 1.15 = 1.32×
- **Expected power gain: ~15-25%**

**Real-World (Mixed Rarities):**
- **Expected power gain: ~10-15%**

### Multiplier Compounding

**Single Neighbor Effect:**
- Power = Base × Multiplier
- Example: 100 × 1.20 = 120

**Two Neighbor Effects (Multiplicative):**
- Power = Base × M1 × M2
- Example: 100 × 1.20 × 1.15 = 138
- **Not additive!** (would be 100 × 1.35 = 135)

**Maximum Theoretical Multiplier:**
- Two Legendary friendly effects: 1.25 × 1.25 = 1.5625× (**+56% power**)
- Unlikely but possible on center slots

**Minimum Theoretical Multiplier:**
- Two extreme unfriendly effects: 0.75 × 0.75 = 0.5625× (**-44% power**)
- Clamped to minimum power 1

### Optimization Complexity

**Brute Force Combinations:**
- 8 slots
- Average 50 items per slot (400 total inventory)
- Combinations: 50^8 = 3.9 × 10^13 (39 trillion!)
- **Computationally intractable**

**Current Algorithm (Greedy + Iteration):**
- Initial: O(n × 8) where n = items per slot
- Iterations: 10 × 8 × n = O(80n)
- **Total: O(n) linear complexity**
- Trade-off: May miss global optimum, but finds very good solutions fast

**Potential Improvement (Genetic Algorithm):**
- Population: 100 configurations
- Generations: 50
- Complexity: O(5000 × neighbor_calc) ≈ O(40000)
- Could find better solutions for large inventories
- *Not currently implemented*

---

## Part 10: Performance & Debugging

### Performance Benchmarks

**Expensive Operations:**

1. **Neighbor Effect Calculation:** O(n) where n = equipped items
   - Cost: <1ms for typical setup (5-8 items)

2. **Power Calculation:** O(n)
   - Cost: <1ms

3. **Gear Optimization:** O(80n) where n = items per slot
   - Cost: 100-500ms for 50 items/slot
   - Acceptable for user experience

4. **Item Generation:** O(1)
   - Cost: <0.1ms

**Memory Usage:**
- Single item: ~500-700 bytes
- 1000 items: ~0.7 MB (negligible)

### Common Debugging Issues

#### Issue 1: Power Not Updating
**Symptoms:** Equipped new item but power display unchanged

**Fix:**
```python
# Always call after equipping:
self.update_gear_slots()
self.update_hero_stats_display()
```

#### Issue 2: Neighbor Effects Missing
**Cause:** Shallow copy instead of deep copy

**Fix:**
```python
# Wrong:
equipped["Helmet"] = inventory[0]

# Right:
equipped["Helmet"] = copy.deepcopy(inventory[0])
```

#### Issue 3: Lucky Options Not Applying
**Cause:** Reward calculation not using bonuses

**Fix:**
```python
bonuses = calculate_total_lucky_bonuses(equipped)
bonus_coins = int(base_coins * (bonuses["coin_bonus"] / 100))
total_coins = base_coins + bonus_coins
```

---

## Part 11: Design Philosophy & Future Enhancements

### Core Design Principles

1. **Complexity Should Feel Rewarding, Not Overwhelming**
   - Visual indicators (⬆️/⬇️) show effect type instantly
   - Optimization button does the math
   - Percentage displays are intuitive

2. **Random Elements Must Have Bounds**
   - Multipliers: 0.5×-2.0×
   - Luck bonuses: capped at 200%
   - Minimum power: 1

3. **Stacking Should Compound, Not Add**
   - Multiplicative: 1.20 × 1.15 = 1.38× (38% boost)
   - Creates nonlinear scaling
   - Rewards optimization

4. **Every Stat Should Matter**
   - Power: Core progression
   - Lucky Options: Economic advantage
   - Neighbor Effects: Strategic depth
   - Rarity: Roll probability
   - Theme: Set bonuses

5. **Optimization Should Be Optional**
   - Casual: Equip highest power manually
   - Engaged: Optimize for builds
   - Hardcore: Theory-craft synergies

### Potential Future Features

#### 1. Conditional Neighbor Effects
```python
"neighbor_effect": {
    "type": "friendly",
    "target": "power",
    "multiplier": 1.20,
    "condition": "same_theme"  # Only if neighbor matches theme
}
```

#### 2. Gem Socket System
```python
item = {
    "sockets": 3,
    "gems": [
        {"type": "ruby", "bonus": "power", "value": 50},
        {"type": "emerald", "bonus": "luck_coin", "value": 10},
        None  # Empty socket
    ]
}
```

#### 3. Gear Evolution
```python
def evolve_item(item, currency_cost=1000):
    item["power"] = int(item["power"] * 1.10)  # +10%
    # Improve lucky options by +1 each
    # Enhance neighbor effect multiplier
```

#### 4. Set Bonuses Expansion
- 2-piece: +5% power
- 4-piece: +10% power + unique effect
- 6-piece: +20% power + double lucky options
- 8-piece: +30% power + all effects become friendly

### Lessons Learned

**Pitfalls Avoided:**
1. **Analysis Paralysis:** Optimization button provides quick solution
2. **Hidden Information:** Power breakdowns show all calculations
3. **Required Grinding:** Benefits scale smoothly, even Common items useful
4. **Power Creep:** Bounded multipliers prevent exponential scaling

**For Future Systems:**
- Can it be explained in one sentence?
- Test edge cases first (0, 1, 1000 items)
- Provide escape hatches (automation + manual control)
- Visual shortcuts (colors, indicators, numbers)
