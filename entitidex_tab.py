"""
Entitidex Tab - Collection viewer for entity companions.

Shows all entities in the current story theme with:
- Full details for collected entities
- Silhouettes for uncollected entities (mysterious appearance)
"""

import os
import math
import logging
from pathlib import Path
from typing import Optional
from collections import OrderedDict

# Industry standard: Use logging module instead of print() for diagnostics
_logger = logging.getLogger(__name__)

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtSvg import QSvgRenderer

# Try to import QWebEngineView for animated SVG support
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    _logger.info("QWebEngineView not available - SVG animations disabled")

# Import entitidex components
from entitidex import (
    get_entities_for_story,
    Entity,
    EntitidexProgress,
)


# Rarity colors
RARITY_COLORS = {
    "common": "#9E9E9E",
    "uncommon": "#4CAF50",
    "rare": "#2196F3",
    "epic": "#9C27B0",
    "legendary": "#FF9800",
}

# Rarity background colors (matching preview_entities.py)
RARITY_BG = {
    "common": "#2D2D2D",
    "uncommon": "#1B3D1B",
    "rare": "#1B2D3D",
    "epic": "#2D1B3D",
    "legendary": "#3D2D1B",
}

# Path to entity SVGs
ENTITY_ICONS_PATH = Path(__file__).parent / "icons" / "entities"
EXCEPTIONAL_ICONS_PATH = ENTITY_ICONS_PATH / "exceptional"

# =============================================================================
# EXCEPTIONAL/SHINY ENTITY COLORS
# Predefined contrasting colors for each entity when it's exceptional
# Format: {entity_id: (R, G, B)} - complementary/contrasting to original
# =============================================================================
EXCEPTIONAL_ENTITY_COLORS = {
    # WARRIOR THEME - Fire/Red creatures get cool blue/teal versions
    "warrior_001": (0, 200, 200),      # Hatchling Drake: Red → Cyan/Teal
    "warrior_002": (100, 50, 150),     # Training Dummy: Brown → Purple
    "warrior_003": (255, 100, 200),    # Battle Falcon: Brown → Pink
    "warrior_004": (50, 200, 100),     # War Horse: Brown → Emerald Green
    "warrior_005": (0, 180, 255),      # Dragon Whelp Ember: Orange → Sky Blue
    "warrior_006": (200, 100, 255),    # Battle Standard: Red → Violet
    "warrior_007": (0, 255, 150),      # Battle Dragon Crimson: Red → Jade Green
    "warrior_008": (255, 200, 50),     # Dire Wolf Fenris: Gray → Golden Yellow
    "warrior_009": (255, 50, 50),      # Old War Ant: Black → Crimson Red
    
    # SCHOLAR THEME - Books/Paper get vibrant magical colors
    "scholar_001": (255, 150, 200),    # Library Mouse: White → Pink
    "scholar_002": (200, 50, 255),     # Study Owl: Brown → Purple
    "scholar_003": (50, 255, 200),     # Reading Candle: Orange → Turquoise
    "scholar_004": (150, 100, 255),    # Library Cat: Orange → Lavender
    "scholar_005": (255, 50, 100),     # Living Bookmark: Gold → Ruby Red
    "scholar_006": (50, 255, 100),     # Sentient Tome: Brown → Lime Green
    "scholar_007": (255, 100, 0),      # Ancient Star Map: Blue → Orange
    "scholar_008": (0, 200, 255),      # Archive Phoenix: Red/Orange → Cyan
    "scholar_009": (255, 215, 0),      # Blank Parchment: Yellow → Gold Shimmer
    
    # WANDERER THEME - Travel gear gets mystical colors
    "wanderer_001": (50, 255, 50),     # Lucky Coin: Copper → Green
    "wanderer_002": (255, 50, 150),    # Brass Compass: Gold → Magenta
    "wanderer_003": (100, 200, 255),   # Journey Journal: Brown → Sky Blue
    "wanderer_004": (255, 255, 100),   # Road Dog: Brown → Bright Yellow
    "wanderer_005": (200, 50, 255),    # Self-Drawing Map: Parchment → Purple
    "wanderer_006": (50, 255, 200),    # Wanderer's Carriage: Brown → Aqua
    "wanderer_007": (255, 100, 50),    # Timeworn Backpack: Brown → Sunset Orange
    "wanderer_008": (255, 50, 255),    # Sky Balloon: Rainbow → Magenta
    "wanderer_009": (0, 255, 200),     # Hobo Rat: Gray → Mint Green
    
    # UNDERDOG THEME - Office items get neon/cyber colors
    "underdog_001": (0, 255, 255),     # Office Rat: Gray → Cyan
    "underdog_002": (255, 100, 255),   # Lucky Sticky Note: Yellow → Magenta
    "underdog_003": (255, 200, 50),    # Vending Machine Coin: Silver → Gold
    "underdog_004": (100, 255, 100),   # Window Pigeon: Gray → Neon Green
    "underdog_005": (255, 50, 150),    # Desk Succulent: Green → Pink
    "underdog_006": (50, 200, 255),    # Coffee Maker: Black → Electric Blue
    "underdog_007": (255, 150, 50),    # Corner Office Chair: Black → Orange
    "underdog_008": (150, 255, 200),   # AGI Assistant: Blue → Mint
    "underdog_009": (255, 100, 100),   # Break Room Fridge: Beige → Salmon Pink
    
    # SCIENTIST THEME - Lab equipment gets bioluminescent colors
    "scientist_001": (200, 50, 255),   # Cracked Test Tube: Clear → Purple
    "scientist_002": (0, 255, 150),    # Old Bunsen Burner: Blue Flame → Green Flame
    "scientist_003": (255, 150, 50),   # Lucky Petri Dish: Clear → Amber
    "scientist_004": (255, 200, 255),  # Wise Lab Rat: Gray → Light Pink
    "scientist_005": (50, 255, 255),   # Vintage Microscope: Brass → Cyan
    "scientist_006": (255, 50, 200),   # Bubbling Flask: Multi → Hot Pink
    "scientist_007": (255, 200, 0),    # Tesla Coil: Purple → Gold Electric
    "scientist_008": (100, 255, 200),  # Golden DNA Helix: Gold → Aquamarine
    "scientist_009": (200, 150, 255),  # White Mouse: White → Lavender
}


