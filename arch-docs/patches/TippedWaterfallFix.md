# TippedWaterfallFix

- **Source:** `src/TippedWaterfallFix/` (generated: `tools/01-build-tipped-waterfall-fix.py`, which also writes the mesh
  into the MO2 mod when given its folder)
- **Ships:** `Zenderal - Tipped Waterfall Fix.esp` (ESL) plus `meshes\effects\zenderal\fxwaterfallthin256x128flat.nif`,
  Enderal's own mesh from `E - Meshes.bsa` (not committed). MO2 mod `Zenderal - Tipped Waterfall Fix`.
- **FormID block:** `0x800` (MSTT `ZEN_FXWaterfallThin256x128Flat`)
- **Pillar:** bug fixes / visuals

## Why

The curator reported water "defying gravity" over the mill-dam walls at the MQ01 campsite (cell `MQ01Campsite 015D43`,
cell −27, 1, near Finn and Carbos), shown in their screenshots as a white sheet sprayed out sideways from the wall top.

SureAI built that stream from the thin waterfall `FXWaterfallThin256x128 1033F2:Skyrim.esm`
(`Effects\FXWaterfallThin256x128.nif`) laid on its side: refs `072D1D` (X rotation −1.46), `072D1E` (+1.46) and
`072D1F` (Y 1.44). Tipped about 84 degrees, the falling sheet reads as flowing water. **Water for ENB - Particle
Waterfalls** replaces that mesh with a particle emitter. The emitter sprays along the mesh's own down axis, which points
sideways once the mesh is tipped.

The first guess, the flat water planes `Water1024` (`072CD8`/`072CD9`/`072CF1`, z 2475, base retyped by Water for
Enderal CS), was the wrong water.

## What it does

- MSTT `0x800`: `1033F2` verbatim, with a new EditorID and the model path `Effects\Zenderal\FXWaterfallThin256x128Flat.nif`.
- The three refs, verbatim from Skyrim.esm with `Base` repointed. The generator refuses any ref that isn't tipped by more
  than 1 radian.
- Cell header forwarded from Skyrim.esm. Its only other overrider, `DynDOLOD.esm`, has a byte-identical header
  (binary load-order scan, 2026-10-31). No list plugin overrides the refs or `1033F2`.
- WRLD header from Skyrim.esm. **Load before `DynDOLOD.esp`**, so that DynDOLOD's, Occlusion's and Vyn Full Extend's
  WRLD still win.

The particle waterfalls stay everywhere else. About 50 more `1033F2` refs across Vyn are tipped more than 20 degrees;
if another spot sprays sideways, add its refs the same way.

## Status

Built and installed 2026-10-31 as the MO2 mod `Zenderal - Tipped Waterfall Fix`. **Verified in game 2026-10-31**
(curator).
