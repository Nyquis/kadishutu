"""Build a standalone executable with PyInstaller and archive it.

This replaces the ``poetry-pyinstaller-plugin`` setup. Run it with
``pixi run -e dev build`` (or ``python src/build.py`` inside the dev
environment).
"""
import os
import platform
import subprocess
import sys
import tomllib
from pathlib import Path
from tarfile import TarFile, TarInfo
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
TOOL_NAME = "pyinstaller-archiver"
NAME = "kadishutu"

PLATFORM_NAMES = {
    "Windows": "windows",
    "Linux": "linux",
    "Darwin": "macos",
}


def platform_name() -> str:
    return PLATFORM_NAMES.get(platform.system(), platform.system().lower())


def short_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def build() -> Path:
    dist_path = ROOT / "dist" / "pyinstaller" / platform_name()
    work_path = ROOT / "build" / "pyinstaller"

    data_sep = os.pathsep
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name", NAME,
        "--distpath", str(dist_path),
        "--workpath", str(work_path),
        "--specpath", str(work_path),
        "--runtime-hook", str(ROOT / "src" / "pyinstaller_runtime.py"),
        "--add-data",
        f"{ROOT / 'src' / 'kadishutu' / 'data' / 'tables'}{data_sep}"
        f"{NAME}/data/tables",
        "--add-data", f"{ROOT / 'README.md'}{data_sep}.",
        "--add-data", f"{ROOT / 'LICENSE'}{data_sep}.",
        "--add-data", f"{ROOT / 'docs'}{data_sep}docs",
        "--add-data", f"{ROOT / 'examples'}{data_sep}examples",
        str(ROOT / "src" / "kadishutu" / "__main__.py"),
    ]
    print("Running:", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)
    return dist_path / NAME


def tar_anonymize(info: TarInfo) -> TarInfo | None:
    info.uid = 1000
    info.uname = "build"
    info.gid = 1000
    info.gname = "build"
    return info


def zip_files(source: Path, target: Path):
    with ZipFile(target, "w", ZIP_DEFLATED) as ark:
        for file in source.rglob("*"):
            ark.write(file, file.relative_to(source))


def xz_files(source: Path, target: Path):
    with TarFile.open(target, "w:xz") as ark:
        for file in source.glob("*"):
            ark.add(file, file.relative_to(source), filter=tar_anonymize)


def sevenz_files(source: Path, target: Path):
    try:
        if target.exists():
            target.unlink()
        subprocess.run(["7z", "a", str(target), "*"], cwd=source, check=True)
    except Exception as e:
        # 7z is optional; don't fail the whole build if it is missing.
        print("Archiving failed for 7z:", repr(e))


def archive(source: Path, config: dict) -> None:
    target_dir = source.parent
    name = config["archive_name"].format(
        name=NAME,
        platform=platform_name(),
        commit=short_commit(),
    )
    formats = config["formats"][platform_name()]
    for fmt in formats:
        if fmt == "zip":
            compressor, extension = zip_files, ".zip"
        elif fmt == "xz":
            compressor, extension = xz_files, ".tar.xz"
        elif fmt == "7z":
            compressor, extension = sevenz_files, ".7z"
        else:
            raise ValueError(f"Invalid archive format: {fmt}")
        target = target_dir / (name + extension)
        print("Archiving:", target)
        compressor(source, target)


def main() -> None:
    with PYPROJECT.open("rb") as file:
        config = tomllib.load(file)["tool"][TOOL_NAME]
    archive(build(), config)


if __name__ == "__main__":
    main()
