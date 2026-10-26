import json
import re
from dataclasses import dataclass
from importlib.machinery import ModuleSpec, SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from types import ModuleType
from typing import Self

from mashumaro.mixins.json import DataClassJSONMixin

from kadishutu.tools.eprint import printexcept

ENCODING = "UTF-8"
PLUGIN_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class PluginError(ValueError):
    pass


class PathJsonMixin(DataClassJSONMixin):
    @classmethod
    def from_path(cls, path: Path, encoding: str = ENCODING) -> Self:
        with path.open("rt", encoding=encoding) as file:
            dat = json.load(file)
        return cls.from_dict(dat)


@dataclass
class PluginPaths:
    plugin: Path

    @property
    def manifest(self) -> Path:
        return self.plugin / "manifest.json"


@dataclass
class PluginInfo(PathJsonMixin):
    name: str
    author: str
    version: str
    stage: str
    load_order: float = 0


@dataclass
class PluginMod:
    loader: SourceFileLoader
    spec: ModuleSpec
    module: ModuleType


@dataclass
class Plugin:
    path: PluginPaths
    manifest: PluginInfo
    source: PluginMod | None = None

    @property
    def pyname(self) -> str:
        return f"kadishutu_plugin_{self.manifest.name}"

    @classmethod
    def load(cls, path: PluginPaths) -> Self:
        try:
            manifest = PluginInfo.from_path(path.manifest)
        except Exception as exc:
            raise PluginError(
                f"Invalid manifest {path.manifest}: {exc}"
            ) from exc
        if not PLUGIN_NAME_RE.fullmatch(manifest.name):
            raise PluginError(
                f"Invalid plugin name {manifest.name!r}: names may only "
                "contain letters, digits, and underscores"
            )
        return cls(
            path,
            manifest,
        )

    @classmethod
    def try_load(cls, path: Path) -> Self | None:
        paths = PluginPaths(path)
        if not paths.manifest.exists():
            return None
        return cls.load(paths)

    def exec(self):
        if self.source:
            return
        try:
            loader = SourceFileLoader(
                self.pyname,
                str(self.path.plugin / (self.manifest.name + ".py")),
            )
            spec = spec_from_loader(self.pyname, loader)
            assert spec is not None, "plugins spec is None"
            module = module_from_spec(spec)
            loader.exec_module(module)
        except Exception as e:
            printexcept("Failed to run plugin", e)
        else:
            self.source = PluginMod(
                loader, spec, module,
            )
