# Manual Testing

This is the long-lived manual test catalog. Use the IDs to reference specific
checks later.

## Current verification

| Field | Value |
|---|---|
| Build | `ac79421` |
| Game | SMT5V |
| OS | Windows |
| Tester | |
| Date | |

Update this block and the per-area status after each manual pass.

## Status overview

| Area | Status | Last verified build | Notes |
|---|---|---|---|
| Save workflow | Not run | | |
| Items | Not run | | |
| Essences | Not run | | |
| Alignment | Not run | | |
| Meta | Not run | | |
| Demons | Not run | | |
| Demon creation | Not run | | |
| Leveling | Not run | | |
| Safety and presets | Not run | | |
| Progression | Not run | | |
| Laylines | Not run | | |
| SysSave | Not run | | |
| Data pipeline | Not run | | |
| Regression | Not run | | |

Status values: `Not run`, `Pass`, `Fail`, `Blocked`, `Deferred`.

## Setup

- Use a disposable copy of the save.
- Keep the original save untouched.
- Confirm a backup is created before writing.
- Test one early save and one late-game save if possible.
- Record the build hash and game version in the verification block.

## Smoke tests

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| SMOKE-01 | Launch the packaged build | App opens normally | Not run | | |
| SMOKE-02 | Open a game save | Save loads and metadata is correct | Not run | | |
| SMOKE-03 | Create a backup | Backup file appears | Not run | | |
| SMOKE-04 | Change a harmless value, Apply, Save to a copy | Copy writes successfully | Not run | | |
| SMOKE-05 | Reopen the saved copy | Change is present | Not run | | |
| SMOKE-06 | Load the copy in SMT5V | Game loads without a title-screen crash | Not run | | |

## Save workflow

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| SAVE-01 | Apply a change and save to a new file | Hash updates and round-trip verification passes | Not run | | |
| SAVE-02 | Switch screens with unapplied edits | App warns or preserves the edits | Not run | | |
| SAVE-03 | Restore a backup from the backup manager | Restored save opens correctly | Not run | | |
| SAVE-04 | Open a save with an invalid hash | App warns before opening | Not run | | |
| SAVE-05 | Open a save whose title location is not mapped | Preview shows the last layline or map region, not `UNKNOWN` | Not run | | |

## Difficulty

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| DIFF-01 | Open the game-save category list | Card is named `Difficulty`, not `Settings` | Not run | | |
| DIFF-02 | Open Difficulty | SysSave note is visible | Not run | | |
| DIFF-03 | Change difficulty and save/reload | Value persists | Not run | | |

## Items

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| ITEM-01 | Open all item tabs | Headers show Icon, Item, Max, Details, Amount | Not run | | |
| ITEM-02 | Search by name and ID | Matching rows remain visible | Not run | | |
| ITEM-03 | Search `unique` and `infinite` | Flag-based filtering works | Not run | | |
| ITEM-04 | Filter rows and use Max all / Clear all | Only visible rows change | Not run | | |
| ITEM-05 | Max Amrita Soda, Periapt, Aquamarine | Limits are 50, 1, 99 | Not run | | |
| ITEM-06 | Open an over-limit save | Warning appears | Not run | | |
| ITEM-07 | Save, reload, and load in game | Amounts persist | Not run | | |

## Essences

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| ESS-01 | Search Pixie’s Essence | `Have` and `Used before` are checked | Not run | | |
| ESS-02 | Uncheck Used before and apply | Badge becomes `Have`; essence remains | Not run | | |
| ESS-03 | Uncheck Have, then re-check it | Used history is preserved | Not run | | |
| ESS-04 | Use filtered bulk actions | Only visible essences change | Not run | | |
| ESS-05 | Save, reload, and load in game | Essence flags persist | Not run | | |

## Alignment

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| ALIGN-01 | Search `A Wish for a Fish` | One row with one dropdown | Not run | | |
| ALIGN-02 | Select Law, then Chaos | Only one side is written | Not run | | |
| ALIGN-03 | Open a crafted both-selected save | `Both selected` warning appears | Not run | | |
| ALIGN-04 | Use alignment filters and summary | Counts match selected choices | Not run | | |
| ALIGN-05 | Toggle raw offset/bit view | Raw columns appear | Not run | | |
| ALIGN-06 | Save, reload, and load in game | Alignment flags persist | Not run | | |

## Meta

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| META-01 | Open Meta | Endings grouped under both canons | Not run | | |
| META-02 | Change cycles | Maximum is 99 | Not run | | |
| META-03 | Mark and clear endings | Per-canon and overall counts update | Not run | | |
| META-04 | Create mismatched header copies | Warning appears; Apply syncs copies | Not run | | |
| META-05 | Toggle Satan beaten | Value persists after save/reload | Not run | | |
| META-06 | Open Miracles → Unlocks | Satan flag is no longer present | Not run | | |

## Demons

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| DEMON-01 | Open Efreet → Skills | Fire Pleroma does not show `491` by default | Not run | | |
| DEMON-02 | Check learn types | Fire Pleroma is Default; Maragion is Library | Not run | | |
| DEMON-03 | Enable Advanced editing | Raw skill IDs appear | Not run | | |
| DEMON-04 | Hover Agi | Mechanics-only summary appears | Not run | | |
| DEMON-05 | Open Stats | Natural/Bonuses/Current/Healable labels appear | Not run | | |
| DEMON-06 | Recalculate current | Current becomes Natural + Bonuses | Not run | | |
| DEMON-07 | Heal HP/MP | Healable copies Current HP/MP | Not run | | |
| DEMON-08 | Enable Advanced editing | Current fields become editable | Not run | | |
| DEMON-09 | Change affinity | Value applies and persists | Not run | | |
| DEMON-10 | Change potential | Signed value applies and persists | Not run | | |
| DEMON-11 | Save, reload, and load demon in game | Stats/skills/affinities/potentials are sane | Not run | | |
| DEMON-12 | Open a demon screen | HP/MP and core-stat growth tables show Current, Weight %, and estimated/average gains | Not run | | |
| DEMON-13 | Change the demon ID | Growth table follows the new species | Not run | | |
| DEMON-14 | Check the level/EXP note | Badge says `separate fields`, not `derived` | Not run | | |
| DEMON-15 | Resize the demon detail to 900×620 with the graphic visible | Growth tables do not overlap; the screen scrolls | Not run | | |

