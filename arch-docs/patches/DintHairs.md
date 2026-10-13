# DintHairs

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/DintHairs/`
- **Ships:** *(rebuilt third-party plugins, MO2 mods `[Dint999] BDOR Hairs - Hairs Only` / `[Dint999] HairPack02 - Hairs Only`)*
- **FormID block:** _(none)_

## What it does

Dint999's **BDOR Hairs SSE 0.23** (141 hairs) and **HairPack02 SSE 1.12 (base)** (220 hairs), **hairs only**: wigs are not wanted. Both archives are on Wabbajack's `opt-out-lists/ServerWhitelist.yml` (BDOR = Google Drive ID `1B1p7p13mZWTrHCE6dsel4jRGtOsHuu7k`, HP02 = the MediaFire link), and their `downloads/*.meta` carry those `directURL`s. A different version of either file won't match the whitelist. `src/DintHairs/tools/01-build-hairs-only.py` serializes each plugin, keeps ONLY `HeadParts` (every TXST is wig-only; ARMO/ARMA/COBJ/BOOK go; HP02's `CELL 016BDF:Skyrim.esm` override, Riften's Bee and Barb for its crafting books, **does not exist in Enderal**), rebuilds under the original filename (FormIDs kept for saves/presets), asserts counts, and copies only assets reachable from the head parts (726 MB + 2.3 GB of 10 GB). HDPTs reference only `HeadPartsAllRacesMinusBeast 0A803F` (present in Enderal). Rebuilt: HEDR 1.70, master Skyrim.esm only, NOT ESL (FormIDs up to `0x2E4C`, so they cannot be compacted without breaking saves): **+2 full plugin slots**. Some `.tri` morphs the HDPTs name were never shipped by the author (removed in HP02 1.11); harmless. Requires FSMP + RaceMenu + XPMSSE (all in the list). Added 2026-10-11 to Alpha 0.5, **disabled**, above KS Hairdos SSE; not yet run in game.
