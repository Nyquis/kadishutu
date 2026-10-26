from dataclasses import dataclass, field

from .tools.json import JsonListMixin
from .tools.path import TABLES_PATH
from .tools.serialization import hex_int_config

ALIGNMENT_DATA_PATH = TABLES_PATH / "alignment_data.json"


@dataclass
class AlignmentBit(JsonListMixin):
    bit: int
    alignment: str
    place: str
    side_quest: str | None
    text: list[str]


@dataclass
class AlignmentByte(JsonListMixin):
    offset: int = field(
        metadata=hex_int_config(5),
    )
    bits: list[AlignmentBit]

    def __init__(self, offset: int, bits: list[AlignmentBit]):
        self.offset = offset
        self.bits = bits
        self.bitmap = {}
        for bitobj in bits:
            self.bitmap[bitobj.bit] = bitobj

    def has_bit(self, bit: int) -> bool:
        try:
            self.bitmap[bit]
        except IndexError:
            return False
        else:
            return True


ALIGNMENT_DATA = AlignmentByte.load_path(ALIGNMENT_DATA_PATH)


def make_alignment_map() -> dict[int, AlignmentByte]:
    res = {}
    for byte in ALIGNMENT_DATA:
        res[byte.offset] = byte
    return res


ALIGNMENT_OFFSET_MAP = make_alignment_map()
