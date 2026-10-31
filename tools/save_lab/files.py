from __future__ import annotations

import contextlib
import io
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kadishutu.core.shared.file_handling import DecryptedSave

_DECRYPTED_SAVE_CLASS = None


def _decrypted_save_class():
    global _DECRYPTED_SAVE_CLASS
    if _DECRYPTED_SAVE_CLASS is None:
        # Importing kadishutu also loads optional game tables and prints
        # warnings when they are absent. Keep the lab CLI output clean.
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            from kadishutu.core.shared.file_handling import DecryptedSave
        _DECRYPTED_SAVE_CLASS = DecryptedSave
    return _DECRYPTED_SAVE_CLASS


def load_save(path: Path) -> DecryptedSave:
    """Open an encrypted or decrypted save and return its decrypted form."""
    save_class = _decrypted_save_class()
    return save_class.auto_open(path)
