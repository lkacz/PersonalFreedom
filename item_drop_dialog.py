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
    
    # Signal emitted when user requests to equip the new item
    equip_requested = QtCore.Signal()
    
    RARITY_COLORS = {
        "Common": "#9e9e9e",
        "Uncommon": "#4caf50", 
        "Rare": "#2196f3",
        "Epic": "#9c27b0",
        "Legendary": "#ff9800"
    }
    
    def __init__(self, new_item: dict, equipped_item: Optional[dict] = None,
                 parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.new_item = new_item
        self.equipped_item = equipped_item
        self._build_ui()
    
    def _build_ui(self):
        """Build comparison display with comprehensive benefit analysis."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Calculate power difference and determine if upgrade
        new_power = self.new_item.get("power", 0)
        eq_power = self.equipped_item.get("power", 0) if self.equipped_item else 0
        power_diff = new_power - eq_power
        
        # Calculate lucky bonuses
        new_lucky = self.new_item.get("lucky_options", {})
        eq_lucky = self.equipped_item.get("lucky_options", {}) if self.equipped_item else {}
        
        new_lucky_score = sum([
            new_lucky.get("coin_discount", 0),
            new_lucky.get("xp_bonus", 0),
            new_lucky.get("merge_luck", 0)
        ])
        eq_lucky_score = sum([
            eq_lucky.get("coin_discount", 0),
            eq_lucky.get("xp_bonus", 0),
            eq_lucky.get("merge_luck", 0)
        ])
        
        is_upgrade = power_diff > 0 or (power_diff == 0 and new_lucky_score > eq_lucky_score)
        is_empty_slot = not self.equipped_item
        
        # Upgrade/Status header
        if is_empty_slot:
            header = QtWidgets.QLabel("✨ <b>NEW GEAR FOR EMPTY SLOT!</b>")
            header.setStyleSheet("color: #4caf50; font-size: 12px;")
        elif is_upgrade:
            header = QtWidgets.QLabel("⬆️ <b>UPGRADE AVAILABLE!</b>")
            header.setStyleSheet("color: #FFD700; font-size: 12px;")
        elif power_diff < 0:
            header = QtWidgets.QLabel("📊 <b>Comparison</b> (Equipped is stronger)")
            header.setStyleSheet("color: #888; font-size: 11px;")
        else:
            header = QtWidgets.QLabel("📊 <b>Comparison</b> (Similar power)")
            header.setStyleSheet("color: #888; font-size: 11px;")
        header.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Side-by-side cards
        cards_layout = QtWidgets.QHBoxLayout()
        cards_layout.setSpacing(16)
        
        # New item (left)
        new_widget = self._create_item_card(self.new_item, "New Item", is_new=True)
        cards_layout.addWidget(new_widget)
        
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
        cards_layout.addWidget(vs_label)
        
        # Current item (right) or "Empty" placeholder
        if self.equipped_item:
            current_widget = self._create_item_card(self.equipped_item, "Equipped", is_new=False)
        else:
            current_widget = self._create_empty_card()
        cards_layout.addWidget(current_widget)
        
        main_layout.addLayout(cards_layout)
        
        # Power difference display (only if there's an equipped item)
        if self.equipped_item:
            diff_color = "#4caf50" if power_diff > 0 else ("#f44336" if power_diff < 0 else "#888")
            diff_sign = "+" if power_diff > 0 else ""
            diff_label = QtWidgets.QLabel(
                f"<span style='color:{diff_color}; font-weight:bold; font-size:14px;'>"
                f"⚔ {diff_sign}{power_diff} Power</span>"
            )
            diff_label.setAlignment(QtCore.Qt.AlignCenter)
            diff_label.setStyleSheet("background: transparent; padding: 4px;")
            main_layout.addWidget(diff_label)
            
            # Lucky options comparison
            lucky_diffs = []
            for key, label, emoji in [
                ("coin_discount", "Merge Cost", "💰"),
                ("xp_bonus", "XP Bonus", "✨"),
                ("merge_luck", "Merge Luck", "🎲")
            ]:
                new_val = new_lucky.get(key, 0)
                old_val = eq_lucky.get(key, 0)
                if new_val != old_val:
                    diff = new_val - old_val
                    d_sign = "+" if diff > 0 else ""
                    d_color = "#4caf50" if diff > 0 else "#f44336"
                    lucky_diffs.append(f"<span style='color:{d_color};'>{emoji} {label}: {d_sign}{diff}%</span>")
            
            if lucky_diffs:
                lucky_label = QtWidgets.QLabel(" | ".join(lucky_diffs))
                lucky_label.setAlignment(QtCore.Qt.AlignCenter)
                lucky_label.setStyleSheet("font-size: 10px; background: transparent;")
                main_layout.addWidget(lucky_label)
    
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
                 parent: Optional[QtWidgets.QWidget] = None, story_id: Optional[str] = None,
                 entity_perk_contributors: Optional[list] = None):
        # Handle None item gracefully
        self.item = item if item is not None else {}
        self.equipped_item = equipped_item
        self.session_minutes = session_minutes
        self.streak_days = streak_days
        self.coins_earned = coins_earned
        self._story_id = story_id  # Store for themed slot names
        self._entity_perk_contributors = entity_perk_contributors or []  # Entity perks that helped
        
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
        
        # Stats line - use themed slot name
        power = self.item.get("power", 10)
        slot = self.item.get("slot", "Unknown")
        display_slot = get_slot_display_name(slot, self._story_id) if slot != "Unknown" else slot
        stats_label = QtWidgets.QLabel(f"[{rarity} {display_slot}] ⚔ +{power} Power")
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
        
        # Entity perk bonus section - show when entities helped boost rarity
        if self._entity_perk_contributors:
            self._add_entity_perk_section(layout)
        
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
        
        # Determine if item is an upgrade
        new_power = self.item.get("power", 0)
        eq_power = self.equipped_item.get("power", 0) if self.equipped_item else 0
        power_diff = new_power - eq_power
        
        new_lucky = self.item.get("lucky_options", {})
        eq_lucky = self.equipped_item.get("lucky_options", {}) if self.equipped_item else {}
        new_lucky_score = sum([new_lucky.get(k, 0) for k in ("coin_discount", "xp_bonus", "merge_luck")])
        eq_lucky_score = sum([eq_lucky.get(k, 0) for k in ("coin_discount", "xp_bonus", "merge_luck")])
        
        is_upgrade = power_diff > 0 or (power_diff == 0 and new_lucky_score > eq_lucky_score)
        is_empty_slot = not self.equipped_item
        
        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Quick equip (if slot is empty OR if new item is an upgrade)
        if is_empty_slot or is_upgrade:
            equip_text = "⚡ Quick Equip" if is_empty_slot else "⚔️ Equip Upgrade"
            equip_btn = QtWidgets.QPushButton(equip_text)
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
    
    def _add_entity_perk_section(self, layout: QtWidgets.QVBoxLayout):
        """Add section showing entity perks that helped with this drop."""
        try:
            if not self._entity_perk_contributors:
                return
            
            # Calculate total bonus
            total_rarity = sum(c.get("value", 0) for c in self._entity_perk_contributors 
                              if c.get("perk_type") == "rarity_bias")
            total_drop = sum(c.get("value", 0) for c in self._entity_perk_contributors 
                            if c.get("perk_type") == "drop_luck")
            
            if total_rarity <= 0 and total_drop <= 0:
                return
            
            # Create section container
            section = QtWidgets.QFrame()
            section.setStyleSheet("""
                QFrame {
                    background-color: rgba(59, 130, 246, 0.1);
                    border: 1px solid #3b82f6;
                    border-radius: 6px;
                    padding: 4px;
                    margin: 4px 0;
                }
            """)
            section_layout = QtWidgets.QVBoxLayout(section)
            section_layout.setContentsMargins(8, 6, 8, 6)
            section_layout.setSpacing(4)
            
            # Check if there are city bonuses
            has_city = any(c.get("is_city", False) for c in self._entity_perk_contributors)
            
            # Header
            bonus_parts = []
            if total_rarity > 0:
                bonus_parts.append(f"+{total_rarity}% rare finds")
            if total_drop > 0:
                bonus_parts.append(f"+{total_drop}% drop luck")
            
            if has_city:
                header_text = "🐾 Patrons & City: " + ", ".join(bonus_parts)
            else:
                header_text = "🐾 Entity Patrons: " + ", ".join(bonus_parts)
            
            header = QtWidgets.QLabel(header_text)
            header.setStyleSheet("color: #7986cb; font-weight: bold; font-size: 10px; background: transparent;")
            header.setAlignment(QtCore.Qt.AlignCenter)
            section_layout.addWidget(header)
            
            # Entity mini-cards in horizontal layout
            cards_container = QtWidgets.QWidget()
            cards_container.setStyleSheet("background: transparent;")
            cards_layout = QtWidgets.QHBoxLayout(cards_container)
            cards_layout.setContentsMargins(0, 0, 0, 0)
            cards_layout.setSpacing(6)
            cards_layout.addStretch()
            
            for entity_data in self._entity_perk_contributors[:4]:  # Limit to 4 for space
                card = QtWidgets.QFrame()
                is_exceptional = entity_data.get("is_exceptional", False)
                card.setStyleSheet("""
                    QFrame {
                        background-color: #2a2a2a;
                        border: 1px solid #444;
                        border-radius: 4px;
                    }
                """)
                
                card_layout = QtWidgets.QHBoxLayout(card)
                card_layout.setContentsMargins(4, 2, 4, 2)
                card_layout.setSpacing(3)
                
                # Entity name and bonus
                name = entity_data.get("name", "Unknown")
                value = entity_data.get("value", 0)
                perk_type = entity_data.get("perk_type", "")
                is_city = entity_data.get("is_city", False)
                icon = "🎲" if perk_type == "rarity_bias" else "🍀"
                display_name = name[:10] + "..." if len(name) > 10 else name
                
                if is_city:
                    # City building - use different style
                    style = "color: #7fdbff; font-weight: bold; font-size: 9px; background: transparent;"
                    prefix = "🏛️ "
                elif is_exceptional:
                    style = "color: #ffd700; font-weight: bold; font-size: 9px; background: transparent;"
                    prefix = "⭐"
                else:
                    style = "color: #ccc; font-size: 9px; background: transparent;"
                    prefix = ""
                
                text_lbl = QtWidgets.QLabel(f"{prefix}{display_name} {icon}+{value}%")
                text_lbl.setStyleSheet(style)
                text_lbl.setToolTip(entity_data.get("description", f"{name}: +{value}%"))
                card_layout.addWidget(text_lbl)
                
                cards_layout.addWidget(card)
            
            if len(self._entity_perk_contributors) > 4:
                more_lbl = QtWidgets.QLabel(f"+{len(self._entity_perk_contributors) - 4} more")
                more_lbl.setStyleSheet("color: #888; font-size: 9px; background: transparent;")
                cards_layout.addWidget(more_lbl)
            
            cards_layout.addStretch()
            section_layout.addWidget(cards_container)
            
            layout.addWidget(section)
            
        except Exception as e:
            print(f"[ItemDropDialog] Error adding entity perk section: {e}")
    
    def _start_celebration(self):
        """Start celebration animation."""
        rarity = self.item.get("rarity", "Common")
        
        # Play win sound for Epic and Legendary using lottery sound system
        if rarity in ["Epic", "Legendary"]:
            try:
                from lottery_sounds import play_win_sound
                play_win_sound()
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
