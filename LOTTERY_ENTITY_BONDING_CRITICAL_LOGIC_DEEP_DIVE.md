# Lottery and Entity Bonding Critical Logic Deep Dive

Date: 2026-02-18
Project: PersonalFreedom

## Implementation Progress (2026-02-18)

This pass implemented a Phase-1 subset:
- Added missing entity collection signal on successful normal live bond path.
  - `gamification.py`
- Added explicit risky finalize contract fields:
  - `operation_success`
  - `bond_success` (while keeping `success` for backward compatibility)
  - `gamification.py`
- Deferred save/refresh in key encounter callbacks until after encounter flow returns:
  - `entitidex_tab.py` saved encounter open path
  - `focus_blocker_qt.py` session and bypass encounter paths
- Added regression tests:
  - `tests/test_entitidex_bond_contract.py`

## Implementation Progress Update (2026-02-18, later pass)

This pass implemented the core Phase-2 "animation-authored roll" contract for entity bonding:

- `show_entity_encounter` now animates first and finalizes backend with the exact roll shown.
  - `entity_drop_dialog.py`
- Roll override is now consumed in backend finalize paths:
  - `attempt_entitidex_bond(...)`
  - `open_saved_encounter_with_recalculate(...)`
  - `finalize_risky_recalculate(...)`
  - `entitidex/catch_mechanics.py`
  - `entitidex/entitidex_manager.py`
- Saved encounter callback wrappers now accept/pass `roll_override`:
  - `entitidex_tab.py`
  - `focus_blocker_qt.py` (normal, bypass, and encounter/debug wrappers)
- Risky recalculate flow now uses two visible lotteries before backend finalize:
  - Stage 1: risky recalc success/fail roll
  - Stage 2: bond roll at selected probability
  - `entitidex_tab.py`
- Added regression tests for canonical roll usage:
  - `tests/test_entitidex_bond_contract.py`
  - verifies no backend re-roll when `roll_override` is provided.

Resolved caveat:
- Saved encounter paid-recalc preconditions are now preflight-checked before lottery animation starts.

## Implementation Progress Update (2026-02-18, follow-up pass)

This follow-up closed two remaining UX-consistency gaps:

- Added paid-recalculate preflight checks before opening saved-encounter lottery:
  - lock check (`has_paid_recalculate`)
  - coin affordability check (`recalculate_cost`)
  - `entitidex_tab.py`
  - Result: no more post-animation failure for common paid-recalculate denial states.

- Updated merge stage-1 celestial visualization to allow true celestial-lane landings:
  - If Celestial is triggered, stage-1 target position is now selected from the visible Celestial lane.
  - Stage-1 display tier and stage-2 wording now align with Celestial outcomes.
  - `lottery_animation.py`

- Added regression test for celestial-lane targeting:
  - `tests/test_lottery_rarity_consistency.py`

## Implementation Progress Update (2026-02-18, stability pass)

Additional hardening applied:

- Contract coverage for paid recalculation failures now explicitly tested:
  - missing paid-perk unlock -> `operation_success=False`
  - insufficient coins -> `operation_success=False`
  - `tests/test_entitidex_bond_contract.py`

- Hydration lottery caller-side pre-roll removed so the lottery dialog owns roll generation path:
  - `focus_blocker_qt.py`
  - `lottery_animation.py` (`WaterLotteryDialog`)

- Added regression test verifying WaterLotteryDialog passes explicit canonical roll overrides into backend rarity evaluation:
  - `tests/test_lottery_rarity_consistency.py`

## Implementation Progress Update (2026-02-18, priority canonical pass)

Priority completion flow was aligned with the same canonical-roll contract used in recent passes:

- Removed caller-side pre-roll from priority completion UI path.
  - `focus_blocker_qt.py`
- Added backend support for explicit canonical roll overrides:
  - `roll_priority_completion_reward(..., win_roll_override, rarity_roll_override)`
  - `gamification.py`
