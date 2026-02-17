# Hero ADHD SVG Performance Scrutinity Report

## Scope
- Requested scope: review only, no code changes.
- Reviewed rendering stack in `focus_blocker_qt.py` and `hero_svg_system.py`.
- Audited all SVG assets under `icons/heroes`.
- This report is based on static/code+asset analysis. No live GPU/CPU profiler capture was run in this pass.

## Executive Summary
The Hero tab has a real high-risk graphics bottleneck and integrity problem cluster:
1. Advanced celestial/thief effects rely on SVG filter animation patterns that are either invalid in some files or engine-fragile.
2. The active asset budget is too heavy for smooth UI on many machines (high simultaneous SMIL count + heavy blur + turbulence/displacement filters).
3. The fallback renderer path is expensive per frame and can explain jitter if WebEngine is unavailable or fails.
4. Current system lacks runtime observability and corpus-level SVG validation gates, so regressions enter easily.

## Integrated Addendum (From `PERFORMANCE_SCRUTINY.md`, Verified)
The additional report is helpful and materially accurate for current local code state.

### Verified code-level mitigations now present in workspace
- HTML reload guard is implemented: `_last_loaded_html` is tracked and identical HTML skips `setHtml(...)` (`focus_blocker_qt.py:18773`, `focus_blocker_qt.py:18839-18841`).
- State signature now keys on visual state (`story_theme`, `tier`, equipment signature) and no longer includes raw integer power (`focus_blocker_qt.py:19001-19005`).
- Aspect-ratio `setFixedHeight(...)` logic in `resizeEvent` is disabled to avoid recursive layout feedback with splitter/scroll area (`focus_blocker_qt.py:19212-19217`).
- `HAS_WEBENGINE=True` is valid in this environment (verified during this review session).

### Net impact on earlier diagnosis
- The additional report’s "layout thrash + repeated WebEngine reload" explanation is a strong root-cause match for the tab jitter symptom.
- Those specific causes appear mitigated by current local edits in `focus_blocker_qt.py`.
- Remaining unresolved risk is still asset integrity and SVG effect complexity (especially celestial/thief filter stacks), which can continue to cause missing/fragile effects even after UI jitter is improved.

## Integrated Addendum (From `claude_performance_scrutinity.md`, Verified With Corrections)
The Claude report is helpful and aligns with key architecture risks. Several counts/wording needed correction after direct verification.

### High-value findings confirmed
- WebEngine hero composition uses `<img>` layers (`hero_svg_system.py:975`), so host-page JS cannot directly control SMIL timelines inside each SVG document.
- Current pause JS targets CSS `animationPlayState` (`focus_blocker_qt.py:18916-18922`), while the SVG corpus is SMIL-driven; effective pause/resume relies mainly on page lifecycle (`Active/Frozen`).
- `MiniHeroWidget` builds a temporary full `CharacterCanvas` and renders offscreen for a 70x90 thumbnail (`focus_blocker_qt.py:31370-31402`), which is non-trivial overhead under frequent updates.
- `ADHDBusterTab._on_power_changed()` checks `self.char_widget`, but Hero tab creates `self.char_canvas` (`focus_blocker_qt.py:26527`, `focus_blocker_qt.py:26788`), so this branch is effectively dead.
- Inventory uses eager `QTableWidget` population (`setRowCount(len(indexed))`) in Hero tab (`focus_blocker_qt.py:28035`), with no custom virtualization strategy.

### Quantitative corrections (verified locally)
- Total hero SVG files: `468` (confirmed).
- Total SVG bytes: `1,042,890` bytes (~1.0 MB).
- Animation tags: `895` total (`608` `<animate>`, `287` `<animateTransform>`).
- Indefinite animations: `893`.
- Filter definitions: `131`.
- Filter primitives: `feGaussianBlur=103`, `feTurbulence=11`, `feDisplacementMap=9`.
- Gradients: `linearGradient=393`, `radialGradient=102`.
- Total gradients: `495` (not 990)
- Duration buckets: `dur<=0.2s: 29`, `dur<=0.5s: 57`, `dur<=1.0s: 116`.

