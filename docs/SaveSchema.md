# Save schema (working notes)

This is a working cross-reference between the binary save layout, the
`docs/GameSave.md` offset notes, and the C++ structs exposed by the
SMT5V modding headers.

It is not a complete format specification. Treat anything marked **inferred**
as a hypothesis to verify against a real save before writing.

## Scope

- PC / Steam saves
- Game save size: `449680` bytes (`0x6dc90`)
- SysSave size: `4832` bytes (`0x12e0`)
- Unreal Engine: `4.27.2`
- GVAS package version: `522`

Confidence labels:

- **verified** — observed in a real save and/or covered by tests
- **inferred** — consistent with the structs and offsets, but not fully proven
- **unknown** — not mapped yet

## Container and GVAS header

Both save types are standard UE 4.27 GVAS files wrapped in a 0x40-byte prefix.

| Range | Contents | Confidence |
| --- | --- | --- |
| `0x00-0x14` | SHA-1 of `data[0x40:]` | verified |
| `0x14-0x40` | Platform wrapper / unhashed data | unknown |
| `0x40-0x44` | `GVAS` magic | verified |
| `0x44-0x4c0` | Standard GVAS header, 55 custom versions | verified |
| variable | Save class name | verified |
| after class | Custom payload, **not** tagged UE properties | verified |

| File | Class | Custom payload |
| --- | --- | --- |
| `GameSave**.sav` | `SaveObject` | `0x4d0` |
| `SysSave.sav` | `SystemSaveObject` | `0x4d6` |

There is no UE property-tag stream and no `None` terminator after the class
name. The game serializes its own data, so offset-based access is expected.
See `docs/GameSave.md` for the hash and encryption details.

## GameSave layout overview

| Range | Contents | Confidence |
| --- | --- | --- |
| `0x4d0-0x988` | Save/load header (`FSaveLoadHeaderData`) | inferred |
| `0x988-0xb60` | Player record (`FCharData`) | verified |
| `0xb60-0x3d10` | 30 demon records (`FNkmData`, 424 bytes each) | verified |
| `0x3d10-0x3d2e` | Party menu order, 30 bytes | verified |
| `0x3d2e-0x3d31` | Summoned demon indices, 3 bytes | verified |
| `0x3d31` | Max demon stock | verified |
| `0x3d32` | Macca | verified |
| `0x3d4a` | Glory | verified |
| `0x3d4e-0x3de0` | Miracle block | inferred |
| `0x3ece` | Magatsuhi gauge | inferred |
| `0x49d8-0x4c20` | Guest/partner records | inferred |
| `0x4c72-0x4ff2` | Item amounts, 896 bytes | verified |
| `0x4ff2-0x5129` | Item flags / `m_Get` region | unknown |
| `0x5129-0x523c` | Essence metadata | inferred |
| `0x567e-0x569a` | Current map IDs and position | verified |
| `0x59d52-0x5b412` | Quest records, 224 × 26 bytes | inferred |
| `0x69cf5-0x69cfd` | Alignment choice bitfield, 8 bytes | verified |
| `0x69a90` | Settings copy (`FSystemData`) | inferred |
| `0x18272-0x2db42` | Analyze/compendium data | inferred |

The custom payload order is not identical to the C++ `FGameData` member order.
Use this table for binary offsets and the struct list below for field names.

## Header: `FSaveLoadHeaderData`

The C++ header describes the save/load header as:

- `int32 m_State`
- `int32 m_SlotIndex`
- `int32 m_Version`
- `int32 m_SaveType`
- `FString m_Name`
- `int32 m_DebugRandValue`
- `FDateTime m_Date`
- `uint8 m_Difficulty`
- `int32 m_TotalPlayTimeSec`
- `TArray<FBattlePartyData> m_BattlePartyData`
- `uint8 m_LastRyuketsuTableIndex`
- `uint8 m_ClearRound`
- `uint8 m_ClearAlignment`
- `int32 m_LoacationMessageId`
- `bool m_CanInherit`
- `TArray<uint8> m_joinDlcFlag`
- `uint8 m_LanguageType`
- `uint8 m_PlayNewOldRoute`
- `bool m_EnablePlayGoLoad`
- `bool m_IsTrialSave`

