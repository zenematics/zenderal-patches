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
