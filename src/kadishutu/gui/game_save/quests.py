from dataclasses import dataclass

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.game_save.game import CANON_OFFSET, detected_canon
from kadishutu.core.game_save.quests import QuestState
from kadishutu.data.quests import QUESTS, Quest

from ..shared import AppliableWidget, MComboBox
from .shared import GameScreenMixin

STATE_LABELS: list[tuple[str, QuestState]] = [
    ("Not started", QuestState.NotStarted),
    ("In progress", QuestState.InProgress),
    ("Report", QuestState.Report),
    ("Done", QuestState.Done),
]

CANON_LABELS = {
    "creation": "Creation only",
    "vengeance": "Vengeance only",
}


@dataclass
class QuestRow:
    quest: Quest
    combo: MComboBox
    name: QLabel
    canon: QLabel
    state: QLabel
    quest_id: QLabel
    widgets: list[QWidget]


class QuestEditorScreen(QWidget, GameScreenMixin, AppliableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quests = self.save.quests
        self.rows: list[QuestRow] = []
        self.visible_indices: set[int] = set()
        self.detected_canon = detected_canon(self.save.data)
        self.canon_raw = (
            self.save.data[CANON_OFFSET]
            if len(self.save.data) > CANON_OFFSET
            else None
        )

        root = QVBoxLayout(self)

        warning = QLabel(
            "Quest states are written directly. Changing them can lock or "
            "unlock rewards. Back up your save before editing them.",
            self,
        )
        warning.setObjectName("Warning")
        warning.setWordWrap(True)
        root.addWidget(warning)

        controls = QGridLayout()
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search by quest name or ID…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _: self.filter_rows())
        controls.addWidget(self.search, 0, 0, 1, 3)

        self.state_filter = QComboBox(self)
        self.state_filter.addItem("All states", "all")
        for label, state in STATE_LABELS:
            self.state_filter.addItem(label, state)
        self.state_filter.addItem("Invalid", "invalid")
        self.state_filter.currentIndexChanged.connect(
            lambda _: self.filter_rows()
        )
        controls.addWidget(self.state_filter, 0, 3)

        self.canon_filter = QComboBox(self)
        for label, key in [
            ("All canons", "all"),
            ("Creation only", "creation"),
            ("Vengeance only", "vengeance"),
            ("Shared", "shared"),
        ]:
            self.canon_filter.addItem(label, key)
        self.canon_filter.currentIndexChanged.connect(
            lambda _: self.filter_rows()
        )
        controls.addWidget(self.canon_filter, 0, 4)

        self.count_label = QLabel(self)
        self.count_label.setObjectName("Muted")
        controls.addWidget(self.count_label, 0, 5)
        root.addLayout(controls)

        self.detected_label = QLabel(self)
        self.detected_label.setObjectName("Muted")
        self.detected_label.setWordWrap(True)
        root.addWidget(self.detected_label)
        self.update_detected_label()

        self.note_label = QLabel(
            "Canon tags are community-sourced and only mark quests that are "
            "exclusive to one storyline. Untagged quests appear under both.",
            self,
        )
        self.note_label.setObjectName("Muted")
        self.note_label.setWordWrap(True)
        root.addWidget(self.note_label)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.inner = QWidget(self.scroll)
        self.scroll.setWidget(self.inner)
        self.grid = QGridLayout(self.inner)
        root.addWidget(self.scroll, 1)

        for column, (title, tooltip) in enumerate([
            ("Quest", "Quest name from your game data export."),
            ("Canon", "Storyline this quest is exclusive to."),
            ("State", "Not started, in progress, report, or done."),
            ("Status", "Warns when the stored flags are inconsistent."),
            ("ID", "Raw quest ID."),
        ]):
            header = QLabel(title, self.inner)
            header.setObjectName("Muted")
            header.setToolTip(tooltip)
            self.grid.addWidget(header, 0, column)

        for quest in QUESTS:
            self.add_row(quest)

        self.apply_detected_filter()
        self.stack_refresh()

    def update_detected_label(self):
        if self.detected_canon is not None:
            label = CANON_LABELS[self.detected_canon]
            self.detected_label.setText(
                f"Detected canon: {label} (0x{CANON_OFFSET:03x} = "
                f"{self.canon_raw}). The filter starts here; change it to "
                "override."
            )
            return
        raw = "?" if self.canon_raw is None else f"0x{self.canon_raw:02x}"
        self.detected_label.setText(
            f"Canon not detected (0x{CANON_OFFSET:03x} = {raw}). "
            "Choose a filter manually."
        )

    def apply_detected_filter(self):
        if self.detected_canon is None:
            return
        index = self.canon_filter.findData(self.detected_canon)
        if index < 0:
            return
        with QSignalBlocker(self.canon_filter):
            self.canon_filter.setCurrentIndex(index)

    def add_row(self, quest: Quest):
        index = len(self.rows) + 1
        combo = MComboBox(self.inner)
        combo.setMinimumWidth(180)
        name = QLabel(quest.name, self.inner)
        name.setToolTip(quest.name)
        canon_text = CANON_LABELS.get(quest.canon or "", "")
        canon = QLabel(canon_text, self.inner)
        canon.setObjectName("Muted")
        state = QLabel(self.inner)
        state.setObjectName("Warning")
        state.setVisible(False)
        quest_id = QLabel(str(quest.id), self.inner)
        quest_id.setObjectName("Muted")
        widgets: list[QWidget] = [name, canon, combo, state, quest_id]
        for column, widget in enumerate(widgets):
            self.grid.addWidget(widget, index, column)

        row = QuestRow(quest, combo, name, canon, state, quest_id, widgets)
        self.rows.append(row)

    def populate_combo(self, row: QuestRow, invalid: bool):
        combo = row.combo
        with QSignalBlocker(combo):
            combo.clear()
            if invalid:
                combo.addItem("Invalid", None)
            for label, state in STATE_LABELS:
                combo.addItem(label, state)
        combo.set_modified(False)

    def matches_query(self, row: QuestRow, query: str) -> bool:
        if not query:
            return True
        text = f"{row.quest.name} {row.quest.id}".lower()
        return all(token in text for token in query.split())

    def matches_state(self, row: QuestRow) -> bool:
        key = self.state_filter.currentData()
        if key == "all":
            return True
        if key == "invalid":
            return row.combo.currentData() is None
        return row.combo.currentData() == key

    def matches_canon(self, row: QuestRow) -> bool:
        key = self.canon_filter.currentData()
        if key == "all":
            return True
        if key == "shared":
            return row.quest.canon is None
        return row.quest.canon == key

    def filter_rows(self):
        query = self.search.text().strip().lower()
        visible: list[int] = []
        for index, row in enumerate(self.rows):
            matches = (
                self.matches_query(row, query)
                and self.matches_state(row)
                and self.matches_canon(row)
            )
            for widget in row.widgets:
                widget.setVisible(matches)
            if matches:
                visible.append(index)
        self.visible_indices = set(visible)
        self.count_label.setText(f"{len(visible)} / {len(self.rows)} quests")

    def stack_refresh(self):
        for row in self.rows:
            editor = self.quests.from_meta(row.quest)
            state = editor.state
            invalid = state == QuestState.Invalid
            self.populate_combo(row, invalid)
            if not invalid:
                row.combo.setCurrentIndex(row.combo.findData(state))
            row.state.setVisible(invalid)
            row.state.setText("Invalid state" if invalid else "")
        self.filter_rows()

    def on_apply_changes(self):
        for row in self.rows:
            if not row.combo.get_modified():
                continue
            state = row.combo.currentData()
            if state is None:
                continue
            editor = self.quests.from_meta(row.quest)
            editor.state = state
            row.combo.set_modified(False)
            row.state.setVisible(False)
