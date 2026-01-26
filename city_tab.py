"""
City Building System - UI Tab
=============================
Visual interface for the city builder mini-game.

Features:
- 1x10 horizontal grid of clickable cells (slots unlock by level)
- Building placement and construction progress
- Resource display and collection
- Synergy bonus visualization
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtSvg import QSvgRenderer

# Try to import QWebEngineView for animated SVG support
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    QWebEngineView = None
    QWebEngineSettings = None
    QWebEnginePage = None

from app_utils import get_app_dir
from styled_dialog import StyledDialog, add_tab_help_button
from gamification import get_level_from_xp

# Import city sounds with graceful fallback
try:
    from city_sounds import (
        play_building_complete,
        play_building_placed,
        play_construction_progress,
        play_income_collected,
        play_upgrade_started,
        play_demolish,
    )
    CITY_SOUNDS_AVAILABLE = True
except ImportError:
    CITY_SOUNDS_AVAILABLE = False
    def play_building_complete(bid): pass
    def play_building_placed(bid=None): pass
    def play_construction_progress(): pass
    def play_income_collected(): pass
    def play_upgrade_started(bid=None): pass
    def play_demolish(): pass

_logger = logging.getLogger(__name__)

# Try to import city module
try:
    from city import (
        CITY_AVAILABLE,
        CellStatus,
        CITY_BUILDINGS,
        GRID_ROWS,
        GRID_COLS,
        RESOURCE_TYPES,
        STOCKPILE_RESOURCES,
        EFFORT_RESOURCES,
        DEMOLISH_REFUND_PERCENT,
        get_city_data,
        get_city_bonuses,
        add_city_resource,
        get_resources,
        can_place_building,
        place_building,
        place_and_start_building,
        remove_building,
        invest_resources,
        get_active_construction,
        get_active_construction_info,
        can_initiate_construction,
        initiate_construction,
        collect_city_income,
        get_pending_income,
        award_focus_session_income,
        award_exercise_income,
        get_max_building_slots,
        get_available_slots,
        get_next_slot_unlock,
        get_placed_buildings,
        get_construction_progress,
        can_upgrade,
        can_initiate_upgrade,
        initiate_upgrade,
        start_upgrade,
        get_all_synergy_bonuses,
        get_synergy_display_info,
        calculate_building_synergy_bonus,
        get_level_requirements,
    )
except ImportError as e:
    _logger.warning(f"City module not available: {e}")
    CITY_AVAILABLE = False
    
    # Fallback definitions when city module not available
    from enum import Enum
    class CellStatus(str, Enum):
        EMPTY = "empty"
        PLACED = "placed"
        BUILDING = "building"
        COMPLETE = "complete"
    
    CITY_BUILDINGS = {}
    GRID_ROWS = 5
    GRID_COLS = 5
    RESOURCE_TYPES = ["water", "materials", "activity", "focus"]
    STOCKPILE_RESOURCES = ["water", "materials"]
    EFFORT_RESOURCES = ["activity", "focus"]
    DEMOLISH_REFUND_PERCENT = 50
    
    # Stub functions that do nothing
    def get_city_data(adhd_buster): return {"grid": [[None]*5 for _ in range(5)], "resources": {}, "active_construction": None}
    def get_city_bonuses(adhd_buster): return {}
    def add_city_resource(adhd_buster, res, amt): return 0
    def get_resources(adhd_buster): return {}
    def can_place_building(adhd_buster, bid): return (False, "City system not available")
    def place_building(adhd_buster, r, c, bid): return False
    def remove_building(adhd_buster, r, c): return None
    def invest_resources(adhd_buster, r, c, inv): return {}
    def get_active_construction(adhd_buster): return None
    def get_active_construction_info(adhd_buster): return None
    def can_initiate_construction(adhd_buster, r, c): return (False, "City system not available")
    def initiate_construction(adhd_buster, r, c, gs=None): return {"success": False, "error": "Not available"}
    def collect_city_income(adhd_buster): return {}
    def get_pending_income(adhd_buster): return {}
    def award_focus_session_income(adhd_buster, minutes, gs=None): return {"coins": 0, "breakdown": []}
    def award_exercise_income(adhd_buster, duration, intensity, eff_mins=None, gs=None): return {"coins": 0, "breakdown": [], "qualified": False}
    def get_max_building_slots(level): return 0
    def get_available_slots(adhd_buster): return 0
    def get_next_slot_unlock(adhd_buster): return {}
    def get_placed_buildings(adhd_buster): return []
    def get_construction_progress(adhd_buster, r, c): return {}
    def can_upgrade(adhd_buster, r, c): return (False, "City system not available")
    def can_initiate_upgrade(adhd_buster, r, c): return (False, "City system not available")
    def initiate_upgrade(adhd_buster, r, c, gs=None): return {"success": False, "error": "Not available"}
    def start_upgrade(adhd_buster, r, c): return False
    def get_all_synergy_bonuses(adhd_buster): return {}
    def get_synergy_display_info(building_id, adhd_buster): return {}
    def calculate_building_synergy_bonus(building_id, adhd_buster): return {"bonus_type": None, "bonus_percent": 0.0, "contributors": [], "capped": False}
    def get_level_requirements(building_def, level): return {}


# ============================================================================
# CONSTANTS & STYLING
# ============================================================================

CITY_ICONS_PATH = get_app_dir() / "icons" / "city"

# SVG cache for performance
_svg_pixmap_cache: Dict[str, QtGui.QPixmap] = {}


def _get_svg_pixmap(svg_path: Path, size: int = 48) -> Optional[QtGui.QPixmap]:
    """Load SVG as pixmap with caching."""
    cache_key = f"{svg_path}_{size}"
    if cache_key in _svg_pixmap_cache:
        return _svg_pixmap_cache[cache_key]
    
    if not svg_path.exists():
        return None
    
    try:
        renderer = QSvgRenderer(str(svg_path))
        if not renderer.isValid():
            return None
        
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        _svg_pixmap_cache[cache_key] = pixmap
        return pixmap
    except Exception as e:
        _logger.debug(f"Failed to load SVG {svg_path}: {e}")
        return None


def _get_construction_composite_pixmap(building_id: str, size: int = 128) -> Optional[QtGui.QPixmap]:
    """
    Create a composite pixmap with building SVG (faded) + construction overlay.
    
    Per CITY_SYSTEM_DESIGN.md:
    - Show the actual building so user knows what's being built
    - Overlay construction scaffolding on top
    - Slight fade on building to indicate "not operational yet"
    """
    cache_key = f"construction_{building_id}_{size}"
    if cache_key in _svg_pixmap_cache:
        return _svg_pixmap_cache[cache_key]
    
    # Load base building SVG
    building_path = CITY_ICONS_PATH / f"{building_id}.svg"
    building_pixmap = _get_svg_pixmap(building_path, size)
    
    # Load construction overlay
    construction_path = CITY_ICONS_PATH / "_construction.svg"
    construction_pixmap = _get_svg_pixmap(construction_path, size)
    
    if not building_pixmap:
        # No building SVG, just use construction overlay
        return construction_pixmap
    
    # Create composite
    composite = QtGui.QPixmap(size, size)
    composite.fill(QtCore.Qt.transparent)
    
    painter = QtGui.QPainter(composite)
    painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
    
    # Draw building at reduced opacity (60%)
    painter.setOpacity(0.6)
    painter.drawPixmap(0, 0, building_pixmap)
    
    # Draw construction overlay at full opacity
    if construction_pixmap:
        painter.setOpacity(1.0)
        painter.drawPixmap(0, 0, construction_pixmap)
    
    painter.end()
    
    _svg_pixmap_cache[cache_key] = composite
    return composite


# SVG content cache for animated widgets (avoids redundant file I/O)
_svg_content_cache: Dict[str, str] = {}


class AnimatedBuildingWidget(QtWidgets.QWidget):
    """
    Widget that displays animated SVG using QWebEngineView.
    
    Key feature: Deferred loading and explicit page lifecycle management.
    
    When embedded in containers that may hide/show the widget (like QStackedWidget),
    Qt WebEngine maps widget visibility to the Page Visibility API (Document.hidden).
    This can cause SMIL animations to freeze if the page thinks it's hidden.
    
    Solution: 
    - Don't call setHtml() until the widget is actually visible
    - Explicitly manage page visibility and lifecycle state
    
    Falls back to static QSvgWidget if WebEngine is not available.
    """
    __slots__ = ('svg_path', 'web_view', 'svg_widget', '_loaded')
    
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.web_view: Optional[QWebEngineView] = None
        self.svg_widget: Optional[QSvgWidget] = None
        self._loaded = False  # Track if HTML has been loaded
        self.setFixedSize(128, 128)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        if HAS_WEBENGINE:
            # Use WebEngine for full SVG animation support
            self.web_view = QWebEngineView(self)
            self.web_view.setFixedSize(128, 128)
            
            # Configure for transparent background
            self.web_view.page().setBackgroundColor(QtCore.Qt.transparent)
            self.web_view.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            
            # Disable scrollbars and interactions
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)  # For CSS/SMIL animations
            
            # NOTE: Do NOT call _load_svg() here - defer until widget is visible
            # This prevents Document.hidden from being true when SVG loads
            
            layout.addWidget(self.web_view)
        else:
            # Fallback to static QSvgWidget
            self.svg_widget = QSvgWidget(svg_path, self)
            self.svg_widget.setFixedSize(128, 128)
            self.svg_widget.setStyleSheet("background: transparent;")
            layout.addWidget(self.svg_widget)
    
    def showEvent(self, event):
        """Load SVG when widget becomes visible for the first time."""
        super().showEvent(event)
        # Defer load one tick to ensure geometry/visibility is fully settled
        QtCore.QTimer.singleShot(0, self.ensure_loaded)
    
    def ensure_loaded(self):
        """Load HTML exactly once, only when widget is actually visible."""
        if not self.web_view or self._loaded:
            return
        self._loaded = True
        
        svg_content = self._get_cached_svg_content(self.svg_path)
        
        # Wrap SVG in HTML with transparent background and scaled display
        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
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
        
        # Ensure page is Active after loading
        self.set_active(True)
    
    @staticmethod
    def _get_cached_svg_content(svg_path: str) -> str:
        """Get cached SVG file content to avoid redundant file I/O."""
        if svg_path in _svg_content_cache:
            return _svg_content_cache[svg_path]
        
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            _logger.debug(f"Error loading SVG {svg_path}")
            content = '<svg></svg>'
        
        _svg_content_cache[svg_path] = content
        return content
    
    def set_active(self, active: bool):
        """Explicitly sync WebEngine page visibility and lifecycle with widget visibility.
        
        Qt WebEngine maps widget visibility to the Page Visibility API (Document.hidden).
        When Document.hidden is true, Chromium throttles/pauses animations.
        
        This method forces the correct state:
        - Active: page.setVisible(True), lifecycle=Active → animations run
        - Inactive: page.setVisible(False), lifecycle=Frozen → save CPU
        """
        if not self.web_view or not HAS_WEBENGINE:
            return
        
        page = self.web_view.page()
        
        # Set page visibility (affects Document.hidden)
        page.setVisible(active)
        
        # Set lifecycle state (Active for visible, Frozen for hidden)
        if QWebEnginePage is not None:
            try:
                if active:
                    page.setLifecycleState(QWebEnginePage.LifecycleState.Active)
                else:
                    page.setLifecycleState(QWebEnginePage.LifecycleState.Frozen)
            except Exception:
                pass  # Lifecycle API may not be available in all Qt versions
    
    def stop_animations(self) -> None:
        """Pause WebEngine animations without destroying content."""
        if self.web_view:
            self.set_active(False)
            self.web_view.page().runJavaScript(
                "document.querySelectorAll('*').forEach(el => el.style.animationPlayState = 'paused');"
                "document.querySelectorAll('animate, animateTransform, animateMotion').forEach(el => el.endElement ? el.endElement() : null);"
            )
    
    def restart_animations(self) -> None:
        """Resume WebEngine animations."""
        if self.web_view:
            self.set_active(True)
            self.web_view.page().runJavaScript(
                "document.querySelectorAll('*').forEach(el => el.style.animationPlayState = '');"
                "document.querySelectorAll('animate, animateTransform, animateMotion').forEach(el => el.beginElement ? el.beginElement() : null);"
            )


# Cell status colors (CellStatus is always defined via import or fallback)
STATUS_COLORS = {
    CellStatus.EMPTY.value: "#2A2A3A",      # Dark empty
    CellStatus.PLACED.value: "#3A3A5A",     # Slightly lit (just placed)
    CellStatus.BUILDING.value: "#4A4A6A",   # Under construction
    CellStatus.COMPLETE.value: "#1A4A2A",   # Green complete
}

# Resource icons (emoji fallback)
RESOURCE_ICONS = {
    "water": "💧",
    "materials": "🧱",
    "activity": "⚡",
    "focus": "🎯",
}

# Resource colors
RESOURCE_COLORS = {
    "water": "#4FC3F7",
    "materials": "#A1887F",
    "activity": "#FFD54F",
    "focus": "#BA68C8",
}

# Landscape SVGs for empty building slots - consistent base with varied elements
# All share the same seamless rolling hills background, but have unique features
EMPTY_LANDSCAPE_SVGS = [
    "_empty_base.svg",        # Base plains with gentle grass
    "_empty_forest.svg",      # Pine trees on the plains
    "_empty_rocks.svg",       # Rock formation in the meadow
    "_empty_meadow.svg",      # Wildflowers scattered
    "_empty_butterfly.svg",   # Butterfly flying over plains
    "_empty_windswept.svg",   # Dense wind-swept grass with seeds
    "_empty_pond.svg",        # Small pond with lily pad
    "_empty_ancient_tree.svg", # Large oak tree with falling leaf
    "_empty_fireflies.svg",   # Fireflies at dusk
    "_empty_bird.svg",        # Birds flying across
    "_empty_shrub.svg",       # Berry bush cluster
]


# ============================================================================
# CITY CELL WIDGET
# ============================================================================

class CityCell(QtWidgets.QFrame):
    """A single cell in the city grid.
    
    Shows:
    - Empty state (clickable to place)
    - Building icon with construction progress
    - Complete building with level indicator (ANIMATED via direct QWebEngineView)
    - Synergy indicator for buildings with active entity synergies
    
    Key insight: QWebEngineView is embedded DIRECTLY without wrapper widgets.
    This matches preview_city_animated.py which works perfectly.
    """
    
    clicked = QtCore.Signal(int, int)  # row, col
    
    def __init__(self, row: int, col: int, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self._cell_state = None
        self._building_def = None
        self._web_view = None  # Direct QWebEngineView for animated buildings
        self._current_svg_path = None  # Track which SVG is loaded
        self._pending_svg_path = None  # SVG to load when visible
        self._has_synergy = False  # Track if building has active synergy
        
        # Fixed size like entitidex EntityCard (128 SVG + padding)
        self.setFixedSize(140, 140)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        
        self._setup_ui()
        self._apply_empty_style()
    
    def _setup_ui(self):
        """Set up the cell's internal UI.
        
        Uses DIRECT QWebEngineView embedding without wrapper widgets.
        This matches the working preview_city_animated.py approach.
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)
        
        # Static icon label (for empty, placed, building states)
        # Hidden when WebEngineView is shown for animated buildings
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setAlignment(QtCore.Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent;")
        self.icon_label.setFixedSize(128, 128)
        layout.addWidget(self.icon_label, 0, QtCore.Qt.AlignCenter)
        
        # Level badge (overlaid on icon) - positioned in resizeEvent
        self.level_badge = QtWidgets.QLabel(self)
        self.level_badge.setAlignment(QtCore.Qt.AlignCenter)
        self.level_badge.setStyleSheet("""
            QLabel {
                background: rgba(0, 0, 0, 0.7);
                color: #FFD700;
                font-size: 10px;
                font-weight: bold;
                border-radius: 6px;
                padding: 1px 4px;
            }
        """)
        
        # Synergy indicator (shown when building has active entity synergy)
        self.synergy_badge = QtWidgets.QLabel(self)
        self.synergy_badge.setAlignment(QtCore.Qt.AlignCenter)
        self.synergy_badge.setText("✨")
        self.synergy_badge.setStyleSheet("""
            QLabel {
                background: rgba(186, 104, 200, 0.8);
                color: white;
                font-size: 10px;
                border-radius: 6px;
                padding: 1px 3px;
            }
        """)
        self.synergy_badge.hide()
        self.level_badge.hide()
        
        # Progress/level bar at bottom
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
    
    def _apply_empty_style(self):
        """Style for empty cell - beautiful animated landscape that can be built on.
        
        Each empty slot shows a different natural environment (forest, waterfall, meadow, etc.)
        with subtle animations. The landscape is deterministically selected based on
        cell position so it stays consistent across refreshes.
        """
        # Minimal border styling - let the animated SVG be the focus
        self.setStyleSheet("""
            CityCell {
                background: transparent;
                border: 2px dashed rgba(120, 150, 120, 0.4);
                border-radius: 12px;
            }
            CityCell:hover {
                border: 2px solid rgba(150, 200, 150, 0.8);
                background: rgba(80, 120, 80, 0.1);
            }
        """)
        
        # Select landscape based on cell position (deterministic)
        landscape_index = (self.row * 7 + self.col * 3) % len(EMPTY_LANDSCAPE_SVGS)
        landscape_svg = CITY_ICONS_PATH / EMPTY_LANDSCAPE_SVGS[landscape_index]
        
        # Use animated SVG if WebEngine available
        if landscape_svg.exists() and HAS_WEBENGINE:
            # Hide static label
            self.icon_label.hide()
            # Show animated landscape
            self._show_animated_svg(str(landscape_svg))
        else:
            # Fallback to static empty icon
            if self._web_view:
                self._web_view.hide()
            self.icon_label.show()
            empty_svg = CITY_ICONS_PATH / "_empty.svg"
            pixmap = _get_svg_pixmap(empty_svg, 128)
            if pixmap:
                self.icon_label.setPixmap(pixmap)
            else:
                self.icon_label.setText("➕")
                self.icon_label.setStyleSheet("font-size: 32px; color: rgba(120, 160, 120, 0.7); background: transparent;")
        
        self.progress_bar.hide()
        self.level_badge.hide()
    
    def _apply_locked_style(self):
        """Style for locked cell - requires higher player level to unlock."""
        # Hide WebEngineView if it exists
        if self._web_view:
            self._web_view.hide()
        
        # Show static icon label
        self.icon_label.show()
        
        self.setStyleSheet("""
            CityCell {
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.7,
                    stop: 0 rgba(50, 50, 60, 0.4),
                    stop: 0.6 rgba(40, 40, 50, 0.3),
                    stop: 1 rgba(30, 30, 40, 0.2)
                );
                border: 2px solid rgba(100, 100, 120, 0.4);
                border-radius: 12px;
            }
            CityCell:hover {
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.7,
                    stop: 0 rgba(60, 60, 70, 0.5),
                    stop: 0.6 rgba(50, 50, 60, 0.4),
                    stop: 1 rgba(40, 40, 50, 0.3)
                );
                border: 2px solid rgba(120, 120, 140, 0.6);
            }
        """)
        # Use locked icon - shows padlock - native 128px scale
        locked_svg = CITY_ICONS_PATH / "_locked.svg"
        pixmap = _get_svg_pixmap(locked_svg, 128)
        if pixmap:
            self.icon_label.setPixmap(pixmap)
        else:
            self.icon_label.setText("🔒")
            self.icon_label.setStyleSheet("font-size: 32px; color: rgba(100, 100, 120, 0.7); background: transparent;")
        self.progress_bar.hide()
        self.level_badge.hide()
    
    def _apply_building_style(self, status: str):
        """Style for cell with building - minimal styling to let SVG shine."""
        if status == CellStatus.COMPLETE.value:
            # Completed building - subtle golden glow, no border
            self.setStyleSheet("""
                CityCell {
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.9,
                        stop: 0 rgba(255, 215, 0, 0.15),
                        stop: 0.5 rgba(255, 215, 0, 0.08),
                        stop: 1 transparent
                    );
                    border: none;
                    border-radius: 12px;
                }
                CityCell:hover {
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.9,
                        stop: 0 rgba(255, 235, 59, 0.25),
                        stop: 0.5 rgba(255, 235, 59, 0.12),
                        stop: 1 transparent
                    );
                }
            """)
        elif status == CellStatus.BUILDING.value:
            # Under construction - subtle orange glow, no border
            self.setStyleSheet("""
                CityCell {
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.9,
                        stop: 0 rgba(255, 167, 38, 0.2),
                        stop: 0.5 rgba(255, 167, 38, 0.1),
                        stop: 1 transparent
                    );
                    border: none;
                    border-radius: 12px;
                }
                CityCell:hover {
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.9,
                        stop: 0 rgba(255, 183, 77, 0.3),
                        stop: 0.5 rgba(255, 183, 77, 0.15),
                        stop: 1 transparent
                    );
                }
            """)
        else:
            # Placed but not started - subtle foundation glow
            self.setStyleSheet("""
                CityCell {
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.9,
                        stop: 0 rgba(120, 144, 156, 0.2),
                        stop: 0.5 rgba(120, 144, 156, 0.1),
                        stop: 1 transparent
                    );
                    border: none;
                    border-radius: 12px;
                }
                CityCell:hover {
                    background: qradialgradient(
                        cx: 0.5, cy: 0.5, radius: 0.9,
                        stop: 0 rgba(144, 164, 174, 0.3),
                        stop: 0.5 rgba(144, 164, 174, 0.15),
                        stop: 1 transparent
                    );
                }
            """)
    
    def set_cell_state(self, cell_state: Optional[Dict], building_def: Optional[Dict] = None, adhd_buster: Optional[Dict] = None, locked: bool = False):
        """Update cell to reflect current state.
        
        Args:
            cell_state: Current cell state dict or None if empty
            building_def: Building definition from CITY_BUILDINGS
            adhd_buster: Player data for synergy calculations
            locked: True if slot is locked (requires higher level)
        """
        # Check if the essential state has changed (building_id and status)
        # to avoid recreating expensive WebEngine widgets on every refresh
        old_building_id = self._cell_state.get("building_id") if self._cell_state else None
        old_status = self._cell_state.get("status") if self._cell_state else None
        old_locked = getattr(self, '_is_locked', None)
        
        new_building_id = cell_state.get("building_id") if cell_state else None
        new_status = cell_state.get("status") if cell_state else None
        
        # Track if we need to recreate the display
        state_changed = (old_building_id != new_building_id or old_status != new_status or old_locked != locked)
        
        self._cell_state = cell_state
        self._building_def = building_def
        self._adhd_buster = adhd_buster  # Store for synergy calculation
        self._is_locked = locked  # Track locked state
        
        # Default: show static label, hide webview
        if state_changed:
            self.icon_label.show()
            if self._web_view:
                self._web_view.hide()
            # Clear cached SVG path to force reload when state changes
            self._current_svg_path = None
        
        # Handle locked slots first
        if locked:
            if state_changed:
                self._apply_locked_style()
            return
        
        if cell_state is None:
            if state_changed:
                self._apply_empty_style()
            return
        
        status = cell_state.get("status", "")
        building_id = cell_state.get("building_id", "")
        level = cell_state.get("level", 1)
        
        # Only rebuild display if state changed
        if state_changed:
            # Apply status-based style
            self._apply_building_style(status)
            
            # Handle building display based on status
            if building_id:
                if status == CellStatus.BUILDING.value:
                    # Under construction: show animated building with animated construction overlay
                    svg_path = CITY_ICONS_PATH / f"{building_id}_animated.svg"
                    if not svg_path.exists():
                        svg_path = CITY_ICONS_PATH / f"{building_id}.svg"
                    construction_path = CITY_ICONS_PATH / "_construction.svg"
                    
                    if svg_path.exists() and construction_path.exists() and HAS_WEBENGINE:
                        # Hide static label
                        self.icon_label.hide()
                        # Load building with construction overlay, both animated
                        self._show_construction_animated_svg(str(svg_path), str(construction_path))
                    elif svg_path.exists():
                        # Fallback to static composite if no WebEngine
                        if self._web_view:
                            self._web_view.hide()
                        self.icon_label.show()
                        pixmap = _get_construction_composite_pixmap(building_id, 128)
                        if pixmap:
                            self.icon_label.setPixmap(pixmap)
                            self.icon_label.setStyleSheet("background: transparent;")
                        else:
                            self._set_emoji_icon(building_def)
                    else:
                        self._set_emoji_icon(building_def)
                else:
                    # COMPLETE or PLACED: use animated SVG via WebEngineView
                    svg_path = CITY_ICONS_PATH / f"{building_id}_animated.svg"
                    if not svg_path.exists():
                        svg_path = CITY_ICONS_PATH / f"{building_id}.svg"
                    
                    if svg_path.exists() and HAS_WEBENGINE:
                        # Hide static label
                        self.icon_label.hide()
                        # Load animated SVG into direct WebEngineView
                        self._show_animated_svg(str(svg_path))
                    elif svg_path.exists():
                        # Fallback to static pixmap if no WebEngine
                        if self._web_view:
                            self._web_view.hide()
                        self.icon_label.show()
                        pixmap = _get_svg_pixmap(svg_path, 128)
                        if pixmap:
                            self.icon_label.setPixmap(pixmap)
                            self.icon_label.setStyleSheet("background: transparent;")
                        else:
                            self._set_emoji_icon(building_def)
                    else:
                        # Fallback to emoji
                        self._set_emoji_icon(building_def)
            else:
                self._set_emoji_icon(building_def)
        
        # Show level badge for completed buildings with level > 1
        if status == CellStatus.COMPLETE.value and level > 1:
            self.level_badge.setText(f"★{level}")
            self.level_badge.show()
            self.level_badge.adjustSize()  # Ensure proper size before positioning
        else:
            self.level_badge.hide()
        
        # Check for synergy bonus and show indicator
        self._has_synergy = False
        if building_id and status == CellStatus.COMPLETE.value and CITY_AVAILABLE:
            synergy_result = calculate_building_synergy_bonus(building_id, self._adhd_buster or {})
            if synergy_result.get("bonus_percent", 0) > 0:
                self._has_synergy = True
                bonus_pct = synergy_result["bonus_percent"] * 100
                self.synergy_badge.setToolTip(f"Entity Synergy: +{bonus_pct:.0f}%")
                self.synergy_badge.show()
            else:
                self.synergy_badge.hide()
        else:
            self.synergy_badge.hide()
        
        # Trigger repositioning of badges
        self._position_badges()
        
        # Show progress bar for under-construction buildings
        if status == CellStatus.BUILDING.value:
            self.progress_bar.show()
            progress = cell_state.get("construction_progress", {})
            # Calculate completion percentage
            if building_def and CITY_AVAILABLE:
                reqs = get_level_requirements(building_def, level)
                total_needed = sum(reqs.values())
                total_invested = sum(progress.values())
                percent = int((total_invested / max(total_needed, 1)) * 100)
                self.progress_bar.setValue(percent)
                self.progress_bar.setStyleSheet("""
                    QProgressBar {
                        background: #333;
                        border-radius: 3px;
                    }
                    QProgressBar::chunk {
                        background: #4CAF50;
                        border-radius: 3px;
                    }
                """)
        elif status == CellStatus.PLACED.value:
            # Show 0% progress for just-placed buildings
            self.progress_bar.show()
            self.progress_bar.setValue(0)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    background: #333;
                    border-radius: 3px;
                }
                QProgressBar::chunk {
                    background: #888;
                    border-radius: 3px;
                }
            """)
        else:
            self.progress_bar.hide()
        
        # Update tooltip
        self.setToolTip(self.get_tooltip_text())
    
    def _set_emoji_icon(self, building_def: Optional[Dict]):
        """Set emoji fallback icon when SVG not available."""
        if building_def:
            name = building_def.get("name", "🏛️")
            icon_char = name.split()[0] if name else "🏛️"
            self.icon_label.setText(icon_char)
            self.icon_label.setStyleSheet("font-size: 48px; background: transparent;")
        else:
            self.icon_label.setText("🏛️")
            self.icon_label.setStyleSheet("font-size: 48px; background: transparent;")
    
    def _show_animated_svg(self, svg_path: str):
        """Show animated SVG using direct QWebEngineView.
        
        This method is called when tab is visible (from _refresh_city via showEvent).
        Load immediately since visibility is guaranteed.
        """
        # Skip if same SVG already loaded
        if self._current_svg_path == svg_path:
            if self._web_view:
                self._web_view.show()
            return
        
        self._current_svg_path = svg_path
        
        # Create WebEngineView if it doesn't exist
        if not self._web_view:
            self._web_view = QWebEngineView()  # No parent - will be added to layout
            self._web_view.setFixedSize(128, 128)
            
            # DON'T set transparent background - it breaks animations
            # Just use dark background to match theme
            # self._web_view.page().setBackgroundColor(QtCore.Qt.transparent)
            # self._web_view.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            
            # Allow mouse clicks to pass through to parent CityCell
            self._web_view.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
            
            # Disable scrollbars
            settings = self._web_view.settings()
            settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            
            # Add to layout at same position as icon_label
            self.layout().insertWidget(0, self._web_view, 0, QtCore.Qt.AlignCenter)
        
        self._web_view.show()
        
        # Load SVG content immediately
        svg_content = self._get_cached_svg_content(svg_path)
        
        # Use dark background to match theme (not transparent)
        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ 
        width: 128px; 
        height: 128px; 
        overflow: hidden;
        background: #2A2A2A;
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
        
        # Load with file:// base URL to allow relative references (required for SMIL)
        base_url = QtCore.QUrl.fromLocalFile(str(Path(svg_path).parent) + '/')
        self._web_view.setHtml(html, base_url)
    
    def _show_construction_animated_svg(self, building_svg_path: str, construction_svg_path: str):
        """Show animated building SVG with animated construction overlay on top.
        
        Both SVGs are rendered with SMIL animations via WebEngineView.
        """
        # Track combined path for caching
        combined_path = f"{building_svg_path}+construction"
        
        # Skip if same combination already loaded
        if self._current_svg_path == combined_path:
            if self._web_view:
                self._web_view.show()
            return
        
        self._current_svg_path = combined_path
        
        # Create WebEngineView if it doesn't exist
        if not self._web_view:
            self._web_view = QWebEngineView()
            self._web_view.setFixedSize(128, 128)
            
            # Allow mouse clicks to pass through to parent CityCell
            self._web_view.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
            
            settings = self._web_view.settings()
            settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            
            self.layout().insertWidget(0, self._web_view, 0, QtCore.Qt.AlignCenter)
        
        self._web_view.show()
        
        # Load both SVG contents
        building_svg = self._get_cached_svg_content(building_svg_path)
        construction_svg = self._get_cached_svg_content(construction_svg_path)
        
        # Create HTML with layered SVGs - building at bottom, construction on top
        html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{ 
        width: 128px; 
        height: 128px; 
        overflow: hidden;
        background: #2A2A2A;
        position: relative;
    }}
    .svg-layer {{
        position: absolute;
        top: 0;
        left: 0;
        width: 128px;
        height: 128px;
    }}
    .svg-layer svg {{
        width: 128px;
        height: 128px;
        display: block;
    }}
    .building-layer {{
        z-index: 1;
    }}
    .construction-layer {{
        z-index: 2;
    }}
</style>
</head>
<body>
<div class="svg-layer building-layer">
{building_svg}
</div>
<div class="svg-layer construction-layer">
{construction_svg}
</div>
</body>
</html>'''
        
        base_url = QtCore.QUrl.fromLocalFile(str(Path(building_svg_path).parent) + '/')
        self._web_view.setHtml(html, base_url)

    @staticmethod
    def _get_cached_svg_content(svg_path: str) -> str:
        """Get cached SVG file content."""
        if svg_path in _svg_content_cache:
            return _svg_content_cache[svg_path]
        
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            content = '<svg></svg>'
        
        _svg_content_cache[svg_path] = content
        return content
    
    def _position_badges(self):
        """Position level and synergy badges at correct locations."""
        # Position level badge at bottom-right
        if self.level_badge.isVisible():
            self.level_badge.adjustSize()
            x = self.width() - self.level_badge.width() - 4
            y = self.height() - self.level_badge.height() - 12  # Above progress bar
            self.level_badge.move(x, y)
        
        # Position synergy badge at top-right
        if self.synergy_badge.isVisible():
            self.synergy_badge.adjustSize()
            x = self.width() - self.synergy_badge.width() - 4
            y = 4
            self.synergy_badge.move(x, y)
    
    def resizeEvent(self, event: QtGui.QResizeEvent):
        """Reposition badges when cell is resized."""
        super().resizeEvent(event)
        self._position_badges()
    
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.row, self.col)
        super().mousePressEvent(event)
    
    def get_tooltip_text(self) -> str:
        """Generate tooltip based on cell state."""
        if self._cell_state is None:
            return (
                "<b>🏗️ Empty Building Slot</b><br><br>"
                "Click to place a building!<br><br>"
                "<b>How to earn resources:</b><br>"
                "💧 <i>Water</i> - Log hydration in Hydration tab<br>"
                "🧱 <i>Materials</i> - Log weight in Body tab<br><br>"
                "<b>After construction starts:</b><br>"
                "🏃 <i>Activity</i> - Log workouts<br>"
                "🎯 <i>Focus</i> - Complete focus sessions"
            )
        
        status = self._cell_state.get("status", "")
        building_id = self._cell_state.get("building_id", "")
        level = self._cell_state.get("level", 1)
        
        if self._building_def:
            name = self._building_def.get("name", building_id)
            desc = self._building_def.get("description", "")
            
            if status == CellStatus.COMPLETE.value:
                return f"<b>{name}</b> (Level {level})<br>{desc}<br><i>Click to upgrade or view details</i>"
            elif status == CellStatus.BUILDING.value:
                return f"<b>{name}</b> (Level {level})<br>Under construction<br><i>Click to invest resources</i>"
            else:
                return f"<b>{name}</b><br>Placed - waiting for construction<br><i>Click to start building</i>"
        
        return f"Building: {building_id}"


# ============================================================================
# CITY GRID WIDGET
# ============================================================================

class CityGrid(QtWidgets.QFrame):
    """Simple horizontal row of 10 city building slots."""
    
    cell_clicked = QtCore.Signal(int, int)  # row, col
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.cells: list[list[CityCell]] = []
        self._adhd_buster: Optional[Dict] = None  # Stored for synergy calculations
        self._apply_simple_style()
        self._setup_ui()
    
    def _apply_simple_style(self):
        """Apply minimal transparent background."""
        self.setStyleSheet("""
            CityGrid {
                background: transparent;
                border: none;
            }
        """)
    
    def _setup_ui(self):
        """Create the horizontal row of cells."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        cols = GRID_COLS if CITY_AVAILABLE else 10
        
        # Single row of cells
        row_cells = []
        for col in range(cols):
            cell = CityCell(0, col)  # All in row 0
            cell.clicked.connect(self._on_cell_clicked)
            layout.addWidget(cell)
            row_cells.append(cell)
        self.cells.append(row_cells)
    
    def _on_cell_clicked(self, row: int, col: int):
        self.cell_clicked.emit(row, col)
    
    def update_grid(self, city_data: Dict, adhd_buster: Optional[Dict] = None):
        """Update all cells from city data."""
        if not CITY_AVAILABLE:
            return
        
        self._adhd_buster = adhd_buster
        grid = city_data.get("grid", [])
        
        # Calculate max slots based on player level
        from gamification import get_level_from_xp
        player_level = get_level_from_xp(adhd_buster.get("total_xp", 0))[0] if adhd_buster else 1
        max_slots = get_max_building_slots(player_level)
        
        # Track slot index (0-based) across the grid
        slot_index = 0
        
        for row, row_cells in enumerate(self.cells):
            for col, cell in enumerate(row_cells):
                # Determine if this slot is locked (beyond player's unlocked slots)
                is_locked = slot_index >= max_slots
                
                # Hide locked cells completely (only show unlocked slots)
                if is_locked:
                    cell.hide()
                else:
                    cell.show()
                    if row < len(grid) and col < len(grid[row]):
                        cell_state = grid[row][col]
                        building_def = None
                        if cell_state and cell_state.get("building_id"):
                            building_def = CITY_BUILDINGS.get(cell_state["building_id"])
                        cell.set_cell_state(cell_state, building_def, adhd_buster, locked=False)
                    else:
                        cell.set_cell_state(None, locked=False)
                
                slot_index += 1


