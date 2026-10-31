from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.game_save.game import Endings
from kadishutu.data.endings import ENDING_INFOS, ENDING_ROUTES

from ..shared import QU8, AppliableWidget, MCheckBox
from .shared import GameScreenMixin


class CrossCycleEditorScreen(QWidget, GameScreenMixin, AppliableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ending_map: dict[Endings, MCheckBox] = {}
        self.ending_details = [
            (Endings(info.flag), info)
            for info in ENDING_INFOS
        ]

        root = QVBoxLayout(self)
        root.setSpacing(12)

        warning = QLabel(
            "These values affect New Game+ and ending state. Back up your "
            "save before editing them.",
            self,
        )
        warning.setObjectName("Warning")
        warning.setWordWrap(True)
        root.addWidget(warning)

        self.copy_warning = QLabel(self)
        self.copy_warning.setObjectName("Warning")
        self.copy_warning.setWordWrap(True)
        self.copy_warning.setVisible(False)
        root.addWidget(self.copy_warning)

        save_group = QGroupBox("Save state", self)
        save_layout = QGridLayout(save_group)

        clear_label = QLabel("Game cleared", save_group)
        clear_label.setToolTip(
            "Inferred clear-save flag. This marks the save as cleared."
        )
        save_layout.addWidget(clear_label, 0, 0)
        self.clear_box = MCheckBox(save_group)
        self.clear_box.setToolTip(clear_label.toolTip())
        save_layout.addWidget(self.clear_box, 0, 1)

        cycles_label = QLabel("Cycles", save_group)
        cycles_label.setToolTip(
            "New Game+ cycle count. The game caps this at 99."
        )
        save_layout.addWidget(cycles_label, 1, 0)
        self.cycles_box = QU8(save_group)
        self.cycles_box.setMaximum(99)
        self.cycles_box.setToolTip(cycles_label.toolTip())
        save_layout.addWidget(self.cycles_box, 1, 1)
        cycles_hint = QLabel("New Game+ cycle count, max 99", save_group)
        cycles_hint.setObjectName("Muted")
        save_layout.addWidget(cycles_hint, 1, 2)
        root.addWidget(save_group)

        endings_group = QGroupBox("Endings achieved", self)
        endings_layout = QVBoxLayout(endings_group)
        self.endings_summary = QLabel(endings_group)
        self.endings_summary.setObjectName("Muted")
        endings_layout.addWidget(self.endings_summary)

        for route in ENDING_ROUTES:
            route_label = QLabel(route, endings_group)
            route_label.setStyleSheet("font-weight: 600; margin-top: 4px;")
            endings_layout.addWidget(route_label)
            route_layout = QGridLayout()
            row = 0
            for flag, info in self.ending_details:
                if info.route != route:
                    continue
                box = MCheckBox(endings_group)
                box.setToolTip(info.description)
                box.checkStateChanged.connect(
                    lambda _: self.update_endings_summary()
                )
                label = QLabel(info.label, endings_group)
                label.setToolTip(info.description)
                route_layout.addWidget(label, row, 0)
                route_layout.addWidget(box, row, 1)
                self.ending_map[flag] = box
                row += 1
            endings_layout.addLayout(route_layout)

        buttons = QHBoxLayout()
        self.mark_all_button = QPushButton("Mark all endings", endings_group)
        self.mark_all_button.clicked.connect(self.mark_all_endings)
        buttons.addWidget(self.mark_all_button)
        self.clear_all_button = QPushButton("Clear all endings", endings_group)
        self.clear_all_button.clicked.connect(self.clear_all_endings)
        buttons.addWidget(self.clear_all_button)
        buttons.addStretch()
        endings_layout.addLayout(buttons)
        root.addWidget(endings_group)

        late_group = QGroupBox("Late-game flags", self)
        late_layout = QGridLayout(late_group)
        satan_label = QLabel("Satan beaten", late_group)
        satan_label.setToolTip(
            "Late-game flag associated with Satan and NG+ progression."
        )
        late_layout.addWidget(satan_label, 0, 0)
        self.satan_box = MCheckBox(late_group)
        self.satan_box.setToolTip(satan_label.toolTip())
        late_layout.addWidget(self.satan_box, 0, 1)
        root.addWidget(late_group)
        root.addStretch()

        self.update_endings_summary()

    def update_endings_summary(self):
        achieved = sum(
            1
            for box in self.ending_map.values()
            if box.isChecked()
        )
        self.endings_summary.setText(
            f"{achieved} / {len(self.ending_map)} endings marked"
        )

    def update_copy_warning(self):
        mismatched = (
            self.save.cycles != self.save.cycles_copy
            or self.save.endings != self.save.endings_copy
        )
        self.copy_warning.setVisible(mismatched)
        if mismatched:
            self.copy_warning.setText(
                "The header copies of cycles/endings differ from the "
                "editable values. Applying changes will sync them."
            )

    def mark_all_endings(self):
        for box in self.ending_map.values():
            box.setChecked(True)
        self.update_endings_summary()

    def clear_all_endings(self):
        for box in self.ending_map.values():
            box.setChecked(False)
        self.update_endings_summary()

    def stack_refresh(self):
        self.clear_box.setChecked(self.save.clear_flag)
        self.clear_box.set_modified(False)
        self.cycles_box.setValue(self.save.cycles)
        self.cycles_box.set_modified(False)
        for flag, box in self.ending_map.items():
            box.setChecked(bool(self.save.endings & flag))
            box.set_modified(False)
        self.satan_box.setChecked(
            self.save.miracle_unlocks.extras.satan_beaten
        )
        self.satan_box.set_modified(False)
        self.update_endings_summary()
        self.update_copy_warning()

    def on_apply_changes(self):
        self.clear_box.setattr_if_modified(self.save, "clear_flag")
        self.cycles_box.setattr_if_modified(self.save, "cycles")
        for flag, box in self.ending_map.items():
            if not box.get_modified():
                continue
            if box.isChecked():
                self.save.endings |= flag
            else:
                self.save.endings &= ~flag
            box.set_modified(False)

        self.save.cycles_copy = self.save.cycles
        self.save.endings_copy = self.save.endings
        self.satan_box.setattr_if_modified(
            self.save.miracle_unlocks.extras,
            "satan_beaten",
        )
        self.update_endings_summary()
        self.update_copy_warning()
