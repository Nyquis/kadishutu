from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.game_save.game import Endings, detected_canon
from kadishutu.data.endings import (
    CANON_DESCRIPTIONS,
    ENDING_INFOS,
    ENDING_ROUTES,
    EndingInfo,
)

from ..shared import QU8, AppliableWidget, MCheckBox
from .shared import GameScreenMixin


class CrossCycleEditorScreen(QWidget, GameScreenMixin, AppliableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ending_map: dict[Endings, MCheckBox] = {}
        self.canon_headers: dict[str, QLabel] = {}
        self.canon_sections: dict[str, QWidget] = {}
        self.detected_canon = detected_canon(self.save.data)
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
        self.canon_label = QLabel(endings_group)
        self.canon_label.setWordWrap(True)
        endings_layout.addWidget(self.canon_label)

        self.endings_summary = QLabel(endings_group)
        self.endings_summary.setObjectName("Muted")
        endings_layout.addWidget(self.endings_summary)

        endings_note = QLabel(
            "Endings are cumulative across cycles. A save can mark endings "
            "from both canons.",
            endings_group,
        )
        endings_note.setObjectName("Muted")
        endings_note.setWordWrap(True)
        endings_layout.addWidget(endings_note)

        for route in ENDING_ROUTES:
            section = QWidget(endings_group)
            section_layout = QVBoxLayout(section)
            section_layout.setContentsMargins(0, 0, 0, 0)

            canon_header = QLabel(section)
            canon_header.setStyleSheet(
                "font-weight: 600; font-size: 14px; margin-top: 8px;"
            )
            section_layout.addWidget(canon_header)
            self.canon_headers[route] = canon_header

            canon_description = QLabel(
                CANON_DESCRIPTIONS[route],
                section,
            )
            canon_description.setObjectName("Muted")
            canon_description.setWordWrap(True)
            section_layout.addWidget(canon_description)

            route_layout = QGridLayout()
            row = 0
            for flag, info in self.ending_details:
                if info.route != route:
                    continue
                tip = f"{info.full_label}\n{info.description}"
                box = MCheckBox(section)
                box.setToolTip(tip)
                box.checkStateChanged.connect(
                    lambda _: self.update_endings_summary()
                )
                label = QLabel(info.label, section)
                label.setToolTip(tip)
                route_layout.addWidget(label, row, 0)
                route_layout.addWidget(box, row, 1)
                self.ending_map[flag] = box
                row += 1
            section_layout.addLayout(route_layout)

            self.canon_sections[route] = section
            endings_layout.addWidget(section)

        self.other_canon_toggle = QCheckBox(
            "Show the other canon's endings", endings_group
        )
        self.other_canon_toggle.setToolTip(
            "Endings are cumulative across cycles, so an older canon's "
            "endings can still be marked in this save."
        )
        self.other_canon_toggle.toggled.connect(
            lambda _: self.update_canon_view()
        )
        endings_layout.addWidget(self.other_canon_toggle)

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
        self.update_canon_view()

    def active_ending_details(self) -> list[tuple[Endings, EndingInfo]]:
        if self.detected_canon is None:
            return list(self.ending_details)
        return [
            (flag, info)
            for flag, info in self.ending_details
            if info.route.lower() == self.detected_canon
        ]

    def update_canon_view(self):
        if self.detected_canon is None:
            self.other_canon_toggle.setVisible(False)
            self.canon_label.setText(
                "Canon not detected (0x53a has an unexpected value). "
                "Showing every ending; both canons are editable."
            )
            for section in self.canon_sections.values():
                section.setVisible(True)
            return

        active_route = next(
            route
            for route in ENDING_ROUTES
            if route.lower() == self.detected_canon
        )
        other_route = next(
            route for route in ENDING_ROUTES if route != active_route
        )
        count = len(self.active_ending_details())
        self.canon_label.setText(
            f"Detected canon: Canon of {active_route} — {count} endings. "
            f"The other canon's endings come from earlier cycles and are "
            "hidden unless you reveal them."
        )
        self.other_canon_toggle.setVisible(True)
        self.other_canon_toggle.setText(
            f"Show Canon of {other_route} endings"
        )
        for route, section in self.canon_sections.items():
            section.setVisible(
                route == active_route or self.other_canon_toggle.isChecked()
            )

    def update_endings_summary(self):
        details = self.active_ending_details()
        achieved = sum(
            1
            for flag, _ in details
            if self.ending_map[flag].isChecked()
        )
        self.endings_summary.setText(
            f"{achieved} / {len(details)} endings marked"
        )
        for route in ENDING_ROUTES:
            route_details = [
                (flag, info)
                for flag, info in self.ending_details
                if info.route == route
            ]
            route_achieved = sum(
                1
                for flag, _ in route_details
                if self.ending_map[flag].isChecked()
            )
            self.canon_headers[route].setText(
                f"Canon of {route} — "
                f"{route_achieved} / {len(route_details)}"
            )
        for route in ENDING_ROUTES:
            route_details = [
                (flag, info)
                for flag, info in self.ending_details
                if info.route == route
            ]
            route_achieved = sum(
                1
                for flag, _ in route_details
                if self.ending_map[flag].isChecked()
            )
            self.canon_headers[route].setText(
                f"Canon of {route} — "
                f"{route_achieved} / {len(route_details)}"
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
