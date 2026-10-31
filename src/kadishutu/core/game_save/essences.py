from enum import IntFlag

from kadishutu.core.shared.editors import EnumEditor
from kadishutu.data.items import ESSENCES_RANGE, ITEM_TABLE_OFFSET, Item

from .items import ItemEditor, ItemManager


class EssenceMetadata(IntFlag):
    Bit0 = 1
    New = 2
    Owned = 4
    Bit3 = 8
    Used = 16
    Absent = Used
    Bit5 = 32
    Bit6 = 64
    Bit7 = 128

    @classmethod
    def all(cls):
        return cls(0xff)

    @classmethod
    def known_bits(cls):
        return cls.New | cls.Owned | cls.Used

    @classmethod
    def new_blockbits(cls):
        return [cls.Owned, cls.Used]


class EssenceEditor(ItemEditor):
    metadata = EnumEditor(0x380, EssenceMetadata)

    @property
    def have(self) -> bool:
        return self.amount != 0

    @have.setter
    def have(self, value: bool):
        if value:
            self.amount = 1
            if not (self.metadata & EssenceMetadata.known_bits()):
                self.metadata |= EssenceMetadata.New
        else:
            self.amount = 0

    @property
    def used(self) -> bool:
        return bool(self.metadata & EssenceMetadata.Used)

    @used.setter
    def used(self, value: bool):
        if value:
            self.metadata |= EssenceMetadata.Used
        else:
            self.metadata &= ~EssenceMetadata.Used

    def is_absent(self) -> bool:
        return self.used

    def is_owned(self) -> bool:
        return self.have

    def is_new(self) -> bool:
        for i in EssenceMetadata.new_blockbits():
            if self.metadata & i:
                return False
        return bool(self.metadata & EssenceMetadata.New)

    def give(self, new: bool = False):
        self.have = True
        if new:
            self.metadata &= ~(EssenceMetadata.Owned | EssenceMetadata.Used)
            self.metadata |= EssenceMetadata.New

    def take(self):
        self.have = False


class EssenceManager(ItemManager):
    @staticmethod
    def _return(r: ItemEditor) -> EssenceEditor:
        assert isinstance(r, EssenceEditor)
        return r

    def at_offset(self, offset: int, *args, **kwargs):
        assert offset - ITEM_TABLE_OFFSET in ESSENCES_RANGE
        return self.dispatch(EssenceEditor, offset, *args, **kwargs)

    def from_meta(self, item: Item) -> EssenceEditor:
        return self._return(super().from_meta(item))

    def from_id(self, id: int) -> EssenceEditor:
        return self._return(super().from_id(id))

    def from_name(self, name: str) -> EssenceEditor:
        return self._return(super().from_name(name))
