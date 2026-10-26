import os
import sys
from collections.abc import Callable
from enum import Enum, auto
from typing import NoReturn

from kadishutu.tools.depinstall import get_install_handler


class Result(Enum):
    Success = 0
    Rejected = auto()


def tk_frontend(install_func: Callable[[], None]) -> Result:
    from tkinter import messagebox
    if not messagebox.askyesno(
        "kadishutu: Additional dependencies",
        "The GUI can't function without additional dependencies. "
        "Do you want to install them?"
    ):
        return Result.Rejected
    try:
        install_func()
    except Exception as e:
        messagebox.showerror(
            "kadishutu",
            f"The following error has occurred: {repr(e)}"
        )
        raise e
    messagebox.showinfo(
        "kadishutu",
        "Installed! The app should restart automatically."
    )
    return Result.Success


def reexec_self() -> NoReturn:
    os.execl(sys.executable, *sys.orig_argv)


def handle_no_qt() -> int:
    print("PySide6 is not installed.")
    try:
        handler = get_install_handler()
    except AssertionError:
        print("Please install it before running the gui.")
        return 1
    handler_frontend = tk_frontend
    res = handler_frontend(lambda: handler.install_group("gui"))
    if res == Result.Success:
        reexec_self()
    return 1
