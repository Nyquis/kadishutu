import sys
from argparse import Namespace
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QCloseEvent,
    QGuiApplication,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from kadishutu.core.game_save import GameSaveEditor

# NOTE: I wish Python had a better tool for this
# Like (for example) rustfmt
from kadishutu.core.shared.file_handling import DecryptedSave
from kadishutu.core.shared.pc_saves import SaveFile, discover_saves
from kadishutu.data.save_locs import SAVE_LOCS
from kadishutu.plugin.loader import PLUGIN_MANAGER

from .components import Card, PageHeader
from .game_save import GameSaveEditorScreen
from .shared import (
    EDIT_EVENTS,
    AppliableWidget,
    OnStackRemovedHook,
    SaveScreenMixin,
    SaveType,
    ScreenMixin,
    refresh_screen,
)
from .shared import has_unapplied_edits as widget_has_unapplied_edits
from .sys_save import SysSaveEditorScreen
from .theme import ThemeController, ThemeMode

MAIN_WINDOW: "MainWindow"


class FileSelector(QWidget):
    _path: Path

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setLayout(QHBoxLayout())
        layout = self.layout()
        assert layout is not None
        layout.setContentsMargins(0, 0, 0, 0)
        self.file_path_display = QLineEdit(self)
        self.file_path_display.setReadOnly(True)
        self.file_path_display.setPlaceholderText("Choose a save file…")
        layout.addWidget(self.file_path_display)
        self.file_open_button = QPushButton("Browse…", self)
        self.file_open_button.clicked.connect(self.on_select_clicked)
        layout.addWidget(self.file_open_button)

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, path: Path):
        self._path = path
        self.file_path_display.setText(str(path))

    def on_select_clicked(self):
        (pathstr, _) = QFileDialog.getOpenFileName(self)
        if not pathstr:
            return
        path = Path(pathstr)
        self._path = path
        self.file_path_display.setText(pathstr)


class FileSelectorPreview(QWidget):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setLayout(QVBoxLayout())
        layout = self.layout()
        assert layout is not None
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.name = QLabel(self)
        layout.addWidget(self.name)
        self.location = QLabel(self)
        layout.addWidget(self.location)
        self.difficulty = QLabel(self)
        layout.addWidget(self.difficulty)
        self.play_time = QLabel(self)
        layout.addWidget(self.play_time)
        self.date = QLabel(self)
        layout.addWidget(self.date)
        self.empty()

    def empty(self):
        self.name.setText("Name: N/A")
        self.location.setText("Location: N/A")
        self.difficulty.setText("Difficulty: N/A")
        self.play_time.setText("Play Time: N/A")
        self.date.setText("Date: N/A")

    def update_preview(self, save: GameSaveEditor):
        self.name.setText("Name: " + save.player.names.save_name.get())
        try:
            save_loc = SAVE_LOCS[save.position.title_save_location]
        except KeyError:
            save_loc = "UNKNOWN"
        self.location.setText("Location: " + save_loc)
        self.difficulty.setText("Difficulty: " + save.difficulty.name)
        self.play_time.setText("Play Time: " + str(save.play_time))
        self.date.setText("Date: " + str(save.time_of_saving))


