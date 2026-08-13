# World and dungeons — regions, locations, the map-marker census

Reference for Enderal's geography as it exists in the records: which region records are real
places, why the usual Skyrim dungeon-indexing machinery (Locations, EncounterZones) is absent, and
the census of every map marker in the game — which *is* Enderal's dungeon index.

Worldspaces are enumerated in [`visuals-and-world.md`](visuals-and-world.md#worldspaces) and not
repeated here. What matters below: the overworld is **`Vyn 001D3C:Skyrim.esm`** ("Vyn, Enderal"),
it carries `CannotFastTravel` — fast travel is the Myrad-tower network, see the census — and FS
adds exactly **one** new worldspace (`FS_NQ01_Qyra_Island 00A6A0`, "Strange Place"); its other 15
worldspace entries are overrides. **[verified]**

Counts taken **2026-08-13** against `reference/base/` (Enderal SE 2.0.12.4).

## Regions: 22 real places among 114 records

**100 REGN in base Enderal, 14 in FS** (4 new + 10 overrides). **[verified]** But a region record
is only a *place* if it carries a `Map:` block — that is the **only** home of a region's display
name (there is no top-level `Name:` on REGN). Only **22** qualify; the other ~92 are weather
zones (15), ambient-sound zones (21), combined weather+sound (12+), one object-placement region,
and **30 completely empty records** — mostly navmesh-generation scratch (`HerzlandNavmesh01–04`,
`NavmeshWste`) and vanilla audio leftovers (`AudioIntDungeonCave01`…). **[verified]**

The 22 named regions **[verified]**:

| EditorID | FormKey | Map name (EN) | Worldspace |
|---|---|---|---|
| `oJohannes` | `0020F3:Skyrim.esm` | **Heartland** | Vyn |
| `NicoSonnenkueste` | `037B8B:Skyrim.esm` | **Sun Coast** | Vyn |
| `Nordwindgebirge` | `0823E4:Skyrim.esm` | **Frostcliff Mountains** | Vyn |
| `Schneepass` | `10D11A:Skyrim.esm` | Frostcliff | Vyn |
| `Wueste` | `139C4D:Skyrim.esm` | **Powder Desert** | Vyn |
| `Jonas` | `0023A3:Skyrim.esm` | **Dark Valley** | Vyn |
| `Bauernkueste` | `074543:Skyrim.esm` | **Farmers Coast** | Vyn |
| `PilzwaldRegion` | `00703D:Skyrim.esm` | Whisperwoods | Vyn |
| `QuellwachtRegion` | `035CCA:Skyrim.esm` | Goldenforst | Vyn |
| `SilberhainRegion` | `08B19D:Skyrim.esm` | Silvergrove | Vyn |
| `eThalgardRegion` | `0022AB:Skyrim.esm` | Thalgard | Vyn |
| `Nebelhaim` | `10A875:Skyrim.esm` | Cliff of Fogville | Vyn |
| `WesternCliff` | `048089:Skyrim.esm` | Western Cliff | Vyn |
| `oJohannesBergpass` | `039293:Skyrim.esm` | Mountain Pass | Vyn |
| `Templeregion` | `0CE136:Skyrim.esm` | Sun Temple | CapitalCityUpperTemple |
| `CapitalCityCastleRegion` | `139A24:Skyrim.esm` | Ark, Barrack Quarter | CapitalCityCastleWorld |
| `CaptialCityStrangerAreaRegion` *(sic)* | `139A21:Skyrim.esm` | Ark, Foreign Quarter | CapitalCityStrangerArea |
| `CapitalCityMarketDUPLICATE001` | `139A20:Skyrim.esm` | Ark, Marketplace | CapitalCityMarketArea |
| `CapitalCityUpperCityRegion` | `139A23:Skyrim.esm` | Ark, Nobles Quarter | CapitalCityUpperCity |
| `CapitalCityLowerCityDUPLICATE001` | `139A22:Skyrim.esm` | Ark, South Quarter | CapitalCityLowerCity |
| `NicoSonnenkuesteTemple` | `0133E0:Enderal - Forgotten Stories.esm` | Sun Coast | *(none set — FS-new)* |
| `Desert` | `043C5D:Skyrim.esm` | ~~Ark, Marketplace~~ | *(none set)* |

Three data-quality warnings, all shipped in the game **[verified]**:

- **`Desert 043C5D`'s English map name is wrong** — it reads "Ark, Marketplace", a copy-paste from
  the real marketplace region. This is the one known case where even the *English* string lies;
  do not quote it as the Powder Desert's identity (`Wueste 139C4D` is the real desert region).
- EditorIDs are chaos: German (`Nordwindgebirge`, `Wueste`), developer first names (`Jonas` = Dark
  Valley, `oJohannes` = Heartland; `Martin`, `DennisHS`, `NicoSullevan` exist among the unnamed
  ones), `*DUPLICATE001` names in shipping data, and one typo (`Captial…`).
- Region membership on exterior cells is the cell's `Regions:` FormKey list — 4,370 of Vyn's
  14,811 exterior cells carry one. **[verified]** That, not the polygon, is the practical way to
  ask "which region is this cell in".

## Why there is no dungeon index

The two systems a Skyrim modder would reach for are both effectively absent **[verified]**:

- **Locations (LCTN): 90 base / 69 FS records, and they are not a dungeon layer.** The vanilla
  `LocType*` keywords all still exist as KYWD records, but across all locations
  **`LocTypeDungeon 0130DB` is used exactly once** — on `AbandonedPrisonLocation 0ECF4C` — and
  `LocTypeDraugrCrypt`, `LocTypeBanditCamp` etc. never. The hierarchy is shallow and city-centric: 30 of the 48 `ParentLocation` links
  point at `CapitalCityLocation 0A1A12` (Ark's shops), 14 at `_00E_UEMasterLocation 103392` (the
  Undercity). Only 183 of 415 interior cells set `Location:` at all — entire dungeon level chains
  (e.g. `AltIniath04BOSS 020AFC`) are orphaned from any location.
- **EncounterZones (ECZN): two records in the whole game, neither carries a level.**
  `NoZoneZone 00001E` and `_00E_NoRespawn 046AEC` (`Flags: [NeverResets]`) — no `MinLevel`, no
  `MaxLevel`, no location links. `_00E_NoRespawn` is referenced by exactly **four cells**: the two
  Ark player-house cells, `CapitalCityBankSafe 00990F`, and FS's `FSNQR05Temple03 01CB21` — it is
  a respawn suppressor for player storage, nothing more. **Skyrim's encounter-zone difficulty
  system is abandoned**; dungeon difficulty is the fixed levels of the hand-placed actors inside
  (see [`bestiary.md`](bestiary.md)).

## The dungeon index Enderal actually has: map markers

Every Vyn map marker is a `PlacedObject` with `Base: 000010:Skyrim.esm` in **one file** —
`reference/base/Skyrim/Worldspaces/Vyn - 001D3C_Skyrim.esm/RecordData.yaml`, inside
`TopCell: → Persistent:`. None live in the 14,811 exterior cell subfolders. **[verified]** Each
carries a localized `MapMarker.Name`, a `Type:` enum (the map icon), and `Placement.Position`
(world coords; cell grid = `floor(coord/4096)`).

**Vyn has 212 markers** — 211 base + 1 added by FS's Vyn override ("Excavation Site", a Camp).
The Ark sub-worldspaces add 8 more (3 in the South Quarter, 2 in the Castle world, 1 each in
Market/Foreign/Nobles). **[verified]** Type histogram for Vyn:

| Type | n | Type | n | Type | n |
|---|---:|---|---:|---|---:|
| Cave | 27 | Settlement | 14 | WoodMill | 4 |
| Fort | 18 | Shack | 12 | Docks | 4 |
| Camp | 18 | ImperialTower | 11 | WheatMill / Grove / Shipwreck | 3 each |
| Farm | 16 | DwemerRuin | 10 | Clearing / OrcStronghold / Pass | 2 each |
| Mine | 16 | NordicRuins | 8 | City | 5 |
| Landmark | 15 | NordicTower | 6 | Lighthouse | 5 |

…plus one each of Town (Riverville), WhiterunCapitol (Fogville), WindhelmCastle (Castle
Goldenford), DragonLair (Dragon Aerie), Stable, Shrine, Doomstone, Altar — the vanilla enum
pressed into Enderal service, so **the icon type is a Skyrim concept and the name is the truth**.

Reading the census as a dungeon list (~85 dungeon-grade markers = Cave + Mine + DwemerRuin +
NordicRuins + Fort + NordicTower):

- **The `DwemerRuin` icon means a Starling ruin**, and SureAI names them as a set: *Old Dothûlgrad,
  Old Askamahn, Old Hatolis, Old Iniath, Old Miskahmur, Old Rashêngrad, Old Sherath, Old Soltyris,
  Old Uskasarak* + *Agnod*. "Old <name>" (`Alt<Name>` in cell EditorIDs) is the house convention
  for the fallen civilization's sites.
- **`ImperialTower` means Myrad tower** — the 11 of them are the fast-travel network that
  `CannotFastTravel` funnels the player through.
- The Fort ring (*Castle Ad'Balor, Castle Bleakstar, Castle Dal'Galar, Fortress
  Fogwatch/Rockwatch/Wellwatch, Old Silver Fortress, Northcliff Hold, The Sun Fire*…) and the
  NordicRuins set (*Old Yogosh, Old Darkesh, Thur, The Living Temple, Grels Grave*…) are the
  boss-tier destinations — cross-reference the boss roster in [`bestiary.md`](bestiary.md).

The full 212-row census is the appendix at the bottom of this file.

## Interior cells — how a dungeon is actually assembled

**415 interior cells in base Enderal, 193 in FS** (~16 FS-new, the rest overrides). **[verified]**
Conventions:

- EditorIDs are German with an `Alt` (= "Old") prefix for ruins and `L1..L4` / `BOSS` level
  suffixes: `AltDothulgradL1..L4` + `AltDothulgradSewers`/`Factory`/`Levelhub`,
  `AltIniath01..04BOSS`, `DesertPulverminenL1..L5`, `Baerenhoehle` (bear cave), `Friedhofsgruft`
  (cemetery crypt), `Frostwasserspalte` (Frostwater Chasm). **[verified]**
- A dungeon cell's header carries `Name` (localized), `Flags` (`IsInteriorCell`, `HasWater`,
  sometimes `ShowSky`), `LightingTemplate`, `AcousticSpace`, `Music`, `ImageSpace`, optionally
  `Location:` and `SkyAndWeatherFromRegion:` (e.g. `DesertAltSoltyrisL2 06E4F1` pulls weather from
  `QuellwachtRegion 035CCA`). **[verified]**
