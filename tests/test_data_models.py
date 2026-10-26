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
