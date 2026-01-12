"""
Lucky Merge Dialog - Industry-Standard UX
==========================================
Professional merge UI with visual feedback, animations, and comprehensive information display.
"""

from datetime import datetime
from typing import Optional
from PySide6 import QtWidgets, QtCore, QtGui

try:
    from gamification import (
        calculate_merge_success_rate, 
        get_merge_result_rarity,
        calculate_total_lucky_bonuses,
        perform_lucky_merge,
        ITEM_RARITIES,
        RARITY_POWER
    )
    GAMIFICATION_AVAILABLE = True
except ImportError:
    GAMIFICATION_AVAILABLE = False


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
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"


class SuccessRateWidget(QtWidgets.QWidget):
    """Visual success rate display with progress bar and breakdown."""
    
    def __init__(self, rate: float, breakdown: dict, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.rate = rate
        self.breakdown = breakdown
        self._build_ui()
    
    def _build_ui(self):
        """Build the success rate visualization."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Header
        header = QtWidgets.QLabel("🎲 Success Probability")
        header.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        layout.addWidget(header)
        
        # Progress bar
        progress_container = QtWidgets.QWidget()
        progress_layout = QtWidgets.QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        progress = QtWidgets.QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(int(self.rate * 100))
        progress.setFormat(f"{self.rate * 100:.1f}%")
        progress.setTextVisible(True)
        
        # Color based on rate
        if self.rate >= 0.7:
            color = "#4caf50"  # Green
        elif self.rate >= 0.4:
            color = "#ff9800"  # Orange
        else:
            color = "#f44336"  # Red
        
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #ddd;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                font-size: 16px;
                background-color: #f5f5f5;
                height: 32px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:1 {self._lighten_color(color)});
                border-radius: 6px;
            }}
        """)
        progress_layout.addWidget(progress)
        layout.addWidget(progress_container)
        
        # Breakdown
        breakdown_label = QtWidgets.QLabel("<b>Calculation Breakdown:</b>")
        breakdown_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(breakdown_label)
        
        breakdown_text = ""
        for component, value in self.breakdown.items():
            breakdown_text += f"  • {component}: +{value}%\n"
        
        breakdown_details = QtWidgets.QLabel(breakdown_text.strip())
        breakdown_details.setStyleSheet("color: #888; font-size: 10px; padding-left: 10px;")
        layout.addWidget(breakdown_details)
    
    def _lighten_color(self, hex_color: str, factor: float = 1.2) -> str:
        """Lighten a hex color."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"


class ResultPreviewWidget(QtWidgets.QWidget):
    """Preview of potential merge result."""
    
    def __init__(self, result_rarity: str, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.result_rarity = result_rarity
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
        title = QtWidgets.QLabel("On Success")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #666;")
        layout.addWidget(title)
        
        # Rarity
        rarity_label = QtWidgets.QLabel(f"<b>{self.result_rarity}</b> Item")
        rarity_label.setAlignment(QtCore.Qt.AlignCenter)
        rarity_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        layout.addWidget(rarity_label)
        
        # Stars
        stars = min(5, max(1, list(ITEM_RARITIES.keys()).index(self.result_rarity) + 1))
        stars_label = QtWidgets.QLabel("★" * stars)
        stars_label.setAlignment(QtCore.Qt.AlignCenter)
        stars_label.setStyleSheet(f"color: {color}; font-size: 16px;")
        layout.addWidget(stars_label)
        
        # Power range
        power_label = QtWidgets.QLabel(f"⚔ ~{power}")
        power_label.setAlignment(QtCore.Qt.AlignCenter)
        power_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(power_label)
        
        self.setStyleSheet(f"""
            ResultPreviewWidget {{
                background: #f9f9f9;
                border: 2px dashed {color};
                border-radius: 12px;
            }}
        """)
    
    def _darken_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Darken a hex color."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"


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
    """
    
    def __init__(self, items: list, luck: int, equipped: dict, 
                 parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.items = items
        self.luck = luck
        self.equipped = equipped
        self.merge_result = None
        
        # Calculate merge stats
        if GAMIFICATION_AVAILABLE and calculate_total_lucky_bonuses:
            lucky_bonuses = calculate_total_lucky_bonuses(equipped)
            self.merge_luck_bonus = lucky_bonuses.get("merge_luck", 0)
        else:
            self.merge_luck_bonus = 0
        
        if GAMIFICATION_AVAILABLE:
            self.success_rate = calculate_merge_success_rate(
                items, luck, gear_merge_luck=self.merge_luck_bonus
            )
            self.result_rarity = get_merge_result_rarity(items)
        else:
            self.success_rate = 0.5
            self.result_rarity = "Rare"
        
        # Calculate breakdown
        base_rate = 0.10
        item_bonus = max(0, len(items) - 1) * 0.03
        luck_bonus = luck * 0.02
        gear_bonus = self.merge_luck_bonus / 100.0
        
        self.breakdown = {
            "Base Rate": int(base_rate * 100),
            f"Item Count ({len(items)} items)": int(item_bonus * 100),
            f"Legacy Luck ({luck})": int(luck_bonus * 100),
        }
        if self.merge_luck_bonus > 0:
            self.breakdown[f"Equipped Gear Bonus"] = self.merge_luck_bonus
        
        self.setWindowTitle("⚡ Lucky Merge")
        self.setMinimumSize(700, 600)
        self._build_ui()
    
    def _build_ui(self):
        """Build the complete merge dialog UI."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header = QtWidgets.QLabel("⚡ Lucky Merge")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333;
            padding: 10px;
        """)
        header.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Subtitle
        subtitle = QtWidgets.QLabel(
            f"Combining {len(self.items)} items into something greater..."
        )
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(subtitle)
        
        # Separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #ddd;")
        main_layout.addWidget(line)
        
        # Items preview section
        items_section = self._create_items_section()
        main_layout.addWidget(items_section)
        
        # Arrow
        arrow = QtWidgets.QLabel("⬇")
        arrow.setAlignment(QtCore.Qt.AlignCenter)
        arrow.setStyleSheet("font-size: 32px; color: #999;")
        main_layout.addWidget(arrow)
        
        # Result preview and success rate side by side
        middle_section = QtWidgets.QWidget()
        middle_layout = QtWidgets.QHBoxLayout(middle_section)
        middle_layout.setSpacing(20)
        
        # Success rate on left
        success_widget = SuccessRateWidget(self.success_rate, self.breakdown)
        middle_layout.addWidget(success_widget, stretch=2)
        
        # Result preview on right
        result_widget = ResultPreviewWidget(self.result_rarity)
        middle_layout.addWidget(result_widget, stretch=1)
        
        main_layout.addWidget(middle_section)
        
        # Warning section
        warning_box = self._create_warning_box()
        main_layout.addWidget(warning_box)
        
        # Spacer
        main_layout.addStretch()
        
        # Buttons
        button_box = self._create_button_box()
        main_layout.addWidget(button_box)
        
        # Set dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #fafafa;
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
    
    def _create_items_section(self) -> QtWidgets.QWidget:
        """Create the items preview section."""
        section = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(section)
        layout.setSpacing(12)
        
        # Title
        title = QtWidgets.QLabel("📦 Items to Merge")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        layout.addWidget(title)
        
        # Items grid
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(220)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
            }
        """)
        
        scroll_content = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(scroll_content)
        grid.setSpacing(12)
        grid.setContentsMargins(12, 12, 12, 12)
        
        # Add item preview widgets
        items_per_row = 4
        for idx, item in enumerate(self.items):
            row = idx // items_per_row
            col = idx % items_per_row
            preview = ItemPreviewWidget(item)
            grid.addWidget(preview, row, col)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return section
    
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
        text = QtWidgets.QLabel(
            "<b>Warning:</b> Merge failure will destroy ALL selected items permanently. "
            "This action cannot be undone!"
        )
        text.setWordWrap(True)
        text.setStyleSheet("color: #d32f2f; font-size: 12px;")
        warning_layout.addWidget(text, stretch=1)
        
        warning.setStyleSheet("""
            QWidget {
                background-color: #ffebee;
                border: 2px solid #f44336;
                border-radius: 8px;
            }
        """)
        
        return warning
    
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
        """Execute the merge with animated feedback."""
        if not GAMIFICATION_AVAILABLE:
            QtWidgets.QMessageBox.warning(
                self, "Feature Unavailable",
                "Gamification features are not available."
            )
            return
        
        # Show processing overlay
        self._show_processing()
        
        # Perform merge
        story_id = self.items[0].get("story_theme", "warrior") if self.items else "warrior"
        self.merge_result = perform_lucky_merge(
            self.items, self.luck,
            story_id=story_id,
            gear_merge_luck=self.merge_luck_bonus
        )
        
        # Delay to show animation
        QtCore.QTimer.singleShot(1500, self._show_result)
    
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
        else:
            self._show_failure_dialog()
        
        self.accept()
    
    def _show_success_dialog(self):
        """Show success result dialog."""
        result_item = self.merge_result.get("result_item", {}) if self.merge_result else {}
        rarity = result_item.get("rarity", "Common")
        name = result_item.get("name", "Unknown Item")
        power = result_item.get("power", 0)
        roll = self.merge_result.get("roll_pct", 0) if self.merge_result else 0
        needed = self.merge_result.get("needed_pct", 0) if self.merge_result else 0
        
        rarity_color = ITEM_RARITIES.get(rarity, {}).get("color", "#9e9e9e")
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("🎉 MERGE SUCCESS!")
        msg.setIcon(QtWidgets.QMessageBox.Information)
        
        text = f"""
        <div style='text-align: center;'>
            <h2 style='color: {rarity_color};'>✨ Success! ✨</h2>
            <p><b>Roll:</b> {roll}% (needed &lt; {needed}%)</p>
            <hr>
            <p style='font-size: 16px;'><b>{name}</b></p>
            <p style='color: {rarity_color};'><b>{rarity}</b> • ⚔ Power: {power}</p>
        </div>
        """
        
        # Add lucky options if present
        if result_item.get("lucky_options"):
            from gamification import format_lucky_options
            try:
                lucky_text = format_lucky_options(result_item["lucky_options"])
                if lucky_text:
                    text += f"<p>✨ <b>Lucky Options:</b> {lucky_text}</p>"
            except Exception:
                pass
        
        msg.setText(text)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: #f1f8e9;
            }}
            QLabel {{
                font-size: 13px;
            }}
        """)
        msg.exec_()
    
    def _show_failure_dialog(self):
        """Show failure result dialog."""
        roll = self.merge_result.get("roll_pct", 0) if self.merge_result else 0
        needed = self.merge_result.get("needed_pct", 0) if self.merge_result else 0
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("💔 Merge Failed")
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        
        text = f"""
        <div style='text-align: center;'>
            <h2 style='color: #f44336;'>💔 Failed 💔</h2>
            <p><b>Roll:</b> {roll}% (needed &lt; {needed}%)</p>
            <hr>
            <p style='color: #d32f2f;'><b>{len(self.items)} items lost forever.</b></p>
            <p>Better luck next time!</p>
        </div>
        """
        
        msg.setText(text)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #ffebee;
            }
            QLabel {
                font-size: 13px;
            }
        """)
        msg.exec_()
