# RiverBush

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/RiverBush/`
- **Ships:** `Zenderal - RiverBush.esp`
- **FormID block:** `0x800–0x81F`

## What it does

32 bushes (`0AC865:Skyrim.esm`) in Riverville exterior cells `FlusshaimMittelweg 001EA7` / `FlusshaimZentrum 001EB1` on top of EPPI Riverville, plus one edited EPPI ref (`002207:EPPIriverville.esp`). Authored in the Creation Kit; it lived ONLY in MO2's `overwrite` (invisible to Wabbajack) at HEDR 1.71, not ESL, FormIDs `0x146D–0x2D68`. Brought into the repo 2026-10-05: HEDR 1.70, ESL, all 32 new refs renumbered into `0x800–0x81F` in original order, placements byte-for-byte unchanged (verified by object-by-object comparison against the CK original; the CK's `-0` rotation components normalise to `0`). Its `Vyn` WRLD record is header-only and matches FS's. Masters: Skyrim + Update + FS + `EPPIriverville.esp`. **When editing it again in the CK, re-serialize the CK output into `src/RiverBush/` and re-apply HEDR 1.70 / ESL** — the CK writes 1.71 and CK-assigned FormIDs.
