# Code Mathematics & Balance Audit Report

## Executive Summary
Following the discovery of a "negligible benefit" bug in the City Synergy system (where simple multiplication yielded invisible gains), a comprehensive audit of the application's mathematical core was conducted to ensure all bonus systems follow "Industry Standard" additive stacking rules.

**Status:** ✅ **All Critical Systems Verified**
- **Synergy System:** Fixed (Was `Base * 1.05`, Now `Base + 5%`).
- **Entity XP:** Fixed (Was Compounding relative to gear, Now Additive Stacking).
- **Merge Logic:** Verified Correct (Additive Probability).
- **Catch Logic:** Verified Correct (Additive Probability).
- **Drop Quality:** Verified Correct (Additive Tier Shifting).
- **Session Income:** Verified Correct (Additive Base + Bonuses).

---

## Detailed Findings

### 1. City Synergy Bonuses (FIXED) 🔧
- **Issue:** Bonuses were applying as `Base * 1.05` (Multiplicative).
  - *Example:* A 3% base bonus with 5% synergy became `3 * 1.05 = 3.15%`.
  - *Impact:* Synergy felt worthless.
- **Fix:** Converted to **Additive Probability**.
  - *New Math:* `Base (3%) + Synergy (5%) = 8%`.
  - *Files Changed:* `city/city_manager.py`, `city_tab.py`.

### 2. Entity XP Perks (FIXED) 🔧
- **Issue:** Entity XP perks were calculated sequentially after Gear bonuses.
- **Fix:** Converted to **Additive Stacking**.
  - *New Math:* `Total XP = Base * (1 + Gear% + Entity%)`.
  - *Impact:* Consistent, transparent bonus stacking where standard +5% perks always grant the same amount of XP regardless of other gear.
  - *Files Changed:* `gamification.py`.

### 3. Merge Success Rate (VERIFIED) ✅
- **Logic Check:** `rate += city_bonus / 100.0`
- **Math:** Additive.
- **Scenario:** Base 20% + City 5% = 25% Success Rate.
- **Conclusion:** Correct. Merging feels rewarding with bonuses.

### 4. Entity Catch Rates (VERIFIED) ✅
- **Logic Check:** `final = min(MAX, with_luck + city_modifier)`
- **Math:** Additive.
- **Scenario:** Base 10% + University 5% = 15% Catch Rate.
- **Conclusion:** University upgrades provide tangible value.

### 5. Item Drop Quality "Luck" (VERIFIED) ✅
- **Logic Check:** `effective_center += drop_luck / 20.0`
- **Math:** Additive Window Shifting.
- **Scenario:** +20% Drop Luck shifts the entire rarity window by +1 Tier.
- **Conclusion:** Luck stats have a massive, tangible impact on loot quality.

### 6. Focus Session Income (Royal Mint) (VERIFIED) ✅
- **Logic Check:** `mint_coins = base_coins + time_bonus`
- **Math:** Additive flat values.
- **Conclusion:** Income scales linearly and predictably.

---

## Technical Recommendations
- **Future Features:** When implementing new percentage-based bonuses, always default to **Additive Stacking** (`Base + Bonus`) for probabilities, and **Additive Multipliers** (`Base * (1 + BonusA + BonusB)`) for resource quantities. Avoid `Base * (1+BonusA) * (1+BonusB)` unless "Exponential Growth" is explicitly desired.
