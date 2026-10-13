# GuardFalconer

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/GuardFalconer/`
- **Ships:** `Zenderal - Guard Falconer Patch.esp`
- **FormID block:** none (overrides only)

## What it does

City guards only half-wore Falconer armor. `GuardArmorReplacerFalconer.esp` (Enderal Nexus 556, load 73) adds NO armor — it repoints four ARMAs at `1Falconer\*` meshes: `ImperialBootsAA 0136D3` (guard boots `05BB88`), `StormcloakHelmSolitudeAA 0EB255` (guard helmet `0C7F5C`), `StormcloakCuirassSolitudeAA 0EB250` (guard cuirass `0C7F5B`), `StormCloakGlovesAA 0A6D7C`. `Pretty Factions Armory.esp` (268) reverts `0EB250` to Enderal's `ArkGuardHaubergeon` and swaps outfit `_15E_CityGuardRegularOutfitHelmetNoShield 046ECE`'s helmet for its own `_00E_LightCityGuardHelmetVariant 000827`. Override: `0EB250` = the replacer's record verbatim (Pretty's differs only in Falconer-specific fields — model paths, `Amulet` flag, `Unknown2`, `WeaponAdjust`; alternate-texture `Data` blobs identical) and `046ECE` = Pretty's with `000827` → `0C7F5C`. `0A6D7C` (Pretty Common Armory, 202, reverts it) is deliberately NOT forwarded: no guard outfit carries gauntlets, and that addon is Heavy Leather Gauntlets `0030B9` / Stormcloak gauntlets for everyone. Winner chain from a master-aware scan of every Alpha 0.5 plugin. Masters: Skyrim + `Pretty Factions Armory.esp` (forces load-after). Built and deployed 2026-10-11, not yet verified in game.
