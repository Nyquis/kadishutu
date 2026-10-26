import os
from pathlib import Path

import pytest

from kadishutu.core.shared import file_handling
from kadishutu.core.shared.file_handling import (
    DecryptedSave,
    EncryptedSave,
    SaveFormatError,
)


def make_decrypted_save(size: int = 0x100) -> DecryptedSave:
    data = bytearray(size)
    data[0x40:0x44] = b"GVAS"
    save = DecryptedSave(data)
    save.hash_update()
    return save


def test_auto_open_rejects_empty_file(tmp_path: Path):
    path = tmp_path / "save.sav"
    path.write_bytes(b"")

    with pytest.raises(SaveFormatError, match="empty"):
        DecryptedSave.auto_open(path)


def test_open_rejects_empty_file(tmp_path: Path):
    path = tmp_path / "save.sav"
    path.write_bytes(b"")

    with pytest.raises(SaveFormatError, match="empty"):
        DecryptedSave.open(path)


def test_auto_open_rejects_encrypted_length_not_block_aligned(tmp_path: Path):
    path = tmp_path / "save.sav"
    path.write_bytes(b"\x01" * 33)

    with pytest.raises(SaveFormatError, match="multiple of 16"):
        DecryptedSave.auto_open(path)


def test_decrypt_rejects_unaligned_data():
    with pytest.raises(SaveFormatError, match="multiple of 16"):
        EncryptedSave(bytearray(b"\x01" * 5)).decrypt()


def test_auto_open_rejects_oversized_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(file_handling, "MAX_SAVE_SIZE", 64)
    path = tmp_path / "save.sav"
    make_decrypted_save(size=0x100).save(path, backup=False)

    with pytest.raises(SaveFormatError, match="too large"):
        DecryptedSave.auto_open(path)


def test_garbage_encrypted_file_opens_but_fails_hash_check(tmp_path: Path):
    path = tmp_path / "save.sav"
    path.write_bytes(os.urandom(0x100))

    save = DecryptedSave.auto_open(path)

    assert not save.hash_validate()


def test_failed_backup_copy_leaves_original_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "save.sav"
    path.write_bytes(b"original save")

    def fail_copy(src, dst, *args, **kwargs):
        raise OSError("copy failed")

    monkeypatch.setattr(file_handling.shutil, "copy2", fail_copy)

    with pytest.raises(OSError, match="copy failed"):
        DecryptedSave(bytearray(b"new save")).save(path)

    assert path.read_bytes() == b"original save"
    assert not list(tmp_path.glob("*.bak"))
    assert not list(tmp_path.glob("*.tmp"))


def test_failed_fsync_cleans_up_temp_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "save.sav"
    path.write_bytes(b"original save")

    def fail_fsync(fd):
        raise OSError("fsync failed")

    monkeypatch.setattr(file_handling.os, "fsync", fail_fsync)

    with pytest.raises(OSError, match="fsync failed"):
        DecryptedSave(bytearray(b"new save")).save(path, backup=False)

    assert path.read_bytes() == b"original save"
    assert not list(tmp_path.glob("*.tmp"))


def test_save_finished_failed_encrypt_leaves_original_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "save.sav"
    path.write_bytes(b"original save")
    save = make_decrypted_save()

    def fail_encrypt(data):
        raise RuntimeError("encrypt failed")

    monkeypatch.setattr(file_handling, "encrypt", fail_encrypt)

    with pytest.raises(RuntimeError, match="encrypt failed"):
        save.save_finished(path)

    assert path.read_bytes() == b"original save"
    assert not list(tmp_path.glob("*.tmp"))
