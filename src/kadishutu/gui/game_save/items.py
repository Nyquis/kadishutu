
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QWidget,
)

from kadishutu.core.game_save.items import ItemEditor
from kadishutu.data.items import (
    CONSUMABLES_RANGE,
    KEY_ITEMS_RANGE,
    RELICS_RANGE_1,
    RELICS_RANGE_2,
    Item,
    items_from,
)

from ..iconloader import ICON_LOADER, handle_image_loading_error
from ..shared import QU8, AppliableWidget
from .shared import GameScreenMixin


class ItemEditorWidget(QScrollArea, GameScreenMixin, AppliableWidget):
    def __init__(self, items: list[Item], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items: list[tuple[ItemEditor, QLabel, QU8]] = []
        self.row_widgets: list[list[QWidget]] = []
        self.visible_indices: set[int] = set()
        self.visible_count = 0

        self.setWidgetResizable(True)
        self.inner = QWidget()
        self.setWidget(self.inner)
        self.l = QGridLayout(self.inner)

        self.search = QLineEdit(self.inner)
        self.search.setPlaceholderText(
            "Search by name, ID, category, effect, or flag…"
        )
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _: self.filter_items())
        self.l.addWidget(self.search, 0, 0, 1, 4)
        self.count_label = QLabel(self.inner)
        self.count_label.setObjectName("Muted")
        self.l.addWidget(self.count_label, 0, 4)

        self.max_button = QPushButton("Max all", self.inner)
        self.max_button.clicked.connect(self.max_all)
        self.l.addWidget(self.max_button, 1, 0, 1, 2)
        self.clear_button = QPushButton("Clear all", self.inner)
        self.clear_button.clicked.connect(self.clear_all)
        self.l.addWidget(self.clear_button, 1, 2, 1, 3)

        self.validation_label = QLabel(self.inner)
        self.validation_label.setObjectName("Warning")
        self.validation_label.setVisible(False)
        self.l.addWidget(self.validation_label, 2, 0, 1, 5)

        for i, meta in enumerate(items):
            row = i + 3
            item = self.save.items.from_meta(meta)
            row_widgets: list[QWidget] = []
            label = QLabel(item.name)
            desc = item.meta.desc
            if desc is not None:
                label.setToolTip(desc)
            self.l.addWidget(label, row, 1)
            row_widgets.append(label)
            try:
                element = item.meta.icon
                pak = ICON_LOADER.element_icon(element)
            except Exception as e:
                handle_image_loading_error(e, "element", element)
            else:
                pix = pak.pixmap.scaled(pak.size_div(2))
                icon = QLabel()
                icon.setFixedSize(pix.size())
                icon.setPixmap(pix)
                if desc is not None:
                    icon.setToolTip(desc)
                self.l.addWidget(icon, row, 0)
                row_widgets.append(icon)
            limit_label = QLabel(self.limit_text(item))
            limit_label.setToolTip(self.limit_tooltip(item))
            self.l.addWidget(limit_label, row, 2)
            row_widgets.append(limit_label)
            details_label = QLabel(self.details_text(item))
            details_label.setObjectName("Muted")
            details_label.setToolTip(self.details_tooltip(item))
            self.l.addWidget(details_label, row, 3)
            row_widgets.append(details_label)
            amount_box = QU8()
            amount_box.setMaximum(max(item.limit, item.amount))
            amount_box.setToolTip(self.details_tooltip(item))
            amount_box.valueChanged.connect(
                lambda _: self.update_validation()
            )
            self.l.addWidget(amount_box, row, 4)
            row_widgets.append(amount_box)
            self.items.append((item, label, amount_box))
            self.row_widgets.append(row_widgets)

        self.update_validation()
        self.filter_items()

    @staticmethod
    def limit_text(item: ItemEditor) -> str:
        if item.limit == 1:
            return "Unique"
        return f"Max {item.limit}"

    @staticmethod
    def limit_tooltip(item: ItemEditor) -> str:
        if item.limit == 1:
            return "This item does not stack."
        return f"Maximum amount: {item.limit}"

    @staticmethod
    def details_text(item: ItemEditor) -> str:
        parts: list[str] = []
        meta = item.meta
        if meta.infinite:
            parts.append("Infinite")
        scene = meta.use_scene_name
        if scene not in ("Unknown", "Not usable"):
            parts.append(scene)
        target = meta.use_target_name
        if target != "Unknown":
            parts.append(f"{target} target")
        return " · ".join(parts)

    @staticmethod
    def details_tooltip(item: ItemEditor) -> str:
        meta = item.meta
        lines: list[str] = []
        if meta.desc:
            lines.append(meta.desc)
        lines.append(f"Category: {meta.category.replace('_', ' ').title()}")
        if meta.item_kind_name != "Unknown":
            lines.append(f"Kind: {meta.item_kind_name}")
        if meta.use_scene_name != "Unknown":
            lines.append(f"Usable: {meta.use_scene_name}")
        if meta.use_target_name != "Unknown":
            lines.append(f"Target: {meta.use_target_name}")
        if meta.infinite:
            lines.append("Infinite use")
        lines.append(ItemEditorWidget.limit_tooltip(item))
        return "\n".join(lines)

    def matches_query(self, item: ItemEditor, query: str) -> bool:
        if not query:
            return True
        if query.isdigit():
            return query == str(item.meta.id)
        return all(token in item.meta.search_text for token in query.split())

    def filter_items(self):
        query = self.search.text().strip().lower()
        visible: list[int] = []
        for index, (item, _, _) in enumerate(self.items):
            matches = self.matches_query(item, query)
            for widget in self.row_widgets[index]:
                widget.setVisible(matches)
            if matches:
                visible.append(index)
        self.visible_indices = set(visible)
        self.visible_count = len(visible)
        if query:
            self.count_label.setText(
                f"{self.visible_count} / {len(self.items)}"
            )
        else:
            self.count_label.setText(f"{len(self.items)} items")

    def max_all(self):
        for index in sorted(self.visible_indices):
            item, _, amount_box = self.items[index]
            amount_box.setValue(item.limit)

    def clear_all(self):
        for index in sorted(self.visible_indices):
            _, _, amount_box = self.items[index]
            amount_box.setValue(0)

    def update_validation(self):
        over_limit = sum(
            1
            for item, _, amount_box in self.items
            if amount_box.value() > item.limit
        )
        self.validation_label.setVisible(over_limit > 0)
        if over_limit:
            noun = "item" if over_limit == 1 else "items"
            self.validation_label.setText(
                f"{over_limit} {noun} exceed the in-game limit. "
                "Lower the amount before saving."
            )

    def stack_refresh(self):
        for item, _, amount_box in self.items:
            amount_box.setMaximum(max(item.limit, item.amount))
            amount_box.setValue(item.amount)
        self.update_validation()
        self.filter_items()

    def on_apply_changes(self):
        for item, _, amount_box in self.items:
            amount_box.setattr_if_modified(item, "amount")


class ItemEditorScreen(QTabWidget, GameScreenMixin, AppliableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tabs: list[ItemEditorWidget] = []

        for name, item_ranges in [
            ("Consumables", [CONSUMABLES_RANGE]),
            ("Relics", [RELICS_RANGE_1, RELICS_RANGE_2]),
            ("Key Items", [KEY_ITEMS_RANGE])
        ]:
            items = items_from(*item_ranges)
            widget = ItemEditorWidget(items)
            self.tabs.append(widget)
            self.addTab(widget, name)

    def stack_refresh(self):
        for tab in self.tabs:
            tab.stack_refresh()

    def on_apply_changes(self):
        for tab in self.tabs:
            tab.on_apply_changes()
