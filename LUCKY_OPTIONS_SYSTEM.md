# Lucky Options System - Implementation Summary

## Overview
A comprehensive gear attribute system that adds random bonus stats to items, creating exciting opportunities for powerful item combinations.

## Lucky Option Types

### 1. Coin Bonus (+1% to +15%)
- **Effect**: Increases coins earned from focus sessions and activities
- **Applied in**: `_give_session_rewards()` in focus_blocker_qt.py
- **Formula**: `bonus_coins = coins_earned * (coin_bonus_pct / 100.0)`

### 2. XP Bonus (+1% to +15%)
- **Effect**: Increases XP earned from focus sessions
- **Applied in**: `calculate_session_xp()` in gamification.py
- **Formula**: Applied additively after strategic priority multiplier

### 3. Drop Luck (+1% to +10%)
- **Effect**: Increases chances of getting higher rarity items
- **Applied in**: `_give_session_rewards()` in focus_blocker_qt.py
- **Formula**: Each 1% = +6 virtual minutes for rarity calculation

### 4. Merge Luck (+1% to +15%)
- **Effect**: Increases success rate for lucky merges
- **Applied in**: `calculate_merge_success_rate()` in gamification.py
- **Formula**: Direct percentage bonus to success rate

## Rarity-Based Probabilities

| Rarity    | Chance for Options | Max Options | Value Weighting |
|-----------|-------------------|-------------|-----------------|
| Common    | 5%                | 1           | Low values      |
| Uncommon  | 15%               | 2           | Low-mid values  |
| Rare      | 35%               | 3           | Mid values      |
| Epic      | 60%               | 4           | High values     |
| Legendary | 90%               | 4           | Highest values  |

## Item Generation
- Lucky options are rolled during `generate_item()` via `roll_lucky_options()`
- Each item can have multiple lucky options (e.g., +5% Coins + +3% XP + +2% Drop Luck)
- Values are weighted toward higher numbers for higher rarity items

## Display Features

### Inventory Tooltips
Items with lucky options show enhanced tooltips:
```
Legendary Quantum Sword of Reality Control
Rarity: Legendary
Slot: Weapon
Power: +250
✨ Lucky Options: +5% Coins, +8% XP, +3% Merge
```

### Gear Tab Display
New "✨ Lucky Options" section shows total bonuses from all equipped gear:
- 💰 +15% Coins - Earn more coins from sessions and activities
- ⭐ +12% XP - Level up faster with bonus experience
- 🎁 +8% Drop Luck - Better chance at higher rarity items
- 🎲 +10% Merge Success - Higher chance for successful merges
- Total Lucky Stat Points: 45

### Merge Dialog
Shows merge luck bonus when present:
```
Success rate: 15% ✨ Gear Bonus: +10% Merge Success!
```

## Technical Implementation

### Core Functions (gamification.py)
- `roll_lucky_options(rarity)` - Generates lucky options for an item
- `calculate_total_lucky_bonuses(equipped)` - Sums bonuses from all equipped gear
- `format_lucky_options(lucky_options)` - Formats options for display

### Integration Points
1. **Item Generation**: `generate_item()` calls `roll_lucky_options()`
2. **Coin Rewards**: Applied in `_give_session_rewards()` before awarding coins
3. **XP Rewards**: Applied in `calculate_session_xp()` with new `lucky_xp_bonus` parameter
4. **Drop Luck**: Applied by adding virtual minutes to session duration for rarity calculation
5. **Merge Luck**: Applied in `calculate_merge_success_rate()` with new `gear_merge_luck` parameter

## Data Structure

### Item with Lucky Options
```json
{
  "name": "Epic Dragon Sword of Cosmic Power",
  "rarity": "Epic",
  "slot": "Weapon",
  "power": 100,
  "lucky_options": {
    "coin_bonus": 5,
    "xp_bonus": 3,
    "drop_luck": 2
  }
}
```

### Calculated Totals
```json
{
  "coin_bonus": 15,
  "xp_bonus": 12,
  "drop_luck": 8,
  "merge_luck": 10
}
```

## Gameplay Impact

### Power Curve
- **Low-level players**: Rare lucky options provide meaningful boosts
- **Mid-level players**: Multiple options stack for significant advantages
- **High-level players**: Hunt for perfect "god-roll" items with max stats

### Strategic Decisions
- Trade power for lucky options? (Lower rarity with great options vs high rarity with none)
- Build specialized sets (coin farming, XP grinding, merge success)
- Balance between immediate power and long-term progression bonuses

## Future Enhancements
- Reroll consumable (spend coins to reroll lucky options on an item)
- Lucky option transfer (move options between items)
- Set bonuses that increase lucky option chances
- Lucky option multipliers during events
- Marketplace to buy/sell items with specific lucky options
