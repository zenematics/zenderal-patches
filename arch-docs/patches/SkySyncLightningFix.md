# SkySyncLightningFix

- **Source:** `src/SkySyncLightningFix/` (CommonLibSSE-NG, AE through Address Library, Microsoft Detours; `build.cmd`)
- **Ships:** `ZenSkySyncLightning.dll` (MO2 mod `Zenderal - Sky Sync Lightning Fix`)
- **Pillar:** modern visuals
- **Log:** `My Games/Skyrim Special Edition/SKSE/ZenSkySyncLightning.log`

## Problem

With Bottled Shaders' **Sky Sync** on, every lightning strike in a storm made the daylight and the shadows sweep across
the scene, which looked like time passing quickly. It did not happen under ENB. It was found on 2026-10-23, and the
curator confirmed it again on 2026-10-29: one sweep per strike.

### Earlier attempts (2026-10-23, all failed or only avoided it)

Recorded in [`modlist/mod-gotchas.md`](../modlist/mod-gotchas.md):

- Sky Sync's `ShadowTransitionDuration` 300 → 0: it still swept.
- `UseAlternateSunPath` true → false: it still swept.
- Sky Sync disabled at boot: the sweep stopped, but Sky Sync was lost. This was the standing decision until 2026-10-29.
- Before that, *No Lightning Flash* (black lightning colour, zero fades) only hid strikes. Its real target was True Storms'
  thunder sounds ([`NoLightningFlash.md`](NoLightningFlash.md)).

## Cause (traced 2026-10-29)

[`ZenSkySyncTrace`](ZenSkySyncTrace.md) logged the sky, the sun and the sun shadow light every frame around 4 strikes
in weather `0001DF4E`, at 10:00 game time. Strike 1:

| ms after strike | flash | sun node / global sun position | directional light | shadow `sunVector` |
|---|---|---|---|---|
| 0 | 1.000 | h 6.13 e 35.50 | h 6.13 e 35.50 | e 35.50 |
| 17 | 0.968 | h 6.13 e 35.51 | h 6.13 e **84.84** | e 35.50 |
| 117 | 0.774 | unchanged | e 78.32 | e **78.32** |
| 234 | 0.548 | unchanged | e 66.25 | e 66.25 |
| 467 | 0.098 | unchanged | e 43.89 | e 43.89 |
| 535 | 0 | unchanged | e 35.53 | e 35.53 |

- The sun never moves.
- On a strike, the **directional light** keeps its heading and tilts to almost straight overhead. It falls back as the
  flash fades over `fWeatherFlashDuration` 0.5 s (`fWeatherFlashDirectional` 1).
- The sun shadow light takes the tilted vector each time its update timer runs out, about every 0.12 s, so the shadows
  shorten to almost nothing and then lengthen again. That is the sweep.
- Strikes 2–4 show the same.

Bottled Shaders' Sky Sync calls the game's own `Sky::Update` and then sets the light from the sun (`Sky_Update` thunk at
`CommunityShaders.dll` +0xC3B930, the original called first). Its only flash-related code
(`fWeatherFlashDirectional` × `sky->flash`, at +0xC3D690) changes the light **colour**, not its direction. Sky Sync's
own settings therefore have nothing to do with the tilt, which is why tuning them failed. Who writes the tilt was not
pinned down further, because the fix below does not depend on it.

## Fix

At data load, if `Sky::Update` (ID 25682/26229) already starts with a jump (Sky Sync's Detours hook), it hooks the same
function with Detours. Its hook runs after Sky Sync's:

- **No flash** (`sky->flash` = 0): it remembers the light's rotation, which is the one Sky Sync just set.
- **During a flash:** it puts that rotation back on the light and updates it.

The flash's colour and ambient boost are untouched, so a strike still lights the scene; only the direction stays put.
Holding the direction for 0.5 s is harmless, since the sun moves about 0.01° in that time.

If Sky Sync is disabled at boot, nothing hooks `Sky::Update`, and the DLL logs that it is not installing.

For the first 5 strikes it logs the light before and after it is held, plus whether the light is still held when an
SKSE task runs later in the same frame. `TILTED AGAIN` would mean something after `Sky::Update` tilts the light again,
and the hold has to move later in the frame.

## Install

- MO2 mod `Zenderal - Sky Sync Lightning Fix`. It shares no files with other mods, so its position doesn't matter.
- Sky Sync has to be enabled (not in *Disable at Boot* in *Zenderal - Settings*' `SettingsUser.json`); it is, as of
  2026-10-29.

## Status

Built and deployed 2026-10-29. **Verified in game 2026-10-29.** The curator tested a forced storm (`fw C8220`) and
confirmed Sky Sync works with it. The logs from that run show 2 strikes:

- the light stayed at elevation 40.5° for the whole flash (85° without the fix);
- the shadow `sunVector` did not move;
- all 63 later-in-frame checks read "still held".

The light was already at its pre-strike direction when this hook ran, both on the first flash frame and later, so the
tilt is not written inside `Sky::Update` itself. The fix still removes it, and which code wrote it was not investigated
further. If a Bottled Shaders update brings the sweep back, re-run [`ZenSkySyncTrace`](ZenSkySyncTrace.md) with the fix
on and with it off.
