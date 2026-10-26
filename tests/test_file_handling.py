from pathlib import Path

import pytest

from kadishutu.core.shared import file_handling
from kadishutu.core.shared.file_handling import (
    DecryptedSave,
    SaveVerificationError,
    is_save_decrypted,
)


def make_decrypted_save(size: int = 0x100) -> DecryptedSave:
    data = bytearray(size)
    data[0x40:0x44] = b"GVAS"
    save = DecryptedSave(data)
    save.hash_update()
    return save


def test_encrypted_save_round_trip(tmp_path: Path):
    save = make_decrypted_save()
    path = tmp_path / "save.sav"

    backup = save.save_finished(path)

    assert backup is None
    assert not is_save_decrypted(bytearray(path.read_bytes()))
    reopened = DecryptedSave.auto_open(path)
    assert reopened.data == save.data
    assert reopened.hash_validate()


def test_save_finished_creates_backup(tmp_path: Path):
    path = tmp_path / "save.sav"
    path.write_bytes(b"original save")

    backup = make_decrypted_save().save_finished(path)

    assert backup is not None
    assert backup.read_bytes() == b"original save"
    assert DecryptedSave.auto_open(path).hash_validate()


def test_save_can_skip_backup(tmp_path: Path):
    path = tmp_path / "save.sav"
    path.write_bytes(b"old")

    backup = DecryptedSave(bytearray(b"new")).save(path, backup=False)

    assert backup is None
    assert path.read_bytes() == b"new"
    assert not list(tmp_path.glob("*.bak"))


def test_failed_replace_leaves_original_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "save.sav"
    path.write_bytes(b"original save")

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(file_handling, "_replace_file", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        DecryptedSave(bytearray(b"new save")).save(path)

    assert path.read_bytes() == b"original save"
    assert not list(tmp_path.glob("*.tmp"))


def test_failed_verification_restores_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "save.sav"
    path.write_bytes(b"original save")
    original_replace = file_handling._replace_file
    first_replace = True

    def corrupt_replace(source: Path, destination: Path) -> None:
        nonlocal first_replace
        if first_replace:
            first_replace = False
            destination.write_bytes(b"corrupt save")
            source.unlink()
            return
        original_replace(source, destination)

    monkeypatch.setattr(file_handling, "_replace_file", corrupt_replace)

    with pytest.raises(SaveVerificationError, match="verification failed"):
        DecryptedSave(bytearray(b"new save")).save(path)

    assert path.read_bytes() == b"original save"
    assert list(tmp_path.glob("*.bak"))


def test_hash_validation_detects_changes():
    save = make_decrypted_save()
    assert save.hash_validate()

    save.data[0x50] ^= 0xFF

    assert not save.hash_validate()


def test_save_finished_updates_hash(tmp_path: Path):
    save = make_decrypted_save()
    save.data[0x50] ^= 0xFF
    assert not save.hash_validate()

    path = tmp_path / "save.sav"
    save.save_finished(path)

    assert DecryptedSave.auto_open(path).hash_validate()


def test_save_finished_detects_round_trip_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "save.sav"
    save = make_decrypted_save()

    class WrongRoundTrip:
        data = bytearray(b"wrong")

        def hash_validate(self) -> bool:
            return True

    monkeypatch.setattr(
        DecryptedSave,
        "auto_open",
        classmethod(lambda cls, path: WrongRoundTrip()),
    )

    with pytest.raises(SaveVerificationError, match="round-trip"):
        save.save_finished(path)


def test_save_finished_restores_backup_on_verification_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "save.sav"
    path.write_bytes(b"original save")
    save = make_decrypted_save()

    class WrongRoundTrip:
        data = bytearray(b"wrong")

        def hash_validate(self) -> bool:
            return True

    monkeypatch.setattr(
        DecryptedSave,
        "auto_open",
        classmethod(lambda cls, path: WrongRoundTrip()),
    )

    with pytest.raises(SaveVerificationError, match="round-trip"):
        save.save_finished(path)

    assert path.read_bytes() == b"original save"


def test_save_finished_detects_hash_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "save.sav"
    save = make_decrypted_save()

    class InvalidHashSave:
        data = save.data

        def hash_validate(self) -> bool:
            return False

    monkeypatch.setattr(
        DecryptedSave,
        "auto_open",
        classmethod(lambda cls, path: InvalidHashSave()),
    )

    with pytest.raises(SaveVerificationError, match="hash verification failed"):
        save.save_finished(path)
