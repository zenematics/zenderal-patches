# ZenSkySyncTrace

- **Source:** `src/ZenSkySyncTrace/` (CommonLibSSE-NG, AE through Address Library; `build.cmd`)
- **Ships:** nothing. **Testing tool, not part of the list.** MO2 mod `Zenderal - Sky Sync Trace (testing)`, listed in
  `Zenderal.compiler_settings`' Ignore list so Wabbajack never compiles it in.
- **Log:** `My Games/Skyrim Special Edition/SKSE/ZenSkySyncTrace.log`

## What it logs

Read-only, from an SKSE task once per frame:

- the sky: game hour, current/last weather, `flash`, `flashTime`, lighting transition;
- the sun: node position, the engine's global sun position (ID 527924/414871), and its directional light's local and
  world direction;
- the sun shadow light (`ShadowSceneNode[0]->sunShadowDirLight`): `sunVector`, `lastSunVector`, `sunUpdate`,
  `sunUpdateMode`;
- once at load: `fWeatherFlash*`, `fSunAlphaTransTime`, `fSunShadowUpdateTime` and `fSunUpdateThreshold`.

It logs every frame from a strike until 25 s after it, otherwise once a second. Directions are logged as
heading/elevation in degrees.

## Result (2026-10-29)

Run in a storm with 4 strikes: on each strike the light, not the sun, tilts to about 85° and falls back over the 0.5 s
flash, and the shadow vector follows. That is the cause [`SkySyncLightningFix`](SkySyncLightningFix.md) fixes.

A second run with the fix on (`fw C8220`, 2 strikes) showed the light and shadows flat through the flash. After that the
mod was to be unticked in MO2; it is Wabbajack-ignored either way.
