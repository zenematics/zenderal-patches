# EppiRivervilleCobbleRemoval

- **Source:** `src/EppiRivervilleCobbleRemoval/` (generated: `tools/01-build-cobble-removal.py`)
- **Ships:** `Zenderal - EPPI Riverville Cobble Removal.esp` (ESL, HEDR 1.7)
- **FormID block:** none (overrides only)
- **Status:** built, round-trip clean; **unverified in game**

## Why

Curator's taste (2026-10-20, from a screenshot of Riverville's streets). **EPPI Riverville**
(`EPPIriverville.esp`) paves the town with pale raised cobble plates. Each one is a placed copy of
EPPI's own static `NorPlatBgFloorRaised01_EPPIrivervillecobble 029B46:EPPIriverville.esp`, which uses
the mesh `NorPlatBgFloorRaised01.nif`. There are 98 of them, all in sub-block `-3, -1` of Vyn:

| Cell | Refs |
|---|---|
| `FlusshaimZentrum 001EB1` | 39 |
| `FlusshaimHonigpresse 001EB2` | 23 |
| `FlusshaimMittelweg 001EA7` | 20 |
| `FlusshaimEingang 001E9C` | 8 |
| `FlusshaimMarktplatz2 001EB0` | 4 |
| `FlusshaimMarktplatz 001EA6` | 3 |
| `001EB9` | 1 |

A binary scan of the `Ultra` load order found no other plugin overriding any of the 98 refs.

## The fix

Each ref is copied verbatim from EPPI and disabled the xEdit way: `InitiallyDisabled`, enable parent
`PlayerRef` with opposite state, and z −30000. The rest of EPPI (its other refs and its navmesh) is
left alone.

Headers are forwarded verbatim from each record's last overrider:

| Record | Taken from |
|---|---|
| WRLD `Vyn 001D3C` | `Water for Enderal CS.esp`. Its header carries `LodWater 000802:Water for Enderal CS.esp`, so that plugin is a master. |
| CELL `001EB1`, `001EA7` | `Zenderal - RiverBush.esp` (`src/RiverBush`). The cell headers carry no RiverBush FormKeys, so RiverBush is not a master. |
| CELL `001EB9`, `001E9C`, `001EA6`, `001EB0`, `001EB2` | `EPPIriverville.esp` |

The masters are Skyrim, Update, FS, `EPPIriverville.esp` and `Water for Enderal CS.esp`. Load it
after `Water for Enderal CS.esp`. In `Ultra` it sits directly below that plugin, at the end of
plugins.txt.

The refs are plugin records, not save state, so the plates disappear on an existing save too.

## Regenerating

1. Re-serialize `EPPIriverville.esp` into `reference/mods/EPPIriverville` and
   `Water for Enderal CS.esp` into `reference/mods/WaterForEnderalCS`.
2. Re-check the header winners in the table above.
3. Run `python src/EppiRivervilleCobbleRemoval/tools/01-build-cobble-removal.py`.

The script asserts 98 refs. It refuses to build if any ref is already disabled, enable-parented or
flagged upstream. Note that `src/RiverBush`'s YAML is LF while reference decompiles are CRLF; the
script normalizes both on read.
