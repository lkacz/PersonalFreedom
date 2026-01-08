# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
