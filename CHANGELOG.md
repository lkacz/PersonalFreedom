# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
