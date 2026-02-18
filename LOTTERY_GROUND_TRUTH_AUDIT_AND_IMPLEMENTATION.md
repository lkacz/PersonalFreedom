# Lottery Ground-Truth Audit And Implementation Report

Date: 2026-02-18

## Objective
Make lotteries ground-truth driven: the roll values shown in animation must be the same values used by backend outcome resolution, and state/progress updates must happen after lottery completion.

## Findings Before Changes

### 1. Merge lottery was pre-resolved before animation
- File: `merge_dialog.py`
- `execute_merge()` called `perform_lucky_merge(...)` first.
- `MergeTwoStageLotteryDialog` then only revealed already-decided values.
- This created a reveal-only animation model, not animation-authored roll authority.

### 2. Eye routine state updated before lottery completion
- File: `eye_protection_tab.py`
- `complete_routine()` persisted `daily_count`, `last_date`, and notified timeline before running lottery dialogs.
- This allowed UI/state to move ahead of what the user had finished seeing.

### 3. Other lottery systems still include reveal-only patterns
- Priority, water, activity, and some reward paths still pass pre-rolled outcomes into animation dialogs.
- This is not necessarily incorrect, but it is not full "animation is source of truth" architecture.

## Implemented Changes

### A. Merge now uses animation-authored roll values
- File: `merge_dialog.py`
- `execute_merge()` now:
  1. Computes merge context (success threshold, tier weights, celestial context).
  2. Launches `MergeTwoStageLotteryDialog` first.
  3. Reads resolved rolls from the dialog (`success_roll`, `tier_roll`, `celestial_roll`).
  4. Calls `perform_lucky_merge(...)` with those exact roll values.
  5. Applies result handling after animation.

Effect:
- Backend no longer decides merge roll outcomes before the animation.
- The values shown in animation now directly drive backend merge resolution.

### B. Merge dialog now supports canonical celestial roll tracking
- File: `lottery_animation.py`
- `MergeTwoStageLotteryDialog` now accepts and stores `celestial_roll`.
- If not provided and celestial chance is active, it generates one.
- It can auto-resolve celestial trigger for animation-authored flow while still respecting explicit backend-provided final rarity when supplied.

Effect:
- Celestial outcome can be synchronized as part of the same canonical roll set.

### C. Eye routine persistence moved to post-lottery
- File: `eye_protection_tab.py`
- `complete_routine()` now defers persistence and timeline notification until after lottery (and optional reroll) completes.
- Then commits:
  - `today_entry.count`
  - `today_entry.items_won` / `tiers` (if won)
  - `daily_count` and `last_date`
  - timeline notification

Effect:
- State/UI updates are now sequenced after the visible lottery outcome.

### D. Priority and water lotteries now use dialog-owned canonical rolls
- Files: `focus_blocker_qt.py`, `lottery_animation.py`, `gamification.py`
- Priority completion:
  - Caller-side pre-roll was removed from `focus_blocker_qt.py`.
  - `PriorityLotteryDialog` now generates canonical win/rarity rolls and passes them to backend.
  - `roll_priority_completion_reward(...)` now accepts `win_roll_override` and `rarity_roll_override`.
- Water:
  - Caller-side pre-roll was removed previously.
  - `WaterLotteryDialog` generates canonical rolls and passes explicit overrides to backend.

Effect:
- The values animated in priority/water are now the exact values backend uses.
- Caller-side reveal-only drift risk is removed for these paths.

### E. Focus session lottery now uses dialog-owned canonical roll generation
- Files: `focus_blocker_qt.py`, `lottery_animation.py`
- `FocusTimerLotteryDialog` now supports canonical roll generation when no item/pre-roll is supplied.
- The dialog passes that explicit roll into backend rarity resolution (`roll_focus_reward_outcome(..., roll=...)`) and generates item using resolved tier.
- Session reward caller now opens the dialog first and consumes `dialog.get_results()` for actual awarded item.

Effect:
- Focus-session indicator movement and backend rarity resolution now share the same roll source.
- Caller-side backend pre-roll before animation has been removed.

### F. Activity base reward now uses canonical dialog result for the awarded item
- Files: `focus_blocker_qt.py`, `lottery_animation.py`
- `ActivityLotteryDialog` now supports canonical roll generation when no pre-awarded item is provided.
- The activity logger now uses `ActivityLotteryDialog.get_results()` as the base reward actually awarded to the user.
- Backend `roll_activity_reward_outcome(..., roll=...)` is used by the dialog in this path.

Effect:
- The base activity reward shown by the indicator is now the same item/tier awarded.
- Trust-model drift between displayed activity roll and awarded base item is removed.

