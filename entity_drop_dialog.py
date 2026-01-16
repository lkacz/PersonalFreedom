"""
Entity Drop/Encounter Dialog - Merge-Style Implementation
=========================================================
Replaces the old complex EntityEncounterDialog with a streamlined,
merge-dialog-style workflow using standard message boxes and 
the reliable lottery animation.
"""

import os
from pathlib import Path
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtSvgWidgets import QSvgWidget
from lottery_animation import LotteryRollDialog
import random
from typing import Callable, Optional

# Path constants for entity SVGs
ENTITY_ICONS_PATH = Path(__file__).parent / "icons" / "entities"
EXCEPTIONAL_ICONS_PATH = ENTITY_ICONS_PATH / "exceptional"


def _resolve_entity_svg_path(entity, is_exceptional: bool = False) -> Optional[str]:
    """
    Resolve the SVG path for an entity.
    
    Args:
        entity: The Entity object
        is_exceptional: If True, look for exceptional variant first
    
    Returns:
        Path to SVG file or None if not found
    """
    name_snake = entity.name.lower().replace(" ", "_").replace("-", "_").replace("'", "")
    
    # If exceptional, try to find the exceptional variant first
    if is_exceptional and EXCEPTIONAL_ICONS_PATH.exists():
        # Try filename pattern {id}_{name_snake_case}_exceptional.svg
        exceptional_path = EXCEPTIONAL_ICONS_PATH / f"{entity.id}_{name_snake}_exceptional.svg"
        if exceptional_path.exists():
            return str(exceptional_path)
        
        # Search for file starting with entity id in exceptional folder
        for svg_file in EXCEPTIONAL_ICONS_PATH.glob(f"{entity.id}*_exceptional.svg"):
            return str(svg_file)
    
    # Fall back to regular SVG resolution
    # Try filename pattern {id}_{name_snake_case}.svg
    pattern_path = ENTITY_ICONS_PATH / f"{entity.id}_{name_snake}.svg"
    if pattern_path.exists():
        return str(pattern_path)
    
    # Search for file starting with entity id
    if ENTITY_ICONS_PATH.exists():
        for svg_file in ENTITY_ICONS_PATH.glob(f"{entity.id}*.svg"):
            # Skip exceptional variants
            if "_exceptional" not in svg_file.name:
                return str(svg_file)
    
    return None


