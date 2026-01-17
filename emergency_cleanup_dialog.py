"""
Enhanced Emergency Cleanup Confirmation - Industry-Standard UX
============================================================
Comprehensive confirmation dialog with impact preview and safety checks.
"""

from typing import Optional, List, Dict, Any
from PySide6 import QtWidgets, QtCore, QtGui


class ImpactPreviewWidget(QtWidgets.QWidget):
    """Preview the impact of emergency cleanup actions."""
    
    def __init__(self, impact_data: Dict[str, Any],
                 parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.impact_data = impact_data
        self._build_ui()
    
    def _build_ui(self):
        """Build impact preview display."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Warning banner
        warning_banner = self._create_warning_banner()
        layout.addWidget(warning_banner)
        
        # Impact summary
        summary = self._create_impact_summary()
        layout.addWidget(summary)
        
        # Item breakdown
        if self.impact_data.get("items_affected"):
            items_section = self._create_items_section()
            layout.addWidget(items_section)
    
    def _create_warning_banner(self) -> QtWidgets.QWidget:
        """Create warning banner."""
        banner = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(banner)
        layout.setSpacing(8)
        
        # Warning icon
        icon_label = QtWidgets.QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 32px;")
        layout.addWidget(icon_label)
        
        # Warning text
        text = QtWidgets.QLabel("This action cannot be undone!")
        text.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #d32f2f;
        """)
        layout.addWidget(text)
        layout.addStretch()
        
        banner.setStyleSheet("""
            QWidget {
                background-color: #ffebee;
                border: 2px solid #ef5350;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        return banner
    
    def _create_impact_summary(self) -> QtWidgets.QWidget:
        """Create impact summary grid."""
        widget = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(widget)
        grid.setSpacing(8)
        
        # Impact items
        impacts = [
            ("📦", "Items Lost", self.impact_data.get("items_count", 0)),
            ("⚔", "Power Lost", self.impact_data.get("power_lost", 0)),
            ("🏆", "Progress Lost", f"{self.impact_data.get('progress_percent', 0)}%"),
            ("💰", "Coins Refund", self.impact_data.get("coins_refund", 0))
        ]
        
        row = 0
        col = 0
        for emoji, label, value in impacts:
            card = self._create_impact_card(emoji, label, value)
            grid.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        return widget
    
    def _create_impact_card(self, emoji: str, label: str, value) -> QtWidgets.QWidget:
        """Create individual impact card."""
        card = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(4)
        
        # Emoji
        icon_label = QtWidgets.QLabel(emoji)
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon_label)
        
        # Value
        value_label = QtWidgets.QLabel(str(value))
        value_label.setAlignment(QtCore.Qt.AlignCenter)
        value_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f;")
        layout.addWidget(value_label)
        
        # Label
        text_label = QtWidgets.QLabel(label)
        text_label.setAlignment(QtCore.Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(text_label)
        
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        
        return card
    
    def _create_items_section(self) -> QtWidgets.QWidget:
        """Create items affected section."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(6)
        
        # Header
        header = QtWidgets.QLabel("Items to be removed:")
        header.setStyleSheet("font-weight: bold; font-size: 12px; color: #333;")
        layout.addWidget(header)
        
        # Scrollable list
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(150)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)
        
        items_container = QtWidgets.QWidget()
        items_layout = QtWidgets.QVBoxLayout(items_container)
        items_layout.setSpacing(4)
        
        # List items
        items = self.impact_data.get("items_affected", [])
        for item in items[:10]:  # Show max 10
            item_label = QtWidgets.QLabel(f"• {item.get('name', 'Unknown')} ({item.get('rarity', 'Common')})")
            item_label.setStyleSheet("font-size: 11px; color: #555;")
            items_layout.addWidget(item_label)
        
        if len(items) > 10:
            more_label = QtWidgets.QLabel(f"... and {len(items) - 10} more")
            more_label.setStyleSheet("font-size: 11px; color: #999; font-style: italic;")
            items_layout.addWidget(more_label)
        
        items_layout.addStretch()
        scroll.setWidget(items_container)
        layout.addWidget(scroll)
        
        return widget


