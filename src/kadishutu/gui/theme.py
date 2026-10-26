from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from string import Template

from PySide6.QtCore import QObject, QSettings, Qt
from PySide6.QtGui import QColor, QFontDatabase, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory


class ThemeMode(Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"

    @classmethod
    def from_value(cls, value: object) -> ThemeMode:
        if isinstance(value, str):
            try:
                return cls(value)
            except ValueError:
                pass
        return cls.SYSTEM

    @property
    def label(self) -> str:
        return self.value.capitalize()


@dataclass(frozen=True, slots=True)
class ThemeColors:
    window: str
    window_alt: str
    surface: str
    surface_alt: str
    surface_hover: str
    border: str
    border_strong: str
    text: str
    text_muted: str
    text_disabled: str
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_text: str
    focus: str
    danger: str
    success: str


DARK_COLORS = ThemeColors(
    window="#0f1115",
    window_alt="#12151c",
    surface="#171b24",
    surface_alt="#1f2531",
    surface_hover="#242b39",
    border="#2b3342",
    border_strong="#3a4557",
    text="#e7eaf0",
    text_muted="#9aa4b5",
    text_disabled="#687284",
    accent="#8b5cf6",
    accent_hover="#a78bfa",
    accent_pressed="#7c3aed",
    accent_text="#ffffff",
    focus="#a78bfa",
    danger="#f87171",
    success="#34d399",
)

LIGHT_COLORS = ThemeColors(
    window="#f4f6fb",
    window_alt="#eef1f7",
    surface="#ffffff",
    surface_alt="#f8fafc",
    surface_hover="#f1f5f9",
    border="#d9e0ea",
    border_strong="#c2ccda",
    text="#1e293b",
    text_muted="#64748b",
    text_disabled="#94a3b8",
    accent="#6d5efc",
    accent_hover="#5b4df0",
    accent_pressed="#4f46e5",
    accent_text="#ffffff",
    focus="#6d5efc",
    danger="#dc2626",
    success="#059669",
)

_FONT_CANDIDATES = (
    "Segoe UI Variable Text",
    "Segoe UI Variable",
    "Segoe UI",
    "Noto Sans",
    "DejaVu Sans",
    "Helvetica Neue",
    "Arial",
)

_THEME_KEY = "appearance/theme"
_SETTINGS_ORG = "kadishutu"
_SETTINGS_APP = "kadishutu"


_STYLESHEET = Template(
    """
QWidget {
    color: $text;
}

QMainWindow, QDialog, QWidget#AppRoot, QStackedWidget, QScrollArea {
    background-color: $window;
}

QScrollArea {
    border: none;
}

QWidget#ScrollContent {
    background-color: $window;
}

QFrame#Card {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}

QLabel#PageTitle {
    font-size: 22px;
    font-weight: 700;
    color: $text;
}

QLabel#PageSubtitle {
    color: $text_muted;
    font-size: 10pt;
}

QLabel#SectionTitle {
    font-size: 13px;
    font-weight: 600;
    color: $text;
}

QLabel#Muted {
    color: $text_muted;
}

QLabel#StatValue {
    font-size: 18px;
    font-weight: 600;
}

QMenuBar {
    background-color: $window;
    border-bottom: 1px solid $border;
    padding: 2px 6px;
}

QMenuBar::item {
    background: transparent;
    border-radius: 6px;
    padding: 6px 10px;
}

QMenuBar::item:selected {
    background-color: $surface_alt;
}

QMenuBar::item:pressed {
    background-color: $surface_hover;
}

QMenu {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    border-radius: 6px;
    padding: 7px 28px 7px 12px;
}

QMenu::item:selected {
    background-color: $surface_hover;
}

QMenu::separator {
    background: $border;
    height: 1px;
    margin: 6px 8px;
}

QToolBar {
    background-color: $surface;
    border-bottom: 1px solid $border;
    padding: 6px 10px;
    spacing: 6px;
}

QToolBar::separator {
    background: $border;
    margin: 4px 6px;
    width: 1px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    color: $text;
    padding: 6px 12px;
}

QToolButton:hover {
    background-color: $surface_alt;
    border-color: $border;
}

QToolButton:pressed {
    background-color: $surface_hover;
}

QToolButton:disabled {
    color: $text_disabled;
}

QStatusBar {
    background-color: $surface;
    border-top: 1px solid $border;
    color: $text_muted;
}

QStatusBar QLabel {
    color: $text_muted;
    padding: 2px 8px;
}

QPushButton {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 8px;
    color: $text;
    min-height: 20px;
    padding: 7px 14px;
}

QPushButton:hover {
    background-color: $surface_hover;
    border-color: $border_strong;
}

QPushButton:pressed {
    background-color: $window_alt;
}

QPushButton:disabled {
    background-color: $window_alt;
    border-color: $border;
    color: $text_disabled;
}

QPushButton:default, QPushButton#PrimaryButton {
    background-color: $accent;
    border-color: $accent;
    color: $accent_text;
    font-weight: 600;
}

QPushButton:default:hover, QPushButton#PrimaryButton:hover {
    background-color: $accent_hover;
    border-color: $accent_hover;
}

QPushButton:default:pressed, QPushButton#PrimaryButton:pressed {
    background-color: $accent_pressed;
    border-color: $accent_pressed;
}

QPushButton#CategoryCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
    font-weight: 600;
    min-height: 58px;
    padding: 14px 16px;
    text-align: left;
}

QPushButton#CategoryCard:hover {
    background-color: $surface_alt;
    border-color: $accent;
}

QPushButton#CategoryCard:pressed {
    background-color: $surface_hover;
}

QPushButton#CategoryCard:disabled {
    border-color: $border;
    color: $text_disabled;
}

QLabel#CategoryTitle {
    color: $text;
    font-size: 12pt;
    font-weight: 600;
}

QLabel#CategoryDescription {
    color: $text_muted;
    font-size: 9pt;
}

QLabel#CategoryTitle:disabled {
    color: $text_disabled;
}

QLabel#CategoryDescription:disabled {
    color: $text_disabled;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 8px;
    min-height: 20px;
    padding: 6px 9px;
    selection-background-color: $accent;
    selection-color: $accent_text;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: $focus;
}

QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: $window_alt;
    color: $text_disabled;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: $surface;
    border: 1px solid $border;
    padding: 4px;
    selection-background-color: $surface_hover;
    selection-color: $text;
}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: transparent;
    border: none;
    width: 18px;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    background-color: $surface_alt;
    border: 1px solid $border_strong;
    border-radius: 4px;
    height: 16px;
    width: 16px;
}

QCheckBox::indicator:hover {
    border-color: $accent;
}

QCheckBox::indicator:checked {
    background-color: $accent;
    border-color: $accent;
}

QTabWidget::pane {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 10px;
    top: -1px;
}

QTabBar::tab {
    background: transparent;
    border-radius: 8px;
    color: $text_muted;
    margin-right: 4px;
    padding: 8px 14px;
}

QTabBar::tab:selected {
    background: $surface_alt;
    color: $text;
}

QTabBar::tab:hover {
    background: $surface_hover;
}

QScrollBar:vertical {
    background: transparent;
    margin: 2px;
    width: 12px;
}

QScrollBar::handle:vertical {
    background: $border_strong;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: $text_muted;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 12px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background: $border_strong;
    border-radius: 5px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background: $text_muted;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QToolTip {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 6px;
    color: $text;
    padding: 5px 8px;
}

QGroupBox {
    border: 1px solid $border;
    border-radius: 10px;
    font-weight: 600;
    margin-top: 12px;
    padding: 14px 10px 10px 10px;
}

QGroupBox::title {
    color: $text_muted;
    left: 12px;
    padding: 0 4px;
    subcontrol-origin: margin;
}

QMessageBox {
    background-color: $surface;
}
"""
)


def theme_colors(mode: ThemeMode) -> ThemeColors:
    if mode is ThemeMode.LIGHT:
        return LIGHT_COLORS
    return DARK_COLORS


def resolve_theme_mode(
    mode: ThemeMode,
    scheme: Qt.ColorScheme | None = None,
) -> ThemeMode:
    if mode is not ThemeMode.SYSTEM:
        return mode
    if scheme is None:
        scheme = QGuiApplication.styleHints().colorScheme()
    if scheme is Qt.ColorScheme.Dark:
        return ThemeMode.DARK
    return ThemeMode.LIGHT


def build_palette(mode: ThemeMode) -> QPalette:
    colors = theme_colors(mode)
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: colors.window,
        QPalette.ColorRole.WindowText: colors.text,
        QPalette.ColorRole.Base: colors.surface_alt,
        QPalette.ColorRole.AlternateBase: colors.surface,
        QPalette.ColorRole.Text: colors.text,
        QPalette.ColorRole.Button: colors.surface_alt,
        QPalette.ColorRole.ButtonText: colors.text,
        QPalette.ColorRole.BrightText: colors.accent_text,
        QPalette.ColorRole.Highlight: colors.accent,
        QPalette.ColorRole.HighlightedText: colors.accent_text,
        QPalette.ColorRole.Link: colors.accent,
        QPalette.ColorRole.LinkVisited: colors.accent_pressed,
        QPalette.ColorRole.PlaceholderText: colors.text_muted,
        QPalette.ColorRole.ToolTipBase: colors.surface_alt,
        QPalette.ColorRole.ToolTipText: colors.text,
        QPalette.ColorRole.Mid: colors.border,
        QPalette.ColorRole.Midlight: colors.border_strong,
        QPalette.ColorRole.Dark: colors.window_alt,
        QPalette.ColorRole.Light: colors.surface,
        QPalette.ColorRole.Shadow: colors.border_strong,
    }
    for role, color in roles.items():
        palette.setColor(role, QColor(color))

    disabled = QPalette.ColorGroup.Disabled
    palette.setColor(disabled, QPalette.ColorRole.Text, QColor(colors.text_disabled))
    palette.setColor(
        disabled, QPalette.ColorRole.WindowText, QColor(colors.text_disabled)
    )
    palette.setColor(
        disabled, QPalette.ColorRole.ButtonText, QColor(colors.text_disabled)
    )
    return palette


