"""
Entity Encounter Dialog - Entitidex bonding UI.

This module provides the UI for entity encounters when users complete
focus sessions. Features an animated reveal with bonding attempt mechanics.
"""

import random
import os
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtSvgWidgets import QSvgWidget

# Import entitidex components
from entitidex import Entity
from entitidex.catch_mechanics import CATCH_CONFIG
from app_utils import get_app_dir
from styled_dialog import styled_info


class EntityEncounterDialog(QtWidgets.QDialog):
    """
    Dialog for entity encounters during session completion.
    
    Shows an animated reveal of the encountered entity with lore,
    then allows the user to attempt bonding with probability display.
    
    Signals:
        bond_attempted: Emitted when user tries to bond (entity_id: str)
        encounter_skipped: Emitted when user skips the encounter
    """
    
    bond_attempted = QtCore.Signal(str)  # entity_id
    encounter_skipped = QtCore.Signal()
    
    # Rarity color mapping
    RARITY_COLORS = {
        "common": "#9E9E9E",      # Gray
        "uncommon": "#4CAF50",    # Green
        "rare": "#2196F3",        # Blue
        "epic": "#9C27B0",        # Purple
        "legendary": "#FF9800",   # Orange/Gold
    }
    
    # Rarity glow effects
    RARITY_GLOW = {
        "common": "rgba(158, 158, 158, 0.3)",
        "uncommon": "rgba(76, 175, 80, 0.4)",
        "rare": "rgba(33, 150, 243, 0.5)",
        "epic": "rgba(156, 39, 176, 0.6)",
        "legendary": "rgba(255, 152, 0, 0.7)",
    }
    
    def __init__(self, entity: Entity, join_probability: float,
                 hero_power: int, parent: Optional[QtWidgets.QWidget] = None,
                 is_exceptional: bool = False):
        """
        Initialize the entity encounter dialog.
        
        Args:
            entity: The encountered Entity
            join_probability: Probability (0.0-1.0) of successful bond
            hero_power: Current hero power for display
            parent: Parent widget
            is_exceptional: True if this is an exceptional variant encounter
        """
        super().__init__(parent)
        self.entity = entity
        self.join_probability = join_probability
        self.hero_power = hero_power
        self.is_exceptional = is_exceptional
        self.bond_result: Optional[bool] = None
        
        self._anims = [] # Keep references to animations
        
        self._setup_ui()
    
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Handle dialog show event to ensure proper layout."""
        super().showEvent(event)
        # Start animation shortly after show
        QtCore.QTimer.singleShot(100, self._start_reveal_animation)
        
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle cleanup."""
        self._anims.clear()
        super().closeEvent(event)
    
    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("✨ Entity Encountered!")
        self.setFixedSize(500, 700)
        # Use standard Dialog flags to prevent OS-level resize anomalies
        self.setWindowFlags(
            QtCore.Qt.Dialog |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.WindowCloseButtonHint
        )
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        
        # Get rarity color
        rarity_color = self.RARITY_COLORS.get(self.entity.rarity.lower(), "#9E9E9E")
        
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Title with animation placeholder
        self.title_label = QtWidgets.QLabel("✨ A wild entity appears! ✨")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #FFD700;
                padding: 10px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Entity display card
        self.entity_card = QtWidgets.QFrame()
        self.entity_card.setMinimumHeight(280)
        self.entity_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2D2D2D, stop:1 #1A1A1A
                );
                border: 2px solid {rarity_color};
                border-radius: 15px;
                padding: 15px;
            }}
        """)
        
        card_layout = QtWidgets.QVBoxLayout(self.entity_card)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(15, 15, 15, 15)
        
        # Entity name - use exceptional name if available for exceptional encounters
        if self.is_exceptional and self.entity.exceptional_name:
            display_name = self.entity.exceptional_name
        else:
            display_name = self.entity.name
        self.name_label = QtWidgets.QLabel(display_name)
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label.setFixedHeight(35)  # Fixed height
        self.name_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {rarity_color};
                padding: 5px;
                border: none;
            }}
        """)
        card_layout.addWidget(self.name_label)
        
        # Entity SVG container
        self.svg_container = QtWidgets.QWidget()
        self.svg_container.setFixedHeight(120)  # Fix height to prevent collapsing/clipping
        self.svg_container.setStyleSheet("border: none; background: transparent;")
        svg_layout = QtWidgets.QHBoxLayout(self.svg_container)
        svg_layout.setContentsMargins(0, 0, 0, 0)
        svg_layout.addStretch()
        
        # SVG Widget
        self.entity_svg = QSvgWidget()
        self.entity_svg.setFixedSize(120, 120)
        
        # Construct SVG filename: entity_id + name in snake_case
        name_snake = self.entity.name.lower().replace(" ", "_").replace("'", "")
        svg_filename = f"{self.entity.id}_{name_snake}.svg"
        svg_path = os.path.join(str(get_app_dir()), "icons", "entities", svg_filename)
        if os.path.exists(svg_path):
            self.entity_svg.load(svg_path)
        self.entity_svg.setStyleSheet("border: none; background: transparent;")
        
        svg_layout.addWidget(self.entity_svg)
        svg_layout.addStretch()
        card_layout.addWidget(self.svg_container)
        
        # Rarity badge context
        self.rarity_container = QtWidgets.QWidget()
        self.rarity_container.setFixedHeight(30)  # Fixed height
        self.rarity_container.setStyleSheet("border: none; background: transparent;")
        rarity_layout = QtWidgets.QHBoxLayout(self.rarity_container)
        rarity_layout.setContentsMargins(0, 0, 0, 0)
        rarity_layout.addStretch()
        
        self.rarity_label = QtWidgets.QLabel(self.entity.rarity.upper())
        self.rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        self.rarity_label.setMinimumHeight(28)
        self.rarity_label.setFixedWidth(120)
        self.rarity_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: bold;
                color: white;
                background: {rarity_color};
                border: none;
                border-radius: 8px;
                padding: 4px 12px;
            }}
        """)
        rarity_layout.addWidget(self.rarity_label)
        rarity_layout.addStretch()
        card_layout.addWidget(self.rarity_container)
        
        # Power display
        self.power_label = QtWidgets.QLabel(f"⚡ Power: {self.entity.power}")
        self.power_label.setAlignment(QtCore.Qt.AlignCenter)
        self.power_label.setFixedHeight(28)  # Fixed height
        self.power_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #FFD700;
                border: none;
                padding: 5px;
            }
        """)
        card_layout.addWidget(self.power_label)
        
        # Theme badge
        theme_names = {
            "warrior": "🛡️ Warrior's Path",
            "scholar": "📚 Scholar's Study",
            "wanderer": "🧭 Wanderer's Journey",
            "underdog": "💪 Underdog's Rise",
            "scientist": "🔬 Scientist's Lab",
            "robot": "🤖 Robot's Awakening",
            "space_pirate": "🏴‍☠️ Space Pirate's Ledger",
            "thief": "Thief's Casebook",
            "zoo_worker": "Zoo Worker's Sanctuary Log",
        }
        theme_display = theme_names.get(self.entity.theme_set, self.entity.theme_set)
        self.theme_label = QtWidgets.QLabel(theme_display)
        self.theme_label.setAlignment(QtCore.Qt.AlignCenter)
        self.theme_label.setFixedHeight(22)  # Fixed height
        self.theme_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #AAAAAA;
                font-style: italic;
                border: none;
            }
        """)
        card_layout.addWidget(self.theme_label)
        
        # Lore text - use exceptional lore if available for exceptional encounters
        if self.is_exceptional and self.entity.exceptional_lore:
            display_lore = self.entity.exceptional_lore
        else:
            display_lore = self.entity.lore
        self.lore_label = QtWidgets.QLabel(display_lore)
        self.lore_label.setAlignment(QtCore.Qt.AlignCenter)
        self.lore_label.setWordWrap(True)
        self.lore_label.setMinimumHeight(80)
        self.lore_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
        self.lore_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #CCCCCC;
                border: none;
                padding: 10px;
                line-height: 1.4;
            }
        """)
        card_layout.addWidget(self.lore_label)
        
        layout.addWidget(self.entity_card)
        
        # Probability display
        prob_percent = int(self.join_probability * 100)
        prob_color = self._get_probability_color(prob_percent)
        
        self.prob_frame = QtWidgets.QFrame()
        self.prob_frame.setStyleSheet("""
            QFrame {
                background: #1E1E1E;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        prob_layout = QtWidgets.QVBoxLayout(self.prob_frame)
        
        prob_title = QtWidgets.QLabel("Bond Probability")
        prob_title.setAlignment(QtCore.Qt.AlignCenter)
        prob_title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #888888;
            }
        """)
        prob_layout.addWidget(prob_title)
        
        self.prob_value = QtWidgets.QLabel(f"{prob_percent}%")
        self.prob_value.setAlignment(QtCore.Qt.AlignCenter)
        
        # Calculate probability breakdown for tooltip
        power_diff = self.hero_power - self.entity.power
        base_chance = 30  # Assumed base
        power_factor = min(50, max(-30, power_diff // 10))  # Power contribution
        rarity_penalty = {"Common": 0, "Uncommon": -5, "Rare": -10, "Epic": -15, "Legendary": -20}.get(self.entity.rarity, 0)
        exceptional_bonus = 10 if self.is_exceptional else 0
        
        breakdown_parts = [
            f"Base chance: {base_chance}%",
            f"Power difference ({power_diff:+d}): {power_factor:+d}%",
            f"Rarity ({self.entity.rarity}): {rarity_penalty:+d}%",
        ]
        if exceptional_bonus:
            breakdown_parts.append(f"Exceptional bonus: +{exceptional_bonus}%")
        breakdown_parts.append(f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
        breakdown_parts.append(f"Final: {prob_percent}%")
        
        prob_tooltip = "\n".join(breakdown_parts)
        self.prob_value.setToolTip(f"🎲 Probability Breakdown:\n{prob_tooltip}")
        
        self.prob_value.setStyleSheet(f"""
            QLabel {{
                font-size: 32px;
                font-weight: bold;
                color: {prob_color};
            }}
        """)
        prob_layout.addWidget(self.prob_value)
        
        # Progress bar for probability
        self.prob_bar = QtWidgets.QProgressBar()
        self.prob_bar.setMaximum(100)
        self.prob_bar.setValue(prob_percent)
        self.prob_bar.setTextVisible(False)
        self.prob_bar.setFixedHeight(8)
        self.prob_bar.setStyleSheet(f"""
            QProgressBar {{
                background: #333333;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {prob_color};
                border-radius: 4px;
            }}
        """)
        prob_layout.addWidget(self.prob_bar)
        
        # Power comparison hint
        power_diff = self.hero_power - self.entity.power
        if power_diff > 100:
            hint = "Your power greatly exceeds theirs!"
        elif power_diff > 0:
            hint = "You're stronger - good odds!"
        elif power_diff > -100:
            hint = "Evenly matched - could go either way..."
        else:
            hint = "They're much stronger - a rare catch!"
        
        hint_label = QtWidgets.QLabel(hint)
        hint_label.setAlignment(QtCore.Qt.AlignCenter)
        hint_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666666;
                font-style: italic;
            }
        """)
        prob_layout.addWidget(hint_label)
        
        layout.addWidget(self.prob_frame)
        
        # Buttons
        self.button_frame = QtWidgets.QFrame()
        button_layout = QtWidgets.QHBoxLayout(self.button_frame)
        button_layout.setSpacing(15)
        
        # Skip button
        self.skip_btn = QtWidgets.QPushButton("Maybe Later")
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background: #444444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 25px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #555555;
            }
        """)
        self.skip_btn.setToolTip("Save this encounter for later when you are stronger.\nYou can relaunch it from the Entitidex.")
        self.skip_btn.clicked.connect(self._on_skip)
        button_layout.addWidget(self.skip_btn)
        
        # Bond button
        self.bond_btn = QtWidgets.QPushButton("🤝 Attempt Bond!")
        self.bond_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {rarity_color}, stop:1 #FFD700
                );
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FFD700, stop:1 {rarity_color}
                );
            }}
        """)
        self.bond_btn.clicked.connect(self._on_bond)
        button_layout.addWidget(self.bond_btn)
        
        layout.addWidget(self.button_frame)
        
        # Set dark theme
        self.setStyleSheet("""
            QDialog {
                background: #121212;
            }
        """)

        # APPLY OPACITY EFFECTS (Initially Invisible)
        self._set_opacity(self.name_label, 0)
        self._set_opacity(self.svg_container, 0)
        self._set_opacity(self.rarity_container, 0)
        self._set_opacity(self.power_label, 0)
        self._set_opacity(self.theme_label, 0)
        self._set_opacity(self.lore_label, 0)
        self._set_opacity(self.prob_frame, 0)
        self._set_opacity(self.button_frame, 0)

    def _set_opacity(self, widget: QtWidgets.QWidget, opacity: float) -> None:
        """Helper to set opacity effect on a widget."""
        effect = QtWidgets.QGraphicsOpacityEffect(widget)
        effect.setOpacity(opacity)
        widget.setGraphicsEffect(effect)

    def _fade_in(self, widget: QtWidgets.QWidget, duration: int = 500) -> None:
        """Start fade in animation for a widget."""
        effect = widget.graphicsEffect()
        if effect:
            anim = QtCore.QPropertyAnimation(effect, b"opacity")
            anim.setDuration(duration)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QtCore.QEasingCurve.OutQuad)
            anim.start()
            self._anims.append(anim)

    def _get_probability_color(self, percent: int) -> str:
        """Get color based on probability percentage."""
        if percent >= 75:
            return "#4CAF50"  # Green - high chance
        elif percent >= 50:
            return "#8BC34A"  # Light green
        elif percent >= 35:
            return "#FFC107"  # Yellow/amber
        elif percent >= 20:
            return "#FF9800"  # Orange
        else:
            return "#F44336"  # Red - low chance
    
    def _start_reveal_animation(self) -> None:
        """Start the entity reveal animation sequence."""
        # Note: No layout activation/recalculation needed as widgets are already there
        
        # Phase 1: Show title with suspense (0-1s)
        QtCore.QTimer.singleShot(1000, self._reveal_entity_name)
    
    def _reveal_entity_name(self) -> None:
        """Reveal the entity name and image."""
        # Use exceptional name if available for exceptional encounters
        if self.is_exceptional and self.entity.exceptional_name:
            display_name = self.entity.exceptional_name
        else:
            display_name = self.entity.name
        self.title_label.setText(f"✨ {display_name} ✨")
        
        self._fade_in(self.name_label)
        self._fade_in(self.svg_container)
        self._fade_in(self.rarity_container)
        
        # Phase 2: Show power and theme (0.5s later)
        QtCore.QTimer.singleShot(500, self._reveal_stats)
    
    def _reveal_stats(self) -> None:
        """Reveal power and theme info."""
        self._fade_in(self.power_label)
        self._fade_in(self.theme_label)
        
        # Phase 3: Show lore (0.5s later)
        QtCore.QTimer.singleShot(500, self._reveal_lore)
    
    def _reveal_lore(self) -> None:
        """Reveal the entity lore."""
        self._fade_in(self.lore_label)
        
        # Phase 4: Show probability and buttons (0.5s later)
        QtCore.QTimer.singleShot(500, self._show_actions)
    
    def _show_actions(self) -> None:
        """Show probability display and action buttons."""
        self._fade_in(self.prob_frame)
        self._fade_in(self.button_frame)
    
    def _on_bond(self) -> None:
        """Handle bond button click."""
        self.bond_attempted.emit(self.entity.id)
        self.accept()
    
    def _on_skip(self) -> None:
        """Handle skip button click."""
        # Inform user about saving
        styled_info(
            self,
            "Encounter Saved",
            "This encounter has been saved for later!\n\n"
            "You can relaunch it from the 'Saved Encounters' button in the Entitidex tab when you are stronger."
        )
        self.encounter_skipped.emit()
        self.reject()


class BondResultDialog(QtWidgets.QDialog):
    """
    Dialog showing the result of a bond attempt.
    
    Displays success or failure with appropriate animations and messages.
    """
    
    def __init__(self, entity: Entity, success: bool, probability: float,
                 pity_bonus: float, consecutive_fails: int,
                 parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the bond result dialog.
        
        Args:
            entity: The entity that was bonded with
            success: Whether the bond succeeded
            probability: The probability used for the attempt
            pity_bonus: Pity bonus that was applied
            consecutive_fails: Current fail streak (if failed)
            parent: Parent widget
        """
        super().__init__(parent)
        self.entity = entity
        self.success = success
        self.probability = probability
        self.pity_bonus = pity_bonus
        self.consecutive_fails = consecutive_fails
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the result dialog UI."""
        self.setWindowTitle("Bond Result")
        self.setFixedSize(400, 350)
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.CustomizeWindowHint
        )
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        if self.success:
            self._setup_success_ui(layout)
        else:
            self._setup_failure_ui(layout)
        
        # OK button
        ok_btn = QtWidgets.QPushButton("Continue")
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #66BB6A;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn, alignment=QtCore.Qt.AlignCenter)
        
        self.setStyleSheet("""
            QDialog {
                background: #121212;
            }
        """)
    
    def _setup_success_ui(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Set up UI for successful bond."""
        # Big success emoji
        emoji = QtWidgets.QLabel("🎉")
        emoji.setAlignment(QtCore.Qt.AlignCenter)
        emoji.setStyleSheet("font-size: 64px;")
        layout.addWidget(emoji)
        
        # Success message
        title = QtWidgets.QLabel("Bond Successful!")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
            }
        """)
        layout.addWidget(title)
        
        # Entity joined message
        message = QtWidgets.QLabel(f"{self.entity.name} has joined your team!")
        message.setAlignment(QtCore.Qt.AlignCenter)
        message.setWordWrap(True)
        message.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(message)
        
        # Power gained
        power_msg = QtWidgets.QLabel(f"+{self.entity.power} Power to your collection!")
        power_msg.setAlignment(QtCore.Qt.AlignCenter)
        power_msg.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #FFD700;
            }
        """)
        layout.addWidget(power_msg)
    
    def _setup_failure_ui(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Set up UI for failed bond."""
        # Sad emoji
        emoji = QtWidgets.QLabel("💨")
        emoji.setAlignment(QtCore.Qt.AlignCenter)
        emoji.setStyleSheet("font-size: 64px;")
        layout.addWidget(emoji)
        
        # Failure message
        title = QtWidgets.QLabel("They Slipped Away...")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #FF9800;
            }
        """)
        layout.addWidget(title)
        
        # Encouragement message
        message = QtWidgets.QLabel(f"{self.entity.name} wasn't ready yet.\nKeep focusing to encounter them again!")
        message.setAlignment(QtCore.Qt.AlignCenter)
        message.setWordWrap(True)
        message.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #CCCCCC;
            }
        """)
        layout.addWidget(message)
        
        # Pity system hint
        pity_t1 = int(CATCH_CONFIG.get("pity_threshold_1", 6))
        pity_t2 = int(CATCH_CONFIG.get("pity_threshold_2", 12))
        pity_t3 = int(CATCH_CONFIG.get("pity_threshold_3", 18))
        pity_b1 = int(CATCH_CONFIG.get("pity_bonus_1", 0.08) * 100)
        pity_b2 = int(CATCH_CONFIG.get("pity_bonus_2", 0.18) * 100)
        pity_b3 = int(CATCH_CONFIG.get("pity_bonus_3", 0.35) * 100)

        if self.consecutive_fails >= max(3, pity_t1 - 2):
            pity_hint = ""
            if self.consecutive_fails >= pity_t3:
                pity_hint = f"Maximum pity bonus active! (+{pity_b3}%)"
            elif self.consecutive_fails >= pity_t2:
                pity_hint = f"High pity bonus active! (+{pity_b2}%)"
            elif self.consecutive_fails >= pity_t1:
                pity_hint = f"Pity bonus building... (+{pity_b1}%)"
            else:
                pity_hint = f"Consecutive misses: {self.consecutive_fails}"
            
            pity_label = QtWidgets.QLabel(pity_hint)
            pity_label.setAlignment(QtCore.Qt.AlignCenter)
            pity_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #888888;
                    font-style: italic;
                }
            """)
            layout.addWidget(pity_label)


