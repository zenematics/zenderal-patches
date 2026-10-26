# AspectLayout

- **Source:** `src/AspectLayout/` — `_ZenAspectLayout.dll` (CommonLibSSE-NG, `build.cmd`, compiled DLL committed),
  `ZenAspectLayout.ini`, and `tools/01-build-layout-sets.py`, which generates the layout sets
- **Ships:** MO2 mod `Zenderal - Aspect Layout`: the DLL + ini, Vel'dun's three HUD layouts under
  `SKSE/Plugins/ZenAspectLayout/<16x9|21x9|32x9>/` with a `manifest.txt` each, the 11 files all three share, and the
  active copies of the 12 that differ. The layout files are generated from the installed Vel'dun patches (not committed).
- **FormID block:** none (no plugin)

## Why

Players had to tick one of 8 `Zenderal - Resolution …` presets and one of 3 `Vel'dun Zenderal patches 16x9/21x9/32x9`
mods. Wabbajack does set a resolution at install (`SetScreenSizeInPrefs` rewrites `Resolution=` in every
`SSEDisplayTweaks.ini`), but the shipped Display Tweaks ini has no `Resolution=` line, the presets override it anyway
through `SSEDisplayTweaks_custom.ini`, and nothing can pick a HUD-layout mod at install. Curator's goal: no manual
tinkering.

## What it does

In `SKSEPlugin_Load`, before the mods that read these files load:

1. Reads the primary monitor's current mode (`EnumDisplaySettingsW`, physical pixels).
2. `AutoResolution = 1`: writes `SKSE/Plugins/SSEDisplayTweaks_custom.ini` (`[Render] Resolution=WxH`) when it differs.
   SSE Display Tweaks 0.5.25 reads it during its own load ("Custom configuration loaded", "Resolution override").
3. Picks the layout from the aspect ratio: below 2.0 → `16x9` (16:9, 16:10), below 2.9 → `21x9` (3360x1440,
   3440x1440, 2560x1080…), else `32x9`. `Layout = 16x9|21x9|32x9` forces one.
4. If that layout differs from `ZenAspectLayout/applied.txt` (or an active file is missing), copies the layout's
   `copy` files over the active ones and records it. Otherwise it leaves them alone, so positions a player changes in
   TrueHUD's or Casting Bar's own menu survive restarts until the screen shape changes.

Load timing **[verified 2026-10-26]**: SKSE 2.3 loads its early plugins (Crash Logger, EnderalSE, Engine Fixes…), then
the rest alphabetically; `_ZenAspectLayout` loads right after `_SplashScreen` (position 184), ahead of CastingBar
(224, reads its ini at load), CompassNavigationOverhaul (240), SSEDisplayTweaks (481) and TrueHUD (504); SkyUI,
SkyHUD and the menu SWFs/meshes/textures are read later still.

## The layout sets (tools/01)

Of the three patches' files, 11 are identical (shipped once, static) and 12 differ: `loadingmenu.swf`, `map.swf`,
`skyhud/skyhud.txt`, `MCM/Settings/SkyUI_SE.ini`, `MCM/Settings/TrueHUD.ini`, `CastingBar.ini`,
`CompassNavigationOverhaul.ini`, `Meshes/Interface/intmenufogparticles.nif`, `Logo/logo.nif`, `logo01ae.nif`,
`mainmenuwallpaper.dds`, `main-menu-wallpaper.dds`. A layout without its own copy gets what wins **without** the aspect
patches (e.g. 16x9's `SkyUI_SE.ini` = Zenderal - Settings', its map/loading menu = Vel'dun UI Enderal Default's); if
nothing provides it (`main-menu-wallpaper.dds`, referenced only by 32x9's own logo mesh), the manifest says `keep`.
`OxygenMeter2.ini` is identical in all three (Oxygen Meter writes its settings back into the winning copy).
**Rerun `tools/01` after any Vel'dun patch update.**

## Load order

`Zenderal - Aspect Layout` must outrank every mod that supplies one of these files: the three Vel'dun aspect patches
(now **disabled**), Zenderal - Settings (`SkyUI_SE.ini`), Vel'dun UI Enderal Default, Casting Bar. It sits at 42 in
Ultra. The 8 resolution presets are **disabled**; enabling one would just be rewritten to the monitor's resolution.
The curator's own `Zen's Ultrawide - 3360x1440 - Do not use` must stay below it (or off), or its copies win.

## Status

Built and deployed 2026-10-26. **Verified in game** on 3360x1440: first launch applied 21x9, second launch logged
"Layout 21x9 already applied", Display Tweaks "Resolution override: (3360x1440)". Not yet tested on a 16:9 or 32:9
screen.