### Additional datapoints confirmed
- `icons/heroes/space_pirate/hero_base.svg` uses non-canonical `viewBox="0 0 600 900"` while almost all others are `180x220`.
- `icons/heroes/space_pirate/fx/tier_legendary.svg` contains a `dur="0.1s"` animation.
- Warrior/Wanderer/Scholar/Scientist gear packs are similar in shape, but not byte-identical across themes (0/48 files had identical content across all four themes).

### Corrective nuance on resource release claim
- Hidden-resource eviction is delayed by 15 seconds (`focus_blocker_qt.py:26679`), but animations are paused immediately on hide (`focus_blocker_qt.py:26677` and `CharacterCanvas.pause_animations()`), so the tab is not left fully animating for the full delay.

### Recommendation utility assessment
- The R1-R10 recommendation framework in `claude_performance_scrutinity.md` is directionally useful, especially R1-R3 (inline SVG composition, ID namespacing, SMIL-aware pause control) and R5-R6 (animation-frequency and reload/debounce pressure control).

## Rendering Architecture Findings

### 1) Dual renderer model (WebEngine vs QSvgRenderer)
- `focus_blocker_qt.py:82-90` gates `HAS_WEBENGINE` on import.
- `CharacterCanvas` creates a `QWebEngineView` when available (`focus_blocker_qt.py:18769-18775`).
- When WebEngine content is loaded, `paintEvent` returns early and no manual painting occurs (`focus_blocker_qt.py:19215-19220`).
- Fallback/secondary path uses `QSvgRenderer` layer rendering (`focus_blocker_qt.py:19278-19287`, `hero_svg_system.py:813-879`).

Impact:
- If WebEngine is missing/failing, only partial SVG animation support is expected (typically transforms/opacity work, advanced filter-driven effects often do not).
- This aligns with your symptom: some animations play (tails/particles/eyes), some do not (wobbly/filter-style effects).

### 2) Hero WebEngine composition uses external SVG images per layer
- HTML is generated by `generate_hero_composed_html` (`hero_svg_system.py:882-994`).
- Layers are emitted as `<img src="file://...svg">` (`hero_svg_system.py:975`).

Impact:
- This is lightweight to implement but less robust for advanced SVG filter animation behavior than inline SVG DOM composition.
- Effects that depend on complex animated filter primitives are more likely to be inconsistent.

### 3) Fallback renderer hot path is expensive when animation is active
- Repaint throttle is ~60 FPS (`focus_blocker_qt.py:19155-19157`).
- On each repaint, `render_hero_svg_character(...)` is called (`focus_blocker_qt.py:19281`).
- `render_hero_svg_character` re-loads manifest and rebuilds layer plan (`hero_svg_system.py:828-835`).
- `load_hero_manifest` reads/parses JSON each call (`hero_svg_system.py:494-514`) and is not cached.

Impact:
- If fallback mode is active while animated layers run, repeated file I/O + path resolution + paint composition can directly cause low FPS and UI jitter.

## Asset Corpus Audit (icons/heroes)

## Inventory size
- Total hero SVG files audited: `468`
- Theme manifests: `9`
- Total files in `icons/heroes`: `477`

### Global feature counts (468 SVG files)
- Animated files (SMIL/CSS): `177`
- Files using `<filter>`: `94`
- Files using `<feGaussianBlur>`: `74`
- Files using `<feTurbulence>`: `11`
- Files using `<feDisplacementMap>`: `9`

### Heaviest themes by total SVG payload
- `space_pirate`: 223,558 bytes, 2,157 nodes, 732 paths
- `thief`: 202,375 bytes, 1,935 nodes, 410 paths
- `underdog`: 164,537 bytes, 1,698 nodes, 349 paths

