# IronGolemClean

- **Source:** `src/IronGolemClean/tools/01-build-cleaned-golem.py` (generator only; its output is third-party
  content and is never committed)
- **Ships:** nothing. It builds a cleaned `mihailirongolem.esp` into the MO2 mod
  *Iron Golem - Enderal cleaned plugin (Zenderal)*.
- **Status:** built and installed 2026-10-21. Type-collision scan: 0. Unverified in game.

## Why

DynDOLOD stopped with *"Record [REFR:00021EDB] in file Skyrim.esm is being overridden by record [WRLD:00021EDB]
in file mihailirongolem.esp."* A scan of the whole `Ultra` load order for **form type collisions** (any override
whose record type differs from the defining plugin's) found exactly one plugin: Mihail's **Iron Golem** (Skyrim SE
mod 29228, v4.0.0). It is a Skyrim mod that places its golems in Skyrim locations:

| Record | Skyrim | Enderal |
|---|---|---|
| `021EDB` LabyrinthianWorld04 (+ cell `021EEA`) | worldspace | a **placed reference** |
| `091872` Labyrinthian03 | interior cell | a **placed reference** |
| Dawnguard `DLC1HunterHQWorld` (4 cells), Dragonborn `DLC2TempleofMiraak02` | locations | empty DLC stubs |

So the plugin redefines two Enderal references as a worldspace and a cell, which is a CTD risk. It has no
leveled-list distribution, so the golems never appear in Enderal. It can't simply be disabled, though:
**`Steel Warden Replacer - EGO.esp` masters it** for the golem's race `000800`, skin `000802`, weapon `000804`,
voice `000832`, AI package `000836` and combat style `00083C`. No plugin references the dropped cells or
worldspaces.

## The fix

The user approved a generated cleaned copy (2026-10-21), on the same pattern as `KataAffinities21`:

- `mihailirongolem.esp`, same filename, serialized from the user's install with **every `Worldspaces/` and
  `Cells/` record removed** (9 records; the generator asserts the count). The other 48 records are unchanged:
  the round trip differs only in the order of two AI packages' data entries. The light-plugin flag and HEDR 1.7
  are preserved.
- Written to a new mod folder placed **directly above** the original in MO2's mod list, so its `.esp` wins the
  file conflict. The original stays enabled for its meshes, textures, sounds and scripts. `plugins.txt` is
  unchanged (same filename).

The copy's remaining references to missing Skyrim/DLC forms (5 in winning records) are handled by
[`UnresolvedRefsCleanup`](UnresolvedRefsCleanup.md), which was regenerated afterwards.

## Regenerating

After any Iron Golem update: `python src/IronGolemClean/tools/01-build-cleaned-golem.py`, then re-run
UnresolvedRefsCleanup's tools 00a → 00b → 01. Retire this if Steel Warden Replacer drops the golem master.
