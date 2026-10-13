# FeverDeathLatchFix

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/FeverDeathLatchFix/`
- **Ships:** *(no plugin — one recompiled script)*
- **FormID block:** _(none)_

## What it does

**Players stuck unable to level** (report 2026-10-10: 11010/5954 XP at level 5). The player's actor script `_00E_EPUpdateFunctions` runs level-ups from its 3.5 s `OnUpdate` loop, gated on `!IsInCombat()`, no Dialogue Menu, `Game.IsActivateControlsEnabled()`, `!Player.IsDead()` **and private `isdead == False`**. At Arcane Fever ≥ 100 it sets `isdead = True` and calls `Player.Kill()`, and **nothing ever resets it** — if the kill doesn't take (tgm, essential, a scene) the flag is saved and blocks every level-up and the fever 40/70 effects forever. The reported case: the player sat in `tgm` while spamming potions — **every Mana and Morning Air (restore-stamina) potion carries `_00E_AlchIncreaseArcaneFever 02F21D:FS`, +2/3/4/5/6 % fever by tier** (health potions carry none), so a potion spree can reach 100 unnoticed, and `tgm` makes `Kill()` a no-op. Diagnose in game: `prid player` → `sv` shows `iLevelUpsNeeded = N` beside `IsDead = True`. No console mod in the list can set a script variable, so the fix is a fork: one `; ZP` guard in `OnUpdate` clears `isdead` when the player is alive and fever < 100. **Forked from Leveling Redone's copy**, not SureAI's — `Leveling Redone (No Skillbooks)` ships the script loose with its 4/3 points per level, so this mod **must sort below it in MO2's left pane**. String table identical to LR's `.pex` (260 strings). Compiling needed new `Message`/`MusicType` stubs in `papyrus-source/vanilla-stubs/` (real vanilla native signatures); `tools.json`'s `papyrusCompiler` (and `papyrusSource.vanilla`) pointed into a Nemesis folder that no longer exists; the compiler key now points at `<modlistRoot>/mods/Creation Kit/Root/Papyrus Compiler/PapyrusCompiler.exe`. **Credit SureAI and Ixion XVII**; LR's redistribution permissions not yet checked. Built and deployed 2026-10-10, not yet verified in game
