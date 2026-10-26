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

    categories = {
        button.property("category")
        for button in screen.findChildren(QPushButton)
        if button.property("category")
    }
    assert {
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
    } <= categories

    assert screen.header.title.text() == "Save Overview"
    assert screen.scroll.widgetResizable()
    assert screen.macca.value() == 123
    assert screen.glory.value() == 456


def test_file_selector_has_header_and_primary_action(main_window):
    from kadishutu.gui.mainwindow import FileSelectorMenu

    menu = FileSelectorMenu()
    assert menu.header.title.text() == "Open a save"
    assert menu.file_open.objectName() == "PrimaryButton"
    assert not menu.file_open.isEnabled()


def test_main_window_has_toolbar_and_status_bar(main_window):
    assert main_window.toolbar.objectName() == "MainToolbar"
    assert main_window.status_label.text() == "No save open"
    actions = main_window.toolbar.actions()
    assert main_window.save_button in actions
    assert main_window.apply_button in actions
    assert main_window.back_button in actions


def test_main_window_has_keyboard_shortcuts(main_window):
    assert main_window.save_button.shortcut().toString() == "Ctrl+S"
    assert main_window.save_as_button.shortcut().toString() == "Ctrl+Shift+S"
    assert main_window.close_button.shortcut().toString() == "Ctrl+W"
    assert main_window.undo_button.shortcut().toString() == "Ctrl+Z"


def test_main_window_has_sensible_minimum_size(main_window):
    assert main_window.minimumWidth() >= 900
    assert main_window.minimumHeight() >= 620


def test_main_window_status_shows_open_save(main_window):
    from kadishutu.gui.sys_save import SysSaveEditorScreen

    editor = SysSaveEditorScreen(
        Path("sys.sav"),
        DecryptedSave(bytearray(0x12E0)),
        main_window,
    )
    main_window.stack_add(editor)

    assert "sys.sav" in main_window.status_label.text()
    assert "sys.sav" in main_window.windowTitle()


def test_theme_menu_updates_controller(qapp: QApplication, tmp_path: Path):
    from PySide6.QtCore import QSettings

    from kadishutu.gui import mainwindow
    from kadishutu.gui.theme import (
        ThemeController,
        ThemeMode,
        apply_theme,
    )

    settings = QSettings(
        str(tmp_path / "settings.ini"),
        QSettings.Format.IniFormat,
    )
    controller = ThemeController(qapp, settings=settings)
    window = mainwindow.MainWindow(theme_controller=controller)
    try:
        assert window.theme_actions[ThemeMode.SYSTEM].isChecked()
        window.theme_actions[ThemeMode.DARK].trigger()

        assert controller.mode is ThemeMode.DARK
        assert controller.resolved_mode is ThemeMode.DARK
        assert window.theme_actions[ThemeMode.DARK].isChecked()
    finally:
        window.close()
        window.deleteLater()
        controller.deleteLater()
        qapp.processEvents()
        apply_theme(qapp, ThemeMode.SYSTEM)


def test_theme_mode_resolution():
    from PySide6.QtCore import Qt

    from kadishutu.gui.theme import ThemeMode, resolve_theme_mode

    assert (
        resolve_theme_mode(ThemeMode.SYSTEM, Qt.ColorScheme.Dark)
        is ThemeMode.DARK
    )
    assert (
        resolve_theme_mode(ThemeMode.SYSTEM, Qt.ColorScheme.Light)
        is ThemeMode.LIGHT
    )
    assert (
        resolve_theme_mode(ThemeMode.LIGHT, Qt.ColorScheme.Dark)
        is ThemeMode.LIGHT
    )


def test_theme_settings_round_trip(tmp_path: Path):
    from PySide6.QtCore import QSettings

    from kadishutu.gui.theme import (
        ThemeMode,
        load_theme_mode,
        save_theme_mode,
    )

    settings = QSettings(
        str(tmp_path / "settings.ini"),
        QSettings.Format.IniFormat,
    )
    save_theme_mode(ThemeMode.DARK, settings)
    settings.sync()

    assert load_theme_mode(settings) is ThemeMode.DARK


def test_apply_theme_updates_palette_and_stylesheet(qapp: QApplication):
    from PySide6.QtGui import QPalette

    from kadishutu.gui.theme import (
        ThemeMode,
        apply_theme,
        build_palette,
        build_stylesheet,
    )

    palette = build_palette(ThemeMode.DARK)
    assert palette.color(QPalette.ColorRole.Window).name() == "#0f1115"
    assert "QPushButton#CategoryCard" in build_stylesheet(ThemeMode.LIGHT)

    try:
        resolved = apply_theme(qapp, ThemeMode.DARK)
        assert resolved is ThemeMode.DARK
        assert "#8b5cf6" in qapp.styleSheet()
    finally:
        apply_theme(qapp, ThemeMode.SYSTEM)


def test_theme_controller_persists_mode(qapp: QApplication, tmp_path: Path):
    from PySide6.QtCore import QSettings

    from kadishutu.gui.theme import (
        ThemeController,
        ThemeMode,
        apply_theme,
        load_theme_mode,
    )

    settings = QSettings(
        str(tmp_path / "settings.ini"),
        QSettings.Format.IniFormat,
    )
    controller = ThemeController(qapp, settings=settings)
    try:
        controller.set_mode(ThemeMode.LIGHT)
        settings.sync()

        assert controller.mode is ThemeMode.LIGHT
        assert controller.resolved_mode is ThemeMode.LIGHT
        assert load_theme_mode(settings) is ThemeMode.LIGHT
    finally:
        controller.deleteLater()
        qapp.processEvents()
        apply_theme(qapp, ThemeMode.SYSTEM)
