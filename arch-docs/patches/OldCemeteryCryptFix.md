# OldCemeteryCryptFix

- **Source:** `src/OldCemeteryCryptFix/` (generated: `tools/01-build-old-cemetery-crypt-fix.py`)
- **Ships:** `Zenderal - Old Cemetery Crypt Fix.esp` (ESL, HEDR 1.7)
- **FormID block:** none (one override)
- **Status:** built, round-trip clean; **verified in game 2026-10-19** (Ultra profile: the house is back behind the crypt door)

## The bug

Reported 2026-10-19 on Discord as "Old Cemetery Crypt Missing Texture". Outside the Old Cemetery Crypt
(interior `Friedhofsgruft 01CB58`) the door stands by itself on the paving with nothing around it.
The dead stone gargoyle there floated in mid-air.

The door is `01D188:Skyrim.esm` (`SHouseDoor02`, persistent, Vyn). Its building is the house shell
`016A98:Skyrim.esm` in exterior cell `Friedhof 001FF8` (grid −7,−6). Its base is `SStyrrsHouse 037F05`
and its scale is 1.09. The gargoyle was perched on that house's roof.

`Enderal TAT CM Fixes.esp` (ETATU - Complex Material Addon, Enderal Nexus 811, the "Save compatible"
plugin, 0.92a) overrides `016A98` and changes only its base, to its own static `0039C5`
`SStyrrsHouse ark`. That static's model is `Architecture\Solitude\SStyrrsHouse ark.nif`, and the mesh
is in no mod folder and no BSA of the install. "ETATU - CM Meshes" ships other `* ark.nif` variants
(`cwtower01 ark`, `sfarmhousesilo ark`), but not this one. A static whose mesh is missing renders
nothing and logs no error.

A binary scan of the `Ultra` profile found these overrides, in load order:

- `016A98`: only ETATU.
- Cell `001FF8`: FS, `GargoylesInEnderal.esp`, then ETATU.
- WRLD `Vyn`: ~80 plugins, won by `DynDOLOD.esp`.

The other ref there is the door frame `01D189` (`SDoorFrameExterior01`), placed pitched 90°. It is
not the cause: SRP Enderal - Architecture's mesh only adds parallax to Enderal's original
(`Skyrim - Meshes0.bsa`), and the geometry is identical.

Four more ETATU statics point at meshes that aren't installed. Three are DynDOLOD LOD
models (`0039C1`–`0039C4`) and one is the Silvercloud sign `074550`. None of those were traced.

## The fix

The script copies ETATU's override of `016A98` verbatim and sets `Base` back to `037F05:Skyrim.esm`.
ETATU's position, rotation, scale and VisibleWhenDistant flag stay as they are. The cell header, the
Vyn header and the block/sub-block scaffolding are also copied verbatim from ETATU, which is the last
overrider of the cell. Vyn's WRLD record is won by DynDOLOD.esp regardless.

Masters: Skyrim, Update, FS, `Enderal TAT CM Fixes.esp`. No record references ETATU; the master is
there only to force the patch to load after it. Place it after ETATU CM Fixes and before
`Occlusion.esp` / `DynDOLOD.esp`.

It is a plugin record, not save state, so the house should come back on an existing save the next
time the cell loads.

## Regenerating

Re-serialize `Enderal TAT CM Fixes.esp` → `reference/mods/ETATUCMFixes`, then run
`python src/OldCemeteryCryptFix/tools/01-build-old-cemetery-crypt-fix.py`. The script refuses to
build if ETATU's cell no longer holds exactly `016A98` on base `0039C5`. Retire the patch if ETATU
starts shipping the mesh or drops the re-base. Check 0.93.0 when the list updates it.
