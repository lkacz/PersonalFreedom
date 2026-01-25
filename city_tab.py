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

from app_utils import get_app_dir
from styled_dialog import StyledDialog, add_tab_help_button
from gamification import get_level_from_xp

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
        DEMOLISH_REFUND_PERCENT,
        get_city_data,
        get_city_bonuses,
        add_city_resource,
        get_resources,
        can_place_building,
        place_building,
        remove_building,
        invest_resources,
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
    DEMOLISH_REFUND_PERCENT = 50
    
    # Stub functions that do nothing
    def get_city_data(adhd_buster): return {"grid": [[None]*5 for _ in range(5)], "resources": {}}
    def get_city_bonuses(adhd_buster): return {}
    def add_city_resource(adhd_buster, res, amt): return 0
    def get_resources(adhd_buster): return {}
    def can_place_building(adhd_buster, bid): return (False, "City system not available")
    def place_building(adhd_buster, r, c, bid): return False
    def remove_building(adhd_buster, r, c): return None
    def invest_resources(adhd_buster, r, c, inv): return {}
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
    """
    
    clicked = QtCore.Signal(int, int)  # row, col
    
    def __init__(self, row: int, col: int, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self._cell_state = None
        self._building_def = None
        
        self.setMinimumSize(64, 64)
        self.setMaximumSize(80, 80)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        
        self._setup_ui()
        self._apply_empty_style()
    
    def _setup_ui(self):
        """Set up the cell's internal UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Building icon (SVG or emoji)
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setAlignment(QtCore.Qt.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.icon_label, 1)
        
        # Progress/level bar at bottom
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
    
    def _apply_empty_style(self):
        """Style for empty cell."""
        self.setStyleSheet(f"""
            CityCell {{
                background: {STATUS_COLORS.get('empty', '#2A2A3A')};
                border: 1px dashed #555;
                border-radius: 8px;
            }}
            CityCell:hover {{
                background: #3A3A5A;
                border: 1px solid #777;
            }}
        """)
        self.icon_label.setText("➕")
        self.icon_label.setStyleSheet("font-size: 20px; color: #555;")
        self.progress_bar.hide()
    
    def _apply_building_style(self, status: str):
        """Style for cell with building."""
        bg_color = STATUS_COLORS.get(status, "#2A2A3A")
        border_color = "#FFD700" if status == CellStatus.COMPLETE.value else "#888"
        
        self.setStyleSheet(f"""
            CityCell {{
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            CityCell:hover {{
                border: 2px solid #FFF;
            }}
        """)
    
    def set_cell_state(self, cell_state: Optional[Dict], building_def: Optional[Dict] = None):
        """Update cell to reflect current state."""
        self._cell_state = cell_state
        self._building_def = building_def
        
        if cell_state is None:
            self._apply_empty_style()
            return
        
        status = cell_state.get("status", "")
        building_id = cell_state.get("building_id", "")
        level = cell_state.get("level", 1)
        
        # Apply status-based style
        self._apply_building_style(status)
        
        # Set building icon
        if building_def:
            # Icon emoji is at the start of name field (e.g. "⛏️ Goldmine")
            name = building_def.get("name", "🏛️")
            icon_char = name.split()[0] if name else "🏛️"
            self.icon_label.setText(icon_char)
            self.icon_label.setStyleSheet("font-size: 28px; background: transparent;")
            
            # Show level badge if complete
            if status == CellStatus.COMPLETE.value and level > 1:
                self.icon_label.setText(f"{icon_char}\n★{level}")
                self.icon_label.setStyleSheet("font-size: 18px; color: #FFD700; background: transparent;")
        
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

