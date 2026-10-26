from dataclasses import dataclass, field

from .miracles import MIRACLE_NAME_MAP, Miracle
from .tools.json import JsonListMixin
from .tools.mapping import make_maps
from .tools.path import TABLES_PATH
from .tools.serialization import hex_int_config

MIRACLE_UNLOCKS_DATA_PATH = TABLES_PATH / "miracle_unlocks.json"


@dataclass
class MiracleUnlock(JsonListMixin):
    id: int = field(
        metadata=hex_int_config(4)
    )
    name: str
    miracles: list[str]

    @property
    def miracles_obj(self) -> list[Miracle]:
        return [
            MIRACLE_NAME_MAP[i]
            for i in self.miracles
        ]


MIRACLE_UNLOCKS = MiracleUnlock.load_path(MIRACLE_UNLOCKS_DATA_PATH)


(MIRACLE_UNLOCK_ID_MAP, MIRACLE_UNLOCK_NAME_MAP) = make_maps(MIRACLE_UNLOCKS)
