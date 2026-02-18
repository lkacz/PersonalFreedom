
import sys
import random
import time
import math
import os
import threading
import wave
import io
import functools
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from PySide6 import QtWidgets, QtCore, QtGui, QtSvg
from PySide6.QtCore import QSettings

from gamification import generate_item, get_entity_qol_perks, get_entity_eye_perks
from game_state import get_game_state
from entitidex.celebration_audio import CelebrationAudioManager, Synthesizer
from styled_dialog import styled_info, styled_warning, add_tab_help_button
from app_utils import get_app_dir

# Try to import piper for offline TTS
# Note: Import success doesn't guarantee runtime availability (espeak-ng dependencies)
# We'll verify actual functionality in GuidanceManager._init_piper()
try:
    from piper import PiperVoice
    PIPER_IMPORT_OK = True
except ImportError:
    PIPER_IMPORT_OK = False
    PiperVoice = None

# This flag gets set to True only after we successfully load and test a voice
PIPER_WORKING = False


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
        global PIPER_WORKING
        
        if not PIPER_IMPORT_OK:
            print("[GuidanceManager] Piper not available (import failed), voice mode disabled")
            PIPER_WORKING = False
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
                        PIPER_WORKING = False
                        return
                else:
                    PIPER_WORKING = False
                    return
            
            self.piper_voice = PiperVoice.load(str(model_path))
            self._voice_sample_rate = voice_config["sample_rate"]
            print(f"[GuidanceManager] Piper voice loaded: {model_path.name}")
            PIPER_WORKING = True
            
        except Exception as e:
            print(f"[GuidanceManager] Failed to load Piper voice: {e}")
            import traceback
            traceback.print_exc()
            self.piper_voice = None
            PIPER_WORKING = False
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_voice_names(self):
        """Return available voice names (only if Piper is working)."""
        # If Piper isn't working, return empty list to prevent showing Voice mode
        if not PIPER_WORKING:
            return []
        
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
        try:
            # If Piper isn't working, don't even try
            if not PIPER_WORKING:
                print("[GuidanceManager] Piper not working, cannot set voice")
                return False
            
            # Guard against empty or invalid names (can happen from combo box signals)
            if not name or name not in self.AVAILABLE_VOICES:
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
        except Exception as e:
            print(f"[GuidanceManager] Error setting voice '{name}': {e}")
            return False
    
    @QtCore.Slot(bytes)
    def _play_tts_audio(self, pcm_44100: bytes):
        """Play TTS audio on the GUI thread (called via queued signal)."""
        from PySide6.QtCore import QByteArray
        qa = QByteArray(pcm_44100)
        self.audio.play_buffer(qa, is_voice=True)
    
    def say(self, text: str):
        """Speak text using Piper TTS (non-blocking)."""
        if not PIPER_WORKING or not self.piper_voice:
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
        # If trying to set Voice mode but Piper isn't working, fall back to Sound
        if mode == EyeGuidanceSettings.MODE_VOICE and not PIPER_WORKING:
            print("[GuidanceManager] Piper not available, falling back to Sound mode")
            mode = EyeGuidanceSettings.MODE_SOUND
        
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


# =============================================================================
# EyeProtectionChartWidget - Industry-Standard Progress Visualization
# =============================================================================

