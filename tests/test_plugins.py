import json
from pathlib import Path

import pytest

from kadishutu.plugin import loader
from kadishutu.plugin.loader import PluginManager
from kadishutu.plugin.meta import Plugin, PluginError


def write_plugin(root: Path, folder: str, name: str, **overrides) -> Path:
    plugin_dir = root / folder
    plugin_dir.mkdir(parents=True)
    manifest = {
        "name": name,
        "author": "tester",
        "version": "1.0",
        "stage": "main",
    }
    manifest.update(overrides)
    (plugin_dir / "manifest.json").write_text(json.dumps(manifest))
    (plugin_dir / f"{name}.py").write_text("LOADED = True\n")
    return plugin_dir


@pytest.mark.parametrize(
    "name",
    ["../evil", "sub/evil", "..", "evil.py", "with space", ""],
)
def test_plugin_name_must_be_a_plain_identifier(tmp_path: Path, name: str):
    plugin_dir = write_plugin(tmp_path, "plug", "good")
    (plugin_dir / "manifest.json").write_text(
        json.dumps({
            "name": name,
            "author": "tester",
            "version": "1.0",
            "stage": "main",
        })
    )

    with pytest.raises(PluginError, match="name"):
        Plugin.try_load(plugin_dir)


def test_valid_plugin_loads(tmp_path: Path):
    plugin_dir = write_plugin(tmp_path, "plug", "good_plugin")

    plugin = Plugin.try_load(plugin_dir)

    assert plugin is not None
    assert plugin.manifest.name == "good_plugin"


def test_missing_manifest_is_not_a_plugin(tmp_path: Path):
    assert Plugin.try_load(tmp_path) is None


def test_malformed_manifest_json_raises_plugin_error(tmp_path: Path):
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()
    (plugin_dir / "manifest.json").write_text("{not json")

    with pytest.raises(PluginError, match="manifest"):
        Plugin.try_load(plugin_dir)


def test_manifest_missing_fields_raises_plugin_error(tmp_path: Path):
    plugin_dir = tmp_path / "plug"
    plugin_dir.mkdir()
    (plugin_dir / "manifest.json").write_text(json.dumps({"name": "x"}))

    with pytest.raises(PluginError, match="manifest"):
        Plugin.try_load(plugin_dir)


def test_reload_skips_broken_plugins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    write_plugin(tmp_path, "good", "good_plugin", stage="gui")
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "manifest.json").write_text("{not json")
    evil = tmp_path / "evil"
    evil.mkdir()
    (evil / "manifest.json").write_text(
        json.dumps({
            "name": "../evil",
            "author": "tester",
            "version": "1.0",
            "stage": "main",
        })
    )

    monkeypatch.setattr(loader, "PLUGINS_PATH", tmp_path)
    monkeypatch.delenv(loader.DISABLE_ENV, raising=False)
    manager = PluginManager()
    monkeypatch.setattr(manager, "plugins", [])

    manager.reload()

    names = [plugin.manifest.name for plugin in manager.plugins]
    assert names == ["good_plugin"]


def test_disable_env_prevents_plugin_loading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    write_plugin(tmp_path, "good", "good_plugin")

    monkeypatch.setattr(loader, "PLUGINS_PATH", tmp_path)
    monkeypatch.setenv(loader.DISABLE_ENV, "1")
    manager = PluginManager()
    monkeypatch.setattr(manager, "plugins", [])

    manager.reload()

    assert manager.plugins == []