class FileSelectorMenu(QWidget):
    raw: DecryptedSave | None = None
    detected_saves: list[SaveFile]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.header = PageHeader(
            "Open a save",
            "Select a game save or system save to begin.",
            self,
        )
        layout.addWidget(self.header)

        self.card = Card(self)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(10)

        detected_label = QLabel("Detected saves", self.card)
        detected_label.setObjectName("SectionTitle")
        card_layout.addWidget(detected_label)
        detected_row = QHBoxLayout()
        self.detected_saves_box = QComboBox(self.card)
        self.detected_saves_box.setPlaceholderText("Select a save…")
        self.detected_saves_box.currentIndexChanged.connect(
            self.detected_save_selected
        )
        detected_row.addWidget(self.detected_saves_box, 1)
        self.detected_saves_refresh = QPushButton("Refresh", self.card)
        self.detected_saves_refresh.clicked.connect(
            self.refresh_detected_saves
        )
        detected_row.addWidget(self.detected_saves_refresh)
        card_layout.addLayout(detected_row)

        file_label = QLabel("Save file", self.card)
        file_label.setObjectName("SectionTitle")
        card_layout.addWidget(file_label)
        self.file_path = FileSelector(self.card)
        file_path_display = self.file_path.file_path_display
        file_path_display.textChanged.connect(self.file_selected)
        card_layout.addWidget(self.file_path)

        type_label = QLabel("Save type", self.card)
        type_label.setObjectName("Muted")
        card_layout.addWidget(type_label)
        self.ty = SaveType.GameSave
        self.file_type = QComboBox(self.card)
        self.file_type.addItems([ty.name for ty in SaveType])
        self.file_type.setCurrentText(SaveType.GameSave.name)
        self.file_type.currentTextChanged.connect(self.on_type_changed)
        card_layout.addWidget(self.file_type)

        preview_label = QLabel("Preview", self.card)
        preview_label.setObjectName("SectionTitle")
        card_layout.addWidget(preview_label)
        self.file_preview = FileSelectorPreview(self.card)
        card_layout.addWidget(self.file_preview)

        self.file_open = QPushButton("Open save", self.card)
        self.file_open.setObjectName("PrimaryButton")
        self.file_open.setEnabled(False)
        self.file_open.clicked.connect(self.on_file_open)
        card_layout.addWidget(self.file_open)

        layout.addWidget(self.card)
        layout.addStretch()
        self.refresh_detected_saves()

    def refresh_detected_saves(self):
        self.detected_saves = discover_saves()
        self.detected_saves_box.blockSignals(True)
        self.detected_saves_box.clear()
        if not self.detected_saves:
            self.detected_saves_box.addItem("No PC saves found")
            self.detected_saves_box.setEnabled(False)
        else:
            for save in self.detected_saves:
                self.detected_saves_box.addItem(
                    save.display_name,
                    str(save.path),
                )
            self.detected_saves_box.setEnabled(True)
            self.detected_saves_box.setCurrentIndex(-1)
        self.detected_saves_box.blockSignals(False)

    def detected_save_selected(self, index: int):
        if index < 0:
            return
        path = self.detected_saves_box.itemData(index)
        if not path:
            return
        self.file_path.path = Path(path)

    def on_file_open(self):
        if self.raw is None:
            return
        if self.ty == SaveType.SysSave:
            editor = SysSaveEditorScreen(self.file_path.path, self.raw, self)
        else:
            editor = GameSaveEditorScreen(self.file_path.path, self.raw, self)
        MAIN_WINDOW.stack_add(editor)

    def file_selected(self):
        path = self.file_path.path
        self.raw = None
        self.file_open.setEnabled(False)
        self.file_preview.empty()

        try:
            raw = DecryptedSave.auto_open(path)
        except (OSError, ValueError, AssertionError) as exc:
            QMessageBox.critical(self, "Could not open save", str(exc))
            return

        if not raw.hash_validate():
            answer = QMessageBox.warning(
                self,
                "Invalid save hash",
                "The save file's hash is invalid. It may be corrupted or "
                "modified by another tool.\n\nOpen it anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        if len(raw.data) == 0x12e0:
            self.file_type.setDisabled(True)
            self.ty = SaveType.SysSave
        elif len(raw.data) == 0x6dc90:
            self.file_type.setDisabled(True)
            self.ty = SaveType.GameSave
            try:
                save = GameSaveEditor(raw)
            except Exception as exc:
                QMessageBox.critical(self, "Could not parse game save", str(exc))
                return
            self.file_preview.update_preview(save)
        else:
            self.file_type.setDisabled(False)
            return

        self.raw = raw
        self.file_open.setEnabled(True)
        self.file_type.setCurrentText(self.ty.name)

    def on_type_changed(self, tystr: str):
        ty = SaveType[tystr]
        self.ty = ty


class LocationBar(QScrollArea):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setFixedHeight(10)
        self.inner = QWidget(self)
        self.setWidget(self.inner)
        self.inner.setLayout(QHBoxLayout())
        inner_layout = self.inner.layout()
        assert inner_layout is not None
        inner_layout.setContentsMargins(0, 0, 0, 0)
        #self.scroll_bar = QScrollBar(QtCore.Orientation.Horizontal, self.scrolla)
        #self.scrolla.setHorizontalScrollBar(self.scroll_bar)
        #self.scrolla.horizontalScrollBar().setEnabled(True)
        #self.scrolla.setHorizontalScrollBarPolicy(QtCore.ScrollBarPolicy.ScrollBarAlwaysOn)
        #self.inner.setHorizontalScrollBarPolicy(QtCore.ScrollBarPolicy.ScrollBarAlwaysOn)
        #self.scroll_area.setWidgetResizable(True)
        #self.inner.setMaximumSize(9999, self.inner.maximumSize().height())
        #self.inner = QWidget(self.scrolla)
        #self.setMaximumHeight(40)
        for i in range(10):
            txt = chr(64 + i + 1) * 6
            b = QPushButton(txt, self.inner)
            b.setContentsMargins(0, 0, 0, 0)
            inner_layout.addWidget(b)
        #self.a = QLabel("aaaaa", self)
        #self.addWidget(self.a)


class ManagedStackWidget(QWidget):
    widget_stack: list[QWidget]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.widget_stack = []
        self.setLayout(QVBoxLayout())
        layout = self.layout()
        assert layout is not None
        layout.setContentsMargins(0, 0, 0, 0)
        # TODO
        #self.location_bar = LocationBar(self)
        #self.layout().addWidget(self.location_bar)
        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack)

    @property
    def should_show_navigation(self) -> bool:
        return len(self.widget_stack) > 1

    def stack_add(self, widget: QWidget):
        if isinstance(widget, ScreenMixin):
            refresh_screen(widget)
        widget.setParent(self)
        self.widget_stack.append(widget)
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)
        #if self.should_show_navigation:
        #    self.location_bar.show()

    def stack_remove(self):
        if len(self.widget_stack) < 2:
            raise ValueError("Refusing to go back with widget stack at 1")
        widget = self.widget_stack.pop()
        if isinstance(widget, OnStackRemovedHook):
            widget.on_stack_removed()
        self.stack.removeWidget(widget)
        self.stack.setCurrentWidget(self.widget_stack[-1])
        #if len(self.widget_stack) < 2:
        #    self.location_bar.hide()

    @property
    def top_widget(self) -> QWidget:
        return self.widget_stack[-1]

    @property
    def editor_widget(self) -> SaveScreenMixin:
        widget = self.widget_stack[1]
        assert isinstance(widget, SaveScreenMixin)
        return widget


