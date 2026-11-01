from collections.abc import Callable, Iterable
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from kadishutu.data.items import ITEM_ID_MAP

from ..components import Card, PageHeader
from ..shared import QU8, AppliableWidget
from .shared import GameScreenMixin


@dataclass(frozen=True)
class GrantItem:
    id: int
    effect: str


LEVEL_ITEMS = (
    GrantItem(82, "Raises the Nahobino by one level."),
    GrantItem(83, "Raises a demon by one level."),
)

NAHOBINO_STAT_ITEMS = (
    GrantItem(84, "Raises the Nahobino's max HP by 1."),
    GrantItem(85, "Raises the Nahobino's max MP by 1."),
    GrantItem(86, "Raises the Nahobino's Strength by 1."),
    GrantItem(87, "Raises the Nahobino's Magic by 1."),
    GrantItem(88, "Raises the Nahobino's Vitality by 1."),
    GrantItem(89, "Raises the Nahobino's Agility by 1."),
    GrantItem(90, "Raises the Nahobino's Luck by 1."),
)

DEMON_STAT_ITEMS = (
    GrantItem(91, "Raises a demon's max HP by 1."),
    GrantItem(92, "Raises a demon's max MP by 1."),
    GrantItem(93, "Raises a demon's Strength by 1."),
    GrantItem(94, "Raises a demon's Magic by 1."),
    GrantItem(95, "Raises a demon's Vitality by 1."),
    GrantItem(96, "Raises a demon's Agility by 1."),
    GrantItem(97, "Raises a demon's Luck by 1."),
)

DEMON_POTENTIAL_ITEMS = (
    GrantItem(98, "Raises a demon's Physical potential by 1."),
    GrantItem(99, "Raises a demon's Fire potential by 1."),
    GrantItem(100, "Raises a demon's Ice potential by 1."),
    GrantItem(101, "Raises a demon's Electric potential by 1."),
    GrantItem(102, "Raises a demon's Force potential by 1."),
    GrantItem(103, "Raises a demon's Light potential by 1."),
    GrantItem(104, "Raises a demon's Dark potential by 1."),
    GrantItem(105, "Raises a demon's Almighty potential by 1."),
    GrantItem(106, "Raises a demon's Recovery potential by 1."),
    GrantItem(107, "Raises a demon's Support potential by 1."),
    GrantItem(108, "Raises a demon's Ailment potential by 1."),
)

GROUPS = (
    (
        "Level-up items",
        "Gospels and Grimoires grant exactly one level in game.",
        LEVEL_ITEMS,
    ),
    (
        "Nahobino stat items",
        "Balms raise the Nahobino's stats when used in game.",
        NAHOBINO_STAT_ITEMS,
    ),
    (
        "Demon stat items",
        "Incenses raise a demon's stats when used in game.",
        DEMON_STAT_ITEMS,
    ),
    (
        "Demon potentials",
        "Sutras raise a demon's potential in one area when used in game.",
        DEMON_POTENTIAL_ITEMS,
    ),
)


class ItemGrantRow(QWidget):
    def __init__(
        self,
        item: GrantItem,
        box: QU8,
        on_add: Callable[[QU8, int], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.box = box
        self.effect = item.effect
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        meta = ITEM_ID_MAP[item.id]
        tooltip = f"{item.effect}\nItem ID: {item.id}"
        self.label = QLabel(meta.name, self)
        self.label.setToolTip(tooltip)
        self.label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        layout.addWidget(self.label, 1)

        box.setToolTip(f"{tooltip}\nMaximum: {meta.limit}")
        box.setFixedWidth(68)
        layout.addWidget(box)

        for text, amount in (("+1", 1), ("+5", 5), ("Max", None)):
            button = QPushButton(text, self)
            button.setFixedWidth(52)
            if amount is None:
                button.clicked.connect(
                    lambda _=False, b=box: on_add(b, b.maximum())
                )
            else:
                button.clicked.connect(
                    lambda _=False, b=box, n=amount: on_add(b, n)
                )
            layout.addWidget(button)


class ProgressionScreen(QWidget, GameScreenMixin, AppliableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_boxes: dict[int, QU8] = {}
        self.item_rows: dict[int, ItemGrantRow] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content = QWidget()
        self.content.setObjectName("ScrollContent")
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll)

        self.l = QVBoxLayout(self.content)
        self.l.setContentsMargins(24, 24, 24, 24)
        self.l.setSpacing(16)
        self.l.addWidget(PageHeader(
            "Progression",
            "Grant level-up and stat items. The game applies them.",
            self.content,
        ))

        for title, note, items in GROUPS:
            self.l.addWidget(self.build_group(title, note, items))
        self.l.addStretch()

    def build_group(
        self,
        title: str,
        note: str,
        items: Iterable[GrantItem],
    ) -> Card:
        card = Card(self.content)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        title_label = QLabel(title, card)
        title_label.setObjectName("SectionTitle")
        layout.addWidget(title_label)

        note_label = QLabel(note, card)
        note_label.setObjectName("Muted")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)

        rows = QVBoxLayout()
        rows.setSpacing(4)
        for item in items:
            meta = ITEM_ID_MAP[item.id]
            box = QU8()
            box.setMaximum(meta.limit)
            self.item_boxes[item.id] = box
            row = ItemGrantRow(item, box, self.add_items, card)
            self.item_rows[item.id] = row
            rows.addWidget(row)
        layout.addLayout(rows)
        return card

    def add_items(self, box: QU8, amount: int):
        box.setValue(min(box.maximum(), box.value() + amount))

    def stack_refresh(self):
        for item_id, box in self.item_boxes.items():
            box.setValue(self.save.items.from_id(item_id).amount)
            box.set_modified(False)

    def on_apply_changes(self):
        for item_id, box in self.item_boxes.items():
            if not box.get_modified():
                continue
            self.save.items.from_id(item_id).amount = box.value()
            box.set_modified(False)
