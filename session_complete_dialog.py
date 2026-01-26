"""
Session Complete Dialog - Styled Frameless Design
==================================================
Celebratory dialog shown when a focus session completes successfully.
Uses the app's StyledDialog base class for consistent look and feel.
Features visual feedback, stats breakdown, rewards, and quick actions.
"""

from datetime import datetime, timedelta
from typing import Optional
from PySide6 import QtWidgets, QtCore, QtGui

from styled_dialog import StyledDialog

try:
    from gamification import GAMIFICATION_AVAILABLE, ITEM_RARITIES
except ImportError:
    GAMIFICATION_AVAILABLE = False
    ITEM_RARITIES = {}


class SessionCompleteDialog(StyledDialog):
    """
    Styled session complete dialog with celebration and stats.
    
    Features:
    - Frameless dark themed design matching app style
    - Large time display with celebration
    - Session statistics breakdown
    - Rewards earned display
    - Streak information
    - Quick action buttons
    - Motivational messages
    """
    
    start_another_session = QtCore.Signal()
    view_stats = QtCore.Signal()
    view_priorities = QtCore.Signal()
    
    def __init__(self, elapsed_seconds: int, rewards: Optional[dict] = None,
                 parent: Optional[QtWidgets.QWidget] = None):
        self.elapsed_seconds = max(0, elapsed_seconds)  # Ensure non-negative
        self.rewards = rewards or {}
        
        super().__init__(
            parent=parent,
            title="Session Complete!",
            header_icon="🎉",
            min_width=480,
            max_width=550,
            modal=True,
        )
        
        # Start celebration animation
        QtCore.QTimer.singleShot(100, self._animate_celebration)
    
    def _build_content(self, layout: QtWidgets.QVBoxLayout):
        """Build the complete dialog content."""
        # Motivational message
        message = self._get_motivational_message()
        message_label = QtWidgets.QLabel(message)
        message_label.setAlignment(QtCore.Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            font-size: 13px;
            color: #888888;
            padding: 0 10px 10px 10px;
        """)
        layout.addWidget(message_label)
        
        # Separator
        self._add_separator(layout)
        
        # Time display - large and prominent
        time_display = self._format_time(self.elapsed_seconds)
        time_label = QtWidgets.QLabel(time_display)
        time_label.setObjectName("timeDisplay")
        time_label.setAlignment(QtCore.Qt.AlignCenter)
        time_label.setStyleSheet("""
            font-size: 56px;
            font-weight: bold;
            color: #4CAF50;
            padding: 15px;
        """)
        layout.addWidget(time_label)
        
        # Stats grid
        stats_widget = self._build_stats_widget()
        layout.addWidget(stats_widget)
        
        # Separator
        self._add_separator(layout)
        
        # Rewards section
        if self.rewards:
            rewards_widget = self._build_rewards_widget()
            layout.addWidget(rewards_widget)
            self._add_separator(layout)
        
        # Quick actions section
        actions_label = QtWidgets.QLabel("What's next?")
        actions_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #FFD700;")
        layout.addWidget(actions_label)
        
        quick_actions = self._build_quick_actions()
        layout.addWidget(quick_actions)
        
        # Spacer
        layout.addStretch()
        
        # Done button using button row helper
        self.add_button_row(layout, [
            ("✓ Done", "secondary", self.accept),
        ])
    
    def _add_separator(self, layout: QtWidgets.QVBoxLayout):
        """Add a styled separator line."""
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #333344; max-height: 1px;")
        layout.addWidget(line)
    
    def _build_stats_widget(self) -> QtWidgets.QWidget:
        """Build the stats display grid."""
        stats_widget = QtWidgets.QWidget()
        grid_layout = QtWidgets.QGridLayout(stats_widget)
        grid_layout.setSpacing(16)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        
        minutes = self.elapsed_seconds // 60
        time_display = self._format_time(self.elapsed_seconds)
        
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
            label_widget.setStyleSheet("color: #888888; font-size: 11px;")
            text_layout.addWidget(label_widget)
            
            value_widget = QtWidgets.QLabel(value)
            value_widget.setStyleSheet("font-weight: bold; font-size: 14px; color: #E0E0E0;")
            text_layout.addWidget(value_widget)
            
            grid_layout.addWidget(text_widget, row, col + 1)
        
        return stats_widget
    
    def _build_rewards_widget(self) -> QtWidgets.QWidget:
        """Build the rewards display."""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QtWidgets.QLabel("🎁 Rewards Earned")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFD700;")
        layout.addWidget(title)
        
        # Rewards container
        rewards_box = QtWidgets.QWidget()
        rewards_box.setStyleSheet("""
            QWidget {
                background-color: rgba(26, 26, 46, 0.7);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        rewards_layout = QtWidgets.QVBoxLayout(rewards_box)
        rewards_layout.setSpacing(6)
        rewards_layout.setContentsMargins(12, 12, 12, 12)
        
        # XP with city bonus breakdown
        if self.rewards.get("xp", 0) > 0:
            city_xp_bonus = self.rewards.get("city_xp_bonus", 0)
            if city_xp_bonus > 0:
                base_xp = self.rewards['xp'] - city_xp_bonus
                xp_label = QtWidgets.QLabel(f"✨ +{self.rewards['xp']} XP ({base_xp} + 📚 Library {city_xp_bonus})")
            else:
                xp_label = QtWidgets.QLabel(f"✨ +{self.rewards['xp']} XP")
            xp_label.setStyleSheet("color: #9c27b0; font-weight: bold; font-size: 13px;")
            rewards_layout.addWidget(xp_label)
        
        # Coins
        if self.rewards.get("coins", 0) > 0:
            coins_label = QtWidgets.QLabel(f"🪙 +{self.rewards['coins']} Coins")
            coins_label.setStyleSheet("color: #ff9800; font-weight: bold; font-size: 13px;")
            rewards_layout.addWidget(coins_label)
        
        # Items - just show teaser, lottery animation will reveal the actual item
        if self.rewards.get("items"):
            item_label = QtWidgets.QLabel("🎁 Item incoming... (lottery next!)")
            item_label.setStyleSheet("color: #FFD700; font-weight: bold; font-size: 13px; font-style: italic;")
            rewards_layout.addWidget(item_label)
        
        # Streak
        if self.rewards.get("streak_maintained"):
            streak_label = QtWidgets.QLabel(f"🔥 Streak: {self.rewards.get('current_streak', 1)} days")
            streak_label.setStyleSheet("color: #f44336; font-weight: bold; font-size: 13px;")
            rewards_layout.addWidget(streak_label)
        
        # City construction contribution preview
        city_construction = self.rewards.get("city_construction")
        if city_construction:
            building_name = city_construction.get("building_name", "Building")
            focus_earned = city_construction.get("focus_earned", 0)
            current_progress = city_construction.get("current_progress", 0)
            mins_needed = city_construction.get("mins_needed", 0)
            
            if focus_earned > 0:
                construction_label = QtWidgets.QLabel(
                    f"🏗️ +{focus_earned} Focus → {building_name} ({current_progress:.0f}%)"
                )
                construction_label.setStyleSheet("color: #7FDBFF; font-weight: bold; font-size: 13px;")
            elif mins_needed > 0:
                construction_label = QtWidgets.QLabel(
                    f"🏗️ {mins_needed} more min → +1 Focus for {building_name}"
                )
                construction_label.setStyleSheet("color: #888888; font-size: 12px;")
            else:
                construction_label = None
            
            if construction_label:
                rewards_layout.addWidget(construction_label)
        
        # Entity Perks Applied (show which entity bonuses contributed)
        entity_perks = self.rewards.get("entity_perks_applied", [])
        if entity_perks:
            perks_label = QtWidgets.QLabel("🐾 Entity Perks Active:")
            perks_label.setStyleSheet("color: #7FDBFF; font-weight: bold; font-size: 11px; margin-top: 6px;")
            rewards_layout.addWidget(perks_label)
            
            for perk in entity_perks[:3]:  # Show max 3 perks to avoid clutter
                perk_text = perk.get("description", "Entity Bonus")
                perk_item = QtWidgets.QLabel(f"  • {perk_text}")
                perk_item.setStyleSheet("color: #888; font-size: 10px;")
                rewards_layout.addWidget(perk_item)
            
            if len(entity_perks) > 3:
                more_label = QtWidgets.QLabel(f"  ...and {len(entity_perks) - 3} more bonuses")
                more_label.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
                rewards_layout.addWidget(more_label)
        
        # If no rewards, show motivational message
        if not any([self.rewards.get("xp"), self.rewards.get("coins"), 
                   self.rewards.get("items"), self.rewards.get("streak_maintained")]):
            no_rewards = QtWidgets.QLabel("Keep going! Longer sessions unlock more rewards.")
            no_rewards.setStyleSheet("color: #888888; font-style: italic; font-size: 11px;")
            rewards_layout.addWidget(no_rewards)
        
        layout.addWidget(rewards_box)
        return container
    
    def _build_quick_actions(self) -> QtWidgets.QWidget:
        """Build the quick action buttons."""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Start another session
        start_btn = QtWidgets.QPushButton("▶ Start Another")
        start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #388E3C);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5CBF60, stop:1 #43A047);
            }
        """)
        start_btn.clicked.connect(self._on_start_another)
        layout.addWidget(start_btn)
        
        # View stats
        stats_btn = QtWidgets.QPushButton("📊 Stats")
        stats_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42A5F5, stop:1 #2196F3);
            }
        """)
        stats_btn.clicked.connect(self._on_view_stats)
        layout.addWidget(stats_btn)
        
        # View priorities
        priorities_btn = QtWidgets.QPushButton("🎯 Priorities")
        priorities_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF9800, stop:1 #F57C00);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFB74D, stop:1 #FF9800);
            }
        """)
        priorities_btn.clicked.connect(self._on_view_priorities)
        layout.addWidget(priorities_btn)
        
        return container
    
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
        """Animate the time display with a pulse effect."""
        time_label = self.findChild(QtWidgets.QLabel, "timeDisplay")
        if time_label:
            effect = QtWidgets.QGraphicsOpacityEffect(time_label)
            time_label.setGraphicsEffect(effect)
            
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
    
    def closeEvent(self, event):
        """Clean up animations on close."""
        if hasattr(self, '_celebration_animation'):
            self._celebration_animation.stop()
        super().closeEvent(event)
