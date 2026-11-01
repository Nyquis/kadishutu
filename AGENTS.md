# AGENTS.md

Instructions and project context for agents working on this repository.

## Project

Kadishutu is a save editor for **Shin Megami Tensei V: Vengeance**.

- Python 3.11-3.13
- PySide6 for the GUI
- Pixi for the environment and tasks
- Windows 11 is the primary target; Linux/macOS are best-effort

Work from the repository root (`kadishutu/`).

## Commands

Use Pixi tasks; the tools are not on the global PATH.

```shell
pixi run test       # pytest
pixi run lint       # ruff check .
pixi run typecheck  # mypy src
pixi run gui        # run the GUI
pixi run build      # PyInstaller + zip
```

Do not install tools globally. Do not use `pytest`, `ruff`, or `mypy` directly.

`pixi run typecheck` is expected to be clean. If it reports errors, fix them
in the same change or document why they are intentional.

## Layout

- `src/kadishutu/data/` - committed tables and generated JSON
- `src/kadishutu/core/` - save parsing and editing
- `src/kadishutu/gui/` - PySide6 screens and widgets
- `tools/save_lab/` - extraction and metadata generators
- `tests/` - pytest suite
- `docs/` - save format, safety, leveling, manual testing
- `lab/` - local extraction output; `lab/dumps/` and `lab/corpus/` are ignored

Put temporary diagnostics under `lab/tmp/`, not the `lab/` root, so they stay
out of `git status`.

## Data extraction rules

- Never modify or write into the game installation.
- Extract only into `lab/`.
- Do not commit game dumps, artwork, or official prose.
- Do not expose item sources or other spoiler-sensitive data.
- Use mechanics-only summaries and local names.
- Generated tables belong in `src/kadishutu/data/tables/`.
- Add a generator under `tools/save_lab/` and document it in
  `src/kadishutu/data/tables/README.md`.

Existing generators:

```shell
pixi run python -m tools.save_lab.item_metadata
pixi run python -m tools.save_lab.miracle_metadata
pixi run python -m tools.save_lab.quest_metadata
pixi run python -m tools.save_lab.leveling_metadata
```

## Save-format and mechanics notes

### Nahobino

- `PlayerGrow` table 2: one row per level, `(HP, MP, STR, VIT, MAG, AGI, LUK)`.
  Row index is the level; row 0 is unused. Levels 1-150.
- `PlayerGrow` table 3: EXP needed to advance one level, index `level - 1`.
- The save's `exp` field is progress inside the current level, not total EXP.
- `stat_points` is the total already allocated, not unspent points.
- Level 150 has no next-level requirement.

### Demons

- `NKMBaseTable` is committed as `Players.csv`.
- `Compendium == 1` is the normal/fusable roster; `0` means enemy/boss/NPC.
- Agrat canonical: ID 392. Enemy variants: 568/570/571/576. Shadows: 762/763.
- Growth weights are relative and normalized by `Growth Total`.
  It is 100 for most demons but can be 98-104.
- A normal level-up grants 3 core-stat points.
  Expected gain: `3 * weight / Growth Total`.
- HP/MP use separate growth values. The screen estimates `HP growth / 4` and
  `MP growth / 6`; this is a corpus estimate, not a confirmed formula.
- Demon EXP requirements scale the Nahobino curve by a community-measured
  multiplier based on levels above the species base level (1.5 ... 10).
- Demon skill schedule is in `Skill Level 1-12` / `Skill at Skill Level 1-12`.

### Save location

- `title_save_location` at `0x524` is only partially mapped in
  `save_locs.json`.
- The preview falls back to: exact mapping, last layline, map region, `UNKNOWN`.
- Do not display `UNKNOWN` when a layline or map region is available.

### SysSave

- Volume slots are bfloat16.
- BGM `0x5e4`, Ambient `0x5e8`, SE `0x5ec`.
- Voice is **not** `0x5e0`; candidates are `0x5f0`/`0x5f4`, still unresolved.
- `0x1232` remains unverified.

## UI conventions

- The global **Advanced** toggle (status bar + Edit menu) is the single gate
  for risky edits. Do not add per-screen advanced-edit checkboxes.