### High-cost "full hero load" snapshots (base + fx + 8 gear layers)
Legendary load:
- `space_pirate`: 100,544 bytes, 871 nodes, 45 animations, 6 filters
- `thief`: 48,798 bytes, 458 nodes, 85 animations, 12 filters
- `underdog`: 53,649 bytes, 524 nodes, 63 animations, 8 filters

Celestial load:
- `thief`: 48,914 bytes, 469 nodes, 71 animations, 20 filters, 8 turbulence + 8 displacement
- `space_pirate`: 74,295 bytes, 656 nodes, 13 animations, 4 filters
- `underdog`: 43,691 bytes, 429 nodes, 42 animations, 8 filters

Interpretation:
- Thief celestial is the highest-risk runtime composition for filter-heavy animation load.
- Space pirate is the highest raw geometry cost (especially base layer).

## Integrity Defects Identified

### 1) Invalid SMIL timing tuple in thief celestial shield
- File: `icons/heroes/thief/gear/shield/shield_celestial.svg:130`
- File: `icons/heroes/thief/gear/shield/shield_celestial.svg:140`
- Issue: `values` has 3 entries while `keyTimes` has 4 entries.

Why this matters:
- This can invalidate the animation, leaving geometry in initial collapsed state.
- This directly causes "effect does not show" behavior for those elements.

### 2) `animate` used for `attributeName="transform"` in multiple files
Examples:
- `icons/heroes/thief/fx/tier_celestial.svg:53`
- `icons/heroes/thief/fx/tier_celestial.svg:57`
- Also present in several robot epic gear files.

Why this matters:
- This pattern is engine-fragile vs `animateTransform` and may be ignored.
- Missing motion symptoms are expected when engines reject these animations.

### 3) Wobbly celestial effect depends on animated turbulence/displacement stack
Examples:
- `icons/heroes/thief/gear/weapon/weapon_celestial.svg:11-21`
- `icons/heroes/thief/gear/shield/shield_celestial.svg:29-39`
- `icons/heroes/thief/gear/helmet/helmet_celestial.svg:36-40`

Observed pattern:
- `feTurbulence` + animated `seed` + `feDisplacementMap` + blur merge.

Why this matters:
- This is one of the most compatibility-sensitive and expensive SVG effect pipelines.
- If the engine ignores or partially supports animated turbulence parameters, wobble appears static or absent.

### 4) Very aggressive micro-loop durations in some assets
Examples include durations `0.08s`, `0.1s`, `0.15s`.

Why this matters:
- High-frequency loops create excessive repaint pressure and can starve main-thread UI responsiveness.

### 5) Heavy blur hotspots
Notable max blur values:
- `icons/heroes/thief/gear/helmet/helmet_celestial.svg` -> stdDeviation `14`
- `icons/heroes/thief/fx/tier_legendary.svg` -> stdDeviation `8`

Why this matters:
- Large blur kernels are expensive and scale badly when multiple animated layers run simultaneously.

## Why Your Specific Symptoms Make Sense

### "Wobbly celestial effect does not play"
Likely causes (ranked):
1. Filter-animation compatibility gap for turbulence/displacement stack.
2. Engine handling differences for external SVG loaded via `<img>` layer composition.
3. Invalid animation tuples in specific files (where present).

### "Lightning in thief FX does not show"
Likely causes (ranked):
1. Fragile transform animation declarations in thief FX celestial file (`animate` on transform).
2. Invalid animation declarations in related thief celestial assets causing expected moving elements to remain collapsed.
3. Low-opacity/blurred FX authored as background layer can be visually lost behind busy foreground composition.

