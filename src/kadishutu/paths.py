from os import getenv
from pathlib import Path

from platformdirs import user_data_dir

from kadishutu.tools.singleton import AbstractSingleton

APP_NAME = "kadishutu"

PORTABLE_PREFIX = "_appdata"


class AppDirs(AbstractSingleton):
    _data_path: Path

    def _init_portable(self):
        self._data_path = Path.cwd() / PORTABLE_PREFIX / "data" / APP_NAME

    def _init_platform(self):
        self._data_path = Path(user_data_dir(APP_NAME, appauthor=False))

    @property
    def data_path(self):
        return self._data_path

    def __init__(self):
        if getenv("PORTABLE_APP"):
            self._init_portable()
        else:
            self._init_platform()


APPDIRS = AppDirs()
