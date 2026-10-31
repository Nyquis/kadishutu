import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QWidget,
)

from kadishutu.core.game_save import GameSaveEditor
from kadishutu.core.shared.file_handling import DecryptedSave

GAME_SAVE_SIZE = 0x6DC90
NOT_IMPLEMENTED = pytest.mark.xfail(
    strict=True,
    reason="apply/save workflow not implemented yet",
)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def window(qapp: QApplication):
    from kadishutu.gui import mainwindow

    win = mainwindow.MainWindow()
    mainwindow.MAIN_WINDOW = win
    yield win
    win.hide()
    win.deleteLater()
    qapp.processEvents()


@pytest.fixture
def editor(window, tmp_path: Path):
    from kadishutu.gui.game_save.game_save import GameSaveEditorScreen

    path = tmp_path / "save.sav"
    raw = DecryptedSave(bytearray(GAME_SAVE_SIZE))
    raw.data[0x40:0x44] = b"GVAS"
    raw.save_finished(path, backup=False)
    screen = GameSaveEditorScreen(path, DecryptedSave.auto_open(path), window)
    window.stack_add(screen)
    return screen


def test_editing_a_value_leaves_it_unapplied(window, editor):
    editor.macca.setValue(555)

    assert window.has_unapplied_edits()
    assert editor.save.macca == 0


def test_item_bulk_buttons_apply_through_the_workflow(window, editor):
    from kadishutu.data.items import CONSUMABLES_RANGE, items_from
    from kadishutu.gui.game_save.items import ItemEditorScreen

    screen = ItemEditorScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()
    tab = screen.tabs[0]
    meta = items_from(CONSUMABLES_RANGE)[0]

    tab.max_button.click()
    assert window.has_unapplied_edits()

    screen.on_apply_changes()
    assert editor.save.items.from_meta(meta).amount == meta.limit

    tab.clear_button.click()
    screen.on_apply_changes()
    assert editor.save.items.from_meta(meta).amount == 0


def test_item_search_filters_and_limits_bulk_actions(window, editor):
    from kadishutu.data.items import CONSUMABLES_RANGE, items_from
    from kadishutu.gui.game_save.items import ItemEditorScreen

    screen = ItemEditorScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()
    tab = screen.tabs[0]
    metas = items_from(CONSUMABLES_RANGE)
    target_index = next(
        index
        for index, (item, _, _) in enumerate(tab.items)
        if item.meta.id == 9
    )
    other_index = 0 if target_index != 0 else 1
    other_meta = metas[other_index]

    tab.search.setText("Amrita Soda")

    assert tab.visible_indices == {target_index}
    assert tab.visible_count == 1
    assert tab.items[other_index][1].isHidden()

    tab.max_button.click()
    screen.on_apply_changes()

    assert editor.save.items.from_id(9).amount == 50
    assert editor.save.items.from_meta(other_meta).amount == 0

    tab.search.setText("")
    assert len(tab.visible_indices) == len(tab.items)

    tab.clear_button.click()
    screen.on_apply_changes()

    assert editor.save.items.from_id(9).amount == 0


def test_item_screen_has_column_headers(window, editor):
    from kadishutu.gui.game_save.items import ItemEditorScreen

    screen = ItemEditorScreen(window)
    window.stack_add(screen)
    tab = screen.tabs[0]

    assert [header.text() for header in tab.headers] == [
        "Icon",
        "Item",
        "Max",
        "Details",
        "Amount",
    ]
    assert tab.headers[2].toolTip()
    assert tab.headers[3].toolTip()
    assert tab.headers[4].toolTip()


def test_item_search_matches_metadata_and_flags(window, editor):
    from kadishutu.gui.game_save.items import ItemEditorScreen

    screen = ItemEditorScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()
    tab = screen.tabs[0]

    tab.search.setText("battle")
    battle_ids = {
        tab.items[index][0].meta.id for index in tab.visible_indices
    }
    assert 9 in battle_ids
    assert all(
        "battle" in tab.items[index][0].meta.search_text
        for index in tab.visible_indices
    )

    tab.search.setText("infinite")
    infinite_ids = {
        tab.items[index][0].meta.id for index in tab.visible_indices
    }
    assert 70 in infinite_ids
    assert all(
        tab.items[index][0].meta.infinite
        for index in tab.visible_indices
    )

    tab.search.setText("unique")
    assert all(
        tab.items[index][0].meta.limit == 1
        for index in tab.visible_indices
    )