### "Hero tab FPS is low; dropdowns jitter"
Likely causes (ranked):
1. High concurrent animated filter load (especially thief celestial compositions).
2. Transparent WebEngine composition cost in a UI with many active widgets.
3. Repeated layout/reload churn in `CharacterCanvas` was a major trigger and is now mitigated by local code changes (`focus_blocker_qt.py`).
4. If fallback mode activates, per-frame manifest/layer resolution overhead compounds repaint cost.

## System Integrity Gaps
- No runtime indicator in Hero UI/log surface proving whether WebEngine path or fallback path is active.
- No automated corpus validator for SMIL correctness (e.g., `keyTimes`/`values` cardinality, transform animation legality).
- No enforced performance budget for hero assets (animation count, blur caps, turbulence count per load).
- Tests mainly cover logic/lifecycle; they do not validate actual production asset quality/performance constraints.

## Industry-Standard Targets (Suggested Baselines)
For a smooth 60 FPS interactive tab:
- Frame budget: <=16.6 ms average, <=25 ms p95 while idle in Hero tab.
- Active animated elements in composed hero view: target <=30 (current thief legendary/celestial exceeds this).
- Full-canvas animated Gaussian blur layers: target <=1 simultaneously.
- Avoid animated turbulence/displacement in multiple simultaneous gear layers.
- Eliminate invalid SMIL declarations from corpus (0 tolerance).

## Priority Risk Ranking
1. High: SVG integrity defects in live assets (invalid SMIL tuples and transform animation patterns).
2. High: Filter-heavy celestial/thief compositions exceed stable interactive budget.
3. Medium: Fallback renderer hot path can be expensive under animation load.
4. Medium: Observability gaps make regressions hard to detect before release.
5. Medium (regression risk): Reintroducing resize-loop or unconditional `setHtml(...)` behavior would likely bring jitter back.

## Solution Architecture (Target State)
1. Rendering model:
- Replace layer `<img>` composition with inline per-layer SVG DOM composition in WebEngine.
- Keep layer isolation by namespacing every inlined SVG id/reference (`id`, `url(#id)`, `href="#id"`).
- Maintain current QSvgRenderer path only as fallback/static mode, not as primary animation path.
2. Animation lifecycle model:
- Use SMIL-native controls for pause/resume (`pauseAnimations()`/`unpauseAnimations()`) on inline `<svg>` roots.
- Keep `QWebEnginePage.LifecycleState` control as a second safety layer.
- Retain CSS pause handling only for CSS animations when present.
3. Asset integrity pipeline:
- Add an SVG lint gate that fails CI for invalid SMIL tuples (`values` vs `keyTimes`), unsupported transform animation patterns, and malformed filter chains.
- Enforce performance budgets per composed hero state (animation count, heavy blur count, turbulence/displacement count).
4. Performance governance:
- Introduce a runtime budget manager that can downgrade low-priority effects when budget is exceeded.
- Cache composed HTML by visual signature + asset mtimes to eliminate redundant page reloads.
5. UI responsiveness:
- Debounce equipment-change reload triggers.
- Fix dead update branches and minimize expensive thumbnail re-render paths.
- Move inventory rendering to a virtualized model/view path for large datasets.

## Implementation Plan (Phased)
1. Phase 0: Baseline instrumentation (1-2 days)
- Add frame-time and tab-latency telemetry around Hero tab interactions.
- Capture baseline metrics for thief celestial and space_pirate legendary loadouts.
- Deliverable: reproducible before/after benchmark script and baseline table.
2. Phase 1: Correctness hotfixes (1-2 days)
- Fix known invalid SMIL in `icons/heroes/thief/gear/shield/shield_celestial.svg`.
- Normalize `animate attributeName=\"transform\"` usages to `animateTransform` where required.
- Add corpus lint script and run it in CI/pre-merge checks.
3. Phase 2: Renderer modernization (4-6 days)
- Implement inline SVG composition function in `hero_svg_system.py`.
- Implement deterministic id namespacing and reference rewriting.
- Add SMIL control hooks callable from `CharacterCanvas`.
- Feature-flag rollout so old and new renderer paths can be switched at runtime.
4. Phase 3: Budget enforcement and graceful degradation (2-4 days)
- Define hard limits for active effects.
- Add downgrade rules by rarity/slot priority when limits are exceeded.
- Prefer preserving core silhouette/readability over high-cost glow/noise effects.
5. Phase 4: Interaction-path performance (2-3 days)
- Add debounce for equipment-change driven recomposition.
- Replace `MiniHeroWidget` full-pipeline thumbnail rendering with cached lightweight render path.
- Replace eager Hero inventory table behavior with a virtualized model-backed table.
6. Phase 5: Verification and rollout (2-3 days)
- Add regression tests for animation lifecycle, renderer switching, and lint rules.
- Run performance acceptance suite on target hardware tiers.
- Roll out behind flag, then enable by default after metrics pass.

