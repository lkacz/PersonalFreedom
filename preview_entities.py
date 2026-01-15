#!/usr/bin/env python3
"""Preview Entity SVG Graphics - View all entity icons in a grid."""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QScrollArea, QFrame, QComboBox, QTabWidget
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtSvgWidgets import QSvgWidget


# Entity data for display
WARRIOR_ENTITIES = [
    ("warrior_001_hatchling_drake.svg", "Hatchling Drake", 10, "common"),
    ("warrior_002_old_training_dummy.svg", "Old Training Dummy", 50, "common"),
    ("warrior_003_battle_falcon_swift.svg", "Battle Falcon Swift", 150, "uncommon"),
    ("warrior_004_war_horse_thunder.svg", "War Horse Thunder", 400, "uncommon"),
    ("warrior_005_dragon_whelp_ember.svg", "Dragon Whelp Ember", 700, "rare"),
    ("warrior_006_battle_standard.svg", "Battle Standard", 1100, "rare"),
    ("warrior_007_battle_dragon_crimson.svg", "Battle Dragon Crimson", 1500, "epic"),
    ("warrior_008_dire_wolf_fenris.svg", "Dire Wolf Fenris", 1800, "epic"),
    ("warrior_009_old_war_ant_general.svg", "Old War Ant General", 2000, "legendary"),
]

SCHOLAR_ENTITIES = [
    ("scholar_001_library_mouse_pip.svg", "Library Mouse Pip", 10, "common"),
    ("scholar_002_study_owl_athena.svg", "Study Owl Athena", 50, "common"),
    ("scholar_003_reading_candle.svg", "Reading Candle", 150, "uncommon"),
    ("scholar_004_library_cat_scholar.svg", "Library Cat Scholar", 400, "uncommon"),
    ("scholar_005_living_bookmark_finn.svg", "Living Bookmark Finn", 700, "rare"),
    ("scholar_006_sentient_tome_magnus.svg", "Sentient Tome Magnus", 1100, "rare"),
    ("scholar_007_ancient_star_map.svg", "Ancient Star Map", 1500, "epic"),
    ("scholar_008_archive_phoenix.svg", "Archive Phoenix", 1800, "epic"),
    ("scholar_009_blank_parchment.svg", "Blank Parchment", 2000, "legendary"),
]

UNDERDOG_ENTITIES = [
    ("underdog_001_office_rat_reginald.svg", "Office Rat Reginald", 10, "common"),
    ("underdog_002_lucky_sticky_note.svg", "Lucky Sticky Note", 50, "common"),
    ("underdog_003_vending_machine_coin.svg", "Vending Machine Coin", 150, "uncommon"),
    ("underdog_004_window_pigeon_winston.svg", "Window Pigeon Winston", 400, "uncommon"),
    ("underdog_005_desk_succulent_sam.svg", "Desk Succulent Sam", 700, "rare"),
    ("underdog_006_break_room_coffee_maker.svg", "Break Room Coffee Maker", 1100, "rare"),
    ("underdog_007_corner_office_chair.svg", "Corner Office Chair", 1500, "epic"),
    ("underdog_008_agi_assistant_chad.svg", "AGI Assistant Chad", 1800, "epic"),
    ("underdog_009_break_room_fridge.svg", "Break Room Fridge", 2000, "legendary"),
]

SCIENTIST_ENTITIES = [
    ("scientist_001_cracked_test_tube.svg", "Cracked Test Tube", 10, "common"),
    ("scientist_002_old_bunsen_burner.svg", "Old Bunsen Burner", 50, "common"),
    ("scientist_003_lucky_petri_dish.svg", "Lucky Petri Dish", 150, "uncommon"),
    ("scientist_004_wise_lab_rat_professor.svg", "Wise Lab Rat Professor", 400, "uncommon"),
    ("scientist_005_vintage_microscope.svg", "Vintage Microscope", 700, "rare"),
    ("scientist_006_bubbling_flask.svg", "Bubbling Flask", 1100, "rare"),
    ("scientist_007_tesla_coil_sparky.svg", "Tesla Coil Sparky", 1500, "epic"),
    ("scientist_008_golden_dna_helix.svg", "Golden DNA Helix", 1800, "epic"),
    ("scientist_009_white_mouse_archimedes.svg", "White Mouse Archimedes", 2000, "legendary"),
]

WANDERER_ENTITIES = [
    ("wanderer_001_lucky_coin.svg", "Lucky Coin", 10, "common"),
    ("wanderer_002_brass_compass.svg", "Brass Compass", 50, "common"),
    ("wanderer_003_journey_journal.svg", "Journey Journal", 150, "uncommon"),
    ("wanderer_004_road_dog_wayfinder.svg", "Road Dog Wayfinder", 400, "uncommon"),
    ("wanderer_005_self_drawing_map.svg", "Self-Drawing Map", 700, "rare"),
    ("wanderer_006_wanderers_carriage.svg", "Wanderer's Carriage", 1100, "rare"),
    ("wanderer_007_timeworn_backpack.svg", "Timeworn Backpack", 1500, "epic"),
    ("wanderer_008_sky_balloon_explorer.svg", "Sky Balloon Explorer", 1800, "epic"),
    ("wanderer_009_hobo_rat.svg", "Hobo Rat", 2000, "legendary"),
]

