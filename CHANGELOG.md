# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Reusable Lottery Animation System** (`lottery_animation.py`):
  - Factored out dramatic slot-machine style roll animation from merge dialog into reusable module.
  - `LotteryRollDialog`: Single-stage bouncing slider animation with configurable threshold.
  - `LotterySliderWidget`: Custom-painted probability bar with WIN/LOSE zones.
  - `TwoStageLotteryDialog`: Two-stage lottery for Item Drop + Tier determination.
  - `MultiTierLotterySlider`: 5-tier rarity visualization for Priority Completion rewards.
  - `PriorityLotteryDialog`: Two-stage lottery specifically for Priority Completion (Win/Lose + Rarity roll).
  - `TierJumpSliderWidget`: 4-zone visualization for merge tier jumps (+1/+2/+3/+4).
  - `MergeTwoStageLotteryDialog`: Two-stage lottery for gear merging (Success + Tier Jump).
  - Eye Protection tab now uses the same animation system as gear merging for consistent UX.
  - **Priority Completion now shows animated lottery** instead of plain message boxes:
    - Stage 1: Win/Lose roll (15-99% based on logged hours)
    - Stage 2: Rarity roll (5% Common, 10% Uncommon, 30% Rare, 35% Epic, 20% Legendary)
  - **Gear Merge now shows two-stage animated lottery**:
    - Stage 1: Success/Fail roll (based on item count and merge luck)
    - Stage 2: Tier Jump roll (+1: 50%, +2: 30%, +3: 15%, +4 JACKPOT: 5%)
- **Health Reminder Notifications**:
  - Eye & Breath tab: Toggle periodic toast reminders (configurable interval, default 60 min).
  - Water tab: Toggle periodic hydration reminders (configurable interval, default 60 min).
  - Activity tab: Existing daily reminder at a specific time.
  - All reminders use system tray toast notifications for non-intrusive alerts.
- **Eye & Breath Protection**:
  - New tab "🌬️ Eye & Breath" dedicated to eye strain relief and mindful breathing.
  - Interactive routine with guided blinking (Close/Hold/Open) and breathing (4s Inhale / 6s Exhale).
  - Uses specific sound cues for each phase to allow users to follow along without looking at the screen.
  - Rising/Falling pitch sequences for breath guidance.
  - Rewards users with "Lottery" items upon completing the routine (5% base chance for Legendary, increasing daily).

### Improved
- **Sound System**:
  - Refactored `SoundGenerator` to use threaded playback, preventing UI freezes during sound sequences.
  - Added new sound patterns: Rising pitch (Inhale), Falling pitch (Exhale), and 3-tone Blink cues.
  - **Lottery sounds** (`lottery_sounds.py`): Complete refactoring with data-driven melody composition
    - Replaced 40 repetitive composer functions with dataclass-based design (`ToneSpec`, `ChordSpec`, `MelodyDefinition`)
    - Added sound caching for zero-latency playback via `preload_lottery_sounds()`
    - Added `__all__` exports, comprehensive type hints, and thread safety documentation
    - Added 51 unit tests covering melody integrity, caching, edge cases, and graceful degradation
- **Sleep Logic**:
  - Sleep suggestions ("Go to Sleep") are now suppressed before 22:00 to prevent nagging.
  - Sleep rewards (Screen Off Bonus) configured to start effectively after 22:00.
- **Code Architecture**:
  - Removed ~270 lines of duplicate animation code from `merge_dialog.py` (now imports from shared module).

## [5.6.3] - 2026-01-11

### Improved
- **ADHD Buster Tab UX Overhaul**:
  - Made "Active Set Bonuses", "Potential Set Bonuses", and "Gear Bonus Effects" sections collapsible.
  - Collapsible sections remember their collapsed/expanded state across sessions.
  - Converted verbose multi-line bonus displays to compact single-line format, significantly reducing vertical space.
  - Used colored icons and inline descriptions for better visual scanning.
- **Item Details Panel**:
  - Fixed special attributes display to show ALL lucky options individually (Coin Bonus, XP Bonus, Drop Luck, Merge Luck).
  - Each special attribute now displayed on its own line with distinctive icon and color.
  - Replaced combined "Lucky Options" string with individual attribute breakdown.

