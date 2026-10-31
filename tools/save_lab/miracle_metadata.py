from __future__ import annotations

import argparse
import struct
from pathlib import Path

from .mmi import single_table, write_entries

DEFAULT_TABLE = Path(
    "lab/dumps/game-tables-json/Project/Content/Blueprints/Gamedata/"
    "BinTable/GodParameter/Table/GodParameterDataTable.json"
)
DEFAULT_OUTPUT = Path("src/kadishutu/data/tables/miracles.generated.json")

MIRACLE_FORMAT = struct.Struct("<HIB5sH?5s")


def build_entries(table) -> list[dict]:
    entries = []
    for row in table.rows:
        (
            miracle_id,
            order_id,
            category,
            _pad1,
            cost,
            toggleable,
            _pad2,
        ) = MIRACLE_FORMAT.unpack(row)
        entries.append({
            "id": miracle_id,
            "order_id": order_id,
            "category": category,
            "cost": cost,
            "toggleable": bool(toggleable),
        })
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate miracle metadata from GodParameterDataTable.",
    )
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    table = single_table(args.table, row_size=MIRACLE_FORMAT.size)
    entries = build_entries(table)
    write_entries(args.output, entries)
    print(f"Wrote {len(entries)} miracles to {args.output}")


if __name__ == "__main__":
    main()
