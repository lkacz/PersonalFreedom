
import sys
import random
import time
import math
import threading
from datetime import datetime, timedelta
from PySide6 import QtWidgets, QtCore, QtGui
from gamification import generate_item, get_entity_qol_perks
from game_state import get_game_state

# Base daily eye rest cap (can be increased by entity perks)
BASE_EYE_REST_CAP = 20

# Platform-safe sound support
try:
    import winsound
except ImportError:
    winsound = None

class SoundGenerator:
    """
    Generates distinct sounds for the eye routine.
    Using threading to ensure UI remains responsive (Non-blocking).
    """
    
    @staticmethod
    def _play_async(sequence):
        """Play a sequence of (freq, duration) tuples in a separate thread."""
        if not winsound:
            return
            
        def run():
            try:
                for freq, ms in sequence:
                    if freq == 0:
                        time.sleep(ms / 1000.0)
                    else:
                        winsound.Beep(freq, ms)
            except Exception:
                pass
                
        threading.Thread(target=run, daemon=True).start()
    
    @staticmethod
    def play_start():
        """Distinct start sound."""
        # 1000Hz (200ms) -> pause (100ms) -> 1500Hz (300ms)
        SoundGenerator._play_async([(1000, 200), (0, 100), (1500, 300)])

    @staticmethod
    def play_blink_close():
        """Cue for closing eyes (Low tone)."""
        SoundGenerator._play_async([(300, 400)])

    @staticmethod
    def play_blink_hold():
        """Cue for keeping eyes closed (Higher tone)."""
        SoundGenerator._play_async([(500, 150)])

    @staticmethod
    def play_blink_open():
        """Cue for opening eyes (Silent/Visual Only)."""
        pass # Silence as requested

    @staticmethod
    def play_gaze_start():
        """Cue for starting far gaze."""
        SoundGenerator._play_async([(1200, 300)])

    @staticmethod
    def play_tick():
        """Soft tick timer."""
        # Very short blip
        SoundGenerator._play_async([(400, 30)])

    @staticmethod
    def play_complete():
        """Success fanfare."""
        # Fanfare pattern
        SoundGenerator._play_async([(1000, 100), (1200, 100), (1500, 300)])

    @staticmethod
    def play_inhale():
        """Rising pitch for inhale (Continuous-like)."""
        # Generated sequence: 300 -> 500 Hz over ~3s
        # 10 steps of 300ms is too choppy, let's do 20 steps of 150ms?
        # A long breath sound might be annoying if monotonic steps. 
        # Using shorter steps: 6 steps of 200ms -> 1.2s cue? 
        # User said "Inhale 4s". "increasing for inhale".
        # Let's try 3 seconds of sound to cue the 4s inhale.
        # 10 steps of 300ms = 3s.
        freqs = range(300, 600, 30) # 300, 330, 360 ... 10 steps
        seq = [(f, 200) for f in freqs]
        SoundGenerator._play_async(seq)

    @staticmethod
    def play_exhale():
        """Lowering pitch for exhale (Continuous-like)."""
        # Generated sequence: 600 -> 300 Hz over ~4s
        freqs = range(600, 300, -25) 
        seq = [(f, 250) for f in freqs]
        SoundGenerator._play_async(seq)


