import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def reset_advanced_mode():
    """Keep GUI tests independent of the user's saved advanced-mode setting."""
    from kadishutu.gui.advanced import advanced_mode

    mode = advanced_mode()
    previous = mode.enabled
    mode.set_enabled(False)
    try:
        yield
    finally:
        mode.set_enabled(previous)

