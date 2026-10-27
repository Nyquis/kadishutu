import io
import struct

import pytest

from kadishutu.tools import tbbreader
from kadishutu.tools.extio import ExtIO
from kadishutu.tools.tbbreader import Tbcr, Tbl

HEADER_SIZE = 16


def make_io(data: bytes) -> ExtIO:
    return ExtIO.from_parent(io.BytesIO(data))


def make_tbcr(table_size: int, row_size: int, rows: bytes) -> bytes:
    header = b"TBCR" + struct.pack("<III", HEADER_SIZE, 1, 0)
    table = b"TBL1" + struct.pack("<II", table_size, row_size) + b"\0" * 4
    return header + table + rows


def test_read_until_null_reads_terminated_string():
    assert make_io(b"abc\0rest").read_until_null() == "abc"


def test_read_until_null_rejects_missing_terminator():
    with pytest.raises(ValueError, match="Unterminated"):
        make_io(b"no terminator").read_until_null()


def test_read_utf16_until_null_reads_terminated_string():
    data = "hi".encode("utf-16-le") + b"\0\0"
    assert make_io(data).read_utf16_le_until_null() == "hi"


def test_read_utf16_until_null_rejects_missing_terminator():
    with pytest.raises(ValueError, match="Unterminated"):
        make_io("hi".encode("utf-16-le")).read_utf16_le_until_null()


def test_read_utf16_until_null_rejects_odd_length_tail():
    with pytest.raises(ValueError, match="Unterminated"):
        make_io(b"h\0i").read_utf16_le_until_null()


def test_table_rejects_zero_row_size():
    table = Tbl(table_size=8, row_size=0, rows=[])
    with pytest.raises(ValueError, match="row size"):
        _ = table.row_amount


def test_table_rejects_misaligned_table_size():
    table = Tbl(table_size=7, row_size=4, rows=[])
    with pytest.raises(ValueError, match="multiple"):
        _ = table.row_amount


def test_tbcr_reads_valid_table():
    data = make_tbcr(table_size=8, row_size=4, rows=b"ABCDEFGH")

    tbcr = Tbcr.open(io.BytesIO(data))

    assert tbcr.tables[0].rows == [b"ABCD", b"EFGH"]


def test_tbcr_rejects_bad_magic():
    with pytest.raises(ValueError, match="magic"):
        Tbcr.open(io.BytesIO(b"NOPE" + b"\0" * 64))


def test_tbcr_rejects_truncated_header():
    with pytest.raises(ValueError, match="truncated"):
        Tbcr.open(io.BytesIO(b"TBCR\0\0"))


def test_tbcr_rejects_truncated_rows():
    data = make_tbcr(table_size=16, row_size=8, rows=b"\0" * 4)

    with pytest.raises(ValueError, match="truncated"):
        Tbcr.open(io.BytesIO(data))


def test_tbcr_rejects_zero_row_size_in_file():
    data = make_tbcr(table_size=16, row_size=0, rows=b"")

    with pytest.raises(ValueError, match="row size"):
        Tbcr.open(io.BytesIO(data))


def test_tbcr_rejects_table_count_that_does_not_fit_file():
    data = b"TBCR" + struct.pack("<II", HEADER_SIZE, 1000) + b"\0" * 16

    with pytest.raises(ValueError, match="table count"):
        Tbcr.open(io.BytesIO(data))


def test_tbcr_rejects_table_count_above_cap(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(tbbreader, "MAX_TABLES", 2)
    data = b"TBCR" + struct.pack("<II", HEADER_SIZE, 3) + b"\0" * 16

    with pytest.raises(ValueError, match="table count"):
        Tbcr.open(io.BytesIO(data))


def test_tbcr_rejects_small_header_size():
    data = b"TBCR" + struct.pack("<II", 8, 0) + b"\0" * 8

    with pytest.raises(ValueError, match="header size"):
        Tbcr.open(io.BytesIO(data))


def test_tbcr_rejects_header_size_beyond_file():
    data = b"TBCR" + struct.pack("<II", 0x1000, 0)

    with pytest.raises(ValueError, match="header size"):
        Tbcr.open(io.BytesIO(data))


def test_tbcr_rejects_table_offset_beyond_file():
    data = b"TBCR" + struct.pack("<III", HEADER_SIZE, 1, 0xFFFF)

    with pytest.raises(ValueError, match="offset"):
        Tbcr.open(io.BytesIO(data))


def test_tbcr_rejects_table_size_beyond_file():
    data = make_tbcr(table_size=100, row_size=4, rows=b"")

    with pytest.raises(ValueError, match="truncated"):
        Tbcr.open(io.BytesIO(data))


def test_tbcr_rejects_table_size_above_cap(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(tbbreader, "MAX_TABLE_SIZE", 8)
    data = make_tbcr(table_size=16, row_size=1, rows=b"\0" * 16)

    with pytest.raises(ValueError, match="too large"):
        Tbcr.open(io.BytesIO(data))


def test_tbcr_rejects_row_count_above_cap(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(tbbreader, "MAX_TABLE_ROWS", 4)
    data = make_tbcr(table_size=8, row_size=1, rows=b"\0" * 8)

    with pytest.raises(ValueError, match="row count"):
        Tbcr.open(io.BytesIO(data))


def test_tbcr_rejects_row_size_larger_than_table():
    data = make_tbcr(table_size=4, row_size=8, rows=b"\0" * 4)

    with pytest.raises(ValueError, match="larger than table size"):
        Tbcr.open(io.BytesIO(data))


def test_tbcr_accepts_empty_table():
    data = make_tbcr(table_size=0, row_size=4, rows=b"")

    tbcr = Tbcr.open(io.BytesIO(data))

    assert tbcr.tables[0].rows == []
