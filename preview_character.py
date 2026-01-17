#!/usr/bin/env python3
"""Preview script to display the enhanced CharacterCanvas with various configurations."""

import sys
import random
from PySide6 import QtWidgets, QtCore, QtGui

# Import the CharacterCanvas from the main module
from focus_blocker_qt import CharacterCanvas


class PreviewWindow(QtWidgets.QWidget):
    """Window showing multiple character previews with different gear and power levels."""

    # Color palettes for random gear
    GEAR_COLORS = [
        "#78909c", "#607d8b", "#546e7a", "#455a64",  # Steel/Gray
        "#8d6e63", "#795548", "#6d4c41", "#5d4037",  # Brown/Leather
        "#7e57c2", "#673ab7", "#5e35b1", "#512da8",  # Purple/Magic
        "#42a5f5", "#2196f3", "#1e88e5", "#1976d2",  # Blue
        "#66bb6a", "#4caf50", "#43a047", "#388e3c",  # Green
        "#ef5350", "#e53935", "#d32f2f", "#c62828",  # Red
        "#ffa726", "#ff9800", "#fb8c00", "#f57c00",  # Orange
        "#ffee58", "#ffeb3b", "#fdd835", "#fbc02d",  # Yellow/Gold
        "#26c6da", "#00bcd4", "#00acc1", "#0097a7",  # Cyan
        "#ec407a", "#e91e63", "#d81b60", "#c2185b",  # Pink
        "#37474f", "#263238", "#1c313a", "#102027",  # Dark/Shadow
        "#ffd54f", "#ffca28", "#ffc107", "#ffb300",  # Gold
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🗽 Personal Liberty - Character Art Preview")
        self.setStyleSheet("""
            QWidget { background-color: #1a1a2e; }
            QLabel { color: #fff; font-family: 'Segoe UI'; }
            QGroupBox { 
                color: #a5b4fc; 
                font-weight: bold; 
                border: 2px solid #444; 
                border-radius: 8px; 
                margin-top: 12px; 
                padding-top: 10px;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 5px; 
            }
            QScrollArea { border: none; background-color: #1a1a2e; }
            QScrollBar:vertical {
                background: #2d2d4a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #6366f1;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Main layout for the window
        window_layout = QtWidgets.QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)

        # Title (outside scroll area)
        title = QtWidgets.QLabel("⚔️ Hero Character Art Preview ⚔️")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #a5b4fc; padding: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        window_layout.addWidget(title)

        # Subtitle
        subtitle = QtWidgets.QLabel("All 5 story themes: Warrior, Scholar, Wanderer, Underdog & Scientist")
        subtitle.setStyleSheet("font-size: 14px; color: #aaa;")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        window_layout.addWidget(subtitle)

        # Scroll area for content
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        # Content widget inside scroll area
        content_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(content_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Row 1: Warrior Power Tiers
        warrior_group = QtWidgets.QGroupBox("⚔️ Warrior Theme - Power Tiers")
        warrior_layout = QtWidgets.QHBoxLayout(warrior_group)
        warrior_layout.setSpacing(12)

        tiers = [
            ("Pathetic", 25),
            ("Modest", 75),
            ("Decent", 175),
            ("Heroic", 350),
            ("Epic", 600),
            ("Legendary", 850),
            ("Godlike", 1100),
        ]

        for tier_name, power in tiers:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas({}, power, 100, 140, story_theme="warrior")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{tier_name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 9px;")
            container.addWidget(label)
            warrior_layout.addLayout(container)

        main_layout.addWidget(warrior_group)

        # Row 2: Scholar Power Tiers
        scholar_group = QtWidgets.QGroupBox("📚 Scholar Theme - Power Tiers")
        scholar_layout = QtWidgets.QHBoxLayout(scholar_group)
        scholar_layout.setSpacing(12)

        for tier_name, power in tiers:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas({}, power, 100, 140, story_theme="scholar")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{tier_name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 9px;")
            container.addWidget(label)
            scholar_layout.addLayout(container)

        main_layout.addWidget(scholar_group)

        # Row 3: Wanderer Power Tiers
        wanderer_group = QtWidgets.QGroupBox("🌙 Wanderer Theme - Power Tiers")
        wanderer_layout = QtWidgets.QHBoxLayout(wanderer_group)
        wanderer_layout.setSpacing(12)

        for tier_name, power in tiers:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas({}, power, 100, 140, story_theme="wanderer")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{tier_name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 9px;")
            container.addWidget(label)
            wanderer_layout.addLayout(container)

        main_layout.addWidget(wanderer_group)

        # Row 4: Underdog Power Tiers
        underdog_group = QtWidgets.QGroupBox("🏢 Underdog Theme - Power Tiers")
        underdog_layout = QtWidgets.QHBoxLayout(underdog_group)
        underdog_layout.setSpacing(12)

        for tier_name, power in tiers:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas({}, power, 100, 140, story_theme="underdog")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{tier_name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 9px;")
            container.addWidget(label)
            underdog_layout.addLayout(container)

        main_layout.addWidget(underdog_group)

        # Row 5: Scientist Power Tiers
        scientist_group = QtWidgets.QGroupBox("🧪 Scientist Theme - Power Tiers")
        scientist_layout = QtWidgets.QHBoxLayout(scientist_group)
        scientist_layout.setSpacing(12)

        for tier_name, power in tiers:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas({}, power, 100, 140, story_theme="scientist")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{tier_name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 9px;")
            container.addWidget(label)
            scientist_layout.addLayout(container)

        main_layout.addWidget(scientist_group)

        # Row 6: Warrior Gear Sets
        warrior_gear_group = QtWidgets.QGroupBox("⚔️ Warrior Equipment Sets")
        warrior_gear_layout = QtWidgets.QHBoxLayout(warrior_gear_group)
        warrior_gear_layout.setSpacing(12)

        warrior_sets = [
            ("Starter", 50, {
                "Helmet": {"color": "#8d6e63"},
                "Chestplate": {"color": "#a1887f"},
                "Boots": {"color": "#6d4c41"},
            }),
            ("Warrior", 350, {
                "Helmet": {"color": "#78909c"},
                "Chestplate": {"color": "#607d8b"},
                "Gauntlets": {"color": "#546e7a"},
                "Boots": {"color": "#455a64"},
                "Weapon": {"color": "#90a4ae"},
                "Shield": {"color": "#b0bec5"},
            }),
            ("Paladin", 650, {
                "Helmet": {"color": "#ffd54f"},
                "Chestplate": {"color": "#ffca28"},
                "Gauntlets": {"color": "#ffb300"},
                "Boots": {"color": "#ffa000"},
                "Cloak": {"color": "#fff8e1"},
                "Shield": {"color": "#ffc107"},
                "Weapon": {"color": "#fff59d"},
                "Amulet": {"color": "#4fc3f7"},
            }),
            ("Shadow", 900, {
                "Helmet": {"color": "#37474f"},
                "Chestplate": {"color": "#263238"},
                "Gauntlets": {"color": "#455a64"},
                "Boots": {"color": "#1c313a"},
                "Cloak": {"color": "#102027"},
                "Weapon": {"color": "#b71c1c"},
                "Amulet": {"color": "#d32f2f"},
            }),
        ]

        for name, power, gear in warrior_sets:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, power, 110, 150, story_theme="warrior")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 10px; font-weight: bold;")
            container.addWidget(label)
            warrior_gear_layout.addLayout(container)

        main_layout.addWidget(warrior_gear_group)

        # Row 5: Scholar Gear Sets
        scholar_gear_group = QtWidgets.QGroupBox("📚 Scholar Equipment Sets")
        scholar_gear_layout = QtWidgets.QHBoxLayout(scholar_gear_group)
        scholar_gear_layout.setSpacing(12)

        scholar_sets = [
            ("Student", 50, {
                "Helmet": {"color": "#1a237e"},  # Mortarboard
                "Chestplate": {"color": "#5c6bc0"},  # Vest
                "Boots": {"color": "#5d4037"},  # Oxford shoes
            }),
            ("Librarian", 350, {
                "Helmet": {"color": "#311b92"},
                "Chestplate": {"color": "#4527a0"},
                "Gauntlets": {"color": "#f5f5dc"},  # Writing gloves
                "Boots": {"color": "#4e342e"},
                "Shield": {"color": "#8d6e63"},  # Book
                "Weapon": {"color": "#1a237e"},  # Quill
            }),
            ("Professor", 650, {
                "Helmet": {"color": "#1a237e"},
                "Chestplate": {"color": "#283593"},
                "Gauntlets": {"color": "#fff8e1"},
                "Boots": {"color": "#3e2723"},
                "Cloak": {"color": "#4a148c"},  # Academic robe
                "Shield": {"color": "#6d4c41"},  # Tome
                "Weapon": {"color": "#311b92"},
                "Amulet": {"color": "#4fc3f7"},  # Pocket watch
            }),
            ("Archmage", 1100, {
                "Helmet": {"color": "#4a148c"},
                "Chestplate": {"color": "#6a1b9a"},
                "Gauntlets": {"color": "#e1bee7"},
                "Boots": {"color": "#4e342e"},
                "Cloak": {"color": "#7b1fa2"},
                "Shield": {"color": "#8d6e63"},
                "Weapon": {"color": "#9c27b0"},
                "Amulet": {"color": "#00bcd4"},
            }),
        ]

        for name, power, gear in scholar_sets:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, power, 110, 150, story_theme="scholar")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 10px; font-weight: bold;")
            container.addWidget(label)
            scholar_gear_layout.addLayout(container)

        main_layout.addWidget(scholar_gear_group)

        # Row 6: Wanderer Gear Sets
        wanderer_gear_group = QtWidgets.QGroupBox("🌙 Wanderer Equipment Sets")
        wanderer_gear_layout = QtWidgets.QHBoxLayout(wanderer_gear_group)
        wanderer_gear_layout.setSpacing(12)

        wanderer_sets = [
            ("Dreamer", 50, {
                "Helmet": {"color": "#3949ab"},  # Star circlet
                "Chestplate": {"color": "#5c6bc0"},  # Starweave robe
                "Boots": {"color": "#3f51b5"},  # Cloud walkers
            }),
            ("Stargazer", 350, {
                "Helmet": {"color": "#5e35b1"},
                "Chestplate": {"color": "#673ab7"},
                "Gauntlets": {"color": "#9575cd"},  # Arm wraps
                "Boots": {"color": "#512da8"},
                "Shield": {"color": "#7e57c2"},  # Reality ward
                "Weapon": {"color": "#b39ddb"},  # Dream staff
            }),
            ("Moon Mystic", 650, {
                "Helmet": {"color": "#4a148c"},
                "Chestplate": {"color": "#6a1b9a"},
                "Gauntlets": {"color": "#9c27b0"},
                "Boots": {"color": "#7b1fa2"},
                "Cloak": {"color": "#1a237e"},  # Star mantle
                "Shield": {"color": "#9c27b0"},  # Astral aegis
                "Weapon": {"color": "#ce93d8"},
                "Amulet": {"color": "#00bcd4"},  # Moon crystal
            }),
            ("Void Walker", 1100, {
                "Helmet": {"color": "#1a1a2e"},
                "Chestplate": {"color": "#0d0d1a"},
                "Gauntlets": {"color": "#2d2d4a"},
                "Boots": {"color": "#1a1a3a"},
                "Cloak": {"color": "#0a0a1a"},
                "Shield": {"color": "#3d3d6a"},
                "Weapon": {"color": "#6a6aaa"},
                "Amulet": {"color": "#9c27b0"},
            }),
        ]

        for name, power, gear in wanderer_sets:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, power, 110, 150, story_theme="wanderer")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 10px; font-weight: bold;")
            container.addWidget(label)
            wanderer_gear_layout.addLayout(container)

        main_layout.addWidget(wanderer_gear_group)

        # Row 7: Random Wanderers
        random_group = QtWidgets.QGroupBox("🌙 Random Wanderer Adventurers")
        random_layout = QtWidgets.QHBoxLayout(random_group)
        random_layout.setSpacing(10)

        random.seed(123)  # Consistent randoms for preview
        wanderer_names = ["Seeker", "Dreamer", "Oracle", "Seer", "Prophet", 
                         "Weaver", "Mystic", "Shaman", "Sage", "Astral"]
        
        for i, name in enumerate(wanderer_names):
            power = random.randint(50, 1100)
            gear = self._generate_random_gear()
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, power, 90, 125, story_theme="wanderer")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 8px;")
            container.addWidget(label)
            random_layout.addLayout(container)

        main_layout.addWidget(random_group)

        # Row 8: Underdog Gear Sets
        underdog_gear_group = QtWidgets.QGroupBox("🏢 Underdog Equipment Sets")
        underdog_gear_layout = QtWidgets.QHBoxLayout(underdog_gear_group)
        underdog_gear_layout.setSpacing(12)

        underdog_sets = [
            ("Intern", 50, {
                "Helmet": {"color": "#2d3436"},  # Basic headphones
                "Chestplate": {"color": "#74b9ff"},  # Polo shirt
                "Boots": {"color": "#636e72"},  # Sneakers
            }),
            ("Employee", 350, {
                "Helmet": {"color": "#1e272e"},
                "Chestplate": {"color": "#0984e3"},
                "Gauntlets": {"color": "#2d3436"},  # Smartwatch
                "Boots": {"color": "#2d3436"},
                "Shield": {"color": "#636e72"},  # Laptop
                "Weapon": {"color": "#1e272e"},  # Smartphone
            }),
            ("Manager", 650, {
                "Helmet": {"color": "#0d47a1"},
                "Chestplate": {"color": "#1565c0"},
                "Gauntlets": {"color": "#ffd700"},  # Premium watch
                "Boots": {"color": "#4e342e"},  # Dress shoes
                "Cloak": {"color": "#2c3e50"},  # Blazer
                "Shield": {"color": "#455a64"},  # MacBook
                "Weapon": {"color": "#1e272e"},
                "Amulet": {"color": "#ffd700"},  # Gold badge
            }),
            ("CEO", 1100, {
                "Helmet": {"color": "#b71c1c"},  # Beats headphones
                "Chestplate": {"color": "#1a237e"},
                "Gauntlets": {"color": "#ffd700"},
                "Boots": {"color": "#3e2723"},
                "Cloak": {"color": "#212121"},  # Designer jacket
                "Shield": {"color": "#37474f"},
                "Weapon": {"color": "#ffd700"},  # Gold phone
                "Amulet": {"color": "#ffd700"},
            }),
        ]

        for name, power, gear in underdog_sets:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, power, 110, 150, story_theme="underdog")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 10px; font-weight: bold;")
            container.addWidget(label)
            underdog_gear_layout.addLayout(container)

        main_layout.addWidget(underdog_gear_group)

        # Row 9: Scientist Equipment Sets
        scientist_gear_group = QtWidgets.QGroupBox("🧪 Scientist Equipment Sets")
        scientist_gear_layout = QtWidgets.QHBoxLayout(scientist_gear_group)
        scientist_gear_layout.setSpacing(12)

        scientist_sets = [
            ("Grad Student", 50, {
                "Helmet": {"color": "#4db8ff"},  # Safety goggles
                "Chestplate": {"color": "#e8e8e8"},  # Lab coat
                "Gauntlets": {"color": "#b0e0ff"},  # Latex gloves
                "Boots": {"color": "#34495e"},  # Lab shoes
            }),
            ("Researcher", 350, {
                "Helmet": {"color": "#4db8ff"},
                "Chestplate": {"color": "#f5f5f5"},
                "Gauntlets": {"color": "#b0e0ff"},
                "Boots": {"color": "#34495e"},
                "Shield": {"color": "#37474f"},  # Lab notebook
                "Weapon": {"color": "#78909c"},  # Pipette
                "Amulet": {"color": "#ffd700"},  # ID badge
            }),
            ("Scientist", 650, {
                "Helmet": {"color": "#4db8ff"},
                "Chestplate": {"color": "#ffffff"},
                "Gauntlets": {"color": "#b0e0ff"},
                "Boots": {"color": "#34495e"},
                "Cloak": {"color": "#ffeb3b"},  # Hazmat suit
                "Shield": {"color": "#37474f"},  # Digital tablet
                "Weapon": {"color": "#78909c"},  # Spectrometer
                "Amulet": {"color": "#ffd700"},
            }),
            ("Nobel Laureate", 1100, {
                "Helmet": {"color": "#4db8ff"},
                "Chestplate": {"color": "#ffffff"},
                "Gauntlets": {"color": "#b0e0ff"},
                "Boots": {"color": "#34495e"},
                "Cloak": {"color": "#ffeb3b"},
                "Shield": {"color": "#37474f"},
                "Weapon": {"color": "#78909c"},  # Quantum analyzer
                "Amulet": {"color": "#ffd700"},  # ID with Nobel medal
            }),
        ]

        for name, power, gear in scientist_sets:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, power, 110, 150, story_theme="scientist")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 10px; font-weight: bold;")
            container.addWidget(label)
            scientist_gear_layout.addLayout(container)

        main_layout.addWidget(scientist_gear_group)

        # Row 10: Random Underdogs
        underdog_random_group = QtWidgets.QGroupBox("🏢 Random Office Workers")
        underdog_random_layout = QtWidgets.QHBoxLayout(underdog_random_group)
        underdog_random_layout.setSpacing(10)

        random.seed(456)  # Different seed for variety
        underdog_names = ["Newbie", "Temp", "Junior", "Senior", "Lead", 
                         "Director", "VP", "Founder", "Hustler", "Legend"]
        
        for i, name in enumerate(underdog_names):
            power = random.randint(50, 1100)
            gear = self._generate_random_gear()
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, power, 90, 125, story_theme="underdog")
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 8px;")
            container.addWidget(label)
            underdog_random_layout.addLayout(container)

        main_layout.addWidget(underdog_random_group)

        # Instructions
        instructions = QtWidgets.QLabel("Scroll to see all themes • Close this window when done")
        instructions.setStyleSheet("font-size: 11px; color: #666; font-style: italic;")
        instructions.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(instructions)

        # Finalize scroll area
        scroll_area.setWidget(content_widget)
        window_layout.addWidget(scroll_area)
        
        # Set a reasonable default size
        self.resize(1200, 800)

    def _generate_random_gear(self) -> dict:
        """Generate a random gear loadout."""
        slots = ["Helmet", "Chestplate", "Gauntlets", "Boots", "Weapon", "Shield", "Cloak", "Amulet"]
        gear = {}
        # Randomly decide how many items (1-8)
        num_items = random.randint(1, 8)
        # Pick random slots
        chosen_slots = random.sample(slots, num_items)
        # Assign random colors
        for slot in chosen_slots:
            gear[slot] = {"color": random.choice(self.GEAR_COLORS)}
        return gear


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = PreviewWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
