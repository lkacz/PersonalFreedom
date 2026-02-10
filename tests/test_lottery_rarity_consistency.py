import os

import pytest
from PySide6 import QtWidgets


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_merge_tier_upgrade_keeps_animation_and_award_in_sync(monkeypatch, qapp):
    import gamification
    import merge_dialog
    from merge_dialog import LuckyMergeDialog

    class DummyMergeLotteryDialog:
        def __init__(self, *args, **kwargs):
            pass

        def exec_(self):
            return QtWidgets.QDialog.Accepted

        def get_results(self):
            return True, "Epic"

    def fake_generate_item(rarity=None, story_id=None, **kwargs):
        rarity = rarity or "Common"
        return {
            "name": f"{rarity} Test Item",
            "rarity": rarity,
            "slot": "weapon",
            "power": gamification.RARITY_POWER.get(rarity, 10),
        }

    items = [
        {"name": "Item A", "rarity": "Common", "slot": "weapon"},
        {"name": "Item B", "rarity": "Uncommon", "slot": "helmet"},
    ]
    adhd_buster = {
        "coins": 1000,
        "inventory": [],
        "equipped": {},
        "entitidex": {"collected_entity_ids": [], "exceptional_entities": {}},
    }

    dialog = LuckyMergeDialog(items, 0, {}, player_coins=1000, adhd_buster=adhd_buster)
    dialog.tier_upgrade_enabled = True
    dialog._show_result = lambda: None

    monkeypatch.setattr(merge_dialog, "MergeTwoStageLotteryDialog", DummyMergeLotteryDialog)
    monkeypatch.setattr(gamification, "generate_item", fake_generate_item)

    dialog.execute_merge()

    assert dialog.merge_result["success"] is True
    assert dialog.merge_result["final_rarity"] == "Epic"
    assert dialog.merge_result["result_item"]["rarity"] == "Epic"
    assert dialog.merge_result["tier_upgraded"] is True


def test_activity_lottery_can_reveal_pre_awarded_item_without_rarity_drift(qapp):
    from lottery_animation import ActivityLotteryDialog

    pre_awarded_item = {
        "name": "Legendary Fixed Reward",
        "rarity": "Legendary",
        "slot": "weapon",
        "power": 250,
    }

    dialog = ActivityLotteryDialog(
        effective_minutes=45,
        pre_rolled_rarity="Rare",
        story_id="warrior",
        item=pre_awarded_item,
    )

    dialog._finish_animation()
    rolled_tier, resolved_item = dialog.get_results()

    assert rolled_tier == "Legendary"
    assert resolved_item is pre_awarded_item