class EntitidexCollectionDialog(QtWidgets.QDialog):
    """
    Dialog showing the user's full Entitidex collection.
    
    Displays all captured entities organized by theme and rarity,
    with collection progress statistics.
    """
    
    def __init__(self, adhd_buster: dict, parent: Optional[QtWidgets.QWidget] = None):
        """
        Initialize the collection dialog.
        
        Args:
            adhd_buster: Hero data dictionary with entitidex data
            parent: Parent widget
        """
        super().__init__(parent)
        self.adhd_buster = adhd_buster
        
        # Import here to avoid circular imports
        from gamification import get_entitidex_stats
        self.stats = get_entitidex_stats(adhd_buster)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the collection dialog UI."""
        self.setWindowTitle("🔖 Entitidex Collection")
        self.setMinimumSize(700, 500)
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.WindowCloseButtonHint
        )
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with stats
        header = self._create_header()
        layout.addWidget(header)
        
        # Tab widget for themes
        tabs = QtWidgets.QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333333;
                border-radius: 8px;
                background: #1E1E1E;
            }
            QTabBar::tab {
                background: #2D2D2D;
                color: #AAAAAA;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1E1E1E;
                color: #FFFFFF;
            }
        """)
        
        # Create tabs for each available entity theme (dynamic, no hardcoded theme count)
        from entitidex.entity_pools import get_entity_count_by_theme
        theme_labels = {
            "warrior": "🛡️ Warrior",
            "scholar": "📚 Scholar",
            "wanderer": "🧭 Wanderer",
            "underdog": "💪 Underdog",
            "scientist": "🔬 Scientist",
            "robot": "🤖 Robot",
            "space_pirate": "🏴‍☠️ Space Pirate",
            "thief": "Thief",
            "zoo_worker": "Zoo Worker",
        }
        theme_ids = list(get_entity_count_by_theme().keys())
        
        for theme_id in theme_ids:
            theme_name = theme_labels.get(theme_id, theme_id.replace("_", " ").title())
            tab = self._create_theme_tab(theme_id)
            tabs.addTab(tab, theme_name)
        
        layout.addWidget(tabs)
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #444444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #555555;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=QtCore.Qt.AlignCenter)
        
        self.setStyleSheet("""
            QDialog {
                background: #121212;
            }
        """)
    
    def _create_header(self) -> QtWidgets.QFrame:
        """Create the header with collection stats."""
        frame = QtWidgets.QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #1E1E1E;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        layout = QtWidgets.QHBoxLayout(frame)
        
        # Collection progress
        from entitidex.entity_pools import get_total_entity_count
        
        progress_pct = self.stats["completion_percentage"]
        caught = self.stats["total_caught"]
        total = get_total_entity_count()
        
        progress_label = QtWidgets.QLabel(f"Collection: {caught}/{total} ({progress_pct:.1f}%)")
        progress_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(progress_label)
        
        layout.addStretch()
        
        # Total encounters
        encounters_label = QtWidgets.QLabel(f"Total Encounters: {self.stats['total_encounters']}")
        encounters_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #888888;
            }
        """)
        layout.addWidget(encounters_label)
        
        return frame
    
    def _create_theme_tab(self, theme_id: str) -> QtWidgets.QWidget:
        """Create a tab for a specific theme."""
        from entitidex import get_entities_for_story
        
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Get entities for this theme
        entities = get_entities_for_story(theme_id)
        
        # Get captured entity IDs
        captured_ids = set(self.stats["collection_by_theme"].get(theme_id, []))
        
        # Create grid of entity cards
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        
        for i, entity in enumerate(entities):
            row = i // 3
            col = i % 3
            
            is_captured = entity.id in captured_ids
            card = self._create_entity_card(entity, is_captured)
            grid.addWidget(card, row, col)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        # Theme progress
        captured_count = len(captured_ids)
        total_count = len(entities)
        progress_label = QtWidgets.QLabel(f"Theme Progress: {captured_count}/{total_count}")
        progress_label.setAlignment(QtCore.Qt.AlignCenter)
        progress_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #888888;
            }
        """)
        layout.addWidget(progress_label)
        
        return widget
    
    def _create_entity_card(self, entity: Entity, is_captured: bool) -> QtWidgets.QFrame:
        """Create a card for a single entity."""
        rarity_colors = {
            "common": "#9E9E9E",
            "uncommon": "#4CAF50",
            "rare": "#2196F3",
            "epic": "#9C27B0",
            "legendary": "#FF9800",
            "celestial": "#00E5FF",
        }
        
        color = rarity_colors.get(entity.rarity.lower(), "#9E9E9E")
        
        frame = QtWidgets.QFrame()
        if is_captured:
            frame.setStyleSheet(f"""
                QFrame {{
                    background: #2D2D2D;
                    border: 2px solid {color};
                    border-radius: 8px;
                    padding: 8px;
                }}
            """)
        else:
            frame.setStyleSheet("""
                QFrame {
                    background: #1A1A1A;
                    border: 2px solid #333333;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
        
        layout = QtWidgets.QVBoxLayout(frame)
        layout.setSpacing(5)
        
        if is_captured:
            # Show entity info
            name = QtWidgets.QLabel(entity.name)
            name.setAlignment(QtCore.Qt.AlignCenter)
            name.setWordWrap(True)
            name.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    font-weight: bold;
                    color: {color};
                }}
            """)
            layout.addWidget(name)
            
            power = QtWidgets.QLabel(f"⚡ {entity.power}")
            power.setAlignment(QtCore.Qt.AlignCenter)
            power.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    color: #FFD700;
                }
            """)
            layout.addWidget(power)
            
            rarity = QtWidgets.QLabel(entity.rarity.capitalize())
            rarity.setAlignment(QtCore.Qt.AlignCenter)
            rarity.setStyleSheet(f"""
                QLabel {{
                    font-size: 10px;
                    color: {color};
                }}
            """)
            layout.addWidget(rarity)
        else:
            # Show placeholder
            mystery = QtWidgets.QLabel("❔")
            mystery.setAlignment(QtCore.Qt.AlignCenter)
            mystery.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    color: #444444;
                }
            """)
            layout.addWidget(mystery)
            
            unknown = QtWidgets.QLabel("Unknown")
            unknown.setAlignment(QtCore.Qt.AlignCenter)
            unknown.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    color: #555555;
                }
            """)
            layout.addWidget(unknown)
        
        frame.setFixedSize(120, 100)
        return frame

