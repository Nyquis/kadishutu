# Safety and advanced editing

The editor warns about unusual or game-managed values but does not block them.
A save that the game will accept is still allowed.

## Advanced editing

Advanced editing is a global toggle in the status bar (`Advanced: OFF`) and in
the **Edit** menu. It is remembered between sessions.

Safe mode still shows every field. It only locks values that the game derives
or recalculates:

- Nahobino and demon level and EXP
- stored `Current` stats on the Stats screen
- direct editing of derived blocks

Advanced mode unlocks those fields. The warnings stay visible, and the game
may still overwrite the value later.

There are no per-screen advanced checkboxes. The global toggle is the single
gate for level/EXP, stored Current stats, and raw skill IDs.

## Risk badges

| Badge | Meaning |
|---|---|
| `game-managed` | The game may recalculate this after battle, death, revival, level-up, and so on. |
| `separate fields` | Related fields are stored separately and are not updated automatically. |
| no badge | A normal stored value. |

Current and Healable HP/MP are game-managed. Changing them is valid, but the
game may clamp or restore them.

## HP = 1 preset

The Stats screen has a **Set HP to 1** button.

- It sets **Healable HP** to 1 and leaves max HP unchanged.
- This is the stored current HP used in battle.
- The game may restore or clamp it after battle, death, revival, or healing.
- The editor shows a warning when the value is 1.

This is intentionally a warning, not a restriction. The save remains valid.

## Demon growth

The demon screen shows two compact growth tables:

- HP/MP: `Current`, raw `Growth`, and an estimated `Est. /level`
- Core stats: `Current`, `Weight %`, and `Avg/level`

`Weight %` is normalized by `Growth Total`, which is 100 for most demons but
can be 98–104. `Avg/level` assumes three core-stat points per normal level-up.

HP/MP `Est. /level` is a corpus estimate (`growth / 4` and `growth / 6`), not a
confirmed game formula. Prayers and fusion add points outside both tables.

The demon detail screen scrolls, so the growth tables keep their row heights
even when the demon graphic is visible on a short window.

## Demon creation

The creation list uses the game's `Compendium` flag:

- Safe mode shows only normal compendium demons.
- Advanced mode also shows enemy, boss, shadow, and NPC entries.
- Non-compendium entries are muted and marked `· Enemy`.
- Selecting one shows a warning; turning Advanced off clears the selection.

The whole creation screen scrolls, so the form and preview do not overlap on
short windows.

## Progression screen

The Progression category grants items:

- Gospels and Grimoires
- Balms for Nahobino stats
- Incenses for demon stats
- Sutras for demon potentials

The screen does **not** plan levels or emulate a level-up. It changes inventory
amounts, and the game applies the actual level-up or stat increase. That keeps
random demon growth, prayer bonuses, caps, and skill learning in the game where
they belong.

Each row has `+1`, `+5`, and `Max` buttons and respects the item limit. Hover a
row to see the item's effect and ID. Sutra tooltips name the potential without
renaming the item, for example:

- `Aiding Sutra` -> Support potential
- `Healing Sutra` -> Recovery potential
- `Calamity Sutra` -> Ailment potential

The screen scrolls, so the item rows stay readable at narrow window sizes.

## Backups

Saving to disk still creates a backup. Advanced mode is not a substitute for a
backup: use a disposable copy when testing unusual values.
