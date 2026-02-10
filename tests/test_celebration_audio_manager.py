from __future__ import annotations

from typing import Iterator

import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtMultimedia import QAudio

from entitidex.celebration_audio import CelebrationAudioManager


class _FakeSink:
    def __init__(self, state: QAudio.State = QAudio.State.StoppedState) -> None:
        self._state = state
        self.stop_calls = 0

    def state(self) -> QAudio.State:
        return self._state

    def stop(self) -> None:
        self.stop_calls += 1
        self._state = QAudio.State.StoppedState


@pytest.fixture
def fresh_audio_manager(qapp):  # noqa: ANN001
    existing = CelebrationAudioManager._instance
    if existing is not None:
        try:
            existing.stop()
        except Exception:
            pass
    CelebrationAudioManager._instance = None

    manager = CelebrationAudioManager.get_instance()
    yield manager

    try:
        manager.stop()
    except Exception:
        pass
    CelebrationAudioManager._instance = None


def _fixed_times(values: list[int]) -> Iterator[int]:
    for value in values:
        yield value


def test_sanitize_volume_clamps_and_falls_back() -> None:
    sanitize = CelebrationAudioManager._sanitize_volume
    assert sanitize(-1.0, 0.5) == 0.0
    assert sanitize(2.0, 0.5) == 1.0
    assert sanitize(float("nan"), 0.5) == 0.5
    assert sanitize(float("inf"), 0.5) == 0.5
    assert sanitize("bad", 0.5) == 0.5


def test_play_buffer_internal_rate_limits_sound_effects(
    fresh_audio_manager: CelebrationAudioManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = fresh_audio_manager
    manager._sink = _FakeSink()

    start_calls = {"count": 0}

    def _fake_start_pending() -> bool:
        start_calls["count"] += 1
        return True

    times = _fixed_times([1000, 1100])
    monkeypatch.setattr(manager, "_now_ms", lambda: next(times))
    monkeypatch.setattr(manager, "_refresh_audio_device_if_needed", lambda: None)
    monkeypatch.setattr(manager, "_ensure_sink_ready", lambda: True)
    monkeypatch.setattr(manager, "_start_pending_playback", _fake_start_pending)
    monkeypatch.setattr(manager, "_is_audio_temporarily_disabled", lambda: False)

    pcm = QByteArray(b"\x00\x00")
    assert manager._play_buffer_internal(pcm, is_voice=False) is True
    assert manager._play_buffer_internal(pcm, is_voice=False) is False
    assert start_calls["count"] == 1


def test_play_buffer_internal_voice_bypasses_rate_limit(
    fresh_audio_manager: CelebrationAudioManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = fresh_audio_manager
    manager._sink = _FakeSink()

    start_calls = {"count": 0}

    def _fake_start_pending() -> bool:
        start_calls["count"] += 1
        return True

    times = _fixed_times([2000, 2050])
    monkeypatch.setattr(manager, "_now_ms", lambda: next(times))
    monkeypatch.setattr(manager, "_refresh_audio_device_if_needed", lambda: None)
    monkeypatch.setattr(manager, "_ensure_sink_ready", lambda: True)
    monkeypatch.setattr(manager, "_start_pending_playback", _fake_start_pending)
    monkeypatch.setattr(manager, "_is_audio_temporarily_disabled", lambda: False)

    pcm = QByteArray(b"\x00\x00")
    assert manager._play_buffer_internal(pcm, is_voice=False) is True
    assert manager._play_buffer_internal(pcm, is_voice=True) is True
    assert start_calls["count"] == 2


def test_play_buffer_internal_active_sink_stops_and_queues(
    fresh_audio_manager: CelebrationAudioManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = fresh_audio_manager
    fake_sink = _FakeSink(QAudio.State.ActiveState)
    manager._sink = fake_sink

    monkeypatch.setattr(manager, "_now_ms", lambda: 5000)
    monkeypatch.setattr(manager, "_refresh_audio_device_if_needed", lambda: None)
    monkeypatch.setattr(manager, "_ensure_sink_ready", lambda: True)
    monkeypatch.setattr(manager, "_is_audio_temporarily_disabled", lambda: False)
    monkeypatch.setattr(
        manager,
        "_start_pending_playback",
        lambda: pytest.fail("_start_pending_playback should not run while sink is ActiveState"),
    )

    pcm = QByteArray(b"\x00\x00")
    assert manager._play_buffer_internal(pcm, is_voice=False) is True
    assert fake_sink.stop_calls == 1
    assert manager._pending_data is not None


def test_audio_cooldown_resets_after_expiry(
    fresh_audio_manager: CelebrationAudioManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = fresh_audio_manager
    manager._audio_disabled_until_ms = 1500
    manager._consecutive_failures = 3

    monkeypatch.setattr(manager, "_now_ms", lambda: 1200)
    assert manager._is_audio_temporarily_disabled() is True

    monkeypatch.setattr(manager, "_now_ms", lambda: 1501)
    assert manager._is_audio_temporarily_disabled() is False
    assert manager._audio_disabled_until_ms == 0
    assert manager._consecutive_failures == 0
