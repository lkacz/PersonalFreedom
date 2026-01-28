"""
Lucky Merge Dialog - Industry-Standard UX
==========================================
Professional merge UI with visual feedback, animations, and comprehensive information display.
"""

import random
from datetime import datetime
from typing import Optional
from PySide6 import QtWidgets, QtCore, QtGui

# Import reusable lottery animation components
from lottery_animation import LotteryRollDialog, LotterySliderWidget, MergeTwoStageLotteryDialog

try:
    from gamification import (
        calculate_merge_success_rate, 
        get_merge_result_rarity,
        perform_lucky_merge,
        ITEM_RARITIES,
        RARITY_POWER,
        RARITY_ORDER,
        RARITY_UPGRADE,
        COIN_COSTS,
        MERGE_BOOST_BONUS,
        get_slot_display_name,
        get_selected_story
    )
    GAMIFICATION_AVAILABLE = True
except ImportError:
    GAMIFICATION_AVAILABLE = False
    COIN_COSTS = {"merge_base": 50, "merge_boost": 50, "merge_tier_upgrade": 50, "merge_retry_bump": 50, "merge_claim": 100, "merge_salvage": 50}
    MERGE_BOOST_BONUS = 0.25
    RARITY_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    RARITY_UPGRADE = {"Common": "Uncommon", "Uncommon": "Rare", "Rare": "Epic", "Epic": "Legendary", "Legendary": "Legendary"}
    ITEM_RARITIES = {
        "Common": {"color": "#9e9e9e", "power": 10},
        "Uncommon": {"color": "#4caf50", "power": 25},
        "Rare": {"color": "#2196f3", "power": 50},
        "Epic": {"color": "#9c27b0", "power": 100},
        "Legendary": {"color": "#ff9800", "power": 250}
    }
    RARITY_POWER = {"Common": 10, "Uncommon": 25, "Rare": 50, "Epic": 100, "Legendary": 250}
    get_slot_display_name = None
    get_selected_story = None

# Try to import SVG support for entity icons
try:
    from PySide6.QtSvg import QSvgRenderer
    HAS_SVG_SUPPORT = True
except ImportError:
    HAS_SVG_SUPPORT = False

# Backwards compatibility aliases for this module
MergeRollAnimationDialog = LotteryRollDialog
MergeSliderWidget = LotterySliderWidget


def create_entity_perk_mini_cards(contributors: list, perk_labels: dict = None) -> QtWidgets.QWidget:
    """
    Create a horizontal layout of mini-cards showing entity perk contributors.
    
    Args:
        contributors: List of dicts with entity_id, name, perk_type, value, icon, 
                     is_exceptional, description
        perk_labels: Optional dict mapping perk_type to display label 
                    (e.g., {"merge_luck": "🍀", "coin_discount": "💰"})
    
    Returns:
        QWidget containing the mini-cards
    """
    if not contributors:
        return None
    
    container = QtWidgets.QWidget()
    layout = QtWidgets.QHBoxLayout(container)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(6)
    
    # Try to import entity icon resolver
    try:
        from entitidex_tab import _resolve_entity_svg_path
        from entitidex.entity_pools import get_entity_by_id
        has_entity_support = True and HAS_SVG_SUPPORT
    except ImportError:
        has_entity_support = False
    
    for entity_data in contributors:
        card = QtWidgets.QFrame()
        is_exceptional = entity_data.get("is_exceptional", False)
        
        # Style cards
        if is_exceptional:
            card.setStyleSheet("""
                QFrame {
                    background-color: #2a2a2a;
                    border: 1px solid #555;
                    border-radius: 5px;
                    padding: 2px;
                }
                QFrame:hover {
                    border-color: #666;
                    background-color: #333;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame {
                    background-color: #2a2a2a;
                    border: 1px solid #444;
                    border-radius: 5px;
                    padding: 2px;
                }
                QFrame:hover {
                    border-color: #555;
                    background-color: #333;
                }
            """)
        
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(6, 4, 6, 4)
        card_layout.setSpacing(2)
        
        # Try to load entity SVG icon
        entity_id = entity_data.get("entity_id", "")
        icon_loaded = False
        
        if has_entity_support and entity_id:
            try:
                entity_obj = get_entity_by_id(entity_id)
                if entity_obj:
                    svg_path = _resolve_entity_svg_path(entity_obj, is_exceptional)
                    if svg_path:
                        renderer = QSvgRenderer(svg_path)
                        if renderer.isValid():
                            icon_size = 32
                            pixmap = QtGui.QPixmap(icon_size, icon_size)
                            pixmap.fill(QtCore.Qt.transparent)
                            painter = QtGui.QPainter(pixmap)
                            renderer.render(painter)
                            painter.end()
                            
                            icon_lbl = QtWidgets.QLabel()
                            icon_lbl.setPixmap(pixmap)
                            icon_lbl.setAlignment(QtCore.Qt.AlignCenter)
                            icon_lbl.setFixedSize(icon_size, icon_size)
                            card_layout.addWidget(icon_lbl, alignment=QtCore.Qt.AlignCenter)
                            icon_loaded = True
            except Exception:
                pass
        
        # Entity name
        name = entity_data.get("name", "Unknown")
        display_name = name[:12] + "..." if len(name) > 15 else name
        
        if is_exceptional:
            name_style = "color: #ffd700; font-weight: bold; font-size: 9px;"
            prefix = "⭐ " if not icon_loaded else ""
        else:
            name_style = "color: #bbb; font-size: 9px;"
            prefix = ""
        
        name_lbl = QtWidgets.QLabel(f"{prefix}{display_name}")
        name_lbl.setStyleSheet(name_style)
        name_lbl.setAlignment(QtCore.Qt.AlignCenter)
        name_lbl.setToolTip(f"{name}\n{entity_data.get('description', '')}")
        name_lbl.setWordWrap(True)
        card_layout.addWidget(name_lbl)
        
        # Perk value with optional perk label
        value = entity_data.get("value", 0)
        perk_type = entity_data.get("perk_type", "")
        perk_icon = perk_labels.get(perk_type, "") if perk_labels else ""
        
        # Choose color based on perk type
        if perk_type in ("merge_luck", "merge_success", "all_luck"):
            value_color = "#4caf50"  # Green for luck
            value_text = f"+{value}% {perk_icon}"
        elif perk_type == "coin_discount":
            value_color = "#ffb74d"  # Orange for coin
            value_text = f"-{value} {perk_icon}"
        elif perk_type == "cooldown":
            value_color = "#64b5f6"  # Blue for cooldown
            value_text = f"-{value}m {perk_icon}"
        elif perk_type == "cap":
            value_color = "#81c784"  # Light green for cap
            value_text = f"+{value} {perk_icon}"
        else:
            value_color = "#aaa"
            value_text = f"+{value}"
        
        value_lbl = QtWidgets.QLabel(value_text)
        value_lbl.setStyleSheet(f"color: {value_color}; font-size: 10px; font-weight: bold;")
        value_lbl.setAlignment(QtCore.Qt.AlignCenter)
        card_layout.addWidget(value_lbl)
        
        layout.addWidget(card)
    
    layout.addStretch()
    return container


class RarityDistributionWidget(QtWidgets.QWidget):
    """Visual widget showing the rarity distribution for merge lottery.
    
    Uses a moving window centered on the base rarity result, showing distribution
    across all tiers that are reachable from the merge.
    """
    
    # Moving window distribution: [5, 15, 60, 15, 5] centered on base result
    # Base gives 60% to the result tier, tapering to nearby tiers
    BASE_WINDOW = [5, 15, 60, 15, 5]
    # Upgraded shifts the window +1 tier higher
    UPGRADED_WINDOW = [5, 10, 25, 45, 15]
    
    def __init__(self, base_rarity: str = "Common", upgraded: bool = False, parent=None):
        super().__init__(parent)
        self.base_rarity = base_rarity
        self.upgraded = upgraded
        self.setMinimumHeight(70)
        self._calculate_distribution()
    
    def _calculate_distribution(self):
        """Calculate the rarity distribution using moving window centered on base rarity."""
        window = self.UPGRADED_WINDOW if self.upgraded else self.BASE_WINDOW
        
        # Get base rarity index (center of the window)
        try:
            base_idx = RARITY_ORDER.index(self.base_rarity)
        except ValueError:
            base_idx = 0
        
        # Apply moving window centered on base_idx
        # Window offsets: [-2, -1, 0, +1, +2] from center
        self.distribution = {}  # rarity -> percentage
        
        for offset, pct in zip([-2, -1, 0, 1, 2], window):
            target_idx = base_idx + offset
            # Clamp to valid tier range [0, 4]
            clamped_idx = max(0, min(len(RARITY_ORDER) - 1, target_idx))
            target_rarity = RARITY_ORDER[clamped_idx]
            
            if target_rarity in self.distribution:
                self.distribution[target_rarity] += pct
            else:
                self.distribution[target_rarity] = pct
    
    def set_upgraded(self, upgraded: bool):
        """Update the upgrade status and recalculate distribution."""
        if self.upgraded != upgraded:
            self.upgraded = upgraded
            self._calculate_distribution()
            self.update()
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        margin = 10
        bar_height = 30
        bar_y = 25
        
        # Title
        painter.setPen(QtGui.QColor("#aaa"))
        painter.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        title = "🎲 Rarity Lottery Distribution"
        if self.upgraded:
            title += " ⬆️"
        painter.drawText(margin, 16, title)
        
        # Draw distribution bars
        cumulative_x = margin
        bar_width = w - 2 * margin
        
        # Get ordered rarities (only those in distribution)
        ordered_rarities = [r for r in RARITY_ORDER if r in self.distribution]
        
        for i, rarity in enumerate(ordered_rarities):
            pct = self.distribution[rarity]
            if pct <= 0:
                continue
            
            zone_width = (pct / 100) * bar_width
            color = ITEM_RARITIES.get(rarity, {}).get("color", "#666")
            
            # Draw zone
            painter.setBrush(QtGui.QColor(color))
            painter.setPen(QtCore.Qt.NoPen)
            
            rect = QtCore.QRectF(cumulative_x, bar_y, zone_width, bar_height)
            if i == 0:
                path = QtGui.QPainterPath()
                path.addRoundedRect(rect, 4, 4)
                painter.drawPath(path)
            elif i == len(ordered_rarities) - 1:
                path = QtGui.QPainterPath()
                path.addRoundedRect(rect, 4, 4)
                painter.drawPath(path)
            else:
                painter.drawRect(rect)
            
            # Draw label with percentage
            if zone_width > 35:
                painter.setPen(QtGui.QColor("#fff"))
                painter.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
                label = f"{rarity[:3]}:{pct:.0f}%"
                label_rect = QtCore.QRectF(cumulative_x, bar_y, zone_width, bar_height)
                painter.drawText(label_rect, QtCore.Qt.AlignCenter, label)
            
            # Draw separator
            if i < len(ordered_rarities) - 1:
                painter.setPen(QtGui.QPen(QtGui.QColor("#1a1a2e"), 2))
                sep_x = cumulative_x + zone_width
                painter.drawLine(int(sep_x), bar_y, int(sep_x), bar_y + bar_height)
            
            cumulative_x += zone_width
        
        # Draw border
        painter.setPen(QtGui.QPen(QtGui.QColor("#444"), 1))
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawRoundedRect(margin, bar_y, bar_width, bar_height, 4, 4)


class ItemPreviewWidget(QtWidgets.QWidget):
    """Visual preview card for a single item in the merge."""
    
    def __init__(self, item: dict, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.item = item
        self.setFixedSize(140, 180)
        self._build_ui()
    
    def _build_ui(self):
        """Build the item preview card."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Rarity color
        rarity = self.item.get("rarity", "Common")
        rarity_info = ITEM_RARITIES.get(rarity, ITEM_RARITIES["Common"])
        color = rarity_info.get("color", "#9e9e9e")
        
        # Item icon/emoji
        emoji = self._get_item_emoji()
        icon_label = QtWidgets.QLabel(emoji)
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 48px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {color}, stop:1 {self._darken_color(color)});
            border-radius: 12px;
            padding: 15px;
            color: white;
        """)
        layout.addWidget(icon_label)
        
        # Item name
        name = self.item.get("name", "Unknown Item")
        name_label = QtWidgets.QLabel(name)
        name_label.setWordWrap(True)
        name_label.setAlignment(QtCore.Qt.AlignCenter)
        name_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 11px;
            color: {color};
        """)
        layout.addWidget(name_label)
        
        # Rarity stars
        stars = min(5, max(1, list(ITEM_RARITIES.keys()).index(rarity) + 1))
        stars_label = QtWidgets.QLabel("★" * stars)
        stars_label.setAlignment(QtCore.Qt.AlignCenter)
        stars_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        layout.addWidget(stars_label)
        
        # Power
        power = self.item.get("power", 0)
        power_label = QtWidgets.QLabel(f"⚔ {power}")
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(power_label)
        
        # Card border
        self.setStyleSheet(f"""
            ItemPreviewWidget {{
                background: white;
                border: 2px solid {color};
                border-radius: 8px;
            }}
        """)
    
    def _get_item_emoji(self) -> str:
        """Get emoji representation for the item."""
        slot = self.item.get("slot", "").lower()
        emoji_map = {
            "helmet": "⛑️",
            "chestplate": "🛡️",
            "gauntlets": "🧤",
            "boots": "👢",
            "shield": "🛡️",
            "weapon": "⚔️",
            "cloak": "🧥",
            "amulet": "📿"
        }
        return emoji_map.get(slot, "🎁")
    
    def _darken_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Darken a hex color."""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) < 6:
                return "#666666"
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r, g, b = int(r * factor), int(g * factor), int(b * factor)
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return "#666666"


