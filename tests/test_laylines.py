from kadishutu.core.game_save import GameSaveEditor
from kadishutu.core.shared.file_handling import DecryptedSave
from kadishutu.data.laylines import LAYLINE_ID_MAP, Layline

GAME_SAVE_SIZE = 0x6DC90


def make_game() -> GameSaveEditor:
    data = bytearray(GAME_SAVE_SIZE)
    data[0x40:0x44] = b"GVAS"
    return GameSaveEditor(DecryptedSave(data))


def test_layline_region_and_place_helpers():
    tamachi = next(
        layline
        for layline in LAYLINE_ID_MAP.values()
        if layline.name == "Da'at: Minato - Tamachi"
    )
    assert tamachi.region == "Da'at: Minato"
    assert tamachi.place == "Tamachi"

    jouin = next(
        layline
        for layline in LAYLINE_ID_MAP.values()
        if layline.name == "Jouin High School"
    )
    assert jouin.region == "Tokyo"
    assert jouin.place == "Jouin High School"


def test_layline_position_unpacks_coordinates():
    layline = LAYLINE_ID_MAP[0x0B]
    position = layline.position

    assert len(position) == 3
    assert all(isinstance(value, float) for value in position)


def test_position_helpers_use_derived_unlock_data():
    game = make_game()
    position = game.position
    layline = LAYLINE_ID_MAP[0x0B]

    assert position.is_layline_unlocked(layline) is False
    position.layline_unlock(layline)
    assert position.is_layline_unlocked(layline) is True


def test_teleport_sets_last_layline_and_unlocks_it():
    game = make_game()
    position = game.position
    layline: Layline = LAYLINE_ID_MAP[0x0B]

    position.layline_teleport(layline, unlock=True)

    assert position.last_layline is layline
    assert position.is_layline_unlocked(layline) is True
    assert position.current_map_upper == layline.map_upper
    assert position.current_map_lower == layline.map_lower
