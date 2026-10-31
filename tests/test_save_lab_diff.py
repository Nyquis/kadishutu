import pytest

from tools.save_lab.diff import (
    Candidate,
    Change,
    decode_candidates,
    diff_runs,
    format_diff,
    group_changes,
)


def test_diff_runs_finds_single_change():
    runs = diff_runs(b"\x00\x01\x02", b"\x00\x05\x02")

    assert runs == [Change(1, b"\x01", b"\x05")]


def test_diff_runs_merges_consecutive_bytes():
    runs = diff_runs(b"\x00\x01\x02\x03", b"\x00\x05\x06\x03")

    assert runs == [Change(1, b"\x01\x02", b"\x05\x06")]


def test_diff_runs_rejects_different_sizes():
    with pytest.raises(ValueError, match="sizes differ"):
        diff_runs(b"\x00", b"\x00\x01")


def test_group_changes_merges_nearby_runs():
    before = b"\x00\x01\x01\x01\x02"
    after = b"\x00\x05\x01\x01\x06"

    groups = group_changes(before, after, gap=4)

    assert groups == [Change(1, before[1:5], after[1:5])]


def test_group_changes_keeps_far_runs_separate():
    before = b"\x00\x01\x00\x00\x00\x00\x02"
    after = b"\x00\x05\x00\x00\x00\x00\x06"

    groups = group_changes(before, after, gap=1)

    assert len(groups) == 2


def test_decode_candidates_includes_integer_and_bits():
    candidates = decode_candidates(Change(0, b"\x00", b"\x01"))

    assert Candidate("u8", 0, 1) in candidates
    assert any(candidate.kind == "bits" for candidate in candidates)


def test_decode_candidates_includes_utf16():
    before = "Rich".encode("utf-16-le")
    after = "Ricu".encode("utf-16-le")

    candidates = decode_candidates(Change(0, before, after))

    assert Candidate("utf16", "Rich", "Ricu") in candidates


def test_format_diff_reports_identical_saves():
    assert format_diff(b"\x00\x01", b"\x00\x01") == "no differences"
