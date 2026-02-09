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
    get_theme_celebration,
    play_celebration_sound,
    preload_celebration_sounds,
)
from entitidex.entity_perks import calculate_active_perks, ENTITY_PERKS, PerkType, get_perk_description, get_perk_explanation
from styled_dialog import add_tab_help_button, styled_info, styled_warning, styled_question
from app_utils import get_app_dir


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

# Path to entity SVGs (use helper for PyInstaller compatibility)
ENTITY_ICONS_PATH = get_app_dir() / "icons" / "entities"
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
                border: 2px solid {border_color};
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
                    border: 2px solid {shiny_hex};
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
                    border: 2px solid {rarity_color};
                    border-radius: 12px;
                }}
                EntityCard:hover {{
                    border: 2px solid #8b8bb8;
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
                    border: 2px solid {border_color};
                    border-radius: 12px;
                }}
                EntityCard:hover {{
                    border: 2px solid {"#5A5A30" if self.is_exceptional else "#444444"};
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
            elif self.is_encountered:
                # Silhouette for encountered but not caught - user knows the shape
                # Industry standard: Pass parent for proper Qt object ownership/cleanup
                icon_widget = SilhouetteSvgWidget(svg_path, svg_container)
                icon_widget.setFixedSize(128, 128)
            else:
                # Question mark for never-encountered - complete mystery
                icon_widget = QtWidgets.QLabel("❓")
                icon_widget.setAlignment(QtCore.Qt.AlignCenter)
                icon_widget.setFixedSize(128, 128)
                icon_widget.setStyleSheet("font-size: 64px; color: #555555; background: transparent;")
        else:
            # X placeholder if SVG file missing or failed to load
            icon_widget = QtWidgets.QLabel("❌")
            icon_widget.setAlignment(QtCore.Qt.AlignCenter)
            icon_widget.setFixedSize(128, 128)
            icon_widget.setStyleSheet("font-size: 64px; color: #AA3333; background: transparent;")
        
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
        
        # Perk label - show brief perk info for collected entities
        if self.is_collected:
            perks = ENTITY_PERKS.get(self.entity.id)
            if perks:
                # Brief perk text: show first perk's icon + short description
                perk = perks[0]  # Primary perk for display
                value = perk.exceptional_value if self.is_exceptional else perk.normal_value
                # Format compact perk text (e.g., "+5% XP" or "+2 Power")
                perk_brief = self._format_brief_perk(perk, value)
                # Add indicator if entity has multiple perks
                if len(perks) > 1:
                    perk_brief += f" (+{len(perks)-1})"
                perk_label = QtWidgets.QLabel(perk_brief)
                perk_label.setAlignment(QtCore.Qt.AlignCenter)
                perk_label.setFont(QtGui.QFont("Segoe UI", 8))
                perk_label.setStyleSheet("color: #7FDBFF; background: transparent;")  # Cyan for perks
                perk_label.setToolTip(get_perk_description(self.entity.id, self.is_exceptional))
                layout.addWidget(perk_label)
        
        # Card size: 180 wide, 255 tall (extra height for perk label)
        self.setFixedSize(180, 255)
        
        # Set hover tooltip with entity info
        self._setup_tooltip()
        
        # Add sparkle decorations for exceptional entities (after setFixedSize so they can be positioned)
        if self.is_collected and self.is_exceptional:
            self._add_sparkle_decorations()
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.entity, self.is_exceptional)
        super().mousePressEvent(event)
    
    def _format_brief_perk(self, perk, value: float) -> str:
        """Format a brief perk description for display on the card.
        
        Args:
            perk: EntityPerk object
            value: The perk value (normal or exceptional)
            
        Returns:
            Brief string like "+5% XP" or "+2 Power"
        """
        ptype = perk.perk_type
        
        # Categorize by perk type for compact display
        if ptype == PerkType.POWER_FLAT:
            return f"{perk.icon} +{int(value)} Power"
        elif ptype in (PerkType.XP_PERCENT, PerkType.XP_SESSION, PerkType.XP_LONG_SESSION, 
                       PerkType.XP_NIGHT, PerkType.XP_MORNING, PerkType.XP_STORY):
            return f"{perk.icon} +{int(value)}% XP"
        elif ptype == PerkType.COIN_FLAT:
            return f"{perk.icon} +{int(value)} Coins"
        elif ptype == PerkType.COIN_PERCENT:
            return f"{perk.icon} +{int(value)}% Coins"
        elif ptype == PerkType.SALVAGE_BONUS:
            return f"{perk.icon} +{int(value)} Salvage"
        elif ptype in (PerkType.DROP_LUCK, PerkType.MERGE_LUCK, PerkType.ALL_LUCK, PerkType.MERGE_SUCCESS):
            return f"{perk.icon} +{int(value)}% Luck"
        elif ptype == PerkType.RARITY_BIAS:
            return f"{perk.icon} +{int(value)}% Rarity"
        elif ptype in (PerkType.ENCOUNTER_CHANCE, PerkType.CAPTURE_BONUS):
            return f"{perk.icon} +{int(value)}% Catch"
        elif ptype == PerkType.PITY_BONUS:
            return f"{perk.icon} +{int(value)}% Pity"
        elif ptype == PerkType.HYDRATION_COOLDOWN:
            return f"{perk.icon} -{int(value)}min Water"
        elif ptype == PerkType.HYDRATION_CAP:
            return f"{perk.icon} +{int(value)} Glass Cap"
        elif ptype == PerkType.EYE_REST_CAP:
            return f"{perk.icon} +{int(value)} Eye Rest"
        elif ptype == PerkType.EYE_TIER_BONUS:
            if int(value) > 0:
                return f"{perk.icon} +{int(value)} Eye Tier"
            else:
                return f"{perk.icon} 50% Eye Reroll"
        elif ptype == PerkType.INVENTORY_SLOTS:
            return f"{perk.icon} +{int(value)} Slots"
        elif ptype == PerkType.PERFECT_SESSION:
            return f"{perk.icon} +{int(value)}% Perfect"
        elif ptype == PerkType.STREAK_SAVE:
            return f"{perk.icon} +{int(value)}% Streak"
        elif ptype == PerkType.SCRAP_CHANCE:
            return f"{perk.icon} +{int(value)}% Scrap"
        else:
            # Fallback: use description template
            return f"{perk.icon} +{int(value)}"
    
    def _setup_tooltip(self):
        """Setup rich hover tooltip with entity info."""
        if self.is_collected:
            # Show full entity info
            variant = "⭐ EXCEPTIONAL" if self.is_exceptional else ""
            name = self.entity.exceptional_name if self.is_exceptional and self.entity.exceptional_name else self.entity.name
            rarity = self.entity.rarity.upper()
            rarity_color = RARITY_COLORS.get(self.entity.rarity.lower(), "#9E9E9E")
            # Use exceptional lore if available for exceptional entities
            if self.is_exceptional and self.entity.exceptional_lore:
                lore = self.entity.exceptional_lore
            else:
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
            
            # Get perk info for tooltip
            perks = ENTITY_PERKS.get(self.entity.id)
            perk_html = ""
            if perks:
                perk_desc = get_perk_description(self.entity.id, self.is_exceptional)
                perk_explain = get_perk_explanation(self.entity.id)
                perk_html = f'''<br><hr style="border-color: #444;">
<span style="color: #7FDBFF;">✨ PERK: {perk_desc}</span><br>
<span style="color: #888; font-size: 11px;">ℹ️ {perk_explain}</span>'''
            
            tooltip = f'''
<div style="padding: 8px; max-width: 320px;">
<b style="color: {rarity_color}; font-size: 14px;">{variant} {name}</b><br>
<span style="color: {rarity_color};">⚔️ Power: {self.entity.power} | {rarity}</span>
<hr style="border-color: #444;">
<span style="color: #CCC;">{lore_wrapped}</span>{perk_html}
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
        
        # Pause WebEngine SVG animations via JavaScript injection
        # This saves CPU when the tab is hidden or minimized for extended periods
        if self._icon_widget and isinstance(self._icon_widget, AnimatedSvgWidget):
            self._icon_widget.stop_animations()
    
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
        
        # Resume WebEngine SVG animations
        if self._icon_widget and isinstance(self._icon_widget, AnimatedSvgWidget):
            self._icon_widget.restart_animations()


# =============================================================================
# CELEBRATION CARD - Theme Completion Reward
# Displayed when user collects all entities from a theme
# =============================================================================

# Path to celebration SVGs (use helper for PyInstaller compatibility)
CELEBRATION_ICONS_PATH = get_app_dir() / "icons" / "celebrations"

# Cache colorsys import for CelebrationCard rainbow effect (avoid per-frame import)
from colorsys import hsv_to_rgb as _hsv_to_rgb


class CelebrationCard(QtWidgets.QFrame):
    """
    Epic celebration card displayed when a theme is fully completed.
    
    Features:
    - Animated SVG background (theme-specific)
    - Chirpy sound on click
    - Pulsing rainbow border glow
    - Floating sparkle particles
    - Shimmer sweep effects
    - Grand visual presentation (wider than entity cards)
    
    This is the CONGRATULATIONS card that rewards theme mastery.
    """
    
    # Note: __slots__ not used here - Qt widgets require __dict__ for signal/slot system
    # and dynamic property binding (glow_value property). Memory overhead is minimal
    # since only one CelebrationCard exists per completed theme (max 5 total).
    
    clicked = QtCore.Signal(str)  # Emits theme_id when clicked
    
    def __init__(self, theme_id: str, parent=None):
        super().__init__(parent)
        self.theme_id = theme_id
        self.celebration = get_theme_celebration(theme_id)
        
        # Initialize all animation state attributes first (needed for pause/resume calls)
        self._glow_animation = None
        self._glow_value = 0.0
        self._shimmer_timer = None
        self._shimmer_pos = -100
        self._shimmer_widget = None
        self._particle_labels = []
        self._animations_paused = False
        self._svg_widget = None  # Track for animation lifecycle
        self._last_border_color = None  # Cache to avoid redundant stylesheet updates
        self._last_click_time = 0.0  # Cooldown: prevent spam clicking
        
        if not self.celebration:
            _logger.warning("No celebration data for theme: %s", theme_id)
            return
        
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)
        self.setLineWidth(3)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setFixedSize(400, 360)  # Wider & taller for full SVG visibility
        
        self._build_ui()
        self._start_animations()
        
    def _build_ui(self):
        """Build the celebration card UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Title banner with gradient
        title_label = QtWidgets.QLabel("🎉 THEME COMPLETE! 🎉")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setFont(QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold))
        title_label.setStyleSheet("""
            color: #FFD700;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255,215,0,30), stop:0.5 rgba(255,255,255,50), stop:1 rgba(255,215,0,30));
            border-radius: 8px;
            padding: 5px;
        """)
        layout.addWidget(title_label)
        
        # SVG container with animation
        svg_container = QtWidgets.QWidget()
        svg_layout = QtWidgets.QHBoxLayout(svg_container)
        svg_layout.setContentsMargins(0, 0, 0, 0)
        svg_layout.addStretch()
        
        # Load celebration SVG
        svg_path = CELEBRATION_ICONS_PATH / self.celebration.svg_filename
        if svg_path.exists() and HAS_WEBENGINE:
            svg_widget = AnimatedSvgWidget(str(svg_path), svg_container)
            svg_widget.setFixedSize(150, 150)
            self._svg_widget = svg_widget  # Track for animation lifecycle
        elif svg_path.exists():
            svg_widget = QSvgWidget(str(svg_path), svg_container)
            svg_widget.setFixedSize(150, 150)
        else:
            # Placeholder emoji for missing SVG
            svg_widget = QtWidgets.QLabel("🏆")
            svg_widget.setAlignment(QtCore.Qt.AlignCenter)
            svg_widget.setFixedSize(150, 150)
            svg_widget.setStyleSheet("font-size: 80px; background: transparent;")
        
        svg_layout.addWidget(svg_widget)
        svg_layout.addStretch()
        layout.addWidget(svg_container)
        
        # Theme-specific title
        theme_title = QtWidgets.QLabel(self.celebration.title)
        theme_title.setAlignment(QtCore.Qt.AlignCenter)
        theme_title.setFont(QtGui.QFont("Segoe UI", 14, QtGui.QFont.Bold))
        primary_color = self.celebration.accent_color
        theme_title.setStyleSheet(f"color: {primary_color}; background: transparent;")
        layout.addWidget(theme_title)
        
        # Subtitle
        subtitle = QtWidgets.QLabel(self.celebration.subtitle)
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        subtitle.setFont(QtGui.QFont("Segoe UI", 10))
        subtitle.setStyleSheet("color: #AAAAAA; background: transparent;")
        layout.addWidget(subtitle)
        
        # Description
        desc_label = QtWidgets.QLabel(self.celebration.description)
        desc_label.setAlignment(QtCore.Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setFont(QtGui.QFont("Segoe UI", 9))
        desc_label.setStyleSheet("color: #888888; background: transparent; font-style: italic;")
        layout.addWidget(desc_label)
        
        # Click hint
        click_hint = QtWidgets.QLabel("🔊 Click for celebration fanfare!")
        click_hint.setAlignment(QtCore.Qt.AlignCenter)
        click_hint.setFont(QtGui.QFont("Segoe UI", 8))
        click_hint.setStyleSheet("color: #666666; background: transparent;")
        layout.addWidget(click_hint)
        
        # Add floating particles
        self._create_particle_decorations()
        
        # Create shimmer overlay
        self._create_shimmer_overlay()
        
        # Set initial style
        self._update_style()
        
    def _create_particle_decorations(self):
        """Create floating particle decorations around the card."""
        particle_chars = ["✨", "⭐", "💫", "🌟", "✦", "❋"]
        positions = [
            (20, 20), (370, 20), (10, 130), (380, 130),
            (30, 250), (360, 250), (190, 10), (190, 260)
        ]
        
        for i, (x, y) in enumerate(positions):
            particle = QtWidgets.QLabel(particle_chars[i % len(particle_chars)], self)
            particle.setStyleSheet("font-size: 16px; background: transparent;")
            particle.move(x, y)
            particle.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            self._particle_labels.append(particle)
    
    def _create_shimmer_overlay(self):
        """Create golden shimmer sweep effect."""
        self._shimmer_widget = QtWidgets.QWidget(self)
        self._shimmer_widget.setFixedSize(400, 280)
        self._shimmer_widget.move(0, 0)
        self._shimmer_widget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self._shimmer_widget.setStyleSheet("background: transparent;")
        self._shimmer_widget.lower()
    
    def _start_animations(self):
        """Start all celebration animations."""
        # Pulsing glow animation
        self._glow_animation = QtCore.QPropertyAnimation(self, b"glow_value")
        self._glow_animation.setDuration(2500)  # Slower for epic effect
        self._glow_animation.setStartValue(0.0)
        self._glow_animation.setEndValue(1.0)
        self._glow_animation.setLoopCount(-1)
        self._glow_animation.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        self._glow_animation.start()
        
        # Shimmer timer
        self._shimmer_timer = QtCore.QTimer(self)
        self._shimmer_timer.timeout.connect(self._update_shimmer)
        self._shimmer_timer.start(40)  # 25 FPS
    
    def _update_shimmer(self):
        """Update shimmer and particle positions."""
        if not self._shimmer_widget:
            return
        
        # Move shimmer across card
        self._shimmer_pos += 4
        if self._shimmer_pos > 500:
            self._shimmer_pos = -100
        
        pos_pct = max(0, min(100, int((self._shimmer_pos / 400) * 100)))
        
        self._shimmer_widget.setStyleSheet(f"""
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0.3,
                stop: {max(0, pos_pct - 20) / 100:.2f} transparent,
                stop: {pos_pct / 100:.2f} rgba(255, 215, 0, 60),
                stop: {min(100, pos_pct + 20) / 100:.2f} transparent
            );
        """)
        
        # Animate particles
        self._update_particles()
    
    def _update_particles(self):
        """Animate floating particles with oscillating motion."""
        positions = [
            (20, 20), (370, 20), (10, 130), (380, 130),
            (30, 250), (360, 250), (190, 10), (190, 260)
        ]
        
        for i, particle in enumerate(self._particle_labels):
            phase = (self._glow_value * math.pi * 2) + (i * math.pi / 4)
            base_x, base_y = positions[i % len(positions)]
            offset_x = math.sin(phase) * 10
            offset_y = math.cos(phase) * 10
            
            opacity = 0.6 + 0.4 * math.sin(phase + math.pi / 2)
            size = 14 + int(4 * math.sin(phase))
            
            particle.move(int(base_x + offset_x), int(base_y + offset_y))
            particle.setStyleSheet(f"font-size: {size}px; background: transparent; opacity: {opacity};")
    
    def _get_glow_value(self):
        return self._glow_value
    
    def _set_glow_value(self, value):
        self._glow_value = value
        self._update_style()
    
    glow_value = QtCore.Property(float, _get_glow_value, _set_glow_value)
    
    def _update_style(self):
        """Update card style with animated rainbow border.
        
        Optimization: Only updates stylesheet when border color actually changes,
        and uses module-level cached import for hsv_to_rgb.
        """
        if not self.celebration:
            return
        
        # Rainbow hue cycling based on glow value
        hue = int(self._glow_value * 360)
        
        # Create HSV color for border using cached import
        r, g, b = _hsv_to_rgb(hue / 360.0, 0.7, 1.0)
        border_color = f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"
        
        # Skip update if border color hasn't changed (avoid redundant style recomputation)
        if border_color == self._last_border_color:
            return
        self._last_border_color = border_color
        
        self.setStyleSheet(f"""
            CelebrationCard {{
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.9,
                    fx: 0.5, fy: 0.5,
                    stop: 0 #1A1A2E,
                    stop: 0.7 #0D0D1A,
                    stop: 1 #050510
                );
                border: 3px solid {border_color};
                border-radius: 16px;
            }}
        """)
        
        # Note: _update_particles() is called from _update_shimmer() timer,
        # no need to call it here (was causing redundant updates)
    
    def mousePressEvent(self, event):
        """Handle click - play celebration sound and speak the celebration quote.
        
        Milestone rewards:
        - Clicks 1-20: Cycle through 20 unique celebration quotes
        - Click 7: +7 coins for curiosity
        - Click 20: Sarcastic message about giving up
        - Click 21: +1 coin for irrational persistence
        - Click 22: +22 coins with formal addiction agreement
        - Click 23+: Same agreement, no coins
        
        Cooldown: 20 seconds between clicks to let music and TTS finish.
        """
        import time
        CLICK_COOLDOWN = 20.0  # Seconds between allowed clicks
        
        if event.button() == QtCore.Qt.LeftButton:
            # Enforce cooldown to let music and TTS finish
            current_time = time.time()
            if current_time - self._last_click_time < CLICK_COOLDOWN:
                remaining = int(CLICK_COOLDOWN - (current_time - self._last_click_time))
                _logger.debug("Celebration click cooldown: %d seconds remaining", remaining)
                super().mousePressEvent(event)
                return
            self._last_click_time = current_time
            
            # Guard: celebration data must exist
            if not self.celebration:
                _logger.warning("No celebration data for theme: %s", self.theme_id)
                super().mousePressEvent(event)
                return
            
            # Play celebration sound (synthesized music/fanfare)
            play_celebration_sound(self.theme_id)
            
            # Get click count from parent EntitidexTab
            click_count = self._increment_click_count()
            
            # Determine what quote/message to speak and rewards to give
            # We use separate quote_index tracking so milestone clicks don't skip quotes
            quote_to_speak = None
            coins_awarded = 0
            is_milestone = False  # Track if this is a milestone (no quote shown)
            
            if click_count == 7:
                # Curiosity reward milestone
                quote_to_speak = self.celebration.curiosity_message or None
                coins_awarded = 7 if quote_to_speak else 0  # Only award if message exists
                is_milestone = True
            elif click_count == 20:
                # Sarcastic "give up" message
                quote_to_speak = self.celebration.resignation_message or None
                is_milestone = True
            elif click_count == 21:
                # Irrational persistence reward
                quote_to_speak = self.celebration.persistence_message or None
                coins_awarded = 1 if quote_to_speak else 0
                is_milestone = True
            elif click_count == 22:
                # Final reward with addiction agreement
                quote_to_speak = self.celebration.addiction_agreement or None
                coins_awarded = 22 if quote_to_speak else 0
                is_milestone = True
            elif click_count >= 23:
                # Same agreement, no coins
                quote_to_speak = self.celebration.addiction_agreement or None
                is_milestone = True
            elif self.celebration.celebration_quotes:
                # Use separate quote index that increments only for normal quotes
                quote_index = self._get_and_increment_quote_index()
                quote_to_speak = self.celebration.celebration_quotes[quote_index]
            
            # Award coins if earned
            if coins_awarded > 0:
                self._award_coins(coins_awarded, click_count)
            
            # Show quote dialog and speak after music finishes
            if quote_to_speak:
                self._show_quote_dialog(quote_to_speak, coins_awarded, is_milestone)
            
            self.clicked.emit(self.theme_id)
        super().mousePressEvent(event)
    
    def _show_quote_dialog(self, quote: str, coins_awarded: int, is_milestone: bool):
        """Show a dialog with the celebration quote and speak it after music.
        
        Args:
            quote: The quote text to display and speak
            coins_awarded: Coins earned (shown in dialog if > 0)
            is_milestone: Whether this is a milestone message
        """
        from PySide6 import QtWidgets, QtCore, QtGui
        
        # Create frameless dialog (no title bar)
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Dialog)
        dialog.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        dialog.setModal(False)  # Non-blocking
        dialog.setMinimumWidth(420)
        dialog.setMaximumWidth(500)
        
        # Style the dialog
        dialog.setStyleSheet("""
            QDialog {
                background: transparent;
            }
            QFrame#dialogFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1A1A2E, stop:1 #0D0D1A);
                border: 2px solid #FFD700;
                border-radius: 16px;
            }
            QLabel {
                color: #E0E0E0;
                background: transparent;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4A4A6A, stop:1 #2A2A4A);
                color: #FFD700;
                border: 1px solid #FFD700;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5A5A7A, stop:1 #3A3A5A);
            }
        """)
        
        # Outer layout for the dialog
        outer_layout = QtWidgets.QVBoxLayout(dialog)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main frame that holds content (this gets the border/background)
        frame = QtWidgets.QFrame()
        frame.setObjectName("dialogFrame")
        outer_layout.addWidget(frame)
        
        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        # Header with emoji
        header_text = "🎉 Celebration! 🎉" if not is_milestone else "🏆 Milestone! 🏆"
        header_label = QtWidgets.QLabel(header_text)
        header_label.setAlignment(QtCore.Qt.AlignCenter)
        header_label.setFont(QtGui.QFont("Segoe UI", 14, QtGui.QFont.Bold))
        header_label.setStyleSheet("color: #FFD700; padding-bottom: 5px;")
        layout.addWidget(header_label)
        
        # Quote text with word wrap
        quote_label = QtWidgets.QLabel(quote)
        quote_label.setWordWrap(True)
        quote_label.setAlignment(QtCore.Qt.AlignCenter)
        quote_label.setFont(QtGui.QFont("Segoe UI", 12))
        quote_label.setStyleSheet("color: #FFFFFF; padding: 10px;")
        layout.addWidget(quote_label)
        
        # Show coins if awarded
        if coins_awarded > 0:
            coins_label = QtWidgets.QLabel(f"🪙 +{coins_awarded} coins!")
            coins_label.setAlignment(QtCore.Qt.AlignCenter)
            coins_label.setFont(QtGui.QFont("Segoe UI", 14, QtGui.QFont.Bold))
            coins_label.setStyleSheet("color: #FFD700;")
            layout.addWidget(coins_label)
        
        # OK button
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QtWidgets.QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Voice toggle checkbox
        voice_enabled = self._get_voice_enabled()
        mute_checkbox = QtWidgets.QCheckBox("🔇 Mute the narrator (I can read!)")
        mute_checkbox.setChecked(not voice_enabled)
        mute_checkbox.setStyleSheet("""
            QCheckBox {
                color: #888888;
                font-size: 10px;
                padding-top: 10px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #666;
                background: #2A2A4A;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #FFD700;
                background: #4A4A6A;
                border-radius: 3px;
            }
        """)
        
        def on_mute_changed(checked):
            self._set_voice_enabled(not checked)
        
        mute_checkbox.stateChanged.connect(on_mute_changed)
        layout.addWidget(mute_checkbox, alignment=QtCore.Qt.AlignCenter)
        
        # Show dialog (non-blocking)
        dialog.show()
        
        # Speak the quote after music finishes (delay ~3 seconds) - only if voice enabled
        def speak_quote():
            if not self._get_voice_enabled():
                return  # Voice muted
            try:
                from eye_protection_tab import GuidanceManager
                guidance = GuidanceManager.get_instance()
                if guidance and guidance.piper_voice:
                    guidance.say(quote)
            except Exception as e:
                _logger.debug("Failed to speak celebration quote: %s", e)
        
        QtCore.QTimer.singleShot(3000, speak_quote)  # 3 second delay for music
    
    def _get_voice_enabled(self) -> bool:
        """Get whether celebration voice is enabled from parent progress."""
        parent = self.parent()
        max_depth = 20
        depth = 0
        while parent and depth < max_depth:
            if hasattr(parent, 'progress') and hasattr(parent.progress, 'celebration_voice_enabled'):
                return parent.progress.celebration_voice_enabled
            parent = parent.parent()
            depth += 1
        return True  # Default enabled
    
    def _set_voice_enabled(self, enabled: bool) -> None:
        """Set celebration voice enabled and save."""
        parent = self.parent()
        max_depth = 20
        depth = 0
        while parent and depth < max_depth:
            if hasattr(parent, 'progress') and hasattr(parent.progress, 'celebration_voice_enabled'):
                parent.progress.celebration_voice_enabled = enabled
                if hasattr(parent, '_save_progress'):
                    try:
                        parent._save_progress()
                    except Exception as e:
                        _logger.debug("Failed to save voice preference: %s", e)
                return
            parent = parent.parent()
            depth += 1
    
    def _increment_click_count(self) -> int:
        """Increment and return the click count for this theme's celebration card.
        
        Persists via the parent EntitidexTab's progress tracker.
        Returns click count (1 as fallback if parent not found).
        """
        # Find parent with progress tracker (EntitidexTab)
        # Use hasattr check since EntitidexTab is defined after CelebrationCard
        parent = self.parent()
        max_depth = 20  # Prevent infinite loop
        depth = 0
        while parent and depth < max_depth:
            if hasattr(parent, 'progress') and hasattr(parent.progress, 'celebration_clicks'):
                break
            parent = parent.parent()
            depth += 1
        
        if parent and hasattr(parent, 'progress'):
            try:
                if self.theme_id not in parent.progress.celebration_clicks:
                    parent.progress.celebration_clicks[self.theme_id] = 0
                parent.progress.celebration_clicks[self.theme_id] += 1
                # Save progress (non-critical, wrapped in try)
                if hasattr(parent, '_save_progress'):
                    try:
                        parent._save_progress()
                    except Exception as e:
                        _logger.debug("Failed to save celebration click progress: %s", e)
                return parent.progress.celebration_clicks[self.theme_id]
            except Exception as e:
                _logger.warning("Error incrementing celebration clicks: %s", e)
                return 1
        
        _logger.debug("Parent EntitidexTab not found for theme: %s", self.theme_id)
        return 1  # Fallback
    
    def _get_and_increment_quote_index(self) -> int:
        """Get current quote index and increment for next time.
        
        This is separate from click_count so milestone clicks (7, 20, 21, 22, 23+)
        don't cause quotes to be skipped.
        
        Returns:
            Quote index (0 to len(quotes)-1), wrapping around cyclically.
        """
        # Find parent with progress tracker (EntitidexTab)
        parent = self.parent()
        max_depth = 20
        depth = 0
        while parent and depth < max_depth:
            if hasattr(parent, 'progress') and hasattr(parent.progress, 'celebration_quote_index'):
                break
            parent = parent.parent()
            depth += 1
        
        num_quotes = len(self.celebration.celebration_quotes) if self.celebration.celebration_quotes else 1
        
        if parent and hasattr(parent, 'progress'):
            try:
                if self.theme_id not in parent.progress.celebration_quote_index:
                    parent.progress.celebration_quote_index[self.theme_id] = 0
                
                # Get current index
                current_idx = parent.progress.celebration_quote_index[self.theme_id] % num_quotes
                
                # Increment for next time (wraps automatically when we use modulo on get)
                parent.progress.celebration_quote_index[self.theme_id] = (current_idx + 1) % num_quotes
                
                # Save progress (non-critical)
                if hasattr(parent, '_save_progress'):
                    try:
                        parent._save_progress()
                    except Exception as e:
                        _logger.debug("Failed to save quote index progress: %s", e)
                
                return current_idx
            except Exception as e:
                _logger.warning("Error getting quote index: %s", e)
                return 0
        
        _logger.debug("Parent EntitidexTab not found for quote index: %s", self.theme_id)
        return 0  # Fallback
    
    def _award_coins(self, amount: int, click_count: int) -> None:
        """Award coins to the user for milestone achievements.
        
        Args:
            amount: Number of coins to award
            click_count: Which click milestone this is for (7, 21, or 22)
        """
        # Find parent with blocker (EntitidexTab)
        parent = self.parent()
        max_depth = 20  # Prevent infinite loop
        depth = 0
        while parent and depth < max_depth:
            if hasattr(parent, 'blocker') and hasattr(parent, 'progress'):
                break
            parent = parent.parent()
            depth += 1
        
        if not parent or not hasattr(parent, 'blocker'):
            _logger.debug("Parent blocker not found for coin award (theme: %s)", self.theme_id)
            return
        
        if not hasattr(parent.blocker, 'adhd_buster') or parent.blocker.adhd_buster is None:
            _logger.debug("adhd_buster not available for coin award")
            return
        
        try:
            adhd_buster = parent.blocker.adhd_buster
            current_coins = adhd_buster.get("coins", 0)
            adhd_buster["coins"] = current_coins + amount
            parent.blocker.save_config()
            
            # Log notification
            reason = {
                7: f"🔍 Curiosity Rewarded! +{amount} coins",
                21: f"🎯 Irrational Persistence! +{amount} coin",
                22: f"📜 Final Agreement Signed! +{amount} coins",
            }.get(click_count, f"+{amount} coins")
            
            _logger.info("Celebration milestone: %s (theme: %s)", reason, self.theme_id)
        except Exception as e:
            _logger.warning("Failed to award celebration coins: %s", e)
    
    def pause_animations(self):
        """Pause animations when card is not visible."""
        if self._animations_paused:
            return
        self._animations_paused = True
        
        if self._glow_animation and self._glow_animation.state() == QtCore.QAbstractAnimation.Running:
            self._glow_animation.pause()
        
        if self._shimmer_timer and self._shimmer_timer.isActive():
            self._shimmer_timer.stop()
        
        # Pause SVG animations if using AnimatedSvgWidget
        if self._svg_widget and isinstance(self._svg_widget, AnimatedSvgWidget):
            self._svg_widget.stop_animations()
    
    def resume_animations(self):
        """Resume animations when card becomes visible."""
        if not self._animations_paused:
            return
        self._animations_paused = False
        
        if self._glow_animation and self._glow_animation.state() == QtCore.QAbstractAnimation.Paused:
            self._glow_animation.resume()
        
        if self._shimmer_timer and not self._shimmer_timer.isActive():
            self._shimmer_timer.start(40)
        
        # Resume SVG animations if using AnimatedSvgWidget
        if self._svg_widget and isinstance(self._svg_widget, AnimatedSvgWidget):
            self._svg_widget.restart_animations()


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
        self._celebration_cards: list = []  # List[CelebrationCard]
        self._is_visible = False
        self._initialized = False  # Lazy init flag
        self._current_theme_index = 0  # Track current theme tab
        
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
        for card in self._celebration_cards:
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
        
        # Resume all card animations (only for current theme tab)
        # Guard: theme_tabs may be empty if _build_ui hasn't run yet
        if not self.theme_tabs:
            return
        
        theme_keys = list(THEME_INFO.keys())
        current_theme = theme_keys[self._current_theme_index] if self._current_theme_index < len(theme_keys) else None
        
        if current_theme:
            current_container = self.theme_tabs.get(current_theme)
            if current_container:
                for card in self._all_cards:
                    # Check if card belongs to current theme container
                    parent = card.parent()
                    while parent and parent != current_container:
                        parent = parent.parent()
                    if parent == current_container:
                        card.resume_animations()
                # Resume celebration cards on current theme
                for card in self._celebration_cards:
                    if hasattr(card, 'theme_id') and card.theme_id == current_theme:
                        card.resume_animations()
    
    def hideEvent(self, event: QtGui.QHideEvent) -> None:
        """Called when tab is hidden - pause animations to save resources."""
        super().hideEvent(event)
        self._is_visible = False
        
        # Pause all card animations to save CPU
        for card in self._all_cards:
            card.pause_animations()
        # Pause all celebration card animations
        for card in self._celebration_cards:
            card.pause_animations()
    
    def on_window_minimized(self) -> None:
        """Called by parent window when app is minimized - ensures all animations pause.
        
        This provides explicit minimize handling in case Qt's hideEvent doesn't
        propagate to nested tab widgets. Useful for system tray minimization.
        """
        if not self._is_visible:
            return  # Already paused
        self._is_visible = False
        
        for card in self._all_cards:
            card.pause_animations()
        for card in self._celebration_cards:
            card.pause_animations()
    
    def on_window_restored(self) -> None:
        """Called by parent window when app is restored from minimize/tray.
        
        Resumes animations only for the currently visible theme tab.
        """
        if self._is_visible:
            return  # Already running
        self._is_visible = True
        
        if not self._initialized:
            return  # Not yet built
        
        # Only resume animations for the currently visible theme tab
        theme_keys = list(THEME_INFO.keys())
        current_theme = theme_keys[self._current_theme_index] if self._current_theme_index < len(theme_keys) else None
        
        if current_theme:
            current_container = self.theme_tabs.get(current_theme)
            if current_container:
                for card in self._all_cards:
                    # Check if card belongs to current theme container
                    parent = card.parent()
                    while parent and parent != current_container:
                        parent = parent.parent()
                    if parent == current_container:
                        card.resume_animations()
                # Resume celebration cards on current theme
                for card in self._celebration_cards:
                    if hasattr(card, 'theme_id') and card.theme_id == current_theme:
                        card.resume_animations()
    
    def _pause_all_animations(self) -> None:
        """Explicitly pause ALL animations when tab is not visible.
        
        Called by MainWindow._on_tab_changed when switching away from Entitidex.
        This is critical for performance - shimmer timers run at 50ms intervals
        and glow animations run continuously, consuming CPU even when hidden.
        """
        if not self._initialized:
            return
        self._is_visible = False
        
        for card in self._all_cards:
            card.pause_animations()
        for card in self._celebration_cards:
            card.pause_animations()
    
    def _resume_all_animations(self) -> None:
        """Explicitly resume animations when switching TO this tab.
        
        Called by MainWindow._on_tab_changed when Entitidex tab becomes active.
        Only resumes animations for cards in the currently visible theme sub-tab.
        """
        if not self._initialized:
            return
        self._is_visible = True
        
        # Only resume animations for the currently visible theme tab
        if not self.theme_tabs:
            return
            
        theme_keys = list(THEME_INFO.keys())
        current_theme = theme_keys[self._current_theme_index] if self._current_theme_index < len(theme_keys) else None
        
        if current_theme:
            current_container = self.theme_tabs.get(current_theme)
            if current_container:
                for card in self._all_cards:
                    # Check if card belongs to current theme container
                    parent = card.parent()
                    while parent and parent != current_container:
                        parent = parent.parent()
                    if parent == current_container:
                        card.resume_animations()
                # Resume celebration cards on current theme
                for card in self._celebration_cards:
                    if hasattr(card, 'theme_id') and card.theme_id == current_theme:
                        card.resume_animations()

    def _load_progress(self):
        """Load entitidex progress from blocker config."""
        try:
            if hasattr(self.blocker, 'adhd_buster'):
                entitidex_data = self.blocker.adhd_buster.get("entitidex", {})
                # ALWAYS reset progress from data - even if empty dict
                # This prevents data leak between users when switching profiles
                # (empty dict means new user with no entities, not "keep old data")
                self.progress = EntitidexProgress.from_dict(entitidex_data) if entitidex_data else EntitidexProgress()
            else:
                # No adhd_buster - start with fresh progress
                self.progress = EntitidexProgress()
        except Exception:
            _logger.exception("Error loading entitidex progress")
            # On error, reset to empty to prevent data corruption
            self.progress = EntitidexProgress()
    
    def _save_progress(self):
        """Save entitidex progress to blocker config."""
        try:
            if hasattr(self.blocker, 'adhd_buster'):
                # Use to_dict() to save ALL fields including failed_catches, captures, stats
                self.blocker.adhd_buster["entitidex"] = self.progress.to_dict()
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
                color: #c4b5fd;
            }
        """)
        header_layout.addWidget(title)
        
        # Add Active Perks "Badge"
        self.perks_button = QtWidgets.QPushButton("✨ Active Perks")
        self.perks_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.perks_button.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: #E6E6FA;
                border: 1px solid #9370DB;
                padding: 4px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6A5ACD;
                border-color: #ffffff;
            }
        """)
        self.perks_button.clicked.connect(self._show_perks_summary)
        header_layout.addWidget(self.perks_button)
        
        # Add Saved Encounters button
        self.saved_button = QtWidgets.QPushButton("📦 Saved Encounters (0)")
        self.saved_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.saved_button.setToolTip(
            "View and open your saved encounters!\n\n"
            "Encounters saved during focus sessions\n"
            "can be opened here anytime."
        )
        self.saved_button.setStyleSheet("""
            QPushButton {
                background-color: #2e5d2e;
                color: #E6E6FA;
                border: 1px solid #4CAF50;
                padding: 4px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3e7d3e;
                border-color: #ffffff;
            }
        """)
        self.saved_button.clicked.connect(self._show_saved_encounters)
        header_layout.addWidget(self.saved_button)
        
        header_layout.addStretch()
        
        # Overall progress label
        self.total_progress_label = QtWidgets.QLabel()
        self.total_progress_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        header_layout.addWidget(self.total_progress_label)
        
        layout.addLayout(header_layout)

        add_tab_help_button(layout, "entitidex", self)
        
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
        
        # Connect theme tab changes to pause/resume animations on hidden/visible tabs
        self.theme_tab_widget.currentChanged.connect(self._on_theme_tab_changed)
        
        # Note: Entity info is now shown via hover tooltips on cards (cleaner UX)
        
        # Load initial data
        self._refresh_all_tabs()
        self._update_saved_button_count()
    
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
    
    def _create_entity_pair_widget(self, entity: Entity, theme_key: str = None) -> QtWidgets.QWidget:
        """Create a widget containing both normal and exceptional cards for an entity.
        
        Args:
            entity: The entity to create cards for
            theme_key: The theme this entity belongs to (for animation lifecycle)
        """
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
        
        # Determine if cards should start paused
        # Pause if: 1) Entitidex tab is hidden, OR 2) This is not the current theme tab
        should_pause = not self._is_visible
        if theme_key and self._is_visible:
            theme_keys = list(THEME_INFO.keys())
            current_theme_key = theme_keys[self._current_theme_index] if self._current_theme_index < len(theme_keys) else None
            if theme_key != current_theme_key:
                should_pause = True
        
        if should_pause:
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
        
        # Cleanup: Remove old celebration cards for this theme
        celebration_cards_to_remove = []
        for card in self._celebration_cards:
            if hasattr(card, 'theme_id') and card.theme_id == theme_key:
                card.pause_animations()  # Stop animations before deletion
                celebration_cards_to_remove.append(card)
        for card in celebration_cards_to_remove:
            self._celebration_cards.remove(card)
        
        # Clear existing cards
        while cards_layout.count():
            child = cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Get entities for this theme
        entities = get_entities_for_story(theme_key)
        entities_sorted = sorted(entities, key=lambda e: e.power)
        
        # Calculate progress - count normal and exceptional separately
        # You can collect each variant independently!
        collected_normal = 0
        collected_exceptional = 0
        encountered_count = 0
        
        for entity in entities_sorted:
            # Check normal collection
            if self.progress.is_collected(entity.id):
                collected_normal += 1
            # Check exceptional collection (independent of normal!)
            if self.progress.is_exceptional(entity.id):
                collected_exceptional += 1
            # Encountered but not collected either way
            if not self.progress.is_collected(entity.id) and not self.progress.is_exceptional(entity.id):
                if self.progress.is_encountered(entity.id):
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
        
        # =====================================================================
        # THEME COMPLETION CELEBRATION CARD
        # Show epic celebration card at top when theme is 100% complete
        # =====================================================================
        current_row = 0
        
        # Check if theme is fully complete (all normal + all exceptional)
        if self.progress.is_theme_fully_complete(theme_key):
            # Record completion if not already recorded
            if theme_key not in self.progress.theme_completions:
                self.progress.record_theme_completion(theme_key)
                self._save_progress()
            
            # Create and add the celebration card
            celebration_card = CelebrationCard(theme_key, cards_container)
            if celebration_card.celebration:  # Only add if valid
                cards_layout.addWidget(celebration_card, current_row, 0, 1, 1, QtCore.Qt.AlignCenter)
                # Register for lifecycle management (pause/resume)
                self._celebration_cards.append(celebration_card)
                # Start paused if tab not visible or this isn't the current theme
                theme_keys = list(THEME_INFO.keys())
                if not self._is_visible or theme_keys.index(theme_key) != self._current_theme_index:
                    celebration_card.pause_animations()
                current_row += 1
                
                # Add separator line below celebration
                separator = QtWidgets.QFrame()
                separator.setFrameShape(QtWidgets.QFrame.HLine)
                separator.setStyleSheet("background-color: #444444; margin: 10px 50px;")
                separator.setFixedHeight(2)
                cards_layout.addWidget(separator, current_row, 0, 1, 1, QtCore.Qt.AlignCenter)
                current_row += 1
        
        # Create paired cards - Layout: Each entity gets [Normal | Exceptional] pair
        # Sort by rarity for proper grouping
        rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}
        entities_by_rarity = sorted(entities_sorted, key=lambda e: rarity_order.get(e.rarity.lower(), 0))
        
        # Separate legendary from others
        legendary = [e for e in entities_by_rarity if e.rarity.lower() == "legendary"]
        others = [e for e in entities_by_rarity if e.rarity.lower() != "legendary"]
        
        # Layout grid with paired cards (each pair is wider, so 2 pairs per row)
        # Row 0: Celebration card (if theme complete) + separator
        # Row N: Legendary pair centered
        # Row N+1-2: Epic pairs
        # Row N+3-4: Rare pairs  
        # Row N+5-6: Uncommon pairs
        # Row N+7-8: Common pairs
        
        # Add legendary at top center
        for entity in legendary:
            pair_widget = self._create_entity_pair_widget(entity, theme_key)
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
                pair_widget = self._create_entity_pair_widget(entity, theme_key)
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

    def _on_theme_tab_changed(self, index: int) -> None:
        """Handle theme tab changes - pause animations on hidden tabs, resume on visible.
        
        Performance optimization: Only run animations for the currently visible theme tab.
        This can save significant CPU when many entity cards have active animations.
        """
        theme_keys = list(THEME_INFO.keys())
        old_theme = theme_keys[self._current_theme_index] if self._current_theme_index < len(theme_keys) else None
        new_theme = theme_keys[index] if index < len(theme_keys) else None
        self._current_theme_index = index
        
        if not self._is_visible:
            return  # Tab not visible, all animations already paused
        
        # Pause animations on cards belonging to the old theme
        if old_theme:
            old_container = self.theme_tabs.get(old_theme)
            if old_container:
                for card in self._all_cards:
                    # Check if card belongs to old theme container
                    parent = card.parent()
                    while parent and parent != old_container:
                        parent = parent.parent()
                    if parent == old_container:
                        card.pause_animations()
                # Pause celebration cards on old theme
                for card in self._celebration_cards:
                    if hasattr(card, 'theme_id') and card.theme_id == old_theme:
                        card.pause_animations()
        
        # Resume animations on cards belonging to the new theme
        if new_theme:
            new_container = self.theme_tabs.get(new_theme)
            if new_container:
                for card in self._all_cards:
                    # Check if card belongs to new theme container
                    parent = card.parent()
                    while parent and parent != new_container:
                        parent = parent.parent()
                    if parent == new_container:
                        card.resume_animations()
                # Resume celebration cards on new theme
                for card in self._celebration_cards:
                    if hasattr(card, 'theme_id') and card.theme_id == new_theme:
                        card.resume_animations()

    def _show_perks_summary(self):
        """Show a dialog listing all active entity perks in a table format."""
        from entitidex.entity_perks import ENTITY_PERKS, PerkType
        from entitidex.entity_pools import get_entity_by_id
        
        active_perks = calculate_active_perks(self.progress)
        
        if not active_perks:
            styled_info(self, "No Active Perks", 
                "Collect entities to unlock passive perks!<br><br>"
                "Each collected entity grants a bonus to power, coins, XP, or luck.")
            return

        # Build contributor mapping: perk_type -> list of (entity_id, value, is_exceptional)
        # When you have BOTH normal AND exceptional, they both contribute
        perk_contributors: dict = {}
        collected = self.progress.collected_entity_ids or set()
        exceptional = self.progress.exceptional_entities or {}
        exceptional_ids = set(exceptional.keys()) if isinstance(exceptional, dict) else set(exceptional)
        
        # Get all unique entity IDs from both collections
        all_entity_ids = collected | exceptional_ids
        
        for entity_id in all_entity_ids:
            perks = ENTITY_PERKS.get(entity_id)
            if perks:
                has_normal = entity_id in collected
                has_exceptional = entity_id in exceptional_ids
                
                for perk in perks:
                    if perk.perk_type not in perk_contributors:
                        perk_contributors[perk.perk_type] = []
                    
                    # Add normal variant contribution
                    if has_normal:
                        perk_contributors[perk.perk_type].append((entity_id, perk.normal_value, False))
                    
                    # Add exceptional variant contribution (stacks!)
                    if has_exceptional:
                        perk_contributors[perk.perk_type].append((entity_id, perk.exceptional_value, True))

        # Create dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("✨ Active Perks")
        dialog.setMinimumSize(520, 400)
        dialog.setMaximumSize(700, 600)
        dialog.setStyleSheet("""
            QDialog { background-color: #1a1a2e; }
            QLabel { color: #E6E6FA; }
            QTableWidget {
                background-color: #16213e;
                color: #E6E6FA;
                gridline-color: #0f3460;
                border: 1px solid #0f3460;
                border-radius: 4px;
            }
            QTableWidget::item { padding: 4px; }
            QHeaderView::section {
                background-color: #0f3460;
                color: #E6E6FA;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0f3460;
                color: #E6E6FA;
                border: 1px solid #4CAF50;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #1a4a7a; }
        """)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setSpacing(10)
        
        # Header
        header = QtWidgets.QLabel("<h2>✨ Active Entity Bonuses</h2>")
        header.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(header)
        
        # Perk descriptions mapping
        PERK_DESCRIPTIONS = {
            PerkType.POWER_FLAT: "Increases your Hero Power stat",
            PerkType.COIN_FLAT: "Bonus coins per session",
            PerkType.COIN_PERCENT: "Percentage boost to all coin gains",
            PerkType.COIN_DISCOUNT: "Reduces coin costs",
            PerkType.STORE_DISCOUNT: "Reduces store refresh cost",
            PerkType.SALVAGE_BONUS: "Bonus coins when salvaging items",
            PerkType.XP_PERCENT: "Percentage boost to all XP gains",
            PerkType.XP_SESSION: "Bonus XP from focus sessions",
            PerkType.XP_LONG_SESSION: "Bonus XP for sessions over 1 hour",
            PerkType.XP_NIGHT: "Bonus XP during night (8PM-6AM)",
            PerkType.XP_MORNING: "Bonus XP during morning (6AM-12PM)",
            PerkType.XP_STORY: "Bonus XP from story chapters",
            PerkType.MERGE_LUCK: "Increases merge success chance",
            PerkType.MERGE_SUCCESS: "Increases merge success rate",
            PerkType.DROP_LUCK: "Increases item drop chance",
            PerkType.ALL_LUCK: "Boosts all luck-related stats",
            PerkType.STREAK_SAVE: "Chance to save your streak",
            PerkType.ENCOUNTER_CHANCE: "Increases entity encounter rate",
            PerkType.CAPTURE_BONUS: "Increases capture probability",
            PerkType.RARITY_BIAS: "Higher chance for rare entities",
            PerkType.PITY_BONUS: "Faster pity system progress",
            PerkType.HYDRATION_COOLDOWN: "Reduces water reminder cooldown",
            PerkType.HYDRATION_CAP: "Increases daily hydration cap",
            PerkType.INVENTORY_SLOTS: "Extra inventory space",
            PerkType.EYE_REST_CAP: "Extra daily eye rest claims",
            PerkType.PERFECT_SESSION: "Bonus for distraction-free sessions",
            PerkType.EYE_TIER_BONUS: "Better eye routine rewards",
            PerkType.EYE_REROLL_CHANCE: "Retry on eye routine failure",
            PerkType.SLEEP_TIER_BONUS: "Better sleep rewards",
            PerkType.WEIGHT_LEGENDARY: "Legendary chance on weight log",
            PerkType.OPTIMIZE_GEAR_DISCOUNT: "Cheaper gear optimization",
            PerkType.SELL_RARITY_BONUS: "Better sell value for rares",
            PerkType.GAMBLE_LUCK: "Improved gamble success",
            PerkType.GAMBLE_SAFETY: "Chance to keep item on gamble fail",
        }
        
        # Create table
        table = QtWidgets.QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Perk", "Bonus", "Effect", "Contributors"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(table.styleSheet() + """
            QTableWidget { alternate-background-color: #1a2744; }
        """)
        
        # Sort perks and populate table
        sorted_keys = sorted(active_perks.keys(), key=lambda k: k.value)
        table.setRowCount(len([k for k in sorted_keys if active_perks[k] != 0]))
        
        row = 0
        for perk_type in sorted_keys:
            val = active_perks[perk_type]
            if val == 0:
                continue
            
            # Determine icon, name, and suffix
            icon = "🔹"
            name = perk_type.name.replace("_", " ").title()
            suffix = ""
            
            if "POWER" in perk_type.name: 
                icon = "💪"; name = "Hero Power"
            elif "XP" in perk_type.name: 
                icon = "📜"; suffix = "%"
            elif "COIN" in perk_type.name: 
                icon = "🪙"; suffix = "" if "FLAT" in perk_type.name else "%"
            elif "LUCK" in perk_type.name or "SUCCESS" in perk_type.name: 
                icon = "🍀"; suffix = "%"
            elif "HYDRATION" in perk_type.name:
                icon = "💧"; suffix = "m" if "COOLDOWN" in perk_type.name else ""
            elif "CAPTURE" in perk_type.name or "ENCOUNTER" in perk_type.name:
                icon = "🎯"; suffix = "%"
            elif "SALVAGE" in perk_type.name or "DISCOUNT" in perk_type.name:
                icon = "💰"
            elif "INVENTORY" in perk_type.name:
                icon = "🎒"
            elif "PERFECT" in perk_type.name:
                icon = "⭐"; suffix = "%"
            elif "GAMBLE" in perk_type.name:
                icon = "🎲"; suffix = "%"
            elif "RARITY" in perk_type.name or "PITY" in perk_type.name:
                icon = "✨"; suffix = "%"
            elif "EYE" in perk_type.name or "SLEEP" in perk_type.name:
                icon = "👁️"
            elif "STREAK" in perk_type.name:
                icon = "🔥"; suffix = "%"
            
            # Perk name cell
            perk_item = QtWidgets.QTableWidgetItem(f"{icon} {name}")
            perk_item.setToolTip(PERK_DESCRIPTIONS.get(perk_type, "Entity perk bonus"))
            table.setItem(row, 0, perk_item)
            
            # Bonus value cell
            bonus_text = f"+{val}{suffix}"
            bonus_item = QtWidgets.QTableWidgetItem(bonus_text)
            bonus_item.setTextAlignment(QtCore.Qt.AlignCenter)
            bonus_item.setForeground(QtGui.QColor("#4CAF50"))
            table.setItem(row, 1, bonus_item)
            
            # Effect description cell
            effect_text = PERK_DESCRIPTIONS.get(perk_type, "Entity perk bonus")
            effect_item = QtWidgets.QTableWidgetItem(effect_text)
            effect_item.setForeground(QtGui.QColor("#aaaaaa"))
            table.setItem(row, 2, effect_item)
            
            # Contributors cell
            contributors = perk_contributors.get(perk_type, [])
            contributor_names = []
            for entity_id, contrib_val, is_exc in contributors:
                entity = get_entity_by_id(entity_id)
                if entity:
                    if is_exc:
                        contributor_names.append(f"⭐{entity.name}")
                    else:
                        contributor_names.append(entity.name)
            
            # Show abbreviated if too many
            if len(contributor_names) > 3:
                display_text = f"{contributor_names[0]}, {contributor_names[1]}... +{len(contributor_names)-2}"
                full_text = ", ".join(contributor_names)
            else:
                display_text = ", ".join(contributor_names)
                full_text = display_text
            
            contrib_item = QtWidgets.QTableWidgetItem(display_text)
            contrib_item.setToolTip(f"Contributors:\n{full_text}")
            contrib_item.setForeground(QtGui.QColor("#87CEEB"))
            table.setItem(row, 3, contrib_item)
            
            row += 1
        
        table.resizeRowsToContents()
        layout.addWidget(table)
        
        # Footer hint
        hint = QtWidgets.QLabel("<i style='color: #888;'>💡 Hover over cells for more details. Collect more entities to stack bonuses!</i>")
        hint.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(hint)
        
        # OK button
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QtWidgets.QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        ok_btn.setFixedWidth(100)
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _show_saved_encounters(self):
        """Show a dialog to view and open saved encounters."""
        from gamification import get_saved_encounters, open_saved_encounter
        
        if not hasattr(self.blocker, 'adhd_buster'):
            styled_warning(self, "Error", "Could not access saved encounters.")
            return
        
        saved_list = get_saved_encounters(self.blocker.adhd_buster)
        
        if not saved_list:
            styled_info(
                self, "📦 No Saved Encounters",
                "You don't have any saved encounters yet!<br><br>"
                "When you encounter an entity during a focus session,<br>"
                "you can choose 'Save' to keep it for later.<br><br>"
                "Saved encounters preserve your bonding chance<br>"
                "so you can open them when you're ready!"
            )
            return
        
        # Create custom dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"📦 Saved Encounters ({len(saved_list)})")
        dialog.setMinimumWidth(450)
        dialog.setMinimumHeight(400)
        dialog.setStyleSheet("""
            QDialog { background: #1a1a2e; }
            QLabel { color: #eee; }
            QScrollArea { border: none; background: transparent; }
        """)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QtWidgets.QLabel(f"<b>📦 Saved Encounters ({len(saved_list)})</b>")
        header.setStyleSheet("font-size: 16px; color: #c4b5fd;")
        layout.addWidget(header)
        
        info = QtWidgets.QLabel(
            "<i>Click 'Open' to attempt bonding with a saved encounter.</i>"
        )
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)
        
        # Scroll area for encounters
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        
        # Add each saved encounter as a card
        for item in saved_list:
            enc_widget = self._create_saved_encounter_card(item, dialog)
            scroll_layout.addWidget(enc_widget)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 12px;
            }
            QPushButton:hover { background: #555; }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=QtCore.Qt.AlignCenter)
        
        dialog.exec_()
        
        # Refresh after closing in case encounters were opened
        self._update_saved_button_count()
    
    def _create_saved_encounter_card(self, item: dict, parent_dialog: QtWidgets.QDialog) -> QtWidgets.QWidget:
        """Create a card widget for a saved encounter."""
        from gamification import open_saved_encounter
        from entity_drop_dialog import show_entity_encounter
        
        entity = item["entity"]
        enc_data = item["saved_encounter"]
        is_exceptional = enc_data.get("is_exceptional", False)
        saved_probability = enc_data.get("catch_probability", 0.5)
        
        # Card frame
        card = QtWidgets.QFrame()
        rarity_color = RARITY_COLORS.get(entity.rarity.lower(), "#888")
        if is_exceptional:
            border_color = "#FFD700"
        else:
            border_color = rarity_color
        
        card.setStyleSheet(f"""
            QFrame {{
                background: #252540;
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        
        card_layout = QtWidgets.QHBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(10, 10, 10, 10)
        
        # Entity icon (small)
        icon_label = QtWidgets.QLabel()
        # Use robust resolution that handles snake_case filenames
        icon_path = _resolve_entity_svg_path(entity, is_exceptional)
        if icon_path and os.path.exists(icon_path):
            pixmap = QtGui.QPixmap(icon_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(50, 50, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                icon_label.setPixmap(scaled)
        icon_label.setFixedSize(50, 50)
        card_layout.addWidget(icon_label)
        
        # Info section
        info_layout = QtWidgets.QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Name with variant
        display_name = item["display_name"]
        variant_label = item["variant_label"]
        name_label = QtWidgets.QLabel(f"<b>{variant_label}</b> {display_name}")
        name_label.setStyleSheet(f"color: {border_color}; font-size: 12px;")
        info_layout.addWidget(name_label)
        
        # Check for story mismatch
        is_story_mismatch = item.get("is_story_mismatch", False)
        saved_story_name = item.get("saved_story_name", "")
        current_story_name = item.get("current_story_name", "")
        
        # Show story info if there's a mismatch
        if is_story_mismatch:
            story_warning = QtWidgets.QLabel(
                f"<span style='color: #FF9800;'>⚠️ Originally saved by: <b>{saved_story_name}</b> hero</span>"
            )
            story_warning.setStyleSheet("font-size: 10px;")
            story_warning.setToolTip(
                f"This encounter was saved while playing as {saved_story_name}.\n\n"
                f"Probability recalculation is based on that hero's power,\n"
                f"not your currently active {current_story_name} hero.\n\n"
                f"This prevents exploits where players save encounters\n"
                f"with weak heroes and catch them with maxed heroes."
            )
            info_layout.addWidget(story_warning)
        
        # Rarity and chance
        chance_pct = int(saved_probability * 100)
        
        # Check if we can improve this chance
        recalc_info = ""
        potential_prob = item.get("potential_probability", 0)
        potential_pct = int(potential_prob * 100)
        
        has_paid = item.get("has_paid_recalculate", False)
        has_risky = item.get("has_risky_recalculate", False)
        cost = item.get("recalculate_cost", 100)
        
        # Get the actual provider name from perk_providers
        perk_providers = item.get("perk_providers", {})
        paid_provider = perk_providers.get("paid_recalculate_provider", {})
        risky_provider = perk_providers.get("risky_recalculate_provider", {})
        paid_provider_name = paid_provider.get("name", "recalculate perk") if paid_provider else "recalculate perk"
        risky_provider_name = risky_provider.get("name", "risky perk") if risky_provider else "risky perk"
        
        # Show improvement hints if ANY improvement is possible (>=1%)
        # Add note about story-specific calculation if there's a mismatch
        story_calc_note = f" ({saved_story_name} hero)" if is_story_mismatch else ""
        if potential_pct > chance_pct:
            improvement = potential_pct - chance_pct
            if has_paid or has_risky:
                # Show available recalculation options
                options = []
                if has_paid:
                    options.append(f"💰 <b>{paid_provider_name}</b> → {potential_pct}%{story_calc_note} for {cost}🪙")
                if has_risky:
                    risky_rate = perk_providers.get("risky_success_percent", "60%")
                    options.append(f"🎲 <b>{risky_provider_name}</b> → {potential_pct}%{story_calc_note} (free, {risky_rate} success)")
                recalc_info = f"<br><span style='color: #4CAF50;'>💡 +{improvement}% possible: {' | '.join(options)}</span>"
            else:
                # Show locked hint - mention example entities that provide recalculate perks
                recalc_info = (
                    f"<br><span style='color: #888;'>🔒 +{improvement}% possible{story_calc_note} – collect recalculate perks from: "
                    f"Old War Ant General, Sentient Tome, Lucky Coin, Coffee Maker, Chad, or Fridge</span>"
                )
        elif potential_pct == chance_pct and (has_paid or has_risky):
            # Same probability - no benefit to recalculate
            recalc_info = f"<br><span style='color: #666;'>✓ Already optimal for {saved_story_name if is_story_mismatch else 'current'} power</span>"
            
        details = QtWidgets.QLabel(f"⭐ {entity.rarity.capitalize()} | 🎲 {chance_pct}% chance{recalc_info}")
        details.setStyleSheet("color: #aaa; font-size: 11px;")
        details.setOpenExternalLinks(False)  # Allow rich text
        info_layout.addWidget(details)
        
        card_layout.addLayout(info_layout, 1)
        
        # Action Buttons Layout
        actions_layout = QtWidgets.QVBoxLayout()
        actions_layout.setSpacing(4)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        # Open button
        open_btn = QtWidgets.QPushButton("🎲 Open")
        open_btn.setToolTip("Attempt to bond with this entity now using saved probability!")
        open_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #66BB6A; }
        """)
        
        # Capture index for closure
        idx = item["index"]
        
        def on_open():
            parent_dialog.accept()  # Close the list dialog
            self._open_saved_encounter_flow(idx)
            
        open_btn.clicked.connect(on_open)
        actions_layout.addWidget(open_btn)
        
        # Recalculate button (if applicable)
        if has_paid and potential_pct > chance_pct:
            recalc_btn = QtWidgets.QPushButton("⚡ Boost")
            recalc_btn.setToolTip(
                f"💰 Paid Recalculate (via {paid_provider_name})\n\n"
                f"Pays {cost} coins to recalculate odds using your CURRENT power.\n"
                f"Old Chance: {chance_pct}%\n"
                f"New Chance: {potential_pct}%\n"
                f"Cost: {cost} coins"
            )
            recalc_btn.setStyleSheet(f"""
                QPushButton {{
                    background: #252540;
                    color: #FFD700;
                    border: 1px solid #FFD700;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 11px;
                }}
                QPushButton:hover {{ background: #2a2a45; }}
            """)
            
            def on_recalc():
                # Confirm recalculation
                # Build message with story mismatch warning if applicable
                recalc_msg = (
                    f"Pay <b>{cost} coins</b> to boost bonding chance?<br><br>"
                    f"📈 <b>{chance_pct}%</b> ➔ <b>{potential_pct}%</b><br><br>"
                )
                
                if is_story_mismatch and saved_story_name:
                    recalc_msg += (
                        f"⚠️ <span style='color: #FFA500;'><b>Story Mismatch!</b></span><br>"
                        f"This entity was encountered as <b>{saved_story_name}</b>.<br>"
                        f"The recalculated probability is based on that hero's power.<br><br>"
                    )
                
                recalc_msg += f"<i>Powered by {paid_provider_name}</i>"
                
                confirm = styled_question(
                    parent_dialog, f"💰 Paid Recalculate",
                    recalc_msg,
                    ["Yes", "No"]
                )
                
                if confirm == "Yes":
                    parent_dialog.accept()
                    self._open_saved_encounter_flow(idx, recalculate=True)
            
            recalc_btn.clicked.connect(on_recalc)
            actions_layout.addWidget(recalc_btn)
        
        # Risky Recalculate button (free but with risk)
        if has_risky and potential_pct > chance_pct:
            risky_rate = perk_providers.get("risky_success_percent", "60%")
            risky_btn = QtWidgets.QPushButton("🎲 Risky")
            risky_btn.setToolTip(
                f"🎲 Free Risky Recalculate (via {risky_provider_name})\n\n"
                f"FREE recalculation but with {risky_rate} success rate.\n"
                f"Success: {chance_pct}% → {potential_pct}%\n"
                f"Failure: Keep original {chance_pct}%\n"
                f"Cost: FREE!"
            )
            risky_btn.setStyleSheet(f"""
                QPushButton {{
                    background: #252540;
                    color: #9C27B0;
                    border: 1px solid #9C27B0;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 11px;
                }}
                QPushButton:hover {{ background: #2a2a45; }}
            """)
            
            def on_risky_recalc():
                # Confirm risky recalculation
                # Build message with story mismatch warning if applicable
                risky_msg = (
                    f"Try a FREE risky recalculation?<br><br>"
                    f"🎯 <b>{risky_rate}</b> chance of success<br>"
                    f"📈 Success: <b>{chance_pct}%</b> ➔ <b>{potential_pct}%</b><br>"
                    f"❌ Failure: Keep original <b>{chance_pct}%</b><br><br>"
                )
                
                if is_story_mismatch and saved_story_name:
                    risky_msg += (
                        f"<br>⚠️ <span style='color: #FFA500;'><b>Story Mismatch!</b></span><br>"
                        f"This entity was encountered as <b>{saved_story_name}</b>.<br>"
                        f"The recalculated probability is based on that hero's power.<br><br>"
                    )
                
                risky_msg += f"<i>Powered by {risky_provider_name}</i>"
                
                confirm = styled_question(
                    parent_dialog, f"🎲 Free Risky Recalculate",
                    risky_msg,
                    ["Roll the Dice!", "Cancel"]
                )
                
                if confirm == "Roll the Dice!":
                    parent_dialog.accept()
                    self._open_saved_encounter_risky_flow(idx)
            
            risky_btn.clicked.connect(on_risky_recalc)
            actions_layout.addWidget(risky_btn)
            
        card_layout.addLayout(actions_layout)
        
        return card
    
    def _open_saved_encounter_flow(self, index: int, recalculate: bool = False):
        """Open a saved encounter and show the entity encounter dialog."""
        from gamification import (
            open_saved_encounter,
            open_saved_encounter_with_recalculate, 
            attempt_entitidex_bond,
            get_saved_encounters,
        )
        from entity_drop_dialog import show_entity_encounter
        from entitidex import get_entity_by_id
        
        if not hasattr(self.blocker, 'adhd_buster'):
            return
        
        # Get the saved encounter info first
        saved_list = get_saved_encounters(self.blocker.adhd_buster)
        if index >= len(saved_list):
            styled_warning(self, "Error", "Saved encounter not found.")
            return
        
        item = saved_list[index]
        entity = item["entity"]
        enc_data = item["saved_encounter"]
        is_exceptional = enc_data.get("is_exceptional", False)
        saved_probability = enc_data.get("catch_probability", 0.5)
        
        # Check for story mismatch and warn user
        is_story_mismatch = item.get("is_story_mismatch", False)
        saved_story_name = item.get("saved_story_name", "")
        current_story_name = item.get("current_story_name", "")
        
        if is_story_mismatch:
            # Show warning about story mismatch
            choice = styled_question(
                self, "⚠️ Different Hero Warning",
                f"This encounter was originally saved by your <b>{saved_story_name}</b> hero, "
                f"but you're currently playing as <b>{current_story_name}</b>.<br><br>"
                f"<b>Why this matters:</b><br>"
                f"• Probability recalculation is based on your {saved_story_name} hero's power<br>"
                f"• This prevents exploiting saves with weak heroes to catch with maxed heroes<br>"
                f"• The entity belongs to whoever catches it (any hero can use Entitidex perks)<br><br>"
                f"<b>Would you like to proceed anyway?</b>",
                ["Proceed", "Cancel"]
            )
            if choice != "Proceed":
                return
        
        # If recalculating, update the displayed probability to current potential
        if recalculate:
            potential_prob = item.get("potential_probability", saved_probability)
            saved_probability = potential_prob
        
        # Create a bond callback that opens the saved encounter
        def bond_callback(entity_id: str) -> dict:
            if recalculate:
                result = open_saved_encounter_with_recalculate(self.blocker.adhd_buster, index, recalculate=True)
            else:
                result = open_saved_encounter(self.blocker.adhd_buster, index)
            
            # Persist to disk (critical: encounter was consumed, must save)
            main_window = self.window()
            game_state = getattr(main_window, "game_state", None)
            if game_state:
                game_state.force_save()
            else:
                self.blocker.save_config()
            
            if result.get("success"):
                self.refresh()  # Refresh the collection
            return result
        
        # Show the encounter dialog
        show_entity_encounter(
            entity=entity,
            join_probability=saved_probability,
            bond_logic_callback=bond_callback,
            parent=self,
            is_exceptional=is_exceptional,
            save_callback=None,  # No save option for already-saved encounters
        )
        
        # Refresh after dialog closes
        self._update_saved_button_count()
        self.refresh()
    
    def _open_saved_encounter_risky_flow(self, index: int):
        """Open a saved encounter with risky (free) probability recalculation."""
        import random
        from gamification import (
            open_saved_encounter_risky_recalculate,
            finalize_risky_recalculate,
            RISKY_RECALC_SUCCESS_RATE,
        )
        
        if not hasattr(self.blocker, 'adhd_buster'):
            return
        
        # Get risky recalculate data (prepares the encounter)
        prep_result = open_saved_encounter_risky_recalculate(self.blocker.adhd_buster, index)
        
        if not prep_result.get("success", False):
            styled_warning(self, "Risky Recalculate", prep_result.get("message", "Error"))
            return
        
        # Do the risky roll locally
        risky_success = random.random() < RISKY_RECALC_SUCCESS_RATE
        new_prob = prep_result.get("new_probability", 0)
        old_prob = prep_result.get("old_probability", 0)
        
        # Show the risky roll result
        if risky_success:
            styled_info(
                self, "🎲 Risky Recalculate SUCCESS!",
                f"<b>The odds are in your favor!</b><br><br>"
                f"📈 Probability boosted: <b>{int(old_prob*100)}%</b> ➔ <b>{int(new_prob*100)}%</b><br><br>"
                f"<i>Now attempting to bond...</i>"
            )
        else:
            styled_info(
                self, "🎲 Risky Recalculate Failed",
                f"<b>The dice were not kind...</b><br><br>"
                f"📊 Using original probability: <b>{int(old_prob*100)}%</b><br><br>"
                f"<i>Now attempting to bond anyway...</i>"
            )
        
        # Finalize - this does the bond attempt
        final_result = finalize_risky_recalculate(
            self.blocker.adhd_buster, 
            index, 
            risky_success
        )
        
        # Save config after encounter consumed
        main_window = self.window()
        game_state = getattr(main_window, "game_state", None)
        if game_state:
            game_state.force_save()
        else:
            self.blocker.save_config()
        
        if not final_result.get("success", True):  # success here means bond success
            # Bond failed
            prob_used = final_result.get("probability", old_prob)
            entity = final_result.get("entity")
            entity_name = entity.name if entity else "Entity"
            styled_info(
                self, "💨 Bond Failed",
                f"<b>{entity_name}</b> slipped away...<br><br>"
                f"🎲 Roll was unlucky at <b>{int(prob_used*100)}%</b> chance<br><br>"
                f"<i>The pity system will help next time!</i>"
            )
        else:
            # Bond succeeded!
            entity = final_result.get("entity")
            is_exceptional = final_result.get("is_exceptional", False)
            xp_awarded = final_result.get("xp_awarded", 0)
            entity_name = entity.exceptional_name if is_exceptional and entity.exceptional_name else entity.name if entity else "Entity"
            
            if is_exceptional:
                styled_info(
                    self, "🌟✨ EXCEPTIONAL BOND! ✨🌟",
                    f"<b>{entity_name}</b> has joined your team!<br><br>"
                    f"⚡ +{xp_awarded} XP awarded!<br>"
                    f"🌟 Exceptional variant collected!"
                )
            else:
                styled_info(
                    self, "🎉 Bond Successful!",
                    f"<b>{entity_name}</b> has joined your team!<br><br>"
                    f"⚡ +{xp_awarded} XP awarded!"
                )
        
        # Refresh after dialog closes
        self._update_saved_button_count()
        self.refresh()

    def _update_saved_button_count(self):
        """Update the saved encounters button count."""
        if not hasattr(self, 'saved_button'):
            return
        try:
            from gamification import get_saved_encounter_count
            if hasattr(self.blocker, 'adhd_buster'):
                count = get_saved_encounter_count(self.blocker.adhd_buster)
                self.saved_button.setText(f"📦 Saved Encounters ({count})")
        except Exception:
            pass
    
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
    
    def reload_data(self):
        """Reload progress data from blocker and refresh display.
        
        Call this when user profile changes or data is externally modified.
        """
        self._load_progress()
        self.refresh()

    def refresh(self):
        """Public method to refresh the display."""
        self._load_progress()
        self._refresh_all_tabs()
        self._update_saved_button_count()