## Demon creation

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| CREATE-01 | Open Create demon with Advanced off | Only compendium demons are listed; Agrat enemy variants are absent | Not run | | |
| CREATE-02 | Enable Advanced | Enemy/NPC entries appear, muted and marked `· Enemy` | Not run | | |
| CREATE-03 | Select an enemy entry in Advanced | Preview warning appears; creation remains available | Not run | | |
| CREATE-04 | Turn Advanced off with an enemy selected | Selection clears and Create is disabled | Not run | | |
| CREATE-05 | Resize to 900×620 | Form and preview do not overlap; the screen scrolls | Not run | | |
| CREATE-06 | Create a normal demon, save, and load in game | Demon appears correctly in storage and party | Not run | | |

## Leveling

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| LVL-01 | Open the Nahobino screen on a level 55 save | EXP to next shows 140,518 | Not run | | |
| LVL-02 | Compare Nahobino base HP/MP with the level table | Values match the game status screen | Not run | | |
| LVL-03 | Open a demon at its base level | EXP to next is 1.5x the Nahobino value | Not run | | |
| LVL-04 | Level a demon up once in game and diff the save | Displayed EXP-to-next changes as predicted | Not run | | |
| LVL-05 | Level the Nahobino up once in game and diff the save | Progress resets and stats match the next table row | Not run | | |

## Safety and presets

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| SAFE-01 | Open a demon with Advanced off | Level/EXP are locked and the note is visible | Not run | | |
| SAFE-02 | Toggle Advanced in the status bar | Fields unlock; action and button stay in sync | Not run | | |
| SAFE-03 | Restart the app | Advanced setting is remembered | Not run | | |
| SAFE-04 | Use Set HP to 1 | Healable HP becomes 1, max HP is unchanged, warning appears | Not run | | |
| SAFE-05 | Save, reopen, and load the HP=1 save | Value persists; note whether the game restores it after death | Not run | | |
| SAFE-06 | Check risk badges and tooltips | `game-managed` and `separate fields` explanations are readable | Not run | | |

## Progression

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| PROG-01 | Open Progression | Item sections are shown; no Nahobino level planner is present | Not run | | |
| PROG-02 | Check the item groups | Level-up, Balm, Incense, and Sutra groups are all present | Not run | | |
| PROG-03 | Grant items with +1/+5/Max and Apply | Inventory amounts update | Not run | | |
| PROG-04 | Hover Sutras | Tooltip names the potential; item name is unchanged | Not run | | |
| PROG-05 | Resize to the minimum window size | Rows do not overlap and the screen scrolls | Not run | | |
| PROG-06 | Grant a Sutra, save, and use it in game | Inventory persists and the game applies the potential increase | Not run | | |

## Laylines

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| LAYLINE-01 | Open Layline Crossing | Laylines are grouped by region | Not run | | |
| LAYLINE-02 | Search and filter | Name/region search and unlocked filter work | Not run | | |
| LAYLINE-03 | Check status columns | Locked/unlocked and last-used markers are correct | Not run | | |
| LAYLINE-04 | Select a layline | Details show region, ID, map, coordinates, status | Not run | | |
| LAYLINE-05 | Teleport to Tokyo Diet Building | Selection enables Teleport | Not run | | |
| LAYLINE-06 | Apply, save, and load in game | Position and unlock state are correct | Not run | | |
| LAYLINE-07 | Open an invalid last-layline save | Warning appears | Not run | | |

## SysSave

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| SYSSAVE-01 | Open SysSave.sav | System Settings screen loads | Not run | | |
| SYSSAVE-02 | Change a volume slider | Percentage updates | Not run | | |
| SYSSAVE-03 | Change camera/display/message options | Controls update correctly | Not run | | |
| SYSSAVE-04 | Toggle inverted settings | Checkbox meaning matches the UI label | Not run | | |
| SYSSAVE-05 | Apply and Save to Disk | Save round-trip succeeds | Not run | | |
| SYSSAVE-06 | Reopen SysSave and launch the game | Settings persist without corruption | Not run | | |

## Data pipeline

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| DATA-01 | Open Miracles | Category tabs populate | Not run | | |
| DATA-02 | Confirm no missing/uncategorized miracle fallback | All expected categories appear | Not run | | |
| DATA-03 | Open the editor with generated quest data | No load errors | Not run | | |

## Regression checks

| ID | Test | Expected | Status | Build | Notes |
|---|---|---|---|---|---|
| REG-01 | Demon selector and creation | Still open/work | Not run | | |
| REG-02 | Player names/stats | Still apply | Not run | | |
| REG-03 | DLC screen | Still opens | Not run | | |
| REG-04 | Theme switching | Still works | Not run | | |
| REG-05 | Backup manager | Still lists/restores backups | Not run | | |
| REG-06 | Save to Disk | Hash verification still passes | Not run | | |

## Release log

| Build | Date | Tester | Result | Notes |
|---|---|---|---|---|
| `ac79421` | 2026-10-31 | | Not run | Initial manual checklist |
