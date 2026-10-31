# save_lab

Development-only tooling for researching SMT5V save files. This package lives
outside `src/`, so it is not included in the packaged kadishutu application.

The lab is intentionally small: it reuses `kadishutu.core.shared.file_handling`
and the editor classes instead of reimplementing decryption, hashing, or field
access.

## Commands

Run from the repository root:

```shell
pixi run python -m tools.save_lab gvas <decrypted-save>
pixi run python -m tools.save_lab diff <before-save> <after-save>
pixi run python -m tools.save_lab coverage <decrypted-save>
pixi run python -m tools.save_lab validate <decrypted-save>
```

- `gvas` — parse and print the GVAS header, class name, and payload offset
- `diff` — annotated byte diff with integer, float, UTF-16, and bit candidates
- `coverage` — mapped, inferred, and unknown byte ranges
- `validate` — check size, class, GVAS offset, hash, item limits, and unused
  item IDs

Generated metadata helpers (run after exporting the relevant asset JSON into
`lab/dumps/`):

```shell
pixi run python -m tools.save_lab.item_metadata
pixi run python -m tools.save_lab.miracle_metadata
pixi run python -m tools.save_lab.quest_metadata
```

`mmi.py` contains the shared `MyFmtData`/TBCR reader and JSON writer.

Planned later:

- `explain` — show the schema entry and editor binding for an offset
- `snapshot` — copy the PC save folder into `lab/snapshots/`

## Layout

```text
tools/save_lab/
  __main__.py       # CLI entry point
  gvas.py           # GVAS header parser
  diff.py           # byte diff and value candidates
  schema.py         # region map and coverage
  files.py          # encrypted/decrypted save loading
  ue4ss/            # optional UE4SS dump kit and collector
  README.md
  __init__.py
```

## UE4SS

UE4SS is optional. The SMT5V-Project headers already expose the save schema;
use UE4SS only when you need live runtime values or reflected offsets. See
[ue4ss/README.md](ue4ss/README.md).

Collected output belongs in `lab/dumps/ue4ss/`, which is ignored by both Git
and Kopia.
