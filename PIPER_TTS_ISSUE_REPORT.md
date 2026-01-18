# Piper TTS Integration Issue Report

## Environment

- **OS**: Windows 10/11
- **Python**: 3.12
- **piper-tts version**: 1.3.0 (latest, July 2025 API)
- **UI Framework**: PySide6 (Qt 6)
- **Audio Backend**: Qt Multimedia with FFmpeg 7.1.2

## Voice Model

- **File**: `voices/en_US-lessac-medium.onnx` (~63MB)
- **Config**: `voices/en_US-lessac-medium.onnx.json`
- **Sample Rate**: 22050 Hz (from config)
- **Format**: 16-bit mono PCM

## What Works

1. **Piper loads successfully**:
   ```
   [GuidanceManager] Piper voice loaded: en_US-lessac-medium.onnx
   ```

2. **Synthesis works in isolation** (standalone test):
   ```python
   from piper import PiperVoice
   import struct
   
   voice = PiperVoice.load('voices/en_US-lessac-medium.onnx')
   for audio_chunk in voice.synthesize("Hello"):
       audio_bytes = audio_chunk.audio_int16_bytes
       # Returns 12288 samples successfully
   ```

3. **Qt audio playback works** for pre-rendered sounds (celebration audio, eye routine sounds) at 44100 Hz.

## The Problem

When integrating Piper TTS with Qt Multimedia for real-time voice playback, we experience:

### Symptom 1: Hard Crash (No Python Traceback)
When calling `say()` synchronously on the main thread during an eye routine:
- App says "starting" (audio plays)
- App crashes immediately with no Python exception
- Exit code 1, no error output
- Suggests crash in C++ layer (ONNX runtime or Qt Multimedia)

### Symptom 2: No Audio (With Threading)
When using background thread for synthesis + `QTimer.singleShot(0, callback)` for playback:
- No crash
- No audio plays
- No error messages

## Current Implementation

```python
class GuidanceManager(QtCore.QObject):
    VOICE_MODEL = "voices/en_US-lessac-medium.onnx"
    
    def __init__(self):
        super().__init__()
        self.audio = CelebrationAudioManager.get_instance()  # Qt audio sink at 44100 Hz
        self._pending_audio = None
        self.piper_voice = PiperVoice.load(str(model_path))
    
    @QtCore.Slot()
    def _play_pending_audio(self):
        """Play pending audio on the main thread."""
        if self._pending_audio:
            qa = QByteArray(self._pending_audio)
            self.audio.play_buffer(qa)  # Uses QAudioSink
            self._pending_audio = None
    
    def say(self, text: str):
        """Speak text using Piper TTS."""
        if not self.piper_voice:
            return
        
        def _synthesize_and_play():
            try:
                import array
                
                # Collect audio chunks
                audio_chunks = []
                for audio_chunk in self.piper_voice.synthesize(text):
                    audio_chunks.append(audio_chunk.audio_int16_bytes)
                
                combined = b''.join(audio_chunks)
                
                # Upsample 22050 -> 44100 (2x, duplicate samples)
                samples = array.array('h')
                samples.frombytes(combined)
                
                upsampled = array.array('h')
                for s in samples:
                    upsampled.append(s)
                    upsampled.append(s)
                
                self._pending_audio = upsampled.tobytes()
                
                # Schedule playback on main thread
                QtCore.QTimer.singleShot(0, self._play_pending_audio)
                
            except Exception as e:
                print(f"[GuidanceManager] TTS error: {e}")
                traceback.print_exc()
        
        thread = threading.Thread(target=_synthesize_and_play, daemon=True)
        thread.start()
```

## Audio Playback System (Working for Other Sounds)

```python
class CelebrationAudioManager(QObject):
    SAMPLE_RATE = 44100
    BIT_DEPTH = 16
    
    def __init__(self):
        format = QAudioFormat()
        format.setSampleRate(44100)
        format.setChannelCount(1)
        format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        
        self._sink = QAudioSink(device, format)
    
    def play_buffer(self, data: QByteArray) -> bool:
        if not self._sink or data.isEmpty():
            return False
        
        self._sink.stop()
        self._current_buffer = QBuffer(data)
        self._current_buffer.setParent(self)
        self._current_buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self._sink.start(self._current_buffer)
        return True
```

## Attempted Solutions

1. **Synchronous synthesis on main thread**: Crashes the app
2. **Threading with QTimer.singleShot**: No audio, no crash
3. **Using struct.pack with *args**: Memory issue with large arrays
4. **Using array.array for efficiency**: No crash, but no audio

## Hypotheses

1. **ONNX Runtime Thread Safety**: Piper's ONNX inference may not be thread-safe, or conflicts with Qt's event loop
2. **QTimer.singleShot from Thread**: May not properly invoke the slot on the main thread
3. **Audio Buffer Lifetime**: The QByteArray or underlying data may be garbage collected before playback completes
4. **Sample Rate Mismatch**: 2x upsampling by duplicating samples may produce inaudible or corrupt audio

## Questions for Expert

1. Is `PiperVoice.synthesize()` thread-safe in piper-tts 1.3.0?
2. What's the correct way to call a Qt slot from a Python thread?
3. Should we use `QMetaObject.invokeMethod` instead of `QTimer.singleShot`?
4. Is there a better resampling approach than sample duplication?
5. Should Piper synthesis happen in a `QThread` instead of `threading.Thread`?

## Desired Outcome

- Non-blocking TTS synthesis (UI stays responsive)
- Audio plays through existing Qt Multimedia infrastructure
- Works offline with Piper neural voices
