from kadishutu.core.game_save.game import detected_canon
from kadishutu.data.quests import QUEST_CANON_MAP, QUESTS


def test_quest_canon_map_uses_only_known_canons():
    assert set(QUEST_CANON_MAP.values()) <= {"creation", "vengeance"}


def test_quest_canon_map_references_existing_quests():
    known = {quest.id for quest in QUESTS}
    assert set(QUEST_CANON_MAP) <= known


def test_quest_canon_marks_known_exclusive_quests():
    # Names fall back to "Quest N" without a game data export, so map by id.
    assert QUEST_CANON_MAP[172] == "vengeance"  # Rite of Resurrection
    assert QUEST_CANON_MAP[40] == "creation"  # The Egyptians' Fate


def test_quest_canon_is_partial():
    # The map only covers canon-exclusive quests; shared quests stay untagged.
    assert 0 < len(QUEST_CANON_MAP) < len(QUESTS)
    assert QUEST_CANON_MAP.get(0) is None


def test_detected_canon_reads_the_save_screen_field():
    data = bytearray(0x600)

    data[0x53A] = 1
    assert detected_canon(data) == "creation"
    data[0x53A] = 2
    assert detected_canon(data) == "vengeance"
    data[0x53A] = 0
    assert detected_canon(data) is None


def test_detected_canon_tolerates_short_data():
    assert detected_canon(bytearray(1)) is None
