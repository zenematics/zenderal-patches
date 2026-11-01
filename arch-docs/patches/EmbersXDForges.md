# EmbersXDForges

- **Source:** none. The mod is two files copied unchanged from Embers XD 3.2.6 (nothing committed).
- **Ships:** MO2 mod `Zenderal - Embers XD Forges` containing `meshes/furniture/blacksmithforgemarker.nif` and
  `blacksmithforgemarkerwr.nif`. It sits directly above `Static Mesh Improvement Mod` and below `PG Patcher Output`.
- **Status:** set up 2026-10-30 and PGPatcher rerun by the curator (Update Output). PG Patcher Output's two forge
  meshes now carry `EmbersHD\mx_coals_*`. Unverified in game.

## Why

The blacksmith forges had no Embers XD coals. The usable forge is furniture `CraftingBlackSmithForge 0CAE0B`
(`Furniture\BlacksmithForgeMarker.nif`), and the Whiterun-style one is `0BF9E1` (`…MarkerWR.nif`). Both paths are
served by three mods:

| Mod (Ultra, top = wins) | Coals |
|---|---|
| `PG Patcher Output` (priority 4) | none. Built 2026-10-26 from SMIM's copy |
| `Static Mesh Improvement Mod` (455) | none (vanilla `FXembers.dds`) |
| `Embers XD` (503) | `textures\EmbersHD\mx_coals_*` |

SMIM outranked Embers XD on these two meshes, so PGPatcher patched SMIM's copy and the coals never reached the game.
The static forge `blacksmithforge01.nif` was fine, because SMIM doesn't ship it.

Embers XD's other losses are deliberate, so they were left alone: Cozy Campfires, SRP, Burnt Wood (Glow) and Flame
VFX Edit. Moving Embers XD itself above SMIM would also flip the firepit, smokestack and chimney meshes, so only the
two forge meshes were copied into a mod of their own.

## After any change

Run PGPatcher **from MO2**, with `PG Patcher Output` unticked, using **Update Output**, then tick the output again.
PGPatcher refuses to run outside MO2's VFS (`VFS not detected`). Even with `--ignore-mo2vfscheck` it still stops,
because the output mod is enabled. Without the VFS its plugin pass would only see Stock game's plugins, so don't
force it.
