"""
Celebration Audio Manager.

Implements a high-quality "Software Synthesizer" using QtMultimedia.
Generates rich procedural audio (sine/triangle waves with envelopes) in real-time.

Features:
- Industry-standard PCM audio generation (44.1kHz, 16-bit).
- Custom ADSR envelopes to prevent "clicking" and shape the sound.
- Polyphonic mixing capabilities.
- Cross-platform (uses PySide6 instead of Windows-specific APIs).
- Caches generated waveforms for zero-latency playback.
"""

import logging
import math
import struct
import time
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, QSettings, Signal, Slot, QThread, QTimer
from PySide6.QtMultimedia import QAudio, QAudioDevice, QAudioFormat, QAudioSink, QMediaDevices

_logger = logging.getLogger(__name__)


class Synthesizer:
    """
    Procedural audio generator.
    Creates PCM audio data mathematically without external files.
    """
    
    SAMPLE_RATE = 44100
    BIT_DEPTH = 16
    MAX_AMPLITUDE = 32700  # Leave some headroom
    
    @staticmethod
    def _pack_sample(value: float) -> bytes:
        """Pack a float sample (-1.0 to 1.0) into 16-bit little-endian bytes."""
        # Clamp value
        value = max(-1.0, min(1.0, value))
        # Scale to integer range
        int_val = int(value * Synthesizer.MAX_AMPLITUDE)
        return struct.pack('<h', int_val)
    
    @staticmethod
    def _unpack_array(ba: QByteArray) -> List[int]:
        """Convert QByteArray to list of int16 samples."""
        # Note: QByteArray can be accessed as bytes in PySide6
        data_bytes = ba.data()
        count = len(data_bytes) // 2
        return list(struct.unpack(f"<{count}h", data_bytes))

    @staticmethod
    def _pack_array(samples: List[int]) -> QByteArray:
        """Convert list of int16 samples to QByteArray."""
        return QByteArray(struct.pack(f"<{len(samples)}h", *samples))

    @staticmethod
    def generate_tone(
        frequency: float, 
        duration_ms: int, 
        volume: float = 0.8,
        wave_type: str = "sine",
        attack_ms: int = 20,
        release_ms: int = 20
    ) -> QByteArray:
        """
        Generate a single tone with envelope.
        """
        num_samples = int(Synthesizer.SAMPLE_RATE * (duration_ms / 1000.0))
        attack_samples = int(Synthesizer.SAMPLE_RATE * (attack_ms / 1000.0))
        release_samples = int(Synthesizer.SAMPLE_RATE * (release_ms / 1000.0))
        
        ba = QByteArray()
        
        # Pre-calculate constants to speed up loop
        two_pi_freq = 2.0 * math.pi * frequency
        sample_rate_inv = 1.0 / Synthesizer.SAMPLE_RATE
        
        for i in range(num_samples):
            t = i * sample_rate_inv
            
            # 1. Oscillator
            if wave_type == "sine":
                sample = math.sin(two_pi_freq * t)
            elif wave_type == "square":
                sample = 1.0 if math.sin(two_pi_freq * t) > 0 else -1.0
            elif wave_type == "saw":
                # Simple saw approximation
                period = 1.0 / frequency
                sample = 2.0 * ((t / period) - math.floor(0.5 + t / period))
            elif wave_type == "rich":
                # Fundamental + Harmonic
                sample = 0.7 * math.sin(two_pi_freq * t)
                sample += 0.3 * math.sin(2.0 * two_pi_freq * t)
            else:
                sample = math.sin(two_pi_freq * t)
                
            # 2. Envelope (ADSR - Simplified to Attack/Release)
            envelope = 1.0
            if i < attack_samples:
                envelope = i / attack_samples
            elif i > num_samples - release_samples:
                remaining = num_samples - i
                envelope = remaining / release_samples
            
            # 3. Final mix
            final_val = sample * volume * envelope
            ba.append(Synthesizer._pack_sample(final_val))
            
        # Add a tiny bit of silence at end for separation
        ba.append(b'\x00\x00' * int(Synthesizer.SAMPLE_RATE * 0.01))
            
        return ba

    @staticmethod
    def mix_sequences(sequences: List[QByteArray]) -> QByteArray:
        """Concatenate multiple audio segments sequentially."""
        full_mix = QByteArray()
        for seq in sequences:
            full_mix.append(seq)
        return full_mix

    @staticmethod
    def mix_tracks(track1: QByteArray, track2: QByteArray) -> QByteArray:
        """Mix two audio tracks polyphonically (summing samples)."""
        s1 = Synthesizer._unpack_array(track1)
        s2 = Synthesizer._unpack_array(track2)
        
        len1 = len(s1)
        len2 = len(s2)
        max_len = max(len1, len2)
        
        # Pad shorter list
        if len1 < max_len:
            s1.extend([0] * (max_len - len1))
        if len2 < max_len:
            s2.extend([0] * (max_len - len2))
            
        mixed = []
        for v1, v2 in zip(s1, s2):
            # Sum and hard clamp to 16-bit signed short range
            val = v1 + v2
            val = max(-32767, min(32767, val))
            mixed.append(val)
            
        return Synthesizer._pack_array(mixed)


