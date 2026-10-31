
from collections.abc import Iterable

from kadishutu.data.items import (
    ITEM_ID_MAP,
    ITEM_NAME_MAP,
    ITEM_TABLE_OFFSET,
    Item,
)

from ..shared.editors import (
    BaseDynamicEditor,
    BaseStaticEditor,
    BaseStructAsSingularValueEditor,
)


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
