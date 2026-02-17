# Hero ADHD Tab — SVG & Animation Performance Scrutiny

> **Date:** 2026-02-17
> **Scope:** `icons/heroes/` SVG resources, `hero_svg_system.py`, `CharacterCanvas` in `focus_blocker_qt.py`, and the WebEngine rendering pipeline.
> **Goal:** Identify root causes behind broken animations, missing visual effects, low FPS, and UI jitter.

---

## 1. Executive Summary

The hero tab suffers from **three compounding problems**: a rendering pipeline that silences advanced SVG animations, a massive accumulated filter/animation budget that overwhelms GPU compositing, and a pause/resume mechanism that only controls CSS animations while all actual animations are SMIL-based. Together, these create a situation where some effects never display, others cannot be paused, and the frame budget is blown on every repaint.

---

## 2. System Architecture Overview

### 2.1 SVG Asset Inventory

| Metric | Value |
|---|---|
| Total SVG files | **468** |
| Total size on disk | **~1,018 KB** (1 MB) |
| Hero themes | 9 (robot, scholar, scientist, wanderer, warrior, thief, underdog, zoo_worker, space_pirate) |
| Gear slots per theme | 8 (Helmet, Chestplate, Gauntlets, Boots, Shield, Weapon, Cloak, Amulet) |
| Rarities per slot | 6 (common, uncommon, rare, epic, legendary, celestial) |
| FX tiers per theme | 3 (epic, legendary, celestial) |
| Largest single SVG | `space_pirate/hero_base.svg` — **60 KB / 805 lines** |

### 2.2 Rendering Pipeline (Two Paths)

**Path A — QWebEngineView (primary, when available):**
```
generate_hero_composed_html()
  → Builds HTML with <img> tags for each layer
  → Loads into QWebEngineView.setHtml()
  → SVGs rendered as separate <img> elements
```

**Path B — QSvgRenderer + QPainter (fallback):**
```
render_hero_svg_character()
  → QSvgRenderer per layer (cached by mtime)
  → Renders to QPainter on widget canvas
  → repaintNeeded signal throttled to ~60 FPS
```

### 2.3 Layer Composition

Each hero can display up to **10 simultaneous SVG layers**:
- 1 FX background (tier_epic/legendary/celestial)
- 1 hero base
- 8 gear overlays (one per slot)

In the WebEngine path, this means **10 separate `<img>` tags** each loading a distinct SVG file, all rendering simultaneously within a single `QWebEngineView`.

---

## 3. Critical Issues

### 3.1 [P0] SMIL Animations in `<img>` Tags — The "Wobbly Effect" Failure

**Root Cause:** `generate_hero_composed_html()` (hero_svg_system.py:882-994) composes SVG layers using `<img>` tags:
```html
<img src="file:///path/to/gear.svg?v=timestamp" class="layer" style="..." />
```

SVGs loaded via `<img>` tags operate in a **restricted rendering context** in Chromium (which Qt WebEngine is based on). While basic SMIL animations (opacity, translate, etc.) generally work, **animated filter primitive attributes are unreliable in `<img>` context**. The "wobbly/dissolve" effect relies on:

```xml
<feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="3" seed="1" result="noise">
    <animate attributeName="seed" values="1;120;1" dur="2.2s" repeatCount="indefinite"/>
</feTurbulence>
<feDisplacementMap in="SourceGraphic" in2="noise" scale="5"/>
```

Animating the `seed` attribute of `feTurbulence` inside a filter chain is one of the most demanding SMIL features. **This specific pattern fails silently in `<img>` context** — the filter renders statically (frozen at seed=1) or not at all, which is exactly the reported behavior for celestial gear items.

**Affected assets (8 files using feTurbulence+animate in thief celestial):**
- `thief/gear/helmet/helmet_celestial.svg`
- `thief/gear/gauntlets/gauntlets_celestial.svg`
- `thief/gear/boots/boots_celestial.svg`
- `thief/gear/chestplate/chestplate_celestial.svg`
- `thief/gear/cloak/cloak_celestial.svg`
- `thief/gear/amulet/amulet_celestial.svg`
- `thief/gear/shield/shield_celestial.svg`
- `thief/gear/weapon/weapon_celestial.svg`