### G. Eye routine lottery now finalizes backend from animation-authored rolls
- File: `eye_protection_tab.py`
- Eye routine now opens `MergeTwoStageLotteryDialog` with dialog-generated rolls.
- After animation, backend outcome is finalized via `roll_eye_routine_reward_outcome(...)` using
  dialog rolls (`success_roll`, `tier_roll`) as explicit overrides.
- Reroll path uses the same pattern.
- Lock metadata (`power_gating`) is still pre-probed so the visual lane/ceiling remains accurate.

Effect:
- Eye routine outcomes are now determined from the same rolls shown in animation.
- Caller-side backend pre-roll before animation has been removed for this path.

### H. Weight daily-progress primary reward now uses canonical dialog roll
- Files: `lottery_animation.py`, `focus_blocker_qt.py`
- `WeightLotteryDialog` now supports canonical generation for daily progress rewards:
  - rolls via `roll_daily_weight_reward_outcome(..., roll=...)`
  - item generation from resolved rarity
- Weight reward flow now uses dialog result as the awarded daily primary item when:
  - primary source is daily reward
  - mode is `loss` or `gain`
  - progress is in the target direction
- Non-daily primary sources (weekly/monthly/streak/milestone/maintenance) remain reveal-style in this pass.

Effect:
- For daily progress primary cases, animation roll and awarded item are now aligned.

## Validation
- `python -m py_compile merge_dialog.py lottery_animation.py eye_protection_tab.py tests/test_lottery_rarity_consistency.py`
- `pytest -q tests/test_lottery_rarity_consistency.py`
- `pytest -q tests/test_gamification.py -k "lucky_merge or roll_merge_lottery"`
- `pytest -q test_lucky_merge_comprehensive.py`
- `python tools/check_text_integrity.py --mode strict`
- `pytest -q tests/test_gamification.py -k "priority_completion_reward"`
- `python -m py_compile lottery_animation.py focus_blocker_qt.py tests/test_lottery_rarity_consistency.py`
- `pytest -q tests/test_lottery_rarity_consistency.py` (includes activity/focus/water/priority canonical roll tests)
- `pytest -q tests/test_gamification.py -k "eye_routine_outcome"`
- `pytest -q tests/test_lottery_rarity_consistency.py` (includes weight daily canonical test)

All passed.

## Remaining Gap To Full Industry-Standard Consistency
To fully standardize all lotteries around one strict ground-truth model, the same pattern should be applied to remaining systems that still pre-roll and reveal:
- Activity reward aggregation still computes a provisional base reward before dialog (now overridden by canonical dialog result)
- Sleep reveal paths where backend award is determined before animation
- Weight non-daily primary sources remain reveal-style (deterministic timed rewards)
- Any other dialog using `pre_rolled_*` outcome payloads

Recommended standard:
1. Animation owns roll generation or receives explicit canonical rolls.
2. Backend consumes exactly those roll values.
3. Persistence and UI notifications happen only after animation completion.
4. Add tests that assert backend receives animation roll values (not fresh random values).

### I. Sleep flow cleanup: single lottery + canonical message sync
- File: `focus_blocker_qt.py`
- Removed duplicated post-award `SleepLotteryDialog` execution. Sleep now shows one lottery before commit.
- When canonical base-sleep roll replaces the provisional reward, the human-readable message list is updated to the same rolled rarity.

Effect:
- No second reveal after award.
- Text shown to user cannot contradict the rolled/awarded base sleep rarity.

### J. Timeline notifications deferred until after reward finalization (weight/activity)
- File: `focus_blocker_qt.py`
- `notify_weight_entry_changed()` now fires after weight lottery + award path completes.
- `notify_activity_entry_changed()` now fires after reward/city side effects are finalized.

Effect:
- Reduces perceived "state moved before lottery/reward finished" behavior in timeline-dependent UI.

### K. Merge stage-1 UI hardening for Celestial lane behavior
- File: `lottery_animation.py`
- Removed redundant celestial info row from stage-1 merge card.
- Hardened stage-1 ceiling handling:
  - treat near-100 ceilings as fully unlocked (float-safe epsilon)
  - keep full-bar traversal when celestial lane is visible and no lock tiers apply.

Effect:
- Cleaner stage-1 panel.
- Prevents accidental clamping that can make Celestial lane appear unreachable due floating-point drift.

## Additional Validation
- `python -m py_compile focus_blocker_qt.py lottery_animation.py`
- `pytest -q tests/test_lottery_rarity_consistency.py`
- `pytest -q tests/test_gamification.py -k "sleep_entry_reward or eye_routine_outcome or priority_completion_reward"`

All passed.
