# Documentation

Start with the safety guide before editing a real save.

## User guides

- [Safety and advanced editing](safety.md) - backups, Advanced mode, warnings,
  HP = 1, item grants.
- [Manual testing](manual-testing.md) - the long-lived manual test catalog.
- [Troubleshooting](Troubleshooting.md) - recovery and known edge cases.

## Mechanics

- [Leveling and growth](leveling.md) - Nahobino stat and EXP tables, demon EXP
  multipliers, growth weights, and the HP/MP estimate.
- [Save location fallback](GameSave.md#save-location) - how the open-save
  preview resolves a location when the title mapping is missing.

## Save format and internals

- [GameSave.md](GameSave.md) - game save layout and offsets.
- [SaveSchema.md](SaveSchema.md) - cross-reference between offsets and the
  game's structs, with confidence labels.
- [SysSave.md](SysSave.md) - system save settings and volume slots.
- [Random offsets](random_offsets.md) - raw notes kept for reference.

## Research notes

- [Cheatroom blog post translation](cheatroom_blog_post_translation.md) -
  alignment research. Not a user guide.

## Developer material

- [AGENTS.md](../AGENTS.md) - project conventions, commands, domain rules, and
  release workflow.
- [Data tables and generators](../src/kadishutu/data/tables/README.md) - how
  generated JSON is produced.
