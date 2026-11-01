import pytest

from kadishutu.data.demons import DEMON_NAME_MAP, DEMONS
from kadishutu.data.leveling import (
    DEMON_EXP_MULTIPLIERS,
    demon_exp_multiplier,
    demon_exp_to_next,
    exp_progress,
    load_leveling_data,
    nahobino_exp_to_next,
    nahobino_stats,
)


def test_nahobino_level_four_matches_a_real_save():
    stats = nahobino_stats(4)

    assert (stats.hp, stats.mp) == (55, 70)
    assert (stats.strength, stats.vitality) == (5, 6)
    assert (stats.magic, stats.agility, stats.luck) == (5, 6, 6)


def test_nahobino_level_fifty_five_matches_a_real_save():
    stats = nahobino_stats(55)

    assert (stats.hp, stats.mp) == (328, 257)
    assert (
        stats.strength,
        stats.vitality,
        stats.magic,
        stats.agility,
        stats.luck,
    ) == (36, 36, 36, 36, 37)


def test_nahobino_table_covers_levels_one_to_max():
    data = load_leveling_data()

    assert sorted(data.stats) == list(range(1, data.max_level + 1))
    assert data.max_level == 150


def test_nahobino_hp_and_mp_never_decrease():
    data = load_leveling_data()
    previous = data.stats_at(1)
    for level in range(2, data.max_level + 1):
        current = data.stats_at(level)
        assert current.hp >= previous.hp
        assert current.mp >= previous.mp
        previous = current


def test_nahobino_exp_curve_edges():
    assert nahobino_exp_to_next(1) == 32
    assert nahobino_exp_to_next(55) == 140518
    assert nahobino_exp_to_next(149) == 727576
    assert nahobino_exp_to_next(150) is None
    assert nahobino_exp_to_next(0) is None


def test_nahobino_stats_rejects_unknown_level():
    with pytest.raises(ValueError, match="outside the table range"):
        nahobino_stats(0)
    with pytest.raises(ValueError, match="outside the table range"):
        nahobino_stats(151)


def test_demon_exp_multiplier_by_levels_above_base():
    assert demon_exp_multiplier(55, 55) == 1.5
    assert demon_exp_multiplier(50, 55) == 1.5
    assert demon_exp_multiplier(56, 55) == 2.0
    assert demon_exp_multiplier(57, 55) == 2.57
    assert demon_exp_multiplier(100, 55) == 10.0
    assert demon_exp_multiplier(55, 55) == DEMON_EXP_MULTIPLIERS[0]


def test_demon_exp_requirement_uses_nahobino_curve():
    scathach = DEMON_NAME_MAP["Scathach"]

    assert demon_exp_to_next(55, scathach.level) == int(140518 * 1.5)


def test_exp_progress_is_clamped():
    assert exp_progress(0, 100) == 0.0
    assert exp_progress(50, 100) == 0.5
    assert exp_progress(150, 100) == 1.0
    assert exp_progress(10, None) is None
    assert exp_progress(10, 0) is None


def test_demon_growth_fields_are_parsed():
    idun = DEMON_NAME_MAP["Idun"]

    assert idun.growth.hp == 19
    assert idun.growth.mp == 25
    assert idun.growth.strength == 13
    assert idun.growth.vitality == 16
    assert idun.growth.magic == 28
    assert idun.growth.agility == 21
    assert idun.growth.luck == 22
    assert idun.growth.total == 100


def test_demon_growth_components_match_total():
    for demon in DEMONS:
        growth = demon.growth
        components = (
            growth.strength
            + growth.vitality
            + growth.magic
            + growth.agility
            + growth.luck
        )
        assert components == growth.total, demon.name


def test_expected_demon_stat_gain():
    from kadishutu.data.leveling import expected_stat_gain

    assert expected_stat_gain(28, 100) == pytest.approx(0.84)
    assert expected_stat_gain(26, 102) == pytest.approx(3 * 26 / 102)
    assert expected_stat_gain(0, 100) == 0.0
    assert expected_stat_gain(20, 0) == 0.0
