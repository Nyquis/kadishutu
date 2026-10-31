from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    start: int
    end: int
    name: str
    status: str = "known"

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise ValueError(f"invalid region {self.start:#x}-{self.end:#x}")

    @property
    def size(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class Coverage:
    size: int
    covered: int
    ranges: tuple[tuple[int, int], ...]
    unknown: tuple[tuple[int, int], ...]

    @property
    def percent(self) -> float:
        if not self.size:
            return 0.0
        return self.covered * 100.0 / self.size


GAME_SAVE_REGIONS: tuple[Region, ...] = (
    Region(0x000, 0x040, "container / hash"),
    Region(0x040, 0x4D0, "GVAS header"),
    Region(0x4D0, 0x988, "save/load header", "inferred"),
    Region(0x988, 0xB60, "player record", "verified"),
    Region(0xB60, 0x3D10, "30 demon records", "verified"),
    Region(0x3D10, 0x3D2E, "party order", "verified"),
    Region(0x3D2E, 0x3D31, "summoned demons", "verified"),
    Region(0x3D31, 0x3D32, "max demon stock", "verified"),
    Region(0x3D32, 0x3D36, "Macca", "verified"),
    Region(0x3D4A, 0x3D4E, "Glory", "verified"),
    Region(0x3D4E, 0x3DE0, "miracle block", "inferred"),
    Region(0x3ECE, 0x3ED0, "Magatsuhi gauge", "inferred"),
    Region(0x49D8, 0x4C20, "guest / partner records", "inferred"),
    Region(0x4C72, 0x4FF2, "item amounts", "verified"),
    Region(0x5129, 0x523C, "essence metadata", "inferred"),
    Region(0x567E, 0x569A, "map and position", "verified"),
    Region(0x59D52, 0x5B412, "quest records", "inferred"),
    Region(0x69A90, 0x6A08E, "settings copy", "inferred"),
    Region(0x18272, 0x2DB42, "analyze / compendium", "inferred"),
)

SYS_SAVE_REGIONS: tuple[Region, ...] = (
    Region(0x000, 0x040, "container / hash"),
    Region(0x040, 0x4D6, "GVAS header"),
    Region(0x4D6, 0x5E0, "save/load header", "inferred"),
    Region(0x5E0, 0x1260, "settings", "inferred"),
)


def regions_for_class(class_name: str) -> tuple[Region, ...]:
    if class_name == "SystemSaveObject":
        return SYS_SAVE_REGIONS
    return GAME_SAVE_REGIONS


def _merged_ranges(regions: tuple[Region, ...], size: int) -> list[tuple[int, int]]:
    clipped = sorted(
        (max(0, region.start), min(size, region.end))
        for region in regions
        if region.start < size and region.end > 0
    )
    merged: list[tuple[int, int]] = []
    for start, end in clipped:
        if start >= end:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def coverage(regions: tuple[Region, ...], size: int) -> Coverage:
    if size < 0:
        raise ValueError("size must not be negative")
    ranges = _merged_ranges(regions, size)
    covered = sum(end - start for start, end in ranges)
    unknown: list[tuple[int, int]] = []
    cursor = 0
    for start, end in ranges:
        if cursor < start:
            unknown.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < size:
        unknown.append((cursor, size))
    return Coverage(
        size=size,
        covered=covered,
        ranges=tuple(ranges),
        unknown=tuple(unknown),
    )


def format_coverage(
    result: Coverage,
    *,
    label: str = "save",
    max_unknown: int = 12,
) -> str:
    lines = [
        f"{label}: {result.covered}/{result.size} bytes covered "
        f"({result.percent:.1f}%)",
        "covered ranges:",
    ]
    lines.extend(
        f"  0x{start:06x}-0x{end:06x}  {end - start:6d} bytes"
        for start, end in result.ranges
    )
    if result.unknown:
        lines.append("unknown ranges:")
        lines.extend(
            f"  0x{start:06x}-0x{end:06x}  {end - start:6d} bytes"
            for start, end in result.unknown[:max_unknown]
        )
        if len(result.unknown) > max_unknown:
            lines.append(
                f"  ... {len(result.unknown) - max_unknown} more range(s)"
            )
    return "\n".join(lines)
