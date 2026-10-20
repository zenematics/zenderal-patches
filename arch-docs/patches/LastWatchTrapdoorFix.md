# LastWatchTrapdoorFix

- **Source:** `src/LastWatchTrapdoorFix/` (generated: `tools/01-build-last-watch-trapdoor-fix.py`)
- **Ships:** `Zenderal - Last Watch Trapdoor Fix.esp` (ESL, HEDR 1.7)
- **FormID block:** none (overrides only)
- **Status:** built, round-trip clean; **unverified in game**

## The bug

A player reported it on 2026-10-20: after climbing from Ark's Last Watch's Watchtower
(`DPassTurm 103F39`) to the top of the tower, there is no trapdoor or ladder to get back down.

The way down is still there. The ladder `TurmLadderLower 1042FD` teleports the player to the
trapdoor `1043D6` (`FarmBTrapdoor02 0E9E08`, persistent in Vyn), and no plugin disables either
one. The trapdoor is buried, because two mods rebuild the tower top without knowing about each
other:

| Plugin (load order) | What it does to the tower top |
|---|---|
| `EPPIimprovedlacations.esp` | Disables Enderal's `TowerTop01` ref `1043EC`. Lays its own plank floor `WRIntCastleFloorWoodMid01QuadS 035BE3` (512×512, scale 1.17, so about x 21775–22374, y 40039–40638) flat at z 13930, and adds cannons, hay and beams on it. Enderal's trapdoor and clutter stay where base put them, at z ≈ 13929, on top of the planks. |
| `Last Watch Overhaul.esp` (Ark's Last Watch 1.1, loads after) | Also disables `1043EC`, and re-bases the tower pieces `0736A4` → `CitywallTower` and `0736A5` → `TowerBaseUpper_Snow`. It drops the trapdoor to (22148, 40103, **13898**), the ladder's arrival point to z 13902, and the top's clutter 20–30 units onto its own lower, tilted top. |

Together, EPPI's planks at z 13930 cover the trapdoor, whose top is now at about 13920. The player
arrives under the floor and pops up onto it, with no trapdoor in sight. The loot chest `1043F6`
(z 13902) and the barrels are buried too. Neither of Last Watch's two EPPI patches touches the tower
top: the Improved Locations patch only edits ground-level refs in `00291B`.

Enderal 2.1 did not cause this. The tower statics and meshes are identical in 2.0.12.4 and 2.1.4.4.

## The fix

Every tower-top ref that Last Watch wins keeps Last Watch's record (including its
`LocationReference` and other fields). Only the `Placement` is replaced, taken from the plugin that
was built for EPPI's floor:

| Ref | Placement from |
|---|---|
| trapdoor `1043D6` | base Enderal: (22050, 40163, 13929) |
| `1043ED`–`1043F2` (barrels, hay) | base Enderal (EPPI kept base's placement) |
| `1043F3`–`1043F6` (snow drifts, loot chest) | EPPI's own overrides |
| ladder `1042FD` `TeleportDestination` | base Enderal: lands next to the trapdoor |

Headers are forwarded verbatim from each record's last overrider:

| Record | Taken from |
|---|---|
| WRLD `Vyn 001D3C` | `Water for Enderal CS.esp` |
| persistent CELL `001D40` | `Zenderal - Ark Bridge Overhaul Fixes.esp` (`src/ArkBridgeOverhaulFixes`) |
| CELL `ArksletzteWacht 00291B` | `Last Watch - EPPI Improved Locations Patch.esp` |
| CELL `DPassTurm 103F39` | `MinotaursInEnderal.esp` (identical to Last Watch's) |

The masters are Skyrim, Update, FS, `EPPIimprovedlacations.esp`, `Last Watch Overhaul.esp` and
`Water for Enderal CS.esp`. Load it after `Water for Enderal CS.esp`. In `Ultra` it is the last
plugin.

Last Watch's three new hay mounds `000174`–`000176` (z ≈ 13916) stay half-sunk into EPPI's planks.
They are mounds, so that reads as hay piled on the floor, and this patch leaves them alone.

The refs are plugin records, so an existing save picks up the fix. One exception: a player
already standing on the tower top may need to leave the cell and come back first.

## Regenerating

1. Re-serialize `Last Watch Overhaul.esp` → `reference/mods/LastWatchOverhaul`,
   `EPPIimprovedlacations.esp` → `reference/mods/EPPIimprovedlocations` and
   `Last Watch - EPPI Improved Locations Patch.esp` → `reference/mods/LastWatchEPPIImproved`.
2. Re-check the header winners in the table above.
3. Run `python src/LastWatchTrapdoorFix/tools/01-build-last-watch-trapdoor-fix.py`. It asserts 12
   overrides and prints each placement change.

Retire the patch if Ark's Last Watch ships an EPPI Improved Locations patch that covers the tower top.
