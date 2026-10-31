from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from kadishutu.data.demons import DEMON_ID_MAP, Demon

from ..components import Card, PageHeader
from ..shared import AppliableWidget
from .shared import GameScreenMixin

DEMONS = sorted(
    DEMON_ID_MAP.values(),
    key=lambda demon: (demon.name.lower(), demon.id),
)
STAT_NAMES = [
    ("HP", "hp"),
    ("MP", "mp"),
    ("Strength", "strength"),
    ("Vitality", "vitality"),
    ("Magic", "magic"),
    ("Agility", "agility"),
    ("Luck", "luck"),
]
AFFINITY_NAMES = [
    ("Physical", "physical"),
    ("Fire", "fire"),
    ("Ice", "ice"),
    ("Electric", "electric"),
    ("Force", "force"),
    ("Light", "light"),
    ("Dark", "dark"),
    ("Almighty", "almighty"),
    ("Poison", "poison"),
    ("Confusion", "confusion"),
    ("Charm", "charm"),
    ("Sleep", "sleep"),
    ("Seal", "seal"),
    ("Mirage", "mirage"),
]
POTENTIAL_NAMES = [
    ("Physical", "physical"),
    ("Fire", "fire"),
    ("Ice", "ice"),
    ("Electric", "electric"),
    ("Force", "force"),
    ("Light", "light"),
    ("Dark", "dark"),
    ("Almighty", "almighty"),
    ("Ailment", "ailment"),
    ("Support", "support"),
    ("Recovery", "recovery"),
]
class DemonCreationScreen(QWidget, GameScreenMixin, AppliableWidget):
    selected: Demon | None = None
    created_slot: int | None = None
    _requested = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.demons = self.save.demons
        self.team = self.save.team
        self.stat_values: dict[str, QLabel] = {}

        self.outer = QVBoxLayout(self)
        self.outer.setContentsMargins(24, 24, 24, 24)
        self.outer.setSpacing(16)

        self.header = PageHeader(
            "Create demon",
            "Experimental: create in an empty storage slot, then save and "
            "verify in-game. Keep a backup.",
            self,
        )
        self.outer.addWidget(self.header)

        self.success_card = Card(self)
        success_layout = QHBoxLayout(self.success_card)
        success_layout.setContentsMargins(18, 14, 18, 14)
        success_layout.setSpacing(12)
        self.success_label = QLabel(self)
        self.success_label.setWordWrap(True)
        success_layout.addWidget(self.success_label, 1)
        self.edit_button = QPushButton("Edit demon", self.success_card)
        self.edit_button.clicked.connect(self.edit_created)
        success_layout.addWidget(self.edit_button)
        self.another_button = QPushButton("Create another", self.success_card)
        self.another_button.clicked.connect(self.reset_form)
        success_layout.addWidget(self.another_button)
        self.back_button = QPushButton("Back to demons", self.success_card)
        self.back_button.clicked.connect(self.stack_remove)
        success_layout.addWidget(self.back_button)
        self.success_card.hide()
        self.outer.addWidget(self.success_card)

        self.body = QHBoxLayout()
        self.body.setSpacing(16)
        self.outer.addLayout(self.body, 1)

        self.form_card = Card(self)
        form = QVBoxLayout(self.form_card)
        form.setContentsMargins(20, 18, 20, 18)
        form.setSpacing(10)

        species_label = QLabel("Species", self.form_card)
        species_label.setObjectName("SectionTitle")
        form.addWidget(species_label)
        self.search = QLineEdit(self.form_card)
        self.search.setPlaceholderText("Search by name…")
        self.search.textChanged.connect(lambda _: self.refresh_demon_list())
        form.addWidget(self.search)
        self.species_list = QListWidget(self.form_card)
        self.species_list.setMinimumHeight(260)
        self.species_list.currentItemChanged.connect(self.species_selected)
        form.addWidget(self.species_list, 1)

        slot_label = QLabel("Storage slot", self.form_card)
        slot_label.setObjectName("SectionTitle")
        form.addWidget(slot_label)
        self.slot_box = QComboBox(self.form_card)
        self.slot_box.currentIndexChanged.connect(
            lambda _: self.validate_form()
        )
        form.addWidget(self.slot_box)
        self.slot_info = QLabel("", self.form_card)
        self.slot_info.setObjectName("Muted")
        self.slot_info.setWordWrap(True)
        form.addWidget(self.slot_info)

        self.level_label = QLabel("Default level: —", self.form_card)
        self.level_label.setObjectName("Muted")
        form.addWidget(self.level_label)
        level_note = QLabel(
            "Created at the species' default level. Change level later in the "
            "demon editor, with the existing warning.",
            self.form_card,
        )
        level_note.setObjectName("Muted")
        level_note.setWordWrap(True)
        form.addWidget(level_note)

        party_note = QLabel(
            "The demon will be added to the first free party-order slot so "
            "it is visible in the demon selector.",
            self.form_card,
        )
        party_note.setObjectName("Muted")
        party_note.setWordWrap(True)
        form.addWidget(party_note)

        self.validation = QLabel("", self.form_card)
        self.validation.setWordWrap(True)
        self.validation.setObjectName("Muted")
        form.addWidget(self.validation)

        actions = QHBoxLayout()
        self.create_button = QPushButton("Create demon", self.form_card)
        self.create_button.setObjectName("PrimaryButton")
        self.create_button.setEnabled(False)
        self.create_button.clicked.connect(self.request_create)
        actions.addWidget(self.create_button)
        self.cancel_button = QPushButton("Cancel", self.form_card)
        self.cancel_button.clicked.connect(self.stack_remove)
        actions.addWidget(self.cancel_button)
        form.addLayout(actions)

        self.body.addWidget(self.form_card, 1)

        self.preview_card = Card(self)
        preview_outer = QVBoxLayout(self.preview_card)
        preview_outer.setContentsMargins(0, 0, 0, 0)
        self.preview_scroll = QScrollArea(self.preview_card)
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setFrameShape(QFrame.Shape.NoFrame)
        preview_inner = QWidget()
        self.preview_layout = QVBoxLayout(preview_inner)
        self.preview_layout.setContentsMargins(20, 18, 20, 18)
        self.preview_layout.setSpacing(10)
        self.preview_scroll.setWidget(preview_inner)
        preview_outer.addWidget(self.preview_scroll)
        self.body.addWidget(self.preview_card, 1)

        preview_title = QLabel("Preview", preview_inner)
        preview_title.setObjectName("SectionTitle")
        self.preview_layout.addWidget(preview_title)
        self.preview_name = QLabel("Select a demon", preview_inner)
        self.preview_name.setObjectName("PageTitle")
        self.preview_layout.addWidget(self.preview_name)
        self.preview_meta = QLabel("", preview_inner)
        self.preview_meta.setObjectName("Muted")
        self.preview_layout.addWidget(self.preview_meta)

        stats_title = QLabel("Stats", preview_inner)
        stats_title.setObjectName("SectionTitle")
        self.preview_layout.addWidget(stats_title)
        self.stats_grid = QGridLayout()
        self.preview_layout.addLayout(self.stats_grid)
        for index, (name, key) in enumerate(STAT_NAMES):
            self.stats_grid.addWidget(QLabel(name), index, 0)
            value = QLabel("—")
            self.stats_grid.addWidget(value, index, 1)
            self.stat_values[key] = value

        self.preview_skills = QLabel("", preview_inner)
        self.preview_skills.setWordWrap(True)
        self.preview_layout.addWidget(self.preview_skills)
        self.preview_innate = QLabel("", preview_inner)
        self.preview_innate.setWordWrap(True)
        self.preview_layout.addWidget(self.preview_innate)
        self.preview_affinities = QLabel("", preview_inner)
        self.preview_affinities.setWordWrap(True)
        self.preview_layout.addWidget(self.preview_affinities)
        self.preview_potentials = QLabel("", preview_inner)
        self.preview_potentials.setWordWrap(True)
        self.preview_layout.addWidget(self.preview_potentials)
        self.preview_layout.addStretch()

        self.refresh_slots()
        self.refresh_demon_list()
        self.update_preview()
        self.validate_form()

    def refresh_slots(self):
        max_stock = min(self.team.max_stock, self.demons.STORAGE_SIZE)
        self.slot_info.setText(
            f"Usable storage: {max_stock} of {self.demons.STORAGE_SIZE} "
            "slots. Divine Garrison increases this limit."
        )
        self.slot_box.blockSignals(True)
        self.slot_box.clear()
        free_slots = self.demons.free_storage_slots(limit=max_stock)
        for slot in free_slots:
            self.slot_box.addItem(f"Storage slot {slot}", slot)
        if free_slots:
            self.slot_box.setCurrentIndex(0)
            self.slot_box.setEnabled(True)
        else:
            self.slot_box.addItem("No free storage slots")
            self.slot_box.setEnabled(False)
        self.slot_box.blockSignals(False)
        self.validate_form()

    def refresh_demon_list(self):
        query = self.search.text().strip().lower()
        selected_id = self.selected.id if self.selected else None
        self.species_list.blockSignals(True)
        self.species_list.clear()
        selected_item: QListWidgetItem | None = None
        for demon in DEMONS:
            if query and query not in demon.name.lower():
                continue
            item = QListWidgetItem(
                f"{demon.name}  ·  Lv {demon.level}"
            )
            item.setData(Qt.ItemDataRole.UserRole, demon.id)
            self.species_list.addItem(item)
            if demon.id == selected_id:
                selected_item = item
        if selected_item is not None:
            self.species_list.setCurrentItem(selected_item)
        self.species_list.blockSignals(False)
        if selected_item is None and self.selected is not None:
            self.selected = None
            self.update_preview()
        self.validate_form()

    def species_selected(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None = None,
    ):
        if current is None:
            self.selected = None
        else:
            demon_id = current.data(Qt.ItemDataRole.UserRole)
            self.selected = DEMON_ID_MAP.get(demon_id)
        self.update_preview()
        self.validate_form()

    def update_preview(self):
        demon = self.selected
        if demon is None:
            self.preview_name.setText("Select a demon")
            self.preview_meta.setText("")
            for label in self.stat_values.values():
                label.setText("—")
            self.preview_skills.setText("")
            self.preview_innate.setText("")
            self.preview_affinities.setText("")
            self.preview_potentials.setText("")
            self.level_label.setText("Default level: —")
            return

        self.preview_name.setText(demon.name)
        self.preview_meta.setText(
            f"ID {demon.id}  ·  Default level {demon.level}"
        )
        self.level_label.setText(f"Default level: {demon.level}")
        for _, key in STAT_NAMES:
            self.stat_values[key].setText(
                str(getattr(demon.stats, key))
            )
        skills = ", ".join(skill.name for skill in demon.skills) or "None"
        self.preview_skills.setText(f"Skills: {skills}")
        self.preview_innate.setText(
            f"Innate: {demon.innate_skill.name}"
        )
        affinities = "  ·  ".join(
            f"{name} {getattr(demon.affinities, key).name}"
            for name, key in AFFINITY_NAMES
        )
        self.preview_affinities.setText(f"Affinities: {affinities}")
        potentials = "  ·  ".join(
            f"{name} {getattr(demon.potentials, key):+d}"
            for name, key in POTENTIAL_NAMES
        )
        self.preview_potentials.setText(f"Potentials: {potentials}")

    def validate_form(self):
        if self.created_slot is not None:
            self.create_button.setEnabled(False)
            return
        if self.selected is None:
            self.validation.setText("Choose a demon to continue.")
            self.create_button.setEnabled(False)
            return
        if self.slot_box.currentData() is None:
            self.validation.setText("No free storage slot is available.")
            self.create_button.setEnabled(False)
            return
        if self.team.free_order_slots() == 0:
            self.validation.setText(
                "The party-order list is full. Free an entry first."
            )
            self.create_button.setEnabled(False)
            return
        self.validation.setText("")
        self.create_button.setEnabled(True)

    def request_create(self):
        if not self.create_button.isEnabled():
            return
        self._requested = True
        self.main_window.on_apply()

    def has_unapplied_changes(self) -> bool:
        return self._requested

    def discard_unapplied_changes(self):
        self._requested = False

    def on_apply_changes(self):
        if not self._requested or self.selected is None:
            self._requested = False
            return
        slot = self.slot_box.currentData()
        if slot is None:
            self._requested = False
            return
        try:
            demon = self.demons.create_from_initial(
                self.selected,
                int(slot),
                max_stock=self.team.max_stock,
            )
        except ValueError as exc:
            self.validation.setText(str(exc))
            self._requested = False
            return
        self.team.add_to_order(demon.slot)
        self.created_slot = demon.slot
        self._requested = False
        self.show_success(demon)

    def show_success(self, demon):
        self.success_label.setText(
            f"Created {demon.name} in storage slot {demon.slot}. "
            "Click Save to Disk to write it."
        )
        self.success_card.show()
        self.edit_button.setEnabled(True)
        self.refresh_slots()
        self.validate_form()

    def reset_form(self):
        self.created_slot = None
        self._requested = False
        self.selected = None
        self.success_card.hide()
        self.search.clear()
        self.species_list.setCurrentItem(None)
        self.refresh_slots()
        self.refresh_demon_list()
        self.update_preview()
        self.validate_form()

    def edit_created(self):
        if self.created_slot is None:
            return
        from .demons import DemonEditorScreen

        demon = self.demons.in_slot(self.created_slot)
        self.stack_add(DemonEditorScreen(demon, self))

    def stack_refresh(self):
        self.refresh_slots()
        self.refresh_demon_list()
        self.update_preview()
        self.validate_form()
