from kadishutu.data.endings import (
    CANON_DESCRIPTIONS,
    ENDING_INFOS,
    ENDING_ROUTES,
)


def test_ending_metadata_is_complete():
    assert len(ENDING_INFOS) == 6
    assert {info.flag for info in ENDING_INFOS} == {
        0x01,
        0x02,
        0x04,
        0x08,
        0x10,
        0x20,
    }
    assert {info.route for info in ENDING_INFOS} == set(ENDING_ROUTES)
    assert all(info.label for info in ENDING_INFOS)
    assert all(info.description for info in ENDING_INFOS)
    assert all(info.canon.startswith("Canon of ") for info in ENDING_INFOS)
    assert all(" — " in info.full_label for info in ENDING_INFOS)
    assert set(CANON_DESCRIPTIONS) == set(ENDING_ROUTES)


def test_ending_labels_are_human_readable():
    labels = {info.flag: info.label for info in ENDING_INFOS}

    assert labels[0x01] == "Neutral"
    assert labels[0x08] == "True Neutral (Secret)"
    assert labels[0x10] == "Law"
    assert labels[0x20] == "Chaos"