class CityGrid(QtWidgets.QWidget):
    """The 5x5 grid of city cells."""
    
    cell_clicked = QtCore.Signal(int, int)  # row, col
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.cells: list[list[CityCell]] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the grid of cells."""
        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        
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
    
    def update_grid(self, city_data: Dict):
        """Update all cells from city data."""
        if not CITY_AVAILABLE:
            return
        
        grid = city_data.get("grid", [])
        
        for row, row_cells in enumerate(self.cells):
            for col, cell in enumerate(row_cells):
                if row < len(grid) and col < len(grid[row]):
                    cell_state = grid[row][col]
                    building_def = None
                    if cell_state and cell_state.get("building_id"):
                        building_def = CITY_BUILDINGS.get(cell_state["building_id"])
                    cell.set_cell_state(cell_state, building_def)
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
        
        # Icon (extract emoji from start of name)
        name = building.get("name", "🏛️")
        icon = name.split()[0] if name else "🏛️"
        icon_label = QtWidgets.QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setFixedWidth(50)
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
        
        # Update visual selection (highlight selected card)
        # Cache placed buildings and placeable status to avoid repeated calls
        placed_buildings = set(get_placed_buildings(self.adhd_buster))
        placeable_cache = {}
        
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
            else:
                # Reset others - use cached placeable status
                is_placed = bid in placed_buildings
                if is_placed:
                    child.setStyleSheet("QFrame { background: #2A2A3A; border: 1px solid #555; border-radius: 8px; padding: 8px; }")
                else:
                    # Cache the can_place result to avoid repeated calls
                    if bid not in placeable_cache:
                        can, _ = can_place_building(self.adhd_buster, bid)
                        placeable_cache[bid] = can
                    if placeable_cache[bid]:
                        child.setStyleSheet("QFrame { background: #1A3A2A; border: 1px solid #4CAF50; border-radius: 8px; padding: 8px; }")
                    else:
                        child.setStyleSheet("QFrame { background: #2A2A3A; border: 1px solid #444; border-radius: 8px; padding: 8px; }")
    
    def _on_place(self):
        """Handle place button click."""
        if self.selected_building_id:
            self.building_selected.emit(self.selected_building_id)
            self.accept()


# ============================================================================
# CONSTRUCTION DIALOG
# ============================================================================

class ConstructionDialog(StyledDialog):
    """Dialog to invest resources into a building under construction."""
    
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
        self.investment = {res: 0 for res in RESOURCE_TYPES}
        
        city = get_city_data(adhd_buster)
        grid = city.get("grid", [])
        
        # Bounds check for grid access
        def is_valid_cell(r, c):
            return 0 <= r < len(grid) and 0 <= c < len(grid[r])
        
        if not is_valid_cell(row, col):
            _logger.warning(f"Invalid grid cell: ({row}, {col})")
            self.building_id = ""
            self.building = {}
        else:
            cell_state = grid[row][col]
            if cell_state is None:
                _logger.warning(f"Empty cell at ({row}, {col})")
                self.building_id = ""
                self.building = {}
            else:
                self.building_id = cell_state.get("building_id", "")
                self.building = CITY_BUILDINGS.get(self.building_id, {})
        
        super().__init__(
            parent=parent,
            title=f"Build {self.building.get('name', 'Building')}",
            header_icon="🔨",
            min_width=400,
            max_width=500,
        )
    
    def _build_content(self, content_layout: QtWidgets.QVBoxLayout):
        """Build the construction investment UI."""
        # Guard against empty building
        if not self.building_id or not self.building:
            error_label = QtWidgets.QLabel("⚠️ Building data not found")
            error_label.setStyleSheet("color: #F44336; font-size: 14px;")
            content_layout.addWidget(error_label)
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(self.accept)
            content_layout.addWidget(close_btn)
            return
        
        city = get_city_data(self.adhd_buster)
        grid = city.get("grid", [])
        
        # Safe grid access with defaults
        if self.row < len(grid) and self.col < len(grid[self.row]) and grid[self.row][self.col]:
            cell = grid[self.row][self.col]
        else:
            cell = {"level": 1, "construction_progress": {}}
        
        level = cell.get("level", 1)
        progress = cell.get("construction_progress", {})
        
        # Get requirements
        reqs = get_level_requirements(self.building, level)
        resources = get_resources(self.adhd_buster)
        
        # Description
        desc = QtWidgets.QLabel(self.building.get("description", ""))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #AAA; margin-bottom: 15px;")
        content_layout.addWidget(desc)
        
        # Progress overview
        total_needed = sum(reqs.values())
        total_invested = sum(progress.values())
        percent = int((total_invested / max(total_needed, 1)) * 100)
        
        progress_label = QtWidgets.QLabel(f"Progress: {percent}%")
        progress_label.setStyleSheet("color: #FFD700; font-size: 16px; font-weight: bold;")
        content_layout.addWidget(progress_label)
        
        progress_bar = QtWidgets.QProgressBar()
        progress_bar.setValue(percent)
        progress_bar.setMaximumHeight(12)
        progress_bar.setStyleSheet("""
            QProgressBar {
                background: #333;
                border-radius: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #66BB6A);
                border-radius: 6px;
            }
        """)
        content_layout.addWidget(progress_bar)
        
        content_layout.addSpacing(15)
        
        # Resource investment sliders
        self.sliders = {}
        for resource_type in RESOURCE_TYPES:
            needed = reqs.get(resource_type, 0)
            invested = progress.get(resource_type, 0)
            remaining = max(0, needed - invested)
            available = resources.get(resource_type, 0)
            max_invest = min(remaining, available)
            
            if needed == 0 and invested == 0:
                continue  # Skip resources not needed
            
            row_widget = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            # Resource icon and label
            icon = RESOURCE_ICONS.get(resource_type, "📦")
            color = RESOURCE_COLORS.get(resource_type, "#CCC")
            label = QtWidgets.QLabel(f"{icon} {resource_type.title()}")
            label.setStyleSheet(f"color: {color}; font-weight: bold; min-width: 100px;")
            row_layout.addWidget(label)
            
            # Progress: invested/needed
            status = QtWidgets.QLabel(f"{invested}/{needed}")
            status.setStyleSheet("color: #888; min-width: 50px;")
            row_layout.addWidget(status)
            
            # Slider
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(max_invest)
            slider.setValue(0)
            slider.setEnabled(max_invest > 0)
            row_layout.addWidget(slider, 1)
            
            # Value display
            value_label = QtWidgets.QLabel("0")
            value_label.setStyleSheet("color: #4CAF50; font-weight: bold; min-width: 30px;")
            row_layout.addWidget(value_label)
            
            self.sliders[resource_type] = (slider, value_label)
            
            # Connect slider
            slider.valueChanged.connect(
                lambda v, rt=resource_type, vl=value_label: self._on_slider_changed(rt, v, vl)
            )
            
            content_layout.addWidget(row_widget)
        
        content_layout.addSpacing(15)
        
        # Quick invest buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        invest_all_btn = QtWidgets.QPushButton("Invest All Available")
        invest_all_btn.clicked.connect(self._invest_all)
        invest_all_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #66BB6A;
            }
        """)
        btn_layout.addWidget(invest_all_btn)
        
        confirm_btn = QtWidgets.QPushButton("Invest Selected")
        confirm_btn.clicked.connect(self._confirm_investment)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #42A5F5;
            }
        """)
        btn_layout.addWidget(confirm_btn)
        
        cancel_btn = QtWidgets.QPushButton("Close")
        cancel_btn.clicked.connect(self.accept)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #555;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
            }
        """)
        btn_layout.addWidget(cancel_btn)
        
        content_layout.addLayout(btn_layout)
    
    def _on_slider_changed(self, resource_type: str, value: int, label: QtWidgets.QLabel):
        self.investment[resource_type] = value
        label.setText(str(value))
    
    def _invest_all(self):
        """Set all sliders to max."""
        for resource_type, (slider, label) in self.sliders.items():
            max_val = slider.maximum()
            slider.setValue(max_val)
    
    def _confirm_investment(self):
        """Invest the selected resources."""
        if all(v == 0 for v in self.investment.values()):
            return
        
        result = invest_resources(self.adhd_buster, self.row, self.col, self.investment)
        
        if result.get("completed"):
            QtWidgets.QMessageBox.information(
                self, 
                "Construction Complete!",
                f"🎉 {self.building.get('name', 'Building')} is now complete!\n\nIt will now generate bonuses."
            )
            self.accept()
        elif result.get("success"):
            # Refresh dialog
            self.accept()
            # Could re-open dialog with updated values
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Investment Failed",
                result.get("error", "Unknown error")
            )


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
            QtWidgets.QMessageBox.information(
                self,
                "Upgrade Started",
                f"Upgrading {self.building.get('name')}!\n\nInvest resources to complete."
            )
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Upgrade Failed",
                f"Could not start upgrade for {self.building.get('name')}.\n\nPlease try again."
            )
    
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
                # Parent will handle save via _on_cell_clicked
                pass
            self.accept()


