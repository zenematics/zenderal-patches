# ArkWallCurbFix

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/ArkWallCurbFix/`
- **Ships:** *(no plugin — Enderal's original meshes, MO2 mod `Zenderal - Ark Wall Curb Fix`)*
- **FormID block:** _(none)_

## What it does

**The curb along Ark's walls smeared into streaks that slid with the camera, ENB on or off** (reported 2026-10-11 at `_00E_Ark_1024WallGate02 041448`, Myrad Tower, Ark's Western Wall). Enderal's Ark wall meshes use no parallax; SRP Enderal - Architecture switched every shape to parallax (type 0→3, flags1 bit 11) with geometry/UVs/diffuse paths byte-identical. **Verified in game:** Enderal's ORIGINAL `1024wallgate02.nif` fixed it. Narrower attempts did NOT: un-parallaxing only `brick02`, and only the `border02` trim — the latter *looked* fixed once, but that screenshot came from a game session started before the file was swapped, so it was still showing the original mesh (cost several rounds; **always confirm the game process started after the file write** — `Get-Process SkyrimSE | Select StartTime`). `src/ArkWallCurbFix/tools/01-restore-enderal-wall-meshes.py` extracts Enderal's original mesh from `E - Meshes.bsa`/`E - Update.bsa` for every winning SRP mesh with a parallax `border02` shape (`EXPECTED_MESHES = 36`: Ark 256/512/1024/1536 walls, towers, gates, ledges, ramp, slope + one Wintercastle wall); SRP's textures still apply. Not committed. Sorts above SRP Architecture. Profile state when verified: `Missing Parallax Heights` ON, `Terrain Parallax Heights` OFF. Lesson: **a console click names the whole REFR, not the shape** — compare against the game's original mesh first.
