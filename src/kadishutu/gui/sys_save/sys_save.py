from enum import Enum

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.sys_save import (
    AutoBattleType,
    CameraAngle,
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

from ..components import PageHeader
from ..shared import (
    QU8,
    AppliableWidget,
    MCheckBox,
    MComboBox,
    ModifiedMixin,
    SaveScreenMixin,
)

ENUM_LABELS = {
    "Standard": "Standard",
    "Reverse": "Reverse",
    "Off": "Off",
    "Display": "Display",
    "Hide": "Hide",
    "HideWhenMoving": "Hide when moving",
    "Slow": "Slow",
    "Normal": "Normal",
    "Fast": "Fast",
    "VerySlow": "Very Slow",
    "VeryFast": "Very Fast",
    "Fastest": "Fastest",
    "NoneAction": "None",
    "ContinuousDash": "Continuous dash",
    "ResetCamera": "Reset camera",
    "AutoAttack": "Auto-Attack",
    "AutoSkill": "Auto-Skill",
    "ChooseAtStart": "Choose at Start",
    "DoubleSpeed": "Double Speed",
    "MaxSpeed": "Max Speed",
    "Skip": "Skip",
    "Plus": "+",
    "X": "X",
    "Narrow": "Narrow",
    "Wide": "Wide",
    "Unknown": "Unknown",
    "A": "A",
    "B": "B",
    "Japanese": "Japanese",
    "English": "English",
}


class MVolumeSlider(QSlider, ModifiedMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setRange(0, 100)
        self.valueChanged.connect(self.flag_as_modified)

    def get_value(self) -> int:
        return self.value()


class SysSaveEditorScreen(SaveScreenMixin, QWidget, AppliableWidget):
    can_save = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.save = SysSaveEditor(self.raw_save)
        self.enum_controls: list[tuple[MComboBox, str, type[Enum]]] = []
        self.bool_controls: list[tuple[MCheckBox, str]] = []
        self.number_controls: list[tuple[QU8, str]] = []
        self.volume_controls: list[
            tuple[MVolumeSlider, QLabel, str]
        ] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("ScrollContent")
        scroll.setWidget(content)
        outer.addWidget(scroll)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(
            PageHeader("System Settings", str(self.path), content)
        )

        warning = QLabel(
            "These settings are stored in SysSave.sav and affect all game "
            "saves. Back up the file before making changes.",
            content,
        )
        warning.setObjectName("Warning")
        warning.setWordWrap(True)
        layout.addWidget(warning)

        self.add_audio_section(layout, content)
        self.add_camera_section(layout, content)
        self.add_messages_section(layout, content)
        self.add_display_section(layout, content)
        self.add_battle_section(layout, content)
        self.add_controls_section(layout, content)
        self.add_other_section(layout, content)
        layout.addStretch()

        self.stack_refresh()

    def add_section(
        self,
        parent: QVBoxLayout,
        title: str,
        widget_parent: QWidget,
    ) -> QFormLayout:
        group = QGroupBox(title, widget_parent)
        form = QFormLayout(group)
        form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        parent.addWidget(group)
        return form

    def add_enum(
        self,
        form: QFormLayout,
        label: str,
        field: str,
        enum_type: type[Enum],
        tooltip: str,
    ):
        combo = MComboBox()
        for member in enum_type:
            combo.addItem(
                ENUM_LABELS.get(member.name, member.name),
                member.value,
            )
        combo.setToolTip(tooltip)
        form.addRow(label, combo)
        self.enum_controls.append((combo, field, enum_type))

    def add_bool(
        self,
        form: QFormLayout,
        label: str,
        field: str,
        tooltip: str,
    ):
        box = MCheckBox()
        box.setToolTip(tooltip)
        form.addRow(label, box)
        self.bool_controls.append((box, field))

    def add_number(
        self,
        form: QFormLayout,
        label: str,
        field: str,
        maximum: int,
        tooltip: str,
    ):
        box = QU8()
        box.setMaximum(maximum)
        box.setFixedWidth(90)
        box.setToolTip(tooltip)
        form.addRow(label, box)
        self.number_controls.append((box, field))

    def add_volume(
        self,
        form: QFormLayout,
        label: str,
        field: str,
    ):
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        slider = MVolumeSlider(container)
        value_label = QLabel("100%", container)
        value_label.setFixedWidth(48)
        slider.valueChanged.connect(
            lambda value, label=value_label: label.setText(f"{value}%")
        )
        row.addWidget(slider, 1)
        row.addWidget(value_label)
        form.addRow(label, container)
        self.volume_controls.append((slider, value_label, field))

    def add_audio_section(
        self,
        layout: QVBoxLayout,
        parent: QWidget,
    ):
        form = self.add_section(layout, "Audio", parent)
        self.add_volume(form, "Voice volume", "voice_volume")
        self.add_volume(form, "BGM volume", "bgm_volume")
        self.add_volume(form, "Ambient volume", "ambient_volume")
        self.add_volume(form, "SFX volume", "sfx_volume")

    def add_camera_section(
        self,
        layout: QVBoxLayout,
        parent: QWidget,
    ):
        form = self.add_section(layout, "Camera", parent)
        self.add_enum(
            form,
            "Horizontal camera",
            "camera_horizontal",
            CameraMode,
            "Horizontal camera movement.",
        )
        self.add_enum(
            form,
            "Vertical camera",
            "camera_vertical",
            CameraMode,
            "Vertical camera movement.",
        )
        self.add_enum(
            form,
            "Camera speed",
            "camera_speed",
            CameraSpeed,
            "Camera rotation speed.",
        )
        self.add_enum(
            form,
            "Camera angle",
            "camera_angle",
            CameraAngle,
            "Field-of-view preset.",
        )

    def add_messages_section(
        self,
        layout: QVBoxLayout,
        parent: QWidget,
    ):
        form = self.add_section(layout, "Messages", parent)
        self.add_enum(
            form,
            "Message speed",
            "message_speed",
            MessageSpeed,
            "Text speed.",
        )
        self.add_bool(
            form,
            "Auto-advance messages",
            "message_auto_advance",
            "Advance dialogue automatically.",
        )
        self.add_bool(
            form,
            "Subtitles",
            "subtitles",
            "Show subtitles during voiced dialogue.",
        )
        self.add_enum(
            form,
            "Skip event button",
            "skip_event_button",
            SkipEventButton,
            "Button used to skip events.",
        )

    def add_display_section(
        self,
        layout: QVBoxLayout,
        parent: QWidget,
    ):
        form = self.add_section(layout, "Display", parent)
        self.add_enum(
            form,
            "Minimap display",
            "minimap_display",
            Visibility,
            "Minimap visibility.",
        )
        self.add_enum(
            form,
            "Party panels in field",
            "party_panels_field",
            Visibility,
            "Party panel visibility outside battle.",
        )
        self.add_enum(
            form,
            "Help display",
            "help_display",
            Visibility,
            "Help text visibility.",
        )
        self.add_bool(
            form,
            "Party panels during skills",
            "party_panels_skills",
            "Show party panels while selecting skills.",
        )
        self.add_enum(
            form,
            "Magatsuhi gauge display",
            "magatsuhi_gauge_display",
            Visibility,
            "Magatsuhi gauge visibility.",
        )
        self.add_bool(
            form,
            "Rotate minimap",
            "minimap_rotation",
            "Rotate the minimap with the camera.",
        )
        self.add_bool(
            form,
            "Obstacle opacity",
            "obstacle_opacity",
            "Reduce obstacle opacity.",
        )
        self.add_number(
            form,
            "Field brightness",
            "field_brightness",
            10,
            "Field brightness from 0 to 10.",
        )
        self.add_number(
            form,
            "Screen brightness",
            "screen_brightness",
            10,
            "Overall screen brightness from 0 to 10.",
        )
        self.add_bool(
            form,
            "Ambient occlusion",
            "ambient_occlusion",
            "Enable ambient occlusion.",
        )
        self.add_bool(
            form,
            "Motion blur",
            "motion_blur",
            "Enable motion blur.",
        )
        self.add_bool(
            form,
            "Anti-aliasing",
            "anti_aliasing",
            "Enable anti-aliasing.",
        )
        self.add_bool(
            form,
            "Pause when resuming",
            "pause_when_resuming",
            "Pause when returning from the background.",
        )

    def add_battle_section(
        self,
        layout: QVBoxLayout,
        parent: QWidget,
    ):
        form = self.add_section(layout, "Battle", parent)
        self.add_bool(
            form,
            "Remember battle cursor",
            "battle_cursor_memory",
            "Remember the last battle command.",
        )
        self.add_bool(
            form,
            "Confirm auto-battle",
            "auto_battle_confirmation",
            "Ask before starting auto-battle.",
        )
        self.add_bool(
            form,
            "Battle item sorting",
            "battle_item_sorting",
            "Sort battle items.",
        )
        self.add_enum(
            form,
            "Auto-battle type",
            "auto_battle_type",
            AutoBattleType,
            "Default auto-battle behavior.",
        )
        self.add_enum(
            form,
            "Skill animation speed",
            "skill_animation_speed",
            SkillAnimationSpeed,
            "Normal skill animation speed.",
        )
        self.add_enum(
            form,
            "Auto-battle animation speed",
            "auto_battle_skill_animation_speed",
            SkillAnimationSpeed,
            "Skill animation speed during auto-battle.",
        )
        self.add_bool(
            form,
            "Skip skill animations",
            "skip_skill_animations",
            "Skip skill animations using the confirm button.",
        )
        self.add_bool(
            form,
            "Estoma field confirmation",
            "estoma_field_confirmation",
            "Ask before using Estoma in the field.",
        )

    def add_controls_section(
        self,
        layout: QVBoxLayout,
        parent: QWidget,
    ):
        form = self.add_section(layout, "Controls", parent)
        self.add_number(
            form,
            "Stick sensitivity",
            "stick_sensitivity",
            10,
            "Analogue stick sensitivity from 0 to 10.",
        )
        self.add_enum(
            form,
            "L stick action",
            "l_stick_action",
            StickAction,
            "Action bound to the L stick.",
        )
        self.add_enum(
            form,
            "R stick action",
            "r_stick_action",
            StickAction,
            "Action bound to the R stick.",
        )
        self.add_enum(
            form,
            "Confirm action",
            "confirm_action",
            ConfirmAction,
            "Button used to confirm.",
        )

    def add_other_section(
        self,
        layout: QVBoxLayout,
        parent: QWidget,
    ):
        form = self.add_section(layout, "Other", parent)
        self.add_enum(
            form,
            "Voice language",
            "voice_language",
            VoiceLanguage,
            "Language used for voiced dialogue.",
        )
        self.add_bool(
            form,
            "Mitama Dance of Glory",
            "mitama_glory",
            "Enable the Mitama Dance of Glory.",
        )
        self.add_bool(
            form,
            "Mitama Dance of Wealth",
            "mitama_wealth",
            "Enable the Mitama Dance of Wealth.",
        )
        self.add_bool(
            form,
            "Mitama Dance of EXP",
            "mitama_exp",
            "Enable the Mitama Dance of EXP.",
        )

    def stack_refresh(self):
        for combo, field, _enum_type in self.enum_controls:
            combo.setCurrentIndex(
                combo.findData(getattr(self.save, field).value)
            )
            combo.set_modified(False)
        for box, field in self.bool_controls:
            box.setChecked(getattr(self.save, field))
            box.set_modified(False)
        for box, field in self.number_controls:
            box.setValue(getattr(self.save, field))
            box.set_modified(False)
        for slider, label, field in self.volume_controls:
            value = round(getattr(self.save, field) * 100)
            slider.setValue(value)
            label.setText(f"{value}%")
            slider.set_modified(False)

    def on_apply_changes(self):
        for combo, field, enum_type in self.enum_controls:
            if not combo.get_modified():
                continue
            setattr(self.save, field, enum_type(combo.currentData()))
            combo.set_modified(False)
        for box, field in self.bool_controls:
            box.setattr_if_modified(self.save, field)
        for box, field in self.number_controls:
            box.setattr_if_modified(self.save, field)
        for slider, _, field in self.volume_controls:
            if slider.get_modified():
                setattr(self.save, field, slider.value() / 100)
                slider.set_modified(False)
