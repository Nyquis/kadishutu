import importlib.util
import os
from pathlib import Path

import pytest

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


def make_app_tree(tmp_path: Path) -> Path:
    app = tmp_path / BUILD.NAME
    dist_info = app / "_internal" / "kadishutu-0.2.0.dist-info"
    examples = app / "_internal" / "examples"
    cache = examples / "__pycache__"
    cache.mkdir(parents=True)
    dist_info.mkdir(parents=True)

    (dist_info / "METADATA").write_text("Name: kadishutu\n", encoding="utf-8")
    (dist_info / "direct_url.json").write_text(
        '{"url":"file:///home/build/kadishutu","dir_info":{"editable":true}}',
        encoding="utf-8",
    )
    (dist_info / "INSTALLER").write_text("pixi\n", encoding="utf-8")
    (examples / "keep.py").write_text("print('hi')\n", encoding="utf-8")
    (cache / "keep.cpython-313.pyc").write_bytes(b"cache")
    (examples / "stray.pyc").write_bytes(b"stray")
    return app


def test_scrub_removes_install_metadata_and_caches(tmp_path: Path):
    app = make_app_tree(tmp_path)

    BUILD.scrub_metadata(app)

    assert (app / "_internal" / "kadishutu-0.2.0.dist-info" / "METADATA").exists()
    assert not (app / "_internal" / "kadishutu-0.2.0.dist-info" / "direct_url.json").exists()
    assert not (app / "_internal" / "kadishutu-0.2.0.dist-info" / "INSTALLER").exists()
    assert not (app / "_internal" / "examples" / "__pycache__").exists()
    assert not (app / "_internal" / "examples" / "stray.pyc").exists()
    assert (app / "_internal" / "examples" / "keep.py").exists()


def test_scrub_is_idempotent_when_clean(tmp_path: Path):
    app = make_app_tree(tmp_path)

    BUILD.scrub_metadata(app)
    BUILD.scrub_metadata(app)

    assert BUILD.find_leaks(app) == []


def test_find_leaks_reports_build_host_path(tmp_path: Path):
    app = make_app_tree(tmp_path)
    BUILD.scrub_metadata(app)
    leaky = app / "_internal" / "leaky.txt"
    leaky.write_text(f"built in {BUILD.ROOT}", encoding="utf-8")

    problems = BUILD.find_leaks(app)

    assert any("leaky.txt" in problem for problem in problems)


def test_find_leaks_reports_surviving_metadata(tmp_path: Path):
    app = make_app_tree(tmp_path)

    problems = BUILD.find_leaks(app)

    assert any("direct_url.json" in problem for problem in problems)
    assert any("__pycache__" in problem for problem in problems)


def test_assert_no_leaks_fails_the_build(tmp_path: Path):
    app = make_app_tree(tmp_path)

    with pytest.raises(SystemExit):
        BUILD.assert_no_leaks(app)


def test_assert_no_leaks_accepts_scrubbed_tree(tmp_path: Path):
    app = make_app_tree(tmp_path)

    BUILD.scrub_metadata(app)
    BUILD.assert_no_leaks(app)


def metadata(author: str = "Nyquis") -> dict:
    return {
        "authors": [{"name": author}],
        "license": "Apache-2.0",
        "description": "A save editor.",
    }


def workspace(author: str = "Nyquis") -> dict:
    return {
        "authors": [author],
        "license": "Apache-2.0",
        "description": "A save editor.",
    }


def test_workspace_metadata_repository_is_consistent():
    BUILD.load_versions()


def test_workspace_metadata_accepts_matching_values():
    BUILD.check_workspace_metadata(metadata(), workspace())


def test_workspace_metadata_rejects_author_drift():
    with pytest.raises(SystemExit, match="authors mismatch"):
        BUILD.check_workspace_metadata(metadata(), workspace("fnrir"))


def test_workspace_metadata_rejects_license_drift():
    drifted = workspace()
    drifted["license"] = "MIT"
    with pytest.raises(SystemExit, match="license mismatch"):
        BUILD.check_workspace_metadata(metadata(), drifted)


def test_workspace_metadata_rejects_description_drift():
    drifted = workspace()
    drifted["description"] = "Something else."
    with pytest.raises(SystemExit, match="description mismatch"):
        BUILD.check_workspace_metadata(metadata(), drifted)


def test_check_version_tag_accepts_matching_tag(capsys):
    BUILD.check_version_tag("v0.2.0", "0.2.0")

    assert "matches version 0.2.0" in capsys.readouterr().out


def test_check_version_tag_rejects_other_tag():
    with pytest.raises(SystemExit, match="does not match"):
        BUILD.check_version_tag("v0.2.1", "0.2.0")


def test_check_version_tag_rejects_missing_prefix():
    with pytest.raises(SystemExit, match="does not match"):
        BUILD.check_version_tag("0.2.0", "0.2.0")


def test_dirty_paths_reports_changes(monkeypatch):
    monkeypatch.setattr(
        BUILD, "git_lines", lambda args: [" M README.md", "?? new.txt"],
    )

    assert BUILD.dirty_paths() == [" M README.md", "?? new.txt"]


def test_dirty_paths_empty_when_clean(monkeypatch):
    monkeypatch.setattr(BUILD, "git_lines", lambda args: [])

    assert BUILD.dirty_paths() == []


def test_dirty_paths_tolerates_missing_git(monkeypatch):
    monkeypatch.setattr(BUILD, "git_lines", lambda args: None)

    assert BUILD.dirty_paths() == []


def test_check_clean_tree_refuses_dirty_worktree(monkeypatch):
    monkeypatch.setattr(BUILD, "dirty_paths", lambda: [" M README.md"])

    with pytest.raises(SystemExit, match="allow-dirty"):
        BUILD.check_clean_tree()


def test_check_clean_tree_allows_clean_worktree(monkeypatch):
    monkeypatch.setattr(BUILD, "dirty_paths", lambda: [])

    BUILD.check_clean_tree()
