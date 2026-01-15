"""
Entitidex Tab - Collection viewer for entity companions.

Shows all entities in the current story theme with:
- Full details for collected entities
- Silhouettes for uncollected entities (mysterious appearance)
"""

import os
from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtSvg import QSvgRenderer

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


def _resolve_entity_svg_path(entity: Entity) -> Optional[str]:
    """
    Resolve the SVG path for an entity using multiple strategies.
    
    SVG files are named: {id}_{name_snake_case}.svg
    e.g., warrior_003_battle_falcon_swift.svg
    """
    # Strategy 1: Try entity's icon_path if provided
    if entity.icon_path and os.path.exists(entity.icon_path):
        return entity.icon_path
    
    # Strategy 2: Try filename pattern {id}_{name_snake_case}.svg
    name_snake = entity.name.lower().replace(" ", "_").replace("-", "_").replace("'", "")
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


class SilhouetteSvgWidget(QtWidgets.QWidget):
    """
    Custom widget that displays an SVG as a silhouette (black shape).
    Used for uncollected entities to show mysterious appearance.
    Size: 128x128 to match preview cards.
    """
    
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.renderer = QSvgRenderer(svg_path)
        self.setFixedSize(128, 128)
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Create a pixmap from the SVG
        pixmap = QtGui.QPixmap(self.size())
        pixmap.fill(QtCore.Qt.transparent)
        
        svg_painter = QtGui.QPainter(pixmap)
        self.renderer.render(svg_painter)
        svg_painter.end()
        
        # Convert to image and make silhouette
        image = pixmap.toImage()
        
        # Create silhouette by making all non-transparent pixels dark
        for x in range(image.width()):
            for y in range(image.height()):
                pixel = image.pixelColor(x, y)
                if pixel.alpha() > 0:
                    # Make it a dark silhouette with slight transparency
                    image.setPixelColor(x, y, QtGui.QColor(30, 30, 40, min(pixel.alpha(), 200)))
        
        # Draw the silhouette
        painter.drawImage(0, 0, image)
        painter.end()


