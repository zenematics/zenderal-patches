# OldTempleWeather

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/OldTempleWeather/`
- **Ships:** `Zenderal - Old Temple Weather.esp`
- **FormID block:** none (overrides only)

## What it does

The intro beach by the Old Temple (`MQP03Temple 01AC7D`; every cell is in region `00E_MQ00_Startregion 01B860`) had odd night lighting. Stock Enderal pins that region to `_00E_EnderalRainLight 021311` @100, but `Obsidian Weathers - Enderal.esp` (234) swaps it for Skyrim's `SkyrimOvercastRainTU 10A242`, which Steamin ENB's `_weatherlist.ini` maps to generic `!_RainyWeather_E.ini` instead of its dedicated `!_Enderal_RainLight.ini`. Obsidian does not master RAO, so the same override also reverted RAO's region sound chances (collateral; Obsidian's RDSA equals base Enderal's). Override = RAO's record verbatim (`reference/mods/RAO/Regions/`); RAO itself still carries `021311`. Masters: Skyrim + `Obsidian Weathers - Enderal.esp` (content-unused, forces load-after). Note: `MQP02Ship` (the intro ship) and this worldspace have no Climate, so they fall back to `DefaultClimate 00015F` → `SkyrimClear 00081A` — both overridden by `Obsidian Weathers.esp`; that is Obsidian's intended look and is NOT patched. Two MO2 mods ship `Obsidian Weathers.esp` ("Obsidian Weathers for Enderal" and "Obsidian Weathers and Seasons") — only the higher-priority copy loads. Built 2026-10-06, not yet verified in game; console `fw 21311` on the beach previews the fix. **Only meaningful while Obsidian Weathers is enabled** — it masters `Obsidian Weathers - Enderal.esp`, so it must be disabled with Obsidian (missing master), and without Obsidian the region keeps Enderal's `021311` on its own. As of 2026-10-06 Obsidian (both copies + `SteaminENB Obsidian Weathers Patch`) is disabled in Alpha 0.3 for an A/B against Enderal's own weathers + True Storms + Diverse Weather, and this patch is disabled with it.
