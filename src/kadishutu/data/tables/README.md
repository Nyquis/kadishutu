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
