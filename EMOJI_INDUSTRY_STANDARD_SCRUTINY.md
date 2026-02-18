# Emoji Handling Scrutiny vs Industry Standard

Date: 2026-02-18
Context: Review of current emoji handling implementation and prior "fixes".

## Post-Implementation Addendum (2026-02-18)

Revalidation after implementation shows the system is now aligned with the planned industry-standard controls for this repository.

### Current Status

1. Text integrity gate is implemented and active:
   - `tools/check_text_integrity.py` in strict mode.
   - pre-commit hook via `.pre-commit-config.yaml`.
   - CI gate via `.github/workflows/ci.yml`.
2. UTF-8 hardening added in CI:
   - `PYTHONUTF8=1`
   - `PYTHONIOENCODING=utf-8`
3. High-risk emoji paths were centralized and remediated:
   - token module: `emoji_tokens.py`
   - refactors/remediation in `gamification.py` and `focus_blocker_qt.py`
4. Strict integrity result is clean:
   - `BOM files: 0`
   - `Mojibake files: 0`
5. Tests validate the contract:
   - integrity checker tests,
   - repository strict integrity test,
   - token tests,
   - gamification tests.

### Updated Verdict

The original scrutiny findings remain valid as root-cause analysis, but the blocking gaps identified in this report have now been addressed in code, tooling, and CI.

## Verdict

Historical baseline verdict (pre-implementation): the implementation was **not industry-standard** yet and contained source-level mojibake regressions with missing preventive controls.

## Findings (Severity-Ordered)

### 1. Critical: Source of truth is currently corrupted in production paths

Mojibake is present in active UI and gameplay literals:
- `focus_blocker_qt.py:36917`
- `focus_blocker_qt.py:37001`
- `gamification.py:686`
- `gamification.py:752`
- `gamification.py:17667`
- `gamification.py:20100`

Impact:
- User-facing text renders as broken glyph sequences.
- Any downstream module consuming these constants inherits corrupted values.

### 2. Critical: No repository-level encoding guardrails

`.gitattributes` is LFS-only and does not enforce text encoding policy:
- `.gitattributes:1`

There is no `.editorconfig` in repo root (missing file).

Impact:
- Editors/tools can re-save text with unsafe transformations.
- Regressions are easy to reintroduce during unrelated edits.

### 3. High: CI does not validate text integrity / mojibake regressions

CI runs flake8/mypy/tests but has no encoding/mojibake gate:
- `.github/workflows/ci.yml:30`
- `.github/workflows/ci.yml:42`

Impact:
- Broken emoji literals can pass CI and ship.

### 4. High: Emoji strategy is inconsistent across modules

Examples of mixed approaches in same codebase:
- Corrupted raw emoji literals (`gamification.py:752`, `focus_blocker_qt.py:37001`)
- Safe escaped literals (`gamification.py:7581`, `gamification.py:14931`)
- Localized fallback sanitizer only for entitidex perks (`entitidex/entity_perks.py:92`, `entitidex/entity_perks.py:136`)

Impact:
- Partial fixes; inconsistent behavior by feature area.

### 5. High: Regression history shows fixes are not durable

Git history already shows fix -> regression cycles:
- `7060eb4` (mojibake fix)
- `996cf9f` (reintroduced mojibake in core files)

Impact:
- The current approach addresses symptoms, not process-level causes.

### 6. Medium: UTF-8 BOM appears in the two most affected Python files

Byte signature check shows BOM (`EF BB BF`) at file start:
- `gamification.py`
- `focus_blocker_qt.py`

Impact:
- Not always harmful in Python, but increases cross-tool inconsistency risk.
- Correlates with files showing repeated text encoding regressions.

### 7. Medium: Tooling scripts still include non-explicit text writes

Examples:
- `update_chestplate_celestial.py:32`
- `update_chestplate_celestial_v2.py:45`
- `update_shield_celestial.py:70`
- `update_shield_celestial_v2.py:159`
- `update_weapon_celestial_aligned.py:98`
- `update_weapon_celestial_saber.py:101`

Impact:
- On Windows defaults, text generation can vary by locale/code page.

## Industry-Standard Target Architecture

### A. Single authoritative text strategy

1. Centralize user-facing emoji labels in one module/resource (not scattered literals).
2. Prefer ASCII-only escaped forms (`\U0001F...`) for critical UI constants, or enforce guaranteed UTF-8 text pipeline across all tools.
3. Keep runtime fallback sanitizer only as a safety net, not as primary correctness mechanism.

### B. Repository-level encoding policy

1. Add `.editorconfig`:
- `charset = utf-8`
- consistent line endings and final newline policy

2. Expand `.gitattributes` for text normalization:
- mark source/docs as text
- enforce deterministic EOL policy

### C. Automated prevention gates

1. Add a text-integrity checker script that fails on:
- mojibake markers (`đź`, `â…` patterns, invalid control chars)
- UTF-8 BOM in Python source (if policy is no-BOM)
- forbidden mixed-encoding signatures

2. Run checker in:
- pre-commit hook
- CI workflow before lint/tests

### D. Test coverage for user-visible emoji contracts

Add tests for:
- main tab labels in `focus_blocker_qt.py` (`_build_deferred_tab_specs`)
- key gameplay constant tables in `gamification.py` (activity/sleep/reward emoji fields)
- roundtrip integrity checks for serialized display strings

### E. One-time migration and lock

1. Perform deterministic cleanup pass on `gamification.py` and `focus_blocker_qt.py`.
2. Validate with automated scanner and snapshot tests.
3. Lock with CI gate so future regressions cannot merge.

## Acceptance Criteria (Definition of Done)

1. Zero mojibake signatures in tracked source files.
2. No BOM in Python files (if adopted policy).
3. CI fails on encoding regressions.
4. Tab-label and key-constant emoji tests pass.
5. Re-run of same scanner on fresh checkout returns clean.
