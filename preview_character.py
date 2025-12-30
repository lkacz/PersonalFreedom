#!/usr/bin/env python3
"""Preview script to display the enhanced CharacterCanvas with various configurations."""

import sys
from PySide6 import QtWidgets, QtCore, QtGui

# Import the CharacterCanvas from the main module
from focus_blocker_qt import CharacterCanvas


class PreviewWindow(QtWidgets.QWidget):
    """Window showing multiple character previews with different gear and power levels."""

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
        main_layout.setSpacing(20)

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
            canvas = CharacterCanvas({}, power, 140, 180)
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{tier_name}\n({power} power)")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 11px;")
            container.addWidget(label)
            tier_layout.addLayout(container)

        main_layout.addWidget(tier_group)

        # Row 2: Gear showcase
        gear_group = QtWidgets.QGroupBox("Gear Showcase - Full Equipment Sets")
        gear_layout = QtWidgets.QHBoxLayout(gear_group)
        gear_layout.setSpacing(20)

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
            ("Shadow Knight", 900, {
                "Helmet": {"color": "#37474f"},
                "Chestplate": {"color": "#263238"},
                "Gauntlets": {"color": "#455a64"},
                "Boots": {"color": "#1c313a"},
                "Cloak": {"color": "#102027"},
                "Shield": {"color": "#4e342e"},
                "Weapon": {"color": "#b71c1c"},
                "Amulet": {"color": "#d32f2f"},
            }),
            ("Divine Champion", 1200, {
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
            canvas = CharacterCanvas(gear, power, 160, 200)
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(f"{name}")
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 12px; font-weight: bold;")
            container.addWidget(label)
            gear_label = QtWidgets.QLabel(f"{len(gear)} items equipped")
            gear_label.setAlignment(QtCore.Qt.AlignCenter)
            gear_label.setStyleSheet("font-size: 10px; color: #888;")
            container.addWidget(gear_label)
            gear_layout.addLayout(container)

        main_layout.addWidget(gear_group)

        # Row 3: Individual gear items
        item_group = QtWidgets.QGroupBox("Individual Gear Items")
        item_layout = QtWidgets.QHBoxLayout(item_group)
        item_layout.setSpacing(15)

        items = [
            ("Helmet Only", {"Helmet": {"color": "#64b5f6"}}),
            ("Chestplate Only", {"Chestplate": {"color": "#81c784"}}),
            ("Weapon Only", {"Weapon": {"color": "#ef5350"}}),
            ("Shield Only", {"Shield": {"color": "#ffb74d"}}),
            ("Cloak Only", {"Cloak": {"color": "#ba68c8"}}),
            ("Amulet Only", {"Amulet": {"color": "#4dd0e1"}}),
            ("Gauntlets Only", {"Gauntlets": {"color": "#a1887f"}}),
            ("Boots Only", {"Boots": {"color": "#8d6e63"}}),
        ]

        for name, gear in items:
            container = QtWidgets.QVBoxLayout()
            canvas = CharacterCanvas(gear, 300, 120, 160)
            container.addWidget(canvas, alignment=QtCore.Qt.AlignCenter)
            label = QtWidgets.QLabel(name.replace(" Only", ""))
            label.setAlignment(QtCore.Qt.AlignCenter)
            label.setStyleSheet("font-size: 10px;")
            container.addWidget(label)
            item_layout.addLayout(container)

        main_layout.addWidget(item_group)

        # Instructions
        instructions = QtWidgets.QLabel("Close this window when done previewing")
        instructions.setStyleSheet("font-size: 12px; color: #666; font-style: italic;")
        instructions.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(instructions)

        self.adjustSize()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = PreviewWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
