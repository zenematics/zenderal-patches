# EGO21Compat

- **Source:** `src/EGO21Compat/` (generated — run `tools/01-build-race-overrides.py` and
  `tools/00-scan-arma-races.py` → `tools/02-build-armor-addons.py`; never hand-edit `Races/` or `ArmorAddons/`)
- **Ships:** `Zenderal - EGO 2.1 Compatibility.esp` (ESL)
- **FormID block:** none (overrides only)
- **Status:** races done 2026-10-20, built and deployed; **unverified in game**. 4 armor addons done
  2026-10-22, built, not deployed, unverified in game. NPC / FormList remaps not started (see "Still to do").

## Why it exists

Enderal 2.1 moved its playable **Half Arazealean** and **Half Qyranian** off the FormIDs 2.0 used
onto the vanilla ones (changelog line 139):

| 2.0 playable | 2.1 playable | 2.1 fate of the old record |
|---|---|---|
| `NordRace 033899:Skyrim.esm` | `NordRace 013746:Skyrim.esm` | `NordRaceOBSOLETE`, Playable flag removed |
| `RedguardRace 033898:Skyrim.esm` | `RedguardRace 013748:Skyrim.esm` | `RedguardRaceOBSOLETE`, Playable flag removed |

**[verified]** against `reference/base-2.1.4.4/{Skyrim,EnderalFS}/Races/`: in 2.1 each old/new pair is
identical except for FormKey, EditorID, the Playable flag and the order of the translated strings.
2.0's `033899` is the same record as 2.1's `033899` except for the EditorID and the Playable flag.

EGO 1.93.1 was written for 2.0, so all three of its race plugins still override the old FormIDs with
Playable set (binary scan of the Ultra load order, 2026-10-20):

- `Enderal SE - Gameplay Overhaul.esp` (load position 56)
- `EGO SE - Increased Carry Weight.esp` (122)
- `EGO SE - DS Movement Stamina UNIQUE RACES.esp` (291) — wins

No list plugin overrides `013746`/`013748` except FS. Character creation therefore showed each race
twice: 2.1's with vanilla Enderal stats, and EGO's obsolete copy.

## What it does

For each race it writes two copies of the **winning** EGO record (DS Movement Stamina UNIQUE RACES;
it is what 2.0 players actually played, ICW's and EGO's values are already folded into or overridden
by it):

- onto the **2.1 playable** FormID — verbatim, with 2.1's EditorID. The race chargen offers now has EGO's stats.
- onto the **obsolete** FormID — verbatim minus `Playable`, with 2.1's `*OBSOLETE` EditorID. Chargen
  lists it once, and any NPC EGO still assigns to the old race keeps EGO's stats.

Masters: `Skyrim.esm`, `Update.esm`, `Enderal - Forgotten Stories.esm` (two head-part preset NPCs
`03029B`… live there), `EGO SE - DS Movement Stamina UNIQUE RACES.esp` (mastered only to force load
order — no record of it is referenced).

The source `reference/mods/EGODSRaces` matched a fresh serialization of the installed plugin
(2026-10-20). Re-serialize and re-run the generator whenever DS Unique Races or EGO updates — and
retire this patch once EGO ships 2.1-aware races.

## Armor addons (2026-10-22)

Reported: Boots of the Righteous Path invisible on the player. EGO's 2.0-era override of their addon
`03E_24_BootsOfTheRighteousPathAA 145879` is 2.1's record minus `013746`/`013748` in
`AdditionalRaces` (it keeps the old `033899`/`033898`), so on a 2.1 Half Arazealean / Half Qyranian
the boots equip and render nothing.

`tools/00-scan-arma-races.py` (read only) compares every winning ARMA in the Ultra load order with
the Skyrim.esm / FS record it overrides. **4 of 919** winners lose a 2.1 playable race, all EGO:

| Addon | Armor |
|---|---|
| `03E_24_BootsOfTheRighteousPathAA 145879` | Boots of the Righteous Path (+ Forged) |
| `01E_07_SteelShieldAA 14587A` | Steel Shield |
| `02E_18_PyreanShieldAA 0E35C7` | Pyrean Shield |
| `_50E_LSet_VenturerArmorAA 14483D` | Venturer armor |

