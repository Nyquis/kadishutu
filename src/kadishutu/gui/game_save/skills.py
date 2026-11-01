from abc import abstractmethod
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.game_save.skills import (
    InnateSkillEditor,
    SkillEditor,
    SkillManager,
)
from kadishutu.data.element_icons import Element
from kadishutu.data.skills import (
    SKILL_ID_MAP,
    SKILL_NAME_MAP,
    LearnSkillType,
)

from ..advanced import advanced_mode
from ..iconloader import ICON_LOADER, handle_image_loading_error
from ..shared import (
    SHIBOKEN_MAX,
    AppliableWidget,
    MComboBox,
    ModifiedMixin,
)
from .shared import GameScreenMixin

BAD_OR_UNKNOWN_SKILL = "???"
LEARN_TYPE_HELP = (
    "Default = natural or level-up skill. "
    "Library = learned from a skill library."
)


class AbstractStrIntMap(QWidget, ModifiedMixin):
    def __init__(self, items: list[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        ModifiedMixin.__init__(self)

        self.l = QHBoxLayout(self)
        self.l.setContentsMargins(0, 0, 0, 0)

        self.str_box = QComboBox()
        self.str_box.addItems(items)
        self.str_box.currentTextChanged.connect(self.str_changed)
        self.l.addWidget(self.str_box)

        self.int_box = QSpinBox()
        self.int_box.valueChanged.connect(self.int_changed)
        self.l.addWidget(self.int_box)

    def get_value(self) -> int:
        return self.int_box.value()

    @abstractmethod
    def refresh(self):
        raise NotImplementedError

    @abstractmethod
    def apply_changes(self):
        raise NotImplementedError

    @abstractmethod
    def int_to_str(self, value: int) -> str:
        raise NotImplementedError

    @abstractmethod
    def str_to_int(self, value: str) -> int:
        raise NotImplementedError

    def int_changed(self, value: int):
        self.set_modified(True)
        self.str_box.setCurrentText(self.int_to_str(value))

    def str_changed(self, value: str):
        self.set_modified(True)
        self.int_box.setValue(self.str_to_int(value))


class SkillBox(AbstractStrIntMap, ModifiedMixin):
    NO_VALUE_INT = 0
    NO_VALUE_STR = "NONE"

    def __init__(self, skill: SkillEditor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.str_box.insertItem(0, self.NO_VALUE_STR)
        ModifiedMixin.__init__(self)
        self.skill = skill
        self.int_box.setMaximum(SHIBOKEN_MAX)

    def update_tooltip(self):
        skill_id = self.int_box.value()
        skill = SKILL_ID_MAP.get(skill_id)
        if skill is not None and skill.summary:
            tooltip = f"Skill ID: {skill_id}\n{skill.summary}"
        else:
            tooltip = f"Skill ID: {skill_id}"
        self.str_box.setToolTip(tooltip)

    def int_changed(self, value: int):
        super().int_changed(value)
        self.update_tooltip()

    def str_changed(self, value: str):
        super().str_changed(value)
        self.update_tooltip()

    def refresh(self):
        self.int_box.setValue(self.skill.id)
        if self.skill.id == self.NO_VALUE_INT:
            self.str_box.setCurrentIndex(0)
            self.update_tooltip()
            return
        try:
            skill_name = self.skill.name
        except KeyError:
            skill_name = BAD_OR_UNKNOWN_SKILL
        self.str_box.setCurrentText(skill_name)
        self.update_tooltip()

    def apply_changes(self):
        if self.get_modified():
            self.skill.id = self.int_box.value()
            self.set_modified(False)

    def int_to_str(self, value: int) -> str:
        if value == self.NO_VALUE_INT:
            return self.NO_VALUE_STR
        try:
            return SKILL_ID_MAP[value].name
        except KeyError:
            return BAD_OR_UNKNOWN_SKILL

    def str_to_int(self, value: str) -> int:
        if value == self.NO_VALUE_STR:
            return self.NO_VALUE_INT
        return SKILL_NAME_MAP[value].id


@dataclass
class SkillRow:
    skill_box: SkillBox
    learn_type_box: MComboBox | None
    icon: QLabel
    mp_cost: QLabel
    innate: bool


class SkillEditorScreen(QWidget, GameScreenMixin, AppliableWidget):
    def __init__(
        self,
        skills: SkillManager,
        innate_skill: SkillEditor,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.skills = skills
        self.rows: list[SkillRow] = []
        self.headers: list[QLabel] = []

        self.l = QVBoxLayout(self)

        top = QHBoxLayout()
        self.advanced_mode = advanced_mode()
        self.advanced_mode.changed.connect(self.set_ids_visible)
        help_label = QLabel(LEARN_TYPE_HELP, self)
        help_label.setObjectName("Muted")
        help_label.setWordWrap(True)
        top.addWidget(help_label, 1)
        self.l.addLayout(top)

        self.grid = QGridLayout()
        self.l.addLayout(self.grid)

        for column, title in enumerate(
            ("Slot", "Icon", "Skill", "MP cost", "Learn type")
        ):
            header = QLabel(title, self)
            header.setObjectName("Muted")
            if title == "Skill":
                header.setToolTip(
                    "Raw skill IDs are visible in Advanced mode."
                )
            self.grid.addWidget(header, 0, column)
            self.headers.append(header)

        all_skills = list(SKILL_NAME_MAP.keys())

        for i in range(9):
            if i == 0:
                skill = innate_skill
                slot_name = "Innate skill"
                innate = True
                learn_type_box = None
            else:
                skill = skills.slot(i - 1)
                slot_name = f"Skill {i}"
                innate = False
                learn_type_box = MComboBox(self)
                learn_type_box.addItem(
                    "Default",
                    LearnSkillType.Default.value,
                )
                learn_type_box.addItem(
                    "Library",
                    LearnSkillType.Library.value,
                )
                learn_type_box.setToolTip(LEARN_TYPE_HELP)

            slot_label = QLabel(slot_name, self)
            self.grid.addWidget(slot_label, i + 1, 0)

            icon = QLabel(self)
            self.grid.addWidget(icon, i + 1, 1)

            skill_box = SkillBox(skill, all_skills)
            self.grid.addWidget(skill_box, i + 1, 2)
            skill_box.int_box.setVisible(False)

            mp_cost = QLabel(self)
            self.grid.addWidget(mp_cost, i + 1, 3)

            if learn_type_box is None:
                learn_type_cell = QLabel("—", self)
                learn_type_cell.setObjectName("Muted")
                self.grid.addWidget(learn_type_cell, i + 1, 4)
            else:
                self.grid.addWidget(learn_type_box, i + 1, 4)

            cb = self.make_meta_refresh_callback(
                icon,
                mp_cost,
                learn_type_box,
                innate,
            )
            skill_box.int_box.valueChanged.connect(cb)
            self.rows.append(
                SkillRow(skill_box, learn_type_box, icon, mp_cost, innate)
            )

        self.set_ids_visible()
        self.stack_refresh()

    def set_ids_visible(self, *_):
        visible = self.advanced_mode.enabled
        for row in self.rows:
            row.skill_box.int_box.setVisible(visible)

    def meta_refresh(
        self,
        skill_id: int,
        icon: QLabel,
        mp_cost: QLabel,
        learn_type_box: MComboBox | None,
        innate: bool,
    ):
        if skill_id == SkillBox.NO_VALUE_INT:
            mp_cost.hide()
            icon.hide()
            if learn_type_box is not None:
                learn_type_box.hide()
            return

        icon.show()
        if innate:
            mp_cost.hide()
        else:
            mp_cost.show()
            if learn_type_box is not None:
                learn_type_box.show()

        try:
            skill_meta = SKILL_ID_MAP[skill_id]
        except KeyError:
            mp_cost.setText("MP cost: Unknown")
            element = Element.Misc
        else:
            element = skill_meta.icon
            if element == Element.Passive:
                mp_cost.setText("MP cost: N/A")
            else:
                mp_cost.setText("MP cost: " + str(skill_meta.mp_cost))
        try:
            pak = ICON_LOADER.element_icon(element)
        except Exception as e:
            handle_image_loading_error(e, "element", element)
        else:
            pix = pak.pixmap.scaled(pak.size_div(2))
            icon.setFixedSize(pix.size())
            icon.setPixmap(pix)

    def make_meta_refresh_callback(
        self,
        icon: QLabel,
        mp_cost: QLabel,
        learn_type_box: MComboBox | None,
        innate: bool,
    ):
        def inner(skill_id: int):
            return self.meta_refresh(
                skill_id,
                icon,
                mp_cost,
                learn_type_box,
                innate,
            )
        return inner

    def stack_refresh(self):
        for row in self.rows:
            row.skill_box.refresh()
            row.skill_box.set_modified(False)
            skill = row.skill_box.skill
            if isinstance(skill, InnateSkillEditor):
                self.meta_refresh(
                    skill.id,
                    row.icon,
                    row.mp_cost,
                    row.learn_type_box,
                    True,
                )
                continue
            assert row.learn_type_box is not None
            index = row.learn_type_box.findData(skill.learn_type.value)
            row.learn_type_box.setCurrentIndex(index if index >= 0 else 0)
            row.learn_type_box.set_modified(False)
            self.meta_refresh(
                skill.id,
                row.icon,
                row.mp_cost,
                row.learn_type_box,
                False,
            )

    def on_apply_changes(self):
        for row in self.rows:
            row.skill_box.apply_changes()
            if row.learn_type_box is None:
                continue
            if not row.learn_type_box.get_modified():
                continue
            row.skill_box.skill.learn_type = LearnSkillType(
                row.learn_type_box.currentData()
            )
            row.learn_type_box.set_modified(False)
