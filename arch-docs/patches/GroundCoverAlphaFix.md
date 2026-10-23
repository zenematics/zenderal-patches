# GroundCoverAlphaFix

- **Source:** `src/GroundCoverAlphaFix/` (generated: `tools/01-raise-groundcover-alpha-threshold.py`)
- **Ships:** *(no plugin — two generated meshes, MO2 mod `Zenderal - Ground Cover Alpha Fix`)*
- **FormID block:** _(none)_

## What it does

**Tropical ground cover no longer draws as flat light-green squares** (reported on the old 2.0 release, with
screenshots of the Starling city in the sky, 2026-10-23). The squares are `_00E_TropicalTree_GroundCover01
088CF2` (`prid` of ref `1350CF`) and its sibling `GroundCover02`: flat cards of leaves cut out by alpha test.

**[verified 2026-10-23 on the Ultra profile]**

- Both meshes, Enderal's in `E - Meshes.bsa` and Fixed Mesh Lighting's winning loose copy, are identical
  where it matters: one shape `palmtree1:1`, `NiAlphaProperty` flags `0x12EC` (test on, function
  *greater*, no blend), **threshold 0**. Every texel with alpha above 0 is drawn.
- Enderal's `coverground01/02.dds` (in `E - Textures2.bsa`) have a clean background: 55.9% / 56.9% of
  texels at alpha 0, only 0.7% / 1.1% at alpha 1–15.
- **ETATU - Plants Leaves Grass Upscaled 2x** replaces both with 2048² BC7 upscales whose background came
  out at alpha 1–15: 42.4% / 40.4% of texels, with only 15.1% / 18.9% left at 0. With threshold 0 the whole
  card is drawn in the light green under the alpha.
- 66 of ETATU's 267 alpha textures have the same faint background, but a scan of all 30,883 winning meshes
  (loose by MO2 priority, then Enderal's and Skyrim's mesh BSAs) found only these two meshes using one with
  an alpha-test threshold under 16. Two DynDOLOD tree LOD meshes didn't parse, but they use their own
  atlases, not these textures.

`tools/01` copies Fixed Mesh Lighting's `groundcover01.nif` and `groundcover02.nif` and sets the one alpha
property's threshold to **128**, the usual foliage cutoff. It asserts one alpha property, test on, threshold 0,
and changes that byte only: `cmp` against the source shows one byte per file. ETATU's sharper texture is
kept. The meshes are generated from the install, not committed.

The mod must have **higher MO2 priority than Fixed Mesh Lighting**; it sits directly above it in Ultra. Rerun
`tools/01` if Fixed Mesh Lighting updates these meshes. Retire it if ETATU fixes the alpha. Persists on
Enderal 2.1: same meshes and textures. **Checked in game 2026-10-23 with the mod enabled:** no squares
seen flying around Star City. Not compared against a run with the mod disabled.

## The alternative not taken

Putting Enderal's two original textures back above ETATU also fixes it, but loses the upscale on these two.
