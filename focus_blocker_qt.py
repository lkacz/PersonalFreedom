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
LOCAL_AI_AVAILABLE = False
GOALS_PATH = None
STATS_PATH = None
BYPASS_LOGGER_AVAILABLE = False
ProductivityAnalyzer = None
GamificationEngine = None
FocusGoals = None
LocalAI = None
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


def load_heavy_modules(splash: Optional[SplashScreen] = None):
    """Load heavy modules with splash screen updates."""
    global BlockerCore, BlockMode, SITE_CATEGORIES, AI_AVAILABLE, LOCAL_AI_AVAILABLE
    global GOALS_PATH, STATS_PATH, BYPASS_LOGGER_AVAILABLE
    global ProductivityAnalyzer, GamificationEngine, FocusGoals, LocalAI
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
    
    if splash:
        splash.set_status("Loading core modules...")
    
    from core_logic import (
        BlockerCore as _BlockerCore,
        BlockMode as _BlockMode,
        SITE_CATEGORIES as _SITE_CATEGORIES,
        AI_AVAILABLE as _AI_AVAILABLE,
        LOCAL_AI_AVAILABLE as _LOCAL_AI_AVAILABLE,
        GOALS_PATH as _GOALS_PATH,
        STATS_PATH as _STATS_PATH,
        BYPASS_LOGGER_AVAILABLE as _BYPASS_LOGGER_AVAILABLE,
    )
    BlockerCore = _BlockerCore
    BlockMode = _BlockMode
    SITE_CATEGORIES = _SITE_CATEGORIES
    AI_AVAILABLE = _AI_AVAILABLE
    LOCAL_AI_AVAILABLE = _LOCAL_AI_AVAILABLE
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
    
    # Local AI for session analysis
    if LOCAL_AI_AVAILABLE:
        if splash:
            splash.set_status("Loading local AI models...")
        from local_ai import LocalAI as _LocalAI
        LocalAI = _LocalAI
    
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
        )
        GAMIFICATION_AVAILABLE = True
        RARITY_POWER = _RARITY_POWER
        ITEM_THEMES = _ITEM_THEMES
        get_item_themes = _get_item_themes
        get_diary_power_tier = _get_diary_power_tier
        calculate_character_power = _calculate_character_power
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
    except ImportError:
        GAMIFICATION_AVAILABLE = False
    
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
        self.setMinimumWidth(500)
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
        # Create a pixmap
        width, height = 400, 60
        pixmap = QtGui.QPixmap(width, height)
        pixmap.fill(QtCore.Qt.transparent)
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Use a monospace font for clear number display
        font = QtGui.QFont("Consolas", 28, QtGui.QFont.Bold)
        painter.setFont(font)
        painter.setPen(QtGui.QColor("#00ff88"))
        
        # Format the expression
        expression = f"{a:,}  {op}  {b:,}  =  ?"
        
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

        layout.addStretch(1)

    def _connect_signals(self) -> None:
        self.start_btn.clicked.connect(self._start_session)
        self.stop_btn.clicked.connect(self._stop_session)

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
        hours = self.hours_spin.value()
        minutes = self.minutes_spin.value()
        total_minutes = hours * 60 + minutes
        if total_minutes <= 0:
            QtWidgets.QMessageBox.warning(self, "Invalid Duration", "Please set a time greater than 0 minutes.")
            return

        mode = self._current_mode()
        self.blocker.mode = mode

        # Reset Pomodoro state
        self.pomodoro_is_break = False
        self.pomodoro_session_count = 0
        self.pomodoro_total_work_time = 0
        self.last_checkin_time = None

        # Pomodoro uses its own durations
        if mode == BlockMode.POMODORO:
            total_seconds = self.blocker.pomodoro_work * 60
            self.status_label.setText(f"🍅 WORK #{self.pomodoro_session_count + 1}")
        else:
            total_seconds = total_minutes * 60

        success, message = self.blocker.block_sites(duration_seconds=total_seconds)
        if not success:
            QtWidgets.QMessageBox.critical(self, "Cannot Start Session", message)
            return

        self.timer_running = True
        self.remaining_seconds = total_seconds
        self.session_start = QtCore.QDateTime.currentDateTime().toSecsSinceEpoch()
        self.timer_label.setText(self._format_time(self.remaining_seconds))
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        if mode != BlockMode.POMODORO:
            self.status_label.setText("🔒 BLOCKING")
        self.qt_timer.start()

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

        if elapsed > 0 and elapsed % interval_seconds < 2:  # 2-second window
            if self.last_checkin_time is None or (elapsed - self.last_checkin_time) >= interval_seconds - 5:
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
        """Give item drop and diary entry rewards."""
        if not GAMIFICATION_AVAILABLE:
            return
        # Skip if gamification mode is disabled
        if not is_gamification_enabled(self.blocker.adhd_buster):
            return

        streak = self.blocker.stats.get("streak_days", 0)
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        
        # Get active story for themed item generation
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")

        # Generate item (generate_item already imported at top)
        item = generate_item(session_minutes=session_minutes, streak_days=streak,
                              story_id=active_story)

        # Lucky upgrade chance based on luck bonus
        luck_chance = min(luck / 100, 10)
        if luck > 0 and random.random() * 100 < luck_chance:
            rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
            current_idx = rarity_order.index(item["rarity"])
            if current_idx < len(rarity_order) - 1:
                item = generate_item(rarity=rarity_order[current_idx + 1],
                                      session_minutes=session_minutes, streak_days=streak,
                                      story_id=active_story)
                item["lucky_upgrade"] = True

        # Add to inventory
        if "inventory" not in self.blocker.adhd_buster:
            self.blocker.adhd_buster["inventory"] = []
        self.blocker.adhd_buster["inventory"].append(item)
        self.blocker.adhd_buster["total_collected"] = self.blocker.adhd_buster.get("total_collected", 0) + 1

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

        # Show item drop dialog
        ItemDropDialog(self.blocker, item, session_minutes, streak, self.window()).exec()

        # Refresh ADHD dialog if open (so new gear shows in dropdowns)
        main_window = self.window()
        if hasattr(main_window, 'refresh_adhd_dialog'):
            main_window.refresh_adhd_dialog()

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

        self.timer_label.setText("00:00:00")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Session complete 🎉")

        # Update tray icon to ready state
        main_window = self.window()
        if hasattr(main_window, '_update_tray_icon'):
            main_window._update_tray_icon(blocking=False)

        session_minutes = elapsed // 60

        # Show AI session dialog if available, otherwise simple message
        main_window = self.window()
        if LOCAL_AI_AVAILABLE and hasattr(main_window, 'show_ai_session_complete'):
            main_window.show_ai_session_complete(elapsed)
        else:
            QtWidgets.QMessageBox.information(self, "Complete!", "🎉 Focus session complete!\nGreat job staying focused!")

        if session_minutes > 0:
            self._give_session_rewards(session_minutes)
            self._show_priority_time_log(session_minutes)

        self.session_complete.emit(elapsed)

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
            self.blocker.unblock_sites(force=True)

            # Give rewards for completing work session
            session_minutes = elapsed // 60
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
        self.local_ai = LocalAI() if LOCAL_AI_AVAILABLE else None
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