def build_stylesheet(mode: ThemeMode) -> str:
    return _STYLESHEET.substitute(asdict(theme_colors(mode)))


def preferred_font_family() -> str | None:
    families = set(QFontDatabase.families())
    for candidate in _FONT_CANDIDATES:
        if candidate in families:
            return candidate
    return None


def apply_theme(app: QApplication, mode: ThemeMode) -> ThemeMode:
    resolved = resolve_theme_mode(mode)
    style = QStyleFactory.create("Fusion")
    if style is not None:
        app.setStyle(style)
    app.setPalette(build_palette(resolved))
    app.setStyleSheet(build_stylesheet(resolved))

    family = preferred_font_family()
    if family is not None:
        font = app.font()
        font.setFamily(family)
        font.setPointSize(10)
        app.setFont(font)
    return resolved


def _settings(settings: QSettings | None = None) -> QSettings:
    if settings is not None:
        return settings
    return QSettings(_SETTINGS_ORG, _SETTINGS_APP)


def load_theme_mode(settings: QSettings | None = None) -> ThemeMode:
    value = _settings(settings).value(_THEME_KEY, ThemeMode.SYSTEM.value)
    return ThemeMode.from_value(value)


def save_theme_mode(mode: ThemeMode, settings: QSettings | None = None) -> None:
    _settings(settings).setValue(_THEME_KEY, mode.value)


class ThemeController(QObject):
    def __init__(
        self,
        app: QApplication,
        parent: QObject | None = None,
        settings: QSettings | None = None,
    ) -> None:
        super().__init__(parent)
        self.app = app
        self.settings = settings
        self._mode = load_theme_mode(settings)
        self._resolved_mode = apply_theme(app, self._mode)
        app.styleHints().colorSchemeChanged.connect(self._on_system_theme_changed)

    @property
    def mode(self) -> ThemeMode:
        return self._mode

    @property
    def resolved_mode(self) -> ThemeMode:
        return self._resolved_mode

    def set_mode(self, mode: ThemeMode) -> None:
        self._mode = mode
        save_theme_mode(mode, self.settings)
        self._resolved_mode = apply_theme(self.app, mode)

    def _on_system_theme_changed(self, _scheme: Qt.ColorScheme) -> None:
        if self._mode is ThemeMode.SYSTEM:
            self._resolved_mode = apply_theme(self.app, self._mode)
