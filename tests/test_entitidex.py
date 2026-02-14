"""
Tests for the Entitidex System.

Comprehensive test suite covering entity pools, catch mechanics,
progress tracking, encounter system, and the main manager.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

# Import the entitidex package
from entitidex import (
    Entity,
    EntityCapture,
    EntitidexProgress,
    EntitidexManager,
    ENTITY_POOLS,
    get_entities_for_story,
    calculate_join_probability,
    apply_pity_bonus,
    attempt_catch,
    should_trigger_encounter,
    select_encounter_entity,
    CATCH_CONFIG,
    ENCOUNTER_CONFIG,
)
from entitidex.entity_pools import (
    get_entity_by_id,
    get_all_entity_ids,
    get_entity_count_by_theme,
    get_total_entity_count,
)


# =============================================================================
# ENTITY POOL TESTS
# =============================================================================

class TestEntityPools:
    """Tests for entity pool definitions."""
    
    def test_all_stories_have_9_entities(self):
        """Each story should have exactly 9 entities."""
        for story_id, pool in ENTITY_POOLS.items():
            assert len(pool) == 9, f"{story_id} has {len(pool)} entities, expected 9"
    
    def test_entity_power_progression(self):
        """Entity power should increase from #001 to #009."""
        for story_id, pool in ENTITY_POOLS.items():
            powers = [e["power"] for e in pool]
            assert powers == sorted(powers), f"{story_id} powers not in ascending order"
    
    def test_entity_ids_are_unique(self):
        """All entity IDs must be unique across all pools."""
        all_ids = get_all_entity_ids()
        assert len(all_ids) == len(set(all_ids)), "Duplicate entity IDs found"
    
    def test_entity_id_format(self):
        """Entity IDs should follow the format: {story}_{number}."""
        for story_id, pool in ENTITY_POOLS.items():
            for i, entity in enumerate(pool, 1):
                expected_id = f"{story_id}_{i:03d}"
                assert entity["id"] == expected_id, f"Expected {expected_id}, got {entity['id']}"
    
    def test_rarity_distribution(self):
        """Check rarity distribution: 2 common, 2 uncommon, 2 rare, 2 epic, 1 legendary."""
        expected_rarities = {
            "common": 2,
            "uncommon": 2,
            "rare": 2,
            "epic": 2,
            "legendary": 1,
        }
        
        for story_id, pool in ENTITY_POOLS.items():
            rarity_counts = {}
            for entity in pool:
                rarity = entity["rarity"]
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
            
            assert rarity_counts == expected_rarities, f"{story_id} has wrong rarity distribution"
    
    def test_get_entities_for_story(self):
        """get_entities_for_story should return Entity objects."""
        entities = get_entities_for_story("warrior")
        
        assert len(entities) == 9
        assert all(isinstance(e, Entity) for e in entities)
        assert entities[0].name == "Hatchling Drake"
        assert entities[8].name == "Old War Ant General"
    
    def test_get_entity_by_id(self):
        """get_entity_by_id should return correct entity."""
        entity = get_entity_by_id("scholar_005")
        
        assert entity is not None
        assert entity.name == "Living Bookmark Finn"
        assert entity.power == 700
        assert entity.rarity == "rare"
    
    def test_get_entity_by_id_not_found(self):
        """get_entity_by_id should return None for unknown ID."""
        entity = get_entity_by_id("nonexistent_999")
        assert entity is None
    
    def test_total_entity_count(self):
        """Total entity count should match 9 entities per registered story."""
        assert get_total_entity_count() == len(ENTITY_POOLS) * 9
    
    def test_all_entities_have_lore(self):
        """Every entity should have lore text."""
        for story_id, pool in ENTITY_POOLS.items():
            for entity in pool:
                assert "lore" in entity and len(entity["lore"]) > 0, \
                    f"{entity['id']} missing lore"


# =============================================================================
# ENTITY MODEL TESTS
# =============================================================================

