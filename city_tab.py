"""
City Building System - UI Tab
=============================
Visual interface for the city builder mini-game.

Features:
- 5x5 grid of clickable cells
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
    from PySide6.QtWebEngineCore import QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    QWebEngineView = None
    QWebEngineSettings = None

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
        remove_building,
        invest_resources,
        get_active_construction,
        get_active_construction_info,
        can_initiate_construction,
        initiate_construction,
        collect_city_income,
        get_pending_income,
        get_max_building_slots,
        get_available_slots,
        get_next_slot_unlock,
        get_placed_buildings,
        get_construction_progress,
        can_upgrade,
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
    def get_max_building_slots(level): return 0
    def get_available_slots(adhd_buster): return 0
    def get_next_slot_unlock(adhd_buster): return {}
    def get_placed_buildings(adhd_buster): return []
    def get_construction_progress(adhd_buster, r, c): return {}
    def can_upgrade(adhd_buster, r, c): return (False, "City system not available")
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


def _get_construction_composite_pixmap(building_id: str, size: int = 48) -> Optional[QtGui.QPixmap]:
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
    
    Used for completed buildings to show their SMIL/CSS animations
    (flickering flames, rotating domes, sparkling effects).
    
    Falls back to static QSvgWidget if WebEngine is not available.
    
    OPTIMIZATION per CITY_SYSTEM_DESIGN.md:
    - Uses cached SVG content to avoid redundant file I/O
    - Disables unnecessary WebEngine features
    - Minimal DOM with single SVG element
    """
    __slots__ = ('svg_path', 'web_view', 'svg_widget', '_size')
    
    def __init__(self, svg_path: str, size: int = 80, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self._size = size
        self.web_view = None
        self.svg_widget = None
        self.setFixedSize(size, size)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        if HAS_WEBENGINE:
            # Use WebEngine for full SVG animation support
            self.web_view = QWebEngineView(self)
            self.web_view.setFixedSize(size, size)
            
            # Configure for transparent background
            self.web_view.page().setBackgroundColor(QtCore.Qt.transparent)
            self.web_view.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            
            # Apply performance optimizations
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
            settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)  # For CSS animations
            settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, False)
            settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
            settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, False)
            settings.setAttribute(QWebEngineSettings.ScreenCaptureEnabled, False)
            settings.setAttribute(QWebEngineSettings.WebGLEnabled, False)
            
            self._load_svg()
            layout.addWidget(self.web_view)
        else:
            # Fallback to static QSvgWidget
            self.svg_widget = QSvgWidget(svg_path, self)
            self.svg_widget.setFixedSize(size, size)
            self.svg_widget.setStyleSheet("background: transparent;")
            layout.addWidget(self.svg_widget)
    
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
    
    def _load_svg(self):
        """Load the SVG file into WebEngine with proper styling."""
        if not self.web_view:
            return
        
        svg_content = self._get_cached_svg_content(self.svg_path)
        size = self._size
        
        # Wrap SVG in minimal HTML with transparent background
        html = f'''<!DOCTYPE html>
<html>
<head>
<style>
    * {{ margin: 0; padding: 0; }}
    html, body {{ 
        width: {size}px; 
        height: {size}px; 
        overflow: hidden;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    svg {{
        width: {size}px;
        height: {size}px;
        display: block;
    }}
</style>
</head>
<body>
{svg_content}
</body>
</html>'''
        
        self.web_view.setHtml(html)


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


# ============================================================================
# CITY CELL WIDGET
# ============================================================================

