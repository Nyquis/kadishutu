from __future__ import annotations

import argparse
from pathlib import Path

from .diff import format_diff
from .files import load_save
from .gvas import GvasError, find_gvas_offset, parse_gvas_header
from .schema import coverage, format_coverage, regions_for_class

SAVE_SIZES = {
    "SaveObject": 0x6DC90,
    "SystemSaveObject": 0x12E0,
}


def _header(path: Path):
    save = load_save(path)
    data = bytes(save.data)
    offset = find_gvas_offset(data)
    return save, parse_gvas_header(data, offset)


def cmd_gvas(args: argparse.Namespace) -> int:
    save, header = _header(args.path)
    print(f"file: {args.path}")
    print(f"size: {len(save.data)} (0x{len(save.data):x})")
    print(
        f"GVAS offset: 0x{header.offset:x} "
        f"save_version={header.save_version} "
        f"package_version={header.package_version}"
    )
    print(
        f"engine: {header.engine} "
        f"branch={header.engine.branch!r}"
    )
    print(
        f"custom_version_format={header.custom_version_format} "
        f"custom_version_count={header.custom_version_count}"
    )
    print(f"class_name: {header.class_name!r}")
    print(f"payload_offset: 0x{header.payload_offset:x}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    before_save = load_save(args.before)
    after_save = load_save(args.after)
    before = bytes(before_save.data)
    after = bytes(after_save.data)
    if len(before) != len(after):
        print(
            f"save sizes differ: 0x{len(before):x} != 0x{len(after):x}"
        )
        return 1
    print(f"before: {args.before}")
    print(f"after:  {args.after}")
    print(format_diff(before, after, gap=args.gap, limit=args.limit))
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    save, header = _header(args.path)
    regions = regions_for_class(header.class_name)
    result = coverage(regions, len(save.data))
    print(f"file: {args.path}")
    print(f"class: {header.class_name}")
    print(format_coverage(result, label=header.class_name))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    save, header = _header(args.path)
    checks: list[tuple[str, bool, str]] = []

    checks.append((
        "hash",
        save.hash_validate(),
        "SHA-1 of data[0x40:] matches",
    ))
    expected_size = SAVE_SIZES.get(header.class_name)
    if expected_size is None:
        checks.append((
            "size",
            False,
            f"unknown save class {header.class_name!r}",
        ))
    else:
        checks.append((
            "size",
            len(save.data) == expected_size,
            f"expected 0x{expected_size:x}, got 0x{len(save.data):x}",
        ))
    checks.append((
        "gvas",
        header.offset == 0x40,
        f"GVAS at 0x{header.offset:x}",
    ))

    failed = False
    for name, ok, detail in checks:
        mark = "OK" if ok else "FAIL"
        print(f"{mark:4s} {name}: {detail}")
        failed = failed or not ok
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="save_lab",
        description="Development-only SMT5V save inspection tools.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gvas_parser = subparsers.add_parser(
        "gvas",
        help="parse and print the GVAS header",
    )
    gvas_parser.add_argument("path", type=Path)
    gvas_parser.set_defaults(func=cmd_gvas)

    diff_parser = subparsers.add_parser(
        "diff",
        help="annotate byte differences between two saves",
    )
    diff_parser.add_argument("before", type=Path)
    diff_parser.add_argument("after", type=Path)
    diff_parser.add_argument(
        "--gap",
        type=int,
        default=8,
        help="merge changes separated by at most this many bytes",
    )
    diff_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="maximum number of changed regions to print",
    )
    diff_parser.set_defaults(func=cmd_diff)

    coverage_parser = subparsers.add_parser(
        "coverage",
        help="report known and unknown byte ranges",
    )
    coverage_parser.add_argument("path", type=Path)
    coverage_parser.set_defaults(func=cmd_coverage)

    validate_parser = subparsers.add_parser(
        "validate",
        help="check size, class, and hash",
    )
    validate_parser.add_argument("path", type=Path)
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (GvasError, OSError, ValueError) as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
