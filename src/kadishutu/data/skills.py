from dataclasses import dataclass
from enum import Enum
from typing import Any

from .element_icons import Element
from .tools.csv import FromCsv, extract_from_str, extractor
from .tools.mapping import make_maps
from .tools.path import TABLES_PATH
from .tools.unused import is_unused

ACTION_SKILLS_PATH = TABLES_PATH / "SMT5V Skill Data Tables - ActionSkills.csv"
AUTO_SKILLS_PATH = TABLES_PATH / "SMT5V Skill Data Tables - AutoSkills.csv"


class SkillType(Enum):
    E_SKILL_TYPE_PHYSICAL_ATK = 0
    E_SKILL_TYPE_MAGIC_ATK = 1
    E_SKILL_TYPE_NODAMAGE_ATK = 2
    E_SKILL_TYPE_RECOVERY = 3
    E_SKILL_TYPE_AID = 4
    E_SKILL_TYPE_SUMMON = 7
    E_SKILL_TYPE_SPECIAL_ATK = 8
    E_SKILL_TYPE_CALL = 9
    E_SKILL_TYPE_EXTRA_ATK = 13
    E_SKILL_TYPE_PHYSICAL_RATE_ATK = 14


class SkillAttribute1(Enum):
    Physical = 0
    Fire = 1
    Ice = 2
    Electric = 3
    Force = 4
    Light = 5
    Dark = 6
    Almighty = 7
    Poison = 8
    Confusion = 10
    Charm = 11
    Sleep = 12
    Seal = 13
    Mirage = 20
    Invalid = 32


class Magatsuhi(Enum):
    # Or empty for not
    Player = 1
    Enemy = 0


class LearnSkillType(Enum):
    Default = 0
    Library = 1


SKILL_TYPE_NAMES = {
    SkillType.E_SKILL_TYPE_PHYSICAL_ATK: "Physical attack",
    SkillType.E_SKILL_TYPE_MAGIC_ATK: "Magic attack",
    SkillType.E_SKILL_TYPE_NODAMAGE_ATK: "Non-damaging attack",
    SkillType.E_SKILL_TYPE_RECOVERY: "Recovery",
    SkillType.E_SKILL_TYPE_AID: "Support",
    SkillType.E_SKILL_TYPE_SUMMON: "Summon",
    SkillType.E_SKILL_TYPE_SPECIAL_ATK: "Special attack",
    SkillType.E_SKILL_TYPE_CALL: "Call",
    SkillType.E_SKILL_TYPE_EXTRA_ATK: "Extra attack",
    SkillType.E_SKILL_TYPE_PHYSICAL_RATE_ATK: "Physical attack",
}
SCENE_NAMES = {
    "E_SKILL_ENABLE_SCENE_NOT_USE": "Not usable",
    "E_SKILL_ENABLE_SCENE_FIELD": "Field",
    "E_SKILL_ENABLE_SCENE_BATTLE": "Battle",
    "E_SKILL_ENABLE_SCENE_FACILITY": "Facility",
    "E_SKILL_ENABLE_SCENE_NOT_BATTLE": "Not battle",
    "E_SKILL_ENABLE_SCENE_NOT_FIELD": "Not field",
    "E_SKILL_ENABLE_SCENE_NOT_FACILITY": "Not facility",
    "E_SKILL_ENABLE_SCENE_ALL_SCENE": "All scenes",
}


def enum_name(text: str) -> str:
    return extractor(text)[1]


def skill_type_name(text: str) -> str:
    number, name = extractor(text)
    try:
        skill_type = SkillType(number)
    except ValueError:
        return name.removeprefix("E_SKILL_TYPE_").replace(
            "_", " "
        ).title()
    return SKILL_TYPE_NAMES.get(skill_type, name)


def scene_name(text: str) -> str:
    name = enum_name(text)
    return SCENE_NAMES.get(name, name)


def int_or_zero(text: str) -> int:
    try:
        return int(text)
    except (TypeError, ValueError):
        return 0


