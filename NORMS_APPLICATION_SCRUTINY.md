# Norms Application Scrutiny Report

**Date:** January 26, 2026  
**Updated:** January 2026 - Added age/sex-specific norms implementation  
**Scope:** Analysis of how normalization and target values are applied throughout the app for health metrics (weight, sleep, activity, hydration, focus sessions)

---

## Executive Summary

The app uses several different normalization and target systems across different health tracking features. This document scrutinizes each system for correctness, consistency, and potential issues.

**Update**: The app now supports age and sex-specific norms for:
- **BMI**: CDC percentile-based thresholds for ages 7-19 (sex-specific), WHO standard for adults 20+
- **Sleep Duration**: AASM/NSF guidelines with age-specific targets (7-12y, 13-18y, 19-64y, 65+y)

---

## 1. Weight Tracking Norms

### 1.1 BMI Classification System (WHO Standard)
**Location:** [gamification.py](gamification.py#L12148-L12158)

```python
BMI_CLASSIFICATIONS = [
    (0, 16.0, "Severely Underweight", "#ff6464"),
    (16.0, 17.0, "Moderately Underweight", "#ffaa64"),
    (17.0, 18.5, "Mildly Underweight", "#ffff64"),
    (18.5, 25.0, "Normal", "#00ff88"),
    (25.0, 30.0, "Overweight", "#ffff64"),
    (30.0, 35.0, "Obese Class I", "#ffaa64"),
    (35.0, 40.0, "Obese Class II", "#ff6464"),
    (40.0, 100.0, "Obese Class III", "#ff3232"),
]
```

**Assessment:** ✅ **CORRECT** - Uses standard WHO BMI classifications.

### 1.2 BMI Thresholds for Mode Detection
**Location:** [gamification.py](gamification.py#L11120-L11121)

```python
BMI_UNDERWEIGHT_THRESHOLD = 18.5
BMI_OVERWEIGHT_THRESHOLD = 25.0
```

**Assessment:** ✅ **CORRECT** - Standard medical thresholds.

### 1.3 Ideal Weight Range Calculation
**Location:** [gamification.py](gamification.py#L12201-L12216)

```python
def get_ideal_weight_range(height_cm: float) -> tuple:
    height_m = height_cm / 100
    min_weight = 18.5 * (height_m ** 2)
    max_weight = 25.0 * (height_m ** 2)
    return (min_weight, max_weight)
```

**Assessment:** ✅ **CORRECT** - Correctly calculates healthy BMI weight range (18.5-25).

### 1.4 Weight Mode Determination
**Location:** [gamification.py](gamification.py#L11124-L11168)

Three modes based on goal or BMI:
- **LOSS mode**: BMI > 25 or current > goal + 2kg
- **GAIN mode**: BMI < 18.5 or current < goal - 2kg
- **MAINTAIN mode**: Within 2kg of goal or BMI 18.5-25

**Assessment:** ✅ **CORRECT** - 2kg tolerance for maintenance is reasonable for daily fluctuations.

### 1.5 Weight Reward Thresholds
**Location:** [gamification.py](gamification.py#L11100-L11113)

```python
WEIGHT_DAILY_THRESHOLDS = {
    0: "Common",       # Same weight = Common item
    100: "Uncommon",   # 100g loss
    200: "Rare",       # 200g loss
    300: "Epic",       # 300g loss
    500: "Legendary",  # 500g+ loss = daily legendary!
}
WEIGHT_WEEKLY_LEGENDARY_THRESHOLD = 500   # 500g in a week
WEIGHT_MONTHLY_LEGENDARY_THRESHOLD = 2000 # 2kg in a month
```

**Assessment:** ⚠️ **MINOR CONCERN** 
- Daily thresholds seem aggressive (500g/day is ~1.1 lb) 
- However, the moving window system softens this with probabilistic distribution
- Weekly/monthly thresholds are reasonable (~0.5-2kg/week is healthy)

### 1.6 Maintenance Mode Tolerance
**Location:** [gamification.py](gamification.py#L11481-L11507)

```python
# MAINTAIN mode: reward staying within range
if abs_change <= 100:  # Within 100g is excellent → Rare
elif abs_change <= 200:  # Within 200g is good → Uncommon
elif abs_change <= 500:  # Within 500g is acceptable → Common
else:  # >500g change → no reward
```

**Assessment:** ✅ **CORRECT** - Appropriate tolerances for daily weight fluctuation (normal variance is 0.5-2kg).

### 1.7 Age and Sex-Specific BMI Norms (NEW)
**Location:** [gamification.py](gamification.py) - `BMI_PERCENTILES_BY_AGE` and related functions

For children and adolescents (ages 7-19), the app now uses **CDC BMI-for-age percentile charts** which account for normal growth patterns:

```python
BMI_PERCENTILES_BY_AGE = {
    7: {"M": (13.7, 15.4, 17.4, 19.2), "F": (13.4, 15.5, 17.6, 19.6)},
    8: {"M": (13.9, 15.8, 18.1, 20.3), "F": (13.6, 15.8, 18.3, 20.6)},
    # ... through age 19
    19: {"M": (18.2, 22.4, 26.6, 30.0), "F": (17.7, 22.1, 27.4, 32.3)},
}
```

**Percentile meanings:**
- P5 (5th percentile): Below = Underweight
- P50 (50th percentile): Median (informational)
- P85 (85th percentile): Above = Overweight
- P95 (95th percentile): Above = Obese

**Implementation functions:**
- `calculate_age_from_birth(birth_year, birth_month)`: Returns age in complete years
- `get_bmi_thresholds_for_age(age, sex)`: Returns (underweight, overweight, obese) thresholds
- `get_bmi_classification_for_age(bmi, age, sex)`: Returns classification and color

**Assessment:** ✅ **CORRECT** - Uses official CDC growth charts. Adults 20+ continue to use WHO standard (18.5-25).

**Scientific Sources:**
- CDC Growth Charts: https://www.cdc.gov/growthcharts/
- AAP Guidelines for Pediatric BMI Assessment

---

## 2. Sleep Duration Norms

### 2.1 Age-Specific Sleep Duration Targets (UPDATED)
**Location:** [gamification.py](gamification.py) - `SLEEP_DURATION_BY_AGE`

The app now uses **age-specific sleep recommendations** from AASM (American Academy of Sleep Medicine) and NSF (National Sleep Foundation):

```python
SLEEP_DURATION_BY_AGE = [
    # (min_age, max_age, min_hours, optimal_hours, max_hours)
    (7, 12, 9, 10, 12),    # School-age: 9-12 hours (AASM 2016)
    (13, 18, 8, 9, 10),    # Teens: 8-10 hours (AASM 2016)
    (19, 64, 7, 8, 9),     # Adults: 7-9 hours (NSF 2015)
    (65, 120, 7, 7.5, 8),  # Seniors: 7-8 hours (NSF 2015)
]
```

**Implementation function:**
```python
def get_sleep_targets_for_age(age: int) -> dict:
    # Returns {"min_hours": X, "optimal_hours": Y, "max_hours": Z}
```

**UI Integration:**
- Both Weight Tab and Sleep Tab include collapsible "Your Profile" sections
- Users enter birth year, birth month, and gender (M/F)
- Age is auto-calculated and displayed
- Sleep Tab shows personalized targets: "Target: 9-12h (optimal: 10h)"
- Duration color coding adapts to age-specific targets

**Assessment:** ✅ **EXCELLENT** - Now properly supports users of all ages with medically appropriate targets.

**Scientific Sources:**
- AASM 2016: "Recommended Amount of Sleep for Pediatric Populations"
- NSF 2015: "National Sleep Foundation's Sleep Time Duration Recommendations"

### 2.2 Legacy Sleep Duration Targets (Adults Default)
**Location:** [gamification.py](gamification.py#L13206-L13212)

```python
SLEEP_DURATION_TARGETS = {
    "minimum": 7.0,      # Below this = sleep deprived
    "optimal_low": 7.5,  # Start of optimal range
    "optimal_high": 9.0, # End of optimal range
    "maximum": 10.0,     # Above this may indicate health issues
}
```

**Assessment:** ✅ **CORRECT** - Aligns with CDC/NIH recommendations (7-9 hours for adults 18-64).

### 2.2 Sleep Duration Scoring
**Location:** [gamification.py](gamification.py#L13357-L13392)

```python
def calculate_duration_score(sleep_hours: float) -> tuple:
    if opt_low <= sleep_hours <= opt_high:
        return (100, "Perfect!")  # 7.5-9h = 100%
    
    if sleep_hours < min_hours:  # <7h
        deficit = min_hours - sleep_hours
        score = max(0, 100 - int(deficit * 20))  # -20 points per hour deficit
        
    if min_hours <= sleep_hours < opt_low:  # 7-7.5h
        return (85, "Good, aim for 7.5+")
        
    if opt_high < sleep_hours <= max_hours:  # 9-10h
        return (90, "Long sleep, typically fine")
        
    # >10h
    return (70, "Very long sleep - consult doctor if frequent")
```

**Assessment:** ✅ **WELL DESIGNED**
- Perfect score for 7.5-9 hours
- Gradual penalty for undersleeping (-20 points/hour)
- Mild penalty for oversleeping (10h+ gets 70%)
- Medical warning for chronic oversleeping

### 2.3 Sleep Score Component Weights
**Location:** [gamification.py](gamification.py#L13214-L13219)

```python
SLEEP_SCORE_COMPONENTS = {
    "duration_weight": 40,      # 40% of score from duration
    "bedtime_weight": 25,       # 25% from bedtime consistency
    "quality_weight": 25,       # 25% from quality
    "consistency_weight": 10,   # 10% from schedule consistency
}
```

**Assessment:** ✅ **APPROPRIATE** - Duration is weighted highest (most important), with supporting factors.

### 2.4 Sleep Reward Thresholds
**Location:** [gamification.py](gamification.py#L13221-L13228)

```python
SLEEP_REWARD_THRESHOLDS = [
    (50, "Common"),      # 50+ score
    (65, "Uncommon"),    # 65+ score
    (80, "Rare"),        # 80+ score
    (90, "Epic"),        # 90+ score
    (97, "Legendary"),   # 97+ score (exceptional sleep)
]
```

**Assessment:** ✅ **BALANCED** - Requires genuinely good sleep for higher rewards.

### 2.5 Chronotype-Based Bedtime Targets
**Location:** [gamification.py](gamification.py#L13120-L13135)

```python
SLEEP_CHRONOTYPES = [
    ("extreme_early", "Extreme Early Bird", "🌅", "19:30", "21:00", 6),  # Optimal 7:30-9pm
    ("early", "Early Bird", "🐦", "20:30", "22:00", 6),                  # Optimal 8:30-10pm
    ("moderate", "Moderate", "🌙", "21:30", "23:00", 7),                 # Optimal 9:30-11pm
    ("late", "Night Owl", "🦉", "22:30", "00:00", 8),                    # Optimal 10:30pm-midnight
    ("extreme_late", "Extreme Night Owl", "🌌", "00:00", "02:00", 9),    # Optimal midnight-2am
]
```

**Assessment:** ✅ **EXCELLENT** - Acknowledges individual chronotype differences rather than one-size-fits-all.

---

## 3. Activity/Exercise Norms

### 3.1 Activity Type Intensity Multipliers
**Location:** [gamification.py](gamification.py#L12630-L12651)

```python
ACTIVITY_TYPES = [
    ("walking", "Walking", "🚶", 1.0),      # Baseline
    ("running", "Running", "🏃", 1.5),
    ("cycling", "Cycling", "🚴", 1.3),
    ("swimming", "Swimming", "🏊", 1.4),
    ("hiit", "HIIT", "🔥", 2.5),            # Highest intensity
    ("yoga", "Yoga", "🧘", 0.8),
    ("stretching", "Stretching", "🤸", 0.8),
    ...
]
```

**Assessment:** ✅ **WELL CALIBRATED** - Relative intensities roughly align with MET values from exercise science.

### 3.2 Intensity Level Multipliers
**Location:** [gamification.py](gamification.py#L12656-L12661)

```python
INTENSITY_LEVELS = [
    ("light", "Light", 0.8),
    ("moderate", "Moderate", 1.0),
    ("vigorous", "Vigorous", 1.3),
    ("intense", "Intense", 1.6),
]
```

**Assessment:** ✅ **APPROPRIATE** - Progression from 0.8x to 1.6x is reasonable for intensity variation.

### 3.3 Effective Minutes Calculation
**Location:** [gamification.py](gamification.py#L12727-L12746)

```python
def calculate_effective_minutes(duration_minutes, activity_id, intensity_id):
    effective = duration_minutes * base_intensity * intensity_mult
    # Example: 30min vigorous HIIT = 30 * 2.5 * 1.3 = 97.5 effective minutes
```

**Assessment:** ✅ **CORRECT FORMULA** - Multiplicative combination of duration × activity × intensity.

### 3.4 Activity Reward Thresholds
**Location:** [gamification.py](gamification.py#L12673-L12679)

```python
ACTIVITY_REWARD_THRESHOLDS = [
    (8, "Common"),       # 8+ effective minutes (10 min light walk)
    (20, "Uncommon"),    # 20+ effective minutes
    (40, "Rare"),        # 40+ effective minutes
    (70, "Epic"),        # 70+ effective minutes
    (120, "Legendary"),  # 120+ effective minutes (~1hr intense workout)
]
```

**Assessment:** ✅ **WELL BALANCED**
- 10 min light walk = 10 × 1.0 × 0.8 = 8 effective → Common (encourages any activity)
- 30 min moderate run = 30 × 1.5 × 1.0 = 45 effective → Rare
- 60 min intense HIIT = 60 × 2.5 × 1.6 = 240 effective → 100% Legendary

### 3.5 Minimum Duration for Rewards
**Location:** [gamification.py](gamification.py#L12670)

```python
ACTIVITY_MIN_DURATION = 10  # Minimum 10 minutes
```

**Assessment:** ✅ **APPROPRIATE** - WHO recommends activity in bouts of at least 10 minutes.

---

## 4. Hydration Norms

### 4.1 Hydration Targets
**Location:** [gamification.py](gamification.py#L13533-L13534)

```python
HYDRATION_MIN_INTERVAL_HOURS = 2  # Minimum 2 hours between glasses
HYDRATION_MAX_DAILY_GLASSES = 5   # Maximum 5 glasses per day
```

**Assessment:** ⚠️ **POTENTIALLY LOW**
- 5 glasses (~250ml each = 1.25L) is below the typical 2-3L recommendation
- However, this likely represents **tracked** water, not total intake (people drink with meals, etc.)
- The 2-hour interval prevents gaming the system

**Recommendation:** Consider adding a tooltip explaining these are "bonus tracked glasses" not total daily intake.

### 4.2 Hydration Rewards by Glass
**Location:** [gamification.py](gamification.py#L13616-L13635)

```python
HYDRATION_GLASS_REWARDS = [
    (1, "Uncommon", "First glass"),
    (2, "Common", "Second glass"),
    (3, "Common", "Third glass"),
    (4, "Rare", "Fourth glass"),
    (5, "Epic", "Final glass - daily goal complete!"),
]
```

**Assessment:** ✅ **GOOD INCENTIVE DESIGN** - Higher rewards for completing all 5 glasses.

---

## 5. Focus Session Norms

### 5.1 Session Duration to Reward Tier
**Location:** [gamification.py](gamification.py#L4446-L4469)

```python
# Session length to center tier:
if session_minutes >= 360:    # 6hr+ = 100% Legendary
elif session_minutes >= 300:  # 5hr = Legendary-centered
elif session_minutes >= 240:  # 4hr = Epic-centered
elif session_minutes >= 180:  # 3hr = Rare-centered
elif session_minutes >= 120:  # 2hr = Uncommon-centered
elif session_minutes >= 60:   # 1hr = Common-centered
elif session_minutes >= 30:   # 30min = Below Common-centered
```

**Assessment:** ✅ **WELL DESIGNED** - Rewards longer focus sessions with better drop rates.

### 5.2 Bonus Item Chance for Marathon Sessions
**Location:** [gamification.py](gamification.py#L4456-L4460)

```python
# Bonus item chance:
if session_minutes >= 480:   # 8hr = 50% chance bonus item
elif session_minutes >= 420: # 7hr = 20% chance bonus item
```

**Assessment:** ✅ **EXCELLENT** - Rewards exceptional focus with potential double rewards.

---

## 6. Moving Window Distribution System

### 6.1 Universal Moving Window Pattern
Used consistently across weight, sleep, activity, and session rewards:

```python
# Base pattern: [5%, 20%, 50%, 20%, 5%] centered on calculated tier
window = [5, 20, 50, 20, 5]  # -2, -1, 0, +1, +2 from center

# Clamp overflow to edges
for offset, pct in zip([-2, -1, 0, 1, 2], window):
    target_tier = center_tier + offset
    clamped_tier = max(0, min(4, target_tier))
    weights[clamped_tier] += pct
```

**Assessment:** ✅ **EXCELLENT CONSISTENCY**
- Same algorithm used everywhere
- Provides predictable variance (50% at target, 20% ±1 tier, 5% ±2 tiers)
- Edge clamping prevents impossible results

---

## 7. Identified Issues & Recommendations

### 7.1 Minor Issues

| Issue | Location | Severity | Recommendation |
|-------|----------|----------|----------------|
| Hydration target (5 glasses) seems low | gamification.py:13534 | Low | Add tooltip explaining this is supplemental tracking |
| Daily weight threshold (500g legendary) is aggressive | gamification.py:11104 | Low | Consider raising to 600-700g for daily legendary |

### 7.2 Implemented Improvements ✅

1. **✅ Age-Specific Sleep Targets**: Now uses AASM/NSF guidelines with age ranges:
   - 7-12 years: 9-12 hours
   - 13-18 years: 8-10 hours
   - 19-64 years: 7-9 hours
   - 65+ years: 7-8 hours

2. **✅ Sex-Specific BMI for Children/Teens**: Now uses CDC percentile-based BMI thresholds for ages 7-19, with separate M/F charts. Adults 20+ continue to use WHO standards.

3. **✅ User Profile Collection at First Run**: A dedicated `UserProfileDialog` is shown during first-run onboarding to collect:
   - Birth year and month (to calculate age)
   - Gender (M/F)
   - This data is collected once and used throughout the app (Weight Tab, Sleep Tab)
   - Users can edit their profile anytime via "Edit" buttons in health tabs

### 7.3 Potential Future Improvements

1. **Activity MET Integration**: Could use actual MET (Metabolic Equivalent of Task) values instead of approximated multipliers for more scientific accuracy.

2. **Weight Mode Override**: Users in "normal" BMI might still want to lose/gain weight. Consider adding manual mode selection.

---

## 8. Conclusion

**Overall Assessment: ✅ WELL IMPLEMENTED**

The normalization systems in this app are:

1. **Medically Sound**: BMI, sleep, and activity targets align with WHO/CDC/AASM/NSF guidelines
2. **Age-Appropriate**: Uses CDC percentile charts for pediatric BMI and age-specific sleep targets
3. **Sex-Specific**: BMI thresholds for ages 7-19 account for developmental differences between males and females
4. **Consistent**: The moving window pattern is applied uniformly across all features
5. **Encouraging**: Low thresholds (e.g., 10-min walks) encourage any positive behavior
6. **Progressive**: Increasing rewards for better performance without punishing baseline activity
7. **Personalized**: Chronotype support for sleep, BMI-based weight modes, age/sex-specific targets

The norms are appropriately applied and scientifically grounded, now with full support for users of all ages through proper pediatric and geriatric guidelines.