class CityCell(QtWidgets.QFrame):
    """A single cell in the city grid.
    
    Shows:
    - Empty state (clickable to place)
    - Building icon with construction progress
    - Complete building with level indicator
    - Synergy indicator for buildings with active entity synergies
    """
    
    clicked = QtCore.Signal(int, int)  # row, col
    
    def __init__(self, row: int, col: int, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self._cell_state = None
        self._building_def = None
        self._animated_widget = None  # For completed buildings with animations
        self._has_synergy = False  # Track if building has active synergy
        
        self.setMinimumSize(96, 96)
        self.setMaximumSize(110, 110)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        
        self._setup_ui()
        self._apply_empty_style()
    
    def _setup_ui(self):
        """Set up the cell's internal UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        # Container for icon and level badge overlay
        self.icon_container = QtWidgets.QWidget()
        self.icon_container.setStyleSheet("background: transparent;")
        icon_layout = QtWidgets.QVBoxLayout(self.icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(0)
        
        # Building icon (SVG pixmap display) - larger for better visuals
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setAlignment(QtCore.Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent;")
        self.icon_label.setMinimumSize(80, 80)
        icon_layout.addWidget(self.icon_label, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(self.icon_container, 1)
        
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
        """Style for empty cell - available building plot with visible plot marker."""
        # Clean up any existing animated widget
        if self._animated_widget:
            self._animated_widget.setParent(None)
            self._animated_widget.deleteLater()
            self._animated_widget = None
        
        # Show the static icon label
        self.icon_label.show()
        
        self.setStyleSheet("""
            CityCell {
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.7,
                    stop: 0 rgba(60, 80, 60, 0.4),
                    stop: 0.6 rgba(50, 70, 50, 0.3),
                    stop: 1 rgba(40, 60, 40, 0.2)
                );
                border: 2px dashed rgba(120, 150, 120, 0.6);
                border-radius: 12px;
            }
            CityCell:hover {
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.7,
                    stop: 0 rgba(80, 120, 80, 0.5),
                    stop: 0.6 rgba(70, 100, 70, 0.4),
                    stop: 1 rgba(60, 90, 60, 0.3)
                );
                border: 2px solid rgba(150, 200, 150, 0.8);
            }
        """)
        # Use empty/plus icon or fallback to emoji - larger for visibility
        empty_svg = CITY_ICONS_PATH / "_locked.svg"
        pixmap = _get_svg_pixmap(empty_svg, 48)
        if pixmap:
            self.icon_label.setPixmap(pixmap)
        else:
            self.icon_label.setText("➕")
            self.icon_label.setStyleSheet("font-size: 32px; color: rgba(120, 160, 120, 0.7); background: transparent;")
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
    
    def set_cell_state(self, cell_state: Optional[Dict], building_def: Optional[Dict] = None, adhd_buster: Optional[Dict] = None):
        """Update cell to reflect current state."""
        self._cell_state = cell_state
        self._building_def = building_def
        self._adhd_buster = adhd_buster  # Store for synergy calculation
        
        # Clean up any existing animated widget
        if self._animated_widget:
            self._animated_widget.setParent(None)
            self._animated_widget.deleteLater()
            self._animated_widget = None
        
        # Show icon_label by default (will be hidden if using animated widget)
        self.icon_label.show()
        
        if cell_state is None:
            self._apply_empty_style()
            return
        
        status = cell_state.get("status", "")
        building_id = cell_state.get("building_id", "")
        level = cell_state.get("level", 1)
        
        # Apply status-based style
        self._apply_building_style(status)
        
        # Handle building display based on status
        if building_id:
            if status == CellStatus.COMPLETE.value:
                # Completed: use ANIMATED SVG widget for full animation support
                svg_path = CITY_ICONS_PATH / f"{building_id}_animated.svg"
                if not svg_path.exists():
                    svg_path = CITY_ICONS_PATH / f"{building_id}.svg"
                
                if svg_path.exists():
                    # Hide static label, use animated widget
                    self.icon_label.hide()
                    self._animated_widget = AnimatedBuildingWidget(str(svg_path), 80, self.icon_container)
                    self.icon_container.layout().addWidget(self._animated_widget, alignment=QtCore.Qt.AlignCenter)
                else:
                    # Fallback to emoji
                    self._set_emoji_icon(building_def)
                
            elif status == CellStatus.BUILDING.value:
                # Under construction: composite of building + scaffolding overlay (static)
                pixmap = _get_construction_composite_pixmap(building_id, 80)
                if pixmap:
                    self.icon_label.setPixmap(pixmap)
                    self.icon_label.setStyleSheet("background: transparent;")
                else:
                    self._set_emoji_icon(building_def)
                
            else:
                # Placed or other: static building SVG
                svg_path = CITY_ICONS_PATH / f"{building_id}.svg"
                pixmap = _get_svg_pixmap(svg_path, 80)
                if pixmap:
                    self.icon_label.setPixmap(pixmap)
                    self.icon_label.setStyleSheet("background: transparent;")
                else:
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
            return "Empty - Click to place a building"
        
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
    """The 5x5 grid of city cells with terrain background."""
    
    cell_clicked = QtCore.Signal(int, int)  # row, col
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.cells: list[list[CityCell]] = []
        self._adhd_buster: Optional[Dict] = None  # Stored for synergy calculations
        self._apply_terrain_style()
        self._setup_ui()
    
    def _apply_terrain_style(self):
        """Apply impressive terrain/land background with natural landscape feel."""
        self.setStyleSheet("""
            CityGrid {
                background: qradialgradient(
                    cx: 0.5, cy: 0.4, radius: 1.0,
                    stop: 0 #4A7A4A,
                    stop: 0.2 #3D6B3D,
                    stop: 0.4 #2F5C2F,
                    stop: 0.6 #285528,
                    stop: 0.8 #1F471F,
                    stop: 1.0 #183A18
                );
                border: 4px solid qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #6B8B6B,
                    stop: 0.3 #5A7A5A,
                    stop: 0.7 #4A6A4A,
                    stop: 1.0 #3A5A3A
                );
                border-radius: 16px;
            }
        """)
    
    def _setup_ui(self):
        """Create the grid of cells."""
        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        rows = GRID_ROWS if CITY_AVAILABLE else 5
        cols = GRID_COLS if CITY_AVAILABLE else 5
        
        for row in range(rows):
            row_cells = []
            for col in range(cols):
                cell = CityCell(row, col)
                cell.clicked.connect(self._on_cell_clicked)
                layout.addWidget(cell, row, col)
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
        
        for row, row_cells in enumerate(self.cells):
            for col, cell in enumerate(row_cells):
                if row < len(grid) and col < len(grid[row]):
                    cell_state = grid[row][col]
                    building_def = None
                    if cell_state and cell_state.get("building_id"):
                        building_def = CITY_BUILDINGS.get(cell_state["building_id"])
                    cell.set_cell_state(cell_state, building_def, adhd_buster)
                else:
                    cell.set_cell_state(None)


# ============================================================================
# RESOURCE BAR WIDGET
# ============================================================================

class ResourceBar(QtWidgets.QFrame):
    """Display current resources horizontally."""
    
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
    """Dialog to select a building to place."""
    
    building_selected = QtCore.Signal(str)  # building_id
    
    def __init__(self, adhd_buster: dict, parent: Optional[QtWidgets.QWidget] = None):
        self.adhd_buster = adhd_buster
        self.selected_building_id = None
        super().__init__(
            parent=parent,
            title="Place Building",
            header_icon="🏗️",
            min_width=500,
            max_width=700,
        )
    
    def _build_content(self, content_layout: QtWidgets.QVBoxLayout):
        """Build the building selection UI."""
        # Header info
        slots = get_available_slots(self.adhd_buster)
        header = QtWidgets.QLabel(f"🏠 Available slots: {slots}")
        header.setStyleSheet("color: #FFD700; font-size: 14px; margin-bottom: 10px;")
        content_layout.addWidget(header)
        
        # Scrollable area for buildings
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(400)
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
        
        placed = get_placed_buildings(self.adhd_buster)
        
        for building_id, building in CITY_BUILDINGS.items():
            can, reason = can_place_building(self.adhd_buster, building_id)
            is_placed = building_id in placed
            
            # Building card
            card = self._create_building_card(building_id, building, can, is_placed, reason)
            scroll_layout.addWidget(card)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        content_layout.addWidget(scroll)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        self.place_btn = QtWidgets.QPushButton("Place Building")
        self.place_btn.setEnabled(False)
        self.place_btn.clicked.connect(self._on_place)
        self.place_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background: #555;
                color: #888;
            }
            QPushButton:hover:!disabled {
                background: #66BB6A;
            }
        """)
        button_layout.addWidget(self.place_btn)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #555;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #666;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        content_layout.addLayout(button_layout)
    
    def _create_building_card(
        self, 
        building_id: str, 
        building: Dict, 
        can_place: bool, 
        is_placed: bool,
        reason: str
    ) -> QtWidgets.QFrame:
        """Create a card for a single building."""
        card = QtWidgets.QFrame()
        card.setProperty("building_id", building_id)
        
        # Style based on availability
        if is_placed:
            bg = "#2A2A3A"
            border = "#555"
        elif can_place:
            bg = "#1A3A2A"
            border = "#4CAF50"
        else:
            bg = "#2A2A3A"
            border = "#444"
        
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
            # Fallback to emoji
            name = building.get("name", "🏛️")
            icon = name.split()[0] if name else "🏛️"
            icon_label.setText(icon)
            icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        layout.addWidget(icon_label)
        
        # Info column
        info_layout = QtWidgets.QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QtWidgets.QLabel(building.get("name", building_id))
        name_label.setStyleSheet("color: #FFD700; font-size: 14px; font-weight: bold;")
        info_layout.addWidget(name_label)
        
        desc_label = QtWidgets.QLabel(building.get("description", "")[:80])
        desc_label.setStyleSheet("color: #AAA; font-size: 11px;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        # Requirements
        reqs = building.get("requirements", {})
        req_parts = []
        for res, amt in reqs.items():
            icon_char = RESOURCE_ICONS.get(res, "📦")
            req_parts.append(f"{icon_char}{amt}")
        if req_parts:
            req_label = QtWidgets.QLabel(" ".join(req_parts))
            req_label.setStyleSheet("color: #888; font-size: 11px;")
            info_layout.addWidget(req_label)
        
        layout.addLayout(info_layout, 1)
        
        # Status indicator
        if is_placed:
            status_label = QtWidgets.QLabel("✓ Placed")
            status_label.setStyleSheet("color: #888; font-size: 11px;")
            layout.addWidget(status_label)
        elif not can_place:
            status_label = QtWidgets.QLabel(reason[:30])
            status_label.setStyleSheet("color: #F44336; font-size: 11px;")
            layout.addWidget(status_label)
        
        # Make clickable if can place
        if can_place and not is_placed:
            card.setCursor(QtCore.Qt.PointingHandCursor)
            card.mousePressEvent = lambda e, bid=building_id: self._select_building(bid)
        
        return card
    
    def _select_building(self, building_id: str):
        """Handle building selection."""
        self.selected_building_id = building_id
        self.place_btn.setEnabled(True)
        
        # Pre-compute placed buildings and placeable status once
        placed_buildings = set(get_placed_buildings(self.adhd_buster))
        placeable_cache = {
            bid: can_place_building(self.adhd_buster, bid)[0]
            for bid in CITY_BUILDINGS.keys()
            if bid not in placed_buildings
        }
        
        # Update visual selection (highlight selected card)
        for child in self.findChildren(QtWidgets.QFrame):
            bid = child.property("building_id")
            if not bid:
                continue
            
            if bid == building_id:
                child.setStyleSheet("""
                    QFrame {
                        background: #2A4A3A;
                        border: 2px solid #FFD700;
                        border-radius: 8px;
                        padding: 8px;
                    }
                """)
            elif bid in placed_buildings:
                child.setStyleSheet("QFrame { background: #2A2A3A; border: 1px solid #555; border-radius: 8px; padding: 8px; }")
            elif placeable_cache.get(bid, False):
                child.setStyleSheet("QFrame { background: #1A3A2A; border: 1px solid #4CAF50; border-radius: 8px; padding: 8px; }")
            else:
                child.setStyleSheet("QFrame { background: #2A2A3A; border: 1px solid #444; border-radius: 8px; padding: 8px; }")
    
    def _on_place(self):
        """Handle place button click."""
        if self.selected_building_id:
            self.building_selected.emit(self.selected_building_id)
            self.accept()


# ============================================================================
# INITIATE CONSTRUCTION DIALOG (For PLACED buildings - pay materials upfront)
# ============================================================================

class InitiateConstructionDialog(StyledDialog):
    """
    Dialog to initiate construction on a PLACED building.
    
    NEW FLOW:
    1. User pays Water + Materials upfront to START construction
    2. Building becomes "under construction" (active_construction)
    3. Activity + Focus earned from activities flow automatically to it
    4. When effort requirements are met, building completes
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
            btn_layout.addWidget(start_btn)
        else:
            # Show why can't initiate
            reason_label = QtWidgets.QLabel(f"⚠️ {reason}")
            reason_label.setStyleSheet("color: #FF9800; font-size: 12px;")
            content_layout.addWidget(reason_label)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
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
        btn_layout.addWidget(cancel_btn)
        
        content_layout.addLayout(btn_layout)
    
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
        
        hint_title = QtWidgets.QLabel("💡 How to Contribute Effort:")
        hint_title.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 12px;")
        hint_layout.addWidget(hint_title)
        
        activity_hint = QtWidgets.QLabel(
            "🏃 <b>Activity</b>: Go to Activities tab → Log any physical activity\n"
            "    💪 Longer + more intense = more Activity points!"
        )
        activity_hint.setStyleSheet("color: #CCC; font-size: 11px;")
        hint_layout.addWidget(activity_hint)
        
        focus_hint = QtWidgets.QLabel(
            "🎯 <b>Focus</b>: Go to Focus tab → Start a focus session\n"
            "    (each 30-minute block earns +1 Focus)"
        )
        focus_hint.setStyleSheet("color: #CCC; font-size: 11px;")
        hint_layout.addWidget(focus_hint)
        
        content_layout.addWidget(hint_frame)
        
        content_layout.addSpacing(15)
        
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
        content_layout.addWidget(close_btn, alignment=QtCore.Qt.AlignCenter)


# Keep legacy name for backward compatibility
ConstructionDialog = InitiateConstructionDialog


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
        content_layout.addWidget(level_label)
        
        # Description
        desc = QtWidgets.QLabel(self.building.get("description", ""))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #AAA; margin: 10px 0;")
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
        if effect_type == "passive_income":
            effect_text = f"• Coins/Hour: +{current_value:.1f}"
        else:
            effect_text = f"• {effect_type.replace('_', ' ').title()}: +{current_value:.0f}%"
        effect_label = QtWidgets.QLabel(effect_text)
        effect_label.setStyleSheet("color: #CCC;")
        effects_layout.addWidget(effect_label)
        
        # Synergy bonus - use calculate_building_synergy_bonus for building-specific bonus
        synergy_result = calculate_building_synergy_bonus(self.building_id, self.adhd_buster)
        synergy_bonus = synergy_result.get("bonus_percent", 0)
        if synergy_bonus > 0:
            synergy_text = f"• Entity Synergy: +{synergy_bonus*100:.0f}%"
            synergy_label = QtWidgets.QLabel(synergy_text)
            synergy_label.setStyleSheet("color: #BA68C8;")
            effects_layout.addWidget(synergy_label)
        
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
            upgrade_layout.addWidget(upgrade_title)
            
            # Requirements
            req_parts = []
            for res, amt in next_reqs.items():
                icon = RESOURCE_ICONS.get(res, "📦")
                req_parts.append(f"{icon} {amt}")
            req_label = QtWidgets.QLabel("Requires: " + "  ".join(req_parts))
            req_label.setStyleSheet("color: #888;")
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
                f"Upgrading {self.building.get('name')}!\n\nInvest resources to complete."
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
        
        # Timer for auto-refreshing pending income display
        self._income_timer = QtCore.QTimer(self)
        self._income_timer.timeout.connect(self._update_pending_income_display)
        
        self._setup_ui()
        self._refresh_city()
    
    def _setup_ui(self):
        """Set up the main tab UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Header with title and info
        header_layout = QtWidgets.QHBoxLayout()
        
        title = QtWidgets.QLabel("🏰 Your City")
        title.setStyleSheet("color: #FFD700; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Building slots indicator
        self.slots_label = QtWidgets.QLabel()
        self.slots_label.setStyleSheet("color: #AAA; font-size: 14px;")
        header_layout.addWidget(self.slots_label)
        
        # Collect income button
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
        header_layout.addWidget(self.collect_btn)
        
        # Help button
        help_btn = QtWidgets.QPushButton("?")
        help_btn.setFixedSize(28, 28)
        help_btn.clicked.connect(self._show_help)
        help_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                color: #FFD700;
                border-radius: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #444;
            }
        """)
        header_layout.addWidget(help_btn)
        
        layout.addLayout(header_layout)
        
        # Resource bar
        self.resource_bar = ResourceBar()
        layout.addWidget(self.resource_bar)
        
        # Active construction indicator (hidden when no active build)
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
        
        # City grid in center
        grid_container = QtWidgets.QWidget()
        grid_container.setStyleSheet("""
            QWidget {
                background: #0D0D1A;
                border: 2px solid #333;
                border-radius: 12px;
            }
        """)
        grid_layout = QtWidgets.QHBoxLayout(grid_container)
        grid_layout.addStretch()
        
        self.city_grid = CityGrid()
        self.city_grid.cell_clicked.connect(self._on_cell_clicked)
        grid_layout.addWidget(self.city_grid)
        
        grid_layout.addStretch()
        layout.addWidget(grid_container, 1)
        
        # Bottom info panel
        self.info_panel = QtWidgets.QLabel()
        self.info_panel.setStyleSheet("color: #888; font-size: 12px;")
        self.info_panel.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.info_panel)
    
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
            
            # Update slots display
            placed = len(get_placed_buildings(self.adhd_buster))
            level = get_level_from_xp(self.adhd_buster.get("total_xp", 0))[0]
            max_slots = get_max_building_slots(level)
            self.slots_label.setText(f"🏠 {placed}/{max_slots} Buildings")
            
            # Update active construction indicator
            self._update_construction_indicator()
            
            # Update pending income
            pending = get_pending_income(self.adhd_buster)
            if pending.get("coins", 0) > 0:
                self.info_panel.setText(
                    f"⏰ Pending income: {pending['coins']} coins ({pending['hours_elapsed']:.1f}h)"
                )
            else:
                active = get_active_construction(self.adhd_buster)
                if active:
                    self.info_panel.setText("🔨 Building in progress - keep up the activities!")
                else:
                    self.info_panel.setText("Click an empty cell to place a building")
        except Exception as e:
            _logger.exception("Error refreshing city display")
            self.info_panel.setText(f"⚠️ Display error: {e}")
    
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
        except Exception as e:
            _logger.exception("Error refreshing city display")
            self.info_panel.setText(f"⚠️ Display error: {e}")
    
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
        except Exception as e:
            _logger.exception(f"Error accessing grid at ({row}, {col})")
            return
        
        try:
            if cell is None:
                # Empty cell - show building picker
                dialog = BuildingPickerDialog(self.adhd_buster, self)
                # Capture row/col by value to prevent closure issues
                r, c = row, col
                dialog.building_selected.connect(lambda bid, r=r, c=c: self._place_building(r, c, bid))
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
                    # Placed but not started - show initiate construction dialog
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
    
    def _show_help(self):
        """Show help dialog."""
        QtWidgets.QMessageBox.information(
            self,
            "City Builder Help",
            "<h3>🏰 City Building System</h3>"
            
            "<p><b>📋 How Construction Works:</b></p>"
            "<ol>"
            "<li><b>Place</b> - Click an empty cell to choose a building</li>"
            "<li><b>Start</b> - Pay 💧 Water + 🧱 Materials upfront to begin</li>"
            "<li><b>Build</b> - Earn 🏃 Activity + 🎯 Focus through your habits</li>"
            "<li><b>Complete</b> - Building finishes when effort requirements are met!</li>"
            "</ol>"
            
            "<hr>"
            "<p><b>💰 Stockpile Resources</b> (Accumulate for Future Use):</p>"
            "<ul>"
            "<li>💧 <b>Water</b>: Log glasses in Hydration tab → accumulates in reserve</li>"
            "<li>🧱 <b>Materials</b>: Log weight in Body tab → accumulates in reserve</li>"
            "</ul>"
            "<p><i>These resources are paid UPFRONT when you start a new building.</i></p>"
            
            "<p><b>🧱 How to Earn Materials (Weight Logging):</b></p>"
            "<table border='1' cellpadding='4' style='border-collapse: collapse;'>"
            "<tr style='background:#2A2A3A;'>"
            "<td><b>Your Goal</b></td><td><b>Achievement</b></td><td><b>Reward</b></td></tr>"
            "<tr><td>📉 Lose weight</td><td>Log weight lower than before</td><td>+2 🧱</td></tr>"
            "<tr><td>📈 Gain weight</td><td>Log weight higher than before</td><td>+2 🧱</td></tr>"
            "<tr><td>⚖️ Maintain</td><td>Stay within healthy BMI (18.5-25)</td><td>+2 🧱</td></tr>"
            "</table>"
            "<p><i>All goals reward equally - just stay on track!</i></p>"
            
            "<p><b>⚡ Effort Resources</b> (Flow Directly to Building):</p>"
            "<ul>"
            "<li>🏃 <b>Activity</b>: Log physical activities → goes to active construction</li>"
            "<li>🎯 <b>Focus</b>: Complete focus sessions → goes to active construction</li>"
            "</ul>"
            
            "<p><i>⚠️ Important: Activity and Focus only count when you have<br>"
            "a building under construction! Start a building first.</i></p>"
            
            "<hr>"
            "<p><b>🔨 One Building at a Time:</b><br>"
            "Only one building can be under active construction.<br>"
            "Complete it to start the next one!</p>"
            
            "<p><b>🏠 Building Slots:</b> Unlock more slots by leveling up!</p>"
            
            "<p><b>✨ Synergies:</b> Collected entities matching a building theme<br>"
            "provide bonus multipliers to that building's output.</p>"
        )
    
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
