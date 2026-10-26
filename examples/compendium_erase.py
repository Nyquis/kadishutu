# SELF-REEXEC HEADER
# DO NOT EDIT
from pathlib import Path
from typing import NoReturn


def run_through_kadishutu() -> NoReturn:
    import os
    import sys
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    script = sys.argv[0]
    file: Path = args.file
    os.execlp("kadishutu", "kadishutu", "run_script", script, str(file))


if __name__ == "__main__":
    run_through_kadishutu()
# EDIT FROM HERE



from kadishutu import DecryptedSave, GameSaveEditor
from kadishutu.core.game_save.compendium import COMPENDIUM_ENTRY_SIZE
from kadishutu.tools.eprint import eprint


def erase(game: GameSaveEditor, offset: int, size: int):
    empty = [0] * size
    game.data[offset:offset + size] = empty


def erase_demons(game: GameSaveEditor):
    demons = game.demons
    for i in game.team.demon_order:
        demon = demons.in_slot(i)
        if demon.is_free:
            continue
        try:
            name = demon.meta.name
        except KeyError:
            name = f"??? ({i})"
        print("Erasing demon:", name)
        game.erase_demon(i)


def erase_compendium(game: GameSaveEditor):
    comp = game.compendium
    for i in range(400):
        demon = comp.from_id(i)
        if not demon.registered:
            continue
        try:
            name = demon.meta.name
        except KeyError:
            name = "??? (i)"
        print("De-registering from compendium:", name)
        demon.registered = False
        erase(game, demon.offset, COMPENDIUM_ENTRY_SIZE)


def modify(game: GameSaveEditor):
    erase_demons(game)
    erase_compendium(game)


def main(path: Path, file: DecryptedSave, args: list[str]):
    game = GameSaveEditor(file)
    non_clear = False
    for arg in args:
        if arg == "nonclear":
            non_clear = True
    if not game.clear_flag and not non_clear:
        eprint("Not a clear save file. Please, complete the game first.")
        eprint('Pass "nonclear" to override this.')
        exit(1)
    print("THIS SCRIPT WILL ERASE ALL DEMONS, BOTH SUMMONED AND IN THE COMPENDIUM")
    ans = input("Continue [y/N]: ")
    if ans.lower() != "y":
        exit(1)
    modify(game)
    file.save_finished(path)