- `PriorityLotteryDialog` now generates canonical win/rarity rolls and forwards them to backend.
  - `lottery_animation.py`
- Added regressions:
  - `tests/test_lottery_rarity_consistency.py` (dialog forwards generated canonical rolls)
  - `tests/test_gamification.py` (backend honors override rolls)

## Implementation Progress Update (2026-02-18, focus canonical pass)

Focus session rewards were moved off caller-side pre-roll into dialog-owned canonical roll generation:

- `FocusTimerLotteryDialog` now supports canonical roll generation when no pre-generated item/outcome is supplied.
- The dialog forwards that roll into backend rarity resolution (`roll_focus_reward_outcome(..., roll=...)`), then generates item from resolved rarity.
- Session reward caller now consumes `lottery_dialog.get_results()` and awards the returned item post-animation.
- Regression added:
  - `tests/test_lottery_rarity_consistency.py` (`FocusTimerLotteryDialog` canonical-roll forwarding)

## Implementation Progress Update (2026-02-18, activity base canonical pass)

Activity base reward flow now consumes the canonical dialog result as the actually-awarded item:

- `ActivityLotteryDialog` can now generate canonical roll/outcome when no pre-awarded item is provided.
- It calls backend activity rarity evaluation with explicit roll (`roll_activity_reward_outcome(..., roll=...)`).
- Activity logging caller now writes dialog result back into the reward payload before processing awards.
- Regression added:
  - `tests/test_lottery_rarity_consistency.py` (`ActivityLotteryDialog` canonical-roll forwarding)

## Implementation Progress Update (2026-02-18, eye routine canonical pass)

Eye routine lottery now resolves backend outcomes from animation-authored rolls:

- `eye_protection_tab.py` no longer consumes backend pre-rolled eye outcomes before opening dialog.
- `MergeTwoStageLotteryDialog` generates rolls; backend finalizes via `roll_eye_routine_reward_outcome(...)`
  with explicit `success_roll` / `tier_roll` from the dialog.
- Reroll path uses the same contract.
- Added test coverage for canonical-roll override handling:
  - `tests/test_gamification.py` (`test_eye_routine_outcome_respects_supplied_canonical_rolls`)

## Implementation Progress Update (2026-02-18, weight daily canonical pass)

Weight daily-progress primary rewards now support canonical dialog-authored roll resolution:

- `WeightLotteryDialog` can generate canonical daily outcome via backend roll API
  (`roll_daily_weight_reward_outcome(..., roll=...)`) when no pre-item is provided.
- Weight processing now consumes dialog result as the awarded daily primary item
  for loss/gain progress cases where daily reward is the primary displayed reward.
- Added regression:
  - `tests/test_lottery_rarity_consistency.py`
    (`test_weight_lottery_dialog_generates_canonical_daily_rolls_for_backend`)

## Scope

This audit focused on lottery truth-model consistency and sequencing across:
- live entity bonding
- saved encounter opening (normal, paid recalc, risky recalc)
- merge lottery (including celestial lane behavior)
- supporting UI callback paths that can mutate state before/after visible lottery completion

Primary question: does the final indicator movement determine outcomes, or only reveal already-resolved outcomes?

Note:
- The detailed findings section below began as a baseline snapshot before the implementation passes above.
- Where it conflicts with the implementation updates, treat the implementation updates as authoritative.

## Current Architecture Snapshot

1. Merge flow is now animation-authoritative for roll values.
- `merge_dialog.py:2050`
- `merge_dialog.py:2081`

2. Entity bonding flow is now animation-authored and backend-finalized with the same roll.
- `entity_drop_dialog.py`
- `gamification.py`

3. Saved encounter open/recalculate consumes animation-authored roll overrides.
- `entitidex_tab.py`
- `gamification.py`

4. Risky recalculate uses explicit two-stage slider animation (risky roll + bond roll) before finalize.
- `entitidex_tab.py`
- `gamification.py`

