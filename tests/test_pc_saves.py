import os
from pathlib import Path

import pytest

from kadishutu.core.shared import pc_saves
from kadishutu.core.shared.pc_saves import (
    GAME_SAVE_SIZE,
    SYS_SAVE_SIZE,
    SaveFile,
    discover_save_dirs,
    discover_saves,
    list_saves,
    save_roots,
)


def make_save(path: Path, size: int, modified: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\0" * size)
    os.utime(path, (modified, modified))
    return path


def test_list_saves_classifies_and_sorts(tmp_path: Path):
    game = make_save(tmp_path / "GameSave01.sav", GAME_SAVE_SIZE, 1000)
    system = make_save(tmp_path / "SysSave.sav", SYS_SAVE_SIZE, 2000)
    make_save(tmp_path / "SysSaveLocal.sav", 3104, 3000)
    make_save(tmp_path / "GameSave01.sav.bak", GAME_SAVE_SIZE, 4000)

    saves = list_saves(tmp_path)

    assert [save.path for save in saves] == [system, game]
    assert [save.kind for save in saves] == ["system", "game"]
    assert saves[0].display_name.startswith(tmp_path.name + "/SysSave.sav")


def test_discover_save_dirs_finds_steam_account_folders(tmp_path: Path):
    first = tmp_path / "111"
    second = tmp_path / "222"
    make_save(first / "GameSave01.sav", GAME_SAVE_SIZE, 1000)
    make_save(second / "AutoSave01.sav", GAME_SAVE_SIZE, 2000)
    (tmp_path / "empty").mkdir()

    assert discover_save_dirs(tmp_path) == [first, second]


def test_discover_saves_sorts_across_folders(tmp_path: Path):
    first = tmp_path / "111"
    second = tmp_path / "222"
    make_save(first / "GameSave01.sav", GAME_SAVE_SIZE, 1000)
    make_save(first / "SysSave.sav", SYS_SAVE_SIZE, 2000)
    make_save(second / "AutoSave01.sav", GAME_SAVE_SIZE, 3000)

    saves = discover_saves(tmp_path)

    assert [save.path.name for save in saves] == [
        "AutoSave01.sav",
        "SysSave.sav",
        "GameSave01.sav",
    ]


def test_save_roots_uses_appdata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    monkeypatch.setattr(pc_saves, "steam_compat_save_roots", lambda: [])

    roots = save_roots()

    assert roots == [
        tmp_path / "Roaming" / "SEGA" / "SMT5V" / "Steam",
    ]


def test_save_file_modified_text_is_stable():
    save = SaveFile(
        path=Path("111/GameSave01.sav"),
        kind="game",
        size=GAME_SAVE_SIZE,
        modified=1_700_000_000,
    )

    assert save.modified_text
    assert "/GameSave01.sav" in save.display_name
