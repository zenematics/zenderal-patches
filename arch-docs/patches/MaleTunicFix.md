# MaleTunicFix

- **Source:** `src/MaleTunicFix/` (generated: `tools/01-build-male-tunic-fix.py`)
- **Ships:** `Zenderal - Male Tunic Fix.esp` (ESL, HEDR 1.7). Masters Skyrim, Update, FS and `Pretty Enderal Clothing.esp`.
  The live copy is in `Zenderal - Patch Collection`. **Must load after `Pretty Enderal Clothing.esp`.**
- **FormID block:** none (one override)
- **Owns:** armor addon `_00E_Mining_FineClothesF_Green_AA 138036:Skyrim.esm`
- **Status:** built and round-trip clean 2026-11-07, deployed. Unverified in game.

## Why

Player report (cptflame, 2026-11-07): in Forgotten Homeland Part 1, when the airship starts, a male character is put
in a "female" tunic.

- **The quest:** SureAI's `_00E_MQ13a_Functions` (lines 321 and 474) undresses the player and equips
  `_00E_Mining_FineClothesF_GreenA 13803C` ("Tunic") and `ClothesJarlShoes`, whatever the player's sex.
- **Base Enderal:** the tunic's addon `138036` gives men plain miner's clothes
  (`Clothes\MinerClothes\MinerClothesm_1.nif`, first person `1stPersonMinerClothesm_1.nif`, both in
  `Skyrim - Meshes0.bsa`).
- **Pretty Enderal Clothing** (the only overrider, so it wins) points both sexes at Kilean's Dancer outfit: men
  `Enderal\Clothes\Kilean\Dancer\Green_m_1.nif`, women `Green_1.nif`. The male mesh exists, but it is a dancer's
  costume and reads as women's clothing on a man.

## The fix

Pretty's `138036` verbatim, with only the male world and first-person models back to base Enderal's. The generator
asserts that Pretty's male paths are the Dancer ones and base's are the miner ones. Women keep Pretty's dancer tunic.
The item record `13803C` is untouched; Pretty's ground model stays.

Pretty's two other Dancer colours (white, lavender) are left alone: they are not forced on the player.

## Upkeep

After a Pretty Enderal Clothing update, re-serialize it into `reference/mods/Pretty/Pretty Enderal Clothing` and rerun
`python -I src/MaleTunicFix/tools/01-build-male-tunic-fix.py`.

## To verify in game

On a male character, reach the airship scene in Forgotten Homeland Part 1, or test from the console:
`player.equipitem 0013803C` (the item is in `Skyrim.esm`, so its prefix is `00`). Both third and first person should
show the miner tunic, not the dancer's outfit.
