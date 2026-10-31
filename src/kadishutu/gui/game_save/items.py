
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
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

        self.setWidgetResizable(True)
        self.inner = QWidget()
        self.setWidget(self.inner)
        self.l = QGridLayout(self.inner)

        self.max_button = QPushButton("Max all", self.inner)
        self.max_button.clicked.connect(self.max_all)
        self.l.addWidget(self.max_button, 0, 0, 1, 2)
        self.clear_button = QPushButton("Clear all", self.inner)
        self.clear_button.clicked.connect(self.clear_all)
        self.l.addWidget(self.clear_button, 0, 2, 1, 2)

        for i, meta in enumerate(items):
            row = i + 1
            item = self.save.items.from_meta(meta)
            label = QLabel(item.name)
            desc = item.meta.desc
            if desc is not None:
                label.setToolTip(desc)
            self.l.addWidget(label, row, 1)
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
            limit_label = QLabel("Limit: " + str(item.limit))
            if desc is not None:
                limit_label.setToolTip(desc)
            self.l.addWidget(limit_label, row, 2)
            amount_box = QU8()
            if desc is not None:
                amount_box.setToolTip(desc)
            self.l.addWidget(amount_box, row, 3)
            self.items.append((item, label, amount_box))

    def max_all(self):
        for item, _, amount_box in self.items:
            amount_box.setValue(item.limit)

    def clear_all(self):
        for _, _, amount_box in self.items:
            amount_box.setValue(0)

    def stack_refresh(self):
        for item, _, amount_box in self.items:
            amount_box.setValue(item.amount)

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
