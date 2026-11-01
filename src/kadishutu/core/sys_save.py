import struct
from enum import Enum, auto

from .shared.editors import (
    BaseMasterEditor,
    BoolEditor,
    EditorGetter,
    EnumEditor,
    U8Editor,
)


class CameraMode(Enum):
    Standard = 0
    Reverse = 1
    Off = 2


class Visibility(Enum):
    Display = 0
    Hide = 1
    HideWhenMoving = 2


class MessageSpeed(Enum):
    Slow = 0
    Normal = auto()
    Fast = auto()


class CameraSpeed(Enum):
    VerySlow = 0
    Slow = auto()
    Standard = auto()
    Fast = auto()
    VeryFast = auto()
    Fastest = auto()


class StickAction(Enum):
    NoneAction = 0
    ContinuousDash = auto()
    ResetCamera = auto()


class AutoBattleType(Enum):
    AutoAttack = 0
    AutoSkill = auto()
    ChooseAtStart = auto()


class SkillAnimationSpeed(Enum):
    Standard = 0
    DoubleSpeed = auto()
    MaxSpeed = auto()
    Skip = auto()


class SkipEventButton(Enum):
    Plus = 0
    X = auto()


class CameraAngle(Enum):
    Narrow = 0
    Standard = auto()
    Unknown = auto()
    Wide = auto()


class ConfirmAction(Enum):
    A = 0
    B = auto()


class VoiceLanguage(Enum):
    Japanese = 0
    English = auto()


class InvertedBoolEditor(BoolEditor):
    def read(self) -> bool:
        return not super().read()

    def write(self, v: int) -> None:
        super().write(int(not v))


class BFloat16Editor(EditorGetter):
    """Read/write a normalized 0..1 value stored as bfloat16."""

    def read(self) -> float:
        raw = int.from_bytes(
            self.data[self.offset:self.offset + 2],
            "little",
        )
        return struct.unpack("<f", struct.pack("<I", raw << 16))[0]

    def write(self, value: float):
        value = max(0.0, min(1.0, value))
        raw = struct.unpack("<H", struct.pack("<f", value)[2:4])[0]
        self.data[self.offset:self.offset + 2] = raw.to_bytes(2, "little")


class SysSaveEditor(BaseMasterEditor):
    # Audio
    voice_volume = BFloat16Editor(0x5E0)
    bgm_volume = BFloat16Editor(0x5E4)
    ambient_volume = BFloat16Editor(0x5E8)
    sfx_volume = BFloat16Editor(0x5EC)

    # Camera
    camera_horizontal = EnumEditor(0x5F6, CameraMode)
    camera_vertical = EnumEditor(0x5F7, CameraMode)
    camera_speed = EnumEditor(0x61C, CameraSpeed)
    camera_angle = EnumEditor(0x1227, CameraAngle)

    # Messages
    message_speed = EnumEditor(0x5FF, MessageSpeed)
    message_auto_advance = BoolEditor(0x1220)
    subtitles = InvertedBoolEditor(0x1221)
    skip_event_button = EnumEditor(0x1225, SkipEventButton)

    # Display
    minimap_display = EnumEditor(0x600, Visibility)
    party_panels_field = EnumEditor(0x601, Visibility)
    help_display = EnumEditor(0x602, Visibility)
    party_panels_skills = InvertedBoolEditor(0x606)
    magatsuhi_gauge_display = EnumEditor(0x1228, Visibility)
    minimap_rotation = InvertedBoolEditor(0x1229)
    obstacle_opacity = InvertedBoolEditor(0x122D)
    field_brightness = U8Editor(0x1233)
    screen_brightness = U8Editor(0x125C)
    ambient_occlusion = InvertedBoolEditor(0x1234)
    motion_blur = InvertedBoolEditor(0x1235)
    anti_aliasing = InvertedBoolEditor(0x1236)
    pause_when_resuming = InvertedBoolEditor(0x125D)

    # Battle
    battle_cursor_memory = InvertedBoolEditor(0x604)
    auto_battle_confirmation = InvertedBoolEditor(0x605)
    battle_item_sorting = InvertedBoolEditor(0x122E)
    auto_battle_type = EnumEditor(0x122F, AutoBattleType)
    skill_animation_speed = EnumEditor(0x1230, SkillAnimationSpeed)
    auto_battle_skill_animation_speed = EnumEditor(
        0x1231,
        SkillAnimationSpeed,
    )
    skip_skill_animations = BoolEditor(0x1232)
    estoma_field_confirmation = InvertedBoolEditor(0x122C)

    # Controls
    stick_sensitivity = U8Editor(0x1222)
    l_stick_action = EnumEditor(0x122A, StickAction)
    r_stick_action = EnumEditor(0x122B, StickAction)
    confirm_action = EnumEditor(0x125E, ConfirmAction)

    # Other
    voice_language = EnumEditor(0x61B, VoiceLanguage)
    mitama_glory = BoolEditor(0x608)
    mitama_wealth = BoolEditor(0x609)
    mitama_exp = BoolEditor(0x60A)
