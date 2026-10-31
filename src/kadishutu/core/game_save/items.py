
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from kadishutu.data.items import (
    ITEM_ID_MAP,
    ITEM_NAME_MAP,
    ITEM_TABLE_OFFSET,
    TOTAL_ITEM_RANGE,
    Item,
)

from ..shared.editors import (
    BaseDynamicEditor,
    BaseStaticEditor,
    BaseStructAsSingularValueEditor,
)


@dataclass(frozen=True)
class ItemIssue:
    item_id: int
    amount: int
    kind: str

    @property
    def item(self) -> Item | None:
        return ITEM_ID_MAP.get(self.item_id)

    @property
    def message(self) -> str:
        if self.kind == "over_limit":
            item = self.item
            assert item is not None
            return (
                f"{item.name} (#{self.item_id}) has {self.amount}, "
                f"but its limit is {item.limit}."
            )
        return f"Unused item ID {self.item_id} has amount {self.amount}."


def item_issues(data: Sequence[int]) -> list[ItemIssue]:
    issues: list[ItemIssue] = []
    for item_id in TOTAL_ITEM_RANGE:
        amount = data[ITEM_TABLE_OFFSET + item_id]
        if amount == 0:
            continue
        item = ITEM_ID_MAP.get(item_id)
        if item is None:
            issues.append(ItemIssue(item_id, amount, "unused_id"))
        elif amount > item.limit:
            issues.append(ItemIssue(item_id, amount, "over_limit"))
    return issues


class ItemEditor(BaseDynamicEditor, BaseStructAsSingularValueEditor):
    struct = "<B"

    def __init__(self, *args, meta: Item | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta = meta

    @property
    def meta(self) -> Item:
        if not self._meta:
            self._meta = ITEM_ID_MAP[self.offset - ITEM_TABLE_OFFSET]
        return self._meta

    @property
    def name_table(self) -> dict[int, str]:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.meta.name

    def get_amount(self) -> int:
        return self.value

    def set_amount(self, v: int):
        self.value = v

    amount = property(get_amount, set_amount)

    @property
    def limit(self) -> int:
        return self.meta.limit


class ItemManager(BaseStaticEditor):
    offset = 0x4c72

    def at_offset(self, offset: int, *args, **kwargs):
        return self.dispatch(ItemEditor, offset, *args, **kwargs)

    def from_meta(self, item: Item):
        return self.at_offset(item.offset, meta=item)

    def from_id(self, id: int):
        return self.from_meta(ITEM_ID_MAP[id])

    def from_name(self, name: str):
        return self.from_meta(ITEM_NAME_MAP[name])

    def validate(self) -> list[ItemIssue]:
        return item_issues(self.data)

    def set_amount(
        self,
        item: Item,
        amount: int,
        *,
        clamp: bool = True,
    ) -> ItemEditor:
        editor = self.from_meta(item)
        if clamp:
            amount = min(amount, editor.limit)
        editor.amount = amount
        return editor

    def set_all(
        self,
        items: Iterable[Item],
        amount: int,
        *,
        clamp: bool = True,
    ) -> None:
        for item in items:
            self.set_amount(item, amount, clamp=clamp)

    def max_all(self, items: Iterable[Item]) -> None:
        for item in items:
            editor = self.from_meta(item)
            editor.amount = editor.limit

    def clear_all(self, items: Iterable[Item]) -> None:
        for item in items:
            self.from_meta(item).amount = 0
