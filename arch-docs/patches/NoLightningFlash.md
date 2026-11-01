# NoLightningFlash

- **Source:** `src/NoLightningFlash/` (generated: `tools/01-build-no-lightning-flash.py`)
- **Ships:** `Zenderal - No Lightning Flash.esp` (ESL, HEDR 1.7)
- **FormID block:** none (overrides only)
- **Status:** **disabled 2026-10-20 — True Storms was removed from the list instead.** Neither v1.0.0 (colour only) nor v1.1.0 (fades zeroed) stopped the flicker: the strikes come from the 21–27 **thunder sound entries** True Storms adds to each weather (the engine fires a lightning strike, which takes over the sun light, with every thunder clap). Colour and fades only change how the strike looks (v1.1.0: a hard on/off blink). If True Storms comes back, the fix is to strip those thunder entries, not recolour.

## Why

Curator's taste (2026-10-20). On the intro beach the "sun" seemed to jump around: the light on the rocks
changed direction and brightness several times a second.

A 7.7 s recording (120 fps, read frame by frame) showed four identical events, at 2.3, 3.8, 5.6 and 6.4 s.
In each, the whole image, darkest pixels included, jumps about 25% brighter within one or two frames,
holds for 0.4–0.8 s, then fades back over about 0.15 s. Side-by-side frames show the rock faces lit from
a different angle during each event. That is a weather lightning strike: for the length of the flash the
engine moves the directional (sun) light to the strike and tints it with the weather's `LightningColor`.

The intro region `00E_MQ00_Startregion 01B860` uses `_00E_EnderalRainLight 021311`. Base Enderal ships
that weather with `LightningColor: #000000` (no flash). **`Diverse Weather - True Storms.esp`** sets it to
`#FFFFFF`, along with 12 other weathers:

| Weather | Base Enderal | True Storms |
|---|---|---|
| `_00E_EnderalRainLight 021311` and `SkyrimOvercastRain` / `…FF` / `…MA` / `…RE` / `…TU` (`0C821F`, `10A23D`, `10A231`, `10A238`, `10A242`) | `#000000` | `#FFFFFF` |
| `SkyrimStormRain` / `…FF` / `…TU`, `FXMagicStormRain` (`0C8220`, `10A23C`, `10A241`, `0D4886`) | `#DBDCEE` | `#FFFFFF` |
| `SkyrimOvercastRainVT 10A7A6` | `#D5FFFF` | `#FFFFFF` |
| Diverse Weathers' `_00E_GoldenforstRainLight 000800`, `_0E_PilzwaldStorm 00080A` | (new records) | `#FFFFFF` |

So base Enderal's own storms did flash, though in a paler colour. The curator chose black for all 13.

## The fix

Each of the 13 records is copied verbatim from `Diverse Weather - True Storms.esp`, which is their last
overrider in the `Ultra` load order (binary scan; `TrueStormsSE_AOS.esp` doesn't touch them). The
lightning is then switched off:

- **`ThunderLightningBeginFadeIn` / `ThunderLightningEndFadeOut` are removed (= 0).** This is the actual
  switch. Across all 204 Enderal 2.1 weathers, every weather with lightning (storms, sandstorms,
  Pilzwald) has an `EndFadeOut` of about 0.85–1, and every weather without lightning has none. True
  Storms added `EndFadeOut 0.50` to 8 weathers that base Enderal ships without lightning, including the
  intro beach's `021311`.
- **`LightningColor` is set to `#00000000`.** v1.0.0 changed only this. The strikes kept firing and kept
  re-aiming the sun, just untinted, and the beach still flickered in game.

True Storms' precipitation, rain sound loops and colours are kept. Its sound entries on these weathers
are all `Precipitation`-type loops, so with lightning off there are no strikes and no thunder.

The masters are Skyrim, Update, FS, `TrueStormsSE.esp`, `Enderal SE - Diverse Weathers.esp` and
`Diverse Weather - True Storms.esp`; the last one is there to force load-after. Load it directly after
`Diverse Weather - True Storms.esp`.

Weathers are plugin records, so an existing save picks up the fix the next time the weather changes.
Use `fw 21311` on the beach to test it right away.

## Regenerating

Re-serialize `Diverse Weather - True Storms.esp` into `reference/mods/DiverseWeatherTrueStorms`, re-check
that it still wins all 13, then run `python src/NoLightningFlash/tools/01-build-no-lightning-flash.py`.
It asserts 13.
