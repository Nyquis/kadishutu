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
