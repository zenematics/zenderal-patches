# ArkGateSiegeFix

- **Source:** `src/ArkGateSiegeFix/` (generated: `tools/01-build-ark-gate-siege-fix.py`)
- **Ships:** `Zenderal - Ark Gate Siege Fix.esp` + 2 scripts — **Enderal 2.0 / old Zenderal release only**
- **FormID block:** `0x800–0x801` (perk, quest) + one override

## What it does

**On Enderal 2.0, the Castle Quarters gate the Black Light siege sends you through opens again.**
Reported on Discord 2026-10-21 by a player on the old (2.0) Zenderal release: after activating the beacon in
the Sun Temple (`MQ12b`, "Black Light" part 2), every way out of the Castle Quarters says it needs a key,
including the one the quest wants, so the only way on was the console. Their `prid` of the door:
`City Gate`, base `11B116`, ref `09EECD`, *Ref last changed by: ArkCityGateConsistencyPatch.esp*, one script.

### The mechanism on 2.0 [verified 2026-10-22 against `reference/base/` = 2.0.12.4]

- Forgotten Stories 2.0 puts `_00E_ChestAndDoorLockScript` on the door bases, both the original
  `SHouseDoor03 05D7EA` and the city gate `_00E_CapitalCity_CityGate01AdjustedSize 11B116`.
  Its `OnActivate` shows `_00E_sDoorLocked` ("requires a key") and does nothing else while
  `MQ12b` is at stage 5–125, unless the door is in a `_00E_SuntempleLocations 03BB5B` location.
  The door is not actually locked, so no lock icon appears.
- SureAI keeps the story path open by placing gate `09EECD` (and its other side `096F6A`) with
  that script flagged **`InheritedAndRemoved`**, which strips it from those two refs only.
- **Ark City Gate Consistency Patch** (Enderal SE Nexus 839, f1.01) overrides both refs to use the gate
  model `11B116`. Its records match **Enderal 2.1's**, which have no `_00E_ChestAndDoorLockScript`
  entry. On 2.0 the base's script comes back, and the gate is locked for the whole siege.
- `096F6A` is fine on the old release: Perpetuum Theater - Neo Enderal loads after the gate patch
  (`Alpha 0.6` plugins.txt line 356 vs 157) and carries 2.0's record verbatim, exemption included.
  It also reverts the gate patch's model swap on that side. No other plugin in the old or current
  load order overrides `09EECD`.
- Of the 48 refs the gate patch overrides, only `09EECD` and `096F6A` differ between 2.0 and 2.1,
  and only in their scripts.

### The fix

`tools/01-build-ark-gate-siege-fix.py` copies the gate patch's `09EECD` record verbatim and inserts
2.0's `VirtualMachineAdapter` (just the `InheritedAndRemoved` entry). The worldspace `070729` and
persistent-cell `07072C` headers are forwarded verbatim from the gate patch. The plugin masters
`ArkCityGateConsistencyPatch.esp` and must load **directly after it**, so the forwarded headers match
the running winner at that point. The script asserts the gate patch still has no scripts on `09EECD`
and that 2.0's block is exactly the one expected.

**1.0 failed on the reporter's save (2026-10-22, "it no worky").** The record change only helps a new
game. The gate is persistent, so every save already holds its `_00E_ChestAndDoorLockScript`
instance, and a plugin can't take a script back off an object in an existing save. The Creation Kit
wiki's [Save File Notes (Papyrus)](https://ck.uesp.net/wiki/Save_File_Notes_(Papyrus)) says a script
removed from an object "will still exist on the object when the save is loaded". The script's
`OnLoad` has also called `BlockActivation(True)` on the ref, and that state is saved too.

**1.1 adds a save-safe route** (scripts in `Scripts/source/`, compiled `.pex` committed):

- **`ZEN_ArkGateSiegeOpenPerk` `0x800`** (hidden): copies the shape of SureAI's 2.1 siege perk
  `0493DB`. It's an `Activate` entry point with *Add Activate Choice*, flags `RunImmediately` and
  `ReplaceDefault`, and conditions player (tab 0) plus target `GetIsReference 09EECD`, `MQ12b` stage
  ≥ 5 and ≤ 125 (tab 1). Fragment `PRKF_ZEN_ArkGateSiegeOpenPerk_00000800` calls
  `akTargetRef.Activate(akActor, True)`. Default processing only skips the baked script's
  `OnActivate` and opens a door whose activation is blocked. That's the same call the lock script
  uses for the doors it lets through.
- **`ZEN_ArkGateSiegeQuest` `0x801`**: start-game enabled and run once. Its `OnInit` adds the perk.
  A start-game-enabled quest new to a save starts on that save's first load.

Outside the siege stages the perk does nothing, and the gate's own script works as before. Compiled
against the 2.1 Enderal tree plus `papyrus-source/vanilla-stubs`. The 2.0 tree has no `Actor.psc`,
and `tools.json`'s `papyrusSource.vanilla` points into the removed Nemesis folder. Only base Papyrus
calls are used, and their signatures are the same in 2.0. The SKSE source folder was left off the
imports: its partial `Quest.psc` needs `GlobalVariable`, which neither tree has.

Round trip (deserialize → serialize) is identical apart from `-0` vs `0` in two rotations. Shipped as
`build/dist/Zenderal - Ark Gate Siege Fix (Enderal 2.0).zip` (`.esp` + `Scripts\*.pex`).
**Unverified in game.** Test on the old release with a save from during the siege: leave the Sun
Temple and use the Castle Quarters gate. Console workaround without the fix: `player.moveto 96F6A`.

## Why 2.1 doesn't need it

Enderal 2.1 removed `_00E_ChestAndDoorLockScript` entirely: no record in `reference/base-2.1.4.4/`
references it, and the 2.1 script source has no such file. The siege lock is now the hidden perk
`_00E_ArkSiegeLockedGatesPerk 0493DB`, whose fragment shows the same message on any door while the
player is outdoors in Ark outside the Sun Temple locations. Seven gates are exempt **by reference ID**,
`09EECD` and `096F6A` among them. The gate patch's base swap can't affect that check, so **do not
ship this plugin with the 2.1 list.** Retire it with the 2.0 release.
