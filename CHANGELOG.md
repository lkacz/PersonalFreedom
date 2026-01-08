# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
