# PrettyArmoryEGO

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/PrettyArmoryEGO/`
- **Ships:** `Zenderal - Pretty Armory EGO Patch.esp`
- **FormID block:** none (overrides only)

## What it does

**GENERATED — never hand-edit the record folders.** 141 overrides (ARMO/WEAP/AMMO/ARMA/PROJ/NPC_) of records the 11 Pretty * plugins revert. Each = the in-game WINNER's record (Pretty's meshes/armatures/outfits/items; for 2 Heavy Leather records the winner is `Enderal Remastered Armory - Heavy Leather.esp`) with the DONOR plugins' gameplay changes forwarded: donors = EGO, `Enderal SE - Bug Fixes.esp`, the two AOS plugins. Field policy lives in the docstring of `src/PrettyArmoryEGO/tools/02-merge-pretty-ego.py`: models/armatures/bounds/templates/outfits/items always the winner's; ARMA only takes FootstepSound + AdditionalRaces; Keywords set-merged; `BodyTemplate` merged per sub-field (FirstPersonFlags from Pretty, ArmorType from EGO); names compared on the English string (EGO and Pretty are both non-localized), where an actual Pretty rename wins. Compression flags (`IsCompressed`/`MajorRecordFlagsRaw`/`MajorFlags: 0x40000`) are ignored — EGO's NPC overrides differ from base there only by storage. Pretty Unique Armory ships 3 weapon descriptions as UTF-8 Russian decoded as cp1252 (`Ð°Ð½…`); the generator detects that and restores EGO's English. **Regenerate: `01-build-override-chains.py` (reads the live MO2 profile via `tools.json`'s `modlistRoot`) then `02-merge-pretty-ego.py`**, after re-serializing the Pretty plugins to `reference/mods/Pretty/` and the donors to `reference/mods/PrettyContext/`. Masters: the base three + EGO + every Pretty plugin it overrides + ERA Heavy Leather — so the engine enforces load-after