class EyeProtectionTab(QtWidgets.QWidget):
    """
    Eye Protection Routine Tab.
    Implements a guided 2-step routine (Blink + Far Gaze) with gamified rewards.
    """
    
    routine_completed = QtCore.Signal(dict) # Emits item dict if won, or empty dict

    def __init__(self, blocker_core):
        super().__init__()
        self.blocker = blocker_core
        self.is_running = False
        
        # State
        self.step_phase = "idle" # idle, blinking, gazing
        self.blink_count = 0
        self.blink_state = "open" # open, closed, hold
        self.gaze_seconds_left = 20
        
        self.init_ui()
        self.update_stats_display()

        # Timer for routine steps
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.on_timer_tick)
        
        # Ensure cleanup on widget destruction
        self.destroyed.connect(self._on_destroyed)
    
    def _on_destroyed(self):
        """Handle widget destruction - stop timers."""
        self.cleanup()
    
    def cleanup(self):
        """Stop any running timers. Call this before destroying the widget."""
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        self.is_running = False

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title with gradient background
        title = QtWidgets.QLabel("👁️ Eye & Breath Relief")
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #ffffff;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #66bb6a, stop:1 #43a047);
            padding: 15px;
            border-radius: 10px;
            border: 2px solid #4caf50;
        """)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Cooldown Status Label with modern card design
        cooldown_card = QtWidgets.QFrame()
        cooldown_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d3436, stop:1 #1e272e);
                border: 2px solid #4caf50;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        cooldown_layout = QtWidgets.QVBoxLayout(cooldown_card)
        self.cooldown_status_label = QtWidgets.QLabel("✅ Ready to start!")
        self.cooldown_status_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #4caf50;
            background: transparent;
            padding: 5px;
        """)
        self.cooldown_status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        cooldown_layout.addWidget(self.cooldown_status_label)
        layout.addWidget(cooldown_card)

        # Instructions / Status Area with gradient card
        instructions_frame = QtWidgets.QGroupBox("📋 Instructions & Status")
        instructions_frame.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #4fc3f7;
                border: 2px solid #2d3436;
                border-radius: 10px;
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
        instructions_layout = QtWidgets.QVBoxLayout(instructions_frame)
        
        instructions = (
            "<b style='color:#66bb6a;'>INSTRUCTIONS (Read before starting):</b><br><br>"
            "<span style='color:#81c784;'>1. <b>Step A (Blinks):</b></span> Low tone = CLOSE, Higher tone = HOLD, Silence = OPEN. Repeat 5x.<br>"
            "<span style='color:#81c784;'>2. <b>Step B (Gaze & Breath):</b></span> Look 20ft (6m) away. Rising sound = INHALE (4s), Falling sound = EXHALE (6s).<br><br>"
            "<i style='color:#ffa726;'>💡 Tip: Blink normally during Step B to avoid dryness!</i>"
        )
        self.status_label = QtWidgets.QLabel(instructions)
        self.status_label.setStyleSheet("font-size: 13px; color: #e0e0e0; background: transparent; padding: 5px;")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.status_label.setWordWrap(True)
        instructions_layout.addWidget(self.status_label)
        layout.addWidget(instructions_frame)

        # Big Visual Cue with modern card design
        cue_card = QtWidgets.QFrame()
        cue_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3c72, stop:1 #2a5298);
                border: 3px solid #2196f3;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        cue_layout = QtWidgets.QVBoxLayout(cue_card)
        cue_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cue_label = QtWidgets.QLabel("Start when you are ready")
        self.cue_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #64b5f6;
            background: transparent;
            padding: 20px;
        """)
        self.cue_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.cue_label.setMinimumHeight(150)
        cue_layout.addWidget(self.cue_label)
        layout.addWidget(cue_card)

        # Start Button with modern gradient (matching HydrationTab style)
        self.start_btn = QtWidgets.QPushButton("👁️ Start Routine (1 min)")
        self.start_btn.setMinimumHeight(70)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66bb6a, stop:1 #43a047);
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
                border: 3px solid #4caf50;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #81c784, stop:1 #66bb6a);
                border: 3px solid #66bb6a;
            }
            QPushButton:pressed {
                background: #388e3c;
                border: 3px solid #2e7d32;
            }
            QPushButton:disabled {
                background: #555555;
                border: 3px solid #444444;
                color: #888888;
            }
        """)
        self.start_btn.clicked.connect(self.start_routine)
        layout.addWidget(self.start_btn)

        # Reminder Settings Section with gradient card
        reminder_frame = QtWidgets.QGroupBox("🔔 Reminders")
        reminder_frame.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #ffa726;
                border: 2px solid #2d3436;
                border-radius: 10px;
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
        reminder_layout = QtWidgets.QHBoxLayout(reminder_frame)
        
        self.reminder_checkbox = QtWidgets.QCheckBox("🔔 Remind me every")
        self.reminder_checkbox.setChecked(getattr(self.blocker, 'eye_reminder_enabled', False))
        self.reminder_checkbox.stateChanged.connect(self._update_reminder_setting)
        reminder_layout.addWidget(self.reminder_checkbox)
        
        self.reminder_interval = QtWidgets.QSpinBox()
        self.reminder_interval.setRange(15, 180)
        self.reminder_interval.setValue(getattr(self.blocker, 'eye_reminder_interval', 60))
        self.reminder_interval.setSuffix(" min")
        self.reminder_interval.valueChanged.connect(self._update_reminder_setting)
        reminder_layout.addWidget(self.reminder_interval)
        
        reminder_layout.addWidget(QtWidgets.QLabel("(via toast notification)"))
        reminder_layout.addStretch()
        layout.addWidget(reminder_frame)

        # Reward Info Box with modern gradient card
        info_frame = QtWidgets.QGroupBox("🎁 Today's Progress & Rewards")
        info_frame.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #ffd700;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
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
        info_layout = QtWidgets.QVBoxLayout(info_frame)
        
        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setStyleSheet("""
            color: #e0e0e0;
            font-size: 13px;
            background: transparent;
            padding: 10px;
        """)
        self.stats_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        info_layout.addWidget(self.stats_label)
        layout.addWidget(info_frame)
        
        layout.addStretch()
        
        # Start cooldown update timer (refresh every minute like hydration)
        self.cooldown_timer = QtCore.QTimer(self)
        self.cooldown_timer.timeout.connect(self._update_cooldown_display)
        self.cooldown_timer.start(60000)  # Update every minute
        
        # Initial update
        self._update_cooldown_display()
    
    def _update_reminder_setting(self):
        """Save reminder settings when changed."""
        self.blocker.eye_reminder_enabled = self.reminder_checkbox.isChecked()
        self.blocker.eye_reminder_interval = self.reminder_interval.value()
        self.blocker.save_config()

    def _update_cooldown_display(self):
        """Update cooldown status display like hydration tracker."""
        stats = self.blocker.stats.get("eye_protection", {})
        last_date_str = stats.get("last_date", "")
        count = self.get_daily_count()
        daily_cap = self.get_daily_cap()
        
        # Check daily limit (can be increased by entity perks)
        if count >= daily_cap:
            self.cooldown_status_label.setText(f"🎯 Daily limit reached! ({daily_cap}/{daily_cap})")
            self.cooldown_status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4caf50; padding: 10px;")
            self.start_btn.setEnabled(False)
            return
        
        # Check 20-minute cooldown
        if last_date_str:
            try:
                last_dt = datetime.fromisoformat(last_date_str)
                elapsed = datetime.now() - last_dt
                
                if elapsed < timedelta(minutes=20):
                    remaining = math.ceil(20 - elapsed.total_seconds() / 60)
                    next_time = (last_dt + timedelta(minutes=20)).strftime("%H:%M")
                    self.cooldown_status_label.setText(f"⏳ Wait {remaining} min (next at {next_time})")
                    self.cooldown_status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800; padding: 10px;")
                    self.start_btn.setEnabled(False)
                    return
            except (ValueError, TypeError):
                pass  # Corrupted date, allow routine
        
        # Ready to start
        self.cooldown_status_label.setText("✅ Ready to start!")
        self.cooldown_status_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4caf50; padding: 10px;")
        self.start_btn.setEnabled(True)
    
    def get_daily_count(self):
        """Get number of routines performed today (reset at 5 AM)."""
        stats = self.blocker.stats.get("eye_protection", {})
        last_date_str = stats.get("last_date", "")
        count = stats.get("daily_count", 0)
        
        # Validate and sanitize count value
        if not isinstance(count, int) or count < 0:
            count = 0
        # Note: Cap is enforced in get_daily_cap(), not here (perks can increase it)
        
        if not last_date_str:
            return 0
        
        try:
            last_dt = datetime.fromisoformat(last_date_str)
        except (ValueError, TypeError):
            return 0  # Treat corrupted date as no history
        now = datetime.now()
        
        # Calculate 5 AM cutoff for today (or yesterday if before 5 AM)
        if now.hour < 5:
            current_day_start = now.replace(hour=5, minute=0, second=0, microsecond=0) - timedelta(days=1)
        else:
            current_day_start = now.replace(hour=5, minute=0, second=0, microsecond=0)
            
        if last_dt < current_day_start:
            return 0
        return count

    def get_daily_cap(self) -> int:
        """Get the daily eye rest cap (base + entity perks)."""
        try:
            qol_perks = get_entity_qol_perks(self.blocker.adhd_buster)
            perk_bonus = qol_perks.get("eye_rest_cap", 0)
            return BASE_EYE_REST_CAP + perk_bonus
        except Exception:
            return BASE_EYE_REST_CAP

    def update_stats_display(self):
        count = self.get_daily_count()
        daily_cap = self.get_daily_cap()
        
        # Check if at daily limit
        if count >= daily_cap:
            text = (
                f"<b>Today's Routines: {count} / {daily_cap}</b><br><br>"
                f"<span style='color:#4caf50;'>🎯 Daily limit reached!</span><br>"
                f"Come back tomorrow for more rewards!"
            )
            self.stats_label.setText(text)
            return
        
        # Moving window: every 4 routines = +1 tier (up to daily_cap)
        # Routines 1-4: Tier 0 (Common), 99% success
        # Routines 5-8: Tier 1 (Uncommon), 80% success
        # Routines 9-12: Tier 2 (Rare), 60% success
        # Routines 13-16: Tier 3 (Epic), 40% success
        # Routines 17-20+: Tier 4 (Legendary), 20% success
        
        next_count = min(count + 1, daily_cap)
        window_tier = min((next_count - 1) // 4, 4)
        tier_names = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        tier_colors = ["#9e9e9e", "#4caf50", "#2196f3", "#9c27b0", "#ff9800"]
        success_rates = [99, 80, 60, 40, 20]
        
        base_tier = tier_names[window_tier]
        base_color = tier_colors[window_tier]
        success_rate = success_rates[window_tier]
        
        # Show which window we're in
        window_start = window_tier * 4 + 1
        window_end = min((window_tier + 1) * 4, daily_cap)
        
        text = (
            f"<b>Today's Routines: {count} / {daily_cap}</b><br><br>"
            f"Next Routine Window: <span style='color:{base_color};'>{window_start}-{window_end} ({base_tier}-centered)</span><br>"
            f"🎲 Success Rate: <span style='color:#4caf50'>{success_rate}%</span><br>"
            f"🎰 Tier Distribution: [5%, 15%, <span style='color:{base_color};'><b>60%</b></span>, 15%, 5%]"
        )
        self.stats_label.setText(text)

    def start_routine(self):
        # Cooldown check is now handled by _update_cooldown_display
        # Double-check before starting
        count = self.get_daily_count()
        daily_cap = self.get_daily_cap()
        if count >= daily_cap:
            QtWidgets.QMessageBox.information(self, "Daily Limit", f"You've reached the daily limit of {daily_cap} routines!")
            return
        
        stats = self.blocker.stats.get("eye_protection", {})
        last_date_str = stats.get("last_date", "")
        if last_date_str:
            try:
                last_dt = datetime.fromisoformat(last_date_str)
            except (ValueError, TypeError):
                last_dt = None  # Corrupted date, allow routine
            if last_dt:
                elapsed = datetime.now() - last_dt
                if elapsed < timedelta(minutes=20):
                    remaining = int(20 - elapsed.total_seconds() / 60)
                    QtWidgets.QMessageBox.warning(self, "Resting Eyes", f"You eyes need to work a bit before resting again!\nWait {remaining} minutes.")
                    return

        self.is_running = True
        self.start_btn.setEnabled(False)
        self.step_phase = "blinking"
        self.blink_count = 0
        self.blink_state = "ready"
        
        # Sound
        SoundGenerator.play_start()
        
        # Start Step A logic
        self.status_label.setText("Step A: 5 Gentle Blinks")
        self.cue_label.setText("Get Ready...")
        
        # Short delay before first blink using QTimer
        QtCore.QTimer.singleShot(2000, self.start_blink_cycle)

    def start_blink_cycle(self):
        # Guard: Don't run if routine stopped or widget destroyed
        if not self.is_running or not self.isVisible():
            return
            
        if self.blink_count >= 5:
            self.start_gaze_phase()
            return
            
        self.blink_count += 1
        self.blink_state = "close"
        
        self.cue_label.setText("CLOSE eyes")
        # Reuse status area for progress, but users have eyes closed mostly
        # self.status_label.setText(f"Blink {self.blink_count}/5") 
        SoundGenerator.play_blink_close()
        
        # Schedule next sub-steps
        # Close duration ~1.5s -> Then Hold signal
        QtCore.QTimer.singleShot(1500, self.do_blink_hold)
        
    def do_blink_hold(self):
        # Guard: Don't run if routine stopped
        if not self.is_running:
            return
        self.blink_state = "hold"
        self.cue_label.setText("HOLD...")
        SoundGenerator.play_blink_hold()
        # Hold duration ~0.5s -> Then Open (Silence)
        QtCore.QTimer.singleShot(500, self.do_blink_open)
        
    def do_blink_open(self):
        # Guard: Don't run if routine stopped
        if not self.is_running:
            return
        self.blink_state = "open"
        self.cue_label.setText("OPEN eyes")
        SoundGenerator.play_blink_open() # Is silent
        # Open duration ~1.5s -> Next cycle
        QtCore.QTimer.singleShot(1500, self.start_blink_cycle)

    def start_gaze_phase(self):
        # Guard: Don't run if routine stopped
        if not self.is_running:
            return
        self.step_phase = "gazing"
        self.gaze_seconds_left = 20
        self.status_label.setText("Step B: Far Gaze + Breathing\n(Blink normally!)")
        self.cue_label.setText("Look away (20ft/6m)")
        SoundGenerator.play_gaze_start()
        
        self.timer.start(1000) # One tick per second
        self.on_timer_tick() # Execute first tick immediately

    def on_timer_tick(self):
        try:
            if self.step_phase == "gazing":
                # 20s total duration
                # 0-4s: Inhale (4s) -> T: 20->16
                # 4-10s: Exhale (6s) -> T: 16->10
                # 10-14s: Inhale (4s) -> T: 10->6
                # 14-20s: Exhale (6s) -> T: 6->0
                
                t = self.gaze_seconds_left
                
                if t > 16:  # Inhale 1
                    if t == 20:
                        SoundGenerator.play_inhale()
                    self.cue_label.setText(f"Look away + INHALE... {t-16}")
                elif t > 10:  # Exhale 1
                    if t == 16:
                        SoundGenerator.play_exhale()
                    self.cue_label.setText(f"Look away + EXHALE... {t-10}")
                elif t > 6:  # Inhale 2
                    if t == 10:
                        SoundGenerator.play_inhale()
                    self.cue_label.setText(f"Look away + INHALE... {t-6}")
                elif t > 0:  # Exhale 2
                    if t == 6:
                        SoundGenerator.play_exhale()
                    self.cue_label.setText(f"Look away + EXHALE... {t}")
                
                self.gaze_seconds_left -= 1
                
                if self.gaze_seconds_left < 0:
                    self.timer.stop()
                    self.complete_routine()
        except Exception:
            # Stop timer safely on any error
            self.timer.stop()
            self.is_running = False
            self.step_phase = "idle"  # Reset to idle state on error

    def complete_routine(self):
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.cue_label.setText("COMPLETE!")
        SoundGenerator.play_complete()
        
        # Update stats
        current_count = self.get_daily_count()
        new_count = min(current_count + 1, 20)  # Cap at 20
        
        # Moving window: Every 4 routines = +1 tier, cap at tier 4 (Legendary)
        # Routines 1-4: Tier 0 (Common-centered)
        # Routines 5-8: Tier 1 (Uncommon-centered)
        # Routines 9-12: Tier 2 (Rare-centered)
        # Routines 13-16: Tier 3 (Epic-centered)
        # Routines 17-20: Tier 4 (Legendary-centered)
        window_tier = min((new_count - 1) // 4, 4)
        
        # Success rate decreases: 99%, 80%, 60%, 40%, 20%
        success_rates = [0.99, 0.80, 0.60, 0.40, 0.20]
        success_rate = success_rates[min(window_tier, len(success_rates) - 1)]
        
        # Map tier to base rarity
        tier_names = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        base_rarity = tier_names[window_tier]
        
        # Save Stats first
        if "eye_protection" not in self.blocker.stats:
            self.blocker.stats["eye_protection"] = {}
            
        self.blocker.stats["eye_protection"]["last_date"] = datetime.now().isoformat()
        self.blocker.stats["eye_protection"]["daily_count"] = new_count
        self.blocker.save_stats()
        
        # Import the merge lottery dialog for moving window animation
        from lottery_animation import MergeTwoStageLotteryDialog
        
        # Show the animated two-stage lottery dialog with moving window
        lottery = MergeTwoStageLotteryDialog(
            success_roll=0.0,  # Will be re-rolled inside
            success_threshold=success_rate,
            tier_upgrade_enabled=False,
            base_rarity=base_rarity,
            parent=self
        )
        lottery.exec()
        
        # Get results after animation completes
        won_item, tier = lottery.get_results()
        
        if won_item:
            # Generate Item
            adhd_data = getattr(self.blocker, 'adhd_buster', {})
            story_theme = adhd_data.get('story_active', 'warrior') if adhd_data else 'warrior'
            
            new_item = generate_item(rarity=tier, theme=story_theme)
            
            # Validate generated item before adding
            if not new_item or not isinstance(new_item, dict):
                self.routine_completed.emit({})
                return
            
            # Use GameStateManager to add item safely
            gs = get_game_state(self.blocker)
            if gs:
                gs.add_item(new_item)
            
            self.routine_completed.emit(new_item)
        else:
            self.routine_completed.emit({})
        
        # Update cooldown display and stats after completion
        self._update_cooldown_display()
        self.update_stats_display()
