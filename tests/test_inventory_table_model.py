from PySide6 import QtCore, QtGui

import focus_blocker_qt


def _find_row_by_orig_idx(model: focus_blocker_qt.InventoryTableModel, orig_idx: int) -> int:
    for row in range(model.rowCount()):
        idx = model.index(row, 0)
        value = model.data(idx, QtCore.Qt.UserRole)
        if value == orig_idx:
            return row
    return -1


def test_inventory_model_sorts_by_power_descending() -> None:
    model = focus_blocker_qt.InventoryTableModel()
    inventory = [
        {"name": "A", "slot": "Helmet", "rarity": "Common", "power": 10, "item_id": "a"},
        {"name": "B", "slot": "Helmet", "rarity": "Rare", "power": 30, "item_id": "b"},
        {"name": "C", "slot": "Helmet", "rarity": "Epic", "power": 20, "item_id": "c"},
    ]

    model.set_inventory(
        inventory=inventory,
        equipped={},
        active_story="warrior",
        sort_key="power",
        is_item_equipped_fn=lambda _item, _equipped: False,
    )

    assert model.rowCount() == 3
    top_idx = model.index(0, 0)
    assert model.data(top_idx, QtCore.Qt.UserRole) == 1
    assert model.data(model.index(0, 5), QtCore.Qt.DisplayRole) == "30"


def test_inventory_model_toggle_merge_respects_equipped_guard() -> None:
    model = focus_blocker_qt.InventoryTableModel()
    inventory = [
        {"name": "A", "slot": "Helmet", "rarity": "Common", "power": 10, "item_id": "a"},
        {"name": "B", "slot": "Helmet", "rarity": "Rare", "power": 30, "item_id": "b"},
    ]
    equipped = {"Helmet": {"item_id": "b", "slot": "Helmet"}}

    def _is_equipped(item: dict, eq: dict) -> bool:
        eq_item = eq.get(item.get("slot")) or {}
        return eq_item.get("item_id") == item.get("item_id")

    model.set_inventory(
        inventory=inventory,
        equipped=equipped,
        active_story="warrior",
        sort_key="newest",
        is_item_equipped_fn=_is_equipped,
    )

    equipped_row = _find_row_by_orig_idx(model, 1)
    normal_row = _find_row_by_orig_idx(model, 0)
    assert equipped_row >= 0
    assert normal_row >= 0

    assert model.toggle_merge_checked(equipped_row) is False
    assert model.selected_original_indices() == []

    assert model.toggle_merge_checked(normal_row) is True
    assert model.selected_original_indices() == [0]
    assert model.data(model.index(normal_row, 0), QtCore.Qt.UserRole + 1) is True
    bg = model.data(model.index(normal_row, 2), QtCore.Qt.BackgroundRole)
    assert isinstance(bg, QtGui.QColor)

    assert model.toggle_merge_checked(normal_row) is True
    assert model.selected_original_indices() == []
    assert model.data(model.index(normal_row, 0), QtCore.Qt.UserRole + 1) is False


def test_inventory_model_template_cache_reused_on_stable_refresh() -> None:
    model = focus_blocker_qt.InventoryTableModel()
    inventory = [
        {
            "name": "A",
            "slot": "Helmet",
            "rarity": "Common",
            "power": 10,
            "item_id": "a",
            "lucky_options": {"coin_discount": 2},
        },
        {
            "name": "B",
            "slot": "Boots",
            "rarity": "Rare",
            "power": 20,
            "item_id": "b",
            "lucky_options": {"merge_luck": 4},
        },
    ]

    model.set_inventory(
        inventory=inventory,
        equipped={},
        active_story="warrior",
        sort_key="newest",
        is_item_equipped_fn=lambda _item, _eq: False,
    )
    first_stats = model.cache_stats()
    assert first_stats["row_count"] == 2
    assert first_stats["template_cache_size"] >= 2

    model.set_inventory(
        inventory=inventory,
        equipped={},
        active_story="warrior",
        sort_key="newest",
        is_item_equipped_fn=lambda _item, _eq: False,
    )
    second_stats = model.cache_stats()
    assert second_stats["row_count"] == 2
    assert second_stats["template_cache_size"] == first_stats["template_cache_size"]
