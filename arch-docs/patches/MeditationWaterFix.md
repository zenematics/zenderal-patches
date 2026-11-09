# MeditationWaterFix

- **Source:** `src/MeditationWaterFix/` (generated: `tools/01-build-meditation-water-fix.py`)
- **Ships:** `Zenderal - Meditation Water Fix.esp` (ESL, HEDR 1.7). Masters Skyrim, Update, FS and
  `Water for Enderal CS.esp`. The live copy is in `Zenderal - Patch Collection`. **Must load after
  `Water for Enderal CS.esp` and `AmnesiaShrine.esp`.**
- **FormID block:** none (overrides only)
- **Owns:** the WRLD header `Akropolis 0A7FB9:Skyrim.esm` (Water for Enderal CS's, verbatim) and all 18 of its cell
  headers, including `ClassMenue 0A7FBC`
- **Status:** v2 (explicit water height 0, water kept) deployed 2026-11-09, **verified in game** the same day.

## v1 was wrong (2026-11-09)

v1 (below) removed `HasWater` and dropped the water to −30000. In game (curator, 2026-11-09) that showed the bare
land at −2048 as light-grey slabs, with dark water strips past the 18 cells: **the sea under the platforms belongs
there** ("the entire water is missing"). The claim below that vanilla shows no water there was never checked.

**v2:** every cell keeps `HasWater`. Only its water height changes, from the "use the worldspace default" marker
`3.4028235E+38` to an explicit `0`, which is the height the engine already used. **Verified in game 2026-11-09** (curator: "confirmed
fixed", after Regenerate Caches): one continuous sea, no sheets. So Unified Water's cache builder evidently reads
that marker as a literal height, which left `Akropolis_cache.wc` empty. Other worldspaces whose cells carry the marker
may show the same sheets; the same fix applies. After deploying: Bottled Shaders → Unified Water → Debug →
**Regenerate Caches**, then check the area. If the sheets still pop, the next suspect is the worldspace's grid origin
(cells start at −2, −1, the misalignment [`UnifiedWaterGridFix`](UnifiedWaterGridFix.md) handles for Vyn).

## Why

Curator's report (2026-11-07): flat grey/purple sheets floated among the platforms and ruins of the meditation
worldspace, *A Strange Place* (`Akropolis`, where Memory Points are spent). They:
- popped in and out as the camera moved, like Vyn's sea before [`UnifiedWaterGridFix`](UnifiedWaterGridFix.md);
- could not be clicked in the console;
- stayed with the vanilla water toggle `tws` off;
- **vanished with Bottled Shaders' Unified Water disabled at boot (verified in game).**

The water comes from base Enderal:
- All 18 Akropolis cells carry `HasWater` with water height `3.4028235E+38`, which means the worldspace default, 0.
- The land sits at about −2048 (no landscape textures). Most placed objects are between z 140 and 390 (measured from
  `reference/base-2.1.4.4`). So the water lies just under the platforms.
- Vanilla shows no water there, and Unified Water draws it as sheets.
- Its cache for this worldspace is empty (`Akropolis_cache.wc`, 32 bytes).

`Water for Enderal CS.esp` overrides the WRLD, pointing its LOD water at its own `000800`. Nothing else in the list
overrides the WRLD.

## The fix

- **The cells:** each cell's winning header, without `HasWater` and with `WaterHeight` −30000, far below the land. The
  cell's refs, land and navmesh are not carried. Every cell's winner is base Enderal except `ClassMenue 0A7FBC`, which
  FS, EGO, `Akropolis_Camping.esp` and `AmnesiaShrine.esp` each override with the same header. The last of them,
  AmnesiaShrine (v4.00, MO2 mod `AmnesiaShrine_v4.00_sse`), is forwarded.
- **The WRLD:** Water for Enderal CS's record, verbatim, because the cells need their worldspace as a parent.
- **The generator asserts** that every cell loses exactly one `HasWater`, had the default water height, and that there
  are 18 cells.

Unified Water stays on everywhere else.

## Upkeep

The plugin overrides every Akropolis cell header, so a later plugin that edits one of them must be forwarded here.
Before re-running `python -I src/MeditationWaterFix/tools/01-build-meditation-water-fix.py`, re-serialize:
- `reference/mods/WaterForEnderalCS`
- `reference/mods/EGO`
- `reference/mods/AkropolisCamping` (`Akropolis_Camping.esp`)
- `reference/mods/AmnesiaShrine`

If a new mod edits Akropolis cells, add it to `OVERRIDES` in load order.

## To verify in game

With Unified Water **on**, enter the meditation area (the Prophecy/Memory Point space) and look around and below the
platforms with `tfc`: there should be no flat sheets. The perk stars and the ruins should look unchanged.
