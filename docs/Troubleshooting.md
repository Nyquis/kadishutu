# Troubleshooting

## "UnicodeDecodeError: '(name)' codec can't decode byte 0x(value) in position (offset): illegal multibyte sequence."

It's caused by Python thinking a UTF-8-encoded file (the default and used
everywhere in this repo) is in some different encoding.

### Solution 1: Upgrade

It's fixed in commit
[781ed59](https://github.com/fnr1r/kadishutu/commit/781ed593e018c7c65059633a3545bd414502cf89).

I tested it on Windows 7 and it should work.

### Solution 2: Change settings (Windows)

If it still happens (which is possible if it's caused by a different file).

Open the control panel, open "Region" from "Clock and Region", and open "Change system locale" from the "Administrative" tab.

Check the "Beta: Use Unicode UTF-8 with worldwide language support" checkbox at the bottom and restart your PC.

NOTE: This can also cause issues with other apps.

### Solution 3: Edit the data file

Find multibyte characters and replace them. For example:

- "š" with "s" (in "Qadištu")
- "é" with "e" (in "Souffle D'éclair")
- "∞" with "inf"

### Sources

[Solution 3 and some info for 2 - pewbeyeaj on GameBanana](https://gamebanana.com/posts/12025667)

[Solution 2 - diphyleia on GameBanana](https://gamebanana.com/posts/11873594)

## Changes made to resistances are reverted

This is expected (at least for demons) since those values are only copies.

## Changes made to skill potentials are reverted

If the skill potential of a demon is below 1, the skill potential can't be
increased (neither in-game with sutras, nor by editing).

As for the player, it might be recalculated based on bought miracles.


## Advanced mode is stuck on

Use the `Advanced: ON` button in the status bar or **Edit > Advanced editing**
to turn it off. The setting is remembered in QSettings under
`ui/advanced_mode`; deleting that key resets it.

## Location shows UNKNOWN

`title_save_location` is only partially mapped. The preview falls back to the
last used layline and then to the map region. A save that has no layline and
no known map region can still show `UNKNOWN`; this is not a save error.

## Voice volume looks wrong

Voice is not the `0x5e0` slot. That slot is currently exposed incorrectly.
BGM (`0x5e4`), Ambient (`0x5e8`), and SE (`0x5ec`) are verified. Voice is one
of the remaining slots and is still being investigated.

## UI text overlaps or collapses

Dense screens should use a scroll area. If a table or group collapses when the
window is short, report the screen name and approximate size. The Skills and
Affinities screens were fixed for 900x620; similar reports help catch others.
