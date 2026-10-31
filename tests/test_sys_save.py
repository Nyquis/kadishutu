from kadishutu.core.shared.file_handling import DecryptedSave
from kadishutu.core.sys_save import (
    AutoBattleType,
    CameraMode,
    CameraSpeed,
    ConfirmAction,
    MessageSpeed,
    SkillAnimationSpeed,
    SkipEventButton,
    StickAction,
    SysSaveEditor,
    Visibility,
    VoiceLanguage,
)

SYS_SAVE_SIZE = 0x12E0


def make_sys_save() -> DecryptedSave:
    data = bytearray(SYS_SAVE_SIZE)
    data[0x40:0x44] = b"GVAS"
    return DecryptedSave(data)


def test_bfloat16_volume_round_trip():
    raw = make_sys_save()
    save = SysSaveEditor(raw)

    save.voice_volume = 1.0
    assert raw.data[0x5E0:0x5E2] == b"\x80\x3f"
    assert save.voice_volume == 1.0

    save.voice_volume = 0.5
    assert 0.49 < save.voice_volume < 0.51


def test_inverted_boolean_round_trip():
    raw = make_sys_save()
    save = SysSaveEditor(raw)

    raw.data[0x1221] = 0
    assert save.subtitles is True
    save.subtitles = False
    assert raw.data[0x1221] == 1

    raw.data[0x1234] = 0
    assert save.ambient_occlusion is True
    save.ambient_occlusion = False
    assert raw.data[0x1234] == 1


def test_sys_save_enums_and_numbers():
    raw = make_sys_save()
    save = SysSaveEditor(raw)

    save.camera_horizontal = CameraMode.Reverse
    assert save.camera_horizontal is CameraMode.Reverse

    save.camera_speed = CameraSpeed.Fast
    assert save.camera_speed is CameraSpeed.Fast

    save.message_speed = MessageSpeed.Fast
    assert save.message_speed is MessageSpeed.Fast

    save.skip_event_button = SkipEventButton.X
    assert save.skip_event_button is SkipEventButton.X

    save.minimap_display = Visibility.HideWhenMoving
    assert save.minimap_display is Visibility.HideWhenMoving

    save.auto_battle_type = AutoBattleType.ChooseAtStart
    assert save.auto_battle_type is AutoBattleType.ChooseAtStart

    save.skill_animation_speed = SkillAnimationSpeed.Skip
    assert save.skill_animation_speed is SkillAnimationSpeed.Skip

    save.l_stick_action = StickAction.ResetCamera
    assert save.l_stick_action is StickAction.ResetCamera

    save.confirm_action = ConfirmAction.B
    assert save.confirm_action is ConfirmAction.B

    save.voice_language = VoiceLanguage.English
    assert save.voice_language is VoiceLanguage.English

    save.field_brightness = 7
    assert save.field_brightness == 7
