# TreeLOD21Match

- **Source:** `src/TreeLOD21Match/` (generator `tools/01-match-tree-lod-crc.py`)
- **Ships:** MO2 mod *Zenderal - Tree LOD 2.1 Match*: 5 generated 3D tree LOD models (copies of Enderal Arboreal
  Revived's, renamed; `tools/01`), and MO2 mod *Zenderal - Tree LOD 3D*: 85 3D tree LOD models built from the full
  trees (`tools/02`). Neither is committed. Run `01` then `02`, then DynDOLOD.
- **FormID block:** none (no plugin)
- **Pillar:** modern visuals
- **Status (2026-10-31):** both generators run, both mods ticked, DynDOLOD rerun (billboard brightness +2, 3D tree
  brightness 0.7): Vyn's LOD4 is 28,628 3D trees / 4 billboards. Verified in game.

## What it does

Gives nine Enderal tree types their 3D LOD back: the six Nehrimese aspens (`_00E_Nehrimese_Aspen01–03` and their
`_Windy` variants) and three Enderalean trees (`_00E_Tree_Enderalean02_Optimised`,
`_00E_Tree_EnderaleanCypress01/02_Optimized_Ark`). Since Enderal 2.1 they had been flat billboards.

## Why

DynDOLOD matches a 3D tree LOD model to a tree by the CRC32 of the full model: `<name>_<CRC32>passthru_lod.nif`.
Enderal 2.1 re-saved many tree meshes (2.1.4 merged Fixed Mesh Lighting's emissive edit, among other changes), so their
CRC32 changed, and Enderal Arboreal Revived's models (made for 2.0) stopped matching. The 2026-10-31 DynDOLOD Tree
Report: 452 TREE base records, 107 with a 3D model, **106 with only a billboard** (`Billboard1 using internal` at LOD4:
two crossed planes, an X seen from above). 28 of those 106 have a 3D model installed under a different CRC32.

dyndolod.info (*Ultra Tree LOD*): "If full models have been converted, update the CRC32 in the 3D tree LOD filename so
they match again." That is only right if the shape is the same, so the generator checks it against Enderal 2.0's
archives (backup `E:/Zenderal-backups/2026-10-19-pre-AE-migration/Stock game/Data/`):

| Result | Trees |
|---|---|
| **Matched**: a model exists for the 2.0 CRC32, and 2.0 and 2.1 have identical vertex positions and triangles in every `BSTriShape` | `nehrimeseaspen01/02/03`, `gkbcyrodil1_optimized`, `gkbcyrodil2_optimized` (models from *For Vanilla EnderalSE*) |
| Shape changed in 2.1, skipped | `treeaspeniced01/02/03/05/06`, `treeaspen04` |
| No model for the 2.0 CRC32 (the HLT add-on's are for Happy Little Trees' own meshes) | `treeaspen01–06`, `reachtree01`, `reachclifftree01/02`, `treereachtree01magic`, `wrtempletree01`, `wrtempletreesapling01` |
| No 2.0 copy (mod meshes) | `treeaspenspring04–06` (Seasonal Aspen Trees), `treepineforeststump01/02a` (Grumbledook Ivy fixes), `reachtree02` (PG Patcher duplicate path) |

DynDOLOD already handles PG Patcher's re-saved meshes itself: its report gives `[Original CRC32] [Patched CRC32]`
and matches on the original. PG Patcher is not the cause.

## Install and rerun

The mod has no plugin and overlaps nothing; any priority works. Tick it, then rerun **DynDOLOD only** (TexGen is not
needed). Rerun `tools/01` after an Enderal update, a tree mesh mod change or a DynDOLOD run that changes the report.
It reads the newest `Tools/DynDOLOD/Logs/DynDOLOD_EnderalSE_Tree_Report.txt` and skips its own output mod.

## Why distant trees look black (2026-10-31)

Measured over the opaque pixels of all 502 TexGen tree billboards: median brightness **48/255**, Scots pines and
Golden Forest pines **19–22**. TexGen does not darken them: the source leaf textures (ETATU's 2x upscales) are as dark
(`scotspinebranch_multi.dds` 19/255, `nehrimeseaspenbranch01.dds` 35, `whispertreebranch.dds` 43). The full trees get
the game's foliage lighting; as LOD cards they are multiplied again by DynDOLOD's billboard vertex colour
(`FlatLODWithNormalMapVertexColor = 0.50`, `FlatLODVertexColor = 0.55` in `DynDOLOD_ENDERALSE.ini`), so pines read as
black. Seen from straight above (free camera over unloaded cells), every billboard is an X of two planes. The levers are
DynDOLOD's billboard Brightness (applied when it builds the atlas) and those two vertex colours. They are taste
settings, to be judged from the ground.

## Every remaining tree in 3D: `tools/02` (2026-10-31)

After `tools/01`, the Vyn LODGen export (`Export/LODGen_EnderalSE_Export_Vyn.txt`, LOD4 column) still drew **8,590 of
28,605 trees (30%) as billboards**, in 83 types. The largest groups were Reach tree 656, Reach cliff trees 891, tropical
dead trees 1,359, iced aspens 1,739, Golden Forest Scots pines 949, plus palms, kapoks, ficus, cypress fall versions,
rhododendrons and crystal trees. Nobody ships 3D LOD for these (checked: Arboreal Revived and Seasonal Aspen Trees of
Enderal are installed; Fabled Forests replaces the forests).

**How a 3D tree LOD model is made, read off Arboreal's:** it is the full tree's static shapes, unchanged: same
vertices, same `BSLightingShaderProperty` flags (`Tree_Anim` included), same textures. They sit under a `BSFadeNode`
root (`Tree_LOD`), with collision, `BSXFlags`, animation and skinning removed (dyndolod.info *3D Tree LOD Model*:
"all tree animation and collision removed", "Skinned shapes are not supported"; `passthru` keeps the shader).
Enderal's animated trees (`BSTreeNode`: iced aspens, Scots pines, crystal trees, King's tree) carry **a static copy of
every part next to the skinned one**. Arboreal's Scots pine is exactly those five static shapes, vertex for vertex, so
nothing needs unskinning.

`tools/02` does that for every TREE that draws a billboard in the latest Tree Report and has no 3D model in any other
installed mod. It works from the full model with the CRC32 DynDOLOD reported (the original, not PG Patcher's copy;
PG's `_pgpatcher_dups` Reach tree 02 has a multi-layer-parallax shader (type 11), so it is built from the original
path when the static shapes are identical). It keeps Default/Glow shaders only and refuses rotated intermediate
nodes. SSE stays SSE, LE stays LE. Each output is re-read and must contain exactly the source's static shapes;
`--selftest` rebuilds Arboreal's own Nehrimese aspen model from the 2.0 mesh and matches it vertex for vertex.

First run: **85 models, 0 refused, 7.8 MB**, covering all 83 billboard types placed in Vyn (plus a few placed
elsewhere). Tree records whose report header carries a display name (`"Orange Tree"`) were missed by both tools'
pattern until it allowed the quoted name. `tools/01` now judges by what is installed rather than by the report's "not
found", since after a DynDOLOD run its own models show as found.

Cost: LOD4 draws about 43% more 3D trees than before (28,605 instead of 20,015). LOD8/16 stay billboards for every tree
(the tree rule's Billboard4), as with Arboreal's.

**Result, DynDOLOD 2026-10-31 18:16:** Vyn's LOD4 now draws **28,628 trees in 3D and 4 as billboards** (from 8,590 /
30%). The 4 are single refs (`071C54`, `071C59`, `071C5E`, `071C7D`: two Enderalean cypresses and the companion tree)
whose bases are 3D everywhere else. LODGen `Code: 0` in all five worlds. **Verified in game the same day** (curator): the trees look right; some 3D trees
are a little dark, left as is (`CrownBrightness`/`TrunkBrightness` 0.7 in `DynDOLOD_ENDERALSE.ini` is the knob, then
rerun DynDOLOD only).
