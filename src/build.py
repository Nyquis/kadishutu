"""Build the standalone PyInstaller release and archive it.

Run it with ``pixi run -e dev build`` (or ``python src/build.py`` inside the
dev environment).

The build excludes the Qt modules the widgets-only GUI never imports, prunes
the leftover DLLs/plugins/translations, scrubs install metadata that would
otherwise expose the build host's paths, then zips the result. The build fails
if any local path survives into the packaged tree.
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

# Install metadata written by pip/pixi. direct_url.json points at the editable
# checkout that produced the build, so it ships the local path and user name.
# None of it is read at runtime.
SCRUBBED_NAMES = [
    "direct_url.json",
    "INSTALLER",
]

# Bytecode caches are build noise. The real modules live in the PYZ archive
# inside the executable, so loose .pyc files are never imported.
SCRUBBED_DIRS = [
    "__pycache__",
]


def platform_name() -> str:
    return PLATFORM_NAMES.get(platform.system(), platform.system().lower())


def short_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


ARCHIVE_SUFFIXES = (".tar.xz", ".zip", ".7z")


def archive_base_name(path: Path) -> str | None:
    for suffix in ARCHIVE_SUFFIXES:
        if path.name.endswith(suffix):
            return path.name[:-len(suffix)]
    return None


def prune_archives(
    directory: Path,
    current_base: str,
    keep_previous: int,
) -> None:
    """Keep the current build plus the newest ``keep_previous`` builds."""
    groups: dict[str, list[Path]] = {}
    prefix = f"{NAME}-{platform_name()}-"
    for path in directory.iterdir():
        if not path.is_file() or not path.name.startswith(prefix):
            continue
        base = archive_base_name(path)
        if base is None:
            continue
        groups.setdefault(base, []).append(path)

    previous = [base for base in groups if base != current_base]
    previous.sort(
        key=lambda base: max(p.stat().st_mtime for p in groups[base]),
        reverse=True,
    )
    stale = previous[keep_previous:]
    removed = 0
    for base in stale:
        for path in groups[base]:
            path.unlink()
            removed += 1
    if removed:
        builds = len(stale)
        noun = "build" if builds == 1 else "builds"
        print(f"Pruned {removed} file(s) from {builds} old {noun}.")



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


def scrub_metadata(app_dir: Path) -> None:
    """Remove install metadata and bytecode caches that name the build host.

    This runs even with ``--no-prune``: it is about information leakage, not
    about the download size.
    """
    removed: list[Path] = []
    for name in SCRUBBED_DIRS:
        removed.extend(p for p in app_dir.rglob(name) if p.is_dir())
    for name in SCRUBBED_NAMES:
        removed.extend(p for p in app_dir.rglob(name) if p.is_file())
    removed.extend(
        p for p in app_dir.rglob("*.pyc")
        if p.is_file() and "__pycache__" not in p.parts
    )
    paths = list(dict.fromkeys(removed))
    for path in paths:
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    if paths:
        print(f"Scrubbed {len(paths)} build-metadata path(s)")


def leak_needles() -> list[bytes]:
    """Local paths that must never appear inside a release."""
    home = Path.home()
    candidates = {str(ROOT), ROOT.as_posix(), str(home), home.as_posix()}
    return [item.encode() for item in candidates if len(item) > 3]


def find_leaks(app_dir: Path) -> list[str]:
    """Report build-host paths and install metadata left in ``app_dir``."""
    needles = leak_needles()
    problems: list[str] = []
    for path in sorted(app_dir.rglob("*")):
        rel = path.relative_to(app_dir)
        if path.is_dir():
            if path.name in SCRUBBED_DIRS:
                problems.append(f"{rel} (bytecode cache directory)")
            continue
        if path.name in SCRUBBED_NAMES:
            problems.append(f"{rel} (install metadata)")
        data = path.read_bytes()
        for needle in needles:
            if needle in data:
                problems.append(f"{rel} (contains {needle.decode()})")
    return problems


def assert_no_leaks(app_dir: Path) -> None:
    """Fail the build rather than publish local paths."""
    problems = find_leaks(app_dir)
    if not problems:
        return
    print("Build machine paths leaked into the release:", file=sys.stderr)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    raise SystemExit(
        "Refusing to package a build that exposes local paths. Extend "
        "SCRUBBED_NAMES/SCRUBBED_DIRS or remove the offending file."
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
    scrub_metadata(app_path)
    if prune:
        prune_dist(app_path)
    assert_no_leaks(app_path)
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


def archive(
    source: Path,
    config: dict,
    version: str,
    keep_previous: int,
    prune_old: bool,
) -> list[Path]:
    target_dir = source.parent
    name = config["archive_name"].format(
        name=NAME,
        platform=platform_name(),
        version=version,
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
    if prune_old:
        prune_archives(target_dir, name, keep_previous)
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
    parser.add_argument(
        "--keep-previous", type=int, default=4, metavar="N",
        help="Keep the current build plus this many previous builds "
             "(default: 4)",
    )
    parser.add_argument(
        "--no-archive-prune", dest="archive_prune", action="store_false",
        help="Keep all old build archives",
    )
    return parser.parse_args(argv)


def load_versions() -> tuple[dict, str]:
    with PYPROJECT.open("rb") as file:
        project = tomllib.load(file)
    version = project["project"]["version"]
    with (ROOT / "pixi.toml").open("rb") as file:
        pixi_version = tomllib.load(file)["workspace"]["version"]
    if pixi_version != version:
        raise SystemExit(
            f"Version mismatch: pyproject.toml has {version}, "
            f"pixi.toml has {pixi_version}"
        )
    return project["tool"][TOOL_NAME], version


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.keep_previous < 0:
        raise SystemExit("--keep-previous must be 0 or greater")
    config, version = load_versions()

    app_path = build(upx=args.upx, prune=not args.no_prune)
    targets = archive(
        app_path,
        config,
        version,
        args.keep_previous,
        args.archive_prune,
    )

    print()
    print(f"{'artifact':<32}{'MiB':>8}")
    print(f"{NAME:<32}{mb(tree_size(app_path)):>8}")
    for target in targets:
        print(f"{target.name:<32}{mb(tree_size(target)):>8}")


if __name__ == "__main__":
    main()
