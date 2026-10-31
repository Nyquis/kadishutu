
from kadishutu.data.skills import SKILL_ID_MAP, LearnSkillType, Skill

from ..shared.editors import (
    BaseDynamicEditor,
    BaseStructAsFieldEditor,
    EnumEditor,
    U32Editor,
)


class SkillEditor(BaseDynamicEditor, BaseStructAsFieldEditor):
    struct = "<I"
    _meta: Skill | None = None

    @property
    def meta(self) -> Skill:
        if not self._meta:
            self._meta = SKILL_ID_MAP[self.id]
        return self._meta

    learn_type = EnumEditor(0, LearnSkillType, "<I")
    id = U32Editor(4)

    @property
    def name(self) -> str:
        return SKILL_ID_MAP[self.id].name


class SkillManager(BaseDynamicEditor, BaseStructAsFieldEditor):
    struct = "<II"

    def slot(self, no: int) -> SkillEditor:
        return self.field_dispatch(SkillEditor, no)

    def __getitem__(self, indices: int | tuple[int, ...]) -> SkillEditor:
        if isinstance(indices, tuple):
            raise NotImplementedError
        return self.slot(indices)


class InnateSkillEditor(SkillEditor):
    learn_type = None
    id = U32Editor(0)
