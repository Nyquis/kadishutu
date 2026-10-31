# Save lab workspace

This directory is the local research workspace for kadishutu. It is mostly
untracked on purpose: real saves, extracted game data, and generated reports
must not end up in the public repository or in the Kopia backup.

## Layout

| Path | Git | Kopia | Purpose |
| --- | --- | --- | --- |
| `corpus/` | ignored | ignored | Raw saves and decrypted copies used for experiments |
| `dumps/` | ignored | ignored | UE4SS, FModel, KismetKompiler, and other extracted game data |
| `dumps/ue4ss/` | ignored | ignored | Object dumps, CXX headers, SDK dumps, UE4SS logs |
| `snapshots/` | ignored | ignored | Timestamped copies of the live save folder |
| `notes/` | ignored | backed up | Small Markdown notes and experiment logs |
| `reports/` | ignored | ignored | Generated diff/coverage reports |
| `artifacts/` | ignored | ignored | Temporary build or analysis output |
| `tmp/` | ignored | ignored | Scratch files |
| `cache/` | ignored | ignored | Parsed save indexes and caches |

The root `.gitignore` and `.kopiaignore` enforce this. Do not move files out
of the ignored directories unless you intend to publish them.

## Rules

- Never commit a real save, a decrypted save, or an editor backup.
- Never commit extracted `.uasset`, `.uexp`, `.pak`, `.usmap`, or `.kms` files.
- Keep one scenario per experiment and record what changed in the save.
- Prefer in-game saves over editor-written saves when learning the format.
- Keep the original encrypted save untouched; work on copies.

## Save folder on PC

```text
%APPDATA%\SEGA\SMT5V\Steam\<SteamID>\
  GameSave**.sav
  SysSave.sav
```

Close the game before copying or restoring saves, and be careful with Steam
Cloud overwriting a restored file.

## UE4SS output

See [tools/save_lab/ue4ss/README.md](../tools/save_lab/ue4ss/README.md).
Collected dumps go to `dumps/ue4ss/<timestamp>/`.

## Directory setup

The ignored directories are not tracked, so a fresh clone will not create them.
From the repository root:

```powershell
New-Item -ItemType Directory -Force `
  lab/corpus, lab/dumps/ue4ss, lab/snapshots, lab/notes, `
  lab/reports, lab/artifacts, lab/tmp, lab/cache
```
