from __future__ import annotations

import argparse
import struct
from pathlib import Path

from .mmi import load_mmi_tbcr, write_entries

DEFAULT_ITEM_TABLE = Path(
    "lab/dumps/item-tables/Project/Content/Blueprints/Gamedata/"
    "BinTable/Item/ItemTable.json"
)
DEFAULT_OUTPUT = Path("src/kadishutu/data/tables/items.generated.json")

CONSUMABLE_END = 220
ESSENCE_END = 615
RELIC_1_END = 655
KEY_ITEM_END = 855
MAX_ITEM_ID = 895


def category_for(item_id: int) -> tuple[str, str]:
    if 1 <= item_id <= CONSUMABLE_END:
        return "consumable", "consumable"
    if 221 <= item_id <= ESSENCE_END:
        return "essence", "essence"
    if 616 <= item_id <= RELIC_1_END:
        return "relic", "relic_1"
    if 656 <= item_id <= KEY_ITEM_END:
        return "key_item", "key_item"
    if 856 <= item_id <= MAX_ITEM_ID:
        return "relic", "relic_2"
    return "unknown", "unknown"


def load_item_table(path: Path) -> tuple[dict[int, dict], dict[int, dict]]:
    tcx = load_mmi_tbcr(path)
    if len(tcx.tables) < 4:
        raise ValueError(f"Expected at least 4 item tables, got {len(tcx.tables)}")
    consumables = tcx.tables[0]
    key_items = tcx.tables[3]
    if consumables.row_size != 100:
        raise ValueError(
            f"Unexpected consumable row size {consumables.row_size}"
        )
    if key_items.row_size != 16:
        raise ValueError(f"Unexpected key item row size {key_items.row_size}")

    consumable_data: dict[int, dict] = {}
    for row in consumables.rows:
        item_id = struct.unpack_from("<I", row, 16)[0]
        consumable_data[item_id] = {
            "limit": row[58],
            "item_kind": row[44],
            "use_scene": row[46],
            "infinite": bool(row[47]),
            "use_target": row[62],
            "is_boost": 82 <= item_id <= 108,
        }

    key_data: dict[int, dict] = {}
    for row in key_items.rows:
        item_id = struct.unpack_from("<I", row, 0)[0]
        key_data[item_id] = {
            "limit": row[5],
            "item_kind": row[4],
            "use_group": row[6],
        }
    return consumable_data, key_data


def build_entries(
    consumable_data: dict[int, dict],
    key_data: dict[int, dict],
) -> list[dict]:
    entries: list[dict] = []
    for item_id in range(0, MAX_ITEM_ID + 1):
        category, group = category_for(item_id)
        data: dict = {}
        if item_id in consumable_data:
            data = consumable_data[item_id]
        elif item_id in key_data:
            data = key_data[item_id]

        limit = data.get("limit")
        if limit is None:
            limit = 1 if category == "essence" else 99
        entry = {
            "id": item_id,
            "limit": int(limit),
            "category": category,
            "group": group,
            "unique": int(limit) == 1,
        }
        for key in (
            "item_kind",
            "use_scene",
            "infinite",
            "use_target",
            "is_boost",
            "use_group",
        ):
            if key in data:
                entry[key] = data[key]
        entries.append(entry)
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate item metadata from an exported ItemTable JSON.",
    )
    parser.add_argument(
        "--item-table",
        type=Path,
        default=DEFAULT_ITEM_TABLE,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    args = parser.parse_args()

    consumable_data, key_data = load_item_table(args.item_table)
    entries = build_entries(consumable_data, key_data)
    write_entries(args.output, entries)
    print(
        f"Wrote {len(entries)} entries to {args.output} "
        f"({len(consumable_data)} consumables, {len(key_data)} key items)"
    )


if __name__ == "__main__":
    main()
