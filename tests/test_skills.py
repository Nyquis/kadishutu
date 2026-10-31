from kadishutu.core.game_save import GameSaveEditor
from kadishutu.core.game_save.skills import InnateSkillEditor
from kadishutu.core.shared.file_handling import DecryptedSave
from kadishutu.data.skills import SKILL_ID_MAP, LearnSkillType

GAME_SAVE_SIZE = 0x6DC90


def make_game() -> GameSaveEditor:
    data = bytearray(GAME_SAVE_SIZE)
    data[0x40:0x44] = b"GVAS"
    return GameSaveEditor(DecryptedSave(data))


def test_skill_slot_learn_type_round_trips():
    game = make_game()
    skill = game.demons.in_slot(0).skills.slot(0)

    skill.id = 491
    skill.learn_type = LearnSkillType.Library

    assert skill.id == 491
    assert skill.learn_type is LearnSkillType.Library

    skill.learn_type = LearnSkillType.Default

    assert skill.learn_type is LearnSkillType.Default


def test_skill_mechanics_summaries_are_generated():
    agi = SKILL_ID_MAP[1]
    fire_pleroma = SKILL_ID_MAP[491]

    assert "Magic attack" in agi.summary
    assert "Fire" in agi.summary
    assert "130 power" in agi.summary
    assert "10 MP" in agi.summary
    assert fire_pleroma.summary == "Passive skill"


def test_innate_skill_has_no_learn_type_slot():
    game = make_game()
    innate = game.demons.in_slot(0).innate_skill
    assert isinstance(innate, InnateSkillEditor)

    innate.id = 669

    assert innate.id == 669
    assert innate.learn_type is None
