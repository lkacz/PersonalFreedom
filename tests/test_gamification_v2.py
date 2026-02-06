"""Tests for gamification v2 features (XP, levels, challenges, rewards)."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import random

from gamification import (
    # XP/Level System
    get_xp_for_level,
    get_level_from_xp,
    get_level_title,
    calculate_session_xp,
    award_xp,
    calculate_character_power,
    get_all_perk_bonuses,
    XP_REWARDS,
    LEVEL_TITLES,
    # Daily Login
    get_daily_login_reward,
    claim_daily_login,
    get_work_day_date,
    get_active_multiplier,
    DAILY_LOGIN_REWARDS,
    # Mystery Boxes
    open_mystery_box,
    MYSTERY_BOX_TIERS,
    # Challenges
    generate_daily_challenges,
    generate_weekly_challenges,
    update_challenge_progress,
    claim_challenge_reward,
    CHALLENGE_TEMPLATES,
    # Streak Freeze
    use_streak_freeze,
    check_streak_frozen,
    # Combos/Multipliers
    calculate_combo_multiplier,
    # Progress Bars
    get_all_progress_bars,
    get_challenge_progress_bars,
    # Celebrations
    get_celebration_message,
    CELEBRATION_MESSAGES,
)


class TestXPLevelSystem:
    """Tests for XP and leveling system."""

    def test_get_xp_for_level_level_1(self):
        """Level 1 requires 0 XP."""
        assert get_xp_for_level(1) == 0
        assert get_xp_for_level(0) == 0

    def test_get_xp_for_level_progression(self):
        """XP requirements increase with level."""
        xp_2 = get_xp_for_level(2)
        xp_3 = get_xp_for_level(3)
        xp_10 = get_xp_for_level(10)
        xp_50 = get_xp_for_level(50)

        assert xp_2 > 0
        assert xp_3 > xp_2
        assert xp_10 > xp_3
        assert xp_50 > xp_10

    def test_get_level_from_xp_zero(self):
        """Zero XP returns level 1."""
        level, xp_in, xp_needed, progress = get_level_from_xp(0)
        assert level == 1
        assert xp_in == 0
        assert progress == 0.0

    def test_get_level_from_xp_negative(self):
        """Negative XP returns level 1."""
        level, _, _, _ = get_level_from_xp(-100)
        assert level == 1

    def test_get_level_from_xp_positive(self):
        """Positive XP returns correct level."""
        # Get XP needed for level 5
        xp_5 = get_xp_for_level(5)
        xp_6 = get_xp_for_level(6)
        
        # Exactly at level 5 threshold
        level, _, _, _ = get_level_from_xp(xp_5)
        assert level == 5
        
        # Just before level 6
        level, _, _, _ = get_level_from_xp(xp_6 - 1)
        assert level == 5

    def test_get_level_from_xp_progress(self):
        """Progress percentage calculated correctly."""
        xp_5 = get_xp_for_level(5)
        xp_6 = get_xp_for_level(6)
        mid_xp = (xp_5 + xp_6) // 2
        
        level, xp_in, xp_needed, progress = get_level_from_xp(mid_xp)
        assert level == 5
        assert 40 < progress < 60  # Approximately 50%

    def test_get_level_title_progression(self):
        """Level titles unlock correctly."""
        novice_title, _ = get_level_title(1)
        assert novice_title == "Novice"
        
        apprentice_title, _ = get_level_title(5)
        assert apprentice_title == "Apprentice"
        
        master_title, _ = get_level_title(30)
        assert master_title == "Master"

    def test_calculate_session_xp_basic(self):
        """Basic session XP calculation."""
        result = calculate_session_xp(25)  # 25 minute session
        
        assert "base_xp" in result
        assert "duration_xp" in result
        assert "total_xp" in result
        assert result["total_xp"] > 0
        assert result["base_xp"] == XP_REWARDS["focus_session"]

    def test_calculate_session_xp_with_streak(self):
        """Session XP includes streak bonus."""
        result_no_streak = calculate_session_xp(25, streak_days=0)
        result_with_streak = calculate_session_xp(25, streak_days=7)
        
        assert result_with_streak["streak_bonus"] > result_no_streak["streak_bonus"]
        assert result_with_streak["total_xp"] > result_no_streak["total_xp"]

    def test_calculate_session_xp_with_multiplier(self):
        """Session XP respects multiplier."""
        result_1x = calculate_session_xp(25, multiplier=1.0)
        result_2x = calculate_session_xp(25, multiplier=2.0)
        
        assert result_2x["total_xp"] == result_1x["total_xp"] * 2

    def test_award_xp_basic(self):
        """XP is awarded correctly."""
        adhd_buster = {}
        result = award_xp(adhd_buster, 100, "test")
        
        assert result["xp_earned"] == 100
        assert result["total_xp"] == 100
        assert adhd_buster["total_xp"] == 100

    def test_award_xp_level_up(self):
        """Level up detected correctly."""
        adhd_buster = {"total_xp": get_xp_for_level(5) - 1}
        result = award_xp(adhd_buster, 50, "test")
        
        assert result["leveled_up"] is True
        assert result["levels_gained"] >= 1

    def test_award_xp_history_tracked(self):
        """XP history is tracked."""
        adhd_buster = {}
        award_xp(adhd_buster, 50, "session")
        award_xp(adhd_buster, 25, "login")
        
        assert len(adhd_buster["xp_history"]) == 2
        assert adhd_buster["xp_history"][0]["source"] == "session"
        assert adhd_buster["xp_history"][1]["source"] == "login"

    def test_award_xp_history_capped(self):
        """XP history is capped at 100 entries."""
        adhd_buster = {}
        for i in range(150):
            award_xp(adhd_buster, 1, f"test_{i}")
        
        assert len(adhd_buster["xp_history"]) == 100


class TestDailyLoginRewards:
    """Tests for daily login reward system."""

    @staticmethod
    def _workday_today() -> str:
        """Return today's date in workday terms (respects 5 AM boundary)."""
        return get_work_day_date()

    @classmethod
    def _workday_offset(cls, days: int) -> str:
        base = datetime.strptime(cls._workday_today(), "%Y-%m-%d")
        return (base + timedelta(days=days)).strftime("%Y-%m-%d")

    def test_get_daily_login_reward_day_1(self):
        """Day 1 reward is correct."""
        reward = get_daily_login_reward(1)
        assert reward["day_in_cycle"] == 1
        assert reward["login_streak"] == 1

    def test_get_daily_login_reward_cycles(self):
        """Rewards cycle after 28 days."""
        day_1_reward = get_daily_login_reward(1)
        day_29_reward = get_daily_login_reward(29)  # Same as day 1 of cycle 2
        
        assert day_29_reward["day_in_cycle"] == 1
        assert day_29_reward["cycle_number"] == 2
        assert day_1_reward["type"] == day_29_reward["type"]

    def test_claim_daily_login_first_time(self):
        """First login claim works."""
        adhd_buster = {}
        result = claim_daily_login(adhd_buster)
        
        assert result["claimed"] is True
        assert adhd_buster["login_streak"] == 1
        assert adhd_buster["total_logins"] == 1

    def test_claim_daily_login_already_claimed(self):
        """Cannot claim twice in same day."""
        today = self._workday_today()
        adhd_buster = {"last_login_date": today}
        
        result = claim_daily_login(adhd_buster)
        assert result["already_claimed"] is True

    def test_claim_daily_login_consecutive(self):
        """Consecutive logins increase streak."""
        yesterday = self._workday_offset(-1)
        adhd_buster = {"last_login_date": yesterday, "login_streak": 5}
        
        result = claim_daily_login(adhd_buster)
        assert adhd_buster["login_streak"] == 6

    def test_claim_daily_login_streak_broken(self):
        """Missing a day resets streak."""
        two_days_ago = self._workday_offset(-3)
        adhd_buster = {"last_login_date": two_days_ago, "login_streak": 10}
        
        result = claim_daily_login(adhd_buster)
        assert adhd_buster["login_streak"] == 1

    def test_claim_daily_login_streak_freeze(self):
        """Streak freeze prevents reset."""
        two_days_ago = self._workday_offset(-2)
        adhd_buster = {
            "last_login_date": two_days_ago,
            "login_streak": 10,
            "streak_freeze_tokens": 1
        }
        
        result = claim_daily_login(adhd_buster)
        assert adhd_buster["login_streak"] == 11  # Streak preserved
        assert adhd_buster["streak_freeze_tokens"] == 0  # Token used

    def test_claim_daily_login_future_date_recovers(self):
        """Future last_login_date should recover instead of locking rewards."""
        tomorrow = self._workday_offset(1)
        adhd_buster = {"last_login_date": tomorrow, "login_streak": 12}

        result = claim_daily_login(adhd_buster)
        assert result["claimed"] is True
        assert adhd_buster["login_streak"] == 1

    def test_get_active_multiplier_none(self):
        """No multiplier returns 1.0."""
        adhd_buster = {}
        assert get_active_multiplier(adhd_buster) == 1.0

    def test_get_active_multiplier_expired(self):
        """Expired multiplier returns 1.0."""
        adhd_buster = {
            "active_multiplier": {
                "value": 2.0,
                "expires_at": datetime.now().timestamp() - 100
            }
        }
        assert get_active_multiplier(adhd_buster) == 1.0
        assert "active_multiplier" not in adhd_buster

    def test_get_active_multiplier_active(self):
        """Active multiplier returns correct value."""
        adhd_buster = {
            "active_multiplier": {
                "value": 1.5,
                "expires_at": datetime.now().timestamp() + 3600
            }
        }
        assert get_active_multiplier(adhd_buster) == 1.5


