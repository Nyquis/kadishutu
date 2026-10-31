from dataclasses import fields

from kadishutu.data.affinity import Affinity
from kadishutu.data.demons import DemonAffinities

AFFINITY_NAMES = [
    "Phys",
    "Fire",
    "Ice",
    "Elec",
    "Force",
    "Light",
    "Dark",
    "Almighty",
    "Poison",
    "Vertigo",
    "Confusion",
    "Charm",
    "Sleep",
    "Seal",
    "Stray",
    "Burn",
    "Freeze",
    "Shock",
    "Laceration",
    "Stone",
    "Mirage",
    "Mud",
]


def test_demon_affinity_columns_are_distinct():
    data = {name: "100" for name in AFFINITY_NAMES}
    data["Mirage"] = "999"

    affinities = DemonAffinities.from_data(data)

    assert len(fields(DemonAffinities)) == 21
    assert affinities.mirage is Affinity.Repel


def test_generated_miracle_metadata_matches_table():
    from kadishutu.data.miracles import (
        MIRACLE_DATA,
        MIRACLES,
        MiracleCategory,
    )

    assert len(MIRACLE_DATA) == 146
    assert len(MIRACLES) == 135
    by_id = {miracle.id: miracle for miracle in MIRACLES}

    assert by_id[1].cost == 150
    assert by_id[1].category is MiracleCategory.Supremacy
    assert by_id[1].name == "Knowledge of Tools"
    assert any(
        miracle.category is MiracleCategory.Cosmos
        for miracle in MIRACLES
    )


def test_generated_quest_metadata_is_available():
    from kadishutu.data.quests import QUEST_DATA, QUESTS

    assert len(QUEST_DATA) == 224
    assert [quest.id for quest in QUEST_DATA[:3]] == [0, 1, 2]
    assert len(QUESTS) == len(QUEST_DATA)
    assert QUESTS[1].name == "Quest 1"
