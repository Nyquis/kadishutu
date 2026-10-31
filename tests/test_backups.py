import os
from datetime import datetime
from pathlib import Path

import pytest

from kadishutu.core.shared.backups import (
    BackupEntry,
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
    validate_backup,
)
from kadishutu.core.shared.file_handling import DecryptedSave

TARGET_NAME = "GameSave01.sav"


def make_target(tmp_path: Path, data: bytes = b"current") -> Path:
    target = tmp_path / TARGET_NAME
    target.write_bytes(data)
    return target


def write_backup(
    target: Path,
    name: str,
    data: bytes,
    modified: float | None = None,
) -> Path:
    path = target.parent / name
    path.write_bytes(data)
    if modified is not None:
        os.utime(path, (modified, modified))
    return path


def test_list_backups_finds_timestamped_legacy_and_collision(tmp_path: Path):
    target = make_target(tmp_path)
    write_backup(
        target,
        f"{TARGET_NAME}.20240102-030405-123456.bak",
        b"timestamped",
    )
    write_backup(target, f"{TARGET_NAME}.bak", b"legacy", 1000)
    write_backup(target, f"{TARGET_NAME}.bak2", b"legacy2", 2000)
    write_backup(
        target,
        f"{TARGET_NAME}.20240102-030405-123456.1.bak",
        b"collision",
    )
    write_backup(tmp_path, "Other.sav.bak", b"other")

    entries = list_backups(target)

    assert len(entries) == 4
    assert {entry.path.name for entry in entries} == {
        f"{TARGET_NAME}.20240102-030405-123456.bak",
        f"{TARGET_NAME}.20240102-030405-123456.1.bak",
        f"{TARGET_NAME}.bak",
        f"{TARGET_NAME}.bak2",
    }
    assert sorted(entry.kind for entry in entries) == [
        "legacy", "legacy", "timestamped", "timestamped",
    ]
    timestamped = [
        entry for entry in entries if entry.kind == "timestamped"
    ]
    assert all(
        entry.created_at == datetime(2024, 1, 2, 3, 4, 5, 123456)
        for entry in timestamped
    )


def test_create_backup_copies_current_file(tmp_path: Path):
    target = make_target(tmp_path, b"current bytes")

    entry = create_backup(target)

    assert entry.target == target
    assert entry.kind == "timestamped"
    assert entry.path.read_bytes() == b"current bytes"
    assert entry in list_backups(target)


def test_create_backup_requires_existing_target(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        create_backup(tmp_path / TARGET_NAME)


def test_restore_backup_creates_safety_backup(tmp_path: Path):
    target = make_target(tmp_path, b"current")
    backup_path = write_backup(
        target,
        f"{TARGET_NAME}.20240102-030405-123456.bak",
        b"old",
    )
    entry = list_backups(target)[0]

    safety = restore_backup(entry)

    assert target.read_bytes() == b"old"
    assert safety is not None
    assert safety.read_bytes() == b"current"
    assert backup_path.read_bytes() == b"old"


def test_restore_rejects_unrelated_file(tmp_path: Path):
    target = make_target(tmp_path)
    unrelated = write_backup(tmp_path, "Other.sav.bak", b"other")
    entry = BackupEntry(
        target=target,
        path=unrelated,
        created_at=datetime.now(),
        size=unrelated.stat().st_size,
        kind="legacy",
    )

    with pytest.raises(ValueError, match="not a backup"):
        restore_backup(entry)


def test_delete_backup_removes_only_backup(tmp_path: Path):
    target = make_target(tmp_path, b"current")
    create_backup(target)
    entry = list_backups(target)[0]

    delete_backup(entry)

    assert not entry.path.exists()
    assert target.read_bytes() == b"current"


def test_delete_rejects_unrelated_file(tmp_path: Path):
    target = make_target(tmp_path)
    unrelated = write_backup(tmp_path, "Other.sav.bak", b"other")
    entry = BackupEntry(
        target=target,
        path=unrelated,
        created_at=datetime.now(),
        size=unrelated.stat().st_size,
        kind="legacy",
    )

    with pytest.raises(ValueError, match="not a backup"):
        delete_backup(entry)


def test_validate_backup_accepts_valid_save(tmp_path: Path):
    target = make_target(tmp_path)
    data = bytearray(0x100)
    data[0x40:0x44] = b"GVAS"
    save = DecryptedSave(data)
    save.hash_update()
    backup_path = write_backup(
        target,
        f"{TARGET_NAME}.20240102-030405-123456.bak",
        bytes(save.data),
    )
    entry = list_backups(target)[0]

    result = validate_backup(entry)

    assert result.ok
    assert "Valid save" in result.message
    assert backup_path.exists()


def test_validate_backup_rejects_corrupt_hash(tmp_path: Path):
    target = make_target(tmp_path)
    data = bytearray(0x100)
    data[0x40:0x44] = b"GVAS"
    save = DecryptedSave(data)
    save.hash_update()
    data = bytearray(save.data)
    data[0x50] ^= 0xFF
    write_backup(
        target,
        f"{TARGET_NAME}.20240102-030405-123456.bak",
        bytes(data),
    )
    entry = list_backups(target)[0]

    result = validate_backup(entry)

    assert not result.ok
    assert "hash" in result.message.lower()
