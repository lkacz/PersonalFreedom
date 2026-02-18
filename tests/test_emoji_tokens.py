"""Tests for canonical emoji token definitions."""

from emoji_tokens import (
    ACTIVITY_EMOJI,
    DAILY_LOGIN_REWARD_EMOJI,
    LEVEL_TITLE_EMOJI,
    MINI_STAT_EMOJI,
    SLEEP_CHRONOTYPE_EMOJI,
    SLEEP_DISRUPTION_EMOJI,
    SLEEP_QUALITY_EMOJI,
    SYMBOL_EMOJI,
    TAB_EMOJI,
    with_label,
)


def test_tab_emoji_tokens_are_non_empty():
    for key, value in TAB_EMOJI.items():
        assert isinstance(key, str) and key
        assert isinstance(value, str) and value


def test_mini_stat_emoji_tokens_are_non_empty():
    for key, value in MINI_STAT_EMOJI.items():
        assert isinstance(key, str) and key
        assert isinstance(value, str) and value


def test_gamification_emoji_tokens_are_non_empty():
    token_groups = (
        ACTIVITY_EMOJI,
        SLEEP_CHRONOTYPE_EMOJI,
        SLEEP_QUALITY_EMOJI,
        SLEEP_DISRUPTION_EMOJI,
        DAILY_LOGIN_REWARD_EMOJI,
        LEVEL_TITLE_EMOJI,
        SYMBOL_EMOJI,
    )
    for group in token_groups:
        for key, value in group.items():
            assert key
            assert isinstance(value, str) and value


def test_common_symbol_tokens_match_expected_codepoints():
    assert SYMBOL_EMOJI["coffee"] == "\u2615"
    assert SYMBOL_EMOJI["star"] == "\u2B50"


def test_with_label_format():
    assert with_label("\U0001F3AF", "Focus") == "\U0001F3AF Focus"
