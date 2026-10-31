import pytest

from kadishutu.core.game_save import GameSaveEditor
from kadishutu.core.game_save.demons import NO_DEMON
from kadishutu.core.shared.file_handling import DecryptedSave

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
