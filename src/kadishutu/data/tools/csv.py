import csv
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Self,
    TypeVar,
)


def csvread_headerless(
    path: Path,
    skip_lines: int = 0,
    encoding: str | None = None,
) -> list[list[str]]:
    with open(path, encoding=encoding) as file:
        while skip_lines > 0:
            if file.read(1) == "\n":
                skip_lines -= 1
        return [
            i
            for i in csv.reader(file)
        ]


def csvread(
    path: Path,
    skip_lines: int = 0,
    encoding: str | None = None,
) -> list[dict[str, str]]:
    with open(path, encoding=encoding) as file:
        while skip_lines > 0:
            if file.read(1) == "\n":
                skip_lines -= 1
        return [
            i
            for i in csv.DictReader(file)
        ]


@dataclass
class FromCsv:
    @classmethod
    def filter_data(cls, item: dict[str, str]) -> bool:
        return True

    @classmethod
    def converter_data(cls) -> dict[str, dict[str, Any]] | None:
        ...

    @classmethod
    def from_csv_headerless(
        cls,
        path: Path,
        skip_lines: int = 0,
        encoding: str | None = None,
    ) -> list[Self]:
        csv_data = csvread_headerless(path, skip_lines)
        res = []
        conversion_info = cls.converter_data()
        for item in csv_data:
            target_item = []
            for i, (k, v) in enumerate(cls.__annotations__.items()):
                if not conversion_info:
                    k_info = {}
                else:
                    try:
                        k_info = conversion_info[k]
                    except KeyError:
                        k_info = {}
                value = item[i]
                try:
                    value = k_info["converter"](v, value)
                except KeyError:
                    value = v(value)
                target_item.append(value)
            res.append(target_item)
        return [
            cls(*i)
            for i in res
        ]

    @classmethod
    def from_csv(
        cls,
        path: Path,
        skip_lines: int = 0,
        encoding: str | None = None,
    ) -> list[Self]:
        csv_data = csvread(path, skip_lines)
        res = []
        conversion_info = cls.converter_data()
        for item in csv_data:
            if not cls.filter_data(item):
                continue
            target_item = {}
            for k, v in cls.__annotations__.items():
                if not conversion_info:
                    k_info = {}
                else:
                    try:
                        k_info = conversion_info[k]
                    except KeyError:
                        k_info = {}
                try:
                    fun: Callable[[dict[str, str]], Any] = k_info["eval"]
                except KeyError:
                    pass
                else:
                    value = fun(item)
                    target_item[k] = value
                    continue
                try:
                    value = item[k_info["field_name"]]
                except KeyError:
                    value = item[k]
                try:
                    value = k_info["converter"](v, value)
                except KeyError:
                    value = v(value)
                target_item[k] = value
            res.append(target_item)
        return [
            cls(**i)
            for i in res
        ]


EXTRACTOR_RE = re.compile(r"(\d+) \((.+)\)")


def extractor(text: str) -> tuple[int, str]:
    res = EXTRACTOR_RE.match(text)
    assert res
    g = res.groups()
    return (int(g[0]), g[1])


REVERSE_EXTRACTOR_RE = re.compile(r"(.+) \((\d+)\)")


def reverse_extractor(text: str) -> tuple[str, int]:
    res = REVERSE_EXTRACTOR_RE.match(text)
    assert res
    g = res.groups()
    return (g[0], int(g[1]))


T = TypeVar("T", bound=Enum)


def extract_from_str(cls: type[T], text: str) -> T:
    (num, _) = extractor(text)
    return cls(num)
