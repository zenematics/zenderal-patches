# ReadTheRoomEnderal

- **Source:** `src/ReadTheRoomEnderal/`
- **Ships:** `Zenderal - Read the Room Enderal.esp` (ESL, HEDR 1.7, one override)
- **FormID block:** none
- **Pillar:** bug fix (a list mod that did nothing in Enderal)

## Why

*Read the Room - Immersive and Animated Helmet Management* 2.2.1 (Nexus 77605) takes the helmet off or puts it on in
`ReadTheRoomMonitor.OnLocationChange` by checking the new location for keywords in two FormLists **[verified from
its source and records]**:

- `SafeKeywords 00080A`: `LocTypeDwelling`, `LocTypeCity`, `LocTypeTown`, `LocTypeSettlement`, `LocTypePlayerHouse`
- `HostileKeywords 000804`: `LocTypeClearable`, the dungeon/camp `LocType*` and `LocSet*` keywords (21 entries)

Those are Skyrim's location keywords, and Enderal barely uses them. Of its 159 locations
(`reference/base/Skyrim` + `EnderalFS`, 2026-10-26), only **Ark** carries `LocTypeCity`, four interiors carry
`LocTypeDwelling` and one `LocTypeSettlement`. Only one location (`AbandonedPrisonLocation`) carries a hostile keyword.
So Riverville, Duneville, the Sun Temple and almost every inn never counted as safe, and the helmet stayed on.
The mod itself loaded fine: its plugin was ticked, IED 1.7.4 loaded, and the Pandora output has its animations. Its
Papyrus log errors are only `None` checks before a helmet has been seen.

Enderal marks its towns with its own keywords:

| Keyword | Locations |
|---|---|
| `_00E_Theriantrophist_NoTransformLocationTown 02EAA6` | 59: Ark and all its shops/houses, Riverville (`FlusshaimLocation`), its tavern, Duneville, Dunehome, the Sun Temple and its rooms, Snowcliff tavern, the farm coast, Undercity living quarters |
| `_00E_Phasmalist_NoSummonLocationTown 01E9FC` | 43 |

## What it does

Overrides `SafeKeywords 00080A:ReadTheRoom.esp` with its 5 entries unchanged, plus those two keywords. Nothing
else in the list masters `ReadTheRoom.esp` (2026-10-26).

Enderal has no dungeon keyword to add to `HostileKeywords`, so set **Equip when** to *leaving a safe area* in Read the
Room's MCM (global `EquipWhenSafe` = 1). The default (0, *entering a hostile area*) almost never fires in Enderal.
Combat Equip (on by default) still puts the helmet on when a fight starts.

## Status

Built 2026-10-26: deserialize/serialize round trip identical apart from the header description's wrapping; bytes
checked (ESL, 1.7, masters Skyrim/Update/FS/ReadTheRoom, FLST `0300080A` with 7 entries). Deployed as the MO2 mod
`Zenderal - Read the Room Enderal`. **Unverified in game.**

## Rest of the setup (2026-10-26)

- **Helmet Toggle 2 disabled** (mod and plugin): a second helmet manager. The generated
  [`UnresolvedRefsCleanup`](UnresolvedRefsCleanup.md) mastered it for two records, so those were dropped from its
  YAML and it was rebuilt (40 masters, 2 records fewer, otherwise the same).
- **Immersive Equipping Animations' head animations off**, as Read the Room's page asks: `bIDA_DressHead`,
  `bIDA_UndressHead`, `bIDAF_DressHead` and `bIDAF_UndressHead` = 0 in *Zenderal - Settings*'
  `MCM/Settings/Immersive Equipping Animations.ini` (MCM Helper, file-based). Its body/hands/feet/neck/ring
  animations are unchanged.
- **Equip = "Leaving safety"** set on every save by [`SettingsApplier`](SettingsApplier.md) (the MCM label keeps
  showing the default).
- The *IED - Unequipped Helmets on Waist* custom profile is installed but not applied in IED's config, so it does
  not double the hip helmet.

Backups: `E:/Zenderal-backups/2026-10-26-read-the-room/`.
