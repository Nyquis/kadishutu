# Manual Testing

This is the long-lived manual test catalog. Use the IDs in PRs and release
issues so a specific check can be referenced later.

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
| Laylines | Not run | | |
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
| DEMON-03 | Enable Show skill IDs | Raw IDs appear | Not run | | |
| DEMON-04 | Hover Agi | Mechanics-only summary appears | Not run | | |
| DEMON-05 | Open Stats | Natural/Bonuses/Current/Healable labels appear | Not run | | |
| DEMON-06 | Recalculate current | Current becomes Natural + Bonuses | Not run | | |
| DEMON-07 | Heal HP/MP | Healable copies Current HP/MP | Not run | | |
| DEMON-08 | Enable direct Current editing | Current fields become editable | Not run | | |
| DEMON-09 | Change affinity | Value applies and persists | Not run | | |
| DEMON-10 | Change potential | Signed value applies and persists | Not run | | |
| DEMON-11 | Save, reload, and load demon in game | Stats/skills/affinities/potentials are sane | Not run | | |

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
