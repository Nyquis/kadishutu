from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from .file_handling import (
    DecryptedSave,
    RawSave,
    copy_backup,
)

BackupKind = Literal["timestamped", "legacy"]
TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S-%f"


@dataclass(frozen=True)
class BackupEntry:
    target: Path
    path: Path
    created_at: datetime
    size: int
    kind: BackupKind


@dataclass(frozen=True)
class BackupCheck:
    ok: bool
    message: str


def _backup_regex(target: Path) -> re.Pattern[str]:
    return re.compile(
        rf"^{re.escape(target.name)}"
        rf"(?:\.(\d{{8}}-\d{{6}}-\d{{6}}))?"
        rf"(?:\.(\d+))?"
        rf"\.bak(\d*)$"
    )


def _timestamp(match: re.Match[str]) -> datetime | None:
    raw = match.group(1)
    if raw is None:
        return None
    try:
        return datetime.strptime(raw, TIMESTAMP_FORMAT)
    except ValueError:
        return None


def list_backups(target: Path) -> list[BackupEntry]:
    target = Path(target)
    pattern = _backup_regex(target)
    entries: list[BackupEntry] = []
    if not target.parent.is_dir():
        return entries
    for path in target.parent.iterdir():
        match = pattern.match(path.name)
        if match is None or not path.is_file():
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        created = _timestamp(match)
        if created is None:
            created = datetime.fromtimestamp(stat.st_mtime)
        entries.append(BackupEntry(
            target=target,
            path=path,
            created_at=created,
            size=stat.st_size,
            kind="timestamped" if match.group(1) else "legacy",
        ))
    return sorted(
        entries,
        key=lambda entry: (entry.created_at, entry.path.name),
        reverse=True,
    )


def create_backup(target: Path) -> BackupEntry:
    target = Path(target)
    if not target.is_file():
        raise FileNotFoundError(f"Cannot back up missing file {target}")
    path = copy_backup(target)
    for entry in list_backups(target):
        if entry.path == path:
            return entry
    raise RuntimeError(f"Created backup {path} was not recognized")


def _recognized(backup: BackupEntry) -> bool:
    return backup.path in {
        entry.path for entry in list_backups(backup.target)
    }


def restore_backup(backup: BackupEntry) -> Path | None:
    if not _recognized(backup):
        raise ValueError(f"{backup.path} is not a backup of {backup.target}")
    if not backup.path.is_file():
        raise FileNotFoundError(f"Backup file is missing: {backup.path}")

    safety: Path | None = None
    if backup.target.exists():
        safety = copy_backup(backup.target)
    RawSave(bytearray(backup.path.read_bytes())).save(
        backup.target,
        backup=False,
    )
    return safety


def delete_backup(backup: BackupEntry) -> None:
    if not _recognized(backup):
        raise ValueError(f"{backup.path} is not a backup of {backup.target}")
    backup.path.unlink()


def validate_backup(backup: BackupEntry) -> BackupCheck:
    try:
        save = DecryptedSave.auto_open(backup.path)
    except Exception as exc:
        return BackupCheck(False, f"Could not read backup: {exc}")
    if not save.hash_validate():
        return BackupCheck(False, "Backup hash is invalid")
    return BackupCheck(True, f"Valid save ({len(save.data)} bytes)")
