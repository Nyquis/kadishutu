import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "kadishutu_build",
    ROOT / "src" / "build.py",
)
assert SPEC is not None
assert SPEC.loader is not None
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


def archive_name(base: str, suffix: str = ".zip") -> str:
    return f"{base}{suffix}"


def touch(path: Path, mtime: int) -> None:
    path.write_bytes(b"x")
    os.utime(path, (mtime, mtime))


def make_base(version: str, commit: str) -> str:
    return f"{BUILD.NAME}-{BUILD.platform_name()}-v{version}-{commit}"


def test_archive_base_name_handles_all_formats():
    assert BUILD.archive_base_name(Path("foo.zip")) == "foo"
    assert BUILD.archive_base_name(Path("foo.tar.xz")) == "foo"
    assert BUILD.archive_base_name(Path("foo.7z")) == "foo"
    assert BUILD.archive_base_name(Path("foo.txt")) is None


def test_prune_keeps_current_plus_four_previous(tmp_path: Path):
    bases = [make_base("0.2.0", f"{index:07d}") for index in range(7)]
    for index, base in enumerate(bases):
        touch(tmp_path / archive_name(base), 1000 + index)
    current = make_base("0.2.0", "current")
    touch(tmp_path / archive_name(current), 2000)

    BUILD.prune_archives(tmp_path, current, 4)

    remaining = sorted(path.name for path in tmp_path.iterdir())
    assert len(remaining) == 5
    assert archive_name(current) in remaining
    assert archive_name(bases[-1]) in remaining
    assert archive_name(bases[-4]) in remaining
    assert archive_name(bases[0]) not in remaining
    assert archive_name(bases[1]) not in remaining
    assert archive_name(bases[2]) not in remaining


def test_prune_counts_multiple_formats_as_one_build(tmp_path: Path):
    current = make_base("0.2.0", "current")
    touch(tmp_path / archive_name(current), 2000)
    old = make_base("0.2.0", "old")
    touch(tmp_path / archive_name(old, ".zip"), 1000)
    touch(tmp_path / archive_name(old, ".tar.xz"), 1001)
    touch(tmp_path / archive_name(old, ".7z"), 1002)

    BUILD.prune_archives(tmp_path, current, 0)

    assert [path.name for path in tmp_path.iterdir()] == [
        archive_name(current),
    ]


def test_prune_zero_keeps_only_current(tmp_path: Path):
    current = make_base("0.2.0", "current")
    touch(tmp_path / archive_name(current), 2000)
    old = make_base("0.2.0", "old")
    touch(tmp_path / archive_name(old), 1000)

    BUILD.prune_archives(tmp_path, current, 0)

    assert [path.name for path in tmp_path.iterdir()] == [
        archive_name(current),
    ]


def test_prune_ignores_other_platforms(tmp_path: Path):
    current = make_base("0.2.0", "current")
    touch(tmp_path / archive_name(current), 2000)
    other = f"{BUILD.NAME}-other-platform-v0.2.0-old.zip"
    touch(tmp_path / other, 1000)

    BUILD.prune_archives(tmp_path, current, 0)

    assert (tmp_path / other).exists()
