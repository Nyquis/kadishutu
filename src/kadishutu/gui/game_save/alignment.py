from dataclasses import dataclass

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

from kadishutu.data.alignment import ALIGNMENT_DATA, AlignmentBit

from ..shared import AppliableWidget, MCheckBox
from .shared import GameScreenMixin

ALIGNMENT_COLORS = {
    "law": "#64b5f6",
    "chaos": "#ef5350",
    "unknown": "#9e9e9e",
}


@dataclass
class AlignmentRow:
    offset: int
    bit: AlignmentBit
    box: MCheckBox
    alignment: QLabel
    place: QLabel
    choice: QLabel
    quest: QLabel
    kind: QLabel
    offset_label: QLabel
    bit_label: QLabel
    widgets: list[QWidget]


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

        self.alignment_filter = QComboBox(self)
        for label, key in [
            ("All alignments", "all"),
            ("Law", "law"),
            ("Chaos", "chaos"),
            ("Unknown", "unknown"),
        ]:
            self.alignment_filter.addItem(label, key)
        self.alignment_filter.currentIndexChanged.connect(
            lambda _: self.filter_rows()
        )
        controls.addWidget(self.alignment_filter, 0, 3)

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

        self.selected_filter = QComboBox(self)
        for label, key in [
            ("All choices", "all"),
            ("Selected", "selected"),
            ("Unselected", "unselected"),
        ]:
            self.selected_filter.addItem(label, key)
        self.selected_filter.currentIndexChanged.connect(
            lambda _: self.filter_rows()
        )
        controls.addWidget(self.selected_filter, 0, 5)

        self.advanced = QCheckBox("Show raw offset/bit", self)
        self.advanced.checkStateChanged.connect(self.set_raw_visible)
        controls.addWidget(self.advanced, 1, 0, 1, 2)

        self.select_button = QPushButton("Select visible", self)
        self.select_button.clicked.connect(self.select_visible)
        controls.addWidget(self.select_button, 1, 2)
        self.clear_button = QPushButton("Clear visible", self)
        self.clear_button.clicked.connect(self.clear_visible)
        controls.addWidget(self.clear_button, 1, 3)

        self.count_label = QLabel(self)
        self.count_label.setObjectName("Muted")
        controls.addWidget(self.count_label, 1, 4, 1, 2)
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
            ("Set", "Whether this alignment choice is selected."),
            ("Alignment", "Law, Chaos, or Unknown."),
            ("Place", "Where the choice happens."),
            ("Choice", "The dialogue or action choice."),
            ("Quest", "The side quest, if any."),
            ("Type", "Main story or side quest."),
            ("Offset", "Raw save offset."),
            ("Bit", "Raw bit inside the offset."),
        ]):
            header = QLabel(title, self.inner)
            header.setObjectName("Muted")
            header.setToolTip(tooltip)
            self.grid.addWidget(header, 0, column)
            self.headers.append(header)

        for offset, bit in self.flat_data():
            self.add_row(offset, bit)

        self.set_raw_visible()
        self.stack_refresh()

    @staticmethod
    def flat_data() -> list[tuple[int, AlignmentBit]]:
        return [
            (byte.offset, bit)
            for byte in ALIGNMENT_DATA
            for bit in byte.bits
        ]

    def add_row(self, offset: int, bit: AlignmentBit):
        index = len(self.rows) + 1
        box = MCheckBox(self.inner)
        alignment = QLabel(self.alignment_text(bit), self.inner)
        color = ALIGNMENT_COLORS.get(
            bit.alignment,
            ALIGNMENT_COLORS["unknown"],
        )
        alignment.setStyleSheet(
            f"color: {color}; font-weight: 600;"
        )
        place = QLabel(bit.place, self.inner)
        choice = QLabel(" — ".join(bit.text), self.inner)
        choice.setWordWrap(True)
        quest = QLabel(bit.side_quest or "", self.inner)
        kind = QLabel(
            "Main story" if bit.side_quest is None else "Side quest",
            self.inner,
        )
        kind.setObjectName("Muted")
        offset_label = QLabel(f"0x{offset:04x}", self.inner)
        bit_label = QLabel(str(bit.bit), self.inner)
        widgets: list[QWidget] = [
            box,
            alignment,
            place,
            choice,
            quest,
            kind,
            offset_label,
            bit_label,
        ]
        for column, widget in enumerate(widgets):
            self.grid.addWidget(widget, index, column)

        row = AlignmentRow(
            offset,
            bit,
            box,
            alignment,
            place,
            choice,
            quest,
            kind,
            offset_label,
            bit_label,
            widgets,
        )
        tooltip = (
            f"Offset: 0x{offset:04x}\n"
            f"Bit: {bit.bit}\n"
            f"Alignment: {self.alignment_text(bit)}\n"
            f"Place: {bit.place}\n"
            f"Quest: {bit.side_quest or 'Main story'}\n"
            f"Choice: {' — '.join(bit.text)}"
        )
        for widget in widgets:
            widget.setToolTip(tooltip)
        box.checkStateChanged.connect(
            lambda _, row=row: self.on_row_changed(row)
        )
        self.rows.append(row)

    @staticmethod
    def alignment_text(bit: AlignmentBit) -> str:
        if bit.alignment == "law":
            return "● Law"
        if bit.alignment == "chaos":
            return "● Chaos"
        return "○ Unknown"

    def set_raw_visible(self, *_):
        self.show_raw = self.advanced.isChecked()
        self.headers[6].setVisible(self.show_raw)
        self.headers[7].setVisible(self.show_raw)
        self.filter_rows()

    def matches_query(self, row: AlignmentRow, query: str) -> bool:
        if not query:
            return True
        text = " ".join([
            row.bit.place,
            " ".join(row.bit.text),
            row.bit.side_quest or "",
            self.alignment_text(row.bit),
            "main story" if row.bit.side_quest is None else "side quest",
            f"0x{row.offset:04x}",
            str(row.bit.bit),
        ]).lower()
        return all(token in text for token in query.split())

    def matches_alignment(self, row: AlignmentRow) -> bool:
        key = self.alignment_filter.currentData()
        if key == "law":
            return row.bit.alignment == "law"
        if key == "chaos":
            return row.bit.alignment == "chaos"
        if key == "unknown":
            return row.bit.is_unknown
        return True

    def matches_kind(self, row: AlignmentRow) -> bool:
        key = self.kind_filter.currentData()
        if key == "main":
            return row.bit.side_quest is None
        if key == "side":
            return row.bit.side_quest is not None
        return True

    def matches_selected(self, row: AlignmentRow) -> bool:
        key = self.selected_filter.currentData()
        if key == "selected":
            return row.box.isChecked()
        if key == "unselected":
            return not row.box.isChecked()
        return True

    def filter_rows(self):
        query = self.search.text().strip().lower()
        visible: list[int] = []
        for index, row in enumerate(self.rows):
            matches = (
                self.matches_query(row, query)
                and self.matches_alignment(row)
                and self.matches_kind(row)
                and self.matches_selected(row)
            )
            for widget in row.widgets:
                widget.setVisible(matches)
            row.offset_label.setVisible(matches and self.show_raw)
            row.bit_label.setVisible(matches and self.show_raw)
            if matches:
                visible.append(index)
        self.visible_indices = set(visible)
        self.count_label.setText(
            f"{len(visible)} / {len(self.rows)} choices"
        )
        self.update_summary()

    def update_summary(self):
        selected = law = chaos = unknown = 0
        for row in self.rows:
            if not row.box.isChecked():
                continue
            selected += 1
            if row.bit.alignment == "law":
                law += 1
            elif row.bit.alignment == "chaos":
                chaos += 1
            else:
                unknown += 1
        unselected = len(self.rows) - selected
        self.summary_label.setText(
            f"Selected {selected}/{len(self.rows)} · "
            f"Law {law} · Chaos {chaos} · Unknown {unknown} · "
            f"Unselected {unselected}"
        )

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

    def on_row_changed(self, row: AlignmentRow):
        self.update_summary()
        if self.selected_filter.currentData() != "all":
            self.filter_rows()

    def visible_rows(self) -> list[AlignmentRow]:
        return [self.rows[index] for index in sorted(self.visible_indices)]

    def select_visible(self):
        for row in self.visible_rows():
            row.box.setChecked(True)

    def clear_visible(self):
        for row in self.visible_rows():
            row.box.setChecked(False)

    def stack_refresh(self):
        for row in self.rows:
            editor = self.alignment.at_offset(row.offset)
            row.box.setChecked(editor.get_flag(row.bit.bit))
            row.box.set_modified(False)
        self.update_summary()
        self.update_unknown_bits()
        self.filter_rows()

    def on_apply_changes(self):
        for row in self.rows:
            editor = self.alignment.at_offset(row.offset)
            editor.set_flag(row.bit.bit, row.box.isChecked())
