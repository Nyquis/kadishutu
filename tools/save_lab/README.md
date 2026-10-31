# save_lab

Development-only tooling for researching SMT5V save files. This package lives
outside `src/`, so it is not included in the packaged kadishutu application.

The lab is intentionally small: it reuses `kadishutu.core.shared.file_handling`
and the editor classes instead of reimplementing decryption, hashing, or field
access.

## Planned commands

- `diff` — annotated diff between two saves or snapshots
- `coverage` — which byte ranges are mapped, inferred, or unknown
- `explain` — show the schema entry and editor binding for an offset
- `validate` — check save invariants before writing
- `gvas` — parse the UE4 `GVAS` payload after the 0x40-byte wrapper
- `snapshot` — copy the PC save folder into `lab/snapshots/`

## Layout

```text
tools/save_lab/
  ue4ss/            # UE4SS dump kit and collector
  README.md
  __init__.py
```

## UE4SS

The first experiment is a one-time UE4SS session to dump the save class and
related data. See [ue4ss/README.md](ue4ss/README.md).

Collected output belongs in `lab/dumps/ue4ss/`, which is ignored by both Git
and Kopia.