class EntityEncounterDialog(QtWidgets.QDialog):
    """
    Clean, stable dialog for entity encounters.
    Uses fixed sizes and standard Qt widgets for reliability.
    """
    
    RARITY_COLORS = {
        "common": "#7f8c8d", 
        "uncommon": "#27ae60", 
        "rare": "#2980b9", 
        "epic": "#8e44ad", 
        "legendary": "#d35400"
    }
    
    def __init__(self, entity, join_probability: float, parent=None):
        super().__init__(parent)
        self.entity = entity
        self.join_probability = join_probability
        self.accepted_bond = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("✨ Entity Encountered!")
        self.setFixedSize(320, 400)
        self.setModal(True)
        
        color = self.RARITY_COLORS.get(self.entity.rarity.lower(), "#2c3e50")
        
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QtWidgets.QLabel(f"You encountered:")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 14px; color: #aaa;")
        layout.addWidget(title)
        
        # Entity name
        name_label = QtWidgets.QLabel(self.entity.name)
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {color};
        """)
        layout.addWidget(name_label)
        
        # SVG Container
        svg_container = QtWidgets.QFrame()
        svg_container.setFixedSize(140, 140)
        svg_container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}40, stop:1 #1a1a2e);
                border: 2px solid {color};
                border-radius: 12px;
            }}
        """)
        svg_layout = QtWidgets.QVBoxLayout(svg_container)
        svg_layout.setContentsMargins(10, 10, 10, 10)
        
        # SVG Widget
        svg_widget = QSvgWidget()
        svg_widget.setFixedSize(120, 120)
        
        # Load SVG using the helper function (normal variant for encounter)
        svg_path = _resolve_entity_svg_path(self.entity, is_exceptional=False)
        if svg_path:
            svg_widget.load(svg_path)
        
        svg_layout.addWidget(svg_widget, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(svg_container, alignment=QtCore.Qt.AlignCenter)
        
        # Rarity badge
        rarity_label = QtWidgets.QLabel(f"⭐ {self.entity.rarity.upper()}")
        rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        rarity_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {color};
            padding: 4px 12px;
            background: {color}30;
            border-radius: 8px;
        """)
        layout.addWidget(rarity_label, alignment=QtCore.Qt.AlignCenter)
        
        # Stats
        stats_label = QtWidgets.QLabel(f"Power: {self.entity.power}")
        stats_label.setAlignment(QtCore.Qt.AlignCenter)
        stats_label.setStyleSheet("font-size: 13px; color: #ccc;")
        layout.addWidget(stats_label)
        
        # Bonding chance
        prob_pct = int(self.join_probability * 100)
        prob_color = "#4caf50" if prob_pct >= 50 else "#ff9800" if prob_pct >= 25 else "#f44336"
        prob_label = QtWidgets.QLabel(f"Bonding Chance: {prob_pct}%")
        prob_label.setAlignment(QtCore.Qt.AlignCenter)
        prob_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {prob_color};")
        layout.addWidget(prob_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(10)
        
        skip_btn = QtWidgets.QPushButton("Skip")
        skip_btn.setFixedHeight(36)
        skip_btn.setStyleSheet("""
            QPushButton {
                background: #444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QPushButton:hover { background: #555; }
        """)
        skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(skip_btn)
        
        bond_btn = QtWidgets.QPushButton("Attempt Bond")
        bond_btn.setFixedHeight(36)
        bond_btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {color}dd; }}
        """)
        bond_btn.clicked.connect(self._on_bond)
        btn_layout.addWidget(bond_btn)
        
        layout.addLayout(btn_layout)
        
        # Dialog styling
        self.setStyleSheet("""
            QDialog {
                background: #1a1a2e;
            }
        """)
    
    def _on_bond(self):
        self.accepted_bond = True
        self.accept()


def show_entity_encounter(entity, join_probability: float, 
                          bond_logic_callback: Callable[[str], dict],
                          parent: QtWidgets.QWidget = None) -> None:
    """
    Show the entity encounter flow using standard widgets and lottery animation.
    
    Args:
        entity: The Entity object encountered.
        join_probability: Chance of bonding (0.0-1.0).
        bond_logic_callback: Function that takes entity_id and returns result dict
                             (from gamification.attempt_entitidex_bond).
        parent: Parent widget.
    """
    
    # 1. Show encounter dialog with SVG
    dialog = EntityEncounterDialog(entity, join_probability, parent)
    result_code = dialog.exec()
    
    if not dialog.accepted_bond:
        return
        
    # 2. Perform the ACTUAL logic
    try:
        result = bond_logic_callback(entity.id)
        success = result.get("success", False)
        is_exceptional = result.get("is_exceptional", False)
        exceptional_colors = result.get("exceptional_colors", None)
    except Exception as e:
        QtWidgets.QMessageBox.critical(parent, "Error", f"Bonding error: {str(e)}")
        return

    # 3. Calculate visualization roll to match the result
    # If success, we need a roll < probability
    # If fail, we need a roll >= probability
    if success:
        # Generate random success roll (0 to prob)
        roll = random.uniform(0.0, max(0.01, join_probability - 0.01))
    else:
        # Generate random fail roll (prob to 1.0)
        roll = random.uniform(min(0.99, join_probability + 0.01), 1.0)
    
    # 4. Show the dramatic lottery animation
    if is_exceptional:
        # Special success text for exceptional
        border_col = exceptional_colors.get("border", "#FFD700") if exceptional_colors else "#FFD700"
        success_text = f"🌟✨ EXCEPTIONAL {entity.name}! ✨🌟"
    else:
        success_text = f"✨ BONDED: {entity.name}! ✨"
    
    anim_dialog = LotteryRollDialog(
        target_roll=roll,
        success_threshold=join_probability,
        title=f"🎲 Bonding with {entity.name}...",
        success_text=success_text,
        failure_text="💔 Bond Failed",
        animation_duration=4.0, 
        parent=parent
    )
    
    anim_dialog.exec()
    
    # 5. Show special exceptional celebration dialog
    if success and is_exceptional:
        _show_exceptional_celebration(entity, exceptional_colors, parent)
    elif not success and result.get("consecutive_fails", 0) > 0:
        fails = result["consecutive_fails"]
        if fails % 3 == 0:  # Only annoy user occasionally
             QtWidgets.QMessageBox.information(
                 parent, "Bond Failed", 
                 f"Don't worry! Pity bonus is building up.\nConsecutive fails: {fails}"
             )


def _show_exceptional_celebration(entity, exceptional_colors: dict, parent: QtWidgets.QWidget):
    """Show special celebration dialog for catching an exceptional entity with its unique SVG."""
    border_col = exceptional_colors.get("border", "#FFD700") if exceptional_colors else "#FFD700"
    glow_col = exceptional_colors.get("glow", "#FF6B9D") if exceptional_colors else "#FF6B9D"
    
    # Create a custom dialog to show the exceptional SVG
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("🌟 EXCEPTIONAL! 🌟")
    dialog.setFixedSize(380, 500)
    dialog.setModal(True)
    
    layout = QtWidgets.QVBoxLayout(dialog)
    layout.setSpacing(15)
    layout.setContentsMargins(20, 20, 20, 20)
    
    # Title
    title = QtWidgets.QLabel(f"✨ EXCEPTIONAL {entity.name}! ✨")
    title.setAlignment(QtCore.Qt.AlignCenter)
    title.setWordWrap(True)
    title.setStyleSheet(f"""
        font-size: 22px;
        font-weight: bold;
        color: {border_col};
    """)
    layout.addWidget(title)
    
    # SVG Container with glow effect
    svg_container = QtWidgets.QFrame()
    svg_container.setFixedSize(180, 180)
    svg_container.setStyleSheet(f"""
        QFrame {{
            background: qradialgradient(cx:0.5, cy:0.5, radius:0.8,
                fx:0.5, fy:0.5,
                stop:0 {glow_col}40, stop:0.5 {border_col}20, stop:1 #1a1a2e);
            border: 3px solid {border_col};
            border-radius: 16px;
        }}
    """)
    svg_layout = QtWidgets.QVBoxLayout(svg_container)
    svg_layout.setContentsMargins(15, 15, 15, 15)
    
    # Load the EXCEPTIONAL SVG variant
    svg_widget = QSvgWidget()
    svg_widget.setFixedSize(150, 150)
    exceptional_svg_path = _resolve_entity_svg_path(entity, is_exceptional=True)
    if exceptional_svg_path:
        svg_widget.load(exceptional_svg_path)
    svg_widget.setStyleSheet("background: transparent;")
    svg_layout.addWidget(svg_widget, alignment=QtCore.Qt.AlignCenter)
    
    # Center the SVG container
    svg_wrapper = QtWidgets.QWidget()
    svg_wrapper_layout = QtWidgets.QHBoxLayout(svg_wrapper)
    svg_wrapper_layout.addStretch()
    svg_wrapper_layout.addWidget(svg_container)
    svg_wrapper_layout.addStretch()
    layout.addWidget(svg_wrapper)
    
    # Info text
    info_label = QtWidgets.QLabel(
        f"<p style='text-align: center; font-size: 14px;'>"
        f"You found an <b>EXCEPTIONAL</b> variant!</p>"
        f"<p style='text-align: center; font-size: 12px; color: #888;'>"
        f"Only 5% of caught entities become Exceptional.<br>"
        f"This one has a unique appearance!</p>"
    )
    info_label.setAlignment(QtCore.Qt.AlignCenter)
    info_label.setStyleSheet("color: #FFFFFF;")
    layout.addWidget(info_label)
    
    # Rarity badge
    rarity_color = {
        "common": "#7f8c8d", "uncommon": "#27ae60", "rare": "#2980b9",
        "epic": "#8e44ad", "legendary": "#d35400"
    }.get(entity.rarity.lower(), "#2c3e50")
    
    rarity_label = QtWidgets.QLabel(f"✨ EXCEPTIONAL {entity.rarity.upper()} ✨")
    rarity_label.setAlignment(QtCore.Qt.AlignCenter)
    rarity_label.setStyleSheet(f"""
        font-size: 14px;
        font-weight: bold;
        color: {border_col};
        padding: 8px 16px;
        background: {border_col}30;
        border: 2px solid {border_col};
        border-radius: 8px;
    """)
    layout.addWidget(rarity_label, alignment=QtCore.Qt.AlignCenter)
    
    layout.addStretch()
    
    # OK button
    ok_btn = QtWidgets.QPushButton("Amazing! 🎉")
    ok_btn.setFixedHeight(44)
    ok_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {border_col};
            color: #000000;
            font-size: 16px;
            font-weight: bold;
            padding: 8px 20px;
            border-radius: 8px;
            min-width: 120px;
        }}
        QPushButton:hover {{
            background-color: {glow_col};
        }}
    """)
    ok_btn.clicked.connect(dialog.accept)
    layout.addWidget(ok_btn, alignment=QtCore.Qt.AlignCenter)
    
    # Dialog styling
    dialog.setStyleSheet("""
        QDialog {
            background-color: #1a1a2e;
        }
    """)
    
    dialog.exec()