# ============================================================================
# RESOURCE BAR WIDGET
# ============================================================================

class ResourceBar(QtWidgets.QFrame):
    """Display current resources horizontally."""
    
    # Resource tooltip descriptions
    RESOURCE_TOOLTIPS = {
        "water": (
            "<b>💧 Water</b><br><br>"
            "Earned by logging hydration in the Hydration tab.<br><br>"
            "<b>Used for:</b> Starting construction on new buildings<br><br>"
            "<i>Stay hydrated, stay building!</i>"
        ),
        "materials": (
            "<b>🧱 Materials</b><br><br>"
            "Earned by logging your weight in the Body tab.<br>"
            "Hitting weight goals = more materials!<br><br>"
            "<b>Used for:</b> Starting construction on new buildings<br><br>"
            "<i>Every weigh-in is a building block!</i>"
        ),
        "activity": (
            "<b>🏃 Activity Points</b><br><br>"
            "Earned by logging workouts and exercises.<br><br>"
            "<b>Used for:</b> Completing buildings under construction<br><br>"
            "<i>Your sweat powers your city!</i>"
        ),
        "focus": (
            "<b>🎯 Focus Points</b><br><br>"
            "Earned by completing focus sessions.<br><br>"
            "<b>Used for:</b> Completing buildings under construction<br><br>"
            "<i>Concentration builds civilizations!</i>"
        ),
    }
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.resource_labels: Dict[str, QtWidgets.QLabel] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Create resource display."""
        self.setStyleSheet("""
            ResourceBar {
                background: #1A1A2A;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 5, 10, 5)
        
        for resource_type in RESOURCE_TYPES if CITY_AVAILABLE else ["water", "materials", "activity", "focus"]:
            icon = RESOURCE_ICONS.get(resource_type, "📦")
            color = RESOURCE_COLORS.get(resource_type, "#CCC")
            
            # Container for this resource
            container = QtWidgets.QWidget()
            container_layout = QtWidgets.QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(4)
            
            # Add tooltip to container
            tooltip = self.RESOURCE_TOOLTIPS.get(resource_type, f"<b>{icon} {resource_type.title()}</b>")
            container.setToolTip(tooltip)
            
            # Icon
            icon_label = QtWidgets.QLabel(icon)
            icon_label.setStyleSheet("font-size: 16px;")
            container_layout.addWidget(icon_label)
            
            # Value
            value_label = QtWidgets.QLabel("0")
            value_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
            container_layout.addWidget(value_label)
            
            self.resource_labels[resource_type] = value_label
            layout.addWidget(container)
        
        layout.addStretch()
    
    def update_resources(self, resources: Dict[str, int]):
        """Update displayed resource values."""
        for resource_type, label in self.resource_labels.items():
            value = resources.get(resource_type, 0)
            label.setText(str(value))


# ============================================================================
# BUILDING PICKER DIALOG
# ============================================================================

class BuildingPickerDialog(StyledDialog):
    """
    Dialog to select and immediately start building construction.
    
    Shows all available buildings with resource costs.
    Buildings with sufficient resources are highlighted green.
    Selecting a building immediately starts construction.
    """
    
    construction_started = QtCore.Signal(str, str)  # building_id, building_name
    
    def __init__(
        self, 
        adhd_buster: dict, 
        row: int,
        col: int,
        parent: Optional[QtWidgets.QWidget] = None
    ):
        self.adhd_buster = adhd_buster
        self.row = row
        self.col = col
        self.selected_building_id = None
        self._result_info = None  # Store result for caller
        super().__init__(
            parent=parent,
            title="Choose Building",
            header_icon="🏗️",
            min_width=550,
            max_width=750,
        )
    
    def _build_content(self, content_layout: QtWidgets.QVBoxLayout):
        """Build the building selection UI."""
        # Current resources display
        resources = get_resources(self.adhd_buster)
        res_parts = []
        for res_type in STOCKPILE_RESOURCES:
            icon = RESOURCE_ICONS.get(res_type, "📦")
            amt = resources.get(res_type, 0)
            color = RESOURCE_COLORS.get(res_type, "#CCC")
            res_parts.append(f'<span style="color:{color}">{icon}{amt}</span>')
        
        resource_header = QtWidgets.QLabel(f"Your Resources: {' '.join(res_parts)}")
        resource_header.setTextFormat(QtCore.Qt.RichText)
        resource_header.setStyleSheet("font-size: 13px; margin-bottom: 8px;")
        resource_header.setToolTip(
            "Your available stockpile resources:\n\n"
            "💧 Water - Earned by logging hydration\n"
            "🧱 Materials - Earned by logging weight (hitting goals)\n\n"
            "These are spent upfront to START construction.\n\n"
            "(Your city treasury. Guard it wisely.)"
        )
        content_layout.addWidget(resource_header)
        
        # Instruction
        instruction = QtWidgets.QLabel("🔨 Select a building to start construction immediately")
        instruction.setStyleSheet("color: #AAA; font-size: 11px; margin-bottom: 10px;")
        instruction.setToolTip(
            "How to build:\n\n"
            "1. Click a building card to select it\n"
            "2. Click 'Start Building' to confirm\n\n"
            "✅ Green border = Ready to build (resources available)\n"
            "🔴 Red border = Not enough resources yet\n"
            "✓ Built = Already placed in your city\n\n"
            "Each building provides unique passive bonuses!\n\n"
            "(Choose wisely. Or don't. You can always demolish later.)"
        )
        content_layout.addWidget(instruction)
        
        # Scrollable area for buildings
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(380)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)
        
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)
        
        placed = set(get_placed_buildings(self.adhd_buster))
        
        for building_id, building in CITY_BUILDINGS.items():
            is_placed = building_id in placed
            
            # Check if we can build (type valid, not already built, have resources)
            can_type, type_reason = can_place_building(self.adhd_buster, building_id)
            
            # Check resource availability
            requirements = building.get("requirements", {})
            missing_resources = {}
            for res_type in STOCKPILE_RESOURCES:
                needed = requirements.get(res_type, 0)
                have = resources.get(res_type, 0)
                if have < needed:
                    missing_resources[res_type] = needed - have
            
            has_resources = len(missing_resources) == 0
            can_build = can_type and has_resources
            
            # Determine reason string
            if is_placed:
                reason = "Already built"
            elif not can_type:
                reason = type_reason
            elif not has_resources:
                parts = [f"{RESOURCE_ICONS.get(r, '📦')}{amt}" for r, amt in missing_resources.items()]
                reason = f"Need: {' '.join(parts)}"
            else:
                reason = ""
            
            # Building card
            card = self._create_building_card(building_id, building, can_build, is_placed, reason, has_resources)
            scroll_layout.addWidget(card)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        content_layout.addWidget(scroll)
        
        # Info label for selected building
        self.info_label = QtWidgets.QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #AAA; font-size: 11px; margin-top: 8px;")
        content_layout.addWidget(self.info_label)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        self.build_btn = QtWidgets.QPushButton("🔨 Start Building")
        self.build_btn.setEnabled(False)
        self.build_btn.clicked.connect(self._on_build)
        self.build_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 10px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:disabled {
                background: #555;
                color: #888;
            }
            QPushButton:hover:!disabled {
                background: #66BB6A;
            }
        """)
        self.build_btn.setToolTip(
            "Start construction on the selected building!\n\n"
            "This will:\n"
            "• Place the building in your city\n"
            "• Deduct 💧 Water & 🧱 Materials from stockpile\n"
            "• Begin the construction process\n\n"
            "Then earn 🏃 Activity and 🎯 Focus to complete it!"
        )
        button_layout.addWidget(self.build_btn)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #555;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #666;
            }
        """)
        cancel_btn.setToolTip("Close without building anything.\n\n(Your city will wait patiently.)")
        button_layout.addWidget(cancel_btn)
        
        content_layout.addLayout(button_layout)
    
    def _create_building_card(
        self, 
        building_id: str, 
        building: Dict, 
        can_build: bool, 
        is_placed: bool,
        reason: str,
        has_resources: bool
    ) -> QtWidgets.QFrame:
        """Create a card for a single building."""
        card = QtWidgets.QFrame()
        card.setProperty("building_id", building_id)
        card.setProperty("can_build", can_build)
        
        # Style based on availability
        if is_placed:
            bg = "#252530"
            border = "#444"
            opacity = "0.6"
        elif can_build:
            bg = "#1A3A2A"
            border = "#4CAF50"
            opacity = "1.0"
        elif has_resources:
            # Can't build but has resources (shouldn't happen often)
            bg = "#2A2A3A"
            border = "#666"
            opacity = "0.8"
        else:
            # Missing resources
            bg = "#2A2525"
            border = "#553333"
            opacity = "0.7"
        
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        
        layout = QtWidgets.QHBoxLayout(card)
        layout.setSpacing(12)
        
        # Icon (SVG with emoji fallback)
        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        
        svg_path = CITY_ICONS_PATH / f"{building_id}.svg"
        pixmap = _get_svg_pixmap(svg_path, 40)
        if pixmap:
            icon_label.setPixmap(pixmap)
            icon_label.setStyleSheet("background: transparent;")
        else:
            name = building.get("name", "🏛️")
            icon = name.split()[0] if name else "🏛️"
            icon_label.setText(icon)
            icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        layout.addWidget(icon_label)
        
        # Info column
        info_layout = QtWidgets.QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Get building effect info for tooltip
        effect = building.get("effect", {})
        effect_type = effect.get("type", "")
        effect_tooltips = {
            "passive_income": "💰 Generates coins automatically over time",
            "merge_success_bonus": "🔧 Increases item merge success chance",
            "rarity_bias_bonus": "✨ Better chance for rare item drops",
            "entity_catch_bonus": "🎯 Higher chance to catch entities",
            "entity_encounter_bonus": "👁️ More entity encounters during sessions",
            "power_bonus": "⚔️ Multiplies your total Power stat",
            "xp_bonus": "📈 Earn more XP from all sources",
            "coin_discount": "💵 Reduces costs on purchases",
            "focus_session_income": "🎯 Earn bonus coins from focus sessions",
            "activity_triggered_income": "🏃 Earn bonus coins from activities",
            "multi": "🌟 Multiple powerful effects combined",
        }
        effect_desc = effect_tooltips.get(effect_type, "Provides passive bonuses")
        
        name_label = QtWidgets.QLabel(building.get("name", building_id))
        name_label.setStyleSheet("color: #FFD700; font-size: 14px; font-weight: bold;")
        name_label.setToolTip(f"{building.get('name', building_id)}\n\n{effect_desc}\n\n(Click to select this building)")
        info_layout.addWidget(name_label)
        
        desc_label = QtWidgets.QLabel(building.get("description", "")[:80])
        desc_label.setStyleSheet("color: #AAA; font-size: 11px;")
        desc_label.setWordWrap(True)
        desc_label.setToolTip(f"{building.get('description', '')}\n\nEffect: {effect_desc}")
        info_layout.addWidget(desc_label)
        
        # Show resource requirements with color coding
        reqs = building.get("requirements", {})
        resources = get_resources(self.adhd_buster)
        req_parts = []
        for res_type in STOCKPILE_RESOURCES:
            needed = reqs.get(res_type, 0)
            have = resources.get(res_type, 0)
            icon = RESOURCE_ICONS.get(res_type, "📦")
            if have >= needed:
                color = "#4CAF50"  # Green - sufficient
            else:
                color = "#F44336"  # Red - insufficient
            req_parts.append(f'<span style="color:{color}">{icon}{needed}</span>')
        
        # Also show effort requirements (activity/focus)
        for res_type in EFFORT_RESOURCES:
            needed = reqs.get(res_type, 0)
            if needed > 0:
                icon = RESOURCE_ICONS.get(res_type, "📦")
                req_parts.append(f'<span style="color:#888">{icon}{needed}</span>')
        
        if req_parts:
            req_label = QtWidgets.QLabel(" ".join(req_parts))
            req_label.setTextFormat(QtCore.Qt.RichText)
            # Build detailed requirements tooltip
            req_tooltip = "Construction requirements:\n\n"
            req_tooltip += "💧🧱 STOCKPILE (paid upfront to start):\n"
            for res_type in STOCKPILE_RESOURCES:
                needed = reqs.get(res_type, 0)
                have = resources.get(res_type, 0)
                icon = RESOURCE_ICONS.get(res_type, "📦")
                status = "✓" if have >= needed else f"(need {needed - have} more)"
                res_names = {"water": "Water", "materials": "Materials"}
                req_tooltip += f"  {icon} {needed} {res_names.get(res_type, res_type)} {status}\n"
            req_tooltip += "\n🏃🎯 EFFORT (earned over time):\n"
            for res_type in EFFORT_RESOURCES:
                needed = reqs.get(res_type, 0)
                icon = RESOURCE_ICONS.get(res_type, "📦")
                res_names = {"activity": "Activity", "focus": "Focus (1 per 30min session)"}
                req_tooltip += f"  {icon} {needed} {res_names.get(res_type, res_type)}\n"
            req_label.setToolTip(req_tooltip)
            info_layout.addWidget(req_label)
        
        layout.addLayout(info_layout, 1)
        
        # Status indicator on right side
        status_layout = QtWidgets.QVBoxLayout()
        status_layout.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        
        if is_placed:
            status_label = QtWidgets.QLabel("✓ Built")
            status_label.setStyleSheet("color: #666; font-size: 11px;")
            status_layout.addWidget(status_label)
        elif can_build:
            status_label = QtWidgets.QLabel("✓ Ready")
            status_label.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")
            status_layout.addWidget(status_label)
        elif reason:
            status_label = QtWidgets.QLabel(reason[:35])
            status_label.setStyleSheet("color: #F44336; font-size: 10px;")
            status_layout.addWidget(status_label)
        
        layout.addLayout(status_layout)
        
        # Make clickable if can build
        if can_build and not is_placed:
            card.setCursor(QtCore.Qt.PointingHandCursor)
            card.mousePressEvent = lambda e, bid=building_id: self._select_building(bid)
        
        return card
    
    def _select_building(self, building_id: str):
        """Handle building selection."""
        self.selected_building_id = building_id
        building = CITY_BUILDINGS.get(building_id, {})
        
        # Update button
        self.build_btn.setEnabled(True)
        self.build_btn.setText(f"🔨 Build {building.get('name', building_id)}")
        
        # Show effect info
        effect = building.get("effect", {})
        effect_desc = building.get("description", "")
        self.info_label.setText(f"📋 {effect_desc}")
        
        # Update visual selection (highlight selected card)
        for child in self.findChildren(QtWidgets.QFrame):
            bid = child.property("building_id")
            if not bid:
                continue
            
            can_build = child.property("can_build")
            
            if bid == building_id:
                child.setStyleSheet("""
                    QFrame {
                        background: #2A4A3A;
                        border: 2px solid #FFD700;
                        border-radius: 8px;
                        padding: 8px;
                    }
                """)
            elif bid in get_placed_buildings(self.adhd_buster):
                child.setStyleSheet("QFrame { background: #252530; border: 1px solid #444; border-radius: 8px; padding: 8px; }")
            elif can_build:
                child.setStyleSheet("QFrame { background: #1A3A2A; border: 1px solid #4CAF50; border-radius: 8px; padding: 8px; }")
            else:
                child.setStyleSheet("QFrame { background: #2A2525; border: 1px solid #553333; border-radius: 8px; padding: 8px; }")
    
    def _on_build(self):
        """Start building construction immediately."""
        if not self.selected_building_id:
            return
        
        # Use the combined place_and_start_building function
        result = place_and_start_building(
            self.adhd_buster,
            self.row,
            self.col,
            self.selected_building_id
        )
        
        if result.get("success"):
            building_name = result.get("building_name", self.selected_building_id)
            self._result_info = result
            
            # Play construction sound
            play_building_placed(self.selected_building_id)
            
            self.construction_started.emit(self.selected_building_id, building_name)
            self.accept()
        else:
            # Show error
            error = result.get("error", "Unknown error")
            missing = result.get("missing_resources", {})
            if missing:
                parts = [f"{RESOURCE_ICONS.get(r, '📦')}{amt}" for r, amt in missing.items()]
                error = f"Need more resources: {' '.join(parts)}"
            
            self.info_label.setText(f"❌ {error}")
            self.info_label.setStyleSheet("color: #F44336; font-size: 12px; margin-top: 8px;")
    
    def get_result(self) -> Optional[dict]:
        """Get the result info after dialog closes."""
        return self._result_info


