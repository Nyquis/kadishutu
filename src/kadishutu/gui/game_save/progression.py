from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from kadishutu.data.items import ITEM_ID_MAP
from kadishutu.data.leveling import load_leveling_data, nahobino_exp_to_next

from ..components import Card, PageHeader
from ..shared import QU8, AppliableWidget
from .shared import GameScreenMixin

LEVEL_ITEMS = (
    (82, "Gospel", "Raises the Nahobino by one level."),
    (83, "Grimoire", "Raises a demon by one level."),
)

BALM_IDS = range(84, 91)
INCENSE_IDS = range(91, 98)


class ProgressionScreen(QWidget, GameScreenMixin, AppliableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_boxes: dict[int, QU8] = {}
        self.root = QVBoxLayout(self)

        self.header = PageHeader(
            "Progression",
            "Plan levels and grant the items that apply them in game.",
            self,
        )
        self.root.addWidget(self.header)

        self.level_card = Card(self)
        level_layout = QVBoxLayout(self.level_card)
        level_layout.setContentsMargins(18, 16, 18, 16)
        level_layout.setSpacing(8)
        self.level_label = QLabel(self.level_card)
        self.level_label.setObjectName("SectionTitle")
        level_layout.addWidget(self.level_label)
        self.exp_label = QLabel(self.level_card)
        self.exp_label.setObjectName("Muted")
        self.exp_label.setWordWrap(True)
        level_layout.addWidget(self.exp_label)

        target_row = QVBoxLayout()
        target_row.addWidget(QLabel("Target level", self.level_card))
        self.target_box = QSpinBox(self.level_card)
        self.target_box.setRange(1, 150)
        self.target_box.valueChanged.connect(self.update_plan)
        target_row.addWidget(self.target_box)
        level_layout.addLayout(target_row)

        self.plan_label = QLabel(self.level_card)
        self.plan_label.setWordWrap(True)
        level_layout.addWidget(self.plan_label)
        self.plan_button = QPushButton(
            "Set Gospels to cover target", self.level_card
        )
        self.plan_button.setToolTip(
            "Set the Gospel amount to the number of levels needed, without "
            "lowering an existing stock."
        )
        self.plan_button.clicked.connect(self.set_gospels_for_target)
        level_layout.addWidget(self.plan_button)
        self.root.addWidget(self.level_card)

        self.level_items_card = Card(self)
        level_items_layout = QVBoxLayout(self.level_items_card)
        level_items_layout.setContentsMargins(18, 16, 18, 16)
        level_items_layout.setSpacing(8)
        title = QLabel("Level-up items", self.level_items_card)
        title.setObjectName("SectionTitle")
        level_items_layout.addWidget(title)
        note = QLabel(
            "Gospels and Grimoires grant exactly one level in game. This "
            "editor only changes how many are in the inventory.",
            self.level_items_card,
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        level_items_layout.addWidget(note)
        level_items_layout.addLayout(self.build_item_grid(LEVEL_ITEMS))
        self.root.addWidget(self.level_items_card)

        self.stat_items_card = Card(self)
        stat_layout = QVBoxLayout(self.stat_items_card)
        stat_layout.setContentsMargins(18, 16, 18, 16)
        stat_layout.setSpacing(8)
        title = QLabel("Stat items", self.stat_items_card)
        title.setObjectName("SectionTitle")
        stat_layout.addWidget(title)
        note = QLabel(
            "Balms and incenses raise stats when used in game. The game "
            "applies its own caps and messages.",
            self.stat_items_card,
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        stat_layout.addWidget(note)

        stat_grid = QGridLayout()
        stat_grid.addWidget(QLabel("Balms", self.stat_items_card), 0, 0)
        stat_grid.addWidget(QLabel("Incenses", self.stat_items_card), 0, 1)
        stat_grid.addLayout(
            self.build_item_grid([
                (item_id, ITEM_ID_MAP[item_id].name, "Raises one stat by 1.")
                for item_id in BALM_IDS
            ]),
            1,
            0,
        )
        stat_grid.addLayout(
            self.build_item_grid([
                (item_id, ITEM_ID_MAP[item_id].name, "Raises one stat by 1.")
                for item_id in INCENSE_IDS
            ]),
            1,
            1,
        )
        stat_layout.addLayout(stat_grid)
        self.root.addWidget(self.stat_items_card)
        self.root.addStretch()

    def build_item_grid(self, items) -> QGridLayout:
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        for row, (item_id, name, description) in enumerate(items):
            meta = ITEM_ID_MAP[item_id]
            label = QLabel(f"{name} (#{item_id})", self)
            label.setToolTip(description)
            grid.addWidget(label, row, 0)
            box = QU8()
            box.setMaximum(meta.limit)
            box.setToolTip(description)
            self.item_boxes[item_id] = box
            grid.addWidget(box, row, 1)
            plus_one = QPushButton("+1", self)
            plus_one.clicked.connect(
                lambda _=False, b=box, n=1: self.add_items(b, n)
            )
            grid.addWidget(plus_one, row, 2)
            plus_five = QPushButton("+5", self)
            plus_five.clicked.connect(
                lambda _=False, b=box, n=5: self.add_items(b, n)
            )
            grid.addWidget(plus_five, row, 3)
            max_button = QPushButton("Max", self)
            max_button.clicked.connect(
                lambda _=False, b=box: self.add_items(b, b.maximum())
            )
            grid.addWidget(max_button, row, 4)
        return grid

    def add_items(self, box: QU8, amount: int):
        box.setValue(min(box.maximum(), box.value() + amount))

    def levels_needed(self) -> int:
        return max(0, self.target_box.value() - self.player.level)

    def exp_needed(self) -> int | None:
        level = self.player.level
        target = self.target_box.value()
        if target <= level:
            return 0
        first = nahobino_exp_to_next(level)
        if first is None:
            return None
        total = max(0, first - self.player.exp)
        for current in range(level + 1, target):
            requirement = nahobino_exp_to_next(current)
            if requirement is None:
                return None
            total += requirement
        return total

    @property
    def player(self):
        return self.save.player

    def stack_refresh(self):
        level = self.player.level
        requirement = nahobino_exp_to_next(level)
        if requirement is None:
            progress = "max level"
        else:
            percent = round(min(1.0, self.player.exp / requirement) * 100)
            progress = (
                f"{self.player.exp:,} / {requirement:,} EXP "
                f"({percent}% earned)"
            )
        self.level_label.setText(f"Nahobino: level {level}")
        self.exp_label.setText(f"Current progress: {progress}")

        max_level = load_leveling_data().max_level
        self.target_box.blockSignals(True)
        self.target_box.setMaximum(max_level)
        self.target_box.setMinimum(level)
        if self.target_box.value() < level:
            self.target_box.setValue(level)
        self.target_box.blockSignals(False)

        for item_id, box in self.item_boxes.items():
            box.setValue(self.save.items.from_id(item_id).amount)
            box.set_modified(False)

        self.update_plan()

    def update_plan(self, *_):
        levels = self.levels_needed()
        exp = self.exp_needed()
        exp_text = "outside the EXP table" if exp is None else f"{exp:,} EXP"
        self.plan_label.setText(
            f"Levels needed: {levels}\n"
            f"EXP from here: {exp_text}\n"
            f"Gospels needed: {levels}"
        )

    def set_gospels_for_target(self):
        levels = self.levels_needed()
        box = self.item_boxes[82]
        current = box.value()
        wanted = max(current, levels)
        box.setValue(min(box.maximum(), wanted))
        if wanted > box.maximum():
            self.plan_label.setText(
                self.plan_label.text()
                + f"\nTarget needs {levels} Gospels, but the limit is "
                f"{box.maximum()}. Grant more in batches."
            )

    def on_apply_changes(self):
        for item_id, box in self.item_boxes.items():
            if not box.get_modified():
                continue
            self.save.items.from_id(item_id).amount = box.value()
            box.set_modified(False)
