# ApocalypseNaviFix

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/ApocalypseNaviFix/`
- **Ships:** *(HOTFIX — rebuilt `Apocalypse - Magic of Skyrim.esp`, MO2 mod `Zenderal - Apocalypse NAVI Fix`)*
- **FormID block:** _(none)_

## What it does

The rebuilt Apocalypse (`Apocalypse - Enderal Patch`) still carried Skyrim's `NavigationMeshInfoMap` at **`012FB4:Skyrim.esm`** — which in Enderal is the Forgotten Temple floor tile `DweRmLgMid01` (`ForgottenTemple 012C3B`, at -2560, 8576, 2368). The NAVI override replaced the REFR: no render, no collision, a triangular hole players fall through, reproducible for everyone. `src/ApocalypseNaviFix/tools/01-rebuild-without-navi.py` serializes the live `.esp`, drops only `NavigationMeshInfoMaps/012FB4`, deserializes, and **asserts** the rebuild re-serializes to the identical tree (3643 files) with the same header/masters (records 3964→3962 = the NAVI + its GRUP). Not committed: the `.esp` is the author's. Must sort above `Apocalypse - Enderal Patch`. **Retire it** once the `enderal-mods` Apocalypse tree drops `NavigationMeshInfoMaps/` (the real fix). Built 2026-10-07, not yet verified in game.
