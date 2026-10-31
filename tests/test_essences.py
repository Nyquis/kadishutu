from kadishutu.core.game_save import GameSaveEditor
from kadishutu.core.game_save.essences import EssenceMetadata
from kadishutu.core.shared.file_handling import DecryptedSave

GAME_SAVE_SIZE = 0x6DC90
PIXIE_ESSENCE_ID = 351


def make_game() -> GameSaveEditor:
    data = bytearray(GAME_SAVE_SIZE)
    data[0x40:0x44] = b"GVAS"
    return GameSaveEditor(DecryptedSave(data))


def test_pixie_essence_can_be_have_and_used_together():
    game = make_game()
    essence = game.essences.from_id(PIXIE_ESSENCE_ID)
    essence.amount = 1
    essence.metadata = (
        EssenceMetadata.New
        | EssenceMetadata.Owned
        | EssenceMetadata.Used
    )

    assert essence.have is True
    assert essence.used is True
    assert essence.is_owned() is True
    assert essence.is_new() is False

    essence.used = False

    assert essence.have is True
    assert essence.metadata == EssenceMetadata.New | EssenceMetadata.Owned

    essence.have = False

    assert essence.have is False
    assert essence.amount == 0
    assert essence.used is False


def test_have_sets_new_only_for_never_obtained_essence():
    game = make_game()
    essence = game.essences.from_id(PIXIE_ESSENCE_ID)

    essence.have = True

    assert essence.amount == 1
    assert essence.metadata == EssenceMetadata.New
    assert essence.is_new() is True

    essence.used = True

    assert essence.have is True
    assert essence.used is True
    assert essence.metadata & EssenceMetadata.New
    assert essence.is_new() is False


def test_essence_flag_toggles_preserve_unknown_bits():
    game = make_game()
    essence = game.essences.from_id(PIXIE_ESSENCE_ID)
    essence.metadata = (
        EssenceMetadata.Bit0
        | EssenceMetadata.Bit3
        | EssenceMetadata.Bit5
        | EssenceMetadata.Bit6
        | EssenceMetadata.Bit7
    )
    essence.amount = 1

    essence.used = True
    essence.have = False
    essence.have = True
    essence.used = False

    assert essence.metadata == (
        EssenceMetadata.Bit0
        | EssenceMetadata.Bit3
        | EssenceMetadata.Bit5
        | EssenceMetadata.Bit6
        | EssenceMetadata.Bit7
    )


def test_absent_is_an_alias_for_used():
    assert EssenceMetadata.Absent is EssenceMetadata.Used
    assert int(EssenceMetadata.Used) == 0x10