# =============================================================================
# THEME SOUND COMPOSITION
# =============================================================================

def _compose_warrior() -> QByteArray:
    """Warrior: Triumphant Brass Fanfare with final chord."""
    seq = []
    # Rapid triplet
    seq.append(Synthesizer.generate_tone(392.00, 100, 0.7, "rich", 10, 10)) # G4
    seq.append(Synthesizer.generate_tone(392.00, 100, 0.7, "rich", 10, 10)) # G4
    seq.append(Synthesizer.generate_tone(392.00, 100, 0.7, "rich", 10, 10)) # G4
    seq.append(Synthesizer.generate_tone(523.25, 400, 0.8, "rich", 10, 50)) # C5
    
    # Final Power Chord (C Major)
    base_chord = Synthesizer.generate_tone(261.63, 800, 0.5, "rich", 50, 400) # C4
    third = Synthesizer.generate_tone(329.63, 800, 0.4, "rich", 50, 400) # E4
    fifth = Synthesizer.generate_tone(392.00, 800, 0.4, "rich", 50, 400) # G4
    
    chord_mix = Synthesizer.mix_tracks(base_chord, third)
    chord_mix = Synthesizer.mix_tracks(chord_mix, fifth)
    
    seq.append(chord_mix)
    
    return Synthesizer.mix_sequences(seq)

def _compose_scholar() -> QByteArray:
    """Scholar: Shimmering ethereal tones."""
    # Create two layers
    # Layer 1: Slow melody
    seq1 = []
    seq1.append(Synthesizer.generate_tone(523.25, 300, 0.5, "sine", 50, 100)) # C5
    seq1.append(Synthesizer.generate_tone(659.25, 300, 0.5, "sine", 50, 100)) # E5
    seq1.append(Synthesizer.generate_tone(783.99, 600, 0.5, "sine", 50, 300)) # G5
    layer1 = Synthesizer.mix_sequences(seq1)
    
    # Layer 2: High shimmer
    seq2 = []
    # Delay start with silence
    seq2.append(QByteArray(b'\x00' * int(Synthesizer.SAMPLE_RATE * 0.1 * 4))) # ~0.2s silence equivalent bytes
    seq2.append(Synthesizer.generate_tone(1046.50, 200, 0.3, "sine", 10, 100)) # C6
    seq2.append(Synthesizer.generate_tone(1318.51, 600, 0.3, "sine", 200, 400)) # E6
    layer2 = Synthesizer.mix_sequences(seq2)
    
    return Synthesizer.mix_tracks(layer1, layer2)

def _compose_wanderer() -> QByteArray:
    """Wanderer: Pentatonic flow with overlap."""
    seq = []
    melody = [392.00, 440.00, 523.25, 392.00, 587.33] # G4, A4, C5, G4, D5
    for freq in melody:
        seq.append(Synthesizer.generate_tone(freq, 180, 0.6, "sine", 40, 60))
    # Final gentle fade
    seq.append(Synthesizer.generate_tone(523.25, 800, 0.5, "sine", 100, 600))
    return Synthesizer.mix_sequences(seq)

def _compose_underdog() -> QByteArray:
    """Underdog: Gritty determination."""
    seq = []
    # Rising chromatic-ish power
    freqs = [220.00, 246.94, 293.66, 329.63, 440.00] 
    for freq in freqs:
        seq.append(Synthesizer.generate_tone(freq, 100, 0.5, "rich", 10, 10))
    # Punchy finish - Octave jump mixed
    low = Synthesizer.generate_tone(220.00, 500, 0.6, "rich", 10, 300)
    high = Synthesizer.generate_tone(440.00, 500, 0.6, "rich", 10, 300)
    seq.append(Synthesizer.mix_tracks(low, high))
    return Synthesizer.mix_sequences(seq)

