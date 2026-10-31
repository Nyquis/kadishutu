from dataclasses import dataclass

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from kadishutu.data.alignment import (
    ALIGNMENT_DATA,
    AlignmentBit,
    AlignmentChoice,
)

from ..shared import AppliableWidget, MComboBox
from .shared import GameScreenMixin

ALIGNMENT_COLORS = {
    "law": "#64b5f6",
    "chaos": "#ef5350",
    "unknown": "#9e9e9e",
}


@dataclass
class AlignmentRow:
    offset: int
    choice: AlignmentChoice
    combo: MComboBox
    status: QLabel
    place: QLabel
    quest: QLabel
    kind: QLabel
    offset_label: QLabel
    bits_label: QLabel
    widgets: list[QWidget]
    invalid: bool = False


class AlignmentEditorScreen(QWidget, GameScreenMixin, AppliableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alignment = self.save.alignment
        self.rows: list[AlignmentRow] = []
        self.visible_indices: set[int] = set()
        self.show_raw = False

        root = QVBoxLayout(self)

        warning = QLabel(
            "Changing alignment flags can affect endings. Back up your save "
            "before editing these values.",
            self,
        )
        warning.setObjectName("Warning")
        warning.setWordWrap(True)
        root.addWidget(warning)

        self.unknown_label = QLabel(self)
        self.unknown_label.setObjectName("Warning")
        self.unknown_label.setWordWrap(True)
        self.unknown_label.setVisible(False)
        root.addWidget(self.unknown_label)

        controls = QGridLayout()
        self.search = QLineEdit(self)
        self.search.setPlaceholderText(
            "Search by place, choice, quest, or type…"
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _: self.filter_rows())
        controls.addWidget(self.search, 0, 0, 1, 3)

        self.selection_filter = QComboBox(self)
        for label, key in [
            ("All choices", "all"),
            ("Law", "law"),
            ("Chaos", "chaos"),
            ("Unknown", "unknown"),
            ("Not chosen", "unselected"),
            ("Invalid", "invalid"),
        ]:
            self.selection_filter.addItem(label, key)
        self.selection_filter.currentIndexChanged.connect(
            lambda _: self.filter_rows()
        )
        controls.addWidget(self.selection_filter, 0, 3)

        self.kind_filter = QComboBox(self)
        for label, key in [
            ("All types", "all"),
            ("Main story", "main"),
            ("Side quests", "side"),
        ]:
            self.kind_filter.addItem(label, key)
        self.kind_filter.currentIndexChanged.connect(
            lambda _: self.filter_rows()
        )
        controls.addWidget(self.kind_filter, 0, 4)

        self.advanced = QCheckBox("Show raw offset/bit", self)
        self.advanced.checkStateChanged.connect(self.set_raw_visible)
        controls.addWidget(self.advanced, 1, 0, 1, 2)

        self.law_button = QPushButton("Law visible", self)
        self.law_button.clicked.connect(self.set_law_visible)
        controls.addWidget(self.law_button, 1, 2)
        self.chaos_button = QPushButton("Chaos visible", self)
        self.chaos_button.clicked.connect(self.set_chaos_visible)
        controls.addWidget(self.chaos_button, 1, 3)
        self.clear_button = QPushButton("Clear visible", self)
        self.clear_button.clicked.connect(self.clear_visible)
        controls.addWidget(self.clear_button, 1, 4)

        self.count_label = QLabel(self)
        self.count_label.setObjectName("Muted")
        controls.addWidget(self.count_label, 1, 5)
        root.addLayout(controls)

        self.summary_label = QLabel(self)
        self.summary_label.setObjectName("Muted")
        root.addWidget(self.summary_label)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.inner = QWidget(self.scroll)
        self.scroll.setWidget(self.inner)
        self.grid = QGridLayout(self.inner)
        root.addWidget(self.scroll, 1)

        self.headers: list[QLabel] = []
        for column, (title, tooltip) in enumerate([
            ("Selection", "The chosen option for this decision."),
            ("Status", "Warns when both sides are set in the save."),
            ("Place", "Where the choice happens."),
            ("Quest", "The side quest, if any."),
            ("Type", "Main story or side quest."),
            ("Offset", "Raw save offset."),
            ("Bits", "Raw bits inside the offset."),
        ]):
            header = QLabel(title, self.inner)
            header.setObjectName("Muted")
            header.setToolTip(tooltip)
            self.grid.addWidget(header, 0, column)
            self.headers.append(header)

        for offset, choice in self.flat_data():
            self.add_row(offset, choice)

        self.set_raw_visible()
        self.stack_refresh()

    @staticmethod
    def flat_data() -> list[tuple[int, AlignmentChoice]]:
        return [
            (byte.offset, choice)
            for byte in ALIGNMENT_DATA
            for choice in byte.choices()
        ]

    def option_label(self, option: AlignmentBit) -> str:
        if option.alignment == "law":
            prefix = "Law"
        elif option.alignment == "chaos":
            prefix = "Chaos"
        else:
            prefix = "Unknown"
        return f"{prefix} — {' / '.join(option.text)}"

    def add_row(self, offset: int, choice: AlignmentChoice):
        index = len(self.rows) + 1
        combo = MComboBox(self.inner)
        combo.setMinimumWidth(260)
        combo.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLengthWithIcon
        )
        combo.setMinimumContentsLength(40)
        status = QLabel(self.inner)
        status.setObjectName("Warning")
        status.setVisible(False)
        place = QLabel(choice.place, self.inner)
        quest = QLabel(choice.side_quest or "", self.inner)
        kind = QLabel(
            "Main story" if choice.side_quest is None else "Side quest",
            self.inner,
        )
        kind.setObjectName("Muted")
        offset_label = QLabel(f"0x{offset:04x}", self.inner)
        bits_label = QLabel(
            ", ".join(str(option.bit) for option in choice.options),
            self.inner,
        )
        widgets: list[QWidget] = [
            combo,
            status,
            place,
            quest,
            kind,
            offset_label,
            bits_label,
        ]
        for column, widget in enumerate(widgets):
            self.grid.addWidget(widget, index, column)

        row = AlignmentRow(
            offset,
            choice,
            combo,
            status,
            place,
            quest,
            kind,
            offset_label,
            bits_label,
            widgets,
        )
        tooltip = "\n".join([
            f"Offset: 0x{offset:04x}",
            f"Bits: {', '.join(str(o.bit) for o in choice.options)}",
            f"Place: {choice.place}",
            f"Quest: {choice.side_quest or 'Main story'}",
            "Options:",
            *[f"  {self.option_label(o)}" for o in choice.options],
        ])
        for widget in widgets:
            widget.setToolTip(tooltip)
        combo.currentIndexChanged.connect(
            lambda _, row=row: self.on_choice_changed(row)
        )
        self.rows.append(row)

    def populate_combo(
        self,
        row: AlignmentRow,
        selected_bits: list[int],
    ):
        combo = row.combo
        with QSignalBlocker(combo):
            combo.clear()
            combo.addItem("Not chosen", None)
            for option in row.choice.options:
                combo.addItem(self.option_label(option), option.bit)
            if len(selected_bits) > 1:
                combo.setCurrentIndex(0)
                row.invalid = True
                row.status.setText("Both selected")
                row.status.setVisible(True)
            else:
                row.invalid = False
                row.status.setVisible(False)
                index = (
                    combo.findData(selected_bits[0])
                    if selected_bits
                    else 0
                )
                combo.setCurrentIndex(index if index >= 0 else 0)
        combo.set_modified(False)

    def set_raw_visible(self, *_):
        self.show_raw = self.advanced.isChecked()
        self.headers[5].setVisible(self.show_raw)
        self.headers[6].setVisible(self.show_raw)
        self.filter_rows()

    def matches_query(self, row: AlignmentRow, query: str) -> bool:
        if not query:
            return True
        text = " ".join([
            row.choice.place,
            row.choice.side_quest or "",
            "main story" if row.choice.side_quest is None else "side quest",
            *[
                " ".join(option.text)
                for option in row.choice.options
            ],
            f"0x{row.offset:04x}",
            *[str(option.bit) for option in row.choice.options],
        ]).lower()
        return all(token in text for token in query.split())

    def selected_option(self, row: AlignmentRow) -> AlignmentBit | None:
        bit = row.combo.currentData()
        if bit is None:
            return None
        return row.choice.option_for_bit(bit)

    def matches_selection(self, row: AlignmentRow) -> bool:
        key = self.selection_filter.currentData()
        if key == "all":
            return True
        if key == "invalid":
            return row.invalid and not row.combo.get_modified()
        if row.invalid and not row.combo.get_modified():
            return False
        option = self.selected_option(row)
        if key == "unselected":
            return option is None
        if option is None:
            return False
        if key == "unknown":
            return option.is_unknown
        return option.alignment == key

    def matches_kind(self, row: AlignmentRow) -> bool:
        key = self.kind_filter.currentData()
        if key == "main":
            return row.choice.side_quest is None
        if key == "side":
            return row.choice.side_quest is not None
        return True

    def filter_rows(self):
        query = self.search.text().strip().lower()
        visible: list[int] = []
        for index, row in enumerate(self.rows):
            matches = (
                self.matches_query(row, query)
                and self.matches_selection(row)
                and self.matches_kind(row)
            )
            for widget in row.widgets:
                widget.setVisible(matches)
            row.status.setVisible(
                matches
                and row.invalid
                and not row.combo.get_modified()
            )
            row.offset_label.setVisible(matches and self.show_raw)
            row.bits_label.setVisible(matches and self.show_raw)
            if matches:
                visible.append(index)
        self.visible_indices = set(visible)
        self.count_label.setText(
            f"{len(visible)} / {len(self.rows)} choices"
        )
        self.update_summary()

    def update_summary(self):
        selected = law = chaos = unknown = invalid = 0
        for row in self.rows:
            if row.invalid and not row.combo.get_modified():
                invalid += 1
                continue
            option = self.selected_option(row)
            if option is None:
                continue
            selected += 1
            if option.alignment == "law":
                law += 1
            elif option.alignment == "chaos":
                chaos += 1
            else:
                unknown += 1
        unselected = len(self.rows) - selected - invalid
        text = (
            f"Selected {selected}/{len(self.rows)} · "
            f"Law {law} · Chaos {chaos} · Unknown {unknown} · "
            f"Unselected {unselected}"
        )
        if invalid:
            text += f" · Invalid {invalid}"
        self.summary_label.setText(text)

    def update_unknown_bits(self):
        warnings = []
        for byte in ALIGNMENT_DATA:
            value = self.alignment.at_offset(byte.offset).byte
            unknown = byte.unknown_bits(value)
            if not unknown:
                continue
            bits = [
                str(bit)
                for bit in range(8)
                if unknown & (1 << bit)
            ]
            warnings.append(f"0x{byte.offset:04x} bit {', '.join(bits)}")
        if warnings:
            self.unknown_label.setText(
                "Unmapped alignment bits set: " + "; ".join(warnings)
            )
            self.unknown_label.setVisible(True)
        else:
            self.unknown_label.setVisible(False)

    def on_choice_changed(self, row: AlignmentRow):
        row.invalid = False
        row.status.setVisible(False)
        self.update_summary()
        if self.selection_filter.currentData() != "all":
            self.filter_rows()

    def visible_rows(self) -> list[AlignmentRow]:
        return [self.rows[index] for index in sorted(self.visible_indices)]

    def set_law_visible(self):
        for row in self.visible_rows():
            option = next(
                (
                    option
                    for option in row.choice.options
                    if option.alignment == "law"
                ),
                None,
            )
            if option is not None:
                row.combo.setCurrentIndex(row.combo.findData(option.bit))

    def set_chaos_visible(self):
        for row in self.visible_rows():
            option = next(
                (
                    option
                    for option in row.choice.options
                    if option.alignment == "chaos"
                ),
                None,
            )
            if option is not None:
                row.combo.setCurrentIndex(row.combo.findData(option.bit))

    def clear_visible(self):
        for row in self.visible_rows():
            row.combo.setCurrentIndex(0)

    def stack_refresh(self):
        for row in self.rows:
            editor = self.alignment.at_offset(row.offset)
            selected_bits = [
                option.bit
                for option in row.choice.options
                if editor.get_flag(option.bit)
            ]
            self.populate_combo(row, selected_bits)
        self.update_summary()
        self.update_unknown_bits()
        self.filter_rows()

    def on_apply_changes(self):
        for row in self.rows:
            if not row.combo.get_modified():
                continue
            editor = self.alignment.at_offset(row.offset)
            selected_bit = row.combo.currentData()
            for option in row.choice.options:
                editor.set_flag(option.bit, option.bit == selected_bit)
            row.invalid = False
            row.status.setVisible(False)
            row.combo.set_modified(False)
