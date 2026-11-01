# GrassBounds

- **Source:** `src/GrassBounds/` (generator `tools/01-build-grass-bounds.py`)
- **Ships:** `Zenderal - Grass Bounds.esp` (ESL, HEDR 1.7, 38 GRAS overrides, masters only `Skyrim.esm`)
- **FormID block:** none (overrides only)
- **Pillar:** modern visuals (grass LOD)
- **Status (2026-10-31):** built, deployed as MO2 mod *Zenderal - Grass Bounds*, enabled in `Ultra`. Grass cache
  (*Zenderal - Grass Cache*), TexGen and DynDOLOD all rerun with grass the same night; unverified in game.

## What it does

Gives object bounds to the grass types base Enderal left without any, so DynDOLOD can make grass LOD for them.

## Why

41 of base Enderal's 72 GRAS records (`Skyrim.esm` 2.1.4.4, `reference/base-2.1.4.4/Skyrim/Grasses/`) have no
`ObjectBounds` (OBND 0,0,0). Among them is nearly all of Enderal's own grass: every `_00E_Heartland_*`, `_00E_Suncoast_*`,
`_00E_Tropical_*` and ocean grass. Two tools read those bounds:

- **TexGen skips a GRAS without object bounds** when it renders grass LOD billboards (dyndolod.info, *Grass LOD*), so
  DynDOLOD would have drawn grass LOD for only 31 of the 72 types, and missed most of Vyn.
- **NGIO's raycast** (`Ray-cast-mode = 1` capsule, `Ray-cast-width = 0`) sizes its capsule from the grass model's
  bounds, and NGIO's own precache guide tells you to fix (0,0,0) bounds before caching.

Only `Skyrim.esm` defines GRAS anywhere in the list (load-order scan, asserted by the generator), so the 38 overrides
revert nothing.

## How the bounds are measured

Each override is SureAI's 2.1.4.4 record verbatim plus `ObjectBounds`. The box is the axis-aligned extent of every
vertex of the **winning** model: the loose file by MO2 priority, else the last archive in load order that has it
(`Enderal.ini` `sResourceArchiveList`/`2`, then plugin BSAs). Node transforms are applied. SSE (`BSTriShape`) and LE
(`NiTriShapeData`) meshes are both read. Values are **truncated toward zero**, like the Creation Kit.

The generator first measures the 30 GRAS SureAI *did* give bounds to, from the archive copy of their model:
**23/30 match exactly**. With floor/ceil every one was off by 1, which is how the truncation was found. The 7 that
differ are stale on SureAI's side, not measurement errors. For example, `_00E_Heartland_Forestgrass01`'s stored box is
exactly what `_00E_Heartland_Forestflowers01`'s mesh measures, and three `_00E_` records carry
`ForestPlants02`'s box.

Many records share one box (e.g. `-44,-26,0 / 38,45,67` for nine Nico grasses). SureAI built those grasses on one
geometry with different textures. The two family members SureAI did bound (`_00E_Suncoast_Wildgrass01`,
`_00E_Tropical_DryGrass02`) carry the same box.

Three records are left alone because their model exists nowhere in the list (nothing to draw or billboard):
`AlpineSnowbell1k` (`AlpineSnowbell-1k.nif`), `_00E_Test_Flowers_01` and `_00E_Test_Flowers_02`.

Most winning meshes come from *Enderal - Fixed Mesh Lighting* (emissive-only edits, same geometry), *Skyrim Flora
Overhaul stripped for Enderal* and *Remove Small Rocks*. **Rerun `tools/01` after any grass mesh mod change, then
regenerate the NGIO cache.**

## The grass LOD pipeline (set up 2026-10-31)

Before this, the list had **no grass LOD at all**: no NGIO, no `Grass/*.cgid` cache (Grass Cache Helper NG last ran
2026-08-11), TexGen `GrassBillboards=0`, DynDOLOD `DoGrass=0`.

1. **NGIO** — *No Grass In Objects* NGIO-NG **2.0.2** (Nexus 42161, file dated 2026-10-27). It reads Address Library
   `versionlib-*.bin`, so it should load on 1.7.104; confirm with `My Games/Skyrim Special Edition/SKSE/NGIO-NG.log`.