CURRENT_THEME = "warrior"  # Default theme

THEME_ENTITIES = {
    "warrior": WARRIOR_ENTITIES,
    "scholar": SCHOLAR_ENTITIES,
    "underdog": UNDERDOG_ENTITIES,
    "scientist": SCIENTIST_ENTITIES,
    "wanderer": WANDERER_ENTITIES,
}
CURRENT_ENTITIES = THEME_ENTITIES.get(CURRENT_THEME, WARRIOR_ENTITIES)

RARITY_COLORS = {
    "common": "#9E9E9E",
    "uncommon": "#4CAF50", 
    "rare": "#2196F3",
    "epic": "#9C27B0",
    "legendary": "#FF9800",
}

RARITY_BG = {
    "common": "#2D2D2D",
    "uncommon": "#1B3D1B",
    "rare": "#1B2D3D",
    "epic": "#2D1B3D",
    "legendary": "#3D2D1B",
}


class EntityCard(QFrame):
    """A card displaying a single entity with its SVG and info."""
    
    def __init__(self, svg_path: str, name: str, power: int, rarity: str, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(2)
        
        # Set background based on rarity
        bg_color = RARITY_BG.get(rarity, "#2D2D2D")
        border_color = RARITY_COLORS.get(rarity, "#9E9E9E")
        self.setStyleSheet(f"""
            EntityCard {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # SVG Widget
        svg_widget = QSvgWidget(svg_path)
        svg_widget.setFixedSize(QSize(128, 128))
        svg_widget.setStyleSheet("background: transparent;")
        
        # Center the SVG
        svg_container = QWidget()
        svg_layout = QHBoxLayout(svg_container)
        svg_layout.addStretch()
        svg_layout.addWidget(svg_widget)
        svg_layout.addStretch()
        svg_layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(svg_container)
        
        # Name label - smaller font with word wrap, centered
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        name_label.setStyleSheet(f"color: {border_color}; background: transparent;")
        layout.addWidget(name_label, 0, Qt.AlignCenter)
        
        # Power label
        power_label = QLabel(f"⚔️ Power: {power}")
        power_label.setAlignment(Qt.AlignCenter)
        power_label.setFont(QFont("Segoe UI", 9))
        power_label.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(power_label)
        
        # Rarity label
        rarity_label = QLabel(rarity.upper())
        rarity_label.setAlignment(Qt.AlignCenter)
        rarity_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        rarity_label.setStyleSheet(f"color: {border_color}; background: transparent;")
        layout.addWidget(rarity_label)
        
        self.setFixedSize(180, 220)


class EntityPreviewWindow(QMainWindow):
    """Main window for previewing entity SVGs."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Entity SVG Preview - All Themes (45 Entities)")
        self.setMinimumSize(900, 700)
        
        # Dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1A1A1A;
            }
            QScrollArea {
                background-color: #1A1A1A;
                border: none;
            }
            QWidget {
                background-color: #1A1A1A;
            }
            QLabel {
                color: #FFFFFF;
            }
            QComboBox {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 4px;
            }
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
            }
            QTabBar::tab:selected {
                background-color: #444444;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Header
        header = QLabel("✨ ENTITIDEX - Complete Entity Collection (45 Entities)")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #FFD700; margin: 10px;")
        main_layout.addWidget(header)
        
        # Tab widget for themes
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab { font-weight: bold; font-size: 12px; }
        """)
        
        theme_info = {
            "warrior": ("🗡️ Warrior", "#C62828"),
            "scholar": ("📚 Scholar", "#6A1B9A"),
            "underdog": ("💪 Underdog", "#E65100"),
            "scientist": ("🔬 Scientist", "#1565C0"),
            "wanderer": ("🗺️ Wanderer", "#2E7D32"),
        }
        
        entities_dir = Path(__file__).parent / "icons" / "entities"
        
        for theme_key, (theme_name, theme_color) in theme_info.items():
            tab = self._create_theme_tab(theme_key, THEME_ENTITIES[theme_key], entities_dir, theme_color)
            tabs.addTab(tab, theme_name)
        
        main_layout.addWidget(tabs)
        
        # Footer
        footer = QLabel("All 45 entity SVGs complete! Each theme has 9 entities with the 'niepozorny' legendary twist.")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #888888; margin: 10px;")
        main_layout.addWidget(footer)
    
    def _create_theme_tab(self, theme_key, entities, entities_dir, theme_color):
        """Create a tab widget for a theme."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(16)
        grid.setContentsMargins(16, 16, 16, 16)
        
        row, col = 0, 0
        max_cols = 5  # 5 columns for better fit
        
        for svg_file, name, power, rarity in entities:
            svg_path = entities_dir / svg_file
            if svg_path.exists():
                card = EntityCard(str(svg_path), name, power, rarity)
                grid.addWidget(card, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            else:
                missing_label = QLabel(f"❌ Missing:\n{svg_file}")
                missing_label.setAlignment(Qt.AlignCenter)
                missing_label.setStyleSheet("color: #FF5252; background: #2D2D2D; padding: 20px; border-radius: 8px;")
                missing_label.setFixedSize(180, 220)
                grid.addWidget(missing_label, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
        
        scroll.setWidget(container)
        return scroll


def main():
    app = QApplication(sys.argv)
    window = EntityPreviewWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
