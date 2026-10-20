# MaceSpeed

- **Source:** `src/MaceSpeed/`
- **Ships:** `Zenderal - Mace Speed.esp` (ESL; masters `Skyrim.esm`, `Update.esm`, FS, `Enderal SE - Gameplay Overhaul.esp`)
- **FormID block:** none (22 overrides)
- **Status:** built 2026-10-19, Spriggit round trip identical. **Unverified in game.**

## The report

Player feedback, 2026-10-19: one-handed + shield feels weak, "especially the mace". The For Honor
mace moveset is "slow without enough damage to justify it"; two-handers hit harder *and* feel faster.

## What was found

- **Every one-handed mace in the list has weapon Speed 0.8.** One-handed axes are 0.9, swords 1.0,
  daggers 1.3; greatswords 0.6–0.75. **[verified]** (`reference/` scan of every WEAP by DNAM
  `AnimationType`, then a live scan of the `Ultra` profile.)
- EGO also *lowered* mace damage against base Enderal (Aeterna 34 → 29, Selna's Crusher 35 → 33,
  Rune 13 → 11), without touching speed. Per swing, an EGO Rune mace (11 × 0.8 = 8.8) now trails a Rune
  sword (9 × 1.0 = 9.0), and its heavier, slower swings land later. **[verified]** in EGO's records.
- The live scan (`tools/00-scan-maces.py`, master-aware binary walk of every enabled plugin) found
  **26 maces; EGO wins 22**. The other four are left alone:
  - `_D_PyreanMace_Unplayable 000802:Pretty Pyrean Armory.esp` — NPC-only.
  - `WB_ConjureDremoraChurl_Weapon(_Enchanted)` `140019`/`14001D:Apocalypse - Magic of Skyrim.esp` — summon weapons.
  - `025902:Castle Bleakstar.esp` (won by `Castle Bleakstar - EGO Patch.esp`) — already 0.85.
- No other Zenderal patch overrides any of the 22. **[verified]** (grep of `src/`.)

## What the patch does

Each of the 22 records is EGO's WEAP copied verbatim from `reference/mods/EGO/Weapons/`, with the
DNAM `Speed` changed from 0.8 to 0.9 (war-axe parity). Damage is unchanged. Weapon Speed is the
attack-animation playback rate, so this also makes NPC mace wielders swing faster.

## Regenerating

```
python -I src/MaceSpeed/tools/00-scan-maces.py     # live load order -> tools/maces.json
python -I src/MaceSpeed/tools/01-build-mace-speed.py
```

`01` refuses to run if any EGO mace's live speed is not 0.8, if a source file has other than one
`Speed: 0.8` line, if a record cites a master the plugin does not declare, or if the count is not 22.
Re-run both after EGO updates, or when a mod that adds or overrides maces is enabled.

## Open questions

- Whether FHR's mace attack clips scale with weapon Speed the way vanilla attacks do. If the
  swings still feel the same, that is the first thing to check (the behaviour graph's
  `weaponSpeedMult`, or a hard-coded playback speed in the moveset).
- Whether 0.9 is enough; the alternative was 1.0 (sword parity).
