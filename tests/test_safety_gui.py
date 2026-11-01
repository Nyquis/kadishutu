from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from kadishutu.core.shared.file_handling import DecryptedSave
from kadishutu.data.demons import DEMON_ID_MAP

GAME_SAVE_SIZE = 0x6DC90


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def window(qapp: QApplication):
    from kadishutu.gui import mainwindow

    win = mainwindow.MainWindow()
    mainwindow.MAIN_WINDOW = win
    try:
        yield win
    finally:
        win.hide()
        win.deleteLater()
        qapp.processEvents()


@pytest.fixture
def editor(window):
    from kadishutu.gui.game_save.game_save import GameSaveEditorScreen

    raw = DecryptedSave(bytearray(GAME_SAVE_SIZE))
    raw.data[0x40:0x44] = b"GVAS"
    screen = GameSaveEditorScreen(Path("save.sav"), raw, window)
    window.stack_add(screen)
    return screen


def make_demon(editor):
    demon = editor.save.demons.in_slot(0)
    demon.demon_id = next(iter(DEMON_ID_MAP))
    return demon


def test_advanced_toggle_syncs_action_and_status_button(window):
    from kadishutu.gui.advanced import advanced_mode

    mode = advanced_mode()
    assert not mode.enabled
    assert window.advanced_button.text() == "Advanced: OFF"

    window.advanced_button.click()

    assert mode.enabled
    assert window.advanced_action.isChecked()
    assert window.advanced_button.isChecked()
    assert window.advanced_button.text() == "Advanced: ON"

    window.advanced_action.trigger()

    assert not mode.enabled
    assert not window.advanced_button.isChecked()
    assert window.advanced_button.text() == "Advanced: OFF"


def test_stats_current_is_locked_until_advanced(window, editor):
    from kadishutu.gui.advanced import advanced_mode
    from kadishutu.gui.game_save.stats import StatEditorScreen

    demon = make_demon(editor)
    screen = StatEditorScreen(demon.stats, demon.healable)
    window.stack_add(screen)
    screen.stack_refresh()

    current = screen.widgets["current"]["strength"]
    assert current.isReadOnly()

    advanced_mode().set_enabled(True)
    assert not current.isReadOnly()

    advanced_mode().set_enabled(False)
    assert current.isReadOnly()


def test_hp_one_preset_only_changes_healable_hp(window, editor):
    from kadishutu.gui.game_save.stats import StatEditorScreen

    demon = make_demon(editor)
    demon.stats.base.hp = 100
    demon.stats.changes.hp = 20
    demon.stats.current.hp = 120
    demon.healable.hp = 120
    demon.stats.base.mp = 50
    demon.stats.current.mp = 50
    demon.healable.mp = 50

    screen = StatEditorScreen(demon.stats, demon.healable)
    window.stack_add(screen)
    screen.stack_refresh()
    screen.hp_one_button.click()

    assert screen.widgets["healable"]["hp"].value() == 1
    assert screen.widgets["current"]["hp"].value() == 120
    assert not screen.hp_warning.isHidden()

    screen.on_apply_changes()

    assert demon.healable.hp == 1
    assert demon.stats.current.hp == 120


def test_demon_level_and_exp_are_locked_until_advanced(window, editor):
    from kadishutu.gui.advanced import advanced_mode
    from kadishutu.gui.game_save.demons import DemonEditorScreen

    demon = make_demon(editor)
    screen = DemonEditorScreen(demon, window)
    window.stack_add(screen)
    screen.stack_refresh()

    assert screen.level_box.isReadOnly()
    assert screen.exp_box.isReadOnly()
    assert not screen.level_note.isHidden()

    advanced_mode().set_enabled(True)

    assert not screen.level_box.isReadOnly()
    assert not screen.exp_box.isReadOnly()
    assert screen.level_note.isHidden()


def test_progression_covers_all_boost_items(window, editor):
    from kadishutu.data.items import ITEMS
    from kadishutu.gui.game_save.progression import ProgressionScreen

    screen = ProgressionScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()

    boost_ids = {item.id for item in ITEMS if item.is_boost}

    assert set(screen.item_boxes) == boost_ids
    assert {82, 98, 107, 108} <= set(screen.item_boxes)


