from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.game_save.affinities import (
    AILMENT_AFFINITY_NAMES,
    ELEMENTAL_AFFINITY_NAMES,
    AffinityManager,
)
from kadishutu.data.affinity import AFFINITY_MAP, Affinity
from kadishutu.data.element_icons import Element

from ..iconloader import ICON_LOADER, handle_image_loading_error
from ..shared import AppliableWidget, MComboBox
from .shared import GameScreenMixin

AFFINITY_CHOICES = [
    Affinity.Weak,
    Affinity.Neutral,
    Affinity.Resist,
    Affinity.Null,
    Affinity.Repel,
    Affinity.Drain,
]
AFFINITY_HELP = (
    "Weak · Neutral · Resist · Null · Repel · Drain. "
    "Unmapped values are shown only when present in the save."
)


class AffinityEditorScreen(QWidget, GameScreenMixin, AppliableWidget):
    def __init__(self, affinities: AffinityManager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.affinities = affinities
        self.ail_aff_map: dict[str, MComboBox] = {}
        self.elem_aff_map: dict[str, MComboBox] = {}
        self.group_titles: list[str] = []

        root = QVBoxLayout(self)
        help_label = QLabel(
            "Editing current affinities. Original stored affinities are "
            "left untouched.",
            self,
        )
        help_label.setObjectName("Muted")
        help_label.setWordWrap(True)
        root.addWidget(help_label)

        legend = QLabel(AFFINITY_HELP, self)
        legend.setObjectName("Muted")
        legend.setWordWrap(True)
        root.addWidget(legend)

        self.make_group(
            root,
            "Elemental affinities",
            ELEMENTAL_AFFINITY_NAMES,
            self.elem_aff_map,
        )
        self.make_group(
            root,
            "Ailment affinities",
            AILMENT_AFFINITY_NAMES,
            self.ail_aff_map,
        )
        root.addStretch()

    def make_group(
        self,
        root: QVBoxLayout,
        title: str,
        names: list[str],
        target: dict[str, MComboBox],
    ):
        self.group_titles.append(title)
        group = QGroupBox(title, self)
        grid = QGridLayout(group)
        for column, header_text in enumerate(("Icon", "Type", "Affinity")):
            header = QLabel(header_text, group)
            header.setObjectName("Muted")
            grid.addWidget(header, 0, column)

        for row, name in enumerate(names, 1):
            label = QLabel(name, group)
            grid.addWidget(label, row, 1)
            affinity_box = MComboBox(group)
            affinity_box.addItems(
                [affinity.name for affinity in AFFINITY_CHOICES]
            )
            affinity_box.setToolTip(AFFINITY_HELP)
            grid.addWidget(affinity_box, row, 2)
            target[name.lower()] = affinity_box

            element = Element[name]
            try:
                pak = ICON_LOADER.element_icon(element)
            except Exception as e:
                handle_image_loading_error(e, "element icon", element)
            else:
                pix = pak.pixmap.scaled(pak.size_div(2))
                icon = QLabel(group)
                icon.setFixedSize(pix.size())
                icon.setPixmap(pix)
                grid.addWidget(icon, row, 0)

        root.addWidget(group)

    @staticmethod
    def populate_box(box: MComboBox, affinity: Affinity):
        with QSignalBlocker(box):
            box.clear()
            box.addItems(
                [choice.name for choice in AFFINITY_CHOICES]
            )
            if affinity not in AFFINITY_CHOICES:
                label = f"Unmapped ({affinity.value})"
                box.addItem(label)
                box.setCurrentText(label)
            else:
                box.setCurrentText(affinity.name)
        box.set_modified(False)

    def stack_refresh(self):
        ail_aff = self.affinities.ailment
        for name, box in self.ail_aff_map.items():
            affinity: Affinity = ail_aff.__getattribute__(name)
            self.populate_box(box, affinity)
        elem_aff = self.affinities.current_elemental
        for name, box in self.elem_aff_map.items():
            affinity: Affinity = elem_aff.__getattribute__(name)
            self.populate_box(box, affinity)

    def _upd(self, aff_editor, name: str):
        def inner(value: str):
            try:
                affinity = AFFINITY_MAP[value]
            except KeyError:
                return
            aff_editor.__setattr__(name, affinity)
        return inner

    def on_apply_changes(self):
        ail_aff = self.affinities.ailment
        for name, box in self.ail_aff_map.items():
            box.update_if_modified(self._upd(ail_aff, name))
        elem_aff = self.affinities.current_elemental
        for name, box in self.elem_aff_map.items():
            box.update_if_modified(self._upd(elem_aff, name))
