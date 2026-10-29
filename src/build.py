"""Build the standalone PyInstaller release and archive it.

Run it with ``pixi run -e dev build`` (or ``python src/build.py`` inside the
dev environment).

The build excludes the Qt modules the widgets-only GUI never imports, prunes
the leftover DLLs/plugins/translations, then zips the result.
"""
import argparse
import os
import platform
import shutil
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

# The GUI only imports PySide6.QtCore, QtGui and QtWidgets, and Pillow handles
# the TGA icons. Excluding the rest takes the release download from ~50 MB to
# ~30 MB. Keep in sync with the prune lists below.
EXCLUDED_MODULES = [
    "PySide6.QtDBus",
    "PySide6.QtNetwork",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "PySide6.QtTest",
    "PySide6.QtXml",
    "PIL.AvifImagePlugin",
    "ssl",
    "tkinter",
]

# Files and directories PyInstaller copies in even when nothing imports them.
PRUNED_FILES = [
    # Qt libraries for the QML, PDF, network and SVG stacks.
    "Qt6Network.dll",
    "Qt6Pdf.dll",
    "Qt6PdfWidgets.dll",
    "Qt6Qml.dll",
    "Qt6QmlCompiler.dll",
    "Qt6QmlMeta.dll",
    "Qt6QmlModels.dll",
    "Qt6QmlWorkerScript.dll",
    "Qt6Quick.dll",
    "Qt6QuickControls2.dll",
    "Qt6QuickDialogs2.dll",
    "Qt6QuickLayouts.dll",
    "Qt6QuickTemplates2.dll",
    "Qt6Svg.dll",
    "Qt6SvgWidgets.dll",
    "Qt6VirtualKeyboard.dll",
    # Qt plugins for formats and transports the app never uses.
    "qcertonlybackend.dll",
    "qdirect2d.dll",
    "qgif.dll",
    "qicns.dll",
    "qnetworklistmanager.dll",
    "qopensslbackend.dll",
    "qpdf.dll",
    "qschannelbackend.dll",
    "qsvg.dll",
    "qsvgicon.dll",
    "qtga.dll",
    "qtiff.dll",
    "qwebp.dll",
    # OpenSSL is only reachable through ssl/socket, which nothing imports.
    "libcrypto-3-x64.dll",
    "libssl-3-x64.dll",
    "_ssl.pyd",
    # Pillow's AVIF codec; only TGA loading is used.
    "_avif.pyd",
]

PRUNED_DIRS = [
    "_tcl_data",
    "_tk_data",
    "networkinformation",
    "platforminputcontexts",
    "tcl8",
    "tls",
    "translations",
]

# Extra globs, matched with rglob relative to the app directory.
PRUNED_GLOBS = [
    "_avif*.pyd",
]


def platform_name() -> str:
    return PLATFORM_NAMES.get(platform.system(), platform.system().lower())


def short_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def tree_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def mb(num_bytes: int) -> float:
    return round(num_bytes / (1024 * 1024), 1)


def prune_dist(app_dir: Path) -> None:
    before = tree_size(app_dir)
    removed = 0

    candidates: list[Path] = []
    for name in PRUNED_FILES:
        candidates.extend(app_dir.rglob(name))
    for name in PRUNED_DIRS:
        candidates.extend(p for p in app_dir.rglob(name) if p.is_dir())
    for pattern in PRUNED_GLOBS:
        candidates.extend(app_dir.rglob(pattern))

    for path in dict.fromkeys(candidates):
        if not path.exists():
            continue
        size = tree_size(path)
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        removed += size

    print(
        f"Pruned {mb(removed)} MiB of unused payload "
        f"({mb(before)} MiB -> {mb(tree_size(app_dir))} MiB)"
    )


def pyinstaller_args(upx: bool) -> list[str]:
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
        "--add-data", f"{ROOT / 'docs'}{data_sep}docs",
        "--add-data", f"{ROOT / 'examples'}{data_sep}examples",
    ]
    # UPX shrinks both the folder and the zipped release: its LZMA packing
    # beats what deflate can do to the raw Qt binaries. Opt out with --no-upx
    # if it triggers antivirus false positives (it also costs ~0.3s startup).
    if not upx:
        args.append("--noupx")
    for module in EXCLUDED_MODULES:
        args += ["--exclude-module", module]
    args.append(str(ROOT / "src" / "kadishutu" / "__main__.py"))
    return args


def copy_licenses(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "LICENSE", target)
    shutil.copy2(ROOT / "NOTICE", target)
    shutil.copytree(ROOT / "LICENSES", target / "LICENSES", dirs_exist_ok=True)


def build(upx: bool = True, prune: bool = True) -> Path:
    print("Running:", " ".join(pyinstaller_args(upx)))
    subprocess.run(pyinstaller_args(upx), cwd=ROOT, check=True)

    app_path = ROOT / "dist" / "pyinstaller" / platform_name() / NAME
    copy_licenses(app_path)
    if prune:
        prune_dist(app_path)
    return app_path


def tar_anonymize(info: TarInfo) -> TarInfo | None:
    info.uid = 1000
    info.uname = "build"
    info.gid = 1000
    info.gname = "build"
    return info


def zip_files(source: Path, target: Path):
    with ZipFile(target, "w", ZIP_DEFLATED, compresslevel=9) as ark:
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


def archive(source: Path, config: dict) -> list[Path]:
    target_dir = source.parent
    name = config["archive_name"].format(
        name=NAME,
        platform=platform_name(),
        commit=short_commit(),
    )
    formats = config["formats"][platform_name()]
    targets: list[Path] = []
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
        targets.append(target)
    return targets


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-prune", action="store_true",
        help="Keep the unused Qt/Pillow/tk payload (for comparison builds)",
    )
    parser.add_argument(
        "--no-upx", dest="upx", action="store_false",
        help="Do not compress the payload with UPX (bigger download, faster "
             "startup, fewer antivirus false positives)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    with PYPROJECT.open("rb") as file:
        config = tomllib.load(file)["tool"][TOOL_NAME]

    app_path = build(upx=args.upx, prune=not args.no_prune)
    targets = archive(app_path, config)

    print()
    print(f"{'artifact':<32}{'MiB':>8}")
    print(f"{NAME:<32}{mb(tree_size(app_path)):>8}")
    for target in targets:
        print(f"{target.name:<32}{mb(tree_size(target)):>8}")


if __name__ == "__main__":
    main()