def test_item_editor_warns_about_existing_over_limit_values(window, editor):
    from kadishutu.data.items import ITEM_ID_MAP
    from kadishutu.gui.game_save.items import ItemEditorScreen

    editor.save.items.set_amount(ITEM_ID_MAP[9], 255, clamp=False)
    screen = ItemEditorScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()
    tab = screen.tabs[0]

    index = next(
        index
        for index, (item, _, _) in enumerate(tab.items)
        if item.meta.id == 9
    )
    amount_box = tab.items[index][2]

    assert amount_box.value() == 255
    assert not tab.validation_label.isHidden()

    amount_box.setValue(50)
    assert tab.validation_label.isHidden()


def test_essence_screen_keeps_have_and_used_flags_separate(window, editor):
    from kadishutu.core.game_save.essences import EssenceMetadata
    from kadishutu.gui.game_save.essences import EssenceEditorScreen

    essence = editor.save.essences.from_id(351)
    essence.amount = 1
    essence.metadata = (
        EssenceMetadata.New
        | EssenceMetadata.Owned
        | EssenceMetadata.Used
    )

    screen = EssenceEditorScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()
    index = next(
        index
        for index, row in enumerate(screen.rows)
        if row.essence.meta.id == 351
    )
    row = screen.rows[index]

    assert row.have.isChecked()
    assert row.used.isChecked()
    assert "Used before" in row.status.text()

    screen.search.setText("351")
    assert screen.visible_indices == {index}

    row.used.setChecked(False)
    screen.on_apply_changes()

    assert essence.amount == 1
    assert essence.metadata == EssenceMetadata.New | EssenceMetadata.Owned

    screen.clear_button.click()
    screen.on_apply_changes()
    assert essence.amount == 0

    screen.used_button.click()
    screen.on_apply_changes()
    assert essence.used is True


def test_alignment_screen_filters_and_edits_choices(window, editor):
    from kadishutu.gui.game_save.alignment import AlignmentEditorScreen

    screen = AlignmentEditorScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()

    assert [header.text() for header in screen.headers[:5]] == [
        "Selection",
        "Status",
        "Place",
        "Quest",
        "Type",
    ]

    screen.search.setText("Heart of Garnet")
    expected = {
        index
        for index, row in enumerate(screen.rows)
        if row.choice.side_quest == "Heart of Garnet"
    }
    assert screen.visible_indices == expected
    assert len(expected) == 1

    row = next(
        row for row in screen.rows
        if row.choice.side_quest == "Heart of Garnet"
    )
    row.combo.setCurrentIndex(row.combo.findData(4))
    screen.on_apply_changes()

    alignment = editor.save.alignment.at_offset(0x69CFA)
    assert alignment.get_flag(4) is True
    assert alignment.get_flag(5) is False
    assert "Law 1" in screen.summary_label.text()

    row.combo.setCurrentIndex(row.combo.findData(5))
    screen.on_apply_changes()

    assert alignment.get_flag(4) is False
    assert alignment.get_flag(5) is True

    screen.advanced.setChecked(True)
    assert not row.offset_label.isHidden()
    assert not row.bits_label.isHidden()


def test_alignment_screen_warns_when_both_sides_are_set(window, editor):
    from kadishutu.gui.game_save.alignment import AlignmentEditorScreen

    alignment = editor.save.alignment.at_offset(0x69CFA)
    alignment.set_flag(4, True)
    alignment.set_flag(5, True)

    screen = AlignmentEditorScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()

    row = next(
        row for row in screen.rows
        if row.choice.side_quest == "Heart of Garnet"
    )

    assert row.invalid is True
    assert "Both selected" in row.status.text()
    assert "Invalid 1" in screen.summary_label.text()

    row.combo.setCurrentIndex(row.combo.findData(4))
    screen.on_apply_changes()

    assert alignment.get_flag(4) is True
    assert alignment.get_flag(5) is False


def test_meta_screen_edits_cycles_endings_and_satan(window, editor):
    from kadishutu.core.game_save.game import Endings
    from kadishutu.gui.game_save.cross_cycle import CrossCycleEditorScreen

    screen = CrossCycleEditorScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()

    assert screen.cycles_box.maximum() == 99
    assert screen.endings_summary.text() == "0 / 6 endings marked"
    assert (
        screen.canon_headers["Creation"].text()
        == "Canon of Creation — 0 / 4"
    )
    assert (
        screen.canon_headers["Vengeance"].text()
        == "Canon of Vengeance — 0 / 2"
    )

    screen.cycles_box.setValue(5)
    screen.ending_map[Endings.CreationLaw].setChecked(True)
    screen.satan_box.setChecked(True)
    screen.on_apply_changes()

    assert editor.save.cycles == 5
    assert editor.save.cycles_copy == 5
    assert editor.save.endings & Endings.CreationLaw
    assert editor.save.endings_copy == editor.save.endings
    assert editor.save.miracle_unlocks.extras.satan_beaten is True
    assert "1 / 6" in screen.endings_summary.text()
    assert (
        screen.canon_headers["Creation"].text()
        == "Canon of Creation — 1 / 4"
    )


