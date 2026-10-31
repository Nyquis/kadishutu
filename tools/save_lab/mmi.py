from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from kadishutu.tools.tbbreader import Tbcr


def load_mmi_tbcr(path: Path) -> Tbcr:
    """Read the TBCR payload from a CUE4Parse JSON export of an MMIAsset."""
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list) or not data:
        raise ValueError(f"{path} is not a CUE4Parse asset export")
    properties = data[0].get("Properties")
    if not isinstance(properties, dict):
        raise ValueError(f"{path} has no asset properties")
    raw = properties.get("MyFmtData")
    if not isinstance(raw, list):
        raise ValueError(f"{path} has no MyFmtData payload")
    return Tbcr.open(io.BytesIO(bytes(raw)))


def single_table(path: Path, *, row_size: int | None = None) -> Any:
    tcx = load_mmi_tbcr(path)
    if len(tcx.tables) != 1:
        raise ValueError(
            f"{path} contains {len(tcx.tables)} tables, expected 1"
        )
    table = tcx.tables[0]
    if row_size is not None and table.row_size != row_size:
        raise ValueError(
            f"{path} row size is {table.row_size}, expected {row_size}"
        )
    return table


def write_entries(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["["]
    for index, entry in enumerate(entries):
        suffix = "," if index != len(entries) - 1 else ""
        lines.append("  " + json.dumps(entry, ensure_ascii=False) + suffix)
    lines.append("]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
