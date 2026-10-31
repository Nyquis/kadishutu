from __future__ import annotations

import math
import struct
from dataclasses import dataclass

MAX_UTF16_SIZE = 64


@dataclass(frozen=True)
class Change:
    offset: int
    before: bytes
    after: bytes

    @property
    def end(self) -> int:
        return self.offset + len(self.after)


@dataclass(frozen=True)
class Candidate:
    kind: str
    before: object
    after: object


def diff_runs(before: bytes, after: bytes) -> list[Change]:
    if len(before) != len(after):
        raise ValueError(
            f"save sizes differ: 0x{len(before):x} != 0x{len(after):x}"
        )

    runs: list[Change] = []
    start: int | None = None
    for index, (old, new) in enumerate(zip(before, after, strict=True)):
        if old != new:
            if start is None:
                start = index
        elif start is not None:
            runs.append(Change(
                start,
                before[start:index],
                after[start:index],
            ))
            start = None

    if start is not None:
        runs.append(Change(start, before[start:], after[start:]))
    return runs


def group_changes(
    before: bytes,
    after: bytes,
    gap: int = 8,
) -> list[Change]:
    if gap < 0:
        raise ValueError("gap must not be negative")
    runs = diff_runs(before, after)
    groups: list[tuple[int, int]] = []
    for run in runs:
        if groups and run.offset - groups[-1][1] <= gap:
            groups[-1] = (groups[-1][0], run.end)
        else:
            groups.append((run.offset, run.end))
    return [
        Change(start, before[start:end], after[start:end])
        for start, end in groups
    ]


def _int_candidate(
    kind: str,
    fmt: str,
    before: bytes,
    after: bytes,
) -> Candidate | None:
    size = struct.calcsize(fmt)
    if len(after) < size:
        return None
    old = struct.unpack_from(fmt, before)[0]
    new = struct.unpack_from(fmt, after)[0]
    return Candidate(kind, old, new)


def _float_candidate(
    kind: str,
    fmt: str,
    before: bytes,
    after: bytes,
) -> Candidate | None:
    size = struct.calcsize(fmt)
    if len(after) < size:
        return None
    old = struct.unpack_from(fmt, before)[0]
    new = struct.unpack_from(fmt, after)[0]
    if not (math.isfinite(old) and math.isfinite(new)):
        return None
    return Candidate(kind, round(old, 6), round(new, 6))


def _utf16_candidate(before: bytes, after: bytes) -> Candidate | None:
    size = len(after)
    if size < 2 or size % 2 or size > MAX_UTF16_SIZE:
        return None
    try:
        old = before.decode("utf-16-le")
        new = after.decode("utf-16-le")
    except UnicodeDecodeError:
        return None
    if not all(char.isprintable() or char == "\0" for char in old + new):
        return None
    return Candidate("utf16", old.rstrip("\0"), new.rstrip("\0"))


def _bit_candidate(before: bytes, after: bytes) -> Candidate | None:
    # Bit listings are useful for flags, but pure noise for hashes and
    # structured records. Only show them for small changes.
    if len(after) > 8:
        return None
    xor = bytes(old ^ new for old, new in zip(before, after, strict=True))
    if not any(xor):
        return None
    bits = [
        index * 8 + bit
        for index, value in enumerate(xor)
        for bit in range(8)
        if value & (1 << bit)
    ]
    return Candidate(
        "bits",
        f"0x{int.from_bytes(before, 'little'):x}",
        f"0x{int.from_bytes(after, 'little'):x} "
        f"(changed bits: {bits})",
    )


def decode_candidates(change: Change) -> list[Candidate]:
    candidates = [
        _int_candidate("u8", "<B", change.before, change.after),
        _int_candidate("i8", "<b", change.before, change.after),
        _int_candidate("u16", "<H", change.before, change.after),
        _int_candidate("i16", "<h", change.before, change.after),
        _int_candidate("u32", "<I", change.before, change.after),
        _int_candidate("i32", "<i", change.before, change.after),
        _int_candidate("u64", "<Q", change.before, change.after),
        _int_candidate("i64", "<q", change.before, change.after),
        _float_candidate("f32", "<f", change.before, change.after),
        _float_candidate("f64", "<d", change.before, change.after),
        _utf16_candidate(change.before, change.after),
        _bit_candidate(change.before, change.after),
    ]
    return [candidate for candidate in candidates if candidate is not None]


def format_change(change: Change, index: int) -> str:
    lines = [
        f"[{index}] 0x{change.offset:06x} "
        f"({len(change.after)} byte(s))",
        f"  before: {change.before.hex(' ')}",
        f"  after:  {change.after.hex(' ')}",
    ]
    for candidate in decode_candidates(change):
        lines.append(
            f"  {candidate.kind}: "
            f"{candidate.before!r} -> {candidate.after!r}"
        )
    return "\n".join(lines)


def format_diff(
    before: bytes,
    after: bytes,
    *,
    gap: int = 8,
    limit: int | None = None,
) -> str:
    changes = group_changes(before, after, gap=gap)
    if not changes:
        return "no differences"

    shown = changes if limit is None else changes[:limit]
    lines = [
        f"{len(changes)} changed region(s); "
        f"{sum(len(change.after) for change in changes)} byte(s) differ"
    ]
    for index, change in enumerate(shown):
        lines.append(format_change(change, index))
    if limit is not None and len(changes) > limit:
        lines.append(f"... {len(changes) - limit} more region(s)")
    return "\n".join(lines)