def test_meta_screen_warns_and_syncs_header_copies(window, editor):
    from kadishutu.gui.game_save.cross_cycle import CrossCycleEditorScreen

    editor.save.cycles = 4
    editor.save.cycles_copy = 9

    screen = CrossCycleEditorScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()

    assert not screen.copy_warning.isHidden()

    screen.on_apply_changes()

    assert editor.save.cycles_copy == 4
    assert screen.copy_warning.isHidden()


def test_meta_screen_bulk_endings(window, editor):
    from kadishutu.gui.game_save.cross_cycle import CrossCycleEditorScreen

    screen = CrossCycleEditorScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()

    screen.mark_all_button.click()
    assert all(box.isChecked() for box in screen.ending_map.values())
    assert "6 / 6" in screen.endings_summary.text()

    screen.clear_all_button.click()
    assert not any(box.isChecked() for box in screen.ending_map.values())
    assert "0 / 6" in screen.endings_summary.text()


def test_skill_screen_labels_learn_type_and_hides_ids(window, editor):
    from kadishutu.data.skills import LearnSkillType
    from kadishutu.gui.game_save.skills import SkillEditorScreen

    demon = editor.save.demons.in_slot(0)
    demon.skills.slot(0).id = 491
    demon.skills.slot(0).learn_type = LearnSkillType.Library
    demon.skills.slot(1).id = 5
    demon.skills.slot(1).learn_type = LearnSkillType.Default
    demon.innate_skill.id = 669

    screen = SkillEditorScreen(demon.skills, demon.innate_skill)
    window.stack_add(screen)
    screen.stack_refresh()

    assert [header.text() for header in screen.headers] == [
        "Slot",
        "Icon",
        "Skill",
        "MP cost",
        "Learn type",
    ]
    assert screen.rows[0].mp_cost.isHidden()
    assert screen.rows[3].learn_type_box.isHidden()
    assert screen.rows[1].skill_box.int_box.isHidden()

    row = screen.rows[1]
    assert row.learn_type_box.currentData() == LearnSkillType.Library.value
    assert "Magic attack" in screen.rows[2].skill_box.str_box.toolTip()

    screen.advanced.setChecked(True)
    assert not row.skill_box.int_box.isHidden()

    row.learn_type_box.setCurrentIndex(
        row.learn_type_box.findData(LearnSkillType.Default.value)
    )
    screen.on_apply_changes()

    assert demon.skills.slot(0).learn_type is LearnSkillType.Default


def test_stats_screen_recalculates_and_heals(window, editor):
    from kadishutu.gui.game_save.stats import StatEditorScreen

    demon = editor.save.demons.in_slot(0)
    demon.stats.base.hp = 100
    demon.stats.base.mp = 50
    demon.stats.base.strength = 10
    demon.stats.changes.hp = 20
    demon.stats.changes.mp = 5
    demon.stats.changes.strength = 3
    demon.stats.current.hp = 120
    demon.stats.current.mp = 55
    demon.stats.current.strength = 13
    demon.healable.hp = 50
    demon.healable.mp = 20

    screen = StatEditorScreen(demon.stats, demon.healable)
    window.stack_add(screen)
    screen.stack_refresh()

    assert screen.headers[1].text() == "Natural"
    assert screen.headers[2].text() == "Bonuses"
    assert screen.headers[3].text() == "Current"
    assert screen.headers[4].text() == "Healable HP/MP"
    assert screen.widgets["current"]["strength"].isReadOnly()

    screen.widgets["current"]["strength"].setValue(999)
    screen.recalculate_button.click()
    assert screen.widgets["current"]["strength"].value() == 13

    screen.heal_button.click()
    assert screen.widgets["healable"]["hp"].value() == 120

    screen.on_apply_changes()

    assert demon.stats.current.strength == 13
    assert demon.healable.hp == 120