class EmergencyCleanupDialog(QtWidgets.QDialog):
    """
    Enhanced emergency cleanup confirmation dialog.
    
    Features:
    - Clear impact preview
    - Safety confirmation checkbox
    - Detailed breakdown of consequences
    - Alternative actions suggested
    - Professional warning UX
    - Keyboard shortcuts
    - Undo warning
    """
    
    def __init__(self, cleanup_type: str, impact_data: Dict[str, Any],
                 parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.cleanup_type = cleanup_type
        self.impact_data = impact_data
        self.confirmed = False
        
        titles = {
            "reset_inventory": "⚠️ Reset Inventory",
            "reset_progress": "⚠️ Reset All Progress",
            "reset_stats": "⚠️ Reset Statistics",
            "emergency_cleanup": "⚠️ Emergency Cleanup"
        }
        self.setWindowTitle(titles.get(cleanup_type, "⚠️ Confirm Action"))
        # Reduced height with scrolling support
        self.setMinimumSize(500, 450)
        self.setMaximumHeight(650)  # Fit on 768px screens
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the complete dialog UI."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Create scroll area for main content
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(scroll_content)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(8, 8, 8, 8)
        
        # Header with warning
        header_label = QtWidgets.QLabel("⚠️ EMERGENCY ACTION ⚠️")
        header_label.setAlignment(QtCore.Qt.AlignCenter)
        header_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #d32f2f;
            padding: 10px;
            background: transparent;
        """)
        content_layout.addWidget(header_label)
        
        # Action description
        descriptions = {
            "reset_inventory": "This will permanently remove all items from your inventory.",
            "reset_progress": "This will reset ALL game progress, including level, XP, and items.",
            "reset_stats": "This will reset all tracked statistics and history.",
            "emergency_cleanup": "This will perform emergency cleanup operations."
        }
        desc = descriptions.get(self.cleanup_type, "This action will make permanent changes.")
        
        desc_label = QtWidgets.QLabel(desc)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(QtCore.Qt.AlignCenter)
        desc_label.setStyleSheet("""
            font-size: 13px;
            color: #555;
            padding: 6px;
            background: transparent;
        """)
        content_layout.addWidget(desc_label)
        
        # Impact preview
        impact_preview = ImpactPreviewWidget(self.impact_data)
        content_layout.addWidget(impact_preview)
        
        # Alternative actions
        alternatives = self._create_alternatives_section()
        content_layout.addWidget(alternatives)
        
        # Separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #ddd;")
        content_layout.addWidget(line)
        
        # Finalize scroll area
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # Safety confirmation checkbox (outside scroll)
        self.confirm_checkbox = QtWidgets.QCheckBox("I understand this action cannot be undone")
        self.confirm_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 12px;
                font-weight: bold;
                color: #d32f2f;
                padding: 6px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.confirm_checkbox.stateChanged.connect(self._on_checkbox_changed)
        main_layout.addWidget(self.confirm_checkbox)
        
        # Action buttons (outside scroll)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(12)
        
        # Cancel (safe default)
        cancel_btn = QtWidgets.QPushButton("✗ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setDefault(True)  # Default action
        button_layout.addWidget(cancel_btn)
        
        # Confirm (dangerous action)
        self.confirm_btn = QtWidgets.QPushButton("⚠️ Proceed with Cleanup")
        self.confirm_btn.setEnabled(False)  # Disabled until checkbox is checked
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #9e9e9e;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:enabled {
                background-color: #d32f2f;
            }
            QPushButton:enabled:hover {
                background-color: #c62828;
            }
        """)
        self.confirm_btn.clicked.connect(self._on_confirm)
        button_layout.addWidget(self.confirm_btn)
        
        main_layout.addLayout(button_layout)
        
        # Dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #fafafa;
                border: 2px solid #e57373;
                border-radius: 12px;
            }
        """)
    
    def _create_alternatives_section(self) -> QtWidgets.QWidget:
        """Create alternatives suggestion section."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # Header
        header = QtWidgets.QLabel("💡 Consider these alternatives:")
        header.setStyleSheet("font-weight: bold; font-size: 12px; color: #ff9800;")
        layout.addWidget(header)
        
        # Suggestions based on cleanup type
        suggestions = {
            "reset_inventory": [
                "Merge duplicate items to save space",
                "Sell unwanted items for coins",
                "Use storage upgrades"
            ],
            "reset_progress": [
                "Take a break instead",
                "Set new goals without resetting",
                "Export your data for backup"
            ],
            "reset_stats": [
                "Archive current stats before reset",
                "Start a new session instead",
                "View stats summary first"
            ],
            "emergency_cleanup": [
                "Check logs for errors",
                "Restart the application",
                "Contact support"
            ]
        }
        
        alt_suggestions = suggestions.get(self.cleanup_type, [])
        for suggestion in alt_suggestions:
            label = QtWidgets.QLabel(f"• {suggestion}")
            label.setStyleSheet("font-size: 11px; color: #666;")
            layout.addWidget(label)
        
        widget.setStyleSheet("""
            QWidget {
                background-color: #fff8e1;
                border: 1px solid #ffb74d;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        
        return widget
    
    def _on_checkbox_changed(self, state):
        """Handle checkbox state change."""
        self.confirm_btn.setEnabled(state == QtCore.Qt.Checked)
    
    def _on_confirm(self):
        """Handle confirm action."""
        # Double-check with system dialog (silent - no sound)
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Final Confirmation")
        msg.setText("Are you absolutely sure?\n\nThis action CANNOT be undone!")
        msg.setIcon(QtWidgets.QMessageBox.NoIcon)
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg.setDefaultButton(QtWidgets.QMessageBox.No)
        msg.setOption(QtWidgets.QMessageBox.DontUseNativeDialog, True)
        reply = msg.exec_()
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.confirmed = True
            self.accept()
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == QtCore.Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


def show_emergency_cleanup_dialog(cleanup_type: str, impact_data: Dict[str, Any],
                                   parent: Optional[QtWidgets.QWidget] = None) -> bool:
    """
    Convenience function to show emergency cleanup dialog.
    
    Args:
        cleanup_type: Type of cleanup ('reset_inventory', 'reset_progress', etc.)
        impact_data: Dictionary containing impact information
        parent: Parent widget
    
    Returns:
        True if user confirmed the action, False otherwise
    """
    dialog = EmergencyCleanupDialog(cleanup_type, impact_data, parent)
    result = dialog.exec()
    return result == QtWidgets.QDialog.Accepted and dialog.confirmed