- **The traversal graph exists only as teleport-door pairs.** Levels chain via `Temporary:` door
  refs whose `TeleportDestination: {Door: <FormKey>, …}` points at the paired door — up the chain
  to the exterior door that stands near the map marker (`AltDothulgradL1 03E739`'s exit door
  `0A9B11` sits beside marker `0A9B15`). With LCTN mostly absent, door pairs are the only
  machine-readable "this dungeon has 4 levels" structure. **[verified]**

## What this means for patching

1. **There is no encounter-zone hook.** Mods that rescale dungeons via ECZN (the standard Skyrim
   approach) do nothing here. Difficulty changes mean editing the placed actors' records.
2. **The Vyn `TopCell` is one giant contested record.** All 212 markers live in the worldspace
   record's persistent cell — a patch adding or editing a map marker overrides refs inside
   `Vyn 001D3C`'s TopCell, the same surface FS already overrides. Copy the *winning* (FS) version
   of anything you touch there, and remember the exterior-scaffolding rules in CLAUDE.md
   ("Placing a ref in an EXTERIOR cell needs three scaffolding files").
3. **Don't trust LCTN for anything spatial.** A mod keying off `LocTypeDungeon`, location-based
   crime, or location events (`WIDragonAttacked` machinery) finds one or zero records. Location-
   aware SPID filters die the same way — see
   [`../tools/spid-in-enderal.md`](../tools/spid-in-enderal.md).
