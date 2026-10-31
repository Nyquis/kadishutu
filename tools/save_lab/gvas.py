from __future__ import annotations

import struct
from dataclasses import dataclass

GVAS_MAGIC = b"GVAS"
DEFAULT_GVAS_OFFSET = 0x40
CUSTOM_VERSION_SIZE = 20
MAX_STRING_LENGTH = 4096
MAX_CUSTOM_VERSIONS = 4096


class GvasError(ValueError):
    """Raised when a GVAS header cannot be parsed."""


@dataclass(frozen=True)
class EngineVersion:
    major: int
    minor: int
    patch: int
    change_list: int
    branch: str

    def __str__(self) -> str:
        return (
            f"{self.major}.{self.minor}.{self.patch}"
            f"-{self.change_list}"
        )


@dataclass(frozen=True)
class GvasHeader:
    offset: int
    save_version: int
    package_version: int
    engine: EngineVersion
    custom_version_format: int
    custom_version_count: int
    class_name: str
    payload_offset: int


class _Reader:
    def __init__(self, data: bytes, offset: int) -> None:
        self.data = data
        self.pos = offset

    def _require(self, size: int) -> None:
        if size < 0 or self.pos + size > len(self.data):
            raise GvasError(
                f"truncated at 0x{self.pos:x}; need {size} more byte(s)"
            )

    def take(self, size: int) -> bytes:
        self._require(size)
        value = self.data[self.pos:self.pos + size]
        self.pos += size
        return value

    def u16(self) -> int:
        return struct.unpack("<H", self.take(2))[0]

    def u32(self) -> int:
        return struct.unpack("<I", self.take(4))[0]

    def i32(self) -> int:
        return struct.unpack("<i", self.take(4))[0]

    def skip(self, size: int) -> None:
        self._require(size)
        self.pos += size

    def fstring(self) -> str:
        length = self.i32()
        if length == 0:
            return ""
        if length > 0:
            if length > MAX_STRING_LENGTH:
                raise GvasError(f"string length {length} is too large")
            raw = self.take(length)
            if not raw.endswith(b"\0"):
                raise GvasError("string is not null-terminated")
            return raw[:-1].decode("utf-8", "replace")
        count = -length
        if count > MAX_STRING_LENGTH:
            raise GvasError(f"wide string length {count} is too large")
        raw = self.take(count * 2)
        if not raw.endswith(b"\0\0"):
            raise GvasError("wide string is not null-terminated")
        return raw[:-2].decode("utf-16-le", "replace")


def find_gvas_offset(data: bytes, limit: int = 0x100) -> int:
    offset = data.find(GVAS_MAGIC, 0, limit)
    if offset < 0:
        raise GvasError(f"no GVAS magic found in the first 0x{limit:x} bytes")
    return offset


def parse_gvas_header(
    data: bytes,
    offset: int = DEFAULT_GVAS_OFFSET,
) -> GvasHeader:
    reader = _Reader(data, offset)
    if reader.take(4) != GVAS_MAGIC:
        raise GvasError(f"no GVAS magic at 0x{offset:x}")

    save_version = reader.u32()
    package_version = reader.u32()
    engine = EngineVersion(
        major=reader.u16(),
        minor=reader.u16(),
        patch=reader.u16(),
        change_list=reader.u32(),
        branch=reader.fstring(),
    )
    custom_version_format = reader.u32()
    custom_version_count = reader.u32()
    if custom_version_count > MAX_CUSTOM_VERSIONS:
        raise GvasError(
            f"custom version count {custom_version_count} is too large"
        )
    reader.skip(custom_version_count * CUSTOM_VERSION_SIZE)
    class_name = reader.fstring()

    return GvasHeader(
        offset=offset,
        save_version=save_version,
        package_version=package_version,
        engine=engine,
        custom_version_format=custom_version_format,
        custom_version_count=custom_version_count,
        class_name=class_name,
        payload_offset=reader.pos,
    )
