"""Contract tests for canonical emoji token usage in high-risk modules."""

from __future__ import annotations

from pathlib import Path

from emoji_tokens import (
    ACTIVITY_EMOJI,
    DAILY_LOGIN_REWARD_EMOJI,
    LEVEL_TITLE_EMOJI,
    MINI_STAT_EMOJI,
    SLEEP_CHRONOTYPE_EMOJI,
    SLEEP_DISRUPTION_EMOJI,
    SLEEP_QUALITY_EMOJI,
    TAB_EMOJI,
)


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _contains_subscript(src: str, mapping: str, key: str) -> bool:
    return f'{mapping}["{key}"]' in src or f"{mapping}['{key}']" in src


def test_focus_blocker_uses_tab_and_mini_stat_token_contract():
    src = _read("focus_blocker_qt.py")

    for key in TAB_EMOJI:
        assert _contains_subscript(src, "TAB_EMOJI", key), key

    for key in MINI_STAT_EMOJI:
        assert _contains_subscript(src, "MINI_STAT_EMOJI", key), key

    assert _contains_subscript(src, "SYMBOL_EMOJI", "star")
    assert _contains_subscript(src, "SYMBOL_EMOJI", "coffee")


def test_gamification_uses_canonical_emoji_token_groups_contract():
    src = _read("gamification.py")

    groups: dict[str, tuple[str, ...]] = {
        "ACTIVITY_EMOJI": tuple(ACTIVITY_EMOJI.keys()),
        "SLEEP_CHRONOTYPE_EMOJI": tuple(SLEEP_CHRONOTYPE_EMOJI.keys()),
        "SLEEP_QUALITY_EMOJI": tuple(SLEEP_QUALITY_EMOJI.keys()),
        "SLEEP_DISRUPTION_EMOJI": tuple(SLEEP_DISRUPTION_EMOJI.keys()),
        "DAILY_LOGIN_REWARD_EMOJI": tuple(DAILY_LOGIN_REWARD_EMOJI.keys()),
    }

    for mapping, keys in groups.items():
        for key in keys:
            assert _contains_subscript(src, mapping, key), f"{mapping}.{key}"

    for level in LEVEL_TITLE_EMOJI:
        assert f"LEVEL_TITLE_EMOJI[{level}]" in src, level

    assert _contains_subscript(src, "SYMBOL_EMOJI", "star")
    assert _contains_subscript(src, "SYMBOL_EMOJI", "coffee")
