# HalfStarlingDS

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/HalfStarlingDS/`
- **Ships:** `Zenderal - Half Starling DS Races.esp`
- **FormID block:** none (overrides only)

## What it does

"Playable Half Starling Race" does NOT add a race — it makes `WoodElfRace 013749:Skyrim.esm` (Enderal's NPC Starling race, shared by EVERY NPC Starling) playable; its `EGO SE - Half Starling.esp` loads after `EGO SE - DS Movement Stamina UNIQUE RACES.esp` (320 vs 296) and so reverts that mod's per-race stats to EGO's flat 50/50/90 + regen 0.1/6.3/3. Override = the EGO-Half-Starling record verbatim with a "might and magic" profile sized against the DS mod's four playable races (Half-Arazealean `NordRace` 125/30/180 r0.35/3/10, Half-Qyranian `RedguardRace` 60/75/40 r0.2/7.5/50, Half-Kilénian `BretonRace` 50/50/90 r0.125/6.3/30, Half-Aeterna `HighElfRace` 30/125/70 r0.1/9/20): **75/75/60, regen 0.3/8/20**. NPC Starlings get it too (shared record). The mod's `_00E_FS_Ab_RacialAb_Qyranian` override is benign — EGO's effects verbatim plus a `GetPCIsRace RedguardRace` guard. Masters: Skyrim + `Enderal SE - Half Starling.esp` + `EGO SE - Half Starling.esp` (content-unused, forces load-after). Built and deployed 2026-10-05, not yet verified in game.

## 2.1: the Qyranian cultural bonus was dead (fixed 2026-10-27)

The `GetPCIsRace RedguardRace` guard above was benign on Enderal 2.0 only. It names `033898:Skyrim.esm`, 2.0's
playable Qyranian. Enderal 2.1 moved the playable Qyranian to `RedguardRace 013748` (FS override; see
[`EGO21Compat.md`](EGO21Compat.md)), so on 2.1 all five effects of `_00E_FS_Ab_RacialAb_Qyranian 01EC66:FS` failed their
condition: Half Qyranians had no Mentalism/Enchanting/Alchemy +2 or Stamina +7 (player report, skill menu at 5). The
ability itself is still added (`_00E_MQP02_Functions.AddRacialAbilites`, `_00E_MQ101_QuickStart`, Skip The Prologue);
the guard exists because Starlings fall into that script's `Else` branch and are given the Qyranian ability too.

This patch now carries `EGO SE - Half Starling.esp`'s record verbatim (EGO's effects: Alteration/Enchanting/Alchemy
+2, Stamina +7, display effect `02F0D9`) with the guard's race `033898` → `013748` (5 conditions, asserted by count).
Masters gained `Update.esm` + `Enderal - Forgotten Stories.esm` (Spriggit failed with an empty `Error:` without FS).
Round-trip identical. Deployed into `Zenderal - Patch Collection` (the only copy loaded; previous one in
`E:/Zenderal-backups/2026-10-27-qyranian-racial-fix/`). The other three racial abilities have no Half Starling guard.
Unverified in game: an existing save should pick the bonus up at once (`player.hasspell <07>01EC66` = 1).
