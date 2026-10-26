from argparse import Namespace
from pathlib import Path

import pytest

import kadishutu.editor_cli as editor_cli
from kadishutu.cli import (
    cmd_decrypt,
    cmd_encrypt,
    cmd_inspect,
    cmd_run_script,
    cmd_update_hash,
)
from kadishutu.core.shared.file_handling import (
    DecryptedSave,
    is_save_decrypted,
)


def make_decrypted_save(size: int = 0x100) -> DecryptedSave:
    data = bytearray(size)
    data[0x40:0x44] = b"GVAS"
    save = DecryptedSave(data)
    save.hash_update()
    return save


def test_cmd_decrypt_rejects_decrypted_input(tmp_path: Path):
    path = tmp_path / "save.sav"
    make_decrypted_save().save(path)

    with pytest.raises(ValueError, match="already decrypted"):
        cmd_decrypt(Namespace(source=path, destination=path))


def test_cmd_decrypt_writes_decrypted_file(tmp_path: Path):
    path = tmp_path / "save.sav"
    save = make_decrypted_save()
    save.save_finished(path)

    cmd_decrypt(Namespace(source=path, destination=path))

    assert is_save_decrypted(bytearray(path.read_bytes()))
    assert DecryptedSave.open(path).hash_validate()


def test_cmd_encrypt_rejects_encrypted_input(tmp_path: Path):
    path = tmp_path / "save.sav"
    make_decrypted_save().save_finished(path)

    with pytest.raises(ValueError, match="already encrypted"):
        cmd_encrypt(Namespace(source=path, destination=path, update_hash=False))


def test_cmd_encrypt_writes_encrypted_file_and_backup(tmp_path: Path):
    path = tmp_path / "save.sav"
    save = make_decrypted_save()
    save.save(path)

    cmd_encrypt(Namespace(source=path, destination=path, update_hash=False))

    assert not is_save_decrypted(bytearray(path.read_bytes()))
    assert DecryptedSave.auto_open(path).data == save.data
    assert DecryptedSave.auto_open(path).hash_validate()
    backups = list(tmp_path.glob("save.sav.*.bak"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == bytes(save.data)


def test_cmd_encrypt_invalid_hash_requires_update_flag(tmp_path: Path):
    path = tmp_path / "save.sav"
    save = make_decrypted_save()
    save.data[0x50] ^= 0xFF
    save.save(path)

    with pytest.raises(ValueError, match="hash is not valid"):
        cmd_encrypt(Namespace(source=path, destination=path, update_hash=False))

    cmd_encrypt(Namespace(source=path, destination=path, update_hash=True))

    assert DecryptedSave.auto_open(path).hash_validate()


def test_cmd_update_hash_rejects_encrypted_input(tmp_path: Path):
    path = tmp_path / "save.sav"
    make_decrypted_save().save_finished(path)

    with pytest.raises(ValueError, match="decrypt it first"):
        cmd_update_hash(Namespace(file=path))


def test_cmd_edit_rejects_invalid_hash_without_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "save.sav"
    save = make_decrypted_save()
    save.data[0x50] ^= 0xFF
    save.save(path)
    calls: list[object] = []

    class DummyGameSaveEditor:
        def __init__(self, savefile: DecryptedSave):
            self.savefile = savefile

    monkeypatch.setattr(editor_cli, "GameSaveEditor", DummyGameSaveEditor)

    def edit(_: Namespace, game: object):
        calls.append(game)

    with pytest.raises(ValueError, match="hash is not valid"):
        editor_cli.cmd_edit(Namespace(file=path, func_x=edit, force=False))

    assert calls == []


def test_cmd_edit_force_updates_invalid_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "save.sav"
    save = make_decrypted_save()
    save.data[0x50] ^= 0xFF
    save.save(path)

    class DummyGameSaveEditor:
        def __init__(self, savefile: DecryptedSave):
            self.savefile = savefile

    monkeypatch.setattr(editor_cli, "GameSaveEditor", DummyGameSaveEditor)

    def edit(_: Namespace, game: object):
        pass

    editor_cli.cmd_edit(Namespace(file=path, func_x=edit, force=True))

    assert DecryptedSave.open(path).hash_validate()


def test_cmd_edit_preserves_encryption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "save.sav"
    save = make_decrypted_save()
    save.save_finished(path)

    class DummyGameSaveEditor:
        def __init__(self, savefile: DecryptedSave):
            self.savefile = savefile

    monkeypatch.setattr(editor_cli, "GameSaveEditor", DummyGameSaveEditor)

    def edit(_: Namespace, game: object):
        pass

    editor_cli.cmd_edit(Namespace(file=path, func_x=edit, force=False))

    assert not is_save_decrypted(bytearray(path.read_bytes()))
    assert DecryptedSave.auto_open(path).hash_validate()


def test_cmd_inspect_rejects_invalid_hash(tmp_path: Path):
    path = tmp_path / "save.sav"
    save = make_decrypted_save()
    save.data[0x50] ^= 0xFF
    save.save(path)

    with pytest.raises(ValueError, match="hash is not valid"):
        cmd_inspect(
            Namespace(
                file=path,
                selector=["macca"],
                ignore_hash=False,
            )
        )


def test_cmd_run_script_rejects_invalid_hash(tmp_path: Path):
    path = tmp_path / "save.sav"
    save = make_decrypted_save()
    save.data[0x50] ^= 0xFF
    save.save(path)
    script = tmp_path / "script.py"
    script.write_text("raise RuntimeError('script loaded')\n")

    with pytest.raises(ValueError, match="hash is not valid"):
        cmd_run_script(
            Namespace(
                file=path,
                script=script,
                rest_of_args=[],
                ignore_hash=False,
            )
        )


def test_sys_save_screen_is_read_only():
    pytest.importorskip("PySide6")
    from kadishutu.gui.shared import SaveScreenMixin
    from kadishutu.gui.sys_save import SysSaveEditorScreen

    assert SaveScreenMixin.can_save is True
    assert SysSaveEditorScreen.can_save is False
