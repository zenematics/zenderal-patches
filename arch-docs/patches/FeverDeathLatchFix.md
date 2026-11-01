# FeverDeathLatchFix

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/FeverDeathLatchFix/`
- **Ships:** *(no plugin — one recompiled script)*
- **FormID block:** _(none)_

## What it does

**Players stuck unable to level** (report 2026-10-10: 11010/5954 XP at level 5). The player's actor script `_00E_EPUpdateFunctions` runs level-ups from its 3.5 s `OnUpdate` loop, gated on `!IsInCombat()`, no Dialogue Menu, `Game.IsActivateControlsEnabled()`, `!Player.IsDead()` **and private `isdead == False`**. At Arcane Fever ≥ 100 it sets `isdead = True` and calls `Player.Kill()`, and **nothing ever resets it** — if the kill doesn't take (tgm, essential, a scene) the flag is saved and blocks every level-up and the fever 40/70 effects forever. The reported case: the player sat in `tgm` while spamming potions — **every Mana and Morning Air (restore-stamina) potion carries `_00E_AlchIncreaseArcaneFever 02F21D:FS`, +2/3/4/5/6 % fever by tier** (health potions carry none), so a potion spree can reach 100 unnoticed, and `tgm` makes `Kill()` a no-op. Diagnose in game: `prid player` → `sv` shows `iLevelUpsNeeded = N` beside `IsDead = True`. No console mod in the list can set a script variable, so the fix is a fork: one `; ZP` guard in `OnUpdate` clears `isdead` when the player is alive and fever < 100. **Forked from SureAI's source** (`ScriptsEnderal.zip`) since 2026-10-14. Until then it forked Leveling Redone's loose copy (LR's 4/3 points per level, `Game.` instead of `Steam.UnlockAchievement`, plain `Show()` fever messages, 0.03 s menu wait) and had to sort below it; LR left the list, so base Enderal's `E - Misc.bsa` copy is the winner again. Verified 2026-10-14: no other mod ships the script loose or in a BSA (AmnesiaShrine and KataPUMB Affinities BSAs only *reference* it), and the extracted base `.pex` matches SureAI's source (`steam`, help-message calls, 0.1 s wait). String table identical to base Enderal's `.pex` (261 strings). Compiled against `papyrus-source/vanilla-stubs/` in place of the vanilla tree, which is empty on this machine (`tools.json`'s `papyrusSource.vanilla` points into a Nemesis folder that no longer exists). Compiling needed new `Message`/`MusicType` stubs in `papyrus-source/vanilla-stubs/` (real vanilla native signatures); `tools.json`'s `papyrusCompiler` (and `papyrusSource.vanilla`) pointed into a Nemesis folder that no longer exists; the compiler key now points at `<modlistRoot>/mods/Creation Kit/Root/Papyrus Compiler/PapyrusCompiler.exe`. **Credit SureAI.** Built and deployed 2026-10-10, not yet verified in game

## Enderal 2.1 rebase (2026-10-20)

Enderal 2.1's `EnderalSE.dll` checks a static `_GetScriptVersion()` on 76 of SureAI's scripts at the
first load and pops *"Script ... is overwritten by a mod ... installed version: N/A"* when the winning
copy lacks it. Our 2.0-based copy tripped it for `_00E_EPUpdateFunctions` (expects 2).

The source is now **2.1's `_00e_epupdatefunctions.psc` plus our six-line `; ZP` block**, inserted at the
same spot (right after `Int iArcaneFever = ...`). 2.1 itself only added `Debug.SetGodMode(false)` before
`Player.Kill()` — that removes one way the kill fails, not the latch, so the fix stays. 2.1 also moved
`ComputeNeededExp` out to `_00E_Func_ComputeNeededExp` and swapped help messages to `_00E_HelpMessage`;
all of that is 2.1's code, untouched. Compiled clean against `papyrus-source/enderal-2.1.4.4`;
deployed to *Zenderal - Patch Collection* and *Zenderal - Fever Death Latch Fix*. Unverified in game.
