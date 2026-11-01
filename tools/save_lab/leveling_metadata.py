from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

from .mmi import load_mmi_tbcr

DEFAULT_TABLE = Path(
    "lab/dumps/game-tables-json/Project/Content/Blueprints/Gamedata/"
    "BinTable/Common/PlayerGrow.json"
)
DEFAULT_OUTPUT = Path("src/kadishutu/data/tables/nahobino_leveling.json")

# PlayerGrow table 2 holds one 7-int row per level; row 0 is unused and
# rows 1..150 map to levels 1..150.
STATS_TABLE_INDEX = 2
# Table 3 holds the EXP needed to advance one level, indexed by level - 1.
EXP_TABLE_INDEX = 3
STATS_FORMAT = struct.Struct("<7i")
EXP_FORMAT = struct.Struct("<i")


def build_payload(path: Path) -> dict:
    tcx = load_mmi_tbcr(path)
    if len(tcx.tables) <= max(STATS_TABLE_INDEX, EXP_TABLE_INDEX):
        raise ValueError(
            f"{path} has {len(tcx.tables)} tables, expected at least 4"
        )

    stats_table = tcx.tables[STATS_TABLE_INDEX]
    if stats_table.row_size != STATS_FORMAT.size:
        raise ValueError(
            f"stats table row size is {stats_table.row_size}, "
            f"expected {STATS_FORMAT.size}"
        )

    stats = []
    for level, row in enumerate(stats_table.rows):
        if level == 0:
            continue
        hp, mp, strength, vitality, magic, agility, luck = \
            STATS_FORMAT.unpack(row)
        stats.append({
            "level": level,
            "hp": hp,
            "mp": mp,
            "strength": strength,
            "vitality": vitality,
            "magic": magic,
            "agility": agility,
            "luck": luck,
        })

    exp_table = tcx.tables[EXP_TABLE_INDEX]
    if exp_table.row_size != EXP_FORMAT.size:
        raise ValueError(
            f"exp table row size is {exp_table.row_size}, "
            f"expected {EXP_FORMAT.size}"
        )
    exp_to_next = [
        EXP_FORMAT.unpack(row)[0]
        for row in exp_table.rows
    ]

    if len(exp_to_next) != stats[-1]["level"] - 1:
        raise ValueError(
            "exp table length does not match the level table: "
            f"{len(exp_to_next)} vs {stats[-1]['level'] - 1}"
        )

    return {
        "source": "PlayerGrow (Common/PlayerGrow)",
        "stats_table": STATS_TABLE_INDEX,
        "exp_table": EXP_TABLE_INDEX,
        "stats_index": "row index = level; row 0 is unused",
        "exp_index": "index = level - 1",
        "stats": stats,
        "exp_to_next": exp_to_next,
    }


def write_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Nahobino stat and EXP tables from PlayerGrow.",
    )
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    payload = build_payload(args.table)
    write_payload(args.output, payload)
    print(
        f"Wrote {len(payload['stats'])} levels and "
        f"{len(payload['exp_to_next'])} EXP entries to {args.output}"
    )


if __name__ == "__main__":
    main()
