import re
import sys

from .generic_early import CommandInstallHandler

PIPX_VENV_RE = re.compile(r"[\\/]pipx[\\/]venvs[\\/]([^\\/]+)[\\/]")


def _argv0() -> str:
    return getattr(sys, "orig_argv", [sys.executable])[0]


class PipxInstallHandler(CommandInstallHandler):
    IDENT = "pipx"

    @classmethod
    def likelyness(cls) -> float:
        if PIPX_VENV_RE.search(_argv0()):
            return 80.0
        else:
            return 0.0

    @property
    def install_venv(self) -> str:
        m = PIPX_VENV_RE.search(_argv0())
        assert m, "Pipx virtual environment regex match failed"
        return m.group(1)

    def install(self, deps: list[str]):
        self.run([
            "inject", self.install_venv, *deps,
        ])
