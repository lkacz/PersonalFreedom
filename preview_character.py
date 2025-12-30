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
                color: #ffd700; 
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
        """)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(15)

        # Title
        title = QtWidgets.QLabel("⚔️ Hero Character Art Preview ⚔️")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffd700;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)

        # Subtitle
        subtitle = QtWidgets.QLabel("Enhanced graphics with detailed gear, expressions, and tier-based effects")
        subtitle.setStyleSheet("font-size: 14px; color: #aaa;")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(subtitle)

        # Row 1: Power tiers (no gear)
        tier_group = QtWidgets.QGroupBox("Power Tiers - Base Character")
        tier_layout = QtWidgets.QHBoxLayout(tier_group)
        tier_layout.setSpacing(15)

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
            canvas = CharacterCanvas({}, power, 120, 160)
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{tier_name}\n({power} power)")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 10px;")
            container.addWidget(label)
            tier_layout.addLayout(container)

        main_layout.addWidget(tier_group)

        # Row 2: Themed gear sets
        gear_group = QtWidgets.QGroupBox("Themed Equipment Sets")
        gear_layout = QtWidgets.QHBoxLayout(gear_group)
        gear_layout.setSpacing(15)

        gear_sets = [
            ("Starter", 50, {
                "Helmet": {"color": "#8d6e63"},
                "Chestplate": {"color": "#a1887f"},
                "Boots": {"color": "#6d4c41"},
            }),
            ("Warrior", 250, {
                "Helmet": {"color": "#78909c"},
                "Chestplate": {"color": "#607d8b"},
                "Gauntlets": {"color": "#546e7a"},
                "Boots": {"color": "#455a64"},
                "Weapon": {"color": "#90a4ae"},
                "Shield": {"color": "#b0bec5"},
            }),
            ("Mage", 400, {
                "Helmet": {"color": "#7e57c2"},
                "Chestplate": {"color": "#9575cd"},
                "Gauntlets": {"color": "#673ab7"},
                "Boots": {"color": "#5e35b1"},
                "Cloak": {"color": "#4527a0"},
                "Amulet": {"color": "#00bcd4"},
                "Weapon": {"color": "#b39ddb"},
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
                "Shield": {"color": "#4e342e"},
                "Weapon": {"color": "#b71c1c"},
                "Amulet": {"color": "#d32f2f"},
            }),
            ("Divine", 1200, {
                "Helmet": {"color": "#fff176"},
                "Chestplate": {"color": "#ffee58"},
                "Gauntlets": {"color": "#ffeb3b"},
                "Boots": {"color": "#fdd835"},
                "Cloak": {"color": "#fffde7"},
                "Shield": {"color": "#f9a825"},
                "Weapon": {"color": "#ffff8d"},
                "Amulet": {"color": "#e1bee7"},
            }),
        ]

        for name, power, gear in gear_sets:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, power, 130, 170)
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 11px; font-weight: bold;")
            container.addWidget(label)
            gear_layout.addLayout(container)

        main_layout.addWidget(gear_group)

        # Row 3: Random combinations
        random_group = QtWidgets.QGroupBox("Random Adventurers")
        random_layout = QtWidgets.QHBoxLayout(random_group)
        random_layout.setSpacing(12)

        random.seed(42)  # Consistent randoms for preview
        adventurer_names = ["Scout", "Ranger", "Knight", "Sorcerer", "Berserker", 
                           "Cleric", "Rogue", "Battlemage", "Guardian", "Champion"]
        
        for i, name in enumerate(adventurer_names):
            power = random.randint(50, 1100)
            gear = self._generate_random_gear()
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, power, 100, 140)
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 9px;")
            container.addWidget(label)
            random_layout.addLayout(container)

        main_layout.addWidget(random_group)

        # Row 4: More random combinations
        random_group2 = QtWidgets.QGroupBox("More Random Heroes")
        random_layout2 = QtWidgets.QHBoxLayout(random_group2)
        random_layout2.setSpacing(12)

        hero_names = ["Nomad", "Sentinel", "Mystic", "Warden", "Slayer",
                      "Oracle", "Templar", "Assassin", "Crusader", "Wanderer"]
        
        for i, name in enumerate(hero_names):
            power = random.randint(100, 1200)
            gear = self._generate_random_gear()
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, power, 100, 140)
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 9px;")
            container.addWidget(label)
            random_layout2.addLayout(container)

        main_layout.addWidget(random_group2)

        # Row 5: Individual gear items
        item_group = QtWidgets.QGroupBox("Individual Gear Items")
        item_layout = QtWidgets.QHBoxLayout(item_group)
        item_layout.setSpacing(12)

        items = [
            ("Helmet", {"Helmet": {"color": "#64b5f6"}}),
            ("Chestplate", {"Chestplate": {"color": "#81c784"}}),
            ("Weapon", {"Weapon": {"color": "#ef5350"}}),
            ("Shield", {"Shield": {"color": "#ffb74d"}}),
            ("Cloak", {"Cloak": {"color": "#ba68c8"}}),
            ("Amulet", {"Amulet": {"color": "#4dd0e1"}}),
            ("Gauntlets", {"Gauntlets": {"color": "#a1887f"}}),
            ("Boots", {"Boots": {"color": "#8d6e63"}}),
        ]

        for name, gear in items:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, 300, 100, 140)
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(name)
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 9px;")
            container.addWidget(label)
            item_layout.addLayout(container)

        main_layout.addWidget(item_group)

        # Instructions
        instructions = QtWidgets.QLabel("Close this window when done previewing")
        instructions.setStyleSheet("font-size: 11px; color: #666; font-style: italic;")
        instructions.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(instructions)

        self.adjustSize()

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
