# Emoji Corruption Bug Report

## Problem

Emojis throughout the application display as garbled characters (mojibake) instead of proper emoji glyphs. For example, tab labels show sequences like `dżŽŻ Focus` instead of `🎯 Focus`, and stat circle icons render as Central European characters instead of emoji.

---

## Root Cause

**Two critical files have corrupted emoji bytes due to a UTF-8 BOM + encoding mismatch:**

| File | Size | BOM Present | Emoji Status |
|------|------|-------------|-------------|
| `focus_blocker_qt.py` | ~1.8 MB | YES (`EF BB BF`) | **CORRUPTED** |
| `gamification.py` | ~0.9 MB | YES (`EF BB BF`) | **CORRUPTED** |

The emoji `🎯` (U+1F3AF) should be stored as UTF-8 bytes `F0 9F 8E AF`, but in these files it is stored as `C4 8D C5 BA C5 BD C5 BB` — which decodes as `čźŽŻ` (Central European/Czech characters). This strongly suggests the files were re-saved through a process that interpreted 4-byte UTF-8 emoji sequences through a CP1250 (Windows Central European) codepage, or underwent a double-encoding corruption.

All other Python files in the project store emoji correctly as standard UTF-8 without BOM.

---

## Scope of Impact

### Corrupted (from `focus_blocker_qt.py`)

- **All 15+ main tab labels** — `addTab()` / `setTabText()` calls at lines ~36874-36963:
  ```python
  self.tabs.addTab(self.timer_tab, "dżŽŻ Focus")       # Should be "🎯 Focus"
  specs.append({"attr": "story_tab", "title": "dź"ś Story"})  # Should be "📜 Story"
  specs.append({"attr": "city_tab", "title": "dźŹ° City"})    # Should be "🏰 City"
  ```
- **Mini-stat circle icons** (Today, Streak, Sessions) at lines ~2979-3010:
  ```python
  create_mini_stat("dź"Š", "Today", ...)    # Should be 📊
  create_mini_stat("dź"Ą", "Streak", ...)   # Should be 🔥
  create_mini_stat("âś…", "Sessions", ...)  # Should be ✅
  ```
- **Section headers** — Stats, Health Dashboard, AI Assistant headers
- **Button text and tooltips** throughout the main window

### Corrupted (from `gamification.py`)

- **Theme names and emojis** in entity/set definitions:
  ```python
  "theme_name": "dź"š Scholar's Tools"   # Should be "📚 Scholar's Tools"
  "emoji": "dź‰"                          # Should be "🐉"
  ```
- **Comment text** — even inline comments show `â‰¤` instead of `≤`

### Correct (unaffected files)

| File | Technique | Example |
|------|-----------|---------|
| `entitidex_tab.py` | **Unicode escapes** | `"\U0001F5E1\ufe0f Warrior"` |
| `session_complete_dialog.py` | Inline UTF-8 (no BOM) | `"🎉"`, `"⏱️"`, `"📊"` |
| `city_tab.py` | Inline UTF-8 (no BOM) | `"⚡"`, `"🎯"`, `"✨"` |
| `merge_dialog.py` | Inline UTF-8 (no BOM) | `"⛑️"`, `"🛡️"`, `"⚔️"` |
| `entity_encounter_dialog.py` | Inline UTF-8 (no BOM) | `"🎉"`, `"💨"` |
| `entitidex/entity_pools.py` | Inline UTF-8 (no BOM) | `"⚪"`, `"🟢"`, `"🔵"` |
| `entitidex/entity_perks.py` | Inline UTF-8 (no BOM) + fallback | `"✨"`, `"🔮"` |
| `eye_protection_tips.py` | Inline UTF-8 (no BOM) | `"🌞"`, `"💻"` |

---

## Existing Workaround in Codebase

The developers are already aware of this issue. `entitidex/entity_perks.py` (lines 88-151) contains a **garbled icon detection and fallback system**:

