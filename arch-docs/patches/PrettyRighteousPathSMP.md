# PrettyRighteousPathSMP

- **Source:** `src/PrettyRighteousPathSMP/` (generated: `tools/01-build-smp-meshes.py`; physics `assets/ZenRighteousPathFlaps.xml`)
- **Ships:** *(no plugin — 8 generated meshes + 1 SMP XML, MO2 mod `Zenderal - Pretty Righteous Path SMP`)*
- **FormID block:** _(none)_

## What it does

Curator's request (2026-10-26): **the front and rear tabard flaps of Pretty Righteous Path Armory's cuirass swing
with Faster HDT-SMP** instead of staying glued to the pelvis.

The cuirass is ARMA `03E_24_CuirassOfTheRighteousPathAA 05B69C:Skyrim.esm` → `armor\ebony\{m,f}\cuirass_1.nif`
(+ `_0`). **[verified 2026-10-26]** on Pretty 2.0's four meshes (male and female have the same layout):

| Shape | Skirt bones | Notes |
|---|---|---|
| `SkirtB` (the flaps, 50 verts) | `SkirtFBone02/03`, `SkirtBBone02/03`, rigid (weight 1.0) | top half (z 57–64) on `02`, bottom half (z 32–50) on `03` |
| `Skirt` (belt/fauld) | `SkirtF/L/RBone01`, **`SkirtBBone02`** (18 verts, z 59–65) | the back belt plate rides the rear flap's top bone |
| `Cuirass` | `SkirtF/L/RBone01` | |
| `Greaves` | `SkirtBBone01` + legs | used as the flaps' collider |

**Two variants, two mesh sets [verified 2026-10-26]:**

| Armor | Winning ARMO → ARMA | Meshes | Tabard |
|---|---|---|---|
| Righteous Path `0907AD`, Forged `13C54B` | → `05B69C:Skyrim.esm` | `armor\ebony\{f,m}\cuirass_{0,1}.nif`, loose in Pretty Righteous Path Armory | red `skirtB_d` |
| Righteous Keeper `0365C7` | Pretty Armory EGO Patch (Semi-Unique merge) → `000817:Pretty Semi-Unique Armory.esp` (`03E_24_CuirassOfTheRighteousPath_alt_AA`) | `armor\ebony\alt\{f,m}\cuirass_{0,1}.nif`, inside `Pretty Semi-Unique Armory.bsa` | black `skirtB_alt_d` |

The `alt` meshes are the same model and rig with `_alt` textures, so one XML serves all eight. The first build
only covered the red set; the Keeper's black tabard didn't move until the `alt` set was added. The generator reads
the BSA with `tools/bsa.py` (SSE v105, LZ4), since `bsab` is not installed at `tools.json`'s path on this machine.

So the author had already rigged the flaps to XPMSE's skirt chains; nothing simulated them. The generator
appends one `NiStringExtraData` "HDT Skinned Mesh Physics Object" = `Meshes\armor\ebony\ZenRighteousPathFlaps.xml`
to each scene root (new block last, every other byte kept; shapes re-read identical in PyNifly).

## The physics

- `SkirtFBone01`/`SkirtBBone01` and the legs stay kinematic; `F/B 02` and `F/B 03` are dynamic.
- XPMSE 4.80's skirt bones (male and female skeleton identical): `F01` z 74.6 → `F02` 61.7 → `F03` 48.8;
  `B01` 77.9 → `B02` 65.1 → `B03` 52.3. **`02` sits at the flap's top edge and `03` at mid-flap**, so each
  constraint is framed at **bodyA** (`frameInA` identity: the child's own origin). With the usual `frameInB` the
  flap would orbit the bone above (the belt, 11 units higher) and its top edge would leave the belt.
- Bone local axes: X lateral (fore/aft swing), Y forward (side swing), Z along the flap. Limits: `02` ±0.3 rad
  fore/aft, `03` ±0.4; side ±0.08/±0.12; twist ±0.03. Angular springs pull back to rest.
- Collision: `SkirtB` (per-triangle) against `Greaves` (per-triangle) minus its pelvis/spine/foot-weighted
  triangles (1664 of 1744 kept). Rest clearance flap→collider ≥ 2.54 units, against 0.6 of combined margin, so
  nothing starts interpenetrated.
- Side effect: the back belt plate (on `SkirtBBone02`) tilts slightly with the rear flap. It sits within 6 units
  of the pivot, so the movement is small; reweighting it to `SkirtBBone01` would need a full NIF rewrite.

## Load order

**The SMP mod must outrank BOTH Pretty Righteous Path Armory and Enderal Remastered Armory Part 1**: all three ship
`armor\ebony\{f,m}\cuirass_{0,1}.nif`. ERA's is a different model (front tassets only, no rear flap), the same
ERA-over-Pretty collision as [`MoonsteelPretty`](MoonsteelPretty.md)'s arrows. On 2026-10-26 the curator moved
Pretty above ERA; the SMP mod was left below both, and the first in-game test showed Pretty's flaps with no physics.
Order needed (MO2 left pane, top to bottom = low to high priority): ERA Part 1 → Pretty Righteous Path Armory →
`Zenderal - Pretty Righteous Path SMP`. Since 2026-10-27 ERA's remaster is its own set,
[`KnightOfThePath`](KnightOfThePath.md), and this order is set in the Ultra profile. The Keeper's `alt` meshes have no loose competitor (Semi-Unique ships them
in its BSA, which any loose file beats), so they work at any position.

## Status

Red set verified in game by the curator (2026-10-26, after sorting it above Pretty). Keeper (`alt`) set built,
**unverified in game**. Rerun `tools/01` after a Pretty Righteous Path or Semi-Unique update; it refuses a mesh whose flap shape is not on
exactly the four skirt bones, or that already has an SMP hook.
