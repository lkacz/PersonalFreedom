"""
Enhanced Item Drop Dialog - Industry-Standard UX
=================================================
Celebratory dialog with animations, comparisons, and quick actions.
"""

from datetime import datetime
from typing import Optional
from PySide6 import QtWidgets, QtCore, QtGui

try:
    from gamification import (
        ITEM_RARITIES, RARITY_POWER, format_lucky_options,
        calculate_rarity_bonuses, STORY_GEAR_THEMES,
        get_slot_display_name, GAMIFICATION_AVAILABLE
    )
except ImportError:
    GAMIFICATION_AVAILABLE = False
    ITEM_RARITIES = {}
    RARITY_POWER = {}


class ItemComparisonWidget(QtWidgets.QWidget):
    """Side-by-side comparison of new item vs currently equipped."""
    
    def __init__(self, new_item: dict, equipped_item: Optional[dict] = None,
                 parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.new_item = new_item
        self.equipped_item = equipped_item
        self._build_ui()
    
    def _build_ui(self):
        """Build comparison display."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # New item (left)
        new_widget = self._create_item_card(self.new_item, "New Item", is_new=True)
        layout.addWidget(new_widget)
        
        # VS indicator
        vs_label = QtWidgets.QLabel("vs")
        vs_label.setAlignment(QtCore.Qt.AlignCenter)
        vs_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #999;
            padding: 0 8px;
        """)
        layout.addWidget(vs_label)
        
        # Current item (right) or "Empty" placeholder
        if self.equipped_item:
            current_widget = self._create_item_card(self.equipped_item, "Equipped", is_new=False)
        else:
            current_widget = self._create_empty_card()
        layout.addWidget(current_widget)
    
    def _create_item_card(self, item: dict, title: str, is_new: bool) -> QtWidgets.QWidget:
        """Create item card widget."""
        card = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(4)
        
        # Title
        title_label = QtWidgets.QLabel(title)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 10px; color: #666; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Rarity color
        rarity = item.get("rarity", "Common")
        rarity_info = ITEM_RARITIES.get(rarity, {})
        color = rarity_info.get("color", "#9e9e9e")
        
        # Item name
        name = item.get("name", "Unknown")
        name_label = QtWidgets.QLabel(name)
        name_label.setWordWrap(True)
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setStyleSheet(f"""
            color: {color};
            font-weight: bold;
            font-size: 11px;
        """)
        layout.addWidget(name_label)
        
        # Power
        power = item.get("power", RARITY_POWER.get(rarity, 10))
        power_label = QtWidgets.QLabel(f"⚔ {power}")
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setStyleSheet("color: #333; font-size: 12px; font-weight: bold;")
        layout.addWidget(power_label)
        
        # Card styling
        border_color = "#4caf50" if is_new else "#999"
        card.setStyleSheet(f"""
            QWidget {{
                background: white;
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        card.setFixedWidth(120)
        
        return card
    
    def _create_empty_card(self) -> QtWidgets.QWidget:
        """Create empty slot placeholder."""
        card = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(4)
        
        empty_label = QtWidgets.QLabel("Empty Slot")
        empty_label.setAlignment(QtCore.Qt.AlignCenter)
        empty_label.setStyleSheet("color: #999; font-size: 11px; font-style: italic;")
        layout.addWidget(empty_label)
        
        icon_label = QtWidgets.QLabel("∅")
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_label.setStyleSheet("color: #ccc; font-size: 32px;")
        layout.addWidget(icon_label)
        
        card.setStyleSheet("""
            QWidget {
                background: #f9f9f9;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        card.setFixedWidth(120)
        
        return card


class EnhancedItemDropDialog(QtWidgets.QDialog):
    """
    Enhanced item drop dialog with modern UX.
    
    Features:
    - Animated reveal
    - Item comparison with equipped gear
    - Quick equip button
    - Detailed stats and bonuses
    - Celebration based on rarity
    - Professional animations
    """
    
    quick_equip_requested = QtCore.Signal()
    view_inventory = QtCore.Signal()
    
    def __init__(self, item: dict, equipped_item: Optional[dict] = None,
                 session_minutes: int = 0, streak_days: int = 0, coins_earned: int = 0,
                 parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.item = item
        self.equipped_item = equipped_item
        self.session_minutes = session_minutes
        self.streak_days = streak_days
        self.coins_earned = coins_earned
        
        # Validate and set defaults
        self.item.setdefault("name", "Unknown Item")
        self.item.setdefault("rarity", "Common")
        self.item.setdefault("slot", "Unknown")
        self.item.setdefault("power", 10)
        
        self.setWindowTitle("🎁 Item Acquired!")
        self.setMinimumSize(450, 500)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        
        self._build_ui()
        QtCore.QTimer.singleShot(100, self._start_celebration)
    
    def _build_ui(self):
        """Build the complete dialog UI."""
        rarity = self.item.get("rarity", "Common")
        rarity_info = ITEM_RARITIES.get(rarity, {})
        color = rarity_info.get("color", "#9e9e9e")
        
        # Background colors by rarity (darker for lucky upgrades)
        if self.item.get("lucky_upgrade"):
            bg_colors = {
                "Common": "#2c2c2c",
                "Uncommon": "#1b3a1b",
                "Rare": "#1a2742",
                "Epic": "#2d1b3a",
                "Legendary": "#3a2c1b"
            }
        else:
            bg_colors = {
                "Common": "#f5f5f5",
                "Uncommon": "#e8f5e9",
                "Rare": "#e3f2fd",
                "Epic": "#f3e5f5",
                "Legendary": "#fff3e0"
            }
        bg_color = bg_colors.get(rarity, "#f5f5f5" if not self.item.get("lucky_upgrade") else "#2c2c2c")
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Header with rarity-based celebration
        if self.item.get("lucky_upgrade"):
            header_text = "🍀 LUCKY UPGRADE! 🍀"
        elif rarity == "Legendary":
            header_text = "⭐ LEGENDARY DROP! ⭐"
        elif rarity == "Epic":
            header_text = "💎 EPIC DROP! 💎"
        elif rarity == "Rare":
            header_text = "💠 RARE FIND! 💠"
        else:
            header_text = "✨ ITEM ACQUIRED! ✨"
        
        self.header_label = QtWidgets.QLabel(header_text)
        self.header_label.setAlignment(QtCore.Qt.AlignCenter)
        # Use bright colors for lucky upgrade dark background
        text_color = "#ffffff" if self.item.get("lucky_upgrade") else color
        self.header_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {text_color};
            padding: 10px;
            background: transparent;
        """)
        main_layout.addWidget(self.header_label)
        
        # Item visual
        item_visual = self._create_item_visual()
        main_layout.addWidget(item_visual)
        
        # Item name and details
        name_label = QtWidgets.QLabel(self.item.get("name", "Unknown Item"))
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setWordWrap(True)
        # Bright color for lucky upgrade dark background
        name_color = "#ffffff" if self.item.get("lucky_upgrade") else color
        name_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {name_color};
            background: transparent;
        """)
        main_layout.addWidget(name_label)
        
        # Stats line
        power = self.item.get("power", 10)
        slot = self.item.get("slot", "Unknown")
        stats_label = QtWidgets.QLabel(f"[{rarity} {slot}] ⚔ +{power} Power")
        stats_label.setAlignment(QtCore.Qt.AlignCenter)
        stats_color = "#cccccc" if self.item.get("lucky_upgrade") else color
        stats_label.setStyleSheet(f"color: {stats_color}; font-size: 13px; background: transparent;")
        main_layout.addWidget(stats_label)
        
        # Lucky options
        lucky_options = self.item.get("lucky_options", {})
        if lucky_options and format_lucky_options:
            try:
                lucky_text = format_lucky_options(lucky_options)
                if lucky_text:
                    lucky_label = QtWidgets.QLabel(f"✨ {lucky_text}")
                    lucky_label.setAlignment(QtCore.Qt.AlignCenter)
                    lucky_label.setStyleSheet("color: #8b5cf6; font-weight: bold; font-size: 12px;")
                    main_layout.addWidget(lucky_label)
            except Exception:
                pass
        
        # Separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #ddd;")
        main_layout.addWidget(line)
        
        # Comparison with equipped
        if self.equipped_item or True:  # Always show comparison
            comparison = ItemComparisonWidget(self.item, self.equipped_item)
            main_layout.addWidget(comparison)
        
        # Bonuses info
        if GAMIFICATION_AVAILABLE and (self.session_minutes > 0 or self.streak_days > 0):
            bonuses = calculate_rarity_bonuses(self.session_minutes, self.streak_days)
            if bonuses["total_bonus"] > 0:
                bonus_parts = []
                if bonuses["session_bonus"] > 0:
                    bonus_parts.append(f"⏱️ {self.session_minutes}min")
                if bonuses["streak_bonus"] > 0:
                    bonus_parts.append(f"🔥 {self.streak_days}day streak")
                bonus_text = " + ".join(bonus_parts) + f" = +{bonuses['total_bonus']}% drop luck!"
                
                bonus_label = QtWidgets.QLabel(bonus_text)
                bonus_label.setAlignment(QtCore.Qt.AlignCenter)
                bonus_label.setStyleSheet("color: #e65100; font-weight: bold; font-size: 11px;")
                main_layout.addWidget(bonus_label)
        
        # Coins earned
        if self.coins_earned > 0:
            coins_label = QtWidgets.QLabel(f"💰 +{self.coins_earned} Coins earned!")
            coins_label.setAlignment(QtCore.Qt.AlignCenter)
            coins_label.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 12px;")
            main_layout.addWidget(coins_label)
        
        # Motivational message
        messages = {
            "Common": ["Every item counts! 💪", "Building your arsenal!", "Nice find!"],
            "Uncommon": ["Nice find! 🌟", "Your focus is paying off!", "Quality gear!"],
            "Rare": ["Rare drop! You're on fire! 🔥", "Sweet loot! ⚡", "Excellent!"],
            "Epic": ["EPIC! Your dedication shows! 💜", "Champion tier! 👑", "Incredible!"],
            "Legendary": ["LEGENDARY! Unstoppable! ⭐", "GODLIKE FOCUS! 🏆", "You are a legend!"]
        }
        import random
        msg = random.choice(messages.get(rarity, messages["Common"]))
        msg_label = QtWidgets.QLabel(msg)
        msg_label.setAlignment(QtCore.Qt.AlignCenter)
        msg_label.setStyleSheet("font-weight: bold; color: #555; font-size: 13px;")
        main_layout.addWidget(msg_label)
        
        # Spacer
        main_layout.addStretch()
        
        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Quick equip (if slot is empty)
        if not self.equipped_item:
            equip_btn = QtWidgets.QPushButton("⚡ Quick Equip")
            equip_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #388e3c;
                }
            """)
            equip_btn.clicked.connect(self._on_quick_equip)
            button_layout.addWidget(equip_btn)
        
        # View inventory
        inventory_btn = QtWidgets.QPushButton("📦 Inventory")
        inventory_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        inventory_btn.clicked.connect(self._on_view_inventory)
        button_layout.addWidget(inventory_btn)
        
        # Close
        close_btn = QtWidgets.QPushButton("✓ Continue")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
        # Dialog style
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border: 3px solid {color};
                border-radius: 12px;
            }}
        """)
    
    def _create_item_visual(self) -> QtWidgets.QWidget:
        """Create visual representation of the item."""
        visual = QtWidgets.QLabel()
        visual.setAlignment(QtCore.Qt.AlignCenter)
        
        # Use pixmap if available, otherwise show large emoji
        rarity = self.item.get("rarity", "Common")
        stars = ["Common", "Uncommon", "Rare", "Epic", "Legendary"].index(rarity) + 1
        star_text = "★" * stars
        
        text = f"🎁\n{star_text}"
        visual.setText(text)
        visual.setStyleSheet("""
            font-size: 48px;
            padding: 20px;
        """)
        
        return visual
    
    def _start_celebration(self):
        """Start celebration animation."""
        rarity = self.item.get("rarity", "Common")
        
        # Pulse animation for header
        self._animation_step = 0
        self._animation_timer = QtCore.QTimer(self)
        self._animation_timer.timeout.connect(self._animate_pulse)
        self._animation_timer.start(200)
        
        # Play sound for Epic and Legendary
        if rarity in ["Epic", "Legendary"]:
            try:
                import winsound
                beeps = 3 if rarity == "Legendary" else 2
                for _ in range(beeps):
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
    
    def _animate_pulse(self):
        """Pulse animation for header."""
        self._animation_step += 1
        
        # Stop after 30 steps
        if self._animation_step >= 30:
            self._animation_timer.stop()
            return
        
        # Pulse effect with emoji rotation
        rarity = self.item.get("rarity", "Common")
        emojis = {
            "Legendary": ["⭐", "🌟", "✨", "💫", "🌠"],
            "Epic": ["💎", "💜", "✨", "🔮"],
            "Rare": ["💠", "🔷", "💙"],
            "Uncommon": ["✨", "🌟"],
            "Common": ["✨"]
        }
        emoji_list = emojis.get(rarity, ["✨"])
        emoji = emoji_list[self._animation_step % len(emoji_list)]
        
        if self.item.get("lucky_upgrade"):
            self.header_label.setText(f"{emoji} LUCKY UPGRADE! {emoji}")
        elif rarity == "Legendary":
            self.header_label.setText(f"{emoji} LEGENDARY DROP! {emoji}")
        elif rarity == "Epic":
            self.header_label.setText(f"{emoji} EPIC DROP! {emoji}")
        elif rarity == "Rare":
            self.header_label.setText(f"{emoji} RARE FIND! {emoji}")
        else:
            self.header_label.setText(f"{emoji} ITEM ACQUIRED! {emoji}")
    
    def _on_quick_equip(self):
        """Handle quick equip action."""
        self.quick_equip_requested.emit()
        self.accept()
    
    def _on_view_inventory(self):
        """Handle view inventory action."""
        self.view_inventory.emit()
        # Don't close dialog - let user manage inventory
    
    def mousePressEvent(self, event):
        """Allow clicking anywhere to close (except buttons)."""
        # Only close if clicking outside buttons
        pass  # Let button clicks handle themselves
    
    def closeEvent(self, event):
        """Clean up animations."""
        if hasattr(self, '_animation_timer'):
            self._animation_timer.stop()
        super().closeEvent(event)
