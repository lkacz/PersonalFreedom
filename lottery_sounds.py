"""
Lottery Result Sound Effects for Personal Liberty.

Provides short melodic feedback for lottery win/lose outcomes:
- Win sounds: Triumphant, ascending, celebratory (~300-500ms)
- Lose sounds: Gentle disappointment, descending, consoling (~300-400ms)

Uses the Qt-based synthesizer for consistent audio quality.
Designed to be satisfying but not annoying on repeated plays.

Thread Safety:
    These functions are NOT thread-safe. Call only from the main/Qt thread.
    The underlying audio manager uses Qt objects which require single-threaded
    access from the Qt event loop.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from PySide6.QtCore import QByteArray

# ============================================================================
# Public API Exports
# ============================================================================

__all__ = [
    "play_win_sound",
    "play_lose_sound",
    "play_lottery_result",
    "is_sound_available",
    "get_win_count",
    "get_lose_count",
    "preload_lottery_sounds",
]

# ============================================================================
# Audio System Import with Graceful Degradation
# ============================================================================

try:
    from entitidex.celebration_audio import (
        CelebrationAudioManager,
        Synthesizer,
    )
    from PySide6.QtCore import QByteArray

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    Synthesizer = None  # type: ignore[misc, assignment]
    CelebrationAudioManager = None  # type: ignore[misc, assignment]
    QByteArray = None  # type: ignore[misc, assignment]


_logger = logging.getLogger(__name__)


# ============================================================================
# Waveform Types (Replaces Magic Strings)
# ============================================================================


class WaveformType(str, Enum):
    """Supported waveform types for tone generation."""

    SINE = "sine"
    RICH = "rich"
    SQUARE = "square"
    SAW = "saw"


# ============================================================================
# Note Frequencies (Hz) - Musical Constants
# ============================================================================

NOTES: Dict[str, float] = {
    # Octave 3 (for lose sounds - lower, softer)
    "E3": 164.81,
    "G3": 196.00,
    "A3": 220.00,
    "B3": 246.94,
    # Octave 4
    "C4": 261.63,
    "D4": 293.66,
    "E4": 329.63,
    "F4": 349.23,
    "G4": 392.00,
    "A4": 440.00,
    "B4": 493.88,
    # Octave 5 (for win sounds - brighter)
    "C5": 523.25,
    "D5": 587.33,
    "E5": 659.25,
    "F5": 698.46,
    "G5": 783.99,
    "A5": 880.00,
    "B5": 987.77,
    # Octave 6 (accent)
    "C6": 1046.50,
    "E6": 1318.51,
    "G6": 1567.98,
}


# ============================================================================
# Duration Constants (milliseconds)
# ============================================================================


class Duration:
    """Named duration constants for melody composition."""

    QUICK = 60
    SHORT = 100
    MEDIUM = 150
    LONG = 200
    RING = 250


# Legacy aliases for backward compatibility
QUICK = Duration.QUICK
SHORT = Duration.SHORT
MEDIUM = Duration.MEDIUM
LONG = Duration.LONG
RING = Duration.RING


# ============================================================================
# Volume Constants
# ============================================================================


class Volume:
    """Named volume levels for consistent audio mixing."""

    WHISPER = 0.20
    QUIET = 0.22
    SOFT = 0.25
    LOW = 0.28
    MEDIUM_LOW = 0.32
    MEDIUM = 0.35
    MEDIUM_HIGH = 0.38
    LOUD = 0.40
    ACCENT = 0.42
    STRONG = 0.45


# ============================================================================
# Envelope Constants (milliseconds)
# ============================================================================


class Envelope:
    """ADSR envelope timing constants."""

    # Attack times
    ATTACK_INSTANT = 5
    ATTACK_QUICK = 8
    ATTACK_NORMAL = 10
    ATTACK_SOFT = 12
    ATTACK_SLOW = 15
    ATTACK_GENTLE = 20
    ATTACK_SWELL = 25
    ATTACK_GRADUAL = 30

    # Release times
    RELEASE_QUICK = 12
    RELEASE_SHORT = 15
    RELEASE_NORMAL = 20
    RELEASE_MEDIUM = 25
    RELEASE_SOFT = 30
    RELEASE_GENTLE = 40
    RELEASE_LONG = 50
    RELEASE_SMOOTH = 60
    RELEASE_SUSTAINED = 70
    RELEASE_RING = 80
    RELEASE_FADE = 90
    RELEASE_ECHO = 100
    RELEASE_AMBIENT = 120


# ============================================================================
# Data-Driven Melody Composition
# ============================================================================


@dataclass(frozen=True)
class ToneSpec:
    """Specification for a single tone in a melody."""

    note: str
    duration: int
    volume: float
    waveform: str = WaveformType.SINE.value
    attack: int = Envelope.ATTACK_QUICK
    release: int = Envelope.RELEASE_NORMAL

    def generate(self):
        """Generate the audio data for this tone.
        
        Raises:
            RuntimeError: If audio system is not available.
            KeyError: If note is not a valid note name.
        """
        if not AUDIO_AVAILABLE or Synthesizer is None:
            raise RuntimeError("Audio system not available")
        if self.note not in NOTES:
            raise KeyError(f"Invalid note '{self.note}'. Valid notes: {', '.join(sorted(NOTES.keys()))}")
        return Synthesizer.generate_tone(
            NOTES[self.note],
            self.duration,
            self.volume,
            self.waveform,
            self.attack,
            self.release,
        )


@dataclass(frozen=True)
class ChordSpec:
    """Specification for layered tones (polyphonic chord)."""

    tones: tuple  # Tuple[ToneSpec, ...]

    def generate(self):
        """Generate mixed audio data for this chord."""
        if not AUDIO_AVAILABLE or Synthesizer is None:
            raise RuntimeError("Audio system not available")
        if not self.tones:
            raise ValueError("ChordSpec must have at least one tone")

        result = self.tones[0].generate()
        for tone in self.tones[1:]:
            result = Synthesizer.mix_tracks(result, tone.generate())
        return result


@dataclass(frozen=True)
class MelodyDefinition:
    """
    Complete melody definition with metadata.

    Supports both sequential notes and polyphonic chords.
    Elements can be ToneSpec (single note) or ChordSpec (layered notes).
    """

    name: str
    description: str
    elements: tuple  # Tuple[Union[ToneSpec, ChordSpec], ...]

    def compose(self):
        """Compose the complete melody from its elements.
        
        Raises:
            RuntimeError: If audio system is not available.
            ValueError: If elements tuple is empty.
        """
        if not AUDIO_AVAILABLE or Synthesizer is None:
            raise RuntimeError("Audio system not available")
        if not self.elements:
            raise ValueError(f"MelodyDefinition '{self.name}' has no elements")

        sequences = [elem.generate() for elem in self.elements]
        return Synthesizer.mix_sequences(sequences)


# ============================================================================
# WIN MELODIES - Triumphant, ascending, celebratory
# ============================================================================

WIN_MELODIES: List[MelodyDefinition] = [
    MelodyDefinition(
        name="victory_fanfare",
        description="Classic ascending triad",
        elements=(
            ToneSpec("C5", SHORT, Volume.MEDIUM, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("E5", SHORT, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("G5", SHORT, Volume.LOUD, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("C6", RING, Volume.STRONG, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_RING),
        ),
    ),
    MelodyDefinition(
        name="triumphant_chord",
        description="Layered harmony",
        elements=(
            ChordSpec((
                ToneSpec("C5", RING, 0.30, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_RING),
                ToneSpec("E5", RING, 0.28, attack=Envelope.ATTACK_GENTLE, release=Envelope.RELEASE_RING),
                ToneSpec("G5", RING, 0.26, attack=Envelope.ATTACK_SWELL, release=Envelope.RELEASE_RING),
            )),
        ),
    ),
    MelodyDefinition(
        name="quick_success",
        description="Double ping rising",
        elements=(
            ToneSpec("G5", QUICK, Volume.MEDIUM, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("G5", QUICK, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("C6", LONG, Volume.ACCENT, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_SUSTAINED),
        ),
    ),
    MelodyDefinition(
        name="sparkle_win",
        description="High shimmer",
        elements=(
            ToneSpec("E5", QUICK, Volume.MEDIUM_LOW, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_NORMAL),
            ToneSpec("G5", QUICK, Volume.MEDIUM, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_NORMAL),
            ToneSpec("C6", SHORT, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_SOFT),
            ToneSpec("E6", MEDIUM, Volume.LOUD, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SMOOTH),
        ),
    ),
    MelodyDefinition(
        name="power_up",
        description="Ascending scale",
        elements=(
            ToneSpec("C5", QUICK, 0.30, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("D5", QUICK, 0.32, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("E5", QUICK, 0.34, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("G5", SHORT, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("C6", MEDIUM, Volume.ACCENT, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SMOOTH),
        ),
    ),
    MelodyDefinition(
        name="coin_collect",
        description="Classic game sound",
        elements=(
            ToneSpec("E5", SHORT, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_NORMAL),
            ToneSpec("B5", LONG, Volume.ACCENT, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_SUSTAINED),
        ),
    ),
    MelodyDefinition(
        name="achievement",
        description="Bold announcement",
        elements=(
            ToneSpec("G4", SHORT, Volume.MEDIUM, WaveformType.RICH.value, Envelope.ATTACK_QUICK, Envelope.RELEASE_NORMAL),
            ToneSpec("C5", SHORT, Volume.MEDIUM_HIGH, WaveformType.RICH.value, Envelope.ATTACK_QUICK, Envelope.RELEASE_NORMAL),
            ToneSpec("E5", MEDIUM, Volume.LOUD, WaveformType.RICH.value, Envelope.ATTACK_NORMAL, Envelope.RELEASE_GENTLE),
            ToneSpec("G5", LONG, Volume.ACCENT, WaveformType.RICH.value, Envelope.ATTACK_NORMAL, Envelope.RELEASE_SUSTAINED),
        ),
    ),
    MelodyDefinition(
        name="lucky_strike",
        description="Bright double",
        elements=(
            ToneSpec("C5", SHORT, Volume.MEDIUM, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_NORMAL),
            ToneSpec("G5", SHORT, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("C6", RING, Volume.ACCENT, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_RING),
        ),
    ),
    MelodyDefinition(
        name="jackpot",
        description="Celebratory cascade",
        elements=(
            ToneSpec("E5", QUICK, Volume.MEDIUM_LOW, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("G5", QUICK, Volume.MEDIUM, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("C6", QUICK, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("E6", SHORT, Volume.LOUD, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_SOFT),
            ToneSpec("G6", MEDIUM, Volume.ACCENT, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SUSTAINED),
        ),
    ),
    MelodyDefinition(
        name="treasure_found",
        description="Magical discovery",
        elements=(
            ChordSpec((
                ToneSpec("C5", RING, Volume.MEDIUM, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_RING),
                ToneSpec("G5", MEDIUM, Volume.SOFT, attack=Envelope.ATTACK_GENTLE, release=Envelope.RELEASE_SMOOTH),
            )),
        ),
    ),
    MelodyDefinition(
        name="level_up",
        description="Heroic rise",
        elements=(
            ToneSpec("G4", SHORT, Volume.MEDIUM, WaveformType.RICH.value, Envelope.ATTACK_QUICK, Envelope.RELEASE_NORMAL),
            ToneSpec("D5", SHORT, Volume.MEDIUM_HIGH, WaveformType.RICH.value, Envelope.ATTACK_QUICK, Envelope.RELEASE_NORMAL),
            ToneSpec("G5", RING, Volume.ACCENT, WaveformType.RICH.value, Envelope.ATTACK_NORMAL, Envelope.RELEASE_RING),
        ),
    ),
    MelodyDefinition(
        name="victory_dance",
        description="Playful bounce",
        elements=(
            ToneSpec("C5", QUICK, Volume.MEDIUM, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("E5", QUICK, Volume.MEDIUM, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("G5", QUICK, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("E5", QUICK, Volume.MEDIUM, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("C6", MEDIUM, Volume.ACCENT, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SMOOTH),
        ),
    ),
    MelodyDefinition(
        name="prize_bell",
        description="Classic chime",
        elements=(
            ChordSpec((
                ToneSpec("E5", RING, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_FADE),
                ToneSpec("C6", SHORT, Volume.SOFT, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_GENTLE),
            )),
        ),
    ),
    MelodyDefinition(
        name="champion",
        description="Bold fanfare",
        elements=(
            ToneSpec("C5", MEDIUM, Volume.MEDIUM_HIGH, WaveformType.RICH.value, Envelope.ATTACK_NORMAL, Envelope.RELEASE_SOFT),
            ToneSpec("G5", MEDIUM, Volume.LOUD, WaveformType.RICH.value, Envelope.ATTACK_NORMAL, Envelope.RELEASE_SOFT),
            ToneSpec("C6", RING, Volume.ACCENT, WaveformType.RICH.value, Envelope.ATTACK_SOFT, Envelope.RELEASE_RING),
        ),
    ),
    MelodyDefinition(
        name="star_collect",
        description="Bright ascending",
        elements=(
            ToneSpec("G5", SHORT, Volume.MEDIUM, attack=6, release=Envelope.RELEASE_NORMAL),
            ToneSpec("A5", SHORT, Volume.MEDIUM_HIGH, attack=6, release=Envelope.RELEASE_NORMAL),
            ToneSpec("B5", SHORT, Volume.LOUD, attack=6, release=Envelope.RELEASE_NORMAL),
            ToneSpec("C6", LONG, Volume.ACCENT, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SUSTAINED),
        ),
    ),
    MelodyDefinition(
        name="bonus_round",
        description="Exciting climb",
        elements=(
            ToneSpec("E5", QUICK, Volume.MEDIUM_LOW, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_QUICK),
            ToneSpec("E5", QUICK, Volume.MEDIUM, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_QUICK),
            ToneSpec("G5", QUICK, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("G5", QUICK, Volume.LOUD, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("C6", MEDIUM, Volume.ACCENT, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SMOOTH),
        ),
    ),
    MelodyDefinition(
        name="reward_drop",
        description="Satisfying pop",
        elements=(
            ToneSpec("C5", SHORT, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("E5", LONG, Volume.ACCENT, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SUSTAINED),
        ),
    ),
    MelodyDefinition(
        name="perfect_score",
        description="Triple accent",
        elements=(
            ToneSpec("E5", QUICK, Volume.MEDIUM, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("G5", QUICK, Volume.MEDIUM_HIGH, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("E5", QUICK, Volume.MEDIUM, attack=Envelope.ATTACK_INSTANT, release=Envelope.RELEASE_SHORT),
            ToneSpec("C6", RING, Volume.ACCENT, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_RING),
        ),
    ),
    MelodyDefinition(
        name="glory",
        description="Majestic chord swell",
        elements=(
            ChordSpec((
                ToneSpec("G4", RING, 0.30, WaveformType.RICH.value, Envelope.ATTACK_GENTLE, Envelope.RELEASE_FADE),
                ToneSpec("C5", RING, 0.28, WaveformType.RICH.value, Envelope.ATTACK_SWELL, Envelope.RELEASE_FADE),
                ToneSpec("E5", RING, 0.26, WaveformType.RICH.value, Envelope.ATTACK_GRADUAL, Envelope.RELEASE_FADE),
            )),
        ),
    ),
    MelodyDefinition(
        name="epic_loot",
        description="Legendary discovery",
        elements=(
            ToneSpec("G4", SHORT, Volume.MEDIUM, WaveformType.RICH.value, Envelope.ATTACK_QUICK, Envelope.RELEASE_NORMAL),
            ToneSpec("C5", SHORT, Volume.MEDIUM_HIGH, WaveformType.RICH.value, Envelope.ATTACK_QUICK, Envelope.RELEASE_NORMAL),
            ToneSpec("E5", SHORT, Volume.LOUD, WaveformType.RICH.value, Envelope.ATTACK_QUICK, Envelope.RELEASE_MEDIUM),
            ToneSpec("G5", SHORT, Volume.ACCENT, WaveformType.RICH.value, Envelope.ATTACK_QUICK, Envelope.RELEASE_MEDIUM),
            ToneSpec("C6", RING, Volume.STRONG, WaveformType.RICH.value, Envelope.ATTACK_SOFT, Envelope.RELEASE_FADE),
        ),
    ),
]


# ============================================================================
# LOSE MELODIES - Gentle disappointment, descending, consoling
# ============================================================================

LOSE_MELODIES: List[MelodyDefinition] = [
    MelodyDefinition(
        name="gentle_letdown",
        description="Soft descending",
        elements=(
            ToneSpec("E5", MEDIUM, Volume.LOW, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_GENTLE),
            ToneSpec("C5", LONG, Volume.SOFT, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_SMOOTH),
        ),
    ),
    MelodyDefinition(
        name="missed",
        description="Falling interval",
        elements=(
            ToneSpec("G5", SHORT, Volume.LOW, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SOFT),
            ToneSpec("E5", SHORT, 0.26, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SOFT),
            ToneSpec("C5", MEDIUM, 0.24, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_LONG),
        ),
    ),
    MelodyDefinition(
        name="try_again",
        description="Encouraging minor",
        elements=(
            ToneSpec("E4", MEDIUM, Volume.LOW, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_GENTLE),
            ToneSpec("G4", LONG, Volume.SOFT, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_SMOOTH),
        ),
    ),
    MelodyDefinition(
        name="slipped_away",
        description="Fading descent",
        elements=(
            ToneSpec("G4", SHORT, Volume.LOW, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SOFT),
            ToneSpec("E4", SHORT, Volume.SOFT, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("C4", MEDIUM, Volume.QUIET, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_LONG),
        ),
    ),
    MelodyDefinition(
        name="almost",
        description="Hopeful yet disappointed",
        elements=(
            ToneSpec("C5", SHORT, Volume.LOW, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("E5", SHORT, Volume.LOW, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("D5", LONG, Volume.SOFT, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_SMOOTH),
        ),
    ),
    MelodyDefinition(
        name="soft_sigh",
        description="Single descending",
        elements=(
            ToneSpec("G4", RING, Volume.SOFT, attack=Envelope.ATTACK_GENTLE, release=Envelope.RELEASE_ECHO),
        ),
    ),
    MelodyDefinition(
        name="next_time",
        description="Gentle double",
        elements=(
            ToneSpec("E5", SHORT, 0.26, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_SOFT),
            ToneSpec("C5", MEDIUM, 0.24, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_LONG),
        ),
    ),
    MelodyDefinition(
        name="consolation",
        description="Warm minor",
        elements=(
            ChordSpec((
                ToneSpec("A4", LONG, Volume.SOFT, attack=18, release=Envelope.RELEASE_SUSTAINED),
                ToneSpec("C5", MEDIUM, Volume.WHISPER, attack=22, release=Envelope.RELEASE_SMOOTH),
            )),
        ),
    ),
    MelodyDefinition(
        name="gentle_close",
        description="Resolving descent",
        elements=(
            ToneSpec("D5", SHORT, 0.26, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SOFT),
            ToneSpec("C5", MEDIUM, 0.24, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_GENTLE),
            ToneSpec("G4", LONG, Volume.QUIET, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_SMOOTH),
        ),
    ),
    MelodyDefinition(
        name="fade_out",
        description="Quiet ending",
        elements=(
            ToneSpec("E4", RING, Volume.QUIET, attack=Envelope.ATTACK_SWELL, release=Envelope.RELEASE_AMBIENT),
        ),
    ),
    MelodyDefinition(
        name="womp_womp",
        description="Playful sad trombone (short)",
        elements=(
            ToneSpec("B4", MEDIUM, Volume.LOW, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SOFT),
            ToneSpec("A4", LONG, Volume.SOFT, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_SMOOTH),
        ),
    ),
    MelodyDefinition(
        name="keep_trying",
        description="Supportive minor",
        elements=(
            ToneSpec("E4", SHORT, 0.26, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("G4", SHORT, 0.26, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("E4", MEDIUM, 0.24, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_GENTLE),
        ),
    ),
    MelodyDefinition(
        name="soft_landing",
        description="Cushioned fall",
        elements=(
            ToneSpec("G5", QUICK, 0.26, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_NORMAL),
            ToneSpec("E5", QUICK, Volume.SOFT, attack=Envelope.ATTACK_QUICK, release=Envelope.RELEASE_NORMAL),
            ToneSpec("C5", SHORT, 0.24, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_SOFT),
            ToneSpec("G4", MEDIUM, Volume.QUIET, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_LONG),
        ),
    ),
    MelodyDefinition(
        name="quiet_close",
        description="Gentle ending",
        elements=(
            ChordSpec((
                ToneSpec("G4", MEDIUM, 0.24, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_SMOOTH),
                ToneSpec("E4", MEDIUM, Volume.WHISPER, attack=18, release=Envelope.RELEASE_SMOOTH),
            )),
        ),
    ),
    MelodyDefinition(
        name="maybe_later",
        description="Hopeful minor",
        elements=(
            ToneSpec("C5", SHORT, 0.26, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("A4", MEDIUM, 0.24, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_GENTLE),
            ToneSpec("E4", LONG, Volume.QUIET, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_SMOOTH),
        ),
    ),
    MelodyDefinition(
        name="neutral_end",
        description="Neither happy nor sad",
        elements=(
            ToneSpec("C5", LONG, 0.24, attack=18, release=Envelope.RELEASE_RING),
        ),
    ),
    MelodyDefinition(
        name="soft_step_down",
        description="Gentle cascade",
        elements=(
            ToneSpec("E5", QUICK, 0.26, attack=Envelope.ATTACK_QUICK, release=18),
            ToneSpec("D5", QUICK, Volume.SOFT, attack=Envelope.ATTACK_QUICK, release=18),
            ToneSpec("C5", MEDIUM, 0.24, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_GENTLE),
        ),
    ),
    MelodyDefinition(
        name="peaceful_end",
        description="Calming close",
        elements=(
            ToneSpec("G4", MEDIUM, Volume.SOFT, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_GENTLE),
            ToneSpec("C4", LONG, Volume.QUIET, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_SUSTAINED),
        ),
    ),
    MelodyDefinition(
        name="tomorrow",
        description="Encouraging finish",
        elements=(
            ToneSpec("A4", SHORT, 0.26, attack=Envelope.ATTACK_NORMAL, release=Envelope.RELEASE_MEDIUM),
            ToneSpec("G4", MEDIUM, 0.24, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_GENTLE),
            ToneSpec("A4", LONG, 0.26, attack=Envelope.ATTACK_SOFT, release=Envelope.RELEASE_SMOOTH),
        ),
    ),
    MelodyDefinition(
        name="soft_resolve",
        description="Gentle acceptance",
        elements=(
            ChordSpec((
                ToneSpec("C5", LONG, 0.24, attack=Envelope.ATTACK_GENTLE, release=Envelope.RELEASE_RING),
                ToneSpec("G4", MEDIUM, Volume.WHISPER, attack=Envelope.ATTACK_SWELL, release=Envelope.RELEASE_SUSTAINED),
            )),
        ),
    ),
]


# ============================================================================
# Sound Cache for Performance
# ============================================================================

# Sound caches - populated lazily or via preload_lottery_sounds()
_win_sound_cache: Dict[int, object] = {}
_lose_sound_cache: Dict[int, object] = {}


def _clear_sound_cache() -> None:
    """Clear the sound cache. Useful for testing or memory management."""
    _win_sound_cache.clear()
    _lose_sound_cache.clear()


def preload_lottery_sounds() -> int:
    """
    Pre-render all lottery sounds to memory for zero-latency playback.

    Call this during application startup if you want instant sound playback.
    Sounds are generated lazily by default, so this is optional.

    Returns:
        Number of sounds preloaded (win + lose).

    Raises:
        RuntimeError: If audio system is not available.
    """
    if not AUDIO_AVAILABLE:
        _logger.warning("Cannot preload sounds: audio system not available")
        return 0

    count = 0
    for idx, melody in enumerate(WIN_MELODIES):
        try:
            if idx not in _win_sound_cache:
                _win_sound_cache[idx] = melody.compose()
                count += 1
        except (RuntimeError, OSError) as e:
            _logger.warning(f"Failed to preload win sound {idx}: {e}")

    for idx, melody in enumerate(LOSE_MELODIES):
        try:
            if idx not in _lose_sound_cache:
                _lose_sound_cache[idx] = melody.compose()
                count += 1
        except (RuntimeError, OSError) as e:
            _logger.warning(f"Failed to preload lose sound {idx}: {e}")

    _logger.info(f"Preloaded {count} lottery sounds")
    return count


# ============================================================================
# Public API
# ============================================================================


def play_win_sound() -> bool:
    """
    Play a random win/success melody.

    Triumphant, ascending sounds for lottery wins and item drops.
    Duration: ~300-500ms.

    Note:
        This function is NOT thread-safe. Call only from the main/Qt thread.
        The underlying audio manager uses Qt objects which require
        single-threaded access from the Qt event loop.

    Returns:
        True if sound was played successfully, False otherwise.
        Never raises exceptions - sound playback is non-critical.
    """
    if not AUDIO_AVAILABLE:
        _logger.debug("Audio system not available for win sound")
        return False

    if not WIN_MELODIES:
        _logger.warning("No win melodies defined")
        return False

    try:
        idx = random.randrange(len(WIN_MELODIES))

        # Use cached audio data if available, otherwise generate and cache
        if idx not in _win_sound_cache:
            _win_sound_cache[idx] = WIN_MELODIES[idx].compose()

        audio_data = _win_sound_cache[idx]
        manager = CelebrationAudioManager.get_instance()  # type: ignore[union-attr]
        return manager.play_buffer(audio_data)  # type: ignore[arg-type]

    except (RuntimeError, OSError, AttributeError) as e:
        # These can occur from audio device issues
        _logger.warning(f"Failed to play win sound: {e}")
        return False
    except Exception as e:
        # Catch-all for unexpected errors - sound is non-critical
        _logger.exception("Unexpected error in win sound playback")
        return False


def play_lose_sound() -> bool:
    """
    Play a random lose/miss melody.

    Gentle, descending sounds for lottery losses - consoling, not harsh.
    Duration: ~300-400ms.

    Note:
        This function is NOT thread-safe. Call only from the main/Qt thread.
        The underlying audio manager uses Qt objects which require
        single-threaded access from the Qt event loop.

    Returns:
        True if sound was played successfully, False otherwise.
        Never raises exceptions - sound playback is non-critical.
    """
    if not AUDIO_AVAILABLE:
        _logger.debug("Audio system not available for lose sound")
        return False

    if not LOSE_MELODIES:
        _logger.warning("No lose melodies defined")
        return False

    try:
        idx = random.randrange(len(LOSE_MELODIES))

        # Use cached audio data if available, otherwise generate and cache
        if idx not in _lose_sound_cache:
            _lose_sound_cache[idx] = LOSE_MELODIES[idx].compose()

        audio_data = _lose_sound_cache[idx]
        manager = CelebrationAudioManager.get_instance()  # type: ignore[union-attr]
        return manager.play_buffer(audio_data)  # type: ignore[arg-type]

    except (RuntimeError, OSError, AttributeError) as e:
        # These can occur from audio device issues
        _logger.warning(f"Failed to play lose sound: {e}")
        return False
    except Exception as e:
        # Catch-all for unexpected errors - sound is non-critical
        _logger.exception("Unexpected error in lose sound playback")
        return False


def play_lottery_result(won: bool) -> bool:
    """
    Play appropriate sound based on lottery result.

    Args:
        won: True for win sound, False for lose sound.

    Returns:
        True if sound was played successfully, False otherwise.
        Never raises exceptions - sound playback is non-critical.
    """
    if won:
        return play_win_sound()
    else:
        return play_lose_sound()


def is_sound_available() -> bool:
    """
    Check if sound playback is available on this system.

    Returns:
        True if the audio system is available and sounds can be played.
    """
    return AUDIO_AVAILABLE


def get_win_count() -> int:
    """
    Return the number of available win melodies.

    Returns:
        Count of win melody variations.
    """
    return len(WIN_MELODIES)


def get_lose_count() -> int:
    """
    Return the number of available lose melodies.

    Returns:
        Count of lose melody variations.
    """
    return len(LOSE_MELODIES)