class AITab(QtWidgets.QWidget):
    """AI insights tab - productivity coach, achievements, goals, challenges."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        # Initialize AI/gamification components
        self.analyzer = ProductivityAnalyzer(STATS_PATH) if ProductivityAnalyzer else None
        self.gamification = GamificationEngine(STATS_PATH) if GamificationEngine else None
        self.focus_goals = FocusGoals(GOALS_PATH, STATS_PATH) if FocusGoals else None
        self.local_ai = LocalAI() if LOCAL_AI_AVAILABLE else None
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

        # GPU AI insights
        if LOCAL_AI_AVAILABLE:
            gpu_group = QtWidgets.QGroupBox("🚀 GPU AI Insights")
            gpu_layout = QtWidgets.QVBoxLayout(gpu_group)
            self.gpu_status_label = QtWidgets.QLabel()
            gpu_layout.addWidget(self.gpu_status_label)
            self.triggers_text = QtWidgets.QTextEdit()
            self.triggers_text.setReadOnly(True)
            self.triggers_text.setMaximumHeight(120)
            gpu_layout.addWidget(self.triggers_text)
            self.mood_text = QtWidgets.QTextEdit()
            self.mood_text.setReadOnly(True)
            self.mood_text.setMaximumHeight(80)
            gpu_layout.addWidget(self.mood_text)
            inner.addWidget(gpu_group)

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
                    remaining = prog["target"] - prog["current"]
                    challenge_text = f"{data['icon']} {data['name']}: {data.get('description', '')} — {prog['current']}/{prog['target']} ({remaining} to go!)"
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

        # GPU insights
        if self.local_ai:
            status_txt = "✅ Running on GPU" if self.local_ai.gpu_available else "💻 Running on CPU"
            self.gpu_status_label.setText(status_txt)

            # Extract notes from session_notes, handling both dict and string formats
            raw_notes = self.blocker.stats.get("session_notes", [])
            notes = []
            for n in raw_notes:
                if isinstance(n, dict):
                    note_text = n.get("note", "")
                    if note_text:
                        notes.append(note_text)
                elif isinstance(n, str) and n:
                    notes.append(n)
            
            if len(notes) >= 3:
                try:
                    triggers = self.local_ai.detect_distraction_triggers(notes)
                    if triggers:
                        lines = [f"• {t['trigger']} ({t['frequency']}) — {t['recommendation']}" for t in triggers]
                        self.triggers_text.setPlainText("\n".join(lines))
                    else:
                        self.triggers_text.setPlainText("No common distraction triggers detected yet.")
                except Exception:
                    self.triggers_text.setPlainText("GPU insights unavailable (missing ML deps).")
            else:
                self.triggers_text.setPlainText("Add at least 3 session notes to analyze distraction triggers.")

            if notes:
                try:
                    mood = self.local_ai.analyze_focus_quality(notes[-1])
                    if mood:
                        self.mood_text.setPlainText(f"Last session sentiment: {mood['interpretation']}")
                    else:
                        self.mood_text.setPlainText("Add a session note to see mood analysis.")
                except Exception:
                    self.mood_text.setPlainText("Mood analysis unavailable (missing ML deps).")

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

    def __init__(self, equipped: dict, power: int, width: int = 180, height: int = 220,
                 parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.equipped = equipped
        self.power = power
        self.setFixedSize(width, height)
        if GAMIFICATION_AVAILABLE:
            self.tier = get_diary_power_tier(power)
        else:
            self.tier = "pathetic" if power < 50 else "modest" if power < 150 else "decent"

    def paintEvent(self, event) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2 + 5

        # Background with subtle gradient
        gradient = QtGui.QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QtGui.QColor("#3d3d3d"))
        gradient.setColorAt(1, QtGui.QColor("#252525"))
        painter.fillRect(self.rect(), gradient)
        
        # Floor shadow
        painter.setBrush(QtGui.QColor(0, 0, 0, 60))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(cx - 35, cy + 70, 70, 15)

        body_color = QtGui.QColor(self.TIER_COLORS.get(self.tier, "#bdbdbd"))
        body_outline = QtGui.QColor(self.TIER_OUTLINE.get(self.tier, "#888"))
        glow = self.TIER_GLOW.get(self.tier)

        def darken(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.darker(amount)
        
        def lighten(color: str, amount: int = 130) -> QtGui.QColor:
            c = QtGui.QColor(color)
            return c.lighter(amount)

        # Glow aura for high tiers
        if glow:
            painter.setBrush(QtGui.QColor(glow))
            painter.setPen(QtCore.Qt.NoPen)
            painter.setOpacity(0.4)
            painter.drawEllipse(cx - 55, cy - 65, 110, 145)
            painter.setOpacity(0.2)
            painter.drawEllipse(cx - 65, cy - 75, 130, 165)
            painter.setOpacity(1.0)

        # === CLOAK (behind body) ===
        cloak = self.equipped.get("Cloak")
        if cloak:
            cc = QtGui.QColor(cloak.get("color", "#666"))
            # Flowing cloak shape
            path = QtGui.QPainterPath()
            path.moveTo(cx - 22, cy - 28)
            path.lineTo(cx + 22, cy - 28)
            path.quadTo(cx + 38, cy + 20, cx + 32, cy + 65)
            path.lineTo(cx - 32, cy + 65)
            path.quadTo(cx - 38, cy + 20, cx - 22, cy - 28)
            painter.setBrush(cc)
            painter.setPen(QtGui.QPen(darken(cloak.get("color", "#666")), 2))
            painter.drawPath(path)
            # Cloak inner shadow
            painter.setBrush(darken(cloak.get("color", "#666"), 150))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(cx - 18, cy - 25, 8, 50)

        # === LEGS ===
        painter.setBrush(body_color)
        painter.setPen(QtGui.QPen(body_outline, 2))
        # Left leg with slight shape
        leg_path_l = QtGui.QPainterPath()
        leg_path_l.moveTo(cx - 18, cy + 22)
        leg_path_l.lineTo(cx - 5, cy + 22)
        leg_path_l.lineTo(cx - 6, cy + 55)
        leg_path_l.lineTo(cx - 17, cy + 55)
        leg_path_l.closeSubpath()
        painter.drawPath(leg_path_l)
        # Right leg
        leg_path_r = QtGui.QPainterPath()
        leg_path_r.moveTo(cx + 5, cy + 22)
        leg_path_r.lineTo(cx + 18, cy + 22)
        leg_path_r.lineTo(cx + 17, cy + 55)
        leg_path_r.lineTo(cx + 6, cy + 55)
        leg_path_r.closeSubpath()
        painter.drawPath(leg_path_r)

        # === BOOTS ===
        boots = self.equipped.get("Boots")
        if boots:
            bc = QtGui.QColor(boots.get("color", "#666"))
            painter.setBrush(bc)
            painter.setPen(QtGui.QPen(bc.darker(130), 2))
            # Left boot with toe
            painter.drawRoundedRect(cx - 20, cy + 52, 18, 22, 3, 3)
            painter.drawEllipse(cx - 22, cy + 68, 12, 8)  # Toe
            # Right boot
            painter.drawRoundedRect(cx + 2, cy + 52, 18, 22, 3, 3)
            painter.drawEllipse(cx + 10, cy + 68, 12, 8)  # Toe
            # Boot details - straps
            painter.setPen(QtGui.QPen(bc.darker(150), 1))
            painter.drawLine(cx - 18, cy + 58, cx - 4, cy + 58)
            painter.drawLine(cx + 4, cy + 58, cx + 18, cy + 58)
        else:
            # Simple feet
            painter.setBrush(QtGui.QColor("#8d6e63"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#5d4037"), 1))
            painter.drawRoundedRect(cx - 18, cy + 55, 14, 16, 3, 3)
            painter.drawRoundedRect(cx + 4, cy + 55, 14, 16, 3, 3)

        # === ARMS ===
        painter.setBrush(body_color)
        painter.setPen(QtGui.QPen(body_outline, 2))
        # Left arm - slightly angled
        arm_path_l = QtGui.QPainterPath()
        arm_path_l.moveTo(cx - 28, cy - 22)
        arm_path_l.lineTo(cx - 38, cy - 18)
        arm_path_l.lineTo(cx - 42, cy + 18)
        arm_path_l.lineTo(cx - 28, cy + 15)
        arm_path_l.closeSubpath()
        painter.drawPath(arm_path_l)
        # Right arm
        arm_path_r = QtGui.QPainterPath()
        arm_path_r.moveTo(cx + 28, cy - 22)
        arm_path_r.lineTo(cx + 38, cy - 18)
        arm_path_r.lineTo(cx + 42, cy + 18)
        arm_path_r.lineTo(cx + 28, cy + 15)
        arm_path_r.closeSubpath()
        painter.drawPath(arm_path_r)

        # === GAUNTLETS ===
        gaunt = self.equipped.get("Gauntlets")
        if gaunt:
            gc = QtGui.QColor(gaunt.get("color", "#666"))
            painter.setBrush(gc)
            painter.setPen(QtGui.QPen(gc.darker(130), 2))
            # Left gauntlet with knuckles
            painter.drawRoundedRect(cx - 46, cy + 8, 22, 22, 4, 4)
            # Finger details
            painter.setPen(QtGui.QPen(gc.darker(150), 1))
            for i in range(3):
                painter.drawLine(cx - 44 + i * 6, cy + 12, cx - 44 + i * 6, cy + 26)
            # Right gauntlet
            painter.setBrush(gc)
            painter.setPen(QtGui.QPen(gc.darker(130), 2))
            painter.drawRoundedRect(cx + 24, cy + 8, 22, 22, 4, 4)
            painter.setPen(QtGui.QPen(gc.darker(150), 1))
            for i in range(3):
                painter.drawLine(cx + 26 + i * 6, cy + 12, cx + 26 + i * 6, cy + 26)
        else:
            # Simple hands
            painter.setBrush(QtGui.QColor("#ffcc80"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#e6a84d"), 1))
            painter.drawEllipse(cx - 44, cy + 12, 14, 14)
            painter.drawEllipse(cx + 30, cy + 12, 14, 14)

        # === TORSO ===
        painter.setBrush(body_color)
        painter.setPen(QtGui.QPen(body_outline, 2))
        torso_path = QtGui.QPainterPath()
        torso_path.moveTo(cx - 25, cy - 28)
        torso_path.lineTo(cx + 25, cy - 28)
        torso_path.lineTo(cx + 22, cy + 25)
        torso_path.lineTo(cx - 22, cy + 25)
        torso_path.closeSubpath()
        painter.drawPath(torso_path)

        # === CHESTPLATE ===
        chest = self.equipped.get("Chestplate")
        if chest:
            cc = QtGui.QColor(chest.get("color", "#666"))
            painter.setBrush(cc)
            painter.setPen(QtGui.QPen(cc.darker(130), 2))
            # Main plate
            chest_path = QtGui.QPainterPath()
            chest_path.moveTo(cx - 22, cy - 26)
            chest_path.lineTo(cx + 22, cy - 26)
            chest_path.lineTo(cx + 19, cy + 22)
            chest_path.lineTo(cx - 19, cy + 22)
            chest_path.closeSubpath()
            painter.drawPath(chest_path)
            # Center line detail
            painter.setPen(QtGui.QPen(cc.darker(140), 2))
            painter.drawLine(cx, cy - 24, cx, cy + 18)
            # Shoulder pads
            painter.setBrush(cc.darker(110))
            painter.setPen(QtGui.QPen(cc.darker(140), 1))
            painter.drawEllipse(cx - 28, cy - 28, 14, 10)
            painter.drawEllipse(cx + 14, cy - 28, 14, 10)
            # Chest emblem (small circle)
            painter.setBrush(cc.lighter(120))
            painter.setPen(QtGui.QPen(cc.darker(120), 1))
            painter.drawEllipse(cx - 5, cy - 15, 10, 10)
        else:
            # Simple tunic lines
            painter.setPen(QtGui.QPen(body_outline, 1))
            painter.drawLine(cx, cy - 25, cx, cy + 20)

        # === HEAD ===
        # Neck
        painter.setBrush(QtGui.QColor("#ffcc80"))
        painter.setPen(QtGui.QPen(QtGui.QColor("#e6a84d"), 1))
        painter.drawRect(cx - 8, cy - 35, 16, 10)
        
        # Head shape (slightly oval)
        head_gradient = QtGui.QRadialGradient(cx, cy - 50, 25)
        head_gradient.setColorAt(0, QtGui.QColor("#ffe0b2"))
        head_gradient.setColorAt(0.7, QtGui.QColor("#ffcc80"))
        head_gradient.setColorAt(1, QtGui.QColor("#e6a84d"))
        painter.setBrush(head_gradient)
        painter.setPen(QtGui.QPen(QtGui.QColor("#d4943a"), 2))
        painter.drawEllipse(cx - 20, cy - 70, 40, 38)

        # === HELMET (if equipped) ===
        helm = self.equipped.get("Helmet")
        if helm:
            hc = QtGui.QColor(helm.get("color", "#666"))
            painter.setBrush(hc)
            painter.setPen(QtGui.QPen(hc.darker(130), 2))
            # Helmet dome
            painter.drawChord(cx - 22, cy - 78, 44, 40, 0, 180 * 16)
            # Helmet rim
            painter.drawRect(cx - 22, cy - 58, 44, 8)
            # Helmet detail - center ridge
            painter.setPen(QtGui.QPen(hc.darker(150), 2))
            painter.drawLine(cx, cy - 78, cx, cy - 52)
            # Visor slit
            painter.setPen(QtGui.QPen(QtGui.QColor("#222"), 2))
            painter.drawLine(cx - 12, cy - 55, cx + 12, cy - 55)
        else:
            # Hair (simple)
            painter.setBrush(QtGui.QColor("#5d4037"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawChord(cx - 18, cy - 72, 36, 20, 0, 180 * 16)
            # Hair strands
            painter.setPen(QtGui.QPen(QtGui.QColor("#4e342e"), 1))
            painter.drawLine(cx - 10, cy - 68, cx - 8, cy - 60)
            painter.drawLine(cx, cy - 70, cx, cy - 62)
            painter.drawLine(cx + 10, cy - 68, cx + 8, cy - 60)

        # === FACE (if no helmet visor) ===
        if not helm:
            # Eyebrows
            painter.setPen(QtGui.QPen(QtGui.QColor("#5d4037"), 2))
            painter.drawLine(cx - 12, cy - 58, cx - 5, cy - 56)
            painter.drawLine(cx + 5, cy - 56, cx + 12, cy - 58)
            
            # Eyes with whites
            painter.setBrush(QtGui.QColor("#fff"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 11, cy - 54, 9, 8)
            painter.drawEllipse(cx + 2, cy - 54, 9, 8)
            # Pupils
            painter.setBrush(QtGui.QColor("#333"))
            painter.drawEllipse(cx - 8, cy - 52, 5, 5)
            painter.drawEllipse(cx + 4, cy - 52, 5, 5)
            # Eye shine
            painter.setBrush(QtGui.QColor("#fff"))
            painter.drawEllipse(cx - 7, cy - 51, 2, 2)
            painter.drawEllipse(cx + 5, cy - 51, 2, 2)

            # Nose (simple)
            painter.setPen(QtGui.QPen(QtGui.QColor("#d4943a"), 1))
            painter.drawLine(cx, cy - 48, cx - 2, cy - 42)
            painter.drawLine(cx - 2, cy - 42, cx + 2, cy - 42)

            # Mouth/expression based on tier
            painter.setPen(QtGui.QPen(QtGui.QColor("#8b4513"), 2))
            if self.tier in ["legendary", "godlike"]:
                # Big smile
                painter.drawArc(cx - 10, cy - 42, 20, 12, 200 * 16, 140 * 16)
            elif self.tier in ["epic", "heroic"]:
                # Confident smirk
                painter.drawArc(cx - 8, cy - 40, 16, 8, 210 * 16, 120 * 16)
            elif self.tier in ["decent", "modest"]:
                # Slight smile
                painter.drawLine(cx - 6, cy - 38, cx + 6, cy - 36)
            else:
                # Neutral/determined
                painter.drawLine(cx - 5, cy - 38, cx + 5, cy - 38)

            # Ears
            painter.setBrush(QtGui.QColor("#ffcc80"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#e6a84d"), 1))
            painter.drawEllipse(cx - 24, cy - 55, 8, 12)
            painter.drawEllipse(cx + 16, cy - 55, 8, 12)

        # === AMULET ===
        amulet = self.equipped.get("Amulet")
        if amulet:
            ac = QtGui.QColor(amulet.get("color", "#666"))
            # Chain
            painter.setPen(QtGui.QPen(QtGui.QColor("#b8860b"), 1))
            painter.drawLine(cx - 12, cy - 28, cx, cy - 18)
            painter.drawLine(cx + 12, cy - 28, cx, cy - 18)
            # Amulet gem
            painter.setBrush(ac)
            painter.setPen(QtGui.QPen(ac.darker(130), 2))
            # Diamond shape
            amulet_path = QtGui.QPainterPath()
            amulet_path.moveTo(cx, cy - 22)
            amulet_path.lineTo(cx + 8, cy - 14)
            amulet_path.lineTo(cx, cy - 4)
            amulet_path.lineTo(cx - 8, cy - 14)
            amulet_path.closeSubpath()
            painter.drawPath(amulet_path)
            # Gem shine
            painter.setBrush(ac.lighter(150))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(cx - 3, cy - 18, 4, 4)

        # === WEAPON ===
        weap = self.equipped.get("Weapon")
        if weap:
            wc = QtGui.QColor(weap.get("color", "#666"))
            # Sword handle
            painter.setBrush(QtGui.QColor("#5d4037"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#3e2723"), 1))
            painter.drawRect(cx - 54, cy - 2, 5, 35)
            # Handle wrap
            painter.setPen(QtGui.QPen(QtGui.QColor("#8d6e63"), 1))
            for i in range(5):
                painter.drawLine(cx - 54, cy + 2 + i * 6, cx - 49, cy + 5 + i * 6)
            # Crossguard
            painter.setBrush(QtGui.QColor("#b8860b"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#8b6914"), 1))
            painter.drawRect(cx - 58, cy - 6, 14, 5)
            # Blade
            blade_path = QtGui.QPainterPath()
            blade_path.moveTo(cx - 55, cy - 6)
            blade_path.lineTo(cx - 48, cy - 6)
            blade_path.lineTo(cx - 51, cy - 55)
            blade_path.closeSubpath()
            painter.setBrush(wc)
            painter.setPen(QtGui.QPen(wc.darker(130), 2))
            painter.drawPath(blade_path)
            # Blade shine
            painter.setPen(QtGui.QPen(wc.lighter(150), 1))
            painter.drawLine(cx - 52, cy - 10, cx - 51, cy - 50)

        # === SHIELD ===
        shield = self.equipped.get("Shield")
        if shield:
            sc = QtGui.QColor(shield.get("color", "#666"))
            # Shield body (kite shape)
            shield_path = QtGui.QPainterPath()
            shield_path.moveTo(cx + 50, cy - 20)
            shield_path.quadTo(cx + 70, cy - 15, cx + 68, cy + 5)
            shield_path.lineTo(cx + 50, cy + 35)
            shield_path.lineTo(cx + 32, cy + 5)
            shield_path.quadTo(cx + 30, cy - 15, cx + 50, cy - 20)
            painter.setBrush(sc)
            painter.setPen(QtGui.QPen(sc.darker(130), 3))
            painter.drawPath(shield_path)
            # Shield rim
            painter.setPen(QtGui.QPen(sc.darker(150), 2))
            painter.drawPath(shield_path)
            # Shield emblem (cross)
            painter.setPen(QtGui.QPen(sc.lighter(130), 3))
            painter.drawLine(cx + 50, cy - 10, cx + 50, cy + 25)
            painter.drawLine(cx + 38, cy + 5, cx + 62, cy + 5)
            # Shield boss (center circle)
            painter.setBrush(sc.darker(120))
            painter.setPen(QtGui.QPen(sc.darker(150), 1))
            painter.drawEllipse(cx + 44, cy, 12, 12)

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


class ADHDBusterDialog(QtWidgets.QDialog):
    """Dialog for viewing and managing the ADHD Buster character and inventory."""

    def __init__(self, blocker: BlockerCore, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.blocker = blocker
        self.setWindowTitle("🦸 ADHD Buster - Character & Inventory")
        self.resize(750, 850)
        self.merge_selected = []
        self.slot_combos: Dict[str, QtWidgets.QComboBox] = {}
        self.slot_labels: Dict[str, QtWidgets.QLabel] = {}  # Store slot label references for theme updates
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

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

        # Stats summary
        total_items = len(self.blocker.adhd_buster.get("inventory", []))
        total_collected = self.blocker.adhd_buster.get("total_collected", total_items)
        streak = self.blocker.stats.get("streak_days", 0)
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        self.stats_lbl = QtWidgets.QLabel(f"📦 {total_items} in bag  |  🎁 {total_collected} collected  |  🔥 {streak} day streak  |  🍀 {luck} luck")
        self.stats_lbl.setStyleSheet("color: gray;")
        self.inner_layout.addWidget(self.stats_lbl)

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
            # Connect signals
            self.mode_story_radio.toggled.connect(self._on_mode_radio_changed)
            self.mode_hero_radio.toggled.connect(self._on_mode_radio_changed)
            self.mode_disabled_radio.toggled.connect(self._on_mode_radio_changed)
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

        # Character canvas and equipment side by side
        char_equip = QtWidgets.QHBoxLayout()
        equipped = self.blocker.adhd_buster.get("equipped", {})
        self.char_canvas = CharacterCanvas(equipped, power_info["total_power"], parent=self)
        char_equip.addWidget(self.char_canvas)
        self.char_equip_layout = char_equip  # Store reference for refresh

        equip_group = QtWidgets.QGroupBox("⚔ Equipped Gear (change with dropdown)")
        equip_layout = QtWidgets.QFormLayout(equip_group)
        slots = ["Helmet", "Chestplate", "Gauntlets", "Boots", "Shield", "Weapon", "Cloak", "Amulet"]
        inventory = self.blocker.adhd_buster.get("inventory", [])
        
        # Get current story for themed slot names
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")

        for slot in slots:
            combo = QtWidgets.QComboBox()
            combo.addItem("[Empty]")
            slot_items = [item for item in inventory if item.get("slot") == slot]
            for idx, item in enumerate(slot_items):
                display = f"{item['name']} (+{item.get('power', 10)}) [{item['rarity'][:1]}]"
                combo.addItem(display, item)
            current = equipped.get(slot)
            if current:
                for i in range(1, combo.count()):
                    if combo.itemData(i) and combo.itemData(i).get("name") == current.get("name"):
                        combo.setCurrentIndex(i)
                        break
            combo.currentIndexChanged.connect(lambda idx, s=slot, c=combo: self._on_equip_change(s, c))
            self.slot_combos[slot] = combo
            # Use themed slot display name
            display_name = get_slot_display_name(slot, active_story) if get_slot_display_name else slot
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
        diary_btn = QtWidgets.QPushButton("📖 Adventure Diary")
        diary_btn.clicked.connect(self._open_diary)
        btn_layout.addWidget(diary_btn)
        salvage_btn = QtWidgets.QPushButton("🗑️ Salvage Duplicates")
        salvage_btn.clicked.connect(self._salvage_duplicates)
        btn_layout.addWidget(salvage_btn)
        btn_layout.addStretch()
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
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
        # Immediately refresh all dependent displays
        self._refresh_character()

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

    def _refresh_character(self) -> None:
        """Refresh all power-related displays after gear changes."""
        if not GAMIFICATION_AVAILABLE:
            return
        # Get updated power info
        equipped = self.blocker.adhd_buster.get("equipped", {})
        power_info = get_power_breakdown(self.blocker.adhd_buster)
        
        # Update character canvas
        self.char_canvas.equipped = equipped
        self.char_canvas.power = power_info["total_power"]
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
        
        # Update set bonuses display
        self._refresh_sets_display(power_info)
        
        # Update story progress labels if available
        if hasattr(self, 'story_progress_lbl'):
            self._update_story_progress_labels()
        
        # Refresh chapter list in case new chapters were unlocked
        if hasattr(self, 'chapter_combo'):
            self._refresh_story_chapter_list()

    def _refresh_all_slot_combos(self) -> None:
        """Refresh all equipment slot combo boxes with current inventory."""
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        needs_save = False
        
        # Update slot labels with themed names
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        for slot, label in self.slot_labels.items():
            display_name = get_slot_display_name(slot, active_story) if get_slot_display_name else slot
            label.setText(f"{display_name}:")
        
        for slot, combo in self.slot_combos.items():
            # Block signals to prevent triggering _on_equip_change
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("[Empty]")
            
            slot_items = [item for item in inventory if item.get("slot") == slot]
            for item in slot_items:
                display = f"{item['name']} (+{item.get('power', 10)}) [{item['rarity'][:1]}]"
                combo.addItem(display, item)
            
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
                    # Equipped item no longer in inventory, clear it
                    self.blocker.adhd_buster["equipped"][slot] = None
                    combo.setCurrentIndex(0)
                    needs_save = True
            else:
                combo.setCurrentIndex(0)
            
            combo.blockSignals(False)
        
        # Persist any equipped items that were cleared
        if needs_save:
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()

    def _refresh_inventory(self) -> None:
        self.inv_list.clear()
        self.merge_selected = []
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        equipped_ts = {item.get("obtained_at") for item in equipped.values() if item}

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
            is_eq = item.get("obtained_at") in equipped_ts
            prefix = "✓ " if is_eq else ""
            power = item.get("power", RARITY_POWER.get(item.get("rarity", "Common"), 10))
            text = f"{prefix}{item['name']} (+{power}) [{item['rarity'][:1]}]"
            list_item = QtWidgets.QListWidgetItem(text)
            list_item.setData(QtCore.Qt.UserRole, orig_idx)
            # Add tooltip with full item details
            list_item.setToolTip(
                f"{item['name']}\n"
                f"Rarity: {item.get('rarity', 'Common')}\n"
                f"Slot: {item.get('slot', 'Unknown')}\n"
                f"Power: +{power}\n"
                f"{'[✓ EQUIPPED - will be unequipped if merged]' if is_eq else '[Click to select for merge]'}"
            )
            # Allow selecting equipped items (they can be merged now)
            list_item.setForeground(QtGui.QColor(item.get("color", "#333")))
            self.inv_list.addItem(list_item)

    def refresh_gear_combos(self) -> None:
        """Refresh gear dropdown combos to reflect new inventory items."""
        inventory = self.blocker.adhd_buster.get("inventory", [])
        equipped = self.blocker.adhd_buster.get("equipped", {})
        
        for slot, combo in self.slot_combos.items():
            # Remember current selection
            current = equipped.get(slot)
            current_name = current.get("name") if current else None
            
            # Block signals to prevent triggering equip changes
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("[Empty]")
            
            # Add all items for this slot
            slot_items = [item for item in inventory if item.get("slot") == slot]
            for item in slot_items:
                display = f"{item['name']} (+{item.get('power', 10)}) [{item['rarity'][:1]}]"
                combo.addItem(display, item)
            
            # Restore selection
            if current_name:
                for i in range(1, combo.count()):
                    if combo.itemData(i) and combo.itemData(i).get("name") == current_name:
                        combo.setCurrentIndex(i)
                        break
            
            combo.blockSignals(False)
        
        # Also refresh inventory list and stats
        self._refresh_inventory()
        self._refresh_character()

    def _update_merge_selection(self) -> None:
        self.merge_selected = [item.data(QtCore.Qt.UserRole) for item in self.inv_list.selectedItems()]
        count = len(self.merge_selected)
        self.merge_btn.setText(f"🎲 Merge Selected ({count})")
        if count >= 2 and GAMIFICATION_AVAILABLE:
            inventory = self.blocker.adhd_buster.get("inventory", [])
            items = [inventory[idx] for idx in self.merge_selected if idx < len(inventory)]
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
        inventory = self.blocker.adhd_buster.get("inventory", [])
        items = [inventory[idx] for idx in self.merge_selected if idx < len(inventory)]
        luck = self.blocker.adhd_buster.get("luck_bonus", 0)
        rate = calculate_merge_success_rate(items, luck)
        result_rarity = get_merge_result_rarity(items)
        summary = "\n".join([f"  • {i['name']} ({i['rarity']})" for i in items])
        if QtWidgets.QMessageBox.question(
            self, "⚠️ Lucky Merge",
            f"Merge {len(items)} items?\n\n{summary}\n\nSuccess rate: {rate*100:.0f}%\n"
            f"On success: {result_rarity}+ item\nOn failure: ALL items LOST!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        ) != QtWidgets.QMessageBox.Yes:
            return
        active_story = self.blocker.adhd_buster.get("active_story", "warrior")
        result = perform_lucky_merge(items, luck, story_id=active_story)
        
        # Get the timestamps of items being merged for equipped cleanup
        merged_timestamps = {item.get("obtained_at") for item in items if item.get("obtained_at")}
        
        # Remove merged items from inventory
        for idx in sorted(self.merge_selected, reverse=True):
            if idx < len(inventory):
                del inventory[idx]
        
        # Clean up equipped items that were merged (in case any were equipped)
        equipped = self.blocker.adhd_buster.get("equipped", {})
        for slot, eq_item in list(equipped.items()):
            if eq_item and eq_item.get("obtained_at") in merged_timestamps:
                self.blocker.adhd_buster["equipped"][slot] = None
        
        if result["success"]:
            inventory.append(result["result_item"])
            self.blocker.adhd_buster["inventory"] = inventory
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
            self.blocker.adhd_buster["inventory"] = inventory
            # Sync changes to active hero before saving
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()
            QtWidgets.QMessageBox.critical(self, "💔 Merge Failed!",
                f"Roll: {result['roll_pct']} (needed < {result['needed_pct']})\n\n"
                f"{len(items)} items lost forever.")
        
        # Refresh both inventory and equipment dropdowns
        self._refresh_inventory()
        self._refresh_all_slot_combos()
        self._refresh_character()

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
                # Revert combo to current story
                for i in range(self.story_combo.count()):
                    if self.story_combo.itemData(i) == current:
                        self.story_combo.setCurrentIndex(i)
                        break
                return
        
        select_story(self.blocker.adhd_buster, story_id)
        self.blocker.save_config()
        
        # Refresh all UI elements for the new hero
        self._update_story_description()
        self._update_story_progress_labels()
        self._refresh_story_chapter_list()
        self._refresh_inventory()
        self._refresh_all_slot_combos()
        self._refresh_character()

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
            
            # Refresh all UI elements
            self._update_story_description()
            self._update_story_progress_labels()
            self._refresh_story_chapter_list()
            self._refresh_inventory()
            self._refresh_all_slot_combos()
            self._refresh_character()
            
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
        self._refresh_inventory()
        self._refresh_all_slot_combos()
        self._refresh_character()

    def _update_mode_ui_state(self) -> None:
        """Update UI elements based on current mode (enable/disable story controls)."""
        if not GAMIFICATION_AVAILABLE:
            return
        enabled = is_gamification_enabled(self.blocker.adhd_buster)
        story_mode = get_story_mode(self.blocker.adhd_buster) == STORY_MODE_ACTIVE
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
            formatted = chapter['content'].strip()
            formatted = formatted.replace("**", "<b>").replace("**", "</b>")
            formatted = formatted.replace("*", "<i>").replace("*", "</i>")
            formatted = formatted.replace("\n\n", "</p><p>")
            formatted = formatted.replace("\n", "<br>")
            formatted = f"<p style='font-size: 13px; line-height: 1.6;'>{formatted}</p>"
            
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
                    formatted = updated_chapter['content'].strip()
                    formatted = formatted.replace("**", "<b>").replace("**", "</b>")
                    formatted = formatted.replace("*", "<i>").replace("*", "</i>")
                    formatted = formatted.replace("\n\n", "</p><p>")
                    formatted = formatted.replace("\n", "<br>")
                    formatted = f"<p style='font-size: 13px; line-height: 1.6;'>{formatted}</p>"
                    
                    content_text.setHtml(formatted)
                    content_text.setStyleSheet("background-color: #1a1a2e; color: #eee; padding: 10px;")
                    cont_layout.addWidget(content_text)
                    
                    # Continue button
                    ok_btn = QtWidgets.QPushButton("Continue My Journey")
                    ok_btn.clicked.connect(continuation_dialog.accept)
                    cont_layout.addWidget(ok_btn)
                    
                    continuation_dialog.exec()
                    
                    # Refresh all story-related UI after decision
                    self._refresh_story_chapter_list()
                    self._update_story_progress_labels()
                
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
                    decision_marker = " ❓"  # Decision pending
            
            self.chapter_combo.addItem(
                f"{emoji} Chapter {ch['number']}: {ch['title']}{decision_marker}",
                ch["number"]
            )

    def _open_diary(self) -> None:
        DiaryDialog(self.blocker, self).exec()

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
        self._refresh_inventory()
        self._refresh_all_slot_combos()


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
        info_lbl = QtWidgets.QLabel(f"[{self.item['rarity']} {self.item['slot']}] +{power} Power")
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
            msg.setInformativeText(
                f"<p style='font-size: 14px;'>{result['message']}</p>"
                f"<p style='font-size: 16px; color: {rarity_color}; font-weight: bold;'>"
                f"{item['name']}</p>"
                f"<p><b>Rarity:</b> <span style='color: {rarity_color};'>{item['rarity']}</span><br>"
                f"<b>Slot:</b> {item['slot']}<br>"
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
        self.local_ai = None
        if LOCAL_AI_AVAILABLE and LocalAI:
            self.local_ai = LocalAI()
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
        if self.local_ai:
            try:
                suggestions = self.local_ai.suggest_break_activity(
                    self.session_duration // 60, None
                )
                if suggestions:
                    text = "\n".join(f"  {i}. {s}" for i, s in enumerate(suggestions, 1))
                    self.suggestions_label.setText(text)
                    return
            except Exception:
                pass
        # Fallback suggestions
        fallback = [
            "Take a 5-minute walk or stretch",
            "Get some water or a healthy snack",
            "Look away from screen - rest your eyes",
            "Do some deep breathing exercises"
        ]
        self.suggestions_label.setText("\n".join(f"  {i}. {s}" for i, s in enumerate(fallback, 1)))

    def _save_and_close(self) -> None:
        note = self.notes_edit.toPlainText().strip()
        if not note and self.selected_rating:
            note = self.selected_rating

        if note and self.local_ai:
            try:
                analysis = self.local_ai.analyze_focus_quality(note)
                if analysis and "interpretation" in analysis:
                    self.analysis_label.setText(f"🧠 AI: {analysis['interpretation']}")
                    # Save to stats
                    self._save_session_note(note, analysis)
            except Exception:
                pass
        elif note:
            self._save_session_note(note, None)

        self.accept()

    def _save_session_note(self, note: str, analysis) -> None:
        """Save session note with AI analysis to stats."""
        session_notes = self.blocker.stats.get("session_notes", [])
        session_notes.append({
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": self.session_duration,
            "note": note,
            "analysis": analysis
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
        # Connect session complete signal to refresh stats
        self.timer_tab.session_complete.connect(self._on_session_complete)

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

        if AI_AVAILABLE:
            self.ai_tab = AITab(self.blocker, self)
            self.tabs.addTab(self.ai_tab, "🧠 AI Insights")

        self.statusBar().showMessage(f"Personal Liberty v{APP_VERSION}")

        # System Tray setup
        self.tray_icon = None
        self.minimize_to_tray = self.blocker.minimize_to_tray  # Load from config
        
        # Track open ADHD Buster dialog for refresh on loot drops
        self.adhd_dialog = None
        self._setup_system_tray()

        # Check for crash recovery on startup
        QtCore.QTimer.singleShot(500, self._check_crash_recovery)

        # Check for scheduled blocking
        QtCore.QTimer.singleShot(700, self._check_scheduled_blocking)

        # Show priorities on startup if enabled
        if self.blocker.show_priorities_on_startup:
            QtCore.QTimer.singleShot(600, self._check_priorities_on_startup)

        # Check for daily gear reward
        if GAMIFICATION_AVAILABLE:
            QtCore.QTimer.singleShot(800, self._check_daily_gear_reward)
            QtCore.QTimer.singleShot(850, self._show_onboarding_prompt)

    def _show_onboarding_prompt(self) -> None:
        """Ask the user how they want to play this session."""
        if not GAMIFICATION_AVAILABLE:
            return

        ensure_hero_structure(self.blocker.adhd_buster)

        # Skip if user already set 'skip_onboarding' flag
        if self.blocker.adhd_buster.get("skip_onboarding", False):
            return

        dialog = OnboardingModeDialog(self.blocker, self)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
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
                    "Not running as administrator - website blocking won't work!\\n\\n"
                    "Right-click the app and select 'Run as administrator',\\n"
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
            # Generate boosted item
            item = generate_daily_reward_item(self.blocker.adhd_buster)
            
            # Add to inventory
            if "inventory" not in self.blocker.adhd_buster:
                self.blocker.adhd_buster["inventory"] = []
            self.blocker.adhd_buster["inventory"].append(item)
            self.blocker.adhd_buster["last_daily_reward_date"] = today
            self.blocker.adhd_buster["total_collected"] = self.blocker.adhd_buster.get("total_collected", 0) + 1
            # Sync changes to active hero before saving
            if GAMIFICATION_AVAILABLE:
                sync_hero_data(self.blocker.adhd_buster)
            self.blocker.save_config()
            
            # Show reward dialog
            current_tier = get_current_tier(self.blocker.adhd_buster)
            boosted_tier = get_boosted_rarity(current_tier)
            
            QtWidgets.QMessageBox.information(
                self,
                f"🎁 {reward_reason}",
                f"You received a special gear item!\n\n"
                f"✨ {item['name']}\n"
                f"⚔ Power: +{item['power']}\n"
                f"🏆 Rarity: {item['rarity']}\n"
                f"📍 Slot: {item['slot']}\n\n"
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
        self.close()

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
        self.adhd_dialog = ADHDBusterDialog(self.blocker, self)
        self.adhd_dialog.finished.connect(self._on_adhd_dialog_closed)
        self.adhd_dialog.exec()
        if GAMIFICATION_AVAILABLE and hasattr(self, "buster_btn"):
            # Update button visibility and text based on mode
            enabled = is_gamification_enabled(self.blocker.adhd_buster)
            self.buster_btn.setVisible(enabled)
            if enabled:
                power = calculate_character_power(self.blocker.adhd_buster)
                self.buster_btn.setText(f"🦸 ADHD Buster  ⚔ {power}")

    def _on_adhd_dialog_closed(self) -> None:
        """Clear reference when ADHD dialog closes."""
        self.adhd_dialog = None

    def refresh_adhd_dialog(self) -> None:
        """Refresh ADHD Buster dialog if it's open."""
        if hasattr(self, 'adhd_dialog') and self.adhd_dialog is not None:
            self.adhd_dialog.refresh_gear_combos()

    def _open_diary(self) -> None:
        dialog = DiaryDialog(self.blocker, self)
        dialog.exec()

    def _emergency_cleanup(self) -> None:
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
                    "� Hardcore Mode Active",
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
            else:
                event.ignore()
        else:
            event.accept()

    def show_ai_session_complete(self, session_duration: int) -> None:
        """Show AI-powered session complete dialog."""
        if LOCAL_AI_AVAILABLE:
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
        QtWidgets.QMessageBox.warning(
            None,
            "Already Running",
            "Personal Liberty is already running.\n\nCheck your system tray or taskbar."
        )
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
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
