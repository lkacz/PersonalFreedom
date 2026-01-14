
import sys
import random
import time
import threading
from datetime import datetime, timedelta
from PySide6 import QtWidgets, QtCore, QtGui
from gamification import generate_item
from game_state import get_game_state
from lottery_animation import TwoStageLotteryDialog

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
        
        # Title
        title = QtWidgets.QLabel("👁️ Eye & Breath Relief")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4caf50;")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Instructions / Status Area
        instructions = (
            "<b>INSTRUCTIONS (Read before starting):</b><br>"
            "1. <b>Step A (Blinks):</b> You will hear a low tone to CLOSE, a higher tone to HOLD, then silence to OPEN. Do this 5 times.<br>"
            "2. <b>Step B (Gaze & Breath):</b> Look 20ft (6m) away. Follow the rising sound to INHALE (4s) and falling sound to EXHALE (6s).<br>"
            "<i>* Blink normally during Step B to avoid dryness!</i>"
        )
        self.status_label = QtWidgets.QLabel(instructions)
        self.status_label.setStyleSheet("font-size: 16px; color: #eee; background-color: #333; padding: 10px; border-radius: 5px;")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Big Visual Cue (Icon or Text)
        self.cue_label = QtWidgets.QLabel("Start when you are ready")
        self.cue_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #2196f3;")
        self.cue_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.cue_label.setMinimumHeight(150)
        layout.addWidget(self.cue_label)

        # Start Button
        self.start_btn = QtWidgets.QPushButton("Start Routine (1 min)")
        self.start_btn.setMinimumHeight(60)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #1976d2; }
            QPushButton:disabled { background-color: #555; color: #aaa; }
        """)
        self.start_btn.clicked.connect(self.start_routine)
        layout.addWidget(self.start_btn)

        # Reminder Settings Section
        reminder_frame = QtWidgets.QFrame()
        reminder_frame.setStyleSheet("background-color: #2d2d2d; border-radius: 10px; padding: 10px;")
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

        # Reward Info Box
        info_frame = QtWidgets.QFrame()
        info_frame.setStyleSheet("background-color: #2d2d2d; border-radius: 10px; padding: 10px;")
        info_layout = QtWidgets.QVBoxLayout(info_frame)
        
        self.stats_label = QtWidgets.QLabel()
        self.stats_label.setStyleSheet("color: #bbb; font-size: 14px;")
        self.stats_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        info_layout.addWidget(self.stats_label)
        layout.addWidget(info_frame)
        
        layout.addStretch()
    
    def _update_reminder_setting(self):
        """Save reminder settings when changed."""
        self.blocker.eye_reminder_enabled = self.reminder_checkbox.isChecked()
        self.blocker.eye_reminder_interval = self.reminder_interval.value()
        self.blocker.save_config()

    def get_daily_count(self):
        """Get number of routines performed today (reset at 5 AM)."""
        stats = self.blocker.stats.get("eye_protection", {})
        last_date_str = stats.get("last_date", "")
        count = stats.get("daily_count", 0)
        
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

    def update_stats_display(self):
        count = self.get_daily_count()
        # Legendary chance: 5% + 1% per routine (max 100%)
        # Drop chance: 1% + 1% per routine (max 100%)
        
        # User said: "It continues and resets at 5:00 AM." "starts at 1% chances... increases by 1% each next time"
        # So for the NEXT routine (count + 1):
        # Legendary chance (for the item IF dropped)
        leg_chance = min(100, 5 + count) 
        epic_chance = 100 - leg_chance
        
        # Actual drop chance
        drop_chance = min(100, 1 + count)
        
        text = (
            f"<b>Today's Routines: {count}</b><br><br>"
            f"Next Reward Chances:<br>"
            f"🎲 Item Drop Chance: <span style='color:#4caf50'>{drop_chance}%</span><br>"
            f"✨ If Item Drops: <span style='color:#a335ee'>{epic_chance}% Epic</span> / "
            f"<span style='color:#ff9800'>{leg_chance}% Legendary</span>"
        )
        self.stats_label.setText(text)

    def start_routine(self):
        # Check cooldown (20 minutes)
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
        new_count = current_count + 1
        
        # Calculate lottery chances (same logic as before)
        # Drop chance: 1% base + 1% per routine done today
        drop_chance = min(100, 1 + current_count) / 100.0
        # Tier chance: 5% base + 1% per routine for Legendary
        tier_chance = min(100, 5 + current_count) / 100.0
        
        # Save Stats first
        if "eye_protection" not in self.blocker.stats:
            self.blocker.stats["eye_protection"] = {}
            
        self.blocker.stats["eye_protection"]["last_date"] = datetime.now().isoformat()
        self.blocker.stats["eye_protection"]["daily_count"] = new_count
        self.blocker.save_stats()
        
        # Show the animated two-stage lottery dialog
        lottery = TwoStageLotteryDialog(
            drop_chance=drop_chance,
            tier_chance=tier_chance,
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
            
