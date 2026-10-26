from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Self

from .extio import ExtIO

UEXP_OFFSET = 0x25


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
        if file.tell() != offset:
            file.seek(offset)
        file.assert_magic(cls.MAGIC)
        table_size = file.read_u32_le()
        row_size = file.read_u32_le()
        file.skip(4)
        this = cls(table_size, row_size, [])
        for _ in range(this.row_amount):
            this.rows.append(file.read_exact(this.row_size))
        return this


@dataclass
class Tbcr:
    tables: list[Tbl]
    MAGIC = "TBCR"

    @classmethod
    def _open(cls, file: ExtIO, start_offset: int = 0) -> Self:
        file.seek(start_offset)
        file.assert_magic(cls.MAGIC)
        header_size = file.read_u32_le()
        table_amount = file.read_u32_le()
        table_offsets = [
            file.read_u32_le() + header_size + start_offset
            for _ in range(table_amount)
        ]
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
