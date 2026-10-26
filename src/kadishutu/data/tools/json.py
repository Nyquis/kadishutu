import json
from pathlib import Path
from typing import Self

from mashumaro.mixins.json import DataClassJSONMixin

from kadishutu.encodings import ENCODING


class JsonListMixin(DataClassJSONMixin):
    @classmethod
    def load_path(cls, path: Path, encoding: str = ENCODING) -> list[Self]:
        with path.open("rt", encoding=encoding) as file:
            return [cls.from_dict(item) for item in json.load(file)]
