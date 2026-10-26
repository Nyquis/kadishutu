import contextlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
from pathlib import Path
from typing import Self

from .encryption import decrypt, encrypt


class SaveVerificationError(RuntimeError):
    pass


class SaveFormatError(ValueError):
    pass


AES_BLOCK_SIZE = 16
MAX_SAVE_SIZE = 16 * 1024 * 1024


def _read_save_bytes(path: Path) -> bytearray:
    size = path.stat().st_size
    if size == 0:
        raise SaveFormatError(f"The save file {path} is empty.")
    if size > MAX_SAVE_SIZE:
        raise SaveFormatError(
            f"The save file {path} is too large ({size} bytes)."
        )
    with open(path, "rb") as file:
        return bytearray(file.read())


def is_save_decrypted(data: bytearray) -> bool:
    return data[0x40:0x44] == b"GVAS"


def _backup_path(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    candidate = path.with_name(f"{path.name}.{stamp}.bak")
    suffix = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.{stamp}.{suffix}.bak")
        suffix += 1
    return candidate


def _replace_file(source: Path, destination: Path) -> None:
    os.replace(source, destination)


def _backup_note(backup_path: Path | None) -> str:
    if backup_path is None:
        return ""
    return f" Backup: {backup_path}"


def _write_atomic(path: Path, data: bytes, *, backup: bool = True) -> Path | None:
    path = Path(path)
    backup_path: Path | None = None
    if backup and path.exists():
        backup_path = _backup_path(path)
        shutil.copy2(path, backup_path)

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        if temp_path.read_bytes() != data:
            raise SaveVerificationError(
                f"Temporary save file verification failed for {path}"
                f"{_backup_note(backup_path)}"
            )
        _replace_file(temp_path, path)
    except BaseException:
        with contextlib.suppress(OSError):
            temp_path.unlink()
        raise

    try:
        written_data = path.read_bytes()
    except OSError as exc:
        _restore_backup(path, backup_path)
        raise SaveVerificationError(
            f"Could not verify the saved file at {path}."
            f"{_backup_note(backup_path)}"
        ) from exc

    if written_data != data:
        _restore_backup(path, backup_path)
        raise SaveVerificationError(
            f"Saved file verification failed for {path}."
            f"{_backup_note(backup_path)}"
        )

    return backup_path


def _restore_backup(path: Path, backup_path: Path | None) -> None:
    if backup_path is None:
        return
    with contextlib.suppress(OSError, SaveVerificationError):
        _write_atomic(path, backup_path.read_bytes(), backup=False)


@dataclass(repr=False)
class RawSave:
    data: bytearray

    def save(self, path: Path, *, backup: bool = True) -> Path | None:
        return _write_atomic(path, bytes(self.data), backup=backup)

    def is_save_decrypted(self) -> bool:
        return is_save_decrypted(self.data)


class EncryptedSave(RawSave):
    @classmethod
    def open(cls, path: Path) -> Self:
        return cls(_read_save_bytes(path))

    def decrypt(self) -> "DecryptedSave":
        assert not self.is_save_decrypted(), "Save not encrypted"
        if len(self.data) % AES_BLOCK_SIZE:
            raise SaveFormatError(
                f"Encrypted save length {len(self.data)} is not a multiple "
                f"of {AES_BLOCK_SIZE} bytes."
            )
        return DecryptedSave(bytearray(decrypt(self.data)))


class DecryptedSave(RawSave):
    @classmethod
    def open(cls, path: Path) -> Self:
        return cls(_read_save_bytes(path))

    @classmethod
    def auto_open(cls, path: Path) -> "DecryptedSave":
        data = _read_save_bytes(path)
        if not is_save_decrypted(data):
            return EncryptedSave(data).decrypt()
        else:
            return cls(data)

    def encrypt(self) -> EncryptedSave:
        assert self.is_save_decrypted(), "Save not decrypted"
        return EncryptedSave(bytearray(encrypt(self.data)))

    def hash_calculate(self):
        return sha1(self.data[0x40:])

    def hash_validate(self) -> bool:
        included_hash = self.data[:20]
        calculated_hash = self.hash_calculate()
        return included_hash == calculated_hash.digest()

    def hash_update(self):
        new_hash = self.hash_calculate()
        data = self.data
        self.data = bytearray(new_hash.digest()) + self.data[20:]
        assert len(data) == len(self.data)

    def save_finished(self, path: Path, *, backup: bool = True) -> Path | None:
        self.hash_update()
        backup_path = self.encrypt().save(path, backup=backup)
        reopened = DecryptedSave.auto_open(path)
        if reopened.data != self.data:
            _restore_backup(path, backup_path)
            raise SaveVerificationError(
                f"Encrypted save round-trip verification failed for {path}."
                f"{_backup_note(backup_path)}"
            )
        if not reopened.hash_validate():
            _restore_backup(path, backup_path)
            raise SaveVerificationError(
                f"Saved hash verification failed for {path}."
                f"{_backup_note(backup_path)}"
            )
        return backup_path