def _compose_scientist() -> QByteArray:
    """Scientist: Futuristic data processing (Soft/Clean)."""
    seq = []
    # Rapid melodic data bursts (Major 7th arpeggio)
    # C5, E5, G5, B5, C6
    notes = [523.25, 659.25, 783.99, 987.77, 1046.50]
    
    # Burst 1 (Up) - Fast "computer thinking" bubbles
    for note in notes:
        # Very short blips, sine wave -> smooth "bloop"
        seq.append(Synthesizer.generate_tone(note, 60, 0.4, "sine", 5, 20))
        
    # Brief pause
    seq.append(QByteArray(b'\x00' * int(Synthesizer.SAMPLE_RATE * 0.05 * 4)))
    
    # Burst 2 (Down)
    for note in reversed(notes[:3]): # G5, E5, C5
        seq.append(Synthesizer.generate_tone(note, 60, 0.4, "sine", 5, 20))
        
    # Final confirmation chime (Soft synth feel)
    # Mix two sine waves slightly detuned for depth
    tone1 = Synthesizer.generate_tone(1046.50, 400, 0.5, "sine", 20, 300) # C6
    tone2 = Synthesizer.generate_tone(1050.00, 400, 0.3, "sine", 20, 300) # Detuned
    final_chime = Synthesizer.mix_tracks(tone1, tone2)
    
    seq.append(final_chime)
    
    return Synthesizer.mix_sequences(seq)

def _compose_robot() -> QByteArray:
    """Robot: Mechanical pulse evolving into hopeful major harmony."""
    seq = []
    
    # Boot sequence pulses
    boot_notes = [220.00, 246.94, 293.66, 329.63]
    for note in boot_notes:
        seq.append(Synthesizer.generate_tone(note, 80, 0.35, "rich", 5, 15))
    
    # Short pause
    seq.append(QByteArray(b'\x00' * int(Synthesizer.SAMPLE_RATE * 0.04 * 4)))
    
    # Awakening rise
    rise_notes = [329.63, 392.00, 440.00, 523.25]
    for note in rise_notes:
        seq.append(Synthesizer.generate_tone(note, 110, 0.40, "sine", 8, 25))
    
    # Final "open sky" chord (A minor to C major feel)
    root = Synthesizer.generate_tone(261.63, 650, 0.45, "sine", 25, 350)   # C4
    third = Synthesizer.generate_tone(329.63, 650, 0.40, "sine", 25, 350)  # E4
    fifth = Synthesizer.generate_tone(392.00, 650, 0.35, "sine", 25, 350)  # G4
    chord = Synthesizer.mix_tracks(root, third)
    chord = Synthesizer.mix_tracks(chord, fifth)
    seq.append(chord)
    
    return Synthesizer.mix_sequences(seq)

def _compose_space_pirate() -> QByteArray:
    """Space Pirate: Mischievous heist pulse into triumphant orbital chord."""
    seq = []
    
    # Sneaky docking pulses
    pulse_notes = [196.00, 233.08, 261.63, 293.66]
    for note in pulse_notes:
        seq.append(Synthesizer.generate_tone(note, 70, 0.35, "rich", 5, 12))
    
    # Short pause
    seq.append(QByteArray(b'\x00' * int(Synthesizer.SAMPLE_RATE * 0.05 * 4)))
    
    # Upward "escape route found" run
    run_notes = [293.66, 349.23, 392.00, 440.00, 523.25]
    for note in run_notes:
        seq.append(Synthesizer.generate_tone(note, 95, 0.40, "sine", 8, 22))
    
    # Final orbital victory chord
    root = Synthesizer.generate_tone(261.63, 700, 0.45, "sine", 25, 360)   # C4
    third = Synthesizer.generate_tone(329.63, 700, 0.40, "sine", 25, 360)  # E4
    fifth = Synthesizer.generate_tone(392.00, 700, 0.35, "sine", 25, 360)  # G4
    top = Synthesizer.generate_tone(523.25, 700, 0.28, "sine", 25, 360)    # C5
    chord = Synthesizer.mix_tracks(root, third)
    chord = Synthesizer.mix_tracks(chord, fifth)
    chord = Synthesizer.mix_tracks(chord, top)
    seq.append(chord)
    
    return Synthesizer.mix_sequences(seq)


