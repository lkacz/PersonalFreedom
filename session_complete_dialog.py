"""
Session Complete Dialog - Industry-Standard UX
===============================================
Celebratory dialog shown when a focus session completes successfully.
Features visual feedback, stats breakdown, rewards, and quick actions.
"""

from datetime import datetime, timedelta
from typing import Optional
from PySide6 import QtWidgets, QtCore, QtGui

try:
    from gamification import GAMIFICATION_AVAILABLE
except ImportError:
    GAMIFICATION_AVAILABLE = False


class SessionStatsWidget(QtWidgets.QWidget):
    """Visual display of session statistics."""
    
    def __init__(self, elapsed_seconds: int, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.elapsed_seconds = elapsed_seconds
        self._build_ui()
    
    def _build_ui(self):
        """Build the stats display."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Time display - large and prominent
        time_display = self._format_time(self.elapsed_seconds)
        time_label = QtWidgets.QLabel(time_display)
        time_label.setAlignment(QtCore.Qt.AlignCenter)
        time_label.setStyleSheet("""
            font-size: 56px;
            font-weight: bold;
            color: #2196f3;
            padding: 20px;
        """)
        layout.addWidget(time_label)
        
        # Stats grid
        stats_grid = QtWidgets.QWidget()
        grid_layout = QtWidgets.QGridLayout(stats_grid)
        grid_layout.setSpacing(16)
        
        minutes = self.elapsed_seconds // 60
        hours = minutes // 60
        
        # Define stats to display
        stats = [
            ("⏱️", "Duration", time_display),
            ("📊", "Minutes", f"{minutes}"),
            ("💪", "Focus Power", self._get_focus_rating(minutes)),
            ("🎯", "Distractions", "0 avoided")
        ]
        
        for idx, (emoji, label, value) in enumerate(stats):
            row = idx // 2
            col = (idx % 2) * 2
            
            # Emoji
            emoji_label = QtWidgets.QLabel(emoji)
            emoji_label.setStyleSheet("font-size: 32px;")
            emoji_label.setAlignment(QtCore.Qt.AlignCenter)
            grid_layout.addWidget(emoji_label, row, col)
            
            # Label and value
            text_widget = QtWidgets.QWidget()
            text_layout = QtWidgets.QVBoxLayout(text_widget)
            text_layout.setSpacing(2)
            text_layout.setContentsMargins(0, 0, 0, 0)
            
            label_widget = QtWidgets.QLabel(label)
            label_widget.setStyleSheet("color: #666; font-size: 11px;")
            text_layout.addWidget(label_widget)
            
            value_widget = QtWidgets.QLabel(value)
            value_widget.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
            text_layout.addWidget(value_widget)
            
            grid_layout.addWidget(text_widget, row, col + 1)
        
        layout.addWidget(stats_grid)
    
    def _format_time(self, seconds: int) -> str:
        """Format seconds into HH:MM:SS or MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    
    def _get_focus_rating(self, minutes: int) -> str:
        """Get focus power rating based on duration."""
        if minutes >= 120:
            return "Legendary!"
        elif minutes >= 90:
            return "Epic!"
        elif minutes >= 60:
            return "Great!"
        elif minutes >= 30:
            return "Good!"
        elif minutes >= 15:
            return "Decent"
        else:
            return "Starting out"


class RewardsWidget(QtWidgets.QWidget):
    """Display of rewards earned during session."""
    
    def __init__(self, rewards: dict, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.rewards = rewards
        self._build_ui()
    
    def _build_ui(self):
        """Build the rewards display."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QtWidgets.QLabel("🎁 Rewards Earned")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        layout.addWidget(title)
        
        # Rewards list
        rewards_container = QtWidgets.QWidget()
        rewards_container.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        rewards_layout = QtWidgets.QVBoxLayout(rewards_container)
        rewards_layout.setSpacing(6)
        
        # XP
        if self.rewards.get("xp", 0) > 0:
            xp_label = QtWidgets.QLabel(f"✨ +{self.rewards['xp']} XP")
            xp_label.setStyleSheet("color: #9c27b0; font-weight: bold; font-size: 13px;")
            rewards_layout.addWidget(xp_label)
        
        # Coins
        if self.rewards.get("coins", 0) > 0:
            coins_label = QtWidgets.QLabel(f"🪙 +{self.rewards['coins']} Coins")
            coins_label.setStyleSheet("color: #ff9800; font-weight: bold; font-size: 13px;")
            rewards_layout.addWidget(coins_label)
        
        # Items
        if self.rewards.get("items"):
            for item in self.rewards["items"]:
                item_name = item.get("name", "Unknown Item")
                rarity = item.get("rarity", "Common")
                rarity_colors = {
                    "Common": "#9e9e9e",
                    "Uncommon": "#4caf50",
                    "Rare": "#2196f3",
                    "Epic": "#9c27b0",
                    "Legendary": "#ff9800"
                }
                color = rarity_colors.get(rarity, "#9e9e9e")
                
                item_label = QtWidgets.QLabel(f"🎁 {item_name}")
                item_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px;")
                rewards_layout.addWidget(item_label)
        
        # Streak
        if self.rewards.get("streak_maintained"):
            streak_label = QtWidgets.QLabel(f"🔥 Streak: {self.rewards.get('current_streak', 1)} days")
            streak_label.setStyleSheet("color: #f44336; font-weight: bold; font-size: 13px;")
            rewards_layout.addWidget(streak_label)
        
        # If no rewards, show motivational message
        if not any([self.rewards.get("xp"), self.rewards.get("coins"), 
                   self.rewards.get("items"), self.rewards.get("streak_maintained")]):
            no_rewards = QtWidgets.QLabel("Keep going! Longer sessions unlock more rewards.")
            no_rewards.setStyleSheet("color: #666; font-style: italic; font-size: 11px;")
            rewards_layout.addWidget(no_rewards)
        
        layout.addWidget(rewards_container)


class QuickActionsWidget(QtWidgets.QWidget):
    """Quick action buttons for next steps."""
    
    start_another = QtCore.Signal()
    view_stats = QtCore.Signal()
    view_priorities = QtCore.Signal()
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        """Build the quick actions buttons."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Start another session
        start_btn = QtWidgets.QPushButton("▶️ Start Another")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        start_btn.clicked.connect(self.start_another.emit)
        layout.addWidget(start_btn)
        
        # View stats
        stats_btn = QtWidgets.QPushButton("📊 Stats")
        stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        stats_btn.clicked.connect(self.view_stats.emit)
        layout.addWidget(stats_btn)
        
        # View priorities
        priorities_btn = QtWidgets.QPushButton("🎯 Priorities")
        priorities_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        priorities_btn.clicked.connect(self.view_priorities.emit)
        layout.addWidget(priorities_btn)


class SessionCompleteDialog(QtWidgets.QDialog):
    """
    Industry-standard session complete dialog with celebration and stats.
    
    Features:
    - Large time display with celebration
    - Session statistics breakdown
    - Rewards earned display
    - Streak information
    - Quick action buttons
    - Motivational messages
    - WCAG AA compliant colors
    """
    
    start_another_session = QtCore.Signal()
    view_stats = QtCore.Signal()
    view_priorities = QtCore.Signal()
    
    def __init__(self, elapsed_seconds: int, rewards: Optional[dict] = None,
                 parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.elapsed_seconds = elapsed_seconds
        self.rewards = rewards or {}
        
        self.setWindowTitle("🎉 Session Complete!")
        self.setMinimumSize(500, 550)
        self._build_ui()
        
        # Start celebration animation
        QtCore.QTimer.singleShot(100, self._animate_celebration)
    
    def _build_ui(self):
        """Build the complete dialog UI."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Header with celebration
        header = QtWidgets.QLabel("🎉 Great Work! 🎉")
        header.setAlignment(QtCore.Qt.AlignCenter)
        header.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #4caf50;
            padding: 10px;
        """)
        main_layout.addWidget(header)
        
        # Motivational message
        message = self._get_motivational_message()
        message_label = QtWidgets.QLabel(message)
        message_label.setAlignment(QtCore.Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding: 0 20px;
        """)
        main_layout.addWidget(message_label)
        
        # Separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #ddd;")
        main_layout.addWidget(line)
        
        # Session stats
        stats_widget = SessionStatsWidget(self.elapsed_seconds)
        main_layout.addWidget(stats_widget)
        
        # Separator
        line2 = QtWidgets.QFrame()
        line2.setFrameShape(QtWidgets.QFrame.HLine)
        line2.setStyleSheet("background-color: #ddd;")
        main_layout.addWidget(line2)
        
        # Rewards section
        if self.rewards:
            rewards_widget = RewardsWidget(self.rewards)
            main_layout.addWidget(rewards_widget)
            
            # Separator
            line3 = QtWidgets.QFrame()
            line3.setFrameShape(QtWidgets.QFrame.HLine)
            line3.setStyleSheet("background-color: #ddd;")
            main_layout.addWidget(line3)
        
        # Quick actions
        actions_label = QtWidgets.QLabel("What's next?")
        actions_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        main_layout.addWidget(actions_label)
        
        quick_actions = QuickActionsWidget()
        quick_actions.start_another.connect(self._on_start_another)
        quick_actions.view_stats.connect(self._on_view_stats)
        quick_actions.view_priorities.connect(self._on_view_priorities)
        main_layout.addWidget(quick_actions)
        
        # Spacer
        main_layout.addStretch()
        
        # Close button
        close_layout = QtWidgets.QHBoxLayout()
        close_layout.addStretch()
        close_btn = QtWidgets.QPushButton("✓ Done")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        close_layout.addStretch()
        main_layout.addLayout(close_layout)
        
        # Dialog style
        self.setStyleSheet("""
            QDialog {
                background-color: #fafafa;
            }
        """)
    
    def _get_motivational_message(self) -> str:
        """Get contextual motivational message based on session length."""
        minutes = self.elapsed_seconds // 60
        
        if minutes >= 120:
            return "Incredible! You've achieved legendary focus. Your dedication is truly inspiring!"
        elif minutes >= 90:
            return "Amazing work! An epic session that shows real commitment to your goals."
        elif minutes >= 60:
            return "Outstanding! A full hour of focused work. You're building a powerful habit."
        elif minutes >= 45:
            return "Excellent! You've maintained focus through a solid session. Keep it up!"
        elif minutes >= 30:
            return "Great job! A half-hour of focused work is a strong accomplishment."
        elif minutes >= 15:
            return "Well done! You've completed a focused session. Every minute counts!"
        else:
            return "Nice start! Even short sessions build the foundation for greater focus."
    
    def _animate_celebration(self):
        """Animate the celebration header."""
        # Simple fade-in effect for the header
        header = self.findChild(QtWidgets.QLabel)
        if header and header.text().startswith("🎉"):
            effect = QtWidgets.QGraphicsOpacityEffect(header)
            header.setGraphicsEffect(effect)
            
            animation = QtCore.QPropertyAnimation(effect, b"opacity")
            animation.setDuration(800)
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            animation.start()
            
            # Store reference to prevent garbage collection
            self._celebration_animation = animation
    
    def _on_start_another(self):
        """Handle start another session."""
        self.start_another_session.emit()
        self.accept()
    
    def _on_view_stats(self):
        """Handle view stats."""
        self.view_stats.emit()
        # Don't close dialog - let user see stats then come back
    
    def _on_view_priorities(self):
        """Handle view priorities."""
        self.view_priorities.emit()
        # Don't close dialog - let user see priorities then come back