Known header offsets from `docs/GameSave.md`:

| Offset | Field | Confidence |
| --- | --- | --- |
| `0x4d8` | Save-screen name (fixed UTF-16) | verified |
| `0x4f4` | Save time (`FDateTime`, 100 ns ticks) | verified |
| `0x4fc` | Difficulty | verified |
| `0x502` | Cycles copy | verified |
| `0x503` | Endings copy | verified |
| `0x524` | Save location | inferred |
| `0x528` | Clear flag | inferred |
| `0x5d0` | Play time, seconds | verified |
| `0x5d4` | Moon phase | inferred |

### Cycles and endings

- `0x6a08a` — editable cycle count, capped at 99 by the game.
- `0x6a08b` — ending bitfield (`0x01`–`0x20`).
- `0x502` / `0x503` — header copies of cycles and endings.
- The editor writes both the editable values and their header copies.

## Player: `FCharData`

The player record is `0x1d8` bytes, from `0x988` to `0xb60`.

| Offset | Field | Confidence |
| --- | --- | --- |
| `0x988` | Initial stats (`FAbilData`, 16 bytes) | verified |
| `0x998` | Stat changes (`FAbilData`) | inferred |
| `0x9a8` | Current stats (`FAbilData`) | inferred |
| `0x9b8` | Global flag / mystery value | inferred |
| `0x9bc` | Healable HP/MP | verified |
| `0x9c0` | Experience | verified |
| `0x9c8` | Level | verified |
| `0x9ca` | Stat points | verified |
| `0x9d0` | First name | verified |
| `0x9e8` | Last name / family name | verified |
| `0x9fc` | Given name copy | verified |
| `0xa10` | Full name | verified |
| `0xa38` | Skills, 8 × 8 bytes | verified |
| `0xa98` | Affinities | verified |
| `0xb38` | Potentials | verified |
| `0xb50` | Innate skill | verified |

The C++ field list additionally includes `m_PlayerType`,
`m_SkillSlotNum`, `m_AutoSkillSlotNum`, `m_AutoSkill`,
`m_FortifyDefenceAishou`, `m_BuildSkillTekisei`,
`m_FortifySkillTekisei`, and `m_UniqueSkill`. Their exact binary offsets are
still being mapped.

## Demon: `FNkmData`

Each demon record is `0x1a8` (424) bytes. The table starts at `0xb60` and has
30 slots.

| Offset | Field | Confidence |
| --- | --- | --- |
| `0x00` | Initial stats (`FAbilData`, 16 bytes) | verified |
| `0x10` | Stat changes | verified |
| `0x20` | Current stats | verified |
| `0x30` | Fourth stat block / fortified values | inferred |
| `0x40` | Garden data: trust, talk desire, flags | inferred |
| `0x44` | Talk desire / friendship-related value | inferred |
| `0x60` | Battle entry / summoned marker | verified |
| `0x64` | Healable HP/MP | verified |
| `0x68` | Experience | verified |
| `0x70` | Level | verified |
| `0x72` | Demon ID (`0xffff` = empty) | verified |
| `0x78` | Skills, 8 × 8 bytes | verified |
| `0xd8` | Affinity block (short) | inferred |
| `0x108` | Affinity block (full) | inferred |
| `0x148` | Unknown / flags | unknown |
| `0x150` | Unknown / flags | unknown |
| `0x160` | Fight counter / flags | inferred |
| `0x180` | Potentials | verified |
| `0x198` | Unique/innate skill | verified |
| `0x19c` | Bonus/guest marker | inferred |

C++ `FNkmData` also exposes `m_EncountCnt`, `m_SkillSlotNum`,
`m_AutoSkillSlotNum`, `m_AutoSkill`, `m_BtlEntryCnt`,
`m_skillExIntervalCnt`, `m_GaveSoulGift`, `m_IsBonusDevil`, and
`m_GlobalEntryId`. These are the fields a complete "new demon" template must
set.

