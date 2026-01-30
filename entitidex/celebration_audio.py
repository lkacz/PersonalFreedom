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
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject
from PySide6.QtMultimedia import QAudioDevice, QAudioFormat, QAudioSink, QMediaDevices

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
    
    Properly releases audio device after playback to prevent interference
    with other Windows applications.
    """
    _instance = None
    
    # Minimum time between plays to prevent audio thread exhaustion (ms)
    MIN_PLAY_INTERVAL_MS = 150
    # Time to wait after playback finishes before releasing device (ms)
    RELEASE_DELAY_MS = 500
    
    def __init__(self):
        super().__init__()
        if CelebrationAudioManager._instance is not None:
            return
            
        CelebrationAudioManager._instance = self
        self._cache: Dict[str, QByteArray] = {}
        self._sink: Optional[QAudioSink] = None
        self._current_buffer: Optional[QBuffer] = None
        self._last_play_time: int = 0  # Track last play time
        self._audio_format: Optional[QAudioFormat] = None
        self._audio_device: Optional[QAudioDevice] = None
        self._release_timer: Optional[object] = None  # Timer for delayed release
        self._prepare_audio_format()
        
    def _prepare_audio_format(self):
        """Prepare audio format without opening the device."""
        try:
            self._audio_device = QMediaDevices.defaultAudioOutput()
            if not self._audio_device:
                _logger.warning("No default audio output device found.")
                return

            fmt = QAudioFormat()
            fmt.setSampleRate(Synthesizer.SAMPLE_RATE)
            fmt.setChannelCount(1)  # Mono
            fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
            
            if not self._audio_device.isFormatSupported(fmt):
                # Try to fall back to a standard format if the exact one isn't supported
                fmt = self._audio_device.preferredFormat()
            
            self._audio_format = fmt
            _logger.info(f"Audio format prepared: {fmt.sampleRate()}Hz (device not opened yet)")
            
        except Exception as e:
            _logger.error(f"Failed to prepare audio format: {e}")
            self._audio_device = None
            self._audio_format = None
    
    def _ensure_sink_ready(self) -> bool:
        """Create audio sink on-demand for playback."""
        if self._sink is not None:
            return True
        
        if not self._audio_device or not self._audio_format:
            return False
        
        try:
            self._sink = QAudioSink(self._audio_device, self._audio_format)
            self._sink.setVolume(0.4)  # Lower volume for comfortable listening
            # Connect to state changes to detect playback completion
            self._sink.stateChanged.connect(self._on_state_changed)
            _logger.debug("Audio sink created for playback")
            return True
        except Exception as e:
            _logger.error(f"Failed to create audio sink: {e}")
            self._sink = None
            return False
    
    def _on_state_changed(self, state) -> None:
        """Handle audio sink state changes to release device when done."""
        from PySide6.QtMultimedia import QAudio
        
        if state == QAudio.State.IdleState:
            # Playback finished - schedule device release
            self._schedule_release()
        elif state == QAudio.State.StoppedState:
            # Explicitly stopped - also schedule release
            self._schedule_release()
    
    def _schedule_release(self) -> None:
        """Schedule audio device release after a short delay."""
        # Cancel any existing release timer
        if self._release_timer is not None:
            try:
                self._release_timer.stop()
            except Exception:
                pass
        
        # Create a timer to release device after delay
        from PySide6.QtCore import QTimer
        self._release_timer = QTimer(self)
        self._release_timer.setSingleShot(True)
        self._release_timer.timeout.connect(self._release_device)
        self._release_timer.start(self.RELEASE_DELAY_MS)
    
    def _release_device(self) -> None:
        """Release the audio device to prevent interference with other apps."""
        if self._sink is not None:
            try:
                self._sink.stop()
                self._sink.deleteLater()
            except Exception as e:
                _logger.debug(f"Error releasing audio sink: {e}")
            self._sink = None
        
        if self._current_buffer is not None:
            try:
                self._current_buffer.close()
                self._current_buffer.deleteLater()
            except Exception:
                pass
            self._current_buffer = None
        
        self._release_timer = None
        _logger.debug("Audio device released")

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

    def play_buffer(self, data: QByteArray) -> bool:
        """Play a raw audio buffer with rate limiting to prevent thread exhaustion."""
        if data.isEmpty():
            return False
        
        # Cancel any pending release since we're about to play
        if self._release_timer is not None:
            try:
                self._release_timer.stop()
                self._release_timer = None
            except Exception:
                pass

        # Rate limit to prevent Windows MMCSS thread exhaustion
        import time
        current_time = int(time.time() * 1000)
        if current_time - self._last_play_time < self.MIN_PLAY_INTERVAL_MS:
            # Too soon, skip this play request
            return False
        self._last_play_time = current_time
        
        # Ensure audio sink is ready (creates on-demand)
        if not self._ensure_sink_ready():
            return False

        # 1. Stop current playback strictly
        self._sink.stop()
        
        # 2. Clean up previous buffer
        if self._current_buffer is not None:
            try:
                self._current_buffer.close()
                self._current_buffer.deleteLater()
            except Exception:
                pass
        
        # 3. Keep the QByteArray alive as instance attribute (prevents use-after-free)
        self._current_data = QByteArray(data)  # Make a copy we own
        
        # 4. Create QBuffer that owns its data via setData()
        self._current_buffer = QBuffer(self)
        self._current_buffer.setData(self._current_data)  # QBuffer now owns the bytes
        self._current_buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        
        # 5. Start playback
        self._sink.start(self._current_buffer)
        return True

    def play(self, theme_id: str = "default") -> bool:
        """Play the synthesized sound for the theme."""
        # Get or generate data
        if theme_id not in self._cache:
             composer = _THEME_COMPOSERS.get(theme_id, _compose_default)
             self._cache[theme_id] = composer()
        
        data = self._cache.get(theme_id)
        if not data:
            return False
            
        return self.play_buffer(data)

    def stop(self):
        """Stop current playback and release device."""
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
