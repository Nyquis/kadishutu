from PySide6.QtWidgets import (
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

from ..advanced import advanced_mode
from ..components import Risk, RiskBadge
from ..shared import QU16, AppliableWidget, hboxed
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

        transient_note = QLabel(
            "Current and Healable HP/MP are game-managed. The game may "
            "clamp or restore them after battle, death, revival, or healing.",
            self,
        )
        transient_note.setObjectName("Muted")
        transient_note.setWordWrap(True)
        root.addLayout(hboxed(
            RiskBadge(
                "game-managed",
                Risk.TRANSIENT,
                "These stored values can be changed, but the game may "
                "recalculate them later.",
            ),
            transient_note,
        ))

        self.advanced_mode = advanced_mode()
        self.advanced_mode.changed.connect(self.on_advanced_mode_changed)
        self.advanced_note = QLabel(
            "Advanced editing is off. Enable it in the status bar to edit "
            "stored Current values directly.",
            self,
        )
        self.advanced_note.setObjectName("Muted")
        self.advanced_note.setWordWrap(True)
        root.addWidget(self.advanced_note)

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
        self.hp_one_button = QPushButton("Set HP to 1", self)
        self.hp_one_button.setToolTip(
            "Preset: set Healable HP to 1 and leave max HP unchanged. "
            "The game may restore it after death, revival, or healing."
        )
        self.hp_one_button.clicked.connect(self.on_set_hp_one)
        buttons.addWidget(self.hp_one_button, 0, 2)
        root.addLayout(buttons)

        self.hp_warning = QLabel(self)
        self.hp_warning.setObjectName("Warning")
        self.hp_warning.setWordWrap(True)
        self.hp_warning.setVisible(False)
        root.addWidget(self.hp_warning)
        self.widgets["healable"]["hp"].valueChanged.connect(
            self.update_hp_warning
        )
        root.addStretch()

        self.on_advanced_mode_changed()
        self.stack_refresh()

    def on_advanced_mode_changed(self, *_):
        enabled = self.advanced_mode.enabled
        self.advanced_note.setVisible(not enabled)
        self.set_current_editable()

    def set_current_editable(self, *_):
        editable = self.advanced_mode.enabled
        for widget in self.widgets["current"].values():
            widget.setReadOnly(not editable)

    def on_set_hp_one(self):
        self.widgets["healable"]["hp"].setValue(1)

    def update_hp_warning(self, value: int):
        if value != 1:
            self.hp_warning.setVisible(False)
            return
        self.hp_warning.setText(
            "Healable HP is set to 1. Max HP is unchanged. The game may "
            "restore or clamp it after battle, death, revival, or healing."
        )
        self.hp_warning.setVisible(True)

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

        if self.advanced_mode.enabled:
            for stat, widget in self.widgets["current"].items():
                widget.update_if_modified(
                    self.apply_widget("current", stat)
                )
        else:
            self.stats.recalculate()

        self.stack_refresh()