- Safe mode locks level/EXP, stored `Current` stats, and raw skill IDs.
- Warnings must inform, not block. A valid save is still allowed.
- Risk badges:
  - `game-managed` - the game may recalculate the value
  - `separate fields` - related fields are stored separately
- HP = 1 preset changes **Healable HP** only; max HP is unchanged.
  Warn that the game may restore it after death/revival.
- Progression grants items only. Do not add a level planner or emulate leveling.
- Keep item names unchanged. Put potential mappings in tooltips.
- Use scroll areas for dense or tall screens. Verify at 900x620; rows must not
  overlap or be compressed to zero height.
- Skills: keep the help label's vertical size policy `Fixed`; the table must
  stay near the top.
- Affinities: content lives in a scroll area; group boxes keep their natural
  height.
- Demon detail: scroll area; the growth tables must keep their row heights even
  with the graphic visible.
- Demon creation:
  - safe mode shows only `Compendium == 1`
  - Advanced shows enemy entries, muted and marked `· Enemy`
  - turning Advanced off clears an enemy selection
- Demon detail growth tables:
  - HP/MP: `Current`, `Growth`, `Est. /level`
  - Core stats: `Current`, `Weight %`, `Avg/level`
- Reuse `RiskBadge` and the `Muted`/`Warning` object names.

## Testing

- Add tests for data, core, and GUI changes.
- GUI tests use a `QApplication` fixture and `mainwindow.MAIN_WINDOW`.
- `tests/conftest.py` resets Advanced OFF for every test.
- For layout regressions, show the window, call `processEvents()`, and assert
  label heights or scroll-area presence.
- Run `pixi run lint` and `pixi run test` before committing.
- Run `pixi run typecheck` and confirm no new errors.

## CI

GitHub Actions runs `.github/workflows/ci.yml` on pull requests, pushes to
`main`, and weekly.

- `lint and typecheck` runs on ubuntu.
- `test` runs `pixi run test -q` on windows, the primary target.
- `package` runs only on the weekly schedule and on manual dispatch. It builds
  without UPX, relies on the build's own leak gate, and runs
  `kadishutu.exe help` to prove the frozen executable boots.

Do not add a package build to pull requests: it is slow and publishes nothing.

## Git and release workflow

- Commit before building: the artifact name uses `git rev-parse --short HEAD`.
- Use conventional commit messages, for example:
  `feat(ui): ...`, `fix(ui): ...`, `docs(...): ...`.
- Build with `pixi run build`.
- Artifact:
  `dist/pyinstaller/windows/kadishutu-windows-v<version>-<shortsha>.zip`.
- `pyproject.toml` and `pixi.toml` versions must match; the build fails if
  they drift.
- The build keeps the new archive plus the four newest previous archives
  (five total). Use `--keep-previous N` or `--no-archive-prune` to change it.
- Report the SHA-256 of the zip.
- The build scrubs install metadata (`direct_url.json`, `INSTALLER`) and
  `__pycache__`/stray `.pyc` files, then fails if any build-host path remains
  in the packaged tree. Do not publish an artifact from a failing build.
- Older archives are pruned automatically; do not commit `dist/`.
- Do not commit `dist/`, `build/`, `.pixi/`, or `lab/` contents.

## Documentation

- Keep manual checks in `docs/manual-testing.md` only; do not add `.github`
  issue or pull request templates. CI workflows live in `.github/workflows/`.
- Update relevant docs with behavior changes:
  - `docs/README.md` - documentation index
  - `docs/safety.md` - advanced mode, warnings, presets
  - `docs/leveling.md` - stat/EXP tables and estimates
  - `docs/GameSave.md` / `docs/SaveSchema.md` - save offsets and fallbacks
- `docs/manual-testing.md` rows must reference the current build when a manual
  pass is actually run.

## Known open work

- SysSave Voice volume slot (`0x5f0` or `0x5f4`).
- SysSave camera/display/message/battle/control manual checks.
- Controlled in-game level-up diff to confirm demon HP/MP growth formulas.
- Optional full extraction of the save-location name table.
