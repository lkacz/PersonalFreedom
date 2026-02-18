# Emoji Formatting Recurring Bug Report

Date: 2026-02-18
Project: `PersonalFreedom`

## Scope

I reviewed how emoji text is authored, stored, and rendered across the app, with focus on why mojibake (for example `dź...` / `đź...`) keeps returning.

## How Emoji Is Implemented

1. Emoji is embedded directly in Python source literals in major runtime files:
- `focus_blocker_qt.py` (tab titles, button labels, dialogs, tooltips)
- `gamification.py` (story themes, rewards, activity/sleep data, narration strings)

2. Some subsystems are centralized and safer:
- `city/city_constants.py:25` uses centralized emoji constants.
- `entitidex/entity_perks.py:147` uses `get_perk_icon()` with mojibake detection and fallback icons (`entitidex/entity_perks.py:132`).

3. Rendering path is standard Qt string rendering:
- UI text goes into `QLabel`, `QPushButton`, tab labels, etc.
- Timeline point icons explicitly use emoji font at `focus_blocker_qt.py:32388` (`Segoe UI Emoji`).

Conclusion: this is primarily a source-text integrity problem, not a rendering engine problem.

## Concrete Findings

### 1) Current mojibake is in source code (not just display-layer noise)

Examples currently in repository:
- `focus_blocker_qt.py:37001` (`story_tab` title) contains mojibake literal.
- `focus_blocker_qt.py:37003` to `focus_blocker_qt.py:37023` tab titles contain mojibake literals.
- `focus_blocker_qt.py:36917` focus tab label contains mojibake literal.
- `gamification.py:752` (`Dragon` set emoji) contains mojibake literal.
- `gamification.py:17668` (`ACTIVITY_TYPES`) contains mojibake emoji literals.
- `gamification.py:20102` (`DAILY_LOGIN_REWARDS`) contains mojibake emoji literals.

Byte-level check confirms mojibake bytes are committed in these files (not a runtime decode glitch).

### 2) Corruption is concentrated in two core files

Marker scan for mojibake pattern (`đź` family) found only:
- `focus_blocker_qt.py`: 675 occurrences
- `gamification.py`: 450 occurrences

These same two files are also the only Python files with UTF-8 BOM in repo:
- `focus_blocker_qt.py`
- `gamification.py`

This strongly suggests repeated whole-file re-encoding/transcoding events on these two files.

### 3) Recurrence is confirmed by git history

Relevant history:
- `7060eb4` (2026-02-16 00:26+01:00): fixed mojibake to proper emoji in `gamification.py`.
- `996cf9f` (2026-02-16 21:31+01:00): reintroduced mojibake in both `gamification.py` and `focus_blocker_qt.py`.

Line-history proof:
- `gamification.py` line history shows `🐉` -> `đź‰` regression in `996cf9f`.
- `focus_blocker_qt.py` line history shows `📜 Story` -> `đź“ś Story` regression in `996cf9f`.

There was also an earlier regression/fix cycle in `gamification.py` (`1b3151f` then `7060eb4`), so this is not a one-off.

### 4) Mixed strategy in same file creates partial fixes

In `gamification.py`, some sections are resilient because they use Unicode escapes:
- `AVAILABLE_STORIES` entries (for example `gamification.py:7581`)
- `STORY_MODES` entries (for example `gamification.py:14931`)

But many other sections still use raw literals and are corrupted (`gamification.py:752`, `gamification.py:17668`, `gamification.py:20102`).

Result: app shows mixed behavior (some emoji paths fine, others broken).

### 5) Guardrails are missing at repo level

- No encoding policy file (`.editorconfig` charset) exists.
- No git text encoding enforcement exists in `.gitattributes`.
- CI (`.github/workflows/ci.yml`) runs lint/tests but has no mojibake/encoding regression check.
- Tests do not cover critical UI emoji labels in `focus_blocker_qt.py` tab construction.

### 6) Existing anti-mojibake handling is local, not systemic

`entitidex/entity_perks.py` includes `_is_garbled_icon()` and fallback icons, but this protection is scoped to entitidex perk icon rendering and does not protect general UI and gamification strings.

## Why This Bug Keeps Returning

Most likely recurrence mechanism:
1. Very large files (`focus_blocker_qt.py`, `gamification.py`) are edited frequently.
2. A tool/editor/process occasionally saves with incorrect text transformation for non-ASCII literals.
3. Fixes are later overwritten by new commits from an already-corrupted working copy or by re-encoding during edit.
4. No automated check blocks the regression at commit/CI time.

Because emojis are distributed across many hardcoded literals, even partial regressions immediately leak to UI.

## Summary

The recurring emoji formatting bug is caused by repeated source-level mojibake regressions in `focus_blocker_qt.py` and `gamification.py`, not by Qt rendering or font support. The regression is historically confirmed and currently present. The architecture (many distributed literals, mixed encoding styles, limited fallback scope, no CI guard) makes recurrence likely until encoding safety is enforced at source-control and test levels.