5. Priority and water now use dialog-owned canonical roll generation with explicit backend roll overrides.
- Priority: `focus_blocker_qt.py:31165`, `lottery_animation.py:1694`, `gamification.py:6887`
- Water: `focus_blocker_qt.py:25702`, `lottery_animation.py:3775`, `gamification.py:18744`

6. Other reward lotteries remain mostly backend-first reveal models (with better post-animation persistence sequencing than entity bonding).
- Activity base reward is now dialog-canonical; aggregation still computes provisional base reward before override.
- Eye routine is now dialog-canonical for both first roll and reroll.
- Weight daily primary is now dialog-canonical; non-daily primary sources remain reveal-style.

## Severity-Ordered Findings

### 1. Critical: Entity bonding is still resolved before the visible lottery

In `show_entity_encounter`, bonding logic is executed first, then the lottery dialog is shown using returned roll/probability.

- backend resolution first: `entity_drop_dialog.py:1156`
- probability/roll read from backend: `entity_drop_dialog.py:1167`
- animation shown after resolution: `entity_drop_dialog.py:1196`

Implication:
- The indicator does not determine the bond outcome in this flow.
- The animation is a reveal layer for already-committed state.

### 2. Critical: Entity state persistence and UI refresh can happen before animation completes

Because callbacks run before `LotteryRollDialog`, several flows persist and refresh immediately.

Saved encounter tab callback:
- `entitidex_tab.py:3527`
- `entitidex_tab.py:3537`
- `entitidex_tab.py:3542`

Session encounter callback path:
- `focus_blocker_qt.py:4617`
- `focus_blocker_qt.py:4626`
- `focus_blocker_qt.py:4639`

Bypass encounter callback path:
- `focus_blocker_qt.py:4838`
- `focus_blocker_qt.py:4849`
- `focus_blocker_qt.py:4860`

Implication:
- Users can observe collection/progress updates that are logically already finalized while lottery animation is still running.
- This is exactly the trust-break pattern reported by users.

### 3. High: Saved encounter paid flow consumes encounter and rolls outcome before animation

`open_saved_encounter_with_recalculate` pops the saved encounter and performs `random.random()` roll in backend.

- pop consumed encounter: `gamification.py:23146`
- backend roll: `gamification.py:23149`

Implication:
- By the time UI animates in `show_entity_encounter`, result is already committed.
- Any interruption during animation is a reveal interruption, not a pending decision.

### 4. High: Risky recalc path lacks indicator-based lottery UX and conflates statuses

Risky flow currently:
- pre-roll risky result in backend: `gamification.py:23302`
- show info popup text, not slider lottery: `entitidex_tab.py:3581`
- finalize then perform bond roll in backend: `gamification.py:23400`

Also, `success` in `finalize_risky_recalculate` means bond success, not operation validity.
- `gamification.py:23465`

Implication:
- The central lottery path is message-driven here, not visibly roll-driven.
- Error and bond-failure semantics are easy to mishandle in callers.

### 5. High: Missing entity-changed signal on normal live bond path

Normal `attempt_entitidex_bond` path saves progress but does not emit `notify_entity_collected` on success.

- save done: `gamification.py:21400`
- signal exists only in force-success path: `gamification.py:21350`
- signal exists in saved encounter paths: `gamification.py:23210`, `gamification.py:23463`

Implication:
- UI refresh behavior differs by bonding path, creating inconsistent timeline/ring updates.

### 6. Medium: Merge celestial lane semantics are visually ambiguous by design

The merge tier slider displays a celestial lane, but stage-1 tier roll is mapped to base (non-celestial) roll space and celestial lane maps back to Legendary for stage-1 tier identity.

- base scale mapping: `lottery_animation.py:2340`, `lottery_animation.py:2344`
- celestial lane remapped to Legendary tier identity: `lottery_animation.py:2322`
- stage-1 uses mapped display target + ceiling handling: `lottery_animation.py:3194`, `lottery_animation.py:3202`, `lottery_animation.py:3207`

