# PrettyArmoryEGO

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/PrettyArmoryEGO/`
- **Ships:** `Zenderal - Pretty Armory EGO Patch.esp`
- **FormID block:** none (overrides only)

## What it does

**GENERATED — never hand-edit the record folders.** 141 overrides (ARMO/WEAP/AMMO/ARMA/PROJ/NPC_) of records the 11 Pretty * plugins revert. Each = the in-game WINNER's record (Pretty's meshes/armatures/outfits/items; for 2 Heavy Leather records the winner is `Enderal Remastered Armory - Heavy Leather.esp`) with the DONOR plugins' gameplay changes forwarded: donors = EGO, `Enderal SE - Bug Fixes.esp`, the two AOS plugins. Field policy lives in the docstring of `src/PrettyArmoryEGO/tools/02-merge-pretty-ego.py`: models/armatures/bounds/templates/outfits/items always the winner's; ARMA only takes FootstepSound + AdditionalRaces; Keywords set-merged; `BodyTemplate` merged per sub-field (FirstPersonFlags from Pretty, ArmorType from EGO); names compared on the English string (EGO and Pretty are both non-localized), where an actual Pretty rename wins. Compression flags (`IsCompressed`/`MajorRecordFlagsRaw`/`MajorFlags: 0x40000`) are ignored — EGO's NPC overrides differ from base there only by storage. Pretty Unique Armory ships 3 weapon descriptions as UTF-8 Russian decoded as cp1252 (`Ð°Ð½…`); the generator detects that and restores EGO's English. **Regenerate: `01-build-override-chains.py` (reads the live MO2 profile via `tools.json`'s `modlistRoot`), then `02-merge-pretty-ego.py`, then `03-forward-npc-faces.py`**, after re-serializing the Pretty plugins to `reference/mods/Pretty/` and the donors to `reference/mods/PrettyContext/`. Masters: the base three + EGO + every Pretty plugin it overrides + ERA Heavy Leather — so the engine enforces load-after

## NPC faces: `tools/03` (2026-10-28)

Reported by a beta player: Tealor's Malphas' Blessing face didn't show, and moving `Malphas' Blessing - Enderal.esp`
below this patch fixed it. Tealor `01ADF1` is one of the patch's 5 NPC records. His live chain is base → EGO →
Pretty Holy Order Grandmaster → Malphas' Blessing → MB - EGO. 02 had taken his `HeadParts` from Pretty and his
`WornArmor` from base, and this patch loads last, so it put the old head and skin back under MB's baked FaceGen
mesh. **[verified]** by field diff across all six records.

`03-forward-npc-faces.py` finds, for every NPC in the patch, the face **owner**: the last plugin in the live
chain that changed any face field (`HeadParts`, `HairColor`, `HeadTexture`, `FaceMorph`, `FaceParts`,
`TintLayers`, `TextureLighting`, `WornArmor`, `Height`, `Weight`) from base. It copies that plugin's whole face
group, so the fields always match one FaceGen mesh, and adds the plugins those fields name as masters, in live
load order. Tealor now has MB - EGO's head parts and MB's skin `000831` (plugin masters
`Malphas' Blessing - Enderal.esp`), plus Pretty's outfit and EGO's perks, skills and combat style. The four
MQ07a enemies keep base faces.

No other Zenderal plugin overrides any of MB's 50 NPCs. A full 02 rerun currently stops: the chains now name
plugins without reference trees, starting with `Zenderal - 2.1 Levelsystem Cleanup.esp`. MB and MB - EGO were
serialized to `reference/mods/PrettyContext/`. Rebuilt into Patch Collection's copy (the only one); backup in
`E:/Zenderal-backups/2026-10-28-pretty-armory-ego-pre-tealor-face/`. Unverified in game.
