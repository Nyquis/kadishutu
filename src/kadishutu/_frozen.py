"""Tweaks and helpers that only apply to standalone (frozen) builds.

PyInstaller runs this module as a runtime hook (``src/pyinstaller_runtime.py``
just calls :func:`apply`).

Keep the import cheap: it runs before the GUI is loaded. In particular this
module must not import ``kadishutu.gui``, which would pull in Qt.
"""
from __future__ import annotations

import os
import sys

import kadishutu.tools.depinstall
import kadishutu.tools.depinstall.generic


def is_frozen() -> bool:
    return hasattr(sys, "frozen") or bool(os.getenv("KADISHUTU_FROZEN"))


def show_error(title: str, message: str) -> None:
    """Report a startup failure without pulling in tkinter."""
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
    else:
        print(f"{title}: {message}", file=sys.stderr)


def _likelyness() -> float:
    return 0.0


def apply() -> None:
    """Stop a frozen build from trying to pipx-install its own dependencies."""
    generic = kadishutu.tools.depinstall.generic
    package = kadishutu.tools.depinstall

    for handler in generic.INSTALL_HANDLERS:
        handler.likelyness = staticmethod(_likelyness)  # type: ignore[method-assign]

    generic.INSTALL_HANDLERS = []

    def get_install_handler():
        raise NotImplementedError(
            "Install handlers are unsupported in frozen builds"
        )

    generic.get_install_handler = get_install_handler  # type: ignore[assignment]
    # The package re-exports the function, and that name is bound when the
    # package is imported, which happens before this module runs.
    package.get_install_handler = get_install_handler  # type: ignore[assignment]