@dataclass
class ActionSkill(FromCsv):
    name: str
    id: int
    mp_cost: int
    skill_type: str
    attribute: str
    target: str
    scene: str
    base_power: int
    min_hits: int
    max_hits: int
    heal_power: int
    heal_percent: int
    icon: Element

    def mechanics_summary(self) -> str:
        parts = []
        if self.skill_type:
            parts.append(self.skill_type)
        if self.attribute and self.attribute != "Invalid":
            parts.append(self.attribute)
        if self.target:
            parts.append(self.target)
        if self.base_power:
            parts.append(f"{self.base_power} power")
        if self.max_hits > 1:
            if self.min_hits == self.max_hits:
                parts.append(f"{self.max_hits} hits")
            else:
                parts.append(f"{self.min_hits}-{self.max_hits} hits")
        if self.heal_power:
            parts.append(f"{self.heal_power} heal")
        if self.heal_percent:
            parts.append(f"{self.heal_percent}% heal")
        if self.mp_cost:
            parts.append(f"{self.mp_cost} MP")
        if self.scene:
            parts.append(self.scene)
        return " · ".join(parts)

    @classmethod
    def converter_data(cls):
        return {
            "name": {
                "field_name": "Skill Name",
            },
            "id": {
                "field_name": "Skill ID",
            },
            "mp_cost": {
                "field_name": "MP Cost",
            },
            "skill_type": {
                "field_name": "Skill Type",
                "converter": lambda _, text: skill_type_name(text),
            },
            "attribute": {
                "field_name": "Skill Attribute 1",
                "converter": lambda _, text: enum_name(text),
            },
            "target": {
                "field_name": "Target Selection Method",
                "converter": lambda _, text: enum_name(text),
            },
            "scene": {
                "field_name": "Usable in Battle or Field",
                "converter": lambda _, text: scene_name(text),
            },
            "base_power": {
                "field_name": "Base Power",
                "converter": lambda _, text: int_or_zero(text),
            },
            "min_hits": {
                "field_name": "Min Hits",
                "converter": lambda _, text: int_or_zero(text),
            },
            "max_hits": {
                "field_name": "Max Hits",
                "converter": lambda _, text: int_or_zero(text),
            },
            "heal_power": {
                "field_name": "Heal Power",
                "converter": lambda _, text: int_or_zero(text),
            },
            "heal_percent": {
                "field_name": "Heal %",
                "converter": lambda _, text: int_or_zero(text),
            },
            "icon": {
                "field_name": "Skill Icon",
                "converter": extract_from_str,
            },
        }


ACTION_SKILLS = ActionSkill.from_csv(ACTION_SKILLS_PATH, 3, "UTF-8")


@dataclass
class AutoSkill(FromCsv):
    name: str
    id: int

    @classmethod
    def converter_data(cls) -> dict[str, dict[str, Any]] | None:
        return {
            "name": {
                "field_name": "Name",
            },
            "id": {
                "field_name": "Skill ID",
            },
        }


AUTO_SKILLS = AutoSkill.from_csv(AUTO_SKILLS_PATH, 1)


@dataclass
class Skill:
    name: str
    id: int
    mp_cost: int
    icon: Element
    summary: str


NEW_SKILLS: list[Skill] = []


for action_skill in ACTION_SKILLS:
    if is_unused(action_skill.name):
        continue
    NEW_SKILLS.append(Skill(
        action_skill.name, action_skill.id, action_skill.mp_cost,
        action_skill.icon, action_skill.mechanics_summary()
    ))


for auto_skill in AUTO_SKILLS:
    if is_unused(auto_skill.name):
        continue
    NEW_SKILLS.append(Skill(
        auto_skill.name, auto_skill.id, 0, Element.Passive, "Passive skill"
    ))


NEW_SKILLS.sort(key=lambda x: x.id)


(SKILL_ID_MAP, SKILL_NAME_MAP) = make_maps(NEW_SKILLS)
