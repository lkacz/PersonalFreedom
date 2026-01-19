"""
Lottery Result Sound Effects for Personal Liberty.

Provides short melodic feedback for lottery win/lose outcomes:
- Win sounds: Triumphant, ascending, celebratory (~300-500ms)
- Lose sounds: Gentle disappointment, descending, consoling (~300-400ms)

Uses the Qt-based synthesizer for consistent audio quality.
Designed to be satisfying but not annoying on repeated plays.
"""

import random
import logging
from typing import List, Callable

from PySide6.QtCore import QByteArray

# Import the celebration audio system
try:
    from entitidex.celebration_audio import (
        Synthesizer,
        CelebrationAudioManager,
    )
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


_logger = logging.getLogger(__name__)


# Note frequencies (Hz)
NOTES = {
    # Octave 3 (for lose sounds - lower, softer)
    'E3': 164.81, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    # Octave 4
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    # Octave 5 (for win sounds - brighter)
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
    'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    # Octave 6 (accent)
    'C6': 1046.50, 'E6': 1318.51, 'G6': 1567.98,
}

# Duration constants (milliseconds)
QUICK = 60
SHORT = 100
MEDIUM = 150
LONG = 200
RING = 250


# ============================================================================
# WIN MELODIES - Triumphant, ascending, celebratory
# ============================================================================

