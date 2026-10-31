from PySide6.QtGui import QValidator
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.game_save.potentials import PotentialEditor, PotentialType
from kadishutu.data.element_icons import Element

from ..iconloader import ICON_LOADER, handle_image_loading_error
from ..shared import AppliableWidget, ModifiedMixin
from .shared import GameScreenMixin

POTENTIAL_HELP = (
    "Higher is better. Range -9 to +9; 0 means no bonus. "
    "Potentials modify damage and healing for this skill family."
)
ELEMENTAL_POTENTIALS = (
    PotentialType.Physical,
    PotentialType.Fire,
    PotentialType.Ice,
    PotentialType.Electric,
    PotentialType.Force,
    PotentialType.Light,
    PotentialType.Dark,
    PotentialType.Almighty,
)
OTHER_POTENTIALS = (
    PotentialType.Ailment,
    PotentialType.Support,
    PotentialType.Recovery,
)


class QPotentialBox(QSpinBox, ModifiedMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimum(-9)
        self.setMaximum(9)
        self.setFixedWidth(90)
        self.valueChanged.connect(self.flag_as_modified)

    def get_value(self) -> int:
        return self.value()

    def textFromValue(self, value: int) -> str:
        if value > 0:
            return f"+{value}"
        return str(value)

    def valueFromText(self, text: str) -> int:
        text = text.strip()
        if text.startswith("+"):
            text = text[1:]
        try:
            return int(text)
        except ValueError:
            return 0

    def validate(self, text: str, pos: int):
        stripped = text.strip()
        if stripped in ("", "+", "-"):
            return QValidator.Intermediate, text, pos
        body = stripped[1:] if stripped[0] in "+-" else stripped
        if body.isdigit() and int(body) <= 9:
            return QValidator.Acceptable, text, pos
        return QValidator.Invalid, text, pos


class PotentialEditorScreen(QWidget, GameScreenMixin, AppliableWidget):
    def __init__(self, potentials: PotentialEditor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.potentials = potentials
        self.potential_map: dict[PotentialType, QPotentialBox] = {}
        self.group_titles: list[str] = []

        root = QVBoxLayout(self)
        help_label = QLabel(POTENTIAL_HELP, self)
        help_label.setObjectName("Muted")
        help_label.setWordWrap(True)
        root.addWidget(help_label)

        self.make_group(
            root,
            "Elemental potentials",
            ELEMENTAL_POTENTIALS,
        )
        self.make_group(
            root,
            "Other potentials",
            OTHER_POTENTIALS,
        )
        root.addStretch()

    def make_group(
        self,
        root: QVBoxLayout,
        title: str,
        potential_types: tuple[PotentialType, ...],
    ):
        self.group_titles.append(title)
        group = QGroupBox(title, self)
        grid = QGridLayout(group)
        for column, header_text in enumerate(("Icon", "Type", "Potential")):
            header = QLabel(header_text, group)
            header.setObjectName("Muted")
            grid.addWidget(header, 0, column)

        for row, ptype in enumerate(potential_types, 1):
            label = QLabel(ptype.name, group)
            label.setToolTip(POTENTIAL_HELP)
            grid.addWidget(label, row, 1)

            potential_box = QPotentialBox(group)
            potential_box.setToolTip(POTENTIAL_HELP)
            grid.addWidget(potential_box, row, 2)
            self.potential_map[ptype] = potential_box

            elname = (
                Element.Misc
                if ptype.name == "_UNKNOWN"
                else Element[ptype.name]
            )
            try:
                pak = ICON_LOADER.element_icon(elname)
            except Exception as e:
                handle_image_loading_error(e, "element", elname)
            else:
                pix = pak.pixmap.scaled(pak.size_div(2))
                icon = QLabel(group)
                icon.setFixedSize(pix.size())
                icon.setPixmap(pix)
                grid.addWidget(icon, row, 0)

        root.addWidget(group)

    def stack_refresh(self):
        for ptype, potential_box in self.potential_map.items():
            potential_box.setValue(self.potentials.read(ptype))
            potential_box.set_modified(False)

    def on_apply_changes(self):
        for ptype, potential_box in self.potential_map.items():
            potential_box.update_if_modified(
                lambda x, ptype=ptype: self.potentials.write(ptype, x)
            )
