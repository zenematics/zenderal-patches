# SPRPBRTweaks

- **Source:** `src/SPRPBRTweaks/` (generated: `tools/01-build-spr-pbr-tweaks.py`)
- **Ships:** *(no plugin — 8 generated PGPatcher JSONs, MO2 mod `Zenderal - SPR PBR Tweaks`, not committed)*
- **FormID block:** _(none)_

## What it does

Lowers PBR parallax on SPR PBR's (Enderal Nexus 1063) **Duenenhaim** (desert town) textures from
`displacement_scale` 1 to **0.3**: `loamwall01/02`, `sandplaster01`, `sandstone`, `sandstone01`,
`southbasewall`, `wrwoodplaster01`, `riftencanalwood01`.

**Why [verified 2026-10-24 from the user's video]:** after SPR PBR was installed and PGPatcher rerun, the Old
Ishmorlep tower `_00E_SandOldCityTower02 0607D1` (`SandOldCityTower02.nif`, PG Patcher Output's copy now on
`textures\pbr\...\duenenhaim\loamwall01`) showed fur-like streaks at grazing angles. SPR PBR's `loamwall01_p`
is SRP's 2022 height map unchanged: mostly flat bright with dark speckle, which full-strength PBR displacement
drags into hairs. Not known whether SRP's own (weaker, non-PBR) parallax showed it before.

Each JSON is SPR PBR's own, copied to the same `PBRNifPatcher/` path with only `displacement_scale` changed, so
SPR PBR's files are untouched and MO2's priority hands PGPatcher the override.

**v1.1 (2026-10-24, second video at 23:56): 0.3 was not enough on the tower, so `loamwall01/02` get PBR
parallax off** (`parallax` false, displacement 0; PBR roughness/normal kept). The tower is Skyrim's
Markarth dwarf tower (`MarkarthDwarfTower01City:*` shapes): measured per-triangle UV stretch shows shapes
`:56` and `:59` with ~14% of their area stretched more than 3× (median 1.2–1.8 elsewhere), plus mirrored UVs
on the top of the base block (the herringbone moss). Displacement on stretched UVs smears into streaks; the
stretch itself is SureAI's/Bethesda's mapping and stays.

## Load order

Sort **above** `SPR PBR - Architecture Dungeons Misc`, then rerun PGPatcher. `--scale S` changes the value
(0 = flat PBR, no depth). Rerun `tools/01` if SPR PBR updates.

## Status

Generated 2026-10-24. Unverified in game.
