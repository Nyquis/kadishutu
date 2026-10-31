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

    screen.advanced.setChecked(True)
    assert not row.skill_box.int_box.isHidden()

    row.learn_type_box.setCurrentIndex(
        row.learn_type_box.findData(LearnSkillType.Default.value)
    )
    screen.on_apply_changes()

    assert demon.skills.slot(0).learn_type is LearnSkillType.Default


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
