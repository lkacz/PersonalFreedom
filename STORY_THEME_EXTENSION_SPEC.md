# Story/Theme Extension Specification (Authoritative)

Status: Canonical implementation contract  
Last updated: 2026-02-14

## 1. Purpose

This file defines the mandatory contract for introducing a new story/theme/hero.

If this file conflicts with any other documentation, this file wins.

This is intentionally abstract and implementation-oriented. It defines required integration surfaces, schemas, and quality gates, not theme ideas.

## 2. Canonical Model

- `story_id` is the canonical identifier and must be lowercase snake_case.
- Story, gear theme, hero identity, Entitidex theme, and celebration theme share the same `story_id`.
- Canonical active key is `active_story`.
- `selected_story` is compatibility-only and must mirror `active_story` when story mode is active.
- `story_active` is invalid and must not be used.

Runtime source-of-truth registries:

- `AVAILABLE_STORIES` in `gamification.py`
- `STORY_GEAR_THEMES` in `gamification.py`
- `STORY_DATA` in `gamification.py`
- `ENTITY_POOLS` in `entitidex/entity_pools.py`
- `ENTITY_PERKS` in `entitidex/entity_perks.py`

Secondary maps (UI labels, tab metadata, debug lists, previews) must be derived from these registries or explicitly validated to stay in sync.

## 3. Non-Negotiable Invariants

1. A new story is incomplete unless all subsystems in Section 4 are wired.
2. Lists/counts must be data-driven; fixed story/entity totals are not allowed.
3. Each story must ship with 9 Entitidex entities (`<story_id>_001..009`) and perk coverage for all 9 IDs.
4. Story state migration must preserve existing user data and must not break old configs.
5. Story mode behavior (`story`, `hero_only`, `disabled`) must remain consistent after adding a story.
6. Unlock policy must be explicit (free vs paid, preview behavior, coin cost path).
7. Manual tooling (debug/admin/preview scripts) must either be updated or explicitly marked unsupported.

## 4. Required Touchpoints (Implementation Matrix)

| Area | Required Changes | Primary Files |
|---|---|---|
| Story registry | Add metadata entry and make story selectable | `gamification.py` (`AVAILABLE_STORIES`) |
| Gear generation | Add full gear theme dictionary and slot naming | `gamification.py` (`STORY_GEAR_THEMES`) |
| Narrative core | Add decisions, chapters, and story mapping | `gamification.py` (`<STORY>_DECISIONS`, `<STORY>_CHAPTERS`, `STORY_DATA`) |
| Diary narrative | Add diary theme data and sentence-style routing | `gamification.py` (`STORY_DIARY_THEMES`, diary sentence builder) |
| Hero visuals | Register character label and render path | `focus_blocker_qt.py` (`CharacterCanvas`, `STORY_MAIN_CHARACTER_NAMES`) |
| Story-state keys | Keep `active_story` as canonical across reward/state flows | `gamification.py`, `game_state.py`, `eye_protection_tab.py` |
| Story unlock/preview | Ensure lock/unlock, preview Chapter 1 flow, and cost usage stay correct | `gamification.py` (`COIN_COSTS`), `focus_blocker_qt.py` |
| Entitidex entity pool | Add 9 entities with complete metadata | `entitidex/entity_pools.py` (`ENTITY_POOLS`) |
| Entitidex perks | Add perk entries for all 9 entity IDs | `entitidex/entity_perks.py` (`ENTITY_PERKS`) |
| Encounter flavor | Add theme flavor routing/functionality | `entitidex/encounter_system.py` |
| Theme completion | Add completion card data | `entitidex/theme_completion.py` (`THEME_CELEBRATIONS`) |
| Celebration audio | Add synthesized composer mapping or explicit default policy | `entitidex/celebration_audio.py` (`_THEME_COMPOSERS`) |
| Entitidex main tab | Register theme tab metadata and optional exceptional colors | `entitidex_tab.py` (`THEME_INFO`, optional color map) |
| Encounter/collection dialogs | Theme list and totals must include the new story dynamically | `entity_encounter_dialog.py` |
| Aggregated stats | Theme/entity totals must derive from data, not constants | `gamification.py` (`get_entitidex_stats`) |
| Story label maps | Any user-facing story name map must include new story or be derived | `gamification.py` (saved encounter labels), UI label maps |
| Custom entity hooks | Audit all entity-ID-specific logic and either extend or intentionally document fallback behavior | `gamification.py`, `focus_blocker_qt.py`, `eye_protection_tab.py`, `weight_control_tips.py`, `entity_drop_dialog.py`, `entitidex_tab.py` |
| Dev/admin tooling | Update hardcoded story lists in debug and preview tools | `focus_blocker_qt.py`, `preview_entities.py`, `preview_character.py` |