def _resolve_entity_svg_path(entity: Entity, is_exceptional: bool = False) -> Optional[str]:
    """
    Resolve the SVG path for an entity using multiple strategies.
    
    SVG files are named: {id}_{name_snake_case}.svg
    e.g., warrior_003_battle_falcon_swift.svg
    
    Exceptional variants are in icons/entities/exceptional/ with _exceptional suffix.
    e.g., warrior_003_battle_falcon_swift_exceptional.svg
    
    Args:
        entity: The Entity to find SVG for
        is_exceptional: If True, look for exceptional variant first
    
    Returns:
        Path to SVG file or None if not found
    """
    name_snake = entity.name.lower().replace(" ", "_").replace("-", "_").replace("'", "")
    
    # If exceptional, try to find the exceptional variant first
    if is_exceptional and EXCEPTIONAL_ICONS_PATH.exists():
        # Strategy 1: Try filename pattern {id}_{name_snake_case}_exceptional.svg
        exceptional_path = EXCEPTIONAL_ICONS_PATH / f"{entity.id}_{name_snake}_exceptional.svg"
        if exceptional_path.exists():
            return str(exceptional_path)
        
        # Strategy 2: Search for file starting with entity id in exceptional folder
        for svg_file in EXCEPTIONAL_ICONS_PATH.glob(f"{entity.id}*_exceptional.svg"):
            return str(svg_file)
    
    # Fall back to regular SVG resolution
    # Strategy 1: Try entity's icon_path if provided
    if entity.icon_path and os.path.exists(entity.icon_path):
        return entity.icon_path
    
    # Strategy 2: Try filename pattern {id}_{name_snake_case}.svg
    pattern_path = ENTITY_ICONS_PATH / f"{entity.id}_{name_snake}.svg"
    if pattern_path.exists():
        return str(pattern_path)
    
    # Strategy 3: Search for file starting with entity id
    if ENTITY_ICONS_PATH.exists():
        for svg_file in ENTITY_ICONS_PATH.glob(f"{entity.id}*.svg"):
            return str(svg_file)
    
    # Strategy 4: Fall back to simple {id}.svg (legacy support)
    simple_path = ENTITY_ICONS_PATH / f"{entity.id}.svg"
    if simple_path.exists():
        return str(simple_path)
    
    return None


# =============================================================================
# SVG RENDERING CACHE (Industry Standard: LRU Pattern with Size Limits)
# Prevents redundant file I/O and SVG parsing for repeated entity loads
# Uses OrderedDict for LRU eviction - standard pattern for memory-bounded caches
#
# NOTE: These caches are NOT thread-safe. Qt GUI operations (including
# QSvgRenderer) must only be called from the main thread. This is standard
# Qt architecture - all widget/renderer operations are main-thread only.
# =============================================================================
_SVG_CACHE_MAX_SIZE = 100  # Max entries per cache (covers all 90 entities + buffer)

_svg_renderer_cache: OrderedDict[str, QSvgRenderer] = OrderedDict()
_silhouette_pixmap_cache: OrderedDict[str, QtGui.QPixmap] = OrderedDict()
_svg_content_cache: OrderedDict[str, str] = OrderedDict()


def _lru_cache_set(cache: OrderedDict, key: str, value, max_size: int = _SVG_CACHE_MAX_SIZE) -> None:
    """Add item to LRU cache, evicting oldest if at capacity.
    
    Industry best practice: Bounded caches prevent unbounded memory growth.
    """
    if key in cache:
        cache.move_to_end(key)  # Mark as recently used
    else:
        if len(cache) >= max_size:
            cache.popitem(last=False)  # Evict least recently used
        cache[key] = value


def _lru_cache_get(cache: OrderedDict, key: str):
    """Get item from LRU cache, marking as recently used."""
    if key in cache:
        cache.move_to_end(key)  # Mark as recently used
        return cache[key]
    return None


def clear_svg_caches() -> None:
    """Clear all SVG-related caches to free memory.
    
    Call this when switching story themes or when memory pressure is detected.
    Industry best practice: Provide explicit cache invalidation for long-running apps.
    """
    global _svg_renderer_cache, _silhouette_pixmap_cache, _svg_content_cache
    _svg_renderer_cache.clear()
    _silhouette_pixmap_cache.clear()
    _svg_content_cache.clear()


def get_svg_cache_stats() -> dict[str, int]:
    """Get current SVG cache statistics for monitoring/debugging.
    
    Industry best practice: Expose cache metrics for performance monitoring
    in long-running applications.
    
    Returns:
        Dictionary with cache sizes: {renderer_count, silhouette_count, content_count, max_size}
    """
    return {
        'renderer_count': len(_svg_renderer_cache),
        'silhouette_count': len(_silhouette_pixmap_cache),
        'content_count': len(_svg_content_cache),
        'max_size': _SVG_CACHE_MAX_SIZE,
    }


def _get_cached_renderer(svg_path: str) -> Optional[QSvgRenderer]:
    """Get a cached QSvgRenderer for the given SVG path.
    
    Industry best practice: Reuse renderers instead of creating new ones
    for each widget, reducing file I/O and memory overhead.
    Uses LRU eviction to bound memory usage.
    
    Returns None if the SVG file is invalid (industry standard: validate resources).
    """
    # Industry standard: Validate path before attempting to load
    if not svg_path or not os.path.isfile(svg_path):
        _logger.warning("SVG file does not exist: %s", svg_path)
        return None
        
    renderer = _lru_cache_get(_svg_renderer_cache, svg_path)
    if renderer is None:
        renderer = QSvgRenderer(svg_path)
        # Industry standard: Validate SVG before caching
        if not renderer.isValid():
            _logger.warning("Invalid SVG file: %s", svg_path)
            return None
        _lru_cache_set(_svg_renderer_cache, svg_path, renderer)
    return renderer


def _get_cached_silhouette(svg_path: str, size: tuple[int, int] = (128, 128)) -> Optional[QtGui.QPixmap]:
    """Get a cached silhouette pixmap for the given SVG.
    
    Industry best practice: Pre-render expensive pixel operations once
    and cache the result, instead of processing on every paintEvent.
    Uses LRU eviction to bound memory usage.
    
    OPTIMIZATION: Uses QPainter composition modes instead of per-pixel Python
    loops for ~100x faster silhouette generation (industry standard).
    
    Args:
        svg_path: Path to the SVG file
        size: Target size as (width, height). Must be positive integers.
    """
    # Industry standard: Validate input parameters
    if size[0] <= 0 or size[1] <= 0:
        _logger.warning("Invalid silhouette size: %s", size)
        return None
        
    cache_key = f"{svg_path}_{size[0]}x{size[1]}"
    
    cached = _lru_cache_get(_silhouette_pixmap_cache, cache_key)
    if cached is not None:
        return cached
    
    renderer = _get_cached_renderer(svg_path)
    if renderer is None:
        return None
    
    # Industry standard: Account for HiDPI displays
    # Get device pixel ratio from primary screen (fallback to 1.0)
    # Handle cases where QApplication or primaryScreen() may be None
    dpr = 1.0
    try:
        app = QtWidgets.QApplication.instance()
        if app is not None:
            screen = app.primaryScreen()
            if screen is not None:
                dpr = screen.devicePixelRatio()
    except Exception:
        pass  # Keep default dpr=1.0
    
    # Create pixmap at device resolution for crisp HiDPI rendering
    actual_size = (int(size[0] * dpr), int(size[1] * dpr))
    
    # Step 1: Render SVG to alpha mask
    pixmap = QtGui.QPixmap(actual_size[0], actual_size[1])
    if pixmap.isNull():
        _logger.warning("Failed to create pixmap for silhouette: %s", svg_path)
        return None
    pixmap.setDevicePixelRatio(dpr)
    pixmap.fill(QtCore.Qt.transparent)
    
    # Industry standard: Use try/finally to ensure QPainter.end() is always called
    svg_painter = QtGui.QPainter(pixmap)
    try:
        if not svg_painter.isActive():
            _logger.warning("Failed to begin QPainter for SVG rendering: %s", svg_path)
            return None
        svg_painter.setRenderHint(QtGui.QPainter.Antialiasing)
        svg_painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        renderer.render(svg_painter)
    finally:
        svg_painter.end()
    
    # Step 2: Create silhouette using QPainter composition (FAST - industry standard)
    # Instead of O(n²) Python loop, use native Qt composition modes
    silhouette = QtGui.QPixmap(actual_size[0], actual_size[1])
    if silhouette.isNull():
        _logger.warning("Failed to create silhouette pixmap: %s", svg_path)
        return None
    silhouette.setDevicePixelRatio(dpr)
    silhouette.fill(QtCore.Qt.transparent)
    
    painter = QtGui.QPainter(silhouette)
    try:
        if not painter.isActive():
            _logger.warning("Failed to begin QPainter for silhouette: %s", svg_path)
            return None
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Draw silhouette color as base (dark blue-black)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
        painter.fillRect(silhouette.rect(), QtGui.QColor(30, 30, 40, 200))
        
        # Use DestinationIn to mask with the SVG's alpha channel
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_DestinationIn)
        painter.drawPixmap(0, 0, pixmap)
    finally:
        painter.end()
    
    # Cache the final silhouette pixmap
    _lru_cache_set(_silhouette_pixmap_cache, cache_key, silhouette)
    
    return silhouette


