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

## Item limits

`item_extra_data.json` limits were checked against the game's
`Project/Content/Blueprints/Gamedata/BinTable/Item/ItemTable` asset. The asset
is an `MMIAsset` whose `MyFmtData` property contains a TBCR table.

- Consumables: table 0; `m_ItemID` at `+0x10`, `m_HaveMax` at `+0x3a`.
- Key items: table 3; `m_ItemID` at `+0x00`, `m_HaveMax` at `+0x05`.

These offsets are specific to the current PC save version and should be
re-checked after a game update.
