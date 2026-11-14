# EVGModestyOff

- **Source:** `src/EVGModestyOff/tools/01-build-modesty-off.py` (generator; output not committed)
- **Ships:** MO2 mod `Zenderal - EVG Modesty Off`, which holds four OAR `user.json` files and nothing else.
  Wabbajack `NoMatchInclude`. It must outrank `EVG Conditional Idles` and its compatibility patch, so in MO2's left
  pane it goes below both.
- **FormID block:** none
- **Status:** built 2026-11-13; it has to be ticked in MO2 (MO2 was open). Unverified in game.

## Why

Player report (2026-11-13): Yuslan Sha'Rim (`02AE01:FS`) "always walks like he is covering" himself.

- EVG Conditional Idles' four Modesty submods (`EVGCI/NPC Modesty F|M`, `Player Modesty F|M`, priority 86001901 in
  the compatibility patch) play a covering walk for any actor wearing nothing with `ArmorCuirass 06C0EC` or
  `ClothingBody 0A8657`.
- In Enderal, plenty of robes and outfits carry neither keyword, so dressed NPCs walk as if naked. Yuslan wears
  outfit `0BCAB9`; his record has no walk-style keywords in base, EGO or Malphas' Fixes, and the 2026-11-12 Malphas
  merge did not change his walk.

The curator chose to turn modesty off for players and NPCs alike.

## How

OAR reads a submod's `user.json` in place of its `config.json`. Each file here is the winning `config.json` (the
compatibility patch's) with only `"disabled": true`. EVG's files are untouched. EVG's MCM toggle for modesty
(global `80D`) only covers houses, so it can't do this.

## Upkeep

Rerun `tools/01` after an EVG Conditional Idles or compatibility-patch update.

## To verify in game

Yuslan and robed NPCs walk normally. OAR's animation log (OAR menu → Animation Log) shows no `Modesty` submod.
