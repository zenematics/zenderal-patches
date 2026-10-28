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

**Still holes (curator, 2026-10-28, same evening):** a thin tan band across the distant sea. That colour is sky
showing through a gap with no geometry at all. Neither Unified Water nor this DLL can add water where the terrain LOD
has no chunk. An offline check (`btr_water.py`, the cache against `XLODGen Output Terrain/meshes/terrain/Vyn/*.btr`)
found:

- Every `.btr` that exists has a water node.
- The terrain LOD stops at the **old** Vyn bounds: LOD4 x −69..58, y −55..124; LOD8 to y 128; LOD16 to y 136.
- **18 LOD4 chunks are missing although their LOD8 parent exists** (row y 125, x −69..−1; 207 sea cells). When the
  camera is close enough for that LOD8 chunk to split into its LOD4 children, a 4-cell strip has no terrain and no
  water.
- 6,067 Full Extend cells (west of x −69, south of y −55) have no terrain LOD at any level, so no distant water ever.

Likely fix: regenerate Vyn's terrain LOD (xLODGen) with `Zenderal - Vyn Full Extend.esp` loaded. That is the job
Full Extend does for Tamriel. Not yet confirmed that the curator's band is one of these strips: it needs the
player's position.

**The brown patches (trace 1.1.0 coverage + grid fix 1.0.2 log, 2026-10-28):** brown = LOD seabed where a cell has
no water tile; they vanish up close because finer chunks take over.
- Of 1,386 uncovered sea cells near the camera, 1,240 are in the Full Extend margin, which has no terrain LOD (nothing
  can draw there).
- The rest all lie in **LOD32 chunk −5,9**. It attached with `block->water` empty although its `.btr` (in
  `E - Meshes.bsa`, not xLODGen's output) has a `WATER` node.
- That file is the odd one of the 24 LOD32 files: no LODGen header, and an extra `background` node before `WATER`.
- Six inland LOD4/8 chunks also have no water node, correctly: they have no sea.

**1.1.0:** before Unified Water's hook runs, a block with no water pointer gets its chunk's child named `WATER`.
Unverified in game.

**Tiles drawn but not visible (trace 1.3.0–1.5.0, 2026-10-28):** the curator confirmed the seabed shows where whole
tiles vanish as the view changes. What the experiments showed:
- Forcing the tiles to draw (cull all pass, always draw, ignore multibounds) changed nothing.
- Setting each tile's plane flat at its own height changed nothing.
- Horizon Fix off changed nothing.
- A hook on `BSWaterShader::SetupGeometry` showed nearly every in-view tile set up every frame (e.g. 224/224).

So the tiles are submitted and still don't show.

**Bottled Shaders differs from upstream here.** Its own code (`InTheBottle/Bottled-Shaders` at `cfcac91ad`, the
installed build) runs `AddWater` under the water system's lock. It then pops the object and releases the
reflection/normals entries the object left behind (`RemoveOrphanedEntry`, deferred release `69180/70544`). Their
comment: those entries "keep raw pointers to its material". 1.1.0 copied upstream's older pop-only code, so every Vyn
tile left them behind. **1.3.0** copies Bottled Shaders' registration and helpers as they are. 1.2.0's 4-cell merge cap
is set back to 32 (off), so this is the only change. Unverified in game.

**Still unexplained (2026-10-28, late):** 1.3.0 didn't clear the patches. Trace 1.4–1.6, from a run where the F10 modes
showed on screen:
- All ~5,000 tiles carry flags `40C4`.
- Every property plane is flat at its tile's height.
- Properties are not shared between tiles.
- Mode 5 (plane forced), mode 6 (Depth bit `0x4` cleared) and mode 7 (Refractions bit `0x80` cleared) changed
  nothing. Caveat: the shader technique may be fixed when the render pass is built, so runtime flag edits may not
  reach the draw (unverified).

**LOD32 chunk −5,9 is Enderal's world-map mesh**, not terrain: `map` plane at z 100,000, `background` at 97,000.
1.1.0's by-name `WATER` hand-over was wrong and is removed in **1.3.1**; it hadn't fired in any later run.

**The seabed patches: fixed in 1.4.0 (verified in game 2026-10-28).** Every tile is now built with Unified Water's
flags minus bit `0x4` (Depth by the usual naming), set before the tile is first drawn.
- With Depth, whole tiles read about zero water thickness from the depth buffer. The shader then shows only its
  refraction, the seabed behind, which looks exactly like a missing tile and comes and goes with the view.
- *Why* the depth read fails for those tiles (Bottled Shaders' ReverseZ, DLSS upscaling, draw order) is not known.
- Cost: distant LOD water has no depth-based shallows. Loaded-cell water is unaffected.
- Trace 1.6's runtime flag edit (mode 6) did nothing, because the technique is fixed when the tile's passes are
  built. The flag has to be set at creation.
- 1.3.0's reflection/normals release (Bottled Shaders' own pattern) stays. The merge cap stays off (32).

Still to do: `Zenderal - Vyn Full Extend.esp` loads **before** `Occlusion.esp` (plugins.txt lines 438/444), against
its doc. Disable `Zenderal - Water Trace (testing)` after use. Worth reporting upstream: the grid origin
(`GetLODCoords`) and the Depth path on Unified Water tiles.

Rebuild against a Bottled Shaders update. The DLL refuses to hook if Attach no longer carries Unified Water's jump. It
depends on Unified Water's cache format and tile layout (`WaterCache.cpp`, `UnifiedWater.cpp`, dev branch 2026-10).

Upstream: worth reporting to Bottled Shaders. `GetLODCoords` (and `GenerateInstructions`' chunking) should use the
worldspace's LOD origin from its `.lod` file, not 0.
