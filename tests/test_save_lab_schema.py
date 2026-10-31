import pytest

from tools.save_lab.schema import (
    GAME_SAVE_REGIONS,
    SYS_SAVE_REGIONS,
    Coverage,
    Region,
    coverage,
    format_coverage,
    regions_for_class,
)


def test_coverage_reports_unknown_gaps():
    regions = (Region(0, 4, "a"), Region(6, 8, "b"))

    result = coverage(regions, 10)

    assert result.covered == 6
    assert result.ranges == ((0, 4), (6, 8))
    assert result.unknown == ((4, 6), (8, 10))
    assert result.percent == pytest.approx(60.0)


def test_coverage_merges_overlapping_regions():
    regions = (Region(0, 4, "a"), Region(2, 6, "b"))

    result = coverage(regions, 10)

    assert result.ranges == ((0, 6),)
    assert result.unknown == ((6, 10),)


def test_coverage_clips_regions_to_file_size():
    result = coverage((Region(0, 20, "a"),), 10)

    assert result.ranges == ((0, 10),)
    assert result.covered == 10
    assert result.unknown == ()


def test_regions_for_class_selects_syssave():
    assert regions_for_class("SystemSaveObject") == SYS_SAVE_REGIONS
    assert regions_for_class("SaveObject") == GAME_SAVE_REGIONS


def test_game_regions_fit_in_save_size():
    result = coverage(GAME_SAVE_REGIONS, 0x6DC90)

    assert result.covered > 0
    assert result.covered < result.size
    assert result.unknown


def test_format_coverage_mentions_unknown_ranges():
    result = Coverage(
        size=10,
        covered=4,
        ranges=((0, 4),),
        unknown=((4, 10),),
    )

    text = format_coverage(result, label="test")

    assert "4/10 bytes" in text
    assert "unknown ranges" in text
    assert "0x000004-0x00000a" in text


def test_region_rejects_invalid_bounds():
    with pytest.raises(ValueError, match="invalid region"):
        Region(5, 4, "bad")
