# WhisperwoodFootsteps

- **Source:** `src/WhisperwoodFootsteps/` (generated: `tools/01-build-whisperwood-footsteps.py`)
- **Ships:** `Zenderal - Whisperwood Footsteps.esp` (ESL, HEDR 1.7, 2 overrides, masters only Skyrim.esm), inside
  `Zenderal - Patch Collection`
- **FormID block:** none
- **Pillar:** bug fixes

## Why

Player report (Discord, GreaseLord, 2026-11-03, still occurring 2026-11-06): in the Whisperwood the player's
footsteps can be heard on roads and rocks, not on the soil.

**[verified in the 2.1 decompile]** Landscape footsteps come from the landscape texture's material (LTEX
`MaterialType`), looked up in the footstep impact sets. Whisperwood's soil (Pilzwald region `00703D`, cells
-26..-16 x -3..7) is mostly `_00E_PilzwaldDirt 016680` (29% of the ground) and `_00E_PilzwaldDirt_Fern 02142D` (7%),
and SureAI gave both **`MaterialOrganicLarge 0D309F`**, the material for flesh and large creatures. None of base
Enderal's 18 `FST*ImpactSet`s and none of Audio Overhaul's 21 maps that material, so the soil is silent **in stock
Enderal too**; weapon and spell impacts on it use the flesh entries that OrganicLarge does have. Roads and rocks use
`MaterialStone 012F34` / `MaterialDirt 012F38`, which are mapped. These are the only two LTEX with that material in
Enderal, and no plugin in the list overrides them (scan 2026-11-08).

## What it does

Both records are base Enderal 2.1's verbatim with `MaterialType` → `MaterialDirt 012F38`, the material of the
region's other dirt (`LReachDirt01`, `LPineForest01/02`, `LDirt01`). Texture, grass, friction and specular untouched;
LOD and the ground's look are unaffected.

## Status

Built, round-trip identical, deployed into `Zenderal - Patch Collection` and enabled in Ultra 2026-11-08 (any
position; nothing else touches the two records). Unverified in game.
