
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.game_save.demonlike import DemonLikeEditor
from kadishutu.data.leveling import exp_progress

from ..advanced import advanced_mode
from ..components import Risk, RiskBadge
from ..shared import QU8, QU32, AppliableWidget, hboxed
from .affinities import AffinityEditorScreen
from .potentials import PotentialEditorScreen
from .shared import GameScreenMixin
from .skills import SkillEditorScreen
from .stats import StatEditorScreen

LEVEL_MUT_WARNING = """WARNING: Changing the level from here is ill-advised.
This editor DOES NOT emulate the changes that would occur within the game \
(such as updating base and current stats, learning skills, etc.).
Please, use Gospels or Grimores to level up instead."""
WARN_EMOJI = "⚠️"


class DemonLikeEditorScreen(QWidget, GameScreenMixin, AppliableWidget):
    demon: DemonLikeEditor

    def __init__(self, demon: DemonLikeEditor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.demon = demon
        self.dl_layout = QVBoxLayout()

        self.side_panel_widgets: list[QWidget] = []

        level_label = QLabel(f"Level ({WARN_EMOJI})")
        level_label.setToolTip(LEVEL_MUT_WARNING)
        self.level_box = QU8()
        self.level_box.setToolTip(LEVEL_MUT_WARNING)
        self.dl_layout.addLayout(hboxed(
            level_label,
            self.level_box
        ))

        exp_label = QLabel("Exp")
        self.exp_box = QU32()
        self.dl_layout.addLayout(hboxed(
            exp_label,
            self.exp_box
        ))

        self.exp_hint = QLabel()
        self.exp_hint.setWordWrap(True)
        self.dl_layout.addWidget(self.exp_hint)

        self.derived_note = QLabel(
            "Changing level or EXP does not recalculate stats or learn "
            "skills. The game may correct them on the next level-up.",
            self,
        )
        self.derived_note.setObjectName("Muted")
        self.derived_note.setWordWrap(True)
        self.separate_badge = RiskBadge(
            "separate fields",
            Risk.INFO,
            "Level, EXP, stats and skills are stored separately. "
            "Editing one does not update the others.",
        )
        self.dl_layout.addLayout(hboxed(
            self.separate_badge,
            self.derived_note,
        ))

        self.advanced_mode = advanced_mode()
        self.advanced_mode.changed.connect(self.refresh_advanced_state)
        self.level_note = QLabel(
            "Advanced editing is off. Enable it in the status bar to change "
            "level or EXP.",
            self,
        )
        self.level_note.setObjectName("Muted")
        self.level_note.setWordWrap(True)
        self.dl_layout.addWidget(self.level_note)

        self.last_box = 5

        for name, fun in [
            ("Stats", lambda: StatEditorScreen(
                self.demon.stats, self.demon.healable
            )),
            ("Skills", lambda: SkillEditorScreen(
                self.demon.skills, self.demon.innate_skill
            )),
            ("Affinities", lambda: AffinityEditorScreen(
                self.demon.affinities
            )),
            ("Potentials", lambda: PotentialEditorScreen(
                self.demon.potentials
            ))
        ]:
            button = QPushButton(name)
            button.clicked.connect(self.spawner(fun))
            self.side_panel_widgets.append(button)

        for widget in self.side_panel_widgets:
            self.dl_layout.addWidget(widget)
        self.dl_layout.addStretch()
        self.refresh_advanced_state()

    def refresh_advanced_state(self, *_):
        editable = self.advanced_mode.enabled
        for box in (self.level_box, self.exp_box):
            box.setReadOnly(not editable)
            box.setButtonSymbols(
                QAbstractSpinBox.ButtonSymbols.UpDownArrows
                if editable
                else QAbstractSpinBox.ButtonSymbols.NoButtons
            )
        self.level_note.setVisible(not editable)

    def stack_refresh(self):
        self.level_box.setValue(self.demon.level)
        self.exp_box.setValue(self.demon.exp)
        self.refresh_exp_hint()

    def exp_required(self) -> int | None:
        return None

    def refresh_exp_hint(self):
        required = self.exp_required()
        if required is None:
            self.exp_hint.setText("EXP to next level: unknown")
            return
        progress = exp_progress(self.exp_box.value(), required)
        percent = 0 if progress is None else round(progress * 100)
        self.exp_hint.setText(
            f"EXP to next level: {required:,} ({percent}% earned)"
        )

    def on_apply_changes(self):
        self.level_box.setattr_if_modified(self.demon, "level")
        self.exp_box.setattr_if_modified(self.demon, "exp")
        self.refresh_exp_hint()
