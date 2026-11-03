# BlackLightWakeUpFix

**Ships:** recompiled `Scripts/_00E_MQ12c_Functions.pex` (+ source), script-only. The live copy is
in `Zenderal - Patch Collection`. **Status:** built and deployed 2026-11-03; compiles, same 66
properties as base Enderal's `.pex`. **Unverified in game.**

## The report

cptflame (2026-11-03): *Black Light, Part III* — after the dream sequence the screen stays black,
the player cannot move, Jespar/Calia never wake you, NPCs can be heard talking. `player.setscale 1`
(a community "fix") did nothing.

## How the wake-up works (base Enderal 2.1.4.4)

- Dream scene `MQ12c_SC03_Dream 134595` ends → stage 35 → `EndSC03()` restores the player's scale,
  applies `FadeToBlackHoldImod 0F756E` and sets stage 40.
- Stage 40 → `StartSC04()`: moves the player to `MQ12c_SC04_CompanionRunREF`, places the companion
  (Calia or Jespar, by sympathy), starts `MQ12c_SC04_WakeUp 1345A9`.
- Scene start (fragment 3): player AI-driven, HUD cart mode, all controls disabled.
- Phase 0: player package `MQ12c_SC02_PlayerGoToSleep 134596` (SitTarget on `MQ12c_SC2_Bed 0A6F3A`,
  base `NobleBedChildSingle01L 0FEDC3`). Completion: player `IsInFurnitureState Lay`.
  **Its OnCompletion fragment is `FadeBack()`** — the only thing that lifts the black screen and
  ends AI control. Phase 1 onwards: the companion walks in and talks.

So a player who never lies down stays blind and frozen with no way out.

## What the list does to it

Nothing (Ultra profile scan, `src/PerkOverhaul/tools/00-scan-overriders.py`): the quest `133D77`,
both scenes, the six SC04 packages, the bed ref and its base are only defined by `Skyrim.esm`; the
quarters cell `0A5F1D` is edited by FS and Myths and Legends VI (one ref ~1300 units from the bed).
No mod replaces `NobleBedSingle01.nif` or ships any script in the chain loose (Waiting Unlocked's
`_00e_bedscript.pex` is `InheritedAndRemoved` on this bed). Treated as the vanilla bug; the SureAI
forum has similar unanswered reports. Why the player does not reach the bed is **not known**.

## The fix

`StartSC04()` arms a watchdog (`iWakeUpWatchdog`, `bFadedBack`, new non-property variables;
`OnUpdate` dispatches to `WakeUpWatchdog()` before SureAI's dream-timescale branch):

1. +15 s: if `FadeBack()` has not run, the scene still plays and `PlayerREF.GetSitState() == 0`,
   `MQ12c_SC2_Bed.Activate(PlayerREF)`. The bed's `_00E_MQ12c_SC2_BedSC` at stage 40 lies the player
   down via its `SetInChargen` + default-activation path (no sleep menu) — SureAI's own route.
2. +15 s more: if still no `FadeBack()`, call it, `EnablePlayerControls`, cart mode off, and
   `BlockActivation(False)` on the bed so the player can lie down and complete phase 0 themselves.
   `FadeBack()` skips the fade IMOD when the watchdog already applied it.

A save already stuck ran the old `StartSC04()`; it needs the console recovery:
`player.moveto 0A6F3A`, `prid 0A6F3A`, `activate player`; if still black `rimod 0F756E` +
`rimod 0EAD71`; last resort `setstage MQ12c 50` + `epc` (skips the companion conversation).
