from types import SimpleNamespace

import pytest


def test_attempt_entitidex_bond_emits_entity_signal_on_success(monkeypatch):
    import gamification

    entity = SimpleNamespace(
        id="warrior_001",
        name="Test Entity",
        rarity="common",
        exceptional_name=None,
    )

    fake_progress = SimpleNamespace(
        get_failed_attempts=lambda *_args, **_kwargs: 0,
        mark_exceptional=lambda *_args, **_kwargs: None,
    )

    catch_result = SimpleNamespace(
        success=True,
        entity=entity,
        probability=0.75,
        roll=0.10,
    )

    fake_manager = SimpleNamespace(
        hero_power=123,
        progress=fake_progress,
        attempt_catch=lambda *_args, **_kwargs: catch_result,
    )

    class _FakeGameState:
        def __init__(self):
            self.collected = []

        def notify_entity_collected(self, entity_id):
            self.collected.append(entity_id)

    fake_game_state = _FakeGameState()

    monkeypatch.setattr("entitidex.get_entity_by_id", lambda _eid: entity)
    monkeypatch.setattr(gamification, "get_entitidex_manager", lambda _ab: fake_manager)
    monkeypatch.setattr(gamification, "save_entitidex_progress", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gamification, "award_xp", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("game_state.get_game_state", lambda: fake_game_state)

    result = gamification.attempt_entitidex_bond({"entitidex": {}}, entity.id, is_exceptional=False)

    assert result["success"] is True
    assert fake_game_state.collected == [entity.id]


def test_attempt_entitidex_bond_forwards_roll_override(monkeypatch):
    import gamification

    entity = SimpleNamespace(
        id="warrior_001",
        name="Test Entity",
        rarity="common",
        exceptional_name=None,
    )

    fake_progress = SimpleNamespace(
        get_failed_attempts=lambda *_args, **_kwargs: 0,
        mark_exceptional=lambda *_args, **_kwargs: None,
    )

    observed = {"roll_override": None}

    def _attempt_catch(*_args, **kwargs):
        observed["roll_override"] = kwargs.get("roll_override")
        return SimpleNamespace(success=False, entity=entity, probability=0.3, roll=0.42)

    fake_manager = SimpleNamespace(
        hero_power=123,
        progress=fake_progress,
        attempt_catch=_attempt_catch,
    )

    monkeypatch.setattr("entitidex.get_entity_by_id", lambda _eid: entity)
    monkeypatch.setattr(gamification, "get_entitidex_manager", lambda _ab: fake_manager)
    monkeypatch.setattr(gamification, "save_entitidex_progress", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gamification, "award_xp", lambda *_args, **_kwargs: None)

    result = gamification.attempt_entitidex_bond(
        {"entitidex": {}},
        entity.id,
        is_exceptional=False,
        roll_override=0.42,
    )

    assert observed["roll_override"] == 0.42
    assert result["operation_success"] is True
    assert result["bond_success"] is False


def test_finalize_risky_recalculate_reports_operation_failure(monkeypatch):
    import gamification

    fake_progress = SimpleNamespace(
        get_saved_encounters=lambda: [],
        get_saved_encounter_count=lambda: 0,
    )
    fake_manager = SimpleNamespace(progress=fake_progress)
    monkeypatch.setattr(gamification, "get_entitidex_manager", lambda _ab: fake_manager)

    result = gamification.finalize_risky_recalculate({"entitidex": {}}, index=0)

    assert result["operation_success"] is False
    assert result["success"] is False


def test_finalize_risky_recalculate_reports_operation_and_bond_success(monkeypatch):
    import gamification

    entity = SimpleNamespace(
        id="warrior_001",
        name="Test Entity",
        rarity="common",
        exceptional_name=None,
        power=50,
    )
    saved = SimpleNamespace(
        entity_id=entity.id,
        is_exceptional=False,
        catch_probability=0.25,
        exceptional_colors=None,
    )

    class _Progress:
        def __init__(self):
            self.saved = [saved]

        def get_saved_encounters(self):
            return list(self.saved)

        def pop_saved_encounter(self, index):
            return self.saved.pop(index)

        def get_saved_encounter_count(self):
            return len(self.saved)

        def record_successful_catch(self, **_kwargs):
            return None

        def record_failed_catch(self, *_args, **_kwargs):
            return None

    fake_progress = _Progress()
    fake_manager = SimpleNamespace(progress=fake_progress)

    monkeypatch.setattr(gamification, "get_entitidex_manager", lambda _ab: fake_manager)
    monkeypatch.setattr("entitidex.get_entity_by_id", lambda _eid: entity)
    monkeypatch.setattr(
        gamification,
        "_calculate_saved_encounter_recalc_probability",
        lambda **_kwargs: (0.8, 200),
    )
    monkeypatch.setattr(gamification, "calculate_character_power", lambda _ab: 200)
    monkeypatch.setattr(gamification, "award_xp", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gamification, "save_entitidex_progress", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("game_state.get_game_state", lambda: None)
    monkeypatch.setattr("random.random", lambda: 0.1)

    result = gamification.finalize_risky_recalculate(
        {"entitidex": {}},
        index=0,
        risky_roll=0.1,
        recalc_succeeded=True,
    )

    assert result["operation_success"] is True
    assert result["bond_success"] is True
    assert result["success"] is True


def test_open_saved_encounter_with_recalculate_uses_roll_override(monkeypatch):
    import gamification

    entity = SimpleNamespace(
        id="warrior_001",
        name="Test Entity",
        rarity="common",
        exceptional_name=None,
        power=40,
    )
    saved = SimpleNamespace(
        entity_id=entity.id,
        is_exceptional=False,
        catch_probability=0.75,
        exceptional_colors=None,
    )

    class _Progress:
        def __init__(self):
            self.saved = [saved]

        def get_saved_encounters(self):
            return list(self.saved)

        def pop_saved_encounter(self, index):
            return self.saved.pop(index)

        def get_saved_encounter_count(self):
            return len(self.saved)

        def record_successful_catch(self, **_kwargs):
            return None

        def record_failed_catch(self, *_args, **_kwargs):
            return None

    fake_progress = _Progress()
    fake_manager = SimpleNamespace(progress=fake_progress)

    monkeypatch.setattr(gamification, "get_entitidex_manager", lambda _ab: fake_manager)
    monkeypatch.setattr("entitidex.get_entity_by_id", lambda _eid: entity)
    monkeypatch.setattr(gamification, "calculate_character_power", lambda _ab: 180)
    monkeypatch.setattr(gamification, "award_xp", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gamification, "save_entitidex_progress", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("game_state.get_game_state", lambda: None)
    monkeypatch.setattr("random.random", lambda: pytest.fail("random.random should not be used when roll_override is provided"))

    result = gamification.open_saved_encounter_with_recalculate(
        {"entitidex": {}},
        index=0,
        recalculate=False,
        roll_override=0.10,
    )

    assert result["operation_success"] is True
    assert result["bond_success"] is True
    assert result["roll"] == 0.10


def test_open_saved_encounter_with_recalculate_reports_operation_failure_when_paid_perk_missing(monkeypatch):
    import gamification

    entity = SimpleNamespace(
        id="warrior_001",
        name="Test Entity",
        rarity="rare",
        exceptional_name=None,
        power=80,
    )
    saved = SimpleNamespace(
        entity_id=entity.id,
        is_exceptional=False,
        catch_probability=0.30,
        exceptional_colors=None,
    )

    class _Progress:
        def __init__(self):
            self.saved = [saved]

        def get_saved_encounters(self):
            return list(self.saved)

        def get_saved_encounter_count(self):
            return len(self.saved)

    fake_progress = _Progress()
    fake_manager = SimpleNamespace(progress=fake_progress)

    monkeypatch.setattr(gamification, "get_entitidex_manager", lambda _ab: fake_manager)
    monkeypatch.setattr("entitidex.get_entity_by_id", lambda _eid: entity)
    monkeypatch.setattr(gamification, "has_paid_recalculate_perk", lambda _ab: False)
    monkeypatch.setattr(gamification, "get_recalculate_provider_names", lambda **_kwargs: ["Provider One"])

    result = gamification.open_saved_encounter_with_recalculate(
        {"entitidex": {}, "coins": 999},
        index=0,
        recalculate=True,
        roll_override=0.2,
    )

    assert result["operation_success"] is False
    assert result["bond_success"] is False
    assert result["success"] is False


def test_open_saved_encounter_with_recalculate_reports_operation_failure_when_coins_insufficient(monkeypatch):
    import gamification

    entity = SimpleNamespace(
        id="warrior_001",
        name="Test Entity",
        rarity="legendary",
        exceptional_name=None,
        power=120,
    )
    saved = SimpleNamespace(
        entity_id=entity.id,
        is_exceptional=False,
        catch_probability=0.20,
        exceptional_colors=None,
    )

    class _Progress:
        def __init__(self):
            self.saved = [saved]

        def get_saved_encounters(self):
            return list(self.saved)

        def get_saved_encounter_count(self):
            return len(self.saved)

    fake_progress = _Progress()
    fake_manager = SimpleNamespace(progress=fake_progress)

    monkeypatch.setattr(gamification, "get_entitidex_manager", lambda _ab: fake_manager)
    monkeypatch.setattr("entitidex.get_entity_by_id", lambda _eid: entity)
    monkeypatch.setattr(gamification, "has_paid_recalculate_perk", lambda _ab: True)

    result = gamification.open_saved_encounter_with_recalculate(
        {"entitidex": {}, "coins": 0},
        index=0,
        recalculate=True,
        roll_override=0.2,
    )

    assert result["operation_success"] is False
    assert result["bond_success"] is False
    assert result["success"] is False


def test_finalize_risky_recalculate_uses_roll_override(monkeypatch):
    import gamification

    entity = SimpleNamespace(
        id="warrior_001",
        name="Test Entity",
        rarity="common",
        exceptional_name=None,
        power=40,
    )
    saved = SimpleNamespace(
        entity_id=entity.id,
        is_exceptional=False,
        catch_probability=0.20,
        exceptional_colors=None,
    )

    class _Progress:
        def __init__(self):
            self.saved = [saved]

        def get_saved_encounters(self):
            return list(self.saved)

        def pop_saved_encounter(self, index):
            return self.saved.pop(index)

        def get_saved_encounter_count(self):
            return len(self.saved)

        def record_successful_catch(self, **_kwargs):
            return None

        def record_failed_catch(self, *_args, **_kwargs):
            return None

    fake_progress = _Progress()
    fake_manager = SimpleNamespace(progress=fake_progress)

    monkeypatch.setattr(gamification, "get_entitidex_manager", lambda _ab: fake_manager)
    monkeypatch.setattr("entitidex.get_entity_by_id", lambda _eid: entity)
    monkeypatch.setattr(
        gamification,
        "_calculate_saved_encounter_recalc_probability",
        lambda **_kwargs: (0.80, 250),
    )
    monkeypatch.setattr(gamification, "calculate_character_power", lambda _ab: 180)
    monkeypatch.setattr(gamification, "award_xp", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(gamification, "save_entitidex_progress", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("game_state.get_game_state", lambda: None)
    monkeypatch.setattr("random.random", lambda: pytest.fail("random.random should not be used when risky_roll and roll_override are provided"))

    result = gamification.finalize_risky_recalculate(
        {"entitidex": {}},
        index=0,
        risky_roll=1.0,   # risky recalc fails -> use original 20% probability
        roll_override=0.10,
    )

    assert result["operation_success"] is True
    assert result["bond_success"] is True
    assert result["roll"] == 0.10