# ============================================================================
# MAIN CITY TAB
# ============================================================================

class CityTab(QtWidgets.QWidget):
    """Main city builder tab widget."""
    
    # Signal to request data save
    request_save = QtCore.Signal()
    
    def __init__(self, adhd_buster: dict, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.adhd_buster = adhd_buster
        self._last_refresh_time = 0  # For throttling refreshes
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
            
            # Update grid
            self.city_grid.update_grid(city)
            
            # Update resources
            resources = get_resources(self.adhd_buster)
            self.resource_bar.update_resources(resources)
            
            # Update slots display
            placed = len(get_placed_buildings(self.adhd_buster))
            level = get_level_from_xp(self.adhd_buster.get("total_xp", 0))[0]
            max_slots = get_max_building_slots(level)
            self.slots_label.setText(f"🏠 {placed}/{max_slots} Buildings")
            
            # Update pending income
            pending = get_pending_income(self.adhd_buster)
            if pending.get("coins", 0) > 0:
                self.info_panel.setText(
                    f"⏰ Pending income: {pending['coins']} coins ({pending['hours_elapsed']:.1f}h)"
                )
            else:
                self.info_panel.setText("Click an empty cell to place a building")
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
                else:
                    # Under construction - show construction dialog
                    dialog = ConstructionDialog(self.adhd_buster, row, col, self)
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
            "<p><b>How to Build:</b></p>"
            "<ol>"
            "<li>Click an empty cell to place a building</li>"
            "<li>Invest resources (💧🧱⚡🎯) to construct</li>"
            "<li>Complete buildings provide passive bonuses</li>"
            "</ol>"
            "<p><b>Earning Resources:</b></p>"
            "<ul>"
            "<li>💧 Water: Stay hydrated, take breaks</li>"
            "<li>🧱 Materials: Complete tasks, earn XP</li>"
            "<li>⚡ Activity: Physical activity, walks</li>"
            "<li>🎯 Focus: Deep work sessions</li>"
            "</ul>"
            "<p><b>Building Slots:</b><br>"
            "Unlock more slots by leveling up!</p>"
            "<p><b>Synergies:</b><br>"
            "Matching entities with buildings provides bonus multipliers.</p>"
        )
    
    def showEvent(self, event: QtGui.QShowEvent):
        """Refresh when tab becomes visible (with throttling)."""
        super().showEvent(event)
        # Throttle refreshes to avoid excessive updates
        current_time = time.time()
        if current_time - self._last_refresh_time > 0.5:  # Max once per 500ms
            self._refresh_city()
            self._last_refresh_time = current_time
