try:
    from PySide6 import __version__  # noqa: F401
except ImportError:
    import sys

    from .prompt_install import handle_no_qt
    sys.exit(handle_no_qt())

from .mainwindow import gui_main

__all__ = ["gui_main"]
