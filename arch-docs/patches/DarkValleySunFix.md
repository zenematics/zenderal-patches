# DarkValleySunFix

- **Source:** `src/DarkValleySunFix/` (generated: `tools/01-build-dark-valley-sun-fix.py`)
- **Ships:** `Zenderal - Dark Valley Sun Fix.esp` (ESL, HEDR 1.7)
- **FormID block:** none (overrides only)
- **Owns:** 32 WTHR since 2026-11-05: every weather Enderal ships sunless that TWoE gives a sun (list below);
  Dark Valley's `048085`, `048087`, `10A23E`, `10A242` were the first four (2026-10-31)
- **Status:** built and deployed 2026-10-31, widened 2026-11-05. **Unverified in game.** Live copy in
  `Zenderal - Patch Collection`; the name stays for saves and the MO2/Wabbajack setup.

## Widened to every sunless weather (2026-11-05)

Player report (Longinus, 2026-11-04): *"so bright when looking at the sky at a specific angle when raining"*,
with a screenshot of a near-white sky in Ark, on the Golden Sickle quest. Ark's regions (`CapitalCity*`) rain with
`_00E_EnderalRainLight 021311` (90% in the castle region, 2% elsewhere) and `SkyrimStormRain 0C8220`. Enderal ships
both with no SunGlare, and `0C8220` with a black day sun. TWoE gives both a glare of 0.39 and `0C8220` a visible sun:
the same white-out as Dark Valley.

Comparing all 64 TWoE weathers with Enderal 2.1's found the same edit on dozens more. The generator now picks by rule:
**Enderal's day sun is black and TWoE's is not, or Enderal has no SunGlare and TWoE adds one.** That rule picks 32,
including Dark Valley's four, which come out byte-identical to the first build (asserted). It covers the fog, rain,
storm and snow weathers, their no-rain variants, and the quest weathers built on them (MQ07a, MQ11, MQ17, MQ18
epilogue, NQR05). `_00E_EnderalRainLight`/`RainLightFogged` keep Enderal's own dim sun `#8C7B6C`; only TWoE's glare
goes. Weathers where TWoE only re-tints a sun Enderal already shows (clear, cloudy, desert) are left as TWoE has them.

TWoE (`Enderal Weather - HDR.esp`, the **Hotfix** copy, which outranks the base TWoE mod) is the last overrider of all
32 (binary scans of the Ultra load order 2026-10-31 and 2026-11-05; the FS-defined ones scanned against FS as
master). `reference/mods/TWoE/Weathers` matched a fresh serialize of the Hotfix on 2026-11-05. The cause is still
inferred from the records and the ENB rays, not reproduced in game. Previous plugin in
`E:/Zenderal-backups/2026-11-05-sunless-weathers/`.

In game: in Ark, `fw 21311` (or `fw C8220`) by day, then look up at the sky toward the sun. There should be no glare
or white-out.

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
  `python -I src/DarkValleySunFix/tools/01-build-dark-valley-sun-fix.py`. It re-picks by the rule, so check its
  printed list against the winners (another weather mod loading after TWoE would need its record as the source).

## To verify in game

In Dark Valley, type `fw 48085` in the console, then `fw 48087`, and look up at the sky during the day.
There should be no sun disc and no ray white-out. With the plugin off, the white-out should come back.
