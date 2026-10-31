from dataclasses import dataclass, field
from struct import unpack

from .tools.json import JsonListMixin
from .tools.path import TABLES_PATH
from .tools.serialization import bytes_config, hex_int_config

LAYLINE_DATA_PATH = TABLES_PATH / "laylines.json"


LAYLINE_UNLOCK_OFFSET = 0x80a2
REGION_ORDER = (
    "Da'at: Minato",
    "Da'at: Shinagawa",
    "Da'at: Chiyoda",
    "Da'at: Taito",
    "Da'at: Shinjuku",
    "Tokyo",
    "Empyrean",
    "Shakan",
    "Temple of Eternity",
    "Serpent's Grave",
    "Other",
)
SPECIAL_REGIONS = {
    "Jouin High School": "Tokyo",
    "Tokyo Diet Building": "Tokyo",
    "Hall of Chaos": "Other",
}


@dataclass
class LaylineUnlock(JsonListMixin):
    offset: int = field(
        metadata=hex_int_config(5)
    )
    bit: int


@dataclass
class Layline(JsonListMixin):
    id: int = field(
        metadata=hex_int_config(0)
    )
    name: str
    map_upper: int = field(
        metadata=hex_int_config(8)
    )
    map_lower: int = field(
        metadata=hex_int_config(8)
    )
    coordinates: bytes = field(
        metadata=bytes_config(12)
    )
    rotation: bytes = field(
        metadata=bytes_config(8)
    )
    unlock: LaylineUnlock | None = None

    @staticmethod
    def unlock_data_from_id(id: int) -> tuple[int, int]:
        (offset, bit) = divmod(id, 8)
        offset += LAYLINE_UNLOCK_OFFSET
        return (offset, bit)

    @property
    def unlock_data(self) -> tuple[int, int]:
        return self.unlock_data_from_id(self.id)

    @property
    def region(self) -> str:
        if " - " in self.name:
            return self.name.split(" - ", 1)[0]
        return SPECIAL_REGIONS.get(self.name, "Other")

    @property
    def place(self) -> str:
        if " - " in self.name:
            return self.name.split(" - ", 1)[1]
        return self.name

    @property
    def position(self) -> tuple[float, float, float]:
        return unpack("<fff", self.coordinates)

    @property
    def region_order(self) -> tuple[int, str]:
        try:
            return (REGION_ORDER.index(self.region), self.region)
        except ValueError:
            return (len(REGION_ORDER), self.region)


LAYLINE_DATA = Layline.load_path(LAYLINE_DATA_PATH)


## Converter sanity check
#for layline in LAYLINE_DATA:
#    if not layline.unlock:
#        continue
#    assert layline.unlock.offset == layline.unlock_data[0]
#    assert layline.unlock.bit == layline.unlock_data[1]


def make_alignment_map() -> tuple[dict[int, Layline], dict[str, Layline]]:
    id_map = {}
    name_map = {}
    for layline in LAYLINE_DATA:
        id_map[layline.id] = layline
        name_map[layline.name] = layline
    return (id_map, name_map)


(LAYLINE_ID_MAP, LAYLINE_NAME_MAP) = make_alignment_map()
