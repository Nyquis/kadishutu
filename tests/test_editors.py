from datetime import datetime, timedelta

from kadishutu.core.game_save.affinities import AffinityEditor
from kadishutu.core.game_save.position import Vector3, Vector3Editor
from kadishutu.core.game_save.team import DemonOrderEditor
from kadishutu.core.shared.editors import (
    BaseMasterEditor,
    BaseStaticEditor,
    BoolEditor,
    TimeDeltaEditor,
    UnrealTimeEditor,
)
from kadishutu.core.shared.file_handling import DecryptedSave
from kadishutu.data.affinity import Affinity


class EditorFixture(BaseStaticEditor):
    offset = 0
    flag = BoolEditor(0)
    delta = TimeDeltaEditor(0x10)
    unreal_time = UnrealTimeEditor(0x20)
    vector = Vector3Editor(0x30)
    affinity = AffinityEditor(0x40)
    order = DemonOrderEditor(0x50)


def test_editor_value_round_trips():
    master = BaseMasterEditor(DecryptedSave(bytearray(256)))
    editor = EditorFixture(master)

    editor.flag = True
    assert editor.flag is True

    editor.delta = timedelta(seconds=123)
    assert editor.delta == timedelta(seconds=123)

    editor.unreal_time = datetime(2020, 1, 2, 3, 4, 5)
    assert editor.unreal_time == datetime(2020, 1, 2, 3, 4, 5)

    editor.vector = Vector3(1.0, 2.0, 3.0)
    assert editor.vector == Vector3(1.0, 2.0, 3.0)

    editor.affinity = Affinity.Repel
    assert editor.affinity is Affinity.Repel

    order = list(range(DemonOrderEditor.fmt.count("B")))
    editor.order = order
    assert editor.order == order
