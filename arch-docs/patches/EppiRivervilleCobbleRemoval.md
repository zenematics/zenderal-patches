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

## White road pieces (2026-10-30)

Player report (Ehlengast): white ground in front of Riverville's Forgotten Basement. EPPI also places 10
copies of `RoadChunkM04_EPPIriverville_grass02 029B3E:EPPIriverville.esp` (`RoadChunkM04.nif`), 5 in
`FlusshaimHonigpresse 001EB2` (`029B3F`–`029B43`) and 5 in `FlusshaimMittelweg 001EA7` (`029B9A`–`029B9E`).
Its alternate textures put TXST `013429` on shape `RoadChunkM04:2` and `007E18` on `RoadChunkM04:0`.

**[verified 2026-10-30 on the Ultra profile]** `PG_1.esp` (PG Patcher) repoints the static at its duplicate
`_pgpatcher_dups\1\landscape\roads\roadchunkm04.nif` and keeps both swaps. In that mesh `RoadChunkM04:0` is
on the environment-map shader (type 1, no PBR flag) while the winning `007E18` is
`PBR Landscapes of Vyn.esp`'s PBR set (`pbr\landscape\cobblestone02` + `_n`, `_rmaos`, `_p`); the grass
shape and `013429` (`Tomato's PBR Landscapes.esp`) are both PBR. All the textures exist. A PBR set on a
non-PBR shader is the likely cause of the flat white; the plates (`029B46`, PG's own set `00005A`) were the
"pale plates" this patch first removed. Not confirmed by clicking the white patch in game.

Fix: the 10 road pieces are disabled the same way (now 108 refs). Disabling, rather than overriding the
static's alternate textures, survives PG Patcher reruns, which rewrite `PG_1.esp`'s copy of `029B3E`. A
binary scan of the Ultra load order found no plugin overriding the 10 refs.

## Regenerating

1. Re-serialize `EPPIriverville.esp` into `reference/mods/EPPIriverville` and
   `Water for Enderal CS.esp` into `reference/mods/WaterForEnderalCS`.
2. Re-check the header winners in the table above.
3. Run `python src/EppiRivervilleCobbleRemoval/tools/01-build-cobble-removal.py`.

The script asserts 98 plates and 10 road pieces. It refuses to build if any ref is already disabled, enable-parented or
flagged upstream. Note that `src/RiverBush`'s YAML is LF while reference decompiles are CRLF; the
script normalizes both on read.