class MainWindow(QMainWindow):
    def __init__(
        self,
        *args,
        theme_controller: ThemeController | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.theme_controller = theme_controller
        self.theme_actions: dict[ThemeMode, QAction] = {}

        self.setWindowTitle("Kadishutu Save Editor")
        self.resize(1120, 760)
        self.setMinimumSize(900, 620)

        self.file_menu = QMenu("File", self)
        self.save_button = self._make_action(
            "Save to Disk",
            QKeySequence.StandardKey.Save,
            self.on_save,
        )
        self.save_button.setToolTip(
            "Write applied changes to the save file and create a backup."
        )
        self.save_as_button = self._make_action(
            "Save as",
            QKeySequence.StandardKey.SaveAs,
            self.on_save_as,
        )
        self.close_button = self._make_action(
            "Close",
            QKeySequence("Ctrl+W"),
            self.on_file_close,
        )
        self.quit_button = self._make_action(
            "Quit",
            QKeySequence.StandardKey.Quit,
            self._quit,
        )
        self.file_menu.addAction(self.save_button)
        self.file_menu.addAction(self.save_as_button)
        self.file_menu.addAction(self.close_button)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.quit_button)
        self.menuBar().addMenu(self.file_menu)

        self.edit_menu = QMenu("Edit", self)
        self.undo_button = self._make_action(
            "Discard Unapplied Edits",
            QKeySequence.StandardKey.Undo,
            self.on_undo,
        )
        self.undo_button.setToolTip(
            "Reload this screen and discard edits that were not applied."
        )
        self.apply_button = self._make_action(
            "Apply Changes",
            QKeySequence("Ctrl+Return"),
            self.on_apply,
        )
        self.apply_button.setToolTip(
            "Copy this screen's edits into the open save. Does not write to "
            "disk."
        )
        self.edit_menu.addAction(self.undo_button)
        self.edit_menu.addAction(self.apply_button)
        self.menuBar().addMenu(self.edit_menu)

        self.navigate_menu = QMenu("Navigate", self)
        self.back_button = self._make_action(
            "Back",
            QKeySequence("Alt+Left"),
            self.on_back,
        )
        self.navigate_menu.addAction(self.back_button)
        self.menuBar().addMenu(self.navigate_menu)

        self._build_theme_menu()
        self._build_toolbar()
        self._build_status_bar()
        EDIT_EVENTS.changed.connect(self.update_status)

        self.inner = ManagedStackWidget(self)
        self.inner.setObjectName("AppRoot")
        self.setCentralWidget(self.inner)

        self.file_selector = FileSelectorMenu(self)
        self.stack_add(self.file_selector)
        self.back_button.setEnabled(False)

    def _make_action(
        self,
        text: str,
        shortcut: QKeySequence | QKeySequence.StandardKey | None,
        slot: Callable[[], None],
    ) -> QAction:
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        return action

    def _quit(self) -> None:
        self.close()

    def _build_theme_menu(self) -> None:
        if self.theme_controller is None:
            return
        self.view_menu = QMenu("View", self)
        theme_menu = self.view_menu.addMenu("Theme")
        group = QActionGroup(self)
        group.setExclusive(True)
        for mode in (ThemeMode.SYSTEM, ThemeMode.LIGHT, ThemeMode.DARK):
            action = QAction(mode.label, self)
            action.setCheckable(True)
            action.setChecked(self.theme_controller.mode is mode)
            action.triggered.connect(
                lambda _checked=False, mode=mode: self._set_theme(mode)
            )
            group.addAction(action)
            theme_menu.addAction(action)
            self.theme_actions[mode] = action
        self.theme_group = group
        self.menuBar().addMenu(self.view_menu)

    def _set_theme(self, mode: ThemeMode) -> None:
        if self.theme_controller is None:
            return
        self.theme_controller.set_mode(mode)
        for action_mode, action in self.theme_actions.items():
            action.setChecked(action_mode is mode)

    def _build_toolbar(self) -> None:
        self.toolbar = QToolBar("Main", self)
        self.toolbar.setObjectName("MainToolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextOnly
        )
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.toolbar.addAction(self.save_button)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.apply_button)
        self.toolbar.addAction(self.back_button)

    def _build_status_bar(self) -> None:
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("No save open", self)
        self.status_bar.addWidget(self.status_label)

    def stack_add(self, widget: QWidget):
        if not self.confirm_leaving(include_applied=False):
            return
        self.inner.stack_add(widget)
        self.refresh_nav_actions()

    def stack_remove(self):
        self.inner.stack_remove()
        self.refresh_nav_actions()

    def refresh_nav_actions(self):
        if len(self.inner.widget_stack) > 2:
            self.back_button.setEnabled(True)
        else:
            self.back_button.setEnabled(False)
        top_widget = self.inner.top_widget
        if isinstance(top_widget, AppliableWidget):
            self.apply_button.setEnabled(True)
        else:
            self.apply_button.setEnabled(False)
        has_editor = len(self.inner.widget_stack) > 1
        can_save = has_editor and self.inner.editor_widget.can_save
        self.save_button.setEnabled(can_save)
        self.save_as_button.setEnabled(can_save)
        self.close_button.setEnabled(has_editor)
        self.undo_button.setEnabled(has_editor)
        self.update_status()

    def update_status(self) -> None:
        if not self.inner.should_show_navigation:
            self.status_label.setText("No save open")
            self.setWindowTitle("Kadishutu Save Editor")
            return
        widget = self.inner.editor_widget
        if self.has_unapplied_edits():
            state = "Unapplied edits — click Apply Changes first"
            marker = " • unapplied"
        elif widget.modified:
            state = "Applied, not saved — click Save to Disk"
            marker = " • unsaved"
        else:
            state = "Saved"
            marker = ""
        self.status_label.setText(f"{state} · {widget.path}")
        self.setWindowTitle(f"{widget.path.name}{marker} — Kadishutu")

    def on_back(self):
        if not self.confirm_leaving(include_applied=False):
            return
        self.stack_remove()

    def on_apply(self):
        widget = self.inner.top_widget
        if not isinstance(widget, AppliableWidget):
            raise NotImplementedError
        if not (
            getattr(widget, "applies_immediately", False)
            or widget_has_unapplied_edits(widget)
        ):
            self.statusBar().showMessage("No unapplied edits to apply.", 3000)
            return
        self.inner.editor_widget.modified = True
        widget.on_apply_changes()
        for widget in self.inner.widget_stack:
            if not isinstance(widget, ScreenMixin):
                continue
            refresh_screen(widget)
        self.update_status()

    def has_unapplied_edits(self) -> bool:
        return any(
            widget_has_unapplied_edits(widget)
            for widget in self.inner.widget_stack
        )

    def on_save(self):
        if not self.inner.should_show_navigation:
            return
        widget = self.inner.editor_widget
        if not widget.can_save or self._refuse_unapplied_save():
            return
        try:
            widget.raw_save.save_finished(widget.path)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        widget.modified = False
        self.update_status()

    def _refuse_unapplied_save(self) -> bool:
        if not self.has_unapplied_edits():
            return False
        QMessageBox.information(
            self,
            "Apply changes first",
            "You have edits that are not applied yet.\n\nClick Apply Changes "
            "first, then Save to Disk. Unapplied edits are not written to the "
            "save file.",
        )
        return True

    def on_save_as(self):
        if self._refuse_unapplied_save():
            return
        (pathstr, _) = QFileDialog.getSaveFileName(self)
        if not pathstr:
            return
        path = Path(pathstr)
        widget = self.inner.editor_widget
        if not widget.can_save:
            return
        try:
            widget.raw_save.save_finished(path)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        widget.path = path
        widget.modified = False
        self.update_status()

    def on_file_close(self):
        if (self.inner.should_show_navigation and
            not self.confirm_leaving(include_applied=True)):
            return
        while len(self.inner.widget_stack) > 1:
            self.stack_remove()

    def on_undo(self):
        widget = self.inner.top_widget
        if not isinstance(widget, ScreenMixin):
            raise NotImplementedError
        refresh_screen(widget)
        self.update_status()

    def discard_unapplied_edits(self) -> None:
        for widget in self.inner.widget_stack:
            if isinstance(widget, ScreenMixin):
                refresh_screen(widget)
        self.update_status()

    def confirm_leaving(self, *, include_applied: bool) -> bool:
        """Return True if the caller may proceed.

        Unapplied edits are always discarded on confirmation. Applied but
        unsaved changes are only checked when closing the save or the app,
        since navigating within the open save keeps them in memory.
        """
        pending = self.has_unapplied_edits()
        applied = (
            include_applied
            and self.inner.should_show_navigation
            and self.inner.editor_widget.modified
        )
        if not (pending or applied):
            return True
        reasons = []
        if pending:
            reasons.append("Unapplied edits will be discarded.")
        if applied:
            reasons.append("Applied changes that are not saved to disk will be lost.")
        answer = QMessageBox.question(
            self,
            "Unsaved changes",
            " ".join(reasons) + "\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False
        if pending:
            self.discard_unapplied_edits()
        return True

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self.confirm_leaving(include_applied=True):
            event.ignore()
            return
        return super().closeEvent(event)


def gui_main(args: Namespace):
    PLUGIN_MANAGER.exec("gui")
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication()
    app.setApplicationName("Kadishutu")
    app.setApplicationDisplayName("Kadishutu")
    app.setOrganizationName("kadishutu")
    theme_controller = ThemeController(app, parent=app)
    widget = MainWindow(theme_controller=theme_controller)
    global MAIN_WINDOW
    MAIN_WINDOW = widget
    if args.file:
        widget.file_selector.file_path.path = args.file
        widget.file_selector.file_open.click()
    widget.show()
    sys.exit(app.exec())
