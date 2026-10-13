# TerrainTextureSetFix

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/TerrainTextureSetFix/`
- **Ships:** `Zenderal - Terrain Texture Set Fix.esp`
- **FormID block:** none (overrides only)

## What it does

**ENB complex terrain parallax smeared ground into radial streaks** — sharp under the camera, stretched outward (reported 2026-10-11 at Frost Crystal Passage, Vyn cell -32,16, layer `_00E_Rockpath01NRIced 030FEC`). Cause: base Enderal fills the TXST **Height (TX04)** slot on only 2 of its 95 landscape texture sets, and both point at a NORMAL map — `_00E_Rockpath01Iced 030FEB` (`rockpath02_n_DXT1.dds`) and `_00E_MossRock 020F1A` (`rock_moss03_n_DXT1.dds`). ENB traces that slot as height. Override = record verbatim minus `Height`; MossRock also forwards **DynDOLOD.esp**'s `NormalOrGloss` (`rock_moss03_dxt1_n.dds`, TexGen output), so the plugin must load **after DynDOLOD.esp** (not mastered — DynDOLOD output is per-user). **Verified in game 2026-10-11 for 030FEB** (smear gone); 020F1A built, not yet seen. Three things that did NOT fix it, in order: turning off complex terrain parallax in the ENB GUI (greyed ticks = restart-only settings, the toggle never applied); regenerating height into the SRP diffuse alpha (`src/TerrainParallaxHeights/`, MO2 mod `Zenderal - Terrain Parallax Heights`, 42 textures — zero visible change, since the TXST height slot wins); and `EnableTerrainParallax=false` (basic) with complex on, now set in Steamin ENB's `enbseries.ini` in place, original in `E:/Zenderal-backups/`. Diagnostic that would have saved the day: **grep the landscape TXSTs for a `Height:` line first.**
