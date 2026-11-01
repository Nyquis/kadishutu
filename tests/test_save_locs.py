from types import SimpleNamespace

from kadishutu.data.laylines import LAYLINE_ID_MAP
from kadishutu.data.save_locs import save_location_name


def position(**kwargs):
    defaults = {
        "title_save_location": 0xFFFF,
        "last_layline": None,
        "current_map_upper": 0,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_exact_title_location_mapping_wins():
    pos = position(title_save_location=0x21)

    assert save_location_name(pos) == "Tamachi"


def test_last_layline_fallback():
    pos = position(
        last_layline=LAYLINE_ID_MAP[74],
        current_map_upper=64,
    )

    assert save_location_name(pos) == "Da'at: Shinjuku - Yoyogi"


def test_map_region_fallback():
    pos = position(current_map_upper=61)

    assert save_location_name(pos) == "Da'at: Minato"


def test_unknown_location_returns_none():
    pos = position()

    assert save_location_name(pos) is None
