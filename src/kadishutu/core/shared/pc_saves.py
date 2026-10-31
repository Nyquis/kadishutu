from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

GAME_SAVE_SIZE = 0x6DC90
SYS_SAVE_SIZE = 0x12E0
STEAM_APP_ID = "1875830"
SAVE_ROOT_PARTS = ("SEGA", "SMT5V", "Steam")

SaveKind = Literal["game", "system"]


@dataclass(frozen=True)
class SaveFile:
    path: Path
    kind: SaveKind
    size: int
    modified: float

    @property
    def modified_text(self) -> str:
        return datetime.fromtimestamp(self.modified).strftime("%Y-%m-%d %H:%M")

    @property
    def display_name(self) -> str:
        return (
            f"{self.path.parent.name}/{self.path.name}"
            f"  ({self.modified_text})"
        )


def windows_save_root() -> Path | None:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return Path(appdata).joinpath(*SAVE_ROOT_PARTS)


def steam_compat_save_roots() -> list[Path]:
    home = Path.home()
    compat = (
        home / ".local" / "share" / "Steam" / "steamapps"
        / "compatdata" / STEAM_APP_ID / "pfx" / "drive_c" / "users"
        / "steamuser" / "AppData" / "Roaming"
    )
    legacy = (
        home / ".steam" / "steam" / "steamapps"
        / "compatdata" / STEAM_APP_ID / "pfx" / "drive_c" / "users"
        / "steamuser" / "AppData" / "Roaming"
    )
    return [
        path.joinpath(*SAVE_ROOT_PARTS)
        for path in (compat, legacy)
        if path.exists()
    ]


def save_roots() -> list[Path]:
    roots: list[Path] = []
    windows = windows_save_root()
    if windows is not None:
        roots.append(windows)
    for root in steam_compat_save_roots():
        if root not in roots:
            roots.append(root)
    return roots


def list_saves(directory: Path) -> list[SaveFile]:
    saves: list[SaveFile] = []
    for path in directory.glob("*.sav"):
        if not path.is_file():
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        if stat.st_size == GAME_SAVE_SIZE:
            kind: SaveKind = "game"
        elif stat.st_size == SYS_SAVE_SIZE:
            kind = "system"
        else:
            continue
        saves.append(SaveFile(path, kind, stat.st_size, stat.st_mtime))
    return sorted(saves, key=lambda save: (-save.modified, save.path.name))


def discover_save_dirs(root: Path | None = None) -> list[Path]:
    roots = [root] if root is not None else save_roots()
    directories: list[Path] = []
    for root_path in roots:
        if not root_path.is_dir():
            continue
        candidates = [root_path]
        candidates.extend(sorted(
            path for path in root_path.iterdir() if path.is_dir()
        ))
        for candidate in candidates:
            if list_saves(candidate) and candidate not in directories:
                directories.append(candidate)
    return directories


def discover_saves(root: Path | None = None) -> list[SaveFile]:
    saves: list[SaveFile] = []
    for directory in discover_save_dirs(root):
        saves.extend(list_saves(directory))
    return sorted(saves, key=lambda save: (-save.modified, save.path.name))