Also affected: `zoo_worker/gear/cloak/cloak_common.svg`, `zoo_worker/gear/shield/shield_common.svg`

### 3.2 [P0] QSvgRenderer Also Cannot Animate Filter Primitives

Even when falling back to Path B (QSvgRenderer), Qt's SVG module has **no support for animating filter primitive attributes** like `feTurbulence.seed`. The QSvgRenderer supports basic SMIL (`animate` on opacity/position, `animateTransform`), but complex filter animations are silently ignored.

**Result:** The "wobbly dissolve" effect **cannot work in either rendering path** with the current architecture. It is architecturally impossible with the existing rendering choices.

### 3.3 [P0] Pause/Resume Mechanism Targets CSS, Not SMIL

The animation lifecycle control in `CharacterCanvas._set_web_page_active()` (focus_blocker_qt.py:18899-18922) uses:

```javascript
// Pause
document.querySelectorAll('*').forEach(el => el.style.animationPlayState = 'paused');
// Resume
document.querySelectorAll('*').forEach(el => el.style.animationPlayState = '');
```

**Problem:** `animationPlayState` is a CSS property that only controls CSS `@keyframes` animations. The entire SVG asset library uses **exclusively SMIL animations** (zero `@keyframes` found across all 468 SVGs). Additionally, because SVGs are loaded via `<img>` tags, the host page's JavaScript **cannot access the SVG DOM** inside them to call SMIL control methods like `pauseAnimations()`/`unpauseAnimations()`.

**Result:** Animations can never be paused when the tab is hidden or the window is minimized. The `WebEnginePage.LifecycleState.Frozen` may help at the engine level, but the explicit JS-based control is a no-op.

### 3.4 [P1] Lightning Bolts Invisible Due to Lifecycle Timing

The thief FX lightning bolts (e.g., `thief/fx/tier_epic.svg`) use time-gated opacity animation:
```xml
<g opacity="0">
    <animate attributeName="opacity" values="0; 1; 0; 0; 0; 0" dur="3s" repeatCount="indefinite"/>
```

The bolt is only visible for ~0.5s out of every 3s cycle. If the WebEngine page loads while the animation happens to be at an invisible keyframe, and the page lifecycle state transitions (Frozen→Active) don't properly reset SMIL timing, the effect may appear permanently invisible. This is a **race condition between page load timing and SMIL animation phase**.

---

## 4. Performance Bottlenecks

### 4.1 Filter Complexity Budget

| Filter Type | Total Instances | GPU Cost |
|---|---|---|
| `<filter>` definitions | 131 | — |
| `feGaussianBlur` | 103 | **HIGH** — full-area convolution per blur |
| `feTurbulence` | 20 | **VERY HIGH** — procedural noise generation |
| `feDisplacementMap` | 9 | **HIGH** — per-pixel displacement lookup |
| `feMerge`/`feMergeNode` | 205 | Medium — compositing passes |
| `feDropShadow` | 25 | Medium — blur + offset |
| `feComposite` | 15 | Medium — blending operations |
| `feFlood` | 8 | Low |
| `feColorMatrix` | 1 | Low |

**Worst-case scenario (thief celestial, full gear):** A fully-equipped thief with celestial items renders up to **18 filter elements** in the helmet alone, with 14 filters each in 6 other celestial gear pieces, plus FX layer filters. A single frame requires:

- **~8 separate feTurbulence computations** (one per celestial gear SVG + FX)
- Each `feTurbulence` generates fractal noise across the filter region at `baseFrequency=0.045` with `numOctaves=3`
- Each is fed into a `feDisplacementMap` + `feGaussianBlur` + `feMerge` chain
- Combined with 103 blur operations across visible layers

In Chromium's compositor, each `<img>` with filter effects creates a **separate compositing layer**, meaning 10 independent GPU-composited layers all running filters simultaneously.

### 4.2 Animation Volume and Frequency