## 5. Data Schema Contract

Required runtime schemas:

### 5.1 `AVAILABLE_STORIES[story_id]`

Required fields:

- `id` (must equal key)
- `title`
- `description`
- `theme` (taxonomy tag)

### 5.2 `STORY_GEAR_THEMES[story_id]`

Required fields:

- `theme_id` (must equal `story_id`)
- `theme_name`
- `slot_display` for all 8 canonical slots
- `item_types` for all 8 canonical slots (non-empty lists)
- `adjectives` for `Common`, `Uncommon`, `Rare`, `Epic`, `Legendary`
- `suffixes` for `Common`, `Uncommon`, `Rare`, `Epic`, `Legendary`

Recommended field:

- `set_themes` (for set-bonus theming)

### 5.3 `STORY_DATA[story_id]`

Required:

- `decisions`: 3 decision points keyed to chapter milestones (project standard: chapters 2, 4, 6)
- `chapters`: 7 chapters (project standard)

Decision entry requires:

- `id`
- `prompt`
- `choices` with `A` and `B`, each containing `label`, `short`, `description`

Chapter entry requires:

- `title`
- `threshold`
- `has_decision`
- `content`

Conditional chapter fields:

- `decision_id` when `has_decision = True`
- `content_variations` for branch-dependent narrative

### 5.4 `ENTITY_POOLS[story_id]`

Exactly 9 entities with IDs `<story_id>_001..009`.

Per entity required:

- `id`, `name`, `power`, `rarity`, `lore`
- `exceptional_name`, `exceptional_lore`
- `unlock_hint`
- `synergy_tags`

### 5.5 `ENTITY_PERKS`

For each new entity ID:

- At least one `EntityPerk` entry
- Correct normal/exceptional values
- Human-readable descriptions for both variants (where applicable)

### 5.6 Custom Entity Hooks (Required Audit)

Beyond generic pool/perk data, the codebase contains behavior keyed to exact `entity_id` values.

Hook categories that must be audited when adding themes/entities:

1. Feature gates keyed by entity ID (unlocking special UI/actions).
2. Special dialogs/tips keyed by entity ID.
3. Narrative/text variants keyed by entity ID.
4. Saved-encounter/recalculation rules keyed by entity ID.
5. Visual overrides keyed by entity ID (exceptional color maps, icon overrides).
6. Cross-system utility logic keyed by entity ID (health/weight/sleep helpers, translators, etc.).

Contract:

1. Any hardcoded entity-ID hook must be intentional and documented in change notes.
2. New entities that should participate in a hook category must be explicitly wired.
3. If a new entity should not participate, fallback behavior must be verified and documented.
4. No hidden one-off behavior should exist without discoverable references (constants/registry/comments).

## 6. Asset Contract

### 6.1 Entity SVGs

Required directories:

- `icons/entities/`
- `icons/entities/exceptional/`

Canonical naming:

- Normal: `icons/entities/<entity_id>_<entity_name_snake>.svg`
- Exceptional: `icons/entities/exceptional/<entity_id>_<entity_name_snake>_exceptional.svg`

Notes:

- Resolver has fallbacks, but canonical naming is required to keep asset lookup deterministic.
- Optional `icon_path` override is allowed but should be used intentionally.

### 6.2 Theme Completion Visuals/Audio

If dedicated assets are provided:

- Celebration visual in `icons/celebrations/`
- Completion metadata must reference it in `entitidex/theme_completion.py`

Audio policy:

- Either provide a theme composer in `_THEME_COMPOSERS` or explicitly rely on default synthesis.
- Missing dedicated waveform assets must not break celebration playback.

## 7. Persistence, Migration, and Backward Compatibility

Required:

1. `ensure_hero_structure()` must continue to produce valid hero data for the active story.
2. Legacy flat keys and hero-per-story sync must remain coherent after story additions.
3. Story switching must not lose inventory, equipped items, decisions, diary, or max power per story.
4. Backward-compat keys (`selected_story`) must not diverge from canonical state in active story mode.

## 8. Unlock and Mode Contract

Required checks for each new story:

1. Lock/unlock state works with `unlocked_stories`.
2. Preview behavior is coherent (Chapter 1 access when locked, if preview is enabled).
3. Story unlock cost path uses centralized coin costs (`story_unlock`).
4. Behavior is correct in all modes: `story`, `hero_only`, `disabled`.

## 9. Scalability Rules (Anti-Regression)

Must remain dynamic:

1. Theme lists for tabs/dialogs/collection views.
2. Story selectors in user-facing UI.
3. Total entity counts and completion percentages.
4. Story iteration in tests and aggregate stats.
5. Story display names used in secondary views (or derive them from canonical registry).
6. Entity-specific hook coverage must be reviewed whenever entity pools change.

Must not be hardcoded:

- Exact number of stories.
- Exact total entities.
- Fixed per-theme arrays in runtime code.
- Invalid legacy key usage (`story_active`).

## 10. Required Validation

### 10.1 Automated

Run at minimum:

```powershell
pytest tests/test_gamification.py tests/test_entitidex.py tests/test_hero_management.py test_story_system.py test_story_logic.py
```

Required test assertions:

1. New story exists in all canonical registries.
2. Story structure matches project standard (7 chapters, 3 decisions).
3. Entitidex pool count is exactly 9 for new story.
4. Every new entity ID has perk coverage.
5. Totals/stats use dynamic counts, not fixed constants.
6. Story state uses canonical key path (`active_story`) in reward/state flows.
7. Custom entity-ID hooks do not regress (gating dialogs/perks/flows still resolve correctly).

Recommended static checks:

```powershell
rg -n "story_active" -g "*.py" -g "*.md"
rg -n "total_entities = 36|for story_id in \[\"warrior\", \"scholar\", \"wanderer\", \"underdog\"\]" -g "*.py"
rg -n "[a-z]+_[0-9]{3}" gamification.py focus_blocker_qt.py eye_protection_tab.py weight_control_tips.py entity_drop_dialog.py entitidex_tab.py
```

### 10.2 Manual UI

Verify:

1. Story appears in selector and can be activated.
2. Lock/unlock and preview flow behaves correctly.
3. Hero panel renders proper story identity.
4. Focus rewards generate story-themed gear.
5. Story chapters, branch decisions, and persistence work end-to-end.
6. Entitidex encounters for new story occur and can be captured.
7. New theme appears in Entitidex tab and collection dialogs.
8. Perks from captured entities apply in gameplay systems.
9. Theme completion celebration triggers correctly for full normal+exceptional completion.

## 11. Documentation and Release Hygiene

Must update:

1. `README.md` if user-facing story counts or story list changed.
2. Story/Entitidex docs that describe current story set.
3. `CHANGELOG.md` with the new story/theme addition and migration notes (if any).

## 12. Definition of Done

A new story/theme is Done only when:

1. All touchpoints in Section 4 are implemented.
2. Schema contract in Section 5 is satisfied.
3. Asset contract in Section 6 is satisfied or explicit fallback is documented.
4. Migration/unlock/mode contracts in Sections 7 and 8 pass.
5. Validation in Section 10 passes.
6. Documentation hygiene in Section 11 is complete.

## 13. Governance

When architecture changes affect story expansion:

1. Update this spec in the same change set.
2. Keep this spec free of line-number references.
3. Prefer invariant rules and schema contracts over one-off procedural steps.
