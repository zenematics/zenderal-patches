# VeiledWomanStatues

- **Source:** `src/VeiledWomanStatues/` (generated: `tools/01-build-veiled-woman-statues.py`, `tools/02-restore-meridia-mesh.py`)
- **Ships:** `Zenderal - Veiled Woman Statues.esp` (ESL, HEDR 1.7, inside `Zenderal - Patch Collection`) + the MO2
  mod `Zenderal - Veiled Woman Statue` (Enderal's own statue mesh, not committed)
- **FormID block:** none (overrides only)
- **Pillar:** bug fixes (lore)

## Why

Player report (Discord, evLRise, 2026-10-23, "Lorebreaking Statue Model - BIG SPOILERS"). Enderal shows the Veiled
Woman with one statue, Skyrim's Statue of Meridia mesh (`LoadScreenStatueofMeridia01 10A17A`,
`Clutter\Statues\StatueofMeridia01.nif`): a hooded, robed woman with one arm raised holding up a glowing orb, placed in
the Ishyian/Pyrean ruins tied to her among the crystal and circle motifs. Seeing the same figure again and again is
how players connect her to those places; Old Sherath depends on it most.

**Mandragorasprouts' Statues for Enderal** (Enderal Nexus 618, `man_DaedricShrines_Enderal.esp`) swaps statues in 18
locations. Its page says it replaced "almost all of the Meridia statues used to represent the Veiled Woman" with
Nocturnal, and it also ships its own sculpt at the Meridia mesh path. Field check (2026-11-08, decompile in
`reference/mods/MandragoraStatues/`): it disables all six `10A17A` placements it touches and adds:

| Cell | SureAI's (disabled by the mod) | Mod's replacement |
|---|---|---|
| `FSNQ02BurgInt 028E8B:FS` (castle interior) | `029766`, `029768`, `029B8E` + ruin brick `029B8F` | Nocturnal `000807`, `00080E`, `00080F` |
| `AltIshmartepL1 0A5894` (Old Ishmartep) | `029953:FS` | Nocturnal `000806` |
| `FSNQ02DalMercerHouse 028441:FS` | `02977A:FS` | Nocturnal `000805` |
| `AltSherathL2 043DEF` (Old Sherath) | `0440BF` | **Kynareth** `000808` |

The seventh Enderal placement (`DGraeberpfadeL1`) isn't moved, but showed the mod's Meridia mesh.

## What it does

- `tools/01`: each cell's header = its current winner verbatim (`Castle Bleakstar.esp` for the castle,
  `EVGAT_Enderal.esp` for Old Sherath, the statue mod for the other two; navmeshes and persistent refs not copied);
  SureAI's 7 objects = base/FS 2.1 verbatim (enabled, original position); the mod's 6 replacements = its record +
  `InitiallyDisabled`, the way it disables SureAI's. Chains asserted. The mod's other statues (Mara, Sanguine,
  Azura, Hircine, Kynareth in the crypts, ...) stay.
- `tools/02`: Enderal's `statueofmeridia01.nif` from `Skyrim - Meshes0.bsa` into the MO2 mod
  `Zenderal - Veiled Woman Statue`, which must outrank the statue mod (directly above it in `modlist.txt`).
  It ships through a Wabbajack `Include` rule (added 2026-11-09; before that the compile had no source for it). It stays
  out of Patch Collection, which only carries our own work.

## Load order

Plugin after `man_DaedricShrines_Enderal.esp`, `Castle Bleakstar.esp` and `EVGAT_Enderal.esp` (all masters); in Ultra
it sits after `Zenderal - Meditation Water Fix.esp`, before the cleanup/DynDOLOD tail. **Rerun `tools/01` when any of
those cells' winners changes** (it stops if a chain changed).

## Status

Built, round-trip identical apart from field order, deployed and enabled 2026-11-08 (profile backups in
`E:/Zenderal-backups/2026-11-08-veiled-woman-footsteps/`). Unverified in game: check Old Sherath's statue (`coc
AltSherathL2`). Not changed: Stunning Statues of Skyrim / Dibella replacers swap Vaermina, Dibella and Nocturnal meshes
for nicer versions of the same figures; the statue mod's other god swaps (e.g. Old Ishmartep L2's Vaermina →
Azura) are outside this report.