def _compose_thief() -> QByteArray:
    """Thief: Noir pulse, disciplined rise, and resolved civic chord."""
    seq = []

    # Low caution pulses (alley heartbeat)
    intro_notes = [164.81, 196.00, 220.00]
    for note in intro_notes:
        seq.append(Synthesizer.generate_tone(note, 80, 0.32, "rich", 5, 14))

    # Short pause
    seq.append(QByteArray(b'\x00' * int(Synthesizer.SAMPLE_RATE * 0.05 * 4)))

    # Upward "redemption climb"
    climb_notes = [220.00, 261.63, 293.66, 329.63, 392.00]
    for note in climb_notes:
        seq.append(Synthesizer.generate_tone(note, 95, 0.40, "sine", 8, 22))

    # Final stable chord (A minor to C major resolution feel)
    root = Synthesizer.generate_tone(261.63, 700, 0.45, "sine", 25, 360)   # C4
    third = Synthesizer.generate_tone(329.63, 700, 0.40, "sine", 25, 360)  # E4
    fifth = Synthesizer.generate_tone(392.00, 700, 0.35, "sine", 25, 360)  # G4
    top = Synthesizer.generate_tone(523.25, 700, 0.25, "sine", 25, 360)    # C5
    chord = Synthesizer.mix_tracks(root, third)
    chord = Synthesizer.mix_tracks(chord, fifth)
    chord = Synthesizer.mix_tracks(chord, top)
    seq.append(chord)

    return Synthesizer.mix_sequences(seq)


def _compose_zoo_worker() -> QByteArray:
    """Zoo Worker: Calm patrol pulse into warm dawn-resolution chord."""
    seq = []

    # Soft patrol pulses
    intro_notes = [174.61, 220.00, 261.63]
    for note in intro_notes:
        seq.append(Synthesizer.generate_tone(note, 85, 0.32, "rich", 6, 16))

    # Brief pause
    seq.append(QByteArray(b'\x00' * int(Synthesizer.SAMPLE_RATE * 0.05 * 4)))

    # Upward hope run
    rise_notes = [261.63, 293.66, 349.23, 392.00, 440.00]
    for note in rise_notes:
        seq.append(Synthesizer.generate_tone(note, 95, 0.40, "sine", 8, 22))

    # Warm final chord
    root = Synthesizer.generate_tone(261.63, 720, 0.44, "sine", 25, 370)   # C4
    third = Synthesizer.generate_tone(329.63, 720, 0.38, "sine", 25, 370)  # E4
    fifth = Synthesizer.generate_tone(392.00, 720, 0.34, "sine", 25, 370)  # G4
    top = Synthesizer.generate_tone(523.25, 720, 0.24, "sine", 25, 370)    # C5
    chord = Synthesizer.mix_tracks(root, third)
    chord = Synthesizer.mix_tracks(chord, fifth)
    chord = Synthesizer.mix_tracks(chord, top)
    seq.append(chord)

    return Synthesizer.mix_sequences(seq)

def _compose_default() -> QByteArray:
    return Synthesizer.generate_tone(440, 200)

def _compose_eye_start() -> QByteArray:
    """Eye Routine: Start Chime (C5, E5, G5)."""
    seq = []
    # C5
    seq.append(Synthesizer.generate_tone(523.25, 200, 0.4, "sine", 10, 100))
    # Pause 50ms
    seq.append(QByteArray(b'\x00' * int(Synthesizer.SAMPLE_RATE * 0.05 * 2)))
    # E5
    seq.append(Synthesizer.generate_tone(659.25, 200, 0.4, "sine", 10, 100))
    # Pause 50ms
    seq.append(QByteArray(b'\x00' * int(Synthesizer.SAMPLE_RATE * 0.05 * 2)))
    # G5
    seq.append(Synthesizer.generate_tone(783.99, 400, 0.4, "sine", 10, 300))
    return Synthesizer.mix_sequences(seq)

def _compose_eye_complete() -> QByteArray:
    """Eye Routine: Complete (Major Chord)."""
    # C4, E4, G4, C5 simple mix
    t1 = Synthesizer.generate_tone(261.63, 600, 0.4, "sine", 50, 400)
    t2 = Synthesizer.generate_tone(329.63, 600, 0.4, "sine", 50, 400)
    t3 = Synthesizer.generate_tone(392.00, 600, 0.4, "sine", 50, 400)
    t4 = Synthesizer.generate_tone(523.25, 600, 0.4, "sine", 50, 400)
    mix = Synthesizer.mix_tracks(t1, t2)
    mix = Synthesizer.mix_tracks(mix, t3)
    return Synthesizer.mix_tracks(mix, t4)

def _compose_eye_inhale() -> QByteArray:
    """Eye Routine: Rising Inhale (300Hz -> 500Hz)."""
    seq = []
    f_start, f_end, count = 300, 500, 15
    total_ms = 3000
    step_val = (f_end - f_start) / max(1, count - 1)
    dur = total_ms // count
    
    for i in range(count):
        f = f_start + (i * step_val)
        # Soft sine waves, minimal attack/release for smoother transition
        seq.append(Synthesizer.generate_tone(f, dur, 0.3, "sine", 20, 20))
    
    return Synthesizer.mix_sequences(seq)