def test_progression_grants_level_and_potential_items(window, editor):
    from kadishutu.gui.game_save.progression import ProgressionScreen

    screen = ProgressionScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()

    screen.add_items(screen.item_boxes[82], 2)
    screen.add_items(screen.item_boxes[107], 1)
    screen.on_apply_changes()

    assert editor.save.items.from_id(82).amount == 2
    assert editor.save.items.from_id(107).amount == 1


def test_progression_has_no_level_planner(window, editor):
    from kadishutu.gui.game_save.progression import ProgressionScreen

    screen = ProgressionScreen(window)
    window.stack_add(screen)
    screen.stack_refresh()

    assert not hasattr(screen, "target_box")
    assert not hasattr(screen, "plan_button")
    assert not hasattr(screen, "levels_needed")


def test_progression_uses_a_scroll_area(window, editor):
    from PySide6.QtWidgets import QScrollArea

    from kadishutu.gui.game_save.progression import ProgressionScreen

    screen = ProgressionScreen(window)
    window.stack_add(screen)

    assert isinstance(screen.scroll, QScrollArea)
    assert screen.scroll.widget() is screen.content
    assert screen.scroll.widgetResizable()


def test_progression_keeps_item_names_and_puts_mapping_in_tooltip(
    window, editor
):
    from kadishutu.gui.game_save.progression import ProgressionScreen

    screen = ProgressionScreen(window)
    window.stack_add(screen)

    aiding = screen.item_rows[107]
    calamity = screen.item_rows[108]
    assert aiding.label.text() == "Aiding Sutra"
    assert calamity.label.text() == "Calamity Sutra"
    assert "Support potential" in aiding.label.toolTip()
    assert "Ailment potential" in calamity.label.toolTip()
    assert "Item ID: 107" in aiding.label.toolTip()
    assert screen.item_rows[84].label.text() == "Health Balm"


def test_game_save_has_progression_category(editor):
    from kadishutu.gui.components import CategoryCard

    titles = {
        card.title_label.text()
        for card in editor.findChildren(CategoryCard)
    }

    assert "Progression" in titles



def test_compendium_flag_distinguishes_enemy_variants():
    from kadishutu.data.demons import DEMON_ID_MAP

    assert DEMON_ID_MAP[392].compendium is True
    assert DEMON_ID_MAP[570].compendium is False
    assert DEMON_ID_MAP[576].compendium is False
    assert DEMON_ID_MAP[762].compendium is False


def test_creation_hides_enemy_entries_in_safe_mode(window, editor):
    from PySide6.QtCore import Qt

    from kadishutu.data.demons import DEMON_ID_MAP
    from kadishutu.gui.game_save.demon_creation import DemonCreationScreen

    editor.save.team.max_stock = 5
    editor.save.team.demon_order = [0xFF] * 30
    for index in range(30):
        editor.save.demons.in_slot(index).demon_id = 0xFFFF

    screen = DemonCreationScreen(window)
    window.stack_add(screen)

    expected = sum(1 for demon in DEMON_ID_MAP.values() if demon.compendium)
    ids = {
        screen.species_list.item(index).data(Qt.ItemDataRole.UserRole)
        for index in range(screen.species_list.count())
    }
    assert screen.species_list.count() == expected
    assert 392 in ids
    assert 570 not in ids


def test_creation_shows_and_marks_enemy_entries_in_advanced(window, editor):
    from PySide6.QtCore import Qt

    from kadishutu.data.demons import DEMON_ID_MAP
    from kadishutu.gui.advanced import advanced_mode
    from kadishutu.gui.game_save.demon_creation import DemonCreationScreen

    editor.save.team.max_stock = 5
    editor.save.team.demon_order = [0xFF] * 30
    for index in range(30):
        editor.save.demons.in_slot(index).demon_id = 0xFFFF

    screen = DemonCreationScreen(window)
    window.stack_add(screen)
    advanced_mode().set_enabled(True)

    assert screen.species_list.count() == len(DEMON_ID_MAP)
    enemy_item = next(
        screen.species_list.item(index)
        for index in range(screen.species_list.count())
        if screen.species_list.item(index).data(Qt.ItemDataRole.UserRole) == 570
    )
    assert enemy_item.text().endswith("Enemy")
    assert "not a normal compendium" in enemy_item.toolTip()

    screen.species_list.setCurrentItem(enemy_item)
    assert screen.selected is not None
    assert screen.selected.id == 570
    assert not screen.preview_warning.isHidden()

    advanced_mode().set_enabled(False)
    assert screen.selected is None
    assert not screen.create_button.isEnabled()


