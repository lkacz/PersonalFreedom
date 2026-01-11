import sys
import json
import random
import platform
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

try:
    from __version__ import __version__ as APP_VERSION
except ImportError:
    APP_VERSION = "3.1.4"

# Hide console window on Windows
if platform.system() == "Windows":
    import ctypes
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

from PySide6 import QtCore, QtGui, QtWidgets


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
    )
    BlockerCore = _BlockerCore
    BlockMode = _BlockMode
    SITE_CATEGORIES = _SITE_CATEGORIES
    AI_AVAILABLE = _AI_AVAILABLE
    GOALS_PATH = _GOALS_PATH
    STATS_PATH = _STATS_PATH
    BYPASS_LOGGER_AVAILABLE = _BYPASS_LOGGER_AVAILABLE
    
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
                # All problems solved!
                self.feedback_label.setText("✅ Correct! Session will stop...")
                self.feedback_label.setStyleSheet("font-size: 14px; color: #28a745; min-height: 30px;")
                QtCore.QTimer.singleShot(500, self.accept)
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

        self.story_combo = QtWidgets.QComboBox()
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
        
        # Pomodoro state
        self.pomodoro_is_break = False
        self.pomodoro_session_count = 0
        self.pomodoro_total_work_time = 0
        
        # Priority check-in tracking
        self.last_checkin_time: Optional[float] = None

        self._build_ui()
        self._connect_signals()

        # QTimer for ticking each second
        self.qt_timer = QtCore.QTimer(self)
        self.qt_timer.setInterval(1000)
        self.qt_timer.timeout.connect(self._on_tick)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        # Timer display
        self.timer_label = QtWidgets.QLabel("00:00:00")
        self.timer_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_label.setStyleSheet("font: 700 36px 'Consolas';")
        layout.addWidget(self.timer_label)

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

        # Duration inputs
        duration_box = QtWidgets.QGroupBox("Duration")
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

        # Presets
        preset_box = QtWidgets.QGroupBox("Presets")
        preset_layout = QtWidgets.QHBoxLayout(preset_box)
        presets = [("25m", 25), ("45m", 45), ("1h", 60), ("2h", 120), ("4h", 240)]
        for label, minutes in presets:
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(lambda _=False, m=minutes: self._set_preset(m))
            preset_layout.addWidget(btn)
        layout.addWidget(preset_box)

        # Notification option
        self.notify_checkbox = QtWidgets.QCheckBox("🔔 Notify me when session ends")
        self.notify_checkbox.setChecked(getattr(self.blocker, 'notify_on_complete', True))
        self.notify_checkbox.setToolTip("Show a desktop notification when your focus session completes")
        layout.addWidget(self.notify_checkbox)

        # Start/Stop buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("▶ Start Focus")
        self.stop_btn = QtWidgets.QPushButton("⬛ Stop")
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Status label
        self.status_label = QtWidgets.QLabel("Ready to focus")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Rewards info section
        rewards_group = QtWidgets.QGroupBox("🎁 Rewards Info")
        rewards_layout = QtWidgets.QVBoxLayout(rewards_group)
        rewards_info = QtWidgets.QLabel(
            "<b>How it works:</b> Complete a focus session to earn 1 random item. Longer sessions shift the rarity distribution higher.<br>"
            "<table style='font-size:10px; color:#888888; margin-top:5px;'>"
            "<tr><th>Session</th><th>Common</th><th>Uncommon</th><th>Rare</th><th>Epic</th><th>Legendary</th><th>Bonus Item</th></tr>"
            "<tr><td>&lt;30min</td><td>50%</td><td>30%</td><td>15%</td><td>4%</td><td>1%</td><td>-</td></tr>"
            "<tr><td>30min</td><td>75%</td><td>20%</td><td>5%</td><td>-</td><td>-</td><td>-</td></tr>"
            "<tr><td>1hr</td><td>25%</td><td>50%</td><td>20%</td><td>5%</td><td>-</td><td>-</td></tr>"
            "<tr><td>2hr</td><td>5%</td><td>20%</td><td>50%</td><td>20%</td><td>5%</td><td>-</td></tr>"
            "<tr><td>3hr</td><td>-</td><td>5%</td><td>20%</td><td>50%</td><td>25%</td><td>-</td></tr>"
            "<tr><td>4hr</td><td>-</td><td>-</td><td>5%</td><td>20%</td><td>75%</td><td>-</td></tr>"
            "<tr><td>5hr</td><td>-</td><td>-</td><td>-</td><td>5%</td><td>95%</td><td>-</td></tr>"
            "<tr><td>6hr+</td><td>-</td><td>-</td><td>-</td><td>-</td><td>100%</td><td>-</td></tr>"
            "<tr><td>7hr+</td><td>-</td><td>-</td><td>-</td><td>-</td><td>100%</td><td>+20% chance</td></tr>"
            "<tr><td>8hr+</td><td>-</td><td>-</td><td>-</td><td>-</td><td>100%</td><td>+50% chance</td></tr>"
            "</table>"
            "<br><b>XP:</b> 25 base + 2/min + streak bonus | <b>Bonus Item:</b> Extra Legendary item at 7hr+"
        )
        rewards_info.setWordWrap(True)
        rewards_info.setStyleSheet("color: #888888; font-size: 10px;")
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
            QtWidgets.QMessageBox.warning(self, "Invalid Duration", "Please set a time greater than 0 minutes.")
            return

        mode = self._current_mode()
        self.blocker.mode = mode

        # Reset Pomodoro state
        self.pomodoro_is_break = False
        self.pomodoro_session_count = 0
        self.pomodoro_total_work_time = 0
        self.last_checkin_time = None
        self._checkin_count = 0  # Reset priority check-in counter

        # Pomodoro uses its own durations
        if mode == BlockMode.POMODORO:
            total_seconds = self.blocker.pomodoro_work * 60
            self.status_label.setText(f"🍅 WORK #{self.pomodoro_session_count + 1}")
        else:
            total_seconds = total_minutes * 60

        success, message = self.blocker.block_sites(duration_seconds=total_seconds)
        if not success:
            self.timer_running = False  # Reset on blocking failure
            QtWidgets.QMessageBox.critical(self, "Cannot Start Session", message)
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
                QtWidgets.QMessageBox.warning(self, "Incorrect Password", "The password you entered is incorrect.\nSession continues.")
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

    def _give_session_rewards(self, session_minutes: int) -> None:
        """Give item drop, XP, and diary entry rewards."""
        if not GAMIFICATION_AVAILABLE:
            return
        # Skip if gamification mode is disabled
        if not is_gamification_enabled(self.blocker.adhd_buster):
            return

        streak = self.blocker.stats.get("streak_days", 0)
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        
        # Get active story for themed item generation
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        
        # Award XP for the focus session
        xp_info = calculate_session_xp(session_minutes, streak)
        xp_result = award_xp(self.blocker.adhd_buster, xp_info["total_xp"], source="focus_session")
        leveled_up = xp_result.get("leveled_up", False)

        # Generate item (generate_item already imported at top)
        item = generate_item(session_minutes=session_minutes, streak_days=streak,
                              story_id=active_story)

        # Lucky upgrade chance based on luck bonus
        luck_chance = min(luck / 100, 10)
        if luck > 0 and random.random() * 100 < luck_chance:
            rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
            try:
                current_idx = rarity_order.index(item["rarity"])
                if current_idx < len(rarity_order) - 1:
                    item = generate_item(rarity=rarity_order[current_idx + 1],
                                          session_minutes=session_minutes, streak_days=streak,
                                          story_id=active_story)
                    item["lucky_upgrade"] = True
            except ValueError:
                pass  # Skip upgrade if rarity is invalid

        # Add to inventory
        if "inventory" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["inventory"] = []
        self.blocker.adhd_buster["inventory"].append(item)
        self.blocker.adhd_buster["total_collected"] = self.blocker.adhd_buster.get("total_collected", 0) + 1
        
        # Cap inventory size to prevent unbounded growth (keep newest items)
        MAX_INVENTORY_SIZE = 500
        if len(self.blocker.adhd_buster["inventory"]) > MAX_INVENTORY_SIZE:
            self.blocker.adhd_buster["inventory"] = self.blocker.adhd_buster["inventory"][-MAX_INVENTORY_SIZE:]

        # Auto-equip if slot empty
        slot = item.get("slot")
        if "equipped" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["equipped"] = {}
        if not self.blocker.adhd_buster["equipped"].get(slot):
            self.blocker.adhd_buster["equipped"][slot] = item.copy()

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

        # Sync changes to active hero before saving
        if GAMIFICATION_AVAILABLE:
            sync_hero_data(self.blocker.adhd_buster)
        self.blocker.save_config()

        # Show level-up celebration first (most exciting!)
        if leveled_up:
            LevelUpCelebrationDialog(xp_result, self.window()).exec()

        # Show item drop dialog
        ItemDropDialog(self.blocker, item, session_minutes, streak, self.window()).exec()

        # Refresh ADHD Buster tab (so new gear shows in dropdowns)
        main_window = self.window()
        if hasattr(main_window, 'refresh_adhd_tab'):
            main_window.refresh_adhd_tab()

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

        # Show session complete dialog with break suggestions
        main_window = self.window()
        if hasattr(main_window, 'show_ai_session_complete'):
            main_window.show_ai_session_complete(elapsed)
        else:
            QtWidgets.QMessageBox.information(self, "Complete!", "🎉 Focus session complete!\nGreat job staying focused!")

        # Defer rewards to allow UI to remain responsive
        if session_minutes > 0:
            QtCore.QTimer.singleShot(50, lambda: self._give_session_rewards_deferred(session_minutes))
        else:
            self.session_complete.emit(elapsed)

    def _give_session_rewards_deferred(self, session_minutes: int) -> None:
        """Deferred session rewards to keep UI responsive."""
        QtWidgets.QApplication.processEvents()
        self._give_session_rewards(session_minutes)
        QtWidgets.QApplication.processEvents()
        self._show_priority_time_log(session_minutes)
        # Calculate elapsed for signal - approximate from session_minutes
        self.session_complete.emit(session_minutes * 60)

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

            if QtWidgets.QMessageBox.question(
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

            if QtWidgets.QMessageBox.question(
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
            QtWidgets.QMessageBox.critical(self, "Blocking Failed", message)
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
        self.analyzer = ProductivityAnalyzer(STATS_PATH) if ProductivityAnalyzer else None
        self.gamification = GamificationEngine(STATS_PATH) if GamificationEngine else None
        self.focus_goals = FocusGoals(GOALS_PATH, STATS_PATH) if FocusGoals else None
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
            QtWidgets.QMessageBox.information(self, "Import", "Sites imported successfully!")

    def _export_sites(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Sites", "", "JSON Files (*.json)")
        if path and self.blocker.export_config(path):
            QtWidgets.QMessageBox.information(self, "Export", "Sites exported successfully!")


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
        QtWidgets.QMessageBox.information(self, f"{category} Sites", text)

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
            QtWidgets.QMessageBox.warning(self, "No Days Selected", "Please select at least one day for the schedule.")
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


class StatsTab(QtWidgets.QWidget):
    """Statistics tab - focus time, sessions, streaks, weekly chart."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        inner = QtWidgets.QVBoxLayout(container)

        # Overview cards
        overview_group = QtWidgets.QGroupBox("📊 Overview")
        overview_layout = QtWidgets.QGridLayout(overview_group)
        self.total_hours_lbl = QtWidgets.QLabel("0h")
        self.total_hours_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.sessions_lbl = QtWidgets.QLabel("0")
        self.sessions_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.streak_lbl = QtWidgets.QLabel("0 days")
        self.streak_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.best_streak_lbl = QtWidgets.QLabel("0 days")
        self.best_streak_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")

        overview_layout.addWidget(QtWidgets.QLabel("Total Focus Time"), 0, 0)
        overview_layout.addWidget(self.total_hours_lbl, 1, 0)
        overview_layout.addWidget(QtWidgets.QLabel("Sessions Completed"), 0, 1)
        overview_layout.addWidget(self.sessions_lbl, 1, 1)
        overview_layout.addWidget(QtWidgets.QLabel("Current Streak"), 2, 0)
        overview_layout.addWidget(self.streak_lbl, 3, 0)
        overview_layout.addWidget(QtWidgets.QLabel("Best Streak"), 2, 1)
        overview_layout.addWidget(self.best_streak_lbl, 3, 1)
        inner.addWidget(overview_group)

        # Focus goals dashboard (weekly/monthly targets)
        goals_group = QtWidgets.QGroupBox("🎯 Focus Goals Dashboard")
        goals_layout = QtWidgets.QVBoxLayout(goals_group)

        # Weekly goal
        weekly_row = QtWidgets.QHBoxLayout()
        weekly_row.addWidget(QtWidgets.QLabel("Weekly Goal:"))
        self.weekly_bar = QtWidgets.QProgressBar()
        self.weekly_bar.setMaximum(100)
        self.weekly_bar.setTextVisible(True)
        weekly_row.addWidget(self.weekly_bar, stretch=1)
        self.weekly_target = QtWidgets.QDoubleSpinBox()
        self.weekly_target.setRange(1, 200)
        self.weekly_target.setSuffix(" h")
        self.weekly_target.setValue(float(self.blocker.stats.get("weekly_goal_hours", 10)))
        weekly_set = QtWidgets.QPushButton("Set")
        weekly_set.clicked.connect(self._set_weekly_goal)
        weekly_row.addWidget(self.weekly_target)
        weekly_row.addWidget(weekly_set)
        goals_layout.addLayout(weekly_row)

        # Monthly goal
        monthly_row = QtWidgets.QHBoxLayout()
        monthly_row.addWidget(QtWidgets.QLabel("Monthly Goal:"))
        self.monthly_bar = QtWidgets.QProgressBar()
        self.monthly_bar.setMaximum(100)
        self.monthly_bar.setTextVisible(True)
        monthly_row.addWidget(self.monthly_bar, stretch=1)
        self.monthly_target = QtWidgets.QDoubleSpinBox()
        self.monthly_target.setRange(1, 1000)
        self.monthly_target.setSuffix(" h")
        self.monthly_target.setValue(float(self.blocker.stats.get("monthly_goal_hours", 40)))
        monthly_set = QtWidgets.QPushButton("Set")
        monthly_set.clicked.connect(self._set_monthly_goal)
        monthly_row.addWidget(self.monthly_target)
        monthly_row.addWidget(monthly_set)
        goals_layout.addLayout(monthly_row)

        inner.addWidget(goals_group)

        # Weekly chart (text-based)
        week_group = QtWidgets.QGroupBox("📈 This Week")
        week_layout = QtWidgets.QVBoxLayout(week_group)
        self.week_text = QtWidgets.QTextEdit()
        self.week_text.setReadOnly(True)
        self.week_text.setFont(QtGui.QFont("Consolas", 10))
        self.week_text.setMaximumHeight(200)
        week_layout.addWidget(self.week_text)
        inner.addWidget(week_group)

        # Distraction attempts (bypass) if available
        if BYPASS_LOGGER_AVAILABLE:
            bypass_group = QtWidgets.QGroupBox("🚫 Distraction Attempts")
            bypass_layout = QtWidgets.QVBoxLayout(bypass_group)

            self.bypass_session_label = QtWidgets.QLabel("Current Session: 0 attempts")
            self.bypass_session_sites = QtWidgets.QLabel("No sites accessed")
            self.bypass_session_sites.setStyleSheet("color: gray;")
            bypass_layout.addWidget(self.bypass_session_label)
            bypass_layout.addWidget(self.bypass_session_sites)

            self.bypass_total_label = QtWidgets.QLabel("Total attempts: 0")
            self.bypass_top_sites = QtWidgets.QLabel("Top distractions: -")
            self.bypass_peak_hours = QtWidgets.QLabel("Peak hours: -")
            bypass_layout.addWidget(self.bypass_total_label)
            bypass_layout.addWidget(self.bypass_top_sites)
            bypass_layout.addWidget(self.bypass_peak_hours)

            self.bypass_insights = QtWidgets.QTextEdit()
            self.bypass_insights.setReadOnly(True)
            self.bypass_insights.setMaximumHeight(80)
            bypass_layout.addWidget(self.bypass_insights)

            refresh_bypass = QtWidgets.QPushButton("🔄 Refresh Attempts")
            refresh_bypass.clicked.connect(self._refresh_bypass_stats)
            bypass_layout.addWidget(refresh_bypass)

            inner.addWidget(bypass_group)

        # Reset button
        reset_btn = QtWidgets.QPushButton("🔄 Reset All Statistics")
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
        weekly_target = float(self.blocker.stats.get("weekly_goal_hours", 10))
        monthly_target = float(self.blocker.stats.get("monthly_goal_hours", 40))
        weekly_minutes = self._sum_focus_minutes(7)
        monthly_minutes = self._sum_focus_minutes(30)

        weekly_pct = 0 if weekly_target <= 0 else min(100, int((weekly_minutes / 60) / weekly_target * 100))
        monthly_pct = 0 if monthly_target <= 0 else min(100, int((monthly_minutes / 60) / monthly_target * 100))

        self.weekly_bar.setFormat(f"{weekly_minutes/60:.1f}h / {weekly_target:.0f}h ({weekly_pct}%)")
        self.weekly_bar.setValue(weekly_pct)
        self.monthly_bar.setFormat(f"{monthly_minutes/60:.1f}h / {monthly_target:.0f}h ({monthly_pct}%)")
        self.monthly_bar.setValue(monthly_pct)

        # Weekly chart
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        today = datetime.now()
        week_data = []
        max_time = 1
        for i in range(6, -1, -1):
            date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            daily = self.blocker.stats.get("daily_stats", {}).get(date_str, {})
            time_min = daily.get("focus_time", 0) // 60
            week_data.append((date_str, time_min))
            max_time = max(max_time, time_min)

        lines = ["Focus time this week:\n"]
        for date_str, time_min in week_data:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = days[dt.weekday()]
            bar_len = int((time_min / max_time) * 30) if max_time > 0 else 0
            bar = "█" * bar_len + "░" * (30 - bar_len)
            lines.append(f"  {day_name}  {bar} {time_min}m")
        total_week = sum(t for _, t in week_data)
        lines.append(f"\n  Total: {total_week} min ({total_week // 60}h {total_week % 60}m)")
        self.week_text.setPlainText("\n".join(lines))

        if BYPASS_LOGGER_AVAILABLE:
            self._refresh_bypass_stats()

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

    def _reset_stats(self) -> None:
        if QtWidgets.QMessageBox.question(self, "Reset Stats", "Reset all statistics?") == QtWidgets.QMessageBox.Yes:
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

    def _set_password(self) -> None:
        pwd, ok = QtWidgets.QInputDialog.getText(self, "Set Password", "Enter new password:", QtWidgets.QLineEdit.Password)
        if not ok or not pwd:
            return
        confirm, ok = QtWidgets.QInputDialog.getText(self, "Confirm", "Confirm password:", QtWidgets.QLineEdit.Password)
        if ok and pwd == confirm:
            self.blocker.set_password(pwd)
            self._update_pwd_status()
            QtWidgets.QMessageBox.information(self, "Password Set", "Your password has been set successfully!")
        else:
            QtWidgets.QMessageBox.warning(self, "Password Mismatch", "The passwords you entered don't match. Please try again.")

    def _remove_password(self) -> None:
        if not self.blocker.password_hash:
            QtWidgets.QMessageBox.information(self, "Info", "No password set")
            return
        pwd, ok = QtWidgets.QInputDialog.getText(self, "Remove Password", "Enter current password:", QtWidgets.QLineEdit.Password)
        if ok and self.blocker.verify_password(pwd or ""):
            self.blocker.set_password(None)
            self._update_pwd_status()
        else:
            QtWidgets.QMessageBox.warning(self, "Incorrect Password", "The password you entered is incorrect.")

    def _save_pomodoro(self) -> None:
        self.blocker.pomodoro_work = self.pomo_work_spin.value()
        self.blocker.pomodoro_break = self.pomo_break_spin.value()
        self.blocker.pomodoro_long_break = self.pomo_long_spin.value()
        self.blocker.save_config()
        QtWidgets.QMessageBox.information(self, "Saved", "Pomodoro settings saved!")

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
            if FocusGoals and Path(GOALS_PATH).exists():
                try:
                    with open(GOALS_PATH, "r", encoding="utf-8") as gf:
                        backup_data["goals"] = json.load(gf)
                except Exception:
                    pass
            with open(path, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2)
            QtWidgets.QMessageBox.information(self, "Backup Complete", "Backup saved successfully!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Backup Failed", str(e))

    def _restore_backup(self) -> None:
        import json
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Backup", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "backup_version" not in data:
                QtWidgets.QMessageBox.warning(self, "Invalid", "Not a valid backup file.")
                return
            if QtWidgets.QMessageBox.question(self, "Confirm", "Restore backup? This will replace all current data.") != QtWidgets.QMessageBox.Yes:
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
                    with open(GOALS_PATH, "w", encoding="utf-8") as gf:
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

            QtWidgets.QMessageBox.information(self, "Restored", "Backup restored successfully!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Restore Failed", str(e))

    def _emergency_cleanup(self) -> None:
        # Extra warning for strict/hardcore modes
        mode = getattr(self.blocker, 'mode', None)
        if mode in (BlockMode.STRICT, BlockMode.HARDCORE) and self.blocker.is_blocking:
            reply = QtWidgets.QMessageBox.warning(
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
        
        if QtWidgets.QMessageBox.question(self, "Emergency Cleanup", "Remove ALL blocks and clean system?") != QtWidgets.QMessageBox.Yes:
            return
        success, message = self.blocker.emergency_cleanup()
        if success:
            QtWidgets.QMessageBox.information(self, "Cleanup Complete", message)
            # Reset Timer UI
            main_win = self.window()
            if hasattr(main_win, "timer_tab"):
                main_win.timer_tab._force_stop_session()
        else:
            QtWidgets.QMessageBox.critical(self, "Cleanup Failed", message)

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
        self.unit_combo = QtWidgets.QComboBox()
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
        self.note_combo = QtWidgets.QComboBox()
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
        
        # Initialize settings from saved values
        self._load_settings()
    
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
            QtWidgets.QMessageBox.information(self, "Goal Cleared", 
                "Goal weight has been cleared. Check the box and set a value to enable.")
            return
        
        goal = self.goal_input.value()
        unit = self.unit_combo.currentText()
        # Store goal in kg for consistency
        self.blocker.weight_goal = goal / 2.20462 if unit == "lbs" else goal
        self.blocker.save_config()
        self._refresh_display()
        QtWidgets.QMessageBox.information(self, "Goal Set", 
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
                story_id
            )
        elif GAMIFICATION_AVAILABLE and check_weight_entry_rewards and is_gamification_enabled(self.blocker.adhd_buster):
            # Fallback to basic rewards
            story_id = self.blocker.adhd_buster.get("active_story", "warrior")
            rewards = check_weight_entry_rewards(
                entries_for_reward, 
                weight_kg, 
                date_str,
                story_id
            )
        
        # Update or add entry
        # Get note from combo
        note = self.note_combo.currentData() or ""
        
        new_entry = {"date": date_str, "weight": weight_kg}
        if note:
            new_entry["note"] = note
        
        if existing_idx is not None:
            reply = QtWidgets.QMessageBox.question(
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
        
        self.blocker.save_config()
        
        # Process rewards
        if rewards and GAMIFICATION_AVAILABLE:
            self._process_rewards(rewards)
        
        self._refresh_display()
    
    def _process_rewards(self, rewards: dict) -> None:
        """Process and show weight loss rewards."""
        items_earned = []
        new_milestone_ids = []
        
        # Get luck bonus for potential upgrades (same as focus session rewards)
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        luck_chance = min(luck / 100, 10) if luck > 0 else 0
        
        def maybe_upgrade_item(item: dict) -> dict:
            """Apply luck-based upgrade chance to item."""
            if luck_chance > 0 and random.random() * 100 < luck_chance:
                rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
                try:
                    current_idx = rarity_order.index(item.get("rarity", "Common"))
                    if current_idx < len(rarity_order) - 1:
                        story_id = self.blocker.adhd_buster.get("active_story", "warrior")
                        upgraded = generate_item(rarity=rarity_order[current_idx + 1], story_id=story_id)
                        upgraded["slot"] = item.get("slot")  # Keep same slot
                        upgraded["lucky_upgrade"] = True
                        return upgraded
                except ValueError:
                    pass  # Skip upgrade if rarity is invalid
            return item
        
        # Collect all earned items - Daily/Weekly/Monthly
        if rewards.get("daily_reward"):
            item = maybe_upgrade_item(rewards["daily_reward"])
            items_earned.append(("Daily", item))
            self.blocker.adhd_buster.setdefault("inventory", []).append(item)
        
        if rewards.get("weekly_reward"):
            item = maybe_upgrade_item(rewards["weekly_reward"])
            items_earned.append(("Weekly Bonus", item))
            self.blocker.adhd_buster.setdefault("inventory", []).append(item)
        
        if rewards.get("monthly_reward"):
            item = maybe_upgrade_item(rewards["monthly_reward"])
            items_earned.append(("Monthly Bonus", item))
            self.blocker.adhd_buster.setdefault("inventory", []).append(item)
        
        # Streak reward
        if rewards.get("streak_reward"):
            streak_data = rewards["streak_reward"]
            item = maybe_upgrade_item(streak_data["item"])
            items_earned.append((f"🔥 {streak_data['streak_days']}-Day Streak", item))
            self.blocker.adhd_buster.setdefault("inventory", []).append(item)
            new_milestone_ids.append(streak_data["milestone_id"])
        
        # Milestone rewards
        for milestone in rewards.get("new_milestones", []):
            item = maybe_upgrade_item(milestone["item"])
            items_earned.append((f"🏆 {milestone['name']}", item))
            self.blocker.adhd_buster.setdefault("inventory", []).append(item)
            new_milestone_ids.append(milestone["milestone_id"])
        
        # Maintenance reward (only if no daily reward to avoid double-rewarding)
        if rewards.get("maintenance_reward") and not rewards.get("daily_reward"):
            maint_data = rewards["maintenance_reward"]
            item = maybe_upgrade_item(maint_data["item"])
            items_earned.append(("⚖️ Maintenance", item))
            self.blocker.adhd_buster.setdefault("inventory", []).append(item)
        
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
            # Update total collected count (same as focus sessions)
            self.blocker.adhd_buster["total_collected"] = self.blocker.adhd_buster.get("total_collected", 0) + len(items_earned)
            
            # Auto-equip items to empty slots (same as focus sessions)
            if "equipped" not in self.blocker.adhd_buster:
                self.blocker.adhd_buster["equipped"] = {}
            for _, item in items_earned:
                slot = item.get("slot")
                if slot and not self.blocker.adhd_buster["equipped"].get(slot):
                    self.blocker.adhd_buster["equipped"][slot] = item.copy()
            
            # Sync hero data (same as focus sessions)
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
            
            QtWidgets.QMessageBox.information(
                self, "🎉 Weight Rewards!",
                f"<h3>Congratulations!</h3>{msg}"
            )
            
            # Show diary entry reveal (same as focus sessions)
            if diary_entry:
                DiaryEntryRevealDialog(self.blocker, diary_entry, session_minutes=0, parent=self.window()).exec()
            
            # Refresh ADHD Buster tab (so new gear shows in dropdowns)
            main_window = self.window()
            if hasattr(main_window, 'refresh_adhd_tab'):
                main_window.refresh_adhd_tab()
        elif rewards.get("messages"):
            # Show info messages even if no rewards
            QtWidgets.QMessageBox.information(
                self, "Weight Logged",
                "\n".join(rewards["messages"])
            )
    
    def _delete_entry(self, date_str: str) -> None:
        """Delete a weight entry."""
        reply = QtWidgets.QMessageBox.question(
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
        QtWidgets.QMessageBox.information(self, "Height Set", f"Height set to {height} cm")
    
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
                QtWidgets.QMessageBox.information(
                    self, "⚖️ Weight Reminder",
                    "Don't forget to log your weight today!"
                )
    
    def _show_weekly_insights(self) -> None:
        """Show weekly insights in a dialog."""
        if not get_weekly_insights:
            QtWidgets.QMessageBox.information(self, "Weekly Insights", "Insights not available")
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
            QtWidgets.QMessageBox.information(self, "Weekly Insights", msg)
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
        self.activity_combo = QtWidgets.QComboBox()
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
        self.intensity_combo = QtWidgets.QComboBox()
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
            reply = QtWidgets.QMessageBox.question(
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
        
        # Process rewards
        if rewards and GAMIFICATION_AVAILABLE:
            self._process_rewards(rewards)
        
        # Reset form
        self.note_input.clear()
        self._refresh_display()
    
    def _process_rewards(self, rewards: dict) -> None:
        """Process and show activity rewards."""
        items_earned = []
        new_milestone_ids = []
        
        # Get luck bonus for potential upgrades
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        luck_chance = min(luck / 100, 10) if luck > 0 else 0
        
        def maybe_upgrade_item(item: dict) -> dict:
            """Apply luck-based upgrade chance to item."""
            if luck_chance > 0 and random.random() * 100 < luck_chance:
                rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
                try:
                    current_idx = rarity_order.index(item.get("rarity", "Common"))
                    if current_idx < len(rarity_order) - 1:
                        story_id = self.blocker.adhd_buster.get("active_story", "warrior")
                        upgraded = generate_item(rarity=rarity_order[current_idx + 1], story_id=story_id)
                        upgraded["slot"] = item.get("slot")
                        upgraded["lucky_upgrade"] = True
                        return upgraded
                except ValueError:
                    pass  # Skip upgrade if rarity is invalid
            return item
        
        # Base activity reward
        if rewards.get("reward"):
            item = maybe_upgrade_item(rewards["reward"])
            items_earned.append(("Activity", item))
            self.blocker.adhd_buster.setdefault("inventory", []).append(item)
        
        # Streak reward
        if rewards.get("streak_reward"):
            streak_data = rewards["streak_reward"]
            item = maybe_upgrade_item(streak_data["item"])
            items_earned.append((f"🔥 {streak_data['streak_days']}-Day Streak", item))
            self.blocker.adhd_buster.setdefault("inventory", []).append(item)
            new_milestone_ids.append(streak_data["milestone_id"])
        
        # Milestone rewards
        for milestone in rewards.get("new_milestones", []):
            item = maybe_upgrade_item(milestone["item"])
            items_earned.append((f"🏆 {milestone['name']}", item))
            self.blocker.adhd_buster.setdefault("inventory", []).append(item)
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
        
        if items_earned:
            # Update total collected count
            self.blocker.adhd_buster["total_collected"] = self.blocker.adhd_buster.get("total_collected", 0) + len(items_earned)
            
            # Auto-equip to empty slots
            if "equipped" not in self.blocker.adhd_buster:
                self.blocker.adhd_buster["equipped"] = {}
            for _, item in items_earned:
                slot = item.get("slot")
                if slot and not self.blocker.adhd_buster["equipped"].get(slot):
                    self.blocker.adhd_buster["equipped"][slot] = item.copy()
            
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
            
            msg = "<br>".join(msg_parts)
            QtWidgets.QMessageBox.information(
                self, "🏆 Activity Rewards!",
                f"<h3>Great workout!</h3>{msg}"
            )
            
            # Show diary entry reveal
            if diary_entry:
                DiaryEntryRevealDialog(self.blocker, diary_entry, session_minutes=0, parent=self.window()).exec()
            
            # Refresh ADHD Buster tab
            main_window = self.window()
            if hasattr(main_window, 'refresh_adhd_tab'):
                main_window.refresh_adhd_tab()
        elif rewards.get("messages"):
            QtWidgets.QMessageBox.information(
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
        reply = QtWidgets.QMessageBox.question(
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
                
                QtWidgets.QMessageBox.information(
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
        self.quality_combo = QtWidgets.QComboBox()
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
            "Earlier = better rewards. Reward is based on current time."
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
        
        # Separator
        sep_line = QtWidgets.QFrame()
        sep_line.setFrameShape(QtWidgets.QFrame.HLine)
        sep_line.setStyleSheet("color: #444;")
        screenoff_main_layout.addWidget(sep_line)
        
        # Existing screen-off time selector (for logging past sleep)
        screenoff_layout = QtWidgets.QHBoxLayout()
        self.screenoff_checkbox = QtWidgets.QCheckBox("I turned off my screen at:")
        self.screenoff_checkbox.setToolTip("Earn a bonus item for healthy digital habits!\nEarlier = better rewards.")
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
        self.chronotype_combo = QtWidgets.QComboBox()
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
        h, m = bedtime.split(":")
        self.bedtime_edit.setTime(QtCore.QTime(int(h), int(m)))
        h, m = wake_time.split(":")
        self.wake_edit.setTime(QtCore.QTime(int(h), int(m)))
    
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
        
        rarity = get_screen_off_bonus_rarity(current_time)
        if rarity:
            rarity_colors = {
                "Legendary": "#ffd700",
                "Epic": "#a335ee",
                "Rare": "#0070dd",
                "Uncommon": "#1eff00",
                "Common": "#ffffff",
            }
            color = rarity_colors.get(rarity, "#888")
            self.sleep_now_info.setText(f"Now: {current_time} → <b style='color:{color}'>{rarity}</b> item!")
            self.sleep_now_btn.setEnabled(True)
        else:
            self.sleep_now_info.setText(f"Now: {current_time} (too late for bonus)")
            self.sleep_now_btn.setEnabled(False)
    
    def _go_to_sleep_now(self) -> None:
        """Handle 'Go to Sleep NOW' button - give immediate reward based on current time."""
        if not GAMIFICATION_AVAILABLE or not is_gamification_enabled(self.blocker.adhd_buster):
            QtWidgets.QMessageBox.information(
                self, "Gamification Disabled",
                "Enable gamification mode to earn rewards!"
            )
            return
        
        if not get_screen_off_bonus_rarity:
            QtWidgets.QMessageBox.warning(
                self, "Feature Unavailable",
                "Sleep tracking module not fully loaded."
            )
            return
        
        # Get current time and calculate reward
        now = QtCore.QTime.currentTime()
        current_time = now.toString("HH:mm")
        rarity = get_screen_off_bonus_rarity(current_time)
        
        if not rarity:
            QtWidgets.QMessageBox.information(
                self, "Too Late",
                "It's too late for the Nighty-Night bonus.\n"
                "Go to sleep before 01:00 to earn rewards!\n\n"
                "Earlier = better rewards:\n"
                "• 21:00 or earlier: Legendary\n"
                "• 22:00: Epic-Legendary\n"
                "• 23:00: Rare-Epic\n"
                "• 00:00: Common-Rare"
            )
            return
        
        # Check if already used today (based on sleep-now timestamp)
        today = datetime.now().strftime("%Y-%m-%d")
        last_sleep_now = self.blocker.adhd_buster.get("last_sleep_now_date", "")
        if last_sleep_now == today:
            QtWidgets.QMessageBox.information(
                self, "Already Used",
                "You already claimed your Nighty-Night bonus today!\n"
                "Come back tomorrow for another reward."
            )
            return
        
        # Generate reward
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        item = generate_item(rarity=rarity, story_id=active_story)
        item["source"] = "sleep_now_bonus"
        
        # Ensure inventory exists
        if "inventory" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["inventory"] = []
        
        self.blocker.adhd_buster["inventory"].append(item)
        self.blocker.adhd_buster["total_collected"] = self.blocker.adhd_buster.get("total_collected", 0) + 1
        self.blocker.adhd_buster["last_sleep_now_date"] = today
        
        # Auto-equip if slot empty
        if "equipped" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["equipped"] = {}
        slot = item.get("slot")
        if slot and not self.blocker.adhd_buster["equipped"].get(slot):
            self.blocker.adhd_buster["equipped"][slot] = item.copy()
        
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
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.exec()
        
        # Update preview to show it's been used
        self.sleep_now_btn.setEnabled(False)
        self.sleep_now_info.setText(f"✓ Claimed at {current_time}! Sweet dreams!")

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
            reply = QtWidgets.QMessageBox.question(
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
        
        # Track screen-off bonus outside the reward block
        screenoff_bonus_item = None
        
        # Handle rewards
        if reward_info and GAMIFICATION_AVAILABLE:
            items_earned = []
            
            # Ensure inventory exists before processing any rewards
            if "inventory" not in self.blocker.adhd_buster:
                self.blocker.adhd_buster["inventory"] = []
            
            # Base reward
            if reward_info.get("reward"):
                item = reward_info["reward"]
                
                # Maybe upgrade item based on luck
                def maybe_upgrade_item(item: dict) -> dict:
                    luck = self.blocker.adhd_buster.get("luck_bonus", 0)
                    if luck > 0:
                        luck_chance = min(luck / 100, 10)
                        if random.random() * 100 < luck_chance:
                            rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
                            try:
                                current_idx = rarity_order.index(item["rarity"])
                                if current_idx < len(rarity_order) - 1:
                                    active_story = self.blocker.adhd_buster.get("active_story", "warrior")
                                    item = generate_item(rarity=rarity_order[current_idx + 1],
                                                        story_id=active_story)
                                    item["lucky_upgrade"] = True
                            except ValueError:
                                pass
                    return item
                
                item = maybe_upgrade_item(item)
                self.blocker.adhd_buster["inventory"].append(item)
                items_earned.append(item)
            
            # Streak reward
            if reward_info.get("streak_reward"):
                streak_item = reward_info["streak_reward"]["item"]
                self.blocker.adhd_buster["inventory"].append(streak_item)
                items_earned.append(streak_item)
                self.blocker.sleep_milestones.append(reward_info["streak_reward"]["milestone_id"])
            
            # Milestone rewards
            new_milestone_ids = []
            for milestone in reward_info.get("new_milestones", []):
                self.blocker.adhd_buster["inventory"].append(milestone["item"])
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
                    self.blocker.adhd_buster["inventory"].append(screenoff_bonus_item)
                    items_earned.append(screenoff_bonus_item)
            
            # Update total collected count (same as other trackers)
            if items_earned:
                self.blocker.adhd_buster["total_collected"] = self.blocker.adhd_buster.get("total_collected", 0) + len(items_earned)
                
                # Auto-equip to empty slots (same as other trackers)
                if "equipped" not in self.blocker.adhd_buster:
                    self.blocker.adhd_buster["equipped"] = {}
                for item in items_earned:
                    slot = item.get("slot")
                    if slot and not self.blocker.adhd_buster["equipped"].get(slot):
                        self.blocker.adhd_buster["equipped"][slot] = item.copy()
            
            # Sync hero data
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
        
        self.blocker.save_config()
        
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
                rarity = screenoff_bonus_item["rarity"]
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
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setTextFormat(QtCore.Qt.RichText)
        msg_box.setText(msg.replace("\n", "<br>"))
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
        
        QtWidgets.QMessageBox.information(self, "Sleep Entry Details", details)
    
    def _delete_entry(self, entry_index: int) -> None:
        """Delete a sleep entry."""
        if entry_index < 0 or entry_index >= len(self.blocker.sleep_entries):
            return
        entry = self.blocker.sleep_entries[entry_index]
        
        reply = QtWidgets.QMessageBox.question(
            self, "Delete Entry",
            f"Delete sleep entry for {entry.get('date', 'Unknown')}?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            del self.blocker.sleep_entries[entry_index]
            self.blocker.save_config()
            self._refresh_display()
    
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
            
            QtWidgets.QMessageBox.information(
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
        self.analyzer = ProductivityAnalyzer(STATS_PATH) if ProductivityAnalyzer else None
        self.gamification = GamificationEngine(STATS_PATH) if GamificationEngine else None
        self.focus_goals = FocusGoals(GOALS_PATH, STATS_PATH) if FocusGoals else None
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
        goals = self.blocker.stats.get("goals", [])
        for goal in goals:
            self.goals_list.addItem(f"📌 {goal}")
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

        # Fallback to legacy ProductivityAI class
        try:
            from productivity_ai import ProductivityAI
            ai = ProductivityAI()
            insights = ai.get_productivity_insights(self.blocker.stats)
            self.insights_text.setPlainText(insights)
        except Exception as e:
            self.insights_text.setPlainText(f"Error: {e}")

    def _new_challenge(self) -> None:
        if self.gamification:
            challenge = self.gamification.get_daily_challenge()
            # Persist simple text fallback for legacy display
            self.blocker.stats["daily_challenge"] = challenge.get("title", "")
            self.blocker.save_stats()
        else:
            import random
            challenges = [
                "Complete a 45-minute deep work session",
                "Stay focused for 30 minutes without checking social media",
                "Take a 5-minute break after every 25 minutes of work",
                "Complete 4 Pomodoro sessions today",
                "Block all distractions for 1 hour straight",
                "Finish one important task before checking email",
                "Do a 60-minute focus session",
                "Complete 3 focus sessions before lunch",
            ]
            challenge = random.choice(challenges)
            self.blocker.stats["daily_challenge"] = challenge
            self.blocker.save_stats()
        self._refresh_data()

    def _add_goal(self) -> None:
        goal, ok = QtWidgets.QInputDialog.getText(self, "Add Goal", "Enter your goal:")
        if ok and goal.strip():
            goals = self.blocker.stats.get("goals", [])
            goals.append(goal.strip())
            self.blocker.stats["goals"] = goals
            self.blocker.save_stats()
            if self.focus_goals:
                try:
                    # Default to weekly 5h target for new AI goal
                    self.focus_goals.add_goal(goal.strip(), "weekly", target=5 * 3600)
                except Exception:
                    pass
            self._refresh_data()

    def _complete_goal(self) -> None:
        item = self.goals_list.currentItem()
        if not item:
            QtWidgets.QMessageBox.warning(self, "No Goal Selected", "Please select a goal from the list first.")
            return
        row = self.goals_list.currentRow()
        goals = self.blocker.stats.get("goals", [])
        if 0 <= row < len(goals):
            completed = goals.pop(row)
            self.blocker.stats["goals"] = goals
            # Track completed goals
            completed_goals = self.blocker.stats.get("completed_goals", [])
            completed_goals.append(completed)
            self.blocker.stats["completed_goals"] = completed_goals
            self.blocker.save_stats()
            QtWidgets.QMessageBox.information(self, "Goal Completed!", f"🎉 '{completed}' marked as complete!")
            self._refresh_data()
            return

        # If not in legacy list, try AI goals
        if self.focus_goals:
            try:
                active = self.focus_goals.get_active_goals()
                if 0 <= row - len(goals) < len(active):
                    goal_id = active[row - len(goals)]["id"]
                    # Mark as completed by setting progress to target
                    for g in self.focus_goals.goals:
                        if g.get("id") == goal_id:
                            g["progress"] = g.get("target", g.get("progress", 0))
                            g["completed"] = True
                    self.focus_goals.save_goals()
                    self._refresh_data()
            except Exception:
                pass


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
                painter.drawText(label_rect.adjusted(offset[0], offset[1], 0, 0), 
                               QtCore.Qt.AlignCenter, f"⚔ {self.power}")
            painter.setOpacity(1.0)
        elif self.tier in ["epic"]:
            painter.setPen(QtGui.QColor("#e040fb"))
        elif self.tier in ["heroic"]:
            painter.setPen(QtGui.QColor("#42a5f5"))
        else:
            painter.setPen(QtGui.QColor("#fff"))
        
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
        robe_color = QtGui.QColor("#1a1a4a") if not self.equipped.get("Chestplate") else QtGui.QColor(self.equipped["Chestplate"].get("color", "#1a1a4a"))
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
                painter.drawText(label_rect.adjusted(offset[0], offset[1], 0, 0), 
                               QtCore.Qt.AlignCenter, f"📚 {self.power}")
            painter.setOpacity(1.0)
        elif self.tier in ["epic"]:
            painter.setPen(QtGui.QColor("#e040fb"))
        elif self.tier in ["heroic"]:
            painter.setPen(QtGui.QColor("#42a5f5"))
        else:
            painter.setPen(QtGui.QColor("#fff"))
        
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
        robe_color = QtGui.QColor("#2a2a5a") if not self.equipped.get("Chestplate") else QtGui.QColor(self.equipped["Chestplate"].get("color", "#2a2a5a"))
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
                painter.drawText(label_rect.adjusted(offset[0], offset[1], 0, 0), 
                               QtCore.Qt.AlignCenter, f"🌙 {self.power}")
            painter.setOpacity(1.0)
        elif self.tier in ["epic"]:
            painter.setPen(QtGui.QColor("#c0a0ff"))
        elif self.tier in ["heroic"]:
            painter.setPen(QtGui.QColor("#a0a0ff"))
        else:
            painter.setPen(QtGui.QColor("#d0d0ff"))
        
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
        shirt_color = QtGui.QColor("#74b9ff") if not self.equipped.get("Chestplate") else QtGui.QColor(self.equipped["Chestplate"].get("color", "#74b9ff"))
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
                painter.drawText(label_rect.adjusted(offset[0], offset[1], 0, 0), 
                               QtCore.Qt.AlignCenter, f"🏢 {self.power}")
            painter.setOpacity(1.0)
        elif self.tier in ["epic"]:
            painter.setPen(QtGui.QColor("#00bcd4"))
        elif self.tier in ["heroic"]:
            painter.setPen(QtGui.QColor("#4fc3f7"))
        else:
            painter.setPen(QtGui.QColor("#b2bec3"))
        
        painter.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Bold))
        painter.drawText(label_rect, QtCore.Qt.AlignCenter, f"🏢 {self.power}")


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
    
    def _log_water(self) -> None:
        """Log a glass of water and award rewards."""
        from datetime import datetime
        
        # Initialize water entries if needed
        if not hasattr(self.blocker, 'water_entries'):
            self.blocker.water_entries = []
        
        # Check if we can log
        if can_log_water:
            check = can_log_water(self.blocker.water_entries)
            if not check["can_log"]:
                QtWidgets.QMessageBox.information(self, "Hydration", check["reason"])
                return
        
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # Count today's glasses
        glasses_today = sum(
            1 for e in self.blocker.water_entries 
            if e.get("date") == today
        )
        
        # Calculate streak
        streak_days = self._calculate_streak()
        
        # Check rewards
        items_earned = []
        messages = []
        
        if check_water_entry_reward and GAMIFICATION_AVAILABLE:
            reward_info = check_water_entry_reward(
                glasses_today=glasses_today,
                streak_days=streak_days,
                story_id=self.blocker.adhd_buster.get("active_story", "warrior")
            )
            
            messages = reward_info.get("messages", [])
            
            for item in reward_info.get("items", []):
                self.blocker.adhd_buster["inventory"].append(item)
                items_earned.append(item)
            
            if items_earned:
                self.blocker.adhd_buster["total_collected"] = self.blocker.adhd_buster.get("total_collected", 0) + len(items_earned)
                
                # Auto-equip
                if "equipped" not in self.blocker.adhd_buster:
                    self.blocker.adhd_buster["equipped"] = {}
                for item in items_earned:
                    slot = item.get("slot")
                    if slot and not self.blocker.adhd_buster["equipped"].get(slot):
                        self.blocker.adhd_buster["equipped"][slot] = item.copy()
                
                if GAMIFICATION_AVAILABLE:
                    sync_hero_data(self.blocker.adhd_buster)
        else:
            messages = [f"💧 Glass #{glasses_today + 1} logged!"]
        
        # Log the entry
        entry = {
            "date": today,
            "time": now.strftime("%H:%M"),
            "glasses": 1
        }
        self.blocker.water_entries.append(entry)
        
        self.blocker.save_config()
        
        # Show feedback
        msg = "\n".join(messages)
        if items_earned:
            msg += "\n\n<b>Items earned:</b>"
            rarity_colors = {
                "Common": "#9e9e9e",
                "Uncommon": "#4caf50",
                "Rare": "#2196f3",
                "Epic": "#9c27b0",
                "Legendary": "#ff9800"
            }
            for item in items_earned:
                rarity = item.get("rarity", "Common")
                color = rarity_colors.get(rarity, "#9e9e9e")
                name = item.get("name", "Unknown Item")
                msg += f"\n<span style='color:{color}; font-weight:bold;'>[{rarity}]</span> {name}"
        
        QtWidgets.QMessageBox.information(self, "Water Logged! 💧", msg)
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
        
        while True:
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
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        if not hasattr(self.blocker, 'water_entries'):
            self.blocker.water_entries = []
        
        # Get today's entries
        today_entries = [e for e in self.blocker.water_entries if e.get("date") == today]
        glasses_today = len(today_entries)
        
        # Update progress display
        self.glasses_label.setText(f"{glasses_today} / {HYDRATION_MAX_DAILY_GLASSES} glasses")
        self.progress_bar.setValue(min(glasses_today, HYDRATION_MAX_DAILY_GLASSES))
        
        if glasses_today >= HYDRATION_MAX_DAILY_GLASSES:
            self.glasses_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4caf50;")
        else:
            self.glasses_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #4fc3f7;")
        
        # Update status/countdown
        if can_log_water:
            check = can_log_water(self.blocker.water_entries)
            if check["can_log"]:
                self.water_btn.setEnabled(True)
                self.status_label.setText("✅ Ready to log!")
                self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4caf50;")
            else:
                if check.get("minutes_remaining", 0) > 0:
                    mins = check["minutes_remaining"]
                    next_time = check.get("next_available_time", "")
                    self.water_btn.setEnabled(False)
                    self.status_label.setText(f"⏳ Wait {mins} min (next at {next_time})")
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
                f"🎯 Days on target ({HYDRATION_MAX_DAILY_GLASSES}+): {stats.get('days_on_target', 0)} "
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
        self._build_ui()
        self.refresh_all()  # Initial data load

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
        finally:
            self._refreshing = False
    
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
        if hasattr(self, 'inv_list'):
            self.inv_list.setEnabled(not active)

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

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        self.inner_layout = QtWidgets.QVBoxLayout(container)

        # Header with power
        header = QtWidgets.QHBoxLayout()
        header.addWidget(QtWidgets.QLabel("<b style='font-size:18px;'>🦸 ADHD Buster</b>"))
        header.addStretch()

        power = calculate_character_power(self.blocker.adhd_buster) if GAMIFICATION_AVAILABLE else 0
        power_info = get_power_breakdown(self.blocker.adhd_buster) if GAMIFICATION_AVAILABLE else {"base_power": 0, "set_bonus": 0, "active_sets": [], "total_power": 0}

        if power_info["set_bonus"] > 0:
            power_txt = f"⚔ Power: {power_info['total_power']} ({power_info['base_power']} + {power_info['set_bonus']} set)"
        else:
            power_txt = f"⚔ Power: {power_info['total_power']}"
        self.power_lbl = QtWidgets.QLabel(power_txt)
        self.power_lbl.setStyleSheet("font-weight: bold; color: #e65100;")
        header.addWidget(self.power_lbl)
        self.inner_layout.addLayout(header)

        # Active set bonuses (container for dynamic updates)
        self.sets_container = QtWidgets.QWidget()
        self.sets_layout = QtWidgets.QVBoxLayout(self.sets_container)
        self.sets_layout.setContentsMargins(0, 0, 0, 0)
        self._refresh_sets_display(power_info)
        self.inner_layout.addWidget(self.sets_container)

        # Potential set bonuses from inventory (container for dynamic updates)
        self.potential_sets_container = QtWidgets.QWidget()
        self.potential_sets_layout = QtWidgets.QVBoxLayout(self.potential_sets_container)
        self.potential_sets_layout.setContentsMargins(0, 0, 0, 0)
        self._refresh_potential_sets_display()
        self.inner_layout.addWidget(self.potential_sets_container)

        # Stats summary
        total_items = len(self.blocker.adhd_buster.get("inventory", []))
        total_collected = self.blocker.adhd_buster.get("total_collected", total_items)
        streak = self.blocker.stats.get("streak_days", 0)
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        self.stats_lbl = QtWidgets.QLabel(f"📦 {total_items} in bag  |  🎁 {total_collected} collected  |  🔥 {streak} day streak  |  🍀 {luck} luck")
        self.stats_lbl.setStyleSheet("color: gray;")
        self.inner_layout.addWidget(self.stats_lbl)

        # Level and XP Progress Section
        if GAMIFICATION_AVAILABLE:
            level_frame = QtWidgets.QFrame()
            level_frame.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e8f5e9, stop:1 #f1f8e9); border-radius: 8px; padding: 5px;")
            level_layout = QtWidgets.QVBoxLayout(level_frame)
            level_layout.setContentsMargins(15, 10, 15, 10)
            level_layout.setSpacing(5)
            
            # Get level info
            total_xp = self.blocker.adhd_buster.get("total_xp", 0)
            level, xp_in_level, xp_needed, progress = get_level_from_xp(total_xp)
            title, emoji = get_level_title(level)
            
            # Level header row
            level_header = QtWidgets.QHBoxLayout()
            self.level_title_lbl = QtWidgets.QLabel(f"{emoji} <b>Level {level}</b> - {title}")
            self.level_title_lbl.setStyleSheet("font-size: 14px; color: #2e7d32;")
            level_header.addWidget(self.level_title_lbl)
            level_header.addStretch()
            self.total_xp_lbl = QtWidgets.QLabel(f"✨ {total_xp:,} Total XP")
            self.total_xp_lbl.setStyleSheet("color: #558b2f; font-weight: bold;")
            level_header.addWidget(self.total_xp_lbl)
            level_layout.addLayout(level_header)
            
            # XP Progress bar
            self.xp_progress_bar = QtWidgets.QProgressBar()
            self.xp_progress_bar.setMaximum(100)
            self.xp_progress_bar.setValue(int(progress))
            self.xp_progress_bar.setTextVisible(False)
            self.xp_progress_bar.setFixedHeight(12)
            self.xp_progress_bar.setStyleSheet(
                "QProgressBar { background: rgba(0,0,0,0.1); border-radius: 6px; }"
                "QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4caf50, stop:1 #8bc34a); border-radius: 6px; }"
            )
            level_layout.addWidget(self.xp_progress_bar)
            
            # XP text
            self.xp_text_lbl = QtWidgets.QLabel(f"{xp_in_level:,} / {xp_needed:,} XP to Level {level + 1}")
            self.xp_text_lbl.setStyleSheet("color: #689f38; font-size: 11px;")
            self.xp_text_lbl.setAlignment(QtCore.Qt.AlignCenter)
            level_layout.addWidget(self.xp_text_lbl)
            
            self.inner_layout.addWidget(level_frame)

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
            self.story_combo = QtWidgets.QComboBox()
            self.story_combo.setMinimumWidth(250)
            
            current_story = get_selected_story(self.blocker.adhd_buster)
            current_idx = 0
            for i, (story_id, story_info) in enumerate(AVAILABLE_STORIES.items()):
                self.story_combo.addItem(f"{story_info['title']}", story_id)
                self.story_combo.setItemData(i, story_info['description'], QtCore.Qt.ToolTipRole)
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
        self.chapter_combo = QtWidgets.QComboBox()
        
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
            combo = QtWidgets.QComboBox()
            # Disable mouse wheel to prevent accidental changes
            combo.wheelEvent = lambda event: event.ignore()
            combo.setFocusPolicy(QtCore.Qt.StrongFocus)
            combo.addItem("[Empty]")
            slot_items = [item for item in inventory if item.get("slot") == slot]
            for idx, item in enumerate(slot_items):
                item_name = item.get('name', 'Unknown')
                item_rarity = item.get('rarity', 'Common')
                item_color = rarity_colors.get(item_rarity, "#9e9e9e")
                power = item.get('power', 10)
                display = f"{item_name} (+{power}) [{item_rarity}]"
                combo.addItem(display, item)
                # Set foreground color for this item
                combo.setItemData(combo.count() - 1, QtGui.QColor(item_color), QtCore.Qt.ForegroundRole)
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
            # Use themed slot display name with rarity color if equipped
            display_name = get_slot_display_name(slot, active_story) if get_slot_display_name else slot
            if current:
                item_rarity = current.get("rarity", "Common")
                item_color = rarity_colors.get(item_rarity, "#9e9e9e")
                slot_label = QtWidgets.QLabel(f'{display_name}: <span style="color:{item_color}; font-weight:bold;">[{item_rarity}]</span>')
                slot_label.setTextFormat(QtCore.Qt.RichText)
            else:
                slot_label = QtWidgets.QLabel(f"{display_name}:")
            self.slot_labels[slot] = slot_label
            equip_layout.addRow(slot_label, combo)
        char_equip.addWidget(equip_group)
        self.inner_layout.addLayout(char_equip)

        # Lucky Merge
        merge_group = QtWidgets.QGroupBox("🎲 Lucky Merge (High Risk, High Reward!)")
        merge_layout = QtWidgets.QVBoxLayout(merge_group)
        merge_layout.addWidget(QtWidgets.QLabel(
            "Click items in the inventory below to select them for merging.\n"
            "Items with ✓ are equipped and will be unequipped if merged."
        ))
        warn_lbl = QtWidgets.QLabel("⚠️ ~90% failure = ALL items lost! Only ~10% success rate!")
        warn_lbl.setStyleSheet("color: #d32f2f; font-weight: bold;")
        merge_layout.addWidget(warn_lbl)
        self.merge_btn = QtWidgets.QPushButton("🎲 Merge Selected (0)")
        self.merge_btn.setEnabled(False)
        self.merge_btn.clicked.connect(self._do_merge)
        merge_layout.addWidget(self.merge_btn)
        self.merge_rate_lbl = QtWidgets.QLabel("↓ Click items below to select for merge (Ctrl+click for multiple)")
        merge_layout.addWidget(self.merge_rate_lbl)
        self.inner_layout.addWidget(merge_group)

        # Inventory
        inv_group = QtWidgets.QGroupBox("📦 Inventory (click items to select for merge)")
        inv_layout = QtWidgets.QVBoxLayout(inv_group)
        sort_bar = QtWidgets.QHBoxLayout()
        sort_bar.addWidget(QtWidgets.QLabel("Sort:"))
        self.sort_combo = QtWidgets.QComboBox()
        self.sort_combo.addItems(["newest", "rarity", "slot", "power"])
        self.sort_combo.currentTextChanged.connect(self._refresh_inventory)
        sort_bar.addWidget(self.sort_combo)
        sort_bar.addStretch()
        inv_layout.addLayout(sort_bar)
        self.inv_list = QtWidgets.QListWidget()
        self.inv_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.inv_list.itemSelectionChanged.connect(self._update_merge_selection)
        inv_layout.addWidget(self.inv_list)
        self.inner_layout.addWidget(inv_group)

        self._refresh_inventory()

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
        salvage_btn = QtWidgets.QPushButton("🗑️ Salvage Duplicates")
        salvage_btn.clicked.connect(self._salvage_duplicates)
        btn_layout.addWidget(salvage_btn)
        optimize_btn = QtWidgets.QPushButton("⚡ Optimize Gear")
        optimize_btn.setToolTip("Automatically equip the best gear for maximum power (including set bonuses)")
        optimize_btn.clicked.connect(self._optimize_gear)
        btn_layout.addWidget(optimize_btn)
        btn_layout.addStretch()
        # Store button references for enabling/disabling during sessions
        self._action_buttons = [refresh_btn, diary_btn, salvage_btn, optimize_btn]
        self.inner_layout.addLayout(btn_layout)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _on_equip_change(self, slot: str, combo: QtWidgets.QComboBox) -> None:
        idx = combo.currentIndex()
        if "equipped" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["equipped"] = {}
        if idx == 0:
            self.blocker.adhd_buster["equipped"][slot] = None
        else:
            item = combo.currentData()
            if item:
                self.blocker.adhd_buster["equipped"][slot] = item.copy()
        # Sync changes to active hero before saving
        if GAMIFICATION_AVAILABLE:
            sync_hero_data(self.blocker.adhd_buster)
        self.blocker.save_config()
        # Use deferred refresh to update character, inventory, and power displays
        QtCore.QTimer.singleShot(0, self.refresh_all)

    def _refresh_sets_display(self, power_info: dict = None) -> None:
        """Refresh the active set bonuses display."""
        # Clear existing widgets from sets_layout
        while self.sets_layout.count():
            child = self.sets_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not GAMIFICATION_AVAILABLE:
            return
            
        if power_info is None:
            power_info = get_power_breakdown(self.blocker.adhd_buster)
        
        if power_info["active_sets"]:
            sets_group = QtWidgets.QGroupBox("🎯 Active Set Bonuses")
            sets_inner = QtWidgets.QVBoxLayout(sets_group)
            for s in power_info["active_sets"]:
                lbl = QtWidgets.QLabel(f"{s['emoji']} {s['name']} ({s['count']} items): +{s['bonus']} power")
                lbl.setStyleSheet("color: #4caf50; font-weight: bold;")
                sets_inner.addWidget(lbl)
            self.sets_layout.addWidget(sets_group)

    def _refresh_potential_sets_display(self) -> None:
        """Refresh the potential set bonuses display from inventory."""
        # Clear existing widgets
        while self.potential_sets_layout.count():
            child = self.potential_sets_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not GAMIFICATION_AVAILABLE:
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
            hint_group = QtWidgets.QGroupBox("💡 Potential Set Bonuses (in your inventory)")
            hint_inner = QtWidgets.QVBoxLayout(hint_group)
            
            for s in improvable_sets[:5]:  # Show top 5 potential sets
                if s["current_bonus"] > 0:
                    # Already have some items equipped for this set
                    hint_text = (
                        f"{s['emoji']} {s['name']}: {s['equipped_count']} equipped + "
                        f"{s['inventory_count']} in bag → could be +{s['potential_bonus']} power"
                    )
                    lbl = QtWidgets.QLabel(hint_text)
                    lbl.setStyleSheet("color: #ff9800;")  # Orange for partial sets
                else:
                    # No items equipped yet
                    hint_text = (
                        f"{s['emoji']} {s['name']}: {s['inventory_count']} items in bag → "
                        f"could be +{s['potential_bonus']} power (need {s['max_equippable']} equipped)"
                    )
                    lbl = QtWidgets.QLabel(hint_text)
                    lbl.setStyleSheet("color: #2196f3;")  # Blue for unequipped sets
                
                hint_inner.addWidget(lbl)
            
            tip_lbl = QtWidgets.QLabel("💡 Use 'Optimize Gear' to automatically equip the best items!")
            tip_lbl.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
            hint_inner.addWidget(tip_lbl)
            
            self.potential_sets_layout.addWidget(hint_group)

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
        
        # Update power label
        if power_info["set_bonus"] > 0:
            power_txt = f"⚔ Power: {power_info['total_power']} ({power_info['base_power']} + {power_info['set_bonus']} set)"
        else:
            power_txt = f"⚔ Power: {power_info['total_power']}"
        self.power_lbl.setText(power_txt)
        
        # Update stats label
        total_items = len(self.blocker.adhd_buster.get("inventory", []))
        total_collected = self.blocker.adhd_buster.get("total_collected", total_items)
        streak = self.blocker.stats.get("streak_days", 0)
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        self.stats_lbl.setText(f"📦 {total_items} in bag  |  🎁 {total_collected} collected  |  🔥 {streak} day streak  |  🍀 {luck} luck")
        
        # Update level and XP display
        if hasattr(self, 'level_title_lbl'):
            total_xp = self.blocker.adhd_buster.get("total_xp", 0)
            level, xp_in_level, xp_needed, progress = get_level_from_xp(total_xp)
            title, emoji = get_level_title(level)
            self.level_title_lbl.setText(f"{emoji} <b>Level {level}</b> - {title}")
            self.total_xp_lbl.setText(f"✨ {total_xp:,} Total XP")
            self.xp_progress_bar.setValue(int(progress))
            self.xp_text_lbl.setText(f"{xp_in_level:,} / {xp_needed:,} XP to Level {level + 1}")
        
        # Update set bonuses display
        self._refresh_sets_display(power_info)
        
        # Update potential set bonuses from inventory
        if hasattr(self, 'potential_sets_layout'):
            self._refresh_potential_sets_display()
        
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
        needs_save = False
        
        # Rarity colors for visual distinction
        rarity_colors = {
            "Common": "#9e9e9e",
            "Uncommon": "#4caf50",
            "Rare": "#2196f3",
            "Epic": "#9c27b0",
            "Legendary": "#ff9800"
        }
        
        # Update slot labels with themed names and equipped item rarity
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        for slot, label in self.slot_labels.items():
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
                combo.addItem(display, item)
                # Set foreground color for this item
                idx = combo.count() - 1
                combo.setItemData(idx, QtGui.QColor(item_color), QtCore.Qt.ForegroundRole)
            
            # Re-select current equipped item if it exists in inventory
            current = equipped.get(slot)
            if current:
                found = False
                for i in range(1, combo.count()):
                    item_data = combo.itemData(i)
                    if item_data and item_data.get("obtained_at") == current.get("obtained_at"):
                        combo.setCurrentIndex(i)
                        found = True
                        # Apply color to the combo box text for selected item
                        item_rarity = current.get("rarity", "Common")
                        item_color = rarity_colors.get(item_rarity, "#9e9e9e")
                        combo.setStyleSheet(f"QComboBox {{ color: {item_color}; font-weight: bold; }}")
                        break
                if not found:
                    # Equipped item no longer in inventory, clear it
                    self.blocker.adhd_buster["equipped"][slot] = None
                    combo.setCurrentIndex(0)
                    combo.setStyleSheet("")  # Reset style for empty slot
                    needs_save = True
            else:
                combo.setCurrentIndex(0)
                combo.setStyleSheet("")  # Reset style for empty slot
            
            combo.blockSignals(False)
        
        # Persist any equipped items that were cleared
        if needs_save:
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()

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
        self.inv_list.clear()
        self.merge_selected = []
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})

        rarity_order = {"Common": 0, "Uncommon": 1, "Rare": 2, "Epic": 3, "Legendary": 4}
        sort_key = self.sort_combo.currentText()

        indexed = list(enumerate(inventory))
        if sort_key == "rarity":
            indexed.sort(key=lambda x: rarity_order.get(x[1].get("rarity", "Common"), 0), reverse=True)
        elif sort_key == "slot":
            indexed.sort(key=lambda x: x[1].get("slot", ""))
        elif sort_key == "power":
            indexed.sort(key=lambda x: x[1].get("power", 10), reverse=True)
        else:
            indexed.reverse()

        for orig_idx, item in indexed:
            # Use robust equipped check that handles items with/without timestamps
            is_eq = self._is_item_equipped(item, equipped)
            prefix = "✓ " if is_eq else ""
            item_name = item.get("name", "Unknown Item")
            item_rarity = item.get("rarity", "Common")
            power = item.get("power", RARITY_POWER.get(item_rarity, 10))
            text = f"{prefix}{item_name} (+{power}) [{item_rarity[:1]}]"
            list_item = QtWidgets.QListWidgetItem(text)
            list_item.setData(QtCore.Qt.UserRole, orig_idx)
            # Add tooltip with full item details (use themed slot name)
            active_story = self.blocker.adhd_buster.get("active_story", "warrior")
            slot_display = get_slot_display_name(item.get('slot', 'Unknown'), active_story) if get_slot_display_name else item.get('slot', 'Unknown')
            list_item.setToolTip(
                f"{item_name}\n"
                f"Rarity: {item_rarity}\n"
                f"Slot: {slot_display}\n"
                f"Power: +{power}\n"
                f"{'[✓ EQUIPPED - unequip to merge]' if is_eq else '[Click to select for merge]'}"
            )
            # Block equipped items from being selected for merge
            if is_eq:
                list_item.setFlags(list_item.flags() & ~QtCore.Qt.ItemIsSelectable)
                list_item.setForeground(QtGui.QColor("#888888"))  # Gray out equipped
            else:
                list_item.setForeground(QtGui.QColor(item.get("color", "#333")))
            self.inv_list.addItem(list_item)

    def refresh_gear_combos(self) -> None:
        """Refresh gear dropdown combos to reflect new inventory items.
        
        This is called externally (e.g., after item drops), so it uses
        the comprehensive refresh_all() method.
        """
        self.refresh_all()

    def _update_merge_selection(self) -> None:
        self.merge_selected = [item.data(QtCore.Qt.UserRole) for item in self.inv_list.selectedItems()]
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        # Filter to only valid indices
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
                luck = self.blocker.adhd_buster.get("luck_bonus", 0)
                rate = calculate_merge_success_rate(items, luck)
                result_rarity = get_merge_result_rarity(items)
                self.merge_rate_lbl.setText(f"Success rate: {rate*100:.0f}% → {result_rarity} item")
        else:
            self.merge_btn.setEnabled(False)
            self.merge_rate_lbl.setText("Select 2+ items to merge")

    def _do_merge(self) -> None:
        if len(self.merge_selected) < 2:
            return
        if not GAMIFICATION_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Feature Unavailable", "Gamification features are not available.")
            return
        
        # Re-fetch inventory fresh to avoid stale indices
        inventory = self.blocker.adhd_buster.get("inventory", [])
        
        # Validate indices are still valid
        valid_indices = [idx for idx in self.merge_selected if 0 <= idx < len(inventory)]
        if len(valid_indices) < 2:
            QtWidgets.QMessageBox.warning(self, "Invalid Selection", 
                "Selected items are no longer valid. Please refresh and try again.")
            self._refresh_inventory()
            return
        
        items = [inventory[idx] for idx in valid_indices]
        
        # Check for items without timestamps (data integrity issue)
        items_without_ts = [i for i in items if not i.get("obtained_at")]
        if items_without_ts:
            # Add timestamps to fix data integrity
            for item in items_without_ts:
                item["obtained_at"] = datetime.now().isoformat()
            self.blocker.save_config()
        
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        rate = calculate_merge_success_rate(items, luck)
        result_rarity = get_merge_result_rarity(items)
        summary = "\n".join([f"  • {i.get('name', 'Unknown')} ({i.get('rarity', 'Common')})" for i in items])
        if QtWidgets.QMessageBox.question(
            self, "⚠️ Lucky Merge",
            f"Merge {len(items)} items?\n\n{summary}\n\nSuccess rate: {rate*100:.0f}%\n"
            f"On success: {result_rarity}+ item\nOn failure: ALL items LOST!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        ) != QtWidgets.QMessageBox.Yes:
            return
        
        # Re-fetch inventory again after dialog (user could have modified in another window)
        inventory = self.blocker.adhd_buster.get("inventory", [])
        
        # Re-validate indices after dialog
        if not all(0 <= idx < len(inventory) for idx in valid_indices):
            QtWidgets.QMessageBox.warning(self, "Inventory Changed", 
                "Inventory changed while dialog was open. Please try again.")
            self._refresh_inventory()
            return
        
        # Re-fetch items with fresh inventory
        items = [inventory[idx] for idx in valid_indices]
        
        # Final safety check: ensure no equipped items are being merged (using robust check)
        equipped = self.blocker.adhd_buster.get("equipped", {})
        equipped_in_merge = [i for i in items if self._is_item_equipped(i, equipped)]
        if equipped_in_merge:
            QtWidgets.QMessageBox.warning(
                self, "Cannot Merge",
                f"Cannot merge equipped items! Unequip them first.\n\n"
                f"Equipped items selected: {len(equipped_in_merge)}"
            )
            return
        
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        result = perform_lucky_merge(items, luck, story_id=active_story)
        
        # Remove merged items from inventory
        # Create a set of items to remove using multiple identifiers
        items_to_remove = set()
        for i in items:
            # Use timestamp if available
            if i.get("obtained_at"):
                items_to_remove.add(("ts", i.get("obtained_at")))
            # Also add name+slot+rarity as fallback identifier
            items_to_remove.add(("key", (i.get("name"), i.get("slot"), i.get("rarity"))))
        
        # Track which items have been removed (to handle duplicates correctly)
        removed_keys = set()
        new_inventory = []
        for item in inventory:
            item_ts = item.get("obtained_at")
            item_key = (item.get("name"), item.get("slot"), item.get("rarity"))
            
            # Check if this item should be removed
            should_remove = False
            if item_ts and ("ts", item_ts) in items_to_remove and ("ts", item_ts) not in removed_keys:
                should_remove = True
                removed_keys.add(("ts", item_ts))
            elif not item_ts and ("key", item_key) in items_to_remove:
                # For items without timestamp, remove only one instance
                remove_identifier = ("key_instance", item_key)
                if remove_identifier not in removed_keys:
                    should_remove = True
                    removed_keys.add(remove_identifier)
            
            if not should_remove:
                new_inventory.append(item)
        
        # Verify we removed the expected number of items
        expected_removal = len(items)
        actual_removal = len(inventory) - len(new_inventory)
        if actual_removal != expected_removal:
            # Fallback: use index-based deletion with item verification
            # Only delete if the item at index matches what we expected
            new_inventory = inventory.copy()
            removed_count = 0
            for idx in sorted(valid_indices, reverse=True):
                if idx < len(new_inventory):
                    item_at_idx = new_inventory[idx]
                    # Verify this is one of our target items
                    for target in items:
                        if (item_at_idx.get("name") == target.get("name") and
                            item_at_idx.get("slot") == target.get("slot") and
                            item_at_idx.get("rarity") == target.get("rarity")):
                            del new_inventory[idx]
                            removed_count += 1
                            break
            
            # If still couldn't remove expected amount, log warning but proceed
            if removed_count != expected_removal:
                import logging
                logging.warning(f"Merge removal mismatch: expected {expected_removal}, got {removed_count}")
        
        if result["success"]:
            new_inventory.append(result["result_item"])
            self.blocker.adhd_buster["inventory"] = new_inventory
            # Sync changes to active hero before saving
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()
            
            # Show result with tier upgrade info
            tier_info = ""
            if result.get("tier_jump", 1) > 1:
                tier_info = f" (+{result['tier_jump']} tiers! 🎯)"
            
            QtWidgets.QMessageBox.information(self, "🎉 MERGE SUCCESS!",
                f"Roll: {result['roll_pct']} (needed < {result['needed_pct']})\n\n"
                f"Created: {result['result_item']['name']}{tier_info}\n"
                f"Rarity: {result['result_item']['rarity']}, Power: +{result['result_item']['power']}")
        else:
            self.blocker.adhd_buster["inventory"] = new_inventory
            # Sync changes to active hero before saving
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()
            QtWidgets.QMessageBox.critical(self, "💔 Merge Failed!",
                f"Roll: {result['roll_pct']} (needed < {result['needed_pct']})\n\n"
                f"{len(items)} items lost forever.")
        
        # Comprehensive refresh after merge
        self.refresh_all()

    def _on_story_change(self, index: int) -> None:
        """Handle story selection change."""
        if not GAMIFICATION_AVAILABLE:
            return
        
        story_id = self.story_combo.currentData()
        if not story_id:
            return
        
        from gamification import select_story, get_selected_story
        current = get_selected_story(self.blocker.adhd_buster)
        
        if story_id != current:
            # Inform about switching to different hero
            reply = QtWidgets.QMessageBox.question(
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
        reply = QtWidgets.QMessageBox.warning(
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
        confirm = QtWidgets.QMessageBox.question(
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
            
            QtWidgets.QMessageBox.information(
                self, "Story Restarted",
                f"'{story_title}' has been reset!\n\n"
                f"Your hero begins anew at Chapter 1.\n"
                f"Good luck on your fresh journey! 🌟"
            )
        else:
            QtWidgets.QMessageBox.critical(
                self, "Error",
                "Failed to restart story. Please try again."
            )

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
            QtWidgets.QMessageBox.warning(self, "Story", "Story system requires gamification module.")
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

    def _open_diary(self) -> None:
        DiaryDialog(self.blocker, self).exec()

    def _optimize_gear(self) -> None:
        """Automatically equip the best gear for maximum power."""
        if not GAMIFICATION_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Optimize Gear", "Gamification module not available!")
            return
        
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        if not inventory and not any(equipped.values()):
            QtWidgets.QMessageBox.information(self, "Optimize Gear", "No gear available to optimize!")
            return
        
        # Calculate optimal gear
        result = optimize_equipped_gear(self.blocker.adhd_buster)
        
        if not result["changes"]:
            QtWidgets.QMessageBox.information(
                self, "Optimize Gear",
                "Your gear is already optimized! ⚔️\n\n"
                f"Current power: {result['old_power']}"
            )
            return
        
        # Show preview of changes
        changes_text = "\n".join(f"  • {c}" for c in result["changes"]) if result["changes"] else "  No changes needed"
        
        msg = (
            f"🔧 Gear Optimization Preview\n\n"
            f"Current Power: {result['old_power']}\n"
            f"Optimized Power: {result['new_power']}\n"
            f"Power Gain: +{result['power_gain']}\n\n"
            f"Changes:\n{changes_text}\n\n"
            f"Apply these changes?"
        )
        
        if QtWidgets.QMessageBox.question(
            self, "Optimize Gear", msg,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        ) != QtWidgets.QMessageBox.Yes:
            return
        
        # Apply the optimized gear
        self.blocker.adhd_buster["equipped"] = result["new_equipped"]
        
        # Sync changes to active hero before saving
        if GAMIFICATION_AVAILABLE:
            sync_hero_data(self.blocker.adhd_buster)
        self.blocker.save_config()
        
        # Show result message first
        if result["power_gain"] > 0:
            QtWidgets.QMessageBox.information(
                self, "Gear Optimized! ⚡",
                f"Power increased from {result['old_power']} to {result['new_power']}!\n"
                f"(+{result['power_gain']} power)"
            )
        else:
            QtWidgets.QMessageBox.information(
                self, "Gear Updated! ⚔️",
                f"Gear configuration updated.\nPower: {result['new_power']}"
            )
        
        # Comprehensive refresh after optimization
        self.refresh_all()

    def _salvage_duplicates(self) -> None:
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        if not inventory:
            QtWidgets.QMessageBox.information(self, "Salvage", "No items to salvage!")
            return
        equipped_ts = {item.get("obtained_at") for item in equipped.values() if item}
        slot_items: Dict[str, dict] = {}
        to_remove = []
        for item in inventory:
            slot = item.get("slot", "Unknown")
            power = item.get("power", 10)
            is_eq = item.get("obtained_at") in equipped_ts
            if is_eq:
                continue
            if slot not in slot_items:
                slot_items[slot] = {"best": item, "dups": []}
            elif power > slot_items[slot]["best"].get("power", 10):
                slot_items[slot]["dups"].append(slot_items[slot]["best"])
                slot_items[slot]["best"] = item
            else:
                slot_items[slot]["dups"].append(item)
        for data in slot_items.values():
            to_remove.extend(data["dups"])
        if not to_remove:
            QtWidgets.QMessageBox.information(self, "Salvage", "No duplicates found!")
            return
        luck_bonus = sum(i.get("power", 10) // 10 for i in to_remove)
        if QtWidgets.QMessageBox.question(
            self, "Salvage Duplicates",
            f"Salvage {len(to_remove)} duplicate items?\nLuck bonus earned: +{luck_bonus} 🍀",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        ) != QtWidgets.QMessageBox.Yes:
            return
        for item in to_remove:
            if item in inventory:
                inventory.remove(item)
        cur_luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        self.blocker.adhd_buster["luck_bonus"] = cur_luck + luck_bonus
        self.blocker.adhd_buster["inventory"] = inventory
        # Sync changes to active hero before saving
        if GAMIFICATION_AVAILABLE:
            sync_hero_data(self.blocker.adhd_buster)
        self.blocker.save_config()
        QtWidgets.QMessageBox.information(self, "Salvage Complete!", f"✨ Salvaged {len(to_remove)} items!\n🍀 Total luck: +{cur_luck + luck_bonus}")
        # Comprehensive refresh after salvage
        self.refresh_all()


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
        if QtWidgets.QMessageBox.question(self, "Clear Diary", "Clear all diary entries?") == QtWidgets.QMessageBox.Yes:
            self.blocker.adhd_buster["diary"] = []
            # Sync changes to active hero before saving
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()
            self.accept()

    def _write_entry(self) -> None:
        if not GAMIFICATION_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Diary", "Gamification not available")
            return
        today = datetime.now().strftime("%Y-%m-%d")
        diary = self.blocker.adhd_buster.get("diary", [])
        bonus_today = [e for e in diary if e.get("date") == today and e.get("story", "").startswith("[Bonus Entry]")]
        if bonus_today:
            QtWidgets.QMessageBox.information(self, "Diary", "You already wrote a bonus entry today!")
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
        # Auto-close after celebration
        close_time = 8000 + (self.levels_gained - 1) * 2000  # Longer for multi-level
        QtCore.QTimer.singleShot(close_time, self.accept)

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
        self.setWindowTitle("🎁 Item Drop!")
        self.setFixedSize(400, 280)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self._build_ui()
        close_time = {"Common": 8000, "Uncommon": 10000, "Rare": 12000, "Epic": 15000, "Legendary": 20000}
        QtCore.QTimer.singleShot(close_time.get(item["rarity"], 10000), self.accept)

    def _build_ui(self) -> None:
        bg_colors = {"Common": "#f5f5f5", "Uncommon": "#e8f5e9", "Rare": "#e3f2fd", "Epic": "#f3e5f5", "Legendary": "#fff3e0"}
        bg = bg_colors.get(self.item["rarity"], "#f5f5f5")
        self.setStyleSheet(f"background-color: {bg};")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        if self.item.get("lucky_upgrade"):
            header_text = "🍀 LUCKY UPGRADE! 🍀"
        elif self.item["rarity"] == "Legendary":
            header_text = "⭐ LEGENDARY DROP! ⭐"
        elif self.item["rarity"] == "Epic":
            header_text = "💎 EPIC DROP! 💎"
        else:
            header_text = "✨ LOOT DROP! ✨"
        header_lbl = QtWidgets.QLabel(header_text)
        header_lbl.setAlignment(QtCore.Qt.AlignCenter)
        header_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        layout.addWidget(header_lbl)
        found_lbl = QtWidgets.QLabel("Your ADHD Buster found:")
        found_lbl.setStyleSheet("color: #333;")
        layout.addWidget(found_lbl)
        name_lbl = QtWidgets.QLabel(self.item["name"])
        name_lbl.setStyleSheet(f"color: {self.item['color']}; font-size: 12px; font-weight: bold;")
        name_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(name_lbl)
        power = self.item.get("power", RARITY_POWER.get(self.item["rarity"], 10))
        # Get themed slot display name
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        slot_display = get_slot_display_name(self.item['slot'], active_story) if get_slot_display_name else self.item['slot']
        info_lbl = QtWidgets.QLabel(f"[{self.item['rarity']} {slot_display}] +{power} Power")
        info_lbl.setStyleSheet(f"color: {self.item['color']};")
        info_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(info_lbl)

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
        msg = random.choice(messages.get(self.item["rarity"], messages["Common"]))
        msg_lbl = QtWidgets.QLabel(msg)
        msg_lbl.setStyleSheet("font-weight: bold; color: #555;")
        msg_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(msg_lbl)
        adventure_lbl = QtWidgets.QLabel("📖 Your adventure awaits...")
        adventure_lbl.setStyleSheet("color: #555;")
        layout.addWidget(adventure_lbl)
        dismiss_lbl = QtWidgets.QLabel("(Click anywhere or wait to dismiss)")
        dismiss_lbl.setStyleSheet("color: #777; font-size: 10px;")
        layout.addWidget(dismiss_lbl)

    def mousePressEvent(self, event) -> None:
        self.accept()


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
        story_len = len(entry.get("story", ""))
        close_time = max(20000, min(45000, story_len * 100))
        QtCore.QTimer.singleShot(close_time, self.accept)

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
        dismiss_lbl = QtWidgets.QLabel("(Click anywhere or wait to dismiss)")
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
        if self.time_spins:
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
        QtCore.QTimer.singleShot(60000, self.reject)  # Auto-close after 60s

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(QtWidgets.QLabel("<b style='font-size:14px;'>🎯 Quick Check-in</b>"))
        layout.addWidget(QtWidgets.QLabel("Are you currently working on your priority tasks?"))

        if GAMIFICATION_AVAILABLE:
            streak = self.blocker.stats.get("streak_days", 0)
            bonuses = calculate_rarity_bonuses(self.session_minutes, streak)
            luck = self.blocker.adhd_buster.get("luck_bonus", 0)
            bonus_parts = []
            if bonuses["session_bonus"] > 0:
                bonus_parts.append(f"⏱️+{bonuses['session_bonus']}%")
            if bonuses["streak_bonus"] > 0:
                bonus_parts.append(f"🔥+{bonuses['streak_bonus']}%")
            if luck > 0:
                bonus_parts.append(f"🍀+{min(luck, 100)}%")
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
        QtWidgets.QMessageBox.information(self, "💪 Time to refocus!",
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
        self.priorities = list(self.blocker.priorities) if self.blocker.priorities else []
        while len(self.priorities) < 3:
            self.priorities.append({"title": "", "days": [], "active": False})
        self.title_edits: list = []
        self.day_checks: list = []
        self.planned_spins: list = []
        self.priority_groups: list = []
        self.complete_buttons: list = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        header = QtWidgets.QHBoxLayout()
        header.addWidget(QtWidgets.QLabel("<b style='font-size:16px;'>🎯 My Priorities</b>"))
        header.addStretch()
        today = datetime.now().strftime("%A, %B %d")
        header.addWidget(QtWidgets.QLabel(today))
        layout.addLayout(header)

        layout.addWidget(QtWidgets.QLabel("Set up to 3 priority tasks. These can span multiple days."))

        for i in range(3):
            self._create_priority_row(layout, i)

        # Today's Focus
        today_box = QtWidgets.QGroupBox("📌 Today's Focus")
        today_layout = QtWidgets.QVBoxLayout(today_box)
        self.today_lbl = QtWidgets.QLabel()
        today_layout.addWidget(self.today_lbl)
        layout.addWidget(today_box)
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

    def _create_priority_row(self, parent_layout: QtWidgets.QVBoxLayout, index: int) -> None:
        group = QtWidgets.QGroupBox(f"Priority #{index + 1}")
        self.priority_groups.append(group)
        g_layout = QtWidgets.QVBoxLayout(group)

        # Title row with complete button
        title_row = QtWidgets.QHBoxLayout()
        title_edit = QtWidgets.QLineEdit(self.priorities[index].get("title", ""))
        title_edit.setPlaceholderText("Enter priority title...")
        title_row.addWidget(title_edit)
        
        complete_btn = QtWidgets.QPushButton("✅ Complete")
        complete_btn.setToolTip("Mark this priority as complete and roll for a Lucky Gift!")
        complete_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        complete_btn.clicked.connect(lambda checked, idx=index: self._complete_priority(idx))
        title_row.addWidget(complete_btn)
        self.complete_buttons.append(complete_btn)
        
        g_layout.addLayout(title_row)
        self.title_edits.append(title_edit)

        days_layout = QtWidgets.QHBoxLayout()
        days_layout.addWidget(QtWidgets.QLabel("Days:"))
        day_checks = []
        saved_days = self.priorities[index].get("days", [])
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
        planned_spin.setValue(self.priorities[index].get("planned_hours", 0))
        planned_layout.addWidget(planned_spin)
        
        logged = self.priorities[index].get("logged_hours", 0)
        planned = self.priorities[index].get("planned_hours", 0)
        
        # Progress bar
        if planned > 0:
            p_bar = QtWidgets.QProgressBar()
            p_bar.setMaximum(100)
            pct = min(100, int((logged / planned) * 100))
            p_bar.setValue(pct)
            p_bar.setFormat(f"{logged:.1f}/{planned:.1f} hrs ({pct}%)")
            p_bar.setFixedWidth(150)
            planned_layout.addWidget(p_bar)
        else:
            planned_layout.addWidget(QtWidgets.QLabel(f"Logged: {logged:.1f} hrs"))
            
        planned_layout.addStretch()
        self.planned_spins.append(planned_spin)
        g_layout.addLayout(planned_layout)

        parent_layout.addWidget(group)

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
        for i in range(3):
            self.priorities[i]["title"] = self.title_edits[i].text().strip()
            self.priorities[i]["days"] = [day for day, cb in self.day_checks[i] if cb.isChecked()]
            self.priorities[i]["planned_hours"] = self.planned_spins[i].value()
        self.blocker.priorities = self.priorities
        self.blocker.save_config()
        self._refresh_today_focus()
        QtWidgets.QMessageBox.information(self, "Saved", "Priorities saved!")

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
            QtWidgets.QMessageBox.warning(self, "No Priority", 
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
        title = self.title_edits[index].text().strip()
        if not title:
            QtWidgets.QMessageBox.warning(self, "No Priority", 
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
        reply = QtWidgets.QMessageBox.question(
            self, "Complete Priority?",
            f"🎯 Mark '{title}' as COMPLETE?\n\n"
            f"You'll get a chance to win a Lucky Gift!\n"
            f"(🎰 {chance}% chance based on {logged_hours:.1f}h logged)",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        
        # Roll for reward with story theme and logged hours
        from gamification import roll_priority_completion_reward
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        result = roll_priority_completion_reward(story_id=active_story, logged_hours=logged_hours)
        
        if result["won"]:
            item = result["item"]
            rarity_color = item.get("color", "#ffffff")
            
            # Add to inventory (use the proper adhd_buster reference)
            if "inventory" not in self.blocker.adhd_buster:
                self.blocker.adhd_buster["inventory"] = []
            self.blocker.adhd_buster["inventory"].append(item)
            self.blocker.adhd_buster["total_collected"] = self.blocker.adhd_buster.get("total_collected", 0) + 1
            # Sync changes to active hero before saving
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()
            
            # Show win dialog
            msg = QtWidgets.QMessageBox(self)
            msg.setWindowTitle("🎁 Lucky Gift!")
            msg.setText(f"<h2 style='color: {rarity_color};'>🎉 YOU WON! 🎉</h2>")
            slot_display = get_slot_display_name(item['slot'], active_story) if get_slot_display_name else item['slot']
            msg.setInformativeText(
                f"<p style='font-size: 14px;'>{result['message']}</p>"
                f"<p style='font-size: 16px; color: {rarity_color}; font-weight: bold;'>"
                f"{item['name']}</p>"
                f"<p><b>Rarity:</b> <span style='color: {rarity_color};'>{item['rarity']}</span><br>"
                f"<b>Slot:</b> {slot_display}<br>"
                f"<b>Power:</b> +{item['power']}</p>"
                f"<p><i>Check your ADHD Buster inventory!</i></p>"
            )
            msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
            msg.exec()
        else:
            QtWidgets.QMessageBox.information(
                self, "Priority Complete!",
                f"✅ '{title}' marked as complete!\n\n"
                f"🎲 {result['message']}"
            )
        
        # Clear the completed priority
        self.priorities[index] = {"title": "", "days": [], "active": False, "planned_hours": 0, "logged_hours": 0}
        self.title_edits[index].setText("")
        for day, cb in self.day_checks[index]:
            cb.setChecked(False)
        self.planned_spins[index].setValue(0)
        
        # Save and refresh
        self.blocker.priorities = self.priorities
        self.blocker.save_config()
        self._refresh_today_focus()


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


class FocusBlockerWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"Personal Liberty v{APP_VERSION}")
        self.resize(900, 700)

        self.blocker = BlockerCore()

        # Menu bar
        self._create_menu_bar()

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
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

        quick_bar.addStretch()
        self.admin_label = QtWidgets.QLabel()
        quick_bar.addWidget(self.admin_label)
        main_layout.addLayout(quick_bar)

        self._update_admin_label()

        self.tabs = QtWidgets.QTabWidget()
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
        self.tabs.addTab(self.stats_tab, "📊 Stats")

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

        # ADHD Buster tab (gamification)
        if GAMIFICATION_AVAILABLE:
            self.adhd_tab = ADHDBusterTab(self.blocker, self)
            self.tabs.addTab(self.adhd_tab, "🦸 Hero")

        if AI_AVAILABLE:
            self.ai_tab = AITab(self.blocker, self)
            self.tabs.addTab(self.ai_tab, "🧠 AI Insights")

        self.statusBar().showMessage(f"Personal Liberty v{APP_VERSION}")

        # System Tray setup
        self.tray_icon = None
        self.minimize_to_tray = self.blocker.minimize_to_tray  # Load from config
        
        self._setup_system_tray()

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
        msgbox.setIcon(QtWidgets.QMessageBox.Warning)
        msgbox.setWindowTitle("Crash Recovery Detected")
        msgbox.setText(f"⚠️ {crash_info} did not shut down properly.\n\nSome websites may still be blocked.")
        msgbox.setInformativeText("Would you like to remove all blocks and clean up?")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.Yes)
        msgbox.button(QtWidgets.QMessageBox.Yes).setText("Remove Blocks")
        msgbox.button(QtWidgets.QMessageBox.No).setText("Keep Blocks")
        msgbox.button(QtWidgets.QMessageBox.Cancel).setText("Decide Later")

        response = msgbox.exec()

        if response == QtWidgets.QMessageBox.Yes:
            success, message = self.blocker.recover_from_crash()
            if success:
                QtWidgets.QMessageBox.information(self, "Recovery Complete", "✅ All blocks have been removed.\n\nYour browser should now be able to access all websites.")
            else:
                QtWidgets.QMessageBox.critical(self, "Recovery Failed", f"Could not clean up: {message}\n\nTry using 'Emergency Cleanup' in Settings tab.")
        elif response == QtWidgets.QMessageBox.No:
            self.blocker.clear_session_state()
            QtWidgets.QMessageBox.information(self, "Blocks Retained", "The blocks have been kept.\n\nUse 'Emergency Cleanup' in Settings tab when you want to remove them.")

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

    def _check_scheduled_blocking(self) -> None:
        """Check if we should be blocking based on schedule."""
        if self.blocker.is_scheduled_block_time() and not self.blocker.is_blocking:
            result = QtWidgets.QMessageBox.question(
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
            
            # Add to inventory
            if "inventory" not in self.blocker.adhd_buster:
                self.blocker.adhd_buster["inventory"] = []
            self.blocker.adhd_buster["inventory"].append(item)
            self.blocker.adhd_buster["total_collected"] = self.blocker.adhd_buster.get("total_collected", 0) + 1
            # Sync changes to active hero before saving
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()
            
            # Show reward dialog with themed slot name
            current_tier = get_current_tier(self.blocker.adhd_buster)
            boosted_tier = get_boosted_rarity(current_tier)
            slot_display = get_slot_display_name(item['slot'], active_story) if get_slot_display_name else item['slot']
            
            QtWidgets.QMessageBox.information(
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
        self.tabs.setCurrentWidget(self.timer_tab)
        QtWidgets.QMessageBox.information(self, "Priority Session", 
                                   f"Starting focus session for:\n\n\"{priority_title}\"\n\n"
                                   "Set your desired duration and click Start Focus!")

    def _open_adhd_buster(self) -> None:
        """Switch to the ADHD Buster tab."""
        if not GAMIFICATION_AVAILABLE or not hasattr(self, 'adhd_tab'):
            QtWidgets.QMessageBox.warning(
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
        # Extra warning for strict/hardcore modes
        mode = getattr(self.blocker, 'mode', None)
        if mode in (BlockMode.STRICT, BlockMode.HARDCORE) and self.blocker.is_blocking:
            reply = QtWidgets.QMessageBox.warning(
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
        
        if QtWidgets.QMessageBox.question(self, "Emergency Cleanup",
            "Remove ALL blocks and clean system?") == QtWidgets.QMessageBox.Yes:
            success, message = self.blocker.emergency_cleanup()
            if success:
                QtWidgets.QMessageBox.information(self, "Cleanup Complete", message)
            else:
                QtWidgets.QMessageBox.critical(self, "Cleanup Failed", message)

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

        if self.timer_tab.timer_running:
            # For Hardcore mode, require solving the challenge to exit
            if self.timer_tab.blocker.mode == BlockMode.HARDCORE:
                reply = QtWidgets.QMessageBox.question(
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
            
            reply = QtWidgets.QMessageBox.question(
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

    def _on_session_complete(self, elapsed_seconds: int) -> None:
        """Handle session completion - refresh stats and related UI."""
        # Reload stats from file to ensure we have latest data
        self.blocker.load_stats()
        
        # Refresh the stats tab to show updated focus time
        if hasattr(self, 'stats_tab'):
            self.stats_tab.refresh()
        
        # Refresh AI tab if available
        if AI_AVAILABLE and hasattr(self, 'ai_tab'):
            self.ai_tab._refresh_data()
        
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
        msg_box.setIcon(QtWidgets.QMessageBox.Question)
        
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
                QtWidgets.QMessageBox.warning(
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
                QtWidgets.QMessageBox.critical(
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
    
    splash.set_status("Creating main window...")
    
    window = FocusBlockerWindow()
    
    # Close splash and show main window
    splash.close()
    
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
