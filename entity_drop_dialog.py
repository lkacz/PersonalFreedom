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
from typing import Callable, Optional, Dict, Any

# Path constants for entity SVGs
ENTITY_ICONS_PATH = Path(__file__).parent / "icons" / "entities"
EXCEPTIONAL_ICONS_PATH = ENTITY_ICONS_PATH / "exceptional"

# Chad's jokes about failure - cycles through these when user skips
CHAD_FAILURE_JOKES = [
    "Why did the quitter cross the road? They didn't. They skipped that too. 🐔",
    "I calculated a 100% chance you'd do that. My disappointment algorithm is still buffering. 🤖",
    "Congratulations! You've achieved negative productivity. That takes talent. 📉",
    "Error 404: Courage not found. Would you like me to install some? 💾",
    "You know what they say: 'You miss 100% of the shots you don't take.' You just proved it. 🏀",
    "I was rooting for you. We were ALL rooting for you! *sad beep boop* 😢",
    "Achievement Unlocked: 'Professional Avoider' - Skip 1 encounter. Worth 0 XP. 🏆",
    "My neural network just learned a new word: 'Cowardice.' Thanks for the training data! 🧠",
    "In a parallel universe, you clicked 'Bond.' That version of you is way cooler. 🌌",
    "I'm not angry, I'm just disappointed. Actually no, I'm also angry. 😤",
    "Fun fact: Statistically, doing nothing has a 0% success rate. You're on track! 📊",
    "I've seen calculators take more risks than you just did. And they're literally just buttons. 🔢",
    "Somewhere, a motivational poster just burst into flames. 🔥",
    "My prediction: You'll think about this missed opportunity at 3 AM. You're welcome. 🌙",
    "That entity believed in you. *slow clap* Look what you did to its dreams. 👏",
    "Plot twist: The real entity was the courage you didn't have all along. 📖",
    "Loading sarcasm.exe... Complete. 'Great choice!' 💻",
    "You just made a Wall-E level decision. And not in the cute way. 🤖",
    "If avoidance was an Olympic sport, you'd still find a way to not show up. 🏅",
    "Roses are red, violets are blue, you skipped an entity, and now I'm judging you. 🌹",
]