def test_affinity_screen_shows_unmapped_values(window, editor):
    from kadishutu.data.affinity import Affinity
    from kadishutu.gui.game_save.affinities import AffinityEditorScreen

    demon = editor.save.demons.in_slot(0)
    demon.affinities.current_elemental.fire = Affinity.Unknown300

    screen = AffinityEditorScreen(demon.affinities)
    window.stack_add(screen)
    screen.stack_refresh()

    box = screen.elem_aff_map["fire"]
    assert box.currentText() == "Unmapped (300)"
    assert screen.group_titles == [
        "Elemental affinities",
        "Ailment affinities",
    ]

    box.setCurrentText("Resist")
    screen.on_apply_changes()

    assert demon.affinities.current_elemental.fire is Affinity.Resist


def test_potentials_screen_uses_signed_values(window, editor):
    from kadishutu.core.game_save.potentials import PotentialType
    from kadishutu.gui.game_save.potentials import PotentialEditorScreen

    demon = editor.save.demons.in_slot(0)
    demon.potentials.physical = 3

    screen = PotentialEditorScreen(demon.potentials)
    window.stack_add(screen)
    screen.stack_refresh()

    box = screen.potential_map[PotentialType.Physical]
    assert box.textFromValue(3) == "+3"
    assert screen.group_titles == [
        "Elemental potentials",
        "Other potentials",
    ]

    box.setValue(-2)
    screen.on_apply_changes()

    assert demon.potentials.read(PotentialType.Physical) == -2


def test_game_save_categories_use_difficulty_label(editor):
    from kadishutu.gui.components import CategoryCard

    titles = {
        card.title_label.text()
        for card in editor.findChildren(CategoryCard)
    }

    assert "Difficulty" in titles
    assert "Settings" not in titles


def test_sys_save_screen_edits_settings(window, tmp_path):
    from kadishutu.core.shared.file_handling import DecryptedSave
    from kadishutu.core.sys_save import CameraMode
    from kadishutu.gui.sys_save.sys_save import SysSaveEditorScreen

    raw = DecryptedSave(bytearray(0x12E0))
    raw.data[0x40:0x44] = b"GVAS"
    path = tmp_path / "SysSave.sav"

    screen = SysSaveEditorScreen(path, raw, window)
    window.stack_add(screen)

    assert screen.can_save

    volume = next(
        slider
        for slider, _, field in screen.volume_controls
        if field == "voice_volume"
    )
    volume.setValue(50)

    camera = next(
        combo
        for combo, field, _ in screen.enum_controls
        if field == "camera_horizontal"
    )
    camera.setCurrentIndex(
        camera.findData(CameraMode.Reverse.value)
    )

    subtitles = next(
        box
        for box, field in screen.bool_controls
        if field == "subtitles"
    )
    subtitles.setChecked(False)

    screen.on_apply_changes()

    assert 0.49 < screen.save.voice_volume < 0.51
    assert screen.save.camera_horizontal is CameraMode.Reverse
    assert raw.data[0x1221] == 1

    screen.raw_save.save_finished(path, backup=False)
    reopened = DecryptedSave.auto_open(path)
    assert reopened.data[0x1221] == 1
    assert reopened.data[0x5F6] == CameraMode.Reverse.value


def test_layline_screen_groups_filters_and_teleports(window, editor):
    from kadishutu.gui.game_save.teleport import TeleporterScreen

    screen = TeleporterScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()

    assert screen.tree.topLevelItemCount() > 0
    assert "Last used layline" in screen.last_label.text()

    screen.search.setText("Tamachi")
    tamachi = next(
        item
        for item in screen.item_by_id.values()
        if item.text(0) == "Tamachi"
    )
    assert not tamachi.isHidden()

    screen.tree.setCurrentItem(tamachi)
    assert screen.selected_layline is not None
    assert screen.selected_layline.name == "Da'at: Minato - Tamachi"
    assert screen.button.isEnabled()
    assert screen.unlock_layline.isEnabled()

    screen.on_apply_changes()

    position = editor.save.position
    assert position.last_layline is not None
    assert position.last_layline.name == "Da'at: Minato - Tamachi"
    assert position.is_layline_unlocked(position.last_layline) is True


def test_layline_screen_warns_about_invalid_last_layline(window, editor):
    from kadishutu.gui.game_save.teleport import TeleporterScreen

    editor.save.position.last_layline_fount = 0xFF

    screen = TeleporterScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()

    assert not screen.warning_label.isHidden()
    assert "not recognized" in screen.warning_label.text()


def test_mirroring_the_save_is_not_an_edit(window, editor):
    from kadishutu.gui.shared import refresh_screen

    editor.save.macca = 999

    refresh_screen(editor)

    assert not window.has_unapplied_edits()


