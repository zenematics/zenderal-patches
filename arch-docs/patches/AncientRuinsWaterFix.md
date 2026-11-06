# AncientRuinsWaterFix

- **Source:** `src/AncientRuinsWaterFix/` (generated: `tools/01-build-ancient-ruins-water-fix.py`)
- **Ships:** `Zenderal - Ancient Ruins Water Fix.esp` (ESL, HEDR 1.7). The live copy is in `Zenderal - Patch
  Collection`, loaded right after the Dark Valley Sun Fix.
- **FormID block:** none (overrides only). `0x800` was build 3's activator `ZEN_Water1024DefaultWater`: **retired, never reuse**
- **Owns:** cell `001460:Myths and Legends VI - The Forgotten One.esp` (header, verbatim), its pond plane `022487`, the
  15 lily pads on it, the 6 shore-foam strips at its edge, the 9 sponges `0F8F8C` and the courtyard's 8 mist effects
  (all the mod's references)
- **Status:** build 6 deployed 2026-11-06. **Verified in game** the same day: mist walls gone, and with the pond and
  lily pads back as the mod has them the courtyard "looks right" (curator). The mist was the real culprit; the water
  looked bad only under it.
- **Disables now:** the 7 mist beams, the low mist `022384`, the 9 sponges and the 6 shore-foam strips (23 refs). The
  pond plane `022487` and its 15 lily pads are the mod's again (the generator's `DISABLE` tuple).

## Why

Player reports (Longinus, confirmed by GreaseLord, 2026-11-06): *"Ancient Ruins looks horrible, probably water
texture overlapping"*. A dark, washed-out sheet lies across the ruins' courtyard, with hard straight edges.

"Ancient Ruins" is the interior cell `aaaeew 001460` that **Myths and Legends VI - The Forgotten One** adds, the
level-50 Forgotten One's lair. All 827 of its records (cell, navmesh, every placed object) are the mod's, and no other
plugin in the list edits any of them (load-order scan 2026-11-06).

The courtyard is a shallow flooded pond: placed water plane `022487`, base `Water1024 03AC83`, at height 56.42 and
scale 2.97 (about 3,040 units square; `Water1024.nif` is ±512), with 15 lily pads on its surface. The walkable floor
under it lies 0–32 units below the surface. The mod built it on `Water1024` → **`DefaultWater 000018`**.

**Water for Enderal CS changes it.** It overrides `Water1024 03AC83` (every placement in the list) to use
**`DefaultIntWaterWaistHeightStill 0CC7B4`**: near-black water (shallow and deep colour both `#040709`), heavy fog
above it (amount 0.7, far plane 600), full fog under it. Over a shallow courtyard that renders as a dark, fogged
sheet with hard edges, which the mod never had (the curator: "the normal mod doesn't look like that").

## The fix (build 5)

The pond set-dressing and the courtyard's mist are disabled the xEdit way (`InitiallyDisabled`, enable parent
PlayerRef set opposite, z −30000; the persistent plane keeps its `0x400` flag):

- the plane `022487`, the 15 lily pads floating on it (those at its height 56.42), the 6 `NicoWave01–05` shore-foam
  strips at the same height round its edge (`02237E`–`022383`) and the 9 sponges;
- the 7 `FXAmbBeamWetMistBig02` mist beams (`0777B2`, scale 2.22, hanging from 2,454) and the low
  `FXMistLowWet01` `022384` (scale 3.22, at 35.8) over the courtyard floor.

Everything else in the cell stays the mod's, including the water and mist pieces in the side areas (all at 1,500+).
The generator asserts 1 + 15 + 9 + 6 + 8 and that none was already disabled.

**Why the mist (curator 2026-11-06: "these white mist walls"):** **Particle Patch** (busybobo, Nexus 65720, 1.4.4)
replaces both mist meshes. Against Skyrim's originals it doubles the emissive multiplier (1.0 → 2.0) on every mist
layer, turns off the greyscale-to-palette colour/alpha flags on the beam's layers, and adds one flag on the low mist.
Its page says the mist "now respond[s] to [PARTICLE] settings": it is tuned for ENB's particle lighting, which
Steamin's `enbseries.ini` sets (`LightingInfluence`/`AmbientInfluence` 0.5). This list runs Steamin through Bottled
Shaders' Effects 11 layer, which most likely does not apply ENB's particle lighting (not verified in its code), so the
mist draws at double brightness, untinted: white walls in this dark interior. Particle Patch supports Community Shaders
per its page and stays; the fix is this cell only, at the curator's choice. If white mist walls show up elsewhere,
the list-wide option is Skyrim's originals of these two meshes in a mod sorted above Particle Patch.

## Dead ends (kept as lessons)

- **Build 1** removed the cell's own `HasWater` flag (water at height 0, no type). That water lies below every navmesh
  vertex (lowest 24.5) and was not what players saw; no visible change.
- **Build 2** shrank and re-centred the plane on its lily pads (2.97 → 2.17). The low floor runs past any square, so
  the edges still cut it.
- **Build 3** pointed the plane at a new activator with `DefaultWater` instead of Water for Enderal's dark interior
  type. The water got lighter, but the curator's screenshot still showed a flat pale sheet with hard straight edges:
  a 3,000-unit square a few units over a stone floor shows its boundary whatever the water type. Water for Enderal's
  retyping of `Water1024` (every placement in the list) is still real and worth knowing for other cells.

## The black sponges

Enderal's sea-floor plant `_00E_Underwater_Fingersponge02` (`0F8F8C`, a TREE record), 9 refs rooted at height −23
through the floor. They were black at a distance and vanished up close, also with the water system off (`tws`). No
plugin edits the TREE; the winning mesh (Enderal - Fixed Mesh Lighting) shades identically to Enderal's, and ETATU's 2×
BC7 texture is normal at every mipmap level. The render cause is not found; they are disabled with the pond, since
they only make sense under water.

## Upkeep

After a Myths and Legends VI update, re-serialize it into `reference/mods/MythsAndLegendsVI`, check the cell's overriders, and rerun
`python -I src/AncientRuinsWaterFix/tools/01-build-ancient-ruins-water-fix.py`.

## To verify in game

`coc aaaeew`, walk to the courtyard: dry stone, no water sheet or straight edges, no lily pads, no white foam strips,
no black shapes, no white mist walls. The courtyard without the plane, lilies and sponges was confirmed in game
2026-11-06 (curator's screenshot); the foam strips and mist were removed after it.
