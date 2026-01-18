"""
Enhanced Item Drop Dialog - Styled Dark Theme
==============================================
Celebratory dialog with animations, comparisons, and quick actions.
Uses StyledDialog base for consistent frameless dark design.
"""

from datetime import datetime
from typing import Optional
from PySide6 import QtWidgets, QtCore, QtGui

from styled_dialog import StyledDialog

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
    """Side-by-side comparison of new item vs currently equipped (dark theme)."""
    
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
            color: #888888;
            padding: 0 8px;
            background: transparent;
        """)
        layout.addWidget(vs_label)
        
        # Current item (right) or "Empty" placeholder
        if self.equipped_item:
            current_widget = self._create_item_card(self.equipped_item, "Equipped", is_new=False)
        else:
            current_widget = self._create_empty_card()
        layout.addWidget(current_widget)
    
    def _create_item_card(self, item: dict, title: str, is_new: bool) -> QtWidgets.QWidget:
        """Create item card widget with dark theme."""
        card = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(4)
        
        # Title
        title_label = QtWidgets.QLabel(title)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 10px; color: #888888; font-weight: bold; background: transparent;")
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
            background: transparent;
        """)
        layout.addWidget(name_label)
        
        # Power
        power = item.get("power", RARITY_POWER.get(rarity, 10))
        power_label = QtWidgets.QLabel(f"⚔ {power}")
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setStyleSheet("color: #E0E0E0; font-size: 12px; font-weight: bold; background: transparent;")
        layout.addWidget(power_label)
        
        # Card styling - dark theme
        border_color = "#4caf50" if is_new else "#666666"
        card.setStyleSheet(f"""
            QWidget {{
                background: #1A1A2E;
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        card.setFixedWidth(120)
        
        return card
    
    def _create_empty_card(self) -> QtWidgets.QWidget:
        """Create empty slot placeholder with dark theme."""
        card = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(4)
        
        empty_label = QtWidgets.QLabel("Empty Slot")
        empty_label.setAlignment(QtCore.Qt.AlignCenter)
        empty_label.setStyleSheet("color: #666666; font-size: 11px; font-style: italic; background: transparent;")
        layout.addWidget(empty_label)
        
        icon_label = QtWidgets.QLabel("∅")
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_label.setStyleSheet("color: #444444; font-size: 32px; background: transparent;")
        layout.addWidget(icon_label)
        
        card.setStyleSheet("""
            QWidget {
                background: #0D0D1A;
                border: 2px dashed #444466;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        card.setFixedWidth(120)
        
        return card


class EnhancedItemDropDialog(StyledDialog):
    """
    Enhanced item drop dialog with dark themed modern UX.
    
    Features:
    - Frameless dark theme matching app style
    - Animated reveal
    - Item comparison with equipped gear
    - Quick equip button
    - Detailed stats and bonuses
    - Celebration based on rarity
    """
    
    quick_equip_requested = QtCore.Signal()
    view_inventory = QtCore.Signal()
    
    def __init__(self, item: dict, equipped_item: Optional[dict] = None,
                 session_minutes: int = 0, streak_days: int = 0, coins_earned: int = 0,
                 parent: Optional[QtWidgets.QWidget] = None):
        # Handle None item gracefully
        self.item = item if item is not None else {}
        self.equipped_item = equipped_item
        self.session_minutes = session_minutes
        self.streak_days = streak_days
        self.coins_earned = coins_earned
        
        # Validate and set defaults
        self.item.setdefault("name", "Unknown Item")
        self.item.setdefault("rarity", "Common")
        self.item.setdefault("slot", "Unknown")
        self.item.setdefault("power", 10)
        
        # Determine header based on rarity
        rarity = self.item.get("rarity", "Common")
        if self.item.get("lucky_upgrade"):
            header_text = "LUCKY UPGRADE!"
            header_icon = "🍀"
        elif rarity == "Legendary":
            header_text = "LEGENDARY DROP!"
            header_icon = "⭐"
        elif rarity == "Epic":
            header_text = "EPIC DROP!"
            header_icon = "💎"
        elif rarity == "Rare":
            header_text = "RARE FIND!"
            header_icon = "💠"
        else:
            header_text = "ITEM ACQUIRED!"
            header_icon = "✨"
        
        super().__init__(
            parent=parent,
            title=header_text,
            header_icon=header_icon,
            min_width=450,
            max_width=550,
            modal=True,
        )
        
        QtCore.QTimer.singleShot(100, self._start_celebration)
    
    def _build_content(self, layout: QtWidgets.QVBoxLayout):
        """Build the complete dialog content."""
        rarity = self.item.get("rarity", "Common")
        rarity_info = ITEM_RARITIES.get(rarity, {})
        color = rarity_info.get("color", "#9e9e9e")
        
        # Item visual
        item_visual = self._create_item_visual()
        layout.addWidget(item_visual)
        
        # Item name and details
        name_label = QtWidgets.QLabel(self.item.get("name", "Unknown Item"))
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {color};
            background: transparent;
        """)
        layout.addWidget(name_label)
        
        # Stats line
        power = self.item.get("power", 10)
        slot = self.item.get("slot", "Unknown")
        stats_label = QtWidgets.QLabel(f"[{rarity} {slot}] ⚔ +{power} Power")
        stats_label.setAlignment(QtCore.Qt.AlignCenter)
        stats_label.setStyleSheet(f"color: {color}; font-size: 13px; background: transparent;")
        layout.addWidget(stats_label)
        
        # Lucky options
        lucky_options = self.item.get("lucky_options", {})
        if lucky_options and format_lucky_options:
            try:
                lucky_text = format_lucky_options(lucky_options)
                if lucky_text:
                    lucky_label = QtWidgets.QLabel(f"✨ {lucky_text}")
                    lucky_label.setAlignment(QtCore.Qt.AlignCenter)
                    lucky_label.setStyleSheet("color: #8b5cf6; font-weight: bold; font-size: 12px; background: transparent;")
                    layout.addWidget(lucky_label)
            except Exception:
                pass
        
        # Separator
        self._add_separator(layout)
        
        # Comparison with equipped
        comparison = ItemComparisonWidget(self.item, self.equipped_item)
        layout.addWidget(comparison)
        
        # Coins earned
        if self.coins_earned > 0:
            coins_label = QtWidgets.QLabel(f"💰 +{self.coins_earned} Coins earned!")
            coins_label.setAlignment(QtCore.Qt.AlignCenter)
            coins_label.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 12px; background: transparent;")
            layout.addWidget(coins_label)
        
        # Motivational message
        messages = {
            "Common": ["Every item counts! 💪", "Building your arsenal!", "Nice find!"],
            "Uncommon": ["Nice find! 🌟", "Your focus is paying off!", "Quality gear!"],
            "Rare": ["Rare drop! You're on fire! 🔥", "Sweet loot! ⚡", "Excellent!"],
            "Epic": ["EPIC! Your dedication shows! 💜", "Champion tier! 👑", "Incredible!"],
            "Legendary": ["LEGENDARY! Unstoppable! ⭐", "GODLIKE FOCUS! 🏆", "You are a legend!"]
        }
        import random
        default_messages = ["Nice find!"]
        msg = random.choice(messages.get(rarity, default_messages))
        msg_label = QtWidgets.QLabel(msg)
        msg_label.setAlignment(QtCore.Qt.AlignCenter)
        msg_label.setStyleSheet("font-weight: bold; color: #888888; font-size: 13px; background: transparent;")
        layout.addWidget(msg_label)
        
        # Spacer
        layout.addStretch()
        
        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Quick equip (if slot is empty)
        if not self.equipped_item:
            equip_btn = QtWidgets.QPushButton("⚡ Quick Equip")
            equip_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4CAF50, stop:1 #388E3C);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #5CBF60, stop:1 #43A047);
                }
            """)
            equip_btn.clicked.connect(self._on_quick_equip)
            button_layout.addWidget(equip_btn)
        
        # View inventory
        inventory_btn = QtWidgets.QPushButton("📦 Inventory")
        inventory_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42A5F5, stop:1 #2196F3);
            }
        """)
        inventory_btn.clicked.connect(self._on_view_inventory)
        button_layout.addWidget(inventory_btn)
        
        # Close
        close_btn = QtWidgets.QPushButton("✓ Continue")
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4A4A6A, stop:1 #2A2A4A);
                color: #FFD700;
                border: 1px solid #FFD700;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5A5A7A, stop:1 #3A3A5A);
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _add_separator(self, layout: QtWidgets.QVBoxLayout):
        """Add a styled separator line."""
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #333344; max-height: 1px;")
        layout.addWidget(line)
    
    def _create_item_visual(self) -> QtWidgets.QWidget:
        """Create visual representation of the item."""
        visual = QtWidgets.QLabel()
        visual.setAlignment(QtCore.Qt.AlignCenter)
        
        # Use pixmap if available, otherwise show large emoji
        rarity = self.item.get("rarity", "Common")
        rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        try:
            stars = rarity_order.index(rarity) + 1
        except ValueError:
            stars = 1  # Default to 1 star for unknown rarity
        star_text = "★" * stars
        
        text = f"🎁\n{star_text}"
        visual.setText(text)
        visual.setStyleSheet("""
            font-size: 48px;
            padding: 20px;
            background: transparent;
        """)
        
        return visual
    
    def _start_celebration(self):
        """Start celebration animation."""
        rarity = self.item.get("rarity", "Common")
        
        # Play sound for Epic and Legendary
        if rarity in ["Epic", "Legendary"]:
            try:
                import winsound
                beeps = 3 if rarity == "Legendary" else 2
                for _ in range(beeps):
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
    
    def _on_quick_equip(self):
        """Handle quick equip action."""
        self.quick_equip_requested.emit()
        self.accept()
    
    def _on_view_inventory(self):
        """Handle view inventory action."""
        self.view_inventory.emit()
        # Don't close dialog - let user manage inventory
    
    def closeEvent(self, event):
        """Clean up animations."""
        super().closeEvent(event)
