"""Nahobino level tables and EXP requirements.

The stat table and the EXP curve are taken from the game's ``PlayerGrow``
asset (tables 2 and 3).  The stat table was checked against two real saves:
level 4 and level 55 match exactly once allocated stat points are removed.

``PlayerGrow`` only covers the Nahobino.  Demon EXP requirements are derived
from the Nahobino curve using the game's level-difference multiplier; see
``DEMON_EXP_MULTIPLIERS``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from .tools.path import TABLES_PATH

DATA_PATH = TABLES_PATH / "nahobino_leveling.json"

# Demon EXP cost relative to the Nahobino, based on how many levels above its
# species' base level the demon is.  Index 0 means "at or below base level".
DEMON_EXP_MULTIPLIERS = (
    1.5,
    2.0,
    2.57,
    3.23,
    3.96,
    4.77,
    5.66,
    6.63,
    7.67,
    8.8,
    10.0,
)

# Normal demon level-ups grant this many points to the five core stats.
DEMON_STAT_POINTS_PER_LEVEL = 3


def expected_stat_gain(
    weight: int,
    total: int,
    points_per_level: int = DEMON_STAT_POINTS_PER_LEVEL,
) -> float:
    """Expected core-stat gain per level from a growth weight."""
    if total <= 0:
        return 0.0
    return points_per_level * weight / total


@dataclass(frozen=True)
class LevelStats:
    level: int
    hp: int
    mp: int
    strength: int
    vitality: int
    magic: int
    agility: int
    luck: int

    @property
    def total(self) -> int:
        return (
            self.strength
            + self.vitality
            + self.magic
            + self.agility
            + self.luck
        )


@dataclass(frozen=True)
class LevelingData:
    stats: dict[int, LevelStats]
    exp_to_next: tuple[int, ...]
    max_level: int

    def stats_at(self, level: int) -> LevelStats:
        try:
            return self.stats[level]
        except KeyError:
            raise ValueError(
                f"level {level} is outside the table range "
                f"(1-{self.max_level})"
            ) from None

    def exp_required(self, level: int) -> int | None:
        """EXP needed to advance from ``level`` to ``level + 1``."""
        if level < 1 or level >= self.max_level:
            return None
        return self.exp_to_next[level - 1]


@lru_cache(maxsize=1)
def load_leveling_data() -> LevelingData:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    stats = {
        entry["level"]: LevelStats(
            entry["level"],
            entry["hp"],
            entry["mp"],
            entry["strength"],
            entry["vitality"],
            entry["magic"],
            entry["agility"],
            entry["luck"],
        )
        for entry in raw["stats"]
    }
    exp_to_next = tuple(raw["exp_to_next"])
    max_level = max(stats)
    if len(exp_to_next) != max_level - 1:
        raise ValueError(
            "EXP table length does not match the stat table: "
            f"{len(exp_to_next)} vs {max_level - 1}"
        )
    return LevelingData(stats, exp_to_next, max_level)


def nahobino_stats(level: int) -> LevelStats:
    """Base Nahobino stats at ``level`` before allocated stat points."""
    return load_leveling_data().stats_at(level)


def nahobino_exp_to_next(level: int) -> int | None:
    """EXP the Nahobino needs to advance from ``level``."""
    return load_leveling_data().exp_required(level)


def demon_exp_multiplier(level: int, base_level: int) -> float:
    """EXP multiplier for a demon grown above its species' base level."""
    above_base = max(0, level - base_level)
    index = min(above_base, len(DEMON_EXP_MULTIPLIERS) - 1)
    return DEMON_EXP_MULTIPLIERS[index]


def demon_exp_to_next(level: int, base_level: int) -> int | None:
    """EXP a demon needs to advance from ``level``."""
    base = nahobino_exp_to_next(level)
    if base is None:
        return None
    return int(base * demon_exp_multiplier(level, base_level))


def exp_progress(exp: int, required: int | None) -> float | None:
    """Fraction of the current level's EXP bar that is filled."""
    if not required:
        return None
    return min(1.0, max(0.0, exp / required))
