import json
from typing import Any

from kadishutu.data.tools.path import TABLES_PATH
from kadishutu.encodings import ENCODING

from .laylines import LAYLINE_ID_MAP

SAVE_LOCS_PATH = TABLES_PATH / "save_locs.json"
with SAVE_LOCS_PATH.open("rt", encoding=ENCODING) as file:
    SAVE_LOCS: dict[int, str] = {
        int(k, base=16): v
        for k, v in json.load(file).items()
    }

SAVE_LOCS_REV = {v: k for k, v in SAVE_LOCS.items()}

MAP_AREA_NAMES: dict[int, str] = {}
for _layline in LAYLINE_ID_MAP.values():
    MAP_AREA_NAMES.setdefault(_layline.map_upper, _layline.region)


def save_location_name(position: Any) -> str | None:
    """Best available location name for a save preview.

    ``title_save_location`` is not fully mapped in the local tables, so fall
    back to the last layline and then to the map region.
    """
    name = SAVE_LOCS.get(position.title_save_location)
    if name is not None:
        return name
    layline = position.last_layline
    if layline is not None:
        return layline.name
    return MAP_AREA_NAMES.get(position.current_map_upper)