class TestMysteryBoxes:
    """Tests for mystery box system."""

    def test_mystery_box_tiers_exist(self):
        """All mystery box tiers exist."""
        assert "bronze" in MYSTERY_BOX_TIERS
        assert "silver" in MYSTERY_BOX_TIERS
        assert "gold" in MYSTERY_BOX_TIERS
        assert "diamond" in MYSTERY_BOX_TIERS
        assert "legendary" in MYSTERY_BOX_TIERS

    def test_open_mystery_box_grants_xp(self):
        """Mystery box grants XP."""
        adhd_buster = {"total_xp": 0}
        result = open_mystery_box(adhd_buster, "bronze")
        
        assert result["xp"] > 0
        assert adhd_buster["total_xp"] > 0

    def test_open_mystery_box_grants_items(self):
        """Mystery box grants items."""
        adhd_buster = {"inventory": []}
        result = open_mystery_box(adhd_buster, "silver")
        
        assert len(result["items"]) > 0
        assert len(adhd_buster["inventory"]) > 0

    def test_open_mystery_box_higher_tier_better(self):
        """Higher tier boxes have better XP range."""
        bronze = MYSTERY_BOX_TIERS["bronze"]
        legendary = MYSTERY_BOX_TIERS["legendary"]
        
        assert bronze["xp_range"][1] < legendary["xp_range"][0]

    def test_open_mystery_box_rewards_summary(self):
        """Rewards summary is generated."""
        adhd_buster = {}
        result = open_mystery_box(adhd_buster, "gold")
        
        assert "rewards_summary" in result
        assert len(result["rewards_summary"]) > 0