2. **`GrassControl.ini`** ships in *Zenderal - Settings* (`SKSE/Plugins/`). It was rewritten with **all 38 keys
   NGIO 2.0.2 reads** (checked against the DLL's strings), because NGIO writes missing keys back on its own. Its
   notes warn that a second `GrassControl.ini` in overwrite leaves the game stuck at the main menu. Zenderal values:
   `Use-grass-cache = true`, `Only-load-from-cache = true`, `DynDOLOD-Grass-Mode = 1`,
   `Asked-Enable-Raycast-Warning = true` (no pop-up mid-cache). Everything else is NGIO's source default, including
   `Grass-cliffs-enabled = true`: its 93 `Grass-cliffs-forms` all resolve to `DirtCliffs*` statics in Enderal's
   own `Skyrim.esm`.
   **With `Only-load-from-cache = true` and no cache, there is no grass anywhere.** Build the cache before playing.
3. **Cache** — trigger file `Stock Game/PrecacheGrass.txt` (empty, next to `SkyrimSE.exe`). Root Builder already
   lists `PrecacheGrass.txt` in its exclusions (`ModOrganizer.ini`), so Root Builder neither moves it into overwrite
   nor deletes it between crash restarts. Launch through the **`Grass Cache`** MO2 profile: a copy of `Ultra` with
   *TrueHUD - HUD Additions*, *Enderal SE - TrueHUD* and *Zenderal - Texture Trace (testing)* off. NGIO lists TrueHUD
   as crashing cache runs, and no plugin masters `TrueHUD.esl`. Relaunch after a crash and it resumes. When the game
   says *"Grass generation finished successfully!"*:
   - NGIO 2.0.2 deletes `Stock Game/PrecacheGrass.txt` itself (seen 2026-10-31). A run that never finishes leaves it,
     and then every launch caches again and Wabbajack sees a stray file;
   - move `overwrite/Grass/` into the mod *Zenderal - Grass Cache* with the `.cgid` files kept in `Grass/`;
   - check that folder for `.fail` files: their cells will have no grass.
   **First run, 2026-10-31:** 6.5 minutes, no crash, 3,094 `.cgid` (130 MB), no `.fail`: Vyn 2,300 cells, the Ark
   city worldspaces 589, the rest Qyra Island, MQ worlds and Kor cave. The `Grass Cache` profile was then moved to
   `E:/Zenderal-backups/2026-10-31-grass-lod/profile-Grass-Cache` (copy it back to `profiles/` for the next cache run).
   An unfinished 2026-08-14 run had left a 12 MB progress `PrecacheGrass.txt` in `overwrite/Root/`. It was moved to
   `E:/Zenderal-backups/2026-10-31-grass-lod/`, so a new run can't resume August's load order.
4. **TexGen** — tick **HD Grass** (Direct 0, Ambient 135, Smoothness 0: TexGen's defaults). Plain *Grass* is greyed
   out in this list: TexGen disables it when Community Shaders (Bottled Shaders) is installed or complex grass is found
   (SFO Complex Grass), and offers HD Grass instead (dyndolod.info *TexGen*). The preset's `GrassBillboards=1` is
   therefore inert. TexGen needs this plugin enabled.
5. **DynDOLOD** — presets `DynDOLOD_EnderalSE_Default.ini` (last session) and `DynDOLOD_EnderalSE_Zenderal.ini`:
   `DoGrass=1`, `GrassLODMode=1` (= NGIO mode 1), `GrassLODDensity=50` (the Grass LOD page: half density or less
   with HD billboards). The *Grass LOD* checkbox is enabled only when
   DynDOLOD finds the `.cgid` files and the billboards, so the cache mod and TexGen output must be enabled. Lower
   density if it costs too much; grass LOD is built for LOD4 only.

**Result, 2026-10-31:** TexGen (HD Grass) wrote 225 grass billboard files, among them Enderal grasses this patch
bounded (`_00E_Suncoast_Wildgrass*`, `_00E_BeachGrassLush`). DynDOLOD's `Export/LODGen_EnderalSE_Grass_Map_Vyn.txt`
maps 41 grass types for Vyn, including the Nico grasses (`NicoDryGrass01 0008D982`, `NicoHagebutte 0008D981`,
`NicoTurtlegrass`, `NicoWheatGrass` …), and LODGen for Vyn ended `Code: 0`. Re-enabling *DynDOLOD_Output* put
`DynDOLOD.esp`/`Occlusion.esp` after `Zenderal - Vyn Full Extend.esp`; see [`UnifiedWaterEnderal.md`](UnifiedWaterEnderal.md).

## Tree LOD brightness (changed the same day)

The 2026-10-30 LOD run had three dimmers stacked, all apparently tuned for ENB (the list has run Bottled Shaders since
2026-10-20):

| Setting | Was | Now |
|---|---|---|
| TexGen tree billboards Direct / Ambient (and HD Direct) | 80 / 55 (80) | 135 / 150 (135), the August SSE-mode run's values |
| DynDOLOD `TreeLODBrightness` (both presets) | -10 | 0 |
| `DynDOLOD_ENDERALSE.ini` `CrownBrightness` / `TrunkBrightness` / `FlatTrunkBrightness` (3D tree LOD vertex colours) | 0.4 (as installed; SSE ini: 1.0) | 0.7 |

Backups of every changed file are in `E:/Zenderal-backups/2026-10-31-grass-lod/`. Judge the result in game and adjust
from there. *Darker Tree LOD for Enderal* and *Darker Distant LOD for ENB* are disabled and play no part.

The Arboreal Revived 3D tree LOD: DynDOLOD used 35 of the 56 *For Fixed Mesh Lighting* models (their CRC32 matches
the winning full trees). *For Vanilla EnderalSE* and the base *Ultra Tree LOD SE* matched none.
