
from os import getenv
from pathlib import Path

from kadishutu.paths import APPDIRS
from kadishutu.tools.eprint import eprintf
from kadishutu.tools.singleton import AbstractSingleton

from .meta import Plugin, PluginError

PLUGINS_PATH = APPDIRS.data_path / "plugins"
# Set to 1 to skip loading plugins entirely. Plugins are arbitrary Python.
DISABLE_ENV = "KADISHUTU_DISABLE_PLUGINS"


class PluginManager(AbstractSingleton):
    plugins: list[Plugin] = []

    def reload(self):
        if getenv(DISABLE_ENV, "") not in ("", "0"):
            self.plugins = []
            return
        if not PLUGINS_PATH.exists():
            return

        def loadp(path: Path) -> Plugin | None:
            try:
                plugin = Plugin.try_load(path)
            except PluginError as exc:
                eprintf("Skipping plugin {}: {}", path.name, exc)
                return None
            if plugin is None:
                eprintf("Failed to load plugin {}", path.name)
            return plugin

        self.plugins = [
            plugin
            for plugin in [
                loadp(plug_path)
                for plug_path in PLUGINS_PATH.iterdir()
            ]
            if plugin is not None
        ]

    def which_have_stage(self, stage: str) -> list[Plugin]:
        return [
            plugin
            for plugin in self.plugins
            if plugin.manifest.stage == stage
        ]

    def exec(self, stage: str):
        for plugin in self.which_have_stage(stage):
            plugin.exec()


PLUGIN_MANAGER = PluginManager()