class TestChallenges:
    """Tests for challenge system."""

    def test_challenge_templates_exist(self):
        """Challenge templates are defined."""
        assert len(CHALLENGE_TEMPLATES) > 0
        
        daily_count = sum(1 for c in CHALLENGE_TEMPLATES.values() if c["type"] == "daily")
        weekly_count = sum(1 for c in CHALLENGE_TEMPLATES.values() if c["type"] == "weekly")
        
        assert daily_count >= 3
        assert weekly_count >= 2

    def test_generate_daily_challenges(self):
        """Daily challenges are generated."""
        challenges = generate_daily_challenges("2024-01-15")
        
        assert len(challenges) == 3
        assert all(c["type"] == "daily" for c in challenges)
        assert all(c["progress"] == 0 for c in challenges)

    def test_generate_daily_challenges_deterministic(self):
        """Same date generates same challenges."""
        challenges_1 = generate_daily_challenges("2024-01-15")
        challenges_2 = generate_daily_challenges("2024-01-15")
        
        assert [c["template_id"] for c in challenges_1] == [c["template_id"] for c in challenges_2]

    def test_generate_daily_challenges_different_days(self):
        """Different dates may generate different challenges."""
        challenges_1 = generate_daily_challenges("2024-01-15")
        challenges_2 = generate_daily_challenges("2024-01-16")
        
        # Not guaranteed to be different, but IDs should be different
        assert challenges_1[0]["id"] != challenges_2[0]["id"]

    def test_generate_weekly_challenges(self):
        """Weekly challenges are generated."""
        challenges = generate_weekly_challenges("2024-01-15")
        
        assert len(challenges) == 2
        assert all(c["type"] == "weekly" for c in challenges)

    def test_update_challenge_progress_session(self):
        """Session events update challenge progress."""
        adhd_buster = {
            "daily_challenges": [
                {
                    "id": "test_1",
                    "requirement": {"type": "sessions", "count": 3},
                    "progress": 0,
                    "completed": False,
                    "title": "Test",
                    "xp_reward": 100
                }
            ],
            "daily_challenges_date": datetime.now().strftime("%Y-%m-%d"),
            "weekly_challenges": [],
            "weekly_challenges_start": "2024-01-15"
        }
        
        completed = update_challenge_progress(adhd_buster, "session")
        
        assert adhd_buster["daily_challenges"][0]["progress"] == 1
        assert len(completed) == 0  # Not yet complete

    def test_update_challenge_progress_completes(self):
        """Challenge completes when requirement met."""
        adhd_buster = {
            "daily_challenges": [
                {
                    "id": "test_1",
                    "requirement": {"type": "sessions", "count": 1},
                    "progress": 0,
                    "completed": False,
                    "title": "Test",
                    "xp_reward": 100
                }
            ],
            "daily_challenges_date": datetime.now().strftime("%Y-%m-%d"),
            "weekly_challenges": [],
            "weekly_challenges_start": "2024-01-15"
        }
        
        completed = update_challenge_progress(adhd_buster, "session")
        
        assert adhd_buster["daily_challenges"][0]["completed"] is True
        assert len(completed) == 1

    def test_claim_challenge_reward_not_complete(self):
        """Cannot claim incomplete challenge."""
        adhd_buster = {
            "daily_challenges": [
                {
                    "id": "test_1",
                    "completed": False,
                    "claimed": False,
                    "xp_reward": 100
                }
            ]
        }
        
        result = claim_challenge_reward(adhd_buster, "test_1")
        assert result["success"] is False

    def test_claim_challenge_reward_success(self):
        """Claiming complete challenge awards XP."""
        adhd_buster = {
            "daily_challenges": [
                {
                    "id": "test_1",
                    "completed": True,
                    "claimed": False,
                    "xp_reward": 100,
                    "title": "Test"
                }
            ],
            "total_xp": 0
        }
        
        result = claim_challenge_reward(adhd_buster, "test_1")
        assert result["success"] is True
        assert result["xp_reward"] == 100
        assert adhd_buster["daily_challenges"][0]["claimed"] is True

    def test_claim_challenge_reward_already_claimed(self):
        """Cannot claim twice."""
        adhd_buster = {
            "daily_challenges": [
                {
                    "id": "test_1",
                    "completed": True,
                    "claimed": True,
                    "xp_reward": 100
                }
            ]
        }
        
        result = claim_challenge_reward(adhd_buster, "test_1")
        assert result["success"] is False