class SuccessRateWidget(QtWidgets.QWidget):
    """Visual success rate display with progress bar and breakdown."""
    
    def __init__(self, rate: float, breakdown: dict, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.rate = rate
        self.breakdown = breakdown
        self.progress_bar = None
        self.breakdown_details = None  # Store reference for updates
        self._build_ui()
    
    def update_rate(self, new_rate: float, boost_active: bool = False):
        """Update the displayed success rate and breakdown."""
        self.rate = new_rate
        if self.progress_bar:
            self.progress_bar.setValue(int(self.rate * 100))
            
            # Format with boost indicator
            boost_text = " 🚀" if boost_active else ""
            self.progress_bar.setFormat(f"{self.rate * 100:.1f}%{boost_text}")
            
            # Update breakdown to show/hide boost
            if self.breakdown_details:
                breakdown_text = ""
                for component, value in self.breakdown.items():
                    breakdown_text += f"  • {component}: +{value}%\n"
                if boost_active:
                    breakdown_text += f"  • <b style='color:#64b5f6;'>🚀 Boost: +25%</b>\n"
                self.breakdown_details.setText(breakdown_text.strip())
            
            # Update color
            if self.rate >= 0.7:
                color = "#4caf50"  # Green
            elif self.rate >= 0.4:
                color = "#ff9800"  # Orange
            else:
                color = "#f44336"  # Red
            
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid #555;
                    border-radius: 8px;
                    text-align: center;
                    font-weight: bold;
                    font-size: 16px;
                    color: white;
                    background-color: #2a2a3a;
                    height: 32px;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {color}, stop:1 {self._lighten_color(color)});
                    border-radius: 6px;
                }}
            """)
    
    def _build_ui(self):
        """Build the success rate visualization."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Header
        header = QtWidgets.QLabel("🎲 Success Probability")
        header.setStyleSheet("font-weight: bold; font-size: 14px; color: #fff;")
        layout.addWidget(header)
        
        # Progress bar
        progress_container = QtWidgets.QWidget()
        progress_layout = QtWidgets.QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(self.rate * 100))
        self.progress_bar.setFormat(f"{self.rate * 100:.1f}%")
        self.progress_bar.setTextVisible(True)
        
        # Color based on rate
        if self.rate >= 0.7:
            color = "#4caf50"  # Green
        elif self.rate >= 0.4:
            color = "#ff9800"  # Orange
        else:
            color = "#f44336"  # Red
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #555;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 16px;
                color: white;
                background-color: #2a2a3a;
                height: 32px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:1 {self._lighten_color(color)});
                border-radius: 6px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        layout.addWidget(progress_container)
        
        # Breakdown
        breakdown_label = QtWidgets.QLabel("<b>Calculation Breakdown:</b>")
        breakdown_label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(breakdown_label)
        
        breakdown_text = ""
        for component, value in self.breakdown.items():
            breakdown_text += f"  • {component}: +{value}%\n"
        
        self.breakdown_details = QtWidgets.QLabel(breakdown_text.strip())
        self.breakdown_details.setStyleSheet("color: #888; font-size: 10px; padding-left: 10px;")
        self.breakdown_details.setTextFormat(QtCore.Qt.RichText)  # Enable rich text for boost styling
        layout.addWidget(self.breakdown_details)
    
    def _lighten_color(self, hex_color: str, factor: float = 1.2) -> str:
        """Lighten a hex color."""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) < 6:
                return "#aaaaaa"
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return "#aaaaaa"


class ResultPreviewWidget(QtWidgets.QWidget):
    """Preview of potential merge result."""
    
    def __init__(self, result_rarity: str, items: list = None, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.result_rarity = result_rarity
        self.items = items if items is not None else []
        self._build_ui()
    
    def _build_ui(self):
        """Build the result preview."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        rarity_info = ITEM_RARITIES.get(self.result_rarity, ITEM_RARITIES["Common"])
        color = rarity_info.get("color", "#9e9e9e")
        power = RARITY_POWER.get(self.result_rarity, 10)
        
        # Result icon
        icon = QtWidgets.QLabel("✨")
        icon.setAlignment(QtCore.Qt.AlignCenter)
        icon.setStyleSheet(f"""
            font-size: 56px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {color}, stop:1 {self._darken_color(color)});
            border-radius: 16px;
            padding: 20px;
        """)
        layout.addWidget(icon)
        
        # Result title
        title = QtWidgets.QLabel("Possible Result")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #aaa;")
        layout.addWidget(title)
        
        # Rarity - show range since tier jump is random
        # Calculate minimum (lowest item tier) and maximum (with max tier jump + upgrade)
        valid_items = [item for item in self.items if item and item.get("rarity")]
        if not valid_items:
            min_rarity_idx = 0  # Default to Common if no valid items
        else:
            min_rarity_idx = min([RARITY_ORDER.index(item.get("rarity", "Common")) for item in valid_items])
        max_tier_jump = 4  # Maximum possible tier jump
        max_rarity_idx = min(min_rarity_idx + max_tier_jump, len(RARITY_ORDER) - 1)
        
        if hasattr(self, 'tier_upgrade_enabled') and self.tier_upgrade_enabled:
            max_rarity_idx = min(max_rarity_idx + 1, len(RARITY_ORDER) - 1)
        
        min_rarity = RARITY_ORDER[min_rarity_idx]
        max_rarity = RARITY_ORDER[max_rarity_idx]
        
        if min_rarity == max_rarity:
            rarity_text = f"<b>{max_rarity}</b> Item"
        else:
            rarity_text = f"<b>{min_rarity}</b> to <b>{max_rarity}</b>"
        
        rarity_label = QtWidgets.QLabel(rarity_text)
        rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        rarity_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        layout.addWidget(rarity_label)
        
        # Add explanation about tier jumps
        if min_rarity != max_rarity:
            tier_note = QtWidgets.QLabel("✨ Lucky tier jumps possible!")
            tier_note.setAlignment(QtCore.Qt.AlignCenter)
            tier_note.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
            layout.addWidget(tier_note)
        elif getattr(self, "all_legendary", False):
            reroll_note = QtWidgets.QLabel("Legendary reroll: result stays Legendary, slot/type may change.")
            reroll_note.setAlignment(QtCore.Qt.AlignCenter)
            reroll_note.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
            layout.addWidget(reroll_note)
        
        # Stars
        stars = min(5, max(1, list(ITEM_RARITIES.keys()).index(self.result_rarity) + 1))
        stars_label = QtWidgets.QLabel("★" * stars)
        stars_label.setAlignment(QtCore.Qt.AlignCenter)
        stars_label.setStyleSheet(f"color: {color}; font-size: 16px;")
        layout.addWidget(stars_label)
        
        # Power range
        power_label = QtWidgets.QLabel(f"⚔ ~{power}")
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(power_label)
        
        self.setStyleSheet(f"""
            ResultPreviewWidget {{
                background: #2a2a3a;
                border: 2px dashed {color};
                border-radius: 12px;
            }}
        """)
    
    def _darken_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Darken a hex color."""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) < 6:
                return "#666666"
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r, g, b = int(r * factor), int(g * factor), int(b * factor)
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return "#666666"