class EntityCard(QtWidgets.QFrame):
    """
    Card widget for displaying a single entity.
    Shows full details if collected, silhouette if not.
    Uses the same layout as preview_entities.py (180x220 with 128x128 SVG).
    """
    
    clicked = QtCore.Signal(object)  # Emits Entity when clicked
    
    def __init__(self, entity: Entity, is_collected: bool, is_encountered: bool = False, parent=None):
        super().__init__(parent)
        self.entity = entity
        self.is_collected = is_collected
        self.is_encountered = is_encountered
        
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)
        self.setLineWidth(2)  # Match preview_entities.py
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self._build_ui()
        
    def _build_ui(self):
        rarity = self.entity.rarity.lower()
        rarity_color = RARITY_COLORS.get(rarity, "#9E9E9E")
        
        # Card styling based on collection status - gradient background with rarity border
        if self.is_collected:
            # Gradient from darker center to slightly lighter edges matching rarity
            bg_base = RARITY_BG.get(rarity, "#2D2D2D")
            border_color = rarity_color
            # Create radial gradient effect with darker center
            gradient_start = "#0D0D0D"  # Very dark center
            gradient_end = bg_base  # Rarity-tinted outer
        else:
            # Darker, mysterious look for uncollected
            gradient_start = "#080808"
            gradient_end = "#1A1A1A"
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
                border: 3px solid {'#FFD700' if self.is_collected else '#444444'};
                background: qradialgradient(
                    cx: 0.5, cy: 0.5, radius: 0.8,
                    fx: 0.5, fy: 0.5,
                    stop: 0 {'#151515' if self.is_collected else '#101010'},
                    stop: 1 {gradient_end if self.is_collected else '#222222'}
                );
            }}
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Entity icon - resolve SVG path properly
        svg_path = _resolve_entity_svg_path(self.entity)
        
        # Center the SVG (matching preview_entities.py layout)
        svg_container = QtWidgets.QWidget()
        svg_layout = QtWidgets.QHBoxLayout(svg_container)
        svg_layout.addStretch()
        svg_layout.setContentsMargins(0, 0, 0, 0)
        
        if svg_path and os.path.exists(svg_path):
            if self.is_collected:
                # Full color SVG for collected - 128x128 like preview cards
                icon_widget = QSvgWidget(svg_path)
                icon_widget.setFixedSize(128, 128)
                icon_widget.setStyleSheet("background: transparent;")
            else:
                # Silhouette for uncollected - also 128x128
                icon_widget = SilhouetteSvgWidget(svg_path)
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
        if self.is_collected:
            name_text = self.entity.name
            name_color = rarity_color
        elif self.is_encountered:
            name_text = "???"
            name_color = "#555555"
        else:
            name_text = "???"
            name_color = "#333333"
        
        name_label = QtWidgets.QLabel(name_text)
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setFont(QtGui.QFont("Segoe UI", 9, QtGui.QFont.Bold))
        name_label.setStyleSheet(f"color: {name_color}; background: transparent;")
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
            rarity_text = rarity.upper()
            rarity_label_color = rarity_color
        else:
            rarity_text = "???"
            rarity_label_color = "#333333"
        
        rarity_label = QtWidgets.QLabel(rarity_text)
        rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        rarity_label.setFont(QtGui.QFont("Segoe UI", 9, QtGui.QFont.Bold))
        rarity_label.setStyleSheet(f"color: {rarity_label_color}; background: transparent;")
        layout.addWidget(rarity_label)
        
        # Match preview_entities.py card size: 180x220
        self.setFixedSize(180, 220)
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.entity)
        super().mousePressEvent(event)


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
    """
    
    def __init__(self, blocker, parent=None):
        super().__init__(parent)
        self.blocker = blocker
        self.current_story = "warrior"
        self.progress = EntitidexProgress()
        self.theme_tabs = {}  # Store references to theme tab widgets
        
        # Load progress from blocker if available
        self._load_progress()
        
        self._build_ui()
    
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
                    self.progress.collected_entity_ids = collected
                    self.progress.encounters = encounters
        except Exception as e:
            print(f"Error loading entitidex progress: {e}")
    
    def _save_progress(self):
        """Save entitidex progress to blocker config."""
        try:
            if hasattr(self.blocker, 'adhd_buster'):
                self.blocker.adhd_buster["entitidex"] = {
                    "collected_entity_ids": list(self.progress.collected_entity_ids),
                    "encounters": self.progress.encounters,
                }
                self.blocker.save_config()
        except Exception as e:
            print(f"Error saving entitidex progress: {e}")
    
    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
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
        
        # Detail panel (shown when entity is clicked)
        self.detail_panel = QtWidgets.QFrame()
        self.detail_panel.setStyleSheet("""
            QFrame {
                background: #1E1E1E;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        self.detail_panel.setVisible(False)
        
        detail_layout = QtWidgets.QVBoxLayout(self.detail_panel)
        
        self.detail_name = QtWidgets.QLabel()
        self.detail_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.detail_name.setAlignment(QtCore.Qt.AlignCenter)
        detail_layout.addWidget(self.detail_name)
        
        self.detail_lore = QtWidgets.QLabel()
        self.detail_lore.setWordWrap(True)
        self.detail_lore.setStyleSheet("color: #CCCCCC; font-size: 12px; padding: 10px;")
        self.detail_lore.setAlignment(QtCore.Qt.AlignCenter)
        detail_layout.addWidget(self.detail_lore)
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #444;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: #555;
            }
        """)
        close_btn.clicked.connect(lambda: self.detail_panel.setVisible(False))
        detail_layout.addWidget(close_btn, 0, QtCore.Qt.AlignCenter)
        
        layout.addWidget(self.detail_panel)
        
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
        cards_layout = QtWidgets.QGridLayout(cards_container)
        cards_layout.setSpacing(16)
        cards_layout.setContentsMargins(16, 16, 16, 16)
        
        scroll.setWidget(cards_container)
        tab_layout.addWidget(scroll)
        
        return tab_container
    
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
        
        # Clear existing cards
        while cards_layout.count():
            child = cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Get entities for this theme
        entities = get_entities_for_story(theme_key)
        entities_sorted = sorted(entities, key=lambda e: e.power)
        
        # Calculate progress
        collected_count = 0
        encountered_count = 0
        
        for entity in entities_sorted:
            if self.progress.is_collected(entity.id):
                collected_count += 1
            elif self.progress.is_encountered(entity.id):
                encountered_count += 1
        
        total = len(entities_sorted)
        progress_percent = int((collected_count / total) * 100) if total > 0 else 0
        
        # Update progress display for this tab
        progress_bar = tab_widget.findChild(QtWidgets.QProgressBar, f"progress_bar_{theme_key}")
        if progress_bar:
            progress_bar.setValue(progress_percent)
            progress_bar.setFormat(f"{collected_count}/{total} ({progress_percent}%)")
        
        stats_label = tab_widget.findChild(QtWidgets.QLabel, f"stats_label_{theme_key}")
        if stats_label:
            stats_label.setText(
                f"✅ Collected: {collected_count}  |  "
                f"👁️ Encountered: {encountered_count}  |  "
                f"❓ Unknown: {total - collected_count - encountered_count}"
            )
        
        # Create cards - 5 columns like preview_entities.py
        cols = 5
        for i, entity in enumerate(entities_sorted):
            row = i // cols
            col = i % cols
            
            is_collected = self.progress.is_collected(entity.id)
            is_encountered = self.progress.is_encountered(entity.id)
            
            card = EntityCard(entity, is_collected, is_encountered)
            card.clicked.connect(self._on_entity_clicked)
            cards_layout.addWidget(card, row, col)
    
    def _refresh_all_tabs(self):
        """Refresh all theme tabs and update total progress."""
        total_collected = 0
        total_entities = 0
        
        for theme_key in THEME_INFO.keys():
            self._refresh_theme_tab(theme_key)
            
            # Count for total progress
            entities = get_entities_for_story(theme_key)
            total_entities += len(entities)
            for entity in entities:
                if self.progress.is_collected(entity.id):
                    total_collected += 1
        
        # Update total progress label
        total_percent = int((total_collected / total_entities) * 100) if total_entities > 0 else 0
        self.total_progress_label.setText(f"Total: {total_collected}/{total_entities} ({total_percent}%)")
    
    def _on_story_changed(self, story: str):
        """Legacy method - kept for compatibility."""
        self.current_story = story
        # Find and select the corresponding tab
        theme_keys = list(THEME_INFO.keys())
        if story in theme_keys:
            self.theme_tab_widget.setCurrentIndex(theme_keys.index(story))
    
    def _on_entity_clicked(self, entity: Entity):
        """Handle entity card click - show details if collected."""
        if self.progress.is_collected(entity.id):
            rarity_color = RARITY_COLORS.get(entity.rarity.lower(), "#9E9E9E")
            self.detail_name.setText(f"{entity.name}")
            self.detail_name.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {rarity_color};")
            self.detail_lore.setText(entity.lore)
            self.detail_panel.setVisible(True)
        else:
            # Show hint for uncollected
            self.detail_name.setText("??? Unknown Entity")
            self.detail_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #666666;")
            if self.progress.is_encountered(entity.id):
                self.detail_lore.setText("You've seen this entity before, but haven't bonded yet.\nComplete focus sessions to encounter it again!")
            else:
                self.detail_lore.setText("This entity awaits discovery.\nComplete focus sessions to encounter new companions!")
            self.detail_panel.setVisible(True)
    
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