def test_toggling_a_dlc_flag_counts_as_unapplied(window, editor):
    from kadishutu.gui.game_save.dlc import DlcEditorScreen

    screen = DlcEditorScreen(window)
    window.stack_add(screen)
    box = next(iter(screen.widgets.values()))

    box.setChecked(not box.isChecked())

    assert window.has_unapplied_edits()


def test_apply_changes_copies_edits_into_the_save(window, editor):
    editor.macca.setValue(555)

    window.on_apply()

    assert editor.save.macca == 555
    assert not window.has_unapplied_edits()
    assert editor.modified


def test_save_writes_only_applied_changes(window, editor):
    editor.macca.setValue(555)
    window.on_apply()

    window.on_save()

    reopened = GameSaveEditor(DecryptedSave.auto_open(editor.path))
    assert reopened.macca == 555
    assert not editor.modified


def test_save_refuses_while_edits_are_unapplied(
    window, editor, monkeypatch: pytest.MonkeyPatch
):
    shown: list[object] = []
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: shown.append(args),
    )
    before = editor.path.read_bytes()
    editor.macca.setValue(555)

    window.on_save()

    assert editor.path.read_bytes() == before
    assert shown
    assert editor.save.macca == 0


def test_failed_save_keeps_applied_changes_marked_unsaved(
    window, editor, monkeypatch: pytest.MonkeyPatch
):
    def fail_save(self, path, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(DecryptedSave, "save_finished", fail_save)
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *args, **kwargs: None
    )
    editor.macca.setValue(555)
    window.on_apply()

    window.on_save()

    assert editor.modified


def test_closing_with_applied_unsaved_changes_asks_first(
    window, editor, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )
    editor.macca.setValue(555)
    window.on_apply()

    assert window.confirm_leaving(include_applied=True) is False


def test_closing_with_unapplied_edits_asks_first(
    window, editor, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )
    editor.macca.setValue(555)

    assert window.confirm_leaving(include_applied=True) is False


def test_opening_another_screen_with_unapplied_edits_asks_first(
    window, editor, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )
    editor.macca.setValue(555)
    count = len(window.inner.widget_stack)

    window.stack_add(QWidget())

    assert len(window.inner.widget_stack) == count


def test_back_with_unapplied_edits_asks_first(
    window, editor, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )
    window.stack_add(QWidget())
    editor.macca.setValue(555)
    count = len(window.inner.widget_stack)

    window.on_back()

    assert len(window.inner.widget_stack) == count


def test_revert_discards_unapplied_edits(window, editor):
    editor.macca.setValue(555)

    window.on_undo()

    assert editor.macca.value() == 0
    assert not window.has_unapplied_edits()


def test_status_text_follows_the_apply_then_save_sequence(window, editor):
    editor.macca.setValue(555)
    assert "Apply Changes" in window.status_label.text()

    window.on_apply()
    assert "Save to Disk" in window.status_label.text()

    window.on_save()
    assert "saved" in window.status_label.text().lower()


def test_toolbar_labels_name_the_two_steps(window):
    assert window.apply_button.text() == "Apply Changes"
    assert window.save_button.text() == "Save to Disk"


def test_actions_explain_the_two_steps(window):
    assert "does not write" in window.apply_button.toolTip().lower()
    assert "backup" in window.save_button.toolTip().lower()


def test_save_as_refuses_while_edits_are_unapplied(
    window, editor, monkeypatch: pytest.MonkeyPatch
):
    shown: list[object] = []
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: shown.append(args),
    )

    def unexpected_dialog(*args, **kwargs):
        raise AssertionError("file dialog should not open")

    monkeypatch.setattr(QFileDialog, "getSaveFileName", unexpected_dialog)
    editor.macca.setValue(555)

    window.on_save_as()

    assert shown


def test_cancelling_close_keeps_the_editor_open(
    window, editor, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )
    editor.macca.setValue(555)

    window.on_file_close()

    assert window.inner.top_widget is editor


def test_confirming_close_returns_to_the_file_picker(
    window, editor, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    editor.macca.setValue(555)

    window.on_file_close()

    assert window.inner.top_widget is window.file_selector
    assert not window.has_unapplied_edits()


def test_confirming_discard_clears_unapplied_edits(
    window, editor, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    editor.macca.setValue(555)

    assert window.confirm_leaving(include_applied=True)
    assert not window.has_unapplied_edits()
    assert editor.macca.value() == 0


def test_quit_is_cancelled_on_request(
    window, editor, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )
    editor.macca.setValue(555)
    window.on_apply()
    event = QCloseEvent()

    window.closeEvent(event)

    assert not event.isAccepted()