## [5.1.2] - 2026-01-08

### Fixed
- Fixed chart goal line label to display correct unit (kg/lbs) instead of raw stored value.
- Fixed lbs change calculation in entries table (was showing incorrect conversion).
- Fixed goal input range initialization when user preference is lbs (ranges now set before loading value).
- Max date for weight entries now refreshes on each display (handles app open past midnight).

## [5.1.1] - 2026-01-08

### Fixed
- **CRITICAL**: Fixed monthly reward being incorrectly assigned to weekly_reward variable.
- **CRITICAL**: Prevented future date selection in weight tracker (max date = today).
- **HIGH**: Fixed reward calculation when updating existing weight entries (now excludes current date from comparison).
- **HIGH**: Added null safety checks for stats display to prevent crashes with corrupted data.
- **HIGH**: Added validation for weight entries on config load (filters invalid/malformed entries).
- Fixed floating point precision issues in weight loss calculations (now properly rounds to 0.1g).
- Fixed goal weight unit conversion - goal now properly stored in kg and converted for display.

## [5.1.0] - 2026-01-08

### Added
- **Weight Tracker Tab**: New dedicated tab for daily weight tracking with visual progress chart.
- Weight logging with date selection and kg/lbs unit support.
- Custom Qt-based weight chart with trend visualization (green = loss, red = gain).
- Goal weight setting with goal line displayed on chart.
- **Weight Loss Gamification Rewards**:
  - Daily rewards based on weight loss: Same weight = Common, 100g = Uncommon, 200g = Rare, 300g = Epic, 500g+ = Legendary.
  - Weekly bonus: 500g loss in 7 days earns a Legendary item.
  - Monthly bonus: 2kg loss in 30 days earns a Legendary item.
- Weight statistics display: current, starting, lowest, highest, trends, and entry streak.
- Recent entries table with delete functionality.
- 33 new unit tests for weight tracking functionality.

## [5.0.8] - 2026-01-08

### Fixed
- **HIGH**: Fixed daily reward race condition - date now set BEFORE item generation to prevent duplicate rewards on rapid open/close.
- Improved priority check-in timing using interval counting instead of narrow time window (no more missed check-ins).
- Added extra confirmation dialog when using Emergency Cleanup during STRICT or HARDCORE sessions.

### Improved
- Priority check-in system now reliably triggers at each interval without timing dependency.
- Emergency Cleanup now warns users about bypassing their chosen strict mode protection.

## [5.0.7] - 2026-01-08

### Fixed
- **CRITICAL**: Config and stats files now use atomic writes (write-to-temp-then-rename) to prevent data corruption on crash.
- **CRITICAL**: Merge system now filters out None items to prevent crashes from corrupted inventory data.
- Added session timer guard to prevent starting new session while one is already running.
- Improved merge item removal with verification - fallback deletion now verifies item identity before removing.
- All merge-related functions now safely handle None items in the items list.

### Security
- Atomic file writes prevent data loss if app crashes mid-save.

## [5.0.6] - 2026-01-08

### Added
- **Optimize Gear button**: Automatically equips the best items for maximum power (including set bonuses).
- **Potential Set Bonuses display**: Shows which items in your inventory could be equipped together for set bonuses.
- Set bonus hints with color coding: orange for partial sets, blue for unequipped sets.
- Smart optimization algorithm considers both base power and set synergies.
- Preview of gear changes before applying with power gain calculation.

### Improved
- Better visibility of the set bonus system with actionable recommendations.
- Added tooltip explaining the Optimize Gear feature.

## [5.0.5] - 2026-01-08

### Added
- Desktop notification when focus session completes (Windows system tray balloon).
- "🔔 Notify me when session ends" checkbox in Focus tab (enabled by default).
- Preference is saved and persisted across sessions.
- Notifications work for regular sessions, Pomodoro work sessions, and break completions.

## [5.0.4] - 2026-01-08

### Fixed
- Added robust `_is_item_equipped()` helper that uses timestamp + name/slot/rarity fallback.
- Fixed equipped detection for legacy items without `obtained_at` timestamps.
- Improved item removal logic to handle mixed items (with/without timestamps).
- Added verification that correct number of items were removed from inventory.
- Fixed duplicate `else` block that caused syntax error.

