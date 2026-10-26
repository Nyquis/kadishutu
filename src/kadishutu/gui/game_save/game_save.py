from pathlib import Path

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.game_save import GameSaveEditor
from kadishutu.core.shared.file_handling import DecryptedSave
from kadishutu.plugin.loader import PLUGIN_MANAGER

from ..components import Card, CategoryCard, PageHeader
from ..shared import (
    QU32,
    AppliableWidget,
    SaveScreenMixin,
)
from .alignment import AlignmentEditorScreen
from .cross_cycle import CrossCycleEditorScreen
from .demons import DemonSelectorScreen
from .dlc import DlcEditorScreen
from .essences import EssenceEditorScreen
from .items import ItemEditorScreen
from .miracles import MiracleEditorScreen
from .player import PlayerEditorScreen
from .plugin import GameSavePluginScreen
from .settings import SettingsEditorScreen
from .teleport import TeleporterScreen


class GameSaveEditorScreen(SaveScreenMixin, QWidget, AppliableWidget):
    path: Path
    raw_save: DecryptedSave
    save: GameSaveEditor
    modified: bool

    def __init__(
        self,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.save = GameSaveEditor(self.raw_save)

        self.outer = QVBoxLayout(self)
        self.outer.setContentsMargins(0, 0, 0, 0)
        self.outer.setSpacing(0)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.content = QWidget()
        self.content.setObjectName("ScrollContent")
        self.scroll.setWidget(self.content)
        self.outer.addWidget(self.scroll)

        self.l = QVBoxLayout(self.content)
        self.l.setContentsMargins(24, 24, 24, 24)
        self.l.setSpacing(16)

        self.header = PageHeader("Save Overview", str(self.path), self.content)
        self.l.addWidget(self.header)

        self.stats_card = Card(self.content)
        stats_layout = QHBoxLayout(self.stats_card)
        stats_layout.setContentsMargins(18, 16, 18, 16)
        stats_layout.setSpacing(28)
        self.macca = QU32()
        stats_layout.addLayout(self._stat_block("Macca", self.macca))
        self.glory = QU32()
        stats_layout.addLayout(self._stat_block("Glory", self.glory))
        stats_layout.addStretch()
        self.l.addWidget(self.stats_card)

        categories_label = QLabel("Categories", self.content)
        categories_label.setObjectName("SectionTitle")
        self.l.addWidget(categories_label)

        self.category_grid = QGridLayout()
        self.category_grid.setHorizontalSpacing(12)
        self.category_grid.setVerticalSpacing(12)
        for index, (name, description, cls) in enumerate([
            ("DLC", "Manage downloadable content", DlcEditorScreen),
            ("Player", "Names, stats, and healing", PlayerEditorScreen),
            ("Demons", "Party, compendium, and affinities", DemonSelectorScreen),
            ("Miracles", "Unlock and upgrade miracles", MiracleEditorScreen),
            ("Items", "Consumables, relics, and key items", ItemEditorScreen),
            ("Essences", "Essence inventory", EssenceEditorScreen),
            (
                "Layline Crossing",
                "Unlock and travel between laylines",
                TeleporterScreen,
            ),
            ("Alignment", "Law, chaos, and neutrality", AlignmentEditorScreen),
            ("Settings", "Difficulty and game settings", SettingsEditorScreen),
            ("Meta", "Cycles, endings, and late bonuses", CrossCycleEditorScreen),
        ]):
            card = CategoryCard(name, description, self.content)
            card.clicked.connect(self.spawner(cls))
            self.category_grid.addWidget(card, index // 2, index % 2)
        self.l.addLayout(self.category_grid)

        extensions_label = QLabel("Extensions", self.content)
        extensions_label.setObjectName("SectionTitle")
        self.l.addWidget(extensions_label)

        self.plugins_button = CategoryCard(
            "Plugins",
            "Game-specific plugin screens",
            self.content,
        )
        self.plugins_button.clicked.connect(self.spawner(GameSavePluginScreen))
        self.l.addWidget(self.plugins_button)

        if not PLUGIN_MANAGER.which_have_stage("gui_game_component"):
            self.plugins_button.setEnabled(False)
            self.plugins_button.title_label.setEnabled(False)
            self.plugins_button.description_label.setEnabled(False)

        self.l.addStretch()

    def _stat_block(self, label: str, widget: QWidget) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(4)
        caption = QLabel(label)
        caption.setObjectName("Muted")
        layout.addWidget(caption)
        widget.setMinimumWidth(180)
        layout.addWidget(widget)
        return layout

    def stack_refresh(self):
        self.header.set_subtitle(str(self.path))
        self.macca.setValue(self.save.macca)
        self.glory.setValue(self.save.glory)

    def on_apply_changes(self):
        self.macca.setattr_if_modified(self.save, "macca")
        self.glory.setattr_if_modified(self.save, "glory")
