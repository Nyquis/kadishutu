import pytest

from kadishutu.core.game_save import GameSaveEditor
from kadishutu.core.game_save.demons import NO_DEMON
from kadishutu.core.shared.file_handling import DecryptedSave
from kadishutu.data.demons import DEMON_ID_MAP

GAME_SAVE_SIZE = 0x6DC90


def make_game() -> GameSaveEditor:
    data = bytearray(GAME_SAVE_SIZE)
    data[0x40:0x44] = b"GVAS"
    return GameSaveEditor(DecryptedSave(data))


def test_storage_iteration_remains_24_slots():
    game = make_game()

    assert len(list(game.demons)) == 24


def test_all_and_guest_iteration_covers_30_slots():
    game = make_game()

    assert len(list(game.demons.all())) == 30
    assert len(list(game.demons.guests())) == 6
    assert [demon.slot for demon in game.demons.guests()] == list(range(24, 30))


def test_guest_slots_are_marked_as_guests():
    game = make_game()

    assert not game.demons.in_slot(23).is_guest
    assert game.demons.in_slot(24).is_guest
    assert game.demons.in_slot(29).is_guest


def test_real_all_includes_guest_records():
    game = make_game()
    for i in range(30):
        game.demons.in_slot(i).demon_id = NO_DEMON
    game.demons.in_slot(24).demon_id = 100

    assert list(game.demons.real()) == []
    assert [demon.slot for demon in game.demons.real_all()] == [24]


def test_find_free_slot_stays_in_storage():
    game = make_game()
    for i in range(24):
        game.demons.in_slot(i).demon_id = 1

    with pytest.raises(RuntimeError):
        game.demons._find_free_slot()

    game.demons.in_slot(23).demon_id = NO_DEMON

    assert game.demons._find_free_slot().slot == 23


def test_in_slot_rejects_out_of_range():
    game = make_game()

    with pytest.raises(IndexError):
        game.demons.in_slot(30)
    with pytest.raises(IndexError):
        game.demons.in_slot(-1)


def test_free_storage_slots_excludes_occupied_slots():
    game = make_game()
    for i in range(30):
        game.demons.in_slot(i).demon_id = NO_DEMON

    assert game.demons.free_storage_slots() == list(range(24))

    game.demons.in_slot(7).demon_id = 1

    assert 7 not in game.demons.free_storage_slots()


def test_create_from_initial_uses_requested_slot():
    game = make_game()
    for i in range(30):
        game.demons.in_slot(i).demon_id = NO_DEMON
    meta = next(iter(DEMON_ID_MAP.values()))

    demon = game.demons.create_from_initial(meta, 7)

    assert demon.slot == 7
    assert demon.demon_id == meta.id
    assert demon.level == meta.level
    assert demon.healable.hp == demon.stats.current.hp
    assert demon.healable.mp == demon.stats.current.mp


def test_create_from_initial_refuses_occupied_slot():
    game = make_game()
    for i in range(30):
        game.demons.in_slot(i).demon_id = NO_DEMON
    game.demons.in_slot(7).demon_id = 1
    meta = next(iter(DEMON_ID_MAP.values()))

    with pytest.raises(ValueError, match="occupied"):
        game.demons.create_from_initial(meta, 7)


def test_create_from_initial_refuses_guest_slot():
    game = make_game()
    for i in range(30):
        game.demons.in_slot(i).demon_id = NO_DEMON
    meta = next(iter(DEMON_ID_MAP.values()))

    with pytest.raises(ValueError, match="storage slot"):
        game.demons.create_from_initial(meta, 24)


def test_add_to_order_uses_first_free_slot():
    game = make_game()
    game.team.demon_order = [0xFF] * 30

    assert game.team.free_order_slots() == 30
    assert game.team.add_to_order(7) is True
    assert game.team.demon_order[0] == 7
    assert game.team.add_to_order(7) is True
    assert game.team.demon_order[0] == 7
    assert game.team.add_to_order(8) is True
    assert game.team.demon_order[1] == 8


def test_add_to_order_returns_false_when_full():
    game = make_game()
    game.team.demon_order = [0] * 30

    assert game.team.free_order_slots() == 0
    assert game.team.add_to_order(7) is False


def test_new_from_initial_sets_current_healable_stats():
    game = make_game()
    for i in range(24):
        game.demons.in_slot(i).demon_id = NO_DEMON
    meta = next(iter(DEMON_ID_MAP.values()))

    demon = game.demons.new_from_initial(meta)

    assert demon.slot < 24
    assert demon.demon_id == meta.id
    assert demon.level == meta.level
    assert demon.healable.hp == demon.stats.current.hp
    assert demon.healable.mp == demon.stats.current.mp
