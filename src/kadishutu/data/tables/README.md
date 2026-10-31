# Source

[Gamebanana Post](https://gamebanana.com/posts/11793083)

[Skill Tables](https://docs.google.com/spreadsheets/d/1qqAH0bFeck0k_BcItcgH3xrV7uCryBwTVerv-iA8Ynw/edit?usp=sharing)

[Demon Tables](https://docs.google.com/spreadsheets/d/15W1WpIfx-h9wYEmXlnPiPTpgAAlsWZ7-M8xiwhVzAN8/edit?usp=sharing)

## Changes

`SMT5V NKM Base Table_Navi Devil Data - Players.csv`

- Added `Pot` prefix to potential values to avoid conflicts

`SMT5V Skill Data Tables - ActionSkills.csv`

- Replaced `∞` with `inf` as per
  [pewbayeaj on GameBanana](https://gamebanana.com/posts/12025667)

## Item metadata

Limits, categories, and basic flags are generated into `items.generated.json`
from the game's `Project/Content/Blueprints/Gamedata/BinTable/Item/ItemTable`
asset. The asset is an `MMIAsset` whose `MyFmtData` property contains a TBCR
table. `item_extra_data.json` keeps only the local names/icons/descriptions.

- Consumables: table 0; `m_ItemID` at `+0x10`, `m_HaveMax` at `+0x3a`,
  `m_UseScene` at `+0x2e`, `m_IsUseInfinite` at `+0x2f`,
  `m_UseTarget` at `+0x3e`.
- Key items: table 3; `m_ItemID` at `+0x00`, `m_HaveMax` at `+0x05`.

Regenerate with:

```shell
pixi run python -m tools.save_lab.item_metadata
```

These offsets are specific to the current PC save version and should be
re-checked after a game update.

## Other generated metadata

The same `MMIAsset`/TBCR pipeline generates miracle and quest metadata without
requiring an optional game asset pack.

- `miracles.generated.json` — `GodParameterDataTable`, table 0, 20-byte rows.
  The row format is `<HIB5sH?5s` (`id`, `order_id`, `category`, padding,
  `cost`, `toggleable`, padding).
- `quests.generated.json` — `MissionTable`, table 0, 372-byte rows. Quest IDs
  are the first two bytes (`<H`) of each row.

Regenerate them with:

```shell
pixi run python -m tools.save_lab.miracle_metadata
pixi run python -m tools.save_lab.quest_metadata
```

Run the CUE4Parse CLI export first and place the JSON output under
`lab/dumps/game-tables-json/`. Demon and map data already have committed local
datasets (`Players.csv`, `laylines.json`), so they do not need extraction yet.

## Alignment choices

`alignment_data.json` decodes the 8-byte alignment bitfield at
`0x69cf5-0x69cfc`. Each entry records the save offset, bit, Law/Chaos value,
place, optional side quest, and the text of the choice.

Every pair of bits describing the same decision shares a `group` value. For
example, both sides of **A Wish for a Fish** use `"group":
"a-wish-for-a-fish"`. The UI shows one dropdown per group because the options
are mutually exclusive.

The data is based on the save experiments in `docs/GameSave.md` and
`docs/cheatroom_blog_post_translation.md`. Some choices are still marked
`"unknown"` where the alignment has not been verified. The editor also reports
unmapped bits instead of silently ignoring them.
