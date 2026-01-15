"""
Entity Drop/Encounter Dialog - Merge-Style Implementation
=========================================================
Replaces the old complex EntityEncounterDialog with a streamlined,
merge-dialog-style workflow using standard message boxes and 
the reliable lottery animation.
"""

import os
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtSvgWidgets import QSvgWidget
from lottery_animation import LotteryRollDialog
import random
from typing import Callable, Optional


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
        
        # Load SVG - try multiple path patterns
        svg_loaded = False
        icon_path = getattr(self.entity, 'icon_path', '')
        
        # 1. Try direct icon_path from entity
        if icon_path and os.path.exists(icon_path):
            svg_widget.load(icon_path)
            svg_loaded = True
        
        if not svg_loaded:
            # 2. Try filename pattern: {id}_{name_snake_case}.svg
            name_snake = self.entity.name.lower().replace(" ", "_").replace("-", "_")
            pattern_path = os.path.join("icons", "entities", f"{self.entity.id}_{name_snake}.svg")
            if os.path.exists(pattern_path):
                svg_widget.load(pattern_path)
                svg_loaded = True
        
        if not svg_loaded:
            # 3. Try searching for file starting with entity id
            icons_dir = os.path.join("icons", "entities")
            if os.path.isdir(icons_dir):
                for filename in os.listdir(icons_dir):
                    if filename.startswith(self.entity.id + "_") and filename.endswith(".svg"):
                        svg_widget.load(os.path.join(icons_dir, filename))
                        svg_loaded = True
                        break
        
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
    anim_dialog = LotteryRollDialog(
        target_roll=roll,
        success_threshold=join_probability,
        title=f"🎲 Bonding with {entity.name}...",
        success_text=f"✨ BONDED: {entity.name}! ✨",
        failure_text="💔 Bond Failed",
        animation_duration=4.0, 
        parent=parent
    )
    
    anim_dialog.exec()
    
    # 5. Optional: Show detailed result if needed (e.g. pity bonus info)
    # The LotteryRollDialog just shows success/fail. 
    # If we want to show "Pity Bonus Increased", we might need another msg box
    # or rely on the status bar updates usually done by the caller.
    if not success and result.get("consecutive_fails", 0) > 0:
        fails = result["consecutive_fails"]
        if fails % 3 == 0: # Only annoy user occasionally
             QtWidgets.QMessageBox.information(
                 parent, "Bond Failed", 
                 f"Don't worry! Pity bonus is building up.\nConsecutive fails: {fails}"
             )

