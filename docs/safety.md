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

## Risk badges

| Badge | Meaning |
|---|---|
| `game-managed` | The game may recalculate this after battle, death, revival, level-up, and so on. |
| `derived` | Related fields are stored separately and are not updated automatically. |
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

## Progression screen

The Progression category plans levels and grants items:

- current level and EXP progress
- target level
- EXP and Gospels needed
- Gospel and Grimoire amounts
- Balm and Incense amounts

The screen does **not** emulate a level-up. It changes inventory amounts, and
the game applies the actual level-up or stat increase. That keeps random demon
growth, prayer bonuses, caps, and skill learning in the game where they belong.

Gospels and Grimoires grant exactly one level in game. The `Set Gospels to
cover target` button never lowers an existing stock and respects the item
limit.

Balms and incenses are stat-up items. Their exact caps and messages are applied
by the game, not by the editor.

## Backups

Saving to disk still creates a backup. Advanced mode is not a substitute for a
backup: use a disposable copy when testing unusual values.
