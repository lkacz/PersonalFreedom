"""
Unit tests for lottery_sounds module.

Tests cover:
- Module import and public API verification
- Melody integrity validation (notes, volumes, durations, waveforms, envelopes)
- Sound caching behavior
- Edge cases (empty chords, invalid notes, empty melody lists)
- Public API contract testing
- Graceful degradation when audio is unavailable
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Set


# ============================================================================
# Module Import Tests
# ============================================================================


class TestModuleImport:
    """Test that the module imports correctly and has expected structure."""

    def test_module_imports_successfully(self):
        """Module should import without errors."""
        import lottery_sounds
        assert lottery_sounds is not None

    def test_all_exports_are_defined(self):
        """All items in __all__ should exist in the module."""
        import lottery_sounds
        
        for name in lottery_sounds.__all__:
            assert hasattr(lottery_sounds, name), f"Missing export: {name}"

    def test_all_exports_are_callable_or_valid(self):
        """Exported items should be callable functions."""
        import lottery_sounds
        
        expected_functions = [
            "play_win_sound",
            "play_lose_sound",
            "play_lottery_result",
            "is_sound_available",
            "get_win_count",
            "get_lose_count",
            "preload_lottery_sounds",
        ]
        
        for name in expected_functions:
            assert callable(getattr(lottery_sounds, name)), f"{name} should be callable"

    def test_public_api_count(self):
        """__all__ should export expected number of items."""
        import lottery_sounds
        assert len(lottery_sounds.__all__) == 7


# ============================================================================
# Constants and Enums Tests
# ============================================================================


class TestConstants:
    """Test that all constants are properly defined."""

    def test_notes_dict_exists_and_populated(self):
        """NOTES dictionary should contain musical note frequencies."""
        import lottery_sounds
        
        assert isinstance(lottery_sounds.NOTES, dict)
        assert len(lottery_sounds.NOTES) > 0

    def test_notes_all_positive_frequencies(self):
        """All note frequencies should be positive numbers."""
        import lottery_sounds
        
        for note, freq in lottery_sounds.NOTES.items():
            assert isinstance(freq, (int, float)), f"{note} frequency should be numeric"
            assert freq > 0, f"{note} frequency should be positive"

    def test_duration_constants_exist(self):
        """Duration constants should be defined."""
        import lottery_sounds
        
        assert lottery_sounds.QUICK > 0
        assert lottery_sounds.SHORT > 0
        assert lottery_sounds.MEDIUM > 0
        assert lottery_sounds.LONG > 0
        assert lottery_sounds.RING > 0

    def test_duration_ordering(self):
        """Duration constants should be in ascending order."""
        import lottery_sounds
        
        assert lottery_sounds.QUICK < lottery_sounds.SHORT
        assert lottery_sounds.SHORT < lottery_sounds.MEDIUM
        assert lottery_sounds.MEDIUM < lottery_sounds.LONG
        assert lottery_sounds.LONG < lottery_sounds.RING

    def test_volume_class_exists(self):
        """Volume class should have named volume levels."""
        import lottery_sounds
        
        assert hasattr(lottery_sounds, 'Volume')
        assert 0 < lottery_sounds.Volume.WHISPER < lottery_sounds.Volume.STRONG <= 1.0

    def test_envelope_class_exists(self):
        """Envelope class should have attack and release constants."""
        import lottery_sounds
        
        assert hasattr(lottery_sounds, 'Envelope')
        assert lottery_sounds.Envelope.ATTACK_INSTANT > 0
        assert lottery_sounds.Envelope.RELEASE_QUICK > 0

    def test_waveform_enum_exists(self):
        """WaveformType enum should define valid waveforms."""
        import lottery_sounds
        
        assert hasattr(lottery_sounds, 'WaveformType')
        assert lottery_sounds.WaveformType.SINE.value == "sine"
        assert lottery_sounds.WaveformType.RICH.value == "rich"


# ============================================================================
# Melody Integrity Tests
# ============================================================================


class TestMelodyIntegrity:
    """Test that all melodies are properly defined with valid values."""

    def test_win_melodies_count(self):
        """Should have exactly 20 win melodies."""
        import lottery_sounds
        assert len(lottery_sounds.WIN_MELODIES) == 20

    def test_lose_melodies_count(self):
        """Should have exactly 20 lose melodies."""
        import lottery_sounds
        assert len(lottery_sounds.LOSE_MELODIES) == 20

    def test_all_win_melodies_have_elements(self):
        """Each win melody should have at least one element."""
        import lottery_sounds
        
        for melody in lottery_sounds.WIN_MELODIES:
            assert len(melody.elements) > 0, f"Melody '{melody.name}' has no elements"

    def test_all_lose_melodies_have_elements(self):
        """Each lose melody should have at least one element."""
        import lottery_sounds
        
        for melody in lottery_sounds.LOSE_MELODIES:
            assert len(melody.elements) > 0, f"Melody '{melody.name}' has no elements"

    def test_all_notes_are_valid(self):
        """All notes used in melodies should exist in NOTES dict."""
        import lottery_sounds
        
        all_melodies = lottery_sounds.WIN_MELODIES + lottery_sounds.LOSE_MELODIES
        
        for melody in all_melodies:
            for elem in melody.elements:
                if hasattr(elem, 'note'):
                    assert elem.note in lottery_sounds.NOTES, \
                        f"Invalid note '{elem.note}' in melody '{melody.name}'"
                elif hasattr(elem, 'tones'):
                    for tone in elem.tones:
                        assert tone.note in lottery_sounds.NOTES, \
                            f"Invalid note '{tone.note}' in chord in melody '{melody.name}'"

    def test_all_volumes_in_valid_range(self):
        """All volumes should be between 0.0 and 1.0."""
        import lottery_sounds
        
        all_melodies = lottery_sounds.WIN_MELODIES + lottery_sounds.LOSE_MELODIES
        
        for melody in all_melodies:
            for elem in melody.elements:
                if hasattr(elem, 'volume'):
                    assert 0.0 <= elem.volume <= 1.0, \
                        f"Invalid volume {elem.volume} in melody '{melody.name}'"
                elif hasattr(elem, 'tones'):
                    for tone in elem.tones:
                        assert 0.0 <= tone.volume <= 1.0, \
                            f"Invalid volume {tone.volume} in chord in melody '{melody.name}'"

    def test_all_durations_positive(self):
        """All durations should be positive integers."""
        import lottery_sounds
        
        all_melodies = lottery_sounds.WIN_MELODIES + lottery_sounds.LOSE_MELODIES
        
        for melody in all_melodies:
            for elem in melody.elements:
                if hasattr(elem, 'duration'):
                    assert elem.duration > 0, \
                        f"Invalid duration {elem.duration} in melody '{melody.name}'"
                elif hasattr(elem, 'tones'):
                    for tone in elem.tones:
                        assert tone.duration > 0, \
                            f"Invalid duration {tone.duration} in chord in melody '{melody.name}'"

    def test_all_waveforms_valid(self):
        """All waveforms should be valid types."""
        import lottery_sounds
        
        valid_waveforms = {'sine', 'rich', 'square', 'saw'}
        all_melodies = lottery_sounds.WIN_MELODIES + lottery_sounds.LOSE_MELODIES
        
        for melody in all_melodies:
            for elem in melody.elements:
                if hasattr(elem, 'waveform'):
                    assert elem.waveform in valid_waveforms, \
                        f"Invalid waveform '{elem.waveform}' in melody '{melody.name}'"
                elif hasattr(elem, 'tones'):
                    for tone in elem.tones:
                        assert tone.waveform in valid_waveforms, \
                            f"Invalid waveform '{tone.waveform}' in chord in melody '{melody.name}'"

    def test_all_envelopes_non_negative(self):
        """All attack and release values should be non-negative."""
        import lottery_sounds
        
        all_melodies = lottery_sounds.WIN_MELODIES + lottery_sounds.LOSE_MELODIES
        
        for melody in all_melodies:
            for elem in melody.elements:
                if hasattr(elem, 'attack'):
                    assert elem.attack >= 0, \
                        f"Negative attack {elem.attack} in melody '{melody.name}'"
                    assert elem.release >= 0, \
                        f"Negative release {elem.release} in melody '{melody.name}'"
                elif hasattr(elem, 'tones'):
                    for tone in elem.tones:
                        assert tone.attack >= 0, \
                            f"Negative attack {tone.attack} in chord in melody '{melody.name}'"
                        assert tone.release >= 0, \
                            f"Negative release {tone.release} in chord in melody '{melody.name}'"

    def test_melody_names_unique(self):
        """All melody names should be unique within their category."""
        import lottery_sounds
        
        win_names = [m.name for m in lottery_sounds.WIN_MELODIES]
        lose_names = [m.name for m in lottery_sounds.LOSE_MELODIES]
        
        assert len(win_names) == len(set(win_names)), "Duplicate win melody names"
        assert len(lose_names) == len(set(lose_names)), "Duplicate lose melody names"


# ============================================================================
# Public API Tests
# ============================================================================


class TestPublicAPI:
    """Test the public API functions."""

    def test_is_sound_available_returns_bool(self):
        """is_sound_available should return a boolean."""
        import lottery_sounds
        
        result = lottery_sounds.is_sound_available()
        assert isinstance(result, bool)

    def test_get_win_count_returns_int(self):
        """get_win_count should return an integer."""
        import lottery_sounds
        
        result = lottery_sounds.get_win_count()
        assert isinstance(result, int)
        assert result == 20

    def test_get_lose_count_returns_int(self):
        """get_lose_count should return an integer."""
        import lottery_sounds
        
        result = lottery_sounds.get_lose_count()
        assert isinstance(result, int)
        assert result == 20

    def test_play_win_sound_returns_bool(self):
        """play_win_sound should return a boolean."""
        import lottery_sounds
        
        result = lottery_sounds.play_win_sound()
        assert isinstance(result, bool)

    def test_play_lose_sound_returns_bool(self):
        """play_lose_sound should return a boolean."""
        import lottery_sounds
        
        result = lottery_sounds.play_lose_sound()
        assert isinstance(result, bool)

    def test_play_lottery_result_with_true(self):
        """play_lottery_result(True) should return a boolean."""
        import lottery_sounds
        
        result = lottery_sounds.play_lottery_result(True)
        assert isinstance(result, bool)

    def test_play_lottery_result_with_false(self):
        """play_lottery_result(False) should return a boolean."""
        import lottery_sounds
        
        result = lottery_sounds.play_lottery_result(False)
        assert isinstance(result, bool)

    def test_play_lottery_result_with_truthy_values(self):
        """play_lottery_result should accept truthy/falsy values."""
        import lottery_sounds
        
        # Should not raise exceptions
        result1 = lottery_sounds.play_lottery_result(1)
        result2 = lottery_sounds.play_lottery_result(0)
        result3 = lottery_sounds.play_lottery_result("yes")
        result4 = lottery_sounds.play_lottery_result("")
        
        assert all(isinstance(r, bool) for r in [result1, result2, result3, result4])


# ============================================================================
# Caching Tests
# ============================================================================


class TestCaching:
    """Test the sound caching mechanism."""

    def test_clear_cache_works(self):
        """_clear_sound_cache should empty both caches."""
        import lottery_sounds
        
        lottery_sounds._clear_sound_cache()
        
        assert len(lottery_sounds._win_sound_cache) == 0
        assert len(lottery_sounds._lose_sound_cache) == 0

    def test_preload_populates_cache(self):
        """preload_lottery_sounds should populate both caches."""
        import lottery_sounds
        
        if not lottery_sounds.is_sound_available():
            pytest.skip("Audio system not available")
        
        lottery_sounds._clear_sound_cache()
        count = lottery_sounds.preload_lottery_sounds()
        
        assert count == 40  # 20 win + 20 lose
        assert len(lottery_sounds._win_sound_cache) == 20
        assert len(lottery_sounds._lose_sound_cache) == 20

    def test_preload_returns_zero_when_already_cached(self):
        """Second preload should return 0 (already cached)."""
        import lottery_sounds
        
        if not lottery_sounds.is_sound_available():
            pytest.skip("Audio system not available")
        
        lottery_sounds._clear_sound_cache()
        count1 = lottery_sounds.preload_lottery_sounds()
        count2 = lottery_sounds.preload_lottery_sounds()
        
        assert count1 == 40
        assert count2 == 0

    def test_preload_returns_zero_when_audio_unavailable(self):
        """preload_lottery_sounds should return 0 when audio is unavailable."""
        import lottery_sounds
        
        original_available = lottery_sounds.AUDIO_AVAILABLE
        try:
            lottery_sounds.AUDIO_AVAILABLE = False
            lottery_sounds._clear_sound_cache()
            
            count = lottery_sounds.preload_lottery_sounds()
            assert count == 0
        finally:
            lottery_sounds.AUDIO_AVAILABLE = original_available


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_note_raises_key_error(self):
        """ToneSpec with invalid note should raise KeyError."""
        import lottery_sounds
        
        if not lottery_sounds.is_sound_available():
            pytest.skip("Audio system not available")
        
        bad_tone = lottery_sounds.ToneSpec('X99', 100, 0.5)
        
        with pytest.raises(KeyError) as exc_info:
            bad_tone.generate()
        
        # Error message should be helpful
        assert 'X99' in str(exc_info.value)
        assert 'Valid notes' in str(exc_info.value)

    def test_empty_chord_raises_value_error(self):
        """ChordSpec with empty tones should raise ValueError."""
        import lottery_sounds
        
        if not lottery_sounds.is_sound_available():
            pytest.skip("Audio system not available")
        
        empty_chord = lottery_sounds.ChordSpec(())
        
        with pytest.raises(ValueError) as exc_info:
            empty_chord.generate()
        
        assert 'at least one tone' in str(exc_info.value)

    def test_empty_melody_raises_value_error(self):
        """MelodyDefinition with empty elements should raise ValueError."""
        import lottery_sounds
        
        if not lottery_sounds.is_sound_available():
            pytest.skip("Audio system not available")
        
        empty_melody = lottery_sounds.MelodyDefinition(
            name="empty",
            description="Empty melody",
            elements=()
        )
        
        with pytest.raises(ValueError) as exc_info:
            empty_melody.compose()
        
        assert 'empty' in str(exc_info.value)

    def test_play_functions_never_raise_exceptions(self):
        """Play functions should never raise exceptions."""
        import lottery_sounds
        
        # These should never raise, even with various inputs
        try:
            lottery_sounds.play_win_sound()
            lottery_sounds.play_lose_sound()
            lottery_sounds.play_lottery_result(True)
            lottery_sounds.play_lottery_result(False)
        except Exception as e:
            pytest.fail(f"Play function raised exception: {e}")


# ============================================================================
# Dataclass Tests
# ============================================================================


class TestDataclasses:
    """Test the dataclass implementations."""

    def test_tone_spec_is_frozen(self):
        """ToneSpec should be immutable (frozen)."""
        import lottery_sounds
        
        tone = lottery_sounds.ToneSpec('C5', 100, 0.5)
        
        with pytest.raises(AttributeError):
            tone.note = 'D5'

    def test_chord_spec_is_frozen(self):
        """ChordSpec should be immutable (frozen)."""
        import lottery_sounds
        
        tone = lottery_sounds.ToneSpec('C5', 100, 0.5)
        chord = lottery_sounds.ChordSpec((tone,))
        
        with pytest.raises(AttributeError):
            chord.tones = ()

    def test_melody_definition_is_frozen(self):
        """MelodyDefinition should be immutable (frozen)."""
        import lottery_sounds
        
        tone = lottery_sounds.ToneSpec('C5', 100, 0.5)
        melody = lottery_sounds.MelodyDefinition(
            name="test",
            description="Test melody",
            elements=(tone,)
        )
        
        with pytest.raises(AttributeError):
            melody.name = "changed"

    def test_tone_spec_default_values(self):
        """ToneSpec should have sensible defaults."""
        import lottery_sounds
        
        tone = lottery_sounds.ToneSpec('C5', 100, 0.5)
        
        assert tone.waveform == lottery_sounds.WaveformType.SINE.value
        assert tone.attack == lottery_sounds.Envelope.ATTACK_QUICK
        assert tone.release == lottery_sounds.Envelope.RELEASE_NORMAL


# ============================================================================
# Sound Generation Tests (requires audio)
# ============================================================================


class TestSoundGeneration:
    """Test actual sound generation (requires audio system)."""

    def test_tone_generates_audio_data(self):
        """ToneSpec.generate() should produce audio data."""
        import lottery_sounds
        
        if not lottery_sounds.is_sound_available():
            pytest.skip("Audio system not available")
        
        tone = lottery_sounds.ToneSpec('C5', 100, 0.5)
        data = tone.generate()
        
        assert data is not None
        assert len(data) > 0

    def test_chord_generates_audio_data(self):
        """ChordSpec.generate() should produce audio data."""
        import lottery_sounds
        
        if not lottery_sounds.is_sound_available():
            pytest.skip("Audio system not available")
        
        chord = lottery_sounds.ChordSpec((
            lottery_sounds.ToneSpec('C5', 100, 0.5),
            lottery_sounds.ToneSpec('E5', 100, 0.4),
        ))
        data = chord.generate()
        
        assert data is not None
        assert len(data) > 0

    def test_melody_composes_audio_data(self):
        """MelodyDefinition.compose() should produce audio data."""
        import lottery_sounds
        
        if not lottery_sounds.is_sound_available():
            pytest.skip("Audio system not available")
        
        melody = lottery_sounds.WIN_MELODIES[0]
        data = melody.compose()
        
        assert data is not None
        assert len(data) > 0

    def test_all_win_melodies_compose(self):
        """All win melodies should compose without error."""
        import lottery_sounds
        
        if not lottery_sounds.is_sound_available():
            pytest.skip("Audio system not available")
        
        for melody in lottery_sounds.WIN_MELODIES:
            try:
                data = melody.compose()
                assert len(data) > 0, f"Melody '{melody.name}' produced empty audio"
            except Exception as e:
                pytest.fail(f"Melody '{melody.name}' failed to compose: {e}")

    def test_all_lose_melodies_compose(self):
        """All lose melodies should compose without error."""
        import lottery_sounds
        
        if not lottery_sounds.is_sound_available():
            pytest.skip("Audio system not available")
        
        for melody in lottery_sounds.LOSE_MELODIES:
            try:
                data = melody.compose()
                assert len(data) > 0, f"Melody '{melody.name}' produced empty audio"
            except Exception as e:
                pytest.fail(f"Melody '{melody.name}' failed to compose: {e}")


# ============================================================================
# Graceful Degradation Tests
# ============================================================================


class TestGracefulDegradation:
    """Test behavior when audio system is unavailable."""

    def test_play_win_sound_returns_false_when_unavailable(self):
        """play_win_sound should return False when audio unavailable."""
        import lottery_sounds
        
        original_available = lottery_sounds.AUDIO_AVAILABLE
        try:
            lottery_sounds.AUDIO_AVAILABLE = False
            
            result = lottery_sounds.play_win_sound()
            assert result is False
        finally:
            lottery_sounds.AUDIO_AVAILABLE = original_available

    def test_play_lose_sound_returns_false_when_unavailable(self):
        """play_lose_sound should return False when audio unavailable."""
        import lottery_sounds
        
        original_available = lottery_sounds.AUDIO_AVAILABLE
        try:
            lottery_sounds.AUDIO_AVAILABLE = False
            
            result = lottery_sounds.play_lose_sound()
            assert result is False
        finally:
            lottery_sounds.AUDIO_AVAILABLE = original_available

    def test_tone_generate_raises_when_unavailable(self):
        """ToneSpec.generate() should raise RuntimeError when unavailable."""
        import lottery_sounds
        
        original_available = lottery_sounds.AUDIO_AVAILABLE
        try:
            lottery_sounds.AUDIO_AVAILABLE = False
            
            tone = lottery_sounds.ToneSpec('C5', 100, 0.5)
            
            with pytest.raises(RuntimeError) as exc_info:
                tone.generate()
            
            assert 'not available' in str(exc_info.value)
        finally:
            lottery_sounds.AUDIO_AVAILABLE = original_available


# ============================================================================
# Consumer Compatibility Tests
# ============================================================================


class TestConsumerCompatibility:
    """Test that the module works with the consumer pattern in lottery_animation.py."""

    def test_lazy_import_pattern(self):
        """Module should work with lazy import pattern."""
        _lottery_sounds_module = None
        
        # Simulate lazy import
        if _lottery_sounds_module is None:
            import lottery_sounds
            _lottery_sounds_module = lottery_sounds
        
        # Should be able to call the expected function
        result = _lottery_sounds_module.play_lottery_result(True)
        assert isinstance(result, bool)

    def test_module_level_caching_pattern(self):
        """Module should support caching pattern used by consumers."""
        import lottery_sounds
        
        # Consumer pattern: check availability, then call
        if lottery_sounds.is_sound_available():
            result = lottery_sounds.play_lottery_result(True)
            assert isinstance(result, bool)
        else:
            # Should still not raise
            result = lottery_sounds.play_lottery_result(True)
            assert result is False


# ============================================================================
# Run tests if executed directly
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
