# Fuse00ArmorRaces

- **Source:** `src/Fuse00ArmorRaces/` (generated — run `tools/01-build-race-overrides.py`, never hand-edit `ArmorAddons/`)
- **Ships:** `Zenderal - Fuse00 Armor Races.esp`
- **FormID block:** none (overrides only)

## What it does

Reported 2026-10-17: Adventurer Armor was invisible on the player, as an outfit and as transmog.

`_Fuse00_AdventurerArmor.esp` (Adventurer HDT-SMP Armor, Nexus SSE 91741) and `_Fuse00_ArmorHelga.esp`
author their 12 ARMAs for vanilla Skyrim: `Race` `DefaultRace 000019` plus the vanilla playable races and
their vampire variants in `AdditionalRaces`. In Enderal the playable Nord and Redguard are **not** vanilla's
`013746`/`013748` — those are the unplayable `NordRaceSkyrim`/`RedguardRaceSkyrim` — but
`NordRace 033899:Skyrim.esm` (**Half Arazealean**) and `RedguardRace 033898:Skyrim.esm` (**Half Qyranian**).
**[verified]** against `reference/base/Skyrim/Races/` and `EnderalFS/Races/`. A player of either race
matches no addon, so the armor draws nothing.

Each override is the mod's ARMA verbatim with `033899` and `033898` appended to `AdditionalRaces`
(8 Adventurer addons, 4 Helga). The Adventurer hood keeps its author's exclusion of the beast races.
No other plugin in the list overrides these addons (binary scan of every `mods/*/*.esp` for `_Fuse00_A`,
2026-10-17), so verbatim is the winning record.

Masters: `Skyrim.esm`, `_Fuse00_ArmorHelga.esp`, `_Fuse00_AdventurerArmor.esp`.

## The general lesson

Any Skyrim armor mod that enumerates races instead of relying on `DefaultRace` is invisible on Half
Arazealean and Half Qyranian players. Check a new armor mod's ARMAs for `033899`/`033898`.

## Status

Built 2026-10-17; deserializes and round-trips byte-identical. **Not yet verified in game.**

## Regenerating

After either Fuse00 mod updates: re-serialize its plugin into `reference/mods/Fuse00AdventurerArmor` or
`reference/mods/Fuse00ArmorHelga`, then run `python src/Fuse00ArmorRaces/tools/01-build-race-overrides.py`
(it asserts 12 addons and that neither race is already present).
