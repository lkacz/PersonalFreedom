
import sys
import random
import time
import math
import os
import threading
import wave
import io
from pathlib import Path
from datetime import datetime, timedelta
from PySide6 import QtWidgets, QtCore, QtGui, QtSvg
from PySide6.QtCore import QSettings

from gamification import generate_item, get_entity_qol_perks, get_entity_eye_perks
from game_state import get_game_state
from entitidex.celebration_audio import CelebrationAudioManager, Synthesizer
from styled_dialog import styled_info, styled_warning, add_tab_help_button
from app_utils import get_app_dir

# Try to import piper for offline TTS
try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    PiperVoice = None


# No-Scroll Widgets - Prevents accidental value changes via scroll wheel
class NoScrollComboBox(QtWidgets.QComboBox):
    """A QComboBox that ignores scroll wheel events."""
    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        event.ignore()


class NoScrollSpinBox(QtWidgets.QSpinBox):
    """A QSpinBox that ignores scroll wheel events."""
    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        event.ignore()


# Base daily eye rest cap (can be increased by entity perks)
BASE_EYE_REST_CAP = 20

class EyeGuidanceSettings:
    """Manages persistence for guidance type."""
    KEY = "EyeGuidanceType"
    KEY_VOICE = "EyeGuidanceVoice" # New: Selected voice name
    
    MODE_SILENT = "Silent"
    MODE_SOUND = "Sound"
    MODE_VOICE = "Voice"
    
    @staticmethod
    def get_mode():
        s = QSettings("PersonalFreedom", "EyeProtection")
        return s.value(EyeGuidanceSettings.KEY, EyeGuidanceSettings.MODE_SOUND)

    @staticmethod
    def set_mode(mode):
        s = QSettings("PersonalFreedom", "EyeProtection")
        s.setValue(EyeGuidanceSettings.KEY, mode)

    @staticmethod
    def get_voice_name():
        s = QSettings("PersonalFreedom", "EyeProtection")
        return s.value(EyeGuidanceSettings.KEY_VOICE, "")

    @staticmethod
    def set_voice_name(name):
        s = QSettings("PersonalFreedom", "EyeProtection")
        s.setValue(EyeGuidanceSettings.KEY_VOICE, name)