def _compose_eye_exhale() -> QByteArray:
    """Eye Routine: Falling Exhale (500Hz -> 300Hz)."""
    seq = []
    f_start, f_end, count = 500, 300, 20
    total_ms = 4000
    step_val = (f_end - f_start) / max(1, count - 1)
    dur = total_ms // count
    
    for i in range(count):
        f = f_start + (i * step_val)
        seq.append(Synthesizer.generate_tone(f, dur, 0.3, "sine", 20, 20))
    
    return Synthesizer.mix_sequences(seq)

def _compose_eye_blink_close() -> QByteArray:
    """Eye Routine: Close Eye (Low Boop)."""
    return Synthesizer.generate_tone(300.0, 300, 0.4, "sine", 20, 20)

def _compose_eye_blink_hold() -> QByteArray:
    """Eye Routine: Hold Eye (Quiet High Tone)."""
    return Synthesizer.generate_tone(400.0, 100, 0.2, "sine", 20, 20)

def _compose_eye_blink_open() -> QByteArray:
    """Eye Routine: Open Eye (High Ping)."""
    return Synthesizer.generate_tone(600.0, 100, 0.2, "sine", 20, 20)

def _compose_eye_tick() -> QByteArray:
    """Eye Routine: Timer Tick (Soft Woodblock)."""
    return Synthesizer.generate_tone(800.0, 20, 0.1, "sine", 5, 5)

_THEME_COMPOSERS = {
    "warrior": _compose_warrior,
    "scholar": _compose_scholar,
    "wanderer": _compose_wanderer,
    "underdog": _compose_underdog,
    "scientist": _compose_scientist,
    "robot": _compose_robot,
    "space_pirate": _compose_space_pirate,
    "thief": _compose_thief,
    "zoo_worker": _compose_zoo_worker,
    
    "eye_start": _compose_eye_start,
    "eye_complete": _compose_eye_complete,
    "eye_inhale": _compose_eye_inhale,
    "eye_exhale": _compose_eye_exhale,
    "eye_blink_close": _compose_eye_blink_close,
    "eye_blink_hold": _compose_eye_blink_hold,
    "eye_blink_open": _compose_eye_blink_open,
    "eye_tick": _compose_eye_tick
}


