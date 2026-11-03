# DarkValleySunFix

- **Source:** `src/DarkValleySunFix/` (generated: `tools/01-build-dark-valley-sun-fix.py`)
- **Ships:** `Zenderal - Dark Valley Sun Fix.esp` (ESL, HEDR 1.7)
- **FormID block:** none (overrides only)
- **Owns:** WTHR `048085`, `048087`, `10A23E`, `10A242` (all `:Skyrim.esm`)
- **Status:** built and deployed 2026-10-31. **Unverified in game.**

## Why

Player report (GreaseLord, 2026-10-31): in Dark Valley, looking up filled the screen with white sun rays.
In the screenshots the whole view washes out, with ray streaks spreading from the top of the frame.

Dark Valley's region (`Jonas 0023A3`, also known as Dark Valley; plus its `HerzlandNebel 0E3B0D`
sub-region for `048085`) picks from six weathers. Enderal 2.1 keeps four of them sunless. No other
region in the list uses these four (grep of every serialized region, base and mods):

| Weather | Chance | Enderal 2.1 (FS record) | The Weathers of Enderal (winner) |
|---|---|---|---|
| `SkyrimFog_HerzlandNebel 048085` | 35% | SunColor black, no SunGlare | `#B9D1DB` by day, glare 0.47 |
| `SkyrimStormRain_DarkValley 048087` | 10% | SunColor black, no SunGlare | `#698B96` by day, glare 0.39 |
| `SkyrimFogFF 10A23E` | 30% | SunColor black, no SunGlare | `#BBCBD8` by day, glare 0.47 |
| `SkyrimOvercastRainTU 10A242` | 15% | black except a dim `#405355` sunset sun | `#94A3B8` by day, glare 0.39 |

TWoE also sets `SunGlareColor` to `#0F0F0F` and thins the cloud layers (alpha 1 → 0.6). It is the last
overrider of all four in the `Ultra` load order: a binary scan of every enabled plugin on 2026-10-31 found
`Skyrim.esm` → FS → `TrueStormsSE.esp`/`Diverse Weather - True Storms.esp` (`10A23E`/`10A242` only) →
`Enderal Weather - HDR.esp` (*The Weathers of Enderal - Hotfix*).

Steamin ENB runs with `EnableSunRays=true` (`[RAYS]` multiplier 1.0 by day in `enbseries.ini` and in the
per-weather inis, e.g. `!_RainStorm_heavy_E.ini`, which `048087` maps to). With a visible sun behind thin
clouds in a near-black valley, eye adaptation raises the exposure and the rays white out the screen.

The cause is inferred from the records and the ENB settings. It was not reproduced in game before
building: the patch was requested straight away.

## The fix

Each record is copied verbatim from `Enderal Weather - HDR.esp` (via `reference/mods/TWoE`, checked
identical to a fresh serialize of the hotfix plugin on 2026-10-31). Only Enderal's sun is put back:

- the `SunColor` and `SunGlareColor` blocks are replaced by Enderal 2.1's (FS record), and
- `SunGlare` is removed (= 0, as Enderal ships it).

Clouds, fog, lighting colours, precipitation and sounds stay TWoE's. The generator asserts one block or line
per field and that Enderal's values are black by day.

## Load order and upkeep

- Masters `Enderal Weather - HDR.esp`, so it loads after TWoE. Nothing else in the list touches these four.
- `10A242` is also in the disabled `NoLightningFlash`. If that is ever re-enabled, merge the two: only one
  Zenderal plugin may own the record.
- Rerun after a TWoE update: re-serialize it into `reference/mods/TWoE`, re-check the winners, then run
  `python -I src/DarkValleySunFix/tools/01-build-dark-valley-sun-fix.py`.

## To verify in game

In Dark Valley, type `fw 48085` in the console, then `fw 48087`, and look up at the sky during the day.
There should be no sun disc and no ray white-out. With the plugin off, the white-out should come back.