class TestEntity:
    """Tests for the Entity data model."""
    
    def test_entity_creation(self):
        """Test creating an Entity instance."""
        entity = Entity(
            id="test_001",
            name="Test Entity",
            power=100,
            rarity="rare",
            lore="Test lore text",
            theme_set="warrior",
        )
        
        assert entity.id == "test_001"
        assert entity.name == "Test Entity"
        assert entity.power == 100
        assert entity.rarity == "rare"
    
    def test_rarity_emoji(self):
        """Test rarity emoji property."""
        assert Entity(id="", name="", power=0, rarity="common", lore="", theme_set="").rarity_emoji == "⚪"
        assert Entity(id="", name="", power=0, rarity="legendary", lore="", theme_set="").rarity_emoji == "🟡"
        assert Entity(id="", name="", power=0, rarity="celestial", lore="", theme_set="").rarity_emoji == "✨"
    
    def test_slot_number(self):
        """Test slot number extraction from ID."""
        entity = Entity(id="warrior_003", name="", power=0, rarity="", lore="", theme_set="")
        assert entity.slot_number == 3
    
    def test_to_dict_and_from_dict(self):
        """Test entity serialization round-trip."""
        original = Entity(
            id="test_001",
            name="Test",
            power=500,
            rarity="epic",
            lore="Test lore",
            theme_set="scholar",
            unlock_hint="A hint",
        )
        
        data = original.to_dict()
        restored = Entity.from_dict(data)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.power == original.power


class TestEntityCapture:
    """Tests for the EntityCapture data model."""
    
    def test_capture_creation(self):
        """Test creating a capture record."""
        capture = EntityCapture(
            entity_id="warrior_001",
            hero_power_at_capture=50,
            attempts_before_capture=2,
            catch_probability=0.65,
            was_lucky_catch=False,
        )
        
        assert capture.entity_id == "warrior_001"
        assert capture.hero_power_at_capture == 50
        assert capture.attempts_before_capture == 2
    
    def test_capture_serialization(self):
        """Test capture serialization round-trip."""
        original = EntityCapture(
            entity_id="scholar_003",
            hero_power_at_capture=200,
            catch_probability=0.75,
            was_lucky_catch=True,
        )
        
        data = original.to_dict()
        restored = EntityCapture.from_dict(data)
        
        assert restored.entity_id == original.entity_id
        assert restored.was_lucky_catch == original.was_lucky_catch


# =============================================================================
# CATCH MECHANICS TESTS
# =============================================================================

class TestCatchMechanics:
    """Tests for catch probability calculations."""
    
    def test_equal_power_gives_50_percent(self):
        """Equal hero and entity power should give 50% catch chance."""
        prob = calculate_join_probability(1000, 1000)
        assert abs(prob - 0.50) < 0.01
    
    def test_double_power_gives_max(self):
        """Hero with 2x entity power should get max (99%) chance."""
        prob = calculate_join_probability(2000, 1000)
        assert prob == CATCH_CONFIG["probability_max"]
    
    def test_half_power_gives_low(self):
        """Hero with half entity power should get ~25% chance."""
        prob = calculate_join_probability(500, 1000)
        assert 0.24 < prob < 0.26
    
    def test_minimum_probability(self):
        """Very weak hero should still have minimum chance."""
        prob = calculate_join_probability(10, 2000)
        assert prob >= CATCH_CONFIG["probability_min"]
    
    def test_zero_power_edge_case(self):
        """Zero power should return minimum probability."""
        assert calculate_join_probability(0, 1000) == CATCH_CONFIG["probability_min"]
        assert calculate_join_probability(1000, 0) == CATCH_CONFIG["probability_min"]
    
    def test_pity_bonus_thresholds(self):
        """Test pity bonus is applied at correct thresholds."""
        base = 0.30
        
        # No bonus under threshold 1
        assert apply_pity_bonus(base, 4) == base
        
        # Bonus 1 at threshold 1
        assert apply_pity_bonus(base, 5) == base + CATCH_CONFIG["pity_bonus_1"]
        
        # Bonus 2 at threshold 2
        assert apply_pity_bonus(base, 10) == base + CATCH_CONFIG["pity_bonus_2"]
        
        # Bonus 3 at threshold 3
        assert apply_pity_bonus(base, 15) == base + CATCH_CONFIG["pity_bonus_3"]
    
    def test_pity_bonus_caps_at_max(self):
        """Pity bonus should not exceed max probability."""
        prob = apply_pity_bonus(0.90, 20)
        assert prob == CATCH_CONFIG["probability_max"]
    
    def test_attempt_catch_returns_result(self):
        """attempt_catch should return proper tuple."""
        entity = get_entity_by_id("warrior_001")
        
        success, prob, roll, message = attempt_catch(
            hero_power=100,
            entity=entity,
            failed_attempts=0,
        )
        
        assert isinstance(success, bool)
        assert 0.0 <= prob <= 1.0
        assert 0.0 <= roll < 1.0
        assert len(message) > 0


