from dataclasses import dataclass

from PySide6.QtCore import QSignalBlocker, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.game_save.game import detected_canon
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

COLUMNS = ["Choice", "Pts", "Place", "Quest", "Type", "Offset", "Bits"]
COLUMN_WIDTHS = {1: 46, 2: 165, 3: 185, 4: 85, 5: 78, 6: 72}


def points_text(points: int) -> str:
    return "1 pt" if points == 1 else f"{points} pts"


@dataclass
class AlignmentRow:
    offset: int
    choice: AlignmentChoice
    combo: MComboBox
    points: QTableWidgetItem
    invalid: bool = False


class AlignmentEditorScreen(QWidget, GameScreenMixin, AppliableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alignment = self.save.alignment
        self.rows: list[AlignmentRow] = []
        self.visible_indices: set[int] = set()
        self.show_raw = False
        self.detected_canon = detected_canon(self.save.data)

        root = QVBoxLayout(self)

        warning = QLabel(
            "Changing alignment flags can affect endings. Back up your save "
            "before editing these values.",
            self,
        )
        warning.setObjectName("Warning")
        warning.setWordWrap(True)
        root.addWidget(warning)

        self.canon_label = QLabel(self)
        self.canon_label.setWordWrap(True)
        self.canon_label.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(self.canon_label)

        self.unknown_label = QLabel(self)
        self.unknown_label.setObjectName("Warning")
        self.unknown_label.setWordWrap(True)
        self.unknown_label.setVisible(False)
        root.addWidget(self.unknown_label)

        search_row = QHBoxLayout()
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search by place, choice, or quest…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _: self.filter_rows())
        search_row.addWidget(self.search, 1)

        search_row.addWidget(QLabel("Canon:", self))
        self.canon_filter = QComboBox(self)
        for label, key in [
            ("Creation", "creation"),
            ("Vengeance", "vengeance"),
            ("Both", "both"),
        ]:
            self.canon_filter.addItem(label, key)
        default = self.detected_canon or "both"
        self.canon_filter.setCurrentIndex(
            max(self.canon_filter.findData(default), 0)
        )
        self.canon_filter.setToolTip(
            "Detected from the save at 0x53a. Change it to override."
        )
        self.canon_filter.currentIndexChanged.connect(
            lambda _: self.on_canon_changed()
        )
        search_row.addWidget(self.canon_filter)

        search_row.addWidget(QLabel("Route:", self))
        self.route_filter = QComboBox(self)
        self.route_filter.setMinimumWidth(130)
        self.route_filter.setToolTip(
            "Sets choices you already made to that side. Decisions you have "
            "not made are left alone, and Apply Changes writes the result."
        )
        self.route_filter.currentIndexChanged.connect(
            lambda _: self.on_route_changed()
        )
        search_row.addWidget(self.route_filter)
        root.addLayout(search_row)

        filter_row = QHBoxLayout()
        self.selection_filter = QComboBox(self)
        for label, key in [
            ("All choices", "all"),
            ("Law", "law"),
            ("Chaos", "chaos"),
            ("Unknown", "unknown"),
            ("Not chosen", "unselected"),
            ("Both set", "invalid"),
        ]:
            self.selection_filter.addItem(label, key)
        self.selection_filter.currentIndexChanged.connect(
            lambda _: self.filter_rows()
        )
        filter_row.addWidget(self.selection_filter)

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
        filter_row.addWidget(self.kind_filter)

        self.advanced = QCheckBox("Show offsets", self)
        self.advanced.checkStateChanged.connect(self.set_raw_visible)
        filter_row.addWidget(self.advanced)

        self.clear_button = QPushButton("Clear visible", self)
        self.clear_button.clicked.connect(self.clear_visible)
        filter_row.addWidget(self.clear_button)

        filter_row.addStretch()
        self.count_label = QLabel(self)
        self.count_label.setObjectName("Muted")
        filter_row.addWidget(self.count_label)
        root.addLayout(filter_row)

        self.route_note = QLabel(self)
        self.route_note.setObjectName("Muted")
        self.route_note.setWordWrap(True)
        root.addWidget(self.route_note)
        self.rebuild_routes()

        summary_row = QHBoxLayout()
        summary_row.setSpacing(18)
        self.law_label = QLabel(self)
        self.law_label.setStyleSheet(f"color: {ALIGNMENT_COLORS['law']};")
        self.chaos_label = QLabel(self)
        self.chaos_label.setStyleSheet(f"color: {ALIGNMENT_COLORS['chaos']};")
        self.verdict_label = QLabel(self)
        self.verdict_label.setObjectName("Muted")
        summary_row.addWidget(self.law_label)
        summary_row.addWidget(self.chaos_label)
        summary_row.addStretch()
        summary_row.addWidget(self.verdict_label)
        root.addLayout(summary_row)

        self.note_label = QLabel(
            "Point values are community-reported. Most choices are worth 1 "
            "point; the major ones are worth 3.",
            self,
        )
        self.note_label.setObjectName("Muted")
        self.note_label.setWordWrap(True)
        root.addWidget(self.note_label)

        self.table = QTableWidget(0, len(COLUMNS), self)
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column, width in COLUMN_WIDTHS.items():
            header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.Interactive
            )
            self.table.setColumnWidth(column, width)
        header.setStretchLastSection(False)
        root.addWidget(self.table, 1)

        for offset, choice in self.flat_data():
            self.add_row(offset, choice)

        self.set_raw_visible()
        self.stack_refresh()
        self.update_canon_label()

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
        index = self.table.rowCount()
        self.table.insertRow(index)
        self.table.setRowHeight(index, 34)

        combo = MComboBox(self.table)
        combo.setToolTip(
            "Law and Chaos options for this decision. Only one can be set."
        )
        self.table.setCellWidget(index, 0, combo)

        points = QTableWidgetItem("")
        points.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(index, 1, points)
        place = QTableWidgetItem(choice.place)
        place.setToolTip(choice.place)
        self.table.setItem(index, 2, place)
        quest = QTableWidgetItem(choice.side_quest or "")
        quest.setToolTip(choice.side_quest or "Main story")
        self.table.setItem(index, 3, quest)
        kind = QTableWidgetItem(
            "Side quest" if choice.side_quest else "Main story"
        )
        kind.setForeground(Qt.GlobalColor.gray)
        self.table.setItem(index, 4, kind)
        offset_item = QTableWidgetItem(f"0x{offset:04x}")
        self.table.setItem(index, 5, offset_item)
        bits_item = QTableWidgetItem(
            ", ".join(str(option.bit) for option in choice.options)
        )
        self.table.setItem(index, 6, bits_item)

        row = AlignmentRow(offset, choice, combo, points)
        tooltip = "\n".join([
            f"Place: {choice.place}",
            f"Quest: {choice.side_quest or 'Main story'}",
            "Options:",
            *[f"  {self.option_label(o)}" for o in choice.options],
        ])
        combo.setToolTip(tooltip)
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
        invalid = len(selected_bits) > 1
        row.invalid = invalid
        with QSignalBlocker(combo):
            combo.clear()
            if invalid:
                combo.addItem("Both are set — pick one", None)
            else:
                combo.addItem("Not chosen", None)
            for option in row.choice.options:
                combo.addItem(self.option_label(option), option.bit)
            if invalid:
                combo.setCurrentIndex(0)
                combo.setToolTip(
                    "Both the Law and Chaos values are set in this save. "
                    "Pick one to resolve it."
                )
            else:
                index = (
                    combo.findData(selected_bits[0])
                    if selected_bits
                    else 0
                )
                combo.setCurrentIndex(index if index >= 0 else 0)
        combo.set_modified(False)
        self.update_points(row)

    def update_points(self, row: AlignmentRow):
        option = self.selected_option(row)
        if option is None:
            row.points.setText("")
        else:
            row.points.setText(str(option.weight))

    def set_raw_visible(self, *_):
        self.show_raw = self.advanced.isChecked()
        for column in (5, 6):
            self.table.setColumnHidden(column, not self.show_raw)
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

    def active_canon(self) -> str | None:
        key = self.canon_filter.currentData()
        if key == "both":
            return None
        return key

    def matches_canon(self, row: AlignmentRow) -> bool:
        canon = self.active_canon()
        if canon is None:
            return True
        return row.choice.canon in ("shared", canon)

    def rebuild_routes(self):
        canon = self.canon_filter.currentData()
        if canon == "creation":
            options = [
                ("No change", None),
                ("Law", "law"),
                ("Neutral", "neutral"),
                ("True Neutral", "true-neutral"),
                ("Chaos", "chaos"),
            ]
        else:
            options = [("No change", None), ("Law", "law"), ("Chaos", "chaos")]
        previous = self.route_filter.currentData()
        with QSignalBlocker(self.route_filter):
            self.route_filter.clear()
            for label, key in options:
                self.route_filter.addItem(label, key)
            index = self.route_filter.findData(previous)
            self.route_filter.setCurrentIndex(index if index >= 0 else 0)

    def on_canon_changed(self):
        self.rebuild_routes()
        self.route_note.setText("")
        self.update_canon_label()
        self.filter_rows()

    def on_route_changed(self):
        route = self.route_filter.currentData()
        self.route_note.setText("")
        if route is None:
            return
        if route in ("neutral", "true-neutral"):
            detail = (
                "Creation's Neutral and True Neutral are chosen at Empyrean, "
                "not from the Law/Chaos totals."
            )
            if route == "true-neutral":
                detail += (
                    " True Neutral also needs the Ra, Fionn, and Shiva "
                    "side quests."
                )
            self.route_note.setText(detail + " Choices were left unchanged.")
            with QSignalBlocker(self.route_filter):
                self.route_filter.setCurrentIndex(0)
            return
        label = "Law" if route == "law" else "Chaos"
        changed = 0
        for row in self.rows:
            if row.invalid or self.selected_option(row) is None:
                continue
            target = next(
                (
                    option
                    for option in row.choice.options
                    if option.alignment == route
                ),
                None,
            )
            if target is None or row.combo.currentData() == target.bit:
                continue
            row.combo.setCurrentIndex(row.combo.findData(target.bit))
            changed += 1
        self.route_note.setText(
            f"Set {changed} already-made choice(s) to {label}. Decisions you "
            "have not made are untouched; Apply Changes writes the result."
            + (
                " In Creation this only moves the tracked alignment and the "
                "matching miracle; the ending is still chosen at Empyrean."
                if self.active_canon() == "creation"
                else ""
            )
        )
        with QSignalBlocker(self.route_filter):
            self.route_filter.setCurrentIndex(0)

    def update_canon_label(self):
        raw = (
            f"0x{self.save.data[0x53A]:02x}"
            if len(self.save.data) > 0x53A
            else "?"
        )
        names = {
            "creation": "Canon of Creation",
            "vengeance": "Canon of Vengeance",
        }
        detected_name = names.get(self.detected_canon or "")
        active = self.active_canon()
        active_name = names.get(active or "")

        if detected_name is None:
            head = (
                f"<b>Canon not detected</b> · 0x53a = {raw} — showing both"
            )
        elif active is None:
            head = (
                f"<b>Showing both canons</b> · detected {detected_name} "
                f"(0x53a = {raw})"
            )
        elif active == self.detected_canon:
            head = (
                f"<b>{active_name}</b> · detected from 0x53a = {raw}"
            )
        else:
            head = (
                f"<b>{active_name}</b> · overridden "
                f"(save says {detected_name}, 0x53a = {raw})"
            )

        if active is None:
            detail = "Choices from both canons are listed."
        elif active == "creation":
            detail = (
                "Shared and Creation choices. Creation-specific choices are "
                "not mapped yet. Law, Neutral, True Neutral, and Chaos are all "
                "decided at Empyrean, not by these points."
            )
        else:
            detail = (
                "Shared and Vengeance choices. Law is the Peaceful route and "
                "Chaos the Apocalypse route; a two-point lead decides which, "
                "and one point or less is Humanity."
            )
        self.canon_label.setText(f"{head}<br>{detail}")

    def filter_rows(self):
        query = self.search.text().strip().lower()
        visible: list[int] = []
        for index, row in enumerate(self.rows):
            matches = (
                self.matches_query(row, query)
                and self.matches_selection(row)
                and self.matches_kind(row)
                and self.matches_canon(row)
            )
            self.table.setRowHidden(index, not matches)
            if matches:
                visible.append(index)
        self.visible_indices = set(visible)
        self.count_label.setText(
            f"{len(visible)} / {len(self.rows)} choices"
        )
        self.update_summary()

    def update_summary(self):
        rows = self.visible_rows()
        law = chaos = unknown = 0
        law_points = chaos_points = 0
        for row in rows:
            option = self.selected_option(row)
            if option is None:
                continue
            if option.alignment == "law":
                law += 1
                law_points += option.weight
            elif option.alignment == "chaos":
                chaos += 1
                chaos_points += option.weight
            else:
                unknown += 1
        self.law_label.setText(
            f"Law {law} · {points_text(law_points)}"
        )
        self.chaos_label.setText(
            f"Chaos {chaos} · {points_text(chaos_points)}"
        )

        if self.detected_canon == "creation":
            self.verdict_label.setText("Endings are chosen at Empyrean")
            return
        net = law_points - chaos_points
        if net >= 2:
            verdict = f"Law leads by {points_text(net)}"
        elif net <= -2:
            verdict = f"Chaos leads by {points_text(-net)}"
        else:
            verdict = "Humanity — within 1 pt"
        if unknown:
            verdict += f" · {unknown} unverified"
        self.verdict_label.setText(verdict)

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
        self.update_points(row)
        self.update_summary()
        if self.selection_filter.currentData() != "all":
            self.filter_rows()

    def visible_rows(self) -> list[AlignmentRow]:
        return [self.rows[index] for index in sorted(self.visible_indices)]

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
            row.combo.set_modified(False)
            self.update_points(row)