# ============================================================================
# INITIATE CONSTRUCTION DIALOG (For PLACED buildings - pay materials upfront)
# ============================================================================

class InitiateConstructionDialog(StyledDialog):
    """
    Dialog to initiate construction on a PLACED building.
    
    NOTE: This dialog is now rarely used since BuildingPickerDialog
    immediately starts construction. Kept for backward compatibility
    with any buildings in PLACED state.
    """
    
    def __init__(
        self, 
        adhd_buster: dict, 
        row: int, 
        col: int, 
        parent: Optional[QtWidgets.QWidget] = None
    ):
        self.adhd_buster = adhd_buster
        self.row = row
        self.col = col
        
        city = get_city_data(adhd_buster)
        grid = city.get("grid", [])
        
        # Bounds check for grid access
        def is_valid_cell(r, c):
            return 0 <= r < len(grid) and 0 <= c < len(grid[r])
        
        if not is_valid_cell(row, col):
            _logger.warning(f"Invalid grid cell: ({row}, {col})")
            self.building_id = ""
            self.building = {}
            self.cell = {}
        else:
            cell_state = grid[row][col]
            if cell_state is None:
                _logger.warning(f"Empty cell at ({row}, {col})")
                self.building_id = ""
                self.building = {}
                self.cell = {}
            else:
                self.building_id = cell_state.get("building_id", "")
                self.building = CITY_BUILDINGS.get(self.building_id, {})
                self.cell = cell_state
        
        super().__init__(
            parent=parent,
            title=f"Build {self.building.get('name', 'Building')}",
            header_icon="🏗️",
            min_width=420,
            max_width=520,
        )
    
    def _build_content(self, content_layout: QtWidgets.QVBoxLayout):
        """Build the initiate construction UI."""
        # Guard against empty building
        if not self.building_id or not self.building:
            error_label = QtWidgets.QLabel("⚠️ Building data not found")
            error_label.setStyleSheet("color: #F44336; font-size: 14px;")
            content_layout.addWidget(error_label)
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(self.accept)
            content_layout.addWidget(close_btn)
            return
        
        # Building icon header with SVG
        icon_container = QtWidgets.QWidget()
        icon_layout = QtWidgets.QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 10)
        
        svg_path = CITY_ICONS_PATH / f"{self.building_id}.svg"
        pixmap = _get_svg_pixmap(svg_path, 64)
        icon_label = QtWidgets.QLabel()
        if pixmap:
            icon_label.setPixmap(pixmap)
        else:
            name = self.building.get("name", "🏛️")
            icon_label.setText(name.split()[0] if name else "🏛️")
            icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_layout.addWidget(icon_label, alignment=QtCore.Qt.AlignCenter)
        content_layout.addWidget(icon_container)
        
        # Description
        desc = QtWidgets.QLabel(self.building.get("description", ""))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #AAA; margin-bottom: 15px;")
        content_layout.addWidget(desc)
        
        level = self.cell.get("level", 1)
        reqs = get_level_requirements(self.building, level)
        resources = get_resources(self.adhd_buster)
        
        # Check if can initiate
        can_init, reason = can_initiate_construction(self.adhd_buster, self.row, self.col)
        
        # Materials required (upfront payment)
        materials_frame = QtWidgets.QFrame()
        materials_frame.setStyleSheet("""
            QFrame {
                background: #1A2A3A;
                border: 1px solid #2196F3;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        materials_layout = QtWidgets.QVBoxLayout(materials_frame)
        
        materials_title = QtWidgets.QLabel("💰 Step 1: Pay Materials Upfront")
        materials_title.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 13px;")
        materials_title.setToolTip(
            "Stockpile resources (paid immediately):\n\n"
            "💧 Water - Earned by logging hydration\n"
            "🧱 Materials - Earned by logging weight (hitting goals)\n\n"
            "These resources are deducted when you start construction.\n\n"
            "(Think of it as a down payment on greatness.)"
        )
        materials_layout.addWidget(materials_title)
        
        materials_hint = QtWidgets.QLabel(
            "These resources are spent immediately to start building:"
        )
        materials_hint.setStyleSheet("color: #888; font-size: 10px; margin-bottom: 5px;")
        materials_layout.addWidget(materials_hint)
        
        for res_type in STOCKPILE_RESOURCES:
            needed = reqs.get(res_type, 0)
            have = resources.get(res_type, 0)
            icon = RESOURCE_ICONS.get(res_type, "📦")
            color = RESOURCE_COLORS.get(res_type, "#CCC")
            
            # Add how-to-earn hint
            if res_type == "water":
                source = "(log hydration)"
            elif res_type == "materials":
                source = "(log weight daily)"
            else:
                source = ""
            
            status_color = "#4CAF50" if have >= needed else "#F44336"
            row_label = QtWidgets.QLabel(f"{icon} {res_type.title()}: {have}/{needed} {source}")
            row_label.setStyleSheet(f"color: {status_color}; font-size: 12px;")
            materials_layout.addWidget(row_label)
        
        # Add detailed materials earning explanation
        materials_info = QtWidgets.QLabel(
            "🧱 <b>How to earn Materials:</b> Log your weight in Body tab!\n"
            "• Overweight → Log lower weight = +2 🧱\n"
            "• Underweight → Log higher weight = +2 🧱\n"
            "• Healthy BMI (18.5-25) → Stay stable = +2 🧱"
        )
        materials_info.setStyleSheet("color: #A1887F; font-size: 10px; margin-top: 8px;")
        materials_info.setWordWrap(True)
        materials_layout.addWidget(materials_info)
        
        content_layout.addWidget(materials_frame)
        content_layout.addSpacing(10)
        
        # Effort required (will be contributed over time)
        effort_frame = QtWidgets.QFrame()
        effort_frame.setStyleSheet("""
            QFrame {
                background: #2A1A3A;
                border: 1px solid #BA68C8;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        effort_layout = QtWidgets.QVBoxLayout(effort_frame)
        
        effort_title = QtWidgets.QLabel("⚡ Effort Required (Earned Over Time)")
        effort_title.setStyleSheet("color: #BA68C8; font-weight: bold; font-size: 13px;")
        effort_title.setToolTip(
            "Effort resources (earned automatically over time):\n\n"
            "🏃 Activity - Earned by logging physical activities\n"
            "   +1 per activity, bonus for longer/intense workouts\n\n"
            "🎯 Focus - Earned during focus sessions\n"
            "   +1 per 30 minutes of focused work\n\n"
            "These flow AUTOMATICALLY to the building!\nJust keep doing your thing and it completes itself.\n\n"
            "(The building is very patient. Unlike us.)"
        )
        effort_layout.addWidget(effort_title)
        
        effort_desc = QtWidgets.QLabel(
            "After starting, your daily habits will\n"
            "automatically contribute to this building:"
        )
        effort_desc.setStyleSheet("color: #999; font-size: 11px; font-style: italic;")
        effort_layout.addWidget(effort_desc)
        
        for res_type in EFFORT_RESOURCES:
            needed = reqs.get(res_type, 0)
            icon = RESOURCE_ICONS.get(res_type, "📦")
            # Add how-to-earn hint
            if res_type == "activity":
                hint = "(log activities - intensity matters!)"
            elif res_type == "focus":
                hint = "(complete focus sessions)"
            else:
                hint = ""
            row_label = QtWidgets.QLabel(f"{icon} {res_type.title()}: {needed} needed {hint}")
            row_label.setStyleSheet("color: #CCC; font-size: 12px;")
            effort_layout.addWidget(row_label)
        
        content_layout.addWidget(effort_frame)
        content_layout.addSpacing(15)
        
        # Action buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        if can_init:
            start_btn = QtWidgets.QPushButton("🔨 Start Construction")
            start_btn.clicked.connect(self._start_construction)
            start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4CAF50, stop:1 #388E3C);
                    color: white;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #66BB6A, stop:1 #4CAF50);
                }
            """)
            start_btn.setToolTip(
                "Start construction on this building!\n\n"
                "This will:\n"
                "• Deduct 💧 Water & 🧱 Materials from stockpile\n"
                "• Make this your active construction project\n"
                "• Begin receiving 🏃 Activity & 🎯 Focus automatically\n\n"
                "The building completes when the effort bar fills!\n\n"
                "(The construction crew is already stretching.)"
            )
            btn_layout.addWidget(start_btn)
        else:
            # Show why can't initiate
            reason_label = QtWidgets.QLabel(f"⚠️ {reason}")
            reason_label.setStyleSheet("color: #FF9800; font-size: 12px;")
            content_layout.addWidget(reason_label)
        
        cancel_btn = QtWidgets.QPushButton("Close")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #555;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #666;
            }
        """)
        cancel_btn.setToolTip("Close without starting construction.\n\n(The building plot will still be here.)")
        btn_layout.addWidget(cancel_btn)
        
        # Remove plot button (no resources invested yet, so no refund needed)
        remove_btn = QtWidgets.QPushButton("🗑️ Remove")
        remove_btn.clicked.connect(self._remove_plot)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: #8B0000;
                color: white;
                padding: 10px 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #A52A2A;
            }
        """)
        remove_btn.setToolTip("Remove this building from the plot.\n\nNo resources have been spent yet,\nso there's nothing to refund.\n\n(Changed your mind? No judgment here.)")
        btn_layout.addWidget(remove_btn)
        
        content_layout.addLayout(btn_layout)
    
    def _remove_plot(self):
        """Remove the placed building before construction starts."""
        building_name = self.building.get("name", "this building")
        
        reply = QtWidgets.QMessageBox.question(
            self,
            "Remove Building?",
            f"Remove {building_name} from this plot?\n\n"
            "(No resources have been invested yet, so nothing to refund.)",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            removed = remove_building(self.adhd_buster, self.row, self.col, refund=False)
            if removed:
                self.accept()
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Could not remove building.")
    
    def _start_construction(self):
        """Initiate construction - pay materials and start building."""
        result = initiate_construction(self.adhd_buster, self.row, self.col)
        
        if result.get("success"):
            play_building_placed(self.building_id)
            
            effort_req = result.get("effort_required", {})
            activity_needed = effort_req.get("activity", 0)
            focus_needed = effort_req.get("focus", 0)
            
            QtWidgets.QMessageBox.information(
                self,
                "Construction Started! 🏗️",
                f"<h3>🔨 {result.get('building_name')} is now under construction!</h3>"
                f"<p><b>What happens next?</b></p>"
                f"<p>Your effort from healthy habits will automatically<br>"
                f"contribute to completing this building:</p>"
                f"<table>"
                f"<tr><td>🏃 <b>Activity needed:</b></td><td>{activity_needed}</td></tr>"
                f"<tr><td>🎯 <b>Focus needed:</b></td><td>{focus_needed}</td></tr>"
                f"</table>"
                f"<hr>"
                f"<p><b>How to earn effort:</b></p>"
                f"<ul>"
                f"<li>🏃 Log physical activities (longer + intense = more!)</li>"
                f"<li>🎯 Complete focus sessions (30 min = +1 Focus)</li>"
                f"</ul>"
                f"<p><i>Keep up the good habits and your building will<br>"
                f"complete automatically! 💪</i></p>"
            )
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Cannot Start",
                f"Could not start construction:\n{result.get('error', 'Unknown error')}"
            )


# ============================================================================
# CONSTRUCTION PROGRESS DIALOG (For BUILDING status - show effort progress)
# ============================================================================

class ConstructionProgressDialog(StyledDialog):
    """
    Dialog showing progress of a building under active construction.
    
    Activity and Focus flow automatically - this just shows progress.
    """
    
    def __init__(
        self, 
        adhd_buster: dict, 
        row: int, 
        col: int, 
        parent: Optional[QtWidgets.QWidget] = None
    ):
        self.adhd_buster = adhd_buster
        self.row = row
        self.col = col
        
        city = get_city_data(adhd_buster)
        grid = city.get("grid", [])
        
        if 0 <= row < len(grid) and 0 <= col < len(grid[row]) and grid[row][col]:
            self.cell = grid[row][col]
            self.building_id = self.cell.get("building_id", "")
            self.building = CITY_BUILDINGS.get(self.building_id, {})
        else:
            self.cell = {}
            self.building_id = ""
            self.building = {}
        
        super().__init__(
            parent=parent,
            title=f"Building: {self.building.get('name', 'Unknown')}",
            header_icon="🔨",
            min_width=400,
            max_width=500,
        )
    
    def _build_content(self, content_layout: QtWidgets.QVBoxLayout):
        """Build the progress display UI."""
        if not self.building_id or not self.building:
            error_label = QtWidgets.QLabel("⚠️ Building data not found")
            error_label.setStyleSheet("color: #F44336; font-size: 14px;")
            content_layout.addWidget(error_label)
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(self.accept)
            content_layout.addWidget(close_btn)
            return
        
        # Building icon
        icon_container = QtWidgets.QWidget()
        icon_layout = QtWidgets.QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 10)
        
        svg_path = CITY_ICONS_PATH / f"{self.building_id}.svg"
        pixmap = _get_svg_pixmap(svg_path, 64)
        icon_label = QtWidgets.QLabel()
        if pixmap:
            icon_label.setPixmap(pixmap)
        else:
            name = self.building.get("name", "🏛️")
            icon_label.setText(name.split()[0] if name else "🏛️")
            icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_layout.addWidget(icon_label, alignment=QtCore.Qt.AlignCenter)
        content_layout.addWidget(icon_container)
        
        # Status indicator
        status_label = QtWidgets.QLabel("🔨 Under Construction")
        status_label.setStyleSheet("color: #FF9800; font-size: 16px; font-weight: bold;")
        status_label.setAlignment(QtCore.Qt.AlignCenter)
        status_label.setToolTip(
            "This building is currently under construction!\n\n"
            "Your activities and focus sessions automatically\n"
            "contribute effort toward completion.\n\n"
            "Only one building can be under construction at a time.\n\n"
            "(The construction crew prefers to focus on one project.)"
        )
        content_layout.addWidget(status_label)
        
        content_layout.addSpacing(15)
        
        level = self.cell.get("level", 1)
        progress = self.cell.get("construction_progress", {})
        reqs = get_level_requirements(self.building, level)
        
        # Effort progress
        effort_frame = QtWidgets.QFrame()
        effort_frame.setStyleSheet("""
            QFrame {
                background: #2A2A3A;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        effort_layout = QtWidgets.QVBoxLayout(effort_frame)
        
        effort_title = QtWidgets.QLabel("⚡ Effort Progress")
        effort_title.setStyleSheet("color: #FFD700; font-weight: bold; font-size: 14px;")
        effort_title.setToolTip(
            "Effort progress toward completing this building:\n\n"
            "🏃 Activity - Earned by logging physical activities\n"
            "🎯 Focus - Earned during focus sessions (1 per 30 min)\n\n"
            "These resources flow AUTOMATICALLY to this building.\n"
            "When the bar reaches 100%, construction completes!\n\n"
            "(The tiny workers are doing their best.)"
        )
        effort_layout.addWidget(effort_title)
        
        total_effort_needed = sum(reqs.get(r, 0) for r in EFFORT_RESOURCES)
        total_effort_done = sum(progress.get(r, 0) for r in EFFORT_RESOURCES)
        effort_percent = int((total_effort_done / max(total_effort_needed, 1)) * 100)
        
        effort_bar = QtWidgets.QProgressBar()
        effort_bar.setValue(effort_percent)
        effort_bar.setMaximumHeight(16)
        effort_bar.setStyleSheet("""
            QProgressBar {
                background: #333;
                border-radius: 8px;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #BA68C8, stop:1 #9C27B0);
                border-radius: 8px;
            }
        """)
        effort_layout.addWidget(effort_bar)
        
        for res_type in EFFORT_RESOURCES:
            needed = reqs.get(res_type, 0)
            done = progress.get(res_type, 0)
            icon = RESOURCE_ICONS.get(res_type, "📦")
            color = RESOURCE_COLORS.get(res_type, "#CCC")
            
            # Add how-to-earn action hint
            if res_type == "activity":
                action = "→ Log activities (intensity matters!)"
            elif res_type == "focus":
                action = "→ Complete focus sessions"
            else:
                action = ""
            
            row_label = QtWidgets.QLabel(f"{icon} {res_type.title()}: {done}/{needed}  {action}")
            row_label.setStyleSheet(f"color: {color}; font-size: 12px;")
            effort_layout.addWidget(row_label)
        
        content_layout.addWidget(effort_frame)
        content_layout.addSpacing(10)
        
        # Detailed how-to hints
        hint_frame = QtWidgets.QFrame()
        hint_frame.setStyleSheet("""
            QFrame {
                background: #1A2A2A;
                border: 1px solid #4CAF50;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        hint_layout = QtWidgets.QVBoxLayout(hint_frame)
        hint_layout.setSpacing(4)
        
        hint_title = QtWidgets.QLabel("💡 How to Earn Effort:")
        hint_title.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 12px;")
        hint_layout.addWidget(hint_title)
        
        activity_hint = QtWidgets.QLabel(
            "🏃 <b>Activity</b>: Activities tab → Log physical activities\n"
            "    Longer + more intense activities = more points!"
        )
        activity_hint.setStyleSheet("color: #CCC; font-size: 11px;")
        hint_layout.addWidget(activity_hint)
        
        focus_hint = QtWidgets.QLabel(
            "🎯 <b>Focus</b>: Focus tab → Start a focus session\n"
            "    Each 30-minute block earns +1 Focus"
        )
        focus_hint.setStyleSheet("color: #CCC; font-size: 11px;")
        hint_layout.addWidget(focus_hint)
        
        content_layout.addWidget(hint_frame)
        
        content_layout.addSpacing(15)
        
        # Button row
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Cancel Construction button (with confirmation)
        cancel_btn = QtWidgets.QPushButton("🗑️ Cancel Construction")
        cancel_btn.clicked.connect(self._confirm_cancel)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #8B0000;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #A52A2A;
            }
        """)
        cancel_btn.setToolTip(
            f"⚠️ Cancel this construction\n\n"
            f"This will:\n"
            f"• Stop construction on this building\n"
            f"• Refund {DEMOLISH_REFUND_PERCENT}% of invested resources\n"
            f"• Free up this slot for a different building\n\n"
            f"⚠️ Requires confirmation.\n\n"
            f"(The workers will understand. Probably.)"
        )
        button_layout.addWidget(cancel_btn)
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #555;
                color: white;
                padding: 10px 30px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #666;
            }
        """)
        close_btn.setToolTip("Close this dialog.\n\nConstruction continues automatically!\n\n(The building will be here when you get back.)")
        button_layout.addWidget(close_btn)
        
        content_layout.addLayout(button_layout)
    
    def _confirm_cancel(self):
        """Show confirmation dialog before canceling construction."""
        # Calculate refund amount
        progress = self.cell.get("construction_progress", {})
        total_invested = sum(progress.get(r, 0) for r in EFFORT_RESOURCES)
        refund_percent = DEMOLISH_REFUND_PERCENT
        refund_estimate = int(total_invested * refund_percent / 100)
        
        building_name = self.building.get("name", "this building")
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Cancel Construction?")
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText(f"Cancel construction of {building_name}?")
        msg.setInformativeText(
            f"You will recover {refund_percent}% of invested resources (~{refund_estimate} effort points).\n\n"
            "The building plot will become free for a new building."
        )
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.setDefaultButton(QtWidgets.QMessageBox.No)
        
        # Style the message box
        msg.setStyleSheet("""
            QMessageBox {
                background: #2A2A3A;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
            QPushButton {
                background: #555;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #666;
            }
        """)
        
        if msg.exec() == QtWidgets.QMessageBox.Yes:
            self._cancel_construction()
    
    def _cancel_construction(self):
        """Cancel the construction and refund resources."""
        try:
            # Remove the building with refund
            removed = remove_building(self.adhd_buster, self.row, self.col, refund=True)
            if removed:
                building_name = self.building.get("name", "Building")
                _logger.info(f"Canceled construction of {building_name} at ({self.row}, {self.col})")
                # Close the dialog
                self.accept()
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Error", "Could not cancel construction."
                )
        except Exception as e:
            _logger.exception(f"Error canceling construction: {e}")
            QtWidgets.QMessageBox.warning(
                self, "Error", f"Failed to cancel: {e}"
            )


# Keep legacy name for backward compatibility
ConstructionDialog = InitiateConstructionDialog


# ============================================================================
# BUILDING COMPLETE DIALOG - Celebration when construction/upgrade finishes
# ============================================================================

class BuildingCompleteDialog(StyledDialog):
    """Congratulations dialog shown when a building completes construction or upgrades."""
    
    def __init__(
        self,
        building_id: str,
        building_def: dict,
        level: int,
        is_upgrade: bool = False,
        parent: Optional[QtWidgets.QWidget] = None
    ):
        self.building_id = building_id
        self.building_def = building_def
        self.level = level
        self.is_upgrade = is_upgrade
        
        title = "🎉 Upgrade Complete!" if is_upgrade else "🎉 Building Complete!"
        super().__init__(parent, title=title, min_width=400, max_width=500)
    
    def _build_content(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Build the celebration content."""
        name = self.building_def.get("name", "Building")
        description = self.building_def.get("description", "")
        effect = self.building_def.get("effect", {})
        effect_type = effect.get("type", "")
        
        # Celebration header with animation effect
        if self.is_upgrade:
            header_text = f"✨ {name} is now Level {self.level}! ✨"
        else:
            header_text = f"✨ {name} Complete! ✨"
        
        header = QtWidgets.QLabel(header_text)
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #FFD700;
            margin: 10px;
        """)
        layout.addWidget(header)
        
        # Building icon
        icon_container = QtWidgets.QWidget()
        icon_layout = QtWidgets.QHBoxLayout(icon_container)
        icon_layout.setAlignment(QtCore.Qt.AlignCenter)
        
        icon_label = QtWidgets.QLabel()
        svg_path = CITY_ICONS_PATH / f"{self.building_id}.svg"
        if svg_path.exists():
            pixmap = _get_svg_pixmap(svg_path, 96)
            if pixmap:
                icon_label.setPixmap(pixmap)
        else:
            icon_char = name.split()[0] if name else "🏛️"
            icon_label.setText(icon_char)
            icon_label.setStyleSheet("font-size: 64px;")
        
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_container)
        
        # Description
        desc_label = QtWidgets.QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(QtCore.Qt.AlignCenter)
        desc_label.setStyleSheet("color: #CCC; font-size: 13px; margin: 10px;")
        layout.addWidget(desc_label)
        
        # Effect explanation box
        effect_frame = QtWidgets.QFrame()
        effect_frame.setStyleSheet("""
            QFrame {
                background: #2A3A4A;
                border: 1px solid #4CAF50;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        effect_layout = QtWidgets.QVBoxLayout(effect_frame)
        
        effect_title = QtWidgets.QLabel("🎁 Active Bonus:")
        effect_title.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14px;")
        effect_layout.addWidget(effect_title)
        
        # Calculate and display the active effect
        effect_text = self._get_effect_description(effect_type, effect, self.level)
        effect_label = QtWidgets.QLabel(effect_text)
        effect_label.setWordWrap(True)
        effect_label.setStyleSheet("color: #FFF; font-size: 13px;")
        effect_layout.addWidget(effect_label)
        
        layout.addWidget(effect_frame)
        
        # Level indicator with max level info
        max_level = self.building_def.get("max_level", 5)
        if self.level < max_level:
            level_text = f"Level {self.level}/{max_level} - Keep upgrading for stronger bonuses!"
            level_style = "color: #FFB74D; font-style: italic; margin: 10px;"
        else:
            level_text = f"⭐ MAX LEVEL {self.level} REACHED! ⭐"
            level_style = "color: #FFD700; font-weight: bold; margin: 10px;"
        
        level_label = QtWidgets.QLabel(level_text)
        level_label.setAlignment(QtCore.Qt.AlignCenter)
        level_label.setStyleSheet(level_style)
        layout.addWidget(level_label)
        
        # Close button
        self.add_button_row(
            layout,
            [("🎮 Awesome!", "primary", self.accept)]
        )
    
    def _get_effect_description(self, effect_type: str, effect: dict, level: int) -> str:
        """Generate human-readable effect description based on effect type and level."""
        level_scaling = self.building_def.get("level_scaling", {})
        
        if effect_type == "passive_income":
            base_rate = effect.get("coins_per_hour", 0)
            scaling = level_scaling.get("coins_per_hour", 0)
            total_rate = base_rate + (level - 1) * scaling
            return f"💰 Generates {total_rate:.1f} coins per hour ({total_rate * 24:.0f}/day)"
        
        elif effect_type == "activity_triggered_income":
            base_coins = effect.get("base_coins", 0)
            per_30min = effect.get("coins_per_effective_30min", 0)
            base_scaling = level_scaling.get("base_coins", 0)
            per_30_scaling = level_scaling.get("coins_per_effective_30min", 0)
            total_base = base_coins + (level - 1) * base_scaling
            total_per_30 = per_30min + (level - 1) * per_30_scaling
            min_intensity = effect.get("min_intensity", "moderate")
            return (f"💰 Earn {total_base} coins per {min_intensity}+ exercise\n"
                    f"   Plus +{total_per_30} coins per 30 effective minutes")
        
        elif effect_type == "merge_success_bonus":
            base = effect.get("bonus_percent", 0)
            scaling = level_scaling.get("bonus_percent", 0)
            total = base + (level - 1) * scaling
            return f"🔧 +{total}% merge success rate when combining gear"
        
        elif effect_type == "rarity_bias_bonus":
            base = effect.get("bonus_percent", 0)
            scaling = level_scaling.get("bonus_percent", 0)
            total = base + (level - 1) * scaling
            return f"✨ +{total}% chance for higher rarity item drops"
        
        elif effect_type == "entity_catch_bonus":
            base = effect.get("bonus_percent", 0)
            scaling = level_scaling.get("bonus_percent", 0)
            total = base + (level - 1) * scaling
            return f"🎯 +{total}% creature capture success rate"
        
        elif effect_type == "entity_encounter_bonus":
            base = effect.get("bonus_percent", 0)
            scaling = level_scaling.get("bonus_percent", 0)
            total = base + (level - 1) * scaling
            return f"👀 +{total}% chance to encounter creatures during activities"
        
        elif effect_type == "power_bonus":
            base = effect.get("power_percent", 0)
            scaling = level_scaling.get("power_percent", 0)
            total = base + (level - 1) * scaling
            return f"💪 +{total}% bonus to your hero's total power"
        
        elif effect_type == "xp_bonus":
            base = effect.get("bonus_percent", 0)
            scaling = level_scaling.get("bonus_percent", 0)
            total = base + (level - 1) * scaling
            return f"📚 +{total}% XP from all activities"
        
        elif effect_type == "coin_discount":
            base = effect.get("discount_percent", 0)
            scaling = level_scaling.get("discount_percent", 0)
            total = base + (level - 1) * scaling
            return f"🏪 {total}% discount on merge costs and shop purchases"
        
        elif effect_type == "focus_session_income":
            base_coins = effect.get("coins_per_30min", 0)
            scaling = level_scaling.get("coins_per_30min", 0)
            total = base_coins + (level - 1) * scaling
            return f"💰 Earn {total} coins per 30 minutes of focus time"
        
        elif effect_type == "multi":
            # Wonder building with multiple effects
            bonuses = effect.get("bonuses", {})
            lines = []
            if bonuses.get("coins_per_hour", 0) > 0:
                lines.append(f"💰 +{bonuses['coins_per_hour']} coins/hour")
            if bonuses.get("power_percent", 0) > 0:
                lines.append(f"💪 +{bonuses['power_percent']}% power")
            if bonuses.get("xp_percent", 0) > 0:
                lines.append(f"📚 +{bonuses['xp_percent']}% XP")
            if bonuses.get("all_bonuses_percent", 0) > 0:
                lines.append(f"✨ +{bonuses['all_bonuses_percent']}% to ALL city bonuses")
            return "\n".join(lines) if lines else "Multiple legendary bonuses active!"
        
        else:
            return "Building effect is now active!"


def show_building_complete_dialog(
    building_id: str,
    level: int,
    is_upgrade: bool,
    parent: Optional[QtWidgets.QWidget] = None
) -> None:
    """Show celebration dialog when building completes."""
    building_def = CITY_BUILDINGS.get(building_id, {})
    if not building_def:
        return
    
    # Play celebration sound
    try:
        play_building_complete(building_id)
    except Exception:
        pass
    
    dialog = BuildingCompleteDialog(
        building_id=building_id,
        building_def=building_def,
        level=level,
        is_upgrade=is_upgrade,
        parent=parent
    )
    dialog.exec()
    dialog.deleteLater()


# ============================================================================
# BUILDING DETAILS DIALOG
# ============================================================================

class BuildingDetailsDialog(StyledDialog):
    """Show details of a completed building, including upgrade options."""
    
    def __init__(
        self, 
        adhd_buster: dict, 
        row: int, 
        col: int, 
        parent: Optional[QtWidgets.QWidget] = None
    ):
        self.adhd_buster = adhd_buster
        self.row = row
        self.col = col
        
        city = get_city_data(adhd_buster)
        grid = city.get("grid", [])
        
        # Bounds check for grid access
        if row < len(grid) and col < len(grid[row]) and grid[row][col] is not None:
            self.cell_state = grid[row][col]
            self.building_id = self.cell_state.get("building_id", "")
            self.building = CITY_BUILDINGS.get(self.building_id, {})
        else:
            _logger.warning(f"Invalid or empty cell at ({row}, {col})")
            self.cell_state = {"level": 1, "status": ""}
            self.building_id = ""
            self.building = {}
        
        super().__init__(
            parent=parent,
            title=self.building.get("name", "Building"),
            header_icon=self.building.get("name", "🏛️").split()[0] if self.building.get("name") else "🏛️",
            min_width=400,
            max_width=500,
        )
    
    def _build_content(self, content_layout: QtWidgets.QVBoxLayout):
        """Build the building details UI."""
        # Guard against empty building
        if not self.building_id or not self.building:
            error_label = QtWidgets.QLabel("⚠️ Building data not found")
            error_label.setStyleSheet("color: #F44336; font-size: 14px;")
            content_layout.addWidget(error_label)
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(self.accept)
            content_layout.addWidget(close_btn)
            return
        
        # Building icon header with SVG (use animated for completed buildings)
        icon_container = QtWidgets.QWidget()
        icon_layout = QtWidgets.QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 10)
        
        # Try animated SVG first for completed buildings
        svg_path = CITY_ICONS_PATH / f"{self.building_id}_animated.svg"
        if not svg_path.exists():
            svg_path = CITY_ICONS_PATH / f"{self.building_id}.svg"
        pixmap = _get_svg_pixmap(svg_path, 64)
        icon_label = QtWidgets.QLabel()
        if pixmap:
            icon_label.setPixmap(pixmap)
        else:
            name = self.building.get("name", "🏛️")
            icon_label.setText(name.split()[0] if name else "🏛️")
            icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_layout.addWidget(icon_label, alignment=QtCore.Qt.AlignCenter)
        content_layout.addWidget(icon_container)
        
        level = self.cell_state.get("level", 1)
        max_level = self.building.get("max_level", 5)
        
        # Level display
        level_label = QtWidgets.QLabel(f"Level {level}/{max_level}")
        level_label.setStyleSheet("color: #FFD700; font-size: 18px; font-weight: bold;")
        level_label.setToolTip(
            f"Building Level: {level} out of {max_level} maximum\n\n"
            "Higher levels = stronger bonuses from this building.\n\n"
            "To upgrade, invest resources:\n"
            "💧 Water & 🧱 Materials - paid upfront to start\n"
            "🏃 Activity & 🎯 Focus - earned over time to complete\n\n"
            "(This building is already judging your upgrade pace. No pressure.)"
        )
        content_layout.addWidget(level_label)
        
        # Description
        desc = QtWidgets.QLabel(self.building.get("description", ""))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #AAA; margin: 10px 0;")
        desc.setToolTip(
            f"{self.building.get('description', '')}\n\n"
            f"This building provides passive bonuses 24/7.\n"
            f"No maintenance required - it just works.\n\n"
            f"(Rumor has it the architect was a perfectionist.)"
        )
        content_layout.addWidget(desc)
        
        # Current effects
        effects_frame = QtWidgets.QFrame()
        effects_frame.setStyleSheet("""
            QFrame {
                background: #1A2A1A;
                border: 1px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        effects_layout = QtWidgets.QVBoxLayout(effects_frame)
        
        effects_title = QtWidgets.QLabel("Current Bonuses:")
        effects_title.setStyleSheet("color: #4CAF50; font-weight: bold;")
        effects_title.setToolTip(
            "Active bonuses from this building:\n\n"
            "• Base bonus from building level\n"
            "• Extra % from entity synergies (if any)\n\n"
            "These effects are always active, even while\n"
            "you're reading this tooltip. Multi-tasking!"
        )
        effects_layout.addWidget(effects_title)
        
        effect = self.building.get("effect", {})
        effect_type = effect.get("type", "")
        level_scaling = self.building.get("level_scaling", {})
        
        # Get the actual effect value based on effect type
        # Effects use specific keys like "coins_per_hour", "bonus_percent", "power_percent"
        effect_key_map = {
            "passive_income": ("coins_per_hour", "coins_per_hour"),
            "merge_success_bonus": ("bonus_percent", "bonus_percent"),
            "rarity_bias_bonus": ("bonus_percent", "bonus_percent"),
            "entity_catch_bonus": ("bonus_percent", "bonus_percent"),
            "entity_encounter_bonus": ("bonus_percent", "bonus_percent"),
            "power_bonus": ("power_percent", "power_percent"),
            "xp_bonus": ("bonus_percent", "bonus_percent"),
            "coin_discount": ("discount_percent", "discount_percent"),
        }
        
        effect_key, scaling_key = effect_key_map.get(effect_type, ("value", "value"))
        base_value = effect.get(effect_key, 0)
        scaling = level_scaling.get(scaling_key, 0)
        current_value = base_value + (level - 1) * scaling
        
        # Format effect text with appropriate units
        # Effect type tooltips - clear explanation + subtle wit
        effect_tooltips = {
            "passive_income": f"💰 Passive Income: +{current_value:.1f} coins/hour\n\nThis building generates coins automatically over time.\nCoins accumulate even when you're away.\n\n(The architect insisted on 24/7 productivity.\nWe didn't have the heart to tell them about weekends.)",
            "merge_success_bonus": f"🔧 Merge Success Bonus: +{current_value:.0f}%\n\nIncreases your chance of successful item merges.\nMerging combines two identical items into higher rarity.\n\n(Some call it gambling. We call it 'strategic probability enhancement.')",
            "rarity_bias_bonus": f"✨ Rarity Bias Bonus: +{current_value:.0f}%\n\nBetter chance to receive Rare, Exceptional, or\nLegendary items from all drop sources.\n\n(The RNG gods smile upon this building's residents.)",
            "entity_catch_bonus": f"🎯 Entity Catch Bonus: +{current_value:.0f}%\n\nIncreases your chance to successfully catch\nentities when they appear.\n\n(Entities have started calling this building 'The Trap House.')",
            "entity_encounter_bonus": f"👁️ Entity Encounter Bonus: +{current_value:.0f}%\n\nEntities appear more frequently during sessions.\nMore encounters = more collection opportunities!\n\n(Word spreads fast in the entity community, apparently.)",
            "power_bonus": f"⚔️ Power Bonus: +{current_value:.0f}%\n\nMultiplies your total Power stat.\nPower is calculated from all equipped gear.\n\n(Your equipment is literally glowing with approval.)",
            "xp_bonus": f"📈 XP Bonus: +{current_value:.0f}%\n\nEarn more experience points from all sources.\nLevel up faster and unlock rewards sooner!\n\n(Experience comes to those who wait. Or to those with this building.)",
            "coin_discount": f"💵 Coin Discount: {current_value:.0f}% off\n\nReduces the cost of all purchases.\nSave coins on shop items and upgrades.\n\n(The shopkeepers are NOT happy about this building.)",
            "focus_session_income": f"🎯 Focus Session Income: +{current_value:.1f} coins/session\n\nEarn bonus coins for each focus session completed.\nLonger sessions earn proportionally more.\n\n(Time literally becomes money. Philosophers hate this one trick.)",
            "activity_triggered_income": f"🏃 Activity Triggered Income: +{current_value:.1f} coins/activity\n\nEarn bonus coins when you log activities.\nEvery activity logged = extra income.\n\n(The building gets excited when you do things. Don't ask why.)",
        }
        
        if effect_type == "passive_income":
            effect_text = f"• Coins/Hour: +{current_value:.1f}"
        else:
            effect_text = f"• {effect_type.replace('_', ' ').title()}: +{current_value:.0f}%"
        effect_label = QtWidgets.QLabel(effect_text)
        effect_label.setStyleSheet("color: #CCC;")
        effect_label.setToolTip(effect_tooltips.get(effect_type, f"Provides +{current_value}% bonus to {effect_type.replace('_', ' ')}."))
        effects_layout.addWidget(effect_label)
        
        # Synergy bonus - use calculate_building_synergy_bonus for building-specific bonus
        synergy_result = calculate_building_synergy_bonus(self.building_id, self.adhd_buster)
        synergy_bonus = synergy_result.get("bonus_percent", 0)
        contributors = synergy_result.get("contributors", [])
        
        if synergy_bonus > 0 or contributors:
            # Add synergy section header
            synergy_header = QtWidgets.QLabel("🔗 Entity Synergies:")
            synergy_header.setStyleSheet("color: #BA68C8; font-weight: bold; margin-top: 8px;")
            synergy_header.setToolTip(
                "Entity Synergies boost this building's effects!\n\n"
                "Entities with matching themes provide bonuses:\n"
                "• Normal entity: +5% bonus\n"
                "• Exceptional entity ⭐: +10% bonus\n\n"
                "Maximum synergy bonus: +50%\n\n"
                "(The entities seem genuinely happy to help.\nWe're not sure why. Don't question it.)"
            )
            effects_layout.addWidget(synergy_header)
            
            if synergy_bonus > 0:
                synergy_text = f"   Total: +{synergy_bonus*100:.0f}%"
                if synergy_result.get("capped", False):
                    synergy_text += " (max)"
                synergy_label = QtWidgets.QLabel(synergy_text)
                synergy_label.setStyleSheet("color: #BA68C8;")
                synergy_tooltip = f"Total synergy bonus: +{synergy_bonus*100:.0f}%\n\n"
                synergy_tooltip += f"This stacks with the building's base effect!\nMore entities = bigger bonus (up to 50% cap)."
                if synergy_result.get("capped", False):
                    synergy_tooltip += "\n\n⭐ Maximum synergy reached!\n(Your entities are working overtime. They don't mind.)"
                synergy_label.setToolTip(synergy_tooltip)
                effects_layout.addWidget(synergy_label)
                
                # Show contributing entities in a scroll area if there are many
                entity_scroll = QtWidgets.QScrollArea()
                entity_scroll.setWidgetResizable(True)
                entity_scroll.setMaximumHeight(120)
                entity_scroll.setStyleSheet("""
                    QScrollArea {
                        background: transparent;
                        border: none;
                    }
                    QScrollArea > QWidget > QWidget {
                        background: transparent;
                    }
                """)
                entity_container = QtWidgets.QWidget()
                entity_layout = QtWidgets.QVBoxLayout(entity_container)
                entity_layout.setContentsMargins(0, 0, 0, 0)
                entity_layout.setSpacing(2)
                
                for contrib in contributors[:6]:
                    entity_id = contrib.get("entity_id", "")
                    is_exceptional = contrib.get("is_exceptional", False)
                    bonus = contrib.get("bonus", 0)
                    
                    # Get entity name
                    try:
                        from entitidex.entity_pools import get_entity_by_id
                        entity = get_entity_by_id(entity_id)
                        name = entity.name if entity else entity_id
                    except Exception:
                        name = entity_id
                    
                    star = "⭐ " if is_exceptional else ""
                    entity_text = f"     {star}{name}: +{bonus*100:.0f}%"
                    entity_label = QtWidgets.QLabel(entity_text)
                    entity_label.setWordWrap(True)  # Allow text wrapping
                    entity_label.setStyleSheet("color: #9575CD; font-size: 11px;")
                    if is_exceptional:
                        entity_label.setToolTip(f"⭐ {name} (Exceptional)\n\nProvides +10% synergy bonus to this building.\nExceptional entities give double the normal bonus!\n\n(This one takes their job very seriously.)")
                    else:
                        entity_label.setToolTip(f"{name}\n\nProvides +5% synergy bonus to this building.\nCatch an exceptional version for +10% instead!\n\n(A reliable contributor. Gold star for effort.)")
                    entity_layout.addWidget(entity_label)
                
                if len(contributors) > 6:
                    more_label = QtWidgets.QLabel(f"     ... and {len(contributors) - 6} more")
                    more_label.setStyleSheet("color: #7E57C2; font-size: 11px;")
                    entity_layout.addWidget(more_label)
                
                entity_scroll.setWidget(entity_container)
                effects_layout.addWidget(entity_scroll)
            else:
                no_synergy = QtWidgets.QLabel("   No matching entities yet")
                no_synergy.setStyleSheet("color: #666; font-style: italic;")
                effects_layout.addWidget(no_synergy)
        
        # Show final calculated bonus (base + entity synergy)
        if synergy_bonus > 0:
            final_value = current_value * (1 + synergy_bonus)
            if effect_type == "passive_income":
                final_text = f"📊 Final Bonus: {current_value:.1f}% + {current_value * synergy_bonus:.1f}% (entity) = {final_value:.1f}%"
            else:
                final_text = f"📊 Final Bonus: {current_value:.0f}% + {current_value * synergy_bonus:.0f}% (entity) = {final_value:.0f}%"
            final_label = QtWidgets.QLabel(final_text)
            final_label.setStyleSheet("color: #4CAF50; font-weight: bold; margin-top: 6px;")
            final_label.setWordWrap(True)
            final_label.setToolTip(
                f"Your total effective bonus from this building:\n\n"
                f"• Base building bonus: {current_value:.0f}%\n"
                f"• Entity synergy multiplier: +{synergy_bonus*100:.0f}%\n"
                f"• Combined effect: {final_value:.0f}%\n\n"
                f"(Math is beautiful when it's on your side.)"
            )
            effects_layout.addWidget(final_label)
        
        content_layout.addWidget(effects_frame)
        content_layout.addSpacing(15)
        
        # Upgrade section
        can_up, up_reason = can_upgrade(self.adhd_buster, self.row, self.col)
        
        if level < max_level:
            next_reqs = get_level_requirements(self.building, level + 1)
            
            upgrade_frame = QtWidgets.QFrame()
            upgrade_frame.setStyleSheet("""
                QFrame {
                    background: #2A2A3A;
                    border: 1px solid #555;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            upgrade_layout = QtWidgets.QVBoxLayout(upgrade_frame)
            
            upgrade_title = QtWidgets.QLabel(f"Upgrade to Level {level + 1}")
            upgrade_title.setStyleSheet("color: #FFD700; font-weight: bold;")
            upgrade_title.setToolTip(
                f"Upgrade this building to Level {level + 1}\n\n"
                "Upgrading increases the building's bonus effect.\n\n"
                "How it works:\n"
                "1. Pay 💧 Water & 🧱 Materials upfront to start\n"
                "2. Earn 🏃 Activity & 🎯 Focus over time to complete\n"
                "3. Building upgrades automatically when filled!\n\n"
                "(The construction crew works fast. No breaks.)"
            )
            upgrade_layout.addWidget(upgrade_title)
            
            # Requirements with detailed tooltip
            req_parts = []
            for res, amt in next_reqs.items():
                icon = RESOURCE_ICONS.get(res, "📦")
                req_parts.append(f"{icon} {amt}")
            req_label = QtWidgets.QLabel("Requires: " + "  ".join(req_parts))
            req_label.setStyleSheet("color: #888;")
            
            # Build detailed requirements tooltip
            resource_explanations = {
                "water": "💧 Water - Earned from hydration logging",
                "materials": "🧱 Materials - Earned from weight logging (hitting goals)",
                "activity": "🏃 Activity - Earned from logged physical activities",
                "focus": "🎯 Focus - Earned during focus sessions (1 per 30 min)",
            }
            req_tooltip = "Resources needed for this upgrade:\n\n"
            for res, amt in next_reqs.items():
                icon = RESOURCE_ICONS.get(res, "📦")
                explanation = resource_explanations.get(res, res.title())
                req_tooltip += f"{icon} {amt} - {explanation}\n"
            req_tooltip += "\n💧🧱 Stockpile resources = paid upfront to START.\n"
            req_tooltip += "🏃🎯 Effort resources = flow in automatically over time.\n\n"
            req_tooltip += "(Resource management: it's like a real city, but less paperwork.)"
            req_label.setToolTip(req_tooltip)
            upgrade_layout.addWidget(req_label)
            
            content_layout.addWidget(upgrade_frame)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        if can_up:
            upgrade_btn = QtWidgets.QPushButton("Start Upgrade")
            upgrade_btn.clicked.connect(self._start_upgrade)
            upgrade_btn.setStyleSheet("""
                QPushButton {
                    background: #FF9800;
                    color: white;
                    padding: 8px 15px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #FFB74D;
                }
            """)
            upgrade_btn.setToolTip(
                "Start the upgrade process!\n\n"
                "This will:\n"
                "• Deduct 💧 Water and 🧱 Materials from stockpile\n"
                "• Put building under construction\n"
                "• Begin receiving 🏃 Activity and 🎯 Focus automatically\n\n"
                "The building completes when effort bar fills!\n\n"
                "(The tiny construction workers are already warming up.)"
            )
            btn_layout.addWidget(upgrade_btn)
        elif level < max_level:
            # Show disabled upgrade button with reason
            upgrade_btn = QtWidgets.QPushButton("⏳ Upgrade Unavailable")
            upgrade_btn.setEnabled(False)
            upgrade_btn.setStyleSheet("""
                QPushButton {
                    background: #555;
                    color: #888;
                    padding: 8px 15px;
                    border-radius: 6px;
                }
            """)
            # Show specific reason
            if "Already building" in up_reason:
                upgrade_btn.setToolTip(
                    f"❌ Cannot upgrade right now\n\n"
                    f"{up_reason}\n\n"
                    f"Only one building can be under construction at a time.\n"
                    f"Wait for current construction to complete first.\n\n"
                    f"(The construction crew doesn't multitask well.)"
                )
            else:
                upgrade_btn.setToolTip(f"Cannot upgrade: {up_reason}")
            btn_layout.addWidget(upgrade_btn)
        
        demolish_btn = QtWidgets.QPushButton("Demolish")
        demolish_btn.clicked.connect(self._demolish)
        demolish_btn.setStyleSheet("""
            QPushButton {
                background: #F44336;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #E57373;
            }
        """)
        demolish_btn.setToolTip(
            f"⚠️ Demolish this building\n\n"
            f"This will:\n"
            f"• Remove the building from this slot\n"
            f"• Refund {DEMOLISH_REFUND_PERCENT}% of invested resources\n"
            f"• Free up the slot for a different building\n\n"
            f"⚠️ Requires confirmation.\n\n"
            f"(Sometimes we outgrow our buildings. It's natural.)"
        )
        btn_layout.addWidget(demolish_btn)
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #555;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
            }
        """)
        close_btn.setToolTip("Close this dialog without making changes.\n\n(The building will still be here when you get back.)")
        btn_layout.addWidget(close_btn)
        
        content_layout.addLayout(btn_layout)
    
    def _start_upgrade(self):
        """Start the upgrade process."""
        success = start_upgrade(self.adhd_buster, self.row, self.col)
        if success:
            # Play ascending anticipation sound
            play_upgrade_started(self.building_id)
            QtWidgets.QMessageBox.information(
                self,
                "Upgrade Started",
                f"Upgrading {self.building.get('name')}!\n\n"
                f"Invest effort to complete:\n"
                f"🏃 Activity - Log workouts\n"
                f"🎯 Focus - Complete focus sessions"
            )
            self.accept()
        else:
            # Silent failure - just close dialog
            self.reject()
    
    def _demolish(self):
        """Demolish the building."""
        # Calculate refund preview before confirming
        progress = self.cell_state.get("construction_progress", {})
        refund_preview = []
        for res_type in RESOURCE_TYPES:
            invested = progress.get(res_type, 0)
            refund_amt = int(invested * DEMOLISH_REFUND_PERCENT / 100)
            if refund_amt > 0:
                icon = RESOURCE_ICONS.get(res_type, "📦")
                refund_preview.append(f"{icon}{refund_amt}")
        
        refund_text = "  ".join(refund_preview) if refund_preview else "None"
        
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Demolish",
            f"Are you sure you want to demolish {self.building.get('name')}?\n\n"
            f"Resource refund ({DEMOLISH_REFUND_PERCENT}%): {refund_text}\n\n"
            "You will free up a building slot.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            removed = remove_building(self.adhd_buster, self.row, self.col)
            if removed:
                # Play gentle demolish sound
                play_demolish()
            self.accept()


# ============================================================================
# MAIN CITY TAB
# ============================================================================

class CityTab(QtWidgets.QWidget):
    """Main city builder tab widget."""
    
    # Signal to request data save
    request_save = QtCore.Signal()
    
    # Auto-refresh interval for pending income display (30 seconds)
    INCOME_REFRESH_INTERVAL_MS = 30000
    
    def __init__(self, adhd_buster: dict, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.adhd_buster = adhd_buster
        self._last_refresh_time = 0  # For throttling refreshes
        self._first_show = True  # Track first showEvent
        
        # Timer for auto-refreshing pending income display
        self._income_timer = QtCore.QTimer(self)
        self._income_timer.timeout.connect(self._update_pending_income_display)
        
        self._setup_ui()
        # Don't call _refresh_city() here - defer to showEvent
        # This prevents WebEngineViews from loading while tab is hidden
    
    def showEvent(self, event):
        """Handle tab becoming visible - load/reload WebEngineViews."""
        super().showEvent(event)
        if self._first_show:
            # First time visible - do initial refresh (deferred to ensure visibility)
            self._first_show = False
            # Use longer delay and also trigger animation load after grid is ready
            QtCore.QTimer.singleShot(100, self._refresh_city)
            QtCore.QTimer.singleShot(500, self._force_reload_all_svgs)
    
    def _force_reload_all_svgs(self):
        """Force reload all SVGs in the grid after a delay."""
        if hasattr(self, 'city_grid') and hasattr(self.city_grid, 'cells'):
            for cell in self.city_grid.cells:
                if hasattr(cell, '_current_svg_path') and cell._current_svg_path:
                    # Force reload by clearing current path
                    svg_path = cell._current_svg_path
                    cell._current_svg_path = None
                    cell._show_animated_svg(svg_path)
    
    def _setup_ui(self):
        """Set up the main tab UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Header with title and info
        header_layout = QtWidgets.QHBoxLayout()
        
        title = QtWidgets.QLabel("🏰 Your City")
        title.setStyleSheet("color: #FFD700; font-size: 20px; font-weight: bold;")
        title.setToolTip(
            "<b>🏰 Your Personal City</b><br><br>"
            "Build and upgrade buildings to earn permanent bonuses!<br><br>"
            "<b>How it works:</b><br>"
            "• Use <b>stockpile resources</b> (💧🧱) to start construction<br>"
            "• Invest <b>effort</b> (🏃🎯) to complete buildings<br>"
            "• Completed buildings give you powerful bonuses<br><br>"
            "<i>Rome wasn't built in a day, but your city can be!</i>"
        )
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Building slots indicator
        self.slots_label = QtWidgets.QLabel()
        self.slots_label.setStyleSheet("color: #AAA; font-size: 14px;")
        self.slots_label.setToolTip(
            "<b>🏠 Building Slots</b><br><br>"
            "You unlock more building slots as you level up!<br><br>"
            "<b>Slot Unlocks:</b><br>"
            "• Level 2: 1st slot<br>"
            "• Level 4: 2nd slot<br>"
            "• Level 7: 3rd slot<br>"
            "• Level 11: 4th slot<br>"
            "• Level 16: 5th slot<br>"
            "• And more as you progress!<br><br>"
            "<i>Keep leveling up to expand your empire!</i>"
        )
        header_layout.addWidget(self.slots_label)
        
        # Collect income button (hidden until passive income buildings exist)
        self.collect_btn = QtWidgets.QPushButton("💰 Collect Income")
        self.collect_btn.clicked.connect(self._collect_income)
        self.collect_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFD700, stop:1 #FFA000);
                color: #1A1A1A;
                padding: 8px 15px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFE44D, stop:1 #FFB300);
            }
        """)
        self.collect_btn.setToolTip(
            "Collect accumulated coins from passive income buildings.\n\n"
            "Note: Currently all buildings generate income when you\n"
            "complete activities or focus sessions, not passively."
        )
        self.collect_btn.hide()  # Hidden until passive income is available
        header_layout.addWidget(self.collect_btn)
        
        # Help button (yellow ? that turns grey after being read)
        from styled_dialog import create_tab_help_button
        help_btn = create_tab_help_button("city", self)
        header_layout.addWidget(help_btn)
        
        layout.addLayout(header_layout)
        
        # Resource bar
        self.resource_bar = ResourceBar()
        layout.addWidget(self.resource_bar)
        
        # 🏙️ City Bonuses Summary (collapsed by default, shows all active bonuses)
        self.bonuses_frame = QtWidgets.QFrame()
        self.bonuses_frame.setStyleSheet("""
            QFrame {
                background: #1E1E2E;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        self.bonuses_frame.setToolTip(
            "<b>✨ Active City Bonuses</b><br><br>"
            "These are permanent bonuses from your completed buildings!<br><br>"
            "<b>Bonus Types:</b><br>"
            "• XP multipliers - Earn more XP from activities<br>"
            "• Coin boosts - Get more coins when you're active<br>"
            "• And more unique bonuses per building<br><br>"
            "<i>Build more, bonus more!</i>"
        )
        self.bonuses_layout = QtWidgets.QVBoxLayout(self.bonuses_frame)
        self.bonuses_layout.setContentsMargins(10, 6, 10, 6)
        self.bonuses_layout.setSpacing(4)
        
        bonuses_header = QtWidgets.QHBoxLayout()
        bonuses_title = QtWidgets.QLabel("✨ Active City Bonuses")
        bonuses_title.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 12px;")
        bonuses_header.addWidget(bonuses_title)
        bonuses_header.addStretch()
        self.bonuses_layout.addLayout(bonuses_header)
        
        self.bonuses_content = QtWidgets.QLabel("No buildings yet")
        self.bonuses_content.setStyleSheet("color: #888; font-size: 11px;")
        self.bonuses_content.setWordWrap(True)
        self.bonuses_layout.addWidget(self.bonuses_content)
        
        layout.addWidget(self.bonuses_frame)
        
        # City grid - simple horizontal row of slots (at top, centered)
        grid_container = QtWidgets.QWidget()
        grid_container.setStyleSheet("background: transparent;")
        grid_layout = QtWidgets.QHBoxLayout(grid_container)
        grid_layout.setContentsMargins(0, 10, 0, 10)
        grid_layout.addStretch()
        
        self.city_grid = CityGrid()
        self.city_grid.cell_clicked.connect(self._on_cell_clicked)
        grid_layout.addWidget(self.city_grid)
        
        grid_layout.addStretch()
        layout.addWidget(grid_container)
        
        # Active construction indicator (below buildings, hidden when no active build)
        self.construction_indicator = QtWidgets.QFrame()
        self.construction_indicator.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2A1A3A, stop:0.5 #3A2A4A, stop:1 #2A1A3A);
                border: 2px solid #BA68C8;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.construction_indicator.setToolTip(
            "<b>🔨 Active Construction</b><br><br>"
            "A building is currently under construction!<br><br>"
            "<b>How to finish it faster:</b><br>"
            "🏃 Log workouts → Activity points<br>"
            "🎯 Complete focus sessions → Focus points<br><br>"
            "The progress bar fills as you invest effort.<br>"
            "Once full, your building is complete!<br><br>"
            "<i>Click the building to see detailed progress.</i>"
        )
        indicator_layout = QtWidgets.QHBoxLayout(self.construction_indicator)
        indicator_layout.setContentsMargins(12, 8, 12, 8)
        
        self.construction_icon = QtWidgets.QLabel("🔨")
        self.construction_icon.setStyleSheet("font-size: 24px;")
        indicator_layout.addWidget(self.construction_icon)
        
        construction_info = QtWidgets.QVBoxLayout()
        construction_info.setSpacing(2)
        
        self.construction_name = QtWidgets.QLabel("Building...")
        self.construction_name.setStyleSheet("color: #FFD700; font-weight: bold; font-size: 13px;")
        construction_info.addWidget(self.construction_name)
        
        self.construction_progress = QtWidgets.QProgressBar()
        self.construction_progress.setMaximumHeight(10)
        self.construction_progress.setToolTip(
            "<b>Construction Progress</b><br><br>"
            "Shows overall completion percentage.<br>"
            "Fill it with activity and focus points!"
        )
        self.construction_progress.setStyleSheet("""
            QProgressBar {
                background: #222;
                border-radius: 5px;
                text-align: center;
                color: white;
                font-size: 9px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #BA68C8, stop:1 #9C27B0);
                border-radius: 5px;
            }
        """)
        construction_info.addWidget(self.construction_progress)
        
        self.construction_status = QtWidgets.QLabel("Effort: 0/100")
        self.construction_status.setStyleSheet("color: #AAA; font-size: 11px;")
        construction_info.addWidget(self.construction_status)
        
        indicator_layout.addLayout(construction_info, 1)
        
        # Add hint about how to contribute
        hint_label = QtWidgets.QLabel("Log activities\n& focus sessions!")
        hint_label.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        hint_label.setAlignment(QtCore.Qt.AlignCenter)
        indicator_layout.addWidget(hint_label)
        
        self.construction_indicator.hide()  # Hidden until active construction exists
        layout.addWidget(self.construction_indicator)
        
        # Spacer to push everything up
        layout.addStretch(1)
        
        # Bottom info panel
        self.info_panel = QtWidgets.QLabel()
        self.info_panel.setStyleSheet("color: #888; font-size: 12px;")
        self.info_panel.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.info_panel)
        
        # Timer for resetting warning style
        self._warning_reset_timer = QtCore.QTimer(self)
        self._warning_reset_timer.setSingleShot(True)
        self._warning_reset_timer.timeout.connect(self._reset_info_style)
    
    def _show_warning(self, message: str):
        """Show a warning message with visual emphasis."""
        self.info_panel.setText(message)
        self.info_panel.setStyleSheet(
            "color: #FFB74D; font-size: 13px; font-weight: bold; "
            "background: rgba(255, 183, 77, 0.15); padding: 6px 12px; "
            "border-radius: 4px;"
        )
        # Reset after 4 seconds
        self._warning_reset_timer.start(4000)
    
    def _reset_info_style(self):
        """Reset info panel to normal style."""
        self.info_panel.setStyleSheet("color: #888; font-size: 12px;")
    
    def _refresh_city(self):
        """Refresh all city displays from data."""
        if not CITY_AVAILABLE:
            self.info_panel.setText("City system not available")
            return
        
        try:
            city = get_city_data(self.adhd_buster)
            
            # Update grid (pass adhd_buster for synergy calculations)
            self.city_grid.update_grid(city, self.adhd_buster)
            
            # Update resources (only stockpile resources accumulate now)
            resources = get_resources(self.adhd_buster)
            self.resource_bar.update_resources(resources)
            
            # Update slots display with next unlock info
            placed = len(get_placed_buildings(self.adhd_buster))
            level = get_level_from_xp(self.adhd_buster.get("total_xp", 0))[0]
            max_slots = get_max_building_slots(level)
            
            # Show next unlock if not at max
            next_info = get_next_slot_unlock(self.adhd_buster)
            next_level = next_info.get("next_unlock_level")
            if next_level and max_slots < 10:
                self.slots_label.setText(f"🏠 {placed}/{max_slots} Buildings (Next slot: Lv.{next_level})")
            else:
                self.slots_label.setText(f"🏠 {placed}/{max_slots} Buildings")
            
            # Update active construction indicator
            self._update_construction_indicator()
            
            # Update city bonuses summary
            self._update_bonuses_display()
            
            # Update pending income and collect button visibility
            pending = get_pending_income(self.adhd_buster)
            if pending.get("coins", 0) > 0:
                self.collect_btn.show()
                self.info_panel.setText(
                    f"⏰ Pending income: {pending['coins']} coins ({pending['hours_elapsed']:.1f}h)"
                )
            else:
                self.collect_btn.hide()
                active = get_active_construction(self.adhd_buster)
                if active:
                    self.info_panel.setText("🔨 Building in progress - keep up the activities!")
                elif max_slots == 0:
                    self.info_panel.setText("🔒 Reach Level 2 to unlock your first building slot!")
                elif placed < max_slots:
                    self.info_panel.setText("Click an empty plot to place a building")
                else:
                    self.info_panel.setText("All building slots are in use!")
        except Exception as e:
            _logger.exception("Error refreshing city display")
            self.info_panel.setText(f"⚠️ Display error: {e}")
    
    def refresh(self):
        """Public method to refresh the city display.
        
        Call this from external modules (like activity logging, focus sessions)
        to update progress bars and resource displays after data changes.
        """
        self._refresh_city()
    
    def _activate_animations(self):
        """Activate animations on all cells when tab becomes visible.
        
        This is called when the tab is re-shown after being hidden.
        WebEngineViews need their content reloaded when becoming visible.
        """
        try:
            if hasattr(self, 'city_grid') and hasattr(self.city_grid, 'cells'):
                for cell in self.city_grid.cells:
                    if hasattr(cell, '_load_pending_svg'):
                        cell._load_pending_svg()
        except Exception as e:
            _logger.debug(f"Error activating animations: {e}")
    
    def _update_construction_indicator(self):
        """Update the active construction indicator bar."""
        try:
            info = get_active_construction_info(self.adhd_buster)
            
            if info is None:
                self.construction_indicator.hide()
                return
            
            self.construction_indicator.show()
            
            building_name = info.get("building_name", "Building")
            progress = info.get("progress", {})
            requirements = info.get("effort_requirements", {})
            
            self.construction_name.setText(f"🔨 {building_name}")
            
            # Calculate overall effort progress
            total_needed = sum(requirements.get(r, 0) for r in EFFORT_RESOURCES)
            total_done = sum(progress.get(r, 0) for r in EFFORT_RESOURCES)
            percent = int((total_done / max(total_needed, 1)) * 100)
            
            self.construction_progress.setValue(percent)
            
            # Status text
            activity_done = progress.get("activity", 0)
            activity_needed = requirements.get("activity", 0)
            focus_done = progress.get("focus", 0)
            focus_needed = requirements.get("focus", 0)
            
            self.construction_status.setText(
                f"🏃 {activity_done}/{activity_needed}  •  🎯 {focus_done}/{focus_needed}"
            )
            
        except Exception as e:
            _logger.exception("Error updating construction indicator")
            self.construction_indicator.hide()
    
    def _update_bonuses_display(self):
        """Update the city bonuses summary display."""
        try:
            bonuses = get_city_bonuses(self.adhd_buster)
            
            bonus_parts = []
            
            # Passive income
            coins_per_hour = bonuses.get("coins_per_hour", 0)
            if coins_per_hour > 0:
                bonus_parts.append(f"💰 {coins_per_hour:.1f} coins/hr")
            
            # Power bonus (Training Ground)
            power_bonus = bonuses.get("power_bonus", 0)
            if power_bonus > 0:
                bonus_parts.append(f"🏋️ +{power_bonus}% Power")
            
            # XP bonus (Library)
            xp_bonus = bonuses.get("xp_bonus", 0)
            if xp_bonus > 0:
                bonus_parts.append(f"📚 +{xp_bonus}% XP")
            
            # Merge success (Forge)
            merge_bonus = bonuses.get("merge_success_bonus", 0)
            if merge_bonus > 0:
                bonus_parts.append(f"🔥 +{merge_bonus}% Merge")
            
            # Rarity bias (Artisan Guild)
            rarity_bonus = bonuses.get("rarity_bias_bonus", 0)
            if rarity_bonus > 0:
                bonus_parts.append(f"🎨 +{rarity_bonus}% Rarity")
            
            # Coin discount (Market)
            coin_discount = bonuses.get("coin_discount", 0)
            if coin_discount > 0:
                bonus_parts.append(f"🏪 -{coin_discount}% Cost")
            
            # Entity encounter (Observatory)
            encounter_bonus = bonuses.get("entity_encounter_bonus", 0)
            if encounter_bonus > 0:
                bonus_parts.append(f"🔭 +{encounter_bonus}% Encounter")
            
            # Entity catch (University)
            catch_bonus = bonuses.get("entity_catch_bonus", 0)
            if catch_bonus > 0:
                bonus_parts.append(f"🎓 +{catch_bonus}% Capture")
            
            if bonus_parts:
                self.bonuses_content.setText("  •  ".join(bonus_parts))
                self.bonuses_content.setStyleSheet("color: #b8e994; font-size: 11px;")
            else:
                self.bonuses_content.setText("Build structures to earn passive bonuses!")
                self.bonuses_content.setStyleSheet("color: #888; font-size: 11px; font-style: italic;")
            
        except Exception as e:
            _logger.debug(f"Error updating bonuses display: {e}")
            self.bonuses_content.setText("No bonuses yet")
            self.bonuses_content.setStyleSheet("color: #888; font-size: 11px;")
    
    def _on_cell_clicked(self, row: int, col: int):
        """Handle cell click."""
        if not CITY_AVAILABLE:
            return
        
        try:
            city = get_city_data(self.adhd_buster)
            grid = city.get("grid", [])
            
            # Bounds check
            if row >= len(grid) or col >= (len(grid[row]) if row < len(grid) else 0):
                _logger.warning(f"Cell click out of bounds: ({row}, {col})")
                return
            
            cell = grid[row][col]
            
            # Check if this slot is locked based on player level
            from gamification import get_level_from_xp
            player_level = get_level_from_xp(self.adhd_buster.get("total_xp", 0))[0]
            max_slots = get_max_building_slots(player_level)
            slot_index = row * GRID_COLS + col  # Calculate slot index
            
            if slot_index >= max_slots:
                # Slot is locked - find next unlock level
                next_info = get_next_slot_unlock(self.adhd_buster)
                next_level = next_info.get("next_unlock_level")
                if next_level:
                    self._show_warning(f"🔒 Slot locked - Reach level {next_level} to unlock!")
                else:
                    self._show_warning("🔒 Slot locked - Keep leveling up!")
                return
                
        except Exception as e:
            _logger.exception(f"Error accessing grid at ({row}, {col})")
            return
        
        try:
            if cell is None:
                # Empty cell - check if there's active construction first
                active_construction = get_active_construction(self.adhd_buster)
                if active_construction is not None:
                    active_row, active_col = active_construction
                    # Get building name for better message
                    active_city = get_city_data(self.adhd_buster)
                    active_grid = active_city.get("grid", [])
                    active_cell = active_grid[active_row][active_col] if active_row < len(active_grid) and active_col < len(active_grid[active_row]) else None
                    active_building_id = active_cell.get("building_id", "") if active_cell else ""
                    active_building = CITY_BUILDINGS.get(active_building_id, {})
                    active_name = active_building.get("name", "a building")
                    self._show_warning(f"🚧 Finish or cancel {active_name} first! (Click it to see progress)")
                    return
                
                # No active construction - show building picker (with row/col for direct placement)
                dialog = BuildingPickerDialog(self.adhd_buster, row, col, self)
                def on_construction_started(bid, name):
                    self.info_panel.setText(f"🔨 Started building {name}! Complete activities to power construction.")
                dialog.construction_started.connect(on_construction_started)
                dialog.exec()
                dialog.deleteLater()  # Ensure cleanup
            else:
                status = cell.get("status", "")
                if status == CellStatus.COMPLETE.value:
                    # Show building details
                    dialog = BuildingDetailsDialog(self.adhd_buster, row, col, self)
                    dialog.exec()
                    dialog.deleteLater()  # Ensure cleanup
                elif status == CellStatus.PLACED.value:
                    # Placed but not started - check if there's other active construction
                    active_construction = get_active_construction(self.adhd_buster)
                    if active_construction is not None and active_construction != (row, col):
                        active_row, active_col = active_construction
                        active_city = get_city_data(self.adhd_buster)
                        active_grid = active_city.get("grid", [])
                        active_cell = active_grid[active_row][active_col] if active_row < len(active_grid) and active_col < len(active_grid[active_row]) else None
                        active_building_id = active_cell.get("building_id", "") if active_cell else ""
                        active_building = CITY_BUILDINGS.get(active_building_id, {})
                        active_name = active_building.get("name", "another building")
                        self._show_warning(f"🚧 Finish or cancel {active_name} first!")
                        return
                    dialog = InitiateConstructionDialog(self.adhd_buster, row, col, self)
                    dialog.exec()
                    dialog.deleteLater()  # Ensure cleanup
                elif status == CellStatus.BUILDING.value:
                    # Under active construction - show progress dialog
                    dialog = ConstructionProgressDialog(self.adhd_buster, row, col, self)
                    dialog.exec()
                    dialog.deleteLater()  # Ensure cleanup
                else:
                    # Unknown status - fallback to construction dialog
                    dialog = InitiateConstructionDialog(self.adhd_buster, row, col, self)
                    dialog.exec()
                    dialog.deleteLater()  # Ensure cleanup
        except Exception as e:
            _logger.exception(f"Error handling cell click at ({row}, {col})")
            self.info_panel.setText(f"⚠️ Error: {e}")
        
        self._refresh_city()
        self.request_save.emit()
    
    def _place_building(self, row: int, col: int, building_id: str):
        """Place a building on the grid."""
        success = place_building(self.adhd_buster, row, col, building_id)
        if success:
            # Play placement confirmation sound
            play_building_placed(building_id)
            building = CITY_BUILDINGS.get(building_id, {})
            name = building.get("name", building_id)
            self.info_panel.setText(f"✅ Placed {name} - invest resources to build!")
        else:
            self.info_panel.setText("❌ Could not place building")
    
    def _collect_income(self):
        """Collect pending passive income."""
        if not CITY_AVAILABLE:
            return
        
        try:
            result = collect_city_income(self.adhd_buster)
            coins = result.get("coins", 0)
            
            if coins > 0:
                # Play satisfying coin collection sound
                play_income_collected()
                self.info_panel.setText(f"💰 Collected {coins} coins!")
            else:
                self.info_panel.setText("No income to collect yet")
        except Exception as e:
            _logger.exception("Error collecting city income")
            self.info_panel.setText(f"⚠️ Collection error: {e}")
        
        self._refresh_city()
        self.request_save.emit()
    
    def showEvent(self, event: QtGui.QShowEvent):
        """Refresh when tab becomes visible (with throttling)."""
        super().showEvent(event)
        # Throttle refreshes to avoid excessive updates
        current_time = time.time()
        if current_time - self._last_refresh_time > 0.5:  # Max once per 500ms
            self._refresh_city()
            self._last_refresh_time = current_time
        
        # Start income auto-refresh timer when tab is visible
        if not self._income_timer.isActive():
            self._income_timer.start(self.INCOME_REFRESH_INTERVAL_MS)
    
    def hideEvent(self, event: QtGui.QHideEvent):
        """Stop auto-refresh when tab is hidden to save resources."""
        super().hideEvent(event)
        self._income_timer.stop()
    
    def _update_pending_income_display(self):
        """Update only the pending income display (lightweight refresh)."""
        if not CITY_AVAILABLE:
            return
        
        try:
            pending = get_pending_income(self.adhd_buster)
            if pending.get("coins", 0) > 0:
                self.info_panel.setText(
                    f"⏰ Pending income: {pending['coins']} coins ({pending['hours_elapsed']:.1f}h)"
                )
        except Exception:
            pass  # Silent fail for background updates
