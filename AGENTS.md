# AGENTS.md

Instructions and project context for agents working on this repository.

Machine-wide rules are in `~/.config/opencode/AGENTS.md`; this file adds project
detail and wins where it is more specific.

## Project

Kadishutu is a save editor for **Shin Megami Tensei V: Vengeance**.

- Python 3.11-3.13, PySide6 for the GUI, Pixi for the environment and tasks
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

## Domain invariants

Offsets, table layouts, and the EXP curves are documented in `docs/`; read the
relevant one before changing parsing. The rules below are the ones that cause
silent corruption or a wrong screen when missed.

- The save's `exp` field is progress inside the current level, not total EXP.
- `stat_points` is the total already allocated, not unspent points.
- Level 150 has no next-level requirement.
- `Compendium == 1` is the normal/fusable roster; `0` means enemy/boss/NPC.
- Never display `UNKNOWN` in the save-location preview when a layline or map
  region is available.
- Volume slots are `bfloat16`. `0x1232` and the Voice slot are unverified; do
  not present either as settled.
- Demon growth weights are relative, normalised by `Growth Total`, and the
  `HP growth / 4`, `MP growth / 6` conversions are corpus estimates, not
  confirmed formulas. Label them as estimates in the UI.

Where to look: `docs/leveling.md` (stat/EXP tables and estimates),
`docs/GameSave.md` and `docs/SaveSchema.md` (offsets and fallbacks),
`docs/SysSave.md` (system save).

## UI conventions

- The global **Advanced** toggle (status bar + Edit menu) is the single gate
  for risky edits. Do not add per-screen advanced-edit checkboxes.
- Safe mode locks level/EXP, stored `Current` stats, and raw skill IDs.
- Warnings must inform, not block. A valid save is still allowed.
- Risk badges: `game-managed` (the game may recalculate the value) and
  `separate fields` (related fields are stored separately).
- HP = 1 preset changes **Healable HP** only; max HP is unchanged.
  Warn that the game may restore it after death/revival.
- Progression grants items only. Do not add a level planner or emulate leveling.
- Keep item names unchanged. Put potential mappings in tooltips.
- Dense or tall screens use scroll areas. Verify at 900x620; rows must not
  overlap or be compressed to zero height.
- Layout regressions to avoid reintroducing: Skills keeps the help label's
  vertical size policy `Fixed` and the table near the top; Affinities keeps its
  content in a scroll area with group boxes at natural height; Demon detail
  keeps table row heights even with the graphic visible.
- Demon creation: safe mode shows only `Compendium == 1`; Advanced adds enemy
  entries, muted and marked `· Enemy`; turning Advanced off clears an enemy
  selection.
- Demon detail growth tables: HP/MP shows `Current`, `Growth`, `Est. /level`;
  core stats show `Current`, `Weight %`, `Avg/level`.
- Reuse `RiskBadge` and the `Muted`/`Warning` object names.

## Testing

- Add tests for data, core, and GUI changes.
- GUI tests use a `QApplication` fixture and `mainwindow.MAIN_WINDOW`;
  `tests/conftest.py` resets Advanced OFF for every test.
- For layout regressions, show the window, call `processEvents()`, then assert
  label heights or scroll-area presence.
- Before committing: `pixi run lint`, `pixi run test`, and `pixi run typecheck`
  with no new errors.

## CI

`.github/workflows/ci.yml` runs on pull requests, pushes to `main`, and weekly:
lint and typecheck on ubuntu, `pixi run test -q` on windows. `package` runs only
on the weekly schedule and manual dispatch; it builds without UPX, relies on the
build's own leak gate, and runs `kadishutu.exe help` to prove the frozen
executable boots. Do not add a package build to pull requests.

## Git and release workflow

- Conventional commit messages, for example `feat(ui): ...`, `fix(ui): ...`.
- Commit before building. The artifact name uses `git rev-parse --short HEAD`
  and the build refuses a dirty tree; `--allow-dirty` is for throwaway builds.
- `pixi run build` produces
  `dist/pyinstaller/windows/kadishutu-windows-v<version>-<shortsha>.zip`.
- Publish by pushing a `v*` tag; `.github/workflows/release.yml` builds and
  releases it. Only on an explicit request in the same task: never tag
  autonomously. Manual fallback: `docs/releasing.md`.
- `pyproject.toml` and `pixi.toml` must agree on version, authors, license, and
  description. The build fails if they drift.
- The build keeps the new archive plus the four newest previous archives
  (five total). Use `--keep-previous N` or `--no-archive-prune` to change it.
- The build scrubs install metadata (`direct_url.json`, `INSTALLER`) and
  `__pycache__`/stray `.pyc` files, then fails if any build-host path remains
  in the packaged tree.
- Report the SHA-256 of the zip. Published releases carry a `SHA256SUMS.txt`.
- Do not commit `dist/`, `build/`, `.pixi/`, or `lab/` contents.

## Versioning

- Pre-1.0: minor (`0.3.0`) for new features or breaking changes, patch
  (`0.2.1`) for fixes and data corrections. Docs, tests, and CI do not bump.
  Bumps happen immediately before tagging a release, as the last commit.
  Development builds keep the current version; the short commit in the
  artifact name distinguishes them.
- If a change looks release-worthy, propose the bump and wait for confirmation.
- The package author is Nyquis. `fnrir` appears only as upstream credit in
  `NOTICE`, `LICENSES/MIT.txt`, and the README; do not treat it as the current
  author.

## Documentation

- Keep manual checks in `docs/manual-testing.md` only; do not add `.github`
  issue or pull request templates. CI workflows live in `.github/workflows/`.
- Update relevant docs with behavior changes:
  - `docs/README.md` - documentation index
  - `docs/safety.md` - advanced mode, warnings, presets
  - `docs/leveling.md` - stat/EXP tables and estimates
  - `docs/GameSave.md` / `docs/SaveSchema.md` - save offsets and fallbacks
  - `docs/SysSave.md` - system save offsets
- `docs/manual-testing.md` rows must reference the current build when a manual
  pass is actually run.