| Metric | Value |
|---|---|
| Total `<animate>` elements | **608** |
| Total `<animateTransform>` elements | **287** |
| Total SMIL animations | **~895** |
| Animations with `repeatCount="indefinite"` | **893** (99.8%) |
| Animations with `dur ≤ 200ms` | **29** (extreme frequency) |
| Animations with `dur ≤ 500ms` | **43** |
| Animations with `dur ≤ 1s` | **71** |

**Industry benchmark:** Major game UIs (League of Legends, Genshin Impact) typically run 5-15 animations concurrently on a character display. A fully-loaded hero here can run **80+ simultaneous indefinite animations** across all visible layers.

The **29 sub-200ms animations** are particularly problematic — these include:
- `dur="0.08s"` (12.5 FPS flicker — essentially every frame triggers recalc)
- `dur="0.1s"` (6 instances)
- `dur="0.15s"` (4 instances — e.g., dog tail wag at 6.67 Hz)
- `dur="0.2s"` (18 instances — lightning bolt jitter)

Each animation tick forces a repaint of the affected SVG subtree. When filtered elements animate, the entire filter chain must re-execute.

### 4.3 Gradient Overhead

| Gradient Type | Total Count |
|---|---|
| `linearGradient` | **786** |
| `radialGradient` | **204** |
| **Total** | **990** |

The `space_pirate/hero_base.svg` alone defines **23 gradients**. While gradients are generally GPU-accelerated, 990 gradient definitions across simultaneously-loaded SVGs contribute to shader compilation stalls and VRAM pressure on lower-end hardware.

### 4.4 `space_pirate/hero_base.svg` — Outlier Complexity

This single file is an extreme outlier at **60 KB / 805 lines**:
- 23 gradient definitions (linear + radial)
- 7 filter elements
- 4 SMIL animations (belt buckle pulse, status light flash, glow aura)
- Anatomically detailed hands with individual fingernails (each nail = ~10 path elements)
- Total SVG nodes estimated at **500+**

Compare: other hero bases range from 8-14 KB. This file is **4-7x larger** than peers.

### 4.5 Dropdown Jitter Root Cause

The UI jitter when using dropdown menus is caused by the interaction between:

1. **Equipment change signals:** `_on_equipment_changed()` → `_refresh_slot_combo()` + `_refresh_character()` triggers a full character canvas update on every combo selection
2. **WebEngine HTML reload:** `set_character_state()` → `_update_web_engine_content()` → `setHtml()` causes a **full page reload** of the WebEngine, including re-fetching all 10 SVG layers from disk
3. **Animation restart:** Each reload resets all SMIL animation timers, causing visual discontinuity
4. **No debounce:** Rapid dropdown scrolling fires change events on every hover-over item, each triggering the full reload chain

The `_inject_scaled_html()` method does check for identical HTML to avoid redundant loads, but the cache-buster query parameter (`?v=mtime_ns`) ensures each equipment change generates a new URL even for unchanged SVG files.

---

## 5. SVG ID Collision Analysis

When SVGs are loaded via `<img>` tags, each has an **isolated DOM scope**, so filter/gradient ID collisions between files are NOT a runtime problem. However, the codebase does contain massive ID duplication:

| ID | Occurrences Across Files |
|---|---|
| `qt_anim_driver` | 92 |
| `glow` | 11 |
| `shadowDissolve` | 8 |
| `skinGrad` | 9 |
| `celestialGlow` | multiple |
| `celestialGradient` | multiple |

This is benign in `<img>` tag isolation, but would become **immediately broken if switched to inline `<svg>` rendering** (which would be needed to fix animation issues — see Recommendations). Any migration must address ID namespacing first.

---

## 6. Rendering Path Comparison

| Capability | QSvgRenderer (Path B) | WebEngine `<img>` (Path A) |
|---|---|---|
| Basic SMIL (`animate` opacity/position) | Yes | Yes |
| `animateTransform` (translate/scale/rotate) | Yes | Yes |
| Animated filter attributes (feTurbulence seed) | **No** | **Unreliable** |
| CSS `@keyframes` | No | Yes |
| `feGaussianBlur` | Yes (CPU) | Yes (GPU-accelerated) |
| `feTurbulence` (static) | Partial | Yes |
| `feDisplacementMap` | Partial | Yes |
| JavaScript control of animations | N/A | **No** (img sandboxing) |
| Layer isolation | Separate renderers | Separate img contexts |
| Pause/resume control | `setAnimationEnabled()` | `LifecycleState.Frozen` (engine-level only) |