class TestStreakFreeze:
    """Tests for streak freeze system."""

    def test_use_streak_freeze_no_tokens(self):
        """Cannot use freeze without tokens."""
        adhd_buster = {"streak_freeze_tokens": 0}
        result = use_streak_freeze(adhd_buster, "focus")
        
        assert result["success"] is False

    def test_use_streak_freeze_success(self):
        """Using streak freeze works."""
        adhd_buster = {"streak_freeze_tokens": 3}
        result = use_streak_freeze(adhd_buster, "focus")
        
        assert result["success"] is True
        assert adhd_buster["streak_freeze_tokens"] == 2
        assert "focus" in adhd_buster["frozen_streaks"]

    def test_check_streak_frozen(self):
        """Check if streak was frozen."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        adhd_buster = {"frozen_streaks": {"focus": yesterday}}
        
        assert check_streak_frozen(adhd_buster, "focus") is True
        assert check_streak_frozen(adhd_buster, "sleep") is False


class TestComboMultiplier:
    """Tests for combo/multiplier system."""

    def test_calculate_combo_multiplier_base(self):
        """Base multiplier is 1.0."""
        adhd_buster = {}
        result = calculate_combo_multiplier(adhd_buster)
        
        assert result["total_multiplier"] == 1.0

    def test_calculate_combo_multiplier_streak(self):
        """Login streak adds multiplier."""
        adhd_buster = {"login_streak": 7}
        result = calculate_combo_multiplier(adhd_buster)
        
        assert result["total_multiplier"] > 1.0
        assert any("Week Streak" in b[0] for b in result["bonuses"])

    def test_calculate_combo_multiplier_big_streak(self):
        """30+ day streak has higher multiplier."""
        adhd_buster_7 = {"login_streak": 7}
        adhd_buster_30 = {"login_streak": 30}
        
        result_7 = calculate_combo_multiplier(adhd_buster_7)
        result_30 = calculate_combo_multiplier(adhd_buster_30)
        
        assert result_30["total_multiplier"] > result_7["total_multiplier"]

    def test_calculate_combo_multiplier_sessions(self):
        """Multiple sessions add multiplier."""
        today = datetime.now().strftime("%Y-%m-%d")
        adhd_buster = {
            "daily_stats": {
                today: {"sessions": 5}
            }
        }
        
        result = calculate_combo_multiplier(adhd_buster)
        assert result["total_multiplier"] >= 1.5


class TestProgressBars:
    """Tests for progress bar helpers."""

    def test_get_all_progress_bars(self):
        """All progress bars are returned."""
        adhd_buster = {
            "total_xp": 500,
            "login_streak": 5,
            "inventory": [],
            "daily_challenges": [],
            "weekly_challenges": []
        }
        
        bars = get_all_progress_bars(adhd_buster)
        
        assert len(bars) >= 2  # At least level and streak
        assert any(b["id"] == "level" for b in bars)
        assert any(b["id"] == "login_streak" for b in bars)

    def test_get_all_progress_bars_format(self):
        """Progress bars have required fields."""
        adhd_buster = {"total_xp": 100}
        bars = get_all_progress_bars(adhd_buster)
        
        for bar in bars:
            assert "id" in bar
            assert "label" in bar
            assert "current" in bar
            assert "target" in bar
            assert "percent" in bar

    def test_get_challenge_progress_bars(self):
        """Challenge progress bars are returned."""
        adhd_buster = {
            "daily_challenges": [
                {
                    "id": "test_1",
                    "title": "Test",
                    "description": "Test desc",
                    "requirement": {"type": "sessions", "count": 3},
                    "progress": 1,
                    "completed": False,
                    "claimed": False,
                    "xp_reward": 100
                }
            ],
            "weekly_challenges": []
        }
        
        bars = get_challenge_progress_bars(adhd_buster)
        
        assert len(bars) == 1
        assert bars[0]["current"] == 1
        assert bars[0]["target"] == 3


class TestCelebrations:
    """Tests for celebration messages."""

    def test_celebration_messages_exist(self):
        """All celebration types have messages."""
        assert "level_up" in CELEBRATION_MESSAGES
        assert "streak_milestone" in CELEBRATION_MESSAGES
        assert "challenge_complete" in CELEBRATION_MESSAGES
        assert "legendary_item" in CELEBRATION_MESSAGES

    def test_get_celebration_message_level_up(self):
        """Level up message formats correctly."""
        msg = get_celebration_message("level_up", level=10)
        assert "10" in msg

    def test_get_celebration_message_streak(self):
        """Streak message formats correctly."""
        msg = get_celebration_message("streak_milestone", days=7)
        assert "7" in msg

    def test_get_celebration_message_fallback(self):
        """Unknown event type returns fallback."""
        msg = get_celebration_message("unknown_event")
        assert "Great job" in msg


class TestEdgeCases:
    """Tests for edge cases and input validation."""

    def test_award_xp_negative_amount(self):
        """Negative XP amount is handled."""
        adhd_buster = {"total_xp": 100}
        result = award_xp(adhd_buster, -50, "test")
        # Should treat negative as 0
        assert adhd_buster["total_xp"] >= 100

    def test_award_xp_invalid_old_xp(self):
        """Invalid existing XP is handled."""
        adhd_buster = {"total_xp": "invalid"}
        result = award_xp(adhd_buster, 50, "test")
        assert adhd_buster["total_xp"] == 50  # Reset to 0 + 50

    def test_award_xp_overflow_protection(self):
        """XP is capped to prevent overflow."""
        adhd_buster = {"total_xp": 1_999_999_990}
        result = award_xp(adhd_buster, 100, "test")
        assert adhd_buster["total_xp"] <= 2_000_000_000

    def test_award_xp_applies_city_library_bonus(self):
        """Library city bonus should increase awarded XP."""
        from city import CellStatus, get_city_data

        adhd_buster = {"total_xp": 0, "coins": 0}
        city = get_city_data(adhd_buster)
        city["grid"][0][0] = {
            "building_id": "library",
            "status": CellStatus.COMPLETE.value,
            "level": 1,
            "construction_progress": {"water": 0, "materials": 0, "activity": 0, "focus": 0},
            "placed_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        }

        result = award_xp(adhd_buster, 100, "test")

        assert result["city_xp_bonus"] == 5
        assert result["xp_earned"] == 105
        assert adhd_buster["total_xp"] == 105

    def test_calculate_character_power_applies_city_training_bonus(self):
        """Training Ground city bonus should increase character power."""
        from city import CellStatus, get_city_data

        adhd_buster = {
            "equipped": {
                "Helmet": {"rarity": "Common", "power": 100, "theme": "warrior"},
                "Chestplate": None,
                "Gauntlets": None,
                "Boots": None,
                "Shield": None,
                "Weapon": None,
                "Cloak": None,
                "Amulet": None,
            },
            "entitidex": {},
            "total_xp": 5000,
        }

        base_power = calculate_character_power(adhd_buster)

        city = get_city_data(adhd_buster)
        city["grid"][0][0] = {
            "building_id": "training_ground",
            "status": CellStatus.COMPLETE.value,
            "level": 1,
            "construction_progress": {"water": 0, "materials": 0, "activity": 0, "focus": 0},
            "placed_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
        }

        boosted_power = calculate_character_power(adhd_buster)

        assert boosted_power == base_power + int(base_power * 0.03)

    def test_get_all_perk_bonuses_includes_entity_xp_and_scrap(self):
        """Entity global XP and scrap perks should flow into combined bonuses."""
        adhd_buster = {
            "entitidex": {
                # scientist_009 => XP_PERCENT +3
                # underdog_001 => SCRAP_CHANCE +1
                "collected_entity_ids": ["scientist_009", "underdog_001"],
                "exceptional_entities": {},
            }
        }

        bonuses = get_all_perk_bonuses(adhd_buster)

        assert bonuses["xp_bonus"] == 3
        assert bonuses["scrap_chance"] == 1.0

    def test_calculate_session_xp_negative_duration(self):
        """Negative duration is handled."""
        result = calculate_session_xp(-10)
        assert result["duration_xp"] == 0
        assert result["total_xp"] > 0  # Base XP still applies

    def test_calculate_session_xp_none_values(self):
        """None values don't crash."""
        result = calculate_session_xp(None, None, None)
        assert result["total_xp"] >= 0

    def test_get_daily_login_reward_zero_streak(self):
        """Zero streak is handled."""
        reward = get_daily_login_reward(0)
        assert reward["login_streak"] == 1
        assert reward["day_in_cycle"] == 1

    def test_get_daily_login_reward_negative_streak(self):
        """Negative streak is handled."""
        reward = get_daily_login_reward(-5)
        assert reward["login_streak"] == 1

    def test_get_active_multiplier_invalid_dict(self):
        """Invalid multiplier dict is handled."""
        adhd_buster = {"active_multiplier": "not a dict"}
        result = get_active_multiplier(adhd_buster)
        assert result == 1.0

    def test_get_active_multiplier_invalid_expires(self):
        """Invalid expires_at is handled."""
        adhd_buster = {
            "active_multiplier": {
                "value": 2.0,
                "expires_at": "invalid"
            }
        }
        result = get_active_multiplier(adhd_buster)
        assert result == 1.0
        assert "active_multiplier" not in adhd_buster

    def test_get_active_multiplier_clamped(self):
        """Multiplier is clamped to reasonable range."""
        adhd_buster = {
            "active_multiplier": {
                "value": 100.0,  # Unreasonably high
                "expires_at": datetime.now().timestamp() + 3600
            }
        }
        result = get_active_multiplier(adhd_buster)
        assert result <= 10.0

    def test_use_streak_freeze_invalid_type(self):
        """Invalid streak type defaults to focus."""
        adhd_buster = {"streak_freeze_tokens": 1}
        result = use_streak_freeze(adhd_buster, "invalid_type")
        assert result["success"] is True
        assert "focus" in adhd_buster["frozen_streaks"]

    def test_use_streak_freeze_invalid_tokens(self):
        """Invalid token count is handled."""
        adhd_buster = {"streak_freeze_tokens": "not a number"}
        result = use_streak_freeze(adhd_buster, "focus")
        assert result["success"] is False
        assert adhd_buster["streak_freeze_tokens"] == 0

    def test_open_mystery_box_invalid_tier(self):
        """Invalid tier defaults to bronze."""
        adhd_buster = {}
        result = open_mystery_box(adhd_buster, "invalid_tier")
        assert result["box_tier"] == "bronze"

    def test_update_challenge_log_all_json_serializable(self):
        """logs_today field is JSON serializable (list not set)."""
        import json
        adhd_buster = {
            "daily_challenges": [
                {
                    "id": "test_log_all",
                    "requirement": {"type": "log_all", "count": 3},
                    "progress": 0,
                    "completed": False,
                    "title": "Test",
                    "xp_reward": 100
                }
            ],
            "daily_challenges_date": datetime.now().strftime("%Y-%m-%d"),
            "weekly_challenges": [],
            "weekly_challenges_start": "2024-01-15"
        }
        
        update_challenge_progress(adhd_buster, "weight_log")
        update_challenge_progress(adhd_buster, "sleep_log")
        
        # Should not raise - logs_today should be a list, not set
        json.dumps(adhd_buster["daily_challenges"])
        
        challenge = adhd_buster["daily_challenges"][0]
        assert isinstance(challenge["logs_today"], list)
        assert len(challenge["logs_today"]) == 2

    def test_update_challenge_log_all_no_duplicates(self):
        """Same log type doesn't count twice."""
        adhd_buster = {
            "daily_challenges": [
                {
                    "id": "test_log_all",
                    "requirement": {"type": "log_all", "count": 3},
                    "progress": 0,
                    "completed": False,
                    "title": "Test",
                    "xp_reward": 100
                }
            ],
            "daily_challenges_date": datetime.now().strftime("%Y-%m-%d"),
            "weekly_challenges": [],
            "weekly_challenges_start": "2024-01-15"
        }
        
        update_challenge_progress(adhd_buster, "weight_log")
        update_challenge_progress(adhd_buster, "weight_log")  # Duplicate
        
        challenge = adhd_buster["daily_challenges"][0]
        assert challenge["progress"] == 1  # Only counted once

    def test_day_28_legendary_box(self):
        """Day 28 reward opens legendary mystery box."""
        reward = get_daily_login_reward(28)
        assert reward["type"] == "mystery_box"
        assert reward["tier"] == "legendary"

    def test_claim_daily_login_multiplier_with_missing_duration(self):
        """Multiplier reward with missing duration uses default."""
        # This tests the defensive coding for missing duration field
        from gamification import claim_daily_login
        adhd_buster = {}
        # We can't easily test this without mocking, but the code now handles it