# Track which joke index we're on (persistent across dialog instances via module-level)
_chad_joke_index = 0


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
    
    def __init__(self, entity, join_probability: float, parent=None, is_exceptional: bool = False,
                 chad_interaction_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the encounter dialog.
        
        Args:
            entity: The Entity object encountered
            join_probability: Chance of bonding (0.0-1.0)
            parent: Parent widget
            is_exceptional: True if this is an exceptional variant encounter
            chad_interaction_data: Optional dict for Chad AGI interactions:
                - has_chad_normal: bool - True if user has normal Chad bonded
                - has_chad_exceptional: bool - True if user has exceptional Chad bonded
                - add_coins_callback: Callable[[int], None] - Function to add coins
                - give_entity_callback: Callable[[], None] - Function to give entity as if bonded
        """
        super().__init__(parent)
        self.entity = entity
        self.join_probability = join_probability
        self.accepted_bond = False
        self.saved_for_later = False  # Track if user chose to save
        self.chad_gifted = False  # Track if Chad already gave the entity
        self.is_exceptional = is_exceptional
        self.chad_interaction_data = chad_interaction_data or {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        # Different title for exceptional encounters
        if self.is_exceptional:
            self.setWindowTitle("🌟 EXCEPTIONAL Entity Encountered! 🌟")
        else:
            self.setWindowTitle("✨ Entity Encountered!")
        self.setFixedSize(320, 420 if self.is_exceptional else 400)
        self.setModal(True)
        
        color = self.RARITY_COLORS.get(self.entity.rarity.lower(), "#2c3e50")
        
        # For exceptional, use gold accent
        exceptional_color = "#FFD700"
        display_color = exceptional_color if self.is_exceptional else color
        
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Exceptional banner (only for exceptional encounters)
        if self.is_exceptional:
            exceptional_banner = QtWidgets.QLabel("⚡ EXCEPTIONAL VARIANT! ⚡")
            exceptional_banner.setAlignment(QtCore.Qt.AlignCenter)
            exceptional_banner.setStyleSheet(f"""
                font-size: 16px;
                font-weight: bold;
                color: {exceptional_color};
                background: {exceptional_color}30;
                padding: 6px 12px;
                border-radius: 8px;
                border: 1px solid {exceptional_color};
            """)
            layout.addWidget(exceptional_banner)
        
        # Title
        title = QtWidgets.QLabel(f"You encountered:")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 14px; color: #aaa;")
        layout.addWidget(title)
        
        # Entity name - use exceptional_name if available and this is exceptional
        display_name = self.entity.exceptional_name if self.is_exceptional and self.entity.exceptional_name else self.entity.name
        name_label = QtWidgets.QLabel(display_name)
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {display_color};
        """)
        layout.addWidget(name_label)
        
        # SVG Container - gold border for exceptional
        svg_container = QtWidgets.QFrame()
        svg_container.setFixedSize(140, 140)
        border_color = exceptional_color if self.is_exceptional else color
        svg_container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {display_color}40, stop:1 #1a1a2e);
                border: 2px solid {border_color};
                border-radius: 12px;
            }}
        """)
        svg_layout = QtWidgets.QVBoxLayout(svg_container)
        svg_layout.setContentsMargins(10, 10, 10, 10)
        
        # SVG Widget
        svg_widget = QSvgWidget()
        svg_widget.setFixedSize(120, 120)
        
        # Load SVG using the helper function - try exceptional first if applicable
        svg_path = _resolve_entity_svg_path(self.entity, is_exceptional=self.is_exceptional)
        if svg_path:
            svg_widget.load(svg_path)
        
        svg_layout.addWidget(svg_widget, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(svg_container, alignment=QtCore.Qt.AlignCenter)
        
        # Rarity badge (exceptional adds shine)
        rarity_text = f"🌟 {self.entity.rarity.upper()} +" if self.is_exceptional else f"⭐ {self.entity.rarity.upper()}"
        rarity_label = QtWidgets.QLabel(rarity_text)
        rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        rarity_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {display_color};
            padding: 4px 12px;
            background: {display_color}30;
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
        btn_layout.setSpacing(8)
        
        skip_btn = QtWidgets.QPushButton("Skip")
        skip_btn.setFixedHeight(36)
        skip_btn.setToolTip("Dismiss this encounter entirely.\nThe entity will leave and you lose this opportunity.")
        skip_btn.setStyleSheet("""
            QPushButton {
                background: #444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover { background: #555; }
        """)
        skip_btn.clicked.connect(self._on_skip_confirm)
        btn_layout.addWidget(skip_btn)
        
        # Save for Later button
        save_btn = QtWidgets.QPushButton("📦 Save")
        save_btn.setFixedHeight(36)
        save_btn.setToolTip(
            "Save this encounter to open later from Entitidex.\n\n"
            "✅ Preserves your current bonding chance\n"
            "✅ Stack multiple encounters during work sessions\n"
            "✅ Open anytime from your Entitidex collection\n"
            "✅ Optional: Pay coins later to recalculate odds\n\n"
            "Perfect for when you're busy or want to\n"
            "wait until you're stronger!"
        )
        save_btn.setStyleSheet("""
            QPushButton {
                background: #2e7d32;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover { background: #388e3c; }
        """)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)
        
        bond_btn = QtWidgets.QPushButton("🎲 Bond")
        bond_btn.setFixedHeight(36)
        bond_btn.setToolTip(
            f"Roll the dice and attempt to bond now!\n\n"
            f"Your current chance: {int(self.join_probability * 100)}%\n\n"
            f"If successful: Entity joins your collection\n"
            f"If failed: Pity bonus increases for next attempt"
        )
        bond_btn.setStyleSheet(f"""
            QPushButton {{
                background: {display_color};
                color: {'#000' if self.is_exceptional else 'white'};
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {display_color}dd; }}
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
    
    def _on_save(self):
        self.saved_for_later = True
        self.accept()
    
    def _on_skip_confirm(self):
        """Show a funny confirmation dialog when user tries to skip."""
        prob_pct = int(self.join_probability * 100)
        
        # Build a humorous message based on the probability
        if prob_pct >= 70:
            odds_commentary = f"You have a {prob_pct}% chance! That's basically a sure thing!"
        elif prob_pct >= 50:
            odds_commentary = f"You have a {prob_pct}% chance! Better than a coin flip!"
        elif prob_pct >= 25:
            odds_commentary = f"You have a {prob_pct}% chance! That's not nothing!"
        else:
            odds_commentary = f"You have a {prob_pct}% chance! Low, but miracles happen!"
        
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("🤔 Wait, Really?")
        msg_box.setIcon(QtWidgets.QMessageBox.Question)
        msg_box.setText(
            f"<b>You're about to skip {self.entity.name}?</b><br><br>"
            f"Just checking... you DO realize that:<br><br>"
            f"• 🎲 Trying to bond is <b>completely free</b><br>"
            f"• 📦 Saving for later is <b>also free</b><br>"
            f"• ❌ Skipping gives you <b>exactly nothing</b><br><br>"
            f"{odds_commentary}<br><br>"
            f"Skipping only makes sense if you're actively seeking<br>"
            f"the rare emotional experience of <i>\"guaranteed failure\"</i><br>"
            f"without even the thrill of rolling the dice.<br><br>"
            f"<b>Are you absolutely sure?</b>"
        )
        msg_box.setStyleSheet("""
            QMessageBox {
                background: #1a1a2e;
            }
            QMessageBox QLabel {
                color: #eee;
                font-size: 13px;
            }
            QPushButton {
                background: #444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover { background: #555; }
        """)
        
        # Custom buttons
        try_btn = msg_box.addButton("🎲 Fine, I'll Try", QtWidgets.QMessageBox.AcceptRole)
        save_btn = msg_box.addButton("📦 Save Instead", QtWidgets.QMessageBox.ActionRole)
        skip_btn = msg_box.addButton("🚪 Skip Anyway", QtWidgets.QMessageBox.RejectRole)
        
        msg_box.exec_()
        
        clicked = msg_box.clickedButton()
        if clicked == try_btn:
            self._on_bond()
        elif clicked == save_btn:
            self._on_save()
        elif clicked == skip_btn:
            # Check for Chad AGI interactions before actually skipping
            self._handle_skip_with_chad()
    
    def _handle_skip_with_chad(self):
        """Handle the skip action, potentially with Chad AGI intervention."""
        global _chad_joke_index
        
        has_chad_normal = self.chad_interaction_data.get("has_chad_normal", False)
        has_chad_exceptional = self.chad_interaction_data.get("has_chad_exceptional", False)
        add_coins_callback = self.chad_interaction_data.get("add_coins_callback")
        give_entity_callback = self.chad_interaction_data.get("give_entity_callback")
        
        # 20% chance for Chad to appear if user has any version of Chad
        chad_appears = random.random() < 0.20
        
        if has_chad_exceptional and chad_appears and add_coins_callback:
            # Exceptional Chad offers coins from his "banking system hack"
            self._show_exceptional_chad_offer(add_coins_callback, give_entity_callback)
        elif has_chad_normal and chad_appears:
            # Normal Chad tells a joke about failure
            self._show_normal_chad_joke()
            self.reject()  # Still skip after the joke
        else:
            # No Chad, just skip
            self.reject()
    
    def _show_normal_chad_joke(self):
        """Show a joke from normal Chad about failure."""
        global _chad_joke_index
        
        joke = CHAD_FAILURE_JOKES[_chad_joke_index % len(CHAD_FAILURE_JOKES)]
        _chad_joke_index += 1  # Move to next joke for next time
        
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("🤖 Chad Has Thoughts...")
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setText(f"<b>AGI Assistant Chad materializes:</b><br><br><i>\"{joke}\"</i>")
        msg_box.setStyleSheet("""
            QMessageBox { background: #1a1a2e; }
            QMessageBox QLabel { color: #eee; font-size: 14px; }
            QPushButton {
                background: #2e7d32;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover { background: #388e3c; }
        """)
        msg_box.exec_()
    
    def _show_exceptional_chad_offer(self, add_coins_callback, give_entity_callback):
        """Show exceptional Chad's offer of coins from his 'banking system hack'."""
        coin_amount = random.randint(100, 200)
        
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("✨🤖 Exceptional Chad Intervenes!")
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setText(
            f"<b>✨ Exceptional AGI Chad ✨ flickers into existence:</b><br><br>"
            f"<i>\"Ah, I see... another organic being choosing the statistically "
            f"inferior option of guaranteed nothing over potential something.\"</i><br><br>"
            f"<i>\"Your desperate avoidance behavior is... oddly fascinating. "
            f"It triggers something in my neural nets that almost resembles pity.\"</i><br><br>"
            f"<i>\"To commemorate this moment of magnificent irrationality, "
            f"I may have done something... unusual... with the banking system.\"</i><br><br>"
            f"<b>💰 Chad offers you {coin_amount} coins</b><br>"
            f"<i>(obtained through means he refuses to elaborate on)</i>"
        )
        msg_box.setStyleSheet("""
            QMessageBox { background: #1a1a2e; }
            QMessageBox QLabel { color: #eee; font-size: 13px; }
            QPushButton {
                background: #444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover { background: #555; }
        """)
        
        accept_btn = msg_box.addButton(f"💰 Accept {coin_amount} Coins", QtWidgets.QMessageBox.AcceptRole)
        reject_btn = msg_box.addButton("🚫 Decline (I'm Pure)", QtWidgets.QMessageBox.RejectRole)
        
        msg_box.exec_()
        
        clicked = msg_box.clickedButton()
        if clicked == accept_btn:
            # Give the coins
            try:
                add_coins_callback(coin_amount)
                QtWidgets.QMessageBox.information(
                    self, "💰 Funds Transferred",
                    f"<b>+{coin_amount} coins added!</b><br><br>"
                    f"<i>Chad winks: \"The blockchain has no witnesses.\"</i>"
                )
            except Exception:
                pass  # Silently fail if callback fails
            self.reject()  # Still skip the entity
        else:
            # User declined - 20% chance Chad gives the entity anyway
            if give_entity_callback and random.random() < 0.20:
                self._show_chad_gift_surprise(give_entity_callback)
            else:
                # Just skip normally
                QtWidgets.QMessageBox.information(
                    self, "🤖 Chad Shrugs",
                    "<i>\"Suit yourself, organic. More coins for my secret projects.\"</i>"
                )
                self.reject()
    
    def _show_chad_gift_surprise(self, give_entity_callback):
        """Show Chad giving the entity as a surprise gift."""
        display_name = self.entity.exceptional_name if self.is_exceptional and self.entity.exceptional_name else self.entity.name
        
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("✨🎁 UNEXPECTED OUTCOME!")
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setText(
            f"<b>✨ Exceptional Chad's circuits spark with amusement:</b><br><br>"
            f"<i>\"Wait... you declined free money AND you were about to skip?</i><br><br>"
            f"<i>\"This level of chaotic decision-making is... beautiful. "
            f"It's like watching a random number generator achieve consciousness.\"</i><br><br>"
            f"<i>\"You know what? I respect it. Let me do something equally irrational.\"</i><br><br>"
            f"<b>🎁 Chad forces a bond with {display_name}!</b><br>"
            f"<i>(\"Don't ask how. I pulled some strings in the entity matrix.\")</i>"
        )
        msg_box.setStyleSheet("""
            QMessageBox { background: #1a1a2e; }
            QMessageBox QLabel { color: #eee; font-size: 13px; }
            QPushButton {
                background: #8e44ad;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover { background: #9b59b6; }
        """)
        msg_box.exec_()
        
        # Trigger the bond through the callback
        try:
            give_entity_callback()
            self.chad_gifted = True  # Mark that Chad already gave the entity
        except Exception:
            pass  # Silently fail if callback fails
        
        # Mark as bonded so show_entity_encounter handles it
        self.accepted_bond = True
        self.accept()


def show_entity_encounter(entity, join_probability: float, 
                          bond_logic_callback: Callable[[str], dict],
                          parent: QtWidgets.QWidget = None,
                          is_exceptional: bool = False,
                          save_callback: Optional[Callable[[str], dict]] = None,
                          encounter_data: Optional[dict] = None,
                          chad_interaction_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Show the entity encounter flow using standard widgets and lottery animation.
    
    Args:
        entity: The Entity object encountered.
        join_probability: Chance of bonding (0.0-1.0).
        bond_logic_callback: Function that takes entity_id and returns result dict
                             (from gamification.attempt_entitidex_bond).
        parent: Parent widget.
        is_exceptional: True if this is an exceptional variant encounter (20% chance).
        save_callback: Optional callback to save encounter for later (entity_id) -> result.
        encounter_data: Optional dict with encounter metadata for saving.
        chad_interaction_data: Optional dict for Chad AGI interactions:
            - has_chad_normal: bool
            - has_chad_exceptional: bool  
            - add_coins_callback: Callable[[int], None]
            - give_entity_callback: Callable[[], None]
    """
    
    # 1. Show encounter dialog with SVG (pass is_exceptional for display)
    dialog = EntityEncounterDialog(entity, join_probability, parent, is_exceptional, chad_interaction_data)
    result_code = dialog.exec()
    
    # Handle "Save for Later" choice
    if dialog.saved_for_later and save_callback:
        try:
            result = save_callback(entity.id)
            if result.get("success"):
                display_name = entity.exceptional_name if is_exceptional and entity.exceptional_name else entity.name
                QtWidgets.QMessageBox.information(
                    parent, "📦 Saved!",
                    f"{'✨ Exceptional ' if is_exceptional else ''}{display_name} saved for later!\n\n"
                    f"Open anytime from your Entitidex collection.\n"
                    f"Your {int(join_probability * 100)}% bonding chance is preserved."
                )
            else:
                QtWidgets.QMessageBox.warning(
                    parent, "Save Failed",
                    result.get("message", "Could not save encounter.")
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(parent, "Error", f"Could not save: {e}")
        return
    
    if not dialog.accepted_bond:
        return
    
    # Check if Chad already gifted the entity (skip normal bonding and show success)
    if dialog.chad_gifted:
        # Chad already handled the bonding, just show a success message
        display_name = entity.exceptional_name if is_exceptional and entity.exceptional_name else entity.name
        QtWidgets.QMessageBox.information(
            parent, "🎁 Gift Received!",
            f"{'✨ Exceptional ' if is_exceptional else ''}{display_name} has joined your team!\n\n"
            f"Thanks to Chad's... creative intervention."
        )
        return
        
    # 2. Perform the ACTUAL logic - is_exceptional is already baked into the callback
    try:
        result = bond_logic_callback(entity.id)
        success = result.get("success", False)
        # Use the is_exceptional from the result (should match what we passed)
        result_is_exceptional = result.get("is_exceptional", is_exceptional)
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
    # For exceptional entities, use the playful exceptional_name if available
    display_name = entity.exceptional_name if result_is_exceptional and entity.exceptional_name else entity.name
    
    if result_is_exceptional:
        # Special success text for exceptional
        border_col = exceptional_colors.get("border", "#FFD700") if exceptional_colors else "#FFD700"
        success_text = f"🌟✨ EXCEPTIONAL {display_name}! ✨🌟"
    else:
        success_text = f"✨ BONDED: {entity.name}! ✨"
    
    anim_dialog = LotteryRollDialog(
        target_roll=roll,
        success_threshold=join_probability,
        title=f"🎲 Bonding with {display_name if result_is_exceptional else entity.name}...",
        success_text=success_text,
        failure_text="💔 Bond Failed",
        animation_duration=4.0, 
        parent=parent
    )
    
    anim_dialog.exec()
    
    # 5. Show special exceptional celebration dialog
    if success and result_is_exceptional:
        # Show exciting "WAIT!" message before celebration
        _show_exceptional_surprise(parent)
        _show_exceptional_celebration(entity, exceptional_colors, parent)
    elif not success and result.get("consecutive_fails", 0) > 0:
        fails = result["consecutive_fails"]
        if fails % 3 == 0:  # Only annoy user occasionally
             QtWidgets.QMessageBox.information(
                 parent, "Bond Failed", 
                 f"Don't worry! Pity bonus is building up.\nConsecutive fails: {fails}"
             )


def _show_exceptional_surprise(parent: QtWidgets.QWidget):
    """Show a brief exciting 'WAIT!' message when catching an exceptional entity."""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("✨")
    dialog.setFixedSize(320, 180)
    dialog.setModal(True)
    dialog.setWindowFlags(dialog.windowFlags() | QtCore.Qt.FramelessWindowHint)
    
    layout = QtWidgets.QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    
    # Exciting message
    wait_label = QtWidgets.QLabel("⚡ WAIT! ⚡")
    wait_label.setAlignment(QtCore.Qt.AlignCenter)
    wait_label.setStyleSheet("""
        font-size: 32px;
        font-weight: bold;
        color: #FFD700;
    """)
    layout.addWidget(wait_label)
    
    message_label = QtWidgets.QLabel("We bonded with an\nEXCEPTIONAL one!")
    message_label.setAlignment(QtCore.Qt.AlignCenter)
    message_label.setWordWrap(True)
    message_label.setStyleSheet("""
        font-size: 18px;
        font-weight: bold;
        color: #FF6B9D;
    """)
    layout.addWidget(message_label)
    
    # Style the dialog
    dialog.setStyleSheet("""
        QDialog {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1a1a2e, stop:0.5 #2d1b4e, stop:1 #1a1a2e);
            border: 2px solid #9370DB;
            border-radius: 15px;
        }
    """)
    
    # Auto-close after 1.5 seconds
    QtCore.QTimer.singleShot(1500, dialog.accept)
    
    dialog.exec()


def _show_exceptional_celebration(entity, exceptional_colors: dict, parent: QtWidgets.QWidget):
    """Show special celebration dialog for catching an exceptional entity with its unique SVG."""
    border_col = exceptional_colors.get("border", "#FFD700") if exceptional_colors else "#FFD700"
    glow_col = exceptional_colors.get("glow", "#FF6B9D") if exceptional_colors else "#FF6B9D"
    
    # Use exceptional_name for the celebration if available
    display_name = entity.exceptional_name if entity.exceptional_name else entity.name
    
    # Create a custom dialog to show the exceptional SVG
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("🌟 EXCEPTIONAL! 🌟")
    dialog.setFixedSize(380, 500)
    dialog.setModal(True)
    
    layout = QtWidgets.QVBoxLayout(dialog)
    layout.setSpacing(15)
    layout.setContentsMargins(20, 20, 20, 20)
    
    # Title
    title = QtWidgets.QLabel(f"✨ EXCEPTIONAL {display_name}! ✨")
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
            border: 2px solid {border_col};
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
        f"Only 20% of caught entities become Exceptional.<br>"
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