# =============================================================================
# PROGRESS TRACKER TESTS
# =============================================================================

class TestEntitidexProgress:
    """Tests for progress tracking."""
    
    def test_initial_state(self):
        """New progress should be empty."""
        progress = EntitidexProgress()
        
        assert len(progress.collected_entity_ids) == 0
        assert progress.total_encounters == 0
        assert progress.total_catch_attempts == 0
    
    def test_record_encounter(self):
        """Recording encounter should update counts."""
        progress = EntitidexProgress()
        
        progress.record_encounter("warrior_001")
        
        assert progress.is_encountered("warrior_001")
        assert progress.get_encounter_count("warrior_001") == 1
        assert progress.total_encounters == 1
    
    def test_record_failed_catch(self):
        """Recording failed catch should update failed count."""
        progress = EntitidexProgress()
        
        progress.record_failed_catch("warrior_003")
        progress.record_failed_catch("warrior_003")
        
        assert progress.get_failed_attempts("warrior_003") == 2
        assert progress.total_catch_attempts == 2
    
    def test_record_successful_catch(self):
        """Successful catch should update collection and clear failed."""
        progress = EntitidexProgress()
        
        # Fail twice first
        progress.record_failed_catch("warrior_005")
        progress.record_failed_catch("warrior_005")
        
        # Then succeed
        capture = progress.record_successful_catch(
            entity_id="warrior_005",
            hero_power=800,
            probability=0.65,
            was_lucky=False,
        )
        
        assert progress.is_collected("warrior_005")
        assert progress.get_failed_attempts("warrior_005") == 0  # Reset after catch
        assert capture.attempts_before_capture == 3  # 2 fails + 1 success
    
    def test_collection_rate(self):
        """Collection rate should calculate correctly."""
        progress = EntitidexProgress()
        
        # Collect 3 warrior entities
        progress.collected_entity_ids.add("warrior_001")
        progress.collected_entity_ids.add("warrior_002")
        progress.collected_entity_ids.add("warrior_003")
        
        rate = progress.get_collection_rate("warrior")
        assert abs(rate - (3/9)) < 0.01
    
    def test_progress_serialization(self):
        """Progress should serialize and deserialize correctly."""
        original = EntitidexProgress()
        original.collected_entity_ids.add("scholar_001")
        original.encounters["scholar_002"] = 3
        original.failed_catches["scholar_003"] = 2
        
        data = original.to_dict()
        restored = EntitidexProgress.from_dict(data)
        
        assert "scholar_001" in restored.collected_entity_ids
        assert restored.encounters["scholar_002"] == 3
        assert restored.failed_catches["scholar_003"] == 2

    def test_progress_from_dict_handles_non_dict_input(self):
        """Malformed non-dict input should safely return defaults."""
        restored = EntitidexProgress.from_dict(None)

        assert restored.collected_entity_ids == set()
        assert restored.encounters == {}
        assert restored.failed_catches == {}
        assert restored.captures == []

    def test_progress_from_dict_sanitizes_malformed_data(self):
        """Malformed nested data should be sanitized instead of crashing."""
        now_iso = datetime.now().isoformat()
        data = {
            "collected_entity_ids": {"warrior_001": True, "warrior_002": False},
            "encounters": {"warrior_001": "3", "warrior_002": "oops", 99: 2},
            "failed_catches": "bad",
            "exceptional_failed_catches": {"warrior_003": "2", "warrior_004": -1},
            "exceptional_entities": {
                "warrior_001": {"border": "#111111", "glow": "#222222"},
                "warrior_002": "invalid",
            },
            "captures": [
                {"entity_id": "warrior_001", "captured_at": "not-a-date"},
                {"entity_id": "warrior_002", "captured_at": now_iso},
            ],
            "saved_encounters": [
                {"entity_id": "warrior_003", "saved_at": "not-a-date"},
                {"entity_id": "warrior_004", "saved_at": now_iso},
            ],
            "current_tier": "5",
            "total_catch_attempts": "7",
            "total_encounters": "9",
            "lucky_catches": "2",
            "theme_completions": {"warrior": 123},
            "celebration_seen": {"warrior": "yes"},
            "celebration_clicks": {"warrior": "4", "scholar": "x"},
            "celebration_quote_index": {"warrior": "2", "scholar": -1},
            "celebration_voice_enabled": "true",
        }

        restored = EntitidexProgress.from_dict(data)

        assert "warrior_001" in restored.collected_entity_ids
        assert "warrior_002" not in restored.collected_entity_ids

        assert restored.encounters["warrior_001"] == 3
        assert restored.encounters["99"] == 2
        assert "warrior_002" not in restored.encounters

        assert restored.failed_catches == {}
        assert restored.exceptional_failed_catches == {"warrior_003": 2}

        assert restored.exceptional_entities == {
            "warrior_001": {"border": "#111111", "glow": "#222222"}
        }

        assert len(restored.captures) == 1
        assert restored.captures[0].entity_id == "warrior_002"

        assert len(restored.saved_encounters) == 1
        assert restored.saved_encounters[0].entity_id == "warrior_004"

        assert restored.current_tier == 5
        assert restored.total_catch_attempts == 7
        assert restored.total_encounters == 9
        assert restored.lucky_catches == 2

        assert restored.theme_completions == {"warrior": "123"}
        assert restored.celebration_seen == {"warrior": True}
        assert restored.celebration_clicks == {"warrior": 4}
        assert restored.celebration_quote_index == {"warrior": 2}
        assert restored.celebration_voice_enabled is True
    
    def test_get_uncollected_entities(self):
        """Should return only uncollected entities."""
        progress = EntitidexProgress()
        progress.collected_entity_ids.add("wanderer_001")
        progress.collected_entity_ids.add("wanderer_002")
        
        uncollected = progress.get_uncollected_entities("wanderer")
        
        assert len(uncollected) == 7
        assert all(e.id not in ["wanderer_001", "wanderer_002"] for e in uncollected)

    def test_statistics_counts_normal_and_exceptional_pity(self):
        """Pity stats should include both normal and exceptional variant failures."""
        progress = EntitidexProgress()
        progress.failed_catches = {"warrior_001": 2}
        progress.exceptional_failed_catches = {"warrior_002": 1, "warrior_003": 4}

        stats = progress.get_statistics("warrior")
        assert stats["entities_with_pity"] == 3


