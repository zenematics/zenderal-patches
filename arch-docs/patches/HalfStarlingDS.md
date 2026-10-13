# HalfStarlingDS

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/HalfStarlingDS/`
- **Ships:** `Zenderal - Half Starling DS Races.esp`
- **FormID block:** none (overrides only)

## What it does

"Playable Half Starling Race" does NOT add a race — it makes `WoodElfRace 013749:Skyrim.esm` (Enderal's NPC Starling race, shared by EVERY NPC Starling) playable; its `EGO SE - Half Starling.esp` loads after `EGO SE - DS Movement Stamina UNIQUE RACES.esp` (320 vs 296) and so reverts that mod's per-race stats to EGO's flat 50/50/90 + regen 0.1/6.3/3. Override = the EGO-Half-Starling record verbatim with a "might and magic" profile sized against the DS mod's four playable races (Half-Arazealean `NordRace` 125/30/180 r0.35/3/10, Half-Qyranian `RedguardRace` 60/75/40 r0.2/7.5/50, Half-Kilénian `BretonRace` 50/50/90 r0.125/6.3/30, Half-Aeterna `HighElfRace` 30/125/70 r0.1/9/20): **75/75/60, regen 0.3/8/20**. NPC Starlings get it too (shared record). The mod's `_00E_FS_Ab_RacialAb_Qyranian` override is benign — EGO's effects verbatim plus a `GetPCIsRace RedguardRace` guard. Masters: Skyrim + `Enderal SE - Half Starling.esp` + `EGO SE - Half Starling.esp` (content-unused, forces load-after). Built and deployed 2026-10-05, not yet verified in game.