Implication:
- Users can perceive that the marker "bounces off" or cannot truly land in celestial, because celestial is modeled as a separate bonus roll instead of stage-1 terminal tier outcome.

### 7. Medium: Encounter logic is duplicated across multiple entry points

There are many callback wrappers in `focus_blocker_qt.py` and tab-level flows with slightly different save/signal behavior.

- examples: `focus_blocker_qt.py:4549`, `focus_blocker_qt.py:4774`, `focus_blocker_qt.py:35313`, `focus_blocker_qt.py:35493`, `focus_blocker_qt.py:35609`, `focus_blocker_qt.py:35726`

Implication:
- Fixes can be applied in one path and regress in others.
- This increases recurring bug risk.

## Fit Against Desired Ground-Truth Model

Desired model (user requirement): the visible indicator movement should determine rarity and win/loss, not only reveal backend-pre-resolved outcomes.

Current fit:
- merge: partially aligned (animation-authored rolls now drive backend)
- entity live bond: not aligned
- saved encounter normal/paid/risky: not aligned
- risky recalc UX: not aligned

## Recommended Target Contract

1. Split lottery flows into two explicit phases:
- Phase A: compute thresholds/distributions only (no final state mutation).
- Phase B: animate and generate canonical roll(s), then finalize backend using exactly those rolls.

2. Backend finalize functions must accept external roll overrides.

3. Persist and emit UI signals only after animation completes and backend finalize returns.

4. Use explicit result envelopes:
- `operation_success` (request/process validity)
- `bond_success` (actual lottery outcome)
- avoid overloading `success` for both meanings.

## Proposed Implementation Sequence

### Phase 1 (low-risk correctness)

- Add missing live-bond entity signal on success.
- Standardize result envelope for risky recalc finalization.
- Stop pre-animation UI refresh/save in callback wrappers; defer post-animation.

### Phase 2 (core architecture alignment)

- Thread roll override through:
  - `attempt_entitidex_bond`
  - `EntitidexManager.attempt_catch`
  - `entitidex.catch_mechanics.attempt_catch`
- Update `show_entity_encounter` to animate first and finalize with the same roll.
- Add dedicated risky recalc slider animation and separate bond slider animation in risky flow.

### Phase 3 (merge celestial clarity)

Choose one of:
- Keep separate celestial roll but add explicit "Celestial Bonus Roll" stage.
- Or unify stage-1 into a single terminal roll distribution including celestial zone.

### Phase 4 (regression gates)

Add tests for:
- backend receives animation-authored roll in entity/saved/risky flows
- no pre-animation progress refresh side effects in UI callbacks
- consistent signal emission (`entities_changed`) across all successful bond paths

## Conclusion

The recurring trust issue is real and structural in entity-related lotteries: several critical paths are still backend-first reveal models, with pre-animation state commits and inconsistent signaling. Merge improvements are solid, but equivalent architecture has not yet been applied to entity bonding and saved encounter paths, which remain the highest-priority gap.

## Status Update (Implementation Pass)

The following items from this deep-dive are now addressed in code:

1. Saved encounter risky flow now uses animation-authored canonical rolls for both stages and finalizes backend with those exact values.
2. Merge stage-1 celestial traversal has additional guardrails:
- near-100 ceilings are treated as fully unlocked (float-safe)
- full visible bar traversal is preserved when celestial lane is available and no locks apply.
3. Merge stage-1 redundant rarity text row was removed to reduce visual noise.
4. Sleep flow no longer runs a duplicated second lottery after reward commit.
5. Weight/activity timeline notifications were moved to post-finalization points to reduce pre-finish UI drift perception.

Remaining architectural risk:
- Entity encounter behavior is still spread across multiple wrappers/callback entry points, so continued consolidation is recommended to reduce regression surface.