class LuckyMergeDialog(QtWidgets.QDialog):
    """
    Industry-standard merge dialog with visual feedback and comprehensive UX.
    
    Features:
    - Visual item preview cards
    - Success rate progress bar with breakdown
    - Result preview
    - Risk/reward clarity
    - Animated execution feedback
    - Accessibility-compliant colors
    - Optional boost for +25% success rate
    """
    
    def __init__(self, items: list, luck: int, equipped: dict, 
                 parent: Optional[QtWidgets.QWidget] = None, player_coins: int = 0, 
                 coin_discount: int = 0, entity_perks: Optional[dict] = None,
                 adhd_buster: Optional[dict] = None):
        super().__init__(parent)
        self.items = items
        self.luck = luck
        self.equipped = equipped
        self.merge_result = None
        self.player_coins = player_coins
        self.boost_enabled = False
        self.tier_upgrade_enabled = False  # +50 coins to upgrade result tier
        self.coin_discount = coin_discount  # Discount percentage from merged items (0-90)
        self.adhd_buster = adhd_buster or {}  # For entity perk checks (Tesla Coil, Blank Parchment)
        self.entity_perks = entity_perks or {}  # Entity perk bonuses
        self.all_legendary = all(i.get("rarity") == "Legendary" for i in items if i)
        
        # Extract entity perk bonuses (supports both old and new format)
        # New format from get_entity_merge_perk_contributors:
        #   total_merge_luck, total_coin_discount, contributors
        # Old format from get_entity_perk_bonuses:
        #   coin_discount, merge_luck, merge_success, all_luck
        self.entity_coin_discount = self.entity_perks.get("total_coin_discount", 
                                    self.entity_perks.get("coin_discount", 0))
        
        # For merge luck, prefer total_merge_luck if available (new format)
        # Otherwise calculate from individual values (old format)
        if "total_merge_luck" in self.entity_perks:
            self.entity_merge_luck = 0
            self.entity_merge_success = 0
            self.entity_all_luck = 0
            self.total_entity_merge_luck = self.entity_perks.get("total_merge_luck", 0)
        else:
            self.entity_merge_luck = self.entity_perks.get("merge_luck", 0)
            self.entity_merge_success = self.entity_perks.get("merge_success", 0)
            self.entity_all_luck = self.entity_perks.get("all_luck", 0)
            self.total_entity_merge_luck = self.entity_merge_luck + self.entity_all_luck + self.entity_merge_success
        
        # Get detailed contributors for display
        self.entity_perk_contributors = self.entity_perks.get("contributors", [])
        
        # Import discount helpers from gamification
        from gamification import apply_coin_discount, apply_coin_flat_reduction
        from city import get_city_bonuses
        
        # Entity coin_discount is a FLAT coin reduction (e.g., -2 coins from Vending Machine perk)
        # Item coin_discount is a PERCENTAGE discount
        self.entity_coin_flat = self.entity_coin_discount  # Renamed for clarity - this is FLAT coins
        self.item_coin_discount_pct = coin_discount  # This is percentage
        
        # 🏙️ CITY BONUS: Market coin discount (percentage)
        self.city_coin_discount = 0
        try:
            city_bonuses = get_city_bonuses(self.adhd_buster)
            self.city_coin_discount = city_bonuses.get("coin_discount", 0)
        except Exception:
            pass
        
        # Combine item + city percentage discounts (cap at 90%)
        total_pct_discount = min(coin_discount + self.city_coin_discount, 90)
        
        # Store total coin discount for UI (percentage only, flat is separate)
        self.total_coin_discount = total_pct_discount  # Combined percentage part
        
        # Apply percentage discount first, then flat reduction
        # Step 1: Apply combined percentage discount (item + city)
        # Step 2: Apply entity flat coin reduction
        self.merge_cost = apply_coin_flat_reduction(apply_coin_discount(COIN_COSTS.get("merge_base", 50), total_pct_discount), self.entity_coin_flat)
        self.boost_cost = apply_coin_flat_reduction(apply_coin_discount(COIN_COSTS.get("merge_boost", 50), total_pct_discount), self.entity_coin_flat)
        self.tier_upgrade_cost = apply_coin_flat_reduction(apply_coin_discount(COIN_COSTS.get("merge_tier_upgrade", 50), total_pct_discount), self.entity_coin_flat)
        self.retry_bump_cost = apply_coin_flat_reduction(apply_coin_discount(COIN_COSTS.get("merge_retry_bump", 50), total_pct_discount), self.entity_coin_flat)
        self.claim_cost = apply_coin_flat_reduction(apply_coin_discount(COIN_COSTS.get("merge_claim", 100), total_pct_discount), self.entity_coin_flat)  # Claim item on near-miss
        self.boost_bonus = MERGE_BOOST_BONUS  # +25% success rate
        
        self.retry_cost_accumulated = 0
        self.near_miss_claimed = False
        self.salvage_requested = False
        
        # Calculate merge luck from ITEMS BEING MERGED (not equipped gear)
        # This encourages players to sacrifice items with merge_luck for better odds
        self.items_merge_luck = 0
        for item in items:
            if item and isinstance(item, dict):
                lucky_opts = item.get("lucky_options", {})
                if isinstance(lucky_opts, dict):
                    self.items_merge_luck += lucky_opts.get("merge_luck", 0)
        
        # Combine items merge luck with entity perk merge luck
        self.total_merge_luck = self.items_merge_luck + self.total_entity_merge_luck
        
        # Get city bonus for merge success (Forge building)
        self.city_merge_bonus = 0
        try:
            from gamification import get_all_perk_bonuses
            all_bonuses = get_all_perk_bonuses(self.adhd_buster)
            self.city_merge_bonus = all_bonuses.get("merge_success", 0)
        except Exception:
            pass
        
        if GAMIFICATION_AVAILABLE:
            # Pass combined merge luck (items + entity perks) + city bonus
            self.base_success_rate = calculate_merge_success_rate(
                items, items_merge_luck=self.total_merge_luck, city_bonus=self.city_merge_bonus
            )
            self.success_rate = self.base_success_rate
            self.result_rarity = get_merge_result_rarity(items)
        else:
            self.base_success_rate = 0.5
            self.success_rate = 0.5
            self.result_rarity = "Rare"
        
        # Calculate upgraded result rarity (for tier upgrade option)
        try:
            result_idx = RARITY_ORDER.index(self.result_rarity)
            self.upgraded_rarity = RARITY_ORDER[min(result_idx + 1, len(RARITY_ORDER) - 1)]
        except (ValueError, IndexError):
            self.upgraded_rarity = self.result_rarity
        
        # Determine which items affect tier (non-Common only)
        self.tier_affecting_items = [i for i in items if i and i.get("rarity", "Common") != "Common"]
        self.fuel_items = [i for i in items if i and i.get("rarity", "Common") == "Common"]
        
        # Calculate breakdown (matches gamification.py constants)
        base_rate = 0.25  # MERGE_BASE_SUCCESS_RATE from gamification.py
        item_bonus = max(0, len(items) - 2) * 0.03  # +3% per item after first two
        items_merge_bonus = self.items_merge_luck / 100.0
        
        self.breakdown = {
            "Base Rate": int(base_rate * 100),
            f"Item Count ({len(items)} items)": int(item_bonus * 100),
        }
        if self.items_merge_luck > 0:
            self.breakdown["Items Merge Luck"] = self.items_merge_luck
        # Add entity perk luck to breakdown (with sparkle icon for visibility)
        if self.total_entity_merge_luck > 0:
            self.breakdown["✨ Entity Perks"] = self.total_entity_merge_luck
        # Add city bonus from Forge building (with building icon)
        if self.city_merge_bonus > 0:
            self.breakdown["🔥 Forge (City)"] = self.city_merge_bonus
        
        self.setWindowTitle("⚡ Lucky Merge")
        
        # Frameless window with translucent background
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Dialog)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self._drag_pos = None
        
        # Size constraints
        self.setMinimumSize(680, 500)
        self.setMaximumHeight(900)
        
        # Load saved geometry
        from lottery_animation import load_dialog_geometry
        load_dialog_geometry(self, "LuckyMergeDialog", QtCore.QSize(680, 650))
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the complete merge dialog UI with styled frameless design."""
        # Outer layout (no margins for transparent background)
        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        
        # Main frame with gold border and dark background
        main_frame = QtWidgets.QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet("""
            QFrame#mainFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1A1A2E, stop:1 #0D0D1A);
                border: 2px solid #FFD700;
                border-radius: 16px;
            }
        """)
        outer_layout.addWidget(main_frame)
        
        frame_layout = QtWidgets.QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        
        # Header bar (draggable)
        self._header_frame = QtWidgets.QFrame()
        self._header_frame.setObjectName("headerFrame")
        self._header_frame.setCursor(QtCore.Qt.OpenHandCursor)
        self._header_frame.setStyleSheet("""
            QFrame#headerFrame {
                background: transparent;
                border: none;
                border-bottom: 1px solid #333344;
            }
        """)
        header_layout = QtWidgets.QHBoxLayout(self._header_frame)
        header_layout.setContentsMargins(20, 12, 10, 8)
        
        # Title with coins display
        header_left = QtWidgets.QWidget()
        header_left_layout = QtWidgets.QHBoxLayout(header_left)
        header_left_layout.setContentsMargins(0, 0, 0, 0)
        header_left_layout.setSpacing(15)
        
        title_label = QtWidgets.QLabel("⚡ Lucky Merge ⚡")
        title_label.setStyleSheet("""
            color: #FFD700;
            font-size: 18px;
            font-weight: bold;
        """)
        header_left_layout.addWidget(title_label)
        
        # Coin balance in header
        coin_widget = QtWidgets.QWidget()
        coin_layout = QtWidgets.QHBoxLayout(coin_widget)
        coin_layout.setContentsMargins(8, 2, 8, 2)
        coin_layout.setSpacing(4)
        coin_icon = QtWidgets.QLabel("🪙")
        coin_icon.setStyleSheet("font-size: 16px;")
        coin_layout.addWidget(coin_icon)
        self.coin_balance_label = QtWidgets.QLabel(f"{self.player_coins:,}")
        self.coin_balance_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #ffd700;
        """)
        coin_layout.addWidget(self.coin_balance_label)
        coin_widget.setStyleSheet("""
            background-color: rgba(255, 215, 0, 0.1);
            border-radius: 10px;
        """)
        header_left_layout.addWidget(coin_widget)
        
        header_layout.addWidget(header_left)
        header_layout.addStretch()
        
        # Close button
        close_btn = QtWidgets.QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setCursor(QtCore.Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton#closeButton {
                background: transparent;
                border: none;
                color: #888888;
                font-size: 18px;
                font-weight: bold;
                padding: 5px 10px;
                min-width: 30px;
            }
            QPushButton#closeButton:hover {
                color: #FF6B6B;
                background: rgba(255, 100, 100, 0.1);
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        
        frame_layout.addWidget(self._header_frame)
        
        # Scroll area for content
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #1A1A2E;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #4A4A6A;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5A5A7A;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Content widget inside scroll area
        content_widget = QtWidgets.QWidget()
        content_widget.setStyleSheet("background: transparent;")
        main_layout = QtWidgets.QVBoxLayout(content_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 15, 20, 15)
        
        # Subtitle with cost info
        original_cost = COIN_COSTS.get("merge_base", 50)
        if self.total_coin_discount > 0:
            # Build discount breakdown text
            discount_parts = []
            if self.item_coin_discount_pct > 0:
                discount_parts.append(f"Items: {self.item_coin_discount_pct}%")
            if self.city_coin_discount > 0:
                discount_parts.append(f"🏪 Market: {self.city_coin_discount}%")
            if self.entity_coin_discount > 0:
                discount_parts.append(f"✨ Entities: -{self.entity_coin_discount}🪙")
            discount_breakdown = " + ".join(discount_parts)
            
            cost_text = (f"Combining {len(self.items)} items • Cost: "
                        f"<span style='text-decoration: line-through; color: #666;'>{original_cost}</span> "
                        f"{self.merge_cost} coins 🪙 <span style='color: #8b5cf6;'>"
                        f"({discount_breakdown} = -{original_cost - self.merge_cost} saved!)</span>")
        else:
            cost_text = f"Combining {len(self.items)} items • Cost: {self.merge_cost} coins 🪙"
        subtitle = QtWidgets.QLabel(cost_text)
        subtitle.setStyleSheet("color: #aaa; font-size: 12px;")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(subtitle)
        
        # Separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #555;")
        main_layout.addWidget(line)
        
        # Items preview section (collapsible, collapsed by default)
        items_section = self._create_items_section()
        main_layout.addWidget(items_section)
        
        # Success rate widget (full width)
        self.success_widget = SuccessRateWidget(self.success_rate, self.breakdown)
        main_layout.addWidget(self.success_widget)
        
        # Entity Perk Contributors section (if any entities contribute to merge bonuses)
        if self.entity_perk_contributors:
            entity_section = self._create_entity_perks_section()
            if entity_section:
                main_layout.addWidget(entity_section)
        
        # Boost section (optional +25% for 50 coins)
        boost_section = self._create_boost_section()
        main_layout.addWidget(boost_section)
        
        # Rarity distribution widget (shows lottery probabilities)
        self.rarity_dist_widget = RarityDistributionWidget(
            base_rarity=self.result_rarity,
            upgraded=False
        )
        self.rarity_dist_widget.setStyleSheet("""
            QWidget {
                background-color: #252540;
                border: 2px solid #555;
                border-radius: 8px;
            }
        """)
        main_layout.addWidget(self.rarity_dist_widget)
        
        # Tier upgrade section (optional +1 tier for 50 coins)
        tier_upgrade_section = self._create_tier_upgrade_section()
        main_layout.addWidget(tier_upgrade_section)
        
        # Warning section
        # Warning box removed - the risk is evident from the UI context
        
        # Spacer
        main_layout.addStretch()
        
        # Buttons
        button_box = self._create_button_box()
        main_layout.addWidget(button_box)
        
        # Add content widget to scroll area
        scroll_area.setWidget(content_widget)
        frame_layout.addWidget(scroll_area, 1)  # Stretch to fill
        
        # Set dialog style for transparent background
        self.setStyleSheet("""
            QDialog {
                background: transparent;
            }
            QLabel {
                color: #E0E0E0;
                background: transparent;
            }
            QPushButton {
                padding: 10px 24px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        """)
    
    # ========================================================================
    # Dragging & Geometry Persistence
    # ========================================================================
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == QtCore.Qt.LeftButton:
            # Check if clicking on header
            if hasattr(self, '_header_frame'):
                header_rect = self._header_frame.geometry()
                if header_rect.contains(event.pos()):
                    self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                    self._header_frame.setCursor(QtCore.Qt.ClosedHandCursor)
                    event.accept()
                    return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging."""
        if self._drag_pos is not None and event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release after dragging."""
        if self._drag_pos is not None:
            self._drag_pos = None
            if hasattr(self, '_header_frame'):
                self._header_frame.setCursor(QtCore.Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)
    
    def closeEvent(self, event):
        """Save geometry on close."""
        from lottery_animation import save_dialog_geometry
        save_dialog_geometry(self, "LuckyMergeDialog")
        super().closeEvent(event)
    
    def reject(self):
        """Save geometry when dialog is rejected (closed or cancelled)."""
        from lottery_animation import save_dialog_geometry
        save_dialog_geometry(self, "LuckyMergeDialog")
        super().reject()
    
    def _create_items_section(self) -> QtWidgets.QWidget:
        """Create the items preview section as a collapsible list."""
        section = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Collapsible header button (collapsed by default)
        self._items_collapsed = True
        self._items_toggle_btn = QtWidgets.QPushButton(f"▶ 📦 Items to Merge ({len(self.items)})")
        self._items_toggle_btn.setCheckable(True)
        self._items_toggle_btn.setChecked(False)
        self._items_toggle_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._items_toggle_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.05);
                border: none;
                border-radius: 4px;
                padding: 8px 10px;
                text-align: left;
                font-weight: bold;
                font-size: 13px;
                color: #ccc;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
            QPushButton:checked {
                color: #fff;
            }
        """)
        layout.addWidget(self._items_toggle_btn)
        
        # Content container (hidden by default)
        self._items_content = QtWidgets.QWidget()
        items_layout = QtWidgets.QVBoxLayout(self._items_content)
        items_layout.setContentsMargins(10, 4, 0, 4)
        items_layout.setSpacing(2)
        
        # Get story ID for themed slot names
        story_id = get_selected_story(self.adhd_buster) if get_selected_story and self.adhd_buster else None
        
        # Items list (text-based for readability)
        for item in self.items:
            rarity = item.get("rarity", "Common")
            rarity_info = ITEM_RARITIES.get(rarity, ITEM_RARITIES.get("Common", {}))
            color = rarity_info.get("color", "#9e9e9e")
            name = item.get("name", "Unknown Item")
            power = item.get("power", 0)
            slot = item.get("slot", "Unknown")
            display_slot = get_slot_display_name(slot, story_id) if get_slot_display_name and slot != "Unknown" else slot
            
            item_label = QtWidgets.QLabel(
                f"• <span style='color:{color};'><b>{name}</b></span> "
                f"<span style='color:#888;'>({display_slot}, +{power} power) [{rarity}]</span>"
            )
            item_label.setTextFormat(QtCore.Qt.RichText)
            item_label.setStyleSheet("font-size: 12px; padding: 2px 0;")
            items_layout.addWidget(item_label)
        
        self._items_content.setVisible(False)  # Collapsed by default
        layout.addWidget(self._items_content)
        
        # Connect toggle
        self._items_toggle_btn.clicked.connect(self._toggle_items_section)
        
        return section
    
    def _toggle_items_section(self):
        """Toggle the items section visibility."""
        self._items_collapsed = not self._items_toggle_btn.isChecked()
        self._items_content.setVisible(not self._items_collapsed)
        arrow = "▼" if not self._items_collapsed else "▶"
        self._items_toggle_btn.setText(f"{arrow} 📦 Items to Merge ({len(self.items)})")
    
    def _create_warning_box(self) -> QtWidgets.QWidget:
        """Create the risk warning box."""
        warning = QtWidgets.QWidget()
        warning_layout = QtWidgets.QHBoxLayout(warning)
        warning_layout.setContentsMargins(16, 12, 16, 12)
        
        # Warning icon
        icon = QtWidgets.QLabel("⚠️")
        icon.setStyleSheet("font-size: 28px;")
        warning_layout.addWidget(icon)
        
        # Warning text
        if getattr(self, "all_legendary", False):
            warning_msg = (
                "<b>Legendary Reroll:</b> Failure destroys all Legendary items. "
                "Success creates a new Legendary (slot/type may change)."
            )
        else:
            warning_msg = (
                "<b>Warning:</b> Merge failure will destroy ALL selected items permanently. "
                "This action cannot be undone!"
            )

        text = QtWidgets.QLabel(warning_msg)
        text.setWordWrap(True)
        text.setStyleSheet("color: #ff6b6b; font-size: 12px;")
        warning_layout.addWidget(text, stretch=1)
        
        warning.setStyleSheet("""
            QWidget {
                background-color: #3a2020;
                border: 2px solid #f44336;
                border-radius: 8px;
            }
        """)
        
        return warning
    
    def _create_entity_perks_section(self) -> Optional[QtWidgets.QWidget]:
        """Create the entity perks mini-cards section showing which entities contribute."""
        if not self.entity_perk_contributors:
            return None
        
        # Split contributors into merge luck boosters and coin discount entities
        luck_contributors = [c for c in self.entity_perk_contributors 
                            if c.get("perk_type") in ("merge_luck", "merge_success", "all_luck")]
        coin_contributors = [c for c in self.entity_perk_contributors 
                            if c.get("perk_type") == "coin_discount"]
        
        if not luck_contributors and not coin_contributors:
            return None
        
        section = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(section)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Section for merge luck boosters
        if luck_contributors:
            luck_title = QtWidgets.QLabel("✨ Entity Patrons Boosting Merge")
            luck_title.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
            layout.addWidget(luck_title)
            
            # Create mini-cards for luck boosters
            luck_labels = {
                "merge_luck": "🍀",
                "merge_success": "🎯",
                "all_luck": "⭐",
            }
            luck_cards = create_entity_perk_mini_cards(luck_contributors, luck_labels)
            if luck_cards:
                layout.addWidget(luck_cards)
        
        # Section for coin discount entities
        if coin_contributors:
            coin_title = QtWidgets.QLabel("💰 Entity Patrons Reducing Cost")
            coin_title.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
            layout.addWidget(coin_title)
            
            # Create mini-cards for coin discount entities
            coin_labels = {
                "coin_discount": "💰",
            }
            coin_cards = create_entity_perk_mini_cards(coin_contributors, coin_labels)
            if coin_cards:
                layout.addWidget(coin_cards)
        
        # Style the section
        section.setStyleSheet("""
            QWidget {
                background-color: #1a1a2a;
                border: 1px solid #333;
                border-radius: 6px;
            }
        """)
        
        return section
    
    def _create_boost_section(self) -> QtWidgets.QWidget:
        """Create the boost option section."""
        boost_frame = QtWidgets.QWidget()
        boost_layout = QtWidgets.QHBoxLayout(boost_frame)
        boost_layout.setContentsMargins(16, 12, 16, 12)
        
        # Boost icon
        icon = QtWidgets.QLabel("🚀")
        icon.setStyleSheet("font-size: 24px;")
        boost_layout.addWidget(icon)
        
        # Boost checkbox
        self.boost_checkbox = QtWidgets.QCheckBox("Boost Success Rate (+25%)")
        self.boost_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: bold;
                color: #64b5f6;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        self.boost_checkbox.toggled.connect(self._on_boost_toggled)
        boost_layout.addWidget(self.boost_checkbox)
        
        # Cost label with discount info
        if self.coin_discount > 0:
            original_boost = COIN_COSTS.get("merge_boost", 50)
            savings = original_boost - self.boost_cost
            self.boost_cost_label = QtWidgets.QLabel(f"(+{self.boost_cost} 🪙) <span style='color: #8b5cf6;'>✨ Save {savings}</span>")
        else:
            self.boost_cost_label = QtWidgets.QLabel(f"(+{self.boost_cost} 🪙)")
        self.boost_cost_label.setStyleSheet("font-size: 13px; color: #aaa;")
        boost_layout.addWidget(self.boost_cost_label)
        
        boost_layout.addStretch()
        
        # Total cost display
        self.total_cost_label = QtWidgets.QLabel(f"Total: {self.merge_cost} 🪙")
        self.total_cost_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
        boost_layout.addWidget(self.total_cost_label)
        
        # Check if player can afford boost
        can_afford_boost = self.player_coins >= (self.merge_cost + self.boost_cost)
        if not can_afford_boost:
            self.boost_checkbox.setEnabled(False)
            self.boost_checkbox.setToolTip(f"Need {self.merge_cost + self.boost_cost} coins (you have {self.player_coins})")
            self.boost_cost_label.setStyleSheet("font-size: 13px; color: #666;")
        
        boost_frame.setStyleSheet("""
            QWidget {
                background-color: #1a3a5c;
                border: 2px solid #2196f3;
                border-radius: 8px;
            }
        """)
        
        return boost_frame
    
    def _on_boost_toggled(self, checked: bool):
        """Handle boost checkbox toggle."""
        self.boost_enabled = checked
        
        # Update success rate
        if checked:
            self.success_rate = min(self.base_success_rate + 0.25, 1.0)  # Cap at 100%
        else:
            self.success_rate = self.base_success_rate
        
        # Update total cost label
        self._update_total_cost()
        
        # Update success rate display via success widget
        if hasattr(self, 'success_widget') and self.success_widget:
            self.success_widget.update_rate(self.success_rate, boost_active=checked)
    
    def _update_total_cost(self):
        """Update the total cost label based on selected options with detailed breakdown."""
        total = self.merge_cost
        breakdown_parts = [f"Base: {self.merge_cost}"]
        
        if self.boost_enabled:
            total += self.boost_cost
            breakdown_parts.append(f"Boost (+25%): +{self.boost_cost}")
        if self.tier_upgrade_enabled:
            total += self.tier_upgrade_cost
            breakdown_parts.append(f"Tier Upgrade: +{self.tier_upgrade_cost}")
        
        # Build breakdown tooltip
        breakdown_text = "\n".join(breakdown_parts)
        remaining = self.player_coins - total
        tooltip = f"💰 Cost Breakdown:\n{breakdown_text}\n─────────────\nTotal: {total} 🪙\nAfter merge: {remaining} 🪙 remaining"
        
        self.total_cost_label.setText(f"Total: {total} 🪙")
        self.total_cost_label.setToolTip(tooltip)
        
        # Color code based on affordability
        if remaining < 0:
            self.total_cost_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f44336;")
        elif remaining < 50:
            self.total_cost_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff9800;")
        else:
            self.total_cost_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4caf50;")
    
    def _create_result_preview_with_info(self) -> QtWidgets.QWidget:
        """Create result preview with tier determination explanation."""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        rarity_info = ITEM_RARITIES.get(self.result_rarity, ITEM_RARITIES.get("Common", {}))
        color = rarity_info.get("color", "#9e9e9e")
        power = RARITY_POWER.get(self.result_rarity, 10) if GAMIFICATION_AVAILABLE else 10
        
        # Result title
        title = QtWidgets.QLabel("Possible Result")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #aaa;")
        layout.addWidget(title)
        
        # Calculate rarity range (minimum from lowest item, maximum with tier jumps)
        valid_items = [item for item in self.items if item and item.get("rarity")]
        if not valid_items:
            min_rarity_idx = 0  # Default to Common if no valid items
        else:
            min_rarity_idx = min([RARITY_ORDER.index(item.get("rarity", "Common")) for item in valid_items])
        max_tier_jump = 4  # Maximum possible tier jump
        max_rarity_idx = min(min_rarity_idx + max_tier_jump, len(RARITY_ORDER) - 1)
        
        if self.tier_upgrade_enabled:
            max_rarity_idx = min(max_rarity_idx + 1, len(RARITY_ORDER) - 1)
        
        min_rarity = RARITY_ORDER[min_rarity_idx]
        max_rarity = RARITY_ORDER[max_rarity_idx]
        
        # Rarity with emoji - show range
        if min_rarity == max_rarity:
            rarity_text = f"<b style='color:{color};'>✨ {max_rarity}</b>"
        else:
            min_color = ITEM_RARITIES.get(min_rarity, {}).get("color", "#9e9e9e")
            max_color = ITEM_RARITIES.get(max_rarity, {}).get("color", "#9e9e9e")
            rarity_text = f"<b style='color:{min_color};'>✨ {min_rarity}</b> to <b style='color:{max_color};'>{max_rarity}</b>"
        
        self.result_rarity_label = QtWidgets.QLabel(rarity_text)
        self.result_rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        self.result_rarity_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.result_rarity_label)
        
        # Add tier jump note if range exists
        if min_rarity != max_rarity:
            tier_note = QtWidgets.QLabel("✨ Lucky tier jumps possible!")
            tier_note.setAlignment(QtCore.Qt.AlignCenter)
            tier_note.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
            layout.addWidget(tier_note)
        
        # Power range
        power_label = QtWidgets.QLabel(f"⚔ ~{power} Power")
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(power_label)
        
        # Separator
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet("background-color: #444;")
        layout.addWidget(sep)
        
        # Tier determination explanation
        info_label = QtWidgets.QLabel()
        info_label.setWordWrap(True)
        info_label.setAlignment(QtCore.Qt.AlignCenter)
        
        if self.tier_affecting_items:
            lowest_rarity = min(
                (i.get("rarity", "Common") for i in self.tier_affecting_items),
                key=lambda r: RARITY_ORDER.index(r) if r in RARITY_ORDER else 0
            )
            info_text = f"<span style='color:#888; font-size:10px;'>"
            info_text += f"Tier based on lowest non-Common: <b style='color:{ITEM_RARITIES.get(lowest_rarity, {}).get('color', '#fff')};'>{lowest_rarity}</b><br>"
            info_text += f"→ Upgrades to {self.result_rarity}"
            if len(self.fuel_items) > 0:
                info_text += f"<br><span style='color:#4caf50;'>+{len(self.fuel_items)} Common items as fuel (no tier loss)</span>"
            info_text += "</span>"
        else:
            info_text = "<span style='color:#4caf50; font-size:10px;'>All Common items → Upgrades to Uncommon</span>"
        
        info_label.setText(info_text)
        layout.addWidget(info_label)
        
        container.setStyleSheet(f"""
            QWidget {{
                background: #2a2a3a;
                border: 2px dashed {color};
                border-radius: 12px;
            }}
        """)
        
        return container
    
    def _create_tier_upgrade_section(self) -> QtWidgets.QWidget:
        """Create the tier upgrade option section (+50 coins for +1 tier)."""
        frame = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Icon
        icon = QtWidgets.QLabel("⬆️")
        icon.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon)
        
        # Checkbox
        upgraded_color = ITEM_RARITIES.get(self.upgraded_rarity, {}).get("color", "#fff")
        self.tier_upgrade_checkbox = QtWidgets.QCheckBox(
            f"Upgrade Result (+1 Tier → {self.upgraded_rarity})"
        )
        self.tier_upgrade_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: 14px;
                font-weight: bold;
                color: {upgraded_color};
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
            }}
        """)
        self.tier_upgrade_checkbox.toggled.connect(self._on_tier_upgrade_toggled)
        layout.addWidget(self.tier_upgrade_checkbox)
        
        # Cost label with discount info
        if self.coin_discount > 0:
            original_tier = COIN_COSTS.get("merge_tier_upgrade", 50)
            savings = original_tier - self.tier_upgrade_cost
            cost_label = QtWidgets.QLabel(f"(+{self.tier_upgrade_cost} 🪙) <span style='color: #8b5cf6;'>✨ Save {savings}</span>")
        else:
            cost_label = QtWidgets.QLabel(f"(+{self.tier_upgrade_cost} 🪙)")
        cost_label.setStyleSheet("font-size: 13px; color: #aaa;")
        layout.addWidget(cost_label)
        
        layout.addStretch()
        
        # Can't upgrade if already Legendary
        if self.result_rarity == "Legendary":
            self.tier_upgrade_checkbox.setEnabled(False)
            self.tier_upgrade_checkbox.setText("Already Legendary!")
            self.tier_upgrade_checkbox.setStyleSheet("color: #666; font-size: 14px;")
        elif self.player_coins < (self.merge_cost + self.tier_upgrade_cost):
            self.tier_upgrade_checkbox.setEnabled(False)
            self.tier_upgrade_checkbox.setToolTip(f"Need {self.merge_cost + self.tier_upgrade_cost} coins")
        
        frame.setStyleSheet("""
            QWidget {
                background-color: #3a2a1a;
                border: 1px solid #555;
                border-radius: 8px;
            }
        """)
        
        return frame
    
    def _on_tier_upgrade_toggled(self, checked: bool):
        """Handle tier upgrade checkbox toggle."""
        self.tier_upgrade_enabled = checked
        self._update_total_cost()
        
        # Update the result preview label
        if hasattr(self, 'result_rarity_label'):
            if checked:
                color = ITEM_RARITIES.get(self.upgraded_rarity, {}).get("color", "#fff")
                self.result_rarity_label.setText(f"<b style='color:{color};'>✨ {self.upgraded_rarity} ⬆️</b>")
            else:
                color = ITEM_RARITIES.get(self.result_rarity, {}).get("color", "#fff")
                self.result_rarity_label.setText(f"<b style='color:{color};'>✨ {self.result_rarity}</b>")
        
        # Update the rarity distribution widget to show shifted probabilities
        if hasattr(self, 'rarity_dist_widget'):
            self.rarity_dist_widget.set_upgraded(checked)
        
        # Tier upgrade doesn't affect success rate - don't update the display
        # (The success rate display should only show boost_active based on self.boost_enabled)

    def _create_button_box(self) -> QtWidgets.QWidget:
        """Create the action button box."""
        button_box = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(button_box)
        layout.setSpacing(12)
        
        # Cancel button
        cancel_btn = QtWidgets.QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        # Spacer
        layout.addStretch()
        
        # Merge button
        merge_btn = QtWidgets.QPushButton("⚡ Merge Items")
        if self.success_rate >= 0.7:
            bg_color = "#4caf50"
            hover_color = "#388e3c"
        elif self.success_rate >= 0.4:
            bg_color = "#ff9800"
            hover_color = "#f57c00"
        else:
            bg_color = "#f44336"
            hover_color = "#d32f2f"
        
        merge_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                padding: 12px 32px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        merge_btn.clicked.connect(self.execute_merge)
        layout.addWidget(merge_btn)
        
        return button_box
    
    def execute_merge(self):
        """Execute the merge with dramatic two-stage roll animation."""
        if not GAMIFICATION_AVAILABLE:
            msg = QtWidgets.QMessageBox(self)
            msg.setWindowTitle("Feature Unavailable")
            msg.setText("Gamification features are not available.")
            msg.setIcon(QtWidgets.QMessageBox.NoIcon)
            msg.setOption(QtWidgets.QMessageBox.DontUseNativeDialog, True)
            msg.exec_()
            return
        
        # Disable all buttons during merge
        for button in self.findChildren(QtWidgets.QPushButton):
            button.setEnabled(False)
        
        # Calculate success rate first
        story_id = self.items[0].get("story_theme", "warrior") if self.items else "warrior"
        boost_bonus = 25 if self.boost_enabled else 0
        # Include: items merge luck + entity perk merge luck + boost bonus
        total_items_merge_luck = self.items_merge_luck + self.total_entity_merge_luck + boost_bonus
        
        # Calculate the success threshold (includes city bonus)
        success_rate = calculate_merge_success_rate(self.items, items_merge_luck=total_items_merge_luck, city_bonus=self.city_merge_bonus)
        
        # Roll for success
        success_roll = random.random()
        is_success = success_roll < success_rate
        
        # Determine base rarity for display
        base_rarity = self.result_rarity  # Calculated in __init__
        
        # Show dramatic two-stage animation (success + tier jump)
        # Pass tier_upgrade_enabled to show boosted distribution
        animation_dialog = MergeTwoStageLotteryDialog(
            success_roll, success_rate,
            tier_upgrade_enabled=self.tier_upgrade_enabled,
            base_rarity=base_rarity,
            parent=self
        )
        animation_dialog.exec_()
        
        # Get results from animation (rolled_tier is the actual rarity name)
        # Use the dialog's authoritative is_success result
        is_success, rolled_rarity = animation_dialog.get_results()
        
        # Now build the merge result using the rolled rarity
        if is_success:
            # Use the rolled rarity directly from animation
            final_rarity = rolled_rarity if rolled_rarity else self.result_rarity
            
            # Calculate tier_jump for backwards compatibility with result display
            def safe_rarity_idx(item):
                rarity = item.get("rarity", "Common")
                try:
                    return RARITY_ORDER.index(rarity)
                except ValueError:
                    return 0
            
            valid_items = [item for item in self.items if item is not None]
            rarity_indices = [safe_rarity_idx(item) for item in valid_items]
            lowest_idx = min(rarity_indices) if rarity_indices else 0
            final_idx = RARITY_ORDER.index(final_rarity) if final_rarity in RARITY_ORDER else lowest_idx
            tier_jump = max(1, final_idx - lowest_idx + 1)
            
            # Generate the result item
            from gamification import generate_item
            result_item = generate_item(rarity=final_rarity, story_id=story_id)
            
            self.merge_result = {
                "success": True,
                "items_lost": valid_items,
                "roll": success_roll,
                "needed": success_rate,
                "tier_jump": tier_jump,
                "result_item": result_item,
                "base_rarity": RARITY_ORDER[lowest_idx],
                "final_rarity": final_rarity
            }
            
            # Apply tier upgrade if enabled
            if self.tier_upgrade_enabled:
                current_rarity = result_item.get("rarity", "Common")
                try:
                    current_idx = RARITY_ORDER.index(current_rarity)
                    new_idx = min(current_idx + 1, len(RARITY_ORDER) - 1)
                    result_item["rarity"] = RARITY_ORDER[new_idx]
                    result_item["power"] = RARITY_POWER.get(result_item["rarity"], result_item.get("power", 10))
                    self.merge_result["tier_upgraded"] = True
                except (ValueError, IndexError):
                    pass
        else:
            self.merge_result = {
                "success": False,
                "items_lost": self.items,
                "roll": success_roll,
                "needed": success_rate,
                "tier_jump": 0,
                "result_item": None
            }
        
        # Show result after animation
        self._show_result()
    
    def _show_processing(self):
        """Show processing/merging animation overlay."""
        # Disable all buttons
        for button in self.findChildren(QtWidgets.QPushButton):
            button.setEnabled(False)
        
        # Create overlay
        overlay = QtWidgets.QWidget(self)
        overlay.setObjectName("processingOverlay")
        overlay.setGeometry(self.rect())
        overlay.setStyleSheet("""
            QWidget#processingOverlay {
                background-color: rgba(0, 0, 0, 0.7);
            }
        """)
        
        # Add label
        layout = QtWidgets.QVBoxLayout(overlay)
        label = QtWidgets.QLabel("⚡ Merging...\n✨")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: white;
        """)
        layout.addWidget(label)
        
        overlay.show()
    
    def _show_result(self):
        """Show merge result dialog."""
        # Hide processing overlay
        overlay = self.findChild(QtWidgets.QWidget, "processingOverlay")
        if overlay:
            overlay.hide()
        
        # Show result
        if self.merge_result["success"]:
            self._show_success_dialog()
            self.accept()
            return
        
        # Failure path
        self._show_failure_dialog()
        
        # If retry was requested, restart the merge sequence
        if getattr(self, "is_retrying", False):
            self.is_retrying = False  # Reset flag
            # Small delay to let dialog close and UI refresh
            QtCore.QTimer.singleShot(100, self.execute_merge)
            return  # Do NOT close the main dialog
        
        # If claim converted failure to success, don't double-accept
        if self.merge_result.get("success"):
            self.accept()
            return
        
        self.accept()
    
    def _show_success_dialog(self):
        """Show success result dialog with optional 'Push Your Luck' re-roll."""
        result_item = self.merge_result.get("result_item", {}) if self.merge_result else {}
        rarity = result_item.get("rarity", "Common")
        
        # Check if Push Your Luck is available (not Legendary)
        if rarity != "Legendary":
            choice = self._show_push_your_luck_dialog(result_item)
            if choice == "reroll":
                # Player wants to risk it for next tier
                self._execute_push_your_luck()
                return  # Don't close dialog yet
        
        # Show standard success message (either kept item or reached Legendary)
        self._show_final_success_message(result_item)
    
    def _show_push_your_luck_dialog(self, current_item: dict) -> str:
        """Show dialog offering to keep item or risk for next tier. Returns 'keep' or 'reroll'."""
        rarity = current_item.get("rarity", "Common")
        name = current_item.get("name", "Unknown Item")
        power = current_item.get("power", 0)
        slot = current_item.get("slot", "Unknown Slot")
        
        # Get themed slot display name
        story_id = get_selected_story(self.adhd_buster) if get_selected_story and self.adhd_buster else None
        display_slot = get_slot_display_name(slot, story_id) if get_slot_display_name and slot != "Unknown Slot" else slot
        
        # Calculate next tier and success chance
        rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        current_idx = rarity_order.index(rarity) if rarity in rarity_order else 0
        next_rarity = rarity_order[min(current_idx + 1, len(rarity_order) - 1)]
        
        # Get current success rate and apply penalty multiplier for push your luck
        # Base penalty is 0.80, but Tesla Coil can modify this
        push_luck_multiplier = getattr(self, 'push_luck_multiplier', 1.0)
        
        # Check for Tesla Coil (scientist_007) gamble perk BEFORE calculating chance
        # No Tesla Coil: 0.80 multiplier (penalty applied)
        # Normal Tesla Coil: 1.00 multiplier (penalty removed)
        # Exceptional Tesla Coil: 1.20 multiplier (bonus!)
        gamble_multiplier = 0.80  # Default: penalty without Tesla Coil
        tesla_coil_collected = False
        tesla_coil_is_exceptional = False
        
        # Check for Blank Parchment (scholar_009) item recovery perk
        blank_parchment_collected = False
        blank_parchment_is_exceptional = False
        blank_parchment_chance = 0
        
        try:
            entitidex_data = self.adhd_buster.get("entitidex", {})
            collected_ids = entitidex_data.get("collected_entity_ids", 
                            entitidex_data.get("collected", []))
            exceptional_entities = entitidex_data.get("exceptional_entities", {})
            
            # Tesla Coil check
            if "scientist_007" in collected_ids:
                tesla_coil_collected = True
                tesla_coil_is_exceptional = "scientist_007" in exceptional_entities
                
                if tesla_coil_is_exceptional:
                    gamble_multiplier = 1.20  # +20% chance (bonus!)
                else:
                    gamble_multiplier = 1.00  # No penalty (protection)
            
            # Blank Parchment check
            if "scholar_009" in collected_ids:
                blank_parchment_collected = True
                blank_parchment_is_exceptional = "scholar_009" in exceptional_entities
                blank_parchment_chance = 20 if blank_parchment_is_exceptional else 10
        except Exception as e:
            print(f"[Gamble Perk] Error checking perks: {e}")
        
        # Apply the gamble multiplier (which may be modified by Tesla Coil)
        new_multiplier = push_luck_multiplier * gamble_multiplier
        reroll_chance = self.success_rate * new_multiplier
        reroll_chance = max(0.01, min(0.99, reroll_chance))  # Clamp between 1% and 99%
        
        rarity_color = ITEM_RARITIES.get(rarity, {}).get("color", "#9e9e9e")
        next_color = ITEM_RARITIES.get(next_rarity, {}).get("color", "#fff")
        
        # Create custom dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("🎉 SUCCESS - Push Your Luck?")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # Success header
        header = QtWidgets.QLabel("🎉 <b>MERGE SUCCESS!</b> 🎉")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("font-size: 18px; color: #4caf50; padding: 10px;")
        layout.addWidget(header)
        
        # Current item display
        current_box = QtWidgets.QGroupBox("✅ You Won:")
        current_layout = QtWidgets.QVBoxLayout(current_box)
        current_lbl = QtWidgets.QLabel(
            f"<p style='text-align:center;'>"
            f"<span style='font-size:16px; font-weight:bold;'>{name}</span><br>"
            f"<span style='color:{rarity_color}; font-size:14px;'>{rarity}</span> • "
            f"<span style='color:#aaa;'>⚔ {power} Power</span><br>"
            f"<span style='color:#8bc34a;'>Slot: {display_slot}</span>"
            f"</p>"
        )
        current_lbl.setTextFormat(QtCore.Qt.RichText)
        current_layout.addWidget(current_lbl)
        current_box.setStyleSheet(f"QGroupBox {{ background: #2a3a2a; border: 2px solid {rarity_color}; border-radius: 8px; padding: 12px; }}")
        layout.addWidget(current_box)
        
        # Separator
        sep = QtWidgets.QLabel("⬇️ <b>OR RISK IT ALL FOR...</b> ⬇️")
        sep.setAlignment(QtCore.Qt.AlignCenter)
        sep.setStyleSheet("font-size: 13px; color: #ff9800; padding: 8px;")
        layout.addWidget(sep)
        
        # Next tier preview with perk info
        next_box = QtWidgets.QGroupBox("🎲 Gamble for Higher Tier:")
        next_layout = QtWidgets.QVBoxLayout(next_box)
        
        # Build chance text with perk indicator
        chance_text = f"Success Chance: <b>{reroll_chance*100:.1f}%</b>"
        if tesla_coil_collected:
            if tesla_coil_is_exceptional:
                chance_text += f" <span style='color:#4caf50;'>(×1.20 ⚡ Bonus!)</span>"
            else:
                chance_text += f" <span style='color:#8bc34a;'>(×1.00 ⚡ Protected)</span>"
        else:
            chance_text += f" <span style='color:#f44336;'>(×0.80 penalty)</span>"
        
        next_lbl = QtWidgets.QLabel(
            f"<p style='text-align:center;'>"
            f"<span style='color:{next_color}; font-size:16px; font-weight:bold;'>{next_rarity}</span><br>"
            f"<span style='color:#aaa; font-size:12px;'>{chance_text}</span><br>"
            f"<span style='color:#f44336; font-size:11px;'>⚠️ Lose everything if you fail!</span>"
            f"</p>"
        )
        next_lbl.setTextFormat(QtCore.Qt.RichText)
        next_layout.addWidget(next_lbl)
        next_box.setStyleSheet(f"QGroupBox {{ background: #3a2a1a; border: 2px dashed {next_color}; border-radius: 8px; padding: 12px; }}")
        layout.addWidget(next_box)
        
        # Tesla Coil perk card (if collected)
        if tesla_coil_collected:
            perk_card = self._create_tesla_coil_perk_card(tesla_coil_is_exceptional, gamble_multiplier)
            if perk_card:
                layout.addWidget(perk_card)
        
        # Blank Parchment safety net card (if collected)
        if blank_parchment_collected:
            safety_card = self._create_blank_parchment_perk_card(blank_parchment_is_exceptional, blank_parchment_chance)
            if safety_card:
                layout.addWidget(safety_card)
        
        # Warning - different text based on Tesla Coil status
        if tesla_coil_collected:
            if tesla_coil_is_exceptional:
                warning_text = "⚡ Tesla Coil boosts your luck by +20%!"
                warning_color = "#4caf50"
            else:
                warning_text = "⚡ Tesla Coil protects you from the re-roll penalty"
                warning_color = "#8bc34a"
        else:
            warning_text = "⚠️ Each re-roll reduces success chance by 20% (×0.80)"
            warning_color = "#d32f2f"
        
        warning = QtWidgets.QLabel(warning_text)
        warning.setAlignment(QtCore.Qt.AlignCenter)
        warning.setStyleSheet(f"font-size: 10px; color: {warning_color}; font-style: italic;")
        layout.addWidget(warning)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        keep_btn = QtWidgets.QPushButton("✅ Keep This Item")
        keep_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #388e3c; }
        """)
        keep_btn.clicked.connect(lambda: dialog.done(0))
        
        reroll_btn = QtWidgets.QPushButton(f"🎲 Risk for {next_rarity}!")
        reroll_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #f57c00; }
        """)
        reroll_btn.clicked.connect(lambda: dialog.done(1))
        
        btn_layout.addWidget(keep_btn)
        btn_layout.addWidget(reroll_btn)
        layout.addLayout(btn_layout)
        
        dialog.setStyleSheet("QDialog { background-color: #1e1e2e; }")
        
        result = dialog.exec_()
        return "reroll" if result == 1 else "keep"
    
    def _create_tesla_coil_perk_card(self, is_exceptional: bool, multiplier_value: float) -> Optional[QtWidgets.QWidget]:
        """Create a mini perk card showing Tesla Coil's gamble multiplier (same style as ADHD Buster patrons)."""
        try:
            from entitidex.entity_pools import get_entity_by_id
            entity = get_entity_by_id("scientist_007")
            if not entity:
                return None
            
            # Container with title
            container = QtWidgets.QFrame()
            container.setStyleSheet("""
                QFrame {
                    background-color: #252530;
                    border: 1px solid #3a3a4a;
                    border-radius: 8px;
                    padding: 4px;
                }
            """)
            container_layout = QtWidgets.QVBoxLayout(container)
            container_layout.setContentsMargins(8, 6, 8, 6)
            container_layout.setSpacing(6)
            
            # Title for the perk
            if is_exceptional:
                title_text = "⚡ Lightning Luck Active"
                title_color = "#ba68c8"
            else:
                title_text = "⚡ Static Shield Active"
                title_color = "#4caf50"
            
            title = QtWidgets.QLabel(title_text)
            title.setStyleSheet(f"color: {title_color}; font-size: 11px; font-weight: bold; background: transparent;")
            title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(title)
            
            # Entity card (same style as ADHD Buster patrons)
            card = QtWidgets.QFrame()
            if is_exceptional:
                card.setStyleSheet("""
                    QFrame {
                        background-color: #2a2a3a;
                        border: 2px solid #ba68c8;
                        border-radius: 6px;
                        padding: 4px;
                    }
                """)
            else:
                card.setStyleSheet("""
                    QFrame {
                        background-color: #2a3a2a;
                        border: 2px solid #4caf50;
                        border-radius: 6px;
                        padding: 4px;
                    }
                """)
            
            card_layout = QtWidgets.QVBoxLayout(card)
            card_layout.setContentsMargins(8, 6, 8, 6)
            card_layout.setSpacing(4)
            
            # Try to load entity SVG icon
            try:
                from entitidex_tab import _resolve_entity_svg_path
                from PySide6.QtSvg import QSvgRenderer
                
                svg_path = _resolve_entity_svg_path(entity, is_exceptional)
                if svg_path:
                    renderer = QSvgRenderer(svg_path)
                    if renderer.isValid():
                        icon_size = 48
                        pixmap = QtGui.QPixmap(icon_size, icon_size)
                        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
                        painter = QtGui.QPainter(pixmap)
                        renderer.render(painter)
                        painter.end()
                        
                        icon_lbl = QtWidgets.QLabel()
                        icon_lbl.setPixmap(pixmap)
                        icon_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                        icon_lbl.setFixedSize(icon_size, icon_size)
                        icon_lbl.setStyleSheet("background: transparent; border: none;")
                        card_layout.addWidget(icon_lbl, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
            except Exception:
                # Fallback emoji
                icon_lbl = QtWidgets.QLabel("⚡")
                icon_lbl.setStyleSheet("font-size: 28px; background: transparent; border: none;")
                icon_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                card_layout.addWidget(icon_lbl)
            
            # Entity name
            variant_text = "✨ " if is_exceptional else ""
            name_color = "#ffd700" if is_exceptional else "#bbb"
            name_label = QtWidgets.QLabel(f"{variant_text}Tesla Coil Sparky")
            name_label.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {name_color}; background: transparent; border: none;")
            name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(name_label)
            
            # Perk value
            if is_exceptional:
                bonus_color = "#4caf50"
                bonus_text = f"×{multiplier_value:.2f} (+20%)"
            else:
                bonus_color = "#8bc34a"
                bonus_text = f"×{multiplier_value:.2f} (Protected)"
            
            value_lbl = QtWidgets.QLabel(bonus_text)
            value_lbl.setStyleSheet(f"color: {bonus_color}; font-size: 11px; font-weight: bold; background: transparent; border: none;")
            value_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(value_lbl)
            
            container_layout.addWidget(card, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
            
            return container
            
        except Exception as e:
            print(f"[Tesla Coil Card] Error creating perk card: {e}")
            return None

    def _create_blank_parchment_perk_card(self, is_exceptional: bool, save_chance: float) -> Optional[QtWidgets.QWidget]:
        """Create a mini perk card showing Blank Parchment's item save chance (same style as ADHD Buster patrons)."""
        try:
            from entitidex.entity_pools import get_entity_by_id
            entity = get_entity_by_id("scholar_009")
            if not entity:
                return None
            
            # Container with title
            container = QtWidgets.QFrame()
            container.setStyleSheet("""
                QFrame {
                    background-color: #252530;
                    border: 1px solid #3a3a4a;
                    border-radius: 8px;
                    padding: 4px;
                }
            """)
            container_layout = QtWidgets.QVBoxLayout(container)
            container_layout.setContentsMargins(8, 6, 8, 6)
            container_layout.setSpacing(6)
            
            # Title for the perk
            if is_exceptional:
                title_text = "📜 Omniscient Scroll Active"
                title_color = "#ffd700"
                border_color = "#ffd700"
            else:
                title_text = "📜 Tabula Rasa Active"
                title_color = "#d7ccc8"
                border_color = "#d7ccc8"
            
            title = QtWidgets.QLabel(title_text)
            title.setStyleSheet(f"color: {title_color}; font-size: 11px; font-weight: bold; background: transparent;")
            title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            title.setToolTip(
                "Blank Parchment entity perk is active!\n\n"
                "If the Push Your Luck gamble fails, there's a chance\n"
                "your item will be saved instead of lost forever."
            )
            container_layout.addWidget(title)
            
            # Entity card (same style as ADHD Buster patrons)
            card = QtWidgets.QFrame()
            if is_exceptional:
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: #3a3a2a;
                        border: 2px solid {border_color};
                        border-radius: 6px;
                        padding: 4px;
                    }}
                """)
            else:
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: #3a3530;
                        border: 2px solid {border_color};
                        border-radius: 6px;
                        padding: 4px;
                    }}
                """)
            
            card_layout = QtWidgets.QVBoxLayout(card)
            card_layout.setContentsMargins(8, 6, 8, 6)
            card_layout.setSpacing(4)
            
            # Try to load entity SVG icon
            try:
                from entitidex_tab import _resolve_entity_svg_path
                from PySide6.QtSvg import QSvgRenderer
                
                svg_path = _resolve_entity_svg_path(entity, is_exceptional)
                if svg_path:
                    renderer = QSvgRenderer(svg_path)
                    if renderer.isValid():
                        icon_size = 48
                        pixmap = QtGui.QPixmap(icon_size, icon_size)
                        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
                        painter = QtGui.QPainter(pixmap)
                        renderer.render(painter)
                        painter.end()
                        
                        icon_lbl = QtWidgets.QLabel()
                        icon_lbl.setPixmap(pixmap)
                        icon_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                        icon_lbl.setFixedSize(icon_size, icon_size)
                        icon_lbl.setStyleSheet("background: transparent; border: none;")
                        card_layout.addWidget(icon_lbl, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
            except Exception:
                # Fallback emoji
                icon_lbl = QtWidgets.QLabel("📜")
                icon_lbl.setStyleSheet("font-size: 28px; background: transparent; border: none;")
                icon_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                card_layout.addWidget(icon_lbl)
            
            # Entity name
            variant_text = "✨ " if is_exceptional else ""
            name_color = "#ffd700" if is_exceptional else "#bbb"
            name_label = QtWidgets.QLabel(f"{variant_text}Blank Parchment")
            name_label.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {name_color}; background: transparent; border: none;")
            name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(name_label)
            
            # Perk value
            save_color = "#4caf50" if is_exceptional else "#8bc34a"
            value_lbl = QtWidgets.QLabel(f"{save_chance:.0f}% Item Recovery")
            value_lbl.setStyleSheet(f"color: {save_color}; font-size: 11px; font-weight: bold; background: transparent; border: none;")
            value_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            value_lbl.setToolTip(
                f"When Push Your Luck fails, you have a {save_chance:.0f}% chance\n"
                "to keep your current item instead of losing everything.\n\n"
                "This is a safety net from the Blank Parchment entity!"
            )
            card_layout.addWidget(value_lbl)
            
            container_layout.addWidget(card, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
            
            return container
            
        except Exception as e:
            print(f"[Blank Parchment Card] Error creating perk card: {e}")
            return None
    
    def _execute_push_your_luck(self):
        """Execute the push-your-luck re-roll with animation."""
        import random
        
        # Track cumulative multiplier for multiple re-rolls
        if not hasattr(self, 'push_luck_multiplier'):
            self.push_luck_multiplier = 1.0
        
        # Apply Tesla Coil gamble perk (modifies the base 0.80 penalty)
        # No Tesla Coil: 0.80 multiplier (penalty applied)
        # Normal Tesla Coil: 1.00 multiplier (penalty removed)
        # Exceptional Tesla Coil: 1.20 multiplier (bonus!)
        gamble_multiplier = 0.80  # Default: penalty without Tesla Coil
        gamble_safety_chance = 0
        blank_parchment_is_exceptional = False
        
        try:
            entitidex_data = self.adhd_buster.get("entitidex", {})
            collected = entitidex_data.get("collected_entity_ids", [])
            exceptional_entities = entitidex_data.get("exceptional_entities", {})
            
            # Tesla Coil check
            if "scientist_007" in collected:
                if "scientist_007" in exceptional_entities:
                    gamble_multiplier = 1.20  # +20% chance (bonus!)
                else:
                    gamble_multiplier = 1.00  # No penalty (protection)
            
            # Blank Parchment check for item recovery
            if "scholar_009" in collected:
                blank_parchment_is_exceptional = "scholar_009" in exceptional_entities
                gamble_safety_chance = 20 if blank_parchment_is_exceptional else 10
        except Exception:
            pass
        
        # Apply the gamble multiplier to cumulative tracker
        self.push_luck_multiplier *= gamble_multiplier
        
        adjusted_rate = self.success_rate * self.push_luck_multiplier
        adjusted_rate = max(0.01, min(0.99, adjusted_rate))  # Clamp between 1% and 99%
        
        roll = random.random()
        
        # Show dramatic roll animation
        animation_dialog = MergeRollAnimationDialog(
            roll, adjusted_rate,
            title="🎲 Push Your Luck!",
            success_text="✨ LUCK HOLDS! ✨",
            failure_text="💔 LUCK RAN OUT 💔",
            parent=self
        )
        animation_dialog.exec_()
        
        current_item = self.merge_result.get("result_item", {})
        rarity = current_item.get("rarity", "Common")
        rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        current_idx = rarity_order.index(rarity) if rarity in rarity_order else 0
        next_rarity = rarity_order[min(current_idx + 1, len(rarity_order) - 1)]
        
        if roll < adjusted_rate:
            # SUCCESS! Upgrade to next tier
            from gamification import generate_item
            story_id = current_item.get("story_theme", "warrior")
            new_item = generate_item(rarity=next_rarity, story_id=story_id)
            
            # Preserve some attributes from original
            if current_item.get("lucky_options"):
                new_item["lucky_options"] = current_item["lucky_options"].copy()
            
            # Update merge result
            self.merge_result["result_item"] = new_item
            self.merge_result["success"] = True
            
            # Show success and offer another re-roll if not Legendary
            self._show_success_dialog()
        else:
            # FAILURE! But check for Blank Parchment item recovery
            item_saved = False
            if gamble_safety_chance > 0:
                save_roll = random.random()
                if save_roll < (gamble_safety_chance / 100.0):
                    item_saved = True
                    self._show_item_saved_dialog(current_item, gamble_safety_chance, blank_parchment_is_exceptional, save_roll)
            
            if not item_saved:
                # Lose everything
                self.merge_result["success"] = False
                self.merge_result["push_luck_failed"] = True
                self.merge_result["roll"] = roll
                self.merge_result["needed"] = adjusted_rate
                
                # Show failure message
                self._show_push_luck_failure_dialog()
                self.accept()  # Close main dialog
    
    def _show_item_saved_dialog(self, saved_item: dict, save_chance: float, is_exceptional: bool, save_roll: float):
        """Show dialog when Blank Parchment saves the item from gamble failure."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        
        rarity = saved_item.get("rarity", "Common")
        name = saved_item.get("name", "Unknown Item")
        power = saved_item.get("power", 0)
        rarity_color = ITEM_RARITIES.get(rarity, {}).get("color", "#9e9e9e")
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📜 ITEM SAVED!")
        dialog.setModal(True)
        dialog.setMinimumWidth(350)
        dialog.setStyleSheet("""
            QDialog { background-color: #2a3a2a; }
            QLabel { color: #fff; }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title with scroll animation
        title = QLabel("📜 Ancient Wisdom Prevails! 📜")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4caf50;")
        layout.addWidget(title)
        
        # Roll info
        roll_info = QLabel(f"Recovery roll: {save_roll*100:.1f}% (needed < {save_chance:.0f}%)")
        roll_info.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        roll_info.setStyleSheet("font-size: 11px; color: #aaa;")
        layout.addWidget(roll_info)
        
        # Blank Parchment perk card
        perk_card = self._create_blank_parchment_perk_card(is_exceptional, save_chance)
        if perk_card:
            card_container = QHBoxLayout()
            card_container.addStretch()
            card_container.addWidget(perk_card)
            card_container.addStretch()
            layout.addLayout(card_container)
        
        # Saved item info
        item_label = QLabel(f"""
            <div style='text-align: center; padding: 10px;'>
                <p style='font-size: 14px; color: #8bc34a;'>✨ Your item was preserved! ✨</p>
                <p style='font-size: 16px; font-weight: bold; color: #fff;'>{name}</p>
                <p style='color: {rarity_color};'><b>{rarity}</b> • ⚔ Power: {power}</p>
            </div>
        """)
        item_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(item_label)
        
        # Note
        note = QLabel("The gamble failed, but you keep your current item!")
        note.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("font-size: 11px; color: #8bc34a; font-style: italic;")
        layout.addWidget(note)
        
        # OK button
        ok_btn = QPushButton("✓ Claim Item")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 24px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #66bb6a; }
        """)
        ok_btn.clicked.connect(dialog.accept)
        layout.addWidget(ok_btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec_()
        
        # Keep the current item - set success to True so item is retained
        self.merge_result["success"] = True
        self.merge_result["item_saved_by_perk"] = True
        self.accept()
    
    def _show_push_luck_failure_dialog(self):
        """Show failure message for push-your-luck."""
        roll = self.merge_result.get("roll", 0)
        needed = self.merge_result.get("needed", 0)
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("💥 GAMBLE FAILED!")
        msg.setIcon(QtWidgets.QMessageBox.NoIcon)
        
        text = f"""
        <div style='text-align: center;'>
            <h2 style='color: #f44336;'>💥 You Lost Everything! 💥</h2>
            <p style='color: #aaa;'>You rolled <b>{roll*100:.1f}%</b> (needed &lt; {needed*100:.1f}%)</p>
            <hr>
            <p style='color: #ff9800; font-size: 13px;'>
                ⚠️ The gamble didn't pay off this time.<br>
                All items have been lost.
            </p>
        </div>
        """
        
        msg.setText(text)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.setStyleSheet("""
            QMessageBox { background-color: #2e1e1e; }
            QLabel { color: #fff; font-size: 13px; }
            QPushButton {
                background-color: #757575;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
        """)
        msg.exec_()
    
    def _show_final_success_message(self, result_item: dict):
        """Show final success message with item comparison to equipped gear."""
        from styled_dialog import ItemRewardDialog
        
        rarity = result_item.get("rarity", "Common")
        slot = result_item.get("slot", "Unknown Slot")
        roll_raw = self.merge_result.get("roll", 0) if self.merge_result else 0
        needed_raw = self.merge_result.get("needed", 0) if self.merge_result else 0
        tier_upgraded = self.merge_result.get("tier_upgraded", False) if self.merge_result else False
        
        # Build extra messages with roll info
        extra_msgs = []
        
        # Build breakdown text
        breakdown_parts = []
        if self.items_merge_luck > 0:
            breakdown_parts.append(f"+{self.items_merge_luck}% from items")
        if self.boost_enabled:
            breakdown_parts.append("+25% boost")
        breakdown_text = f" ({', '.join(breakdown_parts)})" if breakdown_parts else ""
        
        extra_msgs.append(f"Roll: {roll_raw*100:.1f}% (needed < {needed_raw*100:.1f}%{breakdown_text})")
        
        if tier_upgraded:
            extra_msgs.append("⬆️ Tier Upgraded! (+50 🪙)")
        
        # Get currently equipped items for comparison
        equipped = self.adhd_buster.get("equipped", {})
        
        # Show ItemRewardDialog with comparison
        dialog = ItemRewardDialog(
            parent=self,
            title="🎉 Merge Success!",
            header_emoji="🎉",
            source_label="✨ Success! ✨",
            items_earned=[result_item],
            equipped=equipped,  # Compare against currently equipped
            coins_earned=0,
            extra_messages=extra_msgs,
            adhd_buster=self.adhd_buster,  # For themed slot names
        )
        dialog.exec_()
    
    def _show_failure_dialog(self):
        """Show merge failure dialog with recovery options (retry, claim, salvage)."""
        roll_raw = self.merge_result.get("roll", 0) if self.merge_result else 0
        needed_raw = self.merge_result.get("needed", 0) if self.merge_result else 0
        
        # Calculate how close the roll was (margin = how much we missed by)
        margin = roll_raw - needed_raw
        is_near_miss = margin > 0 and margin <= 0.05  # Within 5%
        
        # Calculate remaining coins after merge cost will be deducted
        # (merge cost is deducted AFTER dialog closes, so account for it here)
        total_merge_cost = self.merge_cost
        if self.boost_enabled:
            total_merge_cost += self.boost_cost
        if self.tier_upgrade_enabled:
            total_merge_cost += self.tier_upgrade_cost
            
        # Add accumulated retry costs
        total_merge_cost += self.retry_cost_accumulated
            
        remaining_coins = self.player_coins - total_merge_cost
        
        can_afford_retry = remaining_coins >= self.retry_bump_cost
        can_afford_claim = remaining_coins >= self.claim_cost

        # Salvage option - save one random item (discounted with both percentage and flat)
        # Use total_coin_discount which includes city Market bonus
        from gamification import apply_coin_discount, apply_coin_flat_reduction
        salvage_cost = apply_coin_flat_reduction(
            apply_coin_discount(COIN_COSTS.get("merge_salvage", 50), self.total_coin_discount),
            self.entity_coin_flat
        )
        can_afford_salvage = remaining_coins >= salvage_cost
        
        # Check if retry would help
        new_needed = min(needed_raw + 0.05, 1.0)  # +5% boost
        would_succeed_with_retry = roll_raw < new_needed
        
        # Store result for claim action
        self.near_miss_claimed = False
        self.salvage_requested = False
        
        msg = QtWidgets.QDialog(self)
        msg.setWindowTitle("💔 Merge Failed")
        msg.setMinimumWidth(450)
        
        layout = QtWidgets.QVBoxLayout(msg)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header = QtWidgets.QLabel("<h2 style='color: #f44336;'>💔 Failed 💔</h2>")
        header.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(header)
        
        # Roll info
        roll_info = QtWidgets.QLabel(
            f"<p style='color: #aaa;'><b>Roll:</b> {roll_raw*100:.1f}% (needed &lt; {needed_raw*100:.1f}%)</p>"
            f"<p style='color: #888;'>Missed by: {margin*100:.1f}%</p>"
        )
        roll_info.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(roll_info)
        
        # Running cost total (transparency improvement)
        cost_parts = [f"Base: {self.merge_cost}"]
        if self.boost_enabled:
            cost_parts.append(f"Boost: +{self.boost_cost}")
        if self.tier_upgrade_enabled:
            cost_parts.append(f"Tier: +{self.tier_upgrade_cost}")
        if self.retry_cost_accumulated > 0:
            cost_parts.append(f"Retries: +{self.retry_cost_accumulated}")
        cost_breakdown = " | ".join(cost_parts)
        
        cost_info = QtWidgets.QLabel(
            f"<p style='color: #ffc107; font-size: 11px;'>💰 <b>Spent so far:</b> {total_merge_cost} 🪙</p>"
            f"<p style='color: #888; font-size: 9px;'>{cost_breakdown}</p>"
        )
        cost_info.setAlignment(QtCore.Qt.AlignCenter)
        cost_info.setToolTip(f"Breakdown: {cost_breakdown}\nRemaining: {remaining_coins} coins")
        layout.addWidget(cost_info)
        
        # Near-miss options (only if within 5%)
        if is_near_miss:
            options_frame = QtWidgets.QWidget()
            options_frame.setStyleSheet("""
                QWidget {
                    background-color: #3a3a1a;
                    border: 1px solid #555;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
            options_layout = QtWidgets.QVBoxLayout(options_frame)
            options_layout.setSpacing(12)
            
            # Header for near-miss options
            near_miss_header = QtWidgets.QLabel(
                "<p style='color: #ffeb3b; font-size: 14px;'><b>⚡ SO CLOSE! Recovery Options:</b></p>"
            )
            near_miss_header.setAlignment(QtCore.Qt.AlignCenter)
            options_layout.addWidget(near_miss_header)
            
            # Option buttons layout
            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.setSpacing(12)
            
            # Retry button (50 coins to re-roll) - show new success threshold
            new_threshold = max(0, needed_raw - 0.05)  # -5% means easier (lower threshold)
            retry_text = f"🎲 Retry\n{self.retry_bump_cost} 🪙\n→ {new_threshold*100:.0f}%"
            if self.coin_discount > 0:
                original_retry = COIN_COSTS.get("merge_retry_bump", 50)
                savings = original_retry - self.retry_bump_cost
                retry_text = f"🎲 Retry\n{self.retry_bump_cost} 🪙 ✨-{savings}\n→ {new_threshold*100:.0f}%"
            retry_btn = QtWidgets.QPushButton(retry_text)
            retry_btn.setMinimumHeight(70)
            if can_afford_retry:
                retry_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ff9800;
                        color: white;
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                    QPushButton:hover { background-color: #ffa726; }
                """)
                retry_btn.setToolTip(f"Re-roll with easier threshold: need < {new_threshold*100:.1f}%\n(was {needed_raw*100:.1f}%, now -5% easier)\nTotal spent after: {total_merge_cost + self.retry_bump_cost} 🪙")
            else:
                retry_btn.setEnabled(False)
                retry_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #555;
                        color: #888;
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-size: 12px;
                    }
                """)
                retry_btn.setToolTip("Not enough coins")
            btn_layout.addWidget(retry_btn)
            
            # Claim button (+100 coins to get item directly) - show resulting rarity
            claim_rarity = self.result_rarity
            if self.tier_upgrade_enabled:
                try:
                    current_idx = RARITY_ORDER.index(claim_rarity)
                    if current_idx < len(RARITY_ORDER) - 1:
                        claim_rarity = RARITY_ORDER[current_idx + 1]
                except (ValueError, IndexError):
                    pass
            rarity_color = ITEM_RARITIES.get(claim_rarity, {}).get("color", "#fff")
            claim_text = f"✨ Claim {claim_rarity}\n{self.claim_cost} 🪙"
            if self.coin_discount > 0:
                original_claim = COIN_COSTS.get("merge_claim", 100)
                savings = original_claim - self.claim_cost
                claim_text = f"✨ Claim {claim_rarity}\n{self.claim_cost} 🪙 ✨-{savings}"
            claim_btn = QtWidgets.QPushButton(claim_text)
            claim_btn.setMinimumHeight(70)
            if can_afford_claim:
                claim_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #9c27b0;
                        color: {rarity_color};
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 11px;
                    }}
                    QPushButton:hover {{ background-color: #ab47bc; }}
                """)
                claim_btn.setToolTip(f"Pay {self.claim_cost} 🪙 to claim a {claim_rarity} item directly!\nTotal spent: {total_merge_cost + self.claim_cost} 🪙")
            else:
                claim_btn.setEnabled(False)
                claim_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #555;
                        color: #888;
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-size: 12px;
                    }
                """)
                claim_btn.setToolTip("Not enough coins")
            btn_layout.addWidget(claim_btn)
            
            options_layout.addLayout(btn_layout)
            
            # Info text with clear explanation
            info_text = QtWidgets.QLabel(
                f"<p style='color: #888; font-size: 10px;'>"
                f"<b>Retry:</b> Re-roll with +5% easier threshold | "
                f"<b>Claim:</b> Get {claim_rarity} item guaranteed</p>"
            )
            info_text.setAlignment(QtCore.Qt.AlignCenter)
            options_layout.addWidget(info_text)
            
            layout.addWidget(options_frame)
            
            # Connect buttons
            def on_claim():
                self.near_miss_claimed = True
                msg.accept()
            
            def on_retry():
                self.retry_cost_accumulated += self.retry_bump_cost
                self.is_retrying = True
                msg.reject()
            
            claim_btn.clicked.connect(on_claim)
            retry_btn.clicked.connect(on_retry)
        
        # Loss info
        loss_label = QtWidgets.QLabel(
            f"<p style='color: #ff6b6b;'><b>{len(self.items)} items lost forever.</b></p>"
        )
        loss_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(loss_label)
        
        # Salvage option - always available on failure
        salvage_frame = QtWidgets.QWidget()
        salvage_frame.setStyleSheet("""
            QWidget {
                background-color: #1a2e1a;
                border: 2px solid #4caf50;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        salvage_layout = QtWidgets.QVBoxLayout(salvage_frame)
        salvage_layout.setSpacing(8)
        
        salvage_header = QtWidgets.QLabel(
            "<p style='color: #4caf50; font-size: 12px;'><b>🛡️ Salvage Option:</b></p>"
        )
        salvage_header.setAlignment(QtCore.Qt.AlignCenter)
        salvage_layout.addWidget(salvage_header)
        
        salvage_btn = QtWidgets.QPushButton(f"🎁 Save Random Item ({salvage_cost} 🪙)")
        salvage_btn.setMinimumHeight(40)
        if can_afford_salvage and len(self.items) > 0:
            salvage_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #66bb6a; }
            """)
            salvage_btn.setToolTip("Save one random item from the merge")
        else:
            salvage_btn.setEnabled(False)
            salvage_btn.setStyleSheet("""
                QPushButton {
                    background-color: #555;
                    color: #888;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 12px;
                }
            """)
            salvage_btn.setToolTip("Not enough coins" if not can_afford_salvage else "No items to salvage")
        
        def on_salvage():
            self.salvage_requested = True
            msg.accept()
        
        salvage_btn.clicked.connect(on_salvage)
        salvage_layout.addWidget(salvage_btn)
        
        salvage_info = QtWidgets.QLabel(
            "<p style='color: #888; font-size: 10px;'>One random item from the merge will be returned to your inventory</p>"
        )
        salvage_info.setAlignment(QtCore.Qt.AlignCenter)
        salvage_layout.addWidget(salvage_info)
        
        layout.addWidget(salvage_frame)
        
        # Accept Loss button
        ok_btn = QtWidgets.QPushButton("😢 Accept Loss")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 10px 24px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e53935; }
        """)
        ok_btn.clicked.connect(msg.accept)
        layout.addWidget(ok_btn)
        
        msg.setStyleSheet("background-color: #2e1e1e;")
        result = msg.exec_()
        
        # Handle salvage action first (if requested)
        if self.salvage_requested and can_afford_salvage and len(self.items) > 0:
            # Deduct coins
            self.player_coins -= salvage_cost
            # Pick a random item to save
            import random
            saved_item = random.choice(self.items)
            # Mark in merge_result that we salvaged one item
            self.merge_result["salvaged_item"] = saved_item
            self.merge_result["salvage_cost"] = salvage_cost
            # Show styled confirmation dialog
            item_name = saved_item.get("name", "Unknown")
            item_rarity = saved_item.get("rarity", "Common")
            rarity_color = ITEM_RARITIES.get(item_rarity, {}).get("color", "#9e9e9e")
            item_power = saved_item.get("power", 0)
            item_slot = saved_item.get("slot", "Unknown")
            
            # Create styled dialog
            salvage_dialog = QtWidgets.QDialog(self)
            salvage_dialog.setWindowTitle("🎁 Item Salvaged!")
            salvage_dialog.setModal(True)
            salvage_dialog.setMinimumWidth(400)
            salvage_dialog.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.FramelessWindowHint)
            salvage_dialog.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            
            # Outer layout
            outer_layout = QtWidgets.QVBoxLayout(salvage_dialog)
            outer_layout.setContentsMargins(0, 0, 0, 0)
            
            # Main frame with styled border
            main_frame = QtWidgets.QFrame()
            main_frame.setObjectName("salvageFrame")
            main_frame.setStyleSheet("""
                QFrame#salvageFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1A2E1A, stop:1 #0D1A0D);
                    border: 2px solid #4caf50;
                    border-radius: 16px;
                }
                QLabel { color: #E0E0E0; background: transparent; }
            """)
            outer_layout.addWidget(main_frame)
            
            layout = QtWidgets.QVBoxLayout(main_frame)
            layout.setSpacing(16)
            layout.setContentsMargins(24, 20, 24, 20)
            
            # Title with icon
            title = QtWidgets.QLabel("🛡️ Item Salvaged! 🛡️")
            title.setAlignment(QtCore.Qt.AlignCenter)
            title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4caf50;")
            layout.addWidget(title)
            
            # Item card
            item_card = QtWidgets.QFrame()
            item_card.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(76, 175, 80, 0.1);
                    border: 1px solid {rarity_color};
                    border-radius: 8px;
                    padding: 12px;
                }}
            """)
            item_layout = QtWidgets.QVBoxLayout(item_card)
            item_layout.setSpacing(6)
            
            # Item name
            name_label = QtWidgets.QLabel(f"<b style='font-size: 16px;'>{item_name}</b>")
            name_label.setAlignment(QtCore.Qt.AlignCenter)
            name_label.setStyleSheet(f"color: {rarity_color};")
            item_layout.addWidget(name_label)
            
            # Item details
            details_label = QtWidgets.QLabel(f"<span style='color: {rarity_color};'>{item_rarity}</span> • ⚔ {item_power} Power • 📦 {item_slot}")
            details_label.setAlignment(QtCore.Qt.AlignCenter)
            details_label.setStyleSheet("font-size: 12px; color: #aaa;")
            item_layout.addWidget(details_label)
            
            layout.addWidget(item_card)
            
            # Message
            message = QtWidgets.QLabel("✨ This item has been returned to your inventory!")
            message.setAlignment(QtCore.Qt.AlignCenter)
            message.setStyleSheet("font-size: 13px; color: #8bc34a; font-style: italic;")
            message.setWordWrap(True)
            layout.addWidget(message)
            
            # Cost reminder
            cost_label = QtWidgets.QLabel(f"💰 Salvage cost: {salvage_cost} coins")
            cost_label.setAlignment(QtCore.Qt.AlignCenter)
            cost_label.setStyleSheet("font-size: 11px; color: #888;")
            layout.addWidget(cost_label)
            
            # OK button
            ok_btn = QtWidgets.QPushButton("✓ Continue")
            ok_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    padding: 10px 32px;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #66bb6a; }
            """)
            ok_btn.clicked.connect(salvage_dialog.accept)
            layout.addWidget(ok_btn, alignment=QtCore.Qt.AlignCenter)
            
            salvage_dialog.exec()
            return
        
        # Handle claim action
        if self.near_miss_claimed and can_afford_claim:
            # Deduct coins and generate the item
            self.player_coins -= self.claim_cost
            # Generate the item that would have been created
            from gamification import generate_item
            claimed_item = generate_item(
                rarity=self.result_rarity,
                story_id=self.items[0].get("story_theme") if self.items else None
            )
            # Apply tier upgrade if it was enabled
            if self.tier_upgrade_enabled:
                try:
                    current_idx = RARITY_ORDER.index(claimed_item.get("rarity", "Common"))
                    if current_idx < len(RARITY_ORDER) - 1:
                        new_rarity = RARITY_ORDER[current_idx + 1]
                        claimed_item["rarity"] = new_rarity
                        from gamification import RARITY_POWER
                        claimed_item["power"] = RARITY_POWER.get(new_rarity, claimed_item.get("power", 10))
                except (ValueError, IndexError):
                    pass
            
            # Update merge_result to show success
            self.merge_result["success"] = True
            self.merge_result["result_item"] = claimed_item
            self.merge_result["claimed_with_coins"] = True
            
            # Show success dialog for the claimed item
            self._show_success_dialog()
