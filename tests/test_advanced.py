from PySide6.QtCore import QSettings

from kadishutu.gui.advanced import (
    ADVANCED_KEY,
    AdvancedMode,
    load_advanced,
    save_advanced,
)


def make_settings(tmp_path):
    return QSettings(
        str(tmp_path / "settings.ini"),
        QSettings.Format.IniFormat,
    )


def test_advanced_mode_defaults_to_off(tmp_path):
    settings = make_settings(tmp_path)

    assert load_advanced(settings) is False


def test_advanced_mode_round_trip(tmp_path):
    settings = make_settings(tmp_path)
    mode = AdvancedMode(settings)

    mode.set_enabled(True)

    assert mode.enabled is True
    assert load_advanced(settings) is True
    assert settings.value(ADVANCED_KEY) in (True, "true")

    reopened = AdvancedMode(settings)
    assert reopened.enabled is True

    reopened.set_enabled(False)
    assert load_advanced(settings) is False


def test_advanced_mode_accepts_string_values(tmp_path):
    settings = make_settings(tmp_path)

    settings.setValue(ADVANCED_KEY, "true")
    assert load_advanced(settings) is True

    settings.setValue(ADVANCED_KEY, "off")
    assert load_advanced(settings) is False


def test_advanced_mode_emits_only_on_change(tmp_path):
    settings = make_settings(tmp_path)
    mode = AdvancedMode(settings)
    seen: list[bool] = []
    mode.changed.connect(seen.append)

    mode.set_enabled(False)
    mode.set_enabled(True)
    mode.set_enabled(True)
    mode.toggle()

    assert seen == [True, False]


def test_save_advanced_uses_shared_key(tmp_path):
    settings = make_settings(tmp_path)

    save_advanced(True, settings)

    assert settings.value(ADVANCED_KEY) in (True, "true")