class SilhouetteSvgWidget(QtWidgets.QWidget):
    """
    Custom widget that displays an SVG as a silhouette (black shape).
    Used for uncollected entities to show mysterious appearance.
    Size: 128x128 to match preview cards.
    
    OPTIMIZATION: Uses cached pre-rendered silhouette pixmaps instead of
    processing pixels on every paintEvent. This is industry standard for
    static image transformations in Qt applications.
    """
    # Industry standard: __slots__ reduces memory footprint for many instances
    __slots__ = ('svg_path', '_cached_pixmap')
    
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        # Pre-fetch the cached silhouette (lazy creation on first access)
        self._cached_pixmap = _get_cached_silhouette(svg_path, (128, 128))
        self.setFixedSize(128, 128)
        
    def paintEvent(self, event):
        """Optimized paint: just blit the pre-rendered cached pixmap.
        
        Note: Antialiasing hint not needed for pixmap blitting (no vector ops).
        SmoothPixmapTransform ensures quality on HiDPI displays.
        """
        if self._cached_pixmap is None:
            return  # Industry standard: graceful handling of missing resources
        
        # Industry standard: Use try/finally to ensure QPainter.end() is always called
        painter = QtGui.QPainter(self)
        try:
            if not painter.isActive():
                return
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)  # HiDPI support
            painter.drawPixmap(0, 0, self._cached_pixmap)
        finally:
            painter.end()


class AnimatedSvgWidget(QtWidgets.QWidget):
    """
    Widget that displays SVG with full animation support using QWebEngineView.
    Used for exceptional entities to show their embedded SMIL animations
    (e.g., wagging tails, electricity effects, rotating elements).
    
    Falls back to QSvgWidget if WebEngine is not available.
    
    OPTIMIZATION: Uses cached SVG content to avoid redundant file I/O
    when the same entity appears in multiple contexts.
    """
    # Industry standard: __slots__ reduces memory footprint for many instances
    __slots__ = ('svg_path', 'web_view', 'svg_widget')
    
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.web_view: Optional[QWebEngineView] = None  # Industry standard: explicit typing
        self.svg_widget: Optional[QSvgWidget] = None
        self.setFixedSize(128, 128)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        if HAS_WEBENGINE:
            # Use WebEngine for full SVG animation support
            # Industry standard: Pass parent for proper Qt object ownership/cleanup
            self.web_view = QWebEngineView(self)
            self.web_view.setFixedSize(128, 128)
            
            # Configure for transparent background
            self.web_view.page().setBackgroundColor(QtCore.Qt.transparent)
            self.web_view.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            
            # Disable scrollbars and interactions
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)  # For CSS animations
            
            # Load SVG with transparent background HTML wrapper
            self._load_svg()
            
            layout.addWidget(self.web_view)
        else:
            # Fallback to static QSvgWidget
            # Industry standard: Pass parent for proper Qt object ownership/cleanup
            self.svg_widget = QSvgWidget(svg_path, self)
            self.svg_widget.setFixedSize(128, 128)
            self.svg_widget.setStyleSheet("background: transparent;")
            layout.addWidget(self.svg_widget)
    
    @staticmethod
    def _get_cached_svg_content(svg_path: str) -> str:
        """Get cached SVG file content to avoid redundant file I/O.
        
        Industry best practice: Cache file content for frequently accessed
        resources to minimize disk operations. Uses module-level LRU cache.
        """
        global _svg_content_cache
        cached = _lru_cache_get(_svg_content_cache, svg_path)
        if cached is not None:
            return cached
        
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            _logger.exception("Error loading SVG %s", svg_path)
            content = '<svg></svg>'
        
        _lru_cache_set(_svg_content_cache, svg_path, content)
        return content
    
    def _load_svg(self):
        """Load the SVG file into WebEngine with proper styling."""
        if not self.web_view:
            return  # Industry standard: null safety
            
        # Use cached SVG content (industry standard: avoid redundant I/O)
        svg_content = self._get_cached_svg_content(self.svg_path)
        
        # Wrap SVG in HTML with transparent background and scaled display
        # SVGs are 64x64 viewBox, scale to 128x128 display
        html = f'''<!DOCTYPE html>
<html>
<head>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ 
        width: 128px; 
        height: 128px; 
        overflow: hidden;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    svg {{
        width: 128px;
        height: 128px;
        display: block;
    }}
</style>
</head>
<body>
{svg_content}
</body>
</html>'''
        
        # Load with file:// base URL to allow relative references
        base_url = QtCore.QUrl.fromLocalFile(str(Path(self.svg_path).parent) + '/')
        self.web_view.setHtml(html, base_url)
    
    def stop_animations(self) -> None:
        """Pause WebEngine animations without destroying content.
        
        Industry best practice: Use CSS animation-play-state to pause
        animations instead of unloading content, avoiding expensive re-render.
        """
        if self.web_view:
            # Pause all CSS/SMIL animations via JavaScript without unloading
            self.web_view.page().runJavaScript(
                "document.querySelectorAll('*').forEach(el => el.style.animationPlayState = 'paused');"
                "document.querySelectorAll('animate, animateTransform, animateMotion').forEach(el => el.endElement ? el.endElement() : null);"
            )
    
    def restart_animations(self) -> None:
        """Resume WebEngine animations."""
        if self.web_view:
            # Resume CSS animations; SMIL animations restart automatically on visibility
            self.web_view.page().runJavaScript(
                "document.querySelectorAll('*').forEach(el => el.style.animationPlayState = '');"
                "document.querySelectorAll('animate, animateTransform, animateMotion').forEach(el => el.beginElement ? el.beginElement() : null);"
            )


