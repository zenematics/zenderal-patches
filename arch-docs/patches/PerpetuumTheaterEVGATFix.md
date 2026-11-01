# PerpetuumTheaterEVGATFix

- **Source:** `src/PerpetuumTheaterEVGATFix/` (generated: `tools/01-build-perpetuum-theater-evgat-fix.py`)
- **Ships:** `Zenderal - Perpetuum Theater EVGAT Fix.esp` (ESL, HEDR 1.7)
- **FormID block:** none (overrides only)
- **Status:** built, round-trip clean; **unverified in game**

## The bug

Reported 2026-10-18 from a player's video in Ark, Nobles Quarter, beside the theater: at night a
long wooden plank and a post with a round boss hang in the sky above the stairs at the theater's
south-east corner.

They come from **EVG Animated Traversal - Enderal Addon 2.3** (`EVGAT_Enderal.esp`), not from the
theater. Four EVGAT refs (VersionControl `12853`, so a later batch than the rest of its Ark refs)
were laid out against base Enderal's old theater:

| Ref | Base | Where | What it is now |
|---|---|---|---|
| `0009CC:EVGAT_Enderal.esp` | `ShipWoodplanks01 04F8E9` | cell `07076D`, z 4279 | the floating plank |
| `0009CD:EVGAT_Enderal.esp` | `SSighPost01 0B735A` | cell `07076D`, z 4416 | the floating post |
| `0009CA:EVGAT_Enderal.esp` | `000021` (collision plane, 867×2×1202) | cell `07076D`, z 3924 | invisible wall 65 units from the theater's new steps `004F4B` |
| `0009CB:EVGAT_Enderal.esp` | `000021` (collision plane, 867×2×1202) | `UpperQuarterWatchtower 070770`, z 3914 | invisible wall standing in the theater's new terrace paving |

**The Perpetuum Theater - Neo Enderal** (Enderal Nexus 1092, 1.0) disables that whole corner — the
Bard College statics, patio walls, sign posts `0858F2` and planks it moves — and rebuilds it lower
and further out. Its own **EVGAT Enderal Patch** (1.0) fixes EVGAT's older refs there
(`000873`, `00088E`, `000891`, `000892`, `000894`, the `00088F`/`000890` marker pair) but none of
`0009CA`–`0009CD`. With nothing under them any more, the plank and post sit 400–550 units above
the new ground.

How it was found: a binary scan of every enabled plugin in the `Ultra` profile for a type-1 GRUP
labelled `CapitalCityUpperCity 07072B` gave 14 plugins (Skyrim/FS, EGO, Secure Chests, Temple of
Malphas, Ark City Gate, Ducks and Swans, Mihail Ravens, the three Perpetuum plugins, Maps, EVGAT,
ETATU CM Fixes, DynDOLOD). With all of them serialized, the only refs inside the theater's bounding
box that the theater does not override are these four, plus two Mihail ravens.

## The fix

Each of the four refs is copied verbatim from `EVGAT_Enderal.esp` and disabled the xEdit way:
`InitiallyDisabled`, enable parent `PlayerRef` with opposite state, z −30000. This is the same
shape the theater uses for the vanilla refs it removes.

Headers are forwarded verbatim from the last overrider of each:

| Record | Taken from |
|---|---|
| WRLD `07072B` | `Perpetuum Theater - Enderal TAT CM Fixes.esp` (identical to EGO / Theater / EVGAT) |
| CELL `07076D` | `Perpetuum Theater - Enderal TAT CM Fixes.esp` |
| CELL `070770` | `EVGAT_Enderal.esp` (differs from Theater's only in XCLC padding flags) |

Masters: Skyrim, Update, FS, `EVGAT_Enderal.esp`, `Perpetuum Theater - EVGAT Enderal Patch.esp`,
`Perpetuum Theater - Enderal TAT CM Fixes.esp`. The last two exist only to force it to load after
both theater patches. Place it after `Perpetuum Theater - Enderal TAT CM Fixes.esp` and before
`Occlusion.esp` / `DynDOLOD.esp`.

The refs are plugin records, not save state, so this needs no new game. The theater mod itself
does ask for one, but that is separate.

## Regenerating

Re-serialize `EVGAT_Enderal.esp` → `reference/mods/EVGATEnderal` and
`Perpetuum Theater - Enderal TAT CM Fixes.esp` → `reference/mods/PerpetuumTheaterETATU`, then run
`python src/PerpetuumTheaterEVGATFix/tools/01-build-perpetuum-theater-evgat-fix.py`. The script
refuses to build if any of the four refs is already disabled upstream. Retire the patch if a newer
theater EVGAT patch covers them.
