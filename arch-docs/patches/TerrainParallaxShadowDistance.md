# TerrainParallaxShadowDistance

- **Source:** `src/TerrainParallaxShadowDistance/` (generated: `tools/01-build-parallax-distance.py`)
- **Ships:** *(no plugin: one generated shader include, MO2 mod `Zenderal - Terrain Parallax Shadow Distance`, not committed)*
- **FormID block:** none
- **Pillar:** modern visuals

## Why

Curator's video (Crystal Forest, 2026-10-26): a line across the ground some way ahead, which moves with the player.
Nearer than it, the cobbles have deep crevice shadows; past it the ground looks flat.

**[verified in Bottled Shaders 1.0.18's source]** Bottled Shaders (the list's Community Shaders build, Nexus 192816)
turns terrain parallax **self-shadows** off at a hard view depth: `Lighting.hlsl` ~1509,

```
hasTerrainParallaxShadow = viewPosition.z < ExtendedMaterials::ParallaxCheapDistance && ...
```

with `static const float ParallaxCheapDistance = 1024.0;` in `Shaders/ExtendedMaterials/ExtendedMaterials.hlsli`, so
there is no setting for it. The parallax displacement itself fades smoothly between 1024 and 2048
(`ExtendedMaterialsParallaxCore.hlsli`, `nearBlendToFar`); the shadows do not, which is the line. The terrain here
is PBR (TruePBR) landscape: Extended Materials' own terrain parallax is off (`EnableTerrain` 0).

## What it does

v1.1 (2026-10-26): every terrain-parallax distance limit doubled (`tools/01 [factor]`, default 2), each a one-line
change in a verbatim copy of Bottled Shaders' file:

| File | Limit | 1.0.22 | Here |
|---|---|---|---|
| `ExtendedMaterials/ExtendedMaterials.hlsli` | `ParallaxCheapDistance` (shadows on/off; object shadow quality near/far) | 1024 | 2048 |
| `ExtendedMaterials/ExtendedMaterialsParallaxCore.hlsli` | `nearBlendToFar` depth fade to flat | 1024–2048 | 2048–4096 |
| `Lighting.hlsl` | `doTerrainPom` hard cut-off | 2048 | 4096 |

The curator's screenshot (2026-10-26, green line about 15–20 m out) was still taken without the override (it sat on
the losing side), so which limit draws the line is not settled: this covers both. Costs some GPU time; `tools/01 1.5`
for less. v1.0 changed only the shadow constant (to 3072).

## Load order

The MO2 mod must **outrank** Bottled Shaders: in MO2's left pane it goes **below** Bottled Shaders (in `modlist.txt`, above its line). First try (2026-10-26) sat on the wrong side and changed nothing. Community Shaders recompiles a shader when its source changes; if
the line has not moved, clear the shader cache from its menu and restart. **Rerun `tools/01` after a Bottled Shaders
update** (it refuses if the constant has moved or gone).

## Status

**Verified in game 2026-10-26 (v1.1, factor 2): the line is gone at the curator's spot.** Generated 2026-10-26, regenerated the same day from Bottled Shaders **1.0.22** (constant now at line 35; 1.0.22 also adds a hard `doTerrainPom = viewPosition.z < 2048.0`, hidden because the displacement has already faded to flat between 1024 and 2048, `ExtendedMaterialsParallaxCore.hlsli` line 259).

**Enabled 2026-10-26** in Ultra: `modlist.txt` line 56, directly ahead of Bottled Shaders (57). The compiled cache `overwrite/ShaderCache` (13,201 files) was moved to `E:/Zenderal-backups/2026-10-26-parallax-distance/` so the next launch recompiles from the new source (slow first load).

**Came back 2026-10-27.** Load order and the override files were still right, but Bottled Shaders' 275 shader files had been rewritten at 01:54 (a reinstall during that night's Vanta Core / Bottled add-on tests), so they were newer than the override's copies, and `overwrite/ShaderCache` had been rebuilt until 10:25. Treated as a stale compiled cache: `tools/01` rerun (fresh file dates, same 3 one-line changes against 1.0.22) and the cache moved to `E:/Zenderal-backups/2026-10-27-parallax-cache/`. **After any Bottled Shaders reinstall: rerun `tools/01` and clear the shader cache.** **Verified in game 2026-10-27: the line is gone again** after the recompile, so a stale compiled cache was the cause.
