# Leveling

This note records what the game data already explains about leveling, and what
still needs in-game measurements.

## Nahobino stats

`PlayerGrow` (`Project/Content/Blueprints/Gamedata/BinTable/Common/PlayerGrow`)
is an `MMIAsset` with 14 TBCR tables.

- Table 2 holds one 28-byte row per level: seven `int32` values
  `(HP, MP, STR, VIT, MAG, AGI, LUK)`.
- Row index is the level. Row 0 is unused; rows 1-150 cover levels 1-150.
- These are **base stats before allocated stat points**.

Checked against real saves:

| Level | Table HP/MP | Table STR/VIT/MAG/AGI/LUK | Save base stats | Difference |
|---:|---|---|---|---|
| 4 | 55 / 70 | 5 / 6 / 5 / 6 / 6 | 55 / 70 / 6 / 6 / 5 / 6 / 6 | `+1 STR` |
| 55 | 328 / 257 | 36 / 36 / 36 / 36 / 37 | 328 / 257 / 102 / 40 / 36 / 51 / 37 | `+66 STR, +4 VIT, +15 AGI` |

The differences sum to the save's `stat_points` value (1 at level 4, 85 at
level 55), so `stat_points` is the total number of points already allocated,
not the number of unspent points.

Regenerate the committed table with:

```shell
pixi run python -m tools.save_lab.leveling_metadata
```

The output is `src/kadishutu/data/tables/nahobino_leveling.json`.

## EXP

`PlayerGrow` table 3 holds 149 `int32` values indexed by `level - 1`.
Each value is the EXP needed to advance **one level**, not a cumulative total.

- Nahobino: `exp_to_next(level) = table[level - 1]`
- Level 150 is the table maximum and has no next-level requirement.
- The save's `exp` field is progress inside the current level, not total EXP.
  This is consistent with the low-level test save (level 4, 0 EXP) and with
  the demon entries below.

Examples:

| Level | EXP to next |
|---:|---:|
| 1 | 32 |
| 4 | 126 |
| 55 | 140,518 |
| 149 | 727,576 |

### Demons

A demon's requirement is based on the Nahobino curve multiplied by a factor
that grows with the demon's level above its species' base level:

| Levels above base | 0 | +1 | +2 | +3 | +4 | +5 | +6 | +7 | +8 | +9 | +10 or more |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Multiplier | 1.5 | 2.0 | 2.57 | 3.23 | 3.96 | 4.77 | 5.66 | 6.63 | 7.67 | 8.8 | 10.0 |

```text
demon_next_exp(level, base_level) =
    trunc(nahobino_next_exp(level) * multiplier(level - base_level))
```

The multiplier table is community-measured, so it is the least certain part of
the model. It is implemented in `kadishutu.data.leveling`.

The multiplier rule explains the corpus values: every demon's stored EXP is
smaller than its computed requirement, and the ratio varies between roughly
12% and 63%. Treating the same values as total EXP would contradict the level
ordering.

## Demon stat growth

`NKMBaseTable` (already committed as `Players.csv`) stores, per demon:

- base level and base `HP/MP/STR/VIT/MAG/AGI/LUK`;
- `HP Growth` and `MP Growth`;
- `STR/VIT/MAG/AGI/LUK Growth` weights plus `Growth Total`;
- `Skill Level 1-12` and the skill learned at each of those levels.

The growth fields are now parsed into `DemonGrowth`
(`kadishutu.data.demons`). The weights are relative, not flat per-level gains:
for example Idun is `19/25/13/16/28/21/22`, total `100`.

Observed save deltas over several levels do **not** match the raw weights.
Demon stats in saves also reflect other adjustments that are not yet
understood. A controlled level-up diff is still needed before the exact
formula can be predicted.

## Editor behavior

The Progression screen uses this data for a read-only plan and grants
Gospels/Grimoires instead of writing level-ups directly. In-game items run the
real level-up logic, including stat growth, prayers, caps, and skill learning.

Level and EXP fields are locked unless Advanced editing is enabled. Changing
them never updates stats or skills automatically.

## Still unknown

- Exact demon per-level stat gain formula (weights are confirmed inputs only).
- Whether `PlayerGrow` tables 0 and 1 are dummy rows or belong to other player
  types.
- Nahobino level-up skill unlocks. `PlayerAddGetSkillTable` exists as a struct
  but its asset was not found in the paks.
- Stat-point sources per level (level-ups plus miracles).
