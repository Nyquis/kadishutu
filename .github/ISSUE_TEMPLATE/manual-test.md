---
name: Manual test pass
about: Track manual verification for a specific build
title: "Manual verification — build "
labels: manual-test
assignees: ""
---

## Build

- Build/hash:
- Game version:
- OS:
- Tester:
- Date:

## Status

Copy the relevant test IDs from [`docs/manual-testing.md`](../../docs/manual-testing.md).

Legend: `Not run`, `Pass`, `Fail`, `Blocked`, `Deferred`.

## Smoke tests

- [ ] SMOKE-01 Launch packaged build
- [ ] SMOKE-02 Open a game save
- [ ] SMOKE-03 Create a backup
- [ ] SMOKE-04 Apply and save to a copy
- [ ] SMOKE-05 Reopen the saved copy
- [ ] SMOKE-06 Load the copy in SMT5V

## Save workflow

- [ ] SAVE-01 Save round-trip verification
- [ ] SAVE-02 Switch screens with unapplied edits
- [ ] SAVE-03 Restore a backup
- [ ] SAVE-04 Invalid-hash warning

## Items

- [ ] ITEM-01 Column headers
- [ ] ITEM-02 Search by name/ID
- [ ] ITEM-03 Search by flags
- [ ] ITEM-04 Filtered Max/Clear
- [ ] ITEM-05 Per-item limits
- [ ] ITEM-06 Over-limit warning
- [ ] ITEM-07 Save/reload

## Essences

- [ ] ESS-01 Pixie Have + Used before
- [ ] ESS-02 Uncheck Used before
- [ ] ESS-03 Have off/on preserves history
- [ ] ESS-04 Filtered bulk actions
- [ ] ESS-05 Save/reload

## Alignment

- [ ] ALIGN-01 A Wish for a Fish dropdown
- [ ] ALIGN-02 Law/Chaos exclusivity
- [ ] ALIGN-03 Both-selected warning
- [ ] ALIGN-04 Filters and summary
- [ ] ALIGN-05 Raw offset/bit toggle
- [ ] ALIGN-06 Save/reload

## Meta

- [ ] META-01 Canon subsections
- [ ] META-02 Cycles cap
- [ ] META-03 Mark/clear endings
- [ ] META-04 Copy warning and sync
- [ ] META-05 Satan flag
- [ ] META-06 Miracles no longer has Satan flag

## Demons

- [ ] DEMON-01 Efreet skill IDs hidden
- [ ] DEMON-02 Learn types
- [ ] DEMON-03 Show skill IDs
- [ ] DEMON-04 Mechanics tooltip
- [ ] DEMON-05 Stats labels
- [ ] DEMON-06 Recalculate current
- [ ] DEMON-07 Heal HP/MP
- [ ] DEMON-08 Direct Current editing
- [ ] DEMON-09 Affinity change
- [ ] DEMON-10 Potential change
- [ ] DEMON-11 Save/reload/in-game

## Laylines

- [ ] LAYLINE-01 Region grouping
- [ ] LAYLINE-02 Search/filter
- [ ] LAYLINE-03 Status columns
- [ ] LAYLINE-04 Details panel
- [ ] LAYLINE-05 Teleport selection
- [ ] LAYLINE-06 In-game position/unlock
- [ ] LAYLINE-07 Invalid last-layline warning

## Data pipeline

- [ ] DATA-01 Miracle categories
- [ ] DATA-02 No uncategorized miracle fallback
- [ ] DATA-03 Generated quest data loads

## Regression

- [ ] REG-01 Demon selector/creation
- [ ] REG-02 Player names/stats
- [ ] REG-03 DLC screen
- [ ] REG-04 Theme switching
- [ ] REG-05 Backup manager
- [ ] REG-06 Save hash verification

## Failures / blocked tests

-