# =============================================================================
# ENCOUNTER SYSTEM TESTS
# =============================================================================

class TestEncounterSystem:
    """Tests for encounter triggering and selection."""
    
    def test_base_encounter_chance(self):
        """Base encounter chance should be 40%."""
        from entitidex.encounter_system import calculate_encounter_chance
        
        chance, perk_bonus = calculate_encounter_chance(
            session_minutes=25,
            minimum_session_minutes=25,
        )
        
        assert abs(chance - ENCOUNTER_CONFIG["base_chance"]) < 0.01
        assert perk_bonus == 0.0  # No perks applied
    
    def test_longer_session_bonus(self):
        """Longer sessions should increase encounter chance."""
        from entitidex.encounter_system import calculate_encounter_chance
        
        base_chance, _ = calculate_encounter_chance(25, 25)
        bonus_chance, _ = calculate_encounter_chance(55, 25)  # 30 min extra = 2x15min blocks
        
        expected_bonus = 2 * ENCOUNTER_CONFIG["bonus_per_15min"]
        assert abs(bonus_chance - (base_chance + expected_bonus)) < 0.01
    
    def test_perfect_session_bonus(self):
        """Perfect sessions should increase encounter chance."""
        from entitidex.encounter_system import calculate_encounter_chance
        
        normal, _ = calculate_encounter_chance(25, 25, was_perfect_session=False)
        perfect, _ = calculate_encounter_chance(25, 25, was_perfect_session=True)
        
        assert perfect == normal + ENCOUNTER_CONFIG["bonus_perfect_session"]
    
    def test_bypass_reduces_encounter_chance(self):
        """Bypass should reduce encounter chance, not eliminate it.
        
        This allows users to use bypass when genuinely needed (fatigue, emergencies)
        without feeling completely punished.
        """
        from entitidex.encounter_system import roll_encounter_chance
        
        # Get normal chance
        _, normal_chance, _ = roll_encounter_chance(
            session_minutes=60,
            was_perfect_session=True,
            streak_days=10,
            was_bypass_used=False,
        )
        
        # Get bypass chance
        _, bypass_chance, _ = roll_encounter_chance(
            session_minutes=60,
            was_perfect_session=True,
            streak_days=10,
            was_bypass_used=True,
        )
        
        # Bypass chance should be reduced by the penalty multiplier
        expected_bypass_chance = normal_chance * ENCOUNTER_CONFIG["bypass_penalty_multiplier"]
        assert bypass_chance == expected_bypass_chance
        assert bypass_chance > 0  # Still has a chance, not zero
        assert bypass_chance < normal_chance  # But reduced
    
    def test_select_encounter_entity_from_uncollected(self):
        """Entity selection should only return uncollected entities."""
        progress = EntitidexProgress()
        progress.collected_entity_ids.add("underdog_001")
        progress.collected_entity_ids.add("underdog_002")
        
        # Run many times to ensure we never get collected entities
        for _ in range(50):
            entity, is_exceptional = select_encounter_entity(
                progress=progress,
                hero_power=100,
                story_id="underdog",
            )
            
            assert entity is not None
            # If we got normal variant, entity shouldn't be in collected
            # If we got exceptional variant, the exceptional shouldn't be collected
            if not is_exceptional:
                assert entity.id not in ["underdog_001", "underdog_002"]
    
    def test_select_returns_none_when_complete(self):
        """Selection should return None when collection is complete (both variants)."""
        progress = EntitidexProgress()
        
        # Collect all warrior entities (both normal AND exceptional variants)
        for i in range(1, 10):
            entity_id = f"warrior_{i:03d}"
            progress.collected_entity_ids.add(entity_id)
            progress.exceptional_entities[entity_id] = {"border": "#FFD700", "glow": "#FFA500"}
        
        entity, is_exceptional = select_encounter_entity(
            progress=progress,
            hero_power=2000,
            story_id="warrior",
        )
        
        assert entity is None