## [5.0.3] - 2026-01-08

### Fixed
- Fixed equipped item detection to require valid timestamps (not None/empty).
- Fixed merge selection count to show only valid indices.
- Added safe rarity lookup in gamification.py to handle invalid/missing rarity values.
- Improved robustness of merge functions against corrupted item data.

## [5.0.2] - 2026-01-08

### Fixed
- Hardened merge logic against stale inventory indices and race conditions.
- Added validation to detect if inventory changed between selection and merge.
- Added safety check for items missing `obtained_at` timestamp (auto-fixes data).
- Changed item removal to use timestamp matching instead of fragile index deletion.
- Added fallback to index-based deletion if timestamp matching fails.

## [5.0.1] - 2026-01-08

### Fixed
- Equipped items can no longer be selected for Lucky Merge.
- Previously equipped items could be merged and destroyed, losing them permanently.
- Added safety checks at selection, validation, and merge execution levels.

## [5.0.0] - 2026-01-08

### Removed
- **BREAKING**: Removed heavy AI libraries (torch, transformers, sentence-transformers).
- Removed `local_ai.py` GPU-based sentiment analysis module.
- Removed `requirements_ai.txt` and `install_ai.bat`.
- Removed AI documentation files (`AI_FEATURES.md`, `AI_TAB_GUIDE.md`, `GPU_AI_GUIDE.md`).

### Changed
- Application size reduced from ~3GB to ~100MB.
- Session complete dialog simplified (no AI sentiment analysis).
- AI Tab now shows lightweight pattern analysis only.
- Updated branding to focus on gamification rather than AI.

### Kept
- `productivity_ai.py` (lightweight JSON/datetime analysis - no ML dependencies).
- Full gamification system (ADHD Buster, hero progression, achievements).

## [4.2.7] - 2026-01-08

### Changed
- ADHD Buster dialog is now blocked during active focus sessions.
- Users must complete or stop their session before modifying inventory/equipment.

## [4.2.6] - 2026-01-08

### Fixed
- Priority check-in now waits for the configured interval before first prompt.
- Previously the check-in dialog appeared immediately when starting a session.

## [4.2.5] - 2026-01-08

### Fixed
- Session completion dialog no longer freezes the application.
- Removed unnecessary AI model loading during session complete.
- Deferred reward processing to keep UI responsive.
- Added UI event processing during session transitions.

## [4.2.4] - 2026-01-08

### Fixed
- Character graphics now correctly display the selected story theme (scholar, wanderer, underdog).
- Previously all stories showed the warrior/knight character regardless of selection.
- Character canvas updates properly when switching stories.

## [4.2.3] - 2026-01-08

### Fixed
- Installer now forcefully closes running instances before upgrading.
- Installer removes scheduled task before file replacement to prevent "Access denied" errors.
- Added `CloseApplications=force` to handle locked files during upgrades.

## [4.2.2] - 2026-01-08

### Changed
- Autostart now uses Task Scheduler with admin privileges instead of registry.
- App will start with administrator rights on Windows login (required for blocking).

## [4.2.1] - 2026-01-01

### Fixed
- Uninstall now properly deletes user data files from install directory when user chooses not to keep settings.

## [4.2.0] - 2025-12-31

### Added
- Community health files: `CONTRIBUTING.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`.
- Version info embedded in Windows EXE (shows in file properties).
- `.ico` format tray icons for better Windows compatibility.

### Fixed
- Python 3.9 compatibility (replaced union type syntax with `Optional`).
- Complete uninstall cleanup (processes, shortcuts, scheduled tasks, log files).
- CI build pipeline (added .spec files to repository).

## [4.1.0] - 2025-12-31

### Added
- **AI-Powered Smart Insights**: Machine learning analysis of productivity patterns.
- **Gamification System**: Achievements, daily challenges, and leveling system.
- **New Character Themes**: "Wanderer" theme with mystical styling.
- **System Tray Improvements**: Quick actions and better background handling.

### Changed
- Improved UI with 7-tab interface.
- Enhanced blocking mechanism for better reliability.

### Fixed
- Various bug fixes and performance improvements.
