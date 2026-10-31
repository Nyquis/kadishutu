import struct

import pytest

from tools.save_lab.gvas import (
    GvasError,
    find_gvas_offset,
    parse_gvas_header,
)


def make_gvas_header(class_name: str = "SaveObject") -> tuple[bytes, int]:
    branch = b"++UE4+Release-4.27"
    data = bytearray(0x400)
    offset = 0x40
    data[offset:offset + 4] = b"GVAS"
    struct.pack_into("<II", data, offset + 4, 2, 522)
    struct.pack_into("<HHH", data, offset + 12, 4, 27, 2)
    struct.pack_into("<I", data, offset + 18, 0)
    position = offset + 22
    struct.pack_into("<i", data, position, len(branch) + 1)
    position += 4
    data[position:position + len(branch) + 1] = branch + b"\0"
    position += len(branch) + 1
    struct.pack_into("<II", data, position, 3, 0)
    position += 8
    name = class_name.encode()
    struct.pack_into("<i", data, position, len(name) + 1)
    position += 4
    data[position:position + len(name) + 1] = name + b"\0"
    position += len(name) + 1
    return bytes(data), position


def test_parse_gvas_header_reads_engine_and_class():
    data, payload_offset = make_gvas_header("SaveObject")

    header = parse_gvas_header(data, 0x40)

    assert header.offset == 0x40
    assert header.save_version == 2
    assert header.package_version == 522
    assert header.engine.major == 4
    assert header.engine.minor == 27
    assert header.engine.patch == 2
    assert header.engine.branch == "++UE4+Release-4.27"
    assert header.custom_version_format == 3
    assert header.custom_version_count == 0
    assert header.class_name == "SaveObject"
    assert header.payload_offset == payload_offset


def test_parse_gvas_header_reads_system_class():
    data, _ = make_gvas_header("SystemSaveObject")

    header = parse_gvas_header(data, 0x40)

    assert header.class_name == "SystemSaveObject"


def test_find_gvas_offset():
    data, _ = make_gvas_header()

    assert find_gvas_offset(data) == 0x40


def test_parse_gvas_header_rejects_missing_magic():
    data, _ = make_gvas_header()
    broken = data[:0x40] + b"NOPE" + data[0x44:]

    with pytest.raises(GvasError, match="magic"):
        parse_gvas_header(broken, 0x40)


def test_parse_gvas_header_rejects_truncated_header():
    with pytest.raises(GvasError, match="truncated"):
        parse_gvas_header(b"GVAS", 0)


def test_engine_version_string():
    data, _ = make_gvas_header()

    header = parse_gvas_header(data, 0x40)

    assert str(header.engine) == "4.27.2-0"
