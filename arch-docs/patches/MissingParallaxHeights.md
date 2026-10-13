# MissingParallaxHeights

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/MissingParallaxHeights/`
- **Ships:** *(no plugin — loose textures, MO2 mod `Zenderal - Missing Parallax Heights`)*
- **FormID block:** _(none)_

## What it does

**Parallax meshes whose height map does not exist render "floating"** — the texture slides over the mesh as the camera moves (reported 2026-10-11 on the curb of `_00E_Ark_1024WallGate02`, SRP's `1024wallgate02.nif` → `enderal/architecture/ancientruins/blocks_p.dds`, which exists nowhere). The game substitutes white for a missing `_p`; Auto Parallax (loaded, `AutoParallax.log` present) is supposed to disable parallax then but evidently does not under ENB complex parallax. `src/MissingParallaxHeights/tools/01-flat-heights.py` scans every winning loose mesh for shader type 3 (`BSLightingShaderProperty`) and resolves slot 3 against loose mods + every game BSA: **1017 meshes / 1805 shapes referencing 289 missing `_p`, ~90% SRP Enderal Architecture/Dungeons**. Writes a 4×4 uncompressed mid-grey (128, ENB's "flat, no shift") DDS with mips at each path — adds files only. Asserts `EXPECTED = 289`; re-run after mesh-mod changes, then rebuild CRDW. Sorts at the top of the left pane (no file conflicts by construction). Built 2026-10-11. Its role in the Ark curb is **unclear**: the curb result attributed to it came from a stale game session (see `ArkWallCurbFix`); it was enabled when the original-mesh fix was verified, so it is kept enabled.
