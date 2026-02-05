"""Randomness integrity tests for entitidex catch rolls."""

import random
from unittest.mock import patch

from entitidex.catch_mechanics import attempt_catch
from entitidex.entity import Entity


def _make_entity(power: int = 100) -> Entity:
    return Entity(
        id="test_entity",
        name="Test Entity",
        power=power,
        rarity="common",
        lore="",
        theme_set="warrior",
    )


def test_attempt_catch_returns_roll_and_matches_success() -> None:
    entity = _make_entity()
    rng = random.Random(12345)

    with patch("entitidex.catch_mechanics.random.random", new=rng.random):
        success, probability, roll, _ = attempt_catch(hero_power=100, entity=entity)

    assert 0.0 <= roll < 1.0
    assert success == (roll < probability)


def test_attempt_catch_roll_distribution_reasonable() -> None:
    entity = _make_entity()
    rng = random.Random(424242)
    buckets = [0] * 10
    successes = 0
    n = 5000

    with patch("entitidex.catch_mechanics.random.random", new=rng.random):
        for _ in range(n):
            success, probability, roll, _ = attempt_catch(hero_power=100, entity=entity)
            successes += 1 if success else 0
            idx = min(9, int(roll * 10))
            buckets[idx] += 1

    # Uniform-ish across deciles (within 12% tolerance).
    expected = n / 10
    tolerance = expected * 0.12
    for count in buckets:
        assert abs(count - expected) <= tolerance

    # Success rate should be close to 50% when hero_power == entity.power.
    assert abs((successes / n) - 0.5) < 0.05