def _compose_win_1() -> QByteArray:
    """Victory fanfare - classic ascending triad."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.35, "sine", 8, 25))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], SHORT, 0.38, "sine", 8, 25))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], SHORT, 0.40, "sine", 8, 25))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], RING, 0.45, "sine", 10, 80))
    return Synthesizer.mix_sequences(seq)


def _compose_win_2() -> QByteArray:
    """Triumphant chord - layered harmony."""
    t1 = Synthesizer.generate_tone(NOTES['C5'], RING, 0.30, "sine", 15, 80)
    t2 = Synthesizer.generate_tone(NOTES['E5'], RING, 0.28, "sine", 20, 80)
    t3 = Synthesizer.generate_tone(NOTES['G5'], RING, 0.26, "sine", 25, 80)
    mixed = Synthesizer.mix_tracks(t1, t2)
    return Synthesizer.mix_tracks(mixed, t3)


def _compose_win_3() -> QByteArray:
    """Quick success - double ping rising."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G5'], QUICK, 0.35, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], QUICK, 0.38, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], LONG, 0.42, "sine", 8, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_win_4() -> QByteArray:
    """Sparkle win - high shimmer."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], QUICK, 0.32, "sine", 5, 20))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], QUICK, 0.35, "sine", 5, 20))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], SHORT, 0.38, "sine", 8, 30))
    seq.append(Synthesizer.generate_tone(NOTES['E6'], MEDIUM, 0.40, "sine", 10, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_win_5() -> QByteArray:
    """Power up - ascending scale."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], QUICK, 0.30, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['D5'], QUICK, 0.32, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], QUICK, 0.34, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], SHORT, 0.38, "sine", 8, 25))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], MEDIUM, 0.42, "sine", 10, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_win_6() -> QByteArray:
    """Coin collect - classic game sound."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], SHORT, 0.38, "sine", 5, 20))
    seq.append(Synthesizer.generate_tone(NOTES['B5'], LONG, 0.42, "sine", 8, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_win_7() -> QByteArray:
    """Achievement - bold announcement."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G4'], SHORT, 0.35, "rich", 8, 20))
    seq.append(Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.38, "rich", 8, 20))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], MEDIUM, 0.40, "rich", 10, 40))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], LONG, 0.42, "rich", 10, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_win_8() -> QByteArray:
    """Lucky strike - bright double."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.35, "sine", 8, 20))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], SHORT, 0.38, "sine", 8, 25))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], RING, 0.42, "sine", 10, 80))
    return Synthesizer.mix_sequences(seq)


def _compose_win_9() -> QByteArray:
    """Jackpot - celebratory cascade."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], QUICK, 0.32, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], QUICK, 0.35, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], QUICK, 0.38, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['E6'], SHORT, 0.40, "sine", 8, 30))
    seq.append(Synthesizer.generate_tone(NOTES['G6'], MEDIUM, 0.42, "sine", 10, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_win_10() -> QByteArray:
    """Treasure found - magical discovery."""
    # Layer shimmer with base
    base = Synthesizer.generate_tone(NOTES['C5'], RING, 0.35, "sine", 15, 80)
    shimmer = Synthesizer.generate_tone(NOTES['G5'], MEDIUM, 0.25, "sine", 20, 60)
    return Synthesizer.mix_tracks(base, shimmer)


def _compose_win_11() -> QByteArray:
    """Level up - heroic rise."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G4'], SHORT, 0.35, "rich", 8, 20))
    seq.append(Synthesizer.generate_tone(NOTES['D5'], SHORT, 0.38, "rich", 8, 20))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], RING, 0.42, "rich", 10, 80))
    return Synthesizer.mix_sequences(seq)


def _compose_win_12() -> QByteArray:
    """Victory dance - playful bounce."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], QUICK, 0.35, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], QUICK, 0.35, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], QUICK, 0.38, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], QUICK, 0.35, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], MEDIUM, 0.42, "sine", 10, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_win_13() -> QByteArray:
    """Prize bell - classic chime."""
    main = Synthesizer.generate_tone(NOTES['E5'], RING, 0.38, "sine", 12, 90)
    accent = Synthesizer.generate_tone(NOTES['C6'], SHORT, 0.25, "sine", 8, 40)
    return Synthesizer.mix_tracks(main, accent)


def _compose_win_14() -> QByteArray:
    """Champion - bold fanfare."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], MEDIUM, 0.38, "rich", 10, 30))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], MEDIUM, 0.40, "rich", 10, 30))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], RING, 0.42, "rich", 12, 80))
    return Synthesizer.mix_sequences(seq)


def _compose_win_15() -> QByteArray:
    """Star collect - bright ascending."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G5'], SHORT, 0.35, "sine", 6, 20))
    seq.append(Synthesizer.generate_tone(NOTES['A5'], SHORT, 0.38, "sine", 6, 20))
    seq.append(Synthesizer.generate_tone(NOTES['B5'], SHORT, 0.40, "sine", 6, 20))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], LONG, 0.42, "sine", 10, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_win_16() -> QByteArray:
    """Bonus round - exciting climb."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], QUICK, 0.32, "sine", 5, 12))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], QUICK, 0.35, "sine", 5, 12))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], QUICK, 0.38, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], QUICK, 0.40, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], MEDIUM, 0.42, "sine", 10, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_win_17() -> QByteArray:
    """Reward drop - satisfying pop."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.38, "sine", 8, 25))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], LONG, 0.42, "sine", 10, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_win_18() -> QByteArray:
    """Perfect score - triple accent."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], QUICK, 0.35, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], QUICK, 0.38, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], QUICK, 0.35, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], RING, 0.42, "sine", 10, 80))
    return Synthesizer.mix_sequences(seq)


def _compose_win_19() -> QByteArray:
    """Glory - majestic chord swell."""
    t1 = Synthesizer.generate_tone(NOTES['G4'], RING, 0.30, "rich", 20, 90)
    t2 = Synthesizer.generate_tone(NOTES['C5'], RING, 0.28, "rich", 25, 90)
    t3 = Synthesizer.generate_tone(NOTES['E5'], RING, 0.26, "rich", 30, 90)
    mixed = Synthesizer.mix_tracks(t1, t2)
    return Synthesizer.mix_tracks(mixed, t3)


def _compose_win_20() -> QByteArray:
    """Epic loot - legendary discovery."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G4'], SHORT, 0.35, "rich", 8, 20))
    seq.append(Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.38, "rich", 8, 20))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], SHORT, 0.40, "rich", 8, 25))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], SHORT, 0.42, "rich", 8, 25))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], RING, 0.45, "rich", 12, 90))
    return Synthesizer.mix_sequences(seq)


# ============================================================================
# LOSE MELODIES - Gentle disappointment, descending, consoling
# ============================================================================