class CelebrationAudioManager(QObject):
    """
    Singleton manager using QtMultimedia for low-latency synthesis.
    
    Playback is queue-driven and non-blocking to keep the Qt GUI thread responsive.
    The sink is released shortly after idle, and safely rebuilt when the default
    output device changes.
    """
    _instance = None
    _play_requested = Signal(QByteArray, bool)
    
    # Minimum time between plays to prevent audio thread exhaustion (ms)
    # Windows MMCSS can only handle ~8-10 audio threads per process
    # Higher value = fewer thread creations = more stable audio
    MIN_PLAY_INTERVAL_MS = 300
    # Time to wait after playback finishes before releasing device (ms)
    RELEASE_DELAY_MS = 1200
    # Periodically re-check default output device to follow device changes.
    DEVICE_RECHECK_INTERVAL_MS = 2000
    # Sanitized fallback volumes.
    DEFAULT_SOUND_VOLUME = 0.5
    DEFAULT_VOICE_VOLUME = 0.8
    # Temporary cooldown after repeated backend failures.
    MAX_CONSECUTIVE_FAILURES = 5
    DISABLE_COOLDOWN_MS = 30000
    
    def __init__(self):
        super().__init__()
        if CelebrationAudioManager._instance is not None:
            return
            
        CelebrationAudioManager._instance = self
        self._cache: Dict[str, QByteArray] = {}
        self._sink: Optional[QAudioSink] = None
        self._current_buffer: Optional[QBuffer] = None
        self._current_data: Optional[QByteArray] = None
        self._last_play_time: int = 0  # Track last play time
        self._audio_format: Optional[QAudioFormat] = None
        self._audio_device: Optional[QAudioDevice] = None
        self._audio_device_key: str = ""
        self._release_timer: Optional[QTimer] = None
        self._channel_count: int = 1
        self._pending_data: Optional[QByteArray] = None
        self._pending_volume: Optional[float] = None
        self._last_device_check_ms: int = 0
        self._consecutive_failures: int = 0
        self._audio_disabled_until_ms: int = 0
        
        self._play_requested.connect(self._play_buffer_internal)
        
        # Load volumes
        s = QSettings("PersonalFreedom", "Audio")
        self._sound_volume = self._sanitize_volume(
            s.value("SoundVolume", self.DEFAULT_SOUND_VOLUME),
            self.DEFAULT_SOUND_VOLUME,
        )
        self._voice_volume = self._sanitize_volume(
            s.value("VoiceVolume", self.DEFAULT_VOICE_VOLUME),
            self.DEFAULT_VOICE_VOLUME,
        )
        
        self._prepare_audio_format()

    @staticmethod
    def _now_ms() -> int:
        """Monotonic milliseconds for stable timing/rate-limit logic."""
        return int(time.monotonic() * 1000)

    @staticmethod
    def _sanitize_volume(value: object, default: float) -> float:
        """Convert persisted values safely to a finite 0..1 range."""
        try:
            vol = float(value)
        except (TypeError, ValueError):
            return default
        if not math.isfinite(vol):
            return default
        return max(0.0, min(1.0, vol))

    @staticmethod
    def _device_key(device: QAudioDevice) -> str:
        """Build a stable-ish key for detecting output device changes."""
        try:
            raw_id = bytes(device.id())
            if raw_id:
                return raw_id.hex()
        except Exception:
            pass
        try:
            return device.description()
        except Exception:
            return ""

    @staticmethod
    def _audio_error_code(error_obj: object) -> int:
        """Normalize Qt audio error enums/values to an int code."""
        try:
            return int(getattr(error_obj, "value", error_obj))
        except Exception:
            return -1

    def set_sound_volume(self, vol: float):
        """Set sound effects volume (0.0 to 1.0)."""
        self._sound_volume = self._sanitize_volume(vol, self.DEFAULT_SOUND_VOLUME)
        QSettings("PersonalFreedom", "Audio").setValue("SoundVolume", self._sound_volume)
        QSettings("PersonalFreedom", "Audio").sync()

    def set_voice_volume(self, vol: float):
        """Set voice volume (0.0 to 1.0)."""
        self._voice_volume = self._sanitize_volume(vol, self.DEFAULT_VOICE_VOLUME)
        QSettings("PersonalFreedom", "Audio").setValue("VoiceVolume", self._voice_volume)
        QSettings("PersonalFreedom", "Audio").sync()
        
    def _prepare_audio_format(self):
        """Prepare audio format without opening the device."""
        try:
            self._audio_device = QMediaDevices.defaultAudioOutput()
            if not self._audio_device:
                _logger.warning("No default audio output device found.")
                self._audio_device_key = ""
                return

            fmt = QAudioFormat()
            fmt.setSampleRate(Synthesizer.SAMPLE_RATE)
            fmt.setChannelCount(1)
            fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)

            if self._audio_device.isFormatSupported(fmt):
                self._audio_format = fmt
                self._channel_count = 1
                self._audio_device_key = self._device_key(self._audio_device)
                _logger.info(
                    "Audio format prepared: %sHz, %s ch (device not opened yet)",
                    fmt.sampleRate(),
                    fmt.channelCount(),
                )
                return

            # Fallback: try stereo at the same sample rate (we can duplicate channels)
            stereo_fmt = QAudioFormat()
            stereo_fmt.setSampleRate(Synthesizer.SAMPLE_RATE)
            stereo_fmt.setChannelCount(2)
            stereo_fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)

            if self._audio_device.isFormatSupported(stereo_fmt):
                self._audio_format = stereo_fmt
                self._channel_count = 2
                self._audio_device_key = self._device_key(self._audio_device)
                _logger.info(
                    "Audio format prepared: %sHz, %s ch (stereo fallback, device not opened yet)",
                    stereo_fmt.sampleRate(),
                    stereo_fmt.channelCount(),
                )
                return

            _logger.warning(
                "Audio device does not support 44.1kHz int16 mono/stereo; disabling audio output."
            )
            self._audio_device = None
            self._audio_format = None
            self._audio_device_key = ""
            
        except Exception as e:
            _logger.error(f"Failed to prepare audio format: {e}")
            self._audio_device = None
            self._audio_format = None
            self._audio_device_key = ""

    def _refresh_audio_device_if_needed(self) -> None:
        """Refresh sink/format if the default output device changed at runtime."""
        now_ms = self._now_ms()
        if now_ms - self._last_device_check_ms < self.DEVICE_RECHECK_INTERVAL_MS:
            return
        self._last_device_check_ms = now_ms

        try:
            default_device = QMediaDevices.defaultAudioOutput()
        except Exception as e:
            _logger.debug(f"Failed to query default audio output: {e}")
            return

        if not default_device:
            if self._audio_device is not None:
                _logger.warning("Default audio output disappeared; releasing sink.")
                self._release_device()
                self._audio_device = None
                self._audio_format = None
                self._audio_device_key = ""
            return

        new_key = self._device_key(default_device)
        if not new_key:
            return

        if new_key != self._audio_device_key:
            _logger.info("Default audio output changed. Reinitializing audio sink.")
            self._release_device()
            self._audio_device = None
            self._audio_format = None
            self._audio_device_key = ""
            self._prepare_audio_format()

    def _mono_to_stereo(self, data: QByteArray) -> QByteArray:
        """Duplicate mono int16 samples to stereo interleaved samples."""
        import array

        if data.isEmpty():
            return data

        samples = array.array("h")
        samples.frombytes(bytes(data))
        if not samples:
            return data

        stereo = array.array("h", [0]) * (2 * len(samples))
        for i, sample in enumerate(samples):
            idx = 2 * i
            stereo[idx] = sample
            stereo[idx + 1] = sample

        return QByteArray(stereo.tobytes())
    
    def _ensure_sink_ready(self) -> bool:
        """Create audio sink on-demand for playback."""
        if self._sink is not None:
            return True
        
        if not self._audio_device or not self._audio_format:
            self._prepare_audio_format()
        if not self._audio_device or not self._audio_format:
            return False
        
        try:
            self._sink = QAudioSink(self._audio_device, self._audio_format)
            try:
                # Keep buffer reasonably small to reduce stalls/latency.
                self._sink.setBufferSize(8192)
            except Exception:
                pass
            self._sink.stateChanged.connect(self._on_state_changed)
            _logger.debug("Audio sink created for playback")
            return True
        except Exception as e:
            _logger.error(f"Failed to create audio sink: {e}")
            self._sink = None
            return False
    
    @Slot(QAudio.State)
    def _on_state_changed(self, state: QAudio.State) -> None:
        """Handle audio sink state changes."""
        if self._sink is None:
            return
        _logger.debug("Audio sink state changed to: %s", state)

        if state == QAudio.State.StoppedState:
            try:
                sink_error = self._sink.error()
            except Exception:
                sink_error = QAudio.Error.NoError
            if self._audio_error_code(sink_error) != self._audio_error_code(QAudio.Error.NoError):
                _logger.warning("Audio sink stopped with error: %s", sink_error)
                self._register_failure("sink stopped with backend error")
                self._release_device()
                return

        if state in (QAudio.State.IdleState, QAudio.State.StoppedState):
            if self._pending_data is not None:
                self._start_pending_playback()
            else:
                self._schedule_release()
    
    def _schedule_release(self) -> None:
        """Schedule audio device release after a short delay."""
        if self._sink is None:
            return
        if self._release_timer is None:
            self._release_timer = QTimer(self)
            self._release_timer.setSingleShot(True)
            self._release_timer.timeout.connect(self._release_device)
        self._release_timer.start(self.RELEASE_DELAY_MS)

    def _release_current_buffer(self) -> None:
        """Safely dispose current playback buffer."""
        if self._current_buffer is None:
            return
        try:
            self._current_buffer.close()
            self._current_buffer.deleteLater()
        except Exception:
            pass
        self._current_buffer = None
    
    def _release_device(self) -> None:
        """Release the audio device to prevent interference with other apps."""
        if self._release_timer is not None:
            try:
                self._release_timer.stop()
            except Exception:
                pass

        if self._sink is not None:
            try:
                try:
                    self._sink.stateChanged.disconnect(self._on_state_changed)
                except Exception:
                    pass
                self._sink.stop()
                self._sink.deleteLater()
            except Exception as e:
                _logger.debug(f"Error releasing audio sink: {e}")
            self._sink = None
        
        self._release_current_buffer()
        self._current_data = None
        self._pending_data = None
        self._pending_volume = None
        
        _logger.debug("Audio device released")

    def _register_failure(self, context: str) -> None:
        """Track backend failures and enter cooldown if unstable."""
        self._consecutive_failures += 1
        _logger.debug(
            "Audio failure #%s: %s",
            self._consecutive_failures,
            context,
        )
        if self._consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
            self._audio_disabled_until_ms = self._now_ms() + self.DISABLE_COOLDOWN_MS
            _logger.error(
                "Audio temporarily disabled for %sms after %s consecutive failures.",
                self.DISABLE_COOLDOWN_MS,
                self._consecutive_failures,
            )
            self._release_device()

    def _register_success(self) -> None:
        """Reset failure counter when playback resumes cleanly."""
        self._consecutive_failures = 0
        self._audio_disabled_until_ms = 0

    def _is_audio_temporarily_disabled(self) -> bool:
        if self._audio_disabled_until_ms <= 0:
            return False
        now_ms = self._now_ms()
        if now_ms >= self._audio_disabled_until_ms:
            _logger.info("Audio cooldown elapsed; re-enabling playback.")
            self._audio_disabled_until_ms = 0
            self._consecutive_failures = 0
            return False
        return True

    def _start_pending_playback(self) -> bool:
        """Start queued playback when sink is ready (non-blocking path)."""
        if self._pending_data is None:
            return False
        if not self._ensure_sink_ready():
            self._register_failure("sink not ready while starting pending playback")
            return False
        if self._sink is None:
            self._register_failure("sink unexpectedly missing")
            return False

        try:
            self._release_current_buffer()

            self._current_data = self._pending_data
            self._pending_data = None
            target = self._pending_volume if self._pending_volume is not None else self._sound_volume
            self._pending_volume = None
            self._sink.setVolume(self._sanitize_volume(target, self.DEFAULT_SOUND_VOLUME))

            self._current_buffer = QBuffer(self)
            self._current_buffer.setData(self._current_data)
            if not self._current_buffer.open(QIODevice.OpenModeFlag.ReadOnly):
                raise RuntimeError("Failed to open QBuffer for audio playback")

            self._sink.start(self._current_buffer)
            self._register_success()
            return True
        except Exception as e:
            _logger.error("Failed to start playback: %s", e)
            self._register_failure("exception in _start_pending_playback")
            self._release_current_buffer()
            self._current_data = None
            return False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def preload_all(self):
        """Pre-render all theme sounds to memory."""
        _logger.info("Pre-rendering celebration synthesis...")
        for theme_id, composer in _THEME_COMPOSERS.items():
            try:
                self._cache[theme_id] = composer()
                _logger.debug(f"Rendered {theme_id}")
            except Exception as e:
                _logger.error(f"Failed to render {theme_id}: {e}")

    def play_buffer(self, data: QByteArray, is_voice: bool = False) -> bool:
        """Play a raw audio buffer with non-blocking sink handoff.
        
        Args:
            data: Raw PCM audio data
            is_voice: If True, bypasses rate limiting (voice has synthesis delay built-in)
        """
        if data.isEmpty():
            return False
        # Route non-owner thread calls through a queued signal to keep Qt object access safe.
        if QThread.currentThread() is not self.thread():
            self._play_requested.emit(QByteArray(data), bool(is_voice))
            return True
        return self._play_buffer_internal(data, is_voice)

    @Slot(QByteArray, bool)
    def _play_buffer_internal(self, data: QByteArray, is_voice: bool = False) -> bool:
        """Main-thread playback logic (invoked directly or via queued signal)."""
        if data.isEmpty():
            return False
        if self._is_audio_temporarily_disabled():
            return False

        current_time = self._now_ms()
        if not is_voice and (current_time - self._last_play_time < self.MIN_PLAY_INTERVAL_MS):
            _logger.debug(
                "Rate limited sound play, delta=%sms",
                current_time - self._last_play_time,
            )
            return False

        if self._release_timer is not None and self._release_timer.isActive():
            try:
                self._release_timer.stop()
            except Exception:
                pass

        self._refresh_audio_device_if_needed()
        if not self._ensure_sink_ready():
            self._register_failure("unable to create audio sink")
            return False

        play_data = data
        if self._channel_count == 2:
            play_data = self._mono_to_stereo(data)

        self._pending_data = QByteArray(play_data)
        self._pending_volume = self._voice_volume if is_voice else self._sound_volume
        if not is_voice:
            self._last_play_time = current_time

        if self._sink is None:
            self._register_failure("sink missing after _ensure_sink_ready")
            return False

        state = self._sink.state()
        if state == QAudio.State.ActiveState:
            # Stop is asynchronous; stateChanged handler starts pending data.
            self._sink.stop()
            return True

        return self._start_pending_playback()

    def play(self, theme_id: str = "default") -> bool:
        """Play the synthesized sound for the theme."""
        # Get or generate data
        if theme_id not in self._cache:
             composer = _THEME_COMPOSERS.get(theme_id, _compose_default)
             self._cache[theme_id] = composer()
        
        data = self._cache.get(theme_id)
        if not data:
            return False
            
        return self.play_buffer(data, is_voice=False)

    def stop(self):
        """Stop current playback and release device."""
        self._pending_data = None
        self._pending_volume = None
        if self._sink:
            self._sink.stop()
        self._release_device()


# Public API
def play_celebration_sound(theme_id: str = "default") -> bool:
    manager = CelebrationAudioManager.get_instance()
    return manager.play(theme_id)

def preload_celebration_sounds():
    manager = CelebrationAudioManager.get_instance()
    manager.preload_all()
