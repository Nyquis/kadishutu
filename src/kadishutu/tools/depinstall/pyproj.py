import os
import re
import tomllib
from functools import cache
from importlib.metadata import PackageNotFoundError, metadata
from pathlib import Path
from typing import Any

PYPROJ = "pyproject.toml"
THIS_DIR = Path(os.path.realpath(__file__)).parent
PYPROJECT = THIS_DIR / PYPROJ
OTHER_PYPROJECT = THIS_DIR / "../../../.." / PYPROJ


def _read_pyproject(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def _groups_from_metadata() -> dict[str, list[str]]:
    """Read optional dependencies from the installed distribution metadata.

    This is the fallback for installed builds, where the project's
    ``pyproject.toml`` is not part of the wheel.
    """
    try:
        dist_metadata = metadata("kadishutu")
    except PackageNotFoundError:
        return {}
    groups: dict[str, list[str]] = {}
    for requirement in dist_metadata.get_all("Requires-Dist") or []:
        match = re.match(
            r"^(?P<req>[^;]+);\s*extra\s*==\s*[\"'](?P<extra>[^\"']+)[\"']",
            requirement,
        )
        if not match:
            continue
        groups.setdefault(match["extra"], []).append(match["req"].strip())
    return groups


@cache
def get_groups() -> dict[str, list[str]]:
    for path in (OTHER_PYPROJECT, PYPROJECT):
        try:
            return _read_pyproject(path)["project"]["optional-dependencies"]
        except (FileNotFoundError, KeyError):
            continue
    return _groups_from_metadata()


def get_opt_depends(group: str) -> list[str]:
    try:
        return get_groups()[group]
    except KeyError:
        raise KeyError(f"Unknown optional dependency group: {group}") from None