4. **Region names come from `Map:` blocks and one of them lies** (`Desert 043C5D`). Weather
   patches should target the weather regions (48 carry `Weather:` data), not the named map
   regions — they are mostly disjoint sets.
5. **`coc` navigation**: cell EditorIDs are German — `coc AltDothulgradL1`, not "Old Dothulgrad".
   The glossary in [`factions.md`](factions.md#german--english-glossary) plus the census below
   translate.

## Checklist for a world-touching patch

- [ ] If you touch a map marker or anything persistent in Vyn: did you start from FS's override of
      the worldspace record?
- [ ] If you place an exterior ref: did you build the three-file block/sub-block scaffolding
      (CLAUDE.md Gotchas)?
- [ ] Did you resolve the dungeon's cell chain by door pairs rather than assuming a Location tree?
- [ ] If you read a region name: is it from the `Map:` block, and is it not `Desert 043C5D`?

## Appendix: the full map-marker census

Generated 2026-08-13 from the `TopCell → Persistent` blocks; FS overlay applied (the one FS-added
marker is flagged). Sorted by type, then name. **[verified]**

### Vyn (212)

| Name | Type | FormKey | Position (x, y, z) |
|---|---|---|---|
| Old Temple | Altar | `14FC6B:Skyrim.esm` | -105525, 28543, 6391 |
| Alchemist's Abandoned Camp | Camp | `053B65:Skyrim.esm` | -79991, 47911, 867 |
| Bandit Camp | Camp | `0D587F:Skyrim.esm` | -146134, -23515, 1338 |
| Brigand Camp | Camp | `0D5871:Skyrim.esm` | -102121, -25179, 816 |
| Cliff Camp | Camp | `14FC75:Skyrim.esm` | -35379, -43876, 3186 |
| Excavation Site **(FS-added)** | Camp | `01CFBB:Enderal - Forgotten Stories.esm` | -83270, 116266, 34666 |
| Highwayman Camp | Camp | `0E09F0:Skyrim.esm` | -32071, -41100, 578 |
| Northwind Camp | Camp | `0375C6:Skyrim.esm` | -108556, 112423, 33880 |
| Old Logging Camp | Camp | `14FCE8:Skyrim.esm` | -52776, 13604, 2955 |
| Outlaw Camp | Camp | `0D5872:Skyrim.esm` | -111382, -22514, 368 |
| Pahtira's Camp | Camp | `14871D:Skyrim.esm` | 46314, 5392, 7064 |
| Pathless' Camp | Camp | `0D586E:Skyrim.esm` | -93531, -29128, 1730 |
| Poachers' Camp | Camp | `03CE8E:Skyrim.esm` | 9379, 10210, 6602 |
| Raider Camp | Camp | `132F42:Skyrim.esm` | -71645, 56103, 6403 |
| Scout Tower | Camp | `01CF57:Skyrim.esm` | -45727, -13639, 8127 |
| Tower Encampment | Camp | `132F43:Skyrim.esm` | -67985, 31669, 2471 |
| Vatyr Encampment | Camp | `022FE5:Skyrim.esm` | -30144, 41456, 376 |
| Vatyrs' Lair | Camp | `0548DF:Skyrim.esm` | -66726, 48496, 2684 |
| Wild Mage Camp | Camp | `13F566:Skyrim.esm` | -126531, 76449, 15601 |
| Bear Cave | Cave | `0E3B3D:Skyrim.esm` | -55661, 4802, 2147 |
| Brownrock Cave | Cave | `022FEB:Skyrim.esm` | -59952, 6245, 3663 |
| Cave at the King's Bay | Cave | `14C2A8:Skyrim.esm` | 5500, -32651, 142 |
| Family Crypt Keldron | Cave | `02A4A4:Skyrim.esm` | -53204, -2143, 2598 |
| Family Crypt of the Dal'Marak | Cave | `0F65AF:Skyrim.esm` | 35272, 42475, 1569 |
| Fogville's Sewer Exit | Cave | `14FC7B:Skyrim.esm` | -120772, 25638, 8001 |
| Frostwater Chasm | Cave | `14F7C3:Skyrim.esm` | -59198, 107210, 22610 |
| Glimmerdustcave | Cave | `0DAC8A:Skyrim.esm` | -114355, -43658, 55 |
| Glintwater Crevice | Cave | `0FEBFE:Skyrim.esm` | -77940, 15033, 3402 |
| Glowstone Grotto | Cave | `0F65DE:Skyrim.esm` | 9296, 52854, 4974 |
| Gravespath | Cave | `145341:Skyrim.esm` | 39480, 52490, 2978 |
| Grotto to the Wayside Cross | Cave | `01CF55:Skyrim.esm` | -31989, -7494, 2119 |
| Hermit Cave | Cave | `14383F:Skyrim.esm` | 48628, 70026, 41 |
| Kynea Grotto | Cave | `13B910:Skyrim.esm` | 42000, -34627, 272 |
| Lightgrove | Cave | `053B64:Skyrim.esm` | -97879, 47256, 2620 |
| Old Garagatha | Cave | `1482AB:Skyrim.esm` | -3336, 26782, 2618 |
| Old Ishmartep | Cave | `13E3BE:Skyrim.esm` | 84454, -39295, 1883 |
| Old Lyguria | Cave | `12FAA8:Skyrim.esm` | 65765, -38809, 1973 |
| Pirate Grotto | Cave | `12DDE8:Skyrim.esm` | 9502, 87268, 1038 |
| Pit Shelter | Cave | `108053:Skyrim.esm` | -30489, 12210, 3280 |
| Rock Shelter | Cave | `027CFB:Skyrim.esm` | -35066, 4916, 1921 |
| Sea Chasm | Cave | `0848F1:Skyrim.esm` | -34527, -52709, 484 |
| Small Sand Pit | Cave | `09DDF4:Skyrim.esm` | 65215, -42933, 3079 |
| Soul Bed | Cave | `127F5B:Skyrim.esm` | 49400, -24759, 1414 |
| Thalgard, Crematory | Cave | `036C35:Skyrim.esm` | 73640, 25444, 7219 |
| Water Station of the Throatstone Quarry | Cave | `14FC7C:Skyrim.esm` | -125156, 30055, 3346 |
| Waterhaze Maw | Cave | `14FC6A:Skyrim.esm` | -103611, 21593, 6657 |
| Ark, Harbor Gate | City | `045DB5:Skyrim.esm` | -12680, -19816, 456 |
| Ark, Northern Gate | City | `045DB4:Skyrim.esm` | -6440, 3088, 2584 |
| Ark, West Gate | City | `008627:Skyrim.esm` | -13300, -2802, 2047 |
| Duneville | City | `14B5C0:Skyrim.esm` | 83121, -49994, 26 |
| Thalgard | City | `022BA3:Skyrim.esm` | 54053, 42213, 10450 |
| Bone Farm | Clearing | `127CA5:Skyrim.esm` | -92457, 49434, 2874 |
| Sanctuary of the Gravespath | Clearing | `03D6EE:Skyrim.esm` | 20971, 67475, 6562 |
| Ark, Harbor | Docks | `011170:Skyrim.esm` | -9852, -25375, 522 |
| Fogville, Harbor | Docks | `11C1DF:Skyrim.esm` | -137952, 23627, 216 |
| Old Smuggler Retreat | Docks | `13823E:Skyrim.esm` | -20872, -56717, 204 |
| Smuggler's Harbor | Docks | `11AB48:Skyrim.esm` | 26702, -35967, 391 |
| Ancient Circle of the Lost Ones | Doomstone | `0D166F:Skyrim.esm` | -114134, -9844, 599 |
| Dragon Aerie | DragonLair | `127B45:Skyrim.esm` | -67057, -45990, 2638 |
| Agnod | DwemerRuin | `0B9E9A:Skyrim.esm` | -121117, 95990, 8279 |
| Old Askamahn | DwemerRuin | `09DDF2:Skyrim.esm` | 62913, -24529, 1813 |
| Old Dothûlgrad | DwemerRuin | `0A9B15:Skyrim.esm` | -42133, 35334, 3766 |
| Old Hatolis | DwemerRuin | `1501B6:Skyrim.esm` | -158243, 53869, 12731 |
| Old Iniath | DwemerRuin | `036C3A:Skyrim.esm` | -94208, 98882, 47276 |
| Old Miskahmur | DwemerRuin | `14FC71:Skyrim.esm` | -128232, 61984, 11390 |
| Old Rashêngrad | DwemerRuin | `1421AD:Skyrim.esm` | -42525, 19426, 4188 |
| Old Sherath | DwemerRuin | `0D5866:Skyrim.esm` | -134375, -15620, 213 |
| Old Soltyris | DwemerRuin | `09DDF0:Skyrim.esm` | 74865, -17402, 2976 |
| Old Uskasarak | DwemerRuin | `10C77E:Skyrim.esm` | 26061, 6858, 15049 |
| Borek's Farm | Farm | `008623:Skyrim.esm` | -15740, 24692, 2218 |
| Bridgehead Farm | Farm | `07E9A9:Skyrim.esm` | -4756, 24796, 1961 |
| Burned off Fishing Lodge | Farm | `04C9AF:Skyrim.esm` | -108884, -27409, 251 |
| Field near the Mill | Farm | `0E4291:Skyrim.esm` | 526, 13324, 2982 |
| Fisher's Pier | Farm | `0CB7AC:Skyrim.esm` | -19652, 19865, 1396 |
| Hafner's Farm Store | Farm | `11B2EF:Skyrim.esm` | -1337, 25889, 2669 |
| Honeybrewery at the Upper Farm | Farm | `0C5D7B:Skyrim.esm` | 7534, 43106, 6390 |
| Landlord Borek's Farm | Farm | `0CB7AE:Skyrim.esm` | 3046, 39544, 6132 |
| Lower Haystacks | Farm | `11B2EE:Skyrim.esm` | -8204, 26788, 2215 |
| Old Farm | Farm | `04CDA2:Skyrim.esm` | -101739, -8690, 232 |
| Old Farm House | Farm | `0D5874:Skyrim.esm` | -118642, -16900, 860 |
| Riverville's Honey Farm | Farm | `0333D4:Skyrim.esm` | -67234, -22241, 4474 |
| Riverville, Marek's Farm | Farm | `11119C:Skyrim.esm` | -88516, -25820, 288 |
| Ruined Homestead | Farm | `141820:Skyrim.esm` | -75332, -12669, 3457 |
| Storm Mill, Warehouse | Farm | `022BD5:Skyrim.esm` | -50733, 96870, 19069 |
| Yero's House | Farm | `0D5873:Skyrim.esm` | -114430, -25473, 907 |
| Ark, Northern Watchtower | Fort | `008624:Skyrim.esm` | -4488, 6032, 3176 |
| Castle Ad'Balor | Fort | `0333D3:Skyrim.esm` | -48573, 26179, 2858 |
| Castle Bleakstar | Fort | `12DAB9:Skyrim.esm` | -73103, 42289, 3578 |
| Castle Dal'Galar | Fort | `0DFFD0:Skyrim.esm` | -72344, 72215, 17295 |
| Cliffwatch | Fort | `008626:Skyrim.esm` | -30330, 18825, 4047 |
| Fort Valstaag | Fort | `0E06BC:Skyrim.esm` | -45364, -43795, 3176 |
| Fortress Fogwatch | Fort | `11C231:Skyrim.esm` | -70966, -5768, 7571 |
| Fortress Rockwatch | Fort | `03D023:Skyrim.esm` | -71128, 101172, 35257 |
| Fortress Wellwatch | Fort | `060F69:Skyrim.esm` | 50304, 4864, 7168 |
| Northcliff Hold | Fort | `022B4B:Skyrim.esm` | -37382, 72625, 9280 |
| Old Borderwatch | Fort | `0211B9:Skyrim.esm` | -47113, 11634, 2555 |
| Old Crosswatch | Fort | `141BE7:Skyrim.esm` | -85390, 13915, 4662 |
| Old Customs Facilities | Fort | `01CF56:Skyrim.esm` | -41730, -8305, 2713 |
| Old Guard Post | Fort | `0F65B1:Skyrim.esm` | 41314, 11276, 7399 |
| Old Silver Fortress | Fort | `08F1F6:Skyrim.esm` | 105832, -24720, 1274 |
| Old Warehouse of the Duneville's Fruit Corporation | Fort | `12DF12:Skyrim.esm` | 42057, -39960, 277 |
| The Sun Fire | Fort | `036C5B:Skyrim.esm` | 57586, 36965, 11916 |
| Watchtower | Fort | `008625:Skyrim.esm` | -23159, 1006, 2331 |
| Grels Stones | Grove | `13CA66:Skyrim.esm` | 5917, 25675, 2429 |
| Moonglow Meadow | Grove | `0904A4:Skyrim.esm` | 101058, -13060, 1639 |
| The Cemetery | Grove | `01D18A:Skyrim.esm` | -26568, -21135, 566 |
| Myrad Tower, Ark, Ark's Western Wall | ImperialTower | `135842:Skyrim.esm` | -15601, -11077, 1123 |
| Myrad Tower, Border of the Heartland | ImperialTower | `0357D7:Skyrim.esm` | -66190, 15264, 3767 |
| Myrad Tower, Dark Valley | ImperialTower | `132EED:Skyrim.esm` | -47574, 52169, 820 |
| Myrad Tower, Duneville | ImperialTower | `057545:Skyrim.esm` | 75345, -51278, 2614 |
| Myrad Tower, Farmers Coast | ImperialTower | `0C5D7C:Skyrim.esm` | 1173, 44165, 5258 |
| Myrad Tower, Fogville | ImperialTower | `08065E:Skyrim.esm` | -113135, 25897, 7164 |
| Myrad Tower, Frostcliff Tavern | ImperialTower | `137A31:Skyrim.esm` | -111280, 52846, 8068 |
| Myrad Tower, Nothern Heartland *(sic)* | ImperialTower | `031CBB:Skyrim.esm` | -36464, 21661, 4922 |
| Myrad Tower, Sun Coast | ImperialTower | `037340:Skyrim.esm` | -80966, -27282, 1769 |
| Myrad Tower, Wellwatch | ImperialTower | `060F6A:Skyrim.esm` | 53556, 10905, 7192 |
| Myrad Tower, Western Cliff | ImperialTower | `1126C5:Skyrim.esm` | -46592, -48256, 3008 |
| Aged Man's Manor | Landmark | `0468DF:Skyrim.esm` | -60728, -73878, 4685 |
| Deep Diggers' Cliff | Landmark | `03657B:Skyrim.esm` | -95908, 75059, 28083 |
| Destroyed Abbey | Landmark | `04251F:Skyrim.esm` | 78282, 21638, 8068 |
| Farmers Throne | Landmark | `073A8B:Skyrim.esm` | 8752, 51294, 5516 |
| Fogstone Bridge | Landmark | `14FC6F:Skyrim.esm` | -118645, 29804, 7535 |
| Frost Crystal Passage | Landmark | `14FC72:Skyrim.esm` | -128587, 67773, 11021 |
| Frostcrystal Lake | Landmark | `14FC70:Skyrim.esm` | -116534, 54383, 9051 |
| Goldenford Cliff | Landmark | `14FC77:Skyrim.esm` | -142475, -26165, 2387 |
| Mana Pond | Landmark | `14FC6C:Skyrim.esm` | -98316, 32705, 2277 |
| Miner Cabin | Landmark | `0217F3:Skyrim.esm` | -47121, -13615, 8091 |
| Moonstone Dunes | Landmark | `09DDEC:Skyrim.esm` | 56254, -31084, 2633 |
| Old Kingwatch | Landmark | `14C2A7:Skyrim.esm` | 16557, -34047, 2220 |
| Ritual Site | Landmark | `141BE8:Skyrim.esm` | -76728, 6634, 3455 |
| Rockcrack | Landmark | `060F60:Skyrim.esm` | 51113, -2600, 4028 |
| Stonepath | Landmark | `022FF2:Skyrim.esm` | -56042, 115992, 23173 |
| Abandoned Lighthouse | Lighthouse | `0CB7B0:Skyrim.esm` | -7426, 48924, 197 |
| Lighthouse of Firerock | Lighthouse | `11F0D8:Skyrim.esm` | 369, 83693, 53 |
| Lighthouse of the Western Cliff | Lighthouse | `14FC74:Skyrim.esm` | -37752, -53067, 4169 |
| Old Lighthouse | Lighthouse | `12DD87:Skyrim.esm` | 65727, -50336, 1481 |
| Old Three River Watch | Lighthouse | `032781:Skyrim.esm` | -127663, 3793, 896 |
| Clearwater Cave | Mine | `141EED:Skyrim.esm` | -65655, -18293, 4961 |
| Deep Diggers' Gouge | Mine | `0365B1:Skyrim.esm` | -97812, 78911, 29188 |
| Fogville Mine | Mine | `110131:Skyrim.esm` | -113081, 20901, 7008 |
| Grimlight Gallery | Mine | `141BE9:Skyrim.esm` | -85430, 22404, 4541 |
| Lightbreach Mine | Mine | `0E3B3C:Skyrim.esm` | -54166, 4776, 2168 |
| Mossy Mud Pit | Mine | `053B63:Skyrim.esm` | -94319, 42519, 1693 |
| Northwind Mine | Mine | `141EE6:Skyrim.esm` | -84705, 70835, 10362 |
| Old Silver Mine | Mine | `08F1FA:Skyrim.esm` | 98165, 1651, 4135 |
| Old Starling Mine | Mine | `09DDF1:Skyrim.esm` | 54556, -27709, 2750 |
| Old Tunnel | Mine | `0D5870:Skyrim.esm` | -98866, -26818, 480 |
| Powder Mines | Mine | `09DDEF:Skyrim.esm` | 66415, -16332, 2609 |
| Quarry at the Wellwatch | Mine | `060F71:Skyrim.esm` | 48422, 16907, 7444 |
| Shadow Echo Mine | Mine | `022FE4:Skyrim.esm` | -30888, 31002, 1621 |
| Shimmering Grove | Mine | `0D166E:Skyrim.esm` | -116821, -11155, 427 |
| Stonehammer Mine | Mine | `0CB7B1:Skyrim.esm` | -8812, 42612, 327 |
| Throatstone, Woodworks | Mine | `129106:Skyrim.esm` | -103654, 36766, 2595 |
| Deserted Ruin | NordicRuins | `0379DD:Skyrim.esm` | -103431, -3106, 289 |
| Grels Grave | NordicRuins | `13CA65:Skyrim.esm` | 12756, 23761, 5232 |
| North Grave | NordicRuins | `0365CE:Skyrim.esm` | -113785, 91796, 28028 |
| Old Darkesh | NordicRuins | `08F1F9:Skyrim.esm` | 111358, -4812, 639 |
| Old Yogosh | NordicRuins | `095A74:Skyrim.esm` | 85232, -14348, 3536 |
| Ruin at the Waterfall | NordicRuins | `08F1F8:Skyrim.esm` | 96350, -6950, 1511 |
| The Living Temple | NordicRuins | `036C39:Skyrim.esm` | -133499, 41027, 13520 |
| Thur | NordicRuins | `0726B1:Skyrim.esm` | -56066, 20984, 5333 |
| Dark Leap Watch | NordicTower | `0365CC:Skyrim.esm` | -115162, 84685, 30634 |
| Dual Towers | NordicTower | `141FEC:Skyrim.esm` | -56627, -7838, 5302 |
| East Wind Tower | NordicTower | `02326A:Skyrim.esm` | -64005, 106351, 27272 |
| Fogwind Watch | NordicTower | `14FC73:Skyrim.esm` | -102731, 54551, 8970 |
| Old Damwatch | NordicTower | `0FE4E9:Skyrim.esm` | -68444, -2374, 3409 |
| Old Northwindwatch | NordicTower | `134742:Skyrim.esm` | -54386, 78792, 15093 |
| Eastern Cannon-Wall | OrcStronghold | `06BE65:Skyrim.esm` | 51349, 1713, 8104 |
| Western Cannon-Wall | OrcStronghold | `06BE64:Skyrim.esm` | 45704, -933, 8587 |
| Ark's Last Watch | Pass | `0F017D:Skyrim.esm` | 24279, 37791, 7542 |
| Icecrack | Pass | `11A8C5:Skyrim.esm` | 18496, -11853, 8994 |
| Abandoned House | Settlement | `130B01:Skyrim.esm` | 56286, -51509, 4446 |
| Cabin at the avalanche-prone Slope | Settlement | `1468E8:Skyrim.esm` | -155313, 80652, 5471 |
| Castle Firerock | Settlement | `1457C6:Skyrim.esm` | 32172, 82371, 240 |
| Dairy | Settlement | `08B034:Skyrim.esm` | -5263, 34366, 5710 |
| Deep Diggers' Settlement | Settlement | `0365B2:Skyrim.esm` | -105169, 81439, 31263 |
| Firerock | Settlement | `1387AB:Skyrim.esm` | 1016, 74970, 946 |
| Fortress Goldenforst | Settlement | `1043D1:Skyrim.esm` | 41473, 35520, 2408 |
| Monastery Westgard | Settlement | `132F41:Skyrim.esm` | -58507, 46567, 868 |
| Northwind | Settlement | `0DE743:Skyrim.esm` | -81777, 76090, 12038 |
| Old Canal | Settlement | `022FE7:Skyrim.esm` | -52010, 41503, 0 |
| Pentas' House | Settlement | `125A7F:Skyrim.esm` | -106056, -31809, 199 |
| Powder Cliff | Settlement | `0211FC:Skyrim.esm` | 100704, -46706, 3750 |
| Silvergrove | Settlement | `08F1F7:Skyrim.esm` | 105022, -10714, 1307 |
| Throatstone Manufactory | Settlement | `129105:Skyrim.esm` | -112759, 32890, 3856 |
| Abandoned Cabin | Shack | `022FE6:Skyrim.esm` | -43858, 42541, 408 |
| Abandoned Farm | Shack | `14FC6D:Skyrim.esm` | -91841, 22946, 4692 |
| Abandoned hunting Cabin | Shack | `14FC6E:Skyrim.esm` | -79811, 23830, 2940 |
| Old Barracks | Shack | `0D586F:Skyrim.esm` | -105017, -29794, 893 |
| Old Cabin | Shack | `022B4C:Skyrim.esm` | -57595, 69000, 9960 |
| Old Dam Lookout | Shack | `0D5854:Skyrim.esm` | -108654, 6346, 3184 |
| Old Estate of the Dal'Varek | Shack | `110654:Skyrim.esm` | 71631, -34337, 1516 |
| Old Three River Camp | Shack | `044676:Skyrim.esm` | -118917, 1049, 470 |
| Ore Terminal | Shack | `0D5875:Skyrim.esm` | -125369, -28240, 349 |
| Ruin of Foamville | Shack | `0848F0:Skyrim.esm` | -30230, -51293, 106 |
| Tavern at the Penny Road | Shack | `14FC76:Skyrim.esm` | -52232, -20460, 6905 |
| The Hollow Hand | Shack | `12DF18:Skyrim.esm` | 65197, -56240, 85 |
| Duneville's Supply Ship | Shipwreck | `1043D0:Skyrim.esm` | 44152, -57308, 68 |
| Galleon Wreck | Shipwreck | `0E09EF:Skyrim.esm` | -33835, -63518, 153 |
| Old Wreck | Shipwreck | `14FC78:Skyrim.esm` | -132476, 13454, 247 |
| Shrine in Goldenford | Shrine | `039E5C:Skyrim.esm` | -146488, -31557, 6307 |
| Frostcliff Tavern | Stable | `1466EF:Skyrim.esm` | -113055, 55094, 8465 |
| Riverville | Town | `11119B:Skyrim.esm` | -83865, -18236, 1584 |
| Grenbeard's Mill | WheatMill | `008620:Skyrim.esm` | -13945, 1535, 1252 |
| The Watermill | WheatMill | `0E4290:Skyrim.esm` | -5955, 8618, 1596 |
| Windmill | WheatMill | `022BD6:Skyrim.esm` | -45852, 97095, 18145 |
| Fogville | WhiterunCapitol | `14FC79:Skyrim.esm` | -128501, 21672, 11229 |
| Castle Goldenford | WindhelmCastle | `03487D:Skyrim.esm` | -141341, -34544, 6334 |
| Old Watermill | WoodMill | `053280:Skyrim.esm` | -87771, 47989, 1723 |
| Sawmill | WoodMill | `022FEA:Skyrim.esm` | -63154, 5476, 3292 |
| The old Noria | WoodMill | `096739:Skyrim.esm` | 99916, -10692, 1539 |
| Throatstone Mill | WoodMill | `14FC7A:Skyrim.esm` | -121841, 31177, 3212 |

### The Ark sub-worldspaces (8)

| Worldspace | Name | Type | FormKey |
|---|---|---|---|
| CapitalCityLowerCity | Entrance to the Undercity | Cave | `127932:Skyrim.esm` |
| CapitalCityLowerCity | Ark, South Quarter | City | `127931:Skyrim.esm` |
| CapitalCityLowerCity | Myrad Tower, Ark | ImperialTower | `135841:Skyrim.esm` |
| CapitalCityCastleWorld | Sun Temple | City | `12792D:Skyrim.esm` |
| CapitalCityCastleWorld | Ark, Military Barrack | RiftenCastle | `071FF6:Skyrim.esm` |
| CapitalCityMarketArea | Ark, Marketplace | City | `12792F:Skyrim.esm` |
| CapitalCityStrangerArea | Ark, Foreign Quarter | City | `12792E:Skyrim.esm` |
| CapitalCityUpperCity | Ark, Nobles Quarter | City | `127930:Skyrim.esm` |
