from ..shared.editors import AbsoulteDispatcher, U8Editor, U64Editor
from .affinities import AffinityManager
from .potentials import PotentialEditor
from .skills import InnateSkillEditor, SkillManager
from .stats import HealableEditor, StatBlockEditor


class DemonLikeEditor:
    stats: AbsoulteDispatcher[StatBlockEditor]
    healable: AbsoulteDispatcher[HealableEditor]
    level: U8Editor
    exp: U64Editor
    skills: AbsoulteDispatcher[SkillManager]
    affinities: AbsoulteDispatcher[AffinityManager]
    potentials: AbsoulteDispatcher[PotentialEditor]
    innate_skill: AbsoulteDispatcher[InnateSkillEditor]