class EntityCard(QtWidgets.QFrame):
    """
    Card widget for displaying a single entity.
    Shows full details if collected, silhouette if not.
    Uses the same layout as preview_entities.py (180x220 with 128x128 SVG).
    
    Exceptional entities get special animated effects:
    - Pulsing border glow
    - Floating sparkle decorations
    - Shimmer sweep effect
    - Icon breathing/pulse effect
    - Rotating halo particles
    """
    
    clicked = QtCore.Signal(object, bool)  # Emits (Entity, is_exceptional) when clicked
    
    def __init__(self, entity: Entity, is_collected: bool, is_encountered: bool = False, 
                 is_exceptional: bool = False, exceptional_colors: dict = None, parent=None):
        super().__init__(parent)
        self.entity = entity
        self.is_collected = is_collected
        self.is_encountered = is_encountered
        self.is_exceptional = is_exceptional
        self.exceptional_colors = exceptional_colors or {}
        
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)
        self.setLineWidth(2)  # Match preview_entities.py
        self.setCursor(QtCore.Qt.PointingHandCursor)
        
        # Animation for exceptional cards
        self._glow_animation = None
        self._glow_value = 0.0
        self._sparkle_labels = []  # For sparkle decorations
        self._shimmer_widget = None  # Shimmer sweep overlay
        self._shimmer_timer = None  # Timer for shimmer animation
        self._halo_particles = []  # Rotating particles around icon
        self._icon_widget = None  # Store reference for animation
        self._icon_scale_animation = None
        self._icon_opacity_anim = None  # Opacity animation reference
        self._animations_paused = False  # Track animation state for lifecycle
        
        self._build_ui()
        
        # Start animations for exceptional entities
        if self.is_exceptional and self.is_collected:
            self._start_glow_animation()
            self._start_icon_breathing()
            self._create_shimmer_overlay()
        
    def _start_glow_animation(self):
        """Start the pulsing glow animation for exceptional entities."""
        self._glow_animation = QtCore.QPropertyAnimation(self, b"glow_value")
        self._glow_animation.setDuration(2000)  # 2 second pulse
        self._glow_animation.setStartValue(0.0)
        self._glow_animation.setEndValue(1.0)
        self._glow_animation.setLoopCount(-1)  # Infinite loop
        self._glow_animation.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        self._glow_animation.start()
        
    def _start_icon_breathing(self):
        """Create a subtle opacity pulse animation for the icon (breathing effect).
        
        Note: Skipped when using AnimatedSvgWidget since the SVG already has
        native SMIL animations (e.g., wagging tails, electricity effects).
        """
        if not self._icon_widget:
            return
        
        # Skip breathing effect for AnimatedSvgWidget - it has native SVG animations
        if HAS_WEBENGINE and isinstance(self._icon_widget, AnimatedSvgWidget):
            return
            
        # Use graphics effect for scale simulation via opacity pulse
        self._icon_effect = QtWidgets.QGraphicsOpacityEffect(self._icon_widget)
        self._icon_widget.setGraphicsEffect(self._icon_effect)
        
        self._icon_opacity_anim = QtCore.QPropertyAnimation(self._icon_effect, b"opacity")
        self._icon_opacity_anim.setDuration(1500)
        self._icon_opacity_anim.setStartValue(0.85)
        self._icon_opacity_anim.setEndValue(1.0)
        self._icon_opacity_anim.setLoopCount(-1)
        self._icon_opacity_anim.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        # Ping-pong by using keyframes
        self._icon_opacity_anim.setKeyValueAt(0.5, 1.0)
        self._icon_opacity_anim.setKeyValueAt(1.0, 0.85)
        self._icon_opacity_anim.start()
        
    def _create_shimmer_overlay(self):
        """Create a shimmer sweep effect that moves across the card."""
        # Create a transparent overlay widget for the shimmer
        self._shimmer_widget = QtWidgets.QWidget(self)
        self._shimmer_widget.setFixedSize(180, 220)
        self._shimmer_widget.move(0, 0)
        self._shimmer_widget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self._shimmer_widget.setStyleSheet("background: transparent;")
        self._shimmer_widget.lower()  # Behind sparkles but above background
        
        # Store shimmer position for animation
        self._shimmer_pos = -60  # Start off-screen left
        
        # Timer for shimmer animation
        self._shimmer_timer = QtCore.QTimer(self)
        self._shimmer_timer.timeout.connect(self._update_shimmer)
        self._shimmer_timer.start(50)  # 20 FPS for smooth animation
        
    def _update_shimmer(self):
        """Update shimmer sweep position."""
        if not self._shimmer_widget:
            return
            
        self._shimmer_pos += 3  # Speed of shimmer sweep
        if self._shimmer_pos > 240:  # Past card width + buffer
            self._shimmer_pos = -60  # Reset to start
            
        # Get shiny color for shimmer
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
        r, g, b = shiny_color
        
        # Create gradient shimmer effect at current position
        pos_pct = max(0, min(100, int((self._shimmer_pos / 180) * 100)))
        
        self._shimmer_widget.setStyleSheet(f"""
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0.5,
                stop: {max(0, pos_pct - 15) / 100:.2f} transparent,
                stop: {pos_pct / 100:.2f} rgba({r}, {g}, {b}, 40),
                stop: {min(100, pos_pct + 15) / 100:.2f} transparent
            );
        """)
    
    def _get_glow_value(self):
        return self._glow_value
    
    def _set_glow_value(self, value):
        self._glow_value = value
        self._update_exceptional_style()
    
    glow_value = QtCore.Property(float, _get_glow_value, _set_glow_value)
    
    def _update_exceptional_style(self):
        """Update the stylesheet for animated border shimmer effect."""
        if not self.is_exceptional:
            return
        
        # Use rarity background
        rarity = self.entity.rarity.lower()
        bg_base = RARITY_BG.get(rarity, "#2D2D2D")
        gradient_start = "#0D0D0D"
        gradient_end = bg_base
        
        # Get predefined shiny color for this entity
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))  # Default gold
        
        # Create color shimmer effect for border
        r_base, g_base, b_base = shiny_color
        
        # Pulse between the base color and a brighter version
        brightness_factor = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(self._glow_value * math.pi * 2))
        
        r = min(255, int(r_base + (255 - r_base) * (1 - brightness_factor) * 0.5))
        g = min(255, int(g_base + (255 - g_base) * (1 - brightness_factor) * 0.5))
        b = min(255, int(b_base + (255 - b_base) * (1 - brightness_factor) * 0.5))
        
        border_color = f"#{r:02X}{g:02X}{b:02X}"
        
        # Fixed border width (no bouncing)
        self.setStyleSheet(f"""
            EntityCard {{
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.8,
                    fx: 0.5, fy: 0.5,
                    stop: 0 {gradient_start},
                    stop: 1 {gradient_end}
                );
                border: 3px solid {border_color};
                border-radius: 12px;
            }}
        """)
        
        # Animate sparkle positions around the card
        self._update_sparkle_positions()
    
    def _update_sparkle_positions(self):
        """Animate sparkle decorations floating around the card with varying sizes."""
        if not self._sparkle_labels:
            return
        
        # Get shiny color for sparkle tint
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
        r, g, b = shiny_color
        
        # Sparkle positions orbit around the card
        positions = [
            (10, 10), (160, 10),   # Top corners
            (5, 100), (165, 100),  # Sides
            (40, 200), (130, 200), # Bottom
        ]
        
        for i, sparkle in enumerate(self._sparkle_labels):
            # Oscillate position and opacity with different phases
            phase = (self._glow_value * math.pi * 2) + (i * math.pi / 3)
            
            base_x, base_y = positions[i % len(positions)]
            # Larger orbit movement
            offset_x = math.sin(phase) * 8
            offset_y = math.cos(phase) * 8
            
            sparkle.move(int(base_x + offset_x), int(base_y + offset_y))
            
            # Vary font size for twinkling effect (10-16px)
            size = int(10 + 6 * (0.5 + 0.5 * math.sin(phase * 1.5)))
            
            # Pulse opacity - very subtle (0.1 - 0.25) for background touch
            opacity = 0.1 + 0.15 * (0.5 + 0.5 * math.sin(phase))
            alpha = int(255 * opacity)
            sparkle.setStyleSheet(f"""
                color: rgba({r},{g},{b},{alpha}); 
                background: transparent; 
                font-size: {size}px;
            """)
        
        # Update halo particles if they exist
        self._update_halo_particles()
    
    def _update_halo_particles(self):
        """Update rotating halo particles around the icon."""
        if not self._halo_particles:
            return
            
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
        r, g, b = shiny_color
        
        # Icon center position (90, 74 for 128x128 icon centered in 180 width card)
        center_x, center_y = 90, 74
        radius = 70  # Orbit radius around icon
        
        for i, particle in enumerate(self._halo_particles):
            # Each particle has different phase offset for smooth rotation
            angle = (self._glow_value * math.pi * 2) + (i * math.pi * 2 / len(self._halo_particles))
            
            x = center_x + radius * math.cos(angle) - 6  # -6 to center the particle
            y = center_y + radius * math.sin(angle) - 6
            
            particle.move(int(x), int(y))
            
            # Pulse opacity based on position - very subtle (15-35% opacity)
            opacity_factor = 0.15 + 0.2 * (0.5 + 0.5 * math.sin(angle + math.pi / 2))
            alpha = int(255 * opacity_factor)
            particle.setStyleSheet(f"""
                color: rgba({r},{g},{b},{alpha}); 
                background: transparent; 
                font-size: 10px;
            """)
    
    def _add_sparkle_decorations(self):
        """Add floating sparkle decorations around the card for exceptional entities."""
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
        r, g, b = shiny_color
        
        # Create sparkle emoji labels positioned absolutely on card
        sparkle_chars = ["✦", "✧", "★", "✦", "✧", "★"]
        positions = [
            (10, 10), (160, 10),   # Top corners
            (5, 100), (165, 100),  # Sides
            (40, 200), (130, 200), # Bottom
        ]
        
        for i, (x, y) in enumerate(positions):
            sparkle = QtWidgets.QLabel(sparkle_chars[i], self)
            # Start with low opacity (15%) for subtle effect
            sparkle.setStyleSheet(f"color: rgba({r},{g},{b},38); background: transparent; font-size: 12px;")
            sparkle.setFixedSize(20, 20)  # Slightly larger for size animation
            sparkle.move(x, y)
            sparkle.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            sparkle.show()
            self._sparkle_labels.append(sparkle)
        
        # Add rotating halo particles around the icon
        self._add_halo_particles()
    
    def _add_halo_particles(self):
        """Add rotating particle effect around the entity icon."""
        shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
        r, g, b = shiny_color
        
        # Create 8 small particles that will orbit the icon
        particle_chars = ["•", "◦", "·", "•", "◦", "·", "•", "◦"]
        
        for i, char in enumerate(particle_chars):
            particle = QtWidgets.QLabel(char, self)
            # Start with low opacity (20%) for subtle effect
            particle.setStyleSheet(f"color: rgba({r},{g},{b},51); background: transparent; font-size: 10px;")
            particle.setFixedSize(12, 12)
            particle.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            particle.show()
            self._halo_particles.append(particle)
        
    def _build_ui(self):
        rarity = self.entity.rarity.lower()
        rarity_color = RARITY_COLORS.get(rarity, "#9E9E9E")
        bg_base = RARITY_BG.get(rarity, "#2D2D2D")
        gradient_start = "#0D0D0D"  # Very dark center
        gradient_end = bg_base  # Rarity-tinted outer
        
        # Exceptional entities get golden outline with rarity background
        if self.is_exceptional and self.is_collected:
            # Get predefined shiny color for border
            shiny_color = EXCEPTIONAL_ENTITY_COLORS.get(self.entity.id, (255, 215, 0))
            shiny_hex = f"#{shiny_color[0]:02X}{shiny_color[1]:02X}{shiny_color[2]:02X}"
            self.setStyleSheet(f"""
                EntityCard {{
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8,
                        fx: 0.5, fy: 0.5,
                        stop: 0 {gradient_start},
                        stop: 1 {gradient_end}
                    );
                    border: 3px solid {shiny_hex};
                    border-radius: 12px;
                }}
            """)
        elif self.is_collected:
            # Card styling based on collection status - gradient background with rarity border
            self.setStyleSheet(f"""
                EntityCard {{
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8,
                        fx: 0.5, fy: 0.5,
                        stop: 0 {gradient_start},
                        stop: 1 {gradient_end}
                    );
                    border: 3px solid {rarity_color};
                    border-radius: 12px;
                }}
                EntityCard:hover {{
                    border: 3px solid #FFD700;
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8,
                        fx: 0.5, fy: 0.5,
                        stop: 0 #151515,
                        stop: 1 {gradient_end}
                    );
                }}
            """)
        else:
            # Darker, mysterious look for uncollected
            gradient_start = "#080808"
            gradient_end = "#1A1A1A"
            # Give exceptional uncollected slots a subtle golden border hint
            if self.is_exceptional:
                border_color = "#3A3A20"  # Dim gold hint
            else:
                border_color = "#2A2A2A"
            self.setStyleSheet(f"""
                EntityCard {{
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8,
                        fx: 0.5, fy: 0.5,
                        stop: 0 {gradient_start},
                        stop: 1 {gradient_end}
                    );
                    border: 3px solid {border_color};
                    border-radius: 12px;
                }}
                EntityCard:hover {{
                    border: 3px solid {"#5A5A30" if self.is_exceptional else "#444444"};
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.8,
                        fx: 0.5, fy: 0.5,
                        stop: 0 #101010,
                        stop: 1 #222222
                    );
                }}
            """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Entity icon - resolve SVG path properly
        # Use exceptional SVG if entity is collected and exceptional
        use_exceptional = self.is_collected and self.is_exceptional
        svg_path = _resolve_entity_svg_path(self.entity, is_exceptional=use_exceptional)
        
        # Center the SVG (matching preview_entities.py layout)
        svg_container = QtWidgets.QWidget()
        svg_layout = QtWidgets.QHBoxLayout(svg_container)
        svg_layout.addStretch()
        svg_layout.setContentsMargins(0, 0, 0, 0)
        
        if svg_path and os.path.exists(svg_path):
            if self.is_collected:
                if HAS_WEBENGINE:
                    # Use AnimatedSvgWidget for all collected entities (supports SMIL animations)
                    # This enables wagging tails, electricity effects, rotating elements, etc.
                    # Industry standard: Pass parent for proper Qt object ownership/cleanup
                    icon_widget = AnimatedSvgWidget(svg_path, svg_container)
                else:
                    # Fallback to QSvgWidget if WebEngine not available
                    # Industry standard: Pass parent for proper Qt object ownership/cleanup
                    icon_widget = QSvgWidget(svg_path, svg_container)
                    icon_widget.setFixedSize(128, 128)
                    icon_widget.setStyleSheet("background: transparent;")
                # Store reference for animation
                self._icon_widget = icon_widget
            else:
                # Silhouette for uncollected - also 128x128
                # Industry standard: Pass parent for proper Qt object ownership/cleanup
                icon_widget = SilhouetteSvgWidget(svg_path, svg_container)
                icon_widget.setFixedSize(128, 128)
        else:
            # Placeholder if no SVG
            icon_widget = QtWidgets.QLabel("❓")
            icon_widget.setAlignment(QtCore.Qt.AlignCenter)
            icon_widget.setFixedSize(128, 128)
            icon_widget.setStyleSheet("font-size: 64px; color: #333333;")
        
        svg_layout.addWidget(icon_widget)
        svg_layout.addStretch()
        layout.addWidget(svg_container)
        
        # Entity name - matching preview_entities.py style
        # For exceptional entities, show the playful exceptional_name if available
        if self.is_collected:
            if self.is_exceptional and self.entity.exceptional_name:
                name_text = self.entity.exceptional_name
            else:
                name_text = self.entity.name
            name_color = rarity_color
        elif self.is_encountered:
            name_text = "???"
            name_color = "#555555"
        else:
            name_text = "???"
            name_color = "#333333"
        
        # Add star prefix for exceptional slot
        if self.is_exceptional and not self.is_collected:
            name_text = f"⭐ {name_text}"
            name_color = "#4A4A2A"  # Dim gold hint
        
        name_label = QtWidgets.QLabel(name_text)
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setFont(QtGui.QFont("Segoe UI", 8, QtGui.QFont.Bold))
        name_label.setStyleSheet(f"color: {name_color}; background: transparent;")
        name_label.setMinimumHeight(32)  # Reserve space for two lines
        layout.addWidget(name_label, 0, QtCore.Qt.AlignCenter)
        
        # Power display - matching preview_entities.py style
        if self.is_collected:
            power_text = f"⚔️ Power: {self.entity.power}"
            power_color = "#FFFFFF"
        else:
            power_text = "⚔️ ???"
            power_color = "#333333"
        
        power_label = QtWidgets.QLabel(power_text)
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setFont(QtGui.QFont("Segoe UI", 10))
        power_label.setStyleSheet(f"color: {power_color}; background: transparent;")
        layout.addWidget(power_label)
        
        # Rarity badge - styled like preview_entities.py
        if self.is_collected:
            # Add star icon for exceptional entities
            if self.is_exceptional:
                rarity_text = f"⭐ {rarity.upper()}"
            else:
                rarity_text = rarity.upper()
            rarity_label_color = rarity_color
        else:
            # Show star hint for exceptional slot
            if self.is_exceptional:
                rarity_text = "⭐ ???"
                rarity_label_color = "#4A4A2A"  # Dim gold hint
            else:
                rarity_text = "???"
                rarity_label_color = "#333333"
        
        rarity_label = QtWidgets.QLabel(rarity_text)
        rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        rarity_label.setFont(QtGui.QFont("Segoe UI", 9, QtGui.QFont.Bold))
        rarity_label.setStyleSheet(f"color: {rarity_label_color}; background: transparent;")
        layout.addWidget(rarity_label)
        
        # Card size: 180 wide, 235 tall (extra height for two-line names)
        self.setFixedSize(180, 235)
        
        # Set hover tooltip with entity info
        self._setup_tooltip()
        
        # Add sparkle decorations for exceptional entities (after setFixedSize so they can be positioned)
        if self.is_collected and self.is_exceptional:
            self._add_sparkle_decorations()
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.entity, self.is_exceptional)
        super().mousePressEvent(event)
    
    def _setup_tooltip(self):
        """Setup rich hover tooltip with entity info."""
        if self.is_collected:
            # Show full entity info
            variant = "⭐ EXCEPTIONAL" if self.is_exceptional else ""
            name = self.entity.exceptional_name if self.is_exceptional and self.entity.exceptional_name else self.entity.name
            rarity = self.entity.rarity.upper()
            rarity_color = RARITY_COLORS.get(self.entity.rarity.lower(), "#9E9E9E")
            lore = self.entity.lore
            # Wrap lore text for readability
            lore_lines = []
            words = lore.split()
            current_line = []
            for word in words:
                current_line.append(word)
                if len(' '.join(current_line)) > 50:
                    lore_lines.append(' '.join(current_line))
                    current_line = []
            if current_line:
                lore_lines.append(' '.join(current_line))
            lore_wrapped = '<br>'.join(lore_lines)
            
            tooltip = f'''
<div style="padding: 8px; max-width: 300px;">
<b style="color: {rarity_color}; font-size: 14px;">{variant} {name}</b><br>
<span style="color: {rarity_color};">⚔️ Power: {self.entity.power} | {rarity}</span>
<hr style="border-color: #444;">
<span style="color: #CCC;">{lore_wrapped}</span>
</div>
'''.strip()
        elif self.is_encountered:
            tooltip = '''
<div style="padding: 8px;">
<b style="color: #666;">??? Unknown Entity</b><br>
<span style="color: #888;">You've seen this entity before!</span><br>
<span style="color: #666;">Complete focus sessions to bond with it.</span>
</div>
'''.strip()
        else:
            if self.is_exceptional:
                tooltip = '''
<div style="padding: 8px;">
<b style="color: #FFD700;">⭐ ??? Exceptional Unknown</b><br>
<span style="color: #888;">A rare exceptional variant awaits...</span><br>
<span style="color: #666;">Complete focus sessions to discover it!</span>
</div>
'''.strip()
            else:
                tooltip = '''
<div style="padding: 8px;">
<b style="color: #555;">??? Unknown Entity</b><br>
<span style="color: #666;">Complete focus sessions to encounter new companions!</span>
</div>
'''.strip()
        
        self.setToolTip(tooltip)
    
    def pause_animations(self) -> None:
        """Pause all animations to save CPU when tab is not visible.
        
        Industry best practice: Explicitly manage animation lifecycle to prevent
        background CPU usage from hidden widgets with running animations.
        """
        if self._animations_paused:
            return
        self._animations_paused = True
        
        # Pause glow animation
        if self._glow_animation and self._glow_animation.state() == QtCore.QAbstractAnimation.Running:
            self._glow_animation.pause()
        
        # Pause opacity animation
        if self._icon_opacity_anim and self._icon_opacity_anim.state() == QtCore.QAbstractAnimation.Running:
            self._icon_opacity_anim.pause()
        
        # Stop shimmer timer (high frequency - 50ms)
        if self._shimmer_timer and self._shimmer_timer.isActive():
            self._shimmer_timer.stop()
        
        # Note: WebEngine animations are NOT paused to avoid delay/flicker on tab switch.
        # The CPU cost of small SVG animations is negligible compared to re-render delays.
    
    def resume_animations(self) -> None:
        """Resume animations when tab becomes visible.
        
        Industry best practice: Defer re-initialization until widget is visible
        to avoid wasted work on offscreen widgets.
        """
        if not self._animations_paused:
            return
        self._animations_paused = False
        
        # Resume glow animation
        if self._glow_animation and self._glow_animation.state() == QtCore.QAbstractAnimation.Paused:
            self._glow_animation.resume()
        
        # Resume opacity animation
        if self._icon_opacity_anim and self._icon_opacity_anim.state() == QtCore.QAbstractAnimation.Paused:
            self._icon_opacity_anim.resume()
        
        # Restart shimmer timer
        if self._shimmer_timer and not self._shimmer_timer.isActive():
            self._shimmer_timer.start(50)
        
        # Note: WebEngine animations run continuously (never paused) to avoid delay/flicker.