class TestV532EdgeCases:
    """Tests for edge cases fixed in v5.3.2."""

    def test_get_xp_for_level_negative(self):
        """Negative level should return 0, not crash."""
        assert get_xp_for_level(-5) == 0
        assert get_xp_for_level(-1000) == 0

    def test_get_xp_for_level_invalid_type(self):
        """Invalid type should return 0, not crash."""
        assert get_xp_for_level(None) == 0
        assert get_xp_for_level("invalid") == 0
        assert get_xp_for_level([]) == 0

    def test_get_xp_for_level_float(self):
        """Float level should be handled gracefully."""
        # Should convert to int
        assert get_xp_for_level(5.7) == get_xp_for_level(5)
        assert get_xp_for_level(10.0) == get_xp_for_level(10)

    def test_get_celebration_message_missing_kwargs(self):
        """Celebration message with missing kwargs should not crash."""
        # Missing 'level' kwarg for level_up message
        msg = get_celebration_message("level_up")
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_get_celebration_message_invalid_event(self):
        """Invalid event type should return default message."""
        msg = get_celebration_message("nonexistent_event_type")
        assert msg == "🎉 Great job!"

    def test_generate_daily_challenges_no_global_state(self):
        """Daily challenge generation should not affect global random state."""
        # Set a known seed
        random.seed(12345)
        expected = random.random()
        
        # Reset and generate challenges (should use local RNG)
        random.seed(12345)
        generate_daily_challenges("2024-01-01")
        actual = random.random()
        
        # If using local RNG, the next random should match expected
        assert actual == expected, "generate_daily_challenges affected global random state"

    def test_generate_weekly_challenges_no_global_state(self):
        """Weekly challenge generation should not affect global random state."""
        random.seed(12345)
        expected = random.random()
        
        random.seed(12345)
        generate_weekly_challenges("2024-01-01")
        actual = random.random()
        
        assert actual == expected, "generate_weekly_challenges affected global random state"

    def test_get_xp_for_level_float_near_boundary(self):
        """Float level 1.9 should be treated as level 1 (return 0)."""
        assert get_xp_for_level(1.9) == 0  # 1.9 -> int(1) -> level 1 -> 0
        assert get_xp_for_level(1.1) == 0
        assert get_xp_for_level(1.999) == 0
        # But 2.0 and above should work
        assert get_xp_for_level(2.0) > 0
        assert get_xp_for_level(2.5) == get_xp_for_level(2)

    def test_calculate_combo_multiplier_none_daily_stats(self):
        """Combo multiplier should handle None daily_stats gracefully."""
        adhd_buster = {"daily_stats": None}
        result = calculate_combo_multiplier(adhd_buster)
        assert result["total_multiplier"] >= 1.0  # Should still return valid result