```python
_GARBLED_ICON_MARKERS = ("â", "dź", "ď", "ť", "ź", "Ž", "™", "€", "\x80", "ˆ", "\x8d", "\x9d")

def _is_garbled_icon(icon: str) -> bool:
    if any(marker in icon for marker in _GARBLED_ICON_MARKERS):
        return True
    ...

def get_perk_icon(perk: EntityPerk) -> str:
    if not _is_garbled_icon(perk.icon):
        return perk.icon
    return PERK_TYPE_FALLBACK_ICONS.get(perk.perk_type, "✨")
```

This detects mojibake patterns and substitutes safe fallback emoji. However, this workaround is only applied to entity perk icons — it does not cover tab labels, stat circles, section headers, or gamification theme emojis.

---

## Contributing Factors

### 1. No Application-Wide Emoji Font

The `QApplication` is created without specifying a font that includes emoji support:

```python
app = QtWidgets.QApplication(sys.argv)
app.setApplicationName("Personal Liberty")
# No setFont() or setStyleSheet() call with emoji font
```

The only place `Segoe UI Emoji` is explicitly used is for the timeline ring painter (`focus_blocker_qt.py:32388`). All `QLabel` and `QTabWidget` elements rely on Qt's default font fallback, which may not always resolve emoji codepoints correctly.

### 2. No `.gitattributes` Encoding Rules

The `.gitattributes` file only handles binary/LFS files:

```
*.exe filter=lfs ...
*.dll filter=lfs ...
```

There is no `*.py text working-tree-encoding=UTF-8` rule to enforce encoding on checkout/commit, meaning Git cannot prevent encoding corruption on Windows.

### 3. No `PYTHONUTF8=1` in CI/Build

The GitHub Actions CI workflow (`.github/workflows/ci.yml`) does not set `PYTHONUTF8=1` or run `chcp 65001`. While Python 3 reads `.py` source as UTF-8 by default (PEP 3120), the absence of explicit UTF-8 mode can cause issues with file I/O at runtime on Windows.

### 4. Inconsistent Emoji Encoding Strategy

The codebase uses three different approaches for emoji, with no standard:

| Approach | Resilience | Used In |
|----------|-----------|---------|
| Unicode escapes (`\U0001F3AF`) | **Immune** to encoding corruption | `entitidex_tab.py` |
| Inline UTF-8 literals (`🎯`) in non-BOM files | **Safe** if file encoding preserved | Most dialog files |
| Inline UTF-8 literals in BOM files | **BROKEN** | `focus_blocker_qt.py`, `gamification.py` |

---

## Recommendations

### Immediate Fix

1. **Re-save `focus_blocker_qt.py` and `gamification.py`** as UTF-8 without BOM. All corrupted emoji byte sequences must be replaced with correct UTF-8 emoji or Unicode escape sequences.

2. **Convert all emoji literals in these two files to Unicode escape sequences** for resilience:
   ```python
   # Instead of:
   self.tabs.addTab(self.timer_tab, "🎯 Focus")
   # Use:
   self.tabs.addTab(self.timer_tab, "\U0001F3AF Focus")
   ```

### Preventive Measures

3. **Add encoding rules to `.gitattributes`:**
   ```
   *.py text eol=lf working-tree-encoding=UTF-8
   ```

4. **Set `PYTHONUTF8=1`** in CI and recommend it for development environments.

5. **Add a pre-commit hook or CI check** that detects UTF-8 BOM in Python files and rejects them.

6. **Standardize on Unicode escape sequences** for all emoji in Python source files, project-wide. This is the only encoding-corruption-proof approach.

7. **Set an application-wide font** with emoji fallback at startup:
   ```python
   font = QFont("Segoe UI", 10)
   font.setFamilies(["Segoe UI", "Segoe UI Emoji"])
   app.setFont(font)
   ```

8. **Expand the garbled-icon detection system** from `entity_perks.py` to cover all emoji rendering paths as a safety net.

---

## How to Verify the Fix

1. Open `focus_blocker_qt.py` in a hex editor and search for the byte sequence `EF BB BF` at position 0 — this is the BOM to remove.
2. Search for any byte sequence starting with `C4 8D C5` near string literals that should contain emoji — these are corrupted emoji.
3. After fixing, all tab labels, stat circle icons, and section headers should display proper emoji glyphs.
4. Run the garbled icon detection function against all emoji strings to confirm zero detections.
