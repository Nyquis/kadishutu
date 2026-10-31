import json
from dataclasses import dataclass
from typing import Self

from .element_icons import Element
from .tools.csv import FromCsv
from .tools.json import JsonListMixin
from .tools.mapping import make_maps
from .tools.path import TABLES_PATH
from .tools.unused import is_unused

ITEM_NAMES_TABLE_PATH = TABLES_PATH / "SMT5V NKM Base Table_Navi Devil Data - Item Names.csv"
ITEM_ADDITIONAL_INFO_PATH = TABLES_PATH / "item_extra_data.json"
ITEM_METADATA_PATH = TABLES_PATH / "items.generated.json"


ITEM_TABLE_OFFSET = 0x4c72

# 0x4c72 - 0
# 0x4c73 - 1
# etc...


ITEM_METADATA = {
    int(entry["id"]): entry
    for entry in json.loads(ITEM_METADATA_PATH.read_text(encoding="utf-8"))
}


def _range_for_group(group: str) -> range:
    ids = sorted(
        item_id
        for item_id, entry in ITEM_METADATA.items()
        if entry.get("group") == group
    )
    if not ids:
        return range(0)
    return range(ids[0], ids[-1] + 1)


def _range_for_flag(flag: str) -> range:
    ids = sorted(
        item_id
        for item_id, entry in ITEM_METADATA.items()
        if entry.get(flag)
    )
    if not ids:
        return range(0)
    return range(ids[0], ids[-1] + 1)


TOTAL_ITEM_RANGE = range(0, max(ITEM_METADATA, default=895) + 1)
CONSUMABLES_RANGE = _range_for_group("consumable")
CON_BOOST_RANGE = _range_for_flag("is_boost")
ESSENCES_RANGE = _range_for_group("essence")
RELICS_RANGE_1 = _range_for_group("relic_1")
KEY_ITEMS_RANGE = _range_for_group("key_item")
RELICS_RANGE_2 = _range_for_group("relic_2")


DEFAULT_LIMIT = 99
ESSENCE_ITEM_LIMIT = 1
RELICS_ITEM_LIMIT = DEFAULT_LIMIT

USE_SCENE_NAMES = (
    "Not usable",
    "Field",
    "Battle",
    "Facility",
    "Not battle",
    "Not field",
    "Not facility",
    "All scenes",
)
ITEM_KIND_NAMES = (
    "Use",
    "Skill Get",
    "Utsusemi",
    "Relic",
    "Important",
    "Invalid",
)


@dataclass
class AnyItem(FromCsv):
    id: int
    name: str


ANY_ITEMS = AnyItem.from_csv_headerless(ITEM_NAMES_TABLE_PATH, 1)


@dataclass
class ItemExtraData(JsonListMixin):
    id: int
    limit: int | None = None
    icon: Element | None = None
    desc: str | None = None


ITEM_EXTRA_DATA = ItemExtraData.load_path(ITEM_ADDITIONAL_INFO_PATH)


def guess_icon(id: int) -> Element:
    if id in CON_BOOST_RANGE:
        return Element.Booster
    if id in RELICS_RANGE_1 or id in RELICS_RANGE_2:
        return Element.Relic
    if id in KEY_ITEMS_RANGE:
        return Element.KeyItem
    return Element.Misc


@dataclass
class Item:
    id: int
    name: str
    _limit: int | None
    icon: Element
    desc: str | None

    @property
    def metadata(self) -> dict:
        return ITEM_METADATA.get(self.id, {})

    @property
    def limit(self) -> int:
        if "limit" in self.metadata:
            return int(self.metadata["limit"])
        if self._limit:
            return self._limit
        elif self.id in ESSENCES_RANGE:
            return ESSENCE_ITEM_LIMIT
        elif self.id in RELICS_RANGE_1 or self.id in RELICS_RANGE_2:
            return RELICS_ITEM_LIMIT
        else:
            return DEFAULT_LIMIT

    @property
    def category(self) -> str:
        return str(self.metadata.get("category", "unknown"))

    @property
    def unique(self) -> bool:
        return bool(self.metadata.get("unique", self.limit == 1))

    @property
    def infinite(self) -> bool:
        return bool(self.metadata.get("infinite", False))

    @property
    def use_scene(self) -> int:
        return int(self.metadata.get("use_scene", -1))

    @property
    def use_scene_name(self) -> str:
        if self.use_scene < 0:
            return "Unknown"
        try:
            return USE_SCENE_NAMES[self.use_scene]
        except IndexError:
            return "Unknown"

    @property
    def item_kind(self) -> int:
        return int(self.metadata.get("item_kind", -1))

    @property
    def item_kind_name(self) -> str:
        if self.item_kind < 0:
            return "Unknown"
        try:
            return ITEM_KIND_NAMES[self.item_kind]
        except IndexError:
            return "Unknown"

    @property
    def offset(self) -> int:
        return ITEM_TABLE_OFFSET + self.id

    @classmethod
    def combined(cls) -> list[Self]:
        items = []
        for id in TOTAL_ITEM_RANGE:
            name = [
                it.name
                for it in ANY_ITEMS
                if it.id == id
            ][0]
            if is_unused(name):
                continue
            try:
                extra = [
                    j
                    for j in ITEM_EXTRA_DATA
                    if j.id == id
                ][0]
            except IndexError:
                limit = None
                icon = guess_icon(id)
                desc = None
            else:
                limit = extra.limit
                icon = extra.icon or guess_icon(id)
                desc = extra.desc
            items.append(cls(id, name, limit, icon, desc))
        return items


ITEMS = Item.combined()


def items_from(*args: range) -> list[Item]:
    return [
        item
        for item in ITEMS
        if any([
            item.id in r
            for r in args
        ])
    ]


def items_except_for(*args: range) -> list[Item]:
    return [
        item
        for item in ITEMS
        if not any([
            item.id in r
            for r in args
        ])
    ]


(ITEM_ID_MAP, ITEM_NAME_MAP) = make_maps(ITEMS)
