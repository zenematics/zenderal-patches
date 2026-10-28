# ZenWaterTrace

- **Source:** `src/ZenWaterTrace/` (CommonLibSSE-NG, AE through Address Library; `build.cmd`)
- **Ships:** nothing. **Testing tool, not part of the list.** MO2 mod `Zenderal - Water Trace (testing)`, listed in
  `Zenderal.compiler_settings`' Ignore list so Wabbajack never compiles it in.
- **Log:** `My Games/Skyrim Special Edition/SKSE/ZenWaterTrace.log`

## Why

With [Unified Water](UnifiedWaterEnderal.md) on, Vyn's sea loses whole rectangles of water that come back as the camera
turns (curator's video, 2026-10-28). After `Zenderal - Vyn Full Extend.esp`, the cache is complete: decoding
`Vyn_cache.wc` (header `WTCH`, 32-byte instructions: lodLevel, pad, form (8), x, y, size, height) gives 24,700 LOD4
cells, exactly the cells `tools/00 --with-self` predicts, bounds −96, −64 to 66, 133. So the tiles exist, and something
hides them. A camera-dependent pop points at culling.

Suspects, from Unified Water's source (`BGSTerrainBlock_Attach`): it moves each chunk's water node (a
`BSMultiBoundNode` from the terrain `.btr`, whose AABB covers the chunk at one flat height) under the LOD water root
(`gWaterLOD`, ID 516171/402322), sets its translate and runs only `UpdateUpwardPass`. If that node's bound or multibound
does not match where its tiles really are, the engine culls the whole node when the bound leaves the view.
`UpdateWaterLODCull` also hides LOD4 tiles over loaded cells that have `HasWater`.

## What it logs

Read-only, on the main thread:

- Every 500 ms, one line: camera position and direction; how many chunk nodes under the LOD water root are hidden, out of
  the frustum by world bound, out by multibound AABB; how many tiles are hidden or in view; and
  **`IN-VIEW-NODE-OUT`**, the tiles in view whose node is out of view (they get culled with it). Stops after about 33
  minutes.
- On **F11**: every chunk node and tile (local/world position, scale, bound, hidden, in view, outside the node's AABB),
  the loaded cells (attached, `HasWater`, water height) and the game's own water objects.

## How to use

Stand where the sea flickers, turn the camera slowly across a gap, press F11 once while the gap shows and once while
the water is back.

## Status

Built and deployed 2026-10-28. **Run the same day; it found the cause**, then confirmed the fix,
[`UnifiedWaterGridFix`](UnifiedWaterGridFix.md): 554 samples, all at 0 / 0. **Disabled** in Ultra after that.

## Finding (2026-10-28)

3 F11 dumps at the Vyn coast. Of 919 tiles, **692 lie outside the AABB of the chunk node they are parented to**, and up
to 32 tiles at a time were in view while their node was out of view (`IN-VIEW-NODE-OUT`). Those tiles are culled
with their node as the camera turns: the popping rectangles. Example: LOD16 node at world (−20480, −225280), cell
(−5, −55), AABB centre (12288, −192512) ± 32768; its single tile is at local (−12288, −4096) ×16, outside the node.

Cause, **[verified]**: the terrain LOD grid is not aligned to 0 in Vyn. `lodsettings\vyn.lod` (in `E - Meshes.bsa`)
gives the south-west cell **(−69, −55)**, stride 256, so chunk base cells are −69 + n·L (LOD4 bases ≡ 3, 1 mod 4: the
`.btr` names `Vyn.4.-1.-11`, `Vyn.16.-21.-23`). Unified Water's `WaterCache::GetLODCoords` divides absolute cell
coordinates by the LOD level, i.e. assumes chunks start at multiples of L (true for Tamriel). So each node is given the
tiles of a different, 0-aligned chunk that only partly overlaps it. Their world positions are right, but they hang
under the wrong node (culled with it), and where chunks of different LOD levels meet, cells get water twice or not
at all (the strips). Not fixable from plugin data. Options: a runtime fix that rebuilds each Vyn chunk's tiles on the
real grid, a Bottled Shaders source fix (GetLODCoords using the worldspace's LOD origin), or regenerating all of Vyn's
LOD on a grid moved to (−96, −64).
