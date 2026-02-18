# Celestial Integration Checklist

## Current Status

The Celestial tier is now integrated and hardened across core gameplay flows:

- Merge backend and UI are Celestial-aware.
- Legacy rarity casing (`"legendary"`, `"celestial"`, etc.) is handled in critical paths.
- Story gear pools are normalized to include Celestial adjective/suffix data at access time.
- Reward dialogs and major hero/entity UI surfaces render Celestial color/state correctly.

## What Is Robust Now

### Core rarity logic

- Canonical rarity normalization is used in merge-critical backend paths.
- Celestial merge unlock chance logic handles legacy lowercase rarities.
- Celestial merge rewards are generated via `generate_celestial_item(...)` with special-source metadata.

### Story gear pool integrity

- `get_story_gear_theme(...)` normalizes story adjective/suffix pools so `"Celestial"` is always present.
- `generate_item(...)` consumes normalized story theme pools.

### UI handling

- Hero/merge/item reward UI paths now include Celestial rarity colors.
- Entity encounter/drop dialogs include Celestial color mapping.
- Multiple legacy case-sensitive comparisons in UI inventory/sell/matching flows were hardened.

### Regression coverage

Added/updated tests verify:

- case-insensitive merge rarity behavior
- case-insensitive Celestial unlock from Legendary counts
- case-insensitive current-tier resolution
- story theme Celestial pool normalization

## Intentionally 5-Tier Systems (By Design)

The following systems remain capped below Celestial and should stay that way unless product rules change:

- Standard reward lotteries (Common..Legendary)
- Merge stage-1 rarity window (`MERGE_TIER_ORDER`)
- Priority/activity/sleep non-special reward distributions

Celestial is treated as a dedicated special-acquisition tier, not part of the default progression lottery.

## Remaining Low-Risk Follow-Ups

1. Centralize rarity color constants into a shared helper to reduce duplicate maps.
2. Add a lightweight smoke test that exercises a full UI reward pipeline using lowercase legacy rarity payloads.
3. If Celestial becomes generally obtainable later, revisit caps:
   - `MAX_OBTAINABLE_RARITY`
   - `MAX_STANDARD_REWARD_RARITY`
   - all 5-tier UI/lottery components.
