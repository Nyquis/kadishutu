try:
    from PySide6 import __version__  # noqa: F401
except ImportError:
    import sys

    from kadishutu._frozen import is_frozen, show_error
    if is_frozen():
        # A frozen build always ships Qt, so a missing Qt means the build is
        # broken. Report it without importing tkinter, which frozen builds
        # leave out.
        show_error(
            "kadishutu",
            "Something went wrong in the build process, "
            "making the GUI unusable."
        )
        sys.exit(1)

    from .prompt_install import handle_no_qt
    sys.exit(handle_no_qt())

from .mainwindow import gui_main

__all__ = ["gui_main"]
