"""
Celebration Audio Manager.

Generates celebration sounds using system beeps with creative pitch patterns.
Each theme has a unique audio signature - no external sound files needed!

Uses winsound.Beep() for Windows, with graceful fallback on other platforms.
"""

import logging
import threading
import time
from typing import List, Tuple

_logger = logging.getLogger(__name__)

# Platform-safe sound support (same pattern as eye_protection_tab.py)
try:
    import winsound
except ImportError:
    winsound = None
    _logger.info("winsound not available - celebration sounds disabled on this platform")


def _play_async(sequence: List[Tuple[int, int]]) -> None:
    """
    Play a sequence of (frequency, duration_ms) tuples in a separate thread.
    
    Args:
        sequence: List of (freq_hz, duration_ms) tuples. freq=0 means silence.
    """
    if winsound is None:
        return
    
    # Capture winsound reference for use in thread
    _winsound = winsound
    
    def run():
        try:
            for freq, ms in sequence:
                if freq == 0:
                    time.sleep(ms / 1000.0)
                else:
                    freq = max(37, min(32767, freq))
                    _winsound.Beep(freq, ms)
        except Exception as e:
            _logger.debug(f"Sound playback error: {e}")
    
    threading.Thread(target=run, daemon=True).start()


def _warrior_fanfare() -> List[Tuple[int, int]]:
    return [
        (400, 150), (0, 50), (500, 150), (0, 50), (600, 200), (0, 100),
        (500, 100), (600, 100), (700, 100), (800, 300), (0, 100),
        (700, 80), (800, 80), (900, 80), (1000, 400),
    ]


def _scholar_chime() -> List[Tuple[int, int]]:
    return [
        (1200, 200), (0, 100), (1400, 200), (0, 100), (1600, 200), (0, 150),
        (1800, 100), (1600, 100), (1800, 100), (2000, 250), (0, 100),
        (1500, 150), (1700, 150), (2000, 150), (2200, 400),
    ]


def _wanderer_adventure() -> List[Tuple[int, int]]:
    return [
        (500, 200), (600, 200), (500, 200), (0, 100),
        (600, 150), (700, 150), (800, 150), (700, 150), (0, 100),
        (800, 100), (900, 100), (1000, 100), (1100, 100), (1200, 400),
    ]


def _underdog_triumph() -> List[Tuple[int, int]]:
    return [
        (300, 150), (350, 150), (300, 150), (0, 100),
        (400, 100), (500, 100), (600, 100), (700, 100), (0, 100),
        (800, 100), (900, 100), (1000, 100), (1100, 100),
        (1200, 150), (1300, 150), (1400, 400),
    ]


def _scientist_eureka() -> List[Tuple[int, int]]:
    return [
        (800, 80), (900, 80), (700, 80), (1000, 80), (600, 80), (1100, 80), (0, 100),
        (1000, 60), (1200, 60), (1000, 60), (1200, 60), (1400, 60), (0, 100),
        (1500, 150), (1700, 150), (1900, 150), (2100, 400),
    ]


def _default_celebration() -> List[Tuple[int, int]]:
    return [
        (800, 100), (1000, 100), (1200, 100), (0, 100),
        (1000, 100), (1200, 100), (1500, 300),
    ]


_THEME_PATTERNS = {
    "warrior": _warrior_fanfare,
    "scholar": _scholar_chime,
    "wanderer": _wanderer_adventure,
    "underdog": _underdog_triumph,
    "scientist": _scientist_eureka,
}


def play_celebration_sound(theme_id: str = "default") -> bool:
    if winsound is None:
        _logger.info("winsound not available - cannot play celebration")
        return False
    
    pattern_func = _THEME_PATTERNS.get(theme_id, _default_celebration)
    sequence = pattern_func()
    
    _logger.info(f"Playing {theme_id} celebration sound")
    _play_async(sequence)
    return True


def preload_celebration_sounds() -> None:
    if winsound:
        _logger.info("Celebration audio ready (using system beeps)")
    else:
        _logger.info("Celebration audio unavailable on this platform")


class CelebrationAudioManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def play(self, theme_id: str = "default") -> bool:
        return play_celebration_sound(theme_id)
    
    def stop(self) -> None:
        pass
    
    @classmethod
    def get_instance(cls) -> "CelebrationAudioManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
