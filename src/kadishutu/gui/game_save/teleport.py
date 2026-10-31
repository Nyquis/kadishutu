from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from kadishutu.data.laylines import (
    LAYLINE_DATA,
    LAYLINE_ID_MAP,
    REGION_ORDER,
    Layline,
)

from ..shared import AppliableWidget
from .shared import GameScreenMixin

NOTE_MSG = (
    "Teleport changes your current position and last-used layline. "
    "It does not change the save-slot location; use Save to Disk afterward."
)


class TeleporterScreen(QWidget, GameScreenMixin, AppliableWidget):
    applies_immediately = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selected_layline: Layline | None = None
        self.item_by_id: dict[int, QTreeWidgetItem] = {}

        root = QVBoxLayout(self)

        self.last_label = QLabel(self)
        root.addWidget(self.last_label)
        self.map_label = QLabel(self)
        self.map_label.setObjectName("Muted")
        root.addWidget(self.map_label)

        self.warning_label = QLabel(self)
        self.warning_label.setObjectName("Warning")
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        root.addWidget(self.warning_label)

        note = QLabel(NOTE_MSG, self)
        note.setObjectName("Muted")
        note.setWordWrap(True)
        root.addWidget(note)

        controls = QGridLayout()
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search by layline or region…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _: self.filter_tree())
        controls.addWidget(self.search, 0, 0)

        self.filter = QComboBox(self)
        for label, key in [
            ("All laylines", "all"),
            ("Unlocked", "unlocked"),
            ("Locked", "locked"),
        ]:
            self.filter.addItem(label, key)
        self.filter.currentIndexChanged.connect(lambda _: self.filter_tree())
        controls.addWidget(self.filter, 0, 1)

        self.count_label = QLabel(self)
        self.count_label.setObjectName("Muted")
        controls.addWidget(self.count_label, 0, 2)
        root.addLayout(controls)

        self.tree = QTreeWidget(self)
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Layline", "Status", "Last used"])
        self.tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for column in (1, 2):
            self.tree.header().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.tree.currentItemChanged.connect(self.on_selection_changed)
        root.addWidget(self.tree, 1)

        self.add_laylines()

        self.details_label = QLabel(self)
        self.details_label.setWordWrap(True)
        self.details_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        root.addWidget(self.details_label)

        self.unlock_layline = QCheckBox(
            "Unlock this layline before teleporting",
            self,
        )
        self.unlock_layline.setChecked(True)
        self.unlock_layline.setEnabled(False)
        root.addWidget(self.unlock_layline)

        self.button = QPushButton("Teleport", self)
        self.button.setEnabled(False)
        self.button.clicked.connect(self.main_window.on_apply)
        root.addWidget(self.button)

        self.update_details(None)

    def add_laylines(self):
        grouped: dict[str, list[Layline]] = {}
        for layline in LAYLINE_DATA:
            grouped.setdefault(layline.region, []).append(layline)

        for region in sorted(grouped, key=self.region_order):
            parent = QTreeWidgetItem([region, "", ""])
            parent.setFlags(
                parent.flags() & ~Qt.ItemFlag.ItemIsSelectable
            )
            parent.setExpanded(True)
            self.tree.addTopLevelItem(parent)
            for layline in sorted(
                grouped[region],
                key=lambda item: item.name.lower(),
            ):
                item = QTreeWidgetItem(
                    [layline.place, "Locked", ""]
                )
                item.setData(
                    0,
                    Qt.ItemDataRole.UserRole,
                    layline.id,
                )
                item.setToolTip(0, layline.name)
                parent.addChild(item)
                self.item_by_id[layline.id] = item

        self.tree.expandAll()

    @staticmethod
    def region_order(region: str) -> tuple[int, str]:
        try:
            return (REGION_ORDER.index(region), region)
        except ValueError:
            return (len(REGION_ORDER), region)

    def update_details(self, layline: Layline | None):
        if layline is None:
            self.details_label.setText(
                "Select a layline to see its region, map, coordinates, "
                "and unlock status."
            )
            return
        x, y, z = layline.position
        status = (
            "Unlocked"
            if self.save.position.is_layline_unlocked(layline)
            else "Locked"
        )
        last_used = (
            "Yes"
            if layline.id == self.save.position.last_layline_fount
            else "No"
        )
        self.details_label.setText("\n".join([
            f"Region: {layline.region}",
            f"Layline: {layline.place}",
            f"Layline ID: 0x{layline.id:02x}",
            f"Map: 0x{layline.map_upper:08x} / 0x{layline.map_lower:08x}",
            f"Coordinates: {x:.1f}, {y:.1f}, {z:.1f}",
            f"Status: {status}",
            f"Last used: {last_used}",
        ]))

    def on_selection_changed(
        self,
        current: QTreeWidgetItem | None,
        previous: QTreeWidgetItem | None,
    ):
        if current is None or current.parent() is None:
            self.selected_layline = None
            self.button.setEnabled(False)
            self.unlock_layline.setEnabled(False)
            self.update_details(None)
            return

        layline_id = current.data(0, Qt.ItemDataRole.UserRole)
        layline = LAYLINE_ID_MAP.get(layline_id)
        self.selected_layline = layline
        self.button.setEnabled(layline is not None)
        self.update_details(layline)
        if layline is None:
            self.unlock_layline.setEnabled(False)
            return

        unlocked = self.save.position.is_layline_unlocked(layline)
        self.unlock_layline.setEnabled(not unlocked)
        self.unlock_layline.setChecked(not unlocked)
        if unlocked:
            self.unlock_layline.setText("Already unlocked")
        else:
            self.unlock_layline.setText(
                "Unlock this layline before teleporting"
            )

    def filter_tree(self):
        query = self.search.text().strip().lower()
        filter_key = self.filter.currentData()
        position = self.save.position
        visible_count = 0
        unlocked_count = 0

        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            parent_visible = False
            for j in range(parent.childCount()):
                child = parent.child(j)
                layline_id = child.data(0, Qt.ItemDataRole.UserRole)
                layline = LAYLINE_ID_MAP[layline_id]
                unlocked = position.is_layline_unlocked(layline)
                if unlocked:
                    unlocked_count += 1
                searchable = (
                    f"{layline.name} {layline.region} {layline.place}"
                ).lower()
                matches = not query or all(
                    token in searchable for token in query.split()
                )
                if (
                    (filter_key == "unlocked" and not unlocked)
                    or (filter_key == "locked" and unlocked)
                ):
                    matches = False
                child.setHidden(not matches)
                if matches:
                    parent_visible = True
                    visible_count += 1
            parent.setHidden(not parent_visible)
            if parent_visible:
                parent.setExpanded(True)

        current = self.tree.currentItem()
        if current is not None and current.isHidden():
            self.tree.setCurrentItem(None)

        self.count_label.setText(
            f"{visible_count} shown · "
            f"{unlocked_count} / {len(LAYLINE_DATA)} unlocked"
        )

    def stack_refresh(self):
        position = self.save.position
        last = position.last_layline
        if last is None:
            self.last_label.setText("Last used layline: None")
        else:
            self.last_label.setText(f"Last used layline: {last.name}")

        coords = position.coordinates
        self.map_label.setText(
            f"Current map: 0x{position.current_map_upper:08x} / "
            f"0x{position.current_map_lower:08x} · "
            f"Position: {coords.x:.1f}, {coords.y:.1f}, {coords.z:.1f}"
        )

        invalid = (
            position.last_layline_fount != 0
            and last is None
        )
        self.warning_label.setVisible(invalid)
        if invalid:
            self.warning_label.setText(
                "WARNING: the last-used layline ID is not recognized. "
                "The game may return to the title screen."
            )

        for layline in LAYLINE_DATA:
            item = self.item_by_id[layline.id]
            item.setText(
                1,
                "Unlocked"
                if position.is_layline_unlocked(layline)
                else "Locked",
            )
            item.setText(
                2,
                "Last used"
                if layline.id == position.last_layline_fount
                else "",
            )

        self.filter_tree()
        if last is not None:
            item = self.item_by_id.get(last.id)
            if item is not None:
                self.tree.setCurrentItem(item)

    def on_apply_changes(self):
        if self.selected_layline is None:
            return
        self.save.position.layline_teleport(
            self.selected_layline,
            self.unlock_layline.isChecked(),
        )
        self.stack_remove()