class GuidanceManager(QtCore.QObject):
    """
    Manages audio and voice feedback for the eye routine.
    Uses Piper TTS for high-quality offline English voice synthesis.
    """
    _instance = None
    
    # Signal emitted from worker thread, delivered to GUI thread via queued connection
    tts_ready = QtCore.Signal(bytes)
    
    # Available voice models (relative to app directory)
    AVAILABLE_VOICES = {
        "Lessac (Female, US)": {
            "file": "voices/en_US-lessac-medium.onnx",
            "sample_rate": 22050,
        },
        "Ryan (Male, US - High Quality)": {
            "file": "voices/en_US-ryan-high.onnx",
            "sample_rate": 22050,
        },
    }
    DEFAULT_VOICE = "Lessac (Female, US)"
    
    def __init__(self):
        super().__init__()
        self.mode = EyeGuidanceSettings.get_mode()
        self._current_voice_name = EyeGuidanceSettings.get_voice_name() or self.DEFAULT_VOICE
        self._voice_sample_rate = 22050  # Default, updated when voice loads
        
        # Access audio manager for sound effects
        self.audio = CelebrationAudioManager.get_instance()
        # Pre-render eye sounds (and others) to prevent lag during routine
        self.audio.preload_all()
        
        # Connect TTS signal with queued connection for thread-safe GUI delivery
        self.tts_ready.connect(self._play_tts_audio, QtCore.Qt.ConnectionType.QueuedConnection)
        
        # Lock to serialize Piper calls (espeak-ng has global state)
        self._tts_lock = threading.Lock()
        
        # Initialize Piper TTS
        self.piper_voice = None
        self._init_piper()
    
    def _init_piper(self):
        """Initialize Piper voice for offline TTS."""
        if not PIPER_AVAILABLE:
            print("[GuidanceManager] Piper not available, voice mode disabled")
            return
            
        try:
            # Get voice config for selected voice
            voice_config = self.AVAILABLE_VOICES.get(self._current_voice_name)
            if not voice_config:
                voice_config = self.AVAILABLE_VOICES[self.DEFAULT_VOICE]
                self._current_voice_name = self.DEFAULT_VOICE
            
            # Find voice model path (use helper for PyInstaller compatibility)
            app_dir = get_app_dir()
            model_path = app_dir / voice_config["file"]
            
            if not model_path.exists():
                print(f"[GuidanceManager] Voice model not found: {model_path}")
                # Try fallback to default voice
                if self._current_voice_name != self.DEFAULT_VOICE:
                    print(f"[GuidanceManager] Trying default voice instead...")
                    self._current_voice_name = self.DEFAULT_VOICE
                    voice_config = self.AVAILABLE_VOICES[self.DEFAULT_VOICE]
                    model_path = app_dir / voice_config["file"]
                    if not model_path.exists():
                        return
                else:
                    return
            
            self.piper_voice = PiperVoice.load(str(model_path))
            self._voice_sample_rate = voice_config["sample_rate"]
            print(f"[GuidanceManager] Piper voice loaded: {model_path.name}")
            
        except Exception as e:
            print(f"[GuidanceManager] Failed to load Piper voice: {e}")
            self.piper_voice = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_voice_names(self):
        """Return available voice names."""
        # Return voices that have their model files present (use helper for PyInstaller compatibility)
        app_dir = get_app_dir()
        available = []
        for name, config in self.AVAILABLE_VOICES.items():
            model_path = app_dir / config["file"]
            if model_path.exists():
                available.append(name)
        return available
    
    def get_current_voice(self):
        """Return the currently selected voice name."""
        return self._current_voice_name

    def set_voice(self, name, save=True):
        """Set and load a different voice.
        
        Args:
            name: Voice name from AVAILABLE_VOICES
            save: Whether to persist the setting
            
        Returns:
            True if voice was loaded successfully
        """
        if name not in self.AVAILABLE_VOICES:
            return False
        
        # Check if model exists (use helper for PyInstaller compatibility)
        app_dir = get_app_dir()
        voice_config = self.AVAILABLE_VOICES[name]
        model_path = app_dir / voice_config["file"]
        if not model_path.exists():
            print(f"[GuidanceManager] Voice model not found: {model_path}")
            return False
        
        # Load the new voice
        self._current_voice_name = name
        if save:
            EyeGuidanceSettings.set_voice_name(name)
        
        # Re-initialize with new voice
        self.piper_voice = None
        self._init_piper()
        
        return self.piper_voice is not None
    
    @QtCore.Slot(bytes)
    def _play_tts_audio(self, pcm_44100: bytes):
        """Play TTS audio on the GUI thread (called via queued signal)."""
        from PySide6.QtCore import QByteArray
        qa = QByteArray(pcm_44100)
        self.audio.play_buffer(qa)
    
    def say(self, text: str):
        """Speak text using Piper TTS (non-blocking)."""
        if not self.piper_voice:
            print("[GuidanceManager] No piper voice available")
            return
        
        # Run synthesis in a worker thread to avoid blocking UI
        def _synthesize_worker():
            try:
                import array
                
                # Serialize Piper calls (espeak-ng phonemizer has global state)
                with self._tts_lock:
                    audio_chunks = [c.audio_int16_bytes for c in self.piper_voice.synthesize(text)]
                
                if not audio_chunks:
                    print("[GuidanceManager] No audio chunks generated")
                    return
                
                # Combine all chunks
                pcm_22050 = b''.join(audio_chunks)
                
                # Upsample from 22050 to 44100 by duplicating each sample
                samples = array.array('h')  # signed 16-bit
                samples.frombytes(pcm_22050)
                
                # Create upsampled array (2x size) - more efficient pre-allocation
                upsampled = array.array('h', [0]) * (2 * len(samples))
                for i, s in enumerate(samples):
                    upsampled[2*i] = s
                    upsampled[2*i + 1] = s
                
                pcm_44100 = upsampled.tobytes()
                
                # Emit signal - thread-safe, will be delivered to GUI thread
                self.tts_ready.emit(pcm_44100)
                
            except Exception as e:
                print(f"[GuidanceManager] TTS error: {e}")
                import traceback
                traceback.print_exc()
        
        # Start synthesis thread
        threading.Thread(target=_synthesize_worker, daemon=True).start()
    
    def set_mode(self, mode):
        self.mode = mode
        EyeGuidanceSettings.set_mode(mode)
        
        # Test sound
        if mode == EyeGuidanceSettings.MODE_VOICE:
            self.say("Voice guidance enabled.")
        elif mode == EyeGuidanceSettings.MODE_SOUND:
            self.audio.play("eye_blink_open")



    def play_start(self):
        if self.mode == EyeGuidanceSettings.MODE_SILENT: return
        
        if self.mode == EyeGuidanceSettings.MODE_VOICE:
            self.say("Starting eye routine. Relax.")
        else:
            # Transition sound - "Wind chime" effect
            self.audio.play("eye_start")

    def play_blink_close(self):
        if self.mode == EyeGuidanceSettings.MODE_SILENT: return
        
        if self.mode == EyeGuidanceSettings.MODE_VOICE:
            self.say("Close eyes.")
        else:
            # Gentle Low "Boop"
            self.audio.play("eye_blink_close")

    def play_blink_hold(self):
        # usually silent in hold, or quiet hum?
        if self.mode == EyeGuidanceSettings.MODE_SILENT: return
        
        if self.mode == EyeGuidanceSettings.MODE_VOICE:
            # self.say("Hold.") # Might be too chatty if repeated blinking
            pass 
        else:
            # Very quiet higher tone
            self.audio.play("eye_blink_hold")
            
    def play_blink_open(self):
        if self.mode == EyeGuidanceSettings.MODE_SILENT: return
        
        if self.mode == EyeGuidanceSettings.MODE_VOICE:
            self.say("Open.")
        else:
            # High ping
            self.audio.play("eye_blink_open")

    def play_gaze_start(self):
        if self.mode == EyeGuidanceSettings.MODE_SILENT: return
        
        if self.mode == EyeGuidanceSettings.MODE_VOICE:
            self.say("Look far away. Relax focus.")
        else:
            # Transition sound - "Wind chime" effect
            self.play_start() # Reuse start chime

    def play_tick(self):
        if self.mode == EyeGuidanceSettings.MODE_SILENT: return
        if self.mode == EyeGuidanceSettings.MODE_VOICE: return # No voice ticks
        
        # Soft woodblock click
        self.audio.play("eye_tick")

    def play_complete(self):
        if self.mode == EyeGuidanceSettings.MODE_SILENT: return
        
        if self.mode == EyeGuidanceSettings.MODE_VOICE:
            self.say("Session complete. Great job.")
        # Sound mode: no fanfare, silent completion

    def play_inhale(self):
        if self.mode == EyeGuidanceSettings.MODE_SILENT: return
        
        if self.mode == EyeGuidanceSettings.MODE_VOICE:
            self.say("Inhale deeply.")
        else:
            # Rising gentle wave (3 seconds)
            self.audio.play("eye_inhale")

    def play_exhale(self):
        if self.mode == EyeGuidanceSettings.MODE_SILENT: return
        
        if self.mode == EyeGuidanceSettings.MODE_VOICE:
            self.say("Exhale slowly.")
        else:
            # Falling gentle wave (4 seconds)
            self.audio.play("eye_exhale")

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
        
        # Audio Manager
        self.guidance = GuidanceManager.get_instance()
        
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
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        add_tab_help_button(layout, "eye", self)
        
        # Header row: Title + Cooldown Status
        header_row = QtWidgets.QHBoxLayout()
        header_row.setSpacing(10)
        
        title = QtWidgets.QLabel("👁️ Eye & Breath Relief")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #ffffff;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #66bb6a, stop:1 #43a047);
            padding: 10px 15px;
            border-radius: 8px;
            border: 2px solid #4caf50;
        """)
        header_row.addWidget(title, 1)
        
        # Cooldown status in header
        self.cooldown_status_label = QtWidgets.QLabel("✅ Ready!")
        self.cooldown_status_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #4caf50;
            background: #2d3436;
            padding: 10px 15px;
            border-radius: 8px;
            border: 2px solid #4caf50;
        """)
        self.cooldown_status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(self.cooldown_status_label)
        
        # Guidance Settings (New)
        guidance_label = QtWidgets.QLabel("Speaker:")
        guidance_label.setStyleSheet("color: #b0bec5; font-weight: bold; margin-left: 10px;")
        
        self.guidance_combo = NoScrollComboBox()
        self.guidance_combo.addItems([
            EyeGuidanceSettings.MODE_SILENT, 
            EyeGuidanceSettings.MODE_SOUND, 
            EyeGuidanceSettings.MODE_VOICE
        ])
        self.guidance_combo.setCurrentText(self.guidance.mode)
        self.guidance_combo.currentTextChanged.connect(self.guidance.set_mode)
        self.guidance_combo.setStyleSheet("""
            QComboBox {
                background: #2d3436;
                color: #e0e0e0;
                border: 1px solid #4caf50;
                border-radius: 4px;
                padding: 4px;
                min-width: 80px;
            }
            QComboBox QAbstractItemView {
                background: #2d3436;
                color: #e0e0e0;
                selection-background-color: #4caf50;
            }
        """)
        
        header_row.addWidget(guidance_label)
        header_row.addWidget(self.guidance_combo)

        # Voice Selection (Hidden by default unless Voice mode active)
        self.voice_combo = NoScrollComboBox()
        self.voice_combo.addItems(self.guidance.get_voice_names())
        
        # Set current selection
        current_voice = EyeGuidanceSettings.get_voice_name()
        if current_voice:
            self.voice_combo.setCurrentText(current_voice)
            
        self.voice_combo.currentTextChanged.connect(self.guidance.set_voice)
        self.voice_combo.setStyleSheet("""
            QComboBox {
                background: #2d3436;
                color: #e0e0e0;
                border: 1px solid #4caf50;
                border-radius: 4px;
                padding: 4px;
                min-width: 120px;
            }
            QComboBox QAbstractItemView {
                background: #2d3436;
                color: #e0e0e0;
                selection-background-color: #4caf50;
            }
        """)
        
        header_row.addWidget(self.voice_combo)
        
        # Initial visibility state
        self._update_voice_combo_visibility(self.guidance.mode)
        self.guidance_combo.currentTextChanged.connect(self._update_voice_combo_visibility)
        
        layout.addLayout(header_row)

        # Entity Perk Card (Sam's Focus) - shows when underdog_005 is collected
        self.entity_perk_card = QtWidgets.QFrame()
        self.entity_perk_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2e4a3f, stop:1 #1a2f26);
                border: 2px solid #66bb6a;
                border-radius: 10px;
                padding: 8px;
            }
        """)
        entity_perk_layout = QtWidgets.QHBoxLayout(self.entity_perk_card)
        entity_perk_layout.setContentsMargins(10, 5, 10, 5)
        entity_perk_layout.setSpacing(12)
        
        # SVG icon container
        self.entity_svg_label = QtWidgets.QLabel()
        self.entity_svg_label.setFixedSize(48, 48)
        self.entity_svg_label.setStyleSheet("background: transparent;")
        entity_perk_layout.addWidget(self.entity_svg_label)
        
        # Perk description
        self.entity_perk_label = QtWidgets.QLabel()
        self.entity_perk_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #a5d6a7;
            background: transparent;
        """)
        self.entity_perk_label.setWordWrap(True)
        entity_perk_layout.addWidget(self.entity_perk_label, 1)
        
        layout.addWidget(self.entity_perk_card)
        self.entity_perk_card.hide()  # Hidden until we check perks
        
        # Update entity perk display
        self._update_entity_perk_display()

        # =====================================================================
        # Owl Tips Section (Study Owl Athena - scholar_002) - Compact Layout
        # Shows daily eye protection tips when entity is collected
        # =====================================================================
        self.owl_tips_section = QtWidgets.QFrame()
        self.owl_tips_section.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a3a4a, stop:1 #1a2530);
                border: 2px solid #5c6bc0;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        owl_tips_layout = QtWidgets.QHBoxLayout(self.owl_tips_section)
        owl_tips_layout.setContentsMargins(8, 6, 8, 6)
        owl_tips_layout.setSpacing(10)
        
        # Left: Icon
        self.owl_icon_label = QtWidgets.QLabel()
        self.owl_icon_label.setFixedSize(40, 40)
        self.owl_icon_label.setStyleSheet("""
            QLabel {
                background: #333;
                border: 1px solid #444;
                border-radius: 4px;
            }
        """)
        owl_tips_layout.addWidget(self.owl_icon_label)
        
        # Middle: Title + Tip text (expandable)
        owl_content_col = QtWidgets.QVBoxLayout()
        owl_content_col.setSpacing(2)
        
        # Title row with entity name and tip number
        owl_title_row = QtWidgets.QHBoxLayout()
        self.owl_section_title = QtWidgets.QLabel("🦉 Study Owl Eye Care Tips")
        self.owl_section_title.setStyleSheet("color: #7986cb; font-size: 10px;")
        owl_title_row.addWidget(self.owl_section_title)
        
        self.owl_tip_number = QtWidgets.QLabel("Tip #1 of 100")
        self.owl_tip_number.setStyleSheet("color: #7986cb; font-size: 10px;")
        self.owl_tip_number.hide()  # Hidden - tip number not important
        owl_title_row.addWidget(self.owl_tip_number)
        owl_title_row.addStretch()
        owl_content_col.addLayout(owl_title_row)
        
        # Tip text (larger, more readable)
        self.owl_tip_text = QtWidgets.QLabel("Loading tip...")
        self.owl_tip_text.setStyleSheet("color: #e8eaf6; font-size: 14px;")
        self.owl_tip_text.setWordWrap(True)
        owl_content_col.addWidget(self.owl_tip_text)
        
        # Hidden entity name label (used for tracking)
        self.owl_entity_name = QtWidgets.QLabel("Study Owl Athena")
        self.owl_entity_name.hide()
        
        owl_tips_layout.addLayout(owl_content_col, 1)
        
        # Right: Acknowledge button (compact)
        self.owl_acknowledge_btn = QtWidgets.QPushButton("📖 +1🪙")
        self.owl_acknowledge_btn.setFixedWidth(70)
        self.owl_acknowledge_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5c6bc0, stop:1 #3949ab);
                color: white;
                font-size: 11px;
                font-weight: bold;
                border-radius: 4px;
                border: 1px solid #3f51b5;
                padding: 6px 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7986cb, stop:1 #5c6bc0);
            }
            QPushButton:disabled {
                background: #444;
                color: #777;
                border: 1px solid #333;
            }
        """)
        self.owl_acknowledge_btn.clicked.connect(self._acknowledge_owl_tip)
        owl_tips_layout.addWidget(self.owl_acknowledge_btn)
        
        layout.addWidget(self.owl_tips_section)
        self.owl_tips_section.hide()  # Hidden until we check if entity is collected
        
        # Refresh owl tips
        self._refresh_owl_tips()

        # Compact Instructions - collapsible hint
        instructions_hint = QtWidgets.QLabel(
            "<span style='color:#81c784;'>📋 Step A:</span> Low→CLOSE, High→HOLD, Silence→OPEN (5x) | "
            "<span style='color:#81c784;'>Step B:</span> Look far, Rising=INHALE(4s), Falling=EXHALE(6s)"
        )
        instructions_hint.setStyleSheet("""
            font-size: 11px;
            color: #b0bec5;
            background: #1a1a1a;
            padding: 6px 10px;
            border-radius: 6px;
            border: 1px solid #333;
        """)
        instructions_hint.setWordWrap(True)
        layout.addWidget(instructions_hint)

        # Combined action row: Status | Visual Cue | Start Button
        action_row = QtWidgets.QFrame()
        action_row.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3c72, stop:1 #2a5298);
                border: 2px solid #2196f3;
                border-radius: 10px;
                padding: 8px;
            }
        """)
        action_layout = QtWidgets.QHBoxLayout(action_row)
        action_layout.setContentsMargins(10, 8, 10, 8)
        action_layout.setSpacing(15)
        
        # Status label (shows instructions or current step during routine)
        self.status_label = QtWidgets.QLabel("📋 Ready")
        self.status_label.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #90caf9;
            background: transparent;
        """)
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumWidth(80)
        action_layout.addWidget(self.status_label)
        
        # Visual Cue (center, takes most space)
        self.cue_label = QtWidgets.QLabel("START WHEN READY")
        self.cue_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #64b5f6;
            background: transparent;
            padding: 10px;
        """)
        self.cue_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.cue_label.setMinimumHeight(60)
        action_layout.addWidget(self.cue_label, 1)
        
        # Start Button (right side)
        self.start_btn = QtWidgets.QPushButton("👁️ Start (1 min)")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setMinimumWidth(130)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66bb6a, stop:1 #43a047);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                border: 2px solid #4caf50;
                padding: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #81c784, stop:1 #66bb6a);
                border: 2px solid #66bb6a;
            }
            QPushButton:pressed {
                background: #388e3c;
                border: 2px solid #2e7d32;
            }
            QPushButton:disabled {
                background: #555555;
                border: 2px solid #444444;
                color: #888888;
            }
        """)
        self.start_btn.clicked.connect(self.start_routine)
        action_layout.addWidget(self.start_btn)
        
        layout.addWidget(action_row)

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
        
        self.reminder_interval = NoScrollSpinBox()
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

    def _update_voice_combo_visibility(self, mode):
        """Show voice combo box only when Voice mode is selected."""
        if mode == EyeGuidanceSettings.MODE_VOICE:
            self.voice_combo.show()
        else:
            self.voice_combo.hide()
    
    def _update_reminder_setting(self):
        """Save reminder settings when changed."""
        self.blocker.eye_reminder_enabled = self.reminder_checkbox.isChecked()
        self.blocker.eye_reminder_interval = self.reminder_interval.value()
        self.blocker.save_config()

    def _update_entity_perk_display(self):
        """Update the entity perk display card if Sam/Pam is collected."""
        try:
            adhd_data = getattr(self.blocker, 'adhd_buster', {})
            if not adhd_data:
                self.entity_perk_card.hide()
                return
                
            eye_perks = get_entity_eye_perks(adhd_data)
            tier_bonus = eye_perks.get("eye_tier_bonus", 0)
            reroll_chance = eye_perks.get("eye_reroll_chance", 0)
            
            # Hide if neither perk is active
            if tier_bonus <= 0 and reroll_chance <= 0:
                self.entity_perk_card.hide()
                return
            
            # Show the perk card
            entity_name = eye_perks.get("entity_name", "Desk Succulent Sam")
            is_exceptional = eye_perks.get("is_exceptional", False)
            
            # Update label text based on which perk is active
            if is_exceptional:
                # Pam: 50% Reroll only
                perk_text = (
                    f"<b>🌵 {entity_name}</b><br>"
                    f"<span style='color:#ffa726;'>{reroll_chance}% Reroll on Fail</span>"
                )
            else:
                # Sam: +1 Eye Tier only
                perk_text = (
                    f"<b>🌵 {entity_name}</b><br>"
                    f"<span style='color:#81c784;'>+{tier_bonus} Eye Tier</span>"
                )
            self.entity_perk_label.setText(perk_text)
            
            # Load and display SVG (static, not animated)
            self._load_entity_svg(is_exceptional)
            
            # Update border color for exceptional
            if is_exceptional:
                self.entity_perk_card.setStyleSheet("""
                    QFrame {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #3d2e4a, stop:1 #261a2f);
                        border: 2px solid #ba68c8;
                        border-radius: 10px;
                        padding: 8px;
                    }
                """)
            else:
                self.entity_perk_card.setStyleSheet("""
                    QFrame {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 #2e4a3f, stop:1 #1a2f26);
                        border: 2px solid #66bb6a;
                        border-radius: 10px;
                        padding: 8px;
                    }
                """)
            
            self.entity_perk_card.show()
            
        except Exception as e:
            print(f"[Eye Tab] Error updating entity perk display: {e}")
            self.entity_perk_card.hide()
    
    def _load_entity_svg(self, is_exceptional: bool):
        """Load Sam's SVG icon into the label (static, not animated)."""
        try:
            # Determine the SVG path (use helper for PyInstaller compatibility)
            base_path = str(get_app_dir())
            if is_exceptional:
                svg_path = os.path.join(base_path, "icons", "entities", "exceptional", 
                                        "underdog_005_desk_succulent_sam_exceptional.svg")
            else:
                svg_path = os.path.join(base_path, "icons", "entities", 
                                        "underdog_005_desk_succulent_sam.svg")
            
            if os.path.exists(svg_path):
                # Render SVG to pixmap (static rendering)
                renderer = QtSvg.QSvgRenderer(svg_path)
                if renderer.isValid():
                    pixmap = QtGui.QPixmap(48, 48)
                    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
                    painter = QtGui.QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    self.entity_svg_label.setPixmap(pixmap)
                else:
                    self.entity_svg_label.setText("🌵")
            else:
                self.entity_svg_label.setText("🌵")
        except Exception as e:
            print(f"[Eye Tab] Error loading SVG: {e}")
            self.entity_svg_label.setText("🌵")

    def _refresh_owl_tips(self) -> None:
        """Refresh the Study Owl Athena eye protection tips section."""
        from datetime import datetime
        
        OWL_ENTITY_ID = "scholar_002"  # Study Owl Athena
        
        try:
            from gamification import get_entitidex_manager
            from entitidex_tab import _resolve_entity_svg_path
            from entitidex.entity_pools import get_entity_by_id as get_entity
            from eye_protection_tips import get_tip_by_index, get_tip_count
        except ImportError as e:
            # Dependencies not available
            self.owl_tips_section.setVisible(False)
            return
        
        # Get entitidex manager to check entity collection
        try:
            manager = get_entitidex_manager(self.blocker.adhd_buster)
        except Exception:
            self.owl_tips_section.setVisible(False)
            return
        
        # Check if user has collected Athena (normal or exceptional)
        has_normal = OWL_ENTITY_ID in manager.progress.collected_entity_ids
        has_exceptional = manager.progress.is_exceptional(OWL_ENTITY_ID)
        
        if not has_normal and not has_exceptional:
            # Entity not collected - hide section
            self.owl_tips_section.setVisible(False)
            return
        
        # Entity is collected - show section
        self.owl_tips_section.setVisible(True)
        
        # Determine if we use exceptional tips
        is_exceptional = has_exceptional
        
        # Update section title based on variant
        if is_exceptional:
            self.owl_section_title.setText("⭐ Study Owl (Exceptional) Advanced Eye Tips")
            self.owl_section_title.setStyleSheet("color: #ffd700; padding: 4px;")
            self.owl_entity_name.setText("⭐ Study Owl Athena")
            self.owl_entity_name.setStyleSheet("color: #ffd700; font-weight: bold; font-size: 12px;")
        else:
            self.owl_section_title.setText("🦉 Study Owl Eye Care Tips")
            self.owl_section_title.setStyleSheet("color: #9fa8da; padding: 4px;")
            self.owl_entity_name.setText("Study Owl Athena")
            self.owl_entity_name.setStyleSheet("color: #e5e7eb; font-weight: bold; font-size: 12px;")
        
        # Load entity icon
        try:
            entity = get_entity(OWL_ENTITY_ID)
            if entity:
                svg_path = _resolve_entity_svg_path(entity, is_exceptional)
                if svg_path:
                    renderer = QtSvg.QSvgRenderer(svg_path)
                    if renderer.isValid():
                        icon_size = 48
                        pixmap = QtGui.QPixmap(icon_size, icon_size)
                        pixmap.fill(QtCore.Qt.transparent)
                        painter = QtGui.QPainter(pixmap)
                        renderer.render(painter)
                        painter.end()
                        self.owl_icon_label.setPixmap(pixmap)
                        
                        # Update icon border for exceptional
                        if is_exceptional:
                            self.owl_icon_label.setStyleSheet("""
                                QLabel {
                                    background: #333;
                                    border: 2px solid #ffd700;
                                    border-radius: 6px;
                                }
                            """)
                        else:
                            self.owl_icon_label.setStyleSheet("""
                                QLabel {
                                    background: #333;
                                    border: 1px solid #444;
                                    border-radius: 6px;
                                }
                            """)
        except Exception:
            # Fallback - just show text
            self.owl_icon_label.setText("🦉")
        
        # Get current tip index (sequential cycling)
        tip_key = "owl_tip_index_exceptional" if is_exceptional else "owl_tip_index"
        tip_index = self.blocker.stats.get(tip_key, 0)
        total_tips = get_tip_count(is_exceptional)
        
        # Get the tip at current index
        tip_text, category_emoji = get_tip_by_index(tip_index, is_exceptional)
        
        # Update tip display
        self.owl_tip_number.setText(f"Tip #{tip_index + 1} of {total_tips}")
        self.owl_tip_text.setText(f"{category_emoji} {tip_text}")
        
        # Check if already acknowledged today
        today_str = datetime.now().strftime("%Y-%m-%d")
        ack_key = "owl_tip_acknowledged_date_exceptional" if is_exceptional else "owl_tip_acknowledged_date"
        last_acknowledged = self.blocker.stats.get(ack_key, "")
        
        if last_acknowledged == today_str:
            # Already acknowledged today
            self.owl_acknowledge_btn.setText("✓ Done")
            self.owl_acknowledge_btn.setEnabled(False)
        else:
            # Can acknowledge
            self.owl_acknowledge_btn.setText("📖 +1🪙")
            self.owl_acknowledge_btn.setEnabled(True)

    def _acknowledge_owl_tip(self) -> None:
        """Handle acknowledging the owl tip - award coin and advance to next tip."""
        from datetime import datetime
        from eye_protection_tips import get_tip_count
        
        try:
            # Determine if exceptional
            from gamification import get_entitidex_manager
            manager = get_entitidex_manager(self.blocker.adhd_buster)
            is_exceptional = manager.progress.is_exceptional("scholar_002")
            
            # Get keys based on variant
            tip_key = "owl_tip_index_exceptional" if is_exceptional else "owl_tip_index"
            ack_key = "owl_tip_acknowledged_date_exceptional" if is_exceptional else "owl_tip_acknowledged_date"
            
            # Get current index and total
            current_index = self.blocker.stats.get(tip_key, 0)
            total_tips = get_tip_count(is_exceptional)
            
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
            self.blocker.save_stats()
            
            # Update button to show collected
            self.owl_acknowledge_btn.setText("✓ Done")
            self.owl_acknowledge_btn.setEnabled(False)
            
        except Exception as e:
            print(f"[Eye Tab] Error acknowledging owl tip: {e}")

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
        
        # Get entity perk tier bonus
        tier_bonus = 0
        try:
            adhd_data = getattr(self.blocker, 'adhd_buster', {})
            if adhd_data:
                eye_perks = get_entity_eye_perks(adhd_data)
                tier_bonus = eye_perks.get("eye_tier_bonus", 0)
        except Exception:
            pass
        
        # Apply tier bonus (capped at tier 4 = Legendary)
        effective_tier = min(window_tier + tier_bonus, 4)
        
        base_tier = tier_names[window_tier]
        base_color = tier_colors[window_tier]
        effective_tier_name = tier_names[effective_tier]
        effective_color = tier_colors[effective_tier]
        success_rate = success_rates[window_tier]
        
        # Show which window we're in
        window_start = window_tier * 4 + 1
        window_end = min((window_tier + 1) * 4, daily_cap)
        
        # Build tier display text
        if tier_bonus > 0:
            tier_display = (
                f"<span style='color:{base_color};'>{base_tier}</span> "
                f"<span style='color:#66bb6a;'>→</span> "
                f"<span style='color:{effective_color};'><b>{effective_tier_name}</b></span> "
                f"<span style='color:#a5d6a7;'>(+{tier_bonus} 🌵)</span>"
            )
        else:
            tier_display = f"<span style='color:{base_color};'>{window_start}-{window_end} ({base_tier}-centered)</span>"
        
        text = (
            f"<b>Today's Routines: {count} / {daily_cap}</b><br><br>"
            f"Next Routine: {tier_display}<br>"
            f"🎲 Success Rate: <span style='color:#4caf50'>{success_rate}%</span><br>"
            f"🎰 Tier Distribution: [5%, 15%, <span style='color:{effective_color};'><b>60%</b></span>, 15%, 5%]"
        )
        self.stats_label.setText(text)

    def start_routine(self):
        # Cooldown check is now handled by _update_cooldown_display
        # Double-check before starting
        count = self.get_daily_count()
        daily_cap = self.get_daily_cap()
        if count >= daily_cap:
            styled_info(self, "Daily Limit", f"You've reached the daily limit of {daily_cap} routines!")
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
                    styled_warning(self, "Resting Eyes", f"Your eyes need to work a bit before resting again!\nWait {remaining} minutes.")
                    return

        self.is_running = True
        self.start_btn.setEnabled(False)
        self.step_phase = "blinking"
        self.blink_count = 0
        self.blink_state = "ready"
        
        # Sound
        self.guidance.play_start()
        
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
        self.guidance.play_blink_close()
        
        # Schedule next sub-steps
        # Close duration ~1.5s -> Then Hold signal
        QtCore.QTimer.singleShot(1500, self.do_blink_hold)
        
    def do_blink_hold(self):
        # Guard: Don't run if routine stopped
        if not self.is_running:
            return
        self.blink_state = "hold"
        self.cue_label.setText("HOLD...")
        self.guidance.play_blink_hold()
        # Hold duration ~0.5s -> Then Open (Silence)
        QtCore.QTimer.singleShot(500, self.do_blink_open)
        
    def do_blink_open(self):
        # Guard: Don't run if routine stopped
        if not self.is_running:
            return
        self.blink_state = "open"
        self.cue_label.setText("OPEN eyes")
        self.guidance.play_blink_open() # Is silent
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
        self.guidance.play_gaze_start()
        
        # Delay first tick to allow "Look far away" voice cue to complete
        # before the first "Inhale" cue plays (prevents audio overlap)
        QtCore.QTimer.singleShot(2000, self._start_breathing_timer)

    def _start_breathing_timer(self):
        """Start the breathing timer after initial gaze cue completes."""
        # Guard: Don't run if routine was stopped during the delay
        if not self.is_running or self.step_phase != "gazing":
            return
        self.timer.start(1000)  # One tick per second
        self.on_timer_tick()  # Execute first tick immediately

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
                        self.guidance.play_inhale()
                    self.cue_label.setText(f"Look away + INHALE... {t-16}")
                elif t > 10:  # Exhale 1
                    if t == 16:
                        self.guidance.play_exhale()
                    self.cue_label.setText(f"Look away + EXHALE... {t-10}")
                elif t > 6:  # Inhale 2
                    if t == 10:
                        self.guidance.play_inhale()
                    self.cue_label.setText(f"Look away + INHALE... {t-6}")
                elif t > 0:  # Exhale 2
                    if t == 6:
                        self.guidance.play_exhale()
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
        self.guidance.play_complete()
        
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
        
        # Get entity perk tier bonus and reroll chance
        tier_bonus = 0
        reroll_chance = 0
        entity_name = ""
        try:
            adhd_data = getattr(self.blocker, 'adhd_buster', {})
            if adhd_data:
                eye_perks = get_entity_eye_perks(adhd_data)
                tier_bonus = eye_perks.get("eye_tier_bonus", 0)
                reroll_chance = eye_perks.get("eye_reroll_chance", 0)
                entity_name = eye_perks.get("entity_name", "")
        except Exception:
            pass
        
        # Apply tier bonus (capped at tier 4 = Legendary)
        effective_tier = min(window_tier + tier_bonus, 4)
        
        # Success rate decreases: 99%, 80%, 60%, 40%, 20%
        success_rates = [0.99, 0.80, 0.60, 0.40, 0.20]
        success_rate = success_rates[min(window_tier, len(success_rates) - 1)]
        
        # Map tier to base rarity (using effective tier with bonus!)
        tier_names = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
        base_rarity = tier_names[effective_tier]
        
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
            success_roll=-1,  # Auto-generate random roll (negative = generate)
            success_threshold=success_rate,
            tier_upgrade_enabled=False,
            base_rarity=base_rarity,
            title="👁️‍🗨️ Eye & Breath Reward 👁️‍🗨️",
            parent=self
        )
        lottery.exec()
        
        # Get results after animation completes
        won_item, tier = lottery.get_results()
        
        # ✨ REROLL MECHANIC: If failed and have reroll chance, try again (50% probability)
        if not won_item and reroll_chance > 0:
            # 50% chance to get the opportunity to reroll
            if random.randint(1, 100) <= reroll_chance:
                # Show reroll message
                styled_info(
                    self, 
                    f"{entity_name}'s Second Chance! 🌵",
                    f"{entity_name} grants you another roll!\n\n"
                    f"\"If I can survive fluorescent lights, you can survive this!\""
                )
                
                # Do the reroll with same parameters
                lottery2 = MergeTwoStageLotteryDialog(
                    success_roll=-1,  # Auto-generate random roll
                    success_threshold=success_rate,
                    tier_upgrade_enabled=False,
                    base_rarity=base_rarity,
                    title="🌀 Second Chance Roll 🌀",
                    parent=self
                )
                lottery2.exec()
                won_item, tier = lottery2.get_results()
        
        # Update cooldown display and stats after completion (before item handling)
        self._update_cooldown_display()
        self.update_stats_display()
        
        if won_item:
            # Generate Item
            adhd_data = getattr(self.blocker, 'adhd_buster', {})
            story_theme = adhd_data.get('story_active', 'warrior') if adhd_data else 'warrior'
            
            new_item = generate_item(rarity=tier, story_id=story_theme, adhd_buster=adhd_data)
            
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