`tools/02-build-armor-addons.py` writes EGO's record verbatim with the two races inserted in FormID
order, as 2.1 has them. **[verified]** on the built plugin: each record equals EGO's installed one
subrecord for subrecord plus two `MODL`. 13 further EGO addons (Skaragg/Starling/Bonejudge/Wanderer/
Thalmor/Redguard/Yarl/barkeeper/blacksmith shoes, Venturer gloves) also lack the races in EGO, but
`Audio Overhaul - Enderal patch.esp` or a Pretty plugin wins them with both races present — they are
fine and deliberately not overridden. Re-run 00 → 02 after EGO or any armor mod changes.
Unverified in game.

## Still to do (the rest of EGO vs 2.1)

`reference/mods/EGO` still points at the old races in **75 NPCs, 18 ArmorAddons and 1 FormList**
(ArmorAddons done 2026-10-22, above — only 4 actually won).
Those overrides revert 2.1's own remap of the same records. With this patch the stats are equal, so
the visible risk is mostly in conditions and scripts that test `GetIsRace 013746`/`013748` (2.1)
against an NPC EGO left on `033899`/`033898`, and armor addons that list only the old race. Each needs
the EGO record forwarded with the race swapped. Do this after a chargen check in game.

**Chargen verified in game 2026-10-20:** each race is listed once.

**Paused 2026-10-20 — where the remap stands.** A binary scan of the whole Ultra load order (scratchpad
`racescan.py`, output `racescan.json`) found **849 winning records** that still contain `033899`/`033898`:
726 ARMA, 84 NPC_, 24 INFO, 12 FLST, 2 MGEF, 1 SPEL. Winners include `Skyrim.esm` (296) and FS (39)
themselves, so 2.1 still references the old races in many places. For ARMAs that is normal, since an
addon may list both races. **Next:** filter to the records that reference the old race **but not** the
2.1 one (ARMAs missing `013746`/`013748`, NPCs whose `Race` is old, conditions with `GetIsRace` on old
only). Only those break. Then forward each winner with the new race added or swapped.

## Related

- [`Fuse00ArmorRaces`](Fuse00ArmorRaces.md) added `033899`/`033898` to Fuse00's addons for 2.0.
  On 2.1 the addons' own `013746`/`013748` already match the playable races, so that patch is redundant
  (harmless) on 2.1.
- Migration log: [`../workspace/enderal-update-migration.md`](../workspace/enderal-update-migration.md).

## Werewolf script (2026-10-20)

`_00E_Theriantrophist_PlayerAsWerewolf` (2.1 expects version 2): EGO's 2.0-era copy wins over 2.1's and
has no `_GetScriptVersion`, so EnderalSE.dll popped *"overwritten by a mod"*. 2.1 also rewrote the
script (`Transform(aTransformEffect, duration)` signature, timer-based transform back, non-SKSE
fallbacks), so EGO's copy also runs 2.0 logic against 2.1 callers.

`Scripts/source/` = a three-way merge: base 2.0.12 source, ours 2.1, theirs EGO's shipped `.psc`. Two
conflicts in the stat block were resolved to EGO (its rebalance makes claw damage independent of weapon
strength). One merged line was reverted: EGO's source predates 2.0.12, so its `Game.UnlockAchievement`
is an old base, not a design choice — 2.1's `Steam.UnlockAchievement` is kept. The result differs from
2.1 only in EGO's edits (AlchemyPercentageDmg 0.25, StaminaPercentage 0.06, BalancingDamageMalusPercent
5, restore stamina/magicka on transform, 115/90 attribute thresholds, claw damage formula, damage resist
not stacking the pre-transform value). *Enderal SE - Bug Fixes*' copy (its stamina fix is a subset of
EGO's) is superseded. Compiled clean; deployed to this mod's `Scripts/`, which sorts above EGO.
Unverified in game.
