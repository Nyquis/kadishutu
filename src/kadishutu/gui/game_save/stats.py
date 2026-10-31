from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.game_save.stats import (
    STATS_NAMES,
    HealableEditor,
    StatBlockEditor,
)

from ..shared import QU16, AppliableWidget
from .shared import GameScreenMixin

STAT_COLUMNS = (
    ("Natural", "base"),
    ("Bonuses", "changes"),
    ("Current", "current"),
)
STAT_ATTRS = {
    "natural": "base",
    "bonuses": "changes",
    "current": "current",
}
HEALABLE_TIP = (
    "Current HP/MP available to heal. Use “Heal HP/MP” to copy the "
    "current values."
)


class StatEditorScreen(QWidget, GameScreenMixin, AppliableWidget):
    def __init__(
        self,
        stats: StatBlockEditor,
        healable: HealableEditor,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.stats = stats
        self.healable = healable
        self.labels: list[QLabel] = []
        self.headers: list[QLabel] = []
        self.widgets: dict[str, dict[str, QU16]] = {
            "natural": {},
            "bonuses": {},
            "current": {},
            "healable": {},
        }

        root = QVBoxLayout(self)

        help_label = QLabel(
            "Natural + Bonuses = Current. Current is recalculated when you "
            "apply unless direct editing is enabled.",
            self,
        )
        help_label.setObjectName("Muted")
        help_label.setWordWrap(True)
        root.addWidget(help_label)

        self.advanced = QCheckBox("Edit current directly", self)
        self.advanced.setToolTip(
            "Advanced: edit the stored Current block instead of "
            "recalculating it from Natural + Bonuses."
        )
        self.advanced.checkStateChanged.connect(self.set_current_editable)
        root.addWidget(self.advanced)

        self.grid = QGridLayout()
        root.addLayout(self.grid)

        for column, (title, attr) in enumerate(
            (("Stat", ""), *STAT_COLUMNS),
        ):
            header = QLabel(title, self)
            header.setObjectName("Muted")
            if attr:
                header.setToolTip(
                    f"Stored {attr} stats."
                    if attr != "current"
                    else "Natural + Bonuses; used by the game."
                )
            self.grid.addWidget(header, 0, column)
            self.headers.append(header)

        healable_header = QLabel("Healable HP/MP", self)
        healable_header.setObjectName("Muted")
        healable_header.setToolTip(HEALABLE_TIP)
        self.grid.addWidget(healable_header, 0, 4)
        self.headers.append(healable_header)

        for i, stat_name in enumerate(STATS_NAMES, 1):
            label = QLabel(stat_name, self)
            self.labels.append(label)
            self.grid.addWidget(label, i, 0)
            stat = stat_name.lower()

            for column, (_, attr) in enumerate(STAT_COLUMNS, 1):
                widget = QU16()
                widget.setFixedWidth(90)
                widget.setToolTip(f"Stored {stat_name} {attr} value.")
                ty = "natural" if attr == "base" else (
                    "bonuses" if attr == "changes" else "current"
                )
                value = self.stats.__getattribute__(attr).__getattribute__(
                    stat
                )
                widget.setValue(value)
                self.widgets[ty][stat] = widget
                self.grid.addWidget(widget, i, column)

            if stat in ("hp", "mp"):
                widget = QU16()
                widget.setFixedWidth(90)
                widget.setToolTip(HEALABLE_TIP)
                widget.setValue(self.healable.__getattribute__(stat))
                self.widgets["healable"][stat] = widget
                self.grid.addWidget(widget, i, 4)
            else:
                empty = QLabel("—", self)
                empty.setObjectName("Muted")
                self.grid.addWidget(empty, i, 4)

        buttons = QGridLayout()
        self.recalculate_button = QPushButton("Recalculate current", self)
        self.recalculate_button.setToolTip(
            "Set Current to Natural + Bonuses."
        )
        self.recalculate_button.clicked.connect(self.recalculate_preview)
        buttons.addWidget(self.recalculate_button, 0, 0)
        self.heal_button = QPushButton("Heal HP/MP", self)
        self.heal_button.setToolTip(HEALABLE_TIP)
        self.heal_button.clicked.connect(self.on_heal)
        buttons.addWidget(self.heal_button, 0, 1)
        root.addLayout(buttons)
        root.addStretch()

        self.set_current_editable()
        self.stack_refresh()

    def set_current_editable(self, *_):
        editable = self.advanced.isChecked()
        for widget in self.widgets["current"].values():
            widget.setReadOnly(not editable)

    def recalculate_preview(self):
        for stat in STATS_NAMES:
            stat = stat.lower()
            value = (
                self.widgets["natural"][stat].value()
                + self.widgets["bonuses"][stat].value()
            )
            self.widgets["current"][stat].setValue(value)

    def on_heal(self):
        for stat in ("hp", "mp"):
            value = self.widgets["current"][stat].value()
            self.widgets["healable"][stat].setValue(value)

    def apply_widget(self, ty: str, stat: str):
        if ty == "healable":
            def inner(value: int):
                self.healable.__setattr__(stat, value)
        else:
            attr = STAT_ATTRS[ty]

            def inner(value: int):
                self.stats.__getattribute__(attr).__setattr__(stat, value)
        return inner

    def stack_refresh(self):
        for ty, attr in STAT_ATTRS.items():
            source = self.stats.__getattribute__(attr)
            for stat, widget in self.widgets[ty].items():
                widget.setValue(source.__getattribute__(stat))
                widget.set_modified(False)
        for stat, widget in self.widgets["healable"].items():
            widget.setValue(self.healable.__getattribute__(stat))
            widget.set_modified(False)

    def on_apply_changes(self):
        for ty in ("natural", "bonuses", "healable"):
            for stat, widget in self.widgets[ty].items():
                widget.update_if_modified(self.apply_widget(ty, stat))

        if self.advanced.isChecked():
            for stat, widget in self.widgets["current"].items():
                widget.update_if_modified(
                    self.apply_widget("current", stat)
                )
        else:
            self.stats.recalculate()

        self.stack_refresh()
