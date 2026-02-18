"""Canonical emoji tokens for user-facing UI labels.

Store tokens as Unicode escape sequences to reduce accidental source-encoding
corruption during edits across different Windows editor/codepage setups.
"""

from __future__ import annotations


TAB_EMOJI = {
    "focus": "\U0001F3AF",
    "story": "\U0001F4DC",
    "eyes": "\U0001F441\ufe0f",
    "water": "\U0001F4A7",
    "activity": "\U0001F3C3",
    "weight": "\u2696",
    "sleep": "\U0001F634",
    "entitidex": "\U0001F4D6",
    "city": "\U0001F3F0",
    "productivity": "\U0001F4CA",
    "schedule": "\U0001F4C5",
    "categories": "\U0001F4C1",
    "sites": "\U0001F310",
    "ai": "\U0001F9E0",
    "settings": "\u2699",
    "dev": "\U0001F6E0\ufe0f",
}


MINI_STAT_EMOJI = {
    "today": "\U0001F4CA",
    "streak": "\U0001F525",
    "sessions": "\u2705",
}


ACTIVITY_EMOJI = {
    "walking": "\U0001F6B6",
    "jogging": "\U0001F3C3",
    "running": "\U0001F3C3\u200d\u2642\ufe0f",
    "cycling": "\U0001F6B4",
    "swimming": "\U0001F3CA",
    "hiking": "\U0001F97E",
    "strength": "\U0001F3CB\ufe0f",
    "yoga": "\U0001F9D8",
    "dance": "\U0001F483",
    "sports": "\u26BD",
    "hiit": "\U0001F525",
    "climbing": "\U0001F9D7",
    "martial_arts": "\U0001F94B",
    "stretching": "\U0001F938",
    "other": "\U0001F3AF",
}


SLEEP_CHRONOTYPE_EMOJI = {
    "early_bird": "\U0001F305",
    "moderate": "\u23F0",
    "night_owl": "\U0001F989",
}


SLEEP_QUALITY_EMOJI = {
    "excellent": "\U0001F634\U0001F4A4",
    "good": "\U0001F60A",
    "fair": "\U0001F610",
    "poor": "\U0001F613",
    "terrible": "\U0001F635",
}


SLEEP_DISRUPTION_EMOJI = {
    "none": "\u2705",
    "woke_once": "1\ufe0f\u20e3",
    "woke_multiple": "\U0001F504",
    "nightmares": "\U0001F630",
    "noise": "\U0001F50A",
    "stress": "\U0001F61F",
    "late_caffeine": "\u2615",
    "late_screen": "\U0001F4F1",
    "alcohol": "\U0001F377",
}


DAILY_LOGIN_REWARD_EMOJI = {
    "xp": "\u2728",
    "item": "\U0001F4E6",
    "streak_freeze": "\U0001F9CA",
    "multiplier": "\u26A1",
    "mystery_box_silver": "\U0001F381",
    "mystery_box_gold": "\U0001F381",
    "mystery_box_diamond": "\U0001F48E",
    "mystery_box_legendary": "\U0001F31F",
}


LEVEL_TITLE_EMOJI = {
    1: "\U0001F331",
    5: "\U0001F4DA",
    10: "\U0001F3AF",
    15: "\u2B50",
    20: "\U0001F4AA",
    25: "\U0001F3C6",
    30: "\U0001F451",
    40: "\U0001F52E",
    50: "\u26A1",
    75: "\U0001F31F",
    100: "\u2728",
}


SYMBOL_EMOJI = {
    "coffee": "\u2615",
    "star": "\u2B50",
    "divider_heavy": "\u2501",
}


def with_label(emoji: str, label: str) -> str:
    """Format a compact 'emoji + label' UI string."""
    return f"{emoji} {label}"