def _compose_lose_1() -> QByteArray:
    """Gentle letdown - soft descending."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], MEDIUM, 0.28, "sine", 15, 40))
    seq.append(Synthesizer.generate_tone(NOTES['C5'], LONG, 0.25, "sine", 15, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_2() -> QByteArray:
    """Missed - falling interval."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G5'], SHORT, 0.28, "sine", 10, 30))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], SHORT, 0.26, "sine", 10, 30))
    seq.append(Synthesizer.generate_tone(NOTES['C5'], MEDIUM, 0.24, "sine", 12, 50))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_3() -> QByteArray:
    """Try again - encouraging minor."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E4'], MEDIUM, 0.28, "sine", 12, 40))
    seq.append(Synthesizer.generate_tone(NOTES['G4'], LONG, 0.25, "sine", 15, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_4() -> QByteArray:
    """Slipped away - fading descent."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G4'], SHORT, 0.28, "sine", 10, 30))
    seq.append(Synthesizer.generate_tone(NOTES['E4'], SHORT, 0.25, "sine", 12, 35))
    seq.append(Synthesizer.generate_tone(NOTES['C4'], MEDIUM, 0.22, "sine", 15, 50))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_5() -> QByteArray:
    """Almost - hopeful yet disappointed."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.28, "sine", 10, 25))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], SHORT, 0.28, "sine", 10, 25))
    seq.append(Synthesizer.generate_tone(NOTES['D5'], LONG, 0.25, "sine", 15, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_6() -> QByteArray:
    """Soft sigh - single descending."""
    return Synthesizer.generate_tone(NOTES['G4'], RING, 0.25, "sine", 20, 100)


def _compose_lose_7() -> QByteArray:
    """Next time - gentle double."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], SHORT, 0.26, "sine", 12, 30))
    seq.append(Synthesizer.generate_tone(NOTES['C5'], MEDIUM, 0.24, "sine", 15, 50))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_8() -> QByteArray:
    """Consolation - warm minor."""
    t1 = Synthesizer.generate_tone(NOTES['A4'], LONG, 0.25, "sine", 18, 70)
    t2 = Synthesizer.generate_tone(NOTES['C5'], MEDIUM, 0.20, "sine", 22, 60)
    return Synthesizer.mix_tracks(t1, t2)