def test_creation_screen_is_scrollable(window, editor):
    from kadishutu.gui.game_save.demon_creation import DemonCreationScreen

    screen = DemonCreationScreen(window)
    window.stack_add(screen)

    assert screen.scroll.widget() is screen.content
    assert screen.scroll.widgetResizable()


def test_demon_growth_table_shows_expected_gains(window, editor):
    from kadishutu.data.demons import DEMON_NAME_MAP
    from kadishutu.gui.game_save.demons import DemonEditorScreen

    demon = make_demon(editor)
    demon.demon_id = DEMON_NAME_MAP["Idun"].id
    screen = DemonEditorScreen(demon, window)
    window.stack_add(screen)
    screen.stack_refresh()

    current, weight, average = screen.growth_cells["magic"]
    assert current.text() == str(demon.stats.current.magic)
    assert weight.text() == "28.0%"
    assert average.text() == "+0.84"

    _, hp_growth, hp_average = screen.growth_cells["hp"]
    assert hp_growth.text() == "19"
    assert hp_average.text() == "~4.8"
    _, mp_growth, mp_average = screen.growth_cells["mp"]
    assert mp_growth.text() == "25"
    assert mp_average.text() == "~4.2"

    assert [header.text() for header in screen.hp_mp_headers] == [
        "Stat", "Current", "Growth", "Est. /level",
    ]
    assert [header.text() for header in screen.core_headers] == [
        "Stat", "Current", "Weight %", "Avg/level",
    ]
    assert "corpus estimate" in screen.growth_footer.text().lower()


def test_demon_screen_uses_neutral_separate_fields_badge(window, editor):
    from kadishutu.gui.game_save.demons import DemonEditorScreen

    demon = make_demon(editor)
    screen = DemonEditorScreen(demon, window)
    window.stack_add(screen)

    assert screen.separate_badge.text() == "separate fields"
    assert screen.separate_badge.property("risk") == "info"


def test_skill_ids_are_gated_by_global_advanced(window, editor):
    from kadishutu.gui.advanced import advanced_mode
    from kadishutu.gui.game_save.skills import SkillEditorScreen

    demon = make_demon(editor)
    screen = SkillEditorScreen(demon.skills, demon.innate_skill)
    window.stack_add(screen)
    screen.stack_refresh()

    row = screen.rows[1]
    assert row.skill_box.int_box.isHidden()

    advanced_mode().set_enabled(True)
    assert not row.skill_box.int_box.isHidden()

    advanced_mode().set_enabled(False)
    assert row.skill_box.int_box.isHidden()


def test_demon_screen_is_scrollable(window, editor):
    from PySide6.QtWidgets import QScrollArea

    from kadishutu.gui.game_save.demons import DemonEditorScreen

    demon = make_demon(editor)
    screen = DemonEditorScreen(demon, window)
    window.stack_add(screen)

    assert isinstance(screen.scroll_area, QScrollArea)
    assert screen.scroll_area.widget() is screen.content
    assert screen.scroll_area.widgetResizable()


def test_demon_growth_rows_keep_height_with_graphic(window, editor):
    from PySide6.QtGui import QColor, QPixmap
    from PySide6.QtWidgets import QApplication

    from kadishutu.gui.game_save.demons import DemonEditorScreen

    demon = make_demon(editor)
    screen = DemonEditorScreen(demon, window)
    window.stack_add(screen)
    screen.stack_refresh()

    pixmap = QPixmap(240, 240)
    pixmap.fill(QColor("#333333"))
    screen.demon_graphic.setPixmap(pixmap)
    screen.demon_graphic.setFixedSize(240, 240)
    screen.demon_graphic.show()

    window.resize(900, 620)
    window.show()
    app = QApplication.instance()
    assert app is not None
    app.processEvents()

    heights = [
        label.height()
        for cells in screen.growth_cells.values()
        for label in cells
    ]
    assert min(heights) > 5
    window.hide()
