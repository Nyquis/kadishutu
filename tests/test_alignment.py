from kadishutu.core.game_save import GameSaveEditor
from kadishutu.core.shared.file_handling import DecryptedSave
from kadishutu.data.alignment import ALIGNMENT_OFFSET_MAP

GAME_SAVE_SIZE = 0x6DC90


def make_game() -> GameSaveEditor:
    data = bytearray(GAME_SAVE_SIZE)
    data[0x40:0x44] = b"GVAS"
    return GameSaveEditor(DecryptedSave(data))


def test_alignment_data_includes_heart_of_garnet():
    byte = ALIGNMENT_OFFSET_MAP[0x69CFA]
    bits = {bit.bit: bit for bit in byte.bits}

    assert bits[4].alignment == "law"
    assert bits[4].side_quest == "Heart of Garnet"
    assert bits[4].place == "Da'at - Shinagawa"
    assert bits[5].alignment == "chaos"
    assert bits[5].side_quest == "Heart of Garnet"
    assert bits[5].place == "Da'at - Shinagawa"


def test_alignment_data_names_and_quest_labels_are_corrected():
    byte = ALIGNMENT_OFFSET_MAP[0x69CF8]
    bits = {bit.bit: bit for bit in byte.bits}
    assert bits[4].side_quest == "Searching for the Horn of Plenty"
    assert bits[5].side_quest == "Searching for the Horn of Plenty"

    byte = ALIGNMENT_OFFSET_MAP[0x69CFB]
    bits = {bit.bit: bit for bit in byte.bits}
    assert bits[6].text[-1] == "Defeat Kudlak"
    assert bits[7].text[-1] == "Defeat Kresnik"


def test_alignment_data_marks_unverified_alignments_as_unknown():
    byte = ALIGNMENT_OFFSET_MAP[0x69CFC]
    bits = {bit.bit: bit for bit in byte.bits}

    assert bits[2].alignment == "unknown"
    assert bits[3].alignment == "unknown"
    assert bits[2].is_unknown is True


def test_alignment_byte_unknown_bits_helpers():
    byte = ALIGNMENT_OFFSET_MAP[0x69CFA]

    assert byte.has_bit(4) is True
    assert byte.has_bit(0) is False
    assert byte.unknown_bits(0x01) == 0x01
    assert byte.unknown_bits(0x20) == 0


def test_alignment_editor_reads_and_writes_heart_of_garnet_bits():
    game = make_game()
    editor = game.alignment.at_offset(0x69CFA)

    editor.set_flag(4, True)
    assert editor.get_flag(4) is True
    assert editor.byte == 0x10

    editor.set_flag(5, True)
    assert editor.get_flag(5) is True
    assert editor.byte == 0x30

    editor.set_flag(4, False)
    assert editor.get_flag(4) is False
    assert editor.byte == 0x20
