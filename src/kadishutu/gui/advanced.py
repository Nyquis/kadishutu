"""Global safe/advanced editing state.

Safe mode keeps game-managed and derived fields read-only. Advanced mode
unlocks them, but it never blocks a save: every risky field keeps its warning
and the game may still recalculate the value later.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QSettings, Signal

SETTINGS_ORG = "kadishutu"
SETTINGS_APP = "kadishutu"
ADVANCED_KEY = "ui/advanced_mode"


def _settings(settings: QSettings | None = None) -> QSettings:
    if settings is not None:
        return settings
    return QSettings(SETTINGS_ORG, SETTINGS_APP)


def load_advanced(settings: QSettings | None = None) -> bool:
    value = _settings(settings).value(ADVANCED_KEY, False)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def save_advanced(
    enabled: bool,
    settings: QSettings | None = None,
) -> None:
    _settings(settings).setValue(ADVANCED_KEY, bool(enabled))


class AdvancedMode(QObject):
    changed = Signal(bool)

    def __init__(
        self,
        settings: QSettings | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self._enabled = load_advanced(settings)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._enabled:
            return
        self._enabled = enabled
        save_advanced(enabled, self.settings)
        self.changed.emit(enabled)

    def toggle(self) -> None:
        self.set_enabled(not self._enabled)


_advanced_mode: AdvancedMode | None = None


def advanced_mode() -> AdvancedMode:
    global _advanced_mode
    if _advanced_mode is None:
        _advanced_mode = AdvancedMode()
    return _advanced_mode


def is_advanced() -> bool:
    return advanced_mode().enabled
