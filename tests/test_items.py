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


def test_item_metadata_categories_and_flags():
    amrita = ITEM_ID_MAP[9]
    periapt = ITEM_ID_MAP[706]
    aquamarine = ITEM_ID_MAP[771]
    essence = ITEM_ID_MAP[311]
    relic = ITEM_ID_MAP[616]

    assert amrita.category == "consumable"
    assert amrita.unique is False
    assert amrita.use_scene_name == "Battle"
    assert amrita.infinite is False
    assert amrita.item_kind_name == "Use"

    assert periapt.category == "key_item"
    assert periapt.unique is True
    assert aquamarine.category == "key_item"
    assert aquamarine.unique is False
    assert essence.category == "essence"
    assert relic.category == "relic"


def test_item_use_target_and_search_metadata():
    life_stone = ITEM_ID_MAP[1]
    health_balm = ITEM_ID_MAP[84]
    health_incense = ITEM_ID_MAP[91]
    return_pillar = ITEM_ID_MAP[70]

    assert life_stone.use_target_name == "Any"
    assert health_balm.use_target_name == "Nahobino"
    assert health_incense.use_target_name == "Demon"
    assert return_pillar.infinite is True
    assert "infinite" in return_pillar.search_text
    assert "unique" in ITEM_ID_MAP[706].search_text
    assert "key item" in ITEM_ID_MAP[706].search_text
    assert "battle" in ITEM_ID_MAP[9].search_text


def test_item_validation_flags_over_limit_and_unused_ids():
    game = make_game()
    game.items.set_amount(ITEM_ID_MAP[9], 255, clamp=False)
    game.data[ITEM_TABLE_OFFSET + 29] = 1

    issues = game.items.validate()

    assert (9, "over_limit") in {
        (issue.item_id, issue.kind) for issue in issues
    }
    assert (29, "unused_id") in {
        (issue.item_id, issue.kind) for issue in issues
    }
    assert any("Amrita Soda" in issue.message for issue in issues)


def test_all_known_items_have_positive_limits():
    assert all(item.limit > 0 for item in ITEM_ID_MAP.values())


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