# =============================================================================
# ENTITIDEX MANAGER TESTS
# =============================================================================

class TestEntitidexManager:
    """Tests for the main manager class."""
    
    def test_manager_creation(self):
        """Manager should initialize with defaults."""
        manager = EntitidexManager(
            story_id="scholar",
            hero_power=500,
        )
        
        assert manager.story_id == "scholar"
        assert manager.hero_power == 500
        assert manager.progress is not None
    
    def test_check_for_encounter_no_bypass(self):
        """Encounter check should work when not bypassed."""
        manager = EntitidexManager(story_id="warrior", hero_power=100)
        
        # Force encounter to occur by mocking (patch where it's used, not defined)
        with patch('entitidex.entitidex_manager.should_trigger_encounter', return_value=True):
            result = manager.check_for_encounter(
                session_minutes=30,
                was_perfect_session=True,
            )
        
        assert result.occurred is True
        assert result.entity is not None
        assert result.catch_probability > 0
    
    def test_check_for_encounter_bypass_has_reduced_chance(self):
        """Bypass should have reduced but non-zero encounter chance."""
        from entitidex.encounter_system import ENCOUNTER_CONFIG
        
        manager = EntitidexManager(story_id="warrior", hero_power=100)
        
        # Test multiple times - bypass reduces chance to 25% of normal
        # With 40% base chance, bypass gives ~10% chance
        # So about 90% of attempts should NOT trigger
        bypass_results = []
        for _ in range(100):
            result = manager.check_for_encounter(
                session_minutes=30,
                was_bypass_used=True,
            )
            bypass_results.append(result.occurred)
        
        # Most should be False (reduced chance)
        trigger_rate = sum(bypass_results) / len(bypass_results)
        
        # Expected rate is ~10% (40% base * 25% penalty)
        # Allow for statistical variance
        assert trigger_rate < 0.30  # Much lower than normal 40%
        # Note: We don't assert > 0 because with 10% chance, 
        # getting 0/100 is possible (0.003% probability)
    
    def test_force_encounter(self):
        """Force encounter should work with valid entity ID."""
        manager = EntitidexManager(story_id="scholar", hero_power=1000)
        
        result = manager.force_encounter("scholar_005")
        
        assert result is not None
        assert result.entity.id == "scholar_005"
        assert result.entity.name == "Living Bookmark Finn"
    
    def test_attempt_catch_success(self):
        """Catch attempt should update progress on success."""
        manager = EntitidexManager(story_id="warrior", hero_power=2000)
        
        # Force an encounter
        manager.force_encounter("warrior_001")  # Low power entity
        
        # With 2000 hero power vs 10 entity power, should be ~99% catch rate
        # Run until we get a success (should be very quick)
        result = None
        for _ in range(100):  # Safety limit
            manager.force_encounter("warrior_001")
            result = manager.attempt_catch()
            if result.success:
                break
        
        assert result is not None
        assert result.success is True
        assert manager.progress.is_collected("warrior_001")

    def test_attempt_catch_applies_city_bonus(self):
        """City catch bonus should affect actual catch roll outcome."""
        manager = EntitidexManager(
            story_id="warrior",
            hero_power=10,          # Equal to warrior_001 power
            city_catch_bonus=20.0,  # +20 percentage points
        )
        manager.force_encounter("warrior_001")

        # Base chance is 50% at equal power. With +20% city bonus => 70%.
        with patch("entitidex.catch_mechanics.random.random", return_value=0.60):
            result = manager.attempt_catch()

        assert result is not None
        assert result.success is True
        assert result.probability > 0.69

    def test_encounter_probability_matches_catch_with_pity_perk(self):
        """Displayed encounter probability should match actual catch probability."""
        from entitidex.entity_perks import PerkType

        manager = EntitidexManager(
            story_id="warrior",
            hero_power=10,
            active_perks={PerkType.PITY_BONUS: 50},  # 10 fails -> 15 effective
        )
        manager.progress.failed_catches["warrior_001"] = 10

        encounter = manager.force_encounter("warrior_001")
        assert encounter is not None

        with patch("entitidex.catch_mechanics.random.random", return_value=0.80):
            result = manager.attempt_catch()

        assert result is not None
        assert abs(encounter.catch_probability - result.probability) < 1e-9
        assert result.success is True
    
    def test_get_collection_entities(self):
        """Should return all entities with collection status."""
        manager = EntitidexManager(story_id="wanderer", hero_power=500)
        manager.progress.collected_entity_ids.add("wanderer_001")
        
        entities = manager.get_collection_entities()
        
        assert len(entities) == 9
        
        # First should be collected
        entity, collected = entities[0]
        assert entity.id == "wanderer_001"
        assert collected is True
        
        # Second should not be collected
        entity, collected = entities[1]
        assert entity.id == "wanderer_002"
        assert collected is False
    
    def test_get_statistics(self):
        """Statistics should include all relevant data."""
        manager = EntitidexManager(story_id="underdog", hero_power=750)
        manager.progress.collected_entity_ids.add("underdog_001")
        manager.progress.collected_entity_ids.add("underdog_002")
        
        stats = manager.get_statistics()
        
        assert stats["collected"] == 2
        assert stats["total"] == 9
        assert abs(stats["completion_rate"] - (2/9)) < 0.01
    
    def test_save_and_load_progress(self):
        """Progress should save and load correctly."""
        # Create manager and add some progress
        manager1 = EntitidexManager(story_id="scholar", hero_power=500)
        manager1.progress.collected_entity_ids.add("scholar_001")
        manager1.progress.encounters["scholar_002"] = 5
        
        # Save
        saved_data = manager1.save_progress()
        
        # Create new manager and load
        manager2 = EntitidexManager(story_id="scholar", hero_power=500)
        manager2.load_progress(saved_data)
        
        assert "scholar_001" in manager2.progress.collected_entity_ids
        assert manager2.progress.encounters["scholar_002"] == 5


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the full Entitidex flow."""
    
    def test_full_encounter_and_catch_flow(self):
        """Test the complete flow from encounter to catch."""
        manager = EntitidexManager(
            story_id="warrior",
            hero_power=100,  # Should be able to catch early entities
        )
        
        # Force an encounter with the first entity
        encounter = manager.force_encounter("warrior_001")
        
        assert encounter is not None
        assert encounter.occurred is True
        assert encounter.entity.id == "warrior_001"
        
        # Verify encounter was recorded
        assert manager.progress.is_encountered("warrior_001")
        
        # Attempt catch (high chance with 100 power vs 10 power)
        result = manager.attempt_catch()
        
        assert result is not None
        assert result.entity.id == "warrior_001"
        
        if result.success:
            assert manager.progress.is_collected("warrior_001")
        else:
            assert manager.progress.get_failed_attempts("warrior_001") == 1
    
    def test_pity_system_increases_chance(self):
        """Repeated failures should increase catch chance via pity."""
        manager = EntitidexManager(
            story_id="underdog",
            hero_power=10,  # Very weak
        )
        
        # Simulate many failed attempts
        for _ in range(15):
            manager.progress.record_failed_catch("underdog_009")  # Legendary entity
        
        # Get entity details - should show increased probability
        details = manager.get_entity_details("underdog_009")
        
        # Base probability at 10 vs 2000 power is ~0.5%
        # After 15 failures, should have +50% pity bonus
        assert details["current_catch_probability"] > 0.40
    
    def test_collection_completion(self):
        """Test that completion is detected correctly."""
        manager = EntitidexManager(story_id="scholar", hero_power=5000)
        
        # Collect all but one
        for i in range(1, 9):
            manager.progress.collected_entity_ids.add(f"scholar_{i:03d}")
        
        assert not manager.is_collection_complete()
        
        # Collect the last one
        manager.progress.collected_entity_ids.add("scholar_009")
        
        assert manager.is_collection_complete()

# =============================================================================
# EXCEPTIONAL VARIANT AVAILABILITY
# =============================================================================

class TestExceptionalAvailability:
    """Tests specifically checking that exceptional variants remain obtainable."""

    def test_exceptional_variant_available_after_normal_catch(self):
        """
        CRITICAL: Collecting the normal version MUST NOT block the exceptional version.
        This validates user requirement: 'exceptional versions are still obtainable'.
        """
        progress = EntitidexProgress()
        entity_id = "warrior_001"
        
        # 1. Initially, both should be available
        assert progress.is_variant_available(entity_id, is_exceptional=False)
        assert progress.is_variant_available(entity_id, is_exceptional=True)
        
        # 2. Collect the NORMAL version
        progress.collected_entity_ids.add(entity_id)
        
        # 3. Verify availability
        # Normal should be GONE (already have it)
        assert not progress.is_variant_available(entity_id, is_exceptional=False)
        
        # Exceptional should STILL BE AVAILABLE
        assert progress.is_variant_available(entity_id, is_exceptional=True)
        
        # 4. Verify getting available variants for story
        # This is what the encounter system actually calls
        available_exceptional = progress.get_available_entity_variants("warrior", is_exceptional=True)
        available_ids = [e.id for e in available_exceptional]
        
        assert entity_id in available_ids, "Exceptional variant should appear in available list even if normal is collected"

    def test_normal_variant_available_after_exceptional_catch(self):
        """Converting rare->normal logic (less common but possible flow)."""
        progress = EntitidexProgress()
        entity_id = "warrior_002"
        
        # 1. Collect EXCEPTIONAL first
        progress.mark_exceptional(entity_id, {"border": "#FFD700", "glow": "#FFA500"})
        
        # 2. Verify availability
        # Exceptional should be GONE
        assert not progress.is_variant_available(entity_id, is_exceptional=True)
        
        # Normal should STILL BE AVAILABLE
        assert progress.is_variant_available(entity_id, is_exceptional=False)

    def test_both_variants_collected(self):
        """Verify unavailable when both are collected."""
        progress = EntitidexProgress()
        entity_id = "warrior_003"
        
        # Collect BOTH
        progress.collected_entity_ids.add(entity_id)
        progress.mark_exceptional(entity_id, {"border": "#000", "glow": "#000"})
        
        # Both gone
        assert not progress.is_variant_available(entity_id, is_exceptional=False)
        assert not progress.is_variant_available(entity_id, is_exceptional=True)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
