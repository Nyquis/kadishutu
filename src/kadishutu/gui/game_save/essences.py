from dataclasses import dataclass

from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QWidget,
)

from kadishutu.core.game_save.essences import (
    EssenceEditor,
    EssenceMetadata,
)
from kadishutu.data.items import ESSENCES_RANGE, items_from

from ..shared import AppliableWidget, MCheckBox
from .shared import GameScreenMixin

STATUS_COLORS = {
    "Have": "#4caf50",
    "New": "#42a5f5",
    "Used before": "#ffb74d",
    "Not obtained": "#9e9e9e",
}


@dataclass
class EssenceRow:
    essence: EssenceEditor
    name: QLabel
    status: QLabel
    have: MCheckBox
    used: MCheckBox
    widgets: list[QWidget]


class EssenceEditorScreen(QScrollArea, GameScreenMixin, AppliableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rows: list[EssenceRow] = []
        self.visible_indices: set[int] = set()
        self.visible_count = 0

        self.setWidgetResizable(True)
        self.inner = QWidget()
        self.setWidget(self.inner)
        self.l = QGridLayout(self.inner)

        self.search = QLineEdit(self.inner)
        self.search.setPlaceholderText("Search essences by name or ID…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _: self.filter_items())
        self.l.addWidget(self.search, 0, 0, 1, 2)

        self.filter = QComboBox(self.inner)
        for label, key in [
            ("All", "all"),
            ("Have", "have"),
            ("Not have", "not_have"),
            ("Used before", "used"),
            ("Not used", "not_used"),
            ("New", "new"),
        ]:
            self.filter.addItem(label, key)
        self.filter.currentIndexChanged.connect(lambda _: self.filter_items())
        self.l.addWidget(self.filter, 0, 2)

        self.count_label = QLabel(self.inner)
        self.count_label.setObjectName("Muted")
        self.l.addWidget(self.count_label, 0, 3)

        self.have_button = QPushButton("Have visible", self.inner)
        self.have_button.clicked.connect(self.have_visible)
        self.l.addWidget(self.have_button, 1, 0)
        self.clear_button = QPushButton("Clear visible", self.inner)
        self.clear_button.clicked.connect(self.clear_visible)
        self.l.addWidget(self.clear_button, 1, 1)
        self.used_button = QPushButton("Mark used", self.inner)
        self.used_button.clicked.connect(self.mark_used_visible)
        self.l.addWidget(self.used_button, 1, 2)
        self.unused_button = QPushButton("Mark unused", self.inner)
        self.unused_button.clicked.connect(self.mark_unused_visible)
        self.l.addWidget(self.unused_button, 1, 3)

        help_label = QLabel(
            "“Have” controls whether the essence is in your inventory. "
            "“Used before” is a history flag and does not remove the essence. "
            "Neither is based on your current party.",
            self.inner,
        )
        help_label.setWordWrap(True)
        help_label.setObjectName("Muted")
        self.l.addWidget(help_label, 2, 0, 1, 4)

        for column, title in enumerate(
            ("Status", "Essence", "Have", "Used before")
        ):
            header = QLabel(title, self.inner)
            header.setObjectName("Muted")
            self.l.addWidget(header, 3, column)

        for i, meta in enumerate(items_from(ESSENCES_RANGE)):
            row = i + 4
            essence = self.essence_from_meta(meta)
            status = QLabel(self.inner)
            name = QLabel(essence.name, self.inner)
            have = MCheckBox(self.inner)
            used = MCheckBox(self.inner)
            row_widgets: list[QWidget] = [status, name, have, used]

            self.l.addWidget(status, row, 0)
            self.l.addWidget(name, row, 1)
            self.l.addWidget(have, row, 2)
            self.l.addWidget(used, row, 3)

            entry = EssenceRow(essence, name, status, have, used, row_widgets)
            have.checkStateChanged.connect(
                lambda _, entry=entry: self.update_row_status(entry)
            )
            used.checkStateChanged.connect(
                lambda _, entry=entry: self.update_row_status(entry)
            )
            self.rows.append(entry)

        self.stack_refresh()

    def essence_from_meta(self, meta) -> EssenceEditor:
        essence = self.save.essences.from_meta(meta)
        assert isinstance(essence, EssenceEditor)
        return essence

    @staticmethod
    def raw_metadata(essence: EssenceEditor) -> str:
        value = int(essence.metadata)
        names = []
        for name, bit in (
            ("New", EssenceMetadata.New),
            ("Owned", EssenceMetadata.Owned),
            ("Used", EssenceMetadata.Used),
            ("Bit0", EssenceMetadata.Bit0),
            ("Bit3", EssenceMetadata.Bit3),
            ("Bit5", EssenceMetadata.Bit5),
            ("Bit6", EssenceMetadata.Bit6),
            ("Bit7", EssenceMetadata.Bit7),
        ):
            if essence.metadata & bit:
                names.append(name)
        suffix = f" ({', '.join(names)})" if names else ""
        return f"Raw metadata: 0x{value:02x}{suffix}"

    @staticmethod
    def status_for(
        essence: EssenceEditor,
        have: bool,
        used: bool,
    ) -> str:
        if used:
            return "Used before"
        if have and essence.is_new():
            return "New"
        if have:
            return "Have"
        return "Not obtained"

    def tooltip_for(self, entry: EssenceRow) -> str:
        have = entry.have.isChecked()
        used = entry.used.isChecked()
        lines = [
            f"Have: {'yes' if have else 'no'}",
            f"Used before: {'yes' if used else 'no'}",
            self.raw_metadata(entry.essence),
        ]
        if entry.essence.meta.desc:
            lines.insert(0, entry.essence.meta.desc)
        return "\n".join(lines)

    def update_row_status(self, entry: EssenceRow):
        have = entry.have.isChecked()
        used = entry.used.isChecked()
        text = self.status_for(entry.essence, have, used)
        color = STATUS_COLORS[text]
        mark = "○" if text == "Not obtained" else "●"
        entry.status.setText(f"{mark} {text}")
        entry.status.setStyleSheet(
            f"color: {color}; font-weight: 600;"
        )
        tooltip = self.tooltip_for(entry)
        entry.status.setToolTip(tooltip)
        entry.name.setToolTip(tooltip)
        entry.have.setToolTip(tooltip)
        entry.used.setToolTip(tooltip)

    def matches_query(self, entry: EssenceRow, query: str) -> bool:
        if not query:
            return True
        if query.isdigit():
            return query == str(entry.essence.meta.id)
        have = entry.have.isChecked()
        used = entry.used.isChecked()
        text = " ".join([
            entry.essence.name,
            str(entry.essence.meta.id),
            self.status_for(entry.essence, have, used),
            "have" if have else "not have",
            "used before" if used else "not used",
            "new" if entry.essence.is_new() else "",
            self.raw_metadata(entry.essence),
        ])
        return all(token in text.lower() for token in query.split())

    def matches_filter(self, entry: EssenceRow) -> bool:
        key = self.filter.currentData()
        have = entry.have.isChecked()
        used = entry.used.isChecked()
        if key == "have":
            return have
        if key == "not_have":
            return not have
        if key == "used":
            return used
        if key == "not_used":
            return not used
        if key == "new":
            return entry.essence.is_new()
        return True

    def filter_items(self):
        query = self.search.text().strip().lower()
        visible: list[int] = []
        for index, entry in enumerate(self.rows):
            matches = (
                self.matches_filter(entry)
                and self.matches_query(entry, query)
            )
            for widget in entry.widgets:
                widget.setVisible(matches)
            if matches:
                visible.append(index)
        self.visible_indices = set(visible)
        self.visible_count = len(visible)
        if query or self.filter.currentData() != "all":
            self.count_label.setText(
                f"{self.visible_count} / {len(self.rows)}"
            )
        else:
            self.count_label.setText(f"{len(self.rows)} essences")

    def visible_rows(self) -> list[EssenceRow]:
        return [self.rows[index] for index in sorted(self.visible_indices)]

    def have_visible(self):
        for entry in self.visible_rows():
            entry.have.setChecked(True)

    def clear_visible(self):
        for entry in self.visible_rows():
            entry.have.setChecked(False)

    def mark_used_visible(self):
        for entry in self.visible_rows():
            entry.used.setChecked(True)

    def mark_unused_visible(self):
        for entry in self.visible_rows():
            entry.used.setChecked(False)

    def stack_refresh(self):
        for entry in self.rows:
            entry.have.setChecked(entry.essence.have)
            entry.used.setChecked(entry.essence.used)
            entry.have.set_modified(False)
            entry.used.set_modified(False)
            self.update_row_status(entry)
        self.filter_items()

    def on_apply_changes(self):
        for entry in self.rows:
            entry.have.setattr_if_modified(entry.essence, "have")
            entry.used.setattr_if_modified(entry.essence, "used")
