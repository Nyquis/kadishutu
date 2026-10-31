from pathlib import Path

from test_save_lab_gvas import make_gvas_header

from tools.save_lab.__main__ import main
from tools.save_lab.gvas import DEFAULT_GVAS_OFFSET


def write_save(path: Path, payload: bytes = b"\0" * 0x20) -> Path:
    data, _ = make_gvas_header()
    path.write_bytes(data + payload)
    return path


def test_cli_gvas_prints_class(tmp_path: Path, capsys):
    path = write_save(tmp_path / "save.dec")

    assert main(["gvas", str(path)]) == 0

    output = capsys.readouterr().out
    assert "class_name: 'SaveObject'" in output
    assert f"GVAS offset: 0x{DEFAULT_GVAS_OFFSET:x}" in output


def test_cli_diff_reports_change(tmp_path: Path, capsys):
    before = write_save(tmp_path / "before.dec", b"\0" * 0x20)
    after = write_save(tmp_path / "after.dec", b"\x01" + b"\0" * 0x1F)

    assert main(["diff", str(before), str(after)]) == 0

    output = capsys.readouterr().out
    assert "1 changed region" in output
    assert "0x000400" in output


def test_cli_validate_rejects_bad_hash(tmp_path: Path, capsys):
    path = write_save(tmp_path / "save.dec")

    assert main(["validate", str(path)]) == 1

    output = capsys.readouterr().out
    assert "FAIL hash" in output