`m_GuestBackupData`, `m_PartnerData`, and `m_ShiseijoBackupData` in
`FPartyData` are the likely owners of the `0x49d8-0x4c20` region (guest and
partner demons such as Yoko, Tao, Yuzuru, Ichiro, and the Demi-fiend).

## Items: `FItemSaveData`

The item amount table is contiguous:

- Start: `0x4c72`
- Length: `896` bytes
- Mapping: `offset = 0x4c72 + item_id`

| Item IDs | Category |
| --- | --- |
| `0-220` | Consumables |
| `221-615` | Essences |
| `616-655` | Relics |
| `656-855` | Key items |
| `856-895` | Relics |

The first used essence in a typical save is ID `311` at `0x4da9` (Khonsu).
Lower essence IDs are valid but may be zero/unused. This matches
`data/items.py` and resolves the apparent gap in older notes.

`FItemSaveData` also has `m_Get`, which starts at `0x4ff2`
(`0x4c72 + 0x380`) and mirrors the item IDs. For essences, the byte is a
history/status bitflag:

| Bit | Meaning |
| --- | --- |
| `0x02` | New |
| `0x04` | Owned / seen |
| `0x10` | Used before |

The amount byte and the `m_Get` byte are independent. An essence can have
`amount = 1` and the used-before bit set at the same time.

## Quests: `FMissionSaveData`

Quest records start at `0x59d52`, size `26` bytes, and there are 224 of them.
The current editor exposes five bools. The C++ struct also contains:

- `E_TIME_ATTACK_MISSION_STATE TimeAttackState`
- `int32 MoonAgePassed`
- `int32 MoonAgeReported`
- `TArray<int32> CurrentValues`
- `TArray<int32> LastReportedInfos`

The 26-byte record is therefore much richer than the five bools currently
mapped.

## Map and exploration: `FMapData`

The C++ map struct explains several previously separate-looking regions:

- `m_TakaraFlag`, `m_TakaraBreakFlag` — treasure chests
- `m_MinimapMaskOpenFlag` — revealed terrain
- `m_MagatsukaState` — Magatsuhi spots
- `m_RyuketsuFlag` — laylines
- `m_RelicFlag`, `m_RelicTimer`, `m_RelicOnceFlag` — relics
- `m_MimanFlag`, `m_MimanPositionFlag` — Miman
- `m_MinimapIconShowFlag`, `m_MinimapIconFogGridFlag`,
  `m_MinimapIconHideFlag` — map icons
- `m_FogGrid` — fog grid records
- `m_PlayerPos` — player transform

The large terrain block around `0xab82` and the icon blocks around `0x11xxx`
are believed to be fields of `m_Map`, not independent systems.

## SysSave: `FSystemData`

`SysSave.sav` uses the same GVAS and hash scheme as a game save. The C++ header
contains the full settings list, including:

- Volumes: master, BGM, environment, SE, voice (floats)
- Voice language, vibration, camera speed/reverse/auto-centering
- Difficulty, play time, last slot
- Message speed, minimap/panel display, font size
- Battle cursor, auto-battle, skill display/shortening
- Gamepad/keyboard action and axis mappings
- DLC enable/announced flags
- Camera control, subtitles, stick/mouse sensitivity
- Brightness, AO, motion blur, anti-aliasing, resolution, VSync, frame rate

The documented `0x3f80` volume value is the float `1.0`, not a u16.

## Provenance

Sources for this document:

- `docs/GameSave.md` and `docs/SysSave.md` in this repository
- Controlled save diffs in `docs/experimentation/`
- Direct inspection of decrypted PC saves
- The C++ struct declarations published by
  [SMT5V-Project](https://github.com/bombasticmori/SMT5V-Project)

SMT5V-Project does not currently ship a license file. Do not copy its headers,
assets, or extracted game data into this repository. This document is a
summary of observed facts and field names, not a redistribution of those
files.

## Open questions

- Exact serialization of `FSaveLoadHeaderData` and `FGameData` arrays
- Guest/partner record boundaries and sizes
- `m_Get` and item flag encoding
- Quest `CurrentValues` / `LastReportedInfos` layout
- Full `m_Map` array offsets and sizes
- `m_DataBase` / compendium mapping
- Whether a save format version field exists beyond the GVAS header
