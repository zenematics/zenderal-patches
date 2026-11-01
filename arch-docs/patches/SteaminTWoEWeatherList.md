# SteaminTWoEWeatherList

- **Source:** `src/SteaminTWoEWeatherList/tools/01-build-weatherlist.py`
- **Ships:** a generated `Root/enbseries/_weatherlist.ini` (Steamin ENB's list + 19 IDs), MO2 mod
  `Zenderal - Steamin TWoE Weather List`. Not committed: it is Steamin's file with additions.
- **FormID block:** none (no plugin)

## Why

The list runs **Steamin ENB** through **Bottled Shaders' Effects 11** (CS feature, `Shaders/Features/Effects11.ini`,
Nexus 179824), which loads ENBSeries presets and, like ENB, takes per-weather values from the file each weather is
mapped to in `enbseries/_weatherlist.ini`. "Weathers without a file in `_weatherlist.ini` use the `enbseries.ini`
values" (CS's own text). Steamin's list maps base Enderal's weathers by bare FormID. **The Weathers of Enderal**
(`Enderal Weather - HDR.esp`, + hotfix) adds no weathers, only overrides 55 base + 9 FS ones, and the disabled
*SteaminENB Obsidian Weathers Patch* is byte-identical to Steamin's list. **[verified 2026-10-23]**

A load-order scan (weathers referenced by winning CLMT/REGN records) found **18 weathers in play without an entry**,
plus Foggy Nights' script-forced `NightThickFog`, all falling back to the generic values:

| Weather | Defined in | Steamin file |
|---|---|---|
| `EnderalClearNoClouds 13706E` (3 users) | Skyrim.esm | `!_Enderal_Clearnoclouds.ini` |
| `_00E_Desert 043C5C` (4) | Skyrim.esm | `!_Enderal_Desert.ini` |
| `_00E_EnderalRainLightFogged 0DB551` (13) | Skyrim.esm | `!_Enderal_RainLight.ini` |
| `_00E_Ark_NQ_Kor_CaveWeather 072B93` | Skyrim.esm | `!_Enderal_IsleOfKorWeather.ini` |
| `_00E_Farmcoast 076985` (Pleasant) | Skyrim.esm | `!_ClearWeather_pineforest_E.ini` (Steamin's SkyrimClear file) |
| `_00E_SuncoastSunrise 00703C` | Skyrim.esm | `!_Enderal_Tropenidylle.ini` (Steamin's palm-grove file) |
| `_00E_Thalgard 06877C` (Rainy) | Skyrim.esm | `!_RainyWeather_E.ini` |
| `_00E_Thalgard_New 0373C7` (Cloudy) | Skyrim.esm | `!_Foggy_Thalgard_E.ini` |
| `SkyrimClear_Aurora_Green/Red/Violet 02ED52/50/51` (7/2/1) | FS | `!_Enderal_Clear_Aurora_*.ini` |
| `_00E_FS_NQR05_SiteWeatherSnow 01FDCF` / `_TempleWeather 02E501` | FS | `!_SnowyWeather_E.ini` / `!_ClearWeather_snow_E.ini` |
| `_00E_GoldenforstRainLight`, `SkyrimKristallwald`, `SkyrimFogMAGoldenforst`, `_0E_PilzwaldStorm`, `_0E_PilzwaldFog` (`0x800/801/805/80A/80B`) | Enderal SE - Diverse Weathers.esp | RainLight / Cloudy / Foggy / RainStorm_heavy / Pilzwald |
| `NightThickFog 0x800` | Foggy Nights - Enderal.esp (light) | `!_FoggyWeather_E.ini` |

Files were chosen from each weather's classification flag and the file Steamin already gives its sibling weathers.
IDs are appended to the first section that uses the file (Steamin repeats files across its 499 sections).

## Runtime FormIDs — load-order dependent

Effects 11 parses `WeatherIDs` as hex only (no plugin names, `WeatherManager::ParseWeatherIDs`), so non-base weathers
need their runtime ID. The generator reproduces the engine's order: the 5 base masters, then every `Skyrim.ccc` entry
present in `Stock Game/Data` **in .ccc order, unsorted** (CC Fish, Survival, Curios, AdvDSGS, `_ResourcePack.esl`,
Enderal - Forgotten Stories.esm, SkyUI_SE.esp — so FS is `07`, not 05), then `plugins.txt`'s enabled plugins in
`loadorder.txt` order, masters first. `--check` compares every index with `skse64.log`'s table: 422/422 match
(2026-10-23). **Rerun after any load-order change** (Diverse Weathers was `45`, Foggy Nights light `0EF`).

## Status

Generated and installed 2026-10-23; the mod must be enabled **above Steamin ENB** (MO2 was open). Unverified in game
(check in Effects 11's editor: *Weather files* should list the file for these weathers instead of "no weather file").
