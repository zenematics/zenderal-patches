# Levelsystem21Cleanup

- **Source:** `src/Levelsystem21Cleanup/` (generated: `tools/00-find-winners.py`, then `tools/01-build-levelsystem-cleanup.py`)
- **Ships:** `Zenderal - 2.1 Levelsystem Cleanup.esp` (ESL, HEDR 1.7), loaded **last**
- **FormID block:** none (overrides only)
- **Status:** built, round-trip clean, 0 unresolved FormKeys; a full load-order scan finds no winning record
  still referencing `010AA2`. DynDOLOD not yet re-run.

## Why

Enderal SE 2.1 deleted quest `Levelsystem 010AA2:Skyrim.esm`, because the level system moved into
`EnderalSE.dll`. On 2026-10-20 DynDOLOD stopped with *"Unresolved FormID [00010AA2] … Castle Bleakstar.esp
04E_ChestLarge01Beute01Gross_FSNQ02Burg"*. A binary scan of the `Ultra` load order (compressed records
decompressed) found **92 records whose winning override still references it**, all copied from 2.0:

| Winning plugin | Records |
|---|---|
| Enderal SE - Gameplay Overhaul | 40 (armour sets, talent-book MGEFs, chests, `_00E_MagicalSymbol`, `Player`, `MyradFlight_ControlQuest`) |
| Pretty Unique Sets | 16 |
| EGO SE - KataPUMB Hidden Powers | 15 |
| EGO SE - Relationship Messages | 6 (`_00E_Levelsystem_s*` MESG) |
| KataHiddenPowers | 6 |
| Zenderal - Chocolate Poise Enderal Fix | 4 (Daedric armour; copied from EGO) |
| Castle Bleakstar, Seaview Lodge SE, Wellwatch Manor SE, Golden Mare Mill SE (`NQ09`), Myths and Legends VI (`NQ29`) | 1 each |

In game those references already resolve to None, so the cleanup changes no behaviour. It only makes the
load order resolvable for xEdit and DynDOLOD.

## The fix

Each winning record is copied verbatim, and only the dead reference is handled. In every case this
mirrors what base 2.1 itself does on the same record or script (checked per record against
`reference/base-2.1.4.4`):

| Reference | Fix | Base 2.1 |
|---|---|---|
| script property `Levelsystem` (`_00E_ArmorSetScript`, `_00E_FS_A3_TalentBookSC`, `_00E_A1_ArcticWindSC`, `_00E_FrozenMEScript`, `_00E_TeleportationMEScript`, `_00E_EPOnMagicalSymbolDis`, `_00E_StanceLoadFailsafeSC`, `_00E_MyradSystem02`, `_00E_NQ09/NQ29_Functions`, `_00E_FS_SleightOfHand_HiddenSlotSC`, `_00E_PlayerSetUpScript`) — 85 | removed | property removed (or the whole script: the hidden-slot script and `_00E_PlayerSetUpScript` no longer exist in 2.1) |
| `xion_playerhouse_document` property `Player` = `010AA2` alias 0 (Seaview, Wellwatch deeds) — 2 | repointed to `CustomNameControlQuest 0493BE` alias 0 | 2.1 made exactly this repoint on its own `_00E_Game_Playerhouse_*` deeds |
| MESG `Quest: 010AA2` — 6 | removed | 2.1's `_00E_Levelsystem_s*` messages have no Quest |

**One 2.1 property added (2026-11-06, `MISSING_21_PROPERTIES` in tools/01):** this plugin owns
`MyradFlight_ControlQuest 0D9B17`, so it is the only place a property 2.1's script needs can be filled. EGO's 2.0
record gives `_00E_MyradSystem02` an int `Price` = 50, which 2.1's script no longer reads; 2.1's `PortPlayer` removes
`MyradTripPrice` (global `0493E1` = 25) gold, and EGO's record left that property unfilled. tools/01 now inserts
`MyradTripPrice` → `0493E1` after `MQ04` (asserted: exactly one added). Half of the Myrad 25-penny fix; the
dialogue gates are [`MyradFlightPrice`](MyradFlightPrice.md). Unverified in game.

Known leftover: records with scripts 2.1 deleted (the hidden-slot chests, EGO's `Player` with
`_00E_PlayerSetUpScript`) still carry those scripts. That only logs Papyrus warnings; forwarding 2.1's
script set onto EGO's records is a separate, larger job.

Masters: Skyrim, Update, FS and all 11 winning plugins, in load order. Because every record is a verbatim
copy of a winner, **re-run tools/00 + 01 whenever any of those plugins changes**. tools/00 ignores this
plugin, and tools/01 refuses records where nothing was removed (a stale `winners.json`).

## Regenerating

1. `python src/Levelsystem21Cleanup/tools/00-find-winners.py <scratch>/winners.json`
2. Serialize each plugin it lists with Spriggit 0.40.0 into `<scratch>/<name, alphanumerics only>/`.
3. `python src/Levelsystem21Cleanup/tools/01-build-levelsystem-cleanup.py <scratch> <scratch>/winners.json`
4. Update `RecordData.yaml`'s masters if the set of winners changed, then deserialize.

## Pretty 2.1 regeneration (2026-11-11)

**Load order:** this plugin had drifted to load **before** `Zenderal - Pretty Armory EGO Patch.esp` (line 415 vs
438 in Ultra). The EGO patch mastered it and copied 7 of its records. It now loads just before
`Zenderal - Unresolved References Cleanup.esp` in the three Ultra profiles, after every other generated patch.

**Rerun after Pretty Enderal Armory 2.1:** 78 records, against 92 before.
- Out: 18 Pretty Unique Sets armor-set records. Pretty 2.1 dropped the `Levelsystem` property itself, so their
  winners are clean.
- In: Marksman Rename's two Marksman learning-book effects (`085646`/`085647`).
- Masters: base 3 + the 11 current winners in load order. Pretty Unique Sets is out, Marksman Rename is in.

Deployed to Patch Collection. The previous copy is in `E:/Zenderal-backups/2026-11-11-pretty-2.0/`.

**Folder names in step 2** keep the `esp`: `re.sub('[^A-Za-z0-9]', '', 'Castle Bleakstar.esp')` →
`CastleBleakstaresp`.