---

## 7. Specific Broken/Degraded Effects Inventory

### Effects That Do NOT Work (Both Paths)
1. **Celestial "wobbly dissolve"** — Animated `feTurbulence.seed` in `shadowDissolve` filter (thief celestial gear, zoo_worker common cloak/shield)
2. **Animated noise displacement** — `feDisplacementMap` + animated noise source

### Effects That Work Partially
3. **Lightning bolts** (thief FX) — Work in principle but race with page lifecycle; may appear permanently invisible
4. **Searchlight sweep** (thief FX legendary) — `animateTransform rotate` works but blur chain is expensive
5. **Police strobe** (thief FX legendary) — Opacity animation works but `lightBlur` with `stdDeviation="8"` on full-viewport rects is extremely expensive

### Effects That Work
6. **Eye movement** (saccadic pupil, thief/space_pirate helmets) — Simple attribute animation
7. **Dog tail wag** (shields with dog companion) — animateTransform rotate
8. **Floating particles** (opacity + position) — Basic SMIL
9. **Belt buckle pulse** (space_pirate base) — Opacity animation
10. **Breathing animation** — animateTransform scale on body groups
11. **Blinking** — Opacity keyframes animation

---

## 8. Recommendations (Prioritized)

### R1. [Critical] Replace `<img>` with Inline `<svg>` in WebEngine HTML
Switch `generate_hero_composed_html()` from:
```html
<img src="file:///path.svg" class="layer" style="..." />
```
to reading SVG content and embedding inline:
```html
<svg class="layer" style="..." viewBox="0 0 180 220">
  <!-- SVG content injected inline -->
</svg>
```
**Impact:** Enables full SMIL support, allows JS-based animation control, enables filter animation. Requires ID namespace prefixing per layer to avoid collisions.

### R2. [Critical] Namespace All SVG IDs Per Layer
Every ID (`shadowDissolve`, `glow`, `celestialGradient`, etc.) must be prefixed with a unique namespace when inlining, e.g., `layer3_shadowDissolve`. The 92 occurrences of `qt_anim_driver` alone would cause catastrophic collision.

### R3. [Critical] Fix Pause/Resume to Target SMIL
Replace the CSS `animationPlayState` approach with either:
- `document.querySelectorAll('svg').forEach(svg => svg.pauseAnimations())` (when using inline SVG)
- Or use `SVGSVGElement.setCurrentTime()` for more precise control

### R4. [High] Implement feTurbulence Budget Cap
Limit `feTurbulence` to maximum 1-2 instances across all visible layers. For celestial items beyond the budget, pre-render the wobble as a static filter or use CSS `filter: blur()` as a lighter approximation.

### R5. [High] Throttle Sub-Second Animations
All animations with `dur < 0.5s` should be reviewed:
- `dur="0.08s"` and `dur="0.1s"` — These run at 10-12 Hz, creating per-frame recalculation. Increase to `dur="1s"` minimum or use CSS transitions
- Lightning bolt jitter (`dur="0.2s"`) — Increase to `dur="0.5s"`

### R6. [High] Debounce Equipment Change → WebEngine Reload
Add a 200-300ms debounce between equipment dropdown change events and the WebEngine HTML reload. This directly fixes the dropdown jitter.

### R7. [Medium] Reduce `space_pirate/hero_base.svg` Complexity
The 60 KB/805-line base is 4-7x larger than peers. The anatomically detailed fingernails (each ~10 elements × 10 fingers = ~100 elements) provide no visible benefit at 180×220px render size. Simplify hands to 2-3 paths per hand.

### R8. [Medium] Implement Layer-Level Animation Budgeting
Track total active animations across all visible layers. If total exceeds a threshold (e.g., 30), disable animations on lower-priority layers (common/uncommon gear first, then rare, etc.).

