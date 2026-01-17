import sys
import json
import random
import platform
import copy
import math
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

try:
    from __version__ import __version__ as APP_VERSION
except ImportError:
    APP_VERSION = "3.1.4"

# Import game state manager for reactive UI updates (required)
from game_state import GameStateManager, init_game_state, get_game_state
from eye_protection_tab import EyeProtectionTab
from entitidex_tab import EntitidexTab

# Hide console window on Windows
if platform.system() == "Windows":
    import ctypes
    try:
        # ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        pass
    except Exception:
        pass

from PySide6 import QtCore, QtGui, QtWidgets

# Import enhanced dialogs
from item_drop_dialog import EnhancedItemDropDialog
from level_up_dialog import EnhancedLevelUpDialog
from emergency_cleanup_dialog import EmergencyCleanupDialog, show_emergency_cleanup_dialog


# ============================================================================
# Silent Message Box Helper (no system sound)
# ============================================================================

def show_message(parent, title: str, text: str, icon: QtWidgets.QMessageBox.Icon = QtWidgets.QMessageBox.Information) -> int:
    """Show a message box without playing the system sound."""
    msg = QtWidgets.QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(icon)
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    # Disable the alert sound by setting the window flag
    msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)
    # Alternative: use custom event filter or just show without sound
    msg.setOption(QtWidgets.QMessageBox.Option.DontUseNativeDialog, True)
    return msg.exec()


def show_info(parent, title: str, text: str) -> int:
    """Show an information message box without sound."""
    return show_message(parent, title, text, QtWidgets.QMessageBox.Information)


def show_warning(parent, title: str, text: str) -> int:
    """Show a warning message box without sound."""
    return show_message(parent, title, text, QtWidgets.QMessageBox.Warning)


def show_error(parent, title: str, text: str) -> int:
    """Show an error/critical message box without sound."""
    return show_message(parent, title, text, QtWidgets.QMessageBox.Critical)


def show_question(parent, title: str, text: str, 
                  buttons: QtWidgets.QMessageBox.StandardButtons = QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                  default_button: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.No) -> int:
    """Show a question message box with Yes/No buttons without sound."""
    msg = QtWidgets.QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(QtWidgets.QMessageBox.NoIcon)  # NoIcon = no sound
    msg.setStandardButtons(buttons)
    msg.setDefaultButton(default_button)
    msg.setOption(QtWidgets.QMessageBox.Option.DontUseNativeDialog, True)
    return msg.exec()


# ============================================================================
# Entity Perk Toast Notification - Non-blocking feedback when perks activate
# ============================================================================

class PerkToast(QtWidgets.QWidget):
    """
    A non-blocking toast notification for entity perk activation.
    
    Shows a brief message that fades in and out automatically.
    Used to provide visual feedback when entity perks affect gameplay.
    """
    
    _active_toasts = []  # Track active toasts for stacking
    
    def __init__(self, message: str, icon: str = "✨", duration_ms: int = 2500,
                 parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.Tool |
            QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Create layout
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Icon
        icon_label = QtWidgets.QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_label)
        
        # Message
        msg_label = QtWidgets.QLabel(message)
        msg_label.setStyleSheet("""
            color: #fff;
            font-size: 13px;
            font-weight: bold;
        """)
        layout.addWidget(msg_label)
        
        # Container styling
        self.setStyleSheet("""
            PerkToast {
                background-color: rgba(139, 92, 246, 0.95);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        # Animation setup
        self.opacity = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        
        self.fade_in = QtCore.QPropertyAnimation(self.opacity, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        
        self.fade_out = QtCore.QPropertyAnimation(self.opacity, b"opacity")
        self.fade_out.setDuration(400)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.finished.connect(self._on_finished)
        
        # Timer for auto-dismiss
        self.dismiss_timer = QtCore.QTimer()
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self._start_fade_out)
        self.dismiss_timer.setInterval(duration_ms)
        
    def show_at_bottom_right(self, parent: Optional[QtWidgets.QWidget] = None):
        """Show the toast at bottom-right of parent or screen."""
        self.adjustSize()
        
        # Calculate position
        if parent:
            parent_rect = parent.geometry()
            screen_pos = parent.mapToGlobal(QtCore.QPoint(0, 0))
            x = screen_pos.x() + parent_rect.width() - self.width() - 20
            y = screen_pos.y() + parent_rect.height() - self.height() - 20
        else:
            screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
            x = screen.right() - self.width() - 20
            y = screen.bottom() - self.height() - 20
        
        # Stack below other active toasts
        offset = len(PerkToast._active_toasts) * 50
        y -= offset
        
        self.move(x, y)
        PerkToast._active_toasts.append(self)
        
        self.show()
        self.fade_in.start()
        self.dismiss_timer.start()
        
    def _start_fade_out(self):
        self.fade_out.start()
        
    def _on_finished(self):
        if self in PerkToast._active_toasts:
            PerkToast._active_toasts.remove(self)
        self.close()
        self.deleteLater()


def show_perk_toast(message: str, icon: str = "✨", parent: QtWidgets.QWidget = None):
    """
    Show a non-blocking toast notification for perk activation.
    
    Args:
        message: The perk effect message (e.g., "Saved 1 coin!")
        icon: Emoji icon to display
        parent: Parent widget for positioning
    """
    toast = PerkToast(message, icon, parent=parent)
    toast.show_at_bottom_right(parent)


# ============================================================================
# No-Scroll ComboBox - Prevents accidental changes via scroll wheel
# ============================================================================

class NoScrollComboBox(QtWidgets.QComboBox):
    """
    A QComboBox that ignores scroll wheel events.
    
    This prevents users from accidentally changing dropdown values
    while scrolling through the application.
    """
    
    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """Ignore scroll wheel events to prevent accidental changes."""
        event.ignore()


class SplashScreen(QtWidgets.QWidget):
    """Splash screen shown during application startup."""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.SplashScreen
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Container with rounded corners
        container = QtWidgets.QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-radius: 15px;
                border: 2px solid #4a4a6a;
            }
        """)
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(50, 30, 50, 30)
        container_layout.setSpacing(15)
        
        # App icon/title
        title_label = QtWidgets.QLabel("� Personal Liberty")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title_label)
        
        # Version
        version_label = QtWidgets.QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                background: transparent;
                border: none;
            }
        """)
        version_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(version_label)
        
        container_layout.addSpacing(10)
        
        # Status message
        self.status_label = QtWidgets.QLabel("Loading...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 13px;
                background: transparent;
                border: none;
            }
        """)
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a4a;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #6366f1;
                border-radius: 3px;
            }
        """)
        container_layout.addWidget(self.progress)
        
        # Tip message
        tips = [
            "💡 Tip: Use the AI tab for personalized productivity insights",
            "💡 Tip: Enable Hardcore mode for extra commitment",
            "💡 Tip: Set up schedules to block automatically",
            "💡 Tip: Track your progress in the Statistics tab",
            "💡 Tip: Add custom sites to block in Settings",
        ]
        tip_label = QtWidgets.QLabel(random.choice(tips))
        tip_label.setStyleSheet("""
            QLabel {
                color: #666688;
                font-size: 11px;
                font-style: italic;
                background: transparent;
                border: none;
            }
        """)
        tip_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        tip_label.setWordWrap(True)
        container_layout.addWidget(tip_label)
        
        layout.addWidget(container)
        
        # Set size and center on screen
        self.setFixedSize(380, 200)
        self.center_on_screen()
    
    def center_on_screen(self):
        """Center the splash screen on the primary screen."""
        screen = QtWidgets.QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(screen_geometry.x() + x, screen_geometry.y() + y)
    
    def set_status(self, message: str):
        """Update the status message."""
        self.status_label.setText(message)
        QtWidgets.QApplication.processEvents()


# Module-level variables for deferred imports (initialized in load_heavy_modules)
BlockerCore = None
BlockMode = None
SITE_CATEGORIES = None
AI_AVAILABLE = False
GOALS_PATH = None
STATS_PATH = None
BYPASS_LOGGER_AVAILABLE = False
ProductivityAnalyzer = None
GamificationEngine = None
FocusGoals = None
GAMIFICATION_AVAILABLE = False
RARITY_POWER = {"Common": 10, "Uncommon": 25, "Rare": 50, "Epic": 100, "Legendary": 250}
ITEM_THEMES = None
get_item_themes = None
get_diary_power_tier = None
calculate_character_power = None
get_power_breakdown = None
calculate_rarity_bonuses = None
calculate_merge_success_rate = None
get_merge_result_rarity = None
perform_lucky_merge = None
is_merge_worthwhile = None
generate_diary_entry = None
calculate_set_bonuses = None
generate_item = None
generate_daily_reward_item = None
get_current_tier = None
get_boosted_rarity = None
AVAILABLE_STORIES = {}
STORY_MODE_ACTIVE = "story"
STORY_MODE_HERO_ONLY = "hero_only"
STORY_MODE_DISABLED = "disabled"
set_story_mode = None
get_story_mode = None
switch_story = None
ensure_hero_structure = None
sync_hero_data = None
is_gamification_enabled = lambda adhd_buster: False
# Story gear theme helpers
GEAR_SLOTS = ["Helmet", "Chestplate", "Gauntlets", "Boots", "Shield", "Weapon", "Cloak", "Amulet"]
STORY_GEAR_THEMES = {}
get_story_gear_theme = None
get_slot_display_name = None
# Gear optimization
optimize_equipped_gear = None
find_potential_set_bonuses = None
# Lucky options system
calculate_total_lucky_bonuses = None
format_lucky_options = None
# Entity power perks for hero display
get_entity_power_perks = None
# XP and leveling system
calculate_session_xp = None
award_xp = None
get_level_from_xp = None
get_level_title = None
get_celebration_message = None
# Weight tracking functions
check_weight_entry_rewards = None
get_weight_stats = None
format_weight_change = None
check_all_weight_rewards = None
calculate_bmi = None
get_bmi_classification = None
get_ideal_weight_range = None
predict_goal_date = None
get_historical_comparisons = None
get_weekly_insights = None
WEIGHT_ENTRY_TAGS = []
format_entry_note = None
# Activity tracking functions
ACTIVITY_TYPES = []
INTENSITY_LEVELS = []
ACTIVITY_MIN_DURATION = 10
check_all_activity_rewards = None
get_activity_stats = None
format_activity_duration = None
check_activity_streak = None
# Sleep tracking functions
SLEEP_CHRONOTYPES = []
SLEEP_QUALITY_FACTORS = []
SLEEP_DISRUPTION_TAGS = []
check_all_sleep_rewards = None
get_sleep_stats = None
format_sleep_duration = None
check_sleep_streak = None
get_sleep_recommendation = None
get_screen_off_bonus_rarity = None
# Hydration tracking functions
get_water_reward_rarity = None
can_log_water = None
get_hydration_streak_bonus_rarity = None
check_water_entry_reward = None
get_hydration_stats = None
HYDRATION_MIN_INTERVAL_HOURS = 2
HYDRATION_MAX_DAILY_GLASSES = 5


def load_heavy_modules(splash: Optional[SplashScreen] = None):
    """Load heavy modules with splash screen updates."""
    global BlockerCore, BlockMode, SITE_CATEGORIES, AI_AVAILABLE
    global GOALS_PATH, STATS_PATH, BYPASS_LOGGER_AVAILABLE
    global ProductivityAnalyzer, GamificationEngine, FocusGoals
    global GAMIFICATION_AVAILABLE, RARITY_POWER, ITEM_THEMES, get_item_themes
    global get_diary_power_tier, calculate_character_power, get_power_breakdown
    global calculate_rarity_bonuses, calculate_merge_success_rate, get_merge_result_rarity
    global perform_lucky_merge, is_merge_worthwhile, generate_diary_entry
    global calculate_set_bonuses, generate_item, generate_daily_reward_item
    global get_current_tier, get_boosted_rarity, AVAILABLE_STORIES
    global STORY_MODE_ACTIVE, STORY_MODE_HERO_ONLY, STORY_MODE_DISABLED
    global set_story_mode, get_story_mode, switch_story, ensure_hero_structure
    global sync_hero_data, is_gamification_enabled
    global GEAR_SLOTS, STORY_GEAR_THEMES, get_story_gear_theme, get_slot_display_name
    global optimize_equipped_gear, find_potential_set_bonuses
    global calculate_total_lucky_bonuses, format_lucky_options, get_entity_power_perks
    global calculate_session_xp, award_xp, get_level_from_xp, get_level_title, get_celebration_message
    # Weight tracking
    global check_weight_entry_rewards, get_weight_stats, format_weight_change, check_all_weight_rewards
    global calculate_bmi, get_bmi_classification, get_ideal_weight_range
    global predict_goal_date, get_historical_comparisons, get_weekly_insights
    global WEIGHT_ENTRY_TAGS, format_entry_note
    # Activity tracking
    global ACTIVITY_TYPES, INTENSITY_LEVELS, ACTIVITY_MIN_DURATION
    global check_all_activity_rewards, get_activity_stats, format_activity_duration, check_activity_streak
    # Sleep tracking
    global SLEEP_CHRONOTYPES, SLEEP_QUALITY_FACTORS, SLEEP_DISRUPTION_TAGS
    global check_all_sleep_rewards, get_sleep_stats, format_sleep_duration
    global check_sleep_streak, get_sleep_recommendation, get_screen_off_bonus_rarity
    # Hydration tracking
    global get_water_reward_rarity, can_log_water
    global get_hydration_streak_bonus_rarity, check_water_entry_reward, get_hydration_stats
    global HYDRATION_MIN_INTERVAL_HOURS, HYDRATION_MAX_DAILY_GLASSES
    
    if splash:
        splash.set_status("Loading core modules...")
    
    from core_logic import (
        BlockerCore as _BlockerCore,
        BlockMode as _BlockMode,
        SITE_CATEGORIES as _SITE_CATEGORIES,
        AI_AVAILABLE as _AI_AVAILABLE,
        GOALS_PATH as _GOALS_PATH,
        STATS_PATH as _STATS_PATH,
        BYPASS_LOGGER_AVAILABLE as _BYPASS_LOGGER_AVAILABLE,
        APP_DIR as _APP_DIR,
    )
    BlockerCore = _BlockerCore
    BlockMode = _BlockMode
    SITE_CATEGORIES = _SITE_CATEGORIES
    AI_AVAILABLE = _AI_AVAILABLE
    GOALS_PATH = _GOALS_PATH
    STATS_PATH = _STATS_PATH
    BYPASS_LOGGER_AVAILABLE = _BYPASS_LOGGER_AVAILABLE
    APP_DIR = _APP_DIR
    
    # AI helpers (guarded for optional dependency)
    if AI_AVAILABLE:
        if splash:
            splash.set_status("Loading AI features...")
        try:
            from productivity_ai import (
                ProductivityAnalyzer as _ProductivityAnalyzer,
                GamificationEngine as _GamificationEngine,
                FocusGoals as _FocusGoals
            )
            ProductivityAnalyzer = _ProductivityAnalyzer
            GamificationEngine = _GamificationEngine
            FocusGoals = _FocusGoals
        except Exception:
            pass
    
    # Gamification imports
    if splash:
        splash.set_status("Loading gamification...")
    try:
        from gamification import (
            RARITY_POWER as _RARITY_POWER,
            ITEM_THEMES as _ITEM_THEMES,
            get_item_themes as _get_item_themes,
            get_diary_power_tier as _get_diary_power_tier,
            calculate_character_power as _calculate_character_power,
            # XP and leveling system
            calculate_session_xp as _calculate_session_xp,
            award_xp as _award_xp,
            get_level_from_xp as _get_level_from_xp,
            get_level_title as _get_level_title,
            get_celebration_message as _get_celebration_message,
            get_power_breakdown as _get_power_breakdown,
            calculate_rarity_bonuses as _calculate_rarity_bonuses,
            calculate_merge_success_rate as _calculate_merge_success_rate,
            get_merge_result_rarity as _get_merge_result_rarity,
            perform_lucky_merge as _perform_lucky_merge,
            is_merge_worthwhile as _is_merge_worthwhile,
            generate_diary_entry as _generate_diary_entry,
            calculate_set_bonuses as _calculate_set_bonuses,
            generate_item as _generate_item,
            generate_daily_reward_item as _generate_daily_reward_item,
            get_current_tier as _get_current_tier,
            get_boosted_rarity as _get_boosted_rarity,
            AVAILABLE_STORIES as _AVAILABLE_STORIES,
            STORY_MODE_ACTIVE as _STORY_MODE_ACTIVE,
            STORY_MODE_HERO_ONLY as _STORY_MODE_HERO_ONLY,
            STORY_MODE_DISABLED as _STORY_MODE_DISABLED,
            set_story_mode as _set_story_mode,
            get_story_mode as _get_story_mode,
            switch_story as _switch_story,
            ensure_hero_structure as _ensure_hero_structure,
            sync_hero_data as _sync_hero_data,
            is_gamification_enabled as _is_gamification_enabled,
            # Story gear theme helpers
            GEAR_SLOTS as _GEAR_SLOTS,
            STORY_GEAR_THEMES as _STORY_GEAR_THEMES,
            get_story_gear_theme as _get_story_gear_theme,
            get_slot_display_name as _get_slot_display_name,
            # Gear optimization
            optimize_equipped_gear as _optimize_equipped_gear,
            find_potential_set_bonuses as _find_potential_set_bonuses,
            # Lucky options system
            calculate_total_lucky_bonuses as _calculate_total_lucky_bonuses,
            format_lucky_options as _format_lucky_options,
            # Entity power perks for hero display
            get_entity_power_perks as _get_entity_power_perks,
        )
        GAMIFICATION_AVAILABLE = True
        RARITY_POWER = _RARITY_POWER
        ITEM_THEMES = _ITEM_THEMES
        get_item_themes = _get_item_themes
        get_diary_power_tier = _get_diary_power_tier
        calculate_character_power = _calculate_character_power
        # XP and leveling system
        calculate_session_xp = _calculate_session_xp
        award_xp = _award_xp
        get_level_from_xp = _get_level_from_xp
        get_level_title = _get_level_title
        get_celebration_message = _get_celebration_message
        get_power_breakdown = _get_power_breakdown
        calculate_rarity_bonuses = _calculate_rarity_bonuses
        calculate_merge_success_rate = _calculate_merge_success_rate
        get_merge_result_rarity = _get_merge_result_rarity
        perform_lucky_merge = _perform_lucky_merge
        is_merge_worthwhile = _is_merge_worthwhile
        generate_diary_entry = _generate_diary_entry
        calculate_set_bonuses = _calculate_set_bonuses
        generate_item = _generate_item
        generate_daily_reward_item = _generate_daily_reward_item
        get_current_tier = _get_current_tier
        get_boosted_rarity = _get_boosted_rarity
        AVAILABLE_STORIES = _AVAILABLE_STORIES
        STORY_MODE_ACTIVE = _STORY_MODE_ACTIVE
        STORY_MODE_HERO_ONLY = _STORY_MODE_HERO_ONLY
        STORY_MODE_DISABLED = _STORY_MODE_DISABLED
        set_story_mode = _set_story_mode
        get_story_mode = _get_story_mode
        switch_story = _switch_story
        ensure_hero_structure = _ensure_hero_structure
        sync_hero_data = _sync_hero_data
        is_gamification_enabled = _is_gamification_enabled
        # Story gear theme helpers
        GEAR_SLOTS = _GEAR_SLOTS
        STORY_GEAR_THEMES = _STORY_GEAR_THEMES
        get_story_gear_theme = _get_story_gear_theme
        get_slot_display_name = _get_slot_display_name
        # Gear optimization
        optimize_equipped_gear = _optimize_equipped_gear
        find_potential_set_bonuses = _find_potential_set_bonuses
        # Lucky options system
        calculate_total_lucky_bonuses = _calculate_total_lucky_bonuses
        format_lucky_options = _format_lucky_options
        # Entity power perks for hero display
        get_entity_power_perks = _get_entity_power_perks
    except ImportError:
        GAMIFICATION_AVAILABLE = False
    
    # Weight tracking functions (separate try for backward compat)
    try:
        from gamification import (
            check_weight_entry_rewards as _check_weight_entry_rewards,
            get_weight_stats as _get_weight_stats,
            format_weight_change as _format_weight_change,
            check_all_weight_rewards as _check_all_weight_rewards,
            calculate_bmi as _calculate_bmi,
            get_bmi_classification as _get_bmi_classification,
            get_ideal_weight_range as _get_ideal_weight_range,
            predict_goal_date as _predict_goal_date,
            get_historical_comparisons as _get_historical_comparisons,
            get_weekly_insights as _get_weekly_insights,
            WEIGHT_ENTRY_TAGS as _WEIGHT_ENTRY_TAGS,
            format_entry_note as _format_entry_note,
        )
        check_weight_entry_rewards = _check_weight_entry_rewards
        get_weight_stats = _get_weight_stats
        format_weight_change = _format_weight_change
        check_all_weight_rewards = _check_all_weight_rewards
        calculate_bmi = _calculate_bmi
        get_bmi_classification = _get_bmi_classification
        get_ideal_weight_range = _get_ideal_weight_range
        predict_goal_date = _predict_goal_date
        get_historical_comparisons = _get_historical_comparisons
        get_weekly_insights = _get_weekly_insights
        WEIGHT_ENTRY_TAGS = _WEIGHT_ENTRY_TAGS
        format_entry_note = _format_entry_note
    except ImportError:
        pass
    
    # Activity tracking functions
    try:
        from gamification import (
            ACTIVITY_TYPES as _ACTIVITY_TYPES,
            INTENSITY_LEVELS as _INTENSITY_LEVELS,
            ACTIVITY_MIN_DURATION as _ACTIVITY_MIN_DURATION,
            check_all_activity_rewards as _check_all_activity_rewards,
            get_activity_stats as _get_activity_stats,
            format_activity_duration as _format_activity_duration,
            check_activity_streak as _check_activity_streak,
        )
        ACTIVITY_TYPES = _ACTIVITY_TYPES
        INTENSITY_LEVELS = _INTENSITY_LEVELS
        ACTIVITY_MIN_DURATION = _ACTIVITY_MIN_DURATION
        check_all_activity_rewards = _check_all_activity_rewards
        get_activity_stats = _get_activity_stats
        format_activity_duration = _format_activity_duration
        check_activity_streak = _check_activity_streak
    except ImportError:
        pass
    
    # Sleep tracking functions
    try:
        from gamification import (
            SLEEP_CHRONOTYPES as _SLEEP_CHRONOTYPES,
            SLEEP_QUALITY_FACTORS as _SLEEP_QUALITY_FACTORS,
            SLEEP_DISRUPTION_TAGS as _SLEEP_DISRUPTION_TAGS,
            check_all_sleep_rewards as _check_all_sleep_rewards,
            get_sleep_stats as _get_sleep_stats,
            format_sleep_duration as _format_sleep_duration,
            check_sleep_streak as _check_sleep_streak,
            get_sleep_recommendation as _get_sleep_recommendation,
            get_screen_off_bonus_rarity as _get_screen_off_bonus_rarity,
        )
        SLEEP_CHRONOTYPES = _SLEEP_CHRONOTYPES
        SLEEP_QUALITY_FACTORS = _SLEEP_QUALITY_FACTORS
        SLEEP_DISRUPTION_TAGS = _SLEEP_DISRUPTION_TAGS
        check_all_sleep_rewards = _check_all_sleep_rewards
        get_sleep_stats = _get_sleep_stats
        format_sleep_duration = _format_sleep_duration
        check_sleep_streak = _check_sleep_streak
        get_sleep_recommendation = _get_sleep_recommendation
        get_screen_off_bonus_rarity = _get_screen_off_bonus_rarity
    except ImportError:
        pass
    
    # Hydration tracking functions
    try:
        from gamification import (
            get_water_reward_rarity as _get_water_reward_rarity,
            can_log_water as _can_log_water,
            get_hydration_streak_bonus_rarity as _get_hydration_streak_bonus_rarity,
            check_water_entry_reward as _check_water_entry_reward,
            get_hydration_stats as _get_hydration_stats,
            HYDRATION_MIN_INTERVAL_HOURS as _HYDRATION_MIN_INTERVAL_HOURS,
            HYDRATION_MAX_DAILY_GLASSES as _HYDRATION_MAX_DAILY_GLASSES,
        )
        get_water_reward_rarity = _get_water_reward_rarity
        can_log_water = _can_log_water
        get_hydration_streak_bonus_rarity = _get_hydration_streak_bonus_rarity
        check_water_entry_reward = _check_water_entry_reward
        get_hydration_stats = _get_hydration_stats
        HYDRATION_MIN_INTERVAL_HOURS = _HYDRATION_MIN_INTERVAL_HOURS
        HYDRATION_MAX_DAILY_GLASSES = _HYDRATION_MAX_DAILY_GLASSES
    except ImportError:
        pass
    
    if splash:
        splash.set_status("Initializing interface...")

# Single instance mutex name
MUTEX_NAME = "PersonalLiberty_SingleInstance_Mutex"


class HardcoreChallengeDialog(QtWidgets.QDialog):
    """
    Math challenge dialog for Hardcore mode.
    Requires solving two long number arithmetic problems to stop the session.
    Numbers are rendered as non-selectable images to prevent copy-paste.
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("💪 Hardcore Challenge")
        self.setModal(True)
        self.setMinimumWidth(580)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        
        # Generate two different math problems
        self.problems = self._generate_problems()
        self.current_problem = 0
        self.solved_count = 0
        self._ready_to_finish = False
        
        self._build_ui()
        self._show_current_problem()
    
    def _generate_problems(self) -> list:
        """Generate two challenging math problems with large numbers."""
        problems = []
        operations = ['+', '-', '×']
        
        for _ in range(2):
            op = random.choice(operations)
            
            if op == '+':
                # Addition: two 5-digit numbers
                a = random.randint(10000, 99999)
                b = random.randint(10000, 99999)
                answer = a + b
            elif op == '-':
                # Subtraction: ensure positive result
                a = random.randint(50000, 99999)
                b = random.randint(10000, a - 1)
                answer = a - b
            else:  # ×
                # Multiplication: 4-digit × 2-digit
                a = random.randint(1000, 9999)
                b = random.randint(10, 99)
                answer = a * b
            
            problems.append({
                'a': a,
                'b': b,
                'op': op,
                'answer': answer
            })
        
        return problems
    
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Warning header
        header = QtWidgets.QLabel("⚠️ HARDCORE MODE ACTIVE ⚠️")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #dc3545;
            padding: 10px;
        """)
        header.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(header)
        
        # Instructions
        instructions = QtWidgets.QLabel(
            "To stop this session, you must solve 2 math problems.\n"
            "Type your answers manually - no shortcuts allowed!"
        )
        instructions.setStyleSheet("font-size: 12px; color: #666;")
        instructions.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(instructions)
        
        # Progress indicator
        self.progress_label = QtWidgets.QLabel()
        self.progress_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.progress_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.progress_label)
        
        # Problem display area (using QLabel with custom painting to prevent selection)
        self.problem_frame = QtWidgets.QFrame()
        self.problem_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 2px solid #444;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        problem_layout = QtWidgets.QVBoxLayout(self.problem_frame)
        
        # The math expression - rendered as an image
        self.problem_display = QtWidgets.QLabel()
        self.problem_display.setAlignment(QtCore.Qt.AlignCenter)
        self.problem_display.setMinimumHeight(80)
        problem_layout.addWidget(self.problem_display)
        
        layout.addWidget(self.problem_frame)
        
        # Answer input
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(QtWidgets.QLabel("Your Answer:"))
        self.answer_input = QtWidgets.QLineEdit()
        self.answer_input.setPlaceholderText("Type the result here...")
        self.answer_input.setStyleSheet("""
            QLineEdit {
                font-size: 20px;
                padding: 10px;
                border: 2px solid #007bff;
                border-radius: 5px;
            }
        """)
        # Only allow numbers and minus sign
        self.answer_input.setValidator(QtGui.QIntValidator())
        self.answer_input.returnPressed.connect(self._check_answer)
        input_layout.addWidget(self.answer_input)
        layout.addLayout(input_layout)
        
        # Feedback label
        self.feedback_label = QtWidgets.QLabel("")
        self.feedback_label.setAlignment(QtCore.Qt.AlignCenter)
        self.feedback_label.setStyleSheet("font-size: 14px; min-height: 30px;")
        layout.addWidget(self.feedback_label)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        self.submit_btn = QtWidgets.QPushButton("Submit Answer")
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.submit_btn.clicked.connect(self._check_answer)
        
        self.cancel_btn = QtWidgets.QPushButton("Keep Focusing")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                font-size: 14px;
                padding: 10px 30px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.submit_btn)
        layout.addLayout(btn_layout)
    
    def _render_problem_as_image(self, a: int, b: int, op: str) -> QtGui.QPixmap:
        """Render the math problem as a pixmap to prevent text selection/copying."""
        # Format the expression first to calculate required width
        expression = f"{a:,}  {op}  {b:,}  =  ?"
        
        # Use a monospace font for clear number display
        font = QtGui.QFont("Consolas", 24, QtGui.QFont.Bold)
        
        # Calculate text width using font metrics
        metrics = QtGui.QFontMetrics(font)
        text_width = metrics.horizontalAdvance(expression)
        text_height = metrics.height()
        
        # Add padding for comfortable display
        width = text_width + 60
        height = text_height + 30
        
        # Ensure minimum dimensions
        width = max(width, 480)
        height = max(height, 60)
        
        pixmap = QtGui.QPixmap(width, height)
        pixmap.fill(QtCore.Qt.transparent)
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setFont(font)
        painter.setPen(QtGui.QColor("#00ff88"))
        
        # Draw centered
        rect = QtCore.QRect(0, 0, width, height)
        painter.drawText(rect, QtCore.Qt.AlignCenter, expression)
        
        painter.end()
        return pixmap
    
    def _show_current_problem(self) -> None:
        """Display the current math problem."""
        problem = self.problems[self.current_problem]
        
        # Update progress
        self.progress_label.setText(f"Problem {self.current_problem + 1} of 2")
        
        # Render the problem as an image
        pixmap = self._render_problem_as_image(
            problem['a'], problem['b'], problem['op']
        )
        self.problem_display.setPixmap(pixmap)
        
        # Clear previous input and feedback
        self.answer_input.clear()
        self.feedback_label.setText("")
        self.answer_input.setFocus()
    
    def _check_answer(self) -> None:
        """Verify the user's answer."""
        try:
            user_answer = int(self.answer_input.text().strip())
        except ValueError:
            self.feedback_label.setText("❌ Please enter a valid number!")
            self.feedback_label.setStyleSheet("font-size: 14px; color: #dc3545; min-height: 30px;")
            return
        
        correct_answer = self.problems[self.current_problem]['answer']
        
        if user_answer == correct_answer:
            self.solved_count += 1
            self.current_problem += 1
            
            if self.solved_count >= 2:
                # All problems solved! Require explicit confirmation to close.
                self.feedback_label.setText("✅ Correct! Click 'End Session' to finish.")
                self.feedback_label.setStyleSheet("font-size: 14px; color: #28a745; min-height: 30px;")
                self.answer_input.setEnabled(False)
                self.submit_btn.setText("End Session")
                if not self._ready_to_finish:
                    try:
                        self.submit_btn.clicked.disconnect(self._check_answer)
                    except TypeError:
                        pass
                    self.submit_btn.clicked.connect(self.accept)
                    self._ready_to_finish = True
            else:
                # Show next problem
                self.feedback_label.setText("✅ Correct! One more to go...")
                self.feedback_label.setStyleSheet("font-size: 14px; color: #28a745; min-height: 30px;")
                QtCore.QTimer.singleShot(800, self._show_current_problem)
        else:
            # Wrong answer - generate new problems and restart
            self.feedback_label.setText("❌ Wrong! Starting over with new problems...")
            self.feedback_label.setStyleSheet("font-size: 14px; color: #dc3545; min-height: 30px;")
            
            # Reset with new problems after a delay
            QtCore.QTimer.singleShot(1500, self._reset_challenge)
    
    def _reset_challenge(self) -> None:
        """Reset the challenge with new problems."""
        self.problems = self._generate_problems()
        self.current_problem = 0
        self.solved_count = 0
        self._show_current_problem()
    
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Prevent Escape from closing the dialog easily."""
        if event.key() == QtCore.Qt.Key_Escape:
            # Ignore escape - user must click "Keep Focusing" or solve problems
            return
        super().keyPressEvent(event)


class OnboardingModeDialog(QtWidgets.QDialog):
    """Prompt the user to pick how they want to play on startup."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        ensure_hero_structure(self.blocker.adhd_buster)

        self.setWindowTitle("Choose Gamification Mode")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        layout = QtWidgets.QVBoxLayout(self)
        info = QtWidgets.QLabel(
            "How would you like to play today?\n"
            "• Story: each story has its own hero, gear, and decisions.\n"
            "• Hero only: level up a free hero, no story.\n"
            "• Disabled: no gamification for this session."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.story_radio = QtWidgets.QRadioButton("Story mode")
        self.hero_only_radio = QtWidgets.QRadioButton("Hero only (no story)")
        self.disabled_radio = QtWidgets.QRadioButton("Disabled")

        mode_group = QtWidgets.QButtonGroup(self)
        for btn in (self.story_radio, self.hero_only_radio, self.disabled_radio):
            mode_group.addButton(btn)
            layout.addWidget(btn)

        self.story_combo = NoScrollComboBox()
        if AVAILABLE_STORIES:
            for story_id, info_data in AVAILABLE_STORIES.items():
                self.story_combo.addItem(info_data.get("title", story_id), story_id)
        else:
            self.story_combo.addItem("The Focus Warrior", "warrior")
        layout.addWidget(self.story_combo)

        current_mode = get_story_mode(self.blocker.adhd_buster)
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")

        if current_mode == STORY_MODE_HERO_ONLY:
            self.hero_only_radio.setChecked(True)
        elif current_mode == STORY_MODE_DISABLED:
            self.disabled_radio.setChecked(True)
        else:
            self.story_radio.setChecked(True)

        idx = self.story_combo.findData(active_story)
        if idx >= 0:
            self.story_combo.setCurrentIndex(idx)

        self.story_radio.toggled.connect(self._on_mode_changed)
        self.hero_only_radio.toggled.connect(self._on_mode_changed)
        self.disabled_radio.toggled.connect(self._on_mode_changed)
        self._on_mode_changed()

        # Don't ask again checkbox
        self.dont_ask_checkbox = QtWidgets.QCheckBox("Don't ask again on startup")
        self.dont_ask_checkbox.setToolTip(
            "You can always change your mode from the ADHD Buster dialog (Story Settings)"
        )
        layout.addWidget(self.dont_ask_checkbox)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_mode_changed(self) -> None:
        self.story_combo.setEnabled(self.story_radio.isChecked())

    def get_selection(self) -> tuple:
        if self.disabled_radio.isChecked():
            return STORY_MODE_DISABLED, None
        if self.hero_only_radio.isChecked():
            return STORY_MODE_HERO_ONLY, None
        story_id = self.story_combo.currentData()
        return STORY_MODE_ACTIVE, story_id

    def should_skip_next_time(self) -> bool:
        """Return True if user checked 'Don't ask again'."""
        return self.dont_ask_checkbox.isChecked()


class TimerTab(QtWidgets.QWidget):
    """Qt implementation of the timer tab (start/stop, modes, presets, countdown)."""

    timer_tick = QtCore.Signal(int)  # remaining seconds
    session_complete = QtCore.Signal(int)  # elapsed seconds
    session_started = QtCore.Signal()  # emitted when a session starts

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.timer_running = False
        self.remaining_seconds = 0
        self.session_start: Optional[float] = None
        self._giving_rewards = False  # Re-entrancy guard for deferred rewards
        
        # Pomodoro state
        self.pomodoro_is_break = False
        self.pomodoro_session_count = 0
        self.pomodoro_total_work_time = 0
        
        # Priority check-in tracking
        self.last_checkin_time: Optional[float] = None
        
        # Track if session is on a strategic priority for 2.5x coin multiplier
        self.session_is_strategic: bool = False
        self.session_priority_title: Optional[str] = None

        self._build_ui()
        self._connect_signals()

        # QTimer for ticking each second
        self.qt_timer = QtCore.QTimer(self)
        self.qt_timer.setInterval(1000)
        self.qt_timer.timeout.connect(self._on_tick)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Timer display with modern card design
        timer_card = QtWidgets.QFrame()
        timer_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d3436, stop:1 #1a1a1a);
                border: 2px solid #5f27cd;
                border-radius: 20px;
                padding: 30px;
            }
        """)
        timer_layout = QtWidgets.QVBoxLayout(timer_card)
        timer_layout.setContentsMargins(20, 20, 20, 20)
        
        self.timer_label = QtWidgets.QLabel("00:00:00")
        self.timer_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_label.setStyleSheet("""
            font: 700 48px 'Consolas';
            color: #a29bfe;
            background: transparent;
            padding: 20px;
        """)
        timer_layout.addWidget(self.timer_label)
        layout.addWidget(timer_card)

        # Mode selection
        mode_box = QtWidgets.QGroupBox("Mode")
        mode_layout = QtWidgets.QHBoxLayout(mode_box)
        self.mode_buttons: Dict[str, QtWidgets.QRadioButton] = {}
        modes = [
            ("Normal", BlockMode.NORMAL, "Can stop session anytime"),
            ("Strict 🔐", BlockMode.STRICT, "Requires password to stop"),
            ("Hardcore �", BlockMode.HARDCORE, "Solve math problems to stop - no easy escape!"),
            ("Pomodoro 🍅", BlockMode.POMODORO, "25 min work / 5 min break cycles"),
        ]
        for text, value, tooltip in modes:
            btn = QtWidgets.QRadioButton(text)
            btn.setProperty("mode_value", value)
            btn.setToolTip(tooltip)
            mode_layout.addWidget(btn)
            self.mode_buttons[value] = btn
        self.mode_buttons[BlockMode.NORMAL].setChecked(True)
        layout.addWidget(mode_box)

        # Duration inputs with modern gradient card
        duration_box = QtWidgets.QGroupBox("⏱️ Session Duration")
        duration_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #74b9ff;
                border: 2px solid #2d3436;
                border-radius: 12px;
                margin-top: 10px;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d3436, stop:1 #1a1a1a);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #b2bec3;
                font-size: 13px;
            }
            QSpinBox {
                background: #1a1a1a;
                border: 2px solid #0984e3;
                border-radius: 6px;
                padding: 5px;
                color: #74b9ff;
                font-size: 14px;
                font-weight: bold;
                min-width: 60px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0984e3, stop:1 #0652a8);
                border-radius: 3px;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #74b9ff;
            }
        """)
        duration_layout = QtWidgets.QHBoxLayout(duration_box)
        self.hours_spin = QtWidgets.QSpinBox()
        self.hours_spin.setRange(0, 12)
        self.hours_spin.setValue(0)
        self.minutes_spin = QtWidgets.QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(25)
        duration_layout.addWidget(QtWidgets.QLabel("Hours"))
        duration_layout.addWidget(self.hours_spin)
        duration_layout.addWidget(QtWidgets.QLabel("Minutes"))
        duration_layout.addWidget(self.minutes_spin)
        layout.addWidget(duration_box)

        # Presets with modern gradient buttons
        preset_box = QtWidgets.QGroupBox("⚡ Quick Presets")
        preset_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #ffeaa7;
                border: 2px solid #2d3436;
                border-radius: 12px;
                margin-top: 10px;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d3436, stop:1 #1a1a1a);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        preset_layout = QtWidgets.QHBoxLayout(preset_box)
        presets = [("25m", 25), ("45m", 45), ("1h", 60), ("2h", 120), ("4h", 240)]
        for label, minutes in presets:
            btn = QtWidgets.QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #fdcb6e, stop:1 #e17055);
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                    border-radius: 8px;
                    border: 2px solid #d63031;
                    padding: 8px 15px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffeaa7, stop:1 #fab1a0);
                }
                QPushButton:pressed {
                    background: #d63031;
                }
            """)
            btn.clicked.connect(lambda _=False, m=minutes: self._set_preset(m))
            preset_layout.addWidget(btn)
        layout.addWidget(preset_box)

        # Notification option with modern styling
        self.notify_checkbox = QtWidgets.QCheckBox("🔔 Notify me when session ends")
        self.notify_checkbox.setChecked(getattr(self.blocker, 'notify_on_complete', True))
        self.notify_checkbox.setToolTip("Show a desktop notification when your focus session completes")
        self.notify_checkbox.setStyleSheet("""
            QCheckBox {
                color: #dfe6e9;
                font-size: 13px;
                spacing: 8px;
                padding: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #00b894;
                background: #1a1a1a;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #55efc4, stop:1 #00b894);
                border: 2px solid #55efc4;
            }
        """)
        layout.addWidget(self.notify_checkbox)

        # Start/Stop buttons with modern gradient styling
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.start_btn = QtWidgets.QPushButton("▶ Start Focus Session")
        self.start_btn.setMinimumHeight(65)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00b894, stop:1 #00a884);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 12px;
                border: 2px solid #00cec9;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #55efc4, stop:1 #00b894);
                border: 2px solid #55efc4;
            }
            QPushButton:pressed {
                background: #00a884;
            }
            QPushButton:disabled {
                background: #555555;
                border: 2px solid #444444;
                color: #888888;
            }
        """)
        
        self.stop_btn = QtWidgets.QPushButton("⬛ Stop Session")
        self.stop_btn.setMinimumHeight(65)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #d63031, stop:1 #c0392b);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 12px;
                border: 2px solid #e74c3c;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff7675, stop:1 #d63031);
                border: 2px solid #ff7675;
            }
            QPushButton:pressed {
                background: #c0392b;
            }
            QPushButton:disabled {
                background: #555555;
                border: 2px solid #444444;
                color: #888888;
            }
        """)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Status label with modern card design
        status_card = QtWidgets.QFrame()
        status_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d3436, stop:1 #1a1a1a);
                border: 2px solid #00b894;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        status_layout = QtWidgets.QVBoxLayout(status_card)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QtWidgets.QLabel("✨ Ready to focus")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #00b894;
            background: transparent;
            padding: 5px;
        """)
        status_layout.addWidget(self.status_label)
        layout.addWidget(status_card)
        
        # Rewards info section with modern gradient styling
        rewards_group = QtWidgets.QGroupBox("🎁 Session Rewards")
        rewards_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #a5b4fc;
                border: 2px solid #2d3436;
                border-radius: 12px;
                margin-top: 10px;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d3436, stop:1 #1a1a1a);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        rewards_layout = QtWidgets.QVBoxLayout(rewards_group)
        rewards_info = QtWidgets.QLabel(
            "<b style='color:#ffeaa7;'>How it works:</b> <span style='color:#dfe6e9;'>Complete a focus session to earn 1 random item. Longer sessions shift the rarity distribution higher.</span><br>"
            "<table style='font-size:10px; color:#b2bec3; margin-top:5px;'>"
            "<tr style='color:#ffeaa7;'><th>Session</th><th>Common</th><th>Uncommon</th><th>Rare</th><th>Epic</th><th>Legendary</th></tr>"
            "<tr><td>&lt;30min</td><td>50%</td><td>30%</td><td>15%</td><td>4%</td><td>1%</td></tr>"
            "<tr><td>30min</td><td><b style='color:#4caf50;'>80%</b></td><td>15%</td><td>5%</td><td>-</td><td>-</td></tr>"
            "<tr><td>1hr</td><td>20%</td><td><b style='color:#4caf50;'>60%</b></td><td>15%</td><td>5%</td><td>-</td></tr>"
            "<tr><td>2hr</td><td>5%</td><td>15%</td><td><b style='color:#2196f3;'>60%</b></td><td>15%</td><td>5%</td></tr>"
            "<tr><td>3hr</td><td>-</td><td>5%</td><td>15%</td><td><b style='color:#9c27b0;'>60%</b></td><td>20%</td></tr>"
            "<tr><td>4hr+</td><td>-</td><td>-</td><td>5%</td><td>15%</td><td><b style='color:#ff9800;'>80%</b></td></tr>"
            "</table>"
            "<br><b style='color:#74b9ff;'>Streak bonus:</b> <span style='color:#dfe6e9;'>+1 tier per 7-day streak</span> | <b style='color:#fdcb6e;'>XP:</b> <span style='color:#dfe6e9;'>25 base + 2/min + streak bonus</span>"
        )
        rewards_info.setWordWrap(True)
        rewards_info.setStyleSheet("color: #dfe6e9; font-size: 11px; background: transparent; padding: 8px;")
        rewards_layout.addWidget(rewards_info)
        layout.addWidget(rewards_group)

        layout.addStretch(1)

    def _connect_signals(self) -> None:
        self.start_btn.clicked.connect(self._start_session)
        self.stop_btn.clicked.connect(self._stop_session)
        self.notify_checkbox.stateChanged.connect(self._save_notify_preference)

    def _save_notify_preference(self) -> None:
        """Save the notification preference when checkbox changes."""
        self.blocker.notify_on_complete = self.notify_checkbox.isChecked()
        self.blocker.save_config()

    # === UI helpers ===
    def _set_preset(self, minutes: int) -> None:
        self.hours_spin.setValue(minutes // 60)
        self.minutes_spin.setValue(minutes % 60)

    def _current_mode(self) -> str:
        for value, btn in self.mode_buttons.items():
            if btn.isChecked():
                return value
        return BlockMode.NORMAL

    def _format_time(self, seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _update_timer_display(self) -> None:
        """Update timer label and button states."""
        self.timer_label.setText(self._format_time(self.remaining_seconds))
        if self.timer_running:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("🔒 BLOCKING")
        else:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Ready to focus")

    # === Timer control ===
    def _start_session(self) -> None:
        # Guard against starting while already running
        if self.timer_running:
            return
        
        # Set immediately to prevent race condition from double-clicks
        self.timer_running = True
        
        hours = self.hours_spin.value()
        minutes = self.minutes_spin.value()
        total_minutes = hours * 60 + minutes
        if total_minutes <= 0:
            self.timer_running = False  # Reset on validation failure
            show_warning(self, "Invalid Duration", "Please set a time greater than 0 minutes.")
            return

        mode = self._current_mode()
        self.blocker.mode = mode

        # Reset Pomodoro state
        self.pomodoro_is_break = False
        self.pomodoro_session_count = 0
        self.pomodoro_total_work_time = 0
        self.last_checkin_time = None
        self._checkin_count = 0  # Reset priority check-in counter
        
        # Reset strategic priority tracking (will be set by priority dialog if applicable)
        # Only reset if not already set by _start_priority_session
        if not hasattr(self, '_preserve_strategic_flag'):
            self.session_is_strategic = False
            self.session_priority_title = None
        else:
            delattr(self, '_preserve_strategic_flag')

        # Pomodoro uses its own durations
        if mode == BlockMode.POMODORO:
            total_seconds = self.blocker.pomodoro_work * 60
            self.status_label.setText(f"🍅 WORK #{self.pomodoro_session_count + 1}")
        else:
            total_seconds = total_minutes * 60

        success, message = self.blocker.block_sites(duration_seconds=total_seconds)
        if not success:
            self.timer_running = False  # Reset on blocking failure
            show_error(self, "Cannot Start Session", message)
            return

        self.remaining_seconds = total_seconds
        self.session_start = QtCore.QDateTime.currentDateTime().toSecsSinceEpoch()
        self.timer_label.setText(self._format_time(self.remaining_seconds))
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        if mode != BlockMode.POMODORO:
            self.status_label.setText("🔒 BLOCKING")
        self.qt_timer.start()

        # Emit session started signal
        self.session_started.emit()

        # Update tray icon to blocking state
        main_window = self.window()
        if hasattr(main_window, '_update_tray_icon'):
            main_window._update_tray_icon(blocking=True)

    def _stop_session(self) -> None:
        # Check password for Strict Mode
        if self.blocker.mode == BlockMode.STRICT and self.blocker.password_hash:
            pwd, ok = QtWidgets.QInputDialog.getText(
                self, "Password Required", "Enter password to stop Strict Mode:",
                QtWidgets.QLineEdit.Password
            )
            if not ok or not self.blocker.verify_password(pwd or ""):
                show_warning(self, "Incorrect Password", "The password you entered is incorrect.\nSession continues.")
                return
        
        # Check for Hardcore Mode - must solve math challenges
        if self.blocker.mode == BlockMode.HARDCORE:
            dialog = HardcoreChallengeDialog(self)
            if dialog.exec() != QtWidgets.QDialog.Accepted:
                # User cancelled or failed - session continues
                return

        elapsed = 0
        if self.session_start:
            elapsed = int(QtCore.QDateTime.currentDateTime().toSecsSinceEpoch() - self.session_start)

        self.timer_running = False
        self.qt_timer.stop()
        self.remaining_seconds = 0
        self.timer_label.setText("00:00:00")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Ready to focus")
        self.pomodoro_is_break = False
        self.pomodoro_session_count = 0
        self.pomodoro_total_work_time = 0

        # Update tray icon to ready state
        main_window = self.window()
        if hasattr(main_window, '_update_tray_icon'):
            main_window._update_tray_icon(blocking=False)

        # Unblock sites
        self.blocker.unblock_sites()

        # Only record stats if ran > 60s
        if elapsed > 60:
            self.blocker.update_stats(elapsed, completed=False)
            self.session_complete.emit(elapsed)

    def _on_tick(self) -> None:
        if not self.timer_running:
            return
        self.remaining_seconds -= 1
        self.timer_label.setText(self._format_time(max(self.remaining_seconds, 0)))
        self.timer_tick.emit(max(self.remaining_seconds, 0))

        # Priority check-in during sessions
        self._check_priority_checkin()

        if self.remaining_seconds <= 0:
            self._handle_session_complete()

    def _check_priority_checkin(self) -> None:
        """Check if it's time to show a priority check-in dialog."""
        if not self.blocker.priority_checkin_enabled:
            return
        if self.blocker.mode == BlockMode.POMODORO and self.pomodoro_is_break:
            return  # Don't check-in during breaks
        if not self.session_start:
            return

        elapsed = int(QtCore.QDateTime.currentDateTime().toSecsSinceEpoch() - self.session_start)
        interval_seconds = self.blocker.priority_checkin_interval * 60
        
        if interval_seconds <= 0:
            return

        # Count intervals that should have triggered a check-in
        intervals_passed = elapsed // interval_seconds
        
        # Track how many check-ins we've completed
        if not hasattr(self, '_checkin_count'):
            self._checkin_count = 0
        
        # If we've completed more intervals than check-ins, show one
        if intervals_passed > 0 and intervals_passed > self._checkin_count:
            self._checkin_count = intervals_passed
            self.last_checkin_time = elapsed
            self._show_priority_checkin()

    def _show_priority_checkin(self) -> None:
        """Show the priority check-in dialog."""
        today = datetime.now().strftime("%A")
        today_priorities = [
            p for p in self.blocker.priorities
            if p.get("title", "").strip() and (not p.get("days") or today in p.get("days", []))
        ]
        if not today_priorities:
            return

        elapsed = int(QtCore.QDateTime.currentDateTime().toSecsSinceEpoch() - self.session_start) if self.session_start else 0
        session_minutes = elapsed // 60

        dialog = PriorityCheckinDialog(self.blocker, today_priorities, session_minutes, self.window())
        dialog.exec()

        # Handle on-task confirmation with rewards
        if dialog.result and GAMIFICATION_AVAILABLE:
            self._give_session_rewards(session_minutes)

    def _is_perfect_session(self) -> bool:
        """
        Check if the current session was perfect (no distraction attempts).
        
        A perfect session means the user didn't try to access any blocked sites.
        Returns True if bypass logger shows 0 attempts, or if bypass logger is unavailable.
        """
        if not BYPASS_LOGGER_AVAILABLE:
            return False  # Conservative: if we can't track, assume not perfect
        
        try:
            from bypass_logger import get_bypass_logger
            bypass_logger = get_bypass_logger()
            stats = bypass_logger.get_statistics()
            return stats.get("current_session", 0) == 0
        except Exception:
            return False  # Error getting stats, assume not perfect

    def _give_session_rewards(self, session_minutes: int) -> None:
        """Give item drop, XP, and diary entry rewards with lottery animation."""
        if not GAMIFICATION_AVAILABLE:
            return
        # Skip if gamification mode is disabled
        if not is_gamification_enabled(self.blocker.adhd_buster):
            return

        streak = self.blocker.stats.get("streak_days", 0)
        
        # Get active story for themed item generation
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        
        # Calculate coin earnings
        session_hours = session_minutes / 60.0
        base_coins_per_hour = 10
        coins_earned = int(session_hours * base_coins_per_hour)
        
        # Apply strategic priority bonus (+150% = 2.5x multiplier)
        if self.session_is_strategic:
            coins_earned = int(coins_earned * 2.5)
        
        # Apply lucky options coin bonus from equipped gear - REMOVED (now used for merge discount)
        equipped = self.blocker.adhd_buster.get("equipped", {})
        lucky_bonuses = {"coin_discount": 0, "xp_bonus": 0, "merge_luck": 0}
        if calculate_total_lucky_bonuses:
            lucky_bonuses = calculate_total_lucky_bonuses(equipped)
        
        # Add streak bonus coins (logarithmic scaling)
        streak_bonus = 0
        if streak >= 30:
            streak_bonus = 100
        elif streak >= 14:
            streak_bonus = 50
        elif streak >= 7:
            streak_bonus = 25
        elif streak >= 3:
            streak_bonus = 10
        
        coins_earned += streak_bonus
        
        # ✨ ENTITY PERK BONUS: Apply coin perks from collected entities
        entity_coin_bonus = 0
        coin_perk_breakdown = []
        try:
            from gamification import get_entity_coin_perks
            coin_perks = get_entity_coin_perks(self.blocker.adhd_buster, source="session")
            
            # Add flat coin bonus
            if coin_perks["coin_flat"] > 0:
                entity_coin_bonus += coin_perks["coin_flat"]
                coin_perk_breakdown.append(f"+{coin_perks['coin_flat']} coins")
            
            # Apply percent bonus
            if coin_perks["coin_percent"] > 0:
                pct_bonus = int(coins_earned * (coin_perks["coin_percent"] / 100.0))
                entity_coin_bonus += pct_bonus
                coin_perk_breakdown.append(f"+{coin_perks['coin_percent']}% coins")
            
            coins_earned += entity_coin_bonus
        except Exception as e:
            print(f"[Entity Perks] Error applying coin perks: {e}")
        
        # ✨ PERFECT SESSION BONUS: Apply bonus if no distraction attempts
        is_perfect = self._is_perfect_session()
        perfect_session_bonus_pct = 0
        if is_perfect:
            try:
                from gamification import get_entity_qol_perks
                qol_perks = get_entity_qol_perks(self.blocker.adhd_buster)
                perfect_session_bonus_pct = qol_perks.get("perfect_session_bonus", 0)
                if perfect_session_bonus_pct > 0:
                    perfect_coin_bonus = int(coins_earned * (perfect_session_bonus_pct / 100.0))
                    coins_earned += perfect_coin_bonus
                    coin_perk_breakdown.append(f"+{perfect_session_bonus_pct}% perfect session")
            except Exception as e:
                print(f"[Perfect Session] Error applying bonus: {e}")
        
        # Award XP for the focus session (with lucky XP bonus from gear AND entity perks)
        xp_bonus_pct = lucky_bonuses.get("xp_bonus", 0)
        # Add perfect session bonus to XP if applicable
        if is_perfect and perfect_session_bonus_pct > 0:
            xp_bonus_pct += perfect_session_bonus_pct
        # Cap at 200% to prevent overflow
        xp_bonus_pct = min(xp_bonus_pct, 200)
        xp_info = calculate_session_xp(
            session_minutes, streak, lucky_xp_bonus=xp_bonus_pct,
            adhd_buster=self.blocker.adhd_buster
        )

        # Generate item (100% guaranteed drop) with entity rarity perks
        item = generate_item(session_minutes=session_minutes, streak_days=streak,
                              story_id=active_story, adhd_buster=self.blocker.adhd_buster)

        # Show lottery animation for tier reveal (item is always awarded)
        from lottery_animation import FocusTimerLotteryDialog
        lottery_dialog = FocusTimerLotteryDialog(
            session_minutes=session_minutes,
            streak_days=streak,
            item=item,
            parent=self.window()
        )
        lottery_dialog.exec()

        # Ensure item has all required fields
        if "obtained_at" not in item:
            item["obtained_at"] = datetime.now().isoformat()
        
        # === Use GameState Manager for Atomic Updates ===
        # This ensures all UI components are notified of changes automatically
        main_window = self.window()
        game_state = getattr(main_window, 'game_state', None)
        if not game_state:
            logger.error("GameStateManager not available - cannot award session rewards")
            return
        
        # Use award_items_batch for atomic rewards (handles add + auto-equip)
        # This properly deep-copies items and uses the state manager throughout
        game_state.begin_batch()
        try:
            # Award item with auto-equip to empty slots
            game_state.award_items_batch([item], coins=coins_earned, auto_equip=True, source="session_completion")
            
            # Award XP via state manager
            xp_result_tuple = game_state.add_xp(xp_info["total_xp"])
            xp_result = {
                "new_xp": xp_result_tuple[0],
                "new_level": xp_result_tuple[1],
                "leveled_up": xp_result_tuple[2],
            }
            leveled_up = xp_result["leveled_up"]
            
        finally:
            game_state.end_batch()

        # Generate diary entry (once per day)
        today = datetime.now().strftime("%Y-%m-%d")
        diary = self.blocker.adhd_buster.get("diary", [])
        today_entries = [e for e in diary if e.get("date") == today]

        diary_entry = None
        if not today_entries:
            power = calculate_character_power(self.blocker.adhd_buster)
            equipped = self.blocker.adhd_buster.get("equipped", {})
            diary_entry = generate_diary_entry(power, session_minutes, equipped,
                                               story_id=active_story)
            if "diary" not in self.blocker.adhd_buster:
                self.blocker.adhd_buster["diary"] = []
            self.blocker.adhd_buster["diary"].append(diary_entry)
            if len(self.blocker.adhd_buster["diary"]) > 100:
                self.blocker.adhd_buster["diary"] = self.blocker.adhd_buster["diary"][-100:]

        # Sync changes to active hero before final save
        if GAMIFICATION_AVAILABLE:
            sync_hero_data(self.blocker.adhd_buster)
        
        # Final save (game_state already saved during batch, but diary needs saving)
        game_state.force_save()

        # Show level-up celebration first (most exciting!)
        if leveled_up:
            old_level = xp_result.get("old_level", 1)
            new_level = xp_result.get("new_level", 1)
            stats = {
                "total_power": self.blocker.adhd_buster.get("total_power", 0),
                "total_xp": self.blocker.adhd_buster.get("total_xp", 0),
                "total_coins": self.blocker.adhd_buster.get("coins", 0),
                "productivity_score": self.blocker.adhd_buster.get("productivity_score", 0),
                "total_focus_minutes": self.blocker.adhd_buster.get("total_focus_time", 0) // 60,
                "items_collected": len(self.blocker.adhd_buster.get("inventory", [])),
                "unlocks": [],  # Could add level-specific unlocks
                "rewards": None  # Could add level-up rewards
            }
            # Use fullscreen mode for multi-level gains
            fullscreen = (new_level - old_level) > 1
            dialog = EnhancedLevelUpDialog(old_level, new_level, stats, fullscreen, self.window())
            dialog.view_stats.connect(self._show_stats_dialog)
            dialog.exec()

        # Show enhanced item drop dialog with comparison
        equipped_item = None
        if GAMIFICATION_AVAILABLE:
            try:
                from gamification import get_equipped_item
                equipped_item = get_equipped_item(self.blocker.adhd_buster, item.get("slot", "Unknown"))
            except ImportError:
                pass
        
        dialog = EnhancedItemDropDialog(
            item,
            equipped_item,
            session_minutes,
            streak,
            coins_earned,
            self.window()
        )
        dialog.quick_equip_requested.connect(lambda: self._quick_equip_item(item))
        dialog.view_inventory.connect(self._show_inventory_dialog)
        dialog.exec()
        
        # Note: UI updates are now handled automatically via GameState signals
        # The game_state.end_batch() above triggers power_changed, coins_changed,
        # and inventory_changed signals which update the UI reactively.

        # === Entitidex Encounter Check ===
        # After item rewards, check for entity encounter based on session
        self._check_entitidex_encounter(session_minutes)

        # Show diary entry reveal
        if diary_entry:
            DiaryEntryRevealDialog(self.blocker, diary_entry, session_minutes, self.window()).exec()

    def _play_notification_sound(self) -> None:
        """Play a short notification chime on completion."""
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass

    def _quick_equip_item(self, item: dict) -> None:
        """Quick equip an item to empty slot."""
        if not GAMIFICATION_AVAILABLE:
            return
        
        try:
            slot = item.get("slot", "Unknown")
            
            # Check if slot is empty
            equipped = self.blocker.adhd_buster.get("equipped", {})
            if slot in equipped and equipped[slot]:
                show_info(
                    self.window(),
                    "Slot Occupied",
                    f"The {slot} slot already has an item equipped.\n"
                    "Use the Inventory to manage your gear."
                )
                return
            
            # Get game state manager
            game_state = get_game_state()
            if not game_state:
                show_warning(
                    self.window(),
                    "Error",
                    "Game state manager not available."
                )
                return
            
            # Create deep copy to preserve lucky_options
            new_item = item.copy()
            if "lucky_options" in item and isinstance(item["lucky_options"], dict):
                new_item["lucky_options"] = item["lucky_options"].copy()
            
            # Equip the item using GameState
            game_state.swap_equipped_item(slot, new_item)
            
            # Sync changes to active hero
            from gamification import sync_hero_data
            sync_hero_data(self.blocker.adhd_buster)
            
            show_info(
                self.window(),
                "Item Equipped!",
                f"✓ {item.get('name', 'Item')} equipped to {slot} slot!"
            )
            
            # Refresh UI
            main_window = self.window()
            if hasattr(main_window, 'refresh_adhd_tab'):
                main_window.refresh_adhd_tab()
                
        except Exception as e:
            show_warning(
                self.window(),
                "Equip Failed",
                f"Could not equip item: {str(e)}"
            )

    def _check_entitidex_encounter(self, session_minutes: int) -> None:
        """
        Check for and handle entitidex entity encounter after session completion.
        
        Args:
            session_minutes: Duration of the completed session in minutes
        """
        if not GAMIFICATION_AVAILABLE:
            return
        
        # Skip if gamification mode is disabled
        if not is_gamification_enabled(self.blocker.adhd_buster):
            return
        
        try:
            from gamification import check_entitidex_encounter, attempt_entitidex_bond
            # from entity_encounter_dialog import EntityEncounterDialog, BondResultDialog (DEPRECATED)
            
            # Check if this was a perfect session (no distraction attempts)
            is_perfect = self._is_perfect_session()
            
            # Check for encounter
            encounter = check_entitidex_encounter(
                self.blocker.adhd_buster,
                session_minutes,
                perfect_session=is_perfect
            )
            
            if not encounter["triggered"] or not encounter["entity"]:
                return
            
            # Show perk toast if entity perks helped with encounter
            if encounter.get("perk_bonus_applied"):
                perk_parts = []
                if encounter.get("encounter_perk_bonus", 0) > 0:
                    perk_parts.append(f"+{int(encounter['encounter_perk_bonus'])}% encounter")
                if encounter.get("capture_perk_bonus", 0) > 0:
                    perk_parts.append(f"+{int(encounter['capture_perk_bonus'])}% capture")
                if perk_parts:
                    show_perk_toast(f"Entity Perks: {', '.join(perk_parts)}", "🌟", self)
            
            # Show encounter dialog using new merge-style flow
            entity = encounter["entity"]
            # Capture is_exceptional from encounter result for bond attempt
            encounter_is_exceptional = encounter.get("is_exceptional", False)
            
            try:
                from entity_drop_dialog import show_entity_encounter
                from gamification import save_encounter_for_later
            
                # wrapper callback for the bonding logic
                def bond_callback_wrapper(entity_id: str):
                    # Attempt the bond - pass is_exceptional from encounter
                    result = attempt_entitidex_bond(
                        self.blocker.adhd_buster, entity_id, 
                        is_exceptional=encounter_is_exceptional
                    )
                    
                    # Save the updated data immediately
                    from gamification import sync_hero_data
                    sync_hero_data(self.blocker.adhd_buster)
                    
                    # Get game state and emit XP signal if XP was awarded
                    from game_state import get_game_state
                    game_state = get_game_state()
                    if game_state:
                        # Emit XP signal so UI updates (XP was already added to adhd_buster)
                        xp_awarded = result.get('xp_awarded', 0)
                        if xp_awarded > 0:
                            # Get current XP and level for signal emission
                            total_xp = self.blocker.adhd_buster.get('total_xp', 0)
                            level = self.blocker.adhd_buster.get('hero', {}).get('level', 1)
                            game_state.xp_changed.emit(total_xp, level)
                        game_state.force_save()
                        
                    return result

                # wrapper callback for saving encounter for later
                def save_callback_wrapper(entity_id: str):
                    result = save_encounter_for_later(
                        adhd_buster=self.blocker.adhd_buster,
                        entity_id=entity_id,
                        is_exceptional=encounter_is_exceptional,
                        catch_probability=encounter["join_probability"],
                        encounter_perk_bonus=encounter.get("encounter_perk_bonus", 0.0),
                        capture_perk_bonus=encounter.get("capture_perk_bonus", 0.0),
                        session_minutes=session_minutes,
                        was_perfect_session=is_perfect,
                    )
                    
                    # Save updated data
                    from gamification import sync_hero_data
                    sync_hero_data(self.blocker.adhd_buster)
                    
                    from game_state import get_game_state
                    game_state = get_game_state()
                    if game_state:
                        game_state.force_save()
                    
                    return result

                # Check if user has Chad AGI bonded for special interactions on skip
                CHAD_ENTITY_ID = "underdog_008"
                chad_interaction_data = None
                try:
                    from entitidex import EntitidexManager
                    manager = EntitidexManager()
                    manager.load(self.blocker.adhd_buster.get("entitidex", {}))
                    
                    has_chad_normal = CHAD_ENTITY_ID in manager.progress.collected_entity_ids
                    has_chad_exceptional = manager.progress.is_exceptional(CHAD_ENTITY_ID)
                    
                    if has_chad_normal or has_chad_exceptional:
                        from game_state import get_game_state
                        gs = get_game_state()
                        
                        # Callback to add coins (for exceptional Chad's "banking hack")
                        def add_coins_callback(amount: int):
                            if gs:
                                gs.add_coins(amount)
                        
                        # Callback to give entity as if bonded (for exceptional Chad's gift)
                        def give_entity_callback():
                            # Call the bond logic with guaranteed success (Chad's gift)
                            result = attempt_entitidex_bond(
                                self.blocker.adhd_buster, entity.id,
                                is_exceptional=encounter_is_exceptional,
                                force_success=True  # Chad guarantees the bond!
                            )
                            from gamification import sync_hero_data
                            sync_hero_data(self.blocker.adhd_buster)
                            if gs:
                                xp_awarded = result.get('xp_awarded', 0)
                                if xp_awarded > 0:
                                    total_xp = self.blocker.adhd_buster.get('total_xp', 0)
                                    level = self.blocker.adhd_buster.get('hero', {}).get('level', 1)
                                    gs.xp_changed.emit(total_xp, level)
                                gs.force_save()
                        
                        chad_interaction_data = {
                            "has_chad_normal": has_chad_normal and not has_chad_exceptional,
                            "has_chad_exceptional": has_chad_exceptional,
                            "add_coins_callback": add_coins_callback,
                            "give_entity_callback": give_entity_callback,
                        }
                except Exception as e:
                    logger.debug(f"Could not check for Chad entity: {e}")

                show_entity_encounter(
                    entity=entity,
                    join_probability=encounter["join_probability"],
                    bond_logic_callback=bond_callback_wrapper,
                    parent=self.window(),
                    is_exceptional=encounter_is_exceptional,
                    save_callback=save_callback_wrapper,
                    chad_interaction_data=chad_interaction_data,
                    coin_data=self._get_coin_data(),
                )
            except ImportError:
                 logger.error("Could not import entity_drop_dialog logic")
            
        except ImportError as e:
            # Entitidex not available - silently skip
            logger.debug(f"Entitidex not available: {e}")
        except Exception as e:
            logger.warning(f"Error checking entitidex encounter: {e}")

    def _get_coin_data(self) -> Optional[Dict[str, Any]]:
        """
        Get coin operation callbacks for special entity bonding rewards.
        
        Returns:
            Dict with get_coins_callback and add_coins_callback, or None if unavailable.
        """
        try:
            from game_state import get_game_state
            gs = get_game_state()
            if gs:
                def get_coins_callback() -> int:
                    return gs.coins
                
                def add_coins_callback(amount: int) -> None:
                    gs.add_coins(amount)
                
                return {
                    "get_coins_callback": get_coins_callback,
                    "add_coins_callback": add_coins_callback,
                }
        except Exception as e:
            logger.debug(f"Could not get coin data: {e}")
        return None

    def _show_inventory_dialog(self) -> None:
        """Show inventory management dialog."""
        main_window = self.window()
        if hasattr(main_window, 'adhd_tab'):
            # Switch to ADHD Buster tab
            if hasattr(main_window, 'tabs'):
                tab_index = main_window.tabs.indexOf(main_window.adhd_tab)
                if tab_index >= 0:
                    main_window.tabs.setCurrentIndex(tab_index)
            
            # Open inventory section if available
            if hasattr(main_window.adhd_tab, 'inventory_section'):
                main_window.adhd_tab.inventory_section.show()
                
    def _show_stats_dialog(self) -> None:
        """Show stats/character dialog."""
        main_window = self.window()
        if hasattr(main_window, 'adhd_tab'):
            # Switch to ADHD Buster tab
            if hasattr(main_window, 'tabs'):
                tab_index = main_window.tabs.indexOf(main_window.adhd_tab)
                if tab_index >= 0:
                    main_window.tabs.setCurrentIndex(tab_index)
            
            # Open character section if available
            if hasattr(main_window.adhd_tab, 'character_section'):
                main_window.adhd_tab.character_section.show()

    def _show_desktop_notification(self, title: str, message: str) -> None:
        """Show a Windows toast notification."""
        if not getattr(self, 'notify_checkbox', None) or not self.notify_checkbox.isChecked():
            return
        
        try:
            # Use Windows tray balloon tip (works on all Windows versions)
            main_window = self.window()
            if hasattr(main_window, 'tray_icon') and main_window.tray_icon:
                main_window.tray_icon.showMessage(
                    title,
                    message,
                    QtWidgets.QSystemTrayIcon.Information,
                    10000  # 10 seconds
                )
        except Exception:
            pass  # Silent fail - sound notification still works

    def _handle_session_complete(self) -> None:
        """Handle session completion."""
        self.timer_running = False
        self.qt_timer.stop()

        elapsed = 0
        if self.session_start:
            elapsed = int(QtCore.QDateTime.currentDateTime().toSecsSinceEpoch() - self.session_start)

        # Handle Pomodoro mode specially
        if self.blocker.mode == BlockMode.POMODORO:
            self._handle_pomodoro_complete(elapsed)
            return

        self.blocker.update_stats(elapsed, completed=True)
        self.blocker.unblock_sites(force=True)

        # Notify the user the session has ended
        self._play_notification_sound()
        
        # Show desktop notification if enabled
        session_minutes = elapsed // 60
        self._show_desktop_notification(
            "🎉 Focus Session Complete!",
            f"Great job! You focused for {session_minutes} minutes.\nTime for a well-deserved break!"
        )

        self.timer_label.setText("00:00:00")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Session complete 🎉")

        # Update tray icon to ready state
        main_window = self.window()
        if hasattr(main_window, '_update_tray_icon'):
            main_window._update_tray_icon(blocking=False)

        # Process events to update UI immediately before showing dialogs
        QtWidgets.QApplication.processEvents()

        session_minutes = elapsed // 60

        # Collect rewards first (needed for dialog display)
        rewards_info = {}
        if session_minutes > 0:
            rewards_info = self._collect_session_rewards(session_minutes)
        
        # Emit session_complete EARLY so stats refresh immediately
        # (will emit again after rewards to capture XP/item changes)
        self.session_complete.emit(elapsed)
        
        # Show new professional session complete dialog
        from session_complete_dialog import SessionCompleteDialog
        dialog = SessionCompleteDialog(elapsed, rewards_info, parent=self)
        
        # Connect quick action signals
        dialog.start_another_session.connect(self._start_session)
        dialog.view_stats.connect(lambda: self.window().tabs.setCurrentIndex(1))  # Switch to Stats tab
        main_window = self.window()
        if hasattr(main_window, 'show_priorities_dialog'):
            dialog.view_priorities.connect(main_window.show_priorities_dialog)
        
        dialog.exec()
        
        # Process rewards after dialog shown
        if session_minutes > 0:
            QtCore.QTimer.singleShot(50, lambda: self._give_session_rewards_deferred(session_minutes))

    def _give_session_rewards_deferred(self, session_minutes: int) -> None:
        """Deferred session rewards to keep UI responsive.
        
        Uses a re-entrancy guard to prevent multiple reward grants
        if processEvents() triggers additional callbacks.
        """
        if self._giving_rewards:
            return  # Prevent re-entrancy from processEvents
        self._giving_rewards = True
        try:
            QtWidgets.QApplication.processEvents()
            self._give_session_rewards(session_minutes)
            QtWidgets.QApplication.processEvents()
            self._show_priority_time_log(session_minutes)
            # Calculate elapsed for signal - approximate from session_minutes
            self.session_complete.emit(session_minutes * 60)
        finally:
            self._giving_rewards = False
    
    def _collect_session_rewards(self, session_minutes: int) -> dict:
        """Collect reward information without actually awarding them yet.
        
        Returns dict with reward details for display in session complete dialog.
        """
        rewards = {
            "xp": 0,
            "coins": 0,
            "items": [],
            "streak_maintained": False,
            "current_streak": 0
        }
        
        if not GAMIFICATION_AVAILABLE:
            return rewards
        
        if not is_gamification_enabled(self.blocker.adhd_buster):
            return rewards
        
        streak = self.blocker.stats.get("streak_days", 0)
        rewards["current_streak"] = streak
        rewards["streak_maintained"] = streak > 0
        
        # Calculate XP
        equipped = self.blocker.adhd_buster.get("equipped", {})
        lucky_bonuses = {"xp_bonus": 0}
        if calculate_total_lucky_bonuses:
            lucky_bonuses = calculate_total_lucky_bonuses(equipped)
        xp_bonus_pct = min(lucky_bonuses.get("xp_bonus", 0), 200)
        xp_info = calculate_session_xp(
            session_minutes, streak, lucky_xp_bonus=xp_bonus_pct,
            adhd_buster=self.blocker.adhd_buster
        )
        rewards["xp"] = xp_info["total_xp"]
        
        # Calculate coins
        session_hours = session_minutes / 60.0
        base_coins_per_hour = 10
        coins_earned = int(session_hours * base_coins_per_hour)
        
        if self.session_is_strategic:
            coins_earned = int(coins_earned * 2.5)
        
        # Streak bonus
        if streak >= 30:
            coins_earned += 100
        elif streak >= 14:
            coins_earned += 50
        elif streak >= 7:
            coins_earned += 25
        elif streak >= 3:
            coins_earned += 10
        
        # ✨ ENTITY PERK BONUS: Apply coin perks from collected entities
        try:
            from gamification import get_entity_coin_perks
            coin_perks = get_entity_coin_perks(self.blocker.adhd_buster, source="session")
            if coin_perks["coin_flat"] > 0:
                coins_earned += coin_perks["coin_flat"]
            if coin_perks["coin_percent"] > 0:
                coins_earned += int(coins_earned * (coin_perks["coin_percent"] / 100.0))
        except Exception:
            pass
        
        rewards["coins"] = coins_earned
        
        # Estimate item drop (without actually generating)
        # Just show that an item will be earned
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        
        # Generate preview item (won't be saved)
        preview_item = generate_item(session_minutes=session_minutes, 
                                     streak_days=streak, story_id=active_story)
        rewards["items"] = [preview_item]
        
        return rewards

    def _show_priority_time_log(self, session_minutes: int) -> None:
        """Show priority time logging dialog."""
        today = datetime.now().strftime("%A")
        has_priorities = any(
            p.get("title", "").strip() and (not p.get("days") or today in p.get("days", []))
            for p in self.blocker.priorities
        )
        if has_priorities:
            PriorityTimeLogDialog(self.blocker, session_minutes, self.window()).exec()

    def _handle_pomodoro_complete(self, elapsed: int) -> None:
        """Handle Pomodoro work/break cycle transitions."""
        if self.pomodoro_is_break:
            # Break is over, start next work session
            self.pomodoro_is_break = False
            self._play_notification_sound()
            self._show_desktop_notification(
                "⏰ Break Over!",
                f"Break time is over!\nReady for another focus session?"
            )
            self.blocker.unblock_sites(force=True)

            if show_question(
                self, "Break Over! 🍅",
                f"Break time is over!\n\n"
                f"Sessions completed: {self.pomodoro_session_count}\n"
                f"Total focus time: {self.pomodoro_total_work_time // 60} min\n\n"
                "Ready for another focus session?"
            ) == QtWidgets.QMessageBox.Yes:
                self._start_pomodoro_work()
            else:
                self._end_pomodoro_session()
        else:
            # Work session completed
            self.pomodoro_session_count += 1
            self.pomodoro_total_work_time += elapsed
            self.blocker.update_stats(elapsed, completed=True)
            self._play_notification_sound()
            
            # Show desktop notification
            session_minutes = elapsed // 60
            self._show_desktop_notification(
                f"🍅 Pomodoro #{self.pomodoro_session_count} Complete!",
                f"Great work! You focused for {session_minutes} minutes.\nTime for a break!"
            )
            self.blocker.unblock_sites(force=True)

            # Give rewards for completing work session
            if session_minutes > 0:
                self._give_session_rewards(session_minutes)

            # Determine break length
            sessions_before_long = self.blocker.pomodoro_sessions_before_long
            if self.pomodoro_session_count % sessions_before_long == 0:
                break_minutes = self.blocker.pomodoro_long_break
                break_type = "Long Break"
            else:
                break_minutes = self.blocker.pomodoro_break
                break_type = "Short Break"

            if show_question(
                self, f"Work Complete! 🍅 {break_type}",
                f"Great work! Session #{self.pomodoro_session_count} complete!\n\n"
                f"Time for a {break_minutes}-minute {break_type.lower()}.\n\n"
                "Start break timer?"
            ) == QtWidgets.QMessageBox.Yes:
                self._start_pomodoro_break(break_minutes)
            else:
                self._end_pomodoro_session()

    def _start_pomodoro_work(self) -> None:
        """Start a Pomodoro work session."""
        work_minutes = self.blocker.pomodoro_work
        total_seconds = work_minutes * 60

        success, message = self.blocker.block_sites(duration_seconds=total_seconds)
        if not success:
            show_error(self, "Blocking Failed", message)
            self._end_pomodoro_session()
            return

        self.remaining_seconds = total_seconds
        self.timer_running = True
        self.session_start = QtCore.QDateTime.currentDateTime().toSecsSinceEpoch()
        self.pomodoro_is_break = False
        self.last_checkin_time = None

        self.timer_label.setText(self._format_time(self.remaining_seconds))
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText(f"🍅 WORK #{self.pomodoro_session_count + 1}")
        self.qt_timer.start()
        
        # Emit session started signal
        self.session_started.emit()

    def _start_pomodoro_break(self, break_minutes: int) -> None:
        """Start a Pomodoro break period."""
        total_seconds = break_minutes * 60

        self.remaining_seconds = total_seconds
        self.timer_running = True
        self.session_start = QtCore.QDateTime.currentDateTime().toSecsSinceEpoch()
        self.pomodoro_is_break = True

        self.timer_label.setText(self._format_time(self.remaining_seconds))
        self.status_label.setText("☕ BREAK")
        self.qt_timer.start()
        
        # Emit session started signal (breaks also lock controls)
        self.session_started.emit()

    def _end_pomodoro_session(self) -> None:
        """End the Pomodoro session completely."""
        session_minutes = self.pomodoro_total_work_time // 60

        self.timer_running = False
        self.qt_timer.stop()
        self.remaining_seconds = 0
        self.timer_label.setText("00:00:00")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pomodoro_is_break = False

        # Update tray icon to ready state
        main_window = self.window()
        if hasattr(main_window, '_update_tray_icon'):
            main_window._update_tray_icon(blocking=False)

        if self.pomodoro_session_count > 0:
            self.status_label.setText(
                f"🍅 Done! {self.pomodoro_session_count} sessions, "
                f"{self.pomodoro_total_work_time // 60} min"
            )
            if session_minutes > 0:
                self._show_priority_time_log(session_minutes)
        else:
            self.status_label.setText("Ready to focus")

        # Emit session complete signal to refresh stats
        if session_minutes > 0:
            self.session_complete.emit(session_minutes * 60)

        self.pomodoro_session_count = 0
        self.pomodoro_total_work_time = 0

    def _force_stop_session(self) -> None:
        """Force stop the session without password check (for app exit)."""
        elapsed = 0
        if self.session_start:
            elapsed = int(QtCore.QDateTime.currentDateTime().toSecsSinceEpoch() - self.session_start)

        self.timer_running = False
        self.qt_timer.stop()
        self.remaining_seconds = 0
        self.timer_label.setText("00:00:00")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Ready to focus")
        self.pomodoro_is_break = False
        self.pomodoro_session_count = 0
        self.pomodoro_total_work_time = 0

        # Update tray icon to ready state
        main_window = self.window()
        if hasattr(main_window, '_update_tray_icon'):
            main_window._update_tray_icon(blocking=False)

        # Unblock sites
        self.blocker.unblock_sites()

        # Record stats if ran > 60s
        if elapsed > 60:
            self.blocker.update_stats(elapsed, completed=False)
            self.session_complete.emit(elapsed)


class SitesTab(QtWidgets.QWidget):
    """Sites management tab - blacklist and whitelist."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.analyzer = ProductivityAnalyzer(blocker.stats_path) if ProductivityAnalyzer else None
        self.gamification = GamificationEngine(blocker.stats_path) if GamificationEngine else None
        self.focus_goals = FocusGoals(blocker.goals_path, blocker.stats_path) if FocusGoals else None
        self._build_ui()
        self._refresh_lists()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        # Blacklist section
        black_group = QtWidgets.QGroupBox("Blocked Sites (Custom)")
        black_layout = QtWidgets.QVBoxLayout(black_group)
        self.black_list = QtWidgets.QListWidget()
        self.black_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        black_layout.addWidget(self.black_list)

        black_input_layout = QtWidgets.QHBoxLayout()
        self.black_entry = QtWidgets.QLineEdit()
        self.black_entry.setPlaceholderText("Enter site to block...")
        self.black_entry.returnPressed.connect(self._add_black)
        black_input_layout.addWidget(self.black_entry)
        add_black_btn = QtWidgets.QPushButton("+ Add")
        add_black_btn.clicked.connect(self._add_black)
        black_input_layout.addWidget(add_black_btn)
        rem_black_btn = QtWidgets.QPushButton("- Remove")
        rem_black_btn.clicked.connect(self._remove_black)
        black_input_layout.addWidget(rem_black_btn)
        black_layout.addLayout(black_input_layout)
        layout.addWidget(black_group)

        # Whitelist section
        white_group = QtWidgets.QGroupBox("Whitelist (Never Block)")
        white_layout = QtWidgets.QVBoxLayout(white_group)
        self.white_list = QtWidgets.QListWidget()
        white_layout.addWidget(self.white_list)

        white_input_layout = QtWidgets.QHBoxLayout()
        self.white_entry = QtWidgets.QLineEdit()
        self.white_entry.setPlaceholderText("Enter site to whitelist...")
        self.white_entry.returnPressed.connect(self._add_white)
        white_input_layout.addWidget(self.white_entry)
        add_white_btn = QtWidgets.QPushButton("+ Add")
        add_white_btn.clicked.connect(self._add_white)
        white_input_layout.addWidget(add_white_btn)
        rem_white_btn = QtWidgets.QPushButton("- Remove")
        rem_white_btn.clicked.connect(self._remove_white)
        white_input_layout.addWidget(rem_white_btn)
        white_layout.addLayout(white_input_layout)
        layout.addWidget(white_group)

        # Import/Export buttons
        io_layout = QtWidgets.QHBoxLayout()
        import_btn = QtWidgets.QPushButton("📥 Import")
        import_btn.clicked.connect(self._import_sites)
        io_layout.addWidget(import_btn)
        export_btn = QtWidgets.QPushButton("📤 Export")
        export_btn.clicked.connect(self._export_sites)
        io_layout.addWidget(export_btn)
        io_layout.addStretch()
        layout.addLayout(io_layout)

    def _refresh_lists(self) -> None:
        self.black_list.clear()
        for site in sorted(self.blocker.blacklist):
            self.black_list.addItem(site)
        self.white_list.clear()
        for site in sorted(self.blocker.whitelist):
            self.white_list.addItem(site)

    def _add_black(self) -> None:
        site = self.black_entry.text().strip()
        if site and self.blocker.add_site(site):
            self._refresh_lists()
            self.black_entry.clear()

    def _remove_black(self) -> None:
        for item in self.black_list.selectedItems():
            self.blocker.remove_site(item.text())
        self._refresh_lists()

    def _add_white(self) -> None:
        site = self.white_entry.text().strip()
        if site and self.blocker.add_to_whitelist(site):
            self._refresh_lists()
            self.white_entry.clear()

    def _remove_white(self) -> None:
        for item in self.white_list.selectedItems():
            self.blocker.remove_from_whitelist(item.text())
        self._refresh_lists()

    def _import_sites(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Sites", "", "JSON Files (*.json)")
        if path and self.blocker.import_config(path):
            self._refresh_lists()
            show_info(self, "Import", "Sites imported successfully!")

    def _export_sites(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Sites", "", "JSON Files (*.json)")
        if path and self.blocker.export_config(path):
            show_info(self, "Export", "Sites exported successfully!")


class CategoriesTab(QtWidgets.QWidget):
    """Categories tab - toggle entire categories of sites."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.category_checks: Dict[str, QtWidgets.QCheckBox] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Enable/disable entire categories of sites:"))

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        cat_layout = QtWidgets.QVBoxLayout(container)

        for category, sites in SITE_CATEGORIES.items():
            row = QtWidgets.QHBoxLayout()
            cb = QtWidgets.QCheckBox(f"{category} ({len(sites)} sites)")
            cb.setChecked(self.blocker.categories_enabled.get(category, True))
            cb.stateChanged.connect(lambda state, c=category: self._toggle(c, state))
            self.category_checks[category] = cb
            row.addWidget(cb)
            view_btn = QtWidgets.QPushButton("View")
            view_btn.setFixedWidth(60)
            view_btn.clicked.connect(lambda _, c=category: self._show_sites(c))
            row.addWidget(view_btn)
            row.addStretch()
            cat_layout.addLayout(row)

        cat_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        self.total_label = QtWidgets.QLabel()
        layout.addWidget(self.total_label)
        self._update_total()

    def _toggle(self, category: str, state: int) -> None:
        self.blocker.categories_enabled[category] = (state == QtCore.Qt.Checked)
        self.blocker.save_config()
        self._update_total()

    def _show_sites(self, category: str) -> None:
        sites = SITE_CATEGORIES.get(category, [])
        text = "\n".join(sorted(set(s.replace("www.", "") for s in sites)))
        show_info(self, f"{category} Sites", text)

    def refresh(self) -> None:
        """Refresh checkboxes from blocker config."""
        for category, cb in self.category_checks.items():
            cb.setChecked(self.blocker.categories_enabled.get(category, True))
        self._update_total()

    def _update_total(self) -> None:
        total = len(self.blocker.get_effective_blacklist())
        self.total_label.setText(f"Total sites to block: {total}")


class ScheduleTab(QtWidgets.QWidget):
    """Schedule tab - automatic blocking schedules."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self._build_ui()
        self._refresh_table()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Automatic blocking schedules:"))

        # Schedule table
        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Days", "Time", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        layout.addWidget(self.table)

        # Add schedule form
        add_group = QtWidgets.QGroupBox("Add Schedule")
        add_layout = QtWidgets.QVBoxLayout(add_group)

        days_layout = QtWidgets.QHBoxLayout()
        days_layout.addWidget(QtWidgets.QLabel("Days:"))
        self.day_checks: list[QtWidgets.QCheckBox] = []
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, name in enumerate(day_names):
            cb = QtWidgets.QCheckBox(name)
            cb.setChecked(i < 5)  # default weekdays
            self.day_checks.append(cb)
            days_layout.addWidget(cb)
        days_layout.addStretch()
        add_layout.addLayout(days_layout)

        time_layout = QtWidgets.QHBoxLayout()
        time_layout.addWidget(QtWidgets.QLabel("From:"))
        self.start_time = QtWidgets.QTimeEdit(QtCore.QTime(9, 0))
        time_layout.addWidget(self.start_time)
        time_layout.addWidget(QtWidgets.QLabel("To:"))
        self.end_time = QtWidgets.QTimeEdit(QtCore.QTime(17, 0))
        time_layout.addWidget(self.end_time)
        time_layout.addStretch()
        add_layout.addLayout(time_layout)

        add_btn = QtWidgets.QPushButton("+ Add Schedule")
        add_btn.clicked.connect(self._add_schedule)
        add_layout.addWidget(add_btn)
        layout.addWidget(add_group)

        # Actions
        action_layout = QtWidgets.QHBoxLayout()
        toggle_btn = QtWidgets.QPushButton("Toggle")
        toggle_btn.clicked.connect(self._toggle_schedule)
        action_layout.addWidget(toggle_btn)
        delete_btn = QtWidgets.QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_schedule)
        action_layout.addWidget(delete_btn)
        action_layout.addStretch()
        layout.addLayout(action_layout)

    def _refresh_table(self) -> None:
        self.table.setRowCount(0)
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for sched in self.blocker.schedules:
            row = self.table.rowCount()
            self.table.insertRow(row)
            days_str = ", ".join(day_names[d] for d in sorted(sched.get("days", [])))
            time_str = f"{sched.get('start_time', '')} - {sched.get('end_time', '')}"
            status = "✅ Active" if sched.get("enabled", True) else "⏸ Paused"
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(days_str))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(time_str))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(status))
            # Store schedule id
            self.table.item(row, 0).setData(QtCore.Qt.UserRole, sched["id"])

    def _add_schedule(self) -> None:
        days = [i for i, cb in enumerate(self.day_checks) if cb.isChecked()]
        if not days:
            show_warning(self, "No Days Selected", "Please select at least one day for the schedule.")
            return
        start = self.start_time.time().toString("HH:mm")
        end = self.end_time.time().toString("HH:mm")
        self.blocker.add_schedule(days, start, end)
        self._refresh_table()

    def _selected_id(self) -> Optional[str]:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(QtCore.Qt.UserRole) if item else None

    def _toggle_schedule(self) -> None:
        sid = self._selected_id()
        if sid:
            self.blocker.toggle_schedule(sid)
            self._refresh_table()

    def _delete_schedule(self) -> None:
        sid = self._selected_id()
        if sid:
            self.blocker.remove_schedule(sid)
            self._refresh_table()


# ============================================================================
# PRODUCTIVITY ANALYTICS WIDGETS
# ============================================================================

class HourlyTimelineWidget(QtWidgets.QWidget):
    """
    Custom widget that renders a 24-hour timeline showing focus time distribution.
    Uses heatmap-style coloring with hour labels at 00:00-24:00.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hourly_data = [0.0] * 24  # Average minutes per hour
        self.setMinimumHeight(80)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    
    def set_data(self, hourly_data: list):
        """Set the hourly data (list of 24 floats representing avg minutes per hour)."""
        self.hourly_data = hourly_data[:24] if len(hourly_data) >= 24 else hourly_data + [0.0] * (24 - len(hourly_data))
        self.update()
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        rect = self.rect()
        margin_left = 30
        margin_right = 10
        margin_top = 15
        margin_bottom = 25
        
        chart_left = margin_left
        chart_right = rect.width() - margin_right
        chart_top = margin_top
        chart_bottom = rect.height() - margin_bottom
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        
        if chart_width < 50 or chart_height < 20:
            return
        
        # Background
        painter.fillRect(rect, QtGui.QColor("#333333"))
        
        # Find max value for scaling
        max_val = max(self.hourly_data) if max(self.hourly_data) > 0 else 1
        
        # Draw bars
        bar_width = chart_width / 24
        for hour, value in enumerate(self.hourly_data):
            x = chart_left + hour * bar_width
            
            # Calculate bar height
            bar_height = (value / max_val) * chart_height if max_val > 0 else 0
            
            # Calculate color intensity (gradient from dark to bright cyan/green)
            intensity = value / max_val if max_val > 0 else 0
            if intensity > 0.8:
                color = QtGui.QColor("#10b981")  # Bright green for peak
            elif intensity > 0.6:
                color = QtGui.QColor("#34d399")  # Medium green
            elif intensity > 0.4:
                color = QtGui.QColor("#6ee7b7")  # Light green
            elif intensity > 0.2:
                color = QtGui.QColor("#99f6e4")  # Very light cyan
            elif intensity > 0:
                color = QtGui.QColor("#5eead4")  # Light cyan
            else:
                color = QtGui.QColor("#374151")  # Dark gray for zero
            
            # Draw bar
            bar_rect = QtCore.QRectF(x + 1, chart_bottom - bar_height, bar_width - 2, bar_height)
            painter.fillRect(bar_rect, color)
            
            # Draw subtle border
            painter.setPen(QtGui.QPen(QtGui.QColor("#555"), 0.5))
            painter.drawRect(bar_rect)
        
        # Draw hour labels (every 3 hours)
        painter.setPen(QtGui.QColor("#9ca3af"))
        painter.setFont(QtGui.QFont("Arial", 8))
        for hour in range(0, 25, 3):
            x = chart_left + hour * bar_width
            if hour < 24:
                label = f"{hour:02d}"
            else:
                label = "24"
                x = chart_right
            painter.drawText(int(x - 8), chart_bottom + 15, label)
        
        # Draw "00:00" and "24:00" labels at edges
        painter.drawText(chart_left - 5, chart_bottom + 15, "00")
        
        # Draw Y-axis labels (max value)
        painter.setPen(QtGui.QColor("#6b7280"))
        if max_val > 0:
            painter.drawText(2, chart_top + 10, f"{int(max_val)}m")
        painter.drawText(2, chart_bottom, "0m")
        
        # Draw horizontal grid line at top
        painter.setPen(QtGui.QPen(QtGui.QColor("#444"), 1, QtCore.Qt.DashLine))
        painter.drawLine(chart_left, chart_top, chart_right, chart_top)


class DayOfWeekPatternWidget(QtWidgets.QWidget):
    """
    Custom widget showing day-of-week patterns with confidence intervals.
    Displays bars for each day with error bars showing 95% CI.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Data: [(mean, lower_ci, upper_ci) for each day Mon-Sun]
        self.dow_data = [(0.0, 0.0, 0.0)] * 7
        self.day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.setMinimumHeight(120)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    
    def set_data(self, dow_data: list):
        """Set day-of-week data: list of 7 tuples (mean, lower_ci, upper_ci)."""
        self.dow_data = dow_data[:7] if len(dow_data) >= 7 else dow_data + [(0.0, 0.0, 0.0)] * (7 - len(dow_data))
        self.update()
    
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        rect = self.rect()
        margin_left = 35
        margin_right = 10
        margin_top = 15
        margin_bottom = 30
        
        chart_left = margin_left
        chart_right = rect.width() - margin_right
        chart_top = margin_top
        chart_bottom = rect.height() - margin_bottom
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        
        if chart_width < 50 or chart_height < 30:
            return
        
        # Background
        painter.fillRect(rect, QtGui.QColor("#333333"))
        
        # Find max value for scaling (use upper CI bounds)
        max_val = max(d[2] for d in self.dow_data) if any(d[2] > 0 for d in self.dow_data) else 60
        max_val = max(max_val, 10)  # Minimum scale of 10 minutes
        
        # Draw bars with confidence intervals
        bar_width = chart_width / 7
        bar_inner_width = bar_width * 0.6
        
        for day_idx, (mean, lower_ci, upper_ci) in enumerate(self.dow_data):
            center_x = chart_left + day_idx * bar_width + bar_width / 2
            bar_left = center_x - bar_inner_width / 2
            
            # Calculate heights
            mean_height = (mean / max_val) * chart_height if max_val > 0 else 0
            lower_height = (lower_ci / max_val) * chart_height if max_val > 0 else 0
            upper_height = (upper_ci / max_val) * chart_height if max_val > 0 else 0
            
            # Determine bar color (gradient based on value)
            intensity = mean / max_val if max_val > 0 else 0
            if intensity > 0.8:
                bar_color = QtGui.QColor("#8b5cf6")  # Purple for highest
            elif intensity > 0.6:
                bar_color = QtGui.QColor("#a78bfa")
            elif intensity > 0.4:
                bar_color = QtGui.QColor("#c4b5fd")
            elif intensity > 0.2:
                bar_color = QtGui.QColor("#6366f1")  # Indigo
            else:
                bar_color = QtGui.QColor("#4f46e5")  # Darker indigo
            
            # Draw confidence interval (error bar)
            if upper_ci > lower_ci:
                ci_x = int(center_x)
                ci_top = int(chart_bottom - upper_height)
                ci_bottom = int(chart_bottom - lower_height)
                
                # Vertical line
                painter.setPen(QtGui.QPen(QtGui.QColor("#6b7280"), 2))
                painter.drawLine(ci_x, ci_top, ci_x, ci_bottom)
                
                # Horizontal caps
                cap_width = 4
                painter.drawLine(ci_x - cap_width, ci_top, ci_x + cap_width, ci_top)
                painter.drawLine(ci_x - cap_width, ci_bottom, ci_x + cap_width, ci_bottom)
            
            # Draw main bar
            bar_rect = QtCore.QRectF(bar_left, chart_bottom - mean_height, bar_inner_width, mean_height)
            painter.fillRect(bar_rect, bar_color)
            painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 0.5))
            painter.drawRect(bar_rect)
            
            # Draw value on top of bar
            if mean > 0:
                painter.setPen(QtGui.QColor("#e5e7eb"))
                painter.setFont(QtGui.QFont("Arial", 8, QtGui.QFont.Bold))
                value_text = f"{int(mean)}m" if mean < 60 else f"{mean/60:.1f}h"
                text_rect = QtCore.QRectF(bar_left - 5, chart_bottom - mean_height - 15, bar_inner_width + 10, 15)
                painter.drawText(text_rect, QtCore.Qt.AlignCenter, value_text)
        
        # Draw day labels
        painter.setPen(QtGui.QColor("#9ca3af"))
        painter.setFont(QtGui.QFont("Arial", 9))
        for day_idx, day_name in enumerate(self.day_names):
            center_x = chart_left + day_idx * bar_width + bar_width / 2
            text_rect = QtCore.QRectF(center_x - 20, chart_bottom + 5, 40, 20)
            painter.drawText(text_rect, QtCore.Qt.AlignCenter, day_name)
        
        # Draw Y-axis labels
        painter.setPen(QtGui.QColor("#6b7280"))
        painter.setFont(QtGui.QFont("Arial", 8))
        if max_val >= 60:
            painter.drawText(2, chart_top + 10, f"{max_val/60:.1f}h")
        else:
            painter.drawText(2, chart_top + 10, f"{int(max_val)}m")
        painter.drawText(2, chart_bottom, "0")
        
        # Draw horizontal grid lines
        painter.setPen(QtGui.QPen(QtGui.QColor("#444"), 1, QtCore.Qt.DashLine))
        painter.drawLine(chart_left, chart_top, chart_right, chart_top)
        mid_y = chart_top + chart_height / 2
        painter.drawLine(chart_left, int(mid_y), chart_right, int(mid_y))


class StatsTab(QtWidgets.QWidget):
    """Statistics tab - focus time, sessions, streaks, weekly chart."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        container = QtWidgets.QWidget()
        inner = QtWidgets.QVBoxLayout(container)
        inner.setSpacing(20)

        # Title
        title = QtWidgets.QLabel("📊 Focus Statistics")
        title.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #a5b4fc;
                padding: 8px;
                margin-bottom: 8px;
            }
        """)
        inner.addWidget(title)

        # AGI Assistant Chad Tips Section - hidden by default until entity is unlocked
        self.chad_tips_section = QtWidgets.QGroupBox()
        self.chad_tips_section.setStyleSheet("""
            QGroupBox {
                background: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
            }
        """)
        self.chad_tips_section.setVisible(False)  # Hidden until entity is unlocked
        
        chad_layout = QtWidgets.QVBoxLayout(self.chad_tips_section)
        chad_layout.setSpacing(12)
        
        # Chad section title
        self.chad_section_title = QtWidgets.QLabel("🤖 AGI Assistant Productivity Tips")
        self.chad_section_title.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        self.chad_section_title.setStyleSheet("color: #a5b4fc; padding: 4px;")
        chad_layout.addWidget(self.chad_section_title)
        
        # Entity card container (icon + name)
        chad_card_container = QtWidgets.QHBoxLayout()
        chad_card_container.setSpacing(12)
        
        # Entity icon (48x48)
        self.chad_icon_label = QtWidgets.QLabel()
        self.chad_icon_label.setFixedSize(48, 48)
        self.chad_icon_label.setAlignment(QtCore.Qt.AlignCenter)
        self.chad_icon_label.setStyleSheet("""
            QLabel {
                background: #333;
                border: 1px solid #444;
                border-radius: 6px;
            }
        """)
        chad_card_container.addWidget(self.chad_icon_label)
        
        # Entity name and tip number
        chad_info = QtWidgets.QVBoxLayout()
        self.chad_entity_name = QtWidgets.QLabel("AGI Assistant Chad")
        self.chad_entity_name.setStyleSheet("color: #e5e7eb; font-weight: bold; font-size: 12px;")
        chad_info.addWidget(self.chad_entity_name)
        
        self.chad_tip_number = QtWidgets.QLabel("Tip #1 of 100")
        self.chad_tip_number.setStyleSheet("color: #9ca3af; font-size: 10px;")
        chad_info.addWidget(self.chad_tip_number)
        
        chad_card_container.addLayout(chad_info)
        chad_card_container.addStretch()
        chad_layout.addLayout(chad_card_container)
        
        # Tip text display
        self.chad_tip_text = QtWidgets.QLabel("")
        self.chad_tip_text.setWordWrap(True)
        self.chad_tip_text.setStyleSheet("""
            QLabel {
                background: #333;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 12px;
                color: #e5e7eb;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        chad_layout.addWidget(self.chad_tip_text)
        
        # Acknowledge button
        self.chad_acknowledge_btn = QtWidgets.QPushButton("✓ Got it! (+1 🪙)")
        self.chad_acknowledge_btn.setStyleSheet("""
            QPushButton {
                background: #4ade80;
                color: #1a1a1a;
                border: none;
                border-radius: 4px;
                padding: 10px 18px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #22c55e;
            }
            QPushButton:disabled {
                background: #3d3d3d;
                color: #888;
            }
        """)
        self.chad_acknowledge_btn.clicked.connect(self._acknowledge_chad_tip)
        chad_layout.addWidget(self.chad_acknowledge_btn)
        
        inner.addWidget(self.chad_tips_section)

        # Overview cards - dark theme
        overview_group = QtWidgets.QGroupBox()
        overview_group.setStyleSheet("""
            QGroupBox {
                background: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
            }
        """)
        overview_layout = QtWidgets.QGridLayout(overview_group)
        overview_layout.setSpacing(12)
        
        # Create stat cards - dark theme
        def create_stat_card(icon: str, label_text: str, value_widget, color: str) -> QtWidgets.QWidget:
            card = QtWidgets.QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: #333333;
                    border: 1px solid #444444;
                    border-radius: 8px;
                    padding: 12px;
                }}
            """)
            card_layout = QtWidgets.QVBoxLayout(card)
            card_layout.setSpacing(6)
            
            label = QtWidgets.QLabel(f"{icon} {label_text}")
            label.setFont(QtGui.QFont("Arial", 9))
            label.setStyleSheet("color: #9ca3af; font-weight: 500;")
            card_layout.addWidget(label)
            
            value_widget.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Bold))
            value_widget.setStyleSheet(f"color: #e5e7eb; padding: 4px;")
            value_widget.setAlignment(QtCore.Qt.AlignCenter)
            card_layout.addWidget(value_widget)
            
            return card
        
        self.total_hours_lbl = QtWidgets.QLabel("0h")
        self.sessions_lbl = QtWidgets.QLabel("0")
        self.streak_lbl = QtWidgets.QLabel("0 days")
        self.best_streak_lbl = QtWidgets.QLabel("0 days")
        
        overview_layout.addWidget(
            create_stat_card("⏱️", "Total Focus Time", self.total_hours_lbl, "#2196f3"), 0, 0
        )
        overview_layout.addWidget(
            create_stat_card("✅", "Sessions Completed", self.sessions_lbl, "#4caf50"), 0, 1
        )
        overview_layout.addWidget(
            create_stat_card("🔥", "Current Streak", self.streak_lbl, "#ff9800"), 1, 0
        )
        overview_layout.addWidget(
            create_stat_card("🏆", "Best Streak", self.best_streak_lbl, "#9c27b0"), 1, 1
        )
        inner.addWidget(overview_group)

        # Focus goals dashboard - dark theme
        goals_group = QtWidgets.QGroupBox()
        goals_group.setStyleSheet("""
            QGroupBox {
                background: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 16px;
                margin-top: 8px;
            }
        """)
        goals_layout = QtWidgets.QVBoxLayout(goals_group)
        goals_layout.setSpacing(12)
        
        # Goals title
        goals_title = QtWidgets.QLabel("🎯 Focus Goals")
        goals_title.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        goals_title.setStyleSheet("color: #a5b4fc; padding: 4px;")
        goals_layout.addWidget(goals_title)

        # Weekly goal - dark theme
        weekly_card = QtWidgets.QFrame()
        weekly_card.setStyleSheet("""
            QFrame {
                background: #333333;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        weekly_layout = QtWidgets.QVBoxLayout(weekly_card)
        weekly_layout.setSpacing(6)
        
        weekly_label = QtWidgets.QLabel("📅 Weekly Goal")
        weekly_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        weekly_label.setStyleSheet("color: #93c5fd;")
        weekly_layout.addWidget(weekly_label)
        
        self.weekly_bar = QtWidgets.QProgressBar()
        self.weekly_bar.setMaximum(100)
        self.weekly_bar.setTextVisible(True)
        self.weekly_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                text-align: center;
                background: #2a2a2a;
                height: 24px;
                color: #e5e7eb;
            }
            QProgressBar::chunk {
                background: #6366f1;
                border-radius: 3px;
            }
        """)
        weekly_layout.addWidget(self.weekly_bar)
        
        weekly_controls = QtWidgets.QHBoxLayout()
        target_lbl = QtWidgets.QLabel("Target:")
        target_lbl.setStyleSheet("color: #9ca3af;")
        weekly_controls.addWidget(target_lbl)
        self.weekly_target = QtWidgets.QDoubleSpinBox()
        self.weekly_target.setRange(1, 200)
        self.weekly_target.setSuffix(" h")
        self.weekly_target.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 4px;
                min-width: 80px;
                background: #2a2a2a;
                color: #e5e7eb;
            }
        """)
        try:
            self.weekly_target.setValue(float(self.blocker.stats.get("weekly_goal_hours", 10)))
        except (ValueError, TypeError):
            self.weekly_target.setValue(10.0)
        weekly_controls.addWidget(self.weekly_target)
        
        weekly_set = QtWidgets.QPushButton("Set Goal")
        weekly_set.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #4f46e5;
            }
        """)
        weekly_set.clicked.connect(self._set_weekly_goal)
        weekly_controls.addWidget(weekly_set)
        weekly_controls.addStretch()
        weekly_layout.addLayout(weekly_controls)
        goals_layout.addWidget(weekly_card)

        # Monthly goal - dark theme
        monthly_card = QtWidgets.QFrame()
        monthly_card.setStyleSheet("""
            QFrame {
                background: #333333;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        monthly_layout = QtWidgets.QVBoxLayout(monthly_card)
        monthly_layout.setSpacing(6)
        
        monthly_label = QtWidgets.QLabel("📆 Monthly Goal")
        monthly_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        monthly_label.setStyleSheet("color: #c4b5fd;")
        monthly_layout.addWidget(monthly_label)
        
        self.monthly_bar = QtWidgets.QProgressBar()
        self.monthly_bar.setMaximum(100)
        self.monthly_bar.setTextVisible(True)
        self.monthly_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                text-align: center;
                background: #2a2a2a;
                height: 24px;
                color: #e5e7eb;
            }
            QProgressBar::chunk {
                background: #8b5cf6;
                border-radius: 3px;
            }
        """)
        monthly_layout.addWidget(self.monthly_bar)
        
        monthly_controls = QtWidgets.QHBoxLayout()
        target_lbl2 = QtWidgets.QLabel("Target:")
        target_lbl2.setStyleSheet("color: #9ca3af;")
        monthly_controls.addWidget(target_lbl2)
        self.monthly_target = QtWidgets.QDoubleSpinBox()
        self.monthly_target.setRange(1, 1000)
        self.monthly_target.setSuffix(" h")
        self.monthly_target.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 4px;
                min-width: 80px;
                background: #2a2a2a;
                color: #e5e7eb;
            }
        """)
        try:
            self.monthly_target.setValue(float(self.blocker.stats.get("monthly_goal_hours", 40)))
        except (ValueError, TypeError):
            self.monthly_target.setValue(40.0)
        monthly_controls.addWidget(self.monthly_target)
        
        monthly_set = QtWidgets.QPushButton("Set Goal")
        monthly_set.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)
        monthly_set.clicked.connect(self._set_monthly_goal)
        monthly_controls.addWidget(monthly_set)
        monthly_controls.addStretch()
        monthly_layout.addLayout(monthly_controls)
        goals_layout.addWidget(monthly_card)

        inner.addWidget(goals_group)

        # Weekly chart - dark theme
        week_group = QtWidgets.QGroupBox()
        week_group.setStyleSheet("""
            QGroupBox {
                background: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 12px;
                margin-top: 8px;
            }
        """)
        week_layout = QtWidgets.QVBoxLayout(week_group)
        week_layout.setSpacing(6)
        
        week_title = QtWidgets.QLabel("📊 Weekly Focus Time")
        week_title.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        week_title.setStyleSheet("color: #a5b4fc; padding: 0px 0px 4px 0px;")
        week_layout.addWidget(week_title)
        
        # Store weekly progress bars
        self.week_bars = {}
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day in days:
            day_layout = QtWidgets.QHBoxLayout()
            day_layout.setSpacing(8)
            
            day_label = QtWidgets.QLabel(day)
            day_label.setFixedWidth(35)
            day_label.setStyleSheet("color: #9ca3af; font-weight: 500;")
            day_layout.addWidget(day_label)
            
            progress = QtWidgets.QProgressBar()
            progress.setMaximum(100)
            progress.setValue(0)
            progress.setTextVisible(True)
            progress.setFixedHeight(18)
            progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #444444;
                    border-radius: 3px;
                    background: #333333;
                    text-align: center;
                    color: #e5e7eb;
                    font-size: 10px;
                }
                QProgressBar::chunk {
                    background: #10b981;
                    border-radius: 2px;
                }
            """)
            day_layout.addWidget(progress, 1)
            
            week_layout.addLayout(day_layout)
            self.week_bars[day] = progress
        
        # Total summary
        self.week_total_label = QtWidgets.QLabel("")
        self.week_total_label.setStyleSheet("""
            color: #e5e7eb;
            font-weight: 500;
            padding: 6px 0px 0px 0px;
            border-top: 1px solid #444444;
            margin-top: 4px;
        """)
        week_layout.addWidget(self.week_total_label)
        
        inner.addWidget(week_group)

        # ═══════════════════════════════════════════════════════════════════════
        # PRODUCTIVITY ANALYTICS SECTION - State-of-the-art visualization
        # ═══════════════════════════════════════════════════════════════════════
        
        analytics_group = QtWidgets.QGroupBox()
        analytics_group.setStyleSheet("""
            QGroupBox {
                background: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 12px;
                margin-top: 8px;
            }
        """)
        analytics_layout = QtWidgets.QVBoxLayout(analytics_group)
        analytics_layout.setSpacing(12)
        
        # Analytics header with period selector
        analytics_header = QtWidgets.QHBoxLayout()
        analytics_title = QtWidgets.QLabel("📈 Productivity Analytics")
        analytics_title.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        analytics_title.setStyleSheet("color: #a5b4fc; padding: 4px;")
        analytics_header.addWidget(analytics_title)
        analytics_header.addStretch()
        
        # Period selector
        period_label = QtWidgets.QLabel("Period:")
        period_label.setStyleSheet("color: #9ca3af;")
        analytics_header.addWidget(period_label)
        
        self.analytics_period = NoScrollComboBox()
        self.analytics_period.addItem("Last 7 Days", 7)
        self.analytics_period.addItem("Last 30 Days", 30)
        self.analytics_period.addItem("Last 60 Days", 60)
        self.analytics_period.addItem("Last 6 Months", 180)
        self.analytics_period.addItem("Lifetime", -1)
        self.analytics_period.setCurrentIndex(1)  # Default: 30 days
        self.analytics_period.setStyleSheet("""
            QComboBox {
                background: #333;
                color: #e5e7eb;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #333;
                color: #e5e7eb;
                selection-background-color: #4f46e5;
            }
        """)
        self.analytics_period.currentIndexChanged.connect(self._refresh_analytics)
        analytics_header.addWidget(self.analytics_period)
        analytics_layout.addLayout(analytics_header)
        
        # 24-Hour Timeline Section
        timeline_card = QtWidgets.QFrame()
        timeline_card.setStyleSheet("""
            QFrame {
                background: #333333;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        timeline_layout = QtWidgets.QVBoxLayout(timeline_card)
        timeline_layout.setSpacing(8)
        
        timeline_title = QtWidgets.QLabel("🕐 24-Hour Focus Timeline")
        timeline_title.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        timeline_title.setStyleSheet("color: #93c5fd;")
        timeline_layout.addWidget(timeline_title)
        
        timeline_subtitle = QtWidgets.QLabel("Average focus time by hour of day")
        timeline_subtitle.setStyleSheet("color: #6b7280; font-size: 10px;")
        timeline_layout.addWidget(timeline_subtitle)
        
        # Timeline canvas widget
        self.timeline_canvas = HourlyTimelineWidget()
        self.timeline_canvas.setMinimumHeight(100)
        self.timeline_canvas.setMaximumHeight(120)
        timeline_layout.addWidget(self.timeline_canvas)
        
        # Peak hours label
        self.peak_hours_label = QtWidgets.QLabel("Peak productivity: -")
        self.peak_hours_label.setStyleSheet("color: #10b981; font-size: 10px; font-weight: 500;")
        timeline_layout.addWidget(self.peak_hours_label)
        
        analytics_layout.addWidget(timeline_card)
        
        # Day-of-Week Pattern Analysis with Confidence Intervals
        dow_card = QtWidgets.QFrame()
        dow_card.setStyleSheet("""
            QFrame {
                background: #333333;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        dow_layout = QtWidgets.QVBoxLayout(dow_card)
        dow_layout.setSpacing(8)
        
        dow_title = QtWidgets.QLabel("📅 Weekly Productivity Patterns")
        dow_title.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        dow_title.setStyleSheet("color: #c4b5fd;")
        dow_layout.addWidget(dow_title)
        
        dow_subtitle = QtWidgets.QLabel("Average focus time per day of week (with 95% confidence intervals)")
        dow_subtitle.setStyleSheet("color: #6b7280; font-size: 10px;")
        dow_layout.addWidget(dow_subtitle)
        
        # Day of week canvas
        self.dow_canvas = DayOfWeekPatternWidget()
        self.dow_canvas.setMinimumHeight(140)
        self.dow_canvas.setMaximumHeight(160)
        dow_layout.addWidget(self.dow_canvas)
        
        # Best/worst day labels
        self.best_day_label = QtWidgets.QLabel("Most productive: -")
        self.best_day_label.setStyleSheet("color: #10b981; font-size: 10px; font-weight: 500;")
        dow_layout.addWidget(self.best_day_label)
        
        self.worst_day_label = QtWidgets.QLabel("Least productive: -")
        self.worst_day_label.setStyleSheet("color: #f87171; font-size: 10px; font-weight: 500;")
        dow_layout.addWidget(self.worst_day_label)
        
        analytics_layout.addWidget(dow_card)
        
        # Statistics summary card
        stats_summary_card = QtWidgets.QFrame()
        stats_summary_card.setStyleSheet("""
            QFrame {
                background: #333333;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        stats_summary_layout = QtWidgets.QVBoxLayout(stats_summary_card)
        
        stats_summary_title = QtWidgets.QLabel("📊 Statistical Summary")
        stats_summary_title.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        stats_summary_title.setStyleSheet("color: #fbbf24;")
        stats_summary_layout.addWidget(stats_summary_title)
        
        # Grid of statistics
        stats_grid = QtWidgets.QGridLayout()
        stats_grid.setSpacing(8)
        
        # Create stat labels
        def create_mini_stat(label_text: str, color: str) -> tuple:
            container = QtWidgets.QWidget()
            container_layout = QtWidgets.QVBoxLayout(container)
            container_layout.setContentsMargins(4, 4, 4, 4)
            container_layout.setSpacing(2)
            
            value_lbl = QtWidgets.QLabel("-")
            value_lbl.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
            value_lbl.setStyleSheet(f"color: {color};")
            value_lbl.setAlignment(QtCore.Qt.AlignCenter)
            container_layout.addWidget(value_lbl)
            
            label = QtWidgets.QLabel(label_text)
            label.setStyleSheet("color: #6b7280; font-size: 9px;")
            label.setAlignment(QtCore.Qt.AlignCenter)
            container_layout.addWidget(label)
            
            return container, value_lbl
        
        # Row 1: Productivity Score, Total Time, Sessions, Avg/day
        c0, self.stat_productivity_score = create_mini_stat("Score", "#10b981")
        c1, self.stat_total_time = create_mini_stat("Total Time", "#60a5fa")
        c2, self.stat_total_sessions = create_mini_stat("Sessions", "#34d399")
        c3, self.stat_avg_daily = create_mini_stat("Avg/Day", "#a78bfa")
        
        stats_grid.addWidget(c0, 0, 0)
        stats_grid.addWidget(c1, 0, 1)
        stats_grid.addWidget(c2, 0, 2)
        stats_grid.addWidget(c3, 0, 3)
        
        # Row 2: Consistency, Deep Work %, Avg Session, Goal Rate
        c4, self.stat_consistency = create_mini_stat("Consistency", "#fbbf24")
        c5, self.stat_deep_work = create_mini_stat("Deep Work", "#f472b6")
        c6, self.stat_avg_session = create_mini_stat("Avg Session", "#2dd4bf")
        c7, self.stat_goal_rate = create_mini_stat("Goal Rate", "#fb923c")
        
        stats_grid.addWidget(c4, 1, 0)
        stats_grid.addWidget(c5, 1, 1)
        stats_grid.addWidget(c6, 1, 2)
        stats_grid.addWidget(c7, 1, 3)
        
        # Row 3: Active Days, Best Day, Std Dev, Trend
        c8, self.stat_active_days = create_mini_stat("Active Days", "#818cf8")
        c9, self.stat_max_day = create_mini_stat("Best Day", "#f97316")
        c10, self.stat_std_dev = create_mini_stat("Variability", "#94a3b8")
        c11, self.stat_trend = create_mini_stat("Trend", "#22d3ee")
        
        stats_grid.addWidget(c8, 2, 0)
        stats_grid.addWidget(c9, 2, 1)
        stats_grid.addWidget(c10, 2, 2)
        stats_grid.addWidget(c11, 2, 3)
        
        # Row 4: Week-over-week change
        wow_container = QtWidgets.QWidget()
        wow_layout = QtWidgets.QHBoxLayout(wow_container)
        wow_layout.setContentsMargins(4, 8, 4, 4)
        wow_layout.setSpacing(12)
        
        self.stat_wow_label = QtWidgets.QLabel("📈 Week-over-Week:")
        self.stat_wow_label.setStyleSheet("color: #9ca3af; font-size: 10px;")
        wow_layout.addWidget(self.stat_wow_label)
        
        self.stat_wow_value = QtWidgets.QLabel("-")
        self.stat_wow_value.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        self.stat_wow_value.setStyleSheet("color: #22d3ee;")
        wow_layout.addWidget(self.stat_wow_value)
        
        self.stat_vs_avg_label = QtWidgets.QLabel("   vs. Period Avg:")
        self.stat_vs_avg_label.setStyleSheet("color: #9ca3af; font-size: 10px;")
        wow_layout.addWidget(self.stat_vs_avg_label)
        
        self.stat_vs_avg_value = QtWidgets.QLabel("-")
        self.stat_vs_avg_value.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
        self.stat_vs_avg_value.setStyleSheet("color: #a78bfa;")
        wow_layout.addWidget(self.stat_vs_avg_value)
        
        wow_layout.addStretch()
        stats_grid.addWidget(wow_container, 3, 0, 1, 4)
        
        stats_summary_layout.addLayout(stats_grid)
        analytics_layout.addWidget(stats_summary_card)
        
        inner.addWidget(analytics_group)

        # Distraction attempts (bypass) - dark theme
        if BYPASS_LOGGER_AVAILABLE:
            bypass_group = QtWidgets.QGroupBox()
            bypass_group.setStyleSheet("""
                QGroupBox {
                    background: #2a2a2a;
                    border: 1px solid #3d3d3d;
                    border-radius: 8px;
                    padding: 16px;
                    margin-top: 8px;
                }
            """)
            bypass_layout = QtWidgets.QVBoxLayout(bypass_group)
            bypass_layout.setSpacing(10)
            
            bypass_title = QtWidgets.QLabel("🚫 Distraction Attempts")
            bypass_title.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
            bypass_title.setStyleSheet("color: #fca5a5; padding: 4px;")
            bypass_layout.addWidget(bypass_title)
            
            # Session stats card
            session_card = QtWidgets.QFrame()
            session_card.setStyleSheet("""
                QFrame {
                    background: #3d2a2a;
                    border: 1px solid #5c4444;
                    border-radius: 6px;
                    padding: 10px;
                }
            """)
            session_layout = QtWidgets.QVBoxLayout(session_card)
            
            self.bypass_session_label = QtWidgets.QLabel("Current Session: 0 attempts")
            self.bypass_session_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
            self.bypass_session_label.setStyleSheet("color: #f87171;")
            session_layout.addWidget(self.bypass_session_label)
            
            self.bypass_session_sites = QtWidgets.QLabel("No sites accessed")
            self.bypass_session_sites.setStyleSheet("color: #9ca3af; padding-left: 8px;")
            session_layout.addWidget(self.bypass_session_sites)
            bypass_layout.addWidget(session_card)
            
            # Overall stats card
            overall_card = QtWidgets.QFrame()
            overall_card.setStyleSheet("""
                QFrame {
                    background: #333333;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    padding: 10px;
                }
            """)
            overall_layout = QtWidgets.QVBoxLayout(overall_card)

            self.bypass_total_label = QtWidgets.QLabel("Total attempts: 0")
            self.bypass_total_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
            self.bypass_total_label.setStyleSheet("color: #e5e7eb;")
            overall_layout.addWidget(self.bypass_total_label)
            
            self.bypass_top_sites = QtWidgets.QLabel("Top distractions: -")
            self.bypass_top_sites.setStyleSheet("padding-left: 8px; color: #9ca3af;")
            overall_layout.addWidget(self.bypass_top_sites)
            
            self.bypass_peak_hours = QtWidgets.QLabel("Peak hours: -")
            self.bypass_peak_hours.setStyleSheet("padding-left: 8px; color: #9ca3af;")
            overall_layout.addWidget(self.bypass_peak_hours)
            bypass_layout.addWidget(overall_card)

            # Insights
            self.bypass_insights = QtWidgets.QTextEdit()
            self.bypass_insights.setReadOnly(True)
            self.bypass_insights.setMaximumHeight(70)
            self.bypass_insights.setStyleSheet("""
                QTextEdit {
                    background: #3d3a2a;
                    border: 1px solid #5c5944;
                    border-radius: 6px;
                    padding: 8px;
                    color: #fbbf24;
                }
            """)
            bypass_layout.addWidget(self.bypass_insights)

            refresh_bypass = QtWidgets.QPushButton("🔄 Refresh Attempts")
            refresh_bypass.setStyleSheet("""
                QPushButton {
                    background: #ef4444;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: #dc2626;
                }
            """)
            refresh_bypass.clicked.connect(self._refresh_bypass_stats)
            bypass_layout.addWidget(refresh_bypass)

            inner.addWidget(bypass_group)

        # Reset button - dark theme
        reset_btn = QtWidgets.QPushButton("🔄 Reset All Statistics")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #4b5563;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 18px;
                font-weight: 500;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #374151;
            }
        """)
        reset_btn.clicked.connect(self._reset_stats)
        inner.addWidget(reset_btn)

        inner.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def refresh(self) -> None:
        from datetime import datetime, timedelta
        stats = self.blocker.get_stats_summary()
        self.total_hours_lbl.setText(f"{stats['total_hours']}h")
        self.sessions_lbl.setText(str(stats["sessions_completed"]))
        self.streak_lbl.setText(f"{stats['current_streak']} days")
        self.best_streak_lbl.setText(f"{stats['best_streak']} days")

        # Goals progress
        try:
            weekly_target = float(self.blocker.stats.get("weekly_goal_hours", 10))
        except (ValueError, TypeError):
            weekly_target = 10.0
        try:
            monthly_target = float(self.blocker.stats.get("monthly_goal_hours", 40))
        except (ValueError, TypeError):
            monthly_target = 40.0
        weekly_minutes = self._sum_focus_minutes(7)
        monthly_minutes = self._sum_focus_minutes(30)

        weekly_pct = 0 if weekly_target <= 0 else min(100, int((weekly_minutes / 60) / weekly_target * 100))
        monthly_pct = 0 if monthly_target <= 0 else min(100, int((monthly_minutes / 60) / monthly_target * 100))

        self.weekly_bar.setFormat(f"{weekly_minutes/60:.1f}h / {weekly_target:.0f}h ({weekly_pct}%)")
        self.weekly_bar.setValue(weekly_pct)
        self.monthly_bar.setFormat(f"{monthly_minutes/60:.1f}h / {monthly_target:.0f}h ({monthly_pct}%)")
        self.monthly_bar.setValue(monthly_pct)

        # Weekly chart with graphical bars
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        today = datetime.now()
        week_data = {}
        max_time = 1
        total_week = 0
        
        for i in range(6, -1, -1):
            date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = days[dt.weekday()]
            daily = self.blocker.stats.get("daily_stats", {}).get(date_str, {})
            time_min = daily.get("focus_time", 0) // 60
            week_data[day_name] = time_min
            max_time = max(max_time, time_min)
            total_week += time_min

        # Update each day's progress bar
        for day in days:
            time_min = week_data.get(day, 0)
            percentage = int((time_min / max_time) * 100) if max_time > 0 else 0
            bar = self.week_bars.get(day)
            if bar:
                bar.setValue(percentage)
                hours = time_min // 60
                mins = time_min % 60
                if hours > 0:
                    bar.setFormat(f"{hours}h {mins}m")
                else:
                    bar.setFormat(f"{mins}m")
        
        # Update total
        total_hours = total_week // 60
        total_mins = total_week % 60
        self.week_total_label.setText(f"Total: {total_hours}h {total_mins}m")

        if BYPASS_LOGGER_AVAILABLE:
            self._refresh_bypass_stats()
        
        # Refresh productivity analytics
        self._refresh_analytics()
        
        # Refresh AGI Assistant Chad tips
        self._refresh_chad_tips()

    def _sum_focus_minutes(self, days_back: int) -> int:
        from datetime import datetime, timedelta

        total = 0
        today = datetime.now()
        for i in range(days_back):
            date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            daily = self.blocker.stats.get("daily_stats", {}).get(date_str, {})
            total += daily.get("focus_time", 0) // 60
        return total

    def _set_weekly_goal(self) -> None:
        self.blocker.stats["weekly_goal_hours"] = float(self.weekly_target.value())
        self.blocker.save_stats()
        self.refresh()

    def _set_monthly_goal(self) -> None:
        self.blocker.stats["monthly_goal_hours"] = float(self.monthly_target.value())
        self.blocker.save_stats()
        self.refresh()

    def _refresh_bypass_stats(self) -> None:
        if not BYPASS_LOGGER_AVAILABLE:
            return
        stats = self.blocker.get_bypass_statistics()
        if not stats:
            return

        session_count = stats.get("current_session", 0)
        session_sites = stats.get("session_sites", [])
        self.bypass_session_label.setText(f"Current Session: {session_count} attempts")
        if session_sites:
            sites_text = ", ".join(session_sites[:5])
            if len(session_sites) > 5:
                sites_text += f" (+{len(session_sites) - 5} more)"
            self.bypass_session_sites.setText(f"Sites: {sites_text}")
        else:
            self.bypass_session_sites.setText("No sites accessed")

        self.bypass_total_label.setText(f"Total attempts: {stats.get('total_attempts', 0)}")
        top_sites = stats.get("top_sites", [])[:3]
        if top_sites:
            self.bypass_top_sites.setText(
                "Top distractions: " + ", ".join(f"{s} ({c})" for s, c in top_sites)
            )
        else:
            self.bypass_top_sites.setText("Top distractions: -")

        peak_hours = stats.get("peak_hours", [])[:3]
        if peak_hours:
            self.bypass_peak_hours.setText(
                "Peak hours: " + ", ".join(f"{int(h)}:00" for h, _ in peak_hours)
            )
        else:
            self.bypass_peak_hours.setText("Peak hours: -")

        insights = self.blocker.get_bypass_insights()
        if insights:
            self.bypass_insights.setPlainText("\n".join(insights))
        else:
            self.bypass_insights.setPlainText("No insights yet. Keep focusing!")

    def _refresh_analytics(self) -> None:
        """Refresh the productivity analytics section with statistical analysis."""
        from datetime import datetime, timedelta
        import math
        
        # Get selected period
        period_days = self.analytics_period.currentData()
        
        # Collect daily stats for the period
        daily_stats = self.blocker.stats.get("daily_stats", {})
        today = datetime.now()
        
        # Filter dates within period
        if period_days == -1:  # Lifetime
            relevant_dates = sorted(daily_stats.keys())
        else:
            cutoff = today - timedelta(days=period_days)
            relevant_dates = [d for d in daily_stats.keys() 
                            if datetime.strptime(d, "%Y-%m-%d") >= cutoff]
        
        # ═══════════════════════════════════════════════════════════════════
        # 24-HOUR TIMELINE ANALYSIS
        # ═══════════════════════════════════════════════════════════════════
        
        hourly_totals = [0.0] * 24
        hourly_counts = [0] * 24
        
        for date_str in relevant_dates:
            day_data = daily_stats.get(date_str, {})
            hourly = day_data.get("hourly", {})
            for hour_str, seconds in hourly.items():
                try:
                    hour = int(hour_str)
                    if 0 <= hour < 24:
                        hourly_totals[hour] += seconds / 60  # Convert to minutes
                        hourly_counts[hour] += 1
                except ValueError:
                    pass
        
        # Calculate averages
        hourly_averages = [
            hourly_totals[h] / max(hourly_counts[h], 1) 
            for h in range(24)
        ]
        
        # Update timeline widget
        self.timeline_canvas.set_data(hourly_averages)
        
        # Find peak hours
        peak_hours = sorted(enumerate(hourly_averages), key=lambda x: x[1], reverse=True)[:3]
        if peak_hours[0][1] > 0:
            peak_text = ", ".join([f"{h:02d}:00 ({m:.0f}m)" for h, m in peak_hours if m > 0])
            self.peak_hours_label.setText(f"🔥 Peak productivity: {peak_text}")
        else:
            self.peak_hours_label.setText("Peak productivity: No data yet")
        
        # ═══════════════════════════════════════════════════════════════════
        # DAY-OF-WEEK PATTERN ANALYSIS WITH CONFIDENCE INTERVALS
        # ═══════════════════════════════════════════════════════════════════
        
        # Collect data by day of week
        dow_data = {i: [] for i in range(7)}  # 0=Monday, 6=Sunday
        
        for date_str in relevant_dates:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                day_of_week = dt.weekday()
                day_data = daily_stats.get(date_str, {})
                focus_minutes = day_data.get("focus_time", 0) / 60
                dow_data[day_of_week].append(focus_minutes)
            except ValueError:
                pass
        
        # Calculate statistics with 95% confidence intervals
        dow_stats = []
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for dow in range(7):
            values = dow_data[dow]
            if len(values) > 1:
                n = len(values)
                mean = sum(values) / n
                variance = sum((x - mean) ** 2 for x in values) / (n - 1) if n > 1 else 0
                std_dev = math.sqrt(variance)
                std_error = std_dev / math.sqrt(n)
                
                # 95% CI using t-distribution approximation (z ≈ 1.96 for large n)
                # For small n, use t-value (approximation)
                if n >= 30:
                    t_value = 1.96
                elif n >= 10:
                    t_value = 2.228
                else:
                    t_value = 2.571
                
                margin = t_value * std_error
                lower_ci = max(0, mean - margin)
                upper_ci = mean + margin
                dow_stats.append((mean, lower_ci, upper_ci))
            elif len(values) == 1:
                dow_stats.append((values[0], values[0], values[0]))
            else:
                dow_stats.append((0.0, 0.0, 0.0))
        
        # Update DOW widget
        self.dow_canvas.set_data(dow_stats)
        
        # Find best and worst days
        valid_days = [(i, dow_stats[i][0]) for i in range(7) if dow_stats[i][0] > 0]
        if valid_days:
            best_day_idx = max(valid_days, key=lambda x: x[1])[0]
            worst_day_idx = min(valid_days, key=lambda x: x[1])[0]
            best_mean = dow_stats[best_day_idx][0]
            worst_mean = dow_stats[worst_day_idx][0]
            
            if best_mean >= 60:
                self.best_day_label.setText(f"🏆 Most productive: {day_names[best_day_idx]} ({best_mean/60:.1f}h avg)")
            else:
                self.best_day_label.setText(f"🏆 Most productive: {day_names[best_day_idx]} ({best_mean:.0f}m avg)")
            
            if worst_mean >= 60:
                self.worst_day_label.setText(f"📉 Least productive: {day_names[worst_day_idx]} ({worst_mean/60:.1f}h avg)")
            else:
                self.worst_day_label.setText(f"📉 Least productive: {day_names[worst_day_idx]} ({worst_mean:.0f}m avg)")
        else:
            self.best_day_label.setText("🏆 Most productive: -")
            self.worst_day_label.setText("📉 Least productive: -")
        
        # ═══════════════════════════════════════════════════════════════════
        # STATISTICAL SUMMARY (Industry-Standard Metrics)
        # ═══════════════════════════════════════════════════════════════════
        
        # Collect all daily focus times and session details
        all_daily_focus = []
        total_sessions = 0
        session_lengths = []  # Individual session lengths for analysis
        deep_work_sessions = 0  # Sessions >= 45 minutes
        
        for date_str in relevant_dates:
            day_data = daily_stats.get(date_str, {})
            focus_min = day_data.get("focus_time", 0) / 60
            sessions = day_data.get("sessions", 0)
            all_daily_focus.append(focus_min)
            total_sessions += sessions
            
            # Estimate average session length for this day
            if sessions > 0:
                avg_session_this_day = focus_min / sessions
                session_lengths.append(avg_session_this_day)
                # Count deep work (assume session >= 45min is deep work)
                if avg_session_this_day >= 45:
                    deep_work_sessions += sessions
        
        # Calculate core statistics
        total_focus = sum(all_daily_focus)
        active_days = len([f for f in all_daily_focus if f > 0])
        num_days = len(all_daily_focus) if all_daily_focus else 1
        
        avg_daily = total_focus / num_days if num_days > 0 else 0
        
        if len(all_daily_focus) > 1:
            variance = sum((x - avg_daily) ** 2 for x in all_daily_focus) / (len(all_daily_focus) - 1)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0
        
        max_day = max(all_daily_focus) if all_daily_focus else 0
        
        # ───────────────────────────────────────────────────────────────────
        # INDUSTRY-STANDARD METRICS
        # ───────────────────────────────────────────────────────────────────
        
        # 1. PRODUCTIVITY SCORE (0-100)
        # Composite score based on: consistency, avg focus, trend, goal achievement
        # Industry standard: RescueTime uses similar composite scoring
        
        # Normalize avg daily (assume 120min/day = 100% baseline for solo productivity)
        daily_target = 120  # 2 hours of focused work
        avg_score = min(100, (avg_daily / daily_target) * 100) if daily_target > 0 else 0
        
        # Consistency score (active days percentage, weighted 30%)
        consistency = (active_days / num_days * 100) if num_days > 0 else 0
        consistency_score = consistency  # Already 0-100
        
        # Regularity score (lower std dev = more regular = better)
        # If std_dev is less than 30% of avg, that's good regularity
        if avg_daily > 0:
            cv = (std_dev / avg_daily) if avg_daily > 0 else 1  # Coefficient of variation
            regularity_score = max(0, min(100, (1 - cv) * 100))
        else:
            regularity_score = 0
        
        # Calculate final productivity score (weighted average)
        productivity_score = int(
            avg_score * 0.4 +          # 40% weight on avg focus
            consistency_score * 0.35 + # 35% weight on consistency
            regularity_score * 0.25    # 25% weight on regularity
        )
        productivity_score = max(0, min(100, productivity_score))
        
        # 2. DEEP WORK PERCENTAGE
        # Sessions >= 45 min (Cal Newport's definition)
        deep_work_pct = (deep_work_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # 3. AVERAGE SESSION LENGTH
        avg_session = sum(session_lengths) / len(session_lengths) if session_lengths else 0
        
        # 4. GOAL COMPLETION RATE
        # Compare against weekly and monthly goals
        try:
            weekly_target = float(self.blocker.stats.get("weekly_goal_hours", 10)) * 60  # Convert to minutes
        except (ValueError, TypeError):
            weekly_target = 600  # Default 10 hours
        
        # Calculate goal rate based on period
        if period_days == 7:
            goal_rate = min(100, (total_focus / weekly_target * 100)) if weekly_target > 0 else 0
        elif period_days in [30, 60, 180, -1]:
            # Scale weekly goal to period
            weeks_in_period = num_days / 7 if num_days > 0 else 1
            period_target = weekly_target * weeks_in_period
            goal_rate = min(100, (total_focus / period_target * 100)) if period_target > 0 else 0
        else:
            goal_rate = 0
        
        # 5. WEEK-OVER-WEEK CHANGE
        # Compare last 7 days vs previous 7 days
        last_7_days = []
        prev_7_days = []
        for i, date_str in enumerate(sorted(relevant_dates, reverse=True)):
            if i < 7:
                day_data = daily_stats.get(date_str, {})
                last_7_days.append(day_data.get("focus_time", 0) / 60)
            elif i < 14:
                day_data = daily_stats.get(date_str, {})
                prev_7_days.append(day_data.get("focus_time", 0) / 60)
        
        last_7_total = sum(last_7_days)
        prev_7_total = sum(prev_7_days) if prev_7_days else 0
        
        if prev_7_total > 0:
            wow_change = ((last_7_total - prev_7_total) / prev_7_total) * 100
        else:
            wow_change = 100 if last_7_total > 0 else 0
        
        # 6. VS PERIOD AVERAGE
        if avg_daily > 0 and len(last_7_days) >= 7:
            last_7_avg = last_7_total / 7
            vs_avg_pct = ((last_7_avg - avg_daily) / avg_daily) * 100
        else:
            vs_avg_pct = 0
        
        # 7. TREND (compare first half vs second half)
        if len(all_daily_focus) >= 4:
            half = len(all_daily_focus) // 2
            first_half_avg = sum(all_daily_focus[:half]) / half if half > 0 else 0
            second_half_avg = sum(all_daily_focus[half:]) / (len(all_daily_focus) - half) if (len(all_daily_focus) - half) > 0 else 0
            
            if first_half_avg > 0:
                trend_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                if trend_pct > 5:
                    trend_text = f"↗+{trend_pct:.0f}%"
                    self.stat_trend.setStyleSheet("color: #10b981; font-weight: bold;")
                elif trend_pct < -5:
                    trend_text = f"↘{trend_pct:.0f}%"
                    self.stat_trend.setStyleSheet("color: #f87171; font-weight: bold;")
                else:
                    trend_text = "→ 0%"
                    self.stat_trend.setStyleSheet("color: #94a3b8;")
            else:
                trend_text = "-"
                self.stat_trend.setStyleSheet("color: #94a3b8;")
        else:
            trend_text = "-"
            self.stat_trend.setStyleSheet("color: #94a3b8;")
        
        # ───────────────────────────────────────────────────────────────────
        # UPDATE UI LABELS
        # ───────────────────────────────────────────────────────────────────
        
        # Productivity Score with color coding
        if productivity_score >= 80:
            self.stat_productivity_score.setStyleSheet("color: #10b981; font-weight: bold;")
        elif productivity_score >= 60:
            self.stat_productivity_score.setStyleSheet("color: #34d399;")
        elif productivity_score >= 40:
            self.stat_productivity_score.setStyleSheet("color: #fbbf24;")
        else:
            self.stat_productivity_score.setStyleSheet("color: #f87171;")
        self.stat_productivity_score.setText(f"{productivity_score}")
        
        # Total time
        if total_focus >= 60:
            self.stat_total_time.setText(f"{total_focus/60:.1f}h")
        else:
            self.stat_total_time.setText(f"{total_focus:.0f}m")
        
        self.stat_total_sessions.setText(str(total_sessions))
        
        # Avg daily
        if avg_daily >= 60:
            self.stat_avg_daily.setText(f"{avg_daily/60:.1f}h")
        else:
            self.stat_avg_daily.setText(f"{avg_daily:.0f}m")
        
        # Consistency
        self.stat_consistency.setText(f"{consistency:.0f}%")
        
        # Deep work percentage
        if deep_work_pct >= 50:
            self.stat_deep_work.setStyleSheet("color: #10b981; font-weight: bold;")
        elif deep_work_pct >= 25:
            self.stat_deep_work.setStyleSheet("color: #f472b6;")
        else:
            self.stat_deep_work.setStyleSheet("color: #94a3b8;")
        self.stat_deep_work.setText(f"{deep_work_pct:.0f}%")
        
        # Average session length
        if avg_session >= 45:
            self.stat_avg_session.setStyleSheet("color: #10b981; font-weight: bold;")
        elif avg_session >= 25:
            self.stat_avg_session.setStyleSheet("color: #2dd4bf;")
        else:
            self.stat_avg_session.setStyleSheet("color: #94a3b8;")
        self.stat_avg_session.setText(f"{avg_session:.0f}m")
        
        # Goal completion rate
        if goal_rate >= 100:
            self.stat_goal_rate.setStyleSheet("color: #10b981; font-weight: bold;")
        elif goal_rate >= 75:
            self.stat_goal_rate.setStyleSheet("color: #34d399;")
        elif goal_rate >= 50:
            self.stat_goal_rate.setStyleSheet("color: #fbbf24;")
        else:
            self.stat_goal_rate.setStyleSheet("color: #fb923c;")
        self.stat_goal_rate.setText(f"{goal_rate:.0f}%")
        
        # Active days
        self.stat_active_days.setText(str(active_days))
        
        # Best day (max)
        if max_day >= 60:
            self.stat_max_day.setText(f"{max_day/60:.1f}h")
        else:
            self.stat_max_day.setText(f"{max_day:.0f}m")
        
        # Std dev (variability)
        if std_dev >= 60:
            self.stat_std_dev.setText(f"±{std_dev/60:.1f}h")
        else:
            self.stat_std_dev.setText(f"±{std_dev:.0f}m")
        
        # Trend
        self.stat_trend.setText(trend_text)
        
        # Week-over-week change
        if wow_change > 0:
            self.stat_wow_value.setText(f"↗ +{wow_change:.0f}%")
            self.stat_wow_value.setStyleSheet("color: #10b981; font-weight: bold;")
        elif wow_change < 0:
            self.stat_wow_value.setText(f"↘ {wow_change:.0f}%")
            self.stat_wow_value.setStyleSheet("color: #f87171; font-weight: bold;")
        else:
            self.stat_wow_value.setText("→ 0%")
            self.stat_wow_value.setStyleSheet("color: #94a3b8;")
        
        # Vs period average
        if vs_avg_pct > 0:
            self.stat_vs_avg_value.setText(f"↗ +{vs_avg_pct:.0f}%")
            self.stat_vs_avg_value.setStyleSheet("color: #10b981; font-weight: bold;")
        elif vs_avg_pct < 0:
            self.stat_vs_avg_value.setText(f"↘ {vs_avg_pct:.0f}%")
            self.stat_vs_avg_value.setStyleSheet("color: #f87171; font-weight: bold;")
        else:
            self.stat_vs_avg_value.setText("→ 0%")
            self.stat_vs_avg_value.setStyleSheet("color: #94a3b8;")

    def _refresh_chad_tips(self) -> None:
        """Refresh the AGI Assistant Chad productivity tips section."""
        from datetime import datetime
        
        CHAD_ENTITY_ID = "underdog_008"  # AGI Assistant Chad
        
        try:
            from gamification import get_entitidex_manager
            from entitidex_tab import _resolve_entity_svg_path
            from entitidex.entity_pools import get_entity_by_id as get_entity
            from PySide6.QtSvg import QSvgRenderer
            from productivity_tips import get_tip_by_index, get_tip_count
        except ImportError as e:
            # Dependencies not available
            self.chad_tips_section.setVisible(False)
            return
        
        # Get entitidex manager to check entity collection
        try:
            manager = get_entitidex_manager(self.blocker.adhd_buster)
        except Exception:
            self.chad_tips_section.setVisible(False)
            return
        
        # Check if user has collected Chad (normal or exceptional)
        has_normal = CHAD_ENTITY_ID in manager.progress.collected_entity_ids
        has_exceptional = manager.progress.is_exceptional(CHAD_ENTITY_ID)
        
        if not has_normal and not has_exceptional:
            # Entity not collected - hide section
            self.chad_tips_section.setVisible(False)
            return
        
        # Entity is collected - show section
        self.chad_tips_section.setVisible(True)
        
        # Determine if we use exceptional tips
        is_exceptional = has_exceptional
        
        # Update section title based on variant
        if is_exceptional:
            self.chad_section_title.setText("⭐ AGI Assistant (Exceptional) Advanced Tips")
            self.chad_section_title.setStyleSheet("color: #ffd700; padding: 4px;")
            self.chad_entity_name.setText("⭐ AGI Assistant Chad")
            self.chad_entity_name.setStyleSheet("color: #ffd700; font-weight: bold; font-size: 12px;")
        else:
            self.chad_section_title.setText("🤖 AGI Assistant Productivity Tips")
            self.chad_section_title.setStyleSheet("color: #a5b4fc; padding: 4px;")
            self.chad_entity_name.setText("AGI Assistant Chad")
            self.chad_entity_name.setStyleSheet("color: #e5e7eb; font-weight: bold; font-size: 12px;")
        
        # Load entity icon
        try:
            entity = get_entity(CHAD_ENTITY_ID)
            if entity:
                svg_path = _resolve_entity_svg_path(entity, is_exceptional)
                if svg_path:
                    renderer = QSvgRenderer(svg_path)
                    if renderer.isValid():
                        icon_size = 48
                        pixmap = QtGui.QPixmap(icon_size, icon_size)
                        pixmap.fill(QtCore.Qt.transparent)
                        painter = QtGui.QPainter(pixmap)
                        renderer.render(painter)
                        painter.end()
                        self.chad_icon_label.setPixmap(pixmap)
                        
                        # Update icon border for exceptional
                        if is_exceptional:
                            self.chad_icon_label.setStyleSheet("""
                                QLabel {
                                    background: #333;
                                    border: 2px solid #ffd700;
                                    border-radius: 6px;
                                }
                            """)
                        else:
                            self.chad_icon_label.setStyleSheet("""
                                QLabel {
                                    background: #333;
                                    border: 1px solid #444;
                                    border-radius: 6px;
                                }
                            """)
        except Exception:
            # Fallback - just show text
            self.chad_icon_label.setText("🤖")
        
        # Get current tip index (sequential cycling)
        tip_key = "chad_tip_index_exceptional" if is_exceptional else "chad_tip_index"
        tip_index = self.blocker.stats.get(tip_key, 0)
        total_tips = get_tip_count(is_exceptional)
        
        # Get the tip at current index
        tip_text, category_emoji = get_tip_by_index(tip_index, is_exceptional)
        
        # Update tip display
        self.chad_tip_number.setText(f"Tip #{tip_index + 1} of {total_tips}")
        self.chad_tip_text.setText(f"{category_emoji} {tip_text}")
        
        # Check if already acknowledged today
        today_str = datetime.now().strftime("%Y-%m-%d")
        ack_key = "chad_tip_acknowledged_date_exceptional" if is_exceptional else "chad_tip_acknowledged_date"
        last_acknowledged = self.blocker.stats.get(ack_key, "")
        
        if last_acknowledged == today_str:
            # Already acknowledged today
            self.chad_acknowledge_btn.setEnabled(False)
            self.chad_acknowledge_btn.setText("✓ +1 🪙 collected!")
        else:
            # Can acknowledge
            self.chad_acknowledge_btn.setEnabled(True)
            self.chad_acknowledge_btn.setText("✓ Got it! (+1 🪙)")
    
    def _acknowledge_chad_tip(self) -> None:
        """Acknowledge the daily Chad tip and award 1 coin."""
        from datetime import datetime
        from productivity_tips import get_tip_count
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Determine if we're using exceptional tips
        try:
            from gamification import get_entitidex_manager
            manager = get_entitidex_manager(self.blocker.adhd_buster)
            is_exceptional = manager.progress.is_exceptional("underdog_008")
        except Exception:
            is_exceptional = False
        
        # Use appropriate keys based on variant
        ack_key = "chad_tip_acknowledged_date_exceptional" if is_exceptional else "chad_tip_acknowledged_date"
        tip_key = "chad_tip_index_exceptional" if is_exceptional else "chad_tip_index"
        
        # Check if already acknowledged today (prevent double rewards)
        last_acknowledged = self.blocker.stats.get(ack_key, "")
        if last_acknowledged == today_str:
            return
        
        # Mark as acknowledged
        self.blocker.stats[ack_key] = today_str
        
        # Increment tip index for next time (cycle back to 0 after all tips shown)
        current_index = self.blocker.stats.get(tip_key, 0)
        total_tips = get_tip_count(is_exceptional)
        next_index = (current_index + 1) % total_tips
        self.blocker.stats[tip_key] = next_index
        
        self.blocker.save_stats()
        
        # Award 1 coin
        current_coins = self.blocker.adhd_buster.get("coins", 0)
        self.blocker.adhd_buster["coins"] = current_coins + 1
        self.blocker.save_config()
        
        # Update button state - no dialog, just update text
        self.chad_acknowledge_btn.setEnabled(False)
        self.chad_acknowledge_btn.setText("✓ +1 🪙 collected!")

    def _reset_stats(self) -> None:
        if show_question(self, "Reset Stats", "Reset all statistics?") == QtWidgets.QMessageBox.Yes:
            self.blocker.stats = self.blocker._default_stats()
            self.blocker.save_stats()
            self.refresh()


class SettingsTab(QtWidgets.QWidget):
    """Settings tab - password, pomodoro settings, backup/restore, cleanup."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        inner = QtWidgets.QVBoxLayout(container)

        # User Profile Settings
        user_group = QtWidgets.QGroupBox("👤 User Profile")
        user_layout = QtWidgets.QHBoxLayout(user_group)
        current_user = self.window().blocker.user_dir.name if hasattr(self.window().blocker, 'user_dir') else "Default"
        user_label = QtWidgets.QLabel(f"Current Profile: <b>{current_user}</b>")
        user_layout.addWidget(user_label)
        user_layout.addStretch()
        
        switch_user_btn = QtWidgets.QPushButton("Switch User")
        switch_user_btn.clicked.connect(self._switch_user)
        user_layout.addWidget(switch_user_btn)
        inner.addWidget(user_group)

        # Password protection
        pwd_group = QtWidgets.QGroupBox("🔐 Password Protection")
        pwd_layout = QtWidgets.QVBoxLayout(pwd_group)
        pwd_layout.addWidget(QtWidgets.QLabel("Set a password to prevent stopping Strict Mode sessions early."))
        self.pwd_status = QtWidgets.QLabel()
        pwd_layout.addWidget(self.pwd_status)
        pwd_btn_layout = QtWidgets.QHBoxLayout()
        set_pwd_btn = QtWidgets.QPushButton("Set Password")
        set_pwd_btn.clicked.connect(self._set_password)
        pwd_btn_layout.addWidget(set_pwd_btn)
        rem_pwd_btn = QtWidgets.QPushButton("Remove Password")
        rem_pwd_btn.clicked.connect(self._remove_password)
        pwd_btn_layout.addWidget(rem_pwd_btn)
        pwd_btn_layout.addStretch()
        pwd_layout.addLayout(pwd_btn_layout)
        inner.addWidget(pwd_group)
        self._update_pwd_status()

        # Mode explanations
        mode_group = QtWidgets.QGroupBox("📋 Session Modes")
        mode_layout = QtWidgets.QVBoxLayout(mode_group)
        mode_info = QtWidgets.QLabel(
            "<b>Normal:</b> Can stop anytime - good for flexibility<br>"
            "<b>Strict 🔐:</b> Requires password to stop - prevents impulsive exits<br>"
            "<b>Hardcore 💪:</b> Must solve 2 math problems to stop - maximum commitment!<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;• Numbers are displayed as images (no copy-paste)<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;• Wrong answer = start over with new problems<br>"
            "<b>Pomodoro 🍅:</b> 25 min work / 5 min break cycles - for productivity"
        )
        mode_info.setWordWrap(True)
        mode_info.setStyleSheet("padding: 10px; background-color: #2d2d30; color: #e0e0e0; border-radius: 5px; border: 1px solid #3e3e42;")
        mode_layout.addWidget(mode_info)
        inner.addWidget(mode_group)

        # Pomodoro settings
        pomo_group = QtWidgets.QGroupBox("🍅 Pomodoro Settings")
        pomo_layout = QtWidgets.QFormLayout(pomo_group)
        self.pomo_work_spin = QtWidgets.QSpinBox()
        self.pomo_work_spin.setRange(1, 120)
        self.pomo_work_spin.setValue(self.blocker.pomodoro_work)
        pomo_layout.addRow("Work duration (min):", self.pomo_work_spin)
        self.pomo_break_spin = QtWidgets.QSpinBox()
        self.pomo_break_spin.setRange(1, 60)
        self.pomo_break_spin.setValue(self.blocker.pomodoro_break)
        pomo_layout.addRow("Short break (min):", self.pomo_break_spin)
        self.pomo_long_spin = QtWidgets.QSpinBox()
        self.pomo_long_spin.setRange(1, 60)
        self.pomo_long_spin.setValue(self.blocker.pomodoro_long_break)
        pomo_layout.addRow("Long break (min):", self.pomo_long_spin)
        save_pomo_btn = QtWidgets.QPushButton("Save Pomodoro Settings")
        save_pomo_btn.clicked.connect(self._save_pomodoro)
        pomo_layout.addRow(save_pomo_btn)
        inner.addWidget(pomo_group)

        # Backup/Restore
        backup_group = QtWidgets.QGroupBox("💾 Backup & Restore")
        backup_layout = QtWidgets.QVBoxLayout(backup_group)
        backup_layout.addWidget(QtWidgets.QLabel("Backup or restore all your data (settings, stats, goals)."))
        backup_btn_layout = QtWidgets.QHBoxLayout()
        create_backup_btn = QtWidgets.QPushButton("📤 Create Backup")
        create_backup_btn.clicked.connect(self._create_backup)
        backup_btn_layout.addWidget(create_backup_btn)
        restore_backup_btn = QtWidgets.QPushButton("📥 Restore Backup")
        restore_backup_btn.clicked.connect(self._restore_backup)
        backup_btn_layout.addWidget(restore_backup_btn)
        backup_btn_layout.addStretch()
        backup_layout.addLayout(backup_btn_layout)
        inner.addWidget(backup_group)

        # Emergency cleanup
        cleanup_group = QtWidgets.QGroupBox("⚠️ Emergency Cleanup")
        cleanup_layout = QtWidgets.QVBoxLayout(cleanup_group)
        cleanup_layout.addWidget(QtWidgets.QLabel("Use if websites remain blocked after closing the app."))
        cleanup_btn = QtWidgets.QPushButton("🧹 Remove All Blocks & Clean System")
        cleanup_btn.clicked.connect(self._emergency_cleanup)
        cleanup_layout.addWidget(cleanup_btn)
        inner.addWidget(cleanup_group)

        # System Tray (if available)
        if QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            tray_group = QtWidgets.QGroupBox("🖥️ System Tray")
            tray_layout = QtWidgets.QVBoxLayout(tray_group)
            self.tray_check = QtWidgets.QCheckBox("Minimize to system tray instead of closing")
            self.tray_check.setChecked(self.blocker.minimize_to_tray)  # Load from config
            self.tray_check.toggled.connect(self._toggle_tray)
            tray_layout.addWidget(self.tray_check)
            tray_layout.addWidget(QtWidgets.QLabel(
                "When enabled, clicking the close button will hide the app to the system tray.\n"
                "Double-click the tray icon to restore the window. Use 'Exit' to fully quit."
            ))
            inner.addWidget(tray_group)

        # About
        about_group = QtWidgets.QGroupBox("About")
        about_layout = QtWidgets.QVBoxLayout(about_group)
        about_layout.addWidget(QtWidgets.QLabel(f"Personal Liberty v{APP_VERSION}"))
        about_layout.addWidget(QtWidgets.QLabel("A focus and productivity tool for Windows"))
        inner.addWidget(about_group)

        # Factory Reset - DANGER ZONE
        reset_group = QtWidgets.QGroupBox("🚨 Danger Zone")
        reset_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #e53935;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #e53935;
            }
        """)
        reset_layout = QtWidgets.QVBoxLayout(reset_group)
        reset_warning = QtWidgets.QLabel(
            "⚠️ <b>Factory Reset</b> will permanently delete ALL your data including:\n"
            "• All statistics and history\n"
            "• Weight, sleep, activity, and water tracking data\n"
            "• Hero progress, XP, gear, and story decisions\n"
            "• All settings and preferences\n\n"
            "<b>This action cannot be undone!</b>"
        )
        reset_warning.setWordWrap(True)
        reset_warning.setStyleSheet("color: #ff8a80; padding: 10px; background-color: #2a1a1a; border-radius: 5px;")
        reset_layout.addWidget(reset_warning)
        reset_btn = QtWidgets.QPushButton("🗑️ Factory Reset - Delete All Data")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
        """)
        reset_btn.clicked.connect(self._factory_reset)
        reset_layout.addWidget(reset_btn)
        inner.addWidget(reset_group)

        inner.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _update_pwd_status(self) -> None:
        if self.blocker.password_hash:
            self.pwd_status.setText("🔐 Password is set")
            self.pwd_status.setStyleSheet("color: green;")
        else:
            self.pwd_status.setText("No password set")
            self.pwd_status.setStyleSheet("color: gray;")

    def _switch_user(self) -> None:
        """Clear last user setting and restart app."""
        if show_question(self, "Switch User", 
                        "Are you sure you want to switch profiles?\nThe application will restart.") == QtWidgets.QMessageBox.Yes:
            # Clear stored user
            try:
                from core_logic import APP_DIR
                from user_manager import UserManager
                
                um = UserManager(APP_DIR)
                um.clear_last_user()
                
                # Restart app
                import sys
                import subprocess
                
                # Use subprocess to start a new instance
                subprocess.Popen([sys.executable] + sys.argv)
                
                # Exit current instance
                sys.exit(0)
            except Exception as e:
                show_error(self, "Error", f"Could not switch user: {e}")

    def _set_password(self) -> None:
        pwd, ok = QtWidgets.QInputDialog.getText(self, "Set Password", "Enter new password:", QtWidgets.QLineEdit.Password)
        if not ok or not pwd:
            return
        confirm, ok = QtWidgets.QInputDialog.getText(self, "Confirm", "Confirm password:", QtWidgets.QLineEdit.Password)
        if ok and pwd == confirm:
            self.blocker.set_password(pwd)
            self._update_pwd_status()
            show_info(self, "Password Set", "Your password has been set successfully!")
        else:
            show_warning(self, "Password Mismatch", "The passwords you entered don't match. Please try again.")

    def _remove_password(self) -> None:
        if not self.blocker.password_hash:
            show_info(self, "Info", "No password set")
            return
        pwd, ok = QtWidgets.QInputDialog.getText(self, "Remove Password", "Enter current password:", QtWidgets.QLineEdit.Password)
        if ok and self.blocker.verify_password(pwd or ""):
            self.blocker.set_password(None)
            self._update_pwd_status()
        else:
            show_warning(self, "Incorrect Password", "The password you entered is incorrect.")

    def _save_pomodoro(self) -> None:
        self.blocker.pomodoro_work = self.pomo_work_spin.value()
        self.blocker.pomodoro_break = self.pomo_break_spin.value()
        self.blocker.pomodoro_long_break = self.pomo_long_spin.value()
        self.blocker.save_config()
        show_info(self, "Saved", "Pomodoro settings saved!")

    def _create_backup(self) -> None:
        import json
        from datetime import datetime
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Backup", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            backup_data = {
                "backup_version": APP_VERSION,
                "backup_date": datetime.now().isoformat(),
                "config": {
                    "blacklist": self.blocker.blacklist,
                    "whitelist": self.blocker.whitelist,
                    "categories_enabled": self.blocker.categories_enabled,
                    "pomodoro_work": self.blocker.pomodoro_work,
                    "pomodoro_break": self.blocker.pomodoro_break,
                    "pomodoro_long_break": self.blocker.pomodoro_long_break,
                    "schedules": self.blocker.schedules,
                    "priorities": self.blocker.priorities,
                    "show_priorities_on_startup": self.blocker.show_priorities_on_startup,
                    "priority_checkin_enabled": self.blocker.priority_checkin_enabled,
                    "priority_checkin_interval": self.blocker.priority_checkin_interval,
                    "adhd_buster": self.blocker.adhd_buster,
                },
                "stats": self.blocker.stats,
            }
            # Include goals if available
            if FocusGoals and self.blocker.goals_path.exists():
                try:
                    with open(self.blocker.goals_path, "r", encoding="utf-8") as gf:
                        backup_data["goals"] = json.load(gf)
                except Exception:
                    pass
            with open(path, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2)
            show_info(self, "Backup Complete", "Backup saved successfully!")
        except Exception as e:
            show_error(self, "Backup Failed", str(e))

    def _restore_backup(self) -> None:
        import json
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Backup", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "backup_version" not in data:
                show_warning(self, "Invalid", "Not a valid backup file.")
                return
            if show_question(self, "Confirm", "Restore backup? This will replace all current data.") != QtWidgets.QMessageBox.Yes:
                return
            config = data.get("config", {})
            self.blocker.blacklist = config.get("blacklist", self.blocker.blacklist)
            self.blocker.whitelist = config.get("whitelist", self.blocker.whitelist)
            self.blocker.categories_enabled = config.get("categories_enabled", self.blocker.categories_enabled)
            self.blocker.pomodoro_work = config.get("pomodoro_work", self.blocker.pomodoro_work)
            self.blocker.pomodoro_break = config.get("pomodoro_break", self.blocker.pomodoro_break)
            self.blocker.pomodoro_long_break = config.get("pomodoro_long_break", self.blocker.pomodoro_long_break)
            self.blocker.schedules = config.get("schedules", self.blocker.schedules)
            self.blocker.priorities = config.get("priorities", self.blocker.priorities)
            self.blocker.show_priorities_on_startup = config.get("show_priorities_on_startup", self.blocker.show_priorities_on_startup)
            self.blocker.priority_checkin_enabled = config.get("priority_checkin_enabled", self.blocker.priority_checkin_enabled)
            self.blocker.priority_checkin_interval = config.get("priority_checkin_interval", self.blocker.priority_checkin_interval)
            self.blocker.adhd_buster = config.get("adhd_buster", self.blocker.adhd_buster)
            self.blocker.save_config()
            stats = data.get("stats", {})
            self.blocker.stats = {**self.blocker._default_stats(), **stats}
            self.blocker.save_stats()

            # Restore goals if present
            if FocusGoals and "goals" in data:
                try:
                    with open(self.blocker.goals_path, "w", encoding="utf-8") as gf:
                        json.dump(data["goals"], gf, indent=2)
                except Exception:
                    pass

            # Refresh UI
            self.pomo_work_spin.setValue(self.blocker.pomodoro_work)
            self.pomo_break_spin.setValue(self.blocker.pomodoro_break)
            self.pomo_long_spin.setValue(self.blocker.pomodoro_long_break)
            self._update_pwd_status()

            main_win = self.window()
            if hasattr(main_win, "sites_tab"):
                main_win.sites_tab._refresh_lists()
            if hasattr(main_win, "categories_tab"):
                main_win.categories_tab.refresh()
            if hasattr(main_win, "schedule_tab"):
                main_win.schedule_tab._refresh_table()
            if hasattr(main_win, "stats_tab"):
                main_win.stats_tab.refresh()
            if hasattr(main_win, "ai_tab") and AI_AVAILABLE:
                main_win.ai_tab._refresh_data()

            show_info(self, "Restored", "Backup restored successfully!")
        except Exception as e:
            show_error(self, "Restore Failed", str(e))

    def _emergency_cleanup(self) -> None:
        """Emergency cleanup with enhanced confirmation dialog."""
        # Extra warning for strict/hardcore modes
        mode = getattr(self.blocker, 'mode', None)
        if mode in (BlockMode.STRICT, BlockMode.HARDCORE) and self.blocker.is_blocking:
            reply = show_question(
                self, "⚠️ Active Session Detected",
                f"You have an active {mode.upper()} session!\n\n"
                "Emergency cleanup will bypass the protection you set.\n"
                "This defeats the purpose of using a strict mode.\n\n"
                "Are you SURE you want to proceed?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
        
        # Gather impact data
        impact_data = {
            "items_count": 0,
            "power_lost": 0,
            "progress_percent": 0,
            "coins_refund": 0,
            "items_affected": []
        }
        
        # Calculate impact from inventory
        if GAMIFICATION_AVAILABLE:
            inventory = self.blocker.adhd_buster.get("inventory", [])
            impact_data["items_count"] = len(inventory)
            impact_data["power_lost"] = self.blocker.adhd_buster.get("total_power", 0)
            impact_data["items_affected"] = inventory[:20]  # Show first 20
            
            # Calculate progress percentage
            total_xp = self.blocker.adhd_buster.get("total_xp", 0)
            if total_xp > 0:
                impact_data["progress_percent"] = min(100, int((total_xp / 10000) * 100))
        
        # Show enhanced confirmation dialog
        confirmed = show_emergency_cleanup_dialog("emergency_cleanup", impact_data, self)
        
        if not confirmed:
            return
        
        success, message = self.blocker.emergency_cleanup()
        if success:
            show_info(self, "Cleanup Complete", message)
            # Reset Timer UI
            main_win = self.window()
            if hasattr(main_win, "timer_tab"):
                main_win.timer_tab._force_stop_session()
        else:
            show_error(self, "Cleanup Failed", message)

    def _factory_reset(self) -> None:
        """Factory reset - delete all user data after multiple confirmations."""
        # First confirmation
        reply1 = show_question(
            self, "⚠️ Factory Reset Warning",
            "You are about to DELETE ALL YOUR DATA!\n\n"
            "This includes:\n"
            "• All statistics and session history\n"
            "• Weight, sleep, activity, and water tracking\n"
            "• Hero progress, XP, level, gear, and story\n"
            "• Blocked sites and categories\n"
            "• All settings and preferences\n\n"
            "This action CANNOT be undone!\n\n"
            "Are you sure you want to continue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply1 != QtWidgets.QMessageBox.Yes:
            return
        
        # Second confirmation with typing requirement
        confirm_text, ok = QtWidgets.QInputDialog.getText(
            self, "Confirm Factory Reset",
            "To confirm deletion, type 'DELETE' (all caps):",
            QtWidgets.QLineEdit.Normal
        )
        if not ok or confirm_text != "DELETE":
            show_info(self, "Cancelled", "Factory reset was cancelled. Your data is safe.")
            return
        
        # Final warning
        reply3 = show_question(
            self, "🚨 FINAL WARNING",
            "THIS IS YOUR LAST CHANCE!\n\n"
            "All your progress will be permanently deleted.\n"
            "There is NO way to recover this data.\n\n"
            "Proceed with factory reset?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply3 != QtWidgets.QMessageBox.Yes:
            show_info(self, "Cancelled", "Factory reset was cancelled. Your data is safe.")
            return
        
        # Perform the reset
        try:
            # Get data directory
            data_dir = APP_DIR
            
            # Files to delete
            files_to_delete = [
                "config.json",
                "stats.json",
                "goals.json",
            ]
            
            deleted_count = 0
            for filename in files_to_delete:
                filepath = data_dir / filename
                if filepath.exists():
                    try:
                        filepath.unlink()
                        deleted_count += 1
                    except Exception as e:
                        print(f"Failed to delete {filename}: {e}")
            
            # Reset in-memory state
            self.blocker.blocked_sites = []
            self.blocker.blocked_categories = []
            self.blocker.schedules = []
            self.blocker.password_hash = None
            self.blocker.is_blocking = False
            self.blocker.mode = BlockMode.NORMAL
            self.blocker.stats = {
                "total_sessions": 0,
                "total_focus_time": 0,
                "longest_session": 0,
                "daily_stats": {},
            }
            
            # Reset tracking data
            self.blocker.weight_entries = []
            self.blocker.sleep_entries = []
            self.blocker.activity_entries = []
            self.blocker.water_entries = []
            
            # Reset gamification data
            if GAMIFICATION_AVAILABLE:
                self.blocker.adhd_buster = {
                    "inventory": [],
                    "equipped": {},
                    "total_xp": 0,
                    "coins": 0,
                    "total_power": 0,
                    "current_chapter": 0,
                    "story_decisions": {},
                }
            
            # Reset goals
            self.blocker.goals = {
                "daily_focus_minutes": 120,
                "daily_sessions": 4,
            }
            
            # Save clean state
            self.blocker.save_config()
            self.blocker.save_stats()
            
            show_info(
                self, "Factory Reset Complete",
                f"All data has been deleted ({deleted_count} files removed).\n\n"
                "The application will now restart with a fresh state.\n"
                "Please restart the application."
            )
            
            # Close the application
            main_window = self.window()
            if main_window:
                main_window.close()
                
        except Exception as e:
            show_error(self, "Reset Failed", f"An error occurred during reset:\n{str(e)}")

    def _toggle_tray(self, checked: bool) -> None:
        """Toggle minimize to tray setting and save to config."""
        main_window = self.window()
        if hasattr(main_window, 'minimize_to_tray'):
            main_window.minimize_to_tray = checked
            # Persist the setting
            self.blocker.minimize_to_tray = checked
            self.blocker.save_config()


class WeightChartWidget(QtWidgets.QWidget):
    """Custom widget that draws a weight progress chart using Qt's built-in painting.
    
    Features:
    - Date-based X-axis (proper time spacing)
    - Gap handling with dashed lines for missing days
    - 7-day moving average trend line (for 7+ entries)
    - Weekly binning with min/max bands (for 30+ entries)
    - Trend direction indicator
    """
    
    # Mode thresholds
    WEEKLY_BIN_THRESHOLD = 30  # Switch to weekly binning after this many entries
    MOVING_AVG_WINDOW = 7     # 7-day moving average
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.weight_data = []  # List of (date_str, weight) tuples
        self.goal_weight = None
        self.unit = "kg"
        self.setMinimumHeight(250)
        self.setMinimumWidth(400)
    
    def set_data(self, entries: list, goal: float = None, unit: str = "kg") -> None:
        """Set the weight data to display."""
        # Sort by date and filter valid entries
        valid_entries = [(e["date"], e["weight"]) for e in entries 
                        if e.get("date") and e.get("weight")]
        self.weight_data = sorted(valid_entries, key=lambda x: x[0])
        self.goal_weight = goal
        self.unit = unit
        self.update()
    
    def _parse_date(self, date_str: str):
        """Parse date string to datetime object."""
        from datetime import datetime
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None
    
    def _calculate_weekly_bins(self) -> list:
        """Calculate weekly bins with avg, min, max for each week."""
        from datetime import datetime, timedelta
        
        if not self.weight_data:
            return []
        
        bins = []
        first_date = self._parse_date(self.weight_data[0][0])
        last_date = self._parse_date(self.weight_data[-1][0])
        
        if not first_date or not last_date:
            return []
        
        # Group by week
        current_week_start = first_date
        while current_week_start <= last_date:
            week_end = current_week_start + timedelta(days=6)
            
            # Find weights in this week
            week_weights = []
            for date_str, weight in self.weight_data:
                d = self._parse_date(date_str)
                if d and current_week_start <= d <= week_end:
                    week_weights.append(weight)
            
            if week_weights:
                bins.append({
                    "date": current_week_start,
                    "avg": sum(week_weights) / len(week_weights),
                    "min": min(week_weights),
                    "max": max(week_weights),
                    "count": len(week_weights),
                })
            
            current_week_start += timedelta(days=7)
        
        return bins
    
    def _calculate_moving_average(self) -> list:
        """Calculate 7-day moving average for each data point."""
        from datetime import datetime, timedelta
        
        if len(self.weight_data) < self.MOVING_AVG_WINDOW:
            return []
        
        ma_data = []
        
        for i, (date_str, weight) in enumerate(self.weight_data):
            current_date = self._parse_date(date_str)
            if not current_date:
                continue
            
            # Get weights from past 7 days
            window_start = current_date - timedelta(days=self.MOVING_AVG_WINDOW - 1)
            window_weights = []
            
            for d_str, w in self.weight_data:
                d = self._parse_date(d_str)
                if d and window_start <= d <= current_date:
                    window_weights.append(w)
            
            if len(window_weights) >= 3:  # Need at least 3 points for meaningful average
                ma_data.append((date_str, sum(window_weights) / len(window_weights)))
        
        return ma_data
    
    def _calculate_trend(self) -> tuple:
        """Calculate overall trend direction and rate.
        
        Returns:
            (direction, rate_per_week, r_squared)
            direction: "down", "up", or "stable"
            rate_per_week: kg change per week
            r_squared: strength of trend (0-1)
        """
        if len(self.weight_data) < 3:
            return ("stable", 0, 0)
        
        from datetime import datetime
        
        # Simple linear regression
        dates = []
        weights = []
        first_date = self._parse_date(self.weight_data[0][0])
        
        for date_str, weight in self.weight_data:
            d = self._parse_date(date_str)
            if d and first_date:
                days = (d - first_date).days
                dates.append(days)
                weights.append(weight)
        
        if len(dates) < 3:
            return ("stable", 0, 0)
        
        n = len(dates)
        sum_x = sum(dates)
        sum_y = sum(weights)
        sum_xy = sum(x * y for x, y in zip(dates, weights))
        sum_x2 = sum(x * x for x in dates)
        sum_y2 = sum(y * y for y in weights)
        
        # Slope (rate per day)
        denom = n * sum_x2 - sum_x ** 2
        if denom == 0:
            return ("stable", 0, 0)
        
        slope = (n * sum_xy - sum_x * sum_y) / denom
        
        # R-squared
        mean_y = sum_y / n
        ss_tot = sum((y - mean_y) ** 2 for y in weights)
        
        if ss_tot == 0:
            r_squared = 1.0
        else:
            intercept = (sum_y - slope * sum_x) / n
            ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(dates, weights))
            r_squared = 1 - (ss_res / ss_tot)
        
        # Rate per week (slope * 7)
        rate_per_week = slope * 7
        
        # Determine direction
        if abs(rate_per_week) < 0.1:  # Less than 100g per week
            direction = "stable"
        elif rate_per_week < 0:
            direction = "down"
        else:
            direction = "up"
        
        return (direction, rate_per_week, max(0, r_squared))
    
    def paintEvent(self, event) -> None:
        """Paint the weight chart."""
        from datetime import datetime, timedelta
        
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        margin_left = 55
        margin_right = 20
        margin_top = 35  # More space for trend indicator
        margin_bottom = 45
        chart_rect = QtCore.QRect(
            margin_left, margin_top, 
            rect.width() - margin_left - margin_right, 
            rect.height() - margin_top - margin_bottom
        )
        
        # Background
        painter.fillRect(rect, QtGui.QColor("#1a1a2e"))
        
        # Draw border
        painter.setPen(QtGui.QPen(QtGui.QColor("#4a4a6a"), 1))
        painter.drawRect(chart_rect)
        
        if len(self.weight_data) < 2:
            # Not enough data
            painter.setPen(QtGui.QColor("#888888"))
            painter.setFont(QtGui.QFont("Segoe UI", 12))
            painter.drawText(chart_rect, QtCore.Qt.AlignmentFlag.AlignCenter, 
                           "Enter at least 2 weight entries\nto see your progress chart")
            return
        
        # Determine if we should use weekly binning
        use_weekly_bins = len(self.weight_data) >= self.WEEKLY_BIN_THRESHOLD
        
        # Calculate date range
        first_date = self._parse_date(self.weight_data[0][0])
        last_date = self._parse_date(self.weight_data[-1][0])
        
        if not first_date or not last_date:
            return
        
        total_days = max(1, (last_date - first_date).days)
        
        # Calculate weight range
        weights = [w for _, w in self.weight_data]
        min_weight = min(weights)
        max_weight = max(weights)
        
        # Include goal in range if set
        if self.goal_weight:
            min_weight = min(min_weight, self.goal_weight)
            max_weight = max(max_weight, self.goal_weight)
        
        # Add padding to range
        weight_range = max_weight - min_weight
        if weight_range < 1:
            weight_range = 2
        min_weight -= weight_range * 0.1
        max_weight += weight_range * 0.1
        weight_range = max_weight - min_weight
        
        # Helper functions
        def date_to_x(date):
            if isinstance(date, str):
                date = self._parse_date(date)
            if not date:
                return chart_rect.left()
            days_from_start = (date - first_date).days
            return chart_rect.left() + (chart_rect.width() * days_from_start / total_days)
        
        def weight_to_y(weight):
            return chart_rect.top() + chart_rect.height() * (max_weight - weight) / weight_range
        
        # Draw trend indicator at top
        direction, rate, r_sq = self._calculate_trend()
        painter.setFont(QtGui.QFont("Segoe UI", 10))
        if direction == "down":
            trend_color = QtGui.QColor("#00ff88")
            trend_text = f"↓ Losing {abs(rate)*1000:.0f}g/week"
        elif direction == "up":
            trend_color = QtGui.QColor("#ff6464")
            trend_text = f"↑ Gaining {abs(rate)*1000:.0f}g/week"
        else:
            trend_color = QtGui.QColor("#ffff64")
            trend_text = "→ Stable"
        
        if r_sq > 0.5:
            trend_text += f" (strong trend)"
        elif r_sq > 0.2:
            trend_text += f" (moderate trend)"
        
        painter.setPen(trend_color)
        painter.drawText(margin_left, 20, trend_text)
        
        # Draw grid lines and labels
        painter.setPen(QtGui.QPen(QtGui.QColor("#333355"), 1, QtCore.Qt.PenStyle.DashLine))
        num_lines = 5
        for i in range(num_lines + 1):
            y = chart_rect.top() + (chart_rect.height() * i / num_lines)
            painter.drawLine(chart_rect.left(), int(y), chart_rect.right(), int(y))
            
            # Weight label
            weight_val = max_weight - (weight_range * i / num_lines)
            painter.setPen(QtGui.QColor("#888888"))
            painter.setFont(QtGui.QFont("Segoe UI", 9))
            label = f"{weight_val:.1f}"
            painter.drawText(5, int(y) + 4, label)
            painter.setPen(QtGui.QPen(QtGui.QColor("#333355"), 1, QtCore.Qt.PenStyle.DashLine))
        
        # Draw goal line if set
        if self.goal_weight and min_weight <= self.goal_weight <= max_weight:
            goal_y = weight_to_y(self.goal_weight)
            painter.setPen(QtGui.QPen(QtGui.QColor("#00ff88"), 2, QtCore.Qt.PenStyle.DashLine))
            painter.drawLine(chart_rect.left(), int(goal_y), chart_rect.right(), int(goal_y))
            painter.setPen(QtGui.QColor("#00ff88"))
            goal_display = self.goal_weight * 2.20462 if self.unit == "lbs" else self.goal_weight
            painter.drawText(chart_rect.right() - 60, int(goal_y) - 5, f"Goal: {goal_display:.1f}")
        
        if use_weekly_bins:
            # ===== WEEKLY BINNING MODE =====
            bins = self._calculate_weekly_bins()
            
            if len(bins) >= 2:
                # Draw min/max band
                band_path = QtGui.QPainterPath()
                
                # Top edge (max values)
                first_bin = bins[0]
                band_path.moveTo(date_to_x(first_bin["date"]), weight_to_y(first_bin["max"]))
                for bin_data in bins:
                    x = date_to_x(bin_data["date"])
                    band_path.lineTo(x, weight_to_y(bin_data["max"]))
                
                # Bottom edge (min values, reversed)
                for bin_data in reversed(bins):
                    x = date_to_x(bin_data["date"])
                    band_path.lineTo(x, weight_to_y(bin_data["min"]))
                
                band_path.closeSubpath()
                
                # Fill band
                painter.setBrush(QtGui.QColor(100, 150, 255, 40))
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.drawPath(band_path)
                
                # Draw average line
                painter.setPen(QtGui.QPen(QtGui.QColor("#6496ff"), 3))
                for i in range(len(bins) - 1):
                    x1 = date_to_x(bins[i]["date"])
                    y1 = weight_to_y(bins[i]["avg"])
                    x2 = date_to_x(bins[i + 1]["date"])
                    y2 = weight_to_y(bins[i + 1]["avg"])
                    painter.drawLine(QtCore.QPointF(x1, y1), QtCore.QPointF(x2, y2))
                
                # Draw weekly points with count indicator
                for bin_data in bins:
                    x = date_to_x(bin_data["date"])
                    y = weight_to_y(bin_data["avg"])
                    
                    # Size based on entry count
                    size = min(8, 4 + bin_data["count"])
                    
                    painter.setBrush(QtGui.QColor("#6496ff"))
                    painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff"), 1))
                    painter.drawEllipse(QtCore.QPointF(x, y), size, size)
                
                # Legend for binned mode
                painter.setPen(QtGui.QColor("#888888"))
                painter.setFont(QtGui.QFont("Segoe UI", 8))
                painter.drawText(chart_rect.right() - 100, chart_rect.top() + 15, 
                               f"Weekly avg (n={len(self.weight_data)})")
        
        else:
            # ===== DAILY MODE =====
            # Build points list with date info
            points = []
            prev_date = None
            
            for date_str, weight in self.weight_data:
                current_date = self._parse_date(date_str)
                if not current_date:
                    continue
                
                x = date_to_x(current_date)
                y = weight_to_y(weight)
                
                # Check for gap
                gap_days = 0
                if prev_date:
                    gap_days = (current_date - prev_date).days - 1
                
                points.append({
                    "date": current_date,
                    "date_str": date_str,
                    "weight": weight,
                    "x": x,
                    "y": y,
                    "gap_before": gap_days,
                })
                
                prev_date = current_date
            
            if len(points) >= 2:
                # Draw gradient fill under line
                path = QtGui.QPainterPath()
                path.moveTo(points[0]["x"], chart_rect.bottom())
                for p in points:
                    path.lineTo(p["x"], p["y"])
                path.lineTo(points[-1]["x"], chart_rect.bottom())
                path.closeSubpath()
                
                gradient = QtGui.QLinearGradient(0, chart_rect.top(), 0, chart_rect.bottom())
                gradient.setColorAt(0, QtGui.QColor(100, 150, 255, 100))
                gradient.setColorAt(1, QtGui.QColor(100, 150, 255, 20))
                painter.fillPath(path, gradient)
                
                # Draw connecting lines (dashed for gaps)
                for i in range(len(points) - 1):
                    p1 = points[i]
                    p2 = points[i + 1]
                    
                    if p2["gap_before"] > 1:
                        # Dashed line for gaps > 1 day
                        painter.setPen(QtGui.QPen(
                            QtGui.QColor("#6496ff"), 2, 
                            QtCore.Qt.PenStyle.DashLine
                        ))
                    else:
                        # Solid line for consecutive/near-consecutive days
                        painter.setPen(QtGui.QPen(QtGui.QColor("#6496ff"), 3))
                    
                    painter.drawLine(
                        QtCore.QPointF(p1["x"], p1["y"]), 
                        QtCore.QPointF(p2["x"], p2["y"])
                    )
                
                # Draw 7-day moving average if enough data
                ma_data = self._calculate_moving_average()
                if len(ma_data) >= 2:
                    painter.setPen(QtGui.QPen(QtGui.QColor("#ffaa00"), 2))
                    for i in range(len(ma_data) - 1):
                        x1 = date_to_x(ma_data[i][0])
                        y1 = weight_to_y(ma_data[i][1])
                        x2 = date_to_x(ma_data[i + 1][0])
                        y2 = weight_to_y(ma_data[i + 1][1])
                        painter.drawLine(QtCore.QPointF(x1, y1), QtCore.QPointF(x2, y2))
                    
                    # MA legend
                    painter.setPen(QtGui.QColor("#ffaa00"))
                    painter.setFont(QtGui.QFont("Segoe UI", 8))
                    painter.drawText(chart_rect.right() - 80, chart_rect.top() + 15, "7-day avg")
            
            # Draw data points
            for i, p in enumerate(points):
                # Determine point color based on trend
                if i > 0:
                    prev_weight = points[i - 1]["weight"]
                    if p["weight"] < prev_weight:
                        color = QtGui.QColor("#00ff88")  # Green - lost weight
                    elif p["weight"] > prev_weight:
                        color = QtGui.QColor("#ff6464")  # Red - gained weight
                    else:
                        color = QtGui.QColor("#ffff64")  # Yellow - same
                else:
                    color = QtGui.QColor("#6496ff")  # Blue - first point
                
                # Hollow point for gap interpolation indicator
                if p["gap_before"] > 2:
                    # Draw gap indicator - small triangle pointing to gap
                    painter.setPen(QtGui.QPen(QtGui.QColor("#888888"), 1))
                    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                else:
                    painter.setBrush(color)
                    painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff"), 1))
                
                painter.drawEllipse(QtCore.QPointF(p["x"], p["y"]), 5, 5)
        
        # Draw date labels (smart distribution)
        painter.setPen(QtGui.QColor("#888888"))
        painter.setFont(QtGui.QFont("Segoe UI", 8))
        
        if total_days <= 14:
            # Show more dates for short ranges
            date_step = max(1, total_days // 5)
        elif total_days <= 60:
            date_step = 7  # Weekly
        else:
            date_step = 14  # Bi-weekly
        
        current_date = first_date
        while current_date <= last_date:
            x = date_to_x(current_date)
            date_label = current_date.strftime("%m/%d")
            painter.drawText(int(x) - 15, chart_rect.bottom() + 15, date_label)
            current_date += timedelta(days=date_step)
        
        # Always show last date if not too close to previous
        last_x = date_to_x(last_date)
        if last_x - date_to_x(current_date - timedelta(days=date_step)) > 30:
            painter.drawText(int(last_x) - 15, chart_rect.bottom() + 15, 
                           last_date.strftime("%m/%d"))


class WeightTab(QtWidgets.QWidget):
    """Weight tracking tab with chart, BMI, predictions, and gamification rewards."""
    
    def __init__(self, blocker: 'BlockerCore', parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self._reminder_timer = None
        self._build_ui()
        self._refresh_display()
        self._setup_reminder()
        # Ensure timer is cleaned up when widget is destroyed
        self.destroyed.connect(self._cleanup_timer)
    
    def _cleanup_timer(self) -> None:
        """Stop the reminder timer when the widget is destroyed."""
        if self._reminder_timer is not None:
            self._reminder_timer.stop()
            self._reminder_timer = None
    
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header with insights button
        header_layout = QtWidgets.QHBoxLayout()
        header = QtWidgets.QLabel("⚖️ Weight Tracker")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        insights_btn = QtWidgets.QPushButton("📊 Weekly Insights")
        insights_btn.clicked.connect(self._show_weekly_insights)
        header_layout.addWidget(insights_btn)
        
        layout.addLayout(header_layout)
        
        # Top section: Input and stats side by side
        top_layout = QtWidgets.QHBoxLayout()
        
        # Left: Weight input section
        input_group = QtWidgets.QGroupBox("📝 Log Weight")
        input_layout = QtWidgets.QFormLayout(input_group)
        input_layout.setSpacing(8)
        
        # Weight input
        weight_row = QtWidgets.QHBoxLayout()
        self.weight_input = QtWidgets.QDoubleSpinBox()
        self.weight_input.setRange(20, 500)
        self.weight_input.setDecimals(1)
        self.weight_input.setSingleStep(0.1)
        self.weight_input.setValue(70.0)
        self.weight_input.setSuffix(" kg")
        self.weight_input.setFixedWidth(120)
        weight_row.addWidget(self.weight_input)
        
        # Unit toggle
        self.unit_combo = NoScrollComboBox()
        self.unit_combo.addItems(["kg", "lbs"])
        self.unit_combo.setFixedWidth(60)
        self.unit_combo.currentTextChanged.connect(self._on_unit_changed)
        weight_row.addWidget(self.unit_combo)
        weight_row.addStretch()
        input_layout.addRow("Weight:", weight_row)
        
        # Date input (default to today, max = today to prevent future dates)
        self.date_edit = QtWidgets.QDateEdit()
        self.date_edit.setDate(QtCore.QDate.currentDate())
        self.date_edit.setMaximumDate(QtCore.QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        input_layout.addRow("Date:", self.date_edit)
        
        # Note/Context (tag selection)
        note_row = QtWidgets.QHBoxLayout()
        self.note_combo = NoScrollComboBox()
        self.note_combo.addItem("(none)", "")
        if WEIGHT_ENTRY_TAGS:
            for tag_id, tag_display, tooltip in WEIGHT_ENTRY_TAGS:
                self.note_combo.addItem(tag_display, tag_id)
        self.note_combo.setFixedWidth(150)
        note_row.addWidget(self.note_combo)
        note_row.addStretch()
        input_layout.addRow("Context:", note_row)
        
        # Goal weight with enable checkbox
        goal_row = QtWidgets.QHBoxLayout()
        self.goal_enabled = QtWidgets.QCheckBox()
        self.goal_enabled.setToolTip("Enable/disable goal weight")
        self.goal_enabled.stateChanged.connect(self._on_goal_toggle)
        goal_row.addWidget(self.goal_enabled)
        
        self.goal_input = QtWidgets.QDoubleSpinBox()
        self.goal_input.setRange(1, 500)
        self.goal_input.setDecimals(1)
        self.goal_input.setSingleStep(0.1)
        self.goal_input.setValue(70.0)
        self.goal_input.setFixedWidth(100)
        self.goal_input.setEnabled(False)
        goal_row.addWidget(self.goal_input)
        
        set_goal_btn = QtWidgets.QPushButton("Set")
        set_goal_btn.setFixedWidth(40)
        set_goal_btn.clicked.connect(self._set_goal)
        goal_row.addWidget(set_goal_btn)
        goal_row.addStretch()
        input_layout.addRow("Goal:", goal_row)
        
        # Height input for BMI
        height_row = QtWidgets.QHBoxLayout()
        self.height_input = QtWidgets.QSpinBox()
        self.height_input.setRange(100, 250)
        self.height_input.setValue(170)
        self.height_input.setSuffix(" cm")
        self.height_input.setFixedWidth(80)
        height_row.addWidget(self.height_input)
        
        set_height_btn = QtWidgets.QPushButton("Set")
        set_height_btn.setFixedWidth(40)
        set_height_btn.clicked.connect(self._set_height)
        height_row.addWidget(set_height_btn)
        
        self.bmi_label = QtWidgets.QLabel("")
        self.bmi_label.setStyleSheet("font-size: 11px; margin-left: 10px;")
        height_row.addWidget(self.bmi_label)
        height_row.addStretch()
        input_layout.addRow("Height:", height_row)
        
        # Log button
        log_btn = QtWidgets.QPushButton("📊 Log Weight")
        log_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5aa0e9;
            }
        """)
        log_btn.clicked.connect(self._log_weight)
        input_layout.addRow("", log_btn)
        
        top_layout.addWidget(input_group)
        
        # Right: Stats + Comparisons display
        right_panel = QtWidgets.QVBoxLayout()
        
        # Stats section
        stats_group = QtWidgets.QGroupBox("📈 Statistics")
        stats_layout = QtWidgets.QVBoxLayout(stats_group)
        stats_layout.setSpacing(5)
        
        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("font-size: 11px; line-height: 1.4;")
        stats_layout.addWidget(self.stats_label)
        
        # Prediction label
        self.prediction_label = QtWidgets.QLabel()
        self.prediction_label.setWordWrap(True)
        self.prediction_label.setStyleSheet("font-size: 11px; margin-top: 5px;")
        stats_layout.addWidget(self.prediction_label)
        
        right_panel.addWidget(stats_group)
        
        # Comparisons section
        compare_group = QtWidgets.QGroupBox("📅 Historical")
        compare_layout = QtWidgets.QVBoxLayout(compare_group)
        compare_layout.setSpacing(3)
        
        self.compare_label = QtWidgets.QLabel()
        self.compare_label.setWordWrap(True)
        self.compare_label.setStyleSheet("font-size: 10px; color: #aaaaaa;")
        compare_layout.addWidget(self.compare_label)
        
        right_panel.addWidget(compare_group)
        
        top_layout.addLayout(right_panel)
        layout.addLayout(top_layout)
        
        # Chart section
        chart_group = QtWidgets.QGroupBox("📉 Progress Chart")
        chart_layout = QtWidgets.QVBoxLayout(chart_group)
        
        self.chart = WeightChartWidget()
        chart_layout.addWidget(self.chart)
        
        layout.addWidget(chart_group, 1)
        
        # Bottom row: Recent entries and settings
        bottom_layout = QtWidgets.QHBoxLayout()
        
        # Recent entries table
        entries_group = QtWidgets.QGroupBox("📋 Recent Entries")
        entries_layout = QtWidgets.QVBoxLayout(entries_group)
        
        self.entries_table = QtWidgets.QTableWidget()
        self.entries_table.setColumnCount(5)
        self.entries_table.setHorizontalHeaderLabels(["Date", "Weight", "Note", "Change", "Del"])
        self.entries_table.horizontalHeader().setStretchLastSection(True)
        self.entries_table.setMaximumHeight(130)
        self.entries_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        entries_layout.addWidget(self.entries_table)
        
        bottom_layout.addWidget(entries_group, 2)
        
        # Reminder settings
        settings_group = QtWidgets.QGroupBox("⏰ Reminder")
        settings_layout = QtWidgets.QFormLayout(settings_group)
        settings_layout.setSpacing(5)
        
        self.reminder_enabled = QtWidgets.QCheckBox("Daily reminder")
        self.reminder_enabled.stateChanged.connect(self._on_reminder_toggle)
        settings_layout.addRow(self.reminder_enabled)
        
        self.reminder_time = QtWidgets.QTimeEdit()
        self.reminder_time.setDisplayFormat("HH:mm")
        self.reminder_time.setTime(QtCore.QTime(8, 0))
        self.reminder_time.timeChanged.connect(self._on_reminder_time_changed)
        settings_layout.addRow("Time:", self.reminder_time)
        
        bottom_layout.addWidget(settings_group, 1)
        
        layout.addLayout(bottom_layout)
        
        # Rewards info (collapsed)
        rewards_group = QtWidgets.QGroupBox("🎁 Rewards Info")
        rewards_layout = QtWidgets.QVBoxLayout(rewards_group)
        rewards_info = QtWidgets.QLabel(
            "<b>How it works:</b> Log daily weight to earn 1 item. Reward rarity based on weight loss since previous entry.<br>"
            "<i>Weight gain = no daily reward (maintain streak for rewards)</i><br>"
            "<table style='font-size:10px; color:#888888; margin-top:5px;'>"
            "<tr><th>Daily Loss</th><th>Common</th><th>Uncommon</th><th>Rare</th><th>Epic</th><th>Legendary</th></tr>"
            "<tr><td>0g (maintain)</td><td>75%</td><td>20%</td><td>5%</td><td>-</td><td>-</td></tr>"
            "<tr><td>100g+</td><td>25%</td><td>50%</td><td>20%</td><td>5%</td><td>-</td></tr>"
            "<tr><td>200g+</td><td>5%</td><td>20%</td><td>50%</td><td>20%</td><td>5%</td></tr>"
            "<tr><td>300g+</td><td>-</td><td>5%</td><td>20%</td><td>50%</td><td>25%</td></tr>"
            "<tr><td>400g+</td><td>-</td><td>-</td><td>-</td><td>5%</td><td>95%</td></tr>"
            "<tr><td>500g+</td><td>-</td><td>-</td><td>-</td><td>-</td><td>100%</td></tr>"
            "</table>"
            "<br><b>Weekly:</b> 300g=Epic, 500g=Legendary | <b>Monthly:</b> 1.5kg=Epic, 2kg=Legendary | "
            "<b>Streaks:</b> 7d=Rare, 14d=Epic, 30d+=Legendary"
        )
        rewards_info.setWordWrap(True)
        rewards_info.setStyleSheet("color: #888888; font-size: 10px;")
        rewards_layout.addWidget(rewards_info)
        layout.addWidget(rewards_group)
        
        # =====================================================================
        # Rodent Tips Section - Shows daily weight control tips when any rodent is collected
        # Requires scientist_009 (White Mouse Archimedes) for translation from "rodent language"
        # =====================================================================
        self.rodent_tips_section = QtWidgets.QFrame()
        self.rodent_tips_section.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a3a2a, stop:1 #252518);
                border: 2px solid #8b7355;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        rodent_tips_layout = QtWidgets.QHBoxLayout(self.rodent_tips_section)
        rodent_tips_layout.setContentsMargins(8, 6, 8, 6)
        rodent_tips_layout.setSpacing(10)
        
        # Left: Icon (rodent entity icon)
        self.rodent_icon_label = QtWidgets.QLabel()
        self.rodent_icon_label.setFixedSize(40, 40)
        self.rodent_icon_label.setStyleSheet("""
            QLabel {
                background: #333;
                border: 1px solid #444;
                border-radius: 4px;
            }
        """)
        rodent_tips_layout.addWidget(self.rodent_icon_label)
        
        # Middle: Title + Tip text (expandable)
        rodent_content_col = QtWidgets.QVBoxLayout()
        rodent_content_col.setSpacing(2)
        
        # Title row with entity name and tip number
        rodent_title_row = QtWidgets.QHBoxLayout()
        self.rodent_section_title = QtWidgets.QLabel("🐀 Rodent Squad Weight Tips")
        self.rodent_section_title.setStyleSheet("color: #c4a35a; font-size: 11px; font-weight: bold;")
        rodent_title_row.addWidget(self.rodent_section_title)
        
        self.rodent_tip_number = QtWidgets.QLabel("Tip #1 of 100")
        self.rodent_tip_number.setStyleSheet("color: #8b7355; font-size: 10px;")
        rodent_title_row.addWidget(self.rodent_tip_number)
        rodent_title_row.addStretch()
        rodent_content_col.addLayout(rodent_title_row)
        
        # Tip text (compact)
        self.rodent_tip_text = QtWidgets.QLabel("Loading tip...")
        self.rodent_tip_text.setStyleSheet("color: #d4c4a4; font-size: 11px;")
        self.rodent_tip_text.setWordWrap(True)
        rodent_content_col.addWidget(self.rodent_tip_text)
        
        # Hidden: tracks if user has the telepathic translator
        self.has_translator = False
        
        rodent_tips_layout.addLayout(rodent_content_col, 1)
        
        # Right: Acknowledge button (compact)
        self.rodent_acknowledge_btn = QtWidgets.QPushButton("📖 +1🪙")
        self.rodent_acknowledge_btn.setFixedWidth(70)
        self.rodent_acknowledge_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8b7355, stop:1 #6b5335);
                color: white;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
                border: 1px solid #5b4325;
                padding: 6px 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #a68365, stop:1 #8b7355);
            }
            QPushButton:disabled {
                background: #444;
                color: #777;
                border: 1px solid #333;
            }
        """)
        self.rodent_acknowledge_btn.clicked.connect(self._acknowledge_rodent_tip)
        rodent_tips_layout.addWidget(self.rodent_acknowledge_btn)
        
        layout.addWidget(self.rodent_tips_section)
        self.rodent_tips_section.hide()  # Hidden until we check if any rodent is collected
        
        # Entity Perk Section (Rodent Squad) - shows when rat/mouse entities are collected
        # Uses same mini-card pattern as ADHD Buster patrons
        self.weight_entity_section = CollapsibleSection("🐀 Rodent Squad", "weight_entity_section", parent=self)
        self.weight_entity_section.setVisible(False)
        layout.addWidget(self.weight_entity_section)
        
        # Initialize settings from saved values
        self._load_settings()
        
        # Update entity perk display
        self._update_weight_entity_perk_display()
        
        # Refresh rodent tips
        self._refresh_rodent_tips()
    
    def _on_goal_toggle(self, state: int) -> None:
        """Handle goal checkbox toggle."""
        enabled = state == QtCore.Qt.CheckState.Checked.value
        self.goal_input.setEnabled(enabled)
        if not enabled:
            self.blocker.weight_goal = None
            self.blocker.save_config()
            self._refresh_display()
    
    def _on_unit_changed(self, unit: str) -> None:
        """Handle unit change."""
        self.weight_input.setSuffix(f" {unit}")
        self.goal_input.setSuffix(f" {unit}")
        if unit == "lbs":
            self.weight_input.setRange(44, 1100)  # ~20-500 kg in lbs
            self.goal_input.setRange(2.2, 1100)   # ~1-500 kg in lbs
        else:
            self.weight_input.setRange(20, 500)
            self.goal_input.setRange(1, 500)
        self.blocker.weight_unit = unit
        self.blocker.save_config()
        self._refresh_display()
    
    def _set_goal(self) -> None:
        """Set the goal weight."""
        if not self.goal_enabled.isChecked():
            self.blocker.weight_goal = None
            self.blocker.save_config()
            self._refresh_display()
            show_info(self, "Goal Cleared", 
                "Goal weight has been cleared. Check the box and set a value to enable.")
            return
        
        goal = self.goal_input.value()
        unit = self.unit_combo.currentText()
        # Store goal in kg for consistency
        self.blocker.weight_goal = goal / 2.20462 if unit == "lbs" else goal
        self.blocker.save_config()
        self._refresh_display()
        show_info(self, "Goal Set", 
            f"Goal weight set to {goal:.1f} {unit}")
    
    def _log_weight(self) -> None:
        """Log a new weight entry."""
        weight = self.weight_input.value()
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        unit = self.unit_combo.currentText()
        
        # Convert to kg for storage if needed
        weight_kg = weight / 2.20462 if unit == "lbs" else weight
        
        # Check if entry already exists for this date
        existing_idx = None
        for i, entry in enumerate(self.blocker.weight_entries):
            if entry.get("date") == date_str:
                existing_idx = i
                break
        
        # For reward calculation, we need entries WITHOUT the current date
        # This ensures updating an entry compares against historical data only
        entries_for_reward = [e for e in self.blocker.weight_entries if e.get("date") != date_str]
        
        # Check for rewards before adding entry (use comprehensive function if available)
        # Skip if gamification mode is disabled (same as focus sessions)
        rewards = None
        if GAMIFICATION_AVAILABLE and check_all_weight_rewards and is_gamification_enabled(self.blocker.adhd_buster):
            story_id = self.blocker.adhd_buster.get("active_story", "warrior")
            rewards = check_all_weight_rewards(
                entries_for_reward, 
                weight_kg, 
                date_str,
                self.blocker.weight_goal,
                self.blocker.weight_milestones,
                story_id,
                self.blocker.adhd_buster
            )
        elif GAMIFICATION_AVAILABLE and check_weight_entry_rewards and is_gamification_enabled(self.blocker.adhd_buster):
            # Fallback to basic rewards
            story_id = self.blocker.adhd_buster.get("active_story", "warrior")
            rewards = check_weight_entry_rewards(
                entries_for_reward, 
                weight_kg, 
                date_str,
                story_id,
                self.blocker.adhd_buster
            )
        
        # Update or add entry
        # Get note from combo
        note = self.note_combo.currentData() or ""
        
        new_entry = {"date": date_str, "weight": weight_kg}
        if note:
            new_entry["note"] = note
        
        if existing_idx is not None:
            reply = show_question(
                self, "Update Entry",
                f"An entry for {date_str} already exists.\nUpdate it to {weight:.1f} {unit}?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
            self.blocker.weight_entries[existing_idx] = new_entry
        else:
            self.blocker.weight_entries.append(new_entry)
            # Sort by date
            self.blocker.weight_entries.sort(key=lambda x: x.get("date", ""))
            # Prune to last 365 entries to prevent unbounded growth
            if len(self.blocker.weight_entries) > 365:
                self.blocker.weight_entries = self.blocker.weight_entries[-365:]
        
        self.blocker.save_config()
        
        # Process rewards
        if rewards and GAMIFICATION_AVAILABLE:
            self._process_rewards(rewards)
        
        self._refresh_display()
    
    def _process_rewards(self, rewards: dict) -> None:
        """Process and show weight loss rewards."""
        items_earned = []
        new_milestone_ids = []
        
        # Collect all earned items - Daily/Weekly/Monthly (use defensive copies)
        # Items will be added to inventory via game_state at the end
        if rewards.get("daily_reward"):
            item = rewards["daily_reward"]
            items_earned.append(("Daily", item))
        
        if rewards.get("weekly_reward"):
            item = rewards["weekly_reward"]
            items_earned.append(("Weekly Bonus", item))
        
        if rewards.get("monthly_reward"):
            item = rewards["monthly_reward"]
            items_earned.append(("Monthly Bonus", item))
        
        # Streak reward
        if rewards.get("streak_reward"):
            streak_data = rewards["streak_reward"]
            item = streak_data["item"]
            items_earned.append((f"🔥 {streak_data['streak_days']}-Day Streak", item))
            new_milestone_ids.append(streak_data["milestone_id"])
        
        # Milestone rewards
        for milestone in rewards.get("new_milestones", []):
            item = milestone["item"]
            items_earned.append((f"🏆 {milestone['name']}", item))
            new_milestone_ids.append(milestone["milestone_id"])
        
        # Maintenance reward (only if no daily reward to avoid double-rewarding)
        if rewards.get("maintenance_reward") and not rewards.get("daily_reward"):
            maint_data = rewards["maintenance_reward"]
            item = maint_data["item"]
            items_earned.append(("⚖️ Maintenance", item))
        
        # Save new milestones
        if new_milestone_ids:
            self.blocker.weight_milestones.extend(new_milestone_ids)
        
        # Generate diary entry (once per day, same as focus sessions)
        diary_entry = None
        if items_earned and GAMIFICATION_AVAILABLE and generate_diary_entry and calculate_character_power:
            today = datetime.now().strftime("%Y-%m-%d")
            diary = self.blocker.adhd_buster.get("diary", [])
            today_entries = [e for e in diary if e.get("date") == today]
            
            if not today_entries:
                power = calculate_character_power(self.blocker.adhd_buster)
                equipped = self.blocker.adhd_buster.get("equipped", {})
                active_story = self.blocker.adhd_buster.get("active_story", "warrior")
                diary_entry = generate_diary_entry(power, session_minutes=0, equipped_items=equipped,
                                                   story_id=active_story)
                if "diary" not in self.blocker.adhd_buster:
                    self.blocker.adhd_buster["diary"] = []
                self.blocker.adhd_buster["diary"].append(diary_entry)
                # Keep only last 100 entries
                if len(self.blocker.adhd_buster["diary"]) > 100:
                    self.blocker.adhd_buster["diary"] = self.blocker.adhd_buster["diary"][-100:]
        
        if items_earned:
            # Extract just the items for the batch award
            just_items = [item for _, item in items_earned]
            
            # Use GameState manager for reactive updates
            main_window = self.window()
            game_state = getattr(main_window, 'game_state', None)
            if not game_state:
                logger.error("GameStateManager not available - cannot award weight rewards")
                return
            
            # Use batch award - handles inventory, auto-equip, save, and signals
            game_state.award_items_batch(just_items, coins=0, auto_equip=True, source="weight_tracking")
            
            # Sync hero data
            if GAMIFICATION_AVAILABLE and sync_hero_data:
                sync_hero_data(self.blocker.adhd_buster)
                self.blocker.save_config()
            
            # Build reward message with rarity colors
            rarity_colors = {
                "Common": "#9e9e9e",
                "Uncommon": "#4caf50", 
                "Rare": "#2196f3",
                "Epic": "#9c27b0",
                "Legendary": "#ff9800"
            }
            msg_parts = []
            for source, item in items_earned:
                rarity = item.get("rarity", "Common")
                name = item.get("name", "Unknown Item")
                color = rarity_colors.get(rarity, "#9e9e9e")
                msg_parts.append(f"<b>{source}:</b> <span style='color:{color}; font-weight:bold;'>[{rarity}]</span> {name}")
            
            # Add loss stats
            stats_parts = []
            if rewards.get("daily_loss_grams") is not None:
                loss = rewards["daily_loss_grams"]
                if loss > 0:
                    stats_parts.append(f"Daily: -{loss:.0f}g")
                elif loss < 0:
                    stats_parts.append(f"Daily: +{abs(loss):.0f}g")
            if rewards.get("weekly_loss_grams") is not None:
                stats_parts.append(f"Weekly: {rewards['weekly_loss_grams']:.0f}g")
            if rewards.get("monthly_loss_grams") is not None:
                stats_parts.append(f"Monthly: {rewards['monthly_loss_grams']/1000:.1f}kg")
            
            # Add streak info
            if rewards.get("current_streak", 0) > 0:
                stats_parts.append(f"Streak: {rewards['current_streak']} days")
            
            msg = "<br>".join(msg_parts)
            if stats_parts:
                msg += "<br><br><i>" + " | ".join(stats_parts) + "</i>"
            
            show_info(
                self, "🎉 Weight Rewards!",
                f"<h3>Congratulations!</h3>{msg}"
            )
            
            # Show diary entry reveal (same as focus sessions)
            if diary_entry:
                DiaryEntryRevealDialog(self.blocker, diary_entry, session_minutes=0, parent=self.window()).exec()
            
            # UI updates are handled via GameState signals
        elif rewards.get("messages"):
            # Show info messages even if no rewards
            show_info(
                self, "Weight Logged",
                "\n".join(rewards["messages"])
            )
    
    def _delete_entry(self, date_str: str) -> None:
        """Delete a weight entry."""
        reply = show_question(
            self, "Delete Entry",
            f"Delete the entry for {date_str}?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.blocker.weight_entries = [
                e for e in self.blocker.weight_entries if e.get("date") != date_str
            ]
            self.blocker.save_config()
            self._refresh_display()
    
    def _refresh_display(self) -> None:
        """Refresh all display elements."""
        # Update max date to today (in case app stayed open past midnight)
        self.date_edit.setMaximumDate(QtCore.QDate.currentDate())
        
        unit = self.blocker.weight_unit
        entries = self.blocker.weight_entries
        
        # Update chart
        self.chart.set_data(entries, self.blocker.weight_goal, unit)
        
        # Update stats
        if get_weight_stats:
            stats = get_weight_stats(entries, unit)
            if stats["current"] is not None and stats["starting"] is not None:
                current_display = stats["current"] * 2.20462 if unit == "lbs" else stats["current"]
                starting_display = stats["starting"] * 2.20462 if unit == "lbs" else stats["starting"]
                
                # Check maintenance status
                maintenance_status = ""
                if self.blocker.weight_goal and stats["current"] is not None:
                    deviation = abs(stats["current"] - self.blocker.weight_goal)
                    if deviation <= 0.5:
                        maintenance_status = "<br><b style='color:#00ff88'>⚖️ MAINTENANCE MODE</b> (within ±0.5kg of goal)"
                
                # Milestone count
                milestone_count = len(self.blocker.weight_milestones)
                milestone_text = f" | <b>Milestones:</b> {milestone_count}" if milestone_count > 0 else ""
                
                # Streak display with fire emoji for active streaks
                streak = stats['streak_days']
                if streak >= 7:
                    streak_display = f"🔥 {streak} days"
                else:
                    streak_display = f"{streak} days"
                
                stats_text = f"""
<b>Current:</b> {current_display:.1f} {unit}<br>
<b>Starting:</b> {starting_display:.1f} {unit}<br>
<b>Total Change:</b> {format_weight_change(stats['total_change'], unit) if format_weight_change else 'N/A'}<br>
<b>7-Day Trend:</b> {format_weight_change(stats['trend_7d'], unit) if format_weight_change else 'N/A'}<br>
<b>30-Day Trend:</b> {format_weight_change(stats['trend_30d'], unit) if format_weight_change else 'N/A'}<br>
<b>Entries:</b> {stats['entries_count']} | <b>Streak:</b> {streak_display}{milestone_text}{maintenance_status}
"""
                self.stats_label.setText(stats_text)
            else:
                self.stats_label.setText("No weight entries yet.\nStart logging to see your stats!")
        else:
            self.stats_label.setText("Statistics unavailable")
        
        # Update entries table
        self.entries_table.setRowCount(0)
        sorted_entries = sorted(entries, key=lambda x: x.get("date", ""), reverse=True)[:10]
        
        for i, entry in enumerate(sorted_entries):
            self.entries_table.insertRow(i)
            
            # Date
            self.entries_table.setItem(i, 0, QtWidgets.QTableWidgetItem(entry.get("date", "")))
            
            # Weight
            weight_kg = entry.get("weight", 0)
            weight_display = weight_kg * 2.20462 if unit == "lbs" else weight_kg
            self.entries_table.setItem(i, 1, QtWidgets.QTableWidgetItem(f"{weight_display:.1f} {unit}"))
            
            # Note (formatted)
            note = entry.get("note", "")
            note_display = format_entry_note(note) if format_entry_note and note else ""
            self.entries_table.setItem(i, 2, QtWidgets.QTableWidgetItem(note_display))
            
            # Change (from previous entry to this entry)
            if i < len(sorted_entries) - 1:
                prev_weight = sorted_entries[i + 1].get("weight", weight_kg)
                # change = current - previous (negative = lost weight, positive = gained)
                change = (weight_kg - prev_weight) * 1000  # in grams
                if unit == "lbs":
                    # Convert grams to kg, then kg to lbs
                    change_lbs = (change / 1000) * 2.20462
                    change_text = f"{change_lbs:+.2f} lbs" if abs(change_lbs) >= 0.05 else "—"
                else:
                    change_text = f"{change:+.0f}g" if abs(change) >= 10 else "—"
                
                change_item = QtWidgets.QTableWidgetItem(change_text)
                if change < 0:
                    change_item.setForeground(QtGui.QColor("#00ff88"))  # Green = lost weight
                elif change > 0:
                    change_item.setForeground(QtGui.QColor("#ff6464"))  # Red = gained
                self.entries_table.setItem(i, 3, change_item)
            else:
                self.entries_table.setItem(i, 3, QtWidgets.QTableWidgetItem("—"))
            
            # Delete button
            delete_btn = QtWidgets.QPushButton("🗑")
            delete_btn.setFixedWidth(30)
            date_str = entry.get("date", "")
            delete_btn.clicked.connect(lambda checked, d=date_str: self._delete_entry(d))
            self.entries_table.setCellWidget(i, 4, delete_btn)
        
        self.entries_table.resizeColumnsToContents()
        
        # Update BMI display
        self._update_bmi_display()
        
        # Update prediction
        self._update_prediction()
        
        # Update historical comparisons
        self._update_comparisons()
    
    def _load_settings(self) -> None:
        """Load saved settings into UI controls."""
        # Unit
        if self.blocker.weight_unit == "lbs":
            self.weight_input.setRange(44, 1100)
            self.weight_input.setSuffix(" lbs")
            self.goal_input.setRange(2.2, 1100)
        self.unit_combo.setCurrentText(self.blocker.weight_unit)
        
        # Goal
        if self.blocker.weight_goal:
            goal_display = self.blocker.weight_goal * 2.20462 if self.blocker.weight_unit == "lbs" else self.blocker.weight_goal
            self.goal_input.setValue(goal_display)
            self.goal_enabled.setChecked(True)
            self.goal_input.setEnabled(True)
        
        # Height
        if self.blocker.weight_height:
            self.height_input.setValue(self.blocker.weight_height)
        
        # Reminder
        self.reminder_enabled.setChecked(self.blocker.weight_reminder_enabled)
        if self.blocker.weight_reminder_time:
            try:
                h, m = map(int, self.blocker.weight_reminder_time.split(":"))
                self.reminder_time.setTime(QtCore.QTime(h, m))
            except (ValueError, AttributeError):
                pass
    
    def _set_height(self) -> None:
        """Set the height for BMI calculation."""
        height = self.height_input.value()
        self.blocker.weight_height = height
        self.blocker.save_config()
        self._update_bmi_display()
        show_info(self, "Height Set", f"Height set to {height} cm")
    
    def _update_bmi_display(self) -> None:
        """Update the BMI label with current BMI."""
        if not self.blocker.weight_height or not self.blocker.weight_entries:
            self.bmi_label.setText("")
            return
        
        # Get latest weight
        sorted_entries = sorted(self.blocker.weight_entries, key=lambda x: x.get("date", ""))
        if not sorted_entries:
            self.bmi_label.setText("")
            return
        
        latest_weight = sorted_entries[-1].get("weight", 0)
        
        if calculate_bmi:
            bmi = calculate_bmi(latest_weight, self.blocker.weight_height)
            if bmi and get_bmi_classification:
                classification, color = get_bmi_classification(bmi)
                self.bmi_label.setText(f"<b style='color:{color}'>BMI: {bmi:.1f} ({classification})</b>")
            else:
                self.bmi_label.setText("")
        else:
            self.bmi_label.setText("")
    
    def _update_prediction(self) -> None:
        """Update the goal prediction display."""
        if not self.blocker.weight_goal or not self.blocker.weight_entries:
            self.prediction_label.setText("")
            return
        
        sorted_entries = sorted(self.blocker.weight_entries, key=lambda x: x.get("date", ""))
        if len(sorted_entries) < 3:
            self.prediction_label.setText("<i>Need 3+ entries for prediction</i>")
            return
        
        latest_weight = sorted_entries[-1].get("weight", 0)
        
        if predict_goal_date:
            prediction = predict_goal_date(sorted_entries, self.blocker.weight_goal, latest_weight)
            if prediction:
                status = prediction.get("status", "")
                if status == "achieved":
                    self.prediction_label.setText("<b style='color:#00ff88'>🎯 Goal reached!</b>")
                elif prediction.get("predicted_date"):
                    days = prediction.get("days_remaining", 0)
                    pred_date = prediction["predicted_date"]
                    # Format datetime to string if needed
                    if hasattr(pred_date, 'strftime'):
                        date_str = pred_date.strftime("%b %d, %Y")
                    else:
                        date_str = str(pred_date)
                    if days and days > 0:
                        self.prediction_label.setText(f"📅 Estimated goal: <b>{date_str}</b> ({days} days)")
                    else:
                        self.prediction_label.setText(f"📅 Estimated goal: <b>{date_str}</b>")
                else:
                    msg = prediction.get("message", "")
                    self.prediction_label.setText(f"<i>{msg}</i>" if msg else "")
            else:
                self.prediction_label.setText("")
        else:
            self.prediction_label.setText("")
    
    def _update_comparisons(self) -> None:
        """Update historical comparison display."""
        if not self.blocker.weight_entries:
            self.compare_label.setText("No data for comparisons")
            return
        
        if get_historical_comparisons:
            comparisons = get_historical_comparisons(self.blocker.weight_entries)
            if comparisons:
                parts = []
                unit = self.blocker.weight_unit
                
                # Determine if goal is to lose or gain weight
                is_losing_goal = True  # Default: assume weight loss
                if self.blocker.weight_goal and self.blocker.weight_entries:
                    sorted_e = sorted(self.blocker.weight_entries, key=lambda x: x.get("date", ""))
                    if sorted_e:
                        current = sorted_e[-1].get("weight", 0)
                        is_losing_goal = self.blocker.weight_goal < current
                
                for period_key, data in comparisons.items():
                    if data is not None and isinstance(data, dict):
                        label = data.get("label", period_key)
                        change_kg = data.get("change", 0)
                        
                        if unit == "lbs":
                            change_display = change_kg * 2.20462
                            suffix = "lbs"
                        else:
                            change_display = change_kg
                            suffix = "kg"
                        
                        # Color based on goal direction
                        if is_losing_goal:
                            # Losing goal: negative change (lost weight) is good
                            if change_kg < 0:
                                color = "#00ff88"
                            elif change_kg > 0:
                                color = "#ff6464"
                            else:
                                color = "#888888"
                        else:
                            # Gaining goal: positive change (gained weight) is good
                            if change_kg > 0:
                                color = "#00ff88"
                            elif change_kg < 0:
                                color = "#ff6464"
                            else:
                                color = "#888888"
                        
                        sign = "+" if change_kg > 0 else ""
                        parts.append(f"<span style='color:{color}'>{label}: {sign}{change_display:.1f} {suffix}</span>")
                
                if parts:
                    self.compare_label.setText("<br>".join(parts))
                else:
                    self.compare_label.setText("Not enough historical data")
            else:
                self.compare_label.setText("Not enough historical data")
        else:
            self.compare_label.setText("Comparisons unavailable")
    
    def _on_reminder_toggle(self, state: int) -> None:
        """Handle reminder checkbox toggle."""
        enabled = state == QtCore.Qt.CheckState.Checked.value
        self.blocker.weight_reminder_enabled = enabled
        self.blocker.save_config()
        self._setup_reminder()
    
    def _on_reminder_time_changed(self, time: QtCore.QTime) -> None:
        """Handle reminder time change."""
        self.blocker.weight_reminder_time = time.toString("HH:mm")
        self.blocker.save_config()
        self._setup_reminder()
    
    def _setup_reminder(self) -> None:
        """Set up or cancel the reminder timer."""
        if self._reminder_timer:
            self._reminder_timer.stop()
            self._reminder_timer = None
        
        if not self.blocker.weight_reminder_enabled:
            return
        
        # Check every minute
        self._reminder_timer = QtCore.QTimer(self)
        self._reminder_timer.timeout.connect(self._check_reminder)
        self._reminder_timer.start(60000)  # 60 seconds
    
    def _check_reminder(self) -> None:
        """Check if reminder should be shown."""
        if not self.blocker.weight_reminder_enabled:
            return
        
        today = datetime.date.today().isoformat()
        
        # Skip if already reminded today
        if self.blocker.weight_last_reminder_date == today:
            return
        
        # Check if we already have an entry for today
        has_today_entry = any(e.get("date") == today for e in self.blocker.weight_entries)
        if has_today_entry:
            self.blocker.weight_last_reminder_date = today
            self.blocker.save_config()
            return
        
        # Check if it's at or after the reminder time
        current_time = QtCore.QTime.currentTime()
        reminder_time_str = self.blocker.weight_reminder_time or "08:00"
        try:
            h, m = map(int, reminder_time_str.split(":"))
            reminder_time = QtCore.QTime(h, m)
        except (ValueError, AttributeError):
            reminder_time = QtCore.QTime(8, 0)
        
        # Show reminder if current time is at or past reminder time
        if current_time >= reminder_time:
            self.blocker.weight_last_reminder_date = today
            self.blocker.save_config()
            self._show_reminder_notification()
    
    def _show_reminder_notification(self) -> None:
        """Show the weight reminder notification."""
        # Try system tray notification if available
        parent_window = self.window()
        if hasattr(parent_window, 'tray_icon') and parent_window.tray_icon:
            parent_window.tray_icon.showMessage(
                "⚖️ Weight Reminder",
                "Don't forget to log your weight today!",
                QtWidgets.QSystemTrayIcon.MessageIcon.Information,
                5000
            )
        else:
            # Fallback to message box (only if window is visible)
            if self.isVisible():
                show_info(
                    self, "⚖️ Weight Reminder",
                    "Don't forget to log your weight today!"
                )
    
    def _update_weight_entity_perk_display(self) -> None:
        """Update the entity perk display using mini-cards like ADHD Buster patrons."""
        try:
            adhd_data = getattr(self.blocker, 'adhd_buster', {})
            if not adhd_data:
                self.weight_entity_section.setVisible(False)
                return
            
            from gamification import get_entity_weight_perks
            weight_perks = get_entity_weight_perks(adhd_data)
            legendary_bonus = weight_perks.get("legendary_bonus", 0)
            contributors = weight_perks.get("contributors", [])
            
            # Hide if no bonus
            if legendary_bonus <= 0 or not contributors:
                self.weight_entity_section.setVisible(False)
                return
            
            # Show section with appropriate title
            self.weight_entity_section.setVisible(True)
            self.weight_entity_section.set_title(f"🐀 Rodent Squad (+{legendary_bonus}% Legendary)")
            
            # Clear previous content
            self.weight_entity_section.clear_content()
            
            # Try to import entity icon resolver
            try:
                from entitidex_tab import _resolve_entity_svg_path
                from entitidex.entity_pools import get_entity_by_id as get_entity
                from PySide6.QtSvg import QSvgRenderer
                has_svg_support = True
            except ImportError:
                has_svg_support = False
            
            # Create a horizontal flow layout for entity cards
            patrons_container = QtWidgets.QWidget()
            patrons_layout = QtWidgets.QHBoxLayout(patrons_container)
            patrons_layout.setContentsMargins(5, 5, 5, 5)
            patrons_layout.setSpacing(8)
            
            for entity_data in contributors:
                # Create a mini card for each entity
                card = QtWidgets.QFrame()
                is_exceptional = entity_data.get("is_exceptional", False)
                
                # Style cards - exceptional gets slightly lighter border
                if is_exceptional:
                    card.setStyleSheet("""
                        QFrame {
                            background-color: #2a2a2a;
                            border: 1px solid #555;
                            border-radius: 6px;
                            padding: 4px;
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
                            border-radius: 6px;
                            padding: 4px;
                        }
                        QFrame:hover {
                            border-color: #7986cb;
                            background-color: #333;
                        }
                    """)
                
                card_layout = QtWidgets.QVBoxLayout(card)
                card_layout.setContentsMargins(8, 6, 8, 6)
                card_layout.setSpacing(4)
                
                # Try to load entity SVG icon
                entity_id = entity_data.get("entity_id", "")
                icon_loaded = False
                
                if has_svg_support and entity_id:
                    try:
                        entity_obj = get_entity(entity_id)
                        if entity_obj:
                            svg_path = _resolve_entity_svg_path(entity_obj, is_exceptional)
                            if svg_path:
                                renderer = QSvgRenderer(svg_path)
                                if renderer.isValid():
                                    # Create pixmap from SVG (40x40 size for mini cards)
                                    icon_size = 40
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
                        pass  # Fall back to text display
                
                # Entity name with exceptional styling
                name = entity_data.get("name", "Unknown")
                # Truncate long names
                if len(name) > 18:
                    display_name = name[:15] + "..."
                else:
                    display_name = name
                
                if is_exceptional:
                    name_style = "color: #ffd700; font-weight: bold; font-size: 10px;"
                    prefix = "⭐ " if not icon_loaded else ""
                else:
                    name_style = "color: #ccc; font-size: 10px;"
                    prefix = ""
                
                name_lbl = QtWidgets.QLabel(f"{prefix}{display_name}")
                name_lbl.setStyleSheet(name_style)
                name_lbl.setAlignment(QtCore.Qt.AlignCenter)
                name_lbl.setToolTip(f"{name}")
                name_lbl.setWordWrap(True)
                card_layout.addWidget(name_lbl)
                
                # Bonus value
                bonus_val = entity_data.get("bonus", 0)
                bonus_lbl = QtWidgets.QLabel(f"<b>+{bonus_val}%</b> 🎲")
                bonus_lbl.setStyleSheet("color: #7986cb; font-size: 12px;")
                bonus_lbl.setAlignment(QtCore.Qt.AlignCenter)
                card_layout.addWidget(bonus_lbl)
                
                patrons_layout.addWidget(card)
            
            patrons_layout.addStretch()
            self.weight_entity_section.add_widget(patrons_container)
            
            # Add a tip
            tip_lbl = QtWidgets.QLabel("💡 Collect more Rodent entities in Entitidex to boost Legendary chance when logging weight!")
            tip_lbl.setStyleSheet("color: #888; font-style: italic; font-size: 10px; padding-top: 4px;")
            self.weight_entity_section.add_widget(tip_lbl)
            
        except Exception as e:
            print(f"[Weight Tab] Error updating entity perk display: {e}")
            self.weight_entity_section.setVisible(False)

    def _refresh_rodent_tips(self) -> None:
        """Refresh the Rodent Squad weight control tips section.
        
        Shows tips when user has any rodent entity collected.
        If user has scientist_009 (White Mouse Archimedes), they can understand
        the tips in human language. Otherwise, tips appear as "rodent language" squeaks.
        """
        from datetime import datetime
        
        # Rodent entity IDs that contribute to weight perks
        RODENT_ENTITY_IDS = ["scholar_001", "underdog_001", "scientist_004", 
                            "wanderer_009", "scientist_009"]
        TRANSLATOR_ENTITY_ID = "scientist_009"  # White Mouse Archimedes
        
        try:
            from gamification import get_entitidex_manager
            from entitidex_tab import _resolve_entity_svg_path
            from entitidex.entity_pools import get_entity_by_id as get_entity
            from weight_control_tips import get_tip_by_index, get_tip_count, has_telepathic_translator
        except ImportError as e:
            # Dependencies not available
            self.rodent_tips_section.setVisible(False)
            return
        
        # Get entitidex manager to check entity collection
        try:
            manager = get_entitidex_manager(self.blocker.adhd_buster)
        except Exception:
            self.rodent_tips_section.setVisible(False)
            return
        
        # Check if user has ANY rodent entity collected
        has_any_rodent = False
        first_rodent_id = None
        first_rodent_exceptional = False
        
        for entity_id in RODENT_ENTITY_IDS:
            has_normal = entity_id in manager.progress.collected_entity_ids
            has_exceptional = manager.progress.is_exceptional(entity_id)
            if has_normal or has_exceptional:
                has_any_rodent = True
                if first_rodent_id is None:
                    first_rodent_id = entity_id
                    first_rodent_exceptional = has_exceptional
                break
        
        if not has_any_rodent:
            # No rodent entities collected - hide section
            self.rodent_tips_section.setVisible(False)
            return
        
        # At least one rodent is collected - show section
        self.rodent_tips_section.setVisible(True)
        
        # Check if user has the telepathic translator (Archimedes)
        self.has_translator = has_telepathic_translator(self.blocker.adhd_buster)
        
        # Update section title and styling based on translator status
        if self.has_translator:
            self.rodent_section_title.setText("🐁 Rodent Squad Weight Control Tips")
            self.rodent_section_title.setStyleSheet("color: #81c784; font-size: 11px; font-weight: bold;")
            self.rodent_tips_section.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2a3a2a, stop:1 #182518);
                    border: 2px solid #66bb6a;
                    border-radius: 8px;
                    padding: 6px;
                }
            """)
        else:
            self.rodent_section_title.setText("🐭 Rodent Squad Tips (???)")
            self.rodent_section_title.setStyleSheet("color: #c4a35a; font-size: 11px; font-weight: bold;")
            self.rodent_tips_section.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3a3a2a, stop:1 #252518);
                    border: 2px solid #8b7355;
                    border-radius: 8px;
                    padding: 6px;
                }
            """)
        
        # Load first collected rodent's icon
        try:
            if first_rodent_id:
                entity = get_entity(first_rodent_id)
                if entity:
                    svg_path = _resolve_entity_svg_path(entity, first_rodent_exceptional)
                    if svg_path:
                        from PySide6.QtSvg import QSvgRenderer
                        renderer = QSvgRenderer(svg_path)
                        if renderer.isValid():
                            icon_size = 40
                            pixmap = QtGui.QPixmap(icon_size, icon_size)
                            pixmap.fill(QtCore.Qt.transparent)
                            painter = QtGui.QPainter(pixmap)
                            renderer.render(painter)
                            painter.end()
                            self.rodent_icon_label.setPixmap(pixmap)
                            
                            # Update icon border based on translator status
                            if self.has_translator:
                                self.rodent_icon_label.setStyleSheet("""
                                    QLabel {
                                        background: #333;
                                        border: 2px solid #66bb6a;
                                        border-radius: 6px;
                                    }
                                """)
                            else:
                                self.rodent_icon_label.setStyleSheet("""
                                    QLabel {
                                        background: #333;
                                        border: 1px solid #8b7355;
                                        border-radius: 6px;
                                    }
                                """)
        except Exception:
            # Fallback - just show text
            self.rodent_icon_label.setText("🐭")
        
        # Get current tip index (sequential cycling)
        tip_key = "rodent_tip_index_translated" if self.has_translator else "rodent_tip_index_squeaks"
        tip_index = self.blocker.stats.get(tip_key, 0)
        total_tips = get_tip_count(self.has_translator)
        
        # Get the tip at current index
        tip_text, category_emoji = get_tip_by_index(tip_index, self.has_translator)
        
        # Update tip display
        self.rodent_tip_number.setText(f"Tip #{tip_index + 1} of {total_tips}")
        
        if self.has_translator:
            self.rodent_tip_text.setText(f"{category_emoji} {tip_text}")
            self.rodent_tip_text.setStyleSheet("color: #c5e1c5; font-size: 11px;")
        else:
            # Show rodent language with a hint
            self.rodent_tip_text.setText(f"🐭 {tip_text}\n\n<i style='color:#888;'>💡 Collect White Mouse Archimedes to understand rodent language!</i>")
            self.rodent_tip_text.setStyleSheet("color: #d4c4a4; font-size: 11px;")
        
        # Check if already acknowledged today
        today_str = datetime.now().strftime("%Y-%m-%d")
        ack_key = "rodent_tip_acknowledged_date_translated" if self.has_translator else "rodent_tip_acknowledged_date_squeaks"
        last_acknowledged = self.blocker.stats.get(ack_key, "")
        
        if last_acknowledged == today_str:
            # Already acknowledged today
            self.rodent_acknowledge_btn.setText("✓ Done")
            self.rodent_acknowledge_btn.setEnabled(False)
        else:
            # Can acknowledge
            self.rodent_acknowledge_btn.setText("📖 +1🪙")
            self.rodent_acknowledge_btn.setEnabled(True)
            
        # Update button styling based on translator status
        if self.has_translator:
            self.rodent_acknowledge_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #66bb6a, stop:1 #4caf50);
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 4px;
                    border: 1px solid #388e3c;
                    padding: 6px 8px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #81c784, stop:1 #66bb6a);
                }
                QPushButton:disabled {
                    background: #444;
                    color: #777;
                    border: 1px solid #333;
                }
            """)
        else:
            self.rodent_acknowledge_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #8b7355, stop:1 #6b5335);
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 4px;
                    border: 1px solid #5b4325;
                    padding: 6px 8px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #a68365, stop:1 #8b7355);
                }
                QPushButton:disabled {
                    background: #444;
                    color: #777;
                    border: 1px solid #333;
                }
            """)

    def _acknowledge_rodent_tip(self) -> None:
        """Handle acknowledging the rodent tip - award coin and advance to next tip."""
        from datetime import datetime
        from weight_control_tips import get_tip_count
        
        try:
            # Determine if user has translator
            from weight_control_tips import has_telepathic_translator
            has_translator = has_telepathic_translator(self.blocker.adhd_buster)
            
            # Get keys based on translator status
            tip_key = "rodent_tip_index_translated" if has_translator else "rodent_tip_index_squeaks"
            ack_key = "rodent_tip_acknowledged_date_translated" if has_translator else "rodent_tip_acknowledged_date_squeaks"
            
            # Get current index and total
            current_index = self.blocker.stats.get(tip_key, 0)
            total_tips = get_tip_count(has_translator)
            
            # Advance to next tip (with wraparound)
            next_index = (current_index + 1) % total_tips
            self.blocker.stats[tip_key] = next_index
            
            # Record acknowledgment date
            today_str = datetime.now().strftime("%Y-%m-%d")
            self.blocker.stats[ack_key] = today_str
            
            # Award coin
            adhd_buster = self.blocker.adhd_buster
            adhd_buster["coins"] = adhd_buster.get("coins", 0) + 1
            
            # Save data
            self.blocker.save_config()
            
            # Update button to show collected
            self.rodent_acknowledge_btn.setText("✓ Done")
            self.rodent_acknowledge_btn.setEnabled(False)
            
        except Exception as e:
            print(f"[Weight Tab] Error acknowledging rodent tip: {e}")

    def _show_weekly_insights(self) -> None:
        """Show weekly insights in a dialog."""
        if not get_weekly_insights:
            show_info(self, "Weekly Insights", "Insights not available")
            return
        
        # Calculate actual streak from get_weight_stats
        actual_streak = 0
        if get_weight_stats and self.blocker.weight_entries:
            stats = get_weight_stats(self.blocker.weight_entries, self.blocker.weight_unit)
            actual_streak = stats.get("streak_days", 0)
        
        insights = get_weekly_insights(
            self.blocker.weight_entries,
            self.blocker.weight_milestones,
            actual_streak,
            self.blocker.weight_goal
        )
        
        if not insights or not insights.get("has_data"):
            msg = insights.get("message", "Not enough data for insights") if insights else "Not enough data for insights"
            show_info(self, "Weekly Insights", msg)
            return
        
        # Build insights message
        unit = self.blocker.weight_unit
        msg_parts = []
        
        msg_parts.append("<h3>📊 Weekly Summary</h3>")
        
        if insights.get("entries_count") is not None:
            msg_parts.append(f"<b>Entries logged:</b> {insights['entries_count']}")
        
        if insights.get("average") is not None:
            avg = insights["average"]
            if unit == "lbs":
                avg_display = avg * 2.20462
                suffix = "lbs"
            else:
                avg_display = avg
                suffix = "kg"
            msg_parts.append(f"<b>Average weight:</b> {avg_display:.1f} {suffix}")
        
        if insights.get("min") is not None and insights.get("max") is not None:
            min_w = insights["min"]
            max_w = insights["max"]
            if unit == "lbs":
                min_display = min_w * 2.20462
                max_display = max_w * 2.20462
                suffix = "lbs"
            else:
                min_display = min_w
                max_display = max_w
                suffix = "kg"
            msg_parts.append(f"<b>Range:</b> {min_display:.1f} - {max_display:.1f} {suffix}")
        
        if insights.get("change_from_last_week") is not None:
            change = insights["change_from_last_week"]
            if unit == "lbs":
                change_display = change * 2.20462
                suffix = "lbs"
            else:
                change_display = change
                suffix = "kg"
            color = "#00ff88" if change < 0 else "#ff6464" if change > 0 else "#888888"
            sign = "+" if change > 0 else ""
            msg_parts.append(f"<b>vs Last Week:</b> <span style='color:{color}'>{sign}{change_display:.2f} {suffix}</span>")
        
        if insights.get("streak") is not None and insights["streak"] > 0:
            msg_parts.append(f"<b>Streak:</b> 🔥 {insights['streak']} days")
        
        # Show insights list
        if insights.get("insights"):
            msg_parts.append("<br><b>Highlights:</b>")
            for insight_text in insights["insights"][:5]:  # Limit to 5
                msg_parts.append(f"• {insight_text}")
        
        dialog = QtWidgets.QMessageBox(self)
        dialog.setWindowTitle("📊 Weekly Insights")
        dialog.setTextFormat(QtCore.Qt.TextFormat.RichText)
        dialog.setText("<br>".join(msg_parts))
        dialog.exec()


class ActivityTab(QtWidgets.QWidget):
    """Physical activity tracking tab with gamification rewards."""
    
    def __init__(self, blocker: 'BlockerCore', parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self._reminder_timer = None
        self._build_ui()
        self._refresh_display()
        self._setup_reminder()
        self.destroyed.connect(self._cleanup_timer)
    
    def _cleanup_timer(self) -> None:
        """Stop the reminder timer when the widget is destroyed."""
        if self._reminder_timer is not None:
            self._reminder_timer.stop()
            self._reminder_timer = None
    
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QtWidgets.QLabel("🏃 Activity Tracker")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)
        
        # Main content split
        content_layout = QtWidgets.QHBoxLayout()
        
        # Left: Log activity form
        left_panel = QtWidgets.QGroupBox("Log Activity")
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        
        # Date input
        date_layout = QtWidgets.QHBoxLayout()
        date_layout.addWidget(QtWidgets.QLabel("Date:"))
        self.date_edit = QtWidgets.QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QtCore.QDate.currentDate())
        self.date_edit.setMaximumDate(QtCore.QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        left_layout.addLayout(date_layout)
        
        # Activity type
        type_layout = QtWidgets.QHBoxLayout()
        type_layout.addWidget(QtWidgets.QLabel("Activity:"))
        self.activity_combo = NoScrollComboBox()
        for activity_id, name, emoji, _ in ACTIVITY_TYPES:
            self.activity_combo.addItem(f"{emoji} {name}", activity_id)
        self.activity_combo.setCurrentIndex(0)  # Walking
        type_layout.addWidget(self.activity_combo)
        left_layout.addLayout(type_layout)
        
        # Duration
        duration_layout = QtWidgets.QHBoxLayout()
        duration_layout.addWidget(QtWidgets.QLabel("Duration:"))
        self.duration_spin = QtWidgets.QSpinBox()
        self.duration_spin.setRange(1, 480)  # 1 min to 8 hours
        self.duration_spin.setValue(30)
        self.duration_spin.setSuffix(" min")
        duration_layout.addWidget(self.duration_spin)
        duration_layout.addStretch()
        left_layout.addLayout(duration_layout)
        
        # Intensity
        intensity_layout = QtWidgets.QHBoxLayout()
        intensity_layout.addWidget(QtWidgets.QLabel("Intensity:"))
        self.intensity_combo = NoScrollComboBox()
        for intensity_id, name, _ in INTENSITY_LEVELS:
            self.intensity_combo.addItem(name, intensity_id)
        self.intensity_combo.setCurrentIndex(1)  # Moderate
        intensity_layout.addWidget(self.intensity_combo)
        intensity_layout.addStretch()
        left_layout.addLayout(intensity_layout)
        
        # Note
        note_layout = QtWidgets.QHBoxLayout()
        note_layout.addWidget(QtWidgets.QLabel("Note:"))
        self.note_input = QtWidgets.QLineEdit()
        self.note_input.setPlaceholderText("Optional note...")
        self.note_input.setMaxLength(100)
        note_layout.addWidget(self.note_input)
        left_layout.addLayout(note_layout)
        
        # Log button
        self.log_btn = QtWidgets.QPushButton("🏆 Log Activity")
        self.log_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #66bb6a; }
        """)
        self.log_btn.clicked.connect(self._log_activity)
        left_layout.addWidget(self.log_btn)
        
        # Quick presets
        presets_label = QtWidgets.QLabel("Quick Presets:")
        presets_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(presets_label)
        
        presets_layout = QtWidgets.QGridLayout()
        presets = [
            ("🚶 10min Walk", "walking", 10, "light"),
            ("🚶 30min Walk", "walking", 30, "moderate"),
            ("🏃 20min Jog", "jogging", 20, "moderate"),
            ("🏋️ 45min Gym", "strength", 45, "vigorous"),
            ("🧘 30min Yoga", "yoga", 30, "light"),
            ("🔥 30min HIIT", "hiit", 30, "intense"),
        ]
        for i, (label, activity, duration, intensity) in enumerate(presets):
            btn = QtWidgets.QPushButton(label)
            btn.setStyleSheet("padding: 5px;")
            btn.clicked.connect(lambda _, a=activity, d=duration, i=intensity: self._apply_preset(a, d, i))
            presets_layout.addWidget(btn, i // 2, i % 2)
        left_layout.addLayout(presets_layout)
        
        left_layout.addStretch()
        content_layout.addWidget(left_panel)
        
        # Right: Stats and history
        right_panel = QtWidgets.QGroupBox("Stats & History")
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        
        # Stats display
        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("font-size: 11px;")
        right_layout.addWidget(self.stats_label)
        
        # History table
        self.entries_table = QtWidgets.QTableWidget()
        self.entries_table.setColumnCount(5)
        self.entries_table.setHorizontalHeaderLabels(["Date", "Activity", "Duration", "Intensity", ""])
        self.entries_table.horizontalHeader().setStretchLastSection(True)
        self.entries_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.entries_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.entries_table)
        
        content_layout.addWidget(right_panel)
        layout.addLayout(content_layout)
        
        # Reminder section at bottom
        reminder_layout = QtWidgets.QHBoxLayout()
        self.reminder_checkbox = QtWidgets.QCheckBox("Daily reminder at:")
        self.reminder_checkbox.setChecked(self.blocker.activity_reminder_enabled)
        self.reminder_checkbox.stateChanged.connect(self._update_reminder_setting)
        reminder_layout.addWidget(self.reminder_checkbox)
        
        self.reminder_time = QtWidgets.QTimeEdit()
        self.reminder_time.setDisplayFormat("HH:mm")
        try:
            h, m = self.blocker.activity_reminder_time.split(":")
            self.reminder_time.setTime(QtCore.QTime(int(h), int(m)))
        except (ValueError, AttributeError):
            self.reminder_time.setTime(QtCore.QTime(18, 0))
        self.reminder_time.timeChanged.connect(self._update_reminder_setting)
        reminder_layout.addWidget(self.reminder_time)
        reminder_layout.addStretch()
        layout.addLayout(reminder_layout)
        
        # Entity XP Perk Section - shows entities that boost XP
        self.activity_entity_section = CollapsibleSection("⚡ XP Boosters", "activity_entity_section", parent=self)
        self.activity_entity_section.setVisible(False)
        layout.addWidget(self.activity_entity_section)
        
        # Update entity perk display
        self._update_activity_entity_perk_display()
        
        # Rewards info section
        rewards_group = QtWidgets.QGroupBox("🎁 Rewards Info")
        rewards_layout = QtWidgets.QVBoxLayout(rewards_group)
        rewards_info = QtWidgets.QLabel(
            "<b>How it works:</b> Log activity (10+ min) to earn 1 item. Rarity based on effective minutes.<br>"
            "<i>Effective min = duration × activity multiplier × intensity multiplier</i><br>"
            "<i>Example: 30min jog (2.0×) at moderate (1.0×) = 60 effective min</i><br>"
            "<table style='font-size:10px; color:#888888; margin-top:5px;'>"
            "<tr><th>Eff. Min</th><th>Common</th><th>Uncommon</th><th>Rare</th><th>Epic</th><th>Legendary</th></tr>"
            "<tr><td>&lt;8</td><td colspan='5' style='text-align:center;'>No reward</td></tr>"
            "<tr><td>8+</td><td>75%</td><td>20%</td><td>5%</td><td>-</td><td>-</td></tr>"
            "<tr><td>20+</td><td>25%</td><td>50%</td><td>20%</td><td>5%</td><td>-</td></tr>"
            "<tr><td>40+</td><td>5%</td><td>20%</td><td>50%</td><td>20%</td><td>5%</td></tr>"
            "<tr><td>70+</td><td>-</td><td>5%</td><td>20%</td><td>50%</td><td>25%</td></tr>"
            "<tr><td>100+</td><td>-</td><td>-</td><td>5%</td><td>20%</td><td>75%</td></tr>"
            "<tr><td>120+</td><td>-</td><td>-</td><td>-</td><td>-</td><td>100%</td></tr>"
            "</table>"
            "<br><b>Streaks:</b> 3d=Uncommon, 7d=Rare, 14d=Epic, 30d=Legendary"
        )
        rewards_info.setWordWrap(True)
        rewards_info.setStyleSheet("color: #888888; font-size: 10px;")
        rewards_layout.addWidget(rewards_info)
        layout.addWidget(rewards_group)
    
    def _apply_preset(self, activity: str, duration: int, intensity: str) -> None:
        """Apply a quick preset to the form."""
        # Find activity index
        for i in range(self.activity_combo.count()):
            if self.activity_combo.itemData(i) == activity:
                self.activity_combo.setCurrentIndex(i)
                break
        
        self.duration_spin.setValue(duration)
        
        # Find intensity index
        for i in range(self.intensity_combo.count()):
            if self.intensity_combo.itemData(i) == intensity:
                self.intensity_combo.setCurrentIndex(i)
                break
    
    def _log_activity(self) -> None:
        """Log a new activity entry."""
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        duration = self.duration_spin.value()
        activity_id = self.activity_combo.currentData()
        intensity_id = self.intensity_combo.currentData()
        note = self.note_input.text().strip()
        
        # Allow logging any activity, but warn if below reward threshold
        if duration < ACTIVITY_MIN_DURATION:
            reply = show_question(
                self, "Short Activity",
                f"Activities under {ACTIVITY_MIN_DURATION} minutes don't earn rewards.\n"
                f"Log anyway for tracking?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
        
        # Get entries WITHOUT current date for reward calculation
        entries_for_reward = [e for e in self.blocker.activity_entries if e.get("date") != date_str]
        
        # Check for rewards
        rewards = None
        effective_mins = 0
        rarity = None
        if GAMIFICATION_AVAILABLE and check_all_activity_rewards and is_gamification_enabled(self.blocker.adhd_buster):
            story_id = self.blocker.adhd_buster.get("active_story", "warrior")
            rewards = check_all_activity_rewards(
                entries_for_reward,
                duration,
                activity_id,
                intensity_id,
                date_str,
                self.blocker.activity_milestones,
                story_id
            )
            
            # Get effective minutes and rarity for lottery animation
            if rewards and rewards.get("reward"):
                effective_mins = rewards.get("effective_minutes", 0)
                rarity = rewards.get("rarity")
        
        # Show lottery animation if we got a reward
        if rarity and effective_mins >= 8:
            from lottery_animation import MergeTwoStageLotteryDialog
            
            # Use merge lottery with 100% success (activity rewards are guaranteed)
            lottery = MergeTwoStageLotteryDialog(
                success_roll=0.0,  # Guaranteed success
                success_threshold=1.0,  # 100% success rate
                tier_upgrade_enabled=False,
                base_rarity=rarity,
                parent=self
            )
            lottery.exec()
            # Lottery animation shows the rarity but doesn't change the reward
        
        # Create entry
        new_entry = {
            "date": date_str,
            "duration": duration,
            "activity_type": activity_id,
            "intensity": intensity_id,
        }
        if note:
            new_entry["note"] = note
        
        # Check for existing entry on same date
        # User feedback indicates they prefer separate entries (e.g., multiple walks)
        # rather than merging them. So we simply append the new entry.
        self.blocker.activity_entries.append(new_entry)
        self.blocker.activity_entries.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        self.blocker.save_config()
        
        # Award coins for activity (5-20 coins based on effective minutes)
        coins_earned = 0
        if GAMIFICATION_AVAILABLE and is_gamification_enabled(self.blocker.adhd_buster):
            if rewards and rewards.get("effective_minutes"):
                effective_mins = rewards["effective_minutes"]
                # Scale: 30 eff min = 5 coins, 60+ = 10 coins, 120+ = 20 coins
                if effective_mins >= 120:
                    coins_earned = 20
                elif effective_mins >= 60:
                    coins_earned = 10
                elif effective_mins >= 30:
                    coins_earned = 5
                
                # Coins will be awarded in _process_rewards via game_state
        
        # Process rewards
        if rewards and GAMIFICATION_AVAILABLE:
            self._process_rewards(rewards, coins_earned=coins_earned)
        
        # Update main timeline widget if parent window has it
        if self.parent() and hasattr(self.parent(), 'timeline_widget'):
            try:
                self.parent().timeline_widget.update_data()
            except Exception:
                pass
        
        # Reset form
        self.note_input.clear()
        self._refresh_display()
    
    def _process_rewards(self, rewards: dict, coins_earned: int = 0) -> None:
        """Process and show activity rewards."""
        items_earned = []
        new_milestone_ids = []
        
        # Base activity reward - items added via game_state below
        if rewards.get("reward"):
            item = rewards["reward"]
            items_earned.append(("Activity", item))
        
        # Streak reward
        if rewards.get("streak_reward"):
            streak_data = rewards["streak_reward"]
            item = streak_data["item"]
            items_earned.append((f"🔥 {streak_data['streak_days']}-Day Streak", item))
            new_milestone_ids.append(streak_data["milestone_id"])
        
        # Milestone rewards
        for milestone in rewards.get("new_milestones", []):
            item = milestone["item"]
            items_earned.append((f"🏆 {milestone['name']}", item))
            new_milestone_ids.append(milestone["milestone_id"])
        
        # Save new milestones
        if new_milestone_ids:
            self.blocker.activity_milestones.extend(new_milestone_ids)
        
        # Generate diary entry (once per day)
        diary_entry = None
        if items_earned and GAMIFICATION_AVAILABLE and generate_diary_entry and calculate_character_power:
            today = datetime.now().strftime("%Y-%m-%d")
            diary = self.blocker.adhd_buster.get("diary", [])
            today_entries = [e for e in diary if e.get("date") == today]
            
            if not today_entries:
                power = calculate_character_power(self.blocker.adhd_buster)
                equipped = self.blocker.adhd_buster.get("equipped", {})
                active_story = self.blocker.adhd_buster.get("active_story", "warrior")
                diary_entry = generate_diary_entry(power, session_minutes=0, equipped_items=equipped,
                                                   story_id=active_story)
                if "diary" not in self.blocker.adhd_buster:
                    self.blocker.adhd_buster["diary"] = []
                self.blocker.adhd_buster["diary"].append(diary_entry)
                if len(self.blocker.adhd_buster["diary"]) > 100:
                    self.blocker.adhd_buster["diary"] = self.blocker.adhd_buster["diary"][-100:]
        
        if items_earned or coins_earned > 0:
            # Extract just the items for the batch award
            just_items = [item for _, item in items_earned]
            
            # Use GameState manager for reactive updates
            main_window = self.window()
            game_state = getattr(main_window, 'game_state', None)
            if not game_state:
                logger.error("GameStateManager not available - cannot award activity rewards")
                return
            
            # Use batch award - handles inventory, auto-equip, coins, save, and signals
            game_state.award_items_batch(just_items, coins=coins_earned, auto_equip=True, source="activity_tracking")
            
            # Sync hero data
            if GAMIFICATION_AVAILABLE and sync_hero_data:
                sync_hero_data(self.blocker.adhd_buster)
                self.blocker.save_config()
            
            # Build reward message with rarity colors
            rarity_colors = {
                "Common": "#9e9e9e",
                "Uncommon": "#4caf50", 
                "Rare": "#2196f3",
                "Epic": "#9c27b0",
                "Legendary": "#ff9800"
            }
            msg_parts = []
            for source, item in items_earned:
                rarity = item.get("rarity", "Common")
                name = item.get("name", "Unknown Item")
                color = rarity_colors.get(rarity, "#9e9e9e")
                msg_parts.append(f"<b>{source}:</b> <span style='color:{color}; font-weight:bold;'>[{rarity}]</span> {name}")
            
            # Add effective minutes info
            if rewards.get("effective_minutes"):
                msg_parts.append(f"<br><i>Effective minutes: {rewards['effective_minutes']:.0f}</i>")
            
            # Add streak info
            if rewards.get("current_streak", 0) > 0:
                msg_parts.append(f"<i>Streak: {rewards['current_streak']} days 🔥</i>")
            
            # Add coin earnings
            if coins_earned > 0:
                msg_parts.append(f"<br><b style='color: #f59e0b;'>💰 +{coins_earned} Coins earned!</b>")
            
            msg = "<br>".join(msg_parts)
            show_info(
                self, "🏆 Activity Rewards!",
                f"<h3>Great workout!</h3>{msg}"
            )
            
            # Update coin display
            main_window = self.window()
            if hasattr(main_window, '_update_coin_display'):
                main_window._update_coin_display()
            
            # Show diary entry reveal
            if diary_entry:
                DiaryEntryRevealDialog(self.blocker, diary_entry, session_minutes=0, parent=self.window()).exec()
            
            # Refresh ADHD Buster tab
            main_window = self.window()
            if hasattr(main_window, 'refresh_adhd_tab'):
                main_window.refresh_adhd_tab()
        elif rewards.get("messages"):
            show_info(
                self, "Activity Logged",
                "\n".join(rewards["messages"])
            )
    
    def _delete_entry(self, entry_index: int) -> None:
        """Delete an activity entry by index."""
        if entry_index < 0 or entry_index >= len(self.blocker.activity_entries):
            return
        entry = self.blocker.activity_entries[entry_index]
        date_str = entry.get("date", "")
        activity_type = entry.get("activity_type", "")
        reply = show_question(
            self, "Delete Entry",
            f"Delete the {activity_type} entry for {date_str}?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            del self.blocker.activity_entries[entry_index]
            self.blocker.save_config()
            self._refresh_display()
    
    def _refresh_display(self) -> None:
        """Refresh all display elements."""
        self.date_edit.setMaximumDate(QtCore.QDate.currentDate())
        entries = self.blocker.activity_entries
        
        # Update stats
        if get_activity_stats:
            stats = get_activity_stats(entries)
            
            # Get favorite activity name
            fav_name = "None"
            if stats.get("favorite_activity"):
                for aid, name, emoji, _ in ACTIVITY_TYPES:
                    if aid == stats["favorite_activity"]:
                        fav_name = f"{emoji} {name}"
                        break
            
            # Calculate Today's Breakdown
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_totals = {}
            for e in entries:
                if e.get("date") == today_str:
                    aid = e.get("activity_type")
                    today_totals[aid] = today_totals.get(aid, 0) + e.get("duration", 0)
            
            today_html = ""
            if today_totals:
                today_html = "<br><b>Today's Totals:</b><br>"
                sorted_today = sorted(today_totals.items(), key=lambda x: x[1], reverse=True)
                for aid, mins in sorted_today:
                    aname = aid.title()
                    # Try to match with emoji
                    for taid, tname, temoji, _ in ACTIVITY_TYPES:
                        if taid == aid:
                            aname = f"{temoji} {tname}"
                            break
                    today_html += f"{aname}: {mins} min<br>"
            
            stats_html = f"""
<b>📊 Your Activity Stats</b><br><br>
<b>Total Time:</b> {format_activity_duration(stats['total_minutes']) if format_activity_duration else f"{stats['total_minutes']} min"}<br>
<b>Sessions:</b> {stats['total_sessions']}<br>
<b>This Week:</b> {format_activity_duration(stats['this_week_minutes']) if format_activity_duration else f"{stats['this_week_minutes']} min"}<br>
<b>This Month:</b> {format_activity_duration(stats['this_month_minutes']) if format_activity_duration else f"{stats['this_month_minutes']} min"}<br>
<b>Avg Duration:</b> {stats['avg_duration']:.0f} min<br>
<b>Favorite:</b> {fav_name}<br>
<b>Streak:</b> 🔥 {stats['current_streak']} days<br>
{today_html}
"""
            self.stats_label.setText(stats_html)
        
        # Update history table - create sorted view with original indices
        entries_with_indices = list(enumerate(entries))
        sorted_entries = sorted(entries_with_indices, key=lambda x: x[1].get("date", ""), reverse=True)[:50]
        self.entries_table.setRowCount(len(sorted_entries))
        
        for i, (orig_idx, entry) in enumerate(sorted_entries):
            # Date
            self.entries_table.setItem(i, 0, QtWidgets.QTableWidgetItem(entry.get("date", "")))
            
            # Activity type
            activity_name = entry.get("activity_type", "other")
            for aid, name, emoji, _ in ACTIVITY_TYPES:
                if aid == activity_name:
                    activity_name = f"{emoji} {name}"
                    break
            self.entries_table.setItem(i, 1, QtWidgets.QTableWidgetItem(activity_name))
            
            # Duration
            duration = entry.get("duration", 0)
            self.entries_table.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{duration} min"))
            
            # Intensity
            intensity_name = entry.get("intensity", "moderate")
            for iid, name, _ in INTENSITY_LEVELS:
                if iid == intensity_name:
                    intensity_name = name
                    break
            self.entries_table.setItem(i, 3, QtWidgets.QTableWidgetItem(intensity_name))
            
            # Delete button - pass original index for correct deletion
            del_btn = QtWidgets.QPushButton("🗑")
            del_btn.setMaximumWidth(30)
            del_btn.clicked.connect(
                lambda _, idx=orig_idx: self._delete_entry(idx)
            )
            self.entries_table.setCellWidget(i, 4, del_btn)
        
        self.entries_table.resizeColumnsToContents()
    
    def _setup_reminder(self) -> None:
        """Setup daily reminder timer."""
        if self._reminder_timer:
            self._reminder_timer.stop()
        
        if not self.blocker.activity_reminder_enabled:
            return
        
        self._reminder_timer = QtCore.QTimer(self)
        self._reminder_timer.timeout.connect(self._check_reminder)
        self._reminder_timer.start(60000)  # Check every minute
    
    def _check_reminder(self) -> None:
        """Check if it's time to show reminder."""
        if not self.blocker.activity_reminder_enabled:
            return
        
        today = datetime.now().strftime("%Y-%m-%d")
        if self.blocker.activity_last_reminder_date == today:
            return
        
        current_time = QtCore.QTime.currentTime()
        try:
            h, m = self.blocker.activity_reminder_time.split(":")
            reminder_time = QtCore.QTime(int(h), int(m))
        except (ValueError, AttributeError):
            return
        
        if current_time >= reminder_time:
            # Check if already logged today
            has_today = any(e.get("date") == today for e in self.blocker.activity_entries)
            if not has_today:
                self.blocker.activity_last_reminder_date = today
                self.blocker.save_config()
                
                show_info(
                    self, "🏃 Activity Reminder",
                    "Time to get moving!\n\n"
                    "Even a 10-minute walk earns rewards for your hero.\n"
                    "Log your activity to keep your streak going!"
                )
    
    def _update_reminder_setting(self) -> None:
        """Update reminder settings."""
        self.blocker.activity_reminder_enabled = self.reminder_checkbox.isChecked()
        self.blocker.activity_reminder_time = self.reminder_time.time().toString("HH:mm")
        self.blocker.save_config()
        self._setup_reminder()

    def _update_activity_entity_perk_display(self) -> None:
        """Update the entity perk display using mini-cards for XP boosters."""
        try:
            adhd_data = getattr(self.blocker, 'adhd_buster', {})
            if not adhd_data:
                self.activity_entity_section.setVisible(False)
                return
            
            from gamification import get_entity_xp_perk_contributors
            xp_perks = get_entity_xp_perk_contributors(adhd_data)
            total_xp_bonus = xp_perks.get("total_xp_bonus", 0)
            contributors = xp_perks.get("contributors", [])
            
            # Hide if no contributors
            if total_xp_bonus <= 0 or not contributors:
                self.activity_entity_section.setVisible(False)
                return
            
            # Show section with appropriate title
            self.activity_entity_section.setVisible(True)
            self.activity_entity_section.set_title(f"⚡ XP Boosters (+{total_xp_bonus}% XP)")
            
            # Clear previous content
            self.activity_entity_section.clear_content()
            
            # Try to import entity icon resolver
            try:
                from entitidex_tab import _resolve_entity_svg_path
                from entitidex.entity_pools import get_entity_by_id as get_entity
                from PySide6.QtSvg import QSvgRenderer
                has_svg_support = True
            except ImportError:
                has_svg_support = False
            
            # Create a horizontal flow layout for entity cards
            patrons_container = QtWidgets.QWidget()
            patrons_layout = QtWidgets.QHBoxLayout(patrons_container)
            patrons_layout.setContentsMargins(5, 5, 5, 5)
            patrons_layout.setSpacing(8)
            
            for entity_data in contributors:
                # Create a mini card for each entity
                card = QtWidgets.QFrame()
                is_exceptional = entity_data.get("is_exceptional", False)
                
                # Style cards - exceptional gets slightly lighter border
                if is_exceptional:
                    card.setStyleSheet("""
                        QFrame {
                            background-color: #2a2a2a;
                            border: 1px solid #555;
                            border-radius: 6px;
                            padding: 4px;
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
                            border-radius: 6px;
                            padding: 4px;
                        }
                        QFrame:hover {
                            border-color: #4caf50;
                            background-color: #333;
                        }
                    """)
                
                card_layout = QtWidgets.QVBoxLayout(card)
                card_layout.setContentsMargins(8, 6, 8, 6)
                card_layout.setSpacing(4)
                
                # Try to load entity SVG icon
                entity_id = entity_data.get("entity_id", "")
                icon_loaded = False
                
                if has_svg_support and entity_id:
                    try:
                        entity_obj = get_entity(entity_id)
                        if entity_obj:
                            svg_path = _resolve_entity_svg_path(entity_obj, is_exceptional)
                            if svg_path:
                                renderer = QSvgRenderer(svg_path)
                                if renderer.isValid():
                                    # Create pixmap from SVG (40x40 size for mini cards)
                                    icon_size = 40
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
                        pass  # Fall back to text display
                
                # Entity name with exceptional styling
                name = entity_data.get("name", "Unknown")
                # Truncate long names
                if len(name) > 18:
                    display_name = name[:15] + "..."
                else:
                    display_name = name
                
                if is_exceptional:
                    name_style = "color: #ffd700; font-weight: bold; font-size: 10px;"
                    prefix = "⭐ " if not icon_loaded else ""
                else:
                    name_style = "color: #ccc; font-size: 10px;"
                    prefix = ""
                
                name_lbl = QtWidgets.QLabel(f"{prefix}{display_name}")
                name_lbl.setStyleSheet(name_style)
                name_lbl.setAlignment(QtCore.Qt.AlignCenter)
                name_lbl.setToolTip(entity_data.get("description", name))
                name_lbl.setWordWrap(True)
                card_layout.addWidget(name_lbl)
                
                # Bonus value
                bonus_val = entity_data.get("value", 0)
                bonus_lbl = QtWidgets.QLabel(f"<b>+{bonus_val}%</b> ⚡")
                bonus_lbl.setStyleSheet("color: #4caf50; font-size: 12px;")
                bonus_lbl.setAlignment(QtCore.Qt.AlignCenter)
                card_layout.addWidget(bonus_lbl)
                
                patrons_layout.addWidget(card)
            
            patrons_layout.addStretch()
            self.activity_entity_section.add_widget(patrons_container)
            
            # Add a tip
            tip_lbl = QtWidgets.QLabel("💡 Collect more entities in Entitidex to boost XP gains!")
            tip_lbl.setStyleSheet("color: #888; font-style: italic; font-size: 10px; padding-top: 4px;")
            self.activity_entity_section.add_widget(tip_lbl)
            
        except Exception as e:
            print(f"[Activity Tab] Error updating entity perk display: {e}")
            self.activity_entity_section.setVisible(False)


class SleepTab(QtWidgets.QWidget):
    """Sleep tracking tab with gamification rewards based on scientific recommendations."""
    
    def __init__(self, blocker: 'BlockerCore', parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self._reminder_timer = None
        self._build_ui()
        self._refresh_display()
        self._setup_reminder()
        self.destroyed.connect(self._cleanup_timer)
    
    def _cleanup_timer(self) -> None:
        """Stop the reminder timer when the widget is destroyed."""
        if self._reminder_timer is not None:
            self._reminder_timer.stop()
            self._reminder_timer = None
    
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QtWidgets.QLabel("😴 Sleep Tracker")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)
        
        # Main content split
        content_layout = QtWidgets.QHBoxLayout()
        
        # Left: Log sleep form
        left_panel = QtWidgets.QGroupBox("Log Sleep")
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        
        # Date input (sleep date = night of)
        date_layout = QtWidgets.QHBoxLayout()
        date_layout.addWidget(QtWidgets.QLabel("Night of:"))
        self.date_edit = QtWidgets.QDateEdit()
        self.date_edit.setCalendarPopup(True)
        # Default to yesterday (logging last night's sleep)
        yesterday = QtCore.QDate.currentDate().addDays(-1)
        self.date_edit.setDate(yesterday)
        self.date_edit.setMaximumDate(QtCore.QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        left_layout.addLayout(date_layout)
        
        # Bedtime
        bed_layout = QtWidgets.QHBoxLayout()
        bed_layout.addWidget(QtWidgets.QLabel("Bedtime:"))
        self.bedtime_edit = QtWidgets.QTimeEdit()
        self.bedtime_edit.setDisplayFormat("HH:mm")
        self.bedtime_edit.setWrapping(True)  # Allow wrapping past midnight
        self.bedtime_edit.setTime(QtCore.QTime(23, 0))
        self.bedtime_edit.timeChanged.connect(self._update_sleep_duration)
        bed_layout.addWidget(self.bedtime_edit)
        bed_hint = QtWidgets.QLabel("(wraps past midnight)")
        bed_hint.setStyleSheet("color: #888; font-size: 11px;")
        bed_layout.addWidget(bed_hint)
        bed_layout.addStretch()
        left_layout.addLayout(bed_layout)
        
        # Wake time
        wake_layout = QtWidgets.QHBoxLayout()
        wake_layout.addWidget(QtWidgets.QLabel("Wake time:"))
        self.wake_edit = QtWidgets.QTimeEdit()
        self.wake_edit.setDisplayFormat("HH:mm")
        self.wake_edit.setWrapping(True)  # Allow wrapping past midnight
        self.wake_edit.setTime(QtCore.QTime(7, 0))
        self.wake_edit.timeChanged.connect(self._update_sleep_duration)
        wake_layout.addWidget(self.wake_edit)
        wake_layout.addStretch()
        left_layout.addLayout(wake_layout)
        
        # Calculated sleep duration
        self.duration_label = QtWidgets.QLabel("💤 Sleep duration: 8h 0m")
        self.duration_label.setStyleSheet("font-weight: bold; color: #4caf50;")
        left_layout.addWidget(self.duration_label)
        
        # Quality rating
        quality_layout = QtWidgets.QHBoxLayout()
        quality_layout.addWidget(QtWidgets.QLabel("Sleep quality:"))
        self.quality_combo = NoScrollComboBox()
        for quality_id, name, emoji, _ in SLEEP_QUALITY_FACTORS:
            self.quality_combo.addItem(f"{emoji} {name}", quality_id)
        self.quality_combo.setCurrentIndex(1)  # Good
        quality_layout.addWidget(self.quality_combo)
        left_layout.addLayout(quality_layout)
        
        # Disruptions (checkboxes)
        disruptions_group = QtWidgets.QGroupBox("Disruptions (optional)")
        disruptions_layout = QtWidgets.QGridLayout(disruptions_group)
        self.disruption_checks = {}
        for i, (tag_id, name, emoji, _) in enumerate(SLEEP_DISRUPTION_TAGS):
            if tag_id == "none":
                continue  # Skip "none" as it's the default
            cb = QtWidgets.QCheckBox(f"{emoji} {name}")
            cb.setProperty("tag_id", tag_id)
            self.disruption_checks[tag_id] = cb
            disruptions_layout.addWidget(cb, i // 2, i % 2)
        left_layout.addWidget(disruptions_group)
        
        # Note
        note_layout = QtWidgets.QHBoxLayout()
        note_layout.addWidget(QtWidgets.QLabel("Note:"))
        self.note_input = QtWidgets.QLineEdit()
        self.note_input.setPlaceholderText("Optional note (dreams, how you feel...)")
        self.note_input.setMaxLength(150)
        note_layout.addWidget(self.note_input)
        left_layout.addLayout(note_layout)
        
        # Screen-Off Bonus (Nighty-Night Gift)
        screenoff_group = QtWidgets.QGroupBox("🌙 Nighty-Night Bonus")
        screenoff_main_layout = QtWidgets.QVBoxLayout(screenoff_group)
        
        # Go to Sleep NOW button - immediate reward
        sleep_now_layout = QtWidgets.QHBoxLayout()
        self.sleep_now_btn = QtWidgets.QPushButton("🛏️ Go to Sleep NOW!")
        self.sleep_now_btn.setToolTip(
            "Click when going to sleep right now to get an immediate reward!\n"
            "Rewards available 22:00 - 01:00."
        )
        self.sleep_now_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565c0;
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #1976d2; }
            QPushButton:disabled { background-color: #455a64; color: #888; }
        """)
        self.sleep_now_btn.clicked.connect(self._go_to_sleep_now)
        sleep_now_layout.addWidget(self.sleep_now_btn)
        self.sleep_now_info = QtWidgets.QLabel()
        self.sleep_now_info.setStyleSheet("color: #888; font-size: 11px;")
        self._update_sleep_now_preview()
        sleep_now_layout.addWidget(self.sleep_now_info)
        sleep_now_layout.addStretch()
        screenoff_main_layout.addLayout(sleep_now_layout)
        
        # Entity Perk Card (Owl Athena) - shows when scholar_002 is collected
        self.sleep_entity_perk_card = QtWidgets.QFrame()
        self.sleep_entity_perk_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2e3f4a, stop:1 #1a262f);
                border: 2px solid #5c6bc0;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        entity_perk_layout = QtWidgets.QHBoxLayout(self.sleep_entity_perk_card)
        entity_perk_layout.setContentsMargins(8, 4, 8, 4)
        entity_perk_layout.setSpacing(10)
        
        # SVG icon container
        self.sleep_entity_svg_label = QtWidgets.QLabel()
        self.sleep_entity_svg_label.setFixedSize(40, 40)
        self.sleep_entity_svg_label.setStyleSheet("background: transparent;")
        entity_perk_layout.addWidget(self.sleep_entity_svg_label)
        
        # Perk description
        self.sleep_entity_perk_label = QtWidgets.QLabel()
        self.sleep_entity_perk_label.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #9fa8da;
            background: transparent;
        """)
        self.sleep_entity_perk_label.setWordWrap(True)
        entity_perk_layout.addWidget(self.sleep_entity_perk_label, 1)
        
        screenoff_main_layout.addWidget(self.sleep_entity_perk_card)
        self.sleep_entity_perk_card.hide()  # Hidden until we check perks
        
        # Update entity perk display
        self._update_sleep_entity_perk_display()
        
        # Separator
        sep_line = QtWidgets.QFrame()
        sep_line.setFrameShape(QtWidgets.QFrame.HLine)
        sep_line.setStyleSheet("color: #444;")
        screenoff_main_layout.addWidget(sep_line)
        
        # Existing screen-off time selector (for logging past sleep)
        screenoff_layout = QtWidgets.QHBoxLayout()
        self.screenoff_checkbox = QtWidgets.QCheckBox("I turned off my screen at:")
        self.screenoff_checkbox.setToolTip("Earn a bonus item for healthy digital habits!\nRewards available 22:00 - 01:00.")
        screenoff_layout.addWidget(self.screenoff_checkbox)
        self.screenoff_time = QtWidgets.QTimeEdit()
        self.screenoff_time.setDisplayFormat("HH:mm")
        self.screenoff_time.setTime(QtCore.QTime(22, 0))
        self.screenoff_time.setEnabled(False)
        self.screenoff_checkbox.stateChanged.connect(
            lambda state: self.screenoff_time.setEnabled(state == QtCore.Qt.CheckState.Checked.value)
        )
        screenoff_layout.addWidget(self.screenoff_time)
        screenoff_layout.addStretch()
        screenoff_main_layout.addLayout(screenoff_layout)
        left_layout.addWidget(screenoff_group)
        
        # Log button
        self.log_btn = QtWidgets.QPushButton("🌙 Log Sleep")
        self.log_btn.setStyleSheet("""
            QPushButton {
                background-color: #673ab7;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #7c4dff; }
        """)
        self.log_btn.clicked.connect(self._log_sleep)
        left_layout.addWidget(self.log_btn)
        
        # Quick presets
        presets_label = QtWidgets.QLabel("Quick Presets:")
        presets_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(presets_label)
        
        presets_layout = QtWidgets.QGridLayout()
        presets = [
            ("🌙 Early (22:00-6:00)", "22:00", "06:00"),
            ("😴 Standard (23:00-7:00)", "23:00", "07:00"),
            ("🦉 Night Owl (01:00-9:00)", "01:00", "09:00"),
            ("🌃 Late Night (02:00-10:00)", "02:00", "10:00"),
        ]
        for i, (label, bed, wake) in enumerate(presets):
            btn = QtWidgets.QPushButton(label)
            btn.setStyleSheet("padding: 5px;")
            btn.clicked.connect(lambda _, b=bed, w=wake: self._apply_preset(b, w))
            presets_layout.addWidget(btn, i // 2, i % 2)
        left_layout.addLayout(presets_layout)
        
        left_layout.addStretch()
        content_layout.addWidget(left_panel)
        
        # Right: Stats, recommendations, and history
        right_panel = QtWidgets.QGroupBox("Stats & Recommendations")
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        
        # Chronotype selector
        chrono_layout = QtWidgets.QHBoxLayout()
        chrono_layout.addWidget(QtWidgets.QLabel("Your chronotype:"))
        self.chronotype_combo = NoScrollComboBox()
        for chrono_id, name, emoji, _, _, desc in SLEEP_CHRONOTYPES:
            self.chronotype_combo.addItem(f"{emoji} {name}", chrono_id)
            self.chronotype_combo.setItemData(
                self.chronotype_combo.count() - 1, desc, QtCore.Qt.ToolTipRole
            )
        # Set current chronotype
        for i in range(self.chronotype_combo.count()):
            if self.chronotype_combo.itemData(i) == self.blocker.sleep_chronotype:
                self.chronotype_combo.setCurrentIndex(i)
                break
        self.chronotype_combo.currentIndexChanged.connect(self._on_chronotype_change)
        chrono_layout.addWidget(self.chronotype_combo)
        right_layout.addLayout(chrono_layout)
        
        # Recommendations display
        self.recommendations_label = QtWidgets.QLabel()
        self.recommendations_label.setWordWrap(True)
        self.recommendations_label.setStyleSheet("background-color: #1e1e2e; padding: 10px; border-radius: 5px;")
        right_layout.addWidget(self.recommendations_label)
        self._update_recommendations()
        
        # Stats display
        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("background-color: #1e1e2e; padding: 10px; border-radius: 5px;")
        right_layout.addWidget(self.stats_label)
        
        # History list
        history_label = QtWidgets.QLabel("📋 Recent Sleep History:")
        history_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(history_label)
        
        self.history_list = QtWidgets.QListWidget()
        self.history_list.setMaximumHeight(200)
        self.history_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._show_context_menu)
        right_layout.addWidget(self.history_list)
        
        # Reminder settings
        reminder_box = QtWidgets.QGroupBox("⏰ Bedtime Reminder")
        reminder_layout = QtWidgets.QHBoxLayout(reminder_box)
        self.reminder_checkbox = QtWidgets.QCheckBox("Enable reminder")
        self.reminder_checkbox.setChecked(self.blocker.sleep_reminder_enabled)
        self.reminder_checkbox.stateChanged.connect(self._update_reminder_setting)
        reminder_layout.addWidget(self.reminder_checkbox)
        reminder_layout.addWidget(QtWidgets.QLabel("at"))
        self.reminder_time = QtWidgets.QTimeEdit()
        self.reminder_time.setDisplayFormat("HH:mm")
        try:
            h, m = self.blocker.sleep_reminder_time.split(":")
            self.reminder_time.setTime(QtCore.QTime(int(h), int(m)))
        except (ValueError, AttributeError):
            self.reminder_time.setTime(QtCore.QTime(21, 0))
        self.reminder_time.timeChanged.connect(self._update_reminder_setting)
        reminder_layout.addWidget(self.reminder_time)
        reminder_layout.addStretch()
        right_layout.addWidget(reminder_box)
        
        right_layout.addStretch()
        content_layout.addWidget(right_panel)
        
        layout.addLayout(content_layout)
        
        # Rewards info section
        rewards_group = QtWidgets.QGroupBox("🎁 Rewards Info")
        rewards_layout = QtWidgets.QVBoxLayout(rewards_group)
        rewards_info = QtWidgets.QLabel(
            "<b>How it works:</b> Log sleep to earn 1 item. Rarity based on your sleep score (0-100).<br>"
            "<i>Score = duration (40%) + bedtime alignment (25%) + quality (25%) + consistency (10%)</i><br>"
            "<table style='font-size:10px; color:#888888; margin-top:5px;'>"
            "<tr><th>Score</th><th>Common</th><th>Uncommon</th><th>Rare</th><th>Epic</th><th>Legendary</th></tr>"
            "<tr><td>&lt;50</td><td colspan='5' style='text-align:center'>No reward</td></tr>"
            "<tr><td>50+</td><td>25%</td><td>50%</td><td>20%</td><td>5%</td><td>-</td></tr>"
            "<tr><td>65+</td><td>5%</td><td>20%</td><td>50%</td><td>20%</td><td>5%</td></tr>"
            "<tr><td>80+</td><td>-</td><td>5%</td><td>20%</td><td>50%</td><td>25%</td></tr>"
            "<tr><td>90+</td><td>-</td><td>-</td><td>5%</td><td>20%</td><td>75%</td></tr>"
            "<tr><td>97+</td><td>-</td><td>-</td><td>-</td><td>-</td><td>100%</td></tr>"
            "</table>"
            "<br><b>🛏️ Go to Sleep NOW:</b> Immediate reward for going to sleep! (1x per night)<br>"
            "<b>🌙 Nighty-Night Bonus:</b> Extra item when logging past sleep with screen-off time.<br>"
            "<table style='font-size:10px; color:#888888; margin-top:3px;'>"
            "<tr><th>Time</th><th>Common</th><th>Uncommon</th><th>Rare</th><th>Epic</th><th>Legendary</th></tr>"
            "<tr><td>21:00-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>100%</td></tr>"
            "<tr><td>22:00</td><td>-</td><td>-</td><td>5%</td><td>20%</td><td>75%</td></tr>"
            "<tr><td>23:00</td><td>-</td><td>5%</td><td>20%</td><td>50%</td><td>25%</td></tr>"
            "<tr><td>00:00</td><td>5%</td><td>50%</td><td>25%</td><td>15%</td><td>5%</td></tr>"
            "<tr><td>01:00+</td><td colspan='5' style='text-align:center'>No bonus</td></tr>"
            "</table>"
            "<br><b>Streaks:</b> 3n=Uncommon, 7n=Rare, 14n=Epic, 30n=Legendary (consecutive nights with 7+ hrs)"
        )
        rewards_info.setWordWrap(True)
        rewards_info.setStyleSheet("color: #888888; font-size: 10px;")
        rewards_layout.addWidget(rewards_info)
        layout.addWidget(rewards_group)
        
        self._update_sleep_duration()
    
    def _update_sleep_duration(self) -> None:
        """Update the calculated sleep duration display."""
        bedtime = self.bedtime_edit.time()
        wake_time = self.wake_edit.time()
        
        bed_mins = bedtime.hour() * 60 + bedtime.minute()
        wake_mins = wake_time.hour() * 60 + wake_time.minute()
        
        # Handle overnight sleep
        if wake_mins <= bed_mins:
            duration_mins = (24 * 60 - bed_mins) + wake_mins
        else:
            duration_mins = wake_mins - bed_mins
        
        hours = duration_mins // 60
        mins = duration_mins % 60
        
        # Color based on duration
        if 7 <= hours + mins/60 <= 9:
            color = "#4caf50"  # Green - optimal
            emoji = "🌟"
        elif 6 <= hours + mins/60 < 7:
            color = "#ff9800"  # Orange - slightly low
            emoji = "⚠️"
        elif hours + mins/60 > 9:
            color = "#2196f3"  # Blue - long
            emoji = "💤"
        else:
            color = "#f44336"  # Red - too short
            emoji = "😴"
        
        self.duration_label.setText(f"{emoji} Sleep duration: {hours}h {mins}m")
        self.duration_label.setStyleSheet(f"font-weight: bold; color: {color};")
    
    def _apply_preset(self, bedtime: str, wake_time: str) -> None:
        """Apply a quick preset."""
        try:
            h, m = bedtime.split(":")
            self.bedtime_edit.setTime(QtCore.QTime(int(h), int(m)))
            h, m = wake_time.split(":")
            self.wake_edit.setTime(QtCore.QTime(int(h), int(m)))
        except (ValueError, AttributeError):
            pass  # Invalid preset format, ignore
    
    def _on_chronotype_change(self) -> None:
        """Handle chronotype selection change."""
        chrono_id = self.chronotype_combo.currentData()
        if chrono_id:
            self.blocker.sleep_chronotype = chrono_id
            self.blocker.save_config()
            self._update_recommendations()
    
    def _update_recommendations(self) -> None:
        """Update the recommendations display based on chronotype."""
        if not get_sleep_recommendation:
            self.recommendations_label.setText("Sleep recommendations unavailable.")
            return
        
        rec = get_sleep_recommendation(self.blocker.sleep_chronotype)
        tips_html = "<br>".join(rec["tips"])
        
        self.recommendations_label.setText(
            f"<b>{rec['emoji']} {rec['chronotype']}</b><br><br>"
            f"🛏️ Optimal bedtime: {rec['optimal_bedtime']}<br>"
            f"☀️ Recommended wake: {rec['recommended_wake']}<br>"
            f"⏰ Target: {rec['target_hours']}<br><br>"
            f"<b>Tips:</b><br>{tips_html}"
        )
    
    def _update_sleep_now_preview(self) -> None:
        """Update the 'Go to Sleep NOW' preview showing expected reward tier."""
        now = QtCore.QTime.currentTime()
        current_time = now.toString("HH:mm")
        
        if not get_screen_off_bonus_rarity:
            self.sleep_now_info.setText(f"Now: {current_time}")
            return
        
        base_rarity = get_screen_off_bonus_rarity(current_time)
        if base_rarity:
            # Apply entity perk tier bonus for preview
            from gamification import get_entity_sleep_perks, get_boosted_rarity
            sleep_perks = get_entity_sleep_perks(self.blocker.adhd_buster)
            tier_bonus = sleep_perks.get("sleep_tier_bonus", 0)
            
            rarity = base_rarity
            for _ in range(tier_bonus):
                rarity = get_boosted_rarity(rarity)
            
            rarity_colors = {
                "Legendary": "#ffd700",
                "Epic": "#a335ee",
                "Rare": "#0070dd",
                "Uncommon": "#1eff00",
                "Common": "#ffffff",
            }
            color = rarity_colors.get(rarity, "#888")
            
            # Show bonus indicator if tier is boosted
            bonus_text = f" (+{tier_bonus}🦉)" if tier_bonus > 0 else ""
            self.sleep_now_info.setText(f"Now: {current_time} → <b style='color:{color}'>{rarity}</b>{bonus_text} item!")
            self.sleep_now_btn.setEnabled(True)
        else:
            # Check if it is too early (between 06:00 and 22:00)
            if QtCore.QTime(6, 0) <= now < QtCore.QTime(22, 0):
                msg = "(starts at 22:00)"
            else:
                msg = "(too late for bonus)"
            self.sleep_now_info.setText(f"Now: {current_time} {msg}")
            self.sleep_now_btn.setEnabled(False)
    
    def _update_sleep_entity_perk_display(self) -> None:
        """Update the entity perk display card if Study Owl Athena is collected."""
        try:
            adhd_data = getattr(self.blocker, 'adhd_buster', {})
            if not adhd_data:
                self.sleep_entity_perk_card.hide()
                return
            
            from gamification import get_entity_sleep_perks
            sleep_perks = get_entity_sleep_perks(adhd_data)
            tier_bonus = sleep_perks.get("sleep_tier_bonus", 0)
            
            # Hide if no tier bonus
            if tier_bonus <= 0:
                self.sleep_entity_perk_card.hide()
                return
            
            # Show the perk card
            entity_name = sleep_perks.get("entity_name", "Study Owl Athena")
            is_exceptional = sleep_perks.get("is_exceptional", False)
            description = sleep_perks.get("description", f"+{tier_bonus} Sleep Tier")
            
            perk_text = (
                f"<b>🦉 {entity_name}</b><br>"
                f"<span style='color:#9fa8da;'>{description}</span>"
            )
            self.sleep_entity_perk_label.setText(perk_text)
            
            # Load and display SVG
            self._load_sleep_entity_svg(is_exceptional)
            
            # Update border color for exceptional
            if is_exceptional:
                self.sleep_entity_perk_card.setStyleSheet("""
                    QFrame {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #3d2e4a, stop:1 #261a2f);
                        border: 2px solid #ba68c8;
                        border-radius: 8px;
                        padding: 6px;
                    }
                """)
            else:
                self.sleep_entity_perk_card.setStyleSheet("""
                    QFrame {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #2e3f4a, stop:1 #1a262f);
                        border: 2px solid #5c6bc0;
                        border-radius: 8px;
                        padding: 6px;
                    }
                """)
            
            self.sleep_entity_perk_card.show()
            
        except Exception as e:
            print(f"[Sleep Tab] Error updating entity perk display: {e}")
            self.sleep_entity_perk_card.hide()
    
    def _load_sleep_entity_svg(self, is_exceptional: bool) -> None:
        """Load and display the owl entity SVG icon."""
        try:
            from PySide6.QtSvg import QSvgRenderer
            from entitidex_tab import _resolve_entity_svg_path
            from entitidex.entity_pools import get_entity_by_id
            
            entity = get_entity_by_id("scholar_002")
            if not entity:
                return
            
            svg_path = _resolve_entity_svg_path(entity, is_exceptional)
            if not svg_path:
                return
            
            renderer = QSvgRenderer(svg_path)
            if renderer.isValid():
                icon_size = 40
                pixmap = QtGui.QPixmap(icon_size, icon_size)
                pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                self.sleep_entity_svg_label.setPixmap(pixmap)
                
        except Exception as e:
            print(f"[Sleep Tab] Error loading entity SVG: {e}")

    def _go_to_sleep_now(self) -> None:
        """Handle 'Go to Sleep NOW' button - give immediate reward based on current time."""
        if not GAMIFICATION_AVAILABLE or not is_gamification_enabled(self.blocker.adhd_buster):
            show_info(
                self, "Gamification Disabled",
                "Enable gamification mode to earn rewards!"
            )
            return
        
        if not get_screen_off_bonus_rarity:
            show_warning(
                self, "Feature Unavailable",
                "Sleep tracking module not fully loaded."
            )
            return
        
        # Get current time and calculate reward
        now = QtCore.QTime.currentTime()
        current_time = now.toString("HH:mm")
        base_rarity = get_screen_off_bonus_rarity(current_time)
        
        if not base_rarity:
            show_info(
                self, "Bonus Window Missed",
                "It's outside the Nighty-Night bonus window.\n"
                "Sleep between 22:00 and 01:00 to earn rewards!\n\n"
                "Rewards:\n"
                "• 22:00 - 22:30: Legendary (Best!)\n"
                "• 22:30 - 23:30: Legendary/Epic\n"
                "• 23:30 - 00:30: Epic/Rare\n"
                "• 00:30 - 01:00: Uncommon"
            )
            return
        
        # Apply entity perk tier bonus (Study Owl Athena)
        from gamification import get_entity_sleep_perks, get_boosted_rarity
        sleep_perks = get_entity_sleep_perks(self.blocker.adhd_buster)
        tier_bonus = sleep_perks.get("sleep_tier_bonus", 0)
        
        # Boost rarity by tier_bonus levels (capped at Legendary)
        rarity = base_rarity
        for _ in range(tier_bonus):
            rarity = get_boosted_rarity(rarity)
        
        # Check if already used today (based on sleep-now timestamp)
        today = datetime.now().strftime("%Y-%m-%d")
        last_sleep_now = self.blocker.adhd_buster.get("last_sleep_now_date", "")
        if last_sleep_now == today:
            show_info(
                self, "Already Used",
                "You already claimed your Nighty-Night bonus today!\n"
                "Come back tomorrow for another reward."
            )
            return
        
        # Confirmation dialog before claiming bonus
        rarity_emojis = {
            "Legendary": "🌟✨",
            "Epic": "💎",
            "Rare": "💙",
            "Uncommon": "💚",
            "Common": "⚪",
        }
        emoji = rarity_emojis.get(rarity, "🎁")
        
        # Build bonus info for confirmation
        bonus_info = ""
        if tier_bonus > 0:
            bonus_info = f"\n\n🦉 <i>{sleep_perks.get('entity_name', 'Owl')} boosts your reward by +{tier_bonus} tier!</i>"
        
        confirm = QtWidgets.QMessageBox(self)
        confirm.setWindowTitle("🌙 Claim Nighty-Night Bonus?")
        confirm.setText(
            f"{emoji} <b>Ready for bed?</b>\n\n"
            f"Claiming your Nighty-Night bonus at {current_time}\n"
            f"will earn you a <b>{rarity}</b> reward!{bonus_info}\n\n"
            f"Are you ready to turn off the screen and sleep?"
        )
        confirm.setIcon(QtWidgets.QMessageBox.NoIcon)
        confirm.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        confirm.setDefaultButton(QtWidgets.QMessageBox.Yes)
        confirm.setOption(QtWidgets.QMessageBox.DontUseNativeDialog, True)
        
        if confirm.exec() != QtWidgets.QMessageBox.Yes:
            return
        
        # Generate reward
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        item = generate_item(rarity=rarity, story_id=active_story)
        
        # Add source and validate item has all required fields
        item["source"] = "sleep_now_bonus"
        if "obtained_at" not in item:
            item["obtained_at"] = datetime.now().isoformat()
        
        # Update last claim date
        self.blocker.adhd_buster["last_sleep_now_date"] = today
        
        # Use GameState manager for reactive updates if available
        main_window = self.window()
        game_state = getattr(main_window, 'game_state', None)
        if not game_state:
            logger.error("GameStateManager not available - cannot award sleep now bonus")
            return
        
        # Use batch award - handles inventory, auto-equip, save, and signals
        game_state.award_items_batch([item], coins=0, auto_equip=True, source="sleep_now_bonus")
        
        # Sync hero data
        if GAMIFICATION_AVAILABLE:
            sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()
        
        # Show reward with celebratory message
        rarity_emojis = {
            "Legendary": "🌟✨",
            "Epic": "💎",
            "Rare": "💙",
            "Uncommon": "💚",
            "Common": "⚪",
        }
        emoji = rarity_emojis.get(rarity, "🎁")
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("🛏️ Sweet Dreams!")
        msg.setText(
            f"{emoji} <b>Nighty-Night Reward!</b>\n\n"
            f"For going to sleep at {current_time}, you earned:\n\n"
            f"<b style='font-size:14px'>{item['name']}</b>\n"
            f"<i>{item['rarity']}</i> {item.get('slot', 'item')}\n\n"
            f"Now turn off that screen and get some rest! 😴"
        )
        msg.setIcon(QtWidgets.QMessageBox.NoIcon)
        msg.setOption(QtWidgets.QMessageBox.DontUseNativeDialog, True)
        msg.exec()
        
        # Update preview to show it's been used
        self.sleep_now_btn.setEnabled(False)
        self.sleep_now_info.setText(f"✓ Claimed at {current_time}! Sweet dreams!")
        
        # Refresh Hero tab inventory if available
        if hasattr(self.parent(), 'adhd_tab') and self.parent().adhd_tab:
            self.parent().adhd_tab.refresh_all()

    def _log_sleep(self) -> None:
        """Log a sleep entry and check for rewards."""
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        bedtime = self.bedtime_edit.time().toString("HH:mm")
        wake_time = self.wake_edit.time().toString("HH:mm")
        quality_id = self.quality_combo.currentData()
        note = self.note_input.text().strip()
        
        # Calculate sleep hours
        bed_mins = self.bedtime_edit.time().hour() * 60 + self.bedtime_edit.time().minute()
        wake_mins = self.wake_edit.time().hour() * 60 + self.wake_edit.time().minute()
        if wake_mins <= bed_mins:
            duration_mins = (24 * 60 - bed_mins) + wake_mins
        else:
            duration_mins = wake_mins - bed_mins
        sleep_hours = duration_mins / 60
        
        # Get disruptions
        disruptions = [tag_id for tag_id, cb in self.disruption_checks.items() if cb.isChecked()]
        if not disruptions:
            disruptions = ["none"]
        
        # Check for existing entry on this date
        existing_idx = -1
        for i, entry in enumerate(self.blocker.sleep_entries):
            if entry.get("date") == date_str:
                existing_idx = i
                break
        
        # Get rewards (skip if gamification mode is disabled)
        entries_for_reward = [e for e in self.blocker.sleep_entries if e.get("date") != date_str]
        reward_info = None
        if check_all_sleep_rewards and GAMIFICATION_AVAILABLE and is_gamification_enabled(self.blocker.adhd_buster):
            active_story = self.blocker.adhd_buster.get("active_story", "warrior")
            reward_info = check_all_sleep_rewards(
                entries_for_reward,
                sleep_hours,
                bedtime,
                wake_time,
                quality_id,
                disruptions,
                date_str,
                self.blocker.sleep_milestones,
                self.blocker.sleep_chronotype,
                story_id=active_story,
            )
        
        # Create new entry
        new_entry = {
            "date": date_str,
            "sleep_hours": round(sleep_hours, 2),
            "bedtime": bedtime,
            "wake_time": wake_time,
            "quality": quality_id,
            "disruptions": disruptions,
            "score": reward_info.get("score", 0) if reward_info else 0,
            "note": note,
        }
        
        # Handle existing entry
        if existing_idx >= 0:
            reply = show_question(
                self, "Entry Exists",
                f"You already have a sleep entry for {date_str}.\nReplace it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
            self.blocker.sleep_entries[existing_idx] = new_entry
        else:
            self.blocker.sleep_entries.append(new_entry)
            self.blocker.sleep_entries.sort(key=lambda x: x.get("date", ""), reverse=True)
            # Prune to last 365 entries to prevent unbounded growth
            if len(self.blocker.sleep_entries) > 365:
                self.blocker.sleep_entries = self.blocker.sleep_entries[:365]
        
        # Track screen-off bonus outside the reward block
        screenoff_bonus_item = None
        
        # Handle rewards
        if reward_info and GAMIFICATION_AVAILABLE:
            items_earned = []
            
            # Base reward - collect items, add to inventory via game_state below
            if reward_info.get("reward"):
                item = reward_info["reward"]
                items_earned.append(item)
            
            # Streak reward
            if reward_info.get("streak_reward"):
                streak_item = reward_info["streak_reward"]["item"]
                items_earned.append(streak_item)
                self.blocker.sleep_milestones.append(reward_info["streak_reward"]["milestone_id"])
            
            # Milestone rewards
            new_milestone_ids = []
            for milestone in reward_info.get("new_milestones", []):
                items_earned.append(milestone["item"])
                new_milestone_ids.append(milestone["milestone_id"])
            
            if new_milestone_ids:
                self.blocker.sleep_milestones.extend(new_milestone_ids)
            
            # Screen-Off (Nighty-Night) bonus reward
            screenoff_bonus_item = None
            if self.screenoff_checkbox.isChecked() and get_screen_off_bonus_rarity:
                screenoff_time = self.screenoff_time.time().toString("HH:mm")
                screenoff_rarity = get_screen_off_bonus_rarity(screenoff_time)
                if screenoff_rarity:
                    active_story = self.blocker.adhd_buster.get("active_story", "warrior")
                    screenoff_bonus_item = generate_item(rarity=screenoff_rarity, story_id=active_story)
                    screenoff_bonus_item["source"] = "nighty_night_bonus"
                    if "obtained_at" not in screenoff_bonus_item:
                        screenoff_bonus_item["obtained_at"] = datetime.now().isoformat()
                    items_earned.append(screenoff_bonus_item)
            
            # Award all items via GameState
            if items_earned:
                main_window = self.window()
                game_state = getattr(main_window, 'game_state', None)
                if not game_state:
                    logger.error("GameStateManager not available - cannot award sleep rewards")
                else:
                    # Use batch award - handles inventory, auto-equip, save, and signals
                    game_state.award_items_batch(items_earned, coins=0, auto_equip=True, source="sleep_tracking")
            
            # Sync hero data
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
        
        self.blocker.save_config()
        
        # Update main timeline widget if parent window has it
        if self.parent() and hasattr(self.parent(), 'timeline_widget'):
            try:
                self.parent().timeline_widget.update_data()
            except Exception:
                pass
        
        # Show feedback
        score = new_entry.get("score", 0)
        msg = f"🌙 Sleep logged for {date_str}\n\n"
        msg += f"Duration: {format_sleep_duration(sleep_hours) if format_sleep_duration else f'{sleep_hours:.1f}h'}\n"
        msg += f"Score: {score}/100\n"
        
        if reward_info:
            for m in reward_info.get("messages", [])[:5]:  # Limit messages
                msg += f"\n{m}"
            
            if reward_info.get("reward"):
                rarity = reward_info["reward"]["rarity"]
                rarity_colors = {
                    "Common": "#9e9e9e",
                    "Uncommon": "#4caf50", 
                    "Rare": "#2196f3",
                    "Epic": "#9c27b0",
                    "Legendary": "#ff9800"
                }
                color = rarity_colors.get(rarity, "#9e9e9e")
                name = reward_info["reward"].get("name", "Unknown Item")
                msg += f"\n\n🎁 Earned: <span style='color:{color}; font-weight:bold;'>[{rarity}]</span> {name}"
            
            # Show screen-off bonus if earned
            if screenoff_bonus_item:
                rarity = screenoff_bonus_item.get("rarity", "Common")
                rarity_colors = {
                    "Common": "#9e9e9e",
                    "Uncommon": "#4caf50", 
                    "Rare": "#2196f3",
                    "Epic": "#9c27b0",
                    "Legendary": "#ff9800"
                }
                color = rarity_colors.get(rarity, "#9e9e9e")
                name = screenoff_bonus_item.get("name", "Unknown Item")
                msg += f"\n\n🌙 Nighty-Night Bonus: <span style='color:{color}; font-weight:bold;'>[{rarity}]</span> {name}"
        
        # Use custom QMessageBox to render HTML
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("Sleep Logged! 😴")
        msg_box.setIcon(QtWidgets.QMessageBox.NoIcon)
        msg_box.setTextFormat(QtCore.Qt.RichText)
        msg_box.setText(msg.replace("\n", "<br>"))
        msg_box.setOption(QtWidgets.QMessageBox.DontUseNativeDialog, True)
        msg_box.exec()
        
        # Clear form
        self.note_input.clear()
        for cb in self.disruption_checks.values():
            cb.setChecked(False)
        self.screenoff_checkbox.setChecked(False)
        
        self._refresh_display()
    
    def _refresh_display(self) -> None:
        """Refresh stats and history display."""
        # Update stats
        if get_sleep_stats:
            stats = get_sleep_stats(self.blocker.sleep_entries)
            streak = stats.get("current_streak", 0)
            streak_emoji = "🔥" if streak >= 3 else "📊"
            
            self.stats_label.setText(
                f"<b>📊 Your Sleep Stats</b><br><br>"
                f"🌙 Total nights tracked: {stats.get('total_nights', 0)}<br>"
                f"⏰ Average sleep: {stats.get('avg_hours', 0):.1f}h<br>"
                f"📈 This week average: {stats.get('this_week_avg', 0):.1f}h<br>"
                f"🏆 Best score: {stats.get('best_score', 0):.0f}/100<br>"
                f"✅ Nights on target (7+h): {stats.get('nights_on_target', 0)} "
                f"({stats.get('target_rate', 0):.0f}%)<br>"
                f"{streak_emoji} Current streak: {streak} nights"
            )
        else:
            entries = self.blocker.sleep_entries
            self.stats_label.setText(f"📊 {len(entries)} sleep entries logged")
        
        # Update history
        self.history_list.clear()
        for entry in self.blocker.sleep_entries[:20]:  # Last 20 entries
            date = entry.get("date", "Unknown")
            hours = entry.get("sleep_hours", 0)
            score = entry.get("score", 0)
            quality = entry.get("quality", "unknown")
            
            # Find quality emoji
            quality_emoji = "😴"
            for q_id, _, emoji, _ in SLEEP_QUALITY_FACTORS:
                if q_id == quality:
                    quality_emoji = emoji
                    break
            
            # Score color
            if score >= 80:
                score_color = "🟢"
            elif score >= 60:
                score_color = "🟡"
            else:
                score_color = "🔴"
            
            text = f"{date}: {hours:.1f}h {quality_emoji} {score_color} {score}pts"
            if entry.get("note"):
                text += f" 📝"
            
            item = QtWidgets.QListWidgetItem(text)
            item.setData(QtCore.Qt.UserRole, entry)
            self.history_list.addItem(item)
    
    def _show_context_menu(self, pos: QtCore.QPoint) -> None:
        """Show context menu for history items."""
        item = self.history_list.itemAt(pos)
        if not item:
            return
        
        entry_index = self.history_list.row(item)
        menu = QtWidgets.QMenu(self)
        
        view_action = menu.addAction("📋 View Details")
        delete_action = menu.addAction("🗑️ Delete Entry")
        
        action = menu.exec(self.history_list.mapToGlobal(pos))
        
        if action == view_action:
            self._view_entry_details(entry_index)
        elif action == delete_action:
            self._delete_entry(entry_index)
    
    def _view_entry_details(self, entry_index: int) -> None:
        """Show details for a sleep entry."""
        if entry_index < 0 or entry_index >= len(self.blocker.sleep_entries):
            return
        entry = self.blocker.sleep_entries[entry_index]
        
        disruptions = entry.get("disruptions", [])
        disruption_text = ""
        for d in disruptions:
            for tag_id, name, emoji, _ in SLEEP_DISRUPTION_TAGS:
                if tag_id == d:
                    disruption_text += f"  {emoji} {name}\n"
                    break
        if not disruption_text:
            disruption_text = "  None\n"
        
        details = (
            f"📅 Date: {entry.get('date', 'Unknown')}\n"
            f"🛏️ Bedtime: {entry.get('bedtime', 'Unknown')}\n"
            f"☀️ Wake time: {entry.get('wake_time', 'Unknown')}\n"
            f"⏰ Duration: {entry.get('sleep_hours', 0):.1f} hours\n"
            f"⭐ Quality: {entry.get('quality', 'Unknown')}\n"
            f"📊 Score: {entry.get('score', 0)}/100\n"
            f"\n📋 Disruptions:\n{disruption_text}"
        )
        if entry.get("note"):
            details += f"\n📝 Note: {entry['note']}"
        
        show_info(self, "Sleep Entry Details", details)
    
    def _delete_entry(self, entry_index: int) -> None:
        """Delete a sleep entry."""
        if entry_index < 0 or entry_index >= len(self.blocker.sleep_entries):
            return
        entry = self.blocker.sleep_entries[entry_index]
        
        reply = show_question(
            self, "Delete Entry",
            f"Delete sleep entry for {entry.get('date', 'Unknown')}?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            del self.blocker.sleep_entries[entry_index]
            self.blocker.save_config()
            self._refresh_display()
            
            # Update main timeline widget if parent window has it
            if self.parent() and hasattr(self.parent(), 'timeline_widget'):
                try:
                    self.parent().timeline_widget.update_data()
                except Exception:
                    pass
    
    def _setup_reminder(self) -> None:
        """Setup bedtime reminder timer."""
        if self._reminder_timer is not None:
            self._reminder_timer.stop()
        
        if not self.blocker.sleep_reminder_enabled:
            return
        
        self._reminder_timer = QtCore.QTimer(self)
        self._reminder_timer.timeout.connect(self._check_reminder)
        self._reminder_timer.start(60000)  # Check every minute
    
    def _check_reminder(self) -> None:
        """Check if it's time to show bedtime reminder."""
        if not self.blocker.sleep_reminder_enabled:
            return
        
        today = datetime.now().strftime("%Y-%m-%d")
        if self.blocker.sleep_last_reminder_date == today:
            return
        
        current_time = QtCore.QTime.currentTime()
        try:
            h, m = self.blocker.sleep_reminder_time.split(":")
            reminder_time = QtCore.QTime(int(h), int(m))
        except (ValueError, AttributeError):
            return
        
        if current_time >= reminder_time:
            self.blocker.sleep_last_reminder_date = today
            self.blocker.save_config()
            
            # Get personalized recommendation
            if get_sleep_recommendation:
                rec = get_sleep_recommendation(self.blocker.sleep_chronotype)
                bedtime_rec = rec['optimal_bedtime']
            else:
                bedtime_rec = "before midnight"
            
            show_info(
                self, "🌙 Bedtime Reminder",
                f"Time to start winding down!\n\n"
                f"Your optimal bedtime: {bedtime_rec}\n\n"
                "Tips for better sleep:\n"
                "• Dim the lights\n"
                "• Put away screens\n"
                "• Relax and prepare for rest\n\n"
                "Good sleep = rewards for your hero! 😴"
            )
    
    def _update_reminder_setting(self) -> None:
        """Update reminder settings."""
        self.blocker.sleep_reminder_enabled = self.reminder_checkbox.isChecked()
        self.blocker.sleep_reminder_time = self.reminder_time.time().toString("HH:mm")
        self.blocker.save_config()
        self._setup_reminder()


class AITab(QtWidgets.QWidget):
    """AI insights tab - productivity coach, achievements, goals, challenges."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        # Initialize AI/gamification components
        self.analyzer = ProductivityAnalyzer(blocker.stats_path) if ProductivityAnalyzer else None
        self.gamification = GamificationEngine(blocker.stats_path) if GamificationEngine else None
        self.focus_goals = FocusGoals(blocker.goals_path, blocker.stats_path) if FocusGoals else None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        inner = QtWidgets.QVBoxLayout(container)

        # AI Status
        status_group = QtWidgets.QGroupBox("🤖 AI Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)
        if AI_AVAILABLE:
            status_layout.addWidget(QtWidgets.QLabel("✅ AI features available"))
        else:
            status_layout.addWidget(QtWidgets.QLabel("⚠️ AI not available - install with: pip install -r requirements_ai.txt"))
        inner.addWidget(status_group)

        # Productivity Insights
        insights_group = QtWidgets.QGroupBox("💡 Productivity Insights")
        insights_layout = QtWidgets.QVBoxLayout(insights_group)
        self.insights_text = QtWidgets.QTextEdit()
        self.insights_text.setReadOnly(True)
        self.insights_text.setMaximumHeight(150)
        insights_layout.addWidget(self.insights_text)
        refresh_btn = QtWidgets.QPushButton("🔄 Get AI Insights")
        refresh_btn.clicked.connect(self._get_insights)
        refresh_btn.setEnabled(AI_AVAILABLE)
        insights_layout.addWidget(refresh_btn)
        inner.addWidget(insights_group)

        # Achievements
        achievements_group = QtWidgets.QGroupBox("🏆 Achievements & Challenges")
        achievements_layout = QtWidgets.QVBoxLayout(achievements_group)
        
        # Intro label challenging the user
        self.achievements_intro = QtWidgets.QLabel()
        self.achievements_intro.setWordWrap(True)
        self.achievements_intro.setStyleSheet("font-weight: bold; color: #2196F3; padding: 5px;")
        achievements_layout.addWidget(self.achievements_intro)
        
        # Unlocked trophies section
        unlocked_label = QtWidgets.QLabel("✅ Trophies Earned:")
        unlocked_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        achievements_layout.addWidget(unlocked_label)
        self.unlocked_achievements_list = QtWidgets.QListWidget()
        self.unlocked_achievements_list.setMaximumHeight(80)
        self.unlocked_achievements_list.setStyleSheet("background-color: #E8F5E9; color: #1b5e20;")
        achievements_layout.addWidget(self.unlocked_achievements_list)
        
        # Active challenges section
        challenges_label = QtWidgets.QLabel("🎯 Your Next Challenges — Can You Complete Them?")
        challenges_label.setStyleSheet("font-weight: bold; margin-top: 10px; color: #FF5722;")
        achievements_layout.addWidget(challenges_label)
        self.achievements_list = QtWidgets.QListWidget()
        self.achievements_list.setMaximumHeight(150)
        self.achievements_list.setStyleSheet("background-color: #FFF3E0; color: #5d4037;")
        achievements_layout.addWidget(self.achievements_list)
        
        inner.addWidget(achievements_group)

        # Daily Challenge
        challenge_group = QtWidgets.QGroupBox("🎯 Daily Challenge")
        challenge_layout = QtWidgets.QVBoxLayout(challenge_group)
        self.challenge_label = QtWidgets.QLabel()
        challenge_layout.addWidget(self.challenge_label)
        self.challenge_progress = QtWidgets.QProgressBar()
        self.challenge_progress.setMaximum(100)
        challenge_layout.addWidget(self.challenge_progress)
        new_challenge_btn = QtWidgets.QPushButton("🎲 New Challenge")
        new_challenge_btn.clicked.connect(self._new_challenge)
        challenge_layout.addWidget(new_challenge_btn)
        inner.addWidget(challenge_group)

        # Goals
        goals_group = QtWidgets.QGroupBox("📋 Goals")
        goals_layout = QtWidgets.QVBoxLayout(goals_group)
        self.goals_list = QtWidgets.QListWidget()
        self.goals_list.setMaximumHeight(120)
        goals_layout.addWidget(self.goals_list)
        goals_btn_layout = QtWidgets.QHBoxLayout()
        add_goal_btn = QtWidgets.QPushButton("➕ Add Goal")
        add_goal_btn.clicked.connect(self._add_goal)
        goals_btn_layout.addWidget(add_goal_btn)
        rem_goal_btn = QtWidgets.QPushButton("✓ Complete Goal")
        rem_goal_btn.clicked.connect(self._complete_goal)
        goals_btn_layout.addWidget(rem_goal_btn)
        goals_btn_layout.addStretch()
        goals_layout.addLayout(goals_btn_layout)
        inner.addWidget(goals_group)

        # AI-powered statistics
        stats_group = QtWidgets.QGroupBox("📈 AI-Powered Statistics")
        stats_layout = QtWidgets.QVBoxLayout(stats_group)
        self.ai_stats_text = QtWidgets.QTextEdit()
        self.ai_stats_text.setReadOnly(True)
        self.ai_stats_text.setMaximumHeight(180)
        stats_layout.addWidget(self.ai_stats_text)
        inner.addWidget(stats_group)

        inner.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        self._refresh_data()

    def _refresh_data(self) -> None:
        # Achievements - split into unlocked trophies and active challenges
        self.achievements_list.clear()
        self.unlocked_achievements_list.clear()
        
        if self.gamification:
            progress = self.gamification.check_achievements()
            achievements_def = self.gamification.get_achievements()
            
            unlocked_count = 0
            locked_items = []
            
            for ach_id, data in achievements_def.items():
                prog = progress.get(ach_id, {"current": 0, "target": 1, "unlocked": False})
                pct = min(100, int((prog["current"] / prog["target"]) * 100)) if prog["target"] else 0
                
                if prog.get("unlocked"):
                    # Unlocked achievement - show as trophy
                    unlocked_count += 1
                    item = QtWidgets.QListWidgetItem(f"{data['icon']} {data['name']} — COMPLETE! 🎉")
                    item.setToolTip(f"✅ {data['name']}\n{data.get('description', '')}\nYou did it!")
                    self.unlocked_achievements_list.addItem(item)
                else:
                    # Locked achievement - show as challenge with encouraging text
                    current_val = prog["current"]
                    target_val = prog["target"]
                    
                    # Clamp display values to meaningful ranges
                    display_current = min(current_val, target_val)
                    remaining = max(0, target_val - current_val)
                    
                    challenge_text = f"{data['icon']} {data['name']}: {data.get('description', '')} — {display_current}/{target_val} ({remaining} to go!)"
                    locked_items.append((pct, challenge_text, data))
            
            # Sort challenges by progress (closest to completion first)
            locked_items.sort(key=lambda x: -x[0])
            
            for pct, challenge_text, data in locked_items:
                item = QtWidgets.QListWidgetItem(challenge_text)
                # Add motivational tooltip
                if pct >= 75:
                    tip = f"🔥 SO CLOSE! You're {pct}% there!\n{data.get('description', '')}"
                elif pct >= 50:
                    tip = f"💪 Halfway there! Keep pushing!\n{data.get('description', '')}"
                elif pct >= 25:
                    tip = f"📈 Good progress! Don't stop now!\n{data.get('description', '')}"
                else:
                    tip = f"🚀 Challenge yourself: {data.get('description', '')}"
                item.setToolTip(tip)
                self.achievements_list.addItem(item)
            
            # Update intro label with personalized challenge
            total = len(achievements_def)
            if unlocked_count == 0:
                intro = "🎮 You haven't unlocked any achievements yet! Complete focus sessions to earn your first trophy!"
            elif unlocked_count == total:
                intro = "🏆 LEGENDARY! You've unlocked ALL achievements! You are a focus master!"
            elif unlocked_count >= total * 0.75:
                intro = f"🔥 Almost there! {unlocked_count}/{total} achievements unlocked. Can you get them all?"
            else:
                intro = f"💪 {unlocked_count}/{total} trophies earned! Take on the challenges below to unlock more!"
            self.achievements_intro.setText(intro)
            
            # Show message if no unlocked achievements
            if unlocked_count == 0:
                self.unlocked_achievements_list.addItem("No trophies yet — complete your first focus session!")
        else:
            self.achievements_intro.setText("🔧 AI module not installed")
            self.achievements_list.addItem("Install requirements_ai.txt to unlock achievements and challenges!")

        # Challenge
        if self.gamification:
            challenge = self.gamification.get_daily_challenge()
            current = challenge.get("progress", {}).get("current", 0)
            target = challenge.get("progress", {}).get("target", 1)
            pct = min(100, int((current / target) * 100)) if target else 0
            self.challenge_label.setText(f"{challenge.get('title', 'Daily Challenge')}: {challenge.get('description', '')}")
            self.challenge_progress.setValue(pct)
            self.challenge_progress.setFormat(f"{current}/{target} ({pct}%)")
        else:
            self.challenge_label.setText("Install AI dependencies to enable challenges.")
            self.challenge_progress.setValue(0)

        # Goals
        self.goals_list.clear()
        if self.focus_goals:
            try:
                self.focus_goals.update_progress()
                for goal in self.focus_goals.get_active_goals():
                    pct = 0
                    target = goal.get("target", 1)
                    progress_val = goal.get("progress", 0)
                    pct = min(100, int((progress_val / target) * 100)) if target else 0
                    self.goals_list.addItem(
                        f"🎯 {goal.get('title', 'Goal')} — {pct}% ({progress_val/3600:.1f}h/{target/3600:.1f}h)"
                    )
            except Exception:
                pass

        # AI stats
        stats_lines: List[str] = []
        if self.analyzer:
            try:
                optimal = self.analyzer.predict_optimal_session_length()
                patterns = self.analyzer.get_distraction_patterns()
                stats_lines.append(f"Optimal session length: {optimal} min")
                stats_lines.append(f"Weekday vs weekend: {patterns.get('weekday_vs_weekend', 'balanced')}")
                stats_lines.append(f"Consistency: {patterns.get('consistency', 'n/a')}")
            except Exception:
                stats_lines.append("AI stats unavailable (error reading data).")
        else:
            stats_lines.append("Install AI requirements to view statistics.")
        self.ai_stats_text.setPlainText("\n".join(stats_lines))

    def _get_insights(self) -> None:
        if not AI_AVAILABLE:
            self.insights_text.setPlainText("AI not available")
            return

        # Prefer local analyzer if available
        if self.analyzer:
            try:
                insights = self.analyzer.generate_insights()
                recs = self.analyzer.get_recommendations()
                lines = []
                for ins in insights:
                    lines.append(f"{ins.get('title', 'Insight')}: {ins.get('message', '')}")
                lines.append("\nRecommendations:")
                for rec in recs:
                    lines.append(f"• {rec.get('suggestion', '')} ({rec.get('reason', '')})")
                self.insights_text.setPlainText("\n".join(lines))
                return
            except Exception:
                pass
        
        # Legacy ProductivityAI fallback removed as we don't aim for backward compatibility
        self.insights_text.setPlainText("AI Insights unavailable.")

    def _new_challenge(self) -> None:
        if self.gamification:
            # Refresh daily challenge from AI engine
            challenge = self.gamification.get_daily_challenge()
            self._refresh_data()
        else:
            show_warning(self, "Feature Unavailable", "Gamification Engine is not loaded.")

    def _add_goal(self) -> None:
        goal, ok = QtWidgets.QInputDialog.getText(self, "Add Goal", "Enter your goal:")
        if ok and goal.strip():
            if self.focus_goals:
                try:
                    # Default to weekly 5h target for new AI goal
                    self.focus_goals.add_goal(goal.strip(), "weekly", target=5 * 3600)
                except Exception:
                    show_warning(self, "Error", "Failed to add goal via FocusGoals.")
            else:
                 show_warning(self, "Feature Unavailable", "FocusGoals module not loaded.")
            self._refresh_data()

    def _complete_goal(self) -> None:
        item = self.goals_list.currentItem()
        if not item:
            show_warning(self, "No Goal Selected", "Please select a goal from the list first.")
            return

        # Use FocusGoals exclusively
        if self.focus_goals:
            try:
                row = self.goals_list.currentRow()
                active = self.focus_goals.get_active_goals()
                if 0 <= row < len(active):
                    goal_id = active[row]["id"]
                    self.focus_goals.complete_goal(goal_id)
                    show_info(self, "Goal Completed!", "🎉 Goal marked as complete!")
                    self._refresh_data()
            except Exception:
                show_warning(self, "Error", "Failed to update goal status.")
        else:
             show_warning(self, "Feature Unavailable", "FocusGoals module not loaded.")


# ============================================================================
# Collapsible Section Widget
# ============================================================================

class CollapsibleSection(QtWidgets.QWidget):
    """A collapsible section widget with a toggle button header."""
    
    collapsed_changed = QtCore.Signal(str, bool)  # section_id, is_collapsed
    
    def __init__(self, title: str, section_id: str, parent=None, collapsed: bool = False):
        super().__init__(parent)
        self.section_id = section_id
        self._collapsed = collapsed
        
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header button
        self.toggle_btn = QtWidgets.QPushButton()
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(not collapsed)
        self.toggle_btn.clicked.connect(self._on_toggle)
        self.toggle_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self._update_header(title)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.05);
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
                text-align: left;
                font-weight: bold;
                color: #ccc;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
            QPushButton:checked {
                color: #fff;
            }
        """)
        self.main_layout.addWidget(self.toggle_btn)
        
        # Content container
        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 4, 0, 4)
        self.content_layout.setSpacing(4)
        self.main_layout.addWidget(self.content_widget)
        
        # Set initial state
        self.content_widget.setVisible(not collapsed)
        self._title = title
    
    def _update_header(self, title: str):
        arrow = "▼" if not self._collapsed else "▶"
        self.toggle_btn.setText(f"{arrow} {title}")
    
    def _on_toggle(self):
        self._collapsed = not self.toggle_btn.isChecked()
        self.content_widget.setVisible(not self._collapsed)
        self._update_header(self._title)
        self.collapsed_changed.emit(self.section_id, self._collapsed)
    
    def set_title(self, title: str):
        self._title = title
        self._update_header(title)
    
    def add_widget(self, widget: QtWidgets.QWidget):
        self.content_layout.addWidget(widget)
    
    def clear_content(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self.toggle_btn.setChecked(not collapsed)
        self.content_widget.setVisible(not collapsed)
        self._update_header(self._title)
    
    def is_collapsed(self) -> bool:
        return self._collapsed


# ============================================================================
# ADHD Buster Gamification Dialogs (Qt Implementation)
# ============================================================================

class CharacterCanvas(QtWidgets.QWidget):
    """Qt widget for rendering the ADHD Buster character with equipped gear."""

    TIER_COLORS = {
        "pathetic": "#bdbdbd", "modest": "#a5d6a7", "decent": "#81c784",
        "heroic": "#64b5f6", "epic": "#ba68c8", "legendary": "#ffb74d", "godlike": "#ffd54f"
    }

    TIER_GLOW = {
        "pathetic": None, "modest": None, "decent": "#c8e6c9",
        "heroic": "#bbdefb", "epic": "#e1bee7", "legendary": "#ffe0b2", "godlike": "#fff9c4"
    }
    
    TIER_OUTLINE = {
        "pathetic": "#888", "modest": "#6b9b6d", "decent": "#5a9a5c",
        "heroic": "#4a90c4", "epic": "#8a4a9c", "legendary": "#c98a3a", "godlike": "#d4a82a"
    }
    
    TIER_PARTICLES = {
        "pathetic": None, "modest": None, "decent": None,
        "heroic": ("#64b5f6", 4), "epic": ("#e040fb", 6), 
        "legendary": ("#ffd700", 8), "godlike": ("#fff9c4", 12)
    }

    def __init__(self, equipped: dict, power: int, width: int = 180, height: int = 220,
                 parent: Optional[QtWidgets.QWidget] = None, story_theme: str = "warrior") -> None:
        super().__init__(parent)
        self.equipped = equipped
        self.power = power
        self.story_theme = story_theme  # warrior, scholar, wanderer, underdog
        self.setFixedSize(width, height)
        if GAMIFICATION_AVAILABLE:
            self.tier = get_diary_power_tier(power)
        else:
            self.tier = "pathetic" if power < 50 else "modest" if power < 150 else "decent"
        # Generate stable particle positions based on power (deterministic)
        import random
        rng = random.Random(power)
        self._particles = [(rng.randint(-50, 50), rng.randint(-60, 60), rng.randint(2, 5)) 
                           for _ in range(15)]

    def paintEvent(self, event) -> None:
        """Dispatch to theme-specific drawing method."""
        if self.story_theme == "scholar":
            self._draw_scholar_character(event)
        elif self.story_theme == "wanderer":
            self._draw_wanderer_character(event)
        elif self.story_theme == "underdog":
            self._draw_underdog_character(event)
        elif self.story_theme == "scientist":
            self._draw_scientist_character(event)
        else:
            self._draw_warrior_character(event)

    def _draw_warrior_character(self, event) -> None:
        """Draw the classic fantasy warrior character."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2 + 5

        # Background with radial gradient for depth
        bg_gradient = QtGui.QRadialGradient(cx, cy - 20, max(w, h) * 0.8)
        bg_gradient.setColorAt(0, QtGui.QColor("#404050"))
        bg_gradient.setColorAt(0.5, QtGui.QColor("#2d2d3d"))
        bg_gradient.setColorAt(1, QtGui.QColor("#1a1a2a"))
        painter.fillRect(self.rect(), bg_gradient)
        
        # Floor with gradient
        floor_gradient = QtGui.QLinearGradient(cx - 40, cy + 70, cx + 40, cy + 85)
        floor_gradient.setColorAt(0, QtGui.QColor(0, 0, 0, 30))
        floor_gradient.setColorAt(0.5, QtGui.QColor(0, 0, 0, 80))
        floor_gradient.setColorAt(1, QtGui.QColor(0, 0, 0, 30))
        painter.setBrush(floor_gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(cx - 40, cy + 68, 80, 18)

        body_color = QtGui.QColor(self.TIER_COLORS.get(self.tier, "#bdbdbd"))
        body_outline = QtGui.QColor(self.TIER_OUTLINE.get(self.tier, "#888"))
        glow = self.TIER_GLOW.get(self.tier)

        def darken(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.darker(amount)
        
        def lighten(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.lighter(amount)

        # Glow aura for high tiers (multiple layers)
        if glow:
            glow_color = QtGui.QColor(glow)
            # Outer glow
            painter.setBrush(QtCore.Qt.NoBrush)
            for i, opacity in enumerate([0.1, 0.15, 0.25, 0.35]):
                painter.setOpacity(opacity)
                size = 140 - i * 15
                painter.setPen(QtGui.QPen(glow_color, 3))
                painter.drawEllipse(cx - size//2, cy - 70, size, int(size * 1.2))
            painter.setOpacity(1.0)
            # Inner glow fill
            painter.setBrush(glow_color)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setOpacity(0.25)
            painter.drawEllipse(cx - 50, cy - 60, 100, 130)
            painter.setOpacity(1.0)
        
        # Particle effects for high tiers
        particles = self.TIER_PARTICLES.get(self.tier)
        if particles:
            p_color, p_count = particles
            painter.setBrush(QtGui.QColor(p_color))
            painter.setPen(QtCore.Qt.NoPen)
            for i, (px, py, ps) in enumerate(self._particles[:p_count]):
                painter.setOpacity(0.4 + (i % 3) * 0.2)
                painter.drawEllipse(cx + px, cy + py, ps, ps)
            painter.setOpacity(1.0)

        # === CLOAK (behind body) ===
        cloak = self.equipped.get("Cloak")
        if cloak:
            cc = QtGui.QColor(cloak.get("color", "#666"))
            # Flowing cloak shape with curves
            path = QtGui.QPainterPath()
            path.moveTo(cx - 22, cy - 28)
            path.lineTo(cx + 22, cy - 28)
            path.cubicTo(cx + 35, cy, cx + 40, cy + 35, cx + 35, cy + 68)
            path.quadTo(cx + 20, cy + 72, cx, cy + 70)
            path.quadTo(cx - 20, cy + 72, cx - 35, cy + 68)
            path.cubicTo(cx - 40, cy + 35, cx - 35, cy, cx - 22, cy - 28)
            # Cloak gradient for depth
            cloak_gradient = QtGui.QLinearGradient(cx - 35, cy, cx + 35, cy)
            cloak_gradient.setColorAt(0, darken(cloak.get("color", "#666"), 140))
            cloak_gradient.setColorAt(0.3, cc)
            cloak_gradient.setColorAt(0.7, cc)
            cloak_gradient.setColorAt(1, darken(cloak.get("color", "#666"), 120))
            painter.setBrush(cloak_gradient)
            painter.setPen(QtGui.QPen(darken(cloak.get("color", "#666"), 150), 2))
            painter.drawPath(path)
            # Cloak folds
            painter.setPen(QtGui.QPen(darken(cloak.get("color", "#666"), 160), 1))
            painter.drawLine(cx - 15, cy - 20, cx - 20, cy + 60)
            painter.drawLine(cx + 15, cy - 20, cx + 20, cy + 60)
            painter.drawLine(cx, cy - 15, cx, cy + 65)
            # Cloak clasp at neck
            painter.setBrush(QtGui.QColor("#b8860b"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#8b6914"), 1))
            painter.drawEllipse(cx - 5, cy - 30, 10, 8)

        # === LEGS with shading ===
        # Left leg gradient
        leg_grad_l = QtGui.QLinearGradient(cx - 18, cy + 22, cx - 5, cy + 22)
        leg_grad_l.setColorAt(0, body_color.darker(120))
        leg_grad_l.setColorAt(0.5, body_color)
        leg_grad_l.setColorAt(1, body_color.darker(110))
        painter.setBrush(leg_grad_l)
        painter.setPen(QtGui.QPen(body_outline, 2))
        leg_path_l = QtGui.QPainterPath()
        leg_path_l.moveTo(cx - 18, cy + 22)
        leg_path_l.lineTo(cx - 4, cy + 22)
        leg_path_l.quadTo(cx - 3, cy + 40, cx - 5, cy + 55)
        leg_path_l.lineTo(cx - 18, cy + 55)
        leg_path_l.quadTo(cx - 19, cy + 40, cx - 18, cy + 22)
        painter.drawPath(leg_path_l)
        # Right leg gradient
        leg_grad_r = QtGui.QLinearGradient(cx + 4, cy + 22, cx + 18, cy + 22)
        leg_grad_r.setColorAt(0, body_color.darker(110))
        leg_grad_r.setColorAt(0.5, body_color)
        leg_grad_r.setColorAt(1, body_color.darker(120))
        painter.setBrush(leg_grad_r)
        leg_path_r = QtGui.QPainterPath()
        leg_path_r.moveTo(cx + 4, cy + 22)
        leg_path_r.lineTo(cx + 18, cy + 22)
        leg_path_r.quadTo(cx + 19, cy + 40, cx + 18, cy + 55)
        leg_path_r.lineTo(cx + 5, cy + 55)
        leg_path_r.quadTo(cx + 3, cy + 40, cx + 4, cy + 22)
        painter.drawPath(leg_path_r)

        # === BOOTS ===
        boots = self.equipped.get("Boots")
        if boots:
            bc = QtGui.QColor(boots.get("color", "#666"))
            # Boot gradient for 3D effect
            boot_grad = QtGui.QLinearGradient(0, cy + 52, 0, cy + 74)
            boot_grad.setColorAt(0, bc.lighter(110))
            boot_grad.setColorAt(0.5, bc)
            boot_grad.setColorAt(1, bc.darker(120))
            painter.setBrush(boot_grad)
            painter.setPen(QtGui.QPen(bc.darker(140), 2))
            # Left boot with curved toe
            left_boot = QtGui.QPainterPath()
            left_boot.moveTo(cx - 20, cy + 52)
            left_boot.lineTo(cx - 2, cy + 52)
            left_boot.lineTo(cx - 2, cy + 68)
            left_boot.quadTo(cx - 5, cy + 75, cx - 14, cy + 75)
            left_boot.quadTo(cx - 22, cy + 75, cx - 22, cy + 68)
            left_boot.lineTo(cx - 20, cy + 52)
            painter.drawPath(left_boot)
            # Right boot
            right_boot = QtGui.QPainterPath()
            right_boot.moveTo(cx + 2, cy + 52)
            right_boot.lineTo(cx + 20, cy + 52)
            right_boot.lineTo(cx + 22, cy + 68)
            right_boot.quadTo(cx + 22, cy + 75, cx + 14, cy + 75)
            right_boot.quadTo(cx + 5, cy + 75, cx + 2, cy + 68)
            right_boot.lineTo(cx + 2, cy + 52)
            painter.drawPath(right_boot)
            # Boot cuffs
            painter.setBrush(bc.darker(115))
            painter.drawRect(cx - 21, cy + 52, 20, 6)
            painter.drawRect(cx + 1, cy + 52, 20, 6)
            # Boot buckles
            painter.setBrush(QtGui.QColor("#b8860b"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#8b6914"), 1))
            painter.drawRect(cx - 14, cy + 60, 6, 4)
            painter.drawRect(cx + 8, cy + 60, 6, 4)
            # Boot shine
            painter.setPen(QtGui.QPen(bc.lighter(140), 1))
            painter.drawLine(cx - 16, cy + 56, cx - 8, cy + 56)
            painter.drawLine(cx + 6, cy + 56, cx + 14, cy + 56)
        else:
            # Bare feet with toes
            painter.setBrush(QtGui.QColor("#e6b980"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#c9a066"), 1))
            # Left foot
            painter.drawRoundedRect(cx - 18, cy + 55, 14, 18, 4, 4)
            # Right foot
            painter.drawRoundedRect(cx + 4, cy + 55, 14, 18, 4, 4)
            # Toes
            painter.setBrush(QtGui.QColor("#dba870"))
            for i in range(3):
                painter.drawEllipse(cx - 17 + i * 4, cy + 70, 3, 4)
                painter.drawEllipse(cx + 5 + i * 4, cy + 70, 3, 4)

        # === ARMS with muscle shading ===
        # Left arm gradient
        arm_grad_l = QtGui.QLinearGradient(cx - 42, cy - 5, cx - 28, cy - 5)
        arm_grad_l.setColorAt(0, body_color.darker(125))
        arm_grad_l.setColorAt(0.4, body_color)
        arm_grad_l.setColorAt(1, body_color.darker(110))
        painter.setBrush(arm_grad_l)
        painter.setPen(QtGui.QPen(body_outline, 2))
        arm_path_l = QtGui.QPainterPath()
        arm_path_l.moveTo(cx - 28, cy - 24)
        arm_path_l.quadTo(cx - 36, cy - 26, cx - 40, cy - 20)
        arm_path_l.quadTo(cx - 45, cy, cx - 44, cy + 18)
        arm_path_l.lineTo(cx - 28, cy + 15)
        arm_path_l.quadTo(cx - 27, cy - 5, cx - 28, cy - 24)
        painter.drawPath(arm_path_l)
        # Right arm
        arm_grad_r = QtGui.QLinearGradient(cx + 28, cy - 5, cx + 42, cy - 5)
        arm_grad_r.setColorAt(0, body_color.darker(110))
        arm_grad_r.setColorAt(0.6, body_color)
        arm_grad_r.setColorAt(1, body_color.darker(125))
        painter.setBrush(arm_grad_r)
        arm_path_r = QtGui.QPainterPath()
        arm_path_r.moveTo(cx + 28, cy - 24)
        arm_path_r.quadTo(cx + 36, cy - 26, cx + 40, cy - 20)
        arm_path_r.quadTo(cx + 45, cy, cx + 44, cy + 18)
        arm_path_r.lineTo(cx + 28, cy + 15)
        arm_path_r.quadTo(cx + 27, cy - 5, cx + 28, cy - 24)
        painter.drawPath(arm_path_r)

        # === GAUNTLETS ===
        gaunt = self.equipped.get("Gauntlets")
        if gaunt:
            gc = QtGui.QColor(gaunt.get("color", "#666"))
            # Gauntlet gradient
            gaunt_grad = QtGui.QLinearGradient(0, cy + 8, 0, cy + 30)
            gaunt_grad.setColorAt(0, gc.lighter(115))
            gaunt_grad.setColorAt(0.5, gc)
            gaunt_grad.setColorAt(1, gc.darker(120))
            painter.setBrush(gaunt_grad)
            painter.setPen(QtGui.QPen(gc.darker(140), 2))
            # Left gauntlet with armor plates
            painter.drawRoundedRect(cx - 48, cy + 6, 24, 26, 5, 5)
            # Armor plate lines
            painter.setPen(QtGui.QPen(gc.darker(150), 1))
            painter.drawLine(cx - 46, cy + 12, cx - 26, cy + 12)
            painter.drawLine(cx - 46, cy + 18, cx - 26, cy + 18)
            # Knuckle spikes for epic+ tiers
            if self.tier in ["epic", "legendary", "godlike"]:
                painter.setBrush(gc.darker(130))
                painter.setPen(QtGui.QPen(gc.darker(150), 1))
                for i in range(3):
                    spike = QtGui.QPainterPath()
                    spike.moveTo(cx - 44 + i * 7, cy + 24)
                    spike.lineTo(cx - 41 + i * 7, cy + 32)
                    spike.lineTo(cx - 38 + i * 7, cy + 24)
                    painter.drawPath(spike)
            # Right gauntlet
            painter.setBrush(gaunt_grad)
            painter.setPen(QtGui.QPen(gc.darker(140), 2))
            painter.drawRoundedRect(cx + 24, cy + 6, 24, 26, 5, 5)
            painter.setPen(QtGui.QPen(gc.darker(150), 1))
            painter.drawLine(cx + 26, cy + 12, cx + 46, cy + 12)
            painter.drawLine(cx + 26, cy + 18, cx + 46, cy + 18)
            if self.tier in ["epic", "legendary", "godlike"]:
                painter.setBrush(gc.darker(130))
                for i in range(3):
                    spike = QtGui.QPainterPath()
                    spike.moveTo(cx + 26 + i * 7, cy + 24)
                    spike.lineTo(cx + 29 + i * 7, cy + 32)
                    spike.lineTo(cx + 32 + i * 7, cy + 24)
                    painter.drawPath(spike)
        else:
            # Detailed hands
            painter.setBrush(QtGui.QColor("#ffcc80"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#e6a84d"), 1))
            # Left hand
            painter.drawEllipse(cx - 46, cy + 12, 16, 16)
            # Fingers
            painter.setBrush(QtGui.QColor("#f5c07a"))
            for i in range(4):
                painter.drawEllipse(cx - 46 + i * 4, cy + 24, 3, 6)
            # Right hand
            painter.setBrush(QtGui.QColor("#ffcc80"))
            painter.drawEllipse(cx + 30, cy + 12, 16, 16)
            painter.setBrush(QtGui.QColor("#f5c07a"))
            for i in range(4):
                painter.drawEllipse(cx + 31 + i * 4, cy + 24, 3, 6)

        # === TORSO with shading ===
        torso_grad = QtGui.QLinearGradient(cx - 25, cy, cx + 25, cy)
        torso_grad.setColorAt(0, body_color.darker(115))
        torso_grad.setColorAt(0.3, body_color)
        torso_grad.setColorAt(0.7, body_color)
        torso_grad.setColorAt(1, body_color.darker(115))
        painter.setBrush(torso_grad)
        painter.setPen(QtGui.QPen(body_outline, 2))
        torso_path = QtGui.QPainterPath()
        torso_path.moveTo(cx - 26, cy - 28)
        torso_path.quadTo(cx - 28, cy - 5, cx - 23, cy + 25)
        torso_path.lineTo(cx + 23, cy + 25)
        torso_path.quadTo(cx + 28, cy - 5, cx + 26, cy - 28)
        torso_path.closeSubpath()
        painter.drawPath(torso_path)

        # === CHESTPLATE ===
        chest = self.equipped.get("Chestplate")
        if chest:
            cc = QtGui.QColor(chest.get("color", "#666"))
            # Chestplate gradient for metallic look
            chest_grad = QtGui.QLinearGradient(cx - 22, cy, cx + 22, cy)
            chest_grad.setColorAt(0, cc.darker(130))
            chest_grad.setColorAt(0.2, cc.lighter(110))
            chest_grad.setColorAt(0.5, cc)
            chest_grad.setColorAt(0.8, cc.lighter(110))
            chest_grad.setColorAt(1, cc.darker(130))
            painter.setBrush(chest_grad)
            painter.setPen(QtGui.QPen(cc.darker(140), 2))
            # Main plate with curves
            chest_path = QtGui.QPainterPath()
            chest_path.moveTo(cx - 23, cy - 26)
            chest_path.quadTo(cx, cy - 30, cx + 23, cy - 26)
            chest_path.quadTo(cx + 25, cy, cx + 20, cy + 20)
            chest_path.lineTo(cx - 20, cy + 20)
            chest_path.quadTo(cx - 25, cy, cx - 23, cy - 26)
            painter.drawPath(chest_path)
            # Chest muscle definition lines
            painter.setPen(QtGui.QPen(cc.darker(140), 1))
            painter.drawArc(cx - 15, cy - 18, 14, 12, 30 * 16, 120 * 16)
            painter.drawArc(cx + 1, cy - 18, 14, 12, 30 * 16, 120 * 16)
            # Abs definition for high tiers
            if self.tier in ["heroic", "epic", "legendary", "godlike"]:
                painter.drawLine(cx, cy - 5, cx, cy + 15)
                painter.drawLine(cx - 12, cy, cx + 12, cy)
                painter.drawLine(cx - 10, cy + 10, cx + 10, cy + 10)
            # Shoulder pads with rivets
            painter.setBrush(cc.darker(110))
            painter.setPen(QtGui.QPen(cc.darker(145), 1))
            # Left shoulder
            shoulder_l = QtGui.QPainterPath()
            shoulder_l.moveTo(cx - 26, cy - 26)
            shoulder_l.quadTo(cx - 35, cy - 28, cx - 38, cy - 20)
            shoulder_l.lineTo(cx - 28, cy - 18)
            shoulder_l.closeSubpath()
            painter.drawPath(shoulder_l)
            # Right shoulder
            shoulder_r = QtGui.QPainterPath()
            shoulder_r.moveTo(cx + 26, cy - 26)
            shoulder_r.quadTo(cx + 35, cy - 28, cx + 38, cy - 20)
            shoulder_r.lineTo(cx + 28, cy - 18)
            shoulder_r.closeSubpath()
            painter.drawPath(shoulder_r)
            # Rivets on shoulders
            painter.setBrush(cc.lighter(130))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 32, cy - 24, 4, 4)
            painter.drawEllipse(cx + 28, cy - 24, 4, 4)
            # Center emblem (gem or symbol)
            emblem_grad = QtGui.QRadialGradient(cx, cy - 12, 8)
            emblem_grad.setColorAt(0, QtGui.QColor("#fff"))
            emblem_grad.setColorAt(0.3, cc.lighter(150))
            emblem_grad.setColorAt(1, cc.lighter(120))
            painter.setBrush(emblem_grad)
            painter.setPen(QtGui.QPen(cc.darker(130), 1))
            painter.drawEllipse(cx - 6, cy - 18, 12, 12)
        else:
            # Tunic/shirt details
            painter.setPen(QtGui.QPen(body_outline, 1))
            painter.drawLine(cx, cy - 25, cx, cy + 18)
            # Collar
            painter.drawLine(cx - 10, cy - 26, cx, cy - 20)
            painter.drawLine(cx + 10, cy - 26, cx, cy - 20)
        
        # === BELT (always visible) ===
        belt_color = QtGui.QColor("#5d4037") if not chest else chest.get("color", "#666")
        belt_c = QtGui.QColor(belt_color) if isinstance(belt_color, str) else belt_color
        painter.setBrush(belt_c.darker(140) if chest else QtGui.QColor("#4e342e"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#3e2723"), 1))
        painter.drawRect(cx - 21, cy + 18, 42, 7)
        # Belt buckle
        painter.setBrush(QtGui.QColor("#b8860b"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#8b6914"), 1))
        painter.drawRect(cx - 5, cy + 17, 10, 9)
        # Buckle detail
        painter.setPen(QtGui.QPen(QtGui.QColor("#daa520"), 1))
        painter.drawRect(cx - 3, cy + 19, 6, 5)

        # === HEAD ===
        # Neck with shading
        neck_grad = QtGui.QLinearGradient(cx - 8, cy - 35, cx + 8, cy - 35)
        neck_grad.setColorAt(0, QtGui.QColor("#e6b980"))
        neck_grad.setColorAt(0.5, QtGui.QColor("#ffcc80"))
        neck_grad.setColorAt(1, QtGui.QColor("#e6b980"))
        painter.setBrush(neck_grad)
        painter.setPen(QtGui.QPen(QtGui.QColor("#d4943a"), 1))
        painter.drawRect(cx - 9, cy - 36, 18, 12)
        
        # Head shape with better gradient
        head_gradient = QtGui.QRadialGradient(cx - 5, cy - 55, 30)
        head_gradient.setColorAt(0, QtGui.QColor("#ffe8c8"))
        head_gradient.setColorAt(0.5, QtGui.QColor("#ffcc80"))
        head_gradient.setColorAt(0.8, QtGui.QColor("#e6a84d"))
        head_gradient.setColorAt(1, QtGui.QColor("#d4943a"))
        painter.setBrush(head_gradient)
        painter.setPen(QtGui.QPen(QtGui.QColor("#c9843a"), 2))
        # Slightly more defined head shape
        head_path = QtGui.QPainterPath()
        head_path.moveTo(cx - 2, cy - 32)
        head_path.quadTo(cx - 22, cy - 35, cx - 22, cy - 52)
        head_path.quadTo(cx - 22, cy - 72, cx, cy - 72)
        head_path.quadTo(cx + 22, cy - 72, cx + 22, cy - 52)
        head_path.quadTo(cx + 22, cy - 35, cx + 2, cy - 32)
        head_path.closeSubpath()
        painter.drawPath(head_path)

        # === HELMET (if equipped) ===
        helm = self.equipped.get("Helmet")
        if helm:
            hc = QtGui.QColor(helm.get("color", "#666"))
            # Helmet gradient for metallic
            helm_grad = QtGui.QLinearGradient(cx - 24, cy - 70, cx + 24, cy - 70)
            helm_grad.setColorAt(0, hc.darker(130))
            helm_grad.setColorAt(0.3, hc.lighter(115))
            helm_grad.setColorAt(0.5, hc)
            helm_grad.setColorAt(0.7, hc.lighter(115))
            helm_grad.setColorAt(1, hc.darker(130))
            painter.setBrush(helm_grad)
            painter.setPen(QtGui.QPen(hc.darker(140), 2))
            # Helmet dome with better shape
            helm_path = QtGui.QPainterPath()
            helm_path.moveTo(cx - 24, cy - 52)
            helm_path.quadTo(cx - 26, cy - 75, cx, cy - 80)
            helm_path.quadTo(cx + 26, cy - 75, cx + 24, cy - 52)
            helm_path.closeSubpath()
            painter.drawPath(helm_path)
            # Helmet rim/visor band
            painter.setBrush(hc.darker(115))
            painter.drawRect(cx - 24, cy - 56, 48, 10)
            # Center crest/ridge
            painter.setPen(QtGui.QPen(hc.darker(150), 3))
            painter.drawLine(cx, cy - 80, cx, cy - 48)
            # Side details
            painter.setPen(QtGui.QPen(hc.darker(140), 1))
            painter.drawLine(cx - 12, cy - 70, cx - 12, cy - 52)
            painter.drawLine(cx + 12, cy - 70, cx + 12, cy - 52)
            # Visor slit (eyes area)
            painter.setPen(QtGui.QPen(QtGui.QColor("#1a1a1a"), 3))
            painter.drawLine(cx - 14, cy - 52, cx + 14, cy - 52)
            # Helmet shine
            painter.setPen(QtGui.QPen(hc.lighter(150), 1))
            painter.drawLine(cx - 10, cy - 72, cx - 5, cy - 65)
            # Cheek guards
            painter.setBrush(hc.darker(110))
            painter.setPen(QtGui.QPen(hc.darker(140), 1))
            painter.drawRect(cx - 24, cy - 48, 8, 12)
            painter.drawRect(cx + 16, cy - 48, 8, 12)
            # Plume for epic+ tiers
            if self.tier in ["epic", "legendary", "godlike"]:
                plume_color = QtGui.QColor("#c62828") if self.tier == "epic" else QtGui.QColor("#ffd700")
                painter.setBrush(plume_color)
                painter.setPen(QtGui.QPen(plume_color.darker(130), 1))
                plume = QtGui.QPainterPath()
                plume.moveTo(cx - 3, cy - 80)
                plume.quadTo(cx - 8, cy - 95, cx, cy - 100)
                plume.quadTo(cx + 8, cy - 95, cx + 3, cy - 80)
                painter.drawPath(plume)
        else:
            # Hair on top of head (not covering forehead)
            hair_color = QtGui.QColor("#5d4037")
            hair_grad = QtGui.QRadialGradient(cx, cy - 68, 22)
            hair_grad.setColorAt(0, hair_color.lighter(120))
            hair_grad.setColorAt(0.6, hair_color)
            hair_grad.setColorAt(1, hair_color.darker(130))
            painter.setBrush(hair_grad)
            painter.setPen(QtCore.Qt.NoPen)
            # Hair volume - sits on top, doesn't cover forehead
            hair_path = QtGui.QPainterPath()
            hair_path.moveTo(cx - 20, cy - 60)  # Start at sides above ears
            hair_path.quadTo(cx - 24, cy - 68, cx - 18, cy - 74)  # Left side curve up
            hair_path.quadTo(cx - 8, cy - 80, cx, cy - 79)  # Top left to center peak
            hair_path.quadTo(cx + 8, cy - 80, cx + 18, cy - 74)  # Top right
            hair_path.quadTo(cx + 24, cy - 68, cx + 20, cy - 60)  # Right side down
            hair_path.closeSubpath()
            painter.drawPath(hair_path)
            # Hair texture lines on top
            painter.setPen(QtGui.QPen(QtGui.QColor("#4e342e"), 1))
            painter.drawLine(cx - 12, cy - 72, cx - 10, cy - 64)
            painter.drawLine(cx - 5, cy - 76, cx - 4, cy - 66)
            painter.drawLine(cx, cy - 78, cx, cy - 68)
            painter.drawLine(cx + 5, cy - 76, cx + 4, cy - 66)
            painter.drawLine(cx + 12, cy - 72, cx + 10, cy - 64)
            # Side hair tufts (above ears)
            painter.setBrush(hair_color)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 23, cy - 62, 6, 8)
            painter.drawEllipse(cx + 17, cy - 62, 6, 8)

        # === FACE (if no helmet visor) ===
        if not helm:
            # Eyebrows with expression
            painter.setPen(QtGui.QPen(QtGui.QColor("#4e342e"), 2))
            if self.tier in ["legendary", "godlike"]:
                # Confident raised brows
                painter.drawLine(cx - 13, cy - 60, cx - 5, cy - 58)
                painter.drawLine(cx + 5, cy - 58, cx + 13, cy - 60)
            elif self.tier in ["epic", "heroic"]:
                # Slightly furrowed determined
                painter.drawLine(cx - 13, cy - 58, cx - 5, cy - 59)
                painter.drawLine(cx + 5, cy - 59, cx + 13, cy - 58)
            else:
                # Normal
                painter.drawLine(cx - 12, cy - 58, cx - 5, cy - 57)
                painter.drawLine(cx + 5, cy - 57, cx + 12, cy - 58)
            
            # Eyes with more detail
            # Eye sockets (slight shadow)
            painter.setBrush(QtGui.QColor("#e8c090"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 13, cy - 56, 12, 10)
            painter.drawEllipse(cx + 1, cy - 56, 12, 10)
            # Eye whites
            painter.setBrush(QtGui.QColor("#fff"))
            painter.drawEllipse(cx - 12, cy - 55, 10, 9)
            painter.drawEllipse(cx + 2, cy - 55, 10, 9)
            # Iris (colored based on tier)
            iris_colors = {
                "pathetic": "#6b5b4f", "modest": "#5d7a5d", "decent": "#4a7a4a",
                "heroic": "#4a6a9a", "epic": "#7a4a8a", "legendary": "#8a6a2a", "godlike": "#9a7a1a"
            }
            iris_color = QtGui.QColor(iris_colors.get(self.tier, "#5a5a5a"))
            painter.setBrush(iris_color)
            painter.drawEllipse(cx - 9, cy - 53, 6, 6)
            painter.drawEllipse(cx + 4, cy - 53, 6, 6)
            # Pupils
            painter.setBrush(QtGui.QColor("#1a1a1a"))
            painter.drawEllipse(cx - 7, cy - 51, 3, 3)
            painter.drawEllipse(cx + 6, cy - 51, 3, 3)
            # Eye shine (multiple highlights)
            painter.setBrush(QtGui.QColor("#fff"))
            painter.drawEllipse(cx - 8, cy - 52, 2, 2)
            painter.drawEllipse(cx + 5, cy - 52, 2, 2)
            # Small secondary shine
            painter.setOpacity(0.6)
            painter.drawEllipse(cx - 5, cy - 49, 1, 1)
            painter.drawEllipse(cx + 8, cy - 49, 1, 1)
            painter.setOpacity(1.0)
            # Eyelashes (subtle)
            painter.setPen(QtGui.QPen(QtGui.QColor("#4e342e"), 1))
            painter.drawLine(cx - 12, cy - 54, cx - 14, cy - 55)
            painter.drawLine(cx + 12, cy - 54, cx + 14, cy - 55)

            # Nose with shadow
            painter.setPen(QtGui.QPen(QtGui.QColor("#d4943a"), 1))
            # Nose bridge
            painter.drawLine(cx, cy - 50, cx - 1, cy - 44)
            # Nostril hints
            painter.drawArc(cx - 4, cy - 44, 4, 3, 180 * 16, 180 * 16)
            painter.drawArc(cx, cy - 44, 4, 3, 180 * 16, 180 * 16)

            # Mouth/expression based on tier
            painter.setPen(QtGui.QPen(QtGui.QColor("#a05a3a"), 2))
            if self.tier in ["legendary", "godlike"]:
                # Big confident smile with teeth hint - moved up
                painter.drawArc(cx - 10, cy - 46, 20, 12, 200 * 16, 140 * 16)
                # Teeth
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QtGui.QColor("#fff"))
                painter.drawRect(cx - 6, cy - 40, 12, 3)
            elif self.tier in ["epic", "heroic"]:
                # Confident smirk - moved up
                painter.drawArc(cx - 9, cy - 44, 18, 8, 210 * 16, 120 * 16)
            elif self.tier in ["decent", "modest"]:
                # Slight smile - moved up
                painter.drawArc(cx - 7, cy - 42, 14, 5, 220 * 16, 100 * 16)
            else:
                # Neutral/determined line - moved up
                painter.drawLine(cx - 6, cy - 40, cx + 6, cy - 40)
            
            # Cheek blush for high tiers
            if self.tier in ["legendary", "godlike"]:
                painter.setBrush(QtGui.QColor(255, 150, 150, 40))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(cx - 18, cy - 48, 8, 5)
                painter.drawEllipse(cx + 10, cy - 48, 8, 5)

            # Ears - small and subtle, partially hidden by hair
            painter.setBrush(QtGui.QColor("#ffcc80"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#d4943a"), 1))
            # Left ear - small oval peeking out
            painter.drawEllipse(cx - 24, cy - 52, 5, 9)
            # Right ear
            painter.drawEllipse(cx + 19, cy - 52, 5, 9)
            # Inner ear shadow
            painter.setBrush(QtGui.QColor("#e6b070"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 23, cy - 50, 3, 5)
            painter.drawEllipse(cx + 20, cy - 50, 3, 5)

        # === AMULET ===
        amulet = self.equipped.get("Amulet")
        if amulet:
            ac = QtGui.QColor(amulet.get("color", "#666"))
            # Chain with links
            painter.setPen(QtGui.QPen(QtGui.QColor("#daa520"), 2))
            # Draw chain as small connected circles
            for i in range(4):
                painter.drawEllipse(cx - 12 + i * 3, cy - 28 + i * 2, 3, 3)
                painter.drawEllipse(cx + 9 - i * 3, cy - 28 + i * 2, 3, 3)
            # Amulet setting/frame
            painter.setBrush(QtGui.QColor("#b8860b"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#8b6914"), 2))
            # Ornate frame
            frame_path = QtGui.QPainterPath()
            frame_path.moveTo(cx, cy - 24)
            frame_path.lineTo(cx + 10, cy - 14)
            frame_path.lineTo(cx + 8, cy - 2)
            frame_path.lineTo(cx, cy + 2)
            frame_path.lineTo(cx - 8, cy - 2)
            frame_path.lineTo(cx - 10, cy - 14)
            frame_path.closeSubpath()
            painter.drawPath(frame_path)
            # Gem with gradient
            gem_grad = QtGui.QRadialGradient(cx - 2, cy - 14, 10)
            gem_grad.setColorAt(0, ac.lighter(150))
            gem_grad.setColorAt(0.5, ac)
            gem_grad.setColorAt(1, ac.darker(130))
            painter.setBrush(gem_grad)
            painter.setPen(QtGui.QPen(ac.darker(140), 1))
            # Inner gem
            gem_path = QtGui.QPainterPath()
            gem_path.moveTo(cx, cy - 20)
            gem_path.lineTo(cx + 7, cy - 12)
            gem_path.lineTo(cx + 5, cy - 2)
            gem_path.lineTo(cx, cy)
            gem_path.lineTo(cx - 5, cy - 2)
            gem_path.lineTo(cx - 7, cy - 12)
            gem_path.closeSubpath()
            painter.drawPath(gem_path)
            # Gem shine/sparkle
            painter.setBrush(QtGui.QColor(255, 255, 255, 180))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 4, cy - 18, 5, 5)
            # Small sparkle
            painter.setBrush(QtGui.QColor(255, 255, 255, 120))
            painter.drawEllipse(cx + 2, cy - 8, 2, 2)
            # Magical glow for high tiers
            if self.tier in ["epic", "legendary", "godlike"]:
                painter.setOpacity(0.3)
                painter.setBrush(ac.lighter(130))
                painter.drawEllipse(cx - 12, cy - 22, 24, 28)
                painter.setOpacity(1.0)

        # === WEAPON ===
        weap = self.equipped.get("Weapon")
        if weap:
            wc = QtGui.QColor(weap.get("color", "#666"))
            # Sword handle with wrapping
            handle_grad = QtGui.QLinearGradient(cx - 56, cy, cx - 48, cy)
            handle_grad.setColorAt(0, QtGui.QColor("#4e342e"))
            handle_grad.setColorAt(0.5, QtGui.QColor("#6d4c41"))
            handle_grad.setColorAt(1, QtGui.QColor("#4e342e"))
            painter.setBrush(handle_grad)
            painter.setPen(QtGui.QPen(QtGui.QColor("#3e2723"), 1))
            painter.drawRoundedRect(cx - 56, cy - 2, 8, 38, 2, 2)
            # Handle leather wrap
            painter.setPen(QtGui.QPen(QtGui.QColor("#5d4037"), 2))
            for i in range(6):
                painter.drawLine(cx - 56, cy + 2 + i * 6, cx - 48, cy + 5 + i * 6)
            # Pommel (bottom)
            painter.setBrush(QtGui.QColor("#b8860b"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#8b6914"), 1))
            painter.drawEllipse(cx - 56, cy + 32, 8, 8)
            # Crossguard with curves
            guard_path = QtGui.QPainterPath()
            guard_path.moveTo(cx - 62, cy - 4)
            guard_path.quadTo(cx - 64, cy - 8, cx - 60, cy - 10)
            guard_path.lineTo(cx - 44, cy - 10)
            guard_path.quadTo(cx - 40, cy - 8, cx - 42, cy - 4)
            guard_path.lineTo(cx - 44, cy)
            guard_path.lineTo(cx - 60, cy)
            guard_path.closeSubpath()
            guard_grad = QtGui.QLinearGradient(cx - 62, cy - 10, cx - 42, cy - 10)
            guard_grad.setColorAt(0, QtGui.QColor("#c9a227"))
            guard_grad.setColorAt(0.5, QtGui.QColor("#daa520"))
            guard_grad.setColorAt(1, QtGui.QColor("#c9a227"))
            painter.setBrush(guard_grad)
            painter.setPen(QtGui.QPen(QtGui.QColor("#8b6914"), 1))
            painter.drawPath(guard_path)
            # Blade with gradient
            blade_grad = QtGui.QLinearGradient(cx - 58, cy - 10, cx - 46, cy - 10)
            blade_grad.setColorAt(0, wc.darker(120))
            blade_grad.setColorAt(0.3, wc.lighter(130))
            blade_grad.setColorAt(0.5, wc)
            blade_grad.setColorAt(0.7, wc.lighter(130))
            blade_grad.setColorAt(1, wc.darker(120))
            blade_path = QtGui.QPainterPath()
            blade_path.moveTo(cx - 58, cy - 10)
            blade_path.lineTo(cx - 46, cy - 10)
            blade_path.lineTo(cx - 52, cy - 60)
            blade_path.closeSubpath()
            painter.setBrush(blade_grad)
            painter.setPen(QtGui.QPen(wc.darker(140), 2))
            painter.drawPath(blade_path)
            # Blade edge highlight
            painter.setPen(QtGui.QPen(wc.lighter(160), 1))
            painter.drawLine(cx - 52, cy - 15, cx - 52, cy - 55)
            # Fuller (blood groove)
            painter.setPen(QtGui.QPen(wc.darker(140), 1))
            painter.drawLine(cx - 54, cy - 15, cx - 53, cy - 45)
            # Blade shine spots
            painter.setBrush(QtGui.QColor(255, 255, 255, 100))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 55, cy - 25, 4, 8)
            # Magical glow for legendary+
            if self.tier in ["legendary", "godlike"]:
                painter.setOpacity(0.3)
                painter.setBrush(wc.lighter(150))
                painter.drawEllipse(cx - 60, cy - 55, 20, 50)
                painter.setOpacity(1.0)

        # === SHIELD ===
        shield = self.equipped.get("Shield")
        if shield:
            sc = QtGui.QColor(shield.get("color", "#666"))
            # Shield gradient for 3D effect
            shield_grad = QtGui.QRadialGradient(cx + 45, cy + 5, 30)
            shield_grad.setColorAt(0, sc.lighter(120))
            shield_grad.setColorAt(0.5, sc)
            shield_grad.setColorAt(1, sc.darker(130))
            # Shield body (heater/kite shape)
            shield_path = QtGui.QPainterPath()
            shield_path.moveTo(cx + 50, cy - 22)
            shield_path.quadTo(cx + 72, cy - 18, cx + 70, cy + 8)
            shield_path.quadTo(cx + 68, cy + 28, cx + 50, cy + 40)
            shield_path.quadTo(cx + 32, cy + 28, cx + 30, cy + 8)
            shield_path.quadTo(cx + 28, cy - 18, cx + 50, cy - 22)
            painter.setBrush(shield_grad)
            painter.setPen(QtGui.QPen(sc.darker(150), 3))
            painter.drawPath(shield_path)
            # Shield rim (metallic border)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtGui.QPen(sc.darker(130), 4))
            painter.drawPath(shield_path)
            # Inner rim highlight
            painter.setPen(QtGui.QPen(sc.lighter(130), 1))
            inner_path = QtGui.QPainterPath()
            inner_path.moveTo(cx + 50, cy - 18)
            inner_path.quadTo(cx + 66, cy - 14, cx + 64, cy + 6)
            inner_path.quadTo(cx + 62, cy + 24, cx + 50, cy + 34)
            inner_path.quadTo(cx + 38, cy + 24, cx + 36, cy + 6)
            inner_path.quadTo(cx + 34, cy - 14, cx + 50, cy - 18)
            painter.drawPath(inner_path)
            # Shield emblem (stylized cross/pattern)
            painter.setPen(QtGui.QPen(sc.lighter(140), 3))
            painter.drawLine(cx + 50, cy - 12, cx + 50, cy + 28)
            painter.drawLine(cx + 38, cy + 8, cx + 62, cy + 8)
            # Decorative corners
            painter.setPen(QtGui.QPen(sc.lighter(130), 2))
            painter.drawLine(cx + 40, cy - 5, cx + 45, cy)
            painter.drawLine(cx + 60, cy - 5, cx + 55, cy)
            painter.drawLine(cx + 40, cy + 20, cx + 45, cy + 15)
            painter.drawLine(cx + 60, cy + 20, cx + 55, cy + 15)
            # Shield boss (center dome)
            boss_grad = QtGui.QRadialGradient(cx + 48, cy + 6, 10)
            boss_grad.setColorAt(0, sc.lighter(140))
            boss_grad.setColorAt(0.5, sc.darker(110))
            boss_grad.setColorAt(1, sc.darker(140))
            painter.setBrush(boss_grad)
            painter.setPen(QtGui.QPen(sc.darker(150), 1))
            painter.drawEllipse(cx + 43, cy + 1, 14, 14)
            # Boss highlight
            painter.setBrush(QtGui.QColor(255, 255, 255, 80))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx + 45, cy + 3, 5, 5)
            # Rivets around edge
            painter.setBrush(sc.darker(140))
            painter.setPen(QtGui.QPen(sc.darker(160), 1))
            rivet_positions = [(cx + 50, cy - 16), (cx + 62, cy - 8), (cx + 66, cy + 8),
                              (cx + 60, cy + 26), (cx + 50, cy + 34), (cx + 40, cy + 26),
                              (cx + 34, cy + 8), (cx + 38, cy - 8)]
            for rx, ry in rivet_positions:
                painter.drawEllipse(rx - 2, ry - 2, 4, 4)

        # === POWER LABEL ===
        # Background for label
        label_rect = QtCore.QRect(0, h - 28, w, 25)
        painter.fillRect(label_rect, QtGui.QColor(0, 0, 0, 100))
        
        # Power text with glow for high tiers
        if self.tier in ["legendary", "godlike"]:
            painter.setPen(QtGui.QColor("#ffd700"))
            # Glow effect
            painter.setOpacity(0.5)
            for offset in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                painter.drawText(label_rect.translated(offset[0], offset[1]), 
                               QtCore.Qt.AlignCenter, f"⚔ {self.power}")
            painter.setOpacity(1.0)
        elif self.tier in ["epic"]:
            painter.setPen(QtGui.QColor("#e040fb"))
        elif self.tier in ["heroic"]:
            painter.setPen(QtGui.QColor("#42a5f5"))
        else:
            painter.setPen(QtGui.QColor("#fff"))
        
        # Only draw final text for non-glowing tiers (glow loop already drew it)
        if self.tier not in ["legendary", "godlike"]:
            painter.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Bold))
            painter.drawText(label_rect, QtCore.Qt.AlignCenter, f"⚔ {self.power}")

    def _draw_scholar_character(self, event) -> None:
        """Draw the academic/scholar themed character."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2 + 5

        # Background with warm library gradient
        bg_gradient = QtGui.QRadialGradient(cx, cy - 20, max(w, h) * 0.8)
        bg_gradient.setColorAt(0, QtGui.QColor("#3d3529"))
        bg_gradient.setColorAt(0.5, QtGui.QColor("#2a2419"))
        bg_gradient.setColorAt(1, QtGui.QColor("#1a170f"))
        painter.fillRect(self.rect(), bg_gradient)
        
        # Floor/desk shadow
        floor_gradient = QtGui.QLinearGradient(cx - 40, cy + 70, cx + 40, cy + 85)
        floor_gradient.setColorAt(0, QtGui.QColor(0, 0, 0, 30))
        floor_gradient.setColorAt(0.5, QtGui.QColor(0, 0, 0, 80))
        floor_gradient.setColorAt(1, QtGui.QColor(0, 0, 0, 30))
        painter.setBrush(floor_gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(cx - 40, cy + 68, 80, 18)

        body_color = QtGui.QColor(self.TIER_COLORS.get(self.tier, "#bdbdbd"))
        body_outline = QtGui.QColor(self.TIER_OUTLINE.get(self.tier, "#888"))
        glow = self.TIER_GLOW.get(self.tier)

        def darken(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.darker(amount)
        
        def lighten(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.lighter(amount)

        # Knowledge aura for high tiers (book/scroll particles)
        if glow:
            glow_color = QtGui.QColor(glow)
            painter.setBrush(QtCore.Qt.NoBrush)
            for i, opacity in enumerate([0.1, 0.15, 0.25, 0.35]):
                painter.setOpacity(opacity)
                size = 140 - i * 15
                painter.setPen(QtGui.QPen(glow_color, 3))
                painter.drawEllipse(cx - size//2, cy - 70, size, int(size * 1.2))
            painter.setOpacity(1.0)
            painter.setBrush(glow_color)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setOpacity(0.25)
            painter.drawEllipse(cx - 50, cy - 60, 100, 130)
            painter.setOpacity(1.0)
        
        # Floating knowledge particles (quills, stars, runes)
        particles = self.TIER_PARTICLES.get(self.tier)
        if particles:
            p_color, p_count = particles
            painter.setBrush(QtGui.QColor(p_color))
            painter.setPen(QtCore.Qt.NoPen)
            for i, (px, py, ps) in enumerate(self._particles[:p_count]):
                painter.setOpacity(0.4 + (i % 3) * 0.2)
                # Draw small book/star shapes instead of circles
                if i % 2 == 0:
                    painter.drawRect(cx + px, cy + py, ps + 2, ps)  # Small book
                else:
                    painter.drawEllipse(cx + px, cy + py, ps, ps)  # Star
            painter.setOpacity(1.0)

        # === CLOAK/MANTLE (Academic Robe back) ===
        cloak = self.equipped.get("Cloak")
        if cloak:
            cc = QtGui.QColor(cloak.get("color", "#4a0080"))
            path = QtGui.QPainterPath()
            path.moveTo(cx - 24, cy - 28)
            path.lineTo(cx + 24, cy - 28)
            path.cubicTo(cx + 36, cy, cx + 38, cy + 40, cx + 32, cy + 72)
            path.quadTo(cx + 15, cy + 75, cx, cy + 73)
            path.quadTo(cx - 15, cy + 75, cx - 32, cy + 72)
            path.cubicTo(cx - 38, cy + 40, cx - 36, cy, cx - 24, cy - 28)
            cloak_gradient = QtGui.QLinearGradient(cx - 35, cy, cx + 35, cy)
            cloak_gradient.setColorAt(0, darken(cloak.get("color", "#4a0080"), 140))
            cloak_gradient.setColorAt(0.3, cc)
            cloak_gradient.setColorAt(0.7, cc)
            cloak_gradient.setColorAt(1, darken(cloak.get("color", "#4a0080"), 120))
            painter.setBrush(cloak_gradient)
            painter.setPen(QtGui.QPen(darken(cloak.get("color", "#4a0080"), 150), 2))
            painter.drawPath(path)
            # Robe folds
            painter.setPen(QtGui.QPen(darken(cloak.get("color", "#4a0080"), 160), 1))
            painter.drawLine(cx - 15, cy - 20, cx - 18, cy + 65)
            painter.drawLine(cx + 15, cy - 20, cx + 18, cy + 65)
            painter.drawLine(cx, cy - 15, cx, cy + 68)
            # Academic hood/collar
            painter.setBrush(QtGui.QColor("#f5f5dc"))  # Cream colored lining
            painter.setPen(QtGui.QPen(QtGui.QColor("#d4c8a0"), 1))
            hood_path = QtGui.QPainterPath()
            hood_path.moveTo(cx - 20, cy - 28)
            hood_path.quadTo(cx - 22, cy - 20, cx - 18, cy - 15)
            hood_path.lineTo(cx + 18, cy - 15)
            hood_path.quadTo(cx + 22, cy - 20, cx + 20, cy - 28)
            painter.drawPath(hood_path)

        # === LEGS (hidden by robe, just shoes visible) ===
        # Robe covers most of legs, draw minimal legs
        robe_grad = QtGui.QLinearGradient(cx - 25, cy + 25, cx + 25, cy + 25)
        chestplate = self.equipped.get("Chestplate")
        if chestplate and isinstance(chestplate, dict):
            robe_color = QtGui.QColor(chestplate.get("color", "#1a1a4a"))
        else:
            robe_color = QtGui.QColor("#1a1a4a")
        robe_grad.setColorAt(0, robe_color.darker(120))
        robe_grad.setColorAt(0.5, robe_color)
        robe_grad.setColorAt(1, robe_color.darker(120))
        painter.setBrush(robe_grad)
        painter.setPen(QtGui.QPen(robe_color.darker(150), 2))
        # Long robe bottom
        robe_path = QtGui.QPainterPath()
        robe_path.moveTo(cx - 23, cy + 20)
        robe_path.lineTo(cx + 23, cy + 20)
        robe_path.lineTo(cx + 28, cy + 65)
        robe_path.quadTo(cx, cy + 68, cx - 28, cy + 65)
        robe_path.closeSubpath()
        painter.drawPath(robe_path)

        # === BOOTS/FOOTWEAR (Scholar's shoes/slippers) ===
        boots = self.equipped.get("Boots")
        if boots:
            bc = QtGui.QColor(boots.get("color", "#4a3728"))
            boot_grad = QtGui.QLinearGradient(0, cy + 60, 0, cy + 75)
            boot_grad.setColorAt(0, bc.lighter(110))
            boot_grad.setColorAt(0.5, bc)
            boot_grad.setColorAt(1, bc.darker(120))
            painter.setBrush(boot_grad)
            painter.setPen(QtGui.QPen(bc.darker(140), 2))
            # Left shoe (oxford style)
            left_shoe = QtGui.QPainterPath()
            left_shoe.moveTo(cx - 18, cy + 60)
            left_shoe.lineTo(cx - 4, cy + 60)
            left_shoe.quadTo(cx - 2, cy + 68, cx - 6, cy + 72)
            left_shoe.quadTo(cx - 14, cy + 74, cx - 18, cy + 70)
            left_shoe.closeSubpath()
            painter.drawPath(left_shoe)
            # Right shoe
            right_shoe = QtGui.QPainterPath()
            right_shoe.moveTo(cx + 4, cy + 60)
            right_shoe.lineTo(cx + 18, cy + 60)
            right_shoe.lineTo(cx + 18, cy + 70)
            right_shoe.quadTo(cx + 14, cy + 74, cx + 6, cy + 72)
            right_shoe.quadTo(cx + 2, cy + 68, cx + 4, cy + 60)
            painter.drawPath(right_shoe)
            # Shoe laces
            painter.setPen(QtGui.QPen(bc.darker(150), 1))
            painter.drawLine(cx - 14, cy + 62, cx - 8, cy + 62)
            painter.drawLine(cx + 8, cy + 62, cx + 14, cy + 62)
        else:
            # Simple slippers
            painter.setBrush(QtGui.QColor("#5d4037"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#4e342e"), 1))
            painter.drawRoundedRect(cx - 16, cy + 62, 12, 10, 3, 3)
            painter.drawRoundedRect(cx + 4, cy + 62, 12, 10, 3, 3)

        # === ARMS (Robe sleeves) ===
        arm_color = robe_color if self.equipped.get("Chestplate") else QtGui.QColor("#1a1a4a")
        arm_grad_l = QtGui.QLinearGradient(cx - 42, cy - 5, cx - 28, cy - 5)
        arm_grad_l.setColorAt(0, arm_color.darker(125))
        arm_grad_l.setColorAt(0.4, arm_color)
        arm_grad_l.setColorAt(1, arm_color.darker(110))
        painter.setBrush(arm_grad_l)
        painter.setPen(QtGui.QPen(arm_color.darker(150), 2))
        # Wide robe sleeves
        arm_path_l = QtGui.QPainterPath()
        arm_path_l.moveTo(cx - 26, cy - 24)
        arm_path_l.quadTo(cx - 34, cy - 26, cx - 40, cy - 18)
        arm_path_l.quadTo(cx - 48, cy + 5, cx - 48, cy + 22)
        arm_path_l.lineTo(cx - 30, cy + 18)
        arm_path_l.quadTo(cx - 28, cy - 5, cx - 26, cy - 24)
        painter.drawPath(arm_path_l)
        # Right sleeve
        arm_grad_r = QtGui.QLinearGradient(cx + 28, cy - 5, cx + 42, cy - 5)
        arm_grad_r.setColorAt(0, arm_color.darker(110))
        arm_grad_r.setColorAt(0.6, arm_color)
        arm_grad_r.setColorAt(1, arm_color.darker(125))
        painter.setBrush(arm_grad_r)
        arm_path_r = QtGui.QPainterPath()
        arm_path_r.moveTo(cx + 26, cy - 24)
        arm_path_r.quadTo(cx + 34, cy - 26, cx + 40, cy - 18)
        arm_path_r.quadTo(cx + 48, cy + 5, cx + 48, cy + 22)
        arm_path_r.lineTo(cx + 30, cy + 18)
        arm_path_r.quadTo(cx + 28, cy - 5, cx + 26, cy - 24)
        painter.drawPath(arm_path_r)

        # === GAUNTLETS (Writing Gloves / Ink-stained Gloves) ===
        gaunt = self.equipped.get("Gauntlets")
        if gaunt:
            gc = QtGui.QColor(gaunt.get("color", "#f5f5dc"))
            gaunt_grad = QtGui.QLinearGradient(0, cy + 10, 0, cy + 28)
            gaunt_grad.setColorAt(0, gc.lighter(115))
            gaunt_grad.setColorAt(0.5, gc)
            gaunt_grad.setColorAt(1, gc.darker(110))
            painter.setBrush(gaunt_grad)
            painter.setPen(QtGui.QPen(gc.darker(130), 1))
            # Left glove - elegant writing glove
            painter.drawRoundedRect(cx - 48, cy + 12, 20, 20, 4, 4)
            # Ink stains for high tiers
            if self.tier in ["heroic", "epic", "legendary", "godlike"]:
                painter.setBrush(QtGui.QColor("#1a237e"))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(cx - 44, cy + 18, 4, 4)
                painter.drawEllipse(cx - 38, cy + 22, 3, 3)
            # Right glove
            painter.setBrush(gaunt_grad)
            painter.setPen(QtGui.QPen(gc.darker(130), 1))
            painter.drawRoundedRect(cx + 28, cy + 12, 20, 20, 4, 4)
            if self.tier in ["heroic", "epic", "legendary", "godlike"]:
                painter.setBrush(QtGui.QColor("#1a237e"))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(cx + 40, cy + 16, 3, 4)
        else:
            # Bare hands
            painter.setBrush(QtGui.QColor("#ffcc80"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#e6a84d"), 1))
            painter.drawEllipse(cx - 46, cy + 14, 14, 14)
            painter.drawEllipse(cx + 32, cy + 14, 14, 14)
            # Fingers
            painter.setBrush(QtGui.QColor("#f5c07a"))
            for i in range(4):
                painter.drawEllipse(cx - 46 + i * 3, cy + 25, 3, 5)
                painter.drawEllipse(cx + 32 + i * 3, cy + 25, 3, 5)

        # === TORSO/ROBE ===
        torso_grad = QtGui.QLinearGradient(cx - 25, cy, cx + 25, cy)
        torso_grad.setColorAt(0, robe_color.darker(115))
        torso_grad.setColorAt(0.3, robe_color)
        torso_grad.setColorAt(0.7, robe_color)
        torso_grad.setColorAt(1, robe_color.darker(115))
        painter.setBrush(torso_grad)
        painter.setPen(QtGui.QPen(robe_color.darker(150), 2))
        torso_path = QtGui.QPainterPath()
        torso_path.moveTo(cx - 26, cy - 28)
        torso_path.quadTo(cx - 28, cy - 5, cx - 23, cy + 25)
        torso_path.lineTo(cx + 23, cy + 25)
        torso_path.quadTo(cx + 28, cy - 5, cx + 26, cy - 28)
        torso_path.closeSubpath()
        painter.drawPath(torso_path)

        # === CHESTPLATE (Academic Vest/Cardigan) ===
        chest = self.equipped.get("Chestplate")
        if chest:
            cc = QtGui.QColor(chest.get("color", "#2d2d5a"))
            chest_grad = QtGui.QLinearGradient(cx - 20, cy, cx + 20, cy)
            chest_grad.setColorAt(0, cc.darker(120))
            chest_grad.setColorAt(0.3, cc)
            chest_grad.setColorAt(0.7, cc)
            chest_grad.setColorAt(1, cc.darker(120))
            painter.setBrush(chest_grad)
            painter.setPen(QtGui.QPen(cc.darker(140), 2))
            # Vest/cardigan shape
            vest_path = QtGui.QPainterPath()
            vest_path.moveTo(cx - 22, cy - 26)
            vest_path.lineTo(cx + 22, cy - 26)
            vest_path.lineTo(cx + 18, cy + 18)
            vest_path.lineTo(cx - 18, cy + 18)
            vest_path.closeSubpath()
            painter.drawPath(vest_path)
            # Center buttons
            painter.setBrush(QtGui.QColor("#b8860b"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#8b6914"), 1))
            for i in range(4):
                painter.drawEllipse(cx - 2, cy - 20 + i * 10, 4, 4)
            # Lapels
            painter.setPen(QtGui.QPen(cc.darker(150), 2))
            painter.drawLine(cx - 8, cy - 24, cx - 12, cy + 10)
            painter.drawLine(cx + 8, cy - 24, cx + 12, cy + 10)
            # Pocket with handkerchief for high tiers
            if self.tier in ["epic", "legendary", "godlike"]:
                painter.setBrush(QtGui.QColor("#fff"))
                painter.setPen(QtGui.QPen(QtGui.QColor("#ddd"), 1))
                pocket_path = QtGui.QPainterPath()
                pocket_path.moveTo(cx + 8, cy - 8)
                pocket_path.lineTo(cx + 16, cy - 10)
                pocket_path.lineTo(cx + 14, cy - 2)
                pocket_path.lineTo(cx + 10, cy)
                pocket_path.closeSubpath()
                painter.drawPath(pocket_path)
        else:
            # Simple robe lines
            painter.setPen(QtGui.QPen(robe_color.darker(140), 1))
            painter.drawLine(cx, cy - 25, cx, cy + 18)
            painter.drawLine(cx - 10, cy - 26, cx, cy - 20)
            painter.drawLine(cx + 10, cy - 26, cx, cy - 20)

        # === NECK ===
        neck_grad = QtGui.QLinearGradient(cx - 8, cy - 35, cx + 8, cy - 35)
        neck_grad.setColorAt(0, QtGui.QColor("#e6b980"))
        neck_grad.setColorAt(0.5, QtGui.QColor("#ffcc80"))
        neck_grad.setColorAt(1, QtGui.QColor("#e6b980"))
        painter.setBrush(neck_grad)
        painter.setPen(QtGui.QPen(QtGui.QColor("#d4943a"), 1))
        painter.drawRect(cx - 9, cy - 36, 18, 12)

        # === HEAD ===
        head_gradient = QtGui.QRadialGradient(cx - 5, cy - 55, 30)
        head_gradient.setColorAt(0, QtGui.QColor("#ffe8c8"))
        head_gradient.setColorAt(0.5, QtGui.QColor("#ffcc80"))
        head_gradient.setColorAt(0.8, QtGui.QColor("#e6a84d"))
        head_gradient.setColorAt(1, QtGui.QColor("#d4943a"))
        painter.setBrush(head_gradient)
        painter.setPen(QtGui.QPen(QtGui.QColor("#c9843a"), 2))
        head_path = QtGui.QPainterPath()
        head_path.moveTo(cx - 2, cy - 32)
        head_path.quadTo(cx - 22, cy - 35, cx - 22, cy - 52)
        head_path.quadTo(cx - 22, cy - 72, cx, cy - 72)
        head_path.quadTo(cx + 22, cy - 72, cx + 22, cy - 52)
        head_path.quadTo(cx + 22, cy - 35, cx + 2, cy - 32)
        head_path.closeSubpath()
        painter.drawPath(head_path)

        # === HELMET (Thinking Cap / Mortarboard / Glasses) ===
        helm = self.equipped.get("Helmet")
        if helm:
            hc = QtGui.QColor(helm.get("color", "#1a1a4a"))
            # Mortarboard cap
            # Cap base
            painter.setBrush(hc)
            painter.setPen(QtGui.QPen(hc.darker(140), 2))
            painter.drawEllipse(cx - 18, cy - 70, 36, 12)
            # Flat top board
            board_path = QtGui.QPainterPath()
            board_path.moveTo(cx - 24, cy - 78)
            board_path.lineTo(cx + 24, cy - 78)
            board_path.lineTo(cx + 28, cy - 72)
            board_path.lineTo(cx - 28, cy - 72)
            board_path.closeSubpath()
            painter.setBrush(hc)
            painter.drawPath(board_path)
            # Tassel
            painter.setPen(QtGui.QPen(QtGui.QColor("#ffd700"), 2))
            painter.drawLine(cx + 20, cy - 76, cx + 28, cy - 62)
            # Tassel end
            painter.setBrush(QtGui.QColor("#ffd700"))
            painter.setPen(QtCore.Qt.NoPen)
            for i in range(5):
                painter.drawLine(cx + 28 - i, cy - 62, cx + 26 - i, cy - 54)
        else:
            # Hair
            hair_color = QtGui.QColor("#5d4037")
            hair_grad = QtGui.QRadialGradient(cx, cy - 68, 22)
            hair_grad.setColorAt(0, hair_color.lighter(120))
            hair_grad.setColorAt(0.6, hair_color)
            hair_grad.setColorAt(1, hair_color.darker(130))
            painter.setBrush(hair_grad)
            painter.setPen(QtCore.Qt.NoPen)
            hair_path = QtGui.QPainterPath()
            hair_path.moveTo(cx - 20, cy - 60)
            hair_path.quadTo(cx - 24, cy - 68, cx - 18, cy - 74)
            hair_path.quadTo(cx - 8, cy - 80, cx, cy - 79)
            hair_path.quadTo(cx + 8, cy - 80, cx + 18, cy - 74)
            hair_path.quadTo(cx + 24, cy - 68, cx + 20, cy - 60)
            hair_path.closeSubpath()
            painter.drawPath(hair_path)
            # Hair texture
            painter.setPen(QtGui.QPen(QtGui.QColor("#4e342e"), 1))
            painter.drawLine(cx - 12, cy - 72, cx - 10, cy - 64)
            painter.drawLine(cx, cy - 78, cx, cy - 68)
            painter.drawLine(cx + 12, cy - 72, cx + 10, cy - 64)
            # Side tufts
            painter.setBrush(hair_color)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 23, cy - 62, 6, 8)
            painter.drawEllipse(cx + 17, cy - 62, 6, 8)

        # === FACE ===
        # Eyebrows (scholarly, thoughtful)
        painter.setPen(QtGui.QPen(QtGui.QColor("#4e342e"), 2))
        if self.tier in ["legendary", "godlike"]:
            # Raised knowing brows
            painter.drawLine(cx - 13, cy - 60, cx - 5, cy - 57)
            painter.drawLine(cx + 5, cy - 57, cx + 13, cy - 60)
        else:
            # Focused/thinking
            painter.drawLine(cx - 12, cy - 58, cx - 5, cy - 59)
            painter.drawLine(cx + 5, cy - 59, cx + 12, cy - 58)
        
        # Eyes
        painter.setBrush(QtGui.QColor("#e8c090"))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(cx - 13, cy - 56, 12, 10)
        painter.drawEllipse(cx + 1, cy - 56, 12, 10)
        painter.setBrush(QtGui.QColor("#fff"))
        painter.drawEllipse(cx - 12, cy - 55, 10, 9)
        painter.drawEllipse(cx + 2, cy - 55, 10, 9)
        # Iris
        iris_colors = {
            "pathetic": "#6b5b4f", "modest": "#4a5a6f", "decent": "#3a5a7a",
            "heroic": "#2a4a7a", "epic": "#5a3a7a", "legendary": "#7a5a2a", "godlike": "#4a6a3a"
        }
        iris_color = QtGui.QColor(iris_colors.get(self.tier, "#5a5a5a"))
        painter.setBrush(iris_color)
        painter.drawEllipse(cx - 9, cy - 53, 6, 6)
        painter.drawEllipse(cx + 4, cy - 53, 6, 6)
        painter.setBrush(QtGui.QColor("#1a1a1a"))
        painter.drawEllipse(cx - 7, cy - 51, 3, 3)
        painter.drawEllipse(cx + 6, cy - 51, 3, 3)
        # Eye shine
        painter.setBrush(QtGui.QColor("#fff"))
        painter.drawEllipse(cx - 8, cy - 52, 2, 2)
        painter.drawEllipse(cx + 5, cy - 52, 2, 2)

        # Glasses (always for scholars, even without helmet)
        painter.setBrush(QtCore.Qt.NoBrush)
        glasses_color = QtGui.QColor("#8b7355") if not helm else QtGui.QColor(helm.get("color", "#8b7355")).darker(110)
        painter.setPen(QtGui.QPen(glasses_color, 2))
        # Left lens (round)
        painter.drawEllipse(cx - 15, cy - 57, 14, 12)
        # Right lens
        painter.drawEllipse(cx + 1, cy - 57, 14, 12)
        # Bridge
        painter.drawLine(cx - 1, cy - 52, cx + 1, cy - 52)
        # Temple arms
        painter.drawLine(cx - 15, cy - 52, cx - 22, cy - 54)
        painter.drawLine(cx + 15, cy - 52, cx + 22, cy - 54)
        # Lens shine
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 80), 1))
        painter.drawArc(cx - 13, cy - 55, 8, 6, 45 * 16, 90 * 16)
        painter.drawArc(cx + 3, cy - 55, 8, 6, 45 * 16, 90 * 16)

        # Nose
        painter.setPen(QtGui.QPen(QtGui.QColor("#d4943a"), 1))
        painter.drawLine(cx, cy - 48, cx - 1, cy - 42)
        painter.drawArc(cx - 4, cy - 42, 4, 3, 180 * 16, 180 * 16)
        painter.drawArc(cx, cy - 42, 4, 3, 180 * 16, 180 * 16)

        # Mouth (scholarly expressions)
        painter.setPen(QtGui.QPen(QtGui.QColor("#a05a3a"), 2))
        if self.tier in ["legendary", "godlike"]:
            # Wise knowing smile
            painter.drawArc(cx - 8, cy - 44, 16, 10, 210 * 16, 120 * 16)
        elif self.tier in ["epic", "heroic"]:
            # Slight satisfied smile
            painter.drawArc(cx - 7, cy - 42, 14, 6, 220 * 16, 100 * 16)
        else:
            # Focused/neutral
            painter.drawLine(cx - 5, cy - 38, cx + 5, cy - 38)

        # Ears
        painter.setBrush(QtGui.QColor("#ffcc80"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#d4943a"), 1))
        painter.drawEllipse(cx - 24, cy - 52, 5, 9)
        painter.drawEllipse(cx + 19, cy - 52, 5, 9)

        # === AMULET (Scholar's Medal/Pocket Watch) ===
        amulet = self.equipped.get("Amulet")
        if amulet:
            ac = QtGui.QColor(amulet.get("color", "#4fc3f7"))
            # Chain
            painter.setPen(QtGui.QPen(QtGui.QColor("#b8860b"), 2))
            for i in range(3):
                painter.drawEllipse(cx - 10 + i * 3, cy - 26 + i * 3, 3, 3)
                painter.drawEllipse(cx + 7 - i * 3, cy - 26 + i * 3, 3, 3)
            # Medal/Pocket watch body
            painter.setBrush(QtGui.QColor("#daa520"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#b8860b"), 2))
            painter.drawEllipse(cx - 10, cy - 16, 20, 20)
            # Inner crystal/gem
            gem_grad = QtGui.QRadialGradient(cx - 2, cy - 8, 8)
            gem_grad.setColorAt(0, ac.lighter(150))
            gem_grad.setColorAt(0.5, ac)
            gem_grad.setColorAt(1, ac.darker(130))
            painter.setBrush(gem_grad)
            painter.setPen(QtGui.QPen(ac.darker(140), 1))
            painter.drawEllipse(cx - 7, cy - 13, 14, 14)
            # Watch hands / crystal facets
            if self.tier in ["epic", "legendary", "godlike"]:
                painter.setPen(QtGui.QPen(ac.lighter(170), 1))
                painter.drawLine(cx, cy - 10, cx, cy - 4)
                painter.drawLine(cx - 3, cy - 6, cx + 3, cy - 6)
            # Shine
            painter.setBrush(QtGui.QColor(255, 255, 255, 150))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 4, cy - 11, 4, 4)

        # === WEAPON (Quill/Fountain Pen/Pointer) ===
        weap = self.equipped.get("Weapon")
        if weap:
            wc = QtGui.QColor(weap.get("color", "#1a237e"))
            # Quill pen
            # Feather body
            feather_path = QtGui.QPainterPath()
            feather_path.moveTo(cx - 58, cy + 25)
            feather_path.quadTo(cx - 65, cy - 5, cx - 55, cy - 45)
            feather_path.quadTo(cx - 50, cy - 55, cx - 48, cy - 60)
            feather_path.quadTo(cx - 52, cy - 50, cx - 52, cy - 40)
            feather_path.quadTo(cx - 55, cy - 5, cx - 48, cy + 25)
            feather_path.closeSubpath()
            feather_grad = QtGui.QLinearGradient(cx - 60, cy - 30, cx - 48, cy - 30)
            feather_grad.setColorAt(0, wc.lighter(130))
            feather_grad.setColorAt(0.5, wc)
            feather_grad.setColorAt(1, wc.darker(110))
            painter.setBrush(feather_grad)
            painter.setPen(QtGui.QPen(wc.darker(140), 1))
            painter.drawPath(feather_path)
            # Feather barbs/details
            painter.setPen(QtGui.QPen(wc.darker(130), 1))
            for i in range(6):
                y_pos = cy - 45 + i * 10
                painter.drawLine(cx - 56, y_pos, cx - 50, y_pos - 3)
            # Quill shaft
            painter.setPen(QtGui.QPen(QtGui.QColor("#f5f5dc"), 2))
            painter.drawLine(cx - 53, cy - 40, cx - 53, cy + 30)
            # Quill tip (nib)
            painter.setBrush(QtGui.QColor("#b8860b"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#8b6914"), 1))
            nib_path = QtGui.QPainterPath()
            nib_path.moveTo(cx - 55, cy + 25)
            nib_path.lineTo(cx - 53, cy + 38)
            nib_path.lineTo(cx - 51, cy + 25)
            nib_path.closeSubpath()
            painter.drawPath(nib_path)
            # Ink drip for high tiers
            if self.tier in ["legendary", "godlike"]:
                painter.setBrush(QtGui.QColor("#1a237e"))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(cx - 55, cy + 36, 4, 6)

        # === SHIELD (Tome/Book/Encyclopedia) ===
        shield = self.equipped.get("Shield")
        if shield:
            sc = QtGui.QColor(shield.get("color", "#8d6e63"))
            # Book body
            book_grad = QtGui.QRadialGradient(cx + 48, cy + 8, 25)
            book_grad.setColorAt(0, sc.lighter(115))
            book_grad.setColorAt(0.5, sc)
            book_grad.setColorAt(1, sc.darker(130))
            # Book cover
            book_path = QtGui.QPainterPath()
            book_path.moveTo(cx + 32, cy - 18)
            book_path.lineTo(cx + 68, cy - 18)
            book_path.lineTo(cx + 68, cy + 35)
            book_path.lineTo(cx + 32, cy + 35)
            book_path.closeSubpath()
            painter.setBrush(book_grad)
            painter.setPen(QtGui.QPen(sc.darker(150), 3))
            painter.drawPath(book_path)
            # Book spine
            painter.setBrush(sc.darker(120))
            painter.drawRect(cx + 30, cy - 18, 5, 53)
            # Pages (white edge)
            painter.setBrush(QtGui.QColor("#fffef0"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#e0dcc8"), 1))
            painter.drawRect(cx + 35, cy - 15, 30, 47)
            # Page lines
            painter.setPen(QtGui.QPen(QtGui.QColor("#ccc"), 1))
            for i in range(8):
                painter.drawLine(cx + 38, cy - 10 + i * 6, cx + 62, cy - 10 + i * 6)
            # Cover decoration
            painter.setPen(QtGui.QPen(QtGui.QColor("#daa520"), 2))
            painter.drawRect(cx + 40, cy - 12, 20, 25)
            # Mystical symbol for high tiers
            if self.tier in ["epic", "legendary", "godlike"]:
                painter.setBrush(QtGui.QColor("#daa520"))
                painter.setPen(QtCore.Qt.NoPen)
                # Star symbol
                painter.drawEllipse(cx + 47, cy - 3, 8, 8)
                painter.setPen(QtGui.QPen(QtGui.QColor("#daa520"), 2))
                painter.drawLine(cx + 51, cy - 8, cx + 51, cy + 10)
                painter.drawLine(cx + 44, cy + 1, cx + 58, cy + 1)
            # Bookmark ribbon
            painter.setPen(QtGui.QPen(QtGui.QColor("#c62828"), 2))
            painter.drawLine(cx + 55, cy - 18, cx + 58, cy + 38)

        # === POWER LABEL ===
        label_rect = QtCore.QRect(0, h - 28, w, 25)
        painter.fillRect(label_rect, QtGui.QColor(0, 0, 0, 100))
        
        if self.tier in ["legendary", "godlike"]:
            painter.setPen(QtGui.QColor("#ffd700"))
            painter.setOpacity(0.5)
            for offset in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                painter.drawText(label_rect.translated(offset[0], offset[1]), 
                               QtCore.Qt.AlignCenter, f"📚 {self.power}")
            painter.setOpacity(1.0)
        elif self.tier in ["epic"]:
            painter.setPen(QtGui.QColor("#e040fb"))
        elif self.tier in ["heroic"]:
            painter.setPen(QtGui.QColor("#42a5f5"))
        else:
            painter.setPen(QtGui.QColor("#fff"))
        
        # Only draw final text for non-glowing tiers (glow loop already drew it)
        if self.tier not in ["legendary", "godlike"]:
            painter.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Bold))
            painter.drawText(label_rect, QtCore.Qt.AlignCenter, f"📚 {self.power}")

    def _draw_wanderer_character(self, event) -> None:
        """Draw the mystical/dreamweaver themed character."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2 + 5

        # Background with mystical night sky gradient
        bg_gradient = QtGui.QRadialGradient(cx, cy - 40, max(w, h) * 0.9)
        bg_gradient.setColorAt(0, QtGui.QColor("#1a1a3a"))
        bg_gradient.setColorAt(0.4, QtGui.QColor("#0d0d2b"))
        bg_gradient.setColorAt(0.7, QtGui.QColor("#05051a"))
        bg_gradient.setColorAt(1, QtGui.QColor("#000010"))
        painter.fillRect(self.rect(), bg_gradient)
        
        # Tiny stars in background
        painter.setBrush(QtGui.QColor(255, 255, 255, 180))
        painter.setPen(QtCore.Qt.NoPen)
        import random
        rng = random.Random(self.power + 999)
        for _ in range(12):
            sx, sy = rng.randint(5, w-5), rng.randint(5, int(h * 0.7))
            painter.drawEllipse(sx, sy, 2, 2)
        
        # Floor/mist
        floor_gradient = QtGui.QLinearGradient(cx - 45, cy + 65, cx + 45, cy + 80)
        floor_gradient.setColorAt(0, QtGui.QColor(100, 100, 180, 20))
        floor_gradient.setColorAt(0.5, QtGui.QColor(150, 150, 220, 60))
        floor_gradient.setColorAt(1, QtGui.QColor(100, 100, 180, 20))
        painter.setBrush(floor_gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(cx - 45, cy + 65, 90, 20)

        body_color = QtGui.QColor(self.TIER_COLORS.get(self.tier, "#bdbdbd"))
        body_outline = QtGui.QColor(self.TIER_OUTLINE.get(self.tier, "#888"))
        glow = self.TIER_GLOW.get(self.tier)

        def darken(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.darker(amount)
        
        def lighten(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.lighter(amount)

        # Mystical aura for high tiers
        if glow:
            glow_color = QtGui.QColor(glow)
            painter.setBrush(QtCore.Qt.NoBrush)
            for i, opacity in enumerate([0.08, 0.12, 0.2, 0.3]):
                painter.setOpacity(opacity)
                size = 150 - i * 18
                painter.setPen(QtGui.QPen(glow_color, 2))
                painter.drawEllipse(cx - size//2, cy - 75, size, int(size * 1.2))
            painter.setOpacity(1.0)
            # Inner glow
            painter.setBrush(glow_color)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setOpacity(0.2)
            painter.drawEllipse(cx - 55, cy - 65, 110, 140)
            painter.setOpacity(1.0)
        
        # Floating star/moon particles
        particles = self.TIER_PARTICLES.get(self.tier)
        if particles:
            p_color, p_count = particles
            for i, (px, py, ps) in enumerate(self._particles[:p_count]):
                painter.setOpacity(0.5 + (i % 3) * 0.15)
                # Draw crescent moons and stars
                if i % 3 == 0:
                    # Star
                    painter.setBrush(QtGui.QColor(p_color))
                    painter.setPen(QtCore.Qt.NoPen)
                    star_path = QtGui.QPainterPath()
                    star_cx, star_cy = cx + px, cy + py
                    star_path.moveTo(star_cx, star_cy - ps)
                    star_path.lineTo(star_cx + ps//3, star_cy - ps//3)
                    star_path.lineTo(star_cx + ps, star_cy)
                    star_path.lineTo(star_cx + ps//3, star_cy + ps//3)
                    star_path.lineTo(star_cx, star_cy + ps)
                    star_path.lineTo(star_cx - ps//3, star_cy + ps//3)
                    star_path.lineTo(star_cx - ps, star_cy)
                    star_path.lineTo(star_cx - ps//3, star_cy - ps//3)
                    star_path.closeSubpath()
                    painter.drawPath(star_path)
                else:
                    # Moon crescent
                    painter.setBrush(QtGui.QColor(p_color))
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.drawEllipse(cx + px, cy + py, ps + 1, ps + 1)
            painter.setOpacity(1.0)

        # === CLOAK/SHROUD (Flowing star-cloth) ===
        cloak = self.equipped.get("Cloak")
        if cloak:
            cc = QtGui.QColor(cloak.get("color", "#1a1a4a"))
            path = QtGui.QPainterPath()
            path.moveTo(cx - 24, cy - 28)
            path.lineTo(cx + 24, cy - 28)
            path.cubicTo(cx + 40, cy + 5, cx + 45, cy + 45, cx + 38, cy + 75)
            path.quadTo(cx + 18, cy + 80, cx, cy + 78)
            path.quadTo(cx - 18, cy + 80, cx - 38, cy + 75)
            path.cubicTo(cx - 45, cy + 45, cx - 40, cy + 5, cx - 24, cy - 28)
            cloak_gradient = QtGui.QLinearGradient(cx, cy - 30, cx, cy + 75)
            cloak_gradient.setColorAt(0, cc.lighter(110))
            cloak_gradient.setColorAt(0.5, cc)
            cloak_gradient.setColorAt(1, darken(cloak.get("color", "#1a1a4a"), 130))
            painter.setBrush(cloak_gradient)
            painter.setPen(QtGui.QPen(darken(cloak.get("color", "#1a1a4a"), 150), 2))
            painter.drawPath(path)
            # Star pattern on cloak
            painter.setBrush(QtGui.QColor(255, 255, 200, 100))
            painter.setPen(QtCore.Qt.NoPen)
            cloak_stars = [(cx - 20, cy + 15), (cx + 15, cy + 25), (cx - 8, cy + 45),
                          (cx + 22, cy + 50), (cx - 25, cy + 60), (cx + 8, cy + 65)]
            for sx, sy in cloak_stars:
                painter.drawEllipse(sx, sy, 3, 3)
            # Cloak folds with shimmer
            painter.setPen(QtGui.QPen(cc.lighter(120), 1))
            painter.drawLine(cx - 18, cy - 15, cx - 25, cy + 70)
            painter.drawLine(cx + 18, cy - 15, cx + 25, cy + 70)
            painter.drawLine(cx, cy - 10, cx, cy + 72)

        # === LEGS (hidden by flowing robes) ===
        chestplate = self.equipped.get("Chestplate")
        if chestplate and isinstance(chestplate, dict):
            robe_color = QtGui.QColor(chestplate.get("color", "#2a2a5a"))
        else:
            robe_color = QtGui.QColor("#2a2a5a")
        robe_grad = QtGui.QLinearGradient(cx - 25, cy + 25, cx + 25, cy + 25)
        robe_grad.setColorAt(0, robe_color.darker(120))
        robe_grad.setColorAt(0.5, robe_color)
        robe_grad.setColorAt(1, robe_color.darker(120))
        painter.setBrush(robe_grad)
        painter.setPen(QtGui.QPen(robe_color.darker(150), 2))
        robe_path = QtGui.QPainterPath()
        robe_path.moveTo(cx - 22, cy + 22)
        robe_path.lineTo(cx + 22, cy + 22)
        robe_path.quadTo(cx + 28, cy + 50, cx + 25, cy + 68)
        robe_path.quadTo(cx, cy + 72, cx - 25, cy + 68)
        robe_path.quadTo(cx - 28, cy + 50, cx - 22, cy + 22)
        painter.drawPath(robe_path)

        # === BOOTS/TREADS (Cloud Walkers/Star Treads) ===
        boots = self.equipped.get("Boots")
        if boots:
            bc = QtGui.QColor(boots.get("color", "#3a3a6a"))
            boot_grad = QtGui.QLinearGradient(0, cy + 60, 0, cy + 78)
            boot_grad.setColorAt(0, bc.lighter(120))
            boot_grad.setColorAt(0.5, bc)
            boot_grad.setColorAt(1, bc.darker(120))
            painter.setBrush(boot_grad)
            painter.setPen(QtGui.QPen(bc.darker(140), 2))
            # Left boot - ethereal curved design
            left_boot = QtGui.QPainterPath()
            left_boot.moveTo(cx - 20, cy + 62)
            left_boot.quadTo(cx - 22, cy + 70, cx - 18, cy + 76)
            left_boot.quadTo(cx - 10, cy + 78, cx - 4, cy + 74)
            left_boot.lineTo(cx - 4, cy + 62)
            left_boot.closeSubpath()
            painter.drawPath(left_boot)
            # Right boot
            right_boot = QtGui.QPainterPath()
            right_boot.moveTo(cx + 4, cy + 62)
            right_boot.lineTo(cx + 4, cy + 74)
            right_boot.quadTo(cx + 10, cy + 78, cx + 18, cy + 76)
            right_boot.quadTo(cx + 22, cy + 70, cx + 20, cy + 62)
            right_boot.closeSubpath()
            painter.drawPath(right_boot)
            # Moon/star emblem on boots
            painter.setBrush(QtGui.QColor("#ffd700"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 14, cy + 66, 5, 5)
            painter.drawEllipse(cx + 9, cy + 66, 5, 5)
        else:
            # Bare feet with mystical glow
            painter.setBrush(QtGui.QColor("#e6c8a0"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#c9a066"), 1))
            painter.drawRoundedRect(cx - 16, cy + 62, 12, 14, 4, 4)
            painter.drawRoundedRect(cx + 4, cy + 62, 12, 14, 4, 4)

        # === ARMS (Flowing sleeves) ===
        arm_color = robe_color
        arm_grad_l = QtGui.QLinearGradient(cx - 44, cy - 5, cx - 28, cy - 5)
        arm_grad_l.setColorAt(0, arm_color.darker(125))
        arm_grad_l.setColorAt(0.4, arm_color)
        arm_grad_l.setColorAt(1, arm_color.darker(110))
        painter.setBrush(arm_grad_l)
        painter.setPen(QtGui.QPen(arm_color.darker(150), 2))
        # Wide flowing sleeves
        arm_path_l = QtGui.QPainterPath()
        arm_path_l.moveTo(cx - 26, cy - 24)
        arm_path_l.quadTo(cx - 36, cy - 26, cx - 42, cy - 16)
        arm_path_l.quadTo(cx - 52, cy + 8, cx - 50, cy + 25)
        arm_path_l.lineTo(cx - 30, cy + 20)
        arm_path_l.quadTo(cx - 28, cy - 5, cx - 26, cy - 24)
        painter.drawPath(arm_path_l)
        # Right sleeve
        arm_grad_r = QtGui.QLinearGradient(cx + 28, cy - 5, cx + 44, cy - 5)
        arm_grad_r.setColorAt(0, arm_color.darker(110))
        arm_grad_r.setColorAt(0.6, arm_color)
        arm_grad_r.setColorAt(1, arm_color.darker(125))
        painter.setBrush(arm_grad_r)
        arm_path_r = QtGui.QPainterPath()
        arm_path_r.moveTo(cx + 26, cy - 24)
        arm_path_r.quadTo(cx + 36, cy - 26, cx + 42, cy - 16)
        arm_path_r.quadTo(cx + 52, cy + 8, cx + 50, cy + 25)
        arm_path_r.lineTo(cx + 30, cy + 20)
        arm_path_r.quadTo(cx + 28, cy - 5, cx + 26, cy - 24)
        painter.drawPath(arm_path_r)

        # === GAUNTLETS (Arm Wraps / Dream Catchers) ===
        gaunt = self.equipped.get("Gauntlets")
        if gaunt:
            gc = QtGui.QColor(gaunt.get("color", "#4a4a8a"))
            gaunt_grad = QtGui.QLinearGradient(0, cy + 12, 0, cy + 32)
            gaunt_grad.setColorAt(0, gc.lighter(115))
            gaunt_grad.setColorAt(0.5, gc)
            gaunt_grad.setColorAt(1, gc.darker(110))
            painter.setBrush(gaunt_grad)
            painter.setPen(QtGui.QPen(gc.darker(130), 1))
            # Left arm wrap with bands
            painter.drawRoundedRect(cx - 50, cy + 14, 22, 18, 6, 6)
            # Wrap bands
            painter.setPen(QtGui.QPen(gc.lighter(130), 2))
            painter.drawLine(cx - 48, cy + 18, cx - 30, cy + 18)
            painter.drawLine(cx - 48, cy + 24, cx - 30, cy + 24)
            # Dream catcher circle for high tiers
            if self.tier in ["heroic", "epic", "legendary", "godlike"]:
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.setPen(QtGui.QPen(QtGui.QColor("#ffd700"), 1))
                painter.drawEllipse(cx - 44, cy + 28, 8, 8)
            # Right arm wrap
            painter.setBrush(gaunt_grad)
            painter.setPen(QtGui.QPen(gc.darker(130), 1))
            painter.drawRoundedRect(cx + 28, cy + 14, 22, 18, 6, 6)
            painter.setPen(QtGui.QPen(gc.lighter(130), 2))
            painter.drawLine(cx + 30, cy + 18, cx + 48, cy + 18)
            painter.drawLine(cx + 30, cy + 24, cx + 48, cy + 24)
            if self.tier in ["heroic", "epic", "legendary", "godlike"]:
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.setPen(QtGui.QPen(QtGui.QColor("#ffd700"), 1))
                painter.drawEllipse(cx + 36, cy + 28, 8, 8)
        else:
            # Bare hands with ethereal glow
            painter.setBrush(QtGui.QColor("#e6c8a0"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#c9a066"), 1))
            painter.drawEllipse(cx - 48, cy + 16, 14, 14)
            painter.drawEllipse(cx + 34, cy + 16, 14, 14)

        # === TORSO ===
        torso_grad = QtGui.QLinearGradient(cx - 25, cy, cx + 25, cy)
        torso_grad.setColorAt(0, robe_color.darker(115))
        torso_grad.setColorAt(0.3, robe_color)
        torso_grad.setColorAt(0.7, robe_color)
        torso_grad.setColorAt(1, robe_color.darker(115))
        painter.setBrush(torso_grad)
        painter.setPen(QtGui.QPen(robe_color.darker(150), 2))
        torso_path = QtGui.QPainterPath()
        torso_path.moveTo(cx - 26, cy - 28)
        torso_path.quadTo(cx - 28, cy - 5, cx - 22, cy + 25)
        torso_path.lineTo(cx + 22, cy + 25)
        torso_path.quadTo(cx + 28, cy - 5, cx + 26, cy - 28)
        torso_path.closeSubpath()
        painter.drawPath(torso_path)

        # === CHESTPLATE (Starweave Robe / Mooncloth Vest) ===
        chest = self.equipped.get("Chestplate")
        if chest:
            cc = QtGui.QColor(chest.get("color", "#3a3a7a"))
            chest_grad = QtGui.QLinearGradient(cx - 20, cy - 25, cx + 20, cy + 15)
            chest_grad.setColorAt(0, cc.lighter(120))
            chest_grad.setColorAt(0.5, cc)
            chest_grad.setColorAt(1, cc.darker(110))
            painter.setBrush(chest_grad)
            painter.setPen(QtGui.QPen(cc.darker(140), 2))
            # Flowing vest shape
            vest_path = QtGui.QPainterPath()
            vest_path.moveTo(cx - 22, cy - 26)
            vest_path.quadTo(cx, cy - 30, cx + 22, cy - 26)
            vest_path.lineTo(cx + 18, cy + 18)
            vest_path.quadTo(cx, cy + 22, cx - 18, cy + 18)
            vest_path.closeSubpath()
            painter.drawPath(vest_path)
            # Star pattern embroidery
            painter.setBrush(QtGui.QColor(255, 255, 200, 150))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 12, cy - 15, 4, 4)
            painter.drawEllipse(cx + 8, cy - 10, 3, 3)
            painter.drawEllipse(cx - 5, cy + 2, 4, 4)
            painter.drawEllipse(cx + 10, cy + 8, 3, 3)
            # Moon crescent centerpiece
            painter.setBrush(QtGui.QColor("#ffd700"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#daa520"), 1))
            moon_path = QtGui.QPainterPath()
            moon_path.moveTo(cx - 6, cy - 5)
            moon_path.arcTo(cx - 8, cy - 8, 16, 16, 45, 270)
            moon_path.arcTo(cx - 4, cy - 4, 8, 8, 315, -270)
            painter.drawEllipse(cx - 6, cy - 8, 12, 12)
            # Inner cut for crescent
            painter.setBrush(cc)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 2, cy - 6, 10, 10)
        else:
            # Simple robe pattern
            painter.setPen(QtGui.QPen(robe_color.darker(130), 1))
            painter.drawLine(cx, cy - 25, cx, cy + 18)
            painter.drawLine(cx - 12, cy - 24, cx, cy - 18)
            painter.drawLine(cx + 12, cy - 24, cx, cy - 18)

        # === NECK ===
        neck_grad = QtGui.QLinearGradient(cx - 8, cy - 35, cx + 8, cy - 35)
        neck_grad.setColorAt(0, QtGui.QColor("#d4b090"))
        neck_grad.setColorAt(0.5, QtGui.QColor("#e6c8a0"))
        neck_grad.setColorAt(1, QtGui.QColor("#d4b090"))
        painter.setBrush(neck_grad)
        painter.setPen(QtGui.QPen(QtGui.QColor("#c49a70"), 1))
        painter.drawRect(cx - 9, cy - 36, 18, 12)

        # === HEAD ===
        head_gradient = QtGui.QRadialGradient(cx - 5, cy - 55, 30)
        head_gradient.setColorAt(0, QtGui.QColor("#f5e0c8"))
        head_gradient.setColorAt(0.5, QtGui.QColor("#e6c8a0"))
        head_gradient.setColorAt(0.8, QtGui.QColor("#d4a870"))
        head_gradient.setColorAt(1, QtGui.QColor("#c49060"))
        painter.setBrush(head_gradient)
        painter.setPen(QtGui.QPen(QtGui.QColor("#b08050"), 2))
        head_path = QtGui.QPainterPath()
        head_path.moveTo(cx - 2, cy - 32)
        head_path.quadTo(cx - 22, cy - 35, cx - 22, cy - 52)
        head_path.quadTo(cx - 22, cy - 72, cx, cy - 72)
        head_path.quadTo(cx + 22, cy - 72, cx + 22, cy - 52)
        head_path.quadTo(cx + 22, cy - 35, cx + 2, cy - 32)
        head_path.closeSubpath()
        painter.drawPath(head_path)

        # === HELMET (Dream Crown / Star Circlet / Moon Tiara) ===
        helm = self.equipped.get("Helmet")
        if helm:
            hc = QtGui.QColor(helm.get("color", "#4a4a8a"))
            # Circlet/tiara base
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtGui.QPen(hc.lighter(120), 3))
            painter.drawArc(cx - 20, cy - 68, 40, 20, 0, 180 * 16)
            # Crown points with stars
            painter.setBrush(hc.lighter(130))
            painter.setPen(QtGui.QPen(hc.darker(110), 1))
            # Center star point
            center_star = QtGui.QPainterPath()
            center_star.moveTo(cx, cy - 82)
            center_star.lineTo(cx + 4, cy - 72)
            center_star.lineTo(cx - 4, cy - 72)
            center_star.closeSubpath()
            painter.drawPath(center_star)
            # Side points
            left_point = QtGui.QPainterPath()
            left_point.moveTo(cx - 14, cy - 76)
            left_point.lineTo(cx - 10, cy - 68)
            left_point.lineTo(cx - 18, cy - 68)
            left_point.closeSubpath()
            painter.drawPath(left_point)
            right_point = QtGui.QPainterPath()
            right_point.moveTo(cx + 14, cy - 76)
            right_point.lineTo(cx + 10, cy - 68)
            right_point.lineTo(cx + 18, cy - 68)
            right_point.closeSubpath()
            painter.drawPath(right_point)
            # Center gem (moon crystal)
            gem_grad = QtGui.QRadialGradient(cx, cy - 70, 6)
            gem_grad.setColorAt(0, QtGui.QColor("#fff"))
            gem_grad.setColorAt(0.5, hc.lighter(150))
            gem_grad.setColorAt(1, hc)
            painter.setBrush(gem_grad)
            painter.setPen(QtGui.QPen(hc.darker(120), 1))
            painter.drawEllipse(cx - 5, cy - 74, 10, 10)
            # Gem sparkle
            painter.setBrush(QtGui.QColor(255, 255, 255, 200))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 2, cy - 72, 3, 3)
        else:
            # Flowing hair (silvery/mystical)
            hair_color = QtGui.QColor("#6a6a8a")
            hair_grad = QtGui.QRadialGradient(cx, cy - 68, 24)
            hair_grad.setColorAt(0, hair_color.lighter(130))
            hair_grad.setColorAt(0.6, hair_color)
            hair_grad.setColorAt(1, hair_color.darker(120))
            painter.setBrush(hair_grad)
            painter.setPen(QtCore.Qt.NoPen)
            # Flowing mystical hair
            hair_path = QtGui.QPainterPath()
            hair_path.moveTo(cx - 22, cy - 58)
            hair_path.quadTo(cx - 28, cy - 68, cx - 20, cy - 76)
            hair_path.quadTo(cx - 10, cy - 84, cx, cy - 82)
            hair_path.quadTo(cx + 10, cy - 84, cx + 20, cy - 76)
            hair_path.quadTo(cx + 28, cy - 68, cx + 22, cy - 58)
            hair_path.closeSubpath()
            painter.drawPath(hair_path)
            # Hair strands with shimmer
            painter.setPen(QtGui.QPen(hair_color.lighter(140), 1))
            painter.drawLine(cx - 14, cy - 74, cx - 12, cy - 62)
            painter.drawLine(cx - 6, cy - 80, cx - 5, cy - 66)
            painter.drawLine(cx, cy - 82, cx, cy - 68)
            painter.drawLine(cx + 6, cy - 80, cx + 5, cy - 66)
            painter.drawLine(cx + 14, cy - 74, cx + 12, cy - 62)
            # Side tufts
            painter.setBrush(hair_color)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 25, cy - 60, 7, 10)
            painter.drawEllipse(cx + 18, cy - 60, 7, 10)

        # === FACE ===
        # Mystical/serene eyebrows
        painter.setPen(QtGui.QPen(QtGui.QColor("#5a5a7a"), 2))
        if self.tier in ["legendary", "godlike"]:
            # Serene arched brows
            painter.drawArc(cx - 14, cy - 62, 10, 6, 30 * 16, 120 * 16)
            painter.drawArc(cx + 4, cy - 62, 10, 6, 30 * 16, 120 * 16)
        else:
            # Calm brows
            painter.drawLine(cx - 12, cy - 58, cx - 5, cy - 59)
            painter.drawLine(cx + 5, cy - 59, cx + 12, cy - 58)
        
        # Eyes (mystical, glowing)
        painter.setBrush(QtGui.QColor("#d8c0a0"))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(cx - 13, cy - 56, 12, 10)
        painter.drawEllipse(cx + 1, cy - 56, 12, 10)
        # Eye whites with slight glow
        eye_glow = QtGui.QRadialGradient(cx - 7, cy - 51, 6)
        eye_glow.setColorAt(0, QtGui.QColor("#fff"))
        eye_glow.setColorAt(1, QtGui.QColor("#e8e8ff"))
        painter.setBrush(eye_glow)
        painter.drawEllipse(cx - 12, cy - 55, 10, 9)
        eye_glow2 = QtGui.QRadialGradient(cx + 7, cy - 51, 6)
        eye_glow2.setColorAt(0, QtGui.QColor("#fff"))
        eye_glow2.setColorAt(1, QtGui.QColor("#e8e8ff"))
        painter.setBrush(eye_glow2)
        painter.drawEllipse(cx + 2, cy - 55, 10, 9)
        # Iris (mystical purple/silver)
        iris_colors = {
            "pathetic": "#7a7a9a", "modest": "#6a6aaa", "decent": "#5a5aba",
            "heroic": "#6a4aaa", "epic": "#8a4aca", "legendary": "#aa6ada", "godlike": "#ca8afa"
        }
        iris_color = QtGui.QColor(iris_colors.get(self.tier, "#7a7aaa"))
        iris_grad = QtGui.QRadialGradient(cx - 7, cy - 51, 4)
        iris_grad.setColorAt(0, iris_color.lighter(130))
        iris_grad.setColorAt(1, iris_color)
        painter.setBrush(iris_grad)
        painter.drawEllipse(cx - 9, cy - 53, 6, 6)
        iris_grad2 = QtGui.QRadialGradient(cx + 7, cy - 51, 4)
        iris_grad2.setColorAt(0, iris_color.lighter(130))
        iris_grad2.setColorAt(1, iris_color)
        painter.setBrush(iris_grad2)
        painter.drawEllipse(cx + 4, cy - 53, 6, 6)
        # Pupils (star-shaped for high tiers)
        painter.setBrush(QtGui.QColor("#1a1a2a"))
        if self.tier in ["legendary", "godlike"]:
            # Star pupils
            for px in [cx - 7, cx + 6]:
                star = QtGui.QPainterPath()
                star.moveTo(px, cy - 52)
                star.lineTo(px + 1, cy - 50)
                star.lineTo(px + 2, cy - 51)
                star.lineTo(px + 1, cy - 49)
                star.lineTo(px, cy - 48)
                star.lineTo(px - 1, cy - 49)
                star.lineTo(px - 2, cy - 51)
                star.lineTo(px - 1, cy - 50)
                star.closeSubpath()
                painter.drawPath(star)
        else:
            painter.drawEllipse(cx - 8, cy - 52, 3, 3)
            painter.drawEllipse(cx + 5, cy - 52, 3, 3)
        # Eye shine (multiple for mystical look)
        painter.setBrush(QtGui.QColor("#fff"))
        painter.drawEllipse(cx - 9, cy - 53, 2, 2)
        painter.drawEllipse(cx + 4, cy - 53, 2, 2)
        painter.setOpacity(0.6)
        painter.drawEllipse(cx - 5, cy - 49, 1, 1)
        painter.drawEllipse(cx + 8, cy - 49, 1, 1)
        painter.setOpacity(1.0)

        # Nose
        painter.setPen(QtGui.QPen(QtGui.QColor("#c49060"), 1))
        painter.drawLine(cx, cy - 48, cx - 1, cy - 42)
        painter.drawArc(cx - 4, cy - 42, 4, 3, 180 * 16, 180 * 16)
        painter.drawArc(cx, cy - 42, 4, 3, 180 * 16, 180 * 16)

        # Mouth (serene expressions)
        painter.setPen(QtGui.QPen(QtGui.QColor("#a06050"), 2))
        if self.tier in ["legendary", "godlike"]:
            # Serene knowing smile
            painter.drawArc(cx - 8, cy - 44, 16, 10, 210 * 16, 120 * 16)
        elif self.tier in ["epic", "heroic"]:
            # Slight peaceful smile
            painter.drawArc(cx - 7, cy - 42, 14, 6, 220 * 16, 100 * 16)
        else:
            # Contemplative
            painter.drawLine(cx - 5, cy - 38, cx + 5, cy - 38)

        # Ears
        painter.setBrush(QtGui.QColor("#e6c8a0"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#c49a70"), 1))
        painter.drawEllipse(cx - 24, cy - 52, 5, 9)
        painter.drawEllipse(cx + 19, cy - 52, 5, 9)

        # Third eye mark for high tiers (no helmet)
        if not helm and self.tier in ["epic", "legendary", "godlike"]:
            painter.setBrush(QtGui.QColor(200, 180, 255, 150))
            painter.setPen(QtGui.QPen(QtGui.QColor("#9a8aca"), 1))
            painter.drawEllipse(cx - 3, cy - 62, 6, 4)

        # === AMULET (Dream Catcher / Star Pendant / Moon Crystal) ===
        amulet = self.equipped.get("Amulet")
        if amulet:
            ac = QtGui.QColor(amulet.get("color", "#8a8aca"))
            # Chain with ethereal links
            painter.setPen(QtGui.QPen(QtGui.QColor("#c0c0e0"), 2))
            for i in range(4):
                painter.drawEllipse(cx - 11 + i * 3, cy - 28 + i * 2, 3, 3)
                painter.drawEllipse(cx + 8 - i * 3, cy - 28 + i * 2, 3, 3)
            # Dream catcher circle
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtGui.QPen(ac.lighter(120), 2))
            painter.drawEllipse(cx - 12, cy - 18, 24, 24)
            # Inner web pattern
            painter.setPen(QtGui.QPen(ac, 1))
            painter.drawEllipse(cx - 8, cy - 14, 16, 16)
            painter.drawEllipse(cx - 4, cy - 10, 8, 8)
            # Cross pattern
            painter.drawLine(cx, cy - 18, cx, cy + 6)
            painter.drawLine(cx - 12, cy - 6, cx + 12, cy - 6)
            # Center crystal
            gem_grad = QtGui.QRadialGradient(cx, cy - 6, 5)
            gem_grad.setColorAt(0, QtGui.QColor("#fff"))
            gem_grad.setColorAt(0.5, ac.lighter(140))
            gem_grad.setColorAt(1, ac)
            painter.setBrush(gem_grad)
            painter.setPen(QtGui.QPen(ac.darker(120), 1))
            painter.drawEllipse(cx - 4, cy - 10, 8, 8)
            # Feather dangles for high tiers
            if self.tier in ["epic", "legendary", "godlike"]:
                painter.setPen(QtGui.QPen(ac.lighter(110), 1))
                painter.drawLine(cx - 8, cy + 6, cx - 10, cy + 18)
                painter.drawLine(cx, cy + 6, cx, cy + 16)
                painter.drawLine(cx + 8, cy + 6, cx + 10, cy + 18)

        # === WEAPON (Dream Staff / Star Wand / Void Orb) ===
        weap = self.equipped.get("Weapon")
        if weap:
            wc = QtGui.QColor(weap.get("color", "#6a6aaa"))
            # Staff body
            staff_grad = QtGui.QLinearGradient(cx - 56, cy - 50, cx - 50, cy + 35)
            staff_grad.setColorAt(0, wc.lighter(130))
            staff_grad.setColorAt(0.5, wc)
            staff_grad.setColorAt(1, wc.darker(120))
            painter.setBrush(staff_grad)
            painter.setPen(QtGui.QPen(wc.darker(140), 2))
            # Curved mystical staff
            staff_path = QtGui.QPainterPath()
            staff_path.moveTo(cx - 56, cy + 35)
            staff_path.quadTo(cx - 58, cy, cx - 54, cy - 45)
            staff_path.lineTo(cx - 50, cy - 45)
            staff_path.quadTo(cx - 52, cy, cx - 50, cy + 35)
            staff_path.closeSubpath()
            painter.drawPath(staff_path)
            # Staff spiral wrapping
            painter.setPen(QtGui.QPen(wc.lighter(140), 1))
            for i in range(8):
                y = cy - 35 + i * 8
                painter.drawLine(cx - 56, y, cx - 50, y + 4)
            # Orb at top
            orb_grad = QtGui.QRadialGradient(cx - 52, cy - 55, 12)
            orb_grad.setColorAt(0, QtGui.QColor("#fff"))
            orb_grad.setColorAt(0.3, wc.lighter(150))
            orb_grad.setColorAt(0.7, wc)
            orb_grad.setColorAt(1, wc.darker(130))
            painter.setBrush(orb_grad)
            painter.setPen(QtGui.QPen(wc.darker(120), 2))
            painter.drawEllipse(cx - 62, cy - 65, 20, 20)
            # Orb inner glow
            painter.setBrush(QtGui.QColor(255, 255, 255, 100))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 58, cy - 61, 8, 8)
            # Orbiting stars for high tiers
            if self.tier in ["legendary", "godlike"]:
                painter.setBrush(QtGui.QColor("#ffd700"))
                painter.drawEllipse(cx - 66, cy - 52, 4, 4)
                painter.drawEllipse(cx - 46, cy - 58, 4, 4)
                painter.drawEllipse(cx - 58, cy - 70, 3, 3)

        # === SHIELD (Dream Ward / Reality Anchor / Astral Aegis) ===
        shield = self.equipped.get("Shield")
        if shield:
            sc = QtGui.QColor(shield.get("color", "#5a5a9a"))
            # Circular mystical ward
            shield_grad = QtGui.QRadialGradient(cx + 50, cy + 8, 28)
            shield_grad.setColorAt(0, sc.lighter(140))
            shield_grad.setColorAt(0.5, sc)
            shield_grad.setColorAt(1, sc.darker(130))
            painter.setBrush(shield_grad)
            painter.setPen(QtGui.QPen(sc.darker(150), 3))
            painter.drawEllipse(cx + 28, cy - 14, 44, 44)
            # Outer ring
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtGui.QPen(sc.lighter(130), 2))
            painter.drawEllipse(cx + 32, cy - 10, 36, 36)
            # Inner mystical patterns
            painter.setPen(QtGui.QPen(sc.lighter(140), 1))
            # Star pattern
            for angle in range(0, 360, 60):
                import math
                rad = math.radians(angle)
                x1 = cx + 50 + 12 * math.cos(rad)
                y1 = cy + 8 + 12 * math.sin(rad)
                x2 = cx + 50 + 18 * math.cos(rad)
                y2 = cy + 8 + 18 * math.sin(rad)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            # Center eye symbol
            eye_grad = QtGui.QRadialGradient(cx + 50, cy + 8, 10)
            eye_grad.setColorAt(0, QtGui.QColor("#fff"))
            eye_grad.setColorAt(0.4, sc.lighter(160))
            eye_grad.setColorAt(1, sc)
            painter.setBrush(eye_grad)
            painter.setPen(QtGui.QPen(sc.darker(120), 1))
            painter.drawEllipse(cx + 42, cy, 16, 16)
            # Pupil (void)
            painter.setBrush(QtGui.QColor("#1a1a3a"))
            painter.drawEllipse(cx + 47, cy + 5, 6, 6)
            # Eye shine
            painter.setBrush(QtGui.QColor(255, 255, 255, 180))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx + 48, cy + 6, 2, 2)
            # Floating runes for high tiers
            if self.tier in ["epic", "legendary", "godlike"]:
                painter.setOpacity(0.4)
                painter.setBrush(sc.lighter(150))
                painter.drawEllipse(cx + 26, cy - 4, 6, 6)
                painter.drawEllipse(cx + 68, cy - 2, 5, 5)
                painter.drawEllipse(cx + 30, cy + 22, 5, 5)
                painter.drawEllipse(cx + 64, cy + 20, 6, 6)
                painter.setOpacity(1.0)

        # === POWER LABEL ===
        label_rect = QtCore.QRect(0, h - 28, w, 25)
        painter.fillRect(label_rect, QtGui.QColor(0, 0, 0, 120))
        
        if self.tier in ["legendary", "godlike"]:
            painter.setPen(QtGui.QColor("#e0d0ff"))
            painter.setOpacity(0.5)
            for offset in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                painter.drawText(label_rect.translated(offset[0], offset[1]), 
                               QtCore.Qt.AlignCenter, f"🌙 {self.power}")
            painter.setOpacity(1.0)
        elif self.tier in ["epic"]:
            painter.setPen(QtGui.QColor("#c0a0ff"))
        elif self.tier in ["heroic"]:
            painter.setPen(QtGui.QColor("#a0a0ff"))
        else:
            painter.setPen(QtGui.QColor("#d0d0ff"))
        
        # Only draw final text for non-glowing tiers (glow loop already drew it)
        if self.tier not in ["legendary", "godlike"]:
            painter.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Bold))
            painter.drawText(label_rect, QtCore.Qt.AlignCenter, f"🌙 {self.power}")

    def _draw_underdog_character(self, event) -> None:
        """Draw the modern office/corporate themed character."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2 + 5

        # Background with modern office gradient
        bg_gradient = QtGui.QLinearGradient(0, 0, 0, h)
        bg_gradient.setColorAt(0, QtGui.QColor("#2d3436"))
        bg_gradient.setColorAt(0.3, QtGui.QColor("#636e72"))
        bg_gradient.setColorAt(0.7, QtGui.QColor("#b2bec3"))
        bg_gradient.setColorAt(1, QtGui.QColor("#dfe6e9"))
        painter.fillRect(self.rect(), bg_gradient)
        
        # Office floor tiles
        painter.setPen(QtGui.QPen(QtGui.QColor(100, 100, 100, 60), 1))
        for i in range(-2, 5):
            x = cx + i * 30
            painter.drawLine(x, cy + 50, x + 15, cy + 80)
        for j in range(3):
            y = cy + 55 + j * 10
            painter.drawLine(cx - 60, y, cx + 60, y + 8)
        
        # Floor shadow
        floor_gradient = QtGui.QLinearGradient(cx - 40, cy + 65, cx + 40, cy + 80)
        floor_gradient.setColorAt(0, QtGui.QColor(50, 50, 50, 20))
        floor_gradient.setColorAt(0.5, QtGui.QColor(30, 30, 30, 80))
        floor_gradient.setColorAt(1, QtGui.QColor(50, 50, 50, 20))
        painter.setBrush(floor_gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(cx - 40, cy + 65, 80, 18)

        body_color = QtGui.QColor(self.TIER_COLORS.get(self.tier, "#bdbdbd"))
        body_outline = QtGui.QColor(self.TIER_OUTLINE.get(self.tier, "#888"))
        glow = self.TIER_GLOW.get(self.tier)

        def darken(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.darker(amount)
        
        def lighten(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.lighter(amount)

        # Success aura for high tiers
        if glow:
            glow_color = QtGui.QColor(glow)
            painter.setBrush(QtCore.Qt.NoBrush)
            for i, opacity in enumerate([0.06, 0.1, 0.15, 0.25]):
                painter.setOpacity(opacity)
                size = 140 - i * 16
                painter.setPen(QtGui.QPen(glow_color, 2))
                painter.drawEllipse(cx - size//2, cy - 70, size, int(size * 1.15))
            painter.setOpacity(1.0)
            # Inner glow
            painter.setBrush(glow_color)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setOpacity(0.15)
            painter.drawEllipse(cx - 50, cy - 60, 100, 130)
            painter.setOpacity(1.0)
        
        # Floating success particles (dollar signs, stars, etc.)
        particles = self.TIER_PARTICLES.get(self.tier)
        if particles:
            p_color, p_count = particles
            for i, (px, py, ps) in enumerate(self._particles[:p_count]):
                painter.setOpacity(0.4 + (i % 3) * 0.15)
                painter.setBrush(QtGui.QColor(p_color))
                painter.setPen(QtCore.Qt.NoPen)
                if i % 4 == 0:
                    # Star shape
                    star_cx, star_cy = cx + px, cy + py
                    star = QtGui.QPainterPath()
                    star.moveTo(star_cx, star_cy - ps)
                    star.lineTo(star_cx + ps//3, star_cy - ps//3)
                    star.lineTo(star_cx + ps, star_cy)
                    star.lineTo(star_cx + ps//3, star_cy + ps//3)
                    star.lineTo(star_cx, star_cy + ps)
                    star.lineTo(star_cx - ps//3, star_cy + ps//3)
                    star.lineTo(star_cx - ps, star_cy)
                    star.lineTo(star_cx - ps//3, star_cy - ps//3)
                    star.closeSubpath()
                    painter.drawPath(star)
                else:
                    # Diamond/gem
                    painter.drawEllipse(cx + px, cy + py, ps + 1, ps + 1)
            painter.setOpacity(1.0)

        # === CLOAK/OUTERWEAR (Jacket/Hoodie/Blazer) ===
        cloak = self.equipped.get("Cloak")
        if cloak:
            cc = QtGui.QColor(cloak.get("color", "#34495e"))
            path = QtGui.QPainterPath()
            path.moveTo(cx - 26, cy - 26)
            path.lineTo(cx + 26, cy - 26)
            path.quadTo(cx + 35, cy + 5, cx + 32, cy + 50)
            path.lineTo(cx + 28, cy + 68)
            path.quadTo(cx, cy + 72, cx - 28, cy + 68)
            path.lineTo(cx - 32, cy + 50)
            path.quadTo(cx - 35, cy + 5, cx - 26, cy - 26)
            cloak_gradient = QtGui.QLinearGradient(cx, cy - 30, cx, cy + 70)
            cloak_gradient.setColorAt(0, cc.lighter(115))
            cloak_gradient.setColorAt(0.5, cc)
            cloak_gradient.setColorAt(1, darken(cloak.get("color", "#34495e"), 125))
            painter.setBrush(cloak_gradient)
            painter.setPen(QtGui.QPen(darken(cloak.get("color", "#34495e"), 140), 2))
            painter.drawPath(path)
            # Jacket lapels/collar
            painter.setPen(QtGui.QPen(cc.darker(130), 2))
            painter.drawLine(cx - 8, cy - 22, cx - 12, cy + 20)
            painter.drawLine(cx + 8, cy - 22, cx + 12, cy + 20)
            # Pockets
            painter.drawRect(cx - 22, cy + 25, 12, 8)
            painter.drawRect(cx + 10, cy + 25, 12, 8)

        # === LEGS (Pants/Trousers) ===
        pants_color = QtGui.QColor("#2c3e50")
        pants_grad = QtGui.QLinearGradient(cx - 18, cy + 25, cx + 18, cy + 25)
        pants_grad.setColorAt(0, pants_color.darker(115))
        pants_grad.setColorAt(0.5, pants_color)
        pants_grad.setColorAt(1, pants_color.darker(115))
        painter.setBrush(pants_grad)
        painter.setPen(QtGui.QPen(pants_color.darker(140), 2))
        # Left leg
        left_leg = QtGui.QPainterPath()
        left_leg.moveTo(cx - 18, cy + 25)
        left_leg.lineTo(cx - 4, cy + 25)
        left_leg.lineTo(cx - 6, cy + 62)
        left_leg.lineTo(cx - 20, cy + 62)
        left_leg.closeSubpath()
        painter.drawPath(left_leg)
        # Right leg
        right_leg = QtGui.QPainterPath()
        right_leg.moveTo(cx + 4, cy + 25)
        right_leg.lineTo(cx + 18, cy + 25)
        right_leg.lineTo(cx + 20, cy + 62)
        right_leg.lineTo(cx + 6, cy + 62)
        right_leg.closeSubpath()
        painter.drawPath(right_leg)

        # === BOOTS/FOOTWEAR (Sneakers/Loafers/Dress Shoes) ===
        boots = self.equipped.get("Boots")
        if boots:
            bc = QtGui.QColor(boots.get("color", "#2d3436"))
            boot_grad = QtGui.QLinearGradient(0, cy + 58, 0, cy + 78)
            boot_grad.setColorAt(0, bc.lighter(115))
            boot_grad.setColorAt(0.5, bc)
            boot_grad.setColorAt(1, bc.darker(115))
            painter.setBrush(boot_grad)
            painter.setPen(QtGui.QPen(bc.darker(130), 2))
            # Left shoe - modern sneaker shape
            left_shoe = QtGui.QPainterPath()
            left_shoe.moveTo(cx - 22, cy + 60)
            left_shoe.lineTo(cx - 4, cy + 60)
            left_shoe.lineTo(cx - 2, cy + 72)
            left_shoe.quadTo(cx - 8, cy + 78, cx - 18, cy + 76)
            left_shoe.quadTo(cx - 26, cy + 72, cx - 24, cy + 64)
            left_shoe.closeSubpath()
            painter.drawPath(left_shoe)
            # Right shoe
            right_shoe = QtGui.QPainterPath()
            right_shoe.moveTo(cx + 4, cy + 60)
            right_shoe.lineTo(cx + 22, cy + 60)
            right_shoe.quadTo(cx + 26, cy + 68, cx + 24, cy + 72)
            right_shoe.quadTo(cx + 18, cy + 78, cx + 8, cy + 76)
            right_shoe.lineTo(cx + 2, cy + 72)
            right_shoe.closeSubpath()
            painter.drawPath(right_shoe)
            # Shoe details (laces/stripes)
            painter.setPen(QtGui.QPen(bc.lighter(150), 1))
            painter.drawLine(cx - 18, cy + 64, cx - 8, cy + 64)
            painter.drawLine(cx - 17, cy + 68, cx - 9, cy + 68)
            painter.drawLine(cx + 8, cy + 64, cx + 18, cy + 64)
            painter.drawLine(cx + 9, cy + 68, cx + 17, cy + 68)
            # Sole
            painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 2))
            painter.drawLine(cx - 24, cy + 74, cx - 4, cy + 76)
            painter.drawLine(cx + 4, cy + 76, cx + 24, cy + 74)
        else:
            # Basic shoes
            painter.setBrush(QtGui.QColor("#2d3436"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#1e272e"), 1))
            painter.drawRoundedRect(cx - 22, cy + 60, 18, 16, 4, 4)
            painter.drawRoundedRect(cx + 4, cy + 60, 18, 16, 4, 4)

        # === ARMS (Shirt sleeves) ===
        chestplate = self.equipped.get("Chestplate")
        if chestplate and isinstance(chestplate, dict):
            shirt_color = QtGui.QColor(chestplate.get("color", "#74b9ff"))
        else:
            shirt_color = QtGui.QColor("#74b9ff")
        arm_grad_l = QtGui.QLinearGradient(cx - 42, cy - 5, cx - 26, cy - 5)
        arm_grad_l.setColorAt(0, shirt_color.darker(120))
        arm_grad_l.setColorAt(0.5, shirt_color)
        arm_grad_l.setColorAt(1, shirt_color.darker(105))
        painter.setBrush(arm_grad_l)
        painter.setPen(QtGui.QPen(shirt_color.darker(140), 2))
        # Left arm
        left_arm = QtGui.QPainterPath()
        left_arm.moveTo(cx - 26, cy - 22)
        left_arm.quadTo(cx - 34, cy - 20, cx - 40, cy - 10)
        left_arm.quadTo(cx - 46, cy + 8, cx - 44, cy + 25)
        left_arm.lineTo(cx - 32, cy + 22)
        left_arm.quadTo(cx - 30, cy - 2, cx - 26, cy - 22)
        painter.drawPath(left_arm)
        # Right arm
        arm_grad_r = QtGui.QLinearGradient(cx + 26, cy - 5, cx + 42, cy - 5)
        arm_grad_r.setColorAt(0, shirt_color.darker(105))
        arm_grad_r.setColorAt(0.5, shirt_color)
        arm_grad_r.setColorAt(1, shirt_color.darker(120))
        painter.setBrush(arm_grad_r)
        right_arm = QtGui.QPainterPath()
        right_arm.moveTo(cx + 26, cy - 22)
        right_arm.quadTo(cx + 34, cy - 20, cx + 40, cy - 10)
        right_arm.quadTo(cx + 46, cy + 8, cx + 44, cy + 25)
        right_arm.lineTo(cx + 32, cy + 22)
        right_arm.quadTo(cx + 30, cy - 2, cx + 26, cy - 22)
        painter.drawPath(right_arm)

        # === GAUNTLETS/ACCESSORIES (Smartwatch/Wristband) ===
        gaunt = self.equipped.get("Gauntlets")
        if gaunt:
            gc = QtGui.QColor(gaunt.get("color", "#2d3436"))
            # Left wristwatch/band
            painter.setBrush(gc)
            painter.setPen(QtGui.QPen(gc.darker(130), 1))
            painter.drawRoundedRect(cx - 46, cy + 14, 16, 12, 3, 3)
            # Watch face
            painter.setBrush(QtGui.QColor("#1e272e"))
            painter.drawRoundedRect(cx - 44, cy + 16, 12, 8, 2, 2)
            # Watch screen glow
            screen_grad = QtGui.QRadialGradient(cx - 38, cy + 20, 5)
            screen_grad.setColorAt(0, QtGui.QColor("#00ff88"))
            screen_grad.setColorAt(1, QtGui.QColor("#00aa55"))
            painter.setBrush(screen_grad)
            painter.drawRect(cx - 42, cy + 17, 8, 6)
            # Right wristband/fitness tracker
            painter.setBrush(gc)
            painter.setPen(QtGui.QPen(gc.darker(130), 1))
            painter.drawRoundedRect(cx + 30, cy + 14, 16, 12, 3, 3)
            # Band pattern
            painter.setPen(QtGui.QPen(gc.lighter(130), 1))
            painter.drawLine(cx + 32, cy + 18, cx + 44, cy + 18)
            painter.drawLine(cx + 32, cy + 22, cx + 44, cy + 22)
        else:
            # Bare hands
            painter.setBrush(QtGui.QColor("#e6c8a0"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#c9a066"), 1))
            painter.drawEllipse(cx - 46, cy + 16, 14, 12)
            painter.drawEllipse(cx + 32, cy + 16, 14, 12)

        # === TORSO ===
        torso_grad = QtGui.QLinearGradient(cx - 24, cy, cx + 24, cy)
        torso_grad.setColorAt(0, shirt_color.darker(110))
        torso_grad.setColorAt(0.3, shirt_color)
        torso_grad.setColorAt(0.7, shirt_color)
        torso_grad.setColorAt(1, shirt_color.darker(110))
        painter.setBrush(torso_grad)
        painter.setPen(QtGui.QPen(shirt_color.darker(140), 2))
        torso_path = QtGui.QPainterPath()
        torso_path.moveTo(cx - 24, cy - 26)
        torso_path.quadTo(cx - 26, cy - 5, cx - 18, cy + 28)
        torso_path.lineTo(cx + 18, cy + 28)
        torso_path.quadTo(cx + 26, cy - 5, cx + 24, cy - 26)
        torso_path.closeSubpath()
        painter.drawPath(torso_path)

        # === CHESTPLATE/TOP (Hoodie/Blazer/Polo) ===
        chest = self.equipped.get("Chestplate")
        if chest:
            cc = QtGui.QColor(chest.get("color", "#0984e3"))
            chest_grad = QtGui.QLinearGradient(cx - 20, cy - 24, cx + 20, cy + 20)
            chest_grad.setColorAt(0, cc.lighter(115))
            chest_grad.setColorAt(0.5, cc)
            chest_grad.setColorAt(1, cc.darker(110))
            painter.setBrush(chest_grad)
            painter.setPen(QtGui.QPen(cc.darker(130), 2))
            # Shirt/top shape
            top_path = QtGui.QPainterPath()
            top_path.moveTo(cx - 20, cy - 24)
            top_path.quadTo(cx, cy - 28, cx + 20, cy - 24)
            top_path.lineTo(cx + 16, cy + 22)
            top_path.quadTo(cx, cy + 26, cx - 16, cy + 22)
            top_path.closeSubpath()
            painter.drawPath(top_path)
            # Collar (polo/button-down style)
            painter.setPen(QtGui.QPen(cc.darker(120), 2))
            painter.drawLine(cx - 10, cy - 24, cx, cy - 18)
            painter.drawLine(cx + 10, cy - 24, cx, cy - 18)
            # Buttons
            painter.setBrush(QtGui.QColor("#dfe6e9"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#b2bec3"), 1))
            for by in [cy - 12, cy - 2, cy + 8]:
                painter.drawEllipse(cx - 2, by, 4, 4)
            # Pocket
            painter.setPen(QtGui.QPen(cc.darker(120), 1))
            painter.drawRect(cx - 14, cy - 8, 8, 10)
        else:
            # Plain t-shirt look
            painter.setPen(QtGui.QPen(shirt_color.darker(120), 1))
            painter.drawLine(cx, cy - 24, cx, cy + 20)

        # === NECK ===
        neck_grad = QtGui.QLinearGradient(cx - 8, cy - 32, cx + 8, cy - 32)
        neck_grad.setColorAt(0, QtGui.QColor("#d4b090"))
        neck_grad.setColorAt(0.5, QtGui.QColor("#e6c8a0"))
        neck_grad.setColorAt(1, QtGui.QColor("#d4b090"))
        painter.setBrush(neck_grad)
        painter.setPen(QtGui.QPen(QtGui.QColor("#c49a70"), 1))
        painter.drawRect(cx - 8, cy - 34, 16, 12)

        # === HEAD ===
        head_gradient = QtGui.QRadialGradient(cx - 4, cy - 52, 28)
        head_gradient.setColorAt(0, QtGui.QColor("#f5e0c8"))
        head_gradient.setColorAt(0.5, QtGui.QColor("#e6c8a0"))
        head_gradient.setColorAt(0.8, QtGui.QColor("#d4a870"))
        head_gradient.setColorAt(1, QtGui.QColor("#c49060"))
        painter.setBrush(head_gradient)
        painter.setPen(QtGui.QPen(QtGui.QColor("#b08050"), 2))
        head_path = QtGui.QPainterPath()
        head_path.moveTo(cx - 2, cy - 30)
        head_path.quadTo(cx - 20, cy - 33, cx - 20, cy - 50)
        head_path.quadTo(cx - 20, cy - 70, cx, cy - 70)
        head_path.quadTo(cx + 20, cy - 70, cx + 20, cy - 50)
        head_path.quadTo(cx + 20, cy - 33, cx + 2, cy - 30)
        head_path.closeSubpath()
        painter.drawPath(head_path)

        # === HELMET/HEADWEAR (Headphones/Cap/Beanie) ===
        helm = self.equipped.get("Helmet")
        if helm:
            hc = QtGui.QColor(helm.get("color", "#2d3436"))
            # Headphones design
            # Headband
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtGui.QPen(hc, 4))
            painter.drawArc(cx - 22, cy - 75, 44, 30, 0, 180 * 16)
            # Left ear cup
            painter.setBrush(hc)
            painter.setPen(QtGui.QPen(hc.darker(130), 2))
            left_cup = QtGui.QPainterPath()
            left_cup.addRoundedRect(cx - 28, cy - 60, 12, 18, 4, 4)
            painter.drawPath(left_cup)
            # Ear cup detail (speaker mesh)
            painter.setBrush(hc.darker(140))
            painter.drawEllipse(cx - 26, cy - 56, 8, 10)
            # Right ear cup
            painter.setBrush(hc)
            painter.setPen(QtGui.QPen(hc.darker(130), 2))
            right_cup = QtGui.QPainterPath()
            right_cup.addRoundedRect(cx + 16, cy - 60, 12, 18, 4, 4)
            painter.drawPath(right_cup)
            painter.setBrush(hc.darker(140))
            painter.drawEllipse(cx + 18, cy - 56, 8, 10)
            # LED indicator for high tiers
            if self.tier in ["heroic", "epic", "legendary", "godlike"]:
                painter.setBrush(QtGui.QColor("#00ff88"))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(cx - 25, cy - 46, 4, 4)
                painter.drawEllipse(cx + 21, cy - 46, 4, 4)
        else:
            # Modern haircut
            hair_color = QtGui.QColor("#4a3728")
            hair_grad = QtGui.QRadialGradient(cx, cy - 65, 22)
            hair_grad.setColorAt(0, hair_color.lighter(120))
            hair_grad.setColorAt(0.6, hair_color)
            hair_grad.setColorAt(1, hair_color.darker(115))
            painter.setBrush(hair_grad)
            painter.setPen(QtCore.Qt.NoPen)
            # Modern styled hair
            hair_path = QtGui.QPainterPath()
            hair_path.moveTo(cx - 20, cy - 55)
            hair_path.quadTo(cx - 24, cy - 65, cx - 18, cy - 72)
            hair_path.quadTo(cx - 8, cy - 78, cx + 5, cy - 76)
            hair_path.quadTo(cx + 18, cy - 74, cx + 22, cy - 65)
            hair_path.quadTo(cx + 24, cy - 55, cx + 20, cy - 50)
            hair_path.quadTo(cx + 18, cy - 58, cx + 12, cy - 62)
            hair_path.quadTo(cx, cy - 66, cx - 12, cy - 62)
            hair_path.quadTo(cx - 18, cy - 58, cx - 20, cy - 55)
            painter.drawPath(hair_path)
            # Side hair
            painter.drawEllipse(cx - 22, cy - 56, 6, 12)
            painter.drawEllipse(cx + 16, cy - 56, 6, 12)

        # === FACE ===
        # Modern/confident eyebrows
        painter.setPen(QtGui.QPen(QtGui.QColor("#4a3728"), 2))
        if self.tier in ["legendary", "godlike"]:
            # Confident raised brows
            painter.drawLine(cx - 12, cy - 58, cx - 4, cy - 60)
            painter.drawLine(cx + 4, cy - 60, cx + 12, cy - 58)
        elif self.tier in ["epic", "heroic"]:
            # Focused brows
            painter.drawLine(cx - 12, cy - 57, cx - 5, cy - 58)
            painter.drawLine(cx + 5, cy - 58, cx + 12, cy - 57)
        else:
            # Normal brows
            painter.drawLine(cx - 11, cy - 56, cx - 5, cy - 57)
            painter.drawLine(cx + 5, cy - 57, cx + 11, cy - 56)
        
        # Eyes (alert, focused)
        painter.setBrush(QtGui.QColor("#e8dcc8"))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(cx - 12, cy - 54, 11, 9)
        painter.drawEllipse(cx + 1, cy - 54, 11, 9)
        # Eye whites
        painter.setBrush(QtGui.QColor("#fff"))
        painter.drawEllipse(cx - 11, cy - 53, 9, 8)
        painter.drawEllipse(cx + 2, cy - 53, 9, 8)
        # Iris (determined colors)
        iris_colors = {
            "pathetic": "#6b4423", "modest": "#5d4037", "decent": "#4e342e",
            "heroic": "#1565c0", "epic": "#0d47a1", "legendary": "#00838f", "godlike": "#006064"
        }
        iris_color = QtGui.QColor(iris_colors.get(self.tier, "#5d4037"))
        iris_grad = QtGui.QRadialGradient(cx - 7, cy - 49, 4)
        iris_grad.setColorAt(0, iris_color.lighter(130))
        iris_grad.setColorAt(1, iris_color)
        painter.setBrush(iris_grad)
        painter.drawEllipse(cx - 9, cy - 51, 6, 6)
        iris_grad2 = QtGui.QRadialGradient(cx + 6, cy - 49, 4)
        iris_grad2.setColorAt(0, iris_color.lighter(130))
        iris_grad2.setColorAt(1, iris_color)
        painter.setBrush(iris_grad2)
        painter.drawEllipse(cx + 4, cy - 51, 6, 6)
        # Pupils
        painter.setBrush(QtGui.QColor("#1a1a1a"))
        painter.drawEllipse(cx - 7, cy - 50, 3, 3)
        painter.drawEllipse(cx + 5, cy - 50, 3, 3)
        # Eye shine
        painter.setBrush(QtGui.QColor("#fff"))
        painter.drawEllipse(cx - 8, cy - 51, 2, 2)
        painter.drawEllipse(cx + 4, cy - 51, 2, 2)

        # Nose
        painter.setPen(QtGui.QPen(QtGui.QColor("#c49060"), 1))
        painter.drawLine(cx, cy - 46, cx - 1, cy - 40)
        painter.drawArc(cx - 4, cy - 40, 4, 3, 180 * 16, 180 * 16)
        painter.drawArc(cx, cy - 40, 4, 3, 180 * 16, 180 * 16)

        # Mouth (confident expressions)
        painter.setPen(QtGui.QPen(QtGui.QColor("#a06050"), 2))
        if self.tier in ["legendary", "godlike"]:
            # Big confident grin
            painter.drawArc(cx - 10, cy - 42, 20, 12, 210 * 16, 120 * 16)
            # Teeth hint
            painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 1))
            painter.drawLine(cx - 6, cy - 34, cx + 6, cy - 34)
        elif self.tier in ["epic", "heroic"]:
            # Smirk
            painter.drawArc(cx - 8, cy - 40, 16, 8, 220 * 16, 100 * 16)
        elif self.tier == "decent":
            # Slight smile
            painter.drawArc(cx - 6, cy - 38, 12, 6, 220 * 16, 100 * 16)
        else:
            # Determined/neutral
            painter.drawLine(cx - 5, cy - 36, cx + 5, cy - 36)

        # Ears (only visible when no headphones)
        helm = self.equipped.get("Helmet")
        if not helm:
            painter.setBrush(QtGui.QColor("#e6c8a0"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#c49a70"), 1))
            painter.drawEllipse(cx - 22, cy - 52, 5, 9)
            painter.drawEllipse(cx + 17, cy - 52, 5, 9)

        # 5 o'clock shadow for higher tiers (subtle)
        if self.tier in ["heroic", "epic", "legendary", "godlike"]:
            painter.setOpacity(0.15)
            painter.setBrush(QtGui.QColor("#4a3728"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 10, cy - 38, 20, 10)
            painter.setOpacity(1.0)

        # === AMULET/BADGE (ID Badge/Keycard/Award) ===
        amulet = self.equipped.get("Amulet")
        if amulet:
            ac = QtGui.QColor(amulet.get("color", "#ffd700"))
            # Lanyard
            painter.setPen(QtGui.QPen(QtGui.QColor("#2d3436"), 2))
            painter.drawLine(cx - 8, cy - 26, cx - 6, cy - 12)
            painter.drawLine(cx + 8, cy - 26, cx + 6, cy - 12)
            # ID Badge
            badge_grad = QtGui.QLinearGradient(cx - 10, cy - 12, cx + 10, cy + 8)
            badge_grad.setColorAt(0, QtGui.QColor("#fff"))
            badge_grad.setColorAt(0.3, QtGui.QColor("#f5f5f5"))
            badge_grad.setColorAt(1, QtGui.QColor("#e0e0e0"))
            painter.setBrush(badge_grad)
            painter.setPen(QtGui.QPen(QtGui.QColor("#bdbdbd"), 1))
            painter.drawRoundedRect(cx - 12, cy - 12, 24, 28, 3, 3)
            # Photo area
            painter.setBrush(QtGui.QColor("#b2bec3"))
            painter.drawRect(cx - 8, cy - 8, 16, 12)
            # Barcode
            painter.setPen(QtGui.QPen(QtGui.QColor("#2d3436"), 1))
            for i in range(8):
                x = cx - 7 + i * 2
                painter.drawLine(x, cy + 6, x, cy + 12)
            # Badge clip
            painter.setBrush(ac)
            painter.setPen(QtGui.QPen(ac.darker(130), 1))
            painter.drawRect(cx - 6, cy - 16, 12, 6)
            # Star/award indicator for high tiers
            if self.tier in ["epic", "legendary", "godlike"]:
                painter.setBrush(QtGui.QColor("#ffd700"))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(cx + 6, cy - 10, 8, 8)

        # === WEAPON/DEVICE (Smartphone/Keyboard/Coffee Mug) ===
        weap = self.equipped.get("Weapon")
        if weap:
            wc = QtGui.QColor(weap.get("color", "#2d3436"))
            # Smartphone in hand
            phone_grad = QtGui.QLinearGradient(cx - 58, cy - 10, cx - 42, cy + 20)
            phone_grad.setColorAt(0, wc.lighter(110))
            phone_grad.setColorAt(0.5, wc)
            phone_grad.setColorAt(1, wc.darker(115))
            painter.setBrush(phone_grad)
            painter.setPen(QtGui.QPen(wc.darker(140), 2))
            # Phone body
            painter.drawRoundedRect(cx - 58, cy - 15, 18, 35, 3, 3)
            # Screen
            screen_grad = QtGui.QLinearGradient(cx - 56, cy - 12, cx - 42, cy + 15)
            screen_grad.setColorAt(0, QtGui.QColor("#4fc3f7"))
            screen_grad.setColorAt(0.5, QtGui.QColor("#29b6f6"))
            screen_grad.setColorAt(1, QtGui.QColor("#0288d1"))
            painter.setBrush(screen_grad)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(cx - 56, cy - 10, 14, 26)
            # Screen content (app icons)
            painter.setBrush(QtGui.QColor("#fff"))
            for row in range(3):
                for col in range(2):
                    painter.drawRect(cx - 55 + col * 7, cy - 8 + row * 8, 5, 5)
            # Camera notch
            painter.setBrush(wc.darker(130))
            painter.drawEllipse(cx - 51, cy - 13, 4, 3)
            # Notification badge for high tiers
            if self.tier in ["legendary", "godlike"]:
                painter.setBrush(QtGui.QColor("#e74c3c"))
                painter.drawEllipse(cx - 44, cy - 14, 6, 6)
                painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 1))
                painter.setFont(QtGui.QFont("Segoe UI", 5, QtGui.QFont.Bold))
                painter.drawText(cx - 43, cy - 8, "9")

        # === SHIELD/PROTECTION (Laptop/Tablet/Briefcase) ===
        shield = self.equipped.get("Shield")
        if shield:
            sc = QtGui.QColor(shield.get("color", "#636e72"))
            # Laptop
            laptop_grad = QtGui.QLinearGradient(cx + 28, cy - 20, cx + 70, cy + 25)
            laptop_grad.setColorAt(0, sc.lighter(115))
            laptop_grad.setColorAt(0.5, sc)
            laptop_grad.setColorAt(1, sc.darker(120))
            painter.setBrush(laptop_grad)
            painter.setPen(QtGui.QPen(sc.darker(140), 2))
            # Screen (tilted)
            screen_path = QtGui.QPainterPath()
            screen_path.moveTo(cx + 30, cy - 15)
            screen_path.lineTo(cx + 68, cy - 20)
            screen_path.lineTo(cx + 65, cy + 18)
            screen_path.lineTo(cx + 32, cy + 22)
            screen_path.closeSubpath()
            painter.drawPath(screen_path)
            # Screen display
            display_grad = QtGui.QLinearGradient(cx + 32, cy - 12, cx + 64, cy + 18)
            display_grad.setColorAt(0, QtGui.QColor("#2d3436"))
            display_grad.setColorAt(0.3, QtGui.QColor("#1e272e"))
            display_grad.setColorAt(1, QtGui.QColor("#0d1b2a"))
            painter.setBrush(display_grad)
            painter.setPen(QtCore.Qt.NoPen)
            display_path = QtGui.QPainterPath()
            display_path.moveTo(cx + 34, cy - 10)
            display_path.lineTo(cx + 64, cy - 14)
            display_path.lineTo(cx + 62, cy + 14)
            display_path.lineTo(cx + 35, cy + 18)
            display_path.closeSubpath()
            painter.drawPath(display_path)
            # Code on screen
            painter.setPen(QtGui.QPen(QtGui.QColor("#00ff88"), 1))
            for i in range(5):
                y = cy - 6 + i * 5
                w_line = 10 + (i % 3) * 5
                painter.drawLine(cx + 36, y, cx + 36 + w_line, y)
            # Keyboard base
            painter.setBrush(sc.darker(110))
            painter.setPen(QtGui.QPen(sc.darker(130), 1))
            painter.drawRect(cx + 30, cy + 24, 36, 8)
            # Keyboard keys hint
            painter.setPen(QtGui.QPen(sc.lighter(130), 1))
            for i in range(6):
                painter.drawLine(cx + 34 + i * 5, cy + 26, cx + 34 + i * 5, cy + 30)
            # Apple/brand logo
            if self.tier in ["epic", "legendary", "godlike"]:
                painter.setBrush(QtGui.QColor("#c0c0c0"))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(cx + 46, cy - 2, 6, 6)

        # === POWER LABEL ===
        label_rect = QtCore.QRect(0, h - 28, w, 25)
        painter.fillRect(label_rect, QtGui.QColor(0, 0, 0, 120))
        
        if self.tier in ["legendary", "godlike"]:
            painter.setPen(QtGui.QColor("#ffd700"))
            painter.setOpacity(0.5)
            for offset in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                painter.drawText(label_rect.translated(offset[0], offset[1]), 
                               QtCore.Qt.AlignCenter, f"🏢 {self.power}")
            painter.setOpacity(1.0)
        elif self.tier in ["epic"]:
            painter.setPen(QtGui.QColor("#00bcd4"))
        elif self.tier in ["heroic"]:
            painter.setPen(QtGui.QColor("#4fc3f7"))
        else:
            painter.setPen(QtGui.QColor("#b2bec3"))
        
        # Only draw final text for non-glowing tiers (glow loop already drew it)
        if self.tier not in ["legendary", "godlike"]:
            painter.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Bold))
            painter.drawText(label_rect, QtCore.Qt.AlignCenter, f"🏢 {self.power}")

    def _draw_scientist_character(self, event) -> None:
        """Draw the modern research scientist character."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2 + 5

        # Background with sterile laboratory gradient (cyan/green lab aesthetic)
        bg_gradient = QtGui.QLinearGradient(0, 0, 0, h)
        bg_gradient.setColorAt(0, QtGui.QColor("#004d40"))  # Dark teal
        bg_gradient.setColorAt(0.4, QtGui.QColor("#00695c"))  # Teal
        bg_gradient.setColorAt(0.7, QtGui.QColor("#00897b"))  # Light teal
        bg_gradient.setColorAt(1, QtGui.QColor("#26a69a"))  # Cyan-green
        painter.fillRect(self.rect(), bg_gradient)
        
        # Lab equipment shelves in background (left side)
        painter.setOpacity(0.4)
        painter.setBrush(QtGui.QColor("#263238"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#37474f"), 2))
        # Shelving unit
        painter.drawRect(10, cy - 60, 45, 90)
        painter.drawLine(10, cy - 30, 55, cy - 30)
        painter.drawLine(10, cy, 55, cy)
        # Beakers and flasks on shelves
        painter.setOpacity(0.5)
        # Top shelf - Erlenmeyer flask
        painter.setBrush(QtGui.QColor("#4fc3f7"))
        flask_path = QtGui.QPainterPath()
        flask_path.moveTo(25, cy - 55)
        flask_path.lineTo(22, cy - 45)
        flask_path.quadTo(20, cy - 35, 28, cy - 35)
        flask_path.lineTo(32, cy - 35)
        flask_path.quadTo(40, cy - 35, 38, cy - 45)
        flask_path.lineTo(35, cy - 55)
        flask_path.closeSubpath()
        painter.drawPath(flask_path)
        # Middle shelf - Beaker
        painter.setBrush(QtGui.QColor("#8bc34a"))
        painter.drawRect(18, cy - 25, 12, 18)
        painter.drawLine(18, cy - 15, 30, cy - 15)
        # Bottom shelf - Round flask
        painter.setBrush(QtGui.QColor("#ff9800"))
        painter.drawEllipse(22, cy + 5, 16, 16)
        painter.drawRect(28, cy + 3, 4, 6)
        painter.setOpacity(1.0)
        
        # Lab equipment on right side (microscope stand for high tiers)
        if self.tier in ["heroic", "epic", "legendary", "godlike"]:
            painter.setOpacity(0.35)
            painter.setBrush(QtGui.QColor("#455a64"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#607d8b"), 2))
            # Microscope base
            painter.drawRect(w - 60, cy + 10, 40, 8)
            # Stand
            painter.drawRect(w - 44, cy - 40, 8, 50)
            # Microscope body
            painter.drawEllipse(w - 50, cy - 45, 20, 15)
            painter.setOpacity(1.0)
        
        # Biohazard symbols on walls (all tiers)
        painter.setOpacity(0.25)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtGui.QPen(QtGui.QColor("#ffeb3b"), 2))
        # Left wall biohazard
        painter.drawEllipse(15, 25, 25, 25)
        painter.drawEllipse(22, 32, 11, 11)
        # Draw 3 biohazard segments
        for angle in [0, 120, 240]:
            painter.save()
            painter.translate(27.5, 37.5)
            painter.rotate(angle)
            painter.drawEllipse(8, -3, 6, 6)
            painter.restore()
        painter.setOpacity(1.0)
        
        # Centrifuge (spinning lab equipment) for mid+ tiers
        if self.tier not in ["pathetic", "modest"]:
            painter.setOpacity(0.3)
            painter.setBrush(QtGui.QColor("#37474f"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#546e7a"), 2))
            # Centrifuge body
            painter.drawRect(w - 55, cy - 75, 35, 25)
            # Lid with motion blur effect
            painter.setOpacity(0.15)
            for blur in range(3):
                painter.drawArc(w - 53 + blur * 2, cy - 73, 15, 15, 45 * 16, 270 * 16)
            painter.setOpacity(1.0)
        
        # Fume hood with glowing interior (epic+)
        if self.tier in ["epic", "legendary", "godlike"]:
            painter.setOpacity(0.25)
            painter.setBrush(QtGui.QColor("#263238"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#37474f"), 2))
            # Hood structure
            painter.drawRect(w - 90, 50, 70, 60)
            # Glowing interior
            fume_glow = QtGui.QRadialGradient(w - 55, 80, 30)
            fume_glow.setColorAt(0, QtGui.QColor("#00e676"))
            fume_glow.setColorAt(1, QtGui.QColor("#00695c"))
            painter.setBrush(fume_glow)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(w - 85, 55, 60, 50)
            painter.setOpacity(1.0)
        
        # Achievement certificates/awards on back wall for high tiers
        if self.tier in ["epic", "legendary", "godlike"]:
            painter.setOpacity(0.3)
            painter.setBrush(QtGui.QColor("#ffd700" if self.tier == "godlike" else "#c0c0c0"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#8b7500" if self.tier == "godlike" else "#808080"), 1))
            # Certificate frame (top right)
            painter.drawRect(w - 80, 20, 60, 45)
            painter.drawRect(w - 77, 23, 54, 39)
            # Medal/award (top left) for godlike
            if self.tier == "godlike":
                painter.setBrush(QtGui.QColor("#ffd700"))
                painter.drawEllipse(20, 15, 30, 30)
                painter.setPen(QtGui.QPen(QtGui.QColor("#ff6b6b"), 2))
                painter.drawLine(35, 45, 35, 60)
            painter.setOpacity(1.0)
        
        # Whiteboard with formulas (heroic+ tiers)
        if self.tier in ["heroic", "epic", "legendary", "godlike"]:
            painter.setOpacity(0.35)
            painter.setBrush(QtGui.QColor("#f5f5f5"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#757575"), 2))
            # Whiteboard on right wall
            painter.drawRect(w - 90, cy - 50, 70, 50)
            # Formulas written on board
            painter.setPen(QtGui.QPen(QtGui.QColor("#1e88e5"), 1))
            painter.drawText(w - 85, cy - 40, "E=mc²")
            painter.drawText(w - 85, cy - 30, "ΔG=ΔH-TΔS")
            painter.setPen(QtGui.QPen(QtGui.QColor("#d32f2f"), 1))
            painter.drawLine(w - 85, cy - 20, w - 35, cy - 22)
            painter.drawLine(w - 85, cy - 15, w - 50, cy - 16)
            painter.setOpacity(1.0)
        
        # Computer workstation (legendary/godlike only)
        if self.tier in ["legendary", "godlike"]:
            painter.setOpacity(0.4)
            painter.setBrush(QtGui.QColor("#263238"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#37474f"), 1))
            # Monitor
            painter.drawRect(w - 75, cy + 15, 50, 35)
            # Glowing screen
            screen_glow = QtGui.QRadialGradient(w - 50, cy + 32, 25)
            screen_glow.setColorAt(0, QtGui.QColor("#00e676"))
            screen_glow.setColorAt(1, QtGui.QColor("#00c853"))
            painter.setBrush(screen_glow)
            painter.drawRect(w - 72, cy + 18, 44, 29)
            # Data visualization on screen
            painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff"), 1))
            for i in range(5):
                h = 5 + i * 3
                painter.drawLine(w - 68 + i * 8, cy + 42, w - 68 + i * 8, cy + 42 - h)
            painter.setOpacity(1.0)
        
        # Laboratory floor tiles
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 50), 1))
        for i in range(-3, 4):
            x = cx + i * 25
            painter.drawLine(x, cy + 50, x + 12, cy + 80)
        for j in range(3):
            y = cy + 55 + j * 10
            painter.drawLine(cx - 70, y, cx + 70, y + 6)
        
        # Floor shadow (clean lab floor)
        floor_gradient = QtGui.QLinearGradient(cx - 45, cy + 65, cx + 45, cy + 80)
        floor_gradient.setColorAt(0, QtGui.QColor(50, 50, 100, 30))
        floor_gradient.setColorAt(0.5, QtGui.QColor(30, 30, 80, 90))
        floor_gradient.setColorAt(1, QtGui.QColor(50, 50, 100, 30))
        painter.setBrush(floor_gradient)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(cx - 45, cy + 65, 90, 18)

        body_color = QtGui.QColor(self.TIER_COLORS.get(self.tier, "#bdbdbd"))
        body_outline = QtGui.QColor(self.TIER_OUTLINE.get(self.tier, "#888"))
        glow = self.TIER_GLOW.get(self.tier)

        def darken(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.darker(amount)
        
        def lighten(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.lighter(amount)

        # Scientific aura for high tiers (golden/quantum glow)
        if glow:
            glow_color = QtGui.QColor(glow)
            painter.setBrush(QtCore.Qt.NoBrush)
            for i, opacity in enumerate([0.08, 0.12, 0.18, 0.28]):
                painter.setOpacity(opacity)
                size = 150 - i * 18
                painter.setPen(QtGui.QPen(glow_color, 2))
                painter.drawEllipse(cx - size//2, cy - 75, size, int(size * 1.2))
            painter.setOpacity(1.0)
            # Inner scientific glow
            painter.setBrush(glow_color)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setOpacity(0.18)
            painter.drawEllipse(cx - 55, cy - 65, 110, 140)
            painter.setOpacity(1.0)
        
        # Floating scientific particles (chemical formulas and periodic elements)
        particles = self.TIER_PARTICLES.get(self.tier)
        if particles:
            p_color, p_count = particles
            # Chemical formulas and periodic elements
            elements = ["H₂O", "CO₂", "NaCl", "Au", "Fe", "C", "O₂", "N₂", "CH₄", "H₂SO₄"]
            element_colors = ["#4fc3f7", "#66bb6a", "#ffa726", "#ffd700", "#ef5350", 
                            "#9e9e9e", "#42a5f5", "#ba68c8", "#26c6da", "#ffeb3b"]
            
            for i, (px, py, ps) in enumerate(self._particles[:p_count]):
                painter.setOpacity(0.55 + (i % 3) * 0.15)
                if i % 8 == 0:
                    # Periodic table element box
                    elem_color = QtGui.QColor(element_colors[i % len(element_colors)])
                    painter.setBrush(elem_color)
                    painter.setPen(QtGui.QPen(elem_color.darker(130), 1))
                    painter.drawRect(cx + px - ps*2, cy + py - ps*2, ps*4, ps*4)
                    painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 1))
                    painter.setFont(QtGui.QFont("Arial", max(6, ps)))
                    painter.drawText(cx + px - ps, cy + py + ps//2, elements[i % len(elements)][:2])
                    painter.setPen(QtCore.Qt.NoPen)
                elif i % 8 == 1:
                    # Chemical formula text
                    painter.setPen(QtGui.QPen(QtGui.QColor(p_color), 1))
                    painter.setFont(QtGui.QFont("Arial", max(7, ps + 2)))
                    painter.drawText(cx + px - ps*2, cy + py, elements[i % len(elements)])
                    painter.setPen(QtCore.Qt.NoPen)
                elif i % 8 == 2:
                    # Benzene ring (hexagon)
                    painter.setPen(QtGui.QPen(QtGui.QColor(p_color), 2))
                    painter.setBrush(QtCore.Qt.NoBrush)
                    hex_path = QtGui.QPainterPath()
                    for angle in range(0, 360, 60):
                        rad = angle * 3.14159 / 180
                        x = cx + px + ps * 2 * math.cos(rad)
                        y = cy + py + ps * 2 * math.sin(rad)
                        if angle == 0:
                            hex_path.moveTo(x, y)
                        else:
                            hex_path.lineTo(x, y)
                    hex_path.closeSubpath()
                    painter.drawPath(hex_path)
                    painter.setPen(QtCore.Qt.NoPen)
                elif i % 8 == 3:
                    # DNA helix segment
                    painter.setPen(QtGui.QPen(QtGui.QColor(p_color), 2))
                    painter.drawLine(cx + px - ps, cy + py - ps*2, cx + px + ps, cy + py + ps*2)
                    painter.drawLine(cx + px + ps, cy + py - ps*2, cx + px - ps, cy + py + ps*2)
                    painter.setPen(QtCore.Qt.NoPen)
                elif i % 8 == 4:
                    # Molecule with bonds
                    painter.setBrush(QtGui.QColor(p_color))
                    painter.drawEllipse(cx + px - ps, cy + py - ps, ps * 2, ps * 2)
                    painter.setPen(QtGui.QPen(QtGui.QColor(p_color), 1))
                    painter.drawLine(cx + px, cy + py, cx + px + ps*2, cy + py + ps*2)
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.drawEllipse(cx + px + ps, cy + py + ps, ps * 2, ps * 2)
                elif i % 8 == 5:
                    # Sine wave (data visualization)
                    painter.setPen(QtGui.QPen(QtGui.QColor(p_color), 2))
                    wave_path = QtGui.QPainterPath()
                    wave_path.moveTo(cx + px - ps*2, cy + py)
                    for wx in range(-ps*2, ps*2, 2):
                        wy = ps * math.sin(wx * 0.3)
                        wave_path.lineTo(cx + px + wx, cy + py + wy)
                    painter.drawPath(wave_path)
                    painter.setPen(QtCore.Qt.NoPen)
                else:
                    # Atom with electron cloud
                    painter.setBrush(QtGui.QColor(p_color))
                    painter.drawEllipse(cx + px - ps, cy + py - ps, ps * 2, ps * 2)
                    painter.setPen(QtGui.QPen(QtGui.QColor(p_color), 1))
                    painter.drawEllipse(cx + px - ps*2, cy + py - ps//2, ps*4, ps)
                    painter.setPen(QtCore.Qt.NoPen)
            painter.setOpacity(1.0)

        # === CHESTPLATE (Lab Coat - behind body) ===
        coat = self.equipped.get("Chestplate")
        if coat:
            # Pathetic tier has old, dingy gray coat instead of white
            if self.tier == "pathetic":
                cc = QtGui.QColor("#d7ccc8")  # Dingy beige/gray
            else:
                cc = QtGui.QColor(coat.get("color", "#e8e8e8"))  # Default white lab coat
            # Professional lab coat shape
            path = QtGui.QPainterPath()
            path.moveTo(cx - 28, cy - 28)
            path.lineTo(cx + 28, cy - 28)
            path.quadTo(cx + 38, cy, cx + 36, cy + 50)
            path.lineTo(cx + 32, cy + 70)
            path.quadTo(cx, cy + 74, cx - 32, cy + 70)
            path.lineTo(cx - 36, cy + 50)
            path.quadTo(cx - 38, cy, cx - 28, cy - 28)
            # Clean lab coat gradient
            coat_gradient = QtGui.QLinearGradient(cx - 30, cy - 30, cx + 30, cy + 70)
            coat_gradient.setColorAt(0, cc.lighter(108))
            coat_gradient.setColorAt(0.5, cc)
            coat_gradient.setColorAt(1, darken(coat.get("color", "#e8e8e8"), 115))
            painter.setBrush(coat_gradient)
            painter.setPen(QtGui.QPen(darken(coat.get("color", "#e8e8e8"), 125), 2))
            painter.drawPath(path)
            # Lab coat lapels
            painter.setPen(QtGui.QPen(cc.darker(115), 2))
            painter.drawLine(cx - 12, cy - 26, cx - 18, cy + 25)
            painter.drawLine(cx + 12, cy - 26, cx + 18, cy + 25)
            # Lab coat pockets (signature feature)
            painter.setBrush(cc.darker(108))
            painter.drawRect(cx - 26, cy + 28, 14, 12)
            painter.drawRect(cx + 12, cy + 28, 14, 12)
            # Pocket details
            painter.setPen(QtGui.QPen(cc.darker(120), 1))
            painter.drawLine(cx - 26, cy + 30, cx - 12, cy + 30)
            painter.drawLine(cx + 12, cy + 30, cx + 26, cy + 30)
            # Pocket protector with multiple colored pens (iconic scientist accessory)
            if self.tier in ["heroic", "epic", "legendary", "godlike"]:
                # Pocket protector (white plastic)
                painter.setBrush(QtGui.QColor("#f5f5f5"))
                painter.setPen(QtGui.QPen(QtGui.QColor("#bdbdbd"), 1))
                painter.drawRect(cx - 26, cy + 20, 14, 18)
                # Red pen
                painter.setBrush(QtGui.QColor("#e53935"))
                painter.setPen(QtGui.QPen(QtGui.QColor("#c62828"), 1))
                painter.drawRect(cx - 24, cy + 22, 2, 8)
                painter.drawEllipse(cx - 24, cy + 21, 2, 2)
                # Blue pen
                painter.setBrush(QtGui.QColor("#1976d2"))
                painter.setPen(QtGui.QPen(QtGui.QColor("#0d47a1"), 1))
                painter.drawRect(cx - 21, cy + 24, 2, 8)
                painter.drawEllipse(cx - 21, cy + 23, 2, 2)
                # Green pen
                painter.setBrush(QtGui.QColor("#43a047"))
                painter.setPen(QtGui.QPen(QtGui.QColor("#2e7d32"), 1))
                painter.drawRect(cx - 18, cy + 22, 2, 8)
                painter.drawEllipse(cx - 18, cy + 21, 2, 2)
            elif self.tier in ["decent"]:
                # Single pen for decent tier
                painter.setBrush(QtGui.QColor("#1976d2"))
                painter.setPen(QtGui.QPen(QtGui.QColor("#0d47a1"), 1))
                painter.drawRect(cx - 24, cy + 22, 3, 8)
                painter.drawEllipse(cx - 24, cy + 20, 3, 3)
            # Lab coat stains for lower tiers (realistic research struggle)
            if self.tier == "pathetic":
                # VERY stained and worn coat - multiple large stains
                painter.setOpacity(0.6)
                painter.setBrush(QtGui.QColor("#8b4513"))
                painter.setPen(QtCore.Qt.NoPen)
                # Large coffee stain on chest
                painter.drawEllipse(cx + 12, cy - 10, 10, 10)
                painter.drawEllipse(cx - 10, cy + 5, 8, 8)
                # Chemical splash marks (multiple)
                painter.setBrush(QtGui.QColor("#ff6b6b"))
                painter.drawEllipse(cx - 22, cy + 15, 6, 6)
                painter.drawEllipse(cx - 18, cy + 20, 5, 5)
                painter.drawEllipse(cx + 18, cy + 35, 7, 7)
                # Ink stain
                painter.setBrush(QtGui.QColor("#1a237e"))
                painter.drawEllipse(cx - 20, cy - 5, 5, 8)
                # Mystery yellow stain
                painter.setBrush(QtGui.QColor("#fbc02d"))
                painter.drawEllipse(cx + 20, cy + 25, 6, 6)
                painter.setOpacity(1.0)
            elif self.tier == "modest":
                # Moderately stained
                painter.setOpacity(0.5)
                painter.setBrush(QtGui.QColor("#8b4513"))
                painter.setPen(QtCore.Qt.NoPen)
                # Coffee stains
                painter.drawEllipse(cx + 14, cy - 8, 7, 7)
                painter.drawEllipse(cx - 12, cy + 8, 5, 5)
                # Chemical splash marks
                painter.setBrush(QtGui.QColor("#ff6b6b"))
                painter.drawEllipse(cx - 18, cy + 15, 5, 5)
                painter.drawEllipse(cx - 16, cy + 18, 4, 4)
                painter.setOpacity(1.0)

        # === CLOAK (Hazmat Suit overlay for high-tier containment) ===
        cloak = self.equipped.get("Cloak")
        if cloak:
            cloak_c = QtGui.QColor(cloak.get("color", "#ffeb3b"))  # Yellow hazmat default
            painter.setOpacity(0.35)
            # Transparent hazmat suit overlay
            hazmat_grad = QtGui.QLinearGradient(cx - 35, cy - 30, cx + 35, cy + 60)
            hazmat_grad.setColorAt(0, cloak_c.lighter(120))
            hazmat_grad.setColorAt(0.5, cloak_c)
            hazmat_grad.setColorAt(1, cloak_c.darker(110))
            painter.setBrush(hazmat_grad)
            painter.setPen(QtGui.QPen(cloak_c.darker(130), 2))
            # Hazmat suit shape (wider than lab coat, more protective)
            hazmat_path = QtGui.QPainterPath()
            hazmat_path.moveTo(cx - 32, cy - 30)
            hazmat_path.lineTo(cx + 32, cy - 30)
            hazmat_path.quadTo(cx + 42, cy, cx + 40, cy + 55)
            hazmat_path.lineTo(cx + 36, cy + 72)
            hazmat_path.quadTo(cx, cy + 76, cx - 36, cy + 72)
            hazmat_path.lineTo(cx - 40, cy + 55)
            hazmat_path.quadTo(cx - 42, cy, cx - 32, cy - 30)
            hazmat_path.closeSubpath()
            painter.drawPath(hazmat_path)
            painter.setOpacity(1.0)
            # Hazmat suit seams/details
            painter.setOpacity(0.6)
            painter.setPen(QtGui.QPen(cloak_c.darker(140), 2))
            painter.drawLine(cx - 30, cy - 28, cx - 32, cy + 70)
            painter.drawLine(cx + 30, cy - 28, cx + 32, cy + 70)
            painter.drawLine(cx, cy - 28, cx, cy + 70)
            # Hazmat zipper
            painter.setPen(QtGui.QPen(QtGui.QColor("#455a64"), 2))
            for z in range(cy - 26, cy + 70, 8):
                painter.drawLine(cx - 2, z, cx + 2, z)
            painter.setOpacity(1.0)
            # Warning stripes (biohazard theme)
            painter.setOpacity(0.5)
            painter.setBrush(QtGui.QColor("#ff5722"))
            painter.setPen(QtCore.Qt.NoPen)
            for stripe in range(3):
                y_pos = cy + 15 + stripe * 20
                painter.drawRect(cx - 38, y_pos, 76, 4)
            painter.setOpacity(1.0)

        # === LEGS (Dress pants/Slacks) ===
        pants_color = QtGui.QColor("#2c3e50")
        pants_grad = QtGui.QLinearGradient(cx - 20, cy + 25, cx + 20, cy + 25)
        pants_grad.setColorAt(0, pants_color.darker(118))
        pants_grad.setColorAt(0.5, pants_color)
        pants_grad.setColorAt(1, pants_color.darker(118))
        painter.setBrush(pants_grad)
        painter.setPen(QtGui.QPen(pants_color.darker(145), 2))
        # Left leg
        left_leg = QtGui.QPainterPath()
        left_leg.moveTo(cx - 20, cy + 25)
        left_leg.lineTo(cx - 5, cy + 25)
        left_leg.lineTo(cx - 7, cy + 62)
        left_leg.lineTo(cx - 22, cy + 62)
        left_leg.closeSubpath()
        painter.drawPath(left_leg)
        # Right leg
        right_leg = QtGui.QPainterPath()
        right_leg.moveTo(cx + 5, cy + 25)
        right_leg.lineTo(cx + 20, cy + 25)
        right_leg.lineTo(cx + 22, cy + 62)
        right_leg.lineTo(cx + 7, cy + 62)
        right_leg.closeSubpath()
        painter.drawPath(right_leg)

        # === BOOTS (Comfortable sneakers - not dress shoes!) ===
        boots = self.equipped.get("Boots")
        if boots:
            bc = QtGui.QColor(boots.get("color", "#34495e"))
            boot_grad = QtGui.QLinearGradient(0, cy + 58, 0, cy + 78)
            boot_grad.setColorAt(0, bc.lighter(130))
            boot_grad.setColorAt(0.5, bc)
            boot_grad.setColorAt(1, bc.darker(118))
            painter.setBrush(boot_grad)
            painter.setPen(QtGui.QPen(bc.darker(135), 2))
            # Left sneaker - athletic style
            left_shoe = QtGui.QPainterPath()
            left_shoe.moveTo(cx - 24, cy + 62)
            left_shoe.lineTo(cx - 5, cy + 62)
            left_shoe.lineTo(cx - 3, cy + 72)
            left_shoe.quadTo(cx - 10, cy + 77, cx - 20, cy + 76)
            left_shoe.quadTo(cx - 27, cy + 72, cx - 26, cy + 65)
            left_shoe.closeSubpath()
            painter.drawPath(left_shoe)
            # Right sneaker
            right_shoe = QtGui.QPainterPath()
            right_shoe.moveTo(cx + 5, cy + 62)
            right_shoe.lineTo(cx + 24, cy + 62)
            right_shoe.quadTo(cx + 27, cy + 68, cx + 26, cy + 72)
            right_shoe.quadTo(cx + 20, cy + 77, cx + 10, cy + 76)
            right_shoe.lineTo(cx + 3, cy + 72)
            right_shoe.closeSubpath()
            painter.drawPath(right_shoe)
            # Sneaker details (rubber sole, laces)
            # Rubber sole stripe
            painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 2))
            painter.drawLine(cx - 24, cy + 70, cx - 6, cy + 72)
            painter.drawLine(cx + 6, cy + 72, cx + 24, cy + 70)
            # Laces
            painter.setPen(QtGui.QPen(bc.darker(150), 1))
            for lace_x in range(-18, -8, 4):
                painter.drawLine(cx + lace_x, cy + 64, cx + lace_x + 3, cy + 66)
            for lace_x in range(10, 20, 4):
                painter.drawLine(cx + lace_x, cy + 64, cx + lace_x + 3, cy + 66)
        else:
            # Basic sneakers
            painter.setBrush(QtGui.QColor("#546e7a"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#37474f"), 1))
            painter.drawRoundedRect(cx - 24, cy + 60, 19, 17, 6, 6)
            painter.drawRoundedRect(cx + 5, cy + 60, 19, 17, 6, 6)
            # White rubber sole
            painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 2))
            painter.drawLine(cx - 22, cy + 72, cx - 8, cy + 74)
            painter.drawLine(cx + 7, cy + 74, cx + 21, cy + 72)

        # === ARMS (Shirt sleeves under lab coat) ===
        shirt_color = QtGui.QColor("#74b9ff")
        arm_grad_l = QtGui.QLinearGradient(cx - 44, cy - 5, cx - 28, cy - 5)
        arm_grad_l.setColorAt(0, shirt_color.darker(125))
        arm_grad_l.setColorAt(0.5, shirt_color)
        arm_grad_l.setColorAt(1, shirt_color.darker(108))
        painter.setBrush(arm_grad_l)
        painter.setPen(QtGui.QPen(shirt_color.darker(145), 2))
        # Left arm
        left_arm = QtGui.QPainterPath()
        left_arm.moveTo(cx - 28, cy - 24)
        left_arm.quadTo(cx - 36, cy - 22, cx - 42, cy - 12)
        left_arm.quadTo(cx - 48, cy + 6, cx - 46, cy + 26)
        left_arm.lineTo(cx - 34, cy + 23)
        left_arm.quadTo(cx - 32, cy - 4, cx - 28, cy - 24)
        painter.drawPath(left_arm)
        # Right arm
        arm_grad_r = QtGui.QLinearGradient(cx + 28, cy - 5, cx + 44, cy - 5)
        arm_grad_r.setColorAt(0, shirt_color.darker(108))
        arm_grad_r.setColorAt(0.5, shirt_color)
        arm_grad_r.setColorAt(1, shirt_color.darker(125))
        painter.setBrush(arm_grad_r)
        right_arm = QtGui.QPainterPath()
        right_arm.moveTo(cx + 28, cy - 24)
        right_arm.quadTo(cx + 36, cy - 22, cx + 42, cy - 12)
        right_arm.quadTo(cx + 48, cy + 6, cx + 46, cy + 26)
        right_arm.lineTo(cx + 34, cy + 23)
        right_arm.quadTo(cx + 32, cy - 4, cx + 28, cy - 24)
        painter.drawPath(right_arm)

        # === GAUNTLETS (Latex Gloves) ===
        gaunt = self.equipped.get("Gauntlets")
        # Pathetic tier has no gloves - too expensive
        if self.tier == "pathetic":
            gaunt = None
        if gaunt:
            gc = QtGui.QColor(gaunt.get("color", "#b0e0ff"))  # Light blue latex default
            # Left glove
            painter.setBrush(gc)
            painter.setPen(QtGui.QPen(gc.darker(125), 1))
            left_hand = QtGui.QPainterPath()
            left_hand.moveTo(cx - 48, cy + 18)
            left_hand.quadTo(cx - 52, cy + 22, cx - 50, cy + 28)
            left_hand.quadTo(cx - 46, cy + 30, cx - 44, cy + 26)
            left_hand.quadTo(cx - 44, cy + 20, cx - 48, cy + 18)
            painter.drawPath(left_hand)
            # Glove cuff
            painter.drawRect(cx - 49, cy + 15, 10, 6)
            # Right glove
            right_hand = QtGui.QPainterPath()
            right_hand.moveTo(cx + 48, cy + 18)
            right_hand.quadTo(cx + 52, cy + 22, cx + 50, cy + 28)
            right_hand.quadTo(cx + 46, cy + 30, cx + 44, cy + 26)
            right_hand.quadTo(cx + 44, cy + 20, cx + 48, cy + 18)
            painter.drawPath(right_hand)
            painter.drawRect(cx + 39, cy + 15, 10, 6)
        else:
            # Bare hands
            painter.setBrush(QtGui.QColor("#e6c8a0"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#c9a066"), 1))
            painter.drawEllipse(cx - 48, cy + 17, 15, 13)
            painter.drawEllipse(cx + 33, cy + 17, 15, 13)

        # === TORSO (Casual untucked shirt under lab coat) ===
        torso_grad = QtGui.QLinearGradient(cx - 26, cy, cx + 26, cy)
        torso_grad.setColorAt(0, shirt_color.darker(112))
        torso_grad.setColorAt(0.3, shirt_color)
        torso_grad.setColorAt(0.7, shirt_color)
        torso_grad.setColorAt(1, shirt_color.darker(112))
        painter.setBrush(torso_grad)
        painter.setPen(QtGui.QPen(shirt_color.darker(145), 2))
        torso_path = QtGui.QPainterPath()
        torso_path.moveTo(cx - 26, cy - 28)
        torso_path.quadTo(cx - 28, cy - 7, cx - 20, cy + 28)
        torso_path.lineTo(cx + 20, cy + 28)
        torso_path.quadTo(cx + 28, cy - 7, cx + 26, cy - 28)
        torso_path.closeSubpath()
        painter.drawPath(torso_path)

        # === CHEST LAYER (Casual T-shirt or polo - NO TIE) ===
        cc = QtGui.QColor("#7e57c2") if self.tier in ["pathetic", "modest"] else QtGui.QColor("#3498db")
        chest_grad = QtGui.QLinearGradient(cx - 22, cy - 26, cx + 22, cy + 22)
        chest_grad.setColorAt(0, cc.lighter(118))
        chest_grad.setColorAt(0.5, cc)
        chest_grad.setColorAt(1, cc.darker(112))
        painter.setBrush(chest_grad)
        painter.setPen(QtGui.QPen(cc.darker(135), 2))
        # Casual shirt (untucked, wrinkled appearance)
        shirt_path = QtGui.QPainterPath()
        shirt_path.moveTo(cx - 22, cy - 26)
        shirt_path.quadTo(cx, cy - 30, cx + 22, cy - 26)
        # Untucked bottom edge showing below lab coat opening
        shirt_path.lineTo(cx + 18, cy + 26)
        shirt_path.quadTo(cx + 12, cy + 30, cx, cy + 31)  # Hanging out
        shirt_path.quadTo(cx - 12, cy + 30, cx - 18, cy + 26)
        shirt_path.closeSubpath()
        painter.drawPath(shirt_path)
        # Simple V-neck collar (casual, not button-down)
        painter.setPen(QtGui.QPen(cc.darker(125), 2))
        painter.drawLine(cx - 9, cy - 26, cx, cy - 22)
        painter.drawLine(cx + 9, cy - 26, cx, cy - 22)
        # NO TIE - scientists are casual!
        # Wrinkle lines for realism
        painter.setOpacity(0.3)
        painter.setPen(QtGui.QPen(cc.darker(120), 1))
        painter.drawLine(cx - 12, cy - 8, cx + 10, cy - 6)
        painter.drawLine(cx - 8, cy + 4, cx + 12, cy + 6)
        painter.setOpacity(1.0)

        # === SHIELD (Lab Notebook / Data Tablet) ===
        shield = self.equipped.get("Shield")
        if shield:
            sc = QtGui.QColor(shield.get("color", "#37474f"))  # Dark gray notebook default
            # Notebook/tablet held at side
            notebook_grad = QtGui.QLinearGradient(cx + 32, cy - 8, cx + 44, cy + 12)
            notebook_grad.setColorAt(0, sc.lighter(115))
            notebook_grad.setColorAt(0.5, sc)
            notebook_grad.setColorAt(1, sc.darker(115))
            painter.setBrush(notebook_grad)
            painter.setPen(QtGui.QPen(sc.darker(140), 2))
            # Notebook rectangle
            painter.drawRoundedRect(cx + 32, cy - 8, 16, 22, 2, 2)
            # Notebook binding/spine
            painter.setPen(QtGui.QPen(sc.darker(150), 3))
            painter.drawLine(cx + 33, cy - 8, cx + 33, cy + 14)
            # Page lines (scientific notes)
            painter.setPen(QtGui.QPen(sc.lighter(140), 1))
            for line_y in range(cy - 6, cy + 13, 3):
                painter.drawLine(cx + 35, line_y, cx + 46, line_y)
            # Digital variant for epic+ tiers
            if self.tier in ["epic", "legendary", "godlike"]:
                # Glowing screen effect
                painter.setOpacity(0.6)
                screen_glow = QtGui.QRadialGradient(cx + 40, cy + 3, 12)
                screen_glow.setColorAt(0, QtGui.QColor("#4fc3f7"))
                screen_glow.setColorAt(1, QtGui.QColor("#0277bd"))
                painter.setBrush(screen_glow)
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawRoundedRect(cx + 34, cy - 6, 12, 18, 1, 1)
                painter.setOpacity(1.0)
                # Digital data symbols
                painter.setPen(QtGui.QPen(QtGui.QColor("#e0f7ff"), 1))
                painter.drawText(cx + 36, cy - 2, "01")
                painter.drawText(cx + 36, cy + 4, "10")
                painter.drawText(cx + 36, cy + 10, "11")

        # === WEAPON (Scientific Instrument) ===
        weap = self.equipped.get("Weapon")
        if weap:
            wc = QtGui.QColor(weap.get("color", "#78909c"))  # Steel-gray instrument default
            # Instrument held in left hand (microscope, spectrometer, pipette design)
            # Handle/grip
            handle_grad = QtGui.QLinearGradient(cx - 50, cy + 5, cx - 46, cy + 20)
            handle_grad.setColorAt(0, QtGui.QColor("#546e7a"))
            handle_grad.setColorAt(0.5, QtGui.QColor("#607d8b"))
            handle_grad.setColorAt(1, QtGui.QColor("#455a64"))
            painter.setBrush(handle_grad)
            painter.setPen(QtGui.QPen(QtGui.QColor("#37474f"), 2))
            painter.drawRoundedRect(cx - 54, cy + 8, 8, 24, 3, 3)
            # Grip texture
            painter.setPen(QtGui.QPen(QtGui.QColor("#455a64"), 1))
            for grip_line in range(cy + 10, cy + 30, 4):
                painter.drawLine(cx - 54, grip_line, cx - 46, grip_line)
            # Instrument body (varies by tier)
            body_grad = QtGui.QLinearGradient(cx - 52, cy - 12, cx - 44, cy + 8)
            body_grad.setColorAt(0, wc.lighter(125))
            body_grad.setColorAt(0.3, wc)
            body_grad.setColorAt(1, wc.darker(115))
            painter.setBrush(body_grad)
            painter.setPen(QtGui.QPen(wc.darker(135), 2))
            if self.tier in ["legendary", "godlike"]:
                # Advanced quantum analyzer
                painter.drawRoundedRect(cx - 58, cy - 14, 16, 22, 3, 3)
                # Glowing display panel
                painter.setOpacity(0.7)
                panel_glow = QtGui.QRadialGradient(cx - 50, cy - 3, 8)
                panel_glow.setColorAt(0, QtGui.QColor("#00e676"))
                panel_glow.setColorAt(1, QtGui.QColor("#00c853"))
                painter.setBrush(panel_glow)
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawRect(cx - 56, cy - 10, 12, 14)
                painter.setOpacity(1.0)
                # Digital readout
                painter.setPen(QtGui.QPen(QtGui.QColor("#e0f7ff"), 1))
                painter.drawText(cx - 54, cy - 4, "99.9%")
                # Antenna/sensor array
                painter.setPen(QtGui.QPen(wc, 2))
                painter.drawLine(cx - 50, cy - 14, cx - 50, cy - 22)
                painter.drawEllipse(cx - 52, cy - 24, 4, 4)
            elif self.tier in ["epic", "heroic"]:
                # Precision spectrometer
                painter.drawRoundedRect(cx - 56, cy - 12, 14, 20, 2, 2)
                # Lens/measurement window
                painter.setBrush(QtGui.QColor("#4fc3f7"))
                painter.setPen(QtGui.QPen(QtGui.QColor("#0277bd"), 1))
                painter.drawEllipse(cx - 53, cy - 8, 8, 8)
                # Measurement dial
                painter.setPen(QtGui.QPen(wc.darker(130), 1))
                painter.drawArc(cx - 52, cy - 7, 6, 6, 0, 270 * 16)
                painter.drawLine(cx - 49, cy - 4, cx - 46, cy - 4)
            else:
                # Basic microscope/pipette
                painter.drawRoundedRect(cx - 54, cy - 10, 12, 18, 2, 2)
                # Measurement marks
                painter.setPen(QtGui.QPen(wc.darker(140), 1))
                for mark in range(cy - 8, cy + 6, 3):
                    painter.drawLine(cx - 54, mark, cx - 50, mark)
                # Glass tip (pipette style)
                painter.setBrush(QtGui.QColor("#b0e0ff"))
                painter.setPen(QtGui.QPen(QtGui.QColor("#4fc3f7"), 1))
                tip_path = QtGui.QPainterPath()
                tip_path.moveTo(cx - 51, cy + 8)
                tip_path.lineTo(cx - 49, cy + 8)
                tip_path.lineTo(cx - 49, cy + 16)
                tip_path.lineTo(cx - 50, cy + 18)
                tip_path.lineTo(cx - 51, cy + 16)
                tip_path.closeSubpath()
                painter.drawPath(tip_path)
                # Liquid drop at tip for realism
                if self.tier in ["decent", "modest", "heroic"]:
                    painter.setBrush(QtGui.QColor("#1976d2"))
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.drawEllipse(cx - 51, cy + 18, 2, 3)

        # === NECK ===
        neck_grad = QtGui.QLinearGradient(cx - 9, cy - 34, cx + 9, cy - 34)
        neck_grad.setColorAt(0, QtGui.QColor("#d4b090"))
        neck_grad.setColorAt(0.5, QtGui.QColor("#e6c8a0"))
        neck_grad.setColorAt(1, QtGui.QColor("#d4b090"))
        painter.setBrush(neck_grad)
        painter.setPen(QtGui.QPen(QtGui.QColor("#c49a70"), 1))
        painter.drawRect(cx - 9, cy - 36, 18, 13)

        # === HEAD ===
        head_gradient = QtGui.QRadialGradient(cx - 5, cy - 54, 30)
        head_gradient.setColorAt(0, QtGui.QColor("#f5e0c8"))
        head_gradient.setColorAt(0.5, QtGui.QColor("#e6c8a0"))
        head_gradient.setColorAt(0.8, QtGui.QColor("#d4a870"))
        head_gradient.setColorAt(1, QtGui.QColor("#c49060"))
        painter.setBrush(head_gradient)
        painter.setPen(QtGui.QPen(QtGui.QColor("#b08050"), 2))
        head_path = QtGui.QPainterPath()
        head_path.moveTo(cx - 2, cy - 32)
        head_path.quadTo(cx - 22, cy - 35, cx - 22, cy - 52)
        head_path.quadTo(cx - 22, cy - 72, cx, cy - 72)
        head_path.quadTo(cx + 22, cy - 72, cx + 22, cy - 52)
        head_path.quadTo(cx + 22, cy - 35, cx + 2, cy - 32)
        head_path.closeSubpath()
        painter.drawPath(head_path)

        # === HELMET (Safety Goggles) ===
        helm = self.equipped.get("Helmet")
        # Pathetic tier can't afford goggles - force to basic appearance
        if self.tier == "pathetic":
            helm = None
        if helm:
            hc = QtGui.QColor(helm.get("color", "#4db8ff"))  # Light blue goggles default
            # Goggles strap
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.setPen(QtGui.QPen(hc.darker(140), 3))
            painter.drawArc(cx - 24, cy - 75, 48, 32, 0, 180 * 16)
            # Left goggle lens
            painter.setBrush(hc)
            painter.setPen(QtGui.QPen(hc.darker(135), 2))
            painter.drawEllipse(cx - 24, cy - 58, 14, 12)
            # Lens reflection
            lens_grad_l = QtGui.QRadialGradient(cx - 19, cy - 54, 7)
            lens_grad_l.setColorAt(0, QtGui.QColor("#e0f7ff"))
            lens_grad_l.setColorAt(0.7, hc)
            lens_grad_l.setColorAt(1, hc.darker(125))
            painter.setBrush(lens_grad_l)
            painter.drawEllipse(cx - 23, cy - 57, 12, 10)
            # Right goggle lens
            painter.setBrush(hc)
            painter.setPen(QtGui.QPen(hc.darker(135), 2))
            painter.drawEllipse(cx + 10, cy - 58, 14, 12)
            lens_grad_r = QtGui.QRadialGradient(cx + 15, cy - 54, 7)
            lens_grad_r.setColorAt(0, QtGui.QColor("#e0f7ff"))
            lens_grad_r.setColorAt(0.7, hc)
            lens_grad_r.setColorAt(1, hc.darker(125))
            painter.setBrush(lens_grad_r)
            painter.drawEllipse(cx + 11, cy - 57, 12, 10)
            # Bridge
            painter.setPen(QtGui.QPen(hc.darker(140), 3))
            painter.drawLine(cx - 10, cy - 52, cx + 10, cy - 52)
            # Messy Einstein-style hair showing above goggles
            hair_color = QtGui.QColor("#4a3728") if self.tier not in ["legendary", "godlike"] else QtGui.QColor("#9e9e9e")  # Gray for Nobel tier
            hair_grad = QtGui.QRadialGradient(cx, cy - 67, 24)
            hair_grad.setColorAt(0, hair_color.lighter(125))
            hair_grad.setColorAt(0.6, hair_color)
            hair_grad.setColorAt(1, hair_color.darker(118))
            painter.setBrush(hair_grad)
            painter.setPen(QtCore.Qt.NoPen)
            # Messy hairstyle with wild spikes above goggles
            hair_path = QtGui.QPainterPath()
            hair_path.moveTo(cx - 22, cy - 57)
            # Left side spike
            hair_path.quadTo(cx - 28, cy - 70, cx - 24, cy - 82)
            hair_path.quadTo(cx - 18, cy - 85, cx - 14, cy - 80)
            # Center spike (Einstein wild hair)
            hair_path.quadTo(cx - 8, cy - 86, cx, cy - 88)
            hair_path.quadTo(cx + 8, cy - 86, cx + 14, cy - 80)
            # Right side spike
            hair_path.quadTo(cx + 18, cy - 85, cx + 24, cy - 82)
            hair_path.quadTo(cx + 28, cy - 70, cx + 22, cy - 57)
            hair_path.lineTo(cx + 10, cy - 58)
            hair_path.lineTo(cx - 10, cy - 58)
            hair_path.closeSubpath()
            painter.drawPath(hair_path)
            # Add individual hair strands sticking up
            painter.setPen(QtGui.QPen(hair_color.darker(130), 2))
            painter.drawLine(cx - 16, cy - 78, cx - 18, cy - 84)
            painter.drawLine(cx - 6, cy - 82, cx - 4, cy - 88)
            painter.drawLine(cx + 6, cy - 82, cx + 8, cy - 88)
            painter.drawLine(cx + 16, cy - 78, cx + 18, cy - 84)
            painter.setPen(QtCore.Qt.NoPen)
        else:
            # Messy Einstein-style hair (no goggles)
            hair_color = QtGui.QColor("#4a3728") if self.tier not in ["legendary", "godlike"] else QtGui.QColor("#9e9e9e")
            hair_grad = QtGui.QRadialGradient(cx, cy - 67, 24)
            hair_grad.setColorAt(0, hair_color.lighter(125))
            hair_grad.setColorAt(0.6, hair_color)
            hair_grad.setColorAt(1, hair_color.darker(118))
            painter.setBrush(hair_grad)
            painter.setPen(QtCore.Qt.NoPen)
            # Wild, unkempt hair
            hair_path = QtGui.QPainterPath()
            hair_path.moveTo(cx - 22, cy - 57)
            # Left spike
            hair_path.quadTo(cx - 28, cy - 72, cx - 24, cy - 84)
            hair_path.quadTo(cx - 16, cy - 87, cx - 10, cy - 82)
            # Center wild tuft
            hair_path.quadTo(cx - 6, cy - 88, cx, cy - 90)
            hair_path.quadTo(cx + 6, cy - 88, cx + 10, cy - 82)
            # Right spike
            hair_path.quadTo(cx + 16, cy - 87, cx + 24, cy - 84)
            hair_path.quadTo(cx + 28, cy - 72, cx + 22, cy - 57)
            hair_path.quadTo(cx + 20, cy - 60, cx + 14, cy - 64)
            hair_path.quadTo(cx, cy - 68, cx - 14, cy - 64)
            hair_path.quadTo(cx - 20, cy - 60, cx - 22, cy - 57)
            painter.drawPath(hair_path)
            # Wild side tufts
            painter.drawEllipse(cx - 26, cy - 62, 7, 16)
            painter.drawEllipse(cx + 19, cy - 62, 7, 16)
            # Individual strands
            painter.setPen(QtGui.QPen(hair_color.darker(130), 2))
            painter.drawLine(cx - 18, cy - 80, cx - 20, cy - 86)
            painter.drawLine(cx - 8, cy - 84, cx - 6, cy - 90)
            painter.drawLine(cx + 8, cy - 84, cx + 10, cy - 90)
            painter.drawLine(cx + 18, cy - 80, cx + 20, cy - 86)
            painter.setPen(QtCore.Qt.NoPen)

        # === FACE ===
        # Stubble for low-tier scientists (too busy to shave)
        if self.tier in ["pathetic", "modest"]:
            painter.setOpacity(0.4)
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QColor("#3e2723"))
            # Stippled beard effect
            for stubble_y in range(cy - 38, cy - 32, 2):
                for stubble_x in range(cx - 14, cx + 14, 2):
                    if (stubble_x + stubble_y) % 3 == 0:
                        painter.drawEllipse(stubble_x, stubble_y, 1, 1)
            painter.setOpacity(1.0)
        
        # Face mask hanging around neck (iconic scientist accessory)
        painter.setOpacity(0.7)
        painter.setBrush(QtGui.QColor("#e3f2fd"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#90caf9"), 1))
        # Mask hanging loose
        mask_path = QtGui.QPainterPath()
        mask_path.moveTo(cx - 14, cy - 30)
        mask_path.quadTo(cx - 16, cy - 26, cx - 12, cy - 24)
        mask_path.lineTo(cx + 12, cy - 24)
        mask_path.quadTo(cx + 16, cy - 26, cx + 14, cy - 30)
        mask_path.closeSubpath()
        painter.drawPath(mask_path)
        # Elastic straps
        painter.setPen(QtGui.QPen(QtGui.QColor("#90caf9"), 1))
        painter.drawLine(cx - 14, cy - 28, cx - 20, cy - 36)
        painter.drawLine(cx + 14, cy - 28, cx + 20, cy - 36)
        # Pleats on mask
        painter.drawLine(cx - 8, cy - 27, cx - 8, cy - 25)
        painter.drawLine(cx, cy - 27, cx, cy - 25)
        painter.drawLine(cx + 8, cy - 27, cx + 8, cy - 25)
        painter.setOpacity(1.0)
        
        # Intelligent, focused eyebrows
        painter.setPen(QtGui.QPen(QtGui.QColor("#4a3728"), 2))
        if self.tier in ["legendary", "godlike"]:
            # Confident scientist brows
            painter.drawLine(cx - 13, cy - 59, cx - 5, cy - 61)
            painter.drawLine(cx + 5, cy - 61, cx + 13, cy - 59)
        elif self.tier in ["epic", "heroic"]:
            # Focused researcher brows
            painter.drawLine(cx - 13, cy - 58, cx - 5, cy - 59)
            painter.drawLine(cx + 5, cy - 59, cx + 13, cy - 58)
        else:
            # Thoughtful brows
            painter.drawLine(cx - 12, cy - 57, cx - 5, cy - 58)
            painter.drawLine(cx + 5, cy - 58, cx + 12, cy - 57)
        
        # Eyes (intelligent, observant, slightly squinted from screen work) - positioned lower when wearing goggles
        eye_y = cy - 52 if not helm else cy - 50
        painter.setBrush(QtGui.QColor("#e8dcc8"))
        painter.setPen(QtCore.Qt.NoPen)
        # Slightly narrower eyes (squinting)
        painter.drawEllipse(cx - 13, eye_y + 1, 11, 8)
        painter.drawEllipse(cx + 2, eye_y + 1, 11, 8)
        # Eye whites
        painter.setBrush(QtGui.QColor("#fff"))
        painter.drawEllipse(cx - 12, eye_y + 1, 9, 9)
        painter.drawEllipse(cx + 3, eye_y + 1, 9, 9)
        # Iris (scientific colors - deep blue for intelligence)
        iris_colors = {
            "pathetic": "#795548", "modest": "#6d4c41", "decent": "#5d4037",
            "heroic": "#1976d2", "epic": "#1565c0", "legendary": "#0d47a1", "godlike": "#01579b"
        }
        iris_color = QtGui.QColor(iris_colors.get(self.tier, "#6d4c41"))
        iris_grad = QtGui.QRadialGradient(cx - 8, eye_y + 4, 5)
        iris_grad.setColorAt(0, iris_color.lighter(135))
        iris_grad.setColorAt(1, iris_color)
        painter.setBrush(iris_grad)
        painter.drawEllipse(cx - 10, eye_y + 2, 7, 7)
        iris_grad2 = QtGui.QRadialGradient(cx + 7, eye_y + 4, 5)
        iris_grad2.setColorAt(0, iris_color.lighter(135))
        iris_grad2.setColorAt(1, iris_color)
        painter.setBrush(iris_grad2)
        painter.drawEllipse(cx + 5, eye_y + 2, 7, 7)
        # Pupils
        painter.setBrush(QtGui.QColor("#1a1a1a"))
        painter.drawEllipse(cx - 8, eye_y + 3, 3, 3)
        painter.drawEllipse(cx + 6, eye_y + 3, 3, 3)
        # Eye shine (intelligence sparkle)
        painter.setBrush(QtGui.QColor("#fff"))
        painter.drawEllipse(cx - 9, eye_y + 3, 2, 2)
        painter.drawEllipse(cx + 5, eye_y + 3, 2, 2)
        # Under-eye bags/circles for tired low-tier scientists
        if self.tier == "pathetic":
            # VERY dark, puffy bags - severe exhaustion
            painter.setOpacity(0.6)
            painter.setBrush(QtGui.QColor("#5d4037"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 13, eye_y + 8, 11, 6)
            painter.drawEllipse(cx + 2, eye_y + 8, 11, 6)
            painter.setOpacity(1.0)
            # Eye fatigue redness - severe
            painter.setOpacity(0.4)
            painter.setPen(QtGui.QPen(QtGui.QColor("#ff6b6b"), 2))
            painter.drawLine(cx - 10, eye_y + 2, cx - 6, eye_y + 4)
            painter.drawLine(cx + 5, eye_y + 2, cx + 9, eye_y + 4)
            painter.drawLine(cx - 11, eye_y + 4, cx - 8, eye_y + 6)
            painter.drawLine(cx + 6, eye_y + 4, cx + 10, eye_y + 6)
            painter.setOpacity(1.0)
        elif self.tier == "modest":
            # Moderate bags
            painter.setOpacity(0.4)
            painter.setBrush(QtGui.QColor("#8b7355"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 13, eye_y + 8, 11, 4)
            painter.drawEllipse(cx + 2, eye_y + 8, 11, 4)
            painter.setOpacity(1.0)

        # Nose
        painter.setPen(QtGui.QPen(QtGui.QColor("#c49060"), 1))
        painter.drawLine(cx, cy - 46, cx - 1, cy - 40)
        painter.drawArc(cx - 4, cy - 40, 4, 3, 180 * 16, 180 * 16)
        painter.drawArc(cx, cy - 40, 4, 3, 180 * 16, 180 * 16)

        # Mouth (thoughtful, determined expressions)
        painter.setPen(QtGui.QPen(QtGui.QColor("#a06050"), 2))
        if self.tier in ["legendary", "godlike"]:
            # Satisfied breakthrough smile
            painter.drawArc(cx - 11, cy - 42, 22, 13, 210 * 16, 120 * 16)
            painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 1))
            painter.drawLine(cx - 7, cy - 34, cx + 7, cy - 34)
        elif self.tier in ["epic", "heroic"]:
            # Confident researcher smile
            painter.drawArc(cx - 9, cy - 40, 18, 9, 220 * 16, 100 * 16)
        elif self.tier == "decent":
            # Slight smile of progress
            painter.drawArc(cx - 7, cy - 38, 14, 7, 220 * 16, 100 * 16)
        elif self.tier == "modest":
            # Slight frown of frustration
            painter.drawArc(cx - 6, cy - 38, 12, 6, 30 * 16, 120 * 16)
        else:
            # Stressed/worried (pathetic tier)
            painter.drawArc(cx - 7, cy - 38, 14, 8, 20 * 16, 140 * 16)

        # Ears (visible when no goggles or above goggles)
        if not helm:
            painter.setBrush(QtGui.QColor("#e6c8a0"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#c49a70"), 1))
            painter.drawEllipse(cx - 24, cy - 54, 5, 10)
            painter.drawEllipse(cx + 19, cy - 54, 5, 10)

        # === AMULET (ID Badge / Research Credentials) ===
        amulet = self.equipped.get("Amulet")
        if amulet:
            ac = QtGui.QColor(amulet.get("color", "#ffd700"))
            # Lanyard
            painter.setPen(QtGui.QPen(QtGui.QColor("#2c3e50"), 2))
            painter.drawLine(cx - 9, cy - 28, cx - 7, cy - 14)
            painter.drawLine(cx + 9, cy - 28, cx + 7, cy - 14)
            # ID Badge/Credentials
            badge_grad = QtGui.QLinearGradient(cx - 14, cy - 14, cx + 14, cy + 10)
            badge_grad.setColorAt(0, QtGui.QColor("#fff"))
            badge_grad.setColorAt(0.3, QtGui.QColor("#f8f9fa"))
            badge_grad.setColorAt(1, QtGui.QColor("#e9ecef"))
            painter.setBrush(badge_grad)
            painter.setPen(QtGui.QPen(QtGui.QColor("#adb5bd"), 1))
            painter.drawRoundedRect(cx - 14, cy - 14, 28, 32, 3, 3)
            # Photo area
            painter.setBrush(QtGui.QColor("#ced4da"))
            painter.drawRect(cx - 10, cy - 10, 20, 14)
            # Institution logo/seal
            painter.setBrush(ac)
            painter.setPen(QtGui.QPen(ac.darker(130), 1))
            painter.drawEllipse(cx - 5, cy + 6, 10, 10)
            # Logo detail
            painter.setPen(QtGui.QPen(QtGui.QColor("#fff"), 2))
            painter.drawLine(cx - 2, cy + 11, cx + 2, cy + 11)
            painter.drawLine(cx, cy + 9, cx, cy + 13)
            # Barcode for security
            painter.setPen(QtGui.QPen(QtGui.QColor("#212529"), 1))
            for i in range(9):
                x = cx - 9 + i * 2
                painter.drawLine(x, cy + 2, x, cy + 4)
            # Security hologram for high tiers
            if self.tier in ["epic", "legendary", "godlike"]:
                painter.setBrush(QtGui.QColor("#00d9ff"))
                painter.setPen(QtCore.Qt.NoPen)
                painter.setOpacity(0.6)
                painter.drawRect(cx + 8, cy - 12, 4, 4)
                painter.setOpacity(1.0)
            # Nobel Prize indicator for godlike tier
            if self.tier == "godlike":
                painter.setBrush(QtGui.QColor("#ffd700"))
                painter.setPen(QtGui.QPen(QtGui.QColor("#b8860b"), 1))
                painter.drawEllipse(cx - 16, cy - 16, 6, 6)
                # Medal ribbon
                painter.setPen(QtGui.QPen(QtGui.QColor("#0066cc"), 2))
                painter.drawLine(cx - 13, cy - 10, cx - 13, cy - 14)

        # === WEAPON (Microscope/Lab Equipment) ===
        weap = self.equipped.get("Weapon")
        if weap:
            wc = QtGui.QColor(weap.get("color", "#546e7a"))
            # Microscope held in left hand
            # Base
            painter.setBrush(wc.darker(125))
            painter.setPen(QtGui.QPen(wc.darker(145), 2))
            painter.drawRect(cx - 62, cy + 20, 20, 8)
            # Arm/column
            painter.setBrush(wc)
            painter.drawRect(cx - 58, cy - 10, 8, 32)
            # Eyepiece
            microscope_grad = QtGui.QLinearGradient(cx - 60, cy - 18, cx - 48, cy - 10)
            microscope_grad.setColorAt(0, wc.darker(115))
            microscope_grad.setColorAt(0.5, wc)
            microscope_grad.setColorAt(1, wc.lighter(112))
            painter.setBrush(microscope_grad)
            painter.drawEllipse(cx - 62, cy - 18, 12, 10)
            # Lens turret
            painter.setBrush(wc.darker(110))
            painter.drawEllipse(cx - 59, cy + 8, 10, 8)
            # Objective lenses
            painter.setBrush(QtGui.QColor("#37474f"))
            painter.drawRect(cx - 57, cy + 14, 6, 6)
            # Stage (sample platform)
            painter.setBrush(wc.lighter(108))
            painter.drawRect(cx - 60, cy + 10, 14, 3)
            # Focus knobs
            painter.setBrush(QtGui.QColor("#263238"))
            painter.drawEllipse(cx - 48, cy + 8, 5, 5)
            painter.drawEllipse(cx - 48, cy + 14, 5, 5)
            # Light source for high tiers
            if self.tier in ["heroic", "epic", "legendary", "godlike"]:
                light_grad = QtGui.QRadialGradient(cx - 54, cy + 22, 4)
                light_grad.setColorAt(0, QtGui.QColor("#ffeb3b"))
                light_grad.setColorAt(0.5, QtGui.QColor("#fbc02d"))
                light_grad.setColorAt(1, wc.darker(110))
                painter.setBrush(light_grad)
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(cx - 57, cy + 22, 6, 6)

        # === SHIELD (Clipboard with Data Charts - iconic scientist accessory) ===
        shield = self.equipped.get("Shield")
        # Pathetic tier has no clipboard yet - using scraps of paper
        if self.tier == "pathetic":
            shield = None
        if shield:
            sc = QtGui.QColor(shield.get("color", "#795548"))  # Brown clipboard
            # Clipboard held in right hand at waist level
            # Clipboard backing board
            board_grad = QtGui.QLinearGradient(cx + 30, cy, cx + 58, cy + 35)
            board_grad.setColorAt(0, sc.lighter(118))
            board_grad.setColorAt(0.5, sc)
            board_grad.setColorAt(1, sc.darker(118))
            painter.setBrush(board_grad)
            painter.setPen(QtGui.QPen(sc.darker(135), 2))
            # Clipboard board (rectangular)
            painter.drawRoundedRect(cx + 30, cy, 28, 38, 2, 2)
            
            # Metal clip at top
            painter.setBrush(QtGui.QColor("#757575"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#424242"), 1))
            painter.drawRect(cx + 38, cy - 2, 12, 4)
            painter.drawArc(cx + 40, cy - 4, 8, 6, 0, 180 * 16)
            
            # White paper with data
            painter.setBrush(QtGui.QColor("#ffffff"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(cx + 32, cy + 4, 24, 32)
            
            # Data visualization on clipboard
            painter.setPen(QtGui.QPen(QtGui.QColor("#1e88e5"), 1))
            # Title text
            painter.setFont(QtGui.QFont("Arial", 5, QtGui.QFont.Bold))
            painter.drawText(cx + 34, cy + 8, "DATA")
            
            # Bar chart
            painter.setBrush(QtGui.QColor("#4caf50"))
            painter.setPen(QtCore.Qt.NoPen)
            bar_heights = [6, 10, 8, 12, 14] if self.tier in ["heroic", "epic", "legendary", "godlike"] else [4, 3, 5, 4, 3]
            for i, bar_h in enumerate(bar_heights):
                painter.drawRect(cx + 34 + i * 4, cy + 24 - bar_h, 3, bar_h)
            
            # Grid lines
            painter.setPen(QtGui.QPen(QtGui.QColor("#e0e0e0"), 1))
            for i in range(4):
                y_line = cy + 12 + i * 4
                painter.drawLine(cx + 34, y_line, cx + 54, y_line)
            
            # Checkboxes for low tiers (to-do list)
            if self.tier in ["pathetic", "modest", "decent"]:
                painter.setPen(QtGui.QPen(QtGui.QColor("#616161"), 1))
                painter.setBrush(QtCore.Qt.NoBrush)
                for i in range(3):
                    y_check = cy + 26 + i * 5
                    painter.drawRect(cx + 34, y_check, 3, 3)
                    # Checkmark for completed items
                    if i < 1 or self.tier == "decent":
                        painter.setPen(QtGui.QPen(QtGui.QColor("#4caf50"), 2))
                        painter.drawLine(cx + 34, y_check + 2, cx + 35, y_check + 3)
                        painter.drawLine(cx + 35, y_check + 3, cx + 37, y_check)
                        painter.setPen(QtGui.QPen(QtGui.QColor("#616161"), 1))
            
            # Coffee stain on paper for pathetic tier
            if self.tier == "pathetic":
                painter.setOpacity(0.3)
                painter.setBrush(QtGui.QColor("#8b4513"))
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(cx + 48, cy + 30, 6, 6)
                painter.setOpacity(1.0)
        else:
            # Pathetic tier - crumpled paper notes in hand (no proper clipboard)
            if self.tier == "pathetic":
                painter.setOpacity(0.8)
                painter.setBrush(QtGui.QColor("#f5f5dc"))
                painter.setPen(QtGui.QPen(QtGui.QColor("#8b7355"), 1))
                # Crumpled paper
                paper_path = QtGui.QPainterPath()
                paper_path.moveTo(cx + 38, cy + 8)
                paper_path.lineTo(cx + 50, cy + 6)
                paper_path.lineTo(cx + 52, cy + 18)
                paper_path.lineTo(cx + 48, cy + 22)
                paper_path.lineTo(cx + 40, cy + 20)
                paper_path.closeSubpath()
                painter.drawPath(paper_path)
                # Wrinkle lines
                painter.setPen(QtGui.QPen(QtGui.QColor("#9e9e9e"), 1))
                painter.drawLine(cx + 42, cy + 10, cx + 48, cy + 12)
                painter.drawLine(cx + 44, cy + 15, cx + 50, cy + 16)
                painter.setOpacity(1.0)

        # === CLOAK (Hazmat Suit overlay) ===
        cloak = self.equipped.get("Cloak")
        if cloak:
            haz = QtGui.QColor(cloak.get("color", "#cfd8dc"))
            painter.setOpacity(0.16)
            painter.setBrush(haz)
            painter.setPen(QtGui.QPen(haz.darker(130), 2))
            # Suit body overlay
            painter.drawRoundedRect(cx - 38, cy - 30, 76, 110, 10, 10)
            # Hood overlay
            painter.drawRoundedRect(cx - 28, cy - 82, 56, 60, 18, 18)
            painter.setOpacity(1.0)

        # === POWER LABEL ===
        label_rect = QtCore.QRect(0, h - 28, w, 25)
        painter.fillRect(label_rect, QtGui.QColor(0, 0, 0, 130))
        
        if self.tier in ["legendary", "godlike"]:
            painter.setPen(QtGui.QColor("#ffd700"))
            painter.setOpacity(0.5)
            for offset in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                painter.drawText(label_rect.translated(offset[0], offset[1]), 
                               QtCore.Qt.AlignCenter, f"🔬 {self.power}")
            painter.setOpacity(1.0)
        elif self.tier in ["epic"]:
            painter.setPen(QtGui.QColor("#42a5f5"))
        elif self.tier in ["heroic"]:
            painter.setPen(QtGui.QColor("#64b5f6"))
        else:
            painter.setPen(QtGui.QColor("#90caf9"))
        
        # Only draw final text for non-glowing tiers (glow loop already drew it)
        if self.tier not in ["legendary", "godlike"]:
            painter.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Bold))
            painter.drawText(label_rect, QtCore.Qt.AlignCenter, f"🔬 {self.power}")


class HydrationTab(QtWidgets.QWidget):
    """Hydration tracking tab - log water intake for rewards."""
    
    def __init__(self, blocker: 'BlockerCore', parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_display)
        self._refresh_timer.start(60000)  # Refresh every minute for countdown
        self._build_ui()
        self._refresh_display()
    
    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QtWidgets.QLabel("💧 Hydration Tracker")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)
        
        # Entity perk contributors section (if any)
        self.entity_perks_container = QtWidgets.QWidget()
        self.entity_perks_layout = QtWidgets.QVBoxLayout(self.entity_perks_container)
        self.entity_perks_layout.setContentsMargins(0, 0, 0, 8)
        layout.addWidget(self.entity_perks_container)
        self._refresh_entity_perks_display()
        
        # Main content split
        content_layout = QtWidgets.QHBoxLayout()
        
        # Left: Quick log and timeline
        left_panel = QtWidgets.QGroupBox("Log Water")
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        
        # Big water button
        self.water_btn = QtWidgets.QPushButton("💧 Log Glass of Water")
        self.water_btn.setMinimumHeight(60)
        self.water_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4fc3f7, stop:1 #0288d1);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
                border: 2px solid #0288d1;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #81d4fa, stop:1 #03a9f4);
            }
            QPushButton:pressed {
                background: #0277bd;
            }
            QPushButton:disabled {
                background: #555555;
                border: 2px solid #444444;
                color: #888888;
            }
        """)
        self.water_btn.clicked.connect(self._log_water)
        left_layout.addWidget(self.water_btn)
        
        # Status/countdown label
        self.status_label = QtWidgets.QLabel("🕐 Ready to log!")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4caf50;")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        left_layout.addWidget(self.status_label)
        
        # Today's progress
        progress_group = QtWidgets.QGroupBox("Today's Progress")
        progress_layout = QtWidgets.QVBoxLayout(progress_group)
        
        self.glasses_label = QtWidgets.QLabel("0 / 5 glasses")
        self.glasses_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4fc3f7;")
        self.glasses_label.setAlignment(QtCore.Qt.AlignCenter)
        progress_layout.addWidget(self.glasses_label)
        
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(HYDRATION_MAX_DAILY_GLASSES)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #2d3436;
                border: 1px solid #4fc3f7;
                border-radius: 5px;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4fc3f7, stop:1 #0288d1);
                border-radius: 4px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        left_layout.addWidget(progress_group)
        
        # Timeline graph
        timeline_group = QtWidgets.QGroupBox("📊 Today's Timeline")
        timeline_layout = QtWidgets.QVBoxLayout(timeline_group)
        
        self.timeline_widget = HydrationTimelineWidget()
        self.timeline_widget.setMinimumHeight(80)
        timeline_layout.addWidget(self.timeline_widget)
        
        left_layout.addWidget(timeline_group)
        
        # Rewards info
        rewards_group = QtWidgets.QGroupBox("🎁 Rewards Info")
        rewards_layout = QtWidgets.QVBoxLayout(rewards_group)
        rewards_info = QtWidgets.QLabel(
            "<b>How it works:</b><br>"
            "• Max 5 glasses/day (safe hydration)<br>"
            "• Wait 2 hours between glasses<br>"
            "• Each glass increases reward tier!<br><br>"
            "<b>💧 Per-Glass Reward:</b><br>"
            "<table style='font-size:10px; color:#888888;'>"
            "<tr><th>Glass</th><th>Center Tier</th></tr>"
            "<tr><td>1st</td><td>Common-centered</td></tr>"
            "<tr><td>2nd</td><td>Uncommon-centered</td></tr>"
            "<tr><td>3rd</td><td>Rare-centered</td></tr>"
            "<tr><td>4th</td><td>Epic-centered</td></tr>"
            "<tr><td>5th</td><td>100% Legendary!</td></tr>"
            "</table>"
            "<br><b>🔥 Streaks (5 glasses/day):</b><br>"
            "3d=Uncommon, 7d=Rare, 14d=Epic, 30d=Legendary"
        )
        rewards_info.setWordWrap(True)
        rewards_info.setStyleSheet("color: #888888; font-size: 10px;")
        rewards_layout.addWidget(rewards_info)
        left_layout.addWidget(rewards_group)
        
        left_layout.addStretch()
        content_layout.addWidget(left_panel)
        
        # Right: Stats and history
        right_panel = QtWidgets.QGroupBox("Stats & History")
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        
        self.stats_label = QtWidgets.QLabel("Loading stats...")
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("font-size: 12px;")
        right_layout.addWidget(self.stats_label)
        
        # History list
        history_label = QtWidgets.QLabel("<b>Recent History:</b>")
        right_layout.addWidget(history_label)
        
        self.history_list = QtWidgets.QListWidget()
        self.history_list.setMaximumHeight(200)
        self.history_list.setStyleSheet("""
            QListWidget {
                background: #2d3436;
                border: 1px solid #4a5568;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3d4852;
            }
        """)
        right_layout.addWidget(self.history_list)
        
        right_layout.addStretch()
        content_layout.addWidget(right_panel)
        
        layout.addLayout(content_layout)
        
        # Reminder Settings Section
        reminder_layout = QtWidgets.QHBoxLayout()
        self.reminder_checkbox = QtWidgets.QCheckBox("🔔 Remind me every")
        self.reminder_checkbox.setChecked(getattr(self.blocker, 'water_reminder_enabled', False))
        self.reminder_checkbox.stateChanged.connect(self._update_reminder_setting)
        reminder_layout.addWidget(self.reminder_checkbox)
        
        self.reminder_interval = QtWidgets.QSpinBox()
        self.reminder_interval.setRange(15, 180)
        self.reminder_interval.setValue(getattr(self.blocker, 'water_reminder_interval', 60))
        self.reminder_interval.setSuffix(" min")
        self.reminder_interval.valueChanged.connect(self._update_reminder_setting)
        reminder_layout.addWidget(self.reminder_interval)
        
        reminder_layout.addWidget(QtWidgets.QLabel("(via toast notification)"))
        reminder_layout.addStretch()
        layout.addLayout(reminder_layout)
    
    def _update_reminder_setting(self) -> None:
        """Save reminder settings when changed."""
        self.blocker.water_reminder_enabled = self.reminder_checkbox.isChecked()
        self.blocker.water_reminder_interval = self.reminder_interval.value()
        self.blocker.save_config()
    
    def _log_water(self) -> None:
        """Log a glass of water with animated lottery for reward."""
        from datetime import datetime
        
        # Initialize water entries if needed
        if not hasattr(self.blocker, 'water_entries'):
            self.blocker.water_entries = []
        
        # Initialize lottery attempts counter if needed
        if not hasattr(self.blocker, 'water_lottery_attempts'):
            self.blocker.water_lottery_attempts = 0
        
        # Check if we can log (with entity perk support)
        hydration_perks_active = False
        if can_log_water:
            check = can_log_water(self.blocker.water_entries, adhd_buster=self.blocker.adhd_buster)
            if not check["can_log"]:
                show_info(self, "Hydration", check["reason"])
                return
            # Track if entity perks are helping with hydration
            hydration_perks_active = check.get("perk_bonus_applied", False)
        
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # Count today's glasses (before this one)
        glasses_today = sum(
            1 for e in self.blocker.water_entries 
            if e.get("date") == today
        )
        glass_number = glasses_today + 1  # This glass
        
        # Show animated lottery dialog
        if GAMIFICATION_AVAILABLE:
            from lottery_animation import WaterLotteryDialog
            
            active_story = self.blocker.adhd_buster.get("active_story", "warrior")
            lottery = WaterLotteryDialog(
                glass_number=glass_number,
                lottery_attempts=self.blocker.water_lottery_attempts,
                story_id=active_story,
                parent=self
            )
            
            lottery.exec()
            won, tier, item, new_attempts = lottery.get_results()
            
            # Update attempt counter
            self.blocker.water_lottery_attempts = new_attempts
            
            # Log the water entry
            entry = {
                "date": today,
                "time": now.strftime("%H:%M"),
                "glasses": 1
            }
            self.blocker.water_entries.append(entry)
            # Prune to last 2000 entries (~1 year at 5 glasses/day)
            if len(self.blocker.water_entries) > 2000:
                self.blocker.water_entries = self.blocker.water_entries[-2000:]
            
            # Award item if won
            if won and item:
                item["source"] = f"hydration_glass_{glass_number}"
                
                main_window = self.window()
                game_state = getattr(main_window, 'game_state', None)
                if game_state:
                    game_state.award_items_batch([item], coins=0, auto_equip=True, source="hydration_tracking")
                    
                    if GAMIFICATION_AVAILABLE:
                        sync_hero_data(self.blocker.adhd_buster)
            
            # Check streak bonus (when completing 5 glasses)
            if glass_number >= 5:
                streak_days = self._calculate_streak()
                if streak_days > 0 and get_hydration_streak_bonus_rarity:
                    streak_rarity = get_hydration_streak_bonus_rarity(streak_days + 1)
                    if streak_rarity:
                        from gamification import generate_item
                        streak_item = generate_item(rarity=streak_rarity, story_id=active_story)
                        streak_item["source"] = "hydration_streak"
                        
                        main_window = self.window()
                        game_state = getattr(main_window, 'game_state', None)
                        if game_state:
                            game_state.award_items_batch([streak_item], coins=0, auto_equip=True, source="hydration_streak")
                            show_info(self, "Streak Bonus!", f"🔥 {streak_days + 1}-day streak: [{streak_rarity}] {streak_item.get('name')}!")
            
            self.blocker.save_config()
            
            # Show perk toast if entity perks helped with hydration
            if hydration_perks_active:
                from gamification import get_hydration_cooldown_minutes, get_hydration_daily_cap, HYDRATION_MIN_INTERVAL_HOURS, HYDRATION_MAX_DAILY_GLASSES
                cooldown = get_hydration_cooldown_minutes(self.blocker.adhd_buster)
                cap = get_hydration_daily_cap(self.blocker.adhd_buster)
                perk_parts = []
                if cooldown < HYDRATION_MIN_INTERVAL_HOURS * 60:
                    perk_parts.append(f"{int(HYDRATION_MIN_INTERVAL_HOURS * 60) - cooldown} min faster")
                if cap > HYDRATION_MAX_DAILY_GLASSES:
                    perk_parts.append(f"+{cap - HYDRATION_MAX_DAILY_GLASSES} daily glasses")
                if perk_parts:
                    show_perk_toast(f"Hydration Perks: {', '.join(perk_parts)}", "💧", self)
        else:
            # Fallback without gamification
            entry = {
                "date": today,
                "time": now.strftime("%H:%M"),
                "glasses": 1
            }
            self.blocker.water_entries.append(entry)
            # Prune to last 2000 entries (~1 year at 5 glasses/day)
            if len(self.blocker.water_entries) > 2000:
                self.blocker.water_entries = self.blocker.water_entries[-2000:]
            self.blocker.save_config()
            show_info(self, "Water Logged! 💧", f"💧 Glass #{glass_number} logged!")
        
        self._refresh_display()

    def _calculate_streak(self) -> int:
        """Calculate current hydration streak (5 glasses/day)."""
        from datetime import datetime, timedelta
        
        if not hasattr(self.blocker, 'water_entries') or not self.blocker.water_entries:
            return 0
        
        # Group by date
        daily_totals = {}
        for entry in self.blocker.water_entries:
            date = entry.get("date", "")
            if date:
                daily_totals[date] = daily_totals.get(date, 0) + entry.get("glasses", 1)
        
        # Count consecutive days with 5 glasses
        streak = 0
        check_date = datetime.now().date() - timedelta(days=1)  # Start from yesterday
        max_streak_check = 365  # Max 1 year (realistic maximum streak to display)
        
        while streak < max_streak_check:
            date_str = check_date.strftime("%Y-%m-%d")
            if daily_totals.get(date_str, 0) >= HYDRATION_MAX_DAILY_GLASSES:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def _refresh_display(self) -> None:
        """Refresh stats and history display."""
        from datetime import datetime
        from gamification import get_hydration_daily_cap
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        if not hasattr(self.blocker, 'water_entries'):
            self.blocker.water_entries = []
        
        # Get perk-modified daily cap
        daily_cap = get_hydration_daily_cap(self.blocker.adhd_buster) if get_hydration_daily_cap else HYDRATION_MAX_DAILY_GLASSES
        
        # Get today's entries
        today_entries = [e for e in self.blocker.water_entries if e.get("date") == today]
        glasses_today = len(today_entries)
        
        # Update progress display (use perk-modified cap)
        cap_label = f"{glasses_today} / {daily_cap} glasses"
        if daily_cap > HYDRATION_MAX_DAILY_GLASSES:
            cap_label += " ✨"  # Entity perk indicator
        self.glasses_label.setText(cap_label)
        self.progress_bar.setMaximum(daily_cap)
        self.progress_bar.setValue(min(glasses_today, daily_cap))
        
        if glasses_today >= daily_cap:
            self.glasses_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4caf50;")
        else:
            self.glasses_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4fc3f7;")
        
        # Update status/countdown (with entity perk support)
        if can_log_water:
            check = can_log_water(self.blocker.water_entries, adhd_buster=self.blocker.adhd_buster)
            if check["can_log"]:
                self.water_btn.setEnabled(True)
                self.status_label.setText("✅ Ready to log!")
                self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4caf50;")
            else:
                if check.get("minutes_remaining", 0) > 0:
                    mins = check["minutes_remaining"]
                    next_time = check.get("next_available_time", "")
                    status_text = f"⏳ Wait {mins} min (next at {next_time})"
                    if check.get("perk_bonus_applied"):
                        status_text = status_text.replace("⏳", "⏳✨")  # Perk indicator
                    self.water_btn.setEnabled(False)
                    self.status_label.setText(status_text)
                    self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff9800;")
                else:
                    self.water_btn.setEnabled(False)
                    self.status_label.setText("🎯 Daily goal complete!")
                    self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4caf50;")
        
        # Update timeline
        times_today = [e.get("time", "") for e in today_entries if e.get("time")]
        self.timeline_widget.set_times(times_today)
        
        # Update stats
        if get_hydration_stats:
            stats = get_hydration_stats(self.blocker.water_entries)
            streak = stats.get("current_streak", 0)
            streak_emoji = "🔥" if streak >= 3 else "📊"
            
            self.stats_label.setText(
                f"<b>📊 Your Hydration Stats</b><br><br>"
                f"💧 Total glasses: {stats.get('total_glasses', 0)}<br>"
                f"📅 Days tracked: {stats.get('total_days', 0)}<br>"
                f"⏰ Average daily: {stats.get('avg_daily', 0):.1f} glasses<br>"
                f"🎯 Days on target ({daily_cap}+): {stats.get('days_on_target', 0)} "
                f"({stats.get('target_rate', 0):.0f}%)<br>"
                f"{streak_emoji} Current streak: {streak} days"
            )
        else:
            self.stats_label.setText("Stats unavailable")
        
        # Update history
        self.history_list.clear()
        
        # Group entries by date
        daily_totals = {}
        for entry in self.blocker.water_entries:
            date = entry.get("date", "")
            if date:
                daily_totals[date] = daily_totals.get(date, 0) + entry.get("glasses", 1)
        
        # Show last 10 days
        for date in sorted(daily_totals.keys(), reverse=True)[:10]:
            glasses = daily_totals[date]
            icon = "✅" if glasses >= HYDRATION_MAX_DAILY_GLASSES else "💧"
            item = QtWidgets.QListWidgetItem(f"{icon} {date}: {glasses} glasses")
            self.history_list.addItem(item)
        
        # Update main timeline widget if parent window has it
        if self.parent() and hasattr(self.parent(), 'timeline_widget'):
            try:
                self.parent().timeline_widget.update_data()
            except Exception:
                pass
    
    def _refresh_entity_perks_display(self) -> None:
        """Refresh the entity perks display showing which entities boost hydration."""
        # Clear existing content
        while self.entity_perks_layout.count():
            item = self.entity_perks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            from gamification import get_entity_hydration_perk_contributors
            
            perks = get_entity_hydration_perk_contributors(self.blocker.adhd_buster)
            contributors = perks.get("contributors", [])
            
            if not contributors:
                self.entity_perks_container.hide()
                return
            
            self.entity_perks_container.show()
            
            # Create title with totals
            total_cd = perks.get("total_cooldown_reduction", 0)
            total_cap = perks.get("total_cap_bonus", 0)
            parts = []
            if total_cd > 0:
                parts.append(f"-{total_cd}min cooldown")
            if total_cap > 0:
                parts.append(f"+{total_cap} cap")
            title_text = f"✨ Entity Patrons ({', '.join(parts)})" if parts else "✨ Entity Patrons"
            
            title = QtWidgets.QLabel(title_text)
            title.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
            self.entity_perks_layout.addWidget(title)
            
            # Create mini-cards using shared function
            from merge_dialog import create_entity_perk_mini_cards
            perk_labels = {
                "cooldown": "⏱️",
                "cap": "🥛",
            }
            cards_widget = create_entity_perk_mini_cards(contributors, perk_labels)
            if cards_widget:
                self.entity_perks_layout.addWidget(cards_widget)
                
        except Exception as e:
            print(f"[Hydration] Error refreshing entity perks: {e}")
            self.entity_perks_container.hide()


class HydrationTimelineWidget(QtWidgets.QWidget):
    """Custom widget to show water intake timeline for the day."""
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._times: list = []  # List of "HH:MM" strings
        self.setMinimumHeight(60)
    
    def set_times(self, times: list) -> None:
        """Set the times when water was logged."""
        self._times = times
        self.update()
    
    def paintEvent(self, event) -> None:
        """Draw the timeline."""
        from datetime import datetime
        
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        rect = self.rect()
        margin = 30
        timeline_y = rect.height() // 2
        
        # Draw timeline background
        painter.setPen(QtGui.QPen(QtGui.QColor("#4a5568"), 2))
        painter.drawLine(margin, timeline_y, rect.width() - margin, timeline_y)
        
        # Draw hour markers (6am to 10pm)
        start_hour = 6
        end_hour = 22
        total_hours = end_hour - start_hour
        timeline_width = rect.width() - 2 * margin
        
        painter.setPen(QtGui.QColor("#666666"))
        painter.setFont(QtGui.QFont("Segoe UI", 8))
        
        for h in range(start_hour, end_hour + 1, 2):
            x = margin + (h - start_hour) / total_hours * timeline_width
            painter.drawLine(int(x), timeline_y - 5, int(x), timeline_y + 5)
            painter.drawText(int(x) - 10, timeline_y + 20, f"{h:02d}")
        
        # Draw water drops at logged times
        drop_color = QtGui.QColor("#4fc3f7")
        painter.setBrush(drop_color)
        painter.setPen(QtGui.QPen(QtGui.QColor("#0288d1"), 2))
        
        for time_str in self._times:
            try:
                h, m = map(int, time_str.split(":"))
                hour_decimal = h + m / 60.0
                
                if start_hour <= hour_decimal <= end_hour:
                    x = margin + (hour_decimal - start_hour) / total_hours * timeline_width
                    # Draw water drop
                    painter.drawEllipse(int(x) - 8, timeline_y - 20, 16, 16)
                    # Draw time label
                    painter.setPen(QtGui.QColor("#4fc3f7"))
                    painter.drawText(int(x) - 15, timeline_y - 25, time_str)
                    painter.setPen(QtGui.QPen(QtGui.QColor("#0288d1"), 2))
            except (ValueError, AttributeError):
                continue
        
        # Draw current time marker
        now = datetime.now()
        current_hour = now.hour + now.minute / 60.0
        if start_hour <= current_hour <= end_hour:
            x = margin + (current_hour - start_hour) / total_hours * timeline_width
            painter.setPen(QtGui.QPen(QtGui.QColor("#ff9800"), 2))
            painter.drawLine(int(x), timeline_y - 15, int(x), timeline_y + 15)
        
        painter.end()


# ============================================================================
# Power Analysis Dialog
# ============================================================================

class PowerAnalysisDialog(QtWidgets.QDialog):
    """Dialog showing detailed breakdown of power calculation path."""
    def __init__(self, breakdown: dict, equipped: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Power Calculation Analysis")
        self.setMinimumSize(700, 500)
        self.resize(900, 600)
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #ffffff; }
            QLabel { color: #ffffff; }
            QTableWidget { background-color: #333333; color: #ffffff; gridline-color: #555555; border: none; }
            QTableWidget::item { padding: 5px; border-bottom: 1px solid #444444; }
            QHeaderView::section { background-color: #1a1a1a; color: #aaaaaa; padding: 5px; border: none; }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Summary Header
        total = breakdown.get("total_power", 0)
        base = breakdown.get("base_power", 0)
        set_bonus = breakdown.get("set_bonus", 0)
        # neighbor_adjustment removed - system no longer active
        
        header_widget = QtWidgets.QWidget()
        header_widget.setStyleSheet("background-color: #1a1a1a; border-radius: 10px; padding: 10px;")
        header_layout = QtWidgets.QVBoxLayout(header_widget)
        
        title = QtWidgets.QLabel(f"Total Power: {total}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffca28;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        header_layout.addWidget(title)
        
        formula = QtWidgets.QLabel(
            f"Base Power ({base}) + Set Bonuses ({set_bonus})"
        )
        formula.setStyleSheet("font-size: 14px; color: #cccccc;")
        formula.setAlignment(QtCore.Qt.AlignCenter)
        header_layout.addWidget(formula)
        
        layout.addWidget(header_widget)
        
        # Explanation
        expl = QtWidgets.QLabel(
            "This table shows equipped items and their contribution to total power.\n"
            "Set bonuses apply when multiple items from the same set are equipped."
        )
        expl.setStyleSheet("color: #888888; margin: 10px;")
        expl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(expl)
        
        # Main Table
        table = QtWidgets.QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels([
            "Slot", "Item", "Power", "Rarity"
        ])
        # Configure column sizing for better layout
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)  # Slot
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)  # Item (stretches)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)  # Power
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)  # Rarity
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setWordWrap(True)
        
        slots = ["Helmet", "Chestplate", "Gauntlets", "Boots", "Shield", "Weapon", "Cloak", "Amulet"]
        table.setRowCount(len(slots))
        
        power_by_slot = breakdown.get("power_by_slot", {})
        
        for row, slot in enumerate(slots):
            item = equipped.get(slot)
            is_empty = not item or not isinstance(item, dict)
            item_name = "[Empty Slot]" if is_empty else item.get("name", "Unknown Item")
            
            # 1. Slot
            slot_item = QtWidgets.QTableWidgetItem(slot)
            slot_item.setTextAlignment(QtCore.Qt.AlignVCenter)
            table.setItem(row, 0, slot_item)
            
            # 2. Item Name & Rarity
            rarity = "Common" if is_empty else item.get("rarity", "Common")
            name_item = QtWidgets.QTableWidgetItem(item_name)
            if not is_empty:
                colors = {"Common": "#bdbdbd", "Uncommon": "#a5d6a7", "Rare": "#81c784", 
                          "Epic": "#ba68c8", "Legendary": "#ffb74d"}
                name_item.setForeground(QtGui.QColor(colors.get(rarity, "#bdbdbd")))
                if len(item_name) > 25:
                    name_item.setToolTip(item_name)
            else:
                name_item.setForeground(QtGui.QColor("#888888"))
                italic_font = QtGui.QFont("Segoe UI", 9)
                italic_font.setItalic(True)
                name_item.setFont(italic_font)
            table.setItem(row, 1, name_item)
            
            # 3. Power
            base_p = 0
            if item:
                base_p = item.get("power", 0)
                if base_p == 0:
                    from gamification import RARITY_POWER
                    base_p = RARITY_POWER.get(item.get("rarity", "Common"), 10)
            
            power_item = QtWidgets.QTableWidgetItem(str(base_p))
            power_item.setTextAlignment(QtCore.Qt.AlignCenter)
            power_item.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold))
            table.setItem(row, 2, power_item)
            
            # 4. Rarity
            rarity_item = QtWidgets.QTableWidgetItem(rarity if not is_empty else "-")
            rarity_item.setTextAlignment(QtCore.Qt.AlignCenter)
            table.setItem(row, 3, rarity_item)
            
            table.setRowHeight(row, 40)

        layout.addWidget(table)
        
        # Bottom info - Show active set details
        active_sets = breakdown.get("active_sets", [])
        if active_sets:
            set_info_lines = ["<b>Active Set Bonuses:</b>"]
            for s in active_sets:
                set_info_lines.append(f"  • {s['emoji']} {s['name']}: {s['count']} items = +{s['bonus']} power")
            set_box = QtWidgets.QLabel("<br>".join(set_info_lines))
            set_box.setStyleSheet("color: #4caf50; margin: 10px;")
            layout.addWidget(set_box)
        elif set_bonus > 0:
            # Fallback if active_sets missing but bonus exists
            set_box = QtWidgets.QLabel(f"<b>Set Bonuses:</b> +{set_bonus} power added to final score")
            set_box.setStyleSheet("color: #4caf50; margin: 10px;")
            layout.addWidget(set_box)
            
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        btn_box.accepted.connect(self.accept)
        layout.addWidget(btn_box)


class ADHDBusterTab(QtWidgets.QWidget):
    """Tab for viewing and managing the ADHD Buster character and inventory."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.merge_selected = []
        self.slot_combos: Dict[str, QtWidgets.QComboBox] = {}
        self.slot_labels: Dict[str, QtWidgets.QLabel] = {}  # Store slot label references for theme updates
        self._refreshing = False  # Prevent recursive refresh loops
        self._session_active = False  # Track if a focus session is active
        
        # Collapsible section states (stored in blocker config)
        self._collapsed_sections = self.blocker.adhd_buster.get("collapsed_sections", {})
        
        # Connect to game state manager for reactive updates
        self._game_state = get_game_state()
        if self._game_state:
            # Connect to specific signals for targeted updates
            self._game_state.power_changed.connect(self._on_power_changed)
            self._game_state.equipment_changed.connect(self._on_equipment_changed)
            self._game_state.set_bonus_changed.connect(self._on_set_bonus_changed)
            self._game_state.story_changed.connect(self._on_story_changed)
        
        self._build_ui()
        self.refresh_all()  # Initial data load
    
    # === Collapsible Section Management ===
    
    def _on_section_collapsed(self, section_id: str, collapsed: bool) -> None:
        """Save collapsed state when user toggles a section."""
        self._collapsed_sections[section_id] = collapsed
        self.blocker.adhd_buster["collapsed_sections"] = self._collapsed_sections
        self.blocker.save_config()
    
    # === GameState Signal Handlers ===
    
    def _on_power_changed(self, new_power: int) -> None:
        """Handle power change - update power label."""
        if hasattr(self, 'power_lbl'):
            power_info = get_power_breakdown(self.blocker.adhd_buster) if get_power_breakdown else {"base_power": new_power, "set_bonus": 0, "total_power": new_power}
            if power_info.get("set_bonus", 0) > 0:
                power_txt = f"⚔ Power: {power_info['total_power']} ({power_info['base_power']} + {power_info['set_bonus']} set)"
            else:
                power_txt = f"⚔ Power: {power_info['total_power']}"
            self.power_lbl.setText(power_txt)
        # Also update character display
        if hasattr(self, 'char_widget'):
            self.char_widget.update_from_data(self.blocker.adhd_buster)
    
    def _on_equipment_changed(self, slot: str) -> None:
        """Handle equipment change - update specific slot combo."""
        if slot in self.slot_combos:
            self._refresh_slot_combo(slot)
        self._refresh_character()
    
    def _on_set_bonus_changed(self, breakdown: dict) -> None:
        """Handle set bonus change - update sets display."""
        if hasattr(self, 'sets_section'):
            self._refresh_sets_display(breakdown)
    
    def _on_story_changed(self, story_id: str) -> None:
        """Handle story change - full refresh needed for theme."""
        self.refresh_all()

    def refresh_all(self) -> None:
        """Comprehensive refresh of all UI elements - call after any data change."""
        if self._refreshing:
            return  # Prevent recursive refresh loops
        self._refreshing = True
        try:
            # Refresh in the correct order to ensure consistent state
            self._refresh_all_slot_combos()  # Equipment dropdowns first
            self._refresh_inventory()         # Then inventory list
            self._refresh_character()         # Then power/stats display (also updates story)
            # Update merge selection state
            self._update_merge_selection()
            # Update story description (for story switches)
            if hasattr(self, 'story_desc_lbl'):
                self._update_story_description()
            # Sync story combo selection with current data
            self._sync_story_combo_selection()
            # Update mode UI state (enable/disable controls based on mode)
            self._update_mode_ui_state()
            # Update optimize button label based on entity perks
            self._update_optimize_button_label()
        finally:
            self._refreshing = False
    
    def _update_optimize_button_label(self) -> None:
        """Update the Optimize Gear button label based on Hobo/Robo Rat perk."""
        if not hasattr(self, '_optimize_btn') or not GAMIFICATION_AVAILABLE:
            return
        try:
            from gamification import get_entity_optimize_gear_cost
            optimize_perk = get_entity_optimize_gear_cost(self.blocker.adhd_buster)
            cost = optimize_perk["cost"]
            
            if optimize_perk["has_perk"]:
                if cost == 0:
                    # Robo Rat: FREE
                    self._optimize_btn.setText("⚡ Optimize Gear (FREE 🤖)")
                    self._optimize_btn.setToolTip(f"{optimize_perk['description']}")
                else:
                    # Hobo Rat: 1 coin
                    self._optimize_btn.setText(f"⚡ Optimize Gear ({cost}🪙 🐀)")
                    self._optimize_btn.setToolTip(f"{optimize_perk['description']}")
            else:
                # Default: 10 coins
                self._optimize_btn.setText(f"⚡ Optimize Gear ({cost}🪙)")
                self._optimize_btn.setToolTip("Automatically equip the best gear for maximum power")
        except Exception as e:
            print(f"[GamificationTab] Error updating optimize button: {e}")
    
    def _sync_story_combo_selection(self) -> None:
        """Sync the story combo box selection with the current active story."""
        if not GAMIFICATION_AVAILABLE or not hasattr(self, 'story_combo'):
            return
        from gamification import get_selected_story
        current_story = get_selected_story(self.blocker.adhd_buster)
        # Block signals to prevent triggering _on_story_change
        self.story_combo.blockSignals(True)
        for i in range(self.story_combo.count()):
            if self.story_combo.itemData(i) == current_story:
                self.story_combo.setCurrentIndex(i)
                break
        self.story_combo.blockSignals(False)

    def set_session_active(self, active: bool) -> None:
        """Enable/disable interactive controls during focus sessions."""
        self._session_active = active
        
        # Show/hide session banner
        if hasattr(self, 'session_banner'):
            self.session_banner.setVisible(active)
        
        # Disable/enable equipment dropdowns
        for combo in self.slot_combos.values():
            combo.setEnabled(not active)
        
        # Disable/enable action buttons
        if hasattr(self, '_action_buttons'):
            for btn in self._action_buttons:
                btn.setEnabled(not active)
        
        # Disable/enable merge button
        if hasattr(self, 'merge_btn'):
            self.merge_btn.setEnabled(not active and len(self.merge_selected) >= 2)
        
        # Disable/enable inventory selection
        if hasattr(self, 'inv_table'):
            self.inv_table.setEnabled(not active)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        # Session active warning banner (hidden by default)
        self.session_banner = QtWidgets.QLabel(
            "🔒 Focus session active - Equipment changes disabled until session ends"
        )
        self.session_banner.setStyleSheet(
            "background-color: #ff9800; color: white; padding: 10px; "
            "font-weight: bold; border-radius: 5px;"
        )
        self.session_banner.setAlignment(QtCore.Qt.AlignCenter)
        self.session_banner.setVisible(False)
        layout.addWidget(self.session_banner)

        # Use a splitter to allow resizing between upper content and inventory
        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        main_splitter.setChildrenCollapsible(False)
        
        # Upper section (scrollable content: header, story, character, equipped gear)
        upper_scroll = QtWidgets.QScrollArea()
        upper_scroll.setWidgetResizable(True)
        upper_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        container = QtWidgets.QWidget()
        self.inner_layout = QtWidgets.QVBoxLayout(container)

        # Header with power
        header = QtWidgets.QHBoxLayout()
        header.addWidget(QtWidgets.QLabel("<b style='font-size:18px;'>🦸 ADHD Buster</b>"))
        header.addStretch()

        power = calculate_character_power(self.blocker.adhd_buster) if GAMIFICATION_AVAILABLE else 0
        power_info = get_power_breakdown(self.blocker.adhd_buster) if GAMIFICATION_AVAILABLE else {"base_power": 0, "set_bonus": 0, "entity_bonus": 0, "active_sets": [], "total_power": 0}

        # Build power breakdown string showing all components
        power_parts = [str(power_info['base_power'])]
        if power_info.get("set_bonus", 0) > 0:
            power_parts.append(f"+{power_info['set_bonus']} set")
        if power_info.get("entity_bonus", 0) > 0:
            power_parts.append(f"+{power_info['entity_bonus']} patrons")
        
        if len(power_parts) > 1:
            power_txt = f"⚔ Power: {power_info['total_power']} ({' '.join(power_parts)})"
        else:
            power_txt = f"⚔ Power: {power_info['total_power']}"
        self.power_lbl = QtWidgets.QLabel(power_txt)
        self.power_lbl.setStyleSheet("font-weight: bold; color: #e65100;")
        header.addWidget(self.power_lbl)
        
        # Details Button
        if GAMIFICATION_AVAILABLE:
            self.details_btn = QtWidgets.QPushButton("🔍 Analysis")
            self.details_btn.setCursor(QtCore.Qt.PointingHandCursor)
            self.details_btn.setToolTip("View detailed power calculation path")
            self.details_btn.setStyleSheet("""
                QPushButton {
                    background-color: #333333;
                    color: #eeeeee;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: #444444;
                    border-color: #666666;
                }
            """)
            self.details_btn.clicked.connect(self._show_power_analysis)
            header.addWidget(self.details_btn)
            
        self.inner_layout.addLayout(header)

        # Active set bonuses (collapsible section)
        self.sets_section = CollapsibleSection(
            "🎯 Active Set Bonuses", "sets",
            collapsed=self._collapsed_sections.get("sets", False)
        )
        self.sets_section.collapsed_changed.connect(self._on_section_collapsed)
        self._refresh_sets_display(power_info)
        self.inner_layout.addWidget(self.sets_section)

        # Entity Patrons - entities boosting hero power (collapsible section)
        self.entity_patrons_section = CollapsibleSection(
            "🐉 Entity Patrons", "entity_patrons",
            collapsed=self._collapsed_sections.get("entity_patrons", False)
        )
        self.entity_patrons_section.collapsed_changed.connect(self._on_section_collapsed)
        self._refresh_entity_patrons_display()
        self.inner_layout.addWidget(self.entity_patrons_section)

        # Potential set bonuses from inventory (collapsible section)
        self.potential_sets_section = CollapsibleSection(
            "💡 Potential Set Bonuses (in your inventory)", "potential_sets",
            collapsed=self._collapsed_sections.get("potential_sets", False)
        )
        self.potential_sets_section.collapsed_changed.connect(self._on_section_collapsed)
        self._refresh_potential_sets_display()
        self.inner_layout.addWidget(self.potential_sets_section)
        
        # Gear bonuses (collapsible section)
        self.lucky_bonuses_section = CollapsibleSection(
            "✨ Gear Bonuses & Effects", "lucky_bonuses",
            collapsed=self._collapsed_sections.get("lucky_bonuses", False)
        )
        self.lucky_bonuses_section.collapsed_changed.connect(self._on_section_collapsed)
        self._refresh_lucky_bonuses_display()
        self.inner_layout.addWidget(self.lucky_bonuses_section)

        # Stats summary
        total_items = len(self.blocker.adhd_buster.get("inventory", []))
        total_collected = self.blocker.adhd_buster.get("total_collected", total_items)
        streak = self.blocker.stats.get("streak_days", 0)
        self.stats_lbl = QtWidgets.QLabel(f"📦 {total_items} in bag  |  🎁 {total_collected} collected  |  🔥 {streak} day streak")
        self.stats_lbl.setStyleSheet("color: gray;")
        self.inner_layout.addWidget(self.stats_lbl)

        # XP info is now shown in the XP ring widget in the timeline header
        # Store None references to avoid attribute errors in update functions
        if GAMIFICATION_AVAILABLE:
            self.level_title_lbl = None
            self.total_xp_lbl = None
            self.xp_progress_bar = None
            self.xp_text_lbl = None

        # Story Progress Section (at top for visibility)
        story_group = QtWidgets.QGroupBox("📜 Your Story")
        story_layout = QtWidgets.QVBoxLayout(story_group)

        # Mode selection row
        if GAMIFICATION_AVAILABLE:
            mode_bar = QtWidgets.QHBoxLayout()
            mode_bar.addWidget(QtWidgets.QLabel("Mode:"))
            self.mode_story_radio = QtWidgets.QRadioButton("Story")
            self.mode_hero_radio = QtWidgets.QRadioButton("Hero Only")
            self.mode_disabled_radio = QtWidgets.QRadioButton("Disabled")
            mode_group = QtWidgets.QButtonGroup(self)
            for btn in (self.mode_story_radio, self.mode_hero_radio, self.mode_disabled_radio):
                mode_group.addButton(btn)
                mode_bar.addWidget(btn)
            # Set current mode
            current_mode = get_story_mode(self.blocker.adhd_buster)
            if current_mode == STORY_MODE_HERO_ONLY:
                self.mode_hero_radio.setChecked(True)
            elif current_mode == STORY_MODE_DISABLED:
                self.mode_disabled_radio.setChecked(True)
            else:
                self.mode_story_radio.setChecked(True)
            # Connect signals - use lambda to filter to only checked state
            self.mode_story_radio.toggled.connect(lambda checked: checked and self._on_mode_radio_changed())
            self.mode_hero_radio.toggled.connect(lambda checked: checked and self._on_mode_radio_changed())
            self.mode_disabled_radio.toggled.connect(lambda checked: checked and self._on_mode_radio_changed())
            mode_bar.addStretch()
            story_layout.addLayout(mode_bar)
        
        # Story selection row
        if GAMIFICATION_AVAILABLE:
            from gamification import AVAILABLE_STORIES, get_selected_story, get_story_progress
            
            story_select_bar = QtWidgets.QHBoxLayout()
            story_select_bar.addWidget(QtWidgets.QLabel("Choose Your Story:"))
            self.story_combo = NoScrollComboBox()
            self.story_combo.setMinimumWidth(250)
            
            current_story = get_selected_story(self.blocker.adhd_buster)
            unlocked_stories = self.blocker.adhd_buster.get("unlocked_stories", ["underdog"])
            current_idx = 0
            for i, (story_id, story_info) in enumerate(AVAILABLE_STORIES.items()):
                is_locked = story_id not in unlocked_stories
                lock_icon = "🔒 " if is_locked else ""
                self.story_combo.addItem(f"{lock_icon}{story_info['title']}", story_id)
                tooltip = story_info['description']
                if is_locked:
                    tooltip += "\n\n🔒 Costs 100 coins to unlock"
                self.story_combo.setItemData(i, tooltip, QtCore.Qt.ToolTipRole)
                if story_id == current_story:
                    current_idx = i
            
            self.story_combo.setCurrentIndex(current_idx)
            self.story_combo.currentIndexChanged.connect(self._on_story_change)
            story_select_bar.addWidget(self.story_combo)
            
            # Restart Story button
            self.restart_story_btn = QtWidgets.QPushButton("🔄 Restart Story")
            self.restart_story_btn.setToolTip("Reset this story's hero - lose all gear, progress, and decisions")
            self.restart_story_btn.setStyleSheet("color: #c62828;")
            self.restart_story_btn.clicked.connect(self._on_restart_story)
            story_select_bar.addWidget(self.restart_story_btn)
            
            story_select_bar.addStretch()
            story_layout.addLayout(story_select_bar)
            
            # Story description
            self.story_desc_lbl = QtWidgets.QLabel()
            self.story_desc_lbl.setWordWrap(True)
            self.story_desc_lbl.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
            self._update_story_description()
            story_layout.addWidget(self.story_desc_lbl)
        
        # Story progress info
        if GAMIFICATION_AVAILABLE:
            progress = get_story_progress(self.blocker.adhd_buster)
            
            self.story_progress_lbl = QtWidgets.QLabel()
            self.story_progress_lbl.setStyleSheet("font-weight: bold;")
            story_layout.addWidget(self.story_progress_lbl)
            
            self.story_next_lbl = QtWidgets.QLabel()
            self.story_next_lbl.setStyleSheet("color: #666;")
            story_layout.addWidget(self.story_next_lbl)
            
            # Progress bar for next chapter
            progress_bar_layout = QtWidgets.QHBoxLayout()
            progress_bar_layout.addWidget(QtWidgets.QLabel("Progress to Next Chapter:"))
            self.chapter_progress_bar = QtWidgets.QProgressBar()
            self.chapter_progress_bar.setMinimum(0)
            self.chapter_progress_bar.setMaximum(100)
            self.chapter_progress_bar.setTextVisible(True)
            self.chapter_progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #444;
                    border-radius: 5px;
                    text-align: center;
                    height: 20px;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #4caf50, stop:0.5 #8bc34a, stop:1 #cddc39);
                    border-radius: 4px;
                }
            """)
            progress_bar_layout.addWidget(self.chapter_progress_bar, 1)
            story_layout.addLayout(progress_bar_layout)
            
            self._update_story_progress_labels()
        
        # Chapter selection
        chapter_bar = QtWidgets.QHBoxLayout()
        chapter_bar.addWidget(QtWidgets.QLabel("Select Chapter:"))
        self.chapter_combo = NoScrollComboBox()
        
        if GAMIFICATION_AVAILABLE:
            self._refresh_story_chapter_list()
        else:
            self.chapter_combo.addItem("Story unavailable", 0)
        
        chapter_bar.addWidget(self.chapter_combo)
        read_btn = QtWidgets.QPushButton("📖 Read Chapter")
        read_btn.clicked.connect(self._read_story_chapter)
        chapter_bar.addWidget(read_btn)
        chapter_bar.addStretch()
        story_layout.addLayout(chapter_bar)
        
        self.inner_layout.addWidget(story_group)

        # Update mode UI state (enable/disable story controls based on mode)
        if GAMIFICATION_AVAILABLE:
            self._update_mode_ui_state()

        # Latest Diary Entry - Speech bubble from the character
        diary_bubble_group = QtWidgets.QWidget()
        diary_bubble_layout = QtWidgets.QVBoxLayout(diary_bubble_group)
        diary_bubble_layout.setContentsMargins(10, 5, 10, 5)
        
        # Get the latest diary entry
        diary_entries = self.blocker.adhd_buster.get("diary", [])
        
        # Speech bubble header with button
        bubble_header = QtWidgets.QHBoxLayout()
        bubble_header.addWidget(QtWidgets.QLabel("<b>💬 Latest Adventure:</b>"))
        bubble_header.addStretch()
        self.diary_history_btn = QtWidgets.QPushButton("📖 View All Entries")
        self.diary_history_btn.setStyleSheet("font-size: 11px; padding: 3px 8px;")
        self.diary_history_btn.clicked.connect(self._open_diary)
        bubble_header.addWidget(self.diary_history_btn)
        diary_bubble_layout.addLayout(bubble_header)
        
        # Speech bubble content
        self.speech_bubble = QtWidgets.QLabel()
        self.speech_bubble.setWordWrap(True)
        self.speech_bubble.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                border: 2px solid #555;
                border-radius: 12px;
                padding: 12px;
                color: #f0f0f0;
                font-size: 12px;
            }
        """)
        
        if diary_entries:
            latest = diary_entries[-1]
            entry_text = latest.get("story", "No adventures yet...")
            date_str = latest.get("short_date", latest.get("date", ""))
            tier = latest.get("tier", "unknown")
            self.speech_bubble.setText(f'"{entry_text}"\n\n— {date_str} | Tier: {tier.title()}')
        else:
            self.speech_bubble.setText("No adventures yet... Start a focus session to write your story!")
        
        diary_bubble_layout.addWidget(self.speech_bubble)
        self.inner_layout.addWidget(diary_bubble_group)

        # Character canvas and equipment side by side
        char_equip = QtWidgets.QHBoxLayout()
        equipped = self.blocker.adhd_buster.get("equipped", {})
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        self.char_canvas = CharacterCanvas(equipped, power_info["total_power"], parent=self, story_theme=active_story)
        char_equip.addWidget(self.char_canvas)
        self.char_equip_layout = char_equip  # Store reference for refresh

        equip_group = QtWidgets.QGroupBox("⚔ Equipped Gear (change with dropdown)")
        equip_layout = QtWidgets.QFormLayout(equip_group)
        slots = ["Helmet", "Chestplate", "Gauntlets", "Boots", "Shield", "Weapon", "Cloak", "Amulet"]
        inventory = self.blocker.adhd_buster.get("inventory", [])
        
        # Get current story for themed slot names
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        
        # Rarity colors for visual distinction
        rarity_colors = {
            "Common": "#9e9e9e",
            "Uncommon": "#4caf50",
            "Rare": "#2196f3",
            "Epic": "#9c27b0",
            "Legendary": "#ff9800"
        }

        for slot in slots:
            combo = NoScrollComboBox()
            combo.setFocusPolicy(QtCore.Qt.StrongFocus)
            combo.addItem("[Empty]")
            slot_items = [item for item in inventory if item.get("slot") == slot]
            for idx, item in enumerate(slot_items):
                item_name = item.get('name', 'Unknown')
                item_rarity = item.get('rarity', 'Common')
                item_color = rarity_colors.get(item_rarity, "#9e9e9e")
                power = item.get('power', 10)
                display = f"{item_name} (+{power}) [{item_rarity}]"
                
                # Add lucky options summary to dropdown text if present
                lucky_options = item.get("lucky_options", {})
                if lucky_options and format_lucky_options:
                    try:
                        lucky_text = format_lucky_options(lucky_options)
                        if lucky_text:
                            display += f" ✨{lucky_text}"
                    except Exception:
                        pass  # Skip if formatting fails
                
                combo.addItem(display, item)
                combo_idx = combo.count() - 1
                # Set foreground color for this item
                combo.setItemData(combo_idx, QtGui.QColor(item_color), QtCore.Qt.ForegroundRole)
                
                # Build comprehensive tooltip for this item
                slot_display = get_slot_display_name(slot, active_story) if get_slot_display_name else slot
                tooltip_parts = [f"<b style='color:{item_color};'>{item_name}</b>"]
                item_type = item.get("item_type", "")
                if item_type:
                    tooltip_parts.append(f"<br><i>{item_type}</i>")
                tooltip_parts.append(f"<br>⚔️ Power: +{power}")
                tooltip_parts.append(f"<br>🎭 Rarity: {item_rarity}")
                tooltip_parts.append(f"<br>🎯 Slot: {slot_display}")
                item_set = item.get("set")
                if item_set:
                    tooltip_parts.append(f"<br>🏷️ Set: {item_set}")
                
                # Neighbor system removed - no longer showing neighbor slots
                
                # Special attributes section
                has_special = False
                special_parts = []
                
                if lucky_options and format_lucky_options:
                    try:
                        lucky_text = format_lucky_options(lucky_options)
                        if lucky_text:
                            special_parts.append(f"✨ Lucky Options: {lucky_text}")
                            has_special = True
                    except Exception:
                        pass
                
                if has_special:
                    tooltip_parts.append("<br><br><b>✨ Special Attributes:</b>")
                    for sp in special_parts:
                        tooltip_parts.append(f"<br>  {sp}")
                
                tooltip_html = "".join(tooltip_parts)
                combo.setItemData(combo_idx, tooltip_html, QtCore.Qt.ToolTipRole)
                
            current = equipped.get(slot)
            if current:
                for i in range(1, combo.count()):
                    if combo.itemData(i) and combo.itemData(i).get("name") == current.get("name"):
                        combo.setCurrentIndex(i)
                        # Apply color to the combo box text for selected item
                        curr_rarity = current.get("rarity", "Common")
                        curr_color = rarity_colors.get(curr_rarity, "#9e9e9e")
                        combo.setStyleSheet(f"QComboBox {{ color: {curr_color}; font-weight: bold; }}")
                        break
            combo.currentIndexChanged.connect(lambda idx, s=slot, c=combo: self._on_equip_change(s, c))
            self.slot_combos[slot] = combo
            # Use themed slot display name - power info shown in separate label
            display_name = get_slot_display_name(slot, active_story) if get_slot_display_name else slot
            slot_label = QtWidgets.QLabel(f"{display_name}:")
            self.slot_labels[slot] = slot_label
            equip_layout.addRow(slot_label, combo)
        
        char_equip.addWidget(equip_group)
        self.inner_layout.addLayout(char_equip)
        
        # End of upper section - set it in the scroll area
        upper_scroll.setWidget(container)
        main_splitter.addWidget(upper_scroll)

        # Lower section: Inventory (resizable via splitter)
        inv_container = QtWidgets.QWidget()
        inv_container_layout = QtWidgets.QVBoxLayout(inv_container)
        inv_container_layout.setContentsMargins(5, 0, 5, 0)
        
        # Inventory with split view (list + details panel)
        inv_group = QtWidgets.QGroupBox("📦 Inventory (click items to select for merge)")
        inv_main_layout = QtWidgets.QVBoxLayout(inv_group)
        
        # Inventory stats header
        stats_layout = QtWidgets.QHBoxLayout()
        self.inv_stats_label = QtWidgets.QLabel()
        self.inv_stats_label.setStyleSheet("color: #666; font-size: 10px;")
        stats_layout.addWidget(self.inv_stats_label)
        stats_layout.addStretch()
        inv_main_layout.addLayout(stats_layout)
        
        sort_bar = QtWidgets.QHBoxLayout()
        self.sort_combo = NoScrollComboBox()
        self.sort_combo.addItem("Sort: newest", "newest")
        self.sort_combo.addItem("Sort: rarity", "rarity")
        self.sort_combo.addItem("Sort: slot", "slot")
        self.sort_combo.addItem("Sort: power", "power")
        self.sort_combo.addItem("Sort: lucky", "lucky")
        self.sort_combo.currentIndexChanged.connect(self._refresh_inventory)
        sort_bar.addWidget(self.sort_combo)
        sort_bar.addStretch()
        inv_main_layout.addLayout(sort_bar)
        
        # Inventory Table
        self.inv_table = QtWidgets.QTableWidget()
        self.inv_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.inv_table.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.inv_table.itemSelectionChanged.connect(self._update_merge_selection)
        # self.inv_table.itemSelectionChanged.connect(self._update_item_details_panel) # Panel removed
        self.inv_table.setAlternatingRowColors(True)
        self.inv_table.verticalHeader().setVisible(False)
        self.inv_table.setShowGrid(False)
        self.inv_table.setSortingEnabled(True) # Enable sorting
        
        # Scrollbars are enabled by default
        
        self.inv_table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #ddd;
                border: 1px solid #444;
                gridline-color: #3a3a3a;
            }
            QTableWidget::item {
                padding: 3px 5px;
                border-bottom: 1px solid #3a3a3a;
            }
            QTableWidget::item:selected {
                background-color: #4a6fa5;
            }
            QTableWidget::item:alternate {
                background-color: #333333;
            }
            QHeaderView::section {
                background-color: #1e1e2e;
                color: #aaa;
                padding: 5px;
                border: none;
                font-weight: bold;
                font-size: 10px;
            }
            QToolTip { 
                color: #ffffff; 
                background-color: #2a2a2a; 
                border: 1px solid #555; 
            }
        """)
        
        # Set up columns: Eq, Name, Slot, Tier, Power, Set, +3 bonuses
        columns = [
            "Eq", "Name", "Slot", "Tier", "Pwr", "Set", 
            "💰", "⭐", "🎲"
        ]
        self.inv_table.setColumnCount(len(columns))
        self.inv_table.setHorizontalHeaderLabels(columns)
        
        # Tooltips for headers - detailed explanations
        header_tooltips = [
            "Equipped Status\n✓ = Currently equipped on your hero\nClick to equip/unequip items",
            "Item Name\nThe name of the item including its rarity adjective\nHigher tier items have more impressive names",
            "Equipment Slot\nWhere this item is equipped:\n• Helmet, Chestplate, Gauntlets, Boots\n• Shield, Weapon, Ring, Necklace",
            "Rarity Tier\nItem quality from Common to Legendary:\nC=Common, U=Uncommon, R=Rare, E=Epic, L=Legendary\nHigher tiers have better stats and bonuses",
            "Power Level\nThe item's combat power contribution\nHigher power = stronger hero\nTotal power from all equipped items is shown in hero stats",
            "Item Set\nItems from the same set provide bonus effects\nCollect matching set pieces for additional power",
            "💰 Coin Discount\nReduces costs for merge operations\nHigher % = cheaper merges (up to 90% off)\nGreat for saving coins while upgrading gear",
            "⭐ XP Bonus\nBonus experience points from focus sessions\nHigher % = faster leveling\nLevel up to unlock new features and rewards",
            "🎲 Merge Luck\nIncreases success chance in Lucky Merge\nBase merge success is 25%, this adds to it\nVery valuable for upgrading your gear!"
        ]
        for i, tooltip in enumerate(header_tooltips):
            item = self.inv_table.horizontalHeaderItem(i)
            if item:
                item.setToolTip(tooltip)

        # Configure column resizing
        header = self.inv_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive) # Allow user resizing
        header.setStretchLastSection(True)
        
        # Persistence connections
        header.sectionResized.connect(self._save_inventory_state)
        header.sortIndicatorChanged.connect(self._save_inventory_state)
        
        # Load saved state
        self._load_inventory_state()
        
        inv_main_layout.addWidget(self.inv_table)
        
        # Make inventory group expand to fill available space
        inv_group.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        inv_container_layout.addWidget(inv_group, 1)  # stretch factor 1

        # Lucky Merge (below inventory)
        merge_group = QtWidgets.QGroupBox("🎲 Lucky Merge")
        merge_layout = QtWidgets.QHBoxLayout(merge_group)
        warn_lbl = QtWidgets.QLabel("⚠️ 25% base success (items lost on fail!) • Cost: 50🪙")
        warn_lbl.setStyleSheet("color: #d32f2f; font-size: 10px;")
        merge_layout.addWidget(warn_lbl)
        self.merge_btn = QtWidgets.QPushButton("🎲 Merge Selected (0)")
        self.merge_btn.setEnabled(False)
        self.merge_btn.setToolTip("Combine items for a chance at a higher rarity item (costs 50 coins)")
        self.merge_btn.clicked.connect(self._do_merge)
        merge_layout.addWidget(self.merge_btn)
        self.merge_rate_lbl = QtWidgets.QLabel("← Select 2+ items above")
        self.merge_rate_lbl.setStyleSheet("font-size: 10px;")
        merge_layout.addWidget(self.merge_rate_lbl)
        merge_layout.addStretch()
        inv_container_layout.addWidget(merge_group)

        self._refresh_inventory()
        
        # Add inventory container to splitter
        main_splitter.addWidget(inv_container)
        
        # Set initial splitter sizes (upper section smaller, inventory larger)
        main_splitter.setSizes([300, 400])
        main_splitter.setHandleWidth(8)
        
        # Style the splitter handle for visibility
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #444;
                border: 1px solid #555;
            }
            QSplitter::handle:hover {
                background-color: #666;
            }
        """)
        
        layout.addWidget(main_splitter, 1)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        # Refresh button for manual refresh
        refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Refresh all displays to show current state")
        refresh_btn.clicked.connect(self.refresh_all)
        btn_layout.addWidget(refresh_btn)
        
        diary_btn = QtWidgets.QPushButton("📖 Adventure Diary")
        diary_btn.clicked.connect(self._open_diary)
        btn_layout.addWidget(diary_btn)
        sell_btn = QtWidgets.QPushButton("💰 Sell Items")
        sell_btn.clicked.connect(self._sell_items)
        btn_layout.addWidget(sell_btn)
        self._optimize_btn = QtWidgets.QPushButton("⚡ Optimize Gear (10🪙)")
        self._optimize_btn.setToolTip("Automatically equip the best gear for maximum power")
        self._optimize_btn.clicked.connect(self._optimize_gear)
        btn_layout.addWidget(self._optimize_btn)
        btn_layout.addStretch()
        # Store button references for enabling/disabling during sessions
        self._action_buttons = [refresh_btn, diary_btn, sell_btn, self._optimize_btn]
        layout.addLayout(btn_layout)
        
        # Update optimize button label based on entity perks
        self._update_optimize_button_label()

    def _on_equip_change(self, slot: str, combo: QtWidgets.QComboBox) -> None:
        """Handle equipment slot change - use GameState for reactive updates."""
        idx = combo.currentIndex()
        
        # Rarity colors for combo styling
        rarity_colors = {
            "Common": "#9e9e9e",
            "Uncommon": "#4caf50",
            "Rare": "#2196f3",
            "Epic": "#9c27b0",
            "Legendary": "#ff9800"
        }
        
        # Prepare item data
        new_item = None
        if idx > 0:
            item = combo.currentData()
            if item:
                # Create deep copy to preserve lucky_options
                new_item = item.copy()
                if "lucky_options" in item and isinstance(item["lucky_options"], dict):
                    new_item["lucky_options"] = item["lucky_options"].copy()
                # Update combo color immediately for equipped item
                item_rarity = item.get("rarity", "Common")
                item_color = rarity_colors.get(item_rarity, "#9e9e9e")
                combo.setStyleSheet(f"QComboBox {{ color: {item_color}; font-weight: bold; }}")
        else:
            # Empty selected - reset to white
            combo.setStyleSheet("QComboBox { color: #ffffff; }")
        
        # Use GameState manager for reactive updates
        if not self._game_state:
            logger.error("GameStateManager not available - cannot change equipment")
            return
        
        self._game_state.swap_equipped_item(slot, new_item)
        # Sync changes to active hero
        if GAMIFICATION_AVAILABLE:
            sync_hero_data(self.blocker.adhd_buster)
        # UI updates happen automatically via signals

    def _refresh_sets_display(self, power_info: dict = None) -> None:
        """Refresh the active set bonuses display."""
        # Clear existing content in collapsible section
        self.sets_section.clear_content()
        
        if not GAMIFICATION_AVAILABLE:
            self.sets_section.setVisible(False)
            return
            
        if power_info is None:
            power_info = get_power_breakdown(self.blocker.adhd_buster)
        
        active_sets = power_info.get("active_sets", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        if active_sets:
            self.sets_section.setVisible(True)
            for s in active_sets:
                # Main set bonus line
                lbl = QtWidgets.QLabel(f"{s['emoji']} {s['name']} ({s['count']} items): <b>+{s['bonus']} power</b>")
                lbl.setTextFormat(QtCore.Qt.RichText)
                lbl.setStyleSheet("color: #4caf50; font-size: 11px; padding: 2px 0;")
                self.sets_section.add_widget(lbl)
                
                # Show which items belong to this set
                slots = s.get('slots', [])
                if slots and equipped:
                    item_names = []
                    for slot in slots:
                        item = equipped.get(slot)
                        if item:
                            # Get item name, truncate if too long
                            name = item.get('name', slot.replace('_', ' ').title())
                            if len(name) > 20:
                                name = name[:17] + "..."
                            item_names.append(name)
                    
                    if item_names:
                        items_str = ", ".join(item_names)
                        items_lbl = QtWidgets.QLabel(f"    └ {items_str}")
                        items_lbl.setStyleSheet("color: #888; font-size: 10px; padding-left: 15px;")
                        self.sets_section.add_widget(items_lbl)
            
            # Update title with count
            self.sets_section.set_title(f"🎯 Active Set Bonuses ({len(active_sets)})")
        else:
            self.sets_section.setVisible(False)

    def _refresh_entity_patrons_display(self) -> None:
        """Refresh the entity patrons display showing collected entities that boost hero power."""
        # Clear existing content in collapsible section
        self.entity_patrons_section.clear_content()
        
        if not GAMIFICATION_AVAILABLE or not get_entity_power_perks:
            self.entity_patrons_section.setVisible(False)
            return
        
        # Get entity power perks with contributor details
        power_perks = get_entity_power_perks(self.blocker.adhd_buster)
        contributors = power_perks.get("contributors", [])
        total_power = power_perks.get("total_power", 0)
        
        if contributors:
            self.entity_patrons_section.setVisible(True)
            self.entity_patrons_section.set_title(f"🐉 Entity Patrons (+{total_power} Power)")
            
            # Try to import entity icon resolver
            try:
                from entitidex_tab import _resolve_entity_svg_path
                from entitidex.entity_pools import get_entity_by_id as get_entity
                from PySide6.QtSvg import QSvgRenderer
                has_svg_support = True
            except ImportError:
                has_svg_support = False
            
            # Create a horizontal flow layout for entity cards
            patrons_container = QtWidgets.QWidget()
            patrons_layout = QtWidgets.QHBoxLayout(patrons_container)
            patrons_layout.setContentsMargins(5, 5, 5, 5)
            patrons_layout.setSpacing(8)
            
            for entity_data in contributors:
                # Create a mini card for each entity
                card = QtWidgets.QFrame()
                is_exceptional = entity_data.get("is_exceptional", False)
                
                # Style cards - exceptional gets slightly lighter border
                if is_exceptional:
                    card.setStyleSheet("""
                        QFrame {
                            background-color: #2a2a2a;
                            border: 1px solid #555;
                            border-radius: 6px;
                            padding: 4px;
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
                            border-radius: 6px;
                            padding: 4px;
                        }
                        QFrame:hover {
                            border-color: #e65100;
                            background-color: #333;
                        }
                    """)
                
                card_layout = QtWidgets.QVBoxLayout(card)
                card_layout.setContentsMargins(8, 6, 8, 6)
                card_layout.setSpacing(4)
                
                # Try to load entity SVG icon
                entity_id = entity_data.get("entity_id", "")
                icon_loaded = False
                
                if has_svg_support and entity_id:
                    try:
                        entity_obj = get_entity(entity_id)
                        if entity_obj:
                            svg_path = _resolve_entity_svg_path(entity_obj, is_exceptional)
                            if svg_path:
                                renderer = QSvgRenderer(svg_path)
                                if renderer.isValid():
                                    # Create pixmap from SVG (40x40 size for mini cards)
                                    icon_size = 40
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
                        pass  # Fall back to text display
                
                # Entity name with exceptional styling
                name = entity_data.get("name", "Unknown")
                # Truncate long names
                if len(name) > 18:
                    display_name = name[:15] + "..."
                else:
                    display_name = name
                
                if is_exceptional:
                    name_style = "color: #ffd700; font-weight: bold; font-size: 10px;"
                    prefix = "⭐ " if not icon_loaded else ""
                else:
                    name_style = "color: #ccc; font-size: 10px;"
                    prefix = ""
                
                name_lbl = QtWidgets.QLabel(f"{prefix}{display_name}")
                name_lbl.setStyleSheet(name_style)
                name_lbl.setAlignment(QtCore.Qt.AlignCenter)
                name_lbl.setToolTip(f"{name}\n{entity_data.get('description', '')}")
                name_lbl.setWordWrap(True)
                card_layout.addWidget(name_lbl)
                
                # Power value
                power_val = entity_data.get("power", 0)
                power_lbl = QtWidgets.QLabel(f"<b>+{power_val}</b> ⚔")
                power_lbl.setStyleSheet("color: #e65100; font-size: 12px;")
                power_lbl.setAlignment(QtCore.Qt.AlignCenter)
                card_layout.addWidget(power_lbl)
                
                patrons_layout.addWidget(card)
            
            patrons_layout.addStretch()
            self.entity_patrons_section.add_widget(patrons_container)
            
            # Add a tip
            tip_lbl = QtWidgets.QLabel("💡 Collect more Warrior entities in Entitidex to boost your hero's power!")
            tip_lbl.setStyleSheet("color: #888; font-style: italic; font-size: 10px; padding-top: 4px;")
            self.entity_patrons_section.add_widget(tip_lbl)
        else:
            self.entity_patrons_section.setVisible(False)

    def _show_power_analysis(self) -> None:
        """Show the detailed power analysis dialog."""
        if not GAMIFICATION_AVAILABLE or not get_power_breakdown:
            show_warning(
                self,
                "Analysis Unavailable",
                "Power breakdown is unavailable (gamification module not loaded).",
            )
            return

        try:
            power_info = get_power_breakdown(self.blocker.adhd_buster)
            if not power_info:
                show_warning(
                    self,
                    "Analysis Unavailable",
                    "Power breakdown data is missing. Try again after a session or reload.",
                )
                return

            equipped = self.blocker.adhd_buster.get("equipped", {})
            dlg = PowerAnalysisDialog(power_info, equipped, self)
            dlg.exec()
        except Exception as exc:  # Defensive: surface errors to the user
            show_error(
                self,
                "Analysis Failed",
                f"Could not show power analysis.\n\nDetails: {exc}",
            )
    
    def _refresh_lucky_bonuses_display(self) -> None:
        """Refresh the gear bonuses display showing total bonuses from equipped gear."""
        # Clear existing content in collapsible section
        self.lucky_bonuses_section.clear_content()
        
        if not GAMIFICATION_AVAILABLE:
            self.lucky_bonuses_section.setVisible(False)
            return
        
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        # Calculate lucky options bonuses
        lucky_bonuses = {"coin_bonus": 0, "xp_bonus": 0, "merge_luck": 0}
        if calculate_total_lucky_bonuses:
            lucky_bonuses = calculate_total_lucky_bonuses(equipped)
        
        # Check if there are any bonuses to display
        has_lucky_bonuses = any(v > 0 for v in lucky_bonuses.values())
        
        if has_lucky_bonuses:
            # Build compact display items
            bonus_items = []
            
            if lucky_bonuses.get("coin_discount", 0) > 0:
                bonus_items.append(("💰", f"{lucky_bonuses['coin_discount']}% Merge Discount", "#f59e0b", "Cheaper merges"))
            if lucky_bonuses.get("xp_bonus", 0) > 0:
                bonus_items.append(("⭐", f"+{lucky_bonuses['xp_bonus']}% XP", "#8b5cf6", "Level faster"))
            if lucky_bonuses.get("merge_luck", 0) > 0:
                bonus_items.append(("🎲", f"+{lucky_bonuses['merge_luck']}% Merge Luck", "#3b82f6", "Better merges"))
            
            self.lucky_bonuses_section.setVisible(True)
            self.lucky_bonuses_section.set_title(f"✨ Gear Bonuses ({len(bonus_items)})")
            
            # Compact list with colored items
            for icon, title, color, tooltip in bonus_items:
                lbl = QtWidgets.QLabel(f"<b>{icon} {title}</b> <span style='color:#888;'>— {tooltip}</span>")
                lbl.setTextFormat(QtCore.Qt.RichText)
                lbl.setStyleSheet(f"color: {color}; font-size: 11px; padding: 2px 0;")
                self.lucky_bonuses_section.add_widget(lbl)
            
            # Compact summary
            summary_parts = []
            if lucky_bonuses.get("coin_discount", 0) > 0:
                summary_parts.append(f"{lucky_bonuses['coin_discount']}% merge discount")
            if lucky_bonuses.get("xp_bonus", 0) > 0:
                summary_parts.append(f"+{lucky_bonuses['xp_bonus']}% XP")
            
            if summary_parts:
                summary_lbl = QtWidgets.QLabel(f"📊 <b>Overall:</b> {' | '.join(summary_parts)}")
                summary_lbl.setTextFormat(QtCore.Qt.RichText)
                summary_lbl.setStyleSheet("color: #a78bfa; font-size: 11px; padding: 4px; background: rgba(139,92,246,0.1); border-radius: 4px;")
                self.lucky_bonuses_section.add_widget(summary_lbl)
        else:
            self.lucky_bonuses_section.setVisible(False)

    def _refresh_potential_sets_display(self) -> None:
        """Refresh the potential set bonuses display from inventory."""
        # Clear existing content in collapsible section
        self.potential_sets_section.clear_content()
        
        if not GAMIFICATION_AVAILABLE:
            self.potential_sets_section.setVisible(False)
            return
        
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        potential_sets = find_potential_set_bonuses(inventory, equipped)
        
        # Filter to only show sets that could be improved
        improvable_sets = [
            s for s in potential_sets 
            if s["inventory_count"] > 0 and s["potential_bonus"] > s["current_bonus"]
        ]
        
        if improvable_sets:
            self.potential_sets_section.setVisible(True)
            self.potential_sets_section.set_title(f"💡 Potential Set Bonuses ({len(improvable_sets)})")
            
            for s in improvable_sets[:5]:  # Show top 5 potential sets
                if s["current_bonus"] > 0:
                    # Already have some items equipped for this set
                    lbl = QtWidgets.QLabel(
                        f"{s['emoji']} {s['name']}: <b>{s['equipped_count']} equipped</b> + "
                        f"{s['inventory_count']} in bag → could be <b>+{s['potential_bonus']} power</b>"
                    )
                    lbl.setTextFormat(QtCore.Qt.RichText)
                    lbl.setStyleSheet("color: #ff9800; font-size: 11px; padding: 2px 0;")
                else:
                    # No items equipped yet
                    lbl = QtWidgets.QLabel(
                        f"{s['emoji']} {s['name']}: {s['inventory_count']} in bag → "
                        f"could be <b>+{s['potential_bonus']} power</b> (need {s['max_equippable']} equipped)"
                    )
                    lbl.setTextFormat(QtCore.Qt.RichText)
                    lbl.setStyleSheet("color: #2196f3; font-size: 11px; padding: 2px 0;")
                
                self.potential_sets_section.add_widget(lbl)
            
            tip_lbl = QtWidgets.QLabel("💡 Use 'Optimize Gear' to automatically equip the best items!")
            tip_lbl.setStyleSheet("color: #888; font-style: italic; font-size: 10px;")
            self.potential_sets_section.add_widget(tip_lbl)
        else:
            self.potential_sets_section.setVisible(False)

    def _refresh_character(self) -> None:
        """Refresh all power-related displays after gear changes."""
        if not GAMIFICATION_AVAILABLE:
            return
        # Get updated power info
        equipped = self.blocker.adhd_buster.get("equipped", {})
        power_info = get_power_breakdown(self.blocker.adhd_buster)
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        
        # Update character canvas
        self.char_canvas.equipped = equipped
        self.char_canvas.power = power_info["total_power"]
        self.char_canvas.story_theme = active_story  # Update story theme for correct character graphic
        self.char_canvas.tier = get_diary_power_tier(power_info["total_power"])  # Recalculate tier
        self.char_canvas.update()  # Trigger repaint
        
        # Update power label with all components (gear + sets + entity patrons)
        power_parts = [str(power_info['base_power'])]
        if power_info.get("set_bonus", 0) > 0:
            power_parts.append(f"+{power_info['set_bonus']} set")
        if power_info.get("entity_bonus", 0) > 0:
            power_parts.append(f"+{power_info['entity_bonus']} patrons")
        
        if len(power_parts) > 1:
            power_txt = f"⚔ Power: {power_info['total_power']} ({' '.join(power_parts)})"
        else:
            power_txt = f"⚔ Power: {power_info['total_power']}"
        self.power_lbl.setText(power_txt)
        
        # Update stats label
        total_items = len(self.blocker.adhd_buster.get("inventory", []))
        total_collected = self.blocker.adhd_buster.get("total_collected", total_items)
        streak = self.blocker.stats.get("streak_days", 0)
        self.stats_lbl.setText(f"📦 {total_items} in bag  |  🎁 {total_collected} collected  |  🔥 {streak} day streak")
        
        # XP display is now handled by the XP ring widget in the timeline header
        # (Removed the large horizontal XP bar)
        
        # Update set bonuses display
        self._refresh_sets_display(power_info)
        
        # Update entity patrons display
        if hasattr(self, 'entity_patrons_section'):
            self._refresh_entity_patrons_display()
        
        # Update potential set bonuses from inventory
        if hasattr(self, 'potential_sets_section'):
            self._refresh_potential_sets_display()
        
        # Update lucky bonuses display
        if hasattr(self, 'lucky_bonuses_section'):
            self._refresh_lucky_bonuses_display()
        
        # Update story progress labels if available
        if hasattr(self, 'story_progress_lbl'):
            self._update_story_progress_labels()
        
        # Refresh chapter list in case new chapters were unlocked
        if hasattr(self, 'chapter_combo'):
            self._refresh_story_chapter_list()
        
        # Update speech bubble with latest diary entry
        if hasattr(self, 'speech_bubble'):
            diary_entries = self.blocker.adhd_buster.get("diary", [])
            if diary_entries:
                latest = diary_entries[-1]
                entry_text = latest.get("story", "No adventures yet...")
                date_str = latest.get("short_date", latest.get("date", ""))
                tier = latest.get("tier", "unknown")
                self.speech_bubble.setText(f'"{entry_text}"\n\n— {date_str} | Tier: {tier.title()}')
            else:
                self.speech_bubble.setText("No adventures yet... Start a focus session to write your story!")

    def _refresh_all_slot_combos(self) -> None:
        """Refresh all equipment slot combo boxes with current inventory."""
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        # Rarity colors for visual distinction
        rarity_colors = {
            "Common": "#9e9e9e",
            "Uncommon": "#4caf50",
            "Rare": "#2196f3",
            "Epic": "#9c27b0",
            "Legendary": "#ff9800"
        }
        
        # Update slot labels with themed names (no rarity - shown in dropdown)
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        for slot, label in self.slot_labels.items():
            display_name = get_slot_display_name(slot, active_story) if get_slot_display_name else slot
            label.setText(f"{display_name}:")
            label.setTextFormat(QtCore.Qt.PlainText)
        
        for slot, combo in self.slot_combos.items():
            # Block signals to prevent triggering _on_equip_change
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("[Empty]")
            
            slot_items = [item for item in inventory if item.get("slot") == slot]
            for item in slot_items:
                item_name = item.get('name', 'Unknown')
                item_rarity = item.get('rarity', 'Common')
                item_color = rarity_colors.get(item_rarity, "#9e9e9e")
                power = item.get('power', 10)
                # Show full rarity name with color indicator
                display = f"{item_name} (+{power}) [{item_rarity}]"
                
                # Neighbor system removed - no longer showing indicators
                
                combo.addItem(display, item)
                # Set foreground color for this item
                idx = combo.count() - 1
                combo.setItemData(idx, QtGui.QColor(item_color), QtCore.Qt.ForegroundRole)
                
                # Build comprehensive tooltip for the item
                tooltip_parts = [f"<b style='color:{item_color};'>{item_name}</b>"]
                item_type = item.get("item_type", "")
                if item_type:
                    tooltip_parts.append(f"<i>{item_type}</i>")
                tooltip_parts.append(f"<br>⚔️ Power: +{power}")
                tooltip_parts.append(f"<br>🎭 Rarity: {item_rarity}")
                item_set = item.get("set")
                if item_set:
                    tooltip_parts.append(f"<br>🏷️ Set: {item_set}")
                
                # Neighbor system removed - no longer showing neighbor slots
                
                # Special attributes section
                has_special = False
                special_parts = []
                
                lucky_options = item.get("lucky_options", {})
                if lucky_options and format_lucky_options:
                    try:
                        lucky_text = format_lucky_options(lucky_options)
                        if lucky_text:
                            special_parts.append(f"✨ Lucky: {lucky_text}")
                            has_special = True
                    except Exception:
                        pass
                
                if has_special:
                    tooltip_parts.append("<br><br><b>✨ Special Attributes:</b>")
                    for sp in special_parts:
                        tooltip_parts.append(f"<br>  {sp}")
                
                tooltip_html = "".join(tooltip_parts)
                combo.setItemData(idx, tooltip_html, QtCore.Qt.ToolTipRole)
            
            # Re-select current equipped item if it exists in inventory
            current = equipped.get(slot)
            if current:
                found = False
                for i in range(1, combo.count()):
                    item_data = combo.itemData(i)
                    if item_data and item_data.get("obtained_at") == current.get("obtained_at"):
                        combo.setCurrentIndex(i)
                        found = True
                        break
                if not found:
                    # Item no longer in inventory (merged/deleted) - auto-unequip it
                    equipped[slot] = None
                    self.blocker.adhd_buster["equipped"] = equipped
                    self.blocker.save_config()
                    combo.setCurrentIndex(0)
                    combo.setStyleSheet("QComboBox { color: #ffffff; }")
                else:
                    # Apply color to the combo box text for selected item
                    item_rarity = current.get("rarity", "Common")
                    item_color = rarity_colors.get(item_rarity, "#9e9e9e")
                    combo.setStyleSheet(f"QComboBox {{ color: {item_color}; font-weight: bold; }}")
            else:
                combo.setCurrentIndex(0)
                combo.setStyleSheet("QComboBox { color: #ffffff; }")  # White for empty slot
            
            combo.blockSignals(False)
    
    def _refresh_slot_combo(self, slot: str) -> None:
        """Refresh a single equipment slot combo box (for targeted updates)."""
        if slot not in self.slot_combos:
            return
        
        combo = self.slot_combos[slot]
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        rarity_colors = {
            "Common": "#9e9e9e",
            "Uncommon": "#4caf50",
            "Rare": "#2196f3",
            "Epic": "#9c27b0",
            "Legendary": "#ff9800"
        }
        
        # Update slot label
        if slot in self.slot_labels:
            label = self.slot_labels[slot]
            active_story = self.blocker.adhd_buster.get("active_story", "warrior")
            display_name = get_slot_display_name(slot, active_story) if get_slot_display_name else slot
            current_item = equipped.get(slot)
            if current_item:
                rarity = current_item.get("rarity", "Common")
                color = rarity_colors.get(rarity, "#9e9e9e")
                label.setText(f'{display_name}: <span style="color:{color}; font-weight:bold;">[{rarity}]</span>')
                label.setTextFormat(QtCore.Qt.RichText)
            else:
                label.setText(f"{display_name}:")
                label.setTextFormat(QtCore.Qt.PlainText)
        
        # Refresh combo box
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("[Empty]")
        
        slot_items = [item for item in inventory if item.get("slot") == slot]
        for item in slot_items:
            item_name = item.get('name', 'Unknown')
            item_rarity = item.get('rarity', 'Common')
            item_color = rarity_colors.get(item_rarity, "#9e9e9e")
            power = item.get('power', 10)
            display = f"{item_name} (+{power}) [{item_rarity}]"
            
            combo.addItem(display, item)
            idx = combo.count() - 1
            combo.setItemData(idx, QtGui.QColor(item_color), QtCore.Qt.ForegroundRole)
        
        # Select currently equipped item
        current = equipped.get(slot)
        if current:
            found = False
            for i in range(1, combo.count()):
                item_data = combo.itemData(i)
                if item_data and item_data.get("obtained_at") == current.get("obtained_at"):
                    combo.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                # Item no longer in inventory (merged/deleted) - auto-unequip it
                equipped[slot] = None
                self.blocker.adhd_buster["equipped"] = equipped
                self.blocker.save_config()
                combo.setCurrentIndex(0)
                combo.setStyleSheet("QComboBox { color: #ffffff; }")
            else:
                item_rarity = current.get("rarity", "Common")
                item_color = rarity_colors.get(item_rarity, "#9e9e9e")
                combo.setStyleSheet(f"QComboBox {{ color: {item_color}; font-weight: bold; }}")
        else:
            combo.setCurrentIndex(0)
            combo.setStyleSheet("QComboBox { color: #ffffff; }")  # White for empty slot
        
        combo.blockSignals(False)

    def _is_item_equipped(self, item: dict, equipped: dict) -> bool:
        """Check if an item is currently equipped using multiple methods.
        
        Uses timestamp matching as primary check, falls back to name+slot+rarity
        matching for items without timestamps (legacy data).
        """
        if not item or not equipped:
            return False
        
        item_ts = item.get("obtained_at")
        item_name = item.get("name", "")
        item_slot = item.get("slot", "")
        item_rarity = item.get("rarity", "")
        
        for slot, eq_item in equipped.items():
            if not eq_item:
                continue
            
            # Primary check: timestamp match
            eq_ts = eq_item.get("obtained_at")
            if item_ts and eq_ts and item_ts == eq_ts:
                return True
            
            # Fallback for items without timestamps: match by name, slot, and rarity
            if (not item_ts or not eq_ts):
                if (eq_item.get("name") == item_name and 
                    eq_item.get("slot") == item_slot and
                    eq_item.get("rarity") == item_rarity):
                    return True
        
        return False

    def _refresh_inventory(self) -> None:
        self.inv_table.setSortingEnabled(False)
        self.inv_table.setRowCount(0)
        self.merge_selected = []
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")

        # Basic sorting for initial list (Table widget handles UI sorting)
        rarity_order = {"Common": 0, "Uncommon": 1, "Rare": 2, "Epic": 3, "Legendary": 4}
        rarity_colors = {
            "Common": "#9e9e9e",
            "Uncommon": "#4caf50",
            "Rare": "#2196f3",
            "Epic": "#9c27b0",
            "Legendary": "#ff9800"
        }
        sort_key = self.sort_combo.currentData() or "newest"
        indexed = list(enumerate(inventory))
        
        # Presort logic (optional now that table sorting is enabled)
        if sort_key == "rarity":
            indexed.sort(key=lambda x: rarity_order.get(x[1].get("rarity", "Common"), 0), reverse=True)
        elif sort_key == "slot":
            indexed.sort(key=lambda x: x[1].get("slot", ""))
        elif sort_key == "power":
            indexed.sort(key=lambda x: x[1].get("power", 10), reverse=True)
        elif sort_key == "lucky":
            def lucky_sort_key(item_tuple):
                item = item_tuple[1]
                lucky_opts = item.get("lucky_options", {})
                has_lucky = 1 if lucky_opts else 0
                num_opts = len(lucky_opts) if lucky_opts else 0
                power = item.get("power", 10)
                return (has_lucky, num_opts, power)
            indexed.sort(key=lucky_sort_key, reverse=True)
        else:
            indexed.reverse()

        # Update inventory stats
        lucky_items_count = sum(1 for item in inventory if item.get("lucky_options", {}))
        total_items = len(inventory)
        if hasattr(self, 'inv_stats_label'):
            stats_text = f"Total: {total_items} items"
            if lucky_items_count > 0:
                stats_text += f" | ✨ Lucky: {lucky_items_count} ({lucky_items_count*100//total_items if total_items > 0 else 0}%)"
            self.inv_stats_label.setText(stats_text)

        self.inv_table.setRowCount(len(indexed))
        
        # Neighbor system removed - no longer needed

        for row, (orig_idx, item) in enumerate(indexed):
            is_eq = self._is_item_equipped(item, equipped)
            item_name = item.get("name", "Unknown Item")
            item_type = item.get("item_type", "")
            item_rarity = item.get("rarity", "Common")
            power = item.get("power", RARITY_POWER.get(item_rarity, 10))
            item_set = item.get("set", "")
            slot = item.get("slot", "Unknown")
            slot_display = get_slot_display_name(slot, active_story) if get_slot_display_name else slot
            rarity_color = rarity_colors.get(item_rarity, "#9e9e9e")
            
            lucky_options = item.get("lucky_options", {})
            coin_discount = lucky_options.get("coin_discount", 0)
            xp_bonus = lucky_options.get("xp_bonus", 0)
            merge_luck = lucky_options.get("merge_luck", 0)
            
            # Helper: Create read-only item
            def create_item(text, align=QtCore.Qt.AlignLeft):
                it = QtWidgets.QTableWidgetItem(str(text))
                it.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                it.setTextAlignment(align)
                # Don't gray out equipped items - the Eq column already shows status
                if is_eq:
                    it.setFlags(it.flags() & ~QtCore.Qt.ItemIsSelectable) 
                return it

            # 0: Equipped
            eq_item = create_item("✓" if is_eq else "", QtCore.Qt.AlignCenter)
            if is_eq:
                eq_item.setForeground(QtGui.QColor("#4caf50"))
            eq_item.setToolTip("Equipped" if is_eq else "Not Equipped")
            self.inv_table.setItem(row, 0, eq_item)
            
            # 1: Name
            name_prefix = "✨ " if lucky_options else ""
            name_item = create_item(f"{name_prefix}{item_name}")
            name_item.setForeground(QtGui.QColor(rarity_color))
            name_item.setData(QtCore.Qt.UserRole, orig_idx)
            name_item.setToolTip(f"{item_name}\nRarity: {item_rarity}\n{'Equipped' if is_eq else 'In Inventory'}")
            self.inv_table.setItem(row, 1, name_item)
            
            # 2: Slot
            slot_item = create_item(slot_display[:4], QtCore.Qt.AlignCenter)
            slot_item.setToolTip(f"Slot: {slot_display}")
            self.inv_table.setItem(row, 2, slot_item)
            
            # 3: Tier
            tier_item = create_item(item_rarity[:1], QtCore.Qt.AlignCenter)
            tier_item.setForeground(QtGui.QColor(rarity_color))
            tier_item.setToolTip(f"Rarity: {item_rarity}")
            self.inv_table.setItem(row, 3, tier_item)
            
            # 4: Power
            pwr_item = create_item(str(power), QtCore.Qt.AlignCenter)
            pwr_item.setToolTip(f"Power Level: {power}")
            self.inv_table.setItem(row, 4, pwr_item)
            
            # 5: Set
            set_item = create_item(item_set if item_set else "-", QtCore.Qt.AlignCenter)
            set_item.setToolTip(f"Set: {item_set}" if item_set else "No Set")
            self.inv_table.setItem(row, 5, set_item)
            
            # 6: Coin
            coin_text = f"{coin_discount}%" if coin_discount else ""
            coin_item = create_item(coin_text, QtCore.Qt.AlignCenter)
            if coin_discount: coin_item.setForeground(QtGui.QColor("#fbbf24"))
            coin_item.setToolTip(f"Coin Discount: {coin_discount}% off merge costs")
            self.inv_table.setItem(row, 6, coin_item)
            
            # 7: XP
            xp_text = f"{xp_bonus}%" if xp_bonus else ""
            xp_item = create_item(xp_text, QtCore.Qt.AlignCenter)
            if xp_bonus: xp_item.setForeground(QtGui.QColor("#8b5cf6"))
            xp_item.setToolTip(f"XP Bonus: +{xp_bonus}%")
            self.inv_table.setItem(row, 7, xp_item)
            
            # 8: Merge
            merge_text = f"{merge_luck}%" if merge_luck else ""
            merge_item = create_item(merge_text, QtCore.Qt.AlignCenter)
            if merge_luck: merge_item.setForeground(QtGui.QColor("#06b6d4"))
            merge_item.setToolTip(f"Merge Luck: +{merge_luck}%")
            self.inv_table.setItem(row, 8, merge_item)
            
            self.inv_table.setRowHeight(row, 24)
            
        self.inv_table.setSortingEnabled(True)

    def refresh_gear_combos(self) -> None:
        """Refresh gear dropdown combos to reflect new inventory items.
        
        This is called externally (e.g., after item drops), so it uses
        the comprehensive refresh_all() method.
        """
        self.refresh_all()

    def _update_merge_selection(self) -> None:
        # Get selected indices from table (column 1 stores the UserRole data - Name column)
        selected_rows = set(item.row() for item in self.inv_table.selectedItems())
        raw_selected = []
        for row in selected_rows:
            item = self.inv_table.item(row, 1)  # Name column has UserRole data
            if item:
                idx = item.data(QtCore.Qt.UserRole)
                if idx is not None:
                    raw_selected.append(idx)
        self.merge_selected = [idx for idx in raw_selected if isinstance(idx, int)]
        
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        # Filter to only valid indices within inventory bounds
        valid_indices = [idx for idx in self.merge_selected if 0 <= idx < len(inventory)]
        count = len(valid_indices)
        
        self.merge_btn.setText(f"🎲 Merge Selected ({count})")
        
        # Never enable merge during active session
        if self._session_active:
            self.merge_btn.setEnabled(False)
            self.merge_rate_lbl.setText("🔒 Merging disabled during focus session")
            return
        
        if count >= 2 and GAMIFICATION_AVAILABLE:
            items = [inventory[idx] for idx in valid_indices]
            
            # Check if any selected items are equipped (using robust check)
            equipped_selected = [i for i in items if self._is_item_equipped(i, equipped)]
            if equipped_selected:
                self.merge_btn.setEnabled(False)
                self.merge_rate_lbl.setText("⚠️ Cannot merge equipped items!")
                return
            
            worthwhile, reason = is_merge_worthwhile(items)
            if not worthwhile:
                self.merge_btn.setEnabled(False)
                self.merge_rate_lbl.setText(f"⚠️ {reason}")
            else:
                self.merge_btn.setEnabled(True)
                
                # Calculate merge luck from items being merged (not equipped gear)
                # This encourages sacrificing items with merge_luck for better odds
                items_merge_luck = 0
                for item in items:
                    if item and isinstance(item, dict):
                        lucky_opts = item.get("lucky_options", {})
                        if isinstance(lucky_opts, dict):
                            items_merge_luck += lucky_opts.get("merge_luck", 0)
                
                rate = calculate_merge_success_rate(items, items_merge_luck=items_merge_luck)
                result_rarity = get_merge_result_rarity(items)
                all_legendary = all(i.get("rarity") == "Legendary" for i in items)
                if all_legendary:
                    # Legendary-only merges act as a reroll to a new legendary item/slot.
                    if items_merge_luck > 0:
                        self.merge_rate_lbl.setText(
                            f"Legendary reroll: {rate*100:.0f}% (+{items_merge_luck}% from items) → Legendary item"
                        )
                    else:
                        self.merge_rate_lbl.setText(
                            f"Legendary reroll: {rate*100:.0f}% → Legendary item"
                        )
                else:
                    if items_merge_luck > 0:
                        self.merge_rate_lbl.setText(f"Success rate: {rate*100:.0f}% (+{items_merge_luck}% from items) → {result_rarity} item")
                    else:
                        self.merge_rate_lbl.setText(f"Success rate: {rate*100:.0f}% → {result_rarity} item")
        else:
            self.merge_btn.setEnabled(False)
            self.merge_rate_lbl.setText("Select 2+ items to merge")

    def _update_item_details_panel(self) -> None:
        pass
        # DEPRECATED
        """Update the item details panel based on current selection."""
        return
        # Get selected rows from table
        selected_rows = set(item.row() for item in self.inv_table.selectedItems())
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        
        if not selected_rows:
            # No selection - show placeholder
            self.details_name.setText("Select an item to view details")
            self.details_item_type.setText("")
            self.details_rarity.setText("Rarity: -")
            self.details_slot.setText("Slot: -")
            self.details_power.setText("Power: -")
            self.details_set.setText("Set: -")
            self.details_neighbors.setText("Neighbors: -")
            # Clear special attributes container
            while self.details_special_layout.count():
                child = self.details_special_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.details_special_header.setVisible(False)
            self.details_special_container.setVisible(False)
            self.details_status.setText("")
            return
        
        # Show details for the last selected row
        last_row = max(selected_rows)
        name_item = self.inv_table.item(last_row, 0)
        if not name_item:
            return
        idx = name_item.data(QtCore.Qt.UserRole)
        
        if not isinstance(idx, int) or idx < 0 or idx >= len(inventory):
            return
        
        item = inventory[idx]
        
        # Item name with rarity color
        rarity = item.get("rarity", "Common")
        rarity_colors = {
            "Common": "#9e9e9e",
            "Uncommon": "#4caf50",
            "Rare": "#2196f3",
            "Epic": "#9c27b0",
            "Legendary": "#ff9800"
        }
        color = rarity_colors.get(rarity, "#9e9e9e")
        self.details_name.setText(item.get("name", "Unknown Item"))
        self.details_name.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {color}; border: none;")
        
        # Item type (from the item_type field)
        item_type = item.get("item_type", "")
        if item_type:
            self.details_item_type.setText(f"Type: {item_type}")
        else:
            self.details_item_type.setText("")
        
        # Core stats
        self.details_rarity.setText(f"Rarity: {rarity}")
        self.details_rarity.setStyleSheet(f"color: {color}; border: none;")
        
        slot = item.get("slot", "Unknown")
        slot_display = get_slot_display_name(slot, active_story) if get_slot_display_name else slot
        self.details_slot.setText(f"Slot: {slot_display}")
        
        power = item.get("power", 10)
        self.details_power.setText(f"Power: +{power}")
        
        item_set = item.get("set", None)
        self.details_set.setText(f"Set: {item_set}" if item_set else "Set: None")
        
        # Neighbor system removed - hide neighbor display
        self.details_neighbors.setText("Neighbors: (System Removed)")
        self.details_neighbors.setVisible(False)
        
        # Special attributes - build dynamic list
        # Clear existing special attribute labels
        while self.details_special_layout.count():
            child = self.details_special_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        special_attrs = []
        
        # Lucky options - show each individually
        lucky_options = item.get("lucky_options", {})
        if lucky_options:
            option_info = {
                "coin_discount": ("💰 Coin Discount", "#fbbf24"),
                "xp_bonus": ("⭐ XP Bonus", "#8b5cf6"),
                "merge_luck": ("🎲 Merge Luck", "#06b6d4")
            }
            for opt_key, (opt_name, opt_color) in option_info.items():
                value = lucky_options.get(opt_key, 0)
                if value > 0:
                    special_attrs.append((opt_name, f"+{value}%", opt_color))
        
        # Add labels for each special attribute
        for attr_name, attr_value, attr_color in special_attrs:
            lbl = QtWidgets.QLabel(f"{attr_name}: {attr_value}")
            lbl.setStyleSheet(f"color: {attr_color}; border: none; padding-left: 8px;")
            self.details_special_layout.addWidget(lbl)
        
        # Show/hide special header based on whether there are special attributes
        has_special = len(special_attrs) > 0
        self.details_special_header.setVisible(has_special)
        self.details_special_container.setVisible(has_special)
        
        # Equipped status
        is_eq = self._is_item_equipped(item, equipped)
        if is_eq:
            self.details_status.setText("✓ Currently Equipped")
            self.details_status.setStyleSheet("color: #4caf50; font-style: italic; border: none;")
        else:
            # Show obtained date if available
            obtained = item.get("obtained_at", "")
            if obtained:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(obtained)
                    self.details_status.setText(f"Obtained: {dt.strftime('%b %d, %Y')}")
                except Exception:
                    self.details_status.setText("")
            else:
                self.details_status.setText("")
            self.details_status.setStyleSheet("color: #888; font-style: italic; border: none;")

    def _do_merge(self) -> None:
        if len(self.merge_selected) < 2:
            return
        if not GAMIFICATION_AVAILABLE:
            show_warning(self, "Feature Unavailable", "Gamification features are not available.")
            return
        
        # Re-fetch inventory fresh to avoid stale indices
        inventory = self.blocker.adhd_buster.get("inventory", [])
        
        # Validate indices are integers and within bounds
        valid_indices = [idx for idx in self.merge_selected if isinstance(idx, int) and 0 <= idx < len(inventory)]
        if len(valid_indices) < 2:
            show_warning(self, "Invalid Selection", 
                "Selected items are no longer valid. Please refresh and try again.")
            self._refresh_inventory()
            return

        # Check if player has enough coins for the discounted base merge cost
        from gamification import COIN_COSTS, calculate_merge_discount, apply_coin_discount, apply_coin_flat_reduction, get_entity_merge_perk_contributors
        current_coins = self.blocker.adhd_buster.get("coins", 0)
        temp_discount = calculate_merge_discount([inventory[idx] for idx in valid_indices])
        
        # Get entity flat coin reduction
        entity_perks = get_entity_merge_perk_contributors(self.blocker.adhd_buster)
        entity_coin_flat = entity_perks.get("total_coin_discount", 0)
        
        temp_base_cost = apply_coin_flat_reduction(
            apply_coin_discount(COIN_COSTS.get("merge_base", 50), temp_discount),
            entity_coin_flat
        )
        if current_coins < temp_base_cost:
            show_warning(self, "Not Enough Coins", 
                f"Lucky Merge base cost is {temp_base_cost} coins after discount.\n\n"
                f"You have: {current_coins} coins\n"
                f"You need: {temp_base_cost - current_coins} more coins\n\n"
                f"Complete focus sessions to earn more coins!")
            return
        
        items = [inventory[idx] for idx in valid_indices]
        
        # Check for items without timestamps (data integrity issue)
        items_without_ts = [i for i in items if not i.get("obtained_at")]
        if items_without_ts:
            # Add timestamps to fix data integrity
            for item in items_without_ts:
                item["obtained_at"] = datetime.now().isoformat()
            self.blocker.save_config()
        
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        # Calculate coin discount from items being merged (not equipped)
        from gamification import calculate_merge_discount
        coin_discount = calculate_merge_discount(items)
        
        # Show new professional merge dialog with player coins for boost option
        from merge_dialog import LuckyMergeDialog
        dialog = LuckyMergeDialog(items, 0, equipped, parent=self, player_coins=current_coins, 
                                  coin_discount=coin_discount, entity_perks=entity_perks)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return
        
        # Get result from dialog
        result = dialog.merge_result
        if not result:
            return
        
        # Calculate total cost (base + optional boost + tier upgrade) using centralized costs
        from gamification import COIN_COSTS, apply_coin_discount, apply_coin_flat_reduction
        boost_enabled = getattr(dialog, 'boost_enabled', False)
        tier_upgrade_enabled = getattr(dialog, 'tier_upgrade_enabled', False)
        
        # Calculate discount from ITEMS BEING MERGED (not equipped)
        discount_pct = calculate_merge_discount(items)
        
        # Get entity flat coin reduction from dialog
        entity_coin_flat = getattr(dialog, 'entity_coin_flat', 0)
        
        # Calculate costs: percentage discount first, then flat reduction
        base_cost = apply_coin_flat_reduction(apply_coin_discount(COIN_COSTS.get("merge_base", 50), discount_pct), entity_coin_flat)
        boost_cost = apply_coin_flat_reduction(apply_coin_discount(COIN_COSTS.get("merge_boost", 50), discount_pct), entity_coin_flat) if boost_enabled else 0
        tier_upgrade_cost = apply_coin_flat_reduction(apply_coin_discount(COIN_COSTS.get("merge_tier_upgrade", 50), discount_pct), entity_coin_flat) if tier_upgrade_enabled else 0
        # Add retry costs if any
        retry_cost = getattr(dialog, 'retry_cost_accumulated', 0)
        
        # Add claim cost if item was claimed via near-miss recovery (discounted)
        claim_cost = 0
        if result.get("claimed_with_coins"):
            claim_cost = apply_coin_flat_reduction(apply_coin_discount(COIN_COSTS.get("merge_claim", 100), discount_pct), entity_coin_flat)
            
        total_cost = base_cost + boost_cost + tier_upgrade_cost + retry_cost + claim_cost
        
        # Re-validate inventory state BEFORE spending coins
        inventory = self.blocker.adhd_buster.get("inventory", [])
        if not all(0 <= idx < len(inventory) for idx in valid_indices):
            show_warning(self, "Inventory Changed", 
                "Inventory changed during merge. Please try again.")
            self._refresh_inventory()
            return
        
        # Re-fetch items with fresh inventory
        items = [inventory[idx] for idx in valid_indices]
        
        # Final safety check: ensure no equipped items are being merged (using robust check)
        equipped = self.blocker.adhd_buster.get("equipped", {})
        equipped_in_merge = [i for i in items if self._is_item_equipped(i, equipped)]
        if equipped_in_merge:
            show_warning(
                self, "Cannot Merge",
                f"Cannot merge equipped items! Unequip them first.\n\n"
                f"Equipped items selected: {len(equipped_in_merge)}"
            )
            return
        
        # Spend coins for the merge attempt (AFTER all validation passes)
        # total_cost includes base cost + optional boost
        if self._game_state:
            if not self._game_state.spend_coins(total_cost):
                show_warning(self, "Error", f"Failed to spend {total_cost} coins for merge.")
                return
        else:
            # Fallback: directly deduct coins if no game state manager
            current_coins = self.blocker.adhd_buster.get("coins", 0)
            if current_coins < total_cost:
                show_warning(self, "Error", f"Not enough coins for merge (need {total_cost}).")
                return
            self.blocker.adhd_buster["coins"] = current_coins - total_cost
            self.blocker.save_config()
        
        # Check for salvage (player paid to save one random item)
        salvaged_item = result.get("salvaged_item")
        salvage_cost = result.get("salvage_cost", 0)
        if salvaged_item and salvage_cost > 0:
            # Deduct salvage cost
            if self._game_state:
                self._game_state.spend_coins(salvage_cost)
            else:
                current_coins = self.blocker.adhd_buster.get("coins", 0)
                self.blocker.adhd_buster["coins"] = max(0, current_coins - salvage_cost)
                self.blocker.save_config()
            
            # Remove the salvaged item from the items to be deleted
            items = [i for i in items if i.get("obtained_at") != salvaged_item.get("obtained_at")]
        
        # Use GameState manager to perform the merge atomically
        if self._game_state:
            self._game_state.perform_merge(items, result.get("result_item"), result["success"])
            # Sync changes to active hero
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
        else:
            show_warning(self, "Error", "Game State Manager not initialized. Cannot merge.")
            return
        
        # Result feedback already shown by dialog
        # Clear merge selection
        self.merge_selected = []
        
        # Show perk toast if entity perks contributed to the merge
        if entity_perks.get("coin_discount", 0) > 0 or entity_perks.get("merge_luck", 0) > 0:
            perk_parts = []
            if entity_perks.get("coin_discount", 0) > 0:
                perk_parts.append(f"-{entity_perks['coin_discount']}% coins")
            if entity_perks.get("merge_luck", 0) > 0:
                perk_parts.append(f"+{entity_perks['merge_luck']}% luck")
            if perk_parts:
                show_perk_toast(f"Entity Perks: {', '.join(perk_parts)}", "✨", self)
        
        # Only do manual refresh if GameState not available
        if not self._game_state:
            self.refresh_all()

    def _on_story_change(self, index: int) -> None:
        """Handle story selection change."""
        if not GAMIFICATION_AVAILABLE:
            return
        
        story_id = self.story_combo.currentData()
        if not story_id:
            return
        
        from gamification import select_story, get_selected_story, COIN_COSTS
        current = get_selected_story(self.blocker.adhd_buster)
        
        if story_id != current:
            # Check if story needs to be unlocked (costs coins)
            STORY_UNLOCK_COST = COIN_COSTS.get("story_unlock", 100)
            unlocked_stories = self.blocker.adhd_buster.get("unlocked_stories", ["underdog"])  # Underdog is free
            
            if story_id not in unlocked_stories:
                current_coins = self.blocker.adhd_buster.get("coins", 0)
                if current_coins < STORY_UNLOCK_COST:
                    show_warning(self, "Story Locked", 
                        f"This story costs {STORY_UNLOCK_COST} coins to unlock.\n\n"
                        f"You have: {current_coins} coins\n"
                        f"You need: {STORY_UNLOCK_COST - current_coins} more coins\n\n"
                        f"Complete focus sessions to earn more coins!")
                    # Revert combo
                    self.story_combo.blockSignals(True)
                    for i in range(self.story_combo.count()):
                        if self.story_combo.itemData(i) == current:
                            self.story_combo.setCurrentIndex(i)
                            break
                    self.story_combo.blockSignals(False)
                    return
                
                # Ask to unlock
                from gamification import AVAILABLE_STORIES
                story_info = AVAILABLE_STORIES.get(story_id, {})
                story_title = story_info.get("title", story_id)
                reply = show_question(
                    self, "Unlock Story?",
                    f"Unlock '{story_title}' for {STORY_UNLOCK_COST} coins?\n\n"
                    f"You have: {current_coins} coins\n"
                    f"After unlock: {current_coins - STORY_UNLOCK_COST} coins",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if reply != QtWidgets.QMessageBox.Yes:
                    self.story_combo.blockSignals(True)
                    for i in range(self.story_combo.count()):
                        if self.story_combo.itemData(i) == current:
                            self.story_combo.setCurrentIndex(i)
                            break
                    self.story_combo.blockSignals(False)
                    return
                
                # Spend coins and unlock story
                if self._game_state:
                    if not self._game_state.spend_coins(STORY_UNLOCK_COST):
                        show_warning(self, "Error", "Failed to spend coins.")
                        return
                else:
                    # Fallback: directly deduct coins if no game state manager
                    current_coins = self.blocker.adhd_buster.get("coins", 0)
                    if current_coins < STORY_UNLOCK_COST:
                        show_warning(self, "Error", "Not enough coins.")
                        return
                    self.blocker.adhd_buster["coins"] = current_coins - STORY_UNLOCK_COST
                
                # Add to unlocked stories
                if "unlocked_stories" not in self.blocker.adhd_buster:
                    self.blocker.adhd_buster["unlocked_stories"] = ["underdog"]
                self.blocker.adhd_buster["unlocked_stories"].append(story_id)
                self.blocker.save_config()
                show_info(self, "Story Unlocked! 🎉", f"You've unlocked '{story_title}'!")
                
                # Refresh story combo to update lock icons
                self._refresh_story_combo()
            else:
                # Story already unlocked - just confirm switch
                reply = show_question(
                    self, "Switch Story?",
                    f"Each story has its own hero with separate gear and progress.\n\n"
                    f"Switching will load your hero for this story.\n"
                    f"(Your current hero's progress will be saved.)\n\n"
                    f"Switch to the new story?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )
                if reply != QtWidgets.QMessageBox.Yes:
                    # Revert combo to current story - block signals to prevent recursion
                    self.story_combo.blockSignals(True)
                    for i in range(self.story_combo.count()):
                        if self.story_combo.itemData(i) == current:
                            self.story_combo.setCurrentIndex(i)
                            break
                    self.story_combo.blockSignals(False)
                    return
        
        select_story(self.blocker.adhd_buster, story_id)
        self.blocker.save_config()
        
        # Comprehensive refresh for the new hero (includes story description, progress, chapters)
        self.refresh_all()

    def _on_restart_story(self) -> None:
        """Handle restart story button click - reset current story's hero."""
        if not GAMIFICATION_AVAILABLE:
            return
        
        from gamification import restart_story, get_selected_story, AVAILABLE_STORIES
        
        story_id = get_selected_story(self.blocker.adhd_buster)
        story_info = AVAILABLE_STORIES.get(story_id, {})
        story_title = story_info.get("title", story_id)
        
        # Confirm with serious warning
        reply = show_question(
            self, "⚠️ Restart Story?",
            f"Are you sure you want to RESTART '{story_title}'?\n\n"
            f"This will DELETE:\n"
            f"  ❌ All gear and inventory for this story\n"
            f"  ❌ All story decisions and progress\n"
            f"  ❌ All chapters unlocked\n\n"
            f"Your hero will start from Chapter 1 with nothing.\n\n"
            f"This CANNOT be undone!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No  # Default to No
        )
        
        if reply != QtWidgets.QMessageBox.Yes:
            return
        
        # Double-confirm for safety
        confirm = show_question(
            self, "Final Confirmation",
            f"Type of restart: FULL RESET\n\n"
            f"Really delete all progress for '{story_title}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if confirm != QtWidgets.QMessageBox.Yes:
            return
        
        # Perform the restart
        success = restart_story(self.blocker.adhd_buster, story_id)
        
        if success:
            self.blocker.save_config()
            
            # Comprehensive refresh (includes story description, progress, chapters)
            self.refresh_all()
            
            show_info(
                self, "Story Restarted",
                f"'{story_title}' has been reset!\n\n"
                f"Your hero begins anew at Chapter 1.\n"
                f"Good luck on your fresh journey! 🌟"
            )
        else:
            show_error(
                self, "Error",
                "Failed to restart story. Please try again."
            )

    def _save_inventory_state(self) -> None:
        """Save inventory table column configuration."""
        try:
            settings = QtCore.QSettings("PersonalFreedom", "FocusBlocker")
            header_state = self.inv_table.horizontalHeader().saveState()
            settings.setValue("inventory_header_state", header_state)
        except Exception as e:
            print(f"Error saving inventory state: {e}")

    def _load_inventory_state(self) -> None:
        """Load inventory table column configuration."""
        try:
            settings = QtCore.QSettings("PersonalFreedom", "FocusBlocker")
            header_state = settings.value("inventory_header_state")
            if header_state:
                self.inv_table.horizontalHeader().restoreState(header_state)
        except Exception as e:
            print(f"Error loading inventory state: {e}")

    def _on_mode_radio_changed(self) -> None:
        """Handle mode radio button change."""
        if not GAMIFICATION_AVAILABLE:
            return

        # Determine which mode is selected
        if self.mode_disabled_radio.isChecked():
            new_mode = STORY_MODE_DISABLED
        elif self.mode_hero_radio.isChecked():
            new_mode = STORY_MODE_HERO_ONLY
        else:
            new_mode = STORY_MODE_ACTIVE

        current_mode = get_story_mode(self.blocker.adhd_buster)
        if new_mode == current_mode:
            return

        # Sync any pending changes before mode switch
        sync_hero_data(self.blocker.adhd_buster)

        if new_mode == STORY_MODE_ACTIVE:
            # Switch to story mode - use current active story
            story_id = self.blocker.adhd_buster.get("active_story", "warrior")
            switch_story(self.blocker.adhd_buster, story_id)
        else:
            set_story_mode(self.blocker.adhd_buster, new_mode)

        self.blocker.save_config()

        # Update UI to reflect mode change
        self._update_mode_ui_state()
        self.refresh_all()

    def _update_mode_ui_state(self) -> None:
        """Update UI elements based on current mode (enable/disable story controls)."""
        if not GAMIFICATION_AVAILABLE:
            return
        enabled = is_gamification_enabled(self.blocker.adhd_buster)
        current_mode = get_story_mode(self.blocker.adhd_buster)
        story_mode = current_mode == STORY_MODE_ACTIVE
        
        # Sync radio button selection with current mode (block signals to prevent loop)
        if hasattr(self, 'mode_story_radio'):
            self.mode_story_radio.blockSignals(True)
            self.mode_hero_radio.blockSignals(True)
            self.mode_disabled_radio.blockSignals(True)
            
            if current_mode == STORY_MODE_HERO_ONLY:
                self.mode_hero_radio.setChecked(True)
            elif current_mode == STORY_MODE_DISABLED:
                self.mode_disabled_radio.setChecked(True)
            else:
                self.mode_story_radio.setChecked(True)
            
            self.mode_story_radio.blockSignals(False)
            self.mode_hero_radio.blockSignals(False)
            self.mode_disabled_radio.blockSignals(False)
        
        # Enable story combo only in story mode
        if hasattr(self, "story_combo"):
            self.story_combo.setEnabled(story_mode)
        if hasattr(self, "chapter_combo"):
            self.chapter_combo.setEnabled(story_mode)
    
    def _update_story_description(self) -> None:
        """Update the story description label."""
        if not GAMIFICATION_AVAILABLE or not hasattr(self, 'story_desc_lbl'):
            return
        
        from gamification import AVAILABLE_STORIES, get_selected_story
        story_id = get_selected_story(self.blocker.adhd_buster)
        story_info = AVAILABLE_STORIES.get(story_id, {})
        self.story_desc_lbl.setText(f"📖 {story_info.get('description', '')}")
    
    def _update_story_progress_labels(self) -> None:
        """Update story progress labels and progress bar."""
        if not GAMIFICATION_AVAILABLE:
            return
        
        from gamification import get_story_progress
        progress = get_story_progress(self.blocker.adhd_buster)
        
        if hasattr(self, 'story_progress_lbl'):
            self.story_progress_lbl.setText(
                f"📖 Chapters Unlocked: {len(progress['unlocked_chapters'])}/{progress['total_chapters']}  |  "
                f"⚔ Power: {progress['power']}  |  "
                f"⚡ Decisions: {progress['decisions_made']}/3"
            )
        
        if hasattr(self, 'story_next_lbl'):
            if progress['next_threshold']:
                self.story_next_lbl.setText(
                    f"🔒 Next chapter unlocks at {progress['next_threshold']} power "
                    f"({progress['power_to_next']} more needed)"
                )
                self.story_next_lbl.setStyleSheet("color: #666;")
            else:
                self.story_next_lbl.setText("✨ You have unlocked the entire story!")
                self.story_next_lbl.setStyleSheet("color: #4caf50; font-weight: bold;")
        
        # Update progress bar
        if hasattr(self, 'chapter_progress_bar'):
            unlocked = len(progress['unlocked_chapters'])
            total = progress['total_chapters']
            
            if progress['next_threshold']:
                prev_threshold = progress.get('prev_threshold', 0)
                next_threshold = progress['next_threshold']
                current_power = progress['power']
                next_chapter = unlocked + 1
                
                # Calculate progress percentage within current chapter range
                range_size = next_threshold - prev_threshold
                if range_size > 0:
                    progress_in_range = current_power - prev_threshold
                    percentage = int((progress_in_range / range_size) * 100)
                    percentage = max(0, min(100, percentage))  # Clamp to 0-100
                else:
                    percentage = 100
                
                self.chapter_progress_bar.setValue(percentage)
                self.chapter_progress_bar.setFormat(
                    f"Ch {unlocked}/{total} | {current_power} → {next_threshold} power ({percentage}% to Ch {next_chapter})"
                )
                self.chapter_progress_bar.setVisible(True)
            else:
                # All chapters unlocked
                self.chapter_progress_bar.setValue(100)
                self.chapter_progress_bar.setFormat("✨ Story Complete!")
                self.chapter_progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #444;
                        border-radius: 5px;
                        text-align: center;
                        height: 20px;
                    }
                    QProgressBar::chunk {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #ffd700, stop:0.5 #ffcc00, stop:1 #ffaa00);
                        border-radius: 4px;
                    }
                """)

    def _read_story_chapter(self) -> None:
        """Open a dialog to read the selected story chapter."""
        if not GAMIFICATION_AVAILABLE:
            show_warning(self, "Story", "Story system requires gamification module.")
            return
        
        chapter_num = self.chapter_combo.currentData()
        if not chapter_num:
            return
        
        import re
        def format_story_text(text: str) -> str:
            """Convert markdown-like text to HTML."""
            formatted = text.strip()
            # Bold: **text** -> <b>text</b>
            formatted = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', formatted)
            # Italic: *text* -> <i>text</i> (but not inside bold tags)
            formatted = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', formatted)
            # Paragraphs and line breaks
            formatted = formatted.replace("\n\n", "</p><p>")
            formatted = formatted.replace("\n", "<br>")
            return f"<p style='font-size: 13px; line-height: 1.6;'>{formatted}</p>"
        
        from gamification import get_chapter_content, get_decision_for_chapter, has_made_decision, make_story_decision
        chapter = get_chapter_content(chapter_num, self.blocker.adhd_buster)
        
        if not chapter:
            return
        
        # Create story dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"📜 {chapter['title']}")
        dialog.resize(650, 550)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Title
        title_lbl = QtWidgets.QLabel(f"<h2>{chapter['title']}</h2>")
        title_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)
        
        if not chapter['unlocked']:
            # Locked chapter
            lock_lbl = QtWidgets.QLabel(
                f"<p style='font-size: 48px; text-align: center;'>🔒</p>"
                f"<p style='text-align: center; font-size: 14px;'>"
                f"This chapter is locked.<br><br>"
                f"<b>Required Power:</b> {chapter['threshold']}<br>"
                f"<b>Your Power:</b> {chapter['threshold'] - chapter['power_needed']}<br>"
                f"<b>Power Needed:</b> {chapter['power_needed']}<br><br>"
                f"<i>Equip stronger gear to unlock this chapter!</i></p>"
            )
            lock_lbl.setWordWrap(True)
            layout.addWidget(lock_lbl)
        else:
            # Story content
            content_text = QtWidgets.QTextEdit()
            content_text.setReadOnly(True)
            
            # Format content with markdown-like bold/italic
            formatted = format_story_text(chapter['content'])
            
            content_text.setHtml(formatted)
            content_text.setStyleSheet("background-color: #1a1a2e; color: #eee; padding: 10px;")
            layout.addWidget(content_text)
            
            # Check if this chapter has a pending decision (has_decision is True when decision not yet made)
            if chapter.get('has_decision') and chapter.get('decision'):
                decision = chapter.get('decision', {})
                
                # Decision frame
                decision_frame = QtWidgets.QFrame()
                decision_frame.setStyleSheet(
                    "QFrame { background-color: #2a1a4a; border: 2px solid #9b59b6; "
                    "border-radius: 10px; padding: 15px; }"
                )
                decision_layout = QtWidgets.QVBoxLayout(decision_frame)
                
                # Decision prompt
                prompt_lbl = QtWidgets.QLabel(
                    f"<h3 style='color: #e74c3c;'>⚔️ CRITICAL DECISION ⚔️</h3>"
                    f"<p style='font-size: 13px; color: #fff;'>{decision.get('prompt', 'What will you do?')}</p>"
                )
                prompt_lbl.setWordWrap(True)
                prompt_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                decision_layout.addWidget(prompt_lbl)
                
                # Choice buttons
                choices = decision.get('choices', {})
                btn_layout = QtWidgets.QHBoxLayout()
                
                choice_a = choices.get('A', {})
                choice_b = choices.get('B', {})
                
                btn_a = QtWidgets.QPushButton(f"⚔️ {choice_a.get('label', 'Choice A')}")
                btn_a.setToolTip(choice_a.get('description', ''))
                btn_a.setStyleSheet(
                    "QPushButton { background-color: #c0392b; color: white; font-weight: bold; "
                    "padding: 15px; border-radius: 8px; font-size: 13px; }"
                    "QPushButton:hover { background-color: #e74c3c; }"
                )
                btn_a.setMinimumHeight(60)
                
                btn_b = QtWidgets.QPushButton(f"💡 {choice_b.get('label', 'Choice B')}")
                btn_b.setToolTip(choice_b.get('description', ''))
                btn_b.setStyleSheet(
                    "QPushButton { background-color: #2980b9; color: white; font-weight: bold; "
                    "padding: 15px; border-radius: 8px; font-size: 13px; }"
                    "QPushButton:hover { background-color: #3498db; }"
                )
                btn_b.setMinimumHeight(60)
                
                def make_choice(choice: str, choice_data: dict):
                    # Make the decision
                    make_story_decision(self.blocker.adhd_buster, chapter_num, choice)
                    self.blocker.save_config()
                    dialog.accept()
                    
                    # Get the updated chapter content with the continuation
                    updated_chapter = get_chapter_content(chapter_num, self.blocker.adhd_buster)
                    
                    # Show continuation dialog with the story result
                    continuation_dialog = QtWidgets.QDialog(self)
                    continuation_dialog.setWindowTitle(f"⚡ {choice_data.get('label', 'Your Choice')}")
                    continuation_dialog.resize(650, 550)
                    cont_layout = QtWidgets.QVBoxLayout(continuation_dialog)
                    
                    # Header showing the choice made
                    choice_lbl = QtWidgets.QLabel(
                        f"<h2 style='text-align: center; color: #f39c12;'>⚡ The Die is Cast! ⚡</h2>"
                        f"<p style='text-align: center; font-size: 14px;'>"
                        f"You chose: <b>{choice_data.get('label', 'Unknown')}</b></p>"
                    )
                    choice_lbl.setWordWrap(True)
                    choice_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    cont_layout.addWidget(choice_lbl)
                    
                    # Story continuation content
                    content_text = QtWidgets.QTextEdit()
                    content_text.setReadOnly(True)
                    
                    # Format the full updated content
                    formatted = format_story_text(updated_chapter['content'])
                    
                    content_text.setHtml(formatted)
                    content_text.setStyleSheet("background-color: #1a1a2e; color: #eee; padding: 10px;")
                    cont_layout.addWidget(content_text)
                    
                    # Continue button
                    ok_btn = QtWidgets.QPushButton("Continue My Journey")
                    ok_btn.clicked.connect(continuation_dialog.accept)
                    cont_layout.addWidget(ok_btn)
                    
                    continuation_dialog.exec()
                    
                    # Comprehensive refresh after story decision
                    self.refresh_all()
                
                btn_a.clicked.connect(lambda: make_choice("A", choice_a))
                btn_b.clicked.connect(lambda: make_choice("B", choice_b))
                
                btn_layout.addWidget(btn_a)
                btn_layout.addWidget(btn_b)
                decision_layout.addLayout(btn_layout)
                
                # Warning label
                warning_lbl = QtWidgets.QLabel(
                    "<p style='color: #e74c3c; font-size: 11px; text-align: center;'>"
                    "⚠️ <b>Warning:</b> This choice is permanent and will affect your story!</p>"
                )
                warning_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                decision_layout.addWidget(warning_lbl)
                
                layout.addWidget(decision_frame)
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def _refresh_story_chapter_list(self) -> None:
        """Refresh the story chapter dropdown to reflect decisions made."""
        if not GAMIFICATION_AVAILABLE:
            return
        
        from gamification import get_story_progress
        progress = get_story_progress(self.blocker.adhd_buster)
        
        self.chapter_combo.clear()
        for ch in progress["chapters"]:
            emoji = "✅" if ch["unlocked"] else "🔒"
            decision_marker = ""
            if ch.get("has_decision"):
                if ch.get("decision_made"):
                    decision_marker = " ⚡"  # Decision made
                elif ch.get("unlocked"):
                    decision_marker = " ⚡"  # Decision pending (unlocked)
                else:
                    decision_marker = " ⚡"  # Decision awaits (locked chapter)
            
            self.chapter_combo.addItem(
                f"{emoji} Chapter {ch['number']}: {ch['title']}{decision_marker}",
                ch["number"]
            )

    def _refresh_story_combo(self) -> None:
        """Refresh story combo to show updated lock status."""
        if not GAMIFICATION_AVAILABLE:
            return
        
        from gamification import AVAILABLE_STORIES, get_selected_story
        
        current_story = get_selected_story(self.blocker.adhd_buster)
        unlocked_stories = self.blocker.adhd_buster.get("unlocked_stories", ["underdog"])
        
        self.story_combo.blockSignals(True)
        self.story_combo.clear()
        
        current_idx = 0
        for i, (story_id, story_info) in enumerate(AVAILABLE_STORIES.items()):
            is_locked = story_id not in unlocked_stories
            lock_icon = "🔒 " if is_locked else ""
            self.story_combo.addItem(f"{lock_icon}{story_info['title']}", story_id)
            tooltip = story_info['description']
            if is_locked:
                tooltip += "\n\n🔒 Costs 100 coins to unlock"
            self.story_combo.setItemData(i, tooltip, QtCore.Qt.ToolTipRole)
            if story_id == current_story:
                current_idx = i
        
        self.story_combo.setCurrentIndex(current_idx)
        self.story_combo.blockSignals(False)

    def _open_diary(self) -> None:
        DiaryDialog(self.blocker, self).exec()

    def _optimize_gear(self) -> None:
        """Automatically equip the best gear based on user criteria."""
        if not GAMIFICATION_AVAILABLE:
            show_warning(self, "Optimize Gear", "Gamification module not available!")
            return
        
        # Check if player has enough coins (use centralized costs with entity perk)
        from gamification import COIN_COSTS, get_entity_optimize_gear_cost
        optimize_perk = get_entity_optimize_gear_cost(self.blocker.adhd_buster)
        OPTIMIZE_COST = optimize_perk["cost"]
        current_coins = self.blocker.adhd_buster.get("coins", 0)
        
        # Only check coins if cost > 0
        if OPTIMIZE_COST > 0 and current_coins < OPTIMIZE_COST:
            show_warning(self, "Not Enough Coins", 
                f"Optimize Gear costs {OPTIMIZE_COST} coins.\n\n"
                f"You have: {current_coins} coins\n"
                f"You need: {OPTIMIZE_COST - current_coins} more coins")
            return
        
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        if not inventory and not any(equipped.values()):
            show_info(self, "Optimize Gear", "No gear available to optimize!")
            return

        # Show dialog for optimization criteria
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Optimize Gear Strategy")
        try:
            # Try setting icon if available in resources
            dialog.setWindowIcon(QtGui.QIcon(":/icons/shield.png"))
        except (FileNotFoundError, OSError, Exception):
            pass  # Icon not available, use default
            
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Coin balance display at top
        coin_bar = QtWidgets.QHBoxLayout()
        coin_bar.addStretch()
        coin_bar.addWidget(QtWidgets.QLabel("🪙"))
        coin_label = QtWidgets.QLabel(f"<b style='color: #ffd700;'>{current_coins:,}</b>")
        coin_bar.addWidget(coin_label)
        layout.addLayout(coin_bar)
        
        # Cost info (with entity perk if applicable)
        if optimize_perk["has_perk"]:
            if OPTIMIZE_COST == 0:
                cost_text = f"<span style='color: #00ff88;'>{optimize_perk['description']}</span>"
            else:
                cost_text = f"<span style='color: #ffd700;'>{optimize_perk['description']}</span>"
        else:
            cost_text = f"<span style='color: #aaa;'>Cost: {OPTIMIZE_COST} coins</span>"
        cost_label = QtWidgets.QLabel(cost_text)
        cost_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(cost_label)
        
        layout.addWidget(QtWidgets.QLabel("Select an optimization strategy:", dialog))
        
        # Radio buttons
        btn_group = QtWidgets.QButtonGroup(dialog)
        
        rb_power = QtWidgets.QRadioButton("Maximize Power (Default)", dialog)
        rb_power.setToolTip("Equip items that give the highest total power, considering set bonuses.")
        rb_power.setChecked(True)
        btn_group.addButton(rb_power)
        layout.addWidget(rb_power)
        
        rb_options = QtWidgets.QRadioButton("Maximize Lucky Options", dialog)
        rb_options.setToolTip("Equip items with the best lucky bonuses (Coins, XP, etc). Power is secondary.")
        btn_group.addButton(rb_options)
        layout.addWidget(rb_options)
        
        rb_balanced = QtWidgets.QRadioButton("Balanced (Power + Options)", dialog)
        rb_balanced.setToolTip("Find a balance between raw power and lucky bonuses.")
        btn_group.addButton(rb_balanced)
        layout.addWidget(rb_balanced)
        
        # Options sub-selection (hidden unless Options/Balanced selected)
        options_frame = QtWidgets.QFrame(dialog)
        options_layout = QtWidgets.QHBoxLayout(options_frame)
        options_layout.setContentsMargins(20, 0, 0, 0)
        options_layout.addWidget(QtWidgets.QLabel("Target:", options_frame))
        
        combo_target = NoScrollComboBox(options_frame)
        combo_target.addItems([
            "All Lucky Options 🍀",
            "Coin Discount 💰",
            "XP Bonus ✨",
            "Merge Luck ⚒️"
        ])
        options_layout.addWidget(combo_target)
        layout.addWidget(options_frame)
        options_frame.setVisible(False)
        
        def update_options_visibility():
            options_frame.setVisible(rb_options.isChecked() or rb_balanced.isChecked())
            
        rb_power.toggled.connect(update_options_visibility)
        rb_options.toggled.connect(update_options_visibility)
        rb_balanced.toggled.connect(update_options_visibility)
        
        # Dialog buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            parent=dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return
            
        # Determine mode and target
        mode = "power"
        if rb_options.isChecked():
            mode = "options"
        elif rb_balanced.isChecked():
            mode = "balanced"
            
        target_map = {
            0: "all",
            1: "coin_discount",
            2: "xp_bonus",
            3: "merge_luck"
        }
        target_opt = target_map.get(combo_target.currentIndex(), "all")
        
        # Calculate optimal gear
        result = optimize_equipped_gear(
            self.blocker.adhd_buster, 
            mode=mode, 
            target_opt=target_opt
        )
        
        if not result["changes"]:
            show_info(
                self, "Optimize Gear",
                "Your gear is already optimized for this strategy! ⚔️\n\n"
                f"Current power: {result['old_power']}"
            )
            return
        
        # Show preview of changes
        changes_text = "\n".join(f"  • {c}" for c in result["changes"]) if result["changes"] else "  No changes needed"
        
        # Calculate lucky bonuses difference
        lucky_summary = ""
        if calculate_total_lucky_bonuses:  # BUG FIX #36: Check function exists
            try:
                old_bonuses = calculate_total_lucky_bonuses(equipped)
                new_bonuses = calculate_total_lucky_bonuses(result["new_equipped"])
                
                bonus_changes = []
                for bonus_type in ["coin_discount", "xp_bonus", "merge_luck"]:
                    old_val = old_bonuses.get(bonus_type, 0)
                    new_val = new_bonuses.get(bonus_type, 0)
                    if old_val != new_val:
                        diff = new_val - old_val
                        sign = "+" if diff > 0 else ""
                        names = {"coin_discount": "Merge Discount", "xp_bonus": "XP", "merge_luck": "Merge Success"}
                        bonus_changes.append(f"{names[bonus_type]}: {old_val}% → {new_val}% ({sign}{diff}%)")
                
                if bonus_changes:
                    lucky_summary = "\n\nBonuses Changes:\n" + "\n".join(f"  • {c}" for c in bonus_changes)
            except Exception:
                # Silently ignore if calculation fails
                pass

        # BUG FIX #28: Show appropriate strategy description
        strategy_desc = mode.title()
        if mode != "power" and target_opt != "all":
            strategy_desc += f" ({target_opt.replace('_', ' ').title()})"
        elif mode != "power":
            strategy_desc += " (All Bonuses)"
        
        # Show cost based on entity perk (Robo Rat = FREE)
        if OPTIMIZE_COST == 0:
            cost_str = "🤖 FREE (Robo Rat)"
        elif OPTIMIZE_COST == 1:
            cost_str = "🐀 1 coin (Hobo Rat)"
        else:
            cost_str = f"💰 {OPTIMIZE_COST} coins"
            
        msg = (
            f"Found a better gear configuration!\n"
            f"Strategy: {strategy_desc}\n\n"
            f"Power Gain: {result['power_gain']:+d} ({result['old_power']} → {result['new_power']})\n\n"
            f"Changes:\n{changes_text}"
            f"{lucky_summary}\n\n"
            f"{cost_str}\n\n"
            "Do you want to equip this gear?"
        )
        
        reply = show_question(
            self, "Optimize Gear", msg,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            # Spend coins for optimization (use same cost from earlier check)
            # Skip spending if cost is 0 (Robo Rat perk)
            if OPTIMIZE_COST > 0:
                if self._game_state:
                    if not self._game_state.spend_coins(OPTIMIZE_COST):
                        show_warning(self, "Error", "Failed to spend coins for optimization.")
                        return
                else:
                    # Fallback: directly deduct coins if no game state manager
                    current_coins = self.blocker.adhd_buster.get("coins", 0)
                    if current_coins < OPTIMIZE_COST:
                        show_warning(self, "Error", "Not enough coins for optimization.")
                        return
                    self.blocker.adhd_buster["coins"] = current_coins - OPTIMIZE_COST
            
            # Apply changes via GameStateManager for proper deep copying and signals
            if self._game_state:
                self._game_state.set_all_equipped(result["new_equipped"])
                # Sync to hero
                if GAMIFICATION_AVAILABLE:
                    sync_hero_data(self.blocker.adhd_buster)
            else:
                # Fallback: directly update equipped if no game state manager
                self.blocker.adhd_buster["equipped"] = result["new_equipped"]
                self.blocker.save_config()
                if GAMIFICATION_AVAILABLE:
                    sync_hero_data(self.blocker.adhd_buster)
            
            # Show result message
            if result["power_gain"] > 0:
                show_info(
                    self, "Gear Optimized! ⚡",
                    f"Power increased from {result['old_power']} to {result['new_power']}!\n"
                    f"(+{result['power_gain']} power)"
                )
            else:
                show_info(
                    self, "Gear Updated! ⚔️",
                    f"Gear configuration updated.\nPower: {result['new_power']}"
                )
            
            # Play sound if available
            if hasattr(self, "_play_sound"):
                self._play_sound("equip")
                
            self.refresh_all()

    def _sell_items(self) -> None:
        """Open the sell items dialog."""
        if not self._game_state:
            show_warning(self, "Error", "Game State Manager not initialized. Cannot sell items.")
            return
        
        dialog = SellItemsDialog(self.blocker, self._game_state, self)
        dialog.exec()



class SellItemsDialog(QtWidgets.QDialog):
    """Dialog for selling items by tier or by selection."""

    def __init__(self, blocker: BlockerCore, game_state, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.game_state = game_state
        self.setWindowTitle("💰 Sell Items")
        self.resize(500, 400)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        title = QtWidgets.QLabel("💰 Sell Items for Coins")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        # Tier selection buttons
        tier_group = QtWidgets.QGroupBox("Sell by Tier")
        tier_layout = QtWidgets.QVBoxLayout(tier_group)
        tier_layout.setSpacing(5)

        rarities = [
            ("Common", "#808080"),
            ("Uncommon", "#4caf50"),
            ("Rare", "#2196f3"),
            ("Epic", "#9c27b0"),
            ("Legendary", "#ff9800")
        ]

        for rarity, color in rarities:
            btn = QtWidgets.QPushButton(f"Sell All {rarity} Items")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    font-weight: bold;
                    padding: 8px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {self._darken_color(color)};
                }}
            """)
            btn.clicked.connect(lambda checked=False, r=rarity: self._sell_by_tier(r))
            tier_layout.addWidget(btn)

        layout.addWidget(tier_group)

        # Selection mode button
        select_btn = QtWidgets.QPushButton("📋 Select Specific Items to Sell")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #607d8b;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #455a64;
            }
        """)
        select_btn.clicked.connect(self._sell_by_selection)
        layout.addWidget(select_btn)

        # 🪑 Entity Perk Card (Office Chair sell bonus)
        self._add_sell_perk_display(layout)

        # Info label
        info_label = QtWidgets.QLabel("💡 Earn 1 coin per item + all % from lucky options")
        info_label.setStyleSheet("color: #666; font-style: italic; font-size: 10px;")
        info_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(info_label)

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _darken_color(self, hex_color: str) -> str:
        """Darken a hex color by 20% for hover effects."""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) < 6:
                return "#666666"  # Fallback for invalid color
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            r, g, b = max(0, int(r * 0.8)), max(0, int(g * 0.8)), max(0, int(b * 0.8))
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return "#666666"  # Fallback for invalid color

    def _add_sell_perk_display(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Add entity perk display card for sell bonuses (Office Chair) - matches ADHD Buster patron style."""
        try:
            from gamification import get_entity_sell_perks
            sell_perks = get_entity_sell_perks(self.blocker.adhd_buster)
            
            if not sell_perks.get("has_perk"):
                return  # No perk to display
            
            is_exceptional = sell_perks.get("is_exceptional", False)
            
            # Create perk card frame - dark gradient style matching ADHD Buster patron cards
            perk_card = QtWidgets.QFrame()
            if is_exceptional:
                # Purple exceptional variant
                perk_card.setStyleSheet("""
                    QFrame {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #3d2e4a, stop:1 #251a2f);
                        border: 2px solid #9c27b0;
                        border-radius: 8px;
                        padding: 6px;
                    }
                """)
                text_color = "#ce93d8"
            else:
                # Orange normal variant
                perk_card.setStyleSheet("""
                    QFrame {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #4a3d2e, stop:1 #2f251a);
                        border: 2px solid #ff9800;
                        border-radius: 8px;
                        padding: 6px;
                    }
                """)
                text_color = "#ffcc80"
            
            card_layout = QtWidgets.QHBoxLayout(perk_card)
            card_layout.setContentsMargins(8, 4, 8, 4)
            card_layout.setSpacing(10)
            
            # SVG Icon
            svg_label = QtWidgets.QLabel()
            svg_label.setFixedSize(40, 40)
            svg_label.setStyleSheet("background: transparent;")
            icon_path = sell_perks.get("icon_path", "")
            if icon_path and os.path.exists(icon_path):
                try:
                    from PySide6.QtSvg import QSvgRenderer
                    from PySide6.QtGui import QPixmap, QPainter
                    renderer = QSvgRenderer(icon_path)
                    if renderer.isValid():
                        pixmap = QPixmap(40, 40)
                        pixmap.fill(QtCore.Qt.transparent)
                        painter = QPainter(pixmap)
                        renderer.render(painter)
                        painter.end()
                        svg_label.setPixmap(pixmap)
                except Exception:
                    svg_label.setText("🪑")
                    svg_label.setStyleSheet("font-size: 24px; background: transparent;")
            else:
                svg_label.setText("🪑")
                svg_label.setStyleSheet("font-size: 24px; background: transparent;")
            card_layout.addWidget(svg_label)
            
            # Perk description
            desc_label = QtWidgets.QLabel(sell_perks.get("description", ""))
            desc_label.setStyleSheet(f"""
                font-size: 12px;
                font-weight: bold;
                color: {text_color};
                background: transparent;
            """)
            desc_label.setWordWrap(True)
            card_layout.addWidget(desc_label, 1)
            
            layout.addWidget(perk_card)
            
        except Exception as e:
            print(f"[SellItemsDialog] Error adding perk display: {e}")

    def _calculate_coin_value(self, item: dict, sell_perks: dict = None) -> int:
        """Calculate coin value: 1 base + sum of all % bonuses in lucky options + entity bonuses.
        
        Args:
            item: The item dict to calculate value for
            sell_perks: Pre-fetched sell perks dict (optional, for efficiency)
        """
        coins = 1
        # Add all % values from lucky options
        lucky_options = item.get("lucky_options", {})
        coins += lucky_options.get("coin_discount", 0)
        coins += lucky_options.get("xp_bonus", 0)
        coins += lucky_options.get("merge_luck", 0)
        
        # ✨ ENTITY PERK BONUS: Add salvage bonus from collected entities
        try:
            from gamification import get_entity_coin_perks
            coin_perks = get_entity_coin_perks(self.blocker.adhd_buster, source="salvage")
            salvage_bonus = coin_perks.get("salvage_bonus", 0)
            coins += salvage_bonus
        except Exception:
            pass  # Silently ignore if perks unavailable
        
        # 🪑 OFFICE CHAIR PERK: Apply rarity multiplier for Epic/Legendary items
        try:
            # Use pre-fetched perks if available (more efficient)
            if sell_perks is None:
                from gamification import get_entity_sell_perks
                sell_perks = get_entity_sell_perks(self.blocker.adhd_buster)
            
            if sell_perks.get("has_perk"):
                item_rarity = item.get("rarity", "Common")
                if item_rarity == "Epic" and sell_perks.get("epic_bonus", 1.0) > 1.0:
                    # Apply 25% bonus - minimum +1 coin for qualifying items
                    bonus_coins = max(1, int(coins * (sell_perks.get("epic_bonus", 1.0) - 1.0) + 0.5))
                    coins += bonus_coins
                elif item_rarity == "Legendary" and sell_perks.get("legendary_bonus", 1.0) > 1.0:
                    # Apply 25% bonus - minimum +1 coin for qualifying items
                    bonus_coins = max(1, int(coins * (sell_perks.get("legendary_bonus", 1.0) - 1.0) + 0.5))
                    coins += bonus_coins
        except Exception:
            pass  # Silently ignore if perks unavailable
        
        return coins

    def _sell_by_tier(self, rarity: str) -> None:
        """Sell all items of a specific rarity."""
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        if not inventory:
            show_info(self, "Sell Items", "No items to sell!")
            return

        # Get equipped item timestamps
        equipped_ts = {item.get("obtained_at") for item in equipped.values() if item}

        # Find items of this rarity that are not equipped
        to_sell = [
            item for item in inventory
            if item.get("rarity") == rarity and item.get("obtained_at") not in equipped_ts
        ]

        if not to_sell:
            show_info(self, "Sell Items", f"No {rarity} items to sell!")
            return

        # Cache sell perks for efficiency
        try:
            from gamification import get_entity_sell_perks
            sell_perks = get_entity_sell_perks(self.blocker.adhd_buster)
        except Exception:
            sell_perks = None

        # Calculate total coins
        total_coins = sum(self._calculate_coin_value(item, sell_perks) for item in to_sell)

        # Confirm
        if show_question(
            self, f"Sell {rarity} Items",
            f"Sell {len(to_sell)} {rarity} items for {total_coins} coins?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        ) != QtWidgets.QMessageBox.Yes:
            return

        # Sell items
        self.game_state.bulk_remove_items(to_sell)
        new_coins = self.game_state.add_coins(total_coins)
        
        # Sync to hero data
        if GAMIFICATION_AVAILABLE:
            sync_hero_data(self.blocker.adhd_buster)

        show_info(self, "Sold!", f"✨ Sold {len(to_sell)} items!\n💰 Coins earned: +{total_coins} (Total: {new_coins})")
        
        # Refresh parent UI
        if self.parent():
            self.parent().refresh_all()

    def _sell_by_selection(self) -> None:
        """Open a selection dialog to choose specific items to sell."""
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        if not inventory:
            show_info(self, "Sell Items", "No items to sell!")
            return

        # Get equipped item timestamps
        equipped_ts = {item.get("obtained_at") for item in equipped.values() if item}

        # Filter out equipped items
        sellable_items = [item for item in inventory if item.get("obtained_at") not in equipped_ts]

        if not sellable_items:
            show_info(self, "Sell Items", "No sellable items (all are equipped)!")
            return

        # Create selection dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Select Items to Sell")
        dialog.resize(600, 500)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Instructions
        info = QtWidgets.QLabel("Select items to sell. Equipped items cannot be sold.")
        info.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(info)

        # Scroll area for items
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)

        # Cache sell perks for efficiency
        try:
            from gamification import get_entity_sell_perks
            sell_perks = get_entity_sell_perks(self.blocker.adhd_buster)
        except Exception:
            sell_perks = None

        checkboxes = []
        for item in sellable_items:
            cb = QtWidgets.QCheckBox()
            rarity_color = item.get("color", "#999")
            name = item.get("name", "Unknown")
            power = item.get("power", 10)
            slot = item.get("slot", "Unknown")
            rarity = item.get("rarity", "Common")
            coin_value = self._calculate_coin_value(item, sell_perks)
            
            cb.setText(f"{name} [{rarity} {slot}] +{power} Power → {coin_value} coins")
            cb.setStyleSheet(f"color: {rarity_color}; font-weight: bold;")
            cb.item_data = item
            checkboxes.append(cb)
            scroll_layout.addWidget(cb)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Coin preview
        coin_preview = QtWidgets.QLabel("Selected: 0 items → 0 coins")
        coin_preview.setStyleSheet("font-weight: bold; color: #ff9800; font-size: 12px;")
        layout.addWidget(coin_preview)

        def update_preview():
            selected = [cb for cb in checkboxes if cb.isChecked()]
            total_coins = sum(self._calculate_coin_value(cb.item_data, sell_perks) for cb in selected)
            coin_preview.setText(f"Selected: {len(selected)} items → {total_coins} coins")

        for cb in checkboxes:
            cb.stateChanged.connect(update_preview)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        select_all_btn = QtWidgets.QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in checkboxes])
        btn_layout.addWidget(select_all_btn)

        deselect_all_btn = QtWidgets.QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in checkboxes])
        btn_layout.addWidget(deselect_all_btn)

        btn_layout.addStretch()

        sell_btn = QtWidgets.QPushButton("Sell Selected")
        sell_btn.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; padding: 8px;")
        sell_btn.clicked.connect(lambda: self._confirm_sell_selected([cb.item_data for cb in checkboxes if cb.isChecked()], dialog))
        btn_layout.addWidget(sell_btn)

        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        dialog.exec()

    def _confirm_sell_selected(self, items: list, dialog: QtWidgets.QDialog) -> None:
        """Confirm and sell selected items."""
        if not items:
            show_info(self, "Sell Items", "No items selected!")
            return

        # Cache sell perks for efficiency
        try:
            from gamification import get_entity_sell_perks
            sell_perks = get_entity_sell_perks(self.blocker.adhd_buster)
        except Exception:
            sell_perks = None

        total_coins = sum(self._calculate_coin_value(item, sell_perks) for item in items)

        if show_question(
            self, "Sell Items",
            f"Sell {len(items)} selected items for {total_coins} coins?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        ) != QtWidgets.QMessageBox.Yes:
            return

        # Sell items
        self.game_state.bulk_remove_items(items)
        new_coins = self.game_state.add_coins(total_coins)
        
        # Sync to hero data
        if GAMIFICATION_AVAILABLE:
            sync_hero_data(self.blocker.adhd_buster)

        show_info(self, "Sold!", f"✨ Sold {len(items)} items!\n💰 Coins earned: +{total_coins} (Total: {new_coins})")
        
        # Close selection dialog
        dialog.accept()
        
        # Refresh parent UI
        if self.parent():
            self.parent().refresh_all()


class DiaryDialog(QtWidgets.QDialog):
    """Dialog for viewing the ADHD Buster's adventure diary."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.setWindowTitle("📖 Adventure Diary")
        self.resize(650, 600)
        self._auto_generated_today = False
        self._auto_generate_todays_entry()
        self._build_ui()

    def _auto_generate_todays_entry(self) -> None:
        """Auto-generate today's diary entry if one doesn't exist yet."""
        if not GAMIFICATION_AVAILABLE:
            return
        today = datetime.now().strftime("%Y-%m-%d")
        diary = self.blocker.adhd_buster.get("diary", [])
        today_entries = [e for e in diary if e.get("date") == today]
        if today_entries:
            return  # Already have an entry for today
        
        # Generate today's entry
        power = calculate_character_power(self.blocker.adhd_buster)
        equipped = self.blocker.adhd_buster.get("equipped", {})
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        entry = generate_diary_entry(power, session_minutes=0, equipped_items=equipped,
                                     story_id=active_story)
        entry["story"] = "[Auto] " + entry["story"]
        entry["is_new"] = True  # Mark as new for display
        
        if "diary" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["diary"] = []
        self.blocker.adhd_buster["diary"].append(entry)
        if len(self.blocker.adhd_buster["diary"]) > 100:
            self.blocker.adhd_buster["diary"] = self.blocker.adhd_buster["diary"][-100:]
        
        # Sync changes to active hero before saving
        sync_hero_data(self.blocker.adhd_buster)
        self.blocker.save_config()
        self._auto_generated_today = True

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        power = calculate_character_power(self.blocker.adhd_buster) if GAMIFICATION_AVAILABLE else 0
        tier = get_diary_power_tier(power) if GAMIFICATION_AVAILABLE else "pathetic"

        header = QtWidgets.QHBoxLayout()
        header.addWidget(QtWidgets.QLabel("<b style='font-size:16px;'>📖 The Adventures of ADHD Buster</b>"))
        header.addStretch()
        tier_lbl = QtWidgets.QLabel(f"⚔ Power: {power} ({tier.capitalize()} Tier)")
        tier_lbl.setStyleSheet("font-weight: bold; color: #ff9800;")
        header.addWidget(tier_lbl)
        layout.addLayout(header)

        entries = self.blocker.adhd_buster.get("diary", [])
        if entries:
            stats_lbl = QtWidgets.QLabel(f"📚 {len(entries)} adventures | 🗓️ Latest: {entries[-1].get('short_date', 'Unknown')}")
            stats_lbl.setStyleSheet("color: gray;")
            layout.addWidget(stats_lbl)

        self.diary_text = QtWidgets.QTextEdit()
        self.diary_text.setReadOnly(True)
        new_entries_cleared = False
        if entries:
            for entry in reversed(entries):
                date = entry.get("short_date", entry.get("date", "Unknown"))
                story = entry.get("story", "...")
                pwr = entry.get("power_at_time", 0)
                mins = entry.get("session_minutes", 0)
                tr = entry.get("tier", "pathetic")
                # Show NEW badge for new entries
                new_badge = ""
                if entry.get("is_new"):
                    new_badge = "<span style='background-color:#4CAF50;color:white;padding:2px 6px;border-radius:3px;font-size:11px;margin-left:8px;'>✨ NEW</span>"
                    entry["is_new"] = False  # Clear the new flag after display
                    new_entries_cleared = True
                self.diary_text.append(f"<b style='color:#1976d2;'>{date}</b>{new_badge}<br>{story}<br>"
                                       f"<span style='color:#888;'>Power: {pwr} | Focus: {mins} min | Tier: {tr.capitalize()}</span><br><hr>")
        else:
            self.diary_text.setPlainText("📭 No adventures recorded yet!\n\nComplete focus sessions to record your epic adventures.")
        layout.addWidget(self.diary_text)
        
        # Save if we cleared new flags
        if new_entries_cleared:
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()

        btn_layout = QtWidgets.QHBoxLayout()
        if entries:
            clear_btn = QtWidgets.QPushButton("🗑️ Clear All")
            clear_btn.clicked.connect(self._clear_diary)
            btn_layout.addWidget(clear_btn)
        write_btn = QtWidgets.QPushButton("✍️ Write Today's Entry")
        write_btn.clicked.connect(self._write_entry)
        btn_layout.addWidget(write_btn)
        btn_layout.addStretch()
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _clear_diary(self) -> None:
        if show_question(self, "Clear Diary", "Clear all diary entries?") == QtWidgets.QMessageBox.Yes:
            self.blocker.adhd_buster["diary"] = []
            # Sync changes to active hero before saving
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()
            self.accept()

    def _write_entry(self) -> None:
        if not GAMIFICATION_AVAILABLE:
            show_warning(self, "Diary", "Gamification not available")
            return
        today = datetime.now().strftime("%Y-%m-%d")
        diary = self.blocker.adhd_buster.get("diary", [])
        bonus_today = [e for e in diary if e.get("date") == today and e.get("story", "").startswith("[Bonus Entry]")]
        if bonus_today:
            show_info(self, "Diary", "You already wrote a bonus entry today!")
            return
        power = calculate_character_power(self.blocker.adhd_buster)
        equipped = self.blocker.adhd_buster.get("equipped", {})
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        entry = generate_diary_entry(power, session_minutes=0, equipped_items=equipped,
                                     story_id=active_story)
        entry["story"] = "[Bonus Entry] " + entry["story"]
        if "diary" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["diary"] = []
        self.blocker.adhd_buster["diary"].append(entry)
        if len(self.blocker.adhd_buster["diary"]) > 100:
            self.blocker.adhd_buster["diary"] = self.blocker.adhd_buster["diary"][-100:]
        # Sync changes to active hero before saving
        if GAMIFICATION_AVAILABLE:
            sync_hero_data(self.blocker.adhd_buster)
        self.blocker.save_config()
        self.accept()


class LevelUpCelebrationDialog(QtWidgets.QDialog):
    """Exciting celebration dialog shown when the player levels up."""

    def __init__(self, level_info: dict, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.level_info = level_info
        self.new_level = level_info.get("level", 1)
        self.levels_gained = level_info.get("levels_gained", 1)
        self.new_title = level_info.get("new_title", "")
        self.title_changed = level_info.get("title_changed", False)
        self.xp_earned = level_info.get("xp_earned", 0)
        self.setWindowTitle("⬆️ LEVEL UP!")
        self.setFixedSize(450, 380)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self._animation_step = 0
        self._particles = []
        self._build_ui()
        self._start_celebration()
        # Dialog now stays open until the user dismisses it

    def _build_ui(self) -> None:
        # Gradient background based on level milestone
        if self.new_level >= 50:
            bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffd700, stop:1 #ff8c00)"
            accent = "#ffd700"
        elif self.new_level >= 30:
            bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #9c27b0, stop:1 #e91e63)"
            accent = "#e040fb"
        elif self.new_level >= 20:
            bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2196f3, stop:1 #00bcd4)"
            accent = "#03a9f4"
        elif self.new_level >= 10:
            bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4caf50, stop:1 #8bc34a)"
            accent = "#66bb6a"
        else:
            bg = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3f51b5, stop:1 #7986cb)"
            accent = "#7c4dff"
        
        self.setStyleSheet(f"background: {bg};")
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # Big celebratory header
        if self.levels_gained > 1:
            header_text = f"🎉 MULTI LEVEL UP! 🎉"
        else:
            header_text = "🎉 LEVEL UP! 🎉"
        self.header_lbl = QtWidgets.QLabel(header_text)
        self.header_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.header_lbl.setStyleSheet(
            f"font-size: 28px; font-weight: bold; color: white; "
            f"text-shadow: 2px 2px 4px rgba(0,0,0,0.5);"
        )
        layout.addWidget(self.header_lbl)
        
        # Level number with animated feel
        level_text = f"Level {self.new_level}"
        if self.levels_gained > 1:
            old_level = self.new_level - self.levels_gained
            level_text = f"Level {old_level} → {self.new_level}"
        self.level_lbl = QtWidgets.QLabel(level_text)
        self.level_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.level_lbl.setStyleSheet(
            "font-size: 48px; font-weight: bold; color: white; "
            "text-shadow: 3px 3px 6px rgba(0,0,0,0.4);"
        )
        layout.addWidget(self.level_lbl)
        
        # Title display
        if self.new_title:
            title_prefix = "NEW TITLE: " if self.title_changed else ""
            self.title_lbl = QtWidgets.QLabel(f"{title_prefix}{self.new_title}")
            self.title_lbl.setAlignment(QtCore.Qt.AlignCenter)
            style = "font-size: 20px; font-weight: bold; color: #fff8e1;"
            if self.title_changed:
                style += " text-shadow: 0 0 10px #ffd700, 0 0 20px #ffd700;"
            self.title_lbl.setStyleSheet(style)
            layout.addWidget(self.title_lbl)
        
        # XP earned info
        if self.xp_earned > 0:
            xp_lbl = QtWidgets.QLabel(f"+{self.xp_earned:,} XP")
            xp_lbl.setAlignment(QtCore.Qt.AlignCenter)
            xp_lbl.setStyleSheet("font-size: 18px; color: #e1f5fe;")
            layout.addWidget(xp_lbl)
        
        # Progress to next level
        progress = self.level_info.get("progress", 0)
        xp_in = self.level_info.get("xp_in_level", 0)
        xp_needed = self.level_info.get("xp_needed", 100)
        
        progress_frame = QtWidgets.QFrame()
        progress_frame.setStyleSheet("background: rgba(255,255,255,0.2); border-radius: 10px;")
        progress_layout = QtWidgets.QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(15, 10, 15, 10)
        
        next_lbl = QtWidgets.QLabel(f"Progress to Level {self.new_level + 1}")
        next_lbl.setStyleSheet("color: white; font-size: 12px;")
        next_lbl.setAlignment(QtCore.Qt.AlignCenter)
        progress_layout.addWidget(next_lbl)
        
        progress_bar = QtWidgets.QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setValue(int(progress))
        progress_bar.setTextVisible(False)
        progress_bar.setFixedHeight(20)
        progress_bar.setStyleSheet(
            f"QProgressBar {{ background: rgba(0,0,0,0.3); border-radius: 10px; }}"
            f"QProgressBar::chunk {{ background: {accent}; border-radius: 10px; }}"
        )
        progress_layout.addWidget(progress_bar)
        
        xp_text = QtWidgets.QLabel(f"{xp_in:,} / {xp_needed:,} XP")
        xp_text.setStyleSheet("color: white; font-size: 11px;")
        xp_text.setAlignment(QtCore.Qt.AlignCenter)
        progress_layout.addWidget(xp_text)
        
        layout.addWidget(progress_frame)
        
        # Motivational message
        messages = [
            "Your focus powers grow stronger! 💪",
            "The path to mastery continues! 🌟",
            "You're becoming unstoppable! 🚀",
            "Champions are made through dedication! 🏆",
            "Every level brings new strength! ⚡",
        ]
        if self.new_level >= 50:
            messages = ["LEGENDARY STATUS! You're a focus god! 👑", "The legends speak of your discipline! ⚡"]
        elif self.new_level >= 30:
            messages = ["Master level focus achieved! 🔮", "Your willpower is legendary! ✨"]
        
        msg_lbl = QtWidgets.QLabel(random.choice(messages))
        msg_lbl.setAlignment(QtCore.Qt.AlignCenter)
        msg_lbl.setStyleSheet("font-size: 14px; color: white; font-style: italic;")
        layout.addWidget(msg_lbl)
        
        # Click to dismiss
        dismiss_lbl = QtWidgets.QLabel("(Click anywhere to continue)")
        dismiss_lbl.setAlignment(QtCore.Qt.AlignCenter)
        dismiss_lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 10px;")
        layout.addWidget(dismiss_lbl)

    def _start_celebration(self) -> None:
        """Start the celebration animation."""
        # Pulse animation for header
        self._animation_timer = QtCore.QTimer(self)
        self._animation_timer.timeout.connect(self._animate_step)
        self._animation_timer.start(150)
        
        # Play sound
        try:
            import winsound
            # Multiple beeps for level up excitement
            for _ in range(min(self.levels_gained, 3)):
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

    def _animate_step(self) -> None:
        """Animate the celebration."""
        self._animation_step += 1
        
        # Pulse the header with different emojis
        emojis = ["🎉", "⭐", "🌟", "✨", "🎊", "💫"]
        emoji = emojis[self._animation_step % len(emojis)]
        
        if self.levels_gained > 1:
            self.header_lbl.setText(f"{emoji} MULTI LEVEL UP! {emoji}")
        else:
            self.header_lbl.setText(f"{emoji} LEVEL UP! {emoji}")
        
        # Stop after a while
        if self._animation_step >= 40:
            self._animation_timer.stop()

    def mousePressEvent(self, event) -> None:
        if hasattr(self, '_animation_timer'):
            self._animation_timer.stop()
        self.accept()

    def closeEvent(self, event) -> None:
        if hasattr(self, '_animation_timer'):
            self._animation_timer.stop()
        super().closeEvent(event)


class ItemDropDialog(QtWidgets.QDialog):
    """Dialog shown when an item drops after confirming on-task."""

    def __init__(self, blocker: BlockerCore, item: dict, session_minutes: int = 0,
                 streak_days: int = 0, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.item = item
        self.session_minutes = session_minutes
        self.streak_days = streak_days
        self.coin_earnings_label: Optional[QtWidgets.QLabel] = None
        self.setWindowTitle("🎁 Item Drop!")
        self.setFixedSize(400, 280)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self._build_ui()
        # Dialog stays visible until the user clicks to close it

    def _build_ui(self) -> None:
        # Validate item has required fields
        if not isinstance(self.item, dict):
            self.item = {"name": "Unknown Item", "rarity": "Common", "color": "#999", "slot": "Unknown"}
        
        # Ensure required fields with defaults
        self.item.setdefault("name", "Unknown Item")
        self.item.setdefault("rarity", "Common")
        self.item.setdefault("color", "#999")
        self.item.setdefault("slot", "Unknown")
        
        bg_colors = {"Common": "#f5f5f5", "Uncommon": "#e8f5e9", "Rare": "#e3f2fd", "Epic": "#f3e5f5", "Legendary": "#fff3e0"}
        bg = bg_colors.get(self.item.get("rarity", "Common"), "#f5f5f5")
        self.setStyleSheet(f"background-color: {bg};")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        if self.item.get("lucky_upgrade"):
            header_text = "🍀 LUCKY UPGRADE! 🍀"
        elif self.item.get("rarity") == "Legendary":
            header_text = "⭐ LEGENDARY DROP! ⭐"
        elif self.item.get("rarity") == "Epic":
            header_text = "💎 EPIC DROP! 💎"
        else:
            header_text = "✨ LOOT DROP! ✨"
        header_lbl = QtWidgets.QLabel(header_text)
        header_lbl.setAlignment(QtCore.Qt.AlignCenter)
        header_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        layout.addWidget(header_lbl)

        # Visual card representing the item
        art_pixmap = self._create_item_pixmap()
        if art_pixmap:
            art_lbl = QtWidgets.QLabel()
            art_lbl.setAlignment(QtCore.Qt.AlignCenter)
            art_lbl.setPixmap(art_pixmap)
            layout.addWidget(art_lbl)

        found_lbl = QtWidgets.QLabel("Your ADHD Buster found:")
        found_lbl.setStyleSheet("color: #333;")
        layout.addWidget(found_lbl)
        name_lbl = QtWidgets.QLabel(self.item.get("name", "Unknown Item"))
        name_lbl.setStyleSheet(f"color: {self.item.get('color', '#999')}; font-size: 12px; font-weight: bold;")
        name_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(name_lbl)
        power = self.item.get("power", RARITY_POWER.get(self.item.get("rarity", "Common"), 10))
        # Get themed slot display name
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        slot_display = get_slot_display_name(self.item.get('slot', 'Unknown'), active_story) if get_slot_display_name else self.item.get('slot', 'Unknown')
        info_lbl = QtWidgets.QLabel(f"[{self.item.get('rarity', 'Common')} {slot_display}] +{power} Power")
        info_lbl.setStyleSheet(f"color: {self.item.get('color', '#999')};")
        info_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(info_lbl)
        
        # Display lucky options if item has them
        lucky_options = self.item.get("lucky_options", {})
        if lucky_options and format_lucky_options:
            try:
                lucky_text = format_lucky_options(lucky_options)
                if lucky_text:
                    lucky_lbl = QtWidgets.QLabel(f"✨ {lucky_text}")
                    lucky_lbl.setStyleSheet("color: #8b5cf6; font-weight: bold; font-size: 11px;")
                    lucky_lbl.setAlignment(QtCore.Qt.AlignCenter)
                    layout.addWidget(lucky_lbl)
            except Exception:
                pass  # Silently skip if formatting fails

        if GAMIFICATION_AVAILABLE:
            bonuses = calculate_rarity_bonuses(self.session_minutes, self.streak_days)
            if bonuses["total_bonus"] > 0:
                bonus_parts = []
                if bonuses["session_bonus"] > 0:
                    bonus_parts.append(f"⏱️{self.session_minutes}min")
                if bonuses["streak_bonus"] > 0:
                    bonus_parts.append(f"🔥{self.streak_days}day streak")
                bonus_txt = " + ".join(bonus_parts) + f" = +{bonuses['total_bonus']}% luck!"
                bonus_lbl = QtWidgets.QLabel(bonus_txt)
                bonus_lbl.setStyleSheet("color: #e65100;")
                bonus_lbl.setAlignment(QtCore.Qt.AlignCenter)
                layout.addWidget(bonus_lbl)

        messages = {"Common": ["Every item counts! 💪", "Building your arsenal!"],
                    "Uncommon": ["Nice find! 🌟", "Your focus is paying off!"],
                    "Rare": ["Rare drop! You're on fire! 🔥", "Sweet loot! ⚡"],
                    "Epic": ["EPIC! Your dedication shows! 💜", "Champion tier! 👑"],
                    "Legendary": ["LEGENDARY! You are unstoppable! ⭐", "GODLIKE FOCUS! 🏆"]}
        msg = random.choice(messages.get(self.item.get("rarity", "Common"), messages["Common"]))
        msg_lbl = QtWidgets.QLabel(msg)
        msg_lbl.setStyleSheet("font-weight: bold; color: #555;")
        msg_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(msg_lbl)
        
        # Placeholder for coin earnings (will be set later if available)
        self.coin_earnings_label = QtWidgets.QLabel("")
        self.coin_earnings_label.setStyleSheet("font-weight: bold; color: #f59e0b; font-size: 11px;")
        self.coin_earnings_label.setAlignment(QtCore.Qt.AlignCenter)
        self.coin_earnings_label.setVisible(False)
        layout.addWidget(self.coin_earnings_label)
        
        adventure_lbl = QtWidgets.QLabel("📖 Your adventure awaits...")
        adventure_lbl.setStyleSheet("color: #555;")
        layout.addWidget(adventure_lbl)
        dismiss_lbl = QtWidgets.QLabel("(Click anywhere to dismiss)")
        dismiss_lbl.setStyleSheet("color: #777; font-size: 10px;")
        layout.addWidget(dismiss_lbl)
    
    def set_coin_earnings(self, coins: int, bonus_text: str = "") -> None:
        """Set the coin earnings message to display."""
        if self.coin_earnings_label and coins > 0:
            text = f"💰 +{coins} Coins earned!{bonus_text}"
            self.coin_earnings_label.setText(text)
            self.coin_earnings_label.setVisible(True)

    def mousePressEvent(self, event) -> None:
        self.accept()

    def _create_item_pixmap(self, size: int = 180) -> Optional[QtGui.QPixmap]:
        """Render a stylized pixmap for the awarded item."""
        try:
            color_hex = self.item.get("color", "#9e9e9e")
            base_color = QtGui.QColor(color_hex)
            if not base_color.isValid():
                base_color = QtGui.QColor("#9e9e9e")

            pixmap = QtGui.QPixmap(size, size)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)

            gradient = QtGui.QLinearGradient(0, 0, 0, size)
            gradient.setColorAt(0.0, base_color.lighter(135))
            gradient.setColorAt(1.0, base_color.darker(125))
            painter.setBrush(QtGui.QBrush(gradient))
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 110), 6))

            rect = QtCore.QRectF(8, 8, size - 16, size - 16)
            painter.drawRoundedRect(rect, 26, 26)

            # Determine story emoji for flair
            story_theme = self.item.get("story_theme")
            emoji = "🎁"
            if STORY_GEAR_THEMES and story_theme in STORY_GEAR_THEMES:
                theme_name = STORY_GEAR_THEMES[story_theme].get("theme_name", "").strip()
                if theme_name:
                    emoji = theme_name.split(" ", 1)[0]

            painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff")))
            painter.setFont(QtGui.QFont("Segoe UI Emoji", int(size * 0.38)))
            painter.drawText(rect, QtCore.Qt.AlignCenter, emoji)

            # Draw rarity stars
            rarity = self.item.get("rarity", "Common")
            stars = {
                "Common": 1,
                "Uncommon": 2,
                "Rare": 3,
                "Epic": 4,
                "Legendary": 5,
            }.get(rarity, 1)
            star_rect = QtCore.QRectF(rect.left(), rect.top() + 12, rect.width(), 26)
            painter.setFont(QtGui.QFont("Segoe UI", 12))
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 220)))
            painter.drawText(star_rect, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop, "★" * stars)

            # Slot ribbon at bottom
            slot_name = self.item.get("slot", "")
            if get_slot_display_name and story_theme:
                try:
                    slot_name = get_slot_display_name(slot_name, story_theme) or slot_name
                except Exception:
                    pass
            slot_text = slot_name.upper()
            ribbon_rect = QtCore.QRectF(rect.left() + 12, rect.bottom() - 48, rect.width() - 24, 34)
            painter.setBrush(QtGui.QColor(0, 0, 0, 140))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRoundedRect(ribbon_rect, 12, 12)
            painter.setFont(QtGui.QFont("Segoe UI", 12, QtGui.QFont.Bold))
            painter.setPen(QtGui.QPen(QtGui.QColor("#ffffff")))
            painter.drawText(ribbon_rect, QtCore.Qt.AlignCenter, slot_text)

            painter.end()
            return pixmap
        except Exception:
            return None


class DiaryEntryRevealDialog(QtWidgets.QDialog):
    """Dramatic reveal dialog for the daily diary entry."""

    def __init__(self, blocker: BlockerCore, entry: dict, session_minutes: int = 0,
                 parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.entry = entry
        self.session_minutes = session_minutes
        self.setWindowTitle("📖 Today's Adventure")
        self.setFixedSize(520, 380)
        self._build_ui()
        # Dialog remains until user clicks, no auto-close timer

    def _build_ui(self) -> None:
        tier = self.entry.get("tier", "pathetic")
        tier_styles = {
            "pathetic": {"bg": "#fafafa", "accent": "#9e9e9e", "emoji": "🌱"},
            "modest": {"bg": "#f1f8e9", "accent": "#8bc34a", "emoji": "🛡️"},
            "decent": {"bg": "#e8f5e9", "accent": "#4caf50", "emoji": "💪"},
            "heroic": {"bg": "#e3f2fd", "accent": "#2196f3", "emoji": "🔥"},
            "epic": {"bg": "#f3e5f5", "accent": "#9c27b0", "emoji": "⚡"},
            "legendary": {"bg": "#fff3e0", "accent": "#ff9800", "emoji": "⭐"},
            "godlike": {"bg": "#fffde7", "accent": "#ffc107", "emoji": "🌟"}
        }
        style = tier_styles.get(tier, tier_styles["pathetic"])
        self.setStyleSheet(f"background-color: {style['bg']};")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)

        tier_boosted = self.entry.get("tier_boosted", False)
        if tier_boosted:
            header_text = f"{style['emoji']} Lucky Adventure! {style['emoji']}"
            subheader = f"Your {self.session_minutes}+ min focus earned a bonus tier!"
        else:
            header_text = f"{style['emoji']} Today's Adventure {style['emoji']}"
            subheader = self.entry.get("short_date", "")
        header_lbl = QtWidgets.QLabel(header_text)
        header_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {style['accent']};")
        header_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(header_lbl)
        sub_lbl = QtWidgets.QLabel(subheader)
        sub_lbl.setStyleSheet("color: #666;")
        sub_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(sub_lbl)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet(f"color: {style['accent']};")
        layout.addWidget(line)

        story = self.entry.get("story", "A mysterious adventure occurred...")
        story_lbl = QtWidgets.QLabel(story)
        story_lbl.setWordWrap(True)
        story_lbl.setStyleSheet("font-size: 12px; color: #333;")
        layout.addWidget(story_lbl)

        line2 = QtWidgets.QFrame()
        line2.setFrameShape(QtWidgets.QFrame.HLine)
        line2.setStyleSheet(f"color: {style['accent']};")
        layout.addWidget(line2)

        power = self.entry.get("power_at_time", 0)
        tier_display = tier.capitalize()
        if tier_boosted:
            base_tier = self.entry.get("base_tier", tier)
            power_text = f"⚔ Power: {power}  |  🎭 {base_tier.capitalize()} → {tier_display} (bonus!)"
        else:
            power_text = f"⚔ Power: {power}  |  🎭 {tier_display} Tier"
        pwr_lbl = QtWidgets.QLabel(power_text)
        pwr_lbl.setStyleSheet(f"font-weight: bold; color: {style['accent']};")
        pwr_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(pwr_lbl)
        mins_lbl = QtWidgets.QLabel(f"⏱️ {self.session_minutes} min focus session")
        mins_lbl.setStyleSheet("color: #666;")
        mins_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(mins_lbl)
        dismiss_lbl = QtWidgets.QLabel("(Click anywhere to dismiss)")
        dismiss_lbl.setStyleSheet("color: #777; font-size: 10px;")
        layout.addWidget(dismiss_lbl)

    def mousePressEvent(self, event) -> None:
        self.accept()


# ============================================================================
# Priority Management Dialogs (Qt Implementation)
# ============================================================================

class PriorityTimeLogDialog(QtWidgets.QDialog):
    """Dialog for logging time to priorities after a focus session."""

    def __init__(self, blocker: BlockerCore, session_minutes: int,
                 parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.session_minutes = session_minutes
        self.time_spins: list = []
        self.priority_indices: list = []
        self.setWindowTitle("📊 Log Priority Time")
        self.resize(450, 450)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        header = QtWidgets.QLabel(f"<b>📊 Log Time to Priorities</b><br>"
                                  f"You completed a {self.session_minutes} minute focus session.")
        layout.addWidget(header)

        today = datetime.now().strftime("%A")
        priorities_box = QtWidgets.QGroupBox("Today's Priorities")
        p_layout = QtWidgets.QVBoxLayout(priorities_box)

        has_priorities = False
        for i, priority in enumerate(self.blocker.priorities):
            title = priority.get("title", "").strip()
            days = priority.get("days", [])
            if title and (not days or today in days):
                has_priorities = True
                row = QtWidgets.QHBoxLayout()
                row.addWidget(QtWidgets.QLabel(f"#{i+1}: {title}"))
                spin = QtWidgets.QSpinBox()
                spin.setRange(0, self.session_minutes)
                spin.setValue(0)
                spin.setSuffix(" min")
                row.addWidget(spin)
                p_layout.addLayout(row)
                self.time_spins.append(spin)
                self.priority_indices.append(i)

        if not has_priorities:
            p_layout.addWidget(QtWidgets.QLabel("No active priorities for today."))
        layout.addWidget(priorities_box)

        if has_priorities:
            quick_box = QtWidgets.QGroupBox("Quick Options")
            q_layout = QtWidgets.QHBoxLayout(quick_box)
            all_first_btn = QtWidgets.QPushButton(f"All {self.session_minutes} min to first")
            all_first_btn.clicked.connect(self._log_all_to_first)
            q_layout.addWidget(all_first_btn)
            split_btn = QtWidgets.QPushButton("Split evenly")
            split_btn.clicked.connect(self._split_evenly)
            q_layout.addWidget(split_btn)
            layout.addWidget(quick_box)

        btn_layout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("💾 Save & Close")
        save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(save_btn)
        skip_btn = QtWidgets.QPushButton("Skip")
        skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(skip_btn)
        layout.addLayout(btn_layout)

    def _log_all_to_first(self) -> None:
        if self.time_spins:
            self.time_spins[0].setValue(self.session_minutes)
            for spin in self.time_spins[1:]:
                spin.setValue(0)

    def _split_evenly(self) -> None:
        if self.time_spins and len(self.time_spins) > 0:
            per = self.session_minutes // len(self.time_spins)
            for spin in self.time_spins:
                spin.setValue(per)

    def _save_and_close(self) -> None:
        for spin, idx in zip(self.time_spins, self.priority_indices):
            minutes = spin.value()
            if minutes > 0:
                hours = minutes / 60.0
                cur = self.blocker.priorities[idx].get("logged_hours", 0)
                self.blocker.priorities[idx]["logged_hours"] = cur + hours
        self.blocker.save_config()
        self.accept()


class PriorityCheckinDialog(QtWidgets.QDialog):
    """Dialog shown during a session to ask if user is working on priorities."""

    def __init__(self, blocker: BlockerCore, today_priorities: list, session_minutes: int = 0,
                 parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.today_priorities = today_priorities
        self.session_minutes = session_minutes
        self.result: Optional[bool] = None
        self.setWindowTitle("Priority Check-in ⏰")
        self.resize(420, 380)
        self._build_ui()
        # Dialog stays open until the user chooses an option

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(QtWidgets.QLabel("<b style='font-size:14px;'>🎯 Quick Check-in</b>"))
        layout.addWidget(QtWidgets.QLabel("Are you currently working on your priority tasks?"))

        if GAMIFICATION_AVAILABLE:
            streak = self.blocker.stats.get("streak_days", 0)
            bonuses = calculate_rarity_bonuses(self.session_minutes, streak)
            bonus_parts = []
            if bonuses["session_bonus"] > 0:
                bonus_parts.append(f"⏱️+{bonuses['session_bonus']}%")
            if bonuses["streak_bonus"] > 0:
                bonus_parts.append(f"🔥+{bonuses['streak_bonus']}%")
            if bonus_parts:
                bonus_lbl = QtWidgets.QLabel(f"✨ Loot bonuses: {' '.join(bonus_parts)}")
                bonus_lbl.setStyleSheet("color: #ff9800;")
                layout.addWidget(bonus_lbl)

        p_box = QtWidgets.QGroupBox("Today's Priorities")
        p_layout = QtWidgets.QVBoxLayout(p_box)
        text = "\n".join([f"• {p.get('title', '')}" for p in self.today_priorities])
        p_layout.addWidget(QtWidgets.QLabel(text if text.strip() else "No priorities set"))
        layout.addWidget(p_box)

        btn_layout = QtWidgets.QHBoxLayout()
        yes_btn = QtWidgets.QPushButton("✅ Yes, I'm on task!")
        yes_btn.clicked.connect(self._confirm_on_task)
        btn_layout.addWidget(yes_btn)
        no_btn = QtWidgets.QPushButton("⚠ Need to refocus")
        no_btn.clicked.connect(self._confirm_off_task)
        btn_layout.addWidget(no_btn)
        layout.addLayout(btn_layout)

        dismiss_btn = QtWidgets.QPushButton("Dismiss")
        dismiss_btn.clicked.connect(self.reject)
        layout.addWidget(dismiss_btn)

    def _confirm_on_task(self) -> None:
        self.result = True
        self.accept()

    def _confirm_off_task(self) -> None:
        self.result = False
        show_info(self, "💪 Time to refocus!",
                                           "Take a breath and get back to your priorities.\nYou've got this!")
        self.accept()


class PrioritiesDialog(QtWidgets.QDialog):
    """Dialog for managing daily priorities with day-of-week reminders."""

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def __init__(self, blocker: BlockerCore, on_start_callback=None,
                 parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.on_start_callback = on_start_callback
        self.setWindowTitle("🎯 My Priorities")
        self.resize(550, 620)
        self.priorities = copy.deepcopy(self.blocker.priorities) if self.blocker.priorities else []
        # Mark loaded priorities as existing (locked strategic status)
        for p in self.priorities:
            p["_existing"] = True

        if not self.priorities:
            self.priorities.append(self._empty_priority())
        self.title_edits: List[QtWidgets.QLineEdit] = []
        self.day_checks: List[List[tuple]] = []
        self.planned_spins: List[QtWidgets.QDoubleSpinBox] = []
        self.strategic_checks: List[QtWidgets.QCheckBox] = []
        self.priority_list_layout: Optional[QtWidgets.QVBoxLayout] = None
        self.add_priority_btn: Optional[QtWidgets.QPushButton] = None
        self._build_ui()

    def _empty_priority(self) -> dict:
        """Return a placeholder priority record."""
        return {
            "title": "",
            "days": [],
            "active": False,
            "planned_hours": 0,
            "logged_hours": 0,
            "strategic": False,
        }

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        header = QtWidgets.QHBoxLayout()
        header.addWidget(QtWidgets.QLabel("<b style='font-size:16px;'>🎯 My Priorities</b>"))
        header.addStretch()
        today = datetime.now().strftime("%A, %B %d")
        header.addWidget(QtWidgets.QLabel(today))
        layout.addLayout(header)

        layout.addWidget(QtWidgets.QLabel("Set as many priority tasks as you need. These can span multiple days."))

        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.priority_list_container = QtWidgets.QWidget()
        self.priority_list_layout = QtWidgets.QVBoxLayout(self.priority_list_container)
        self.priority_list_layout.setContentsMargins(0, 0, 0, 0)
        self.priority_list_layout.setSpacing(12)
        self.priority_list_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_area.setWidget(self.priority_list_container)
        layout.addWidget(self.scroll_area)

        self.add_priority_btn = QtWidgets.QPushButton("➕ Add Priority")
        self.add_priority_btn.clicked.connect(self._add_priority)
        layout.addWidget(self.add_priority_btn)

        # Today's Focus
        today_box = QtWidgets.QGroupBox("📌 Today's Focus")
        today_layout = QtWidgets.QVBoxLayout(today_box)
        self.today_lbl = QtWidgets.QLabel()
        today_layout.addWidget(self.today_lbl)
        layout.addWidget(today_box)

        self._rebuild_priority_rows()
        self._refresh_today_focus()

        btn_layout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("💾 Save Priorities")
        save_btn.clicked.connect(self._save_priorities)
        btn_layout.addWidget(save_btn)
        if self.on_start_callback:
            start_btn = QtWidgets.QPushButton("▶ Start Working on Priority")
            start_btn.clicked.connect(self._start_session)
            btn_layout.addWidget(start_btn)
        btn_layout.addStretch()
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        # Settings section
        settings_box = QtWidgets.QGroupBox("⚙️ Settings")
        settings_layout = QtWidgets.QVBoxLayout(settings_box)
        
        # Startup toggle
        self.startup_check = QtWidgets.QCheckBox("Show this dialog when the app starts")
        self.startup_check.setChecked(self.blocker.show_priorities_on_startup)
        self.startup_check.toggled.connect(self._toggle_startup)
        settings_layout.addWidget(self.startup_check)
        
        # Check-in settings
        checkin_layout = QtWidgets.QHBoxLayout()
        self.checkin_enabled = QtWidgets.QCheckBox("Ask if I'm working on priorities every")
        self.checkin_enabled.setChecked(self.blocker.priority_checkin_enabled)
        self.checkin_enabled.toggled.connect(self._toggle_checkin)
        checkin_layout.addWidget(self.checkin_enabled)
        
        self.checkin_interval_spin = QtWidgets.QSpinBox()
        self.checkin_interval_spin.setRange(5, 120)
        self.checkin_interval_spin.setValue(self.blocker.priority_checkin_interval)
        self.checkin_interval_spin.valueChanged.connect(self._update_checkin_interval)
        checkin_layout.addWidget(self.checkin_interval_spin)
        
        checkin_layout.addWidget(QtWidgets.QLabel("minutes during sessions"))
        checkin_layout.addStretch()
        settings_layout.addLayout(checkin_layout)
        
        layout.addWidget(settings_box)

    def _create_priority_row(self, index: int) -> None:
        priority = self.priorities[index]
        group = QtWidgets.QGroupBox(f"Priority #{index + 1}")
        g_layout = QtWidgets.QVBoxLayout(group)

        # Title row with actions
        title_row = QtWidgets.QHBoxLayout()
        title_edit = QtWidgets.QLineEdit(priority.get("title", ""))
        title_edit.setPlaceholderText("Enter priority title...")
        title_row.addWidget(title_edit)

        # Strategic Priority Checkbox (Locked for existing items)
        is_existing = priority.get("_existing", False)
        # Check if any OTHER priority is ALREADY strategic and locked (existing)
        # We look at the data source self.priorities because widgets might not be built yet
        locked_strategic_exists = any(p.get("strategic", False) and p.get("_existing", False) for p in self.priorities)

        strategic_chk = QtWidgets.QCheckBox("Strategic (+50% XP)")
        is_strategic = priority.get("strategic", False)
        strategic_chk.setChecked(is_strategic)

        # Locking Logic:
        # 1. If priority is existing, strategic status is immutable -> Disabled
        # 2. If priority is new, but there is already a locked strategic priority -> Disabled
        if is_existing:
            strategic_chk.setEnabled(False)
            strategic_chk.setToolTip("Strategic status cannot be changed for existing priorities.")
        elif locked_strategic_exists:
            strategic_chk.setEnabled(False)
            strategic_chk.setToolTip("A strategic priority is already active and cannot be superseded.")
        else:
            strategic_chk.setEnabled(True)
            strategic_chk.setToolTip("Sessions focused on this priority grant +50% XP.")
            strategic_chk.toggled.connect(lambda checked, idx=index: self._on_strategic_toggled(idx, checked))

        title_row.addWidget(strategic_chk)
        self.strategic_checks.append(strategic_chk)

        complete_btn = QtWidgets.QPushButton("✅ Complete")
        complete_btn.setToolTip("Mark this priority as complete and roll for a Lucky Gift!")
        complete_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        complete_btn.clicked.connect(lambda checked=False, idx=index: self._complete_priority(idx))
        title_row.addWidget(complete_btn)

        remove_btn = QtWidgets.QPushButton("🗑 Remove")
        remove_btn.setToolTip("Remove this priority entry")
        remove_btn.clicked.connect(lambda checked=False, idx=index: self._remove_priority(idx))
        remove_btn.setEnabled(len(self.priorities) > 1)
        title_row.addWidget(remove_btn)

        g_layout.addLayout(title_row)
        self.title_edits.append(title_edit)

        days_layout = QtWidgets.QHBoxLayout()
        days_layout.addWidget(QtWidgets.QLabel("Days:"))
        day_checks = []
        saved_days = priority.get("days", [])
        for day in self.DAYS:
            cb = QtWidgets.QCheckBox(day[:3])
            cb.setChecked(day in saved_days)
            days_layout.addWidget(cb)
            day_checks.append((day, cb))
        self.day_checks.append(day_checks)
        g_layout.addLayout(days_layout)

        planned_layout = QtWidgets.QHBoxLayout()
        planned_layout.addWidget(QtWidgets.QLabel("Planned hours:"))
        planned_spin = QtWidgets.QDoubleSpinBox()
        planned_spin.setRange(0, 100)
        planned_spin.setValue(priority.get("planned_hours", 0))
        planned_layout.addWidget(planned_spin)

        logged = priority.get("logged_hours", 0)
        planned = priority.get("planned_hours", 0)

        if planned > 0:
            p_bar = QtWidgets.QProgressBar()
            p_bar.setMaximum(100)
            pct = min(100, int((logged / planned) * 100)) if planned else 0
            p_bar.setValue(pct)
            p_bar.setFormat(f"{logged:.1f}/{planned:.1f} hrs ({pct}%)")
            p_bar.setFixedWidth(160)
            planned_layout.addWidget(p_bar)
            if idx < len(self.strategic_checks):
                priority["strategic"] = self.strategic_checks[idx].isChecked()

    def _on_strategic_toggled(self, index: int, checked: bool) -> None:
        """Handle strategic status changes with exclusivity."""
        if not checked:
            return

        # If this one is checked, uncheck all OTHER NEW strategic checkboxes
        for i, chk in enumerate(self.strategic_checks):
            if i != index and chk.isEnabled() and chk.isChecked():
                chk.setChecked(False)

    def _sync_ui_into_priorities(self) -> None:
        """Sync current UI widget values back into self.priorities data."""
        for i in range(len(self.priorities)):
            if i < len(self.title_edits):
                self.priorities[i]["title"] = self.title_edits[i].text().strip()
            if i < len(self.day_checks):
                days = [day for day, cb in self.day_checks[i] if cb.isChecked()]
                self.priorities[i]["days"] = days
            if i < len(self.planned_spins):
                self.priorities[i]["planned_hours"] = self.planned_spins[i].value()
            if i < len(self.strategic_checks):
                self.priorities[i]["strategic"] = self.strategic_checks[i].isChecked()

    def _rebuild_priority_rows(self) -> None:
        """Recreate the priority row widgets to reflect current data."""
        if self.priority_list_layout is None:
            return

        self._sync_ui_into_priorities()

        # Clean up widgets
        while self.priority_list_layout.count():
            item = self.priority_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.title_edits = []
        self.day_checks = []
        self.planned_spins = []
        self.strategic_checks = []

        for i in range(len(self.priorities)):
            self._create_priority_row(i)
        for priority in self.priorities:
            if priority.get("strategic") and not strategic_seen:
                strategic_seen = True
            else:
                priority["strategic"] = False

        if self.strategic_group is not None:
            self.strategic_group.deleteLater()
        self.strategic_group = QtWidgets.QButtonGroup(self)
        self.strategic_group.setExclusive(True)

        while self.priority_list_layout.count():
            item = self.priority_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.title_edits = []
        self.day_checks = []
        self.planned_spins = []

        if not self.priorities:
            self.priorities.append(self._empty_priority())

        for idx in range(len(self.priorities)):
            self._create_priority_row(idx)

    def _add_priority(self) -> None:
        """Append a new blank priority entry."""
        self._sync_ui_into_priorities()
        self.priorities.append(self._empty_priority())
        self._rebuild_priority_rows()
        self._refresh_today_focus()

    def _remove_priority(self, index: int) -> None:
        """Remove a priority by index or clear the final remaining entry."""
        self._sync_ui_into_priorities()
        if index < 0 or index >= len(self.priorities):
            return
        if len(self.priorities) <= 1:
            self.priorities[0] = self._empty_priority()
        else:
            self.priorities.pop(index)
        self._rebuild_priority_rows()
        self._refresh_today_focus()

    def _refresh_today_focus(self) -> None:
        today = datetime.now().strftime("%A")
        today_priorities = []
        for i, p in enumerate(self.priorities):
            title = p.get("title", "").strip()
            days = p.get("days", [])
            if title and (not days or today in days):
                today_priorities.append(f"#{i+1}: {title}")
        if today_priorities:
            self.today_lbl.setText("\n".join(today_priorities))
        else:
            self.today_lbl.setText("No priorities set for today.")

    def _save_priorities(self) -> None:
        self._sync_ui_into_priorities()
        self.blocker.priorities = copy.deepcopy(self.priorities)
        self.blocker.save_config()
        self._rebuild_priority_rows()
        self._refresh_today_focus()
        show_info(self, "Saved", "Priorities saved!")

    def _start_session(self) -> None:
        self._save_priorities()
        
        # Find the first priority for today
        today = datetime.now().strftime("%A")
        target_priority = None
        
        for p in self.priorities:
            if p.get("title", "").strip() and (not p.get("days") or today in p.get("days", [])):
                target_priority = p.get("title")
                break
        
        if target_priority:
            self.accept()
            if self.on_start_callback:
                self.on_start_callback(target_priority)
        else:
            show_warning(self, "No Priority", 
                                  "No priority task found for today!\n"
                                  "Add a task above and ensure today is selected.")

    def _toggle_startup(self, checked: bool) -> None:
        self.blocker.show_priorities_on_startup = checked
        self.blocker.save_config()

    def _toggle_checkin(self, checked: bool) -> None:
        self.blocker.priority_checkin_enabled = checked
        self.blocker.save_config()

    def _update_checkin_interval(self, value: int) -> None:
        if 5 <= value <= 120:
            self.blocker.priority_checkin_interval = value
            self.blocker.save_config()

    def _complete_priority(self, index: int) -> None:
        """Mark a priority as complete and roll for a lucky gift reward."""
        self._sync_ui_into_priorities()
        title = self.title_edits[index].text().strip()
        if not title:
            show_warning(self, "No Priority", 
                "This priority slot is empty. Enter a title first!")
            return
        
        # Get logged hours for this priority
        logged_hours = self.priorities[index].get("logged_hours", 0)
        
        # Calculate chance for display
        if logged_hours >= 20:
            chance = 99
        elif logged_hours > 0:
            chance = min(99, int(15 + (logged_hours / 20) * 84))
        else:
            chance = 15
        
        # Confirm completion
        reply = show_question(
            self, "Complete Priority?",
            f"🎯 Mark '{title}' as COMPLETE?\n\n"
            f"You'll get a chance to win a Lucky Gift!\n"
            f"(🎰 {chance}% chance based on {logged_hours:.1f}h logged)",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        
        # Show animated lottery dialog for priority completion
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        
        from lottery_animation import PriorityLotteryDialog
        lottery = PriorityLotteryDialog(
            win_chance=chance / 100.0,
            priority_title=title,
            logged_hours=logged_hours,
            story_id=active_story,
            parent=self
        )
        lottery.exec()
        
        # Get results from lottery
        won, rarity, item = lottery.get_results()
        
        # Prepare items and coins for batch award
        items_earned = []
        coins_earned = 100  # Base coins for completing a priority
        
        if won and item:
            # Ensure item has all required fields
            if "obtained_at" not in item:
                item["obtained_at"] = datetime.now().isoformat()
            items_earned.append(item)
        
        # Use GameState manager for reactive updates
        main_window = self.window()
        game_state = getattr(main_window, 'game_state', None)
        if not game_state:
            logger.error("GameStateManager not available - cannot award priority completion rewards")
            return
        
        # Use batch award - handles inventory, auto-equip, coins, save, and signals
        game_state.award_items_batch(items_earned, coins=coins_earned, auto_equip=True, source="priority_completion")
        
        # Sync changes to active hero
        if GAMIFICATION_AVAILABLE:
            sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()
        
        # Clear the completed priority
        self.priorities[index] = self._empty_priority()
        
        # Save and refresh
        self.blocker.priorities = copy.deepcopy(self.priorities)
        self.blocker.save_config()
        self._rebuild_priority_rows()
        self._refresh_today_focus()
        
        # Update coin display in main window
        main_window = self.parent()
        while main_window and not isinstance(main_window, QtWidgets.QMainWindow):
            main_window = main_window.parent()
        if main_window and hasattr(main_window, '_update_coin_display'):
            main_window._update_coin_display()


class AISessionCompleteDialog(QtWidgets.QDialog):
    """AI-powered session completion dialog with ratings, notes, and break suggestions."""

    def __init__(self, blocker: BlockerCore, session_duration: int,
                 parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.session_duration = session_duration
        self.selected_rating = ""
        # Don't create LocalAI here - suggest_break_activity doesn't need it
        self.setWindowTitle("Session Complete! 🎉")
        self.resize(500, 520)
        self.setMinimumSize(450, 400)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        # Congratulations header
        header = QtWidgets.QLabel("🎉 Great work!")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(header)

        duration_label = QtWidgets.QLabel(f"You focused for {self.session_duration // 60} minutes")
        duration_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(duration_label)

        # Rating section
        rating_group = QtWidgets.QGroupBox("📝 How was your focus? (optional)")
        rating_layout = QtWidgets.QVBoxLayout(rating_group)

        rating_layout.addWidget(QtWidgets.QLabel("Rate your session:"))

        btn_layout = QtWidgets.QHBoxLayout()
        ratings = [
            ("😫 Struggled", "Struggled to concentrate, many distractions"),
            ("😐 Okay", "Decent session, some distractions"),
            ("😊 Good", "Good session, stayed mostly focused"),
            ("🌟 Excellent", "Amazing session! In the zone!")
        ]
        self.rating_buttons = []
        for emoji, description in ratings:
            btn = QtWidgets.QPushButton(emoji)
            btn.setProperty("rating_desc", description)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, d=description, b=btn: self._select_rating(d, b))
            btn_layout.addWidget(btn)
            self.rating_buttons.append(btn)
        rating_layout.addLayout(btn_layout)

        rating_layout.addWidget(QtWidgets.QLabel("Or write your own notes:"))
        self.notes_edit = QtWidgets.QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("How did the session go?")
        rating_layout.addWidget(self.notes_edit)

        # AI analysis display
        self.analysis_label = QtWidgets.QLabel("")
        self.analysis_label.setStyleSheet("color: #0066cc; font-style: italic;")
        self.analysis_label.setWordWrap(True)
        rating_layout.addWidget(self.analysis_label)

        layout.addWidget(rating_group)

        # Break suggestions
        suggestion_group = QtWidgets.QGroupBox("💡 Suggested Break Activities")
        suggestion_layout = QtWidgets.QVBoxLayout(suggestion_group)
        self.suggestions_label = QtWidgets.QLabel()
        self.suggestions_label.setWordWrap(True)
        suggestion_layout.addWidget(self.suggestions_label)
        layout.addWidget(suggestion_group)

        # Generate suggestions
        self._generate_suggestions()

        # Buttons
        btn_layout2 = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("💾 Save & Continue")
        save_btn.clicked.connect(self._save_and_close)
        btn_layout2.addWidget(save_btn)
        skip_btn = QtWidgets.QPushButton("Skip")
        skip_btn.clicked.connect(self.accept)
        btn_layout2.addWidget(skip_btn)
        layout.addLayout(btn_layout2)

    def _select_rating(self, description: str, clicked_btn: QtWidgets.QPushButton) -> None:
        self.selected_rating = description
        for btn in self.rating_buttons:
            btn.setChecked(btn == clicked_btn)

    def _generate_suggestions(self) -> None:
        """Generate break activity suggestions based on session duration."""
        session_mins = self.session_duration // 60
        
        # Generate suggestions based on session length (same logic as LocalAI.suggest_break_activity)
        if session_mins > 60:  # Long session
            suggestions = [
                "🚶 Take a 10-minute walk to refresh",
                "💧 Drink water and do light stretching",
                "🌳 Step outside for fresh air"
            ]
        elif session_mins > 30:
            suggestions = [
                "☕ Quick coffee/tea break",
                "🧘 5-minute breathing exercises",
                "👀 Look away from screen, rest eyes"
            ]
        else:
            suggestions = [
                "⚡ Brief 2-minute stretch",
                "💪 Do 10 pushups for energy",
                "🎵 Listen to one song"
            ]
        
        text = "\n".join(f"  {i}. {s}" for i, s in enumerate(suggestions, 1))
        self.suggestions_label.setText(text)

    def _save_and_close(self) -> None:
        note = self.notes_edit.toPlainText().strip()
        if not note and self.selected_rating:
            note = self.selected_rating

        if note:
            self._save_session_note(note)

        self.accept()

    def _save_session_note(self, note: str) -> None:
        """Save session note to stats."""
        session_notes = self.blocker.stats.get("session_notes", [])
        session_notes.append({
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": self.session_duration,
            "note": note
        })
        # Keep last 50 notes
        self.blocker.stats["session_notes"] = session_notes[-50:]
        self.blocker.save_stats()


# ============================================================================
# Daily Timeline Widgets
# ============================================================================

class WaterRingWidget(QtWidgets.QWidget):
    """Circular progress bar for daily hydration goal."""
    clicked = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.percentage = 0.0
        self.current = 0
        self.goal = 5
        self.setMinimumSize(60, 60)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    def set_progress(self, current: int, goal: int = 5):
        """Set water progress (glasses consumed / goal)."""
        goal = max(1, goal)  # Avoid division by zero
        self.percentage = min(current / goal, 1.0)
        self.current = current
        self.goal = goal
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        rect = self.rect().adjusted(5, 5, -5, -5)
        
        # Background Track
        pen = QtGui.QPen(QtGui.QColor("#1a3a5c"), 6)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(rect)
        
        # Progress Arc (cyan/blue for water)
        pen.setColor(QtGui.QColor("#4fc3f7"))
        painter.setPen(pen)
        
        start_angle = 90 * 16
        span_angle = -int(self.percentage * 360 * 16)
        painter.drawArc(rect, start_angle, span_angle)
        
        # Main text: glasses count with emoji
        painter.setPen(QtGui.QColor("#ffffff"))
        font = painter.font()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        
        main_rect = QtCore.QRectF(rect)
        painter.drawText(main_rect, QtCore.Qt.AlignmentFlag.AlignCenter, f"💧{self.current}")
        
        # Subtext: "of 8" label
        font.setPixelSize(10)
        font.setBold(False)
        painter.setFont(font)
        sub_rect = QtCore.QRectF(rect.adjusted(0, 20, 0, 0))
        painter.setPen(QtGui.QColor("#4fc3f7"))
        painter.drawText(sub_rect, QtCore.Qt.AlignmentFlag.AlignCenter, f"of {self.goal}")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ChapterRingWidget(QtWidgets.QWidget):
    """Circular progress bar for story chapter progress (power-based)."""
    clicked = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.percentage = 0.0
        self.unlocked = 0
        self.total = 7
        self.is_complete = False
        self.setMinimumSize(60, 60)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    def set_progress(self, unlocked_chapters: int, progress_pct: float, total_chapters: int = 7, is_complete: bool = False):
        """Set chapter progress.
        
        Args:
            unlocked_chapters: Number of chapters currently unlocked
            progress_pct: Progress percentage toward next chapter (0-100)
            total_chapters: Total chapters in story
            is_complete: Whether all chapters are unlocked
        """
        self.percentage = min(max(progress_pct / 100.0, 0.0), 1.0)
        self.unlocked = unlocked_chapters
        self.total = total_chapters
        self.is_complete = is_complete
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        rect = self.rect().adjusted(5, 5, -5, -5)
        
        # Background Track
        pen = QtGui.QPen(QtGui.QColor("#2a3a2a"), 6)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(rect)
        
        # Progress Arc (green for story progress, gold if complete)
        arc_color = "#ffd700" if self.is_complete else "#8bc34a"
        pen.setColor(QtGui.QColor(arc_color))
        painter.setPen(pen)
        
        start_angle = 90 * 16
        span_angle = -int(self.percentage * 360 * 16)
        painter.drawArc(rect, start_angle, span_angle)
        
        # Main text: "📖 X/Y" chapters
        painter.setPen(QtGui.QColor("#ffffff"))
        font = painter.font()
        font.setPixelSize(13)
        font.setBold(True)
        painter.setFont(font)
        
        main_rect = QtCore.QRectF(rect)
        painter.drawText(main_rect, QtCore.Qt.AlignmentFlag.AlignCenter, f"📖{self.unlocked}/{self.total}")
        
        # Subtext: progress percentage or "Done!"
        font.setPixelSize(10)
        font.setBold(False)
        painter.setFont(font)
        sub_rect = QtCore.QRectF(rect.adjusted(0, 20, 0, 0))
        painter.setPen(QtGui.QColor(arc_color))
        
        if self.is_complete:
            painter.drawText(sub_rect, QtCore.Qt.AlignmentFlag.AlignCenter, "✨Done")
        else:
            pct = int(self.percentage * 100)
            painter.drawText(sub_rect, QtCore.Qt.AlignmentFlag.AlignCenter, f"{pct}%")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class XPRingWidget(QtWidgets.QWidget):
    """Circular progress bar for XP to next level."""
    clicked = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.percentage = 0.0
        self.text = "Lv.1"
        self.subtext = "Novice"
        self.setMinimumSize(60, 60)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    def set_progress(self, level: int, xp_in_level: int, xp_needed: int, total_xp: int):
        """Set XP progress toward next level."""
        xp_needed = max(1, xp_needed)  # Avoid division by zero
        self.percentage = min(xp_in_level / xp_needed, 1.0)
        self.text = f"Lv.{level}"
        
        # Get level title name
        try:
            from gamification import get_level_title
            title, emoji = get_level_title(level)
            self.subtext = title
        except Exception:
            self.subtext = "Novice"
        
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Adjust rect to ensure stroke doesn't clip
        rect = self.rect().adjusted(5, 5, -5, -5)
        
        # Draw Background Track
        pen = QtGui.QPen(QtGui.QColor("#2a2a4a"), 6)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(rect)
        
        # Draw Progress Arc (gold/yellow for XP)
        pen.setColor(QtGui.QColor("#ffd700"))
        painter.setPen(pen)
        
        start_angle = 90 * 16
        span_angle = -int(self.percentage * 360 * 16)
        painter.drawArc(rect, start_angle, span_angle)
        
        # Draw Level Text
        painter.setPen(QtGui.QColor("#ffffff"))
        font = painter.font()
        font.setPixelSize(13)
        font.setBold(True)
        painter.setFont(font)
        
        text_rect = QtCore.QRectF(rect)
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, self.text)
        
        # Draw XP subtext below
        font.setPixelSize(10)
        font.setBold(False)
        painter.setFont(font)
        sub_rect = QtCore.QRectF(rect.adjusted(0, 20, 0, 0))
        painter.setPen(QtGui.QColor("#ffd700"))
        painter.drawText(sub_rect, QtCore.Qt.AlignmentFlag.AlignCenter, self.subtext)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class FocusRingWidget(QtWidgets.QWidget):
    """Circular progress bar for daily focus goal."""
    clicked = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.percentage = 0.0
        self.text = "0%"
        self.subtext = "Focus"
        self.setMinimumSize(60, 60)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    def set_progress(self, current_seconds, goal_seconds):
        # Guard against negative values
        current_seconds = max(0, current_seconds)
        goal_seconds = max(1, goal_seconds)  # Minimum 1 to avoid division by zero
        
        self.percentage = min(current_seconds / goal_seconds, 1.0)
            
        hours = int(current_seconds // 3600)
        mins = int((current_seconds % 3600) // 60)
        
        # If less than an hour, show minutes only or "0h 30m"
        if hours > 0:
            self.text = f"{hours}h {mins}m"
        else:
            self.text = f"{mins}m"
            
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Adjust rect to ensure stroke doesn't clip
        rect = self.rect().adjusted(5, 5, -5, -5)
        
        # Draw Background Track
        pen = QtGui.QPen(QtGui.QColor("#2a2a4a"), 6)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(rect)
        
        # Draw Progress Arc
        # QPainter draws arcs in 1/16th of a degree
        # 0 degrees is 3 o'clock. We want to start at 12 o'clock (90 degrees)
        # Positive span is counter-clockwise? No, generic is counter-clockwise.
        # But wait, 90 is 12 o'clock. 
        # To draw clockwise, we need negative span.
        
        pen.setColor(QtGui.QColor("#6366f1"))
        painter.setPen(pen)
        
        start_angle = 90 * 16
        span_angle = -int(self.percentage * 360 * 16)
        
        # If full circle, draw ellipse to avoid artifact? Arc is fine.
        painter.drawArc(rect, start_angle, span_angle)
        
        # Draw Text
        painter.setPen(QtGui.QColor("#ffffff"))
        
        # Center Text
        font = painter.font()
        font.setPixelSize(13)
        font.setBold(True)
        painter.setFont(font)
        
        # Draw main text in center
        text_rect = QtCore.QRectF(rect)
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, self.text)
        
        # Draw subtext below
        font.setPixelSize(10)
        font.setBold(False)
        painter.setFont(font)
        sub_rect = QtCore.QRectF(rect.adjusted(0, 20, 0, 0))
        painter.setPen(QtGui.QColor("#aaaaaa"))
        painter.drawText(sub_rect, QtCore.Qt.AlignmentFlag.AlignCenter, self.subtext)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class EntitiesRingWidget(QtWidgets.QWidget):
    """Circular progress bar for entities bonded (Entitidex collection)."""
    clicked = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.percentage = 0.0
        self.normal_count = 0
        self.exceptional_count = 0
        self.total_possible = 45  # 9 entities × 5 story pools
        self.setMinimumSize(60, 60)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    def set_progress(self, normal_count: int, exceptional_count: int, total_possible: int = 45):
        """Set entities bonded progress.
        
        Args:
            normal_count: Number of normal entities collected
            exceptional_count: Number of exceptional entities collected
            total_possible: Total entities that can be collected
        """
        self.normal_count = normal_count
        self.exceptional_count = exceptional_count
        self.total_possible = max(1, total_possible)
        total_bonded = normal_count + exceptional_count
        self.percentage = min(total_bonded / self.total_possible, 1.0)
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        rect = self.rect().adjusted(5, 5, -5, -5)
        
        # Background Track
        pen = QtGui.QPen(QtGui.QColor("#2a2a3a"), 6)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(rect)
        
        # Progress Arc (purple/magenta for entities)
        # Golden glow if we have any exceptional entities
        if self.exceptional_count > 0:
            arc_color = "#ba68c8"  # Purple for exceptional
        else:
            arc_color = "#9c27b0"  # Darker purple for normal only
        
        pen.setColor(QtGui.QColor(arc_color))
        painter.setPen(pen)
        
        start_angle = 90 * 16
        span_angle = -int(self.percentage * 360 * 16)
        painter.drawArc(rect, start_angle, span_angle)
        
        # Main text: total count with star emoji, exceptional part in brighter color
        total_bonded = self.normal_count + self.exceptional_count
        font = painter.font()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        
        main_rect = QtCore.QRectF(rect)
        
        # Draw the count with exceptional part highlighted
        if self.exceptional_count > 0 and self.normal_count > 0:
            # Format: ⭐normal+exceptional where exceptional is brighter
            text = f"⭐{self.normal_count}"
            exc_text = f"+{self.exceptional_count}"
            
            # Calculate positions for centered text
            fm = QtGui.QFontMetrics(font)
            full_text = text + exc_text
            total_width = fm.horizontalAdvance(full_text)
            center_x = main_rect.center().x()
            start_x = center_x - total_width / 2
            text_y = main_rect.center().y() + fm.ascent() / 2 - 2
            
            # Draw normal part in white
            painter.setPen(QtGui.QColor("#ffffff"))
            painter.drawText(QtCore.QPointF(start_x, text_y), text)
            
            # Draw exceptional part in bright gold
            painter.setPen(QtGui.QColor("#ffd700"))
            painter.drawText(QtCore.QPointF(start_x + fm.horizontalAdvance(text), text_y), exc_text)
        else:
            # Just show total in appropriate color
            if self.exceptional_count > 0:
                painter.setPen(QtGui.QColor("#ffd700"))  # All exceptional - gold
            else:
                painter.setPen(QtGui.QColor("#ffffff"))  # Normal only - white
            painter.drawText(main_rect, QtCore.Qt.AlignmentFlag.AlignCenter, f"⭐{total_bonded}")
        
        # Subtext: "Bonded" or show exceptional count if any
        font.setPixelSize(10)
        font.setBold(False)
        painter.setFont(font)
        sub_rect = QtCore.QRectF(rect.adjusted(0, 20, 0, 0))
        painter.setPen(QtGui.QColor(arc_color))
        
        if self.exceptional_count > 0:
            painter.drawText(sub_rect, QtCore.Qt.AlignmentFlag.AlignCenter, f"✨{self.exceptional_count}")
        else:
            painter.drawText(sub_rect, QtCore.Qt.AlignmentFlag.AlignCenter, "Bonded")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ChronoStreamWidget(QtWidgets.QWidget):
    """Timeline visualization for 24h events."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.events = []  # List of dicts with 'start', 'end', 'color', 'label'
        self.setMinimumHeight(60)
        
        # Update current time indicator periodically
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update) # Just repaint
        self.timer.start(60000) # Every minute
        self.destroyed.connect(self._cleanup_timer)
    
    def _cleanup_timer(self):
        """Stop timer when widget is destroyed."""
        if self.timer:
            self.timer.stop()

    def set_events(self, events):
        self.events = events
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        
        # Guard against zero/invalid dimensions
        if width < 10 or height < 10:
            return
        
        # Colors
        bg_color = QtGui.QColor("#16213e")
        line_color = QtGui.QColor("#4a4a6a")
        text_color = QtGui.QColor("#8888aa")
        
        # Background
        painter.fillRect(rect, bg_color)
        
        # Geometry
        # Top half: Visualization blocks
        # Bottom half: Ruler
        ruler_y = int(height * 0.7)
        block_y = int(height * 0.2)
        block_h = int(height * 0.4)
        
        # Draw Ruler Line
        pen = QtGui.QPen(line_color)
        painter.setPen(pen)
        painter.drawLine(0, ruler_y, width, ruler_y)
        
        # Draw Hour Markers
        painter.setFont(QtGui.QFont("Segoe UI", 8))
        for h in range(0, 25, 4): # 0, 4, 8, 12...
            x = int((h / 24.0) * width)
            
            # Tick
            painter.drawLine(x, ruler_y, x, ruler_y + 5)
            
            # Label
            # Adjust x for text centering
            label = f"{h:02}"
            text_rect = QtCore.QRect(x - 15, ruler_y + 8, 30, 20)
            painter.setPen(text_color)
            painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, label)
            painter.setPen(line_color) # Reset for next line

        # Draw Events
        for evt in self.events:
            start = evt.get('start', 0)
            end = evt.get('end', 0)
            color = evt.get('color', QtGui.QColor("#4caf50"))
            
            # Validate and clamp values to 0-24 range
            start = max(0.0, min(24.0, start))
            end = max(0.0, min(24.0, end))
            
            # Skip if start == end (zero duration)
            if abs(end - start) < 0.01:
                continue
            
            # Normalize to 0-24
            # Handle wrapping
            blocks = []
            if end < start:
                blocks.append((start, 24.0))
                blocks.append((0.0, end))
            else:
                blocks.append((start, end))
                
            painter.setBrush(QtGui.QBrush(color))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            
            for s, e in blocks:
                # Calculate coords
                x = (s / 24.0) * width
                w = ((e - s) / 24.0) * width
                
                block_rect = QtCore.QRectF(x, block_y, w, block_h)
                painter.drawRoundedRect(block_rect, 4, 4)

        # Draw Current Time Indicator
        now = datetime.now()
        curr_h = now.hour + now.minute / 60.0
        cx = int((curr_h / 24.0) * width)
        
        pen_curr = QtGui.QPen(QtGui.QColor("#ff5252"), 2)
        painter.setPen(pen_curr)
        painter.drawLine(cx, 0, cx, height)
        
        # Draw "Now" bubble
        bubble_rect = QtCore.QRectF(cx - 16, 5, 32, 16)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#ff5252")))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bubble_rect, 8, 8)
        
        painter.setPen(QtGui.QColor("#ffffff"))
        font = painter.font()
        font.setPixelSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(bubble_rect, QtCore.Qt.AlignmentFlag.AlignCenter, "NOW")


class DailyTimelineWidget(QtWidgets.QFrame):
    """Container widget for the Daily Timeline (Hybrid View)."""
    
    # Signals emitted when ring widgets are clicked
    water_clicked = QtCore.Signal()
    chapter_clicked = QtCore.Signal()
    focus_clicked = QtCore.Signal()
    xp_clicked = QtCore.Signal()
    entities_clicked = QtCore.Signal()
    
    def __init__(self, blocker: 'BlockerCore', parent=None):
        super().__init__(parent)
        self.blocker = blocker
        self.setObjectName("DailyTimeline")
        self.setStyleSheet("""
            #DailyTimeline {
                background-color: #1a1a2e;
                border-bottom: 1px solid #2a2a4a;
            }
        """)
        self.setFixedHeight(110)
        
        self._init_ui()
        
        # Timer for periodic updates
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(30000) # Every 30 seconds
        self.destroyed.connect(self._cleanup_timer)
        
        # Initial update - delayed to avoid blocking window creation
        QtCore.QTimer.singleShot(1000, self.update_data)
    
    def _cleanup_timer(self):
        """Stop timer when widget is destroyed."""
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()

    def _init_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)
        
        # Ring widgets in order: Water, Chapter, Focus, Entities, XP
        
        # Water Ring
        self.water_ring = WaterRingWidget()
        self.water_ring.setFixedSize(70, 70)
        self.water_ring.clicked.connect(self.water_clicked.emit)
        layout.addWidget(self.water_ring)
        
        # Chapter Ring
        self.chapter_ring = ChapterRingWidget()
        self.chapter_ring.setFixedSize(70, 70)
        self.chapter_ring.clicked.connect(self.chapter_clicked.emit)
        layout.addWidget(self.chapter_ring)
        
        # Focus Ring
        self.focus_ring = FocusRingWidget()
        self.focus_ring.setFixedSize(70, 70)
        self.focus_ring.clicked.connect(self.focus_clicked.emit)
        layout.addWidget(self.focus_ring)
        
        # Entities Ring (Entitidex bonded count)
        self.entities_ring = EntitiesRingWidget()
        self.entities_ring.setFixedSize(70, 70)
        self.entities_ring.clicked.connect(self.entities_clicked.emit)
        layout.addWidget(self.entities_ring)
        
        # XP Ring
        self.xp_ring = XPRingWidget()
        self.xp_ring.setFixedSize(70, 70)
        self.xp_ring.clicked.connect(self.xp_clicked.emit)
        layout.addWidget(self.xp_ring)
        
        # Separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #2a2a4a;")
        layout.addWidget(line)
        
        # 2. Chrono-Stream
        self.timeline = ChronoStreamWidget()
        layout.addWidget(self.timeline, stretch=1)

    def update_data(self):
        """Update all timeline data. Called periodically and on events."""
        if not self.isVisible():
            return
            
        # 1. Update Focus Ring
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            daily_stats = self.blocker.stats.get("daily_stats", {}).get(today, {})
            focus_sec = daily_stats.get("focus_time", 0)
            
            # Todo: Get goal from somewhere. Defaulting to 4 hours.
            goal_sec = 4 * 3600 
            
            self.focus_ring.set_progress(focus_sec, goal_sec)
        except Exception:
            pass

        # 2. Update Water Ring (with entity perk-enhanced cap)
        try:
            today_date = datetime.now().strftime("%Y-%m-%d")
            water_entries = getattr(self.blocker, 'water_entries', [])
            today_water = sum(1 for e in water_entries if e.get('date') == today_date)
            
            # Get perk-enhanced daily cap (default 8, but entity perks can increase it)
            daily_cap = 8
            if hasattr(self.blocker, 'adhd_buster') and self.blocker.adhd_buster:
                try:
                    from gamification import get_hydration_daily_cap
                    daily_cap = get_hydration_daily_cap(self.blocker.adhd_buster)
                except Exception:
                    pass
            
            self.water_ring.set_progress(today_water, daily_cap)
        except Exception:
            self.water_ring.set_progress(0, 8)

        # 3. Update Chapter Ring (power-based story progress)
        try:
            if hasattr(self.blocker, 'adhd_buster') and self.blocker.adhd_buster:
                from gamification import get_story_progress
                story = get_story_progress(self.blocker.adhd_buster)
                
                unlocked = len(story.get('unlocked_chapters', []))
                total = story.get('total_chapters', 7)
                
                # Calculate progress percentage toward next chapter
                if story.get('next_threshold'):
                    prev_threshold = story.get('prev_threshold', 0)
                    next_threshold = story['next_threshold']
                    current_power = story.get('power', 0)
                    
                    range_size = next_threshold - prev_threshold
                    if range_size > 0:
                        progress_in_range = current_power - prev_threshold
                        chapter_progress = (progress_in_range / range_size) * 100
                        chapter_progress = max(0, min(100, chapter_progress))
                    else:
                        chapter_progress = 100.0
                    is_complete = False
                else:
                    # All chapters unlocked
                    chapter_progress = 100.0
                    is_complete = True
                
                self.chapter_ring.set_progress(unlocked, chapter_progress, total, is_complete)
            else:
                self.chapter_ring.set_progress(0, 0.0, 7, False)
        except Exception:
            self.chapter_ring.set_progress(0, 0.0, 7, False)

        # 4. Update XP Ring
        try:
            if hasattr(self.blocker, 'adhd_buster') and self.blocker.adhd_buster:
                total_xp = self.blocker.adhd_buster.get("total_xp", 0)
                if get_level_from_xp:
                    level, xp_in_level, xp_needed, progress = get_level_from_xp(total_xp)
                    self.xp_ring.set_progress(level, xp_in_level, xp_needed, total_xp)
                    self.xp_ring.setVisible(True)
                else:
                    self.xp_ring.setVisible(False)
            else:
                self.xp_ring.setVisible(False)
        except Exception:
            pass

        # 5. Update Entities Ring (Entitidex bonded count)
        try:
            if hasattr(self.blocker, 'adhd_buster') and self.blocker.adhd_buster:
                entitidex_data = self.blocker.adhd_buster.get("entitidex", {})
                collected = entitidex_data.get("collected_entity_ids", [])
                exceptional_entities = entitidex_data.get("exceptional_entities", {})
                
                # collected_entity_ids contains ALL collected (both normal + exceptional)
                # exceptional_entities is a dict keyed by entity_id for exceptional ones
                total_collected = len(collected)
                exceptional_count = len(exceptional_entities)
                normal_count = total_collected - exceptional_count  # Subtract to get normal-only count
                
                # Total possible: 9 entities × 5 story pools = 45
                total_possible = 45
                
                self.entities_ring.set_progress(normal_count, exceptional_count, total_possible)
                self.entities_ring.setVisible(True)
            else:
                self.entities_ring.set_progress(0, 0, 45)
        except Exception:
            self.entities_ring.set_progress(0, 0, 45)

        # 6. Update Timeline Events
        events = []
        
        today_date = datetime.now().date()
        yesterday_date = today_date - timedelta(days=1)
        today_str = today_date.strftime("%Y-%m-%d")
        yesterday_str = yesterday_date.strftime("%Y-%m-%d")

        # Add sleep events
        try:
            sleep_entries = getattr(self.blocker, 'sleep_entries', [])
            for entry in sleep_entries:
                entry_date = entry.get('date')
                bedtime_str = entry.get('bedtime')
                waketime_str = entry.get('wake_time')
                
                if not (bedtime_str and waketime_str): 
                    continue
                    
                # Convert times to floats
                try:
                    bh, bm = map(int, bedtime_str.split(':'))
                    wh, wm = map(int, waketime_str.split(':'))
                    
                    # Validate time ranges
                    if not (0 <= bh <= 23 and 0 <= bm <= 59 and 0 <= wh <= 23 and 0 <= wm <= 59):
                        continue
                    
                    b_float = bh + bm/60.0
                    w_float = wh + wm/60.0
                except (ValueError, AttributeError, TypeError):
                    continue

                if entry_date == yesterday_str:
                    # Sleep started yesterday. Ends today?
                    if w_float < b_float:
                        # Ends today (standard sleep)
                        events.append({
                            'start': 0.0,
                            'end': w_float,
                            'color': QtGui.QColor("#3949ab"), # Indigo
                            'label': 'Sleep'
                        })
                
                elif entry_date == today_str:
                    # Sleep starts today
                    if w_float < b_float:
                        # Wraps to tomorrow
                        events.append({
                            'start': b_float,
                            'end': 24.0,
                            'color': QtGui.QColor("#3949ab"),
                            'label': 'Sleep'
                        })
                    else:
                        # Nap
                        events.append({
                            'start': b_float,
                            'end': w_float,
                            'color': QtGui.QColor("#3949ab"),
                            'label': 'Nap'
                        })
        except Exception as e:
            pass 

        # Add water events (mark moments when water was logged)
        try:
            water_entries = getattr(self.blocker, 'water_entries', [])
            for entry in water_entries:
                entry_date = entry.get('date')
                entry_time = entry.get('time')
                
                if entry_date == today_str and entry_time:
                    try:
                        # Parse time
                        h, m = map(int, entry_time.split(':'))
                        if 0 <= h <= 23 and 0 <= m <= 59:
                            time_float = h + m/60.0
                            # Show as a 5-minute block
                            events.append({
                                'start': time_float,
                                'end': min(time_float + 5/60.0, 24.0),
                                'color': QtGui.QColor("#4fc3f7"), # Cyan
                                'label': '💧 Water'
                            })
                    except (ValueError, AttributeError, TypeError):
                        continue
        except Exception:
            pass

        # Add active focus session (if currently running)
        try:
            if hasattr(self.blocker, 'session_start') and self.blocker.session_start:
                session_start_ts = self.blocker.session_start
                now_ts = QtCore.QDateTime.currentDateTime().toSecsSinceEpoch()
                
                # Convert to datetime objects
                session_start_dt = datetime.fromtimestamp(session_start_ts)
                now_dt = datetime.fromtimestamp(now_ts)
                
                # Check if session started today
                if session_start_dt.date() == today_date:
                    start_hour = session_start_dt.hour + session_start_dt.minute / 60.0
                    end_hour = now_dt.hour + now_dt.minute / 60.0
                    
                    # Handle sessions that cross midnight
                    if end_hour < start_hour:
                        # Session continues past midnight - show until end of day
                        events.append({
                            'start': start_hour,
                            'end': 24.0,
                            'color': QtGui.QColor("#4caf50"), # Green for active session
                            'label': '🎯 Focus Session (Active)'
                        })
                    else:
                        events.append({
                            'start': start_hour,
                            'end': end_hour,
                            'color': QtGui.QColor("#4caf50"), # Green for active session
                            'label': '🎯 Focus Session (Active)'
                        })
        except Exception:
            pass

        self.timeline.set_events(events)


class DevTab(QtWidgets.QWidget):
    """Developer tools tab for testing - generate items, add coins, add XP."""

    def __init__(self, blocker, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        
        # Warning label
        warning = QtWidgets.QLabel("⚠️ Developer Tools - For Testing Only")
        warning.setStyleSheet("color: #ff9800; font-weight: bold; font-size: 14px; padding: 10px;")
        warning.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(warning)

        # Generate Item Section
        item_group = QtWidgets.QGroupBox("🎁 Generate Item")
        item_layout = QtWidgets.QVBoxLayout(item_group)
        
        # Rarity selector
        rarity_layout = QtWidgets.QHBoxLayout()
        rarity_layout.addWidget(QtWidgets.QLabel("Rarity:"))
        self.rarity_combo = NoScrollComboBox()
        self.rarity_combo.addItems(["Common", "Uncommon", "Rare", "Epic", "Legendary"])
        self.rarity_combo.setCurrentText("Common")
        rarity_layout.addWidget(self.rarity_combo)
        rarity_layout.addStretch()
        item_layout.addLayout(rarity_layout)
        
        # Generate buttons for each rarity
        btn_layout = QtWidgets.QHBoxLayout()
        for rarity in ["Common", "Uncommon", "Rare", "Epic", "Legendary"]:
            btn = QtWidgets.QPushButton(rarity)
            color = {"Common": "#9e9e9e", "Uncommon": "#4caf50", "Rare": "#2196f3", 
                     "Epic": "#9c27b0", "Legendary": "#ff9800"}[rarity]
            btn.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold; padding: 8px;")
            btn.clicked.connect(lambda checked, r=rarity: self._generate_item(r))
            btn_layout.addWidget(btn)
        item_layout.addLayout(btn_layout)
        
        layout.addWidget(item_group)

        # Add Coins Section
        coins_group = QtWidgets.QGroupBox("🪙 Add Coins")
        coins_layout = QtWidgets.QHBoxLayout(coins_group)
        
        for amount in [100, 500, 1000, 5000]:
            btn = QtWidgets.QPushButton(f"+{amount}")
            btn.setStyleSheet("background-color: #ffd700; color: black; font-weight: bold; padding: 8px;")
            btn.clicked.connect(lambda checked, a=amount: self._add_coins(a))
            coins_layout.addWidget(btn)
        
        layout.addWidget(coins_group)

        # Add XP Section
        xp_group = QtWidgets.QGroupBox("⭐ Add Experience")
        xp_layout = QtWidgets.QHBoxLayout(xp_group)
        
        for amount in [50, 100, 500, 1000]:
            btn = QtWidgets.QPushButton(f"+{amount} XP")
            btn.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; padding: 8px;")
            btn.clicked.connect(lambda checked, a=amount: self._add_xp(a))
            xp_layout.addWidget(btn)
        
        layout.addWidget(xp_group)

        # Cooldown Reset Section
        cooldown_group = QtWidgets.QGroupBox("⏱️ Reset Cooldowns")
        cooldown_layout = QtWidgets.QHBoxLayout(cooldown_group)
        
        water_reset_btn = QtWidgets.QPushButton("💧 Reset Water Cooldown")
        water_reset_btn.setStyleSheet("background-color: #2196f3; color: white; font-weight: bold; padding: 8px;")
        water_reset_btn.clicked.connect(self._reset_water_cooldown)
        cooldown_layout.addWidget(water_reset_btn)
        
        water_attempts_btn = QtWidgets.QPushButton("🎰 Reset Lottery Attempts")
        water_attempts_btn.setStyleSheet("background-color: #9c27b0; color: white; font-weight: bold; padding: 8px;")
        water_attempts_btn.clicked.connect(self._reset_water_lottery_attempts)
        cooldown_layout.addWidget(water_attempts_btn)
        
        layout.addWidget(cooldown_group)

        # Entity Encounter Section
        entity_group = QtWidgets.QGroupBox("🐾 Entity Encounter Test")
        entity_layout = QtWidgets.QVBoxLayout(entity_group)
        
        # Story selector
        story_layout = QtWidgets.QHBoxLayout()
        story_layout.addWidget(QtWidgets.QLabel("Story:"))
        self.story_combo = NoScrollComboBox()
        self.story_combo.addItems(["warrior", "scholar", "underdog", "scientist", "wanderer"])
        self.story_combo.currentTextChanged.connect(self._refresh_entity_selector)
        story_layout.addWidget(self.story_combo)
        story_layout.addStretch()
        entity_layout.addLayout(story_layout)
        
        # Entity selector
        entity_select_layout = QtWidgets.QHBoxLayout()
        entity_select_layout.addWidget(QtWidgets.QLabel("Entity:"))
        self.entity_combo = NoScrollComboBox()
        self.entity_combo.setMinimumWidth(250)
        entity_select_layout.addWidget(self.entity_combo)
        entity_select_layout.addStretch()
        entity_layout.addLayout(entity_select_layout)
        
        # Initialize entity list
        QtCore.QTimer.singleShot(50, self._refresh_entity_selector)
        
        # Encounter buttons
        encounter_btn_layout = QtWidgets.QHBoxLayout()
        
        selected_btn = QtWidgets.QPushButton("🎯 Encounter Selected")
        selected_btn.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; padding: 8px;")
        selected_btn.clicked.connect(self._encounter_selected_entity)
        encounter_btn_layout.addWidget(selected_btn)
        
        trigger_btn = QtWidgets.QPushButton("🎲 Random Encounter")
        trigger_btn.setStyleSheet("background-color: #2196f3; color: white; font-weight: bold; padding: 8px;")
        trigger_btn.clicked.connect(self._trigger_entity_encounter)
        encounter_btn_layout.addWidget(trigger_btn)
        
        entity_layout.addLayout(encounter_btn_layout)
        
        # Rarity-specific encounter buttons
        rarity_btn_layout = QtWidgets.QHBoxLayout()
        for rarity in ["common", "uncommon", "rare", "epic", "legendary"]:
            btn = QtWidgets.QPushButton(rarity.capitalize())
            color = {"common": "#9e9e9e", "uncommon": "#4caf50", "rare": "#2196f3", 
                     "epic": "#9c27b0", "legendary": "#ff9800"}[rarity]
            btn.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold; padding: 6px;")
            btn.clicked.connect(lambda checked, r=rarity: self._encounter_by_rarity(r))
            rarity_btn_layout.addWidget(btn)
        entity_layout.addLayout(rarity_btn_layout)
        
        # Entitidex viewer button
        view_btn = QtWidgets.QPushButton("📖 View Entitidex")
        view_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 8px;")
        view_btn.clicked.connect(self._view_entitidex)
        entity_layout.addWidget(view_btn)
        
        # Generate Exceptional Entity button
        exceptional_btn = QtWidgets.QPushButton("🌟 Generate EXCEPTIONAL Entity (Guaranteed)")
        exceptional_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B9D, stop:0.5 #FFD700, stop:1 #00FFFF);
                color: black;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00FFFF, stop:0.5 #FF6B9D, stop:1 #FFD700);
            }
        """)
        exceptional_btn.clicked.connect(self._generate_exceptional_entity)
        entity_layout.addWidget(exceptional_btn)
        
        layout.addWidget(entity_group)

        # Entity Lock/Unlock Section
        lock_group = QtWidgets.QGroupBox("🔓 Entity Lock/Unlock (Testing)")
        lock_layout = QtWidgets.QVBoxLayout(lock_group)
        
        # Story selector for lock/unlock
        lock_story_layout = QtWidgets.QHBoxLayout()
        lock_story_layout.addWidget(QtWidgets.QLabel("Story:"))
        self.lock_story_combo = NoScrollComboBox()
        self.lock_story_combo.addItems(["warrior", "scholar", "underdog", "scientist", "wanderer"])
        self.lock_story_combo.currentTextChanged.connect(self._refresh_entity_lock_list)
        lock_story_layout.addWidget(self.lock_story_combo)
        lock_story_layout.addStretch()
        lock_layout.addLayout(lock_story_layout)
        
        # Entity list with checkboxes (scrollable)
        self.entity_lock_list = QtWidgets.QListWidget()
        self.entity_lock_list.setStyleSheet("""
            QListWidget {
                background: #2D2D2D;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background: #3D3D3D;
            }
        """)
        self.entity_lock_list.setMaximumHeight(200)
        lock_layout.addWidget(self.entity_lock_list)
        
        # Quick action buttons
        quick_btn_layout = QtWidgets.QHBoxLayout()
        
        unlock_all_btn = QtWidgets.QPushButton("🔓 Unlock All")
        unlock_all_btn.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; padding: 8px;")
        unlock_all_btn.clicked.connect(self._unlock_all_entities)
        quick_btn_layout.addWidget(unlock_all_btn)
        
        lock_all_btn = QtWidgets.QPushButton("🔒 Lock All")
        lock_all_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        lock_all_btn.clicked.connect(self._lock_all_entities)
        quick_btn_layout.addWidget(lock_all_btn)
        
        apply_btn = QtWidgets.QPushButton("💾 Apply Changes")
        apply_btn.setStyleSheet("background-color: #2196f3; color: white; font-weight: bold; padding: 8px;")
        apply_btn.clicked.connect(self._apply_entity_lock_changes)
        quick_btn_layout.addWidget(apply_btn)
        
        lock_layout.addLayout(quick_btn_layout)
        
        layout.addWidget(lock_group)
        
        # Initial population of entity list
        QtCore.QTimer.singleShot(100, self._refresh_entity_lock_list)

        # Status display
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: #4caf50; padding: 10px;")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _generate_item(self, rarity: str) -> None:
        """Generate an item of the specified rarity."""
        try:
            from gamification import generate_item
            game_state = get_game_state()
            if not game_state:
                self.status_label.setText("❌ Game state not available")
                return
            
            active_story = self.blocker.adhd_buster.get("active_story", "warrior")
            item = generate_item(rarity=rarity, story_id=active_story)
            item["source"] = "dev_tools"
            
            game_state.add_item(item)
            self.status_label.setText(f"✅ Generated: {item.get('name', 'Unknown')} ({rarity})")
            self.status_label.setStyleSheet(f"color: #4caf50; padding: 10px;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _add_coins(self, amount: int) -> None:
        """Add coins to the player."""
        try:
            game_state = get_game_state()
            if not game_state:
                self.status_label.setText("❌ Game state not available")
                return
            
            new_total = game_state.add_coins(amount)
            self.status_label.setText(f"✅ Added {amount} coins! New total: {new_total}")
            self.status_label.setStyleSheet("color: #ffd700; padding: 10px;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _add_xp(self, amount: int) -> None:
        """Add XP to the hero."""
        try:
            game_state = get_game_state()
            if not game_state:
                self.status_label.setText("❌ Game state not available")
                return
            
            new_xp, new_level, leveled_up = game_state.add_xp(amount)
            if leveled_up:
                self.status_label.setText(f"🎉 Level Up! Now level {new_level} with {new_xp} XP")
            else:
                self.status_label.setText(f"✅ Added {amount} XP! Level {new_level}, {new_xp} XP")
            self.status_label.setStyleSheet("color: #4caf50; padding: 10px;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _get_coin_data(self) -> Optional[Dict[str, Any]]:
        """
        Get coin operation callbacks for special entity bonding rewards.
        
        Returns:
            Dict with get_coins_callback and add_coins_callback, or None if unavailable.
        """
        try:
            gs = get_game_state()
            if gs:
                def get_coins_callback() -> int:
                    return gs.coins
                
                def add_coins_callback(amount: int) -> None:
                    gs.add_coins(amount)
                
                return {
                    "get_coins_callback": get_coins_callback,
                    "add_coins_callback": add_coins_callback,
                }
        except Exception as e:
            logger.debug(f"Could not get coin data: {e}")
        return None

    def _reset_water_cooldown(self) -> None:
        """Reset water logging cooldown by clearing today's last entry time."""
        try:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Find all entries for today and set their times to 00:00
            if hasattr(self.blocker, 'water_entries') and self.blocker.water_entries:
                today_entries = [e for e in self.blocker.water_entries if e.get("date") == today]
                if today_entries:
                    # Set ALL today's entry times to 00:00 to ensure cooldown is bypassed
                    for entry in today_entries:
                        entry["time"] = "00:00"
                    self.blocker.save_config()
                    self.status_label.setText(f"✅ Water cooldown reset! ({len(today_entries)} entries set to 00:00)")
                    self.status_label.setStyleSheet("color: #2196f3; padding: 10px;")
                else:
                    self.status_label.setText("ℹ️ No water entries today - no cooldown to reset")
                    self.status_label.setStyleSheet("color: #888; padding: 10px;")
            else:
                self.status_label.setText("ℹ️ No water entries - no cooldown to reset")
                self.status_label.setStyleSheet("color: #888; padding: 10px;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _reset_water_lottery_attempts(self) -> None:
        """Reset water lottery attempts counter to 0."""
        try:
            if hasattr(self.blocker, 'water_lottery_attempts'):
                old_attempts = self.blocker.water_lottery_attempts
                self.blocker.water_lottery_attempts = 0
                self.blocker.save_config()
                self.status_label.setText(f"✅ Lottery attempts reset! (was {old_attempts}, now 0 → 1% win chance)")
                self.status_label.setStyleSheet("color: #9c27b0; padding: 10px;")
            else:
                self.blocker.water_lottery_attempts = 0
                self.blocker.save_config()
                self.status_label.setText("✅ Lottery attempts initialized to 0")
                self.status_label.setStyleSheet("color: #9c27b0; padding: 10px;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _refresh_entity_selector(self) -> None:
        """Refresh the entity selector dropdown based on selected story."""
        try:
            from entitidex import get_entities_for_story
            
            story_id = self.story_combo.currentText()
            entities = get_entities_for_story(story_id)
            
            self.entity_combo.clear()
            
            # Sort entities by rarity for easier navigation
            rarity_order = {"common": 0, "uncommon": 1, "rare": 2, "epic": 3, "legendary": 4}
            sorted_entities = sorted(entities, key=lambda e: (rarity_order.get(e.rarity.lower(), 5), e.name))
            
            for entity in sorted_entities:
                rarity_icon = {"common": "⚪", "uncommon": "🟢", "rare": "🔵", 
                               "epic": "🟣", "legendary": "🟠"}.get(entity.rarity.lower(), "⚪")
                self.entity_combo.addItem(f"{rarity_icon} {entity.name} ({entity.id})", entity.id)
            
        except Exception as e:
            self.status_label.setText(f"❌ Error loading entities: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _encounter_selected_entity(self) -> None:
        """Trigger an encounter with the selected entity."""
        try:
            from entitidex import get_entities_for_story, calculate_join_probability
            from entity_drop_dialog import show_entity_encounter
            from gamification import attempt_entitidex_bond
            import random
            
            game_state = get_game_state()
            if not game_state:
                self.status_label.setText("❌ Game state not available")
                return
            
            story_id = self.story_combo.currentText()
            entity_id = self.entity_combo.currentData()
            
            if not entity_id:
                self.status_label.setText("❌ No entity selected")
                return
            
            # Find the entity
            entities = get_entities_for_story(story_id)
            entity = next((e for e in entities if e.id == entity_id), None)
            
            if not entity:
                self.status_label.setText(f"❌ Entity not found: {entity_id}")
                return
            
            hero_power = game_state.get_current_power()
            join_prob = calculate_join_probability(hero_power, entity.power)
            is_exceptional = random.random() < 0.20  # 20% exceptional chance
            
            def bond_callback_wrapper(eid: str, exceptional: bool = is_exceptional):
                result = attempt_entitidex_bond(
                    self.blocker.adhd_buster, 
                    eid,
                    is_exceptional=exceptional
                )
                self.status_label.setText(f"Result: {'Success' if result.get('success') else 'Failed'}")
                xp_awarded = result.get('xp_awarded', 0)
                if xp_awarded > 0:
                    gs = get_game_state()
                    if gs:
                        total_xp = self.blocker.adhd_buster.get('total_xp', 0)
                        level = self.blocker.adhd_buster.get('hero', {}).get('level', 1)
                        gs.xp_changed.emit(total_xp, level)
                main_win = self.window()
                if hasattr(main_win, 'entitidex_tab'):
                    main_win.entitidex_tab.refresh()
                return result

            # Build Chad interaction data for skip interactions
            CHAD_ENTITY_ID = "underdog_008"
            chad_interaction_data = None
            try:
                from gamification import get_entitidex_manager
                manager = get_entitidex_manager(self.blocker.adhd_buster)
                
                has_chad_normal = CHAD_ENTITY_ID in manager.progress.collected_entity_ids
                has_chad_exceptional = manager.progress.is_exceptional(CHAD_ENTITY_ID)
                
                if has_chad_normal or has_chad_exceptional:
                    # Callback to add coins (for exceptional Chad's "banking hack")
                    def add_coins_callback(amount: int):
                        gs = get_game_state()
                        if gs:
                            gs.add_coins(amount)
                    
                    # Callback to give entity as if bonded (for exceptional Chad's gift)
                    def give_entity_callback():
                        result = attempt_entitidex_bond(
                            self.blocker.adhd_buster, entity.id,
                            is_exceptional=is_exceptional,
                            force_success=True  # Chad guarantees the bond!
                        )
                        from gamification import sync_hero_data
                        sync_hero_data(self.blocker.adhd_buster)
                        gs = get_game_state()
                        if gs:
                            xp_awarded = result.get('xp_awarded', 0)
                            if xp_awarded > 0:
                                total_xp = self.blocker.adhd_buster.get('total_xp', 0)
                                level = self.blocker.adhd_buster.get('hero', {}).get('level', 1)
                                gs.xp_changed.emit(total_xp, level)
                            gs.force_save()
                        main_win = self.window()
                        if hasattr(main_win, 'entitidex_tab'):
                            main_win.entitidex_tab.refresh()
                    
                    chad_interaction_data = {
                        "has_chad_normal": has_chad_normal,
                        "has_chad_exceptional": has_chad_exceptional,
                        "add_coins_callback": add_coins_callback,
                        "give_entity_callback": give_entity_callback,
                    }
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"Could not check for Chad entity: {e}")

            def save_callback_wrapper(entity_id: str):
                from gamification import save_encounter_for_later
                result = save_encounter_for_later(
                    self.blocker.adhd_buster,
                    entity_id,
                    is_exceptional=is_exceptional,
                    catch_probability=join_prob
                )
                self.blocker.save_config()
                main_win = self.window()
                if hasattr(main_win, 'entitidex_tab'):
                    main_win.entitidex_tab._update_saved_button_count()
                return result

            show_entity_encounter(
                entity=entity,
                join_probability=join_prob,
                bond_logic_callback=bond_callback_wrapper,
                parent=self.window(),
                is_exceptional=is_exceptional,
                chad_interaction_data=chad_interaction_data,
                coin_data=self._get_coin_data() if hasattr(self, '_get_coin_data') else None,
                save_callback=save_callback_wrapper,
            )
            
            self.status_label.setText(f"✨ Encountered: {entity.name} ({entity.rarity}){' ⭐' if is_exceptional else ''}")
            self.status_label.setStyleSheet("color: #4caf50; padding: 10px;")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _trigger_entity_encounter(self) -> None:
        """Trigger a full entity encounter with the encounter dialog."""
        try:
            from entitidex import (
                select_encounter_entity,
                calculate_join_probability,
                load_entitidex_progress,
                get_entities_for_story,
            )
            # from entity_encounter_dialog import EntityEncounterDialog
            
            game_state = get_game_state()
            if not game_state:
                self.status_label.setText("❌ Game state not available")
                return
            
            story_id = self.story_combo.currentText()
            hero_power = game_state.get_current_power()
            
            # Load real progress from file
            progress = load_entitidex_progress(story_id)
            
            # Select an entity for encounter (now returns tuple with is_exceptional)
            entity, is_exceptional = select_encounter_entity(progress, hero_power, story_id)
            
            if not entity:
                # Fallback: get a random entity from the story
                entities = get_entities_for_story(story_id)
                if entities:
                    import random
                    entity = random.choice(entities)
                    is_exceptional = random.random() < 0.20  # 20% exceptional chance
                else:
                    self.status_label.setText("❌ No entities available")
                    return
            
            # Calculate join probability
            join_prob = calculate_join_probability(hero_power, entity.power)
            
            # Show encounter dialog using new merge-style flow
            from entity_drop_dialog import show_entity_encounter
            
            def bond_callback_wrapper(entity_id: str, exceptional: bool = is_exceptional):
                from gamification import attempt_entitidex_bond
                result = attempt_entitidex_bond(
                    self.blocker.adhd_buster, 
                    entity_id,
                    is_exceptional=exceptional
                )
                self.status_label.setText(f"Result: {'Success' if result.get('success') else 'Failed'}")
                # Emit XP signal if XP was awarded
                xp_awarded = result.get('xp_awarded', 0)
                if xp_awarded > 0:
                    from game_state import get_game_state
                    gs = get_game_state()
                    if gs:
                        total_xp = self.blocker.adhd_buster.get('total_xp', 0)
                        level = self.blocker.adhd_buster.get('hero', {}).get('level', 1)
                        gs.xp_changed.emit(total_xp, level)
                # Refresh entitidex tab after bond attempt
                main_win = self.window()
                if hasattr(main_win, 'entitidex_tab'):
                    main_win.entitidex_tab.refresh()
                return result

            def save_callback_wrapper(entity_id: str):
                from gamification import save_encounter_for_later
                result = save_encounter_for_later(
                    self.blocker.adhd_buster,
                    entity_id,
                    is_exceptional=is_exceptional,
                    catch_probability=join_prob
                )
                self.blocker.save_config()
                main_win = self.window()
                if hasattr(main_win, 'entitidex_tab'):
                    main_win.entitidex_tab._update_saved_button_count()
                return result

            show_entity_encounter(
                entity=entity,
                join_probability=join_prob,
                bond_logic_callback=bond_callback_wrapper,
                parent=self.window(),
                is_exceptional=is_exceptional,
                coin_data=self._get_coin_data() if hasattr(self, '_get_coin_data') else None,
                save_callback=save_callback_wrapper,
            )
            
        except ImportError as e:
            self.status_label.setText(f"❌ Import error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _show_random_entity(self) -> None:
        """Show a random entity encounter from the selected story."""
        try:
            from entitidex import get_entities_for_story, calculate_join_probability
            # from entity_encounter_dialog import EntityEncounterDialog
            import random
            
            game_state = get_game_state()
            hero_power = game_state.get_current_power() if game_state else 100
            
            story_id = self.story_combo.currentText()
            entities = get_entities_for_story(story_id)
            
            if not entities:
                self.status_label.setText(f"❌ No entities for story: {story_id}")
                return
            
            entity = random.choice(entities)
            join_prob = calculate_join_probability(hero_power, entity.power)
            is_exceptional = random.random() < 0.20  # 20% exceptional chance
            
            # Show encounter dialog using new merge-style flow
            from entity_drop_dialog import show_entity_encounter
            
            def bond_callback_wrapper(entity_id: str, exceptional: bool = is_exceptional):
                from gamification import attempt_entitidex_bond
                result = attempt_entitidex_bond(
                    self.blocker.adhd_buster, entity_id, is_exceptional=exceptional
                )
                self.status_label.setText(f"Result: {result['success']}")
                # Emit XP signal if XP was awarded
                xp_awarded = result.get('xp_awarded', 0)
                if xp_awarded > 0:
                    from game_state import get_game_state
                    gs = get_game_state()
                    if gs:
                        total_xp = self.blocker.adhd_buster.get('total_xp', 0)
                        level = self.blocker.adhd_buster.get('hero', {}).get('level', 1)
                        gs.xp_changed.emit(total_xp, level)
                # Refresh entitidex tab after bond attempt
                main_win = self.window()
                if hasattr(main_win, 'entitidex_tab'):
                    main_win.entitidex_tab.refresh()
                return result

            def save_callback_wrapper(entity_id: str):
                from gamification import save_encounter_for_later
                result = save_encounter_for_later(
                    self.blocker.adhd_buster,
                    entity_id,
                    is_exceptional=is_exceptional,
                    catch_probability=join_prob
                )
                self.blocker.save_config()
                main_win = self.window()
                if hasattr(main_win, 'entitidex_tab'):
                    main_win.entitidex_tab._update_saved_button_count()
                return result

            show_entity_encounter(
                entity=entity, 
                join_probability=join_prob,
                bond_logic_callback=bond_callback_wrapper,
                parent=self.window(),
                is_exceptional=is_exceptional,
                coin_data=self._get_coin_data() if hasattr(self, '_get_coin_data') else None,
                save_callback=save_callback_wrapper,
            )
            
            self.status_label.setText(f"✨ Encountered: {entity.name} ({entity.rarity}){' ⭐' if is_exceptional else ''}")
            self.status_label.setStyleSheet("color: #2196f3; padding: 10px;")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _encounter_by_rarity(self, rarity: str) -> None:
        """Show an entity encounter for a specific rarity."""
        try:
            from entitidex import get_entities_for_story, calculate_join_probability
            # from entity_encounter_dialog import EntityEncounterDialog
            import random
            
            game_state = get_game_state()
            hero_power = game_state.get_current_power() if game_state else 100
            
            story_id = self.story_combo.currentText()
            entities = get_entities_for_story(story_id)
            
            # Filter by rarity
            matching = [e for e in entities if e.rarity.lower() == rarity.lower()]
            
            if not matching:
                self.status_label.setText(f"❌ No {rarity} entities for {story_id}")
                return
            
            entity = random.choice(matching)
            join_prob = calculate_join_probability(hero_power, entity.power)
            is_exceptional = random.random() < 0.20  # 20% exceptional chance
            
            # Show encounter dialog using new merge-style flow
            from entity_drop_dialog import show_entity_encounter
            
            def bond_callback_wrapper(entity_id: str, exceptional: bool = is_exceptional):
                from gamification import attempt_entitidex_bond
                result = attempt_entitidex_bond(
                    self.blocker.adhd_buster, entity_id, is_exceptional=exceptional
                )
                # Emit XP signal if XP was awarded
                xp_awarded = result.get('xp_awarded', 0)
                if xp_awarded > 0:
                    from game_state import get_game_state
                    gs = get_game_state()
                    if gs:
                        total_xp = self.blocker.adhd_buster.get('total_xp', 0)
                        level = self.blocker.adhd_buster.get('hero', {}).get('level', 1)
                        gs.xp_changed.emit(total_xp, level)
                # Refresh entitidex tab after bond attempt
                main_win = self.window()
                if hasattr(main_win, 'entitidex_tab'):
                    main_win.entitidex_tab.refresh()
                return result

            def save_callback_wrapper(entity_id: str):
                from gamification import save_encounter_for_later
                result = save_encounter_for_later(
                    self.blocker.adhd_buster,
                    entity_id,
                    is_exceptional=is_exceptional,
                    catch_probability=join_prob
                )
                self.blocker.save_config()
                main_win = self.window()
                if hasattr(main_win, 'entitidex_tab'):
                    main_win.entitidex_tab._update_saved_button_count()
                return result

            show_entity_encounter(
                entity=entity, 
                join_probability=join_prob,
                bond_logic_callback=bond_callback_wrapper,
                parent=self.window(),
                is_exceptional=is_exceptional,
                coin_data=self._get_coin_data() if hasattr(self, '_get_coin_data') else None,
                save_callback=save_callback_wrapper,
            )
            
            self.status_label.setText(f"✨ {rarity.upper()}: {entity.name}{' ⭐' if is_exceptional else ''}")
            color = {"common": "#9e9e9e", "uncommon": "#4caf50", "rare": "#2196f3", 
                     "epic": "#9c27b0", "legendary": "#ff9800"}.get(rarity, "#4caf50")
            self.status_label.setStyleSheet(f"color: {color}; padding: 10px;")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _generate_exceptional_entity(self) -> None:
        """Generate a guaranteed exceptional entity (bypasses 5% roll)."""
        try:
            from entitidex import get_entities_for_story, calculate_join_probability
            from gamification import _generate_exceptional_colors, get_entitidex_manager, save_entitidex_progress
            from entity_drop_dialog import _show_exceptional_celebration
            import random
            
            story_id = self.story_combo.currentText()
            entities = get_entities_for_story(story_id)
            
            if not entities:
                self.status_label.setText(f"❌ No entities for story: {story_id}")
                return
            
            # Pick a random entity
            entity = random.choice(entities)
            
            # Generate exceptional colors
            exceptional_colors = _generate_exceptional_colors()
            
            # Get the entitidex manager and add the entity as collected + exceptional
            manager = get_entitidex_manager(self.blocker.adhd_buster)
            
            # Mark as collected if not already
            if entity.id not in manager.progress.collected_entity_ids:
                manager.progress.collected_entity_ids.add(entity.id)
            
            # Mark as exceptional with unique colors
            manager.progress.mark_exceptional(entity.id, exceptional_colors)
            
            # Save progress
            save_entitidex_progress(self.blocker.adhd_buster, manager)
            self.blocker.save_config()
            
            # Refresh entitidex tab
            main_win = self.window()
            if hasattr(main_win, 'entitidex_tab'):
                main_win.entitidex_tab.refresh()
            
            # Show celebration
            _show_exceptional_celebration(entity, exceptional_colors, self.window())
            
            # Use exceptional_name if available
            display_name = entity.exceptional_name if entity.exceptional_name else entity.name
            border_col = exceptional_colors.get("border", "#FFD700")
            self.status_label.setText(f"🌟 EXCEPTIONAL {display_name} added!")
            self.status_label.setStyleSheet(f"color: {border_col}; padding: 10px; font-weight: bold;")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _view_entitidex(self) -> None:
        """Open the Entitidex viewer dialog."""
        try:
            from entitidex import get_entities_for_story
            
            story_id = self.story_combo.currentText()
            entities = get_entities_for_story(story_id)
            
            # Create a simple viewer dialog
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle(f"📖 Entitidex - {story_id.capitalize()}")
            dialog.setFixedSize(600, 500)
            dialog.setStyleSheet("background: #1E1E1E;")
            
            layout = QtWidgets.QVBoxLayout(dialog)
            
            # Title
            title = QtWidgets.QLabel(f"🐾 {story_id.capitalize()} Entities ({len(entities)} total)")
            title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700; padding: 10px;")
            title.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(title)
            
            # Scroll area for entities
            scroll = QtWidgets.QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: none; }")
            
            content = QtWidgets.QWidget()
            grid = QtWidgets.QGridLayout(content)
            grid.setSpacing(10)
            
            rarity_colors = {
                "common": "#9e9e9e", "uncommon": "#4caf50", "rare": "#2196f3",
                "epic": "#9c27b0", "legendary": "#ff9800"
            }
            
            for i, entity in enumerate(entities):
                row, col = i // 3, i % 3
                
                card = QtWidgets.QFrame()
                color = rarity_colors.get(entity.rarity.lower(), "#9e9e9e")
                card.setStyleSheet(f"""
                    QFrame {{
                        background: #2D2D2D;
                        border: 2px solid {color};
                        border-radius: 8px;
                        padding: 8px;
                    }}
                """)
                card.setFixedSize(170, 100)
                
                card_layout = QtWidgets.QVBoxLayout(card)
                card_layout.setSpacing(2)
                card_layout.setContentsMargins(5, 5, 5, 5)
                
                name = QtWidgets.QLabel(entity.name)
                name.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 10px;")
                name.setWordWrap(True)
                card_layout.addWidget(name)
                
                power = QtWidgets.QLabel(f"⚡ {entity.power}")
                power.setStyleSheet("color: #FFD700; font-size: 10px;")
                card_layout.addWidget(power)
                
                rarity_lbl = QtWidgets.QLabel(entity.rarity.upper())
                rarity_lbl.setStyleSheet(f"color: {color}; font-size: 9px;")
                card_layout.addWidget(rarity_lbl)
                
                grid.addWidget(card, row, col)
            
            scroll.setWidget(content)
            layout.addWidget(scroll)
            
            # Close button
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.setStyleSheet("background: #444; color: white; padding: 8px; border-radius: 5px;")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
            self.status_label.setText(f"📖 Viewing {len(entities)} {story_id} entities")
            self.status_label.setStyleSheet("color: #ff9800; padding: 10px;")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _refresh_entity_lock_list(self) -> None:
        """Refresh the entity lock/unlock list for the selected story."""
        try:
            from entitidex import get_entities_for_story
            from gamification import get_entitidex_manager
            
            self.entity_lock_list.clear()
            
            story_id = self.lock_story_combo.currentText()
            entities = get_entities_for_story(story_id)
            
            # Get current collection state
            manager = get_entitidex_manager(self.blocker.adhd_buster)
            collected = manager.progress.collected_entity_ids
            exceptional = manager.progress.exceptional_entities
            
            rarity_colors = {
                "common": "#9e9e9e", "uncommon": "#4caf50", "rare": "#2196f3",
                "epic": "#9c27b0", "legendary": "#ff9800"
            }
            
            for entity in sorted(entities, key=lambda e: (
                ["common", "uncommon", "rare", "epic", "legendary"].index(e.rarity.lower()),
                e.name
            )):
                color = rarity_colors.get(entity.rarity.lower(), "#9e9e9e")
                
                # Normal variant row
                normal_item = QtWidgets.QListWidgetItem()
                normal_item.setData(QtCore.Qt.UserRole, entity.id)
                normal_item.setData(QtCore.Qt.UserRole + 1, False)  # Normal variant
                
                is_normal_unlocked = entity.id in collected
                normal_checkbox = QtWidgets.QCheckBox(f"  {entity.name} ({entity.rarity}) ⚡{entity.power}")
                normal_checkbox.setChecked(is_normal_unlocked)
                normal_checkbox.setStyleSheet(f"color: {color}; font-weight: bold;")
                
                normal_item.setSizeHint(normal_checkbox.sizeHint())
                self.entity_lock_list.addItem(normal_item)
                self.entity_lock_list.setItemWidget(normal_item, normal_checkbox)
                
                # Exceptional variant row
                exceptional_item = QtWidgets.QListWidgetItem()
                exceptional_item.setData(QtCore.Qt.UserRole, entity.id)
                exceptional_item.setData(QtCore.Qt.UserRole + 1, True)  # Exceptional variant
                
                is_exceptional_unlocked = entity.id in exceptional
                exc_name = entity.exceptional_name if entity.exceptional_name else f"{entity.name} ⭐"
                exceptional_checkbox = QtWidgets.QCheckBox(f"  ⭐ {exc_name}")
                exceptional_checkbox.setChecked(is_exceptional_unlocked)
                # Golden gradient style for exceptional
                exceptional_checkbox.setStyleSheet(
                    "color: #FFD700; font-weight: bold; font-style: italic;"
                )
                
                exceptional_item.setSizeHint(exceptional_checkbox.sizeHint())
                self.entity_lock_list.addItem(exceptional_item)
                self.entity_lock_list.setItemWidget(exceptional_item, exceptional_checkbox)
            
            collected_count = sum(1 for e in entities if e.id in collected)
            exceptional_count = sum(1 for e in entities if e.id in exceptional)
            self.status_label.setText(
                f"📋 {story_id}: {collected_count}/{len(entities)} normal, "
                f"{exceptional_count}/{len(entities)} exceptional ⭐"
            )
            self.status_label.setStyleSheet("color: #2196f3; padding: 10px;")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error loading entities: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _unlock_all_entities(self) -> None:
        """Check all entity checkboxes (unlock all)."""
        for i in range(self.entity_lock_list.count()):
            item = self.entity_lock_list.item(i)
            checkbox = self.entity_lock_list.itemWidget(item)
            if checkbox:
                checkbox.setChecked(True)
        self.status_label.setText("✅ All entities marked for unlock - click 'Apply Changes' to save")
        self.status_label.setStyleSheet("color: #4caf50; padding: 10px;")

    def _lock_all_entities(self) -> None:
        """Uncheck all entity checkboxes (lock all)."""
        for i in range(self.entity_lock_list.count()):
            item = self.entity_lock_list.item(i)
            checkbox = self.entity_lock_list.itemWidget(item)
            if checkbox:
                checkbox.setChecked(False)
        self.status_label.setText("🔒 All entities marked for lock - click 'Apply Changes' to save")
        self.status_label.setStyleSheet("color: #f44336; padding: 10px;")

    def _apply_entity_lock_changes(self) -> None:
        """Apply the current checkbox states to the entitidex progress."""
        try:
            from entitidex import get_entity_by_id
            from gamification import get_entitidex_manager, save_entitidex_progress, _generate_exceptional_colors
            
            manager = get_entitidex_manager(self.blocker.adhd_buster)
            hero_power = manager.hero_power
            
            normal_unlocked = 0
            normal_locked = 0
            exceptional_unlocked = 0
            exceptional_locked = 0
            
            for i in range(self.entity_lock_list.count()):
                item = self.entity_lock_list.item(i)
                entity_id = item.data(QtCore.Qt.UserRole)
                is_exceptional = item.data(QtCore.Qt.UserRole + 1)
                checkbox = self.entity_lock_list.itemWidget(item)
                
                if not checkbox:
                    continue
                    
                is_checked = checkbox.isChecked()
                
                if is_exceptional:
                    # Handle exceptional variant
                    was_exceptional = entity_id in manager.progress.exceptional_entities
                    
                    if is_checked and not was_exceptional:
                        # Unlock exceptional - generate colors and record catch
                        exceptional_colors = _generate_exceptional_colors()
                        manager.progress.record_successful_catch(
                            entity_id=entity_id,
                            hero_power=hero_power,
                            probability=1.0,  # Dev forced unlock
                            was_lucky=False,
                            is_exceptional=True,
                            exceptional_colors=exceptional_colors,
                        )
                        # Also record as encountered if not already
                        if not manager.progress.is_encountered(entity_id):
                            manager.progress.record_encounter(entity_id)
                        exceptional_unlocked += 1
                    elif not is_checked and was_exceptional:
                        # Lock exceptional (remove from exceptional_entities)
                        del manager.progress.exceptional_entities[entity_id]
                        exceptional_locked += 1
                else:
                    # Handle normal variant
                    was_collected = entity_id in manager.progress.collected_entity_ids
                    
                    if is_checked and not was_collected:
                        # Unlock normal entity
                        manager.progress.record_successful_catch(
                            entity_id=entity_id,
                            hero_power=hero_power,
                            probability=1.0,  # Dev forced unlock
                            was_lucky=False,
                            is_exceptional=False,
                            exceptional_colors=None,
                        )
                        # Also record as encountered if not already
                        if not manager.progress.is_encountered(entity_id):
                            manager.progress.record_encounter(entity_id)
                        normal_unlocked += 1
                    elif not is_checked and was_collected:
                        # Lock normal entity (remove from collection)
                        manager.progress.collected_entity_ids.discard(entity_id)
                        normal_locked += 1
            
            # Save changes
            save_entitidex_progress(self.blocker.adhd_buster, manager)
            self.blocker.save_config()
            
            # Refresh entitidex tab if available
            main_win = self.window()
            if hasattr(main_win, 'entitidex_tab'):
                main_win.entitidex_tab.refresh()
            
            # Build status message
            parts = []
            if normal_unlocked > 0:
                parts.append(f"{normal_unlocked} normal unlocked")
            if normal_locked > 0:
                parts.append(f"{normal_locked} normal locked")
            if exceptional_unlocked > 0:
                parts.append(f"{exceptional_unlocked} exceptional ⭐ unlocked")
            if exceptional_locked > 0:
                parts.append(f"{exceptional_locked} exceptional ⭐ locked")
            
            if parts:
                self.status_label.setText(f"✅ Applied: {', '.join(parts)}")
            else:
                self.status_label.setText("ℹ️ No changes to apply")
            self.status_label.setStyleSheet("color: #4caf50; padding: 10px;")
            
        except Exception as e:
            self.status_label.setText(f"❌ Error applying changes: {e}")
            self.status_label.setStyleSheet("color: #f44336; padding: 10px;")


class FocusBlockerWindow(QtWidgets.QMainWindow):
    def __init__(self, username: Optional[str] = None) -> None:
        super().__init__()
        self.setWindowTitle(f"Personal Liberty v{APP_VERSION}")
        if username and username != "Default":
            self.setWindowTitle(f"Personal Liberty v{APP_VERSION} - {username}")
        self.resize(900, 700)

        self.blocker = BlockerCore(username=username)
        
        # Initialize centralized game state manager for reactive UI updates (required)
        self.game_state = None
        if GAMIFICATION_AVAILABLE:
            self.game_state = init_game_state(self.blocker)
            # Connect to global UI update signals
            self.game_state.power_changed.connect(self._on_power_changed)
            self.game_state.coins_changed.connect(self._on_coins_changed)
            self.game_state.xp_changed.connect(self._on_xp_changed)
            self.game_state.inventory_changed.connect(self._on_inventory_changed)
            self.game_state.full_refresh_required.connect(self._on_full_refresh_required)

        # Menu bar
        self._create_menu_bar()

        # Make window scrollable with scroll area
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setCentralWidget(scroll_area)
        
        central = QtWidgets.QWidget()
        scroll_area.setWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        # Quick access bar
        quick_bar = QtWidgets.QHBoxLayout()

        # Priorities button
        priorities_btn = QtWidgets.QPushButton("🎯 Priorities")
        priorities_btn.setStyleSheet("font-weight: bold; padding: 6px 12px;")
        priorities_btn.clicked.connect(self._open_priorities)
        quick_bar.addWidget(priorities_btn)

        # ADHD Buster button (only when gamification is available and not disabled)
        if GAMIFICATION_AVAILABLE:
            power = calculate_character_power(self.blocker.adhd_buster)
            self.buster_btn = QtWidgets.QPushButton(f"🦸 ADHD Buster  ⚔ {power}")
            self.buster_btn.setStyleSheet("font-weight: bold; padding: 6px 12px;")
            self.buster_btn.clicked.connect(self._open_adhd_buster)
            # Hide if gamification is disabled
            if not is_gamification_enabled(self.blocker.adhd_buster):
                self.buster_btn.setVisible(False)
            quick_bar.addWidget(self.buster_btn)
            
            # Coin counter
            coins = self.blocker.adhd_buster.get("coins", 0)
            self.coin_label = QtWidgets.QPushButton(f"💰 {coins:,} Coins")
            
            # Build tooltip with lucky bonus info if available
            tooltip = "Your currency for unlocking features and boosters"
            if calculate_total_lucky_bonuses:
                equipped = self.blocker.adhd_buster.get("equipped", {})
                lucky_bonuses = calculate_total_lucky_bonuses(equipped)
                coin_discount = lucky_bonuses.get("coin_discount", 0)
                if coin_discount > 0:
                    effective_discount = min(coin_discount, 90)
                    tooltip += f"\n✨ Gear Bonus: {effective_discount}% off merge costs!"
            
            self.coin_label.setStyleSheet("font-weight: bold; padding: 6px 12px;")
            self.coin_label.setToolTip(tooltip)
            self.coin_label.clicked.connect(self._show_coin_info)
            if not is_gamification_enabled(self.blocker.adhd_buster):
                self.coin_label.setVisible(False)
            quick_bar.addWidget(self.coin_label)

        quick_bar.addStretch()
        self.admin_label = QtWidgets.QLabel()
        quick_bar.addWidget(self.admin_label)
        main_layout.addLayout(quick_bar)

        self._update_admin_label()

        # Daily Timeline (Hybrid View)
        self.timeline_widget = DailyTimelineWidget(self.blocker, self)
        main_layout.addWidget(self.timeline_widget)
        
        # Connect timeline ring clicks to tab navigation (connected after tabs created)
        self._connect_timeline_signals()

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setMovable(True)  # Allow drag-and-drop tab reordering
        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs)

        self.timer_tab = TimerTab(self.blocker, self)
        self.tabs.addTab(self.timer_tab, "⏱ Timer")
        # Connect session signals to refresh stats and manage ADHD tab state
        self.timer_tab.session_complete.connect(self._on_session_complete)
        self.timer_tab.session_started.connect(self._on_session_started)

        self.sites_tab = SitesTab(self.blocker, self)
        self.tabs.addTab(self.sites_tab, "🌐 Sites")

        self.categories_tab = CategoriesTab(self.blocker, self)
        self.tabs.addTab(self.categories_tab, "📁 Categories")

        self.schedule_tab = ScheduleTab(self.blocker, self)
        self.tabs.addTab(self.schedule_tab, "📅 Schedule")

        self.stats_tab = StatsTab(self.blocker, self)
        self.tabs.addTab(self.stats_tab, "📊 Productivity")

        self.settings_tab = SettingsTab(self.blocker, self)
        self.tabs.addTab(self.settings_tab, "⚙ Settings")

        # Weight tracking tab
        self.weight_tab = WeightTab(self.blocker, self)
        self.tabs.addTab(self.weight_tab, "⚖ Weight")
        
        # Activity tracking tab
        self.activity_tab = ActivityTab(self.blocker, self)
        self.tabs.addTab(self.activity_tab, "🏃 Activity")
        
        # Sleep tracking tab
        self.sleep_tab = SleepTab(self.blocker, self)
        self.tabs.addTab(self.sleep_tab, "😴 Sleep")
        
        # Hydration tracking tab
        self.hydration_tab = HydrationTab(self.blocker, self)
        self.tabs.addTab(self.hydration_tab, "💧 Water")

        # Eye Protection tab
        self.eye_tab = EyeProtectionTab(self.blocker)
        self.tabs.addTab(self.eye_tab, "🌬️ Eye & Breath")
        # Connect signal to show item drop dialog if item won
        self.eye_tab.routine_completed.connect(self._on_eye_routine_completed)

        # ADHD Buster tab (gamification)
        if GAMIFICATION_AVAILABLE:
            self.adhd_tab = ADHDBusterTab(self.blocker, self)
            self.tabs.addTab(self.adhd_tab, "🦸 Hero")
            
            # Entitidex tab (entity collection)
            self.entitidex_tab = EntitidexTab(self.blocker, self)
            self.tabs.addTab(self.entitidex_tab, "📖 Entitidex")

        if AI_AVAILABLE:
            self.ai_tab = AITab(self.blocker, self)
            self.tabs.addTab(self.ai_tab, "🧠 AI Insights")

        # Developer tools tab (for testing)
        if GAMIFICATION_AVAILABLE:
            self.dev_tab = DevTab(self.blocker, self)
            self.tabs.addTab(self.dev_tab, "🛠️ Dev")

        self.statusBar().showMessage(f"Personal Liberty v{APP_VERSION}")

        # System Tray setup
        self.tray_icon = None
        self.minimize_to_tray = self.blocker.minimize_to_tray  # Load from config
        
        self._setup_system_tray()
        
        # Health reminder notification timer (checks every minute)
        self._health_reminder_timer = QtCore.QTimer(self)
        self._health_reminder_timer.timeout.connect(self._check_health_reminders)
        self._health_reminder_timer.start(60000)  # Check every 60 seconds

        # Check for crash recovery on startup
        QtCore.QTimer.singleShot(500, self._check_crash_recovery)

        # Check for scheduled blocking
        QtCore.QTimer.singleShot(700, self._check_scheduled_blocking)

        # Show priorities on startup if enabled
        if self.blocker.show_priorities_on_startup:
            QtCore.QTimer.singleShot(600, self._check_priorities_on_startup)

        # Check for daily gear reward (delayed until after onboarding so story is selected)
        if GAMIFICATION_AVAILABLE:
            QtCore.QTimer.singleShot(900, self._show_onboarding_prompt)
            # Pre-load Entitidex tab in background for instant display when user clicks it
            QtCore.QTimer.singleShot(2000, self._preload_entitidex_tab)

    def _preload_entitidex_tab(self) -> None:
        """Pre-load the Entitidex tab UI in background for instant display."""
        if hasattr(self, 'entitidex_tab') and self.entitidex_tab:
            try:
                self.entitidex_tab.preload()
            except Exception as e:
                logger.warning(f"Failed to preload Entitidex tab: {e}")

    def _show_onboarding_prompt(self) -> None:
        """Ask the user how they want to play this session."""
        if not GAMIFICATION_AVAILABLE:
            return

        ensure_hero_structure(self.blocker.adhd_buster)

        # Skip if user already set 'skip_onboarding' flag
        if self.blocker.adhd_buster.get("skip_onboarding", False):
            # Still check for daily reward even if skipping onboarding
            self._check_daily_gear_reward()
            return

        dialog = OnboardingModeDialog(self.blocker, self)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            # Still check for daily reward even if dialog cancelled
            self._check_daily_gear_reward()
            return

        mode, story_id = dialog.get_selection()

        # Save 'Don't ask again' preference
        if dialog.should_skip_next_time():
            self.blocker.adhd_buster["skip_onboarding"] = True

        # Persist any pending flat changes before switching modes
        sync_hero_data(self.blocker.adhd_buster)

        if mode == STORY_MODE_ACTIVE:
            target_story = story_id or self.blocker.adhd_buster.get("active_story", "warrior")
            switch_story(self.blocker.adhd_buster, target_story)
        else:
            set_story_mode(self.blocker.adhd_buster, mode)

        if GAMIFICATION_AVAILABLE and hasattr(self, "buster_btn"):
            # Update button visibility and text based on mode
            enabled = is_gamification_enabled(self.blocker.adhd_buster)
            self.buster_btn.setVisible(enabled)
            if enabled:
                power = calculate_character_power(self.blocker.adhd_buster)
                self.buster_btn.setText(f"🦸 ADHD Buster  ⚔ {power}")

        self.blocker.save_config()
        
        # Now check for daily gear reward AFTER story is selected
        self._check_daily_gear_reward()

    def _check_priorities_on_startup(self) -> None:
        """Check if priorities dialog should be shown on startup."""
        if not self.blocker.show_priorities_on_startup:
            return
        
        # Check if today is a day with any priorities
        today = datetime.now().strftime("%A")
        has_priority_today = False
        
        for priority in self.blocker.priorities:
            title = priority.get("title", "").strip()
            days = priority.get("days", [])
            if title and (not days or today in days):
                has_priority_today = True
                break
        
        # Show dialog if there are priorities for today, or if no priorities set yet
        if has_priority_today or not any(p.get("title", "").strip() for p in self.blocker.priorities):
            self._open_priorities()

    def _check_crash_recovery(self) -> None:
        """Check for orphaned sessions from a previous crash and offer recovery."""
        orphaned = self.blocker.check_orphaned_session()

        if orphaned is None:
            return

        # Format crash info
        if orphaned.get("unknown"):
            crash_info = "An unknown previous session"
        else:
            start_time = orphaned.get("start_time", "unknown")
            mode = orphaned.get("mode", "unknown")
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(start_time)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                time_str = start_time
            crash_info = f"A session started at {time_str} (mode: {mode})"

        # Ask user what to do
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIcon(QtWidgets.QMessageBox.NoIcon)
        msgbox.setWindowTitle("Crash Recovery Detected")
        msgbox.setText(f"⚠️ {crash_info} did not shut down properly.\n\nSome websites may still be blocked.")
        msgbox.setInformativeText("Would you like to remove all blocks and clean up?")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.Yes)
        msgbox.button(QtWidgets.QMessageBox.Yes).setText("Remove Blocks")
        msgbox.button(QtWidgets.QMessageBox.No).setText("Keep Blocks")
        msgbox.button(QtWidgets.QMessageBox.Cancel).setText("Decide Later")
        msgbox.setOption(QtWidgets.QMessageBox.DontUseNativeDialog, True)

        response = msgbox.exec()

        if response == QtWidgets.QMessageBox.Yes:
            success, message = self.blocker.recover_from_crash()
            if success:
                show_info(self, "Recovery Complete", "✅ All blocks have been removed.\n\nYour browser should now be able to access all websites.")
            else:
                show_error(self, "Recovery Failed", f"Could not clean up: {message}\n\nTry using 'Emergency Cleanup' in Settings tab.")
        elif response == QtWidgets.QMessageBox.No:
            self.blocker.clear_session_state()
            show_info(self, "Blocks Retained", "The blocks have been kept.\n\nUse 'Emergency Cleanup' in Settings tab when you want to remove them.")

    def _update_admin_label(self) -> None:
        if hasattr(self, "admin_label"):
            if self.blocker.is_admin():
                self.admin_label.setText("✅ Admin")
                self.admin_label.setStyleSheet("color: green; font-weight: bold;")
                self.admin_label.setToolTip("Running with administrator privileges - website blocking will work.")
            else:
                self.admin_label.setText("⚠ Not Admin")
                self.admin_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
                self.admin_label.setToolTip(
                    "Not running as administrator - website blocking won't work!\n\n"
                    "Right-click the app and select 'Run as administrator',\n"
                    "or use the 'run_as_admin.bat' script."
                )
    
    def _check_health_reminders(self) -> None:
        """Check if any health reminder notifications should be shown."""
        from datetime import datetime
        now = datetime.now()
        
        # Check Eye & Breath reminder
        if getattr(self.blocker, 'eye_reminder_enabled', False):
            interval = getattr(self.blocker, 'eye_reminder_interval', 60)
            last_time_str = getattr(self.blocker, 'eye_last_reminder_time', None)
            
            should_remind = False
            if not last_time_str:
                should_remind = True
            else:
                try:
                    last_time = datetime.fromisoformat(last_time_str)
                    elapsed = (now - last_time).total_seconds() / 60
                    if elapsed >= interval:
                        should_remind = True
                except (ValueError, TypeError):
                    should_remind = True
            
            if should_remind:
                self.blocker.eye_last_reminder_time = now.isoformat()
                self.blocker.save_config()
                if self.tray_icon:
                    self.tray_icon.showMessage(
                        "👁️ Eye & Breath Reminder",
                        "Time for an eye routine! Rest your eyes with blinks and far gazing.",
                        QtWidgets.QSystemTrayIcon.Information,
                        5000
                    )
        
        # Check Water/Hydration reminder
        if getattr(self.blocker, 'water_reminder_enabled', False):
            interval = getattr(self.blocker, 'water_reminder_interval', 60)
            last_time_str = getattr(self.blocker, 'water_last_reminder_time', None)
            
            should_remind = False
            if not last_time_str:
                should_remind = True
            else:
                try:
                    last_time = datetime.fromisoformat(last_time_str)
                    elapsed = (now - last_time).total_seconds() / 60
                    if elapsed >= interval:
                        should_remind = True
                except (ValueError, TypeError):
                    should_remind = True
            
            if should_remind:
                self.blocker.water_last_reminder_time = now.isoformat()
                self.blocker.save_config()
                if self.tray_icon:
                    self.tray_icon.showMessage(
                        "💧 Hydration Reminder",
                        "Time to drink some water! Stay hydrated for better focus.",
                        QtWidgets.QSystemTrayIcon.Information,
                        5000
                    )
    
    def _update_coin_display(self) -> None:
        """Update the coin counter in the toolbar."""
        if GAMIFICATION_AVAILABLE and hasattr(self, 'coin_label'):
            coins = self.blocker.adhd_buster.get("coins", 0)
            self.coin_label.setText(f"💰 {coins:,} Coins")
    
    # === GameState Signal Handlers (Reactive UI Updates) ===
    
    def _on_power_changed(self, new_power: int) -> None:
        """Handle power change signal - update power display in toolbar."""
        if hasattr(self, 'buster_btn'):
            self.buster_btn.setText(f"🦸 ADHD Buster  ⚔ {new_power}")
    
    def _on_coins_changed(self, new_coins: int) -> None:
        """Handle coins change signal - update coin display in toolbar."""
        if hasattr(self, 'coin_label'):
            self.coin_label.setText(f"💰 {new_coins:,} Coins")

    def _on_xp_changed(self, new_xp: int, new_level: int) -> None:
        """Handle XP change signal - update timeline XP ring."""
        if hasattr(self, 'timeline_widget'):
            self.timeline_widget.update_data()
    
    def _on_inventory_changed(self) -> None:
        """Handle inventory change signal - refresh ADHD tab if visible."""
        if GAMIFICATION_AVAILABLE and hasattr(self, 'adhd_tab'):
            # Only refresh inventory-specific parts, not full refresh
            if hasattr(self.adhd_tab, '_refresh_inventory'):
                self.adhd_tab._refresh_inventory()
            if hasattr(self.adhd_tab, '_refresh_all_slot_combos'):
                self.adhd_tab._refresh_all_slot_combos()
    
    def _on_full_refresh_required(self) -> None:
        """Handle full refresh signal - comprehensive UI update."""
        if GAMIFICATION_AVAILABLE and hasattr(self, 'adhd_tab'):
            self.adhd_tab.refresh_all()
        self._update_coin_display()
        if hasattr(self, 'buster_btn') and calculate_character_power:
            power = calculate_character_power(self.blocker.adhd_buster)
            self.buster_btn.setText(f"🦸 ADHD Buster  ⚔ {power}")
    
    def _show_coin_info(self) -> None:
        """Show information about the coin economy."""
        coins = self.blocker.adhd_buster.get("coins", 0)
        
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("💰 Coin Economy")
        msg_box.setText(f"<h2>Your Balance: {coins:,} Coins</h2>")
        
        # Build bonus info if lucky gear is equipped
        bonus_info = ""
        if calculate_total_lucky_bonuses:
            equipped = self.blocker.adhd_buster.get("equipped", {})
            lucky_bonuses = calculate_total_lucky_bonuses(equipped)
            coin_discount = lucky_bonuses.get("coin_discount", 0)
            if coin_discount > 0:
                effective_discount = min(coin_discount, 90)
                bonus_info = f"<p style='color: #8b5cf6;'><b>✨ Active Gear Bonus: {effective_discount}% off merge costs!</b></p>"
        
        msg_box.setInformativeText(
            f"{bonus_info}"
            "<p><b>How to Earn Coins:</b></p>"
            "<ul>"
            "<li><b>Focus Sessions:</b> 10 Coins per hour</li>"
            "<li><b>Strategic Priority:</b> 25 Coins per hour (2.5x bonus!)</li>"
            "<li><b>Complete Priority:</b> 100 Coins</li>"
            "<li><b>Streak Bonuses:</b> Up to 100 Coins/day at 30+ day streaks</li>"
            "<li><b>✨ Lucky Gear:</b> Discount on merge costs from equipped items with coin_discount!</li>"
            "</ul>"
            "<p><b>What You Can Buy:</b></p>"
            "<ul>"
            "<li><b>Streak Freeze:</b> 2,000 Coins - Skip a day without losing your streak</li>"
            "<li><b>Reward Reroll:</b> 150 Coins - Reroll your last item drop</li>"
            "<li><b>Rarity Incense:</b> 300 Coins - +10% luck for next session</li>"
            "<li><b>New Stories:</b> 1,000 Coins - Unlock new character themes</li>"
            "<li><b>App Features:</b> 500-1,000 Coins - Advanced analytics, themes, etc.</li>"
            "</ul>"
            "<p><i>💡 Tip: Mark one priority as 'Strategic' to maximize coin earnings!</i></p>"
            "<p><i>⚠️ Note: Marketplace features coming soon!</i></p>"
        )
        msg_box.setIcon(QtWidgets.QMessageBox.NoIcon)
        msg_box.setOption(QtWidgets.QMessageBox.DontUseNativeDialog, True)
        msg_box.exec()

    def _check_scheduled_blocking(self) -> None:
        """Check if we should be blocking based on schedule."""
        if self.blocker.is_scheduled_block_time() and not self.blocker.is_blocking:
            result = show_question(
                self, "Scheduled Block",
                "You have a blocking schedule active now.\nStart blocking?"
            )
            if result == QtWidgets.QMessageBox.Yes:
                self.blocker.mode = BlockMode.SCHEDULED
                self.blocker.block_sites(duration_seconds=8 * 60 * 60)
                self.timer_tab._update_timer_display()

        # Check again in 60 seconds
        QtCore.QTimer.singleShot(60000, self._check_scheduled_blocking)

    def _check_daily_gear_reward(self) -> None:
        """Check if user should receive a daily gear reward.
        
        On first app start: Always award gear.
        On subsequent starts: 10% chance per day.
        Gear is one tier higher than current equipped tier.
        """
        if not GAMIFICATION_AVAILABLE:
            return
        # Skip if gamification mode is disabled
        if not is_gamification_enabled(self.blocker.adhd_buster):
            return
        
        today = datetime.now().strftime("%Y-%m-%d")
        last_reward_date = self.blocker.adhd_buster.get("last_daily_reward_date", "")
        first_launch = self.blocker.adhd_buster.get("first_launch_complete", False)
        
        # Already received reward today
        if last_reward_date == today:
            return
        
        # Determine if we should give reward
        should_reward = False
        reward_reason = ""
        
        if not first_launch:
            # First time ever - always reward
            should_reward = True
            reward_reason = "🎁 Welcome Gift!"
            self.blocker.adhd_buster["first_launch_complete"] = True
        else:
            # Subsequent launches - 10% daily chance
            import random
            if random.random() < 0.10:
                should_reward = True
                reward_reason = "🎲 Lucky Daily Drop!"
        
        if should_reward:
            # Set reward date FIRST to prevent race conditions (rapid open/close)
            self.blocker.adhd_buster["last_daily_reward_date"] = today
            
            # Get active story for themed item generation
            active_story = self.blocker.adhd_buster.get("active_story", "warrior")
            
            # Generate boosted item with correct story theme
            item = generate_daily_reward_item(self.blocker.adhd_buster, story_id=active_story)
            
            # Ensure item has all required fields
            if "obtained_at" not in item:
                item["obtained_at"] = datetime.now().isoformat()
            
            # Use GameState manager for reactive updates
            game_state = getattr(self, 'game_state', None)
            if not game_state:
                logger.error("GameStateManager not available - cannot award daily reward")
                return
            
            # Use batch award - handles inventory, auto-equip, save, and signals
            game_state.award_items_batch([item], coins=0, auto_equip=False, source="daily_reward")
            
            # Sync changes to active hero
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
                self.blocker.save_config()
            
            # Show reward dialog with themed slot name
            current_tier = get_current_tier(self.blocker.adhd_buster)
            boosted_tier = get_boosted_rarity(current_tier)
            slot_display = get_slot_display_name(item['slot'], active_story) if get_slot_display_name else item['slot']
            
            show_info(
                self,
                f"🎁 {reward_reason}",
                f"You received a special gear item!\n\n"
                f"✨ {item['name']}\n"
                f"⚔ Power: +{item['power']}\n"
                f"🏆 Rarity: {item['rarity']}\n"
                f"📍 Slot: {slot_display}\n\n"
                f"(Based on your current tier: {current_tier} → boosted to {boosted_tier})\n\n"
                f"Check your ADHD Buster inventory to equip it!"
            )

    def _setup_system_tray(self) -> None:
        """Setup system tray icon if available."""
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Personal Liberty - Focus Blocker")

        # Create tray icon (green circle with check)
        self._update_tray_icon(blocking=False)

        # Create tray menu
        tray_menu = QtWidgets.QMenu()
        
        self.tray_status_action = tray_menu.addAction("Ready")
        self.tray_status_action.setEnabled(False)
        tray_menu.addSeparator()
        
        show_action = tray_menu.addAction("Show Window")
        show_action.triggered.connect(self._restore_from_tray)
        
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self._quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

        # Timer to update tray status
        self.tray_update_timer = QtCore.QTimer(self)
        self.tray_update_timer.setInterval(1000)
        self.tray_update_timer.timeout.connect(self._update_tray_status)

        # Show tray icon immediately and start update timer
        self.tray_icon.show()
        self.tray_update_timer.start()

    def _update_tray_icon(self, blocking: bool = False) -> None:
        """Update the tray icon image."""
        if not self.tray_icon:
            return

        size = 64
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if blocking:
            # Red circle with lock when blocking
            painter.setBrush(QtGui.QColor("#e74c3c"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#c0392b"), 2))
            painter.drawEllipse(4, 4, size - 8, size - 8)
            # Lock symbol
            painter.setBrush(QtGui.QColor("white"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(20, 30, 24, 20)
            painter.setPen(QtGui.QPen(QtGui.QColor("white"), 4))
            painter.drawArc(24, 18, 16, 16, 0, 180 * 16)
        else:
            # Green circle with check when ready
            painter.setBrush(QtGui.QColor("#2ecc71"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#27ae60"), 2))
            painter.drawEllipse(4, 4, size - 8, size - 8)
            # Check mark
            painter.setPen(QtGui.QPen(QtGui.QColor("white"), 4))
            painter.drawLine(20, 32, 28, 42)
            painter.drawLine(28, 42, 44, 22)

        painter.end()

        self.tray_icon.setIcon(QtGui.QIcon(pixmap))

    def _update_tray_status(self) -> None:
        """Update tray icon status text."""
        if not self.tray_icon:
            return

        if self.timer_tab.timer_running:
            remaining = self.timer_tab.remaining_seconds
            h = remaining // 3600
            m = (remaining % 3600) // 60
            s = remaining % 60
            self.tray_status_action.setText(f"🔒 Blocking - {h:02d}:{m:02d}:{s:02d}")
            self.tray_icon.setToolTip(f"Personal Liberty - Blocking ({h:02d}:{m:02d}:{s:02d})")
        else:
            self.tray_status_action.setText("Ready")
            self.tray_icon.setToolTip("Personal Liberty - Ready")

    def _on_tray_activated(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation (double-click to restore)."""
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self._restore_from_tray()

    def _restore_from_tray(self) -> None:
        """Restore window from system tray."""
        self.showNormal()  # Ensures window is not minimized
        self.raise_()
        self.activateWindow()
        # Tray icon stays visible and timer keeps running

    def _quit_application(self) -> None:
        """Force quit the application (bypasses minimize to tray)."""
        self._force_quit = True
        # Stop tray icon and update timer
        if self.tray_icon:
            self.tray_icon.hide()
        if hasattr(self, 'tray_update_timer') and self.tray_update_timer:
            self.tray_update_timer.stop()
        # Force close the window and quit the app
        self.close()
        QtWidgets.QApplication.instance().quit()

    def changeEvent(self, event: QtCore.QEvent) -> None:
        """Handle window state changes."""
        # Note: We no longer hide to tray on minimize - only on close
        # This keeps minimize behavior standard (to taskbar)
        super().changeEvent(event)

    def _hide_to_tray(self) -> None:
        """Hide window to system tray."""
        if self.tray_icon:
            self.hide()
            self.tray_icon.showMessage(
                "Personal Liberty",
                "Still running in system tray. Double-click to restore, or right-click → Exit to quit.",
                QtWidgets.QSystemTrayIcon.Information,
                2000
            )

    def _create_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")
        priorities_action = file_menu.addAction("🎯 Priorities")
        priorities_action.triggered.connect(self._open_priorities)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self._quit_application)

        # Tools menu
        tools_menu = menu_bar.addMenu("&Tools")
        if GAMIFICATION_AVAILABLE:
            buster_action = tools_menu.addAction("🦸 ADHD Buster")
            buster_action.triggered.connect(self._open_adhd_buster)
            diary_action = tools_menu.addAction("📖 Adventure Diary")
            diary_action.triggered.connect(self._open_diary)
        cleanup_action = tools_menu.addAction("🧹 Emergency Cleanup")
        cleanup_action.triggered.connect(self._emergency_cleanup)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about)

    def _open_priorities(self) -> None:
        dialog = PrioritiesDialog(self.blocker, on_start_callback=self._start_priority_session, parent=self)
        dialog.exec()

    def _start_priority_session(self, priority_title: str) -> None:
        # Find if this priority is strategic
        is_strategic = False
        for priority in self.blocker.priorities:
            if priority.get("title", "").strip() == priority_title:
                is_strategic = priority.get("strategic", False)
                break
        
        # Store priority context in timer tab
        self.timer_tab.session_priority_title = priority_title
        self.timer_tab.session_is_strategic = is_strategic
        self.timer_tab._preserve_strategic_flag = True  # Prevent reset in _start_session
        
        strategic_msg = "\n\n💰 This is a STRATEGIC priority!\nYou'll earn 2.5x Coins (25/hour instead of 10/hour)" if is_strategic else ""
        
        self.tabs.setCurrentWidget(self.timer_tab)
        show_info(self, "Priority Session", 
                                   f"Starting focus session for:\n\n\"{priority_title}\"{strategic_msg}\n\n"
                                   "Set your desired duration and click Start Focus!")

    def _open_adhd_buster(self) -> None:
        """Switch to the ADHD Buster tab."""
        if not GAMIFICATION_AVAILABLE or not hasattr(self, 'adhd_tab'):
            show_warning(
                self, "Unavailable",
                "ADHD Buster features are not available."
            )
            return
        
        # Find the index of the ADHD tab and switch to it
        tab_index = self.tabs.indexOf(self.adhd_tab)
        if tab_index >= 0:
            self.tabs.setCurrentIndex(tab_index)
            # Refresh the tab and set session state
            self.adhd_tab.set_session_active(self.timer_tab.timer_running)
            self.adhd_tab.refresh_all()
        
        # Update button text
        if hasattr(self, "buster_btn"):
            enabled = is_gamification_enabled(self.blocker.adhd_buster)
            self.buster_btn.setVisible(enabled)
            if enabled:
                power = calculate_character_power(self.blocker.adhd_buster)
                self.buster_btn.setText(f"🦸 ADHD Buster  ⚔ {power}")

    def refresh_adhd_tab(self) -> None:
        """Refresh ADHD Buster tab if it exists."""
        if GAMIFICATION_AVAILABLE and hasattr(self, 'adhd_tab'):
            self.adhd_tab.refresh_all()

    def _open_diary(self) -> None:
        dialog = DiaryDialog(self.blocker, self)
        dialog.exec()

    def _emergency_cleanup(self) -> None:
        """Emergency cleanup with enhanced confirmation dialog."""
        # Extra warning for strict/hardcore modes
        mode = getattr(self.blocker, 'mode', None)
        if mode in (BlockMode.STRICT, BlockMode.HARDCORE) and self.blocker.is_blocking:
            reply = show_question(
                self, "⚠️ Active Session Detected",
                f"You have an active {mode.upper()} session!\n\n"
                "Emergency cleanup will bypass the protection you set.\n"
                "This defeats the purpose of using a strict mode.\n\n"
                "Are you SURE you want to proceed?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
        
        # Gather impact data
        impact_data = {
            "items_count": 0,
            "power_lost": 0,
            "progress_percent": 0,
            "coins_refund": 0,
            "items_affected": []
        }
        
        # Calculate impact from inventory
        if GAMIFICATION_AVAILABLE:
            inventory = self.blocker.adhd_buster.get("inventory", [])
            impact_data["items_count"] = len(inventory)
            impact_data["power_lost"] = self.blocker.adhd_buster.get("total_power", 0)
            impact_data["items_affected"] = inventory[:20]  # Show first 20
            
            # Calculate progress percentage
            total_xp = self.blocker.adhd_buster.get("total_xp", 0)
            if total_xp > 0:
                impact_data["progress_percent"] = min(100, int((total_xp / 10000) * 100))
        
        # Show enhanced confirmation dialog
        confirmed = show_emergency_cleanup_dialog("emergency_cleanup", impact_data, self)
        
        if confirmed:
            success, message = self.blocker.emergency_cleanup()
            if success:
                show_info(self, "Cleanup Complete", message)
            else:
                show_error(self, "Cleanup Failed", message)

    def _show_about(self) -> None:
        QtWidgets.QMessageBox.about(self, "About Personal Liberty",
            f"<b>Personal Liberty v{APP_VERSION}</b><br><br>"
            "A focus and productivity tool for Windows.<br><br>"
            "Built with PySide6 (Qt for Python).")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close - minimize to tray if enabled, else prompt/close."""
        # If minimize_to_tray is enabled and tray is available, hide to tray instead of closing
        if self.minimize_to_tray and self.tray_icon and not getattr(self, '_force_quit', False):
            event.ignore()
            self._hide_to_tray()
            return

        # Stop tray icon and update timer
        if self.tray_icon:
            self.tray_icon.hide()
        if hasattr(self, 'tray_update_timer') and self.tray_update_timer:
            self.tray_update_timer.stop()
        if hasattr(self, '_health_reminder_timer') and self._health_reminder_timer:
            self._health_reminder_timer.stop()

        if self.timer_tab.timer_running:
            # For Hardcore mode, require solving the challenge to exit
            if self.timer_tab.blocker.mode == BlockMode.HARDCORE:
                reply = show_question(
                    self,
                    "🔥 Hardcore Mode Active",
                    "A Hardcore session is running!\n\n"
                    "You must solve the math challenge to exit.\n\nContinue?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                if reply == QtWidgets.QMessageBox.Yes:
                    dialog = HardcoreChallengeDialog(self)
                    if dialog.exec() == QtWidgets.QDialog.Accepted:
                        self.timer_tab._force_stop_session()
                        event.accept()
                        QtWidgets.QApplication.instance().quit()
                    else:
                        event.ignore()
                else:
                    event.ignore()
                return
            
            reply = show_question(
                self,
                "Confirm Exit",
                "A focus session is still running!\n\nStop the session and exit?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self.timer_tab._force_stop_session()
                event.accept()
                QtWidgets.QApplication.instance().quit()
            else:
                event.ignore()
        else:
            event.accept()
            QtWidgets.QApplication.instance().quit()

    def show_ai_session_complete(self, session_duration: int) -> None:
        """Show session complete dialog with break suggestions."""
        dialog = AISessionCompleteDialog(self.blocker, session_duration, self)
        dialog.exec()

    def _on_eye_routine_completed(self, item: dict) -> None:
        """Handle completion of eye protection routine."""
        # If an item was won (dict is not empty), show the drop dialog
        if item:
            dialog = EnhancedItemDropDialog(item, self)
            dialog.exec()
            
            # Refresh inventory UI if it exists
            if hasattr(self, 'adhd_tab'):
                self.adhd_tab.refresh_inventory()
                self._update_coin_display()

    def _on_session_complete(self, elapsed_seconds: int) -> None:
        """Handle session completion - refresh stats and related UI."""
        # Reload stats from file to ensure we have latest data
        self.blocker.load_stats()
        
        # Update coin display if gamification is available
        if GAMIFICATION_AVAILABLE:
            self._update_coin_display()
        
        # Refresh the stats tab to show updated focus time
        if hasattr(self, 'stats_tab'):
            self.stats_tab.refresh()
        
        # Refresh AI tab if available
        if AI_AVAILABLE and hasattr(self, 'ai_tab'):
            self.ai_tab._refresh_data()
        
        # Refresh Timeline
        if hasattr(self, 'timeline_widget'):
            self.timeline_widget.update_data()
        
        # Re-enable all tabs after session ends
        self._set_tabs_enabled(True)
        
        # Refresh ADHD Buster tab after session ends
        if GAMIFICATION_AVAILABLE and hasattr(self, 'adhd_tab'):
            self.adhd_tab.set_session_active(False)
            self.adhd_tab.refresh_all()

    def _on_session_started(self) -> None:
        """Handle session start - disable non-essential tabs to minimize distraction."""
        self._set_tabs_enabled(False)
        if GAMIFICATION_AVAILABLE and hasattr(self, 'adhd_tab'):
            self.adhd_tab.set_session_active(True)
    
    def _set_tabs_enabled(self, enabled: bool) -> None:
        """Enable or disable non-essential tabs during focus sessions.
        
        Only the Timer tab (index 0) remains enabled during sessions,
        as it's needed to stop the session or view remaining time.
        """
        for i in range(self.tabs.count()):
            # Keep Timer tab (index 0) always enabled
            if i == 0:
                continue
            self.tabs.setTabEnabled(i, enabled)

    def _connect_timeline_signals(self) -> None:
        """Connect timeline ring widget clicks to tab navigation.
        
        Called after tabs are created to enable navigation:
        - Water ring → Water tab
        - Chapter ring → Hero tab
        - Focus ring → Timer tab
        - XP ring → Hero tab
        """
        # Use a deferred connection since tabs aren't created yet when this is called
        QtCore.QTimer.singleShot(0, self._do_connect_timeline_signals)
    
    def _do_connect_timeline_signals(self) -> None:
        """Actually connect the timeline signals after tabs exist."""
        if not hasattr(self, 'timeline_widget'):
            return
            
        self.timeline_widget.water_clicked.connect(self._go_to_water_tab)
        self.timeline_widget.chapter_clicked.connect(self._go_to_hero_tab)
        self.timeline_widget.focus_clicked.connect(self._go_to_timer_tab)
        self.timeline_widget.xp_clicked.connect(self._go_to_hero_tab)
    
    def _go_to_water_tab(self) -> None:
        """Navigate to the Water tab."""
        if hasattr(self, 'hydration_tab'):
            index = self.tabs.indexOf(self.hydration_tab)
            if index >= 0:
                self.tabs.setCurrentIndex(index)
    
    def _go_to_timer_tab(self) -> None:
        """Navigate to the Timer tab."""
        if hasattr(self, 'timer_tab'):
            index = self.tabs.indexOf(self.timer_tab)
            if index >= 0:
                self.tabs.setCurrentIndex(index)
    
    def _go_to_hero_tab(self) -> None:
        """Navigate to the Hero tab."""
        if GAMIFICATION_AVAILABLE and hasattr(self, 'adhd_tab'):
            index = self.tabs.indexOf(self.adhd_tab)
            if index >= 0:
                self.tabs.setCurrentIndex(index)

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab changes - refresh data for the newly selected tab."""
        widget = self.tabs.widget(index)
        
        # Refresh stats tab when switched to
        if hasattr(self, 'stats_tab') and widget == self.stats_tab:
            self.blocker.load_stats()
            self.stats_tab.refresh()
        
        # Refresh AI tab when switched to
        elif AI_AVAILABLE and hasattr(self, 'ai_tab') and widget == self.ai_tab:
            self.ai_tab._refresh_data()
        
        # Refresh ADHD Buster tab when switched to
        elif GAMIFICATION_AVAILABLE and hasattr(self, 'adhd_tab') and widget == self.adhd_tab:
            self.adhd_tab.set_session_active(self.timer_tab.timer_running)
            self.adhd_tab.refresh_all()


def check_single_instance():
    """Check if another instance is already running using a Windows mutex.
    Returns the mutex handle if this is the first instance, None otherwise.
    """
    if platform.system() != "Windows":
        return True  # No mutex on non-Windows
    
    try:
        import ctypes
        # Try to create a named mutex
        mutex = ctypes.windll.kernel32.CreateMutexW(None, True, MUTEX_NAME)
        last_error = ctypes.windll.kernel32.GetLastError()
        
        # ERROR_ALREADY_EXISTS = 183
        if last_error == 183:
            # Another instance is running
            ctypes.windll.kernel32.CloseHandle(mutex)
            return None
        
        # This is the first instance, return the mutex handle
        return mutex
    except Exception:
        # If we can't create a mutex, allow running anyway
        return True


def find_and_activate_existing_window():
    """Try to find and activate an existing Personal Liberty window."""
    if platform.system() != "Windows":
        return False
    
    try:
        import ctypes
        from ctypes import wintypes
        
        user32 = ctypes.windll.user32
        
        # Find window by title
        hwnd = user32.FindWindowW(None, "Personal Liberty")
        if hwnd:
            # Constants
            SW_RESTORE = 9
            SW_SHOW = 5
            
            # Restore if minimized
            user32.ShowWindow(hwnd, SW_RESTORE)
            # Bring to foreground
            user32.SetForegroundWindow(hwnd)
            return True
        
        # Try partial match with version
        EnumWindows = user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        GetWindowTextW = user32.GetWindowTextW
        GetWindowTextLengthW = user32.GetWindowTextLengthW
        
        found_hwnd = [None]
        
        def enum_callback(hwnd, lParam):
            length = GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                if "Personal Liberty" in title:
                    found_hwnd[0] = hwnd
                    return False  # Stop enumeration
            return True
        
        EnumWindows(EnumWindowsProc(enum_callback), 0)
        
        if found_hwnd[0]:
            user32.ShowWindow(found_hwnd[0], 9)  # SW_RESTORE
            user32.SetForegroundWindow(found_hwnd[0])
            return True
        
        return False
    except Exception:
        return False


def kill_existing_instances():
    """Kill all existing PersonalLiberty processes except the current one."""
    if platform.system() != "Windows":
        return False
    
    try:
        import subprocess
        current_pid = os.getpid()
        
        # Use taskkill to terminate PersonalLiberty.exe processes
        result = subprocess.run(
            ["taskkill", "/F", "/IM", "PersonalLiberty.exe"],
            capture_output=True,
            text=True
        )
        
        # Give processes time to terminate
        import time
        time.sleep(1)
        
        return True
    except Exception:
        return False


def main() -> None:
    # Set application attributes before creating QApplication
    QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(
        QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create app early so we can show splash
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Personal Liberty")
    app.setOrganizationName("PersonalLiberty")
    app.setApplicationVersion(APP_VERSION)
    
    # Check for single instance first
    mutex_handle = check_single_instance()
    if mutex_handle is None:
        # Another instance is running - ask user what to do
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle("Already Running")
        msg_box.setText("Personal Liberty is already running.")
        msg_box.setInformativeText("What would you like to do?")
        msg_box.setIcon(QtWidgets.QMessageBox.NoIcon)
        msg_box.setOption(QtWidgets.QMessageBox.DontUseNativeDialog, True)
        
        switch_btn = msg_box.addButton("Switch to Running App", QtWidgets.QMessageBox.AcceptRole)
        kill_btn = msg_box.addButton("Kill && Restart", QtWidgets.QMessageBox.DestructiveRole)
        cancel_btn = msg_box.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
        
        msg_box.exec()
        clicked = msg_box.clickedButton()
        
        if clicked == switch_btn:
            # Try to activate existing window
            if find_and_activate_existing_window():
                sys.exit(0)
            else:
                show_warning(
                    None, "Not Found",
                    "Could not find the running window.\n\n"
                    "The app may be minimized to system tray.\n"
                    "Check your system tray icons."
                )
                sys.exit(0)
        elif clicked == kill_btn:
            # Kill existing instances and continue
            kill_existing_instances()
            # Try to acquire mutex again
            mutex_handle = check_single_instance()
            if mutex_handle is None:
                show_error(
                    None, "Failed",
                    "Could not terminate the existing instance.\n\n"
                    "Please close it manually from Task Manager."
                )
                sys.exit(1)
        else:
            sys.exit(0)
    
    # Parse command-line arguments
    start_minimized = "--minimized" in sys.argv or "--tray" in sys.argv
    
    # Show splash screen during loading
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    # Load heavy modules with splash feedback
    load_heavy_modules(splash)
    
    # User Selection Logic
    try:
        from core_logic import APP_DIR
        from user_manager import UserManager
        from user_selection_dialog import UserSelectionDialog
        
        user_manager = UserManager(APP_DIR)
        user_manager.migrate_if_needed()
        
        # Check for auto-login
        last_user = user_manager.get_last_user()
        selected_user = None

        if last_user:
            # Validate that auto-login user still exists with proper directory
            if user_manager.user_exists(last_user):
                try:
                    user_dir = user_manager.get_user_dir(last_user)
                    if user_dir.exists() and user_dir.is_dir():
                        selected_user = last_user
                        splash.set_status(f"Auto-loading profile: {selected_user}...")
                    else:
                        # Directory was deleted - clear invalid last_user
                        user_manager.clear_last_user()
                        last_user = None
                except (ValueError, OSError):
                    # Invalid user - clear and prompt
                    user_manager.clear_last_user()
                    last_user = None
            else:
                # User no longer exists - clear invalid last_user
                user_manager.clear_last_user()
                last_user = None
        
        if not selected_user:
            splash.hide() # Hide splash for dialog
            
            selection_dialog = UserSelectionDialog(user_manager)
            if selection_dialog.exec() == QtWidgets.QDialog.Accepted:
                selected_user = selection_dialog.selected_user
                if selected_user:  # Validate selection is not None
                    user_manager.save_last_user(selected_user)
                    splash.show()
                    splash.set_status(f"Loading profile: {selected_user}...")
                else:
                    show_error(None, "Selection Error", "No user profile was selected.")
                    sys.exit(1)
            else:
                sys.exit(0)
    except ImportError as e:
        show_error(None, "Startup Error", f"Failed to import required modules:\n{e}")
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        import traceback
        show_error(
            None, 
            "Unexpected Error", 
            f"An unexpected error occurred during user selection:\n{e}\n\nPlease report this issue."
        )
        traceback.print_exc()
        sys.exit(1)
    
    splash.set_status("Creating main window...")
    
    window = FocusBlockerWindow(username=selected_user)
    
    # Close splash and show main window
    splash.close()
    app.processEvents()  # Ensure splash is fully closed before showing window
    
    if start_minimized and window.tray_icon:
        # Start minimized to system tray
        window.hide()
        window.tray_icon.showMessage(
            "Personal Liberty",
            "Running in system tray. Double-click to open.",
            QtWidgets.QSystemTrayIcon.Information,
            3000
        )
    else:
        window.show()
        window.raise_()
        window.activateWindow()
    
    exit_code = app.exec()
    
    # Release the mutex on exit
    if mutex_handle and mutex_handle is not True:
        try:
            import ctypes
            ctypes.windll.kernel32.ReleaseMutex(mutex_handle)
            ctypes.windll.kernel32.CloseHandle(mutex_handle)
        except Exception:
            pass
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
