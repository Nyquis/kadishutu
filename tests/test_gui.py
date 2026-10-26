import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from kadishutu.core.shared.file_handling import DecryptedSave


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def main_window(qapp: QApplication):
    from kadishutu.gui import mainwindow

    window = mainwindow.MainWindow()
    mainwindow.MAIN_WINDOW = window
    yield window
    window.close()
    window.deleteLater()
    qapp.processEvents()


def test_main_window_initial_actions_are_disabled(main_window):
    assert not main_window.save_button.isEnabled()
    assert not main_window.save_as_button.isEnabled()
    assert not main_window.close_button.isEnabled()
    assert not main_window.undo_button.isEnabled()
    assert not main_window.apply_button.isEnabled()
    assert not main_window.back_button.isEnabled()


def test_sys_save_is_read_only(main_window):
    from kadishutu.gui.sys_save import SysSaveEditorScreen

    editor = SysSaveEditorScreen(
        Path("sys.sav"),
        DecryptedSave(bytearray(0x12E0)),
        main_window,
    )
    main_window.stack_add(editor)

    assert not main_window.save_button.isEnabled()
    assert not main_window.save_as_button.isEnabled()
    assert main_window.close_button.isEnabled()


def test_file_selector_rejects_invalid_hash(
    main_window, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from kadishutu.gui.mainwindow import FileSelectorMenu

    path = tmp_path / "save.sav"
    save = DecryptedSave(bytearray(0x100))
    save.data[0x40:0x44] = b"GVAS"
    save.hash_update()
    save.data[0x50] ^= 0xFF
    save.save(path)

    def reject(*args, **kwargs):
        return QMessageBox.StandardButton.No

    monkeypatch.setattr(QMessageBox, "warning", reject)
    menu = FileSelectorMenu()
    menu.file_path.path = path

    assert menu.raw is None
    assert not menu.file_open.isEnabled()


def test_save_overview_builds_category_buttons(
    main_window, monkeypatch: pytest.MonkeyPatch
):
    from kadishutu.gui.game_save import game_save

    class DummyGameSaveEditor:
        macca = 123
        glory = 456

        def __init__(self, raw_save: DecryptedSave):
            self.raw_save = raw_save

    monkeypatch.setattr(game_save, "GameSaveEditor", DummyGameSaveEditor)
    screen = game_save.GameSaveEditorScreen(
        Path("save.sav"),
        DecryptedSave(bytearray(0x100)),
        main_window,
    )
    screen.stack_refresh()

    button_texts = [
        button.text()
        for button in screen.findChildren(QPushButton)
    ]
    for name in [
        "DLC",
        "Player",
        "Demons",
        "Miracles",
        "Items",
        "Essences",
        "Layline Crossing",
        "Alignment",
        "Settings",
        "Meta",
        "Plugins",
    ]:
        assert any(name in text for text in button_texts)

    assert screen.macca.value() == 123
    assert screen.glory.value() == 456