## Acceptance Criteria (Industry Standard)
1. Smoothness:
- Hero tab steady-state: >=58 FPS average, >=50 FPS p95 under worst-case supported loadout.
2. Interaction latency:
- Equipment dropdown open/select latency <=50 ms p95.
3. Animation correctness:
- Celestial wobble/lightning visibility reproducible without random disappearance across repeated tab switches.
- No animation resets when visual state signature is unchanged.
4. Resource discipline:
- Hidden/inactive Hero tab consumes near-idle animation cost immediately after pause.
5. CI quality gates:
- Zero SVG integrity violations in corpus lint.
- Zero budget violations in default shipping assets.

## Suggested Execution Order
1. Ship Phase 1 first (fast correctness wins).
2. Land Phase 2 behind feature flag.
3. Add Phase 3 budget guardrails before enabling by default.
4. Complete Phase 4 to remove residual UI jitter under large inventories.
5. Finalize Phase 5 and flip default path after metrics pass.

## Closing Assessment
The current hero graphics system is functionally advanced but not yet at industry-standard performance integrity. The integrated addenda identify important mitigations already present and confirm remaining blockers. The plan above provides a concrete path to eliminate current rendering failures and achieve stable, smooth, production-grade animation behavior.

## Implementation Status (2026-02-17)
Completed in current workspace:
1. Phase 0 implemented: telemetry + benchmark tooling (`hero_performance_telemetry.py`, `tools/benchmark_hero_rendering.py`, `artifacts/hero_perf_live_monitor.md`).
2. Phase 1 implemented: hero SVG lint gate + correctness fixes (invalid SMIL tuples and fragile transform animations corrected in thief celestial assets; lint script and tests added).
3. Phase 2 implemented: inline SVG DOM composition with deterministic ID namespacing and SMIL lifecycle controls.
4. Phase 3 implemented: runtime SVG budget manager with effect downgrades by layer priority; updated to preserve celestial gear wobble/noise/glow while degrading lower-priority FX first.
5. Phase 4 implemented: interaction-path optimization (debounced WebEngine HTML/scale updates, resize-settle animation throttling, virtualized inventory model/table path, stale char_widget branch removed).
6. Deep SVG integrity sweep implemented for app-wide entity assets with Qt parser warning fixes (remaining runtime scanner warnings reduced to zero for app assets; preview-only files excluded).

Validation status:
1. Targeted regression suite passes: `56 passed` (`tests/test_hero_svg_system.py`, `tests/test_svg_animation_lifecycle.py`, `tests/test_hero_svg_asset_lint.py`, `tests/test_inventory_table_model.py`, `tests/test_hero_performance_telemetry.py`, `tests/test_lottery_rarity_consistency.py`).
2. Deep scan clean for current tracked app assets: no `types are incorrect`, no empty image href, no filter-id paint-server misuse.

Still required for full sign-off:
1. Manual in-app acceptance capture against production hardware tiers for FPS and p95 interaction targets in this report.
2. Final go/no-go decision to tune default runtime budget thresholds after live telemetry review.

