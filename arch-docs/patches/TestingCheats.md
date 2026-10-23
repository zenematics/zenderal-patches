# TestingCheats

- **Source:** `src/TestingCheats/` (hand-written records + two scripts)
- **Ships:** `Zenderal - Testing Cheats.esp` (ESL, HEDR 1.7; masters Skyrim, Update, FS) + `ZEN_TC_MenuEffect.pex`, `ZEN_TC_Init.pex`
- **Requires:** B612 (its QuantitySlider). Prophecy is optional.
- **FormID block:** `0x800–0x804`: `800` power `ZEN_TC_Power`, `801` effect `ZEN_TC_PowerEffect`, `802` menu message, `803` StartGameEnabled+RunOnce quest `ZEN_TC_Init` (gives the power), `804` confirm message
- **Status:** built 2026-10-22; Spriggit round trip identical, all 10 FormKeys resolve. **A testing tool, not part of the list.** Unverified in game.

The curator's test helper: the lesser power **Testing Cheats** opens a message box: *Gain levels* · *Add
experience* · *Add Prophecy points* · *Cancel*. Each option is a B612 QuantitySlider followed by an
"Apply N?" confirmation.

## How a level-up is made real **[verified from Enderal's source, 2.1.4.4]**

Enderal's levelling is `_00E_EPUpdateFunctions`, a script on the Player actor (the list runs
[`FeverDeathLatchFix`](FeverDeathLatchFix.md)'s fork of it, with the same `bool receiveEP(int)`):

- Experience is the global `PlayerExp 012596`. **Setting it alone does nothing**: `OnUpdate` only calls
  `levelUp()` while `iLevelUpsNeeded > 0`, and only `receiveEP` (any EP gain) recomputes that.
- `levelUp()` is the real thing: `PlayerLevel` +1, `Game.SetPlayerLevel`, 1 talent point (`TalentPoints`, mirrored
  in `dragonsouls`), 5 learning points (`Lernpunkte`), 4 crafting points (`Handwerkspunkte`), and the
  Health/Magicka/Stamina choice box. It runs once per level, out of combat, with activate controls enabled and no
  dialogue open.
- Total EP for level *L*+1 = `_00E_Func_ComputeNeededExp.Run(L, EXPMultSlope, EXPMult)`: `L^1.655 × EXPMult`, with
  progressive multipliers above 20/30/40 (×1.2/×1.5/×2). EGO sets `EXPMult` to **450** (base Enderal's differs).
  With EGO, level 50 needs 413,090 EP total and level 51 needs 432,277.

So the effect calls `(Game.GetPlayer() as _00E_EPUpdateFunctions).receiveEP(amount)`. *Gain levels* asks
`ComputeNeededExp` for the target level with the live globals and adds exactly the shortfall + 1.

**Console fallback (no mod):** `set PlayerExp to 413100`, then earn any EP (mix one potion, pick one lock):
`receiveEP` runs and every level from there to 50 is handed out.

## Prophecy points

`GetFormFromFile(0x802, "Zenderal - Prophecy.esp")` = `ZP_ProphecyPoints`, `.Mod(n)`. The Prophecy menu's own
`AwardPoints` pays `level / LevelsPerPoint − ZP_ProphecyPointsEarned` on open, and never takes points away, so
granted points survive. Console: `set ZP_ProphecyPoints to 25`.

## Notes

- B612's `QuantitySlider.Show` returns a remembered value that is only updated on Confirm, so a Cancel could
  return the last pick. The confirm box makes that harmless.
