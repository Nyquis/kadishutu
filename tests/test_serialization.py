import json
from pathlib import Path

import pytest

from kadishutu.data.alignment import ALIGNMENT_DATA, AlignmentBit, AlignmentByte
from kadishutu.data.element_icons import Element
from kadishutu.data.items import ITEM_EXTRA_DATA, ItemExtraData
from kadishutu.data.laylines import LAYLINE_DATA, Layline, LaylineUnlock
from kadishutu.data.miracle_unlocks import MIRACLE_UNLOCKS, MiracleUnlock
from kadishutu.data.miracles import MIRACLE_TEXT_DATA, MiracleText
from kadishutu.plugin.meta import PluginInfo

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def assert_round_trip(obj):
    cls = type(obj)
    assert cls.from_dict(obj.to_dict()) == obj
    assert cls.from_json(obj.to_json()) == obj


def test_alignment_round_trip():
    obj = AlignmentByte(
        offset=0x69CF5,
        bits=[
            AlignmentBit(
                bit=2,
                alignment="law",
                place="The Empyrean",
                side_quest=None,
                text=["Choose the law choice (?)"],
            )
        ],
    )
    assert_round_trip(obj)
    assert obj.has_bit(2)


def test_alignment_golden():
    obj = AlignmentByte(
        offset=0x69CF5,
        bits=[
            AlignmentBit(
                bit=2,
                alignment="law",
                place="The Empyrean",
                side_quest=None,
                text=["Choose the law choice (?)"],
            )
        ],
    )
    expected = json.loads((GOLDEN_DIR / "alignment_byte.json").read_text())
    assert obj.to_dict() == expected


def test_layline_round_trip():
    obj = Layline(
        id=0x0B,
        name="Da'at: Minato - Tamachi",
        map_upper=0x3D,
        map_lower=0,
        coordinates=bytes.fromhex("f75144c54fc26647109c8844"),
        rotation=bytes.fromhex("89f67fbfc0368b3c"),
        unlock=LaylineUnlock(offset=0x80A3, bit=3),
    )
    assert_round_trip(obj)


def test_layline_golden():
    obj = Layline(
        id=0x0B,
        name="Da'at: Minato - Tamachi",
        map_upper=0x3D,
        map_lower=0,
        coordinates=bytes.fromhex("f75144c54fc26647109c8844"),
        rotation=bytes.fromhex("89f67fbfc0368b3c"),
        unlock=LaylineUnlock(offset=0x80A3, bit=3),
    )
    expected = json.loads((GOLDEN_DIR / "layline.json").read_text())
    assert obj.to_dict() == expected


def test_miracle_round_trip():
    obj = MiracleText(id=0x01, name="Knowledge of Tools")
    assert_round_trip(obj)
    assert obj.to_dict()["id"] == "0x01"
    assert obj.to_dict()["desc"] is None


def test_item_extra_round_trip():
    obj = ItemExtraData(
        id=1,
        limit=50,
        icon=Element(10),
        desc="Slight HP recovery to 1 ally.",
    )
    assert_round_trip(obj)
    assert obj.to_dict()["icon"] == 10


def test_miracle_unlock_round_trip():
    obj = MiracleUnlock(
        id=0x67A3,
        name="Minato - Mita",
        miracles=["Art of Essences I", "Divine Garrison I"],
    )
    assert_round_trip(obj)
    assert obj.to_dict()["id"] == "0x67a3"


def test_plugin_manifest():
    info = PluginInfo.from_path(
        REPO_ROOT / "examples" / "plugin_example_gui" / "manifest.json"
    )
    assert info.name == "plugin_example_gui"
    assert info.stage == "gui"
    assert info.load_order == 0


@pytest.mark.parametrize(
    "items",
    [
        ALIGNMENT_DATA,
        ITEM_EXTRA_DATA,
        LAYLINE_DATA,
        MIRACLE_TEXT_DATA,
        MIRACLE_UNLOCKS,
    ],
    ids=[
        "alignment",
        "items",
        "laylines",
        "miracles",
        "miracle_unlocks",
    ],
)
def test_all_data_files_round_trip(items):
    for item in items:
        assert type(item).from_dict(item.to_dict()) == item
