# UnifiedWaterGridFix

- **Source:** `src/UnifiedWaterGridFix/` (CommonLibSSE-NG, AE through Address Library, Microsoft Detours; `build.cmd`)
- **Ships:** `ZenUnifiedWaterGrid.dll` (MO2 mod `Zenderal - Unified Water Grid Fix`)
- **Pillar:** modern visuals
- **Log:** `My Games/Skyrim Special Edition/SKSE/ZenUnifiedWaterGrid.log`

## Why

[`ZenWaterTrace`](ZenWaterTrace.md) found it (2026-10-28). Bottled Shaders' Unified Water looks each terrain LOD chunk
up with `WaterCache::GetLODCoords`, which divides the chunk's base cell by the LOD level. That assumes chunks start at
multiples of their size, as Tamriel's do. Vyn's grid starts at cell **(−69, −55)** (`lodsettings\vyn.lod`). So every Vyn
chunk got the tiles of a different, 0-aligned chunk:

- tiles hang under the wrong node and vanish with it as the camera turns (692 of 919 tiles outside their node's AABB);
- where chunks of different LOD levels meet, cells get water twice or not at all (the strips).

The cache itself is complete once [`UnifiedWaterEnderal`](UnifiedWaterEnderal.md)'s plugin is loaded.

## What it does

At data load, if `CommunityShaders.dll` is loaded and `BGSTerrainBlock::Attach` (ID 30934/31737) already carries Unified
Water's Detours jump, it hooks the same function with Detours. Its hook runs Unified Water's hook first, then fixes the
result.

For a chunk that just attached whose base cell is **not** a multiple of its LOD level, it:

1. throws away the tiles Unified Water made;
2. rebuilds them from Unified Water's own disk cache (`<worldspace>_cache.wc`: the per-cell LOD4 entries, re-read when
   the file changes) for the chunk's real cells;
3. merges them like Unified Water (greedy squares of equal height and form above LOD4);
4. registers them like Unified Water: clone of `meshes\water\watermesh.nif`, `AddWater` then `pop_back`, the same
   shader flags;
5. hides LOD4 tiles over loaded water cells, by the same rule as Unified Water;
6. stretches the node's multibound in Z over lake heights.

If Unified Water found nothing for the wrong chunk and left the node on the terrain chunk, it takes the node the way
Unified Water does. Unified Water's detach hook then cleans up as usual (`waterAttached`).

Aligned chunks (all of Tamriel) are left alone. Bottled Shaders and its files are not modified.

## Status

Built 2026-10-28. Deployed as MO2 mod `Zenderal - Unified Water Grid Fix` (top of Ultra's `modlist.txt`), next to
`Zenderal - Vyn Full Extend` and Unified Water. **Verified in game the same day.** The curator says the sea no longer
pops with the camera. The log shows the hook found Unified Water's, 24,700 cache cells read, and chunks rebuilt (LOD8
and LOD16, some that Unified Water had left empty). [`ZenWaterTrace`](ZenWaterTrace.md) ran alongside for about
4.6 minutes at the coast: every one of 554 samples had **0 tiles outside their node's AABB and 0
`IN-VIEW-NODE-OUT`**. The first run had 692 of 919 tiles outside. The trace was disabled afterwards.

Rebuild against a Bottled Shaders update. The DLL refuses to hook if Attach no longer carries Unified Water's jump. It
depends on Unified Water's cache format and tile layout (`WaterCache.cpp`, `UnifiedWater.cpp`, dev branch 2026-10).

Upstream: worth reporting to Bottled Shaders. `GetLODCoords` (and `GenerateInstructions`' chunking) should use the
worldspace's LOD origin from its `.lod` file, not 0.
