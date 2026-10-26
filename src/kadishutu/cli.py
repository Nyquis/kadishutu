import contextlib
import importlib
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import FunctionType, MethodType
from typing import Any

from kadishutu.core.game_save import GameSaveEditor
from kadishutu.core.shared.file_handling import DecryptedSave, EncryptedSave


def cmd_decrypt(args):
    source = args.source
    destination = args.destination or source
    print(f"Opening {source}")
    savefile = EncryptedSave.open(source)
    if savefile.is_save_decrypted():
        raise ValueError("The save file is already decrypted.")
    print("Decrypting...")
    savefile = savefile.decrypt()
    if not savefile.is_save_decrypted():
        raise ValueError("The save file decryption failed.")
    if not savefile.hash_validate():
        raise ValueError("The save file's hash is not valid.")
    print(f"Saving file to {destination}")
    savefile.save(destination)


def cmd_encrypt(args):
    source = args.source
    destination = args.destination or source
    print(f"Opening {source}")
    savefile = DecryptedSave.open(source)
    if not savefile.is_save_decrypted():
        raise ValueError("The save file is already encrypted.")
    if savefile.hash_validate():
        print("Contained hash is valid.")
    elif getattr(args, "update_hash", False):
        print("Updating contained hash.")
        savefile.hash_update()
    else:
        raise ValueError(
            "The save file's hash is not valid. "
            "Re-run with \"--update-hash\"."
        )
    print(f"Saving file to {destination}")
    savefile.save_finished(destination)


def cmd_inspect(args):
    path = args.file
    savefile = DecryptedSave.auto_open(path)
    if (not getattr(args, "ignore_hash", False) and
        not savefile.hash_validate()):
        raise ValueError(
            "The save file's hash is not valid. "
            "Re-run with \"--ignore-hash\" to inspect it anyway."
        )
    game = GameSaveEditor(savefile)
    this = game
    skip = 0
    # JaNkTaStIc!
    for i, txt in enumerate(args.selector):
        if skip:
            skip -= 1
            continue
        this = this.__getattribute__(txt)
        if isinstance(this, (MethodType, FunctionType)):
            arglist = this.__annotations__
            with contextlib.suppress(KeyError):
                arglist.pop("return")
            skip = len(arglist)
            arglistd = []
            for k, v in enumerate(arglist.values()):
                tx = args.selector[i + k + 1]
                arglistd.append(v(tx))
            this = this(*arglistd)
            continue
    #if isinstance(this, property):
    #    this = this.getter()
    this: Any
    # NOTE: Currently broken for properties
    if hasattr(this, "offset"):
        print(f"Offset: 0x{this.offset:x}")
    #raise ValueError("Offset not available")
    print(this)


def cmd_run_script(args):
    path: Path = args.file
    script_path: Path = args.script.absolute()
    savefile = DecryptedSave.auto_open(path)
    if (not getattr(args, "ignore_hash", False) and
        not savefile.hash_validate()):
        raise ValueError(
            "The save file's hash is not valid. "
            "Re-run with \"--ignore-hash\" to run the script anyway."
        )
    #script = importlib.import_module(str(script_path))
    loader = SourceFileLoader("script", str(script_path))
    spec = importlib.util.spec_from_loader("script", loader)
    if spec is None:
        raise ValueError(f"Could not load script {script_path}")
    script = importlib.util.module_from_spec(spec)
    loader.exec_module(script)
    #if not hasattr(script, "main"):
    #    raise ValueError("The main function is not defined")
    #assert script.main
    #if not isinstance(script.main, FunctionType):
    #    raise ValueError("main is not a function")
    script.main(path, savefile, args.rest_of_args)


def cmd_update_hash(args):
    path = args.file
    savefile = DecryptedSave.open(path)
    if not savefile.is_save_decrypted():
        raise ValueError("The save file is encrypted; decrypt it first.")
    if savefile.hash_validate():
        print("The hash is already valid.")
        return
    savefile.hash_update()
    savefile.save(path)
