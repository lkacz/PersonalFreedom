"""
Startup notification sounds for Personal Liberty.

Plays short notification chimes when the app starts minimized to system tray,
reminding users the app is running and ready to use.

Uses the same Qt-based synthesizer as celebration sounds for consistent quality.

Design principles (industry-standard notification sounds):
- Short duration: 200-400ms total (2-3 notes)
- Pleasant frequencies: 500-1200 Hz range (comfortable hearing)
- Harmonic intervals: perfect fifths, major thirds, octaves
- Soft envelopes: gentle attack/release to avoid clicks
- Moderate volume: 0.25-0.35 to avoid startling
- Bell-like quality: pure sine tones with quick decay
"""

import random
import logging
from typing import List, Optional, Callable

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


# Note frequencies (Hz) - focused on pleasant notification range
NOTES = {
    # Octave 4 (foundation)
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    # Octave 5 (primary notification range - most pleasant)
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
    'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
    # Octave 6 (accent notes)
    'C6': 1046.50, 'D6': 1174.66, 'E6': 1318.51,
}

# Duration constants (milliseconds) - shorter for notifications
PING = 60       # Quick accent
SHORT = 100     # Standard note  
MEDIUM = 150    # Sustained note
RING = 200      # Final resonance


def _compose_chime_1() -> QByteArray:
    """Classic two-tone ascending - Windows-style notification."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], SHORT, 0.30, "sine", 8, 40))
    seq.append(Synthesizer.generate_tone(NOTES['A5'], RING, 0.28, "sine", 8, 80))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_2() -> QByteArray:
    """Gentle bell - single tone with harmonic."""
    # Layer two tones for bell-like quality
    main = Synthesizer.generate_tone(NOTES['G5'], RING, 0.28, "sine", 10, 100)
    harmonic = Synthesizer.generate_tone(NOTES['D6'], PING, 0.15, "sine", 5, 60)
    return Synthesizer.mix_tracks(main, harmonic)


def _compose_chime_3() -> QByteArray:
    """Perfect fifth rise - clean and professional."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.28, "sine", 10, 35))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], MEDIUM, 0.30, "sine", 8, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_4() -> QByteArray:
    """Soft triple - macOS-inspired."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], PING, 0.25, "sine", 8, 25))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], PING, 0.27, "sine", 8, 25))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], MEDIUM, 0.30, "sine", 10, 80))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_5() -> QByteArray:
    """Doorbell - friendly two-note."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G5'], MEDIUM, 0.30, "sine", 10, 50))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], RING, 0.28, "sine", 10, 90))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_6() -> QByteArray:
    """Octave ping - clear and bright."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.28, "sine", 8, 30))
    seq.append(Synthesizer.generate_tone(NOTES['C6'], MEDIUM, 0.30, "sine", 8, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_7() -> QByteArray:
    """Slack-style - quick double tap."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['F5'], PING, 0.28, "sine", 5, 20))
    seq.append(Synthesizer.generate_tone(NOTES['A5'], MEDIUM, 0.30, "sine", 8, 60))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_8() -> QByteArray:
    """Crystal - high and delicate."""
    main = Synthesizer.generate_tone(NOTES['A5'], RING, 0.25, "sine", 12, 100)
    shimmer = Synthesizer.generate_tone(NOTES['E6'], PING, 0.12, "sine", 5, 40)
    return Synthesizer.mix_tracks(main, shimmer)


def _compose_chime_9() -> QByteArray:
    """Major third - warm and welcoming."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.28, "sine", 10, 35))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], RING, 0.30, "sine", 10, 90))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_10() -> QByteArray:
    """Attention - subtle urgency."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], PING, 0.28, "sine", 6, 20))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], PING, 0.28, "sine", 6, 20))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], MEDIUM, 0.30, "sine", 8, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_11() -> QByteArray:
    """Zen bell - single pure tone."""
    return Synthesizer.generate_tone(NOTES['G5'], RING + 50, 0.30, "sine", 15, 120)


def _compose_chime_12() -> QByteArray:
    """Positive - ascending major triad (fast)."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['C5'], PING, 0.25, "sine", 6, 20))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], PING, 0.27, "sine", 6, 20))
    seq.append(Synthesizer.generate_tone(NOTES['G5'], MEDIUM, 0.30, "sine", 8, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_13() -> QByteArray:
    """Wind chime - layered harmonics."""
    t1 = Synthesizer.generate_tone(NOTES['E5'], RING, 0.22, "sine", 10, 80)
    t2 = Synthesizer.generate_tone(NOTES['B5'], MEDIUM, 0.18, "sine", 15, 60)
    t3 = Synthesizer.generate_tone(NOTES['G5'], SHORT, 0.15, "sine", 20, 40)
    # Chain mix_tracks calls for 3 tracks
    mixed = Synthesizer.mix_tracks(t1, t2)
    return Synthesizer.mix_tracks(mixed, t3)


def _compose_chime_14() -> QByteArray:
    """Ready - confident two-note."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['D5'], SHORT, 0.28, "sine", 8, 30))
    seq.append(Synthesizer.generate_tone(NOTES['A5'], RING, 0.30, "sine", 8, 90))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_15() -> QByteArray:
    """Soft ping - gentle single."""
    return Synthesizer.generate_tone(NOTES['E5'], RING, 0.28, "sine", 12, 100)


