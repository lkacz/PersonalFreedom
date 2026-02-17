# Performance Scrutiny Report: Hero ADHD Tab

## Issue Identification
User reported "jittery UI" and "missing animations" (turbulence) in the Hero ADHD Tab when using new Celestial items.

### Investigation Findings
1.  **Rendering Pipeline**: The application uses `QWebEngineView` for full SVG support (including `feTurbulence` animations), with a fallback to `QSvgRenderer`.
2.  **Jitter Cause 1 (Layout Thrash)**: The `CharacterCanvas.resizeEvent` forced a `setFixedHeight` call to maintain aspect ratio. This conflicted with the parent `QSplitter` and `QScrollArea`, causing an infinite layout/resize loop when dimensions were near scrollbar thresholds.
3.  **Jitter Cause 2 (Excessive Reloads)**: `CharacterCanvas.set_character_state` was called frequently (e.g., on any power change). This updated the `_state_signature` because `power` (int) was included.
    *   This triggered `_update_web_engine_content`.
    *   This called `web_view.setHtml(...)`.
    *   `setHtml` is an expensive async operation that reloads the entire frame.
    *   **Result**: The WebEngine view was constantly reloading.
4.  **Missing Animations Cause**:
    *   `feTurbulence` animations rely on time (`dur` attributes).
    *   When `setHtml` reloads the page, the SVG document is re-parsed and animations reset to `t=0`.
    *   If reloads happen frequently (e.g., due to layout jitter or power updates), the animation never progresses, appearing static or missing.
    *   `QSvgRenderer` fallback (which lacks `feTurbulence` support) might also be triggered if WebEngine crashes from load stress, but stabilization fixes this risk.

## Applied Fixes
1.  **Stabilized HTML Injection**:
    *   Added `_last_loaded_html` caching in `CharacterCanvas`.
    *   `_inject_scaled_html` now checks if content is identical before calling `setHtml`. This prevents reload-on-resize or reload-on-identical-update.

2.  **Optimized State Signature**:
    *   Removed `int(power)` from `_state_signature` in `set_character_state`.
    *   The visual appearance depends on `tier`, not raw power. `tier` changes much less frequently.
    *   This prevents unnecessary updates when power changes slightly (e.g. +1 coin/power) but tier remains "Legendary".

3.  **Removed Recursive Resize Logic**:
    *   Disabled `self.setFixedHeight(ideal_height)` in `resizeEvent`.
    *   WebEngine view handles content scaling internally via CSS/JS (`_update_web_view_scale`), so forcing the widget aspect ratio causing layout loops was unnecessary and harmful.

## Verification
*   Verified `HAS_WEBENGINE=True` in environment.
*   Verified `QWebEngineView` loads Celestial SVGs correctly in isolation.
*   The applied fixes ensure the WebEngine view is only reloaded when *actual visual content* (items, theme, tier) changes.

## Future Recommendations
*   If `QWebEngineView` remains heavy, consider caching the composed SVG as a static image (rasterize to PNG) for static states, and only enable WebEngine when interacting/animating. (Current implementation pauses animations when hidden/inactive, which is good).
