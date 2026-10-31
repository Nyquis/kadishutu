# UE4SS dump kit

This is a one-time research session, not part of the editor runtime.

**UE4SS is now optional for SMT5V.** The `SMT5V-Project` C++ headers already
expose the save schema (`FGameData`, `FPartyData`, `FNkmData`, `FCharData`,
`FItemSaveData`, `FSystemData`, and others). Use UE4SS only if you need live
runtime values, exact reflected property offsets, or the save object while it
exists during a save/load. See `lab/notes/smt5v-project.md` for the header map.

If you do run it, the goal is to learn the save class, its properties, and the
demon/item record types from the game itself instead of guessing offsets from
diffs.

## Before you start

- Close the game.
- Back up `%APPDATA%\SEGA\SMT5V\Steam\<SteamID>\` somewhere safe.
- Keep the original saves; do experiments on copies.
- UE4SS is for the single-player PC build. There is no anticheat concern here,
  but a broken mod can still crash the game, so back up first.

## Install

RE-UE4SS has two layouts. Check which one your release uses.

### New experimental layout (2025+)

All UE4SS files live in a `ue4ss` subfolder next to the game executable:

```text
Binaries\Win64\
  dwmapi.dll          # only the proxy DLL stays here
  ue4ss\
    UE4SS.dll
    UE4SS-settings.ini
    Mods\
```

Only the proxy DLL goes in `Win64`. Delete any old `xinput1_3.dll`; newer
releases warn that it can crash the game.

### Old stable layout (v3.0.1 and older)

Everything lives directly in `Binaries\Win64`:

```text
Binaries\Win64\
  UE4SS.dll
  UE4SS-settings.ini
  Mods\
```

### Common steps

1. Download a RE-UE4SS release that supports Unreal Engine 4.27.
2. Extract it into the correct layout above, next to
   `SMT5V-Win64-Shipping.exe`.
3. Pick one proxy DLL as described by the UE4SS docs. `dwmapi.dll` is the
   usual choice; if the game does not start, try `xinput1_3.dll` or
   `version.dll` instead. Keep only one proxy at a time.
4. In `UE4SS-settings.ini`, enable the console:

   ```ini
   [General]
   GuiConsoleEnabled = 1
   GuiConsoleVisible = 1
   ```

5. If automatic engine detection fails, add:

   ```ini
   [EngineVersionOverride]
   MajorVersion = 4
   MinorVersion = 27
   ```

6. Optional: install the starter script.
   - Create `Mods\SaveLab\Scripts\main.lua` inside the UE4SS root (inside
     `ue4ss\` for the new layout, or in `Win64\` for the old one) and copy
     [`find_save_objects.lua`](find_save_objects.lua) there.
   - Enable `SaveLab` the same way the bundled mods are enabled. In most
     UE4SS builds that means adding `SaveLab : 1` to `Mods\mods.txt`; check
     the bundled entries and the UE4SS version's documentation.

## Run

1. Start the game and load a save.
2. Press the keybinds from the starter script:
   - `F8` — list likely save/demon/item classes and their instances
   - `F9` — `DumpAllObjects()`
   - `F10` — `GenerateSDK()` (writes `CXXHeaderDump\`)
3. The built-in UE4SS keybinds also work:
   - `Ctrl+J` — object dump
   - `Ctrl+H` — C++ header dump
4. Open the **Live Property Viewer** and search for `SaveGame`, `SaveData`,
   `Demon`, `Item`, and `SysSave`. Screenshot or note the property names and
   values of the live save object.

The save object may only exist during load/save. If `F8` finds nothing, trigger
an in-game save and press `F8` again while the save menu is open.

Avoid setting `LoadAllAssetsBeforeDumpingObjects = 1`; it can load several GB
and crash the game. The default (`0`) is fine.

## Collect the output

From the repository root:

```powershell
pwsh -File tools/save_lab/ue4ss/collect.ps1 `
  -GameBinaries "C:\Program Files (x86)\Steam\steamapps\common\SMT5V\Binaries\Win64"
```

If your path differs, pass the real one. The collector writes to:

```text
lab/dumps/ue4ss/<timestamp>/
```

It copies, when present:

- `UE4SS_ObjectDump.txt`
- `UE4SS.log`
- `UE4SS-settings.ini`
- `CXXHeaderDump/`
- `UE4SS_SDK/`
- `Mappings/`

These directories are ignored by Git and Kopia, so they never enter the public
repository or the minimal backup.

## What to look for

- The save game class name and its properties
- Whether the payload is a structured `USaveGame` or a single byte array
- The demon record type, field names, and array size
- The item table type and any per-item metadata
- A `SysSave` class, if it exists
- Enum and DataTable names for items, demons, quests, miracles, and maps

## Cleanup

When the session is finished, remove the proxy DLL from `Binaries\Win64` if you
do not want UE4SS loaded on every launch. Keep the collected dumps in
`lab/dumps/ue4ss/`.