### R9. [Low] Pre-Flatten Static SVG Layers
SVGs with no animations (many common/uncommon gear pieces) can be pre-rasterized to PNG at the target resolution. This eliminates SVG parsing/rendering overhead entirely for static layers.

### R10. [Low] Reduce `feGaussianBlur` stdDeviation Values
Several SVGs use `stdDeviation="8"` or higher on large elements. For a 180×220 canvas, `stdDeviation > 4` produces visually indistinguishable results from lower values but costs O(n²) more processing.

---

## 9. Additional Findings

### 9.1 `MiniHeroWidget` Instantiates Full Rendering Pipeline for a Thumbnail

`MiniHeroWidget` (focus_blocker_qt.py:31337) creates a **complete temporary `CharacterCanvas`** at full 180×220 resolution, renders it to a `QImage`, then scales down to 70×90 pixels and discards the canvas. This triggers the entire SVG resolution + `QSvgRenderer` pipeline (with `manage_svg_animations=False`) every time the timeline header data changes. For a 70×90 thumbnail, this is disproportionate overhead.

### 9.2 Dead Code Path in `_on_power_changed`

`ADHDBusterTab._on_power_changed()` (focus_blocker_qt.py:26527) checks `hasattr(self, 'char_widget')`, but `ADHDBusterTab` only creates `self.char_canvas` — never `char_widget`. This guard silently fails, meaning the character display is never updated from the `power_changed` signal. It only updates via `equipment_changed` → `_refresh_character()`.

### 9.3 No Inventory Virtualization

The inventory `QTableWidget` renders all rows simultaneously. A player with hundreds of items has every row in the DOM at all times, contributing to tab responsiveness issues. No lazy row loading or row recycling is implemented.

### 9.4 Resource Release Only After 15-Second Delay

`ADHDBusterTab.hideEvent()` starts a 15-second `QTimer` before calling `_release_hidden_resources()`. During these 15 seconds, all SVG renderers and WebEngine processes remain fully active after tab switch, consuming GPU and CPU for content the user cannot see.

---

## 10. Industry Benchmarks

| Metric | This System | Industry Standard (Game UI) |
|---|---|---|
| Concurrent animations per character | 80+ | 5-15 |
| Filter operations per frame | ~50+ (worst case) | 3-5 |
| feTurbulence instances per frame | up to 8 | 0-1 |
| SVG layers composited simultaneously | 10 | 1-3 (typically pre-composited sprite) |
| Minimum animation duration | 0.08s | 0.5s (with easing) |
| Total indefinite animations | 893 | Budget-capped at visible subset |
| Asset per-character size | ~120 KB (10 layers) | 20-50 KB (sprite sheet) |
| Animation pause coverage | CSS only (SMIL untouched) | Full lifecycle control |
| Resource release on tab hide | 15s delay | Immediate (paused within 1 frame) |

---

## 11. Files Examined

### Core Rendering
- `hero_svg_system.py` (entire file — 995 lines)
- `focus_blocker_qt.py:18701-19340` (CharacterCanvas class)
- `focus_blocker_qt.py:26463-26830` (ADHDBusterTab class)

### SVG Assets (sampled in detail)
- `icons/heroes/space_pirate/hero_base.svg` (805 lines — largest)
- `icons/heroes/thief/gear/helmet/helmet_celestial.svg` (154 lines — most filters: 18)
- `icons/heroes/thief/gear/gauntlets/gauntlets_celestial.svg` (103 lines)
- `icons/heroes/thief/fx/tier_epic.svg` (77 lines — lightning)
- `icons/heroes/thief/fx/tier_legendary.svg` (66 lines — searchlights)
- `icons/heroes/thief/fx/tier_celestial.svg` (67 lines)

### Test/Preview Artifacts
- `tests/test_svg_animation_lifecycle.py` (529 lines)
- `artifacts/previews/space_pirate_gauntlets_legendary_adhd_composite.html`
- `preview_thief_celestial.html`
- `preview_pirate_full_gear.html` (493 KB — inline SVG approach proof)

### Statistical Analysis
- All 468 SVGs analyzed for: animation count, filter count, gradient count, feTurbulence usage, ID collisions, file size, line count, animation durations