class EyeProtectionChartWidget(QtWidgets.QWidget):
    """Custom widget that draws an eye protection routine progress chart.
    
    Features:
    - Daily routine count bar chart with gradient fills
    - Daily goal/cap line visualization
    - Streak indicators for consecutive days
    - 7-day rolling average trend line
    - Item tier distribution pie chart overlay
    - Interactive tooltips with daily details
    - Zoom/pan support for large date ranges
    - Cached rendering for performance
    
    Industry Standards Applied:
    - Type hints throughout for IDE support
    - Proper resource cleanup via context managers
    - Defensive programming with input validation
    - Consistent coordinate system transformations
    - Accessibility support (screen reader hints)
    - LRU caching for expensive date parsing
    """
    
    # Display mode thresholds
    WEEKLY_BIN_THRESHOLD: int = 30
    MOVING_AVG_WINDOW: int = 7
    
    # Display constants
    MIN_HEIGHT: int = 280
    MIN_WIDTH: int = 450
    MARGIN_LEFT: int = 50
    MARGIN_RIGHT: int = 25
    MARGIN_TOP: int = 45
    MARGIN_BOTTOM: int = 55
    GRID_LINES: int = 5
    BAR_WIDTH: float = 0.7  # Fraction of available space
    LINE_WIDTH: int = 2
    
    # Theme colors - eye protection themed (greens and teals)
    COLORS = {
        "background": "#1a1a2e",
        "border": "#4a6a4a",
        "grid": "#335533",
        "text": "#888888",
        "text_light": "#aaaaaa",
        "bar_full": "#4CAF50",           # Green - met daily cap
        "bar_high": "#66BB6A",           # Light green - above average
        "bar_mid": "#81C784",             # Lighter green - average
        "bar_low": "#A5D6A7",             # Pale green - below average
        "bar_zero": "#455A64",            # Gray - no routines
        "line_ma": "#FF9800",             # Orange for moving average
        "cap_line": "#4CAF50",            # Green cap line
        "streak_glow": "#FFD700",         # Gold for streaks
        "tier_common": "#9e9e9e",
        "tier_uncommon": "#4caf50",
        "tier_rare": "#2196f3",
        "tier_epic": "#9c27b0",
        "tier_legendary": "#ff9800",
        "gradient_top": (129, 199, 132, 150),     # Light green
        "gradient_bottom": (56, 142, 60, 40),    # Dark green
    }
    
    # Daily routine cap (can be overridden)
    DEFAULT_DAILY_CAP: int = 20
    
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        
        # Data storage
        self._routine_history: List[Dict] = []  # [{date: str, count: int, items_won: int, tiers: list}]
        self._daily_cap: int = self.DEFAULT_DAILY_CAP
        
        # Calculation cache
        self._cache_valid: bool = False
        self._cached_trend: Optional[Tuple[str, float, float]] = None
        self._cached_moving_avg: Optional[List[Tuple[str, float]]] = None
        self._cached_weekly_bins: Optional[List[Dict]] = None
        self._cached_daily_totals: Optional[Dict[str, Dict]] = None
        self._cached_streaks: Optional[List[Tuple[str, str, int]]] = None
        
        # Interaction state
        self._hover_bar_date: Optional[str] = None
        self._zoom_level: float = 1.0
        self._pan_offset_x: float = 0.0
        self._is_panning: bool = False
        self._last_mouse_pos: Optional[QtCore.QPoint] = None
        
        # Display settings
        self.setMinimumHeight(self.MIN_HEIGHT)
        self.setMinimumWidth(self.MIN_WIDTH)
        self.setMouseTracking(True)
        
        # Accessibility
        self.setAccessibleName("Eye Protection Progress Chart")
        self.setAccessibleDescription("Visual chart showing eye protection routine completion over time")
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def set_data(self, history: List[Dict], daily_cap: int = 20) -> None:
        """Set the routine history data to display.
        
        Args:
            history: List of history dicts with keys:
                - date: str (YYYY-MM-DD format)
                - count: int (routines completed that day)
                - items_won: int (optional, items received)
                - tiers: list (optional, tier names of items won)
            daily_cap: Daily routine cap (default 20)
        """
        if history is None:
            history = []
        
        # Validate entries
        valid_entries: List[Dict] = []
        for e in history:
            if not isinstance(e, dict):
                continue
            
            date_str = e.get("date")
            if not date_str or not isinstance(date_str, str):
                continue
            
            # Validate date format
            if not self._parse_date(date_str):
                continue
            
            valid_entry = {
                "date": date_str,
                "count": max(0, int(e.get("count", 0))),
                "items_won": max(0, int(e.get("items_won", 0))),
                "tiers": e.get("tiers", []) if isinstance(e.get("tiers", []), list) else [],
            }
            valid_entries.append(valid_entry)
        
        # Sort by date
        valid_entries.sort(key=lambda x: x["date"])
        
        # Remove duplicates (keep last entry for each date)
        seen_dates: Dict[str, Dict] = {}
        for entry in valid_entries:
            seen_dates[entry["date"]] = entry
        valid_entries = list(seen_dates.values())
        valid_entries.sort(key=lambda x: x["date"])
        
        # Update state
        self._routine_history = valid_entries
        self._daily_cap = max(1, daily_cap)
        
        # Invalidate cache
        self._invalidate_cache()
        
        # Reset interaction state
        self._hover_bar_date = None
        self._zoom_level = 1.0
        self._pan_offset_x = 0.0
        
        self.update()
    
    def reset_view(self) -> None:
        """Reset zoom and pan to default view."""
        self._zoom_level = 1.0
        self._pan_offset_x = 0.0
        self.update()
    
    # =========================================================================
    # Cache management
    # =========================================================================
    
    def _invalidate_cache(self) -> None:
        """Invalidate all cached calculations."""
        self._cache_valid = False
        self._cached_trend = None
        self._cached_moving_avg = None
        self._cached_weekly_bins = None
        self._cached_daily_totals = None
        self._cached_streaks = None
    
    def _ensure_cache(self) -> None:
        """Ensure cached calculations are up to date."""
        if self._cache_valid:
            return
        
        self._cached_daily_totals = self._calculate_daily_totals_impl()
        self._cached_trend = self._calculate_trend_impl()
        self._cached_moving_avg = self._calculate_moving_average_impl()
        self._cached_weekly_bins = self._calculate_weekly_bins_impl()
        self._cached_streaks = self._calculate_streaks_impl()
        self._cache_valid = True
    
    # =========================================================================
    # Date parsing with caching
    # =========================================================================
    
    @staticmethod
    @functools.lru_cache(maxsize=512)
    def _parse_date_cached(date_str: str) -> Optional[datetime]:
        """Parse date string with LRU caching for performance."""
        if not date_str or not isinstance(date_str, str):
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime."""
        return self._parse_date_cached(date_str)
    
    # =========================================================================
    # Statistical calculations
    # =========================================================================
    
    def _calculate_daily_totals_impl(self) -> Dict[str, Dict]:
        """Calculate daily aggregates from history.
        
        Returns:
            Dict mapping date string to {count, items_won, tiers, met_cap}
        """
        totals: Dict[str, Dict] = {}
        
        for entry in self._routine_history:
            date_str = entry["date"]
            count = entry.get("count", 0)
            items_won = entry.get("items_won", 0)
            tiers = entry.get("tiers", [])
            
            totals[date_str] = {
                "count": count,
                "items_won": items_won,
                "tiers": tiers,
                "met_cap": count >= self._daily_cap,
            }
        
        return totals
    
    def _calculate_trend_impl(self) -> Optional[Tuple[str, float, float]]:
        """Calculate linear trend using simple regression.
        
        Returns:
            Tuple of (direction, slope, r_squared) or None
        """
        if len(self._routine_history) < 3:
            return None
        
        entries = self._routine_history[-30:]  # Last 30 days max
        
        if len(entries) < 3:
            return None
        
        # Use indices as x values
        n = len(entries)
        x_vals = list(range(n))
        y_vals = [e.get("count", 0) for e in entries]
        
        # Calculate means
        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n
        
        # Calculate slope and intercept
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        
        if abs(denominator) < 0.0001:
            return None
        
        slope = numerator / denominator
        
        # Calculate R-squared
        y_pred = [x_mean + slope * (x - x_mean) + y_mean for x in x_vals]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(y_vals, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
        
        if abs(ss_tot) < 0.0001:
            r_squared = 0.0
        else:
            r_squared = max(0, 1 - ss_res / ss_tot)
        
        # Determine direction
        if slope > 0.05:
            direction = "improving"
        elif slope < -0.05:
            direction = "declining"
        else:
            direction = "stable"
        
        return (direction, slope, r_squared)
    
    def _calculate_moving_average_impl(self) -> List[Tuple[str, float]]:
        """Calculate 7-day moving average.
        
        Returns:
            List of (date_str, average_count) tuples
        """
        if len(self._routine_history) < self.MOVING_AVG_WINDOW:
            return []
        
        result: List[Tuple[str, float]] = []
        window: List[int] = []
        
        for entry in self._routine_history:
            count = entry.get("count", 0)
            window.append(count)
            
            if len(window) > self.MOVING_AVG_WINDOW:
                window.pop(0)
            
            if len(window) == self.MOVING_AVG_WINDOW:
                avg = sum(window) / len(window)
                result.append((entry["date"], avg))
        
        return result
    
    def _calculate_weekly_bins_impl(self) -> List[Dict]:
        """Calculate weekly aggregations for large date ranges.
        
        Returns:
            List of {week_start, week_end, total_count, avg_count, days_active, items_won}
        """
        if not self._routine_history:
            return []
        
        weeks: Dict[str, Dict] = {}
        
        for entry in self._routine_history:
            dt = self._parse_date(entry["date"])
            if not dt:
                continue
            
            # Get Monday of the week
            week_start = dt - timedelta(days=dt.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            week_end = week_start + timedelta(days=6)
            
            if week_key not in weeks:
                weeks[week_key] = {
                    "week_start": week_key,
                    "week_end": week_end.strftime("%Y-%m-%d"),
                    "total_count": 0,
                    "days": [],
                    "items_won": 0,
                }
            
            weeks[week_key]["total_count"] += entry.get("count", 0)
            weeks[week_key]["days"].append(entry.get("count", 0))
            weeks[week_key]["items_won"] += entry.get("items_won", 0)
        
        # Calculate averages
        result: List[Dict] = []
        for week_key in sorted(weeks.keys()):
            week = weeks[week_key]
            days_active = len(week["days"])
            avg_count = week["total_count"] / days_active if days_active > 0 else 0
            result.append({
                "week_start": week["week_start"],
                "week_end": week["week_end"],
                "total_count": week["total_count"],
                "avg_count": avg_count,
                "days_active": days_active,
                "items_won": week["items_won"],
            })
        
        return result
    
    def _calculate_streaks_impl(self) -> List[Tuple[str, str, int]]:
        """Calculate streaks of consecutive days with routines.
        
        Returns:
            List of (start_date, end_date, length) tuples for significant streaks (3+ days)
        """
        if not self._routine_history:
            return []
        
        streaks: List[Tuple[str, str, int]] = []
        current_streak_start: Optional[str] = None
        current_streak_end: Optional[str] = None
        current_streak_len: int = 0
        last_date: Optional[datetime] = None
        
        for entry in self._routine_history:
            if entry.get("count", 0) <= 0:
                # Day with no routines breaks streak
                if current_streak_len >= 3 and current_streak_start and current_streak_end:
                    streaks.append((current_streak_start, current_streak_end, current_streak_len))
                current_streak_start = None
                current_streak_end = None
                current_streak_len = 0
                last_date = None
                continue
            
            dt = self._parse_date(entry["date"])
            if not dt:
                continue
            
            if last_date is None:
                # Start new streak
                current_streak_start = entry["date"]
                current_streak_end = entry["date"]
                current_streak_len = 1
            else:
                # Check if consecutive
                delta = (dt - last_date).days
                if delta == 1:
                    # Continue streak
                    current_streak_end = entry["date"]
                    current_streak_len += 1
                else:
                    # Gap - save previous streak if significant
                    if current_streak_len >= 3 and current_streak_start and current_streak_end:
                        streaks.append((current_streak_start, current_streak_end, current_streak_len))
                    # Start new streak
                    current_streak_start = entry["date"]
                    current_streak_end = entry["date"]
                    current_streak_len = 1
            
            last_date = dt
        
        # Don't forget the last streak
        if current_streak_len >= 3 and current_streak_start and current_streak_end:
            streaks.append((current_streak_start, current_streak_end, current_streak_len))
        
        return streaks
    
    def _get_current_streak(self) -> int:
        """Get the current active streak length (includes today or yesterday)."""
        if not self._routine_history:
            return 0
        
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Check if most recent entry is today or yesterday
        last_entry = self._routine_history[-1]
        last_date = last_entry.get("date", "")
        
        if last_date not in (today, yesterday) or last_entry.get("count", 0) <= 0:
            return 0
        
        # Count backwards from last entry
        streak = 0
        last_dt = None
        
        for entry in reversed(self._routine_history):
            if entry.get("count", 0) <= 0:
                break
            
            dt = self._parse_date(entry["date"])
            if not dt:
                continue
            
            if last_dt is None:
                streak = 1
            else:
                delta = (last_dt - dt).days
                if delta == 1:
                    streak += 1
                else:
                    break
            
            last_dt = dt
        
        return streak
    
    # =========================================================================
    # Drawing
    # =========================================================================
    
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Main paint handler - orchestrates all drawing.
        
        Uses try/finally to guarantee QPainter cleanup on any exception.
        """
        painter = QtGui.QPainter(self)
        try:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            
            self._ensure_cache()
            
            # Background
            self._draw_background(painter)
            
            # Handle empty state
            if not self._routine_history:
                self._draw_empty_state(painter)
                return
            
            # Determine display mode
            num_days = len(self._routine_history)
            use_weekly = num_days > self.WEEKLY_BIN_THRESHOLD
            
            # Calculate drawing area
            rect = self.rect()
            chart_left = self.MARGIN_LEFT
            chart_right = rect.width() - self.MARGIN_RIGHT
            chart_top = self.MARGIN_TOP
            chart_bottom = rect.height() - self.MARGIN_BOTTOM
            chart_width = chart_right - chart_left
            chart_height = chart_bottom - chart_top
            
            if chart_width <= 0 or chart_height <= 0:
                return
            
            # Apply zoom/pan transform with nested try/finally for restore
            painter.save()
            try:
                painter.translate(chart_left + self._pan_offset_x, 0)
                painter.scale(max(0.1, self._zoom_level), 1.0)  # Prevent zero scale
                painter.translate(-chart_left, 0)
                
                # Draw components
                self._draw_grid(painter, chart_left, chart_top, chart_width, chart_height)
                
                if use_weekly:
                    self._draw_weekly_bars(painter, chart_left, chart_top, chart_width, chart_height)
                else:
                    self._draw_daily_bars(painter, chart_left, chart_top, chart_width, chart_height)
                    self._draw_cap_line(painter, chart_left, chart_top, chart_width, chart_height)
                    self._draw_moving_average(painter, chart_left, chart_top, chart_width, chart_height)
            finally:
                painter.restore()
            
            # Draw axes (not transformed)
            self._draw_axes(painter, chart_left, chart_top, chart_width, chart_height, use_weekly)
            
            # Draw title and legend
            self._draw_title(painter, rect)
            self._draw_legend(painter, rect, use_weekly)
            
            # Draw hover tooltip
            self._draw_tooltip(painter)
            
            # Draw streak indicator
            self._draw_streak_indicator(painter, rect)
        except Exception as e:
            # Log but don't crash - charts should be robust
            import logging
            logging.warning(f"EyeProtectionChartWidget.paintEvent error: {e}")
        finally:
            painter.end()
    
    def _draw_background(self, painter: QtGui.QPainter) -> None:
        """Draw chart background."""
        painter.fillRect(self.rect(), QtGui.QColor(self.COLORS["background"]))
        
        # Border
        pen = QtGui.QPen(QtGui.QColor(self.COLORS["border"]), 1)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
    
    def _draw_empty_state(self, painter: QtGui.QPainter) -> None:
        """Draw placeholder when no data."""
        font = painter.font()
        font.setPointSize(14)
        painter.setFont(font)
        painter.setPen(QtGui.QColor(self.COLORS["text_light"]))
        
        text = "đź‘ď¸Ź No eye protection history yet\nComplete routines to see your progress!"
        painter.drawText(self.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, text)
    
    def _draw_grid(self, painter: QtGui.QPainter, left: int, top: int, 
                   width: int, height: int) -> None:
        """Draw horizontal grid lines."""
        pen = QtGui.QPen(QtGui.QColor(self.COLORS["grid"]), 1, QtCore.Qt.PenStyle.DashLine)
        painter.setPen(pen)
        
        for i in range(1, self.GRID_LINES):
            y = top + (height * i // self.GRID_LINES)
            painter.drawLine(int(left), int(y), int(left + width), int(y))
    
    def _draw_daily_bars(self, painter: QtGui.QPainter, left: int, top: int,
                         width: int, height: int) -> None:
        """Draw individual bars for daily data."""
        num_days = len(self._routine_history)
        if num_days == 0:
            return
        
        bar_spacing = width / max(num_days, 1)
        bar_width = max(4, bar_spacing * self.BAR_WIDTH)
        
        # Find max value for scaling
        max_count = max(e.get("count", 0) for e in self._routine_history)
        max_count = max(max_count, self._daily_cap, 1)  # Ensure cap is visible
        
        for i, entry in enumerate(self._routine_history):
            count = entry.get("count", 0)
            date_str = entry["date"]
            met_cap = count >= self._daily_cap
            
            # Calculate bar geometry
            x = left + i * bar_spacing + (bar_spacing - bar_width) / 2
            bar_height = (count / max_count) * height if max_count > 0 else 0
            y = top + height - bar_height
            
            # Choose color based on performance
            if count == 0:
                color = QtGui.QColor(self.COLORS["bar_zero"])
            elif met_cap:
                color = QtGui.QColor(self.COLORS["bar_full"])
            elif count >= self._daily_cap * 0.75:
                color = QtGui.QColor(self.COLORS["bar_high"])
            elif count >= self._daily_cap * 0.5:
                color = QtGui.QColor(self.COLORS["bar_mid"])
            else:
                color = QtGui.QColor(self.COLORS["bar_low"])
            
            # Draw gradient bar
            gradient = QtGui.QLinearGradient(x, y, x, y + bar_height)
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color.darker(110))
            
            painter.setBrush(QtGui.QBrush(gradient))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            
            rect = QtCore.QRectF(x, y, bar_width, bar_height)
            painter.drawRoundedRect(rect, 2, 2)
            
            # Highlight hovered bar
            if date_str == self._hover_bar_date:
                painter.setBrush(QtGui.QColor(255, 255, 255, 40))
                painter.drawRoundedRect(rect, 2, 2)
            
            # Star indicator for cap met
            if met_cap and bar_height > 15:
                painter.setPen(QtGui.QColor(self.COLORS["streak_glow"]))
                font = painter.font()
                font.setPointSize(8)
                painter.setFont(font)
                painter.drawText(int(x), int(y - 2), int(bar_width), 15,
                                QtCore.Qt.AlignmentFlag.AlignCenter, "â­")
    
    def _draw_weekly_bars(self, painter: QtGui.QPainter, left: int, top: int,
                          width: int, height: int) -> None:
        """Draw weekly aggregated bars."""
        if not self._cached_weekly_bins:
            return
        
        num_weeks = len(self._cached_weekly_bins)
        if num_weeks == 0:
            return
        
        bar_spacing = width / max(num_weeks, 1)
        bar_width = max(8, bar_spacing * self.BAR_WIDTH)
        
        # Find max for scaling (total routines per week)
        max_total = max(w["total_count"] for w in self._cached_weekly_bins)
        max_total = max(max_total, self._daily_cap * 7, 1)
        
        for i, week in enumerate(self._cached_weekly_bins):
            total_count = week["total_count"]
            days_active = week["days_active"]
            
            # Calculate bar geometry
            x = left + i * bar_spacing + (bar_spacing - bar_width) / 2
            bar_height = (total_count / max_total) * height if max_total > 0 else 0
            y = top + height - bar_height
            
            # Color based on activity level
            if days_active >= 7:
                color = QtGui.QColor(self.COLORS["bar_full"])
            elif days_active >= 5:
                color = QtGui.QColor(self.COLORS["bar_high"])
            elif days_active >= 3:
                color = QtGui.QColor(self.COLORS["bar_mid"])
            else:
                color = QtGui.QColor(self.COLORS["bar_low"])
            
            # Gradient bar
            gradient = QtGui.QLinearGradient(x, y, x, y + bar_height)
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color.darker(110))
            
            painter.setBrush(QtGui.QBrush(gradient))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            
            rect = QtCore.QRectF(x, y, bar_width, bar_height)
            painter.drawRoundedRect(rect, 3, 3)
            
            # Activity indicator
            if days_active == 7:
                painter.setPen(QtGui.QColor(self.COLORS["streak_glow"]))
                font = painter.font()
                font.setPointSize(9)
                painter.setFont(font)
                painter.drawText(int(x), int(y - 2), int(bar_width), 15,
                                QtCore.Qt.AlignmentFlag.AlignCenter, "đźŹ†")
    
    def _draw_cap_line(self, painter: QtGui.QPainter, left: int, top: int,
                       width: int, height: int) -> None:
        """Draw daily cap reference line."""
        max_count = max((e.get("count", 0) for e in self._routine_history), default=0)
        max_count = max(max_count, self._daily_cap, 1)
        
        cap_y = top + height - (self._daily_cap / max_count) * height
        
        # Dashed line
        pen = QtGui.QPen(QtGui.QColor(self.COLORS["cap_line"]), 2, QtCore.Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(int(left), int(cap_y), int(left + width), int(cap_y))
        
        # Label
        painter.setPen(QtGui.QColor(self.COLORS["cap_line"]))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(int(left + width - 60), int(cap_y - 5), f"Cap: {self._daily_cap}")
    
    def _draw_moving_average(self, painter: QtGui.QPainter, left: int, top: int,
                             width: int, height: int) -> None:
        """Draw moving average trend line."""
        if not self._cached_moving_avg or len(self._cached_moving_avg) < 2:
            return
        
        num_days = len(self._routine_history)
        bar_spacing = width / max(num_days, 1)
        
        max_count = max((e.get("count", 0) for e in self._routine_history), default=0)
        max_count = max(max_count, self._daily_cap, 1)
        
        # Build path
        path = QtGui.QPainterPath()
        first = True
        
        # Map MA dates to indices
        date_to_idx = {e["date"]: i for i, e in enumerate(self._routine_history)}
        
        for date_str, avg in self._cached_moving_avg:
            idx = date_to_idx.get(date_str)
            if idx is None:
                continue
            
            x = left + idx * bar_spacing + bar_spacing / 2
            y = top + height - (avg / max_count) * height
            
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)
        
        # Draw line
        pen = QtGui.QPen(QtGui.QColor(self.COLORS["line_ma"]), self.LINE_WIDTH)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
    
    def _draw_axes(self, painter: QtGui.QPainter, left: int, top: int,
                   width: int, height: int, use_weekly: bool) -> None:
        """Draw axis labels."""
        painter.setPen(QtGui.QColor(self.COLORS["text"]))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        
        # Y-axis labels
        max_count = max((e.get("count", 0) for e in self._routine_history), default=0)
        max_count = max(max_count, self._daily_cap, 1)
        
        for i in range(self.GRID_LINES + 1):
            value = max_count * (self.GRID_LINES - i) / self.GRID_LINES
            y = top + (height * i / self.GRID_LINES)
            painter.drawText(0, int(y - 8), left - 5, 20,
                            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter,
                            f"{value:.0f}")
        
        # X-axis labels
        if use_weekly and self._cached_weekly_bins:
            num_weeks = len(self._cached_weekly_bins)
            bar_spacing = width / max(num_weeks, 1)
            
            for i, week in enumerate(self._cached_weekly_bins):
                if i % max(1, num_weeks // 6) == 0:  # Show ~6 labels
                    x = left + i * bar_spacing + bar_spacing / 2
                    dt = self._parse_date(week["week_start"])
                    if dt:
                        label = dt.strftime("%m/%d")
                        painter.drawText(int(x - 25), int(top + height + 5), 50, 20,
                                        QtCore.Qt.AlignmentFlag.AlignCenter, label)
        elif self._routine_history:
            num_days = len(self._routine_history)
            bar_spacing = width / max(num_days, 1)
            
            for i, entry in enumerate(self._routine_history):
                if i % max(1, num_days // 7) == 0:  # Show ~7 labels
                    x = left + i * bar_spacing + bar_spacing / 2
                    dt = self._parse_date(entry["date"])
                    if dt:
                        label = dt.strftime("%m/%d")
                        painter.drawText(int(x - 25), int(top + height + 5), 50, 20,
                                        QtCore.Qt.AlignmentFlag.AlignCenter, label)
    
    def _draw_title(self, painter: QtGui.QPainter, rect: QtCore.QRect) -> None:
        """Draw chart title with trend indicator."""
        painter.setPen(QtGui.QColor(self.COLORS["text_light"]))
        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        
        title = "đź‘ď¸Ź Eye Protection Progress"
        
        # Add trend indicator
        if self._cached_trend:
            direction, slope, r_sq = self._cached_trend
            if direction == "improving":
                title += " đź“"
            elif direction == "declining":
                title += " đź“‰"
        
        painter.drawText(self.MARGIN_LEFT, 5, rect.width() - self.MARGIN_LEFT - self.MARGIN_RIGHT, 
                        25, QtCore.Qt.AlignmentFlag.AlignLeft, title)
    
    def _draw_legend(self, painter: QtGui.QPainter, rect: QtCore.QRect, 
                     use_weekly: bool) -> None:
        """Draw chart legend."""
        font = painter.font()
        font.setPointSize(8)
        font.setBold(False)
        painter.setFont(font)
        
        legend_y = rect.height() - 15
        legend_x = self.MARGIN_LEFT
        
        legend_items = [
            (self.COLORS["bar_full"], "Cap Met"),
            (self.COLORS["line_ma"], "7-Day Avg"),
            (self.COLORS["cap_line"], "Daily Cap"),
        ]
        
        for color, label in legend_items:
            # Color swatch
            painter.setBrush(QtGui.QColor(color))
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.drawRect(legend_x, legend_y - 8, 10, 10)
            
            # Label
            painter.setPen(QtGui.QColor(self.COLORS["text"]))
            painter.drawText(legend_x + 14, legend_y + 2, label)
            
            legend_x += 80
    
    def _draw_streak_indicator(self, painter: QtGui.QPainter, rect: QtCore.QRect) -> None:
        """Draw current streak indicator."""
        streak = self._get_current_streak()
        if streak < 2:
            return
        
        # Position in top right
        painter.setPen(QtGui.QColor(self.COLORS["streak_glow"]))
        font = painter.font()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        
        streak_text = f"đź”Ą {streak} day streak!"
        text_rect = QtCore.QRect(rect.width() - 120, 5, 110, 25)
        
        # Glow background
        painter.setBrush(QtGui.QColor(255, 215, 0, 30))
        painter.drawRoundedRect(text_rect, 5, 5)
        
        painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignCenter, streak_text)
    
    def _draw_tooltip(self, painter: QtGui.QPainter) -> None:
        """Draw tooltip for hovered bar."""
        if not self._hover_bar_date or not self._cached_daily_totals:
            return
        
        data = self._cached_daily_totals.get(self._hover_bar_date)
        if not data:
            return
        
        count = data.get("count", 0)
        items_won = data.get("items_won", 0)
        met_cap = data.get("met_cap", False)
        
        # Format date
        dt = self._parse_date(self._hover_bar_date)
        if dt:
            date_label = dt.strftime("%A, %B %d")
        else:
            date_label = self._hover_bar_date
        
        # Build tooltip text
        lines = [
            date_label,
            f"Routines: {count} / {self._daily_cap}",
        ]
        if items_won > 0:
            lines.append(f"Items Won: {items_won}")
        if met_cap:
            lines.append("â­ Daily Cap Met!")
        
        tooltip_text = "\n".join(lines)
        
        # Calculate tooltip position
        num_days = len(self._routine_history)
        idx = next((i for i, e in enumerate(self._routine_history) 
                   if e["date"] == self._hover_bar_date), -1)
        if idx < 0:
            return
        
        rect = self.rect()
        chart_left = self.MARGIN_LEFT
        chart_width = rect.width() - self.MARGIN_LEFT - self.MARGIN_RIGHT
        bar_spacing = chart_width / max(num_days, 1)
        
        tooltip_x = int(chart_left + idx * bar_spacing + self._pan_offset_x)
        tooltip_y = int(self.MARGIN_TOP + 20)
        
        # Draw tooltip background
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        
        fm = QtGui.QFontMetrics(font)
        text_width = max(fm.horizontalAdvance(line) for line in lines) + 16
        text_height = fm.height() * len(lines) + 12
        
        # Keep tooltip on screen
        if tooltip_x + text_width > rect.width() - 10:
            tooltip_x = rect.width() - text_width - 10
        if tooltip_x < 10:
            tooltip_x = 10
        
        tooltip_rect = QtCore.QRect(tooltip_x, tooltip_y, text_width, text_height)
        
        # Background
        painter.setBrush(QtGui.QColor(30, 30, 40, 230))
        painter.setPen(QtGui.QPen(QtGui.QColor(self.COLORS["border"]), 1))
        painter.drawRoundedRect(tooltip_rect, 5, 5)
        
        # Text
        painter.setPen(QtGui.QColor(255, 255, 255))
        painter.drawText(tooltip_rect.adjusted(8, 6, -8, -6), 
                        QtCore.Qt.AlignmentFlag.AlignLeft, tooltip_text)
    
    # =========================================================================
    # Mouse interaction
    # =========================================================================
    
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle mouse press for panning."""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._is_panning = True
            self._last_mouse_pos = event.pos()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle mouse release."""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._is_panning = False
            self._last_mouse_pos = None
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle mouse move for panning and hover detection."""
        if self._is_panning and self._last_mouse_pos:
            delta = event.pos().x() - self._last_mouse_pos.x()
            self._pan_offset_x += delta
            self._last_mouse_pos = event.pos()
            self.update()
        else:
            # Hover detection
            self._update_hover(event.pos())
        super().mouseMoveEvent(event)
    
    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom_level = min(5.0, self._zoom_level * 1.1)
        else:
            self._zoom_level = max(0.5, self._zoom_level / 1.1)
        self.update()
        event.accept()
    
    def leaveEvent(self, event: QtCore.QEvent) -> None:
        """Handle mouse leave."""
        self._hover_bar_date = None
        self._is_panning = False
        self.update()
        super().leaveEvent(event)
    
    def _update_hover(self, pos: QtCore.QPoint) -> None:
        """Update hover state based on mouse position."""
        if not self._routine_history:
            return
        
        rect = self.rect()
        chart_left = self.MARGIN_LEFT
        chart_right = rect.width() - self.MARGIN_RIGHT
        chart_top = self.MARGIN_TOP
        chart_bottom = rect.height() - self.MARGIN_BOTTOM
        
        # Check if in chart area
        if not (chart_left <= pos.x() <= chart_right and 
                chart_top <= pos.y() <= chart_bottom):
            if self._hover_bar_date:
                self._hover_bar_date = None
                self.update()
            return
        
        # Find which bar
        num_days = len(self._routine_history)
        chart_width = chart_right - chart_left
        bar_spacing = chart_width / max(num_days, 1)
        
        # Adjust for pan
        adjusted_x = (pos.x() - chart_left - self._pan_offset_x) / self._zoom_level
        bar_idx = int(adjusted_x / bar_spacing)
        
        if 0 <= bar_idx < num_days:
            new_hover = self._routine_history[bar_idx]["date"]
            if new_hover != self._hover_bar_date:
                self._hover_bar_date = new_hover
                self.update()
        elif self._hover_bar_date:
            self._hover_bar_date = None
            self.update()
    
    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle double-click to reset view."""
        self.reset_view()
        super().mouseDoubleClickEvent(event)


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
    
    def showEvent(self, event):
        """Refresh entity-related features when tab becomes visible.
        
        This ensures that if entities are collected in Entitidex while viewing
        another tab, the Owl Tips and entity perk displays will update when returning here.
        """
        super().showEvent(event)
        # Refresh entity perk display and owl tips
        # These are fast operations that check collection status
        if hasattr(self, '_update_entity_perk_display'):
            self._update_entity_perk_display()
        if hasattr(self, '_refresh_owl_tips'):
            self._refresh_owl_tips()
    
    def hideEvent(self, event):
        """Handle tab switch away - cancel routine if running to prevent freezes."""
        super().hideEvent(event)
        if self.is_running:
            self._cancel_routine_silently()
    
    def _cancel_routine_silently(self):
        """Cancel the running routine without showing dialogs (used on tab switch)."""
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        self.is_running = False
        self.step_phase = "idle"
        self.blink_count = 0
        self.blink_state = "open"
        self.gaze_seconds_left = 20
        # Reset UI when visible again
        if hasattr(self, 'main_action_btn'):
            self._update_cooldown_display()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        add_tab_help_button(layout, "eye", self)
        
        # Header row: Title + Guidance Settings (compact)
        header_row = QtWidgets.QHBoxLayout()
        header_row.setSpacing(10)
        
        title = QtWidgets.QLabel("đź‘ď¸Ź Eyes")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #81c784;
            background: transparent;
            padding: 5px 0px;
        """)
        header_row.addWidget(title)
        header_row.addStretch(1)
        
        # Hidden cooldown status label (kept for compatibility but not shown in header)
        self.cooldown_status_label = QtWidgets.QLabel("")
        self.cooldown_status_label.hide()  # No longer shown separately
        
        # Guidance Settings (New)
        guidance_label = QtWidgets.QLabel("Speaker:")
        guidance_label.setStyleSheet("color: #b0bec5; font-weight: bold; margin-left: 10px;")
        
        self.guidance_combo = NoScrollComboBox()
        # Only show Voice mode if Piper is actually working
        if PIPER_WORKING:
            self.guidance_combo.addItems([
                EyeGuidanceSettings.MODE_SILENT, 
                EyeGuidanceSettings.MODE_SOUND, 
                EyeGuidanceSettings.MODE_VOICE
            ])
        else:
            # Piper not available - only Silent and Sound modes
            self.guidance_combo.addItems([
                EyeGuidanceSettings.MODE_SILENT, 
                EyeGuidanceSettings.MODE_SOUND
            ])
        # If saved mode was Voice but Piper isn't available, fall back to Sound
        saved_mode = self.guidance.mode
        if saved_mode == EyeGuidanceSettings.MODE_VOICE and not PIPER_WORKING:
            saved_mode = EyeGuidanceSettings.MODE_SOUND
            self.guidance.set_mode(saved_mode)
        self.guidance_combo.setCurrentText(saved_mode)
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
        
        # Block signals during initialization to prevent spurious set_voice calls
        self.voice_combo.blockSignals(True)
        self.voice_combo.addItems(self.guidance.get_voice_names())
        
        # Set current selection
        current_voice = EyeGuidanceSettings.get_voice_name()
        if current_voice and current_voice in self.guidance.AVAILABLE_VOICES:
            self.voice_combo.setCurrentText(current_voice)
        self.voice_combo.blockSignals(False)
            
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
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(102, 187, 106, 0.3);
                border-radius: 8px;
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
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(92, 107, 192, 0.3);
                border-radius: 8px;
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
                background: transparent;
                border: none;
            }
        """)
        owl_tips_layout.addWidget(self.owl_icon_label)
        
        # Middle: Title + Tip text (expandable)
        owl_content_col = QtWidgets.QVBoxLayout()
        owl_content_col.setSpacing(2)
        
        # Title row with entity name and tip number
        owl_title_row = QtWidgets.QHBoxLayout()
        self.owl_section_title = QtWidgets.QLabel("đź¦‰ Study Owl Eye Care Tips")
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
        self.owl_acknowledge_btn = QtWidgets.QPushButton("đź“– +1đźŞ™")
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
            "<span style='color:#81c784;'>đź“‹ Step A:</span> Lowâ†’CLOSE, Highâ†’HOLD, Silenceâ†’OPEN (5x) | "
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

        # Unified Action Row: Status on left, Main clickable center, empty right
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
        
        # Status label (left side - shows step info during routine)
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #90caf9;
            background: #1a2a4a;
            border: 1px solid #2196f3;
            border-radius: 6px;
            padding: 8px 12px;
        """)
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumWidth(180)
        self.status_label.setMaximumWidth(200)
        action_layout.addWidget(self.status_label)
        
        # Main Action Area (center) - clickable button that shows different states
        # States: START (ready), instructions (running), Wait X min (cooldown)
        self.main_action_btn = QtWidgets.QPushButton("đź‘ď¸Ź START (1 min)")
        self.main_action_btn.setMinimumHeight(60)
        self.main_action_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._set_main_action_ready_style()
        self.main_action_btn.clicked.connect(self._on_main_action_click)
        action_layout.addWidget(self.main_action_btn, 1)
        
        # Visual Cue label (hidden, used during routine for breathing cues)
        self.cue_label = QtWidgets.QLabel("")
        self.cue_label.hide()  # Now integrated into main_action_btn
        
        # Hidden start button for compatibility (actual logic moved to main_action_btn)
        self.start_btn = QtWidgets.QPushButton()
        self.start_btn.hide()
        
        layout.addWidget(action_row)

        # Reminder Settings Section with gradient card
        reminder_frame = QtWidgets.QGroupBox("đź”” Reminders")
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
        
        self.reminder_checkbox = QtWidgets.QCheckBox("đź”” Remind me every")
        self.reminder_checkbox.setChecked(getattr(self.blocker, 'eye_reminder_enabled', False))
        self.reminder_checkbox.stateChanged.connect(self._update_reminder_setting)
        reminder_layout.addWidget(self.reminder_checkbox)
        
        self.reminder_interval = NoScrollSpinBox()
        self.reminder_interval.setRange(15, 180)
        self.reminder_interval.setValue(getattr(self.blocker, 'eye_reminder_interval', 60))
        self.reminder_interval.setSuffix(" min")
        self.reminder_interval.valueChanged.connect(self._update_reminder_setting)
        reminder_layout.addWidget(self.reminder_interval)
        
        reminder_layout.addWidget(QtWidgets.QLabel("via:"))
        self.reminder_type_combo = NoScrollComboBox()
        self.reminder_type_combo.addItems(["Toast", "Voice", "Sound", "Sound + Voice"])
        # Load saved notification type
        saved_type = getattr(self.blocker, 'eye_reminder_notification_type', 'Toast')
        idx = self.reminder_type_combo.findText(saved_type)
        if idx >= 0:
            self.reminder_type_combo.setCurrentIndex(idx)
        self.reminder_type_combo.currentTextChanged.connect(self._update_reminder_setting)
        self.reminder_type_combo.setMinimumWidth(110)
        reminder_layout.addWidget(self.reminder_type_combo)
        
        reminder_layout.addStretch()
        layout.addWidget(reminder_frame)

        # Reward Info Box with modern gradient card
        info_frame = QtWidgets.QGroupBox("đźŽ Today's Progress & Rewards")
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
        
        # Progress Chart - Eye Protection history visualization
        chart_label = QtWidgets.QLabel("đź“Š Eye Protection Progress:")
        chart_label.setStyleSheet("font-weight: bold; margin-top: 8px; color: #81c784;")
        info_layout.addWidget(chart_label)
        
        self.eye_chart = EyeProtectionChartWidget()
        self.eye_chart.setMinimumHeight(280)
        info_layout.addWidget(self.eye_chart)
        
        # Initial chart data load
        self._refresh_chart()
        
        layout.addWidget(info_frame)
        
        layout.addStretch()
        
        # Start cooldown update timer (refresh every minute like hydration)
        self.cooldown_timer = QtCore.QTimer(self)
        self.cooldown_timer.timeout.connect(self._update_cooldown_display)
        self.cooldown_timer.start(60000)  # Update every minute
        
        # Initial update
        self._update_cooldown_display()

    def _refresh_display(self):
        """Refresh logic called when switching users."""
        # Update reminder settings from new blocker
        if hasattr(self, 'reminder_checkbox'):
            self.reminder_checkbox.setChecked(getattr(self.blocker, 'eye_reminder_enabled', False))
        
        if hasattr(self, 'reminder_interval'):
            self.reminder_interval.setValue(getattr(self.blocker, 'eye_reminder_interval', 60))
        
        # Restore notification type preference
        if hasattr(self, 'reminder_type_combo'):
            saved_type = getattr(self.blocker, 'eye_reminder_notification_type', 'Toast')
            idx = self.reminder_type_combo.findText(saved_type)
            if idx >= 0:
                self.reminder_type_combo.setCurrentIndex(idx)
            
        # Refresh all dynamic sections
        self.update_stats_display()
        self._update_cooldown_display()
        self._refresh_owl_tips()
        self._update_entity_perk_display()
        self._refresh_chart()

    def _refresh_chart(self) -> None:
        """Refresh the eye protection progress chart with current history data."""
        if not hasattr(self, 'eye_chart'):
            return
        
        try:
            # Get history from stats
            stats = self.blocker.stats.get("eye_protection", {})
            history = stats.get("history", [])
            
            # Get daily cap
            daily_cap = self.get_daily_cap()
            
            # Update chart with data
            self.eye_chart.set_data(history, daily_cap)
        except Exception as e:
            print(f"[EyeProtectionTab] Error refreshing chart: {e}")

    def _update_voice_combo_visibility(self, mode):
        """Show voice combo box only when Voice mode is selected."""
        if mode == EyeGuidanceSettings.MODE_VOICE:
            self.voice_combo.show()
        else:
            self.voice_combo.hide()
    
    def _set_main_action_ready_style(self):
        """Style the main action button for ready/start state."""
        self.main_action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66bb6a, stop:1 #43a047);
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 8px;
                border: 2px solid #4caf50;
                padding: 15px;
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
        """)
    
    def _set_main_action_cooldown_style(self):
        """Style the main action button for cooldown/waiting state."""
        self.main_action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5d4037, stop:1 #3e2723);
                color: #ff9800;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
                border: 2px solid #ff9800;
                padding: 15px;
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5d4037, stop:1 #3e2723);
                color: #ff9800;
                border: 2px solid #ff9800;
            }
        """)
    
    def _set_main_action_limit_style(self):
        """Style the main action button for daily limit reached state."""
        self.main_action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2e7d32, stop:1 #1b5e20);
                color: #a5d6a7;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
                border: 2px solid #4caf50;
                padding: 15px;
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2e7d32, stop:1 #1b5e20);
                color: #a5d6a7;
                border: 2px solid #4caf50;
            }
        """)
    
    def _set_main_action_running_style(self):
        """Style the main action button for running/active routine state."""
        self.main_action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3c72, stop:1 #2a5298);
                color: #64b5f6;
                font-size: 24px;
                font-weight: bold;
                border-radius: 8px;
                border: 2px solid #2196f3;
                padding: 15px;
            }
            QPushButton:disabled {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3c72, stop:1 #2a5298);
                color: #64b5f6;
                border: 2px solid #2196f3;
            }
        """)
    
    def _on_main_action_click(self):
        """Handle click on main action button - delegates to start_routine."""
        self.start_routine()
    
    def _update_reminder_setting(self):
        """Save reminder settings when changed."""
        from datetime import datetime
        
        was_enabled = getattr(self.blocker, 'eye_reminder_enabled', False)
        now_enabled = self.reminder_checkbox.isChecked()
        
        self.blocker.eye_reminder_enabled = now_enabled
        self.blocker.eye_reminder_interval = self.reminder_interval.value()
        
        # Save notification type preference
        if hasattr(self, 'reminder_type_combo'):
            self.blocker.eye_reminder_notification_type = self.reminder_type_combo.currentText()
        
        # If user just enabled reminders, set the last reminder time to now
        # so the first reminder fires after the full interval (not immediately)
        if now_enabled and not was_enabled:
            self.blocker.eye_last_reminder_time = datetime.now().isoformat()
        
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
                    f"<b>đźŚµ {entity_name}</b><br>"
                    f"<span style='color:#ffa726;'>{reroll_chance}% Reroll on Fail</span>"
                )
            else:
                # Sam: +1 Eye Tier only
                perk_text = (
                    f"<b>đźŚµ {entity_name}</b><br>"
                    f"<span style='color:#81c784;'>+{tier_bonus} Eye Tier</span>"
                )
            self.entity_perk_label.setText(perk_text)
            
            # Load and display SVG (static, not animated)
            self._load_entity_svg(is_exceptional)
            
            # Update border color for exceptional
            if is_exceptional:
                self.entity_perk_card.setStyleSheet("""
                    QFrame {
                        background-color: rgba(255, 255, 255, 0.04);
                        border: 1px solid rgba(186, 104, 200, 0.3);
                        border-radius: 8px;
                    }
                """)
            else:
                self.entity_perk_card.setStyleSheet("""
                    QFrame {
                        background-color: rgba(255, 255, 255, 0.04);
                        border: 1px solid rgba(102, 187, 106, 0.3);
                        border-radius: 8px;
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
                    self.entity_svg_label.setText("đźŚµ")
            else:
                self.entity_svg_label.setText("đźŚµ")
        except Exception as e:
            print(f"[Eye Tab] Error loading SVG: {e}")
            self.entity_svg_label.setText("đźŚµ")

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
            self.owl_section_title.setText("â­ Study Owl (Exceptional) Advanced Eye Tips")
            self.owl_section_title.setStyleSheet("color: #ffd700; padding: 4px;")
            self.owl_entity_name.setText("â­ Study Owl Athena")
            self.owl_entity_name.setStyleSheet("color: #ffd700; font-weight: bold; font-size: 12px;")
        else:
            self.owl_section_title.setText("đź¦‰ Study Owl Eye Care Tips")
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
                                    background: transparent;
                                    border: none;
                                }
                            """)
                        else:
                            self.owl_icon_label.setStyleSheet("""
                                QLabel {
                                    background: transparent;
                                    border: none;
                                }
                            """)
        except Exception:
            # Fallback - just show text
            self.owl_icon_label.setText("đź¦‰")
        
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
            self.owl_acknowledge_btn.setText("âś“ Done")
            self.owl_acknowledge_btn.setEnabled(False)
        else:
            # Can acknowledge
            self.owl_acknowledge_btn.setText("đź“– +1đźŞ™")
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
            self.owl_acknowledge_btn.setText("âś“ Done")
            self.owl_acknowledge_btn.setEnabled(False)
            
        except Exception as e:
            print(f"[Eye Tab] Error acknowledging owl tip: {e}")

    def _update_cooldown_display(self):
        """Update main action button to reflect current cooldown state."""
        stats = self.blocker.stats.get("eye_protection", {})
        last_date_str = stats.get("last_date", "")
        count = self.get_daily_count()
        daily_cap = self.get_daily_cap()
        
        # Check daily limit (can be increased by entity perks)
        if count >= daily_cap:
            self._set_main_action_limit_style()
            self.main_action_btn.setText(f"đźŽŻ Daily limit reached! ({daily_cap}/{daily_cap})")
            self.main_action_btn.setEnabled(False)
            self.status_label.setText(f"Done for today!")
            return
        
        # Check 20-minute cooldown
        if last_date_str:
            try:
                last_dt = datetime.fromisoformat(last_date_str)
                elapsed = datetime.now() - last_dt
                
                if elapsed < timedelta(minutes=20):
                    remaining = math.ceil(20 - elapsed.total_seconds() / 60)
                    next_time = (last_dt + timedelta(minutes=20)).strftime("%H:%M")
                    self._set_main_action_cooldown_style()
                    self.main_action_btn.setText(f"âŹł Wait {remaining} min (next at {next_time})")
                    self.main_action_btn.setEnabled(False)
                    self.status_label.setText(f"{count}/{daily_cap} today")
                    return
            except (ValueError, TypeError):
                pass  # Corrupted date, allow routine
        
        # Ready to start
        self._set_main_action_ready_style()
        self.main_action_btn.setText("đź‘ď¸Ź START (1 min)")
        self.main_action_btn.setEnabled(True)
        self.status_label.setText(f"{count}/{daily_cap} today")
    
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
                f"<span style='color:#4caf50;'>đźŽŻ Daily limit reached!</span><br>"
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
                f"<span style='color:#66bb6a;'>â†’</span> "
                f"<span style='color:{effective_color};'><b>{effective_tier_name}</b></span> "
                f"<span style='color:#a5d6a7;'>(+{tier_bonus} đźŚµ)</span>"
            )
        else:
            tier_display = f"<span style='color:{base_color};'>{window_start}-{window_end} ({base_tier}-centered)</span>"
        
        text = (
            f"<b>Today's Routines: {count} / {daily_cap}</b><br><br>"
            f"Next Routine: {tier_display}<br>"
            f"đźŽ˛ Success Rate: <span style='color:#4caf50'>{success_rate}%</span><br>"
            f"đźŽ° Tier Distribution: [5%, 15%, <span style='color:{effective_color};'><b>60%</b></span>, 15%, 5%]"
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
        self.main_action_btn.setEnabled(False)
        self._set_main_action_running_style()
        self.step_phase = "blinking"
        self.blink_count = 0
        self.blink_state = "ready"
        
        # Sound
        self.guidance.play_start()
        
        # Start Step A logic
        self.status_label.setText("Step A: 5 Gentle Blinks")
        self.main_action_btn.setText("đź‘ď¸Ź Get Ready...")
        
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
        
        self.main_action_btn.setText("đź´ CLOSE eyes")
        # Reuse status area for progress, but users have eyes closed mostly
        # self.status_label.setText(f"Blink {self.blink_count}/5") 
        self.guidance.play_blink_close()
        
        # Schedule next sub-steps
        # Close duration ~1.5s -> Then Hold signal
        QtCore.QTimer.singleShot(1500, self.do_blink_hold)
        
    def do_blink_hold(self):
        # Guard: Don't run if routine stopped or tab switched away
        if not self.is_running or not self.isVisible():
            return
        self.blink_state = "hold"
        self.main_action_btn.setText("đź HOLD...")
        self.guidance.play_blink_hold()
        # Hold duration ~0.5s -> Then Open (Silence)
        QtCore.QTimer.singleShot(500, self.do_blink_open)
        
    def do_blink_open(self):
        # Guard: Don't run if routine stopped or tab switched away
        if not self.is_running or not self.isVisible():
            return
        self.blink_state = "open"
        self.main_action_btn.setText("đź‘€ OPEN eyes")
        self.guidance.play_blink_open() # Is silent
        # Open duration ~1.5s -> Next cycle
        QtCore.QTimer.singleShot(1500, self.start_blink_cycle)

    def start_gaze_phase(self):
        # Guard: Don't run if routine stopped or tab switched away
        if not self.is_running or not self.isVisible():
            return
        self.step_phase = "gazing"
        self.gaze_seconds_left = 20
        self.status_label.setText("Step B: Far Gaze + Breathing\n(Blink normally!)")
        self.main_action_btn.setText("đź‘ď¸Ź Look away (20ft/6m)")
        self.guidance.play_gaze_start()
        
        # Delay first tick to allow "Look far away" voice cue to complete
        # before the first "Inhale" cue plays (prevents audio overlap)
        QtCore.QTimer.singleShot(2000, self._start_breathing_timer)

    def _start_breathing_timer(self):
        """Start the breathing timer after initial gaze cue completes."""
        # Guard: Don't run if routine was stopped during the delay or tab switched
        if not self.is_running or self.step_phase != "gazing" or not self.isVisible():
            return
        self.timer.start(1000)  # One tick per second
        self.on_timer_tick()  # Execute first tick immediately

    def on_timer_tick(self):
        # Guard: Stop timer if routine was cancelled or tab switched
        if not self.is_running or not self.isVisible():
            self.timer.stop()
            return
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
                    self.main_action_btn.setText(f"đźŚ¬ď¸Ź INHALE... {t-16}")
                elif t > 10:  # Exhale 1
                    if t == 16:
                        self.guidance.play_exhale()
                    self.main_action_btn.setText(f"đź’¨ EXHALE... {t-10}")
                elif t > 6:  # Inhale 2
                    if t == 10:
                        self.guidance.play_inhale()
                    self.main_action_btn.setText(f"đźŚ¬ď¸Ź INHALE... {t-6}")
                elif t > 0:  # Exhale 2
                    if t == 6:
                        self.guidance.play_exhale()
                    self.main_action_btn.setText(f"đź’¨ EXHALE... {t}")
                
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
        self.main_action_btn.setEnabled(True)
        self.main_action_btn.setText("âś… COMPLETE!")
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
        
        # Prepare stats containers; persist only after lottery resolves.
        if "eye_protection" not in self.blocker.stats:
            self.blocker.stats["eye_protection"] = {}
        
        # Get today's date for history
        from app_utils import get_activity_date
        today_str = get_activity_date()
        
        # Initialize history array if needed
        if "history" not in self.blocker.stats["eye_protection"]:
            self.blocker.stats["eye_protection"]["history"] = []
        
        history = self.blocker.stats["eye_protection"]["history"]
        
        # Find or create today's entry
        today_entry = None
        for entry in history:
            if entry.get("date") == today_str:
                today_entry = entry
                break
        
        if today_entry is None:
            today_entry = {"date": today_str, "count": 0, "items_won": 0, "tiers": []}
            history.append(today_entry)
        
        # Import backend roller + merge lottery dialog for moving window animation
        from gamification import roll_eye_routine_reward_outcome
        from lottery_animation import MergeTwoStageLotteryDialog
        
        adhd_data = getattr(self.blocker, "adhd_buster", None)
        # Probe lock metadata once so stage-1 rendering reflects unlocked spans,
        # while the actual success/tier rolls are generated by the animation.
        lock_probe = roll_eye_routine_reward_outcome(
            success_threshold=success_rate,
            base_rarity=base_rarity,
            adhd_buster=adhd_data,
            success_roll=0.0,
            tier_roll=50.0,
        )
        # Show the animated two-stage lottery dialog with moving window
        lottery = MergeTwoStageLotteryDialog(
            success_roll=-1.0,
            success_threshold=success_rate,
            tier_upgrade_enabled=False,
            base_rarity=base_rarity,
            title="đź‘ď¸Źâ€Ťđź—¨ď¸Ź Eyes Routine Reward đź‘ď¸Źâ€Ťđź—¨ď¸Ź",
            parent=self,
            tier_weights=lock_probe["tier_weights"],
            power_gating=lock_probe.get("power_gating"),
        )
        lottery.exec()
        # Finalize against backend using the exact rolls that were animated.
        lottery_outcome = roll_eye_routine_reward_outcome(
            success_threshold=success_rate,
            base_rarity=base_rarity,
            adhd_buster=adhd_data,
            success_roll=getattr(lottery, "success_roll", None),
            tier_roll=getattr(lottery, "tier_roll", None),
        )
        won_item = bool(lottery_outcome.get("success", False))
        tier = lottery_outcome.get("rolled_tier", "")        
        # âś¨ REROLL MECHANIC: If failed and have reroll chance, try again (50% probability)
        if not won_item and reroll_chance > 0:
            # 50% chance to get the opportunity to reroll
            if random.randint(1, 100) <= reroll_chance:
                # Show reroll message
                styled_info(
                    self, 
                    f"{entity_name}'s Second Chance! đźŚµ",
                    f"{entity_name} grants you another roll!\n\n"
                    f"\"If I can survive fluorescent lights, you can survive this!\""
                )
                
                # Do the reroll with same parameters
                lottery2 = MergeTwoStageLotteryDialog(
                    success_roll=-1.0,
                    success_threshold=success_rate,
                    tier_upgrade_enabled=False,
                    base_rarity=base_rarity,
                    title="đźŚ€ Second Chance Roll đźŚ€",
                    parent=self,
                    tier_weights=lock_probe["tier_weights"],
                    power_gating=lock_probe.get("power_gating"),
                )
                lottery2.exec()
                reroll_outcome = roll_eye_routine_reward_outcome(
                    success_threshold=success_rate,
                    base_rarity=base_rarity,
                    adhd_buster=adhd_data,
                    success_roll=getattr(lottery2, "success_roll", None),
                    tier_roll=getattr(lottery2, "tier_roll", None),
                )
                won_item = bool(reroll_outcome.get("success", False))
                tier = reroll_outcome.get("rolled_tier", "")
        # Persist routine progress only after lottery is complete.
        today_entry["count"] = new_count
        if won_item and tier:
            today_entry["items_won"] = today_entry.get("items_won", 0) + 1
            if "tiers" not in today_entry:
                today_entry["tiers"] = []
            today_entry["tiers"].append(tier)

        self.blocker.stats["eye_protection"]["last_date"] = datetime.now().isoformat()
        self.blocker.stats["eye_protection"]["daily_count"] = new_count
        self.blocker.save_stats()

        # Notify timeline/state subscribers only after persistence is complete.
        try:
            from game_state import get_game_state
            game_state = get_game_state()
            if game_state:
                game_state.notify_eye_routine_changed(new_count)
        except Exception:
            pass

        # Refresh tab UI now that final outcome has been committed.
        self._update_cooldown_display()
        self.update_stats_display()
        
        # Refresh chart with new data
        self._refresh_chart()
        
        if won_item:
            # Generate Item
            adhd_data = getattr(self.blocker, 'adhd_buster', {})
            story_theme = adhd_data.get('active_story', 'warrior') if adhd_data else 'warrior'
            
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

