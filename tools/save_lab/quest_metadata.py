from __future__ import annotations

import argparse
import struct
from pathlib import Path

from .mmi import single_table, write_entries

DEFAULT_TABLE = Path(
    "lab/dumps/game-tables-json/Project/Content/Blueprints/Gamedata/"
    "BinTable/Mission/MissionTable.json"
)
DEFAULT_OUTPUT = Path("src/kadishutu/data/tables/quests.generated.json")

QUEST_ROW_SIZE = 0x174


def build_entries(table) -> list[dict]:
    entries = []
    for row in table.rows:
        quest_id = struct.unpack_from("<H", row, 0)[0]
        entries.append({"id": quest_id})
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate quest metadata from MissionTable.",
    )
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    table = single_table(args.table, row_size=QUEST_ROW_SIZE)
    entries = build_entries(table)
    write_entries(args.output, entries)
    print(f"Wrote {len(entries)} quests to {args.output}")


if __name__ == "__main__":
    main()
