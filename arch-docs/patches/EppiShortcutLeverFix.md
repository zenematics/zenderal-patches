# EppiShortcutLeverFix

- **Source:** `src/EppiShortcutLeverFix/` (generated: `tools/01-build-eppi-shortcut-lever-fix.py`)
- **Ships:** `Zenderal - EPPI Shortcut Lever Fix.esp` (ESL, HEDR 1.7). Masters Skyrim, Update, FS,
  `EPPIareadividerandconnectors.esp` and `Water for Enderal CS.esp`. The live copy is in `Zenderal - Patch Collection`.
  **Load after `Zenderal - Last Watch Trapdoor Fix.esp`, before `DynDOLOD.esp`** (it carries the Vyn persistent cell's
  header).
- **FormID block:** none (one override)
- **Owns:** the pull bar `0093EC:EPPIareadividerandconnectors.esp` (persistent, in Vyn's persistent cell)
- **Status:** built and round-trip clean 2026-11-08, deployed and enabled in Ultra (after Last Watch Trapdoor Fix).
  Unverified in game.

## Why

Player report (GreaseLord, 2026-11-06): "you can open old dams water house from beyond the gate".

- **The gate is EPPI's, not base Enderal's.** *EPPI Obstacles and Shortcuts* (`EPPIareadividerandconnectors.esp`)
  closes a short Nordic hall in Vyn cell (−27, 3), on the west coast north of the Sun Coast:
  - `NorHallSm1wayEndExSm01` ×2 (`0093E6`/`0093E7`), platforms (`0093ED`/`0093EE`), shaft beams (`0093EA`/`0093EB`);
  - portcullis `0093E9` (`NorPortcullis`), whose activate parent is the pull bar `0093EC` (`NorPullBar01 098668`).
    *Oblivion Interaction Icons* renames that activator "Pull Bar".
- **The geometry, relative to the portcullis:**
  - the outside is east (+X): meadow, rocks, a shovel, a skull, a skeleton-archer spawn;
  - the inside is west (−X): the hall and its beams;
  - the pull bar was at dx −131, dy −77, 95 units up (wall-mounted).
- **The reach:** the engine's activation reach is `iActivatePickLength` = **150** (base Enderal; no list plugin
  overrides it). A player pressed against the bars stands about 140 from the pull bar, so it can be pulled from
  outside and the shortcut opened early.
- Only EPPI places pull bars in Vyn; its other one is elsewhere, at (−125181, 80204). No other plugin overrides this ref.

## The fix

The pull bar moved **64 units further in along the same wall**: X −109691.97 → −109756.21 (dx −195 from the
portcullis). Y, Z, rotation, scale and everything else are verbatim from EPPI.

- That puts it about 200 units from the bars, out of reach, and still in front of EPPI's shaft beam `0093EA` (dx −220,
  dy −71).
- The generator asserts that the ref is still EPPI's pull bar at the old X and that the portcullis still hangs on it.
- Headers, from each record's last overrider before DynDOLOD:
  - WRLD Vyn `001D3C` ← `Water for Enderal CS.esp` (its own LodWater `000802`, so it is mastered);
  - persistent CELL `001D40` ← `Zenderal - Last Watch Trapdoor Fix.esp` (repo YAML).

## Upkeep

After an EPPI or Water for Enderal CS update, re-serialize `reference/mods/EPPIareadividerandconnectors` and
`reference/mods/WaterForEnderalCS`, then rerun `python -I src/EppiShortcutLeverFix/tools/01-build-eppi-shortcut-lever-fix.py`.

## To verify in game

`coc` near cell (−27, 3) or walk to the gate (west coast, north of the Sun Coast):
- From outside, pressed against the portcullis: no "Pull Bar" prompt.
- From inside: the pull bar is on the same wall, slightly deeper, not floating or clipping into the beam, and it still
  opens the portcullis.

If it sits wrong, adjust `NEW_X` in the generator and rerun.