# Theme info for tabs (matching preview_entities.py)
THEME_INFO = {
    "warrior": ("🗡️ Warrior", "#C62828"),
    "scholar": ("📚 Scholar", "#6A1B9A"),
    "underdog": ("💪 Underdog", "#E65100"),
    "scientist": ("🔬 Scientist", "#1565C0"),
    "wanderer": ("🗺️ Wanderer", "#2E7D32"),
}


class EntitidexTab(QtWidgets.QWidget):
    """
    Main Entitidex tab showing the entity collection.
    Uses tabbed interface with one tab per story theme (matching preview_entities.py).
    
    Performance optimizations:
    - Lazy initialization: UI only built on first show
    - Animation lifecycle: All animations pause when tab hidden
    - Card tracking: All cards registered for bulk pause/resume
    """
    
    def __init__(self, blocker, parent=None):
        super().__init__(parent)
        self.blocker = blocker
        self.current_story = "warrior"
        self.progress = EntitidexProgress()
        self.theme_tabs = {}  # Store references to theme tab widgets
        
        # Performance: Track all cards for animation lifecycle management
        self._all_cards: list = []  # List[EntityCard]
        self._is_visible = False
        self._initialized = False  # Lazy init flag
        
        # Lightweight placeholder - actual UI built on first showEvent
        self._placeholder_layout = QtWidgets.QVBoxLayout(self)
        self._placeholder_label = QtWidgets.QLabel("📖 Loading Entitidex...")
        self._placeholder_label.setAlignment(QtCore.Qt.AlignCenter)
        self._placeholder_label.setStyleSheet("color: #666; font-size: 16px;")
        self._placeholder_layout.addWidget(self._placeholder_label)
    
    def preload(self) -> None:
        """Pre-initialize the tab in background for instant display.
        
        Call this from the main window after startup to build the UI
        before the user clicks the tab, eliminating load delay.
        """
        if self._initialized:
            return
        self._initialized = True
        # Remove placeholder label
        if self._placeholder_label:
            self._placeholder_label.deleteLater()
            self._placeholder_label = None
        # Load data and build real UI (reuses existing layout)
        self._load_progress()
        self._build_ui()
        # Start with animations paused since tab isn't visible yet
        for card in self._all_cards:
            card.pause_animations()
    
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Called when tab becomes visible - lazy init and resume animations."""
        super().showEvent(event)
        self._is_visible = True
        
        # Lazy initialization on first show
        if not self._initialized:
            self._initialized = True
            # Remove placeholder label
            self._placeholder_label.deleteLater()
            self._placeholder_label = None
            # Load data and build real UI (reuses existing layout)
            self._load_progress()
            self._build_ui()
        
        # Resume all card animations
        for card in self._all_cards:
            card.resume_animations()
    
    def hideEvent(self, event: QtGui.QHideEvent) -> None:
        """Called when tab is hidden - pause animations to save resources."""
        super().hideEvent(event)
        self._is_visible = False
        
        # Pause all card animations to save CPU
        for card in self._all_cards:
            card.pause_animations()
    
    def _load_progress(self):
        """Load entitidex progress from blocker config."""
        try:
            if hasattr(self.blocker, 'adhd_buster'):
                entitidex_data = self.blocker.adhd_buster.get("entitidex", {})
                if entitidex_data:
                    # Support both old "collected" and new "collected_entity_ids" keys
                    collected = set(entitidex_data.get("collected_entity_ids", 
                                    entitidex_data.get("collected", [])))
                    encounters = entitidex_data.get("encounters", {})
                    exceptional = entitidex_data.get("exceptional_entities", {})
                    self.progress.collected_entity_ids = collected
                    self.progress.encounters = encounters
                    self.progress.exceptional_entities = exceptional
        except Exception:
            _logger.exception("Error loading entitidex progress")
    
    def _save_progress(self):
        """Save entitidex progress to blocker config."""
        try:
            if hasattr(self.blocker, 'adhd_buster'):
                self.blocker.adhd_buster["entitidex"] = {
                    "collected_entity_ids": list(self.progress.collected_entity_ids),
                    "encounters": self.progress.encounters,
                    "exceptional_entities": self.progress.exceptional_entities,
                }
                self.blocker.save_config()
        except Exception:
            _logger.exception("Error saving entitidex progress")
    
    def _build_ui(self):
        # Reuse the existing placeholder layout instead of creating a new one
        layout = self._placeholder_layout
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QtWidgets.QHBoxLayout()
        
        title = QtWidgets.QLabel("📖 Entitidex")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #FFD700;
            }
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Overall progress label
        self.total_progress_label = QtWidgets.QLabel()
        self.total_progress_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        header_layout.addWidget(self.total_progress_label)
        
        layout.addLayout(header_layout)
        
        # Tab widget for themes (matching preview_entities.py style)
        self.theme_tab_widget = QtWidgets.QTabWidget()
        self.theme_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #1A1A1A;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #FFFFFF;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #444444;
            }
            QTabBar::tab:hover {
                background-color: #3A3A3A;
            }
        """)
        
        # Create a tab for each theme
        for theme_key, (theme_name, theme_color) in THEME_INFO.items():
            tab_widget = self._create_theme_tab(theme_key)
            self.theme_tab_widget.addTab(tab_widget, theme_name)
            self.theme_tabs[theme_key] = tab_widget
        
        layout.addWidget(self.theme_tab_widget)
        
        # Note: Entity info is now shown via hover tooltips on cards (cleaner UX)
        
        # Load initial data
        self._refresh_all_tabs()
    
    def _create_theme_tab(self, theme_key: str) -> QtWidgets.QWidget:
        """Create a tab widget for a specific theme."""
        tab_container = QtWidgets.QWidget()
        tab_layout = QtWidgets.QVBoxLayout(tab_container)
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        
        # Progress bar for this theme
        progress_frame = QtWidgets.QFrame()
        progress_frame.setStyleSheet("""
            QFrame {
                background: #1E1E1E;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        progress_layout = QtWidgets.QVBoxLayout(progress_frame)
        
        progress_label = QtWidgets.QLabel(f"Collection Progress - {theme_key.capitalize()}")
        progress_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        progress_label.setObjectName(f"progress_label_{theme_key}")
        progress_layout.addWidget(progress_label)
        
        progress_bar = QtWidgets.QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setTextVisible(True)
        progress_bar.setObjectName(f"progress_bar_{theme_key}")
        progress_bar.setStyleSheet("""
            QProgressBar {
                background: #333333;
                border-radius: 5px;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #8BC34A);
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(progress_bar)
        
        stats_label = QtWidgets.QLabel()
        stats_label.setAlignment(QtCore.Qt.AlignCenter)
        stats_label.setStyleSheet("color: #888888; font-size: 11px;")
        stats_label.setObjectName(f"stats_label_{theme_key}")
        progress_layout.addWidget(stats_label)
        
        tab_layout.addWidget(progress_frame)
        
        # Scroll area for entity cards
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #1E1E1E;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        cards_container = QtWidgets.QWidget()
        cards_container.setObjectName(f"cards_container_{theme_key}")
        # Prevent container from requesting excessive size
        cards_container.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, 
            QtWidgets.QSizePolicy.Preferred
        )
        cards_layout = QtWidgets.QGridLayout(cards_container)
        cards_layout.setSpacing(16)
        cards_layout.setContentsMargins(16, 16, 16, 16)
        
        scroll.setWidget(cards_container)
        tab_layout.addWidget(scroll)
        
        return tab_container
    
    def _create_entity_pair_widget(self, entity: Entity) -> QtWidgets.QWidget:
        """Create a widget containing both normal and exceptional cards for an entity."""
        pair_widget = QtWidgets.QWidget()
        pair_layout = QtWidgets.QHBoxLayout(pair_widget)
        pair_layout.setContentsMargins(0, 0, 0, 0)
        pair_layout.setSpacing(8)
        
        # Normal card
        is_collected_normal = self.progress.is_collected(entity.id) and not self.progress.is_exceptional(entity.id)
        # If user has exceptional, they also have normal (exceptional is upgrade)
        if self.progress.is_collected(entity.id):
            is_collected_normal = True
        is_encountered = self.progress.is_encountered(entity.id)
        
        normal_card = EntityCard(
            entity, is_collected_normal, is_encountered,
            is_exceptional=False,
            exceptional_colors={}
        )
        # Note: Click removed - hover tooltips show entity info now
        pair_layout.addWidget(normal_card)
        
        # Exceptional card
        is_collected_exceptional = self.progress.is_exceptional(entity.id)
        exceptional_colors = self.progress.get_exceptional_colors(entity.id)
        
        exceptional_card = EntityCard(
            entity, is_collected_exceptional, is_encountered,
            is_exceptional=True,
            exceptional_colors=exceptional_colors
        )
        # Note: Click removed - hover tooltips show entity info now
        pair_layout.addWidget(exceptional_card)
        
        # Register cards for lifecycle management (pause/resume)
        self._all_cards.append(normal_card)
        self._all_cards.append(exceptional_card)
        
        # If tab is currently hidden, start with animations paused
        if not self._is_visible:
            normal_card.pause_animations()
            exceptional_card.pause_animations()
        
        return pair_widget

    def _refresh_theme_tab(self, theme_key: str):
        """Refresh a single theme tab."""
        if theme_key not in self.theme_tabs:
            return
            
        tab_widget = self.theme_tabs[theme_key]
        
        # Find the cards container and clear it
        cards_container = tab_widget.findChild(QtWidgets.QWidget, f"cards_container_{theme_key}")
        if not cards_container:
            return
            
        cards_layout = cards_container.layout()
        
        # Cleanup: Remove old cards from lifecycle tracking before deletion
        cards_to_remove = []
        for card in self._all_cards:
            # Check if card belongs to this container (via parent chain)
            if card.parent() and card.parent().parent() == cards_container:
                card.pause_animations()  # Stop animations before deletion
                cards_to_remove.append(card)
        for card in cards_to_remove:
            self._all_cards.remove(card)
        
        # Clear existing cards
        while cards_layout.count():
            child = cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Get entities for this theme
        entities = get_entities_for_story(theme_key)
        entities_sorted = sorted(entities, key=lambda e: e.power)
        
        # Calculate progress - count normal and exceptional separately
        collected_normal = 0
        collected_exceptional = 0
        encountered_count = 0
        
        for entity in entities_sorted:
            if self.progress.is_collected(entity.id):
                collected_normal += 1
                if self.progress.is_exceptional(entity.id):
                    collected_exceptional += 1
            elif self.progress.is_encountered(entity.id):
                encountered_count += 1
        
        total_entities = len(entities_sorted)
        total_slots = total_entities * 2  # Normal + Exceptional for each
        total_collected = collected_normal + collected_exceptional
        progress_percent = int((total_collected / total_slots) * 100) if total_slots > 0 else 0
        
        # Update progress display for this tab
        progress_bar = tab_widget.findChild(QtWidgets.QProgressBar, f"progress_bar_{theme_key}")
        if progress_bar:
            progress_bar.setValue(progress_percent)
            progress_bar.setFormat(f"{total_collected}/{total_slots} ({progress_percent}%)")
        
        stats_label = tab_widget.findChild(QtWidgets.QLabel, f"stats_label_{theme_key}")
        if stats_label:
            stats_label.setText(
                f"✅ Normal: {collected_normal}/{total_entities}  |  "
                f"⭐ Exceptional: {collected_exceptional}/{total_entities}  |  "
                f"👁️ Encountered: {encountered_count}"
            )
        
        # Create paired cards - Layout: Each entity gets [Normal | Exceptional] pair
        # Sort by rarity for proper grouping
        rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}
        entities_by_rarity = sorted(entities_sorted, key=lambda e: rarity_order.get(e.rarity.lower(), 0))
        
        # Separate legendary from others
        legendary = [e for e in entities_by_rarity if e.rarity.lower() == "legendary"]
        others = [e for e in entities_by_rarity if e.rarity.lower() != "legendary"]
        
        # Layout grid with paired cards (each pair is wider, so 2 pairs per row)
        # Row 0: Legendary pair centered
        # Row 1-2: Epic pairs
        # Row 3-4: Rare pairs  
        # Row 5-6: Uncommon pairs
        # Row 7-8: Common pairs
        
        current_row = 0
        
        # Add legendary at top center
        for entity in legendary:
            pair_widget = self._create_entity_pair_widget(entity)
            cards_layout.addWidget(pair_widget, current_row, 0, 1, 1, QtCore.Qt.AlignCenter)
            current_row += 1
        
        # Sort remaining by rarity (highest first for display)
        epic = [e for e in others if e.rarity.lower() == "epic"]
        rare = [e for e in others if e.rarity.lower() == "rare"]
        uncommon = [e for e in others if e.rarity.lower() == "uncommon"]
        common = [e for e in others if e.rarity.lower() == "common"]
        
        # Add each rarity group - one entity pair per row, centered
        for rarity_group in [epic, rare, uncommon, common]:
            for entity in rarity_group:
                pair_widget = self._create_entity_pair_widget(entity)
                cards_layout.addWidget(pair_widget, current_row, 0, 1, 1, QtCore.Qt.AlignCenter)
                current_row += 1
    
    def _refresh_all_tabs(self):
        """Refresh all theme tabs and update total progress."""
        total_normal = 0
        total_exceptional = 0
        total_entities = 0
        
        for theme_key in THEME_INFO.keys():
            self._refresh_theme_tab(theme_key)
            
            # Count for total progress
            entities = get_entities_for_story(theme_key)
            total_entities += len(entities)
            for entity in entities:
                if self.progress.is_collected(entity.id):
                    total_normal += 1
                    if self.progress.is_exceptional(entity.id):
                        total_exceptional += 1
        
        # Update total progress label (both normal and exceptional)
        total_slots = total_entities * 2  # Normal + Exceptional for each
        total_collected = total_normal + total_exceptional
        total_percent = int((total_collected / total_slots) * 100) if total_slots > 0 else 0
        self.total_progress_label.setText(
            f"Total: {total_collected}/{total_slots} ({total_percent}%) | "
            f"Normal: {total_normal} | ⭐ Exceptional: {total_exceptional}"
        )
    
    def _on_story_changed(self, story: str):
        """Legacy method - kept for compatibility."""
        self.current_story = story
        # Find and select the corresponding tab
        theme_keys = list(THEME_INFO.keys())
        if story in theme_keys:
            self.theme_tab_widget.setCurrentIndex(theme_keys.index(story))
    
    # Note: _on_entity_clicked removed - entity info now shown via hover tooltips
    
    def add_collected_entity(self, entity_id: str):
        """Mark an entity as collected and refresh display."""
        self.progress.collected_entity_ids.add(entity_id)
        self._save_progress()
        self._refresh_all_tabs()
    
    def add_encountered_entity(self, entity_id: str):
        """Mark an entity as encountered and refresh display."""
        self.progress.record_encounter(entity_id)
        self._save_progress()
        self._refresh_all_tabs()
    
    def refresh(self):
        """Public method to refresh the display."""
        self._load_progress()
        self._refresh_all_tabs()
