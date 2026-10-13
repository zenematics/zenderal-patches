# ArkMarketTreeFix

> Moved out of `CLAUDE.md` on 2026-10-13. Text is verbatim; `[verified]` marks and dates are as originally recorded.

- **Source:** `src/ArkMarketTreeFix/`
- **Ships:** `Zenderal - Ark Market Tree Fix.esp`
- **FormID block:** none (overrides only)

## What it does

Floating juniper in Ark's market (reported 2026-10-11). `Ark Marketplace house exterior addon.esp` (*House at the Marketplace - Exterior Add-on*, load 79 in Alpha 0.5) places `_00E_Juniper 14BD3A` ref `003A97` (scale 0.48) in `ArkMarket 070794` (`CapitalCityMarketArea 07072A`) at Z **2142.7**, while its own LAND there decodes to **2074.5** and base Enderal's manhole `070E04` beside it sits at 2073: the author's placement error, not a conflict. A binary scan of every Alpha 0.5 plugin found only Skyrim/FS/the addon touching the cell. One REFR override lowering it to Z 2068 (trunk ~6 units into the ground), every other field verbatim; WRLD record header-only plus group scaffolding, cell header from the addon (field-for-field identical to FS). Masters: Skyrim + Update + FS + the addon. Deployed 2026-10-11 as MO2 mod `Zenderal - Ark Market Tree Fix`, not yet verified in game.