def _compose_lose_9() -> QByteArray:
    """Gentle close - resolving descent."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['D5'], SHORT, 0.26, "sine", 10, 30))
    seq.append(Synthesizer.generate_tone(NOTES['C5'], MEDIUM, 0.24, "sine", 12, 45))
    seq.append(Synthesizer.generate_tone(NOTES['G4'], LONG, 0.22, "sine", 15, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_10() -> QByteArray:
    """Fade out - quiet ending."""
    return Synthesizer.generate_tone(NOTES['E4'], RING, 0.22, "sine", 25, 120)


def _compose_lose_11() -> QByteArray:
    """Womp womp - playful sad trombone (short)."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['B4'], MEDIUM, 0.28, "sine", 10, 30))
    seq.append(Synthesizer.generate_tone(NOTES['A4'], LONG, 0.25, "sine", 12, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_12() -> QByteArray:
    """Keep trying - supportive minor."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E4'], SHORT, 0.26, "sine", 10, 25))
    seq.append(Synthesizer.generate_tone(NOTES['G4'], SHORT, 0.26, "sine", 10, 25))
    seq.append(Synthesizer.generate_tone(NOTES['E4'], MEDIUM, 0.24, "sine", 12, 45))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_13() -> QByteArray:
    """Soft landing - cushioned fall."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G5'], QUICK, 0.26, "sine", 8, 20))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], QUICK, 0.25, "sine", 8, 20))
    seq.append(Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.24, "sine", 10, 30))
    seq.append(Synthesizer.generate_tone(NOTES['G4'], MEDIUM, 0.22, "sine", 12, 50))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_14() -> QByteArray:
    """Quiet close - gentle ending."""
    t1 = Synthesizer.generate_tone(NOTES['G4'], MEDIUM, 0.24, "sine", 15, 60)
    t2 = Synthesizer.generate_tone(NOTES['E4'], MEDIUM, 0.20, "sine", 18, 60)
    return Synthesizer.mix_tracks(t1, t2)


def _compose_lose_15() -> QByteArray:
    """Maybe later - hopeful minor."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.26, "sine", 10, 25))
    seq.append(Synthesizer.generate_tone(NOTES['A4'], MEDIUM, 0.24, "sine", 12, 45))
    seq.append(Synthesizer.generate_tone(NOTES['E4'], LONG, 0.22, "sine", 15, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_16() -> QByteArray:
    """Neutral end - neither happy nor sad."""
    return Synthesizer.generate_tone(NOTES['C5'], LONG, 0.24, "sine", 18, 80)


def _compose_lose_17() -> QByteArray:
    """Soft step down - gentle cascade."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], QUICK, 0.26, "sine", 8, 18))
    seq.append(Synthesizer.generate_tone(NOTES['D5'], QUICK, 0.25, "sine", 8, 18))
    seq.append(Synthesizer.generate_tone(NOTES['C5'], MEDIUM, 0.24, "sine", 10, 45))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_18() -> QByteArray:
    """Peaceful end - calming close."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G4'], MEDIUM, 0.25, "sine", 12, 40))
    seq.append(Synthesizer.generate_tone(NOTES['C4'], LONG, 0.22, "sine", 15, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_19() -> QByteArray:
    """Tomorrow - encouraging finish."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['A4'], SHORT, 0.26, "sine", 10, 25))
    seq.append(Synthesizer.generate_tone(NOTES['G4'], MEDIUM, 0.24, "sine", 12, 40))
    seq.append(Synthesizer.generate_tone(NOTES['A4'], LONG, 0.26, "sine", 15, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_lose_20() -> QByteArray:
    """Soft resolve - gentle acceptance."""
    t1 = Synthesizer.generate_tone(NOTES['C5'], LONG, 0.24, "sine", 20, 80)
    t2 = Synthesizer.generate_tone(NOTES['G4'], MEDIUM, 0.20, "sine", 25, 70)
    return Synthesizer.mix_tracks(t1, t2)


# ============================================================================
# Sound Lists
# ============================================================================

WIN_COMPOSERS: List[Callable[[], QByteArray]] = [
    _compose_win_1,
    _compose_win_2,
    _compose_win_3,
    _compose_win_4,
    _compose_win_5,
    _compose_win_6,
    _compose_win_7,
    _compose_win_8,
    _compose_win_9,
    _compose_win_10,
    _compose_win_11,
    _compose_win_12,
    _compose_win_13,
    _compose_win_14,
    _compose_win_15,
    _compose_win_16,
    _compose_win_17,
    _compose_win_18,
    _compose_win_19,
    _compose_win_20,
]

LOSE_COMPOSERS: List[Callable[[], QByteArray]] = [
    _compose_lose_1,
    _compose_lose_2,
    _compose_lose_3,
    _compose_lose_4,
    _compose_lose_5,
    _compose_lose_6,
    _compose_lose_7,
    _compose_lose_8,
    _compose_lose_9,
    _compose_lose_10,
    _compose_lose_11,
    _compose_lose_12,
    _compose_lose_13,
    _compose_lose_14,
    _compose_lose_15,
    _compose_lose_16,
    _compose_lose_17,
    _compose_lose_18,
    _compose_lose_19,
    _compose_lose_20,
]


# ============================================================================
# Public API
# ============================================================================

def play_win_sound() -> bool:
    """
    Play a random win/success melody.
    
    Triumphant, ascending sounds for lottery wins and item drops.
    Duration: ~300-500ms.
    
    Returns:
        True if sound was played successfully, False otherwise.
    """
    if not AUDIO_AVAILABLE:
        _logger.warning("Audio system not available for win sound")
        return False
    
    try:
        composer = random.choice(WIN_COMPOSERS)
        audio_data = composer()
        manager = CelebrationAudioManager.get_instance()
        return manager.play_buffer(audio_data)
    except Exception as e:
        _logger.error(f"Failed to play win sound: {e}")
        return False


def play_lose_sound() -> bool:
    """
    Play a random lose/miss melody.
    
    Gentle, descending sounds for lottery losses - consoling, not harsh.
    Duration: ~300-400ms.
    
    Returns:
        True if sound was played successfully, False otherwise.
    """
    if not AUDIO_AVAILABLE:
        _logger.warning("Audio system not available for lose sound")
        return False
    
    try:
        composer = random.choice(LOSE_COMPOSERS)
        audio_data = composer()
        manager = CelebrationAudioManager.get_instance()
        return manager.play_buffer(audio_data)
    except Exception as e:
        _logger.error(f"Failed to play lose sound: {e}")
        return False


def play_lottery_result(won: bool) -> bool:
    """
    Play appropriate sound based on lottery result.
    
    Args:
        won: True for win sound, False for lose sound.
        
    Returns:
        True if sound was played successfully, False otherwise.
    """
    if won:
        return play_win_sound()
    else:
        return play_lose_sound()


def is_sound_available() -> bool:
    """Check if sound playback is available on this system."""
    return AUDIO_AVAILABLE


def get_win_count() -> int:
    """Return the number of available win melodies."""
    return len(WIN_COMPOSERS)


def get_lose_count() -> int:
    """Return the number of available lose melodies."""
    return len(LOSE_COMPOSERS)
