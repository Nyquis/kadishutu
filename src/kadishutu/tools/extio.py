from abc import ABC
from dataclasses import dataclass
from typing import BinaryIO, Generic, Self, TypeVar

MAGIC_ENCODING = "ascii"
ENCODING = "UTF-16"


T = TypeVar("T")


@dataclass
class WrapperClass(Generic[T], ABC):
    _inner: T

    def __getattribute__(self, name: str):
        if name == "_inner":
            return super().__getattribute__(name)
        try:
            return self._inner.__getattribute__(name)
        except AttributeError:
            pass
        return super().__getattribute__(name)

    @classmethod
    def from_parent(cls, io: T) -> Self:
        return cls(io)


class ExtIO(BinaryIO, WrapperClass):
    _inner: BinaryIO

    def skip(self, amount: int):
        self.seek(self.tell() + amount)

    def assert_magic(
        self,
        magic: str | bytes,
        encoding: str = MAGIC_ENCODING
    ):
        if isinstance(magic, str):
            magic = magic.encode(encoding)
        data = self.read_exact(len(magic))
        if data != magic:
            raise ValueError(f"Invalid magic {data!r} instead of {magic!r}")

    def read_exact(self, amount: int) -> bytes:
        data = self.read(amount)
        if len(data) != amount:
            raise ValueError(
                f"Data is truncated: wanted {amount} bytes, got {len(data)}"
            )
        return data

    def read_u32_le(self) -> int:
        return int.from_bytes(self.read_exact(4), byteorder="little")

    def read_chars(self, amount: int, encoding: str = ENCODING) -> str:
        return self.read_exact(amount).decode(encoding)

    def _read_until_terminator(self, terminator: bytes) -> bytes:
        width = len(terminator)
        chunks: list[bytes] = []
        while True:
            chunk = self.read(width)
            if len(chunk) != width:
                raise ValueError("Unterminated string")
            if chunk == terminator:
                return b"".join(chunks)
            chunks.append(chunk)

    def read_until_null(self) -> str:
        return self._read_until_terminator(b"\0").decode()

    def read_utf16_le_until_null(self) -> str:
        return self._read_until_terminator(b"\0\0").decode("UTF-16-LE")
