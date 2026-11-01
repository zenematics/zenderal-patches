# NoCrystalBases

- **Source:** `src/NoCrystalBases/` (generated: `tools/01-build-no-crystal-bases.py`)
- **Ships:** `Zenderal - No Crystal Bases.esp` (ESL, HEDR 1.7, 4 overrides)
- **FormID block:** none
- **Pillar:** curator's taste (a look test for now)

## What it does

The flat, pale ground pieces under Enderal's crystal clusters (Crystal Forest and elsewhere) are their own statics:

| Static | Mesh |
|---|---|
| `_00E_CrystalArcane_Base 0FA16A` | `Enderal\Dungeons\crystals\crystalbase01pink.nif` |
| `_00E_CrystalRed_Base 0FA16B` | `...\crystalbase01red.nif` |
| `_00E_CrystalGreen_Base 0824B8` | `...\crystalbase01green.nif` |
| `_00E_CrystalBlue_Base 0824B9` | `...\crystalbase01blue.nif` |

All four are base Enderal's (`Skyrim.esm`), and no list plugin overrides them (scan 2026-10-26; the console showed
"Base last changed by Skyrim.esm"). Each override is Enderal's record verbatim with the model set to
`Effects\FXEmptyObject.nif` (an empty mesh in `Skyrim - Meshes0.bsa`) and its texture-hash `Data` removed, so every
placed base disappears, collision included, without editing any placed reference. The crystals are separate statics
and stay.

Distant object LOD (DynDOLOD) may still show the bases far away until DynDOLOD is rerun.

## Load order

Ultra: `plugins.txt` right after `Zenderal - Bloody Crit Sound.esp`; mod after `Zenderal - Level Up Sound`. Undo:
untick the plugin (profile backups in `E:/Zenderal-backups/2026-10-26-no-crystal-bases/`).

## Status

Built and enabled 2026-10-26 for the curator's look test, then **reverted the same day at the curator's request**:
removed from the Ultra profile, MO2 mod folder moved to `E:/Zenderal-backups/2026-10-26-no-crystal-bases/removed-mod/`.
Not shipped (no manifest entry). The source stays here in case the look is wanted later.
