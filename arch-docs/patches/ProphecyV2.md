# Prophecy v2 (Sanctum)

- **Source:** `src/ProphecyV2/` — **generated** by `tools/01-build-v2.py` from the v1 build (`src/Prophecy/`, run its
  `tools/01-build-trees.py` first). Never hand-edit `ProphecyESP/`.
- **Ships:** `Zenderal - Prophecy.esp` (same plugin as v1 — two archives of one ModKey) + 33 scripts + v1's assets.
- **FormID block:** v1's `0x800–0x915` (shared, identical) + v2-only `0xC00–0xD27`.
- **Status:** built 2026-10-21, round-trips; **not run in game.** v1 (thumbnail menu) and v2 are being A/B tested;
  one will ship.

## What it is

The Prophecy power teleports you into **ZP_ProphecySanctum**, an interior cell built from Enderal's own meditation
space (worldspace `Akropolis 0A7FB9`), and back out again — the same mechanics as Enderal's Meditation
(`_00E_Class_OpenClassMenuScript`: save position on a marker, `05BCFF` IMOD + `05C23E` sound, `MoveTo`). There the four
Prophecy trees hang as walk-up constellations: activate a star, read its description box (Learn / Back), and the
star glows (`PlayAnim02`), its lines light (`Unlock`) and the memory streams into you — the same forms Enderal's
`_00E_Class_PerkScript` uses (`03A1E7`, `02E6AD`, `0ACDC5`, `03C692`). Cost is Prophecy points (1 per 5 levels).
On entry every learned star/line is re-lit, so perks bought in v1 show.
Glory (4 perks, added 2026-10-21) hangs on the Blade Dancer wall; each tree's lines follow its perks' prerequisites,
so trees of 4 and 5 share one layout rule (`LAYOUTS` in `tools/01-build-v2.py`). v2's own IDs moved to `0xC00–0xD37`.

## How Enderal's physical trees are built (measured, reusable)

| Piece | Record | Notes |
|---|---|---|
| star | `_00E_Class_MemoryStar 05BD42` MSTT | `AkropolisPerk.nif`; sequences animIdle01/02, animTrans01 driven by event `PlayAnim02` |
| line | `_00E_Class_PerkLine 0A8263` STAT | vanilla `interface/intperkline01.nif`; sequences `Unlock`/`Unlocked`. Fitted on all 243 Enderal lines: runs along local **+Y**, rotation matrix **Rx(−rx)·Ry(−ry)·Rz(−rz)**, origin **4.1** past the start star, scale = star distance / **81.3**, ribbon normal (local Z) = wall normal (0.97–1.0 alignment) |
| node | `_00E_Class_Acti_*` ACTI | `invisiblecollision_perks.nif` at the star, scale ~2–3, script `_00E_Class_PerkScript` with per-ref properties |
| walls | 9 class constellations | vertical, ~80 wide × 200 tall, three per root stone (Warrior/Mage/Rogue); stars are persistent refs in the WRLD top cell |

Our trees reuse four of those walls (Faith → Thaumaturge, Gunslinger → Trickster, Gadgets → Infiltrator,
Martial Arts → Vandal): same plane, same star rotation, layout root → two branches → merge → capstone. The cell takes
Enderal's environment refs at their own coordinates (212, minus Enderal's stars/lines/nodes/markers/triggers/water)
and the lighting of `MQP03TempleInnerVision` (Enderal's vision void). Spawn = Enderal's `_00E_ClassMenuOrigin` position.

## Unverified / likely to need tuning in game
Lighting and sky (interior, no Akropolis weather); whether star/line animations persist across save/load (re-lit on
entry regardless); star spacing (`HALF_WIDTH` 40, vertical span = the reused wall's); the player keeps fighting/
casting enabled so the power can be recast to leave.
