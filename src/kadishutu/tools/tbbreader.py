from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Self

from .extio import ExtIO

UEXP_OFFSET = 0x25
TBCR_HEADER_MIN = 12
TBL_HEADER_SIZE = 16
MAX_TABLES = 4096
MAX_TABLE_SIZE = 256 * 1024 * 1024
MAX_TABLE_ROWS = 1_000_000


def _file_size(file: ExtIO) -> int:
    position = file.tell()
    size = file.seek(0, 2)
    file.seek(position)
    return size


@dataclass
class Tbl:
    table_size: int
    row_size: int
    rows: list[bytes]
    MAGIC = "TBL1"

    @property
    def row_amount(self) -> int:
        if self.row_size <= 0:
            raise ValueError(f"Invalid table row size {self.row_size}")
        (res, chk) = divmod(self.table_size, self.row_size)
        if chk != 0:
            raise ValueError(
                f"Table size {self.table_size} is not a multiple of "
                f"row size {self.row_size}"
            )
        return res

    @classmethod
    def open(cls, file: ExtIO, offset: int) -> Self:
        file_size = _file_size(file)
        if offset < 0 or offset + TBL_HEADER_SIZE > file_size:
            raise ValueError(f"Table offset {offset} is outside the file")
        if file.tell() != offset:
            file.seek(offset)
        file.assert_magic(cls.MAGIC)
        table_size = file.read_u32_le()
        row_size = file.read_u32_le()
        file.skip(4)
        if row_size <= 0:
            raise ValueError(f"Invalid table row size {row_size}")
        remaining = file_size - file.tell()
        if table_size > remaining:
            raise ValueError(
                f"Table size {table_size} exceeds the {remaining} bytes "
                "remaining; data is truncated"
            )
        if table_size > MAX_TABLE_SIZE:
            raise ValueError(
                f"Table size {table_size} is too large "
                f"(limit {MAX_TABLE_SIZE})"
            )
        if table_size and row_size > table_size:
            raise ValueError(
                f"Row size {row_size} is larger than table size {table_size}"
            )
        this = cls(table_size, row_size, [])
        if this.row_amount > MAX_TABLE_ROWS:
            raise ValueError(
                f"Table row count {this.row_amount} exceeds "
                f"limit {MAX_TABLE_ROWS}"
            )
        for _ in range(this.row_amount):
            this.rows.append(file.read_exact(this.row_size))
        return this


@dataclass
class Tbcr:
    tables: list[Tbl]
    MAGIC = "TBCR"

    @classmethod
    def _open(cls, file: ExtIO, start_offset: int = 0) -> Self:
        file_size = _file_size(file)
        if start_offset < 0 or start_offset + TBCR_HEADER_MIN > file_size:
            raise ValueError("TBCR header is truncated")
        file.seek(start_offset)
        file.assert_magic(cls.MAGIC)
        header_size = file.read_u32_le()
        table_amount = file.read_u32_le()
        if header_size < TBCR_HEADER_MIN:
            raise ValueError(f"Invalid TBCR header size {header_size}")
        header_end = start_offset + header_size
        if header_end > file_size:
            raise ValueError(
                f"TBCR header size {header_size} extends beyond the file"
            )
        max_tables_by_file = (
            file_size - start_offset - TBCR_HEADER_MIN
        ) // 4
        if table_amount > MAX_TABLES:
            raise ValueError(
                f"TBCR table count {table_amount} exceeds limit {MAX_TABLES}"
            )
        if table_amount > max_tables_by_file:
            raise ValueError(
                f"TBCR table count {table_amount} does not fit in the file"
            )
        table_offsets = [
            file.read_u32_le() + header_size + start_offset
            for _ in range(table_amount)
        ]
        for offset in table_offsets:
            if offset < header_end or offset + TBL_HEADER_SIZE > file_size:
                raise ValueError(
                    f"Table offset {offset} is outside the table data"
                )
        tables = [
            Tbl.open(file, offset)
            for offset in table_offsets
        ]
        return cls(tables)

    @classmethod
    def open(cls, file: BinaryIO, start_offset: int = 0) -> Self:
        return cls._open(ExtIO.from_parent(file), start_offset)

    @classmethod
    def from_path(cls, path: Path, start_offset: int = 0) -> Self:
        if not start_offset and path.name.endswith(".uexp"):
            start_offset = UEXP_OFFSET
        return cls.open(path.open("rb"), start_offset)
