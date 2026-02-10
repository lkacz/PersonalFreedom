"""
Enhanced Level Up Dialog - Industry-Standard UX
==============================================
Full-screen celebration with stat showcase and unlocks.
"""

from typing import Optional, Dict, Any
from PySide6 import QtWidgets, QtCore, QtGui
from styled_dialog import StyledDialog


class StatShowcaseWidget(QtWidgets.QWidget):
    """Display level-up stats with visual progression."""
    
    def __init__(self, old_level: int, new_level: int, stats: Dict[str, Any],
                 parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.old_level = old_level
        self.new_level = new_level
        self.stats = stats
        self._build_ui()
    
    def _build_ui(self):
        """Build stats showcase."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Level progression display
        level_progress = self._create_level_progress()
        layout.addWidget(level_progress)
        
        # Stats grid
        stats_grid = self._create_stats_grid()
        layout.addWidget(stats_grid)
        
        # Unlocks/rewards
        if self.stats.get("unlocks"):
            unlocks = self._create_unlocks_section()
            layout.addWidget(unlocks)
    
    def _create_level_progress(self) -> QtWidgets.QWidget:
        """Create level progression visual."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setSpacing(16)
        
        # Old level
        old_label = QtWidgets.QLabel(f"Level\n{self.old_level}")
        old_label.setAlignment(QtCore.Qt.AlignCenter)
        old_label.setStyleSheet("""
            background-color: #e0e0e0;
            border-radius: 8px;
            padding: 16px;
            font-size: 18px;
            font-weight: bold;
            color: #666;
        """)
        layout.addWidget(old_label)
        
        # Arrow
        arrow_label = QtWidgets.QLabel("→")
        arrow_label.setAlignment(QtCore.Qt.AlignCenter)
        arrow_label.setStyleSheet("font-size: 32px; color: #4caf50;")
        layout.addWidget(arrow_label)
        
        # New level (highlighted)
        new_label = QtWidgets.QLabel(f"Level\n{self.new_level}")
        new_label.setAlignment(QtCore.Qt.AlignCenter)
        new_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                         stop:0 #66bb6a, stop:1 #43a047);
            border-radius: 8px;
            padding: 16px;
            font-size: 22px;
            font-weight: bold;
            color: white;
            border: 2px solid #388e3c;
        """)
        layout.addWidget(new_label)
        
        return widget
    
    def _create_stats_grid(self) -> QtWidgets.QWidget:
        """Create grid of stat changes."""
        widget = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(widget)
        grid.setSpacing(10)
        
        # Show relevant stats
        stat_items = [
            ("⚔", "Total Power", self.stats.get("total_power", 0)),
            ("🏆", "Total XP", self.stats.get("total_xp", 0)),
            ("💰", "Total Coins", self.stats.get("total_coins", 0)),
            ("🎯", "Productivity Score", self.stats.get("productivity_score", 0)),
            ("⏱️", "Focus Time", f"{self.stats.get('total_focus_minutes', 0)}min"),
            ("📦", "Items Collected", self.stats.get("items_collected", 0))
        ]
        
        row = 0
        col = 0
        for emoji, label, value in stat_items:
            stat_card = self._create_stat_card(emoji, label, value)
            grid.addWidget(stat_card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        return widget
    
    def _create_stat_card(self, emoji: str, label: str, value) -> QtWidgets.QWidget:
        """Create individual stat card."""
        card = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(card)
        layout.setSpacing(4)
        
        # Emoji icon
        icon_label = QtWidgets.QLabel(emoji)
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 32px;")
        layout.addWidget(icon_label)
        
        # Value
        value_label = QtWidgets.QLabel(str(value))
        value_label.setAlignment(QtCore.Qt.AlignCenter)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(value_label)
        
        # Label
        text_label = QtWidgets.QLabel(label)
        text_label.setAlignment(QtCore.Qt.AlignCenter)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("font-size: 11px; color: #666;")
        layout.addWidget(text_label)
        
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        return card
    
    def _create_unlocks_section(self) -> QtWidgets.QWidget:
        """Create unlocks/rewards section."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setSpacing(8)
        
        # Header
        header = QtWidgets.QLabel("🔓 New Unlocks!")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #ff9800;
            padding: 8px;
        """)
        layout.addWidget(header)
        
        # List unlocks
        unlocks = self.stats.get("unlocks", [])
        for unlock in unlocks:
            unlock_label = QtWidgets.QLabel(f"✨ {unlock}")
            unlock_label.setAlignment(QtCore.Qt.AlignCenter)
            unlock_label.setStyleSheet("font-size: 12px; color: #555;")
            layout.addWidget(unlock_label)
        
        widget.setStyleSheet("""
            QWidget {
                background-color: #fff8e1;
                border: 2px solid #ffb74d;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        return widget


class EnhancedLevelUpDialog(StyledDialog):
    """
    Enhanced level-up dialog with full celebration experience.
    
    Features:
    - Consistent StyledDialog design with gold accents
    - Animated stat showcase
    - Level progression visual
    - Unlocks and rewards
    - Victory sound effects
    - Quick actions
    """
    
    view_stats = QtCore.Signal()
    claim_rewards = QtCore.Signal()
    
    def __init__(self, old_level: int, new_level: int, stats: Dict[str, Any],
                 fullscreen: bool = False, parent: Optional[QtWidgets.QWidget] = None):
        self.old_level = old_level
        self.new_level = new_level
        self.stats = stats
        self.fullscreen_mode = fullscreen
        
        # Initialize StyledDialog with celebration header
        super().__init__(
            title="LEVEL UP!",
            header_icon="🎊",
            closable=not fullscreen,
            parent=parent
        )
        
        if fullscreen:
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
            self.showFullScreen()
        else:
            # Constrain height to fit most screens (leave room for taskbar)
            self.setMinimumSize(550, 500)
            self.setMaximumHeight(700)  # Max height to fit on 768px screens
        
        QtCore.QTimer.singleShot(200, self._start_celebration)
    
    def _build_content(self, layout: QtWidgets.QVBoxLayout):
        """Build the dialog content using StyledDialog pattern."""
        # Create scroll area for content in windowed mode
        if not self.fullscreen_mode:
            scroll = QtWidgets.QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
            
            scroll_content = QtWidgets.QWidget()
            content_layout = QtWidgets.QVBoxLayout(scroll_content)
            content_layout.setSpacing(15)
            content_layout.setContentsMargins(0, 0, 0, 0)
        else:
            content_layout = layout
            content_layout.setAlignment(QtCore.Qt.AlignCenter)
        
        # Celebration header (animated)
        self.header_label = QtWidgets.QLabel("🎊 LEVEL UP! 🎊")
        self.header_label.setAlignment(QtCore.Qt.AlignCenter)
        # Smaller header for windowed mode, gold color to match theme
        header_size = "48px" if self.fullscreen_mode else "32px"
        self.header_label.setStyleSheet(f"""
            font-size: {header_size};
            font-weight: bold;
            color: {self.BORDER_COLOR};
            padding: 15px;
            background: transparent;
        """)
        content_layout.addWidget(self.header_label)
        
        # Level difference message
        levels_gained = self.new_level - self.old_level
        if levels_gained > 1:
            msg = f"🌟 {levels_gained} LEVELS GAINED! 🌟"
            multi_label = QtWidgets.QLabel(msg)
            multi_label.setAlignment(QtCore.Qt.AlignCenter)
            multi_size = "24px" if self.fullscreen_mode else "18px"
            multi_label.setStyleSheet(f"""
                font-size: {multi_size};
                font-weight: bold;
                color: #ff9800;
                padding: 8px;
                background: transparent;
            """)
            content_layout.addWidget(multi_label)
        
        # Stats showcase (in container for centering)
        showcase_container = QtWidgets.QWidget()
        if not self.fullscreen_mode:
            showcase_container.setMaximumWidth(500)
        showcase_layout = QtWidgets.QVBoxLayout(showcase_container)
        showcase_layout.setContentsMargins(0, 0, 0, 0)
        
        showcase = StatShowcaseWidget(self.old_level, self.new_level, self.stats)
        showcase_layout.addWidget(showcase)
        
        content_layout.addWidget(showcase_container, alignment=QtCore.Qt.AlignCenter if self.fullscreen_mode else QtCore.Qt.AlignLeft)
        
        # Motivational message
        messages = [
            "You're unstoppable! Keep going! 💪",
            "Excellence is a habit - you're proving it! 🏆",
            "Your dedication is inspiring! ⭐",
            "Champion mindset unlocked! 👑",
            "Greatness achieved through focus! 🎯"
        ]
        import random
        msg = random.choice(messages)
        msg_label = QtWidgets.QLabel(msg)
        msg_label.setAlignment(QtCore.Qt.AlignCenter)
        msg_size = "16px" if self.fullscreen_mode else "13px"
        msg_label.setStyleSheet(f"""
            font-size: {msg_size};
            font-weight: bold;
            color: {self.TEXT_COLOR};
            padding: 8px;
            background: transparent;
        """)
        content_layout.addWidget(msg_label)
        
        # Finalize scroll area in windowed mode
        if not self.fullscreen_mode:
            scroll.setWidget(scroll_content)
            layout.addWidget(scroll)
        
        # Action buttons using StyledDialog button row
        buttons = [
            ("📊 View Stats", "default", self._on_view_stats),
        ]
        
        # Claim rewards button if rewards exist
        if self.stats.get("rewards"):
            buttons.append(("🎁 Claim Rewards", "primary", self._on_claim_rewards))
        
        buttons.append(("✓ Continue", "primary", self.accept))
        
        self.add_button_row(layout, buttons, centered=True)
    
    def _start_celebration(self):
        """Start celebration animations and effects."""
        # Victory sound using lottery sound system
        try:
            from lottery_sounds import play_win_sound
            play_win_sound()
        except Exception:
            pass
        
        # Header animation
        self._animation_step = 0
        self._animation_timer = QtCore.QTimer(self)
        self._animation_timer.timeout.connect(self._animate_celebration)
        self._animation_timer.start(180)
    
    def _animate_celebration(self):
        """Animate the celebration header."""
        self._animation_step += 1
        
        # Stop after 50 steps
        if self._animation_step >= 50:
            self._animation_timer.stop()
            return
        
        # Emoji rotation
        emojis = ["🎊", "🎉", "⭐", "🌟", "✨", "💫", "🎊", "🏆", "👑", "💪"]
        emoji = emojis[self._animation_step % len(emojis)]
        
        self.header_label.setText(f"{emoji} LEVEL UP! {emoji}")
        
        # Color pulse with gold theme
        colors = [self.BORDER_COLOR, "#FFEB3B", "#FFC107", "#FFEB3B"]
        color = colors[self._animation_step % len(colors)]
        header_size = "48px" if self.fullscreen_mode else "32px"
        self.header_label.setStyleSheet(f"""
            font-size: {header_size};
            font-weight: bold;
            color: {color};
            padding: 15px;
            background: transparent;
        """)
    
    def _on_view_stats(self):
        """Handle view stats action."""
        self.view_stats.emit()
        # Don't close - let user view stats
    
    def _on_claim_rewards(self):
        """Handle claim rewards action."""
        self.claim_rewards.emit()
        self.accept()
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Space):
            self.accept()
        elif event.key() == QtCore.Qt.Key_Escape:
            if not self.fullscreen_mode:
                self.accept()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Clean up animations."""
        if hasattr(self, '_animation_timer'):
            self._animation_timer.stop()
        super().closeEvent(event)
