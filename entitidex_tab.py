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

# Path to entity SVGs
ENTITY_ICONS_PATH = Path(__file__).parent / "icons" / "entities"


class SilhouetteSvgWidget(QtWidgets.QWidget):
    """
    Custom widget that displays an SVG as a silhouette (black shape).
    Used for uncollected entities to show mysterious appearance.
    """
    
    def __init__(self, svg_path: str, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.renderer = QSvgRenderer(svg_path)
        self.setFixedSize(96, 96)
        
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
    """
    
    clicked = QtCore.Signal(object)  # Emits Entity when clicked
    
    def __init__(self, entity: Entity, is_collected: bool, is_encountered: bool = False, parent=None):
        super().__init__(parent)
        self.entity = entity
        self.is_collected = is_collected
        self.is_encountered = is_encountered
        
        self.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Raised)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self._build_ui()
        
    def _build_ui(self):
        rarity = self.entity.rarity.lower()
        rarity_color = RARITY_COLORS.get(rarity, "#9E9E9E")
        
        # Card styling based on collection status
        if self.is_collected:
            bg_color = "#2D2D2D"
            border_color = rarity_color
        else:
            bg_color = "#1A1A1A"
            border_color = "#333333"
        
        self.setStyleSheet(f"""
            EntityCard {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 10px;
                padding: 5px;
            }}
            EntityCard:hover {{
                border: 2px solid {'#FFD700' if self.is_collected else '#555555'};
            }}
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Entity icon
        svg_filename = f"{self.entity.id}.svg"
        svg_path = str(ENTITY_ICONS_PATH / svg_filename)
        
        icon_container = QtWidgets.QWidget()
        icon_layout = QtWidgets.QHBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addStretch()
        
        if os.path.exists(svg_path):
            if self.is_collected:
                # Full color SVG for collected
                icon_widget = QSvgWidget(svg_path)
                icon_widget.setFixedSize(96, 96)
            else:
                # Silhouette for uncollected
                icon_widget = SilhouetteSvgWidget(svg_path)
        else:
            # Placeholder if no SVG
            icon_widget = QtWidgets.QLabel("❓")
            icon_widget.setAlignment(QtCore.Qt.AlignCenter)
            icon_widget.setFixedSize(96, 96)
            icon_widget.setStyleSheet("font-size: 48px;")
        
        icon_layout.addWidget(icon_widget)
        icon_layout.addStretch()
        layout.addWidget(icon_container)
        
        # Entity name
        if self.is_collected:
            name_text = self.entity.name
            name_color = rarity_color
        elif self.is_encountered:
            name_text = "???"
            name_color = "#666666"
        else:
            name_text = "???"
            name_color = "#444444"
        
        name_label = QtWidgets.QLabel(name_text)
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {name_color};
                font-weight: bold;
                font-size: 11px;
            }}
        """)
        layout.addWidget(name_label)
        
        # Power display
        if self.is_collected:
            power_text = f"⚡ {self.entity.power}"
            power_color = "#FFD700"
        else:
            power_text = "⚡ ???"
            power_color = "#444444"
        
        power_label = QtWidgets.QLabel(power_text)
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setStyleSheet(f"color: {power_color}; font-size: 10px;")
        layout.addWidget(power_label)
        
        # Rarity badge
        if self.is_collected:
            rarity_text = rarity.upper()
            rarity_bg = rarity_color
        else:
            rarity_text = "???"
            rarity_bg = "#333333"
        
        rarity_label = QtWidgets.QLabel(rarity_text)
        rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        rarity_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                background: {rarity_bg};
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(rarity_label, 0, QtCore.Qt.AlignCenter)
        
        # Collection status indicator
        if self.is_collected:
            status_text = "✅ Collected"
            status_color = "#4CAF50"
        elif self.is_encountered:
            status_text = "👁️ Seen"
            status_color = "#666666"
        else:
            status_text = "❓ Unknown"
            status_color = "#444444"
        
        status_label = QtWidgets.QLabel(status_text)
        status_label.setAlignment(QtCore.Qt.AlignCenter)
        status_label.setStyleSheet(f"color: {status_color}; font-size: 9px;")
        layout.addWidget(status_label)
        
        self.setFixedSize(140, 200)
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.entity)
        super().mousePressEvent(event)


class EntitidexTab(QtWidgets.QWidget):
    """
    Main Entitidex tab showing the entity collection.
    """
    
    def __init__(self, blocker, parent=None):
        super().__init__(parent)
        self.blocker = blocker
        self.current_story = "warrior"
        self.progress = EntitidexProgress()
        
        # Load progress from blocker if available
        self._load_progress()
        
        self._build_ui()
    
    def _load_progress(self):
        """Load entitidex progress from blocker config."""
        try:
            if hasattr(self.blocker, 'adhd_buster'):
                entitidex_data = self.blocker.adhd_buster.get("entitidex", {})
                if entitidex_data:
                    collected = set(entitidex_data.get("collected", []))
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
                    "collected": list(self.progress.collected_entity_ids),
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
        
        # Story selector
        story_label = QtWidgets.QLabel("Story Theme:")
        story_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        header_layout.addWidget(story_label)
        
        self.story_combo = QtWidgets.QComboBox()
        self.story_combo.addItems(["warrior", "scholar", "underdog", "scientist", "wanderer"])
        self.story_combo.setCurrentText(self.current_story)
        self.story_combo.currentTextChanged.connect(self._on_story_changed)
        self.story_combo.setStyleSheet("""
            QComboBox {
                background: #2D2D2D;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px 10px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #2D2D2D;
                color: white;
                selection-background-color: #4CAF50;
            }
        """)
        header_layout.addWidget(self.story_combo)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_frame = QtWidgets.QFrame()
        self.progress_frame.setStyleSheet("""
            QFrame {
                background: #1E1E1E;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        progress_layout = QtWidgets.QVBoxLayout(self.progress_frame)
        
        self.progress_label = QtWidgets.QLabel("Collection Progress")
        self.progress_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
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
        progress_layout.addWidget(self.progress_bar)
        
        # Stats row
        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setAlignment(QtCore.Qt.AlignCenter)
        self.stats_label.setStyleSheet("color: #888888; font-size: 11px;")
        progress_layout.addWidget(self.stats_label)
        
        layout.addWidget(self.progress_frame)
        
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
        
        self.cards_container = QtWidgets.QWidget()
        self.cards_layout = QtWidgets.QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(15)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
        
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
        self._refresh_display()
    
    def _on_story_changed(self, story: str):
        self.current_story = story
        self._refresh_display()
    
    def _refresh_display(self):
        """Refresh the entity grid display."""
        # Clear existing cards
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Get entities for current story
        entities = get_entities_for_story(self.current_story)
        
        # Sort by power (progression order)
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
        
        # Update progress display
        self.progress_bar.setValue(progress_percent)
        self.progress_bar.setFormat(f"{collected_count}/{total} ({progress_percent}%)")
        self.progress_label.setText(f"Collection Progress - {self.current_story.capitalize()}")
        self.stats_label.setText(
            f"✅ Collected: {collected_count}  |  "
            f"👁️ Encountered: {encountered_count}  |  "
            f"❓ Unknown: {total - collected_count - encountered_count}"
        )
        
        # Create cards
        cols = 5  # Cards per row
        for i, entity in enumerate(entities_sorted):
            row = i // cols
            col = i % cols
            
            is_collected = self.progress.is_collected(entity.id)
            is_encountered = self.progress.is_encountered(entity.id)
            
            card = EntityCard(entity, is_collected, is_encountered)
            card.clicked.connect(self._on_entity_clicked)
            self.cards_layout.addWidget(card, row, col)
    
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
        self._refresh_display()
    
    def add_encountered_entity(self, entity_id: str):
        """Mark an entity as encountered and refresh display."""
        self.progress.record_encounter(entity_id)
        self._save_progress()
        self._refresh_display()
    
    def refresh(self):
        """Public method to refresh the display."""
        self._load_progress()
        self._refresh_display()
