# ZarAhTextureFix

- **Source:** `src/ZarAhTextureFix/` (generated: `tools/01-copy-zarah-textures.py`)
- **Ships:** *(no plugin — six copied textures, MO2 mod `Zenderal - ZarAh Texture Fix`)*
- **FormID block:** _(none)_

## What it does

**Zar'Ah has her hair and scars again instead of a bald head and an offset dark-blue face plate**
(bug report with screenshot, 2026-10-21).

Zar'Ah is `_00E_FS_NQR05_ZarAh 01F1B2:Enderal - Forgotten Stories.esm`. Three plugins override her: EGO,
`Malphas' Blessing - Enderal.esp` and `MB - EGO.esp`. The last one wins, and its head parts
(`MB_HeadFemale 00083D`, hair `mbZarah 00089C`) match the winning facegen, Malphas' Blessing's
`0001F1B2.nif`, which outranks Enderal NPC Overhaul's. The record and facegen match; the bug is elsewhere.
**[verified 2026-10-21]**

The facegen bakes six texture paths under `textures\MB\F\mbZar'ah\` (with an apostrophe): the hair
`BrokenSC` and the two scar overlays `NBfacerightsidegash18` / `NBfemalefaceleftsidegash13`, each with
its `_n`. The mod ships the folder as `textures\MB\F\mbZarah\`, so none of them resolve. The scar
overlays are full-face meshes sitting just in front of the head. Untextured, they draw as an opaque
dark-blue plate, and the hair does not draw at all. Its shape names (`mbZar'ah`, `mbZar'ahHL`) show the
facegen was exported before the author renamed the head part and folder.
**[verified 2026-10-21]**

A scan of every Malphas' Blessing mesh for `textures\MB\` and `textures\0mb\` paths the mod does not
ship found only these six, also baked into `00025312.nif` (`_38E_Phasmalist_Apparation_Warrior_Tier4`,
which reuses Zar'Ah's face), plus one minor miss: `0mbBodies\Female\body\femalebody_msn.dds` in
`femalefeet_0/1.nif`.

`tools/01-copy-zarah-textures.py` reads the paths from both facegen files, asserts there are six and
that each exists under `mbZarah\`, and copies them to `textures\MB\F\mbZar'ah\` in the new mod. The
textures are the mod author's work, so they are generated from the install and not committed.
Wabbajack matches files by hash, so the copies survive a compile.

The mod must have **higher MO2 priority than Malphas' Blessing**. Since nothing else ships the path,
any position would work today. Generated and enabled in Ultra
2026-10-21. **Unverified in game.** Retire it if Malphas' Blessing regenerates the facegen or
renames the folder back.
