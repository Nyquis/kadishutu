import pytest

from kadishutu.core.game_save import GameSaveEditor
from kadishutu.core.shared.file_handling import DecryptedSave
from kadishutu.data.items import (
    CONSUMABLES_RANGE,
    ITEM_ID_MAP,
    ITEM_TABLE_OFFSET,
    items_from,
)

GAME_SAVE_SIZE = 0x6DC90
ITEM_TABLE_SIZE = 896


def make_game() -> GameSaveEditor:
    data = bytearray(GAME_SAVE_SIZE)
    data[0x40:0x44] = b"GVAS"
    return GameSaveEditor(DecryptedSave(data))


def changed_offsets(before: bytes, after: bytes) -> set[int]:
    return {
        index
        for index, (old, new) in enumerate(zip(before, after, strict=True))
        if old != new
    }


def test_essence_offset_matches_known_khonsu_slot():
    game = make_game()

    assert game.items.from_id(311).offset == 0x4DA9


def test_set_all_writes_only_inside_item_table():
    game = make_game()
    items = items_from(CONSUMABLES_RANGE)
    before = bytes(game.data)

    game.items.set_all(items, 5)

    changed = changed_offsets(before, bytes(game.data))
    assert changed
    assert all(
        ITEM_TABLE_OFFSET <= offset < ITEM_TABLE_OFFSET + ITEM_TABLE_SIZE
        for offset in changed
    )
    assert game.items.from_meta(items[0]).amount == 5
    assert game.items.from_meta(items[-1]).amount == 5


def test_amrita_soda_uses_in_game_limit():
    game = make_game()
    item = ITEM_ID_MAP[9]

    assert item.name == "Amrita Soda"
    assert item.limit == 50

    game.items.max_all([item])

    assert game.items.from_meta(item).amount == 50


@pytest.mark.parametrize(
    ("item_id", "expected_limit"),
    [
        (9, 50),
        (656, 3),
        (706, 1),
        (757, 8),
        (769, 99),
        (771, 99),
        (772, 10),
        (799, 10),
        (800, 50),
        (801, 38),
    ],
)
def test_item_limits_match_game_table(item_id: int, expected_limit: int):
    item = ITEM_ID_MAP[item_id]

    assert item.limit == expected_limit


def test_max_all_uses_per_item_limits():
    game = make_game()
    items = items_from(CONSUMABLES_RANGE)

    game.items.max_all(items)

    for item in items[:10]:
        assert game.items.from_meta(item).amount == item.limit


def test_clear_all_zeroes_items():
    game = make_game()
    items = items_from(CONSUMABLES_RANGE)
    game.items.max_all(items)

    game.items.clear_all(items)

    assert all(game.items.from_meta(item).amount == 0 for item in items)


def test_set_amount_clamps_by_default():
    game = make_game()
    item = items_from(CONSUMABLES_RANGE)[0]

    editor = game.items.set_amount(item, 255)

    assert editor.amount == item.limit


def test_set_amount_can_skip_clamping():
    game = make_game()
    item = items_from(CONSUMABLES_RANGE)[0]

    editor = game.items.set_amount(item, 255, clamp=False)

    assert editor.amount == 255


@pytest.mark.parametrize("amount", [0, 1, 99, 255])
def test_set_all_accepts_valid_byte_amounts(amount: int):
    game = make_game()
    item = items_from(CONSUMABLES_RANGE)[0]

    game.items.set_all([item], amount, clamp=False)

    assert game.items.from_meta(item).amount == amount