def _compose_chime_16() -> QByteArray:
    """Discord-style - quick rising."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G4'], PING, 0.25, "sine", 5, 15))
    seq.append(Synthesizer.generate_tone(NOTES['D5'], MEDIUM, 0.30, "sine", 8, 70))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_17() -> QByteArray:
    """Bright - high octave jump."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['E5'], SHORT, 0.27, "sine", 8, 30))
    seq.append(Synthesizer.generate_tone(NOTES['E6'], MEDIUM, 0.25, "sine", 8, 80))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_18() -> QByteArray:
    """Calm - descending fifth."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['G5'], SHORT, 0.28, "sine", 10, 40))
    seq.append(Synthesizer.generate_tone(NOTES['C5'], RING, 0.30, "sine", 10, 100))
    return Synthesizer.mix_sequences(seq)


def _compose_chime_19() -> QByteArray:
    """Sparkle - triple with shimmer."""
    main = Synthesizer.generate_tone(NOTES['C5'], SHORT, 0.25, "sine", 8, 30)
    mid = Synthesizer.generate_tone(NOTES['G5'], MEDIUM, 0.28, "sine", 8, 50)
    high = Synthesizer.generate_tone(NOTES['E6'], PING, 0.15, "sine", 5, 40)
    
    # Sequence the first two, layer the shimmer
    base = Synthesizer.mix_sequences([main, mid])
    return Synthesizer.mix_tracks(base, high)


def _compose_chime_20() -> QByteArray:
    """Productivity - clean professional tone."""
    seq = []
    seq.append(Synthesizer.generate_tone(NOTES['A4'], SHORT, 0.28, "sine", 10, 35))
    seq.append(Synthesizer.generate_tone(NOTES['E5'], RING, 0.30, "sine", 10, 90))
    return Synthesizer.mix_sequences(seq)


# List of all chime composers
CHIME_COMPOSERS: List[Callable[[], QByteArray]] = [
    _compose_chime_1,
    _compose_chime_2,
    _compose_chime_3,
    _compose_chime_4,
    _compose_chime_5,
    _compose_chime_6,
    _compose_chime_7,
    _compose_chime_8,
    _compose_chime_9,
    _compose_chime_10,
    _compose_chime_11,
    _compose_chime_12,
    _compose_chime_13,
    _compose_chime_14,
    _compose_chime_15,
    _compose_chime_16,
    _compose_chime_17,
    _compose_chime_18,
    _compose_chime_19,
    _compose_chime_20,
]

# Keep backward compatibility alias
FANFARE_COMPOSERS = CHIME_COMPOSERS


def play_startup_sound() -> bool:
    """
    Play a random startup notification chime.
    
    Uses the Qt-based audio system for high-quality sound.
    Each chime is short (~200-400ms) with soft, pleasant tones.
    
    Industry-standard design:
    - 2-3 notes maximum
    - Pure sine wave tones
    - Harmonic intervals (thirds, fifths, octaves)
    - Soft attack/release envelopes
    - Moderate volume (0.25-0.35)
    
    Returns:
        True if sound was played successfully, False otherwise.
    """
    if not AUDIO_AVAILABLE:
        _logger.warning("Audio system not available for startup sound")
        return False
    
    try:
        # Pick a random chime and compose it
        composer = random.choice(CHIME_COMPOSERS)
        audio_data = composer()
        
        # Play using the celebration audio manager
        manager = CelebrationAudioManager.get_instance()
        return manager.play_buffer(audio_data)
        
    except Exception as e:
        _logger.error(f"Failed to play startup sound: {e}")
        return False


def play_specific_chime(index: int) -> bool:
    """
    Play a specific notification chime by index (0-19).
    Useful for testing or preview.
    
    Args:
        index: Chime index (0-19)
        
    Returns:
        True if sound was played successfully, False otherwise.
    """
    if not AUDIO_AVAILABLE:
        return False
    
    if not (0 <= index < len(CHIME_COMPOSERS)):
        return False
    
    try:
        composer = CHIME_COMPOSERS[index]
        audio_data = composer()
        manager = CelebrationAudioManager.get_instance()
        return manager.play_buffer(audio_data)
    except Exception as e:
        _logger.error(f"Failed to play chime {index}: {e}")
        return False


# Backward compatibility alias
play_specific_fanfare = play_specific_chime


def get_chime_count() -> int:
    """Return the number of available notification chimes."""
    return len(CHIME_COMPOSERS)


# Backward compatibility alias
get_fanfare_count = get_chime_count


def is_sound_available() -> bool:
    """Check if sound playback is available on this system."""
    return AUDIO_AVAILABLE
