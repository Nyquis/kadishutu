# Qadištu (カディシュトゥ, Kadishutu) save editor

A save editor for Shin Megami Tensei V: Vengeance.

Windows 11 is the primary target. Linux and macOS support is best-effort.
Running from source requires Python 3.11–3.13.

## Installation

### Prebuilt binary

If a prebuilt binary is available for your platform, download it from the
[release page](https://github.com/Nyquis/kadishutu/releases). The binaries are
built with PyInstaller, so antivirus software may flag them even though they
are not malicious.

### From source with Pixi

This is the recommended route for a local checkout. It installs the runtime
dependencies and the GUI (PySide6 and Pillow) into a reproducible environment.

1. Install [pixi](https://pixi.sh).
2. Clone the repository and install the environment:

   ```shell
   git clone https://github.com/Nyquis/kadishutu.git
   cd kadishutu
   pixi install
   pixi run gui
   ```

   `pixi run kadishutu` is equivalent.

On Windows, `setup.bat` and `run.bat` are thin wrappers around `pixi install`
and `pixi run kadishutu`.

To update a Pixi checkout:

```shell
git pull
pixi install
```

### With pipx

Use this only for a published package or when installing from a checkout. The
GUI dependencies are optional, so the `gui` extra is required.

Published package:

```shell
pipx install "kadishutu[gui]"
```

From a checkout:

```shell
pipx install ".[gui]"
```

Upgrade a published install with:

```shell
pipx upgrade kadishutu
```

For a local checkout, update the checkout and reinstall:

```shell
git pull
pipx install --force ".[gui]"
```

Installing without the `[gui]` extra leaves out PySide6 and Pillow. The app has
a fallback prompt that can install them later, but that is not the recommended
setup. See the [pipx documentation](https://pipx.pypa.io/latest/) for details.

## Development

The project uses [pixi](https://pixi.sh) for dependency management and
reproducible development environments. The developer tools (Ruff, mypy,
PyInstaller) live in the `dev` environment:

```shell
pixi run -e dev lint
pixi run -e dev typecheck
pixi run -e dev test
pixi run -e dev build
```

`build` produces the release: a `kadishutu` folder plus a
`kadishutu-<platform>-<commit>.zip` archive next to it.

The build skips the Qt modules the widgets-only GUI never imports (QML/Quick,
PDF, Network, SVG) and then prunes the DLLs, plugins and translations that
PyInstaller copies in anyway. That is what keeps the download near 30 MB
instead of 50 MB; pass `--no-prune` to build the unpruned payload for
comparison.

PyInstaller uses UPX when it is available, because its LZMA packing shrinks
both the folder and the zip. Pass `--no-upx` if the packed executable trips
antivirus heuristics on your machine; it also starts ~0.3s faster that way.

The optional dependencies for `examples/late_bonuses.py` are in the
`example-late-bonuses` environment:

```shell
pixi run -e example-late-bonuses python examples/late_bonuses.py
```

## Usage

### GUI

Open the GUI by running `kadishutu gui $OPTIONALLY_A_SAVE_FILE` in a terminal,
or by double-clicking the executable.

#### Applying and saving

Editing happens in two steps:

1. **Apply Changes** copies the current screen's edits into the open save in
   memory. It does not write to disk.
2. **Save to Disk** writes applied changes to the save file and creates a
   timestamped backup.

Saving is refused while edits are still unapplied, and the status bar says
which step is next. Leaving a screen, closing the save, or quitting asks
before discarding unapplied edits; closing the save or app also warns about
applied changes that were not written to disk.

### In a terminal

Available subcommands:

- `decrypt`
- `edit`
- `encrypt`
- `help`
- `inspect`
- `run_script`
- `update_hash`

Saves are written atomically and a timestamped `.bak` copy of the previous
file is created before it is replaced. Commands that read a save validate its
hash by default; `encrypt --update-hash`, `edit --force`, and
`inspect --ignore-hash` / `run_script --ignore-hash` are explicit overrides.

#### Edit subcommand

##### DLC

- clear - Clears all DLC flags
- print - Prints what DLCs were used
- remove - Removes a DLC flag

### As a library

```python
from kadishutu import EncryptedSave, GameSaveEditor
from pathlib import Path

path = Path(...)
savefile = EncryptedSave.open(path).decrypt()
game = GameSaveEditor(savefile)

stats = game.player.stats
stats.max_with_sbis()
stats.current.hp = 999
stats.current.mp = 999

# Yes. This surprisingly works.
stats.current.strength = 0xffff

game.player.healable.hp = 999
game.player.healable.mp = 999
game.macca = 9999999
game.items.from_name("Big Glory Crystal").amount = 99

# Updates the hash, encrypts, writes atomically, creates a timestamped
# backup, and verifies the saved file.
savefile.save_finished(path)
```

## Additional setup

Some data is not bundled with the editor. While not strictly necessary, adding
it gives you a better experience with the editor.

The files can be dumped/saved/exported with
[umodel](https://www.gildor.org/en/projects/umodel).

(Don't use the Linux version, it is outdated.)

[Fmodel](https://fmodel.app/) should also work, but it is hit or miss for me.

### Game data

```txt
Game/Blueprints/Gamedata/BinTable/GodParameter/Table/GodParameterDataTable.uexp
Game/Blueprints/Gamedata/BinTable/Mission/MissionTable.uexp
```

(GodParameter means Miracle.)

### Game image data

```txt
Game/Design/UI/CharaIcon/Textures/*
Game/Design/UI/Icon/Element/Textures/icon_element_01.tga
Game/Design/UI/LoadingCharaIcon/*
```

### App data directory

For Linux, it is usually:

`$HOME/.local/share/kadishutu`

For Windows, it is:

`$HOME/AppData/Local/kadishutu`

For macOS, it is:

`$HOME/Library/Application Support/kadishutu`

The app can also be made portable by setting the `PORTABLE_APP` environment
variable. Then data is stored in/loaded from:

`./_appdata/data`

(More info in [paths.py](src/kadishutu/paths.py).)

## Plugins and scripts are trusted code

Plugins in the app data `plugins` directory and scripts passed to
`run_script` are arbitrary Python and run with your full user permissions.
Only install plugins and run scripts from sources you trust.

Plugin names must be plain identifiers (letters, digits, and underscores).
Broken plugins are skipped with a warning. To start the app without loading
any plugins, set `KADISHUTU_DISABLE_PLUGINS=1`.

## Troubleshooting and recovery

### Restoring a backup

Before replacing a save, the app creates a timestamped backup next to it:

```txt
SaveGame.sav.20261027-153000-123456.bak
```

To restore one:

1. Close the editor and the game.
2. Keep a copy of the current save.
3. Replace the current save with the `.bak` file, or rename the backup back to
   the original save name.
4. Reopen the save and verify it in the game.

### Missing GUI dependencies

If the app reports that PySide6 is missing, install the GUI extra rather than
the base package:

```shell
pipx install --force ".[gui]"
```

or use Pixi:

```shell
pixi install
pixi run gui
```

### Invalid save hash

The editor warns when a save's hash is invalid. This can mean the save is
corrupted or was modified by another tool. Do not bypass the warning unless
you have a backup and know why the hash is wrong.

### Failed writes

Saves are written through a temporary file and verified after replacement.
If a write fails, the original file should remain intact and the error may
include the backup path. Keep the backup until the save has been checked in
the game.

More troubleshooting information is in [docs/Troubleshooting.md](docs/Troubleshooting.md).

## Project status

NOTE: This is tested with the Switch version of the game (`010069C01AB82000`
with all DLCs more specifically), but it also works with the PC version.

### What works?

- Encryption/decryption
- Viewing and editing of the following values
  - Player names
  - Time of saving (it is a bit weird, but it works)
  - Used DLCs (this will not give you DLC-exclusive content; it is mainly for
    importing a save file from a copy with DLCs)
  - Play time
  - Miracles and unlocking them
  - Summoned demons and player placement
  - For the player and demons:
    - Affinities, potentials, stats, skills, EXP, level, innate skill
  - Player stat points
  - Demons (demon IDs)
  - Team composition (summoned demons and their order)
  - Macca, Glory
  - Items
  - Essences (partially)
  - Position
  - Early compendium and quest support
  - Alignment
  - Number of cycles, endings, clear state, and late-game flags
  - Game difficulty
  - SysSave system settings: audio, camera, display, messages, battle,
    controls, language, and Mitama dances
- Summoning new demons partially works, but it is not recommended because the
  demon block is not fully understood

### Known limitations

- The CLI is functional but unpolished.
- The demon block and some compendium/quest data are not fully understood.
- Plugins and scripts are trusted code rather than sandboxed extensions.
- Some SysSave advanced/DLC flags are not exposed yet.

### Planned

- Editing more data
  - Properly implementing compendium and quest support
    (Tao and Yoko might be in a separate block)
  - Full demon support
- Better CLI
- Allowing the user to add files that modify the demon/skill database, in
  correlation with mods
- Rewrite the core in Rust once the format is better understood

## Documentation

The save-file documentation is in the `docs` folder:

- [GameSave.md](docs/GameSave.md)
- [SysSave.md](docs/SysSave.md)
- [SaveSchema.md](docs/SaveSchema.md)
- [Leveling.md](docs/leveling.md)
- [Troubleshooting.md](docs/Troubleshooting.md)
- [Manual testing](docs/manual-testing.md)

## License

This fork is licensed under the [Apache License 2.0](LICENSE).

Portions inherited from the upstream project remain under the MIT License.
See [LICENSES/MIT.txt](LICENSES/MIT.txt) and [NOTICE](NOTICE) for details.

## Credits

- [zmbkilla's SMTVV Save Editor](https://github.com/zmbkilla/SMTV-VSaveEditor/tree/e8def6cd038d1a3d23d5bdc7612b1fd13808dfaf)
  for most working offsets, the AES key, innate skill IDs, and demon IDs

And some save editors for the original game:

- [Aogami Save Editor](https://github.com/supremetakoyaki/Aogami)
  for the inspiration for the name
- [this save editor](https://github.com/Amuyea-gbatemp/Shin-Megami-Tensei-V-Save-Editor)
  for information on how other types of data are stored

## External links

[![This project is also on GameBanana.](https://gamebanana.com/tools/embeddables/17599?type=large)](https://gamebanana.com/tools/17599)
