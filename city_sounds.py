"""
City Building System - Sound Effects
=====================================
Unique melodic feedback for city building events.

Each building type has a distinctive sound based on its theme:
- Goldmine: Metallic, ascending coin-like sounds
- Forge: Warm, powerful hammering tones
- Artisan Guild: Artistic, elegant flourishes
- University: Scholarly, enlightening progression
- Training Ground: Strong, marching beats
- Library: Mystical, page-turning whispers
- Market: Busy, transaction jingles
- Royal Mint: Grand, regal fanfares
- Observatory: Ethereal, celestial twinkles
- Wonder: Epic, orchestral crescendo

Sound Events:
- Building Placed: Quick confirmation
- Construction Progress: Rhythmic work sounds
- Building Complete: Celebratory fanfare
- Upgrade Started: Ascending anticipation
- Upgrade Complete: Enhanced celebration
- Income Collected: Satisfying coin sounds
- Demolish: Gentle deconstruction

Uses the Qt-based synthesizer for consistent audio quality.
Thread Safety: Call only from the main/Qt thread.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

_logger = logging.getLogger(__name__)

# ============================================================================
# Audio System Import with Graceful Degradation
# ============================================================================

try:
    from entitidex.celebration_audio import (
        CelebrationAudioManager,
        Synthesizer,
    )
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    Synthesizer = None
    CelebrationAudioManager = None

# ============================================================================
# Note Frequencies (Hz)
# ============================================================================

NOTES: Dict[str, float] = {
    # Low register (warmth, foundation)
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61,
    "G3": 196.00, "A3": 220.00, "B3": 246.94,
    # Mid register (body, melody)
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88,
    # High register (brightness, accents)
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46,
    "G5": 783.99, "A5": 880.00, "B5": 987.77,
    # Sparkle register (magical, ethereal)
    "C6": 1046.50, "D6": 1174.66, "E6": 1318.51, "F6": 1396.91,
    "G6": 1567.98, "A6": 1760.00,
}

# ============================================================================
# Duration Constants (milliseconds)
# ============================================================================

TICK = 40      # Percussive accent
QUICK = 60     # Fast note
SHORT = 100    # Standard note
MEDIUM = 150   # Sustained note
LONG = 200     # Held note
RING = 250     # Resonant finish

# ============================================================================
# Volume Levels
# ============================================================================

WHISPER = 0.18
SOFT = 0.22
LOW = 0.26
MEDIUM_VOL = 0.30
NORMAL = 0.34
ACCENT = 0.38
LOUD = 0.42

# ============================================================================
# Sound Cache
# ============================================================================

_sound_cache: Dict[str, object] = {}


def _clear_cache() -> None:
    """Clear the sound cache."""
    _sound_cache.clear()


def _generate_tone(note: str, duration: int, volume: float,
                   waveform: str = "sine", attack: int = 8, release: int = 20) -> object:
    """Generate a single tone."""
    if not AUDIO_AVAILABLE or Synthesizer is None:
        return None
    return Synthesizer.generate_tone(
        NOTES.get(note, 440.0), duration, volume, waveform, attack, release
    )


def _mix_sequence(tones: list) -> object:
    """Mix tones in sequence."""
    if not AUDIO_AVAILABLE or Synthesizer is None or not tones:
        return None
    valid_tones = [t for t in tones if t is not None]
    if not valid_tones:
        return None
    return Synthesizer.mix_sequences(valid_tones)


def _mix_layers(tones: list) -> object:
    """Mix tones as layers (chord)."""
    if not AUDIO_AVAILABLE or Synthesizer is None or not tones:
        return None
    valid_tones = [t for t in tones if t is not None]
    if not valid_tones:
        return None
    result = valid_tones[0]
    for tone in valid_tones[1:]:
        result = Synthesizer.mix_tracks(result, tone)
    return result


def _play_sound(cache_key: str, generator_func) -> bool:
    """Play a sound with caching."""
    if not AUDIO_AVAILABLE:
        return False
    
    try:
        if cache_key not in _sound_cache:
            audio_data = generator_func()
            if audio_data is None:
                return False
            _sound_cache[cache_key] = audio_data
        
        manager = CelebrationAudioManager.get_instance()
        return manager.play_buffer(_sound_cache[cache_key])
    except Exception as e:
        _logger.debug(f"Sound playback failed for {cache_key}: {e}")
        return False


# ============================================================================
# BUILDING-SPECIFIC SOUND GENERATORS
# Each building has a unique melodic signature
# ============================================================================

def _gen_goldmine_complete():
    """⛏️ Goldmine: Metallic, coin-cascade ascending."""
    return _mix_sequence([
        _generate_tone("E5", TICK, NORMAL, "rich", 3, 15),
        _generate_tone("G5", TICK, NORMAL, "rich", 3, 15),
        _generate_tone("B5", SHORT, ACCENT, "rich", 5, 20),
        _generate_tone("E6", MEDIUM, LOUD, "rich", 8, 40),
    ])


def _gen_forge_complete():
    """🔥 Forge: Warm, powerful hammering with fire crackle."""
    return _mix_sequence([
        _generate_tone("G3", SHORT, NORMAL, "rich", 5, 25),
        _generate_tone("D4", SHORT, ACCENT, "rich", 5, 25),
        _generate_tone("G4", SHORT, LOUD, "rich", 5, 25),
        _mix_layers([
            _generate_tone("D5", RING, ACCENT, "rich", 10, 50),
            _generate_tone("G4", RING, LOW, "rich", 15, 60),
        ]),
    ])


def _gen_artisan_complete():
    """🎨 Artisan Guild: Elegant, artistic flourish."""
    return _mix_sequence([
        _generate_tone("E5", QUICK, SOFT, "sine", 5, 20),
        _generate_tone("F5", QUICK, LOW, "sine", 5, 20),
        _generate_tone("G5", QUICK, NORMAL, "sine", 5, 20),
        _generate_tone("A5", SHORT, ACCENT, "sine", 8, 30),
        _generate_tone("C6", LONG, LOUD, "sine", 10, 50),
    ])


def _gen_university_complete():
    """🎓 University: Scholarly, enlightening progression."""
    return _mix_sequence([
        _generate_tone("C4", SHORT, LOW, "sine", 10, 30),
        _generate_tone("E4", SHORT, NORMAL, "sine", 10, 30),
        _generate_tone("G4", SHORT, ACCENT, "sine", 10, 30),
        _mix_layers([
            _generate_tone("C5", RING, LOUD, "sine", 12, 60),
            _generate_tone("E5", MEDIUM, NORMAL, "sine", 15, 50),
        ]),
    ])


def _gen_training_complete():
    """🏋️ Training Ground: Strong, marching victory."""
    return _mix_sequence([
        _generate_tone("G3", TICK, ACCENT, "square", 3, 15),
        _generate_tone("G3", TICK, LOUD, "square", 3, 15),
        _generate_tone("D4", SHORT, LOUD, "rich", 5, 25),
        _generate_tone("G4", SHORT, ACCENT, "rich", 5, 25),
        _generate_tone("B4", MEDIUM, LOUD, "rich", 8, 40),
    ])


def _gen_library_complete():
    """📚 Library: Mystical, ancient wisdom revealed."""
    return _mix_sequence([
        _mix_layers([
            _generate_tone("A4", MEDIUM, SOFT, "sine", 20, 50),
            _generate_tone("E4", MEDIUM, WHISPER, "sine", 25, 60),
        ]),
        _generate_tone("B4", SHORT, LOW, "sine", 10, 30),
        _generate_tone("C5", SHORT, NORMAL, "sine", 10, 30),
        _generate_tone("E5", RING, ACCENT, "sine", 12, 70),
    ])


def _gen_market_complete():
    """🏪 Market: Busy, jingly transaction sounds."""
    return _mix_sequence([
        _generate_tone("C5", TICK, NORMAL, "rich", 3, 12),
        _generate_tone("E5", TICK, NORMAL, "rich", 3, 12),
        _generate_tone("G5", TICK, ACCENT, "rich", 3, 12),
        _generate_tone("C5", TICK, NORMAL, "rich", 3, 12),
        _generate_tone("E5", SHORT, ACCENT, "rich", 5, 20),
        _generate_tone("C6", MEDIUM, LOUD, "rich", 8, 35),
    ])


def _gen_royal_mint_complete():
    """🏛️ Royal Mint: Grand, regal fanfare."""
    return _mix_sequence([
        _mix_layers([
            _generate_tone("C4", SHORT, LOW, "rich", 8, 30),
            _generate_tone("G3", SHORT, WHISPER, "rich", 10, 35),
        ]),
        _generate_tone("E4", SHORT, NORMAL, "rich", 8, 25),
        _generate_tone("G4", SHORT, ACCENT, "rich", 8, 25),
        _generate_tone("C5", MEDIUM, LOUD, "rich", 10, 40),
        _mix_layers([
            _generate_tone("E5", RING, ACCENT, "rich", 12, 60),
            _generate_tone("C5", RING, NORMAL, "rich", 15, 70),
            _generate_tone("G4", RING, LOW, "rich", 18, 80),
        ]),
    ])


def _gen_observatory_complete():
    """🔭 Observatory: Ethereal, celestial discovery."""
    return _mix_sequence([
        _generate_tone("E5", QUICK, WHISPER, "sine", 15, 40),
        _generate_tone("G5", QUICK, SOFT, "sine", 15, 40),
        _generate_tone("B5", QUICK, LOW, "sine", 15, 40),
        _generate_tone("E6", SHORT, NORMAL, "sine", 12, 50),
        _mix_layers([
            _generate_tone("G6", LONG, ACCENT, "sine", 10, 80),
            _generate_tone("E6", MEDIUM, LOW, "sine", 15, 70),
            _generate_tone("B5", MEDIUM, WHISPER, "sine", 20, 60),
        ]),
    ])


def _gen_wonder_complete():
    """🏰 Wonder: Epic, orchestral triumph."""
    return _mix_sequence([
        # Dramatic opening
        _mix_layers([
            _generate_tone("C4", SHORT, NORMAL, "rich", 10, 35),
            _generate_tone("G3", SHORT, LOW, "rich", 12, 40),
        ]),
        _generate_tone("E4", SHORT, ACCENT, "rich", 8, 30),
        _generate_tone("G4", SHORT, LOUD, "rich", 8, 30),
        _generate_tone("C5", MEDIUM, LOUD, "rich", 8, 35),
        # Triumphant climax
        _mix_layers([
            _generate_tone("E5", RING, ACCENT, "rich", 10, 60),
            _generate_tone("G5", RING, LOUD, "rich", 12, 70),
            _generate_tone("C6", RING, ACCENT, "rich", 15, 80),
        ]),
        # Majestic resolution
        _mix_layers([
            _generate_tone("C5", LONG, NORMAL, "rich", 20, 100),
            _generate_tone("E5", LONG, LOW, "rich", 25, 100),
            _generate_tone("G5", LONG, SOFT, "rich", 30, 100),
        ]),
    ])


# ============================================================================
# GENERIC SOUND GENERATORS (for common events)
# ============================================================================

def _gen_placed():
    """Quick confirmation: Building placed on grid."""
    return _mix_sequence([
        _generate_tone("E5", TICK, NORMAL, "sine", 3, 15),
        _generate_tone("G5", SHORT, ACCENT, "sine", 5, 25),
    ])


def _gen_progress():
    """Work sound: Resources invested."""
    return _mix_sequence([
        _generate_tone("C5", TICK, LOW, "rich", 3, 12),
        _generate_tone("E5", TICK, NORMAL, "rich", 3, 12),
    ])


def _gen_income():
    """Coin collection: Satisfying cash register."""
    return _mix_sequence([
        _generate_tone("E5", TICK, NORMAL, "rich", 3, 10),
        _generate_tone("G5", TICK, ACCENT, "rich", 3, 10),
        _generate_tone("E5", TICK, NORMAL, "rich", 3, 10),
        _generate_tone("C6", SHORT, LOUD, "rich", 5, 30),
    ])


def _gen_upgrade_start():
    """Upgrade initiated: Ascending anticipation."""
    return _mix_sequence([
        _generate_tone("G4", QUICK, LOW, "sine", 5, 20),
        _generate_tone("A4", QUICK, NORMAL, "sine", 5, 20),
        _generate_tone("B4", QUICK, ACCENT, "sine", 5, 20),
        _generate_tone("C5", MEDIUM, LOUD, "sine", 8, 40),
    ])


def _gen_demolish():
    """Demolish: Gentle deconstruction."""
    return _mix_sequence([
        _generate_tone("E5", SHORT, LOW, "sine", 10, 30),
        _generate_tone("C5", SHORT, SOFT, "sine", 12, 35),
        _generate_tone("G4", MEDIUM, WHISPER, "sine", 15, 50),
    ])


# ============================================================================
# PUBLIC API
# ============================================================================

# Building ID to generator mapping
_BUILDING_COMPLETE_SOUNDS = {
    "goldmine": _gen_goldmine_complete,
    "forge": _gen_forge_complete,
    "artisan_guild": _gen_artisan_complete,
    "university": _gen_university_complete,
    "training_ground": _gen_training_complete,
    "library": _gen_library_complete,
    "market": _gen_market_complete,
    "royal_mint": _gen_royal_mint_complete,
    "observatory": _gen_observatory_complete,
    "wonder": _gen_wonder_complete,
}


def play_building_complete(building_id: str) -> bool:
    """
    Play building completion sound with unique melody per building type.
    
    Args:
        building_id: The building identifier (goldmine, forge, etc.)
    
    Returns:
        True if sound played successfully, False otherwise.
    """
    generator = _BUILDING_COMPLETE_SOUNDS.get(building_id)
    if generator:
        return _play_sound(f"complete_{building_id}", generator)
    # Fallback to generic complete sound
    return _play_sound("complete_generic", _gen_goldmine_complete)


def play_building_placed(building_id: Optional[str] = None) -> bool:
    """Play sound when building is placed on grid."""
    return _play_sound("placed", _gen_placed)


def play_construction_progress() -> bool:
    """Play sound when resources are invested."""
    return _play_sound("progress", _gen_progress)


def play_income_collected() -> bool:
    """Play sound when passive income is collected."""
    return _play_sound("income", _gen_income)


def play_upgrade_started(building_id: Optional[str] = None) -> bool:
    """Play sound when upgrade is initiated."""
    return _play_sound("upgrade_start", _gen_upgrade_start)


def play_upgrade_complete(building_id: str) -> bool:
    """Play upgrade completion - enhanced version of building complete."""
    # Upgrades use the same building melody (already distinctive)
    return play_building_complete(building_id)


def play_demolish() -> bool:
    """Play sound when building is demolished."""
    return _play_sound("demolish", _gen_demolish)


def is_city_sound_available() -> bool:
    """Check if city sounds are available."""
    return AUDIO_AVAILABLE


def preload_city_sounds() -> int:
    """
    Pre-render all city sounds to memory for zero-latency playback.
    
    Returns:
        Number of sounds preloaded.
    """
    if not AUDIO_AVAILABLE:
        return 0
    
    count = 0
    
    # Preload all building completion sounds
    for building_id, generator in _BUILDING_COMPLETE_SOUNDS.items():
        try:
            cache_key = f"complete_{building_id}"
            if cache_key not in _sound_cache:
                audio = generator()
                if audio is not None:
                    _sound_cache[cache_key] = audio
                    count += 1
        except Exception as e:
            _logger.warning(f"Failed to preload {building_id} sound: {e}")
    
    # Preload generic sounds
    generic_sounds = [
        ("placed", _gen_placed),
        ("progress", _gen_progress),
        ("income", _gen_income),
        ("upgrade_start", _gen_upgrade_start),
        ("demolish", _gen_demolish),
    ]
    
    for cache_key, generator in generic_sounds:
        try:
            if cache_key not in _sound_cache:
                audio = generator()
                if audio is not None:
                    _sound_cache[cache_key] = audio
                    count += 1
        except Exception as e:
            _logger.warning(f"Failed to preload {cache_key} sound: {e}")
    
    _logger.info(f"Preloaded {count} city sounds")
    return count
