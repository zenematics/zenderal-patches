# SilvergroveStoneWalls

- **Source:** `src/SilvergroveStoneWalls/` (generated: `tools/01-build-silvergrove-stone-walls.py`)
- **Ships:** *(no plugin — 3 generated meshes + 3 textures, MO2 mod `Zenderal - Silvergrove Stone Walls`, not committed)*
- **FormID block:** _(none)_

## What it does

Curator's taste: the low stone walls of Enderal's desert towns (`_00E_Tropical_ClayHouseWall01–03`, e.g.
`08A23F`, placed by EPPI Duneville around Old Ishmorlep) get **Skyrim 202X's farmhouse cobbles**, warmed to
Enderal's palette, instead of SureAI's 2014 `silvergrove\brickwall01`.

**[verified on disk 2026-10-24]**

- `wall01/02/03.nif` are the **only** meshes using `brickwall01` (scan of every winning loose mesh plus
  `E - Meshes.bsa` / `Skyrim - Meshes0/1.bsa`). Each is a baked unwrap into one quarter of the 2048 atlas,
  ~2.5 texels per game unit, which is why the stones read as smeared blobs.
- Nothing newer exists: SRP (2K) and ETATU (8K normal, flatter) upscale the same art; SPR PBR (Enderal
  Nexus 1063) keeps SRP's diffuse (an even ~18-level brightness shift) with a shallow 1K height map. Nexus has
  no Silvergrove/desert architecture retexture.
- The meshes carry **vertex colours** (the red-brown tint in game), so the new diffuse is colour-matched to
  the old one: 202X mean RGB [54, 47, 37] → [124, 105, 94], against brickwall01's [124, 109, 95].

## How (tools/01)

1. Copies SRP's three meshes (`SRP Enderal - Architecture (2K)`).
2. Gives every triangle a box projection by which way the **face** points in the wall's frame (PCA long
   axis L, thickness W, up Z): out of the wall → (L, Z), along it (ends and the jagged stone flanks) → (W, Z),
   cap → (L, W). One repeat per **160 units** (`--tile N`). A vertex shared by faces of different classes is
   duplicated per class (253/222/153 → 487/408/322 vertices), so no triangle spans two projections.
   Area-weighted UV stretch (singular-value ratio) ends at median 1.09–1.12, 99th percentile ≤ 1.61 — the
   same as SureAI's hand unwrap (1.12–1.15 / 1.65).
3. Recomputes tangent and bitangent from the new UVs. The storage mapping is learned from the original mesh:
   recomputing from the original UVs reproduces the stored vectors with mean dot **1.00** on all three, as
   *stored tangent = dP/dv, stored bitangent = dP/du*. Positions, normals and colours are asserted equal to
   their source vertex. The BSTriShape block and its header size entry are rewritten; the result is parsed
   back and checked (block types, counts, positions).
4. Diffuse: 202X `stonewall01.dds` (8K) → 4K, CIELAB mean/std matched to SRP's brickwall01 (numpy maths),
   BC7. Normal (4K) and height (2K) copied unchanged. All written to the `brickwall01` paths (nothing else uses
   them).

**v1 (2026-10-24, first in-game look) was wrong twice:** one projection along the wall for every vertex
stretched one texture column across the many faces that point along it (the jagged flanks and ends: chevron
streaks), and Pillow's `LAB` mode stores a*/b* as **signed** bytes, so the green moss in 202X's mortar wrapped
round to magenta ("pink bits"). v1.1 fixes both.

## The well (v1.2, 2026-10-24)

`_00E_Tropical_ClayHouseWell 08A241` (`silvergrove\well.nif`, the only user of `silvergrove\well.dds`) had
SureAI's 1K baked stone atlas (SRP never retextured it; ETATU only a 4K normal) and our flat-grey `_p`. Its
stone shape (`well:7`) gets the same material and per-face box projection, on **world X/Y/Z** (the well is
round: no wall axis), 415 → 663 vertices, stretch median 1.10. The wood (`well:11`, which PGPatcher had given
SPR PBR's planks) and black shapes are asserted byte-identical. `well.dds/_n/_p` are copies of the wall
material.

## Load order

- **Sort ABOVE `PG Patcher Output`.** PGPatcher had already re-pointed these three meshes at SPR PBR's copy
  of the old art.
- PGPatcher's blocklist (`Tools/PG Patcher/PGPatcher/cfg/settings.json`) has
  `*\enderal\architecture\silvergrove\wall01/02/03.nif` and `well.nif`, so later runs leave them alone (backup
  `E:/Zenderal-backups/2026-10-24-silvergrove-walls/`).
- Rerun `tools/01` if SRP or Skyrim 202X updates.

## Status

v1.1 generated 2026-10-24. Unverified in game. Seams show where the projection class changes (front to flank
to cap). If streaks remain at grazing angles, they are parallax from 202X's height map on this lumpy mesh,
not UVs.
