# DragonPriestStaffSwap

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/DragonPriestStaffSwap/`
- **Ships:** *(no plugin — loose meshes, MO2 mod `Zenderal - Dragon Priest Staff Swap`)*
- **FormID block:** _(none)_

## What it does

Curator's taste: Pretty Mages Armory replaces the vanilla Dragon Priest staff by PATH (`weapons\dragonpriest\dragonprieststaff3rd.nif` = WEAP Model, `dragonprieststaff.nif` = 1st-person STAT `01C200`, both in its BSA) with a brass "Maelstrom Staff" (texture `maelstromstaff\staff\maelstromstaff.dds`). Pretty's plugin repoints 17 Enderal staffs to their own meshes, but 8 Enderal records still use that path — Fire Wrath `07C982`/`07C9AD`/`03990E`, Frostbite `07C9B0`, Grounding `07C980`/`07C9B1`, Lightning `07C9AA`, template `0BE11F` — plus 19 Apocalypse and 7 Triumvirate staffs. `src/DragonPriestStaffSwap/tools/01-swap-dragon-priest-staff.py` writes Pretty's own Staff of Chain Lightning mesh (`enderal\weapons\staves\staffofchainlightning.nif`, black blade head + orb; Pretty itself uses that one file for both 3rd and 1st person) loose at both paths; loose beats BSA, no other mod ships either path. Not committed (Pretty's mesh). Rebuild CRDW after enabling. Built 2026-10-13, verified in game 2026-10-13.
